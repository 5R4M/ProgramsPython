import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
import sys

# Agregar el directorio raíz del proyecto al PATH de Python
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from src.database.db_manager import (
    obtener_tipos_insumo,
    obtener_presentaciones,
    obtener_insumos_por_tipo,
    obtener_insumo_por_id,
    obtener_insumo_por_nombre,
    agregar_tipo_insumo,
    agregar_presentacion,
    agregar_insumo,
    actualizar_tipo_insumo,
    actualizar_insumo,
    eliminar_tipo_insumo,
    actualizar_presentacion,
    eliminar_presentacion,
    eliminar_insumo,
    verificar_conexion
)

from src.database import (
    verificar_tablas,
    crear_base_datos
)

def resource_path(relative_path):
    import sys, os
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # subir desde src/gui a src
    return os.path.join(base_path, relative_path)

class GestionInsumos:

    def __init__(self, parent_frame, main_window):
        self.parent = parent_frame
        self.main_window = main_window
        self.setup_styles()

        if not self.verificar_base_datos():
            messagebox.showerror("Error", "Error en la base de datos. La aplicación no puede continuar.")
            self.cerrar_ventana()
            return

        if not self.verificar_conexion_db():
            messagebox.showerror("Error", "No se pudo conectar a la base de datos")
            self.cerrar_ventana()
            return

        self.cargar_iconos()
        self.setup_ui()

    def setup_styles(self):
        self.COLORS = {
            'primary': '#2E86AB',
            'secondary': '#A23B72',
            'success': '#27AE60',
            'warning': '#F39C12',
            'danger': '#E74C3C',
            'accent': '#8E44AD',
            'light': '#F8F9FA',
            'white': '#FFFFFF',
            'text_dark': '#2C3E50',
            'text_light': '#7F8C8D',
            'border': '#BDC3C7'
        }

        style = ttk.Style()
        style.theme_use('clam')

        style.configure('Card.TLabelframe',
                        background=self.COLORS['white'],
                        relief='solid',
                        borderwidth=1,
                        labeloutside=False)

        style.configure('Card.TLabelframe.Label',
                        background=self.COLORS['primary'],
                        foreground=self.COLORS['white'],
                        font=('Segoe UI', 9, 'bold'),
                        padding=(8, 3))

        style.configure('Primary.TButton',
                        font=('Segoe UI', 9, 'bold'),
                        padding=(12, 6),
                        relief='flat',
                        borderwidth=0,
                        background=self.COLORS['primary'],
                        foreground=self.COLORS['white'])

        style.map('Primary.TButton',
                background=[('active', '#1F5F8B'),
                            ('pressed', '#1A4F7A')])

    def create_titled_frame(self, parent, title):
        container = tk.Frame(parent, bg=self.COLORS['white'], relief='solid', borderwidth=1)

        header = tk.Frame(container, bg=self.COLORS['primary'], height=20)
        header.pack(fill='x')
        header.pack_propagate(False)

        label = tk.Label(header, text=title, font=('Segoe UI', 8, 'bold'),
                        fg=self.COLORS['white'], bg=self.COLORS['primary'])
        label.pack(side='left', padx=10, pady=2)

        content = tk.Frame(container, bg=self.COLORS['white'])
        content.pack(fill='both', expand=True, padx=10, pady=10)

        return container, content
    
    def cargar_iconos(self):
        try:
            icons_path = resource_path(os.path.join("utils", "icons"))
            self.icon_add    = tk.PhotoImage(file=os.path.join(icons_path, "agregar.png")).subsample(2, 2)
            self.icon_edit   = tk.PhotoImage(file=os.path.join(icons_path, "editar.png")).subsample(2, 2)
            self.icon_delete = tk.PhotoImage(file=os.path.join(icons_path, "eliminar.png")).subsample(2, 2)
            self.icon_excel  = tk.PhotoImage(file=os.path.join(icons_path, "excel.png")).subsample(2, 2)
            self.icon_close  = tk.PhotoImage(file=os.path.join(icons_path, "cerrar.png")).subsample(2, 2)
        except Exception as e:
            print(f"Error cargando iconos: {e}")
            self.icon_add = self.icon_edit = self.icon_delete = self.icon_excel = self.icon_close = None
    
    def verificar_base_datos(self):
        try:
            # Crear base de datos y tablas si no existen
            if not crear_base_datos():
                raise Exception("No se pudo crear la base de datos")
            print("Base de datos creada o verificada correctamente")

            # Verificar que las tablas existan
            if not verificar_tablas():
                print("La estructura de la base de datos es incorrecta. Recreándola...")
                # En MySQL no hay archivo local que eliminar, solo recrear tablas
                if not crear_base_datos():
                    raise Exception("No se pudo recrear la base de datos")
                print("Base de datos recreada correctamente")

            return True
        except Exception as e:
            print(f"Error al verificar la base de datos: {e}")
            return False

    def verificar_conexion_db(self):
        try:
            ok = False
            err = None
            try:
                ok, err = verificar_conexion(return_error=True)
            except TypeError:
                ok = verificar_conexion()
            if ok:
                return True
            if err:
                messagebox.showerror("Error de conexión", f"No se pudo conectar a MySQL.\nDetalle: {err}")
            return False
        except Exception as e:
            messagebox.showerror("Error de conexión", f"Fallo al verificar la conexión.\nDetalle: {e}")
            return False

    # --- Utilidades ---

    def centrar_ventana(self, ventana):
        ventana.update_idletasks()
        width = ventana.winfo_width()
        height = ventana.winfo_height()
        x = (ventana.winfo_screenwidth() // 2) - (width // 2)
        y = (ventana.winfo_screenheight() // 2) - (height // 2)
        ventana.geometry(f'{width}x{height}+{x}+{y}')

    def obtener_id_tipo_insumo(self, descripcion):
        tipos = obtener_tipos_insumo()
        for tipo in tipos:
            if tipo['descripcion'] == descripcion:
                return tipo['id']
        return None

    def obtener_id_presentacion(self, nombre):
        presentaciones = obtener_presentaciones()
        for pres in presentaciones:
            if pres['nombre'] == nombre:
                return pres['id']
        return None

    def obtener_id_insumo(self, nombre_insumo, id_tipo_insumo):
        insumos = obtener_insumos_por_tipo(id_tipo_insumo)
        for insumo in insumos:
            if insumo['nombre'] == nombre_insumo:
                return insumo['id']
        return None

    # --- Configuración UI ---

    def setup_ui(self):
        
        # Título principal con estilo
        title_frame = tk.Frame(self.parent, bg=self.COLORS['primary'], height=50)
        title_frame.pack(fill='x', padx=10, pady=(10, 5))
        title_frame.pack_propagate(False)

        tk.Label(title_frame, text="Gestión de Insumos del Sistema",
                font=('Segoe UI', 16, 'bold'),
                fg=self.COLORS['white'],
                bg=self.COLORS['primary']).pack(anchor='w', padx=10, pady=10)

        tk.Label(title_frame, text="Administre los insumos",
                font=('Segoe UI', 10),
                fg=self.COLORS['white'],
                bg=self.COLORS['primary']).pack(anchor='w', padx=10)

        # Separador con color gris claro
        sep = ttk.Separator(self.parent, orient='horizontal')
        sep.pack(fill='x', padx=10, pady=5)

        self.notebook = ttk.Notebook(self.parent)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        self.tab_tipos = ttk.Frame(self.notebook)
        self.tab_insumos = ttk.Frame(self.notebook)
        self.tab_presentaciones = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_tipos, text="Tipos de Insumo")
        self.notebook.add(self.tab_insumos, text="Insumos")
        self.notebook.add(self.tab_presentaciones, text="Presentaciones")

        self.setup_tipos_tab()
        self.setup_insumos_tab()
        self.setup_presentaciones_tab()

        # Botón cerrar con estilo
        btn_close = tk.Button(self.parent,
                            text="Cerrar",
                            command=self.cerrar_ventana,
                            font=('Segoe UI', 10, 'bold'),
                            bg=self.COLORS['white'],
                            fg=self.COLORS['text_dark'],
                            relief='flat',
                            borderwidth=0,
                            padx=15, pady=6,
                            cursor='hand2')
        btn_close.pack(pady=10, padx=10, anchor='e')

        self.actualizar_tipos()
        self.actualizar_insumos()
        self.actualizar_presentaciones()

    # --- Tipos de Insumo ---

    def setup_tipos_tab(self):
        # Usar create_titled_frame para "Carga desde Excel"
        frame_excel_container, frame_excel = self.create_titled_frame(self.tab_tipos, "Carga desde Excel")
        frame_excel_container.pack(fill="x", padx=5, pady=5)

        btn_cargar = tk.Button(frame_excel, text="Cargar Excel", command=self.cargar_excel_tipos,
                            font=('Segoe UI', 9),
                            bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                            relief='flat', borderwidth=1, padx=10, pady=5, cursor='hand2')
        btn_cargar.pack(side="left", padx=5, pady=5)

        btn_exportar = tk.Button(frame_excel, text="Exportar a Excel", command=self.exportar_excel_tipos,
                                font=('Segoe UI', 9),
                                bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                                relief='flat', borderwidth=1, padx=10, pady=5, cursor='hand2')
        btn_exportar.pack(side="left", padx=5, pady=5)

        # Usar create_titled_frame para "Tipos de Insumo"
        frame_lista_container, frame_lista = self.create_titled_frame(self.tab_tipos, "Tipos de Insumo")
        frame_lista_container.pack(fill="both", expand=True, padx=5, pady=5)

        self.tree_tipos = ttk.Treeview(frame_lista, columns=('descripcion',), show='headings')
        self.tree_tipos.heading('descripcion', text='Tipo Insumo')
        self.tree_tipos.pack(fill='both', expand=True, side='left', padx=(0,5), pady=5)

        scrolly = ttk.Scrollbar(frame_lista, orient="vertical", command=self.tree_tipos.yview)
        self.tree_tipos.configure(yscrollcommand=scrolly.set)
        scrolly.pack(side='left', fill='y', pady=5)

        frame_botones = tk.Frame(frame_lista, bg=self.COLORS['white'])
        frame_botones.pack(side='left', fill='y', padx=5, pady=5)

        btn_agregar = tk.Button(frame_botones, text="Agregar", command=self.agregar_tipo,
                            font=('Segoe UI', 9),
                            bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                            relief='flat', borderwidth=1, padx=10, pady=6, cursor='hand2')
        btn_agregar.pack(fill='x', pady=3)

        btn_editar = tk.Button(frame_botones, text="Editar", command=self.editar_tipo,
                            font=('Segoe UI', 9),
                            bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                            relief='flat', borderwidth=1, padx=10, pady=6, cursor='hand2')
        btn_editar.pack(fill='x', pady=3)

        btn_eliminar = tk.Button(frame_botones, text="Eliminar", command=self.eliminar_tipo,
                                font=('Segoe UI', 9),
                                bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                                relief='flat', borderwidth=1, padx=10, pady=6, cursor='hand2')
        btn_eliminar.pack(fill='x', pady=3)

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
                if tipo:
                    try:
                        agregar_tipo_insumo(tipo)
                    except Exception:
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
        ventana = tk.Toplevel(self.parent)
        ventana.title("Agregar Tipo de Insumo")
        ventana.geometry("350x120")
        self.centrar_ventana(ventana)

        ttk.Label(ventana, text="Descripción:").pack(pady=5)
        descripcion = ttk.Entry(ventana, width=40)
        descripcion.pack(pady=5)

        def guardar():
            desc = descripcion.get().strip()
            if not desc:
                messagebox.showwarning("Advertencia", "Ingrese una descripción")
                return
            if self.obtener_id_tipo_insumo(desc):
                messagebox.showerror("Error", "Ya existe un tipo de insumo con esa descripción")
                return
            agregar_tipo_insumo(desc)
            self.actualizar_tipos()
            ventana.destroy()
            messagebox.showinfo("Éxito", "Tipo de insumo agregado correctamente")

        frame_botones = ttk.Frame(ventana)
        frame_botones.pack(pady=10)
        ttk.Button(frame_botones, text="Guardar", command=guardar).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Cerrar", command=ventana.destroy).pack(side="left", padx=5)

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
            nuevo_desc = nuevo_nombre.get().strip()
            if not nuevo_desc:
                messagebox.showwarning("Advertencia", "Ingrese una descripción")
                return
            id_tipo = self.obtener_id_tipo_insumo(item['values'][0])
            if id_tipo is None:
                messagebox.showerror("Error", "Tipo de insumo no encontrado")
                return
            id_existente = self.obtener_id_tipo_insumo(nuevo_desc)
            if id_existente and id_existente != id_tipo:
                messagebox.showerror("Error", "Ya existe un tipo de insumo con esa descripción")
                return
            actualizar_tipo_insumo(id_tipo, nuevo_desc)
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
            if id_tipo:
                eliminado = eliminar_tipo_insumo(id_tipo)
                if eliminado:
                    self.actualizar_tipos()
                    messagebox.showinfo("Éxito", "Tipo de insumo eliminado correctamente")
                else:
                    messagebox.showerror("Error", "No se pudo eliminar el tipo de insumo. Puede tener insumos asociados.")
            else:
                messagebox.showerror("Error", "Tipo de insumo no encontrado")

    def actualizar_tipos(self):
        self.tree_tipos.delete(*self.tree_tipos.get_children())
        tipos = obtener_tipos_insumo()
        for tipo in tipos:
            self.tree_tipos.insert('', 'end', values=(tipo['descripcion'],))

    # --- Insumos ---

    def setup_insumos_tab(self):
        frame_excel_container, frame_excel = self.create_titled_frame(self.tab_insumos, "Carga desde Excel")
        frame_excel_container.pack(fill="x", padx=5, pady=5)

        btn_cargar = tk.Button(frame_excel, text="Cargar Excel", command=self.cargar_excel_insumos,
                            font=('Segoe UI', 9),
                            bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                            relief='flat', borderwidth=1, padx=10, pady=5, cursor='hand2')
        btn_cargar.pack(side="left", padx=5, pady=5)

        btn_exportar = tk.Button(frame_excel, text="Exportar a Excel", command=self.exportar_excel_insumos,
                                font=('Segoe UI', 9),
                                bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                                relief='flat', borderwidth=1, padx=10, pady=5, cursor='hand2')
        btn_exportar.pack(side="left", padx=5, pady=5)

        frame_lista_container, frame_lista = self.create_titled_frame(self.tab_insumos, "Insumos")
        frame_lista_container.pack(fill="both", expand=True, padx=5, pady=5)

        self.tree_insumos = ttk.Treeview(frame_lista, columns=('tipo', 'nombre'), show='headings')
        self.tree_insumos.heading('tipo', text='Tipo de Insumo')
        self.tree_insumos.heading('nombre', text='Insumo')
        self.tree_insumos.pack(fill='both', expand=True, side='left', padx=(0,5), pady=5)

        scrolly = ttk.Scrollbar(frame_lista, orient="vertical", command=self.tree_insumos.yview)
        self.tree_insumos.configure(yscrollcommand=scrolly.set)
        scrolly.pack(side='left', fill='y', pady=5)

        frame_botones = tk.Frame(frame_lista, bg=self.COLORS['white'])
        frame_botones.pack(side='left', fill='y', padx=5, pady=5)

        btn_agregar = tk.Button(frame_botones, text="Agregar", command=self.agregar_insumo,
                            font=('Segoe UI', 9),
                            bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                            relief='flat', borderwidth=1, padx=10, pady=6, cursor='hand2')
        btn_agregar.pack(fill='x', pady=3)

        btn_editar = tk.Button(frame_botones, text="Editar", command=self.editar_insumo,
                            font=('Segoe UI', 9),
                            bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                            relief='flat', borderwidth=1, padx=10, pady=6, cursor='hand2')
        btn_editar.pack(fill='x', pady=3)

        btn_eliminar = tk.Button(frame_botones, text="Eliminar", command=self.eliminar_insumo,
                                font=('Segoe UI', 9),
                                bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                                relief='flat', borderwidth=1, padx=10, pady=6, cursor='hand2')
        btn_eliminar.pack(fill='x', pady=3)

    def cargar_excel_insumos(self):
        filename = filedialog.askopenfilename(title="Seleccionar archivo Excel", filetypes=[("Excel files", "*.xlsx *.xls")])
        if not filename:
            return
        try:
            df = pd.read_excel(filename)
            columnas_requeridas = ['Tipo de Insumo', 'Insumo', 'Presentación']
            faltantes = [col for col in columnas_requeridas if col not in df.columns]
            if faltantes:
                messagebox.showerror("Error", f"Faltan las columnas: {', '.join(faltantes)}")
                return

            registros_procesados = 0
            errores = []

            for idx, row in df.iterrows():
                try:
                    tipo = str(row['Tipo de Insumo']).strip()
                    insumo = str(row['Insumo']).strip()
                    presentacion = str(row['Presentación']).strip()
                    if not (tipo and insumo and presentacion):
                        continue

                    id_tipo = self.obtener_id_tipo_insumo(tipo)
                    if not id_tipo:
                        id_tipo = agregar_tipo_insumo(tipo)

                    id_presentacion = self.obtener_id_presentacion(presentacion)
                    if not id_presentacion:
                        id_presentacion = agregar_presentacion(presentacion)

                    agregar_insumo(insumo, None, id_presentacion, None, id_tipo)
                    registros_procesados += 1
                except Exception as e:
                    errores.append(f"Fila {idx + 2}: {str(e)}")

            self.actualizar_insumos()
            self.actualizar_presentaciones()

            if errores:
                mensaje = f"Se procesaron {registros_procesados} registros con {len(errores)} errores.\n"
                mensaje += "\n".join(errores[:5])
                if len(errores) > 5:
                    mensaje += f"\n... y {len(errores) - 5} errores más."
                messagebox.showwarning("Advertencia", mensaje)
            else:
                messagebox.showinfo("Éxito", f"Se procesaron {registros_procesados} registros correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar el archivo: {str(e)}")

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
        ventana.geometry("350x190")
        self.centrar_ventana(ventana)

        frame_campos = ttk.Frame(ventana)
        frame_campos.pack(padx=10, pady=5, fill='x')

        ttk.Label(frame_campos, text="Tipo de Insumo:").pack(pady=5)
        combo_tipo = ttk.Combobox(frame_campos, state="readonly")
        tipos = obtener_tipos_insumo()
        combo_tipo['values'] = [t['descripcion'] for t in tipos]
        combo_tipo.pack(pady=5, fill='x')

        ttk.Label(frame_campos, text="Nombre del Insumo:").pack(pady=5)
        nombre = ttk.Entry(frame_campos)
        nombre.pack(pady=5, fill='x')

        def guardar():
            if not combo_tipo.get():
                messagebox.showwarning("Advertencia", "Seleccione un tipo de insumo")
                return
            if not nombre.get().strip():
                messagebox.showwarning("Advertencia", "Ingrese un nombre para el insumo")
                return

            id_tipo = self.obtener_id_tipo_insumo(combo_tipo.get())
            id_presentacion = self.obtener_id_presentacion("Sin Presentación")
            if not id_presentacion:
                id_presentacion = agregar_presentacion("Sin Presentación")

            if obtener_insumo_por_nombre(nombre.get().strip(), id_tipo):
                messagebox.showerror("Error", "Ya existe un insumo con ese nombre para el tipo seleccionado")
                return

            agregar_insumo(nombre.get().strip(), None, id_presentacion, None, id_tipo)
            self.actualizar_insumos()
            ventana.destroy()
            messagebox.showinfo("Éxito", "Insumo agregado correctamente")

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
        ventana.geometry("350x250")
        self.centrar_ventana(ventana)

        frame_campos = ttk.Frame(ventana)
        frame_campos.pack(padx=10, pady=5, fill='x')

        ttk.Label(frame_campos, text="Tipo de Insumo:").pack(pady=5)
        combo_tipo = ttk.Combobox(frame_campos, state="readonly")
        tipos = obtener_tipos_insumo()
        combo_tipo['values'] = [t['descripcion'] for t in tipos]
        combo_tipo.set(item['values'][0])
        combo_tipo.pack(pady=5, fill='x')

        ttk.Label(frame_campos, text="Nombre:").pack(pady=5)
        nombre = ttk.Entry(frame_campos)
        nombre.insert(0, item['values'][1])
        nombre.pack(pady=5, fill='x')

        ttk.Label(frame_campos, text="Presentación (opcional):").pack(pady=5)
        combo_presentacion = ttk.Combobox(frame_campos, state="readonly")
        presentaciones = obtener_presentaciones()
        combo_presentacion['values'] = [p['nombre'] for p in presentaciones]
        combo_presentacion.pack(pady=5, fill='x')

        id_tipo = self.obtener_id_tipo_insumo(item['values'][0])
        id_insumo = self.obtener_id_insumo(item['values'][1], id_tipo)
        insumo_data = obtener_insumo_por_id(id_insumo)
        if insumo_data and insumo_data['nombre_presentacion']:
            combo_presentacion.set(insumo_data['nombre_presentacion'])

        def guardar():
            if not combo_tipo.get() or not nombre.get().strip():
                messagebox.showwarning("Advertencia", "Complete todos los campos")
                return

            id_tipo = self.obtener_id_tipo_insumo(combo_tipo.get())
            id_presentacion = self.obtener_id_presentacion(combo_presentacion.get()) if combo_presentacion.get() else None

            insumo_existente = obtener_insumo_por_nombre(nombre.get().strip(), id_tipo)
            if insumo_existente and insumo_existente['id'] != id_insumo:
                messagebox.showerror("Error", "Ya existe un insumo con ese nombre para el tipo seleccionado")
                return

            actualizar_insumo(id_insumo, nombre.get().strip(), None, id_presentacion, None, id_tipo)
            self.actualizar_insumos()
            ventana.destroy()
            messagebox.showinfo("Éxito", "Insumo actualizado correctamente")

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
            if id_insumo:
                eliminado = eliminar_insumo(id_insumo)
                if eliminado:
                    self.actualizar_insumos()
                    messagebox.showinfo("Éxito", "Insumo eliminado correctamente")
                else:
                    messagebox.showerror("Error", "No se pudo eliminar el insumo. Puede estar asociado a otros registros.")
            else:
                messagebox.showerror("Error", "Insumo no encontrado")

    def actualizar_insumos(self):
        self.tree_insumos.delete(*self.tree_insumos.get_children())
        tipos = obtener_tipos_insumo()
        for tipo in tipos:
            insumos = obtener_insumos_por_tipo(tipo['id'])
            for insumo in insumos:
                self.tree_insumos.insert('', 'end', values=(tipo['descripcion'], insumo['nombre']))

    # --- Presentaciones ---

    def setup_presentaciones_tab(self):
        frame_excel_container, frame_excel = self.create_titled_frame(self.tab_presentaciones, "Carga desde Excel")
        frame_excel_container.pack(fill="x", padx=5, pady=5)

        btn_cargar = tk.Button(frame_excel, text="Cargar Excel", command=self.cargar_excel_presentaciones,
                            font=('Segoe UI', 9),
                            bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                            relief='flat', borderwidth=1, padx=10, pady=5, cursor='hand2')
        btn_cargar.pack(side="left", padx=5, pady=5)

        btn_exportar = tk.Button(frame_excel, text="Exportar a Excel", command=self.exportar_excel_presentaciones,
                                font=('Segoe UI', 9),
                                bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                                relief='flat', borderwidth=1, padx=10, pady=5, cursor='hand2')
        btn_exportar.pack(side="left", padx=5, pady=5)

        frame_lista_container, frame_lista = self.create_titled_frame(self.tab_presentaciones, "Presentaciones")
        frame_lista_container.pack(fill="both", expand=True, padx=5, pady=5)

        self.tree_presentaciones = ttk.Treeview(frame_lista,
            columns=('tipo', 'insumo', 'presentacion'), show='headings')
        self.tree_presentaciones.heading('tipo', text='Tipo de Insumo')
        self.tree_presentaciones.heading('insumo', text='Insumo')
        self.tree_presentaciones.heading('presentacion', text='Presentación')
        self.tree_presentaciones.pack(fill='both', expand=True, side='left', padx=(0,5), pady=5)

        scrolly = ttk.Scrollbar(frame_lista, orient="vertical", command=self.tree_presentaciones.yview)
        self.tree_presentaciones.configure(yscrollcommand=scrolly.set)
        scrolly.pack(side='left', fill='y', pady=5)

        frame_botones = tk.Frame(frame_lista, bg=self.COLORS['white'])
        frame_botones.pack(side='left', fill='y', padx=5, pady=5)

        btn_agregar = tk.Button(frame_botones, text="Agregar", command=self.agregar_presentacion,
                            font=('Segoe UI', 9),
                            bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                            relief='flat', borderwidth=1, padx=10, pady=6, cursor='hand2')
        btn_agregar.pack(fill='x', pady=3)

        btn_editar = tk.Button(frame_botones, text="Editar", command=self.editar_presentacion,
                            font=('Segoe UI', 9),
                            bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                            relief='flat', borderwidth=1, padx=10, pady=6, cursor='hand2')
        btn_editar.pack(fill='x', pady=3)

        btn_eliminar = tk.Button(frame_botones, text="Eliminar", command=self.eliminar_presentacion,
                                font=('Segoe UI', 9),
                                bg=self.COLORS['white'], fg=self.COLORS['text_dark'],
                                relief='flat', borderwidth=1, padx=10, pady=6, cursor='hand2')
        btn_eliminar.pack(fill='x', pady=3)

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
                if presentacion:
                    try:
                        agregar_presentacion(presentacion)
                    except Exception:
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

        ttk.Label(frame_campos, text="Tipo de Insumo:").pack(pady=5)
        combo_tipo = ttk.Combobox(frame_campos, state="readonly")
        tipos = obtener_tipos_insumo()
        combo_tipo['values'] = [t['descripcion'] for t in tipos]
        combo_tipo.pack(pady=5, fill='x')

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

        ttk.Label(frame_campos, text="Descripción de Presentación:").pack(pady=5)
        nombre = ttk.Entry(frame_campos)
        nombre.pack(pady=5, fill='x')

        def guardar():
            if not combo_tipo.get() or not combo_insumo.get() or not nombre.get().strip():
                messagebox.showwarning("Advertencia", "Complete todos los campos")
                return

            id_tipo = self.obtener_id_tipo_insumo(combo_tipo.get())
            id_insumo = self.obtener_id_insumo(combo_insumo.get(), id_tipo)

            id_presentacion = self.obtener_id_presentacion(nombre.get().strip())
            if not id_presentacion:
                id_presentacion = agregar_presentacion(nombre.get().strip())

            actualizar_insumo(id_insumo, combo_insumo.get(), None, id_presentacion, None, id_tipo)
            self.actualizar_presentaciones()
            ventana.destroy()
            messagebox.showinfo("Éxito", "Presentación agregada correctamente")

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

        ttk.Label(frame_campos, text="Tipo de Insumo:").pack(pady=5)
        combo_tipo = ttk.Combobox(frame_campos, state="readonly")
        tipos = obtener_tipos_insumo()
        combo_tipo['values'] = [t['descripcion'] for t in tipos]
        combo_tipo.set(item['values'][0])
        combo_tipo.pack(pady=5, fill='x')

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

        actualizar_insumos()
        combo_insumo.set(item['values'][1])

        ttk.Label(frame_campos, text="Presentación:").pack(pady=5)
        nuevo_nombre = ttk.Entry(frame_campos)
        nuevo_nombre.insert(0, item['values'][2])
        nuevo_nombre.pack(pady=5, fill='x')

        def guardar():
            if not all([combo_tipo.get(), combo_insumo.get(), nuevo_nombre.get().strip()]):
                messagebox.showwarning("Advertencia", "Complete todos los campos")
                return

            id_tipo = self.obtener_id_tipo_insumo(combo_tipo.get())
            id_insumo = self.obtener_id_insumo(combo_insumo.get(), id_tipo)
            id_presentacion_actual = self.obtener_id_presentacion(item['values'][2])

            if nuevo_nombre.get().strip() != item['values'][2]:
                actualizar_presentacion(id_presentacion_actual, nuevo_nombre.get().strip())
                id_presentacion = id_presentacion_actual
            else:
                id_presentacion = id_presentacion_actual

            actualizar_insumo(id_insumo, combo_insumo.get(), None, id_presentacion, None, id_tipo)
            self.actualizar_presentaciones()
            ventana.destroy()
            messagebox.showinfo("Éxito", "Presentación actualizada correctamente")

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
            id_pres = self.obtener_id_presentacion(item['values'][2])
            if id_pres:
                eliminado = eliminar_presentacion(id_pres)
                if eliminado:
                    self.actualizar_presentaciones()
                    messagebox.showinfo("Éxito", "Presentación eliminada correctamente")
                else:
                    messagebox.showerror("Error", "No se pudo eliminar la presentación. Puede tener insumos asociados.")
            else:
                messagebox.showerror("Error", "No se encontró la presentación seleccionada")

    def actualizar_presentaciones(self):
        self.tree_presentaciones.delete(*self.tree_presentaciones.get_children())
        tipos = obtener_tipos_insumo()
        for tipo in tipos:
            insumos = obtener_insumos_por_tipo(tipo['id'])
            for insumo in insumos:
                presentacion = insumo['nombre_presentacion'] if insumo['nombre_presentacion'] else 'N/A'
                nombre_insumo = insumo['nombre']
                self.tree_presentaciones.insert('', 'end', values=(tipo['descripcion'], nombre_insumo, presentacion))

    # --- Cierre ---

    def cerrar_ventana(self):
        if messagebox.askyesno("Confirmar", "¿Está seguro que desea cerrar esta ventana?"):
            for widget in self.parent.winfo_children():
                widget.destroy()
            if hasattr(self.main_window, 'show_welcome_screen'):
                self.main_window.show_welcome_screen()
            else:
                self.parent.destroy()