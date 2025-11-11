"""Process management utilities"""

import psutil
from typing import List


def kill_processes_by_name(process_names: List[str]) -> int:
    """
    Kill all processes matching the given names.
    Returns the number of processes killed.
    """
    killed_count = 0
    
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] in process_names:
                psutil.Process(proc.info['pid']).kill()
                killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    return killed_count


def get_process_info(pid: int) -> dict:
    """Get information about a process by PID"""
    try:
        proc = psutil.Process(pid)
        return {
            'pid': pid,
            'name': proc.name(),
            'status': proc.status(),
            'cpu_percent': proc.cpu_percent(interval=0.1),
            'memory_mb': proc.memory_info().rss / 1024 / 1024,
            'create_time': proc.create_time()
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


def is_process_running(pid: int) -> bool:
    """Check if a process with the given PID is running"""
    return psutil.pid_exists(pid)

