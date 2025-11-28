"""Service execution strategies using Strategy Pattern"""

from abc import ABC, abstractmethod
import subprocess
import os
import plistlib
import re
from pathlib import Path
from typing import Optional, Dict, Any, Tuple


class ServiceStrategy(ABC):
    """Abstract base class for service execution strategies"""
    
    @abstractmethod
    def start(self, config: Dict[str, Any]) -> Optional[subprocess.Popen]:
        """Start the service based on its configuration"""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate service configuration. Returns (is_valid, error_message)"""
        pass


class ExecutableServiceStrategy(ServiceStrategy):
    """Strategy for running executable files"""
    
    def start(self, config: Dict[str, Any]) -> Optional[subprocess.Popen]:
        command_path = config.get('command', '')
        if not os.path.exists(command_path):
            return None
        
        args = list(config.get('args', []))
        profile_args = self._build_profile_args(config, command_path, args)
        if profile_args:
            args = profile_args + args
        
        env = self._prepare_environment(config)
        
        # On macOS, handle .app bundles
        if os.name != 'nt' and command_path.endswith('.app'):
            # If we have profile args or need to track child processes, 
            # launch the executable directly from inside the .app bundle
            # for better control and process tracking
            if profile_args or config.get('track_child_processes', False):
                executable_path = self._find_executable_in_app_bundle(command_path)
                if executable_path:
                    cmd = [executable_path] + args
                else:
                    # Fallback to open command if we can't find the executable
                    cmd = ['open', '-a', command_path]
                    if args:
                        cmd.extend(['--args'] + args)
            else:
                # Use open command for simpler cases
                cmd = ['open', '-a', command_path]
                if args:
                    cmd.extend(['--args'] + args)
        else:
            cmd = [command_path] + args
        
        try:
            return subprocess.Popen(cmd, env=env)
        except Exception as e:
            print(f"Error starting executable: {e}")
            return None
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        if not config.get('command'):
            return False, "Executable path is required"
        command_path = config['command']
        if not os.path.exists(command_path):
            return False, f"Executable not found: {command_path}"
        
        # On Unix systems, check if file is executable (but skip check for .app bundles)
        if os.name != 'nt' and not command_path.endswith('.app'):
            if os.path.isdir(command_path):
                return False, f"Path is a directory, not an executable: {command_path}"
            if not os.access(command_path, os.X_OK):
                return False, f"File is not executable: {command_path}. Run: chmod +x {command_path}"
        
        # For .app bundles on macOS, verify it's a directory
        if os.name != 'nt' and command_path.endswith('.app'):
            if not os.path.isdir(command_path):
                return False, f"Invalid .app bundle: {command_path}"
        
        return True, ""
    
    def _prepare_environment(self, config: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Prepare environment variables for the process"""
        custom_env = config.get('environment', {})
        if not custom_env:
            return None
        
        # Merge custom environment with system environment
        env = os.environ.copy()
        for key, value in custom_env.items():
            # Support environment variable substitution
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                env_var_name = value[2:-1]
                env[key] = os.environ.get(env_var_name, '')
            else:
                env[key] = str(value)
        
        return env
    
    def _build_profile_args(self, config: Dict[str, Any], command_path: str, existing_args: list) -> list:
        """Inject --user-data-dir when unique browser profiles are requested."""
        use_unique_profile = config.get('use_unique_profile')
        if use_unique_profile is None:
            use_unique_profile = True
        if not use_unique_profile:
            config.pop('_isolated_profile_path', None)
            return []
        
        if any(isinstance(arg, str) and arg.startswith('--user-data-dir') for arg in existing_args):
            return []
        
        base_dir = config.get('profile_base_dir') or str(Path.home() / '.watchdogd_launcher' / 'profiles')
        profile_name = config.get('name') or Path(command_path).stem or 'service'
        safe_name = re.sub(r'[^a-z0-9._-]+', '-', profile_name.lower()).strip('-_.')
        if not safe_name:
            safe_name = 'service'
        
        profile_path = (Path(base_dir).expanduser() / safe_name).resolve()
        try:
            profile_path.mkdir(parents=True, exist_ok=True)
        except Exception:
            config.pop('_isolated_profile_path', None)
            return []
        
        profile_str = str(profile_path)
        config['_isolated_profile_path'] = profile_str
        return [f"--user-data-dir={profile_str}"]
    
    def _find_executable_in_app_bundle(self, app_path: str) -> Optional[str]:
        """Find the actual executable inside a macOS .app bundle."""
        try:
            # Read Info.plist to get the executable name
            info_plist_path = Path(app_path) / 'Contents' / 'Info.plist'
            if info_plist_path.exists():
                with open(info_plist_path, 'rb') as f:
                    plist_data = plistlib.load(f)
                    executable_name = plist_data.get('CFBundleExecutable')
                    if executable_name:
                        executable_path = Path(app_path) / 'Contents' / 'MacOS' / executable_name
                        if executable_path.exists():
                            return str(executable_path)
            
            # Fallback: try to find any executable in Contents/MacOS/
            macos_dir = Path(app_path) / 'Contents' / 'MacOS'
            if macos_dir.exists():
                for item in macos_dir.iterdir():
                    if item.is_file() and os.access(str(item), os.X_OK):
                        return str(item)
        except Exception as e:
            print(f"Error finding executable in .app bundle: {e}")
        
        return None


