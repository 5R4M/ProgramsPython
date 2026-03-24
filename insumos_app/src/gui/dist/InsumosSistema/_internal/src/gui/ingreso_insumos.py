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
    """Tooltip simple para widgets Tk/ttk. Muestra el texto completo sin cambiar el ancho del widget."""
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
        widget_width = self.widget.winfo_width()
        if hasattr(self.widget, 'tk') and 'Combobox' in str(type(self.widget)):
            available = max(0, widget_width - 30)
        else:
            available = max(0, widget_width - 16)
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
        self._hide()
        self._show()
        if self.tw:
            self.widget.after(ms, self._hide)

# Agregar el directorio raíz del proyecto al PATH de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.db_manager import (  # noqa: E402
    obtener_areas,
    obtener_distritos_por_area,
    obtener_distritos,
    obtener_tipos_servicio_por_distrito,
    obtener_servicios_por_tipo,
    obtener_tipos_insumo,
    obtener_insumos_por_tipo,
    obtener_tipos_movimiento,
    obtener_id_servicio,
    obtener_id_presentacion,
    obtener_id_tipo_movimiento,
    guardar_movimiento
)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(base_path, relative_path)

class DataCache:
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

        self.distritos_por_area = {}
        self.tipos_servicio_por_distrito = {}
        self.tipos_serv_desc_to_id_by_distrito = {}

        self.servicios_por_tipo = {}
        self.servicio_name_to_id_by_tipo = {}

        self.insumos_por_tipo = {}
        self.insumo_name_to_id_by_tipo = {}

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

    def get_area_names(self):
        return [a['nombre'] for a in self.areas]

    def get_distritos_names(self):
        return [d['nombre'] for d in self.distritos]

    def get_tipos_insumo_names(self):
        return [ti['descripcion'] for ti in self.tipos_insumo]

    def get_tipos_movimiento_names(self):
        return [tm['descripcion'] for tm in self.tipos_movimiento]

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

    def area_id(self, nombre): return self.area_name_to_id.get(nombre)
    def distrito_id(self, nombre): return self.distrito_name_to_id.get(nombre)
    def tipo_insumo_id(self, desc): return self.tipo_insumo_desc_to_id.get(desc)
    def tipo_movimiento_id(self, desc): return self.tipo_mov_desc_to_id.get(desc)

    def tipo_servicio_id(self, desc, distrito_id):
        if not desc or not distrito_id:
            return None
        self.get_tipos_servicio_por_distrito(distrito_id)
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


cache = DataCache()

