# Watchdogd Development Environment Launcher v2.0

A dynamic, configurable service management application with automatic restart capabilities for Windows.

## Features

- **Dynamic Service Management**: Add, edit, and remove services at runtime through a GUI
- **Multiple Service Types**: Support for executables, NPM scripts, and PowerShell scripts
- **Auto-Restart**: Automatically restart services if they crash
- **Crash Logging**: Track service crashes with detailed logs
- **Startup Ordering**: Control service startup order and delays
- **Persistent Configuration**: JSON-based configuration stored in user profile
- **Environment Variables**: Support for custom environment variables per service
- **Optional Browser Auto-Launch**: Toggle automatic browser opening on startup with a single checkbox

## Installation

1. Install Python 3.8 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Application

```bash
python watchdogd-launcher.py
```

Or build an executable using PyInstaller:
```bash
pyinstaller watchdogd-launcher.spec
```

### First Run

On first run, the application will create a configuration file at:
```
%USERPROFILE%\.watchdogd_launcher\config.json
```

You can start with no services configured and add them through the GUI, or copy the example configuration from `config/default_config.json`.

### Managing Services

1. Click **Manage Services** button or use **File > Manage Services** menu
2. In the Service Manager dialog:
   - **Add Service**: Create a new service configuration
   - **Edit Service**: Modify an existing service
   - **Duplicate**: Create a copy of a service
   - **Remove Service**: Delete a service
   - **Move Up/Down**: Reorder services (affects startup order)
   - **Toggle Enabled**: Enable or disable a service
3. Click **Save Changes** to persist your configuration

### Service Types

#### Executable (.exe)
Run standalone executable files.
- **Command**: Full path to .exe file
- **Arguments**: Command-line arguments (space-separated)
- **Workspace**: Not used

#### NPM/PNPM Script
Run npm, pnpm, or yarn commands.
- **Command**: The npm command (e.g., `pnpm dev`, `npm start`)
- **Workspace**: Path to project directory containing package.json
- **Arguments**: Not used (include in command)

#### PowerShell Script (.ps1)
Run PowerShell scripts.
- **Command**: Full path to .ps1 file
- **Arguments**: Script arguments (space-separated)
- **Workspace**: Working directory (optional, defaults to script directory)

### Service Options

All services support these options:

- **Service Name**: Display name in the GUI
- **Enabled**: Whether to start the service
- **Auto-restart on crash**: Automatically restart if the service crashes
- **Startup Delay**: Seconds to wait before starting (useful for dependencies)

### Environment Variables

You can set custom environment variables for each service. Use `${VAR_NAME}` syntax to reference system environment variables:

```json
"environment": {
  "NODE_ENV": "development",
  "API_KEY": "${MY_API_KEY}"
}
```

## Project Structure

```
LiveInstall_StartupAutomation/
├── watchdogd_launcher/           # Main package
│   ├── __init__.py
│   ├── main.py               # Application entry point
│   ├── config_manager.py     # Configuration management
│   ├── service_manager.py    # Service lifecycle management
│   ├── service_definitions.py # Service strategy implementations
│   ├── gui/                  # GUI components
│   │   ├── __init__.py
│   │   ├── main_window.py    # Main application window
│   │   ├── settings_dialog.py # Service management dialog
│   │   └── service_editor.py  # Service add/edit dialog
│   └── utils/                # Utility modules
│       ├── __init__.py
│       ├── logger.py         # Logging utilities
│       └── process_utils.py  # Process management helpers
├── config/                   # Example configurations
│   ├── default_config.json   # Example service configuration
│   └── README.md            # Configuration documentation
├── watchdogd-launcher.py        # Entry point script
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## Configuration File Location

User configuration is stored at:
```
%USERPROFILE%\.watchdogd_launcher\config.json
```

Logs are stored at:
```
%USERPROFILE%\.watchdogd_launcher\logs\
```

## Design Patterns

The application uses several design patterns for maintainability:

- **Strategy Pattern**: Different service execution strategies (executable, npm, PowerShell)
- **Factory Pattern**: ServiceStrategyFactory creates appropriate strategies
- **Repository Pattern**: ConfigManager acts as data access layer
- **Observer Pattern**: Log callbacks for event notification
- **MVC Pattern**: Separation of GUI, business logic, and data

## Building Executable

To create a standalone executable:

```bash
pyinstaller watchdogd-launcher.spec
```

The executable will be created in the `dist/` directory.

## Migration from v1.x

If you have the old `watchdogd-launcher.old.py` file:

1. Run the new application
2. Click **Manage Services**
3. Add your services using the GUI
4. The old hardcoded configuration is now dynamic and stored in your user profile

## Troubleshooting

### Services not starting
- Check the Activity Log for error messages
- Verify paths in service configuration are correct
- Ensure you have necessary permissions
- Check crash logs at `%USERPROFILE%\.watchdogd_launcher\logs\crash_events.log`

### Configuration not saving
- Verify you have write permissions to `%USERPROFILE%\.watchdogd_launcher\`
- Check for JSON syntax errors in manual edits

### Application won't start
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (3.8+ required)

## License

This project is for internal use.

## Version History

### v2.0.0
- Complete refactor to modular architecture
- Dynamic service management through GUI
- JSON-based persistent configuration
- Multiple service type support
- Environment variable support
- Improved crash logging
- Strategy pattern implementation

### v1.0.0
- Initial version with hardcoded services
