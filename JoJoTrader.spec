# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

# Collect all resources for problematic libraries to avoid missing dependencies
datas = []
binaries = []
hiddenimports = ['PySide6', 'mplfinance', 'plotly', 'pandas', 'jojo_trading', '_cffi_backend']

# Robustly collect everything for Shioaji, NaCl, and Filelock
for lib in ['shioaji', 'nacl', 'filelock', 'pyrsca', 'base58']:
    tmp_ret = collect_all(lib)
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]

a = Analysis(
    ['src/jojo_trader/main_desktop.py'],
    pathex=['d:/Workspace/dev_projects/trading/jojo_trading/src'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['streamlit', 'altair', 'tornado', 'pydeck', 'watchdog', 'nbformat', 'ipython', 'jedi', 'tkinter'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='JoJoTrader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='JoJoTrader',
)
