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
    ventana.geometry("1200x800")

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

    # Frame Servicios
    frame_servicios = ttk.LabelFrame(ventana, text="Servicios")
    frame_servicios.pack(fill="x", padx=10, pady=5)

    # Distrito
    ttk.Label(frame_servicios, text="Distrito:").grid(row=0, column=0, padx=5, pady=5)
    distrito_cb = ttk.Combobox(frame_servicios, textvariable=distrito_var, state="readonly")
    distrito_cb['values'] = [d['nombre'] for d in obtener_distritos() or []]
    distrito_cb.grid(row=0, column=1, padx=5, pady=5)

    # Tipo de Servicio
    ttk.Label(frame_servicios, text="Tipo de Servicio:").grid(row=0, column=2, padx=5, pady=5)
    tipo_servicio_cb = ttk.Combobox(frame_servicios, textvariable=tipo_servicio_var, state="readonly")
    tipo_servicio_cb.grid(row=0, column=3, padx=5, pady=5)

    # Servicio
    ttk.Label(frame_servicios, text="Servicio:").grid(row=0, column=4, padx=5, pady=5)
    servicio_cb = ttk.Combobox(frame_servicios, textvariable=servicio_var, state="readonly")
    servicio_cb.grid(row=0, column=5, padx=5, pady=5)

    # Frame Insumos
    frame_insumos = ttk.LabelFrame(ventana, text="Insumos")
    frame_insumos.pack(fill="x", padx=10, pady=5)

    # Tipo de Insumo
    ttk.Label(frame_insumos, text="Tipo de Insumo:").grid(row=0, column=0, padx=5, pady=5)
    tipo_insumo_cb = ttk.Combobox(frame_insumos, textvariable=tipo_insumo_var, state="readonly")
    tipo_insumo_cb['values'] = [ti['descripcion'] for ti in obtener_tipos_insumo() or []]
    tipo_insumo_cb.grid(row=0, column=1, padx=5, pady=5)

    # Insumo
    ttk.Label(frame_insumos, text="Insumo:").grid(row=0, column=2, padx=5, pady=5)
    insumo_cb = ttk.Combobox(frame_insumos, textvariable=insumo_var, state="readonly")
    insumo_cb.grid(row=0, column=3, padx=5, pady=5)

    # Presentación
    ttk.Label(frame_insumos, text="Presentación:").grid(row=0, column=4, padx=5, pady=5)
    presentacion_cb = ttk.Combobox(frame_insumos, textvariable=presentacion_var, state="readonly")
    presentacion_cb['values'] = [p['nombre'] for p in obtener_presentaciones() or []]
    presentacion_cb.grid(row=0, column=5, padx=5, pady=5)

    # Lote
    ttk.Label(frame_insumos, text="Lote:").grid(row=1, column=0, padx=5, pady=5)
    lote_entry = ttk.Entry(frame_insumos)
    lote_entry.grid(row=1, column=1, padx=5, pady=5)

    # Fecha de Vencimiento
    ttk.Label(frame_insumos, text="Fecha de Vencimiento:").grid(row=1, column=2, padx=5, pady=5)
    fecha_venc = DateEntry(frame_insumos, width=12, background='darkblue',
                          foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
    fecha_venc.grid(row=1, column=3, padx=5, pady=5)

    # Botón Agregar Movimiento
    ttk.Button(ventana, text="Agregar Movimiento").pack(pady=5)

    # Frame Registro de Movimiento
    frame_registro = ttk.LabelFrame(ventana, text="Registro de Movimiento")
    frame_registro.pack(fill="x", padx=10, pady=5)

    # Fecha de Registro
    ttk.Label(frame_registro, text="Fecha de Registro:").grid(row=0, column=0, padx=5, pady=5)
    fecha_reg = DateEntry(frame_registro, width=12, background='darkblue',
                         foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
    fecha_reg.grid(row=0, column=1, padx=5, pady=5)

    # Tipo de Movimiento
    ttk.Label(frame_registro, text="Tipo de Movimiento:").grid(row=0, column=2, padx=5, pady=5)
    tipo_mov_cb = ttk.Combobox(frame_registro, textvariable=tipo_movimiento_var, state="readonly")
    tipo_mov_cb['values'] = [tm['descripcion'] for tm in obtener_tipos_movimiento() or []]
    tipo_mov_cb.grid(row=0, column=3, padx=5, pady=5)

    # Cantidad
    ttk.Label(frame_registro, text="Cantidad:").grid(row=0, column=4, padx=5, pady=5)
    cantidad_entry = ttk.Entry(frame_registro)
    cantidad_entry.grid(row=0, column=5, padx=5, pady=5)

    # Frame Movimientos (Treeview)
    frame_movimientos = ttk.LabelFrame(ventana, text="Movimientos")
    frame_movimientos.pack(fill="both", expand=True, padx=10, pady=5)

    # Crear Treeview
    columns = ('fecha_registro', 'tipo_movimiento', 'insumo', 'presentacion',
               'lote', 'fecha_vencimiento', 'cantidad')
    tree = ttk.Treeview(frame_movimientos, columns=columns, show='headings')

    # Definir los encabezados
    tree.heading('fecha_registro', text='Fecha de Registro')
    tree.heading('tipo_movimiento', text='Tipo de Movimiento')
    tree.heading('insumo', text='Insumo')
    tree.heading('presentacion', text='Presentación')
    tree.heading('lote', text='Lote')
    tree.heading('fecha_vencimiento', text='Fecha de Vencimiento')
    tree.heading('cantidad', text='Cantidad')

    # Configurar el ancho de las columnas
    for col in columns:
        tree.column(col, width=150)

    # Agregar scrollbar
    scrollbar = ttk.Scrollbar(frame_movimientos, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    # Empaquetar Treeview y scrollbar
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Frame para botones
    frame_botones = ttk.Frame(ventana)
    frame_botones.pack(fill="x", padx=10, pady=5)

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

            # Validar campos requeridos
            if not all([tipo_movimiento, insumo, presentacion, lote, cantidad]):
                messagebox.showerror("Error", "Todos los campos son requeridos")
                return

            # Insertar en Treeview
            tree.insert('', 'end', values=(
                fecha_registro, tipo_movimiento, insumo, presentacion,
                lote, fecha_venc_str, cantidad
            ))

            # Limpiar campos
            tipo_movimiento_var.set('')
            cantidad_entry.delete(0, 'end')

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

    ventana.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    abrir_ingreso_insumos(root)