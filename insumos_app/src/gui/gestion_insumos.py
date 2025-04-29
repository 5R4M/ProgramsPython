import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import pandas as pd
import sqlite3
import sys
import os
from src.database import (
    DB_PATH,
    verificar_tablas,
    crear_base_datos
)

# Validar que las dependencias necesarias estén instaladas
try:
    import pandas as pd
except ImportError:
    messagebox.showerror("Error", "El módulo pandas no está instalado. Por favor, instálelo con 'pip install pandas'")
    sys.exit(1)

# Agregar el directorio raíz del proyecto al PATH de Python
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# Importaciones locales
from src.database.db_manager import (
    obtener_tipos_insumo,
    obtener_presentaciones,
    obtener_insumos_por_tipo,
    obtener_insumo_por_id,
    agregar_tipo_insumo,
    agregar_presentacion,
    agregar_insumo,
    actualizar_tipo_insumo,
    actualizar_insumo,
    eliminar_tipo_insumo,
    eliminar_presentacion,
    eliminar_insumo,
    verificar_conexion
)

from src.database import crear_base_datos, DB_PATH, verificar_tablas

class GestionInsumos:
    
    def verificar_base_datos(self):
        """Verifica que la base de datos exista y tenga la estructura correcta"""
        try:
            # Verificar si la base de datos existe
            if not os.path.exists(DB_PATH):
                if not crear_base_datos():
                    raise Exception("No se pudo crear la base de datos")
                print("Base de datos creada correctamente")

            # Verificar la estructura de la base de datos
            if not verificar_tablas():
                print("La estructura de la base de datos es incorrecta. Recreándola...")
                if os.path.exists(DB_PATH):
                    os.remove(DB_PATH)
                if not crear_base_datos():
                    raise Exception("No se pudo recrear la base de datos")
                print("Base de datos recreada correctamente")

            return True

        except Exception as e:
            print(f"Error al verificar la base de datos: {e}")
            return False
    
    def __init__(self, parent_frame, main_window):
        self.parent = parent_frame
        self.main_window = main_window
        
        # Verificar la base de datos antes de continuar
        if not self.verificar_base_datos():
            messagebox.showerror("Error",
                "Error en la base de datos. La aplicación no puede continuar.")
            self.cerrar_ventana()
            return

        # Verificar conexión a la base de datos
        if not self.verificar_conexion_db():
            messagebox.showerror("Error",
                "No se pudo conectar a la base de datos")
            self.cerrar_ventana()
            return

        self.setup_ui()
    
    def verificar_conexion_db(self):
        """Verifica la conexión a la base de datos."""
        try:
            return verificar_conexion()
        except Exception as e:
            print(f"Error al verificar conexión: {e}")
            return False
    
    def centrar_ventana(self, ventana):
        """Centra una ventana en la pantalla."""
        ventana.update_idletasks()
        width = ventana.winfo_width()
        height = ventana.winfo_height()
        x = (ventana.winfo_screenwidth() // 2) - (width // 2)
        y = (ventana.winfo_screenheight() // 2) - (height // 2)
        ventana.geometry(f'{width}x{height}+{x}+{y}')

    def obtener_id_tipo_insumo(self, descripcion):
        """Obtiene el ID de un tipo de insumo por su descripción."""
        tipos = obtener_tipos_insumo()
        if tipos:
            for tipo in tipos:
                if tipo['descripcion'] == descripcion:
                    return tipo['id']
        return None

    def obtener_id_presentacion(self, nombre):
        """Obtiene el ID de una presentación por su nombre."""
        presentaciones = obtener_presentaciones()
        if presentaciones:
            for pres in presentaciones:
                if pres['nombre'] == nombre:
                    return pres['id']
        return None

    def obtener_id_insumo(self, nombre_insumo, id_tipo_insumo):
        """Obtiene el ID de un insumo por su nombre y tipo de insumo."""
        insumos = obtener_insumos_por_tipo(id_tipo_insumo)
        if insumos:
            for insumo in insumos:
                if insumo['nombre'] == nombre_insumo:
                    return insumo['id']
        return None

    def setup_ui(self):
        # Notebook para pestañas
        self.notebook = ttk.Notebook(self.parent)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # Pestañas
        self.tab_tipos = ttk.Frame(self.notebook)
        self.tab_insumos = ttk.Frame(self.notebook)
        self.tab_presentaciones = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_tipos, text="Tipos de Insumo")
        self.notebook.add(self.tab_insumos, text="Insumos")
        self.notebook.add(self.tab_presentaciones, text="Presentaciones")

        # Configurar cada pestaña
        self.setup_tipos_tab()
        self.setup_insumos_tab()
        self.setup_presentaciones_tab()

        # Botón Cerrar
        ttk.Button(self.parent, text="Cerrar",
                  command=self.cerrar_ventana).pack(pady=10)

        self.actualizar_tipos()
        self.actualizar_insumos()
        self.actualizar_presentaciones()

    # --------- TIPOS DE INSUMO ---------
    def setup_tipos_tab(self):
        frame_excel = ttk.LabelFrame(self.tab_tipos, text="Carga desde Excel")
        frame_excel.pack(fill="x", padx=5, pady=5)
        ttk.Button(frame_excel, text="Cargar Excel", command=self.cargar_excel_tipos).pack(side="left", padx=5, pady=5)
        ttk.Button(frame_excel, text="Exportar a Excel", command=self.exportar_excel_tipos).pack(side="left", padx=5, pady=5)

        frame_lista = ttk.LabelFrame(self.tab_tipos, text="Tipos de Insumo")
        frame_lista.pack(fill="both", expand=True, padx=5, pady=5)

        self.tree_tipos = ttk.Treeview(frame_lista, columns=('descripcion',), show='headings')
        self.tree_tipos.heading('descripcion', text='Tipo Insumo')
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
        filename = filedialog.askopenfilename(title="Seleccionar archivo Excel", filetypes=[("Excel files", "*.xlsx *.xls")])
        if not filename:
            return
        try:
            df = pd.read_excel(filename)
            if 'Tipo de Insumo' not in df.columns:
                messagebox.showerror("Error", "El archivo debe tener la columna: Tipo de Insumo")
                return

            for tipo in df['Tipo de Insumo'].dropna().unique():
                tipo = str(tipo).strip()
                if tipo:  # Verificar que no esté vacío
                    try:
                        agregar_tipo_insumo(tipo)
                    except sqlite3.IntegrityError:
                        print(f"El tipo de insumo '{tipo}' ya existe")
                        continue

            self.actualizar_tipos()
            messagebox.showinfo("Éxito", "Tipos de insumo cargados correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar el archivo: {str(e)}")

    def exportar_excel_tipos(self):
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if not filename:
            return
        tipos = obtener_tipos_insumo()
        df = pd.DataFrame([{'Tipo de Insumo': t['descripcion']} for t in tipos])
        df.to_excel(filename, index=False)
        messagebox.showinfo("Éxito", "Tipos de insumo exportados correctamente")

    def agregar_tipo(self):
        try:
            ventana = tk.Toplevel(self.parent)
            ventana.title("Agregar Tipo de Insumo")
            ventana.geometry("350x120")
            self.centrar_ventana(ventana)

            ttk.Label(ventana, text="Descripción:").pack(pady=5)
            descripcion = ttk.Entry(ventana, width=40)
            descripcion.pack(pady=5)

            def guardar():
                try:
                    if not descripcion.get().strip():
                        messagebox.showwarning("Advertencia",
                            "Ingrese una descripción")
                        return

                    if not self.verificar_conexion_db():
                        messagebox.showerror("Error",
                            "No hay conexión con la base de datos")
                        return

                    agregar_tipo_insumo(descripcion.get().strip())
                    self.actualizar_tipos()
                    ventana.destroy()
                    messagebox.showinfo("Éxito",
                        "Tipo de insumo agregado correctamente")
                except sqlite3.IntegrityError:
                    messagebox.showerror("Error",
                        "Ya existe un tipo de insumo con esa descripción")
                except Exception as e:
                    messagebox.showerror("Error",
                        f"Error al agregar tipo de insumo: {str(e)}")

            frame_botones = ttk.Frame(ventana)
            frame_botones.pack(pady=10)
            ttk.Button(frame_botones, text="Guardar",
                    command=guardar).pack(side="left", padx=5)
            ttk.Button(frame_botones, text="Cerrar",
                    command=ventana.destroy).pack(side="left", padx=5)

        except Exception as e:
            messagebox.showerror("Error",
                f"Error al crear ventana: {str(e)}")

    def editar_tipo(self):
        selected = self.tree_tipos.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un tipo de insumo para editar")
            return
        item = self.tree_tipos.item(selected[0])
        ventana = tk.Toplevel(self.parent)
        ventana.title("Editar Tipo de Insumo")
        ventana.geometry("350x120")
        self.centrar_ventana(ventana)
        ttk.Label(ventana, text="Nuevo nombre:").pack(pady=5)
        nuevo_nombre = ttk.Entry(ventana, width=40)
        nuevo_nombre.insert(0, item['values'][0])
        nuevo_nombre.pack(pady=5)
        def guardar():
            id_tipo = self.obtener_id_tipo_insumo(item['values'][0])
            actualizar_tipo_insumo(id_tipo, nuevo_nombre.get())
            self.actualizar_tipos()
            ventana.destroy()
            messagebox.showinfo("Éxito", "Tipo de insumo actualizado correctamente")
        frame_botones = ttk.Frame(ventana)
        frame_botones.pack(pady=10)
        ttk.Button(frame_botones, text="Guardar", command=guardar).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Cerrar", command=ventana.destroy).pack(side="left", padx=5)

    def eliminar_tipo(self):
        selected = self.tree_tipos.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un tipo de insumo para eliminar")
            return
        item = self.tree_tipos.item(selected[0])
        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este tipo de insumo?"):
            id_tipo = self.obtener_id_tipo_insumo(item['values'][0])
            eliminar_tipo_insumo(id_tipo)
            self.actualizar_tipos()
            messagebox.showinfo("Éxito", "Tipo de insumo eliminado correctamente")

    def actualizar_tipos(self):
        """Actualiza la lista de tipos de insumo en el TreeView"""
        try:
            self.tree_tipos.delete(*self.tree_tipos.get_children())
            tipos = obtener_tipos_insumo()
            if tipos is None:
                raise Exception("No se pudieron obtener los tipos de insumo")
            for tipo in tipos:
                self.tree_tipos.insert('', 'end', values=(tipo['descripcion'],))
        except Exception as e:
            messagebox.showerror("Error",
                f"Error al actualizar tipos de insumo: {str(e)}")

    def obtener_id_tipo_insumo(self, descripcion):
        tipos = obtener_tipos_insumo()
        for tipo in tipos:
            if tipo['descripcion'] == descripcion:
                return tipo['id']
        return None

    # --------- INSUMOS ---------
    def setup_insumos_tab(self):
        frame_excel = ttk.LabelFrame(self.tab_insumos, text="Carga desde Excel")
        frame_excel.pack(fill="x", padx=5, pady=5)
        ttk.Button(frame_excel, text="Cargar Excel", command=self.cargar_excel_insumos).pack(side="left", padx=5, pady=5)
        ttk.Button(frame_excel, text="Exportar a Excel", command=self.exportar_excel_insumos).pack(side="left", padx=5, pady=5)

        frame_lista = ttk.LabelFrame(self.tab_insumos, text="Insumos")
        frame_lista.pack(fill="both", expand=True, padx=5, pady=5)

        self.tree_insumos = ttk.Treeview(frame_lista, columns=('tipo', 'nombre'), show='headings')
        self.tree_insumos.heading('tipo', text='Tipo de Insumo')
        self.tree_insumos.heading('nombre', text='Insumo')
        self.tree_insumos.grid(row=0, column=0, sticky="nsew")
        scrolly = ttk.Scrollbar(frame_lista, orient="vertical", command=self.tree_insumos.yview)
        self.tree_insumos.configure(yscrollcommand=scrolly.set)
        scrolly.grid(row=0, column=1, sticky="ns")
        frame_lista.grid_rowconfigure(0, weight=1)
        frame_lista.grid_columnconfigure(0, weight=1)

        frame_botones = ttk.Frame(frame_lista)
        frame_botones.grid(row=1, column=0, columnspan=2, pady=5)
        ttk.Button(frame_botones, text="Agregar", command=self.agregar_insumo).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Editar", command=self.editar_insumo).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Eliminar", command=self.eliminar_insumo).pack(side="left", padx=5)

    def cargar_excel_insumos(self):
        try:
            filename = filedialog.askopenfilename(
                title="Seleccionar archivo Excel",
                filetypes=[("Excel files", "*.xlsx *.xls")]
            )

            if not filename:
                return

            # Validar el archivo
            if not os.path.exists(filename):
                messagebox.showerror("Error", "El archivo seleccionado no existe")
                return

            # Leer el archivo Excel
            try:
                df = pd.read_excel(filename)
            except Exception as e:
                messagebox.showerror("Error", f"Error al leer el archivo Excel: {str(e)}")
                return

            # Validar columnas
            columnas_requeridas = ['Tipo de Insumo', 'Insumo', 'Presentación']
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]

            if columnas_faltantes:
                messagebox.showerror("Error",
                    f"Faltan las siguientes columnas: {', '.join(columnas_faltantes)}")
                return

            # Procesar datos
            registros_procesados = 0
            errores = []

            for _, row in df.iterrows():
                try:
                    tipo = str(row['Tipo de Insumo']).strip()
                    insumo = str(row['Insumo']).strip()
                    presentacion = str(row['Presentación']).strip()

                    if not all([tipo, insumo, presentacion]):
                        continue

                    # Obtener o crear tipo de insumo
                    id_tipo = self.obtener_id_tipo_insumo(tipo)
                    if not id_tipo:
                        id_tipo = agregar_tipo_insumo(tipo)

                    # Obtener o crear presentación
                    id_presentacion = self.obtener_id_presentacion(presentacion)
                    if not id_presentacion:
                        id_presentacion = agregar_presentacion(presentacion)

                    # Agregar insumo
                    agregar_insumo(
                        nombre=insumo,
                        lote=None,
                        id_presentacion=id_presentacion,
                        fecha_vencimiento=None,
                        id_tipo_insumo=id_tipo
                    )
                    registros_procesados += 1

                except Exception as e:
                    errores.append(f"Error en fila {_ + 2}: {str(e)}")

            # Actualizar interfaz
            self.actualizar_insumos()
            self.actualizar_presentaciones()

            # Mostrar resultado
            if errores:
                mensaje = f"Se procesaron {registros_procesados} registros con {len(errores)} errores.\n\n"
                mensaje += "\n".join(errores[:5])
                if len(errores) > 5:
                    mensaje += f"\n... y {len(errores) - 5} errores más."
                messagebox.showwarning("Advertencia", mensaje)
            else:
                messagebox.showinfo("Éxito", f"Se procesaron {registros_procesados} registros correctamente")

        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")

    def exportar_excel_insumos(self):
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if not filename:
            return
        datos = []
        for tipo in obtener_tipos_insumo():
            insumos = obtener_insumos_por_tipo(tipo['id'])
            for insumo in insumos:
                datos.append({'Tipo de Insumo': tipo['descripcion'], 'Insumo': insumo['nombre']})
        df = pd.DataFrame(datos)
        df.to_excel(filename, index=False)
        messagebox.showinfo("Éxito", "Insumos exportados correctamente")

    def agregar_insumo(self):
        ventana = tk.Toplevel(self.parent)
        ventana.title("Agregar Insumo")
        ventana.geometry("350x200")
        self.centrar_ventana(ventana)

        # Frame para los campos
        frame_campos = ttk.Frame(ventana)
        frame_campos.pack(padx=10, pady=5, fill='x')

        # Tipo de Insumo
        ttk.Label(frame_campos, text="Tipo de Insumo:").pack(pady=5)
        combo_tipo = ttk.Combobox(frame_campos, state="readonly")
        tipos = obtener_tipos_insumo()
        combo_tipo['values'] = [t['descripcion'] for t in tipos]
        combo_tipo.pack(pady=5, fill='x')

        # Nombre del Insumo
        ttk.Label(frame_campos, text="Nombre:").pack(pady=5)
        nombre = ttk.Entry(frame_campos)
        nombre.pack(pady=5, fill='x')

        def guardar():
            if not combo_tipo.get():
                messagebox.showwarning("Advertencia", "Seleccione un tipo de insumo")
                return
            if not nombre.get().strip():
                messagebox.showwarning("Advertencia", "Ingrese un nombre")
                return

            id_tipo = self.obtener_id_tipo_insumo(combo_tipo.get())

            try:
                agregar_insumo(
                    nombre=nombre.get().strip(),
                    lote=None,
                    id_presentacion=None,
                    fecha_vencimiento=None,
                    id_tipo_insumo=id_tipo
                )
                self.actualizar_insumos()
                ventana.destroy()
                messagebox.showinfo("Éxito", "Insumo agregado correctamente")
            except Exception as e:
                messagebox.showerror("Error", f"Error al agregar insumo: {str(e)}")

        # Frame para los botones
        frame_botones = ttk.Frame(ventana)
        frame_botones.pack(pady=10)
        ttk.Button(frame_botones, text="Guardar", command=guardar).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Cerrar", command=ventana.destroy).pack(side="left", padx=5)

    def editar_insumo(self):
        selected = self.tree_insumos.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un insumo para editar")
            return

        item = self.tree_insumos.item(selected[0])
        ventana = tk.Toplevel(self.parent)
        ventana.title("Editar Insumo")
        ventana.geometry("350x200")
        self.centrar_ventana(ventana)

        # Frame para los campos
        frame_campos = ttk.Frame(ventana)
        frame_campos.pack(padx=10, pady=5, fill='x')

        # Tipo de Insumo
        ttk.Label(frame_campos, text="Tipo de Insumo:").pack(pady=5)
        combo_tipo = ttk.Combobox(frame_campos, state="readonly")
        tipos = obtener_tipos_insumo()
        combo_tipo['values'] = [t['descripcion'] for t in tipos]
        combo_tipo.set(item['values'][0])  # Tipo de insumo actual
        combo_tipo.pack(pady=5, fill='x')

        # Nombre del Insumo
        ttk.Label(frame_campos, text="Nombre:").pack(pady=5)
        nombre = ttk.Entry(frame_campos)
        nombre.insert(0, item['values'][1])  # Nombre actual
        nombre.pack(pady=5, fill='x')


        def guardar():
            if not combo_tipo.get() or not nombre.get().strip():
                messagebox.showwarning("Advertencia", "Complete todos los campos")
                return

            try:
                id_tipo = self.obtener_id_tipo_insumo(combo_tipo.get())
                id_insumo = self.obtener_id_insumo(item['values'][1], self.obtener_id_tipo_insumo(item['values'][0]))

                actualizar_insumo(
                    id_insumo=id_insumo,
                    nombre=nombre.get().strip(),
                    lote=None,
                    id_presentacion=None,
                    fecha_vencimiento=None,
                    id_tipo_insumo=id_tipo
                )
                self.actualizar_insumos()
                ventana.destroy()
                messagebox.showinfo("Éxito", "Insumo actualizado correctamente")
            except Exception as e:
                messagebox.showerror("Error", f"Error al actualizar insumo: {str(e)}")

        # Frame para los botones
        frame_botones = ttk.Frame(ventana)
        frame_botones.pack(pady=10)
        ttk.Button(frame_botones, text="Guardar", command=guardar).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Cerrar", command=ventana.destroy).pack(side="left", padx=5)

    def eliminar_insumo(self):
        selected = self.tree_insumos.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un insumo para eliminar")
            return
        item = self.tree_insumos.item(selected[0])
        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este insumo?"):
            id_tipo = self.obtener_id_tipo_insumo(item['values'][0])
            id_insumo = self.obtener_id_insumo(item['values'][1], id_tipo)
            eliminar_insumo(id_insumo)
            self.actualizar_insumos()
            messagebox.showinfo("Éxito", "Insumo eliminado correctamente")

    def actualizar_insumos(self):
        """Actualiza la lista de insumos en el TreeView."""
        try:
            self.tree_insumos.delete(*self.tree_insumos.get_children())
            tipos = obtener_tipos_insumo()

            if not tipos:
                return

            for tipo in tipos:
                insumos = obtener_insumos_por_tipo(tipo['id'])
                if insumos:
                    for insumo in insumos:
                        if isinstance(insumo, sqlite3.Row):
                            insumo = dict(insumo)
                        nombre = insumo['nombre'] if 'nombre' in insumo else 'N/A'
                        self.tree_insumos.insert('', 'end', values=(
                            tipo['descripcion'],
                            nombre
                        ))

        except Exception as e:
            print(f"Error específico al actualizar insumos: {str(e)}")
            messagebox.showerror("Error", f"Error al actualizar insumos: {str(e)}")
                
    def obtener_id_insumo(self, nombre_insumo, id_tipo_insumo):
        insumos = obtener_insumos_por_tipo(id_tipo_insumo)
        for insumo in insumos:
            if insumo['nombre'] == nombre_insumo:
                return insumo['id']
        return None

    # --------- PRESENTACIONES ---------
    def setup_presentaciones_tab(self):
        frame_excel = ttk.LabelFrame(self.tab_presentaciones, text="Carga desde Excel")
        frame_excel.pack(fill="x", padx=5, pady=5)
        ttk.Button(frame_excel, text="Cargar Excel", command=self.cargar_excel_presentaciones).pack(side="left", padx=5, pady=5)
        ttk.Button(frame_excel, text="Exportar a Excel", command=self.exportar_excel_presentaciones).pack(side="left", padx=5, pady=5)

        frame_lista = ttk.LabelFrame(self.tab_presentaciones, text="Presentaciones")
        frame_lista.pack(fill="both", expand=True, padx=5, pady=5)

        self.tree_presentaciones = ttk.Treeview(frame_lista,
        columns=('tipo', 'insumo', 'presentacion'), show='headings')
        self.tree_presentaciones.heading('tipo', text='Tipo de Insumo')
        self.tree_presentaciones.heading('insumo', text='Insumo')
        self.tree_presentaciones.heading('presentacion', text='Presentación')
        self.tree_presentaciones.grid(row=0, column=0, sticky="nsew")
        scrolly = ttk.Scrollbar(frame_lista, orient="vertical", command=self.tree_presentaciones.yview)
        self.tree_presentaciones.configure(yscrollcommand=scrolly.set)
        scrolly.grid(row=0, column=1, sticky="ns")
        frame_lista.grid_rowconfigure(0, weight=1)
        frame_lista.grid_columnconfigure(0, weight=1)

        frame_botones = ttk.Frame(frame_lista)
        frame_botones.grid(row=1, column=0, columnspan=2, pady=5)
        ttk.Button(frame_botones, text="Agregar", command=self.agregar_presentacion).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Editar", command=self.editar_presentacion).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Eliminar", command=self.eliminar_presentacion).pack(side="left", padx=5)

    def cargar_excel_presentaciones(self):
        filename = filedialog.askopenfilename(title="Seleccionar archivo Excel", filetypes=[("Excel files", "*.xlsx *.xls")])
        if not filename:
            return
        try:
            df = pd.read_excel(filename)
            if 'Presentación' not in df.columns:
                messagebox.showerror("Error", "El archivo debe tener la columna: Presentación")
                return

            for presentacion in df['Presentación'].dropna().unique():
                presentacion = str(presentacion).strip()
                if presentacion:  # Verificar que no esté vacío
                    try:
                        agregar_presentacion(presentacion)
                    except sqlite3.IntegrityError:
                        print(f"La presentación '{presentacion}' ya existe")
                        continue

            self.actualizar_presentaciones()
            messagebox.showinfo("Éxito", "Presentaciones cargadas correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar el archivo: {str(e)}")

    def exportar_excel_presentaciones(self):
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if not filename:
            return
        presentaciones = obtener_presentaciones()
        df = pd.DataFrame([{'Presentación': p['nombre']} for p in presentaciones])
        df.to_excel(filename, index=False)
        messagebox.showinfo("Éxito", "Presentaciones exportadas correctamente")

    def agregar_presentacion(self):
        ventana = tk.Toplevel(self.parent)
        ventana.title("Agregar Presentación")
        ventana.geometry("350x250")
        self.centrar_ventana(ventana)

        frame_campos = ttk.Frame(ventana)
        frame_campos.pack(padx=10, pady=5, fill='x')

        # Tipo de Insumo
        ttk.Label(frame_campos, text="Tipo de Insumo:").pack(pady=5)
        combo_tipo = ttk.Combobox(frame_campos, state="readonly")
        tipos = obtener_tipos_insumo()
        combo_tipo['values'] = [t['descripcion'] for t in tipos]
        combo_tipo.pack(pady=5, fill='x')

        # Insumo (se actualizará cuando se seleccione el tipo)
        ttk.Label(frame_campos, text="Insumo:").pack(pady=5)
        combo_insumo = ttk.Combobox(frame_campos, state="readonly")
        combo_insumo.pack(pady=5, fill='x')

        # Actualizar insumos cuando cambie el tipo
        def actualizar_insumos(*args):
            combo_insumo['values'] = []
            if combo_tipo.get():
                id_tipo = self.obtener_id_tipo_insumo(combo_tipo.get())
                insumos = obtener_insumos_por_tipo(id_tipo)
                combo_insumo['values'] = [i['nombre'] for i in insumos]

        combo_tipo.bind('<<ComboboxSelected>>', actualizar_insumos)

        # Presentación
        ttk.Label(frame_campos, text="Presentación:").pack(pady=5)
        nombre = ttk.Entry(frame_campos)
        nombre.pack(pady=5, fill='x')

        def guardar():
            if not all([combo_tipo.get(), combo_insumo.get(), nombre.get().strip()]):
                messagebox.showwarning("Advertencia", "Complete todos los campos")
                return

            try:
                id_tipo = self.obtener_id_tipo_insumo(combo_tipo.get())
                id_insumo = self.obtener_id_insumo(combo_insumo.get(), id_tipo)

                # Agregar presentación y asociarla al insumo
                id_presentacion = agregar_presentacion(nombre.get().strip())
                actualizar_insumo(
                    id_insumo=id_insumo,
                    nombre=combo_insumo.get(),
                    lote=None,
                    id_presentacion=id_presentacion,
                    fecha_vencimiento=None,
                    id_tipo_insumo=id_tipo
                )

                self.actualizar_presentaciones()
                ventana.destroy()
                messagebox.showinfo("Éxito", "Presentación agregada correctamente")
            except Exception as e:
                messagebox.showerror("Error", f"Error al agregar presentación: {str(e)}")

        # Frame para los botones
        frame_botones = ttk.Frame(ventana)
        frame_botones.pack(pady=10)
        ttk.Button(frame_botones, text="Guardar", command=guardar).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Cerrar", command=ventana.destroy).pack(side="left", padx=5)

    def editar_presentacion(self):
        selected = self.tree_presentaciones.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione una presentación para editar")
            return

        item = self.tree_presentaciones.item(selected[0])
        ventana = tk.Toplevel(self.parent)
        ventana.title("Editar Presentación")
        ventana.geometry("350x250")
        self.centrar_ventana(ventana)

        frame_campos = ttk.Frame(ventana)
        frame_campos.pack(padx=10, pady=5, fill='x')

        # Tipo de Insumo
        ttk.Label(frame_campos, text="Tipo de Insumo:").pack(pady=5)
        combo_tipo = ttk.Combobox(frame_campos, state="readonly")
        tipos = obtener_tipos_insumo()
        combo_tipo['values'] = [t['descripcion'] for t in tipos]
        combo_tipo.set(item['values'][0])  # Tipo actual
        combo_tipo.pack(pady=5, fill='x')

        # Insumo
        ttk.Label(frame_campos, text="Insumo:").pack(pady=5)
        combo_insumo = ttk.Combobox(frame_campos, state="readonly")
        combo_insumo.pack(pady=5, fill='x')

        def actualizar_insumos(*args):
            combo_insumo['values'] = []
            if combo_tipo.get():
                id_tipo = self.obtener_id_tipo_insumo(combo_tipo.get())
                insumos = obtener_insumos_por_tipo(id_tipo)
                combo_insumo['values'] = [i['nombre'] for i in insumos]

        combo_tipo.bind('<<ComboboxSelected>>', actualizar_insumos)

        # Establecer valores iniciales
        actualizar_insumos()
        combo_insumo.set(item['values'][1])  # Insumo actual

        # Presentación
        ttk.Label(frame_campos, text="Presentación:").pack(pady=5)
        nuevo_nombre = ttk.Entry(frame_campos)
        nuevo_nombre.insert(0, item['values'][2])  # Presentación actual
        nuevo_nombre.pack(pady=5, fill='x')

        def guardar():
            if not all([combo_tipo.get(), combo_insumo.get(), nuevo_nombre.get().strip()]):
                messagebox.showwarning("Advertencia", "Complete todos los campos")
                return

            try:
                id_tipo = self.obtener_id_tipo_insumo(combo_tipo.get())
                id_insumo = self.obtener_id_insumo(combo_insumo.get(), id_tipo)

                # Actualizar la presentación
                id_presentacion = agregar_presentacion(nuevo_nombre.get().strip())

                # Actualizar el insumo con la nueva presentación
                actualizar_insumo(
                    id_insumo=id_insumo,
                    nombre=combo_insumo.get(),
                    lote=None,
                    id_presentacion=id_presentacion,
                    fecha_vencimiento=None,
                    id_tipo_insumo=id_tipo
                )

                self.actualizar_presentaciones()
                ventana.destroy()
                messagebox.showinfo("Éxito", "Presentación actualizada correctamente")
            except Exception as e:
                messagebox.showerror("Error", f"Error al actualizar presentación: {str(e)}")

        frame_botones = ttk.Frame(ventana)
        frame_botones.pack(pady=10)
        ttk.Button(frame_botones, text="Guardar", command=guardar).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Cerrar", command=ventana.destroy).pack(side="left", padx=5)

    def eliminar_presentacion(self):
        selected = self.tree_presentaciones.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione una presentación para eliminar")
            return
        item = self.tree_presentaciones.item(selected[0])
        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar esta presentación?"):
            id_pres = self.obtener_id_presentacion(item['values'][0])
            eliminar_presentacion(id_pres)
            self.actualizar_presentaciones()
            messagebox.showinfo("Éxito", "Presentación eliminada correctamente")

    def actualizar_presentaciones(self):
        """Actualiza la lista de presentaciones en el TreeView"""
        try:
            self.tree_presentaciones.delete(*self.tree_presentaciones.get_children())
            tipos = obtener_tipos_insumo()

            if not tipos:
                return

            for tipo in tipos:
                insumos = obtener_insumos_por_tipo(tipo['id'])
                if insumos:
                    for insumo in insumos:
                        if isinstance(insumo, sqlite3.Row):
                            insumo = dict(insumo)

                        # Obtener la presentación del insumo
                        presentacion = insumo.get('nombre_presentacion', 'N/A')

                        self.tree_presentaciones.insert('', 'end', values=(
                            tipo['descripcion'],
                            insumo['nombre'],
                            presentacion
                        ))

        except Exception as e:
            messagebox.showerror("Error",
                f"Error al actualizar presentaciones: {str(e)}")

    def obtener_id_presentacion(self, nombre):
        presentaciones = obtener_presentaciones()
        for pres in presentaciones:
            if pres['nombre'] == nombre:
                return pres['id']
        return None

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
                    # Intentar cerrar la ventana de todas formas
                    self.parent.destroy()
        except Exception as e:
            print(f"Error al cerrar ventana: {e}")
            try:
                self.parent.destroy()
            except:
                pass