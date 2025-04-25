import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import sys
import os
from tkinter.scrolledtext import ScrolledText

# Agregar el directorio raíz del proyecto al PATH de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.db_manager import (
    obtener_tipos_insumo,
    obtener_presentaciones,
    obtener_insumos_por_tipo,
    agregar_tipo_insumo,
    agregar_presentacion,
    agregar_insumo,
    actualizar_tipo_insumo,
    actualizar_presentacion,
    actualizar_insumo,
    eliminar_tipo_insumo,
    eliminar_presentacion,
    eliminar_insumo
)

# Funciones auxiliares para obtener IDs
def obtener_id_tipo_insumo(descripcion):
    """Obtiene el ID de un tipo de insumo por su descripción."""
    tipos = obtener_tipos_insumo()
    if tipos:
        for tipo in tipos:
            if tipo['descripcion'] == descripcion:
                return tipo['id']
    return None

def obtener_id_presentacion(nombre):
    """Obtiene el ID de una presentación por su nombre."""
    presentaciones = obtener_presentaciones()
    if presentaciones:
        for pres in presentaciones:
            if pres['nombre'] == nombre:
                return pres['id']
    return None

def obtener_id_insumo(nombre_insumo, id_tipo_insumo):
    """Obtiene el ID de un insumo por su nombre y tipo de insumo."""
    insumos = obtener_insumos_por_tipo(id_tipo_insumo)
    if insumos:
        for insumo in insumos:
            if insumo['nombre'] == nombre_insumo:
                return insumo['id']
    return None

# Funciones auxiliares para obtener IDs
def obtener_id_tipo_insumo(descripcion):
    """Obtiene el ID de un tipo de insumo por su descripción."""
    tipos = obtener_tipos_insumo()
    if tipos:
        for tipo in tipos:
            if tipo['descripcion'] == descripcion:
                return tipo['id']
    return None

def obtener_id_presentacion(nombre):
    """Obtiene el ID de una presentación por su nombre."""
    presentaciones = obtener_presentaciones()
    if presentaciones:
        for pres in presentaciones:
            if pres['nombre'] == nombre:
                return pres['id']
    return None

