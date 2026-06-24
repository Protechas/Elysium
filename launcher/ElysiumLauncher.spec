# -*- mode: python ; coding: utf-8 -*-
# Build with: .\build.ps1
# Produces dist\ELYSIUM.exe — replacement for the legacy Desktop bootstrap.

import os

launcher_dir = SPECPATH
repo_dir = os.path.dirname(SPECPATH)

block_cipher = None

a = Analysis(
    [os.path.join(launcher_dir, 'elysium_launcher.py')],
    pathex=[repo_dir],
    binaries=[],
    datas=[(os.path.join(launcher_dir, 'stop-flow.ps1'), 'launcher')],
    hiddenimports=['elysium.bootstrap.repo_sync'],
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
    name='ELYSIUM',
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
