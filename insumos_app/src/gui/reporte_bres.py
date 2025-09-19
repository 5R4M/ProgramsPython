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
            return f"{num:.2f}"
        except (ValueError, TypeError):
            return "0.00"

    def __init__(self, parent_frame, main_window=None):
        self.parent = parent_frame
        self.main_window = main_window
        self.cargar_iconos()
        self.movimientos_data = None

        # Paleta local (solo variables, no estilos globales)
        self.COLORS = {
            'primary':   '#2c3e50',
            'accent':    '#3498db',
            'danger':    '#e74c3c',
            'white':     '#ffffff',
            'light':     '#f7f7f7',
            'text_dark': '#2c3e50'
        }

        self.areas = []
        self.distritos = []
        self.tipos_servicio = []
        self.tipos_insumo = []
        self.insumos = []
        self.presentaciones = []

        self.setup_ui()

    def create_titled_frame(self, parent, title):
        # Contenedor con encabezado local (sin estilos globales)
        container = tk.Frame(parent, bg=self.COLORS['white'], relief='solid', bd=1)

        header = tk.Frame(container, bg=self.COLORS['primary'], height=26)
        header.pack(fill='x')
        header.pack_propagate(False)

        label = tk.Label(header, text=title, font=('Segoe UI', 9, 'bold'),
                         fg=self.COLORS['white'], bg=self.COLORS['primary'])
        label.pack(side='left', padx=10, pady=2)

        content = tk.Frame(container, bg=self.COLORS['white'])
        content.pack(fill='both', expand=True, padx=10, pady=10)

        return container, content

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

    def generar_codigo_insumo(self, movimientos_raw):
        """
        Genera códigos únicos basados en posición relativa dentro de cada tipo (no afecta UI).
        """
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

            insumos_por_tipo = {}
            for resultado in resultados_principales:
                insumo_id = resultado['insumo_id']
                tipo_id = resultado['tipo_id']
                tipo_descripcion = (resultado['tipo_insumo_descripcion'] or '').strip().upper()

                if tipo_id not in insumos_por_tipo:
                    insumos_por_tipo[tipo_id] = {
                        'descripcion': tipo_descripcion,
                        'insumos': []
                    }
                insumos_por_tipo[tipo_id]['insumos'].append(insumo_id)

            codigos_insumos = {}
            for tipo_id, info_tipo in insumos_por_tipo.items():
                tipo_descripcion = info_tipo['descripcion']
                insumos_del_reporte = info_tipo['insumos']

                cursor.execute("""
                    SELECT i.id as insumo_id
                    FROM insumo i
                    WHERE i.id_tipo_insumo = %s
                    ORDER BY i.id ASC
                """, (tipo_id,))
                todos_insumos_tipo = cursor.fetchall()

                posicion_relativa = {}
                for indice, insumo in enumerate(todos_insumos_tipo, 1):
                    posicion_relativa[insumo['insumo_id']] = indice

                tipo_limpio = ''.join(c for c in tipo_descripcion if c.isalnum())
                prefijo = (tipo_limpio[:4] if len(tipo_limpio) >= 4 else (tipo_limpio + 'XXXX')[:4]).upper()

                for insumo_id in insumos_del_reporte:
                    if insumo_id in posicion_relativa:
                        posicion = posicion_relativa[insumo_id]
                        codigo = f"{prefijo}-{posicion:04d}"
                        codigos_insumos[insumo_id] = codigo

            conn.close()
            return codigos_insumos

        except Exception as e:
            print(f"DEBUG OPTIMIZED: Error: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def procesar_datos_bres(self, movimientos_raw, fecha_ini, fecha_fin):
        """
        Lógica de datos (no toca estilos).
        """
        for m in movimientos_raw:
            if 'tipo_servicio_desc' in m and 'tipo_servicio_descripcion' not in m:
                m['tipo_servicio_descripcion'] = m['tipo_servicio_desc']

        codigos_insumos = self.generar_codigo_insumo(movimientos_raw)
        if not codigos_insumos:
            return []

        datos_agrupados = {}

        nivel_area = self.combo_area.get().strip()
        nivel_distrito = self.combo_distrito.get().strip()
        nivel_tipo_servicio = self.combo_tipo_servicio.get().strip()
        nivel_servicio = self.combo_servicio.get().strip()

        for mov in movimientos_raw:
            insumo_id = mov.get('codigo_insumo')
            if insumo_id is None or str(insumo_id).strip() == '':
                continue

            codigo = codigos_insumos.get(insumo_id, f"TEMP-{str(insumo_id).zfill(4)}")
            nombre = mov.get('nombre_insumo', '')
            area = mov.get('area_nombre', '')
            distrito = mov.get('distrito_nombre', '')
            tipo_servicio = mov.get('tipo_servicio_descripcion', '')
            servicio = mov.get('servicio_nombre', '')
            tipo_movimiento = str(mov.get('tipo_movimiento', '')).upper()

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

        insumo_ids = [datos['insumo_id'] for datos in datos_agrupados.values() if datos['insumo_id'] is not None]
        promedios_batch = self.calcular_promedio_demanda_real(insumo_ids, fecha_ini, fecha_fin)

        datos_procesados = []

        for codigo, datos in datos_agrupados.items():
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

            promedio_mensual = promedios_batch.get(datos['insumo_id'], 0.0)
            meses_existencia = saldo_mes_siguiente / promedio_mensual if promedio_mensual > 0 else 0
            try:
                nivel_maximo = float(self.nivel_maximo_var.get()) if self.nivel_maximo_var.get() else 6
            except Exception:
                nivel_maximo = 6
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
        if not insumo_ids:
            return {}
        try:
            conn = conectar_db()
            if not conn:
                return {}
            cursor = conn.cursor(dictionary=True)

            fecha_inicio_calculo = fecha_fin - timedelta(days=90)

            area_sel = self.combo_area.get().strip() or None
            distrito_sel = self.combo_distrito.get().strip() or None
            tipo_serv_sel = self.combo_tipo_servicio.get().strip() or None
            servicio_sel = self.combo_servicio.get().strip() or None

            placeholders = ','.join(['%s'] * len(insumo_ids))
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

            if servicio_sel:
                query += " AND a_directa.nombre = %s AND d_directa.nombre = %s AND s_directa.nombre = %s"
                params.extend([area_sel, distrito_sel, servicio_sel])
            elif tipo_serv_sel:
                query += " AND a_directa.nombre = %s AND d_directa.nombre = %s AND ts_directa.descripcion = %s"
                params.extend([area_sel, distrito_sel, tipo_serv_sel])
            elif distrito_sel:
                query += " AND a_directa.nombre = %s AND (d_directa.nombre = %s OR s_directa.id IN (SELECT s.id FROM servicio s INNER JOIN tipo_servicio ts ON s.id_tipo_servicio = ts.id INNER JOIN distrito d ON ts.id_distrito = d.id WHERE d.nombre = %s))"
                params.extend([area_sel, distrito_sel, distrito_sel])
            elif area_sel:
                query += " AND (a_directa.nombre = %s OR d_directa.id IN (SELECT d.id FROM distrito d INNER JOIN area a ON d.id_area = a.id WHERE a.nombre = %s) OR s_directa.id IN (SELECT s.id FROM servicio s INNER JOIN tipo_servicio ts ON s.id_tipo_servicio = ts.id INNER JOIN distrito d ON ts.id_distrito = d.id INNER JOIN area a ON d.id_area = a.id WHERE a.nombre = %s))"
                params.extend([area_sel, area_sel, area_sel])

            query += " GROUP BY m.insumo_id, YEAR(m.fecha_registro), MONTH(m.fecha_registro)"
            cursor.execute(query, params)
            resultados = cursor.fetchall()
            conn.close()

            demandas_por_insumo = {}
            for r in resultados:
                ins = r['insumo_id']
                val = float(r['demanda_mes']) if r['demanda_mes'] else 0.0
                demandas_por_insumo.setdefault(ins, []).append(val)

            promedios = {}
            for ins in insumo_ids:
                if ins in demandas_por_insumo:
                    arr = demandas_por_insumo[ins]
                    ult = arr[-3:] if len(arr) >= 3 else arr
                    prom = sum(ult) / len(ult) if ult else 0.0
                    promedios[ins] = round(prom, 2)
                else:
                    promedios[ins] = 0.0
            return promedios
        except Exception as e:
            print(f"DEBUG OPTIMIZED: Error calculando promedios batch: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def obtener_demanda_mes(self, insumo_id, fecha_inicio, fecha_fin):
        conn = None
        cursor = None
        try:
            if insumo_id is None:
                return 0.0

            conn = conectar_db()
            if not conn:
                return 0.0

            cursor = conn.cursor(dictionary=True)

            area_sel = self.combo_area.get().strip() or None
            distrito_sel = self.combo_distrito.get().strip() or None
            tipo_serv_sel = self.combo_tipo_servicio.get().strip() or None
            servicio_sel = self.combo_servicio.get().strip() or None

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

            if servicio_sel:
                query += " AND a_directa.nombre = %s AND d_directa.nombre = %s AND s_directa.nombre = %s"
                params.extend([area_sel, distrito_sel, servicio_sel])
            elif tipo_serv_sel:
                query += " AND a_directa.nombre = %s AND d_directa.nombre = %s AND ts_directa.descripcion = %s"
                params.extend([area_sel, distrito_sel, tipo_serv_sel])
            elif distrito_sel:
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
                params.extend([area_sel, distrito_sel, distrito_sel])
            elif area_sel:
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
                params.extend([area_sel, area_sel, area_sel])

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
        try:
            from src.database.db_manager import obtener_movimientos_historicos
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

            demanda_total = sum(
                float(mov.get('cantidad', 0))
                for mov in movimientos_actuales
                if mov.get('tipo_movimiento') in ['ENTREGADO', 'NO ENTREGADO']
            )
            dias_periodo = (fecha_fin - fecha_inicio).days
            meses_periodo = max(1, dias_periodo / 30.44)
            promedio = demanda_total / meses_periodo
            return round(promedio, 2)
        except Exception as e:
            print(f"Error calculando promedio del período actual: {e}")
            return 0.0

    def obtener_saldo_mes_anterior(self, codigo_insumo, fecha_corte):
        try:
            fecha_mes_anterior = fecha_corte - timedelta(days=90)
            movimientos = obtener_movimientos_bres(
                fecha_mes_anterior.strftime('%Y-%m-%d'),
                (fecha_corte - timedelta(days=1)).strftime('%Y-%m-%d'),
                self.combo_area.get().strip() or None,
                self.combo_distrito.get().strip() or None,
                self.combo_tipo_servicio.get().strip() or None,
                self.combo_servicio.get().strip() or None,
                self.combo_tipo_insumo.get().strip() or None,
                self.combo_insumo.get().strip() or None,
                self.combo_presentacion.get().strip() or None
            )

            movimientos_insumo = [mov for mov in movimientos if mov.get('codigo_insumo') == codigo_insumo]
            saldo = 0
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

    def setup_ui(self):
        # Contenedor principal local, sin tocar estilos globales
        self.main_container = tk.Frame(self.parent, bg=self.COLORS['white'])
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

        tk.Label(title_inner,
                 text="📊 Reporte BRES",
                 font=('Segoe UI', 12, 'bold'),
                 fg=self.COLORS['white'],
                 bg=self.COLORS['primary']).pack(anchor='w')

        tk.Label(title_inner,
                 text="Balance, Requisición y Envío de Suministros",
                 font=('Segoe UI', 8),
                 fg=self.COLORS['white'],
                 bg=self.COLORS['primary']).pack(anchor='w', pady=(2, 0))

        # Sección Fechas
        self.frame_fechas_container, self.frame_fechas = self.create_titled_frame(
            self.main_container, "📅 Selección de Fechas/Corte Logístico"
        )
        self.frame_fechas_container.pack(fill="x", padx=5, pady=5)

        self.modo_fecha_var = tk.StringVar(value="rango")

        # Rango
        self.frame_rango = tk.Frame(self.frame_fechas, bg=self.COLORS['white'])
        self.frame_rango.pack(fill="x", padx=5, pady=2)
        for i in range(5):
            self.frame_rango.grid_columnconfigure(i, weight=1)

        ttk.Radiobutton(
            self.frame_rango,
            text="Rango de Fechas:",
            variable=self.modo_fecha_var,
            value="rango",
            command=self.actualizar_visibilidad_fechas,
        ).grid(row=0, column=0, padx=5, sticky='w')

        ttk.Label(self.frame_rango, text="Fecha Inicial:") \
            .grid(row=0, column=1, padx=5, sticky='e')
        self.fecha_inicial = DateEntry(self.frame_rango, width=16, date_pattern='dd/mm/yyyy', state='normal')
        self.fecha_inicial.grid(row=0, column=2, padx=5, sticky='ew')

        ttk.Label(self.frame_rango, text="Fecha Final:") \
            .grid(row=0, column=3, padx=5, sticky='e')
        self.fecha_final = DateEntry(self.frame_rango, width=16, date_pattern='dd/mm/yyyy', state='normal')
        self.fecha_final.grid(row=0, column=4, padx=5, sticky='ew')

        # Corte
        self.frame_corte = tk.Frame(self.frame_fechas, bg=self.COLORS['white'])
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
        ).grid(row=0, column=0, padx=5, sticky='w')

        ttk.Label(self.frame_corte, text="Año:") \
            .grid(row=0, column=1, padx=5, sticky='w')
        self.anio_var = tk.StringVar()
        anios = [str(a) for a in range(datetime.now().year - 5, datetime.now().year + 2)]
        self.combo_anio = ttk.Combobox(self.frame_corte, textvariable=self.anio_var, values=anios, width=8, state="readonly")
        self.combo_anio.grid(row=0, column=2, padx=5, sticky='ew')
        self.combo_anio.set(str(datetime.now().year))

        ttk.Label(self.frame_corte, text="Mes Inicio:") \
            .grid(row=0, column=3, padx=5, sticky='w')
        self.mes_inicio_var = tk.StringVar()
        meses = [datetime(2024, m, 1).strftime("%B").capitalize() for m in range(1, 13)]
        self.combo_mes_inicio = ttk.Combobox(self.frame_corte, textvariable=self.mes_inicio_var, values=meses, width=12, state="readonly")
        self.combo_mes_inicio.grid(row=0, column=4, padx=5, sticky='ew')

        ttk.Label(self.frame_corte, text="Mes Final:") \
            .grid(row=0, column=5, padx=5, sticky='w')
        self.mes_final_var = tk.StringVar()
        self.combo_mes_final = ttk.Combobox(self.frame_corte, textvariable=self.mes_final_var, values=meses, width=12, state="readonly")
        self.combo_mes_final.grid(row=0, column=6, padx=5, sticky='ew')

        self.combo_anio.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte)
        self.combo_mes_inicio.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte)
        self.combo_mes_final.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte)

        self.actualizar_visibilidad_fechas()

        # Ubicación
        self.frame_ubicacion_container, frame_ubicacion_content = self.create_titled_frame(self.main_container, "📍 Ubicación")
        self.frame_ubicacion_container.pack(fill="x", padx=5, pady=5)

        frame_ubicacion_content.grid_columnconfigure(1, weight=1)
        frame_ubicacion_content.grid_columnconfigure(3, weight=1)
        frame_ubicacion_content.grid_columnconfigure(5, weight=1)
        frame_ubicacion_content.grid_columnconfigure(7, weight=1)

        ttk.Label(frame_ubicacion_content, text="Área:").grid(row=0, column=0, padx=5, sticky='w')
        self.area_var = tk.StringVar()
        self.combo_area = AutocompleteCombobox(frame_ubicacion_content, textvariable=self.area_var, state="normal", font=('Segoe UI', 9))
        self.combo_area.grid(row=0, column=1, padx=5, sticky='ew')

        ttk.Label(frame_ubicacion_content, text="Distrito:").grid(row=0, column=2, padx=5, sticky='w')
        self.distrito_var = tk.StringVar()
        self.combo_distrito = AutocompleteCombobox(frame_ubicacion_content, textvariable=self.distrito_var, state="normal", font=('Segoe UI', 9))
        self.combo_distrito.grid(row=0, column=3, padx=5, sticky='ew')

        ttk.Label(frame_ubicacion_content, text="Tipo de Servicio:").grid(row=0, column=4, padx=5, sticky='w')
        self.tipo_servicio_var = tk.StringVar()
        self.combo_tipo_servicio = AutocompleteCombobox(frame_ubicacion_content, textvariable=self.tipo_servicio_var, state="normal", font=('Segoe UI', 9))
        self.combo_tipo_servicio.grid(row=0, column=5, padx=5, sticky='ew')

        ttk.Label(frame_ubicacion_content, text="Servicio:").grid(row=0, column=6, padx=5, sticky='w')
        self.servicio_var = tk.StringVar()
        self.combo_servicio = AutocompleteCombobox(frame_ubicacion_content, textvariable=self.servicio_var, state="normal", font=('Segoe UI', 9))
        self.combo_servicio.grid(row=0, column=7, padx=5, sticky='ew')

        # Insumo
        self.frame_insumo_container, frame_insumo_content = self.create_titled_frame(self.main_container, "💊 Insumo")
        self.frame_insumo_container.pack(fill="x", padx=5, pady=5)

        frame_insumo_content.grid_columnconfigure(1, weight=1)
        frame_insumo_content.grid_columnconfigure(3, weight=1)
        frame_insumo_content.grid_columnconfigure(5, weight=1)

        ttk.Label(frame_insumo_content, text="Tipo de Insumo:").grid(row=0, column=0, padx=5, sticky='w')
        self.tipo_insumo_var = tk.StringVar()
        self.combo_tipo_insumo = AutocompleteCombobox(frame_insumo_content, textvariable=self.tipo_insumo_var, state="normal", font=('Segoe UI', 9))
        self.combo_tipo_insumo.grid(row=0, column=1, padx=5, sticky='ew')

        ttk.Label(frame_insumo_content, text="Insumo:").grid(row=0, column=2, padx=5, sticky='w')
        self.insumo_var = tk.StringVar()
        self.combo_insumo = AutocompleteCombobox(frame_insumo_content, textvariable=self.insumo_var, state="normal", font=('Segoe UI', 9))
        self.combo_insumo.grid(row=0, column=3, padx=5, sticky='ew')

        ttk.Label(frame_insumo_content, text="Presentación:").grid(row=0, column=4, padx=5, sticky='w')
        self.presentacion_var = tk.StringVar()
        self.combo_presentacion = AutocompleteCombobox(frame_insumo_content, textvariable=self.presentacion_var, state="normal", font=('Segoe UI', 9))
        self.combo_presentacion.grid(row=0, column=5, padx=5, sticky='ew')

        # Nivel Máximo
        self.frame_nivel_container, frame_nivel_content = self.create_titled_frame(self.main_container, "📈 Nivel Máximo")
        self.frame_nivel_container.pack(fill="x", padx=5, pady=(10, 10))

        ttk.Label(frame_nivel_content, text="Nivel Máximo:").grid(row=0, column=0, padx=5, sticky='w')
        self.nivel_maximo_var = tk.StringVar()
        niveles = [str(i) for i in range(1, 13)]
        self.combo_nivel_maximo = ttk.Combobox(frame_nivel_content, textvariable=self.nivel_maximo_var, values=niveles, width=10, state="readonly")
        self.combo_nivel_maximo.grid(row=0, column=1, padx=5, sticky='w')
        self.combo_nivel_maximo.set("6")

        # Visor PDF
        self.pdf_outer = tk.Frame(self.main_container, bg=self.COLORS['white'])
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

        # Botones inferiores (tk.Button locales)
        self.frame_botones = tk.Frame(self.main_container, bg=self.COLORS['white'])
        self.frame_botones.pack(fill="x", side="bottom", pady=(20, 10))

        btn_font = ('Segoe UI', 9, 'bold')
        btn_bg = self.COLORS['white']
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

    # Métodos de carga de datos
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
        try:
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

            if not movimientos_raw:
                messagebox.showinfo("Info", "No hay datos para mostrar")
                return

            self.movimientos_data = self.procesar_datos_bres(movimientos_raw, fecha_ini, fecha_fin)
            if not self.movimientos_data:
                messagebox.showwarning("Sin datos", "No hay datos procesados para mostrar")
                return

            import tempfile
            temp_dir = tempfile.gettempdir()
            self.temp_pdf_path = os.path.join(temp_dir, "vista_previa_bres.pdf")
            self.generar_pdf(self.temp_pdf_path, es_vista_previa=True)

            for w in self.pdf_body.winfo_children():
                w.destroy()

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
                               xscrollcommand=h_scrollbar.set)
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
                zoom_label.config(text=f"Zoom: {int(self.zoom_level * 100)}%")

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
                    ventana_max.title("Reporte BRES - Vista Maximizada")
                    ventana_max.configure(bg=self.COLORS['white'])
                    try:
                        ventana_max.state('zoomed')
                    except Exception:
                        ventana_max.attributes('-zoomed', True)
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
            elements.append(Paragraph("BALANCE, REQUISICIÓN Y ENVÍO DE SUMINISTROS", subtitle_style))
            elements.append(Paragraph(f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", timestamp_style))

            left_style = ParagraphStyle(name="LeftAlign", alignment=0, fontSize=9, fontName='Helvetica')
            filtros = [
                f"Área: {self.combo_area.get()}",
                f"Distrito: {self.combo_distrito.get()}",
                f"Tipo de Servicio: {self.combo_tipo_servicio.get()}",
                f"Servicio: {self.combo_servicio.get()}",
                f"Tipo de Insumo: {self.combo_tipo_insumo.get()}",
                f"Nivel Máximo: {self.combo_nivel_maximo.get()}"
            ]
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
            elements.append(Spacer(1, 24))

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

            colWidths = [
                0.7*inch,
                3.0*inch,
                0.8*inch,
                0.8*inch,
                0.8*inch,
                0.8*inch,
                0.8*inch,
                0.8*inch,
                0.8*inch,
                0.8*inch,
                0.9*inch,
                0.9*inch,
                0.8*inch,
                0.8*inch
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

                    worksheet.set_row(0, 30)
                    worksheet.set_row(1, 25)
                    worksheet.set_row(2, 25)
                    worksheet.set_row(3, 20)
                    worksheet.set_row(fila_inicio - 1, 60)
                    worksheet.set_row(5, 25)

                    worksheet.merge_range(0, 0, 0, len(encabezados) - 1,
                        "DIRECCIÓN DEPARTAMENTAL DE REDES INTEGRADAS DE SERVICIOS DE SALUD DE GUATEMALA,", title_format)
                    worksheet.merge_range(1, 0, 1, len(encabezados) - 1, "ÁREA NOR ORIENTE", subtitle_format)
                    worksheet.merge_range(2, 0, 2, len(encabezados) - 1, "BALANCE, REQUISICIÓN Y ENVÍO DE SUMINISTROS", subtitle_format)
                    worksheet.merge_range(3, 0, 3, len(encabezados) - 1, f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", subtitle_format)

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
            if len((linea_actual + " " + palabra).strip()) > max_caracteres_por_linea:
                if linea_actual:
                    lineas.append(linea_actual.strip())
                linea_actual = palabra
            else:
                linea_actual = (linea_actual + " " + palabra).strip() if linea_actual else palabra
        if linea_actual:
            lineas.append(linea_actual.strip())
        if len(lineas) > 3:
            lineas = lineas[:2] + [lineas[2][:max_caracteres_por_linea-3] + "..."]
        return "\n".join(lineas)

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
            tipo_servicio_mov = mov.get('tipo_servicio_descripcion')
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
        try:
            if hasattr(self, 'main_container') and self.main_container:
                self.main_container.destroy()
        except Exception:
            pass