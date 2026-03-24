# Imports existentes
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
from reportlab.lib.pagesizes import landscape, legal
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Agregar el directorio raíz del proyecto al PATH de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.gui import styles
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

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        # En desarrollo, base_path es la raíz del proyecto (subir un nivel desde gui)
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(base_path, relative_path)

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

        # Crear estilos locales de TFrame (no globales)
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
        # Paleta compartida del sistema
        self.COLORS = styles.COLORS

        # Solo estilos locales, sin imponer tema global
        style = ttk.Style(self.parent if hasattr(self, 'parent') else None)
        # No forzamos theme_use globalmente

        # Frames base
        style.configure('White.TFrame', background=self.COLORS['light'])
        style.configure('Enabled.TFrame', background=self.COLORS['white'])
        style.configure('Disabled.TFrame', background='#f0f0f0')

        # Labels y botones base (opcionales, no cambian globales)
        style.configure(
            'White.TLabel',
            background=self.COLORS['light'],
            foreground=self.COLORS['text_dark'],
            font=('Segoe UI', 9)
        )
        style.configure(
            'White.TButton',
            background=self.COLORS['light'],
            foreground=self.COLORS['text_dark'],
            font=('Segoe UI', 9),
            relief='flat',
            borderwidth=0
        )
        style.map(
            'White.TButton',
            background=[('active', self.COLORS['light']), ('pressed', self.COLORS['light'])]
        )

        # Botón primario local
        style.configure(
            'Primary.TButton',
            font=('Segoe UI', 9, 'bold'),
            padding=(12, 6),
            relief='flat',
            borderwidth=0,
            background=self.COLORS['accent'],
            foreground=self.COLORS['white']
        )
        style.map(
            'Primary.TButton',
            background=[('active', '#2980b9'), ('pressed', '#117a8b')],
            foreground=[('active', '#ffff'), ('pressed', '#ffff')]
        )

        # Popups de lista (opcional, no invasivo)
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

        style.configure('TCombobox', fieldbackground=self.COLORS['white'], background=self.COLORS['light'], foreground=self.COLORS['text_dark'])
        style.configure('TEntry', selectbackground=self.COLORS['accent'], selectforeground='#ffff')

    def create_titled_frame(self, parent, title, header_icon=None):
        # Contenedor tipo tarjeta sobre fondo Light
        container = tk.Frame(parent, bg=self.COLORS['light'], relief='solid', borderwidth=1)

        # Header compacto
        header = tk.Frame(container, bg=self.COLORS['primary'], height=16)
        header.pack(fill='x')
        header.pack_propagate(False)

        # Mini-ícono opcional
        if header_icon:
            tk.Label(
                header, text=header_icon,
                font=('Segoe UI Emoji', 8),
                fg=self.COLORS['white'], bg=self.COLORS['primary']
            ).pack(side='left', padx=(8, 3))

        # Título
        tk.Label(
            header, text=title,
            font=('Segoe UI', 7, 'bold'),
            fg=self.COLORS['white'], bg=self.COLORS['primary']
        ).pack(side='left', padx=2, pady=1)

        # Contenido en Light
        content = tk.Frame(container, bg=self.COLORS['light'])
        content.pack(fill='both', expand=True, padx=6, pady=4)

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

    def mostrar_mensaje_inicial(self):
        """Muestra mensaje inicial antes de generar vista previa"""
        for widget in self.pdf_body.winfo_children():
            widget.destroy()
        
        # Resetear atributos de animación
        self._icon_size = 64
        self._icon_direction = -1
        
        initial_frame = tk.Frame(self.pdf_body, bg=self.COLORS['white'])
        initial_frame.pack(expand=True)
        
        # Ícono animado
        self.initial_icon = tk.Label(
            initial_frame, 
            text="📋", 
            font=('Segoe UI Emoji', 64),
            fg=self.COLORS['accent'], 
            bg=self.COLORS['white']
        )
        self.initial_icon.pack(pady=(80, 20))
        
        # Texto principal
        tk.Label(
            initial_frame,
            text="Seleccione los filtros y genere la vista previa",
            font=('Segoe UI', 13, 'bold'),
            fg=self.COLORS['text_dark'],
            bg=self.COLORS['white']
        ).pack(pady=(0, 8))
        
        # Texto secundario
        tk.Label(
            initial_frame,
            text="Configure las fechas y filtros deseados, luego presione 'Generar Vista Previa'",
            font=('Segoe UI', 9),
            fg=self.COLORS['text_light'],
            bg=self.COLORS['white']
        ).pack(pady=(0, 5))
               
    def mostrar_animacion_carga(self):
        """Muestra animación de carga mientras se genera el reporte"""
        for widget in self.pdf_body.winfo_children():
            widget.destroy()
        
        loading_frame = tk.Frame(self.pdf_body, bg=self.COLORS['white'])
        loading_frame.pack(expand=True)
        
        self.loading_label = tk.Label(
            loading_frame, 
            text="⏳", 
            font=('Segoe UI Emoji', 48),
            fg=self.COLORS['accent'], 
            bg=self.COLORS['white']
        )
        self.loading_label.pack(pady=(50, 10))
        
        self.loading_text = tk.Label(
            loading_frame, 
            text="Generando reporte",
            font=('Segoe UI', 11, 'bold'), 
            fg=self.COLORS['accent'],
            bg=self.COLORS['white']
        )
        self.loading_text.pack()
        
        # Texto secundario
        tk.Label(
            loading_frame,
            text="Por favor espere mientras se procesa la información...",
            font=('Segoe UI', 9),
            fg=self.COLORS['text_light'],
            bg=self.COLORS['white']
        ).pack(pady=(5, 0))
        
        self.loading_dots = 0
    
    def ordenar_movimientos(self, movimientos):
        """
        1) Fecha (día) ascendente
        2) Dentro del mismo día: POSITIVOS (1) -> NEGATIVOS (2) -> NO ENTREGADO (3) -> otros (4)
        3) Desempate: hora (si existe) y por último (referencia, tipo) para estabilidad
        """
        from datetime import datetime, date as _date

        POSITIVOS = {'INVENTARIO INICIAL', 'ENTRADA NIVEL SUPERIOR', 'REAJUSTE (+)', 'REAJUSTE POSITIVO'}
        NEGATIVOS = {'SALIDA NIVEL INFERIOR', 'REAJUSTE (-)', 'REAJUSTE NEGATIVO', 'ENTREGADO'}
        INDIFERENTE = {'NO ENTREGADO'}

        def prioridad_tipo(tipo_mov):
            t = (tipo_mov or '').strip().upper()
            if t in POSITIVOS:
                return 1
            if t in NEGATIVOS:
                return 2
            if t in INDIFERENTE:
                return 3
            return 4

        # Parser robusto: devuelve (fecha_dia: date, hora_tuple: (hh,mm,ss) o (99,99,99) si sin hora)
        def parse_fecha(f):
            if f is None or f == '':
                return (_date.max, (99, 99, 99))
            # datetime/date
            try:
                if isinstance(f, datetime):
                    return (f.date(), (f.hour, f.minute, f.second))
                if hasattr(f, 'strftime'):  # date
                    return (f, (99, 99, 99))
            except Exception:
                pass
            # string
            if isinstance(f, str):
                f_str = f.strip()
                formatos = [
                    '%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S',
                    '%d/%m/%Y %H:%M:%S', '%d-%m-%Y %H:%M:%S',
                    '%Y-%m-%d', '%Y/%m/%d',
                    '%d/%m/%Y', '%d-%m-%Y',
                ]
                for fmt in formatos:
                    try:
                        dt = datetime.strptime(f_str, fmt)
                        if 'H' in fmt:
                            return (dt.date(), (dt.hour, dt.minute, dt.second))
                        return (dt.date(), (99, 99, 99))
                    except Exception:
                        continue
            # No se pudo parsear → al final
            return (_date.max, (99, 99, 99))

        def tie_key(m):
            # Estabilidad extra
            ref = str(m.get('referencia', '') or '').strip()
            tipo = str(m.get('tipo_movimiento', '') or '').strip().upper()
            return (ref, tipo)

        def sort_key(m):
            fecha_dia, hora = parse_fecha(m.get('fecha'))
            prio = prioridad_tipo(m.get('tipo_movimiento'))
            return (fecha_dia, prio, hora, tie_key(m))

        return sorted(movimientos, key=sort_key)

    def calcular_saldo_acumulado(self, movimientos_ordenados):
        saldo = 0.0
        movimientos_con_saldo = []

        INDIFERENTE = {'NO ENTREGADO'}

        def parse_cantidad(mov):
            posibles = [
                'cantidad', 'cantidad_movimiento', 'cantidad_entrada', 'cantidad_salida',
                'qty', 'quantity', 'cant', 'valor_cantidad'
            ]
            for campo in posibles:
                if campo in mov and mov[campo] not in (None, ''):
                    try:
                        return float(mov[campo])
                    except Exception:
                        pass
            for k, v in mov.items():
                if 'cantidad' in str(k).lower() and v not in (None, ''):
                    try:
                        return float(v)
                    except Exception:
                        pass
            return 0.0

        for mov in movimientos_ordenados:
            tipo_raw = mov.get('tipo_movimiento', '')
            tipo = (tipo_raw or '').strip().upper()

            cantidad = parse_cantidad(mov)

            # Fechas
            def _fmt_ddmmyyyy(f):
                # Devuelve dd/mm/YYYY (sin hora) o "" si no se puede
                from datetime import datetime
                if not f:
                    return ""
                if hasattr(f, 'strftime'):
                    try:
                        # si es datetime, tomar solo fecha
                        if hasattr(f, 'date'):
                            try:
                                return f.strftime('%d/%m/%Y') if not isinstance(f, datetime) else f.date().strftime('%d/%m/%Y')
                            except Exception:
                                pass
                        return f.strftime('%d/%m/%Y')
                    except Exception:
                        return ""
                if isinstance(f, str):
                    f_str = f.strip()
                    formatos = [
                        '%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S',
                        '%d/%m/%Y %H:%M:%S', '%d-%m-%Y %H:%M:%S',
                        '%Y-%m-%d', '%Y/%m/%d',
                        '%d/%m/%Y', '%d-%m-%Y',
                    ]
                    for fmt in formatos:
                        try:
                            dt = datetime.strptime(f_str, fmt)
                            return dt.strftime('%d/%m/%Y')
                        except Exception:
                            continue
                return ""

            fecha_registro = _fmt_ddmmyyyy(mov.get('fecha', ''))
            fv_raw = mov.get('fecha_vencimiento')
            fecha_vencimiento = "N/A" if fv_raw in (None, '') else _fmt_ddmmyyyy(fv_raw) or "N/A"
            
            lote_val = mov.get('lote')
            lote_val = "N/A" if lote_val in (None, '') else lote_val

            # Remitente/Destinatario (humano para salidas a nivel inferior)
            remit_dest = tipo_raw
            if tipo == 'SALIDA NIVEL INFERIOR':
                # Priorizar servicio_destino sobre distrito_destino
                if mov.get('servicio_destino'):
                    remit_dest = mov.get('servicio_destino')
                elif mov.get('distrito_destino'):
                    remit_dest = mov.get('distrito_destino')

            # Columnas
            entrada = ""
            salida = ""
            reajuste = ""
            cantidad_col = self.formato_float(cantidad)  # SIEMPRE mostrar aquí

            # INVENTARIO INICIAL: no va en 'Entrada', solo 'Cantidad', pero sí suma saldo
            if tipo == 'INVENTARIO INICIAL':
                saldo += cantidad

            elif tipo in ('ENTRADA NIVEL SUPERIOR',):
                entrada = self.formato_float(cantidad)  # ENTRADA sí va a 'Entrada'
                saldo += cantidad

            elif tipo in ('REAJUSTE (+)', 'REAJUSTE POSITIVO'):
                reajuste = f"+{self.formato_float(cantidad)}" if cantidad > 0 else "+0.00"
                saldo += cantidad

            elif tipo in ('REAJUSTE (-)', 'REAJUSTE NEGATIVO'):
                reajuste = f"-{self.formato_float(cantidad)}" if cantidad > 0 else "-0.00"
                saldo -= cantidad

            elif tipo in ('SALIDA NIVEL INFERIOR', 'ENTREGADO'):
                salida = self.formato_float(cantidad)  # SALIDAS sí van a 'Salidas'
                saldo -= cantidad

            elif tipo in INDIFERENTE:  # NO ENTREGADO
                # No afecta saldo, y NO debe mostrarse en 'Salidas'
                # Solo mostrar su cantidad en 'Cantidad'
                pass

            movimientos_con_saldo.append({
                'fecha': fecha_registro,
                'referencia': mov.get('referencia', ''),
                'tipo_movimiento': remit_dest,
                'entrada': entrada,
                'precio_unitario': "",
                'valor_total': "",
                'lote': lote_val,
                'fecha_vencimiento': fecha_vencimiento,
                'salida': salida,
                'reajuste': reajuste,
                'cantidad_col': cantidad_col,
                'saldo': self.formato_float(saldo),
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
            if isinstance(fecha, str):
                formatos_entrada = [
                    '%Y-%m-%d',
                    '%Y/%m/%d',
                    '%d-%m-%Y',
                    '%d/%m/%Y',
                    '%Y-%m-%d %H:%M:%S',
                    '%Y/%m/%d %H:%M:%S'
                ]
                for formato in formatos_entrada:
                    try:
                        fecha_obj = datetime.strptime(fecha, formato)
                        return fecha_obj.strftime('%d/%m/%Y')
                    except ValueError:
                        continue
                return fecha
            elif hasattr(fecha, 'strftime'):
                return fecha.strftime('%d/%m/%Y')
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
            except:  # noqa: E722
                pass
        # Destruir contenedor principal si existe
        if hasattr(self, 'main_container'):
            try:
                self.main_container.destroy()
            except Exception:
                pass

    def setup_ui(self):
        # --- Frame principal que contendrá todo ---
        self.main_container = tk.Frame(self.parent, bg=self.COLORS['light'])
        self.main_container.pack(fill="both", expand=True)

        # Franja superior azul para pegar el header al tope
        top_strip = tk.Frame(self.main_container, bg=self.COLORS['primary'], height=6)
        top_strip.pack(fill='x', padx=0, pady=0)
        top_strip.pack_propagate(False)
        
        # --- Título principal (más compacto) ---
        title_frame = tk.Frame(self.main_container, bg=self.COLORS['primary'], height=55) 
        title_frame.pack(fill='x', padx=0)
        title_frame.pack_propagate(False)

        title_inner = tk.Frame(title_frame, bg=self.COLORS['primary'])
        title_inner.pack(fill='both', expand=True, padx=15, pady=5)  

        tk.Label(
            title_inner,
            text="📒 Reporte Tarjeta Kardex",
            font=('Segoe UI', 10, 'bold'),  
            fg=self.COLORS['white'],
            bg=self.COLORS['primary']
        ).pack(anchor='w')

        tk.Label(
            title_inner,
            text="Consulte kardex de los movimientos de los insumos",
            font=('Segoe UI', 7), 
            fg=self.COLORS['white'],
            bg=self.COLORS['primary']
        ).pack(anchor='w', pady=(1, 0))  

        # Frame para fechas con título personalizado (más compacto)
        self.frame_fechas_container, self.frame_fechas = self.create_titled_frame(
            self.main_container, "📅 Selección de Fechas/Corte Logístico", header_icon=None
        )
        self.frame_fechas_container.config(bg=self.COLORS['light'])
        self.frame_fechas.config(bg=self.COLORS['light'])
        self.frame_fechas_container.pack(fill="x", expand=False, padx=5, pady=(3, 2))  

        # Modo de selección de fechas (más compacto)
        self.modo_fecha_var = tk.StringVar(value="rango")

        # Rango de fechas
        self.frame_fechas.grid_columnconfigure(2, weight=1)
        self.frame_fechas.grid_columnconfigure(4, weight=1)

        self.radio_rango = tk.Radiobutton(
            self.frame_fechas,
            text="Rango de Fechas:",
            variable=self.modo_fecha_var,
            value="rango",
            command=self.actualizar_visibilidad_fechas,
            bg=self.COLORS['light'],
            fg=self.COLORS['text_dark'],
            font=('Segoe UI', 8), 
            selectcolor=self.COLORS['white']
        )
        self.radio_rango.grid(row=0, column=0, padx=5, pady=1, sticky='w') 

        tk.Label(self.frame_fechas, text="Fecha Inicial:", bg=self.COLORS['light'], 
                fg=self.COLORS['text_dark'], font=('Segoe UI', 8)).grid(row=0, column=1, padx=5, pady=1, sticky='w')
        self.fecha_inicial = DateEntry(self.frame_fechas, width=12, date_pattern='dd/mm/yyyy', state='normal')
        self.fecha_inicial.grid(row=0, column=2, padx=5, pady=1, sticky='ew')

        tk.Label(self.frame_fechas, text="Fecha Final:", bg=self.COLORS['light'], 
                fg=self.COLORS['text_dark'], font=('Segoe UI', 8)).grid(row=0, column=3, padx=5, pady=1, sticky='w')
        self.fecha_final = DateEntry(self.frame_fechas, width=12, date_pattern='dd/mm/yyyy', state='normal')
        self.fecha_final.grid(row=0, column=4, padx=5, pady=1, sticky='ew')

        # Corte logístico (más compacto)
        self.frame_fechas.grid_columnconfigure(6, weight=1)
        self.radio_corte = tk.Radiobutton(
            self.frame_fechas,
            text="Corte Logístico:",
            variable=self.modo_fecha_var,
            value="corte",
            command=self.actualizar_visibilidad_fechas,
            bg=self.COLORS['light'],
            fg=self.COLORS['text_dark'],
            font=('Segoe UI', 8),  # ✅ Reducido de 9 a 8
            selectcolor=self.COLORS['white']
        )
        self.radio_corte.grid(row=1, column=0, padx=5, pady=1, sticky='w')

        tk.Label(self.frame_fechas, text="Año:", bg=self.COLORS['light'], 
                fg=self.COLORS['text_dark'], font=('Segoe UI', 8)).grid(row=1, column=1, padx=5, pady=1, sticky='w')
        self.anio_var = tk.StringVar()
        anios = [str(a) for a in range(datetime.now().year - 5, datetime.now().year + 2)]
        self.combo_anio = ttk.Combobox(self.frame_fechas, textvariable=self.anio_var, values=anios, width=8)
        self.combo_anio.grid(row=1, column=2, padx=5, pady=1, sticky='ew')
        self.combo_anio.set(str(datetime.now().year))

        tk.Label(self.frame_fechas, text="Mes Inicio:", bg=self.COLORS['light'], 
                fg=self.COLORS['text_dark'], font=('Segoe UI', 8)).grid(row=1, column=3, padx=5, pady=1, sticky='w')
        self.mes_inicio_var = tk.StringVar()
        meses = [datetime(2024, m, 1).strftime("%B").capitalize() for m in range(1, 13)]
        self.combo_mes_inicio = ttk.Combobox(self.frame_fechas, textvariable=self.mes_inicio_var, values=meses, width=12)
        self.combo_mes_inicio.grid(row=1, column=4, padx=5, pady=1, sticky='ew')

        tk.Label(self.frame_fechas, text="Mes Final:", bg=self.COLORS['light'], 
                fg=self.COLORS['text_dark'], font=('Segoe UI', 8)).grid(row=1, column=5, padx=5, pady=1, sticky='w')
        self.mes_final_var = tk.StringVar()
        self.combo_mes_final = ttk.Combobox(self.frame_fechas, textvariable=self.mes_final_var, values=meses, width=12)
        self.combo_mes_final.grid(row=1, column=6, padx=5, pady=1, sticky='ew')

        # Eventos para actualizar fechas
        self.combo_anio.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte)
        self.combo_mes_inicio.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte)
        self.combo_mes_final.bind('<<ComboboxSelected>>', self.actualizar_fechas_por_corte)

        # Frame de botones: empaquetar ANTES de frame_combos para que el
        # pack manager le reserve su espacio antes de que expand=True lo consuma
        self.frame_botones = tk.Frame(self.main_container, bg=self.COLORS['light'], height=48)
        self.frame_botones.pack(fill="x", side="bottom", pady=(4, 6))
        self.frame_botones.pack_propagate(False)

        # Frame para combos (expand=True toma el espacio restante)
        self.frame_combos = ttk.Frame(self.main_container, style='White.TFrame')
        self.frame_combos.pack(fill="both", expand=True, padx=5, pady=0)

        # Inicializar visibilidad
        self.actualizar_visibilidad_fechas()

        # Primera fila de combos (más compacta)
        self.frame_ubicacion_container, self.frame_ubicacion_content = self.create_titled_frame(
            self.frame_combos, "📍 Ubicación", header_icon=None
        )
        self.frame_ubicacion_container.config(bg=self.COLORS['light'])
        self.frame_ubicacion_content.config(bg=self.COLORS['light'])
        self.frame_ubicacion_container.pack(fill="x", expand=False, pady=(0, 2))  
        self.frame_ubicacion_content.grid_columnconfigure(1, weight=1)
        self.frame_ubicacion_content.grid_columnconfigure(3, weight=1)
        self.frame_ubicacion_content.grid_columnconfigure(5, weight=1)
        self.frame_ubicacion_content.grid_columnconfigure(7, weight=1)

        label_style = {'style': 'White.TLabel'}
        ttk.Label(self.frame_ubicacion_content, text="Área:", **label_style).grid(row=0, column=0, padx=5, pady=2, sticky='w')
        self.area_var = tk.StringVar()
        self.combo_area = AutocompleteCombobox(self.frame_ubicacion_content, textvariable=self.area_var, 
                                            state="normal", font=('Segoe UI', 8))  
        self.combo_area.grid(row=0, column=1, padx=5, pady=2, sticky='ew')

        ttk.Label(self.frame_ubicacion_content, text="Distrito:", **label_style).grid(row=0, column=2, padx=5, pady=2, sticky='w')
        self.distrito_var = tk.StringVar()
        self.combo_distrito = AutocompleteCombobox(self.frame_ubicacion_content, textvariable=self.distrito_var, 
                                                state="normal", font=('Segoe UI', 8))
        self.combo_distrito.grid(row=0, column=3, padx=5, pady=2, sticky='ew')

        ttk.Label(self.frame_ubicacion_content, text="Tipo de Servicio:", **label_style).grid(row=0, column=4, padx=5, pady=2, sticky='w')
        self.tipo_servicio_var = tk.StringVar()
        self.combo_tipo_servicio = AutocompleteCombobox(self.frame_ubicacion_content, textvariable=self.tipo_servicio_var, 
                                                        state="normal", font=('Segoe UI', 8))
        self.combo_tipo_servicio.grid(row=0, column=5, padx=5, pady=2, sticky='ew')

        ttk.Label(self.frame_ubicacion_content, text="Servicio:", **label_style).grid(row=0, column=6, padx=5, pady=2, sticky='w')
        self.servicio_var = tk.StringVar()
        self.combo_servicio = AutocompleteCombobox(self.frame_ubicacion_content, textvariable=self.servicio_var, 
                                                state="normal", font=('Segoe UI', 8))
        self.combo_servicio.grid(row=0, column=7, padx=5, pady=2, sticky='ew')

        # Segunda fila de combos (más compacta)
        self.frame_insumo_container, self.frame_insumo_content = self.create_titled_frame(
            self.frame_combos, "💊 Insumo", header_icon=None
        )
        self.frame_insumo_container.config(bg=self.COLORS['light'])
        self.frame_insumo_content.config(bg=self.COLORS['light'])
        self.frame_insumo_container.pack(fill="x", expand=False, pady=(0, 2))  

        self.frame_insumo_content.grid_columnconfigure(1, weight=1, minsize=150)
        self.frame_insumo_content.grid_columnconfigure(3, weight=3, minsize=350)
        self.frame_insumo_content.grid_columnconfigure(5, weight=1, minsize=150)

        ttk.Label(self.frame_insumo_content, text="Tipo de Insumo:", **label_style).grid(row=0, column=0, padx=5, pady=2, sticky='w')
        self.tipo_insumo_var = tk.StringVar()
        self.combo_tipo_insumo = AutocompleteCombobox(self.frame_insumo_content, textvariable=self.tipo_insumo_var, 
                                                    state="normal", font=('Segoe UI', 8))
        self.combo_tipo_insumo.grid(row=0, column=1, padx=5, pady=2, sticky='ew')

        ttk.Label(self.frame_insumo_content, text="Insumo:", **label_style).grid(row=0, column=2, padx=5, pady=2, sticky='w')
        self.insumo_var = tk.StringVar()
        self.combo_insumo = AutocompleteCombobox(self.frame_insumo_content, textvariable=self.insumo_var, 
                                                state="normal", font=('Segoe UI', 8))
        self.combo_insumo.grid(row=0, column=3, padx=5, pady=2, sticky='ew')

        ttk.Label(self.frame_insumo_content, text="Presentación:", **label_style).grid(row=0, column=4, padx=5, pady=2, sticky='w')
        self.presentacion_var = tk.StringVar()
        self.combo_presentacion = AutocompleteCombobox(self.frame_insumo_content, textvariable=self.presentacion_var, 
                                                    state="normal", font=('Segoe UI', 8))
        self.combo_presentacion.grid(row=0, column=5, padx=5, pady=2, sticky='ew')

        # --- Visor PDF con encabezado, borde y MAYOR ALTURA ---
        self.pdf_outer = tk.Frame(self.frame_combos, bg=self.COLORS['white'])
        self.pdf_outer.pack(fill="both", expand=True, pady=(0, 0))

        self.pdf_frame = tk.Frame(self.pdf_outer, bg=self.COLORS['white'], relief="solid", bd=1, highlightthickness=0)
        self.pdf_frame.pack(fill="both", expand=True)
        self.pdf_frame.configure(height=550)
        self.pdf_frame.pack_propagate(False)

        self.pdf_header = tk.Frame(self.pdf_frame, bg=self.COLORS['primary'], height=22)
        self.pdf_header.pack(fill="x")
        self.pdf_header.pack_propagate(False)

        tk.Label(
            self.pdf_header,
            text="🖼️ Vista previa del PDF",
            font=('Segoe UI', 8, 'bold'),
            fg=self.COLORS['white'],
            bg=self.COLORS['primary']
        ).pack(side="left", padx=8, pady=1)

        self.pdf_body = tk.Frame(self.pdf_frame, bg=self.COLORS['white'])
        self.pdf_body.pack(fill="both", expand=True, padx=6, pady=6)

        self.mostrar_mensaje_inicial()
        
        # --- Frame para botones (abajo) ---
        btn_font = ('Segoe UI', 9, 'bold')
        btn_bg = self.COLORS['light']
        btn_fg = self.COLORS['text_dark']

        btn_preview = tk.Button(
            self.frame_botones,
            text="Generar Vista Previa",
            command=self.generar_vista_previa,
            font=btn_font, bg=btn_bg, fg=btn_fg,
            relief='flat', borderwidth=0,
            highlightthickness=0, padx=15, pady=4,
            cursor='hand2',
            image=self.icon_preview, compound='left'
        )
        btn_preview.pack(side="left", padx=5, pady=4)

        btn_print = tk.Button(
            self.frame_botones,
            text="Imprimir",
            command=self.imprimir_pdf,
            font=btn_font, bg=btn_bg, fg=btn_fg,
            relief='flat', borderwidth=0,
            highlightthickness=0, padx=15, pady=4,
            cursor='hand2',
            image=self.icon_print, compound='left'
        )
        btn_print.pack(side="left", padx=5, pady=4)

        btn_pdf = tk.Button(
            self.frame_botones,
            text="Exportar a PDF",
            command=self.exportar_pdf,
            font=btn_font, bg=btn_bg, fg=btn_fg,
            relief='flat', borderwidth=0,
            highlightthickness=0, padx=15, pady=4,
            cursor='hand2',
            image=self.icon_pdf, compound='left'
        )
        btn_pdf.pack(side="left", padx=5, pady=4)

        btn_excel = tk.Button(
            self.frame_botones,
            text="Exportar a Excel",
            command=self.generar_kardex,
            font=btn_font, bg=btn_bg, fg=btn_fg,
            relief='flat', borderwidth=0,
            highlightthickness=0, padx=15, pady=4,
            cursor='hand2',
            image=self.icon_excel, compound='left'
        )
        btn_excel.pack(side="left", padx=5, pady=4)

        btn_close = tk.Button(
            self.frame_botones,
            text="Cerrar",
            command=self.cerrar_ventana,
            font=btn_font, bg=btn_bg, fg=btn_fg,
            relief='flat', borderwidth=0,
            highlightthickness=0, padx=15, pady=4,
            cursor='hand2',
            image=self.icon_close, compound='left'
        )
        btn_close.pack(side="right", padx=5, pady=4)

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
        """
        Calcula el rango de fechas para el corte logístico.
        Retorna (fecha_inicial, fecha_final) en formato dd/mm/yyyy
        """
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
        """
        Actualiza las fechas en los DateEntry cuando se selecciona año y meses
        """
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
        
        # Mostrar animación de carga
        self.mostrar_animacion_carga()
        self.parent.update()
        
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
                fecha_ini_str, fecha_fin_str = self.calcular_rango_corte_logistico(anio, mes_inicio, mes_final)
                fecha_ini = datetime.strptime(fecha_ini_str, '%d/%m/%Y')
                fecha_fin = datetime.strptime(fecha_fin_str, '%d/%m/%Y')

            if fecha_fin < fecha_ini:
                messagebox.showerror("Error", "La fecha final debe ser mayor a la inicial")
                return

            if not self.combo_insumo.get():
                messagebox.showerror("Error", "Debe seleccionar un insumo")
                return

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
                messagebox.showwarning("Sin datos", "No hay movimientos para mostrar con los filtros seleccionados.")
                return

            movimientos_ordenados = self.ordenar_movimientos(movimientos_filtrados)
            self.movimientos_data = self.calcular_saldo_acumulado(movimientos_ordenados)
            if not self.movimientos_data:
                messagebox.showwarning("Sin datos", "No se pudieron procesar los datos para el reporte.")
                return

            # --- Generar PDF temporal ---
            import tempfile
            import fitz
            from PIL import Image, ImageTk

            temp_dir = tempfile.gettempdir()
            self.temp_pdf_path = os.path.join(temp_dir, "vista_previa_kardex.pdf")
            self.generar_pdf(self.temp_pdf_path, es_vista_previa=True)

            # --- Limpiar visor PDF (solo el cuerpo) ---
            body_target = getattr(self, 'pdf_body', self.pdf_frame)
            for widget in body_target.winfo_children():
                widget.destroy()

            contenedor = tk.Frame(body_target, bg=self.COLORS['white'])
            contenedor.pack(fill="both", expand=True)

            control_frame = tk.Frame(contenedor, bg=self.COLORS['white'])
            control_frame.pack(fill="x", side="bottom", pady=5)

            canvas_frame = tk.Frame(contenedor, bg=self.COLORS['white'])
            canvas_frame.pack(side="top", fill="both", expand=True)

            v_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical")
            v_scrollbar.pack(side="right", fill="y")
            h_scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal")
            h_scrollbar.pack(side="bottom", fill="x")

            canvas = tk.Canvas(canvas_frame, bg=self.COLORS['white'], yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set, highlightthickness=0, bd=0)
            canvas.pack(side="left", fill="both", expand=True)
            v_scrollbar.config(command=canvas.yview)
            h_scrollbar.config(command=canvas.xview)

            doc = fitz.open(self.temp_pdf_path)
            self.current_page = 0
            self.total_pages = len(doc)
            self.zoom_level = 1.0

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

            # Ajustar al ancho solo una vez cuando esté listo
            def ajustar_una_vez(event=None):
                try:
                    canvas_width = canvas.winfo_width()
                    if canvas_width > 100:
                        page = doc.load_page(self.current_page)
                        zoom = (canvas_width - 20) / page.rect.width
                        self.zoom_level = max(0.5, min(zoom, 3.0))
                        canvas.delete("all")
                        pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom_level, self.zoom_level))
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        tk_img = ImageTk.PhotoImage(image=img)
                        canvas.image = tk_img
                        x = max((canvas_width - pix.width) // 2, 0)
                        canvas.create_image(x, 0, anchor="nw", image=tk_img)
                        canvas.config(scrollregion=canvas.bbox("all"))
                        zoom_label.config(text=f"Zoom: {int(self.zoom_level * 100)}%")
                        canvas.unbind("<Map>")  # Desvincula para que solo se ejecute una vez
                except Exception as e:
                    print(f"Error en ajustar_una_vez: {e}")

            canvas.bind("<Map>", ajustar_una_vez)
            
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
                    ventana_max.title("Reporte Kardex - Vista Maximizada")
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

            separator = tk.Label(control_frame, text="|", bg=self.COLORS['white'], fg=self.COLORS['text_dark'], font=('Segoe UI', 12, 'bold'))
            separator.pack(side="left", padx=5, pady=2)

            btn_zoom_out = tk.Button(
                control_frame, text="🔍−", command=lambda: change_zoom(-0.25),
                bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                font=('Segoe UI', 9, 'bold'), relief='flat', borderwidth=0, cursor='hand2'
            )
            btn_zoom_out.pack(side="left", padx=2, pady=2)

            zoom_label = tk.Label(control_frame, text=f"Zoom: {int(self.zoom_level * 100)}%", bg=self.COLORS['white'], fg=self.COLORS['text_dark'], font=('Segoe UI', 9, 'bold'))
            zoom_label.pack(side="left", padx=2, pady=2)

            btn_zoom_in = tk.Button(
                control_frame, text="🔍+", command=lambda: change_zoom(0.25),
                bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                font=('Segoe UI', 9, 'bold'), relief='flat', borderwidth=0, cursor='hand2'
            )
            btn_zoom_in.pack(side="left", padx=2, pady=2)

            separator2 = tk.Label(control_frame, text="|", bg=self.COLORS['white'], fg=self.COLORS['text_dark'], font=('Segoe UI', 12, 'bold'))
            separator2.pack(side="left", padx=5, pady=2)

            btn_fit_width = tk.Button(control_frame, text="↔ Ajustar Ancho", command=fit_to_width, bg=self.COLORS['white'], fg=self.COLORS['text_dark'], font=('Segoe UI', 9, 'bold'), relief='flat', borderwidth=0, cursor='hand2')
            btn_fit_width.pack(side="left", padx=2, pady=2)

            btn_fit_page = tk.Button(control_frame, text="⛶ Ajustar Página", command=fit_to_page, bg=self.COLORS['white'], fg=self.COLORS['text_dark'], font=('Segoe UI', 9, 'bold'), relief='flat', borderwidth=0, cursor='hand2')
            btn_fit_page.pack(side="left", padx=2, pady=2)

            btn_maximizar = tk.Button(control_frame, text="🔳 Maximizar", command=maximizar_reporte, bg=self.COLORS['primary'], fg='white', font=('Segoe UI', 10, 'bold'), relief='flat', borderwidth=0, cursor='hand2', pady=4, padx=12)
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
        """Abre el PDF en una aplicación externa del sistema"""
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
            # Obtener fechas según el modo seleccionado
            if self.modo_fecha_var.get() == "rango":
                fecha_ini = datetime.strptime(self.fecha_inicial.get(), '%d/%m/%Y')
                fecha_fin = datetime.strptime(self.fecha_final.get(), '%d/%m/%Y')
                periodo = f"{fecha_ini.strftime('%d%m%Y')}_{fecha_fin.strftime('%d%m%Y')}"
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
                periodo = f"{mes_inicio}_{mes_final}_{anio}"

            if fecha_fin < fecha_ini:
                messagebox.showerror("Error", "La fecha final debe ser mayor a la inicial")
                return

            if not self.combo_insumo.get():
                messagebox.showerror("Error", "Debe seleccionar un insumo")
                return

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
                    self.combo_area.get() if self.combo_area.get().strip() else None
                )

                if not movimientos_raw:
                    messagebox.showinfo("Info", "No hay datos para mostrar")
                    return

                movimientos_filtrados = self.filtrar_movimientos_por_nivel(movimientos_raw)
                if not movimientos_filtrados:
                    messagebox.showwarning("Sin datos", "No hay movimientos para mostrar con los filtros seleccionados.")
                    return

                movimientos_ordenados = self.ordenar_movimientos(movimientos_filtrados)
                self.movimientos_data = self.calcular_saldo_acumulado(movimientos_ordenados)

                if not self.movimientos_data:
                    messagebox.showwarning("Sin datos", "No se pudieron procesar los datos para el reporte.")
                    return

            # Generar nombre de archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"Reporte_Kardex_{periodo}_{timestamp}.pdf"
            downloads_path = os.path.expanduser("~/Downloads")
            full_path = os.path.join(downloads_path, file_name)

            # Generar el PDF
            self.generar_pdf(full_path)

            # Abrir PDF
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
        if not getattr(self, 'movimientos_data', None):
            messagebox.showwarning("Advertencia", "No hay datos para mostrar")
            return

        try:
            from reportlab.lib.enums import TA_CENTER, TA_LEFT

            doc = SimpleDocTemplate(
                ruta_pdf,
                pagesize=landscape(legal),
                rightMargin=36,
                leftMargin=36,
                topMargin=150,
                bottomMargin=36
            )

            styles = getSampleStyleSheet()
            elements = []

            ParagraphStyle('CustomTitle', parent=styles['Heading1'], alignment=TA_CENTER, spaceAfter=6, fontSize=12)
            ParagraphStyle('CustomSubtitle', parent=styles['Heading2'], alignment=TA_CENTER, spaceAfter=4, fontSize=10)
            filtro_style = ParagraphStyle('FiltroStyle', parent=styles['Normal'], alignment=TA_LEFT, fontSize=9, leading=11, spaceAfter=0)
            referencia_style = ParagraphStyle('ReferenciaStyle', parent=styles['Normal'], alignment=TA_CENTER, fontSize=8, leading=10)
            observaciones_style = ParagraphStyle('ObservacionesStyle', parent=styles['Normal'], alignment=TA_CENTER, fontSize=8, leading=10)

            header_row_height = 36
            row_height = 30

            headers = [
                'Fecha',
                'No.\nReferencia',
                'Remitente/\nDestinatario',
                'Entrada',
                'Precio Unit. (Q.)',
                'Valor Total (Q.)',
                'No.\nLote',
                'Fecha de\nVencimiento',
                'Salidas',
                'Reajustes\n(+) (-)',
                'Cantidad',
                'Saldo',
                'Observaciones'
            ]

            data = [headers]
            for mov in self.movimientos_data:
                referencia_par = Paragraph(str(mov.get('referencia', '') or ''), referencia_style)
                observaciones_par = Paragraph(str(mov.get('observaciones', '') or ''), observaciones_style)
                row = [
                    str(mov.get('fecha', '') or ''),
                    referencia_par,
                    str(mov.get('tipo_movimiento', '') or ''),
                    str(mov.get('entrada', '') or ''),
                    str(mov.get('precio_unitario', '') or ''),
                    str(mov.get('valor_total', '') or ''),
                    str(mov.get('lote') or "N/A"),
                    str(mov.get('fecha_vencimiento', '') or ''),
                    str(mov.get('salida', '') or ''),
                    str(mov.get('reajuste', '') or ''),
                    str(mov.get('cantidad_col', '') or ''),
                    str(mov.get('saldo', '') or ''),
                    observaciones_par
                ]
                data.append(row)

            colWidths = [
                0.8*inch, 0.9*inch, 1.7*inch, 0.7*inch, 0.9*inch, 0.9*inch,
                0.9*inch, 0.9*inch, 0.7*inch, 0.8*inch, 0.7*inch, 0.8*inch, 1.5*inch
            ]

            rowHeights = [header_row_height] + [row_height] * (len(data) - 1)

            table = Table(data, colWidths=colWidths, rowHeights=rowHeights, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
                ('TEXTCOLOR', (0,0), (-1,0), colors.black),
                ('ALIGN', (0,0), (-1,0), 'CENTER'),
                ('ALIGN', (0,1), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 8),
                ('FONTSIZE', (0,1), (-1,-1), 8),
                ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('LEFTPADDING', (0,0), (-1,-1), 4),
                ('RIGHTPADDING', (0,0), (-1,-1), 4),
            ]))

            elements.append(Spacer(1, 12))
            elements.append(table)

            def header(canvas, doc):
                canvas.saveState()
                page_num = canvas.getPageNumber()

                page_width, page_height = doc.pagesize
                left = doc.leftMargin
                right = page_width - doc.rightMargin

                if page_num % 2 == 1:
                    y_titulo_principal = page_height - 50
                    y_area = y_titulo_principal - 14
                    y_tarjeta = y_area - 14
                    y_fecha_generacion = y_tarjeta - 14

                    canvas.setFont('Helvetica-Bold', 11)
                    canvas.drawCentredString(page_width / 2.0, y_titulo_principal,
                        "DIRECCIÓN DEPARTAMENTAL DE REDES INTEGRADAS DE SERVICIOS DE SALUD DE GUATEMALA,")
                    canvas.setFont('Helvetica', 9)
                    canvas.drawCentredString(page_width / 2.0, y_area, "ÁREA NOR ORIENTE")
                    canvas.drawCentredString(page_width / 2.0, y_tarjeta, "TARJETA DE CONTROL DE SUMINISTROS")

                    canvas.setFont('Helvetica', 8)
                    fecha_generacion = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                    canvas.drawCentredString(page_width / 2.0, y_fecha_generacion, f"Generado el: {fecha_generacion}")

                    y_filtros = y_fecha_generacion - 30

                    table_width = sum(colWidths)
                    usable_width = right - left
                    table_start_x = left + (usable_width - table_width) / 2

                    filtros_columnas = [
                        (0, 1), (2, 3), (4, 5), (6, 7), (8, 9), (10, 11), (12, 12)
                    ]

                    filtros_info = []
                    for inicio_col, fin_col in filtros_columnas:
                        pos_x = table_start_x + sum(colWidths[:inicio_col])
                        ancho = sum(colWidths[inicio_col:fin_col+1])
                        filtros_info.append((pos_x, ancho))

                    filtros_list = [
                        f"Área:\n{self.combo_area.get()}",
                        f"Distrito:\n{self.combo_distrito.get()}",
                        f"Tipo de Servicio:\n{self.combo_tipo_servicio.get()}",
                        f"Servicio:\n{self.combo_servicio.get()}",
                        f"Insumo:\n{self.combo_insumo.get()}",
                        f"Presentación:\n{self.combo_presentacion.get()}",
                    ]

                    try:
                        usable_table_height = doc.height
                        filas_por_pagina_estimadas = int(usable_table_height // row_height)
                        data_rows_per_page = max(1, filas_por_pagina_estimadas - 1)
                    except Exception:
                        data_rows_per_page = 20

                    saldo_val = 0
                    if page_num > 1:
                        last_index_prev = (page_num - 1) * data_rows_per_page - 1
                        if 0 <= last_index_prev < len(self.movimientos_data):
                            raw = self.movimientos_data[last_index_prev].get('saldo', 0)
                            try:
                                saldo_val = float(raw) if raw not in (None, '') else 0
                            except Exception:
                                saldo_val = 0
                        else:
                            saldo_val = 0
                    else:
                        saldo_val = 0

                    filtros_list.append(f"Saldo anterior:\n{saldo_val:,.2f}" if isinstance(saldo_val, (int, float)) else f"Saldo anterior:\n{saldo_val}")

                    for idx, txt in enumerate(filtros_list):
                        pos_x, ancho = filtros_info[idx]
                        p = Paragraph(txt, filtro_style)
                        max_h = filtro_style.leading * 2 + 2
                        w_par, h_par = p.wrap(ancho, max_h)
                        x_draw = pos_x + 4
                        y_draw = y_filtros - (h_par / 2.0)
                        p.drawOn(canvas, x_draw, y_draw)

                canvas.restoreState()

            doc.build(elements, onFirstPage=header, onLaterPages=header)

            if not es_vista_previa:
                messagebox.showinfo("Éxito", f"PDF guardado en:\n{ruta_pdf}")

        except Exception as e:
            messagebox.showerror("Error", f"Error al generar PDF: {str(e)}")

    def generar_kardex(self):
        try:
            if self.modo_fecha_var.get() == "rango":
                fecha_ini = datetime.strptime(self.fecha_inicial.get(), '%d/%m/%Y')
                fecha_fin = datetime.strptime(self.fecha_final.get(), '%d/%m/%Y')
                periodo = f"{fecha_ini.strftime('%d%m%Y')}_{fecha_fin.strftime('%d%m%Y')}"
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
                periodo = f"{mes_inicio}_{mes_final}_{anio}"

            if fecha_fin < fecha_ini:
                messagebox.showerror("Error", "La fecha final debe ser mayor a la inicial")
                return

            if not self.combo_insumo.get():
                messagebox.showerror("Error", "Debe seleccionar un insumo")
                return

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
                    "No hay movimientos para mostrar con los filtros seleccionados.\n\n"
                    "Verifique que:\n"
                    "• Existan movimientos en el rango de fechas seleccionado\n"
                    "• Los movimientos estén guardados en el nivel jerárquico seleccionado\n"
                    "• Los filtros de insumo sean correctos"
                )
                return

            movimientos_ordenados = self.ordenar_movimientos(movimientos_filtrados)
            movimientos = self.calcular_saldo_acumulado(movimientos_ordenados)

            if not movimientos:
                messagebox.showwarning("Sin datos", "No se pudieron procesar los datos para el reporte.\nVerifique los filtros seleccionados.")
                return

            full_path = self.generar_excel(movimientos, periodo)

            if full_path and messagebox.askyesno("Excel Generado", "Reporte guardado exitosamente.\n¿Desea abrirlo ahora?"):
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
            import os
            from datetime import datetime

            filas_por_hoja = 1000
            total_movimientos = len(movimientos)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"Reporte_Kardex_{periodo}_{timestamp}.xlsx"

            downloads_path = os.path.expanduser("~/Downloads")
            full_path = os.path.join(downloads_path, file_name)

            writer = pd.ExcelWriter(full_path, engine='xlsxwriter')
            workbook = writer.book

            title_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 12, 'text_wrap': True})
            subtitle_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 10, 'text_wrap': True})
            saldo_filter_format = workbook.add_format({'bold': True, 'align': 'right', 'valign': 'vcenter', 'font_size': 10, 'text_wrap': True})
            header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 8, 'bg_color': '#ADD8E6', 'text_wrap': True, 'border': 1, 'border_color': '#808080'})
            saldo_anterior_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'bg_color': '#FFFFE0', 'border': 1, 'border_color': '#808080'})
            data_format_center = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'border': 1, 'border_color': '#808080', 'text_wrap': True})
            data_format_center_text = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'border': 1, 'border_color': '#808080', 'text_wrap': True})

            for hoja_num in range(0, total_movimientos, filas_por_hoja):
                nombre_hoja = f"Kardex_{hoja_num // filas_por_hoja + 1}"

                fin_hoja = min(hoja_num + filas_por_hoja, total_movimientos)
                movimientos_hoja = movimientos[hoja_num:fin_hoja]

                columnas_relevantes = [
                    'fecha', 'referencia', 'tipo_movimiento', 'entrada',
                    'precio_unitario', 'valor_total', 'lote', 'fecha_vencimiento',
                    'salida', 'reajuste', 'cantidad_col', 'saldo', 'observaciones'
                ]

                df = pd.DataFrame(movimientos_hoja)[columnas_relevantes]

                df.columns = [
                    'Fecha',
                    'No.\nReferencia',
                    'Remitente/\nDestinatario',
                    'Entrada',
                    'Precio Unit. (Q.)',
                    'Valor Total (Q.)',
                    'No.\nLote',
                    'Fecha de\nVencimiento',
                    'Salidas',
                    'Reajustes\n(+) (-)',
                    'Cantidad',
                    'Saldo',
                    'Observaciones'
                ]

                if hoja_num > 0:
                    raw_saldo = movimientos[hoja_num - 1].get('saldo', 0)
                    saldo_para_filtro = raw_saldo if raw_saldo not in (None, '') else 0
                else:
                    saldo_para_filtro = 0

                fila_inicio = 8

                if hoja_num > 0:
                    saldo_anterior = movimientos[hoja_num - 1].get('saldo', 0)
                    saldo_df = pd.DataFrame([{
                        'Fecha': 'SALDO ANTERIOR',
                        'No.\nReferencia': '',
                        'Remitente/\nDestinatario': '',
                        'Entrada': '',
                        'Precio Unit. (Q.)': '',
                        'Valor Total (Q.)': '',
                        'No.\nLote': '',
                        'Fecha de\nVencimiento': '',
                        'Salidas': '',
                        'Reajustes\n(+) (-)': '',
                        'Cantidad': '',
                        'Saldo': saldo_anterior,
                        'Observaciones': ''
                    }])
                    saldo_df.to_excel(writer, sheet_name=nombre_hoja, startrow=fila_inicio, index=False, header=False)
                    fila_inicio += 1

                df.to_excel(writer, sheet_name=nombre_hoja, startrow=fila_inicio, index=False, header=False)
                worksheet = writer.sheets[nombre_hoja]

                self.configurar_hoja_excel(
                    worksheet, workbook,
                    title_format, subtitle_format,
                    header_format, saldo_anterior_format,
                    df, hoja_num > 0, fila_inicio,
                    data_format_center, data_format_center_text,
                    saldo_para_filtro, saldo_filter_format
                )

            writer.close()
            messagebox.showinfo("Éxito", f"Reporte guardado en:\n{full_path}")
            return full_path

        except Exception as e:
            messagebox.showerror("Error", f"Error al generar Excel: {str(e)}")
            return None

    def configurar_hoja_excel(self, worksheet, workbook, title_format, subtitle_format,
                              header_format, saldo_anterior_format, df, tiene_saldo_anterior, fila_inicio,
                              data_format_center, data_format_center_text,
                              saldo_para_filtro, saldo_filter_format):
        """Configura la hoja Excel: mayor separación encabezado/filtros, filtros centrados en 2 líneas e incluye Saldo anterior."""
        from datetime import datetime

        row_height = 30
        header_row_height = 36

        worksheet.set_row(0, 36)
        worksheet.set_row(1, 30)
        worksheet.set_row(2, 30)
        worksheet.set_row(3, 24)
        worksheet.set_row(4, 8)
        worksheet.set_row(5, 40)

        worksheet.merge_range('A1:M1', 'DIRECCIÓN DEPARTAMENTAL DE REDES INTEGRADAS DE SERVICIOS DE SALUD DE GUATEMALA,', title_format)
        worksheet.merge_range('A2:M2', 'ÁREA NOR ORIENTE', subtitle_format)
        worksheet.merge_range('A3:M3', 'TARJETA DE CONTROL DE SUMINISTROS', subtitle_format)
        worksheet.merge_range('A4:M4', f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", subtitle_format)

        worksheet.merge_range('A6:B6', f"Área:\n{self.combo_area.get()}", subtitle_format)
        worksheet.merge_range('C6:D6', f"Distrito:\n{self.combo_distrito.get()}", subtitle_format)
        worksheet.merge_range('E6:F6', f"Tipo de Servicio:\n{self.combo_tipo_servicio.get()}", subtitle_format)
        worksheet.merge_range('G6:H6', f"Servicio:\n{self.combo_servicio.get()}", subtitle_format)
        worksheet.merge_range('I6:J6', f"Insumo:\n{self.combo_insumo.get()}", subtitle_format)
        worksheet.merge_range('K6:L6', f"Presentación:\n{self.combo_presentacion.get()}", subtitle_format)

        saldo_val = saldo_para_filtro if saldo_para_filtro not in (None, '') else 0
        worksheet.write('M6', f"Saldo anterior:\n{saldo_val}", subtitle_format)

        worksheet.set_row(fila_inicio - 1, header_row_height)
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(fila_inicio - 1, col_num, value, header_format)

        if tiene_saldo_anterior:
            saldo_row = fila_inicio
            worksheet.set_row(saldo_row, row_height)
            for col_idx in range(len(df.columns)):
                worksheet.write(saldo_row, col_idx, '', saldo_anterior_format)

        worksheet.set_landscape()
        worksheet.set_paper(5)
        worksheet.fit_to_pages(1, 1)
        worksheet.center_horizontally()
        worksheet.set_margins(left=0.5, right=0.5, top=0.5, bottom=0.5)

        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 10)
        worksheet.set_column('E:E', 14)
        worksheet.set_column('F:F', 14)
        worksheet.set_column('G:G', 12)
        worksheet.set_column('H:H', 12)
        worksheet.set_column('I:I', 10)
        worksheet.set_column('J:J', 10)
        worksheet.set_column('K:K', 10)
        worksheet.set_column('L:L', 10)
        worksheet.set_column('M:M', 18)

        data_start_row = fila_inicio + (1 if tiene_saldo_anterior else 0)
        for row_idx in range(len(df)):
            worksheet.set_row(data_start_row + row_idx, row_height)
            for col_idx in range(len(df.columns)):
                value = df.iloc[row_idx, col_idx]
                formato = data_format_center_text if (col_idx == 1 or col_idx == 12) else data_format_center
                worksheet.write(data_start_row + row_idx, col_idx, value, formato)

    def cerrar_ventana(self):
        """
        Cierra la ventana del reporte, limpia recursos y muestra la pantalla de bienvenida.
        """
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
        """
        Filtra los movimientos según el nivel jerárquico seleccionado.
        Solo muestra movimientos que fueron guardados exactamente en el nivel seleccionado.
        Retorna una lista de movimientos (no tupla), alineado con Reporte Demanda Real.
        """
        area_seleccionada = self.combo_area.get().strip()
        distrito_seleccionado = self.combo_distrito.get().strip()
        tipo_servicio_seleccionado = self.combo_tipo_servicio.get().strip()
        servicio_seleccionado = self.combo_servicio.get().strip()

        if not any([area_seleccionada, distrito_seleccionado, tipo_servicio_seleccionado, servicio_seleccionado]):
            return movimientos

        movimientos_filtrados = []

        def es_nulo_o_vacio(valor):
            return valor is None or valor == '' or str(valor).strip() == '' or str(valor).lower() in ['null', 'none']

        for mov in movimientos:
            mov_area = mov.get('area_nombre')
            mov_distrito = mov.get('distrito_nombre')
            mov_tipo_servicio = mov.get('tipo_servicio_desc')
            mov_servicio = mov.get('servicio_nombre')

            incluir_movimiento = False

            # Nivel Área
            if area_seleccionada and not distrito_seleccionado and not tipo_servicio_seleccionado and not servicio_seleccionado:
                if (mov_area == area_seleccionada and es_nulo_o_vacio(mov_distrito) and es_nulo_o_vacio(mov_tipo_servicio) and es_nulo_o_vacio(mov_servicio)):
                    incluir_movimiento = True
            # Nivel Distrito
            elif area_seleccionada and distrito_seleccionado and not tipo_servicio_seleccionado and not servicio_seleccionado:
                if (mov_area == area_seleccionada and mov_distrito == distrito_seleccionado and es_nulo_o_vacio(mov_tipo_servicio) and es_nulo_o_vacio(mov_servicio)):
                    incluir_movimiento = True
            # Nivel Tipo Servicio
            elif area_seleccionada and distrito_seleccionado and tipo_servicio_seleccionado and not servicio_seleccionado:
                if (mov_area == area_seleccionada and mov_distrito == distrito_seleccionado and mov_tipo_servicio == tipo_servicio_seleccionado and es_nulo_o_vacio(mov_servicio)):
                    incluir_movimiento = True
            # Nivel Servicio
            elif area_seleccionada and distrito_seleccionado and tipo_servicio_seleccionado and servicio_seleccionado:
                if (mov_area == area_seleccionada and mov_distrito == distrito_seleccionado and mov_tipo_servicio == tipo_servicio_seleccionado and mov_servicio == servicio_seleccionado):
                    incluir_movimiento = True

            if incluir_movimiento:
                movimientos_filtrados.append(mov)

        return movimientos_filtrados