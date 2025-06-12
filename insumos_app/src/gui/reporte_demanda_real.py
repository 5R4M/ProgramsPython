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
    obtener_movimientos_kardex,
    obtener_id_area,
    obtener_id_distrito,
    obtener_id_tipo_servicio,
    obtener_id_tipo_insumo
)

class ReporteDemandaReal:
    def __init__(self, parent_frame, main_window=None):
        self.parent = parent_frame
        self.main_window = main_window
        self.movimientos_data = None

        # Crear estilos para los frames (ya no se necesitan los estilos Enabled/Disabled)
        style = ttk.Style()
        
        self.areas = []
        self.distritos = []       
        self.tipos_servicio = []  
        self.tipos_insumo = []
        self.insumos = []
        self.presentaciones = []
    
        self.setup_ui()

    def setup_ui(self):
        # Frame principal - USAR PACK PARA TODO
        self.frame_principal = ttk.LabelFrame(self.parent, text="Filtros de Reporte Demanda Real")
        self.frame_principal.pack(fill="both", expand=True, padx=10, pady=5)

        # Frame para corte logístico - UNA SOLA LÍNEA
        self.frame_corte_logistico = ttk.LabelFrame(self.frame_principal, text="Corte Logístico")
        self.frame_corte_logistico.pack(fill="x", padx=5, pady=5)
        
        self.frame_corte = ttk.Frame(self.frame_corte_logistico)
        self.frame_corte.pack(fill="x", padx=5, pady=5)

        # Una sola fila - Año, Mes Inicio y Mes Final
        ttk.Label(self.frame_corte, text="Año:").grid(row=0, column=0, padx=5, sticky='w')
        self.anio_var = tk.StringVar()
        anios = [str(a) for a in range(datetime.now().year - 5, datetime.now().year + 2)]
        self.combo_anio = ttk.Combobox(
            self.frame_corte,
            textvariable=self.anio_var,
            values=anios,
            width=8,
            state="readonly"
        )
        self.combo_anio.grid(row=0, column=1, padx=5)
        self.combo_anio.set(str(datetime.now().year))

        ttk.Label(self.frame_corte, text="Mes Inicio:").grid(row=0, column=2, padx=5, sticky='w')
        self.mes_inicio_var = tk.StringVar()
        
        # Obtener nombres de meses en español
        meses = [datetime(2024, m, 1).strftime("%B").capitalize() for m in range(1, 13)]
        
        self.combo_mes_inicio = ttk.Combobox(
            self.frame_corte,
            textvariable=self.mes_inicio_var,
            values=meses,
            width=12,
            state="readonly"
        )
        self.combo_mes_inicio.grid(row=0, column=3, padx=5)
        self.combo_mes_inicio.set(datetime.now().strftime("%B").capitalize())

        ttk.Label(self.frame_corte, text="Mes Final:").grid(row=0, column=4, padx=5, sticky='w')
        self.mes_final_var = tk.StringVar()
        
        self.combo_mes_final = ttk.Combobox(
            self.frame_corte,
            textvariable=self.mes_final_var,
            values=meses,
            width=12,
            state="readonly"
        )
        self.combo_mes_final.grid(row=0, column=5, padx=5)
        self.combo_mes_final.set(datetime.now().strftime("%B").capitalize())

        # Eventos para actualizar fechas
        self.combo_anio.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte)
        self.combo_mes_inicio.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte)
        self.combo_mes_final.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte)

        # Frame para combos
        self.frame_combos = ttk.Frame(self.frame_principal)
        self.frame_combos.pack(fill="x", padx=5, pady=5)
        
        # Frame para Ubicación - UNA SOLA LÍNEA
        self.frame_ubicacion = ttk.LabelFrame(self.frame_principal, text="Ubicación")
        self.frame_ubicacion.pack(fill="x", padx=5, pady=5)

        self.frame_ubicacion_content = ttk.Frame(self.frame_ubicacion)
        self.frame_ubicacion_content.pack(fill="x", padx=5, pady=5)
        
        # Una sola fila - Área, Distrito, Tipo de Servicio y Servicio
        ttk.Label(self.frame_ubicacion_content, text="Área:").grid(row=0, column=0, padx=5, sticky='w')
        self.area_var = tk.StringVar()
        self.combo_area = AutocompleteCombobox(self.frame_ubicacion_content, textvariable=self.area_var, state="normal", width=20)
        self.combo_area.grid(row=0, column=1, padx=5, sticky='w')
        
        ttk.Label(self.frame_ubicacion_content, text="Distrito:").grid(row=0, column=2, padx=5, sticky='w')
        self.distrito_var = tk.StringVar()
        self.combo_distrito = AutocompleteCombobox(self.frame_ubicacion_content, textvariable=self.distrito_var, state="normal", width=20)
        self.combo_distrito.grid(row=0, column=3, padx=5, sticky='w')

        ttk.Label(self.frame_ubicacion_content, text="Tipo de Servicio:").grid(row=0, column=4, padx=5, sticky='w')
        self.tipo_servicio_var = tk.StringVar()
        self.combo_tipo_servicio = AutocompleteCombobox(self.frame_ubicacion_content, textvariable=self.tipo_servicio_var, state="normal", width=20)
        self.combo_tipo_servicio.grid(row=0, column=5, padx=5, sticky='w')
        
        ttk.Label(self.frame_ubicacion_content, text="Servicio:").grid(row=0, column=6, padx=5, sticky='w')
        self.servicio_var = tk.StringVar()
        self.combo_servicio = AutocompleteCombobox(self.frame_ubicacion_content, textvariable=self.servicio_var, state="normal", width=20)
        self.combo_servicio.grid(row=0, column=7, padx=5, sticky='w')

        # Frame para Insumos - UNA SOLA LÍNEA
        self.frame_insumos = ttk.LabelFrame(self.frame_principal, text="Insumo")
        self.frame_insumos.pack(fill="x", padx=5, pady=5)

        self.frame_insumos_content = ttk.Frame(self.frame_insumos)
        self.frame_insumos_content.pack(fill="x", padx=5, pady=5)
        
        # Una sola fila - Tipo de Insumo, Insumo y Presentación
        ttk.Label(self.frame_insumos_content, text="Tipo de Insumo:").grid(row=0, column=0, padx=5, sticky='w')
        self.tipo_insumo_var = tk.StringVar()
        self.combo_tipo_insumo = AutocompleteCombobox(self.frame_insumos_content, textvariable=self.tipo_insumo_var, state="normal", width=20)
        self.combo_tipo_insumo.grid(row=0, column=1, padx=5, sticky='w')
        
        ttk.Label(self.frame_insumos_content, text="Insumo:").grid(row=0, column=2, padx=5, sticky='w')
        self.insumo_var = tk.StringVar()
        self.combo_insumo = AutocompleteCombobox(self.frame_insumos_content, textvariable=self.insumo_var, state="normal", width=25)
        self.combo_insumo.grid(row=0, column=3, padx=5, sticky='w')
        
        ttk.Label(self.frame_insumos_content, text="Presentación:").grid(row=0, column=4, padx=5, sticky='w')
        self.presentacion_var = tk.StringVar()
        self.combo_presentacion = AutocompleteCombobox(self.frame_insumos_content, textvariable=self.presentacion_var, state="readonly", width=20)
        self.combo_presentacion.grid(row=0, column=5, padx=5, sticky='w')

        # Frame para el visor PDF
        self.pdf_frame = ttk.Frame(self.frame_principal)
        self.pdf_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.pdf_viewer = None

        # Frame para botones
        self.frame_botones = ttk.Frame(self.frame_principal)
        self.frame_botones.pack(fill="x", pady=10)

        botones_grid = ttk.Frame(self.frame_botones)
        botones_grid.pack()

        ttk.Button(botones_grid, text="Generar Vista Previa", command=self.generar_reporte).grid(row=0, column=0, padx=5)
        ttk.Button(botones_grid, text="Imprimir", command=self.imprimir_pdf).grid(row=0, column=1, padx=5)
        ttk.Button(botones_grid, text="Exportar a PDF", command=self.exportar_pdf).grid(row=0, column=2, padx=5)
        ttk.Button(botones_grid, text="Exportar a Excel", command=self.exportar_excel).grid(row=0, column=3, padx=5)
        ttk.Button(botones_grid, text="Cerrar", command=self.cerrar_ventana).grid(row=0, column=4, padx=5)

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
                    'entregado': {dia: 0 for dia in dias},  # Usar el parámetro dias
                    'no_entregado': {dia: 0 for dia in dias},  # Usar el parámetro dias
                    'inventario_inicial': 0,
                    'entrada_nivel_superior': 0,
                    'salida_nivel_inferior': 0,
                    'reajuste_positivo': 0,
                    'reajuste_negativo': 0
                }
            
            # Usar get() para obtener valores de manera segura
            fecha_str = mov.get('fecha', '')
            if not fecha_str:
                continue  # Saltar si no hay fecha
                
            try:
                fecha_mov = datetime.strptime(fecha_str, '%Y-%m-%d')
            except ValueError:
                continue  # Saltar si la fecha no es válida
                
            dia = fecha_mov.day
            cantidad = mov.get('cantidad', 0)
            tipo_mov = mov.get('tipo_movimiento', '')
            
            if tipo_mov == 'ENTREGADO' and dia in dias:  # Usar el parámetro dias
                insumos[insumo_key]['entregado'][dia] += cantidad
            elif tipo_mov == 'NO ENTREGADO' and dia in dias:  # Usar el parámetro dias
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
        
        # Resto del código permanece igual...
        datos_procesados = {}
        for insumo_key, valores in insumos.items():
            fila_datos = {
                'codigo': valores['codigo'],
                'nombre_insumo': valores['nombre_insumo'],
                'presentacion': valores['presentacion']
            }
            
            # Agregar días
            for dia in dias:  # Usar el parámetro dias
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
            
            datos_procesados[insumo_key] = fila_datos
        
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
                'font_name': 'Arial',
                'border': 1,
                'border_color': '#D3D3D3'
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
                'valign': 'vcenter',
                'font_size': 8,
                'font_name': 'Arial',
                'border': 1,
                'border_color': 'black'
            })

            text_format = workbook.add_format({
                'align': 'left',
                'valign': 'vcenter',
                'font_size': 8,
                'font_name': 'Arial',
                'border': 1,
                'border_color': 'black'
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
            # IMPORTANTE: usar fila_encabezado_1-1 y fila_encabezado_2-1 porque merge_range usa índices 0-based
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

            # Procesar datos de insumos
            for insumo_key, valores in self.datos.items():
                # Extraer información del insumo - CORREGIDO
                if ' - ' in insumo_key:
                    partes = insumo_key.split(' - ', 1)
                    codigo = partes[0]
                    nombre_presentacion = partes[1]
                else:
                    # Si no hay separador, usar toda la cadena como nombre y código vacío
                    codigo = ''
                    nombre_presentacion = insumo_key

                # Calcular totales
                total_entregado = valores.get('Total_Entregado', 0)
                total_no_entregado = valores.get('Total_No_Entregado', 0)
                demanda = valores.get('Demanda', 0)
                existencia = valores.get('Existencia', 0)
                reajuste = valores.get('Reajuste', 0)

                # FILA ENTREGADO
                # Combinar celdas verticalmente para código y nombre
                worksheet.merge_range(fila_actual, 0, fila_actual+1, 0, codigo, data_format)  # Código
                worksheet.merge_range(fila_actual, 1, fila_actual+1, 1, nombre_presentacion, text_format)  # Nombre

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

            # CONFIGURACIÓN DE COLUMNAS
            worksheet.set_column('A:A', 8)   # Código
            worksheet.set_column('B:B', 25)  # Medicamento
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

        # Agrupar datos por insumo (codigo, nombre+presentacion)
        insumos = {}
        for mov in datos_movimientos:
            codigo = mov.get('codigo', '')
            nombre = mov.get('nombre_insumo', '')
            presentacion = mov.get('presentacion', '')
            key = (codigo, f"{nombre} {presentacion}".strip())
            
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

        for (codigo, nombre_pres), valores in insumos.items():
            # Calcular totales de entregado y no entregado
            total_entregado = sum(valores['entregado'].get(d, 0) for d in dias)
            total_no_entregado = sum(valores['no_entregado'].get(d, 0) for d in dias)
            
            # Calcular reajuste total (positivo - negativo)
            reajuste_total = valores['reajuste_positivo'] - valores['reajuste_negativo']
            
            # Calcular existencia según la fórmula:
            # Inventario inicial + Entrada nivel superior + Reajuste positivo - Salida nivel inferior - Entregado - Reajuste negativo
            existencia = (valores['inventario_inicial'] + 
                        valores['entrada_nivel_superior'] + 
                        valores['reajuste_positivo'] - 
                        valores['salida_nivel_inferior'] - 
                        total_entregado - 
                        valores['reajuste_negativo'])

            # Fila Entregado
            fila_entregado = [
                codigo,              # Código
                nombre_pres,         # Medicamento
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

        # Anchos de columna
        col_widths = [0.5*inch, 1.5*inch, 0.8*inch] + [0.3*inch] * len(dias) + [0.5*inch, 0.5*inch, 0.5*inch, 0.5*inch, 0.7*inch]

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

        # AHORA SÍ llamar a procesar_datos con self.dias ya definido
        datos_movimientos = self.procesar_datos(movimientos_filtrados, fecha_ini, fecha_fin, self.dias)

        # Crear self.datos con la estructura necesaria para Excel
        self.datos = {}
        insumos = {}
        
        # Agrupar datos por insumo
        for mov in movimientos_filtrados:  # Usar movimientos_filtrados en lugar de datos_movimientos
            codigo = mov.get('codigo', '')
            nombre = mov.get('nombre_insumo', '')
            presentacion = mov.get('nombre_presentacion', '')  # Usar nombre_presentacion
            key = f"{codigo} - {nombre} {presentacion}".strip()
            
            if key not in insumos:
                insumos[key] = {
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

        # Convertir a formato para Excel
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
            
            self.datos[insumo_key] = fila_datos

        periodo_str = f"{fecha_ini.strftime('%d%m%Y')}_{fecha_fin.strftime('%d%m%Y')}"
        self.periodo_str = periodo_str

        import tempfile
        temp_dir = tempfile.gettempdir()
        self.temp_pdf_path = os.path.join(temp_dir, f"vista_previa_demanda_real_{periodo_str}.pdf")
        self.generar_pdf(movimientos_filtrados, self.temp_pdf_path)  # Usar movimientos_filtrados

        self.generar_vista_previa_pdf()

    def generar_vista_previa_pdf(self):
        try:
            # Limpiar frame pdf si ya existe
            for widget in self.pdf_frame.winfo_children():
                widget.destroy()

            # Crear frame contenedor con tamaño fijo para el canvas
            canvas_container = ttk.Frame(self.pdf_frame)
            canvas_container.pack(fill="both", expand=True)

            # Crear canvas
            canvas = tk.Canvas(canvas_container, bg='white')
            canvas.pack(side="left", fill="both", expand=True)

            # Scrollbars
            v_scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)
            v_scrollbar.pack(side="right", fill="y")
            h_scrollbar = ttk.Scrollbar(self.pdf_frame, orient="horizontal", command=canvas.xview)
            h_scrollbar.pack(fill="x")

            canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

            # Abrir PDF con PyMuPDF
            doc = fitz.open(self.temp_pdf_path)
            self.current_page = 0
            self.total_pages = len(doc)

            # Frame para controles de página
            control_frame = ttk.Frame(self.pdf_frame)
            control_frame.pack(fill="x", pady=5)

            def change_page(delta):
                self.current_page = max(0, min(self.current_page + delta, self.total_pages - 1))
                display_page()
                page_label.config(text=f"Página {self.current_page + 1} de {self.total_pages}")

            ttk.Button(control_frame, text="<<", command=lambda: change_page(-1)).pack(side="left", padx=5)
            page_label = ttk.Label(control_frame, text=f"Página 1 de {self.total_pages}")
            page_label.pack(side="left", padx=10)
            ttk.Button(control_frame, text=">>", command=lambda: change_page(1)).pack(side="left", padx=5)

            def display_page():
                canvas.delete("all")
                page = doc.load_page(self.current_page)
                pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))  # Ajusta zoom si quieres
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                tk_img = ImageTk.PhotoImage(img)
                canvas.image = tk_img  # evitar GC
                canvas.create_image(0, 0, anchor="nw", image=tk_img)
                # Configurar scrollregion al tamaño de la imagen
                canvas.config(scrollregion=(0, 0, pix.width, pix.height))

            display_page()

        except Exception as e:
            messagebox.showerror("Error", f"Error al mostrar vista previa PDF: {str(e)}")
    
    def cerrar_ventana(self):
        if hasattr(self, 'temp_pdf_path') and self.temp_pdf_path and os.path.exists(self.temp_pdf_path):
            try:
                os.remove(self.temp_pdf_path)
            except:
                pass

        if self.main_window:
            self.main_window.destroy()
        else:
            self.parent.destroy()
    
    def destroy(self):
        if hasattr(self, 'frame_principal'):
            self.frame_principal.destroy()