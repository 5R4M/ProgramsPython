# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_all

BASE_DIR = os.path.abspath(os.getcwd())

# Recolectar mysql-connector-python
datas, binaries, hiddenimports = collect_all('mysql')

def add_dir_to_datas(src_dir, prefix):
    """Añade todos los archivos de src_dir a datas manteniendo estructura relativa bajo prefix."""
    entries = []
    if not os.path.isdir(src_dir):
        return entries
    for root, _, files in os.walk(src_dir):
        for fname in files:
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, src_dir)
            dest_dir = os.path.join(prefix, os.path.dirname(rel_path)) if os.path.dirname(rel_path) else prefix
            entries.append((full_path, dest_dir))
    return entries

# Directorios relativos asumiendo que ejecutas pyinstaller desde src/gui
UTILS_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'utils'))
DATABASE_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'database'))

datas += add_dir_to_datas(UTILS_DIR, 'utils')
datas += add_dir_to_datas(DATABASE_DIR, 'database')

# Incluir la carpeta _internal generada por PyInstaller
INTERNAL_DIR = os.path.abspath(os.path.join(BASE_DIR, 'dist', 'login_window', '_internal'))
datas += add_dir_to_datas(INTERNAL_DIR, '_internal')

# Archivos sueltos junto a login_window.py
BAT_PATH = os.path.join(BASE_DIR, 'modificar_mysql.bat')
INI_PATH = os.path.join(BASE_DIR, 'mysql_config.ini')
ICON_PATH = os.path.join(BASE_DIR, 'icono.ico')

if os.path.isfile(BAT_PATH):
    datas += [(BAT_PATH, '.')]
if os.path.isfile(INI_PATH):
    datas += [(INI_PATH, '.')]

hiddenimports += [
    'mysql.connector',
    'PIL',  # si no usas PIL/Pillow, puedes quitarlo
    'configparser',
    'tkinter.messagebox',
    'src.database.db_manager',
    'src.gui.main_window',
]

block_cipher = None

a = Analysis(
    ['login_window.py'],
    pathex=[BASE_DIR],
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

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    console=False,  # ponlo True durante pruebas
    icon=ICON_PATH if os.path.isfile(ICON_PATH) else None,
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