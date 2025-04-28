import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import datetime
import sys
import os

# Agregar el directorio raíz del proyecto al PATH de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.db_manager import (
    obtener_distritos,
    obtener_tipos_servicio_por_distrito,
    obtener_servicios_por_tipo,
    obtener_tipos_insumo,
    obtener_insumos_por_tipo,
    obtener_presentaciones,
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
        # Frame Servicios
        self.frame_servicios = ttk.LabelFrame(self.parent, text="Servicios")
        self.frame_servicios.pack(fill="x", padx=10, pady=10)

        # Distrito
        ttk.Label(self.frame_servicios, text="Distrito:", anchor="w").grid(
            row=0, column=0, padx=5, pady=5, sticky="w")
        self.distrito_cb = ttk.Combobox(self.frame_servicios, textvariable=self.distrito_var,
                                state="readonly", width=25)
        self.distrito_cb['values'] = [d['nombre'] for d in obtener_distritos() or []]
        self.distrito_cb.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Tipo de Servicio
        ttk.Label(self.frame_servicios, text="Tipo de Servicio:", anchor="w").grid(
            row=0, column=2, padx=5, pady=5, sticky="w")
        self.tipo_servicio_cb = ttk.Combobox(self.frame_servicios, textvariable=self.tipo_servicio_var,
                                    state="readonly", width=25)
        self.tipo_servicio_cb.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # Servicio
        ttk.Label(self.frame_servicios, text="Servicio:", anchor="w").grid(
            row=0, column=4, padx=5, pady=5, sticky="w")
        self.servicio_cb = ttk.Combobox(self.frame_servicios, textvariable=self.servicio_var,
                                state="readonly", width=25)
        self.servicio_cb.grid(row=0, column=5, padx=5, pady=5, sticky="w")

        # Frame Insumos
        self.frame_insumos = ttk.LabelFrame(self.parent, text="Insumos")
        self.frame_insumos.pack(fill="x", padx=10, pady=10)

        # Tipo de Insumo
        ttk.Label(self.frame_insumos, text="Tipo de Insumo:", anchor="w").grid(
            row=0, column=0, padx=5, pady=5, sticky="w")
        self.tipo_insumo_cb = ttk.Combobox(self.frame_insumos, textvariable=self.tipo_insumo_var,
                                    state="readonly", width=25)
        self.tipo_insumo_cb['values'] = [ti['descripcion'] for ti in obtener_tipos_insumo() or []]
        self.tipo_insumo_cb.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Insumo
        ttk.Label(self.frame_insumos, text="Insumo:", anchor="w").grid(
            row=0, column=2, padx=5, pady=5, sticky="w")
        self.insumo_cb = ttk.Combobox(self.frame_insumos, textvariable=self.insumo_var,
                                state="readonly", width=25)
        self.insumo_cb.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # Presentación
        ttk.Label(self.frame_insumos, text="Presentación:", anchor="w").grid(
            row=0, column=4, padx=5, pady=5, sticky="w")
        self.presentacion_cb = ttk.Combobox(self.frame_insumos, textvariable=self.presentacion_var,
                                    state="readonly", width=25)
        self.presentacion_cb['values'] = [p['nombre'] for p in obtener_presentaciones() or []]
        self.presentacion_cb.grid(row=0, column=5, padx=5, pady=5, sticky="w")

        # Lote
        ttk.Label(self.frame_insumos, text="Lote:", anchor="w").grid(
            row=1, column=0, padx=5, pady=5, sticky="w")
        self.lote_entry = ttk.Entry(self.frame_insumos, width=27)
        self.lote_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Fecha de Vencimiento
        ttk.Label(self.frame_insumos, text="Fecha de Vencimiento:", anchor="w").grid(
            row=1, column=2, padx=5, pady=5, sticky="w")
        self.fecha_venc = DateEntry(self.frame_insumos, width=25, background='darkblue',
                            foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        self.fecha_venc.grid(row=1, column=3, padx=5, pady=5, sticky="w")

        # Frame Registro de Movimiento
        self.frame_registro = ttk.LabelFrame(self.parent, text="Registro de Movimiento")
        self.frame_registro.pack(fill="x", padx=10, pady=10)

        # Fecha de Registro
        ttk.Label(self.frame_registro, text="Fecha de Registro:", anchor="w").grid(
            row=0, column=0, padx=5, pady=5, sticky="w")
        self.fecha_reg = DateEntry(self.frame_registro, width=25, background='darkblue',
                            foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        self.fecha_reg.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Referencia
        ttk.Label(self.frame_registro, text="Referencia:", anchor="w").grid(
            row=0, column=2, padx=5, pady=5, sticky="w")
        self.referencia_entry = ttk.Entry(self.frame_registro, width=27)
        self.referencia_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # Tipo de Movimiento
        ttk.Label(self.frame_registro, text="Tipo de Movimiento:", anchor="w").grid(
            row=0, column=4, padx=5, pady=5, sticky="w")
        self.tipo_mov_cb = ttk.Combobox(self.frame_registro, textvariable=self.tipo_movimiento_var,
                                state="readonly", width=25)
        self.tipo_mov_cb['values'] = [tm['descripcion'] for tm in obtener_tipos_movimiento() or []]
        self.tipo_mov_cb.grid(row=0, column=5, padx=5, pady=5, sticky="w")

        # Cantidad
        ttk.Label(self.frame_registro, text="Cantidad:", anchor="w").grid(
            row=1, column=0, padx=5, pady=5, sticky="w")
        self.cantidad_entry = ttk.Entry(self.frame_registro, width=27)
        self.cantidad_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Observaciones
        ttk.Label(self.frame_registro, text="Observaciones:", anchor="w").grid(
            row=1, column=2, padx=5, pady=5, sticky="w")
        self.observaciones_entry = ttk.Entry(self.frame_registro, width=60)
        self.observaciones_entry.grid(row=1, column=3, columnspan=3, padx=5, pady=5, sticky="w")

        # Botón Agregar Movimiento
        self.btn_agregar = ttk.Button(self.parent, text="Agregar Movimiento", command=self.agregar_movimiento)
        self.btn_agregar.pack(pady=10)

        # Frame Movimientos (Treeview)
        self.frame_movimientos = ttk.LabelFrame(self.parent, text="Movimientos")
        self.frame_movimientos.pack(fill="both", expand=True, padx=10, pady=10)

        # Frame contenedor para Treeview y scrollbars
        self.tree_frame = ttk.Frame(self.frame_movimientos)
        self.tree_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Crear contenedor interno para el Treeview y scrollbars
        self.tree_container = ttk.Frame(self.tree_frame)
        self.tree_container.pack(fill="both", expand=True)

        # Configurar el grid del contenedor interno
        self.tree_container.grid_rowconfigure(0, weight=1)
        self.tree_container.grid_columnconfigure(0, weight=1)

        # Crear Treeview con scrollbars
        columns = ('fecha_registro', 'referencia', 'tipo_movimiento', 'insumo', 'presentacion',
                'lote', 'fecha_vencimiento', 'cantidad', 'observaciones')

        # Crear el Treeview
        self.tree = ttk.Treeview(self.tree_container, columns=columns, show='headings', height=10)

        # Definir los encabezados y configurar las columnas
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

        # Configurar las columnas y sus encabezados
        for col in columns:
            self.tree.heading(col, text=encabezados[col])
            self.tree.column(col, width=150, minwidth=150)

        # Crear los scrollbars
        self.scrollbar_y = ttk.Scrollbar(self.tree_container, orient="vertical", command=self.tree.yview)
        self.scrollbar_x = ttk.Scrollbar(self.tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.scrollbar_y.set, xscrollcommand=self.scrollbar_x.set)

        # Colocar el Treeview y los scrollbars usando grid
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.scrollbar_y.grid(row=0, column=1, sticky="ns")
        self.scrollbar_x.grid(row=1, column=0, sticky="ew")

        # Configurar el tamaño mínimo del frame contenedor
        self.tree_frame.update()
        min_height = 300  # altura mínima en píxeles
        self.tree_frame.configure(height=min_height)

        # Agregar binding para el evento de configuración
        def on_treeview_configure(event):
            # Ajustar el ancho de las columnas proporcionalmente
            width = event.width
            col_width = max(150, width // len(columns) - 5)  # -5 para el espacio entre columnas
            for col in columns:
                self.tree.column(col, width=col_width, minwidth=150)

        self.tree.bind('<Configure>', on_treeview_configure)

        # Frame para botones
        self.frame_botones = ttk.Frame(self.parent)
        self.frame_botones.pack(fill="x", padx=10, pady=10)

        # Botones
        self.btn_editar = ttk.Button(self.frame_botones, text="Editar", command=self.editar_movimiento)
        self.btn_editar.pack(side="left", padx=5)
        self.btn_eliminar = ttk.Button(self.frame_botones, text="Eliminar", command=self.eliminar_movimiento)
        self.btn_eliminar.pack(side="left", padx=5)
        self.btn_guardar = ttk.Button(self.frame_botones, text="Guardar Movimientos", command=self.guardar_movimientos)
        self.btn_guardar.pack(side="left", padx=5)
        self.btn_cerrar = ttk.Button(self.frame_botones, text="Cerrar", command=self.cerrar_ventana)
        self.btn_cerrar.pack(side="right", padx=5)

    def setup_bindings(self):
        self.distrito_var.trace('w', self.actualizar_tipos_servicio)
        self.tipo_servicio_var.trace('w', self.actualizar_servicios)
        self.tipo_insumo_var.trace('w', self.actualizar_insumos)

    def actualizar_tipos_servicio(self, *args):
        distrito_id = next((d['id'] for d in obtener_distritos()
                        if d['nombre'] == self.distrito_var.get()), None)
        if distrito_id:
            tipos_servicio = obtener_tipos_servicio_por_distrito(distrito_id)
            self.tipo_servicio_cb['values'] = [ts['descripcion'] for ts in tipos_servicio or []]
            self.tipo_servicio_var.set('')
            self.servicio_var.set('')

    def actualizar_servicios(self, *args):
        try:
            tipo_servicio_id = next((ts['id'] for ts in obtener_tipos_servicio_por_distrito(
                next(d['id'] for d in obtener_distritos() if d['nombre'] == self.distrito_var.get()))
                if ts['descripcion'] == self.tipo_servicio_var.get()), None)
            if tipo_servicio_id:
                servicios = obtener_servicios_por_tipo(tipo_servicio_id)
                self.servicio_cb['values'] = [s['nombre'] for s in servicios or []]
                self.servicio_var.set('')
        except Exception:
            self.servicio_cb['values'] = []
            self.servicio_var.set('')

    def actualizar_insumos(self, *args):
        tipo_insumo_id = next((ti['id'] for ti in obtener_tipos_insumo()
                            if ti['descripcion'] == self.tipo_insumo_var.get()), None)
        if tipo_insumo_id:
            insumos = obtener_insumos_por_tipo(tipo_insumo_id)
            self.insumo_cb['values'] = [i['nombre'] for i in insumos or []]
            self.insumo_var.set('')

    def agregar_movimiento(self):
        try:
            fecha_registro = self.fecha_reg.get_date().strftime('%d/%m/%Y')
            tipo_movimiento = self.tipo_movimiento_var.get()
            insumo = self.insumo_var.get()
            presentacion = self.presentacion_var.get()
            lote = self.lote_entry.get()
            fecha_venc_str = self.fecha_venc.get_date().strftime('%d/%m/%Y')
            cantidad = float(self.cantidad_entry.get())
            referencia = self.referencia_entry.get()
            observaciones = self.observaciones_entry.get()

            if not all([tipo_movimiento, insumo, presentacion, lote, cantidad, referencia]):
                messagebox.showerror("Error", "Los campos son requeridos excepto observaciones")
                return

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
        editar_ventana.geometry("400x300")

        ttk.Label(editar_ventana, text="Fecha de Registro:").pack(pady=5)
        fecha_edit = DateEntry(editar_ventana, width=12, background='darkblue',
                            foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        fecha_edit.pack(pady=5)
        fecha_actual = datetime.strptime(valores[0], '%d/%m/%Y').date()
        fecha_edit.set_date(fecha_actual)

        def guardar_cambios():
            nuevos_valores = (
                fecha_edit.get_date().strftime('%d/%m/%Y'),
                # Aquí agregarías el resto de los valores editados
            )
            self.tree.item(selected_item, values=nuevos_valores)
            editar_ventana.destroy()

        ttk.Button(editar_ventana, text="Guardar", command=guardar_cambios).pack(pady=10)

    def eliminar_movimiento(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un movimiento para eliminar")
            return

        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este movimiento?"):
            self.tree.delete(selected_item)
    
    def guardar_movimientos(self):
        try:
            # Obtener todos los items del Treeview
            items = self.tree.get_children()

            if not items:
                messagebox.showwarning("Advertencia", "No hay movimientos para guardar")
                return

            # Confirmar antes de guardar
            if not messagebox.askyesno("Confirmar", "¿Está seguro de guardar todos los movimientos?"):
                return

            movimientos_guardados = 0
            errores = []

            for item in items:
                try:
                    valores = self.tree.item(item)['values']

                    # Obtener los IDs necesarios
                    distrito_id = obtener_id_distrito(self.distrito_var.get())
                    tipo_servicio_id = obtener_id_tipo_servicio(self.tipo_servicio_var.get())
                    servicio_id = obtener_id_servicio(self.servicio_var.get())
                    tipo_insumo_id = obtener_id_tipo_insumo(self.tipo_insumo_var.get())
                    insumo_id = obtener_id_insumo(valores[3])  # índice del insumo en el tree
                    presentacion_id = obtener_id_presentacion(valores[4])  # índice de la presentación
                    tipo_movimiento_id = obtener_id_tipo_movimiento(valores[2])  # índice del tipo de movimiento

                    # Convertir las fechas al formato correcto
                    fecha_registro = datetime.strptime(valores[0], '%d/%m/%Y')
                    fecha_vencimiento = datetime.strptime(valores[6], '%d/%m/%Y')

                    # Crear diccionario con los datos del movimiento
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

                    # Guardar el movimiento en la base de datos
                    guardar_movimiento(movimiento_data)
                    movimientos_guardados += 1

                except Exception as e:
                    errores.append(f"Error en movimiento {movimientos_guardados + 1}: {str(e)}")

            # Mostrar resultado
            if errores:
                mensaje_error = "\n".join(errores)
                messagebox.showerror("Errores al guardar",
                                f"Se guardaron {movimientos_guardados} movimientos, pero hubo errores:\n{mensaje_error}")
            else:
                messagebox.showinfo("Éxito",
                                f"Se guardaron {movimientos_guardados} movimientos correctamente")
                # Limpiar el Treeview después de guardar exitosamente
                self.tree.delete(*self.tree.get_children())

        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar los movimientos: {str(e)}")
    
    def cerrar_ventana(self):
        if messagebox.askyesno("Confirmar", "¿Está seguro que desea cerrar esta ventana?"):
            # Limpiar el frame principal
            for widget in self.parent.winfo_children():
                widget.destroy()
            # Mostrar la pantalla de bienvenida
            self.main_window.show_welcome_screen()