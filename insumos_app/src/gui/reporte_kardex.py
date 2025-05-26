# Imports existentes
from calendar import month_name
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import pandas as pd
from datetime import datetime
import sys
import os
from ttkwidgets.autocomplete import AutocompleteCombobox

# Nuevos imports para PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

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
    obtener_movimientos_kardex
)

class ReporteKardex:
    # Definir las columnas como atributo de la clase
    COLUMNAS = [
        'Fecha', 'Referencia', 'Remitente/Destinatario', 'Entrada',
        'Precio Unitario', 'Valor Total', 'Lote', 'Fecha Vencimiento', 
        'Salidas', 'Reajustes', 'Saldo', 'Observaciones'
    ]
    
    def formato_float(self, valor):
        try:
            return f"{float(valor):.2f}"
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

    def ordenar_movimientos(self, movimientos):
        """
        Ordena los movimientos por fecha y luego por prioridad de tipo de movimiento.
        Positivos primero, luego negativos, luego neutrales (NO ENTREGADO).
        """
        def obtener_prioridad(tipo_movimiento):
            tipo = tipo_movimiento.upper()
            # Movimientos positivos (prioridad 1)
            if tipo in ['INVENTARIO INICIAL', 'ENTRADA NIVEL SUPERIOR', 'REAJUSTE POSITIVO']:
                return 1
            # Movimientos negativos que SÍ afectan el saldo (prioridad 2)
            elif tipo in ['SALIDA NIVEL INFERIOR', 'REAJUSTE NEGATIVO', 'ENTREGADO']:
                return 2
            # Movimientos neutrales que NO afectan el saldo (prioridad 3)
            elif tipo == 'NO ENTREGADO':
                return 3
            # Cualquier otro tipo no reconocido (prioridad 4)
            else:
                return 4

        # Ordenar por fecha y luego por prioridad
        return sorted(movimientos, key=lambda x: (x['fecha'], obtener_prioridad(x['tipo_movimiento'])))

    def calcular_saldo_acumulado(self, movimientos_ordenados):
        """
        Calcula el saldo acumulado para los movimientos ordenados.
        Los movimientos "NO ENTREGADO" se muestran pero no afectan el saldo.
        """
        saldo = 0
        movimientos_con_saldo = []

        for mov in movimientos_ordenados:
            tipo = mov['tipo_movimiento'].upper()

            # Buscar la cantidad usando múltiples posibles nombres de campo
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

            # Si no encontramos cantidad en los campos esperados, buscar cualquier campo que contenga 'cantidad'
            if cantidad == 0:
                for key, value in mov.items():
                    if 'cantidad' in key.lower() and value is not None:
                        try:
                            cantidad = float(value)
                            break
                        except (ValueError, TypeError):
                            continue

            # Formatear fechas
            fecha_registro = self.formatear_fecha(mov.get('fecha', ''))
            fecha_vencimiento = self.formatear_fecha(mov.get('fecha_vencimiento', ''))

            # Determinar el destinatario para SALIDA NIVEL INFERIOR
            destinatario = mov['tipo_movimiento']
            if tipo == 'SALIDA NIVEL INFERIOR':
                if mov.get('distrito_destino'):
                    destinatario = f"Distrito: {mov['distrito_destino']}"
                elif mov.get('servicio_destino'):
                    destinatario = f"Servicio: {mov['servicio_destino']}"

            # Configurar las columnas según el tipo de movimiento
            entrada = 0
            salida = ""
            reajuste = 0
            cantidad_col = 0

            if tipo in ['INVENTARIO INICIAL', 'ENTRADA NIVEL SUPERIOR']:
                entrada = cantidad
                cantidad_col = cantidad
                saldo += cantidad  # SÍ afecta el saldo
            elif tipo in ['SALIDA NIVEL INFERIOR', 'ENTREGADO']:
                salida = f"{cantidad:.2f} ({tipo.title()})"
                cantidad_col = cantidad
                saldo -= cantidad  # SÍ afecta el saldo
            elif tipo == 'REAJUSTE POSITIVO':
                reajuste = cantidad
                cantidad_col = cantidad
                saldo += cantidad  # SÍ afecta el saldo
            elif tipo == 'REAJUSTE NEGATIVO':
                reajuste = -cantidad
                cantidad_col = cantidad
                saldo -= cantidad  # SÍ afecta el saldo
            elif tipo == 'NO ENTREGADO':
                # NO ENTREGADO se muestra en el reporte pero NO afecta el saldo
                salida = f"{cantidad:.2f} (No Entregado)"
                cantidad_col = cantidad
                # NO se modifica el saldo: saldo permanece igual

            movimientos_con_saldo.append({
                'fecha': fecha_registro,
                'referencia': mov.get('referencia', ''),
                'tipo_movimiento': destinatario,
                'entrada': entrada,
                'precio_unitario': "",
                'valor_total': "",
                'lote': mov.get('lote', ''),
                'fecha_vencimiento': fecha_vencimiento,
                'salida': salida,
                'reajuste': reajuste,
                'cantidad_col': cantidad_col,
                'saldo': saldo,
                'observaciones': mov.get('observaciones', '')
            })

        return movimientos_con_saldo

    def formatear_fecha(self, fecha):
        """
        Convierte una fecha al formato día/mes/año
        """
        if not fecha:
            return ""

        try:
            # Si la fecha viene como string, intentar parsearla
            if isinstance(fecha, str):
                # Intentar diferentes formatos de entrada
                formatos_entrada = [
                    '%Y-%m-%d',      # 2024-01-15
                    '%Y/%m/%d',      # 2024/01/15
                    '%d-%m-%Y',      # 15-01-2024
                    '%d/%m/%Y',      # 15/01/2024
                    '%Y-%m-%d %H:%M:%S',  # 2024-01-15 10:30:00
                    '%Y/%m/%d %H:%M:%S'   # 2024/01/15 10:30:00
                ]

                for formato in formatos_entrada:
                    try:
                        fecha_obj = datetime.strptime(fecha, formato)
                        return fecha_obj.strftime('%d/%m/%Y')
                    except ValueError:
                        continue

                # Si no se pudo parsear, devolver la fecha original
                return fecha

            # Si la fecha viene como objeto datetime
            elif hasattr(fecha, 'strftime'):
                return fecha.strftime('%d/%m/%Y')

            # Si es otro tipo, convertir a string
            else:
                return str(fecha)

        except Exception as e:
            print(f"Error al formatear fecha {fecha}: {e}")
            return str(fecha) if fecha else ""

    def setup_ui(self):
        # Frame principal - USAR PACK PARA TODO
        self.frame_principal = ttk.LabelFrame(self.parent, text="Filtros de Reporte")
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
            state='normal'  # Aseguramos que sea editable
        )
        self.fecha_inicial.grid(row=0, column=2, padx=5)

        ttk.Label(self.frame_rango, text="Fecha Final:").grid(row=0, column=3, padx=5)
        self.fecha_final = DateEntry(
            self.frame_rango,
            width=12,
            date_pattern='dd/mm/yyyy',
            state='normal'  # Aseguramos que sea editable
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
        self.combo_anio.set(str(datetime.now().year))  # Año actual por defecto

        # Mes inicio
        ttk.Label(self.frame_corte, text="Mes Inicio:").grid(row=0, column=3, padx=5)
        self.mes_inicio_var = tk.StringVar()

        # Obtener nombres de meses en español
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

        # Inicializar visibilidad
        self.actualizar_visibilidad_fechas()

        # Frame para combos
        self.frame_combos = ttk.Frame(self.frame_principal)
        self.frame_combos.pack(fill="x", padx=5, pady=5)

        # Primera fila de combos
        self.frame_combos1 = ttk.Frame(self.frame_combos)
        self.frame_combos1.pack(fill="x", pady=5)
        
        # Grid DENTRO del frame_combos1 (esto es válido)
        ttk.Label(self.frame_combos1, text="Área:").grid(row=0, column=0, padx=5, sticky='w')
        self.area_var = tk.StringVar()
        self.combo_area = AutocompleteCombobox(self.frame_combos1, textvariable=self.area_var, state="normal", width=20)
        self.combo_area.grid(row=0, column=1, padx=5, sticky='w')
        ttk.Label(self.frame_combos1, text="Distrito:").grid(row=0, column=2, padx=5, sticky='w')
        self.distrito_var = tk.StringVar()
        self.combo_distrito = AutocompleteCombobox(self.frame_combos1, textvariable=self.distrito_var, state="normal", width=20)
        self.combo_distrito.grid(row=0, column=3, padx=5, sticky='w')
        ttk.Label(self.frame_combos1, text="Tipo de Servicio:").grid(row=0, column=4, padx=5, sticky='w')
        self.tipo_servicio_var = tk.StringVar()
        self.combo_tipo_servicio = AutocompleteCombobox(self.frame_combos1, textvariable=self.tipo_servicio_var, state="normal", width=20)
        self.combo_tipo_servicio.grid(row=0, column=5, padx=5, sticky='w')
        ttk.Label(self.frame_combos1, text="Servicio:").grid(row=0, column=6, padx=5, sticky='w')
        self.servicio_var = tk.StringVar()
        self.combo_servicio = AutocompleteCombobox(self.frame_combos1, textvariable=self.servicio_var, state="normal", width=20)
        self.combo_servicio.grid(row=0, column=7, padx=5, sticky='w')

        # Segunda fila de combos
        self.frame_combos2 = ttk.Frame(self.frame_combos)
        self.frame_combos2.pack(fill="x", pady=5)
        
        # Grid DENTRO del frame_combos2 (esto es válido)
        ttk.Label(self.frame_combos2, text="Tipo de Insumo:").grid(row=0, column=0, padx=5, sticky='w')
        self.tipo_insumo_var = tk.StringVar()
        self.combo_tipo_insumo = AutocompleteCombobox(self.frame_combos2, textvariable=self.tipo_insumo_var, state="normal", width=20)
        self.combo_tipo_insumo.grid(row=0, column=1, padx=5, sticky='w')
        ttk.Label(self.frame_combos2, text="Insumo:").grid(row=0, column=2, padx=5, sticky='w')
        self.insumo_var = tk.StringVar()
        self.combo_insumo = AutocompleteCombobox(self.frame_combos2, textvariable=self.insumo_var, state="normal", width=20)
        self.combo_insumo.grid(row=0, column=3, padx=5, sticky='w')
        ttk.Label(self.frame_combos2, text="Presentación:").grid(row=0, column=4, padx=5, sticky='w')
        self.presentacion_var = tk.StringVar()
        self.combo_presentacion = AutocompleteCombobox(self.frame_combos2, textvariable=self.presentacion_var, state="normal", width=20)
        self.combo_presentacion.grid(row=0, column=5, padx=5, sticky='w')

        # Frame para el visor PDF (SOLO pack aquí y en sus hijos)
        self.pdf_frame = ttk.Frame(self.frame_principal)
        self.pdf_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.pdf_viewer = None

        # Frame para botones
        self.frame_botones = ttk.Frame(self.frame_principal)
        self.frame_botones.pack(fill="x", pady=10)

        botones_grid = ttk.Frame(self.frame_botones)
        botones_grid.pack(fill="x")

        ttk.Button(botones_grid, text="Generar Vista Previa", command=self.generar_vista_previa).grid(row=0, column=0, padx=5)
        ttk.Button(botones_grid, text="Imprimir", command=self.imprimir_pdf).grid(row=0, column=1, padx=5)
        ttk.Button(botones_grid, text="Exportar a PDF", command=self.exportar_pdf).grid(row=0, column=2, padx=5)
        ttk.Button(botones_grid, text="Exportar a Excel", command=self.generar_kardex).grid(row=0, column=3, padx=5)
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
            # Habilitar DateEntry
            self.fecha_inicial.config(state="normal")
            self.fecha_final.config(state="normal")

            # Deshabilitar combos de corte
            self.combo_anio.config(state="disabled")
            self.combo_mes_inicio.config(state="disabled")
            self.combo_mes_final.config(state="disabled")

            # Resaltar visualmente el frame activo
            self.frame_rango.configure(style='Enabled.TFrame')
            self.frame_corte.configure(style='Disabled.TFrame')
        else:
            # Deshabilitar DateEntry
            self.fecha_inicial.config(state="disabled")
            self.fecha_final.config(state="disabled")

            # Habilitar combos de corte
            self.combo_anio.config(state="readonly")
            self.combo_mes_inicio.config(state="readonly")
            self.combo_mes_final.config(state="readonly")

            # Resaltar visualmente el frame activo
            self.frame_rango.configure(style='Disabled.TFrame')
            self.frame_corte.configure(style='Enabled.TFrame')

        # Forzar actualización visual
        self.frame_fechas.update()
    
    def calcular_rango_corte_logistico(self, anio, mes_inicio, mes_final):
        """
        Calcula el rango de fechas para el corte logístico.
        Retorna (fecha_inicial, fecha_final) en formato dd/mm/yyyy
        """
        # Diccionario de meses en español a números
        meses_a_numero = {
            'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4,
            'Mayo': 5, 'Junio': 6, 'Julio': 7, 'Agosto': 8,
            'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12
        }

        # Convertir nombres de meses a números
        m_ini = meses_a_numero.get(mes_inicio)
        m_fin = meses_a_numero.get(mes_final)

        if not (m_ini and m_fin):
            raise ValueError("Mes inicio y mes final deben ser válidos")

        try:
            anio = int(anio)
        except ValueError:
            raise ValueError("Año debe ser un número válido")

        # Calcular fecha inicial (26 del mes anterior)
        if m_ini == 1:  # Si es enero, el mes anterior es diciembre del año anterior
            fecha_ini = datetime(anio - 1, 12, 26)
        else:
            fecha_ini = datetime(anio, m_ini - 1, 26)

        # Calcular fecha final (25 del mes actual)
        fecha_fin = datetime(anio, m_fin, 25)

        return fecha_ini.strftime('%d/%m/%Y'), fecha_fin.strftime('%d/%m/%Y')
    
    def actualizar_fechas_por_corte(self, event=None):
        """
        Actualiza las fechas en los DateEntry cuando se selecciona año y meses
        """
        try:
            anio = self.anio_var.get()
            mes_inicio = self.mes_inicio_var.get()
            mes_final = self.mes_final_var.get()

            if anio and mes_inicio and mes_final:
                fecha_ini, fecha_fin = self.calcular_rango_corte_logistico(anio, mes_inicio, mes_final)

                # Actualizar los DateEntry
                self.fecha_inicial.set_date(datetime.strptime(fecha_ini, '%d/%m/%Y'))
                self.fecha_final.set_date(datetime.strptime(fecha_fin, '%d/%m/%Y'))
        except Exception as e:
            messagebox.showerror("Error", f"Error al calcular fechas: {str(e)}")
            
    def cargar_areas(self):
        self.areas = obtener_areas()
        if self.areas:
            opciones = [''] + [a['nombre'] for a in self.areas]
            self.combo_area.set_completion_list(opciones)

    def cargar_distritos(self):
        self.distritos = obtener_distritos()
        if self.distritos:
            opciones = [''] + [d['nombre'] for d in self.distritos]
            self.combo_distrito.set_completion_list(opciones)
    
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
                # No borrar texto actual para no interferir con la escritura del usuario
                # self.combo_distrito.set('')  # <-- comentar o eliminar esta línea
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

            # Validar selección de insumo
            if not self.combo_insumo.get():
                messagebox.showerror("Error", "Debe seleccionar un insumo")
                return

            # Obtener datos
            movimientos_raw = obtener_movimientos_kardex(
                fecha_ini.strftime('%Y-%m-%d'),
                fecha_fin.strftime('%Y-%m-%d'),
                self.combo_distrito.get(),
                self.combo_tipo_servicio.get(),
                self.combo_servicio.get(),
                self.combo_tipo_insumo.get(),
                self.combo_insumo.get(),
                self.combo_presentacion.get()
            )

            if not movimientos_raw:
                messagebox.showinfo("Info", "No hay datos para mostrar")
                return

            # Ordenar movimientos y calcular saldo
            movimientos_ordenados = self.ordenar_movimientos(movimientos_raw)
            self.movimientos_data = self.calcular_saldo_acumulado(movimientos_ordenados)

            # Generar PDF temporal
            import tempfile
            import os

            # Crear archivo temporal
            temp_dir = tempfile.gettempdir()
            self.temp_pdf_path = os.path.join(temp_dir, "vista_previa_kardex.pdf")

            # Generar el PDF en el archivo temporal
            self.generar_pdf(self.temp_pdf_path, es_vista_previa=True)

            # Importar las bibliotecas necesarias
            import fitz  # PyMuPDF
            from PIL import Image, ImageTk

            # Limpiar el frame PDF si existe
            if hasattr(self, 'pdf_frame'):
                for widget in self.pdf_frame.winfo_children():
                    widget.destroy()

            # Asegurarse de que el frame PDF existe
            if not hasattr(self, 'pdf_frame'):
                self.pdf_frame = ttk.Frame(self.frame_principal)
                self.pdf_frame.pack(fill="both", expand=True, padx=5, pady=5)

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
                pix = page.get_pixmap(matrix=fitz.Matrix(1.2, 1.2))  # Escala 1.2 para mejor calidad

                # Convertir a formato PIL
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # Convertir a formato Tkinter
                tk_img = ImageTk.PhotoImage(image=img)

                # Guardar referencia para evitar que sea eliminada por el recolector de basura
                canvas.image = tk_img

                # Mostrar en canvas
                canvas.create_image(0, 0, anchor="nw", image=tk_img)

                # Configurar región de desplazamiento
                canvas.config(scrollregion=canvas.bbox("all"))

            # Mostrar la primera página
            display_page()

        except Exception as e:
            # Capturar y mostrar cualquier error que ocurra
            import traceback
            error_detallado = traceback.format_exc()
            print(f"Error detallado:\n{error_detallado}")  # Para deb
            messagebox.showerror(
                "Error",
                f"Error al generar vista previa:\n{str(e)}\n\nPor favor, verifique los datos e intente nuevamente."
            )

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
    
    def exportar_pdf(self):
        try:
            import os  # Importar os al inicio del método

            # Obtener fechas según el modo seleccionado
            if self.modo_fecha_var.get() == "rango":
                fecha_ini = datetime.strptime(self.fecha_inicial.get(), '%d/%m/%Y')
                fecha_fin = datetime.strptime(self.fecha_final.get(), '%d/%m/%Y')
                periodo = f"{fecha_ini.strftime('%d%m%Y')}_{fecha_fin.strftime('%d%m%Y')}"  # Formato para rango
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
                periodo = f"{mes_inicio}_{mes_final}_{anio}"  # Formato para corte

            # Validar fechas
            if fecha_fin < fecha_ini:
                messagebox.showerror("Error", "La fecha final debe ser mayor a la inicial")
                return

            # Validar selección de insumo
            if not self.combo_insumo.get():
                messagebox.showerror("Error", "Debe seleccionar un insumo")
                return

            # Obtener datos si no existen
            if not self.movimientos_data:
                movimientos_raw = obtener_movimientos_kardex(
                    fecha_ini.strftime('%Y-%m-%d'),
                    fecha_fin.strftime('%Y-%m-%d'),
                    self.combo_distrito.get(),
                    self.combo_tipo_servicio.get(),
                    self.combo_servicio.get(),
                    self.combo_tipo_insumo.get(),
                    self.combo_insumo.get(),
                    self.combo_presentacion.get()
                )

                if not movimientos_raw:
                    messagebox.showinfo("Info", "No hay datos para mostrar")
                    return

                # Ordenar movimientos y calcular saldo
                movimientos_ordenados = self.ordenar_movimientos(movimientos_raw)
                self.movimientos_data = self.calcular_saldo_acumulado(movimientos_ordenados)

            # Generar nombre de archivo con fecha y hora
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"Reporte_Kardex_{periodo}_{timestamp}.pdf"  # Incluir periodo en nombre

            # Ruta a la carpeta Descargas
            downloads_path = os.path.expanduser("~/Downloads")
            full_path = os.path.join(downloads_path, file_name)

            # Generar el PDF en la ruta de Descargas
            self.generar_pdf(full_path)

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
                pagesize=landscape(letter),
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
            elements.append(Paragraph("TARJETA DE CONTROL DE SUMINISTROS", subtitle_style))
            elements.append(Paragraph(
                f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                timestamp_style))

            # Filtros en dos filas horizontales
            filtros = [
                f"Área: {self.combo_area.get()}",
                f"Distrito: {self.combo_distrito.get()}",
                f"Tipo de Servicio: {self.combo_tipo_servicio.get()}",
                f"Servicio: {self.combo_servicio.get()}",
                f"Insumo: {self.combo_insumo.get()}",
                f"Presentación: {self.combo_presentacion.get()}"
            ]

            # Crear estilo para alineación izquierda
            left_style = ParagraphStyle(
                name="LeftAlign",
                alignment=0,  # 0 = LEFT
                fontSize=9,
                fontName='Helvetica'
            )

            # Crear tabla con una sola fila y 5 columnas
            data_filtros = [[Paragraph(item, left_style) for item in filtros]]

            # Anchos de columna (ajustar según necesidad)
            col_widths = [125, 125, 125, 125, 125]

            table_filtros = Table(data_filtros, colWidths=col_widths)
            table_filtros.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey)
            ]))

            elements.append(table_filtros)
            elements.append(Spacer(1, 30))

            # Dividir datos en páginas (aproximadamente 25 filas por página)
            filas_por_pagina = 25
            total_movimientos = len(self.movimientos_data)
            
            for pagina in range(0, total_movimientos, filas_por_pagina):
                # Si no es la primera página, agregar salto de página
                if pagina > 0:
                    from reportlab.platypus import PageBreak
                    elements.append(PageBreak())
                    
                    # Agregar títulos en cada página nueva
                    elements.append(Paragraph(
                        "DIRECCIÓN DEPARTAMENTAL DE REDES INTEGRADAS DE SERVICIOS DE SALUD DE GUATEMALA,",
                        title_style))
                    elements.append(Paragraph("ÁREA NOR ORIENTE", subtitle_style))
                    elements.append(Paragraph("TARJETA DE CONTROL DE SUMINISTROS", subtitle_style))
                    elements.append(Spacer(1, 20))

                # Encabezados de la tabla
                headers = [
                    'Fecha',
                    'Referencia',
                    'Remitente/\nDestinatario',
                    'Entrada',
                    'Precio\nUnitario',
                    'Valor\nTotal',
                    'Lote',
                    'Fecha\nVencimiento',
                    'Salidas',
                    'Reajustes\n(+) (-)',
                    'Cantidad',
                    'Saldo',
                    'Observaciones'
                ]

                # Datos de la página actual
                data = [headers]
                
                # Si no es la primera página, agregar fila con saldo anterior
                if pagina > 0:
                    saldo_anterior = self.movimientos_data[pagina - 1]['saldo']
                    fila_saldo_anterior = [
                        "SALDO ANTERIOR", "", "", "", "", "", "", "", "", "", "", 
                        self.formato_float(saldo_anterior), ""
                    ]
                    data.append(fila_saldo_anterior)

                # Agregar movimientos de esta página
                fin_pagina = min(pagina + filas_por_pagina, total_movimientos)
                for i in range(pagina, fin_pagina):
                    mov = self.movimientos_data[i]
                    row = [
                        mov['fecha'],
                        mov['referencia'] or "",
                        mov['tipo_movimiento'],
                        self.formato_float(mov['entrada']),
                        self.formato_float(mov['precio_unitario']),
                        self.formato_float(mov['valor_total']),
                        mov['lote'] or "",
                        mov['fecha_vencimiento'] or "",
                        mov['salida'],
                        f"{mov['reajuste']:+.2f}" if mov['reajuste'] != 0 else "",
                        self.formato_float(mov['cantidad_col']),
                        self.formato_float(mov['saldo']),
                        mov['observaciones'] or ""
                    ]
                    data.append(row)

                # Crear tabla con formato y anchos ajustados
                colWidths = [
                    0.7*inch,  # Fecha
                    0.8*inch,  # Ref.
                    1.5*inch,  # Remitente
                    0.6*inch,  # Entrada
                    0.7*inch,  # P.Unit.
                    0.7*inch,  # V.Total
                    0.8*inch,  # Lote
                    0.7*inch,  # F.Venc.
                    0.6*inch,  # Salidas
                    0.6*inch,  # Reaj.
                    0.6*inch,  # Cant.
                    0.6*inch,  # Saldo
                    1.1*inch   # Obs.
                ]

                table = Table(data, colWidths=colWidths)
                
                # Estilo base de la tabla
                table_style = [
                    ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.black),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,0), 7),
                    ('FONTSIZE', (0,1), (-1,-1), 7),
                    ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('TOPPADDING', (0,0), (-1,0), 6),
                    ('BOTTOMPADDING', (0,0), (-1,0), 6),
                    ('TOPPADDING', (0,1), (-1,-1), 2),
                    ('BOTTOMPADDING', (0,1), (-1,-1), 2),
                    ('LEFTPADDING', (0,0), (-1,-1), 2),
                    ('RIGHTPADDING', (0,0), (-1,-1), 2),
                    ('WORDWRAP', (0,0), (-1,0), True),
                ]
                
                # Si hay saldo anterior, resaltarlo
                if pagina > 0:
                    table_style.append(('BACKGROUND', (0,1), (-1,1), colors.lightyellow))
                    table_style.append(('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'))

                table.setStyle(TableStyle(table_style))
                elements.append(table)

            doc.build(elements)

            if not es_vista_previa:
                messagebox.showinfo("Éxito", f"PDF guardado en:\n{ruta_pdf}")

        except Exception as e:
            messagebox.showerror("Error", f"Error al generar PDF: {str(e)}")

    def generar_kardex(self):
        try:
            # Obtener fechas según el modo seleccionado
            if self.modo_fecha_var.get() == "rango":
                fecha_ini = datetime.strptime(self.fecha_inicial.get(), '%d/%m/%Y')
                fecha_fin = datetime.strptime(self.fecha_final.get(), '%d/%m/%Y')
                periodo = f"{fecha_ini.strftime('%d%m%Y')}_{fecha_fin.strftime('%d%m%Y')}"  # Formato para rango
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
                periodo = f"{mes_inicio}_{mes_final}_{anio}"  # Formato para corte

            # Validar fechas
            if fecha_fin < fecha_ini:
                messagebox.showerror("Error", "La fecha final debe ser mayor a la inicial")
                return

            # Validar selección de insumo
            if not self.combo_insumo.get():
                messagebox.showerror("Error", "Debe seleccionar un insumo")
                return

            # Obtener datos para el reporte
            movimientos_raw = obtener_movimientos_kardex(
                fecha_ini.strftime('%Y-%m-%d'),
                fecha_fin.strftime('%Y-%m-%d'),
                self.combo_distrito.get(),
                self.combo_tipo_servicio.get(),
                self.combo_servicio.get(),
                self.combo_tipo_insumo.get(),
                self.combo_insumo.get(),
                self.combo_presentacion.get()
            )

            if not movimientos_raw:
                messagebox.showinfo("Info", "No hay datos para mostrar")
                return

            # Ordenar movimientos y calcular saldo
            movimientos_ordenados = self.ordenar_movimientos(movimientos_raw)
            movimientos = self.calcular_saldo_acumulado(movimientos_ordenados)

            # Crear DataFrame y generar Excel
            full_path = self.generar_excel(movimientos, periodo)

            # Preguntar si desea abrir el Excel
            if messagebox.askyesno("Excel Generado", "Reporte guardado exitosamente.\n¿Desea abrirlo ahora?"):
                import os
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
            messagebox.showerror("Error", f"Error al generar reporte: {str(e)}")

    def generar_excel(self, movimientos, periodo):
        try:
            import os  # Importar os al inicio del método
            
            # Dividir movimientos en hojas (máximo 1000 filas por hoja)
            filas_por_hoja = 1000
            total_movimientos = len(movimientos)
            
            # Generar nombre de archivo con fecha y hora
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"Reporte_Kardex_{periodo}_{timestamp}.xlsx"

            # Ruta a la carpeta Descargas
            downloads_path = os.path.expanduser("~/Downloads")
            full_path = os.path.join(downloads_path, file_name)

            # Crear archivo Excel
            writer = pd.ExcelWriter(full_path, engine='xlsxwriter')
            workbook = writer.book

            # Estilos comunes
            title_format = workbook.add_format({
                'bold': True,
                'align': 'center',
                'valign': 'vcenter',
                'font_size': 12,
                'text_wrap': True
            })

            subtitle_format = workbook.add_format({
                'bold': True,
                'align': 'center',
                'valign': 'vcenter',
                'font_size': 10,
                'text_wrap': True
            })

            header_format = workbook.add_format({
                'bold': True,
                'align': 'center',
                'valign': 'vcenter',
                'font_size': 9,
                'bg_color': '#ADD8E6',
                'text_wrap': True,
                'border': 1,
                'border_color': '#808080'
            })

            saldo_anterior_format = workbook.add_format({
                'bold': True,
                'align': 'center',
                'valign': 'vcenter',
                'font_size': 9,
                'bg_color': '#FFFFE0',
                'border': 1
            })

            # Procesar cada hoja
            for hoja_num in range(0, total_movimientos, filas_por_hoja):
                nombre_hoja = f"Kardex_{hoja_num//filas_por_hoja + 1}"
                
                # Filtrar y renombrar columnas para esta hoja
                fin_hoja = min(hoja_num + filas_por_hoja, total_movimientos)
                movimientos_hoja = movimientos[hoja_num:fin_hoja]
                
                columnas_relevantes = [
                    'fecha', 'referencia', 'tipo_movimiento', 'entrada',
                    'precio_unitario', 'valor_total', 'lote', 'fecha_vencimiento',
                    'salida', 'reajuste', 'cantidad_col', 'saldo', 'observaciones'
                ]
                
                df = pd.DataFrame(movimientos_hoja)[columnas_relevantes]

                # Nombres de columnas mejorados
                df.columns = [
                    'Fecha',
                    'No.\nReferencia',
                    'Remitente/\nDestinatario',
                    'Entrada',
                    'Precio\nUnitario\n(Q.)',
                    'Valor\nTotal\n(Q.)',
                    'No.\nLote',
                    'Fecha de\nVencimiento',
                    'Salidas',
                    'Reajustes\n(+) (-)',
                    'Cantidad',
                    'Saldo',
                    'Observaciones'
                ]

                # Escribir datos comenzando en fila 8
                fila_inicio = 8
                
                # Si no es la primera hoja, agregar fila de saldo anterior
                if hoja_num > 0:
                    saldo_anterior = movimientos[hoja_num - 1]['saldo']
                    # Crear DataFrame para saldo anterior
                    saldo_df = pd.DataFrame([{
                        'Fecha': 'SALDO ANTERIOR',
                        'No.\nReferencia': '',
                        'Remitente/\nDestinatario': '',
                        'Entrada': '',
                        'Precio\nUnitario\n(Q.)': '',
                        'Valor\nTotal\n(Q.)': '',
                        'No.\nLote': '',
                        'Fecha de\nVencimiento': '',
                        'Salidas': '',
                        'Reajustes\n(+) (-)': '',
                        'Cantidad': '',
                        'Saldo': saldo_anterior,
                        'Observaciones': ''
                    }])
                    
                    # Escribir saldo anterior
                    saldo_df.to_excel(writer, sheet_name=nombre_hoja, startrow=fila_inicio, index=False, header=False)
                    fila_inicio += 1

                # Escribir datos principales
                df.to_excel(writer, sheet_name=nombre_hoja, startrow=fila_inicio, index=False)

                # Obtener worksheet
                worksheet = writer.sheets[nombre_hoja]

                # Configurar títulos y encabezados
                self.configurar_hoja_excel(worksheet, workbook, title_format, subtitle_format, 
                                         header_format, saldo_anterior_format, df, hoja_num > 0, fila_inicio)

            # Guardar archivo
            writer.close()
            messagebox.showinfo("Éxito", f"Reporte guardado en:\n{full_path}")
            return full_path
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar Excel: {str(e)}")
            return None

    def configurar_hoja_excel(self, worksheet, workbook, title_format, subtitle_format, 
                            header_format, saldo_anterior_format, df, tiene_saldo_anterior, fila_inicio):
        """Configura el formato de una hoja de Excel"""
        
        # Configurar altura de filas
        worksheet.set_row(0, 30)
        worksheet.set_row(1, 25)
        worksheet.set_row(2, 25)
        worksheet.set_row(3, 20)
        worksheet.set_row(5, 25)
        worksheet.set_row(fila_inicio - 1, 45)  # Encabezados

        # Títulos principales
        worksheet.merge_range('A1:M1',
            'DIRECCIÓN DEPARTAMENTAL DE REDES INTEGRADAS DE SERVICIOS DE SALUD DE GUATEMALA,',
            title_format)
        worksheet.merge_range('A2:M2', 'ÁREA NOR ORIENTE', subtitle_format)
        worksheet.merge_range('A3:M3', 'TARJETA DE CONTROL DE SUMINISTROS', subtitle_format)
        worksheet.merge_range('A4:M4',
            f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            subtitle_format)

        # Filtros
        worksheet.merge_range('A6:B6', f"Área: {self.combo_area.get()}", subtitle_format)
        worksheet.merge_range('C6:D6', f"Distrito: {self.combo_distrito.get()}", subtitle_format)
        worksheet.merge_range('E6:F6', f"Tipo de Servicio: {self.combo_tipo_servicio.get()}", subtitle_format)
        worksheet.merge_range('G6:H6', f"Servicio: {self.combo_servicio.get()}", subtitle_format)
        worksheet.merge_range('I6:J6', f"Insumo: {self.combo_insumo.get()}", subtitle_format)
        worksheet.merge_range('K6:M6', f"Presentación: {self.combo_presentacion.get()}", subtitle_format)

        # Aplicar formato a encabezados
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(fila_inicio - 1, col_num, value, header_format)

        # Si hay saldo anterior, aplicar formato especial
        if tiene_saldo_anterior:
            for col in range(13):
                worksheet.write(fila_inicio, col, 
                              worksheet.cell(fila_inicio, col).value, saldo_anterior_format)

        # Configuración de página
        worksheet.set_landscape()
        worksheet.set_paper(9)
        worksheet.fit_to_pages(1, 1)

        # Ajustar anchos de columna
        worksheet.set_column('A:A', 10)    # Fecha
        worksheet.set_column('B:B', 12)    # No. Referencia
        worksheet.set_column('C:C', 20)    # Remitente/Destinatario
        worksheet.set_column('D:D', 10)    # Entrada
        worksheet.set_column('E:E', 10)    # Precio Unitario
        worksheet.set_column('F:F', 10)    # Valor Total

    def cerrar_ventana(self):
        """
        Cierra la ventana del reporte y limpia los recursos
        """
        try:
            # Limpiar archivo temporal si existe
            if hasattr(self, 'temp_pdf_path') and os.path.exists(self.temp_pdf_path):
                try:
                    os.remove(self.temp_pdf_path)
                except:
                    pass  # No importa si no se puede eliminar

            # Si hay una referencia a la ventana principal, volver al menú principal
            if self.main_window:
                self.main_window.show_main_menu()

        except Exception as e:
            print(f"Error al cerrar ventana: {e}")
            # En caso de error, intentar cerrar de todas formas
            if self.main_window:
                try:
                    self.main_window.show_main_menu()
                except:
                    pass