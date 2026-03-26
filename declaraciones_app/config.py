import os
import sys
import tkinter as tk

# ============================================================
# SISTEMA DE CONFIGURACIÓN RESPONSIVO MEJORADO
# ============================================================

def get_base_dir():
    """
    Retorna el directorio base de la aplicación.
    - En desarrollo: carpeta del script config.py
    - En ejecutable: carpeta donde está el .exe
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


# ===== DETECCIÓN MEJORADA DE RESOLUCIÓN =====
def obtener_info_pantalla():
    """
    Detecta el tamaño de pantalla y retorna información detallada.
    Retorna: (ancho, alto, factor_escala, tipo_pantalla)
    """
    try:
        root = tk.Tk()
        ancho = root.winfo_screenwidth()
        alto = root.winfo_screenheight()
        root.withdraw()
        root.destroy()
        
        # Determinar tipo de pantalla y factor de escala
        if ancho <= 1366 and alto <= 768:
            # Laptops pequeños 13-14" (1366x768, 1280x720)
            tipo = "PEQUEÑA (13-14 pulgadas)"
            escala = 0.75
        elif ancho <= 1440 and alto <= 900:
            # Laptops medianos 14-15" (1440x900)
            tipo = "COMPACTA (14-15 pulgadas)"
            escala = 0.82
        elif ancho <= 1600 and alto <= 900:
            # Monitores HD+ (1600x900)
            tipo = "HD+ (15-16 pulgadas)"
            escala = 0.88
        elif ancho <= 1920 and alto <= 1080:
            # Full HD - Más común (1920x1080)
            tipo = "FULL HD (17+ pulgadas o 1080p)"
            escala = 1.0
        elif ancho <= 2560 and alto <= 1440:
            # QHD/2K (2560x1440)
            tipo = "2K/QHD (27+ pulgadas)"
            escala = 1.15
        elif ancho <= 3840 and alto <= 2160:
            # 4K UHD (3840x2160)
            tipo = "4K UHD (27+ pulgadas)"
            escala = 1.35
        else:
            # Pantallas muy grandes o multi-monitor
            tipo = "ULTRA GRANDE"
            escala = 1.5
        
        return ancho, alto, escala, tipo

    except Exception as e:
        # Valores por defecto seguros (1366x768)
        return 1366, 768, 0.75, "DESCONOCIDA"


# Obtener información de pantalla
ANCHO_PANTALLA, ALTO_PANTALLA, ESCALA_PANTALLA, TIPO_PANTALLA = obtener_info_pantalla()


# ===== FUNCIÓN DE ESCALADO =====
def escalar(valor_base):
    """
    Aplica el factor de escala a un valor numérico.
    
    Args:
        valor_base: Valor diseñado para 1920x1080 (escala 1.0)
    
    Returns:
        Valor escalado según resolución detectada
    """
    return int(valor_base * ESCALA_PANTALLA)


# ===== CONFIGURACIÓN DE RUTAS =====
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

# Tamaño de ventana inicial (se maximiza después)
# Usar 90% del ancho y 85% del alto disponible
WINDOW_WIDTH = int(ANCHO_PANTALLA * 0.90)
WINDOW_HEIGHT = int(ALTO_PANTALLA * 0.85)
WINDOW_SIZE = f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}"


# ===== CONFIGURACIÓN DE COLORES =====
# Colores principales (sin cambios - compatibles con tema oscuro)
COLOR_BG_PRINCIPAL = "#001a33"      # Fondo principal (azul muy oscuro)
COLOR_BG_SECUNDARIO = "#003d66"     # Fondo secundario (azul oscuro)
COLOR_BG_MENU = "#003d66"           # Fondo menú lateral
COLOR_ACCENT = "#005187"            # Color de acento (azul medio)
COLOR_HOVER = "#2d5f8d"             # Color hover botones

# Colores de estado
COLOR_PRIMARY = "#3498db"
COLOR_SUCCESS = "#2ecc71"
COLOR_WARNING = "#f39c12"
COLOR_DANGER = "#e74c3c"
COLOR_ERROR = "#e74c3c"
COLOR_INFO = "#1abc9c"

# Colores de texto
COLOR_TEXT_PRIMARY = "#e0e1dd"      # Texto principal (blanco hueso)
COLOR_TEXT_SECONDARY = "#778da9"    # Texto secundario (gris azulado)


# ============================================================
# TAMAÑOS RESPONSIVOS - BASE PARA 1920x1080 (ESCALA 1.0)
# Se escalan automáticamente según resolución detectada
# ============================================================

# ===== TAMAÑOS DE FUENTE =====
# Valores base diseñados para 1920x1080
FONT_SIZE_TITLE_MAIN = escalar(32)      # Título principal de pantallas
FONT_SIZE_TITLE = escalar(24)           # Títulos de sección
FONT_SIZE_SUBTITLE = escalar(18)        # Subtítulos
FONT_SIZE_NORMAL = escalar(14)          # Texto normal/párrafos
FONT_SIZE_SMALL = escalar(12)           # Texto pequeño
FONT_SIZE_TINY = escalar(10)            # Texto muy pequeño (footer, etc)
FONT_SIZE_CARD_TITLE = escalar(16)      # Títulos en tarjetas
FONT_SIZE_BUTTON = escalar(13)          # Texto en botones

# ===== TAMAÑOS DE ICONOS =====
# Tuplas (ancho, alto) escaladas
ICON_SIZE_MENU = (escalar(24), escalar(24))         # Iconos en menú lateral
ICON_SIZE_MENU_SMALL = (escalar(20), escalar(20))   # Iconos pequeños en menú
ICON_SIZE_CARD = (escalar(56), escalar(56))         # Iconos en tarjetas de inicio
ICON_SIZE_LOGO = (escalar(64), escalar(64))         # Logo principal
ICON_SIZE_BUTTON = (escalar(22), escalar(22))       # Iconos en botones

# ✅ NUEVAS CONSTANTES PARA VENTANA DE LOGIN Y OTROS COMPONENTES
ICON_SIZE_LARGE = (escalar(32), escalar(32))        # Iconos grandes (títulos)
ICON_SIZE_MEDIUM = (escalar(24), escalar(24))       # Iconos medianos (botones)
ICON_SIZE_SMALL = (escalar(18), escalar(18))        # Iconos pequeños (labels)

# ===== ESPACIADO Y PADDING =====
PADDING_LARGE = escalar(20)         # Espaciado grande entre secciones
PADDING_MEDIUM = escalar(15)        # Espaciado medio
PADDING_SMALL = escalar(10)         # Espaciado pequeño
PADDING_TINY = escalar(5)           # Espaciado mínimo

# ===== DIMENSIONES DE COMPONENTES PRINCIPALES =====
MENU_WIDTH = escalar(260)           # Ancho del menú lateral
BUTTON_HEIGHT = escalar(45)         # Altura de botones principales
BUTTON_HEIGHT_SMALL = escalar(36)   # Altura de botones secundarios
STATUS_BAR_HEIGHT = escalar(30)     # Altura de barra de estado
INPUT_HEIGHT = escalar(38)          # Altura de campos de entrada

# ===== TARJETAS Y CONTENEDORES =====
CARD_CORNER_RADIUS = escalar(15)    # Radio de esquinas de tarjetas
CARD_PADDING = escalar(20)          # Padding interno de tarjetas
CARD_MIN_WIDTH = escalar(220)       # Ancho mínimo de tarjetas

# ===== DIMENSIONES DE VENTANAS SECUNDARIAS =====
DIALOG_WIDTH = escalar(500)         # Ancho de diálogos
DIALOG_HEIGHT = escalar(350)        # Alto de diálogos
VISOR_WIDTH = escalar(700)          # Ancho de visor de documentos
VISOR_HEIGHT = escalar(800)         # Alto de visor de documentos

# ===== TABLAS Y LISTAS =====
TABLE_ROW_HEIGHT = escalar(40)      # Altura de filas en tablas
TABLE_HEADER_HEIGHT = escalar(45)   # Altura de encabezados de tabla
SCROLLBAR_WIDTH = escalar(14)       # Ancho de scrollbars

# ===== FORMULARIOS =====
LABEL_WIDTH = escalar(180)          # Ancho de etiquetas en formularios
TEXTAREA_HEIGHT = escalar(120)      # Altura de áreas de texto
COMBOBOX_HEIGHT = escalar(38)       # Altura de combobox

# Dimensiones de TextBox de logs
TEXTBOX_LOG_WIDTH = escalar(650)
TEXTBOX_LOG_HEIGHT = escalar(280)

# ============================================================
# AJUSTES ESPECÍFICOS POR RESOLUCIÓN
# ============================================================

# Para pantallas muy pequeñas (≤1366x768), hacer ajustes adicionales
if ANCHO_PANTALLA <= 1366:
    MENU_WIDTH = int(MENU_WIDTH * 0.9)
    CARD_PADDING = max(8, int(CARD_PADDING * 0.7))
    PADDING_LARGE = max(10, int(PADDING_LARGE * 0.8))

# Para pantallas grandes (≥2560), hacer ajustes adicionales
elif ANCHO_PANTALLA >= 2560:
    CARD_MIN_WIDTH = int(CARD_MIN_WIDTH * 1.2)


# ===== LISTA DE NOTARIOS =====
NOMBRES_NOTARIOS = [
    "Néstor Antolín Najarro López",
    "Nestor Antolin Najarro Lopez",
    "NÉSTOR ANTOLÍN NAJARRO LÓPEZ",
    "NESTOR ANTOLIN NAJARRO LOPEZ",
]


# ============================================================
# FUNCIONES AUXILIARES PARA UI RESPONSIVO
# ============================================================

def es_pantalla_pequena():
    """Retorna True si la pantalla es pequeña (≤1366x768)"""
    return ANCHO_PANTALLA <= 1366


def es_pantalla_grande():
    """Retorna True si la pantalla es grande (≥1920x1080)"""
    return ANCHO_PANTALLA >= 1920


def ajustar_grid_columnas():
    """
    Retorna número óptimo de columnas para grids según resolución.
    Útil para layouts de tarjetas.
    """
    if ANCHO_PANTALLA <= 1366:
        return 2  # 2 columnas en pantallas pequeñas
    elif ANCHO_PANTALLA <= 1600:
        return 3  # 3 columnas en pantallas medianas
    elif ANCHO_PANTALLA <= 1920:
        return 4  # 4 columnas en Full HD
    else:
        return 5  # 5+ columnas en pantallas grandes


# ============================================================
# INFORMACIÓN DE CONFIGURACIÓN (DEBUG)
# ============================================================

