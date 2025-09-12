import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import sys
import os

# Agregar el directorio raíz del proyecto al PATH de Python
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from src.database.db_manager import (
    agregar_area,
    obtener_areas,
    actualizar_area,
    eliminar_area,
    obtener_distritos,
    obtener_distritos_por_area,
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

# ================= Estilos unificados =================
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
    # Card exterior con borde fino
    style.configure('Card.TFrame', background=COLORS['white'], relief='solid', borderwidth=1)
    # Frame interno sin bordes
    style.configure('NoBorder.TFrame', background=COLORS['white'], relief='flat', borderwidth=0)

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

    # Treeview sin borde
    style.configure("Custom.Treeview",
                    background=COLORS['white'],
                    foreground=COLORS['text_dark'],
                    rowheight=22,
                    fieldbackground=COLORS['white'],
                    font=('Segoe UI', 9),
                    borderwidth=0,
                    relief='flat')
    HEADER_BG = '#e5e7eb'
    HEADER_FG = '#111827'
    style.configure("Custom.Treeview.Heading",
                    background=HEADER_BG,
                    foreground=HEADER_FG,
                    font=('Segoe UI', 8, 'bold'),
                    relief='flat',
                    borderwidth=0,
                    padding=(3, 6, 3, 6),
                    anchor='center',
                    justify='center')
    style.map("Custom.Treeview",
              background=[('selected', COLORS['accent'])],
              foreground=[('selected', '#ffffff')])

    # Scrollbars planos (sin contorno)
    style.configure('Vertical.TScrollbar',
                    gripcount=0,
                    troughcolor=COLORS['white'],
                    background=COLORS['white'],
                    bordercolor=COLORS['white'],
                    lightcolor=COLORS['white'],
                    darkcolor=COLORS['white'],
                    arrowsize=12,
                    relief='flat')
    style.configure('Horizontal.TScrollbar',
                    gripcount=0,
                    troughcolor=COLORS['white'],
                    background=COLORS['white'],
                    bordercolor=COLORS['white'],
                    lightcolor=COLORS['white'],
                    darkcolor=COLORS['white'],
                    arrowsize=12,
                    relief='flat')

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


class GestionServicios:
    def __init__(self, parent_frame, main_window):
        self.parent = parent_frame
        self.main_window = main_window

        # Estilos
        self.COLORS, self._style = setup_styles(self.parent.winfo_toplevel())

        self.setup_ui()

        # Aplicar estilo al contenedor raíz si es ttk
        if isinstance(self.parent, ttk.Widget):
            self.parent.configure(style='Light.TFrame')

    # ---------- Utilería de UI ----------
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

        # Contenido sin borde interno
        content = ttk.Frame(card, style='NoBorder.TFrame')
        content.pack(fill='both', expand=True, padx=12, pady=8)

        return content

    # ---------- Utilidades ----------
    def centrar_ventana(self, ventana):
        ventana.update_idletasks()
        width = ventana.winfo_width()
        height = ventana.winfo_height()
        x = (ventana.winfo_screenwidth() // 2) - (width // 2)
        y = (ventana.winfo_screenheight() // 2) - (height // 2)
        ventana.geometry(f'{width}x{height}+{x}+{y}')

    # --- Obtención de IDs ---
    def obtener_id_area(self, nombre):
        for a in obtener_areas():
            if a['nombre'] == nombre:
                return a['id']
        return None

    def obtener_id_distrito(self, nombre):
        distritos = obtener_distritos()
        if distritos:
            for distrito in distritos:
                if distrito['nombre'] == nombre:
                    return distrito['id']
        return None

    def obtener_id_tipo_servicio(self, nombre_tipo, nombre_distrito):
        id_distrito = self.obtener_id_distrito(nombre_distrito)
        if id_distrito:
            tipos_servicio = obtener_tipos_servicio_por_distrito(id_distrito)
            if tipos_servicio:
                for tipo in tipos_servicio:
                    if tipo['descripcion'] == nombre_tipo:
                        return tipo['id']
        return None

    def obtener_id_servicio(self, nombre_servicio, nombre_tipo, nombre_distrito):
        id_tipo = self.obtener_id_tipo_servicio(nombre_tipo, nombre_distrito)
        if id_tipo:
            servicios = obtener_servicios_por_tipo(id_tipo)
            if servicios:
                for servicio in servicios:
                    if servicio['nombre'] == nombre_servicio:
                        return servicio['id']
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
            "🛠️ Gestión de Servicios del Sistema",
            "Administre áreas, distritos, tipos y servicios"
        )

        # Notebook
        nb_container = ttk.Frame(self.parent, style='Light.TFrame')
        nb_container.pack(fill="both", expand=True, padx=10, pady=5)

        self.notebook = ttk.Notebook(nb_container)
        self.notebook.pack(fill="both", expand=True)

        self.tab_areas = ttk.Frame(self.notebook, style='Light.TFrame')
        self.tab_distritos = ttk.Frame(self.notebook, style='Light.TFrame')
        self.tab_tipos = ttk.Frame(self.notebook, style='Light.TFrame')
        self.tab_servicios = ttk.Frame(self.notebook, style='Light.TFrame')

        self.notebook.add(self.tab_areas, text="🏢 Áreas")
        self.notebook.add(self.tab_distritos, text="🗺️ Distritos")
        self.notebook.add(self.tab_tipos, text="🧾 Tipos de Servicio")
        self.notebook.add(self.tab_servicios, text="🛎️ Servicios")

        self.setup_areas_tab()
        self.setup_distritos_tab()
        self.setup_tipos_tab()
        self.setup_servicios_tab()

        # Botón cerrar
        button_frame = ttk.Frame(self.parent, style='Light.TFrame')
        button_frame.pack(fill='x', pady=10, padx=10)
        ttk.Button(button_frame, text="↩️ Cerrar", style='Primary.TButton',
                   command=self.cerrar_ventana).pack(anchor='e')

        # Cargar datos
        self.actualizar_areas()
        self.actualizar_distritos()
        self.actualizar_tipos()
        self.actualizar_servicios()

    # ================== ÁREAS ==================
    def setup_areas_tab(self):
        frame_excel = self._card_section(self.tab_areas, "Carga desde Excel", "📥")
        ttk.Button(frame_excel, text="📂 Cargar Excel", style='Primary.TButton',
                   command=self.cargar_excel_areas).pack(side="left", padx=(0, 8), pady=2)
        ttk.Button(frame_excel, text="📤 Exportar a Excel", style='Primary.TButton',
                   command=self.exportar_excel_areas).pack(side="left", padx=(0, 8), pady=2)

        frame_lista = self._card_section(self.tab_areas, "Áreas", "🏢")

        table_wrap = ttk.Frame(frame_lista, style='NoBorder.TFrame')
        table_wrap.pack(fill='both', expand=True)

        self.tree_areas = ttk.Treeview(table_wrap, columns=('nombre',), show='headings', style="Custom.Treeview")
        self.tree_areas.heading('nombre', text='Área', anchor='w')
        self.tree_areas.column('nombre', anchor='w', width=320)
        self.tree_areas.pack(fill='both', expand=True, side='left', padx=(0, 5), pady=2)

        scrolly = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree_areas.yview, style='Vertical.TScrollbar')
        self.tree_areas.configure(yscrollcommand=scrolly.set)
        scrolly.pack(side='left', fill='y')

        # Botonera horizontal sin marco
        btns = ttk.Frame(frame_lista, style='NoBorder.TFrame')
        btns.pack(fill='x', padx=0, pady=(6, 0))
        ttk.Button(btns, text="➕ Agregar", style='Primary.TButton',
                   command=self.agregar_area).pack(side='left', padx=(0, 6))
        ttk.Button(btns, text="✏️ Editar", style='Primary.TButton',
                   command=self.editar_area).pack(side='left', padx=(0, 6))
        ttk.Button(btns, text="🗑️ Eliminar", style='Primary.TButton',
                   command=self.eliminar_area).pack(side='left')

    def cargar_excel_areas(self):
        filename = filedialog.askopenfilename(title="Seleccionar archivo Excel de Áreas", filetypes=[("Excel files", "*.xlsx *.xls")])
        if not filename:
            return
        df = pd.read_excel(filename)
        if 'Área' not in df.columns:
            messagebox.showerror("Error", "El archivo debe tener la columna: Área")
            return
        for area in df['Área'].dropna().unique():
            nombre = str(area).strip()
            if nombre:
                try:
                    agregar_area(nombre)
                except Exception:
                    pass
        messagebox.showinfo("Éxito", "Áreas cargadas correctamente")
        self.actualizar_areas()

    def exportar_excel_areas(self):
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if not filename:
            return
        areas = obtener_areas()
        df = pd.DataFrame([{'Área': a['nombre']} for a in areas])
        df.to_excel(filename, index=False)
        messagebox.showinfo("Éxito", "Áreas exportadas correctamente")

    def agregar_area(self):
        ventana = tk.Toplevel(self.parent)
        ventana.title("➕ Agregar Área")
        self._estilizar_toplevel(ventana)

        container = self._dialog_container(ventana, "➕ Agregar Área", "Ingrese el nombre del área")
        body = container['body']

        ttk.Label(body, text="Nombre:", style='Light.TLabel').pack(pady=(0, 4), anchor='w')
        nombre = ttk.Entry(body, width=40)
        nombre.pack(fill='x')

        def guardar():
            if nombre.get().strip():
                agregar_area(nombre.get().strip())
                self.actualizar_areas()
                ventana.destroy()
                messagebox.showinfo("Éxito", "Área agregada correctamente")
            else:
                messagebox.showwarning("Advertencia", "Ingrese un nombre")

        self._dialog_buttons(container['buttons'], guardar, ventana.destroy)

    def editar_area(self):
        selected = self.tree_areas.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un área para editar")
            return

        item = self.tree_areas.item(selected[0])
        ventana = tk.Toplevel(self.parent)
        ventana.title("✏️ Editar Área")
        self._estilizar_toplevel(ventana)

        container = self._dialog_container(ventana, "✏️ Editar Área", "Modifique el nombre del área")
        body = container['body']

        ttk.Label(body, text="Nuevo nombre:", style='Light.TLabel').pack(pady=(0, 4), anchor='w')
        nuevo_nombre = ttk.Entry(body, width=40)
        nuevo_nombre.insert(0, item['values'][0])
        nuevo_nombre.pack(fill='x')

        def guardar():
            id_area = self.obtener_id_area(item['values'][0])
            actualizar_area(id_area, nuevo_nombre.get().strip())
            self.actualizar_areas()
            ventana.destroy()
            messagebox.showinfo("Éxito", "Área actualizada correctamente")

        self._dialog_buttons(container['buttons'], guardar, ventana.destroy)

    def eliminar_area(self):
        selected = self.tree_areas.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un área para eliminar")
            return
        item = self.tree_areas.item(selected[0])
        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar esta área?"):
            id_area = self.obtener_id_area(item['values'][0])
            eliminar_area(id_area)
            self.actualizar_areas()
            messagebox.showinfo("Éxito", "Área eliminada correctamente")

    def actualizar_areas(self):
        # Optimización: ocultar columnas durante inserción (aunque hay una)
        self.tree_areas.configure(displaycolumns=())
        self.tree_areas.delete(*self.tree_areas.get_children())
        areas = obtener_areas()
        if areas:
            for area in areas:
                self.tree_areas.insert('', 'end', values=(area['nombre'],))
        self.tree_areas.configure(displaycolumns=('nombre',))

    # ================== DISTRITOS ==================
    def setup_distritos_tab(self):
        frame_excel = self._card_section(self.tab_distritos, "Carga desde Excel", "📥")
        ttk.Button(frame_excel, text="📂 Cargar Excel", style='Primary.TButton',
                   command=self.cargar_excel_distritos).pack(side="left", padx=(0, 8), pady=2)
        ttk.Button(frame_excel, text="📤 Exportar a Excel", style='Primary.TButton',
                   command=self.exportar_excel_distritos).pack(side="left", padx=(0, 8), pady=2)

        frame_lista = self._card_section(self.tab_distritos, "Distritos", "🗺️")

        table_wrap = ttk.Frame(frame_lista, style='NoBorder.TFrame')
        table_wrap.pack(fill='both', expand=True)

        self.tree_distritos = ttk.Treeview(table_wrap, columns=('nombre','area'), show='headings', style="Custom.Treeview")
        self.tree_distritos.heading('nombre', text='Distrito', anchor='w')
        self.tree_distritos.heading('area', text='Área', anchor='w')
        self.tree_distritos.column('nombre', width=240, anchor='w')
        self.tree_distritos.column('area', width=220, anchor='w')
        self.tree_distritos.pack(fill='both', expand=True, side='left', padx=(0, 5), pady=2)

        scrolly = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree_distritos.yview, style='Vertical.TScrollbar')
        self.tree_distritos.configure(yscrollcommand=scrolly.set)
        scrolly.pack(side='left', fill='y')

        btns = ttk.Frame(frame_lista, style='NoBorder.TFrame')
        btns.pack(fill='x', padx=0, pady=(6, 0))
        ttk.Button(btns, text="➕ Agregar", style='Primary.TButton',
                   command=self.agregar_distrito).pack(side='left', padx=(0, 6))
        ttk.Button(btns, text="✏️ Editar", style='Primary.TButton',
                   command=self.editar_distrito).pack(side='left', padx=(0, 6))
        ttk.Button(btns, text="🗑️ Eliminar", style='Primary.TButton',
                   command=self.eliminar_distrito).pack(side='left')

    def cargar_excel_distritos(self):
        filename = filedialog.askopenfilename(title="Seleccionar archivo Excel de Distritos", filetypes=[("Excel files", "*.xlsx *.xls")])
        if not filename:
            return
        df = pd.read_excel(filename)
        if 'Distrito' not in df.columns or 'Área' not in df.columns:
            messagebox.showerror("Error", "El archivo debe tener las columnas: Distrito y Área")
            return
        for _, row in df.iterrows():
            distrito = str(row['Distrito']).strip()
            area_nombre = str(row['Área']).strip()
            id_area = self.obtener_id_area(area_nombre) if area_nombre else None
            if distrito:
                try:
                    agregar_distrito(distrito, id_area)
                except Exception:
                    pass
        messagebox.showinfo("Éxito", "Distritos cargados correctamente")
        self.actualizar_distritos()

    def exportar_excel_distritos(self):
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if not filename:
            return
        distritos = obtener_distritos()
        df = pd.DataFrame([{'Distrito': d['nombre'], 'Área': d['area_nombre']} for d in distritos])
        df.to_excel(filename, index=False)
        messagebox.showinfo("Éxito", "Distritos exportados correctamente")

    def agregar_distrito(self):
        ventana = tk.Toplevel(self.parent)
        ventana.title("➕ Agregar Distrito")
        self._estilizar_toplevel(ventana)

        container = self._dialog_container(ventana, "➕ Agregar Distrito", "Complete los campos")
        body = container['body']

        ttk.Label(body, text="Área:", style='Light.TLabel').pack(pady=(0, 4), anchor='w')
        combo_area = ttk.Combobox(body, state="readonly")
        combo_area['values'] = [a['nombre'] for a in obtener_areas()]
        combo_area.pack(fill='x')

        ttk.Label(body, text="Nombre:", style='Light.TLabel').pack(pady=(8, 4), anchor='w')
        nombre = ttk.Entry(body, width=40)
        nombre.pack(fill='x')

        def guardar():
            if nombre.get().strip() and combo_area.get():
                area_nombre = combo_area.get()
                id_area = self.obtener_id_area(area_nombre)
                agregar_distrito(nombre.get().strip(), id_area)
                self.actualizar_distritos()
                ventana.destroy()
                messagebox.showinfo("Éxito", "Distrito agregado correctamente")
            else:
                messagebox.showwarning("Advertencia", "Complete todos los campos")

        self._dialog_buttons(container['buttons'], guardar, ventana.destroy)

    def editar_distrito(self):
        selected = self.tree_distritos.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un distrito para editar")
            return

        item = self.tree_distritos.item(selected[0])
        ventana = tk.Toplevel(self.parent)
        ventana.title("✏️ Editar Distrito")
        self._estilizar_toplevel(ventana)

        container = self._dialog_container(ventana, "✏️ Editar Distrito", "Modifique los datos del distrito")
        body = container['body']

        ttk.Label(body, text="Área:", style='Light.TLabel').pack(pady=(0, 4), anchor='w')
        combo_area = ttk.Combobox(body, state="readonly")
        areas = obtener_areas()
        combo_area['values'] = [a['nombre'] for a in areas]
        current_area = item['values'][1] if len(item['values']) > 1 else ''
        combo_area.set(current_area)
        combo_area.pack(fill='x')

        ttk.Label(body, text="Nuevo nombre:", style='Light.TLabel').pack(pady=(8, 4), anchor='w')
        nuevo_nombre = ttk.Entry(body, width=40)
        nuevo_nombre.insert(0, item['values'][0])
        nuevo_nombre.pack(fill='x')

        def guardar():
            id_distrito = self.obtener_id_distrito(item['values'][0])
            area_nombre = combo_area.get()
            id_area = self.obtener_id_area(area_nombre) if area_nombre else None
            actualizar_distrito(id_distrito, nuevo_nombre.get().strip(), id_area)
            self.actualizar_distritos()
            ventana.destroy()
            messagebox.showinfo("Éxito", "Distrito actualizado correctamente")

        self._dialog_buttons(container['buttons'], guardar, ventana.destroy)

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
        self.tree_distritos.configure(displaycolumns=())
        self.tree_distritos.delete(*self.tree_distritos.get_children())
        distritos = obtener_distritos()
        if distritos:
            for d in distritos:
                self.tree_distritos.insert('', 'end', values=(d['nombre'], d['area_nombre']))
        self.tree_distritos.configure(displaycolumns=('nombre', 'area'))

    # ================== TIPOS DE SERVICIO ==================
    def setup_tipos_tab(self):
        frame_excel = self._card_section(self.tab_tipos, "Carga desde Excel", "📥")
        ttk.Button(frame_excel, text="📂 Cargar Excel", style='Primary.TButton',
                   command=self.cargar_excel_tipos).pack(side="left", padx=(0, 8), pady=2)
        ttk.Button(frame_excel, text="📤 Exportar a Excel", style='Primary.TButton',
                   command=self.exportar_excel_tipos).pack(side="left", padx=(0, 8), pady=2)

        frame_lista = self._card_section(self.tab_tipos, "Tipos de Servicio", "🧾")

        table_wrap = ttk.Frame(frame_lista, style='NoBorder.TFrame')
        table_wrap.pack(fill='both', expand=True)

        self.tree_tipos = ttk.Treeview(table_wrap, columns=('distrito', 'descripcion'), show='headings', style="Custom.Treeview")
        self.tree_tipos.heading('distrito', text='Distrito', anchor='w')
        self.tree_tipos.heading('descripcion', text='Tipo de Servicio', anchor='w')
        self.tree_tipos.column('distrito', width=240, anchor='w')
        self.tree_tipos.column('descripcion', width=280, anchor='w')
        self.tree_tipos.pack(fill='both', expand=True, side='left', padx=(0, 5), pady=2)

        scrolly = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree_tipos.yview, style='Vertical.TScrollbar')
        self.tree_tipos.configure(yscrollcommand=scrolly.set)
        scrolly.pack(side='left', fill='y')

        btns = ttk.Frame(frame_lista, style='NoBorder.TFrame')
        btns.pack(fill='x', padx=0, pady=(6, 0))
        ttk.Button(btns, text="➕ Agregar", style='Primary.TButton',
                   command=self.agregar_tipo).pack(side='left', padx=(0, 6))
        ttk.Button(btns, text="✏️ Editar", style='Primary.TButton',
                   command=self.editar_tipo).pack(side='left', padx=(0, 6))
        ttk.Button(btns, text="🗑️ Eliminar", style='Primary.TButton',
                   command=self.eliminar_tipo).pack(side='left')

    def cargar_excel_tipos(self):
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo Excel de Tipos de Servicio",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if not filename:
            return

        try:
            df = pd.read_excel(filename)
            required_columns = ['Distrito', 'Tipo de Servicio']
            if not all(col in df.columns for col in required_columns):
                messagebox.showerror("Error", "El archivo debe tener las columnas: Distrito, Tipo de Servicio")
                return

            registros_procesados = 0
            registros_existentes = 0

            for _, row in df.iterrows():
                try:
                    distrito = str(row['Distrito']).strip()
                    tipo = str(row['Tipo de Servicio']).strip()
                    if not distrito or not tipo:
                        continue

                    id_distrito = self.obtener_id_distrito(distrito)
                    if not id_distrito:
                        id_distrito = agregar_distrito(distrito)

                    tipo_existente = self.obtener_id_tipo_servicio(tipo, distrito)
                    if tipo_existente:
                        registros_existentes += 1
                        continue

                    agregar_tipo_servicio(id_distrito, tipo)
                    registros_procesados += 1
                except Exception:
                    continue

            self.actualizar_tipos()
            mensaje = f"Proceso completado:\n- Registros nuevos agregados: {registros_procesados}\n- Registros existentes omitidos: {registros_existentes}"
            messagebox.showinfo("Éxito", mensaje)

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar el archivo: {str(e)}")

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
        ventana.title("➕ Agregar Tipo de Servicio")
        self._estilizar_toplevel(ventana)

        container = self._dialog_container(ventana, "➕ Agregar Tipo de Servicio", "Complete los campos")
        body = container['body']

        ttk.Label(body, text="Área:", style='Light.TLabel').pack(pady=(0, 4), anchor='w')
        combo_area = ttk.Combobox(body, state="readonly")
        areas = obtener_areas()
        combo_area['values'] = [a['nombre'] for a in areas]
        combo_area.pack(fill='x')

        ttk.Label(body, text="Distrito:", style='Light.TLabel').pack(pady=(8, 4), anchor='w')
        combo_distrito = ttk.Combobox(body, state="readonly")
        combo_distrito.pack(fill='x')

        def actualizar_distritos(event=None):
            area_nombre = combo_area.get()
            id_area = next((a['id'] for a in areas if a['nombre'] == area_nombre), None)
            if id_area:
                distritos = obtener_distritos_por_area(id_area)
                combo_distrito['values'] = [d['nombre'] for d in distritos]
                combo_distrito.set('')
            else:
                combo_distrito['values'] = []
                combo_distrito.set('')

        combo_area.bind("<<ComboboxSelected>>", actualizar_distritos)

        ttk.Label(body, text="Tipo de Servicio:", style='Light.TLabel').pack(pady=(8, 4), anchor='w')
        descripcion = ttk.Entry(body, width=40)
        descripcion.pack(fill='x')

        def guardar():
            if not combo_area.get() or not combo_distrito.get() or not descripcion.get().strip():
                messagebox.showwarning("Advertencia", "Complete todos los campos")
                return

            id_distrito = self.obtener_id_distrito(combo_distrito.get())
            tipo = descripcion.get().strip()

            tipo_existente = self.obtener_id_tipo_servicio(tipo, combo_distrito.get())
            if tipo_existente:
                messagebox.showwarning("Advertencia", "Ya existe un tipo de servicio con ese nombre en el distrito seleccionado")
                return

            agregar_tipo_servicio(id_distrito, tipo)
            self.actualizar_tipos()
            ventana.destroy()
            messagebox.showinfo("Éxito", "Tipo de servicio agregado correctamente")

        self._dialog_buttons(container['buttons'], guardar, ventana.destroy)

    def editar_tipo(self):
        selected = self.tree_tipos.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un tipo de servicio para editar")
            return
        item = self.tree_tipos.item(selected[0])

        ventana = tk.Toplevel(self.parent)
        ventana.title("✏️ Editar Tipo de Servicio")
        self._estilizar_toplevel(ventana)

        container = self._dialog_container(ventana, "✏️ Editar Tipo de Servicio", "Actualice los datos")
        body = container['body']

        ttk.Label(body, text="Área:", style='Light.TLabel').pack(pady=(0, 4), anchor='w')
        combo_area = ttk.Combobox(body, state="readonly")
        areas = obtener_areas()
        combo_area['values'] = [a['nombre'] for a in areas]
        combo_area.pack(fill='x')

        ttk.Label(body, text="Distrito:", style='Light.TLabel').pack(pady=(8, 4), anchor='w')
        combo_distrito = ttk.Combobox(body, state="readonly")
        combo_distrito.pack(fill='x')

        def actualizar_distritos(event=None):
            area_nombre = combo_area.get()
            id_area = next((a['id'] for a in areas if a['nombre'] == area_nombre), None)
            if id_area:
                distritos = obtener_distritos_por_area(id_area)
                combo_distrito['values'] = [d['nombre'] for d in distritos]
            else:
                combo_distrito['values'] = []

        combo_area.bind("<<ComboboxSelected>>", actualizar_distritos)

        # Establecer valores iniciales desde item
        distrito_actual = item['values'][0]
        distritos = obtener_distritos()
        area_actual = ''
        for d in distritos:
            if d['nombre'] == distrito_actual:
                area_actual = d.get('area_nombre', '')
                break

        combo_area.set(area_actual)
        actualizar_distritos(None)
        combo_distrito.set(distrito_actual)

        ttk.Label(body, text="Tipo de Servicio:", style='Light.TLabel').pack(pady=(8, 4), anchor='w')
        descripcion = ttk.Entry(body, width=40)
        descripcion.insert(0, item['values'][1])
        descripcion.pack(fill='x')

        def guardar():
            if not combo_area.get() or not combo_distrito.get() or not descripcion.get().strip():
                messagebox.showwarning("Advertencia", "Complete todos los campos")
                return

            id_tipo = self.obtener_id_tipo_servicio(item['values'][1], item['values'][0])
            actualizar_tipo_servicio(id_tipo, descripcion.get().strip())
            self.actualizar_tipos()
            ventana.destroy()
            messagebox.showinfo("Éxito", "Tipo de servicio actualizado correctamente")

        self._dialog_buttons(container['buttons'], guardar, ventana.destroy)

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
        self.tree_tipos.configure(displaycolumns=())
        self.tree_tipos.delete(*self.tree_tipos.get_children())
        for d in obtener_distritos():
            for t in obtener_tipos_servicio_por_distrito(d['id']):
                self.tree_tipos.insert('', 'end', values=(d['nombre'], t['descripcion']))
        self.tree_tipos.configure(displaycolumns=('distrito', 'descripcion'))

    # ================== SERVICIOS ==================
    def setup_servicios_tab(self):
        frame_excel = self._card_section(self.tab_servicios, "Carga desde Excel", "📥")
        ttk.Button(frame_excel, text="📂 Cargar Excel", style='Primary.TButton',
                   command=self.cargar_excel_servicios).pack(side="left", padx=(0, 8), pady=2)
        ttk.Button(frame_excel, text="📤 Exportar a Excel", style='Primary.TButton',
                   command=self.exportar_excel_servicios).pack(side="left", padx=(0, 8), pady=2)

        frame_lista = self._card_section(self.tab_servicios, "Servicios", "🛎️")

        table_wrap = ttk.Frame(frame_lista, style='NoBorder.TFrame')
        table_wrap.pack(fill='both', expand=True)

        self.tree_servicios = ttk.Treeview(table_wrap, columns=('distrito', 'tipo', 'nombre'), show='headings', style="Custom.Treeview")
        self.tree_servicios.heading('distrito', text='Distrito', anchor='w')
        self.tree_servicios.heading('tipo', text='Tipo de Servicio', anchor='w')
        self.tree_servicios.heading('nombre', text='Servicio', anchor='w')
        self.tree_servicios.column('distrito', width=220, anchor='w')
        self.tree_servicios.column('tipo', width=260, anchor='w')
        self.tree_servicios.column('nombre', width=260, anchor='w')
        self.tree_servicios.pack(fill='both', expand=True, side='left', padx=(0, 5), pady=2)

        scrolly = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree_servicios.yview, style='Vertical.TScrollbar')
        self.tree_servicios.configure(yscrollcommand=scrolly.set)
        scrolly.pack(side='left', fill='y')

        btns = ttk.Frame(frame_lista, style='NoBorder.TFrame')
        btns.pack(fill='x', padx=0, pady=(6, 0))
        ttk.Button(btns, text="➕ Agregar", style='Primary.TButton',
                   command=self.agregar_servicio).pack(side='left', padx=(0, 6))
        ttk.Button(btns, text="✏️ Editar", style='Primary.TButton',
                   command=self.editar_servicio).pack(side='left', padx=(0, 6))
        ttk.Button(btns, text="🗑️ Eliminar", style='Primary.TButton',
                   command=self.eliminar_servicio).pack(side='left')

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
            if not (distrito and tipo and servicio):
                continue
            id_distrito = self.obtener_id_distrito(distrito)
            if not id_distrito:
                id_distrito = agregar_distrito(distrito)
            id_tipo = self.obtener_id_tipo_servicio(tipo, distrito)
            if not id_tipo:
                id_tipo = agregar_tipo_servicio(id_distrito, tipo)
            try:
                agregar_servicio(id_tipo, servicio)
            except Exception:
                pass
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
        ventana.title("➕ Agregar Servicio")
        self._estilizar_toplevel(ventana)

        container = self._dialog_container(ventana, "➕ Agregar Servicio", "Complete los campos")
        body = container['body']

        ttk.Label(body, text="Área:", style='Light.TLabel').pack(pady=(0, 4), anchor='w')
        combo_area = ttk.Combobox(body, state="readonly")
        areas = obtener_areas()
        combo_area['values'] = [a['nombre'] for a in areas]
        combo_area.pack(fill='x')

        ttk.Label(body, text="Distrito:", style='Light.TLabel').pack(pady=(8, 4), anchor='w')
        combo_distrito = ttk.Combobox(body, state="readonly")
        combo_distrito.pack(fill='x')

        ttk.Label(body, text="Tipo de Servicio:", style='Light.TLabel').pack(pady=(8, 4), anchor='w')
        combo_tipo = ttk.Combobox(body, state="readonly")
        combo_tipo.pack(fill='x')

        def actualizar_distritos(event=None):
            area_nombre = combo_area.get()
            id_area = next((a['id'] for a in areas if a['nombre'] == area_nombre), None)
            if id_area:
                distritos = obtener_distritos_por_area(id_area)
                combo_distrito['values'] = [d['nombre'] for d in distritos]
                combo_distrito.set('')
                combo_tipo.set('')
                combo_tipo['values'] = []
            else:
                combo_distrito['values'] = []
                combo_distrito.set('')
                combo_tipo['values'] = []
                combo_tipo.set('')

        def actualizar_tipos(event=None):
            id_distrito = self.obtener_id_distrito(combo_distrito.get())
            tipos = obtener_tipos_servicio_por_distrito(id_distrito) if id_distrito else []
            combo_tipo['values'] = [t['descripcion'] for t in tipos]
            combo_tipo.set('')

        combo_area.bind("<<ComboboxSelected>>", actualizar_distritos)
        combo_distrito.bind("<<ComboboxSelected>>", actualizar_tipos)

        ttk.Label(body, text="Servicio:", style='Light.TLabel').pack(pady=(8, 4), anchor='w')
        nombre = ttk.Entry(body, width=40)
        nombre.pack(fill='x')

        def guardar():
            if not combo_area.get() or not combo_distrito.get() or not combo_tipo.get() or not nombre.get().strip():
                messagebox.showwarning("Advertencia", "Complete todos los campos")
                return

            id_tipo = self.obtener_id_tipo_servicio(combo_tipo.get(), combo_distrito.get())
            agregar_servicio(id_tipo, nombre.get().strip())
            self.actualizar_servicios()
            ventana.destroy()
            messagebox.showinfo("Éxito", "Servicio agregado correctamente")

        self._dialog_buttons(container['buttons'], guardar, ventana.destroy)

    def editar_servicio(self):
        selected = self.tree_servicios.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un servicio para editar")
            return
        item = self.tree_servicios.item(selected[0])

        ventana = tk.Toplevel(self.parent)
        ventana.title("✏️ Editar Servicio")
        self._estilizar_toplevel(ventana)

        container = self._dialog_container(ventana, "✏️ Editar Servicio", "Actualice los datos")
        body = container['body']

        ttk.Label(body, text="Área:", style='Light.TLabel').pack(pady=(0, 4), anchor='w')
        combo_area = ttk.Combobox(body, state="readonly")
        areas = obtener_areas()
        combo_area['values'] = [a['nombre'] for a in areas]
        combo_area.pack(fill='x')

        ttk.Label(body, text="Distrito:", style='Light.TLabel').pack(pady=(8, 4), anchor='w')
        combo_distrito = ttk.Combobox(body, state="readonly")
        combo_distrito.pack(fill='x')

        ttk.Label(body, text="Tipo de Servicio:", style='Light.TLabel').pack(pady=(8, 4), anchor='w')
        combo_tipo = ttk.Combobox(body, state="readonly")
        combo_tipo.pack(fill='x')

        def actualizar_distritos(event=None):
            area_nombre = combo_area.get()
            id_area = next((a['id'] for a in areas if a['nombre'] == area_nombre), None)
            if id_area:
                distritos = obtener_distritos_por_area(id_area)
                combo_distrito['values'] = [d['nombre'] for d in distritos]
                if item['values'][0] not in [d['nombre'] for d in distritos]:
                    combo_distrito.set('')
            else:
                combo_distrito['values'] = []
                combo_distrito.set('')

        def actualizar_tipos(event=None):
            id_distrito = self.obtener_id_distrito(combo_distrito.get())
            tipos = obtener_tipos_servicio_por_distrito(id_distrito) if id_distrito else []
            combo_tipo['values'] = [t['descripcion'] for t in tipos]
            if item['values'][1] not in [t['descripcion'] for t in tipos]:
                combo_tipo.set('')

        combo_area.bind("<<ComboboxSelected>>", actualizar_distritos)
        combo_distrito.bind("<<ComboboxSelected>>", actualizar_tipos)

        # Establecer valores iniciales
        distritos = obtener_distritos()
        area_actual = ''
        for d in distritos:
            if d['nombre'] == item['values'][0]:
                area_actual = d.get('area_nombre', '')
                break

        combo_area.set(area_actual)
        actualizar_distritos(None)
        combo_distrito.set(item['values'][0])
        actualizar_tipos(None)
        combo_tipo.set(item['values'][1])

        ttk.Label(body, text="Servicio:", style='Light.TLabel').pack(pady=(8, 4), anchor='w')
        nombre = ttk.Entry(body, width=40)
        nombre.insert(0, item['values'][2])
        nombre.pack(fill='x')

        def guardar():
            if not combo_area.get() or not combo_distrito.get() or not combo_tipo.get() or not nombre.get().strip():
                messagebox.showwarning("Advertencia", "Complete todos los campos")
                return

            id_servicio = self.obtener_id_servicio(item['values'][2], item['values'][1], item['values'][0])
            actualizar_servicio(id_servicio, nombre.get().strip())
            self.actualizar_servicios()
            ventana.destroy()
            messagebox.showinfo("Éxito", "Servicio actualizado correctamente")

        self._dialog_buttons(container['buttons'], guardar, ventana.destroy)

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
        self.tree_servicios.configure(displaycolumns=())
        self.tree_servicios.delete(*self.tree_servicios.get_children())
        for d in obtener_distritos():
            for t in obtener_tipos_servicio_por_distrito(d['id']):
                for s in obtener_servicios_por_tipo(t['id']):
                    self.tree_servicios.insert('', 'end', values=(d['nombre'], t['descripcion'], s['nombre']))
        self.tree_servicios.configure(displaycolumns=('distrito', 'tipo', 'nombre'))

    # ---------- Diálogos y Toplevel estilizados ----------
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

    # ---------- Cierre ----------
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