class NPMScriptServiceStrategy(ServiceStrategy):
    """Strategy for running npm/pnpm/yarn scripts"""
    
    def start(self, config: Dict[str, Any]) -> Optional[subprocess.Popen]:
        workspace = config.get('workspace', '')
        if not workspace or not os.path.exists(workspace):
            return None
        
        command = config.get('command', '')
        if not command:
            return None
        
        env = self._prepare_environment(config)
        
        try:
            kwargs = {'cwd': workspace, 'shell': True, 'env': env}
            if os.name == 'nt':
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
            return subprocess.Popen(command, **kwargs)
        except Exception as e:
            print(f"Error starting npm script: {e}")
            return None
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        if not config.get('workspace'):
            return False, "Workspace directory is required"
        if not os.path.exists(config['workspace']):
            return False, f"Workspace not found: {config['workspace']}"
        if not config.get('command'):
            return False, "Command is required"
        return True, ""
    
    def _prepare_environment(self, config: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Prepare environment variables for the process"""
        custom_env = config.get('environment', {})
        if not custom_env:
            return None
        
        env = os.environ.copy()
        for key, value in custom_env.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                env_var_name = value[2:-1]
                env[key] = os.environ.get(env_var_name, '')
            else:
                env[key] = str(value)
        
        return env


class PowerShellScriptServiceStrategy(ServiceStrategy):
    """Strategy for running PowerShell scripts"""
    
    def start(self, config: Dict[str, Any]) -> Optional[subprocess.Popen]:
        script_path = config.get('command', '')
        if not os.path.exists(script_path):
            return None
        
        workspace = config.get('workspace', '')
        if not workspace:
            workspace = os.path.dirname(script_path)
        
        args = config.get('args', [])
        args_str = ' '.join([f'"{arg}"' if ' ' in arg else arg for arg in args])
        
        cmd = f'powershell -ExecutionPolicy Bypass -File "{script_path}" {args_str}'.strip()
        env = self._prepare_environment(config)
        
        try:
            kwargs = {'cwd': workspace, 'shell': True, 'env': env}
            if os.name == 'nt':
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
            return subprocess.Popen(cmd, **kwargs)
        except Exception as e:
            print(f"Error starting PowerShell script: {e}")
            return None
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        if not config.get('command'):
            return False, "Script path is required"
        if not os.path.exists(config['command']):
            return False, f"Script not found: {config['command']}"
        return True, ""
    
    def _prepare_environment(self, config: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Prepare environment variables for the process"""
        custom_env = config.get('environment', {})
        if not custom_env:
            return None
        
        env = os.environ.copy()
        for key, value in custom_env.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                env_var_name = value[2:-1]
                env[key] = os.environ.get(env_var_name, '')
            else:
                env[key] = str(value)
        
        return env


class ShellScriptServiceStrategy(ServiceStrategy):
    """Strategy for running shell scripts (.sh) on macOS/Linux"""
    
    def start(self, config: Dict[str, Any]) -> Optional[subprocess.Popen]:
        script_path = config.get('command', '')
        if not os.path.exists(script_path):
            return None
        
        workspace = config.get('workspace', '')
        if not workspace:
            workspace = os.path.dirname(script_path)
        
        args = config.get('args', [])
        args_str = ' '.join([f'"{arg}"' if ' ' in arg else arg for arg in args])
        
        cmd = f'/bin/bash "{script_path}" {args_str}'.strip()
        env = self._prepare_environment(config)
        
        try:
            kwargs = {'cwd': workspace, 'shell': True, 'env': env}
            if os.name == 'nt':
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
            return subprocess.Popen(cmd, **kwargs)
        except Exception as e:
            print(f"Error starting shell script: {e}")
            return None
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        if not config.get('command'):
            return False, "Script path is required"
        if not os.path.exists(config['command']):
            return False, f"Script not found: {config['command']}"
        return True, ""
    
    def _prepare_environment(self, config: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Prepare environment variables for the process"""
        custom_env = config.get('environment', {})
        if not custom_env:
            return None
        
        env = os.environ.copy()
        for key, value in custom_env.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                env_var_name = value[2:-1]
                env[key] = os.environ.get(env_var_name, '')
            else:
                env[key] = str(value)
        
        return env


class ServiceStrategyFactory:
    """Factory for creating service strategies"""
    
    _strategies = {
        'executable': ExecutableServiceStrategy,
        'npm_script': NPMScriptServiceStrategy,
        'powershell_script': PowerShellScriptServiceStrategy,
        'shell_script': ShellScriptServiceStrategy
    }
    
    @classmethod
    def create(cls, service_type: str) -> ServiceStrategy:
        """Create a service strategy based on type"""
        strategy_class = cls._strategies.get(service_type)
        if not strategy_class:
            raise ValueError(f"Unknown service type: {service_type}")
        return strategy_class()
    
    @classmethod
    def get_available_types(cls) -> list:
        """Get list of available service types"""
        return list(cls._strategies.keys())
    
    @classmethod
    def get_type_display_names(cls) -> Dict[str, str]:
        """Get human-readable names for service types"""
        return {
            'executable': 'Executable',
            'npm_script': 'NPM/PNPM Script',
            'powershell_script': 'PowerShell Script (.ps1)',
            'shell_script': 'Shell Script (.sh)'
        }

