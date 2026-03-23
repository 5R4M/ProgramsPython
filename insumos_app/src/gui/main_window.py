import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sys
import os
from PIL import Image, ImageTk
from ttkthemes import ThemedStyle

# Importar las funciones de la base de datos
from src.database import crear_base_datos, verificar_tablas
from src.gui.ingreso_insumos import IngresoInsumos
from src.gui.gestion_insumos import GestionInsumos
from src.gui.gestion_servicios import GestionServicios
from src.gui.gestion_movimientos import GestionMovimientos
from src.gui.reporte_kardex import ReporteKardex
from src.gui.reporte_demanda_real import ReporteDemandaReal
from src.gui.reporte_bres import ReporteBres
from src.gui.reporte_balance_bodega import ReporteBalanceBodega
from src.gui.configurar_servidor import ConfigurarServidor
from src.gui.reporte_cantidad_solicitada import ReporteCantidadSolicitada
from src.gui.importar_exportar_manager import ImportarExportarManager

# Agregar el directorio raíz del proyecto al PATH de Python
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

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
        
        # Variables para controlar el sidebar
        self.sidebar_visible = True
        self.sidebar_width = 240

        # CREAR VENTANA OCULTA PRIMERO — así messagebox tiene padre válido
        self.root = tk.Tk()
        self.root.withdraw()

        # Inicializar la base de datos (messagebox ya tiene padre)
        if not self.initialize_database():
            messagebox.showerror("Error Fatal",
                "No se pudo inicializar la base de datos. El programa se cerrará.",
                parent=self.root)
            self.root.destroy()
            sys.exit(1)

        self.root.title("Módulo de Productos Afines")

        # Configurar icono de la ventana si existe
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'icons', 'app_icon.ico')
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:  # noqa: E722
            pass

        # Aplicar tema moderno
        style = ThemedStyle(self.root)
        style.set_theme("arc")

        # CONFIGURAR TODO ANTES DE MOSTRAR
        self.setup_window()
        self.setup_styles()
        self.load_icons()
        self.create_layout()

        # Mostrar la pantalla de bienvenida inicial
        self.show_welcome_screen()

        # MOSTRAR VENTANA SOLO DESPUÉS DE QUE TODO ESTÉ CONFIGURADO
        self.root.deiconify()  # MOSTRAR VENTANA
        self.root.focus_force()  # DARLE FOCO

        # Manejar el cierre de la ventana principal
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.setup_keyboard_shortcuts()

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

    def create_rounded_button(self, parent, text, bg_color, hover_color, command, icon=None, radius=18):
        from PIL import Image, ImageDraw, ImageTk
        if not hasattr(self, "_button_images"):
            self._button_images = []

        wrapper = tk.Frame(parent, bg=self.COLORS['primary'], highlightthickness=0, bd=0)
        wrapper.pack(fill="x", padx=16, pady=10)

        pill_height = 46
        def make_rounded_bg(width, color_hex):
            width = max(60, int(width))
            img = Image.new("RGBA", (width, pill_height), (0, 0, 0, 0))
            ImageDraw.Draw(img).rounded_rectangle([0, 0, width, pill_height], radius=radius, fill=color_hex)
            return ImageTk.PhotoImage(img)

        pill = tk.Label(wrapper, bg=self.COLORS['primary'], bd=0, highlightthickness=0)
        pill.pack(fill="x", padx=2, pady=2)

        btn = tk.Button(
            pill, text=text, font=('Segoe UI', 11, 'bold'),
            bg=bg_color, activebackground=bg_color,
            fg=self.COLORS['white'] if bg_color != self.COLORS['light'] else self.COLORS['text_dark'],
            relief='flat', borderwidth=0, padx=16, pady=10, cursor='hand2',
            highlightthickness=0, command=command
        )
        if icon:
            btn.config(image=icon, compound='left')
        btn.pack(fill="x")

        def init_bg():
            wrapper.update_idletasks()
            w = pill.winfo_width()
            if not w or w <= 1:
                wrapper.after(50, init_bg)
                return
            img_normal = make_rounded_bg(w, bg_color)
            img_hover = make_rounded_bg(w, hover_color)
            pill._bg_img_normal = img_normal
            pill._bg_img_hover = img_hover
            pill.config(image=img_normal)
            self._button_images.extend([img_normal, img_hover])

            def on_enter(_): 
                if getattr(pill, "_bg_img_hover", None): 
                    pill.config(image=pill._bg_img_hover)
            def on_leave(_): 
                if getattr(pill, "_bg_img_normal", None): 
                    pill.config(image=pill._bg_img_normal)
            for wdg in (pill, btn, wrapper):
                wdg.bind('<Enter>', on_enter)
                wdg.bind('<Leave>', on_leave)

        wrapper.after(50, init_bg)
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
            'configurar_servidor': 'configurar_servidor.png',
            'import_export': 'importar-exportar.png',
            'ingreso': 'ingreso.png',
            'kardex': 'kardex.png',
            'demanda': 'demanda-real.png',
            'correcciones': 'correcion.png',
            'bres': 'bres.png',
            'cantidad_solicitada': 'cantidad_solicitada.png',
            'balance': 'balance.png',
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

  
    def create_navigation_menu(self, parent):
        """Crea el menú de navegación con estructura de árbol colapsable"""
        rol = self.usuario['rol']
        
        # Frame contenedor del menú árbol
        tree_container = tk.Frame(parent, bg=self.COLORS['primary'])
        tree_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Diccionario para mantener el estado de expansión de cada categoría
        self.menu_expanded = {}
        
        # Diccionario para almacenar los frames de subcategorías
        self.submenu_frames = {}
        
        # Definir la estructura del menú por categorías
        menu_structure = self.get_menu_structure(rol)
        
        # Crear cada categoría del menú
        for category, items in menu_structure.items():
            self.create_menu_category(tree_container, category, items)

    def get_menu_structure(self, rol):
        """Define la estructura del menú según el rol del usuario"""
        menu_structure = {}
        
        if rol in ("admin", "super_admin"):
            menu_structure["👥 ADMINISTRACIÓN"] = [
                ("Gestión de Usuarios", self.load_gestion_usuarios, 'usuarios'),
                ("Gestión de Insumos", self.load_gestion_insumos, 'insumos'),
                ("Gestión de Servicios", self.load_gestion_servicios, 'servicios'),
                ("Gestión de Movimientos", self.load_gestion_movimientos, 'movimientos'),
            ]
            
            menu_structure["⚙️ CONFIGURACIÓN"] = [
                ("Configurar Servidor", self.load_configurar_servidor, 'configurar_servidor'),
                ("Importar/Exportar", self.load_importar_exportar, 'import_export'),
            ]
        elif rol == "usuario":
            # Para usuarios normales, solo exponemos Importar/Exportar en Configuración
            menu_structure["⚙️ CONFIGURACIÓN"] = [
                ("Importar/Exportar", self.load_importar_exportar, 'import_export'),
            ]
        
        if rol in ("usuario", "admin", "super_admin"):
            menu_structure["📦 OPERACIONES"] = [
                ("Ingreso de Insumos", self.load_ingreso_insumos, 'ingreso'),
                ("Correcciones", self.load_correccion_movimientos, 'correcciones'),
            ]
            
            menu_structure["📊 REPORTES"] = [
                ("Reporte Kardex", self.load_reporte_kardex, 'kardex'),
                ("Reporte Demanda Real", self.load_reporte_demanda_real, 'demanda'),
                ("Reporte BRES", self.load_reporte_bres, 'bres'),
                ("Reporte Cantidad Solicitada", self.load_reporte_cantidad_solicitada, 'cantidad_solicitada'),
                ("Reporte Balance Bodega", self.load_reporte_balance_bodega, 'balance'),
            ]
        
        return menu_structure

    def create_layout(self):
        """Crea el layout principal de la aplicación"""
        # **SIDEBAR (MENÚ LATERAL)** - Ancho aumentado para acomodar texto completo
        self.sidebar = ttk.Frame(self.root, style='Sidebar.TFrame', width=self.sidebar_width)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.sidebar.grid_propagate(False)  # Mantener ancho fijo - CRÍTICO
        self.sidebar.pack_propagate(False)   # También prevenir expansión con pack

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
        """Crea el menú lateral con botón toggle centrado verticalmente"""
        # Header
        header_frame = tk.Frame(self.sidebar, bg=self.COLORS['primary'], height=140)
        header_frame.pack(fill="x", pady=0)
        header_frame.pack_propagate(False)

        # Logo
        if self.icons.get('logo'):
            tk.Label(header_frame, image=self.icons['logo'], 
                    bg=self.COLORS['primary']).pack(pady=(25, 8))
        else:
            tk.Frame(header_frame, bg=self.COLORS['primary'], height=30).pack()

        tk.Label(header_frame, text="MÓDULO DE PRODUCTOS", 
                font=('Segoe UI', 12, 'bold'),
                fg=self.COLORS['white'], 
                bg=self.COLORS['primary']).pack(pady=(5, 2))
        tk.Label(header_frame, text="AFINES", 
                font=('Segoe UI', 12, 'bold'),
                fg=self.COLORS['white'], 
                bg=self.COLORS['primary']).pack(pady=(0, 15))

        # Contenedor para botones inferiores (toggle y salir)
        bottom_buttons_frame = tk.Frame(self.sidebar, bg=self.COLORS['primary'])
        bottom_buttons_frame.pack(fill="x", side="bottom", pady=(0, 20))

        # Botón para ocultar menú con texto y flecha
        self.toggle_menu_btn = tk.Button(
            bottom_buttons_frame,
            text="◀ Ocultar menú",
            font=('Segoe UI', 11, 'bold'),
            bg=self.COLORS['primary'],
            fg=self.COLORS['white'],
            activebackground=self.COLORS['secondary'],
            activeforeground=self.COLORS['white'],
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            cursor='hand2',
            command=self.toggle_sidebar
        )
        self.toggle_menu_btn.pack(fill="x", padx=16, pady=(0, 10))

        # Botón Salir debajo del toggle
        exit_btn = tk.Button(
            bottom_buttons_frame,
            text="  Salir del Sistema",
            font=('Segoe UI', 11, 'bold'),
            bg=self.COLORS['primary'],
            fg=self.COLORS['white'],
            activebackground=self.COLORS['secondary'],
            activeforeground=self.COLORS['white'],
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            cursor='hand2',
            command=self.on_closing
        )
        if self.icons.get('salir'):
            exit_btn.config(image=self.icons['salir'], compound='left')
        exit_btn.pack(fill="x", padx=16)

        # Hover para toggle_menu_btn
        def on_toggle_enter(e):
            self.toggle_menu_btn.config(bg=self.COLORS['secondary'])
        def on_toggle_leave(e):
            self.toggle_menu_btn.config(bg=self.COLORS['primary'])
        self.toggle_menu_btn.bind('<Enter>', on_toggle_enter)
        self.toggle_menu_btn.bind('<Leave>', on_toggle_leave)

        # Hover para exit_btn
        def on_exit_enter(e):
            exit_btn.config(bg=self.COLORS['secondary'])
        def on_exit_leave(e):
            exit_btn.config(bg=self.COLORS['primary'])
        exit_btn.bind('<Enter>', on_exit_enter)
        exit_btn.bind('<Leave>', on_exit_leave)

        # Contenedor del menú con scroll (antes del bottom_buttons_frame)
        nav_container = tk.Frame(self.sidebar, bg=self.COLORS['primary'])
        nav_container.pack(fill="both", expand=True, padx=0, pady=10)

        canvas = tk.Canvas(nav_container, bg=self.COLORS['primary'], 
                        highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(nav_container, orient="vertical", 
                                command=canvas.yview)
        nav_frame = tk.Frame(canvas, bg=self.COLORS['primary'])

        nav_frame.bind("<Configure>", 
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=nav_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.create_navigation_menu(nav_frame)

    def create_menu_category(self, parent, category_name, items):
        # Frame principal de la categoría con ancho máximo
        category_frame = tk.Frame(parent, bg=self.COLORS['primary'])
        category_frame.pack(fill="x", pady=2)
        
        # Inicializar estado colapsado
        self.menu_expanded[category_name] = False
        
        # Frame para el header de la categoría (clickeable) con ancho fijo
        header_frame = tk.Frame(category_frame, bg=self.COLORS['primary'], cursor='hand2')
        header_frame.pack(fill="x")
        
        # Crear el botón de expansión/colapso
        expand_button = tk.Button(
            header_frame,
            text="▶",
            font=('Segoe UI', 10),
            fg=self.COLORS['white'],
            bg=self.COLORS['primary'],
            activeforeground=self.COLORS['hover'],
            activebackground=self.COLORS['primary'],
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            width=2,
            cursor='hand2'
        )
        expand_button.pack(side="left", padx=(15, 5))

        # Opcional: efecto hover para cambiar el color del texto
        def on_enter(e):
            if not self.menu_expanded[category_name]:
                expand_button.config(fg=self.COLORS['hover'])

        def on_leave(e):
            if not self.menu_expanded[category_name]:
                expand_button.config(fg=self.COLORS['white'])

        expand_button.bind('<Enter>', on_enter)
        expand_button.bind('<Leave>', on_leave)
        
        # Label del título de la categoría con texto truncado si es necesario
        category_label = tk.Label(header_frame,
                                text=category_name,
                                font=('Segoe UI', 10, 'bold'),
                                fg=self.COLORS['white'],
                                bg=self.COLORS['primary'],
                                anchor='w',
                                cursor='hand2')
        category_label.pack(side="left", fill="x", expand=True, padx=(0, 15))
        
        # Frame para los elementos hijo (inicialmente oculto) con ancho controlado
        submenu_frame = tk.Frame(category_frame, bg=self.COLORS['primary'], relief='flat', borderwidth=0)
        self.submenu_frames[category_name] = submenu_frame
        
        # Agregar elementos hijo
        for item_text, item_command, icon_key in items:
            self.create_tree_menu_item(submenu_frame, item_text, item_command, icon_key)
        
        # Función para alternar expansión/colapso
        def toggle_category():
            self.toggle_menu_category(category_name, expand_button, submenu_frame)
        
        # Vincular eventos de clic a todos los elementos del header
        header_frame.bind('<Button-1>', lambda e: toggle_category())
        expand_button.bind('<Button-1>', lambda e: toggle_category())
        category_label.bind('<Button-1>', lambda e: toggle_category())
        
        # Efectos hover para el header completo
        def on_header_enter(e):
            if not self.menu_expanded[category_name]:
                header_frame.config(bg=self.COLORS['secondary'])
                expand_button.config(bg=self.COLORS['secondary'])
                category_label.config(bg=self.COLORS['secondary'])
        
        def on_header_leave(e):
            if not self.menu_expanded[category_name]:
                header_frame.config(bg=self.COLORS['primary'])
                expand_button.config(bg=self.COLORS['primary'])
                category_label.config(bg=self.COLORS['primary'])
        
        # Guardar referencias para poder desvincular/vincular
        header_frame._on_enter = on_header_enter
        header_frame._on_leave = on_header_leave

        header_frame.bind('<Enter>', on_header_enter)
        header_frame.bind('<Leave>', on_header_leave)
        expand_button.bind('<Enter>', on_header_enter)
        expand_button.bind('<Leave>', on_header_leave)
        category_label.bind('<Enter>', on_header_enter)
        category_label.bind('<Leave>', on_header_leave)

    def create_tree_menu_item(self, parent, text, command, icon_key):
        """Crea un elemento individual del menú árbol sin recuadros y con efecto hover"""
        # Frame contenedor sin padding para eliminar recuadros transparentes
        item_frame = tk.Frame(parent, bg=self.COLORS['secondary'])
        item_frame.pack(fill="x", padx=0, pady=0)  # Sin pady para eliminar espacios
        
        # Frame interno para el contenido - mismo color de fondo que el padre
        inner_frame = tk.Frame(item_frame, bg=self.COLORS['secondary'])
        inner_frame.pack(fill="x", padx=(25, 15))
        
        # Indicador de jerarquía
        tree_indicator = tk.Label(inner_frame,
                                text="├─",
                                font=('Consolas', 9),
                                fg=self.COLORS['white'],
                                bg=self.COLORS['secondary'],
                                width=2)
        tree_indicator.pack(side="left")
        
        # Mostrar texto completo sin truncar
        display_text = text
        
        # Botón del item del menú - configurado para fusionarse con el fondo
        item_button = tk.Button(inner_frame,
                            text=f" {display_text}",
                            font=('Segoe UI', 9),
                            bg=self.COLORS['secondary'],
                            fg=self.COLORS['white'],
                            relief='flat',
                            borderwidth=0,
                            highlightthickness=0,  # Eliminar borde de foco
                            padx=5,
                            pady=8,  # Ligeramente más alto para mejor área de clic
                            anchor='w',
                            cursor='hand2',
                            command=command)
        
        # Agregar icono si existe
        if self.icons.get(icon_key):
            item_button.config(image=self.icons[icon_key], compound='left')
        
        item_button.pack(side="left", fill="x", expand=True)
        
        # Efectos hover que cubren toda el área del elemento
        def on_item_enter(e):
            # Cambiar todos los elementos para un hover uniforme
            item_frame.config(bg=self.COLORS['hover'])
            inner_frame.config(bg=self.COLORS['hover'])
            tree_indicator.config(bg=self.COLORS['hover'])
            item_button.config(bg=self.COLORS['hover'])
        
        def on_item_leave(e):
            # Restaurar todos los colores
            item_frame.config(bg=self.COLORS['secondary'])
            inner_frame.config(bg=self.COLORS['secondary'])
            tree_indicator.config(bg=self.COLORS['secondary'])
            item_button.config(bg=self.COLORS['secondary'])
        
        def on_item_click(e):
            # Efecto visual de clic en todo el elemento
            item_frame.config(bg=self.COLORS['active'])
            inner_frame.config(bg=self.COLORS['active'])
            tree_indicator.config(bg=self.COLORS['active'])
            item_button.config(bg=self.COLORS['active'])
            # Restaurar color después del clic
            item_frame.after(150, lambda: on_item_leave(None))
        
        # Vincular eventos a todos los elementos para área de hover más grande
        for widget in [item_frame, inner_frame, tree_indicator, item_button]:
            widget.bind('<Enter>', on_item_enter)
            widget.bind('<Leave>', on_item_leave)
            widget.bind('<Button-1>', on_item_click)

    def toggle_menu_category(self, category_name, expand_button, submenu_frame):
        is_expanded = self.menu_expanded[category_name]
        parent_frame = expand_button.master

        if is_expanded:
            # Colapsar
            submenu_frame.pack_forget()
            expand_button.config(text="▶")
            self.menu_expanded[category_name] = False

            # Restaurar colores del header
            parent_frame.config(bg=self.COLORS['primary'])
            expand_button.config(bg=self.COLORS['primary'])
            for child in parent_frame.winfo_children():
                if isinstance(child, tk.Label) and child != expand_button:
                    child.config(bg=self.COLORS['primary'])

            # Volver a vincular eventos hover
            parent_frame.bind('<Enter>', parent_frame._on_enter)
            parent_frame.bind('<Leave>', parent_frame._on_leave)
            expand_button.bind('<Enter>', parent_frame._on_enter)
            expand_button.bind('<Leave>', parent_frame._on_leave)
            for widget in parent_frame.winfo_children():
                if widget != expand_button:
                    widget.bind('<Enter>', parent_frame._on_enter)
                    widget.bind('<Leave>', parent_frame._on_leave)

        else:
            # Expandir
            submenu_frame.pack(fill="x")
            expand_button.config(text="▼")
            self.menu_expanded[category_name] = True

            # Cambiar colores del header
            parent_frame.config(bg=self.COLORS['secondary'])
            expand_button.config(bg=self.COLORS['secondary'])
            for child in parent_frame.winfo_children():
                if isinstance(child, tk.Label) and child != expand_button:
                    child.config(bg=self.COLORS['secondary'])

            # Desvincular eventos hover para desactivar hover mientras está expandido
            parent_frame.unbind('<Enter>')
            parent_frame.unbind('<Leave>')
            expand_button.unbind('<Enter>')
            expand_button.unbind('<Leave>')
            for widget in parent_frame.winfo_children():
                if widget != expand_button:
                    widget.unbind('<Enter>')
                    widget.unbind('<Leave>')

        self.sidebar.update_idletasks()

    def animate_menu_transition(self):
        """Proporciona una transición suave para el menú"""
        # Forzar actualización del layout
        if hasattr(self, 'sidebar'):
            self.sidebar.update_idletasks()

    def expand_all_menu_categories(self):
        """Expande todas las categorías del menú"""
        for category_name in self.menu_expanded.keys():
            if not self.menu_expanded[category_name]:
                # Buscar el botón de expansión y el frame correspondiente
                for widget in self.sidebar.winfo_children():
                    if isinstance(widget, tk.Frame):
                        for child in widget.winfo_children():
                            if isinstance(child, tk.Frame):
                                for grandchild in child.winfo_children():
                                    if isinstance(grandchild, tk.Frame):
                                        for item in grandchild.winfo_children():
                                            if (isinstance(item, tk.Label) and 
                                                hasattr(item, 'cget') and 
                                                item.cget('text') in ['▶', '▼']):
                                                if item.cget('text') == '▶':
                                                    submenu_frame = self.submenu_frames.get(category_name)
                                                    if submenu_frame:
                                                        self.toggle_menu_category(category_name, item, submenu_frame)

    def collapse_all_menu_categories(self):
        """Colapsa todas las categorías del menú"""
        for category_name in self.menu_expanded.keys():
            if self.menu_expanded[category_name]:
                # Similar al método anterior pero para colapsar
                for widget in self.sidebar.winfo_children():
                    if isinstance(widget, tk.Frame):
                        for child in widget.winfo_children():
                            if isinstance(child, tk.Frame):
                                for grandchild in child.winfo_children():
                                    if isinstance(grandchild, tk.Frame):
                                        for item in grandchild.winfo_children():
                                            if (isinstance(item, tk.Label) and 
                                                hasattr(item, 'cget') and 
                                                item.cget('text') in ['▶', '▼']):
                                                if item.cget('text') == '▼':
                                                    submenu_frame = self.submenu_frames.get(category_name)
                                                    if submenu_frame:
                                                        self.toggle_menu_category(category_name, item, submenu_frame)

    def create_nav_button(self, parent, text, command, icon_key):
        """Crea un botón de navegación"""
        btn = tk.Button(parent,
                    text=f"  {text}",
                    font=('Segoe UI', 11),
                    bg=self.COLORS['primary'],
                    fg=self.COLORS['white'],
                    relief='flat',
                    borderwidth=0,
                    padx=15,
                    pady=6,
                    anchor='w',
                    cursor='hand2',
                    command=command)

        # Agregar icono si existe
        if self.icons.get(icon_key):
            btn.config(image=self.icons[icon_key], compound='left')

        btn.pack(fill="x", padx=10, pady=1)

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
        """Crea el área de contenido principal con mejor alineación"""
        self.main_content_frame = ttk.Frame(self.main_area, style='MainArea.TFrame')
        self.main_content_frame.pack(fill="both", expand=True, padx=0, pady=0)  # Sin padding aquí
        
        # Configurar grid para control preciso
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        self.main_content_frame.grid_columnconfigure(0, weight=1)

    def create_status_bar(self):
        """Crea la barra de estado con botón mostrar menú a la izquierda, usuario/servidor en el centro y fecha a la derecha"""
        # Información del usuario
        nombre_usuario = self.usuario.get('nombre_completo', self.usuario.get('username', 'Usuario'))
        rol_usuario = self.usuario.get('rol', '')

        # Obtener nombre del servidor desde la configuración de conexión
        from src.database.db_manager import get_config
        config = get_config()
        nombre_servidor = config.get('host', 'Servidor desconocido')

        import datetime
        fecha_actual = datetime.datetime.now().strftime("%d/%m/%Y")

        self.status_bar.config(padding=5)

        # Botón mostrar menú (izquierda)
        self.show_menu_btn = tk.Button(
            self.status_bar,
            text="▶ Mostrar menú",
            font=('Segoe UI', 10, 'bold'),
            bg=self.COLORS['secondary'],
            fg=self.COLORS['white'],
            activebackground=self.COLORS['primary'],
            activeforeground=self.COLORS['white'],
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            cursor='hand2',
            command=self.toggle_sidebar
        )
        self.show_menu_btn.pack(side="left", padx=(10,5), pady=2)

        # Mostrar u ocultar botón según estado inicial del sidebar
        if self.sidebar_visible:
            self.show_menu_btn.pack_forget()

        # Etiqueta usuario y servidor (centro)
        self.user_label = ttk.Label(
            self.status_bar,
            text=f"👤 Usuario: {nombre_usuario} ({rol_usuario})    🖥️ Servidor: {nombre_servidor}",
            style='StatusBar.TLabel'
        )
        self.user_label.pack(side="left", padx=10)

        # Etiqueta versión (centro derecha)
        self.version_label = ttk.Label(
            self.status_bar,
            text="Versión: 1.1",
            style='StatusBar.TLabel'
        )
        self.version_label.pack(side="left", padx=10)

        # Etiqueta fecha (derecha)
        self.date_label = ttk.Label(
            self.status_bar,
            text=f"📅 {fecha_actual}",
            style='StatusBar.TLabel'
        )
        self.date_label.pack(side="right", padx=10)

        # Hover para el botón mostrar menú
        def on_enter(e):
            self.show_menu_btn.config(bg=self.COLORS['primary'])
        def on_leave(e):
            self.show_menu_btn.config(bg=self.COLORS['secondary'])

        self.show_menu_btn.bind('<Enter>', on_enter)
        self.show_menu_btn.bind('<Leave>', on_leave)

    def show_welcome_screen(self):
        """Muestra la pantalla de bienvenida mejorada con mejor alineación"""
        self.clear_content_frame()
        
        # NO llamar reset_window_size() aquí si la ventana está oculta
        if self.root.winfo_viewable():
            self.reset_window_size()

        # Frame principal de bienvenida con mejor estructura
        welcome_frame = tk.Frame(self.main_content_frame, bg=self.COLORS['light'])
        welcome_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # Configurar el grid principal para mejor control
        welcome_frame.grid_rowconfigure(0, weight=0)  # Header
        welcome_frame.grid_rowconfigure(1, weight=0)  # Spacer
        welcome_frame.grid_rowconfigure(2, weight=1)  # Cards area
        welcome_frame.grid_rowconfigure(3, weight=0)  # Footer
        welcome_frame.grid_columnconfigure(0, weight=1)

        # === HEADER CARD (fila 0) ===
        header_container = tk.Frame(welcome_frame, bg=self.COLORS['light'])
        header_container.grid(row=0, column=0, sticky="ew", padx=40, pady=(40, 0))
        
        header_card = tk.Frame(header_container, bg=self.COLORS['white'], relief='solid', bd=1)
        header_card.pack(fill="x")
        
        header_content = tk.Frame(header_card, bg=self.COLORS['white'])
        header_content.pack(fill="x", padx=30, pady=25)

        # Título principal centrado
        title_label = tk.Label(
            header_content,
            text="¡Bienvenido al Sistema!",
            font=('Segoe UI', 28, 'bold'),
            fg=self.COLORS['primary'],
            bg=self.COLORS['white']
        )
        title_label.pack(anchor='center')

        # Subtítulo centrado
        subtitle_label = tk.Label(
            header_content,
            text=(
                "DIRECCIÓN DEPARTAMENTAL DE REDES INTEGRADAS\n"
                "DE SERVICIOS DE SALUD DE GUATEMALA\n"
                "ÁREA NOR ORIENTE"
            ),
            font=('Segoe UI', 14),
            fg=self.COLORS['text_light'],
            bg=self.COLORS['white'],
            justify='center'
        )
        subtitle_label.pack(anchor='center', pady=(15, 0))

        # === SPACER (fila 1) ===
        spacer = tk.Frame(welcome_frame, bg=self.COLORS['light'], height=30)
        spacer.grid(row=1, column=0, sticky="ew")

        # === CARDS AREA (fila 2) ===
        cards_container = tk.Frame(welcome_frame, bg=self.COLORS['light'])
        cards_container.grid(row=2, column=0, sticky="nsew", padx=40, pady=0)

        # Una sola tarjeta que ocupe todo el ancho (como el header)
        cards_container.grid_rowconfigure(0, weight=1)
        cards_container.grid_columnconfigure(0, weight=1)

        # Crear UNA SOLA tarjeta combinada que ocupe todo el ancho
        self.create_combined_info_card(
            cards_container,
            [
                ("🎯 Funcionalidades Principales", [
                    "• Gestión completa de insumos médicos",
                    "• Control de inventarios en tiempo real", 
                    "• Generación de reportes especializados",
                    "• Seguimiento de movimientos detallado",
                    "• Administración de usuarios y permisos"
                ]),
                ("🚀 Inicio Rápido", [
                    "• Seleccione una opción del menú lateral",
                    "• Use 'Ingreso de Insumos' para registrar",
                    "• Genere reportes desde el menú",
                    "• Consulte el Kardex para seguimiento",
                    "• Configure el sistema en Gestión"
                ])
            ],
            0, 0
        )

        # === FOOTER (fila 3) ===
        footer_container = tk.Frame(welcome_frame, bg=self.COLORS['light'])
        footer_container.grid(row=3, column=0, sticky="ew", pady=(20, 20))
        
        # Frame interno del footer para centrar contenido
        footer_content = tk.Frame(footer_container, bg=self.COLORS['light'])
        footer_content.pack(expand=True)

        user_info = f"Sesión iniciada como: {self.usuario.get('nombre_completo', 'Usuario')} ({self.usuario.get('rol', '')})"
        footer_label = tk.Label(
            footer_content,
            text=user_info,
            font=('Segoe UI', 11),
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['light']
        )
        footer_label.pack()

    def create_combined_info_card(self, parent, sections_data, row, col):
        """Crea una tarjeta combinada que ocupa todo el ancho con dos secciones lado a lado"""
        # Frame principal que ocupa todo el ancho disponible
        card_frame = tk.Frame(
            parent,
            bg=self.COLORS['white'],
            relief='solid',
            borderwidth=1
        )
        card_frame.grid(row=row, column=col, sticky="nsew", pady=10)
        
        # Configurar grid interno para dos columnas
        card_frame.grid_rowconfigure(0, weight=1)
        card_frame.grid_columnconfigure(0, weight=1)
        card_frame.grid_columnconfigure(1, weight=1)
        
        # Crear cada sección (Funcionalidades e Inicio Rápido)
        for section_col, (section_title, section_items) in enumerate(sections_data):
            # Contenedor de cada sección
            section_container = tk.Frame(card_frame, bg=self.COLORS['white'])
            section_container.grid(row=0, column=section_col, sticky="nsew", padx=25, pady=20)
            
            # Título de la sección
            title_label = tk.Label(
                section_container,
                text=section_title,
                font=('Segoe UI', 16, 'bold'),
                fg=self.COLORS['primary'],
                bg=self.COLORS['white'],
                anchor="w"
            )
            title_label.pack(anchor="w", pady=(0, 15))
            
            # Items de la sección
            for item in section_items:
                item_label = tk.Label(
                    section_container,
                    text=item,
                    font=('Segoe UI', 11),
                    fg=self.COLORS['text_dark'],
                    bg=self.COLORS['white'],
                    anchor="w",
                    justify="left",
                    wraplength=280  # Ajustado para dos columnas
                )
                item_label.pack(anchor="w", pady=(0, 8))
        
        # Línea divisoria vertical centrada entre las dos secciones
        divider = tk.Frame(card_frame, bg=self.COLORS['light'], width=1)
        divider.grid(row=0, column=0, columnspan=2, sticky="ns")
        divider.place(relx=0.5, rely=0, relheight=1, anchor="n")

    def create_info_card(self, parent, title, items, row, col):
        """Crea una tarjeta de información con dimensiones uniformes"""
        # Frame contenedor con padding uniforme
        card_container = tk.Frame(parent, bg=self.COLORS['light'])
        card_container.grid(row=row, column=col, sticky="nsew", padx=15, pady=10)
        
        # Configurar el contenedor para expansión uniforme
        card_container.grid_rowconfigure(0, weight=1)
        card_container.grid_columnconfigure(0, weight=1)
        
        # Tarjeta principal con dimensiones fijas
        card_frame = tk.Frame(
            card_container,
            bg=self.COLORS['white'],
            relief='solid',
            borderwidth=1
        )
        card_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configurar grid interno de la tarjeta
        card_frame.grid_rowconfigure(0, weight=0)  # Título
        card_frame.grid_rowconfigure(1, weight=1)  # Contenido
        card_frame.grid_columnconfigure(0, weight=1)
        
        # === TÍTULO ===
        title_container = tk.Frame(card_frame, bg=self.COLORS['white'])
        title_container.grid(row=0, column=0, sticky="ew", padx=25, pady=(20, 10))
        
        title_label = tk.Label(
            title_container,
            text=title,
            font=('Segoe UI', 16, 'bold'),
            fg=self.COLORS['primary'],
            bg=self.COLORS['white'],
            anchor="w"
        )
        title_label.pack(anchor="w")

        # === CONTENIDO ===
        content_container = tk.Frame(card_frame, bg=self.COLORS['white'])
        content_container.grid(row=1, column=0, sticky="nsew", padx=25, pady=(0, 20))
        
        # Crear items con espaciado uniforme
        for i, item in enumerate(items):
            item_label = tk.Label(
                content_container,
                text=item,
                font=('Segoe UI', 11),
                fg=self.COLORS['text_dark'],
                bg=self.COLORS['white'],
                anchor="w",
                justify="left",
                wraplength=300  # Evitar que el texto se desborde
            )
            item_label.pack(anchor="w", pady=(0, 8))

    def center_window(self, width, height):
        """Centra la ventana en la pantalla tanto horizontal como verticalmente"""
        # NO LLAMAR update_idletasks() aquí si la ventana está oculta
        if self.root.winfo_viewable():
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

    def toggle_sidebar(self):
        if self.sidebar_visible:
            # Ocultar sidebar
            self.sidebar.grid_forget()
            self.sidebar_visible = False

            # Mostrar botón en barra de estado
            self.show_menu_btn.pack(side="right", padx=10, pady=2)
        else:
            # Mostrar sidebar
            self.sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
            self.sidebar_visible = True

            # Ocultar botón en barra de estado
            self.show_menu_btn.pack_forget()

        self.root.update_idletasks()

    def setup_keyboard_shortcuts(self):
        """Configura atajos de teclado"""
        self.root.bind('<F9>', lambda e: self.toggle_sidebar())
        self.root.bind('<Control-b>', lambda e: self.toggle_sidebar())
    
    def initialize_database(self):
        """Inicializa la base de datos y verifica su estructura en MySQL"""
        try:
            # Crear base de datos y tablas si no existen
            if not crear_base_datos():
                raise Exception("No se pudo crear la base de datos")

            # Verificar que las tablas existan
            if not verificar_tablas():
                # En MySQL no hay archivo local que eliminar, solo recrear tablas
                print("La estructura de la base de datos es incorrecta. Recreándola...")
                if not crear_base_datos():
                    raise Exception("No se pudo recrear la base de datos")
                print("Base de datos recreada correctamente")

            return True

        except Exception as e:
            print(f"Error al inicializar la base de datos: {e}")
            parent = getattr(self, 'root', None)
            messagebox.showerror("Error", f"Error al inicializar la base de datos: {str(e)}",
                                 parent=parent)
            return False

    def verify_database_connection(self):
        try:
            from src.database.db_manager import verificar_conexion, get_config
            try:
                ok, err = verificar_conexion(return_error=True)
            except TypeError:
                ok = verificar_conexion()
                err = None if ok else "Fallo de conexión"
            if ok:
                return True
            cfg = get_config()
            messagebox.showerror(
                "Error de conexión",
                f"No se pudo conectar a MySQL.\nServidor: {cfg.get('host')}:{cfg.get('port')}\nUsuario: {cfg.get('user')}\nBase: {cfg.get('database')}\n\nDetalle: {err}"
            )
            return False
        except Exception as e:
            messagebox.showerror("Error de conexión", f"Fallo al verificar la conexión.\nDetalle: {e}")
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
                    except:  # noqa: E722
                        pass
                self.pantalla_actual = None

            if hasattr(self, 'main_content_frame') and self.main_content_frame.winfo_exists():
                for widget in self.main_content_frame.winfo_children():
                    try:
                        widget.destroy()
                    except:  # noqa: E722
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
        
    def load_configurar_servidor(self):
        if not self.verify_database_connection():
            messagebox.showerror("Error", "No se puede conectar a la base de datos")
            return
        self.clear_content_frame()
        self.reset_window_size()
        self.pantalla_actual = ConfigurarServidor(self.main_content_frame, self)

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
    
    def load_reporte_cantidad_solicitada(self):
        if not self.verify_database_connection():
            messagebox.showerror("Error", "No se puede conectar a la base de datos")
            return
        self.clear_content_frame()
        self.reset_window_size()
        self.pantalla_actual = ReporteCantidadSolicitada(self.main_content_frame, self)
    
    def load_reporte_balance_bodega(self):
        if not self.verify_database_connection():
            messagebox.showerror("Error", "No se puede conectar a la base de datos")
            return
        self.clear_content_frame()
        self.reset_window_size()
        self.pantalla_actual = ReporteBalanceBodega(self.main_content_frame, self)

    def load_importar_exportar(self):
        if not self.verify_database_connection():
            messagebox.showerror("Error", "No se puede conectar a la base de datos")
            return
        self.clear_content_frame()
        self.reset_window_size()
        try:
            from src.database import DB_PATH
            db_path = DB_PATH
        except:  # noqa: E722
            db_path = 'database.db'
        self.pantalla_actual = ImportarExportarManager(self.main_content_frame, self)
        self.pantalla_actual.db_path = db_path

    def run(self):
        """Ejecuta la aplicación"""
        self.root.mainloop()