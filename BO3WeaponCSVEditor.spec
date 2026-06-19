from PyInstaller.utils.hooks import collect_all

datas = [('CSVEdit.png', '.'), ('CSVEdit.ico', '.'), ('dragdrop.png', '.')]
binaries = []
hiddenimports = ['PIL.Image', 'PIL.ImageTk', 'PIL.ImageDraw', 'PIL.ImageFont']
tmp_ret = collect_all('tkinterdnd2')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

a = Analysis(
    ['BO3CSVEditor.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'test',
        'unittest',
        'pydoc',
        'doctest',
        'xmlrpc',
        'lib2to3',
    ],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BO3WeaponCSVEditor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['CSVEdit.ico'],
)

COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='BO3WeaponCSVEditor',
)
