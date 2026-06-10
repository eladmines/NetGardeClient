# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for TrustEdge menu bar .app (double-click)."""

import os

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))

block_cipher = None

hiddenimports = [
    "cryptography.hazmat.backends.openssl.backend",
    "cryptography.hazmat.primitives.asymmetric.x25519",
    "rumps",
    "objc",
    "Foundation",
    "AppKit",
    "trustedge_wg.gui.connection_panel",
    "trustedge_wg.gui.icons",
]

a = Analysis(
    [os.path.join(ROOT, "trustedge_wg/gui/app.py")],
    pathex=[ROOT],
    binaries=[],
    datas=[(os.path.join(ROOT, "trustedge_wg/gui/assets"), "trustedge_wg/gui/assets")],
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
    name="TrustEdge",
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
    name="TrustEdge",
)

app = BUNDLE(
    coll,
    name="TrustEdge.app",
    icon=None,
    bundle_identifier="com.trustedge.client",
    info_plist={
        "CFBundleName": "TrustEdge",
        "CFBundleDisplayName": "TrustEdge",
        "LSUIElement": True,
        "NSHighResolutionCapable": True,
    },
)
