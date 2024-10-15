# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['bigclock.py'],
    pathex=[],
    binaries=[],
    datas=[('resources/bayer_universal_type.ttf', 'resources'), ('resources/wiggle_wiggle_LMFAO_clip.mp3', 'resources')],
    hiddenimports=[],
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
    name='bigclock',
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
    icon=['icon.iconset/icon-windowed.icns'],
)
app = BUNDLE(
    exe,
    name='bigclock.app',
    icon='icon.iconset/icon-windowed.icns',
    bundle_identifier=None,
)
