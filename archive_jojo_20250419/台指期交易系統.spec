# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    datas=[('credentials\\.env', 'credentials')],
    hiddenimports=['nacl', 'nacl.bindings', 'nacl.encoding', 'nacl.public', 'nacl.signing', 'nacl.secret', 'nacl.utils', 'nacl.pwhash', 'nacl.hash', 'nacl.exceptions', 'pyrsca', 'requests', 'urllib3', 'charset_normalizer', 'idna', 'certifi', 'filelock', 'unittest', 'unittest.mock', 'unittest.case', 'base58', 'shioaji.common', 'shioaji.backend', 'shioaji.backend.solace', 'shioaji.backend.solace.api', 'shioaji.backend.solace.utils', 'shioaji.error', 'shioaji.contracts', 'shioaji.order', 'shioaji.position', 'shioaji.account', 'shioaji.constant', 'shioaji.utils', 'python-dotenv', 'PyQt6.QtCore', 'PyQt6.QtWidgets', 'PyQt6.QtGui', 'matplotlib', 'mplfinance', 'pandas', 'numpy'],
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
    [],
    exclude_binaries=True,
    name='台指期交易系統',
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
    name='台指期交易系統',
)
