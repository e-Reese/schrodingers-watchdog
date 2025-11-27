# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Watchdogd Launcher (cross-platform)

import sys
from pathlib import Path

block_cipher = None

project_root = Path(__name__).parent
config_dir = project_root / 'config'

datas = [
    (str(config_dir / 'example_config.json'), 'config'),
    (str(config_dir / 'README.md'), 'config'),
]

# Detect platform
is_macos = sys.platform == 'darwin'
is_windows = sys.platform == 'win32'

a = Analysis(
    ['watchdogd-launcher.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'psutil',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Watchdogd-Launcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=is_macos,  # Enable argv emulation on macOS for drag-and-drop
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Create .app bundle on macOS
if is_macos:
    app = BUNDLE(
        exe,
        name='Watchdogd-Launcher.app',
        icon=None,
        bundle_identifier='com.watchdogd-launcher',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
            'CFBundleShortVersionString': '2.0.0',
            'CFBundleVersion': '2.0.0',
        },
    )
