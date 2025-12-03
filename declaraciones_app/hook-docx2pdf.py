# hook-docx2pdf.py
# Coloca este archivo en la raíz de tu proyecto

from PyInstaller.utils.hooks import collect_all, collect_submodules

# Recolectar todos los recursos de docx2pdf
datas, binaries, hiddenimports = collect_all('docx2pdf')

# Recolectar submodulos de comtypes (necesario para docx2pdf)
hiddenimports += collect_submodules('comtypes')
hiddenimports += collect_submodules('comtypes.gen')

# Asegurar que comtypes y win32com estén incluidos
hiddenimports += [
    'comtypes',
    'comtypes.client',
    'comtypes.gen',
    'comtypes.stream',
    'win32com',
    'win32com.client',
    'win32com.client.gencache',
    'pythoncom',
    'pywintypes',
    'win32api',
    'win32con',
]

# Añadir módulos de sistema necesarios
hiddenimports += [
    'io',
    'subprocess',
    'tempfile',
]