import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import sys
import os
from tkinter.scrolledtext import ScrolledText

# Agregar el directorio raíz del proyecto al PATH de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.db_manager import (
    obtener_distritos,
    obtener_tipos_servicio_por_distrito,
    obtener_servicios_por_tipo,
    agregar_distrito,
    agregar_tipo_servicio,
    agregar_servicio,
    actualizar_distrito,
    actualizar_tipo_servicio,
    actualizar_servicio,
    eliminar_distrito,
    eliminar_tipo_servicio,
    eliminar_servicio
)

# Funciones auxiliares para obtener IDs
def obtener_id_distrito(nombre_distrito):
    """Obtiene el ID de un distrito por su nombre."""
    distritos = obtener_distritos()
    if distritos:
        for distrito in distritos:
            if distrito['nombre'] == nombre_distrito:
                return distrito['id']
    return None

def obtener_id_tipo_servicio(nombre_tipo, nombre_distrito):
    """Obtiene el ID de un tipo de servicio por su nombre y distrito."""
    id_distrito = obtener_id_distrito(nombre_distrito)
    if id_distrito:
        tipos_servicio = obtener_tipos_servicio_por_distrito(id_distrito)
        if tipos_servicio:
            for tipo in tipos_servicio:
                if tipo['descripcion'] == nombre_tipo:
                    return tipo['id']
    return None

def obtener_id_servicio(nombre_servicio, nombre_tipo_servicio):
    """Obtiene el ID de un servicio por su nombre y tipo de servicio."""
    id_tipo = obtener_id_tipo_servicio(nombre_tipo_servicio)
    if id_tipo:
        servicios = obtener_servicios_por_tipo(id_tipo)
        if servicios:
            for servicio in servicios:
                if servicio['nombre'] == nombre_servicio:
                    return servicio['id']
    return None

