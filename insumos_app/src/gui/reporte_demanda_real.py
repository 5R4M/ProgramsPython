import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import pandas as pd
from datetime import datetime, timedelta, date, time
import sys
import os
from ttkwidgets.autocomplete import AutocompleteCombobox

# ReportLab para PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

import fitz  # PyMuPDF
from PIL import Image, ImageTk
from ttkwidgets.autocomplete import AutocompleteCombobox

import locale

# Intentar establecer el locale a español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Linux
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES')  # Otro sistema
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, 'spanish')  # Windows
        except locale.Error:
            print("No se pudo establecer el locale a español")

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.db_manager import (
    obtener_areas,
    obtener_distritos_por_area,
    obtener_tipos_servicio_por_distrito,
    obtener_servicios_por_tipo,
    obtener_tipos_insumo,
    obtener_insumos_por_tipo,
    obtener_presentaciones,
    obtener_movimientos_kardex,
    conectar_db
)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        # En desarrollo, base_path es la raíz del proyecto (subir un nivel desde gui)
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(base_path, relative_path)

class ReporteDemandaReal:
    
    def __init__(self, parent_frame, main_window=None):
        self.parent = parent_frame
        self.main_window = main_window
        self.setup_styles()
        self.cargar_iconos()
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
  
        self.setup_ui()

    def setup_styles(self):
        # Paleta igual a IngresoInsumos
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
            'border':    '#bdc3c7',
            'header_dark': '#1f2937'
        }

        # Espaciados compactos como IngresoInsumos
        self.SPACING = {
            'section_pady': 2,
            'section_padx': 15,
            'card_padx': 8,
            'card_pady': 2,
            'header_height': 20,
            'content_padx': 10,
            'content_pady': 4,
            'label_pady': 2,
            'widget_pady': 2
        }

        try:
            ttk.Style().theme_use('clam')
        except Exception:
            pass

        style = ttk.Style(self.parent if hasattr(self, 'parent') else None)

        # Fondo general claro
        style.configure('MainArea.TFrame', background=self.COLORS['light'])

        # Tarjetas
        style.configure('Card.TFrame', background=self.COLORS['white'], relief='solid', borderwidth=1)
        style.configure('White.TFrame', background=self.COLORS['light'])

        # Encabezados de sección
        style.configure('Header.TFrame', background=self.COLORS['primary'])
        style.configure('Header.TLabel', background=self.COLORS['primary'], foreground=self.COLORS['white'], font=('Segoe UI', 8, 'bold'))

        # Labels y botones blancos
        style.configure('White.TLabel', background=self.COLORS['light'], foreground=self.COLORS['text_dark'], font=('Segoe UI', 9))
        style.configure('White.TButton', background=self.COLORS['white'], foreground=self.COLORS['text_dark'], font=('Segoe UI', 9), relief='flat', borderwidth=0)
        style.map('White.TButton', background=[('active', self.COLORS['light']), ('pressed', self.COLORS['light'])])

        # Botón primario (coherente con IngresoInsumos)
        style.configure('Primary.TButton', font=('Segoe UI', 9, 'bold'), padding=(10, 4), relief='flat', borderwidth=0, background=self.COLORS['accent'], foreground=self.COLORS['white'])
        style.map('Primary.TButton', background=[('active', '#2980b9'), ('pressed', '#117a8b')], foreground=[('active', '#ffffff'), ('pressed', '#ffffff')])

        # Radio y combo
        style.configure('White.TRadiobutton', background=self.COLORS['white'], foreground=self.COLORS['text_dark'], font=('Segoe UI', 9))
        style.configure('White.TCombobox', fieldbackground=self.COLORS['white'], background=self.COLORS['white'], foreground=self.COLORS['text_dark'])
    
    def create_titled_frame(self, parent, title, header_icon=None):
        # Contenedor tipo tarjeta (igual patrón que Kardex)
        container = tk.Frame(parent, bg=self.COLORS['light'], relief='solid', borderwidth=1)

        # Header compacto
        header = tk.Frame(container, bg=self.COLORS['primary'], height=self.SPACING['header_height'])
        header.pack(fill='x')
        header.pack_propagate(False)

        # Mini-ícono opcional
        if header_icon:
            tk.Label(
                header, text=header_icon,
                font=('Segoe UI Emoji', 9),
                fg=self.COLORS['white'], bg=self.COLORS['primary']
            ).pack(side='left', padx=(10, 4))

        # Título
        tk.Label(
            header, text=title,
            font=('Segoe UI', 8, 'bold'),
            fg=self.COLORS['white'], bg=self.COLORS['primary']
        ).pack(side='left', padx=2, pady=2)

        # Contenido
        content = tk.Frame(container, bg=self.COLORS['light'])
        content.pack(fill='both', expand=True, padx=10, pady=10)

        return container, content
  
    def cargar_iconos(self):
        try:
            icons_path = resource_path(os.path.join('utils', 'icons'))
          
            # Ajusta la ruta según tu proyecto
            self.icon_preview = tk.PhotoImage(file=os.path.join(icons_path, "vista_previa.png")).subsample(2, 2)
            self.icon_print = tk.PhotoImage(file=os.path.join(icons_path, "imprimir.png")).subsample(2, 2)
            self.icon_pdf = tk.PhotoImage(file=os.path.join(icons_path, "pdf.png")).subsample(2, 2)
            self.icon_excel = tk.PhotoImage(file=os.path.join(icons_path, "excel.png")).subsample(2, 2)
            self.icon_close = tk.PhotoImage(file=os.path.join(icons_path, "cerrar.png")).subsample(2, 2)
        except Exception as e:
            print(f"Error cargando iconos: {e}")
            self.icon_preview = None
            self.icon_print = None
            self.icon_pdf = None
            self.icon_excel = None
            self.icon_close = None
  
    def setup_ui(self):
        # Contenedor principal
        self.main_container = tk.Frame(self.parent, bg=self.COLORS['light'])
        self.main_container.pack(fill="both", expand=True)

        # Header principal (alineado a Kardex)
        title_frame = tk.Frame(self.main_container, bg=self.COLORS['primary'], height=70)
        title_frame.pack(fill='x', padx=0, pady=(10, 5))
        title_frame.pack_propagate(False)

        title_inner = tk.Frame(title_frame, bg=self.COLORS['primary'])
        title_inner.pack(fill='both', expand=True, padx=15, pady=8)

        tk.Label(
            title_inner,
            text="📑 Reporte Demanda Real por Servicio de Salud",
            font=('Segoe UI', 12, 'bold'),
            fg=self.COLORS['white'], bg=self.COLORS['primary']
        ).pack(anchor='w')

        tk.Label(
            title_inner,
            text="Consulte demanda de los movimientos de los insumos",
            font=('Segoe UI', 8),
            fg=self.COLORS['white'], bg=self.COLORS['primary']
        ).pack(anchor='w', pady=(2, 0))

        # Un único contenedor para secciones (igual que Kardex), controla el ancho
        self.frame_combos = ttk.Frame(self.main_container, style='White.TFrame')
        self.frame_combos.pack(fill="x", expand=False, padx=5, pady=5)

        # Corte Logístico
        self.frame_corte_container, self.frame_corte_content = self.create_titled_frame(
            self.frame_combos, "🗓️ Corte Logístico", header_icon=None
        )
        # Empaquetar igual que Kardex
        self.frame_corte_container.pack(fill="x", expand=False, pady=5)

        # Grid de corte
        self.frame_corte_content.grid_columnconfigure(1, weight=1)  # Año
        self.frame_corte_content.grid_columnconfigure(3, weight=1)  # Mes Inicio
        self.frame_corte_content.grid_columnconfigure(5, weight=1)  # Mes Final

        ttk.Label(self.frame_corte_content, text="Año:", style='White.TLabel').grid(row=0, column=0, padx=5, pady=2, sticky='w')
        self.anio_var = tk.StringVar()
        anios = [str(a) for a in range(datetime.now().year - 5, datetime.now().year + 2)]
        self.combo_anio = ttk.Combobox(self.frame_corte_content, textvariable=self.anio_var, values=anios, width=8, state="readonly")
        self.combo_anio.grid(row=0, column=1, padx=5, pady=2, sticky='ew')
        self.combo_anio.set(str(datetime.now().year))

        ttk.Label(self.frame_corte_content, text="Mes Inicio:", style='White.TLabel').grid(row=0, column=2, padx=5, pady=2, sticky='w')
        self.mes_inicio_var = tk.StringVar()
        self._meses_es = [datetime(2024, m, 1).strftime("%B").capitalize() for m in range(1, 13)]
        self.combo_mes_inicio = ttk.Combobox(self.frame_corte_content, textvariable=self.mes_inicio_var, values=self._meses_es, width=12, state="readonly")
        self.combo_mes_inicio.grid(row=0, column=3, padx=5, pady=2, sticky='ew')
        self.combo_mes_inicio.set(datetime.now().strftime("%B").capitalize())

        ttk.Label(self.frame_corte_content, text="Mes Final:", style='White.TLabel').grid(row=0, column=4, padx=5, pady=2, sticky='w')
        self.mes_final_var = tk.StringVar()
        self.combo_mes_final = ttk.Combobox(self.frame_corte_content, textvariable=self.mes_final_var, values=self._meses_es, width=12, state="readonly")
        self.combo_mes_final.grid(row=0, column=5, padx=5, pady=2, sticky='ew')
        self.combo_mes_final.set(datetime.now().strftime("%B").capitalize())

        # Eventos
        self.parent.after_idle(lambda: self.combo_anio.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte))
        self.parent.after_idle(lambda: self.combo_mes_inicio.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte))
        self.parent.after_idle(lambda: self.combo_mes_final.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte))

        # Ubicación (igual empaque que Kardex)
        self.frame_ubicacion_container, self.frame_ubicacion_content = self.create_titled_frame(
            self.frame_combos, "📍 Ubicación", header_icon=None
        )
        self.frame_ubicacion_container.pack(fill="x", expand=False, pady=5)

        self.frame_ubicacion_content.grid_columnconfigure(1, weight=1)
        self.frame_ubicacion_content.grid_columnconfigure(3, weight=1)
        self.frame_ubicacion_content.grid_columnconfigure(5, weight=1)
        self.frame_ubicacion_content.grid_columnconfigure(7, weight=1)

        label_style = {'style': 'White.TLabel'}
        ttk.Label(self.frame_ubicacion_content, text="Área:", **label_style).grid(row=0, column=0, padx=5, pady=2, sticky='w')
        self.area_var = tk.StringVar()
        self.combo_area = AutocompleteCombobox(self.frame_ubicacion_content, textvariable=self.area_var, state="normal", font=('Segoe UI', 9))
        self.combo_area.grid(row=0, column=1, padx=5, pady=2, sticky='ew')

        ttk.Label(self.frame_ubicacion_content, text="Distrito:", **label_style).grid(row=0, column=2, padx=5, pady=2, sticky='w')
        self.distrito_var = tk.StringVar()
        self.combo_distrito = AutocompleteCombobox(self.frame_ubicacion_content, textvariable=self.distrito_var, state="normal", font=('Segoe UI', 9))
        self.combo_distrito.grid(row=0, column=3, padx=5, pady=2, sticky='ew')

        ttk.Label(self.frame_ubicacion_content, text="Tipo de Servicio:", **label_style).grid(row=0, column=4, padx=5, pady=2, sticky='w')
        self.tipo_servicio_var = tk.StringVar()
        self.combo_tipo_servicio = AutocompleteCombobox(self.frame_ubicacion_content, textvariable=self.tipo_servicio_var, state="normal", font=('Segoe UI', 9))
        self.combo_tipo_servicio.grid(row=0, column=5, padx=5, pady=2, sticky='ew')

        ttk.Label(self.frame_ubicacion_content, text="Servicio:", **label_style).grid(row=0, column=6, padx=5, pady=2, sticky='w')
        self.servicio_var = tk.StringVar()
        self.combo_servicio = AutocompleteCombobox(self.frame_ubicacion_content, textvariable=self.servicio_var, state="normal", font=('Segoe UI', 9))
        self.combo_servicio.grid(row=0, column=7, padx=5, pady=2, sticky='ew')

        # Insumo (igual empaque que Kardex)
        self.frame_insumo_container, self.frame_insumo_content = self.create_titled_frame(
            self.frame_combos, "💊 Insumo", header_icon=None
        )
        self.frame_insumo_container.pack(fill="x", expand=False, pady=5)

        self.frame_insumo_content.grid_columnconfigure(1, weight=1)
        self.frame_insumo_content.grid_columnconfigure(3, weight=1)
        self.frame_insumo_content.grid_columnconfigure(5, weight=1)

        ttk.Label(self.frame_insumo_content, text="Tipo de Insumo:", **label_style).grid(row=0, column=0, padx=5, pady=2, sticky='w')
        self.tipo_insumo_var = tk.StringVar()
        self.combo_tipo_insumo = AutocompleteCombobox(self.frame_insumo_content, textvariable=self.tipo_insumo_var, state="normal", font=('Segoe UI', 9))
        self.combo_tipo_insumo.grid(row=0, column=1, padx=5, pady=2, sticky='ew')

        ttk.Label(self.frame_insumo_content, text="Insumo:", **label_style).grid(row=0, column=2, padx=5, pady=2, sticky='w')
        self.insumo_var = tk.StringVar()
        self.combo_insumo = AutocompleteCombobox(self.frame_insumo_content, textvariable=self.insumo_var, state="normal", font=('Segoe UI', 9))
        self.combo_insumo.grid(row=0, column=3, padx=5, pady=2, sticky='ew')

        ttk.Label(self.frame_insumo_content, text="Presentación:", **label_style).grid(row=0, column=4, padx=5, pady=2, sticky='w')
        self.presentacion_var = tk.StringVar()
        self.combo_presentacion = AutocompleteCombobox(self.frame_insumo_content, textvariable=self.presentacion_var, state="normal", font=('Segoe UI', 9))
        self.combo_presentacion.grid(row=0, column=5, padx=5, pady=2, sticky='ew')

        # Visor PDF alineado al ancho y con header como Kardex
        self.pdf_outer = tk.Frame(self.frame_combos, bg=self.COLORS['white'])
        self.pdf_outer.pack(fill="x", expand=False, pady=5)

        self.pdf_frame = tk.Frame(self.pdf_outer, bg=self.COLORS['white'], relief="solid", bd=1, highlightthickness=0)
        self.pdf_frame.pack(fill="x")
        self.pdf_frame.configure(height=350)
        self.pdf_frame.pack_propagate(False)

        self.pdf_header = tk.Frame(self.pdf_frame, bg=self.COLORS['primary'], height=26)
        self.pdf_header.pack(fill="x")
        self.pdf_header.pack_propagate(False)

        tk.Label(
            self.pdf_header,
            text="📄 Vista previa del PDF",
            font=('Segoe UI', 9, 'bold'),
            fg=self.COLORS['white'], bg=self.COLORS['primary']
        ).pack(side="left", padx=10, pady=2)

        # Cuerpo del visor
        self.pdf_body = tk.Frame(self.pdf_frame, bg=self.COLORS['white'])
        self.pdf_body.pack(fill="both", expand=True, padx=8, pady=8)

        # Botones abajo, mismo ancho
        self.frame_botones = ttk.Frame(self.main_container, style='White.TFrame')
        self.frame_botones.pack(fill="x", side="bottom", pady=(20, 10))

        btn_font = ('Segoe UI', 9, 'bold')
        btn_bg = self.COLORS['light']
        btn_fg = self.COLORS['text_dark']

        def make_btn(parent, text, cmd, img=None):
            return tk.Button(
                parent, text=text, command=cmd, font=btn_font, bg=btn_bg, fg=btn_fg,
                relief='flat', borderwidth=0, highlightthickness=0, padx=12, pady=6,
                cursor='hand2', image=img, compound='left'
            )

        btn_preview = make_btn(self.frame_botones, "Generar Vista Previa", self.generar_reporte, self.icon_preview)
        btn_preview.pack(side="left", padx=5)

        btn_print = make_btn(self.frame_botones, "Imprimir", self.imprimir_pdf, self.icon_print)
        btn_print.pack(side="left", padx=5)

        btn_pdf = make_btn(self.frame_botones, "Exportar a PDF", self.exportar_pdf, self.icon_pdf)
        btn_pdf.pack(side="left", padx=5)

        btn_excel = make_btn(self.frame_botones, "Exportar a Excel", self.exportar_excel, self.icon_excel)
        btn_excel.pack(side="left", padx=5)

        btn_close = make_btn(self.frame_botones, "Cerrar", self.cerrar_ventana, self.icon_close)
        btn_close.pack(side="right", padx=5)

        # Eventos Combos
        self.combo_area.bind('<<ComboboxSelected>>', self.cargar_distritos_por_area)
        self.combo_distrito.bind('<<ComboboxSelected>>', self.cargar_tipos_servicio)
        self.combo_tipo_servicio.bind('<<ComboboxSelected>>', self.cargar_servicios)
        self.combo_tipo_insumo.bind('<<ComboboxSelected>>', self.cargar_insumos)
        self.combo_insumo.bind('<<ComboboxSelected>>', self.actualizar_presentacion)

        # Cargar datos
        self.cargar_areas()
        self.distritos = []
        self.combo_distrito.set_completion_list([''])
        self.cargar_tipos_insumo()
        self.cargar_presentaciones()
      
    def calcular_rango_corte_logistico(self, anio, mes_inicio, mes_final):
        """
        Calcula el rango de fechas para el corte logístico.
        Del 26 del mes anterior al mes inicio hasta el 25 del mes final.
        Retorna (fecha_inicial, fecha_final) en formato dd/mm/yyyy
        """
        # Diccionario de meses en español a números
        meses_a_numero = {
            'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4,
            'Mayo': 5, 'Junio': 6, 'Julio': 7, 'Agosto': 8,
            'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12
        }

        # Convertir nombres de meses a números
        mes_inicio_num = meses_a_numero.get(mes_inicio)
        mes_final_num = meses_a_numero.get(mes_final)

        if not mes_inicio_num or not mes_final_num:
            raise ValueError("Los meses deben ser válidos")

        try:
            anio = int(anio)
        except ValueError:
            raise ValueError("Año debe ser un número válido")

        # Calcular fecha inicial (26 del mes anterior al mes inicio)
        if mes_inicio_num == 1:  # Si es enero, el mes anterior es diciembre del año anterior
            fecha_ini = datetime(anio - 1, 12, 26)
        else:
            fecha_ini = datetime(anio, mes_inicio_num - 1, 26)

        # Calcular fecha final (25 del mes final)
        fecha_fin = datetime(anio, mes_final_num, 25)

        return fecha_ini.strftime('%d/%m/%Y'), fecha_fin.strftime('%d/%m/%Y')

    def actualizar_fechas_por_corte(self, event=None):
        """
        Actualiza las fechas cuando se selecciona año, mes inicio y mes final
        """
        try:
            anio = self.anio_var.get()
            mes_inicio = self.mes_inicio_var.get()
            mes_final = self.mes_final_var.get()

            if anio and mes_inicio and mes_final:
                fecha_ini, fecha_fin = self.calcular_rango_corte_logistico(anio, mes_inicio, mes_final)
                # Solo para mostrar información, no necesitamos DateEntry
                print(f"Período: {fecha_ini} - {fecha_fin}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al calcular fechas: {str(e)}")

    def cargar_areas(self):
        areas_raw = obtener_areas()
        self.areas = [dict(a) for a in areas_raw] if areas_raw else []
        if self.areas:
            opciones = [''] + [a['nombre'] for a in self.areas]
            self.combo_area.set_completion_list(opciones)

    def cargar_distritos_por_area(self, event=None):
        area_nombre = self.combo_area.get().strip()
        if area_nombre:
            area = next((a for a in self.areas if a['nombre'] == area_nombre), None)
            if area:
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
                insumos_raw = obtener_insumos_por_tipo(tipo_insumo['id'])
                # Convertir sqlite3.Row a diccionarios
                self.insumos = [dict(i) for i in insumos_raw] if insumos_raw else []
                opciones = [''] + [i['nombre'] for i in self.insumos]
                self.combo_insumo.set_completion_list(opciones)

    def cargar_presentaciones(self):
        presentaciones_raw = obtener_presentaciones()
        self.presentaciones = [dict(p) for p in presentaciones_raw] if presentaciones_raw else []
        if self.presentaciones:
            opciones = [''] + [p['nombre'] for p in self.presentaciones]
            self.combo_presentacion.set_completion_list(opciones)

    def actualizar_presentacion(self, event=None):
        """
        Actualiza automáticamente la presentación cuando se selecciona un insumo
        """
        insumo_nombre = self.combo_insumo.get().strip()
        if insumo_nombre and self.insumos:
            insumo = next((i for i in self.insumos if i['nombre'] == insumo_nombre), None)
            if insumo:
                # Buscar la presentación del insumo seleccionado
                presentacion = insumo.get('nombre_presentacion', '')
                if presentacion:
                    self.combo_presentacion.set(presentacion)
                else:
                    # Si no tiene presentación específica, buscar en la lista general
                    if self.presentaciones:
                        # Tomar la primera presentación disponible como default
                        self.combo_presentacion.set(self.presentaciones[0]['nombre'])
                    else:
                        self.combo_presentacion.set('')
            else:
                self.combo_presentacion.set('')
        else:
            self.combo_presentacion.set('')


    def formato_valor(self, valor):
        """
        Formatea un valor numérico, mostrando 0 cuando el valor es 0
        """
        try:
            num = float(valor)
            return int(num) if num == int(num) else f"{num:.2f}"
        except (ValueError, TypeError):
            return "0"
  
    def generar_codigo_insumo(self, movimientos_raw):
        """
        Genera códigos con prefijo por tipo de insumo.
        - Normaliza los IDs (int) para evitar misses str/int.
        - Mantiene 1 consulta por los insumos presentes.
        - CORREGIDO: Enumera basado en la posición real dentro de cada tipo (empezando en 1)
        """
        # 1) Extraer insumos únicos normalizando a int
        insumos_unicos = {}
        for mov in movimientos_raw:
            insumo_id_raw = mov.get('codigo_insumo') or mov.get('insumo_id') or mov.get('codigo')
            if insumo_id_raw is None or str(insumo_id_raw).strip() == '':
                continue
            try:
                insumo_id = int(str(insumo_id_raw).strip())
            except:
                continue

            if insumo_id not in insumos_unicos:
                insumos_unicos[insumo_id] = mov.get('nombre_insumo', '')

        print(f"DEBUG OPT: Insumos únicos encontrados: {len(insumos_unicos)}")
        if not insumos_unicos:
            return {}

        try:
            conn = conectar_db()
            if not conn:
                print("DEBUG OPT: No se pudo conectar a la base de datos")
                return {}

            cursor = conn.cursor(dictionary=True)

            # 2) NUEVA CONSULTA: Obtener TODOS los insumos por tipo para calcular posición relativa
            query_tipos = """
                SELECT DISTINCT ti.id as tipo_id, ti.descripcion as tipo_descripcion
                FROM tipo_insumo ti
                INNER JOIN insumo i ON i.id_tipo_insumo = ti.id
                WHERE i.id IN ({})
                ORDER BY ti.descripcion
            """.format(','.join(['%s'] * len(insumos_unicos)))
            
            cursor.execute(query_tipos, list(insumos_unicos.keys()))
            tipos_resultado = cursor.fetchall()

            codigos_insumos = {}
            
            # 3) Para cada tipo de insumo, obtener TODOS los insumos de ese tipo ordenados por ID
            for tipo_info in tipos_resultado:
                tipo_id = tipo_info['tipo_id']
                tipo_descripcion = tipo_info['tipo_descripcion']
                
                # Consultar TODOS los insumos de este tipo ordenados por ID
                query_insumos_tipo = """
                    SELECT i.id AS insumo_id, i.nombre AS insumo_nombre
                    FROM insumo i
                    WHERE i.id_tipo_insumo = %s
                    ORDER BY i.id ASC
                """
                cursor.execute(query_insumos_tipo, (tipo_id,))
                todos_insumos_tipo = cursor.fetchall()
                
                # 4) Crear mapeo de ID a posición relativa (empezando en 1)
                posicion_en_tipo = {}
                for indice, insumo in enumerate(todos_insumos_tipo, 1):
                    posicion_en_tipo[insumo['insumo_id']] = indice
                
                # 5) Generar códigos solo para los insumos que están en movimientos_raw
                tipo_limpio = ''.join(c for c in tipo_descripcion.strip().upper() if c.isalnum())
                prefijo = (tipo_limpio[:4].upper() + 'XXXX')[:4] if tipo_limpio else 'XXXX'
                
                for insumo_id in insumos_unicos.keys():
                    if insumo_id in posicion_en_tipo:
                        posicion = posicion_en_tipo[insumo_id]
                        codigos_insumos[insumo_id] = f"{prefijo}-{posicion:04d}"

            conn.close()

            print(f"DEBUG OPT: Códigos generados: {len(codigos_insumos)} (muestra: {list(codigos_insumos.items())[:3]})")
            return codigos_insumos

        except Exception as e:
            print(f"DEBUG OPT: Error en generar_codigo_insumo: {e}")
            import traceback; traceback.print_exc()
            return {}

    def _to_datetime(self, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, time.min)
        if isinstance(value, str):
            try:
                return datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                return datetime.fromisoformat(value)
        raise TypeError(f"Tipo de fecha no soportado: {type(value)}")
  
    def procesar_datos(self, movimientos, fecha_ini, fecha_fin, dias):
        """
        Versión corregida de procesar_datos que integra correctamente la generación de códigos con prefijos
        """
        # 1. Generar códigos de insumos (1 consulta en lugar de N)
        codigos_insumos = self.generar_codigo_insumo(movimientos)
        
        print(f"DEBUG: Códigos generados para {len(codigos_insumos)} insumos")
        
        # 2. Procesar datos como antes, pero usando los códigos generados
        insumos = {}
        
        for mov in movimientos:
            insumo_id_raw = mov.get('codigo_insumo') or mov.get('insumo_id') or mov.get('codigo')
            try:
                insumo_id = int(str(insumo_id_raw).strip()) if insumo_id_raw else None
            except:
                insumo_id = None

            if insumo_id is None:
                continue  # no se puede mapear

            # CORREGIDO: Usar el código con prefijo generado
            codigo_con_prefijo = codigos_insumos.get(insumo_id)
            if not codigo_con_prefijo:
                codigo_con_prefijo = f"TEMP-{str(insumo_id).zfill(4)}"
            
            nombre_insumo = mov.get('nombre_insumo', '')
            presentacion = mov.get('nombre_presentacion', '')
            
            insumo_key = f"{codigo_con_prefijo}_{nombre_insumo}_{presentacion}"
            
            if insumo_key not in insumos:
                insumos[insumo_key] = {
                    'codigo': codigo_con_prefijo,  # Usar el código con prefijo
                    'insumo_id': insumo_id,  # AGREGADO: Guardar el ID para referencia
                    'nombre_insumo': nombre_insumo,
                    'presentacion': presentacion,
                    'entregado': {dia: 0 for dia in dias},
                    'no_entregado': {dia: 0 for dia in dias},
                    'inventario_inicial': 0,
                    'entrada_nivel_superior': 0,
                    'salida_nivel_inferior': 0,
                    'reajuste_positivo': 0,
                    'reajuste_negativo': 0
                }
            
            # Usar get() para obtener valores de manera segura
            fecha_str = mov.get('fecha', '')
            if not fecha_str:
                continue
                
            try:
                fecha_mov = self._to_datetime(fecha_str)
            except ValueError:
                continue
                
            dia = fecha_mov.day
            cantidad = mov.get('cantidad', 0)
            tipo_mov = mov.get('tipo_movimiento', '')
            
            if tipo_mov == 'ENTREGADO' and dia in dias:
                insumos[insumo_key]['entregado'][dia] += cantidad
            elif tipo_mov == 'NO ENTREGADO' and dia in dias:
                insumos[insumo_key]['no_entregado'][dia] += cantidad
            elif tipo_mov == 'INVENTARIO INICIAL':
                insumos[insumo_key]['inventario_inicial'] += cantidad
            elif tipo_mov == 'ENTRADA NIVEL SUPERIOR':
                insumos[insumo_key]['entrada_nivel_superior'] += cantidad
            elif tipo_mov == 'SALIDA NIVEL INFERIOR':
                insumos[insumo_key]['salida_nivel_inferior'] += cantidad
            elif tipo_mov == 'REAJUSTE POSITIVO':
                insumos[insumo_key]['reajuste_positivo'] += cantidad
            elif tipo_mov == 'REAJUSTE NEGATIVO':
                insumos[insumo_key]['reajuste_negativo'] += cantidad
        
        # 3. Procesar datos finales manteniendo el formato original
        datos_procesados = {}
        
        for insumo_key, valores in insumos.items():
            fila_datos = {
                'codigo': valores['codigo'],  # Usar el código con prefijo
                'insumo_id': valores['insumo_id'],  # AGREGADO: Para referencia
                'nombre_insumo': valores['nombre_insumo'],
                'presentacion': valores['presentacion']
            }
            
            # Agregar días
            for dia in dias:
                fila_datos[f'Día_{dia}_Entregado'] = self.formato_valor(valores['entregado'].get(dia, 0))
                fila_datos[f'Día_{dia}_No_Entregado'] = self.formato_valor(valores['no_entregado'].get(dia, 0))
            
            # Calcular totales
            total_entregado = sum(valores['entregado'].values())
            total_no_entregado = sum(valores['no_entregado'].values())
            
            # Calcular reajuste total (positivo - negativo)
            reajuste_total = valores['reajuste_positivo'] - valores['reajuste_negativo']
            
            # Calcular existencia según la fórmula
            existencia = (valores['inventario_inicial'] + 
                        valores['entrada_nivel_superior'] + 
                        valores['reajuste_positivo'] - 
                        valores['salida_nivel_inferior'] - 
                        total_entregado - 
                        valores['reajuste_negativo'])
            
            # Agregar totales
            fila_datos['Total_Entregado'] = self.formato_valor(total_entregado)
            fila_datos['Total_No_Entregado'] = self.formato_valor(total_no_entregado)
            fila_datos['Demanda'] = self.formato_valor(total_entregado + total_no_entregado)
            fila_datos['Existencia'] = self.formato_valor(existencia)
            fila_datos['Reajuste'] = self.formato_valor(reajuste_total)
            
            # Guardar valores originales para el PDF
            fila_datos['_valores_originales'] = {
                'entregado': valores['entregado'],
                'no_entregado': valores['no_entregado'],
                'total_entregado': total_entregado,
                'total_no_entregado': total_no_entregado,
                'existencia': existencia,
                'reajuste': reajuste_total
            }
            
            # **USAR EL CÓDIGO CON PREFIJO PARA LA CLAVE Y MOSTRAR**
            nueva_clave = f"{valores['codigo']} - {valores['nombre_insumo']} - {valores['presentacion']}"
            datos_procesados[nueva_clave] = fila_datos
        
        # AGREGADO: Guardar códigos para uso en Excel
        self.codigos_insumos = codigos_insumos
        
        return datos_procesados

    def exportar_excel(self):
        if not hasattr(self, 'dias') or not hasattr(self, 'datos'):
            messagebox.showerror("Error", "Primero debe generar la vista previa del reporte.")
            return

        try:         
            # Función para convertir número de columna a letra(s)
            def col_num_to_letter(col_num):
                """Convierte número de columna (0-based) a letra(s) de Excel"""
                result = ""
                while col_num >= 0:
                    result = chr(col_num % 26 + ord('A')) + result
                    col_num = col_num // 26 - 1
                    if col_num < 0:
                        break
                return result
            
            # Obtener período para el nombre del archivo
            anio = self.anio_var.get()
            mes_inicio = self.mes_inicio_var.get()
            mes_final = self.mes_final_var.get()
            periodo_str = f"{mes_inicio}_{mes_final}_{anio}"

            # Generar nombre de archivo con fecha y hora
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"Reporte_Demanda_Real_{periodo_str}_{timestamp}.xlsx"

            # Ruta a la carpeta Descargas
            downloads_path = os.path.expanduser("~/Downloads")
            full_path = os.path.join(downloads_path, file_name)

            # Crear archivo Excel
            writer = pd.ExcelWriter(full_path, engine='xlsxwriter')
            workbook = writer.book
            worksheet = workbook.add_worksheet('Demanda_Real')

            # CALCULAR NÚMERO TOTAL DE COLUMNAS PRIMERO
            fecha_ini_str, fecha_fin_str = self.calcular_rango_corte_logistico(anio, mes_inicio, mes_final)
            fecha_inicio = datetime.strptime(fecha_ini_str, '%d/%m/%Y')
            fecha_fin = datetime.strptime(fecha_fin_str, '%d/%m/%Y')

            # Generar lista de días hábiles
            dias = []
            fecha_iter = fecha_inicio
            while fecha_iter <= fecha_fin:
                if fecha_iter.weekday() < 5:  # 0=lunes, ..., 4=viernes
                    dias.append(fecha_iter.day)
                fecha_iter += timedelta(days=1)

            # Calcular columna final (Código + Medicamento + Movimientos + Días + 5 columnas finales)
            total_columnas = 3 + len(dias) + 5  # A, B, C + días + Total Entregado, Total No Entregado, Demanda, Existencia, Reajuste
            ultima_columna = col_num_to_letter(total_columnas - 1)  # Convertir a letra de columna

            # ESTILOS
            title_format = workbook.add_format({
                'bold': True,
                'align': 'center',
                'valign': 'vcenter',
                'font_size': 12,
                'text_wrap': True,
                'font_name': 'Arial'
            })

            subtitle_format = workbook.add_format({
                'bold': True,
                'align': 'center',
                'valign': 'vcenter',
                'font_size': 10,
                'text_wrap': True,
                'font_name': 'Arial'
            })

            timestamp_format = workbook.add_format({
                'align': 'center',
                'valign': 'vcenter',
                'font_size': 9,
                'text_wrap': True,
                'font_name': 'Arial'
            })

            filter_format = workbook.add_format({
                'align': 'left',
                'valign': 'vcenter',
                'font_size': 9,
                'text_wrap': True,
                'font_name': 'Arial'
            })

            header_format = workbook.add_format({
                'bold': True,
                'align': 'center',
                'valign': 'vcenter',
                'font_size': 8,
                'text_wrap': True,
                'font_name': 'Arial',
                'bg_color': '#ADD8E6',  # Azul claro
                'font_color': 'black',
                'border': 1,
                'border_color': 'black'
            })

            data_format = workbook.add_format({
                'align': 'center',
                'valign': 'vcenter',  # Cambié de 'top' a 'vcenter' para centrado vertical
                'font_size': 8,
                'font_name': 'Arial',
                'border': 1,
                'border_color': 'black'
            })

            # NUEVO: Formato específico para texto de medicamentos centrado
            text_format = workbook.add_format({
                'align': 'center',      # Centrado horizontal
                'valign': 'vcenter',    # Centrado vertical
                'font_size': 8,
                'font_name': 'Arial',
                'border': 1,
                'border_color': 'black',
                'text_wrap': True       # Habilitar ajuste automático de texto
            })

            # TÍTULOS PRINCIPALES - ABARCAN HASTA LA ÚLTIMA COLUMNA
            worksheet.merge_range(f'A1:{ultima_columna}1', 
                'DIRECCIÓN DEPARTAMENTAL DE REDES INTEGRADAS DE SERVICIOS DE SALUD DE GUATEMALA,', 
                title_format)
            worksheet.merge_range(f'A2:{ultima_columna}2', 'ÁREA NOR ORIENTE', subtitle_format)
            worksheet.merge_range(f'A3:{ultima_columna}3', 'REGISTRO DIARIO DE CONSUMO Y DEMANDA REAL', subtitle_format)
            worksheet.merge_range(f'A4:{ultima_columna}4', 
                f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", 
                timestamp_format)

            # FILTROS EN UNA SOLA FILA (fila 6)
            filtros = [
                f"Área: {self.combo_area.get()}",
                f"Distrito: {self.combo_distrito.get()}",
                f"Tipo de Servicio: {self.combo_tipo_servicio.get()}",
                f"Servicio: {self.combo_servicio.get()}"
            ]

            # Calcular ancho de cada filtro
            ancho_filtro = max(1, total_columnas // 4)
            col_actual = 0

            for i, filtro in enumerate(filtros):
                if i == 3:  # Último filtro, usar todas las columnas restantes
                    col_fin = total_columnas - 1
                else:
                    col_fin = min(col_actual + ancho_filtro - 1, total_columnas - 1)
                
                # Evitar merge de una sola celda
                if col_actual != col_fin:
                    col_inicio_letra = col_num_to_letter(col_actual)
                    col_fin_letra = col_num_to_letter(col_fin)
                    worksheet.merge_range(f'{col_inicio_letra}6:{col_fin_letra}6', filtro, filter_format)
                else:
                    col_letra = col_num_to_letter(col_actual)
                    worksheet.write(f'{col_letra}6', filtro, filter_format)
                
                col_actual = col_fin + 1

            # ENCABEZADOS DE LA TABLA (filas 8 y 9) - TODOS EN LAS MISMAS FILAS
            fila_encabezado_1 = 8
            fila_encabezado_2 = 9

            # COLUMNAS BÁSICAS (A, B, C)
            worksheet.merge_range(f'A{fila_encabezado_1}:A{fila_encabezado_2}', 'Código', header_format)
            worksheet.merge_range(f'B{fila_encabezado_1}:B{fila_encabezado_2}', 'MEDICAMENTO\nNombre, Concentración\ny Presentación', header_format)
            worksheet.merge_range(f'C{fila_encabezado_1}:C{fila_encabezado_2}', 'DIA DEL MES', header_format)

            # DÍAS DEL MES
            col_inicio_dias = 3  # Columna D (índice 3)
            col_fin_dias = col_inicio_dias + len(dias) - 1
            
            # Título "DÍA DEL MES" que abarca todos los días (FILA 8)
            if len(dias) > 1:
                col_inicio_dias_letra = col_num_to_letter(col_inicio_dias)
                col_fin_dias_letra = col_num_to_letter(col_fin_dias)
                worksheet.merge_range(f'{col_inicio_dias_letra}{fila_encabezado_1}:{col_fin_dias_letra}{fila_encabezado_1}', 
                                    'CANTIDAD DE MEDICAMENTOS Y/O PRODUCTOS A FIN', header_format)
            else:
                col_letra = col_num_to_letter(col_inicio_dias)
                worksheet.write(f'{col_letra}{fila_encabezado_1}', 'CANTIDAD DE MEDICAMENTOS Y/O PRODUCTOS A FIN', header_format)

            # Escribir números de días en la segunda fila (FILA 9)
            for i, dia in enumerate(dias):
                col_letra = col_num_to_letter(col_inicio_dias + i)
                worksheet.write(f'{col_letra}{fila_encabezado_2}', str(dia), header_format)

            # COLUMNAS FINALES - CORREGIDO: TODAS EN LAS MISMAS FILAS 8 Y 9
            col_total_entregado = col_fin_dias + 1
            col_total_no_entregado = col_total_entregado + 1
            col_demanda = col_total_no_entregado + 1
            col_existencia = col_demanda + 1
            col_reajuste = col_existencia + 1

            # ESCRIBIR TÍTULOS DE COLUMNAS FINALES EN LAS MISMAS FILAS QUE LOS DÍAS
            worksheet.merge_range(fila_encabezado_1-1, col_total_entregado, fila_encabezado_2-1, col_total_entregado, 
                                'Total\nEntregado', header_format)
            worksheet.merge_range(fila_encabezado_1-1, col_total_no_entregado, fila_encabezado_2-1, col_total_no_entregado, 
                                'Total\nNo\nEntregado', header_format)
            worksheet.merge_range(fila_encabezado_1-1, col_demanda, fila_encabezado_2-1, col_demanda, 
                                'Demanda', header_format)
            worksheet.merge_range(fila_encabezado_1-1, col_existencia, fila_encabezado_2-1, col_existencia, 
                                'Existencia', header_format)
            worksheet.merge_range(fila_encabezado_1-1, col_reajuste, fila_encabezado_2-1, col_reajuste, 
                                'Reajuste (+) (-)', header_format)

            # DATOS DE LA TABLA - Empezar en fila 10 (sin línea en blanco)
            fila_actual = 9  # Directamente después de los encabezados

            # **PROCESAR DATOS DE INSUMOS CON CÓDIGOS CON PREFIJOS CORRECTOS**
            for insumo_key, valores in self.datos.items():
                # CORREGIDO: Usar el código con prefijo que ya está en valores['codigo']
                codigo_con_prefijo = valores.get('codigo', '')
                
                # Mantener el nombre/presentación sin el número secuencial
                nombre_presentacion = f"{valores.get('nombre_insumo', '')} {valores.get('presentacion', '')}".strip()

                # Aplicar división de texto
                nombre_dividido = self.dividir_texto_en_lineas(nombre_presentacion, max_caracteres_por_linea=40)

                # Calcular totales
                total_entregado = valores.get('Total_Entregado', 0)
                total_no_entregado = valores.get('Total_No_Entregado', 0)
                demanda = valores.get('Demanda', 0)
                existencia = valores.get('Existencia', 0)
                reajuste = valores.get('Reajuste', 0)

                # FILA ENTREGADO
                # Combinar celdas verticalmente para código y nombre
                worksheet.merge_range(fila_actual, 0, fila_actual+1, 0, codigo_con_prefijo, data_format)  # **Código con prefijo**
                worksheet.merge_range(fila_actual, 1, fila_actual+1, 1, nombre_dividido, text_format)  # **Nombre con texto dividido**

                # Movimiento "Entregado"
                worksheet.write(fila_actual, 2, 'Entregado', data_format)

                # Días - valores entregados
                for i, dia in enumerate(dias):
                    valor = valores.get(f'Día_{dia}_Entregado', 0)
                    worksheet.write(fila_actual, col_inicio_dias + i, valor, data_format)

                # Totales para fila Entregado (combinar verticalmente)
                worksheet.merge_range(fila_actual, col_total_entregado, fila_actual+1, col_total_entregado, 
                                    total_entregado, data_format)
                worksheet.merge_range(fila_actual, col_total_no_entregado, fila_actual+1, col_total_no_entregado, 
                                    total_no_entregado, data_format)
                worksheet.merge_range(fila_actual, col_demanda, fila_actual+1, col_demanda, 
                                    demanda, data_format)
                worksheet.merge_range(fila_actual, col_existencia, fila_actual+1, col_existencia, 
                                    existencia, data_format)
                worksheet.merge_range(fila_actual, col_reajuste, fila_actual+1, col_reajuste, 
                                    reajuste, data_format)

                # FILA NO ENTREGADO
                # Movimiento "No Entregado"
                worksheet.write(fila_actual+1, 2, 'No Entregado', data_format)

                # Días - valores no entregados
                for i, dia in enumerate(dias):
                    valor = valores.get(f'Día_{dia}_No_Entregado', 0)
                    worksheet.write(fila_actual+1, col_inicio_dias + i, valor, data_format)

                fila_actual += 2  # Avanzar 2 filas para el siguiente insumo

            # CONFIGURACIÓN DE COLUMNAS - AUMENTAR ANCHO DE COLUMNA B Y AJUSTAR ALTURA DE FILAS
            worksheet.set_column('A:A', 12)   # Código - AUMENTADO para códigos con prefijos
            worksheet.set_column('B:B', 35)  # Medicamento
            worksheet.set_column('C:C', 12)  # Movimientos
            
            # Días (columnas más estrechas)
            for i in range(len(dias)):
                col_letter = col_num_to_letter(col_inicio_dias + i)
                worksheet.set_column(f'{col_letter}:{col_letter}', 4)
            
            # Columnas finales
            col_total_entregado_letra = col_num_to_letter(col_total_entregado)
            col_total_no_entregado_letra = col_num_to_letter(col_total_no_entregado)
            col_demanda_letra = col_num_to_letter(col_demanda)
            col_existencia_letra = col_num_to_letter(col_existencia)
            col_reajuste_letra = col_num_to_letter(col_reajuste)
            
            worksheet.set_column(f'{col_total_entregado_letra}:{col_total_entregado_letra}', 8)
            worksheet.set_column(f'{col_total_no_entregado_letra}:{col_total_no_entregado_letra}', 8)
            worksheet.set_column(f'{col_demanda_letra}:{col_demanda_letra}', 8)
            worksheet.set_column(f'{col_existencia_letra}:{col_existencia_letra}', 8)
            worksheet.set_column(f'{col_reajuste_letra}:{col_reajuste_letra}', 10)

            # **AJUSTAR ALTURA UNIFORME DE LAS FILAS DE DATOS**
            fila_inicio_datos = 9   # Empezamos en fila 9 (índice base-0), que es fila 10 en Excel
            fila_fin_datos = fila_actual - 1  # Última fila con datos

            altura_fila_uniforme = 25  # Altura en píxeles

            # Aplicar altura uniforme a todas las filas de datos
            for fila in range(fila_inicio_datos, fila_fin_datos + 1):
                worksheet.set_row(fila, altura_fila_uniforme)

            # CONFIGURACIÓN DE PÁGINA - TAMAÑO LEGAL
            worksheet.set_landscape()
            worksheet.set_paper(5)  # 5 = Legal (8.5 x 14 pulgadas)
            worksheet.set_margins(0.5, 0.5, 0.5, 0.5)
            worksheet.fit_to_pages(1, 0)  # 1 página de ancho, altura automática

            # Cerrar archivo
            writer.close()
            
            # Mensaje con opción de abrir archivo
            respuesta = messagebox.askyesno(
                "Éxito", 
                f"Reporte exportado exitosamente a:\n{full_path}\n\n¿Desea abrir el archivo?"
            )
            
            if respuesta:
                try:
                    import sys
                    if sys.platform.startswith('win'):
                        os.startfile(full_path)
                    elif sys.platform.startswith('darwin'):
                        os.system(f'open "{full_path}"')
                    else:
                        os.system(f'xdg-open "{full_path}"')
                except Exception as e:
                    messagebox.showwarning("Advertencia", f"No se pudo abrir el archivo automáticamente: {str(e)}")

        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar Excel: {str(e)}")
      
    def exportar_pdf(self):
        if not hasattr(self, 'temp_pdf_path') or not self.temp_pdf_path:
            messagebox.showerror("Error", "Primero debe generar la vista previa del reporte.")
            return

        downloads_path = os.path.expanduser("~/Downloads")
      
        # Generar nombre con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"Reporte_Demanda_Real_{self.periodo_str}_{timestamp}.pdf"
        full_path = os.path.join(downloads_path, file_name)

        try:
            import shutil
            shutil.copy2(self.temp_pdf_path, full_path)
          
            # Mensaje con opción de abrir archivo
            respuesta = messagebox.askyesno(
                "Éxito", 
                f"Reporte exportado exitosamente a:\n{full_path}\n\n¿Desea abrir el archivo?"
            )
          
            if respuesta:
                try:
                    import sys
                    if sys.platform.startswith('win'):
                        os.startfile(full_path)
                    elif sys.platform.startswith('darwin'):
                        os.system(f'open "{full_path}"')
                    else:
                        os.system(f'xdg-open "{full_path}"')
                except Exception as e:
                    messagebox.showwarning("Advertencia", f"No se pudo abrir el archivo automáticamente: {str(e)}")
                  
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar PDF: {str(e)}")

    def imprimir_pdf(self):
        try:
            import os
            import sys
            if not hasattr(self, 'temp_pdf_path') or not os.path.exists(self.temp_pdf_path):
                messagebox.showerror("Error", "Primero debe generar la vista previa del PDF.")
                return
            if sys.platform.startswith('win'):
                os.startfile(self.temp_pdf_path)
            elif sys.platform.startswith('darwin'):
                os.system(f'open "{self.temp_pdf_path}"')
            else:
                os.system(f'xdg-open "{self.temp_pdf_path}"')
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el PDF: {str(e)}")
  
    def generar_pdf(self, datos_movimientos, ruta_pdf):
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import legal, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from datetime import datetime, timedelta

        anio = self.anio_var.get()
        mes_inicio = self.mes_inicio_var.get()
        mes_final = self.mes_final_var.get()
        fecha_ini_str, fecha_fin_str = self.calcular_rango_corte_logistico(anio, mes_inicio, mes_final)
        fecha_inicio = datetime.strptime(fecha_ini_str, '%d/%m/%Y')
        fecha_fin = datetime.strptime(fecha_fin_str, '%d/%m/%Y')

        # Días hábiles
        dias = []
        fecha_iter = fecha_inicio
        while fecha_iter <= fecha_fin:
            if fecha_iter.weekday() < 5:
                dias.append(fecha_iter.day)
            fecha_iter += timedelta(days=1)

        # Códigos con prefijo
        codigos_insumos = self.generar_codigo_insumo(datos_movimientos)

        # Agrupar
        insumos = {}
        for mov in datos_movimientos:
            insumo_id_raw = mov.get('codigo_insumo') or mov.get('insumo_id') or mov.get('codigo')
            try:
                insumo_id = int(str(insumo_id_raw).strip()) if insumo_id_raw else None
            except:
                insumo_id = None
            if insumo_id is None:
                continue

            codigo_con_prefijo = codigos_insumos.get(insumo_id, f"TEMP-{str(insumo_id).zfill(4)}")
            nombre = mov.get('nombre_insumo', '')
            presentacion = mov.get('nombre_presentacion', '')
            key = (codigo_con_prefijo, f"{nombre} {presentacion}".strip())

            if key not in insumos:
                insumos[key] = {
                    'entregado': {d: 0 for d in dias},
                    'no_entregado': {d: 0 for d in dias},
                    'inventario_inicial': 0,
                    'entrada_nivel_superior': 0,
                    'salida_nivel_inferior': 0,
                    'reajuste_positivo': 0,
                    'reajuste_negativo': 0
                }

            fecha_mov = self._to_datetime(mov.get('fecha'))
            if fecha_mov is None:
                continue

            dia_mov = fecha_mov.day
            tipo = str(mov.get('tipo_movimiento', '')).upper()
            cantidad = mov.get('cantidad', 0)

            if fecha_inicio <= fecha_mov <= fecha_fin:
                if tipo == 'ENTREGADO' and dia_mov in dias:
                    insumos[key]['entregado'][dia_mov] += cantidad
                elif tipo == 'NO ENTREGADO' and dia_mov in dias:
                    insumos[key]['no_entregado'][dia_mov] += cantidad

            if tipo == 'INVENTARIO INICIAL':
                insumos[key]['inventario_inicial'] += cantidad
            elif tipo == 'ENTRADA NIVEL SUPERIOR':
                insumos[key]['entrada_nivel_superior'] += cantidad
            elif tipo == 'SALIDA NIVEL INFERIOR':
                insumos[key]['salida_nivel_inferior'] += cantidad
            elif tipo == 'REAJUSTE POSITIVO':
                insumos[key]['reajuste_positivo'] += cantidad
            elif tipo == 'REAJUSTE NEGATIVO':
                insumos[key]['reajuste_negativo'] += cantidad

        # Documento
        doc = SimpleDocTemplate(
            ruta_pdf,
            pagesize=landscape(legal),
            topMargin=0.5 * inch, bottomMargin=0.5 * inch,
            leftMargin=0.5 * inch, rightMargin=0.5 * inch
        )
        elementos = []
        estilos = getSampleStyleSheet()

        # Títulos superiores
        title_style = ParagraphStyle('CustomTitle', parent=estilos['Heading1'], alignment=1, spaceAfter=12, fontSize=12)
        subtitle_style = ParagraphStyle('CustomSubtitle', parent=estilos['Heading2'], alignment=1, spaceAfter=8, fontSize=10)
        timestamp_style = ParagraphStyle('TimestampStyle', parent=estilos['Normal'], alignment=1, spaceAfter=12, fontSize=9)

        # Estilos tabla
        header_title_style = ParagraphStyle('HeaderTitle', parent=estilos['Normal'], fontName='Helvetica-Bold', fontSize=6.2, leading=6.6, alignment=1, wordWrap='CJK')
        header_subtitle_style = ParagraphStyle('HeaderSubtitle', parent=estilos['Normal'], fontName='Helvetica-Bold', fontSize=6.0, leading=6.4, alignment=1, wordWrap='CJK')

        # Títulos de “Total Entregado/No Entregado” muy compactos
        header_totals_xxs = ParagraphStyle(
            'HeaderTotalsXXS', parent=estilos['Normal'],
            fontName='Helvetica-Bold', fontSize=4.7, leading=5.3, alignment=1, wordWrap='CJK'
        )
        # Truco de tracking: agregamos hair spaces para compactar sin romper palabras
        def compact(title):
            # inserta espacios finos entre palabras para permitir mejor ajuste
            return title.replace(' ', '\u2009')

        # Código pequeño
        cell_code_style = ParagraphStyle('CellCodeStyle', parent=estilos['Normal'], fontName='Helvetica', fontSize=5.2, leading=6.8, alignment=1, wordWrap='CJK')
        # Movimientos
        cell_mov_style = ParagraphStyle('CellMovStyle', parent=estilos['Normal'], fontName='Helvetica-Bold', fontSize=5.6, leading=6.8, alignment=1)
        # Días
        cell_day_style = ParagraphStyle('CellDayStyle', parent=estilos['Normal'], fontName='Helvetica', fontSize=5.4, leading=6.8, alignment=1)
        # Totales (contenido)
        cell_total_small = ParagraphStyle('CellTotalSmall', parent=estilos['Normal'], fontName='Helvetica-Bold', fontSize=5.2, leading=6.8, alignment=1)
        # Nombre de medicamento
        cell_text_style = ParagraphStyle('CellTextStyle', parent=estilos['Normal'], fontName='Helvetica', fontSize=6.0, leading=6.8, alignment=1)

        # Encabezado del documento
        elementos.append(Paragraph("DIRECCIÓN DEPARTAMENTAL DE REDES INTEGRADAS DE SERVICIOS DE SALUD DE GUATEMALA,", title_style))
        elementos.append(Paragraph("ÁREA NOR ORIENTE", subtitle_style))
        elementos.append(Paragraph("REGISTRO DIARIO DE CONSUMO Y DEMANDA REAL", subtitle_style))
        elementos.append(Paragraph(f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", timestamp_style))

        # Filtros
        left_style = ParagraphStyle('LeftAlign', alignment=0, fontSize=9, fontName='Helvetica')
        filtros = [
            f"Área: {self.combo_area.get()}",
            f"Distrito: {self.combo_distrito.get()}",
            f"Tipo de Servicio: {self.combo_tipo_servicio.get()}",
            f"Servicio: {self.combo_servicio.get()}"
        ]
        data_filtros = [[Paragraph(str(item), left_style) for item in filtros]]
        table_filtros = Table(data_filtros, colWidths=[150, 150, 150, 150])
        table_filtros.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ]))
        elementos.append(table_filtros)
        elementos.append(Spacer(1, 18))

        # Encabezados de tabla
        encabezado1 = [
            Paragraph('Código', header_title_style),
            Paragraph('MEDICAMENTO', header_title_style),
            Paragraph('DIA DEL MES', header_title_style),
            Paragraph('CANTIDAD DE MEDICAMENTOS Y/O PRODUCTOS A FIN', header_title_style)
        ] + [''] * (len(dias) - 1) + [
            Paragraph(compact('Total Entregado'), header_totals_xxs),
            Paragraph(compact('Total No Entregado'), header_totals_xxs),
            Paragraph('Demanda', header_title_style),
            Paragraph('Existencia', header_subtitle_style),  # se mantiene pequeño medio
            Paragraph('Reajuste (+) (-)', header_title_style)
        ]
        encabezado2 = [
            Paragraph('', header_subtitle_style),
            Paragraph('Nombre, Concentración y Presentación', header_subtitle_style),
            Paragraph('', header_subtitle_style)
        ] + [Paragraph(str(d), header_subtitle_style) for d in dias] + [
            Paragraph('', header_subtitle_style),
            Paragraph('', header_subtitle_style),
            Paragraph('', header_subtitle_style),
            Paragraph('', header_subtitle_style),
            Paragraph('', header_subtitle_style)
        ]
        data = [encabezado1, encabezado2]

        # Filas de datos
        for (codigo_con_prefijo, nombre_pres), valores in insumos.items():
            total_entregado = sum(valores['entregado'].get(d, 0) for d in dias)
            total_no_entregado = sum(valores['no_entregado'].get(d, 0) for d in dias)
            reajuste_total = valores['reajuste_positivo'] - valores['reajuste_negativo']
            existencia = (valores['inventario_inicial'] +
                        valores['entrada_nivel_superior'] +
                        valores['reajuste_positivo'] -
                        valores['salida_nivel_inferior'] -
                        total_entregado -
                        valores['reajuste_negativo'])

            codigo_paragraph = Paragraph(str(codigo_con_prefijo), cell_code_style)
            nombre_paragraph = Paragraph(str(nombre_pres), cell_text_style)

            mov_entregado = Paragraph('Entregado', cell_mov_style)
            mov_no_entregado = Paragraph('No Entregado', cell_mov_style)

            fila_entregado = [codigo_paragraph, nombre_paragraph, mov_entregado]
            for d in dias:
                fila_entregado.append(Paragraph(str(self.formato_valor(valores['entregado'].get(d, 0))), cell_day_style))
            fila_entregado += [
                Paragraph(str(self.formato_valor(total_entregado)), cell_total_small),
                Paragraph(str(self.formato_valor(total_no_entregado)), cell_total_small),
                Paragraph(str(self.formato_valor(total_entregado + total_no_entregado)), header_subtitle_style),
                Paragraph(str(self.formato_valor(existencia)), cell_total_small),
                Paragraph(str(self.formato_valor(reajuste_total)), header_subtitle_style),
            ]

            fila_no_entregado = [Paragraph('', cell_code_style), Paragraph('', cell_text_style), mov_no_entregado]
            for d in dias:
                fila_no_entregado.append(Paragraph(str(self.formato_valor(valores['no_entregado'].get(d, 0))), cell_day_style))
            fila_no_entregado += ['', '', '', '', '']

            data.append(fila_entregado)
            data.append(fila_no_entregado)

        # Anchos dinámicos: damos más aire a "Total Entregado" y "Total No Entregado"
        page_width, _ = landscape(legal)
        left_margin = doc.leftMargin
        right_margin = doc.rightMargin
        ancho_util = page_width - left_margin - right_margin

        num_dias = len(dias)
        base_codigo = 0.58 * inch
        base_medicamento = 2.45 * inch  # compactamos un poco más para ceder espacio a totales
        base_mov = 0.74 * inch
        base_dia = 0.22 * inch
        # base_totales: [Total Entregado, Total No Entregado, Demanda, Existencia, Reajuste]
        base_totales = [0.56 * inch, 0.56 * inch, 0.56 * inch, 0.58 * inch, 0.68 * inch]

        ancho_base = base_codigo + base_medicamento + base_mov + (base_dia * max(0, num_dias)) + sum(base_totales)
        if ancho_base > ancho_util:
            factor = max(0.70, min(1.0, ancho_util / ancho_base))
            base_codigo *= factor
            base_medicamento *= factor
            base_mov *= factor
            base_dia *= factor
            base_totales = [w * factor for w in base_totales]

        col_widths = [base_codigo, base_medicamento, base_mov] + [base_dia] * num_dias + base_totales
        suma_col = sum(col_widths)
        if suma_col > ancho_util and suma_col > 0:
            factor_final = ancho_util / suma_col
            col_widths = [w * factor_final for w in col_widths]

        # Tabla
        tabla = Table(data, repeatRows=2, colWidths=col_widths)

        # Estilos de tabla
        estilos_tabla = [
            # Spans de encabezado
            ('SPAN', (0, 0), (0, 1)),
            ('SPAN', (2, 0), (2, 1)),
            ('SPAN', (3, 0), (2 + num_dias, 0)),
            ('SPAN', (3 + num_dias, 0), (3 + num_dias, 1)),
            ('SPAN', (4 + num_dias, 0), (4 + num_dias, 1)),
            ('SPAN', (5 + num_dias, 0), (5 + num_dias, 1)),
            ('SPAN', (6 + num_dias, 0), (6 + num_dias, 1)),
            ('SPAN', (7 + num_dias, 0), (7 + num_dias, 1)),

            ('BACKGROUND', (0, 0), (-1, 1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

            ('ALIGN', (0, 2), (0, -1), 'CENTER'),
            ('VALIGN', (0, 2), (0, -1), 'MIDDLE'),
            ('ALIGN', (1, 2), (1, -1), 'CENTER'),
            ('VALIGN', (1, 2), (1, -1), 'MIDDLE'),

            # Padding y alto homogéneo
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2.3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.3),

            # Altura uniforme (ajusta 14->15 si lo deseas más alto)
            ('ROWHEIGHT', (0, 0), (-1, -1), 15),
        ]

        # Spans verticales por par de filas
        fila_inicio = 2
        while fila_inicio < len(data):
            fila_fin = fila_inicio + 1
            estilos_tabla.append(('SPAN', (0, fila_inicio), (0, fila_fin)))
            estilos_tabla.append(('SPAN', (1, fila_inicio), (1, fila_fin)))
            estilos_tabla.append(('SPAN', (3 + num_dias, fila_inicio), (3 + num_dias, fila_fin)))
            estilos_tabla.append(('SPAN', (4 + num_dias, fila_inicio), (4 + num_dias, fila_fin)))
            estilos_tabla.append(('SPAN', (5 + num_dias, fila_inicio), (5 + num_dias, fila_fin)))
            estilos_tabla.append(('SPAN', (6 + num_dias, fila_inicio), (6 + num_dias, fila_fin)))
            estilos_tabla.append(('SPAN', (7 + num_dias, fila_inicio), (7 + num_dias, fila_fin)))
            fila_inicio += 2

        tabla.setStyle(TableStyle(estilos_tabla))
        elementos.append(tabla)
        doc.build(elementos)
      
    def generar_reporte(self):
        # Validar que al menos el área esté seleccionada
        if not self.combo_area.get():
            messagebox.showerror("Error", "Debe seleccionar al menos el Área")
            return

        # Obtener fechas del corte logístico
        anio = self.anio_var.get()
        mes_inicio = self.mes_inicio_var.get()
        mes_final = self.mes_final_var.get()

        if not all([anio, mes_inicio, mes_final]):
            messagebox.showerror("Error", "Debe seleccionar Año, Mes Inicio y Mes Final")
            return

        fecha_ini_str, fecha_fin_str = self.calcular_rango_corte_logistico(anio, mes_inicio, mes_final)
        fecha_ini = datetime.strptime(fecha_ini_str, '%d/%m/%Y')
        fecha_fin = datetime.strptime(fecha_fin_str, '%d/%m/%Y')

        if fecha_fin < fecha_ini:
            messagebox.showerror("Error", "La fecha final debe ser mayor a la inicial")
            return

        # DEFINIR self.dias ANTES de llamar a procesar_datos
        self.dias = []
        fecha_iter = fecha_ini
        while fecha_iter <= fecha_fin:
            if fecha_iter.weekday() < 5:  # 0=lunes, ..., 4=viernes
                self.dias.append(fecha_iter.day)
            fecha_iter += timedelta(days=1)

        # Obtener nombres de los combos (pueden estar vacíos)
        distrito_nombre = self.combo_distrito.get().strip()
        tipo_servicio_desc = self.combo_tipo_servicio.get().strip()
        servicio_nombre = self.combo_servicio.get().strip()
        tipo_insumo_desc = self.combo_tipo_insumo.get().strip()
        insumo_nombre = self.combo_insumo.get().strip()
        presentacion_nombre = self.combo_presentacion.get().strip()

        # Obtener movimientos sin filtrar tipo movimiento
        # Pasar None o el valor según si está vacío
        movimientos_raw = obtener_movimientos_kardex(
            fecha_ini.strftime('%Y-%m-%d'),
            fecha_fin.strftime('%Y-%m-%d'),
            distrito_nombre if distrito_nombre else None,
            tipo_servicio_desc if tipo_servicio_desc else None,
            servicio_nombre if servicio_nombre else None,
            tipo_insumo_desc if tipo_insumo_desc else None,
            insumo_nombre if insumo_nombre else None,
            presentacion_nombre if presentacion_nombre else None
        )

        if not movimientos_raw:
            messagebox.showinfo("Info", "No hay datos para mostrar")
            return

        # Filtrar movimientos relevantes para demanda real
        movimientos_filtrados = [m for m in movimientos_raw if m.get('tipo_movimiento', '').upper() in [
            'ENTREGADO', 'NO ENTREGADO', 'REAJUSTE POSITIVO', 'REAJUSTE NEGATIVO', 'INVENTARIO INICIAL', 'ENTRADA NIVEL SUPERIOR', 'SALDO ANTERIOR'
        ]]

        # **USAR EL NUEVO MÉTODO CON CÓDIGOS CON PREFIJOS**
        self.datos = self.procesar_datos(movimientos_filtrados, fecha_ini, fecha_fin, self.dias)

        periodo_str = f"{fecha_ini.strftime('%d%m%Y')}_{fecha_fin.strftime('%d%m%Y')}"
        self.periodo_str = periodo_str

        import tempfile
        temp_dir = tempfile.gettempdir()
        self.temp_pdf_path = os.path.join(temp_dir, f"vista_previa_demanda_real_{periodo_str}.pdf")
      
        # **MODIFICAR generar_pdf para usar los códigos con prefijos**
        self.generar_pdf(movimientos_filtrados, self.temp_pdf_path)

        self.generar_vista_previa_pdf()

    def generar_vista_previa_pdf(self):
        try:
            # --- Limpiar visor PDF ---
            body_target = getattr(self, 'pdf_body', self.pdf_frame)
            for widget in body_target.winfo_children():
                widget.destroy()
            contenedor = tk.Frame(body_target, bg=self.COLORS['white'])

            # --- Contenedor principal para visor y controles ---
            contenedor = tk.Frame(self.pdf_frame, bg=self.COLORS['white'])
            contenedor.pack(fill="both", expand=True)

            # --- Frame para controles de navegación (abajo, fondo blanco) ---
            control_frame = tk.Frame(contenedor, bg=self.COLORS['white'])
            control_frame.pack(fill="x", side="bottom", pady=5)

            # --- Frame del visor PDF (canvas + scrollbars) ---
            canvas_frame = tk.Frame(contenedor, bg=self.COLORS['white'])
            canvas_frame.pack(side="top", fill="both", expand=True)

            # Scrollbars
            v_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical")
            v_scrollbar.pack(side="right", fill="y")
            h_scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal")
            h_scrollbar.pack(side="bottom", fill="x")

            # Canvas
            canvas = tk.Canvas(
                canvas_frame,
                bg=self.COLORS['white'],
                yscrollcommand=v_scrollbar.set,
                xscrollcommand=h_scrollbar.set,
                highlightthickness=0
            )
            canvas.pack(side="left", fill="both", expand=True)
            v_scrollbar.config(command=canvas.yview)
            h_scrollbar.config(command=canvas.xview)

            # Abrir PDF y preparar navegación
            doc = fitz.open(self.temp_pdf_path)
            self.current_page = 0
            self.total_pages = len(doc)
            self.zoom_level = 1.5

            def display_page():
                canvas.delete("all")
                page = doc.load_page(self.current_page)
                pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom_level, self.zoom_level))
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                tk_img = ImageTk.PhotoImage(image=img)
                canvas.image = tk_img

                canvas_width = canvas.winfo_width()
                canvas_height = canvas.winfo_height()
                x = max((canvas_width - pix.width) // 2, 0)
                y = max((canvas_height - pix.height) // 2, 0)

                canvas.create_image(x, y, anchor="nw", image=tk_img)
                canvas.config(scrollregion=canvas.bbox("all"))
                page_label.config(text=f"Página {self.current_page + 1} de {self.total_pages}")
                zoom_label.config(text=f"Zoom: {int(self.zoom_level * 100)}%")

            def change_page(delta):
                self.current_page = max(0, min(self.current_page + delta, self.total_pages - 1))
                display_page()
                btn_anterior.config(state="normal" if self.current_page > 0 else "disabled")
                btn_siguiente.config(state="normal" if self.current_page < self.total_pages - 1 else "disabled")

            def change_zoom(delta):
                self.zoom_level = max(0.5, min(self.zoom_level + delta, 3.0))
                display_page()
                zoom_label.config(text=f"Zoom: {int(self.zoom_level * 100)}%")

            def fit_to_width():
                try:
                    canvas_width = canvas.winfo_width()
                    if canvas_width > 100:
                        page = doc.load_page(self.current_page)
                        zoom = (canvas_width - 20) / page.rect.width
                        self.zoom_level = max(0.5, min(zoom, 3.0))
                        display_page()
                        zoom_label.config(text=f"Zoom: {int(self.zoom_level * 100)}%")
                except Exception as e:
                    print(f"Error en fit_to_width: {e}")

            def fit_to_page():
                try:
                    canvas_width = canvas.winfo_width()
                    canvas_height = canvas.winfo_height()
                    if canvas_width > 100 and canvas_height > 100:
                        page = doc.load_page(self.current_page)
                        zoom_x = (canvas_width - 20) / page.rect.width
                        zoom_y = (canvas_height - 20) / page.rect.height
                        zoom = min(zoom_x, zoom_y)
                        self.zoom_level = max(0.5, min(zoom, 3.0))
                        display_page()
                        zoom_label.config(text=f"Zoom: {int(self.zoom_level * 100)}%")
                except Exception as e:
                    print(f"Error en fit_to_page: {e}")

            def maximizar_reporte():
                try:
                    ventana_max = tk.Toplevel(self.parent)
                    ventana_max.title("Reporte Demanda Real - Vista Maximizada")
                    ventana_max.configure(bg=self.COLORS['white'])
                    ventana_max.state('zoomed')
                    ventana_max.resizable(True, True)

                    main_frame = tk.Frame(ventana_max, bg=self.COLORS['white'])
                    main_frame.pack(fill="both", expand=True)

                    control_top_frame = tk.Frame(main_frame, bg=self.COLORS['white'])
                    control_top_frame.pack(fill="x", pady=5)

                    btn_cerrar_max = tk.Button(
                        control_top_frame, text="✕ Cerrar Vista Maximizada",
                        command=ventana_max.destroy,
                        bg=self.COLORS['danger'], fg='white',
                        font=('Segoe UI', 10, 'bold'), relief='flat', borderwidth=0, cursor='hand2',
                        pady=8, padx=15
                    )
                    btn_cerrar_max.pack(side="right", padx=10)

                    btn_abrir_externo = tk.Button(
                        control_top_frame, text="📄 Abrir en App Externa",
                        command=self.abrir_pdf_externo,
                        bg=self.COLORS['primary'], fg='white',
                        font=('Segoe UI', 10, 'bold'), relief='flat', borderwidth=0, cursor='hand2',
                        pady=8, padx=15
                    )
                    btn_abrir_externo.pack(side="right", padx=5)

                    canvas_max_frame = tk.Frame(main_frame, bg=self.COLORS['white'])
                    canvas_max_frame.pack(side="top", fill="both", expand=True, padx=5)

                    h_scroll_max = ttk.Scrollbar(canvas_max_frame, orient="horizontal")
                    h_scroll_max.pack(side="bottom", fill="x")

                    v_scroll_max = ttk.Scrollbar(canvas_max_frame, orient="vertical")
                    v_scroll_max.pack(side="right", fill="y")

                    canvas_max = tk.Canvas(
                        canvas_max_frame,
                        xscrollcommand=h_scroll_max.set,
                        yscrollcommand=v_scroll_max.set,
                        bg=self.COLORS['white'],
                        highlightthickness=0
                    )
                    canvas_max.pack(side="left", fill="both", expand=True)

                    h_scroll_max.config(command=canvas_max.xview)
                    v_scroll_max.config(command=canvas_max.yview)

                    control_max_frame = tk.Frame(main_frame, bg=self.COLORS['white'])
                    control_max_frame.pack(fill="x", side="bottom", pady=5)

                    current_page_max = [0]
                    zoom_level_max = [1.0]

                    def display_page_max():
                        canvas_max.delete("all")
                        page = doc.load_page(current_page_max[0])
                        pix = page.get_pixmap(matrix=fitz.Matrix(zoom_level_max[0], zoom_level_max[0]))
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        tk_img = ImageTk.PhotoImage(image=img)
                        canvas_max.image = tk_img

                        canvas_width = canvas_max.winfo_width()
                        canvas_height = canvas_max.winfo_height()
                        x = max((canvas_width - pix.width) // 2, 0)
                        y = max((canvas_height - pix.height) // 2, 0)

                        canvas_max.create_image(x, y, anchor="nw", image=tk_img)
                        canvas_max.config(scrollregion=canvas_max.bbox("all"))

                    def change_page_max(delta):
                        current_page_max[0] = max(0, min(current_page_max[0] + delta, self.total_pages - 1))
                        display_page_max()
                        page_label_max.config(text=f"Página {current_page_max[0] + 1} de {self.total_pages}")

                    def change_zoom_max(delta):
                        zoom_level_max[0] = max(0.5, min(zoom_level_max[0] + delta, 4.0))
                        display_page_max()
                        zoom_label_max.config(text=f"Zoom: {int(zoom_level_max[0] * 100)}%")

                    def fit_to_page_max():
                        try:
                            canvas_width = canvas_max.winfo_width()
                            canvas_height = canvas_max.winfo_height()
                            if canvas_width > 100 and canvas_height > 100:
                                page = doc.load_page(current_page_max[0])
                                zoom_x = (canvas_width - 20) / page.rect.width
                                zoom_y = (canvas_height - 20) / page.rect.height
                                zoom = min(zoom_x, zoom_y)
                                zoom_level_max[0] = max(0.5, min(zoom, 4.0))
                                display_page_max()
                                zoom_label_max.config(text=f"Zoom: {int(zoom_level_max[0] * 100)}%")
                        except Exception as e:
                            print(f"Error en fit_to_page_max: {e}")

                    btn_prev_max = tk.Button(
                        control_max_frame, text="◀◀ Anterior", command=lambda: change_page_max(-1),
                        bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                        font=('Segoe UI', 11, 'bold'), relief='flat', borderwidth=1, cursor='hand2',
                        pady=5, padx=15
                    )
                    btn_prev_max.pack(side="left", padx=5)

                    page_label_max = tk.Label(
                        control_max_frame, text=f"Página 1 de {self.total_pages}",
                        bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                        font=('Segoe UI', 11, 'bold')
                    )
                    page_label_max.pack(side="left", padx=10)

                    btn_next_max = tk.Button(
                        control_max_frame, text="Siguiente ▶▶", command=lambda: change_page_max(1),
                        bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                        font=('Segoe UI', 11, 'bold'), relief='flat', borderwidth=1, cursor='hand2',
                        pady=5, padx=15
                    )
                    btn_next_max.pack(side="left", padx=5)

                    btn_zoom_out_max = tk.Button(
                        control_max_frame, text="🔍− Alejar", command=lambda: change_zoom_max(-0.25),
                        bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                        font=('Segoe UI', 10, 'bold'), relief='flat', borderwidth=1, cursor='hand2',
                        pady=5, padx=10
                    )
                    btn_zoom_out_max.pack(side="left", padx=5)

                    zoom_label_max = tk.Label(
                        control_max_frame, text=f"Zoom: {int(zoom_level_max[0] * 100)}%",
                        bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                        font=('Segoe UI', 10, 'bold')
                    )
                    zoom_label_max.pack(side="left", padx=5)

                    btn_zoom_in_max = tk.Button(
                        control_max_frame, text="🔍+ Acercar", command=lambda: change_zoom_max(0.25),
                        bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                        font=('Segoe UI', 10, 'bold'), relief='flat', borderwidth=1, cursor='hand2',
                        pady=5, padx=10
                    )
                    btn_zoom_in_max.pack(side="left", padx=5)

                    ventana_max.bind("<Configure>", lambda e: fit_to_page_max())

                    display_page_max()

                    canvas_max.bind("<MouseWheel>", lambda e: canvas_max.yview_scroll(int(-1*(e.delta/120)), "units"))

                    ventana_max.focus_force()
                    ventana_max.grab_set()

                except Exception as e:
                    messagebox.showerror("Error", f"Error al maximizar reporte: {str(e)}")

            # Controles normales

            btn_anterior = tk.Button(
                control_frame, text="◀", command=lambda: change_page(-1),
                bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                font=('Segoe UI', 10, 'bold'), relief='flat', borderwidth=0, cursor='hand2',
                activebackground=self.COLORS['white'], activeforeground=self.COLORS['text_dark']
            )
            btn_anterior.pack(side="left", padx=(10, 2), pady=2)

            page_label = tk.Label(
                control_frame, text=f"Página 1 de {self.total_pages}",
                bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                font=('Segoe UI', 10, 'bold')
            )
            page_label.pack(side="left", padx=2, pady=2)

            btn_siguiente = tk.Button(
                control_frame, text="▶", command=lambda: change_page(1),
                bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                font=('Segoe UI', 10, 'bold'), relief='flat', borderwidth=0, cursor='hand2',
                activebackground=self.COLORS['white'], activeforeground=self.COLORS['text_dark']
            )
            btn_siguiente.pack(side="left", padx=2, pady=2)

            separator = tk.Label(
                control_frame, text="|",
                bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                font=('Segoe UI', 12, 'bold')
            )
            separator.pack(side="left", padx=5, pady=2)

            btn_zoom_out = tk.Button(
                control_frame, text="🔍−", command=lambda: change_zoom(-0.25),
                bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                font=('Segoe UI', 9, 'bold'), relief='flat', borderwidth=0, cursor='hand2'
            )
            btn_zoom_out.pack(side="left", padx=2, pady=2)

            zoom_label = tk.Label(
                control_frame, text=f"Zoom: {int(self.zoom_level * 100)}%",
                bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                font=('Segoe UI', 9, 'bold')
            )
            zoom_label.pack(side="left", padx=2, pady=2)

            btn_zoom_in = tk.Button(
                control_frame, text="🔍+", command=lambda: change_zoom(0.25),
                bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                font=('Segoe UI', 9, 'bold'), relief='flat', borderwidth=0, cursor='hand2'
            )
            btn_zoom_in.pack(side="left", padx=2, pady=2)

            separator2 = tk.Label(
                control_frame, text="|",
                bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                font=('Segoe UI', 12, 'bold')
            )
            separator2.pack(side="left", padx=5, pady=2)

            btn_fit_width = tk.Button(
                control_frame, text="↔ Ajustar Ancho", command=fit_to_width,
                bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                font=('Segoe UI', 9, 'bold'), relief='flat', borderwidth=0, cursor='hand2'
            )
            btn_fit_width.pack(side="left", padx=2, pady=2)

            btn_fit_page = tk.Button(
                control_frame, text="⛶ Ajustar Página", command=fit_to_page,
                bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                font=('Segoe UI', 9, 'bold'), relief='flat', borderwidth=0, cursor='hand2'
            )
            btn_fit_page.pack(side="left", padx=2, pady=2)

            btn_maximizar = tk.Button(
                control_frame, text="🔳 Maximizar", command=maximizar_reporte,
                bg=self.COLORS['primary'], fg='white',
                font=('Segoe UI', 10, 'bold'), relief='flat', borderwidth=0, cursor='hand2',
                pady=4, padx=12
            )
            btn_maximizar.pack(side="left", padx=5, pady=2)

            # Inicializar estado botones
            btn_anterior.config(state="disabled")
            btn_siguiente.config(state="normal" if self.total_pages > 1 else "disabled")

            display_page()

            def on_mousewheel(event):
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            canvas.bind("<MouseWheel>", on_mousewheel)

        except Exception as e:
            import traceback
            error_detallado = traceback.format_exc()
            print(f"Error detallado:\n{error_detallado}")
            messagebox.showerror("Error", f"Error al mostrar vista previa PDF: {str(e)}")
  
    def abrir_pdf_externo(self):
        """Abre el PDF en una aplicación externa del sistema"""
        try:
            if not hasattr(self, 'temp_pdf_path') or not os.path.exists(self.temp_pdf_path):
                messagebox.showerror("Error", "No hay un PDF generado para abrir.")
                return
              
            import sys
            import subprocess
          
            if sys.platform.startswith('win'):
                os.startfile(self.temp_pdf_path)
            elif sys.platform.startswith('darwin'):  # macOS
                subprocess.run(['open', self.temp_pdf_path], check=True)
            else:  # Linux
                subprocess.run(['xdg-open', self.temp_pdf_path], check=True)
              
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el PDF: {str(e)}")
  
    def dividir_texto_en_lineas(self, texto, max_caracteres_por_linea=30):
        """Divide el texto en múltiples líneas para mejor ajuste"""
        if not texto:
            return ""
      
        texto = str(texto).strip()
        palabras = texto.split()
        lineas = []
        linea_actual = ""
      
        for palabra in palabras:
            if len(palabra) > max_caracteres_por_linea:
                if linea_actual:
                    lineas.append(linea_actual.strip())
                    linea_actual = ""
                lineas.append(palabra[:max_caracteres_por_linea-3] + "...")
                continue
              
            if len(linea_actual + " " + palabra) > max_caracteres_por_linea:
                if linea_actual:
                    lineas.append(linea_actual.strip())
                    linea_actual = palabra
                else:
                    lineas.append(palabra)
            else:
                linea_actual += " " + palabra if linea_actual else palabra
      
        if linea_actual:
            lineas.append(linea_actual.strip())
      
        # Limitar a máximo 3 líneas
        if len(lineas) > 3:
            lineas = lineas[:2] + [lineas[2][:max_caracteres_por_linea-3] + "..."]
      
        return "\n".join(lineas)
  
    def cerrar_ventana(self):
        """
        Cierra la ventana del reporte, limpia recursos y muestra la pantalla de bienvenida.
        """
        if not messagebox.askyesno("Confirmar", "¿Está seguro que desea cerrar esta ventana?"):
            return  # Si el usuario cancela, no hace nada

        try:
            # Limpiar archivo temporal si existe
            if hasattr(self, 'temp_pdf_path') and os.path.exists(self.temp_pdf_path):
                try:
                    os.remove(self.temp_pdf_path)
                except Exception:
                    pass

            # Cerrar documento PDF si está abierto
            if hasattr(self, 'pdf_document') and self.pdf_document:
                try:
                    self.pdf_document.close()
                except Exception:
                    pass

            # Desvincular el evento del mouse wheel antes de cerrar (si existe self.canvas)
            try:
                if hasattr(self, "canvas"):
                    self.canvas.unbind_all("<MouseWheel>")
            except Exception:
                pass

            # Limpiar el frame principal
            if hasattr(self, 'parent') and self.parent:
                for widget in self.parent.winfo_children():
                    widget.destroy()

            # Mostrar la pantalla de bienvenida si existe
            if hasattr(self, "main_window") and self.main_window:
                self.main_window.show_welcome_screen()

        except Exception as e:
            print(f"Error al cerrar ventana: {e}")
            # Forzar cierre si hay error
            try:
                import sys
                if hasattr(self, 'parent') and self.parent:
                    self.parent.quit()
                else:
                    sys.exit()
            except Exception:
                pass
              
        except Exception as e:
            print(f"Error al cerrar ventana: {e}")
            # En caso de error, intentar cerrar la aplicación
            try:
                self.parent.quit()
            except:
                pass
          
    def destroy(self):
        if hasattr(self, 'frame_principal'):
            self.frame_principal.destroy()