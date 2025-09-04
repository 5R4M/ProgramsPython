# Imports existentes
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
import sys
import os
from ttkwidgets.autocomplete import AutocompleteCombobox
import threading
import tkinter.font as tkfont

class HoverTooltip:
    """Tooltip simple para widgets Tk/ttk. Muestra el texto completo sin cambiar el ancho del widget.
       text_provider: función que devuelve el texto a mostrar (por ejemplo, lambda: combo.get()).
       show_only_if_clipped: si True, solo muestra el tooltip si el texto no cabe en el combobox.
    """
    def __init__(self, widget, text_provider, delay=250, bg='#111827', fg='#ffffff', show_only_if_clipped=True):
        self.widget = widget
        self.text_provider = text_provider
        self.delay = delay
        self.bg = bg
        self.fg = fg
        self.show_only_if_clipped = show_only_if_clipped
        self.tw = None
        self.after_id = None

        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._hide)
        widget.bind("<Motion>", self._move)
        widget.bind("<Destroy>", self._on_destroy)

    def _schedule(self, _=None):
        self._cancel()
        self.after_id = self.widget.after(self.delay, self._show)

    def _cancel(self):
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None

    def _is_clipped(self, text):
        try:
            f = tkfont.Font(font=self.widget.cget('font') or 'TkDefaultFont')
        except Exception:
            f = tkfont.nametofont('TkDefaultFont')
        text_px = f.measure(text)
        # algo de margen interno del combobox
        available = max(0, self.widget.winfo_width() - 16)
        return text_px > available

    def _show(self):
        text = (self.text_provider() or '').strip()
        if not text:
            return
        if self.show_only_if_clipped and not self._is_clipped(text):
            return

        if self.tw:
            self._hide()

        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        try:
            self.tw.attributes('-topmost', True)
        except Exception:
            pass

        label = tk.Label(self.tw, text=text, justify='left',
                         background=self.bg, foreground=self.fg,
                         relief='solid', borderwidth=1,
                         padx=6, pady=3, font=('Segoe UI', 9))
        label.pack()
        self._place()

    def _place(self, _=None):
        if not self.tw:
            return
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 2
        screen_w = self.widget.winfo_screenwidth()
        self.tw.update_idletasks()
        tip_w = self.tw.winfo_reqwidth()
        if x + tip_w > screen_w - 10:
            x = screen_w - tip_w - 10
        self.tw.wm_geometry(f"+{x}+{y}")

    def _move(self, e=None):
        self._place()

    def _hide(self, _=None):
        self._cancel()
        if self.tw:
            try:
                self.tw.destroy()
            except Exception:
                pass
            self.tw = None

    def _on_destroy(self, _=None):
        self._hide()

    def flash(self, ms=2000):
        """Muestra el tooltip durante ms milisegundos (útil al seleccionar)."""
        self._hide()
        self._show()
        if self.tw:
            self.widget.after(ms, self._hide)

# Agregar el directorio raíz del proyecto al PATH de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.db_manager import (
    obtener_areas,
    obtener_distritos,
    obtener_distritos_por_area,
    obtener_tipos_servicio_por_distrito,
    obtener_servicios_por_tipo,
    obtener_tipos_insumo,
    obtener_insumos_por_tipo,
    obtener_presentaciones,
    buscar_movimientos_por_filtros,
    obtener_tipos_movimiento
)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        # En desarrollo, base_path es la raíz del proyecto (subir un nivel desde gui)
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(base_path, relative_path)

class DataCache:
    """
    Cachea catálogos y resuelve IDs sin golpear la BD repetidamente.
    Prefetch global: áreas, distritos, tipos_insumo, tipos_movimiento.
    Lazy: distritos_por_area, tipos_servicio_por_distrito, servicios_por_tipo, insumos_por_tipo.
    """
    def __init__(self):
        self.lock = threading.RLock()
        self.initialized = False

        self.areas = []
        self.area_name_to_id = {}

        self.distritos = []
        self.distrito_name_to_id = {}

        self.tipos_insumo = []
        self.tipo_insumo_desc_to_id = {}

        self.tipos_movimiento = []
        self.tipo_mov_desc_to_id = {}

        self.distritos_por_area = {}  # area_id -> list(dict)
        self.tipos_servicio_por_distrito = {}  # distrito_id -> list(dict)
        self.tipos_serv_desc_to_id_by_distrito = {}  # (distrito_id, desc) -> id

        self.servicios_por_tipo = {}  # tipo_servicio_id -> list(dict)
        self.servicio_name_to_id_by_tipo = {}  # (tipo_servicio_id, nombre) -> id

        self.insumos_por_tipo = {}  # tipo_insumo_id -> list(dict)
        self.insumo_name_to_id_by_tipo = {}  # (tipo_insumo_id, nombre) -> id

    def reset(self):
        with self.lock:
            self.__init__()

    def initialize(self):
        with self.lock:
            if self.initialized:
                return
            self.areas = obtener_areas() or []
            self.area_name_to_id = {a['nombre']: a['id'] for a in self.areas}

            self.distritos = obtener_distritos() or []
            self.distrito_name_to_id = {d['nombre']: d['id'] for d in self.distritos}

            self.tipos_insumo = obtener_tipos_insumo() or []
            self.tipo_insumo_desc_to_id = {ti['descripcion']: ti['id'] for ti in self.tipos_insumo}

            self.tipos_movimiento = obtener_tipos_movimiento() or []
            self.tipo_mov_desc_to_id = {tm['descripcion']: tm['id'] for tm in self.tipos_movimiento}

            self.initialized = True

    # Getters nombres
    def get_area_names(self):
        return [a['nombre'] for a in self.areas]

    def get_distritos_names(self):
        return [d['nombre'] for d in self.distritos]

    def get_tipos_insumo_names(self):
        return [ti['descripcion'] for ti in self.tipos_insumo]

    def get_tipos_movimiento_names(self):
        return [tm['descripcion'] for tm in self.tipos_movimiento]

    # Lazy fetch por relaciones
    def get_distritos_por_area(self, area_id):
        with self.lock:
            if area_id in self.distritos_por_area:
                return self.distritos_por_area[area_id]
        distritos = obtener_distritos_por_area(area_id) or []
        with self.lock:
            self.distritos_por_area[area_id] = distritos
        return distritos

    def get_tipos_servicio_por_distrito(self, distrito_id):
        with self.lock:
            if distrito_id in self.tipos_servicio_por_distrito:
                return self.tipos_servicio_por_distrito[distrito_id]
        tipos = obtener_tipos_servicio_por_distrito(distrito_id) or []
        with self.lock:
            self.tipos_servicio_por_distrito[distrito_id] = tipos
            for ts in tipos:
                self.tipos_serv_desc_to_id_by_distrito[(distrito_id, ts['descripcion'])] = ts['id']
        return tipos

    def get_servicios_por_tipo(self, tipo_servicio_id):
        with self.lock:
            if tipo_servicio_id in self.servicios_por_tipo:
                return self.servicios_por_tipo[tipo_servicio_id]
        servicios = obtener_servicios_por_tipo(tipo_servicio_id) or []
        with self.lock:
            self.servicios_por_tipo[tipo_servicio_id] = servicios
            for s in servicios:
                self.servicio_name_to_id_by_tipo[(tipo_servicio_id, s['nombre'])] = s['id']
        return servicios

    def get_insumos_por_tipo(self, tipo_insumo_id):
        with self.lock:
            if tipo_insumo_id in self.insumos_por_tipo:
                return self.insumos_por_tipo[tipo_insumo_id]
        insumos = obtener_insumos_por_tipo(tipo_insumo_id) or []
        with self.lock:
            self.insumos_por_tipo[tipo_insumo_id] = insumos
            for i in insumos:
                self.insumo_name_to_id_by_tipo[(tipo_insumo_id, i['nombre'])] = i['id']
        return insumos

    # Resolutores de ID
    def area_id(self, nombre): return self.area_name_to_id.get(nombre)
    def distrito_id(self, nombre): return self.distrito_name_to_id.get(nombre)
    def tipo_insumo_id(self, desc): return self.tipo_insumo_desc_to_id.get(desc)
    def tipo_movimiento_id(self, desc): return self.tipo_mov_desc_to_id.get(desc)

    def tipo_servicio_id(self, desc, distrito_id):
        if not desc or not distrito_id:
            return None
        self.get_tipos_servicio_por_distrito(distrito_id)  # asegura caché
        return self.tipos_serv_desc_to_id_by_distrito.get((distrito_id, desc))

    def servicio_id(self, nombre, tipo_servicio_id):
        if not nombre or not tipo_servicio_id:
            return None
        self.get_servicios_por_tipo(tipo_servicio_id)
        return self.servicio_name_to_id_by_tipo.get((tipo_servicio_id, nombre))

    def insumo_id(self, nombre, tipo_insumo_id):
        if not nombre or not tipo_insumo_id:
            return None
        self.get_insumos_por_tipo(tipo_insumo_id)
        return self.insumo_name_to_id_by_tipo.get((tipo_insumo_id, nombre))