def abrir_gestion_servicios(ventana_principal):
    ventana = tk.Toplevel()
    ventana.title("Gestión de Servicios")
    ventana.geometry("1200x800")

    def centrar_ventana(ventana):
        ventana.update_idletasks()
        width = ventana.winfo_width()
        height = ventana.winfo_height()
        x = (ventana.winfo_screenwidth() // 2) - (width // 2)
        y = (ventana.winfo_screenheight() // 2) - (height // 2)
        ventana.geometry(f'{width}x{height}+{x}+{y}')

    centrar_ventana(ventana)

    # Frame para carga de Excel
    frame_excel = ttk.LabelFrame(ventana, text="Carga desde Excel")
    frame_excel.pack(fill="x", padx=10, pady=5)

    def cargar_excel():
        try:
            filename = filedialog.askopenfilename(
                title="Seleccionar archivo Excel",
                filetypes=[("Excel files", "*.xlsx *.xls")]
            )
            if not filename:
                return

            df = pd.read_excel(filename)
            required_columns = ['Distrito', 'Tipo de Servicio', 'Servicio']

            if not all(col in df.columns for col in required_columns):
                messagebox.showerror("Error",
                    "El archivo debe tener las columnas: Distrito, Tipo de Servicio, Servicio")
                return

            # Procesar datos
            distritos_procesados = {}
            tipos_servicio_procesados = {}

            for _, row in df.iterrows():
                distrito_nombre = row['Distrito'].strip()
                tipo_servicio_nombre = row['Tipo de Servicio'].strip()
                servicio_nombre = row['Servicio'].strip()

                # Procesar distrito
                if distrito_nombre not in distritos_procesados:
                    id_distrito = agregar_distrito(distrito_nombre)
                    distritos_procesados[distrito_nombre] = id_distrito
                else:
                    id_distrito = distritos_procesados[distrito_nombre]

                # Procesar tipo de servicio
                tipo_key = f"{distrito_nombre}_{tipo_servicio_nombre}"
                if tipo_key not in tipos_servicio_procesados:
                    id_tipo = agregar_tipo_servicio(id_distrito, tipo_servicio_nombre)
                    tipos_servicio_procesados[tipo_key] = id_tipo
                else:
                    id_tipo = tipos_servicio_procesados[tipo_key]

                # Agregar servicio
                agregar_servicio(id_tipo, servicio_nombre)

            messagebox.showinfo("Éxito", "Datos cargados correctamente")
            actualizar_arboles()

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar el archivo: {str(e)}")

    def exportar_excel():
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                title="Guardar como"
            )
            if not filename:
                return

            # Crear lista de datos
            datos = []
            distritos = obtener_distritos()
            for distrito in distritos:
                tipos_servicio = obtener_tipos_servicio_por_distrito(distrito['id'])
                for tipo in tipos_servicio:
                    servicios = obtener_servicios_por_tipo(tipo['id'])
                    for servicio in servicios:
                        datos.append({
                            'Distrito': distrito['nombre'],
                            'Tipo de Servicio': tipo['descripcion'],
                            'Servicio': servicio['nombre']
                        })

            # Crear DataFrame y exportar
            df = pd.DataFrame(datos)
            df.to_excel(filename, index=False)
            messagebox.showinfo("Éxito", "Datos exportados correctamente")

        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {str(e)}")

    frame_botones_excel = ttk.Frame(frame_excel)
    frame_botones_excel.pack(pady=10)
    ttk.Button(frame_botones_excel, text="Cargar Excel",
               command=cargar_excel).pack(side="left", padx=5)
    ttk.Button(frame_botones_excel, text="Exportar a Excel",
               command=exportar_excel).pack(side="left", padx=5)

    # Frame para visualización y edición
    frame_edicion = ttk.LabelFrame(ventana, text="Gestión de Servicios")
    frame_edicion.pack(fill="both", expand=True, padx=10, pady=5)

    # Crear árbol de servicios
    tree = ttk.Treeview(frame_edicion, columns=('tipo', 'nombre'), show='tree headings')
    tree.heading('tipo', text='Tipo')
    tree.heading('nombre', text='Nombre')
    tree.pack(fill="both", expand=True, padx=5, pady=5)

    def actualizar_arboles():
        for item in tree.get_children():
            tree.delete(item)

        distritos = obtener_distritos()
        for distrito in distritos:
            distrito_item = tree.insert('', 'end', text=distrito['nombre'],
                                      values=('Distrito', distrito['nombre']))

            tipos_servicio = obtener_tipos_servicio_por_distrito(distrito['id'])
            for tipo in tipos_servicio:
                tipo_item = tree.insert(distrito_item, 'end',
                                      text=tipo['descripcion'],
                                      values=('Tipo de Servicio', tipo['descripcion']))

                servicios = obtener_servicios_por_tipo(tipo['id'])
                for servicio in servicios:
                    tree.insert(tipo_item, 'end', text=servicio['nombre'],
                              values=('Servicio', servicio['nombre']))

    def agregar_nuevo():
        ventana_nuevo = tk.Toplevel(ventana)
        ventana_nuevo.title("Agregar Nuevo")
        ventana_nuevo.geometry("400x300")
        centrar_ventana(ventana_nuevo)

        selected = tree.selection()
        item_type = tree.item(selected[0])['values'][0] if selected else None

        if not selected or item_type == 'Distrito':
            # Agregar nuevo distrito
            ttk.Label(ventana_nuevo, text="Nombre del Distrito:").pack(pady=5)
            nombre_distrito = ttk.Entry(ventana_nuevo)
            nombre_distrito.pack(pady=5)

            def guardar_distrito():
                try:
                    if agregar_distrito(nombre_distrito.get()):
                        messagebox.showinfo("Éxito", "Distrito agregado correctamente")
                        actualizar_arboles()
                        ventana_nuevo.destroy()
                except Exception as e:
                    messagebox.showerror("Error", str(e))

            ttk.Button(ventana_nuevo, text="Guardar",
                      command=guardar_distrito).pack(pady=10)

        elif item_type == 'Tipo de Servicio':
            # Agregar nuevo tipo de servicio
            distrito_id = obtener_id_distrito(tree.item(tree.parent(selected[0]))['text'])

            ttk.Label(ventana_nuevo, text="Nombre del Tipo de Servicio:").pack(pady=5)
            nombre_tipo = ttk.Entry(ventana_nuevo)
            nombre_tipo.pack(pady=5)

            def guardar_tipo():
                try:
                    if agregar_tipo_servicio(distrito_id, nombre_tipo.get()):
                        messagebox.showinfo("Éxito", "Tipo de servicio agregado correctamente")
                        actualizar_arboles()
                        ventana_nuevo.destroy()
                except Exception as e:
                    messagebox.showerror("Error", str(e))

            ttk.Button(ventana_nuevo, text="Guardar",
                      command=guardar_tipo).pack(pady=10)

        elif item_type == 'Servicio':
            # Agregar nuevo servicio
            tipo_id = obtener_id_tipo_servicio(
                tree.item(tree.parent(selected[0]))['text'],
                tree.item(tree.parent(tree.parent(selected[0])))['text']
            )

            ttk.Label(ventana_nuevo, text="Nombre del Servicio:").pack(pady=5)
            nombre_servicio = ttk.Entry(ventana_nuevo)
            nombre_servicio.pack(pady=5)

            def guardar_servicio():
                try:
                    if agregar_servicio(tipo_id, nombre_servicio.get()):
                        messagebox.showinfo("Éxito", "Servicio agregado correctamente")
                        actualizar_arboles()
                        ventana_nuevo.destroy()
                except Exception as e:
                    messagebox.showerror("Error", str(e))

            ttk.Button(ventana_nuevo, text="Guardar",
                      command=guardar_servicio).pack(pady=10)

    def editar_seleccionado():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un elemento para editar")
            return

        item = tree.item(selected[0])
        item_type = item['values'][0]

        ventana_editar = tk.Toplevel(ventana)
        ventana_editar.title(f"Editar {item_type}")
        ventana_editar.geometry("400x200")
        centrar_ventana(ventana_editar)

        ttk.Label(ventana_editar, text=f"Nuevo nombre:").pack(pady=5)
        nuevo_nombre = ttk.Entry(ventana_editar)
        nuevo_nombre.insert(0, item['text'])
        nuevo_nombre.pack(pady=5)

        def guardar_cambios():
            try:
                if item_type == 'Distrito':
                    actualizar_distrito(obtener_id_distrito(item['text']),
                                     nuevo_nombre.get())
                elif item_type == 'Tipo de Servicio':
                    actualizar_tipo_servicio(
                        obtener_id_tipo_servicio(item['text'],
                        tree.item(tree.parent(selected[0]))['text']),
                        nuevo_nombre.get()
                    )
                elif item_type == 'Servicio':
                    actualizar_servicio(
                        obtener_id_servicio(item['text'],
                        tree.item(tree.parent(selected[0]))['text']),
                        nuevo_nombre.get()
                    )

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

        if not messagebox.askyesno("Confirmar",
            f"¿Está seguro de eliminar este {item_type}?\n" +
            "Se eliminarán también todos los elementos relacionados."):
            return

        try:
            if item_type == 'Distrito':
                eliminar_distrito(obtener_id_distrito(item['text']))
            elif item_type == 'Tipo de Servicio':
                eliminar_tipo_servicio(
                    obtener_id_tipo_servicio(item['text'],
                    tree.item(tree.parent(selected[0]))['text'])
                )
            elif item_type == 'Servicio':
                eliminar_servicio(
                    obtener_id_servicio(item['text'],
                    tree.item(tree.parent(selected[0]))['text'])
                )

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
    abrir_gestion_servicios(root)