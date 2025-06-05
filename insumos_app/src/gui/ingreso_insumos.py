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
        self.salida_distrito_var = tk.StringVar()
        self.salida_tipo_servicio_var = tk.StringVar()
        self.salida_servicio_var = tk.StringVar()
        
        # Variable para radio buttons nivel de bodega
        self.nivel_bodega_var = tk.StringVar(value="area")  

        # Constantes para el diseño
        self.LABEL_WIDTH = 15
        self.WIDGET_WIDTH = 25
        self.PADDING_X = 10
        self.PADDING_Y = 5

        self.setup_ui()
        self.setup_bindings()
        self.actualizar_estado_comboboxes()  
    
    # 1. Métodos de configuración de UI
    
    def setup_ui(self):
        # --- Tu código GUI original sin cambios ---
        # Frame Nivel de Bodega (radio buttons)
        self.frame_nivel_bodega = ttk.LabelFrame(self.parent, text="Nivel de Bodega")
        self.frame_nivel_bodega.pack(fill="x", padx=10, pady=(10, 0))

        # Radio buttons
        rb_area = ttk.Radiobutton(self.frame_nivel_bodega, text="Área", variable=self.nivel_bodega_var, value="area", command=self.actualizar_estado_comboboxes)
        rb_distrito = ttk.Radiobutton(self.frame_nivel_bodega, text="Distrito", variable=self.nivel_bodega_var, value="distrito", command=self.actualizar_estado_comboboxes)
        rb_servicio = ttk.Radiobutton(self.frame_nivel_bodega, text="Servicio", variable=self.nivel_bodega_var, value="servicio", command=self.actualizar_estado_comboboxes)

        # Layout radio buttons horizontal con espacio uniforme
        rb_area.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        rb_distrito.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        rb_servicio.grid(row=0, column=2, padx=10, pady=5, sticky="w")
        
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
        
        self.sin_fecha_venc = tk.BooleanVar()
        self.check_sin_fecha = ttk.Checkbutton(
            self.frame_insumos,
            text="Sin fecha de vencimiento",
            variable=self.sin_fecha_venc,
            command=self.toggle_fecha_vencimiento
        )
        self.check_sin_fecha.grid(row=1, column=4, padx=5, pady=5, sticky="w")
        
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
        
        # Salida Nivel Inferior
        self.frame_salida_nivel_inferior = ttk.LabelFrame(self.parent, text="Salida Nivel Inferior")

        # Distrito
        ttk.Label(self.frame_salida_nivel_inferior, text="Distrito:", anchor="w").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        distritos = [d['nombre'] for d in obtener_distritos() or []]
        self.salida_distrito_cb = AutocompleteCombobox(self.frame_salida_nivel_inferior, textvariable=self.salida_distrito_var, width=25, completevalues=distritos, state="disabled")
        self.salida_distrito_cb.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Tipo de Servicio
        ttk.Label(self.frame_salida_nivel_inferior, text="Tipo de Servicio:", anchor="w").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.salida_tipo_servicio_cb = AutocompleteCombobox(self.frame_salida_nivel_inferior, textvariable=self.salida_tipo_servicio_var, width=25, completevalues=[], state="disabled")
        self.salida_tipo_servicio_cb.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # Servicio
        ttk.Label(self.frame_salida_nivel_inferior, text="Servicio:", anchor="w").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.salida_servicio_cb = AutocompleteCombobox(self.frame_salida_nivel_inferior, textvariable=self.salida_servicio_var, width=25, completevalues=[], state="disabled")
        self.salida_servicio_cb.grid(row=0, column=5, padx=5, pady=5, sticky="w")

        # Inicializar combobox vacíos
        self.salida_tipo_servicio_cb.config(completevalues=[])
        self.salida_tipo_servicio_var.set('')
        self.salida_servicio_cb.config(completevalues=[])
        self.salida_servicio_var.set('')
        
        # Botón Agregar Movimiento
        self.btn_agregar = ttk.Button(self.parent, text="Agregar Movimiento", command=self.agregar_movimiento)
        self.btn_agregar.pack(pady=10)

        # Frame Movimientos (Treeview)
        self.frame_movimientos = ttk.LabelFrame(self.parent, text="Movimientos")
        self.frame_movimientos.pack(fill="both", expand=True, padx=10, pady=10)

        columns = (
            'fecha_registro', 'referencia', 'tipo_movimiento', 'insumo', 'presentacion', 'servicio',
            'lote', 'fecha_vencimiento', 'cantidad', 'salida_distrito', 'salida_servicio',
            'observaciones', 'tipo_insumo', 'area', 'distrito', 'tipo_servicio'
        )

        self.tree = ttk.Treeview(self.frame_movimientos, columns=columns, show='headings')
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        encabezados = {
            'fecha_registro': 'Fecha de Registro',
            'referencia': 'Referencia',
            'tipo_movimiento': 'Tipo de Movimiento',
            'insumo': 'Insumo',
            'presentacion': 'Presentación',
            'servicio': 'Servicio',
            'lote': 'Lote',
            'fecha_vencimiento': 'Fecha de Vencimiento',
            'cantidad': 'Cantidad',
            'salida_distrito': 'Salida Distrito',
            'salida_servicio': 'Salida Servicio',
            'observaciones': 'Observaciones',
            'tipo_insumo': 'Tipo Insumo',
            'area': 'Área',           
            'distrito': 'Distrito',   
            'tipo_servicio': 'Tipo Servicio'  
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
        
        # Ocultar inicialmente el frame de salida nivel inferior
        self.frame_salida_nivel_inferior.pack_forget()
        
    def setup_bindings(self):
        self.area_var.trace_add('write', self.on_area_selected)
        self.distrito_var.trace_add('write', self.actualizar_tipos_servicio)
        self.tipo_servicio_var.trace_add('write', self.actualizar_servicios)
        self.tipo_insumo_var.trace_add('write', self.actualizar_insumos)
        self.insumo_var.trace_add('write', self.actualizar_presentacion)
    
        # Bind para tipo de movimiento para actualizar estado del frame salida nivel inferior
        self.tipo_movimiento_var.trace_add('write', lambda *args: self.actualizar_estado_salida_nivel_inferior())
      
        # También bind para radio buttons nivel de bodega
        self.nivel_bodega_var.trace_add('write', lambda *args: self.actualizar_estado_salida_nivel_inferior())
        
        # Bind para salida distrito para actualizar tipos servicio en salida nivel inferior
        self.salida_distrito_var.trace_add('write', self.actualizar_tipos_servicio_salida)

        # Bind para salida tipo servicio para actualizar servicios en salida nivel inferior
        self.salida_tipo_servicio_var.trace_add('write', self.actualizar_servicios_salida)
    
    # 2. Métodos de actualización de estado
    
    def actualizar_estado_comboboxes(self):
        nivel = self.nivel_bodega_var.get()
        if nivel == "area":
            self.area_cb.config(state="normal")
            self.distrito_cb.config(state="disabled")
            self.tipo_servicio_cb.config(state="disabled")
            self.servicio_cb.config(state="disabled")
        elif nivel == "distrito":
            self.area_cb.config(state="normal")
            self.distrito_cb.config(state="normal")
            self.tipo_servicio_cb.config(state="disabled")
            self.servicio_cb.config(state="disabled")
        elif nivel == "servicio":
            self.area_cb.config(state="normal")
            self.distrito_cb.config(state="normal")
            self.tipo_servicio_cb.config(state="normal")
            self.servicio_cb.config(state="normal")

        # Actualizar tipos de movimiento filtrados según nivel
        self.actualizar_tipos_movimiento_filtrados()

        # Ajustar tamaño de ventana si el frame salida nivel inferior está visible
        if self.frame_salida_nivel_inferior.winfo_ismapped():
            self.ajustar_tamano_ventana(mostrar_salida=True)
        else:
            self.ajustar_tamano_ventana(mostrar_salida=False)

        # Si el nivel es "distrito", llenar el combobox de distrito en "Salida Nivel Inferior" al inicio
        if nivel == "distrito" and self.tipo_movimiento_var.get().strip().upper() == "SALIDA NIVEL INFERIOR":
            self.salida_distrito_var.set(self.distrito_var.get())
            self.actualizar_tipos_servicio_salida()

    def actualizar_estado_salida_nivel_inferior(self):
        tipo_mov = self.tipo_movimiento_var.get().strip().upper()
        nivel = self.nivel_bodega_var.get()

        if tipo_mov == "SALIDA NIVEL INFERIOR":
            if not self.frame_salida_nivel_inferior.winfo_ismapped():
                self.frame_salida_nivel_inferior.pack(fill="x", padx=10, pady=10, before=self.btn_agregar)

            if nivel == "area":
                self.salida_distrito_cb.config(state="normal")
                self.salida_tipo_servicio_cb.config(state="disabled")
                self.salida_servicio_cb.config(state="disabled")
            elif nivel == "distrito":
                # Llenar el combobox de distrito y bloquearlo
                self.salida_distrito_var.set(self.distrito_var.get())
                self.salida_distrito_cb.config(state="disabled")  # Bloquear el combobox
                self.salida_distrito_cb.config(completevalues=[self.distrito_var.get()])  # Limitar las opciones solo al distrito seleccionado

                self.salida_tipo_servicio_cb.config(state="normal")
                self.salida_servicio_cb.config(state="normal")
                self.actualizar_tipos_servicio_salida()
            else:
                self.salida_distrito_cb.config(state="disabled")
                self.salida_tipo_servicio_cb.config(state="disabled")
                self.salida_servicio_cb.config(state="disabled")

            self.ajustar_tamano_ventana(mostrar_salida=True)
        else:
            self.frame_salida_nivel_inferior.pack_forget()
            self.salida_distrito_var.set('')
            self.salida_tipo_servicio_var.set('')
            self.salida_servicio_var.set('')
            self.ajustar_tamano_ventana(mostrar_salida=False)   
            
    def actualizar_tipos_movimiento_filtrados(self):
        nivel = self.nivel_bodega_var.get()
        tipos_movimiento = [tm['descripcion'] for tm in obtener_tipos_movimiento() or []]

        if nivel in ("area", "distrito"):
            # Excluir "ENTREGADO" y "NO ENTREGADO"
            tipos_movimiento = [tm for tm in tipos_movimiento if tm not in ("ENTREGADO", "NO ENTREGADO")]
        elif nivel == "servicio":
            # Excluir "SALIDA NIVEL INFERIOR"
            tipos_movimiento = [tm for tm in tipos_movimiento if tm != "SALIDA NIVEL INFERIOR"]

        self.tipo_mov_cb.config(completevalues=tipos_movimiento)

        # Limpiar selección si el valor actual no está en la lista filtrada
        if self.tipo_movimiento_var.get() not in tipos_movimiento:
            self.tipo_movimiento_var.set('')
        
    # 3. Métodos de actualización de datos
    
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
            if insumo_seleccionado and insumo_seleccionado['nombre_presentacion']:
                self.presentacion_cb.config(completevalues=[insumo_seleccionado['nombre_presentacion']])
                self.presentacion_var.set(insumo_seleccionado['nombre_presentacion'])
                return
        self.presentacion_cb.config(completevalues=[])
        self.presentacion_var.set('')
    
    def actualizar_tipos_servicio_salida(self, *args):
        distrito_nombre = self.salida_distrito_var.get()
        distritos = obtener_distritos() or []
        distrito_id = next((d['id'] for d in distritos if d['nombre'] == distrito_nombre), None)

        if distrito_id:
            tipos_servicio = obtener_tipos_servicio_por_distrito(distrito_id) or []
            opciones = [ts['descripcion'] for ts in tipos_servicio]
            self.salida_tipo_servicio_cb.config(completevalues=opciones)
            self.salida_tipo_servicio_var.set('')
            self.salida_servicio_var.set('')
        else:
            self.salida_tipo_servicio_cb.config(completevalues=[])
            self.salida_tipo_servicio_var.set('')
            self.salida_servicio_cb.config(completevalues=[])
            self.salida_servicio_var.set('')

    def actualizar_servicios_salida(self, *args):
        distrito_nombre = self.salida_distrito_var.get()
        tipo_servicio_desc = self.salida_tipo_servicio_var.get()
        distritos = obtener_distritos() or []
        distrito_id = next((d['id'] for d in distritos if d['nombre'] == distrito_nombre), None)

        if distrito_id:
            tipos_servicio = obtener_tipos_servicio_por_distrito(distrito_id) or []
            tipo_servicio_id = next((ts['id'] for ts in tipos_servicio if ts['descripcion'] == tipo_servicio_desc), None)
            if tipo_servicio_id:
                servicios = obtener_servicios_por_tipo(tipo_servicio_id) or []
                opciones = [s['nombre'] for s in servicios]
                self.salida_servicio_cb.config(completevalues=opciones)
                self.salida_servicio_var.set('')
                return
        self.salida_servicio_cb.config(completevalues=[])
        self.salida_servicio_var.set('')

    def toggle_fecha_vencimiento(self):
        if self.sin_fecha_venc.get():
            self.fecha_venc.configure(state='disabled')
        else:
            self.fecha_venc.configure(state='normal')

    # 5. Métodos de gestión de movimientos 

    def agregar_movimiento(self):
        try:
            fecha_registro = self.fecha_reg.get_date().strftime('%d/%m/%Y')
            tipo_movimiento = self.tipo_movimiento_var.get()
            tipo_insumo = self.tipo_insumo_var.get()
            insumo = self.insumo_var.get()
            presentacion = self.presentacion_var.get()
            lote = self.lote_entry.get().upper()
            if self.sin_fecha_venc.get():
                fecha_venc_str = "N/A"
            else:
                fecha_venc_str = self.fecha_venc.get_date().strftime('%d/%m/%Y')
            cantidad_str = self.cantidad_entry.get()
            referencia = self.referencia_entry.get().upper()
            observaciones = self.observaciones_entry.get().upper()

            # Obtener datos de servicios
            area = self.area_var.get()
            distrito = self.distrito_var.get()
            tipo_servicio = self.tipo_servicio_var.get()
            servicio = self.servicio_var.get()

            salida_distrito = ''
            salida_servicio = ''
            if tipo_movimiento.strip().upper() == "SALIDA NIVEL INFERIOR":
                salida_distrito = self.salida_distrito_var.get()
                salida_servicio = self.salida_servicio_var.get()

            if not tipo_insumo:
                messagebox.showerror("Error", "Debe seleccionar un tipo de insumo")
                return

            if not all([tipo_movimiento, insumo, presentacion, lote, cantidad_str, referencia]):
                messagebox.showerror("Error", "Los campos son requeridos excepto observaciones")
                return

            cantidad = float(cantidad_str)

            # Insertar en el Treeview con TODOS los datos necesarios
            self.tree.insert('', 'end', values=(
                fecha_registro,      # 0
                referencia,          # 1
                tipo_movimiento,     # 2
                insumo,             # 3
                presentacion,       # 4
                servicio,           # 5
                lote,               # 6
                fecha_venc_str,     # 7
                cantidad,           # 8
                salida_distrito,    # 9
                salida_servicio,    # 10
                observaciones,      # 11
                tipo_insumo,        # 12
                area,               # 13 - NUEVO
                distrito,           # 14 - NUEVO
                tipo_servicio       # 15 - NUEVO
            ))

            self.limpiar_campos()

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

        # Tamaño inicial amplio para que se vean bien los widgets con los anchos que tienes
        ancho_ventana = 1000
        alto_ventana = 400

        # Obtener dimensiones de pantalla para centrar
        screen_width = editar_ventana.winfo_screenwidth()
        screen_height = editar_ventana.winfo_screenheight()

        x = (screen_width // 2) - (ancho_ventana // 2)
        y = (screen_height // 2) - (alto_ventana // 2)

        editar_ventana.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")
        editar_ventana.resizable(True, True)

        # Variables para edición
        edit_nivel_bodega_var = tk.StringVar(value="area")  # Default, luego se ajusta
        edit_area_var = tk.StringVar()
        edit_distrito_var = tk.StringVar()
        edit_tipo_servicio_var = tk.StringVar()
        edit_servicio_var = tk.StringVar()
        edit_tipo_insumo_var = tk.StringVar()
        edit_insumo_var = tk.StringVar()
        edit_presentacion_var = tk.StringVar()
        edit_tipo_movimiento_var = tk.StringVar()
        edit_salida_distrito_var = tk.StringVar()
        edit_salida_tipo_servicio_var = tk.StringVar()
        edit_salida_servicio_var = tk.StringVar()

        PADDING = 10

        main_frame = ttk.Frame(editar_ventana, padding=PADDING)
        main_frame.pack(fill="both", expand=True)

        # Frame Nivel de Bodega (radio buttons)
        frame_nivel_bodega = ttk.LabelFrame(main_frame, text="Nivel de Bodega")
        frame_nivel_bodega.pack(fill="x", pady=5)

        rb_area = ttk.Radiobutton(frame_nivel_bodega, text="Área", variable=edit_nivel_bodega_var, value="area")
        rb_distrito = ttk.Radiobutton(frame_nivel_bodega, text="Distrito", variable=edit_nivel_bodega_var, value="distrito")
        rb_servicio = ttk.Radiobutton(frame_nivel_bodega, text="Servicio", variable=edit_nivel_bodega_var, value="servicio")

        rb_area.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        rb_distrito.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        rb_servicio.grid(row=0, column=2, padx=10, pady=5, sticky="w")

        # Frame Servicios (Área, Distrito, Tipo Servicio, Servicio)
        frame_servicios = ttk.LabelFrame(main_frame, text="Servicios")
        frame_servicios.pack(fill="x", pady=PADDING)

        # Configurar columnas sin expansión para que no se estiren
        for col in range(8):
            frame_servicios.columnconfigure(col, weight=1)

        ttk.Label(frame_servicios, text="Área:", width=15, anchor="w").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        area_cb = AutocompleteCombobox(frame_servicios, textvariable=edit_area_var, width=25, state="normal")
        area_cb.set_completion_list([a['nombre'] for a in obtener_areas() or []])
        area_cb.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_servicios, text="Distrito:", width=15, anchor="w").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        distrito_cb = AutocompleteCombobox(frame_servicios, textvariable=edit_distrito_var, width=25, state="normal")
        distrito_cb.set_completion_list([d['nombre'] for d in obtener_distritos() or []])
        distrito_cb.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_servicios, text="Tipo de Servicio:", width=15, anchor="w").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        tipo_servicio_cb = AutocompleteCombobox(frame_servicios, textvariable=edit_tipo_servicio_var, width=25, state="normal")
        tipo_servicio_cb.grid(row=0, column=5, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_servicios, text="Servicio:", width=15, anchor="w").grid(row=0, column=6, padx=5, pady=5, sticky="w")
        servicio_cb = AutocompleteCombobox(frame_servicios, textvariable=edit_servicio_var, width=25, state="normal")
        servicio_cb.grid(row=0, column=7, padx=5, pady=5, sticky="ew")

        # Frame Insumos
        frame_insumos = ttk.LabelFrame(main_frame, text="Insumos")
        frame_insumos.pack(fill="x", pady=5)

        for col in range(6):
            frame_insumos.columnconfigure(col, weight=1)

        ttk.Label(frame_insumos, text="Tipo de Insumo:", width=15, anchor="w").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        tipo_insumo_cb = AutocompleteCombobox(frame_insumos, textvariable=edit_tipo_insumo_var, width=25, state="normal")
        tipo_insumo_cb.set_completion_list([ti['descripcion'] for ti in obtener_tipos_insumo() or []])
        tipo_insumo_cb.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_insumos, text="Insumo:", width=15, anchor="w").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        insumo_cb = AutocompleteCombobox(frame_insumos, textvariable=edit_insumo_var, width=25, state="normal")
        insumo_cb.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_insumos, text="Presentación:", width=15, anchor="w").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        presentacion_cb = AutocompleteCombobox(frame_insumos, textvariable=edit_presentacion_var, width=25, state="normal")
        presentacion_cb.grid(row=0, column=5, padx=5, pady=5, sticky="ew")

        # Frame Detalles del Movimiento
        frame_detalles = ttk.LabelFrame(main_frame, text="Detalles del Movimiento")
        frame_detalles.pack(fill="x", pady=5)

        for col in range(6):
            frame_detalles.columnconfigure(col, weight=1)

        ttk.Label(frame_detalles, text="Fecha de Registro:", width=15, anchor="w").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        fecha_edit = DateEntry(frame_detalles, width=25, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        fecha_edit.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_detalles, text="Referencia:", width=15, anchor="w").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        referencia_entry = ttk.Entry(frame_detalles, width=27)
        referencia_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_detalles, text="Tipo Movimiento:", width=15, anchor="w").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        tipo_mov_cb = AutocompleteCombobox(frame_detalles, textvariable=edit_tipo_movimiento_var, width=25, state="normal")
        tipo_mov_cb.set_completion_list([tm['descripcion'] for tm in obtener_tipos_movimiento() or []])
        tipo_mov_cb.grid(row=0, column=5, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_detalles, text="Lote:", width=15, anchor="w").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        lote_entry = ttk.Entry(frame_detalles, width=27)
        lote_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_detalles, text="Fecha Vencimiento:", width=15, anchor="w").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        fecha_venc_edit = DateEntry(frame_detalles, width=25, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        fecha_venc_edit.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
        
        edit_sin_fecha_venc = tk.BooleanVar()
        edit_check_sin_fecha = ttk.Checkbutton(
            frame_detalles,
            text="Sin fecha de vencimiento",
            variable=edit_sin_fecha_venc,
            command=lambda: fecha_venc_edit.configure(state='disabled' if edit_sin_fecha_venc.get() else 'normal')
        )
        edit_check_sin_fecha.grid(row=2, column=2, padx=5, pady=5, sticky="w")

        ttk.Label(frame_detalles, text="Cantidad:", width=15, anchor="w").grid(row=1, column=4, padx=5, pady=5, sticky="w")
        cantidad_entry = ttk.Entry(frame_detalles, width=27)
        cantidad_entry.grid(row=1, column=5, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_detalles, text="Observaciones:", width=15, anchor="w").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        observaciones_entry = ttk.Entry(frame_detalles, width=80)
        observaciones_entry.grid(row=2, column=1, columnspan=5, padx=5, pady=5, sticky="ew")

        # Frame Salida Nivel Inferior
        frame_salida_nivel_inferior_edit = ttk.LabelFrame(main_frame, text="Salida Nivel Inferior")

        ttk.Label(frame_salida_nivel_inferior_edit, text="Distrito:", width=15, anchor="w").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        salida_distrito_cb = AutocompleteCombobox(frame_salida_nivel_inferior_edit, textvariable=edit_salida_distrito_var, width=25, completevalues=[d['nombre'] for d in obtener_distritos() or []], state="disabled")
        salida_distrito_cb.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_salida_nivel_inferior_edit, text="Tipo de Servicio:", width=15, anchor="w").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        salida_tipo_servicio_cb = AutocompleteCombobox(frame_salida_nivel_inferior_edit, textvariable=edit_salida_tipo_servicio_var, width=25, completevalues=[], state="disabled")
        salida_tipo_servicio_cb.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        ttk.Label(frame_salida_nivel_inferior_edit, text="Servicio:", width=15, anchor="w").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        salida_servicio_cb = AutocompleteCombobox(frame_salida_nivel_inferior_edit, textvariable=edit_salida_servicio_var, width=25, completevalues=[], state="disabled")
        salida_servicio_cb.grid(row=0, column=5, padx=5, pady=5, sticky="ew")

        # 1. Funciones de actualización de estado de la UI
        
        def actualizar_estado_comboboxes_edit(*args):
            nivel = edit_nivel_bodega_var.get()
            if nivel == "area":
                area_cb.config(state="normal")
                distrito_cb.config(state="disabled")
                tipo_servicio_cb.config(state="disabled")
                servicio_cb.config(state="disabled")
            elif nivel == "distrito":
                area_cb.config(state="normal")
                distrito_cb.config(state="normal")
                tipo_servicio_cb.config(state="disabled")
                servicio_cb.config(state="disabled")
            elif nivel == "servicio":
                area_cb.config(state="normal")
                distrito_cb.config(state="normal")
                tipo_servicio_cb.config(state="normal")
                servicio_cb.config(state="normal")

            actualizar_tipos_movimiento_filtrados_edit()

            # Si el nivel es "distrito", llenar el combobox de distrito en "Salida Nivel Inferior" al inicio
            if nivel == "distrito" and edit_tipo_movimiento_var.get().strip().upper() == "SALIDA NIVEL INFERIOR":
                edit_salida_distrito_var.set(edit_distrito_var.get())
                actualizar_tipos_servicio_salida_edit()
        
        def actualizar_estado_salida_nivel_inferior_edit(*args):
            tipo_mov = edit_tipo_movimiento_var.get().strip().upper()
            nivel = edit_nivel_bodega_var.get()

            if tipo_mov == "SALIDA NIVEL INFERIOR":
                if not frame_salida_nivel_inferior_edit.winfo_ismapped():
                    try:
                        frame_salida_nivel_inferior_edit.pack(fill="x", pady=5, before=frame_botones)
                    except NameError:
                        frame_salida_nivel_inferior_edit.pack(fill="x", pady=5)

                if nivel == "area":
                    salida_distrito_cb.config(state="normal")
                    salida_tipo_servicio_cb.config(state="disabled")
                    salida_servicio_cb.config(state="disabled")
                elif nivel == "distrito":
                    # Llenar el combobox de distrito y bloquearlo
                    edit_salida_distrito_var.set(edit_distrito_var.get())
                    salida_distrito_cb.config(state="disabled")  # Bloquear el combobox
                    salida_distrito_cb.set_completion_list([edit_distrito_var.get()])  # Limitar las opciones solo al distrito seleccionado

                    salida_tipo_servicio_cb.config(state="normal")
                    salida_servicio_cb.config(state="normal")
                    actualizar_tipos_servicio_salida_edit()
                else:
                    salida_distrito_cb.config(state="disabled")
                    salida_tipo_servicio_cb.config(state="disabled")
                    salida_servicio_cb.config(state="disabled")

                editar_ventana.update_idletasks()
                ajustar_tamano_ventana_editar(True)
            else:
                frame_salida_nivel_inferior_edit.pack_forget()
                edit_salida_distrito_var.set('')
                edit_salida_tipo_servicio_var.set('')
                edit_salida_servicio_var.set('')
                editar_ventana.update_idletasks()
                ajustar_tamano_ventana_editar(False)
                
        def ajustar_tamano_ventana_editar(mostrar_salida):
            ancho_base = 1000
            alto_base = 400

            editar_ventana.update_idletasks()
            altura_frame = frame_salida_nivel_inferior_edit.winfo_reqheight() + 50  # margen extra

            if mostrar_salida:
                nuevo_alto = alto_base + altura_frame
            else:
                nuevo_alto = alto_base

            screen_width = editar_ventana.winfo_screenwidth()
            screen_height = editar_ventana.winfo_screenheight()

            x = max(0, (screen_width - ancho_base) // 2)
            y = max(0, (screen_height - nuevo_alto) // 2)

            editar_ventana.geometry(f"{ancho_base}x{nuevo_alto}+{x}+{y}")

        def actualizar_tipos_movimiento_filtrados_edit():
            nivel = edit_nivel_bodega_var.get()
            tipos_movimiento = [tm['descripcion'] for tm in obtener_tipos_movimiento() or []]

            if nivel in ("area", "distrito"):
                tipos_movimiento = [tm for tm in tipos_movimiento if tm not in ("ENTREGADO", "NO ENTREGADO")]
            elif nivel == "servicio":
                tipos_movimiento = [tm for tm in tipos_movimiento if tm != "SALIDA NIVEL INFERIOR"]

            tipo_mov_cb.config(completevalues=tipos_movimiento)

            if edit_tipo_movimiento_var.get() not in tipos_movimiento:
                edit_tipo_movimiento_var.set('')
        
        # 2. Funciones de actualización de datos de los combobox
        
        def actualizar_tipos_servicio_edit(*args):
            distrito_nombre = edit_distrito_var.get()
            distritos = obtener_distritos() or []
            distrito_id = next((d['id'] for d in distritos if d['nombre'] == distrito_nombre), None)

            if distrito_id:
                tipos_servicio = obtener_tipos_servicio_por_distrito(distrito_id) or []
                opciones = [ts['descripcion'] for ts in tipos_servicio]
                tipo_servicio_cb.set_completion_list(opciones)
                if edit_tipo_servicio_var.get() not in opciones:
                    edit_tipo_servicio_var.set('')
            else:
                tipo_servicio_cb.set_completion_list([])
                edit_tipo_servicio_var.set('')
                servicio_cb.set_completion_list([])
                edit_servicio_var.set('')

        def actualizar_servicios_edit(*args):
            distrito_nombre = edit_distrito_var.get()
            tipo_servicio_desc = edit_tipo_servicio_var.get()
            distritos = obtener_distritos() or []
            distrito_id = next((d['id'] for d in distritos if d['nombre'] == distrito_nombre), None)

            if distrito_id:
                tipos_servicio = obtener_tipos_servicio_por_distrito(distrito_id) or []
                tipo_servicio_id = next((ts['id'] for ts in tipos_servicio if ts['descripcion'] == tipo_servicio_desc), None)
                if tipo_servicio_id:
                    servicios = obtener_servicios_por_tipo(tipo_servicio_id) or []
                    opciones = [s['nombre'] for s in servicios]
                    servicio_cb.set_completion_list(opciones)
                    if edit_servicio_var.get() not in opciones:
                        edit_servicio_var.set('')
            else:
                servicio_cb.set_completion_list([])
                edit_servicio_var.set('')

        def actualizar_tipos_servicio_salida_edit(*args):
            distrito_nombre = edit_salida_distrito_var.get()
            distritos = obtener_distritos() or []
            distrito_id = next((d['id'] for d in distritos if d['nombre'] == distrito_nombre), None)

            if distrito_id:
                tipos_servicio = obtener_tipos_servicio_por_distrito(distrito_id) or []
                opciones = [ts['descripcion'] for ts in tipos_servicio]
                salida_tipo_servicio_cb.set_completion_list(opciones)
                if edit_salida_tipo_servicio_var.get() not in opciones:
                    edit_salida_tipo_servicio_var.set('')
                    edit_salida_servicio_var.set('')
            else:
                salida_tipo_servicio_cb.set_completion_list([])
                edit_salida_tipo_servicio_var.set('')
                salida_servicio_cb.set_completion_list([])
                edit_salida_servicio_var.set('')

        def actualizar_servicios_salida_edit(*args):
            distrito_nombre = edit_salida_distrito_var.get()
            tipo_servicio_desc = edit_salida_tipo_servicio_var.get()
            distritos = obtener_distritos() or []
            distrito_id = next((d['id'] for d in distritos if d['nombre'] == distrito_nombre), None)

            if distrito_id:
                tipos_servicio = obtener_tipos_servicio_por_distrito(distrito_id) or []
                tipo_servicio_id = next((ts['id'] for ts in tipos_servicio if ts['descripcion'] == tipo_servicio_desc), None)
                if tipo_servicio_id:
                    servicios = obtener_servicios_por_tipo(tipo_servicio_id) or []
                    opciones = [s['nombre'] for s in servicios]
                    salida_servicio_cb.set_completion_list(opciones)
                    if edit_salida_servicio_var.get() not in opciones:
                        edit_salida_servicio_var.set('')
            else:
                salida_servicio_cb.set_completion_list([])
                edit_salida_servicio_var.set('')

        def actualizar_insumos_edit(*args):
            tipo_insumo_desc = edit_tipo_insumo_var.get()
            tipos_insumo = obtener_tipos_insumo() or []
            tipo_insumo_id = next((ti['id'] for ti in tipos_insumo if ti['descripcion'] == tipo_insumo_desc), None)

            if tipo_insumo_id:
                insumos = obtener_insumos_por_tipo(tipo_insumo_id) or []
                insumo_cb.set_completion_list([i['nombre'] for i in insumos])
                if edit_insumo_var.get() not in [i['nombre'] for i in insumos]:
                    edit_insumo_var.set('')
            else:
                insumo_cb.set_completion_list([])
                edit_insumo_var.set('')

        def actualizar_presentacion_edit(*args):
            tipo_insumo_desc = edit_tipo_insumo_var.get()
            insumo_nombre = edit_insumo_var.get()
            tipos_insumo = obtener_tipos_insumo() or []
            tipo_insumo_id = next((ti['id'] for ti in tipos_insumo if ti['descripcion'] == tipo_insumo_desc), None)

            if tipo_insumo_id and insumo_nombre:
                insumos = obtener_insumos_por_tipo(tipo_insumo_id) or []
                insumo_seleccionado = next((i for i in insumos if i['nombre'] == insumo_nombre), None)
                if insumo_seleccionado and insumo_seleccionado['nombre_presentacion']:
                    presentacion_cb.set_completion_list([insumo_seleccionado['nombre_presentacion']])
                    edit_presentacion_var.set(insumo_seleccionado['nombre_presentacion'])
                    return
            presentacion_cb.set_completion_list([])
            edit_presentacion_var.set('')
        
        # 3. Funciones de carga y guardado
        
        def cargar_datos_iniciales():
            if valores[8] and valores[9]:  
                edit_nivel_bodega_var.set("area")
            else:
                edit_nivel_bodega_var.set("area")

            actualizar_estado_comboboxes_edit()
            actualizar_estado_salida_nivel_inferior_edit()
            
            # Cargar valores en campos
            edit_area_var.set(self.area_var.get())
            edit_distrito_var.set(self.distrito_var.get())
            edit_tipo_servicio_var.set(self.tipo_servicio_var.get())
            edit_servicio_var.set(self.servicio_var.get())
            edit_tipo_insumo_var.set(self.tipo_insumo_var.get())
            edit_insumo_var.set(valores[3])
            edit_presentacion_var.set(valores[4])
            fecha_edit.set_date(datetime.strptime(valores[0], '%d/%m/%Y').date())
            referencia_entry.delete(0, tk.END)
            referencia_entry.insert(0, valores[1])
            edit_tipo_movimiento_var.set(valores[2])
            lote_entry.delete(0, tk.END)
            lote_entry.insert(0, valores[6])
            if valores[7] == "N/A":
                fecha_venc_edit.set_date(datetime.now().date())
                fecha_venc_edit.configure(state='disabled')
                edit_sin_fecha_venc.set(True)
            else:
                fecha_venc_edit.set_date(datetime.strptime(valores[7], '%d/%m/%Y').date())
                fecha_venc_edit.configure(state='normal')
                edit_sin_fecha_venc.set(False)
            cantidad_entry.delete(0, tk.END)
            cantidad_entry.insert(0, valores[8])
            observaciones_entry.delete(0, tk.END)
            if valores[11]:
                observaciones_entry.insert(0, valores[11])

            # Salida nivel inferior
            edit_salida_distrito_var.set(valores[9] if valores[9] else '')
            edit_salida_tipo_servicio_var.set('')
            edit_salida_servicio_var.set(valores[10] if valores[10] else '')

            # Actualizar estado combos y frame salida
            actualizar_estado_comboboxes_edit()
            actualizar_estado_salida_nivel_inferior_edit()
        
        editar_ventana.after(100, cargar_datos_iniciales)
        
        frame_salida_nivel_inferior_edit.pack(fill="x", pady=5)

        # Botones Guardar y Cerrar
        frame_botones = ttk.Frame(main_frame)
        frame_botones.pack(pady=10)
        
        def guardar_cambios():
            try:
                nuevos_valores = (
                    fecha_edit.get_date().strftime('%d/%m/%Y'),    # 0
                    referencia_entry.get().upper(),                # 1
                    edit_tipo_movimiento_var.get(),                # 2
                    edit_insumo_var.get(),                         # 3
                    edit_presentacion_var.get(),                   # 4
                    edit_servicio_var.get(),                       # 5
                    lote_entry.get().upper(),                      # 6
                    "N/A" if edit_sin_fecha_venc.get() else fecha_venc_edit.get_date().strftime('%d/%m/%Y'), # 7
                    cantidad_entry.get(),                          # 8
                    edit_salida_distrito_var.get(),                # 9
                    edit_salida_servicio_var.get(),                # 10
                    observaciones_entry.get().upper(),             # 11
                    edit_tipo_insumo_var.get(),                    # 12
                    edit_area_var.get(),                           # 13
                    edit_distrito_var.get(),                       # 14 
                    edit_tipo_servicio_var.get()                   # 15 
                )

                if not all(nuevos_valores[:8]):
                    messagebox.showerror("Error", "Todos los campos son requeridos excepto observaciones")
                    return

                try:
                    float(nuevos_valores[8])
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

        # Bindings
        edit_nivel_bodega_var.trace_add('write', actualizar_estado_comboboxes_edit)
        edit_tipo_movimiento_var.trace_add('write', actualizar_estado_salida_nivel_inferior_edit)
        edit_area_var.trace_add('write', lambda *a: self.on_area_selected_edit(edit_area_var, edit_distrito_var, distrito_cb))
        edit_distrito_var.trace_add('write', actualizar_tipos_servicio_edit)
        edit_tipo_servicio_var.trace_add('write', actualizar_servicios_edit)
        edit_salida_distrito_var.trace_add('write', actualizar_tipos_servicio_salida_edit)
        edit_salida_tipo_servicio_var.trace_add('write', actualizar_servicios_salida_edit)
        edit_tipo_insumo_var.trace_add('write', actualizar_insumos_edit)
        edit_insumo_var.trace_add('write', actualizar_presentacion_edit)       

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

                # Obtener datos con los índices correctos
                fecha_registro_str = valores[0]
                referencia = valores[1]
                tipo_movimiento_desc = valores[2]
                insumo_nombre = valores[3]
                presentacion_nombre = valores[4]
                servicio_nombre = valores[5]
                lote = valores[6]
                fecha_vencimiento_str = valores[7]
                cantidad = float(valores[8])
                salida_distrito_nombre = valores[9] if valores[9] else None
                salida_servicio_nombre = valores[10] if valores[10] else None
                observaciones = valores[11] if valores[11] else None
                tipo_insumo_desc = valores[12]
                area_nombre = valores[13]           # NUEVO
                distrito_nombre = valores[14]       # NUEVO
                tipo_servicio_desc = valores[15]    # NUEVO

                # Validaciones
                if not tipo_insumo_desc:
                    raise ValueError("El tipo de insumo no puede estar vacío")

                # Obtener IDs
                area_id = None
                if area_nombre:
                    areas = obtener_areas() or []
                    area_id = next((a['id'] for a in areas if a['nombre'] == area_nombre), None)

                distrito_id = obtener_id_distrito(distrito_nombre) if distrito_nombre else None

                tipo_servicio_id = None
                if tipo_servicio_desc and distrito_id:
                    tipos_servicio = obtener_tipos_servicio_por_distrito(distrito_id) or []
                    tipo_servicio_id = next((ts['id'] for ts in tipos_servicio if ts['descripcion'] == tipo_servicio_desc), None)

                servicio_id = None
                if servicio_nombre and tipo_servicio_id:
                    servicios = obtener_servicios_por_tipo(tipo_servicio_id) or []
                    servicio_id = next((s['id'] for s in servicios if s['nombre'] == servicio_nombre), None)

                tipo_insumo_id = obtener_id_tipo_insumo(tipo_insumo_desc)
                if tipo_insumo_id is None:
                    raise ValueError(f"No se encontró el tipo de insumo: {tipo_insumo_desc}")

                insumo_id = obtener_id_insumo(insumo_nombre, tipo_insumo_id)
                if insumo_id is None:
                    raise ValueError(f"No se encontró el insumo: {insumo_nombre}")

                presentacion_id = obtener_id_presentacion(presentacion_nombre) if presentacion_nombre else None
                tipo_movimiento_id = obtener_id_tipo_movimiento(tipo_movimiento_desc)

                # Convertir fechas
                fecha_registro = datetime.strptime(fecha_registro_str, '%d/%m/%Y')
                if fecha_vencimiento_str == "N/A":
                    fecha_vencimiento = None
                else:
                    fecha_vencimiento = datetime.strptime(fecha_vencimiento_str, '%d/%m/%Y')

                # Manejar salida nivel inferior
                salida_distrito_id = obtener_id_distrito(salida_distrito_nombre) if salida_distrito_nombre else None
                salida_servicio_id = obtener_id_servicio(salida_servicio_nombre) if salida_servicio_nombre else None

                # Crear diccionario con datos del movimiento
                movimiento_data = {
                    'fecha_registro': fecha_registro,
                    'referencia': referencia,
                    'tipo_movimiento_id': tipo_movimiento_id,
                    'area_id': area_id,
                    'distrito_id': distrito_id,
                    'tipo_servicio_id': tipo_servicio_id,
                    'servicio_id': servicio_id,
                    'tipo_insumo_id': tipo_insumo_id,
                    'insumo_id': insumo_id,
                    'presentacion_id': presentacion_id,
                    'lote': lote,
                    'fecha_vencimiento': fecha_vencimiento,
                    'cantidad': cantidad,
                    'salida_distrito_id': salida_distrito_id,
                    'salida_servicio_id': salida_servicio_id,
                    'observaciones': observaciones
                }

                # Debug: imprimir los IDs que se van a guardar
                print(f"Guardando movimiento: area_id={area_id}, distrito_id={distrito_id}, servicio_id={servicio_id}")

                # Guardar movimiento
                guardar_movimiento(movimiento_data)
                movimientos_guardados += 1

            except Exception as e:
                errores.append(f"Error en movimiento {movimientos_guardados + 1}: {str(e)}")

        # Mostrar mensaje de resultado
        if errores:
            messagebox.showerror("Errores al guardar",
                                f"Se guardaron {movimientos_guardados} movimientos, pero hubo errores:\n" +
                                "\n".join(errores))
        else:
            messagebox.showinfo("Éxito",
                                f"Se guardaron {movimientos_guardados} movimientos correctamente")
            self.tree.delete(*self.tree.get_children())
    
    # 6. Métodos de utilidad
    
    def limpiar_campos(self):
        self.area_var.set('')
        self.distrito_var.set('')
        self.tipo_servicio_var.set('')
        self.servicio_var.set('')
        self.tipo_insumo_var.set('')
        self.insumo_var.set('')
        self.presentacion_var.set('')
        self.tipo_movimiento_var.set('')
        self.salida_distrito_var.set('')
        self.salida_tipo_servicio_var.set('')
        self.salida_servicio_var.set('')

        # Limpiar entries
        self.lote_entry.delete(0, 'end')
        self.referencia_entry.delete(0, 'end')
        self.cantidad_entry.delete(0, 'end')
        self.observaciones_entry.delete(0, 'end')

        # Resetear fechas a la fecha actual
        self.fecha_reg.set_date(datetime.now())
        self.fecha_venc.set_date(datetime.now())

        # Resetear nivel de bodega a "area"
        self.nivel_bodega_var.set("area")

        # Actualizar estados de los combobox
        self.actualizar_estado_comboboxes()

        # Ocultar frame de salida nivel inferior si está visible
        if self.frame_salida_nivel_inferior.winfo_ismapped():
            self.frame_salida_nivel_inferior.pack_forget()
    
    def ajustar_tamano_ventana(self, mostrar_salida):
        """Ajusta el tamaño de la ventana cuando se muestra/oculta el frame de salida"""
        if mostrar_salida:
            # Calcular altura adicional necesaria
            self.parent.update_idletasks()
            altura_frame = self.frame_salida_nivel_inferior.winfo_reqheight() + 50
            self.main_window.resize_window_for_content(altura_frame)
        else:
            # Restaurar tamaño original
            self.main_window.reset_window_size()
        
    def cerrar_ventana(self):
        if messagebox.askyesno("Confirmar", "¿Está seguro que desea cerrar esta ventana?"):
            for widget in self.parent.winfo_children():
                widget.destroy()
            self.main_window.show_welcome_screen()

    # 7. Métodos auxiliares
    
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
    
    def on_area_selected_edit(self, area_var, distrito_var, distrito_cb):
        area_nombre = area_var.get()
        areas = obtener_areas() or []
        area_id = next((a['id'] for a in areas if a['nombre'] == area_nombre), None)

        if area_id:
            distritos = obtener_distritos_por_area(area_id) or []
            distritos_nombres = [d['nombre'] for d in distritos]
            distrito_cb.set_completion_list(distritos_nombres)
            if distrito_var.get() not in distritos_nombres:
                distrito_var.set('')
        else:
            distrito_cb.set_completion_list([])
            distrito_var.set('')