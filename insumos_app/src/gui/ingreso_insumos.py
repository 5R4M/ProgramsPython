import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
import sys
import os
from ttkwidgets.autocomplete import AutocompleteCombobox

import os

# Agregar el directorio raíz del proyecto al PATH de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.db_manager import (
    obtener_areas,
    obtener_distritos_por_area,
    obtener_distritos,
    obtener_tipos_servicio_por_distrito,
    obtener_servicios_por_tipo,
    obtener_tipos_insumo,
    obtener_insumos_por_tipo,
    obtener_tipos_movimiento,
    obtener_id_distrito,
    obtener_id_tipo_servicio,
    obtener_id_servicio,
    obtener_id_tipo_insumo,
    obtener_id_insumo,
    obtener_id_presentacion,
    obtener_id_tipo_movimiento,
    guardar_movimiento
)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        # En desarrollo, base_path es la raíz del proyecto (subir un nivel desde gui)
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(base_path, relative_path)

class IngresoInsumos:
    def __init__(self, parent_frame, main_window):
        
        self.parent = parent_frame
        self.main_window = main_window
        
        self.manual_widths = {}
        self.auto_resize_enabled = True

        # Variables para los combobox
        self.distrito_var = tk.StringVar()
        self.tipo_servicio_var = tk.StringVar()
        self.servicio_var = tk.StringVar()
        self.tipo_insumo_var = tk.StringVar()
        self.insumo_var = tk.StringVar()
        self.presentacion_var = tk.StringVar()
        self.tipo_movimiento_var = tk.StringVar()
        self.salida_distrito_var = tk.StringVar()
        self.salida_tipo_servicio_var = tk.StringVar()
        self.salida_servicio_var = tk.StringVar()
        self.lote_var = tk.StringVar()
        
        # Variable para radio buttons nivel de bodega
        self.nivel_bodega_var = tk.StringVar(value="area")  

        # Constantes para el diseño
        self.LABEL_WIDTH = 15
        self.WIDGET_WIDTH = 25
        self.PADDING_X = 10
        self.PADDING_Y = 5
        
        self.setup_styles()
        self.cargar_iconos()
        
        self.setup_ui()
        self.setup_bindings()
        self.actualizar_estado_comboboxes()  
        self.setup_window_behavior()
    
    def setup_window_behavior(self):
        """Configura el comportamiento de la ventana para iniciar minimizada"""
        # Obtener la ventana principal
        root = self.parent.winfo_toplevel()
        
        # **CONFIGURAR TAMAÑO INICIAL COMPACTO**
        initial_width = 1400
        initial_height = 900
        
        # Centrar ventana
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - initial_width) // 2
        y = (screen_height - initial_height) // 2
        
        # **ESTABLECER TAMAÑO INICIAL**
        root.geometry(f"{initial_width}x{initial_height}+{x}+{y}")
        root.minsize(1200, 700)  # Tamaño mínimo
        
        # **BIND PARA REDIMENSIONAMIENTO DINÁMICO**
        root.bind('<Configure>', self.on_window_configure)
        
        # **FORZAR ACTUALIZACIÓN INICIAL**
        root.after(100, self.update_layout)

    def on_window_configure(self, event):
        """Maneja el redimensionamiento de la ventana"""
        # Solo procesar eventos de la ventana principal, no de widgets internos
        if event.widget == self.parent.winfo_toplevel():
            self.parent.after_idle(self.update_layout)

    def update_layout(self):
        """Actualiza el layout cuando cambia el tamaño de la ventana"""
        try:
            # Solo actualizar el layout del frame principal
            self.parent.update_idletasks()
        except (tk.TclError, AttributeError):
            # Ignorar errores si los widgets no están listos
            pass
    
    def setup_styles(self):
        """Configurar estilos y colores para la interfaz"""
        # **PALETA DE COLORES PROFESIONAL**
        self.COLORS = {
            'primary': '#2E86AB',      # Azul principal
            'secondary': '#A23B72',    # Rosa/Morado
            'success': '#27AE60',      # Verde éxito
            'warning': '#F39C12',      # Naranja advertencia
            'danger': '#E74C3C',       # Rojo peligro
            'accent': '#8E44AD',       # Morado acento
            'light': '#F8F9FA',        # Gris muy claro
            'white': '#FFFFFF',        # Blanco
            'text_dark': '#2C3E50',    # Texto oscuro
            'text_light': '#7F8C8D',   # Texto claro
            'border': '#BDC3C7'        # Borde
        }
        
        # **CONFIGURACIÓN DE ANCHOS UNIFORMES**
        self.UNIFORM_WIDTH = 500  # Ancho uniforme para todos los frames principales
        self.WIDGET_WIDTH = 18    # Ancho uniforme para widgets (Entry, Combobox, etc.)
        self.BUTTON_WIDTH = 15    # Ancho uniforme para botones

        style = ttk.Style()
        
        # Estilo para LabelFrames (tarjetas)
        style.configure('Card.TLabelframe',
            background=self.COLORS['white'],
            relief='solid',
            borderwidth=1,
            labeloutside=False)
        
        style.configure('Card.TLabelframe.Label',
            background=self.COLORS['white'],
            foreground=self.COLORS['primary'],
            font=('Segoe UI', 9, 'bold'),
            padding=(8, 3))
        
        # Estilo para botones principales 
        style.configure('Primary.TButton',
            font=('Segoe UI', 9, 'bold'),  
            padding=(12, 6),  
            relief='flat',
            borderwidth=0,
            background=self.COLORS['primary'],
            foreground=self.COLORS['white'])
        
        style.map('Primary.TButton',
            background=[('active', '#1F5F8B'),
            ('pressed', '#1A4F7A')])
        
        # Estilo para botones de acción 
        style.configure('Action.TButton',
            font=('Segoe UI', 8),  
            padding=(10, 4),  
            relief='flat',
            borderwidth=0)
        
        # Estilo para labels de título
        style.configure('Title.TLabel',
            font=('Segoe UI', 14, 'bold'), 
            background=self.COLORS['white'],
            foreground=self.COLORS['primary'])
        
        style.configure('Subtitle.TLabel',
            font=('Segoe UI', 9),  
            background=self.COLORS['white'],
            foreground=self.COLORS['text_light'])
    
    def cargar_iconos(self):
        """Cargar iconos PNG"""
        try:
            # __file__ está en .../src/gui/archivo.py
            icons_path = resource_path(os.path.join('utils', 'icons'))
            
            self.icon_area = tk.PhotoImage(file=os.path.join(icons_path, "area.png")).subsample(3, 3)
            self.icon_distrito = tk.PhotoImage(file=os.path.join(icons_path, "distrito.png")).subsample(3, 3)
            self.icon_servicio = tk.PhotoImage(file=os.path.join(icons_path, "servicio_1.png")).subsample(3, 3)
            
            self.icon_agregar = tk.PhotoImage(file=os.path.join(icons_path, "agregar.png")).subsample(2, 2)
            
            self.icon_editar = tk.PhotoImage(file=os.path.join(icons_path, "editar.png")).subsample(2, 2)
            self.icon_eliminar = tk.PhotoImage(file=os.path.join(icons_path, "eliminar.png")).subsample(2, 2)
            self.icon_guardar = tk.PhotoImage(file=os.path.join(icons_path, "guardar.png")).subsample(2, 2)
            self.icon_cerrar = tk.PhotoImage(file=os.path.join(icons_path, "cerrar.png")).subsample(2, 2)
            
        except Exception as e:
            print(f"Error cargando iconos: {e}")
            self.icon_area = None
            self.icon_distrito = None
            self.icon_servicio = None
            self.icon_agregar = None
            self.icon_editar = None
            self.icon_eliminar = None
            self.icon_guardar = None
            self.icon_cerrar = None
        
    # 1. Métodos de configuración de UI
    
    def create_compact_frame(self, parent, title, bg_color='white', header_color='primary'):
        """Crear frame compacto con header profesional"""
        # Contenedor principal
        container = tk.Frame(parent, bg=self.COLORS['light'])
        container.pack(fill="x", padx=15, pady=3)  # Padding reducido
        
        # Frame principal más compacto
        main_frame = tk.Frame(container, 
                            bg=self.COLORS[bg_color], 
                            relief='solid', 
                            borderwidth=1)
        main_frame.pack(fill="x", padx=8, pady=3)  # Padding reducido
        
        # Header más compacto
        header = tk.Frame(main_frame, bg=self.COLORS[header_color], height=22)  # Altura reducida
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(header, 
                text=title, 
                font=('Segoe UI', 9, 'bold'),  # Fuente más pequeña
                fg=self.COLORS['white'], 
                bg=self.COLORS[header_color]).pack(side='left', padx=10, pady=3)  # Padding reducido
        
        # Contenido más compacto
        content = tk.Frame(main_frame, bg=self.COLORS[bg_color])
        content.pack(fill='x', padx=10, pady=6)  # Padding reducido
        
        return content, container
        
    def setup_ui(self):
        
        # Frame principal que contendrá el canvas y scrollbar
        self.main_frame = tk.Frame(self.parent, bg=self.COLORS['light'])
        self.main_frame.pack(fill="both", expand=True)
        
        # REEMPLAZAR CON UN FRAME FIJO:
        self.scrollable_frame = tk.Frame(self.main_frame, bg=self.COLORS['light'])
        self.scrollable_frame.pack(fill="both", expand=True)
        
        # **HEADER PRINCIPAL**
        header_frame = tk.Frame(self.scrollable_frame, bg=self.COLORS['primary'], height=70)
        
        header_frame.pack(fill='x', padx=0, pady=(10, 5))
        header_frame.pack_propagate(False)

        # Frame interno con padding - CAMBIO: fondo primary
        header_inner = tk.Frame(header_frame, bg=self.COLORS['primary'])
        header_inner.pack(fill='both', expand=True, padx=15, pady=5)

        # Título principal
        title_label = tk.Label(header_inner, 
                    text="Ingreso Insumos",
                    font=('Segoe UI', 12, 'bold'),  # Más compacto
                    fg=self.COLORS['white'],        # Texto blanco
                    bg=self.COLORS['primary'])      # Fondo primary
        title_label.pack(anchor='w')

        # Subtítulo - CAMBIO: texto blanco y fondo primary
        subtitle_label = tk.Label(header_inner,
                                text="Registre los movimientos de insumos de manera eficiente y organizada",
                                font=('Segoe UI', 8),
                                fg=self.COLORS['white'],     # CAMBIO: texto blanco
                                bg=self.COLORS['primary'])   # CAMBIO: fondo primary
        subtitle_label.pack(anchor='w', pady=(1, 0))
        
        # Frame Nivel de Bodega (radio buttons)
        nivel_container = tk.Frame(self.scrollable_frame, bg=self.COLORS['light'])
        nivel_container.pack(fill="x", padx=15, pady=3)
        
        self.frame_nivel_bodega = tk.Frame(nivel_container, 
                                        bg=self.COLORS['light'], 
                                        relief='solid', 
                                        borderwidth=1)
        self.frame_nivel_bodega.pack(fill="x", padx=8, pady=3)
        
        # Header del frame
        nivel_header = tk.Frame(self.frame_nivel_bodega, bg=self.COLORS['primary'], height=20)
        nivel_header.pack(fill='x')
        nivel_header.pack_propagate(False)
        
        tk.Label(nivel_header, 
                text="🏢 Nivel de Bodega", 
                font=('Segoe UI', 8, 'bold'),
                fg=self.COLORS['white'], 
                bg=self.COLORS['primary']).pack(side='left', padx=10, pady=2)
        
        # Contenido del frame
        nivel_content = tk.Frame(self.frame_nivel_bodega, bg=self.COLORS['light'])
        nivel_content.pack(fill='x', padx=12, pady=4)
        
        # **RADIO BUTTONS CON ESTILO MEJORADO - COMPACTO VERTICAL**
        rb_frame = tk.Frame(nivel_content, bg=self.COLORS['light'])
        rb_frame.pack(fill='x', pady=2)  # Cambio: de pady=5 a pady=2

        rb_area = tk.Radiobutton(rb_frame, 
                        text="Área",
                        image=self.icon_area,
                        compound='left',
                        variable=self.nivel_bodega_var, 
                        value="area",
                        command=self.actualizar_estado_comboboxes,
                        font=('Segoe UI', 8),  # Cambio: de 9 a 8
                        bg=self.COLORS['light'],
                        fg=self.COLORS['text_dark'],
                        selectcolor=self.COLORS['white'],
                        activebackground=self.COLORS['white'])

        rb_distrito = tk.Radiobutton(rb_frame, 
                                text="Distrito",
                                image=self.icon_distrito,
                                compound='left',
                                variable=self.nivel_bodega_var, 
                                value="distrito",
                                command=self.actualizar_estado_comboboxes,
                                font=('Segoe UI', 8),  # Cambio: de 9 a 8
                                bg=self.COLORS['light'],
                                fg=self.COLORS['text_dark'],
                                selectcolor=self.COLORS['white'],
                                activebackground=self.COLORS['white'])

        rb_servicio = tk.Radiobutton(rb_frame, 
                                    text="Servicio",
                                    image=self.icon_servicio,
                                    compound='left',
                                    variable=self.nivel_bodega_var, 
                                    value="servicio",
                                    command=self.actualizar_estado_comboboxes,
                                    font=('Segoe UI', 8),  # Cambio: de 9 a 8
                                    bg=self.COLORS['light'],
                                    fg=self.COLORS['text_dark'],
                                    selectcolor=self.COLORS['white'],
                                    activebackground=self.COLORS['white'])

        # Alineados a la izquierda con padding vertical reducido
        rb_area.grid(row=0, column=0, padx=(0, 20), pady=2, sticky="w")      # Cambio: de pady=5 a pady=2
        rb_distrito.grid(row=0, column=1, padx=(0, 20), pady=2, sticky="w")  # Cambio: de pady=5 a pady=2
        rb_servicio.grid(row=0, column=2, padx=(0, 20), pady=2, sticky="w")  # Cambio: de pady=5 a pady=2
        
        # **FRAME SERVICIOS MEJORADO**
        servicios_container = tk.Frame(self.scrollable_frame, bg=self.COLORS['light'])
        servicios_container.pack(fill="x", padx=15, pady=3)
        
        self.frame_servicios = tk.Frame(servicios_container, 
                                    bg=self.COLORS['light'], 
                                    relief='solid', 
                                    borderwidth=1)
        self.frame_servicios.pack(fill="x", padx=8, pady=3)
        
        # Header del frame
        servicios_header = tk.Frame(self.frame_servicios, bg=self.COLORS['primary'], height=20)
        servicios_header.pack(fill='x')
        servicios_header.pack_propagate(False)
        
        tk.Label(servicios_header, 
                text="🏥 Configuración de Servicios", 
                font=('Segoe UI', 8, 'bold'),
                fg=self.COLORS['white'], 
                bg=self.COLORS['primary']).pack(side='left', padx=10, pady=2)
        
        # Contenido del frame con grid mejorado - DISTRIBUCIÓN SIMÉTRICA
        servicios_content = tk.Frame(self.frame_servicios, bg=self.COLORS['light'])
        servicios_content.pack(fill='x', padx=12, pady=4)

        # Configurar grid para 4 columnas simétricas (2x2)
        for i in range(4):
            servicios_content.columnconfigure(i, weight=1, uniform="servicios_group")

        # **PRIMERA FILA: ÁREA Y DISTRITO**
        # Área
        tk.Label(servicios_content, text="Área:", 
                font=('Segoe UI', 8, 'bold'),
                fg=self.COLORS['text_dark'],
                bg=self.COLORS['light']).grid(row=0, column=0, padx=5, pady=3, sticky="w")

        areas = [a['nombre'] for a in obtener_areas() or []]
        self.area_var = tk.StringVar()
        self.area_cb = AutocompleteCombobox(servicios_content, 
                                        textvariable=self.area_var, 
                                        completevalues=areas, 
                                        state="normal",
                                        font=('Segoe UI', 8))
        self.area_cb.grid(row=1, column=0, padx=5, pady=3, sticky="ew")

        # Distrito
        tk.Label(servicios_content, text="Distrito:", 
                font=('Segoe UI', 8, 'bold'),
                fg=self.COLORS['text_dark'],
                bg=self.COLORS['light']).grid(row=0, column=1, padx=5, pady=3, sticky="w")

        self.distrito_var = tk.StringVar()
        distritos = [d['nombre'] for d in obtener_distritos() or []]
        self.distrito_cb = AutocompleteCombobox(servicios_content, 
                                            textvariable=self.distrito_var, 
                                            completevalues=distritos, 
                                            state="normal",
                                            font=('Segoe UI', 8))
        self.distrito_cb.grid(row=1, column=1, padx=5, pady=3, sticky="ew")

        # **SEGUNDA FILA: TIPO DE SERVICIO Y SERVICIO**
        # Tipo de Servicio
        tk.Label(servicios_content, text="Tipo de Servicio:", 
                font=('Segoe UI', 8, 'bold'),
                fg=self.COLORS['text_dark'],
                bg=self.COLORS['light']).grid(row=0, column=2, padx=5, pady=3, sticky="w")

        self.tipo_servicio_var = tk.StringVar()
        self.tipo_servicio_cb = AutocompleteCombobox(servicios_content, 
                                                    textvariable=self.tipo_servicio_var, 
                                                    completevalues=[], 
                                                    state="normal",
                                                    font=('Segoe UI', 8))
        self.tipo_servicio_cb.grid(row=1, column=2, padx=5, pady=3, sticky="ew")

        # Servicio
        tk.Label(servicios_content, text="Servicio:", 
                font=('Segoe UI', 8, 'bold'),
                fg=self.COLORS['text_dark'],
                bg=self.COLORS['light']).grid(row=0, column=3, padx=5, pady=3, sticky="w")

        self.servicio_var = tk.StringVar()
        self.servicio_cb = AutocompleteCombobox(servicios_content, 
                                            textvariable=self.servicio_var, 
                                            completevalues=[], 
                                            state="normal",
                                            font=('Segoe UI', 8))
        self.servicio_cb.grid(row=1, column=3, padx=5, pady=3, sticky="ew")
        
        # Inicializar distritos vacíos
        self.distrito_cb.config(completevalues=[])
        self.distrito_var.set('')

        # **FRAME INSUMOS MEJORADO - COMPACTO**
        insumos_container = tk.Frame(self.scrollable_frame, bg=self.COLORS['light'])
        insumos_container.pack(fill="x", padx=15, pady=2)  # Cambio: de pady=3 a pady=2

        self.frame_insumos = tk.Frame(insumos_container,
            bg=self.COLORS['light'],
            relief='solid',
            borderwidth=1)
        self.frame_insumos.pack(fill="x", padx=8, pady=2)  # Cambio: de pady=3 a pady=2

        # Header del frame - MÁS COMPACTO
        insumos_header = tk.Frame(self.frame_insumos, bg=self.COLORS['primary'], height=18)  # Cambio: de 20 a 18
        insumos_header.pack(fill='x')
        insumos_header.pack_propagate(False)

        tk.Label(insumos_header,
            text="💊 Gestión de Insumos",
            font=('Segoe UI', 8, 'bold'),  # Cambio: de 8 a 7
            fg=self.COLORS['white'],
            bg=self.COLORS['primary']).pack(side='left', padx=12, pady=1)  # Cambio: de pady=2 a pady=1

        # Contenido del frame - MÁS COMPACTO
        insumos_content = tk.Frame(self.frame_insumos, bg=self.COLORS['light'])
        insumos_content.pack(fill='x', padx=15, pady=4)  # Cambio: de pady=6 a pady=4

        # Configurar grid para 6 columnas simétricas
        for i in range(6):
            insumos_content.columnconfigure(i, weight=1, uniform="insumos_group")

        # **PRIMERA FILA: TIPO INSUMO, INSUMO, PRESENTACIÓN (cada uno ocupa 2 columnas)**
        # Tipo de Insumo (columna 0-1)
        tk.Label(insumos_content, text="Tipo de Insumo:",
            font=('Segoe UI', 8, 'bold'),  # Cambio: de 9 a 8
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['light']).grid(row=0, column=0, padx=5, pady=2, sticky="w")  # Cambio: de pady=3 a pady=2

        tipos_insumo = [ti['descripcion'] for ti in obtener_tipos_insumo() or []]
        self.tipo_insumo_cb = AutocompleteCombobox(insumos_content,
            textvariable=self.tipo_insumo_var,
            completevalues=tipos_insumo,
            state="normal",
            font=('Segoe UI', 8))  # Cambio: de 9 a 8
        self.tipo_insumo_cb.grid(row=1, column=0, columnspan=2, padx=5, pady=2, sticky="ew")  # Cambio: de pady=3 a pady=2

        # Insumo (columna 2-3)
        tk.Label(insumos_content, text="Insumo:",
            font=('Segoe UI', 8, 'bold'),  # Cambio: de 9 a 8
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['light']).grid(row=0, column=2, padx=5, pady=2, sticky="w")  # Cambio: de pady=3 a pady=2

        self.insumo_cb = AutocompleteCombobox(insumos_content,
            textvariable=self.insumo_var,
            completevalues=[],
            state="normal",
            font=('Segoe UI', 8))  # Cambio: de 9 a 8
        self.insumo_cb.grid(row=1, column=2, columnspan=2, padx=5, pady=2, sticky="ew")  # Cambio: de pady=3 a pady=2

        # Presentación (columna 4-5)
        tk.Label(insumos_content, text="Presentación:",
            font=('Segoe UI', 8, 'bold'),  # Cambio: de 9 a 8
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['light']).grid(row=0, column=4, padx=5, pady=2, sticky="w")  # Cambio: de pady=3 a pady=2

        self.presentacion_cb = AutocompleteCombobox(insumos_content,
            textvariable=self.presentacion_var,
            completevalues=[],
            state="normal",
            font=('Segoe UI', 8))  # Cambio: de 9 a 8
        self.presentacion_cb.grid(row=1, column=4, columnspan=2, padx=5, pady=2, sticky="ew")  # Cambio: de pady=3 a pady=2

        # **SEGUNDA FILA: LOTE Y FECHA DE VENCIMIENTO - CAMBIAR row=2 (era row=3 y row=4)**
        # Lote (columna 0-2)
        tk.Label(insumos_content, text="Lote:",
            font=('Segoe UI', 8, 'bold'),  # Cambio: de 9 a 8
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['light']).grid(row=2, column=0, padx=5, pady=2, sticky="w")  # Cambio: row=2 y pady=2

        # Frame para lote y checkbox
        frame_lote = tk.Frame(insumos_content, bg=self.COLORS['light'])
        frame_lote.grid(row=3, column=0, columnspan=3, padx=5, pady=2, sticky="ew")  # Cambio: row=3 y pady=2
        frame_lote.columnconfigure(0, weight=1)

        self.lote_entry = ttk.Entry(frame_lote, 
            textvariable=self.lote_var,
            font=('Segoe UI', 8))  # Cambio: de 9 a 8
        self.lote_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        # Checkbox Sin lote
        self.sin_lote_var = tk.BooleanVar()
        self.check_sin_lote = tk.Checkbutton(frame_lote,
            text="Sin lote",
            variable=self.sin_lote_var,
            command=lambda: self.lote_entry.config(state='disabled' if self.sin_lote_var.get() else 'normal'),
            font=('Segoe UI', 8),  # Cambio: de 9 a 8
            bg=self.COLORS['light'],
            fg=self.COLORS['text_dark'],
            selectcolor=self.COLORS['white'],
            activebackground=self.COLORS['white'])
        self.check_sin_lote.grid(row=0, column=1, sticky="w")

        # Fecha de Vencimiento (columna 3-5)
        tk.Label(insumos_content, text="Fecha Vencimiento:",
            font=('Segoe UI', 8, 'bold'),  # Cambio: de 9 a 8
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['light']).grid(row=2, column=3, padx=5, pady=2, sticky="w")  # Cambio: row=2 y pady=2

        # Frame para fecha y checkbox
        frame_fecha = tk.Frame(insumos_content, bg=self.COLORS['light'])
        frame_fecha.grid(row=3, column=3, columnspan=3, padx=5, pady=2, sticky="ew")  # Cambio: row=3 y pady=2
        frame_fecha.columnconfigure(0, weight=1)

        self.fecha_venc = DateEntry(frame_fecha, 
            width=12, 
            background='darkblue',
            foreground='white', 
            borderwidth=2, 
            date_pattern='dd/mm/yyyy',
            font=('Segoe UI', 8))  # Cambio: de 9 a 8
        self.fecha_venc.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        # Checkbox Sin fecha de vencimiento
        self.sin_fecha_venc = tk.BooleanVar(value=False)
        self.check_sin_fecha = tk.Checkbutton(frame_fecha,
            text="Sin fecha",
            variable=self.sin_fecha_venc,
            command=self.toggle_fecha_vencimiento,
            font=('Segoe UI', 8),  # Cambio: de 9 a 8
            bg=self.COLORS['light'],
            fg=self.COLORS['text_dark'],
            selectcolor=self.COLORS['white'],
            activebackground=self.COLORS['white'])
        self.check_sin_fecha.grid(row=0, column=1, sticky="w")
        
        # **FRAME REGISTRO DE MOVIMIENTO MEJORADO**
        registro_container = tk.Frame(self.scrollable_frame, bg=self.COLORS['light'])
        registro_container.pack(fill="x", padx=15, pady=3)

        self.frame_registro = tk.Frame(registro_container,
            bg=self.COLORS['light'],
            relief='solid',
            borderwidth=1)
        self.frame_registro.pack(fill="x", padx=8, pady=3)

        # Header del frame
        registro_header = tk.Frame(self.frame_registro, bg=self.COLORS['primary'], height=20)
        registro_header.pack(fill='x')
        registro_header.pack_propagate(False)

        tk.Label(registro_header,
            text="📋 Registro de Movimiento",
            font=('Segoe UI', 8, 'bold'),
            fg=self.COLORS['light'],
            bg=self.COLORS['primary']).pack(side='left', padx=12, pady=2)

        # Contenido del frame - DISTRIBUCIÓN SIMÉTRICA
        registro_content = tk.Frame(self.frame_registro, bg=self.COLORS['light'])
        registro_content.pack(fill='x', padx=15, pady=6)

        # Configurar grid para 5 columnas simétricas
        for i in range(5):
            registro_content.columnconfigure(i, weight=1, uniform="registro_group")

        # **PRIMERA FILA: 5 ELEMENTOS**
        # Fecha de Registro
        tk.Label(registro_content, text="Fecha de Registro:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['light']).grid(row=0, column=0, padx=5, pady=3, sticky="w")

        self.fecha_reg = DateEntry(registro_content, 
            width=18, 
            background='darkblue',
            foreground='white', 
            borderwidth=2, 
            date_pattern='dd/mm/yyyy',
            font=('Segoe UI', 9))
        self.fecha_reg.grid(row=1, column=0, padx=5, pady=3, sticky="ew")

        # Referencia
        tk.Label(registro_content, text="Referencia:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['light']).grid(row=0, column=1, padx=5, pady=3, sticky="w")

        self.referencia_entry = ttk.Entry(registro_content, 
            font=('Segoe UI', 9))
        self.referencia_entry.grid(row=1, column=1, padx=5, pady=3, sticky="ew")

        # Tipo de Movimiento
        tk.Label(registro_content, text="Tipo de Movimiento:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['light']).grid(row=0, column=2, padx=5, pady=3, sticky="w")

        tipos_movimiento = [tm['descripcion'] for tm in obtener_tipos_movimiento() or []]
        self.tipo_mov_cb = AutocompleteCombobox(registro_content,
            textvariable=self.tipo_movimiento_var,
            completevalues=tipos_movimiento,
            state="normal",
            font=('Segoe UI', 9))
        self.tipo_mov_cb.grid(row=1, column=2, padx=5, pady=3, sticky="ew")

        # Cantidad
        tk.Label(registro_content, text="Cantidad:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['light']).grid(row=0, column=3, padx=5, pady=3, sticky="w")

        self.cantidad_entry = ttk.Entry(registro_content, 
            font=('Segoe UI', 9))
        self.cantidad_entry.grid(row=1, column=3, padx=5, pady=3, sticky="ew")

        # Observaciones
        tk.Label(registro_content, text="Observaciones:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['light']).grid(row=0, column=4, padx=5, pady=3, sticky="w")

        self.observaciones_entry = ttk.Entry(registro_content, 
            font=('Segoe UI', 9))
        self.observaciones_entry.grid(row=1, column=4, padx=5, pady=3, sticky="ew")
        
        # **FRAME SALIDA NIVEL INFERIOR MEJORADO**
        salida_container = tk.Frame(self.scrollable_frame, bg=self.COLORS['light'])
        
        self.frame_salida_nivel_inferior = tk.Frame(salida_container,
            bg=self.COLORS['light'],
            relief='solid',
            borderwidth=1)

        # Header del frame
        salida_header = tk.Frame(self.frame_salida_nivel_inferior, bg=self.COLORS['primary'], height=22)
        salida_header.pack(fill='x')
        salida_header.pack_propagate(False)

        tk.Label(salida_header,
            text="🔄 Salida a Nivel Inferior",
            font=('Segoe UI', 8, 'bold'),
            fg=self.COLORS['light'],
            bg=self.COLORS['primary']).pack(side='left', padx=10, pady=4)

        # Contenido del frame - DISTRIBUCIÓN SIMÉTRICA
        salida_content = tk.Frame(self.frame_salida_nivel_inferior, bg=self.COLORS['light'])
        salida_content.pack(fill='x', padx=12, pady=6)

        # Configurar grid para 3 columnas simétricas
        for i in range(3):
            salida_content.columnconfigure(i, weight=1, uniform="salida_group")

        # Distrito
        tk.Label(salida_content, text="Distrito:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['light']).grid(row=0, column=0, padx=5, pady=3, sticky="w")

        distritos = [d['nombre'] for d in obtener_distritos() or []]
        self.salida_distrito_cb = AutocompleteCombobox(salida_content,
            textvariable=self.salida_distrito_var,
            completevalues=distritos,
            state="disabled",
            font=('Segoe UI', 9))
        self.salida_distrito_cb.grid(row=1, column=0, padx=5, pady=3, sticky="ew")

        # Tipo de Servicio
        tk.Label(salida_content, text="Tipo de Servicio:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['light']).grid(row=0, column=1, padx=5, pady=3, sticky="w")

        self.salida_tipo_servicio_cb = AutocompleteCombobox(salida_content,
            textvariable=self.salida_tipo_servicio_var,
            completevalues=[],
            state="disabled",
            font=('Segoe UI', 9))
        self.salida_tipo_servicio_cb.grid(row=1, column=1, padx=5, pady=3, sticky="ew")

        # Servicio
        tk.Label(salida_content, text="Servicio:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['light']).grid(row=0, column=2, padx=5, pady=3, sticky="w")

        self.salida_servicio_cb = AutocompleteCombobox(salida_content,
            textvariable=self.salida_servicio_var,
            completevalues=[],
            state="disabled",
            font=('Segoe UI', 9))
        self.salida_servicio_cb.grid(row=1, column=2, padx=5, pady=3, sticky="ew")

        # Inicializar combobox vacíos
        self.salida_tipo_servicio_cb.config(completevalues=[])
        self.salida_tipo_servicio_var.set('')
        self.salida_servicio_cb.config(completevalues=[])
        self.salida_servicio_var.set('')

        # Guardar referencia del contenedor para poder mostrarlo/ocultarlo
        self.salida_container = salida_container
        
        # **BOTÓN AGREGAR MOVIMIENTO MEJORADO - PADDING REDUCIDO**
        btn_container = tk.Frame(self.scrollable_frame, bg=self.COLORS['light'])
        btn_container.pack(fill="x", padx=20, pady=1)  # CAMBIO: de pady=5 a pady=1

        btn_inner = tk.Frame(btn_container, bg=self.COLORS['light'])
        btn_inner.pack(padx=10, pady=2)  # CAMBIO: de pady=5 a pady=2

        self.btn_agregar = tk.Button(btn_inner,
            text="Agregar Movimiento",
            image=self.icon_agregar,
            compound='left',
            command=self.agregar_movimiento,
            font=('Segoe UI', 9, 'bold'),
            bg=self.COLORS['light'],         
            fg=self.COLORS['text_dark'],      
            relief='flat',                    
            borderwidth=0,                    
            highlightthickness=0,             
            padx=25,
            pady=8,
            cursor='hand2')
        self.btn_agregar.pack()

        # **FRAME MOVIMIENTOS MEJORADO - TAMAÑO REDUCIDO**
        movimientos_container = tk.Frame(self.scrollable_frame, bg=self.COLORS['light'])
        movimientos_container.pack(fill="x", padx=15, pady=1)  # CAMBIO: fill="x" en lugar de "both", expand=False

        self.frame_movimientos = tk.Frame(movimientos_container,
            bg=self.COLORS['light'],
            relief='solid',
            borderwidth=1,
            height=120)  # CAMBIO: altura fija reducida
        self.frame_movimientos.pack(fill="x", padx=8, pady=2)  # CAMBIO: fill="x" y pady reducido

        # Header del frame - MÁS COMPACTO
        movimientos_header = tk.Frame(self.frame_movimientos, bg=self.COLORS['primary'], height=22)  # CAMBIO: altura reducida
        movimientos_header.pack(fill='x')
        movimientos_header.pack_propagate(False)

        tk.Label(movimientos_header,
            text="📊 Listado de Movimientos",  # CAMBIO: texto más corto
            font=('Segoe UI', 8, 'bold'),  # CAMBIO: fuente más pequeña
            fg=self.COLORS['white'],
            bg=self.COLORS['primary']).pack(side='left', padx=10, pady=2)  # CAMBIO: padding reducido

        # Contenido del treeview - MÁS COMPACTO
        tree_content = tk.Frame(self.frame_movimientos, bg=self.COLORS['light'])
        tree_content.pack(fill="both", expand=True, padx=8, pady=4)  # CAMBIO: padding ligeramente mayor

        columns = (
            'fecha_registro', 'referencia', 'tipo_movimiento', 'insumo', 'presentacion', 'servicio',
            'lote', 'fecha_vencimiento', 'cantidad', 'salida_distrito', 'salida_servicio',
            'observaciones', 'tipo_insumo', 'area', 'distrito', 'tipo_servicio'
        )

        # Estilo para el Treeview - CORREGIDO
        style = ttk.Style()

        style.theme_use('clam')

        # Configurar estilo del Treeview
        style.configure("Custom.Treeview",
            background=self.COLORS['white'],
            foreground=self.COLORS['text_dark'],
            rowheight=20,
            fieldbackground=self.COLORS['white'],
            font=('Segoe UI', 9),
            borderwidth=1,
            relief='solid')

        # **CONFIGURAR HEADERS CON COLORES CONTRASTANTES**
        style.configure("Custom.Treeview.Heading",
            background='#2c3e50',  # ← Color fijo que funciona
            foreground='#ffffff',    # ← Color fijo que funciona
            font=('Segoe UI', 8, 'bold'),
            relief='raised',
            borderwidth=1,
            padding=(3, 8, 3, 8),
            anchor= 'center',
            justify= 'center')

        # Mapeos para interactividad
        style.map("Custom.Treeview.Heading",
            background=[('active', '##34495e')],
            foreground=[('active', '#ffffff')])

        style.map("Custom.Treeview",
            background=[('selected', self.COLORS['text_light'])],
            foreground=[('selected', 'white')])

        # **CONFIGURAR GRID PARA POSICIONAMIENTO CORRECTO DE SCROLLBARS**
        tree_content.grid_rowconfigure(0, weight=1)
        tree_content.grid_columnconfigure(0, weight=1)

        # **CREAR TREEVIEW**
        self.tree = ttk.Treeview(tree_content,
            columns=columns,
            show='headings',
            height=5,
            style="Custom.Treeview")
        
        # **CONFIGURACIÓN MEJORADA DE COLUMNAS DEL TREEVIEW**
        # Configurar headers y columnas con anchos específicos
        encabezados = {
            'fecha_registro': 'FECHA REGISTRO',
            'referencia': 'REFERENCIA',
            'tipo_movimiento': 'TIPO MOVIMIENTO',
            'insumo': 'INSUMO',
            'presentacion': 'PRESENTACION',
            'servicio': 'SERVICIO',
            'lote': 'LOTE',
            'fecha_vencimiento': 'VENCIMIENTO',
            'cantidad': 'CANTIDAD',
            'salida_distrito': 'SALIDA DISTRITO',
            'salida_servicio': 'SALIDA SERVICIO',
            'observaciones': 'OBSERVACIONES',
            'tipo_insumo': 'TIPO INSUMO',
            'area': 'AREA',
            'distrito': 'DISTRITO',
            'tipo_servicio': 'TIPO SERVICIO'
        }

        # Anchos específicos para cada columna
        anchos_columnas = {
            'fecha_registro': 140,
            'referencia': 120,
            'tipo_movimiento': 150,
            'insumo': 200,
            'presentacion': 130,
            'servicio': 180,
            'lote': 100,
            'fecha_vencimiento': 140,
            'cantidad': 100,
            'salida_distrito': 150,
            'salida_servicio': 150,
            'observaciones': 250,
            'tipo_insumo': 130,
            'area': 120,
            'distrito': 120,
            'tipo_servicio': 150
        }

        # Justificación del texto por columna
        justificacion = {
            'fecha_registro': 'center',
            'referencia': 'center',
            'tipo_movimiento': 'center',
            'insumo': 'w',
            'presentacion': 'center',
            'servicio': 'w',
            'lote': 'center',
            'fecha_vencimiento': 'center',
            'cantidad': 'center',
            'salida_distrito': 'w',
            'salida_servicio': 'w',
            'observaciones': 'w',
            'tipo_insumo': 'center',
            'area': 'w',
            'distrito': 'w',
            'tipo_servicio': 'center'
        }

        for col in columns:
            self.tree.heading(col, text=encabezados[col], anchor='center')
            self.tree.column(col,
                            width=anchos_columnas[col],
                            minwidth=80,
                            anchor=justificacion[col])

        # **POSICIONAR TREEVIEW Y SCROLLBARS CON GRID**
        self.tree.grid(row=0, column=0, sticky="nsew")

        # Scrollbar vertical a la derecha (fila 0, columna 1)
        scrollbar_y = ttk.Scrollbar(tree_content, orient="vertical", command=self.tree.yview)
        scrollbar_y.grid(row=0, column=1, sticky="ns")

        # Scrollbar horizontal debajo (fila 1, columna 0)
        scrollbar_x = ttk.Scrollbar(tree_content, orient="horizontal", command=self.tree.xview)
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        # **CONFIGURAR SCROLLBARS EN EL TREEVIEW**
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # **SCROLL CON MOUSE WHEEL PARA EL TREEVIEW**
        def on_treeview_mousewheel(event):
            self.tree.yview_scroll(int(-1*(event.delta/120)), "units")

        def bind_treeview_mousewheel(event):
            self.tree.bind_all("<MouseWheel>", on_treeview_mousewheel)

        def unbind_treeview_mousewheel(event):
            self.tree.unbind_all("<MouseWheel>")

        self.tree.bind('<Enter>', bind_treeview_mousewheel)
        self.tree.bind('<Leave>', unbind_treeview_mousewheel)

        # **FRAME BOTONES FINALES MEJORADO - ESPACIO REDUCIDO**
        botones_container = tk.Frame(self.scrollable_frame, bg=self.COLORS['light'])
        botones_container.pack(fill="x", padx=15, pady=2)  # CAMBIO: padding reducido

        self.frame_botones = tk.Frame(botones_container, bg=self.COLORS['light'])
        self.frame_botones.pack(fill="x", padx=8, pady=2)  # CAMBIO: padding reducido

        # Frame interno para centrar botones - MÁS COMPACTO
        botones_inner = tk.Frame(self.frame_botones, bg=self.COLORS['light'])
        botones_inner.pack(expand=True, pady=3)  # CAMBIO: padding muy reducido

        # Botón Editar
        self.btn_editar = tk.Button(botones_inner,
            text="Editar",
            image=self.icon_editar,
            compound='left',
            command=self.editar_movimiento,
            font=('Segoe UI', 9, 'bold'),
            bg=self.COLORS['light'],          
            fg=self.COLORS['text_dark'],      
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            padx=10,
            pady=3,
            cursor='hand2')
        self.btn_editar.pack(side="left", padx=10)

        # Botón Eliminar
        self.btn_eliminar = tk.Button(botones_inner,
            text="Eliminar",
            image=self.icon_eliminar,
            compound='left',
            command=self.eliminar_movimiento,
            font=('Segoe UI', 9, 'bold'),
            bg=self.COLORS['light'],
            fg=self.COLORS['text_dark'],
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            padx=10,
            pady=3,
            cursor='hand2')
        self.btn_eliminar.pack(side="left", padx=10)

        # Botón Guardar
        self.btn_guardar = tk.Button(botones_inner,
            text="Guardar",
            image=self.icon_guardar,
            compound='left',
            command=self.guardar_movimientos,
            font=('Segoe UI', 9, 'bold'),
            bg=self.COLORS['light'],
            fg=self.COLORS['text_dark'],
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            padx=10,
            pady=3,
            cursor='hand2')
        self.btn_guardar.pack(side="left", padx=10)

        # Botón Cerrar
        self.btn_cerrar = tk.Button(botones_inner,
            text="Cerrar",
            image=self.icon_cerrar,
            compound='left',
            command=self.cerrar_ventana,
            font=('Segoe UI', 9, 'bold'),
            bg=self.COLORS['light'],
            fg=self.COLORS['text_dark'],
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            padx=10,
            pady=3,
            cursor='hand2')
        self.btn_cerrar.pack(side="right", padx=10)

        # Ocultar inicialmente el frame de salida nivel inferior
        self.frame_salida_nivel_inferior.pack_forget()
        
    def setup_bindings(self):
        self.area_var.trace_add('write', self.on_area_selected)
        self.distrito_var.trace_add('write', self.actualizar_tipos_servicio)
        self.tipo_servicio_var.trace_add('write', self.actualizar_servicios)
        self.tipo_insumo_var.trace_add('write', self.actualizar_insumos)
        self.insumo_var.trace_add('write', self.actualizar_presentacion)
    
        # Bind para tipo de movimiento para actualizar estado del frame salida nivel inferior
        self.tipo_movimiento_var.trace_add('write', lambda *args: self.actualizar_estado_salida_nivel_inferior())
      
        # También bind para radio buttons nivel de bodega
        self.nivel_bodega_var.trace_add('write', lambda *args: self.actualizar_estado_salida_nivel_inferior())
        
        # Bind para salida distrito para actualizar tipos servicio en salida nivel inferior
        self.salida_distrito_var.trace_add('write', self.actualizar_tipos_servicio_salida)

        # Bind para salida tipo servicio para actualizar servicios en salida nivel inferior
        self.salida_tipo_servicio_var.trace_add('write', self.actualizar_servicios_salida)
    
    # 2. Métodos de actualización de estado
    
    def actualizar_estado_comboboxes(self):
        nivel = self.nivel_bodega_var.get()
        if nivel == "area":
            self.area_cb.config(state="normal")
            self.distrito_cb.config(state="disabled")
            self.tipo_servicio_cb.config(state="disabled")
            self.servicio_cb.config(state="disabled")
        elif nivel == "distrito":
            self.area_cb.config(state="normal")
            self.distrito_cb.config(state="normal")
            self.tipo_servicio_cb.config(state="disabled")
            self.servicio_cb.config(state="disabled")
        elif nivel == "servicio":
            self.area_cb.config(state="normal")
            self.distrito_cb.config(state="normal")
            self.tipo_servicio_cb.config(state="normal")
            self.servicio_cb.config(state="normal")

        # Actualizar tipos de movimiento filtrados según nivel
        self.actualizar_tipos_movimiento_filtrados()

        # Ajustar tamaño de ventana si el frame salida nivel inferior está visible
        if self.frame_salida_nivel_inferior.winfo_ismapped():
            self.ajustar_tamano_ventana(mostrar_salida=True)
        else:
            self.ajustar_tamano_ventana(mostrar_salida=False)

        # Si el nivel es "distrito", llenar el combobox de distrito en "Salida Nivel Inferior" al inicio
        if nivel == "distrito" and self.tipo_movimiento_var.get().strip().upper() == "SALIDA NIVEL INFERIOR":
            self.salida_distrito_var.set(self.distrito_var.get())
            self.actualizar_tipos_servicio_salida()

    def actualizar_estado_salida_nivel_inferior(self):
        tipo_mov = self.tipo_movimiento_var.get().strip().upper()
        nivel = self.nivel_bodega_var.get()

        if tipo_mov == "SALIDA NIVEL INFERIOR":
            # **MOSTRAR EL FRAME DE SALIDA NIVEL INFERIOR**
            if not self.salida_container.winfo_ismapped():
                # Buscar el contenedor del botón agregar de manera más simple
                btn_container = None
                for child in self.scrollable_frame.winfo_children():
                    # Buscar por el tipo de widget y contenido
                    if isinstance(child, tk.Frame):
                        for subchild in child.winfo_children():
                            if isinstance(subchild, tk.Frame):
                                for widget in subchild.winfo_children():
                                    if isinstance(widget, tk.Button):
                                        try:
                                            # Verificar si es el botón correcto usando el texto
                                            if hasattr(widget, 'cget') and 'Agregar Movimiento' in str(widget.cget('text')):
                                                btn_container = child
                                                break
                                        except tk.TclError:
                                            # Si hay error al obtener el texto, continuar
                                            continue
                                if btn_container:
                                    break
                        if btn_container:
                            break
                
                # Empaquetar con el mismo padding que otros frames
                if btn_container:
                    self.salida_container.pack(fill="x", padx=15, pady=5, before=btn_container)
                else:
                    # Si no encuentra el botón, simplemente agregar al final
                    self.salida_container.pack(fill="x", padx=15, pady=5)

            # Mostrar el frame dentro del contenedor
            if not self.frame_salida_nivel_inferior.winfo_ismapped():
                self.frame_salida_nivel_inferior.pack(fill="x", padx=8, pady=5)

            # Configurar estados según nivel
            if nivel == "area":
                self.salida_distrito_cb.config(state="normal")
                self.salida_tipo_servicio_cb.config(state="disabled")
                self.salida_servicio_cb.config(state="disabled")
            elif nivel == "distrito":
                self.salida_distrito_var.set(self.distrito_var.get())
                self.salida_distrito_cb.config(state="disabled")
                self.salida_tipo_servicio_cb.config(state="normal")
                self.salida_servicio_cb.config(state="normal")
                self.actualizar_tipos_servicio_salida()
            else:
                self.salida_distrito_cb.config(state="disabled")
                self.salida_tipo_servicio_cb.config(state="disabled")
                self.salida_servicio_cb.config(state="disabled")
                
            # **ACTUALIZAR LAYOUT DESPUÉS DE MOSTRAR**
            self.parent.after_idle(self.update_layout)
        else:
            # **OCULTAR EL FRAME**
            if self.salida_container.winfo_ismapped():
                self.salida_container.pack_forget()
            
            # Limpiar valores
            self.salida_distrito_var.set('')
            self.salida_tipo_servicio_var.set('')
            self.salida_servicio_var.set('')
            
            # **ACTUALIZAR LAYOUT DESPUÉS DE OCULTAR**
            self.parent.after_idle(self.update_layout)
        
        # LÍNEA AGREGADA: Actualizar altura del treeview según el tipo de movimiento
        self.actualizar_altura_treeview()
         
    def actualizar_altura_treeview(self):
        """Actualiza la altura del treeview según el tipo de movimiento"""
        tipo_mov = self.tipo_movimiento_var.get().strip().upper()
        
        if tipo_mov == "SALIDA NIVEL INFERIOR":
            # Cambiar a 2 filas cuando es salida nivel inferior
            altura_filas = 2
            self.tree.configure(height=altura_filas)
            # Calcular altura total del frame: header + (filas * altura_fila) + scrollbars + padding
            altura_total = 22 + (altura_filas * 25) + 40 + 20  # ~132px
        else:
            # Mantener 5 filas para otros tipos de movimiento
            altura_filas = 5
            self.tree.configure(height=altura_filas)
            # Calcular altura total del frame: header + (filas * altura_fila) + scrollbars + padding
            altura_total = 22 + (altura_filas * 25) + 40 + 20  # ~207px
        
        # Configurar altura del frame contenedor
        self.frame_movimientos.configure(height=altura_total)
        self.frame_movimientos.pack_propagate(False)  # Mantener altura fija calculada
            
    def actualizar_tipos_movimiento_filtrados(self):
        nivel = self.nivel_bodega_var.get()
        tipos_movimiento = [tm['descripcion'] for tm in obtener_tipos_movimiento() or []]

        if nivel in ("area", "distrito"):
            # Excluir "ENTREGADO" y "NO ENTREGADO"
            tipos_movimiento = [tm for tm in tipos_movimiento if tm not in ("ENTREGADO", "NO ENTREGADO")]
        elif nivel == "servicio":
            # Excluir "SALIDA NIVEL INFERIOR"
            tipos_movimiento = [tm for tm in tipos_movimiento if tm != "SALIDA NIVEL INFERIOR"]

        self.tipo_mov_cb.config(completevalues=tipos_movimiento)

        # Limpiar selección si el valor actual no está en la lista filtrada
        if self.tipo_movimiento_var.get() not in tipos_movimiento:
            self.tipo_movimiento_var.set('')
        
    # 3. Métodos de actualización de datos
    
    def actualizar_tipos_servicio(self, *args):
        distrito_nombre = self.distrito_var.get()
        distritos = obtener_distritos() or []
        distrito_id = next((d['id'] for d in distritos if d['nombre'] == distrito_nombre), None)

        if distrito_id:
            tipos_servicio = obtener_tipos_servicio_por_distrito(distrito_id) or []
            opciones = [ts['descripcion'] for ts in tipos_servicio]
            self.tipo_servicio_cb.config(completevalues=opciones)
            self.tipo_servicio_var.set('')
            self.servicio_var.set('')
        else:
            self.tipo_servicio_cb.config(completevalues=[])
            self.tipo_servicio_var.set('')
            self.servicio_cb.config(completevalues=[])
            self.servicio_var.set('')
            
    def actualizar_servicios(self, *args):
        distrito_nombre = self.distrito_var.get()
        tipo_servicio_desc = self.tipo_servicio_var.get()
        distritos = obtener_distritos() or []
        distrito_id = next((d['id'] for d in distritos if d['nombre'] == distrito_nombre), None)

        if distrito_id:
            tipos_servicio = obtener_tipos_servicio_por_distrito(distrito_id) or []
            tipo_servicio_id = next((ts['id'] for ts in tipos_servicio if ts['descripcion'] == tipo_servicio_desc), None)
            if tipo_servicio_id:
                servicios = obtener_servicios_por_tipo(tipo_servicio_id) or []
                opciones = [s['nombre'] for s in servicios]
                self.servicio_cb.config(completevalues=opciones)
                self.servicio_var.set('')
                return
        self.servicio_cb.config(completevalues=[])
        self.servicio_var.set('')
    
    def actualizar_insumos(self, *args):
        tipo_insumo_desc = self.tipo_insumo_var.get()
        tipos_insumo = obtener_tipos_insumo() or []
        tipo_insumo_id = next((ti['id'] for ti in tipos_insumo if ti['descripcion'] == tipo_insumo_desc), None)

        if tipo_insumo_id:
            insumos = obtener_insumos_por_tipo(tipo_insumo_id) or []
            opciones = [i['nombre'] for i in insumos]
            self.insumo_cb.config(completevalues=opciones)
            self.insumo_var.set('')
        else:
            self.insumo_cb.config(completevalues=[])
            self.insumo_var.set('')

    def actualizar_presentacion(self, *args):
        tipo_insumo_desc = self.tipo_insumo_var.get()
        insumo_nombre = self.insumo_var.get()
        tipos_insumo = obtener_tipos_insumo() or []
        tipo_insumo_id = next((ti['id'] for ti in tipos_insumo if ti['descripcion'] == tipo_insumo_desc), None)

        if tipo_insumo_id and insumo_nombre:
            insumos = obtener_insumos_por_tipo(tipo_insumo_id) or []
            insumo_seleccionado = next((i for i in insumos if i['nombre'] == insumo_nombre), None)
            if insumo_seleccionado and insumo_seleccionado['nombre_presentacion']:
                self.presentacion_cb.config(completevalues=[insumo_seleccionado['nombre_presentacion']])
                self.presentacion_var.set(insumo_seleccionado['nombre_presentacion'])
                return
        self.presentacion_cb.config(completevalues=[])
        self.presentacion_var.set('')
    
    def actualizar_tipos_servicio_salida(self, *args):
        distrito_nombre = self.salida_distrito_var.get()
        distritos = obtener_distritos() or []
        distrito_id = next((d['id'] for d in distritos if d['nombre'] == distrito_nombre), None)

        if distrito_id:
            tipos_servicio = obtener_tipos_servicio_por_distrito(distrito_id) or []
            opciones = [ts['descripcion'] for ts in tipos_servicio]
            self.salida_tipo_servicio_cb.config(completevalues=opciones)
            self.salida_tipo_servicio_var.set('')
            self.salida_servicio_var.set('')
        else:
            self.salida_tipo_servicio_cb.config(completevalues=[])
            self.salida_tipo_servicio_var.set('')
            self.salida_servicio_cb.config(completevalues=[])
            self.salida_servicio_var.set('')

    def actualizar_servicios_salida(self, *args):
        distrito_nombre = self.salida_distrito_var.get()
        tipo_servicio_desc = self.salida_tipo_servicio_var.get()
        distritos = obtener_distritos() or []
        distrito_id = next((d['id'] for d in distritos if d['nombre'] == distrito_nombre), None)

        if distrito_id:
            tipos_servicio = obtener_tipos_servicio_por_distrito(distrito_id) or []
            tipo_servicio_id = next((ts['id'] for ts in tipos_servicio if ts['descripcion'] == tipo_servicio_desc), None)
            if tipo_servicio_id:
                servicios = obtener_servicios_por_tipo(tipo_servicio_id) or []
                opciones = [s['nombre'] for s in servicios]
                self.salida_servicio_cb.config(completevalues=opciones)
                self.salida_servicio_var.set('')
                return
        self.salida_servicio_cb.config(completevalues=[])
        self.salida_servicio_var.set('')

    def toggle_fecha_vencimiento(self):
        if self.sin_fecha_venc.get():
            self.fecha_venc.configure(state='disabled')
        else:
            self.fecha_venc.configure(state='normal')
    
    def toggle_lote(self):
        if self.sin_lote_var.get():
            self.lote_entry.delete(0, 'end')
            self.lote_entry.config(state='disabled')
        else:
            self.lote_entry.config(state='normal')

    # 5. Métodos de gestión de movimientos 

    def agregar_movimiento(self):
        try:
            fecha_registro = self.fecha_reg.get_date().strftime('%d/%m/%Y')
            tipo_movimiento = self.tipo_movimiento_var.get()
            tipo_insumo = self.tipo_insumo_var.get()
            insumo = self.insumo_var.get()
            presentacion = self.presentacion_var.get()
            if self.sin_lote_var.get():
                lote = "N/A"
            else:
                lote = self.lote_entry.get().upper()
            if self.sin_fecha_venc.get():
                fecha_venc_str = "N/A"
            else:
                fecha_venc_str = self.fecha_venc.get_date().strftime('%d/%m/%Y')
            cantidad_str = self.cantidad_entry.get()
            referencia = self.referencia_entry.get().upper()
            observaciones = self.observaciones_entry.get().upper()

            # Obtener datos de servicios
            area = self.area_var.get()
            distrito = self.distrito_var.get()
            tipo_servicio = self.tipo_servicio_var.get()
            servicio = self.servicio_var.get()

            salida_distrito = ''
            salida_servicio = ''
            if tipo_movimiento.strip().upper() == "SALIDA NIVEL INFERIOR":
                salida_distrito = self.salida_distrito_var.get()
                salida_servicio = self.salida_servicio_var.get()

            if not tipo_insumo:
                messagebox.showerror("Error", "Debe seleccionar un tipo de insumo")
                return

            if not all([tipo_movimiento, insumo, presentacion, lote, cantidad_str, referencia]):
                messagebox.showerror("Error", "Los campos son requeridos excepto observaciones")
                return

            cantidad = float(cantidad_str)

            # Insertar en el Treeview con TODOS los datos necesarios
            self.tree.insert('', 'end', values=(
                fecha_registro,      # 0
                referencia,          # 1
                tipo_movimiento,     # 2
                insumo,             # 3
                presentacion,       # 4
                servicio,           # 5
                lote,               # 6
                fecha_venc_str,     # 7
                cantidad,           # 8
                salida_distrito,    # 9
                salida_servicio,    # 10
                observaciones,      # 11
                tipo_insumo,        # 12
                area,               # 13 - NUEVO
                distrito,           # 14 - NUEVO
                tipo_servicio       # 15 - NUEVO
            ))

            self.ajustar_ancho_columnas_automatico()
            
            self.limpiar_campos()

        except ValueError:
            messagebox.showerror("Error", "La cantidad debe ser un número válido")
        except Exception as e:
            messagebox.showerror("Error", f"Error al agregar movimiento: {str(e)}")

    def editar_movimiento(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un movimiento para editar")
            return

        valores = self.tree.item(selected_item)['values']

        editar_ventana = tk.Toplevel(self.parent)
        editar_ventana.title("Editar Movimiento")
        editar_ventana.configure(bg=self.COLORS['light'])

        # Configurar dimensiones iniciales (como main_window.py)
        ancho_ventana = 1055
        alto_ventana = 745

        # Obtener dimensiones de pantalla para centrar
        screen_width = editar_ventana.winfo_screenwidth()
        screen_height = editar_ventana.winfo_screenheight()

        x = (screen_width // 2) - (ancho_ventana // 2)
        y = (screen_height // 2) - (alto_ventana // 2)

        editar_ventana.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")
        editar_ventana.resizable(True, True)

        # **CONFIGURAR ESTILOS PARA LA VENTANA DE EDICIÓN**
        style = ttk.Style()
        style.theme_use('clam')

        # Configurar estilos para radiobuttons y checkbuttons con fondo blanco
        style.configure("Custom.TRadiobutton",
            background=self.COLORS['white'],
            foreground=self.COLORS['text_dark'],
            font=('Segoe UI', 9),
            focuscolor='none')

        style.map("Custom.TRadiobutton",
            background=[('active', self.COLORS['white'])],
            indicatorcolor=[('selected', 'white'),
                        ('!selected', 'white'),
                        ('active', 'white')])

        style.configure("Custom.TCheckbutton",
            background=self.COLORS['white'],
            foreground=self.COLORS['text_dark'],
            font=('Segoe UI', 9),
            focuscolor='none')

        style.map("Custom.TCheckbutton",
            background=[('active', self.COLORS['white'])],
            indicatorcolor=[('selected', 'white'),
                        ('!selected', 'white'),
                        ('active', 'white')])

        # Configurar estilos para frames
        style.configure("Custom.TLabelframe",
            background=self.COLORS['white'],
            borderwidth=2,
            relief='solid')

        style.configure("Custom.TLabelframe.Label",
            background=self.COLORS['white'],
            foreground=self.COLORS['text_dark'],
            font=('Segoe UI', 9, 'bold'))

        def toggle_lote_edit():
            if edit_sin_lote_var.get():
                lote_entry.delete(0, tk.END)
                lote_entry.config(state='disabled')
            else:
                lote_entry.config(state='normal')

        def toggle_fecha_venc_edit():
            if edit_sin_fecha_venc.get():
                fecha_venc_edit.configure(state='disabled')
            else:
                fecha_venc_edit.configure(state='normal')
        
        # Variables para edición
        edit_nivel_bodega_var = tk.StringVar(value="area")
        edit_area_var = tk.StringVar()
        edit_distrito_var = tk.StringVar()
        edit_tipo_servicio_var = tk.StringVar()
        edit_servicio_var = tk.StringVar()
        edit_tipo_insumo_var = tk.StringVar()
        edit_insumo_var = tk.StringVar()
        edit_presentacion_var = tk.StringVar()
        edit_tipo_movimiento_var = tk.StringVar()
        edit_salida_distrito_var = tk.StringVar()
        edit_salida_tipo_servicio_var = tk.StringVar()
        edit_salida_servicio_var = tk.StringVar()
        edit_sin_lote_var = tk.BooleanVar()
        edit_sin_fecha_venc = tk.BooleanVar()

        # CONTENEDOR PRINCIPAL CON SCROLL
        container = tk.Frame(editar_ventana)
        container.pack(fill='both', expand=True)

        main_canvas = tk.Canvas(container, bg=self.COLORS['light'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient='vertical', command=main_canvas.yview)
        scrollable_frame = tk.Frame(main_canvas, bg=self.COLORS['light'])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)

        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # HEADER PRINCIPAL
        header_frame = tk.Frame(scrollable_frame, bg=self.COLORS['primary'], height=40)
        header_frame.pack(fill="x", padx=20, pady=(20, 0))
        header_frame.pack_propagate(False)

        header_label = tk.Label(header_frame, 
            text="EDITAR MOVIMIENTO", 
            font=('Segoe UI', 16, 'bold'), 
            bg=self.COLORS['primary'], 
            fg='white')
        header_label.pack(expand=True)

        # FRAME NIVEL DE BODEGA (con estilo mejorado)
        self.frame_nivel_bodega_edit = tk.Frame(scrollable_frame, bg=self.COLORS['light'], relief='solid', borderwidth=1)
        self.frame_nivel_bodega_edit.pack(fill="x", padx=20, pady=15)

        nivel_header = tk.Frame(self.frame_nivel_bodega_edit, bg=self.COLORS['primary'], height=22)
        nivel_header.pack(fill='x')
        nivel_header.pack_propagate(False)

        tk.Label(nivel_header, 
                text="🏢 Nivel de Bodega", 
                font=('Segoe UI', 9, 'bold'),
                fg=self.COLORS['white'], 
                bg=self.COLORS['primary']).pack(side='left', padx=10, pady=4)

        nivel_content = tk.Frame(self.frame_nivel_bodega_edit, bg=self.COLORS['light'])
        nivel_content.pack(fill='x', padx=12, pady=6)

        # Radiobuttons con estilo mejorado
        rb_area = tk.Radiobutton(nivel_content, text="Área", image=self.icon_area, compound='left',
                                variable=edit_nivel_bodega_var, value="area",
                                font=('Segoe UI', 9), bg=self.COLORS['light'], fg=self.COLORS['text_dark'],
                                selectcolor=self.COLORS['white'], activebackground=self.COLORS['white'])
        rb_distrito = tk.Radiobutton(nivel_content, text="Distrito", image=self.icon_distrito, compound='left',
                                    variable=edit_nivel_bodega_var, value="distrito",
                                    font=('Segoe UI', 9), bg=self.COLORS['light'], fg=self.COLORS['text_dark'],
                                    selectcolor=self.COLORS['white'], activebackground=self.COLORS['white'])
        rb_servicio = tk.Radiobutton(nivel_content, text="Servicio", image=self.icon_servicio, compound='left',
                                    variable=edit_nivel_bodega_var, value="servicio",
                                    font=('Segoe UI', 9), bg=self.COLORS['light'], fg=self.COLORS['text_dark'],
                                    selectcolor=self.COLORS['white'], activebackground=self.COLORS['white'])

        rb_area.grid(row=0, column=0, padx=(0, 20), pady=5, sticky="w")
        rb_distrito.grid(row=0, column=1, padx=(0, 20), pady=5, sticky="w")
        rb_servicio.grid(row=0, column=2, padx=(0, 20), pady=5, sticky="w")

        # FRAME SERVICIOS (con estilo mejorado)
        self.frame_servicios_edit = tk.Frame(scrollable_frame, bg=self.COLORS['light'], relief='solid', borderwidth=1)
        self.frame_servicios_edit.pack(fill="x", padx=20, pady=15)

        servicios_header = tk.Frame(self.frame_servicios_edit, bg=self.COLORS['primary'], height=25)
        servicios_header.pack(fill='x')
        servicios_header.pack_propagate(False)

        tk.Label(servicios_header, text="🏥 Configuración de Servicios", font=('Segoe UI', 9, 'bold'),
                fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(side='left', padx=10, pady=4)

        servicios_content = tk.Frame(self.frame_servicios_edit, bg=self.COLORS['light'])
        servicios_content.pack(fill="x", padx=12, pady=6)

        for col in range(8):
            servicios_content.columnconfigure(col, weight=1)

        # Aquí agregas tus labels y comboboxes para servicios con grid, igual que antes
        tk.Label(servicios_content, text="Área:", font=('Segoe UI', 9),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=0, column=0, padx=5, pady=8, sticky="w")
        area_cb = AutocompleteCombobox(servicios_content, textvariable=edit_area_var, width=25, state="normal")
        area_cb.set_completion_list([a['nombre'] for a in obtener_areas() or []])
        area_cb.grid(row=0, column=1, padx=5, pady=8, sticky="ew")

        tk.Label(servicios_content, text="Distrito:", font=('Segoe UI', 9),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=0, column=2, padx=5, pady=8, sticky="w")
        distrito_cb = AutocompleteCombobox(servicios_content, textvariable=edit_distrito_var, width=25, state="normal")
        distrito_cb.set_completion_list([d['nombre'] for d in obtener_distritos() or []])
        distrito_cb.grid(row=0, column=3, padx=5, pady=8, sticky="ew")

        tk.Label(servicios_content, text="Tipo de Servicio:", font=('Segoe UI', 9),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=0, column=4, padx=5, pady=8, sticky="w")
        tipo_servicio_cb = AutocompleteCombobox(servicios_content, textvariable=edit_tipo_servicio_var, width=25, state="normal")
        tipo_servicio_cb.grid(row=0, column=5, padx=5, pady=8, sticky="ew")

        tk.Label(servicios_content, text="Servicio:", font=('Segoe UI', 9),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=0, column=6, padx=5, pady=8, sticky="w")
        servicio_cb = AutocompleteCombobox(servicios_content, textvariable=edit_servicio_var, width=25, state="normal")
        servicio_cb.grid(row=0, column=7, padx=5, pady=8, sticky="ew")

        # FRAME INSUMOS (con estilo mejorado)
        self.frame_insumos_edit = tk.Frame(scrollable_frame, bg=self.COLORS['light'], relief='solid', borderwidth=1)
        self.frame_insumos_edit.pack(fill="x", padx=20, pady=15)

        insumos_header = tk.Frame(self.frame_insumos_edit, bg=self.COLORS['primary'], height=25)
        insumos_header.pack(fill='x')
        insumos_header.pack_propagate(False)

        tk.Label(insumos_header, text="💊 Gestión de Insumos", font=('Segoe UI', 9, 'bold'),
                fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(side='left', padx=10, pady=4)

        insumos_content = tk.Frame(self.frame_insumos_edit, bg=self.COLORS['light'])
        insumos_content.pack(fill="x", padx=12, pady=6)

        for col in range(6):
            insumos_content.columnconfigure(col, weight=1)

        # Aquí agregas tus labels y comboboxes para insumos con grid, igual que antes
        tk.Label(insumos_content, text="Tipo de Insumo:", font=('Segoe UI', 9),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=0, column=0, padx=5, pady=8, sticky="w")
        tipo_insumo_cb = AutocompleteCombobox(insumos_content, textvariable=edit_tipo_insumo_var, width=25, state="normal")
        tipo_insumo_cb.set_completion_list([ti['descripcion'] for ti in obtener_tipos_insumo() or []])
        tipo_insumo_cb.grid(row=0, column=1, padx=5, pady=8, sticky="ew")

        tk.Label(insumos_content, text="Insumo:", font=('Segoe UI', 9),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=0, column=2, padx=5, pady=8, sticky="w")
        insumo_cb = AutocompleteCombobox(insumos_content, textvariable=edit_insumo_var, width=25, state="normal")
        insumo_cb.grid(row=0, column=3, padx=5, pady=8, sticky="ew")

        tk.Label(insumos_content, text="Presentación:", font=('Segoe UI', 9),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=0, column=4, padx=5, pady=8, sticky="w")
        presentacion_cb = AutocompleteCombobox(insumos_content, textvariable=edit_presentacion_var, width=25, state="normal")
        presentacion_cb.grid(row=0, column=5, padx=5, pady=8, sticky="ew")

        # FRAME DETALLES DEL MOVIMIENTO (con estilo mejorado)
        self.frame_detalles_edit = tk.Frame(scrollable_frame, bg=self.COLORS['light'], relief='solid', borderwidth=1)
        self.frame_detalles_edit.pack(fill="x", padx=20, pady=15)

        detalles_header = tk.Frame(self.frame_detalles_edit, bg=self.COLORS['primary'], height=25)
        detalles_header.pack(fill='x')
        detalles_header.pack_propagate(False)

        tk.Label(detalles_header, text="📋 Detalles del Movimiento", font=('Segoe UI', 9, 'bold'),
                fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(side='left', padx=10, pady=4)

        detalles_content = tk.Frame(self.frame_detalles_edit, bg=self.COLORS['light'])
        detalles_content.pack(fill="x", padx=12, pady=6)

        for col in range(6):
            detalles_content.columnconfigure(col, weight=1)

        # Aquí agregas tus widgets para detalles con grid, igual que antes
        tk.Label(detalles_content, text="Fecha de Registro:", font=('Segoe UI', 9),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=0, column=0, padx=5, pady=8, sticky="w")
        fecha_edit = DateEntry(detalles_content, width=25, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        fecha_edit.grid(row=0, column=1, padx=5, pady=8, sticky="ew")

        tk.Label(detalles_content, text="Referencia:", font=('Segoe UI', 9),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=0, column=2, padx=5, pady=8, sticky="w")
        referencia_entry = ttk.Entry(detalles_content, width=27)
        referencia_entry.grid(row=0, column=3, padx=5, pady=8, sticky="ew")

        tk.Label(detalles_content, text="Tipo Movimiento:", font=('Segoe UI', 9),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=0, column=4, padx=5, pady=8, sticky="w")
        tipo_mov_cb = AutocompleteCombobox(detalles_content, textvariable=edit_tipo_movimiento_var, width=25, state="normal")
        tipo_mov_cb.set_completion_list([tm['descripcion'] for tm in obtener_tipos_movimiento() or []])
        tipo_mov_cb.grid(row=0, column=5, padx=5, pady=8, sticky="ew")

        tk.Label(detalles_content, text="Lote:", font=('Segoe UI', 9),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=1, column=0, padx=5, pady=8, sticky="w")
        lote_frame = tk.Frame(detalles_content, bg=self.COLORS['light'])
        lote_frame.grid(row=1, column=1, padx=5, pady=8, sticky="ew")
        lote_entry = ttk.Entry(lote_frame, width=20)
        lote_entry.pack(side="left", fill="x", expand=True)
        edit_check_sin_lote = ttk.Checkbutton(lote_frame, text="Sin\nlote", variable=edit_sin_lote_var,
                                            command=toggle_lote_edit, style="Custom.TCheckbutton")
        edit_check_sin_lote.pack(side="right", padx=(5, 0))

        tk.Label(detalles_content, text="Fecha\nVencimiento:", font=('Segoe UI', 9),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=1, column=2, padx=5, pady=8, sticky="w")
        fecha_venc_frame = tk.Frame(detalles_content, bg=self.COLORS['light'])
        fecha_venc_frame.grid(row=1, column=3, padx=5, pady=8, sticky="ew")
        fecha_venc_edit = DateEntry(fecha_venc_frame, width=15, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        fecha_venc_edit.pack(side="left")
        edit_check_sin_fecha = ttk.Checkbutton(fecha_venc_frame, text="Sin fecha\nvencimiento", variable=edit_sin_fecha_venc,
                                            command=toggle_fecha_venc_edit, style="Custom.TCheckbutton")
        edit_check_sin_fecha.pack(side="right", padx=(5, 0))

        tk.Label(detalles_content, text="Cantidad:", font=('Segoe UI', 9),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=1, column=4, padx=5, pady=8, sticky="w")
        cantidad_entry = ttk.Entry(detalles_content, width=27)
        cantidad_entry.grid(row=1, column=5, padx=5, pady=8, sticky="ew")

        tk.Label(detalles_content, text="Observaciones:", font=('Segoe UI', 9),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=2, column=0, padx=5, pady=8, sticky="w")
        observaciones_entry = ttk.Entry(detalles_content, width=80)
        observaciones_entry.grid(row=2, column=1, columnspan=5, padx=5, pady=8, sticky="ew")

        # FRAME SALIDA NIVEL INFERIOR (con estilo mejorado)
        self.frame_salida_nivel_inferior_edit = tk.Frame(scrollable_frame, bg=self.COLORS['light'], relief='solid', borderwidth=1)
        self.frame_salida_nivel_inferior_edit.pack(fill="x", padx=20, pady=15)

        salida_header = tk.Frame(self.frame_salida_nivel_inferior_edit, bg=self.COLORS['primary'], height=25)
        salida_header.pack(fill='x')
        salida_header.pack_propagate(False)

        tk.Label(salida_header, text="🔄 Salida a Nivel Inferior", font=('Segoe UI', 9, 'bold'),
                fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(side='left', padx=10, pady=4)

        salida_content = tk.Frame(self.frame_salida_nivel_inferior_edit, bg=self.COLORS['light'])
        salida_content.pack(fill='x', padx=12, pady=6)

        for col in range(6):
            salida_content.columnconfigure(col, weight=1)

        tk.Label(salida_content, text="Distrito:", font=('Segoe UI', 9),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=0, column=0, padx=5, pady=8, sticky="w")
        salida_distrito_cb = AutocompleteCombobox(salida_content, textvariable=edit_salida_distrito_var, width=25,
                                                completevalues=[d['nombre'] for d in obtener_distritos() or []], state="disabled")
        salida_distrito_cb.grid(row=0, column=1, padx=5, pady=8, sticky="ew")

        tk.Label(salida_content, text="Tipo de Servicio:", font=('Segoe UI', 9),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=0, column=2, padx=5, pady=8, sticky="w")
        salida_tipo_servicio_cb = AutocompleteCombobox(salida_content, textvariable=edit_salida_tipo_servicio_var, width=25,
                                                    completevalues=[], state="disabled")
        salida_tipo_servicio_cb.grid(row=0, column=3, padx=5, pady=8, sticky="ew")

        tk.Label(salida_content, text="Servicio:", font=('Segoe UI', 9),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=0, column=4, padx=5, pady=8, sticky="w")
        salida_servicio_cb = AutocompleteCombobox(salida_content, textvariable=edit_salida_servicio_var, width=25,
                                                completevalues=[], state="disabled")
        salida_servicio_cb.grid(row=0, column=5, padx=5, pady=8, sticky="ew")

        # **FUNCIONES DE ACTUALIZACIÓN** (mantener las mismas que tenías)
        def actualizar_estado_comboboxes_edit(*args):
            nivel = edit_nivel_bodega_var.get()
            if nivel == "area":
                area_cb.config(state="normal")
                distrito_cb.config(state="disabled")
                tipo_servicio_cb.config(state="disabled")
                servicio_cb.config(state="disabled")
            elif nivel == "distrito":
                area_cb.config(state="normal")
                distrito_cb.config(state="normal")
                tipo_servicio_cb.config(state="disabled")
                servicio_cb.config(state="disabled")
            elif nivel == "servicio":
                area_cb.config(state="normal")
                distrito_cb.config(state="normal")
                tipo_servicio_cb.config(state="normal")
                servicio_cb.config(state="normal")

            actualizar_tipos_movimiento_filtrados_edit()

            if nivel == "distrito" and edit_tipo_movimiento_var.get().strip().upper() == "SALIDA NIVEL INFERIOR":
                edit_salida_distrito_var.set(edit_distrito_var.get())
                actualizar_tipos_servicio_salida_edit()
        
        def actualizar_estado_salida_nivel_inferior_edit(*args):
            tipo_mov = edit_tipo_movimiento_var.get().strip().upper()
            nivel = edit_nivel_bodega_var.get()

            if tipo_mov == "SALIDA NIVEL INFERIOR":
                if not self.frame_salida_nivel_inferior_edit.winfo_ismapped():
                    try:
                        self.frame_salida_nivel_inferior_edit.pack(fill="x", padx=20, pady=15, before=frame_botones)
                    except NameError:
                        self.frame_salida_nivel_inferior_edit.pack(fill="x", padx=20, pady=15)

                if nivel == "area":
                    salida_distrito_cb.config(state="normal")
                    salida_tipo_servicio_cb.config(state="disabled")
                    salida_servicio_cb.config(state="disabled")
                elif nivel == "distrito":
                    edit_salida_distrito_var.set(edit_distrito_var.get())
                    salida_distrito_cb.config(state="disabled")
                    salida_distrito_cb.set_completion_list([edit_distrito_var.get()])
                    salida_tipo_servicio_cb.config(state="normal")
                    salida_servicio_cb.config(state="normal")
                    actualizar_tipos_servicio_salida_edit()
                else:
                    salida_distrito_cb.config(state="disabled")
                    salida_tipo_servicio_cb.config(state="disabled")
                    salida_servicio_cb.config(state="disabled")
            else:
                self.frame_salida_nivel_inferior_edit.pack_forget()
                edit_salida_distrito_var.set('')
                edit_salida_tipo_servicio_var.set('')
                edit_salida_servicio_var.set('')

        def actualizar_tipos_movimiento_filtrados_edit():
            nivel = edit_nivel_bodega_var.get()
            tipos_movimiento = [tm['descripcion'] for tm in obtener_tipos_movimiento() or []]

            if nivel in ("area", "distrito"):
                tipos_movimiento = [tm for tm in tipos_movimiento if tm not in ("ENTREGADO", "NO ENTREGADO")]
            elif nivel == "servicio":
                tipos_movimiento = [tm for tm in tipos_movimiento if tm != "SALIDA NIVEL INFERIOR"]

            tipo_mov_cb.config(completevalues=tipos_movimiento)

            if edit_tipo_movimiento_var.get() not in tipos_movimiento:
                edit_tipo_movimiento_var.set('')
        
        def actualizar_tipos_servicio_edit(*args):
            distrito_nombre = edit_distrito_var.get()
            distritos = obtener_distritos() or []
            distrito_id = next((d['id'] for d in distritos if d['nombre'] == distrito_nombre), None)

            if distrito_id:
                tipos_servicio = obtener_tipos_servicio_por_distrito(distrito_id) or []
                opciones = [ts['descripcion'] for ts in tipos_servicio]
                tipo_servicio_cb.set_completion_list(opciones)
                if edit_tipo_servicio_var.get() not in opciones:
                    edit_tipo_servicio_var.set('')
            else:
                tipo_servicio_cb.set_completion_list([])
                edit_tipo_servicio_var.set('')
                servicio_cb.set_completion_list([])
                edit_servicio_var.set('')

        def actualizar_servicios_edit(*args):
            distrito_nombre = edit_distrito_var.get()
            tipo_servicio_desc = edit_tipo_servicio_var.get()
            distritos = obtener_distritos() or []
            distrito_id = next((d['id'] for d in distritos if d['nombre'] == distrito_nombre), None)

            if distrito_id:
                tipos_servicio = obtener_tipos_servicio_por_distrito(distrito_id) or []
                tipo_servicio_id = next((ts['id'] for ts in tipos_servicio if ts['descripcion'] == tipo_servicio_desc), None)
                if tipo_servicio_id:
                    servicios = obtener_servicios_por_tipo(tipo_servicio_id) or []
                    opciones = [s['nombre'] for s in servicios]
                    servicio_cb.set_completion_list(opciones)
                    if edit_servicio_var.get() not in opciones:
                        edit_servicio_var.set('')
            else:
                servicio_cb.set_completion_list([])
                edit_servicio_var.set('')

        def actualizar_tipos_servicio_salida_edit(*args):
            distrito_nombre = edit_salida_distrito_var.get()
            distritos = obtener_distritos() or []
            distrito_id = next((d['id'] for d in distritos if d['nombre'] == distrito_nombre), None)

            if distrito_id:
                tipos_servicio = obtener_tipos_servicio_por_distrito(distrito_id) or []
                opciones = [ts['descripcion'] for ts in tipos_servicio]
                salida_tipo_servicio_cb.set_completion_list(opciones)
                if edit_salida_tipo_servicio_var.get() not in opciones:
                    edit_salida_tipo_servicio_var.set('')
                    edit_salida_servicio_var.set('')
            else:
                salida_tipo_servicio_cb.set_completion_list([])
                edit_salida_tipo_servicio_var.set('')
                salida_servicio_cb.set_completion_list([])
                edit_salida_servicio_var.set('')

        def actualizar_servicios_salida_edit(*args):
            distrito_nombre = edit_salida_distrito_var.get()
            tipo_servicio_desc = edit_salida_tipo_servicio_var.get()
            distritos = obtener_distritos() or []
            distrito_id = next((d['id'] for d in distritos if d['nombre'] == distrito_nombre), None)

            if distrito_id:
                tipos_servicio = obtener_tipos_servicio_por_distrito(distrito_id) or []
                tipo_servicio_id = next((ts['id'] for ts in tipos_servicio if ts['descripcion'] == tipo_servicio_desc), None)
                if tipo_servicio_id:
                    servicios = obtener_servicios_por_tipo(tipo_servicio_id) or []
                    opciones = [s['nombre'] for s in servicios]
                    salida_servicio_cb.set_completion_list(opciones)
                    if edit_salida_servicio_var.get() not in opciones:
                        edit_salida_servicio_var.set('')
            else:
                salida_servicio_cb.set_completion_list([])
                edit_salida_servicio_var.set('')

        def actualizar_insumos_edit(*args):
            tipo_insumo_desc = edit_tipo_insumo_var.get()
            tipos_insumo = obtener_tipos_insumo() or []
            tipo_insumo_id = next((ti['id'] for ti in tipos_insumo if ti['descripcion'] == tipo_insumo_desc), None)

            if tipo_insumo_id:
                insumos = obtener_insumos_por_tipo(tipo_insumo_id) or []
                insumo_cb.set_completion_list([i['nombre'] for i in insumos])
                if edit_insumo_var.get() not in [i['nombre'] for i in insumos]:
                    edit_insumo_var.set('')
            else:
                insumo_cb.set_completion_list([])
                edit_insumo_var.set('')

        def actualizar_presentacion_edit(*args):
            tipo_insumo_desc = edit_tipo_insumo_var.get()
            insumo_nombre = edit_insumo_var.get()
            tipos_insumo = obtener_tipos_insumo() or []
            tipo_insumo_id = next((ti['id'] for ti in tipos_insumo if ti['descripcion'] == tipo_insumo_desc), None)

            if tipo_insumo_id and insumo_nombre:
                insumos = obtener_insumos_por_tipo(tipo_insumo_id) or []
                insumo_seleccionado = next((i for i in insumos if i['nombre'] == insumo_nombre), None)
                if insumo_seleccionado and insumo_seleccionado['nombre_presentacion']:
                    presentacion_cb.set_completion_list([insumo_seleccionado['nombre_presentacion']])
                    edit_presentacion_var.set(insumo_seleccionado['nombre_presentacion'])
                    return
            presentacion_cb.set_completion_list([])
            edit_presentacion_var.set('')
        
        def cargar_datos_iniciales():
            area_valor = valores[13] if len(valores) > 13 else ''
            distrito_valor = valores[14] if len(valores) > 14 else ''
            tipo_servicio_valor = valores[15] if len(valores) > 15 else ''
            servicio_valor = valores[5]
            
            if servicio_valor and tipo_servicio_valor and distrito_valor:
                edit_nivel_bodega_var.set("servicio")
            elif distrito_valor and not servicio_valor:
                edit_nivel_bodega_var.set("distrito")
            else:
                edit_nivel_bodega_var.set("area")

            actualizar_estado_comboboxes_edit()
            
            edit_area_var.set(area_valor)
            edit_distrito_var.set(distrito_valor)
            edit_tipo_servicio_var.set(tipo_servicio_valor)
            edit_servicio_var.set(servicio_valor)
            edit_tipo_insumo_var.set(valores[12])
            edit_insumo_var.set(valores[3])
            edit_presentacion_var.set(valores[4])
            
            fecha_edit.set_date(datetime.strptime(valores[0], '%d/%m/%Y').date())
            referencia_entry.delete(0, tk.END)
            referencia_entry.insert(0, valores[1])
            edit_tipo_movimiento_var.set(valores[2])
            
            if valores[6] == "N/A":
                edit_sin_lote_var.set(True)
                lote_entry.config(state='disabled')
            else:
                edit_sin_lote_var.set(False)
                lote_entry.config(state='normal')
            lote_entry.delete(0, 'end')
            if valores[6] != "N/A":
                lote_entry.insert(0, valores[6])
                
            if valores[7] == "N/A":
                fecha_venc_edit.set_date(datetime.now().date())
                fecha_venc_edit.configure(state='disabled')
                edit_sin_fecha_venc.set(True)
            else:
                fecha_venc_edit.set_date(datetime.strptime(valores[7], '%d/%m/%Y').date())
                fecha_venc_edit.configure(state='normal')
                edit_sin_fecha_venc.set(False)
                
            cantidad_entry.delete(0, tk.END)
            cantidad_entry.insert(0, valores[8])
            observaciones_entry.delete(0, tk.END)
            if valores[11]:
                observaciones_entry.insert(0, valores[11])

            edit_salida_distrito_var.set(valores[9] if valores[9] else '')
            edit_salida_servicio_var.set(valores[10] if valores[10] else '')

            actualizar_estado_salida_nivel_inferior_edit()
        
        editar_ventana.after(100, cargar_datos_iniciales)

        # **FRAME BOTONES**
        frame_botones = tk.Frame(scrollable_frame, bg=self.COLORS['light'])
        frame_botones.pack(fill="x", padx=20, pady=30)
        
        botones_container = tk.Frame(frame_botones, bg=self.COLORS['light'])
        botones_container.pack(anchor="center")
        
        def validar_campos():
            # Validar fecha registro
            if not fecha_edit.get_date():
                messagebox.showerror("Error", "La fecha de registro es obligatoria")
                return False

            # Validar referencia
            if not referencia_entry.get().strip():
                messagebox.showerror("Error", "La referencia es obligatoria")
                return False

            # Validar tipo movimiento
            if not edit_tipo_movimiento_var.get().strip():
                messagebox.showerror("Error", "El tipo de movimiento es obligatorio")
                return False

            # Validar insumo
            if not edit_insumo_var.get().strip():
                messagebox.showerror("Error", "El insumo es obligatorio")
                return False

            # Validar presentación
            if not edit_presentacion_var.get().strip():
                messagebox.showerror("Error", "La presentación es obligatoria")
                return False

            # Validar servicio según nivel de bodega
            nivel = edit_nivel_bodega_var.get()
            
            if nivel == "area":
                # Solo área es obligatorio, distrito, tipo_servicio y servicio pueden estar vacíos
                pass
            elif nivel == "distrito":
                if not edit_distrito_var.get().strip():
                    messagebox.showerror("Error", "El distrito es obligatorio para nivel Distrito")
                    return False
            elif nivel == "servicio":
                if not edit_distrito_var.get().strip():
                    messagebox.showerror("Error", "El distrito es obligatorio para nivel Servicio")
                    return False
                if not edit_tipo_servicio_var.get().strip():
                    messagebox.showerror("Error", "El tipo de servicio es obligatorio para nivel Servicio")
                    return False
                if not edit_servicio_var.get().strip():
                    messagebox.showerror("Error", "El servicio es obligatorio para nivel Servicio")
                    return False

            # Validar lote según checkbox
            if not edit_sin_lote_var.get():
                if not lote_entry.get().strip():
                    messagebox.showerror("Error", "El campo Lote es obligatorio si no está marcado 'Sin lote'")
                    return False

            # Validar fecha vencimiento según checkbox
            if not edit_sin_fecha_venc.get():
                if not fecha_venc_edit.get_date():
                    messagebox.showerror("Error", "El campo Fecha de Vencimiento es obligatorio si no está marcado 'Sin fecha vencimiento'")
                    return False

            # Validar cantidad numérica
            try:
                cantidad = float(cantidad_entry.get().strip())
                if cantidad <= 0:
                    messagebox.showerror("Error", "La cantidad debe ser un número positivo")
                    return False
            except ValueError:
                messagebox.showerror("Error", "La cantidad debe ser un número válido")
                return False

            return True

        def guardar_cambios():
            if not validar_campos():
                return

            lote_val = "N/A" if edit_sin_lote_var.get() else lote_entry.get().upper().strip()
            fecha_venc_val = "N/A" if edit_sin_fecha_venc.get() else fecha_venc_edit.get_date().strftime('%d/%m/%Y')

            nuevos_valores = (
                fecha_edit.get_date().strftime('%d/%m/%Y'),
                referencia_entry.get().upper().strip(),
                edit_tipo_movimiento_var.get().strip(),
                edit_insumo_var.get().strip(),
                edit_presentacion_var.get().strip(),
                edit_servicio_var.get().strip(),
                lote_val,
                fecha_venc_val,
                cantidad_entry.get().strip(),
                edit_salida_distrito_var.get().strip(),
                edit_salida_servicio_var.get().strip(),
                observaciones_entry.get().upper().strip(),
                edit_tipo_insumo_var.get().strip(),
                edit_area_var.get().strip(),
                edit_distrito_var.get().strip(),
                edit_tipo_servicio_var.get().strip()
            )

            self.tree.item(selected_item, values=nuevos_valores)
            self.ajustar_ancho_columnas_automatico()
            editar_ventana.destroy()
            messagebox.showinfo("Éxito", "Movimiento actualizado correctamente")

        # Botones con estilo
        btn_guardar = tk.Button(botones_container, 
            text="GUARDAR", 
            image=self.icon_guardar,
            compound='left',
            command=guardar_cambios,
            bg=self.COLORS['light'], 
            fg=self.COLORS['text_dark'],
            font=('Segoe UI', 9, 'bold'),
            relief='flat',
            padx=10, 
            pady=10,
            cursor='hand2',
            borderwidth=0,
            highlightthickness=0)
        btn_guardar.pack(side="left", padx=10)

        btn_cerrar = tk.Button(botones_container, 
            text="CERRAR", 
            image=self.icon_cerrar,
            compound='left',
            command=editar_ventana.destroy,
            bg=self.COLORS['light'], 
            fg=self.COLORS['text_dark'],
            font=('Segoe UI', 9, 'bold'),
            relief='flat',
            padx=10, 
            pady=10,
            cursor='hand2',
            borderwidth=0,
            highlightthickness=0)
        btn_cerrar.pack(side="left", padx=10)

        # **BINDINGS**
        edit_nivel_bodega_var.trace_add('write', actualizar_estado_comboboxes_edit)
        edit_tipo_movimiento_var.trace_add('write', actualizar_estado_salida_nivel_inferior_edit)
        edit_area_var.trace_add('write', lambda *a: self.on_area_selected_edit(edit_area_var, edit_distrito_var, distrito_cb))
        edit_distrito_var.trace_add('write', actualizar_tipos_servicio_edit)
        edit_tipo_servicio_var.trace_add('write', actualizar_servicios_edit)
        edit_salida_distrito_var.trace_add('write', actualizar_tipos_servicio_salida_edit)
        edit_salida_tipo_servicio_var.trace_add('write', actualizar_servicios_salida_edit)
        edit_tipo_insumo_var.trace_add('write', actualizar_insumos_edit)
        edit_insumo_var.trace_add('write', actualizar_presentacion_edit)    

    def eliminar_movimiento(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un movimiento para eliminar")
            return

        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este movimiento?"):
            self.tree.delete(selected_item)

    def guardar_movimientos(self):
        items = self.tree.get_children()
        if not items:
            messagebox.showwarning("Advertencia", "No hay movimientos para guardar")
            return

        if not messagebox.askyesno("Confirmar", "¿Está seguro de guardar todos los movimientos?"):
            return

        movimientos_guardados = 0
        errores = []

        for item in items:
            try:
                valores = self.tree.item(item)['values']

                # Obtener datos con los índices correctos
                fecha_registro_str = valores[0]
                referencia = valores[1]
                tipo_movimiento_desc = valores[2]
                insumo_nombre = valores[3]
                presentacion_nombre = valores[4]
                servicio_nombre = valores[5]
                lote = valores[6]
                if lote == "N/A":
                    lote = None
                fecha_vencimiento_str = valores[7]
                cantidad = float(valores[8])
                salida_distrito_nombre = valores[9] if valores[9] else None
                salida_servicio_nombre = valores[10] if valores[10] else None
                observaciones = valores[11] if valores[11] else None
                tipo_insumo_desc = valores[12]
                area_nombre = valores[13]          
                distrito_nombre = valores[14]       
                tipo_servicio_desc = valores[15]    

                # Validaciones
                if not tipo_insumo_desc:
                    raise ValueError("El tipo de insumo no puede estar vacío")

                # Obtener IDs
                area_id = None
                if area_nombre:
                    areas = obtener_areas() or []
                    area_id = next((a['id'] for a in areas if a['nombre'] == area_nombre), None)

                distrito_id = obtener_id_distrito(distrito_nombre) if distrito_nombre else None

                tipo_servicio_id = None
                if tipo_servicio_desc and distrito_id:
                    tipos_servicio = obtener_tipos_servicio_por_distrito(distrito_id) or []
                    tipo_servicio_id = next((ts['id'] for ts in tipos_servicio if ts['descripcion'] == tipo_servicio_desc), None)

                servicio_id = None
                if servicio_nombre and tipo_servicio_id:
                    servicios = obtener_servicios_por_tipo(tipo_servicio_id) or []
                    servicio_id = next((s['id'] for s in servicios if s['nombre'] == servicio_nombre), None)

                tipo_insumo_id = obtener_id_tipo_insumo(tipo_insumo_desc)
                if tipo_insumo_id is None:
                    raise ValueError(f"No se encontró el tipo de insumo: {tipo_insumo_desc}")

                insumo_id = obtener_id_insumo(insumo_nombre, tipo_insumo_id)
                if insumo_id is None:
                    raise ValueError(f"No se encontró el insumo: {insumo_nombre}")

                presentacion_id = obtener_id_presentacion(presentacion_nombre) if presentacion_nombre else None
                tipo_movimiento_id = obtener_id_tipo_movimiento(tipo_movimiento_desc)

                # Convertir fechas
                fecha_registro = datetime.strptime(fecha_registro_str, '%d/%m/%Y')
                if fecha_vencimiento_str == "N/A":
                    fecha_vencimiento = None
                else:
                    fecha_vencimiento = datetime.strptime(fecha_vencimiento_str, '%d/%m/%Y')

                # Manejar salida nivel inferior
                salida_distrito_id = obtener_id_distrito(salida_distrito_nombre) if salida_distrito_nombre else None
                salida_servicio_id = obtener_id_servicio(salida_servicio_nombre) if salida_servicio_nombre else None

                # Crear diccionario con datos del movimiento
                movimiento_data = {
                    'fecha_registro': fecha_registro,
                    'referencia': referencia,
                    'tipo_movimiento_id': tipo_movimiento_id,
                    'area_id': area_id,
                    'distrito_id': distrito_id,
                    'tipo_servicio_id': tipo_servicio_id,
                    'servicio_id': servicio_id,
                    'tipo_insumo_id': tipo_insumo_id,
                    'insumo_id': insumo_id,
                    'presentacion_id': presentacion_id,
                    'lote': lote,
                    'fecha_vencimiento': fecha_vencimiento,
                    'cantidad': cantidad,
                    'salida_distrito_id': salida_distrito_id,
                    'salida_servicio_id': salida_servicio_id,
                    'observaciones': observaciones
                }

                # Debug: imprimir los IDs que se van a guardar
                print(f"Guardando movimiento: area_id={area_id}, distrito_id={distrito_id}, servicio_id={servicio_id}")

                # Guardar movimiento
                guardar_movimiento(movimiento_data)
                movimientos_guardados += 1

            except Exception as e:
                errores.append(f"Error en movimiento {movimientos_guardados + 1}: {str(e)}")

        # Mostrar mensaje de resultado
        if errores:
            messagebox.showerror("Errores al guardar",
                                f"Se guardaron {movimientos_guardados} movimientos, pero hubo errores:\n" +
                                "\n".join(errores))
        else:
            messagebox.showinfo("Éxito",
                                f"Se guardaron {movimientos_guardados} movimientos correctamente")
            self.tree.delete(*self.tree.get_children())
            
        self.limpiar_campos_completo()
    
    # 6. Métodos de utilidad
    
    def limpiar_campos(self):
        """Limpia los campos del formulario sin afectar la fecha de registro seleccionada por el usuario"""        
        # **LIMPIAR SOLO LOS CAMPOS DE MOVIMIENTO ESPECÍFICO**
        self.tipo_movimiento_var.set('')
        self.salida_distrito_var.set('')
        self.salida_tipo_servicio_var.set('')
        self.salida_servicio_var.set('')

        # Limpiar entries de datos específicos del movimiento
        self.lote_entry.delete(0, 'end')
        self.referencia_entry.delete(0, 'end')
        self.cantidad_entry.delete(0, 'end')
        self.observaciones_entry.delete(0, 'end')

        # **MANTENER LA FECHA DE REGISTRO QUE SELECCIONÓ EL USUARIO**
        # self.fecha_reg.set_date(datetime.now())  # NO RESETEAR
        
        # Resetear fecha de vencimiento a la fecha actual
        self.fecha_venc.set_date(datetime.now())
        
        # Resetear checkboxes
        self.sin_lote_var.set(False)
        self.lote_entry.config(state='normal')
        
        self.sin_fecha_venc.set(False)
        self.fecha_venc.configure(state='normal')

        # **NO ACTUALIZAR ESTADOS DE COMBOBOXES - MANTENER CONFIGURACIÓN ACTUAL**
        # self.actualizar_estado_comboboxes()  # NO EJECUTAR

        # Ocultar frame de salida nivel inferior si está visible
        if self.frame_salida_nivel_inferior.winfo_ismapped():
            self.frame_salida_nivel_inferior.pack_forget()
      
    def limpiar_campos_completo(self):
        """Limpia TODOS los campos y selecciones - usado después de guardar movimientos"""
        
        # Limpiar configuración de servicios
        self.area_var.set('')
        self.distrito_var.set('')
        self.tipo_servicio_var.set('')
        self.servicio_var.set('')
        
        # Limpiar gestión de insumos
        self.tipo_insumo_var.set('')
        self.insumo_var.set('')
        self.presentacion_var.set('')
        
        # Limpiar registro de movimiento
        self.tipo_movimiento_var.set('')
        self.salida_distrito_var.set('')
        self.salida_tipo_servicio_var.set('')
        self.salida_servicio_var.set('')

        # Limpiar entries
        self.lote_entry.delete(0, 'end')
        self.referencia_entry.delete(0, 'end')
        self.cantidad_entry.delete(0, 'end')
        self.observaciones_entry.delete(0, 'end')

        # Resetear fechas a la fecha actual
        self.fecha_reg.set_date(datetime.now())
        self.fecha_venc.set_date(datetime.now())

        # Resetear nivel de bodega a "area"
        self.nivel_bodega_var.set("area")
        
        # Resetear checkboxes
        self.sin_lote_var.set(False)
        self.lote_entry.config(state='normal')
        
        self.sin_fecha_venc.set(False)
        self.fecha_venc.configure(state='normal')

        # Actualizar estados de los comboboxes
        self.actualizar_estado_comboboxes()

        # Ocultar frame de salida nivel inferior si está visible
        if self.frame_salida_nivel_inferior.winfo_ismapped():
            self.frame_salida_nivel_inferior.pack_forget()
        
        # Limpiar listas de comboboxes
        self.distrito_cb.config(completevalues=[])
        self.tipo_servicio_cb.config(completevalues=[])
        self.servicio_cb.config(completevalues=[])
        self.insumo_cb.config(completevalues=[])
        self.presentacion_cb.config(completevalues=[])
      
    def ajustar_ancho_columnas_automatico(self):
        import tkinter.font as tkFont
        font = tkFont.Font(family="Segoe UI", size=9)

        max_widths = {}
        for col in self.tree['columns']:
            header_text = str(self.tree.heading(col)['text'])
            header_width = font.measure(header_text) + 30
            max_widths[col] = max(80, header_width)

        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            for i, col in enumerate(self.tree['columns']):
                if i < len(values) and values[i] is not None:
                    cell_text = str(values[i])
                    cell_width = font.measure(cell_text) + 25
                    max_widths[col] = max(max_widths.get(col, 80), cell_width)

        limites_configuracion = {
            'fecha_registro': {'min': 100, 'max': 140},
            'referencia': {'min': 80, 'max': 150},
            'tipo_movimiento': {'min': 120, 'max': 200},
            'insumo': {'min': 200, 'max': 600},
            'presentacion': {'min': 100, 'max': 180},
            'servicio': {'min': 120, 'max': 280},
            'lote': {'min': 60, 'max': 120},
            'fecha_vencimiento': {'min': 100, 'max': 140},
            'cantidad': {'min': 70, 'max': 100},
            'salida_distrito': {'min': 100, 'max': 200},
            'salida_servicio': {'min': 120, 'max': 250},
            'observaciones': {'min': 150, 'max': 400},
            'tipo_insumo': {'min': 100, 'max': 180},
            'area': {'min': 80, 'max': 160},
            'distrito': {'min': 100, 'max': 180},
            'tipo_servicio': {'min': 120, 'max': 200}
        }

        for col in max_widths:
            ancho_calculado = max_widths[col]
            config = limites_configuracion.get(col, {'min': 80, 'max': 200})
            if col == 'insumo':
                ancho_final = max(config['min'], min(ancho_calculado, config['max']))
                if ancho_calculado > config['max']:
                    ancho_final = min(ancho_calculado, 800)
            else:
                ancho_final = max(config['min'], min(ancho_calculado, config['max']))
            self.tree.column(col, width=ancho_final, minwidth=config['min'])

        self.tree.update_idletasks()
                            
    def ajustar_tamano_ventana(self, mostrar_salida):
        """Ajusta el tamaño de la ventana cuando se muestra/oculta el frame de salida"""
        if mostrar_salida:
            # Calcular altura adicional necesaria
            self.parent.update_idletasks()
            altura_frame = self.frame_salida_nivel_inferior.winfo_reqheight() + 50
            self.main_window.resize_window_for_content(altura_frame)
        else:
            # Restaurar tamaño original
            self.main_window.reset_window_size()
        
    def cerrar_ventana(self):
        if messagebox.askyesno("Confirmar", "¿Está seguro que desea cerrar esta ventana?"):
            # Limpiar el frame principal
            for widget in self.parent.winfo_children():
                widget.destroy()
            # Mostrar la pantalla de bienvenida si existe
            if hasattr(self, "main_window") and self.main_window:
                self.main_window.show_welcome_screen()

    # 7. Métodos auxiliares
    
    def on_area_selected(self, *args):
        area_nombre = self.area_var.get()
        areas = obtener_areas() or []
        area_id = next((a['id'] for a in areas if a['nombre'] == area_nombre), None)

        if area_id:
            distritos = obtener_distritos_por_area(area_id) or []
            distritos_nombres = [d['nombre'] for d in distritos]
            self.distrito_cb.config(completevalues=distritos_nombres)
            self.distrito_var.set('')
        else:
            self.distrito_cb.config(completevalues=[])
            self.distrito_var.set('')
    
    def on_area_selected_edit(self, area_var, distrito_var, distrito_cb):
        area_nombre = area_var.get()
        areas = obtener_areas() or []
        area_id = next((a['id'] for a in areas if a['nombre'] == area_nombre), None)

        if area_id:
            distritos = obtener_distritos_por_area(area_id) or []
            distritos_nombres = [d['nombre'] for d in distritos]
            distrito_cb.set_completion_list(distritos_nombres)
            if distrito_var.get() not in distritos_nombres:
                distrito_var.set('')
        else:
            distrito_cb.set_completion_list([])
            distrito_var.set('')