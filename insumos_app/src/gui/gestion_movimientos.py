import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import sys
import os
from tkinter.scrolledtext import ScrolledText

# Agregar el directorio raíz del proyecto al PATH de Python
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from src.database.db_manager import (
    obtener_tipos_movimiento,
    agregar_tipo_movimiento,
    actualizar_tipo_movimiento,
    eliminar_tipo_movimiento,
)

class GestionMovimientos:
    def __init__(self, parent_frame, main_window):
        self.parent = parent_frame
        self.main_window = main_window
        self.setup_ui()

    def centrar_ventana(self, ventana):
        """Centra una ventana en la pantalla."""
        ventana.update_idletasks()
        width = ventana.winfo_width()
        height = ventana.winfo_height()
        x = (ventana.winfo_screenwidth() // 2) - (width // 2)
        y = (ventana.winfo_screenheight() // 2) - (height // 2)
        ventana.geometry(f'{width}x{height}+{x}+{y}')

    def setup_ui(self):
        # Notebook para pestañas
        self.notebook = ttk.Notebook(self.parent)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # Pestaña de tipos de movimiento
        self.tab_tipos = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_tipos, text="Tipos de Movimiento")

        self.setup_tipos_tab()

        # Botón Cerrar
        ttk.Button(self.parent, text="Cerrar",
                  command=self.cerrar_ventana).pack(pady=10)

        self.actualizar_tipos()

    def setup_tipos_tab(self):
        frame_excel = ttk.LabelFrame(self.tab_tipos, text="Carga desde Excel")
        frame_excel.pack(fill="x", padx=5, pady=5)
        ttk.Button(frame_excel, text="Cargar Excel",
                  command=self.cargar_excel_tipos).pack(side="left", padx=5, pady=5)
        ttk.Button(frame_excel, text="Exportar a Excel",
                  command=self.exportar_excel_tipos).pack(side="left", padx=5, pady=5)

        frame_lista = ttk.LabelFrame(self.tab_tipos, text="Tipos de Movimiento")
        frame_lista.pack(fill="both", expand=True, padx=5, pady=5)

        self.tree_tipos = ttk.Treeview(frame_lista,
                                     columns=('descripcion',),
                                     show='headings')
        self.tree_tipos.heading('descripcion', text='Tipos Movimiento')
        self.tree_tipos.grid(row=0, column=0, sticky="nsew")

        scrolly = ttk.Scrollbar(frame_lista, orient="vertical",
                              command=self.tree_tipos.yview)
        self.tree_tipos.configure(yscrollcommand=scrolly.set)
        scrolly.grid(row=0, column=1, sticky="ns")

        frame_lista.grid_rowconfigure(0, weight=1)
        frame_lista.grid_columnconfigure(0, weight=1)

        frame_botones = ttk.Frame(frame_lista)
        frame_botones.grid(row=1, column=0, columnspan=2, pady=5)
        ttk.Button(frame_botones, text="Agregar",
                  command=self.agregar_tipo).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Editar",
                  command=self.editar_tipo).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Eliminar",
                  command=self.eliminar_tipo).pack(side="left", padx=5)

    def cargar_excel_tipos(self):
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo Excel",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if not filename:
            return

        try:
            df = pd.read_excel(filename)
            required_columns = ['Tipo de Movimiento']

            if not all(col in df.columns for col in required_columns):
                messagebox.showerror("Error",
                    "El archivo debe tener la columna: Tipo de Movimiento")
                return

            registros_procesados = 0
            registros_existentes = 0

            for _, row in df.iterrows():
                try:
                    descripcion = str(row['Tipo de Movimiento']).strip()
                    if not descripcion:
                        continue

                    tipos_existentes = obtener_tipos_movimiento()
                    existe = any(tipo['descripcion'].lower() == descripcion.lower() 
                               for tipo in tipos_existentes)
                    if existe:
                        registros_existentes += 1
                        continue

                    agregar_tipo_movimiento(descripcion)
                    registros_procesados += 1

                except Exception as e:
                    print(f"Error al procesar fila: {str(e)}")
                    continue

            self.actualizar_tipos()

            mensaje = f"Proceso completado:\n"
            mensaje += f"- Registros nuevos agregados: {registros_procesados}\n"
            mensaje += f"- Registros existentes omitidos: {registros_existentes}"
            messagebox.showinfo("Éxito", mensaje)

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar el archivo: {str(e)}")

    def exportar_excel_tipos(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )
        if not filename:
            return

        tipos = obtener_tipos_movimiento()
        df = pd.DataFrame([{
            'Tipo de Movimiento': t['descripcion']
        } for t in tipos])

        df.to_excel(filename, index=False)
        messagebox.showinfo("Éxito", "Tipos de movimiento exportados correctamente")

    def agregar_tipo(self):
        ventana = tk.Toplevel(self.parent)
        ventana.title("Agregar Tipo de Movimiento")
        ventana.geometry("350x120")
        self.centrar_ventana(ventana)

        frame_campos = ttk.Frame(ventana)
        frame_campos.pack(padx=10, pady=5, fill='x')

        ttk.Label(frame_campos, text="Tipo de Movimiento:").pack(pady=5)
        descripcion = ttk.Entry(frame_campos, width=40)
        descripcion.pack(pady=5, fill='x')

        def guardar():
            if not descripcion.get().strip():
                messagebox.showwarning("Advertencia", "Ingrese la descripción")
                return
            try:
                agregar_tipo_movimiento(descripcion.get().strip())
                self.actualizar_tipos()
                ventana.destroy()
                messagebox.showinfo("Éxito", "Tipo de movimiento agregado correctamente")
            except Exception as e:
                messagebox.showerror("Error", f"Error al agregar tipo de movimiento: {str(e)}")

        frame_botones = ttk.Frame(ventana)
        frame_botones.pack(pady=10)
        ttk.Button(frame_botones, text="Guardar", command=guardar).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Cerrar", command=ventana.destroy).pack(side="left", padx=5)

    def editar_tipo(self):
        selected = self.tree_tipos.selection()
        if not selected:
            messagebox.showwarning("Advertencia",
                "Seleccione un tipo de movimiento para editar")
            return

        item = self.tree_tipos.item(selected[0])
        ventana = tk.Toplevel(self.parent)
        ventana.title("Editar Tipo de Movimiento")
        ventana.geometry("350x120")
        self.centrar_ventana(ventana)

        frame_campos = ttk.Frame(ventana)
        frame_campos.pack(padx=10, pady=5, fill='x')

        ttk.Label(frame_campos, text="Descripción:").pack(pady=5)
        descripcion = ttk.Entry(frame_campos, width=40)
        descripcion.insert(0, item['values'][0])
        descripcion.pack(pady=5, fill='x')

        def guardar():
            try:
                tipos = obtener_tipos_movimiento()
                id_tipo = None
                for tipo in tipos:
                    if tipo['descripcion'] == item['values'][0]:
                        id_tipo = tipo['id']
                        break

                if id_tipo:
                    actualizar_tipo_movimiento(id_tipo, descripcion.get().strip())
                    self.actualizar_tipos()
                    ventana.destroy()
                    messagebox.showinfo("Éxito",
                        "Tipo de movimiento actualizado correctamente")
            except Exception as e:
                messagebox.showerror("Error",
                    f"Error al actualizar tipo de movimiento: {str(e)}")

        frame_botones = ttk.Frame(ventana)
        frame_botones.pack(pady=10)
        ttk.Button(frame_botones, text="Guardar",
                  command=guardar).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Cerrar",
                  command=ventana.destroy).pack(side="left", padx=5)

    def eliminar_tipo(self):
        selected = self.tree_tipos.selection()
        if not selected:
            messagebox.showwarning("Advertencia",
                "Seleccione un tipo de movimiento para eliminar")
            return

        item = self.tree_tipos.item(selected[0])
        if messagebox.askyesno("Confirmar",
            "¿Está seguro de eliminar este tipo de movimiento?"):
            try:
                tipos = obtener_tipos_movimiento()
                id_tipo = None
                for tipo in tipos:
                    if tipo['descripcion'] == item['values'][0]:
                        id_tipo = tipo['id']
                        break

                if id_tipo:
                    eliminar_tipo_movimiento(id_tipo)
                    self.actualizar_tipos()
                    messagebox.showinfo("Éxito",
                        "Tipo de movimiento eliminado correctamente")
            except Exception as e:
                messagebox.showerror("Error",
                    f"Error al eliminar tipo de movimiento: {str(e)}")

    def actualizar_tipos(self):
        """Actualiza la lista de tipos de movimiento en el TreeView"""
        try:
            self.tree_tipos.delete(*self.tree_tipos.get_children())
            tipos = obtener_tipos_movimiento()
            if tipos is None:
                return

            for tipo in tipos:
                self.tree_tipos.insert('', 'end', values=(tipo['descripcion'],))
        except Exception as e:
            messagebox.showerror("Error",
                f"Error al actualizar tipos de movimiento: {str(e)}")

    def cerrar_ventana(self):
        """Cierra la ventana de gestión y muestra la pantalla de bienvenida"""
        try:
            if messagebox.askyesno("Confirmar",
                "¿Está seguro que desea cerrar esta ventana?"):
                # Limpiar widgets
                for widget in self.parent.winfo_children():
                    widget.destroy()

                # Mostrar pantalla de bienvenida
                if hasattr(self.main_window, 'show_welcome_screen'):
                    self.main_window.show_welcome_screen()
                else:
                    print("Advertencia: método show_welcome_screen no encontrado")
                    self.parent.destroy()
        except Exception as e:
            print(f"Error al cerrar ventana: {e}")
            try:
                self.parent.destroy()
            except:
                pass