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
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


# ================= Estilos unificados (igual a otros módulos) =================
def setup_styles(root):
    COLORS = {
        'primary':   '#2c3e50',
        'secondary': '#34495e',
        'accent':    '#3498db',
        'success':   '#27ae60',
        'warning':   '#f39c12',
        'danger':    '#e74c3c',
        'light':     '#ecf0f1',
        'white':     '#ffffff',
        'text_dark': '#2c3e50',
        'text_light':'#7f8c8d',
        'border':    '#d1d5db'
    }

    style = ttk.Style(root)
    try:
        style.theme_use('clam')
    except Exception:
        pass

    try:
        root.configure(bg=COLORS['light'])
    except Exception:
        pass

    style.configure('.', font=('Segoe UI', 9))

    # Frames
    style.configure('Light.TFrame', background=COLORS['light'])
    style.configure('Card.TFrame', background=COLORS['white'], relief='solid', borderwidth=1)

    # Header de card
    style.configure('Header.TFrame', background=COLORS['primary'])
    style.configure('Header.TLabel', background=COLORS['primary'], foreground=COLORS['white'], font=('Segoe UI', 10, 'bold'))

    # Labels
    style.configure('Light.TLabel', background=COLORS['light'], foreground=COLORS['text_dark'], font=('Segoe UI', 9))
    style.configure('Card.TLabel', background=COLORS['white'], foreground=COLORS['text_dark'], font=('Segoe UI', 9))

    # Botón primario
    style.configure('Primary.TButton',
                    font=('Segoe UI', 9, 'bold'),
                    padding=(10, 5),
                    relief='flat',
                    borderwidth=0,
                    background=COLORS['accent'],
                    foreground=COLORS['white'])
    style.map('Primary.TButton',
              background=[('active', '#2980b9'), ('pressed', '#117a8b')],
              foreground=[('active', '#ffffff'), ('pressed', '#ffffff')])

    # Entry/Combobox
    style.configure('TCombobox',
                    fieldbackground=COLORS['white'],
                    background=COLORS['white'],
                    foreground=COLORS['text_dark'])
    style.configure('TEntry',
                    fieldbackground=COLORS['white'],
                    foreground=COLORS['text_dark'])

    root.option_add('*TCombobox*Listbox.background', COLORS['white'])
    root.option_add('*TCombobox*Listbox.foreground', COLORS['text_dark'])
    root.option_add('*TCombobox*Listbox.selectBackground', COLORS['accent'])
    root.option_add('*TCombobox*Listbox.selectForeground', COLORS['white'])
    root.option_add('*TCombobox*Listbox.font', '{Segoe UI} 9')

    # Treeview
    style.configure("Custom.Treeview",
                    background=COLORS['white'],
                    foreground=COLORS['text_dark'],
                    rowheight=22,
                    fieldbackground=COLORS['white'],
                    font=('Segoe UI', 9),
                    borderwidth=1,
                    relief='solid')
    HEADER_BG = '#e5e7eb'
    HEADER_FG = '#111827'
    style.configure("Custom.Treeview.Heading",
                    background=HEADER_BG,
                    foreground=HEADER_FG,
                    font=('Segoe UI', 8, 'bold'),
                    relief='flat',
                    borderwidth=1,
                    padding=(3, 6, 3, 6),
                    anchor='center',
                    justify='center')
    style.map("Custom.Treeview",
              background=[('selected', COLORS['accent'])],
              foreground=[('selected', '#ffffff')])

    # Notebook
    style.configure('TNotebook', background=COLORS['light'], borderwidth=0)
    style.configure('TNotebook.Tab',
                    background=COLORS['light'],
                    foreground=COLORS['text_dark'],
                    font=('Segoe UI', 9))
    style.map('TNotebook.Tab',
              background=[('selected', COLORS['white'])],
              foreground=[('selected', COLORS['text_dark'])])

    return COLORS, style


