# -*- mode: python ; coding: utf-8 -*-


from pathlib import Path
import shutil
from imageio_ffmpeg import get_ffmpeg_exe

ffmpeg = Path(get_ffmpeg_exe())
ffmpeg_dir = Path(workpath)
ffmpeg_dir.mkdir(parents=True, exist_ok=True)
ffmpeg_bundle = ffmpeg_dir / "ffmpeg.exe"
shutil.copyfile(ffmpeg, ffmpeg_bundle)

a = Analysis(
    ['gestor_vn.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icono.ico', '.'), ('vndb.ico', '.'), ('vndb.png', '.'),
        (str(ffmpeg_bundle), '.'),
    ],
    excludes=['imageio_ffmpeg'],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    noarchive=False,
    optimize=0,
)
# Windows 10/11 provide their own UCRT and ICU runtime. Copies collected
# from the build machine can shadow the system DLLs when Qt loads.
system_dlls = {'ucrtbase.dll', 'icudt78.dll', 'icuuc.dll'}
a.binaries = [
    entry for entry in a.binaries
    if not (
        Path(entry[0]).name.lower() in system_dlls
        or Path(entry[0]).name.lower().startswith('api-ms-win-')
    )
]
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NyuhuhuGallery5.0',
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
    icon=['icono.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NyuhuhuGallery5.0',
)