# Instancia global
cache = DataCache()

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
        self.preload_data_async()

    def cargar_iconos(self):
        try:
            icons_path = resource_path(os.path.join('utils', 'icons'))

            # Ajusta la ruta según tu proyecto
            self.icon_editar = tk.PhotoImage(file=os.path.join(icons_path, "editar.png")).subsample(2, 2)
            self.icon_eliminar = tk.PhotoImage(file=os.path.join(icons_path, "eliminar.png")).subsample(2, 2)
            self.icon_cerrar = tk.PhotoImage(file=os.path.join(icons_path, "cerrar.png")).subsample(2, 2)
            self.icon_buscar = tk.PhotoImage(file=os.path.join(icons_path, "buscar.png")).subsample(2, 2)
            self.icon_limpiar = tk.PhotoImage(file=os.path.join(icons_path, "limpiar.png")).subsample(2, 2)
        except Exception as e:
            print(f"Error cargando iconos: {e}")
            self.icon_editar = None
            self.icon_eliminar = None
            self.icon_cerrar = None
            self.icon_buscar = None
            self.icon_limpiar = None

    def create_titled_frame(self, parent, title, content_padx=10, content_pady=10):
        container = tk.Frame(parent, bg=self.COLORS['white'], relief='solid', borderwidth=1)

        header = tk.Frame(container, bg=self.COLORS['primary'], height=20)
        header.pack(fill='x')
        header.pack_propagate(False)

        label = tk.Label(header, text=title, font=('Segoe UI', 8, 'bold'),
                        fg=self.COLORS['white'], bg=self.COLORS['primary'])
        label.pack(side='left', padx=10, pady=2)

        content = tk.Frame(container, bg=self.COLORS['white'])
        content.pack(fill='both', expand=True, padx=content_padx, pady=content_pady)

        return container, content

    def setup_styles(self):
        # Paleta igual a IngresoInsumos.py
        self.COLORS = {
            'primary':   '#2c3e50',
            'secondary': '#34495e',
            'accent':    '#3498db',
            'success':   '#27ae60',
            'warning':   '#f39c12',
            'danger':    '#e74c3c',
            'light':     '#ecf0f1',
            'white':     '#ffffff',
            'text_dark': '#2c3e50',
            'text_light':'#7f8c8d',
            'border':    '#bdc3c7'
        }

        style = ttk.Style()
        try:
            style.theme_use('clam')  # asegura que ttk respete los colores
        except Exception:
            pass

        # Estilos base usados por esta pantalla
        style.configure('White.TFrame', background=self.COLORS['white'])
        style.configure('White.TLabel',
            background=self.COLORS['white'],
            foreground=self.COLORS['text_dark'],
            font=('Segoe UI', 9)
        )
        style.configure('White.TButton',
            background=self.COLORS['white'],
            foreground=self.COLORS['text_dark'],
            font=('Segoe UI', 9),
            relief='flat',
            borderwidth=0
        )
        style.map('White.TButton',
            background=[('active', self.COLORS['light']), ('pressed', self.COLORS['light'])]
        )

        style.configure('Card.TLabelframe',
            background=self.COLORS['white'],
            relief='solid',
            borderwidth=1,
            labeloutside=False
        )
        style.configure('Card.TLabelframe.Label',
            background=self.COLORS['primary'],
            foreground=self.COLORS['light'],
            font=('Segoe UI', 9, 'bold'),
            padding=(8, 3)
        )

        style.configure('Primary.TButton',
            font=('Segoe UI', 9, 'bold'),
            padding=(12, 6),
            relief='flat',
            borderwidth=0,
            background=self.COLORS['accent'],
            foreground=self.COLORS['white']
        )
        style.map('Primary.TButton',
            background=[('active', '#2980b9'), ('pressed', '#117a8b')],
            foreground=[('active', '#ffffff'), ('pressed', '#ffffff')]
        )

        style.configure('Search.TButton',
            font=('Segoe UI', 9, 'bold'),
            padding=(8, 4),
            relief='flat',
            borderwidth=0,
            background=self.COLORS['accent'],
            foreground=self.COLORS['white'],
            focuscolor='none'
        )
        style.map('Search.TButton',
            background=[('active', '#2980b9'), ('pressed', '#117a8b')]
        )

        style.configure('Title.TLabel',
            font=('Segoe UI', 12, 'bold'),
            background=self.COLORS['white'],
            foreground=self.COLORS['primary']
        )
        style.configure('Subtitle.TLabel',
            font=('Segoe UI', 8),
            background=self.COLORS['white'],
            foreground=self.COLORS['text_light']
        )

        # Treeview igual que IngresoInsumos.py y con headers grises claros
        style.configure("Custom.Treeview",
            background=self.COLORS['white'],
            foreground=self.COLORS['text_dark'],
            rowheight=18,
            fieldbackground=self.COLORS['white'],
            font=('Segoe UI', 9),
            borderwidth=1,
            relief='solid'
        )

        # Encabezados gris claro, texto oscuro
        HEADER_BG = '#e5e7eb'   # gris claro
        HEADER_FG = '#111827'   # texto oscuro

        for heading_style in ("Treeview.Heading", "Custom.Treeview.Heading"):
            style.configure(
                heading_style,
                background=HEADER_BG,
                foreground=HEADER_FG,
                font=('Segoe UI', 8, 'bold'),
                relief='flat',
                borderwidth=1,
                padding=(3, 6, 3, 6),
                anchor='center',
                justify='center'
            )
            style.map(heading_style, background=[], foreground=[])

        style.map("Custom.Treeview",
            background=[('selected', self.COLORS['accent'])],
            foreground=[('selected', '#ffffff')]
        )

    def setup_ui(self):
        # --- Frame principal que contendrá todo ---
        main_container = tk.Frame(self.parent, bg=self.COLORS['light'])  # <--- CAMBIO
        main_container.pack(fill="both", expand=True)

        # --- Título principal ---
        title_frame = tk.Frame(main_container, bg=self.COLORS['primary'], height=70)  # <--- CAMBIO
        title_frame.pack(fill='x', padx=0, pady=(10, 5))
        title_frame.pack_propagate(False)

        title_inner = tk.Frame(title_frame, bg=self.COLORS['primary'])
        title_inner.pack(fill='both', expand=True, padx=15, pady=8)

        tk.Label(title_inner,
                text="🛠️ Correcciones Movimientos de Insumos",
                font=('Segoe UI', 12, 'bold'),
                fg=self.COLORS['white'],
                bg=self.COLORS['primary']).pack(anchor='w')

        tk.Label(title_inner,
                text="Corrija los movimientos de los insumos",
                font=('Segoe UI', 8),
                fg=self.COLORS['white'],
                bg=self.COLORS['primary']).pack(anchor='w', pady=(2, 0))

        # CONTENIDO SIN SCROLL VERTICAL
        content_frame = tk.Frame(main_container, bg=self.COLORS['white'])
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Mantén el mismo nombre de variable que usas después
        self.scrollable_frame = content_frame

        self.frame_principal = tk.Frame(self.scrollable_frame, bg=self.COLORS['white'])
        self.frame_principal.pack(fill="x", expand=False, pady=5)

        # Frame para fechas con título personalizado (menos padding)
        self.frame_fechas_container, self.frame_fechas = self.create_titled_frame(
            self.frame_principal, "📅 Selección de Fechas", content_padx=5, content_pady=5
        )
        self.frame_fechas_container.config(bg=self.COLORS['white'])
        self.frame_fechas.config(bg=self.COLORS['white'])
        self.frame_fechas_container.pack(fill="x", expand=False, pady=5, padx=5)

        # Frame para rango de fechas con márgenes simétricos
        self.frame_rango = ttk.Frame(self.frame_fechas, style='White.TFrame')
        self.frame_rango.pack(fill="x", expand=False, padx=5, pady=8)

        # Configurar grid IGUAL que los otros frames (8 columnas para consistencia)
        self.frame_rango.grid_columnconfigure(0, weight=0, minsize=80)
        self.frame_rango.grid_columnconfigure(1, weight=1, minsize=120)
        self.frame_rango.grid_columnconfigure(2, weight=0, minsize=80)
        self.frame_rango.grid_columnconfigure(3, weight=1, minsize=120)
        self.frame_rango.grid_columnconfigure(4, weight=0, minsize=20)   # Espaciador reducido
        self.frame_rango.grid_columnconfigure(5, weight=1, minsize=40)   # Espaciador reducido
        self.frame_rango.grid_columnconfigure(6, weight=0, minsize=20)   # Espaciador reducido
        self.frame_rango.grid_columnconfigure(7, weight=1, minsize=40)   # Espaciador reducido

        # Aplicar padding simétrico IGUAL que los combos
        label_style = {'style': 'White.TLabel'}
        padding_config = {'pady': 8}

        # Elementos con padding simétrico IGUAL que los combos
        ttk.Label(self.frame_rango, text="Fecha Inicial:", **label_style).grid(
            row=0, column=0, padx=(10, 4), sticky='w', **padding_config
        )
        
        self.fecha_inicial = DateEntry(
            self.frame_rango,
            width=12,
            date_pattern='dd/mm/yyyy',
            state='normal'
        )
        self.fecha_inicial.grid(row=0, column=1, padx=4, sticky='ew', **padding_config)

        ttk.Label(self.frame_rango, text="Fecha Final:", **label_style).grid(
            row=0, column=2, padx=4, sticky='w', **padding_config
        )

        self.fecha_final = DateEntry(
            self.frame_rango,
            width=12,
            date_pattern='dd/mm/yyyy',
            state='normal'
        )
        self.fecha_final.grid(row=0, column=3, padx=4, sticky='ew', **padding_config)

        # AGREGAR elementos invisibles para igualar ancho con otros frames
        ttk.Label(self.frame_rango, text="", **label_style).grid(
            row=0, column=4, padx=8, sticky='w', **padding_config
        )
        ttk.Label(self.frame_rango, text="", **label_style).grid(
            row=0, column=5, padx=8, sticky='ew', **padding_config
        )
        ttk.Label(self.frame_rango, text="", **label_style).grid(
            row=0, column=6, padx=8, sticky='w', **padding_config
        )
        ttk.Label(self.frame_rango, text="", **label_style).grid(
            row=0, column=7, padx=(8, 20), sticky='ew', **padding_config
        )

        # Frame para combos con márgenes consistentes
        self.frame_combos = ttk.Frame(self.frame_principal, style='White.TFrame')
        self.frame_combos.pack(fill="x", expand=False, padx=5, pady=5)

        # Primera fila de combos con título personalizado
        self.frame_combos1_container, self.frame_combos1 = self.create_titled_frame(
            self.frame_combos, "📍 Selección de Ubicación", content_padx=5, content_pady=5
        )
        self.frame_combos1_container.config(bg=self.COLORS['white'])
        self.frame_combos1.config(bg=self.COLORS['white'])
        self.frame_combos1_container.pack(fill="x", expand=False, padx=0, pady=5)

        # Configurar grid para distribución geométrica uniforme con márgenes simétricos
        self.frame_combos1.grid_columnconfigure(0, weight=0, minsize=80)   # Labels fijos
        self.frame_combos1.grid_columnconfigure(1, weight=1, minsize=120)  # Combos expandibles
        self.frame_combos1.grid_columnconfigure(2, weight=0, minsize=80)   
        self.frame_combos1.grid_columnconfigure(3, weight=1, minsize=120)  
        self.frame_combos1.grid_columnconfigure(4, weight=0, minsize=100)  # Label más ancho
        self.frame_combos1.grid_columnconfigure(5, weight=1, minsize=120)  
        self.frame_combos1.grid_columnconfigure(6, weight=0, minsize=80)   
        self.frame_combos1.grid_columnconfigure(7, weight=1, minsize=120)  

        ttk.Label(self.frame_combos1, text="Área:", **label_style).grid(
            row=0, column=0, padx=(20, 8), sticky='w', **padding_config
        )
        self.area_var = tk.StringVar()
        self.combo_area = AutocompleteCombobox(self.frame_combos1, textvariable=self.area_var, state="normal", font=('Segoe UI', 9))
        self.combo_area.grid(row=0, column=1, padx=8, sticky='ew', **padding_config)

        ttk.Label(self.frame_combos1, text="Distrito:", **label_style).grid(
            row=0, column=2, padx=8, sticky='w', **padding_config
        )
        self.distrito_var = tk.StringVar()
        self.combo_distrito = AutocompleteCombobox(self.frame_combos1, textvariable=self.distrito_var, state="normal", font=('Segoe UI', 9))
        self.combo_distrito.grid(row=0, column=3, padx=8, sticky='ew', **padding_config)

        ttk.Label(self.frame_combos1, text="Tipo de Servicio:", **label_style).grid(
            row=0, column=4, padx=8, sticky='w', **padding_config
        )
        self.tipo_servicio_var = tk.StringVar()
        self.combo_tipo_servicio = AutocompleteCombobox(self.frame_combos1, textvariable=self.tipo_servicio_var, state="normal", font=('Segoe UI', 9))
        self.combo_tipo_servicio.grid(row=0, column=5, padx=8, sticky='ew', **padding_config)

        ttk.Label(self.frame_combos1, text="Servicio:", **label_style).grid(
            row=0, column=6, padx=8, sticky='w', **padding_config
        )
        self.servicio_var = tk.StringVar()
        self.combo_servicio = AutocompleteCombobox(self.frame_combos1, textvariable=self.servicio_var, state="normal", font=('Segoe UI', 9))
        self.combo_servicio.grid(row=0, column=7, padx=(8, 20), sticky='ew', **padding_config)

        # Segunda fila de combos con título personalizado
        self.frame_combos2_container, self.frame_combos2 = self.create_titled_frame(
            self.frame_combos, "💊 Insumos / Tipo Movimiento", content_padx=5, content_pady=5
        )
        self.frame_combos2_container.config(bg=self.COLORS['white'])
        self.frame_combos2.config(bg=self.COLORS['white'])
        self.frame_combos2_container.pack(fill="x", expand=False, padx=0, pady=5)

        # Configurar grid idéntico para simetría
        self.frame_combos2.grid_columnconfigure(0, weight=0, minsize=80)   
        self.frame_combos2.grid_columnconfigure(1, weight=1, minsize=120)  
        self.frame_combos2.grid_columnconfigure(2, weight=0, minsize=80)   
        self.frame_combos2.grid_columnconfigure(3, weight=1, minsize=120)  
        self.frame_combos2.grid_columnconfigure(4, weight=0, minsize=100)  
        self.frame_combos2.grid_columnconfigure(5, weight=1, minsize=120)  
        self.frame_combos2.grid_columnconfigure(6, weight=0, minsize=80)   
        self.frame_combos2.grid_columnconfigure(7, weight=1, minsize=120)  

        ttk.Label(self.frame_combos2, text="Tipo\nInsumo:", **label_style).grid(
            row=0, column=0, padx=(20, 8), sticky='w', **padding_config
        )
        self.tipo_insumo_var = tk.StringVar()
        self.combo_tipo_insumo = AutocompleteCombobox(self.frame_combos2, textvariable=self.tipo_insumo_var, state="normal", font=('Segoe UI', 9))
        self.combo_tipo_insumo.grid(row=0, column=1, padx=8, sticky='ew', **padding_config)

        ttk.Label(self.frame_combos2, text="Insumo:", **label_style).grid(
            row=0, column=2, padx=8, sticky='w', **padding_config
        )
        self.insumo_var = tk.StringVar()
        self.combo_insumo = AutocompleteCombobox(self.frame_combos2, textvariable=self.insumo_var, state="normal", font=('Segoe UI', 9))
        self.combo_insumo.grid(row=0, column=3, padx=8, sticky='ew', **padding_config)
        
        # Tooltip para mostrar el nombre completo del Insumo
        self.tooltip_insumo = HoverTooltip(
            self.combo_insumo,
            text_provider=lambda: self.combo_insumo.get(),
            delay=250,
            show_only_if_clipped=True  # Cambia a False si quieres que se muestre siempre
        )

        ttk.Label(self.frame_combos2, text="Presentación:", **label_style).grid(
            row=0, column=4, padx=8, sticky='w', **padding_config
        )
        self.presentacion_var = tk.StringVar()
        self.combo_presentacion = AutocompleteCombobox(self.frame_combos2, textvariable=self.presentacion_var, state="normal", font=('Segoe UI', 9))
        self.combo_presentacion.config(completevalues=[''])
        self.combo_presentacion.grid(row=0, column=5, padx=8, sticky='ew', **padding_config)

        ttk.Label(self.frame_combos2, text="Tipo\nMovimiento:", **label_style).grid(
            row=0, column=6, padx=8, sticky='w', **padding_config
        )
        self.tipo_movimiento_var = tk.StringVar()
        self.combo_tipo_movimiento = AutocompleteCombobox(self.frame_combos2, textvariable=self.tipo_movimiento_var, state="normal", font=('Segoe UI', 9))
        self.combo_tipo_movimiento.grid(row=0, column=7, padx=(8, 20), sticky='ew', **padding_config)

        # Frame para botones de búsqueda
        self.frame_botones_busqueda = ttk.Frame(self.frame_principal, style='White.TFrame')
        self.frame_botones_busqueda.pack(fill="x", pady=5)

        # Botones con iconos y sin relleno/bordes
        self.btn_buscar = tk.Button(self.frame_botones_busqueda,
            text="Buscar Movimientos",
            image=self.icon_buscar,
            compound='left',
            command=self.buscar_movimientos,
            font=('Segoe UI', 9, 'bold'),
            bg=self.COLORS['white'],
            fg=self.COLORS['text_dark'],
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            padx=15,
            pady=6,
            cursor='hand2')
        self.btn_buscar.pack(side="left", padx=5)

        self.btn_limpiar = tk.Button(self.frame_botones_busqueda,
            text="Limpiar Filtros",
            image=self.icon_limpiar,
            compound='left',
            command=self.limpiar_filtros,
            font=('Segoe UI', 9, 'bold'),
            bg=self.COLORS['white'],
            fg=self.COLORS['text_dark'],
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            padx=15,
            pady=6,
            cursor='hand2')
        self.btn_limpiar.pack(side="left", padx=5)
        
        # Frame para el Treeview con título personalizado
        self.frame_treeview_container, self.frame_treeview = self.create_titled_frame(
            self.frame_principal, "📊 Resultados", content_padx=5, content_pady=5
        )
        self.frame_treeview_container.pack(fill="x", expand=False, padx=5, pady=5)

        # Frame para Treeview compacto
        self.tree_frame = tk.Frame(self.frame_treeview, bg=self.COLORS['white'], relief='solid', borderwidth=1)
        self.tree_frame.pack(fill="x", expand=False, padx=5, pady=5)
        self.tree_frame.pack_propagate(True)
        self.tree_frame.config(height=5 * 25 + 30)  # 5 filas * rowheight + espacio encabezado

        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass

        HEADER_BG = '#e5e7eb'
        HEADER_FG = '#111827'

        style.configure("Custom.Treeview",
            font=('Segoe UI', 9),
            rowheight=18,
            background=self.COLORS['white'],
            foreground=self.COLORS['text_dark'],
            fieldbackground=self.COLORS['white']
        )
        style.configure("Custom.Treeview.Heading",
            font=('Segoe UI', 8, 'bold'),
            background=HEADER_BG,
            foreground=HEADER_FG,
            relief='flat',
            borderwidth=1,
            padding=(3, 6, 3, 6)
        )
        style.map("Custom.Treeview.Heading", background=[], foreground=[])
        style.map("Custom.Treeview",
            background=[('selected', self.COLORS['accent'])],
            foreground=[('selected', '#ffffff')]
        )
        
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
        self.cargar_tipos_movimiento()

    def preload_data_async(self):
        """Precarga catálogos en un hilo y aplica los valores a los combos."""
        def _run():
            try:
                cache.initialize()
                self.parent.after(0, self._apply_prefetched_data)
            except Exception as e:
                print("Error precargando datos:", e)
        threading.Thread(target=_run, daemon=True).start()

    def _apply_prefetched_data(self):
        """Carga listas precargadas a los comboboxes (no bloquea el arranque)."""
        try:
            # Áreas
            if hasattr(self, 'combo_area'):
                self.combo_area.config(completevalues=[''] + cache.get_area_names())
            # Distritos inicial vacío (depende de área)
            if hasattr(self, 'combo_distrito'):
                self.combo_distrito.config(completevalues=[''])
            # Tipos de insumo
            if hasattr(self, 'combo_tipo_insumo'):
                self.combo_tipo_insumo.config(completevalues=[''] + cache.get_tipos_insumo_names())
            # Presentación se resuelve al seleccionar insumo (como en IngresoInsumos)
            if hasattr(self, 'combo_presentacion'):
                self.combo_presentacion.config(completevalues=[''])
            # Tipos de movimiento
            if hasattr(self, 'combo_tipo_movimiento'):
                self.combo_tipo_movimiento.config(completevalues=[''] + cache.get_tipos_movimiento_names())
        except Exception as e:
            print("Error aplicando datos precargados:", e)

    def _enable_search_ui(self, enabled: bool):
        state = 'normal' if enabled else 'disabled'
        try:
            self.btn_buscar.config(state=state, cursor=('hand2' if enabled else 'watch'))
        except Exception:
            pass
        try:
            self.btn_limpiar.config(state=state)
        except Exception:
            pass
        try:
            root = self.parent.winfo_toplevel()
            root.configure(cursor=('' if enabled else 'watch'))
        except Exception:
            pass
    
    def cargar_areas(self):
        # La precarga ya llena; forzamos sincronizar arrays locales si las usas
        self.areas = cache.areas
        if hasattr(self, 'combo_area'):
            self.combo_area.config(completevalues=[''] + cache.get_area_names())

    def cargar_distritos(self):
        self.distritos = obtener_distritos()
        if self.distritos:
            opciones = [''] + [d['nombre'] for d in self.distritos]
            self.combo_distrito.set_completion_list(opciones)

    def cargar_distritos_por_area(self, event=None):
        area_nombre = (self.combo_area.get() or '').strip()
        area_id = cache.area_id(area_nombre)
        if area_id:
            distritos = cache.get_distritos_por_area(area_id) or []
            self.distritos = distritos
            self.combo_distrito.config(completevalues=[''] + [d['nombre'] for d in distritos])
        else:
            self.distritos = []
            self.combo_distrito.config(completevalues=[''])
            self.combo_distrito.set('')

        # Limpiar dependientes
        if hasattr(self, 'combo_tipo_servicio'):
            self.combo_tipo_servicio.config(completevalues=[''])
            self.combo_tipo_servicio.set('')
        if hasattr(self, 'combo_servicio'):
            self.combo_servicio.config(completevalues=[''])
            self.combo_servicio.set('')

    def cargar_tipos_servicio(self, event=None):
        self.combo_tipo_servicio.set('')
        self.combo_servicio.config(completevalues=[''])
        self.combo_servicio.set('')

        distrito_nombre = (self.combo_distrito.get() or '').strip()
        distrito_id = cache.distrito_id(distrito_nombre)
        if distrito_id:
            tipos = cache.get_tipos_servicio_por_distrito(distrito_id) or []
            self.tipos_servicio = tipos
            self.combo_tipo_servicio.config(completevalues=[''] + [t['descripcion'] for t in tipos])

    def cargar_servicios(self, event=None):
        self.combo_servicio.set('')
        tipo_servicio_desc = (self.combo_tipo_servicio.get() or '').strip()
        distrito_nombre = (self.combo_distrito.get() or '').strip()
        distrito_id = cache.distrito_id(distrito_nombre)

        if tipo_servicio_desc and distrito_id:
            tipo_servicio_id = cache.tipo_servicio_id(tipo_servicio_desc, distrito_id)
            if tipo_servicio_id:
                servicios = cache.get_servicios_por_tipo(tipo_servicio_id) or []
                self.combo_servicio.config(completevalues=[''] + [s['nombre'] for s in servicios])

    def cargar_tipos_insumo(self):
        self.tipos_insumo = cache.tipos_insumo
        self.combo_tipo_insumo.config(completevalues=[''] + cache.get_tipos_insumo_names())

    def cargar_insumos(self, event=None):
        self.combo_insumo.set('')
        self.combo_presentacion.set('')

        tipo_insumo_desc = (self.combo_tipo_insumo.get() or '').strip()
        tipo_insumo_id = cache.tipo_insumo_id(tipo_insumo_desc)
        if tipo_insumo_id:
            self.insumos = cache.get_insumos_por_tipo(tipo_insumo_id) or []
            self.combo_insumo.config(completevalues=[''] + [i['nombre'] for i in self.insumos])
        else:
            self.insumos = []
            self.combo_insumo.config(completevalues=[''])

    def actualizar_presentacion(self, event=None):
        insumo_nombre = (self.combo_insumo.get() or '').strip()
        tipo_insumo_desc = (self.combo_tipo_insumo.get() or '').strip()
        tipo_insumo_id = cache.tipo_insumo_id(tipo_insumo_desc)
        if tipo_insumo_id and insumo_nombre:
            insumos = cache.get_insumos_por_tipo(tipo_insumo_id) or []
            insumo_sel = next((i for i in insumos if i['nombre'] == insumo_nombre), None)
            if insumo_sel and insumo_sel.get('nombre_presentacion'):
                self.combo_presentacion.config(completevalues=[insumo_sel['nombre_presentacion']])
                self.combo_presentacion.set(insumo_sel['nombre_presentacion'])
                return
        self.combo_presentacion.config(completevalues=[''])
        self.combo_presentacion.set('')

    def cargar_tipos_movimiento(self):
        self.tipos_movimiento = cache.tipos_movimiento  # <-- guardar la lista completa
        self.combo_tipo_movimiento.config(completevalues=[''] + cache.get_tipos_movimiento_names())

    def buscar_movimientos(self):
        try:
            # Validaciones rápidas
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

            # Deshabilitar UI y cursor espera
            self._enable_search_ui(False)

            params = (
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

            def _run():
                try:
                    data = buscar_movimientos_por_filtros(*params) or []
                except Exception as e:
                    data = e
                self.parent.after(0, lambda: self._on_search_result(data))

            threading.Thread(target=_run, daemon=True).start()

        except Exception as e:
            self._enable_search_ui(True)
            messagebox.showerror("Error", f"Error al iniciar la búsqueda: {str(e)}")

    def _on_search_result(self, data):
        # Rehabilitar UI
        self._enable_search_ui(True)

        if isinstance(data, Exception):
            messagebox.showerror("Error", f"Error al buscar movimientos:\n{data}")
            return

        self.movimientos_data = data

        # Limpiar Treeview rápido
        try:
            self.tree.delete(*self.tree.get_children())
        except Exception:
            for item in self.tree.get_children():
                self.tree.delete(item)

        if not data:
            messagebox.showinfo("Info", "No hay datos para mostrar")
            return

        rows = []
        for mov in data:
            fecha_venc = mov.get('fecha_vencimiento') or "N/A"
            lote = mov.get('lote') or "N/A"
            rows.append((
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

        self._populate_tree_chunked(rows, chunk_size=600)

    def _populate_tree_chunked(self, rows, chunk_size=600):
        total = len(rows)
        index = 0
        def _insert_chunk():
            nonlocal index
            end = min(index + chunk_size, total)
            for i in range(index, end):
                self.tree.insert('', 'end', values=rows[i])
            index = end
            if index < total:
                self.parent.after(1, _insert_chunk)
        _insert_chunk()

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
        self.tree.delete(*self.tree.get_children())
        self.movimientos_data = None

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
        """
        Edición con estilo de 'Ingreso de Insumos':
        - Paleta self.COLORS.
        - Sin nivel de bodega (ubicación solo lectura).
        - Nombre de insumo envuelto a varias líneas.
        - Presentación asegurada (resolución robusta vía DataCache sin depender de combos activos).
        - Checkbuttons con fondo blanco consistente.
        - Optimización: after_idle y caché.
        """
        win = tk.Toplevel(self.parent)
        win.title("Editar Movimiento")
        win.configure(bg=self.COLORS['light'])
        win.grab_set()
        win.transient(self.parent)

        # Dimensiones y centrado
        W, H = 980, 650
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        x, y = (sw - W)//2, (sh - H)//2
        win.geometry(f"{W}x{H}+{x}+{y}")
        win.resizable(True, True)

        # Estilo base
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass

        # Helper de tarjeta
        def card(parent, title, pad=(20, 15), header_h=26):
            cont = tk.Frame(parent, bg=self.COLORS['white'], relief='solid', borderwidth=1)
            cont.pack(fill="x", padx=pad[0], pady=pad[1])
            header = tk.Frame(cont, bg=self.COLORS['primary'], height=header_h)
            header.pack(fill='x')
            header.pack_propagate(False)
            tk.Label(
                header, text=title, font=('Segoe UI', 9, 'bold'),
                fg=self.COLORS['white'], bg=self.COLORS['primary']
            ).pack(side='left', padx=10, pady=4)
            content = tk.Frame(cont, bg=self.COLORS['white'])
            content.pack(fill='x', padx=12, pady=8)
            return cont, content

        # Encabezado
        header_frame = tk.Frame(win, bg=self.COLORS['primary'], height=44)
        header_frame.pack(fill="x", padx=20, pady=(20, 0))
        header_frame.pack_propagate(False)
        tk.Label(
            header_frame, text="EDITAR MOVIMIENTO",
            font=('Segoe UI', 16, 'bold'), bg=self.COLORS['primary'], fg='white'
        ).pack(expand=True)

        # Variables
        ref_var = tk.StringVar(value=movimiento.get('referencia', '') or "")
        tipo_mov_var = tk.StringVar(value=movimiento.get('tipo_movimiento', '') or "")
        cantidad_var = tk.StringVar(value=self.formato_float(movimiento.get('cantidad', 0)))
        obs_var = tk.StringVar(value=movimiento.get('observaciones', '') or "")

        lote_val_ini = movimiento.get('lote')
        sin_lote_inicial = (not lote_val_ini) or (lote_val_ini in ("", "N/A", None))
        lote_var = tk.StringVar(value="" if sin_lote_inicial else (lote_val_ini or ""))
        sin_lote_var = tk.BooleanVar(value=sin_lote_inicial)

        fecha_db = movimiento.get('fecha')
        fv_db = movimiento.get('fecha_vencimiento')
        sin_fv_inicial = not bool(fv_db)
        sin_fecha_var = tk.BooleanVar(value=sin_fv_inicial)

        insumo_nombre = (movimiento.get('insumo_nombre') or "").strip()
        # Usa también campos alternativos si existieran en el dict del movimiento
        presentacion_var = tk.StringVar(value=(movimiento.get('presentacion') or movimiento.get('nombre_presentacion') or "").strip())

        # Tarjeta: Detalles
        _, det = card(win, "📋 Detalles del Movimiento")
        for c in range(6):
            det.grid_columnconfigure(c, weight=1)

        ttk.Label(det, text="Fecha de Registro:", style='White.TLabel').grid(row=0, column=0, padx=5, pady=8, sticky='w')
        fecha_entry = DateEntry(det, width=25, date_pattern='dd/mm/yyyy')
        fecha_entry.grid(row=0, column=1, padx=5, pady=8, sticky='ew')
        try:
            if fecha_db:
                fecha_entry.set_date(datetime.strptime(fecha_db, '%Y-%m-%d'))
        except Exception:
            pass

        ttk.Label(det, text="Referencia:", style='White.TLabel').grid(row=0, column=2, padx=5, pady=8, sticky='w')
        ref_entry = ttk.Entry(det, textvariable=ref_var, width=27)
        ref_entry.grid(row=0, column=3, padx=5, pady=8, sticky='ew')

        ttk.Label(det, text="Tipo Movimiento:", style='White.TLabel').grid(row=0, column=4, padx=5, pady=8, sticky='w')
        tipo_mov_cb = AutocompleteCombobox(det, textvariable=tipo_mov_var, width=25, state="normal")
        tipo_mov_cb.grid(row=0, column=5, padx=5, pady=8, sticky='ew')
        det.after_idle(lambda: tipo_mov_cb.set_completion_list(cache.get_tipos_movimiento_names() or []))

        ttk.Label(det, text="Lote:", style='White.TLabel').grid(row=1, column=0, padx=5, pady=8, sticky='w')
        lote_row = tk.Frame(det, bg=self.COLORS['white'])
        lote_row.grid(row=1, column=1, padx=5, pady=8, sticky='ew')
        lote_row.columnconfigure(0, weight=1)
        lote_entry = ttk.Entry(lote_row, textvariable=lote_var, width=22)
        lote_entry.grid(row=0, column=0, sticky='ew')
        # Checkbutton con fondo blanco
        chk_sin_lote = tk.Checkbutton(
            lote_row, text="Sin lote", variable=sin_lote_var,
            command=lambda: lote_entry.config(state=('disabled' if sin_lote_var.get() else 'normal')),
            bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
            activebackground=self.COLORS['white'], activeforeground=self.COLORS['text_dark'],
            highlightthickness=0, bd=0
        )
        chk_sin_lote.grid(row=0, column=1, padx=(8, 0), sticky='w')
        lote_entry.config(state=('disabled' if sin_lote_var.get() else 'normal'))

        ttk.Label(det, text="Fecha Vencimiento:", style='White.TLabel').grid(row=1, column=2, padx=5, pady=8, sticky='w')
        fv_row = tk.Frame(det, bg=self.COLORS['white'])
        fv_row.grid(row=1, column=3, padx=5, pady=8, sticky='w')
        fecha_venc_entry = DateEntry(fv_row, width=15, date_pattern='dd/mm/yyyy')
        fecha_venc_entry.pack(side='left')
        chk_sin_fv = tk.Checkbutton(
            fv_row, text="Sin fecha", variable=sin_fecha_var,
            command=lambda: fecha_venc_entry.config(state=('disabled' if sin_fecha_var.get() else 'normal')),
            bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
            activebackground=self.COLORS['white'], activeforeground=self.COLORS['text_dark'],
            highlightthickness=0, bd=0
        )
        chk_sin_fv.pack(side='left', padx=(8, 0))
        try:
            if fv_db:
                fecha_venc_entry.set_date(datetime.strptime(fv_db, '%Y-%m-%d'))
        except Exception:
            pass
        fecha_venc_entry.config(state=('disabled' if sin_fecha_var.get() else 'normal'))

        ttk.Label(det, text="Cantidad:", style='White.TLabel').grid(row=1, column=4, padx=5, pady=8, sticky='w')
        cantidad_entry = ttk.Entry(det, textvariable=cantidad_var, width=27)
        cantidad_entry.grid(row=1, column=5, padx=5, pady=8, sticky='ew')

        ttk.Label(det, text="Observaciones:", style='White.TLabel').grid(row=2, column=0, padx=5, pady=8, sticky='w')
        obs_entry = ttk.Entry(det, textvariable=obs_var, width=80)
        obs_entry.grid(row=2, column=1, columnspan=5, padx=5, pady=8, sticky='ew')

        # Tarjeta: Insumo
        _, ins = card(win, "💊 Insumo")
        for c in range(4):
            ins.grid_columnconfigure(c, weight=1)

        ttk.Label(ins, text="Insumo:", style='White.TLabel').grid(row=0, column=0, padx=5, pady=8, sticky='w')
        insumo_wrap = tk.Label(
            ins, text=insumo_nombre, bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
            font=('Segoe UI', 9), justify='left', anchor='w', wraplength=420
        )
        insumo_wrap.grid(row=0, column=1, padx=5, pady=8, sticky='ew')

        ttk.Label(ins, text="Presentación:", style='White.TLabel').grid(row=0, column=2, padx=5, pady=8, sticky='w')
        presentacion_cb = AutocompleteCombobox(ins, textvariable=presentacion_var, width=25, state="normal")
        presentacion_cb.grid(row=0, column=3, padx=5, pady=8, sticky='ew')

        # Resolución robusta de Presentación
        def cargar_presentacion_insumo():
            try:
                preset = (presentacion_var.get() or "").strip()
                if preset:
                    # Sólo asegura la lista del combo una vez
                    presentacion_cb.set_completion_list([preset])
                    return

                # Construir o reutilizar índice
                if hasattr(cache, 'get_insumo_by_nombre'):
                    ins_sel = cache.get_insumo_by_nombre(insumo_nombre)
                else:
                    # Índice local en la vista
                    if getattr(self, '_idx_insumos_por_nombre', None) is None:
                        # Construcción diferida para no bloquear la UI
                        def build_and_set():
                            self._idx_insumos_por_nombre = {}
                            for ti in (cache.tipos_insumo or []):
                                for ins in (cache.get_insumos_por_tipo(ti.get('id')) or []):
                                    nombre = (ins.get('nombre') or '').strip()
                                    if nombre and nombre not in self._idx_insumos_por_nombre:
                                        self._idx_insumos_por_nombre[nombre] = ins
                            # Luego de construir, resolver presentación
                            ins_sel2 = self._idx_insumos_por_nombre.get(insumo_nombre)
                            pres = (ins_sel2 or {}).get('nombre_presentacion') or (ins_sel2 or {}).get('presentacion') or ''
                            presentacion_var.set(pres)
                            presentacion_cb.set_completion_list([pres or ''])
                        ins.after(1, build_and_set)
                        return
                    ins_sel = self._idx_insumos_por_nombre.get(insumo_nombre)

                pres = (ins_sel or {}).get('nombre_presentacion') or (ins_sel or {}).get('presentacion') or ''
                presentacion_var.set(pres)
                presentacion_cb.set_completion_list([pres or ''])

            except Exception as e:
                print("Error determinando presentación:", e)
                presentacion_var.set('')
                presentacion_cb.set_completion_list([''])

        # Cargar presentación tras pintar UI (no bloquear)
        ins.after_idle(cargar_presentacion_insumo)

        # Tarjeta: Ubicación (solo lectura)
        _, ubi = card(win, "📍 Ubicación")
        for c in range(4):
            ubi.grid_columnconfigure(c, weight=1)

        ttk.Label(ubi, text="Área:", style='White.TLabel').grid(row=0, column=0, padx=5, pady=6, sticky='w')
        ttk.Label(ubi, text=movimiento.get('area_nombre', '') or "", style='White.TLabel').grid(row=0, column=1, padx=5, pady=6, sticky='w')
        ttk.Label(ubi, text="Distrito:", style='White.TLabel').grid(row=0, column=2, padx=5, pady=6, sticky='w')
        ttk.Label(ubi, text=movimiento.get('distrito_nombre', '') or "", style='White.TLabel').grid(row=0, column=3, padx=5, pady=6, sticky='w')

        ttk.Label(ubi, text="Tipo de Servicio:", style='White.TLabel').grid(row=1, column=0, padx=5, pady=6, sticky='w')
        ttk.Label(ubi, text=movimiento.get('tipo_servicio_desc', '') or "", style='White.TLabel').grid(row=1, column=1, padx=5, pady=6, sticky='w')
        ttk.Label(ubi, text="Servicio:", style='White.TLabel').grid(row=1, column=2, padx=5, pady=6, sticky='w')
        ttk.Label(ubi, text=movimiento.get('servicio_nombre', '') or "", style='White.TLabel').grid(row=1, column=3, padx=5, pady=6, sticky='w')

        # Botones
        btns_frame = tk.Frame(win, bg=self.COLORS['light'])
        btns_frame.pack(fill="x", padx=20, pady=24)
        btns_inner = tk.Frame(btns_frame, bg=self.COLORS['light'])
        btns_inner.pack(anchor='center')

        def validar():
            try:
                _ = fecha_entry.get_date()
            except Exception:
                messagebox.showerror("Error", "La fecha de registro es obligatoria")
                return False

            if not tipo_mov_var.get().strip():
                messagebox.showerror("Error", "El tipo de movimiento es obligatorio")
                return False

            if not (presentacion_var.get() or "").strip():
                messagebox.showerror("Error", "No se pudo determinar la presentación del insumo")
                return False

            if not sin_lote_var.get() and not (lote_var.get() or "").strip():
                messagebox.showerror("Error", "El campo Lote es obligatorio si no está marcado 'Sin lote'")
                return False

            if not sin_fecha_var.get():
                try:
                    _ = fecha_venc_entry.get_date()
                except Exception:
                    messagebox.showerror("Error", "La fecha de vencimiento es obligatoria si no está marcado 'Sin fecha'")
                    return False

            try:
                c = float(cantidad_var.get().strip() or "0")
                if c <= 0:
                    messagebox.showerror("Error", "La cantidad debe ser un número positivo")
                    return False
            except Exception:
                messagebox.showerror("Error", "La cantidad debe ser un número válido")
                return False

            return True

        def guardar():
            if not validar():
                return
            try:
                fecha_val = fecha_entry.get_date().strftime('%Y-%m-%d')
                tipo_mov_val = tipo_mov_var.get().strip()
                lote_val = None if sin_lote_var.get() else (lote_var.get().upper().strip() or None)
                fv_val = None if sin_fecha_var.get() else fecha_venc_entry.get_date().strftime('%Y-%m-%d')
                cantidad_val = float(cantidad_var.get().strip() or "0")

                datos_actualizados = {
                    'id': movimiento['id'],
                    'fecha': fecha_val,
                    'referencia': ref_var.get(),
                    'tipo_movimiento': tipo_mov_val,
                    'lote': lote_val,
                    'fecha_vencimiento': fv_val,
                    'cantidad': cantidad_val,
                    'observaciones': obs_var.get()
                }

                from src.database.db_manager import actualizar_movimiento
                actualizar_movimiento(datos_actualizados['id'], datos_actualizados)

                messagebox.showinfo("Éxito", "Movimiento actualizado correctamente")
                win.destroy()
                self.buscar_movimientos()
            except Exception as e:
                messagebox.showerror("Error", f"Error al actualizar movimiento: {str(e)}")

        btn_guardar = tk.Button(
            btns_inner, text="GUARDAR",
            image=getattr(self, 'icon_guardar', getattr(self, 'icon_editar', None)),
            compound='left', command=guardar,
            bg=self.COLORS['light'], fg=self.COLORS['text_dark'],
            font=('Segoe UI', 9, 'bold'), relief='flat',
            padx=10, pady=10, cursor='hand2',
            borderwidth=0, highlightthickness=0
        )
        btn_guardar.pack(side='left', padx=10)

        btn_cerrar = tk.Button(
            btns_inner, text="CERRAR",
            image=self.icon_cerrar if getattr(self, 'icon_cerrar', None) else None,
            compound='left', command=win.destroy,
            bg=self.COLORS['light'], fg=self.COLORS['text_dark'],
            font=('Segoe UI', 9, 'bold'), relief='flat',
            padx=10, pady=10, cursor='hand2',
            borderwidth=0, highlightthickness=0
        )
        btn_cerrar.pack(side='left', padx=10)

        ref_entry.focus_set()

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