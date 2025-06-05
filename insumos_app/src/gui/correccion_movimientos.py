# Imports existentes
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import pandas as pd
from datetime import datetime
import sys
import os
from ttkwidgets.autocomplete import AutocompleteCombobox

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
    buscar_movimientos_por_filtros,
    obtener_tipos_movimiento
)

class CorreccionMovimientos:
    # Definir las columnas como atributo de la clase
    COLUMNAS = [
        'ID', 'Fecha', 'Referencia', 'Servicio', 'Tipo de Movimiento', 'Lote',
        'Fecha Vencimiento', 'Cantidad', 'Insumo', 'Distrito Salida', 'Servicio Salida',
        'Observaciones'
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
        self.tipos_movimiento = []

        self.setup_ui()

    def setup_ui(self):
        # Frame principal - USAR PACK PARA TODO
        self.frame_principal = ttk.LabelFrame(self.parent, text="Filtros de Búsqueda")
        self.frame_principal.pack(fill="both", expand=True, padx=10, pady=5)

        # Frame para fechas
        self.frame_fechas = ttk.LabelFrame(self.frame_principal, text="Selección de Fechas")
        self.frame_fechas.pack(fill="x", padx=5, pady=5)

        # Frame para rango de fechas
        self.frame_rango = ttk.Frame(self.frame_fechas)
        self.frame_rango.pack(fill="x", padx=5, pady=2)

        ttk.Label(self.frame_rango, text="Fecha Inicial:").grid(row=0, column=0, padx=5)
        self.fecha_inicial = DateEntry(
            self.frame_rango,
            width=12,
            date_pattern='dd/mm/yyyy',
            state='normal'
        )
        self.fecha_inicial.grid(row=0, column=1, padx=5)

        ttk.Label(self.frame_rango, text="Fecha Final:").grid(row=0, column=2, padx=5)
        self.fecha_final = DateEntry(
            self.frame_rango,
            width=12,
            date_pattern='dd/mm/yyyy',
            state='normal'
        )
        self.fecha_final.grid(row=0, column=3, padx=5)

        # Frame para combos
        self.frame_combos = ttk.Frame(self.frame_principal)
        self.frame_combos.pack(fill="x", padx=5, pady=5)

        # Primera fila de combos
        self.frame_combos1 = ttk.Frame(self.frame_combos)
        self.frame_combos1.pack(fill="x", pady=5)

        # Grid DENTRO del frame_combos1
        ttk.Label(self.frame_combos1, text="Área:").grid(row=0, column=0, padx=5, sticky='w')
        self.area_var = tk.StringVar()
        self.combo_area = AutocompleteCombobox(self.frame_combos1, textvariable=self.area_var, state="normal", width=18)
        self.combo_area.grid(row=0, column=1, padx=5, sticky='w')

        ttk.Label(self.frame_combos1, text="Distrito:").grid(row=0, column=2, padx=5, sticky='w')
        self.distrito_var = tk.StringVar()
        self.combo_distrito = AutocompleteCombobox(self.frame_combos1, textvariable=self.distrito_var, state="normal", width=18)
        self.combo_distrito.grid(row=0, column=3, padx=5, sticky='w')

        ttk.Label(self.frame_combos1, text="Tipo de Servicio:").grid(row=0, column=4, padx=5, sticky='w')
        self.tipo_servicio_var = tk.StringVar()
        self.combo_tipo_servicio = AutocompleteCombobox(self.frame_combos1, textvariable=self.tipo_servicio_var, state="normal", width=18)
        self.combo_tipo_servicio.grid(row=0, column=5, padx=5, sticky='w')

        ttk.Label(self.frame_combos1, text="Servicio:").grid(row=0, column=6, padx=5, sticky='w')
        self.servicio_var = tk.StringVar()
        self.combo_servicio = AutocompleteCombobox(self.frame_combos1, textvariable=self.servicio_var, state="normal", width=18)
        self.combo_servicio.grid(row=0, column=7, padx=5, sticky='w')

        # Segunda fila de combos
        self.frame_combos2 = ttk.Frame(self.frame_combos)
        self.frame_combos2.pack(fill="x", pady=5)

        # Grid DENTRO del frame_combos2
        ttk.Label(self.frame_combos2, text="Tipo\nInsumo:").grid(row=0, column=0, padx=5, sticky='w')
        self.tipo_insumo_var = tk.StringVar()
        self.combo_tipo_insumo = AutocompleteCombobox(self.frame_combos2, textvariable=self.tipo_insumo_var, state="normal", width=18)
        self.combo_tipo_insumo.grid(row=0, column=1, padx=5, sticky='w')

        ttk.Label(self.frame_combos2, text="Insumo:").grid(row=0, column=2, padx=5, sticky='w')
        self.insumo_var = tk.StringVar()
        self.combo_insumo = AutocompleteCombobox(self.frame_combos2, textvariable=self.insumo_var, state="normal", width=18)
        self.combo_insumo.grid(row=0, column=3, padx=5, sticky='w')

        ttk.Label(self.frame_combos2, text="Presentación:").grid(row=0, column=4, padx=5, sticky='w')
        self.presentacion_var = tk.StringVar()
        self.combo_presentacion = AutocompleteCombobox(self.frame_combos2, textvariable=self.presentacion_var, state="normal", width=18)
        self.combo_presentacion.grid(row=0, column=5, padx=5, sticky='w')

        ttk.Label(self.frame_combos2, text="Tipo\nMovimiento:").grid(row=0, column=6, padx=5, sticky='w')
        self.tipo_movimiento_var = tk.StringVar()
        self.combo_tipo_movimiento = AutocompleteCombobox(self.frame_combos2, textvariable=self.tipo_movimiento_var, state="normal", width=18)
        self.combo_tipo_movimiento.grid(row=0, column=7, padx=5, sticky='w')

        # Frame para botones de búsqueda
        self.frame_botones_busqueda = ttk.Frame(self.frame_principal)
        self.frame_botones_busqueda.pack(fill="x", pady=5)

        ttk.Button(self.frame_botones_busqueda, text="Buscar Movimientos", command=self.buscar_movimientos).pack(side="left", padx=5)
        ttk.Button(self.frame_botones_busqueda, text="Limpiar Filtros", command=self.limpiar_filtros).pack(side="left", padx=5)

        # Frame para el Treeview
        self.frame_treeview = ttk.LabelFrame(self.frame_principal, text="Resultados")
        self.frame_treeview.pack(fill="both", expand=True, padx=5, pady=5)

        # Crear Treeview con scrollbars
        self.tree_frame = ttk.Frame(self.frame_treeview)
        self.tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Courier", 9))

        # Scrollbars para el Treeview
        self.tree_scroll_y = ttk.Scrollbar(self.tree_frame)
        self.tree_scroll_y.pack(side="right", fill="y")

        self.tree_scroll_x = ttk.Scrollbar(self.tree_frame, orient="horizontal")
        self.tree_scroll_x.pack(side="bottom", fill="x")

        # Configurar estilos
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Consolas", 9, "bold"))
        style.configure("Treeview", font=("Consolas", 9), rowheight=25)

        # Crear Treeview
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=self.COLUMNAS,
            show="headings",
            yscrollcommand=self.tree_scroll_y.set,
            xscrollcommand=self.tree_scroll_x.set
        )

        # Títulos simples y claros
        encabezados = {
            'ID': 'ID',
            'Fecha': 'FECHA',
            'Referencia': 'REFERENCIA',
            'Servicio': 'SERVICIO',
            'Tipo de Movimiento': 'TIPO MOVIMIENTO',
            'Lote': 'LOTE',
            'Fecha Vencimiento': 'FECHA VENCIMIENTO',
            'Cantidad': 'CANTIDAD',
            'Insumo': 'INSUMO',
            'Distrito Salida': 'DISTRITO SALIDA',
            'Servicio Salida': 'SERVICIO SALIDA',
            'Observaciones': 'OBSERVACIONES'
        }

        for col in self.COLUMNAS:
            self.tree.heading(col, text=encabezados[col])

            # Anchos aumentados basados en los títulos
            if col == "Referencia":
                width = 120  # Aumentado para "REFERENCIA"
            elif col == "Observaciones":
                width = 250  # Aumentado para "OBSERVACIONES"
            elif col == "Tipo de Movimiento":
                width = 180  # Aumentado para "TIPO MOVIMIENTO"
            elif col == "Fecha Vencimiento":
                width = 150  # Aumentado para "F. VENCIMIENTO"
            elif col in ["Servicio", "Insumo"]:
                width = 160  # Aumentado para "SERVICIO" e "INSUMO"
            elif col in ["Distrito Salida", "Servicio Salida"]:
                width = 140  # Aumentado para "DIST. SALIDA" y "SERV. SALIDA"
            elif col == "Cantidad":
                width = 120  # Aumentado para "CANTIDAD"
            elif col == "Fecha":
                width = 110  # Aumentado para "FECHA"
            elif col == "Lote":
                width = 100  # Aumentado para "LOTE"
            else:
                width = 100  # Ancho por defecto

            # Configurar alineación
            if col in ["Cantidad"]:
                self.tree.column(col, width=width, anchor='center')
            elif col in ["Fecha", "Fecha Vencimiento"]:
                self.tree.column(col, width=width, anchor='center')
            else:
                self.tree.column(col, width=width, anchor='w')

        self.tree.column("ID", width=0, stretch=False)
                    
        # Empaquetar el Treeview
        self.tree.pack(side="left", fill="both", expand=True)

        # Configurar scrollbars
        self.tree_scroll_y.config(command=self.tree.yview)
        self.tree_scroll_x.config(command=self.tree.xview)

        # Frame para botones de acción
        self.frame_botones_accion = ttk.Frame(self.frame_principal)
        self.frame_botones_accion.pack(fill="x", pady=10)

        ttk.Button(self.frame_botones_accion, text="Editar Movimiento", command=self.editar_movimiento).pack(side="left", padx=5)
        ttk.Button(self.frame_botones_accion, text="Eliminar Movimiento", command=self.eliminar_movimiento).pack(side="left", padx=5)
        ttk.Button(self.frame_botones_accion, text="Cerrar", command=self.cerrar_ventana).pack(side="right", padx=5)

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
        self.cargar_tipos_movimiento()

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

    def cargar_tipos_movimiento(self):
        self.tipos_movimiento = obtener_tipos_movimiento()
        if self.tipos_movimiento:
            opciones = [''] + [t['descripcion'] for t in self.tipos_movimiento]
            self.combo_tipo_movimiento.set_completion_list(opciones)

    def buscar_movimientos(self):
        try:
            
            # Validar que al menos un filtro esté seleccionado
            if not any([
                self.fecha_inicial.get(),
                self.fecha_final.get(),
                self.combo_area.get(),
                self.combo_distrito.get(),
                self.combo_tipo_servicio.get(),
                self.combo_servicio.get(),
                self.combo_tipo_insumo.get(),
                self.combo_insumo.get(),
                self.combo_presentacion.get(),
                self.combo_tipo_movimiento.get()
            ]):
                messagebox.showwarning("Advertencia", "Por favor, seleccione al menos un filtro para buscar movimientos.")
                return
            
            # Obtener fechas
            fecha_ini = datetime.strptime(self.fecha_inicial.get(), '%d/%m/%Y')
            fecha_fin = datetime.strptime(self.fecha_final.get(), '%d/%m/%Y')

            # Validar fechas
            if fecha_fin < fecha_ini:
                messagebox.showerror("Error", "La fecha final debe ser mayor a la inicial")
                return

            # Obtener datos
            self.movimientos_data = buscar_movimientos_por_filtros(
                fecha_ini.strftime('%Y-%m-%d'),
                fecha_fin.strftime('%Y-%m-%d'),
                self.combo_area.get(),
                self.combo_distrito.get(),
                self.combo_tipo_servicio.get(),
                self.combo_servicio.get(),
                self.combo_tipo_insumo.get(),
                self.combo_insumo.get(),
                self.combo_presentacion.get(),
                self.combo_tipo_movimiento.get()
            )

            if not self.movimientos_data:
                messagebox.showinfo("Info", "No hay datos para mostrar")
                return

            # Limpiar el Treeview
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Llenar el Treeview con los datos (nuevo orden con Servicio)
            for mov in self.movimientos_data:
                fecha_venc = mov.get('fecha_vencimiento')
                if fecha_venc is None or fecha_venc == '':
                    fecha_venc = "N/A"
                self.tree.insert('', 'end', values=(
                    mov.get('id', ''),                          # ID
                    mov.get('fecha', ''),                       # Fecha
                    mov.get('referencia', '') or "",            # Referencia
                    mov.get('servicio_nombre', '') or "",       # Servicio (NUEVO)
                    mov.get('tipo_movimiento', '') or "",       # Tipo de Movimiento
                    mov.get('lote', '') or "",                  # Lote
                    fecha_venc,                                 # Fecha Vencimiento
                    self.formato_float(mov.get('cantidad', 0)), # Cantidad
                    mov.get('insumo_nombre', '') or "",         # Insumo
                    mov.get('distrito_salida', '') or "",       # Distrito Salida
                    mov.get('servicio_salida', '') or "",       # Servicio Salida
                    mov.get('observaciones', '') or ""          # Observaciones
                ))

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error al buscar movimientos:\n{str(e)}\n\nPor favor, verifique los datos e intente nuevamente."
            )

    def limpiar_filtros(self):
        # Restablecer fechas
        self.fecha_inicial.set_date(datetime.now())
        self.fecha_final.set_date(datetime.now())

        # Limpiar combos
        self.combo_area.set('')
        self.combo_distrito.set('')
        self.combo_tipo_servicio.set('')
        self.combo_servicio.set('')
        self.combo_tipo_insumo.set('')
        self.combo_insumo.set('')
        self.combo_presentacion.set('')
        self.combo_tipo_movimiento.set('')

        # Limpiar Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Limpiar datos
        self.movimientos_data = None

    def editar_movimiento(self):
        # Obtener el item seleccionado
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un movimiento para editar")
            return

        # Obtener el ID del movimiento seleccionado (sigue siendo la primera columna)
        item_values = self.tree.item(selected_item[0], 'values')
        movimiento_id = item_values[0]  # ID sigue siendo índice 0

        # Buscar el movimiento en los datos
        movimiento = next((m for m in self.movimientos_data if str(m['id']) == str(movimiento_id)), None)
        if not movimiento:
            messagebox.showerror("Error", "No se pudo encontrar el movimiento seleccionado")
            return

        # Crear ventana de edición
        self.abrir_ventana_edicion(movimiento)

    def abrir_ventana_edicion(self, movimiento):
        # Crear ventana de edición
        edicion_window = tk.Toplevel(self.parent)
        edicion_window.title("Editar Movimiento")
        edicion_window.geometry("600x500")
        edicion_window.grab_set()  # Hacer modal

        # Centrar la ventana
        edicion_window.transient(self.parent)
        edicion_window.update_idletasks()

        # Obtener dimensiones de la pantalla y la ventana
        screen_width = edicion_window.winfo_screenwidth()
        screen_height = edicion_window.winfo_screenheight()
        window_width = 600
        window_height = 500

        # Calcular posición para centrar
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        edicion_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Frame principal con padding
        frame_edicion = ttk.Frame(edicion_window, padding=20)
        frame_edicion.pack(fill="both", expand=True)

        # Título centrado (sin ID)
        titulo_frame = ttk.Frame(frame_edicion)
        titulo_frame.pack(fill="x", pady=(0, 20))

        ttk.Label(titulo_frame, text="Editar Movimiento",
                font=("Arial", 14, "bold")).pack()

        # Frame para los campos con grid
        campos_frame = ttk.Frame(frame_edicion)
        campos_frame.pack(fill="both", expand=True)

        # Configurar columnas para que se expandan uniformemente
        campos_frame.columnconfigure(1, weight=1)

        # Tamaño estándar para todos los campos
        ANCHO_CAMPO = 25

        row = 0

        # Fecha
        ttk.Label(campos_frame, text="Fecha:", font=("Arial", 10)).grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=8
        )
        fecha_entry = DateEntry(
            campos_frame,
            width=ANCHO_CAMPO,
            date_pattern='dd/mm/yyyy',
            font=("Arial", 10)
        )
        fecha_entry.grid(row=row, column=1, sticky="ew", pady=8)
        if movimiento['fecha']:
            try:
                fecha_entry.set_date(datetime.strptime(movimiento['fecha'], '%Y-%m-%d'))
            except:
                pass
        row += 1

        # Referencia
        ttk.Label(campos_frame, text="Referencia:", font=("Arial", 10)).grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=8
        )
        referencia_var = tk.StringVar(value=movimiento.get('referencia', '') or "")
        referencia_entry = ttk.Entry(campos_frame, textvariable=referencia_var,
                                    width=ANCHO_CAMPO, font=("Arial", 10))
        referencia_entry.grid(row=row, column=1, sticky="ew", pady=8)
        row += 1

        # Insumo (solo lectura)
        ttk.Label(campos_frame, text="Insumo:", font=("Arial", 10)).grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=8
        )
        insumo_frame = ttk.Frame(campos_frame)
        insumo_frame.grid(row=row, column=1, sticky="ew", pady=8)
        insumo_frame.columnconfigure(0, weight=1)

        insumo_label = ttk.Label(insumo_frame,
                                text=movimiento.get('insumo_nombre', '') or "",
                                foreground="blue",
                                font=("Arial", 10),
                                relief="sunken",
                                padding=5)
        insumo_label.grid(row=0, column=0, sticky="ew")
        row += 1

        # Tipo de Movimiento
        ttk.Label(campos_frame, text="Tipo de Movimiento:", font=("Arial", 10)).grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=8
        )
        tipo_movimiento_var = tk.StringVar(value=movimiento.get('tipo_movimiento', '') or "")
        tipo_movimiento_combo = ttk.Combobox(campos_frame, textvariable=tipo_movimiento_var,
                                            width=ANCHO_CAMPO, font=("Arial", 10))
        tipo_movimiento_combo['values'] = [t['descripcion'] for t in self.tipos_movimiento] if self.tipos_movimiento else []
        tipo_movimiento_combo.grid(row=row, column=1, sticky="ew", pady=8)
        row += 1

        # Lote
        ttk.Label(campos_frame, text="Lote:", font=("Arial", 10)).grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=8
        )
        lote_var = tk.StringVar(value=movimiento.get('lote', '') or "")
        lote_entry = ttk.Entry(campos_frame, textvariable=lote_var,
                            width=ANCHO_CAMPO, font=("Arial", 10))
        lote_entry.grid(row=row, column=1, sticky="ew", pady=8)
        row += 1

        # Fecha Vencimiento
        ttk.Label(campos_frame, text="Fecha Vencimiento:", font=("Arial", 10)).grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=8
        )
        fecha_venc_entry = DateEntry(
            campos_frame,
            width=ANCHO_CAMPO,
            date_pattern='dd/mm/yyyy',
            font=("Arial", 10)
        )
        fecha_venc_entry.grid(row=row, column=1, sticky="ew", pady=8)
        if movimiento.get('fecha_vencimiento'):
            try:
                fecha_venc_entry.set_date(datetime.strptime(movimiento['fecha_vencimiento'], '%Y-%m-%d'))
            except:
                pass
        row += 1

        # Cantidad
        ttk.Label(campos_frame, text="Cantidad:", font=("Arial", 10)).grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=8
        )
        cantidad_var = tk.StringVar(value=self.formato_float(movimiento.get('cantidad', 0)))
        cantidad_entry = ttk.Entry(campos_frame, textvariable=cantidad_var,
                                width=ANCHO_CAMPO, font=("Arial", 10))
        cantidad_entry.grid(row=row, column=1, sticky="ew", pady=8)
        row += 1

        # Observaciones
        ttk.Label(campos_frame, text="Observaciones:", font=("Arial", 10)).grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=8
        )
        observaciones_var = tk.StringVar(value=movimiento.get('observaciones', '') or "")
        observaciones_entry = ttk.Entry(campos_frame, textvariable=observaciones_var,
                                    width=ANCHO_CAMPO, font=("Arial", 10))
        observaciones_entry.grid(row=row, column=1, sticky="ew", pady=8)
        row += 1

        # Función para guardar cambios
        def guardar_cambios():
            try:
                # Validar datos
                fecha = fecha_entry.get_date().strftime('%Y-%m-%d')
                tipo_movimiento = tipo_movimiento_var.get()

                # Validar campos numéricos
                try:
                    cantidad = float(cantidad_var.get()) if cantidad_var.get() else 0
                except ValueError:
                    messagebox.showerror("Error", "El campo cantidad debe contener un valor numérico válido")
                    return

                # Preparar datos para actualización
                datos_actualizados = {
                    'id': movimiento['id'],
                    'fecha': fecha,
                    'referencia': referencia_var.get(),
                    'tipo_movimiento': tipo_movimiento,
                    'lote': lote_var.get(),
                    'fecha_vencimiento': fecha_venc_entry.get_date().strftime('%Y-%m-%d') if fecha_venc_entry.get() else None,
                    'cantidad': cantidad,
                    'observaciones': observaciones_var.get()
                }

                # Llamar a la función de actualización en la base de datos
                from src.database.db_manager import actualizar_movimiento
                actualizar_movimiento(datos_actualizados['id'], datos_actualizados)

                messagebox.showinfo("Éxito", "Movimiento actualizado correctamente")
                edicion_window.destroy()

                # Actualizar la vista
                self.buscar_movimientos()

            except Exception as e:
                messagebox.showerror("Error", f"Error al actualizar movimiento: {str(e)}")

        # Frame para botones centrado
        frame_botones = ttk.Frame(frame_edicion)
        frame_botones.pack(pady=20)

        # Botones con estilo uniforme
        btn_guardar = ttk.Button(frame_botones, text="Modificar",
                                command=guardar_cambios, width=15)
        btn_guardar.pack(side="left", padx=10)

        btn_cancelar = ttk.Button(frame_botones, text="Cancelar",
                                command=edicion_window.destroy, width=15)
        btn_cancelar.pack(side="left", padx=10)

        # Enfocar el primer campo
        referencia_entry.focus_set()

    def eliminar_movimiento(self):
        # Obtener el item seleccionado
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un movimiento para eliminar")
            return

        # Obtener el ID del movimiento seleccionado
        item_values = self.tree.item(selected_item[0], 'values')
        movimiento_id = item_values[0]

        # Confirmar eliminación
        if not messagebox.askyesno("Confirmar Eliminación",
                                  "¿Está seguro que desea eliminar este movimiento?\n\n"
                                  "Esta acción no se puede deshacer y puede afectar el saldo de inventario."):
            return

        try:
            # Llamar a la función de eliminación en la base de datos
            from src.database.db_manager import eliminar_movimiento
            eliminar_movimiento(movimiento_id)

            messagebox.showinfo("Éxito", "Movimiento eliminado correctamente")

            # Actualizar la vista
            self.buscar_movimientos()

        except Exception as e:
            messagebox.showerror("Error", f"Error al eliminar movimiento: {str(e)}")

    def cerrar_ventana(self):
        if messagebox.askyesno("Confirmar", "¿Está seguro que desea cerrar esta ventana?"):
            # Limpiar el frame principal
            for widget in self.parent.winfo_children():
                widget.destroy()
            # Mostrar la pantalla de bienvenida
            if self.main_window:
                self.main_window.show_welcome_screen()