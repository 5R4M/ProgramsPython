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
        print(f"[ADVERTENCIA] Directorio no encontrado: {src_dir}")
        return entries
    for root, _, files in os.walk(src_dir):
        for fname in files:
            if fname.endswith(('.pyc', '__pycache__')):
                continue
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, src_dir)
            dest_dir = os.path.join(prefix, os.path.dirname(rel_path)) if os.path.dirname(rel_path) else prefix
            entries.append((full_path, dest_dir))
    return entries

# Directorios relativos asumiendo que ejecutas pyinstaller desde src/gui/
UTILS_DIR    = os.path.abspath(os.path.join(BASE_DIR, '..', 'utils'))
DATABASE_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'database'))
GUI_DIR      = os.path.abspath(BASE_DIR)
SRC_DIR      = os.path.abspath(os.path.join(BASE_DIR, '..'))

datas += add_dir_to_datas(UTILS_DIR,    'src/utils')
datas += add_dir_to_datas(DATABASE_DIR, 'src/database')
datas += add_dir_to_datas(GUI_DIR,      'src/gui')

# Archivos sueltos junto a login_window.py
BAT_PATH  = os.path.join(BASE_DIR, 'modificar_mysql.bat')
INI_PATH  = os.path.join(BASE_DIR, 'mysql_config.ini')
ICON_PATH = os.path.join(BASE_DIR, 'icono.ico')

if os.path.isfile(BAT_PATH):
    datas += [(BAT_PATH, '.')]
if os.path.isfile(INI_PATH):
    datas += [(INI_PATH, '.')]

hiddenimports += [
    'mysql.connector',
    'mysql.connector.plugins',
    'mysql.connector.plugins.mysql_native_password',
    'configparser',
    'tkinter',
    'tkinter.messagebox',
    'tkinter.ttk',
    'tkinter.filedialog',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'src',
    'src.database',
    'src.database.db_manager',
    'src.database.__init__',
    'src.gui',
    'src.gui.main_window',
    'src.gui.styles',
    'src.gui.gestion_insumos',
    'src.gui.gestion_movimientos',
    'src.gui.gestion_usuarios',
    'src.gui.gestion_servicios',
    'src.gui.reporte_kardex',
    'src.gui.reporte_bres',
    'src.gui.reporte_balance_bodega',
    'src.gui.reporte_cantidad_solicitada',
    'src.gui.correccion_movimientos',
    'src.gui.importar_exportar_manager',
    'src.gui.configurar_servidor',
    'src.gui.bitacora',
    'src.utils',
]

a = Analysis(
    ['login_window.py'],
    pathex=[BASE_DIR, SRC_DIR, os.path.abspath(os.path.join(BASE_DIR, '..', '..'))],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pathlib'],          # excluir el backport obsoleto
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='InsumosSistema',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,                 # cambia a True si necesitas ver errores en consola
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
    name='InsumosSistema',
)
