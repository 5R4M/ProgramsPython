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
    obtener_areas,
    obtener_distritos,
    obtener_tipos_servicio_por_distrito,
    obtener_servicios_por_tipo,
    obtener_tipos_insumo,
    obtener_insumos_por_tipo,
    obtener_presentaciones,
    obtener_movimientos_kardex,
    obtener_movimientos_bres
)

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
            if num == 0:
                return ""  # Retornar cadena vacía si es 0
            return f"{num:.2f}"
        except (ValueError, TypeError):
            return ""
    
    def __init__(self, parent_frame, main_window=None):
        self.parent = parent_frame
        self.main_window = main_window
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

    def procesar_datos_bres(self, movimientos_raw, fecha_ini, fecha_fin):
        """
        Procesa los datos para generar el reporte BRES
        """
        # Agrupar movimientos por insumo
        insumos_dict = {}
        
        for mov in movimientos_raw:
            codigo_insumo = mov.get('codigo_insumo', '')
            nombre_insumo = mov.get('nombre_insumo', '')
            tipo_movimiento = mov.get('tipo_movimiento', '').upper()
            
            # Buscar la cantidad
            cantidad = 0
            posibles_campos_cantidad = [
                'cantidad', 'cantidad_movimiento', 'cantidad_entrada', 'cantidad_salida',
                'qty', 'quantity', 'cant', 'cantidades', 'valor_cantidad'
            ]

            for campo in posibles_campos_cantidad:
                if campo in mov and mov[campo] is not None:
                    try:
                        cantidad = float(mov[campo])
                        break
                    except (ValueError, TypeError):
                        continue

            # Inicializar insumo si no existe
            if codigo_insumo not in insumos_dict:
                insumos_dict[codigo_insumo] = {
                    'codigo_insumo': codigo_insumo,
                    'nombre_insumo': nombre_insumo,
                    'saldo_anterior': 0,
                    'entradas_nivel_superior': 0,
                    'entregado_usuario': 0,
                    'no_entregado': 0,
                    'reajuste_positivo': 0,
                    'reajuste_negativo': 0,
                    'movimientos_historicos': []  # Para calcular promedio
                }

            # Clasificar movimientos
            if tipo_movimiento == 'INVENTARIO INICIAL':
                insumos_dict[codigo_insumo]['saldo_anterior'] += cantidad
            elif tipo_movimiento == 'ENTRADA NIVEL SUPERIOR':
                insumos_dict[codigo_insumo]['entradas_nivel_superior'] += cantidad
            elif tipo_movimiento == 'ENTREGADO':
                insumos_dict[codigo_insumo]['entregado_usuario'] += cantidad
            elif tipo_movimiento == 'NO ENTREGADO':
                insumos_dict[codigo_insumo]['no_entregado'] += cantidad
            elif tipo_movimiento == 'REAJUSTE POSITIVO':
                insumos_dict[codigo_insumo]['reajuste_positivo'] += cantidad
            elif tipo_movimiento == 'REAJUSTE NEGATIVO':
                insumos_dict[codigo_insumo]['reajuste_negativo'] += cantidad

        # Obtener datos históricos para promedio (últimos 3 meses)
        fecha_inicio_historico = fecha_ini - timedelta(days=90)  # Aproximadamente 3 meses
        
        # Procesar cada insumo
        datos_procesados = []
        
        for codigo, datos in insumos_dict.items():
            # Calcular demanda
            demanda = datos['entregado_usuario'] + datos['no_entregado']
            
            # Calcular reajustes netos
            reajustes_netos = datos['reajuste_positivo'] - datos['reajuste_negativo']
            
            # Calcular saldo mes siguiente
            saldo_mes_siguiente = (
                datos['saldo_anterior'] + 
                datos['entradas_nivel_superior'] - 
                datos['entregado_usuario'] + 
                reajustes_netos
            )
            
            # Existencia física (mismo que saldo mes siguiente por ahora)
            existencia_fisica = saldo_mes_siguiente
            
            # Obtener promedio mensual (aquí necesitarías implementar la lógica para obtener datos históricos)
            promedio_mensual = self.calcular_promedio_mensual(codigo, fecha_inicio_historico, fecha_fin)
            
            # Meses de existencia disponible
            meses_existencia = 0
            if promedio_mensual > 0:
                meses_existencia = existencia_fisica / promedio_mensual
            
            # Cantidad máxima (usando nivel máximo seleccionado)
            nivel_maximo = float(self.nivel_maximo_var.get()) if self.nivel_maximo_var.get() else 6
            cantidad_maxima = promedio_mensual * nivel_maximo
            
            # Cantidad a solicitar
            cantidad_solicitar = max(0, cantidad_maxima - existencia_fisica)
            
            datos_procesados.append({
                'codigo_insumo': codigo,
                'nombre_insumo': datos['nombre_insumo'],
                'saldo_anterior': self.formato_float(datos['saldo_anterior']),
                'entradas_nivel_superior': self.formato_float(datos['entradas_nivel_superior']),
                'entregado_usuario': self.formato_float(datos['entregado_usuario']),
                'no_entregado': self.formato_float(datos['no_entregado']),
                'demanda': self.formato_float(demanda),
                'reajustes': f"+{self.formato_float(datos['reajuste_positivo'])} -{self.formato_float(datos['reajuste_negativo'])}" if datos['reajuste_positivo'] > 0 or datos['reajuste_negativo'] > 0 else "",
                'saldo_mes_siguiente': self.formato_float(saldo_mes_siguiente),
                'existencia_fisica': self.formato_float(existencia_fisica),
                'promedio_mensual': self.formato_float(promedio_mensual),
                'meses_existencia': self.formato_float(meses_existencia),
                'cantidad_maxima': self.formato_float(cantidad_maxima),
                'cantidad_solicitar': self.formato_float(cantidad_solicitar)
            })
        
        return datos_procesados

    def calcular_promedio_mensual(self, codigo_insumo, fecha_inicio, fecha_fin):
        """
        Calcula el promedio mensual de demanda real para un insumo
        basado en los últimos 3 meses de datos históricos
        """
        try:
            # Importar las funciones de db_manager
            from src.database.db_manager import obtener_demanda_por_meses
            
            # Calcular fecha de inicio para los últimos 3 meses
            fecha_inicio_historico = fecha_inicio - timedelta(days=90)  # Aproximadamente 3 meses atrás
            
            # Obtener demanda por meses
            demanda_mensual = obtener_demanda_por_meses(
                codigo_insumo,
                fecha_inicio_historico.strftime('%Y-%m-%d'),
                fecha_fin.strftime('%Y-%m-%d'),
                self.combo_distrito.get() if self.combo_distrito.get() else None,
                self.combo_tipo_servicio.get() if self.combo_tipo_servicio.get() else None,
                self.combo_servicio.get() if self.combo_servicio.get() else None
            )
            
            if not demanda_mensual:
                # Si no hay datos históricos, intentar calcular con datos actuales
                return self.calcular_promedio_periodo_actual(codigo_insumo, fecha_inicio, fecha_fin)
            
            # Calcular promedio de los meses disponibles
            total_demanda = sum(mes['demanda_total'] for mes in demanda_mensual)
            num_meses = len(demanda_mensual)
            
            if num_meses == 0:
                return 0.0
            
            promedio = total_demanda / num_meses
            
            # Si tenemos menos de 3 meses de datos, ajustar el cálculo
            if num_meses < 3:
                # Complementar con datos del período actual si es necesario
                promedio_actual = self.calcular_promedio_periodo_actual(codigo_insumo, fecha_inicio, fecha_fin)
                # Hacer un promedio ponderado
                if promedio_actual > 0:
                    promedio = (promedio * num_meses + promedio_actual) / (num_meses + 1)
            
            return round(promedio, 2)
            
        except Exception as e:
            print(f"Error calculando promedio mensual para {codigo_insumo}: {e}")
            # En caso de error, intentar calcular con datos del período actual
            return self.calcular_promedio_periodo_actual(codigo_insumo, fecha_inicio, fecha_fin)

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
        # Frame principal - USAR PACK PARA TODO
        self.frame_principal = ttk.LabelFrame(self.parent, text="Filtros de Reporte BRES")
        self.frame_principal.pack(fill="both", expand=True, padx=10, pady=5)

        # Frame para fechas
        self.frame_fechas = ttk.LabelFrame(self.frame_principal, text="Selección de Fechas/Corte Logístico")
        self.frame_fechas.pack(fill="x", padx=5, pady=5)
        
        # Modo de selección de fechas
        self.modo_fecha_var = tk.StringVar(value="rango")

        # Frame para rango de fechas
        self.frame_rango = ttk.Frame(self.frame_fechas)
        self.frame_rango.pack(fill="x", padx=5, pady=2)

        # Radiobutton y controles para rango de fechas
        self.radio_rango = ttk.Radiobutton(
            self.frame_rango,
            text="Rango de Fechas:",
            variable=self.modo_fecha_var,
            value="rango",
            command=self.actualizar_visibilidad_fechas
        )
        self.radio_rango.grid(row=0, column=0, padx=5, sticky='w')

        ttk.Label(self.frame_rango, text="Fecha Inicial:").grid(row=0, column=1, padx=5)
        self.fecha_inicial = DateEntry(
            self.frame_rango,
            width=12,
            date_pattern='dd/mm/yyyy',
            state='normal'
        )
        self.fecha_inicial.grid(row=0, column=2, padx=5)

        ttk.Label(self.frame_rango, text="Fecha Final:").grid(row=0, column=3, padx=5)
        self.fecha_final = DateEntry(
            self.frame_rango,
            width=12,
            date_pattern='dd/mm/yyyy',
            state='normal'
        )
        self.fecha_final.grid(row=0, column=4, padx=5)

        # Frame para corte logístico
        self.frame_corte = ttk.Frame(self.frame_fechas)
        self.frame_corte.pack(fill="x", padx=5, pady=2)

        # Radiobutton y controles para corte logístico
        self.radio_corte = ttk.Radiobutton(
            self.frame_corte,
            text="Corte Logístico:",
            variable=self.modo_fecha_var,
            value="corte",
            command=self.actualizar_visibilidad_fechas
        )
        self.radio_corte.grid(row=0, column=0, padx=5, sticky='w')

        # Año
        ttk.Label(self.frame_corte, text="Año:").grid(row=0, column=1, padx=5)
        self.anio_var = tk.StringVar()
        anios = [str(a) for a in range(datetime.now().year - 5, datetime.now().year + 2)]
        self.combo_anio = ttk.Combobox(
            self.frame_corte,
            textvariable=self.anio_var,
            values=anios,
            width=8
        )
        self.combo_anio.grid(row=0, column=2, padx=5)
        self.combo_anio.set(str(datetime.now().year))

        # Mes inicio
        ttk.Label(self.frame_corte, text="Mes Inicio:").grid(row=0, column=3, padx=5)
        self.mes_inicio_var = tk.StringVar()
        meses = [datetime(2024, m, 1).strftime("%B").capitalize() for m in range(1, 13)]
        self.combo_mes_inicio = ttk.Combobox(
            self.frame_corte,
            textvariable=self.mes_inicio_var,
            values=meses,
            width=12
        )
        self.combo_mes_inicio.grid(row=0, column=4, padx=5)

        # Mes final
        ttk.Label(self.frame_corte, text="Mes Final:").grid(row=0, column=5, padx=5)
        self.mes_final_var = tk.StringVar()
        self.combo_mes_final = ttk.Combobox(
            self.frame_corte,
            textvariable=self.mes_final_var,
            values=meses,
            width=12
        )
        self.combo_mes_final.grid(row=0, column=6, padx=5)

        # Eventos para actualizar fechas
        self.combo_anio.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte)
        self.combo_mes_inicio.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte)
        self.combo_mes_final.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte)
        
        # Frame para combos
        self.frame_combos = ttk.Frame(self.frame_principal)
        self.frame_combos.pack(fill="x", padx=5, pady=5)

        # Inicializar visibilidad
        self.actualizar_visibilidad_fechas()

        # Primera fila de combos - Ubicación
        self.frame_ubicacion = ttk.LabelFrame(self.frame_combos, text="Ubicación")
        self.frame_ubicacion.pack(fill="x", padx=5, pady=5)
        
        self.frame_ubicacion_content = ttk.Frame(self.frame_ubicacion)
        self.frame_ubicacion_content.pack(fill="x", padx=5, pady=5)
        
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

        # Segunda fila de combos - Insumo
        self.frame_insumo = ttk.LabelFrame(self.frame_combos, text="Insumo")
        self.frame_insumo.pack(fill="x", padx=5, pady=5)
        
        self.frame_insumo_content = ttk.Frame(self.frame_insumo)
        self.frame_insumo_content.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(self.frame_insumo_content, text="Tipo de Insumo:").grid(row=0, column=0, padx=5, sticky='w')
        self.tipo_insumo_var = tk.StringVar()
        self.combo_tipo_insumo = AutocompleteCombobox(self.frame_insumo_content, textvariable=self.tipo_insumo_var, state="normal", width=20)
        self.combo_tipo_insumo.grid(row=0, column=1, padx=5, sticky='w')
        
        ttk.Label(self.frame_insumo_content, text="Insumo:").grid(row=0, column=2, padx=5, sticky='w')
        self.insumo_var = tk.StringVar()
        self.combo_insumo = AutocompleteCombobox(self.frame_insumo_content, textvariable=self.insumo_var, state="normal", width=20)
        self.combo_insumo.grid(row=0, column=3, padx=5, sticky='w')
        
        ttk.Label(self.frame_insumo_content, text="Presentación:").grid(row=0, column=4, padx=5, sticky='w')
        self.presentacion_var = tk.StringVar()
        self.combo_presentacion = AutocompleteCombobox(self.frame_insumo_content, textvariable=self.presentacion_var, state="normal", width=20)
        self.combo_presentacion.grid(row=0, column=5, padx=5, sticky='w')

        # Tercera fila - Nivel Máximo
        self.frame_nivel = ttk.LabelFrame(self.frame_combos, text="Configuración")
        self.frame_nivel.pack(fill="x", padx=5, pady=5)
        
        self.frame_nivel_content = ttk.Frame(self.frame_nivel)
        self.frame_nivel_content.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(self.frame_nivel_content, text="Nivel Máximo:").grid(row=0, column=0, padx=5, sticky='w')
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

        # Frame para el visor PDF (SOLO pack aquí y en sus hijos)
        self.pdf_frame = ttk.Frame(self.frame_principal)
        self.pdf_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.pdf_viewer = None

        # Frame para botones
        self.frame_botones = ttk.Frame(self.frame_principal)
        self.frame_botones.pack(fill="x", pady=10)

        botones_grid = ttk.Frame(self.frame_botones)
        botones_grid.pack(fill="x")

        ttk.Button(botones_grid, text="Generar Reporte", command=self.generar_vista_previa).grid(row=0, column=0, padx=5)
        ttk.Button(botones_grid, text="Imprimir", command=self.imprimir_pdf).grid(row=0, column=1, padx=5)
        ttk.Button(botones_grid, text="Exportar a PDF", command=self.exportar_pdf).grid(row=0, column=2, padx=5)
        ttk.Button(botones_grid, text="Exportar a Excel", command=self.generar_excel_reporte).grid(row=0, column=3, padx=5)
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

    def actualizar_visibilidad_fechas(self):
        modo = self.modo_fecha_var.get()
        if modo == "rango":
            self.fecha_inicial.config(state="normal")
            self.fecha_final.config(state="normal")
            self.combo_anio.config(state="disabled")
            self.combo_mes_inicio.config(state="disabled")
            self.combo_mes_final.config(state="disabled")
            self.frame_rango.configure(style='Enabled.TFrame')
            self.frame_corte.configure(style='Disabled.TFrame')
        else:
            self.fecha_inicial.config(state="disabled")
            self.fecha_final.config(state="disabled")
            self.combo_anio.config(state="readonly")
            self.combo_mes_inicio.config(state="readonly")
            self.combo_mes_final.config(state="readonly")
            self.frame_rango.configure(style='Disabled.TFrame')
            self.frame_corte.configure(style='Enabled.TFrame')
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
        try:
            # Obtener fechas según el modo seleccionado
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

            # Validar fechas
            if fecha_fin < fecha_ini:
                messagebox.showerror("Error", "La fecha final debe ser mayor a la inicial")
                return

            # Obtener datos usando la función específica para BRES
            movimientos_raw = obtener_movimientos_bres(
                fecha_ini.strftime('%Y-%m-%d'),
                fecha_fin.strftime('%Y-%m-%d'),
                self.combo_distrito.get() if self.combo_distrito.get() else None,
                self.combo_tipo_servicio.get() if self.combo_tipo_servicio.get() else None,
                self.combo_servicio.get() if self.combo_servicio.get() else None,
                self.combo_tipo_insumo.get() if self.combo_tipo_insumo.get() else None,
                self.combo_insumo.get() if self.combo_insumo.get() else None,
                self.combo_presentacion.get() if self.combo_presentacion.get() else None
            )

            if not movimientos_raw:
                messagebox.showinfo("Info", "No hay datos para mostrar")
                return

            # Procesar datos para BRES
            self.movimientos_data = self.procesar_datos_bres(movimientos_raw, fecha_ini, fecha_fin)

            if not self.movimientos_data:
                messagebox.showwarning("Sin datos", "No hay datos procesados para mostrar")
                return

            # Generar PDF temporal
            import tempfile
            temp_dir = tempfile.gettempdir()
            self.temp_pdf_path = os.path.join(temp_dir, "vista_previa_bres.pdf")

            # Generar el PDF en el archivo temporal
            self.generar_pdf(self.temp_pdf_path, es_vista_previa=True)

            # Limpiar el frame PDF si existe
            for widget in self.pdf_frame.winfo_children():
                widget.destroy()

            # Crear un canvas con scrollbars dentro del pdf_frame
            canvas_frame = ttk.Frame(self.pdf_frame)
            canvas_frame.pack(fill="both", expand=True)

            # Scrollbars
            h_scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal")
            h_scrollbar.pack(side="bottom", fill="x")

            v_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical")
            v_scrollbar.pack(side="right", fill="y")

            # Canvas
            canvas = tk.Canvas(canvas_frame,
                            xscrollcommand=h_scrollbar.set,
                            yscrollcommand=v_scrollbar.set)
            canvas.pack(side="left", fill="both", expand=True)

            # Configurar scrollbars
            h_scrollbar.config(command=canvas.xview)
            v_scrollbar.config(command=canvas.yview)

            # Abrir el PDF con PyMuPDF
            doc = fitz.open(self.temp_pdf_path)

            # Variables para controlar la página actual
            self.current_page = 0
            self.total_pages = len(doc)

            # Frame para controles de navegación
            control_frame = ttk.Frame(self.pdf_frame)
            control_frame.pack(fill="x", pady=5)

            # Función para cambiar de página
            def change_page(delta):
                self.current_page = max(0, min(self.current_page + delta, self.total_pages - 1))
                display_page()
                page_label.config(text=f"Página {self.current_page + 1} de {self.total_pages}")

            # Botones de navegación
            ttk.Button(control_frame, text="<<", command=lambda: change_page(-1)).pack(side="left", padx=5)
            page_label = ttk.Label(control_frame, text=f"Página 1 de {self.total_pages}")
            page_label.pack(side="left", padx=10)
            ttk.Button(control_frame, text=">>", command=lambda: change_page(1)).pack(side="left", padx=5)

            # Función para mostrar la página actual
            def display_page():
                # Limpiar canvas
                canvas.delete("all")

                # Obtener la página actual
                page = doc.load_page(self.current_page)

                # Renderizar a imagen
                pix = page.get_pixmap(matrix=fitz.Matrix(1.2, 1.2))

                # Convertir a formato PIL
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # Convertir a formato Tkinter
                tk_img = ImageTk.PhotoImage(image=img)

                # Guardar referencia
                canvas.image = tk_img

                # Mostrar en canvas
                canvas.create_image(0, 0, anchor="nw", image=tk_img)

                # Configurar región de desplazamiento
                canvas.config(scrollregion=canvas.bbox("all"))

            # Mostrar la primera página
            display_page()

            # **MENSAJE ELIMINADO - Ya no aparece el messagebox de éxito**

        except Exception as e:
            import traceback
            error_detallado = traceback.format_exc()
            print(f"Error detallado:\n{error_detallado}")
            messagebox.showerror("Error", f"Error al generar reporte:\n{str(e)}")
            
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
                    mov.get('nombre_insumo', ''),
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
                2.2*inch,   # Descripción del Insumo (más ancho sin presentación)
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

            table = Table(data, colWidths=colWidths)
            
            # **ESTILO MEJORADO CON ALTURA DE FILA AJUSTADA**
            table_style = [
                ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
                ('TEXTCOLOR', (0,0), (-1,0), colors.black),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 7),
                ('FONTSIZE', (0,1), (-1,-1), 7),
                ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0,0), (-1,0), [colors.lightblue]),
                # **ALTURA AUMENTADA PARA ENCABEZADOS**
                ('TOPPADDING', (0,0), (-1,0), 8),      # Aumentado de 6 a 8
                ('BOTTOMPADDING', (0,0), (-1,0), 8),   # Aumentado de 6 a 8
                ('TOPPADDING', (0,1), (-1,-1), 3),     # Aumentado de 2 a 3
                ('BOTTOMPADDING', (0,1), (-1,-1), 3),  # Aumentado de 2 a 3
                ('LEFTPADDING', (0,0), (-1,-1), 2),
                ('RIGHTPADDING', (0,0), (-1,-1), 2),
                ('WORDWRAP', (0,0), (-1,-1), True),    # Aplicar a toda la tabla
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

            # Generar nombre de archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"Reporte_BRES_{timestamp}.xlsx"

            # Ruta a la carpeta Descargas
            downloads_path = os.path.expanduser("~/Downloads")
            full_path = os.path.join(downloads_path, file_name)

            # Crear DataFrame
            df = pd.DataFrame(self.movimientos_data)
            df.columns = self.COLUMNAS

            # Crear archivo Excel
            with pd.ExcelWriter(full_path, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Reporte BRES', index=False)
                
                # Obtener workbook y worksheet
                workbook = writer.book
                worksheet = writer.sheets['Reporte BRES']
                
                # Formato para encabezados
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#D7E4BC',
                    'border': 1
                })
                
                # Aplicar formato a encabezados
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Ajustar anchos de columna
                worksheet.set_column('A:N', 15)

            messagebox.showinfo("Éxito", f"Excel guardado en:\n{full_path}")

            # Preguntar si desea abrir el Excel
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

        except Exception as e:
            messagebox.showerror("Error", f"Error al generar Excel: {str(e)}")

    def cerrar_ventana(self):
        try:
            if hasattr(self, 'temp_pdf_path') and os.path.exists(self.temp_pdf_path):
                try:
                    os.remove(self.temp_pdf_path)
                except:
                    pass

            if self.main_window:
                self.main_window.show_main_menu()

        except Exception as e:
            print(f"Error al cerrar ventana: {e}")
            if self.main_window:
                try:
                    self.main_window.show_main_menu()
                except:
                    pass
    
    def destroy(self):
        if hasattr(self, 'frame_principal'):
            self.frame_principal.destroy()