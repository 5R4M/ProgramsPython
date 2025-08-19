# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_all

# Recolectar todo lo necesario de mysql-connector-python
datas, binaries, hiddenimports = collect_all('mysql')

# Añadir manualmente tus carpetas/archivos
datas += [
    ('../utils/**', 'utils'),        # src/utils → dentro del exe se llamará utils
    ('../database/**', 'database'),  # src/database → dentro del exe se llamará database
    ('modificar_mysql.bat', '.'),    # está junto a login_window.py (src/gui)
    ('mysql_config.ini', '.'),       # está junto a login_window.py (src/gui)
]

hiddenimports += [
    'mysql.connector',
    'PIL',
    'configparser',
    'tkinter.messagebox',
    'src.database.db_manager',
    'src.gui.main_window'
]

block_cipher = None

a = Analysis(
    ['login_window.py'],
    pathex=[os.path.abspath('.')],   # directorio actual
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='login_window',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,   # False = ventana oculta (usa Tkinter como GUI)
    icon='icono.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='login_window'
)