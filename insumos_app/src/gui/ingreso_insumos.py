import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
import sys
import os
from ttkwidgets.autocomplete import AutocompleteCombobox

# Agregar el directorio raíz del proyecto al PATH de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.db_manager import (
    obtener_areas,
    obtener_distritos_por_area,
    obtener_distritos,
    obtener_tipos_servicio_por_distrito,
    obtener_servicios_por_tipo,
    obtener_tipos_insumo,
    obtener_insumos_por_tipo,
    obtener_tipos_movimiento,
    obtener_id_distrito,
    obtener_id_tipo_servicio,
    obtener_id_servicio,
    obtener_id_tipo_insumo,
    obtener_id_insumo,
    obtener_id_presentacion,
    obtener_id_tipo_movimiento,
    guardar_movimiento
)

class IngresoInsumos:
    def __init__(self, parent_frame, main_window):
        self.parent = parent_frame
        self.main_window = main_window

        # Variables para los combobox
        self.distrito_var = tk.StringVar()
        self.tipo_servicio_var = tk.StringVar()
        self.servicio_var = tk.StringVar()
        self.tipo_insumo_var = tk.StringVar()
        self.insumo_var = tk.StringVar()
        self.presentacion_var = tk.StringVar()
        self.tipo_movimiento_var = tk.StringVar()

        # Constantes para el diseño
        self.LABEL_WIDTH = 15
        self.WIDGET_WIDTH = 25
        self.PADDING_X = 10
        self.PADDING_Y = 5

        self.setup_ui()
        self.setup_bindings()

    def setup_ui(self):
        # --- Tu código GUI original sin cambios ---
        # Frame Servicios
        self.frame_servicios = ttk.LabelFrame(self.parent, text="Servicios")
        self.frame_servicios.pack(fill="x", padx=10, pady=10)

        # Área
        ttk.Label(self.frame_servicios, text="Área:", anchor="w").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        areas = [a['nombre'] for a in obtener_areas() or []]
        self.area_var = tk.StringVar()
        self.area_cb = AutocompleteCombobox(self.frame_servicios, textvariable=self.area_var, width=20, completevalues=areas, state="normal")
        self.area_cb.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Distrito
        ttk.Label(self.frame_servicios, text="Distrito:", anchor="w").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.distrito_var = tk.StringVar()
        distritos = [d['nombre'] for d in obtener_distritos() or []]
        self.distrito_cb = AutocompleteCombobox(self.frame_servicios, textvariable=self.distrito_var, width=20, completevalues=distritos, state="normal")
        self.distrito_cb.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # Tipo de Servicio
        ttk.Label(self.frame_servicios, text="Tipo de Servicio:", anchor="w").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.tipo_servicio_var = tk.StringVar()
        self.tipo_servicio_cb = AutocompleteCombobox(self.frame_servicios, textvariable=self.tipo_servicio_var, width=20, completevalues=[], state="normal")
        self.tipo_servicio_cb.grid(row=0, column=5, padx=5, pady=5, sticky="w")

        # Servicio
        ttk.Label(self.frame_servicios, text="Servicio:", anchor="w").grid(row=0, column=6, padx=5, pady=5, sticky="w")
        self.servicio_var = tk.StringVar()
        self.servicio_cb = AutocompleteCombobox(self.frame_servicios, textvariable=self.servicio_var, width=20, completevalues=[], state="normal")
        self.servicio_cb.grid(row=0, column=7, padx=5, pady=5, sticky="w")

        # Inicializar distritos vacíos
        self.distrito_cb.config(completevalues=[])
        self.distrito_var.set('')

        # Frame Insumos
        self.frame_insumos = ttk.LabelFrame(self.parent, text="Insumos")
        self.frame_insumos.pack(fill="x", padx=10, pady=10)

        # Tipo de Insumo
        ttk.Label(self.frame_insumos, text="Tipo de Insumo:", anchor="w").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        tipos_insumo = [ti['descripcion'] for ti in obtener_tipos_insumo() or []]
        self.tipo_insumo_cb = AutocompleteCombobox(self.frame_insumos, textvariable=self.tipo_insumo_var, width=25, completevalues=tipos_insumo, state="normal")
        self.tipo_insumo_cb.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Insumo
        ttk.Label(self.frame_insumos, text="Insumo:", anchor="w").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.insumo_cb = AutocompleteCombobox(self.frame_insumos, textvariable=self.insumo_var, width=25, completevalues=[], state="normal")
        self.insumo_cb.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # Presentación
        ttk.Label(self.frame_insumos, text="Presentación:", anchor="w").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.presentacion_cb = AutocompleteCombobox(self.frame_insumos, textvariable=self.presentacion_var, width=25, completevalues=[], state="normal")
        self.presentacion_cb.grid(row=0, column=5, padx=5, pady=5, sticky="w")

        # Lote
        ttk.Label(self.frame_insumos, text="Lote:", anchor="w").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.lote_entry = ttk.Entry(self.frame_insumos, width=27)
        self.lote_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Fecha de Vencimiento
        ttk.Label(self.frame_insumos, text="Fecha de Vencimiento:", anchor="w").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.fecha_venc = DateEntry(self.frame_insumos, width=25, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        self.fecha_venc.grid(row=1, column=3, padx=5, pady=5, sticky="w")

        # Frame Registro de Movimiento
        self.frame_registro = ttk.LabelFrame(self.parent, text="Registro de Movimiento")
        self.frame_registro.pack(fill="x", padx=10, pady=10)

        # Fecha de Registro
        ttk.Label(self.frame_registro, text="Fecha de Registro:", anchor="w").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.fecha_reg = DateEntry(self.frame_registro, width=25, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        self.fecha_reg.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Referencia
        ttk.Label(self.frame_registro, text="Referencia:", anchor="w").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.referencia_entry = ttk.Entry(self.frame_registro, width=27)
        self.referencia_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # Tipo de Movimiento
        ttk.Label(self.frame_registro, text="Tipo de Movimiento:", anchor="w").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        tipos_movimiento = [tm['descripcion'] for tm in obtener_tipos_movimiento() or []]
        self.tipo_mov_cb = AutocompleteCombobox(self.frame_registro, textvariable=self.tipo_movimiento_var, width=25, completevalues=tipos_movimiento, state="normal")
        self.tipo_mov_cb.grid(row=0, column=5, padx=5, pady=5, sticky="w")

        # Cantidad
        ttk.Label(self.frame_registro, text="Cantidad:", anchor="w").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.cantidad_entry = ttk.Entry(self.frame_registro, width=27)
        self.cantidad_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Observaciones
        ttk.Label(self.frame_registro, text="Observaciones:", anchor="w").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.observaciones_entry = ttk.Entry(self.frame_registro, width=60)
        self.observaciones_entry.grid(row=1, column=3, columnspan=3, padx=5, pady=5, sticky="w")

        # Botón Agregar Movimiento
        self.btn_agregar = ttk.Button(self.parent, text="Agregar Movimiento", command=self.agregar_movimiento)
        self.btn_agregar.pack(pady=10)

        # Frame Movimientos (Treeview)
        self.frame_movimientos = ttk.LabelFrame(self.parent, text="Movimientos")
        self.frame_movimientos.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ('fecha_registro', 'referencia', 'tipo_movimiento', 'insumo', 'presentacion',
                   'lote', 'fecha_vencimiento', 'cantidad', 'observaciones')

        self.tree = ttk.Treeview(self.frame_movimientos, columns=columns, show='headings')
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        encabezados = {
            'fecha_registro': 'Fecha de Registro',
            'referencia': 'Referencia',
            'tipo_movimiento': 'Tipo de Movimiento',
            'insumo': 'Insumo',
            'presentacion': 'Presentación',
            'lote': 'Lote',
            'fecha_vencimiento': 'Fecha de Vencimiento',
            'cantidad': 'Cantidad',
            'observaciones': 'Observaciones'
        }

        for col in columns:
            self.tree.heading(col, text=encabezados[col])
            self.tree.column(col, width=150, minwidth=150)

        scrollbar_y = ttk.Scrollbar(self.frame_movimientos, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(self.frame_movimientos, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")

        def on_treeview_configure(event):
            width = event.width
            col_width = max(150, width // len(columns) - 5)
            for col in columns:
                self.tree.column(col, width=col_width, minwidth=150)

        self.tree.bind('<Configure>', on_treeview_configure)

        # Frame para botones
        self.frame_botones = ttk.Frame(self.parent)
        self.frame_botones.pack(fill="x", padx=10, pady=10)

        self.btn_editar = ttk.Button(self.frame_botones, text="Editar", command=self.editar_movimiento)
        self.btn_editar.pack(side="left", padx=5)
        self.btn_eliminar = ttk.Button(self.frame_botones, text="Eliminar", command=self.eliminar_movimiento)
        self.btn_eliminar.pack(side="left", padx=5)
        self.btn_guardar = ttk.Button(self.frame_botones, text="Guardar Movimientos", command=self.guardar_movimientos)
        self.btn_guardar.pack(side="left", padx=5)
        self.btn_cerrar = ttk.Button(self.frame_botones, text="Cerrar", command=self.cerrar_ventana)
        self.btn_cerrar.pack(side="right", padx=5)

    def setup_bindings(self):
        self.area_var.trace_add('write', self.on_area_selected)
        self.distrito_var.trace_add('write', self.actualizar_tipos_servicio)
        self.tipo_servicio_var.trace_add('write', self.actualizar_servicios)
        self.tipo_insumo_var.trace_add('write', self.actualizar_insumos)
        self.insumo_var.trace_add('write', self.actualizar_presentacion)

    def on_area_selected(self, *args):
        area_nombre = self.area_var.get()
        areas = obtener_areas() or []
        area_id = next((a['id'] for a in areas if a['nombre'] == area_nombre), None)

        if area_id:
            distritos = obtener_distritos_por_area(area_id) or []
            distritos_nombres = [d['nombre'] for d in distritos]
            self.distrito_cb.config(completevalues=distritos_nombres)
            self.distrito_var.set('')
        else:
            self.distrito_cb.config(completevalues=[])
            self.distrito_var.set('')

    def actualizar_tipos_servicio(self, *args):
        distrito_nombre = self.distrito_var.get()
        distritos = obtener_distritos() or []
        distrito_id = next((d['id'] for d in distritos if d['nombre'] == distrito_nombre), None)

        if distrito_id:
            tipos_servicio = obtener_tipos_servicio_por_distrito(distrito_id) or []
            opciones = [ts['descripcion'] for ts in tipos_servicio]
            self.tipo_servicio_cb.config(completevalues=opciones)
            self.tipo_servicio_var.set('')
            self.servicio_var.set('')
        else:
            self.tipo_servicio_cb.config(completevalues=[])
            self.tipo_servicio_var.set('')
            self.servicio_cb.config(completevalues=[])
            self.servicio_var.set('')

    def actualizar_servicios(self, *args):
        distrito_nombre = self.distrito_var.get()
        tipo_servicio_desc = self.tipo_servicio_var.get()
        distritos = obtener_distritos() or []
        distrito_id = next((d['id'] for d in distritos if d['nombre'] == distrito_nombre), None)

        if distrito_id:
            tipos_servicio = obtener_tipos_servicio_por_distrito(distrito_id) or []
            tipo_servicio_id = next((ts['id'] for ts in tipos_servicio if ts['descripcion'] == tipo_servicio_desc), None)
            if tipo_servicio_id:
                servicios = obtener_servicios_por_tipo(tipo_servicio_id) or []
                opciones = [s['nombre'] for s in servicios]
                self.servicio_cb.config(completevalues=opciones)
                self.servicio_var.set('')
                return
        self.servicio_cb.config(completevalues=[])
        self.servicio_var.set('')

    def actualizar_insumos(self, *args):
        tipo_insumo_desc = self.tipo_insumo_var.get()
        tipos_insumo = obtener_tipos_insumo() or []
        tipo_insumo_id = next((ti['id'] for ti in tipos_insumo if ti['descripcion'] == tipo_insumo_desc), None)

        if tipo_insumo_id:
            insumos = obtener_insumos_por_tipo(tipo_insumo_id) or []
            opciones = [i['nombre'] for i in insumos]
            self.insumo_cb.config(completevalues=opciones)
            self.insumo_var.set('')
        else:
            self.insumo_cb.config(completevalues=[])
            self.insumo_var.set('')

    def actualizar_presentacion(self, *args):
        tipo_insumo_desc = self.tipo_insumo_var.get()
        insumo_nombre = self.insumo_var.get()
        tipos_insumo = obtener_tipos_insumo() or []
        tipo_insumo_id = next((ti['id'] for ti in tipos_insumo if ti['descripcion'] == tipo_insumo_desc), None)

        if tipo_insumo_id and insumo_nombre:
            insumos = obtener_insumos_por_tipo(tipo_insumo_id) or []
            insumo_seleccionado = next((i for i in insumos if i['nombre'] == insumo_nombre), None)
            if insumo_seleccionado and insumo_seleccionado.get('nombre_presentacion'):
                self.presentacion_cb.config(completevalues=[insumo_seleccionado['nombre_presentacion']])
                self.presentacion_var.set(insumo_seleccionado['nombre_presentacion'])
                return
        self.presentacion_cb.config(completevalues=[])
        self.presentacion_var.set('')

    def agregar_movimiento(self):
        try:
            fecha_registro = self.fecha_reg.get_date().strftime('%d/%m/%Y')
            tipo_movimiento = self.tipo_movimiento_var.get()
            insumo = self.insumo_var.get()
            presentacion = self.presentacion_var.get()
            lote = self.lote_entry.get()
            fecha_venc_str = self.fecha_venc.get_date().strftime('%d/%m/%Y')
            cantidad_str = self.cantidad_entry.get()
            referencia = self.referencia_entry.get()
            observaciones = self.observaciones_entry.get()

            if not all([tipo_movimiento, insumo, presentacion, lote, cantidad_str, referencia]):
                messagebox.showerror("Error", "Los campos son requeridos excepto observaciones")
                return

            cantidad = float(cantidad_str)

            self.tree.insert('', 'end', values=(
                fecha_registro, referencia, tipo_movimiento, insumo,
                presentacion, lote, fecha_venc_str, cantidad, observaciones
            ))

            self.tipo_movimiento_var.set('')
            self.cantidad_entry.delete(0, 'end')
            self.referencia_entry.delete(0, 'end')
            self.observaciones_entry.delete(0, 'end')

        except ValueError:
            messagebox.showerror("Error", "La cantidad debe ser un número válido")
        except Exception as e:
            messagebox.showerror("Error", f"Error al agregar movimiento: {str(e)}")

    def editar_movimiento(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un movimiento para editar")
            return

        valores = self.tree.item(selected_item)['values']

        editar_ventana = tk.Toplevel(self.parent)
        editar_ventana.title("Editar Movimiento")
        editar_ventana.geometry("900x725")

        # Centrar la ventana
        editar_ventana.update_idletasks()
        width = editar_ventana.winfo_width()
        height = editar_ventana.winfo_height()
        x = (editar_ventana.winfo_screenwidth() // 2) - (width // 2)
        y = (editar_ventana.winfo_screenheight() // 2) - (height // 2)
        editar_ventana.geometry(f'{width}x{height}+{x}+{y}')

        # Variables para combobox en ventana edición
        edit_area_var = tk.StringVar()
        edit_distrito_var = tk.StringVar()
        edit_tipo_servicio_var = tk.StringVar()
        edit_servicio_var = tk.StringVar()
        edit_tipo_insumo_var = tk.StringVar()
        edit_insumo_var = tk.StringVar()
        edit_presentacion_var = tk.StringVar()
        edit_tipo_movimiento_var = tk.StringVar()

        ANCHO_LABEL = 20
        ANCHO_CAMPO = 60
        PADDING = 10

        main_frame = ttk.Frame(editar_ventana, padding=PADDING)
        main_frame.pack(fill="both", expand=True)

        # Frame Servicios
        frame_servicios = ttk.LabelFrame(main_frame, text="Servicios", padding=PADDING)
        frame_servicios.pack(fill="x", pady=5)

        ttk.Label(frame_servicios, text="Área:", width=ANCHO_LABEL, anchor="e").grid(row=0, column=0, padx=5, pady=5)
        area_cb = AutocompleteCombobox(frame_servicios, textvariable=edit_area_var, width=ANCHO_CAMPO, state="normal")
        areas = [a['nombre'] for a in obtener_areas() or []]
        area_cb.set_completion_list(areas)
        area_cb.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_servicios, text="Distrito:", width=ANCHO_LABEL, anchor="e").grid(row=1, column=0, padx=5, pady=5)
        distrito_cb = AutocompleteCombobox(frame_servicios, textvariable=edit_distrito_var, width=ANCHO_CAMPO, state="normal")
        distrito_cb.set_completion_list([d['nombre'] for d in obtener_distritos() or []])
        distrito_cb.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_servicios, text="Tipo de Servicio:", width=ANCHO_LABEL, anchor="e").grid(row=2, column=0, padx=5, pady=5)
        tipo_servicio_cb = AutocompleteCombobox(frame_servicios, textvariable=edit_tipo_servicio_var, width=ANCHO_CAMPO, state="normal")
        tipo_servicio_cb.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_servicios, text="Servicio:", width=ANCHO_LABEL, anchor="e").grid(row=3, column=0, padx=5, pady=5)
        servicio_cb = AutocompleteCombobox(frame_servicios, textvariable=edit_servicio_var, width=ANCHO_CAMPO, state="normal")
        servicio_cb.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        # Frame Insumos
        frame_insumos = ttk.LabelFrame(main_frame, text="Insumos", padding=PADDING)
        frame_insumos.pack(fill="x", pady=5)

        ttk.Label(frame_insumos, text="Tipo de Insumo:", width=ANCHO_LABEL, anchor="e").grid(row=0, column=0, padx=5, pady=5)
        tipo_insumo_cb = AutocompleteCombobox(frame_insumos, textvariable=edit_tipo_insumo_var, width=ANCHO_CAMPO, state="normal")
        tipo_insumo_cb.set_completion_list([ti['descripcion'] for ti in obtener_tipos_insumo() or []])
        tipo_insumo_cb.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_insumos, text="Insumo:", width=ANCHO_LABEL, anchor="e").grid(row=1, column=0, padx=5, pady=5)
        insumo_cb = AutocompleteCombobox(frame_insumos, textvariable=edit_insumo_var, width=ANCHO_CAMPO, state="normal")
        insumo_cb.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_insumos, text="Presentación:", width=ANCHO_LABEL, anchor="e").grid(row=2, column=0, padx=5, pady=5)
        presentacion_cb = AutocompleteCombobox(frame_insumos, textvariable=edit_presentacion_var, width=ANCHO_CAMPO, state="normal")
        presentacion_cb.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        # Frame Detalles
        frame_detalles = ttk.LabelFrame(main_frame, text="Detalles del Movimiento", padding=PADDING)
        frame_detalles.pack(fill="x", pady=5)

        ttk.Label(frame_detalles, text="Fecha de Registro:", width=ANCHO_LABEL, anchor="e").grid(row=0, column=0, padx=5, pady=5)
        fecha_edit = DateEntry(frame_detalles, width=ANCHO_CAMPO, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        fecha_edit.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_detalles, text="Referencia:", width=ANCHO_LABEL, anchor="e").grid(row=1, column=0, padx=5, pady=5)
        referencia_entry = ttk.Entry(frame_detalles, width=ANCHO_CAMPO)
        referencia_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_detalles, text="Tipo Movimiento:", width=ANCHO_LABEL, anchor="e").grid(row=2, column=0, padx=5, pady=5)
        tipo_mov_cb = AutocompleteCombobox(frame_detalles, textvariable=edit_tipo_movimiento_var, width=ANCHO_CAMPO, state="normal")
        tipo_mov_cb.set_completion_list([tm['descripcion'] for tm in obtener_tipos_movimiento() or []])
        tipo_mov_cb.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_detalles, text="Lote:", width=ANCHO_LABEL, anchor="e").grid(row=3, column=0, padx=5, pady=5)
        lote_entry = ttk.Entry(frame_detalles, width=ANCHO_CAMPO)
        lote_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_detalles, text="Fecha Vencimiento:", width=ANCHO_LABEL, anchor="e").grid(row=4, column=0, padx=5, pady=5)
        fecha_venc_edit = DateEntry(frame_detalles, width=ANCHO_CAMPO, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        fecha_venc_edit.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_detalles, text="Cantidad:", width=ANCHO_LABEL, anchor="e").grid(row=5, column=0, padx=5, pady=5)
        cantidad_entry = ttk.Entry(frame_detalles, width=ANCHO_CAMPO)
        cantidad_entry.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_detalles, text="Observaciones:", width=ANCHO_LABEL, anchor="e").grid(row=6, column=0, padx=5, pady=5)
        observaciones_entry = ttk.Entry(frame_detalles, width=ANCHO_CAMPO)
        observaciones_entry.grid(row=6, column=1, padx=5, pady=5, sticky="ew")

        # Configurar grid para expandirse
        for frame in [frame_servicios, frame_insumos, frame_detalles]:
            frame.grid_columnconfigure(1, weight=1)

        # Frame Botones
        frame_botones = ttk.Frame(main_frame)
        frame_botones.pack(pady=PADDING)

        # Funciones para actualizar listas según selección en edición
        def actualizar_distritos_edit(*args):
            area_nombre = edit_area_var.get()
            areas = obtener_areas()
            area_id = next((a['id'] for a in areas if a['nombre'] == area_nombre), None)
            if area_id:
                distritos = obtener_distritos_por_area(area_id)
                distritos_nombres = [d['nombre'] for d in distritos]
                distrito_cb.set_completion_list(distritos_nombres)
                if edit_distrito_var.get() not in distritos_nombres:
                    edit_distrito_var.set('')
            else:
                distrito_cb.set_completion_list([])
                edit_distrito_var.set('')

        def actualizar_tipos_servicio_edit(*args):
            distrito_nombre = edit_distrito_var.get()
            distritos = obtener_distritos()
            distrito_id = next((d['id'] for d in distritos if d['nombre'] == distrito_nombre), None)
            if distrito_id:
                tipos_servicio = obtener_tipos_servicio_por_distrito(distrito_id)
                tipo_servicio_cb.set_completion_list([ts['descripcion'] for ts in tipos_servicio or []])

        def actualizar_servicios_edit(*args):
            try:
                distrito_nombre = edit_distrito_var.get()
                distritos = obtener_distritos()
                distrito_id = next((d['id'] for d in distritos if d['nombre'] == distrito_nombre), None)
                if distrito_id:
                    tipos_servicio = obtener_tipos_servicio_por_distrito(distrito_id)
                    tipo_servicio_id = next((ts['id'] for ts in tipos_servicio if ts['descripcion'] == edit_tipo_servicio_var.get()), None)
                    if tipo_servicio_id:
                        servicios = obtener_servicios_por_tipo(tipo_servicio_id)
                        servicio_cb.set_completion_list([s['nombre'] for s in servicios or []])
                        servicio_actual = self.servicio_var.get()
                        if servicio_actual in [s['nombre'] for s in servicios]:
                            edit_servicio_var.set(servicio_actual)
                        else:
                            edit_servicio_var.set('')
            except Exception as e:
                print(f"Error al actualizar servicios: {e}")
                servicio_cb.set_completion_list([])

        def actualizar_insumos_edit(*args):
            tipo_insumo_desc = edit_tipo_insumo_var.get()
            tipos_insumo = obtener_tipos_insumo()
            tipo_insumo_id = next((ti['id'] for ti in tipos_insumo if ti['descripcion'] == tipo_insumo_desc), None)
            if tipo_insumo_id:
                insumos = obtener_insumos_por_tipo(tipo_insumo_id)
                insumo_cb.set_completion_list([i['nombre'] for i in insumos or []])

        def actualizar_presentacion_edit(*args):
            try:
                tipo_insumo_desc = edit_tipo_insumo_var.get()
                tipos_insumo = obtener_tipos_insumo()
                tipo_insumo_id = next((ti['id'] for ti in tipos_insumo if ti['descripcion'] == tipo_insumo_desc), None)
                if tipo_insumo_id and edit_insumo_var.get():
                    insumos = obtener_insumos_por_tipo(tipo_insumo_id)
                    insumo_seleccionado = next((i for i in insumos if i['nombre'] == edit_insumo_var.get()), None)
                    if insumo_seleccionado and insumo_seleccionado.get('nombre_presentacion'):
                        presentacion_cb.set_completion_list([insumo_seleccionado['nombre_presentacion']])
                        edit_presentacion_var.set(insumo_seleccionado['nombre_presentacion'])
            except Exception as e:
                print(f"Error al actualizar presentación: {e}")
                presentacion_cb.set_completion_list([])

        # Bindings para actualización dinámica
        edit_area_var.trace_add('write', actualizar_distritos_edit)
        edit_distrito_var.trace_add('write', actualizar_tipos_servicio_edit)
        edit_tipo_servicio_var.trace_add('write', actualizar_servicios_edit)
        edit_tipo_insumo_var.trace_add('write', actualizar_insumos_edit)
        edit_insumo_var.trace_add('write', actualizar_presentacion_edit)

        # Cargar valores iniciales en los widgets de edición
        distrito_actual = self.distrito_var.get()
        area_actual = ''
        distritos = obtener_distritos()
        for d in distritos:
            if d['nombre'] == distrito_actual:
                area_actual = d.get('area_nombre', '') or ''
                break

        edit_area_var.set(area_actual)

        def set_distrito():
            edit_distrito_var.set(distrito_actual)

            def cargar_tipo_servicio():
                edit_tipo_servicio_var.set(self.tipo_servicio_var.get())

                def cargar_servicio():
                    edit_servicio_var.set(self.servicio_var.get())

                    def cargar_resto_valores():
                        edit_tipo_insumo_var.set(self.tipo_insumo_var.get())

                        def cargar_insumo():
                            edit_insumo_var.set(valores[3])
                            edit_presentacion_var.set(valores[4])

                            fecha_actual = datetime.strptime(valores[0], '%d/%m/%Y').date()
                            fecha_edit.set_date(fecha_actual)
                            referencia_entry.delete(0, tk.END)
                            referencia_entry.insert(0, valores[1])
                            edit_tipo_movimiento_var.set(valores[2])
                            lote_entry.delete(0, tk.END)
                            lote_entry.insert(0, valores[5])
                            fecha_venc = datetime.strptime(valores[6], '%d/%m/%Y').date()
                            fecha_venc_edit.set_date(fecha_venc)
                            cantidad_entry.delete(0, tk.END)
                            cantidad_entry.insert(0, valores[7])
                            if valores[8]:
                                observaciones_entry.insert(0, valores[8])

                        editar_ventana.after(100, cargar_insumo)

                    editar_ventana.after(100, cargar_resto_valores)

                editar_ventana.after(100, cargar_servicio)

            editar_ventana.after(150, set_distrito)

        editar_ventana.after(150, set_distrito)

        # Botones Guardar y Cerrar
        def guardar_cambios():
            try:
                nuevos_valores = (
                    fecha_edit.get_date().strftime('%d/%m/%Y'),
                    referencia_entry.get(),
                    edit_tipo_movimiento_var.get(),
                    edit_insumo_var.get(),
                    edit_presentacion_var.get(),
                    lote_entry.get(),
                    fecha_venc_edit.get_date().strftime('%d/%m/%Y'),
                    cantidad_entry.get(),
                    observaciones_entry.get()
                )

                if not all(nuevos_valores[:8]):
                    messagebox.showerror("Error", "Todos los campos son requeridos excepto observaciones")
                    return

                try:
                    float(nuevos_valores[7])
                except ValueError:
                    messagebox.showerror("Error", "La cantidad debe ser un número válido")
                    return

                self.tree.item(selected_item, values=nuevos_valores)
                editar_ventana.destroy()
                messagebox.showinfo("Éxito", "Movimiento actualizado correctamente")
            except Exception as e:
                messagebox.showerror("Error", f"Error al actualizar movimiento: {str(e)}")

        ttk.Button(frame_botones, text="Guardar", command=guardar_cambios).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Cerrar", command=editar_ventana.destroy).pack(side="left", padx=5)

    def eliminar_movimiento(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un movimiento para eliminar")
            return

        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este movimiento?"):
            self.tree.delete(selected_item)

    def guardar_movimientos(self):
        items = self.tree.get_children()
        if not items:
            messagebox.showwarning("Advertencia", "No hay movimientos para guardar")
            return

        if not messagebox.askyesno("Confirmar", "¿Está seguro de guardar todos los movimientos?"):
            return

        movimientos_guardados = 0
        errores = []

        for item in items:
            try:
                valores = self.tree.item(item)['values']

                distrito_id = obtener_id_distrito(self.distrito_var.get())
                tipo_servicio_id = obtener_id_tipo_servicio(self.tipo_servicio_var.get())
                servicio_id = obtener_id_servicio(self.servicio_var.get())
                tipo_insumo_id = obtener_id_tipo_insumo(self.tipo_insumo_var.get())
                insumo_id = obtener_id_insumo(valores[3])
                presentacion_id = obtener_id_presentacion(valores[4])
                tipo_movimiento_id = obtener_id_tipo_movimiento(valores[2])

                fecha_registro = datetime.strptime(valores[0], '%d/%m/%Y')
                fecha_vencimiento = datetime.strptime(valores[6], '%d/%m/%Y')

                movimiento_data = {
                    'fecha_registro': fecha_registro,
                    'referencia': valores[1],
                    'tipo_movimiento_id': tipo_movimiento_id,
                    'distrito_id': distrito_id,
                    'tipo_servicio_id': tipo_servicio_id,
                    'servicio_id': servicio_id,
                    'tipo_insumo_id': tipo_insumo_id,
                    'insumo_id': insumo_id,
                    'presentacion_id': presentacion_id,
                    'lote': valores[5],
                    'fecha_vencimiento': fecha_vencimiento,
                    'cantidad': float(valores[7]),
                    'observaciones': valores[8] if valores[8] else None
                }

                guardar_movimiento(movimiento_data)
                movimientos_guardados += 1

            except Exception as e:
                errores.append(f"Error en movimiento {movimientos_guardados + 1}: {str(e)}")

        if errores:
            messagebox.showerror("Errores al guardar",
                                f"Se guardaron {movimientos_guardados} movimientos, pero hubo errores:\n" +
                                "\n".join(errores))
        else:
            messagebox.showinfo("Éxito",
                                f"Se guardaron {movimientos_guardados} movimientos correctamente")
            self.tree.delete(*self.tree.get_children())

    def cerrar_ventana(self):
        if messagebox.askyesno("Confirmar", "¿Está seguro que desea cerrar esta ventana?"):
            for widget in self.parent.winfo_children():
                widget.destroy()
            self.main_window.show_welcome_screen()