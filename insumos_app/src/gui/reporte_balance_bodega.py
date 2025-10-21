import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import pandas as pd
from datetime import datetime
import sys
import os
from ttkwidgets.autocomplete import AutocompleteCombobox
from datetime import timedelta

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
    conectar_db,
    obtener_areas,
    obtener_tipos_insumo,
    obtener_insumos_por_tipo,
    obtener_presentaciones
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
        
        self.db = conectar_db()
        
        self._cache_promedios = {}
        self._cache_codigos = {}
        self._cache_saldos = {}
        
        self.movimientos_data = None

        self.cargar_iconos()

        # Paleta local (solo para contenedores de esta vista)
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
            'text_light': '#7f8c8d'
        }
        
        self.modo_fecha_var = tk.StringVar(value="rango")
        self.area_var = tk.StringVar()
        self.distrito_var = tk.StringVar()
        self.tipo_insumo_var = tk.StringVar()
        self.insumo_var = tk.StringVar()
        self.presentacion_var = tk.StringVar()
        self.nivel_maximo_var = tk.StringVar(value="6")
        self.desglose_var = tk.BooleanVar(value=False)
        
        self.current_page = 0
        self.total_pages = 0
        self.zoom_level = 1.0
        self.pdf_path = None
        self.movimientos_data = []

        self.cargar_iconos()

        self.areas = []
        self.distritos = []
        self.tipos_insumo = []
        self.insumos = []
        self.presentaciones = []

        self.setup_ui()
        
        self.cargar_datos_iniciales()

    # -----------------------------
    # Utilidad: Titled Frame con mini-ícono (local, sin estilos globales)
    # -----------------------------
    
    def cargar_datos_iniciales(self):
        """Carga los datos iniciales para los filtros"""
        try:
            conn = conectar_db()
            if not conn:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos")
                return
                
            # Cargar áreas (ya tienes este método)
            self.cargar_areas()
            
            # Cargar tipos de insumo (ya tienes este método)
            self.cargar_tipos_insumo()
            
            # Cargar presentaciones (ya tienes este método)
            self.cargar_presentaciones()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar datos iniciales: {str(e)}")
    
    def create_titled_frame(self, parent, title_text_with_emoji):
        """Crea un frame con título y borde"""
        container = tk.Frame(parent, bg=self.COLORS['white'], bd=1, relief='solid')

        # Header MÁS compacto (de 22 a 18)
        header = tk.Frame(container, bg=self.COLORS['primary'], height=18)
        header.pack(fill='x')
        header.pack_propagate(False)

        label = tk.Label(header,
                        text=title_text_with_emoji,
                        font=('Segoe UI', 7, 'bold'),  
                        fg=self.COLORS['white'],
                        bg=self.COLORS['primary'])
        label.pack(side='left', padx=6, pady=0)  

        # Content MÁS compacto
        content = tk.Frame(container, bg=self.COLORS['white'])
        content.pack(fill='both', expand=True, padx=6, pady=4)  

        return container, content

    def show_initial_message(self):
        """Muestra el mensaje inicial en el visor PDF"""
        # DESTRUIR TODOS LOS WIDGETS HIJOS PRIMERO
        for widget in self.pdf_body.winfo_children():
            widget.destroy()
        
        # Forzar actualización
        self.pdf_body.update_idletasks()

        message_frame = tk.Frame(self.pdf_body, bg=self.COLORS['white'])
        message_frame.place(relx=0.5, rely=0.5, anchor='center')

        self.initial_icon = tk.Label(
            message_frame, 
            text="📋", 
            font=('Segoe UI Emoji', 64),
            fg=self.COLORS['accent'], 
            bg=self.COLORS['white']
        )
        self.initial_icon.pack(pady=(80, 20))
        
        tk.Label(
            message_frame,
            text="Seleccione los filtros y genere la vista previa",
            font=('Segoe UI', 13, 'bold'),
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['white']
        ).pack(pady=(0, 8))
        
        tk.Label(
            message_frame,
            text="Configure las fechas y filtros deseados, luego presione 'Generar Vista Previa'",
            font=('Segoe UI', 9),
            fg=self.COLORS['text_light'],
            bg=self.COLORS['white']
        ).pack(pady=(0, 5))
    
    def show_loading(self):
        """Muestra el indicador de carga"""
        # DESTRUIR TODOS LOS WIDGETS HIJOS PRIMERO
        for widget in self.pdf_body.winfo_children():
            widget.destroy()
        
        # Forzar actualización para asegurar que se destruyeron
        self.pdf_body.update_idletasks()
        
        loading_frame = tk.Frame(self.pdf_body, bg=self.COLORS['white'])
        loading_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        loading_icon = tk.Label(
            loading_frame,  
            text="⏳",
            font=('Segoe UI', 48),
            bg=self.COLORS['white'],
            fg=self.COLORS['accent']
        )
        loading_icon.pack(pady=(0, 15))
        
        loading_label = tk.Label(
            loading_frame,
            text="Generando reporte",
            font=('Segoe UI', 12, 'bold'),
            bg=self.COLORS['white'],
            fg=self.COLORS['accent']
        )
        loading_label.pack()
        
        tk.Label(
            loading_frame,
            text="Por favor espere mientras se procesa la información...",
            font=('Segoe UI', 9),
            fg=self.COLORS['text_light'],
            bg=self.COLORS['white']
        ).pack(pady=(5, 0))
        
        # Forzar actualización para mostrar el loading inmediatamente
        self.pdf_body.update()
    
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

    def _derivar_nivel_y_filtros(self):
        # Deriva el nivel según los combos y retorna un dict para construir WHEREs coherentes
        area = (self.combo_area.get() or '').strip() or None
        distrito = (self.combo_distrito.get() or '').strip() or None

        if distrito:
            return {
                'nivel': 'distrito',
                'area': None,
                'distrito': distrito,
            }
        elif area:
            return {
                'nivel': 'area',
                'area': area,
                'distrito': None,
            }
        else:
            return {
                'nivel': 'general',
                'area': None,
                'distrito': None,
            }
    
    def obtener_movimientos_balance(self, fecha_ini_dt, fecha_fin_dt, contexto):
        conn = self._get_conn()
        if conn is None:
            return []
        cur = conn.cursor(dictionary=True)

        nivel_info = self._derivar_nivel_y_filtros()

        where = []
        params = []

        # Rango del periodo
        where.append("DATE(m.fecha_registro) BETWEEN %s AND %s")
        params.extend([fecha_ini_dt.strftime('%Y-%m-%d'), fecha_fin_dt.strftime('%Y-%m-%d')])

        # Filtro por nivel
        if nivel_info['nivel'] == 'area' and nivel_info['area']:
            where.append("a.nombre = %s")
            params.append(nivel_info['area'])
            where.append("m.distrito_id IS NULL")
        elif nivel_info['nivel'] == 'distrito' and nivel_info['distrito']:
            where.append("d.nombre = %s")
            params.append(nivel_info['distrito'])
            where.append("m.servicio_id IS NULL")

        # Filtros por insumo
        if contexto.get('tipo_insumo'):
            where.append("ti.descripcion = %s")
            params.append(contexto['tipo_insumo'])

        if contexto.get('insumo'):
            where.append("i.nombre = %s")
            params.append(contexto['insumo'])

        # Presentación por EXISTS
        presentacion = contexto.get('presentacion')
        if presentacion:
            where.append("""
                EXISTS (
                    SELECT 1
                    FROM insumo_presentacion ip2
                    JOIN presentacion p2 ON p2.id = ip2.presentacion_id
                    WHERE ip2.insumo_id = m.insumo_id
                    AND p2.nombre = %s
                )
            """)
            params.append(presentacion)

        where_sql = " AND ".join(where)

        sql = f"""
            SELECT
                m.insumo_id AS codigo_insumo,
                i.nombre AS nombre_insumo,
                ti.descripcion AS tipo_insumo,
                a.nombre AS area_nombre,
                d.nombre AS distrito_nombre,
                tm.descripcion AS tipo_movimiento,
                m.cantidad,
                m.fecha_registro,
                d_salida.nombre AS distrito_destino,
                s_salida.nombre AS servicio_destino
            FROM movimiento m
            JOIN insumo i ON i.id = m.insumo_id
            JOIN tipo_insumo ti ON ti.id = i.id_tipo_insumo
            JOIN tipo_movimiento tm ON tm.id = m.tipo_movimiento_id
            LEFT JOIN area a ON a.id = m.area_id
            LEFT JOIN distrito d ON d.id = m.distrito_id
            LEFT JOIN distrito d_salida ON d_salida.id = m.salida_distrito_id
            LEFT JOIN servicio s_salida ON s_salida.id = m.salida_servicio_id
            WHERE {where_sql}
            ORDER BY m.fecha_registro, m.id
        """

        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        return rows
    
    def _fecha_corte_anterior(self, fecha_inicio_periodo):
        """
        Devuelve un datetime del día 25 del mismo mes de 'fecha_inicio_periodo'.
        Si el periodo es [26/M/Y, 25/(M+1)/Y], el corte anterior es 25/M/Y.
        """
        y = fecha_inicio_periodo.year
        m = fecha_inicio_periodo.month
        return datetime(y, m, 25)

    def _formatear_periodo_logistico(self, fecha_ini, fecha_fin):
        """
        Devuelve un string 'Periodo logístico: 26/MM/YYYY – 25/MM/YYYY'
        """
        ini = fecha_ini.strftime('%d/%m/%Y')
        fin = fecha_fin.strftime('%d/%m/%Y')
        return f"Periodo logístico: {ini} – {fin}"

    def _get_conn(self):
        try:
            if self.db is None or not self.db.is_connected():
                self.db = conectar_db()
        except Exception:
            self.db = conectar_db()
        return self.db
    
    def _obtener_saldo_corte_bd(self, fecha_corte_dt, contexto, insumo_id):
        conn = self._get_conn()
        cur = conn.cursor(dictionary=True)

        nivel_info = self._derivar_nivel_y_filtros()

        where = [
            "m.insumo_id = %s",
            "DATE(m.fecha_registro) <= %s"
        ]
        params = [insumo_id, fecha_corte_dt.strftime('%Y-%m-%d')]

        # Filtro por nivel
        if nivel_info['nivel'] == 'area' and nivel_info['area']:
            where.append("a.nombre = %s")
            params.append(nivel_info['area'])
            where.append("m.distrito_id IS NULL")
        elif nivel_info['nivel'] == 'distrito' and nivel_info['distrito']:
            where.append("d.nombre = %s")
            params.append(nivel_info['distrito'])
            where.append("m.servicio_id IS NULL")

        # Filtros por insumo/tipo/presentación
        if contexto.get('tipo_insumo'):
            where.append("ti.descripcion = %s")
            params.append(contexto['tipo_insumo'])

        if contexto.get('insumo'):
            where.append("i.nombre = %s")
            params.append(contexto['insumo'])

        if contexto.get('presentacion'):
            where.append("""
                EXISTS (
                    SELECT 1
                    FROM insumo_presentacion ip2
                    JOIN presentacion p2 ON p2.id = ip2.presentacion_id
                    WHERE ip2.insumo_id = m.insumo_id
                    AND p2.nombre = %s
                )
            """)
            params.append(contexto['presentacion'])

        where_sql = " AND ".join(where)

        sql = f"""
            SELECT
                SUM(
                    CASE
                        WHEN tm.descripcion IN ('ENTRADA NIVEL SUPERIOR', 'INVENTARIO INICIAL', 'REAJUSTE (+)')
                            THEN m.cantidad
                        WHEN tm.descripcion IN ('SALIDA NIVEL INFERIOR', 'REAJUSTE (-)')
                            THEN -m.cantidad
                        ELSE 0
                    END
                ) AS saldo
            FROM movimiento m
            JOIN insumo i ON i.id = m.insumo_id
            JOIN tipo_insumo ti ON ti.id = i.id_tipo_insumo
            JOIN tipo_movimiento tm ON tm.id = m.tipo_movimiento_id
            LEFT JOIN area a ON a.id = m.area_id
            LEFT JOIN distrito d ON d.id = m.distrito_id
            WHERE {where_sql}
        """

        cur.execute(sql, params)
        row = cur.fetchone()
        cur.close()
        return (row['saldo'] or 0) if row and row['saldo'] is not None else 0

    def _obtener_insumos_con_saldo(self, fecha_corte_dt, contexto):
        conn = self._get_conn()
        cur = conn.cursor(dictionary=True)

        nivel_info = self._derivar_nivel_y_filtros()

        where = ["DATE(m.fecha_registro) <= %s"]
        params = [fecha_corte_dt.strftime('%Y-%m-%d')]

        # Filtro por nivel
        if nivel_info['nivel'] == 'area' and nivel_info['area']:
            where.append("a.nombre = %s")
            params.append(nivel_info['area'])
            where.append("m.distrito_id IS NULL")
        elif nivel_info['nivel'] == 'distrito' and nivel_info['distrito']:
            where.append("d.nombre = %s")
            params.append(nivel_info['distrito'])
            where.append("m.servicio_id IS NULL")

        # Filtros por insumo
        if contexto.get('tipo_insumo'):
            where.append("ti.descripcion = %s")
            params.append(contexto['tipo_insumo'])

        if contexto.get('insumo'):
            where.append("i.nombre = %s")
            params.append(contexto['insumo'])

        # Presentación
        if contexto.get('presentacion'):
            where.append("""
                EXISTS (
                    SELECT 1
                    FROM insumo_presentacion ip2
                    JOIN presentacion p2 ON p2.id = ip2.presentacion_id
                    WHERE ip2.insumo_id = m.insumo_id
                    AND p2.nombre = %s
                )
            """)
            params.append(contexto['presentacion'])

        where_sql = " AND ".join(where)

        sql = f"""
            SELECT DISTINCT m.insumo_id
            FROM movimiento m
            JOIN insumo i ON i.id = m.insumo_id
            JOIN tipo_insumo ti ON ti.id = i.id_tipo_insumo
            LEFT JOIN area a ON a.id = m.area_id
            LEFT JOIN distrito d ON d.id = m.distrito_id
            WHERE {where_sql}
        """

        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()

        return {r['insumo_id'] for r in rows}

    def _obtener_saldos_batch(self, fecha_corte_dt, contexto, insumos_ids):
        if not insumos_ids:
            return {}

        conn = self._get_conn()
        cur = conn.cursor(dictionary=True)

        nivel_info = self._derivar_nivel_y_filtros()

        where = [
            f"m.insumo_id IN ({','.join(['%s'] * len(insumos_ids))})",
            "DATE(m.fecha_registro) <= %s"
        ]
        params = list(insumos_ids) + [fecha_corte_dt.strftime('%Y-%m-%d')]

        if nivel_info['nivel'] == 'area' and nivel_info['area']:
            where.append("a.nombre = %s")
            params.append(nivel_info['area'])
            where.append("m.distrito_id IS NULL")
        elif nivel_info['nivel'] == 'distrito' and nivel_info['distrito']:
            where.append("d.nombre = %s")
            params.append(nivel_info['distrito'])
            where.append("m.servicio_id IS NULL")

        if contexto.get('tipo_insumo'):
            where.append("ti.descripcion = %s")
            params.append(contexto['tipo_insumo'])

        if contexto.get('insumo'):
            where.append("i.nombre = %s")
            params.append(contexto['insumo'])

        if contexto.get('presentacion'):
            where.append("""
                EXISTS (
                    SELECT 1
                    FROM insumo_presentacion ip2
                    JOIN presentacion p2 ON p2.id = ip2.presentacion_id
                    WHERE ip2.insumo_id = m.insumo_id
                    AND p2.nombre = %s
                )
            """)
            params.append(contexto['presentacion'])

        where_sql = " AND ".join(where)

        sql = f"""
            SELECT
                m.insumo_id,
                SUM(
                    CASE
                        WHEN tm.descripcion IN ('ENTRADA NIVEL SUPERIOR', 'INVENTARIO INICIAL', 'REAJUSTE (+)')
                            THEN m.cantidad
                        WHEN tm.descripcion IN ('SALIDA NIVEL INFERIOR', 'REAJUSTE (-)')
                            THEN -m.cantidad
                        ELSE 0
                    END
                ) AS saldo
            FROM movimiento m
            JOIN insumo i ON i.id = m.insumo_id
            JOIN tipo_insumo ti ON ti.id = i.id_tipo_insumo
            JOIN tipo_movimiento tm ON tm.id = m.tipo_movimiento_id
            LEFT JOIN area a ON a.id = m.area_id
            LEFT JOIN distrito d ON d.id = m.distrito_id
            WHERE {where_sql}
            GROUP BY m.insumo_id
        """

        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()

        return {r['insumo_id']: (r['saldo'] or 0) for r in rows}
        
    # -----------------------------
    # Formateo
    # -----------------------------
    def formato_float(self, v):
        try:
            num = float(v)
            return f"{num:.2f}"
        except:  # noqa: E722
            return "0.00"
    
    def _normalizar_tipo_mov(self, valor):
        if not valor:
            return 'OTRO'
        t = str(valor).strip().upper()
        while '  ' in t:
            t = t.replace('  ', ' ')
        t = (t.replace('( + )', '(+)')
            .replace('( - )', '(-)')
            .replace('+ )', '+)')
            .replace('( +', '(+')
            .replace('REAJUSTE +', 'REAJUSTE (+)')
            .replace('REAJUSTE -', 'REAJUSTE (-)'))
        s = t.replace(' ', '')

        if ('REAJUSTE' in t and ('(+)' in t or ' POS' in t or 'POSITIVO' in t or ' + ' in t or t.endswith('+'))) or s in ('REAJUSTE(+)', 'REAJUSTE+'):
            return 'REAJUSTE (+)'
        if ('REAJUSTE' in t and ('(-)' in t or ' NEG' in t or 'NEGATIVO' in t or ' - ' in t or t.endswith('-'))) or s in ('REAJUSTE(-)', 'REAJUSTE-'):
            return 'REAJUSTE (-)'

        if t == 'INVENTARIO INICIAL':
            return 'INVENTARIO INICIAL'
        if t == 'ENTRADA NIVEL SUPERIOR':
            return 'ENTRADA NIVEL SUPERIOR'
        if t == 'SALIDA NIVEL INFERIOR':
            return 'SALIDA NIVEL INFERIOR'
        if t == 'ENTREGADO':
            return 'ENTREGADO'
        if t == 'NO ENTREGADO':
            return 'NO ENTREGADO'

        return 'OTRO'
    
    # ==== BEGIN PATCH: handler toggle desglose ====
    def on_toggle_desglose(self, *args):
        try:
            # Limpiar caches y estados dependientes
            if hasattr(self, '_cache_saldos'):
                self._cache_saldos.clear()
            if hasattr(self, '_cache_codigos'):
                self._cache_codigos.clear()
            # Resetear destinos del desglose
            self.destinos_desglose = []
        except Exception as e:
            print(f"[DEBUG] on_toggle_desglose error: {e}")
    # ==== END PATCH ====
    
    # -----------------------------
    # UI principal (sin frame intermedio global, solo local)
    # -----------------------------
    def setup_ui(self):
        # Contenedor principal con fondo light (local)
        self.main_container = tk.Frame(self.parent, bg=self.COLORS['light'])
        self.main_container.pack(fill="both", expand=True)

        # Franja superior azul para pegar el header al tope
        top_strip = tk.Frame(self.main_container, bg=self.COLORS['primary'], height=6)
        top_strip.pack(fill='x', padx=0, pady=0)
        top_strip.pack_propagate(False)
        
        # Título principal (local)
        title_frame = tk.Frame(self.main_container, bg=self.COLORS['primary'], height=70)
        title_frame.pack(fill='x', padx=0)
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

        # Sección Fechas - MÁS COMPACTA
        self.frame_fechas_container, self.frame_fechas = self.create_titled_frame(
            self.main_container, "📅 Selección de Fechas/Corte Logístico"
        )
        self.frame_fechas_container.config(bg=self.COLORS['light'])
        self.frame_fechas.config(bg=self.COLORS['light'])
        self.frame_fechas_container.pack(fill="x", padx=5, pady=2)  

        # Rango - Reducir espaciado
        self.frame_rango = tk.Frame(self.frame_fechas, bg=self.COLORS['light'])
        self.frame_rango.pack(fill="x", padx=5, pady=1) 
        
        for i in range(5):
            self.frame_rango.grid_columnconfigure(i, weight=1)

        ttk.Radiobutton(
            self.frame_rango,
            text="Rango de Fechas:",
            variable=self.modo_fecha_var,
            value="rango",
            command=self.actualizar_visibilidad_fechas
        ).grid(row=0, column=0, padx=5, sticky='w')

        ttk.Label(self.frame_rango, text="Fecha Inicial:").grid(row=0, column=1, padx=5, sticky='e')
        self.fecha_inicial = DateEntry(self.frame_rango, width=16, date_pattern='dd/mm/yyyy', state='normal')
        self.fecha_inicial.grid(row=0, column=2, padx=5, sticky='ew')

        ttk.Label(self.frame_rango, text="Fecha Final:").grid(row=0, column=3, padx=5, sticky='e')
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
            command=self.actualizar_visibilidad_fechas
        ).grid(row=0, column=0, padx=5, sticky='w')

        ttk.Label(self.frame_corte, text="Año:").grid(row=0, column=1, padx=5, sticky='w')
        self.anio_var = tk.StringVar()
        anios = [str(a) for a in range(datetime.now().year - 5, datetime.now().year + 2)]
        self.combo_anio = ttk.Combobox(self.frame_corte, textvariable=self.anio_var, values=anios, width=8, state="readonly")
        self.combo_anio.grid(row=0, column=2, padx=5, sticky='ew')
        self.combo_anio.set(str(datetime.now().year))

        ttk.Label(self.frame_corte, text="Mes Inicio:").grid(row=0, column=3, padx=5, sticky='w')
        self.mes_inicio_var = tk.StringVar()
        meses = [datetime(2024, m, 1).strftime("%B").capitalize() for m in range(1, 13)]
        self.combo_mes_inicio = ttk.Combobox(self.frame_corte, textvariable=self.mes_inicio_var, values=meses, width=12, state="readonly")
        self.combo_mes_inicio.grid(row=0, column=4, padx=5, sticky='ew')

        ttk.Label(self.frame_corte, text="Mes Final:").grid(row=0, column=5, padx=5, sticky='w')
        self.mes_final_var = tk.StringVar()
        self.combo_mes_final = ttk.Combobox(self.frame_corte, textvariable=self.mes_final_var, values=meses, width=12, state="readonly")
        self.combo_mes_final.grid(row=0, column=6, padx=5, sticky='ew')

        self.combo_anio.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte)
        self.combo_mes_inicio.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte)
        self.combo_mes_final.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte)
        self.actualizar_visibilidad_fechas()

        # Ubicación (Área / Distrito) - MÁS COMPACTA
        self.frame_ubicacion_container, frame_ubicacion_content = self.create_titled_frame(
            self.main_container, "📍 Ubicación"
        )
        self.frame_ubicacion_container.config(bg=self.COLORS['light'])
        frame_ubicacion_content.config(bg=self.COLORS['light'])
        self.frame_ubicacion_container.pack(fill="x", padx=5, pady=2)  

        frame_ubicacion_content.grid_columnconfigure(1, weight=1)
        frame_ubicacion_content.grid_columnconfigure(3, weight=1)

        ttk.Label(frame_ubicacion_content, text="Área:").grid(row=0, column=0, padx=3, pady=2, sticky='w')  
        self.area_var = tk.StringVar()
        self.combo_area = AutocompleteCombobox(frame_ubicacion_content, textvariable=self.area_var, state="normal", font=('Segoe UI', 9))
        self.combo_area.grid(row=0, column=1, padx=3, pady=2, sticky='ew')

        ttk.Label(frame_ubicacion_content, text="Distrito:").grid(row=0, column=2, padx=3, pady=2, sticky='w')
        self.distrito_var = tk.StringVar()
        self.combo_distrito = AutocompleteCombobox(frame_ubicacion_content, textvariable=self.distrito_var, state="normal", font=('Segoe UI', 9))
        self.combo_distrito.grid(row=0, column=3, padx=3, pady=2, sticky='ew')

        # Insumo - MÁS COMPACTA
        self.frame_insumo_container, frame_insumo_content = self.create_titled_frame(
            self.main_container, "💊 Insumo"
        )
        self.frame_insumo_container.config(bg=self.COLORS['light'])
        frame_insumo_content.config(bg=self.COLORS['light'])
        self.frame_insumo_container.pack(fill="x", padx=5, pady=2)  

        frame_insumo_content.grid_columnconfigure(1, weight=1, minsize=150)
        frame_insumo_content.grid_columnconfigure(3, weight=3, minsize=350)
        frame_insumo_content.grid_columnconfigure(5, weight=1, minsize=150)

        ttk.Label(frame_insumo_content, text="Tipo de Insumo:").grid(row=0, column=0, padx=3, pady=2, sticky='w')
        self.tipo_insumo_var = tk.StringVar()
        self.combo_tipo_insumo = AutocompleteCombobox(frame_insumo_content, textvariable=self.tipo_insumo_var, state="normal", font=('Segoe UI', 9))
        self.combo_tipo_insumo.grid(row=0, column=1, padx=3, pady=2, sticky='ew')

        ttk.Label(frame_insumo_content, text="Insumo:").grid(row=0, column=2, padx=3, pady=2, sticky='w')
        self.insumo_var = tk.StringVar()
        self.combo_insumo = AutocompleteCombobox(frame_insumo_content, textvariable=self.insumo_var, state="normal", font=('Segoe UI', 9))
        self.combo_insumo.grid(row=0, column=3, padx=3, pady=2, sticky='ew')

        ttk.Label(frame_insumo_content, text="Presentación:").grid(row=0, column=4, padx=3, pady=2, sticky='w')
        self.presentacion_var = tk.StringVar()
        self.combo_presentacion = AutocompleteCombobox(frame_insumo_content, textvariable=self.presentacion_var, state="normal", font=('Segoe UI', 9))
        self.combo_presentacion.grid(row=0, column=5, padx=3, pady=2, sticky='ew')

        # Nivel Máximo - MÁS COMPACTA
        self.frame_nivel_container, frame_nivel_content = self.create_titled_frame(
            self.main_container, "📈 Nivel Máximo"
        )
        self.frame_nivel_container.config(bg=self.COLORS['light'])
        frame_nivel_content.config(bg=self.COLORS['light'])
        self.frame_nivel_container.pack(fill="x", padx=5, pady=2)

        ttk.Label(frame_nivel_content, text="Nivel Máximo:").grid(row=0, column=0, padx=3, pady=2, sticky='w')
        self.nivel_maximo_var = tk.StringVar()
        niveles = [str(i) for i in range(1, 12 + 1)]
        self.combo_nivel_maximo = ttk.Combobox(frame_nivel_content, textvariable=self.nivel_maximo_var, values=niveles, width=10, state="readonly")
        self.combo_nivel_maximo.grid(row=0, column=1, padx=3, pady=2, sticky='w')
        self.combo_nivel_maximo.set("6")

        # ==== BEGIN PATCH: Checkbutton desglose con trace ====
        ttk.Checkbutton(
            frame_nivel_content, 
            text="Detalle de Salidas por Distrito o Servicio", 
            variable=self.desglose_var
        ).grid(row=0, column=2, padx=15, pady=2, sticky='w')

        # Vincular cambio de estado del check para limpiar caches/estados
        self.desglose_var.trace_add('write', lambda *a: self.on_toggle_desglose())
        # ==== END PATCH ====

        # Visor PDF - AUMENTAR TAMAÑO VERTICAL
        self.pdf_outer = tk.Frame(self.main_container, bg=self.COLORS['light'])
        self.pdf_outer.pack(fill="both", expand=True, padx=5, pady=3)  # expand=True para que crezca

        self.pdf_frame = tk.Frame(self.pdf_outer, bg=self.COLORS['white'], relief="solid", bd=1, highlightthickness=0)
        self.pdf_frame.pack(fill="both", expand=True)  # expand=True

        # Header compacto
        pdf_header = tk.Frame(self.pdf_frame, bg=self.COLORS['primary'], height=22)  # De 26 a 22
        pdf_header.pack(fill="x")
        pdf_header.pack_propagate(False)

        tk.Label(pdf_header,
                text="🖼️ Vista previa del PDF",
                font=('Segoe UI', 8, 'bold'),  # De 9 a 8
                fg=self.COLORS['white'],
                bg=self.COLORS['primary']).pack(side="left", padx=8, pady=1)

        self.pdf_body = tk.Frame(self.pdf_frame, bg=self.COLORS['white'])
        self.pdf_body.pack(fill="both", expand=True, padx=6, pady=6)  # De 8 a 6

        # MOSTRAR MENSAJE INICIAL
        self.show_initial_message()

        # Botones - MÁS COMPACTOS
        self.frame_botones = tk.Frame(self.main_container, bg=self.COLORS['light'])
        self.frame_botones.pack(fill="x", side="bottom", pady=(5, 8))  # De (20, 10) a (5, 8)

        btn_font = ('Segoe UI', 9, 'bold')
        btn_bg = self.COLORS['light']
        btn_fg = self.COLORS['text_dark']

        btn_report = tk.Button(self.frame_botones,
                            text="Generar Vista Previa",
                            command=self.generar_vista_previa,
                            font=btn_font, bg=btn_bg, fg=btn_fg,
                            relief='flat', borderwidth=0,
                            highlightthickness=0, padx=12, pady=5,  
                            cursor='hand2',
                            image=self.icon_preview if self.icon_preview else "",
                            compound='left' if self.icon_preview else None)
        btn_report.pack(side="left", padx=3)  

        btn_print = tk.Button(self.frame_botones,
                              text="Imprimir",
                              command=self.imprimir_pdf,
                              font=btn_font, bg=btn_bg, fg=btn_fg,
                              relief='flat', borderwidth=0,
                              highlightthickness=0, padx=15, pady=5,
                              cursor='hand2',
                              image=self.icon_print if self.icon_print else "",
                              compound='left' if self.icon_print else None)
        btn_print.pack(side="left", padx=3)

        btn_pdf = tk.Button(self.frame_botones,
                            text="Exportar a PDF",
                            command=self.exportar_pdf,
                            font=btn_font, bg=btn_bg, fg=btn_fg,
                            relief='flat', borderwidth=0,
                            highlightthickness=0, padx=15, pady=5,
                            cursor='hand2',
                            image=self.icon_pdf if self.icon_pdf else "",
                            compound='left' if self.icon_pdf else None)
        btn_pdf.pack(side="left", padx=3)

        btn_excel = tk.Button(self.frame_botones,
                              text="Exportar a Excel",
                              command=self.generar_excel_reporte,
                              font=btn_font, bg=btn_bg, fg=btn_fg,
                              relief='flat', borderwidth=0,
                              highlightthickness=0, padx=15, pady=5,
                              cursor='hand2',
                              image=self.icon_excel if self.icon_excel else "",
                              compound='left' if self.icon_excel else None)
        btn_excel.pack(side="left", padx=3)

        btn_close = tk.Button(self.frame_botones,
                              text="Cerrar",
                              command=self.cerrar_ventana,
                              font=btn_font, bg=btn_bg, fg=btn_fg,
                              relief='flat', borderwidth=0,
                              highlightthickness=0, padx=15, pady=5,
                              cursor='hand2',
                              image=self.icon_close if self.icon_close else "",
                              compound='left' if self.icon_close else None)
        btn_close.pack(side="right", padx=3)

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

        # Inicio: 26 del mes anterior al mes_inicio
        if m_ini == 1:
            fecha_ini_dt = datetime(anio - 1, 12, 26)
        else:
            fecha_ini_dt = datetime(anio, m_ini - 1, 26)

        # Fin: 25 del mes_final
        fecha_fin_dt = datetime(anio, m_fin, 25)

        fecha_ini_str = fecha_ini_dt.strftime('%d/%m/%Y')
        fecha_fin_str = fecha_fin_dt.strftime('%d/%m/%Y')
        return fecha_ini_str, fecha_fin_str, fecha_ini_dt, fecha_fin_dt
    
    def actualizar_fechas_por_corte(self, event=None):
        try:
            anio = self.anio_var.get()
            mes_inicio = self.mes_inicio_var.get()
            mes_final = self.mes_final_var.get()
            if anio and mes_inicio and mes_final:
                fecha_ini_str, fecha_fin_str, fecha_ini_dt, fecha_fin_dt = self.calcular_rango_corte_logistico(anio, mes_inicio, mes_final)
                # Sincroniza los DateEntry usando los datetime
                self.fecha_inicial.set_date(fecha_ini_dt)
                self.fecha_final.set_date(fecha_fin_dt)
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
    # Códigos de insumo
    # -----------------------------
    
    def generar_codigo_insumo(self, movimientos_raw):
        """Genera códigos únicos con una sola consulta optimizada"""
        
        # ✅ Verificar cache
        insumos_unicos = {}
        for mov in movimientos_raw:
            insumo_id = mov.get('codigo_insumo')
            if insumo_id is not None and str(insumo_id).strip():
                if insumo_id not in insumos_unicos:
                    insumos_unicos[insumo_id] = mov.get('nombre_insumo', '')

        if not insumos_unicos:
            return {}

        # ✅ Verificar si ya están en cache
        cache_key = tuple(sorted(insumos_unicos.keys()))
        if cache_key in self._cache_codigos:
            return self._cache_codigos[cache_key]

        try:
            conn = conectar_db()
            if not conn:
                return {}

            cursor = conn.cursor(dictionary=True)
            insumo_ids = list(insumos_unicos.keys())
            placeholders = ','.join(['%s'] * len(insumo_ids))
            
            # ✅ UNA SOLA CONSULTA optimizada
            query_optimizada = f"""
                SELECT 
                    i.id as insumo_id,
                    ti.id as tipo_id,
                    ti.descripcion as tipo_insumo_descripcion,
                    ti.codigo_prefijo,
                    (SELECT COUNT(*) FROM insumo i2 
                    WHERE i2.id_tipo_insumo = ti.id AND i2.id <= i.id) as posicion
                FROM insumo i
                INNER JOIN tipo_insumo ti ON i.id_tipo_insumo = ti.id
                WHERE i.id IN ({placeholders})
                ORDER BY ti.id, i.id
            """
            cursor.execute(query_optimizada, insumo_ids)
            resultados = cursor.fetchall()

            codigos_insumos = {}
            for resultado in resultados:
                insumo_id = resultado['insumo_id']
                tipo_descripcion = (resultado['tipo_insumo_descripcion'] or '').strip().upper()
                codigo_prefijo = resultado['codigo_prefijo']
                posicion = resultado['posicion']
                
                # Usar codigo_prefijo de BD o generar
                if codigo_prefijo:
                    prefijo = codigo_prefijo
                else:
                    tipo_limpio = ''.join(c for c in tipo_descripcion if c.isalnum())
                    prefijo = (tipo_limpio[:4] if len(tipo_limpio) >= 4 else (tipo_limpio + 'XXXX')[:4]).upper()
                
                codigo = f"{prefijo}-{posicion:04d}"
                codigos_insumos[insumo_id] = codigo

            conn.close()
            
            # ✅ Guardar en cache
            self._cache_codigos[cache_key] = codigos_insumos
            return codigos_insumos

        except Exception as e:
            print(f"DEBUG: Error obteniendo códigos de insumo: {e}")
            import traceback
            traceback.print_exc()
            return {}
   
    # -----------------------------
    # Procesamiento de datos
    # -----------------------------
    
    def _formatear_periodo_logistico(self, fecha_ini, fecha_fin):
        """
        Devuelve un string 'Periodo logístico: 26/MM/YYYY – 25/MM/YYYY' usando fecha_ini/fecha_fin.
        """
        ini = fecha_ini.strftime('%d/%m/%Y')
        fin = fecha_fin.strftime('%d/%m/%Y')
        return f"Periodo logístico: {ini} – {fin}"
    
    def procesar_datos_balance(self, movimientos_raw, fecha_ini, fecha_fin, todos_los_insumos=None):
        codigos_insumos = self.generar_codigo_insumo(movimientos_raw)

        if todos_los_insumos is None:
            todos_los_insumos = set(codigos_insumos.keys())

        # Agregar insumos sin movimientos
        conn = conectar_db()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                for insumo_id in todos_los_insumos:
                    if insumo_id not in codigos_insumos:
                        cursor.execute("""
                            SELECT 
                                i.id,
                                i.nombre AS nombre_insumo,
                                i.id_tipo_insumo,
                                ti.descripcion AS tipo_insumo_descripcion,
                                ti.codigo_prefijo
                            FROM insumo i
                            INNER JOIN tipo_insumo ti ON i.id_tipo_insumo = ti.id
                            WHERE i.id = %s
                        """, (insumo_id,))
                        
                        info = cursor.fetchone()
                        if info:
                            if info.get('codigo_prefijo'):
                                prefijo = info['codigo_prefijo']
                            else:
                                tipo_descripcion = (info.get('tipo_insumo_descripcion') or '').strip().upper()
                                tipo_limpio = ''.join(c for c in tipo_descripcion if c.isalnum())
                                prefijo = (tipo_limpio[:4] if len(tipo_limpio) >= 4 else (tipo_limpio + 'XXXX')[:4]).upper()
                            
                            cursor.execute("""
                                SELECT COUNT(*) + 1 as posicion
                                FROM insumo
                                WHERE id_tipo_insumo = %s AND id < %s
                            """, (info['id_tipo_insumo'], insumo_id))
                            pos = cursor.fetchone()['posicion']
                            codigos_insumos[insumo_id] = f"{prefijo}-{str(pos).zfill(4)}"
                            
                            movimientos_raw.append({
                                'codigo_insumo': insumo_id,
                                'nombre_insumo': info['nombre_insumo'],
                                'tipo_movimiento': 'INVENTARIO INICIAL',
                                'cantidad': 0,
                                'fecha_registro': fecha_ini,
                            })
            finally:
                cursor.close()
                conn.close()

        # Determinar si se debe desglosar
        desglosar = self.desglose_var.get()
        nivel = None
        destinos = []
        
        if desglosar:
            area_sel = self.combo_area.get().strip()
            distrito_sel = self.combo_distrito.get().strip()
            
            if area_sel and not distrito_sel:
                nivel = 'area'
                destinos = self.obtener_destinos_salida(movimientos_raw, 'area')
            elif distrito_sel:
                nivel = 'distrito'
                destinos = self.obtener_destinos_salida(movimientos_raw, 'distrito')

        insumos_dict = {}

        for mov in movimientos_raw:
            insumo_id = mov.get('codigo_insumo')
            if insumo_id is None or str(insumo_id).strip() == '':
                continue

            codigo_generado = codigos_insumos.get(insumo_id) or f"TEMP-{str(insumo_id).zfill(4)}"
            nombre_insumo = mov.get('nombre_insumo', '')
            tipo_movimiento = self._normalizar_tipo_mov(mov.get('tipo_movimiento', ''))

            raw_cant = str(mov.get('cantidad', '0')).replace(',', '')
            try:
                cantidad = float(raw_cant)
            except:  # noqa: E722
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
                    'reajustes_neto': 0.0,
                }
                
                if desglosar and destinos:
                    for destino in destinos:
                        insumos_dict[codigo_generado][f'salida_{destino}'] = 0.0

            # ✅ Incluir INVENTARIO INICIAL como entrada del periodo logístico
            if tipo_movimiento in ('INVENTARIO INICIAL', 'ENTRADA NIVEL SUPERIOR'):
                insumos_dict[codigo_generado]['entrada_nivel_superior'] += cantidad

            elif tipo_movimiento == 'SALIDA NIVEL INFERIOR':
                insumos_dict[codigo_generado]['salida_nivel_inferior'] += cantidad
                
                if desglosar and destinos:
                    if nivel == 'area':
                        destino = mov.get('distrito_destino', '')
                    elif nivel == 'distrito':
                        destino = mov.get('servicio_destino', '')
                    else:
                        destino = ''
                    
                    if destino and f'salida_{destino}' in insumos_dict[codigo_generado]:
                        insumos_dict[codigo_generado][f'salida_{destino}'] += cantidad

            elif tipo_movimiento == 'REAJUSTE (+)':
                insumos_dict[codigo_generado]['reajuste_positivo'] += cantidad
                insumos_dict[codigo_generado]['reajustes_neto'] += cantidad

            elif tipo_movimiento == 'REAJUSTE (-)':
                insumos_dict[codigo_generado]['reajuste_negativo'] += cantidad
                insumos_dict[codigo_generado]['reajustes_neto'] -= cantidad

        # ✅ ASIGNAR SALDO ANTERIOR DESDE BD (calculado hasta el 25 del mes de inicio)
        for codigo, datos in insumos_dict.items():
            insumo_id = datos['insumo_id_original']
            # Usar el saldo calculado hasta la fecha de corte anterior
            saldo_bd = self.saldo_anterior_por_insumo.get(insumo_id, 0.0)
            datos['saldo_anterior'] = saldo_bd

        # Construir filas de salida
        datos_procesados = []
        for codigo, datos in insumos_dict.items():
            reajustes_total = float(datos['reajustes_neto'])

            # ✅ CÁLCULO CORRECTO DEL SALDO MES SIGUIENTE
            saldo_mes_siguiente = (
                float(datos['saldo_anterior']) +
                float(datos['entrada_nivel_superior']) -
                float(datos['salida_nivel_inferior']) +
                reajustes_total
            )

            if reajustes_total > 0:
                reajustes_texto = f"+{self.formato_float(reajustes_total)}"
            elif reajustes_total < 0:
                reajustes_texto = self.formato_float(reajustes_total)
            else:
                reajustes_texto = self.formato_float(reajustes_total)

            fila = {
                'codigo_insumo': codigo,
                'nombre_insumo': datos['nombre_insumo'],
                'saldo_anterior': self.formato_float(datos['saldo_anterior']),
                'entrada_nivel_superior': self.formato_float(datos['entrada_nivel_superior']),
                'salida_nivel_inferior': self.formato_float(datos['salida_nivel_inferior']),
                'reajuste_mas': self.formato_float(datos['reajuste_positivo']),
                'reajuste_menos': self.formato_float(datos['reajuste_negativo']),
                'reajustes': reajustes_texto,
                'saldo_mes_siguiente': self.formato_float(saldo_mes_siguiente),
            }
            
            if desglosar and destinos:
                for destino in destinos:
                    fila[f'salida_{destino}'] = self.formato_float(datos.get(f'salida_{destino}', 0.0))
            
            datos_procesados.append(fila)

        datos_procesados.sort(key=lambda x: x['codigo_insumo'])
        
        self.destinos_desglose = destinos if (desglosar and destinos) else []
        
        return datos_procesados
    
    def obtener_destinos_salida(self, movimientos_raw, nivel):
        """
        Obtiene los destinos únicos de SALIDA NIVEL INFERIOR
        - Si nivel = 'area': retorna distritos
        - Si nivel = 'distrito': retorna servicios
        """
        destinos = set()
        
        for mov in movimientos_raw:
            tipo_mov = self._normalizar_tipo_mov(mov.get('tipo_movimiento', ''))
            if tipo_mov == 'SALIDA NIVEL INFERIOR':
                if nivel == 'area':
                    destino = mov.get('distrito_destino')
                    if destino:
                        destinos.add(destino)
                elif nivel == 'distrito':
                    destino = mov.get('servicio_destino')
                    if destino:
                        destinos.add(destino)
        
        return sorted(list(destinos))
    
    # -----------------------------
    # Generar Vista Previa (visor local)
    # -----------------------------
    def generar_vista_previa(self):
        try:
            # MOSTRAR LOADING
            self.show_loading()
            self.parent.update_idletasks()
            
            # ==== BEGIN PATCH: reset de caches/estados por corrida ====
            # Limpiar caches volátiles en cada generación para evitar residuos entre modos (con/sin desglose)
            if hasattr(self, '_cache_saldos'):
                self._cache_saldos.clear()
            if hasattr(self, '_cache_codigos'):
                self._cache_codigos.clear()
            # Asegurar que destinos_desglose se recalcula en esta corrida
            self.destinos_desglose = []
            # ==== END PATCH ====
            
            # Fechas
            if self.modo_fecha_var.get() == "rango":
                fecha_ini = datetime.strptime(self.fecha_inicial.get(), '%d/%m/%Y')
                fecha_fin = datetime.strptime(self.fecha_final.get(), '%d/%m/%Y')
                self.periodo_logistico_text = f"Periodo logístico: {self.fecha_inicial.get()} al {self.fecha_final.get()}"
            else:
                anio = self.anio_var.get()
                mes_inicio = self.mes_inicio_var.get()
                mes_final = self.mes_final_var.get()
                if not all([anio, mes_inicio, mes_final]):
                    messagebox.showerror("Error", "Debe seleccionar Año, Mes Inicio y Mes Final")
                    return
                fecha_ini_str, fecha_fin_str, fecha_ini_dt, fecha_fin_dt = self.calcular_rango_corte_logistico(anio, mes_inicio, mes_final)
                fecha_ini = fecha_ini_dt
                fecha_fin = fecha_fin_dt
                
                periodo_txt = self._formatear_periodo_logistico(fecha_ini, fecha_fin)
                if not hasattr(self, 'lbl_periodo_logistico_ui'):
                    self.lbl_periodo_logistico_ui = tk.Label(self.pdf_outer, text=periodo_txt, bg=self.COLORS['light'], fg=self.COLORS['text_dark'], font=('Segoe UI', 9, 'italic'))
                    self.lbl_periodo_logistico_ui.pack(anchor='w', padx=5, pady=(0, 4))
                else:
                    self.lbl_periodo_logistico_ui.config(text=periodo_txt)
                
            if fecha_fin < fecha_ini:
                messagebox.showerror("Error", "La fecha final debe ser mayor a la inicial")
                return

            # Construir contexto primero
            contexto = {
                'area': (self.combo_area.get() or '').strip() or None,
                'distrito': (self.combo_distrito.get() or '').strip() or None,
                'presentacion': (self.combo_presentacion.get() or '').strip() or None,
                'tipo_insumo': (self.combo_tipo_insumo.get() or '').strip() or None,
                'insumo': (self.combo_insumo.get() or '').strip() or None
            }

            # Usar el método de la clase
            movimientos_raw = self.obtener_movimientos_balance(
                fecha_ini,  # pasa datetime
                fecha_fin,
                contexto
            )

            # Construir contexto con TODOS los filtros
            contexto = {
                'area': (self.combo_area.get() or '').strip() or None,
                'distrito': (self.combo_distrito.get() or '').strip() or None,
                'presentacion': (self.combo_presentacion.get() or '').strip() or None,
                'tipo_insumo': (self.combo_tipo_insumo.get() or '').strip() or None,
                'insumo': (self.combo_insumo.get() or '').strip() or None
            }

            # ✅ Calcular saldo hasta UN DÍA ANTES del inicio del periodo
            fecha_corte_anterior = fecha_ini - timedelta(days=1)

            # Obtener insumos con saldo
            insumos_con_saldo = self._obtener_insumos_con_saldo(fecha_corte_anterior, contexto)

            # Detectar insumos con movimientos en el periodo actual
            insumo_ids_en_periodo = set()
            for m in movimientos_raw:
                iid = m.get('codigo_insumo')
                if iid is not None:
                    try:
                        iid = int(str(iid).strip())
                        insumo_ids_en_periodo.add(iid)
                    except:  # noqa: E722
                        pass

            # Combinar
            todos_los_insumos = set(insumos_con_saldo) | insumo_ids_en_periodo

            if not todos_los_insumos:
                messagebox.showinfo("Info", "No hay datos para mostrar")
                return

            # ✅ CRÍTICO: Calcular saldo anterior ANTES de procesar datos
            self.saldo_anterior_por_insumo = self._obtener_saldos_batch(
                fecha_corte_anterior,
                contexto, 
                list(todos_los_insumos)
            )

            # ✅ AHORA SÍ procesar datos (con saldos ya calculados)
            self.movimientos_data = self.procesar_datos_balance(
                movimientos_raw, 
                fecha_ini, 
                fecha_fin, 
                todos_los_insumos
            )

            # ==== BEGIN PATCH: sin destinos en desglose (limpiar, recalcular una sola vez) ====
            # NUEVA VALIDACIÓN: Verificar si hay desglose pero no hay destinos
            if self.desglose_var.get() and (not hasattr(self, 'destinos_desglose') or not self.destinos_desglose):
                area_sel = self.combo_area.get().strip()
                distrito_sel = self.combo_distrito.get().strip()
                
                if area_sel and not distrito_sel:
                    mensaje = "No se encontraron salidas a nivel inferior hacia distritos en el periodo seleccionado.\n\n"
                    mensaje += "El reporte se mostrará sin desglose por destinos."
                    messagebox.showwarning("Sin datos de desglose", mensaje)
                elif distrito_sel:
                    mensaje = "No se encontraron salidas a nivel inferior hacia servicios en el periodo seleccionado.\n\n"
                    mensaje += "El reporte se mostrará sin desglose por destinos."
                    messagebox.showwarning("Sin datos de desglose", mensaje)
                
                # Desmarcar el checkbox automáticamente
                self.desglose_var.set(False)
                
                # Limpiar caches y destinos (importante limpiar códigos también)
                self._cache_saldos.clear()
                self._cache_codigos.clear()
                self.destinos_desglose = []
                
                # Recalcular insumos y saldo anterior UNA sola vez
                insumos_con_saldo = self._obtener_insumos_con_saldo(fecha_corte_anterior, contexto)
                insumo_ids_en_periodo = set()
                for m in movimientos_raw:
                    iid = m.get('codigo_insumo')
                    if iid is not None:
                        try:
                            iid = int(str(iid).strip())
                            insumo_ids_en_periodo.add(iid)
                        except:  # noqa: E722
                            pass
                todos_los_insumos = set(insumos_con_saldo) | insumo_ids_en_periodo

                self.saldo_anterior_por_insumo = self._obtener_saldos_batch(
                    fecha_corte_anterior,
                    contexto, 
                    list(todos_los_insumos)
                )
                
                # Reprocesar sin desglose
                self.movimientos_data = self.procesar_datos_balance(movimientos_raw, fecha_ini, fecha_fin, todos_los_insumos)
            # ==== END PATCH ====
            
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

            # [RESTO DEL CÓDIGO DEL VISOR PDF SIN CAMBIOS...]
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
            
            # AJUSTAR AUTOMÁTICAMENTE AL ANCHO DEL VISOR AL CARGAR
            def ajustar_inicial():
                try:
                    canvas.update_idletasks()
                    cw = canvas.winfo_width()
                    if cw > 100:
                        page = doc.load_page(0)
                        zoom = (cw - 40) / page.rect.width  # 40 para margen de scroll
                        self.zoom_level = max(0.5, min(zoom, 3.0))
                        display_page()
                except Exception as e:
                    print(f"Error en ajuste inicial: {e}")
                    display_page()

            # Ejecutar ajuste después de que el canvas esté renderizado
            canvas.after(100, ajustar_inicial)

            def on_mousewheel(event):
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            canvas.bind("<MouseWheel>", on_mousewheel)
            
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

            # SOLO UNA VEZ el periodo logístico
            try:
                if self.modo_fecha_var.get() == "corte" and self.mes_inicio_var.get() and self.mes_final_var.get() and self.anio_var.get():
                    fecha_ini_str, fecha_fin_str, _, _ = self.calcular_rango_corte_logistico(self.anio_var.get(), self.mes_inicio_var.get(), self.mes_final_var.get())
                    _fi = datetime.strptime(fecha_ini_str, '%d/%m/%Y')
                    _ff = datetime.strptime(fecha_fin_str, '%d/%m/%Y')
                else:
                    _fi = datetime.strptime(self.fecha_inicial.get(), '%d/%m/%Y')
                    _ff = datetime.strptime(self.fecha_final.get(), '%d/%m/%Y')

                periodo_txt = self._formatear_periodo_logistico(_fi, _ff)
                periodo_style = ParagraphStyle('PeriodoStyle', parent=styles['Normal'], alignment=1, spaceAfter=12, fontSize=9)
                elements.append(Paragraph(periodo_txt, periodo_style))
            except Exception:
                pass
            
            if hasattr(self, 'periodo_logistico_text'):
                periodo_style = ParagraphStyle('PeriodoStyle', parent=styles['Normal'], alignment=1, spaceAfter=12, fontSize=9)
                elements.append(Paragraph(self.periodo_logistico_text, periodo_style))

            # Filtros
            left_style = ParagraphStyle(name="LeftAlign", alignment=0, fontSize=9, fontName='Helvetica')
            filtros = [
                f"Área: {self.combo_area.get()}",
                f"Distrito: {self.combo_distrito.get()}",
                f"Tipo de Insumo: {self.combo_tipo_insumo.get()}",
                f"Nivel Máximo: {self.combo_nivel_maximo.get()}"
            ]
            data_filtros = [[Paragraph(item, left_style) for item in filtros]]
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

            # Headers dinámicos MÁS COMPACTOS
            headers = [
                'Código',
                'Descripción',
                'Saldo\nAnterior',
                'Entrada\nNivel\nSuperior'
            ]

            # Si hay desglose, agregar columnas de destinos con nombres completos en 3 líneas
            if hasattr(self, 'destinos_desglose') and self.destinos_desglose:
                for destino in self.destinos_desglose:
                    # Dividir nombre en palabras para distribuir en 3 líneas
                    palabras = destino.split()
                    if len(palabras) == 1:
                        # Si es una sola palabra, intentar partir por longitud
                        if len(destino) > 20:
                            tercio = len(destino) // 3
                            linea1 = destino[:tercio]
                            linea2 = destino[tercio:tercio*2]
                            linea3 = destino[tercio*2:]
                            nombre_formateado = f'{linea1}\n{linea2}\n{linea3}'
                        else:
                            nombre_formateado = destino
                    elif len(palabras) == 2:
                        nombre_formateado = f'{palabras[0]}\n{palabras[1]}\n'
                    elif len(palabras) >= 3:
                        # Distribuir palabras en 3 líneas
                        palabras_por_linea = len(palabras) // 3
                        if palabras_por_linea == 0:
                            palabras_por_linea = 1
                        linea1 = ' '.join(palabras[:palabras_por_linea])
                        linea2 = ' '.join(palabras[palabras_por_linea:palabras_por_linea*2])
                        linea3 = ' '.join(palabras[palabras_por_linea*2:])
                        nombre_formateado = f'{linea1}\n{linea2}\n{linea3}'
                    else:
                        nombre_formateado = destino
                    
                    headers.append(nombre_formateado)
            else:
                headers.append('Salida\nNivel\nInferior')

            headers.extend([
                'Reajuste\n(+)(-)',
                'Saldo\nMes\nSiguiente'
            ])

            data = [headers]
            
            for mov in self.movimientos_data:
                row = [
                    mov.get('codigo_insumo', ''),
                    self.dividir_texto_en_lineas(mov.get('nombre_insumo', ''), 30),
                    mov.get('saldo_anterior', ''),
                    mov.get('entrada_nivel_superior', '')
                ]
                
                # Si hay desglose, agregar columnas de destinos
                if hasattr(self, 'destinos_desglose') and self.destinos_desglose:
                    for destino in self.destinos_desglose:
                        row.append(mov.get(f'salida_{destino}', '0.00'))
                else:
                    row.append(mov.get('salida_nivel_inferior', ''))
                
                row.extend([
                    mov.get('reajustes', ''),
                    mov.get('saldo_mes_siguiente', '')
                ])
                
                data.append(row)

            # Anchos de columna dinámicos MÁS AJUSTADOS
            colWidths = [
                0.6*inch,  # Código (reducido)
                2.5*inch,  # Descripción (reducido)
                0.7*inch,  # Saldo Anterior (reducido)
                0.7*inch   # Entradas NS (reducido)
            ]

            # Si hay desglose, distribuir espacio entre destinos
            if hasattr(self, 'destinos_desglose') and self.destinos_desglose:
                ancho_por_destino = 1.0*inch  # Un poco más ancho para nombres completos
                colWidths.extend([ancho_por_destino] * len(self.destinos_desglose))
            else:
                colWidths.append(0.8*inch)  # Salida NI

            colWidths.extend([
                0.8*inch,  # Reajustes (reducido)
                0.8*inch   # Saldo Siguiente (reducido)
            ])
            
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

                columnas_base = [
                    'codigo_insumo', 'nombre_insumo', 'saldo_anterior', 'entrada_nivel_superior'
                ]

                encabezados_base = [
                    'Código', 'Descripción', 'Saldo\nAnterior', 'Entrada\nNivel\nSuperior'
                ]

                col_widths_base = [10, 30, 8, 8]

                # Si hay desglose, agregar columnas de destinos con nombres completos
                if hasattr(self, 'destinos_desglose') and self.destinos_desglose:
                    for destino in self.destinos_desglose:
                        columnas_base.append(f'salida_{destino}')
                        # Dividir nombre en 3 líneas
                        palabras = destino.split()
                        if len(palabras) == 1:
                            if len(destino) > 20:
                                tercio = len(destino) // 3
                                linea1 = destino[:tercio]
                                linea2 = destino[tercio:tercio*2]
                                linea3 = destino[tercio*2:]
                                nombre_formateado = f'{linea1}\n{linea2}\n{linea3}'
                            else:
                                nombre_formateado = destino
                        elif len(palabras) == 2:
                            nombre_formateado = f'{palabras[0]}\n{palabras[1]}\n'
                        elif len(palabras) >= 3:
                            palabras_por_linea = len(palabras) // 3
                            if palabras_por_linea == 0:
                                palabras_por_linea = 1
                            linea1 = ' '.join(palabras[:palabras_por_linea])
                            linea2 = ' '.join(palabras[palabras_por_linea:palabras_por_linea*2])
                            linea3 = ' '.join(palabras[palabras_por_linea*2:])
                            nombre_formateado = f'{linea1}\n{linea2}\n{linea3}'
                        else:
                            nombre_formateado = destino
                        
                        encabezados_base.append(nombre_formateado)
                        col_widths_base.append(15)  # Más ancho para nombres completos
                else:
                    columnas_base.append('salida_nivel_inferior')
                    encabezados_base.append('Salida\nNivel\nInferior')
                    col_widths_base.append(8)

                columnas_base.extend(['reajustes', 'saldo_mes_siguiente'])
                encabezados_base.extend(['Reajuste\n(+)(-)', 'Saldo\nMes\nSiguiente'])
                col_widths_base.extend([8, 8])

                columnas = columnas_base
                encabezados = encabezados_base
                col_widths = col_widths_base

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
                        'font_size': 8, 'bg_color': '#ADD8E6', 'font_color': 'black',
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
                    worksheet.set_row(fila_inicio - 1, 50)
                    worksheet.set_row(5, 25)

                    worksheet.merge_range(0, 0, 0, len(encabezados) - 1,
                        "DIRECCIÓN DEPARTAMENTAL DE REDES INTEGRADAS DE SERVICIOS DE SALUD DE GUATEMALA,", title_format)
                    worksheet.merge_range(1, 0, 1, len(encabezados) - 1, "ÁREA NOR ORIENTE", subtitle_format)
                    worksheet.merge_range(2, 0, 2, len(encabezados) - 1, "BALANCE DE BODEGA", subtitle_format)
                    worksheet.merge_range(3, 0, 3, len(encabezados) - 1, f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", subtitle_format)
                    
                    # Fila 4 para el periodo logístico
                    try:
                        if self.modo_fecha_var.get() == "corte" and self.mes_inicio_var.get() and self.mes_final_var.get() and self.anio_var.get():
                            fi_str, ff_str, _, _ = self.calcular_rango_corte_logistico(self.anio_var.get(), self.mes_inicio_var.get(), self.mes_final_var.get())
                            _fi = datetime.strptime(fi_str, '%d/%m/%Y')
                            _ff = datetime.strptime(ff_str, '%d/%m/%Y')
                        else:
                            _fi = datetime.strptime(self.fecha_inicial.get(), '%d/%m/%Y')
                            _ff = datetime.strptime(self.fecha_final.get(), '%d/%m/%Y')

                        periodo_txt = self._formatear_periodo_logistico(_fi, _ff)
                        worksheet.merge_range(4, 0, 4, len(encabezados) - 1, periodo_txt, subtitle_format)
                        worksheet.set_row(4, 20)
                    except Exception:
                        pass
                                        
                    if hasattr(self, 'periodo_logistico_text'):
                        worksheet.merge_range(4, 0, 4, len(encabezados) - 1, self.periodo_logistico_text, subtitle_format)
                        worksheet.set_row(4, 20)

                    worksheet.merge_range(5, 0, 5, 1, f"Área: {self.combo_area.get()}", filtro_format)
                    worksheet.merge_range(5, 2, 5, 3, f"Distrito: {self.combo_distrito.get()}", filtro_format)
                    worksheet.write(5, 4, f"Tipo de Insumo: {self.combo_tipo_insumo.get()}", filtro_format)
                    worksheet.write(5, 5, f"Nivel Máximo: {self.combo_nivel_maximo.get()}", filtro_format)

                    for col_num, header in enumerate(encabezados):
                        worksheet.write(fila_inicio - 1, col_num, header, header_format)
                        worksheet.set_column(col_num, col_num, col_widths[col_num])

                    for row_offset, row_data in enumerate(df.values):
                        for col_num, cell_value in enumerate(row_data):
                            if encabezados[col_num] == 'Descripción':
                                worksheet.write(fila_inicio + row_offset, col_num, cell_value, cell_format_wrap)
                            elif encabezados[col_num] not in ['Reaj.\n(+)(-)', 'Código'] and col_num > 1:
                                try:
                                    val = float(cell_value)
                                    worksheet.write_number(fila_inicio + row_offset, col_num, val, cell_format_number)
                                except:  # noqa: E722
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
            # ✅ Limpiar todos los caches
            if hasattr(self, '_cache_promedios'):
                self._cache_promedios.clear()
            if hasattr(self, '_cache_codigos'):
                self._cache_codigos.clear()
            if hasattr(self, '_cache_saldos'):
                self._cache_saldos.clear()
            if hasattr(self, 'saldo_anterior_por_insumo'):
                self.saldo_anterior_por_insumo.clear()
            
            # Eliminar PDF temporal
            if hasattr(self, 'temp_pdf_path') and os.path.exists(self.temp_pdf_path):
                try:
                    os.remove(self.temp_pdf_path)
                except Exception:
                    pass
            
            # Desvincular eventos
            try:
                if hasattr(self, "canvas"):
                    self.canvas.unbind_all("<MouseWheel>")
            except Exception:
                pass
            
            # Destruir widgets
            if hasattr(self, 'parent') and self.parent:
                for widget in self.parent.winfo_children():
                    widget.destroy()
            
            # Mostrar pantalla de bienvenida
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
        # Destruye el contenedor principal creado por esta vista y limpia temporales
        try:
            if hasattr(self, 'temp_pdf_path') and os.path.exists(self.temp_pdf_path):
                try:
                    os.remove(self.temp_pdf_path)
                except Exception:
                    pass
        except Exception:
            pass
        if hasattr(self, 'main_container') and self.main_container.winfo_exists():
            self.main_container.destroy()