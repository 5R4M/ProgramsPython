import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
import sys
import os
from ttkwidgets.autocomplete import AutocompleteCombobox

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

class IngresoInsumos:
    def __init__(self, parent_frame, main_window):
        
        self.parent = parent_frame
        self.main_window = main_window

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
            # Forzar actualización del canvas y scroll region
            self.parent.update_idletasks()
            
            # Actualizar scroll region
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
            # Ajustar ancho del frame scrollable
            canvas_width = self.canvas.winfo_width()
            if canvas_width > 1:  # Evitar errores si el canvas no está listo
                self.canvas.itemconfig(self.canvas_window, width=canvas_width)
                
        except (tk.TclError, AttributeError):
            # Ignorar errores si los widgets no están listos
            pass
    
    def setup_styles(self):
        """Configura los estilos profesionales para la interfaz"""
        # Colores del tema profesional (mantener igual)
        self.COLORS = {
            'primary': '#2c3e50',
            'secondary': '#34495e',
            'accent': '#3498db',
            'success': '#27ae60',
            'warning': '#f39c12',
            'danger': '#e74c3c',
            'light': '#ecf0f1',
            'white': '#ffffff',
            'text_dark': '#2c3e50',
            'text_light': '#7f8c8d',
            'hover': '#3498db',
            'active': '#2980b9',
            'card_bg': '#ffffff',
            'border': '#bdc3c7'
        }

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
            font=('Segoe UI', 10, 'bold'),
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
            background=[('active', self.COLORS['hover']),
            ('pressed', self.COLORS['active'])])
        
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
    
    # 1. Métodos de configuración de UI
    
    def setup_ui(self):
        
        # Frame principal que contendrá el canvas y scrollbar
        main_container = tk.Frame(self.parent, bg=self.COLORS['light'])
        main_container.pack(fill="both", expand=True)
        
        # Canvas para el scroll
        self.canvas = tk.Canvas(main_container, bg=self.COLORS['light'], highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Scrollbar vertical
        v_scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=self.canvas.yview)
        v_scrollbar.pack(side="right", fill="y")
        
        # Scrollbar horizontal
        h_scrollbar = ttk.Scrollbar(self.parent, orient="horizontal", command=self.canvas.xview)
        h_scrollbar.pack(side="bottom", fill="x")
        
        # Configurar canvas
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Frame scrollable que contendrá todo el contenido
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.COLORS['light'])
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # **HEADER PRINCIPAL**
        header_frame = tk.Frame(self.scrollable_frame, bg=self.COLORS['white'], height=60)
        
        header_frame.pack(fill='x', padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Frame interno con padding
        header_inner = tk.Frame(header_frame, bg=self.COLORS['white'])
        header_inner.pack(fill='both', expand=True, padx=15, pady=8)
        
        # Título principal
        title_label = tk.Label(header_inner, 
                            text="Ingreso de Movimientos al Sistema",
                            font=('Segoe UI', 14, 'bold'),
                            fg=self.COLORS['primary'],
                            bg=self.COLORS['white'])
        title_label.pack(anchor='w')
        
        # Subtítulo
        subtitle_label = tk.Label(header_inner,
                                text="Registre los movimientos de insumos de manera eficiente y organizada",
                                font=('Segoe UI', 8),
                                fg=self.COLORS['text_light'],
                                bg=self.COLORS['white'])
        subtitle_label.pack(anchor='w', pady=(2, 0))
        
        # Línea decorativa
        line_frame = tk.Frame(header_inner, bg=self.COLORS['accent'], height=2)
        line_frame.pack(fill='x', pady=(5, 0))
        
        # Frame Nivel de Bodega (radio buttons)
        nivel_container = tk.Frame(self.scrollable_frame, bg=self.COLORS['light'])
        nivel_container.pack(fill="x", padx=15, pady=5)
        
        self.frame_nivel_bodega = tk.Frame(nivel_container, 
                                        bg=self.COLORS['white'], 
                                        relief='solid', 
                                        borderwidth=1)
        self.frame_nivel_bodega.pack(fill="x", padx=8, pady=5)
        
        # Header del frame
        nivel_header = tk.Frame(self.frame_nivel_bodega, bg=self.COLORS['primary'], height=25)
        nivel_header.pack(fill='x')
        nivel_header.pack_propagate(False)
        
        tk.Label(nivel_header, 
                text="🏢 Nivel de Bodega", 
                font=('Segoe UI', 10, 'bold'),
                fg=self.COLORS['white'], 
                bg=self.COLORS['primary']).pack(side='left', padx=10, pady=4)
        
        # Contenido del frame
        nivel_content = tk.Frame(self.frame_nivel_bodega, bg=self.COLORS['white'])
        nivel_content.pack(fill='x', padx=12, pady=6)
        
        # Radio buttons con estilo mejorado
        rb_frame = tk.Frame(nivel_content, bg=self.COLORS['white'])
        rb_frame.pack(anchor='w')
        
        rb_area = tk.Radiobutton(rb_frame, 
                                text="📍 Área", 
                                variable=self.nivel_bodega_var, 
                                value="area",
                                command=self.actualizar_estado_comboboxes,
                                font=('Segoe UI', 9),
                                bg=self.COLORS['white'],
                                fg=self.COLORS['text_dark'],
                                selectcolor=self.COLORS['white'],
                                activebackground=self.COLORS['white'])
        
        rb_distrito = tk.Radiobutton(rb_frame, 
                                    text="🏛️ Distrito", 
                                    variable=self.nivel_bodega_var, 
                                    value="distrito",
                                    command=self.actualizar_estado_comboboxes,
                                    font=('Segoe UI', 9),
                                    bg=self.COLORS['white'],
                                    fg=self.COLORS['text_dark'],
                                    selectcolor=self.COLORS['white'],
                                    activebackground=self.COLORS['white'])
        
        rb_servicio = tk.Radiobutton(rb_frame, 
                                    text="🏥 Servicio", 
                                    variable=self.nivel_bodega_var, 
                                    value="servicio",
                                    command=self.actualizar_estado_comboboxes,
                                    font=('Segoe UI', 9),
                                    bg=self.COLORS['white'],
                                    fg=self.COLORS['text_dark'],
                                    selectcolor=self.COLORS['white'],
                                    activebackground=self.COLORS['white'])
        
        rb_area.pack(side='left', padx=(0, 25))
        rb_distrito.pack(side='left', padx=(0, 25))
        rb_servicio.pack(side='left')
        
        # **FRAME SERVICIOS MEJORADO**
        servicios_container = tk.Frame(self.scrollable_frame, bg=self.COLORS['light'])
        servicios_container.pack(fill="x", padx=15, pady=5)
        
        self.frame_servicios = tk.Frame(servicios_container, 
                                    bg=self.COLORS['white'], 
                                    relief='solid', 
                                    borderwidth=1)
        self.frame_servicios.pack(fill="x", padx=8, pady=5)
        
        # Header del frame
        servicios_header = tk.Frame(self.frame_servicios, bg=self.COLORS['success'], height=25)
        servicios_header.pack(fill='x')
        servicios_header.pack_propagate(False)
        
        tk.Label(servicios_header, 
                text="🏥 Configuración de Servicios", 
                font=('Segoe UI', 9, 'bold'),
                fg=self.COLORS['white'], 
                bg=self.COLORS['success']).pack(side='left', padx=10, pady=4)
        
        # Contenido del frame con grid mejorado
        servicios_content = tk.Frame(self.frame_servicios, bg=self.COLORS['white'])
        servicios_content.pack(fill='x', padx=12, pady=6)
        
        # Configurar grid
        for i in range(4):
            servicios_content.columnconfigure(i*2+1, weight=1)
        
        # Área
        tk.Label(servicios_content, text="Área:", 
                font=('Segoe UI', 8, 'bold'),
                fg=self.COLORS['text_dark'],
                bg=self.COLORS['white']).grid(row=0, column=0, padx=(0, 8), pady=6, sticky="w")
        
        areas = [a['nombre'] for a in obtener_areas() or []]
        self.area_var = tk.StringVar()
        self.area_cb = AutocompleteCombobox(servicios_content, 
                                        textvariable=self.area_var, 
                                        width=16, 
                                        completevalues=areas, 
                                        state="normal",
                                        font=('Segoe UI', 8))
        self.area_cb.grid(row=0, column=1, padx=(0, 15), pady=6, sticky="ew")
        
        # Distrito
        tk.Label(servicios_content, text="Distrito:", 
                font=('Segoe UI', 9, 'bold'),
                fg=self.COLORS['text_dark'],
                bg=self.COLORS['white']).grid(row=0, column=2, padx=(0, 8), pady=6, sticky="w")
        
        self.distrito_var = tk.StringVar()
        distritos = [d['nombre'] for d in obtener_distritos() or []]
        self.distrito_cb = AutocompleteCombobox(servicios_content, 
                                            textvariable=self.distrito_var, 
                                            width=18, 
                                            completevalues=distritos, 
                                            state="normal",
                                            font=('Segoe UI', 9))
        self.distrito_cb.grid(row=0, column=3, padx=(0, 20), pady=8, sticky="ew")
        
        # Tipo de Servicio
        tk.Label(servicios_content, text="Tipo de Servicio:", 
                font=('Segoe UI', 9, 'bold'),
                fg=self.COLORS['text_dark'],
                bg=self.COLORS['white']).grid(row=1, column=0, padx=(0, 8), pady=6, sticky="w")
        
        self.tipo_servicio_var = tk.StringVar()
        self.tipo_servicio_cb = AutocompleteCombobox(servicios_content, 
                                                    textvariable=self.tipo_servicio_var, 
                                                    width=18, 
                                                    completevalues=[], 
                                                    state="normal",
                                                    font=('Segoe UI', 9))
        self.tipo_servicio_cb.grid(row=1, column=1, padx=(0, 20), pady=8, sticky="ew")
        
        # Servicio
        tk.Label(servicios_content, text="Servicio:", 
                font=('Segoe UI', 9, 'bold'),
                fg=self.COLORS['text_dark'],
                bg=self.COLORS['white']).grid(row=1, column=2, padx=(0, 8), pady=6, sticky="w")
        
        self.servicio_var = tk.StringVar()
        self.servicio_cb = AutocompleteCombobox(servicios_content, 
                                            textvariable=self.servicio_var, 
                                            width=18, 
                                            completevalues=[], 
                                            state="normal",
                                            font=('Segoe UI', 9))
        self.servicio_cb.grid(row=1, column=3, padx=(0, 20), pady=8, sticky="ew")
        
        # Inicializar distritos vacíos
        self.distrito_cb.config(completevalues=[])
        self.distrito_var.set('')

        # **FRAME INSUMOS MEJORADO**
        insumos_container = tk.Frame(self.scrollable_frame, bg=self.COLORS['light'])
        insumos_container.pack(fill="x", padx=20, pady=8)

        self.frame_insumos = tk.Frame(insumos_container,
            bg=self.COLORS['white'],
            relief='solid',
            borderwidth=1)
        self.frame_insumos.pack(fill="x", padx=10, pady=10)

        # Header del frame
        insumos_header = tk.Frame(self.frame_insumos, bg=self.COLORS['warning'], height=30)
        insumos_header.pack(fill='x')
        insumos_header.pack_propagate(False)

        tk.Label(insumos_header,
            text="💊 Gestión de Insumos",
            font=('Segoe UI', 10, 'bold'),
            fg=self.COLORS['white'],
            bg=self.COLORS['warning']).pack(side='left', padx=12, pady=6)

        # Contenido del frame
        insumos_content = tk.Frame(self.frame_insumos, bg=self.COLORS['white'])
        insumos_content.pack(fill='x', padx=15, pady=10)

        # Configurar grid
        for i in range(3):
            insumos_content.columnconfigure(i*2+1, weight=1)

        # Tipo de Insumo
        tk.Label(insumos_content, text="Tipo de Insumo:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['white']).grid(row=0, column=0, padx=(0, 8), pady=6, sticky="w")

        tipos_insumo = [ti['descripcion'] for ti in obtener_tipos_insumo() or []]
        self.tipo_insumo_cb = AutocompleteCombobox(insumos_content,
            textvariable=self.tipo_insumo_var,
            width=20,
            completevalues=tipos_insumo,
            state="normal",
            font=('Segoe UI', 9))
        self.tipo_insumo_cb.grid(row=0, column=1, padx=(0, 20), pady=8, sticky="ew")

        # Insumo
        tk.Label(insumos_content, text="Insumo:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['white']).grid(row=0, column=2, padx=(0, 8), pady=6, sticky="w")

        self.insumo_cb = AutocompleteCombobox(insumos_content,
            textvariable=self.insumo_var,
            width=20,
            completevalues=[],
            state="normal",
            font=('Segoe UI', 9))
        self.insumo_cb.grid(row=0, column=3, padx=(0, 20), pady=8, sticky="ew")

        # Presentación
        tk.Label(insumos_content, text="Presentación:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['white']).grid(row=0, column=4, padx=(0, 8), pady=6, sticky="w")

        self.presentacion_cb = AutocompleteCombobox(insumos_content,
            textvariable=self.presentacion_var,
            width=20,
            completevalues=[],
            state="normal",
            font=('Segoe UI', 9))
        self.presentacion_cb.grid(row=0, column=5, padx=0, pady=8, sticky="ew")

        # **SEGUNDA FILA - Lote y Fecha de Vencimiento**
        # Separador visual
        separator_frame = tk.Frame(insumos_content, bg=self.COLORS['border'], height=1)
        separator_frame.grid(row=1, column=0, columnspan=6, sticky="ew", pady=10)

        # Lote
        tk.Label(insumos_content, text="Lote:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['white']).grid(row=2, column=0, padx=(0, 8), pady=6, sticky="w")

        # Frame para lote y checkbox
        frame_lote = tk.Frame(insumos_content, bg=self.COLORS['white'])
        frame_lote.grid(row=2, column=1, padx=(0, 20), pady=8, sticky="ew")
        frame_lote.columnconfigure(0, weight=1)

        self.lote_entry = ttk.Entry(frame_lote, 
            textvariable=self.lote_var,
            font=('Segoe UI', 9))
        self.lote_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        # Checkbox Sin lote con estilo
        self.sin_lote_var = tk.BooleanVar()
        self.check_sin_lote = tk.Checkbutton(frame_lote,
            text="Sin lote",
            variable=self.sin_lote_var,
            command=lambda: self.lote_entry.config(state='disabled' if self.sin_lote_var.get() else 'normal'),
            font=('Segoe UI', 9),
            bg=self.COLORS['white'],
            fg=self.COLORS['text_dark'],
            selectcolor=self.COLORS['white'],
            activebackground=self.COLORS['white'])
        self.check_sin_lote.grid(row=0, column=1, sticky="w")

        # Fecha de Vencimiento
        tk.Label(insumos_content, text="Fecha Vencimiento:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['white']).grid(row=2, column=2, padx=(0, 8), pady=6, sticky="w")

        # Frame para fecha y checkbox
        frame_fecha = tk.Frame(insumos_content, bg=self.COLORS['white'])
        frame_fecha.grid(row=2, column=3, columnspan=2, padx=0, pady=8, sticky="ew")
        frame_fecha.columnconfigure(0, weight=1)

        self.fecha_venc = DateEntry(frame_fecha, 
            width=12, 
            background='darkblue',
            foreground='white', 
            borderwidth=2, 
            date_pattern='dd/mm/yyyy',
            font=('Segoe UI', 9))
        self.fecha_venc.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        # Checkbox Sin fecha de vencimiento
        self.sin_fecha_venc = tk.BooleanVar()
        self.check_sin_fecha = tk.Checkbutton(frame_fecha,
            text="Sin fecha",
            variable=self.sin_fecha_venc,
            command=self.toggle_fecha_vencimiento,
            font=('Segoe UI', 9),
            bg=self.COLORS['white'],
            fg=self.COLORS['text_dark'],
            selectcolor=self.COLORS['white'],
            activebackground=self.COLORS['white'])
        self.check_sin_fecha.grid(row=0, column=1, sticky="w")
        
        # **FRAME REGISTRO DE MOVIMIENTO MEJORADO**
        registro_container = tk.Frame(self.scrollable_frame, bg=self.COLORS['light'])
        registro_container.pack(fill="x", padx=20, pady=8)

        self.frame_registro = tk.Frame(registro_container,
            bg=self.COLORS['white'],
            relief='solid',
            borderwidth=1)
        self.frame_registro.pack(fill="x", padx=10, pady=10)

        # Header del frame
        registro_header = tk.Frame(self.frame_registro, bg=self.COLORS['accent'], height=30)
        registro_header.pack(fill='x')
        registro_header.pack_propagate(False)

        tk.Label(registro_header,
            text="📋 Registro de Movimiento",
            font=('Segoe UI', 10, 'bold'),
            fg=self.COLORS['white'],
            bg=self.COLORS['accent']).pack(side='left', padx=12, pady=6)

        # Contenido del frame
        registro_content = tk.Frame(self.frame_registro, bg=self.COLORS['white'])
        registro_content.pack(fill='x', padx=15, pady=10)

        # Configurar grid
        for i in range(3):
            registro_content.columnconfigure(i*2+1, weight=1)

        # **PRIMERA FILA**
        # Fecha de Registro
        tk.Label(registro_content, text="Fecha de Registro:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['white']).grid(row=0, column=0, padx=(0, 8), pady=6, sticky="w")

        self.fecha_reg = DateEntry(registro_content, 
            width=18, 
            background='darkblue',
            foreground='white', 
            borderwidth=2, 
            date_pattern='dd/mm/yyyy',
            font=('Segoe UI', 9))
        self.fecha_reg.grid(row=0, column=1, padx=(0, 20), pady=8, sticky="ew")

        # Referencia
        tk.Label(registro_content, text="Referencia:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['white']).grid(row=0, column=2, padx=(0, 8), pady=6, sticky="w")

        self.referencia_entry = ttk.Entry(registro_content, 
            width=20,
            font=('Segoe UI', 9))
        self.referencia_entry.grid(row=0, column=3, padx=(0, 20), pady=8, sticky="ew")

        # Tipo de Movimiento
        tk.Label(registro_content, text="Tipo de Movimiento:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['white']).grid(row=0, column=4, padx=(0, 9), pady=6, sticky="w")

        tipos_movimiento = [tm['descripcion'] for tm in obtener_tipos_movimiento() or []]
        self.tipo_mov_cb = AutocompleteCombobox(registro_content,
            textvariable=self.tipo_movimiento_var,
            width=20,
            completevalues=tipos_movimiento,
            state="normal",
            font=('Segoe UI', 9))
        self.tipo_mov_cb.grid(row=0, column=5, padx=0, pady=8, sticky="ew")

        # Separador visual
        separator_frame2 = tk.Frame(registro_content, bg=self.COLORS['border'], height=1)
        separator_frame2.grid(row=1, column=0, columnspan=6, sticky="ew", pady=10)

        # **SEGUNDA FILA**
        # Cantidad
        tk.Label(registro_content, text="Cantidad:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['white']).grid(row=2, column=0, padx=(0, 8), pady=6, sticky="w")

        self.cantidad_entry = ttk.Entry(registro_content, 
            width=18,
            font=('Segoe UI', 9))
        self.cantidad_entry.grid(row=2, column=1, padx=(0, 20), pady=8, sticky="ew")

        # Observaciones
        tk.Label(registro_content, text="Observaciones:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['white']).grid(row=2, column=2, padx=(0, 8), pady=6, sticky="w")

        self.observaciones_entry = ttk.Entry(registro_content, 
            width=40,
            font=('Segoe UI', 9))
        self.observaciones_entry.grid(row=2, column=3, columnspan=3, padx=0, pady=8, sticky="ew")
        
        # **FRAME SALIDA NIVEL INFERIOR MEJORADO**
        salida_container = tk.Frame(self.scrollable_frame, bg=self.COLORS['light'])
        
        self.frame_salida_nivel_inferior = tk.Frame(salida_container,
            bg=self.COLORS['white'],
            relief='solid',
            borderwidth=1)

        # Header del frame
        salida_header = tk.Frame(self.frame_salida_nivel_inferior, bg=self.COLORS['danger'], height=25)
        salida_header.pack(fill='x')
        salida_header.pack_propagate(False)

        tk.Label(salida_header,
            text="🔄 Salida a Nivel Inferior",
            font=('Segoe UI', 9, 'bold'),
            fg=self.COLORS['white'],
            bg=self.COLORS['danger']).pack(side='left', padx=10, pady=4)

        # Contenido del frame
        salida_content = tk.Frame(self.frame_salida_nivel_inferior, bg=self.COLORS['white'])
        salida_content.pack(fill='x', padx=12, pady=6)

        # Configurar grid
        for i in range(3):
            salida_content.columnconfigure(i*2+1, weight=1)

        # Distrito
        tk.Label(salida_content, text="Distrito:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['white']).grid(row=0, column=0, padx=(0, 8), pady=6, sticky="w")

        distritos = [d['nombre'] for d in obtener_distritos() or []]
        self.salida_distrito_cb = AutocompleteCombobox(salida_content,
            textvariable=self.salida_distrito_var,
            width=20,
            completevalues=distritos,
            state="disabled",
            font=('Segoe UI', 9))
        self.salida_distrito_cb.grid(row=0, column=1, padx=(0, 20), pady=8, sticky="ew")

        # Tipo de Servicio
        tk.Label(salida_content, text="Tipo de Servicio:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['white']).grid(row=0, column=2, padx=(0, 8), pady=6, sticky="w")

        self.salida_tipo_servicio_cb = AutocompleteCombobox(salida_content,
            textvariable=self.salida_tipo_servicio_var,
            width=20,
            completevalues=[],
            state="disabled",
            font=('Segoe UI', 9))
        self.salida_tipo_servicio_cb.grid(row=0, column=3, padx=(0, 20), pady=8, sticky="ew")

        # Servicio
        tk.Label(salida_content, text="Servicio:",
            font=('Segoe UI', 9, 'bold'),
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['white']).grid(row=0, column=4, padx=(0, 8), pady=6, sticky="w")

        self.salida_servicio_cb = AutocompleteCombobox(salida_content,
            textvariable=self.salida_servicio_var,
            width=20,
            completevalues=[],
            state="disabled",
            font=('Segoe UI', 9))
        self.salida_servicio_cb.grid(row=0, column=5, padx=0, pady=8, sticky="ew")

        # Inicializar combobox vacíos
        self.salida_tipo_servicio_cb.config(completevalues=[])
        self.salida_tipo_servicio_var.set('')
        self.salida_servicio_cb.config(completevalues=[])
        self.salida_servicio_var.set('')

        # Guardar referencia del contenedor para poder mostrarlo/ocultarlo
        self.salida_container = salida_container
        
        # **BOTÓN AGREGAR MOVIMIENTO MEJORADO**
        btn_container = tk.Frame(self.scrollable_frame, bg=self.COLORS['light'])
        btn_container.pack(fill="x", padx=20, pady=10)

        btn_inner = tk.Frame(btn_container, bg=self.COLORS['white'])
        btn_inner.pack(padx=10, pady=10)

        self.btn_agregar = tk.Button(btn_inner,
            text="➕ Agregar Movimiento",
            command=self.agregar_movimiento,
            font=('Segoe UI', 10, 'bold'),
            bg=self.COLORS['success'],
            fg=self.COLORS['white'],
            relief='flat',
            borderwidth=0,
            padx=25,
            pady=8,
            cursor='hand2')
        self.btn_agregar.pack()

        # Efectos hover para el botón
        def on_enter_agregar(e):
            self.btn_agregar.config(bg='#229954')
        def on_leave_agregar(e):
            self.btn_agregar.config(bg=self.COLORS['success'])

        self.btn_agregar.bind('<Enter>', on_enter_agregar)
        self.btn_agregar.bind('<Leave>', on_leave_agregar)

        # **FRAME MOVIMIENTOS MEJORADO**
        movimientos_container = tk.Frame(self.scrollable_frame, bg=self.COLORS['light'])
        movimientos_container.pack(fill="both", expand=True, padx=20, pady=8)

        self.frame_movimientos = tk.Frame(movimientos_container,
            bg=self.COLORS['white'],
            relief='solid',
            borderwidth=1)
        self.frame_movimientos.pack(fill="both", expand=True, padx=10, pady=10)

        # Header del frame
        movimientos_header = tk.Frame(self.frame_movimientos, bg=self.COLORS['secondary'], height=40)
        movimientos_header.pack(fill='x')
        movimientos_header.pack_propagate(False)

        tk.Label(movimientos_header,
            text="📊 Lista de Movimientos Registrados",
            font=('Segoe UI', 11, 'bold'),
            fg=self.COLORS['white'],
            bg=self.COLORS['secondary']).pack(side='left', padx=15, pady=10)

        # Contenido del treeview
        tree_content = tk.Frame(self.frame_movimientos, bg=self.COLORS['white'])
        tree_content.pack(fill="both", expand=True, padx=15, pady=15)

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
            rowheight=25,
            fieldbackground=self.COLORS['white'],
            font=('Segoe UI', 8),
            borderwidth=1,
            relief='solid')

        # **CONFIGURAR HEADERS CON COLORES CONTRASTANTES**
        style.configure("Custom.Treeview.Heading",
            background='#34495e',  # ← Color fijo que funciona
            foreground='white',    # ← Color fijo que funciona
            font=('Segoe UI', 8, 'bold'),
            relief='raised',
            borderwidth=1)

        # Mapeos para interactividad
        style.map("Custom.Treeview.Heading",
            background=[('active', '#2c3e50')],
            foreground=[('active', 'white')])

        style.map("Custom.Treeview",
            background=[('selected', self.COLORS['accent'])],
            foreground=[('selected', 'white')])

        # **CONFIGURAR GRID PARA POSICIONAMIENTO CORRECTO DE SCROLLBARS**
        tree_content.grid_rowconfigure(0, weight=1)
        tree_content.grid_columnconfigure(0, weight=1)

        # **CREAR TREEVIEW**
        self.tree = ttk.Treeview(tree_content,
            columns=columns,
            show='headings',
            height=6,
            style="Custom.Treeview")

        # Configurar headers
        encabezados = {
            'fecha_registro': 'Fecha de Registro',
            'referencia': 'Referencia',
            'tipo_movimiento': 'Tipo de Movimiento',
            'insumo': 'Insumo',
            'presentacion': 'Presentación',
            'servicio': 'Servicio',
            'lote': 'Lote',
            'fecha_vencimiento': 'Fecha de Vencimiento',
            'cantidad': 'Cantidad',
            'salida_distrito': 'Salida Distrito',
            'salida_servicio': 'Salida Servicio',
            'observaciones': 'Observaciones',
            'tipo_insumo': 'Tipo Insumo',
            'area': 'Área',
            'distrito': 'Distrito',
            'tipo_servicio': 'Tipo Servicio'
        }

        for col in columns:
            self.tree.heading(col, text=encabezados[col])
            self.tree.column(col, width=120, minwidth=80)

        # **POSICIONAR TREEVIEW Y SCROLLBARS CON GRID**
        # Treeview en posición principal (fila 0, columna 0)
        self.tree.grid(row=0, column=0, sticky="nsew")

        # Scrollbar vertical a la derecha (fila 0, columna 1)
        scrollbar_y = ttk.Scrollbar(tree_content, orient="vertical", command=self.tree.yview)
        scrollbar_y.grid(row=0, column=1, sticky="ns")

        # Scrollbar horizontal debajo (fila 1, columna 0)
        scrollbar_x = ttk.Scrollbar(tree_content, orient="horizontal", command=self.tree.xview)
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        # **CONFIGURAR SCROLLBARS EN EL TREEVIEW**
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # Función para ajustar columnas automáticamente
        def on_treeview_configure(event):
            if event.widget == self.tree:
                width = event.width
                col_width = max(100, width // len(columns) - 5)
                for col in columns:
                    self.tree.column(col, width=col_width, minwidth=80)

        self.tree.bind('<Configure>', on_treeview_configure)

        # **SCROLL CON MOUSE WHEEL PARA EL TREEVIEW**
        def on_treeview_mousewheel(event):
            self.tree.yview_scroll(int(-1*(event.delta/120)), "units")

        def bind_treeview_mousewheel(event):
            self.tree.bind_all("<MouseWheel>", on_treeview_mousewheel)

        def unbind_treeview_mousewheel(event):
            self.tree.unbind_all("<MouseWheel>")

        self.tree.bind('<Enter>', bind_treeview_mousewheel)
        self.tree.bind('<Leave>', unbind_treeview_mousewheel)

        # **FRAME BOTONES FINALES MEJORADO**
        botones_container = tk.Frame(self.scrollable_frame, bg=self.COLORS['light'])
        botones_container.pack(fill="x", padx=20, pady=10)

        self.frame_botones = tk.Frame(botones_container, bg=self.COLORS['white'])
        self.frame_botones.pack(fill="x", padx=10, pady=10)

        # Frame interno para centrar botones
        botones_inner = tk.Frame(self.frame_botones, bg=self.COLORS['white'])
        botones_inner.pack(expand=True, pady=15)

        # Botón Editar
        self.btn_editar = tk.Button(botones_inner,
            text="✏️ Editar",
            command=self.editar_movimiento,
            font=('Segoe UI', 9, 'bold'),
            bg=self.COLORS['warning'],
            fg=self.COLORS['white'],
            relief='flat',
            borderwidth=0,
            padx=15,
            pady=6,
            cursor='hand2')
        self.btn_editar.pack(side="left", padx=10)

        # Botón Eliminar
        self.btn_eliminar = tk.Button(botones_inner,
            text="🗑️ Eliminar",
            command=self.eliminar_movimiento,
            font=('Segoe UI', 9, 'bold'),
            bg=self.COLORS['danger'],
            fg=self.COLORS['white'],
            relief='flat',
            borderwidth=0,
            padx=15,
            pady=6,
            cursor='hand2')
        self.btn_eliminar.pack(side="left", padx=10)

        # Botón Guardar
        self.btn_guardar = tk.Button(botones_inner,
            text="💾 Guardar Movimientos",
            command=self.guardar_movimientos,
            font=('Segoe UI', 9, 'bold'),
            bg=self.COLORS['success'],
            fg=self.COLORS['white'],
            relief='flat',
            borderwidth=0,
            padx=15,
            pady=6,
            cursor='hand2')
        self.btn_guardar.pack(side="left", padx=10)

        # Botón Cerrar
        self.btn_cerrar = tk.Button(botones_inner,
            text="❌ Cerrar",
            command=self.cerrar_ventana,
            font=('Segoe UI', 9, 'bold'),
            bg=self.COLORS['secondary'],
            fg=self.COLORS['white'],
            relief='flat',
            borderwidth=0,
            padx=15,
            pady=6,
            cursor='hand2')
        self.btn_cerrar.pack(side="right", padx=10)

        # Efectos hover para todos los botones
        def create_hover_effect(button, normal_color, hover_color):
            def on_enter(e):
                button.config(bg=hover_color)
            def on_leave(e):
                button.config(bg=normal_color)
            button.bind('<Enter>', on_enter)
            button.bind('<Leave>', on_leave)

        create_hover_effect(self.btn_editar, self.COLORS['warning'], '#e67e22')
        create_hover_effect(self.btn_eliminar, self.COLORS['danger'], '#c0392b')
        create_hover_effect(self.btn_guardar, self.COLORS['success'], '#229954')
        create_hover_effect(self.btn_cerrar, self.COLORS['secondary'], '#2c3e50')

        # Ocultar inicialmente el frame de salida nivel inferior
        self.frame_salida_nivel_inferior.pack_forget()
        
        # Función para actualizar el scroll region
        def configure_scroll_region(event=None):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        # Función para ajustar el ancho del frame scrollable
        def configure_canvas_width(event=None):
            canvas_width = self.canvas.winfo_width()
            self.canvas.itemconfig(self.canvas_window, width=canvas_width)
        
        # Bindings para el scroll
        self.scrollable_frame.bind('<Configure>', configure_scroll_region)
        self.canvas.bind('<Configure>', configure_canvas_width)
        
        # Scroll con mouse wheel
        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def bind_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        def unbind_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")
        
        self.canvas.bind('<Enter>', bind_mousewheel)
        self.canvas.bind('<Leave>', unbind_mousewheel)
        
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
            # **MOSTRAR CON EL MISMO PADDING QUE OTROS FRAMES**
            if not self.salida_container.winfo_ismapped():
                # Encontrar el contenedor del botón agregar
                btn_container = None
                for child in self.scrollable_frame.winfo_children():
                    if hasattr(child, 'winfo_children'):
                        for subchild in child.winfo_children():
                            if hasattr(subchild, 'winfo_children'):
                                for btn in subchild.winfo_children():
                                    if hasattr(btn, 'cget') and btn.cget('text') == '➕ Agregar Movimiento':
                                        btn_container = child
                                        break
                
                # Empaquetar con el mismo padding que otros frames
                if btn_container:
                    self.salida_container.pack(fill="x", padx=15, pady=5, before=btn_container)  # ← MISMO PADDING
                else:
                    self.salida_container.pack(fill="x", padx=15, pady=5)

            # Mostrar el frame dentro del contenedor
            if not self.frame_salida_nivel_inferior.winfo_ismapped():
                self.frame_salida_nivel_inferior.pack(fill="x", padx=8, pady=5)  # ← MISMO PADDING

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
            # Ocultar el frame
            self.salida_container.pack_forget()
            self.salida_distrito_var.set('')
            self.salida_tipo_servicio_var.set('')
            self.salida_servicio_var.set('')
            
            # **ACTUALIZAR LAYOUT DESPUÉS DE OCULTAR**
            self.parent.after_idle(self.update_layout)
            
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

        # Tamaño inicial amplio para que se vean bien los widgets con los anchos que tienes
        ancho_ventana = 1100
        alto_ventana = 450

        # Obtener dimensiones de pantalla para centrar
        screen_width = editar_ventana.winfo_screenwidth()
        screen_height = editar_ventana.winfo_screenheight()

        x = (screen_width // 2) - (ancho_ventana // 2)
        y = (screen_height // 2) - (alto_ventana // 2)

        editar_ventana.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")
        editar_ventana.resizable(True, True)

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
        edit_nivel_bodega_var = tk.StringVar(value="area")  # Default, luego se ajusta
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

        PADDING = 10

        main_frame = ttk.Frame(editar_ventana, padding=PADDING)
        main_frame.pack(fill="both", expand=True)

        # Frame Nivel de Bodega (radio buttons)
        frame_nivel_bodega = ttk.LabelFrame(main_frame, text="Nivel de Bodega")
        frame_nivel_bodega.pack(fill="x", pady=5)

        rb_area = ttk.Radiobutton(frame_nivel_bodega, text="Área", variable=edit_nivel_bodega_var, value="area")
        rb_distrito = ttk.Radiobutton(frame_nivel_bodega, text="Distrito", variable=edit_nivel_bodega_var, value="distrito")
        rb_servicio = ttk.Radiobutton(frame_nivel_bodega, text="Servicio", variable=edit_nivel_bodega_var, value="servicio")

        rb_area.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        rb_distrito.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        rb_servicio.grid(row=0, column=2, padx=10, pady=5, sticky="w")

        # Frame Servicios (Área, Distrito, Tipo Servicio, Servicio)
        frame_servicios = ttk.LabelFrame(main_frame, text="Servicios")
        frame_servicios.pack(fill="x", pady=PADDING)

        # Configurar columnas sin expansión para que no se estiren
        for col in range(8):
            frame_servicios.columnconfigure(col, weight=1)

        ttk.Label(frame_servicios, text="Área:", width=15, anchor="w").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        area_cb = AutocompleteCombobox(frame_servicios, textvariable=edit_area_var, width=25, state="normal")
        area_cb.set_completion_list([a['nombre'] for a in obtener_areas() or []])
        area_cb.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_servicios, text="Distrito:", width=15, anchor="w").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        distrito_cb = AutocompleteCombobox(frame_servicios, textvariable=edit_distrito_var, width=25, state="normal")
        distrito_cb.set_completion_list([d['nombre'] for d in obtener_distritos() or []])
        distrito_cb.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_servicios, text="Tipo de Servicio:", width=15, anchor="w").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        tipo_servicio_cb = AutocompleteCombobox(frame_servicios, textvariable=edit_tipo_servicio_var, width=25, state="normal")
        tipo_servicio_cb.grid(row=0, column=5, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_servicios, text="Servicio:", width=15, anchor="w").grid(row=0, column=6, padx=5, pady=5, sticky="w")
        servicio_cb = AutocompleteCombobox(frame_servicios, textvariable=edit_servicio_var, width=25, state="normal")
        servicio_cb.grid(row=0, column=7, padx=5, pady=5, sticky="ew")

        # Frame Insumos
        frame_insumos = ttk.LabelFrame(main_frame, text="Insumos")
        frame_insumos.pack(fill="x", pady=5)

        for col in range(6):
            frame_insumos.columnconfigure(col, weight=1)

        ttk.Label(frame_insumos, text="Tipo de Insumo:", width=15, anchor="w").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        tipo_insumo_cb = AutocompleteCombobox(frame_insumos, textvariable=edit_tipo_insumo_var, width=25, state="normal")
        tipo_insumo_cb.set_completion_list([ti['descripcion'] for ti in obtener_tipos_insumo() or []])
        tipo_insumo_cb.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_insumos, text="Insumo:", width=15, anchor="w").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        insumo_cb = AutocompleteCombobox(frame_insumos, textvariable=edit_insumo_var, width=25, state="normal")
        insumo_cb.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_insumos, text="Presentación:", width=15, anchor="w").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        presentacion_cb = AutocompleteCombobox(frame_insumos, textvariable=edit_presentacion_var, width=25, state="normal")
        presentacion_cb.grid(row=0, column=5, padx=5, pady=5, sticky="ew")

        # Frame Detalles del Movimiento
        frame_detalles = ttk.LabelFrame(main_frame, text="Detalles del Movimiento")
        frame_detalles.pack(fill="x", pady=5)

        for col in range(6):
            frame_detalles.columnconfigure(col, weight=1)

        ttk.Label(frame_detalles, text="Fecha de Registro:", width=15, anchor="w").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        fecha_edit = DateEntry(frame_detalles, width=25, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        fecha_edit.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_detalles, text="Referencia:", width=15, anchor="w").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        referencia_entry = ttk.Entry(frame_detalles, width=27)
        referencia_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_detalles, text="Tipo Movimiento:", width=15, anchor="w").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        tipo_mov_cb = AutocompleteCombobox(frame_detalles, textvariable=edit_tipo_movimiento_var, width=25, state="normal")
        tipo_mov_cb.set_completion_list([tm['descripcion'] for tm in obtener_tipos_movimiento() or []])
        tipo_mov_cb.grid(row=0, column=5, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_detalles, text="Lote:", width=15, anchor="w").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        lote_frame = ttk.Frame(frame_detalles)
        lote_frame.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        lote_entry = ttk.Entry(lote_frame, width=20)
        lote_entry.pack(side="left", fill="x", expand=True)
        edit_check_sin_lote = ttk.Checkbutton(lote_frame, text="Sin\nlote", variable=edit_sin_lote_var, command=toggle_lote_edit)
        edit_check_sin_lote.pack(side="right", padx=(5, 0))

        ttk.Label(frame_detalles, text="Fecha\nVencimiento:", width=15, anchor="w").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        fecha_venc_frame = ttk.Frame(frame_detalles)
        fecha_venc_frame.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
        fecha_venc_edit = DateEntry(fecha_venc_frame, width=15, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        fecha_venc_edit.pack(side="left")
        edit_check_sin_fecha = ttk.Checkbutton(fecha_venc_frame, text="Sin fecha\nvencimiento", variable=edit_sin_fecha_venc, command=toggle_fecha_venc_edit)
        edit_check_sin_fecha.pack(side="right", padx=(5, 0))

        ttk.Label(frame_detalles, text="Cantidad:", width=15, anchor="w").grid(row=1, column=4, padx=5, pady=5, sticky="w")
        cantidad_entry = ttk.Entry(frame_detalles, width=27)
        cantidad_entry.grid(row=1, column=5, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_detalles, text="Observaciones:", width=15, anchor="w").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        observaciones_entry = ttk.Entry(frame_detalles, width=80)
        observaciones_entry.grid(row=2, column=1, columnspan=5, padx=5, pady=5, sticky="ew")

        # Frame Salida Nivel Inferior
        frame_salida_nivel_inferior_edit = ttk.LabelFrame(main_frame, text="Salida Nivel Inferior")

        ttk.Label(frame_salida_nivel_inferior_edit, text="Distrito:", width=15, anchor="w").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        salida_distrito_cb = AutocompleteCombobox(frame_salida_nivel_inferior_edit, textvariable=edit_salida_distrito_var, width=25, completevalues=[d['nombre'] for d in obtener_distritos() or []], state="disabled")
        salida_distrito_cb.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_salida_nivel_inferior_edit, text="Tipo de Servicio:", width=15, anchor="w").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        salida_tipo_servicio_cb = AutocompleteCombobox(frame_salida_nivel_inferior_edit, textvariable=edit_salida_tipo_servicio_var, width=25, completevalues=[], state="disabled")
        salida_tipo_servicio_cb.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_salida_nivel_inferior_edit, text="Servicio:", width=15, anchor="w").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        salida_servicio_cb = AutocompleteCombobox(frame_salida_nivel_inferior_edit, textvariable=edit_salida_servicio_var, width=25, completevalues=[], state="disabled")
        salida_servicio_cb.grid(row=0, column=5, padx=5, pady=5, sticky="ew")

        # 1. Funciones de actualización de estado de la UI
        
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

            # Si el nivel es "distrito", llenar el combobox de distrito en "Salida Nivel Inferior" al inicio
            if nivel == "distrito" and edit_tipo_movimiento_var.get().strip().upper() == "SALIDA NIVEL INFERIOR":
                edit_salida_distrito_var.set(edit_distrito_var.get())
                actualizar_tipos_servicio_salida_edit()
        
        def actualizar_estado_salida_nivel_inferior_edit(*args):
            tipo_mov = edit_tipo_movimiento_var.get().strip().upper()
            nivel = edit_nivel_bodega_var.get()

            if tipo_mov == "SALIDA NIVEL INFERIOR":
                if not frame_salida_nivel_inferior_edit.winfo_ismapped():
                    try:
                        frame_salida_nivel_inferior_edit.pack(fill="x", pady=5, before=frame_botones)
                    except NameError:
                        frame_salida_nivel_inferior_edit.pack(fill="x", pady=5)

                if nivel == "area":
                    salida_distrito_cb.config(state="normal")
                    salida_tipo_servicio_cb.config(state="disabled")
                    salida_servicio_cb.config(state="disabled")
                elif nivel == "distrito":
                    # Llenar el combobox de distrito y bloquearlo
                    edit_salida_distrito_var.set(edit_distrito_var.get())
                    salida_distrito_cb.config(state="disabled")  # Bloquear el combobox
                    salida_distrito_cb.set_completion_list([edit_distrito_var.get()])  # Limitar las opciones solo al distrito seleccionado

                    salida_tipo_servicio_cb.config(state="normal")
                    salida_servicio_cb.config(state="normal")
                    actualizar_tipos_servicio_salida_edit()
                else:
                    salida_distrito_cb.config(state="disabled")
                    salida_tipo_servicio_cb.config(state="disabled")
                    salida_servicio_cb.config(state="disabled")

                editar_ventana.update_idletasks()
                ajustar_tamano_ventana_editar(True)
            else:
                frame_salida_nivel_inferior_edit.pack_forget()
                edit_salida_distrito_var.set('')
                edit_salida_tipo_servicio_var.set('')
                edit_salida_servicio_var.set('')
                editar_ventana.update_idletasks()
                ajustar_tamano_ventana_editar(False)
                
        def ajustar_tamano_ventana_editar(mostrar_salida):
            ancho_base = 1000
            alto_base = 450

            editar_ventana.update_idletasks()
            altura_frame = frame_salida_nivel_inferior_edit.winfo_reqheight() + 50  # margen extra

            if mostrar_salida:
                nuevo_alto = alto_base + altura_frame
            else:
                nuevo_alto = alto_base

            screen_width = editar_ventana.winfo_screenwidth()
            screen_height = editar_ventana.winfo_screenheight()

            x = max(0, (screen_width - ancho_base) // 2)
            y = max(0, (screen_height - nuevo_alto) // 2)

            editar_ventana.geometry(f"{ancho_base}x{nuevo_alto}+{x}+{y}")

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
        
        # 2. Funciones de actualización de datos de los combobox
        
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
        
        # 3. Funciones de carga y guardado
        
        def cargar_datos_iniciales():
        # Determinar nivel de bodega basado en los datos del movimiento
            area_valor = valores[13] if len(valores) > 13 else ''
            distrito_valor = valores[14] if len(valores) > 14 else ''
            tipo_servicio_valor = valores[15] if len(valores) > 15 else ''
            servicio_valor = valores[5]
            
            # Determinar nivel de bodega
            if servicio_valor and tipo_servicio_valor and distrito_valor:
                edit_nivel_bodega_var.set("servicio")
            elif distrito_valor and not servicio_valor:
                edit_nivel_bodega_var.set("distrito")
            else:
                edit_nivel_bodega_var.set("area")

            actualizar_estado_comboboxes_edit()
            
            # Cargar valores DESDE EL TREEVIEW, no desde las variables principales
            edit_area_var.set(area_valor)
            edit_distrito_var.set(distrito_valor)
            edit_tipo_servicio_var.set(tipo_servicio_valor)
            edit_servicio_var.set(servicio_valor)
            edit_tipo_insumo_var.set(valores[12])  # tipo_insumo desde treeview
            edit_insumo_var.set(valores[3])
            edit_presentacion_var.set(valores[4])
            
            # Resto del código igual...
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

            # Salida nivel inferior
            edit_salida_distrito_var.set(valores[9] if valores[9] else '')
            edit_salida_servicio_var.set(valores[10] if valores[10] else '')

            # Actualizar estado final
            actualizar_estado_salida_nivel_inferior_edit()
        
        editar_ventana.after(100, cargar_datos_iniciales)
        
        frame_salida_nivel_inferior_edit.pack(fill="x", pady=5)

        # Botones Guardar y Cerrar
        frame_botones = ttk.Frame(main_frame)
        frame_botones.pack(pady=20)
        
        # Crear un frame interno para centrar los botones
        botones_inner = ttk.Frame(frame_botones)
        botones_inner.pack(anchor="center")
        
        def guardar_cambios():
            try:
                lote_val = "N/A" if edit_sin_lote_var.get() else lote_entry.get().upper()
                nuevos_valores = (
                    fecha_edit.get_date().strftime('%d/%m/%Y'),    # 0
                    referencia_entry.get().upper(),                # 1
                    edit_tipo_movimiento_var.get(),                # 2
                    edit_insumo_var.get(),                         # 3
                    edit_presentacion_var.get(),                   # 4
                    edit_servicio_var.get(),                       # 5
                    lote_val,                                      # 6
                    "N/A" if edit_sin_fecha_venc.get() else fecha_venc_edit.get_date().strftime('%d/%m/%Y'), # 7
                    cantidad_entry.get(),                          # 8
                    edit_salida_distrito_var.get(),                # 9
                    edit_salida_servicio_var.get(),                # 10
                    observaciones_entry.get().upper(),             # 11
                    edit_tipo_insumo_var.get(),                    # 12
                    edit_area_var.get(),                           # 13
                    edit_distrito_var.get(),                       # 14 
                    edit_tipo_servicio_var.get()                   # 15 
                )

                if not all(nuevos_valores[:8]):
                    messagebox.showerror("Error", "Todos los campos son requeridos excepto observaciones")
                    return

                try:
                    float(nuevos_valores[8])
                except ValueError:
                    messagebox.showerror("Error", "La cantidad debe ser un número válido")
                    return

                self.tree.item(selected_item, values=nuevos_valores)
                editar_ventana.destroy()
                messagebox.showinfo("Éxito", "Movimiento actualizado correctamente")
            except Exception as e:
                messagebox.showerror("Error", f"Error al actualizar movimiento: {str(e)}")

        ttk.Button(botones_inner, text="Guardar", command=guardar_cambios, width=15).pack(side="left", padx=10)
        ttk.Button(botones_inner, text="Cerrar", command=editar_ventana.destroy, width=15).pack(side="left", padx=10)        

        # Bindings
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
    
    # 6. Métodos de utilidad
    
    def limpiar_campos(self):
        self.area_var.set('')
        self.distrito_var.set('')
        self.tipo_servicio_var.set('')
        self.servicio_var.set('')
        self.tipo_insumo_var.set('')
        self.insumo_var.set('')
        self.presentacion_var.set('')
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
        
        # Resetear Sin lote
        self.sin_lote_var.set(False)
        self.lote_entry.config(state='normal')

        # Actualizar estados de los combobox
        self.actualizar_estado_comboboxes()

        # Ocultar frame de salida nivel inferior si está visible
        if self.frame_salida_nivel_inferior.winfo_ismapped():
            self.frame_salida_nivel_inferior.pack_forget()
    
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
            for widget in self.parent.winfo_children():
                widget.destroy()
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