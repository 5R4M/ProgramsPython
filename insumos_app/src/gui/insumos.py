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
    obtener_tipos_movimiento
)

def abrir_ingreso_insumos(ventana_principal):
    # Ocultar ventana principal
    ventana_principal.withdraw()

    # Crear ventana de insumos
    ventana = tk.Toplevel()
    ventana.title("Ingreso de Insumos")
    ventana.geometry("1000x800")
    
    # Función para manejar el cierre de la ventana
    def on_closing():
        if messagebox.askokcancel("Confirmar", "¿Está seguro que desea cerrar la ventana?"):
            ventana.destroy()
            ventana_principal.deiconify()

    # Configurar el protocolo de cierre
    ventana.protocol("WM_DELETE_WINDOW", on_closing)

    def centrar_ventana(ventana):
        ventana.update_idletasks()
        width = ventana.winfo_width()
        height = ventana.winfo_height()
        x = (ventana.winfo_screenwidth() // 2) - (width // 2)
        y = (ventana.winfo_screenheight() // 2) - (height // 2)
        ventana.geometry(f'{width}x{height}+{x}+{y}')

    centrar_ventana(ventana)

    # Variables para los combobox
    distrito_var = tk.StringVar()
    tipo_servicio_var = tk.StringVar()
    servicio_var = tk.StringVar()
    tipo_insumo_var = tk.StringVar()
    insumo_var = tk.StringVar()
    presentacion_var = tk.StringVar()
    tipo_movimiento_var = tk.StringVar()

    # Primero, definimos algunas constantes para mantener consistencia
    LABEL_WIDTH = 15  # Ancho para todas las etiquetas
    WIDGET_WIDTH = 25  # Ancho para todos los widgets de entrada
    PADDING_X = 10    # Padding horizontal
    PADDING_Y = 5     # Padding vertical

    # Función auxiliar para crear etiquetas con estilo consistente
    def create_label(parent, text):
        return ttk.Label(parent, text=text, anchor="w", width=LABEL_WIDTH)

    # Función auxiliar para configurar el grid de un frame
    def configure_grid(frame):
        for i in range(6):
            if i % 2 == 0:  # Columnas de etiquetas
                frame.grid_columnconfigure(i, weight=0, minsize=120)
            else:  # Columnas de campos
                frame.grid_columnconfigure(i, weight=1, minsize=200)
  
    # Frame Servicios
    frame_servicios = ttk.LabelFrame(ventana, text="Servicios")
    frame_servicios.pack(fill="x", padx=10, pady=10)
    
    # Agregar padding interno al frame
    for widget in frame_servicios.winfo_children():
        widget.grid_configure(pady=10)

    # Distrito
    ttk.Label(frame_servicios, text="Distrito:", anchor="w").grid(
        row=0, column=0, padx=5, pady=5, sticky="w")
    distrito_cb = ttk.Combobox(frame_servicios, textvariable=distrito_var,
                            state="readonly", width=25)
    distrito_cb['values'] = [d['nombre'] for d in obtener_distritos() or []]
    distrito_cb.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    # Tipo de Servicio
    ttk.Label(frame_servicios, text="Tipo de Servicio:", anchor="w").grid(
        row=0, column=2, padx=5, pady=5, sticky="w")
    tipo_servicio_cb = ttk.Combobox(frame_servicios, textvariable=tipo_servicio_var,
                                state="readonly", width=25)
    tipo_servicio_cb.grid(row=0, column=3, padx=5, pady=5, sticky="w")

    # Servicio
    ttk.Label(frame_servicios, text="Servicio:", anchor="w").grid(
        row=0, column=4, padx=5, pady=5, sticky="w")
    servicio_cb = ttk.Combobox(frame_servicios, textvariable=servicio_var,
                            state="readonly", width=25)
    servicio_cb.grid(row=0, column=5, padx=5, pady=5, sticky="w")

    # Frame Insumos
    frame_insumos = ttk.LabelFrame(ventana, text="Insumos")
    frame_insumos.pack(fill="x", padx=10, pady=10)
    
    # Agregar padding interno al frame
    for widget in frame_insumos.winfo_children():
        widget.grid_configure(pady=10)

    # Tipo de Insumo
    ttk.Label(frame_insumos, text="Tipo de Insumo:", anchor="w").grid(
        row=0, column=0, padx=5, pady=5, sticky="w")
    tipo_insumo_cb = ttk.Combobox(frame_insumos, textvariable=tipo_insumo_var,
                                state="readonly", width=25)
    tipo_insumo_cb['values'] = [ti['descripcion'] for ti in obtener_tipos_insumo() or []]
    tipo_insumo_cb.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    # Insumo
    ttk.Label(frame_insumos, text="Insumo:", anchor="w").grid(
        row=0, column=2, padx=5, pady=5, sticky="w")
    insumo_cb = ttk.Combobox(frame_insumos, textvariable=insumo_var,
                            state="readonly", width=25)
    insumo_cb.grid(row=0, column=3, padx=5, pady=5, sticky="w")

    # Presentación
    ttk.Label(frame_insumos, text="Presentación:", anchor="w").grid(
        row=0, column=4, padx=5, pady=5, sticky="w")
    presentacion_cb = ttk.Combobox(frame_insumos, textvariable=presentacion_var,
                                state="readonly", width=25)
    presentacion_cb['values'] = [p['nombre'] for p in obtener_presentaciones() or []]
    presentacion_cb.grid(row=0, column=5, padx=5, pady=5, sticky="w")

    # Lote
    ttk.Label(frame_insumos, text="Lote:", anchor="w").grid(
        row=1, column=0, padx=5, pady=5, sticky="w")
    lote_entry = ttk.Entry(frame_insumos, width=27)
    lote_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    # Fecha de Vencimiento
    ttk.Label(frame_insumos, text="Fecha de Vencimiento:", anchor="w").grid(
        row=1, column=2, padx=5, pady=5, sticky="w")
    fecha_venc = DateEntry(frame_insumos, width=25, background='darkblue',
                        foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
    fecha_venc.grid(row=1, column=3, padx=5, pady=5, sticky="w")

    # Frame Registro de Movimiento
    frame_registro = ttk.LabelFrame(ventana, text="Registro de Movimiento")
    frame_registro.pack(fill="x", padx=10, pady=10)
    
    for widget in frame_registro.winfo_children():
        widget.grid_configure(pady=10)

    # Primera fila
    # Fecha de Registro
    ttk.Label(frame_registro, text="Fecha de Registro:", anchor="w").grid(
        row=0, column=0, padx=5, pady=5, sticky="w")
    fecha_reg = DateEntry(frame_registro, width=25, background='darkblue',
                        foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
    fecha_reg.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    # Referencia
    ttk.Label(frame_registro, text="Referencia:", anchor="w").grid(
        row=0, column=2, padx=5, pady=5, sticky="w")
    referencia_entry = ttk.Entry(frame_registro, width=27)
    referencia_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")

    # Tipo de Movimiento
    ttk.Label(frame_registro, text="Tipo de Movimiento:", anchor="w").grid(
        row=0, column=4, padx=5, pady=5, sticky="w")
    tipo_mov_cb = ttk.Combobox(frame_registro, textvariable=tipo_movimiento_var,
                            state="readonly", width=25)
    tipo_mov_cb['values'] = [tm['descripcion'] for tm in obtener_tipos_movimiento() or []]
    tipo_mov_cb.grid(row=0, column=5, padx=5, pady=5, sticky="w")

    # Segunda fila
    # Cantidad
    ttk.Label(frame_registro, text="Cantidad:", anchor="w").grid(
        row=1, column=0, padx=5, pady=5, sticky="w")
    cantidad_entry = ttk.Entry(frame_registro, width=27)
    cantidad_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    # Observaciones (alineado con el tipo de movimiento)
    ttk.Label(frame_registro, text="Observaciones:", anchor="w").grid(
        row=1, column=2, padx=5, pady=5, sticky="w")
    observaciones_entry = ttk.Entry(frame_registro, width=60)  # Ancho fijo para alinear con tipo de movimiento
    observaciones_entry.grid(row=1, column=3, columnspan=3, padx=5, pady=5, sticky="w")  # Cambiado a sticky="w"

    # Botón Agregar Movimiento
    ttk.Button(ventana, text="Agregar Movimiento").pack(pady=10)
  
    # Frame Movimientos (Treeview)
    frame_movimientos = ttk.LabelFrame(ventana, text="Movimientos")
    frame_movimientos.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Frame contenedor para Treeview y scrollbars
    tree_frame = ttk.Frame(frame_movimientos)
    tree_frame.pack(fill="both", expand=True, padx=5, pady=5)

    # Crear Treeview
    columns = ('fecha_registro','referencia','tipo_movimiento', 'insumo', 'presentacion',
               'lote', 'fecha_vencimiento', 'cantidad','observaciones')
    tree = ttk.Treeview(tree_frame, columns=columns, show='headings')

    # Definir los encabezados
    tree.heading('fecha_registro', text='Fecha de Registro')
    tree.heading('referencia', text='Referencia')
    tree.heading('tipo_movimiento', text='Tipo de Movimiento')
    tree.heading('insumo', text='Insumo')
    tree.heading('presentacion', text='Presentación')
    tree.heading('lote', text='Lote')
    tree.heading('fecha_vencimiento', text='Fecha de Vencimiento')
    tree.heading('cantidad', text='Cantidad')
    tree.heading('observaciones', text='Observaciones')

    # Configurar el ancho de las columnas
    for col in columns:
        tree.column(col, width=150)

    # Scrollbars
    scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

    # Ubicar con grid
    tree.grid(row=0, column=0, sticky="nsew")
    scrollbar_y.grid(row=0, column=1, sticky="ns")
    scrollbar_x.grid(row=1, column=0, sticky="ew")

    # Configurar expansión del grid
    tree_frame.grid_rowconfigure(0, weight=1)
    tree_frame.grid_columnconfigure(0, weight=1)

    # Frame para botones
    frame_botones = ttk.Frame(ventana)
    frame_botones.pack(fill="x", padx=10, pady=10)

    # Botones
    ttk.Button(frame_botones, text="Editar").pack(side="left", padx=5)
    ttk.Button(frame_botones, text="Eliminar").pack(side="left", padx=5)
    ttk.Button(frame_botones, text="Guardar Movimientos").pack(side="left", padx=5)
    ttk.Button(frame_botones, text="Cerrar",
               command=lambda: [ventana.destroy(), ventana_principal.deiconify()]).pack(side="right", padx=5)

    # Funciones para actualizar comboboxes
    def actualizar_tipos_servicio(*args):
        distrito_id = next((d['id'] for d in obtener_distritos()
                          if d['nombre'] == distrito_var.get()), None)
        if distrito_id:
            tipos_servicio = obtener_tipos_servicio_por_distrito(distrito_id)
            tipo_servicio_cb['values'] = [ts['descripcion'] for ts in tipos_servicio or []]
            tipo_servicio_var.set('')
            servicio_var.set('')

    def actualizar_servicios(*args):
        tipo_servicio_id = next((ts['id'] for ts in obtener_tipos_servicio_por_distrito(
            next(d['id'] for d in obtener_distritos() if d['nombre'] == distrito_var.get()))
            if ts['descripcion'] == tipo_servicio_var.get()), None)
        if tipo_servicio_id:
            servicios = obtener_servicios_por_tipo(tipo_servicio_id)
            servicio_cb['values'] = [s['nombre'] for s in servicios or []]
            servicio_var.set('')

    def actualizar_insumos(*args):
        tipo_insumo_id = next((ti['id'] for ti in obtener_tipos_insumo()
                             if ti['descripcion'] == tipo_insumo_var.get()), None)
        if tipo_insumo_id:
            insumos = obtener_insumos_por_tipo(tipo_insumo_id)
            insumo_cb['values'] = [i['nombre'] for i in insumos or []]
            insumo_var.set('')

    # Vincular funciones a eventos de combobox
    distrito_var.trace('w', actualizar_tipos_servicio)
    tipo_servicio_var.trace('w', actualizar_servicios)
    tipo_insumo_var.trace('w', actualizar_insumos)

    # Función para agregar movimiento al Treeview
    def agregar_movimiento():
        try:
            # Obtener valores
            fecha_registro = fecha_reg.get_date().strftime('%d/%m/%Y')
            tipo_movimiento = tipo_movimiento_var.get()
            insumo = insumo_var.get()
            presentacion = presentacion_var.get()
            lote = lote_entry.get()
            fecha_venc_str = fecha_venc.get_date().strftime('%d/%m/%Y')
            cantidad = float(cantidad_entry.get())
            referencia = referencia_entry.get()
            observaciones = observaciones_entry.get()

            # Validar campos requeridos
            if not all([tipo_movimiento, insumo, presentacion, lote, cantidad, referencia]):
                messagebox.showerror("Error", "Los campos son requeridos excepto observaciones")
                return

            # Insertar en Treeview
            tree.insert('', 'end', values=(
                fecha_registro, referencia, tipo_movimiento, insumo,
                presentacion, lote, fecha_venc_str, cantidad, observaciones
            ))

            # Limpiar campos
            tipo_movimiento_var.set('')
            cantidad_entry.delete(0, 'end')
            referencia_entry.delete(0, 'end')
            observaciones_entry.delete(0, 'end')

        except ValueError:
            messagebox.showerror("Error", "La cantidad debe ser un número válido")
        except Exception as e:
            messagebox.showerror("Error", f"Error al agregar movimiento: {str(e)}")

    # Función para editar movimiento
    def editar_movimiento():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un movimiento para editar")
            return

        # Obtener valores actuales
        valores = tree.item(selected_item)['values']

        # Crear ventana de edición
        editar_ventana = tk.Toplevel(ventana)
        editar_ventana.title("Editar Movimiento")
        editar_ventana.geometry("400x300")
        centrar_ventana(editar_ventana)

        # Crear campos de edición
        ttk.Label(editar_ventana, text="Fecha de Registro:").pack(pady=5)
        fecha_edit = DateEntry(editar_ventana, width=12, background='darkblue',
                             foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        fecha_edit.pack(pady=5)

        # Establecer fecha actual
        fecha_actual = datetime.strptime(valores[0], '%d/%m/%Y').date()
        fecha_edit.set_date(fecha_actual)

        # Resto de campos...
        # [Agregar aquí el resto de los campos para edición]

        def guardar_cambios():
            # Actualizar Treeview con nuevos valores
            nuevos_valores = (
                fecha_edit.get_date().strftime('%d/%m/%Y'),
                # [Agregar aquí el resto de los valores]
            )
            tree.item(selected_item, values=nuevos_valores)
            editar_ventana.destroy()

        ttk.Button(editar_ventana, text="Guardar", command=guardar_cambios).pack(pady=10)

    # Función para eliminar movimiento
    def eliminar_movimiento():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un movimiento para eliminar")
            return

        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este movimiento?"):
            tree.delete(selected_item)

    # Asignar funciones a botones
    for widget in frame_botones.winfo_children():
        if isinstance(widget, ttk.Button):
            if widget['text'] == "Editar":
                widget.configure(command=editar_movimiento)
            elif widget['text'] == "Eliminar":
                widget.configure(command=eliminar_movimiento)

    # Configurar el botón de Agregar Movimiento
    for widget in ventana.winfo_children():
        if isinstance(widget, ttk.Button) and widget['text'] == "Agregar Movimiento":
            widget.configure(command=agregar_movimiento)


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    abrir_ingreso_insumos(root)
    root.mainloop()