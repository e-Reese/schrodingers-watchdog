"""Service management with auto-restart capability"""

import os
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Dict, Any
import subprocess

import psutil

from .service_definitions import ServiceStrategyFactory


class ServiceManager:
    """Manages individual service processes with auto-restart capability"""
    
    def __init__(self, service_config: Dict[str, Any], log_callback: Callable, crash_log_path: Path):
        self.config = service_config
        self.name = service_config.get('name', 'Unknown Service')
        self.log_callback = log_callback
        self.crash_log_path = crash_log_path
        
        # Get strategy for this service type
        try:
            self.strategy = ServiceStrategyFactory.create(service_config.get('type', 'executable'))
        except ValueError as e:
            raise ValueError(f"Invalid service type for {self.name}: {e}")
        
        # Validate configuration
        is_valid, error = self.strategy.validate_config(service_config)
        if not is_valid:
            raise ValueError(f"Invalid configuration for {self.name}: {error}")
        
        self.process = None
        self.should_run = False
        self.monitor_thread = None
        self.crash_count = 0
        self.last_start_time = None
        self.tracked_pids = []  # Track child processes for apps that spawn and exit
        self.before_snapshot = {}  # Snapshot of processes before launch (for snapshot mode)
        self.profile_path = None
        self.profile_flag = None
        
        # Default to per-service profiles unless explicitly disabled
        if 'use_unique_profile' not in self.config:
            self.config['use_unique_profile'] = True
    
    def start(self):
        """Start the service and begin monitoring"""
        if self.should_run:
            self.log_callback(f"[{self.name}] Service is already running")
            return
        
        if not self.config.get('enabled', True):
            self.log_callback(f"[{self.name}] Service is disabled, skipping")
            return
        
        self.should_run = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop(self):
        """Stop the service and monitoring"""
        self.should_run = False
        self._kill_process()
    
    def is_running(self) -> bool:
        """Check if the service is currently running"""
        return self.should_run and self._is_process_alive()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current service status"""
        return {
            'name': self.name,
            'running': self.is_running(),
            'enabled': self.config.get('enabled', True),
            'crash_count': self.crash_count,
            'pid': self.process.pid if self.process and self._is_process_alive() else None,
            'last_start_time': self.last_start_time.isoformat() if self.last_start_time else None
        }
    
    def _monitor_loop(self):
        """Main monitoring loop - restarts service if it crashes"""
        # Apply startup delay if configured
        startup_delay = self.config.get('startup_delay', 0)
        if startup_delay > 0:
            self.log_callback(f"[{self.name}] Waiting {startup_delay}s before starting...")
            time.sleep(startup_delay)
        
        check_interval = 5  # Default check interval
        auto_restart = self.config.get('auto_restart', True)
        min_uptime_for_crash = self.config.get('min_uptime_for_crash', 10)  # Minimum seconds before considering exit a crash
        
        while self.should_run:
            try:
                # Only try to start/restart if nothing is alive (no parent and no tracked children)
                if not self._is_process_alive():
                    # Check if this is a crash (process was running but stopped)
                    if self.process is not None and self.last_start_time is not None:
                        # Calculate uptime
                        uptime_seconds = (datetime.now() - self.last_start_time).total_seconds()
                        exit_code = self.process.poll()
                        
                        # Determine if this is a crash:
                        # 1. If exit code is non-zero, it's ALWAYS a crash
                        # 2. If min_uptime_for_crash is 0, exits with code 0 are NEVER crashes (special case for browsers)
                        # 3. Otherwise, crash if process ran longer than minimum threshold
                        if exit_code is not None and exit_code != 0:
                            is_crash = True  # Non-zero exit code is always a crash
                        elif min_uptime_for_crash == 0:
                            is_crash = False  # min_uptime=0 means "quick exits with code 0 are normal"
                        else:
                            is_crash = uptime_seconds >= min_uptime_for_crash  # Crash if ran too long before exiting
                        
                        if is_crash:
                            self._log_crash_event()
                            if not auto_restart:
                                self.log_callback(f"[{self.name}] Auto-restart disabled, stopping monitor")
                                self.should_run = False
                                break
                        else:
                            # Normal exit (quick exit with code 0 - likely redirected to existing instance)
                            self.log_callback(f"[{self.name}] Service exited normally (exit code: {exit_code}, uptime: {uptime_seconds:.1f}s)")
                            
                            # Check if we should track child processes
                            track_children = self.config.get('track_child_processes', False)
                            if track_children:
                                # Wait briefly for background snapshot thread to complete
                                if not self.tracked_pids:
                                    self.log_callback(f"[{self.name}] Waiting for snapshot capture to complete...")
                                    time.sleep(1.0)  # Give background thread time to finish
                                
                                # If still no PIDs, take immediate snapshot
                                if not self.tracked_pids:
                                    self.log_callback(f"[{self.name}] Taking immediate snapshot to find child processes...")
                                    after_snapshot = self._take_process_snapshot(self.config.get('command', ''))
                                    parent_pid = self.process.pid if self.process else None
                                    new_pids = self._build_tracking_pids(after_snapshot, parent_pid)
                                    if new_pids:
                                        self.tracked_pids = new_pids
                                        self.log_callback(f"[{self.name}] Found {len(new_pids)} new process(es): {new_pids}")
                                
                                if self.tracked_pids:
                                    self.log_callback(f"[{self.name}] Tracking {len(self.tracked_pids)} child process(es): {self.tracked_pids}")
                                    self.process = None  # Clear parent process
                                    continue  # Continue monitoring children
                                else:
                                    self.log_callback(f"[{self.name}] No child processes found to track")
                            
                            self.log_callback(f"[{self.name}] Normal exit detected, stopping monitor")
                            self.should_run = False
                            break
                    
                    # Start the service
                    self.log_callback(f"[{self.name}] Starting service...")
                    self._set_profile_context(None)
                    
                    # If tracking children, take BEFORE snapshot
                    track_children = self.config.get('track_child_processes', False)
                    if track_children:
                        self.before_snapshot = self._take_process_snapshot(self.config.get('command', ''))
                        self.log_callback(f"[{self.name}] Before snapshot captured {len(self.before_snapshot)} running process(es)")
                    
                    try:
                        self.process = self.strategy.start(self.config)
                    except Exception as e:
                        self.log_callback(f"[{self.name}] Error starting service: {e}")
                        self.process = None
                    
                    if self.process:
                        self.last_start_time = datetime.now()
                        self._set_profile_context(self.config.get('_isolated_profile_path'))
                        self.log_callback(f"[{self.name}] Service started (PID: {self.process.pid})")
                        
                        # If tracking children, capture them using snapshot method
                        track_children = self.config.get('track_child_processes', False)
                        if track_children:
                            self.log_callback(f"[{self.name}] Starting snapshot-based child process capture...")
                            
                            # Start background thread for snapshot capture
                            # This runs in background to not block the main monitoring loop
                            capture_thread = threading.Thread(
                                target=self._snapshot_capture,
                                args=(self.process.pid, self.config.get('command', '')),
                                daemon=True
                            )
                            capture_thread.start()
                    else:
                        self.log_callback(f"[{self.name}] Failed to start service")
                        time.sleep(5)
                        continue
                
                time.sleep(check_interval)
                
            except Exception as e:
                self.log_callback(f"[{self.name}] Monitor error: {str(e)}")
                time.sleep(5)
    
    def _take_process_snapshot(self, exe_path):
        """
        Take a snapshot of all currently running processes.
        
        Args:
            exe_path: Full path to the executable (used for logging/context)
        
        Returns:
            Dict mapping PID -> lightweight process metadata captured at snapshot time
        """
        snapshot = {}
        
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'ppid']):
            try:
                info = proc.info
                snapshot[info['pid']] = {
                    'name': (info.get('name') or '').lower(),
                    'exe': (info.get('exe') or '').lower(),
                    'cmdline': [arg.lower() for arg in (info.get('cmdline') or [])],
                    'ppid': info.get('ppid'),
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
                continue
        
        return snapshot

    def _calculate_new_pids(self, after_snapshot):
        """Return the set of PIDs that appeared between BEFORE and AFTER snapshots."""
        if isinstance(self.before_snapshot, dict):
            before_keys = set(self.before_snapshot.keys())
        elif isinstance(self.before_snapshot, set):
            before_keys = set(self.before_snapshot)
        else:
            before_keys = set()
        
        return set(after_snapshot.keys()) - before_keys
    
    def _set_profile_context(self, path: Optional[str]):
        """Track the resolved profile path for snapshot filtering."""
        if path:
            self.profile_path = str(path)
            self.profile_flag = f"--user-data-dir={self.profile_path.lower()}"
        else:
            self.profile_path = None
            self.profile_flag = None
    
    def _cmdline_contains_profile(self, cmdline_args):
        if not self.profile_flag:
            return True
        if not cmdline_args:
            return False
        return any(self.profile_flag in (arg or '') for arg in cmdline_args)
    
    def _snapshot_entry_matches_profile(self, info):
        if not self.profile_flag:
            return True
        if not info:
            return False
        return self._cmdline_contains_profile(info.get('cmdline'))
    
    def _pid_matches_profile(self, pid, snapshot_data=None):
        if not self.profile_flag:
            return True
        
        if snapshot_data:
            info = snapshot_data.get(pid)
            if info and self._snapshot_entry_matches_profile(info):
                return True
        
        try:
            proc = psutil.Process(pid)
            return self._psutil_process_matches_profile(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return False
    
    def _psutil_process_matches_profile(self, proc):
        if not self.profile_flag:
            return True
        try:
            cmdline = [arg.lower() for arg in (proc.cmdline() or [])]
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return False
        return self._cmdline_contains_profile(cmdline)

    def _filter_candidate_processes(self, new_pids, snapshot_data, parent_pid):
        """Filter new processes using light-weight heuristics to avoid obvious false positives."""
        if not new_pids:
            return []
        
        exe_path = (self.config.get('command') or '').lower()
        exe_dir = os.path.dirname(exe_path)
        exe_name = os.path.basename(exe_path)
        exe_token = os.path.splitext(exe_name)[0]
        
        configured_names = [name.lower() for name in self.config.get('process_names', [])]
        exact_names = {name for name in configured_names if name}
        if exe_name:
            exact_names.add(exe_name)
        
        fuzzy_tokens = {os.path.splitext(name)[0] for name in exact_names if name}
        if exe_token:
            fuzzy_tokens.add(exe_token)
        
        try:
            ancestor_depth = int(self.config.get('snapshot_ancestor_depth', 10))
        except (TypeError, ValueError):
            ancestor_depth = 10
        ancestor_depth = max(1, ancestor_depth)
        
        filtered = []
        for pid in new_pids:
            info = snapshot_data.get(pid) or {}
            name = info.get('name') or ''
            exe = info.get('exe') or ''
            cmdline = ' '.join(info.get('cmdline') or [])
            ppid = info.get('ppid')
            parent_info = snapshot_data.get(ppid or -1) or {}
            
            if self.profile_flag:
                if not self._snapshot_entry_matches_profile(info) and not self._snapshot_entry_matches_profile(parent_info):
                    continue
            
            matches_parent = parent_pid is not None and ppid == parent_pid
            matches_new_parent = ppid in new_pids
            matches_exact = bool(name and name in exact_names)
            matches_token = any(token and token in name for token in fuzzy_tokens)
            matches_dir = bool(exe_dir and exe.startswith(exe_dir))
            matches_cmd = bool(exe_name and exe_name in cmdline)
            parent_name = (parent_info.get('name') or '').lower()
            parent_name_match = bool(parent_name and parent_name in exact_names)
            ancestor_match = self._has_matching_ancestor(pid, parent_pid, exact_names, ancestor_depth)
            
            if (
                matches_parent
                or matches_new_parent
                or matches_exact
                or matches_token
                or matches_dir
                or matches_cmd
                or parent_name_match
                or ancestor_match
            ):
                filtered.append(pid)
        
        return filtered
    
    def _has_matching_ancestor(self, pid, parent_pid, exact_names, depth_limit):
        """Return True if pid descends from parent_pid or an allowed executable name."""
        if depth_limit <= 0:
            return False
        
        try:
            proc = psutil.Process(pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return False
        
        depth = 0
        current = proc
        while current and depth < depth_limit:
            if parent_pid and current.pid == parent_pid:
                return self._psutil_process_matches_profile(current)
            try:
                name = current.name().lower()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                break
            if name in exact_names and self._psutil_process_matches_profile(current):
                return True
            try:
                current = current.parent()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                break
            depth += 1
        
        return False


    def _collect_descendant_pids(self, root_pids, snapshot_data=None):
        """Expand the PID list by including descendants of each root PID."""
        if not root_pids:
            return set()
        
        try:
            limit = int(self.config.get('snapshot_descendant_limit', 50))
        except (TypeError, ValueError):
            limit = 50
        limit = max(1, limit)
        
        collected = set()
        queue = deque(root_pids)
        
        while queue and len(collected) < limit:
            pid = queue.popleft()
            if pid in collected:
                continue
            
            if not self._pid_matches_profile(pid, snapshot_data):
                continue
            
            collected.add(pid)
            
            if len(collected) >= limit:
                break
            
            try:
                proc = psutil.Process(pid)
                if not self._psutil_process_matches_profile(proc):
                    continue
                for child in proc.children(recursive=False):
                    if child.pid not in collected and self._psutil_process_matches_profile(child):
                        queue.append(child.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return collected

    def _build_tracking_pids(self, after_snapshot, parent_pid):
        """
        Combine snapshot diff, filtering, and descendant expansion into a final PID list.
        """
        new_pids = self._calculate_new_pids(after_snapshot)
        if not new_pids:
            return []
        
        self.log_callback(f"[{self.name}] Snapshot diff: {len(new_pids)} new process(es) detected")
        filtered_pids = self._filter_candidate_processes(new_pids, after_snapshot, parent_pid)
        if filtered_pids and len(filtered_pids) != len(new_pids):
            self.log_callback(
                f"[{self.name}] Snapshot filter kept {len(filtered_pids)} candidate process(es)"
            )
        elif not filtered_pids:
            if self.profile_flag:
                self.log_callback(
                    f"[{self.name}] No profile-specific processes detected in snapshot diff"
                )
                return []
            filtered_pids = list(new_pids)
        
        expanded_pids = self._collect_descendant_pids(filtered_pids, after_snapshot)
        if expanded_pids and len(expanded_pids) > len(filtered_pids):
            self.log_callback(
                f"[{self.name}] Added {len(expanded_pids) - len(filtered_pids)} descendant process(es)"
            )
        
        final_pids = expanded_pids or set(filtered_pids)
        final_filtered = [
            pid for pid in final_pids
            if self._pid_matches_profile(pid, after_snapshot)
        ]
        return sorted(final_filtered)
    
    def _validate_process(self, pid, parent_pid, expected_args):
        """
        Validate that a process belongs to our launch (extensible for hybrid mode).
        
        Currently returns True (full snapshot mode). Can be extended to add:
        - Command-line argument validation
        - Parent-child relationship checking
        - Other safety checks
        
        Args:
            pid: Process ID to validate
            parent_pid: Original parent PID that launched the service
            expected_args: Expected command-line arguments
        
        Returns:
            True if process should be tracked, False otherwise
        """
        # Full snapshot mode: Accept all new processes
        # Future hybrid mode can add validation here:
        # 
        # try:
        #     proc = psutil.Process(pid)
        #     
        #     # Check if it's a descendant of parent
        #     current = proc
        #     while current.pid != 1:
        #         if current.pid == parent_pid:
        #             return True
        #         current = current.parent()
        #     
        #     # Check if command line contains our args
        #     cmdline = ' '.join(proc.cmdline()).lower()
        #     if expected_args and any(arg.lower() in cmdline for arg in expected_args):
        #         return True
        #         
        #     return False
        # except:
        #     return False
        
        return True  # Full snapshot mode: no validation
    
    def _snapshot_capture(self, parent_pid, exe_path):
        """
        Snapshot-based child process capture.
        Compares before/after snapshots to find new processes.
        
        Args:
            parent_pid: PID of the parent process
            exe_path: Path to the executable
        """
        try:
            # Wait for processes to spawn
            capture_duration = self.config.get('snapshot_capture_duration', 2.0)
            self.log_callback(f"[{self.name}] Waiting {capture_duration}s for processes to spawn...")
            time.sleep(capture_duration)
            
            # Optional short delay before taking the AFTER snapshot so new processes can settle
            settle_delay = self.config.get('snapshot_settle_delay', 3.0)
            if settle_delay > 0:
                time.sleep(settle_delay)

            # Take AFTER snapshot
            after_snapshot = self._take_process_snapshot(exe_path)
            self.log_callback(f"[{self.name}] After snapshot captured {len(after_snapshot)} running process(es)")
            
            new_pids = self._build_tracking_pids(after_snapshot, parent_pid)
            if not new_pids:
                self.log_callback(f"[{self.name}] No new processes detected in snapshot")
                return
            
            # Validate processes (extensible for hybrid mode)
            validated_pids = []
            expected_args = self.config.get('args', [])
            
            for pid in new_pids:
                if self._validate_process(pid, parent_pid, expected_args):
                    validated_pids.append(pid)
            
            # Update tracked PIDs
            if validated_pids:
                self.tracked_pids = validated_pids
                self.log_callback(
                    f"[{self.name}] Captured {len(validated_pids)} child process(es) "
                    f"via snapshot: {validated_pids}"
                )
            else:
                self.log_callback(f"[{self.name}] Warning: No validated processes to track")
                
        except Exception as e:
            self.log_callback(f"[{self.name}] Error in snapshot capture: {e}")
    
    def _is_process_alive(self) -> bool:
        """Check if the process or tracked children are still running"""
        # Check main process
        if self.process is not None:
            try:
                return psutil.pid_exists(self.process.pid) and self.process.poll() is None
            except Exception:
                return False
        
        # Check tracked child processes
        if self.tracked_pids:
            alive_pids = []
            for pid in self.tracked_pids:
                try:
                    if psutil.pid_exists(pid):
                        proc = psutil.Process(pid)
                        if proc.is_running() and self._psutil_process_matches_profile(proc):
                            alive_pids.append(pid)
                except Exception:
                    pass
            
            # Update tracked PIDs to only alive ones
            self.tracked_pids = alive_pids
            return len(alive_pids) > 0
        
        return False
    
    def _kill_process(self):
        """Kill the process and all its children"""
        # Kill main process and its children
        if self.process is not None:
            try:
                parent = psutil.Process(self.process.pid)
                children = parent.children(recursive=True)
                
                # Kill children first
                for child in children:
                    try:
                        child.kill()
                    except Exception:
                        pass
                
                # Kill parent
                try:
                    parent.kill()
                except Exception:
                    pass
                
                # Wait for process to terminate
                try:
                    self.process.wait(timeout=5)
                except Exception:
                    pass
                    
            except psutil.NoSuchProcess:
                pass
            except Exception as e:
                self.log_callback(f"[{self.name}] Error killing process: {str(e)}")
            
            self.process = None
        
        # Kill tracked child processes
        if self.tracked_pids:
            self.log_callback(f"[{self.name}] Stopping {len(self.tracked_pids)} tracked process(es)")
            for pid in self.tracked_pids:
                try:
                    proc = psutil.Process(pid)
                    if self.profile_flag and not self._psutil_process_matches_profile(proc):
                        continue
                    # Kill its children first
                    for child in proc.children(recursive=True):
                        if self.profile_flag and not self._psutil_process_matches_profile(child):
                            continue
                        try:
                            child.kill()
                        except Exception:
                            pass
                    # Kill the process
                    proc.kill()
                except Exception:
                    pass
            
            self.tracked_pids = []
        
        self._set_profile_context(None)
    
    def _log_crash_event(self):
        """Log crash event to crash log file"""
        self.crash_count += 1
        crash_time = datetime.now()
        
        # Calculate uptime
        uptime = "Unknown"
        if self.last_start_time:
            uptime_delta = crash_time - self.last_start_time
            uptime = str(uptime_delta).split('.')[0]  # Remove microseconds
        
        # Get exit code if available
        exit_code = "Unknown"
        if self.process:
            try:
                exit_code = self.process.poll()
                if exit_code is None:
                    exit_code = "Process killed"
            except Exception:
                pass
        
        # Create crash event message
        crash_message = (
            f"\n{'='*80}\n"
            f"CRASH EVENT #{self.crash_count}\n"
            f"{'='*80}\n"
            f"Timestamp:     {crash_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Service:       {self.name}\n"
            f"Type:          {self.config.get('type', 'unknown')}\n"
            f"PID:           {self.process.pid if self.process else 'Unknown'}\n"
            f"Exit Code:     {exit_code}\n"
            f"Uptime:        {uptime}\n"
            f"Started At:    {self.last_start_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_start_time else 'Unknown'}\n"
            f"Command:       {self.config.get('command', 'Unknown')}\n"
            f"{'='*80}\n"
        )
        
        # Log to callback (GUI)
        self.log_callback(f"[{self.name}] CRASH DETECTED! (Crash #{self.crash_count}) - Auto-restarting...")
        
        # Write to crash log file
        try:
            self.crash_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.crash_log_path, 'a', encoding='utf-8') as f:
                f.write(crash_message)
        except Exception as e:
            self.log_callback(f"[{self.name}] Error writing crash log: {str(e)}")

