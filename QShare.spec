# -*- mode: python ; coding: utf-8 -*-

import os

# Ensure the correct path for the icon
icon_path = os.path.abspath("res/app_icon.ico")

a = Analysis(
    ['QShare.py'],
    pathex=[],
    binaries=[],
    datas=[('res/app_icon.ico', 'res'), ('res/app_logo.png', 'res'),('res/Roboto-Black.ttf', 'res')],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='QShare',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # False ensures a GUI application, set True for console mode
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,  # Corrected icon path
)
