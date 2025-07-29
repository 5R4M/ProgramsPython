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
from reportlab.lib.pagesizes import letter, landscape, legal
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
            num = float(valor)
            if num == 0:
                return ""  # Retornar cadena vacía si es 0
            return f"{num:.2f}"
        except (ValueError, TypeError):
            return ""
    
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
            base_dir = os.path.dirname(os.path.dirname(__file__))  # Sube un nivel: de gui/ a src/
            icons_path = os.path.join(base_dir, "utils", "icons")
            
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
            fecha_vencimiento = mov.get('fecha_vencimiento')
            if fecha_vencimiento is None:
                fecha_vencimiento = "N/A"
            else:
                fecha_vencimiento = self.formatear_fecha(fecha_vencimiento)

            lote_val = mov.get('lote')
            if lote_val is None or lote_val == '':
                lote_val = "N/A"
            
            # Determinar el destinatario para SALIDA NIVEL INFERIOR
            destinatario = mov['tipo_movimiento']
            if tipo == 'SALIDA NIVEL INFERIOR':
                if mov.get('distrito_destino'):
                    destinatario = mov['distrito_destino']
                elif mov.get('servicio_destino'):
                    destinatario = mov['servicio_destino']

            # Configurar las columnas según el tipo de movimiento
            entrada = ""  # CAMBIO: Inicializar como cadena vacía
            salida = ""
            reajuste = ""  # CAMBIO: Inicializar como cadena vacía
            cantidad_col = self.formato_float(cantidad)  # CAMBIO: Usar formato_float

            if tipo in ['INVENTARIO INICIAL', 'ENTRADA NIVEL SUPERIOR']:
                entrada = self.formato_float(cantidad)  # CAMBIO: Usar formato_float
                saldo += cantidad  # SÍ afecta el saldo
            elif tipo == 'SALIDA NIVEL INFERIOR':
                salida = self.formato_float(cantidad)  # CAMBIO: Usar formato_float
                saldo -= cantidad  # SÍ afecta el saldo
            elif tipo == 'ENTREGADO':
                salida = self.formato_float(cantidad)  # CAMBIO: Usar formato_float
                saldo -= cantidad  # SÍ afecta el saldo
            elif tipo == 'REAJUSTE POSITIVO':
                reajuste = f"+{self.formato_float(cantidad)}" if cantidad > 0 else ""  # CAMBIO: Formato con signo
                saldo += cantidad  # SÍ afecta el saldo
            elif tipo == 'REAJUSTE NEGATIVO':
                reajuste = f"-{self.formato_float(cantidad)}" if cantidad > 0 else ""  # CAMBIO: Formato con signo
                saldo -= cantidad  # SÍ afecta el saldo
            elif tipo == 'NO ENTREGADO':
                # NO ENTREGADO se muestra en el reporte pero NO afecta el saldo
                salida = self.formato_float(cantidad)  # CAMBIO: Usar formato_float
                # NO se modifica el saldo: saldo permanece igual

            movimientos_con_saldo.append({
                'fecha': fecha_registro,
                'referencia': mov.get('referencia', ''),
                'tipo_movimiento': destinatario,
                'entrada': entrada,
                'precio_unitario': "",
                'valor_total': "",
                'lote': lote_val,
                'fecha_vencimiento': fecha_vencimiento,
                'salida': salida,
                'reajuste': reajuste,
                'cantidad_col': cantidad_col,
                'saldo': self.formato_float(saldo),  # CAMBIO: Usar formato_float para el saldo
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

    def destroy(self):
        # Desvincular eventos de los combobox
        try:
            self.combo_area.unbind('<<ComboboxSelected>>')
            self.combo_distrito.unbind('<<ComboboxSelected>>')
            self.combo_tipo_servicio.unbind('<<ComboboxSelected>>')
            self.combo_tipo_insumo.unbind('<<ComboboxSelected>>')
            self.combo_insumo.unbind('<<ComboboxSelected>>')
        except Exception as e:
            print("Error al desvincular eventos:", e)
        # Limpiar archivo temporal si existe
        if hasattr(self, 'temp_pdf_path') and os.path.exists(self.temp_pdf_path):
            try:
                os.remove(self.temp_pdf_path)
            except:
                pass
    
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
                text="Reporte Tarjeta Kardex",
                font=('Segoe UI', 12, 'bold'),
                fg=self.COLORS['white'],
                bg=self.COLORS['primary']).pack(anchor='w')

        tk.Label(title_inner,
                text="Consulte kardex de los movimientos de los insumos",
                font=('Segoe UI', 8),
                fg=self.COLORS['white'],
                bg=self.COLORS['primary']).pack(anchor='w', pady=(2, 0))

        # Frame principal con título personalizado
        self.frame_principal_container, self.frame_principal = self.create_titled_frame(main_container, "Filtros de Reporte")
        self.frame_principal_container.config(bg=self.COLORS['white'])
        self.frame_principal.config(bg=self.COLORS['white'])
        self.frame_principal_container.pack(fill="both", expand=True, padx=10, pady=5)

        # Frame para fechas con título personalizado
        self.frame_fechas_container, self.frame_fechas = self.create_titled_frame(self.frame_principal, "Selección de Fechas/Corte Logístico")
        self.frame_fechas_container.config(bg=self.COLORS['white'])
        self.frame_fechas.config(bg=self.COLORS['white'])
        self.frame_fechas_container.pack(fill="x", expand=False, padx=5, pady=5)

        # Modo de selección de fechas
        self.modo_fecha_var = tk.StringVar(value="rango")

        # Rango de fechas (fila 0)
        self.frame_fechas.grid_columnconfigure(2, weight=1)
        self.frame_fechas.grid_columnconfigure(4, weight=1)

        self.radio_rango = tk.Radiobutton(
            self.frame_fechas,
            text="Rango de Fechas:",
            variable=self.modo_fecha_var,
            value="rango",
            command=self.actualizar_visibilidad_fechas,
            bg=self.COLORS['white'],
            fg=self.COLORS['text_dark'],
            font=('Segoe UI', 9),
            selectcolor=self.COLORS['white']
        )
        self.radio_rango.grid(row=0, column=0, padx=5, sticky='w')

        tk.Label(self.frame_fechas, text="Fecha Inicial:", 
                bg=self.COLORS['white'], fg=self.COLORS['text_dark'], 
                font=('Segoe UI', 9)).grid(row=0, column=1, padx=5, sticky='w')

        self.fecha_inicial = DateEntry(
            self.frame_fechas,
            width=12,
            date_pattern='dd/mm/yyyy',
            state='normal'
        )
        self.fecha_inicial.grid(row=0, column=2, padx=5, sticky='ew')

        tk.Label(self.frame_fechas, text="Fecha Final:", 
                bg=self.COLORS['white'], fg=self.COLORS['text_dark'], 
                font=('Segoe UI', 9)).grid(row=0, column=3, padx=5, sticky='w')

        self.fecha_final = DateEntry(
            self.frame_fechas,
            width=12,
            date_pattern='dd/mm/yyyy',
            state='normal'
        )
        self.fecha_final.grid(row=0, column=4, padx=5, sticky='ew')

        # Corte logístico (fila 1)
        self.frame_fechas.grid_columnconfigure(6, weight=1)

        self.radio_corte = tk.Radiobutton(
            self.frame_fechas,
            text="Corte Logístico:",
            variable=self.modo_fecha_var,
            value="corte",
            command=self.actualizar_visibilidad_fechas,
            bg=self.COLORS['white'],
            fg=self.COLORS['text_dark'],
            font=('Segoe UI', 9),
            selectcolor=self.COLORS['white']
        )
        self.radio_corte.grid(row=1, column=0, padx=5, sticky='w')

        tk.Label(self.frame_fechas, text="Año:", 
                bg=self.COLORS['white'], fg=self.COLORS['text_dark'], 
                font=('Segoe UI', 9)).grid(row=1, column=1, padx=5, sticky='w')

        self.anio_var = tk.StringVar()
        anios = [str(a) for a in range(datetime.now().year - 5, datetime.now().year + 2)]
        self.combo_anio = ttk.Combobox(
            self.frame_fechas,
            textvariable=self.anio_var,
            values=anios,
            width=8
        )
        self.combo_anio.grid(row=1, column=2, padx=5, sticky='ew')
        self.combo_anio.set(str(datetime.now().year))

        tk.Label(self.frame_fechas, text="Mes Inicio:", 
                bg=self.COLORS['white'], fg=self.COLORS['text_dark'], 
                font=('Segoe UI', 9)).grid(row=1, column=3, padx=5, sticky='w')

        self.mes_inicio_var = tk.StringVar()
        meses = [datetime(2024, m, 1).strftime("%B").capitalize() for m in range(1, 13)]
        self.combo_mes_inicio = ttk.Combobox(
            self.frame_fechas,
            textvariable=self.mes_inicio_var,
            values=meses,
            width=12
        )
        self.combo_mes_inicio.grid(row=1, column=4, padx=5, sticky='ew')

        tk.Label(self.frame_fechas, text="Mes Final:", 
                bg=self.COLORS['white'], fg=self.COLORS['text_dark'], 
                font=('Segoe UI', 9)).grid(row=1, column=5, padx=5, sticky='w')

        self.mes_final_var = tk.StringVar()
        self.combo_mes_final = ttk.Combobox(
            self.frame_fechas,
            textvariable=self.mes_final_var,
            values=meses,
            width=12
        )
        self.combo_mes_final.grid(row=1, column=6, padx=5, sticky='ew')

        # Eventos para actualizar fechas
        self.combo_anio.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte)
        self.combo_mes_inicio.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte)
        self.combo_mes_final.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte)

        # Frame para combos
        self.frame_combos = ttk.Frame(self.frame_principal, style='White.TFrame')
        self.frame_combos.pack(fill="x", expand=False, padx=5, pady=5)

        # Inicializar visibilidad
        self.actualizar_visibilidad_fechas()

        # Primera fila de combos con título personalizado
        self.frame_ubicacion_container, self.frame_ubicacion_content = self.create_titled_frame(self.frame_combos, "Ubicación")
        self.frame_ubicacion_container.config(bg=self.COLORS['white'])
        self.frame_ubicacion_content.config(bg=self.COLORS['white'])
        self.frame_ubicacion_container.pack(fill="x", expand=False, pady=5)

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

        # Segunda fila de combos con título personalizado
        self.frame_insumo_container, self.frame_insumo_content = self.create_titled_frame(self.frame_combos, "Insumo")
        self.frame_insumo_container.config(bg=self.COLORS['white'])
        self.frame_insumo_content.config(bg=self.COLORS['white'])
        self.frame_insumo_container.pack(fill="x", expand=False, pady=5)

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
                            command=self.generar_vista_previa,
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
                            command=self.generar_kardex,
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

        else:
            # Deshabilitar DateEntry
            self.fecha_inicial.config(state="disabled")
            self.fecha_final.config(state="disabled")

            # Habilitar combos de corte
            self.combo_anio.config(state="readonly")
            self.combo_mes_inicio.config(state="readonly")
            self.combo_mes_final.config(state="readonly")

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
                self.combo_distrito.get() if self.combo_distrito.get().strip() else None,
                self.combo_tipo_servicio.get() if self.combo_tipo_servicio.get().strip() else None,
                self.combo_servicio.get() if self.combo_servicio.get().strip() else None,
                self.combo_tipo_insumo.get() if self.combo_tipo_insumo.get().strip() else None,
                self.combo_insumo.get() if self.combo_insumo.get().strip() else None,
                self.combo_presentacion.get() if self.combo_presentacion.get().strip() else None,
                self.combo_area.get() if self.combo_area.get().strip() else None
            )

            if not movimientos_raw:
                messagebox.showinfo("Info", "No hay datos para mostrar")
                return

            movimientos_filtrados = self.filtrar_movimientos_por_nivel(movimientos_raw)
            if not movimientos_filtrados:
                messagebox.showwarning(
                    "Sin datos", 
                    "No hay movimientos para mostrar con los filtros seleccionados."
                )
                return

            movimientos_ordenados = self.ordenar_movimientos(movimientos_filtrados)
            self.movimientos_data = self.calcular_saldo_acumulado(movimientos_ordenados)
            if not self.movimientos_data:
                messagebox.showwarning(
                    "Sin datos", 
                    "No se pudieron procesar los datos para el reporte."
                )
                return

            # --- Generar PDF temporal ---
            import tempfile, os, fitz
            from PIL import Image, ImageTk

            temp_dir = tempfile.gettempdir()
            self.temp_pdf_path = os.path.join(temp_dir, "vista_previa_kardex.pdf")
            self.generar_pdf(self.temp_pdf_path, es_vista_previa=True)

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
            self.canvas = tk.Canvas(
                canvas_frame,
                bg=self.COLORS['white'],
                yscrollcommand=v_scrollbar.set,
                xscrollcommand=h_scrollbar.set
            )
            self.canvas.pack(side="left", fill="both", expand=True)
            v_scrollbar.config(command=self.canvas.yview)
            h_scrollbar.config(command=self.canvas.xview)

            # --- Abrir PDF y preparar navegación ---
            self.pdf_document = fitz.open(self.temp_pdf_path)
            self.current_page = 0
            self.total_pages = len(self.pdf_document)

            # --- Frame de navegación alineado a la izquierda ---
            nav_frame = tk.Frame(control_frame, bg=self.COLORS['white'])
            nav_frame.pack(side="left", padx=0)

            # --- Función para mostrar página ---
            def mostrar_pagina():
                self.canvas.delete("all")
                page = self.pdf_document.load_page(self.current_page)
                pix = page.get_pixmap(matrix=fitz.Matrix(1.2, 1.2))
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                tk_img = ImageTk.PhotoImage(image=img)
                self.canvas.image = tk_img
                self.canvas.create_image(0, 0, anchor="nw", image=tk_img)
                self.canvas.config(scrollregion=self.canvas.bbox("all"))
                self.lbl_pagina.config(text=f"Página {self.current_page + 1} de {self.total_pages}")

            # --- Función para cambiar de página ---
            def change_page(delta):
                nueva_pagina = self.current_page + delta
                if 0 <= nueva_pagina < self.total_pages:
                    self.current_page = nueva_pagina
                    mostrar_pagina()
                # Deshabilitar botones si corresponde
                self.btn_anterior.config(state="normal" if self.current_page > 0 else "disabled")
                self.btn_siguiente.config(state="normal" if self.current_page < self.total_pages - 1 else "disabled")

            # --- Botón página anterior (ESTILO BRES) ---
            self.btn_anterior = tk.Button(
                nav_frame,
                text="◀",
                command=lambda: change_page(-1),
                bg=self.COLORS['white'],
                fg=self.COLORS['text_dark'],
                font=('Segoe UI', 10, 'bold'),
                relief="flat",
                borderwidth=0,
                cursor="hand2",
                activebackground=self.COLORS['white'],
                activeforeground=self.COLORS['text_dark']
            )
            self.btn_anterior.pack(side="left", padx=(10, 2), pady=2)

            # --- Label de información de página (ESTILO BRES) ---
            self.lbl_pagina = tk.Label(
                nav_frame,
                text=f"Página {self.current_page + 1} de {self.total_pages}",
                bg=self.COLORS['white'],
                fg=self.COLORS['text_dark'],
                font=('Segoe UI', 10, 'bold')
            )
            self.lbl_pagina.pack(side="left", padx=2, pady=2)

            # --- Botón página siguiente (ESTILO BRES) ---
            self.btn_siguiente = tk.Button(
                nav_frame,
                text="▶",
                command=lambda: change_page(1),
                bg=self.COLORS['white'],
                fg=self.COLORS['text_dark'],
                font=('Segoe UI', 10, 'bold'),
                relief="flat",
                borderwidth=0,
                cursor="hand2",
                activebackground=self.COLORS['white'],
                activeforeground=self.COLORS['text_dark']
            )
            self.btn_siguiente.pack(side="left", padx=2, pady=2)

            # --- Mostrar la primera página y actualizar botones ---
            mostrar_pagina()
            self.btn_anterior.config(state="disabled")
            if self.total_pages <= 1:
                self.btn_siguiente.config(state="disabled")
            else:
                self.btn_siguiente.config(state="normal")

            # --- Scroll con mouse wheel ---
            def on_mousewheel(event):
                if self.canvas.winfo_exists():
                    self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            self.canvas.bind("<MouseWheel>", on_mousewheel)

        except Exception as e:
            import traceback
            print(traceback.format_exc())
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
                    self.combo_distrito.get() if self.combo_distrito.get().strip() else None,
                    self.combo_tipo_servicio.get() if self.combo_tipo_servicio.get().strip() else None,
                    self.combo_servicio.get() if self.combo_servicio.get().strip() else None,
                    self.combo_tipo_insumo.get() if self.combo_tipo_insumo.get().strip() else None,
                    self.combo_insumo.get() if self.combo_insumo.get().strip() else None,
                    self.combo_presentacion.get() if self.combo_presentacion.get().strip() else None,
                    self.combo_area.get() if self.combo_area.get().strip() else None  # NUEVO PARÁMETRO
                )

                if not movimientos_raw:
                    messagebox.showinfo("Info", "No hay datos para mostrar")
                    return

                # Filtrar movimientos por nivel jerárquico - NUEVA LÍNEA
                movimientos_filtrados = self.filtrar_movimientos_por_nivel(movimientos_raw)

                # VALIDAR SI HAY DATOS DESPUÉS DEL FILTRADO
                if not movimientos_filtrados:
                    messagebox.showwarning(
                        "Sin datos", 
                        "No hay movimientos para mostrar con los filtros seleccionados.\n\n"
                        "Verifique que:\n"
                        "• Existan movimientos en el rango de fechas seleccionado\n"
                        "• Los movimientos estén guardados en el nivel jerárquico seleccionado\n"
                        "• Los filtros de insumo sean correctos"
                    )
                    return  # No generar el reporte si no hay datos

                # Ordenar movimientos y calcular saldo - USAR MOVIMIENTOS FILTRADOS
                movimientos_ordenados = self.ordenar_movimientos(movimientos_filtrados)
                self.movimientos_data = self.calcular_saldo_acumulado(movimientos_ordenados)

                # VALIDAR NUEVAMENTE DESPUÉS DEL PROCESAMIENTO
                if not self.movimientos_data:
                    messagebox.showwarning(
                        "Sin datos", 
                        "No se pudieron procesar los datos para el reporte.\n"
                        "Verifique los filtros seleccionados."
                    )
                    return

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
                    
                    lote_val = mov['lote']
                    if lote_val is None or lote_val == '':
                        lote_val = "N/A"
                    
                    row = [
                        mov['fecha'],
                        mov['referencia'] or "",
                        mov['tipo_movimiento'],
                        mov['entrada'],  
                        mov['precio_unitario'],  
                        mov['valor_total'], 
                        lote_val,
                        mov['fecha_vencimiento'] or "",
                        mov['salida'],  
                        mov['reajuste'],  
                        mov['cantidad_col'],  
                        mov['saldo'],  
                        mov['observaciones'] or ""
                    ]
                    data.append(row)

                # Crear tabla con formato y anchos ajustados
                colWidths = [
                    0.8*inch,  # Fecha (era 0.7)
                    0.9*inch,  # Ref. (era 0.8)
                    1.7*inch,  # Remitente (era 1.5)
                    0.7*inch,  # Entrada (era 0.6)
                    0.8*inch,  # P.Unit. (era 0.7)
                    0.8*inch,  # V.Total (era 0.7)
                    0.9*inch,  # Lote (era 0.8)
                    0.8*inch,  # F.Venc. (era 0.7)
                    0.7*inch,  # Salidas (era 0.6)
                    0.7*inch,  # Reaj. (era 0.6)
                    0.7*inch,  # Cant. (era 0.6)
                    0.7*inch,  # Saldo (era 0.6)
                    1.3*inch   # Obs. (era 1.1
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
                self.combo_distrito.get() if self.combo_distrito.get().strip() else None,
                self.combo_tipo_servicio.get() if self.combo_tipo_servicio.get().strip() else None,
                self.combo_servicio.get() if self.combo_servicio.get().strip() else None,
                self.combo_tipo_insumo.get() if self.combo_tipo_insumo.get().strip() else None,
                self.combo_insumo.get() if self.combo_insumo.get().strip() else None,
                self.combo_presentacion.get() if self.combo_presentacion.get().strip() else None,
                self.combo_area.get() if self.combo_area.get().strip() else None  # NUEVO PARÁMETRO
            )

            if not movimientos_raw:
                messagebox.showinfo("Info", "No hay datos para mostrar")
                return

            # Filtrar movimientos por nivel jerárquico - NUEVA LÍNEA
            movimientos_filtrados = self.filtrar_movimientos_por_nivel(movimientos_raw)

            # VALIDAR SI HAY DATOS DESPUÉS DEL FILTRADO
            if not movimientos_filtrados:
                messagebox.showwarning(
                    "Sin datos", 
                    "No hay movimientos para mostrar con los filtros seleccionados.\n\n"
                    "Verifique que:\n"
                    "• Existan movimientos en el rango de fechas seleccionado\n"
                    "• Los movimientos estén guardados en el nivel jerárquico seleccionado\n"
                    "• Los filtros de insumo sean correctos"
                )
                return  # No generar el reporte si no hay datos

            # Ordenar movimientos y calcular saldo - USAR MOVIMIENTOS FILTRADOS
            movimientos_ordenados = self.ordenar_movimientos(movimientos_filtrados)
            movimientos = self.calcular_saldo_acumulado(movimientos_ordenados)

            # VALIDAR NUEVAMENTE DESPUÉS DEL PROCESAMIENTO
            if not movimientos:
                messagebox.showwarning(
                    "Sin datos", 
                    "No se pudieron procesar los datos para el reporte.\n"
                    "Verifique los filtros seleccionados."
                )
                return

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
                df.to_excel(writer, sheet_name=nombre_hoja, startrow=fila_inicio, index=False, header=False)

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

        # Aplicar formato a fila saldo anterior (si existe)
        if tiene_saldo_anterior:
            worksheet.set_row(fila_inicio, None, saldo_anterior_format)

        # Crear formato para los datos
        data_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 9,
            'border': 1,
            'border_color': '#808080'
        })

        # Aplicar formato a los datos (reescribiendo valores)
        data_start_row = fila_inicio + (1 if tiene_saldo_anterior else 0)
        for row_offset, row_data in enumerate(df.values):
            for col_num, cell_value in enumerate(row_data):
                worksheet.write(data_start_row + row_offset, col_num, cell_value, data_format)

        # Configuración de página
        worksheet.set_landscape()
        worksheet.set_paper(5)
        worksheet.fit_to_pages(1, 1)
        
        # Centrar Hoja
        worksheet.center_horizontally()

        # Ajustar anchos de columna
        worksheet.set_column('A:A', 10)    # Fecha
        worksheet.set_column('B:B', 12)    # No. Referencia
        worksheet.set_column('C:C', 20)    # Remitente/Destinatario
        worksheet.set_column('D:D', 10)    # Entrada
        worksheet.set_column('E:E', 10)    # Precio Unitario
        worksheet.set_column('F:F', 10)    # Valor Total

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
        """
        Filtra los movimientos según el nivel jerárquico seleccionado.
        Solo muestra movimientos que fueron guardados exactamente en el nivel seleccionado.
        """
        # Obtener valores seleccionados
        area_seleccionada = self.combo_area.get().strip()
        distrito_seleccionado = self.combo_distrito.get().strip()
        tipo_servicio_seleccionado = self.combo_tipo_servicio.get().strip()
        servicio_seleccionado = self.combo_servicio.get().strip()
        
        # Si no hay ningún filtro de ubicación, devolver todos los movimientos
        if not any([area_seleccionada, distrito_seleccionado, tipo_servicio_seleccionado, servicio_seleccionado]):
            return movimientos
        
        movimientos_filtrados = []
        
        for mov in movimientos:
            # Obtener datos del movimiento - manejar NULL/None correctamente
            mov_area = mov.get('area_nombre')
            mov_distrito = mov.get('distrito_nombre')
            mov_tipo_servicio = mov.get('tipo_servicio_desc')
            mov_servicio = mov.get('servicio_nombre')
            
            # Función auxiliar para verificar si un campo está vacío/nulo
            def es_nulo_o_vacio(valor):
                return valor is None or valor == '' or str(valor).strip() == '' or str(valor).lower() in ['null', 'none']
            
            incluir_movimiento = False
            
            # CASO 1: Solo se seleccionó ÁREA
            if area_seleccionada and not distrito_seleccionado and not tipo_servicio_seleccionado and not servicio_seleccionado:
                # Incluir si: área coincide Y distrito/tipo_servicio/servicio son NULL/None/vacío
                if (mov_area == area_seleccionada and 
                    es_nulo_o_vacio(mov_distrito) and 
                    es_nulo_o_vacio(mov_tipo_servicio) and 
                    es_nulo_o_vacio(mov_servicio)):
                    incluir_movimiento = True
            
            # CASO 2: Se seleccionó ÁREA + DISTRITO
            elif area_seleccionada and distrito_seleccionado and not tipo_servicio_seleccionado and not servicio_seleccionado:
                # Incluir si: área y distrito coinciden Y tipo_servicio/servicio son NULL/None/vacío
                if (mov_area == area_seleccionada and 
                    mov_distrito == distrito_seleccionado and 
                    es_nulo_o_vacio(mov_tipo_servicio) and 
                    es_nulo_o_vacio(mov_servicio)):
                    incluir_movimiento = True
            
            # CASO 3: Se seleccionó ÁREA + DISTRITO + TIPO DE SERVICIO
            elif area_seleccionada and distrito_seleccionado and tipo_servicio_seleccionado and not servicio_seleccionado:
                # Incluir si: área, distrito y tipo_servicio coinciden Y servicio es NULL/None/vacío
                if (mov_area == area_seleccionada and 
                    mov_distrito == distrito_seleccionado and 
                    mov_tipo_servicio == tipo_servicio_seleccionado and 
                    es_nulo_o_vacio(mov_servicio)):
                    incluir_movimiento = True
            
            # CASO 4: Se seleccionó ÁREA + DISTRITO + TIPO DE SERVICIO + SERVICIO
            elif area_seleccionada and distrito_seleccionado and tipo_servicio_seleccionado and servicio_seleccionado:
                # Incluir si: todos los niveles coinciden exactamente
                if (mov_area == area_seleccionada and 
                    mov_distrito == distrito_seleccionado and 
                    mov_tipo_servicio == tipo_servicio_seleccionado and 
                    mov_servicio == servicio_seleccionado):
                    incluir_movimiento = True
            
            if incluir_movimiento:
                movimientos_filtrados.append(mov)
        
        return movimientos_filtrados
    
    def destroy(self):
        if hasattr(self, 'frame_principal'):
            self.frame_principal.destroy()