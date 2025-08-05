import tkinter as tk
import sqlite3
from tkinter import ttk
from tkinter import messagebox
import sys
import os
from PIL import Image, ImageTk
from ttkthemes import ThemedStyle

# Agregar el directorio raíz del proyecto al PATH de Python
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# Importar las funciones de la base de datos
from src.database import DB_PATH, crear_base_datos, verificar_tablas
from src.gui.ingreso_insumos import IngresoInsumos
from src.gui.gestion_insumos import GestionInsumos
from src.gui.gestion_servicios import GestionServicios
from src.gui.gestion_movimientos import GestionMovimientos
from src.gui.reporte_kardex import ReporteKardex
from src.gui.reporte_demanda_real import ReporteDemandaReal
from src.gui.reporte_bres import ReporteBres
from src.gui.importar_exportar_manager import ImportarExportarManager, crear_gestor_importar_exportar

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        # En desarrollo, base_path es la raíz del proyecto (subir un nivel desde gui)
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(base_path, relative_path)

class MainWindow:
    def __init__(self, usuario):
        self.usuario = usuario

        # **CONFIGURACIÓN DE TAMAÑO ESTÁNDAR PARA TODAS LAS VENTANAS**
        self.ANCHO_VENTANA = 1400  # Aumentado para mejor proporción
        self.ALTO_VENTANA = 900    # Alto estándar

        # Colores del tema
        self.COLORS = {
            'primary': '#2c3e50',      # Azul oscuro
            'secondary': '#34495e',     # Gris azulado
            'accent': '#3498db',        # Azul claro
            'success': '#27ae60',       # Verde
            'warning': '#f39c12',       # Naranja
            'danger': '#e74c3c',        # Rojo
            'light': '#ecf0f1',         # Gris muy claro
            'white': '#ffffff',         # Blanco
            'text_dark': '#2c3e50',     # Texto oscuro
            'text_light': '#7f8c8d',    # Texto claro
            'hover': '#3498db',         # Color hover
            'active': '#2980b9',        # Color activo
            'exit_btn': '#17a2b8',      # Color celeste para botón salir
            'exit_hover': '#138496'     # Color celeste oscuro para hover
        }

        # Inicializar la base de datos antes de crear la ventana
        if not self.initialize_database():
            messagebox.showerror("Error Fatal",
                "No se pudo inicializar la base de datos. El programa se cerrará.")
            sys.exit(1)

        self.root = tk.Tk()
        self.root.title("Sistema de Gestión de Insumos")

        # Configurar icono de la ventana si existe
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'icons', 'app_icon.ico')
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass

        # Aplicar tema moderno
        style = ThemedStyle(self.root)
        style.set_theme("arc")

        self.setup_window()
        self.setup_styles()
        self.load_icons()
        self.create_layout()

        # Mostrar la pantalla de bienvenida inicial
        self.show_welcome_screen()

        # Manejar el cierre de la ventana principal
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_styles(self):
        """Configura los estilos personalizados"""
        style = ttk.Style()

        # Estilo para el menú lateral
        style.configure('Sidebar.TFrame',
                       background=self.COLORS['primary'],
                       relief='flat',
                       borderwidth=0)

        # Estilo para botones del menú
        style.configure('MenuButton.TButton',
                       font=('Segoe UI', 11),
                       padding=(20, 12),
                       relief='flat',
                       borderwidth=0,
                       background=self.COLORS['primary'],
                       foreground=self.COLORS['white'],
                       focuscolor='none')

        style.map('MenuButton.TButton',
                 background=[('active', self.COLORS['hover']),
                           ('pressed', self.COLORS['active'])],
                 foreground=[('active', self.COLORS['white']),
                           ('pressed', self.COLORS['white'])])

        # Estilo para el botón de salir - ACTUALIZADO CON COLOR CELESTE
        style.configure('ExitButton.TButton',
                       font=('Segoe UI', 11, 'bold'),
                       padding=(20, 12),
                       relief='flat',
                       borderwidth=0,
                       background=self.COLORS['exit_btn'],  # Color celeste
                       foreground=self.COLORS['white'],
                       focuscolor='none')

        style.map('ExitButton.TButton',
                 background=[('active', self.COLORS['exit_hover']),
                           ('pressed', '#117a8b')])  # Celeste aún más oscuro

        # Estilo para el área principal
        style.configure('MainArea.TFrame',
                       background=self.COLORS['light'],
                       relief='flat',
                       borderwidth=0)

        # Estilo para tarjetas
        style.configure('Card.TFrame',
                       background=self.COLORS['white'],
                       relief='solid',
                       borderwidth=1)

        # Estilo para títulos
        style.configure('Title.TLabel',
                       font=('Segoe UI', 24, 'bold'),
                       background=self.COLORS['white'],
                       foreground=self.COLORS['primary'])

        style.configure('Subtitle.TLabel',
                       font=('Segoe UI', 14),
                       background=self.COLORS['white'],
                       foreground=self.COLORS['text_light'])

        # Estilo para la barra de estado
        style.configure('StatusBar.TFrame',
                       background=self.COLORS['secondary'],
                       relief='flat',
                       borderwidth=0)

        style.configure('StatusBar.TLabel',
                       font=('Segoe UI', 9),
                       background=self.COLORS['secondary'],
                       foreground=self.COLORS['white'],
                       padding=(10, 5))

    def create_rounded_button(self, parent, text, bg_color, hover_color, command, icon=None):
        """Crea un botón con apariencia de bordes redondeados"""

        # Frame contenedor para simular bordes redondeados
        button_frame = tk.Frame(parent, bg=bg_color, relief='flat', bd=0)
        button_frame.pack(fill="x", padx=20, pady=5)

        # Frame interno para el efecto redondeado
        inner_frame = tk.Frame(button_frame, bg=bg_color, relief='flat', bd=0)
        inner_frame.pack(fill="both", expand=True, padx=3, pady=3)

        # Botón principal
        btn = tk.Button(inner_frame,
                       text=text,
                       font=('Segoe UI', 11, 'bold'),
                       bg=bg_color,
                       fg='white',
                       relief='flat',
                       borderwidth=0,
                       padx=20,
                       pady=12,
                       cursor='hand2',
                       command=command)

        if icon:
            btn.config(image=icon, compound='left')

        btn.pack(fill="both", expand=True)

        # Efectos hover
        def on_enter(e):
            btn.config(bg=hover_color)
            inner_frame.config(bg=hover_color)
            button_frame.config(bg=hover_color)

        def on_leave(e):
            btn.config(bg=bg_color)
            inner_frame.config(bg=bg_color)
            button_frame.config(bg=bg_color)

        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        button_frame.bind('<Enter>', on_enter)
        button_frame.bind('<Leave>', on_leave)
        inner_frame.bind('<Enter>', on_enter)
        inner_frame.bind('<Leave>', on_leave)

        return btn

    def load_icons(self):
        """Carga los iconos para los botones del menú"""
        self.icons = {}
        icon_path = resource_path(os.path.join('utils', 'icons'))

        # Crear directorio de iconos si no existe
        if not os.path.exists(icon_path):
            os.makedirs(icon_path)

        # Mapeo de iconos
        icon_files = {
            'usuarios': 'usuario.png',
            'insumos': 'insumo.png',
            'servicios': 'servicio.png',
            'movimientos': 'movimiento.png',
            'import_export': 'importar-exportar.png',
            'ingreso': 'ingreso.png',
            'kardex': 'kardex.png',
            'demanda': 'demanda-real.png',
            'correcciones': 'correcion.png',
            'bres': 'bres.png',
            'salir': 'salir.png',
            'logo': 'logo.png'
        }

        # Cargar iconos
        for key, filename in icon_files.items():
            try:
                icon_full_path = os.path.join(icon_path, filename)
                if os.path.exists(icon_full_path):
                    image = Image.open(icon_full_path)
                    if key == 'logo':
                        image = image.resize((80, 80), Image.Resampling.LANCZOS)
                    else:
                        image = image.resize((20, 20), Image.Resampling.LANCZOS)
                    self.icons[key] = ImageTk.PhotoImage(image)
                else:
                    self.icons[key] = None
            except Exception as e:
                print(f"Error cargando icono {filename}: {e}")
                self.icons[key] = None

    def setup_window(self):
        """Configura la ventana principal con tamaño estándar"""
        # Configurar tamaño y centrar ventana
        self.center_window(self.ANCHO_VENTANA, self.ALTO_VENTANA)

        # Configurar tamaño mínimo
        self.root.minsize(1200, 700)

        # Permitir redimensionamiento
        self.root.resizable(True, True)

        # Configurar el grid principal
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(1, weight=0)  # Barra de estado

    def create_layout(self):
        """Crea el layout principal de la aplicación"""
        # **SIDEBAR (MENÚ LATERAL)**
        self.sidebar = ttk.Frame(self.root, style='Sidebar.TFrame', width=280)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.sidebar.grid_propagate(False)  # Mantener ancho fijo

        # **ÁREA PRINCIPAL**
        self.main_area = ttk.Frame(self.root, style='MainArea.TFrame')
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)

        # **BARRA DE ESTADO**
        self.status_bar = ttk.Frame(self.root, style='StatusBar.TFrame')
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

        # Crear contenido del sidebar
        self.create_sidebar()

        # Crear área de contenido principal
        self.create_main_content_area()

        # Crear barra de estado
        self.create_status_bar()

    def create_sidebar(self):
        """Crea el menú lateral"""
        # **HEADER DEL SIDEBAR**
        header_frame = tk.Frame(self.sidebar, bg=self.COLORS['primary'], height=140)
        header_frame.pack(fill="x", pady=0)
        header_frame.pack_propagate(False)

        # Logo (si existe)
        if self.icons.get('logo'):
            logo_label = tk.Label(header_frame, 
                                image=self.icons['logo'],
                                bg=self.COLORS['primary'])
            logo_label.pack(pady=(25, 8))
        else:
            # Si no hay logo, agregar espacio equivalente
            spacer = tk.Frame(header_frame, bg=self.COLORS['primary'], height=30)
            spacer.pack()

        # Título del sistema
        title_label = tk.Label(header_frame,
                              text="SISTEMA DE GESTIÓN",
                              font=('Segoe UI', 12, 'bold'),
                              fg=self.COLORS['white'],
                              bg=self.COLORS['primary'])
        title_label.pack(pady=(5, 2))

        subtitle_label = tk.Label(header_frame,
                                 text="DE INSUMOS",
                                 font=('Segoe UI', 12, 'bold'),
                                 fg=self.COLORS['white'],
                                 bg=self.COLORS['primary'])
        subtitle_label.pack(pady=(0, 15))

        # **SEPARADOR**
        separator = tk.Frame(self.sidebar, bg=self.COLORS['accent'], height=2)
        separator.pack(fill="x", pady=0)

        # **MENÚ DE NAVEGACIÓN**
        nav_frame = tk.Frame(self.sidebar, bg=self.COLORS['primary'])
        nav_frame.pack(fill="both", expand=True, padx=0, pady=20)

        # Crear botones según rol
        self.create_navigation_menu(nav_frame)

        # **BOTÓN DE SALIR (EN LA PARTE INFERIOR) - ACTUALIZADO**
        exit_frame = tk.Frame(self.sidebar, bg=self.COLORS['primary'], height=70)
        exit_frame.pack(fill="x", side="bottom", pady=(0, 20))
        exit_frame.pack_propagate(False)

        # Usar la función de botón redondeado con color celeste
        exit_btn = self.create_rounded_button(
            exit_frame,
            "  Salir del Sistema",
            self.COLORS['exit_btn'],  # Color celeste
            self.COLORS['exit_hover'], # Color hover celeste oscuro
            self.on_closing,
            self.icons.get('salir')
        )

    def create_navigation_menu(self, parent):
        """Crea el menú de navegación"""
        rol = self.usuario['rol']

        # Definir menús por rol
        menu_items = []

        if rol in ("admin", "super_admin"):
            menu_items.extend([
                ("Gestión de Usuarios", self.load_gestion_usuarios, 'usuarios'),
                ("Gestión de Insumos", self.load_gestion_insumos, 'insumos'),
                ("Gestión de Servicios", self.load_gestion_servicios, 'servicios'),
                ("Gestión de Movimientos", self.load_gestion_movimientos, 'movimientos'),
            ])

        if rol in ("usuario", "admin", "super_admin"):
            menu_items.extend([
                ("Ingreso de Insumos", self.load_ingreso_insumos, 'ingreso'),
                ("Reporte Kardex", self.load_reporte_kardex, 'kardex'),
                ("Reporte Demanda Real", self.load_reporte_demanda_real, 'demanda'),
                ("Reporte BRES", self.load_reporte_bres, 'bres'),
                ("Correcciones", self.load_correccion_movimientos, 'correcciones'),
                ("Importar/Exportar", self.load_importar_exportar, 'import_export'),
            ])

        # Crear botones
        for text, command, icon_key in menu_items:
            self.create_nav_button(parent, text, command, icon_key)

    def create_nav_button(self, parent, text, command, icon_key):
        """Crea un botón de navegación"""
        btn = tk.Button(parent,
                    text=f"  {text}",
                    font=('Segoe UI', 11),
                    bg=self.COLORS['primary'],
                    fg=self.COLORS['white'],
                    relief='flat',
                    borderwidth=0,
                    padx=20,
                    pady=12,
                    anchor='w',
                    cursor='hand2',
                    command=command)

        # Agregar icono si existe
        if self.icons.get(icon_key):
            btn.config(image=self.icons[icon_key], compound='left')

        btn.pack(fill="x", padx=20, pady=2)

        # Efectos hover mejorados
        def on_enter(e):
            btn.config(bg=self.COLORS['hover'])
        
        def on_leave(e):
            btn.config(bg=self.COLORS['primary'])
        
        def on_click(e):
            # Cambiar a color activo momentáneamente
            btn.config(bg=self.COLORS['active'])
            # Después de ejecutar el comando, volver al color normal
            parent.after(150, lambda: btn.config(bg=self.COLORS['primary']))

        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        btn.bind('<Button-1>', on_click)

    def create_main_content_area(self):
        """Crea el área de contenido principal"""
        # Frame contenedor con padding
        self.main_content_frame = ttk.Frame(self.main_area, style='Card.TFrame')
        self.main_content_frame.pack(fill="both", expand=True, padx=20, pady=20)

    def create_status_bar(self):
        """Crea la barra de estado"""
        # Información del usuario
        nombre_usuario = self.usuario.get('nombre_completo', self.usuario.get('username', 'Usuario'))
        rol_usuario = self.usuario.get('rol', '')

        self.user_label = ttk.Label(
            self.status_bar,
            text=f"👤 Usuario: {nombre_usuario} ({rol_usuario})",
            style='StatusBar.TLabel'
        )
        self.user_label.pack(side="left")

        # Información adicional (fecha, hora, etc.)
        import datetime
        fecha_actual = datetime.datetime.now().strftime("%d/%m/%Y")

        self.date_label = ttk.Label(
            self.status_bar,
            text=f"📅 {fecha_actual}",
            style='StatusBar.TLabel'
        )
        self.date_label.pack(side="right")

    def show_welcome_screen(self):
        """Muestra la pantalla de bienvenida mejorada"""
        self.clear_content_frame()
        self.reset_window_size()

        # Forzar fondo blanco en el frame principal
        try:
            self.main_content_frame.configure(style='Card.TFrame')
        except:
            pass
        try:
            self.main_content_frame.configure(bg=self.COLORS['white'])
        except:
            pass
        
        # Frame principal de bienvenida
        welcome_frame = tk.Frame(self.main_content_frame, bg=self.COLORS['white'])
        welcome_frame.pack(fill="both", expand=True, padx=40, pady=40)

        # **HEADER DE BIENVENIDA**
        header_frame = tk.Frame(welcome_frame, bg=self.COLORS['white'])
        header_frame.pack(fill="x", pady=(0, 30))

        # Título principal
        title_label = tk.Label(header_frame,
                              text="¡Bienvenido al Sistema!",
                              font=('Segoe UI', 28, 'bold'),
                              fg=self.COLORS['primary'],
                              bg=self.COLORS['white'])
        title_label.pack()

        # Subtítulo
        subtitle_label = tk.Label(header_frame,
                                 text="DIRECCIÓN DEPARTAMENTAL DE REDES INTEGRADAS\n" +
                                      "DE SERVICIOS DE SALUD DE GUATEMALA\n" +
                                      "ÁREA NOR ORIENTE",
                                 font=('Segoe UI', 14),
                                 fg=self.COLORS['text_light'],
                                 bg=self.COLORS['white'],
                                 justify='center')
        subtitle_label.pack(pady=(10, 0))

        # **SEPARADOR DECORATIVO**
        separator_frame = tk.Frame(welcome_frame, bg=self.COLORS['white'], height=40)
        separator_frame.pack(fill="x")

        separator_line = tk.Frame(separator_frame, bg=self.COLORS['accent'], height=3)
        separator_line.pack(expand=True, fill="x", padx=100)

        # **TARJETAS DE INFORMACIÓN**
        cards_frame = tk.Frame(welcome_frame, bg=self.COLORS['white'])
        cards_frame.pack(fill="both", expand=True, pady=20)

        # Configurar grid para las tarjetas
        cards_frame.grid_columnconfigure(0, weight=1)
        cards_frame.grid_columnconfigure(1, weight=1)

        # Tarjeta de funcionalidades
        self.create_info_card(cards_frame, 
                             "🎯 Funcionalidades Principales",
                             [
                                 "• Gestión completa de insumos médicos",
                                 "• Control de inventarios en tiempo real",
                                 "• Generación de reportes especializados",
                                 "• Seguimiento de movimientos detallado",
                                 "• Administración de usuarios y permisos"
                             ], 0, 0)

        # Tarjeta de inicio rápido
        self.create_info_card(cards_frame,
                             "🚀 Inicio Rápido",
                             [
                                 "• Seleccione una opción del menú lateral",
                                 "• Use 'Ingreso de Insumos' para registrar",
                                 "• Genere reportes desde el menú",
                                 "• Consulte el Kardex para seguimiento",
                                 "• Configure el sistema en Gestión"
                             ], 0, 1)

        # **FOOTER CON INFORMACIÓN DEL USUARIO**
        footer_frame = tk.Frame(welcome_frame, bg=self.COLORS['light'], height=60)
        footer_frame.pack(fill="x", side="bottom", pady=(30, 0))
        footer_frame.pack_propagate(False)

        user_info = f"Sesión iniciada como: {self.usuario.get('nombre_completo', 'Usuario')} ({self.usuario.get('rol', '')})"
        footer_label = tk.Label(footer_frame,
                               text=user_info,
                               font=('Segoe UI', 10),
                               fg=self.COLORS['text_dark'],
                               bg=self.COLORS['light'])
        footer_label.pack(expand=True)

    def create_info_card(self, parent, title, items, row, col):
        """Crea una tarjeta de información"""
        card_frame = tk.Frame(parent, 
                             bg=self.COLORS['white'],
                             relief='solid',
                             borderwidth=1,
                             padx=20,
                             pady=20)
        card_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        # Título de la tarjeta
        title_label = tk.Label(card_frame,
                              text=title,
                              font=('Segoe UI', 16, 'bold'),
                              fg=self.COLORS['primary'],
                              bg=self.COLORS['white'])
        title_label.pack(anchor="w", pady=(0, 15))

        # Items de la tarjeta
        for item in items:
            item_label = tk.Label(card_frame,
                                 text=item,
                                 font=('Segoe UI', 11),
                                 fg=self.COLORS['text_dark'],
                                 bg=self.COLORS['white'],
                                 anchor="w",
                                 justify="left")
            item_label.pack(anchor="w", pady=2)

    # Resto de métodos sin cambios...
    def center_window(self, width, height):
        """Centra la ventana en la pantalla tanto horizontal como verticalmente"""
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        x = max(0, x)
        y = max(0, y)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def resize_window_for_content(self, extra_height=0):
        """Redimensiona la ventana cuando se necesita espacio adicional"""
        nuevo_alto = self.ALTO_VENTANA + extra_height
        self.root.update_idletasks()
        x = self.root.winfo_x()
        screen_height = self.root.winfo_screenheight()
        y = (screen_height - nuevo_alto) // 2
        if y + nuevo_alto > screen_height:
            y = max(0, screen_height - nuevo_alto)
        elif y < 0:
            y = 0
        self.root.geometry(f"{self.ANCHO_VENTANA}x{nuevo_alto}+{x}+{y}")

    def reset_window_size(self):
        """Restaura el tamaño original de la ventana y la centra"""
        self.center_window(self.ANCHO_VENTANA, self.ALTO_VENTANA)

    def initialize_database(self):
        """Inicializa la base de datos y verifica su estructura"""
        try:
            if not os.path.exists(DB_PATH):
                print("La base de datos no existe. Creándola...")
                if not crear_base_datos():
                    raise Exception("No se pudo crear la base de datos")
                print("Base de datos creada correctamente")

            if not verificar_tablas():
                print("La estructura de la base de datos es incorrecta. Recreándola...")
                if os.path.exists(DB_PATH):
                    os.remove(DB_PATH)
                if not crear_base_datos():
                    raise Exception("No se pudo recrear la base de datos")
                print("Base de datos recreada correctamente")

            return True

        except Exception as e:
            print(f"Error al inicializar la base de datos: {e}")
            messagebox.showerror("Error", f"Error al inicializar la base de datos: {str(e)}")
            return False

    def verify_database_connection(self):
        """Verifica la conexión a la base de datos"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            conn.close()
            return True
        except Exception as e:
            print(f"Error al verificar conexión a la base de datos: {e}")
            return False

    def on_closing(self):
        """Maneja el cierre de la ventana principal"""
        if messagebox.askokcancel("Salir", "¿Desea salir del sistema?"):
            self.root.quit()
            self.root.destroy()

    def clear_content_frame(self):
        """Limpia el contenido del frame principal de forma segura"""
        try:
            if hasattr(self, 'pantalla_actual') and self.pantalla_actual:
                if hasattr(self.pantalla_actual, 'destroy'):
                    try:
                        self.pantalla_actual.destroy()
                    except:
                        pass
                self.pantalla_actual = None

            if hasattr(self, 'main_content_frame') and self.main_content_frame.winfo_exists():
                for widget in self.main_content_frame.winfo_children():
                    try:
                        widget.destroy()
                    except:
                        pass
                self.main_content_frame.update_idletasks()

        except Exception as e:
            print(f"Error limpiando frame: {e}")

    # Métodos para cargar módulos (sin cambios)
    def load_ingreso_insumos(self):
        if not self.verify_database_connection():
            messagebox.showerror("Error", "No se puede conectar a la base de datos")
            return
        self.clear_content_frame()
        self.reset_window_size()
        self.pantalla_actual = IngresoInsumos(self.main_content_frame, self)

    def load_gestion_insumos(self):
        if not self.verify_database_connection():
            messagebox.showerror("Error", "No se puede conectar a la base de datos")
            return
        self.clear_content_frame()
        self.reset_window_size()
        self.pantalla_actual = GestionInsumos(self.main_content_frame, self)

    def load_gestion_servicios(self):
        if not self.verify_database_connection():
            messagebox.showerror("Error", "No se puede conectar a la base de datos")
            return
        self.clear_content_frame()
        self.reset_window_size()
        self.pantalla_actual = GestionServicios(self.main_content_frame, self)

    def load_gestion_movimientos(self):
        if not self.verify_database_connection():
            messagebox.showerror("Error", "No se puede conectar a la base de datos")
            return
        self.clear_content_frame()
        self.reset_window_size()
        self.pantalla_actual = GestionMovimientos(self.main_content_frame, self)

    def load_reporte_kardex(self):
        try:
            if not self.verify_database_connection():
                messagebox.showerror("Error", "No se puede conectar a la base de datos")
                return
            self.clear_content_frame()
            if not hasattr(self, 'main_content_frame') or not self.main_content_frame.winfo_exists():
                messagebox.showerror("Error", "Frame principal no disponible")
                return
            self.reset_window_size()
            self.pantalla_actual = ReporteKardex(self.main_content_frame, self)
        except Exception as e:
            print(f"Error cargando reporte Kardex: {e}")
            messagebox.showerror("Error", f"Error al cargar reporte Kardex: {str(e)}")

    def load_gestion_usuarios(self):
        if not self.verify_database_connection():
            messagebox.showerror("Error", "No se puede conectar a la base de datos")
            return
        self.clear_content_frame()
        self.reset_window_size()
        from src.gui.gestion_usuarios import GestionUsuarios
        self.pantalla_actual = GestionUsuarios(self.main_content_frame, self)

    def load_correccion_movimientos(self):
        if not self.verify_database_connection():
            messagebox.showerror("Error", "No se puede conectar a la base de datos")
            return
        self.clear_content_frame()
        self.reset_window_size()
        from src.gui.correccion_movimientos import CorreccionMovimientos
        self.pantalla_actual = CorreccionMovimientos(self.main_content_frame, self)

    def load_reporte_demanda_real(self):
        if not self.verify_database_connection():
            messagebox.showerror("Error", "No se puede conectar a la base de datos")
            return
        self.clear_content_frame()
        self.reset_window_size()
        self.pantalla_actual = ReporteDemandaReal(self.main_content_frame, self)

    def load_reporte_bres(self):
        if not self.verify_database_connection():
            messagebox.showerror("Error", "No se puede conectar a la base de datos")
            return
        self.clear_content_frame()
        self.reset_window_size()
        self.pantalla_actual = ReporteBres(self.main_content_frame, self)

    def load_importar_exportar(self):
        if not self.verify_database_connection():
            messagebox.showerror("Error", "No se puede conectar a la base de datos")
            return
        self.clear_content_frame()
        self.reset_window_size()
        try:
            from src.database import DB_PATH
            db_path = DB_PATH
        except:
            db_path = 'database.db'
        self.pantalla_actual = ImportarExportarManager(self.main_content_frame, self)
        self.pantalla_actual.db_path = db_path

    def run(self):
        """Ejecuta la aplicación"""
        self.root.mainloop()
