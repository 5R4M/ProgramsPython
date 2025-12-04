import os
import sys

# Función para obtener el directorio base correctamente en ejecutable y desarrollo
def get_base_dir():
    """
    Retorna el directorio base de la aplicación.
    - En desarrollo: carpeta del script config.py
    - En ejecutable: carpeta donde está el .exe
    """
    if getattr(sys, 'frozen', False):
        # Estamos en un ejecutable de PyInstaller
        # sys.executable apunta al .exe
        return os.path.dirname(sys.executable)
    else:
        # Estamos en desarrollo
        return os.path.dirname(os.path.abspath(__file__))

# Configuración de rutas
BASE_DIR = get_base_dir()
DATA_DIR = os.path.join(BASE_DIR, 'data')
PLANTILLAS_DIR = os.path.join(DATA_DIR, 'plantillas')
DOCUMENTOS_DIR = os.path.join(DATA_DIR, 'documentos')
DB_PATH = os.path.join(BASE_DIR, 'actas_notariales.db')

# Crear directorios si no existen
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PLANTILLAS_DIR, exist_ok=True)
os.makedirs(DOCUMENTOS_DIR, exist_ok=True)

# Configuración de la aplicación
APP_NAME = "Sistema de Actas Notariales"
APP_VERSION = "1.0.0"
WINDOW_SIZE = "1400x900"

# Configuración de colores
COLOR_PRIMARY = "#3498db"
COLOR_SUCCESS = "#2ecc71"
COLOR_WARNING = "#f39c12"
COLOR_DANGER = "#e74c3c"

# Lista de nombres de notarios (para excluir de la extracción)
NOMBRES_NOTARIOS = [
    "Néstor Antolín Najarro López",
    "Nestor Antolin Najarro Lopez",
    "NÉSTOR ANTOLÍN NAJARRO LÓPEZ",
    "NESTOR ANTOLIN NAJARRO LOPEZ",
    # Agrega otros notarios aquí si los hay
]