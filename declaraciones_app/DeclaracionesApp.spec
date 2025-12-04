# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Archivos de datos a incluir
datas = []

# Incluir la base de datos existente (si existe) - pero NO como archivo obligatorio
# La app debe crear una nueva si no existe
if os.path.exists('actas_notariales.db'):
    datas.append(('actas_notariales.db', '.'))

# Incluir carpeta data completa (plantillas, documentos, etc.)
if os.path.exists('data'):
    datas.append(('data', 'data'))

# Incluir icono y otros recursos de utils
if os.path.exists('utils'):
    datas.append(('utils', 'utils'))

# Icono de la aplicación
icon_path = 'utils/app_icono.ico'
if os.path.exists(icon_path):
    icon_file = icon_path
else:
    icon_file = None

# Recolectar datos de paquetes que los necesiten
try:
    datas += collect_data_files('customtkinter')
except:
    pass

# Hidden imports mejorados
hiddenimports = [
    # BCrypt y seguridad
    'bcrypt',
    'bcrypt._bcrypt',
    '_cffi_backend',
    
    # Base de datos
    'sqlite3',
    
    # CustomTkinter y dependencias
    'customtkinter',
    'customtkinter.windows',
    'customtkinter.windows.widgets',
    'customtkinter.windows.ctk_tk',
    
    # PIL/Pillow
    'PIL',
    'PIL._imagingtk',
    'PIL._tkinter_finder',
    'PIL.Image',
    'PIL.ImageTk',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    
    # python-docx y dependencias
    'docx',
    'docx.oxml',
    'docx.oxml.ns',
    'docx.oxml.text',
    'docx.oxml.xmlchemy',
    'docx.text',
    'docx.document',
    'docx.shared',
    'docx.enum',
    'docx.enum.text',
    
    # lxml
    'lxml',
    'lxml.etree',
    'lxml._elementpath',
    'lxml.objectify',
    
    # Otros
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.filedialog',
    'datetime',
    'json',
    'hashlib',
]

# Binarios adicionales que pueden ser necesarios
binaries = []

# Exclusiones para reducir tamaño
excludes = [
    'matplotlib',
    'numpy',
    'pandas',
    'pytest',
    'scipy',
    'tornado',
    'setuptools',
]

a = Analysis(
    ['main.py'],
    pathex=[os.path.abspath('.')],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DeclaracionesApp',
    debug=False,  # Cambiar a True para debugging
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[
        'vcruntime140.dll',
        'python3.dll',
        'python39.dll',
        'python310.dll',
        'python311.dll',
        'python312.dll',
        '_tkinter.pyd',
        'tk86t.dll',
        'tcl86t.dll',
        '_sqlite3.pyd',
        '_cffi_backend.pyd',
    ],
    runtime_tmpdir=None,
    console=False,  # Cambiar a True temporalmente para ver errores
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)