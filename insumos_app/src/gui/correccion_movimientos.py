# Imports existentes
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import pandas as pd
from datetime import datetime
import sys
import os
from ttkwidgets.autocomplete import AutocompleteCombobox

# Agregar el directorio raíz del proyecto al PATH de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.db_manager import (
    obtener_areas,
    obtener_distritos,
    obtener_tipos_servicio_por_distrito,
    obtener_servicios_por_tipo,
    obtener_tipos_insumo,
    obtener_insumos_por_tipo,
    obtener_presentaciones,
    buscar_movimientos_por_filtros,
    obtener_tipos_movimiento
)

class CorreccionMovimientos:
    # Definir las columnas como atributo de la clase
    COLUMNAS = [
        'ID', 'Fecha', 'Área', 'Distrito', 'Tipo de Servicio', 'Referencia', 'Servicio',
        'Tipo de Movimiento', 'Lote', 'Fecha Vencimiento', 'Cantidad', 'Insumo',
        'Distrito Salida', 'Servicio Salida', 'Observaciones'
    ]

    def formato_float(self, valor):
        try:
            return f"{float(valor):.2f}"
        except (ValueError, TypeError):
            return ""

    def __init__(self, parent_frame, main_window=None):
        self.parent = parent_frame
        self.main_window = main_window
        self.setup_styles()
        self.cargar_iconos()  # Carga los iconos PNG aquí
        self.movimientos_data = None

        # Crear estilos para los frames
        style = ttk.Style()
        style.configure('Enabled.TFrame', background='white')
        style.configure('Disabled.TFrame', background='#f0f0f0')

        self.areas = []
        self.distritos = []
        self.tipos_servicio = []
        self.tipos_insumo = []
        self.insumos = []
        self.presentaciones = []
        self.tipos_movimiento = []

        self.setup_ui()

    def cargar_iconos(self):
        try:
            base_dir = os.path.dirname(os.path.dirname(__file__))  # Sube un nivel: de gui/ a src/
            icons_path = os.path.join(base_dir, "utils", "icons")
            
            # Ajusta la ruta según tu proyecto
            self.icon_editar = tk.PhotoImage(file=os.path.join(icons_path, "editar.png")).subsample(2, 2)
            self.icon_eliminar = tk.PhotoImage(file=os.path.join(icons_path, "eliminar.png")).subsample(2, 2)
            self.icon_cerrar = tk.PhotoImage(file=os.path.join(icons_path, "cerrar.png")).subsample(2, 2)
        except Exception as e:
            print(f"Error cargando iconos: {e}")
            self.icon_editar = None
            self.icon_eliminar = None
            self.icon_cerrar = None

    def create_titled_frame(self, parent, title):
        container = tk.Frame(parent, bg=self.COLORS['white'], relief='solid', borderwidth=1)
        container.pack(fill='x', padx=10, pady=5)

        header = tk.Frame(container, bg=self.COLORS['primary'], height=25)
        header.pack(fill='x')
        header.pack_propagate(False)

        label = tk.Label(header, text=title, font=('Segoe UI', 9, 'bold'),
                        fg=self.COLORS['white'], bg=self.COLORS['primary'])
        label.pack(side='left', padx=10, pady=3)

        content = tk.Frame(container, bg=self.COLORS['white'])
        content.pack(fill='both', expand=True, padx=10, pady=10)

        return container, content

    def setup_styles(self):
        self.COLORS = {
            'primary': '#2E86AB',
            'secondary': '#A23B72',
            'success': '#27AE60',
            'warning': '#F39C12',
            'danger': '#E74C3C',
            'accent': '#8E44AD',
            'light': '#F8F9FA',
            'white': '#FFFFFF',
            'text_dark': '#2C3E50',
            'text_light': '#7F8C8D',
            'border': '#BDC3C7'
        }

        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('White.TFrame', background=self.COLORS['white'])
        
        # Estilo para labels con fondo blanco
        style.configure('White.TLabel',
            background=self.COLORS['white'],
            foreground=self.COLORS['text_dark'],
            font=('Segoe UI', 9))

        # Estilo para botones con fondo blanco
        style.configure('White.TButton',
            background=self.COLORS['white'],
            foreground=self.COLORS['text_dark'],
            font=('Segoe UI', 9),
            relief='flat',
            borderwidth=0)
        style.map('White.TButton',
            background=[('active', self.COLORS['light']),
                        ('pressed', self.COLORS['light'])])
        
        style.configure('Card.TLabelframe',
            background=self.COLORS['white'],
            relief='solid',
            borderwidth=1,
            labeloutside=False)

        style.configure('Card.TLabelframe.Label',
            background=self.COLORS['primary'],
            foreground=self.COLORS['light'],
            font=('Segoe UI', 9, 'bold'),
            padding=(8, 3))

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

        style.configure('Title.TLabel',
            font=('Segoe UI', 14, 'bold'),
            background=self.COLORS['white'],
            foreground=self.COLORS['primary'])

        style.configure('Subtitle.TLabel',
            font=('Segoe UI', 9),
            background=self.COLORS['white'],
            foreground=self.COLORS['text_light'])

        style.configure("Custom.Treeview",
            background=self.COLORS['white'],
            foreground=self.COLORS['text_dark'],
            rowheight=25,
            fieldbackground=self.COLORS['white'],
            font=('Segoe UI', 8),
            borderwidth=1,
            relief='solid')

        style.configure("Custom.Treeview.Heading",
            background=self.COLORS['primary'],
            foreground='white',
            font=('Segoe UI', 9, 'bold'),
            relief='raised',
            borderwidth=1)

    def setup_ui(self):
        # --- Título principal ---
        title_frame = tk.Frame(self.parent, bg=self.COLORS['primary'], height=70)
        title_frame.pack(fill='x', padx=0, pady=(10, 5))
        title_frame.pack_propagate(False)

        title_inner = tk.Frame(title_frame, bg=self.COLORS['primary'])
        title_inner.pack(fill='both', expand=True, padx=15, pady=8)

        tk.Label(title_inner,
                text="Correcciones Movimientos de Insumos",
                font=('Segoe UI', 12, 'bold'),
                fg=self.COLORS['white'],
                bg=self.COLORS['primary']).pack(anchor='w')

        tk.Label(title_inner,
                text="Corrija los movimientos de los insumos",
                font=('Segoe UI', 8),
                fg=self.COLORS['white'],
                bg=self.COLORS['primary']).pack(anchor='w', pady=(2, 0))

        # Separador
        ttk.Separator(self.parent, orient='horizontal').pack(fill='x', padx=10, pady=5)

        # Frame principal con título personalizado
        self.frame_principal_container, self.frame_principal = self.create_titled_frame(self.parent, "Filtros de Búsqueda")
        self.frame_principal_container.config(bg=self.COLORS['white'])
        self.frame_principal.config(bg=self.COLORS['white'])
        self.frame_principal_container.pack(fill="x", expand=False, padx=10, pady=5)
        self.frame_principal_container.config(width=900)

        # Frame para fechas con título personalizado
        self.frame_fechas_container, self.frame_fechas = self.create_titled_frame(self.frame_principal, "Selección de Fechas")
        self.frame_fechas_container.config(bg=self.COLORS['white'])
        self.frame_fechas.config(bg=self.COLORS['white'])
        self.frame_fechas_container.pack(fill="x", expand=False, padx=5, pady=5)
        self.frame_fechas_container.config(width=900)

        # Frame para rango de fechas
        self.frame_rango = ttk.Frame(self.frame_fechas, style='White.TFrame')
        self.frame_rango.pack(fill="x", padx=5, pady=2)

        ttk.Label(self.frame_rango, text="Fecha Inicial:", style='White.TLabel').grid(row=0, column=0, padx=5)
        self.fecha_inicial = DateEntry(
            self.frame_rango,
            width=12,
            date_pattern='dd/mm/yyyy',
            state='normal'
        )
        self.fecha_inicial.grid(row=0, column=1, padx=5)

        ttk.Label(self.frame_rango, text="Fecha Final:", style='White.TLabel').grid(row=0, column=2, padx=5)
        self.fecha_final = DateEntry(
            self.frame_rango,
            width=12,
            date_pattern='dd/mm/yyyy',
            state='normal'
        )
        self.fecha_final.grid(row=0, column=3, padx=5)

        # Frame para combos
        self.frame_combos = ttk.Frame(self.frame_principal, style='White.TFrame')
        self.frame_combos.pack(fill="x", expand=False, padx=5, pady=5)
        self.frame_combos.config(width=900)

        # Primera fila de combos con título personalizado
        self.frame_combos1_container, self.frame_combos1 = self.create_titled_frame(self.frame_combos, "Selección de Ubicación")
        self.frame_combos1_container.config(bg=self.COLORS['white'])
        self.frame_combos1.config(bg=self.COLORS['white'])
        self.frame_combos1_container.pack(fill="x", expand=False, pady=5)
        self.frame_combos1_container.config(width=900)

        label_style = {'style': 'White.TLabel'}
        ttk.Label(self.frame_combos1, text="Área:", **label_style).grid(row=0, column=0, padx=5, sticky='w')
        self.area_var = tk.StringVar()
        self.combo_area = AutocompleteCombobox(self.frame_combos1, textvariable=self.area_var, state="normal", width=18, font=('Segoe UI', 9))
        self.combo_area.grid(row=0, column=1, padx=5, sticky='w')

        ttk.Label(self.frame_combos1, text="Distrito:", **label_style).grid(row=0, column=2, padx=5, sticky='w')
        self.distrito_var = tk.StringVar()
        self.combo_distrito = AutocompleteCombobox(self.frame_combos1, textvariable=self.distrito_var, state="normal", width=18, font=('Segoe UI', 9))
        self.combo_distrito.grid(row=0, column=3, padx=5, sticky='w')

        ttk.Label(self.frame_combos1, text="Tipo de Servicio:", **label_style).grid(row=0, column=4, padx=5, sticky='w')
        self.tipo_servicio_var = tk.StringVar()
        self.combo_tipo_servicio = AutocompleteCombobox(self.frame_combos1, textvariable=self.tipo_servicio_var, state="normal", width=18, font=('Segoe UI', 9))
        self.combo_tipo_servicio.grid(row=0, column=5, padx=5, sticky='w')

        ttk.Label(self.frame_combos1, text="Servicio:", **label_style).grid(row=0, column=6, padx=5, sticky='w')
        self.servicio_var = tk.StringVar()
        self.combo_servicio = AutocompleteCombobox(self.frame_combos1, textvariable=self.servicio_var, state="normal", width=18, font=('Segoe UI', 9))
        self.combo_servicio.grid(row=0, column=7, padx=5, sticky='w')

        # Segunda fila de combos con título personalizado
        self.frame_combos2_container, self.frame_combos2 = self.create_titled_frame(self.frame_combos, "Selección de Insumos / Tipo Movimiento")
        self.frame_combos2_container.config(bg=self.COLORS['white'])
        self.frame_combos2.config(bg=self.COLORS['white'])
        self.frame_combos2_container.pack(fill="x", expand=False, pady=5)
        self.frame_combos2_container.config(width=900)

        ttk.Label(self.frame_combos2, text="Tipo\nInsumo:", **label_style).grid(row=0, column=0, padx=5, sticky='w')
        self.tipo_insumo_var = tk.StringVar()
        self.combo_tipo_insumo = AutocompleteCombobox(self.frame_combos2, textvariable=self.tipo_insumo_var, state="normal", width=18, font=('Segoe UI', 9))
        self.combo_tipo_insumo.grid(row=0, column=1, padx=5, sticky='w')

        ttk.Label(self.frame_combos2, text="Insumo:", **label_style).grid(row=0, column=2, padx=5, sticky='w')
        self.insumo_var = tk.StringVar()
        self.combo_insumo = AutocompleteCombobox(self.frame_combos2, textvariable=self.insumo_var, state="normal", width=18, font=('Segoe UI', 9))
        self.combo_insumo.grid(row=0, column=3, padx=5, sticky='w')

        ttk.Label(self.frame_combos2, text="Presentación:", **label_style).grid(row=0, column=4, padx=5, sticky='w')
        self.presentacion_var = tk.StringVar()
        self.combo_presentacion = AutocompleteCombobox(self.frame_combos2, textvariable=self.presentacion_var, state="normal", width=18, font=('Segoe UI', 9))
        self.combo_presentacion.grid(row=0, column=5, padx=5, sticky='w')

        ttk.Label(self.frame_combos2, text="Tipo\nMovimiento:", **label_style).grid(row=0, column=6, padx=5, sticky='w')
        self.tipo_movimiento_var = tk.StringVar()
        self.combo_tipo_movimiento = AutocompleteCombobox(self.frame_combos2, textvariable=self.tipo_movimiento_var, state="normal", width=18, font=('Segoe UI', 9))
        self.combo_tipo_movimiento.grid(row=0, column=7, padx=5, sticky='w')

        # Frame para botones de búsqueda
        self.frame_botones_busqueda = ttk.Frame(self.frame_principal)
        self.frame_botones_busqueda.pack(fill="x", pady=5)

        btn_style = 'Primary.TButton'
        ttk.Button(self.frame_botones_busqueda, text="🔍 Buscar Movimientos", style=btn_style, command=self.buscar_movimientos).pack(side="left", padx=5)
        ttk.Button(self.frame_botones_busqueda, text="🧹 Limpiar Filtros", style=btn_style, command=self.limpiar_filtros).pack(side="left", padx=5)

        # Frame para el Treeview con título personalizado
        self.frame_treeview_container, self.frame_treeview = self.create_titled_frame(self.frame_principal, "Resultados")
        self.frame_treeview_container.pack(fill="x", expand=False, padx=5, pady=5)
        self.frame_treeview_container.config(width=900)

        # Frame para Treeview compacto
        self.tree_frame = tk.Frame(self.frame_treeview, bg=self.COLORS['white'], relief='solid', borderwidth=1)
        self.tree_frame.pack(fill="x", expand=False, padx=5, pady=5)
        self.tree_frame.pack_propagate(True)
        self.tree_frame.config(height=5 * 25 + 30)  # 5 filas * rowheight + espacio encabezado

        style = ttk.Style()
        style.configure("Custom.Treeview.Heading",
                        font=("Segoe UI", 9, "bold"),
                        background=self.COLORS['primary'],
                        foreground='white')
        style.configure("Custom.Treeview",
                        font=("Segoe UI", 9),
                        rowheight=25,
                        background=self.COLORS['white'],
                        foreground=self.COLORS['text_dark'],
                        fieldbackground=self.COLORS['white'])

        # Scrollbars para el Treeview
        self.tree_scroll_y = ttk.Scrollbar(self.tree_frame)
        self.tree_scroll_y.pack(side="right", fill="y")

        self.tree_scroll_x = ttk.Scrollbar(self.tree_frame, orient="horizontal")
        self.tree_scroll_x.pack(side="bottom", fill="x")

        # Crear Treeview con altura 5 filas
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=self.COLUMNAS,
            show="headings",
            yscrollcommand=self.tree_scroll_y.set,
            xscrollcommand=self.tree_scroll_x.set,
            style="Custom.Treeview",
            height=8  # Aquí la reducción a 5 filas visibles
        )

        # Configurar encabezados y columnas (igual que antes)
        encabezados = {
            'ID': 'ID',
            'Fecha': 'FECHA',
            'Área': 'ÁREA',
            'Distrito': 'DISTRITO',
            'Tipo de Servicio': 'TIPO SERVICIO',
            'Referencia': 'REFERENCIA',
            'Servicio': 'SERVICIO',
            'Tipo de Movimiento': 'TIPO MOVIMIENTO',
            'Lote': 'LOTE',
            'Fecha Vencimiento': 'FECHA VENCIMIENTO',
            'Cantidad': 'CANTIDAD',
            'Insumo': 'INSUMO',
            'Distrito Salida': 'DISTRITO SALIDA',
            'Servicio Salida': 'SERVICIO SALIDA',
            'Observaciones': 'OBSERVACIONES'
        }

        for col in self.COLUMNAS:
            self.tree.heading(col, text=encabezados[col])
            if col == "Área":
                width = 120
            elif col == "Distrito":
                width = 120
            elif col == "Tipo de Servicio":
                width = 150
            elif col == "Referencia":
                width = 120
            elif col == "Observaciones":
                width = 250
            elif col == "Tipo de Movimiento":
                width = 180
            elif col == "Fecha Vencimiento":
                width = 150
            elif col in ["Servicio", "Insumo"]:
                width = 160
            elif col in ["Distrito Salida", "Servicio Salida"]:
                width = 140
            elif col == "Cantidad":
                width = 120
            elif col == "Fecha":
                width = 110
            elif col == "Lote":
                width = 100
            else:
                width = 100

            if col in ["Cantidad", "Fecha", "Fecha Vencimiento"]:
                self.tree.column(col, width=width, anchor='center')
            else:
                self.tree.column(col, width=width, anchor='w')

        self.tree.column("ID", width=0, stretch=False)
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree_scroll_y.config(command=self.tree.yview)
        self.tree_scroll_x.config(command=self.tree.xview)

        # Frame para botones de acción
        self.frame_botones_accion = tk.Frame(self.frame_principal, bg=self.COLORS['white'])
        self.frame_botones_accion.pack(fill="x", pady=10)

        btn_padx = 10
        btn_pady = 6
        btn_font = ('Segoe UI', 9, 'bold')
        btn_bg = self.COLORS['white']
        btn_fg = self.COLORS['text_dark']

        self.btn_editar = tk.Button(self.frame_botones_accion,
            text="Editar",
            image=self.icon_editar,
            compound='left',
            command=self.editar_movimiento,
            font=btn_font,
            bg=btn_bg,
            fg=btn_fg,
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            padx=25,
            pady=btn_pady,
            cursor='hand2')
        self.btn_editar.pack(side="left", padx=btn_padx)

        self.btn_eliminar = tk.Button(self.frame_botones_accion,
            text="Eliminar",
            image=self.icon_eliminar,
            compound='left',
            command=self.eliminar_movimiento,
            font=btn_font,
            bg=btn_bg,
            fg=btn_fg,
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            padx=25,
            pady=btn_pady,
            cursor='hand2')
        self.btn_eliminar.pack(side="left", padx=btn_padx)

        self.btn_cerrar = tk.Button(self.frame_botones_accion,
            text="Cerrar",
            image=self.icon_cerrar,
            compound='left',
            command=self.cerrar_ventana,
            font=btn_font,
            bg=btn_bg,
            fg=btn_fg,
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            padx=25,
            pady=btn_pady,
            cursor='hand2')
        self.btn_cerrar.pack(side="right", padx=btn_padx)

        # Vincular eventos de cambio
        self.combo_area.bind('<<ComboboxSelected>>', self.cargar_distritos_por_area)
        self.combo_distrito.bind('<<ComboboxSelected>>', self.cargar_tipos_servicio)
        self.combo_tipo_servicio.bind('<<ComboboxSelected>>', self.cargar_servicios)
        self.combo_tipo_insumo.bind('<<ComboboxSelected>>', self.cargar_insumos)
        self.combo_insumo.bind('<<ComboboxSelected>>', self.actualizar_presentacion)

        # Cargar datos iniciales
        self.cargar_areas()
        self.distritos = []
        self.combo_distrito.set_completion_list([''])
        self.cargar_tipos_insumo()
        self.cargar_presentaciones()
        self.cargar_tipos_movimiento()

    def cargar_areas(self):
        self.areas = obtener_areas()
        if self.areas:
            opciones = [''] + [a['nombre'] for a in self.areas]
            self.combo_area.set_completion_list(opciones)

    def cargar_distritos(self):
        self.distritos = obtener_distritos()
        if self.distritos:
            opciones = [''] + [d['nombre'] for d in self.distritos]
            self.combo_distrito.set_completion_list(opciones)

    def cargar_distritos_por_area(self, event=None):
        area_nombre = self.combo_area.get().strip()
        if area_nombre:
            area = next((a for a in self.areas if a['nombre'] == area_nombre), None)
            if area:
                from src.database.db_manager import obtener_distritos_por_area
                distritos = obtener_distritos_por_area(area['id'])
                self.distritos = distritos or []
                opciones = [''] + [d['nombre'] for d in self.distritos]
                self.combo_distrito.set_completion_list(opciones)
            else:
                self.distritos = []
                self.combo_distrito.set_completion_list([''])
                self.combo_distrito.set('')
        else:
            self.distritos = []
            self.combo_distrito.set_completion_list([''])
            self.combo_distrito.set('')

    def cargar_tipos_servicio(self, event=None):
        self.combo_tipo_servicio.set('')
        distrito_nombre = self.combo_distrito.get().strip()
        if distrito_nombre:
            distrito = next((d for d in self.distritos if d['nombre'] == distrito_nombre), None)
            if distrito:
                self.tipos_servicio = obtener_tipos_servicio_por_distrito(distrito['id'])
                opciones = [''] + [t['descripcion'] for t in self.tipos_servicio]
                self.combo_tipo_servicio.set_completion_list(opciones)

    def cargar_servicios(self, event=None):
        self.combo_servicio.set('')
        tipo_servicio_desc = self.combo_tipo_servicio.get().strip()
        if tipo_servicio_desc:
            tipo_servicio = next((t for t in self.tipos_servicio if t['descripcion'] == tipo_servicio_desc), None)
            if tipo_servicio:
                servicios = obtener_servicios_por_tipo(tipo_servicio['id'])
                opciones = [''] + [s['nombre'] for s in servicios]
                self.combo_servicio.set_completion_list(opciones)

    def cargar_tipos_insumo(self):
        self.tipos_insumo = obtener_tipos_insumo()
        if self.tipos_insumo:
            opciones = [''] + [t['descripcion'] for t in self.tipos_insumo]
            self.combo_tipo_insumo.set_completion_list(opciones)

    def cargar_insumos(self, event=None):
        self.combo_insumo.set('')
        self.combo_presentacion.set('')
        tipo_insumo_desc = self.combo_tipo_insumo.get().strip()
        if tipo_insumo_desc:
            tipo_insumo = next((t for t in self.tipos_insumo if t['descripcion'] == tipo_insumo_desc), None)
            if tipo_insumo:
                self.insumos = obtener_insumos_por_tipo(tipo_insumo['id'])
                opciones = [''] + [i['nombre'] for i in self.insumos]
                self.combo_insumo.set_completion_list(opciones)

    def actualizar_presentacion(self, event=None):
        insumo_nombre = self.combo_insumo.get().strip()
        if insumo_nombre and self.insumos:
            insumo = next((i for i in self.insumos if i['nombre'] == insumo_nombre), None)
            if insumo:
                self.combo_presentacion.set(insumo['nombre_presentacion'] if 'nombre_presentacion' in insumo.keys() else '')
            else:
                self.combo_presentacion.set('')
        else:
            self.combo_presentacion.set('')

    def cargar_presentaciones(self):
        self.presentaciones = obtener_presentaciones()
        if self.presentaciones:
            opciones = [''] + [p['nombre'] for p in self.presentaciones]
            self.combo_presentacion.set_completion_list(opciones)

    def cargar_tipos_movimiento(self):
        self.tipos_movimiento = obtener_tipos_movimiento()
        if self.tipos_movimiento:
            opciones = [''] + [t['descripcion'] for t in self.tipos_movimiento]
            self.combo_tipo_movimiento.set_completion_list(opciones)

    def buscar_movimientos(self):
        try:
            # Validar fechas
            fecha_ini_str = self.fecha_inicial.get()
            fecha_fin_str = self.fecha_final.get()

            if not fecha_ini_str or not fecha_fin_str:
                messagebox.showwarning("Advertencia", "Debe seleccionar fecha inicial y fecha final.")
                return

            fecha_ini = datetime.strptime(fecha_ini_str, '%d/%m/%Y')
            fecha_fin = datetime.strptime(fecha_fin_str, '%d/%m/%Y')

            if fecha_fin < fecha_ini:
                messagebox.showerror("Error", "La fecha final debe ser mayor a la inicial")
                return

            # Validar que al menos un filtro de ubicación, insumo o tipo movimiento esté seleccionado
            filtros_obligatorios = [
                self.combo_area.get().strip(),
                self.combo_distrito.get().strip(),
                self.combo_tipo_servicio.get().strip(),
                self.combo_servicio.get().strip(),
                self.combo_tipo_insumo.get().strip(),
                self.combo_insumo.get().strip(),
                self.combo_presentacion.get().strip(),
                self.combo_tipo_movimiento.get().strip()
            ]

            if not any(filtros_obligatorios):
                messagebox.showwarning(
                    "Advertencia",
                    "Debe seleccionar al menos un filtro de ubicación, insumo o tipo de movimiento."
                )
                return

            # Obtener datos y asignar a self.movimientos_data
            self.movimientos_data = buscar_movimientos_por_filtros(
                fecha_ini.strftime('%Y-%m-%d'),
                fecha_fin.strftime('%Y-%m-%d'),
                self.combo_area.get(),
                self.combo_distrito.get(),
                self.combo_tipo_servicio.get(),
                self.combo_servicio.get(),
                self.combo_tipo_insumo.get(),
                self.combo_insumo.get(),
                self.combo_presentacion.get(),
                self.combo_tipo_movimiento.get()
            )

            if not self.movimientos_data:
                messagebox.showinfo("Info", "No hay datos para mostrar")
                return

            # Limpiar el Treeview
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Llenar el Treeview con los datos
            for mov in self.movimientos_data:
                fecha_venc = mov.get('fecha_vencimiento')
                if fecha_venc is None or fecha_venc == '':
                    fecha_venc = "N/A"
                    
                lote = mov.get('lote')
                if lote is None or lote == '':
                    lote = "N/A"
                    
                self.tree.insert('', 'end', values=(
                    mov.get('id', ''),                          # ID
                    mov.get('fecha', ''),                       # Fecha
                    mov.get('area_nombre', '') or "",           # Área
                    mov.get('distrito_nombre', '') or "",       # Distrito
                    mov.get('tipo_servicio_desc', '') or "",    # Tipo de Servicio
                    mov.get('referencia', '') or "",            # Referencia
                    mov.get('servicio_nombre', '') or "",       # Servicio
                    mov.get('tipo_movimiento', '') or "",       # Tipo de Movimiento
                    lote,                                       # Lote
                    fecha_venc,                                 # Fecha Vencimiento
                    self.formato_float(mov.get('cantidad', 0)), # Cantidad
                    mov.get('insumo_nombre', '') or "",         # Insumo
                    mov.get('distrito_salida', '') or "",       # Distrito Salida
                    mov.get('servicio_salida', '') or "",       # Servicio Salida
                    mov.get('observaciones', '') or ""          # Observaciones
                ))

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error al buscar movimientos:\n{str(e)}\n\nPor favor, verifique los datos e intente nuevamente."
            )

    def limpiar_filtros(self):
        # Restablecer fechas
        self.fecha_inicial.set_date(datetime.now())
        self.fecha_final.set_date(datetime.now())

        # Limpiar combos
        self.combo_area.set('')
        self.combo_distrito.set('')
        self.combo_tipo_servicio.set('')
        self.combo_servicio.set('')
        self.combo_tipo_insumo.set('')
        self.combo_insumo.set('')
        self.combo_presentacion.set('')
        self.combo_tipo_movimiento.set('')

        # Limpiar Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Limpiar datos
        self.movimientos_data = None

    def editar_movimiento(self):
        # Obtener el item seleccionado
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un movimiento para editar")
            return

        # Obtener el ID del movimiento seleccionado (sigue siendo la primera columna)
        item_values = self.tree.item(selected_item[0], 'values')
        movimiento_id = item_values[0]  # ID sigue siendo índice 0

        # Buscar el movimiento en los datos
        movimiento = next((m for m in self.movimientos_data if str(m['id']) == str(movimiento_id)), None)
        if not movimiento:
            messagebox.showerror("Error", "No se pudo encontrar el movimiento seleccionado")
            return

        # Crear ventana de edición
        self.abrir_ventana_edicion(movimiento)

    def abrir_ventana_edicion(self, movimiento):
        # Crear ventana de edición
        edicion_window = tk.Toplevel(self.parent)
        edicion_window.title("Editar Movimiento")
        edicion_window.geometry("600x550")
        edicion_window.grab_set()  # Hacer modal

        # Centrar la ventana
        edicion_window.transient(self.parent)
        edicion_window.update_idletasks()

        # Obtener dimensiones de la pantalla y la ventana
        screen_width = edicion_window.winfo_screenwidth()
        screen_height = edicion_window.winfo_screenheight()
        window_width = 600
        window_height = 550

        # Calcular posición para centrar
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        edicion_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Frame principal con padding
        frame_edicion = ttk.Frame(edicion_window, padding=20)
        frame_edicion.pack(fill="both", expand=True)

        # Título centrado (sin ID)
        titulo_frame = ttk.Frame(frame_edicion)
        titulo_frame.pack(fill="x", pady=(0, 20))

        ttk.Label(titulo_frame, text="Editar Movimiento",
                font=("Arial", 14, "bold")).pack()

        # Frame para los campos con grid
        campos_frame = ttk.Frame(frame_edicion)
        campos_frame.pack(fill="both", expand=True)

        # Configurar columnas para que se expandan uniformemente
        campos_frame.columnconfigure(1, weight=1)

        # Tamaño estándar para todos los campos
        ANCHO_CAMPO = 25

        row = 0

        # Fecha
        ttk.Label(campos_frame, text="Fecha:", font=("Arial", 10)).grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=8
        )
        fecha_entry = DateEntry(
            campos_frame,
            width=ANCHO_CAMPO,
            date_pattern='dd/mm/yyyy',
            font=("Arial", 10)
        )
        fecha_entry.grid(row=row, column=1, sticky="ew", pady=8)
        if movimiento['fecha']:
            try:
                fecha_entry.set_date(datetime.strptime(movimiento['fecha'], '%Y-%m-%d'))
            except:
                pass
        row += 1

        # Referencia
        ttk.Label(campos_frame, text="Referencia:", font=("Arial", 10)).grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=8
        )
        referencia_var = tk.StringVar(value=movimiento.get('referencia', '') or "")
        referencia_entry = ttk.Entry(campos_frame, textvariable=referencia_var,
                                    width=ANCHO_CAMPO, font=("Arial", 10))
        referencia_entry.grid(row=row, column=1, sticky="ew", pady=8)
        row += 1

        # Insumo (solo lectura)
        ttk.Label(campos_frame, text="Insumo:", font=("Arial", 10)).grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=8
        )
        insumo_frame = ttk.Frame(campos_frame)
        insumo_frame.grid(row=row, column=1, sticky="ew", pady=8)
        insumo_frame.columnconfigure(0, weight=1)

        insumo_label = ttk.Label(insumo_frame,
                                text=movimiento.get('insumo_nombre', '') or "",
                                foreground="blue",
                                font=("Arial", 10),
                                relief="sunken",
                                padding=5)
        insumo_label.grid(row=0, column=0, sticky="ew")
        row += 1

        # Tipo de Movimiento
        ttk.Label(campos_frame, text="Tipo de Movimiento:", font=("Arial", 10)).grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=8
        )
        tipo_movimiento_var = tk.StringVar(value=movimiento.get('tipo_movimiento', '') or "")
        tipo_movimiento_combo = ttk.Combobox(campos_frame, textvariable=tipo_movimiento_var,
                                            width=ANCHO_CAMPO, font=("Arial", 10))
        tipo_movimiento_combo['values'] = [t['descripcion'] for t in self.tipos_movimiento] if self.tipos_movimiento else []
        tipo_movimiento_combo.grid(row=row, column=1, sticky="ew", pady=8)
        row += 1

        # Lote
        ttk.Label(campos_frame, text="Lote:", font=("Arial", 10)).grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=8
        )
        lote_var = tk.StringVar(value=movimiento.get('lote', '') or "")
        lote_entry = ttk.Entry(campos_frame, textvariable=lote_var,
                            width=ANCHO_CAMPO, font=("Arial", 10))
        lote_entry.grid(row=row, column=1, sticky="ew", pady=8)

        row += 1
        
        # Checkbox Sin lote
        sin_lote_var = tk.BooleanVar(value=False)

        def toggle_lote():
            if sin_lote_var.get():
                lote_entry.delete(0, 'end')
                lote_entry.config(state='disabled')
            else:
                lote_entry.config(state='normal')

        checkbox_sin_lote = ttk.Checkbutton(
            campos_frame,
            text="Sin lote",
            variable=sin_lote_var,
            command=toggle_lote
        )
        checkbox_sin_lote.grid(row=row, column=1, sticky='nw', padx=5, pady=2)

        # Inicializar checkbox según valor actual
        if not movimiento.get('lote') or movimiento.get('lote') in ("", "N/A", None):
            sin_lote_var.set(True)
            lote_entry.config(state='disabled')
        else:
            sin_lote_var.set(False)
            lote_entry.config(state='normal')

        row += 1

        # Fecha Vencimiento
        ttk.Label(campos_frame, text="Fecha Vencimiento:", font=("Arial", 10)).grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=8
        )
        fecha_venc_entry = DateEntry(
            campos_frame,
            width=ANCHO_CAMPO,
            date_pattern='dd/mm/yyyy',
            font=("Arial", 10)
        )
        fecha_venc_entry.grid(row=row, column=1, sticky="ew", pady=8)
        if movimiento.get('fecha_vencimiento'):
            try:
                fecha_venc_entry.set_date(datetime.strptime(movimiento['fecha_vencimiento'], '%Y-%m-%d'))
            except:
                pass
        row += 1
        
        sin_fecha_var = tk.BooleanVar(value=False)
        def toggle_fecha_venc():
            if sin_fecha_var.get():
                fecha_venc_entry.config(state='disabled')
            else:
                fecha_venc_entry.config(state='normal')

        checkbox_sin_fecha = ttk.Checkbutton(
            campos_frame,
            text="Sin fecha de vencimiento",
            variable=sin_fecha_var,
            command=toggle_fecha_venc
        )
        checkbox_sin_fecha.grid(row=row, column=1, sticky='w', pady=2)
        row += 1

        # Inicializar checkbox según valor actual
        if not movimiento.get('fecha_vencimiento'):
            sin_fecha_var.set(True)
            fecha_venc_entry.config(state='disabled')
        else:
            sin_fecha_var.set(False)
            fecha_venc_entry.config(state='normal')

        # Cantidad
        ttk.Label(campos_frame, text="Cantidad:", font=("Arial", 10)).grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=8
        )
        cantidad_var = tk.StringVar(value=self.formato_float(movimiento.get('cantidad', 0)))
        cantidad_entry = ttk.Entry(campos_frame, textvariable=cantidad_var,
                                width=ANCHO_CAMPO, font=("Arial", 10))
        cantidad_entry.grid(row=row, column=1, sticky="ew", pady=8)
        row += 1

        # Observaciones
        ttk.Label(campos_frame, text="Observaciones:", font=("Arial", 10)).grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=8
        )
        observaciones_var = tk.StringVar(value=movimiento.get('observaciones', '') or "")
        observaciones_entry = ttk.Entry(campos_frame, textvariable=observaciones_var,
                                    width=ANCHO_CAMPO, font=("Arial", 10))
        observaciones_entry.grid(row=row, column=1, sticky="ew", pady=8)
        row += 1

        # Función para guardar cambios
        def guardar_cambios():
            try:
                # Validar datos
                fecha = fecha_entry.get_date().strftime('%Y-%m-%d')
                tipo_movimiento = tipo_movimiento_var.get()

                # Validar campos numéricos
                try:
                    cantidad = float(cantidad_var.get()) if cantidad_var.get() else 0
                except ValueError:
                    messagebox.showerror("Error", "El campo cantidad debe contener un valor numérico válido")
                    return
                
                if sin_fecha_var.get():
                    fecha_vencimiento_val = None
                else:
                    fecha_vencimiento_val = fecha_venc_entry.get_date().strftime('%Y-%m-%d')
                    
                if sin_lote_var.get():
                    lote_val = None  # o "N/A" según cómo manejes en la base
                else:
                    lote_val = lote_var.get().upper()

                # Preparar datos para actualización
                datos_actualizados = {
                    'id': movimiento['id'],
                    'fecha': fecha,
                    'referencia': referencia_var.get(),
                    'tipo_movimiento': tipo_movimiento,
                    'lote': lote_val,
                    'fecha_vencimiento': fecha_vencimiento_val,
                    'cantidad': cantidad,
                    'observaciones': observaciones_var.get()
                }

                # Llamar a la función de actualización en la base de datos
                from src.database.db_manager import actualizar_movimiento
                actualizar_movimiento(datos_actualizados['id'], datos_actualizados)

                messagebox.showinfo("Éxito", "Movimiento actualizado correctamente")
                edicion_window.destroy()

                # Actualizar la vista
                self.buscar_movimientos()

            except Exception as e:
                messagebox.showerror("Error", f"Error al actualizar movimiento: {str(e)}")

        # Frame para botones centrado
        frame_botones = ttk.Frame(frame_edicion)
        frame_botones.pack(pady=20)

        # Botones con estilo uniforme
        btn_guardar = ttk.Button(frame_botones, text="Modificar",
                                command=guardar_cambios, width=15)
        btn_guardar.pack(side="left", padx=10)

        btn_cancelar = ttk.Button(frame_botones, text="Cancelar",
                                command=edicion_window.destroy, width=15)
        btn_cancelar.pack(side="left", padx=10)

        # Enfocar el primer campo
        referencia_entry.focus_set()

    def eliminar_movimiento(self):
        # Obtener el item seleccionado
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un movimiento para eliminar")
            return

        # Obtener el ID del movimiento seleccionado
        item_values = self.tree.item(selected_item[0], 'values')
        movimiento_id = item_values[0]

        # Confirmar eliminación
        if not messagebox.askyesno("Confirmar Eliminación",
                                  "¿Está seguro que desea eliminar este movimiento?\n\n"
                                  "Esta acción no se puede deshacer y puede afectar el saldo de inventario."):
            return

        try:
            # Llamar a la función de eliminación en la base de datos
            from src.database.db_manager import eliminar_movimiento
            eliminar_movimiento(movimiento_id)

            messagebox.showinfo("Éxito", "Movimiento eliminado correctamente")

            # Actualizar la vista
            self.buscar_movimientos()

        except Exception as e:
            messagebox.showerror("Error", f"Error al eliminar movimiento: {str(e)}")

    def cerrar_ventana(self):
        if messagebox.askyesno("Confirmar", "¿Está seguro que desea cerrar esta ventana?"):
            # Limpiar el frame principal
            for widget in self.parent.winfo_children():
                widget.destroy()
            # Mostrar la pantalla de bienvenida
            if self.main_window:
                self.main_window.show_welcome_screen()