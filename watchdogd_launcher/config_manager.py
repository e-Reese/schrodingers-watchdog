"""Configuration management with JSON persistence"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import copy


class ConfigManager:
    """Manages application configuration with persistence"""
    
    DEFAULT_CONFIG = {
        'app_settings': {
            'check_interval': 5,
            'auto_open_browser': False,
            'browser_delay': 8,
            'crash_log_enabled': True,
            'frontend_url': 'http://localhost:3000/'
        },
        'services': []
    }
    
    SERVICE_TEMPLATE = {
        'name': '',
        'type': 'executable',
        'enabled': True,
        'auto_restart': True,
        'workspace': '',
        'command': '',
        'args': [],
        'startup_delay': 0,
        'min_uptime_for_crash': 0,
        'track_child_processes': False,
        'use_unique_profile': True,
        'profile_base_dir': '',
        'health_check_url': None,
        'environment': {}
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path.home() / '.watchdogd_launcher' / 'config.json'
        
        self.config_path = config_path
        self.config = None
        self.load()
    
    def load(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                self._validate_config()
                return self.config
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.")
                self.config = copy.deepcopy(self.DEFAULT_CONFIG)
        else:
            self.config = copy.deepcopy(self.DEFAULT_CONFIG)
            self.save()
        
        return self.config
    
    def save(self) -> bool:
        """Save configuration to file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def _validate_config(self):
        """Ensure config has required structure"""
        if 'app_settings' not in self.config:
            self.config['app_settings'] = copy.deepcopy(self.DEFAULT_CONFIG['app_settings'])
        else:
            # Merge with defaults to ensure all keys exist
            for key, value in self.DEFAULT_CONFIG['app_settings'].items():
                if key not in self.config['app_settings']:
                    self.config['app_settings'][key] = value
        
        if 'services' not in self.config:
            self.config['services'] = []
    
    def get_services(self) -> List[Dict[str, Any]]:
        """Get list of configured services"""
        return self.config.get('services', [])
    
    def add_service(self, service_config: Dict[str, Any]) -> bool:
        """Add a new service configuration"""
        self.config['services'].append(service_config)
        return self.save()
    
    def update_service(self, index: int, service_config: Dict[str, Any]) -> bool:
        """Update an existing service configuration"""
        if 0 <= index < len(self.config['services']):
            self.config['services'][index] = service_config
            return self.save()
        return False
    
    def remove_service(self, index: int) -> bool:
        """Remove a service configuration"""
        if 0 <= index < len(self.config['services']):
            del self.config['services'][index]
            return self.save()
        return False
    
    def move_service(self, from_index: int, to_index: int) -> bool:
        """Move a service to a different position (for startup order)"""
        if 0 <= from_index < len(self.config['services']) and 0 <= to_index < len(self.config['services']):
            service = self.config['services'].pop(from_index)
            self.config['services'].insert(to_index, service)
            return self.save()
        return False
    
    def get_app_setting(self, key: str, default=None):
        """Get an application setting"""
        return self.config.get('app_settings', {}).get(key, default)
    
    def set_app_setting(self, key: str, value: Any) -> bool:
        """Set an application setting"""
        if 'app_settings' not in self.config:
            self.config['app_settings'] = {}
        self.config['app_settings'][key] = value
        return self.save()
    
    def get_log_dir(self) -> Path:
        """Get the log directory path"""
        return self.config_path.parent / 'logs'
    
    def get_crash_log_file(self) -> Path:
        """Get the crash log file path"""
        return self.get_log_dir() / 'crash_events.log'
    
    def export_config(self, export_path: Path) -> bool:
        """Export configuration to a file"""
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting config: {e}")
            return False
    
    def import_config(self, import_path: Path) -> bool:
        """Import configuration from a file"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            self.config = imported_config
            self._validate_config()
            return self.save()
        except Exception as e:
            print(f"Error importing config: {e}")
            return False