def abrir_gestion_insumos(ventana_principal):
    ventana = tk.Toplevel()
    ventana.title("Gestión de Insumos")
    ventana.geometry("1200x800")

    def centrar_ventana(ventana):
        ventana.update_idletasks()
        width = ventana.winfo_width()
        height = ventana.winfo_height()
        x = (ventana.winfo_screenwidth() // 2) - (width // 2)
        y = (ventana.winfo_screenheight() // 2) - (height // 2)
        ventana.geometry(f'{width}x{height}+{x}+{y}')

    centrar_ventana(ventana)

    # Frame para carga de Excel de Tipos e Insumos
    frame_excel_tipos = ttk.LabelFrame(ventana, text="Carga de Tipos de Insumo e Insumos")
    frame_excel_tipos.pack(fill="x", padx=10, pady=5)

    def cargar_excel_tipos():
        try:
            filename = filedialog.askopenfilename(
                title="Seleccionar archivo Excel de Tipos e Insumos",
                filetypes=[("Excel files", "*.xlsx *.xls")]
            )
            if not filename:
                return

            df = pd.read_excel(filename)
            required_columns = ['Tipo de Insumo', 'Insumo']

            if not all(col in df.columns for col in required_columns):
                messagebox.showerror("Error",
                    "El archivo debe tener las columnas: Tipo de Insumo, Insumo")
                return

            # Procesar datos
            tipos_procesados = {}

            for _, row in df.iterrows():
                tipo_nombre = row['Tipo de Insumo'].strip()
                insumo_nombre = row['Insumo'].strip()

                # Procesar tipo de insumo
                if tipo_nombre not in tipos_procesados:
                    id_tipo = agregar_tipo_insumo(tipo_nombre)
                    tipos_procesados[tipo_nombre] = id_tipo
                else:
                    id_tipo = tipos_procesados[tipo_nombre]

                # Agregar insumo sin presentación
                agregar_insumo(insumo_nombre, "", None, None, id_tipo)

            messagebox.showinfo("Éxito", "Tipos de insumo e insumos cargados correctamente")
            actualizar_arboles()

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar el archivo: {str(e)}")

    def exportar_excel_tipos():
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                title="Guardar Tipos e Insumos como"
            )
            if not filename:
                return

            # Crear lista de datos
            datos = []
            tipos_insumo = obtener_tipos_insumo()
            for tipo in tipos_insumo:
                insumos = obtener_insumos_por_tipo(tipo['id'])
                for insumo in insumos:
                    datos.append({
                        'Tipo de Insumo': tipo['descripcion'],
                        'Insumo': insumo['nombre']
                    })

            # Crear DataFrame y exportar
            df = pd.DataFrame(datos)
            df.to_excel(filename, index=False)
            messagebox.showinfo("Éxito", "Tipos e insumos exportados correctamente")

        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {str(e)}")

    # Frame para carga de Excel de Presentaciones
    frame_excel_pres = ttk.LabelFrame(ventana, text="Carga de Presentaciones")
    frame_excel_pres.pack(fill="x", padx=10, pady=5)

    def cargar_excel_presentaciones():
        try:
            filename = filedialog.askopenfilename(
                title="Seleccionar archivo Excel de Presentaciones",
                filetypes=[("Excel files", "*.xlsx *.xls")]
            )
            if not filename:
                return

            df = pd.read_excel(filename)
            if 'Presentación' not in df.columns:
                messagebox.showerror("Error",
                    "El archivo debe tener la columna: Presentación")
                return

            # Procesar presentaciones
            for _, row in df.iterrows():
                presentacion_nombre = row['Presentación'].strip()
                agregar_presentacion(presentacion_nombre)

            messagebox.showinfo("Éxito", "Presentaciones cargadas correctamente")
            actualizar_arboles()

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar el archivo: {str(e)}")

    def exportar_excel_presentaciones():
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                title="Guardar Presentaciones como"
            )
            if not filename:
                return

            # Crear lista de datos
            presentaciones = obtener_presentaciones()
            datos = [{'Presentación': pres['nombre']} for pres in presentaciones]

            # Crear DataFrame y exportar
            df = pd.DataFrame(datos)
            df.to_excel(filename, index=False)
            messagebox.showinfo("Éxito", "Presentaciones exportadas correctamente")

        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {str(e)}")

    # Botones para Excel de Tipos e Insumos
    frame_botones_tipos = ttk.Frame(frame_excel_tipos)
    frame_botones_tipos.pack(pady=10)
    ttk.Button(frame_botones_tipos, text="Cargar Tipos e Insumos",
               command=cargar_excel_tipos).pack(side="left", padx=5)
    ttk.Button(frame_botones_tipos, text="Exportar Tipos e Insumos",
               command=exportar_excel_tipos).pack(side="left", padx=5)

    # Botones para Excel de Presentaciones
    frame_botones_pres = ttk.Frame(frame_excel_pres)
    frame_botones_pres.pack(pady=10)
    ttk.Button(frame_botones_pres, text="Cargar Presentaciones",
               command=cargar_excel_presentaciones).pack(side="left", padx=5)
    ttk.Button(frame_botones_pres, text="Exportar Presentaciones",
               command=exportar_excel_presentaciones).pack(side="left", padx=5)

    # Frame para visualización y edición
    frame_edicion = ttk.LabelFrame(ventana, text="Gestión de Insumos")
    frame_edicion.pack(fill="both", expand=True, padx=10, pady=5)

    # Crear árbol de insumos
    tree = ttk.Treeview(frame_edicion, columns=('tipo', 'nombre'), show='tree headings')
    tree.heading('tipo', text='Tipo')
    tree.heading('nombre', text='Nombre')
    tree.pack(fill="both", expand=True, padx=5, pady=5)

    def actualizar_arboles():
        for item in tree.get_children():
            tree.delete(item)

        # Agregar tipos de insumo
        tipos = obtener_tipos_insumo()
        for tipo in tipos:
            tipo_item = tree.insert('', 'end', text=tipo['descripcion'],
                                  values=('Tipo de Insumo', tipo['descripcion']))

            # Agregar insumos
            insumos = obtener_insumos_por_tipo(tipo['id'])
            for insumo in insumos:
                tree.insert(tipo_item, 'end', text=insumo['nombre'],
                          values=('Insumo', insumo['nombre']))

        # Agregar presentaciones
        pres_root = tree.insert('', 'end', text='Presentaciones',
                              values=('Raíz', 'Presentaciones'))
        presentaciones = obtener_presentaciones()
        for pres in presentaciones:
            tree.insert(pres_root, 'end', text=pres['nombre'],
                       values=('Presentación', pres['nombre']))

    def agregar_nuevo():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un elemento")
            return

        item = tree.item(selected[0])
        item_type = item['values'][0]

        ventana_nuevo = tk.Toplevel(ventana)
        ventana_nuevo.title("Agregar Nuevo")
        ventana_nuevo.geometry("400x200")
        centrar_ventana(ventana_nuevo)

        if item_type == 'Tipo de Insumo' or item_type == 'Raíz':
            # Agregar nuevo tipo de insumo
            ttk.Label(ventana_nuevo, text="Descripción del Tipo:").pack(pady=5)
            descripcion = ttk.Entry(ventana_nuevo)
            descripcion.pack(pady=5)

            def guardar():
                if agregar_tipo_insumo(descripcion.get()):
                    messagebox.showinfo("Éxito", "Tipo de insumo agregado correctamente")
                    actualizar_arboles()
                    ventana_nuevo.destroy()

            ttk.Button(ventana_nuevo, text="Guardar", command=guardar).pack(pady=10)

        elif item_type == 'Insumo':
            # Agregar nuevo insumo
            id_tipo = obtener_id_tipo_insumo(tree.item(tree.parent(selected[0]))['text'])

            ttk.Label(ventana_nuevo, text="Nombre del Insumo:").pack(pady=5)
            nombre = ttk.Entry(ventana_nuevo)
            nombre.pack(pady=5)

            def guardar():
                if agregar_insumo(nombre.get(), "", None, None, id_tipo):
                    messagebox.showinfo("Éxito", "Insumo agregado correctamente")
                    actualizar_arboles()
                    ventana_nuevo.destroy()

            ttk.Button(ventana_nuevo, text="Guardar", command=guardar).pack(pady=10)

        elif item_type == 'Presentación' or item['text'] == 'Presentaciones':
            # Agregar nueva presentación
            ttk.Label(ventana_nuevo, text="Nombre de la Presentación:").pack(pady=5)
            nombre = ttk.Entry(ventana_nuevo)
            nombre.pack(pady=5)

            def guardar():
                if agregar_presentacion(nombre.get()):
                    messagebox.showinfo("Éxito", "Presentación agregada correctamente")
                    actualizar_arboles()
                    ventana_nuevo.destroy()

            ttk.Button(ventana_nuevo, text="Guardar", command=guardar).pack(pady=10)

    def editar_seleccionado():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un elemento para editar")
            return

        item = tree.item(selected[0])
        item_type = item['values'][0]

        if item_type in ['Raíz', '']:
            return

        ventana_editar = tk.Toplevel(ventana)
        ventana_editar.title(f"Editar {item_type}")
        ventana_editar.geometry("400x200")
        centrar_ventana(ventana_editar)

        ttk.Label(ventana_editar, text="Nuevo nombre:").pack(pady=5)
        nuevo_nombre = ttk.Entry(ventana_editar)
        nuevo_nombre.insert(0, item['text'])
        nuevo_nombre.pack(pady=5)

        def guardar_cambios():
            try:
                if item_type == 'Tipo de Insumo':
                    actualizar_tipo_insumo(obtener_id_tipo_insumo(item['text']),
                                         nuevo_nombre.get())
                elif item_type == 'Presentación':
                    actualizar_presentacion(obtener_id_presentacion(item['text']),
                                          nuevo_nombre.get())
                elif item_type == 'Insumo':
                    id_tipo = obtener_id_tipo_insumo(
                        tree.item(tree.parent(selected[0]))['text'])
                    actualizar_insumo(obtener_id_insumo(item['text'], id_tipo),
                                    nuevo_nombre.get())

                messagebox.showinfo("Éxito", "Elemento actualizado correctamente")
                actualizar_arboles()
                ventana_editar.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(ventana_editar, text="Guardar",
                  command=guardar_cambios).pack(pady=10)

    def eliminar_seleccionado():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un elemento para eliminar")
            return

        item = tree.item(selected[0])
        item_type = item['values'][0]

        if item_type in ['Raíz', '']:
            return

        if not messagebox.askyesno("Confirmar",
            f"¿Está seguro de eliminar este {item_type}?\n" +
            "Se eliminarán también todos los elementos relacionados."):
            return

        try:
            if item_type == 'Tipo de Insumo':
                eliminar_tipo_insumo(obtener_id_tipo_insumo(item['text']))
            elif item_type == 'Presentación':
                eliminar_presentacion(obtener_id_presentacion(item['text']))
            elif item_type == 'Insumo':
                id_tipo = obtener_id_tipo_insumo(
                    tree.item(tree.parent(selected[0]))['text'])
                eliminar_insumo(obtener_id_insumo(item['text'], id_tipo))

            messagebox.showinfo("Éxito", "Elemento eliminado correctamente")
            actualizar_arboles()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # Frame de botones
    frame_botones = ttk.Frame(frame_edicion)
    frame_botones.pack(fill="x", pady=5)

    ttk.Button(frame_botones, text="Agregar",
               command=agregar_nuevo).pack(side="left", padx=5)
    ttk.Button(frame_botones, text="Editar",
               command=editar_seleccionado).pack(side="left", padx=5)
    ttk.Button(frame_botones, text="Eliminar",
               command=eliminar_seleccionado).pack(side="left", padx=5)

    # Botón Cerrar
    ttk.Button(ventana, text="Cerrar",
               command=lambda: [ventana.destroy(),
                              ventana_principal.deiconify()]).pack(pady=10)

    # Inicializar árbol
    actualizar_arboles()

    ventana.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    abrir_gestion_insumos(root)