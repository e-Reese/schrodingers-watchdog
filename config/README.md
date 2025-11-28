# Configuration Files

This directory contains example configuration files for Watchdogd Launcher.

## User Configuration

Your personal configuration is stored at:

**Windows:** `%USERPROFILE%\.watchdogd_launcher\config.json`

**macOS/Linux:** `~/.watchdogd_launcher/config.json`

## Default Configuration

The `default_config.json` file in this directory is an example configuration with sample services. You can use this as a reference when creating your own services.

## Service Types

The launcher supports four types of services:

### 1. Executable
Run standalone executable files
- **type**: `executable`
- **command**: Full path to executable file
  - **Windows**: `.exe` files (e.g., `C:\Program Files\App\app.exe`)
  - **macOS**: 
    - `.app` bundles (e.g., `/Applications/Visual Studio Code.app`)
    - Direct executables inside .app (e.g., `/Applications/Visual Studio Code.app/Contents/MacOS/Electron`)
    - Unix executables (no extension, e.g., `/usr/local/bin/myapp`)
  - **Linux**: Unix executables (no extension)
- **args**: Array of command-line arguments
- **workspace**: Not used (leave empty)
- **Important for macOS**: 
  - .app bundles with isolated profiles or child process tracking are launched directly via their internal executable for better control
  - .app bundles without these features use the `open` command for standard macOS behavior
  - Unix executables must have execute permissions. Run `chmod +x /path/to/file` if needed.

### 2. NPM Script
Run npm, pnpm, or yarn commands
- **type**: `npm_script`
- **command**: The npm command (e.g., "pnpm dev", "npm start")
- **args**: Not used (include in command string)
- **workspace**: Path to project directory

### 3. PowerShell Script
Run PowerShell .ps1 scripts (Windows only)
- **type**: `powershell_script`
- **command**: Full path to .ps1 file
- **args**: Array of script arguments
- **workspace**: Working directory for script (optional, defaults to script directory)
- **Platform**: Windows only
- **Example**: `C:\Scripts\setup.ps1`

### 4. Shell Script
Run bash/shell .sh scripts (macOS/Linux only)
- **type**: `shell_script`
- **command**: Full path to .sh file
- **args**: Array of script arguments
- **workspace**: Working directory for script (optional, defaults to script directory)
- **Platform**: macOS/Linux only
- **Example**: `/home/user/scripts/setup.sh`
- **Note**: Script does not need execute permissions (runs via bash interpreter)

## Optional Browser Launching

The example configuration includes a Chrome browser service that is **disabled by default**. This is completely optional.

To use browser launching:
1. Enable the Chrome service in your configuration
2. Change the URL in the `args` array to your desired URL (default is `http://localhost:3000`)
3. Adjust the `startup_delay` to ensure your services start before the browser opens
4. The browser will open automatically when you start services

**Windows Example:**
```json
{
  "name": "Chrome Browser",
  "type": "executable",
  "enabled": true,
  "command": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "args": ["--new-window", "http://localhost:3000"],
  "startup_delay": 10
}
```

**macOS Example (using .app bundle):**
```json
{
  "name": "Visual Studio Code",
  "type": "executable",
  "enabled": true,
  "command": "/Applications/Visual Studio Code.app",
  "args": ["."],
  "startup_delay": 0,
  "track_child_processes": true,
  "use_unique_profile": true,
  "min_uptime_for_crash": 0
}
```

This configuration will:
- Launch VS Code directly from its internal executable (not via `open`)
- Track all child processes spawned by VS Code
- Use an isolated profile in `~/.watchdogd_launcher/profiles/visual-studio-code`
- Not treat quick exits as crashes (VS Code may redirect to existing instances)

**macOS Example (using direct executable):**
```json
{
  "name": "Chrome Browser",
  "type": "executable",
  "enabled": true,
  "command": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "args": ["--new-window", "http://localhost:3000"],
  "startup_delay": 10
}
```

**Unix Executable Example:**
```json
{
  "name": "Custom Server",
  "type": "executable",
  "enabled": true,
  "command": "/usr/local/bin/myserver",
  "args": ["--port", "8080"],
  "startup_delay": 0
}
```

You can also use other browsers by changing the command path:
- **Windows:** Edge, Firefox, etc.
- **macOS:** Safari (`/Applications/Safari.app/Contents/MacOS/Safari`), Firefox, etc.

## Common Service Options

