# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Watchdogd Launcher

from pathlib import Path

block_cipher = None

project_root = Path(__name__).parent
config_dir = project_root / 'config'

datas = [
    (str(config_dir / 'example_config.json'), 'config'),
    (str(config_dir / 'README.md'), 'config'),
]

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
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
