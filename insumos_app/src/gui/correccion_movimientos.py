import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime, date
import sys
import os
from ttkwidgets.autocomplete import AutocompleteCombobox
import threading
import tkinter.font as tkfont

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
    buscar_movimientos_por_filtros,
    obtener_tipos_movimiento,
    actualizar_movimiento,
    eliminar_movimiento,
)

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
        # margen interno del combobox
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

        # Paleta igual a IngresoInsumos / MainWindow
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

        self.cargar_iconos()  # Carga los iconos PNG aquí
        self.movimientos_data = None

        # Listas locales
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
            self.icon_editar = tk.PhotoImage(file=os.path.join(icons_path, "editar.png")).subsample(2, 2)
            self.icon_eliminar = tk.PhotoImage(file=os.path.join(icons_path, "eliminar.png")).subsample(2, 2)
            self.icon_cerrar = tk.PhotoImage(file=os.path.join(icons_path, "cerrar.png")).subsample(2, 2)
            self.icon_buscar = tk.PhotoImage(file=os.path.join(icons_path, "buscar.png")).subsample(2, 2)
            self.icon_limpiar = tk.PhotoImage(file=os.path.join(icons_path, "limpiar.png")).subsample(2, 2)
            # icon_guardar opcional; si no está, usamos icon_editar
            guardar_path = os.path.join(icons_path, "guardar.png")
            self.icon_guardar = tk.PhotoImage(file=guardar_path).subsample(2, 2) if os.path.exists(guardar_path) else None
        except Exception as e:
            print(f"Error cargando iconos: {e}")
            self.icon_editar = None
            self.icon_eliminar = None
            self.icon_cerrar = None
            self.icon_buscar = None
            self.icon_limpiar = None
            self.icon_guardar = None

    def create_titled_frame(self, parent, title, content_padx=10, content_pady=6):
        container = tk.Frame(parent, bg=self.COLORS['light'], relief='solid', borderwidth=1)

        header = tk.Frame(container, bg=self.COLORS['primary'], height=18)
        header.pack(fill='x')
        header.pack_propagate(False)

        label = tk.Label(header, text=title, font=('Segoe UI', 7, 'bold'),
                        fg=self.COLORS['white'], bg=self.COLORS['primary'])
        label.pack(side='left', padx=8, pady=1)

        # contenido en Light (antes estaba en blanco)
        content = tk.Frame(container, bg=self.COLORS['light'])
        content.pack(fill='both', expand=True, padx=content_padx, pady=content_pady)

        return container, content

    def setup_ui(self):
        
        style = ttk.Style(self.parent)

        # Etiquetas Light (ya usas Light.TLabel)
        style.configure('Light.TLabel',
                        background=self.COLORS['light'],
                        foreground=self.COLORS['text_dark'])
        
        style.configure('Light.TFrame', background=self.COLORS['light'])

        # Estilo para DateEntry (tkcalendar usa ttk internamente)
        style.configure('Light.DateEntry',
                        fieldbackground=self.COLORS['light'],
                        background=self.COLORS['light'],
                        foreground=self.COLORS['text_dark'])
        # Nota: según plataforma, también ayuda:
        style.map('Light.DateEntry',
                fieldbackground=[('readonly', self.COLORS['light']), ('!disabled', self.COLORS['light'])],
                foreground=[('!disabled', self.COLORS['text_dark'])])
        
        # --- Frame principal que contendrá todo ---
        main_container = tk.Frame(self.parent, bg=self.COLORS['light'])
        main_container.pack(fill="both", expand=True)

        # --- Título principal ---
        title_frame = tk.Frame(main_container, bg=self.COLORS['primary'], height=70)
        title_frame.pack(fill='x', padx=0)
        title_frame.pack_propagate(False)

        title_inner = tk.Frame(title_frame, bg=self.COLORS['primary'])
        title_inner.pack(fill='both', expand=True, padx=15, pady=8)

        top_strip = tk.Frame(main_container, bg=self.COLORS['primary'], height=6)
        top_strip.pack(fill='x', padx=0, pady=0)
        top_strip.pack_propagate(False)
        
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
        content_frame = tk.Frame(main_container, bg=self.COLORS['light'])
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.scrollable_frame = content_frame

        self.frame_principal = tk.Frame(self.scrollable_frame, bg=self.COLORS['light'])
        self.frame_principal.pack(fill="x", expand=False, pady=5)

        # Fechas
        self.frame_fechas_container, self.frame_fechas = self.create_titled_frame(
            self.frame_principal, "📅 Selección de Fechas", content_padx=5, content_pady=5
        )
        self.frame_fechas_container.config(bg=self.COLORS['light'])
        self.frame_fechas.config(bg=self.COLORS['light'])
        self.frame_fechas_container.pack(fill="x", expand=False, pady=5, padx=5)

        self.frame_rango = ttk.Frame(self.frame_fechas, style='Light.TFrame')
        self.frame_rango.pack(fill="x", expand=False, padx=5, pady=4)

        self.frame_rango.grid_columnconfigure(0, weight=0, minsize=80)
        self.frame_rango.grid_columnconfigure(1, weight=1, minsize=120)
        self.frame_rango.grid_columnconfigure(2, weight=0, minsize=80)
        self.frame_rango.grid_columnconfigure(3, weight=1, minsize=120)
        self.frame_rango.grid_columnconfigure(4, weight=0, minsize=20)
        self.frame_rango.grid_columnconfigure(5, weight=1, minsize=40)
        self.frame_rango.grid_columnconfigure(6, weight=0, minsize=20)
        self.frame_rango.grid_columnconfigure(7, weight=1, minsize=40)

        label_style = {'style': 'Light.TLabel'}
        padding_config = {'pady': 4}

        ttk.Label(self.frame_rango, text="Fecha Inicial:", **label_style).grid(
            row=0, column=0, padx=(10, 4), sticky='w', **padding_config
        )
        self.fecha_inicial = DateEntry(
            self.frame_rango,
            width=12,
            date_pattern='dd/mm/yyyy',
            state='normal',
            style='Light.DateEntry'
        )
        self.fecha_inicial.grid(row=0, column=1, padx=4, sticky='ew', **padding_config)

        ttk.Label(self.frame_rango, text="Fecha Final:", **label_style).grid(
            row=0, column=2, padx=4, sticky='w', **padding_config
        )
        self.fecha_final = DateEntry(
            self.frame_rango,
            width=12,
            date_pattern='dd/mm/yyyy',
            state='normal',
            style='Light.DateEntry'
        )
        self.fecha_final.grid(row=0, column=3, padx=4, sticky='ew', **padding_config)

        # relleno para cuadrícula
        ttk.Label(self.frame_rango, text="", **label_style).grid(row=0, column=4, padx=8, sticky='w', **padding_config)
        ttk.Label(self.frame_rango, text="", **label_style).grid(row=0, column=5, padx=8, sticky='ew', **padding_config)
        ttk.Label(self.frame_rango, text="", **label_style).grid(row=0, column=6, padx=8, sticky='w', **padding_config)
        ttk.Label(self.frame_rango, text="", **label_style).grid(row=0, column=7, padx=(8, 20), sticky='ew', **padding_config)

        # Combos sección 1
        self.frame_combos = tk.Frame(self.frame_principal, bg=self.COLORS['light'])
        self.frame_combos.pack(fill="x", expand=False, padx=5, pady=5)

        self.frame_combos1_container, self.frame_combos1 = self.create_titled_frame(
            self.frame_combos, "📍 Selección de Ubicación", content_padx=5, content_pady=5
        )
        self.frame_combos1_container.config(bg=self.COLORS['light'])
        self.frame_combos1.config(bg=self.COLORS['light'])
        self.frame_combos1_container.pack(fill="x", expand=False, padx=0, pady=8)

        self.frame_combos1.grid_columnconfigure(0, weight=0, minsize=80)
        self.frame_combos1.grid_columnconfigure(1, weight=1, minsize=120)
        self.frame_combos1.grid_columnconfigure(2, weight=0, minsize=80)
        self.frame_combos1.grid_columnconfigure(3, weight=1, minsize=120)
        self.frame_combos1.grid_columnconfigure(4, weight=0, minsize=100)
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

        # Combos sección 2
        self.frame_combos2_container, self.frame_combos2 = self.create_titled_frame(
            self.frame_combos, "💊 Insumos / Tipo Movimiento", content_padx=5, content_pady=5
        )
        self.frame_combos2_container.config(bg=self.COLORS['light'])
        self.frame_combos2.config(bg=self.COLORS['light'])
        self.frame_combos2_container.pack(fill="x", expand=False, padx=0, pady=5)

        # Nueva configuración de columnas con más ancho
        self.frame_combos2.grid_columnconfigure(0, weight=0, minsize=100)
        self.frame_combos2.grid_columnconfigure(1, weight=2, minsize=200)  # Aumentado
        self.frame_combos2.grid_columnconfigure(2, weight=0, minsize=20)   # Espaciador
        self.frame_combos2.grid_columnconfigure(3, weight=0, minsize=100)
        self.frame_combos2.grid_columnconfigure(4, weight=2, minsize=200)  # Aumentado

        # Primera fila: Tipo Insumo e Insumo
        ttk.Label(self.frame_combos2, text="Tipo\nInsumo:", **label_style).grid(
            row=0, column=0, padx=(20, 8), sticky='w', **padding_config
        )
        self.tipo_insumo_var = tk.StringVar()
        self.combo_tipo_insumo = AutocompleteCombobox(self.frame_combos2, textvariable=self.tipo_insumo_var, state="normal", font=('Segoe UI', 9))
        self.combo_tipo_insumo.grid(row=0, column=1, padx=8, sticky='ew', **padding_config)

        # Espaciador
        ttk.Label(self.frame_combos2, text="", **label_style).grid(row=0, column=2, padx=4)

        ttk.Label(self.frame_combos2, text="Insumo:", **label_style).grid(
            row=0, column=3, padx=8, sticky='w', **padding_config
        )
        self.insumo_var = tk.StringVar()
        self.combo_insumo = AutocompleteCombobox(self.frame_combos2, textvariable=self.insumo_var, state="normal", font=('Segoe UI', 9))
        self.combo_insumo.grid(row=0, column=4, padx=(8, 20), sticky='ew', **padding_config)

        # Tooltip para mostrar el nombre completo del Insumo
        self.tooltip_insumo = HoverTooltip(
            self.combo_insumo,
            text_provider=lambda: self.combo_insumo.get(),
            delay=250,
            show_only_if_clipped=True
        )

        # Segunda fila: Presentación y Tipo Movimiento
        ttk.Label(self.frame_combos2, text="Presentación:", **label_style).grid(
            row=1, column=0, padx=(20, 8), sticky='w', **padding_config
        )
        self.presentacion_var = tk.StringVar()
        self.combo_presentacion = AutocompleteCombobox(self.frame_combos2, textvariable=self.presentacion_var, state="normal", font=('Segoe UI', 9))
        self.combo_presentacion.config(completevalues=[''])
        self.combo_presentacion.grid(row=1, column=1, padx=8, sticky='ew', **padding_config)

        # Espaciador
        ttk.Label(self.frame_combos2, text="", **label_style).grid(row=1, column=2, padx=4)

        ttk.Label(self.frame_combos2, text="Tipo\nMovimiento:", **label_style).grid(
            row=1, column=3, padx=8, sticky='w', **padding_config
        )
        self.tipo_movimiento_var = tk.StringVar()
        self.combo_tipo_movimiento = AutocompleteCombobox(self.frame_combos2, textvariable=self.tipo_movimiento_var, state="normal", font=('Segoe UI', 9))
        self.combo_tipo_movimiento.grid(row=1, column=4, padx=(8, 20), sticky='ew', **padding_config)

        # Botones de búsqueda
        self.frame_botones_busqueda = tk.Frame(self.frame_principal, bg=self.COLORS['light'])
        self.frame_botones_busqueda.pack(fill="x", pady=8)

        self.btn_buscar = tk.Button(self.frame_botones_busqueda,
            text="Buscar Movimientos",
            image=self.icon_buscar,
            compound='left',
            command=self.buscar_movimientos,
            font=('Segoe UI', 9, 'bold'),
            bg=self.COLORS['light'],
            fg=self.COLORS['text_dark'],
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            padx=12,
            pady=5,
            cursor='hand2')
        self.btn_buscar.pack(side="left", padx=5)

        self.btn_limpiar = tk.Button(self.frame_botones_busqueda,
            text="Limpiar Filtros",
            image=self.icon_limpiar,
            compound='left',
            command=self.limpiar_filtros,
            font=('Segoe UI', 9, 'bold'),
            bg=self.COLORS['light'],
            fg=self.COLORS['text_dark'],
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            padx=12,
            pady=5,
            cursor='hand2')
        self.btn_limpiar.pack(side="left", padx=5)

        # Treeview igual a Ingreso: cuerpo blanco, encabezados gris claro
        header_bg = '#e5e7eb'
        header_fg = '#111827'
        style.configure('Correccion.Treeview',
                        background=self.COLORS['white'],
                        fieldbackground=self.COLORS['white'],
                        foreground=self.COLORS['text_dark'],
                        rowheight=18,
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
        
        # Resultados
        self.frame_treeview_container, self.frame_treeview = self.create_titled_frame(
            self.frame_principal, "📊 Resultados", content_padx=5, content_pady=5
        )
        self.frame_treeview_container.pack(fill="x", expand=False, padx=5, pady=8)

        self.tree_frame = tk.Frame(self.frame_treeview, bg=self.COLORS['light'], relief='solid', borderwidth=1)
        self.tree_frame.pack(fill="x", expand=False, padx=5, pady=5)
        self.tree_frame.pack_propagate(True)
        self.tree_frame.config(height=8 * 25 + 30)  # aprox para 8 filas

        # Scrollbars
        self.tree_scroll_y = ttk.Scrollbar(self.tree_frame)
        self.tree_scroll_y.pack(side="right", fill="y")
        self.tree_scroll_x = ttk.Scrollbar(self.tree_frame, orient="horizontal")
        self.tree_scroll_x.pack(side="bottom", fill="x")

        # Definición de columnas basadas en self.COLUMNAS
        columns = tuple(self.COLUMNAS)

        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=columns,
            show="headings",
            height=8,
            style='Correccion.Treeview'
        )

        # Encabezados visibles (igual a las columnas)
        encabezados_visibles = {
            'ID': 'ID',
            'Fecha': 'FECHA',
            'Área': 'ÁREA',
            'Distrito': 'DISTRITO',
            'Tipo de Servicio': 'TIPO SERVICIO',
            'Referencia': 'REFERENCIA',
            'Servicio': 'SERVICIO',
            'Tipo de Movimiento': 'TIPO MOVIMIENTO',
            'Lote': 'LOTE',
            'Fecha Vencimiento': 'VENCIMIENTO',
            'Cantidad': 'CANTIDAD',
            'Insumo': 'INSUMO',
            'Distrito Salida': 'SALIDA DISTRITO',
            'Servicio Salida': 'SALIDA SERVICIO',
            'Observaciones': 'OBSERVACIONES'
        }

        # Anchos aproximados por columna (ajústalos a tu gusto)
        anchos_columnas = {
            'ID': 60,
            'Fecha': 120,
            'Área': 120,
            'Distrito': 140,
            'Tipo de Servicio': 150,
            'Referencia': 120,
            'Servicio': 180,
            'Tipo de Movimiento': 150,
            'Lote': 100,
            'Fecha Vencimiento': 140,
            'Cantidad': 100,
            'Insumo': 260,
            'Distrito Salida': 150,
            'Servicio Salida': 150,
            'Observaciones': 260
        }

        # Justificación por columna
        justificacion = {
            'ID': 'center',
            'Fecha': 'center',
            'Área': 'w',
            'Distrito': 'w',
            'Tipo de Servicio': 'center',
            'Referencia': 'center',
            'Servicio': 'w',
            'Tipo de Movimiento': 'center',
            'Lote': 'center',
            'Fecha Vencimiento': 'center',
            'Cantidad': 'center',
            'Insumo': 'w',
            'Distrito Salida': 'w',
            'Servicio Salida': 'w',
            'Observaciones': 'w'
        }

        for col in columns:
            self.tree.heading(col, text=encabezados_visibles.get(col, col), anchor='center')
            self.tree.column(col, width=anchos_columnas.get(col, 120), minwidth=80, anchor=justificacion.get(col, 'w'))

        # Ubicar Treeview y conectar scrollbars existentes
        self.tree.pack(fill="both", expand=True)

        self.tree_scroll_y.config(orient="vertical", command=self.tree.yview)
        self.tree_scroll_x.config(orient="horizontal", command=self.tree.xview)

        self.tree.configure(yscrollcommand=self.tree_scroll_y.set, xscrollcommand=self.tree_scroll_x.set)

        # Botones de acción
        self.frame_botones_accion = tk.Frame(self.frame_principal, bg=self.COLORS['light'])
        self.frame_botones_accion.pack(fill="x", pady=12)

        btn_padx = 10
        btn_pady = 6
        btn_font = ('Segoe UI', 9, 'bold')
        btn_bg = self.COLORS['light']
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
            command=self.eliminar_movimiento_accion,
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
        try:
            self.combo_distrito.set_completion_list([''])
        except Exception:
            pass
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
            if hasattr(self, 'combo_area'):
                self.combo_area.config(completevalues=[''] + cache.get_area_names())
            if hasattr(self, 'combo_distrito'):
                self.combo_distrito.config(completevalues=[''])
            if hasattr(self, 'combo_tipo_insumo'):
                self.combo_tipo_insumo.config(completevalues=[''] + cache.get_tipos_insumo_names())
            if hasattr(self, 'combo_presentacion'):
                self.combo_presentacion.config(completevalues=[''])
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

    # Cargas dependientes
    def cargar_areas(self):
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
        self.combo_tipo_servicio.config(completevalues=[''])
        self.combo_tipo_servicio.set('')
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
        insumo_nombre = (self.insumo_var.get() or '').strip()
        tipo_insumo_desc = (self.tipo_insumo_var.get() or '').strip()
        tipo_insumo_id = cache.tipo_insumo_id(tipo_insumo_desc)
        if tipo_insumo_id and insumo_nombre:
            insumos = cache.get_insumos_por_tipo(tipo_insumo_id) or []
            insumo_sel = next((i for i in insumos if i['nombre'] == insumo_nombre), None)
            if insumo_sel:
                nombre_pres = insumo_sel.get('nombre_presentacion') or insumo_sel.get('presentacion')
                if nombre_pres:
                    try:
                        self.combo_presentacion.set_completion_list([nombre_pres])
                    except Exception:
                        self.combo_presentacion.config(completevalues=[nombre_pres])
                    self.presentacion_var.set(nombre_pres)
                    return
        try:
            self.combo_presentacion.set_completion_list([''])
        except Exception:
            self.combo_presentacion.config(completevalues=[''])
        self.presentacion_var.set('')

    def cargar_tipos_movimiento(self):
        self.tipos_movimiento = cache.tipos_movimiento
        self.combo_tipo_movimiento.config(completevalues=[''] + cache.get_tipos_movimiento_names())

    # Búsqueda
    def buscar_movimientos(self):
        try:
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
        self._enable_search_ui(True)

        if isinstance(data, Exception):
            messagebox.showerror("Error", f"Error al buscar movimientos:\n{data}")
            return

        self.movimientos_data = data

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
            # Cambio: usar cadena vacía en lugar de "N/A" para mantener consistencia
            fecha_venc = mov.get('fecha_vencimiento') or ""
            lote = mov.get('lote') or ""
            
            rows.append((
                mov.get('id', ''),                          # ID
                mov.get('fecha', ''),                       # Fecha
                mov.get('area_nombre', '') or "",           # Área
                mov.get('distrito_nombre', '') or "",       # Distrito
                mov.get('tipo_servicio_desc', '') or "",    # Tipo de Servicio
                mov.get('referencia', '') or "",            # Referencia
                mov.get('servicio_nombre', '') or "",       # Servicio
                mov.get('tipo_movimiento', '') or "",       # Tipo de Movimiento
                lote,                                       # Lote (CAMBIO: vacío en lugar de N/A)
                fecha_venc,                                 # Fecha Vencimiento (CAMBIO: vacío en lugar de N/A)
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
        self.fecha_inicial.set_date(datetime.now())
        self.fecha_final.set_date(datetime.now())

        self.combo_area.set('')
        self.combo_distrito.set('')
        self.combo_tipo_servicio.set('')
        self.combo_servicio.set('')
        self.combo_tipo_insumo.set('')
        self.combo_insumo.set('')
        self.combo_presentacion.set('')
        self.combo_tipo_movimiento.set('')

        self.tree.delete(*self.tree.get_children())
        self.movimientos_data = None

    # Edición
    def editar_movimiento(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un movimiento para editar")
            return

        item_values = self.tree.item(selected_item[0], 'values')
        movimiento_id = item_values[0]

        movimiento = next((m for m in self.movimientos_data if str(m['id']) == str(movimiento_id)), None)
        if not movimiento:
            messagebox.showerror("Error", "No se pudo encontrar el movimiento seleccionado")
            return

        self.abrir_ventana_edicion(movimiento)

    def abrir_ventana_edicion(self, movimiento):
        win = tk.Toplevel(self.parent)
        win.title("Editar Movimiento")
        win.configure(bg=self.COLORS['light'])
        win.grab_set()
        win.transient(self.parent)

        W, H = 980, 650
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        x, y = (sw - W)//2, (sh - H)//2
        win.geometry(f"{W}x{H}+{x}+{y}")
        win.resizable(True, True)

        # Helper tarjeta - COMPACTA EN ALTURA
        def card(parent, title, pad=(20, 6), header_h=22):
            cont = tk.Frame(parent, bg=self.COLORS['light'], relief='solid', borderwidth=1)
            cont.pack(fill="x", padx=pad[0], pady=pad[1])
            header = tk.Frame(cont, bg=self.COLORS['primary'], height=header_h)
            header.pack(fill='x')
            header.pack_propagate(False)
            tk.Label(header, text=title, font=('Segoe UI', 9, 'bold'),
                    fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(side='left', padx=10, pady=2)
            content = tk.Frame(cont, bg=self.COLORS['light'])
            content.pack(fill='x', padx=12, pady=4)
            return cont, content

        header_frame = tk.Frame(win, bg=self.COLORS['primary'], height=40)
        header_frame.pack(fill="x", padx=20, pady=(10, 6))
        header_frame.pack_propagate(False)
        tk.Label(
            header_frame, text="EDITAR MOVIMIENTO",
            font=('Segoe UI', 14, 'bold'), bg=self.COLORS['primary'], fg='white'
        ).pack(expand=True)

        # Vars
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
        presentacion_var = tk.StringVar(value=(movimiento.get('presentacion') or movimiento.get('nombre_presentacion') or "").strip())

        # DETALLES
        _, det = card(win, "📋 Detalles del Movimiento")
        for c in range(6):
            det.grid_columnconfigure(c, weight=1)

        ttk.Label(det, text="Fecha de Registro:", style='Light.TLabel').grid(row=0, column=0, padx=5, pady=4, sticky='w')
        fecha_entry = DateEntry(det, width=25, date_pattern='dd/mm/yyyy', style='Light.DateEntry')
        fecha_entry.grid(row=0, column=1, padx=5, pady=4, sticky='ew')
        
        def cargar_fecha_registro():
            if fecha_db:
                try:
                    if isinstance(fecha_db, (datetime, date)):
                        fecha_entry.set_date(fecha_db)
                    else:
                        try:
                            fecha_obj = datetime.strptime(str(fecha_db), '%Y-%m-%d')
                            fecha_entry.set_date(fecha_obj)
                        except ValueError:
                            fecha_obj = datetime.strptime(str(fecha_db), '%d/%m/%Y')
                            fecha_entry.set_date(fecha_obj)
                except Exception as e:
                    print(f"Error cargando fecha de registro: {e}, valor: {fecha_db}, tipo: {type(fecha_db)}")
        
        det.after(50, cargar_fecha_registro)

        ttk.Label(det, text="Referencia:", style='Light.TLabel').grid(row=0, column=2, padx=5, pady=4, sticky='w')
        ref_entry = ttk.Entry(det, textvariable=ref_var, width=27)
        ref_entry.grid(row=0, column=3, padx=5, pady=4, sticky='ew')

        ttk.Label(det, text="Tipo Movimiento:", style='Light.TLabel').grid(row=0, column=4, padx=5, pady=4, sticky='w')
        tipo_mov_cb = AutocompleteCombobox(det, textvariable=tipo_mov_var, width=25, state="normal")
        tipo_mov_cb.grid(row=0, column=5, padx=5, pady=4, sticky='ew')
        det.after_idle(lambda: tipo_mov_cb.set_completion_list(cache.get_tipos_movimiento_names() or []))

        ttk.Label(det, text="Lote:", style='Light.TLabel').grid(row=1, column=0, padx=5, pady=4, sticky='w')
        lote_row = tk.Frame(det, bg=self.COLORS['light'])
        lote_row.grid(row=1, column=1, padx=5, pady=4, sticky='ew')
        lote_row.columnconfigure(0, weight=1)
        lote_entry = ttk.Entry(lote_row, textvariable=lote_var, width=22)
        lote_entry.grid(row=0, column=0, sticky='ew')
        chk_sin_lote = tk.Checkbutton(
            lote_row, text="Sin lote", variable=sin_lote_var,
            command=lambda: lote_entry.config(state=('disabled' if sin_lote_var.get() else 'normal')),
            bg=self.COLORS['light'], fg=self.COLORS['text_dark'],
            activebackground=self.COLORS['light'], activeforeground=self.COLORS['text_dark'],
            highlightthickness=0, bd=0
        )
        chk_sin_lote.grid(row=0, column=1, padx=(8, 0), sticky='w')
        lote_entry.config(state=('disabled' if sin_lote_var.get() else 'normal'))

        ttk.Label(det, text="Fecha Vencimiento:", style='Light.TLabel').grid(row=1, column=2, padx=5, pady=4, sticky='w')
        fv_row = tk.Frame(det, bg=self.COLORS['light'])
        fv_row.grid(row=1, column=3, padx=5, pady=4, sticky='w')
        fecha_venc_entry = DateEntry(fv_row, width=15, date_pattern='dd/mm/yyyy', style='Light.DateEntry')
        fecha_venc_entry.pack(side='left')
        chk_sin_fv = tk.Checkbutton(
            fv_row, text="Sin fecha", variable=sin_fecha_var,
            command=lambda: fecha_venc_entry.config(state=('disabled' if sin_fecha_var.get() else 'normal')),
            bg=self.COLORS['light'], fg=self.COLORS['text_dark'],
            activebackground=self.COLORS['light'], activeforeground=self.COLORS['text_dark'],
            highlightthickness=0, bd=0
        )
        chk_sin_fv.pack(side='left', padx=(8, 0))
        
        def cargar_fecha_vencimiento():
            if fv_db:
                try:
                    if isinstance(fv_db, (datetime, date)):
                        fecha_venc_entry.set_date(fv_db)
                    else:
                        try:
                            fv_obj = datetime.strptime(str(fv_db), '%Y-%m-%d')
                            fecha_venc_entry.set_date(fv_obj)
                        except ValueError:
                            fv_obj = datetime.strptime(str(fv_db), '%d/%m/%Y')
                            fecha_venc_entry.set_date(fv_obj)
                except Exception as e:
                    print(f"Error cargando fecha vencimiento: {e}, valor: {fv_db}, tipo: {type(fv_db)}")
            
            fecha_venc_entry.config(state=('disabled' if sin_fecha_var.get() else 'normal'))
        
        fv_row.after(50, cargar_fecha_vencimiento)

        ttk.Label(det, text="Cantidad:", style='Light.TLabel').grid(row=1, column=4, padx=5, pady=4, sticky='w')
        cantidad_entry = ttk.Entry(det, textvariable=cantidad_var, width=27)
        cantidad_entry.grid(row=1, column=5, padx=5, pady=4, sticky='ew')

        ttk.Label(det, text="Observaciones:", style='Light.TLabel').grid(row=2, column=0, padx=5, pady=4, sticky='w')
        obs_entry = ttk.Entry(det, textvariable=obs_var, width=80)
        obs_entry.grid(row=2, column=1, columnspan=5, padx=5, pady=4, sticky='ew')

        # SALIDA NIVEL INFERIOR
        salida_container, salida_content = card(win, "🔄 Salida Nivel Inferior", pad=(20, 6))
        
        for c in range(4):
            salida_content.grid_columnconfigure(c, weight=1)
        
        ttk.Label(salida_content, text="Distrito Salida:", style='Light.TLabel').grid(row=0, column=0, padx=5, pady=4, sticky='w')
        distrito_salida_var = tk.StringVar()
        distrito_salida_cb = AutocompleteCombobox(salida_content, textvariable=distrito_salida_var, width=30, state="disabled")
        distrito_salida_cb.grid(row=0, column=1, padx=5, pady=4, sticky='ew')
        
        ttk.Label(salida_content, text="Servicio Salida:", style='Light.TLabel').grid(row=0, column=2, padx=5, pady=4, sticky='w')
        servicio_salida_var = tk.StringVar()
        servicio_salida_cb = AutocompleteCombobox(salida_content, textvariable=servicio_salida_var, width=30, state="disabled")
        servicio_salida_cb.grid(row=0, column=3, padx=5, pady=4, sticky='ew')
        
        distrito_salida_inicial = (movimiento.get('distrito_salida') or '').strip()
        servicio_salida_inicial = (movimiento.get('servicio_salida') or '').strip()
        if distrito_salida_inicial:
            distrito_salida_var.set(distrito_salida_inicial)
        if servicio_salida_inicial:
            servicio_salida_var.set(servicio_salida_inicial)
        
        def on_tipo_movimiento_change(*args):
            tipo_seleccionado = (tipo_mov_var.get() or '').strip().upper()
            if tipo_seleccionado == "SALIDA NIVEL INFERIOR":
                distrito_salida_cb.config(state="normal")
                servicio_salida_cb.config(state="normal")
                
                distritos_salida = cache.get_distritos_names()
                distrito_salida_cb.set_completion_list([''] + distritos_salida)
                
                if distrito_salida_inicial:
                    distrito_id = cache.distrito_id(distrito_salida_inicial)
                    if distrito_id:
                        tipos_serv = cache.get_tipos_servicio_por_distrito(distrito_id) or []
                        servicios = []
                        for ts in tipos_serv:
                            servicios.extend(cache.get_servicios_por_tipo(ts['id']) or [])
                        servicio_salida_cb.set_completion_list([''] + [s['nombre'] for s in servicios])
            else:
                distrito_salida_cb.config(state="disabled")
                servicio_salida_cb.config(state="disabled")
                distrito_salida_var.set('')
                servicio_salida_var.set('')
        
        def on_distrito_salida_change(*args):
            if distrito_salida_cb.cget('state') == 'disabled':
                return
                
            distrito_nombre = (distrito_salida_var.get() or '').strip()
            if not distrito_nombre:
                servicio_salida_cb.set_completion_list([''])
                servicio_salida_var.set('')
                return
            
            distrito_id = cache.distrito_id(distrito_nombre)
            if distrito_id:
                tipos_serv = cache.get_tipos_servicio_por_distrito(distrito_id) or []
                servicios = []
                for ts in tipos_serv:
                    servicios.extend(cache.get_servicios_por_tipo(ts['id']) or [])
                servicio_salida_cb.set_completion_list([''] + [s['nombre'] for s in servicios])
            else:
                servicio_salida_cb.set_completion_list([''])
        
        tipo_mov_var.trace_add('write', on_tipo_movimiento_change)
        distrito_salida_var.trace_add('write', on_distrito_salida_change)
        win.after(100, on_tipo_movimiento_change)
        
        # INSUMO
        _, ins = card(win, "💊 Insumo")
        for c in range(4):
            ins.grid_columnconfigure(c, weight=1)

        ttk.Label(ins, text="Insumo:", style='Light.TLabel').grid(row=0, column=0, padx=5, pady=4, sticky='w')
        insumo_wrap = tk.Label(
            ins, text=(movimiento.get('insumo_nombre') or ""),
            bg=self.COLORS['light'], fg=self.COLORS['text_dark'],
            font=('Segoe UI', 9), justify='left', anchor='w', wraplength=420
        )
        insumo_wrap.grid(row=0, column=1, padx=5, pady=4, sticky='ew')

        ttk.Label(ins, text="Presentación:", style='Light.TLabel').grid(row=0, column=2, padx=5, pady=4, sticky='w')
        presentacion_cb = AutocompleteCombobox(ins, textvariable=presentacion_var, width=25, state="normal")
        presentacion_cb.grid(row=0, column=3, padx=5, pady=4, sticky='ew')

        def cargar_presentacion_insumo():
            try:
                preset = (presentacion_var.get() or "").strip()
                if preset:
                    presentacion_cb.set_completion_list([preset])
                    return
                if getattr(self, '_idx_insumos_por_nombre', None) is None:
                    def build_and_set():
                        self._idx_insumos_por_nombre = {}
                        for ti in (cache.tipos_insumo or []):
                            for i in (cache.get_insumos_por_tipo(ti.get('id')) or []):
                                nombre = (i.get('nombre') or '').strip()
                                if nombre and nombre not in self._idx_insumos_por_nombre:
                                    self._idx_insumos_por_nombre[nombre] = i
                        ins_sel2 = self._idx_insumos_por_nombre.get((movimiento.get('insumo_nombre') or '').strip())
                        pres = (ins_sel2 or {}).get('nombre_presentacion') or (ins_sel2 or {}).get('presentacion') or ''
                        presentacion_var.set(pres)
                        presentacion_cb.set_completion_list([pres or ''])
                    ins.after(1, build_and_set)
                    return
                ins_sel = self._idx_insumos_por_nombre.get((movimiento.get('insumo_nombre') or '').strip())
                pres = (ins_sel or {}).get('nombre_presentacion') or (ins_sel or {}).get('presentacion') or ''
                presentacion_var.set(pres)
                presentacion_cb.set_completion_list([pres or ''])
            except Exception as e:
                print("Error determinando presentación:", e)
                presentacion_var.set('')
                presentacion_cb.set_completion_list([''])

        ins.after_idle(cargar_presentacion_insumo)

        # UBICACIÓN
        _, ubi = card(win, "📍 Ubicación")
        for c in range(4):
            ubi.grid_columnconfigure(c, weight=1)

        ttk.Label(ubi, text="Área:", style='Light.TLabel').grid(row=0, column=0, padx=5, pady=4, sticky='w')
        ttk.Label(ubi, text=movimiento.get('area_nombre', '') or "", style='Light.TLabel').grid(row=0, column=1, padx=5, pady=4, sticky='w')
        ttk.Label(ubi, text="Distrito:", style='Light.TLabel').grid(row=0, column=2, padx=5, pady=4, sticky='w')
        ttk.Label(ubi, text=movimiento.get('distrito_nombre', '') or "", style='Light.TLabel').grid(row=0, column=3, padx=5, pady=4, sticky='w')

        ttk.Label(ubi, text="Tipo de Servicio:", style='Light.TLabel').grid(row=1, column=0, padx=5, pady=4, sticky='w')
        ttk.Label(ubi, text=movimiento.get('tipo_servicio_desc', '') or "", style='Light.TLabel').grid(row=1, column=1, padx=5, pady=4, sticky='w')
        ttk.Label(ubi, text="Servicio:", style='Light.TLabel').grid(row=1, column=2, padx=5, pady=4, sticky='w')
        ttk.Label(ubi, text=movimiento.get('servicio_nombre', '') or "", style='Light.TLabel').grid(row=1, column=3, padx=5, pady=4, sticky='w')

        # BOTONES FIJOS EN PARTE INFERIOR
        btns_frame = tk.Frame(win, bg=self.COLORS['light'], height=50)
        btns_frame.pack(side="bottom", fill="x", padx=20, pady=10)
        btns_frame.pack_propagate(False)
        
        btns_inner = tk.Frame(btns_frame, bg=self.COLORS['light'])
        btns_inner.pack(expand=True)

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

                # IMPORTANTE: Limpiar distrito_salida y servicio_salida si NO es SALIDA NIVEL INFERIOR
                distrito_salida_val = None
                servicio_salida_val = None
                
                if tipo_mov_val.upper() == "SALIDA NIVEL INFERIOR":
                    distrito_salida_val = (distrito_salida_var.get() or '').strip() or None
                    servicio_salida_val = (servicio_salida_var.get() or '').strip() or None
                
                datos_actualizados = {
                    'id': movimiento['id'],
                    'fecha': fecha_val,
                    'referencia': ref_var.get(),
                    'tipo_movimiento': tipo_mov_val,
                    'lote': lote_val,
                    'fecha_vencimiento': fv_val,
                    'cantidad': cantidad_val,
                    'observaciones': obs_var.get(),
                    'distrito_salida': distrito_salida_val,
                    'servicio_salida': servicio_salida_val
                }

                # Guardar en base de datos
                actualizar_movimiento(datos_actualizados['id'], datos_actualizados)

                # PASO 1: Actualizar los datos en memoria (self.movimientos_data)
                for i, mov in enumerate(self.movimientos_data):
                    if str(mov['id']) == str(movimiento['id']):
                        # Actualizar todos los campos
                        self.movimientos_data[i]['fecha'] = fecha_val
                        self.movimientos_data[i]['referencia'] = datos_actualizados['referencia']
                        self.movimientos_data[i]['tipo_movimiento'] = tipo_mov_val
                        self.movimientos_data[i]['lote'] = lote_val if lote_val else ""
                        self.movimientos_data[i]['fecha_vencimiento'] = fv_val if fv_val else ""
                        self.movimientos_data[i]['cantidad'] = cantidad_val
                        self.movimientos_data[i]['observaciones'] = datos_actualizados['observaciones']
                        self.movimientos_data[i]['distrito_salida'] = distrito_salida_val if distrito_salida_val else ""
                        self.movimientos_data[i]['servicio_salida'] = servicio_salida_val if servicio_salida_val else ""
                        break

                # PASO 2: Actualizar la fila en el TreeView
                for item in self.tree.get_children():
                    item_values = self.tree.item(item, 'values')
                    if str(item_values[0]) == str(movimiento['id']):  # Comparar por ID
                        # Convertir fechas al formato DD/MM/YYYY para el TreeView
                        try:
                            fecha_mostrar = datetime.strptime(fecha_val, '%Y-%m-%d').strftime('%d/%m/%Y')
                        except Exception:
                            fecha_mostrar = fecha_val
                        
                        fv_mostrar = ""
                        if fv_val:
                            try:
                                fv_mostrar = datetime.strptime(fv_val, '%Y-%m-%d').strftime('%d/%m/%Y')
                            except Exception:
                                fv_mostrar = fv_val
                        
                        # Construir la nueva fila con los datos actualizados
                        # IMPORTANTE: Usar item_values[índice] para mantener los valores que no cambian
                        new_values = (
                            datos_actualizados['id'],                           # ID
                            fecha_mostrar,                                      # Fecha (ACTUALIZADO)
                            item_values[2],                                     # Área (mantener valor actual del tree)
                            item_values[3],                                     # Distrito (mantener valor actual del tree)
                            item_values[4],                                     # Tipo Servicio (mantener valor actual del tree)
                            datos_actualizados['referencia'],                   # Referencia (ACTUALIZADO)
                            item_values[6],                                     # Servicio (mantener valor actual del tree)
                            tipo_mov_val,                                       # Tipo Movimiento (ACTUALIZADO)
                            lote_val if lote_val else "",                       # Lote (ACTUALIZADO)
                            fv_mostrar,                                         # Fecha Vencimiento (ACTUALIZADO)
                            self.formato_float(cantidad_val),                   # Cantidad (ACTUALIZADO)
                            item_values[11],                                    # Insumo (mantener valor actual del tree)
                            distrito_salida_val if distrito_salida_val else "", # Distrito Salida (ACTUALIZADO)
                            servicio_salida_val if servicio_salida_val else "", # Servicio Salida (ACTUALIZADO)
                            datos_actualizados['observaciones']                 # Observaciones (ACTUALIZADO)
                        )
                        # Actualizar la fila del TreeView
                        self.tree.item(item, values=new_values)
                        break

                messagebox.showinfo("Éxito", "Movimiento actualizado correctamente")
                win.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al actualizar movimiento: {str(e)}")

        btn_guardar = tk.Button(
            btns_inner, text="GUARDAR",
            image=self.icon_guardar if self.icon_guardar else self.icon_editar,
            compound='left', command=guardar,
            bg=self.COLORS['light'], fg=self.COLORS['text_dark'],
            font=('Segoe UI', 9, 'bold'), relief='flat',
            padx=10, pady=10, cursor='hand2',
            borderwidth=0, highlightthickness=0
        )
        btn_guardar.pack(side='left', padx=10)

        btn_cerrar = tk.Button(
            btns_inner, text="CERRAR",
            image=self.icon_cerrar if self.icon_cerrar else None,
            compound='left', command=win.destroy,
            bg=self.COLORS['light'], fg=self.COLORS['text_dark'],
            font=('Segoe UI', 9, 'bold'), relief='flat',
            padx=10, pady=10, cursor='hand2',
            borderwidth=0, highlightthickness=0
        )
        btn_cerrar.pack(side='left', padx=10)

        ref_entry.focus_set()

    # Eliminación
    def eliminar_movimiento_accion(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un movimiento para eliminar")
            return

        item_values = self.tree.item(selected_item[0], 'values')
        movimiento_id = item_values[0]

        if not messagebox.askyesno(
            "Confirmar Eliminación",
            "¿Está seguro que desea eliminar este movimiento?\n\n"
            "Esta acción no se puede deshacer y puede afectar el saldo de inventario."
        ):
            return

        try:
            eliminar_movimiento(movimiento_id)
            messagebox.showinfo("Éxito", "Movimiento eliminado correctamente")
            self.buscar_movimientos()
        except Exception as e:
            messagebox.showerror("Error", f"Error al eliminar movimiento: {str(e)}")

    # Cierre
    def cerrar_ventana(self):
        if messagebox.askyesno("Confirmar", "¿Está seguro que desea cerrar esta ventana?"):
            for widget in self.parent.winfo_children():
                try:
                    widget.destroy()
                except Exception:
                    pass
            if self.main_window and hasattr(self.main_window, "show_welcome_screen"):
                self.main_window.show_welcome_screen()