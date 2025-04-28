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

class GestionServicios:
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

    def obtener_id_distrito(self, nombre_distrito):
        """Obtiene el ID de un distrito por su nombre."""
        distritos = obtener_distritos()
        if distritos:
            for distrito in distritos:
                if distrito['nombre'] == nombre_distrito:
                    return distrito['id']
        return None

    def obtener_id_tipo_servicio(self, nombre_tipo, nombre_distrito):
        """Obtiene el ID de un tipo de servicio por su nombre y distrito."""
        id_distrito = self.obtener_id_distrito(nombre_distrito)
        if id_distrito:
            tipos_servicio = obtener_tipos_servicio_por_distrito(id_distrito)
            if tipos_servicio:
                for tipo in tipos_servicio:
                    if tipo['descripcion'] == nombre_tipo:
                        return tipo['id']
        return None

    def obtener_id_servicio(self, nombre_servicio, nombre_tipo_servicio):
        """Obtiene el ID de un servicio por su nombre y tipo de servicio."""
        id_tipo = self.obtener_id_tipo_servicio(nombre_tipo_servicio)
        if id_tipo:
            servicios = obtener_servicios_por_tipo(id_tipo)
            if servicios:
                for servicio in servicios:
                    if servicio['nombre'] == nombre_servicio:
                        return servicio['id']
        return None

    def setup_ui(self):
        self.notebook = ttk.Notebook(self.parent)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        self.tab_distritos = ttk.Frame(self.notebook)
        self.tab_tipos = ttk.Frame(self.notebook)
        self.tab_servicios = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_distritos, text="Distritos")
        self.notebook.add(self.tab_tipos, text="Tipos de Servicio")
        self.notebook.add(self.tab_servicios, text="Servicios")

        self.setup_distritos_tab()
        self.setup_tipos_tab()
        self.setup_servicios_tab()

        ttk.Button(self.parent, text="Cerrar", command=self.cerrar_ventana).pack(pady=10)

        self.actualizar_distritos()
        self.actualizar_tipos()
        self.actualizar_servicios()

    # --------- DISTRITOS ---------
    def setup_distritos_tab(self):
        frame_excel = ttk.LabelFrame(self.tab_distritos, text="Carga desde Excel")
        frame_excel.pack(fill="x", padx=5, pady=5)
        ttk.Button(frame_excel, text="Cargar Excel", command=self.cargar_excel_distritos).pack(side="left", padx=5, pady=5)
        ttk.Button(frame_excel, text="Exportar a Excel", command=self.exportar_excel_distritos).pack(side="left", padx=5, pady=5)

        frame_lista = ttk.LabelFrame(self.tab_distritos, text="Distritos")
        frame_lista.pack(fill="both", expand=True, padx=5, pady=5)

        self.tree_distritos = ttk.Treeview(frame_lista, columns=('nombre',), show='headings')
        self.tree_distritos.heading('nombre', text='Nombre')
        self.tree_distritos.grid(row=0, column=0, sticky="nsew")
        scrolly = ttk.Scrollbar(frame_lista, orient="vertical", command=self.tree_distritos.yview)
        self.tree_distritos.configure(yscrollcommand=scrolly.set)
        scrolly.grid(row=0, column=1, sticky="ns")
        frame_lista.grid_rowconfigure(0, weight=1)
        frame_lista.grid_columnconfigure(0, weight=1)

        frame_botones = ttk.Frame(frame_lista)
        frame_botones.grid(row=1, column=0, columnspan=2, pady=5)
        ttk.Button(frame_botones, text="Agregar", command=self.agregar_distrito).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Editar", command=self.editar_distrito).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Eliminar", command=self.eliminar_distrito).pack(side="left", padx=5)

    def cargar_excel_distritos(self):
        filename = filedialog.askopenfilename(title="Seleccionar archivo Excel de Distritos", filetypes=[("Excel files", "*.xlsx *.xls")])
        if not filename:
            return
        df = pd.read_excel(filename)
        if 'Distrito' not in df.columns:
            messagebox.showerror("Error", "El archivo debe tener la columna: Distrito")
            return
        for distrito in df['Distrito'].dropna().unique():
            agregar_distrito(str(distrito).strip())
        messagebox.showinfo("Éxito", "Distritos cargados correctamente")
        self.actualizar_distritos()

    def exportar_excel_distritos(self):
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if not filename:
            return
        distritos = obtener_distritos()
        df = pd.DataFrame([{'Distrito': d['nombre']} for d in distritos])
        df.to_excel(filename, index=False)
        messagebox.showinfo("Éxito", "Distritos exportados correctamente")

    def agregar_distrito(self):
        ventana = tk.Toplevel(self.parent)
        ventana.title("Agregar Distrito")
        ventana.geometry("350x120")
        self.centrar_ventana(ventana)
        ttk.Label(ventana, text="Nombre:").pack(pady=5)
        nombre = ttk.Entry(ventana, width=40)
        nombre.pack(pady=5)
        def guardar():
            if nombre.get().strip():
                agregar_distrito(nombre.get().strip())
                self.actualizar_distritos()
                ventana.destroy()
                messagebox.showinfo("Éxito", "Distrito agregado correctamente")
            else:
                messagebox.showwarning("Advertencia", "Ingrese un nombre")
        frame_botones = ttk.Frame(ventana)
        frame_botones.pack(pady=10)
        ttk.Button(frame_botones, text="Guardar", command=guardar).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Cerrar", command=ventana.destroy).pack(side="left", padx=5)

    def editar_distrito(self):
        selected = self.tree_distritos.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un distrito para editar")
            return
        item = self.tree_distritos.item(selected[0])
        ventana = tk.Toplevel(self.parent)
        ventana.title("Editar Distrito")
        ventana.geometry("350x120")
        self.centrar_ventana(ventana)
        ttk.Label(ventana, text="Nuevo nombre:").pack(pady=5)
        nuevo_nombre = ttk.Entry(ventana, width=40)
        nuevo_nombre.insert(0, item['values'][0])
        nuevo_nombre.pack(pady=5)
        def guardar():
            id_distrito = self.obtener_id_distrito(item['values'][0])
            actualizar_distrito(id_distrito, nuevo_nombre.get())
            self.actualizar_distritos()
            ventana.destroy()
            messagebox.showinfo("Éxito", "Distrito actualizado correctamente")
        frame_botones = ttk.Frame(ventana)
        frame_botones.pack(pady=10)
        ttk.Button(frame_botones, text="Guardar", command=guardar).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Cerrar", command=ventana.destroy).pack(side="left", padx=5)

    def eliminar_distrito(self):
        selected = self.tree_distritos.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un distrito para eliminar")
            return
        item = self.tree_distritos.item(selected[0])
        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este distrito?"):
            id_distrito = self.obtener_id_distrito(item['values'][0])
            eliminar_distrito(id_distrito)
            self.actualizar_distritos()
            messagebox.showinfo("Éxito", "Distrito eliminado correctamente")

    def actualizar_distritos(self):
        self.tree_distritos.delete(*self.tree_distritos.get_children())
        for d in obtener_distritos():
            self.tree_distritos.insert('', 'end', values=(d['nombre'],))

    def obtener_id_distrito(self, nombre):
        for d in obtener_distritos():
            if d['nombre'] == nombre:
                return d['id']
        return None

    # --------- TIPOS DE SERVICIO ---------
    def setup_tipos_tab(self):
        frame_excel = ttk.LabelFrame(self.tab_tipos, text="Carga desde Excel")
        frame_excel.pack(fill="x", padx=5, pady=5)
        ttk.Button(frame_excel, text="Cargar Excel", command=self.cargar_excel_tipos).pack(side="left", padx=5, pady=5)
        ttk.Button(frame_excel, text="Exportar a Excel", command=self.exportar_excel_tipos).pack(side="left", padx=5, pady=5)

        frame_lista = ttk.LabelFrame(self.tab_tipos, text="Tipos de Servicio")
        frame_lista.pack(fill="both", expand=True, padx=5, pady=5)

        self.tree_tipos = ttk.Treeview(frame_lista, columns=('distrito', 'descripcion'), show='headings')
        self.tree_tipos.heading('distrito', text='Distrito')
        self.tree_tipos.heading('descripcion', text='Tipo de Servicio')
        self.tree_tipos.grid(row=0, column=0, sticky="nsew")
        scrolly = ttk.Scrollbar(frame_lista, orient="vertical", command=self.tree_tipos.yview)
        self.tree_tipos.configure(yscrollcommand=scrolly.set)
        scrolly.grid(row=0, column=1, sticky="ns")
        frame_lista.grid_rowconfigure(0, weight=1)
        frame_lista.grid_columnconfigure(0, weight=1)

        frame_botones = ttk.Frame(frame_lista)
        frame_botones.grid(row=1, column=0, columnspan=2, pady=5)
        ttk.Button(frame_botones, text="Agregar", command=self.agregar_tipo).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Editar", command=self.editar_tipo).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Eliminar", command=self.eliminar_tipo).pack(side="left", padx=5)

    def cargar_excel_tipos(self):
        filename = filedialog.askopenfilename(title="Seleccionar archivo Excel de Tipos de Servicio", filetypes=[("Excel files", "*.xlsx *.xls")])
        if not filename:
            return
        df = pd.read_excel(filename)
        required_columns = ['Distrito', 'Tipo de Servicio']
        if not all(col in df.columns for col in required_columns):
            messagebox.showerror("Error", "El archivo debe tener las columnas: Distrito, Tipo de Servicio")
            return
        for _, row in df.iterrows():
            distrito = str(row['Distrito']).strip()
            tipo = str(row['Tipo de Servicio']).strip()
            id_distrito = self.obtener_id_distrito(distrito)
            if not id_distrito:
                id_distrito = agregar_distrito(distrito)
            agregar_tipo_servicio(id_distrito, tipo)
        messagebox.showinfo("Éxito", "Tipos de servicio cargados correctamente")
        self.actualizar_tipos()

    def exportar_excel_tipos(self):
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if not filename:
            return
        datos = []
        for d in obtener_distritos():
            for t in obtener_tipos_servicio_por_distrito(d['id']):
                datos.append({'Distrito': d['nombre'], 'Tipo de Servicio': t['descripcion']})
        df = pd.DataFrame(datos)
        df.to_excel(filename, index=False)
        messagebox.showinfo("Éxito", "Tipos de servicio exportados correctamente")

    def agregar_tipo(self):
        ventana = tk.Toplevel(self.parent)
        ventana.title("Agregar Tipo de Servicio")
        ventana.geometry("350x180")
        self.centrar_ventana(ventana)
        ttk.Label(ventana, text="Distrito:").pack(pady=5)
        combo_distrito = ttk.Combobox(ventana, state="readonly")
        distritos = obtener_distritos()
        combo_distrito['values'] = [d['nombre'] for d in distritos]
        combo_distrito.pack(pady=5)
        ttk.Label(ventana, text="Tipo de Servicio:").pack(pady=5)
        descripcion = ttk.Entry(ventana, width=40)
        descripcion.pack(pady=5)
        def guardar():
            if combo_distrito.get() and descripcion.get().strip():
                id_distrito = self.obtener_id_distrito(combo_distrito.get())
                agregar_tipo_servicio(id_distrito, descripcion.get().strip())
                self.actualizar_tipos()
                ventana.destroy()
                messagebox.showinfo("Éxito", "Tipo de servicio agregado correctamente")
            else:
                messagebox.showwarning("Advertencia", "Complete todos los campos")
        frame_botones = ttk.Frame(ventana)
        frame_botones.pack(pady=10)
        ttk.Button(frame_botones, text="Guardar", command=guardar).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Cerrar", command=ventana.destroy).pack(side="left", padx=5)
        
    def editar_tipo(self):
        selected = self.tree_tipos.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un tipo de servicio para editar")
            return
        item = self.tree_tipos.item(selected[0])
        ventana = tk.Toplevel(self.parent)
        ventana.title("Editar Tipo de Servicio")
        ventana.geometry("350x180")
        self.centrar_ventana(ventana)
        ttk.Label(ventana, text="Distrito:").pack(pady=5)
        combo_distrito = ttk.Combobox(ventana, state="readonly")
        distritos = obtener_distritos()
        combo_distrito['values'] = [d['nombre'] for d in distritos]
        combo_distrito.set(item['values'][0])
        combo_distrito.pack(pady=5)
        ttk.Label(ventana, text="Tipo de Servicio:").pack(pady=5)
        descripcion = ttk.Entry(ventana, width=40)
        descripcion.insert(0, item['values'][1])
        descripcion.pack(pady=5)
        def guardar():
            id_distrito = self.obtener_id_distrito(combo_distrito.get())
            id_tipo = self.obtener_id_tipo_servicio(item['values'][1], item['values'][0])
            actualizar_tipo_servicio(id_tipo, descripcion.get().strip())
            self.actualizar_tipos()
            ventana.destroy()
            messagebox.showinfo("Éxito", "Tipo de servicio actualizado correctamente")
        frame_botones = ttk.Frame(ventana)
        frame_botones.pack(pady=10)
        ttk.Button(frame_botones, text="Guardar", command=guardar).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Cerrar", command=ventana.destroy).pack(side="left", padx=5)

    def eliminar_tipo(self):
        selected = self.tree_tipos.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un tipo de servicio para eliminar")
            return
        item = self.tree_tipos.item(selected[0])
        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este tipo de servicio?"):
            id_tipo = self.obtener_id_tipo_servicio(item['values'][1], item['values'][0])
            eliminar_tipo_servicio(id_tipo)
            self.actualizar_tipos()
            messagebox.showinfo("Éxito", "Tipo de servicio eliminado correctamente")

    def actualizar_tipos(self):
        self.tree_tipos.delete(*self.tree_tipos.get_children())
        for d in obtener_distritos():
            for t in obtener_tipos_servicio_por_distrito(d['id']):
                self.tree_tipos.insert('', 'end', values=(d['nombre'], t['descripcion']))

    def obtener_id_tipo_servicio(self, nombre_tipo, nombre_distrito):
        id_distrito = self.obtener_id_distrito(nombre_distrito)
        if id_distrito:
            for tipo in obtener_tipos_servicio_por_distrito(id_distrito):
                if tipo['descripcion'] == nombre_tipo:
                    return tipo['id']
        return None

    # --------- SERVICIOS ---------
    def setup_servicios_tab(self):
        frame_excel = ttk.LabelFrame(self.tab_servicios, text="Carga desde Excel")
        frame_excel.pack(fill="x", padx=5, pady=5)
        ttk.Button(frame_excel, text="Cargar Excel", command=self.cargar_excel_servicios).pack(side="left", padx=5, pady=5)
        ttk.Button(frame_excel, text="Exportar a Excel", command=self.exportar_excel_servicios).pack(side="left", padx=5, pady=5)

        frame_lista = ttk.LabelFrame(self.tab_servicios, text="Servicios")
        frame_lista.pack(fill="both", expand=True, padx=5, pady=5)

        self.tree_servicios = ttk.Treeview(frame_lista, columns=('distrito', 'tipo', 'nombre'), show='headings')
        self.tree_servicios.heading('distrito', text='Distrito')
        self.tree_servicios.heading('tipo', text='Tipo de Servicio')
        self.tree_servicios.heading('nombre', text='Servicio')
        self.tree_servicios.grid(row=0, column=0, sticky="nsew")
        scrolly = ttk.Scrollbar(frame_lista, orient="vertical", command=self.tree_servicios.yview)
        self.tree_servicios.configure(yscrollcommand=scrolly.set)
        scrolly.grid(row=0, column=1, sticky="ns")
        frame_lista.grid_rowconfigure(0, weight=1)
        frame_lista.grid_columnconfigure(0, weight=1)

        frame_botones = ttk.Frame(frame_lista)
        frame_botones.grid(row=1, column=0, columnspan=2, pady=5)
        ttk.Button(frame_botones, text="Agregar", command=self.agregar_servicio).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Editar", command=self.editar_servicio).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Eliminar", command=self.eliminar_servicio).pack(side="left", padx=5)

    def cargar_excel_servicios(self):
        filename = filedialog.askopenfilename(title="Seleccionar archivo Excel de Servicios", filetypes=[("Excel files", "*.xlsx *.xls")])
        if not filename:
            return
        df = pd.read_excel(filename)
        required_columns = ['Distrito', 'Tipo de Servicio', 'Servicio']
        if not all(col in df.columns for col in required_columns):
            messagebox.showerror("Error", "El archivo debe tener las columnas: Distrito, Tipo de Servicio, Servicio")
            return
        for _, row in df.iterrows():
            distrito = str(row['Distrito']).strip()
            tipo = str(row['Tipo de Servicio']).strip()
            servicio = str(row['Servicio']).strip()
            id_distrito = self.obtener_id_distrito(distrito)
            if not id_distrito:
                id_distrito = agregar_distrito(distrito)
            id_tipo = self.obtener_id_tipo_servicio(tipo, distrito)
            if not id_tipo:
                id_tipo = agregar_tipo_servicio(id_distrito, tipo)
            agregar_servicio(id_tipo, servicio)
        messagebox.showinfo("Éxito", "Servicios cargados correctamente")
        self.actualizar_servicios()

    def exportar_excel_servicios(self):
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if not filename:
            return
        datos = []
        for d in obtener_distritos():
            for t in obtener_tipos_servicio_por_distrito(d['id']):
                for s in obtener_servicios_por_tipo(t['id']):
                    datos.append({'Distrito': d['nombre'], 'Tipo de Servicio': t['descripcion'], 'Servicio': s['nombre']})
        df = pd.DataFrame(datos)
        df.to_excel(filename, index=False)
        messagebox.showinfo("Éxito", "Servicios exportados correctamente")

    def agregar_servicio(self):
        ventana = tk.Toplevel(self.parent)
        ventana.title("Agregar Servicio")
        ventana.geometry("350x250")
        self.centrar_ventana(ventana)
        ttk.Label(ventana, text="Distrito:").pack(pady=5)
        combo_distrito = ttk.Combobox(ventana, state="readonly")
        distritos = obtener_distritos()
        combo_distrito['values'] = [d['nombre'] for d in distritos]
        combo_distrito.pack(pady=5)
        ttk.Label(ventana, text="Tipo de Servicio:").pack(pady=5)
        combo_tipo = ttk.Combobox(ventana, state="readonly")
        combo_tipo.pack(pady=5)
        def actualizar_tipos(event):
            id_distrito = self.obtener_id_distrito(combo_distrito.get())
            tipos = obtener_tipos_servicio_por_distrito(id_distrito) if id_distrito else []
            combo_tipo['values'] = [t['descripcion'] for t in tipos]
            combo_tipo.set('')
        combo_distrito.bind("<<ComboboxSelected>>", actualizar_tipos)
        ttk.Label(ventana, text="Servicio:").pack(pady=5)
        nombre = ttk.Entry(ventana, width=40)
        nombre.pack(pady=5)
        def guardar():
            if combo_distrito.get() and combo_tipo.get() and nombre.get().strip():
                id_tipo = self.obtener_id_tipo_servicio(combo_tipo.get(), combo_distrito.get())
                agregar_servicio(id_tipo, nombre.get().strip())
                self.actualizar_servicios()
                ventana.destroy()
                messagebox.showinfo("Éxito", "Servicio agregado correctamente")
            else:
                messagebox.showwarning("Advertencia", "Complete todos los campos")
        frame_botones = ttk.Frame(ventana)
        frame_botones.pack(pady=10)
        ttk.Button(frame_botones, text="Guardar", command=guardar).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Cerrar", command=ventana.destroy).pack(side="left", padx=5)

    def editar_servicio(self):
        selected = self.tree_servicios.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un servicio para editar")
            return
        item = self.tree_servicios.item(selected[0])
        ventana = tk.Toplevel(self.parent)
        ventana.title("Editar Servicio")
        ventana.geometry("350x250")
        self.centrar_ventana(ventana)
        ttk.Label(ventana, text="Distrito:").pack(pady=5)
        combo_distrito = ttk.Combobox(ventana, state="readonly")
        distritos = obtener_distritos()
        combo_distrito['values'] = [d['nombre'] for d in distritos]
        combo_distrito.set(item['values'][0])
        combo_distrito.pack(pady=5)
        ttk.Label(ventana, text="Tipo de Servicio:").pack(pady=5)
        combo_tipo = ttk.Combobox(ventana, state="readonly")
        combo_tipo.pack(pady=5)
        def actualizar_tipos(event):
            id_distrito = self.obtener_id_distrito(combo_distrito.get())
            tipos = obtener_tipos_servicio_por_distrito(id_distrito) if id_distrito else []
            combo_tipo['values'] = [t['descripcion'] for t in tipos]
            combo_tipo.set(item['values'][1])
        combo_distrito.bind("<<ComboboxSelected>>", actualizar_tipos)
        actualizar_tipos(None)
        ttk.Label(ventana, text="Servicio:").pack(pady=5)
        nombre = ttk.Entry(ventana, width=40)
        nombre.insert(0, item['values'][2])
        nombre.pack(pady=5)
        def guardar():
            id_tipo = self.obtener_id_tipo_servicio(combo_tipo.get(), combo_distrito.get())
            id_servicio = self.obtener_id_servicio(item['values'][2], item['values'][1], item['values'][0])
            actualizar_servicio(id_servicio, nombre.get().strip())
            self.actualizar_servicios()
            ventana.destroy()
            messagebox.showinfo("Éxito", "Servicio actualizado correctamente")
        frame_botones = ttk.Frame(ventana)
        frame_botones.pack(pady=10)
        ttk.Button(frame_botones, text="Guardar", command=guardar).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Cerrar", command=ventana.destroy).pack(side="left", padx=5)

    def eliminar_servicio(self):
        selected = self.tree_servicios.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un servicio para eliminar")
            return
        item = self.tree_servicios.item(selected[0])
        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este servicio?"):
            id_servicio = self.obtener_id_servicio(item['values'][2], item['values'][1], item['values'][0])
            eliminar_servicio(id_servicio)
            self.actualizar_servicios()
            messagebox.showinfo("Éxito", "Servicio eliminado correctamente")

    def actualizar_servicios(self):
        self.tree_servicios.delete(*self.tree_servicios.get_children())
        for d in obtener_distritos():
            for t in obtener_tipos_servicio_por_distrito(d['id']):
                for s in obtener_servicios_por_tipo(t['id']):
                    self.tree_servicios.insert('', 'end', values=(d['nombre'], t['descripcion'], s['nombre']))

    def obtener_id_servicio(self, nombre_servicio, nombre_tipo, nombre_distrito):
        id_tipo = self.obtener_id_tipo_servicio(nombre_tipo, nombre_distrito)
        if id_tipo:
            for s in obtener_servicios_por_tipo(id_tipo):
                if s['nombre'] == nombre_servicio:
                    return s['id']
        return None

    def cerrar_ventana(self):
        if messagebox.askyesno("Confirmar", "¿Está seguro que desea cerrar esta ventana?"):
            for widget in self.parent.winfo_children():
                widget.destroy()
            self.main_window.show_welcome_screen()