class IngresoInsumos:
    def __init__(self, parent_frame, main_window):
        self.parent = parent_frame
        self.main_window = main_window

        # Reutilizar paleta del MainWindow o defaults
        self.COLORS = getattr(self.main_window, "COLORS", {
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
            'border':    '#bdc3c7',
            'header_dark': '#1f2937'
        })

        self.manual_widths = {}
        self.auto_resize_enabled = True

        # Variables
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
        self.nivel_bodega_var = tk.StringVar(value="area")

        # Limpieza/control de recursos
        self._trace_ids = []              # [(var, mode, cbname)]
        self._open_toplevels = []         # [Toplevel, ...]
        self._tree_on_mousewheel = None
        self._enter_bind_id = None
        self._leave_bind_id = None
        self._after_update_id = None      # si luego usas after(), guarda IDs aquí

        self.LABEL_WIDTH = 15
        self.WIDGET_WIDTH = 25
        self.PADDING_X = 8
        self.PADDING_Y = 2

        self._setup_local_styles()
        self.cargar_iconos()

        self.setup_ui()
        self.setup_bindings()
        self.actualizar_estado_comboboxes()
        self.preload_data_async()

    # Estilos locales namespaced (no toca tema global ni estilos genéricos)
    def _setup_local_styles(self):
        self.SPACING = {
            'section_pady': 2,
            'section_padx': 15,
            'card_padx': 8,
            'card_pady': 2,
            'header_height': 18,
            'content_padx': 10,
            'content_pady': 4,
            'label_pady': 2,
            'widget_pady': 2
        }
        self.WIDGET_WIDTH = 18
        self.BUTTON_WIDTH = 15

        style = ttk.Style(self.parent)

        # Área general del módulo
        style.configure('Ingreso.Main.TFrame', background=self.COLORS['light'])

        # Cards y headers
        style.configure('Ingreso.Card.TFrame', background=self.COLORS['light'], relief='solid', borderwidth=1)
        style.configure('Ingreso.Header.TFrame', background=self.COLORS['primary'])
        style.configure('Ingreso.Header.TLabel', background=self.COLORS['primary'],
                        foreground=self.COLORS['white'], font=('Segoe UI', 8, 'bold'))
        style.configure('Ingreso.Title.TLabel', font=('Segoe UI', 12, 'bold'),
                        background=self.COLORS['white'], foreground=self.COLORS['primary'])
        style.configure('Ingreso.Subtitle.TLabel', font=('Segoe UI', 8),
                        background=self.COLORS['white'], foreground=self.COLORS['text_light'])

        # Labels, entries, combos locales
        style.configure('Ingreso.TLabel', background=self.COLORS['light'], foreground=self.COLORS['text_dark'])
        style.configure('Ingreso.SectionLabel.TLabel', background=self.COLORS['light'], foreground=self.COLORS['text_dark'], font=('Segoe UI', 8, 'bold'))

        # Botones
        style.configure('Ingreso.Primary.TButton',
                        font=('Segoe UI', 9, 'bold'),
                        padding=(10, 4),
                        relief='flat',
                        borderwidth=0,
                        background=self.COLORS['accent'],
                        foreground=self.COLORS['white'])
        style.map('Ingreso.Primary.TButton',
                  background=[('active', '#2980b9'), ('pressed', '#117a8b')],
                  foreground=[('active', '#ffffff'), ('pressed', '#ffffff')])

        style.configure('Ingreso.Danger.TButton',
                        font=('Segoe UI', 9, 'bold'),
                        padding=(10, 4),
                        relief='flat',
                        borderwidth=0,
                        background=self.COLORS['danger'],
                        foreground='#ffffff')
        style.map('Ingreso.Danger.TButton',
                  background=[('active', '#b91c1c')])

        # Treeview local
        style.configure('Ingreso.Treeview',
                        background=self.COLORS['white'],
                        foreground=self.COLORS['text_dark'],
                        rowheight=18,
                        fieldbackground=self.COLORS['white'],
                        font=('Segoe UI', 9),
                        borderwidth=1,
                        relief='solid')

        header_bg = '#e5e7eb'
        header_fg = '#111827'
        style.configure('Ingreso.Treeview.Heading',
                        background=header_bg,
                        foreground=header_fg,
                        font=('Segoe UI', 8, 'bold'),
                        relief='flat',
                        borderwidth=1,
                        padding=(3, 6, 3, 6),
                        anchor='center',
                        justify='center')
        style.map('Ingreso.Treeview', background=[('selected', self.COLORS['accent'])],
                  foreground=[('selected', '#ffffff')])

    def preload_data_async(self):
        def _run():
            try:
                cache.initialize()
                self.parent.after(0, self._apply_prefetched_data)
            except Exception as e:
                print("Error precargando datos:", e)
        threading.Thread(target=_run, daemon=True).start()

    def _apply_prefetched_data(self):
        try:
            if hasattr(self, 'area_cb'):
                self.area_cb.config(completevalues=cache.get_area_names())
            if hasattr(self, 'salida_distrito_cb'):
                self.salida_distrito_cb.config(completevalues=cache.get_distritos_names())
            if hasattr(self, 'tipo_insumo_cb'):
                self.tipo_insumo_cb.config(completevalues=cache.get_tipos_insumo_names())
            if hasattr(self, 'tipo_mov_cb'):
                # El combo de tipo de movimiento será luego gobernado por el filtro,
                # pero podemos inicializar con todos.
                self.tipo_mov_cb.config(completevalues=cache.get_tipos_movimiento_names())
            # Refresco explícito del filtro tras la precarga
            self.actualizar_tipos_movimiento_filtrados()
        except Exception as e:
            print("Error aplicando datos precargados:", e)

    def update_layout(self):
        try:
            self.parent.update_idletasks()
        except (tk.TclError, AttributeError):
            pass

    # Se reemplaza setup_styles por _setup_local_styles; no toca tema global
    def setup_styles(self):
        pass  # retrocompatibilidad; no hacer nada aquí

    def cargar_iconos(self):
        try:
            icons_path = resource_path(os.path.join('utils', 'icons'))
            self.icon_area = tk.PhotoImage(file=os.path.join(icons_path, "area.png")).subsample(3, 3)
            self.icon_distrito = tk.PhotoImage(file=os.path.join(icons_path, "distrito.png")).subsample(3, 3)
            self.icon_servicio = tk.PhotoImage(file=os.path.join(icons_path, "servicio_1.png")).subsample(3, 3)

            self.icon_agregar = tk.PhotoImage(file=os.path.join(icons_path, "agregar.png")).subsample(2, 2)
            self.icon_editar = tk.PhotoImage(file(os.path.join(icons_path, "editar.png"))).subsample(2, 2) if False else tk.PhotoImage(file=os.path.join(icons_path, "editar.png")).subsample(2, 2)  # noqa: F821
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

    def _setup_treeview_styles(self):
        style = ttk.Style(self.parent)
        header_bg = '#e5e7eb'
        header_fg = '#111827'

        style.configure('Correccion.Treeview',
                        background=self.COLORS['white'],
                        foreground=self.COLORS['text_dark'],
                        rowheight=18,
                        fieldbackground=self.COLORS['white'],
                        font=('Segoe UI', 9),
                        borderwidth=1,
                        relief='solid')

        style.configure('Correccion.Treeview.Heading',
                        background=header_bg,
                        foreground=header_fg,
                        font=('Segoe UI', 8, 'bold'),
                        relief='flat',
                        borderwidth=1,
                        padding=(3, 6, 3, 6),
                        anchor='center',
                        justify='center')

        style.map('Correccion.Treeview',
                  background=[('selected', self.COLORS['accent'])],
                  foreground=[('selected', '#ffffff')])

    def setup_ui(self):
        self._setup_treeview_styles()

        # Frame raíz del módulo
        self.main_frame = ttk.Frame(self.parent, style='Ingreso.Main.TFrame')
        self.main_frame.pack(fill="both", expand=True)

        # Scrollable base
        self.scrollable_frame = tk.Frame(self.main_frame, bg=self.COLORS['light'])
        self.scrollable_frame.pack(fill="both", expand=True)

        # Top strip
        top_strip = ttk.Frame(self.scrollable_frame, style='Ingreso.Header.TFrame', height=6)
        top_strip.pack(fill='x', padx=0, pady=0)
        top_strip.pack_propagate(False)

        # Header
        header_frame = ttk.Frame(self.scrollable_frame, style='Ingreso.Header.TFrame', height=55)
        header_frame.pack(fill='x', padx=0, pady=(0, 6))
        header_frame.pack_propagate(False)

        header_inner = ttk.Frame(header_frame, style='Ingreso.Header.TFrame')
        header_inner.pack(fill='both', expand=True, padx=15, pady=4)
        ttk.Label(header_inner, text="📦 Ingreso Insumos", style='Ingreso.Header.TLabel').pack(anchor='w')
        ttk.Label(header_inner,
                  text="Registre los movimientos de insumos de manera eficiente y organizada",
                  style='Ingreso.Header.TLabel').pack(anchor='w', pady=(1, 0))

        # Nivel de bodega
        nivel_container = ttk.Frame(self.scrollable_frame, style='Ingreso.Main.TFrame')
        nivel_container.pack(fill="x", padx=15, pady=3)

        self.frame_nivel_bodega = ttk.Frame(nivel_container, style='Ingreso.Card.TFrame')
        self.frame_nivel_bodega.pack(fill="x", padx=8, pady=3)

        nivel_header = ttk.Frame(self.frame_nivel_bodega, style='Ingreso.Header.TFrame', height=20)
        nivel_header.pack(fill='x')
        nivel_header.pack_propagate(False)
        ttk.Label(nivel_header, text="🏢 Nivel de Bodega", style='Ingreso.Header.TLabel').pack(side='left', padx=10, pady=2)

        nivel_content = ttk.Frame(self.frame_nivel_bodega, style='Ingreso.Main.TFrame')
        nivel_content.pack(fill='x', padx=12, pady=4)

        rb_frame = ttk.Frame(nivel_content, style='Ingreso.Main.TFrame')
        rb_frame.pack(fill='x', pady=2)

        rb_area = tk.Radiobutton(rb_frame, text="Área", image=self.icon_area, compound='left',
                                 variable=self.nivel_bodega_var, value="area",
                                 command=self.actualizar_estado_comboboxes,
                                 font=('Segoe UI', 8),
                                 bg=self.COLORS['light'], fg=self.COLORS['text_dark'],
                                 selectcolor=self.COLORS['white'], activebackground=self.COLORS['white'])
        rb_distrito = tk.Radiobutton(rb_frame, text="Distrito", image=self.icon_distrito, compound='left',
                                     variable=self.nivel_bodega_var, value="distrito",
                                     command=self.actualizar_estado_comboboxes,
                                     font=('Segoe UI', 8),
                                     bg=self.COLORS['light'], fg=self.COLORS['text_dark'],
                                     selectcolor=self.COLORS['white'], activebackground=self.COLORS['white'])
        rb_servicio = tk.Radiobutton(rb_frame, text="Servicio", image=self.icon_servicio, compound='left',
                                     variable=self.nivel_bodega_var, value="servicio",
                                     command=self.actualizar_estado_comboboxes,
                                     font=('Segoe UI', 8),
                                     bg=self.COLORS['light'], fg=self.COLORS['text_dark'],
                                     selectcolor=self.COLORS['white'], activebackground=self.COLORS['white'])

        rb_area.grid(row=0, column=0, padx=(0, 20), pady=2, sticky="w")
        rb_distrito.grid(row=0, column=1, padx=(0, 20), pady=2, sticky="w")
        rb_servicio.grid(row=0, column=2, padx=(0, 20), pady=2, sticky="w")

        # Servicios
        servicios_container = ttk.Frame(self.scrollable_frame, style='Ingreso.Main.TFrame')
        servicios_container.pack(fill="x", padx=15, pady=3)

        self.frame_servicios = ttk.Frame(servicios_container, style='Ingreso.Card.TFrame')
        self.frame_servicios.pack(fill="x", padx=8, pady=2)

        servicios_header = ttk.Frame(self.frame_servicios, style='Ingreso.Header.TFrame', height=16)
        servicios_header.pack(fill='x')
        servicios_header.pack_propagate(False)
        ttk.Label(servicios_header, text="🏥 Configuración de Servicios",
                  style='Ingreso.Header.TLabel').pack(side='left', padx=8, pady=0)

        servicios_content = ttk.Frame(self.frame_servicios, style='Ingreso.Main.TFrame')
        servicios_content.pack(fill='x', padx=10, pady=2)

        for i in range(4):
            servicios_content.columnconfigure(i, weight=1, uniform="servicios_group")

        ttk.Label(servicios_content, text="Área:", style='Ingreso.SectionLabel.TLabel').grid(row=0, column=0, padx=4, pady=(1,1), sticky="w")
        self.area_var = tk.StringVar()
        self.area_cb = AutocompleteCombobox(servicios_content, textvariable=self.area_var,
                                            completevalues=[], state="normal", font=('Segoe UI', 8))
        self.area_cb.grid(row=1, column=0, padx=4, pady=(1,2), sticky="ew")

        ttk.Label(servicios_content, text="Distrito:", style='Ingreso.SectionLabel.TLabel').grid(row=0, column=1, padx=4, pady=(1,1), sticky="w")
        self.distrito_var = tk.StringVar()
        self.distrito_cb = AutocompleteCombobox(servicios_content, textvariable=self.distrito_var,
                                                completevalues=[], state="normal", font=('Segoe UI', 8))
        self.distrito_cb.grid(row=1, column=1, padx=4, pady=(1,2), sticky="ew")

        ttk.Label(servicios_content, text="Tipo de Servicio:", style='Ingreso.SectionLabel.TLabel').grid(row=0, column=2, padx=4, pady=(1,1), sticky="w")
        self.tipo_servicio_var = tk.StringVar()
        self.tipo_servicio_cb = AutocompleteCombobox(servicios_content, textvariable=self.tipo_servicio_var,
                                                     completevalues=[], state="normal", font=('Segoe UI', 8))
        self.tipo_servicio_cb.grid(row=1, column=2, padx=4, pady=(1,2), sticky="ew")

        ttk.Label(servicios_content, text="Servicio:", style='Ingreso.SectionLabel.TLabel').grid(row=0, column=3, padx=4, pady=(1,1), sticky="w")
        self.servicio_var = tk.StringVar()
        self.servicio_cb = AutocompleteCombobox(servicios_content, textvariable=self.servicio_var,
                                                completevalues=[], state="normal", font=('Segoe UI', 8))
        self.servicio_cb.grid(row=1, column=3, padx=4, pady=(1,2), sticky="ew")

        self.distrito_cb.config(completevalues=[])
        self.distrito_var.set('')

        # Insumos
        insumos_container = ttk.Frame(self.scrollable_frame, style='Ingreso.Main.TFrame')
        insumos_container.pack(fill="x", padx=15, pady=1)

        self.frame_insumos = ttk.Frame(insumos_container, style='Ingreso.Card.TFrame')
        self.frame_insumos.pack(fill="x", padx=8, pady=2)

        insumos_header = ttk.Frame(self.frame_insumos, style='Ingreso.Header.TFrame', height=16)
        insumos_header.pack(fill='x')
        insumos_header.pack_propagate(False)
        ttk.Label(insumos_header, text="💊 Gestión de Insumos", style='Ingreso.Header.TLabel').pack(side='left', padx=10, pady=0)

        insumos_content = ttk.Frame(self.frame_insumos, style='Ingreso.Main.TFrame')
        insumos_content.pack(fill='x', padx=12, pady=2)

        for i in range(8):
            insumos_content.columnconfigure(i, weight=1, uniform="insumos_group")

        ttk.Label(insumos_content, text="Tipo de Insumo:", style='Ingreso.SectionLabel.TLabel').grid(row=0, column=0, padx=3, pady=(1,1), sticky="w")
        self.tipo_insumo_cb = AutocompleteCombobox(insumos_content, textvariable=self.tipo_insumo_var,
                                                   completevalues=[], state="normal", font=('Segoe UI', 8))
        self.tipo_insumo_cb.grid(row=1, column=0, columnspan=2, padx=3, pady=(1,2), sticky="ew")

        ttk.Label(insumos_content, text="Insumo:", style='Ingreso.SectionLabel.TLabel').grid(row=0, column=2, padx=3, pady=(1,1), sticky="w")
        self.insumo_cb = AutocompleteCombobox(insumos_content, textvariable=self.insumo_var,
                                              completevalues=[], state="normal", font=('Segoe UI', 8))
        self.insumo_cb.grid(row=1, column=2, columnspan=4, padx=3, pady=(1,2), sticky="ew")
        self.tooltip_insumo = HoverTooltip(self.insumo_cb, text_provider=lambda: self.insumo_var.get(),
                                           delay=250, show_only_if_clipped=True)

        ttk.Label(insumos_content, text="Presentación:", style='Ingreso.SectionLabel.TLabel').grid(row=0, column=6, padx=3, pady=(1,1), sticky="w")
        self.presentacion_cb = AutocompleteCombobox(insumos_content, textvariable=self.presentacion_var,
                                                    completevalues=[], state="normal", font=('Segoe UI', 8))
        self.presentacion_cb.grid(row=1, column=6, columnspan=2, padx=3, pady=(1,2), sticky="ew")

        # Segunda fila: Lote y Vencimiento
        ttk.Label(insumos_content, text="Lote:", style='Ingreso.SectionLabel.TLabel').grid(row=2, column=0, padx=4, pady=(2,1), sticky="w")
        frame_lote = ttk.Frame(insumos_content, style='Ingreso.Main.TFrame')
        frame_lote.grid(row=3, column=0, columnspan=4, padx=4, pady=(1,2), sticky="ew")
        frame_lote.columnconfigure(0, weight=1)

        self.lote_entry = ttk.Entry(frame_lote, textvariable=self.lote_var, font=('Segoe UI', 8))
        self.lote_entry.grid(row=0, column=0, padx=(0, 8), pady=0, sticky="ew")

        self.sin_lote_var = tk.BooleanVar()
        tk.Checkbutton(frame_lote, text="Sin lote",
                       variable=self.sin_lote_var,
                       command=lambda: self.lote_entry.config(state='disabled' if self.sin_lote_var.get() else 'normal'),
                       font=('Segoe UI', 8),
                       bg=self.COLORS['light'], fg=self.COLORS['text_dark'],
                       selectcolor=self.COLORS['white'], activebackground=self.COLORS['white']).grid(row=0, column=1, sticky="w", padx=0, pady=0)

        ttk.Label(insumos_content, text="Fecha Vencimiento:", style='Ingreso.SectionLabel.TLabel').grid(row=2, column=4, padx=4, pady=(2,1), sticky="w")
        frame_fecha = ttk.Frame(insumos_content, style='Ingreso.Main.TFrame')
        frame_fecha.grid(row=3, column=4, columnspan=4, padx=4, pady=(1,2), sticky="ew")
        frame_fecha.columnconfigure(0, weight=1)

        self.fecha_venc = DateEntry(frame_fecha, width=12, background='darkblue', foreground='white',
                                    borderwidth=2, date_pattern='dd/mm/yyyy', font=('Segoe UI', 8))
        self.fecha_venc.grid(row=0, column=0, padx=(0, 8), pady=0, sticky="ew")

        self.sin_fecha_venc = tk.BooleanVar(value=False)
        tk.Checkbutton(frame_fecha, text="Sin fecha",
                       variable=self.sin_fecha_venc, command=self.toggle_fecha_vencimiento,
                       font=('Segoe UI', 8),
                       bg=self.COLORS['light'], fg=self.COLORS['text_dark'],
                       selectcolor=self.COLORS['white'], activebackground=self.COLORS['white']).grid(row=0, column=1, sticky="w", padx=0, pady=0)

        # Registro de movimiento
        registro_container = ttk.Frame(self.scrollable_frame, style='Ingreso.Main.TFrame')
        registro_container.pack(fill="x", padx=15, pady=2)

        self.frame_registro = ttk.Frame(registro_container, style='Ingreso.Card.TFrame')
        self.frame_registro.pack(fill="x", padx=8, pady=2)

        registro_header = ttk.Frame(self.frame_registro, style='Ingreso.Header.TFrame', height=16)
        registro_header.pack(fill='x')
        registro_header.pack_propagate(False)
        ttk.Label(registro_header, text="📋 Registro de Movimiento", style='Ingreso.Header.TLabel').pack(side='left', padx=10, pady=0)

        registro_content = ttk.Frame(self.frame_registro, style='Ingreso.Main.TFrame')
        registro_content.pack(fill='x', padx=12, pady=2)

        for i in range(5):
            registro_content.columnconfigure(i, weight=1, uniform="registro_group")

        ttk.Label(registro_content, text="Fecha de Registro:", style='Ingreso.SectionLabel.TLabel').grid(row=0, column=0, padx=4, pady=(1,1), sticky="w")
        self.fecha_reg = DateEntry(registro_content, width=16, background='darkblue', foreground='white',
                                   borderwidth=2, date_pattern='dd/mm/yyyy', font=('Segoe UI', 8))
        self.fecha_reg.grid(row=1, column=0, padx=4, pady=(1,2), sticky="ew")

        ttk.Label(registro_content, text="Referencia:", style='Ingreso.SectionLabel.TLabel').grid(row=0, column=1, padx=4, pady=(1,1), sticky="w")
        self.referencia_entry = ttk.Entry(registro_content, font=('Segoe UI', 8))
        self.referencia_entry.grid(row=1, column=1, padx=4, pady=(1,2), sticky="ew")

        ttk.Label(registro_content, text="Tipo de Movimiento:", style='Ingreso.SectionLabel.TLabel').grid(row=0, column=2, padx=4, pady=(1,1), sticky="w")
        self.tipo_mov_cb = AutocompleteCombobox(registro_content, textvariable=self.tipo_movimiento_var,
                                                completevalues=[], state="normal", font=('Segoe UI', 8))
        self.tipo_mov_cb.grid(row=1, column=2, padx=4, pady=(1,2), sticky="ew")

        ttk.Label(registro_content, text="Cantidad:", style='Ingreso.SectionLabel.TLabel').grid(row=0, column=3, padx=4, pady=(1,1), sticky="w")
        self.cantidad_entry = ttk.Entry(registro_content, font=('Segoe UI', 8))
        self.cantidad_entry.grid(row=1, column=3, padx=4, pady=(1,2), sticky="ew")

        ttk.Label(registro_content, text="Observaciones:", style='Ingreso.SectionLabel.TLabel').grid(row=0, column=4, padx=4, pady=(1,1), sticky="w")
        self.observaciones_entry = ttk.Entry(registro_content, font=('Segoe UI', 8))
        self.observaciones_entry.grid(row=1, column=4, padx=4, pady=(1,2), sticky="ew")

        # Salida a Nivel Inferior
        self.salida_container = ttk.Frame(self.scrollable_frame, style='Ingreso.Main.TFrame')
        self.salida_container.pack(fill="x", padx=15, pady=2)

        self.frame_salida_nivel_inferior = ttk.Frame(self.salida_container, style='Ingreso.Card.TFrame')
        self.frame_salida_nivel_inferior.pack(fill="x", padx=8, pady=2)

        salida_header = ttk.Frame(self.frame_salida_nivel_inferior, style='Ingreso.Header.TFrame', height=16)
        salida_header.pack(fill='x')
        salida_header.pack_propagate(False)
        ttk.Label(salida_header, text="🔄 Salida a Nivel Inferior", style='Ingreso.Header.TLabel').pack(side='left', padx=8, pady=0)

        salida_content = ttk.Frame(self.frame_salida_nivel_inferior, style='Ingreso.Main.TFrame')
        salida_content.pack(fill='x', padx=10, pady=2)

        for i in range(3):
            salida_content.columnconfigure(i, weight=1, uniform="salida_group")

        ttk.Label(salida_content, text="Distrito:", style='Ingreso.SectionLabel.TLabel').grid(row=0, column=0, padx=4, pady=(1,1), sticky="w")
        self.salida_distrito_cb = AutocompleteCombobox(salida_content, textvariable=self.salida_distrito_var,
                                                       completevalues=[], state="disabled", font=('Segoe UI', 8))
        self.salida_distrito_cb.grid(row=1, column=0, padx=4, pady=(1,2), sticky="ew")

        ttk.Label(salida_content, text="Tipo de Servicio:", style='Ingreso.SectionLabel.TLabel').grid(row=0, column=1, padx=4, pady=(1,1), sticky="w")
        self.salida_tipo_servicio_cb = AutocompleteCombobox(salida_content, textvariable=self.salida_tipo_servicio_var,
                                                            completevalues=[], state="disabled", font=('Segoe UI', 8))
        self.salida_tipo_servicio_cb.grid(row=1, column=1, padx=4, pady=(1,2), sticky="ew")

        ttk.Label(salida_content, text="Servicio:", style='Ingreso.SectionLabel.TLabel').grid(row=0, column=2, padx=4, pady=(1,1), sticky="w")
        self.salida_servicio_cb = AutocompleteCombobox(salida_content, textvariable=self.salida_servicio_var,
                                                       completevalues=[], state="disabled", font=('Segoe UI', 8))
        self.salida_servicio_cb.grid(row=1, column=2, padx=4, pady=(1,2), sticky="ew")

        # Botón Agregar
        btn_container = ttk.Frame(self.scrollable_frame, style='Ingreso.Main.TFrame')
        btn_container.pack(fill="x", padx=20, pady=1)

        btn_inner = ttk.Frame(btn_container, style='Ingreso.Main.TFrame')
        btn_inner.pack(padx=8, pady=1)

        self.btn_agregar = tk.Button(btn_inner, text="Agregar Movimiento", image=self.icon_agregar, compound='left',
                                     command=self.agregar_movimiento,
                                     font=('Segoe UI', 8, 'bold'),
                                     bg=self.COLORS['light'], fg=self.COLORS['text_dark'],
                                     relief='flat', borderwidth=0, highlightthickness=0,
                                     padx=18, pady=4, cursor='hand2')
        self.btn_agregar.pack()

        # Listado
        movimientos_container = ttk.Frame(self.scrollable_frame, style='Ingreso.Main.TFrame')
        movimientos_container.pack(fill="x", padx=15, pady=1)

        self.frame_movimientos = ttk.Frame(movimientos_container, style='Ingreso.Card.TFrame')
        self.frame_movimientos.pack(fill="x", padx=8, pady=2)

        movimientos_header = ttk.Frame(self.frame_movimientos, style='Ingreso.Header.TFrame', height=22)
        movimientos_header.pack(fill='x')
        movimientos_header.pack_propagate(False)
        ttk.Label(movimientos_header, text="📊 Listado de Movimientos",
                  style='Ingreso.Header.TLabel').pack(side='left', padx=10, pady=2)

        tree_content = ttk.Frame(self.frame_movimientos, style='Ingreso.Main.TFrame')
        tree_content.pack(fill="both", expand=True, padx=8, pady=4)

        columns = (
            'fecha_registro', 'referencia', 'tipo_movimiento', 'insumo', 'presentacion', 'servicio',
            'lote', 'fecha_vencimiento', 'cantidad', 'salida_distrito', 'salida_servicio',
            'observaciones', 'tipo_insumo', 'area', 'distrito', 'tipo_servicio'
        )

        tree_content.grid_rowconfigure(0, weight=1)
        tree_content.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_content, columns=columns, show='headings', height=6, style="Ingreso.Treeview")

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

        anchos_columnas = {
            'fecha_registro': 140,
            'referencia': 120,
            'tipo_movimiento': 150,
            'insumo': 260,
            'presentacion': 110,
            'servicio': 180,
            'lote': 100,
            'fecha_vencimiento': 140,
            'cantidad': 100,
            'salida_distrito': 150,
            'salida_servicio': 150,
            'observaciones': 250,
            'tipo_insumo': 110,
            'area': 120,
            'distrito': 120,
            'tipo_servicio': 150
        }

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
            self.tree.column(col, width=anchos_columnas[col], minwidth=80, anchor=justificacion[col])

        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar_y = ttk.Scrollbar(tree_content, orient="vertical", command=self.tree.yview)
        scrollbar_y.grid(row=0, column=1, sticky="ns")

        scrollbar_x = ttk.Scrollbar(tree_content, orient="horizontal", command=self.tree.xview)
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # Binds locales del tree (evita bind_all)
        def on_treeview_mousewheel(event):
            try:
                self.tree.yview_scroll(int(-1*(event.delta/120)), "units")
            except Exception:
                pass
            return "break"

        self._tree_on_mousewheel = on_treeview_mousewheel
        self.tree.bind("<MouseWheel>", self._tree_on_mousewheel)

        # Botones inferiores
        botones_container = ttk.Frame(self.scrollable_frame, style='Ingreso.Main.TFrame')
        botones_container.pack(fill="x", padx=15, pady=2)

        self.frame_botones = ttk.Frame(botones_container, style='Ingreso.Main.TFrame')
        self.frame_botones.pack(fill="x", padx=8, pady=2)

        botones_inner = ttk.Frame(self.frame_botones, style='Ingreso.Main.TFrame')
        botones_inner.pack(expand=True, pady=3)

        self.btn_editar = tk.Button(botones_inner, text="Editar", image=self.icon_editar, compound='left',
                                    command=self.editar_movimiento,
                                    font=('Segoe UI', 9, 'bold'),
                                    bg=self.COLORS['light'], fg=self.COLORS['text_dark'],
                                    relief='flat', borderwidth=0, highlightthickness=0,
                                    padx=10, pady=3, cursor='hand2')
        self.btn_editar.pack(side="left", padx=10)

        self.btn_eliminar = tk.Button(botones_inner, text="Eliminar", image=self.icon_eliminar, compound='left',
                                      command=self.eliminar_movimiento,
                                      font=('Segoe UI', 9, 'bold'),
                                      bg=self.COLORS['light'], fg=self.COLORS['text_dark'],
                                      relief='flat', borderwidth=0, highlightthickness=0,
                                      padx=10, pady=3, cursor='hand2')
        self.btn_eliminar.pack(side="left", padx=10)

        self.btn_guardar = tk.Button(botones_inner, text="Guardar", image=self.icon_guardar, compound='left',
                                     command=self.guardar_movimientos,
                                     font=('Segoe UI', 9, 'bold'),
                                     bg=self.COLORS['light'], fg=self.COLORS['text_dark'],
                                     relief='flat', borderwidth=0, highlightthickness=0,
                                     padx=10, pady=3, cursor='hand2')
        self.btn_guardar.pack(side="left", padx=10)

        self.btn_cerrar = tk.Button(botones_inner, text="Cerrar", image=self.icon_cerrar, compound='left',
                                    command=self.cerrar_ventana,
                                    font=('Segoe UI', 9, 'bold'),
                                    bg=self.COLORS['light'], fg=self.COLORS['text_dark'],
                                    relief='flat', borderwidth=0, highlightthickness=0,
                                    padx=10, pady=3, cursor='hand2')
        self.btn_cerrar.pack(side="right", padx=10)

    def _trace(self, var, mode, cb):
        cbname = var.trace_add(mode, cb)
        self._trace_ids.append((var, mode, cbname))

    def setup_bindings(self):
        # Registrar traces y guardar IDs para limpieza
        self._trace(self.area_var, 'write', self.on_area_selected)
        self._trace(self.distrito_var, 'write', self.actualizar_tipos_servicio)
        self._trace(self.tipo_servicio_var, 'write', self.actualizar_servicios)
        self._trace(self.tipo_insumo_var, 'write', self._on_tipo_insumo_changed)
        self._trace(self.insumo_var, 'write', self._on_insumo_changed)
        # Refuerzo: si cambia la presentación, recalculamos (no debería afectar, pero mantiene consistencia)
        self._trace(self.presentacion_var, 'write', lambda *a: self.actualizar_tipos_movimiento_filtrados())

        self._trace(self.tipo_movimiento_var, 'write', lambda *args: self.actualizar_estado_salida_nivel_inferior())
        self._trace(self.nivel_bodega_var, 'write', lambda *args: (self.actualizar_estado_comboboxes(), self.actualizar_tipos_movimiento_filtrados()))

        self._trace(self.salida_distrito_var, 'write', self.actualizar_tipos_servicio_salida)
        self._trace(self.salida_tipo_servicio_var, 'write', self.actualizar_servicios_salida)

    # Cache mínimo en sesión para no consultar cada vez
    _cache_inventario_inicial_por_insumo = {}

    def _insumo_tiene_inventario_inicial(self):
        return self._insumo_tiene_inventario_inicial_por_desc(
            (self.tipo_insumo_var.get() or '').strip(),
            (self.insumo_var.get() or '').strip()
        )

    def _insumo_tiene_inventario_inicial_por_desc(self, tipo_insumo_desc, insumo_nombre):
        tipo_insumo_desc = (tipo_insumo_desc or '').strip()
        insumo_nombre = (insumo_nombre or '').strip()
        if not tipo_insumo_desc or not insumo_nombre:
            return False
        key = (tipo_insumo_desc, insumo_nombre)
        if key in self._cache_inventario_inicial_por_insumo:
            return self._cache_inventario_inicial_por_insumo[key]
        tipo_insumo_id = cache.tipo_insumo_id(tipo_insumo_desc)
        if not tipo_insumo_id:
            self._cache_inventario_inicial_por_insumo[key] = False
            return False
        insumo_id = cache.insumo_id(insumo_nombre, tipo_insumo_id)
        if not insumo_id:
            insumos = obtener_insumos_por_tipo(tipo_insumo_id) or []
            target = insumo_nombre.strip().casefold()
            insumo_id = next((i['id'] for i in insumos if (i.get('nombre') or '').strip().casefold() == target), None)
            if not insumo_id:
                self._cache_inventario_inicial_por_insumo[key] = False
                return False
        conn = None
        try:
            from src.database.db_manager import conectar_db
            conn = conectar_db()
            if not conn:
                self._cache_inventario_inicial_por_insumo[key] = False
                return False
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT COUNT(*) AS cnt
                FROM movimiento m
                JOIN tipo_movimiento tm ON tm.id = m.tipo_movimiento_id
                WHERE m.insumo_id = %s AND UPPER(TRIM(tm.descripcion)) = 'INVENTARIO INICIAL'
                LIMIT 1
            """, (insumo_id,))
            row = cur.fetchone()
            existe = bool(row and row.get('cnt', 0) > 0)
            self._cache_inventario_inicial_por_insumo[key] = existe
            return existe
        except Exception:
            self._cache_inventario_inicial_por_insumo[key] = False
            return False
        finally:
            try:
                if conn:
                    conn.close()
            except Exception:
                pass

    def _invalidate_inventario_inicial_cache_for_current(self):
        ti = (self.tipo_insumo_var.get() or '').strip()
        ins = (self.insumo_var.get() or '').strip()
        if ti or ins:
            self._cache_inventario_inicial_por_insumo.pop((ti, ins), None)

    def _on_tipo_insumo_changed(self, *args):
        self._invalidate_inventario_inicial_cache_for_current()
        self.actualizar_insumos()
        self.actualizar_tipos_movimiento_filtrados()

    def _on_insumo_changed(self, *args):
        self._invalidate_inventario_inicial_cache_for_current()
        self.actualizar_presentacion()
        self.actualizar_tipos_movimiento_filtrados()

    def _resolver_insumo_id_robusto(self, tipo_insumo_desc, insumo_nombre):
        """
        Devuelve insumo_id a partir de descripciones, buscando primero en cache y luego en BD con matching robusto.
        """
        tipo_insumo_desc = (tipo_insumo_desc or '').strip()
        insumo_nombre = (insumo_nombre or '').strip()
        if not tipo_insumo_desc or not insumo_nombre:
            return None

        tipo_insumo_id = cache.tipo_insumo_id(tipo_insumo_desc)
        if not tipo_insumo_id:
            return None

        insumo_id = cache.insumo_id(insumo_nombre, tipo_insumo_id)
        if insumo_id:
            return insumo_id

        # Fallback robusto por nombre
        try:
            insumos = obtener_insumos_por_tipo(tipo_insumo_id) or []
            target = insumo_nombre.strip().casefold()
            insumo_id = next((i['id'] for i in insumos if (i.get('nombre') or '').strip().casefold() == target), None)
            return insumo_id
        except Exception:
            return None
    
    def _obtener_saldo_actual(self, nivel, area_id, distrito_id, tipo_servicio_id, servicio_id, insumo_id):
        """
        Calcula el saldo acumulado en BD para el insumo dado, restringido al nivel:
        - area: area_id
        - distrito: area_id + distrito_id
        - servicio: area_id + distrito_id + servicio_id
        saldo = sum(positivos) - sum(negativos)
        """
        if not insumo_id or not area_id:
            return 0.0

        # Normalizados
        POSITIVOS = ("INVENTARIO INICIAL", "ENTRADA NIVEL SUPERIOR", "REAJUSTE (+)")
        NEGATIVOS = ("SALIDA NIVEL INFERIOR", "REAJUSTE (-)", "ENTREGADO")

        condiciones = ["m.insumo_id = %s", "m.area_id = %s"]
        params_where = [insumo_id, area_id]

        if nivel in ('distrito', 'servicio'):
            if not distrito_id:
                return 0.0
            condiciones.append("m.distrito_id = %s")
            params_where.append(distrito_id)

        if nivel == 'servicio':
            if not servicio_id:
                return 0.0
            condiciones.append("m.servicio_id = %s")
            params_where.append(servicio_id)

        where_clause = " AND ".join(condiciones)

        sql = f"""
            SELECT
                COALESCE(SUM(CASE WHEN UPPER(TRIM(tm.descripcion)) IN (%s, %s, %s) THEN m.cantidad ELSE 0 END), 0)
            - COALESCE(SUM(CASE WHEN UPPER(TRIM(tm.descripcion)) IN (%s, %s, %s) THEN m.cantidad ELSE 0 END), 0)
            AS saldo
            FROM movimiento m
            JOIN tipo_movimiento tm ON tm.id = m.tipo_movimiento_id
            WHERE {where_clause}
        """

        params = list(POSITIVOS) + list(NEGATIVOS) + params_where

        conn = None
        try:
            from src.database.db_manager import conectar_db
            conn = conectar_db()
            if not conn:
                return 0.0
            cur = conn.cursor(buffered=True)
            cur.execute(sql, params)
            row = cur.fetchone()
            return float(row[0]) if row and row[0] is not None else 0.0
        except Exception as e:
            print(f"Error _obtener_saldo_actual: {e}")
            return 0.0
        finally:
            try:
                if conn:
                    conn.close()
            except Exception:
                pass
    
    def _saldo_virtual_treeview(self, nivel, area_id, distrito_id, tipo_servicio_id, servicio_id, insumo_id, excluir_item=None):
        """
        Suma el saldo de los movimientos en el TreeView (no guardados en BD) que aplican
        al mismo contexto e insumo. Usa la misma lógica de positivos/negativos.
        
        excluir_item: ID del item del TreeView a excluir del cálculo (para evitar contar dos veces)
        """
        if not insumo_id or not area_id:
            return 0.0

        def norm(s): return (s or '').strip().upper()
        POSITIVOS = {"INVENTARIO INICIAL", "ENTRADA NIVEL SUPERIOR", "REAJUSTE (+)"}
        NEGATIVOS = {"SALIDA NIVEL INFERIOR", "REAJUSTE (-)", "ENTREGADO"}

        saldo = 0.0
        for item in self.tree.get_children():
            # Excluir el item especificado
            if excluir_item and item == excluir_item:
                continue
                
            vals = self.tree.item(item)['values']
            try:
                tipo_mov_desc = norm(vals[2])
                insumo_nombre = (vals[3] or '').strip()
                presentacion_nombre = (vals[4] or '').strip()  # noqa: F841
                servicio_nombre = (vals[5] or '').strip()
                cantidad = float(vals[8])
                tipo_insumo_desc = (vals[12] or '').strip()
                area_nombre = (vals[13] or '').strip()
                distrito_nombre = (vals[14] or '').strip()
                tipo_servicio_desc = (vals[15] or '').strip()

                # Resolver IDs
                area_id_i = cache.area_id(area_nombre) if area_nombre else None
                distrito_id_i = cache.distrito_id(distrito_nombre) if distrito_nombre else None

                tipo_servicio_id_i = None
                if tipo_servicio_desc and distrito_id_i:
                    tipo_servicio_id_i = cache.tipo_servicio_id(tipo_servicio_desc, distrito_id_i)
                    if tipo_servicio_id_i is None:
                        tipos = obtener_tipos_servicio_por_distrito(distrito_id_i) or []
                        tipo_servicio_id_i = next((ts['id'] for ts in tipos if ts['descripcion'] == tipo_servicio_desc), None)

                servicio_id_i = None
                if servicio_nombre and tipo_servicio_id_i:
                    servicio_id_i = cache.servicio_id(servicio_nombre, tipo_servicio_id_i)
                    if servicio_id_i is None:
                        servicios = obtener_servicios_por_tipo(tipo_servicio_id_i) or []
                        servicio_id_i = next((s['id'] for s in servicios if s['nombre'] == servicio_nombre), None)

                insumo_id_i = self._resolver_insumo_id_robusto(tipo_insumo_desc, insumo_nombre)

                # Debe ser el mismo insumo y mismo contexto
                if insumo_id_i != insumo_id:
                    continue
                if area_id_i != area_id:
                    continue
                if nivel in ('distrito', 'servicio'):
                    if distrito_id_i != distrito_id:
                        continue
                if nivel == 'servicio':
                    if tipo_servicio_id_i != tipo_servicio_id or servicio_id_i != servicio_id:
                        continue

                if tipo_mov_desc in POSITIVOS:
                    saldo += cantidad
                elif tipo_mov_desc in NEGATIVOS:
                    saldo -= cantidad
            except Exception:
                continue
        return saldo
    
    def before_destroy(self):
        # 1) Quitar traces
        try:
            if self._trace_ids:
                for var, mode, cbname in self._trace_ids:
                    try:
                        var.trace_remove(mode, cbname)
                    except Exception:
                        pass
                self._trace_ids.clear()
        except Exception:
            pass

        # 2) Unbind eventos del Treeview
        try:
            if hasattr(self, 'tree') and self.tree and self.tree.winfo_exists():
                try:
                    self.tree.unbind("<MouseWheel>")
                except Exception:
                    pass
                if self._enter_bind_id:
                    try:
                        self.tree.unbind('<Enter>', self._enter_bind_id)
                    except Exception:
                        pass
                    self._enter_bind_id = None
                if self._leave_bind_id:
                    try:
                        self.tree.unbind('<Leave>', self._leave_bind_id)
                    except Exception:
                        pass
                    self._leave_bind_id = None
        except Exception:
            pass

        # 3) Cerrar tooltip
        try:
            if hasattr(self, 'tooltip_insumo') and self.tooltip_insumo:
                try:
                    self.tooltip_insumo._hide()
                except Exception:
                    pass
                self.tooltip_insumo = None
        except Exception:
            pass

        # 4) Cancelar afters si usas
        try:
            if self._after_update_id:
                self.parent.after_cancel(self._after_update_id)
                self._after_update_id = None
        except Exception:
            pass

        # 5) Cerrar Toplevels abiertos
        try:
            if self._open_toplevels:
                for tl in list(self._open_toplevels):
                    try:
                        if tl and tl.winfo_exists():
                            tl.destroy()
                    except Exception:
                        pass
                self._open_toplevels.clear()
        except Exception:
            pass

    def actualizar_estado_comboboxes(self):
        if not hasattr(self, 'area_cb'):
            return
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

        self.actualizar_tipos_movimiento_filtrados()
        self.actualizar_estado_salida_nivel_inferior()

        if nivel == "distrito" and self.tipo_movimiento_var.get().strip().upper() == "SALIDA NIVEL INFERIOR":
            self.salida_distrito_var.set(self.distrito_var.get())
            self.actualizar_tipos_servicio_salida()

    def actualizar_estado_salida_nivel_inferior(self):
        if not hasattr(self, 'salida_distrito_cb'):
            return
        tipo_mov = self.tipo_movimiento_var.get().strip().upper()
        nivel = self.nivel_bodega_var.get()

        if tipo_mov == "SALIDA NIVEL INFERIOR":
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
        else:
            self.salida_distrito_cb.config(state="disabled")
            self.salida_tipo_servicio_cb.config(state="disabled")
            self.salida_servicio_cb.config(state="disabled")
            self.salida_distrito_var.set('')
            self.salida_tipo_servicio_var.set('')
            self.salida_servicio_var.set('')

        self.actualizar_altura_treeview()

    def actualizar_altura_treeview(self):
        if hasattr(self, 'tree'):
            self.tree.configure(height=6)

    def actualizar_tipos_movimiento_filtrados(self):
        """
        Llena el combo de tipos de movimiento cumpliendo:
        - En nivel Área y Distrito: ocultar 'ENTREGADO' y 'NO ENTREGADO'.
        - En nivel Servicio: ocultar 'SALIDA NIVEL INFERIOR'.
        - Orden deseado: primero positivos (INVENTARIO INICIAL, ENTRADA NIVEL SUPERIOR, REAJUSTE POSITIVO),
                        luego negativos (SALIDA NIVEL INFERIOR, REAJUSTE NEGATIVO, ENTREGADO),
                        finalmente indiferentes (NO ENTREGADO).
        - Si el insumo ya tiene 'INVENTARIO INICIAL' guardado, ocultarlo de la lista.
        """
        if not hasattr(self, 'tipo_mov_cb'):
            return

        # Obtener todos los tipos desde la BD
        tipos_raw = [tm['descripcion'] for tm in (obtener_tipos_movimiento() or [])]

        # Normalizaciones útiles
        def norm(s): return (s or '').strip().upper()

        # Particiones
        POSITIVOS = ["INVENTARIO INICIAL", "ENTRADA NIVEL SUPERIOR", "REAJUSTE (+)"]
        NEGATIVOS = ["SALIDA NIVEL INFERIOR", "REAJUSTE (-)", "ENTREGADO"]
        INDIFERENTES = ["NO ENTREGADO"]

        # Conjuntos normalizados
        pos_set = {norm(x) for x in POSITIVOS}
        neg_set = {norm(x) for x in NEGATIVOS}
        ind_set = {norm(x) for x in INDIFERENTES}

        nivel = self.nivel_bodega_var.get()

        # Filtrado por nivel
        filtrados = []
        for t in tipos_raw:
            t_up = norm(t)
            if nivel in ("area", "distrito"):
                # Ocultar ENTREGADO y NO ENTREGADO
                if t_up == "ENTREGADO" or t_up == "NO ENTREGADO":
                    continue
            elif nivel == "servicio":
                # Ocultar SALIDA NIVEL INFERIOR
                if t_up == "SALIDA NIVEL INFERIOR":
                    continue
            filtrados.append(t)

        # Ocultar INVENTARIO INICIAL si ya existe para el insumo seleccionado
        try:
            if self._insumo_tiene_inventario_inicial():
                filtrados = [t for t in filtrados if norm(t) != "INVENTARIO INICIAL"]
        except Exception:
            pass

        # Ordenar según prioridad
        def orden_clave(t):
            tu = norm(t)
            if tu in pos_set:
                order_map = {
                    "INVENTARIO INICIAL": 1,
                    "ENTRADA NIVEL SUPERIOR": 2,
                    "REAJUSTE (+)": 3
                }
                return (1, order_map.get(tu, 99), tu)
            if tu in neg_set:
                order_map = {
                    "SALIDA NIVEL INFERIOR": 1,
                    "REAJUSTE (-)": 2,
                    "ENTREGADO": 3
                }
                return (2, order_map.get(tu, 99), tu)
            if tu in ind_set:
                order_map = {
                    "NO ENTREGADO": 1
                }
                return (3, order_map.get(tu, 99), tu)
            return (4, 99, tu)

        filtrados.sort(key=orden_clave)

        # Aplicar a combobox
        self.tipo_mov_cb.config(completevalues=filtrados)

        # Reset si el valor ya no está en la lista
        if self.tipo_movimiento_var.get() not in filtrados:
            self.tipo_movimiento_var.set('')
        
    def actualizar_tipos_servicio(self, *args):
        if not hasattr(self, 'tipo_servicio_cb'):
            return
        distrito_nombre = self.distrito_var.get()
        distrito_id = cache.distrito_id(distrito_nombre)
        if distrito_id:
            tipos_servicio = cache.get_tipos_servicio_por_distrito(distrito_id) or []
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
        if not hasattr(self, 'servicio_cb'):
            return
        distrito_nombre = self.distrito_var.get()
        tipo_servicio_desc = self.tipo_servicio_var.get()
        distrito_id = cache.distrito_id(distrito_nombre)
        if distrito_id:
            tipo_servicio_id = cache.tipo_servicio_id(tipo_servicio_desc, distrito_id)
            if tipo_servicio_id:
                servicios = cache.get_servicios_por_tipo(tipo_servicio_id) or []
                opciones = [s['nombre'] for s in servicios]
                self.servicio_cb.config(completevalues=opciones)
                self.servicio_var.set('')
                return
        self.servicio_cb.config(completevalues=[])
        self.servicio_var.set('')

    def actualizar_insumos(self, *args):
        if not hasattr(self, 'insumo_cb'):
            return
        tipo_insumo_desc = self.tipo_insumo_var.get()
        tipo_insumo_id = cache.tipo_insumo_id(tipo_insumo_desc)
        if tipo_insumo_id:
            insumos = cache.get_insumos_por_tipo(tipo_insumo_id) or []
            opciones = [i['nombre'] for i in insumos]
            self.insumo_cb.config(completevalues=opciones)
            self.insumo_var.set('')
        else:
            self.insumo_cb.config(completevalues=[])
            self.insumo_var.set('')

    def actualizar_presentacion(self, *args):
        if not hasattr(self, 'presentacion_cb'):
            return
        tipo_insumo_desc = self.tipo_insumo_var.get()
        insumo_nombre = self.insumo_var.get()
        tipo_insumo_id = cache.tipo_insumo_id(tipo_insumo_desc)
        if tipo_insumo_id and insumo_nombre:
            insumos = cache.get_insumos_por_tipo(tipo_insumo_id) or []
            insumo_sel = next((i for i in insumos if i['nombre'] == insumo_nombre), None)
            if insumo_sel and insumo_sel.get('nombre_presentacion'):
                self.presentacion_cb.config(completevalues=[insumo_sel['nombre_presentacion']])
                self.presentacion_var.set(insumo_sel['nombre_presentacion'])
                return
        self.presentacion_cb.config(completevalues=[])
        self.presentacion_var.set('')

    def actualizar_tipos_servicio_salida(self, *args):
        if not hasattr(self, 'salida_tipo_servicio_cb'):
            return
        distrito_nombre = self.salida_distrito_var.get()
        distrito_id = cache.distrito_id(distrito_nombre)
        if distrito_id:
            tipos_servicio = cache.get_tipos_servicio_por_distrito(distrito_id) or []
            opciones = [ts['descripcion'] for ts in tipos_servicio]
            self.salida_tipo_servicio_cb.config(completevalues=opciones)
            if self.salida_tipo_servicio_var.get() not in opciones:
                self.salida_tipo_servicio_var.set('')
                self.salida_servicio_var.set('')
        else:
            self.salida_tipo_servicio_cb.config(completevalues=[])
            self.salida_tipo_servicio_var.set('')
            self.salida_servicio_cb.config(completevalues=[])
            self.salida_servicio_var.set('')

    def actualizar_servicios_salida(self, *args):
        if not hasattr(self, 'salida_servicio_cb'):
            return
        distrito_nombre = self.salida_distrito_var.get()
        tipo_servicio_desc = self.salida_tipo_servicio_var.get()
        distrito_id = cache.distrito_id(distrito_nombre)
        if distrito_id:
            tipo_servicio_id = cache.tipo_servicio_id(tipo_servicio_desc, distrito_id)
            if tipo_servicio_id:
                servicios = cache.get_servicios_por_tipo(tipo_servicio_id) or []
                opciones = [s['nombre'] for s in servicios]
                self.salida_servicio_cb.config(completevalues=opciones)
                if self.salida_servicio_var.get() not in opciones:
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

    def _validar_previas_para_salida(self):
        tipo_mov = self.tipo_movimiento_var.get().strip().upper()
        if tipo_mov != "SALIDA NIVEL INFERIOR":
            return True

        nivel = self.nivel_bodega_var.get()
        if nivel == "area":
            if not self.salida_distrito_var.get().strip():
                messagebox.showerror("Requisito", "Debe seleccionar un Distrito (Salida) antes de continuar.")
                self.salida_distrito_cb.focus_set()
                return False
        elif nivel == "distrito":
            if not self.salida_servicio_var.get().strip():
                messagebox.showerror("Requisito", "Debe seleccionar un Servicio (Salida) antes de continuar.")
                self.salida_servicio_cb.focus_set()
                return False
        return True

    def agregar_movimiento(self):
        try:
            if not self._validar_previas_para_salida():
                return

            fecha_registro = self.fecha_reg.get_date().strftime('%d/%m/%Y')
            tipo_movimiento = (self.tipo_movimiento_var.get() or '').strip()
            tipo_mov_up = tipo_movimiento.upper()
            tipo_insumo = (self.tipo_insumo_var.get() or '').strip()
            insumo = (self.insumo_var.get() or '').strip()
            presentacion = (self.presentacion_var.get() or '').strip()
            lote = "N/A" if self.sin_lote_var.get() else (self.lote_entry.get() or '').upper().strip()
            fecha_venc_str = "N/A" if self.sin_fecha_venc.get() else self.fecha_venc.get_date().strftime('%d/%m/%Y')
            cantidad_str = (self.cantidad_entry.get() or '').strip()
            referencia = (self.referencia_entry.get() or '').upper().strip()
            observaciones = (self.observaciones_entry.get() or '').upper().strip()

            area = (self.area_var.get() or '').strip()
            distrito = (self.distrito_var.get() or '').strip()
            tipo_servicio = (self.tipo_servicio_var.get() or '').strip()
            servicio = (self.servicio_var.get() or '').strip()

            salida_distrito = ''
            salida_servicio = ''
            if tipo_mov_up == "SALIDA NIVEL INFERIOR":
                salida_distrito = (self.salida_distrito_var.get() or '').strip()
                salida_servicio = (self.salida_servicio_var.get() or '').strip()

            if not tipo_insumo:
                messagebox.showerror("Error", "Debe seleccionar un tipo de insumo")
                return

            if not all([tipo_movimiento, insumo, presentacion, lote, cantidad_str, referencia]):
                messagebox.showerror("Error", "Los campos son requeridos excepto observaciones")
                return
            
            cantidad = float(cantidad_str)
            if cantidad <= 0:
                messagebox.showerror("Error", "La cantidad debe ser un número positivo")
                return

            # Validación de saldo previo si el movimiento es negativo
            NEGATIVOS = {"SALIDA NIVEL INFERIOR", "REAJUSTE (-)", "ENTREGADO"}
            if tipo_mov_up in NEGATIVOS:
                # Resolver IDs de contexto según nivel
                nivel_val = self.nivel_bodega_var.get()
                area_id = cache.area_id(area) if area else None
                distrito_id = cache.distrito_id(distrito) if distrito else None

                tipo_servicio_id = None
                if tipo_servicio and distrito_id:
                    tipo_servicio_id = cache.tipo_servicio_id(tipo_servicio, distrito_id)
                    if tipo_servicio_id is None:
                        tipos = obtener_tipos_servicio_por_distrito(distrito_id) or []
                        tipo_servicio_id = next((ts['id'] for ts in tipos if ts['descripcion'] == tipo_servicio), None)

                servicio_id = None
                if servicio and tipo_servicio_id:
                    servicio_id = cache.servicio_id(servicio, tipo_servicio_id)
                    if servicio_id is None:
                        servicios = obtener_servicios_por_tipo(tipo_servicio_id) or []
                        servicio_id = next((s['id'] for s in servicios if s['nombre'] == servicio), None)

                insumo_id = self._resolver_insumo_id_robusto(tipo_insumo, insumo)

                # Saldo en BD y saldo virtual por separado
                saldo_bd = self._obtener_saldo_actual(nivel_val, area_id, distrito_id, tipo_servicio_id, servicio_id, insumo_id)
                saldo_virtual = self._saldo_virtual_treeview(nivel_val, area_id, distrito_id, tipo_servicio_id, servicio_id, insumo_id)
                saldo_total_estimado = saldo_bd + saldo_virtual

                # 1) No permitir negativos si en BD ya no hay saldo
                if saldo_bd <= 0:
                    messagebox.showerror(
                        "Saldo insuficiente (BD)",
                        "No puede registrar un movimiento negativo porque el insumo no tiene saldo previo en la base de datos para el nivel seleccionado.\n"
                        "Registre primero un movimiento positivo (p. ej. Inventario Inicial o Entrada)."
                    )
                    return

                # 2) No permitir que el negativo supere lo que ya existe en BD
                if cantidad > saldo_bd:
                    messagebox.showerror(
                        "Saldo insuficiente (BD)",
                        f"La cantidad solicitada ({cantidad}) excede el saldo disponible en base de datos ({saldo_bd:.2f})."
                    )
                    return

                # 3) Adicionalmente controlar que no se pase del total estimado (BD + TreeView)
                if cantidad > saldo_total_estimado:
                    messagebox.showerror(
                        "Saldo insuficiente",
                        f"La cantidad solicitada ({cantidad}) excede el saldo total estimado ({saldo_total_estimado:.2f})."
                    )
                    return

            # Insertar al listado temporal
            self.tree.insert('', 'end', values=(
                fecha_registro,
                referencia,
                tipo_movimiento,
                insumo,
                presentacion,
                servicio,
                lote,
                fecha_venc_str,
                cantidad,
                salida_distrito,
                salida_servicio,
                observaciones,
                tipo_insumo,
                area,
                distrito,
                tipo_servicio
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
            messagebox.showwarning("Advertencia", "Por favor, seleccione un movimiento para editar", parent=self.parent)
            return

        valores = self.tree.item(selected_item)['values']

        editar_ventana = tk.Toplevel(self.parent)
        editar_ventana.title("Editar Movimiento")
        editar_ventana.configure(bg=self.COLORS['light'])
        editar_ventana.transient(self.parent)
        editar_ventana.grab_set()
        editar_ventana.focus_set()

        # Registrar toplevel para limpieza
        self._open_toplevels.append(editar_ventana)
        def _on_close_editor():
            try:
                try:
                    self._open_toplevels.remove(editar_ventana)
                except ValueError:
                    pass
                if editar_ventana and editar_ventana.winfo_exists():
                    editar_ventana.destroy()
            except Exception:
                pass
        editar_ventana.protocol("WM_DELETE_WINDOW", _on_close_editor)

        # Centrado
        ancho_ventana = 1075
        alto_ventana = 525
        screen_width = editar_ventana.winfo_screenwidth()
        screen_height = editar_ventana.winfo_screenheight()
        x = (screen_width // 2) - (ancho_ventana // 2)
        y = (screen_height // 2) - (alto_ventana // 2)
        editar_ventana.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")
        editar_ventana.resizable(True, True)

        try:
            cache.initialize()
        except Exception:
            pass

        # Contenedor scroll
        scrollable_frame = tk.Frame(editar_ventana, bg=self.COLORS['light'])
        scrollable_frame.pack(fill='both', expand=True)

        # Header
        header_frame = tk.Frame(scrollable_frame, bg=self.COLORS['primary'], height=22)
        header_frame.pack(fill="x", padx=14, pady=(10, 4))
        header_frame.pack_propagate(False)
        tk.Label(header_frame, text="EDITAR MOVIMIENTO",
                font=('Segoe UI', 10, 'bold'),
                bg=self.COLORS['primary'], fg='white').pack(expand=True)

        # Nivel de Bodega
        self.frame_nivel_bodega_edit = tk.Frame(scrollable_frame, bg=self.COLORS['light'], relief='solid', borderwidth=1)
        self.frame_nivel_bodega_edit.pack(fill="x", padx=14, pady=6)

        nivel_header = tk.Frame(self.frame_nivel_bodega_edit, bg=self.COLORS['primary'], height=16)
        nivel_header.pack(fill='x')
        nivel_header.pack_propagate(False)
        tk.Label(nivel_header, text="🏢 Nivel de Bodega",
                font=('Segoe UI', 8, 'bold'),
                fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(side='left', padx=8, pady=0)

        nivel_content = tk.Frame(self.frame_nivel_bodega_edit, bg=self.COLORS['light'])
        nivel_content.pack(fill='x', padx=10, pady=3)

        # Variable compartida para los tres radios
        nivel_sel = tk.StringVar(value="area")  # inicial, luego será establecido por cargar_datos_iniciales

        rb_area = tk.Radiobutton(nivel_content, text="Área", image=self.icon_area, compound='left',
                                variable=nivel_sel, value="area",
                                font=('Segoe UI', 8), bg=self.COLORS['light'], fg=self.COLORS['text_dark'],
                                selectcolor=self.COLORS['light'], activebackground=self.COLORS['light'])
        rb_distrito = tk.Radiobutton(nivel_content, text="Distrito", image=self.icon_distrito, compound='left',
                                    variable=nivel_sel, value="distrito",
                                    font=('Segoe UI', 8), bg=self.COLORS['light'], fg=self.COLORS['text_dark'],
                                    selectcolor=self.COLORS['light'], activebackground=self.COLORS['light'])
        rb_servicio = tk.Radiobutton(nivel_content, text="Servicio", image=self.icon_servicio, compound='left',
                                    variable=nivel_sel, value="servicio",
                                    font=('Segoe UI', 8), bg=self.COLORS['light'], fg=self.COLORS['text_dark'],
                                    selectcolor=self.COLORS['light'], activebackground=self.COLORS['light'])

        rb_area.grid(row=0, column=0, padx=(0, 12), pady=2, sticky="w")
        rb_distrito.grid(row=0, column=1, padx=(0, 12), pady=2, sticky="w")
        rb_servicio.grid(row=0, column=2, padx=(0, 0), pady=2, sticky="w")

        # Configuración de Servicios
        self.frame_servicios_edit = tk.Frame(scrollable_frame, bg=self.COLORS['light'], relief='solid', borderwidth=1)
        self.frame_servicios_edit.pack(fill="x", padx=14, pady=6)

        servicios_header = tk.Frame(self.frame_servicios_edit, bg=self.COLORS['primary'], height=16)
        servicios_header.pack(fill='x')
        servicios_header.pack_propagate(False)
        tk.Label(servicios_header, text="🏥 Configuración de Servicios",
                font=('Segoe UI', 8, 'bold'), fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(side='left', padx=8, pady=0)

        servicios_content = tk.Frame(self.frame_servicios_edit, bg=self.COLORS['light'])
        servicios_content.pack(fill="x", padx=10, pady=3)

        for col in range(8):
            servicios_content.columnconfigure(col, weight=1)

        tk.Label(servicios_content, text="Área:", font=('Segoe UI', 8, 'bold'),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=0, column=0, padx=4, pady=(1,1), sticky="w")
        edit_area_var = tk.StringVar()
        area_cb = AutocompleteCombobox(servicios_content, textvariable=edit_area_var, width=25, state="normal", font=('Segoe UI', 8))
        editar_ventana.after_idle(lambda: area_cb.set_completion_list(cache.get_area_names()))
        area_cb.grid(row=0, column=1, padx=4, pady=(1,2), sticky="ew")

        tk.Label(servicios_content, text="Distrito:", font=('Segoe UI', 8, 'bold'),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=0, column=2, padx=4, pady=(1,1), sticky="w")
        edit_distrito_var = tk.StringVar()
        distrito_cb = AutocompleteCombobox(servicios_content, textvariable=edit_distrito_var, width=25, state="normal", font=('Segoe UI', 8))
        editar_ventana.after_idle(lambda: distrito_cb.set_completion_list(cache.get_distritos_names()))
        distrito_cb.grid(row=0, column=3, padx=4, pady=(1,2), sticky="ew")

        tk.Label(servicios_content, text="Tipo de Servicio:", font=('Segoe UI', 8, 'bold'),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=0, column=4, padx=4, pady=(1,1), sticky="w")
        edit_tipo_servicio_var = tk.StringVar()
        tipo_servicio_cb = AutocompleteCombobox(servicios_content, textvariable=edit_tipo_servicio_var, width=25, state="normal", font=('Segoe UI', 8))
        tipo_servicio_cb.grid(row=0, column=5, padx=4, pady=(1,2), sticky="ew")

        tk.Label(servicios_content, text="Servicio:", font=('Segoe UI', 8, 'bold'),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=0, column=6, padx=4, pady=(1,1), sticky="w")
        edit_servicio_var = tk.StringVar()
        servicio_cb = AutocompleteCombobox(servicios_content, textvariable=edit_servicio_var, width=25, state="normal", font=('Segoe UI', 8))
        servicio_cb.grid(row=0, column=7, padx=4, pady=(1,2), sticky="ew")

        # Gestión de Insumos
        self.frame_insumos_edit = tk.Frame(scrollable_frame, bg=self.COLORS['light'], relief='solid', borderwidth=1)
        self.frame_insumos_edit.pack(fill="x", padx=14, pady=6)

        insumos_header = tk.Frame(self.frame_insumos_edit, bg=self.COLORS['primary'], height=16)
        insumos_header.pack(fill='x')
        insumos_header.pack_propagate(False)
        tk.Label(insumos_header, text="💊 Gestión de Insumos",
                font=('Segoe UI', 8, 'bold'), fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(side='left', padx=8, pady=0)

        insumos_content = tk.Frame(self.frame_insumos_edit, bg=self.COLORS['light'])
        insumos_content.pack(fill="x", padx=10, pady=3)

        for col in range(8):
            insumos_content.columnconfigure(col, weight=1, uniform="insumos_edit")

        tk.Label(insumos_content, text="Tipo de Insumo:", font=('Segoe UI', 8, 'bold'),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=0, column=0, columnspan=2, padx=4, pady=(1,1), sticky="w")
        edit_tipo_insumo_var = tk.StringVar()
        tipo_insumo_cb = AutocompleteCombobox(insumos_content, textvariable=edit_tipo_insumo_var,
                                            width=18, state="normal", font=('Segoe UI', 8))
        tipo_insumo_cb.set_completion_list([ti['descripcion'] for ti in obtener_tipos_insumo() or []])
        tipo_insumo_cb.grid(row=1, column=0, columnspan=2, padx=4, pady=(1,2), sticky="ew")

        tk.Label(insumos_content, text="Insumo:", font=('Segoe UI', 8, 'bold'),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=0, column=2, columnspan=4, padx=4, pady=(1,1), sticky="w")
        edit_insumo_var = tk.StringVar()
        insumo_cb = AutocompleteCombobox(insumos_content, textvariable=edit_insumo_var,
                                        width=38, state="normal", font=('Segoe UI', 8))
        insumo_cb.grid(row=1, column=2, columnspan=4, padx=4, pady=(1,2), sticky="ew")

        tk.Label(insumos_content, text="Presentación:", font=('Segoe UI', 8, 'bold'),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=0, column=6, columnspan=2, padx=4, pady=(1,1), sticky="w")
        edit_presentacion_var = tk.StringVar()
        presentacion_cb = AutocompleteCombobox(insumos_content, textvariable=edit_presentacion_var,
                                            width=18, state="normal", font=('Segoe UI', 8))
        presentacion_cb.grid(row=1, column=6, columnspan=2, padx=4, pady=(1,2), sticky="ew")

        # Detalles del Movimiento
        self.frame_detalles_edit = tk.Frame(scrollable_frame, bg=self.COLORS['light'], relief='solid', borderwidth=1)
        self.frame_detalles_edit.pack(fill="x", padx=14, pady=6)

        detalles_header = tk.Frame(self.frame_detalles_edit, bg=self.COLORS['primary'], height=16)
        detalles_header.pack(fill='x')
        detalles_header.pack_propagate(False)
        tk.Label(detalles_header, text="📋 Detalles del Movimiento",
                font=('Segoe UI', 8, 'bold'),
                fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(side='left', padx=8, pady=0)

        detalles_content = tk.Frame(self.frame_detalles_edit, bg=self.COLORS['light'])
        detalles_content.pack(fill="x", padx=10, pady=3)

        for col in range(6):
            detalles_content.columnconfigure(col, weight=1)

        tk.Label(detalles_content, text="Fecha de Registro:", font=('Segoe UI', 8, 'bold'),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=0, column=0, padx=4, pady=(1,1), sticky="w")
        fecha_edit = DateEntry(detalles_content, width=18, background='darkblue', foreground='white',
                            borderwidth=2, date_pattern='dd/mm/yyyy', font=('Segoe UI', 8))
        fecha_edit.grid(row=0, column=1, padx=4, pady=(1,2), sticky="ew")

        tk.Label(detalles_content, text="Referencia:", font=('Segoe UI', 8, 'bold'),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=0, column=2, padx=4, pady=(1,1), sticky="w")
        referencia_entry = ttk.Entry(detalles_content, width=24, font=('Segoe UI', 8))
        referencia_entry.grid(row=0, column=3, padx=4, pady=(1,2), sticky="ew")

        tk.Label(detalles_content, text="Tipo Movimiento:", font=('Segoe UI', 8, 'bold'),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=0, column=4, padx=4, pady=(1,1), sticky="w")
        edit_tipo_movimiento_var = tk.StringVar()
        tipo_mov_cb = AutocompleteCombobox(detalles_content, textvariable=edit_tipo_movimiento_var, width=25, state="normal", font=('Segoe UI', 8))
        editar_ventana.after_idle(lambda: tipo_mov_cb.set_completion_list(cache.get_tipos_movimiento_names()))
        tipo_mov_cb.grid(row=0, column=5, padx=4, pady=(1,2), sticky="ew")

        tk.Label(detalles_content, text="Lote:", font=('Segoe UI', 8, 'bold'),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=1, column=0, padx=4, pady=(1,1), sticky="w")
        lote_frame = tk.Frame(detalles_content, bg=self.COLORS['light'])
        lote_frame.grid(row=1, column=1, padx=4, pady=(1,2), sticky="ew")
        lote_entry = ttk.Entry(lote_frame, width=20, font=('Segoe UI', 8))
        lote_entry.pack(side="left", fill="x", expand=True)
        edit_sin_lote_var = tk.BooleanVar()
        edit_check_sin_lote = tk.Checkbutton(lote_frame, text="Sin\nlote", variable=edit_sin_lote_var,
                                            command=lambda: (lote_entry.delete(0, tk.END) or lote_entry.config(state='disabled')) if edit_sin_lote_var.get() else lote_entry.config(state='normal'),
                                            font=('Segoe UI', 8),
                                            bg=self.COLORS['light'], fg=self.COLORS['text_dark'],
                                            activebackground=self.COLORS['white'], activeforeground=self.COLORS['text_dark'],
                                            selectcolor=self.COLORS['white'])
        edit_check_sin_lote.pack(side="right", padx=(5, 0))

        tk.Label(detalles_content, text="Fecha\nVencimiento:", font=('Segoe UI', 8, 'bold'),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=1, column=2, padx=4, pady=(1,1), sticky="w")
        fecha_venc_frame = tk.Frame(detalles_content, bg=self.COLORS['light'])
        fecha_venc_frame.grid(row=1, column=3, padx=4, pady=(1,2), sticky="ew")
        fecha_venc_edit = DateEntry(fecha_venc_frame, width=15, background='darkblue', foreground='white',
                                    borderwidth=2, date_pattern='dd/mm/yyyy', font=('Segoe UI', 8))
        fecha_venc_edit.pack(side="left")
        edit_sin_fecha_venc = tk.BooleanVar()
        edit_check_sin_fecha = tk.Checkbutton(fecha_venc_frame, text="Sin fecha\nvencimiento", variable=edit_sin_fecha_venc,
                                            command=lambda: fecha_venc_edit.configure(state='disabled' if edit_sin_fecha_venc.get() else 'normal'),
                                            font=('Segoe UI', 8),
                                            bg=self.COLORS['light'], fg=self.COLORS['text_dark'],
                                            activebackground=self.COLORS['white'], activeforeground=self.COLORS['text_dark'],
                                            selectcolor=self.COLORS['white'])
        edit_check_sin_fecha.pack(side="right", padx=(5, 0))

        tk.Label(detalles_content, text="Cantidad:", font=('Segoe UI', 8, 'bold'),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=1, column=4, padx=4, pady=(1,1), sticky="w")
        cantidad_entry = ttk.Entry(detalles_content, width=24, font=('Segoe UI', 8))
        cantidad_entry.grid(row=1, column=5, padx=4, pady=(1,2), sticky="ew")

        tk.Label(detalles_content, text="Observaciones:", font=('Segoe UI', 8, 'bold'),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=2, column=0, padx=4, pady=(1,1), sticky="w")
        observaciones_entry = ttk.Entry(detalles_content, width=80, font=('Segoe UI', 8))
        observaciones_entry.grid(row=2, column=1, columnspan=5, padx=4, pady=(1,2), sticky="ew")

        # Salida a Nivel Inferior
        self.frame_salida_nivel_inferior_edit = tk.Frame(scrollable_frame, bg=self.COLORS['light'], relief='solid', borderwidth=1)
        self.frame_salida_nivel_inferior_edit.pack(fill="x", padx=14, pady=6)

        salida_header = tk.Frame(self.frame_salida_nivel_inferior_edit, bg=self.COLORS['primary'], height=16)
        salida_header.pack(fill='x')
        salida_header.pack_propagate(False)
        tk.Label(salida_header, text="🔄 Salida a Nivel Inferior",
                font=('Segoe UI', 8, 'bold'), fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(side='left', padx=8, pady=0)

        salida_content = tk.Frame(self.frame_salida_nivel_inferior_edit, bg=self.COLORS['light'])
        salida_content.pack(fill='x', padx=10, pady=3)

        for col in range(6):
            salida_content.columnconfigure(col, weight=1)

        tk.Label(salida_content, text="Distrito:", font=('Segoe UI', 8, 'bold'),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=0, column=0, padx=4, pady=(1,1), sticky="w")
        edit_salida_distrito_var = tk.StringVar()
        salida_distrito_cb = AutocompleteCombobox(salida_content, textvariable=edit_salida_distrito_var, width=25,
                                                completevalues=[d['nombre'] for d in obtener_distritos() or []], state="disabled", font=('Segoe UI', 8))
        salida_distrito_cb.grid(row=0, column=1, padx=4, pady=(1,2), sticky="ew")

        tk.Label(salida_content, text="Tipo de Servicio:", font=('Segoe UI', 8, 'bold'),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=0, column=2, padx=4, pady=(1,1), sticky="w")
        edit_salida_tipo_servicio_var = tk.StringVar()
        salida_tipo_servicio_cb = AutocompleteCombobox(salida_content, textvariable=edit_salida_tipo_servicio_var, width=25,
                                                    completevalues=[], state="disabled", font=('Segoe UI', 8))
        salida_tipo_servicio_cb.grid(row=0, column=3, padx=4, pady=(1,2), sticky="ew")

        tk.Label(salida_content, text="Servicio:", font=('Segoe UI', 8, 'bold'),
                bg=self.COLORS['light'], fg=self.COLORS['text_dark']).grid(row=0, column=4, padx=4, pady=(1,1), sticky="w")
        edit_salida_servicio_var = tk.StringVar()
        salida_servicio_cb = AutocompleteCombobox(salida_content, textvariable=edit_salida_servicio_var, width=25,
                                                completevalues=[], state="disabled", font=('Segoe UI', 8))
        salida_servicio_cb.grid(row=0, column=5, padx=4, pady=(1,2), sticky="ew")

        # Funciones auxiliares del diálogo
        def actualizar_estado_comboboxes_edit(*args):
            nivel_val = nivel_sel.get()
            if nivel_val == "area":
                area_cb.config(state="normal")
                distrito_cb.config(state="disabled")
                tipo_servicio_cb.config(state="disabled")
                servicio_cb.config(state="disabled")
            elif nivel_val == "distrito":
                area_cb.config(state="normal")
                distrito_cb.config(state="normal")
                tipo_servicio_cb.config(state="disabled")
                servicio_cb.config(state="disabled")
            elif nivel_val == "servicio":
                area_cb.config(state="normal")
                distrito_cb.config(state="normal")
                tipo_servicio_cb.config(state="normal")
                servicio_cb.config(state="normal")
            actualizar_tipos_movimiento_filtrados_edit()
            if nivel_val == "distrito" and edit_tipo_movimiento_var.get().strip().upper() == "SALIDA NIVEL INFERIOR":
                edit_salida_distrito_var.set(edit_distrito_var.get())
                actualizar_tipos_servicio_salida_edit()

        def actualizar_estado_salida_nivel_inferior_edit(*args):
            tipo_mov = edit_tipo_movimiento_var.get().strip().upper()
            nivel_val = nivel_sel.get()
            if tipo_mov == "SALIDA NIVEL INFERIOR":
                if nivel_val == "area":
                    salida_distrito_cb.config(state="normal")
                    salida_tipo_servicio_cb.config(state="disabled")
                    salida_servicio_cb.config(state="disabled")
                elif nivel_val == "distrito":
                    edit_salida_distrito_var.set(edit_distrito_var.get())
                    salida_distrito_cb.config(state="disabled")
                    salida_tipo_servicio_cb.config(state="normal")
                    salida_servicio_cb.config(state="normal")
                    actualizar_tipos_servicio_salida_edit()
                else:
                    salida_distrito_cb.config(state="disabled")
                    salida_tipo_servicio_cb.config(state="disabled")
                    salida_servicio_cb.config(state="disabled")
            else:
                edit_salida_distrito_var.set('')
                edit_salida_tipo_servicio_var.set('')
                edit_salida_servicio_var.set('')
                salida_distrito_cb.config(state="disabled")
                salida_tipo_servicio_cb.config(state="disabled")
                salida_servicio_cb.config(state="disabled")

        def actualizar_tipos_movimiento_filtrados_edit():
            tipos_raw = cache.get_tipos_movimiento_names() or []

            def norm(s): return (s or '').strip().upper()

            POSITIVOS = ["INVENTARIO INICIAL", "ENTRADA NIVEL SUPERIOR", "REAJUSTE (+)"]
            NEGATIVOS = ["SALIDA NIVEL INFERIOR", "REAJUSTE (-)","ENTREGADO"]
            INDIFERENTES = ["NO ENTREGADO"]

            pos_set = {norm(x) for x in POSITIVOS}
            neg_set = {norm(x) for x in NEGATIVOS}
            ind_set = {norm(x) for x in INDIFERENTES}

            nivel_val = nivel_sel.get()

            filtrados = []
            for t in tipos_raw:
                tu = norm(t)
                if nivel_val in ("area", "distrito"):
                    if tu in ind_set:
                        continue
                elif nivel_val == "servicio":
                    if tu == "SALIDA NIVEL INFERIOR":
                        continue
                filtrados.append(t)

            # Ocultar INVENTARIO INICIAL si ya existe para el insumo de la edición
            try:
                ti_desc = (edit_tipo_insumo_var.get() or '').strip()
                ins_desc = (edit_insumo_var.get() or '').strip()
                if ti_desc and ins_desc:
                    if self._insumo_tiene_inventario_inicial_por_desc(ti_desc, ins_desc):
                        filtrados = [t for t in filtrados if norm(t) != "INVENTARIO INICIAL"]
            except Exception:
                pass

            def orden_clave(t):
                tu = norm(t)
                if tu in pos_set:
                    order_map = {
                        "INVENTARIO INICIAL": 1,
                        "ENTRADA NIVEL SUPERIOR": 2,
                        "REAJUSTE (+)": 3
                    }
                    return (1, order_map.get(tu, 99), tu)
                if tu in neg_set:
                    order_map = {
                        "SALIDA NIVEL INFERIOR": 1,
                        "REAJUSTE (-)": 2,
                        "ENTREGADO": 3
                    }
                    return (2, order_map.get(tu, 99), tu)
                if tu in ind_set:
                    order_map = {
                        "NO ENTREGADO": 1
                    }
                    return (3, order_map.get(tu, 99), tu)
                return (4, 99, tu)

            filtrados.sort(key=orden_clave)

            tipo_mov_cb.set_completion_list(filtrados)
            if edit_tipo_movimiento_var.get() not in filtrados:
                edit_tipo_movimiento_var.set('')

        def actualizar_tipos_servicio_edit(*args):
            distrito_nombre = edit_distrito_var.get()
            distrito_id = cache.distrito_id(distrito_nombre)
            if distrito_id:
                tipos_servicio = cache.get_tipos_servicio_por_distrito(distrito_id) or []
                opciones = [ts['descripcion'] for ts in tipos_servicio]
                tipo_servicio_cb.set_completion_list(opciones)
                if edit_tipo_servicio_var.get() not in opciones:
                    edit_tipo_servicio_var.set('')
                servicio_cb.set_completion_list([])
                edit_servicio_var.set('')
            else:
                tipo_servicio_cb.set_completion_list([])
                edit_tipo_servicio_var.set('')
                servicio_cb.set_completion_list([])
                edit_servicio_var.set('')

        def actualizar_servicios_edit(*args):
            distrito_nombre = edit_distrito_var.get()
            tipo_servicio_desc = edit_tipo_servicio_var.get()
            distrito_id = cache.distrito_id(distrito_nombre)
            if distrito_id:
                tipo_servicio_id = cache.tipo_servicio_id(tipo_servicio_desc, distrito_id)
                if tipo_servicio_id:
                    servicios = cache.get_servicios_por_tipo(tipo_servicio_id) or []
                    opciones = [s['nombre'] for s in servicios]
                    servicio_cb.set_completion_list(opciones)
                    if edit_servicio_var.get() not in opciones:
                        edit_servicio_var.set('')
                    return
            servicio_cb.set_completion_list([])
            edit_servicio_var.set('')

        def actualizar_tipos_servicio_salida_edit(*args):
            distrito_nombre = edit_salida_distrito_var.get()
            distrito_id = cache.distrito_id(distrito_nombre)
            if distrito_id:
                tipos_servicio = cache.get_tipos_servicio_por_distrito(distrito_id) or []
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
            distrito_id = cache.distrito_id(distrito_nombre)
            if distrito_id:
                tipo_servicio_id = cache.tipo_servicio_id(tipo_servicio_desc, distrito_id)
                if tipo_servicio_id:
                    servicios = cache.get_servicios_por_tipo(tipo_servicio_id) or []
                    opciones = [s['nombre'] for s in servicios]
                    salida_servicio_cb.set_completion_list(opciones)
                    if edit_salida_servicio_var.get() not in opciones:
                        edit_salida_servicio_var.set('')
                    return
            salida_servicio_cb.set_completion_list([])
            edit_salida_servicio_var.set('')

        def actualizar_insumos_edit(*args):
            tipo_insumo_desc = edit_tipo_insumo_var.get()
            tipo_insumo_id = cache.tipo_insumo_id(tipo_insumo_desc)
            if tipo_insumo_id:
                insumos = cache.get_insumos_por_tipo(tipo_insumo_id) or []
                opciones = [i['nombre'] for i in insumos]
                insumo_cb.set_completion_list(opciones)
                if edit_insumo_var.get() not in opciones:
                    edit_insumo_var.set('')
            else:
                insumo_cb.set_completion_list([])
                edit_insumo_var.set('')

        def actualizar_presentacion_edit(*args):
            tipo_insumo_desc = edit_tipo_insumo_var.get()
            insumo_nombre = edit_insumo_var.get()
            tipo_insumo_id = cache.tipo_insumo_id(tipo_insumo_desc)
            if tipo_insumo_id and insumo_nombre:
                insumos = cache.get_insumos_por_tipo(tipo_insumo_id) or []
                insumo_sel = next((i for i in insumos if i['nombre'] == insumo_nombre), None)
                if insumo_sel and insumo_sel.get('nombre_presentacion'):
                    presentacion_cb.set_completion_list([insumo_sel['nombre_presentacion']])
                    edit_presentacion_var.set(insumo_sel['nombre_presentacion'])
                    return
            presentacion_cb.set_completion_list([])
            edit_presentacion_var.set('')

        # Variables del diálogo
        nivel_sel.trace_add("write", actualizar_estado_comboboxes_edit)

        edit_distrito_var.trace_add("write", actualizar_tipos_servicio_edit)
        edit_tipo_servicio_var.trace_add("write", actualizar_servicios_edit)
        def _on_tipo_mov_edit_changed(*args):
            actualizar_estado_salida_nivel_inferior_edit()

        edit_tipo_movimiento_var.trace_add("write", _on_tipo_mov_edit_changed)
        nivel_sel.trace_add("write", lambda *a: (actualizar_estado_comboboxes_edit(), actualizar_tipos_movimiento_filtrados_edit()))
        edit_distrito_var.trace_add("write", lambda *a: (actualizar_tipos_servicio_edit(), actualizar_tipos_movimiento_filtrados_edit()))
        edit_tipo_servicio_var.trace_add("write", lambda *a: (actualizar_servicios_edit(), actualizar_tipos_movimiento_filtrados_edit()))
        edit_tipo_insumo_var.trace_add("write", lambda *a: (actualizar_insumos_edit(), actualizar_tipos_movimiento_filtrados_edit()))
        edit_insumo_var.trace_add("write", lambda *a: (actualizar_presentacion_edit(), actualizar_tipos_movimiento_filtrados_edit()))
        edit_salida_distrito_var.trace_add("write", actualizar_tipos_servicio_salida_edit)
        edit_salida_tipo_servicio_var.trace_add("write", actualizar_servicios_salida_edit)
        edit_tipo_insumo_var.trace_add("write", actualizar_insumos_edit)
        edit_insumo_var.trace_add("write", actualizar_presentacion_edit)

        # Carga inicial de datos
        def cargar_datos_iniciales():
            area_valor = valores[13] if len(valores) > 13 else ''
            distrito_valor = valores[14] if len(valores) > 14 else ''
            tipo_servicio_valor = valores[15] if len(valores) > 15 else ''
            servicio_valor = valores[5]

            if servicio_valor and tipo_servicio_valor and distrito_valor:
                nivel_sel.set("servicio")
            elif distrito_valor and not servicio_valor:
                nivel_sel.set("distrito")
            else:
                nivel_sel.set("area")

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

            # Cargar datos de Salida a Nivel Inferior
            salida_distrito_nombre = valores[9] if valores[9] else ''
            salida_servicio_nombre = valores[10] if valores[10] else ''

            edit_salida_distrito_var.set(salida_distrito_nombre)

            # Si hay distrito de salida, cargar sus tipos de servicio
            if salida_distrito_nombre:
                salida_distrito_id = cache.distrito_id(salida_distrito_nombre)
                if salida_distrito_id:
                    tipos_servicio_salida = cache.get_tipos_servicio_por_distrito(salida_distrito_id) or []
                    salida_tipo_servicio_cb.set_completion_list([ts['descripcion'] for ts in tipos_servicio_salida])
                    
                    # Si hay servicio de salida, encontrar su tipo de servicio
                    if salida_servicio_nombre:
                        # Buscar el tipo de servicio del servicio de salida
                        for ts in tipos_servicio_salida:
                            servicios_del_tipo = cache.get_servicios_por_tipo(ts['id']) or []
                            if any(s['nombre'] == salida_servicio_nombre for s in servicios_del_tipo):
                                edit_salida_tipo_servicio_var.set(ts['descripcion'])
                                salida_servicio_cb.set_completion_list([s['nombre'] for s in servicios_del_tipo])
                                break

            edit_salida_servicio_var.set(salida_servicio_nombre)

            actualizar_estado_salida_nivel_inferior_edit()

        editar_ventana.after_idle(cargar_datos_iniciales)

        def validar_campos():
            if not fecha_edit.get_date():
                messagebox.showerror("Error", "La fecha de registro es obligatoria", parent=editar_ventana)
                return False
            if not referencia_entry.get().strip():
                messagebox.showerror("Error", "La referencia es obligatoria", parent=editar_ventana)
                return False
            if not edit_tipo_movimiento_var.get().strip():
                messagebox.showerror("Error", "El tipo de movimiento es obligatorio", parent=editar_ventana)
                return False
            if not edit_insumo_var.get().strip():
                messagebox.showerror("Error", "El insumo es obligatorio", parent=editar_ventana)
                return False
            if not edit_presentacion_var.get().strip():
                messagebox.showerror("Error", "La presentación es obligatoria", parent=editar_ventana)
                return False

            nivel_val = nivel_sel.get()
            if nivel_val == "distrito" and not edit_distrito_var.get().strip():
                messagebox.showerror("Error", "El distrito es obligatorio para nivel Distrito", parent=editar_ventana)
                return False
            if nivel_val == "servicio":
                if not edit_distrito_var.get().strip():
                    messagebox.showerror("Error", "El distrito es obligatorio para nivel Servicio", parent=editar_ventana)
                    return False
                if not edit_tipo_servicio_var.get().strip():
                    messagebox.showerror("Error", "El tipo de servicio es obligatorio para nivel Servicio", parent=editar_ventana)
                    return False
                if not edit_servicio_var.get().strip():
                    messagebox.showerror("Error", "El servicio es obligatorio para nivel Servicio", parent=editar_ventana)
                    return False

            if edit_tipo_movimiento_var.get().strip().upper() == "SALIDA NIVEL INFERIOR":
                if nivel_val == "area" and not edit_salida_distrito_var.get().strip():
                    messagebox.showerror("Requisito", "Debe seleccionar un Distrito (Salida) antes de continuar.", parent=editar_ventana)
                    return False
                if nivel_val == "distrito" and not edit_salida_servicio_var.get().strip():
                    messagebox.showerror("Requisito", "Debe seleccionar un Servicio (Salida) antes de continuar.", parent=editar_ventana)
                    return False

            if not edit_sin_lote_var.get() and not lote_entry.get().strip():
                messagebox.showerror("Error", "El campo Lote es obligatorio si no está marcado 'Sin lote'", parent=editar_ventana)
                return False
            if not edit_sin_fecha_venc.get() and not fecha_venc_edit.get_date():
                messagebox.showerror("Error", "La fecha de vencimiento es obligatoria si no está marcada 'Sin fecha'", parent=editar_ventana)
                return False

            try:
                cantidad = float(cantidad_entry.get().strip())
                if cantidad <= 0:
                    messagebox.showerror("Error", "La cantidad debe ser un número positivo", parent=editar_ventana)
                    return False
            except ValueError:
                messagebox.showerror("Error", "La cantidad debe ser un número válido", parent=editar_ventana)
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
            
            # VALIDACIÓN DE SALDO PARA MOVIMIENTOS NEGATIVOS (sin cambiar nombres)
            desc_up = (edit_tipo_movimiento_var.get() or '').strip().upper()
            NEGATIVOS = {"SALIDA NIVEL INFERIOR", "REAJUSTE (-)", "ENTREGADO"}
            if desc_up in NEGATIVOS:
                try:
                    nivel_val = (nivel_sel.get() or '').strip()

                    area_nombre = (edit_area_var.get() or '').strip()
                    distrito_nombre = (edit_distrito_var.get() or '').strip()
                    tipo_servicio_desc = (edit_tipo_servicio_var.get() or '').strip()
                    servicio_nombre = (edit_servicio_var.get() or '').strip()
                    tipo_insumo_desc = (edit_tipo_insumo_var.get() or '').strip()
                    insumo_nombre = (edit_insumo_var.get() or '').strip()

                    area_id = cache.area_id(area_nombre) if area_nombre else None
                    distrito_id = cache.distrito_id(distrito_nombre) if distrito_nombre else None

                    tipo_servicio_id = None
                    if tipo_servicio_desc and distrito_id:
                        tipo_servicio_id = cache.tipo_servicio_id(tipo_servicio_desc, distrito_id)
                        if tipo_servicio_id is None:
                            tipos = obtener_tipos_servicio_por_distrito(distrito_id) or []
                            tipo_servicio_id = next((ts['id'] for ts in tipos if ts['descripcion'] == tipo_servicio_desc), None)

                    servicio_id = None
                    if servicio_nombre and tipo_servicio_id:
                        servicio_id = cache.servicio_id(servicio_nombre, tipo_servicio_id)
                        if servicio_id is None:
                            servicios = obtener_servicios_por_tipo(tipo_servicio_id) or []
                            servicio_id = next((s['id'] for s in servicios if s['nombre'] == servicio_nombre), None)

                    insumo_id = self._resolver_insumo_id_robusto(tipo_insumo_desc, insumo_nombre)

                    try:
                        cantidad_val = float(cantidad_entry.get().strip())
                    except Exception:
                        messagebox.showerror("Error", "La cantidad debe ser un número válido", parent=editar_ventana)
                        return

                    saldo_bd = self._obtener_saldo_actual(nivel_val, area_id, distrito_id, tipo_servicio_id, servicio_id, insumo_id)
                    saldo_virtual = self._saldo_virtual_treeview(nivel_val, area_id, distrito_id, tipo_servicio_id, servicio_id, insumo_id)
                    saldo_total_estimado = saldo_bd + saldo_virtual

                    if saldo_bd <= 0:
                        messagebox.showerror(
                            "Saldo insuficiente (BD)",
                            "No puede guardar un movimiento negativo porque el insumo no tiene saldo previo en la base de datos para el nivel seleccionado.\n"
                            "Registre primero un movimiento positivo (p. ej. Inventario Inicial o Entrada).",
                            parent=editar_ventana
                        )
                        return

                    if cantidad_val > saldo_bd:
                        messagebox.showerror(
                            "Saldo insuficiente (BD)",
                            f"La cantidad ({cantidad_val}) excede el saldo disponible en base de datos ({saldo_bd:.2f}).",
                            parent=editar_ventana
                        )
                        return

                    if cantidad_val > saldo_total_estimado:
                        messagebox.showerror(
                            "Saldo insuficiente",
                            f"La cantidad ({cantidad_val}) excede el saldo total estimado ({saldo_total_estimado:.2f}).",
                            parent=editar_ventana
                        )
                        return

                except Exception as e:
                    messagebox.showerror("Error", f"Error validando saldo: {str(e)}", parent=editar_ventana)
                    return

            self.tree.item(selected_item, values=nuevos_valores)
            self.ajustar_ancho_columnas_automatico()
            messagebox.showinfo("Éxito", "Movimiento actualizado correctamente", parent=editar_ventana)
            _on_close_editor()

        frame_botones = tk.Frame(scrollable_frame, bg=self.COLORS['light'])
        frame_botones.pack(fill="x", padx=14, pady=8)
        botones_container = tk.Frame(frame_botones, bg=self.COLORS['light'])
        botones_container.pack(anchor="center")

        btn_guardar = tk.Button(botones_container, text="GUARDAR", image=self.icon_guardar, compound='left',
                                command=guardar_cambios, bg=self.COLORS['light'], fg=self.COLORS['text_dark'],
                                font=('Segoe UI', 8, 'bold'), relief='flat', padx=12, pady=4,
                                cursor='hand2', borderwidth=0, highlightthickness=0)
        btn_guardar.pack(side="left", padx=6, pady=(0,2))

        btn_cerrar = tk.Button(botones_container, text="CERRAR", image=self.icon_cerrar, compound='left',
                            command=_on_close_editor, bg=self.COLORS['light'], fg=self.COLORS['text_dark'],
                            font=('Segoe UI', 8, 'bold'), relief='flat', padx=12, pady=4,
                            cursor='hand2', borderwidth=0, highlightthickness=0)
        btn_cerrar.pack(side="left", padx=6, pady=(0,2))

        # Enlaces extra
        edit_area_var.trace_add('write', lambda *a: self.on_area_selected_edit(edit_area_var, edit_distrito_var, distrito_cb))

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

        for idx, item in enumerate(items, start=1):
            try:
                valores = self.tree.item(item)['values']

                fecha_registro_str = valores[0]
                referencia = valores[1]
                tipo_movimiento_desc = valores[2]
                insumo_nombre = valores[3]
                presentacion_nombre = valores[4]
                servicio_nombre = valores[5]
                lote = valores[6] if valores[6] != "N/A" else None
                fecha_vencimiento_str = valores[7]
                cantidad = float(valores[8])
                salida_distrito_nombre = valores[9] or None
                salida_servicio_nombre = valores[10] or None
                observaciones = valores[11] or None
                tipo_insumo_desc = valores[12]
                area_nombre = valores[13]
                distrito_nombre = valores[14]
                tipo_servicio_desc = valores[15]

                area_id = cache.area_id(area_nombre) if area_nombre else None
                distrito_id = cache.distrito_id(distrito_nombre) if distrito_nombre else None

                tipo_servicio_id = None
                if tipo_servicio_desc and distrito_id:
                    tipo_servicio_id = cache.tipo_servicio_id(tipo_servicio_desc, distrito_id)
                    if tipo_servicio_id is None:
                        tipos = obtener_tipos_servicio_por_distrito(distrito_id) or []
                        tipo_servicio_id = next((ts['id'] for ts in tipos if ts['descripcion'] == tipo_servicio_desc), None)

                servicio_id = None
                if servicio_nombre and tipo_servicio_id:
                    servicio_id = cache.servicio_id(servicio_nombre, tipo_servicio_id)
                    if servicio_id is None:
                        servicios = obtener_servicios_por_tipo(tipo_servicio_id) or []
                        servicio_id = next((s['id'] for s in servicios if s['nombre'] == servicio_nombre), None)

                tipo_insumo_id = cache.tipo_insumo_id(tipo_insumo_desc)
                if tipo_insumo_id is None:
                    raise ValueError(f"No se encontró el tipo de insumo: {tipo_insumo_desc}")

                insumo_id = cache.insumo_id(insumo_nombre, tipo_insumo_id)
                if insumo_id is None:
                    insumos = obtener_insumos_por_tipo(tipo_insumo_id) or []
                    insumo_id = next((i['id'] for i in insumos if i['nombre'] == insumo_nombre), None)
                    if insumo_id is None:
                        raise ValueError(f"No se encontró el insumo: {insumo_nombre}")

                presentacion_id = obtener_id_presentacion(presentacion_nombre) if presentacion_nombre else None

                tipo_movimiento_id = cache.tipo_movimiento_id(tipo_movimiento_desc)
                if tipo_movimiento_id is None:
                    tipo_movimiento_id = obtener_id_tipo_movimiento(tipo_movimiento_desc)

                fecha_registro = datetime.strptime(fecha_registro_str, '%d/%m/%Y')
                fecha_vencimiento = None if fecha_vencimiento_str == "N/A" else datetime.strptime(fecha_vencimiento_str, '%d/%m/%Y')

                salida_distrito_id = cache.distrito_id(salida_distrito_nombre) if salida_distrito_nombre else None
                salida_servicio_id = None
                if salida_servicio_nombre:
                    salida_servicio_id = obtener_id_servicio(salida_servicio_nombre)
                
                # VALIDACIÓN NEGATIVOS: impedir guardar si no hay saldo suficiente
                desc_up = (tipo_movimiento_desc or '').strip().upper()
                NEGATIVOS = {"SALIDA NIVEL INFERIOR", "REAJUSTE (-)", "ENTREGADO"}
                if desc_up in NEGATIVOS:
                    nivel_val = self.nivel_bodega_var.get()  # nivel de la pantalla al guardar
                    saldo_bd = self._obtener_saldo_actual(nivel_val, area_id, distrito_id, tipo_servicio_id, servicio_id, insumo_id)
                    saldo_virtual = self._saldo_virtual_treeview(nivel_val, area_id, distrito_id, tipo_servicio_id, servicio_id, insumo_id, excluir_item=item)  # <-- AGREGADO excluir_item=item
                    saldo_total_estimado = saldo_bd + saldo_virtual

                    if saldo_bd <= 0:
                        raise ValueError("Saldo insuficiente (BD): no existe saldo previo en base de datos para registrar un movimiento negativo.")
                    if cantidad > saldo_bd:
                        raise ValueError(f"Saldo insuficiente (BD): cantidad {cantidad} excede el saldo disponible en base de datos {saldo_bd:.2f}.")
                    if cantidad > saldo_total_estimado:
                        raise ValueError(f"Saldo insuficiente: la cantidad {cantidad} excede el saldo total estimado {saldo_total_estimado:.2f}.")
                
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

                guardar_movimiento(movimiento_data)
                
                # Si guardamos un INVENTARIO INICIAL para ese insumo, invalidar cache y refrescar el combo
                desc_up = (tipo_movimiento_desc or '').strip().upper()
                if desc_up == 'INVENTARIO INICIAL':
                    ti = (tipo_insumo_desc or '').strip()
                    ins = (insumo_nombre or '').strip()
                    # invalidar entrada de cache
                    self._cache_inventario_inicial_por_insumo.pop((ti, ins), None)
                    # si el usuario mantiene seleccionado el mismo insumo en pantalla, refrescar lista
                    if ti == (self.tipo_insumo_var.get() or '').strip() and ins == (self.insumo_var.get() or '').strip():
                        self.actualizar_tipos_movimiento_filtrados()
                
                movimientos_guardados += 1

            except Exception as e:
                errores.append(f"Error en movimiento {idx}: {str(e)}")

        if errores:
            messagebox.showerror("Errores al guardar",
                                 f"Se guardaron {movimientos_guardados} movimientos, pero hubo errores:\n" +
                                 "\n".join(errores))
        else:
            messagebox.showinfo("Éxito",
                                f"Se guardaron {movimientos_guardados} movimientos correctamente")
            self.tree.delete(*self.tree.get_children())

        self.limpiar_campos_completo()

    def limpiar_campos(self):
        self.tipo_movimiento_var.set('')
        self.salida_distrito_var.set('')
        self.salida_tipo_servicio_var.set('')
        self.salida_servicio_var.set('')

        self.lote_entry.delete(0, 'end')
        self.referencia_entry.delete(0, 'end')
        self.cantidad_entry.delete(0, 'end')
        self.observaciones_entry.delete(0, 'end')

        self.fecha_venc.set_date(datetime.now())
        self.sin_lote_var.set(False)
        self.lote_entry.config(state='normal')
        self.sin_fecha_venc.set(False)
        self.fecha_venc.configure(state='normal')

        self.actualizar_estado_salida_nivel_inferior()

    def limpiar_campos_completo(self):
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

        self.lote_entry.delete(0, 'end')
        self.referencia_entry.delete(0, 'end')
        self.cantidad_entry.delete(0, 'end')
        self.observaciones_entry.delete(0, 'end')

        self.fecha_reg.set_date(datetime.now())
        self.fecha_venc.set_date(datetime.now())

        self.nivel_bodega_var.set("area")

        self.sin_lote_var.set(False)
        self.lote_entry.config(state='normal')
        self.sin_fecha_venc.set(False)
        self.fecha_venc.configure(state='normal')

        self.actualizar_estado_comboboxes()

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
            'insumo': {'min': 220, 'max': 800},
            'presentacion': {'min': 90, 'max': 150},
            'servicio': {'min': 120, 'max': 280},
            'lote': {'min': 60, 'max': 120},
            'fecha_vencimiento': {'min': 100, 'max': 140},
            'cantidad': {'min': 70, 'max': 100},
            'salida_distrito': {'min': 100, 'max': 200},
            'salida_servicio': {'min': 120, 'max': 250},
            'observaciones': {'min': 150, 'max': 400},
            'tipo_insumo': {'min': 90, 'max': 150},
            'area': {'min': 80, 'max': 160},
            'distrito': {'min': 100, 'max': 180},
            'tipo_servicio': {'min': 120, 'max': 200}
        }

        for col in max_widths:
            ancho_calculado = max_widths[col]
            config = limites_configuracion.get(col, {'min': 80, 'max': 200})
            ancho_final = max(config['min'], min(ancho_calculado, config['max']))
            self.tree.column(col, width=ancho_final, minwidth=config['min'])
        self.tree.update_idletasks()

    def cerrar_ventana(self):
        if messagebox.askyesno("Confirmar", "¿Está seguro que desea cerrar esta ventana?"):
            # Limpieza defensiva
            try:
                self.before_destroy()
            except Exception:
                pass
            for widget in self.parent.winfo_children():
                try:
                    widget.destroy()
                except Exception:
                    pass
            if hasattr(self, "main_window") and self.main_window:
                self.main_window.show_welcome_screen()

    def on_area_selected(self, *args):
        if not hasattr(self, 'distrito_cb'):
            return
        area_nombre = self.area_var.get()
        area_id = cache.area_id(area_nombre)
        if area_id:
            distritos = cache.get_distritos_por_area(area_id) or []
            distritos_nombres = [d['nombre'] for d in distritos]
            self.distrito_cb.config(completevalues=distritos_nombres)
            self.distrito_var.set('')
        else:
            self.distrito_cb.config(completevalues=[])
            self.distrito_var.set('')

    def on_area_selected_edit(self, area_var, distrito_var, distrito_cb):
        area_nombre = area_var.get()
        area_id = cache.area_id(area_nombre)
        if area_id:
            distritos = cache.get_distritos_por_area(area_id) or []
            distritos_nombres = [d['nombre'] for d in distritos]
            distrito_cb.set_completion_list(distritos_nombres)
            if distrito_var.get() not in distritos_nombres:
                distrito_var.set('')
        else:
            distrito_cb.set_completion_list([])
            distrito_var.set('')