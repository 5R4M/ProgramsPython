import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import pandas as pd
from datetime import datetime, timedelta
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
    obtener_movimientos_kardex
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
            foreground=self.COLORS['white'],
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
        
        # Estilos adicionales para radiobuttons y combobox
        style.configure(
            'White.TRadiobutton',
            background=self.COLORS['white'],
            foreground=self.COLORS['text_dark'],
            font=('Segoe UI', 9)
        )
        style.configure(
            'White.TCombobox',
            fieldbackground=self.COLORS['white'],
            background=self.COLORS['white'],
            foreground=self.COLORS['text_dark']
        )
    
    def create_titled_frame(self, parent, title):
        container = tk.Frame(parent, bg=self.COLORS['white'], relief='solid', borderwidth=1)

        header = tk.Frame(container, bg=self.COLORS['primary'], height=20)
        header.pack(fill='x')
        header.pack_propagate(False)

        label = tk.Label(header, text=title, font=('Segoe UI', 8, 'bold'),
                        fg=self.COLORS['white'], bg=self.COLORS['primary'])
        label.pack(side='left', padx=10, pady=2)

        content = tk.Frame(container, bg=self.COLORS['white'])
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
        # --- Frame principal que contendrá todo ---
        main_container = tk.Frame(self.parent, bg=self.COLORS['light'])
        main_container.pack(fill="both", expand=True)

        # --- Título principal ---
        title_frame = tk.Frame(main_container, bg=self.COLORS['primary'], height=70)
        title_frame.pack(fill='x', padx=0, pady=(10, 5))
        title_frame.pack_propagate(False)

        title_inner = tk.Frame(title_frame, bg=self.COLORS['primary'])
        title_inner.pack(fill='both', expand=True, padx=15, pady=8)

        tk.Label(title_inner,
                text="Reporte Demanda Real por Servicio de Salud",
                font=('Segoe UI', 12, 'bold'),
                fg=self.COLORS['white'],
                bg=self.COLORS['primary']).pack(anchor='w')

        tk.Label(title_inner,
                text="Consulte demanda de los movimientos de los insumos",
                font=('Segoe UI', 8),
                fg=self.COLORS['white'],
                bg=self.COLORS['primary']).pack(anchor='w', pady=(2, 0))

        # Frame principal con título personalizado
        self.frame_principal_container, self.frame_principal = self.create_titled_frame(main_container, "Filtros de Reporte Demanda Real")
        self.frame_principal_container.config(bg=self.COLORS['white'])
        self.frame_principal.config(bg=self.COLORS['white'])
        self.frame_principal_container.pack(fill="both", expand=True, padx=10, pady=5)

        # Frame para corte logístico
        self.frame_corte_container, self.frame_corte_content = self.create_titled_frame(self.frame_principal, "Corte Logístico")
        self.frame_corte_container.config(bg=self.COLORS['white'])
        self.frame_corte_content.config(bg=self.COLORS['white'])
        self.frame_corte_container.pack(fill="x", expand=False, padx=0, pady=5)

        # Configurar grid EXACTAMENTE IGUAL que ubicación (solo columnas expandibles específicas)
        self.frame_corte_content.grid_columnconfigure(1, weight=1)  # Año
        self.frame_corte_content.grid_columnconfigure(3, weight=1)  # Mes Inicio  
        self.frame_corte_content.grid_columnconfigure(5, weight=1)  # Mes Final
        # NO configurar las demás columnas para que no se expandan

        # Distribuir elementos - Año, Mes Inicio, Mes Final
        ttk.Label(self.frame_corte_content, text="Año:", style='White.TLabel').grid(row=0, column=0, padx=5, sticky='w')
        self.anio_var = tk.StringVar()
        anios = [str(a) for a in range(datetime.now().year - 5, datetime.now().year + 2)]
        self.combo_anio = ttk.Combobox(
            self.frame_corte_content,
            textvariable=self.anio_var,
            values=anios,
            width=8,
            state="readonly"
        )
        self.combo_anio.grid(row=0, column=1, padx=5, sticky='ew')
        self.combo_anio.set(str(datetime.now().year))

        ttk.Label(self.frame_corte_content, text="Mes Inicio:", style='White.TLabel').grid(row=0, column=2, padx=5, sticky='w')
        self.mes_inicio_var = tk.StringVar()
        
        # Obtener nombres de meses en español
        meses = [datetime(2024, m, 1).strftime("%B").capitalize() for m in range(1, 13)]
        
        self.combo_mes_inicio = ttk.Combobox(
            self.frame_corte_content,
            textvariable=self.mes_inicio_var,
            values=meses,
            width=12,
            state="readonly"
        )
        self.combo_mes_inicio.grid(row=0, column=3, padx=5, sticky='ew')
        self.combo_mes_inicio.set(datetime.now().strftime("%B").capitalize())

        ttk.Label(self.frame_corte_content, text="Mes Final:", style='White.TLabel').grid(row=0, column=4, padx=5, sticky='w')
        self.mes_final_var = tk.StringVar()
        
        self.combo_mes_final = ttk.Combobox(
            self.frame_corte_content,
            textvariable=self.mes_final_var,
            values=meses,
            width=12,
            state="readonly"
        )
        self.combo_mes_final.grid(row=0, column=5, padx=5, sticky='ew')
        self.combo_mes_final.set(datetime.now().strftime("%B").capitalize())

        # NO agregar labels vacíos en columnas 6 y 7 para mantener el ancho correcto

        # Eventos para actualizar fechas
        self.combo_anio.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte)
        self.combo_mes_inicio.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte)
        self.combo_mes_final.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte)

        # Frame ubicación
        self.frame_ubicacion_container, self.frame_ubicacion_content = self.create_titled_frame(self.frame_principal, "Ubicación")
        self.frame_ubicacion_container.config(bg=self.COLORS['white'])
        self.frame_ubicacion_content.config(bg=self.COLORS['white'])
        self.frame_ubicacion_container.pack(fill="x", expand=False, padx=0, pady=5)

        # Configurar grid para distribución uniforme
        self.frame_ubicacion_content.grid_columnconfigure(1, weight=1)
        self.frame_ubicacion_content.grid_columnconfigure(3, weight=1)
        self.frame_ubicacion_content.grid_columnconfigure(5, weight=1)
        self.frame_ubicacion_content.grid_columnconfigure(7, weight=1)

        label_style = {'style': 'White.TLabel'}
        ttk.Label(self.frame_ubicacion_content, text="Área:", **label_style).grid(row=0, column=0, padx=5, sticky='w')
        self.area_var = tk.StringVar()
        self.combo_area = AutocompleteCombobox(self.frame_ubicacion_content, textvariable=self.area_var, state="normal", font=('Segoe UI', 9))
        self.combo_area.grid(row=0, column=1, padx=5, sticky='ew')
        
        ttk.Label(self.frame_ubicacion_content, text="Distrito:", **label_style).grid(row=0, column=2, padx=5, sticky='w')
        self.distrito_var = tk.StringVar()
        self.combo_distrito = AutocompleteCombobox(self.frame_ubicacion_content, textvariable=self.distrito_var, state="normal", font=('Segoe UI', 9))
        self.combo_distrito.grid(row=0, column=3, padx=5, sticky='ew')

        ttk.Label(self.frame_ubicacion_content, text="Tipo de Servicio:", **label_style).grid(row=0, column=4, padx=5, sticky='w')
        self.tipo_servicio_var = tk.StringVar()
        self.combo_tipo_servicio = AutocompleteCombobox(self.frame_ubicacion_content, textvariable=self.tipo_servicio_var, state="normal", font=('Segoe UI', 9))
        self.combo_tipo_servicio.grid(row=0, column=5, padx=5, sticky='ew')
        
        ttk.Label(self.frame_ubicacion_content, text="Servicio:", **label_style).grid(row=0, column=6, padx=5, sticky='w')
        self.servicio_var = tk.StringVar()
        self.combo_servicio = AutocompleteCombobox(self.frame_ubicacion_content, textvariable=self.servicio_var, state="normal", font=('Segoe UI', 9))
        self.combo_servicio.grid(row=0, column=7, padx=5, sticky='ew')

        # Frame insumo
        self.frame_insumo_container, self.frame_insumo_content = self.create_titled_frame(self.frame_principal, "Insumo")
        self.frame_insumo_container.config(bg=self.COLORS['white'])
        self.frame_insumo_content.config(bg=self.COLORS['white'])
        self.frame_insumo_container.pack(fill="x", expand=False, padx=0, pady=5)

        # Configurar grid para distribución uniforme
        self.frame_insumo_content.grid_columnconfigure(1, weight=1)
        self.frame_insumo_content.grid_columnconfigure(3, weight=1)
        self.frame_insumo_content.grid_columnconfigure(5, weight=1)

        ttk.Label(self.frame_insumo_content, text="Tipo de Insumo:", **label_style).grid(row=0, column=0, padx=5, sticky='w')
        self.tipo_insumo_var = tk.StringVar()
        self.combo_tipo_insumo = AutocompleteCombobox(self.frame_insumo_content, textvariable=self.tipo_insumo_var, state="normal", font=('Segoe UI', 9))
        self.combo_tipo_insumo.grid(row=0, column=1, padx=5, sticky='ew')
        
        ttk.Label(self.frame_insumo_content, text="Insumo:", **label_style).grid(row=0, column=2, padx=5, sticky='w')
        self.insumo_var = tk.StringVar()
        self.combo_insumo = AutocompleteCombobox(self.frame_insumo_content, textvariable=self.insumo_var, state="normal", font=('Segoe UI', 9))
        self.combo_insumo.grid(row=0, column=3, padx=5, sticky='ew')
        
        ttk.Label(self.frame_insumo_content, text="Presentación:", **label_style).grid(row=0, column=4, padx=5, sticky='w')
        self.presentacion_var = tk.StringVar()
        self.combo_presentacion = AutocompleteCombobox(self.frame_insumo_content, textvariable=self.presentacion_var, state="normal", font=('Segoe UI', 9))
        self.combo_presentacion.grid(row=0, column=5, padx=5, sticky='ew')

        # --- Frame para el visor PDF (ALTURA FIJA) ---
        self.pdf_frame = tk.Frame(self.frame_principal, bg=self.COLORS['white'], height=350)
        self.pdf_frame.pack(fill="x", padx=5, pady=5)
        self.pdf_frame.pack_propagate(False)  # Para que respete la altura fija
        self.pdf_viewer = None

        # --- Frame para botones (fuera del frame principal, pegado abajo) ---
        self.frame_botones = ttk.Frame(main_container, style='White.TFrame')
        self.frame_botones.pack(fill="x", side="bottom", pady=(20, 10))

        btn_font = ('Segoe UI', 9, 'bold')
        btn_bg = self.COLORS['white']
        btn_fg = self.COLORS['text_dark']

        # Botón Generar Vista Previa
        btn_preview = tk.Button(self.frame_botones, 
                            text="Generar Vista Previa", 
                            command=self.generar_reporte,
                            font=btn_font, bg=btn_bg, fg=btn_fg, 
                            relief='flat', borderwidth=0,
                            highlightthickness=0, padx=15, pady=6, 
                            cursor='hand2',
                            image=self.icon_preview,
                            compound='left')
        btn_preview.pack(side="left", padx=5)

        # Botón Imprimir
        btn_print = tk.Button(self.frame_botones, 
                            text="Imprimir", 
                            command=self.imprimir_pdf,
                            font=btn_font, bg=btn_bg, fg=btn_fg, 
                            relief='flat', borderwidth=0,
                            highlightthickness=0, padx=15, pady=6, 
                            cursor='hand2',
                            image=self.icon_print,
                            compound='left')
        btn_print.pack(side="left", padx=5)

        # Botón Exportar a PDF
        btn_pdf = tk.Button(self.frame_botones, 
                        text="Exportar a PDF", 
                        command=self.exportar_pdf,
                        font=btn_font, bg=btn_bg, fg=btn_fg, 
                        relief='flat', borderwidth=0,
                        highlightthickness=0, padx=15, pady=6, 
                        cursor='hand2',
                        image=self.icon_pdf,
                        compound='left')
        btn_pdf.pack(side="left", padx=5)

        # Botón Exportar a Excel
        btn_excel = tk.Button(self.frame_botones, 
                            text="Exportar a Excel", 
                            command=self.exportar_excel,
                            font=btn_font, bg=btn_bg, fg=btn_fg, 
                            relief='flat', borderwidth=0,
                            highlightthickness=0, padx=15, pady=6, 
                            cursor='hand2',
                            image=self.icon_excel,
                            compound='left')
        btn_excel.pack(side="left", padx=5)

        # Botón Cerrar
        btn_close = tk.Button(self.frame_botones, 
                            text="Cerrar", 
                            command=self.cerrar_ventana,
                            font=btn_font, bg=btn_bg, fg=btn_fg, 
                            relief='flat', borderwidth=0,
                            highlightthickness=0, padx=15, pady=6, 
                            cursor='hand2',
                            image=self.icon_close,
                            compound='left')
        btn_close.pack(side="right", padx=5)

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
    
    def procesar_datos(self, movimientos, fecha_ini, fecha_fin, dias):
        insumos = {}
        
        for mov in movimientos:
            # Usar get() con valores por defecto para evitar KeyError
            codigo = mov.get('codigo', '')
            nombre_insumo = mov.get('nombre_insumo', '')
            presentacion = mov.get('nombre_presentacion', '')
            
            insumo_key = f"{codigo}_{nombre_insumo}_{presentacion}"
            
            if insumo_key not in insumos:
                insumos[insumo_key] = {
                    'codigo': codigo,
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
                fecha_mov = datetime.strptime(fecha_str, '%Y-%m-%d')
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
        
        # **AGREGAR NUMERACIÓN SECUENCIAL**
        datos_procesados = {}
        contador = 1  # Iniciar contador en 1
        
        for insumo_key, valores in insumos.items():
            fila_datos = {
                'codigo': str(contador),  # **ASIGNAR NÚMERO SECUENCIAL**
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
            
            # **USAR EL CONTADOR COMO CLAVE PARA MANTENER EL ORDEN**
            datos_procesados[f"{contador:03d}_{insumo_key}"] = fila_datos
            contador += 1  # Incrementar contador
        
        return datos_procesados

    def exportar_excel(self):
        if not hasattr(self, 'dias') or not hasattr(self, 'datos'):
            messagebox.showerror("Error", "Primero debe generar la vista previa del reporte.")
            return

        try:
            import os
            from datetime import datetime, timedelta
            
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

            # **PROCESAR DATOS DE INSUMOS CON NUMERACIÓN SECUENCIAL Y DIVISIÓN DE TEXTO**
            for insumo_key, valores in self.datos.items():
                # **EXTRAER NÚMERO SECUENCIAL DEL INICIO DE LA CLAVE**
                if ' - ' in insumo_key:
                    partes = insumo_key.split(' - ', 1)
                    codigo = partes[0]  # Número secuencial (001, 002, etc.)
                    nombre_presentacion = partes[1]
                else:
                    # Si no hay separador, usar toda la cadena como nombre y código vacío
                    codigo = ''
                    nombre_presentacion = insumo_key

                # **APLICAR DIVISIÓN DE TEXTO AL NOMBRE DEL MEDICAMENTO**
                nombre_dividido = self.dividir_texto_en_lineas(nombre_presentacion, max_caracteres_por_linea=40)

                # Calcular totales
                total_entregado = valores.get('Total_Entregado', 0)
                total_no_entregado = valores.get('Total_No_Entregado', 0)
                demanda = valores.get('Demanda', 0)
                existencia = valores.get('Existencia', 0)
                reajuste = valores.get('Reajuste', 0)

                # FILA ENTREGADO
                # Combinar celdas verticalmente para código y nombre
                worksheet.merge_range(fila_actual, 0, fila_actual+1, 0, codigo, data_format)  # **Código secuencial**
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
            worksheet.set_column('A:A', 8)   # Código
            worksheet.set_column('B:B', 35)  # Medicamento - AUMENTÉ DE 25 A 35 PARA MÁS ESPACIO
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

            # **AJUSTAR ALTURA UNIFORME DE LAS FILAS DE DATOS - CORREGIDO**
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

        # USAR LAS FECHAS CALCULADAS DEL CORTE LOGÍSTICO
        anio = self.anio_var.get()
        mes_inicio = self.mes_inicio_var.get()
        mes_final = self.mes_final_var.get()
        fecha_ini_str, fecha_fin_str = self.calcular_rango_corte_logistico(anio, mes_inicio, mes_final)
        fecha_inicio = datetime.strptime(fecha_ini_str, '%d/%m/%Y')
        fecha_fin = datetime.strptime(fecha_fin_str, '%d/%m/%Y')

        # Generar lista de días hábiles (lunes a viernes) para columnas
        dias = []
        fecha_iter = fecha_inicio
        while fecha_iter <= fecha_fin:
            if fecha_iter.weekday() < 5:  # 0=lunes, ..., 4=viernes
                dias.append(fecha_iter.day)
            fecha_iter += timedelta(days=1)

        # Agrupar datos por insumo (codigo_original, nombre+presentacion)
        insumos = {}
        for mov in datos_movimientos:
            codigo_original = mov.get('codigo', '')
            nombre = mov.get('nombre_insumo', '')
            presentacion = mov.get('nombre_presentacion', '')
            key = (codigo_original, f"{nombre} {presentacion}".strip())
            
            if key not in insumos:
                insumos[key] = {
                    'entregado': {d:0 for d in dias},
                    'no_entregado': {d:0 for d in dias},
                    'inventario_inicial': 0,
                    'entrada_nivel_superior': 0,
                    'salida_nivel_inferior': 0,
                    'reajuste_positivo': 0,
                    'reajuste_negativo': 0
                }
            
            fecha_mov = datetime.strptime(mov['fecha'], '%Y-%m-%d')
            dia_mov = fecha_mov.day
            tipo = mov.get('tipo_movimiento', '').upper()
            cantidad = mov.get('cantidad', 0)
            
            if fecha_inicio <= fecha_mov <= fecha_fin:
                if tipo == 'ENTREGADO' and dia_mov in dias:
                    insumos[key]['entregado'][dia_mov] += cantidad
                elif tipo == 'NO ENTREGADO' and dia_mov in dias:
                    insumos[key]['no_entregado'][dia_mov] += cantidad
            
            # Procesar todos los movimientos para el cálculo de existencia (sin filtro de fecha)
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

        # Función para formatear valores (mostrar vacío si es 0)
        def formato_valor(valor):
            try:
                num = float(valor)
                return int(num) if num == int(num) else f"{num:.2f}"
            except (ValueError, TypeError):
                return "0"

        # Construir documento PDF
        doc = SimpleDocTemplate(
            ruta_pdf,
            pagesize=landscape(legal),
            topMargin=0.5*inch, bottomMargin=0.5*inch,
            leftMargin=0.5*inch, rightMargin=0.5*inch
        )
        elementos = []
        estilos = getSampleStyleSheet()

        # Estilos personalizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=estilos['Heading1'],
            alignment=1,
            spaceAfter=15,
            fontSize=12
        )
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=estilos['Heading2'],
            alignment=1,
            spaceAfter=10,
            fontSize=10
        )
        timestamp_style = ParagraphStyle(
            'TimestampStyle',
            parent=estilos['Normal'],
            alignment=1,
            spaceAfter=15,
            fontSize=9
        )

        # NUEVO: Estilo para texto de celdas con división de líneas - CENTRADO
        cell_text_style = ParagraphStyle(
            'CellTextStyle',
            parent=estilos['Normal'],
            fontSize=6,
            leading=7,  # Espaciado entre líneas
            alignment=1,  # Alineación centrada horizontalmente
            fontName='Helvetica'
        )

        # Títulos principales
        elementos.append(Paragraph(
            "DIRECCIÓN DEPARTAMENTAL DE REDES INTEGRADAS DE SERVICIOS DE SALUD DE GUATEMALA,",
            title_style))
        elementos.append(Paragraph("ÁREA NOR ORIENTE", subtitle_style))
        elementos.append(Paragraph("REGISTRO DIARIO DE CONSUMO Y DEMANDA REAL", subtitle_style))
        elementos.append(Paragraph(
            f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            timestamp_style))

        # Filtros en una sola fila horizontal
        filtros = [
            f"Área: {self.combo_area.get()}",
            f"Distrito: {self.combo_distrito.get()}",
            f"Tipo de Servicio: {self.combo_tipo_servicio.get()}",
            f"Servicio: {self.combo_servicio.get()}"
        ]

        # Crear estilo para alineación izquierda
        left_style = ParagraphStyle(
            name="LeftAlign",
            alignment=0,  # 0 = LEFT
            fontSize=9,
            fontName='Helvetica'
        )

        # Crear tabla con una sola fila y 4 columnas
        data_filtros = [[Paragraph(item, left_style) for item in filtros]]
        col_widths = [150, 150, 150, 150]

        table_filtros = Table(data_filtros, colWidths=col_widths)
        table_filtros.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey)
        ]))

        elementos.append(table_filtros)
        elementos.append(Spacer(1, 30))

        # Encabezados de la tabla
        encabezado1 = [
            'Código',
            'MEDICAMENTO',
            'DIA DEL MES',
            f'CANTIDAD DE MEDICAMENTOS Y/O PRODUCTOS A FIN'
        ] + [''] * (len(dias) - 1) + [
            'Total\nEntregado',
            'Total\nNo\nEntregado',
            'Demanda',
            'Existencia',
            'Reajuste (+) (-)'
        ]
        encabezado2 = [
            '',
            'Nombre, Concentración\ny Presentación',
            ''
        ] + [str(d) for d in dias] + ['', '', '', '', '']

        data = [encabezado1, encabezado2]

        # **AGREGAR DATOS CON NUMERACIÓN SECUENCIAL Y DIVISIÓN DE TEXTO**
        contador = 1
        for (codigo_original, nombre_pres), valores in insumos.items():
            # Calcular totales de entregado y no entregado
            total_entregado = sum(valores['entregado'].get(d, 0) for d in dias)
            total_no_entregado = sum(valores['no_entregado'].get(d, 0) for d in dias)
            
            # Calcular reajuste total (positivo - negativo)
            reajuste_total = valores['reajuste_positivo'] - valores['reajuste_negativo']
            
            # Calcular existencia según la fórmula:
            existencia = (valores['inventario_inicial'] + 
                        valores['entrada_nivel_superior'] + 
                        valores['reajuste_positivo'] - 
                        valores['salida_nivel_inferior'] - 
                        total_entregado - 
                        valores['reajuste_negativo'])

            # **APLICAR DIVISIÓN DE TEXTO AL NOMBRE DEL MEDICAMENTO**
            nombre_dividido = self.dividir_texto_en_lineas(nombre_pres, max_caracteres_por_linea=35)
            
            # Crear Paragraph para el nombre del medicamento con división de líneas
            nombre_paragraph = Paragraph(nombre_dividido, cell_text_style)

            # Fila Entregado - **USAR CONTADOR SECUENCIAL**
            fila_entregado = [
                str(contador),       # **NÚMERO SECUENCIAL EN LUGAR DEL CÓDIGO ORIGINAL**
                nombre_paragraph,    # **USAR PARAGRAPH CON TEXTO DIVIDIDO**
                'Entregado'
            ]
            for d in dias:
                valor = valores['entregado'].get(d, 0)
                fila_entregado.append(formato_valor(valor))
            
            fila_entregado += [
                formato_valor(total_entregado),                             # Total Entregado
                formato_valor(total_no_entregado),                          # Total No Entregado
                formato_valor(total_entregado + total_no_entregado),        # Demanda
                formato_valor(existencia),                                  # Existencia calculada
                formato_valor(reajuste_total)                               # Reajuste calculado
            ]

            # Fila No Entregado
            fila_no_entregado = [
                '',                  # Código (vacío, SPAN)
                '',                  # Medicamento (vacío, SPAN)
                'No Entregado'
            ]
            for d in dias:
                valor = valores['no_entregado'].get(d, 0)
                fila_no_entregado.append(formato_valor(valor))
            
            fila_no_entregado += [
                '',                  # Total Entregado (vacío, SPAN)
                '',                  # Total No Entregado (vacío, SPAN)
                '',                  # Demanda (vacío, SPAN)
                '',                  # Existencia (vacío, SPAN)
                ''                   # Reajuste (vacío, SPAN)
            ]

            data.append(fila_entregado)
            data.append(fila_no_entregado)
            contador += 1  # **INCREMENTAR CONTADOR**

        # Anchos de columna - **AUMENTAR ANCHO DE LA COLUMNA DE MEDICAMENTO**
        col_widths = [0.4*inch, 2.8*inch, 0.7*inch] + [0.25*inch] * len(dias) + [0.5*inch, 0.5*inch, 0.5*inch, 0.5*inch, 0.7*inch]

        tabla = Table(data, repeatRows=2, colWidths=col_widths)

        estilos_tabla = [
            ('SPAN', (0,0), (0,1)),  # Código encabezado
            ('SPAN', (2,0), (2,1)),  # Movimientos encabezado
            ('SPAN', (3,0), (len(dias)+2,0)),  # Días encabezado
            ('SPAN', (len(dias)+3,0), (len(dias)+3,1)),  # Total Entregado encabezado
            ('SPAN', (len(dias)+4,0), (len(dias)+4,1)),  # Total No Entregado encabezado
            ('SPAN', (len(dias)+5,0), (len(dias)+5,1)),  # Demanda encabezado
            ('SPAN', (len(dias)+6,0), (len(dias)+6,1)),  # Existencia encabezado
            ('SPAN', (len(dias)+7,0), (len(dias)+7,1)),  # Reajuste encabezado
            # Encabezados: fondo azul claro y texto negro
            ('BACKGROUND', (0,0), (-1,1), colors.lightblue),
            ('TEXTCOLOR', (0,0), (-1,1), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.25, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            # **ALINEACIÓN ESPECIAL PARA LA COLUMNA DE MEDICAMENTOS - CENTRADO**
            ('ALIGN', (1,2), (1,-1), 'CENTER'),  # Columna medicamento centrada horizontalmente
            ('VALIGN', (1,2), (1,-1), 'MIDDLE'), # Columna medicamento centrada verticalmente
        ]

        # SPAN dinámico para las celdas vacías de cada insumo
        fila_inicio = 2  # porque las dos primeras filas son encabezados
        while fila_inicio < len(data):
            fila_fin = fila_inicio + 1  # la fila de No Entregado
            estilos_tabla.append(('SPAN', (0, fila_inicio), (0, fila_fin)))  # Código
            estilos_tabla.append(('SPAN', (1, fila_inicio), (1, fila_fin)))  # Medicamento
            estilos_tabla.append(('SPAN', (len(dias)+3, fila_inicio), (len(dias)+3, fila_fin)))  # Total Entregado
            estilos_tabla.append(('SPAN', (len(dias)+4, fila_inicio), (len(dias)+4, fila_fin)))  # Total No Entregado
            estilos_tabla.append(('SPAN', (len(dias)+5, fila_inicio), (len(dias)+5, fila_fin)))  # Demanda
            estilos_tabla.append(('SPAN', (len(dias)+6, fila_inicio), (len(dias)+6, fila_fin)))  # Existencia
            estilos_tabla.append(('SPAN', (len(dias)+7, fila_inicio), (len(dias)+7, fila_fin)))  # Reajuste
            fila_inicio += 2

        tabla.setStyle(TableStyle(estilos_tabla))
        elementos.append(tabla)
        doc.build(elementos)
        
    def generar_reporte(self):
        # Validar filtros obligatorios hasta servicio
        if not all([
            self.combo_area.get(),
            self.combo_distrito.get(),
            self.combo_tipo_servicio.get(),
            self.combo_servicio.get(),
            self.combo_tipo_insumo.get()
        ]):
            messagebox.showerror("Error", "Debe seleccionar todos los filtros hasta Servicio, Insumo y Presentación")
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

        # Obtener nombres de los combos
        distrito_nombre = self.combo_distrito.get()
        tipo_servicio_desc = self.combo_tipo_servicio.get()
        servicio_nombre = self.combo_servicio.get()
        tipo_insumo_desc = self.combo_tipo_insumo.get()
        insumo_nombre = self.combo_insumo.get()
        presentacion_nombre = self.combo_presentacion.get()

        # Obtener movimientos sin filtrar tipo movimiento
        movimientos_raw = obtener_movimientos_kardex(
            fecha_ini.strftime('%Y-%m-%d'),
            fecha_fin.strftime('%Y-%m-%d'),
            distrito_nombre,
            tipo_servicio_desc,
            servicio_nombre,
            tipo_insumo_desc,
            insumo_nombre,
            presentacion_nombre
        )

        if not movimientos_raw:
            messagebox.showinfo("Info", "No hay datos para mostrar")
            return

        # Filtrar movimientos relevantes para demanda real
        movimientos_filtrados = [m for m in movimientos_raw if m.get('tipo_movimiento', '').upper() in [
            'ENTREGADO', 'NO ENTREGADO', 'REAJUSTE POSITIVO', 'REAJUSTE NEGATIVO', 'INVENTARIO INICIAL', 'ENTRADA NIVEL SUPERIOR', 'SALDO ANTERIOR'
        ]]

        # Agrupar datos por insumo
        insumos = {}
        
        for mov in movimientos_filtrados:
            codigo = mov.get('codigo', '')
            nombre = mov.get('nombre_insumo', '')
            presentacion = mov.get('nombre_presentacion', '')
            key = f"{codigo}_{nombre}_{presentacion}"
            
            if key not in insumos:
                insumos[key] = {
                    'codigo_original': codigo,
                    'nombre': nombre,
                    'presentacion': presentacion,
                    'entregado': {d:0 for d in self.dias},
                    'no_entregado': {d:0 for d in self.dias},
                    'inventario_inicial': 0,
                    'entrada_nivel_superior': 0,
                    'salida_nivel_inferior': 0,
                    'reajuste_positivo': 0,
                    'reajuste_negativo': 0
                }
            
            fecha_str = mov.get('fecha', '')
            if fecha_str:
                try:
                    fecha_mov = datetime.strptime(fecha_str, '%Y-%m-%d')
                    dia_mov = fecha_mov.day
                    tipo = mov.get('tipo_movimiento', '').upper()
                    cantidad = mov.get('cantidad', 0)
                    
                    if fecha_ini <= fecha_mov <= fecha_fin:
                        if tipo == 'ENTREGADO' and dia_mov in self.dias:
                            insumos[key]['entregado'][dia_mov] += cantidad
                        elif tipo == 'NO ENTREGADO' and dia_mov in self.dias:
                            insumos[key]['no_entregado'][dia_mov] += cantidad
                    
                    # Procesar movimientos para cálculo de existencia
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
                except ValueError:
                    continue

        # **CONVERTIR A FORMATO PARA EXCEL CON NUMERACIÓN SECUENCIAL**
        self.datos = {}
        contador = 1
        
        for insumo_key, valores in insumos.items():
            fila_datos = {}
            
            # Agregar días
            for dia in self.dias:
                fila_datos[f'Día_{dia}_Entregado'] = valores['entregado'].get(dia, 0)
                fila_datos[f'Día_{dia}_No_Entregado'] = valores['no_entregado'].get(dia, 0)
            
            # Calcular totales
            total_entregado = sum(valores['entregado'].values())
            total_no_entregado = sum(valores['no_entregado'].values())
            reajuste_total = valores['reajuste_positivo'] - valores['reajuste_negativo']
            existencia = (valores['inventario_inicial'] + 
                        valores['entrada_nivel_superior'] + 
                        valores['reajuste_positivo'] - 
                        valores['salida_nivel_inferior'] - 
                        total_entregado - 
                        valores['reajuste_negativo'])
            
            # Agregar totales
            fila_datos['Total_Entregado'] = total_entregado
            fila_datos['Total_No_Entregado'] = total_no_entregado
            fila_datos['Demanda'] = total_entregado + total_no_entregado
            fila_datos['Existencia'] = existencia
            fila_datos['Reajuste'] = reajuste_total
            
            # **USAR CONTADOR COMO CLAVE CON INFORMACIÓN DEL INSUMO**
            nombre_completo = f"{valores['nombre']} - {valores['presentacion']}"
            nueva_clave = f"{contador:03d} - {nombre_completo}"
            self.datos[nueva_clave] = fila_datos
            contador += 1

        periodo_str = f"{fecha_ini.strftime('%d%m%Y')}_{fecha_fin.strftime('%d%m%Y')}"
        self.periodo_str = periodo_str

        import tempfile
        temp_dir = tempfile.gettempdir()
        self.temp_pdf_path = os.path.join(temp_dir, f"vista_previa_demanda_real_{periodo_str}.pdf")
        self.generar_pdf(movimientos_filtrados, self.temp_pdf_path)

        self.generar_vista_previa_pdf()

    def generar_vista_previa_pdf(self):
        try:
            # --- Limpiar visor PDF ---
            for widget in self.pdf_frame.winfo_children():
                widget.destroy()

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