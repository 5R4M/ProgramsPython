import os
import sys
import tkinter as tk

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

# ===== DETECCIÓN AUTOMÁTICA DE RESOLUCIÓN =====
def obtener_escala_pantalla():
    """
    Detecta el tamaño de pantalla y retorna factor de escala.
    Optimizado para laptops de 14-15 pulgadas.
    """
    try:
        root = tk.Tk()
        ancho = root.winfo_screenwidth()
        alto = root.winfo_screenheight()
        root.withdraw()
        root.destroy()
        
        # Detectar pantallas pequeñas (laptops 14-15")
        if ancho <= 1440 and alto <= 900:
            return 0.85  # Reducir 15% para pantallas pequeñas
        elif ancho <= 1680 and alto <= 1050:
            return 0.90  # Reducir 10% para pantallas medianas
        return 1.0  # Tamaño normal para pantallas grandes
    except:  # noqa: E722
        return 0.85  # Por defecto, asumir pantalla pequeña

ESCALA_PANTALLA = obtener_escala_pantalla()

# Función auxiliar para aplicar escala
def escalar(valor):
    """Aplica el factor de escala a un valor numérico"""
    return int(valor * ESCALA_PANTALLA)

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

# ===== CONFIGURACIÓN DE LA APLICACIÓN =====
APP_NAME = "Sistema de Actas Notariales"
APP_VERSION = "1.0.0"

# Tamaño de ventana adaptado (base 1300x700, se ajusta con maximizar)
WINDOW_SIZE = f"{escalar(1300)}x{escalar(700)}"

# ===== CONFIGURACIÓN DE COLORES (sin cambios) =====
COLOR_PRIMARY = "#3498db"
COLOR_SUCCESS = "#2ecc71"
COLOR_WARNING = "#f39c12"
COLOR_DANGER = "#e74c3c"
COLOR_INFO = "#1abc9c"

# ===== TAMAÑOS DE FUENTE ADAPTADOS =====
FONT_SIZE_TITLE_MAIN = escalar(32)      # Título principal (antes 42)
FONT_SIZE_TITLE = escalar(20)            # Títulos de sección (antes 24)
FONT_SIZE_SUBTITLE = escalar(16)         # Subtítulos (antes 18-20)
FONT_SIZE_NORMAL = escalar(12)           # Texto normal (antes 14)
FONT_SIZE_SMALL = escalar(11)            # Texto pequeño (antes 12)
FONT_SIZE_TINY = escalar(10)             # Texto muy pequeño (antes 11)
FONT_SIZE_CARD_TITLE = escalar(15)       # Títulos de tarjetas (antes 18)
FONT_SIZE_BUTTON = escalar(13)           # Texto de botones (antes 15)

# ===== TAMAÑOS DE ICONOS ADAPTADOS =====
ICON_SIZE_MENU = (escalar(20), escalar(20))           # Menú lateral (antes 24x24)
ICON_SIZE_MENU_SMALL = (escalar(18), escalar(18))     # Íconos pequeños menú (antes 20x20)
ICON_SIZE_CARD = (escalar(40), escalar(40))           # Tarjetas inicio (antes 48x48)
ICON_SIZE_LOGO = (escalar(56), escalar(56))           # Logo principal (antes 64x64)
ICON_SIZE_BUTTON = (escalar(20), escalar(20))         # Botones generales (antes 24x24)

# ===== ESPACIADO Y DIMENSIONES ADAPTADOS =====
PADDING_LARGE = escalar(15)              # Padding grande (antes 20-40)
PADDING_MEDIUM = escalar(10)             # Padding medio (antes 15)
PADDING_SMALL = escalar(8)               # Padding pequeño (antes 10)
PADDING_TINY = escalar(5)                # Padding mínimo (antes 5-8)

MENU_WIDTH = escalar(240)                # Ancho menú lateral (antes 280)
BUTTON_HEIGHT = escalar(40)              # Altura botones menú (antes 48)
BUTTON_HEIGHT_SMALL = escalar(32)        # Altura botones pequeños (antes 40)
STATUS_BAR_HEIGHT = escalar(24)          # Altura barra estado (antes 28)
INPUT_HEIGHT = escalar(32)               # Altura inputs (antes 36-40)

CARD_CORNER_RADIUS = escalar(12)         # Radio de esquinas tarjetas (antes 15)
CARD_PADDING = escalar(12)               # Padding interno tarjetas (antes 20)

# ===== DIMENSIONES DE VENTANAS SECUNDARIAS =====
DIALOG_WIDTH = escalar(420)              # Ancho diálogos (antes 500)
DIALOG_HEIGHT = escalar(260)             # Alto diálogos (antes 300)
VISOR_WIDTH = escalar(550)               # Ancho visor documentos (antes 650)
VISOR_HEIGHT = escalar(650)              # Alto visor documentos (antes 750)

# ===== LISTA DE NOTARIOS (sin cambios) =====
NOMBRES_NOTARIOS = [
    "Néstor Antolín Najarro López",
    "Nestor Antolin Najarro Lopez",
    "NÉSTOR ANTOLÍN NAJARRO LÓPEZ",
    "NESTOR ANTOLIN NAJARRO LOPEZ",
    # Agrega otros notarios aquí si los hay
]