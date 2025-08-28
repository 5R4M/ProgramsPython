# Imports existentes
from calendar import month_name
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import pandas as pd
from datetime import datetime, timedelta
import locale
import sys
import os
from ttkwidgets.autocomplete import AutocompleteCombobox

# Nuevos imports para PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape, legal
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
    obtener_tipos_servicio_por_distrito,
    obtener_servicios_por_tipo,
    obtener_tipos_insumo,
    obtener_insumos_por_tipo,
    obtener_presentaciones,
    obtener_movimientos_bres
)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        # En desarrollo, base_path es la raíz del proyecto (subir un nivel desde gui)
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(base_path, relative_path)

class ReporteBres:
    # Definir las columnas como atributo de la clase
    COLUMNAS = [
        'Código Insumo', 'Nombre del Insumo', 'Saldo Anterior', 'Entradas Nivel Superior',
        'Entregado a Usuario', 'No Entregado', 'Demanda', 'Reajustes (+) (-)',
        'Saldo Mes Siguiente', 'Existencia Física', 'Promedio Mensual Demanda Real',
        'Meses Existencia Disponible', 'Cantidad Máxima', 'Cantidad a Solicitar'
    ]
    
    def formato_float(self, valor):
        try:
            num = float(valor)
            return f"{num:.2f}"  # Siempre mostrar formato con 2 decimales
        except (ValueError, TypeError):
            return "0.00"  # Mostrar 0.00 en lugar de cadena vacía
    
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
        
        style.configure('White.TLabel',
            background=self.COLORS['white'],
            foreground=self.COLORS['text_dark'],
            font=('Segoe UI', 9))
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
        
        style = ttk.Style()
        style.theme_use('clam')
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
        style = ttk.Style()
        style.configure('White.TCombobox', fieldbackground='white', background='white')
        style.configure('White.TLabel', background='white')
        style.configure('White.TRadiobutton', background='white')
        
    
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
    
    def generar_codigo_insumo(self, movimientos_raw):
        """
        VERSIÓN OPTIMIZADA: Genera códigos únicos basados en posición relativa dentro de cada tipo
        - Una consulta principal para obtener los insumos del reporte
        - Una consulta adicional por tipo para obtener la posición relativa correcta
        """
        # Obtener insumos únicos
        insumos_unicos = {}
        for mov in movimientos_raw:
            insumo_id = mov.get('codigo_insumo')
            insumo_nombre = mov.get('nombre_insumo', '')
            
            if insumo_id is not None and str(insumo_id).strip():
                if insumo_id not in insumos_unicos:
                    insumos_unicos[insumo_id] = insumo_nombre
        
        print(f"DEBUG OPTIMIZED: Insumos únicos encontrados: {len(insumos_unicos)}")
        
        if not insumos_unicos:
            return {}
        
        try:
            conn = conectar_db()
            if not conn:
                print("DEBUG OPTIMIZED: No se pudo conectar a la base de datos")
                return {}
            
            cursor = conn.cursor(dictionary=True)
            
            # CONSULTA PRINCIPAL: Obtener insumos del reporte y sus tipos
            insumo_ids = list(insumos_unicos.keys())
            placeholders = ','.join(['%s'] * len(insumo_ids))
            
            query_principal = f"""
            SELECT 
                i.id as insumo_id,
                ti.id as tipo_id,
                ti.descripcion as tipo_insumo_descripcion
            FROM insumo i
            INNER JOIN tipo_insumo ti ON i.id_tipo_insumo = ti.id
            WHERE i.id IN ({placeholders})
            ORDER BY ti.descripcion, i.id
            """
            
            cursor.execute(query_principal, insumo_ids)
            resultados_principales = cursor.fetchall()
            
            print(f"DEBUG OPTIMIZED: Consulta principal ejecutada para {len(insumo_ids)} insumos, {len(resultados_principales)} resultados")
            
            # Agrupar por tipo de insumo
            insumos_por_tipo = {}
            tipos_unicos = set()
            
            for resultado in resultados_principales:
                insumo_id = resultado['insumo_id']
                tipo_id = resultado['tipo_id']
                tipo_descripcion = resultado['tipo_insumo_descripcion'].strip().upper()
                
                tipos_unicos.add(tipo_id)
                
                if tipo_id not in insumos_por_tipo:
                    insumos_por_tipo[tipo_id] = {
                        'descripcion': tipo_descripcion,
                        'insumos': []
                    }
                
                insumos_por_tipo[tipo_id]['insumos'].append(insumo_id)
            
            # Para cada tipo, obtener TODOS los insumos para calcular posición relativa
            codigos_insumos = {}
            
            for tipo_id, info_tipo in insumos_por_tipo.items():
                tipo_descripcion = info_tipo['descripcion']
                insumos_del_reporte = info_tipo['insumos']
                
                # Consultar TODOS los insumos de este tipo para obtener posiciones relativas
                query_todos_tipo = """
                SELECT i.id as insumo_id
                FROM insumo i
                WHERE i.id_tipo_insumo = %s
                ORDER BY i.id ASC
                """
                
                cursor.execute(query_todos_tipo, (tipo_id,))
                todos_insumos_tipo = cursor.fetchall()
                
                # Crear mapeo de insumo_id a posición relativa (empezando en 1)
                posicion_relativa = {}
                for indice, insumo in enumerate(todos_insumos_tipo, 1):
                    posicion_relativa[insumo['insumo_id']] = indice
                
                # Generar códigos para los insumos que están en el reporte
                tipo_limpio = ''.join(c for c in tipo_descripcion if c.isalnum())
                prefijo = tipo_limpio[:4].upper()
                
                while len(prefijo) < 4:
                    prefijo += 'X'
                
                for insumo_id in insumos_del_reporte:
                    if insumo_id in posicion_relativa:
                        posicion = posicion_relativa[insumo_id]
                        codigo = f"{prefijo}-{posicion:04d}"
                        codigos_insumos[insumo_id] = codigo
            
            conn.close()
            
            print(f"DEBUG OPTIMIZED: Códigos generados: {len(codigos_insumos)} (muestra: {list(codigos_insumos.items())[:3]})")
            return codigos_insumos
            
        except Exception as e:
            print(f"DEBUG OPTIMIZED: Error: {e}")
            import traceback
            traceback.print_exc()
            return {}
        
    def procesar_datos_bres(self, movimientos_raw, fecha_ini, fecha_fin):
        """
        VERSIÓN OPTIMIZADA del método procesar_datos_bres
        Utiliza los métodos batch para reducir drásticamente las consultas SQL
        """
        print(f"DEBUG OPTIMIZED: Procesando {len(movimientos_raw)} movimientos")
        
        # 1. Generar códigos de insumos (1 consulta en lugar de N)
        codigos_insumos = self.generar_codigo_insumo(movimientos_raw)
        
        if not codigos_insumos:
            print("DEBUG OPTIMIZED: No se generaron códigos de insumos")
            return []
        
        # 2. Procesar datos agrupados (igual que antes)
        datos_agrupados = {}
        
        nivel_area = self.combo_area.get().strip()
        nivel_distrito = self.combo_distrito.get().strip()
        nivel_tipo_servicio = self.combo_tipo_servicio.get().strip()
        nivel_servicio = self.combo_servicio.get().strip()

        print(f"DEBUG: Filtros - Área: {nivel_area}, Distrito: {nivel_distrito}, Tipo Servicio: {nivel_tipo_servicio}, Servicio: {nivel_servicio}")

        for mov in movimientos_raw:
            insumo_id = mov.get('codigo_insumo')
            
            if insumo_id is None or str(insumo_id).strip() == '':
                continue
            
            codigo = codigos_insumos.get(insumo_id)
            if not codigo:
                codigo = f"TEMP-{str(insumo_id).zfill(4)}"
            
            nombre = mov.get('nombre_insumo', '')
            area = mov.get('area_nombre', '')
            distrito = mov.get('distrito_nombre', '')
            tipo_servicio = mov.get('tipo_servicio_descripcion', '')
            servicio = mov.get('servicio_nombre', '')
            tipo_movimiento = mov.get('tipo_movimiento', '').upper()
            
            try:
                cantidad = float(mov.get('cantidad', 0))
            except:
                cantidad = 0
            
            if codigo not in datos_agrupados:
                datos_agrupados[codigo] = {
                    'nombre_insumo': nombre,
                    'insumo_id': insumo_id,
                    'saldo_anterior_area': 0,
                    'saldo_anterior_distritos': 0,
                    'saldo_anterior_servicios': 0,
                    'entradas_nivel_superior_area': 0,
                    'entradas_nivel_superior_distritos': 0,
                    'entradas_nivel_superior_servicios': 0,
                    'salidas_nivel_inferior_area': 0,
                    'salidas_nivel_inferior_distritos': 0,
                    'entregado_distritos': 0,
                    'entregado_servicios': 0,
                    'no_entregado_distritos': 0,
                    'no_entregado_servicios': 0,
                    'reajustes_area': 0,
                    'reajustes_distritos': 0,
                    'reajustes_servicios': 0,
                }
            
            # Clasificación y acumulación (igual que antes)
            es_nivel_area = bool(area and not distrito)
            es_nivel_distrito = bool(distrito and not servicio)
            es_nivel_servicio = bool(servicio)
            
            if tipo_movimiento == 'INVENTARIO INICIAL':
                if es_nivel_area:
                    datos_agrupados[codigo]['saldo_anterior_area'] += cantidad
                elif es_nivel_distrito:
                    datos_agrupados[codigo]['saldo_anterior_distritos'] += cantidad
                elif es_nivel_servicio:
                    datos_agrupados[codigo]['saldo_anterior_servicios'] += cantidad
            
            elif tipo_movimiento == 'ENTRADA NIVEL SUPERIOR':
                if es_nivel_area:
                    datos_agrupados[codigo]['entradas_nivel_superior_area'] += cantidad
                elif es_nivel_distrito:
                    datos_agrupados[codigo]['entradas_nivel_superior_distritos'] += cantidad
                elif es_nivel_servicio:
                    datos_agrupados[codigo]['entradas_nivel_superior_servicios'] += cantidad
            
            elif tipo_movimiento == 'SALIDA NIVEL INFERIOR':
                if es_nivel_area:
                    datos_agrupados[codigo]['salidas_nivel_inferior_area'] += cantidad
                elif es_nivel_distrito:
                    datos_agrupados[codigo]['salidas_nivel_inferior_distritos'] += cantidad
            
            elif tipo_movimiento == 'ENTREGADO':
                if es_nivel_distrito:
                    datos_agrupados[codigo]['entregado_distritos'] += cantidad
                elif es_nivel_servicio:
                    datos_agrupados[codigo]['entregado_servicios'] += cantidad
            
            elif tipo_movimiento == 'NO ENTREGADO':
                if es_nivel_distrito:
                    datos_agrupados[codigo]['no_entregado_distritos'] += cantidad
                elif es_nivel_servicio:
                    datos_agrupados[codigo]['no_entregado_servicios'] += cantidad
            
            elif tipo_movimiento == 'REAJUSTE POSITIVO':
                if es_nivel_area:
                    datos_agrupados[codigo]['reajustes_area'] += cantidad
                elif es_nivel_distrito:
                    datos_agrupados[codigo]['reajustes_distritos'] += cantidad
                elif es_nivel_servicio:
                    datos_agrupados[codigo]['reajustes_servicios'] += cantidad
            
            elif tipo_movimiento == 'REAJUSTE NEGATIVO':
                if es_nivel_area:
                    datos_agrupados[codigo]['reajustes_area'] -= cantidad
                elif es_nivel_distrito:
                    datos_agrupados[codigo]['reajustes_distritos'] -= cantidad
                elif es_nivel_servicio:
                    datos_agrupados[codigo]['reajustes_servicios'] -= cantidad
        
        print(f"DEBUG OPTIMIZED: Datos agrupados para {len(datos_agrupados)} códigos")
        
        # 3. OPTIMIZACIÓN: Calcular promedios en lote (1 consulta en lugar de N)
        insumo_ids = [datos['insumo_id'] for datos in datos_agrupados.values() if datos['insumo_id'] is not None]
        promedios_batch = self.calcular_promedio_demanda_real(insumo_ids, fecha_ini, fecha_fin)
        
        print(f"DEBUG OPTIMIZED: Promedios calculados en lote para {len(promedios_batch)} insumos")
        
        # 4. Procesar datos finales usando promedios precalculados
        datos_procesados = []
        
        for codigo, datos in datos_agrupados.items():
            # Consolidación por nivel (igual que antes)
            if nivel_servicio:
                saldo_anterior_total = datos['saldo_anterior_servicios']
                entradas_nivel_superior_total = datos['entradas_nivel_superior_servicios']
                entregado_total = datos['entregado_servicios']
                no_entregado_total = datos['no_entregado_servicios']
                reajustes_total = datos['reajustes_servicios']
            elif nivel_tipo_servicio:
                saldo_anterior_total = datos['saldo_anterior_servicios']
                entradas_nivel_superior_total = datos['entradas_nivel_superior_servicios']
                entregado_total = datos['entregado_servicios']
                no_entregado_total = datos['no_entregado_servicios']
                reajustes_total = datos['reajustes_servicios']
            elif nivel_distrito:
                saldo_anterior_total = datos['saldo_anterior_distritos'] + datos['saldo_anterior_servicios']
                entradas_nivel_superior_total = (datos['entradas_nivel_superior_distritos'] + datos['entradas_nivel_superior_servicios'] - datos['salidas_nivel_inferior_distritos'])
                entregado_total = datos['entregado_distritos'] + datos['entregado_servicios']
                no_entregado_total = datos['no_entregado_distritos'] + datos['no_entregado_servicios']
                reajustes_total = datos['reajustes_distritos'] + datos['reajustes_servicios']
            elif nivel_area:
                saldo_anterior_total = datos['saldo_anterior_area'] + datos['saldo_anterior_distritos'] + datos['saldo_anterior_servicios']
                entradas_nivel_superior_total = (datos['entradas_nivel_superior_area'] + datos['entradas_nivel_superior_distritos'] - datos['salidas_nivel_inferior_area'])
                entregado_total = datos['entregado_distritos'] + datos['entregado_servicios']
                no_entregado_total = datos['no_entregado_distritos'] + datos['no_entregado_servicios']
                reajustes_total = datos['reajustes_area'] + datos['reajustes_distritos'] + datos['reajustes_servicios']
            else:
                saldo_anterior_total = datos['saldo_anterior_area'] + datos['saldo_anterior_distritos'] + datos['saldo_anterior_servicios']
                entradas_nivel_superior_total = (datos['entradas_nivel_superior_area'] + datos['entradas_nivel_superior_distritos'] + datos['entradas_nivel_superior_servicios'] - datos['salidas_nivel_inferior_area'] - datos['salidas_nivel_inferior_distritos'])
                entregado_total = datos['entregado_distritos'] + datos['entregado_servicios']
                no_entregado_total = datos['no_entregado_distritos'] + datos['no_entregado_servicios']
                reajustes_total = datos['reajustes_area'] + datos['reajustes_distritos'] + datos['reajustes_servicios']
            
            saldo_mes_siguiente = (saldo_anterior_total + entradas_nivel_superior_total - entregado_total + reajustes_total)
            demanda_total = entregado_total + no_entregado_total
            
            # USAR PROMEDIO PRECALCULADO (sin consulta adicional)
            promedio_mensual = promedios_batch.get(datos['insumo_id'], 0.0)
            
            meses_existencia = saldo_mes_siguiente / promedio_mensual if promedio_mensual > 0 else 0
            nivel_maximo = float(self.nivel_maximo_var.get()) if self.nivel_maximo_var.get() else 6
            cantidad_maxima = promedio_mensual * nivel_maximo
            cantidad_solicitar = cantidad_maxima - saldo_mes_siguiente
            
            datos_procesados.append({
                'codigo_insumo': codigo,
                'nombre_insumo': datos['nombre_insumo'],
                'saldo_anterior': self.formato_float(saldo_anterior_total),
                'entradas_nivel_superior': self.formato_float(entradas_nivel_superior_total),
                'entregado_usuario': self.formato_float(entregado_total),
                'no_entregado': self.formato_float(no_entregado_total),
                'demanda': self.formato_float(demanda_total),
                'reajustes': f"{'+' if reajustes_total >= 0 else ''}{self.formato_float(reajustes_total)}",
                'saldo_mes_siguiente': self.formato_float(saldo_mes_siguiente),
                'existencia_fisica': self.formato_float(saldo_mes_siguiente),
                'promedio_mensual': self.formato_float(promedio_mensual),
                'meses_existencia': self.formato_float(meses_existencia),
                'cantidad_maxima': self.formato_float(cantidad_maxima),
                'cantidad_solicitar': self.formato_float(cantidad_solicitar),
                'movimientos_individuales': {}
            })
        
        return datos_procesados

    def calcular_promedio_demanda_real(self, insumo_ids, fecha_ini, fecha_fin):
        """
        VERSIÓN OPTIMIZADA: Calcula promedios de demanda para múltiples insumos
        En lugar de hacer 3 consultas por cada insumo, hace 1 consulta para todos
        """
        if not insumo_ids:
            return {}
        
        try:
            from datetime import datetime, timedelta
            
            conn = conectar_db()
            if not conn:
                return {}
            
            cursor = conn.cursor(dictionary=True)
            
            # Calcular rango de fechas para los últimos 3 meses
            fecha_actual = fecha_fin
            
            # Fecha inicio para los 3 meses
            fecha_inicio_calculo = fecha_actual - timedelta(days=90)  # Aproximadamente 3 meses
            
            # Obtener filtros de nivel
            area_seleccionada = getattr(self, 'combo_area', None)
            area_seleccionada = area_seleccionada.get().strip() if area_seleccionada and area_seleccionada.get() else None
            
            distrito_seleccionado = getattr(self, 'combo_distrito', None) 
            distrito_seleccionado = distrito_seleccionado.get().strip() if distrito_seleccionado and distrito_seleccionado.get() else None
            
            tipo_servicio_seleccionado = getattr(self, 'combo_tipo_servicio', None)
            tipo_servicio_seleccionado = tipo_servicio_seleccionado.get().strip() if tipo_servicio_seleccionado and tipo_servicio_seleccionado.get() else None
            
            servicio_seleccionado = getattr(self, 'combo_servicio', None)
            servicio_seleccionado = servicio_seleccionado.get().strip() if servicio_seleccionado and servicio_seleccionado.get() else None
            
            placeholders = ','.join(['%s'] * len(insumo_ids))
            
            # CONSULTA OPTIMIZADA: Demanda por insumo y mes en una sola consulta
            query = f"""
            SELECT 
                m.insumo_id,
                YEAR(m.fecha_registro) as anio,
                MONTH(m.fecha_registro) as mes,
                SUM(m.cantidad) as demanda_mes
            FROM movimiento m
            INNER JOIN tipo_movimiento tm ON m.tipo_movimiento_id = tm.id
            LEFT JOIN area a_directa ON m.area_id = a_directa.id
            LEFT JOIN distrito d_directa ON m.distrito_id = d_directa.id  
            LEFT JOIN servicio s_directa ON m.servicio_id = s_directa.id
            LEFT JOIN tipo_servicio ts_directa ON s_directa.id_tipo_servicio = ts_directa.id
            WHERE m.insumo_id IN ({placeholders})
            AND m.fecha_registro BETWEEN %s AND %s
            AND tm.descripcion IN ('ENTREGADO', 'NO ENTREGADO')
            """
            
            params = list(insumo_ids) + [fecha_inicio_calculo.strftime('%Y-%m-%d'), fecha_fin.strftime('%Y-%m-%d')]
            
            # Agregar filtros de nivel según corresponda
            if servicio_seleccionado:
                query += " AND a_directa.nombre = %s AND d_directa.nombre = %s AND s_directa.nombre = %s"
                params.extend([area_seleccionada, distrito_seleccionado, servicio_seleccionado])
            elif tipo_servicio_seleccionado:
                query += " AND a_directa.nombre = %s AND d_directa.nombre = %s AND ts_directa.descripcion = %s"
                params.extend([area_seleccionada, distrito_seleccionado, tipo_servicio_seleccionado])
            elif distrito_seleccionado:
                query += " AND a_directa.nombre = %s AND (d_directa.nombre = %s OR s_directa.id IN (SELECT s.id FROM servicio s INNER JOIN tipo_servicio ts ON s.id_tipo_servicio = ts.id INNER JOIN distrito d ON ts.id_distrito = d.id WHERE d.nombre = %s))"
                params.extend([area_seleccionada, distrito_seleccionado, distrito_seleccionado])
            elif area_seleccionada:
                query += " AND (a_directa.nombre = %s OR d_directa.id IN (SELECT d.id FROM distrito d INNER JOIN area a ON d.id_area = a.id WHERE a.nombre = %s) OR s_directa.id IN (SELECT s.id FROM servicio s INNER JOIN tipo_servicio ts ON s.id_tipo_servicio = ts.id INNER JOIN distrito d ON ts.id_distrito = d.id INNER JOIN area a ON d.id_area = a.id WHERE a.nombre = %s))"
                params.extend([area_seleccionada, area_seleccionada, area_seleccionada])
            
            query += " GROUP BY m.insumo_id, YEAR(m.fecha_registro), MONTH(m.fecha_registro)"
            
            cursor.execute(query, params)
            resultados = cursor.fetchall()
            conn.close()
            
            print(f"DEBUG OPTIMIZED: Consulta batch ejecutada, {len(resultados)} registros obtenidos")
            
            # Procesar resultados para calcular promedios
            demandas_por_insumo = {}
            for resultado in resultados:
                insumo_id = resultado['insumo_id']
                demanda_mes = float(resultado['demanda_mes']) if resultado['demanda_mes'] else 0.0
                
                if insumo_id not in demandas_por_insumo:
                    demandas_por_insumo[insumo_id] = []
                
                demandas_por_insumo[insumo_id].append(demanda_mes)
            
            # Calcular promedios
            promedios = {}
            for insumo_id in insumo_ids:
                if insumo_id in demandas_por_insumo:
                    demandas = demandas_por_insumo[insumo_id]
                    # Tomar las últimas 3 mediciones o las disponibles
                    ultimas_demandas = demandas[-3:] if len(demandas) >= 3 else demandas
                    promedio = sum(ultimas_demandas) / len(ultimas_demandas) if ultimas_demandas else 0.0
                    promedios[insumo_id] = round(promedio, 2)
                else:
                    promedios[insumo_id] = 0.0
            
            print(f"DEBUG OPTIMIZED: Promedios calculados para {len(promedios)} insumos")
            return promedios
            
        except Exception as e:
            print(f"DEBUG OPTIMIZED: Error calculando promedios batch: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def obtener_demanda_mes(self, insumo_id, fecha_inicio, fecha_fin):
        """
        Obtiene la demanda total de un insumo en un período específico
        aplicando filtro de nivel seleccionado con lógica de consolidación
        """
        conn = None
        cursor = None
        try:
            if insumo_id is None:
                return 0.0

            conn = conectar_db()
            if not conn:
                return 0.0

            cursor = conn.cursor(dictionary=True)

            # Obtener filtros con seguridad
            area_seleccionada = getattr(self, 'combo_area', None)
            area_seleccionada = area_seleccionada.get().strip() if area_seleccionada and area_seleccionada.get() else None

            distrito_seleccionado = getattr(self, 'combo_distrito', None)
            distrito_seleccionado = distrito_seleccionado.get().strip() if distrito_seleccionado and distrito_seleccionado.get() else None

            tipo_servicio_seleccionado = getattr(self, 'combo_tipo_servicio', None)
            tipo_servicio_seleccionado = tipo_servicio_seleccionado.get().strip() if tipo_servicio_seleccionado and tipo_servicio_seleccionado.get() else None

            servicio_seleccionado = getattr(self, 'combo_servicio', None)
            servicio_seleccionado = servicio_seleccionado.get().strip() if servicio_seleccionado and servicio_seleccionado.get() else None

            query = """
            SELECT SUM(m.cantidad) as total_demanda
            FROM movimiento m
            INNER JOIN tipo_movimiento tm ON m.tipo_movimiento_id = tm.id
            LEFT JOIN area a_directa ON m.area_id = a_directa.id
            LEFT JOIN distrito d_directa ON m.distrito_id = d_directa.id
            LEFT JOIN servicio s_directa ON m.servicio_id = s_directa.id
            LEFT JOIN tipo_servicio ts_directa ON s_directa.id_tipo_servicio = ts_directa.id
            WHERE m.insumo_id = %s
            AND m.fecha_registro BETWEEN %s AND %s
            AND tm.descripcion IN ('ENTREGADO', 'NO ENTREGADO')
            """

            params = [insumo_id, fecha_inicio.strftime('%Y-%m-%d'), fecha_fin.strftime('%Y-%m-%d')]

            if servicio_seleccionado:
                query += " AND a_directa.nombre = %s AND d_directa.nombre = %s AND s_directa.nombre = %s"
                params.extend([area_seleccionada, distrito_seleccionado, servicio_seleccionado])
            elif tipo_servicio_seleccionado:
                query += " AND a_directa.nombre = %s AND d_directa.nombre = %s AND ts_directa.descripcion = %s"
                params.extend([area_seleccionada, distrito_seleccionado, tipo_servicio_seleccionado])
            elif distrito_seleccionado:
                query += """
                AND a_directa.nombre = %s 
                AND (
                    (d_directa.nombre = %s AND s_directa.nombre IS NULL) OR
                    (s_directa.id IN (
                        SELECT s.id 
                        FROM servicio s 
                        INNER JOIN tipo_servicio ts ON s.id_tipo_servicio = ts.id 
                        INNER JOIN distrito d ON ts.id_distrito = d.id 
                        WHERE d.nombre = %s
                    ))
                )
                """
                params.extend([area_seleccionada, distrito_seleccionado, distrito_seleccionado])
            elif area_seleccionada:
                query += """
                AND (
                    (a_directa.nombre = %s AND d_directa.nombre IS NULL) OR
                    (d_directa.id IN (
                        SELECT d.id 
                        FROM distrito d 
                        INNER JOIN area a ON d.id_area = a.id 
                        WHERE a.nombre = %s
                    ) AND s_directa.nombre IS NULL) OR
                    (s_directa.id IN (
                        SELECT s.id 
                        FROM servicio s 
                        INNER JOIN tipo_servicio ts ON s.id_tipo_servicio = ts.id 
                        INNER JOIN distrito d ON ts.id_distrito = d.id 
                        INNER JOIN area a ON d.id_area = a.id 
                        WHERE a.nombre = %s
                    ))
                )
                """
                params.extend([area_seleccionada, area_seleccionada, area_seleccionada])

            cursor.execute(query, params)
            resultado = cursor.fetchone()

            total_demanda = float(resultado['total_demanda']) if resultado and resultado['total_demanda'] else 0.0
            return total_demanda

        except Exception as e:
            print(f"Error obteniendo demanda del mes: {e}")
            import traceback
            traceback.print_exc()
            return 0.0
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def calcular_promedio_periodo_actual(self, codigo_insumo, fecha_inicio, fecha_fin):
        """
        Calcula el promedio basado en los datos del período actual
        como fallback cuando no hay datos históricos suficientes
        """
        try:
            from src.database.db_manager import obtener_movimientos_historicos
            
            # Obtener movimientos del período actual
            movimientos_actuales = obtener_movimientos_historicos(
                codigo_insumo,
                fecha_inicio.strftime('%Y-%m-%d'),
                fecha_fin.strftime('%Y-%m-%d'),
                self.combo_distrito.get() if self.combo_distrito.get() else None,
                self.combo_tipo_servicio.get() if self.combo_tipo_servicio.get() else None,
                self.combo_servicio.get() if self.combo_servicio.get() else None
            )
            
            if not movimientos_actuales:
                return 0.0
            
            # Sumar demanda total del período
            demanda_total = sum(
                float(mov.get('cantidad', 0)) 
                for mov in movimientos_actuales 
                    if mov.get('tipo_movimiento') in ['ENTREGADO', 'NO ENTREGADO']
            )
            
            # Calcular número de meses en el período
            dias_periodo = (fecha_fin - fecha_inicio).days
            meses_periodo = max(1, dias_periodo / 30.44)  # Promedio de días por mes
            
            promedio = demanda_total / meses_periodo
            return round(promedio, 2)
            
        except Exception as e:
            print(f"Error calculando promedio del período actual: {e}")
            return 0.0

    def obtener_saldo_mes_anterior(self, codigo_insumo, fecha_corte):
        """
        Obtiene el saldo del mes anterior para usar como saldo anterior
        si no existe inventario inicial
        """
        try:
            from src.database.db_manager import obtener_movimientos_bres
            
            # Calcular fecha de inicio del mes anterior (3 meses atrás para tener más datos)
            fecha_mes_anterior = fecha_corte - timedelta(days=90)
            
            # Obtener todos los movimientos hasta la fecha de corte del mes anterior
            movimientos = obtener_movimientos_bres(
                fecha_mes_anterior.strftime('%Y-%m-%d'),
                (fecha_corte - timedelta(days=1)).strftime('%Y-%m-%d'),
                self.combo_distrito.get() if self.combo_distrito.get() else None,
                self.combo_tipo_servicio.get() if self.combo_tipo_servicio.get() else None,
                self.combo_servicio.get() if self.combo_servicio.get() else None
            )
            
            # Filtrar movimientos del mismo insumo
            movimientos_insumo = [
                mov for mov in movimientos 
                if mov.get('codigo_insumo') == codigo_insumo
            ]
            
            # Calcular saldo acumulado
            saldo = 0
            for mov in movimientos_insumo:
                tipo = mov.get('tipo_movimiento', '').upper()
                cantidad = float(mov.get('cantidad', 0))
                
                if tipo in ['INVENTARIO INICIAL', 'ENTRADA NIVEL SUPERIOR', 'REAJUSTE POSITIVO']:
                    saldo += cantidad
                elif tipo in ['ENTREGADO', 'SALIDA NIVEL INFERIOR', 'REAJUSTE NEGATIVO']:
                    saldo -= cantidad
                # NO ENTREGADO no afecta el saldo
            
            return saldo
            
        except Exception as e:
            print(f"Error obteniendo saldo mes anterior: {e}")
            return 0.0

    
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
                text="Reporte BRES",
                font=('Segoe UI', 12, 'bold'),
                fg=self.COLORS['white'],
                bg=self.COLORS['primary']).pack(anchor='w')

        tk.Label(title_inner,
                text="Balance, Requisición y Envío de Suministros",
                font=('Segoe UI', 8),
                fg=self.COLORS['white'],
                bg=self.COLORS['primary']).pack(anchor='w', pady=(2, 0))

        # --- Frame principal tipo tarjeta ---
        self.frame_principal_container, self.frame_principal = self.create_titled_frame(main_container, "Filtros de Reporte BRES")
        self.frame_principal_container.config(bg=self.COLORS['white'])
        self.frame_principal.config(bg=self.COLORS['white'])
        self.frame_principal_container.pack(fill="both", expand=True, padx=10, pady=5)

        # --- Frame de fechas tipo tarjeta ---
        self.frame_fechas_container, self.frame_fechas = self.create_titled_frame(self.frame_principal, "Selección de Fechas/Corte Logístico")
        self.frame_fechas_container.config(bg=self.COLORS['white'])
        self.frame_fechas.config(bg=self.COLORS['white'])
        self.frame_fechas_container.pack(fill="x", padx=5, pady=5)

        self.modo_fecha_var = tk.StringVar(value="rango")

        # --- Frame para rango de fechas ---
        self.frame_rango = tk.Frame(self.frame_fechas, bg=self.COLORS['white'])
        self.frame_rango.pack(fill="x", padx=5, pady=2)
        for i in range(5):
            self.frame_rango.grid_columnconfigure(i, weight=1)

        self.radio_rango = ttk.Radiobutton(
            self.frame_rango,
            text="Rango de Fechas:",
            variable=self.modo_fecha_var,
            value="rango",
            command=self.actualizar_visibilidad_fechas,
            style='White.TRadiobutton'
        )
        self.radio_rango.grid(row=0, column=0, padx=5, sticky='w')

        ttk.Label(self.frame_rango, text="Fecha Inicial:", style='White.TLabel').grid(row=0, column=1, padx=5, sticky='e')
        self.fecha_inicial = DateEntry(
            self.frame_rango,
            width=16,
            date_pattern='dd/mm/yyyy',
            state='normal'
        )
        self.fecha_inicial.grid(row=0, column=2, padx=5, sticky='ew')

        ttk.Label(self.frame_rango, text="Fecha Final:", style='White.TLabel').grid(row=0, column=3, padx=5, sticky='e')
        self.fecha_final = DateEntry(
            self.frame_rango,
            width=16,
            date_pattern='dd/mm/yyyy',
            state='normal'
        )
        self.fecha_final.grid(row=0, column=4, padx=5, sticky='ew')

        # --- Frame para corte logístico ---
        self.frame_corte = tk.Frame(self.frame_fechas, bg=self.COLORS['white'])
        self.frame_corte.pack(fill="x", padx=5, pady=2)

        # Igual que en Kardex
        self.frame_corte.grid_columnconfigure(2, weight=1)
        self.frame_corte.grid_columnconfigure(4, weight=1)
        self.frame_corte.grid_columnconfigure(6, weight=1)

        self.radio_corte = ttk.Radiobutton(
            self.frame_corte,
            text="Corte Logístico:",
            variable=self.modo_fecha_var,
            value="corte",
            command=self.actualizar_visibilidad_fechas,
            style='White.TRadiobutton'
        )
        self.radio_corte.grid(row=0, column=0, padx=5, sticky='w')

        ttk.Label(self.frame_corte, text="Año:", style='White.TLabel').grid(row=0, column=1, padx=5, sticky='w')
        self.anio_var = tk.StringVar()
        anios = [str(a) for a in range(datetime.now().year - 5, datetime.now().year + 2)]
        self.combo_anio = ttk.Combobox(
            self.frame_corte,
            textvariable=self.anio_var,
            values=anios,
            width=8  # Igual que en Kardex
        )
        self.combo_anio.grid(row=0, column=2, padx=5, sticky='ew')
        self.combo_anio.set(str(datetime.now().year))

        ttk.Label(self.frame_corte, text="Mes Inicio:", style='White.TLabel').grid(row=0, column=3, padx=5, sticky='w')
        self.mes_inicio_var = tk.StringVar()
        meses = [datetime(2024, m, 1).strftime("%B").capitalize() for m in range(1, 13)]
        self.combo_mes_inicio = ttk.Combobox(
            self.frame_corte,
            textvariable=self.mes_inicio_var,
            values=meses,
            width=12  # Igual que en Kardex
        )
        self.combo_mes_inicio.grid(row=0, column=4, padx=5, sticky='ew')

        ttk.Label(self.frame_corte, text="Mes Final:", style='White.TLabel').grid(row=0, column=5, padx=5, sticky='w')
        self.mes_final_var = tk.StringVar()
        self.combo_mes_final = ttk.Combobox(
            self.frame_corte,
            textvariable=self.mes_final_var,
            values=meses,
            width=12  # Igual que en Kardex
        )
        self.combo_mes_final.grid(row=0, column=6, padx=5, sticky='ew')

        self.combo_anio.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte)
        self.combo_mes_inicio.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte)
        self.combo_mes_final.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte)

        self.actualizar_visibilidad_fechas()

        # Primera fila de combos - Ubicación
        self.frame_ubicacion_container, self.frame_ubicacion = self.create_titled_frame(self.frame_principal, "Seleccione Ubicación")
        self.frame_ubicacion_container.config(bg=self.COLORS['white'])
        self.frame_ubicacion.config(bg=self.COLORS['white'])
        self.frame_ubicacion_container.pack(fill="x", padx=5, pady=5)

        self.frame_ubicacion_content = tk.Frame(self.frame_ubicacion, bg=self.COLORS['white'])
        self.frame_ubicacion_content.pack(fill="x", padx=5, pady=5)

        for i in range(8):
            self.frame_ubicacion_content.grid_columnconfigure(i, weight=1)

        ttk.Label(self.frame_ubicacion_content, text="Área:", background="white").grid(row=0, column=0, padx=5, sticky='ew')
        self.area_var = tk.StringVar()
        self.combo_area = AutocompleteCombobox(self.frame_ubicacion_content, textvariable=self.area_var, state="normal", width=20)
        self.combo_area.grid(row=0, column=1, padx=5, sticky='ew')

        ttk.Label(self.frame_ubicacion_content, text="Distrito:", background="white").grid(row=0, column=2, padx=5, sticky='ew')
        self.distrito_var = tk.StringVar()
        self.combo_distrito = AutocompleteCombobox(self.frame_ubicacion_content, textvariable=self.distrito_var, state="normal", width=20)
        self.combo_distrito.grid(row=0, column=3, padx=5, sticky='ew')

        ttk.Label(self.frame_ubicacion_content, text="Tipo de Servicio:", background="white").grid(row=0, column=4, padx=5, sticky='ew')
        self.tipo_servicio_var = tk.StringVar()
        self.combo_tipo_servicio = AutocompleteCombobox(self.frame_ubicacion_content, textvariable=self.tipo_servicio_var, state="normal", width=20)
        self.combo_tipo_servicio.grid(row=0, column=5, padx=5, sticky='ew')

        ttk.Label(self.frame_ubicacion_content, text="Servicio:", background="white").grid(row=0, column=6, padx=5, sticky='ew')
        self.servicio_var = tk.StringVar()
        self.combo_servicio = AutocompleteCombobox(self.frame_ubicacion_content, textvariable=self.servicio_var, state="normal", width=20)
        self.combo_servicio.grid(row=0, column=7, padx=5, sticky='ew')

        # Segunda fila de combos - Insumo
        self.frame_insumo_container, self.frame_insumo = self.create_titled_frame(self.frame_principal, "Seleccione Insumo")
        self.frame_insumo_container.config(bg=self.COLORS['white'])
        self.frame_insumo.config(bg=self.COLORS['white'])
        self.frame_insumo_container.pack(fill="x", padx=5, pady=5)

        self.frame_insumo_content = tk.Frame(self.frame_insumo, bg=self.COLORS['white'])
        self.frame_insumo_content.pack(fill="x", padx=5, pady=5)

        for i in range(6):
            self.frame_insumo_content.grid_columnconfigure(i, weight=1)

        ttk.Label(self.frame_insumo_content, text="Tipo de Insumo:", background="white").grid(row=0, column=0, padx=5, sticky='ew')
        self.tipo_insumo_var = tk.StringVar()
        self.combo_tipo_insumo = AutocompleteCombobox(self.frame_insumo_content, textvariable=self.tipo_insumo_var, state="normal", width=20)
        self.combo_tipo_insumo.grid(row=0, column=1, padx=5, sticky='ew')

        ttk.Label(self.frame_insumo_content, text="Insumo:", background="white").grid(row=0, column=2, padx=5, sticky='ew')
        self.insumo_var = tk.StringVar()
        self.combo_insumo = AutocompleteCombobox(self.frame_insumo_content, textvariable=self.insumo_var, state="normal", width=20)
        self.combo_insumo.grid(row=0, column=3, padx=5, sticky='ew')

        ttk.Label(self.frame_insumo_content, text="Presentación:", background="white").grid(row=0, column=4, padx=5, sticky='ew')
        self.presentacion_var = tk.StringVar()
        self.combo_presentacion = AutocompleteCombobox(self.frame_insumo_content, textvariable=self.presentacion_var, state="normal", width=20)
        self.combo_presentacion.grid(row=0, column=5, padx=5, sticky='ew')

        # Tercera fila - Nivel Máximo
        self.frame_nivel_container, self.frame_nivel = self.create_titled_frame(self.frame_principal, "Seleccione Nivel Máximo")
        self.frame_nivel_container.config(bg=self.COLORS['white'])
        self.frame_nivel.config(bg=self.COLORS['white'])
        self.frame_nivel_container.pack(fill="x", padx=5, pady=(10, 30))

        self.frame_nivel_content = tk.Frame(self.frame_nivel, bg=self.COLORS['white'])
        self.frame_nivel_content.pack(fill="x", padx=5, pady=5)

        ttk.Label(self.frame_nivel_content, text="Nivel Máximo:", background="white").grid(row=0, column=0, padx=5, sticky='w')
        self.nivel_maximo_var = tk.StringVar()
        niveles = [str(i) for i in range(1, 13)]  # 1 al 12
        self.combo_nivel_maximo = ttk.Combobox(
            self.frame_nivel_content,
            textvariable=self.nivel_maximo_var,
            values=niveles,
            width=10,
            state="readonly"
        )
        self.combo_nivel_maximo.grid(row=0, column=1, padx=5, sticky='w')
        self.combo_nivel_maximo.set("6")  # Valor por defecto

        # --- Frame para el visor PDF (ALTURA FIJA) ---
        self.pdf_frame = tk.Frame(self.frame_principal, bg=self.COLORS['white'], height=230)
        self.pdf_frame.pack(fill="x", padx=5, pady=5)
        self.pdf_frame.pack_propagate(False)  # Para que respete la altura fija
        self.pdf_viewer = None
    
        # --- Frame para botones (fuera del frame principal, pegado abajo) ---
        self.frame_botones = ttk.Frame(main_container, style='White.TFrame')
        self.frame_botones.pack(fill="x", side="bottom", pady=(20, 10))

        btn_font = ('Segoe UI', 9, 'bold')
        btn_bg = self.COLORS['white']
        btn_fg = self.COLORS['text_dark']

        # Botón Generar Reporte
        btn_report = tk.Button(self.frame_botones, 
                            text="Generar Reporte", 
                            command=self.generar_vista_previa,
                            font=btn_font, bg=btn_bg, fg=btn_fg, 
                            relief='flat', borderwidth=0,
                            highlightthickness=0, padx=15, pady=6, 
                            cursor='hand2',
                            image=self.icon_preview if self.icon_preview else "",
                            compound='left' if self.icon_preview else None)
        btn_report.pack(side="left", padx=5)

        # Botón Imprimir
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

        # Botón Exportar a PDF
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

        # Botón Exportar a Excel
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

        # Botón Cerrar - AHORA CON SIDE="RIGHT" PARA QUE VAYA AL MARGEN DERECHO
        btn_close = tk.Button(self.frame_botones, 
                            text="Cerrar", 
                            command=self.cerrar_ventana,
                            font=btn_font, bg=btn_bg, fg=btn_fg, 
                            relief='flat', borderwidth=0,
                            highlightthickness=0, padx=15, pady=6, 
                            cursor='hand2',
                            image=self.icon_close if self.icon_close else "",
                            compound='left' if self.icon_close else None)
        btn_close.pack(side="right", padx=5)  # <-- CAMBIO AQUÍ: side="right"

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

    def actualizar_visibilidad_fechas(self):
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

    # Métodos de carga de datos (iguales que en ReporteKardex)
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

    def generar_vista_previa(self):
        """
        VERSIÓN OPTIMIZADA de generar_vista_previa()
        Reemplaza la llamada a procesar_datos_bres con la versión optimizada
        """
        try:
            # ... (mismo código de validación de fechas) ...
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

                fecha_ini_str, fecha_fin_str = self.calcular_rango_corte_logistico(
                    anio, mes_inicio, mes_final
                )
                fecha_ini = datetime.strptime(fecha_ini_str, '%d/%m/%Y')
                fecha_fin = datetime.strptime(fecha_fin_str, '%d/%m/%Y')

            if fecha_fin < fecha_ini:
                messagebox.showerror("Error", "La fecha final debe ser mayor a la inicial")
                return

            print("DEBUG OPTIMIZED: Iniciando obtención de movimientos...")
            
            # Obtener datos usando la función específica para BRES
            movimientos_raw = obtener_movimientos_bres(
                fecha_ini.strftime('%Y-%m-%d'),
                fecha_fin.strftime('%Y-%m-%d'),
                area_nombre=self.combo_area.get().strip() or None,
                distrito_nombre=self.combo_distrito.get().strip() or None,
                tipo_servicio_desc=self.combo_tipo_servicio.get().strip() or None,
                servicio_nombre=self.combo_servicio.get().strip() or None,
                tipo_insumo_desc=self.combo_tipo_insumo.get().strip() or None,
                insumo_nombre=self.combo_insumo.get().strip() or None,
                presentacion_nombre=self.combo_presentacion.get().strip() or None
            )

            print(f"DEBUG OPTIMIZED: Movimientos obtenidos: {len(movimientos_raw) if movimientos_raw else 0}")
            
            if not movimientos_raw:
                messagebox.showinfo("Info", "No hay datos para mostrar")
                return

            print("DEBUG OPTIMIZED: Iniciando procesamiento optimizado...")
            
            # USAR MÉTODO OPTIMIZADO
            self.movimientos_data = self.procesar_datos_bres(movimientos_raw, fecha_ini, fecha_fin)

            if not self.movimientos_data:
                messagebox.showwarning("Sin datos", "No hay datos procesados para mostrar")
                return

            print(f"DEBUG OPTIMIZED: Procesamiento completado. {len(self.movimientos_data)} registros procesados")


            # Generar PDF temporal
            import tempfile
            temp_dir = tempfile.gettempdir()
            self.temp_pdf_path = os.path.join(temp_dir, "vista_previa_bres.pdf")

            # Generar el PDF en el archivo temporal
            self.generar_pdf(self.temp_pdf_path, es_vista_previa=True)

            # Limpiar el frame PDF si existe
            for widget in self.pdf_frame.winfo_children():
                widget.destroy()

            contenedor = tk.Frame(self.pdf_frame, bg=self.COLORS['white'])
            contenedor.pack(fill="both", expand=True)

            # --- Frame para controles de navegación (abajo, fondo blanco) ---
            control_frame = tk.Frame(contenedor, bg=self.COLORS['white'])
            control_frame.pack(fill="x", side="bottom", pady=5)

            # --- Frame del visor PDF (canvas + scrollbars) ---
            canvas_frame = tk.Frame(contenedor, bg=self.COLORS['white'])
            canvas_frame.pack(side="top", fill="both", expand=True)

            h_scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal")
            h_scrollbar.pack(side="bottom", fill="x")

            v_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical")
            v_scrollbar.pack(side="right", fill="y")

            canvas = tk.Canvas(
                canvas_frame,
                xscrollcommand=h_scrollbar.set,
                yscrollcommand=v_scrollbar.set,
                bg=self.COLORS['white'],
                highlightthickness=0
            )
            canvas.pack(side="left", fill="both", expand=True)

            h_scrollbar.config(command=canvas.xview)
            v_scrollbar.config(command=canvas.yview)

            # Abrir el PDF con PyMuPDF
            doc = fitz.open(self.temp_pdf_path)
            self.current_page = 0
            self.total_pages = len(doc)
            self.zoom_level = 1.5  # Zoom inicial

            # --- Función para mostrar página centrada ---
            def display_page():
                canvas.delete("all")
                page = doc.load_page(self.current_page)
                pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom_level, self.zoom_level))
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                tk_img = ImageTk.PhotoImage(image=img)
                canvas.image = tk_img

                # Calcular posición para centrar la imagen en el canvas
                canvas_width = canvas.winfo_width()
                canvas_height = canvas.winfo_height()
                x = max((canvas_width - pix.width) // 2, 0)
                y = max((canvas_height - pix.height) // 2, 0)

                canvas.create_image(x, y, anchor="nw", image=tk_img)
                canvas.config(scrollregion=canvas.bbox("all"))

            # --- Función para cambiar página ---
            def change_page(delta):
                self.current_page = max(0, min(self.current_page + delta, self.total_pages - 1))
                display_page()
                page_label.config(text=f"Página {self.current_page + 1} de {self.total_pages}")

            # --- Función para cambiar zoom ---
            def change_zoom(delta):
                self.zoom_level = max(0.5, min(self.zoom_level + delta, 3.0))
                display_page()
                zoom_label.config(text=f"Zoom: {int(self.zoom_level * 100)}%")

            # --- Ajustar al ancho ---
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

            # --- Ajustar a página completa ---
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

            # --- Función para maximizar reporte con ajuste y centrado ---
            def maximizar_reporte():
                try:
                    ventana_max = tk.Toplevel(self.parent)
                    ventana_max.title("Reporte BRES - Vista Maximizada")
                    ventana_max.configure(bg=self.COLORS['white'])
                    ventana_max.state('zoomed')  # Maximizar ventana (Windows)
                    ventana_max.resizable(True, True)

                    main_frame = tk.Frame(ventana_max, bg=self.COLORS['white'])
                    main_frame.pack(fill="both", expand=True)

                    # Frame controles superiores
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

                    # Frame canvas maximizado
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
                    zoom_level_max = [1.0]  # Inicial, se ajustará

                    def display_page_max():
                        canvas_max.delete("all")
                        page = doc.load_page(current_page_max[0])
                        pix = page.get_pixmap(matrix=fitz.Matrix(zoom_level_max[0], zoom_level_max[0]))
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        tk_img = ImageTk.PhotoImage(image=img)
                        canvas_max.image = tk_img

                        # Centrar imagen en canvas maximizado
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

                    # Botones navegación maximizada
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

                    # Botones zoom maximizada
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

                    # Mostrar primera página y ajustar a ventana
                    def on_resize(event=None):
                        fit_to_page_max()

                    ventana_max.bind("<Configure>", on_resize)

                    display_page_max()

                    # Scroll con mouse maximizado
                    def on_mousewheel_max(event):
                        if canvas_max.winfo_exists():
                            canvas_max.yview_scroll(int(-1*(event.delta/120)), "units")
                    canvas_max.bind("<MouseWheel>", on_mousewheel_max)

                    ventana_max.focus_force()
                    ventana_max.grab_set()

                except Exception as e:
                    messagebox.showerror("Error", f"Error al maximizar reporte: {str(e)}")

            # --- Botones y controles en visor normal ---

            btn_nav_prev = tk.Button(
                control_frame, text="◀", command=lambda: change_page(-1),
                bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                font=('Segoe UI', 10, 'bold'), relief='flat', borderwidth=0, cursor='hand2',
                activebackground=self.COLORS['white'], activeforeground=self.COLORS['text_dark']
            )
            btn_nav_prev.pack(side="left", padx=(10, 2), pady=2)

            page_label = tk.Label(
                control_frame, text=f"Página 1 de {self.total_pages}",
                bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                font=('Segoe UI', 10, 'bold')
            )
            page_label.pack(side="left", padx=2, pady=2)

            btn_nav_next = tk.Button(
                control_frame, text="▶", command=lambda: change_page(1),
                bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                font=('Segoe UI', 10, 'bold'), relief='flat', borderwidth=0, cursor='hand2',
                activebackground=self.COLORS['white'], activeforeground=self.COLORS['text_dark']
            )
            btn_nav_next.pack(side="left", padx=2, pady=2)

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

            # Mostrar primera página
            display_page()

            # Scroll con mouse
            def on_mousewheel(event):
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            canvas.bind("<MouseWheel>", on_mousewheel)

        except Exception as e:
            import traceback
            error_detallado = traceback.format_exc()
            print(f"Error detallado:\n{error_detallado}")
            messagebox.showerror("Error", f"Error al generar reporte:\n{str(e)}")
        
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
            
    def mostrar_pdf(self, pdf_path):
        """Muestra el PDF generado en una nueva ventana"""
        try:
            import subprocess
            import platform
            
            # Abrir PDF según el sistema operativo
            if platform.system() == 'Windows':
                subprocess.run(['start', pdf_path], shell=True, check=True)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', pdf_path], check=True)
            else:  # Linux
                subprocess.run(['xdg-open', pdf_path], check=True)
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el PDF: {str(e)}")
            print(f"Error al abrir PDF: {e}")

    def imprimir_pdf(self):
        try:
            import os
            import sys
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

            # Generar nombre de archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"Reporte_BRES_{timestamp}.pdf"

            # Ruta a la carpeta Descargas
            downloads_path = os.path.expanduser("~/Downloads")
            full_path = os.path.join(downloads_path, file_name)

            # Generar el PDF
            self.generar_pdf(full_path, es_vista_previa=False)

            # Preguntar si desea abrir el PDF
            if messagebox.askyesno("PDF Generado", "PDF guardado exitosamente.\n¿Desea abrirlo ahora?"):
                import sys
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

            # Estilos personalizados
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                alignment=1,
                spaceAfter=15,
                fontSize=12
            )
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading2'],
                alignment=1,
                spaceAfter=10,
                fontSize=10
            )
            timestamp_style = ParagraphStyle(
                'TimestampStyle',
                parent=styles['Normal'],
                alignment=1,
                spaceAfter=15,
                fontSize=9
            )

            # Títulos principales
            elements.append(Paragraph(
                "DIRECCIÓN DEPARTAMENTAL DE REDES INTEGRADAS DE SERVICIOS DE SALUD DE GUATEMALA,",
                title_style))
            elements.append(Paragraph("ÁREA NOR ORIENTE", subtitle_style))
            elements.append(Paragraph("BALANCE, REQUISICIÓN Y ENVÍO DE SUMINISTROS", subtitle_style))
            elements.append(Paragraph(
                f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                timestamp_style))

            # Filtros
            filtros = [
                f"Área: {self.combo_area.get()}",
                f"Distrito: {self.combo_distrito.get()}",
                f"Tipo de Servicio: {self.combo_tipo_servicio.get()}",
                f"Servicio: {self.combo_servicio.get()}",
                f"Tipo de Insumo: {self.combo_tipo_insumo.get()}",
                f"Nivel Máximo: {self.combo_nivel_maximo.get()}"
            ]

            # Crear estilo para alineación izquierda
            left_style = ParagraphStyle(
                name="LeftAlign",
                alignment=0,
                fontSize=9,
                fontName='Helvetica'
            )

            # Crear tabla con filtros
            data_filtros = [[Paragraph(item, left_style) for item in filtros]]
            col_widths = [125, 125, 125, 125, 125, 125]

            table_filtros = Table(data_filtros, colWidths=col_widths)
            table_filtros.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey)
            ]))

            elements.append(table_filtros)
            elements.append(Spacer(1, 30))

            # **ENCABEZADOS MEJORADOS SIN PRESENTACIÓN**
            headers = [
                'Código',
                'Descripción\ndel Insumo',
                'Saldo\nAnterior',
                'Entradas\nNivel\nSuperior',
                'Entregado\na Usuario',
                'No\nEntregado',
                'Demanda',
                'Reajustes\n(+) (-)',
                'Saldo Mes\nSiguiente',
                'Existencia\nFísica',
                'Promedio\nMensual\nDemanda Real',
                'Meses\nExistencia\nDisponible',
                'Cantidad\nMáxima',
                'Cantidad a\nSolicitar'
            ]

            # Datos de la tabla (SIN PRESENTACIÓN)
            data = [headers]
            
            for mov in self.movimientos_data:
                row = [
                    mov.get('codigo_insumo', ''),
                    self.dividir_texto_en_lineas(mov.get('nombre_insumo', ''), 30),
                    mov.get('saldo_anterior', ''),
                    mov.get('entradas_nivel_superior', ''),
                    mov.get('entregado_usuario', ''),
                    mov.get('no_entregado', ''),
                    mov.get('demanda', ''),
                    mov.get('reajustes', ''),
                    mov.get('saldo_mes_siguiente', ''),
                    mov.get('existencia_fisica', ''),
                    mov.get('promedio_mensual', ''),
                    mov.get('meses_existencia', ''),
                    mov.get('cantidad_maxima', ''),
                    mov.get('cantidad_solicitar', '')
                ]
                data.append(row)

            # Crear tabla con anchos ajustados (SIN PRESENTACIÓN)
            colWidths = [
                0.7*inch,   # Código
                3.0*inch,   # Descripción del Insumo (más ancho sin presentación)
                0.8*inch,   # Saldo Anterior
                0.8*inch,   # Entradas Nivel Superior
                0.8*inch,   # Entregado a Usuario
                0.8*inch,   # No Entregado
                0.8*inch,   # Demanda
                0.8*inch,   # Reajustes (+) (-)
                0.8*inch,   # Saldo Mes Siguiente
                0.8*inch,   # Existencia Física
                0.9*inch,   # Promedio Mensual Demanda Real
                0.9*inch,   # Meses Existencia Disponible
                0.8*inch,   # Cantidad Máxima
                0.8*inch    # Cantidad a Solicitar
            ]

            table = Table(data, colWidths=colWidths, repeatRows=1)
            
            # **ESTILO MEJORADO CON ALTURA DE FILA AJUSTADA**
            table_style = [
                ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
                ('TEXTCOLOR', (0,0), (-1,0), colors.black),
                # **CENTRADO HORIZONTAL Y VERTICAL PARA TODA LA TABLA**
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 7),
                ('FONTSIZE', (0,1), (-1,-1), 7),
                ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
                ('ROWBACKGROUNDS', (0,0), (-1,0), [colors.lightblue]),
                # **PADDING AUMENTADO PARA MEJOR APARIENCIA**
                ('TOPPADDING', (0,0), (-1,0), 8),      # Encabezados
                ('BOTTOMPADDING', (0,0), (-1,0), 8),   # Encabezados
                ('TOPPADDING', (0,1), (-1,-1), 6),     # Celdas de datos
                ('BOTTOMPADDING', (0,1), (-1,-1), 6),  # Celdas de datos
                ('LEFTPADDING', (0,0), (-1,-1), 4),    # Todas las celdas
                ('RIGHTPADDING', (0,0), (-1,-1), 4),   # Todas las celdas
                ('WORDWRAP', (0,0), (-1,-1), True),    # Permitir salto de línea
            ]

            table.setStyle(TableStyle(table_style))
            elements.append(table)

            doc.build(elements)

            if not es_vista_previa:
                messagebox.showinfo("Éxito", f"PDF guardado en:\n{ruta_pdf}")

        except Exception as e:
            messagebox.showerror("Error", f"Error al generar PDF: {str(e)}")

    def generar_excel_reporte(self):
        try:
            if not self.movimientos_data:
                messagebox.showerror("Error", "Primero debe generar el reporte")
                return

            import os
            filas_por_hoja = 1000
            total_movimientos = len(self.movimientos_data)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"Reporte_BRES_{timestamp}.xlsx"
            downloads_path = os.path.expanduser("~/Downloads")
            full_path = os.path.join(downloads_path, file_name)

            with pd.ExcelWriter(full_path, engine='xlsxwriter') as writer:
                workbook = writer.book

                columnas = [
                    'codigo_insumo', 'nombre_insumo', 'saldo_anterior', 'entradas_nivel_superior',
                    'entregado_usuario', 'no_entregado', 'demanda', 'reajustes',
                    'saldo_mes_siguiente', 'existencia_fisica', 'promedio_mensual',
                    'meses_existencia', 'cantidad_maxima', 'cantidad_solicitar'
                ]
                encabezados = [
                    'Código', 'Descripción\ndel Insumo', 'Saldo\nAnterior', 'Entradas\nNivel\nSuperior',
                    'Entregado\na Usuario', 'No\nEntregado', 'Demanda', 'Reajustes\n(+) (-)',
                    'Saldo Mes\nSiguiente', 'Existencia\nFísica', 'Promedio\nMensual\nDemanda Real',
                    'Meses\nExistencia\nDisponible', 'Cantidad\nMáxima', 'Cantidad a\nSolicitar'
                ]
                col_widths = [10, 30, 10, 12, 12, 10, 10, 12, 12, 12, 18, 18, 12, 12]

                for hoja_num in range(0, total_movimientos, filas_por_hoja):
                    nombre_hoja = f"BRES_{hoja_num // filas_por_hoja + 1}"
                    fin_hoja = min(hoja_num + filas_por_hoja, total_movimientos)
                    datos_hoja = self.movimientos_data[hoja_num:fin_hoja]

                    df = pd.DataFrame(datos_hoja)[columnas]
                    df.columns = encabezados

                    fila_inicio = 8

                    df.to_excel(writer, sheet_name=nombre_hoja, startrow=fila_inicio, index=False, header=False)

                    worksheet = writer.sheets[nombre_hoja]

                    title_format = workbook.add_format({
                        'bold': True,
                        'align': 'center',
                        'valign': 'vcenter',
                        'font_size': 12,
                        'font_name': 'Segoe UI'
                    })
                    subtitle_format = workbook.add_format({
                        'bold': True,
                        'align': 'center',
                        'valign': 'vcenter',
                        'font_size': 10,
                        'font_name': 'Segoe UI'
                    })
                    header_format = workbook.add_format({
                        'bold': True,
                        'align': 'center',
                        'valign': 'vcenter',
                        'font_size': 9,
                        'bg_color': '#ADD8E6',
                        'font_color': 'black',
                        'border': 1,
                        'text_wrap': True,
                        'font_name': 'Segoe UI'
                    })
                    filtro_format = workbook.add_format({
                        'bold': True,
                        'align': 'center',
                        'valign': 'vcenter',
                        'font_size': 9,
                        'text_wrap': True,
                        'font_name': 'Segoe UI',
                        'fg_color': 'white',
                    })
                    cell_format_center = workbook.add_format({
                        'align': 'center',
                        'valign': 'vcenter',
                        'font_size': 9,
                        'border': 1,
                        'font_name': 'Segoe UI'
                    })
                    cell_format_wrap = workbook.add_format({
                        'align': 'left',
                        'valign': 'top',
                        'text_wrap': True,
                        'font_size': 9,
                        'border': 1,
                        'font_name': 'Segoe UI'
                    })
                    cell_format_number = workbook.add_format({
                        'num_format': '#,##0.00',
                        'align': 'right',
                        'valign': 'vcenter',
                        'font_size': 9,
                        'border': 1,
                        'font_name': 'Segoe UI'
                    })

                    # Altura filas títulos y subtítulos (moderada)
                    worksheet.set_row(0, 30)
                    worksheet.set_row(1, 25)
                    worksheet.set_row(2, 25)
                    worksheet.set_row(3, 20)

                    # Altura fila encabezados de tabla aumentada para mejor visibilidad
                    worksheet.set_row(fila_inicio - 1, 60)

                    # Altura fila filtros
                    worksheet.set_row(5, 25)

                    worksheet.merge_range(0, 0, 0, len(encabezados) - 1,
                                        "DIRECCIÓN DEPARTAMENTAL DE REDES INTEGRADAS DE SERVICIOS DE SALUD DE GUATEMALA,",
                                        title_format)
                    worksheet.merge_range(1, 0, 1, len(encabezados) - 1,
                                        "ÁREA NOR ORIENTE",
                                        subtitle_format)
                    worksheet.merge_range(2, 0, 2, len(encabezados) - 1,
                                        "BALANCE, REQUISICIÓN Y ENVÍO DE SUMINISTROS",
                                        subtitle_format)
                    worksheet.merge_range(3, 0, 3, len(encabezados) - 1,
                                        f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                                        subtitle_format)

                    worksheet.merge_range(5, 0, 5, 1, f"Área: {self.combo_area.get()}", filtro_format)
                    worksheet.merge_range(5, 2, 5, 3, f"Distrito: {self.combo_distrito.get()}", filtro_format)
                    worksheet.merge_range(5, 4, 5, 5, f"Tipo de Servicio: {self.combo_tipo_servicio.get()}", filtro_format)
                    worksheet.merge_range(5, 6, 5, 7, f"Servicio: {self.combo_servicio.get()}", filtro_format)
                    worksheet.merge_range(5, 8, 5, 9, f"Tipo de Insumo: {self.combo_tipo_insumo.get()}", filtro_format)
                    worksheet.merge_range(5, 10, 5, 13, f"Nivel Máximo: {self.combo_nivel_maximo.get()}", filtro_format)

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
                import sys
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
    
    def filtrar_movimientos_por_nivel(self, movimientos):
        if not movimientos:
            return []

        area_seleccionada = self.combo_area.get().strip()
        distrito_seleccionado = self.combo_distrito.get().strip()
        tipo_servicio_seleccionado = self.combo_tipo_servicio.get().strip()
        servicio_seleccionado = self.combo_servicio.get().strip()

        movimientos_filtrados = []

        for mov in movimientos:
            area_mov = mov.get('area_nombre')
            distrito_mov = mov.get('distrito_nombre')
            tipo_servicio_mov = mov.get('tipo_servicio_desc')
            servicio_mov = mov.get('servicio_nombre')

            incluir = False

            if servicio_seleccionado:
                if (area_mov == area_seleccionada and
                    distrito_mov == distrito_seleccionado and
                    tipo_servicio_mov == tipo_servicio_seleccionado and
                    servicio_mov == servicio_seleccionado):
                    incluir = True

            elif tipo_servicio_seleccionado:
                if (area_mov == area_seleccionada and
                    distrito_mov == distrito_seleccionado and
                    tipo_servicio_mov == tipo_servicio_seleccionado):
                    incluir = True

            elif distrito_seleccionado:
                if (area_mov == area_seleccionada and
                    distrito_mov == distrito_seleccionado):
                    incluir = True

            elif area_seleccionada:
                if area_mov == area_seleccionada:
                    incluir = True

            else:
                incluir = True

            if incluir:
                movimientos_filtrados.append(mov)

        return movimientos_filtrados
    
    def destroy(self):
        if hasattr(self, 'frame_principal'):
            self.frame_principal.destroy()