All services support these options:
- **name**: Display name for the service
- **enabled**: Whether the service should start (true/false)
- **auto_restart**: Automatically restart if the service crashes (true/false)
- **startup_delay**: Seconds to wait before starting (useful for dependencies)
- **min_uptime_for_crash**: Minimum seconds a process must run before an exit is considered a crash (default: 0)
- **track_child_processes**: Monitor child processes after parent exits (default: false)
- **snapshot_capture_duration**: How long to wait for snapshot capture in seconds (default: 2.0)
- **process_names**: Additional process names to search for when tracking children (optional, array of strings)
- **environment**: Custom environment variables (key-value pairs)

### Important: min_uptime_for_crash

This setting prevents false crash detection for applications that:
- Redirect to existing instances (browsers, editors)
- Exit immediately with success code 0

**Recommended values:**
- **0** for browsers (Chrome, Edge, Firefox) and editors (VS Code, Notepad++) - they redirect to existing instances
- **10** for servers and long-running services - actual crashes should be detected
- **5** for quick startup utilities that might legitimately exit early

If a process exits within `min_uptime_for_crash` seconds with exit code 0, it's logged as "normal exit" rather than a crash.

### Important: track_child_processes

This setting enables tracking of child processes spawned by applications like browsers and editors.

**macOS .app Bundle Behavior:**
When using `.app` bundles with `track_child_processes` or `use_unique_profile` enabled, the launcher automatically finds and executes the actual binary inside the .app bundle (e.g., `/Applications/Visual Studio Code.app/Contents/MacOS/Electron`). This provides better control over arguments and ensures all child processes with the isolated profile are properly tracked.

**How it works (Snapshot Mode):**
1. Takes a BEFORE snapshot of all running processes before launching the service
2. Launches the service
3. Waits 2 seconds for all child processes to spawn
4. Takes an AFTER snapshot of all running processes
5. Compares BEFORE and AFTER to identify new processes created by the launch
6. Tracks all new processes, continuing to monitor them
7. When all tracked processes exit, the service stops

**Advantages:**
- Captures ALL processes, not just parent-child relationships
- Works with complex multi-process architectures (browsers, IDEs)
- No timing issues or race conditions during capture
- Simple and reliable

**When to use:**
- **Browsers** (Chrome, Edge, Firefox, Safari) - The launcher starts, passes the URL to an existing browser process, then exits
- **Editors** (VS Code, Sublime, TextEdit) - The launcher redirects to an existing window, then exits
- **Any app that spawns a child and exits immediately**

**Benefits:**
- Monitor and restart browsers if they crash
- Get notified when browsers are closed
- Track actual application lifetime, not just launcher lifetime

**Example:**
```json
{
  "name": "Microsoft Edge",
  "min_uptime_for_crash": 0,
  "track_child_processes": true,
  "auto_restart": true
}
```

With these settings:
1. Edge launcher starts and immediately spawns child processes
2. Aggressive polling captures children within 50-100ms
3. Launcher exits with code 0 after ~1 second
4. Child processes continue to be monitored
5. If browser crashes, it can be restarted (if auto_restart enabled)
6. When you close the browser, the service stops

### Advanced: snapshot_capture_duration

Controls how long to wait between BEFORE and AFTER snapshots. Default is 2.0 seconds.

**When to adjust:**
- **Increase (3-5s)** for slow-starting applications with many processes
- **Decrease (1.0s)** for fast-starting simple applications
- Most applications work fine with the 2 second default

**Example:**
```json
{
  "name": "Heavy Application",
  "track_child_processes": true,
  "snapshot_capture_duration": 4.0
}
```

### Advanced: process_names

This optional setting is for applications that spawn processes with different names than the launcher.

**When to use:**
- The launcher executable name differs from the actual running process
- The application spawns multiple different process types
- You need to track specific helper processes

**Example:**
```json
{
  "name": "My Custom App",
  "command": "C:\\Path\\to\\launcher.exe",
  "track_child_processes": true,
  "process_names": ["actual-app.exe", "helper.exe"]
}
```

In most cases, you do not need this setting. The launcher automatically detects child processes using snapshot comparison.

### Extensibility: Future Hybrid Mode

The snapshot capture system is designed to be extensible. A future "hybrid mode" can add validation:
- Command-line argument matching to verify processes belong to your launch
- Parent-child relationship checking for additional safety
- Configurable validation rules

The validation logic is centralized in the `_validate_process()` method, making it easy to add these features without rewriting the capture system.

## Environment Variable Substitution

You can reference system environment variables in the environment section:
```json
"environment": {
  "API_KEY": "${MY_API_KEY}"
}
```

This will use the value of the MY_API_KEY environment variable from your system.

