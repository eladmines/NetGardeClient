# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for NetGarde menu bar .app (double-click)."""

block_cipher = None

hiddenimports = [
    "cryptography.hazmat.backends.openssl.backend",
    "cryptography.hazmat.primitives.asymmetric.x25519",
    "rumps",
    "objc",
    "Foundation",
    "AppKit",
    "netgarde_wg.gui.connection_panel",
    "netgarde_wg.gui.icons",
]

a = Analysis(
    ["netgarde_wg/gui/app.py"],
    pathex=[],
    binaries=[],
    datas=[("netgarde_wg/gui/assets", "netgarde_wg/gui/assets")],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="NetGarde",
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
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="NetGarde",
)

app = BUNDLE(
    coll,
    name="NetGarde.app",
    icon=None,
    bundle_identifier="com.netgarde.client",
    info_plist={
        "CFBundleName": "NetGarde",
        "CFBundleDisplayName": "NetGarde",
        "LSUIElement": True,
        "NSHighResolutionCapable": True,
    },
)