class GestionInsumos:
    def __init__(self, parent_frame, main_window):
        self.parent = parent_frame
        self.main_window = main_window

        # Estilos/paleta
        self.COLORS, self._style = setup_styles(self.parent.winfo_toplevel())

        if not self.verificar_base_datos():
            messagebox.showerror("Error", "Error en la base de datos. La aplicación no puede continuar.")
            self.cerrar_ventana()
            return

        if not self.verificar_conexion_db():
            messagebox.showerror("Error", "No se pudo conectar a la base de datos")
            self.cerrar_ventana()
            return

        self.setup_ui()

        # Aplicar estilo si parent es ttk
        if isinstance(self.parent, ttk.Widget):
            self.parent.configure(style='Light.TFrame')

    # ---------- Utilería de UI (header/cards) ----------
    def _header_title_sub(self, parent, title_text, subtitle_text):
        header_frame = tk.Frame(parent, bg=self.COLORS['primary'], height=55)
        header_frame.pack(fill='x', padx=10, pady=(10, 6))
        header_frame.pack_propagate(False)

        header_inner = tk.Frame(header_frame, bg=self.COLORS['primary'])
        header_inner.pack(fill='both', expand=True, padx=10, pady=4)

        tk.Label(header_inner, text=title_text,
                 font=('Segoe UI', 12, 'bold'),
                 fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(anchor='w')
        tk.Label(header_inner, text=subtitle_text,
                 font=('Segoe UI', 9),
                 fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(anchor='w', pady=(1, 0))

    def _card_section(self, parent, title, icon):
        container = ttk.Frame(parent, style='Light.TFrame')
        container.pack(fill='x', padx=10, pady=6)

        card = ttk.Frame(container, style='Card.TFrame')
        card.pack(fill='both', expand=True)

        header = ttk.Frame(card, style='Header.TFrame', height=24)
        header.pack(fill='x')
        header.pack_propagate(False)

        ttk.Label(header, text=f"{icon} {title}", style='Header.TLabel').pack(side='left', padx=10)

        content = ttk.Frame(card, style='Card.TFrame')
        content.pack(fill='both', expand=True, padx=12, pady=8)

        return content

    # ---------- Verificación DB ----------
    def verificar_base_datos(self):
        try:
            if not crear_base_datos():
                raise Exception("No se pudo crear la base de datos")
            if not verificar_tablas():
                # Si faltan tablas, intentar recrear
                if not crear_base_datos():
                    raise Exception("No se pudo recrear la base de datos")
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
        # fondo parent
        try:
            if isinstance(self.parent, ttk.Widget):
                self.parent.configure(style='Light.TFrame')
            else:
                self.parent.configure(bg=self.COLORS['light'])
        except Exception:
            pass

        # Header principal
        self._header_title_sub(
            self.parent,
            "📦 Gestión de Insumos del Sistema",
            "Administre tipos, insumos y presentaciones"
        )

        # Notebook
        nb_container = ttk.Frame(self.parent, style='Light.TFrame')
        nb_container.pack(fill="both", expand=True, padx=10, pady=5)

        self.notebook = ttk.Notebook(nb_container)
        self.notebook.pack(fill="both", expand=True)

        # Tabs
        self.tab_tipos = ttk.Frame(self.notebook, style='Light.TFrame')
        self.tab_insumos = ttk.Frame(self.notebook, style='Light.TFrame')
        self.tab_presentaciones = ttk.Frame(self.notebook, style='Light.TFrame')

        self.notebook.add(self.tab_tipos, text="📑 Tipos de Insumo")
        self.notebook.add(self.tab_insumos, text="🧾 Insumos")
        self.notebook.add(self.tab_presentaciones, text="🏷️ Presentaciones")

        self.setup_tipos_tab()
        self.setup_insumos_tab()
        self.setup_presentaciones_tab()

        # Botón cerrar
        button_frame = ttk.Frame(self.parent, style='Light.TFrame')
        button_frame.pack(fill='x', pady=10, padx=10)
        ttk.Button(button_frame, text="↩️ Cerrar", style='Primary.TButton',
                   command=self.cerrar_ventana).pack(anchor='e')

        # Cargar datos
        self.actualizar_tipos()
        self.actualizar_insumos()
        self.actualizar_presentaciones()

    # --- Tipos de Insumo ---
    def setup_tipos_tab(self):
        # Carga desde Excel
        frame_excel = self._card_section(self.tab_tipos, "Carga desde Excel", "📥")
        ttk.Button(frame_excel, text="📂 Cargar Excel", style='Primary.TButton',
                   command=self.cargar_excel_tipos).pack(side="left", padx=(0, 8), pady=2)
        ttk.Button(frame_excel, text="📤 Exportar a Excel", style='Primary.TButton',
                   command=self.exportar_excel_tipos).pack(side="left", padx=(0, 8), pady=2)

        # Lista de tipos
        frame_lista = self._card_section(self.tab_tipos, "Tipos de Insumo", "📑")

        table_wrap = ttk.Frame(frame_lista, style='Card.TFrame')
        table_wrap.pack(fill='both', expand=True)

        self.tree_tipos = ttk.Treeview(table_wrap, columns=('descripcion',), show='headings', style="Custom.Treeview")
        self.tree_tipos.heading('descripcion', text='Tipo de Insumo', anchor='w')
        self.tree_tipos.column('descripcion', anchor='w', width=320)
        self.tree_tipos.pack(fill='both', expand=True, side='left', padx=(0, 5), pady=2)

        scrolly = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree_tipos.yview)
        self.tree_tipos.configure(yscrollcommand=scrolly.set)
        scrolly.pack(side='left', fill='y')

        btns = ttk.Frame(frame_lista, style='Card.TFrame')
        btns.pack(fill='x', padx=0, pady=(6, 0))
        ttk.Button(btns, text="➕ Agregar", style='Primary.TButton',
                command=self.agregar_tipo).pack(side='left', padx=(0, 6), pady=0)
        ttk.Button(btns, text="✏️ Editar", style='Primary.TButton',
                command=self.editar_tipo).pack(side='left', padx=(0, 6), pady=0)
        ttk.Button(btns, text="🗑️ Eliminar", style='Primary.TButton',
                command=self.eliminar_tipo).pack(side='left', padx=(0, 0), pady=0)

    def cargar_excel_tipos(self):
        filename = filedialog.askopenfilename(title="Seleccionar archivo Excel",
                                              filetypes=[("Excel files", "*.xlsx *.xls")])
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
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                filetypes=[("Excel files", "*.xlsx")])
        if not filename:
            return
        tipos = obtener_tipos_insumo()
        df = pd.DataFrame([{'Tipo de Insumo': t['descripcion']} for t in tipos])
        df.to_excel(filename, index=False)
        messagebox.showinfo("Éxito", "Tipos de insumo exportados correctamente")

    def agregar_tipo(self):
        ventana = tk.Toplevel(self.parent)
        ventana.title("➕ Agregar Tipo de Insumo")
        self._estilizar_toplevel(ventana)

        container = self._dialog_container(ventana, "➕ Agregar Tipo de Insumo", "Ingrese la descripción del tipo")
        body = container['body']

        ttk.Label(body, text="Descripción:", style='Light.TLabel').pack(pady=(0, 4), anchor='w')
        descripcion = ttk.Entry(body, width=40)
        descripcion.pack(fill='x')

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

        self._dialog_buttons(container['buttons'], guardar, ventana.destroy)

    def editar_tipo(self):
        selected = self.tree_tipos.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un tipo de insumo para editar")
            return
        item = self.tree_tipos.item(selected[0])

        ventana = tk.Toplevel(self.parent)
        ventana.title("✏️ Editar Tipo de Insumo")
        self._estilizar_toplevel(ventana)

        container = self._dialog_container(ventana, "✏️ Editar Tipo de Insumo", "Modifique la descripción")
        body = container['body']

        ttk.Label(body, text="Nuevo nombre:", style='Light.TLabel').pack(pady=(0, 4), anchor='w')
        nuevo_nombre = ttk.Entry(body, width=40)
        nuevo_nombre.insert(0, item['values'][0])
        nuevo_nombre.pack(fill='x')

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

        self._dialog_buttons(container['buttons'], guardar, ventana.destroy)

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
        frame_excel = self._card_section(self.tab_insumos, "Carga desde Excel", "📥")
        ttk.Button(frame_excel, text="📂 Cargar Excel", style='Primary.TButton',
                   command=self.cargar_excel_insumos).pack(side="left", padx=(0, 8), pady=2)
        ttk.Button(frame_excel, text="📤 Exportar a Excel", style='Primary.TButton',
                   command=self.exportar_excel_insumos).pack(side="left", padx=(0, 8), pady=2)

        frame_lista = self._card_section(self.tab_insumos, "Insumos", "🧾")

        table_wrap = ttk.Frame(frame_lista, style='Card.TFrame')
        table_wrap.pack(fill='both', expand=True)

        self.tree_insumos = ttk.Treeview(table_wrap, columns=('tipo', 'nombre'), show='headings', style="Custom.Treeview")
        self.tree_insumos.heading('tipo', text='Tipo de Insumo', anchor='w')
        self.tree_insumos.heading('nombre', text='Insumo', anchor='w')
        self.tree_insumos.column('tipo', width=200, anchor='w')
        self.tree_insumos.column('nombre', width=260, anchor='w')
        self.tree_insumos.pack(fill='both', expand=True, side='left', padx=(0, 5), pady=2)

        scrolly = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree_insumos.yview)
        self.tree_insumos.configure(yscrollcommand=scrolly.set)
        scrolly.pack(side='left', fill='y')

        btns = ttk.Frame(frame_lista, style='Card.TFrame')
        btns.pack(fill='x', padx=0, pady=(6, 0))
        ttk.Button(btns, text="➕ Agregar", style='Primary.TButton',
                command=self.agregar_insumo).pack(side='left', padx=(0, 6), pady=0)
        ttk.Button(btns, text="✏️ Editar", style='Primary.TButton',
                command=self.editar_insumo).pack(side='left', padx=(0, 6), pady=0)
        ttk.Button(btns, text="🗑️ Eliminar", style='Primary.TButton',
                command=self.eliminar_insumo).pack(side='left', padx=(0, 0), pady=0)

    def cargar_excel_insumos(self):
        filename = filedialog.askopenfilename(title="Seleccionar archivo Excel",
                                              filetypes=[("Excel files", "*.xlsx *.xls")])
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
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                filetypes=[("Excel files", "*.xlsx")])
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
        ventana.title("➕ Agregar Insumo")
        self._estilizar_toplevel(ventana)

        container = self._dialog_container(ventana, "➕ Agregar Insumo", "Ingrese los datos del insumo")
        body = container['body']

        ttk.Label(body, text="Tipo de Insumo:", style='Light.TLabel').pack(pady=(0, 4), anchor='w')
        combo_tipo = ttk.Combobox(body, state="readonly")
        tipos = obtener_tipos_insumo()
        combo_tipo['values'] = [t['descripcion'] for t in tipos]
        combo_tipo.pack(fill='x')

        ttk.Label(body, text="Nombre del Insumo:", style='Light.TLabel').pack(pady=(8, 4), anchor='w')
        nombre = ttk.Entry(body)
        nombre.pack(fill='x')

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

        self._dialog_buttons(container['buttons'], guardar, ventana.destroy)

    def editar_insumo(self):
        selected = self.tree_insumos.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un insumo para editar")
            return

        item = self.tree_insumos.item(selected[0])

        ventana = tk.Toplevel(self.parent)
        ventana.title("✏️ Editar Insumo")
        self._estilizar_toplevel(ventana)

        container = self._dialog_container(ventana, "✏️ Editar Insumo", "Modifique los campos necesarios")
        body = container['body']

        ttk.Label(body, text="Tipo de Insumo:", style='Light.TLabel').pack(pady=(0, 4), anchor='w')
        combo_tipo = ttk.Combobox(body, state="readonly")
        tipos = obtener_tipos_insumo()
        combo_tipo['values'] = [t['descripcion'] for t in tipos]
        combo_tipo.set(item['values'][0])
        combo_tipo.pack(fill='x')

        ttk.Label(body, text="Nombre:", style='Light.TLabel').pack(pady=(8, 4), anchor='w')
        nombre = ttk.Entry(body)
        nombre.insert(0, item['values'][1])
        nombre.pack(fill='x')

        ttk.Label(body, text="Presentación (opcional):", style='Light.TLabel').pack(pady=(8, 4), anchor='w')
        combo_presentacion = ttk.Combobox(body, state="readonly")
        presentaciones = obtener_presentaciones()
        combo_presentacion['values'] = [p['nombre'] for p in presentaciones]
        combo_presentacion.pack(fill='x')

        id_tipo = self.obtener_id_tipo_insumo(item['values'][0])
        id_insumo = self.obtener_id_insumo(item['values'][1], id_tipo)
        insumo_data = obtener_insumo_por_id(id_insumo)
        if insumo_data and insumo_data['nombre_presentacion']:
            combo_presentacion.set(insumo_data['nombre_presentacion'])

        def guardar():
            if not combo_tipo.get() or not nombre.get().strip():
                messagebox.showwarning("Advertencia", "Complete todos los campos")
                return

            id_tipo_sel = self.obtener_id_tipo_insumo(combo_tipo.get())
            id_presentacion = self.obtener_id_presentacion(combo_presentacion.get()) if combo_presentacion.get() else None

            insumo_existente = obtener_insumo_por_nombre(nombre.get().strip(), id_tipo_sel)
            if insumo_existente and insumo_existente['id'] != id_insumo:
                messagebox.showerror("Error", "Ya existe un insumo con ese nombre para el tipo seleccionado")
                return

            actualizar_insumo(id_insumo, nombre.get().strip(), None, id_presentacion, None, id_tipo_sel)
            self.actualizar_insumos()
            ventana.destroy()
            messagebox.showinfo("Éxito", "Insumo actualizado correctamente")

        self._dialog_buttons(container['buttons'], guardar, ventana.destroy)

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
        frame_excel = self._card_section(self.tab_presentaciones, "Carga desde Excel", "📥")
        ttk.Button(frame_excel, text="📂 Cargar Excel", style='Primary.TButton',
                   command=self.cargar_excel_presentaciones).pack(side="left", padx=(0, 8), pady=2)
        ttk.Button(frame_excel, text="📤 Exportar a Excel", style='Primary.TButton',
                   command=self.exportar_excel_presentaciones).pack(side="left", padx=(0, 8), pady=2)

        frame_lista = self._card_section(self.tab_presentaciones, "Presentaciones", "🏷️")

        table_wrap = ttk.Frame(frame_lista, style='Card.TFrame')
        table_wrap.pack(fill='both', expand=True)

        self.tree_presentaciones = ttk.Treeview(
            table_wrap,
            columns=('tipo', 'insumo', 'presentacion'),
            show='headings',
            style="Custom.Treeview"
        )
        self.tree_presentaciones.heading('tipo', text='Tipo de Insumo', anchor='w')
        self.tree_presentaciones.heading('insumo', text='Insumo', anchor='w')
        self.tree_presentaciones.heading('presentacion', text='Presentación', anchor='w')
        self.tree_presentaciones.column('tipo', width=200, anchor='w')
        self.tree_presentaciones.column('insumo', width=220, anchor='w')
        self.tree_presentaciones.column('presentacion', width=200, anchor='w')
        self.tree_presentaciones.pack(fill='both', expand=True, side='left', padx=(0, 5), pady=2)

        scrolly = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree_presentaciones.yview)
        self.tree_presentaciones.configure(yscrollcommand=scrolly.set)
        scrolly.pack(side='left', fill='y')

        btns = ttk.Frame(frame_lista, style='Card.TFrame')
        btns.pack(fill='x', padx=0, pady=(6, 0))
        ttk.Button(btns, text="➕ Agregar", style='Primary.TButton',
                command=self.agregar_presentacion).pack(side='left', padx=(0, 6), pady=0)
        ttk.Button(btns, text="✏️ Editar", style='Primary.TButton',
                command=self.editar_presentacion).pack(side='left', padx=(0, 6), pady=0)
        ttk.Button(btns, text="🗑️ Eliminar", style='Primary.TButton',
                command=self.eliminar_presentacion).pack(side='left', padx=(0, 0), pady=0)

    def cargar_excel_presentaciones(self):
        filename = filedialog.askopenfilename(title="Seleccionar archivo Excel",
                                              filetypes=[("Excel files", "*.xlsx *.xls")])
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
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                filetypes=[("Excel files", "*.xlsx")])
        if not filename:
            return
        presentaciones = obtener_presentaciones()
        df = pd.DataFrame([{'Presentación': p['nombre']} for p in presentaciones])
        df.to_excel(filename, index=False)
        messagebox.showinfo("Éxito", "Presentaciones exportadas correctamente")

    def agregar_presentacion(self):
        ventana = tk.Toplevel(self.parent)
        ventana.title("➕ Agregar Presentación")
        self._estilizar_toplevel(ventana)

        container = self._dialog_container(ventana, "➕ Agregar Presentación", "Complete los campos")
        body = container['body']

        ttk.Label(body, text="Tipo de Insumo:", style='Light.TLabel').pack(pady=(0, 4), anchor='w')
        combo_tipo = ttk.Combobox(body, state="readonly")
        tipos = obtener_tipos_insumo()
        combo_tipo['values'] = [t['descripcion'] for t in tipos]
        combo_tipo.pack(fill='x')

        ttk.Label(body, text="Insumo:", style='Light.TLabel').pack(pady=(8, 4), anchor='w')
        combo_insumo = ttk.Combobox(body, state="readonly")
        combo_insumo.pack(fill='x')

        def actualizar_insumos(*args):
            combo_insumo['values'] = []
            if combo_tipo.get():
                id_tipo = self.obtener_id_tipo_insumo(combo_tipo.get())
                insumos = obtener_insumos_por_tipo(id_tipo)
                combo_insumo['values'] = [i['nombre'] for i in insumos]

        combo_tipo.bind('<<ComboboxSelected>>', actualizar_insumos)

        ttk.Label(body, text="Descripción de Presentación:", style='Light.TLabel').pack(pady=(8, 4), anchor='w')
        nombre = ttk.Entry(body)
        nombre.pack(fill='x')

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

        self._dialog_buttons(container['buttons'], guardar, ventana.destroy)

    def editar_presentacion(self):
        selected = self.tree_presentaciones.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione una presentación para editar")
            return

        item = self.tree_presentaciones.item(selected[0])

        ventana = tk.Toplevel(self.parent)
        ventana.title("✏️ Editar Presentación")
        self._estilizar_toplevel(ventana)

        container = self._dialog_container(ventana, "✏️ Editar Presentación", "Actualice los datos necesarios")
        body = container['body']

        ttk.Label(body, text="Tipo de Insumo:", style='Light.TLabel').pack(pady=(0, 4), anchor='w')
        combo_tipo = ttk.Combobox(body, state="readonly")
        tipos = obtener_tipos_insumo()
        combo_tipo['values'] = [t['descripcion'] for t in tipos]
        combo_tipo.set(item['values'][0])
        combo_tipo.pack(fill='x')

        ttk.Label(body, text="Insumo:", style='Light.TLabel').pack(pady=(8, 4), anchor='w')
        combo_insumo = ttk.Combobox(body, state="readonly")
        combo_insumo.pack(fill='x')

        def actualizar_insumos(*args):
            combo_insumo['values'] = []
            if combo_tipo.get():
                id_tipo = self.obtener_id_tipo_insumo(combo_tipo.get())
                insumos = obtener_insumos_por_tipo(id_tipo)
                combo_insumo['values'] = [i['nombre'] for i in insumos]

        combo_tipo.bind('<<ComboboxSelected>>', actualizar_insumos)
        actualizar_insumos()
        combo_insumo.set(item['values'][1])

        ttk.Label(body, text="Presentación:", style='Light.TLabel').pack(pady=(8, 4), anchor='w')
        nuevo_nombre = ttk.Entry(body)
        nuevo_nombre.insert(0, item['values'][2])
        nuevo_nombre.pack(fill='x')

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

        self._dialog_buttons(container['buttons'], guardar, ventana.destroy)

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

    # --- Diálogos y Toplevel estilizados ---
    def _estilizar_toplevel(self, ventana):
        try:
            ventana.configure(bg=self.COLORS['light'])
        except Exception:
            pass
        ventana.geometry("420x260")
        self.centrar_ventana(ventana)

    def _dialog_container(self, ventana, title_text, subtitle_text):
        outer = ttk.Frame(ventana, style='Light.TFrame', padding=(10, 10))
        outer.pack(fill='both', expand=True)

        header = tk.Frame(outer, bg=self.COLORS['primary'])
        header.pack(fill='x', pady=(0, 8))
        tk.Label(header, text=title_text, font=('Segoe UI', 10, 'bold'),
                 fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(side='left', padx=10, pady=4)
        tk.Label(header, text=subtitle_text, font=('Segoe UI', 8),
                 fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(side='left', padx=10)

        body = ttk.Frame(outer, style='Light.TFrame')
        body.pack(fill='both', expand=True)

        buttons = ttk.Frame(outer, style='Light.TFrame')
        buttons.pack(fill='x', pady=(8, 0), anchor='e')

        return {'outer': outer, 'body': body, 'buttons': buttons}

    def _dialog_buttons(self, container_buttons, on_accept, on_cancel):
        ttk.Button(container_buttons, text="✔️ Aceptar", style='Primary.TButton',
                   command=on_accept).pack(side='right', padx=6)
        ttk.Button(container_buttons, text="✖️ Cancelar", style='Primary.TButton',
                   command=on_cancel).pack(side='right', padx=6)

    # --- Cierre ---
    def cerrar_ventana(self):
        if messagebox.askyesno("Confirmar", "¿Está seguro que desea cerrar esta ventana?"):
            for widget in self.parent.winfo_children():
                widget.destroy()
            if hasattr(self.main_window, 'show_welcome_screen'):
                self.main_window.show_welcome_screen()
            else:
                try:
                    self.parent.destroy()
                except Exception:
                    pass