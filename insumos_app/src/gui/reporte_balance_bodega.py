# -*- coding: utf-8 -*-
# Reporte Balance de Bodega (estilo unificado como Reporte BRES)

from calendar import month_name
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
from ttkwidgets.autocomplete import AutocompleteCombobox

# PDF/Imágenes
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, legal
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

import fitz  # PyMuPDF
from PIL import Image, ImageTk

# Agregar el directorio raíz del proyecto al PATH de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.db_manager import (
    obtener_areas,
    obtener_tipos_insumo,
    obtener_insumos_por_tipo,
    obtener_presentaciones,
    obtener_movimientos_balance
)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # pyinstaller
    except AttributeError:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(base_path, relative_path)


class ReporteBalanceBodega:
    # Columnas informativas (para consistencia)
    COLUMNAS = [
        'Código Insumo', 'Nombre del Insumo', 'Saldo Anterior', 'Entradas Nivel Superior',
        'Salida a Nivel Inferior', 'Reajustes (+) (-)', 'Saldo Mes Siguiente'
    ]

    def __init__(self, parent_frame, main_window=None):
        self.parent = parent_frame
        self.main_window = main_window
        self.movimientos_data = None

        self.setup_styles()
        self.cargar_iconos()

        self.areas = []
        self.distritos = []
        self.tipos_insumo = []
        self.insumos = []
        self.presentaciones = []

        self.setup_ui()

    # -----------------------------
    # Estilos (igualados a BRES)
    # -----------------------------
    def setup_styles(self):
        # Paleta unificada
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

        style = ttk.Style(self.parent if hasattr(self, 'parent') else None)
        try:
            style.theme_use('clam')
        except Exception:
            pass

        # Frames base
        style.configure('White.TFrame', background=self.COLORS['light'])
        style.configure('Enabled.TFrame', background=self.COLORS['light'])
        style.configure('Disabled.TFrame', background='#f0f0f0')

        # Labels y botones base
        style.configure('White.TLabel',
                        background=self.COLORS['light'],
                        foreground=self.COLORS['text_dark'],
                        font=('Segoe UI', 9))

        style.configure('White.TButton',
                        background=self.COLORS['light'],
                        foreground=self.COLORS['text_dark'],
                        font=('Segoe UI', 9),
                        relief='flat',
                        borderwidth=0)
        style.map('White.TButton',
                  background=[('active', self.COLORS['light']),
                              ('pressed', self.COLORS['light'])])

        # Títulos de tarjetas
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

        # Botón primario
        style.configure('Primary.TButton',
                        font=('Segoe UI', 9, 'bold'),
                        padding=(12, 6),
                        relief='flat',
                        borderwidth=0,
                        background=self.COLORS['accent'],
                        foreground=self.COLORS['white'])
        style.map('Primary.TButton',
                  background=[('active', '#2980b9'), ('pressed', '#117a8b')],
                  foreground=[('active', '#ffffff'), ('pressed', '#ffffff')])

        # Cabeceras compactas
        style.configure('Header.TFrame', background=self.COLORS['primary'])
        style.configure('Header.TLabel',
                        background=self.COLORS['primary'],
                        foreground=self.COLORS['white'],
                        font=('Segoe UI', 8, 'bold'))

        # Popup Combobox y Listbox
        root = self.parent.winfo_toplevel() if hasattr(self, 'parent') else None
        if root:
            root.option_add('*TCombobox*Listbox.background', self.COLORS['white'])
            root.option_add('*TCombobox*Listbox.foreground', self.COLORS['text_dark'])
            root.option_add('*TCombobox*Listbox.selectBackground', self.COLORS['accent'])
            root.option_add('*TCombobox*Listbox.selectForeground', self.COLORS['white'])
            root.option_add('*TCombobox*Listbox.font', '{Segoe UI} 9')

            root.option_add('*Listbox.background', self.COLORS['white'])
            root.option_add('*Listbox.foreground', self.COLORS['text_dark'])
            root.option_add('*Listbox.selectBackground', self.COLORS['accent'])
            root.option_add('*Listbox.selectForeground', self.COLORS['white'])
            root.option_add('*Listbox.font', '{Segoe UI} 9')

        # Entradas y Combobox
        style.configure('TCombobox',
                        fieldbackground=self.COLORS['white'],
                        background=self.COLORS['white'],
                        foreground=self.COLORS['text_dark'])
        style.configure('TEntry',
                        selectbackground=self.COLORS['accent'],
                        selectforeground='#ffffff')

        style.configure('White.TRadiobutton',
                        background=self.COLORS['light'],
                        foreground=self.COLORS['text_dark'],
                        font=('Segoe UI', 9))

    # -----------------------------
    # Utilidad: Titled Frame con mini-ícono
    # -----------------------------
    def create_titled_frame(self, parent, title_text_with_emoji):
        container = tk.Frame(parent, bg=self.COLORS['white'], relief='solid', borderwidth=1)

        header = tk.Frame(container, bg=self.COLORS['primary'], height=26)
        header.pack(fill='x')
        header.pack_propagate(False)

        label = tk.Label(header,
                         text=title_text_with_emoji,
                         font=('Segoe UI', 9, 'bold'),
                         fg=self.COLORS['white'],
                         bg=self.COLORS['primary'])
        label.pack(side='left', padx=10, pady=2)

        content = tk.Frame(container, bg=self.COLORS['white'])
        content.pack(fill='both', expand=True, padx=10, pady=10)

        return container, content

    # -----------------------------
    # Íconos (solo para botones)
    # -----------------------------
    def cargar_iconos(self):
        try:
            icons_path = resource_path(os.path.join('utils', 'icons'))
            self.icon_preview = tk.PhotoImage(file=os.path.join(icons_path, "vista_previa.png")).subsample(2, 2)
            self.icon_print   = tk.PhotoImage(file=os.path.join(icons_path, "imprimir.png")).subsample(2, 2)
            self.icon_pdf     = tk.PhotoImage(file=os.path.join(icons_path, "pdf.png")).subsample(2, 2)
            self.icon_excel   = tk.PhotoImage(file=os.path.join(icons_path, "excel.png")).subsample(2, 2)
            self.icon_close   = tk.PhotoImage(file=os.path.join(icons_path, "cerrar.png")).subsample(2, 2)
        except Exception as e:
            print(f"Error cargando iconos: {e}")
            self.icon_preview = None
            self.icon_print = None
            self.icon_pdf = None
            self.icon_excel = None
            self.icon_close = None

    # -----------------------------
    # Formateo
    # -----------------------------
    def formato_float(self, valor):
        try:
            num = float(valor)
            return f"{num:.2f}"
        except (ValueError, TypeError):
            return "0.00"

    # -----------------------------
    # UI principal (sin frame intermedio)
    # -----------------------------
    def setup_ui(self):
        # Contenedor principal con fondo light
        self.main_container = tk.Frame(self.parent, bg=self.COLORS['light'])
        self.main_container.pack(fill="both", expand=True)

        # Título principal
        title_frame = tk.Frame(self.main_container, bg=self.COLORS['primary'], height=70)
        title_frame.pack(fill='x', padx=0, pady=(10, 5))
        title_frame.pack_propagate(False)

        title_inner = tk.Frame(title_frame, bg=self.COLORS['primary'])
        title_inner.pack(fill='both', expand=True, padx=15, pady=8)

        tk.Label(
            title_inner,
            text="📦 Reporte Balance de Bodega",
            font=('Segoe UI', 12, 'bold'),
            fg=self.COLORS['white'],
            bg=self.COLORS['primary']
        ).pack(anchor='w')

        tk.Label(
            title_inner,
            text="Balance de Bodega por Insumo",
            font=('Segoe UI', 8),
            fg=self.COLORS['white'],
            bg=self.COLORS['primary']
        ).pack(anchor='w', pady=(2, 0))

        # Sección Fechas
        self.frame_fechas_container, self.frame_fechas = self.create_titled_frame(
            self.main_container, "📅 Selección de Fechas/Corte Logístico"
        )
        self.frame_fechas_container.config(bg=self.COLORS['light'])
        self.frame_fechas.config(bg=self.COLORS['light'])
        self.frame_fechas_container.pack(fill="x", padx=5, pady=5)

        self.modo_fecha_var = tk.StringVar(value="rango")

        # Rango
        self.frame_rango = tk.Frame(self.frame_fechas, bg=self.COLORS['light'])
        self.frame_rango.pack(fill="x", padx=5, pady=2)
        for i in range(5):
            self.frame_rango.grid_columnconfigure(i, weight=1)

        ttk.Radiobutton(
            self.frame_rango,
            text="Rango de Fechas:",
            variable=self.modo_fecha_var,
            value="rango",
            command=self.actualizar_visibilidad_fechas,
            style='White.TRadiobutton'
        ).grid(row=0, column=0, padx=5, sticky='w')

        ttk.Label(self.frame_rango, text="Fecha Inicial:", style='White.TLabel').grid(row=0, column=1, padx=5, sticky='e')
        self.fecha_inicial = DateEntry(self.frame_rango, width=16, date_pattern='dd/mm/yyyy', state='normal')
        self.fecha_inicial.grid(row=0, column=2, padx=5, sticky='ew')

        ttk.Label(self.frame_rango, text="Fecha Final:", style='White.TLabel').grid(row=0, column=3, padx=5, sticky='e')
        self.fecha_final = DateEntry(self.frame_rango, width=16, date_pattern='dd/mm/yyyy', state='normal')
        self.fecha_final.grid(row=0, column=4, padx=5, sticky='ew')

        # Corte
        self.frame_corte = tk.Frame(self.frame_fechas, bg=self.COLORS['light'])
        self.frame_corte.pack(fill="x", padx=5, pady=2)
        self.frame_corte.grid_columnconfigure(2, weight=1)
        self.frame_corte.grid_columnconfigure(4, weight=1)
        self.frame_corte.grid_columnconfigure(6, weight=1)

        ttk.Radiobutton(
            self.frame_corte,
            text="Corte Logístico:",
            variable=self.modo_fecha_var,
            value="corte",
            command=self.actualizar_visibilidad_fechas,
            style='White.TRadiobutton'
        ).grid(row=0, column=0, padx=5, sticky='w')

        ttk.Label(self.frame_corte, text="Año:", style='White.TLabel').grid(row=0, column=1, padx=5, sticky='w')
        self.anio_var = tk.StringVar()
        anios = [str(a) for a in range(datetime.now().year - 5, datetime.now().year + 2)]
        self.combo_anio = ttk.Combobox(self.frame_corte, textvariable=self.anio_var, values=anios, width=8)
        self.combo_anio.grid(row=0, column=2, padx=5, sticky='ew')
        self.combo_anio.set(str(datetime.now().year))

        ttk.Label(self.frame_corte, text="Mes Inicio:", style='White.TLabel').grid(row=0, column=3, padx=5, sticky='w')
        self.mes_inicio_var = tk.StringVar()
        meses = [datetime(2024, m, 1).strftime("%B").capitalize() for m in range(1, 13)]
        self.combo_mes_inicio = ttk.Combobox(self.frame_corte, textvariable=self.mes_inicio_var, values=meses, width=12)
        self.combo_mes_inicio.grid(row=0, column=4, padx=5, sticky='ew')

        ttk.Label(self.frame_corte, text="Mes Final:", style='White.TLabel').grid(row=0, column=5, padx=5, sticky='w')
        self.mes_final_var = tk.StringVar()
        self.combo_mes_final = ttk.Combobox(self.frame_corte, textvariable=self.mes_final_var, values=meses, width=12)
        self.combo_mes_final.grid(row=0, column=6, padx=5, sticky='ew')

        self.combo_anio.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte)
        self.combo_mes_inicio.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte)
        self.combo_mes_final.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte)
        self.actualizar_visibilidad_fechas()

        # Ubicación (Área / Distrito)
        self.frame_ubicacion_container, frame_ubicacion_content = self.create_titled_frame(
            self.main_container, "📍 Ubicación"
        )
        self.frame_ubicacion_container.config(bg=self.COLORS['light'])
        frame_ubicacion_content.config(bg=self.COLORS['light'])
        self.frame_ubicacion_container.pack(fill="x", padx=5, pady=5)

        frame_ubicacion_content.grid_columnconfigure(1, weight=1)
        frame_ubicacion_content.grid_columnconfigure(3, weight=1)

        ttk.Label(frame_ubicacion_content, text="Área:", style='White.TLabel').grid(row=0, column=0, padx=5, sticky='w')
        self.area_var = tk.StringVar()
        self.combo_area = AutocompleteCombobox(frame_ubicacion_content, textvariable=self.area_var, state="normal", font=('Segoe UI', 9))
        self.combo_area.grid(row=0, column=1, padx=5, sticky='ew')

        ttk.Label(frame_ubicacion_content, text="Distrito:", style='White.TLabel').grid(row=0, column=2, padx=5, sticky='w')
        self.distrito_var = tk.StringVar()
        self.combo_distrito = AutocompleteCombobox(frame_ubicacion_content, textvariable=self.distrito_var, state="normal", font=('Segoe UI', 9))
        self.combo_distrito.grid(row=0, column=3, padx=5, sticky='ew')

        # Insumo
        self.frame_insumo_container, frame_insumo_content = self.create_titled_frame(
            self.main_container, "💊 Insumo"
        )
        self.frame_insumo_container.config(bg=self.COLORS['light'])
        frame_insumo_content.config(bg=self.COLORS['light'])
        self.frame_insumo_container.pack(fill="x", padx=5, pady=5)

        frame_insumo_content.grid_columnconfigure(1, weight=1)
        frame_insumo_content.grid_columnconfigure(3, weight=1)
        frame_insumo_content.grid_columnconfigure(5, weight=1)

        ttk.Label(frame_insumo_content, text="Tipo de Insumo:", style='White.TLabel').grid(row=0, column=0, padx=5, sticky='w')
        self.tipo_insumo_var = tk.StringVar()
        self.combo_tipo_insumo = AutocompleteCombobox(frame_insumo_content, textvariable=self.tipo_insumo_var, state="normal", font=('Segoe UI', 9))
        self.combo_tipo_insumo.grid(row=0, column=1, padx=5, sticky='ew')

        ttk.Label(frame_insumo_content, text="Insumo:", style='White.TLabel').grid(row=0, column=2, padx=5, sticky='w')
        self.insumo_var = tk.StringVar()
        self.combo_insumo = AutocompleteCombobox(frame_insumo_content, textvariable=self.insumo_var, state="normal", font=('Segoe UI', 9))
        self.combo_insumo.grid(row=0, column=3, padx=5, sticky='ew')

        ttk.Label(frame_insumo_content, text="Presentación:", style='White.TLabel').grid(row=0, column=4, padx=5, sticky='w')
        self.presentacion_var = tk.StringVar()
        self.combo_presentacion = AutocompleteCombobox(frame_insumo_content, textvariable=self.presentacion_var, state="normal", font=('Segoe UI', 9))
        self.combo_presentacion.grid(row=0, column=5, padx=5, sticky='ew')

        # Nivel Máximo
        self.frame_nivel_container, frame_nivel_content = self.create_titled_frame(
            self.main_container, "📈 Nivel Máximo"
        )
        self.frame_nivel_container.config(bg=self.COLORS['light'])
        frame_nivel_content.config(bg=self.COLORS['light'])
        self.frame_nivel_container.pack(fill="x", padx=5, pady=(10, 10))

        ttk.Label(frame_nivel_content, text="Nivel Máximo:", style='White.TLabel').grid(row=0, column=0, padx=5, sticky='w')
        self.nivel_maximo_var = tk.StringVar()
        niveles = [str(i) for i in range(1, 12 + 1)]
        self.combo_nivel_maximo = ttk.Combobox(frame_nivel_content, textvariable=self.nivel_maximo_var, values=niveles, width=10, state="readonly")
        self.combo_nivel_maximo.grid(row=0, column=1, padx=5, sticky='w')
        self.combo_nivel_maximo.set("6")

        # Visor PDF (encabezado con mini-ícono y fondo white)
        self.pdf_outer = tk.Frame(self.main_container, bg=self.COLORS['light'])
        self.pdf_outer.pack(fill="x", expand=False, padx=5, pady=5)

        self.pdf_frame = tk.Frame(self.pdf_outer, bg=self.COLORS['white'], relief="solid", bd=1, highlightthickness=0)
        self.pdf_frame.pack(fill="x")
        self.pdf_frame.configure(height=280)
        self.pdf_frame.pack_propagate(False)

        pdf_header = tk.Frame(self.pdf_frame, bg=self.COLORS['primary'], height=26)
        pdf_header.pack(fill="x")
        pdf_header.pack_propagate(False)

        tk.Label(pdf_header,
                 text="🖼️ Vista previa del PDF",
                 font=('Segoe UI', 9, 'bold'),
                 fg=self.COLORS['white'],
                 bg=self.COLORS['primary']).pack(side="left", padx=10, pady=2)

        self.pdf_body = tk.Frame(self.pdf_frame, bg=self.COLORS['white'])
        self.pdf_body.pack(fill="both", expand=False, padx=8, pady=8)

        # Botones
        self.frame_botones = ttk.Frame(self.main_container, style='White.TFrame')
        self.frame_botones.pack(fill="x", side="bottom", pady=(20, 10))

        btn_font = ('Segoe UI', 9, 'bold')
        btn_bg = self.COLORS['light']
        btn_fg = self.COLORS['text_dark']

        btn_report = tk.Button(self.frame_botones,
                               text="Generar Vista Previa",
                               command=self.generar_vista_previa,
                               font=btn_font, bg=btn_bg, fg=btn_fg,
                               relief='flat', borderwidth=0,
                               highlightthickness=0, padx=15, pady=6,
                               cursor='hand2',
                               image=self.icon_preview if self.icon_preview else "",
                               compound='left' if self.icon_preview else None)
        btn_report.pack(side="left", padx=5)

        btn_print = tk.Button(self.frame_botones,
                              text="Imprimir",
                              command=self.imprimir_pdf,
                              font=btn_font, bg=btn_bg, fg=btn_fg,
                              relief='flat', borderwidth=0,
                              highlightthickness=0, padx=15, pady=6,
                              cursor='hand2',
                              image=self.icon_print if self.icon_print else "",
                              compound='left' if self.icon_print else None)
        btn_print.pack(side="left", padx=5)

        btn_pdf = tk.Button(self.frame_botones,
                            text="Exportar a PDF",
                            command=self.exportar_pdf,
                            font=btn_font, bg=btn_bg, fg=btn_fg,
                            relief='flat', borderwidth=0,
                            highlightthickness=0, padx=15, pady=6,
                            cursor='hand2',
                            image=self.icon_pdf if self.icon_pdf else "",
                            compound='left' if self.icon_pdf else None)
        btn_pdf.pack(side="left", padx=5)

        btn_excel = tk.Button(self.frame_botones,
                              text="Exportar a Excel",
                              command=self.generar_excel_reporte,
                              font=btn_font, bg=btn_bg, fg=btn_fg,
                              relief='flat', borderwidth=0,
                              highlightthickness=0, padx=15, pady=6,
                              cursor='hand2',
                              image=self.icon_excel if self.icon_excel else "",
                              compound='left' if self.icon_excel else None)
        btn_excel.pack(side="left", padx=5)

        btn_close = tk.Button(self.frame_botones,
                              text="Cerrar",
                              command=self.cerrar_ventana,
                              font=btn_font, bg=btn_bg, fg=btn_fg,
                              relief='flat', borderwidth=0,
                              highlightthickness=0, padx=15, pady=6,
                              cursor='hand2',
                              image=self.icon_close if self.icon_close else "",
                              compound='left' if self.icon_close else None)
        btn_close.pack(side="right", padx=5)

        # Vincular eventos de cambio
        self.combo_area.bind('<<ComboboxSelected>>', self.cargar_distritos_por_area)
        self.combo_tipo_insumo.bind('<<ComboboxSelected>>', self.cargar_insumos)
        self.combo_insumo.bind('<<ComboboxSelected>>', self.actualizar_presentacion)

        # Cargar datos iniciales
        self.cargar_areas()
        self.distritos = []
        self.combo_distrito.set_completion_list([''])
        self.cargar_tipos_insumo()
        self.cargar_presentaciones()

    # -----------------------------
    # Visibilidad Fechas
    # -----------------------------
    def actualizar_visibilidad_fechas(self, event=None):
        modo = self.modo_fecha_var.get()
        if modo == "rango":
            self.fecha_inicial.config(state="normal")
            self.fecha_final.config(state="normal")
            self.combo_anio.config(state="disabled")
            self.combo_mes_inicio.config(state="disabled")
            self.combo_mes_final.config(state="disabled")
        else:
            self.fecha_inicial.config(state="disabled")
            self.fecha_final.config(state="disabled")
            self.combo_anio.config(state="readonly")
            self.combo_mes_inicio.config(state="readonly")
            self.combo_mes_final.config(state="readonly")
        self.frame_fechas.update()

    def calcular_rango_corte_logistico(self, anio, mes_inicio, mes_final):
        meses_a_numero = {
            'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4,
            'Mayo': 5, 'Junio': 6, 'Julio': 7, 'Agosto': 8,
            'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12
        }
        m_ini = meses_a_numero.get(mes_inicio)
        m_fin = meses_a_numero.get(mes_final)
        if not (m_ini and m_fin):
            raise ValueError("Mes inicio y mes final deben ser válidos")
        try:
            anio = int(anio)
        except ValueError:
            raise ValueError("Año debe ser un número válido")

        if m_ini == 1:
            fecha_ini = datetime(anio - 1, 12, 26)
        else:
            fecha_ini = datetime(anio, m_ini - 1, 26)
        fecha_fin = datetime(anio, m_fin, 25)
        return fecha_ini.strftime('%d/%m/%Y'), fecha_fin.strftime('%d/%m/%Y')

    def actualizar_fechas_por_corte(self, event=None):
        try:
            anio = self.anio_var.get()
            mes_inicio = self.mes_inicio_var.get()
            mes_final = self.mes_final_var.get()
            if anio and mes_inicio and mes_final:
                fecha_ini, fecha_fin = self.calcular_rango_corte_logistico(anio, mes_inicio, mes_final)
                self.fecha_inicial.set_date(datetime.strptime(fecha_ini, '%d/%m/%Y'))
                self.fecha_final.set_date(datetime.strptime(fecha_fin, '%d/%m/%Y'))
        except Exception as e:
            messagebox.showerror("Error", f"Error al calcular fechas: {str(e)}")

    # -----------------------------
    # Carga de datos (áreas/insumos)
    # -----------------------------
    def cargar_areas(self):
        self.areas = obtener_areas()
        if self.areas:
            opciones = [''] + [a['nombre'] for a in self.areas]
            self.combo_area.set_completion_list(opciones)

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
                self.combo_presentacion.set(insumo.get('nombre_presentacion', ''))
            else:
                self.combo_presentacion.set('')
        else:
            self.combo_presentacion.set('')

    def cargar_presentaciones(self):
        self.presentaciones = obtener_presentaciones()
        if self.presentaciones:
            opciones = [''] + [p['nombre'] for p in self.presentaciones]
            self.combo_presentacion.set_completion_list(opciones)

    # -----------------------------
    # Códigos de insumo (misma lógica, limpieza menor)
    # -----------------------------
    def generar_codigo_insumo(self, movimientos_raw):
        from src.database.db_manager import conectar_db

        codigos_insumos = {}
        insumos_unicos = {}

        for mov in movimientos_raw:
            insumo_id = mov.get('codigo_insumo')
            insumo_nombre = mov.get('nombre_insumo', '')
            if insumo_id is not None and str(insumo_id).strip():
                if insumo_id not in insumos_unicos:
                    insumos_unicos[insumo_id] = insumo_nombre

        if not insumos_unicos:
            return {}

        try:
            conn = conectar_db()
            if not conn:
                return {}

            cursor = conn.cursor(dictionary=True)
            insumos_por_tipo = {}

            # Para cada insumo obtener su tipo
            for insumo_id, _ in insumos_unicos.items():
                query = """
                    SELECT ti.id as tipo_id, ti.descripcion as tipo_insumo_descripcion
                    FROM insumo i
                    INNER JOIN tipo_insumo ti ON i.id_tipo_insumo = ti.id
                    WHERE i.id = %s
                """
                cursor.execute(query, (insumo_id,))
                resultado = cursor.fetchone()

                if resultado:
                    tipo_id = resultado['tipo_id']
                    tipo_insumo = resultado['tipo_insumo_descripcion'].strip().upper()
                    insumos_por_tipo.setdefault(tipo_id, {
                        'descripcion': tipo_insumo,
                        'insumos_reporte': []
                    })
                    insumos_por_tipo[tipo_id]['insumos_reporte'].append(insumo_id)
                else:
                    tipo_id_default = -1
                    insumos_por_tipo.setdefault(tipo_id_default, {
                        'descripcion': "GENERAL",
                        'insumos_reporte': []
                    })
                    insumos_por_tipo[tipo_id_default]['insumos_reporte'].append(insumo_id)

            # Para cada tipo, obtener todos los insumos para posición relativa
            for tipo_id, info_tipo in insumos_por_tipo.items():
                tipo_descripcion = info_tipo['descripcion']
                insumos_del_reporte = info_tipo['insumos_reporte']

                tipo_limpio = ''.join(c for c in tipo_descripcion if c.isalnum())
                prefijo = (tipo_limpio[:4] if len(tipo_limpio) >= 4 else (tipo_limpio + 'XXXX')[:4]).upper()

                if tipo_id == -1:
                    # Secuencial simple
                    for contador, insumo_id in enumerate(sorted(insumos_del_reporte), 1):
                        codigos_insumos[insumo_id] = f"{prefijo}-{contador:04d}"
                else:
                    query_todos_tipo = """
                        SELECT i.id as insumo_id
                        FROM insumo i
                        WHERE i.id_tipo_insumo = %s
                        ORDER BY i.id ASC
                    """
                    cursor.execute(query_todos_tipo, (tipo_id,))
                    todos_insumos_tipo = cursor.fetchall()
                    posicion_relativa = {ins['insumo_id']: idx for idx, ins in enumerate(todos_insumos_tipo, 1)}

                    for insumo_id in insumos_del_reporte:
                        if insumo_id in posicion_relativa:
                            pos = posicion_relativa[insumo_id]
                            codigos_insumos[insumo_id] = f"{prefijo}-{pos:04d}"

            conn.close()
            return codigos_insumos

        except Exception as e:
            print(f"DEBUG: Error obteniendo tipos de insumo: {e}")
            import traceback
            traceback.print_exc()
            return {}

    # -----------------------------
    # Procesamiento de datos
    # -----------------------------
    def procesar_datos_balance(self, movimientos_raw, fecha_ini, fecha_fin):
        codigos_insumos = self.generar_codigo_insumo(movimientos_raw)

        # Fallback si no hay códigos
        if not codigos_insumos:
            for mov in movimientos_raw:
                insumo_id = mov.get('codigo_insumo')
                if insumo_id and insumo_id not in codigos_insumos:
                    codigos_insumos[insumo_id] = f"TEMP-{str(insumo_id).zfill(4)}"

        insumos_dict = {}

        for mov in movimientos_raw:
            insumo_id = mov.get('codigo_insumo')
            codigo_generado = codigos_insumos.get(insumo_id) or f"TEMP-{str(insumo_id).zfill(4)}"
            nombre_insumo = mov.get('nombre_insumo', '')
            tipo_movimiento = str(mov.get('tipo_movimiento', '')).upper()

            try:
                cantidad = float(mov.get('cantidad', 0))
            except:
                cantidad = 0.0

            if codigo_generado not in insumos_dict:
                insumos_dict[codigo_generado] = {
                    'codigo_insumo': codigo_generado,
                    'nombre_insumo': nombre_insumo,
                    'insumo_id_original': insumo_id,
                    'saldo_anterior': 0.0,
                    'entrada_nivel_superior': 0.0,
                    'salida_nivel_inferior': 0.0,
                    'reajuste_positivo': 0.0,
                    'reajuste_negativo': 0.0,
                }

            if tipo_movimiento == 'INVENTARIO INICIAL':
                insumos_dict[codigo_generado]['saldo_anterior'] += cantidad
            elif tipo_movimiento == 'ENTRADA NIVEL SUPERIOR':
                insumos_dict[codigo_generado]['entrada_nivel_superior'] += cantidad
            elif tipo_movimiento == 'SALIDA NIVEL INFERIOR':
                insumos_dict[codigo_generado]['salida_nivel_inferior'] += cantidad
            elif tipo_movimiento == 'REAJUSTE POSITIVO':
                insumos_dict[codigo_generado]['reajuste_positivo'] += cantidad
            elif tipo_movimiento == 'REAJUSTE NEGATIVO':
                insumos_dict[codigo_generado]['reajuste_negativo'] += cantidad

        # Saldo anterior si no hubo inventario inicial
        for codigo, datos in insumos_dict.items():
            if datos['saldo_anterior'] == 0:
                saldo_anterior = self.obtener_saldo_mes_anterior(datos['insumo_id_original'], fecha_ini)
                datos['saldo_anterior'] = saldo_anterior

        datos_procesados = []
        for codigo, datos in insumos_dict.items():
            reajustes_netos = datos['reajuste_positivo'] - datos['reajuste_negativo']
            saldo_mes_siguiente = (
                datos['saldo_anterior'] +
                datos['entrada_nivel_superior'] -
                datos['salida_nivel_inferior'] +
                reajustes_netos
            )
            datos_procesados.append({
                'codigo_insumo': codigo,
                'nombre_insumo': datos['nombre_insumo'],
                'saldo_anterior': self.formato_float(datos['saldo_anterior']),
                'entrada_nivel_superior': self.formato_float(datos['entrada_nivel_superior']),
                'salida_nivel_inferior': self.formato_float(datos['salida_nivel_inferior']),
                'reajustes': f"+{self.formato_float(datos['reajuste_positivo'])} -{self.formato_float(datos['reajuste_negativo'])}" if (datos['reajuste_positivo'] > 0 or datos['reajuste_negativo'] > 0) else "0.00",
                'saldo_mes_siguiente': self.formato_float(saldo_mes_siguiente)
            })

        return datos_procesados

    def obtener_saldo_mes_anterior(self, insumo_id_original, fecha_corte):
        try:
            # 90 días atrás para tener datos
            fecha_mes_anterior = fecha_corte - timedelta(days=90)
            movimientos = obtener_movimientos_balance(
                fecha_mes_anterior.strftime('%Y-%m-%d'),
                (fecha_corte - timedelta(days=1)).strftime('%Y-%m-%d'),
                self.combo_distrito.get().strip() or None,
                None,
                None
            )
            movimientos_insumo = [m for m in movimientos if m.get('codigo_insumo') == insumo_id_original]

            saldo = 0.0
            for mov in movimientos_insumo:
                tipo = str(mov.get('tipo_movimiento', '')).upper()
                cantidad = float(mov.get('cantidad', 0))
                if tipo in ['INVENTARIO INICIAL', 'ENTRADA NIVEL SUPERIOR', 'REAJUSTE POSITIVO']:
                    saldo += cantidad
                elif tipo in ['ENTREGADO', 'SALIDA NIVEL INFERIOR', 'REAJUSTE NEGATIVO']:
                    saldo -= cantidad
            return saldo
        except Exception as e:
            print(f"Error obteniendo saldo mes anterior: {e}")
            return 0.0

    # -----------------------------
    # Generar Vista Previa (visor unificado)
    # -----------------------------
    def generar_vista_previa(self):
        try:
            # Fechas
            if self.modo_fecha_var.get() == "rango":
                fecha_ini = datetime.strptime(self.fecha_inicial.get(), '%d/%m/%Y')
                fecha_fin = datetime.strptime(self.fecha_final.get(), '%d/%m/%Y')
            else:
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

            # Datos
            movimientos_raw = obtener_movimientos_balance(
                fecha_ini.strftime('%Y-%m-%d'),
                fecha_fin.strftime('%Y-%m-%d'),
                area_nombre=self.combo_area.get().strip() or None,
                distrito_nombre=self.combo_distrito.get().strip() or None,
                tipo_insumo_desc=self.combo_tipo_insumo.get().strip() or None,
                insumo_nombre=self.combo_insumo.get().strip() or None,
                presentacion_nombre=self.combo_presentacion.get().strip() or None
            )

            if not movimientos_raw:
                messagebox.showinfo("Info", "No hay datos para mostrar")
                return

            self.movimientos_data = self.procesar_datos_balance(movimientos_raw, fecha_ini, fecha_fin)
            if not self.movimientos_data:
                messagebox.showwarning("Sin datos", "No hay datos procesados para mostrar")
                return

            # PDF temporal
            import tempfile
            temp_dir = tempfile.gettempdir()
            self.temp_pdf_path = os.path.join(temp_dir, "vista_previa_balance.pdf")
            self.generar_pdf(self.temp_pdf_path, es_vista_previa=True)

            # Limpiar visor
            for w in self.pdf_body.winfo_children():
                w.destroy()

            # Visor
            contenedor = tk.Frame(self.pdf_body, bg=self.COLORS['white'])
            contenedor.pack(fill="both", expand=True)

            control_frame = tk.Frame(contenedor, bg=self.COLORS['white'])
            control_frame.pack(fill="x", side="bottom", pady=5)

            canvas_frame = tk.Frame(contenedor, bg=self.COLORS['white'])
            canvas_frame.pack(side="top", fill="both", expand=True)

            v_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical")
            v_scrollbar.pack(side="right", fill="y")
            h_scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal")
            h_scrollbar.pack(side="bottom", fill="x")

            canvas = tk.Canvas(canvas_frame, bg=self.COLORS['white'],
                               yscrollcommand=v_scrollbar.set,
                               xscrollcommand=h_scrollbar.set,
                               highlightthickness=0)
            canvas.pack(side="left", fill="both", expand=True)
            v_scrollbar.config(command=canvas.yview)
            h_scrollbar.config(command=canvas.xview)

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
                cw = canvas.winfo_width()
                ch = canvas.winfo_height()
                x = max((cw - pix.width) // 2, 0)
                y = max((ch - pix.height) // 2, 0)
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

            def fit_to_width():
                try:
                    cw = canvas.winfo_width()
                    if cw > 100:
                        page = doc.load_page(self.current_page)
                        zoom = (cw - 20) / page.rect.width
                        self.zoom_level = max(0.5, min(zoom, 3.0))
                        display_page()
                except Exception as e:
                    print(f"Error en fit_to_width: {e}")

            def fit_to_page():
                try:
                    cw = canvas.winfo_width()
                    ch = canvas.winfo_height()
                    if cw > 100 and ch > 100:
                        page = doc.load_page(self.current_page)
                        zoom_x = (cw - 20) / page.rect.width
                        zoom_y = (ch - 20) / page.rect.height
                        zoom = min(zoom_x, zoom_y)
                        self.zoom_level = max(0.5, min(zoom, 3.0))
                        display_page()
                except Exception as e:
                    print(f"Error en fit_to_page: {e}")

            def maximizar_reporte():
                try:
                    ventana_max = tk.Toplevel(self.parent)
                    ventana_max.title("Reporte Balance de Bodega - Vista Maximizada")
                    ventana_max.configure(bg=self.COLORS['white'])
                    ventana_max.state('zoomed')
                    ventana_max.resizable(True, True)

                    main_frame = tk.Frame(ventana_max, bg=self.COLORS['white'])
                    main_frame.pack(fill="both", expand=True)

                    control_top_frame = tk.Frame(main_frame, bg=self.COLORS['white'])
                    control_top_frame.pack(fill="x", pady=5)

                    btn_cerrar_max = tk.Button(control_top_frame, text="✕ Cerrar Vista Maximizada",
                                               command=ventana_max.destroy,
                                               bg=self.COLORS['danger'], fg='white',
                                               font=('Segoe UI', 10, 'bold'), relief='flat', borderwidth=0, cursor='hand2',
                                               pady=8, padx=15)
                    btn_cerrar_max.pack(side="right", padx=10)

                    btn_abrir_externo = tk.Button(control_top_frame, text="📄 Abrir en App Externa",
                                                  command=self.abrir_pdf_externo,
                                                  bg=self.COLORS['primary'], fg='white',
                                                  font=('Segoe UI', 10, 'bold'), relief='flat', borderwidth=0, cursor='hand2',
                                                  pady=8, padx=15)
                    btn_abrir_externo.pack(side="right", padx=5)

                    canvas_max_frame = tk.Frame(main_frame, bg=self.COLORS['white'])
                    canvas_max_frame.pack(side="top", fill="both", expand=True, padx=5)

                    h_scroll_max = ttk.Scrollbar(canvas_max_frame, orient="horizontal")
                    h_scroll_max.pack(side="bottom", fill="x")
                    v_scroll_max = ttk.Scrollbar(canvas_max_frame, orient="vertical")
                    v_scroll_max.pack(side="right", fill="y")

                    canvas_max = tk.Canvas(canvas_max_frame, xscrollcommand=h_scroll_max.set, yscrollcommand=v_scroll_max.set,
                                           bg=self.COLORS['white'], highlightthickness=0)
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
                        cw = canvas_max.winfo_width()
                        ch = canvas_max.winfo_height()
                        x = max((cw - pix.width) // 2, 0)
                        y = max((ch - pix.height) // 2, 0)
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
                            cw = canvas_max.winfo_width()
                            ch = canvas_max.winfo_height()
                            if cw > 100 and ch > 100:
                                page = doc.load_page(current_page_max[0])
                                zoom_x = (cw - 20) / page.rect.width
                                zoom_y = (ch - 20) / page.rect.height
                                zoom = min(zoom_x, zoom_y)
                                zoom_level_max[0] = max(0.5, min(zoom, 4.0))
                                display_page_max()
                                zoom_label_max.config(text=f"Zoom: {int(zoom_level_max[0] * 100)}%")
                        except Exception as e:
                            print(f"Error en fit_to_page_max: {e}")

                    btn_prev_max = tk.Button(control_max_frame, text="◀◀ Anterior", command=lambda: change_page_max(-1),
                                             bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                                             font=('Segoe UI', 11, 'bold'), relief='flat', borderwidth=1, cursor='hand2',
                                             pady=5, padx=15)
                    btn_prev_max.pack(side="left", padx=5)

                    page_label_max = tk.Label(control_max_frame, text=f"Página 1 de {self.total_pages}",
                                              bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                                              font=('Segoe UI', 11, 'bold'))
                    page_label_max.pack(side="left", padx=10)

                    btn_next_max = tk.Button(control_max_frame, text="Siguiente ▶▶", command=lambda: change_page_max(1),
                                             bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                                             font=('Segoe UI', 11, 'bold'), relief='flat', borderwidth=1, cursor='hand2',
                                             pady=5, padx=15)
                    btn_next_max.pack(side="left", padx=5)

                    btn_zoom_out_max = tk.Button(control_max_frame, text="🔍− Alejar", command=lambda: change_zoom_max(-0.25),
                                                 bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                                                 font=('Segoe UI', 10, 'bold'), relief='flat', borderwidth=1, cursor='hand2',
                                                 pady=5, padx=10)
                    btn_zoom_out_max.pack(side="left", padx=5)

                    zoom_label_max = tk.Label(control_max_frame, text=f"Zoom: {int(zoom_level_max[0] * 100)}%",
                                              bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                                              font=('Segoe UI', 10, 'bold'))
                    zoom_label_max.pack(side="left", padx=5)

                    btn_zoom_in_max = tk.Button(control_max_frame, text="🔍+ Acercar", command=lambda: change_zoom_max(0.25),
                                                bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                                                font=('Segoe UI', 10, 'bold'), relief='flat', borderwidth=1, cursor='hand2',
                                                pady=5, padx=10)
                    btn_zoom_in_max.pack(side="left", padx=5)

                    ventana_max.bind("<Configure>", lambda e: fit_to_page_max())
                    display_page_max()

                    canvas_max.bind("<MouseWheel>", lambda e: canvas_max.yview_scroll(int(-1*(e.delta/120)), "units"))

                    ventana_max.focus_force()
                    ventana_max.grab_set()

                except Exception as e:
                    messagebox.showerror("Error", f"Error al maximizar reporte: {str(e)}")

            # Controles normales
            btn_anterior = tk.Button(control_frame, text="◀", command=lambda: change_page(-1),
                                     bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                                     font=('Segoe UI', 10, 'bold'), relief='flat', borderwidth=0, cursor='hand2',
                                     activebackground=self.COLORS['white'], activeforeground=self.COLORS['text_dark'])
            btn_anterior.pack(side="left", padx=(10, 2), pady=2)

            page_label = tk.Label(control_frame, text=f"Página 1 de {self.total_pages}",
                                  bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                                  font=('Segoe UI', 10, 'bold'))
            page_label.pack(side="left", padx=2, pady=2)

            btn_siguiente = tk.Button(control_frame, text="▶", command=lambda: change_page(1),
                                      bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                                      font=('Segoe UI', 10, 'bold'), relief='flat', borderwidth=0, cursor='hand2',
                                      activebackground=self.COLORS['white'], activeforeground=self.COLORS['text_dark'])
            btn_siguiente.pack(side="left", padx=2, pady=2)

            separator = tk.Label(control_frame, text="|",
                                 bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                                 font=('Segoe UI', 12, 'bold'))
            separator.pack(side="left", padx=5, pady=2)

            btn_zoom_out = tk.Button(control_frame, text="🔍−", command=lambda: change_zoom(-0.25),
                                     bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                                     font=('Segoe UI', 9, 'bold'), relief='flat', borderwidth=0, cursor='hand2')
            btn_zoom_out.pack(side="left", padx=2, pady=2)

            zoom_label = tk.Label(control_frame, text=f"Zoom: {int(self.zoom_level * 100)}%",
                                  bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                                  font=('Segoe UI', 9, 'bold'))
            zoom_label.pack(side="left", padx=2, pady=2)

            btn_zoom_in = tk.Button(control_frame, text="🔍+", command=lambda: change_zoom(0.25),
                                    bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                                    font=('Segoe UI', 9, 'bold'), relief='flat', borderwidth=0, cursor='hand2')
            btn_zoom_in.pack(side="left", padx=2, pady=2)

            separator2 = tk.Label(control_frame, text="|",
                                  bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                                  font=('Segoe UI', 12, 'bold'))
            separator2.pack(side="left", padx=5, pady=2)

            btn_fit_width = tk.Button(control_frame, text="↔ Ajustar Ancho", command=fit_to_width,
                                      bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                                      font=('Segoe UI', 9, 'bold'), relief='flat', borderwidth=0, cursor='hand2')
            btn_fit_width.pack(side="left", padx=2, pady=2)

            btn_fit_page = tk.Button(control_frame, text="⛶ Ajustar Página", command=fit_to_page,
                                     bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                                     font=('Segoe UI', 9, 'bold'), relief='flat', borderwidth=0, cursor='hand2')
            btn_fit_page.pack(side="left", padx=2, pady=2)

            btn_maximizar = tk.Button(control_frame, text="🔳 Maximizar", command=maximizar_reporte,
                                      bg=self.COLORS['primary'], fg='white',
                                      font=('Segoe UI', 10, 'bold'), relief='flat', borderwidth=0, cursor='hand2',
                                      pady=4, padx=12)
            btn_maximizar.pack(side="left", padx=5, pady=2)

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
            messagebox.showerror("Error", f"Error al generar reporte:\n{str(e)}")

    # -----------------------------
    # Abrir/Imprimir/Exportar
    # -----------------------------
    def abrir_pdf_externo(self):
        try:
            if not hasattr(self, 'temp_pdf_path') or not os.path.exists(self.temp_pdf_path):
                messagebox.showerror("Error", "No hay un PDF generado para abrir.")
                return
            import subprocess
            if sys.platform.startswith('win'):
                os.startfile(self.temp_pdf_path)
            elif sys.platform.startswith('darwin'):
                subprocess.run(['open', self.temp_pdf_path], check=True)
            else:
                subprocess.run(['xdg-open', self.temp_pdf_path], check=True)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el PDF: {str(e)}")

    def imprimir_pdf(self):
        try:
            if not hasattr(self, 'temp_pdf_path') or not os.path.exists(self.temp_pdf_path):
                messagebox.showerror("Error", "Primero debe generar el reporte.")
                return
            if sys.platform.startswith('win'):
                os.startfile(self.temp_pdf_path)
            elif sys.platform.startswith('darwin'):
                os.system(f'open "{self.temp_pdf_path}"')
            else:
                os.system(f'xdg-open "{self.temp_pdf_path}"')
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el PDF: {str(e)}")

    def exportar_pdf(self):
        try:
            if not self.movimientos_data:
                messagebox.showerror("Error", "Primero debe generar el reporte")
                return
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"Reporte_BRES_{timestamp}.pdf"
            downloads_path = os.path.expanduser("~/Downloads")
            full_path = os.path.join(downloads_path, file_name)
            self.generar_pdf(full_path, es_vista_previa=False)
            if messagebox.askyesno("PDF Generado", "PDF guardado exitosamente.\n¿Desea abrirlo ahora?"):
                try:
                    if sys.platform.startswith('win'):
                        os.startfile(full_path)
                    elif sys.platform.startswith('darwin'):
                        os.system(f'open "{full_path}"')
                    else:
                        os.system(f'xdg-open "{full_path}"')
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo abrir el PDF: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar PDF: {str(e)}")

    # -----------------------------
    # Generación PDF
    # -----------------------------
    def generar_pdf(self, ruta_pdf, es_vista_previa=False):
        if not self.movimientos_data:
            messagebox.showwarning("Advertencia", "No hay datos para mostrar")
            return
        try:
            doc = SimpleDocTemplate(
                ruta_pdf,
                pagesize=landscape(legal),
                rightMargin=36,
                leftMargin=36,
                topMargin=36,
                bottomMargin=36
            )

            elements = []
            styles = getSampleStyleSheet()

            title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], alignment=1, spaceAfter=10, fontSize=12)
            subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Heading2'], alignment=1, spaceAfter=8, fontSize=10)
            timestamp_style = ParagraphStyle('TimestampStyle', parent=styles['Normal'], alignment=1, spaceAfter=12, fontSize=9)

            elements.append(Paragraph("DIRECCIÓN DEPARTAMENTAL DE REDES INTEGRADAS DE SERVICIOS DE SALUD DE GUATEMALA,", title_style))
            elements.append(Paragraph("ÁREA NOR ORIENTE", subtitle_style))
            elements.append(Paragraph("BALANCE DE BODEGA", subtitle_style))
            elements.append(Paragraph(f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", timestamp_style))

            # Filtros (alineados a la izquierda)
            left_style = ParagraphStyle(name="LeftAlign", alignment=0, fontSize=9, fontName='Helvetica')
            filtros = [
                f"Área: {self.combo_area.get()}",
                f"Distrito: {self.combo_distrito.get()}",
                f"Tipo de Insumo: {self.combo_tipo_insumo.get()}",
                f"Nivel Máximo: {self.combo_nivel_maximo.get()}"
            ]
            data_filtros = [[Paragraph(item, left_style) for item in filtros]]
            # 6 columnas por consistencia visual
            col_widths = [125, 125, 125, 125, 125, 125]
            table_filtros = Table(data_filtros, colWidths=col_widths[:len(filtros)])
            table_filtros.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey)
            ]))
            elements.append(table_filtros)
            elements.append(Spacer(1, 24))

            headers = [
                'Código',
                'Descripción\ndel Insumo',
                'Saldo\nAnterior',
                'Entradas\nNivel\nSuperior',
                'Salida\nNivel\nInferior',
                'Reajustes\n(+) (-)',
                'Saldo Mes\nSiguiente'
            ]

            data = [headers]
            for mov in self.movimientos_data:
                row = [
                    mov.get('codigo_insumo', ''),
                    self.dividir_texto_en_lineas(mov.get('nombre_insumo', ''), 30),
                    mov.get('saldo_anterior', ''),
                    mov.get('entrada_nivel_superior', ''),
                    mov.get('salida_nivel_inferior', ''),
                    mov.get('reajustes', ''),
                    mov.get('saldo_mes_siguiente', '')
                ]
                data.append(row)

            colWidths = [
                0.7*inch,  # Código
                3.0*inch,  # Descripción
                1.0*inch,  # Saldo Anterior
                1.0*inch,  # Entradas NS
                1.0*inch,  # Salida NI
                1.2*inch,  # Reajustes
                1.0*inch   # Saldo Siguiente
            ]

            table = Table(data, colWidths=colWidths, repeatRows=1)
            table_style = [
                ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
                ('TEXTCOLOR', (0,0), (-1,0), colors.black),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 7),
                ('FONTSIZE', (0,1), (-1,-1), 7),
                ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
                ('TOPPADDING', (0,0), (-1,0), 8),
                ('BOTTOMPADDING', (0,0), (-1,0), 8),
                ('TOPPADDING', (0,1), (-1,-1), 6),
                ('BOTTOMPADDING', (0,1), (-1,-1), 6),
                ('LEFTPADDING', (0,0), (-1,-1), 4),
                ('RIGHTPADDING', (0,0), (-1,-1), 4),
                ('WORDWRAP', (0,0), (-1,-1), True),
            ]
            table.setStyle(TableStyle(table_style))
            elements.append(table)

            doc.build(elements)

            if not es_vista_previa:
                messagebox.showinfo("Éxito", f"PDF guardado en:\n{ruta_pdf}")

        except Exception as e:
            messagebox.showerror("Error", f"Error al generar PDF: {str(e)}")

    # -----------------------------
    # Excel
    # -----------------------------
    def generar_excel_reporte(self):
        try:
            if not self.movimientos_data:
                messagebox.showerror("Error", "Primero debe generar el reporte")
                return

            filas_por_hoja = 1000
            total_movimientos = len(self.movimientos_data)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"Reporte_BRES_{timestamp}.xlsx"
            downloads_path = os.path.expanduser("~/Downloads")
            full_path = os.path.join(downloads_path, file_name)

            with pd.ExcelWriter(full_path, engine='xlsxwriter') as writer:
                workbook = writer.book

                columnas = [
                    'codigo_insumo', 'nombre_insumo', 'saldo_anterior', 'entrada_nivel_superior',
                    'salida_nivel_inferior', 'reajustes', 'saldo_mes_siguiente'
                ]
                encabezados = [
                    'Código', 'Descripción\ndel Insumo', 'Saldo\nAnterior', 'Entradas\nNivel\nSuperior',
                    'Salida\nNivel\nInferior', 'Reajustes\n(+) (-)', 'Saldo Mes\nSiguiente'
                ]
                col_widths = [10, 35, 10, 12, 12, 12, 12]

                for hoja_num in range(0, total_movimientos, filas_por_hoja):
                    nombre_hoja = f"BRES_{hoja_num // filas_por_hoja + 1}"
                    fin_hoja = min(hoja_num + filas_por_hoja, total_movimientos)
                    datos_hoja = self.movimientos_data[hoja_num:fin_hoja]

                    df = pd.DataFrame(datos_hoja)
                    for col in columnas:
                        if col not in df.columns:
                            df[col] = ""

                    df = df[columnas]
                    df.columns = encabezados

                    fila_inicio = 8
                    df.to_excel(writer, sheet_name=nombre_hoja, startrow=fila_inicio, index=False, header=False)
                    worksheet = writer.sheets[nombre_hoja]

                    title_format = workbook.add_format({
                        'bold': True, 'align': 'center', 'valign': 'vcenter',
                        'font_size': 12, 'font_name': 'Segoe UI'
                    })
                    subtitle_format = workbook.add_format({
                        'bold': True, 'align': 'center', 'valign': 'vcenter',
                        'font_size': 10, 'font_name': 'Segoe UI'
                    })
                    header_format = workbook.add_format({
                        'bold': True, 'align': 'center', 'valign': 'vcenter',
                        'font_size': 9, 'bg_color': '#ADD8E6', 'font_color': 'black',
                        'border': 1, 'text_wrap': True, 'font_name': 'Segoe UI'
                    })
                    filtro_format = workbook.add_format({
                        'bold': True, 'align': 'center', 'valign': 'vcenter',
                        'font_size': 9, 'text_wrap': True, 'font_name': 'Segoe UI',
                        'fg_color': 'white',
                    })
                    cell_format_center = workbook.add_format({
                        'align': 'center', 'valign': 'vcenter', 'font_size': 9,
                        'border': 1, 'font_name': 'Segoe UI'
                    })
                    cell_format_wrap = workbook.add_format({
                        'align': 'left', 'valign': 'top', 'text_wrap': True,
                        'font_size': 9, 'border': 1, 'font_name': 'Segoe UI'
                    })
                    cell_format_number = workbook.add_format({
                        'num_format': '#,##0.00', 'align': 'right', 'valign': 'vcenter',
                        'font_size': 9, 'border': 1, 'font_name': 'Segoe UI'
                    })

                    # Alturas
                    worksheet.set_row(0, 30)
                    worksheet.set_row(1, 25)
                    worksheet.set_row(2, 25)
                    worksheet.set_row(3, 20)
                    worksheet.set_row(fila_inicio - 1, 60)
                    worksheet.set_row(5, 25)

                    worksheet.merge_range(0, 0, 0, len(encabezados) - 1,
                        "DIRECCIÓN DEPARTAMENTAL DE REDES INTEGRADAS DE SERVICIOS DE SALUD DE GUATEMALA,", title_format)
                    worksheet.merge_range(1, 0, 1, len(encabezados) - 1, "ÁREA NOR ORIENTE", subtitle_format)
                    worksheet.merge_range(2, 0, 2, len(encabezados) - 1, "BALANCE DE BODEGA", subtitle_format)
                    worksheet.merge_range(3, 0, 3, len(encabezados) - 1, f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", subtitle_format)

                    worksheet.merge_range(5, 0, 5, 1, f"Área: {self.combo_area.get()}", filtro_format)
                    worksheet.merge_range(5, 2, 5, 3, f"Distrito: {self.combo_distrito.get()}", filtro_format)
                    worksheet.write(5, 4, f"Tipo de Insumo: {self.combo_tipo_insumo.get()}", filtro_format)
                    worksheet.write(5, 5, f"Nivel Máximo: {self.combo_nivel_maximo.get()}", filtro_format)

                    for col_num, header in enumerate(encabezados):
                        worksheet.write(fila_inicio - 1, col_num, header, header_format)
                        worksheet.set_column(col_num, col_num, col_widths[col_num])

                    for row_offset, row_data in enumerate(df.values):
                        for col_num, cell_value in enumerate(row_data):
                            if encabezados[col_num] == 'Descripción\ndel Insumo':
                                worksheet.write(fila_inicio + row_offset, col_num, cell_value, cell_format_wrap)
                            elif encabezados[col_num] != 'Reajustes\n(+) (-)' and col_num > 2:
                                try:
                                    val = float(cell_value)
                                    worksheet.write_number(fila_inicio + row_offset, col_num, val, cell_format_number)
                                except:
                                    worksheet.write(fila_inicio + row_offset, col_num, cell_value, cell_format_center)
                            else:
                                worksheet.write(fila_inicio + row_offset, col_num, cell_value, cell_format_center)

                    worksheet.set_landscape()
                    worksheet.set_paper(5)
                    worksheet.fit_to_pages(1, 1)
                    worksheet.center_horizontally()

            messagebox.showinfo("Éxito", f"Reporte guardado en:\n{full_path}")
            if messagebox.askyesno("Excel Generado", "¿Desea abrir el archivo?"):
                try:
                    if sys.platform.startswith('win'):
                        os.startfile(full_path)
                    elif sys.platform.startswith('darwin'):
                        os.system(f'open "{full_path}"')
                    else:
                        os.system(f'xdg-open "{full_path}"')
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo abrir el Excel: {str(e)}")
            return full_path

        except Exception as e:
            messagebox.showerror("Error", f"Error al generar Excel: {str(e)}")
            return None

    # -----------------------------
    # Utilidades varias
    # -----------------------------
    def dividir_texto_en_lineas(self, texto, max_caracteres_por_linea=30):
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
                lineas.append(palabra[:max_caracteres_por_linea - 3] + "...")
                continue
            if len((linea_actual + " " + palabra).strip()) > max_caracteres_por_linea:
                if linea_actual:
                    lineas.append(linea_actual.strip())
                linea_actual = palabra
            else:
                linea_actual = (linea_actual + " " + palabra).strip() if linea_actual else palabra
        if linea_actual:
            lineas.append(linea_actual.strip())
        if len(lineas) > 3:
            lineas = lineas[:2] + [lineas[2][:max_caracteres_por_linea - 3] + "..."]
        return "\n".join(lineas)

    def filtrar_movimientos_por_nivel(self, movimientos):
        if not movimientos:
            return []
        area_seleccionada = self.combo_area.get().strip()
        distrito_seleccionado = self.combo_distrito.get().strip()
        movimientos_filtrados = []
        for mov in movimientos:
            area_mov = mov.get('area_nombre')
            distrito_mov = mov.get('distrito_nombre')
            incluir = False
            if distrito_seleccionado:
                if (area_mov == area_seleccionada and distrito_mov == distrito_seleccionado):
                    incluir = True
            elif area_seleccionada:
                if area_mov == area_seleccionada:
                    incluir = True
            else:
                incluir = True
            if incluir:
                movimientos_filtrados.append(mov)
        return movimientos_filtrados

    def cerrar_ventana(self):
        if not messagebox.askyesno("Confirmar", "¿Está seguro que desea cerrar esta ventana?"):
            return
        try:
            if hasattr(self, 'temp_pdf_path') and os.path.exists(self.temp_pdf_path):
                try:
                    os.remove(self.temp_pdf_path)
                except Exception:
                    pass
            try:
                if hasattr(self, "canvas"):
                    self.canvas.unbind_all("<MouseWheel>")
            except Exception:
                pass
            if hasattr(self, 'parent') and self.parent:
                for widget in self.parent.winfo_children():
                    widget.destroy()
            if hasattr(self, "main_window") and self.main_window:
                self.main_window.show_welcome_screen()
        except Exception as e:
            print(f"Error al cerrar ventana: {e}")
            try:
                if hasattr(self, 'parent') and self.parent:
                    self.parent.quit()
                else:
                    sys.exit()
            except Exception:
                pass

    def destroy(self):
        # Quitar cualquier contenedor principal creado por esta clase
        if hasattr(self, 'main_container'):
            self.main_container.destroy()