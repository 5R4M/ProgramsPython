# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import sys
import os

# Agregar el directorio raíz del proyecto al PATH de Python
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.database.db_manager import (
    agregar_area,
    obtener_areas,
    actualizar_area,
    eliminar_area,
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

        # Paleta local (no modifica estilos globales)
        self.COLORS = {
            'primary':   '#2c3e50',
            'accent':    '#3498db',
            'light':     '#ecf0f1',
            'white':     '#ffffff',
            'text_dark': '#2c3e50',
        }

        # Caches en memoria
        self.areas_by_id = {}
        self.areas_by_name = {}
        self.distritos_by_id = {}
        self.distritos_by_name = {}
        self.distritos_by_area = {}      # id_area -> [ {id, nombre} ]
        self.tipos_by_distrito = {}      # id_distrito -> [ {id, descripcion} ]
        self.tipos_flat = []             # [(id_tipo, id_distrito, desc)]
        self.servicios_by_tipo = {}      # id_tipo -> [ {id, nombre} ]

        # Flags de carga por pestaña
        self._areas_loaded = False
        self._distritos_loaded = False
        self._tipos_loaded = False
        self._servicios_loaded = False

        self.setup_ui()

        # Cargar inicialmente solo la pestaña de Áreas
        self._load_areas_tab()

        # Carga diferida al cambiar de pestaña
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    # ---------- Utilería de UI ----------
    def _header_title_sub(self, parent, title_text, subtitle_text):
        # Header azul a todo el ancho, pegado arriba, sin separadores laterales
        header_frame = tk.Frame(parent, bg=self.COLORS['primary'], height=55)
        header_frame.pack(fill='x', padx=0, pady=(0, 6))  # sin margen superior ni laterales
        header_frame.pack_propagate(False)

        header_inner = tk.Frame(header_frame, bg=self.COLORS['primary'])
        header_inner.pack(fill='both', expand=True, padx=10, pady=4)  # padding interno solo para el contenido

        tk.Label(header_inner, text=title_text,
                font=('Segoe UI', 12, 'bold'),
                fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(anchor='w')
        tk.Label(header_inner, text=subtitle_text,
                font=('Segoe UI', 9),
                fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(anchor='w', pady=(1, 0))

    def _card_section(self, parent, title, icon):
        container = tk.Frame(parent, bg=self.COLORS['light'])
        container.pack(fill='x', padx=10, pady=6)

        card = tk.Frame(container, bg=self.COLORS['white'], bd=1, relief='solid', highlightthickness=0)
        card.pack(fill='both', expand=True)

        header = tk.Frame(card, bg=self.COLORS['primary'], height=24)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(header, text=f"{icon} {title}", font=('Segoe UI', 10, 'bold'),
                 fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(side='left', padx=10)

        content = tk.Frame(card, bg=self.COLORS['white'])
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

    # --- Carga diferida por pestañas ---
    def _on_tab_changed(self, event):
        tab = event.widget.select()
        current = event.widget.tab(tab, "text")
        if current.startswith("🏢"):
            self._load_areas_tab()
        elif current.startswith("🗺️"):
            self._load_distritos_tab()
        elif current.startswith("🧾"):
            self._load_tipos_tab()
        elif current.startswith("🛎️"):
            self._load_servicios_tab()
        
        # Forzar actualización de scrollbars después de cambio de pestaña
        self.parent.after(100, self._actualizar_scrollbars)

    def _load_areas_tab(self):
        if not self._areas_loaded:
            self._refresh_caches_base()
            self.actualizar_areas()
            self._areas_loaded = True

    def _load_distritos_tab(self):
        if not self._distritos_loaded:
            self._refresh_caches_base()
            self.actualizar_distritos()
            self._distritos_loaded = True

    def _load_tipos_tab(self):
        if not self._tipos_loaded:
            self._refresh_caches_base()
            self._refresh_cache_tipos()
            self.actualizar_tipos()
            self._tipos_loaded = True

    def _load_servicios_tab(self):
        if not self._servicios_loaded:
            self._refresh_caches_base()
            self._refresh_cache_tipos()
            self._refresh_cache_servicios()
            self.actualizar_servicios()
            self._servicios_loaded = True

    # --- Caches de datos ---
    def _refresh_caches_base(self):
        # Áreas
        areas = obtener_areas() or []
        self.areas_by_id = {a['id']: a['nombre'] for a in areas}
        self.areas_by_name = {a['nombre']: a['id'] for a in areas}

        # Distritos (ideal si tu función devuelve area_id y area_nombre)
        distritos = obtener_distritos() or []
        self.distritos_by_id = {
            d['id']: {
                'id': d['id'],
                'nombre': d['nombre'],
                'area_id': d.get('area_id'),
                'area_nombre': d.get('area_nombre')
            } for d in distritos
        }
        self.distritos_by_name = {d['nombre']: d['id'] for d in distritos}

        # Mapear distritos por área
        self.distritos_by_area = {}
        for d in distritos:
            aid = d.get('area_id')
            if aid is None and d.get('area_nombre'):
                aid = self.areas_by_name.get(d['area_nombre'])
            if aid is not None:
                self.distritos_by_area.setdefault(aid, []).append({'id': d['id'], 'nombre': d['nombre']})

    def _refresh_cache_tipos(self):
        self.tipos_by_distrito = {}
        self.tipos_flat = []
        for d_id in self.distritos_by_id.keys():
            tipos = obtener_tipos_servicio_por_distrito(d_id) or []
            self.tipos_by_distrito[d_id] = tipos
            for t in tipos:
                self.tipos_flat.append((t['id'], d_id, t['descripcion']))

    def _refresh_cache_servicios(self):
        self.servicios_by_tipo = {}
        for t_id, _d_id, _desc in self.tipos_flat:
            servicios = obtener_servicios_por_tipo(t_id) or []
            self.servicios_by_tipo[t_id] = servicios

    # --- Lookups O(1) sobre caches ---
    def obtener_id_area(self, nombre):
        return self.areas_by_name.get(nombre)

    def obtener_id_distrito(self, nombre):
        return self.distritos_by_name.get(nombre)

    def obtener_id_tipo_servicio(self, nombre_tipo, nombre_distrito):
        d_id = self.obtener_id_distrito(nombre_distrito)
        if not d_id:
            return None
        for t in self.tipos_by_distrito.get(d_id, []):
            if t['descripcion'] == nombre_tipo:
                return t['id']
        return None

    def obtener_id_servicio(self, nombre_servicio, nombre_tipo, nombre_distrito):
        t_id = self.obtener_id_tipo_servicio(nombre_tipo, nombre_distrito)
        if not t_id:
            return None
        for s in self.servicios_by_tipo.get(t_id, []):
            if s['nombre'] == nombre_servicio:
                return s['id']
        return None

    # --- Configuración UI ---
    def setup_ui(self):
        # Header principal
        self._header_title_sub(
            self.parent,
            "🛠️ Gestión de Servicios del Sistema",
            "Administre áreas, distritos, tipos y servicios"
        )

        # Notebook
        nb_container = tk.Frame(self.parent, bg=self.COLORS['light'])
        nb_container.pack(fill="both", expand=True, padx=10, pady=5)

        self.notebook = ttk.Notebook(nb_container)
        self.notebook.pack(fill="both", expand=True)

        self.tab_areas = tk.Frame(self.notebook, bg=self.COLORS['light'])
        self.tab_distritos = tk.Frame(self.notebook, bg=self.COLORS['light'])
        self.tab_tipos = tk.Frame(self.notebook, bg=self.COLORS['light'])
        self.tab_servicios = tk.Frame(self.notebook, bg=self.COLORS['light'])

        self.notebook.add(self.tab_areas, text="🏢 Áreas")
        self.notebook.add(self.tab_distritos, text="🗺️ Distritos")
        self.notebook.add(self.tab_tipos, text="🧾 Tipos de Servicio")
        self.notebook.add(self.tab_servicios, text="🛎️ Servicios")

        self.setup_areas_tab()
        self.setup_distritos_tab()
        self.setup_tipos_tab()
        self.setup_servicios_tab()

        # Botón cerrar
        button_frame = tk.Frame(self.parent, bg=self.COLORS['light'])
        button_frame.pack(fill='x', pady=10, padx=10)
        tk.Button(button_frame, text="↩️ Cerrar",
                  bg=self.COLORS['accent'], fg='white', relief='flat', padx=10, pady=5,
                  command=self.cerrar_ventana).pack(anchor='e')

    # ================== ÁREAS ==================
    def setup_areas_tab(self):
        frame_excel = self._card_section(self.tab_areas, "Carga desde Excel", "📥")
        tk.Button(frame_excel, text="📂 Cargar Excel",
                bg=self.COLORS['accent'], fg='white', relief='flat', padx=10, pady=5,
                command=self.cargar_excel_areas).pack(side="left", padx=(0, 8), pady=2)
        tk.Button(frame_excel, text="📤 Exportar a Excel",
                bg=self.COLORS['accent'], fg='white', relief='flat', padx=10, pady=5,
                command=self.exportar_excel_areas).pack(side="left", padx=(0, 8), pady=2)

        frame_lista = self._card_section(self.tab_areas, "Áreas", "🏢")

        table_wrap = tk.Frame(frame_lista, bg=self.COLORS['white'])
        table_wrap.pack(fill='both', expand=True)

        # Crear Treeview con altura mínima
        self.tree_areas = ttk.Treeview(table_wrap, columns=('nombre',), show='headings', height=10)
        self.tree_areas.heading('nombre', text='Área', anchor='w')
        self.tree_areas.column('nombre', anchor='w', width=320, stretch=True)
        
        # Scrollbar vertical - CONFIGURACIÓN MEJORADA
        scrolly_areas = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree_areas.yview)
        self.tree_areas.configure(yscrollcommand=scrolly_areas.set)
        
        # Empaquetado correcto - scrollbar primero
        scrolly_areas.pack(side='right', fill='y')
        self.tree_areas.pack(side='left', fill='both', expand=True, pady=2)

        btns = tk.Frame(frame_lista, bg=self.COLORS['white'])
        btns.pack(fill='x', padx=0, pady=(6, 0))
        tk.Button(btns, text="➕ Agregar", bg=self.COLORS['accent'], fg='white',
                relief='flat', padx=10, pady=5, command=self.agregar_area).pack(side='left', padx=(0, 6))
        tk.Button(btns, text="✏️ Editar", bg=self.COLORS['accent'], fg='white',
                relief='flat', padx=10, pady=5, command=self.editar_area).pack(side='left', padx=(0, 6))
        tk.Button(btns, text="🗑️ Eliminar", bg=self.COLORS['accent'], fg='white',
                relief='flat', padx=10, pady=5, command=self.eliminar_area).pack(side='left')

    def cargar_excel_areas(self):
        filename = filedialog.askopenfilename(title="Seleccionar archivo Excel de Áreas", filetypes=[("Excel files", "*.xlsx *.xls")])
        if not filename:
            return
        df = pd.read_excel(filename)
        if 'Área' not in df.columns:
            messagebox.showerror("Error", "El archivo debe tener la columna: Área")
            return
        nuevos = 0
        existentes = 0
        existentes_set = set(self.areas_by_name.keys())
        for area in df['Área'].dropna().unique():
            nombre = str(area).strip()
            if not nombre:
                continue
            if nombre in existentes_set:
                existentes += 1
                continue
            try:
                new_id = agregar_area(nombre)
                self.areas_by_id[new_id] = nombre
                self.areas_by_name[nombre] = new_id
                nuevos += 1
            except Exception:
                existentes += 1
        messagebox.showinfo("Éxito", f"Áreas cargadas.\nNuevas: {nuevos}\nExistentes: {existentes}")
        self.actualizar_areas()

    def exportar_excel_areas(self):
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if not filename:
            return
        df = pd.DataFrame([{'Área': nombre} for _id, nombre in self.areas_by_id.items()])
        df = df.sort_values(by='Área')
        df.to_excel(filename, index=False)
        messagebox.showinfo("Éxito", "Áreas exportadas correctamente")

    def agregar_area(self):
        ventana = tk.Toplevel(self.parent)
        ventana.title("➕ Agregar Área")
        self._estilizar_toplevel(ventana)

        container = self._dialog_container(ventana, "➕ Agregar Área", "Ingrese el nombre del área")
        body = container['body']

        tk.Label(body, text="Nombre:", bg=self.COLORS['white']).pack(pady=(0, 4), anchor='w')
        nombre = ttk.Entry(body, width=40)
        nombre.pack(fill='x')

        def guardar():
            nom = nombre.get().strip()
            if not nom:
                messagebox.showwarning("Advertencia", "Ingrese un nombre")
                return
            if nom in self.areas_by_name:
                messagebox.showwarning("Advertencia", "El área ya existe")
                return
            new_id = agregar_area(nom)
            self.areas_by_id[new_id] = nom
            self.areas_by_name[nom] = new_id
            self.actualizar_areas()
            ventana.destroy()
            messagebox.showinfo("Éxito", "Área agregada correctamente")

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

        tk.Label(body, text="Nuevo nombre:", bg=self.COLORS['white']).pack(pady=(0, 4), anchor='w')
        nuevo_nombre = ttk.Entry(body, width=40)
        nuevo_nombre.insert(0, item['values'][0])
        nuevo_nombre.pack(fill='x')

        def guardar():
            old_name = item['values'][0]
            new_name = nuevo_nombre.get().strip()
            if not new_name:
                messagebox.showwarning("Advertencia", "Ingrese un nombre")
                return
            if new_name == old_name:
                ventana.destroy()
                return
            area_id = self.areas_by_name.get(old_name)
            actualizar_area(area_id, new_name)
            self.areas_by_id[area_id] = new_name
            self.areas_by_name.pop(old_name, None)
            self.areas_by_name[new_name] = area_id
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
            area_name = item['values'][0]
            area_id = self.areas_by_name.get(area_name)
            eliminar_area(area_id)
            self.areas_by_name.pop(area_name, None)
            self.areas_by_id.pop(area_id, None)
            self.distritos_by_area.pop(area_id, None)
            self.actualizar_areas()
            if self._distritos_loaded:
                self._refresh_caches_base()
                self.actualizar_distritos()
            if self._tipos_loaded:
                self._refresh_cache_tipos()
                self.actualizar_tipos()
            if self._servicios_loaded:
                self._refresh_cache_tipos()
                self._refresh_cache_servicios()
                self.actualizar_servicios()
            messagebox.showinfo("Éxito", "Área eliminada correctamente")

    def actualizar_areas(self):
        self.tree_areas.configure(displaycolumns=())
        self.tree_areas.delete(*self.tree_areas.get_children())
        for aid, nombre in sorted(self.areas_by_id.items(), key=lambda kv: kv[1].lower()):
            self.tree_areas.insert('', 'end', values=(nombre,))
        self.tree_areas.configure(displaycolumns=('nombre',))
        # Forzar actualización del scrollbar
        self.tree_areas.update_idletasks()

    # ================== DISTRITOS ==================
    def setup_distritos_tab(self):
        frame_excel = self._card_section(self.tab_distritos, "Carga desde Excel", "📥")
        tk.Button(frame_excel, text="📂 Cargar Excel",
                bg=self.COLORS['accent'], fg='white', relief='flat', padx=10, pady=5,
                command=self.cargar_excel_distritos).pack(side="left", padx=(0, 8), pady=2)
        tk.Button(frame_excel, text="📤 Exportar a Excel",
                bg=self.COLORS['accent'], fg='white', relief='flat', padx=10, pady=5,
                command=self.exportar_excel_distritos).pack(side="left", padx=(0, 8), pady=2)

        frame_lista = self._card_section(self.tab_distritos, "Distritos", "🗺️")

        table_wrap = tk.Frame(frame_lista, bg=self.COLORS['white'])
        table_wrap.pack(fill='both', expand=True)

        self.tree_distritos = ttk.Treeview(table_wrap, columns=('nombre','area'), show='headings', height=10)
        self.tree_distritos.heading('nombre', text='Distrito', anchor='w')
        self.tree_distritos.heading('area', text='Área', anchor='w')
        self.tree_distritos.column('nombre', width=240, anchor='w', stretch=True)
        self.tree_distritos.column('area', width=220, anchor='w', stretch=True)

        # Scrollbar vertical mejorada
        scrolly_distritos = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree_distritos.yview)
        self.tree_distritos.configure(yscrollcommand=scrolly_distritos.set)
        
        scrolly_distritos.pack(side='right', fill='y')
        self.tree_distritos.pack(side='left', fill='both', expand=True, pady=2)

        btns = tk.Frame(frame_lista, bg=self.COLORS['white'])
        btns.pack(fill='x', padx=0, pady=(6, 0))
        tk.Button(btns, text="➕ Agregar", bg=self.COLORS['accent'], fg='white',
                relief='flat', padx=10, pady=5, command=self.agregar_distrito).pack(side='left', padx=(0, 6))
        tk.Button(btns, text="✏️ Editar", bg=self.COLORS['accent'], fg='white',
                relief='flat', padx=10, pady=5, command=self.editar_distrito).pack(side='left', padx=(0, 6))
        tk.Button(btns, text="🗑️ Eliminar", bg=self.COLORS['accent'], fg='white',
                relief='flat', padx=10, pady=5, command=self.eliminar_distrito).pack(side='left')

    def cargar_excel_distritos(self):
        filename = filedialog.askopenfilename(title="Seleccionar archivo Excel de Distritos", filetypes=[("Excel files", "*.xlsx *.xls")])
        if not filename:
            return
        df = pd.read_excel(filename)
        if 'Distrito' not in df.columns or 'Área' not in df.columns:
            messagebox.showerror("Error", "El archivo debe tener las columnas: Distrito y Área")
            return
        nuevos = 0
        existentes = 0
        for _, row in df.iterrows():
            distrito = str(row['Distrito']).strip()
            area_nombre = str(row['Área']).strip()
            if not distrito:
                continue
            area_id = self.areas_by_name.get(area_nombre)
            if area_nombre and area_id is None:
                area_id = agregar_area(area_nombre)
                self.areas_by_id[area_id] = area_nombre
                self.areas_by_name[area_nombre] = area_id
            if distrito in self.distritos_by_name:
                existentes += 1
                continue
            try:
                d_id = agregar_distrito(distrito, area_id)
                self.distritos_by_id[d_id] = {'id': d_id, 'nombre': distrito, 'area_id': area_id, 'area_nombre': area_nombre}
                self.distritos_by_name[distrito] = d_id
                if area_id is not None:
                    self.distritos_by_area.setdefault(area_id, []).append({'id': d_id, 'nombre': distrito})
                nuevos += 1
            except Exception:
                existentes += 1
        messagebox.showinfo("Éxito", f"Distritos cargados.\nNuevos: {nuevos}\nExistentes: {existentes}")
        self.actualizar_distritos()

    def exportar_excel_distritos(self):
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if not filename:
            return
        data = []
        for d in self.distritos_by_id.values():
            data.append({'Distrito': d['nombre'], 'Área': d.get('area_nombre') or self.areas_by_id.get(d.get('area_id'))})
        df = pd.DataFrame(data).sort_values(by=['Área','Distrito'], na_position='last')
        df.to_excel(filename, index=False)
        messagebox.showinfo("Éxito", "Distritos exportados correctamente")

    def agregar_distrito(self):
        ventana = tk.Toplevel(self.parent)
        ventana.title("➕ Agregar Distrito")
        self._estilizar_toplevel(ventana)

        container = self._dialog_container(ventana, "➕ Agregar Distrito", "Complete los campos")
        body = container['body']

        tk.Label(body, text="Área:", bg=self.COLORS['white']).pack(pady=(0, 4), anchor='w')
        combo_area = ttk.Combobox(body, state="readonly", values=sorted(self.areas_by_name.keys()))
        combo_area.pack(fill='x')

        tk.Label(body, text="Nombre:", bg=self.COLORS['white']).pack(pady=(8, 4), anchor='w')
        nombre = ttk.Entry(body, width=40)
        nombre.pack(fill='x')

        def guardar():
            nom = nombre.get().strip()
            area_nombre = combo_area.get()
            if not nom or not area_nombre:
                messagebox.showwarning("Advertencia", "Complete todos los campos")
                return
            if nom in self.distritos_by_name:
                messagebox.showwarning("Advertencia", "El distrito ya existe")
                return
            area_id = self.areas_by_name.get(area_nombre)
            d_id = agregar_distrito(nom, area_id)
            self.distritos_by_id[d_id] = {'id': d_id, 'nombre': nom, 'area_id': area_id, 'area_nombre': area_nombre}
            self.distritos_by_name[nom] = d_id
            self.distritos_by_area.setdefault(area_id, []).append({'id': d_id, 'nombre': nom})
            self.actualizar_distritos()
            ventana.destroy()
            messagebox.showinfo("Éxito", "Distrito agregado correctamente")

        self._dialog_buttons(container['buttons'], guardar, ventana.destroy)

    def editar_distrito(self):
        selected = self.tree_distritos.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un distrito para editar")
            return

        item = self.tree_distritos.item(selected[0])
        old_name = item['values'][0]
        old_area_name = item['values'][1]

        ventana = tk.Toplevel(self.parent)
        ventana.title("✏️ Editar Distrito")
        self._estilizar_toplevel(ventana)

        container = self._dialog_container(ventana, "✏️ Editar Distrito", "Modifique los datos del distrito")
        body = container['body']

        tk.Label(body, text="Área:", bg=self.COLORS['white']).pack(pady=(0, 4), anchor='w')
        combo_area = ttk.Combobox(body, state="readonly", values=sorted(self.areas_by_name.keys()))
        combo_area.set(old_area_name or '')
        combo_area.pack(fill='x')

        tk.Label(body, text="Nuevo nombre:", bg=self.COLORS['white']).pack(pady=(8, 4), anchor='w')
        nuevo_nombre = ttk.Entry(body, width=40)
        nuevo_nombre.insert(0, old_name)
        nuevo_nombre.pack(fill='x')

        def guardar():
            new_name = nuevo_nombre.get().strip()
            new_area_name = combo_area.get()
            if not new_name or not new_area_name:
                messagebox.showwarning("Advertencia", "Complete todos los campos")
                return
            d_id = self.distritos_by_name.get(old_name)
            new_area_id = self.areas_by_name.get(new_area_name)
            actualizar_distrito(d_id, new_name, new_area_id)
            self.distritos_by_name.pop(old_name, None)
            self.distritos_by_name[new_name] = d_id
            self.distritos_by_id[d_id].update({'nombre': new_name, 'area_id': new_area_id, 'area_nombre': new_area_name})
            for aid in list(self.distritos_by_area.keys()):
                self.distritos_by_area[aid] = [d for d in self.distritos_by_area[aid] if d['id'] != d_id]
                if not self.distritos_by_area[aid]:
                    self.distritos_by_area.pop(aid, None)
            self.distritos_by_area.setdefault(new_area_id, []).append({'id': d_id, 'nombre': new_name})
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
            d_name = item['values'][0]
            d_id = self.distritos_by_name.get(d_name)
            eliminar_distrito(d_id)
            self.distritos_by_name.pop(d_name, None)
            info = self.distritos_by_id.pop(d_id, {})
            aid = info.get('area_id')
            if aid in self.distritos_by_area:
                self.distritos_by_area[aid] = [d for d in self.distritos_by_area[aid] if d['id'] != d_id]
                if not self.distritos_by_area[aid]:
                    self.distritos_by_area.pop(aid, None)
            if d_id in self.tipos_by_distrito:
                self.tipos_by_distrito.pop(d_id, None)
            self.actualizar_distritos()
            if self._tipos_loaded:
                self._refresh_cache_tipos()
                self.actualizar_tipos()
            if self._servicios_loaded:
                self._refresh_cache_tipos()
                self._refresh_cache_servicios()
                self.actualizar_servicios()
            messagebox.showinfo("Éxito", "Distrito eliminado correctamente")

    def actualizar_distritos(self):
        self.tree_distritos.configure(displaycolumns=())
        self.tree_distritos.delete(*self.tree_distritos.get_children())
        rows = []
        for d in self.distritos_by_id.values():
            area_nombre = d.get('area_nombre') or self.areas_by_id.get(d.get('area_id')) or ''
            rows.append((d['nombre'], area_nombre))
        for nombre, area in sorted(rows, key=lambda r: (r[1].lower(), r[0].lower())):
            self.tree_distritos.insert('', 'end', values=(nombre, area))
        self.tree_distritos.configure(displaycolumns=('nombre', 'area'))
        self.tree_distritos.update_idletasks()

    # ================== TIPOS DE SERVICIO ==================
    def setup_tipos_tab(self):
        frame_excel = self._card_section(self.tab_tipos, "Carga desde Excel", "📥")
        tk.Button(frame_excel, text="📂 Cargar Excel",
                bg=self.COLORS['accent'], fg='white', relief='flat', padx=10, pady=5,
                command=self.cargar_excel_tipos).pack(side="left", padx=(0, 8), pady=2)
        tk.Button(frame_excel, text="📤 Exportar a Excel",
                bg=self.COLORS['accent'], fg='white', relief='flat', padx=10, pady=5,
                command=self.exportar_excel_tipos).pack(side="left", padx=(0, 8), pady=2)

        frame_lista = self._card_section(self.tab_tipos, "Tipos de Servicio", "🧾")

        table_wrap = tk.Frame(frame_lista, bg=self.COLORS['white'])
        table_wrap.pack(fill='both', expand=True)

        self.tree_tipos = ttk.Treeview(table_wrap, columns=('distrito', 'descripcion'), show='headings', height=10)
        self.tree_tipos.heading('distrito', text='Distrito', anchor='w')
        self.tree_tipos.heading('descripcion', text='Tipo de Servicio', anchor='w')
        self.tree_tipos.column('distrito', width=240, anchor='w', stretch=True)
        self.tree_tipos.column('descripcion', width=280, anchor='w', stretch=True)

        # Scrollbar vertical mejorada
        scrolly_tipos = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree_tipos.yview)
        self.tree_tipos.configure(yscrollcommand=scrolly_tipos.set)
        
        scrolly_tipos.pack(side='right', fill='y')
        self.tree_tipos.pack(side='left', fill='both', expand=True, pady=2)

        btns = tk.Frame(frame_lista, bg=self.COLORS['white'])
        btns.pack(fill='x', padx=0, pady=(6, 0))
        tk.Button(btns, text="➕ Agregar", bg=self.COLORS['accent'], fg='white',
                relief='flat', padx=10, pady=5, command=self.agregar_tipo).pack(side='left', padx=(0, 6))
        tk.Button(btns, text="✏️ Editar", bg=self.COLORS['accent'], fg='white',
                relief='flat', padx=10, pady=5, command=self.editar_tipo).pack(side='left', padx=(0, 6))
        tk.Button(btns, text="🗑️ Eliminar", bg=self.COLORS['accent'], fg='white',
                relief='flat', padx=10, pady=5, command=self.eliminar_tipo).pack(side='left')

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
                distrito = str(row['Distrito']).strip()
                tipo = str(row['Tipo de Servicio']).strip()
                if not distrito or not tipo:
                    continue

                d_id = self.distritos_by_name.get(distrito)
                if not d_id:
                    d_id = agregar_distrito(distrito, None)
                    self.distritos_by_id[d_id] = {'id': d_id, 'nombre': distrito, 'area_id': None, 'area_nombre': None}
                    self.distritos_by_name[distrito] = d_id

                if any(t['descripcion'] == tipo for t in self.tipos_by_distrito.get(d_id, [])):
                    registros_existentes += 1
                    continue

                agregar_tipo_servicio(d_id, tipo)
                self.tipos_by_distrito.setdefault(d_id, []).append({'id': None, 'descripcion': tipo})
                registros_procesados += 1

            self._refresh_cache_tipos()
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
        for d_id, tipos in self.tipos_by_distrito.items():
            d_name = self.distritos_by_id.get(d_id, {}).get('nombre', '')
            for t in tipos:
                datos.append({'Distrito': d_name, 'Tipo de Servicio': t['descripcion']})
        df = pd.DataFrame(datos)
        df = df.sort_values(by=['Distrito','Tipo de Servicio'])
        df.to_excel(filename, index=False)
        messagebox.showinfo("Éxito", "Tipos de servicio exportados correctamente")

    def agregar_tipo(self):
        ventana = tk.Toplevel(self.parent)
        ventana.title("➕ Agregar Tipo de Servicio")
        self._estilizar_toplevel(ventana)

        container = self._dialog_container(ventana, "➕ Agregar Tipo de Servicio", "Complete los campos")
        body = container['body']

        tk.Label(body, text="Área:", bg=self.COLORS['white']).pack(pady=(0, 4), anchor='w')
        combo_area = ttk.Combobox(body, state="readonly", values=sorted(self.areas_by_name.keys()))
        combo_area.pack(fill='x')

        tk.Label(body, text="Distrito:", bg=self.COLORS['white']).pack(pady=(8, 4), anchor='w')
        combo_distrito = ttk.Combobox(body, state="readonly")
        combo_distrito.pack(fill='x')

        def actualizar_distritos(event=None):
            area_nombre = combo_area.get()
            id_area = self.areas_by_name.get(area_nombre)
            distritos = self.distritos_by_area.get(id_area, [])
            combo_distrito['values'] = [d['nombre'] for d in distritos]
            combo_distrito.set('')

        combo_area.bind("<<ComboboxSelected>>", actualizar_distritos)

        tk.Label(body, text="Tipo de Servicio:", bg=self.COLORS['white']).pack(pady=(8, 4), anchor='w')
        descripcion = ttk.Entry(body, width=40)
        descripcion.pack(fill='x')

        def guardar():
            if not combo_area.get() or not combo_distrito.get() or not descripcion.get().strip():
                messagebox.showwarning("Advertencia", "Complete todos los campos")
                return

            d_id = self.distritos_by_name.get(combo_distrito.get())
            tipo = descripcion.get().strip()
            if any(t['descripcion'] == tipo for t in self.tipos_by_distrito.get(d_id, [])):
                messagebox.showwarning("Advertencia", "Ya existe un tipo de servicio con ese nombre en el distrito seleccionado")
                return

            agregar_tipo_servicio(d_id, tipo)
            self.tipos_by_distrito[d_id] = obtener_tipos_servicio_por_distrito(d_id) or []
            self._tipos_loaded = True
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

        tk.Label(body, text="Área:", bg=self.COLORS['white']).pack(pady=(0, 4), anchor='w')
        combo_area = ttk.Combobox(body, state="readonly", values=sorted(self.areas_by_name.keys()))
        combo_area.pack(fill='x')

        tk.Label(body, text="Distrito:", bg=self.COLORS['white']).pack(pady=(8, 4), anchor='w')
        combo_distrito = ttk.Combobox(body, state="readonly")
        combo_distrito.pack(fill='x')

        def actualizar_distritos(event=None):
            area_nombre = combo_area.get()
            id_area = self.areas_by_name.get(area_nombre)
            distritos = self.distritos_by_area.get(id_area, [])
            combo_distrito['values'] = [d['nombre'] for d in distritos]

        combo_area.bind("<<ComboboxSelected>>", actualizar_distritos)

        distrito_actual = item['values'][0]
        area_actual = self.distritos_by_id.get(self.distritos_by_name.get(distrito_actual), {}).get('area_nombre', '')
        combo_area.set(area_actual or '')
        actualizar_distritos(None)
        combo_distrito.set(distrito_actual)

        tk.Label(body, text="Tipo de Servicio:", bg=self.COLORS['white']).pack(pady=(8, 4), anchor='w')
        descripcion = ttk.Entry(body, width=40)
        descripcion.insert(0, item['values'][1])
        descripcion.pack(fill='x')

        def guardar():
            if not combo_area.get() or not combo_distrito.get() or not descripcion.get().strip():
                messagebox.showwarning("Advertencia", "Complete todos los campos")
                return
            d_name = item['values'][0]
            t_old_desc = item['values'][1]
            t_id = self.obtener_id_tipo_servicio(t_old_desc, d_name)
            actualizar_tipo_servicio(t_id, descripcion.get().strip())
            d_id = self.distritos_by_name.get(d_name)
            self.tipos_by_distrito[d_id] = obtener_tipos_servicio_por_distrito(d_id) or []
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
            t_id = self.obtener_id_tipo_servicio(item['values'][1], item['values'][0])
            eliminar_tipo_servicio(t_id)
            d_id = self.distritos_by_name.get(item['values'][0])
            self.tipos_by_distrito[d_id] = [t for t in self.tipos_by_distrito.get(d_id, []) if t.get('id') != t_id and t.get('descripcion') != item['values'][1]]
            self.servicios_by_tipo.pop(t_id, None)
            self.actualizar_tipos()
            if self._servicios_loaded:
                self._refresh_cache_servicios()
                self.actualizar_servicios()
            messagebox.showinfo("Éxito", "Tipo de servicio eliminado correctamente")

    def actualizar_tipos(self):
        self.tree_tipos.configure(displaycolumns=())
        self.tree_tipos.delete(*self.tree_tipos.get_children())
        rows = []
        for d_id, tipos in self.tipos_by_distrito.items():
            d_name = self.distritos_by_id.get(d_id, {}).get('nombre', '')
            for t in tipos:
                rows.append((d_name, t['descripcion']))
        for dname, desc in sorted(rows, key=lambda r: (r[0].lower(), r[1].lower())):
            self.tree_tipos.insert('', 'end', values=(dname, desc))
        self.tree_tipos.configure(displaycolumns=('distrito', 'descripcion'))
        self.tree_tipos.update_idletasks()

    # ================== SERVICIOS ==================
    def setup_servicios_tab(self):
        frame_excel = self._card_section(self.tab_servicios, "Carga desde Excel", "📥")
        tk.Button(frame_excel, text="📂 Cargar Excel",
                bg=self.COLORS['accent'], fg='white', relief='flat', padx=10, pady=5,
                command=self.cargar_excel_servicios).pack(side="left", padx=(0, 8), pady=2)
        tk.Button(frame_excel, text="📤 Exportar a Excel",
                bg=self.COLORS['accent'], fg='white', relief='flat', padx=10, pady=5,
                command=self.exportar_excel_servicios).pack(side="left", padx=(0, 8), pady=2)

        frame_lista = self._card_section(self.tab_servicios, "Servicios", "🛎️")

        table_wrap = tk.Frame(frame_lista, bg=self.COLORS['white'])
        table_wrap.pack(fill='both', expand=True)

        self.tree_servicios = ttk.Treeview(table_wrap, columns=('distrito', 'tipo', 'nombre'), show='headings', height=10)
        self.tree_servicios.heading('distrito', text='Distrito', anchor='w')
        self.tree_servicios.heading('tipo', text='Tipo de Servicio', anchor='w')
        self.tree_servicios.heading('nombre', text='Servicio', anchor='w')
        self.tree_servicios.column('distrito', width=220, anchor='w', stretch=True)
        self.tree_servicios.column('tipo', width=260, anchor='w', stretch=True)
        self.tree_servicios.column('nombre', width=260, anchor='w', stretch=True)

        # Scrollbar vertical mejorada
        scrolly_servicios = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree_servicios.yview)
        self.tree_servicios.configure(yscrollcommand=scrolly_servicios.set)
        
        scrolly_servicios.pack(side='right', fill='y')
        self.tree_servicios.pack(side='left', fill='both', expand=True, pady=2)

        btns = tk.Frame(frame_lista, bg=self.COLORS['white'])
        btns.pack(fill='x', padx=0, pady=(6, 0))
        tk.Button(btns, text="➕ Agregar", bg=self.COLORS['accent'], fg='white',
                relief='flat', padx=10, pady=5, command=self.agregar_servicio).pack(side='left', padx=(0, 6))
        tk.Button(btns, text="✏️ Editar", bg=self.COLORS['accent'], fg='white',
                relief='flat', padx=10, pady=5, command=self.editar_servicio).pack(side='left', padx=(0, 6))
        tk.Button(btns, text="🗑️ Eliminar", bg=self.COLORS['accent'], fg='white',
                relief='flat', padx=10, pady=5, command=self.eliminar_servicio).pack(side='left')

    def cargar_excel_servicios(self):
        filename = filedialog.askopenfilename(title="Seleccionar archivo Excel de Servicios", filetypes=[("Excel files", "*.xlsx *.xls")])
        if not filename:
            return
        df = pd.read_excel(filename)
        required_columns = ['Distrito', 'Tipo de Servicio', 'Servicio']
        if not all(col in df.columns for col in required_columns):
            messagebox.showerror("Error", "El archivo debe tener las columnas: Distrito, Tipo de Servicio, Servicio")
            return
        nuevos = 0
        existentes = 0
        for _, row in df.iterrows():
            distrito = str(row['Distrito']).strip()
            tipo = str(row['Tipo de Servicio']).strip()
            servicio = str(row['Servicio']).strip()
            if not (distrito and tipo and servicio):
                continue
            d_id = self.distritos_by_name.get(distrito)
            if not d_id:
                d_id = agregar_distrito(distrito, None)
                self.distritos_by_id[d_id] = {'id': d_id, 'nombre': distrito, 'area_id': None, 'area_nombre': None}
                self.distritos_by_name[distrito] = d_id

            t_id = self.obtener_id_tipo_servicio(tipo, distrito)
            if not t_id:
                agregar_tipo_servicio(d_id, tipo)
                self.tipos_by_distrito[d_id] = obtener_tipos_servicio_por_distrito(d_id) or []
                t_id = self.obtener_id_tipo_servicio(tipo, distrito)

            if any(s['nombre'] == servicio for s in self.servicios_by_tipo.get(t_id, [])):
                existentes += 1
                continue

            try:
                agregar_servicio(t_id, servicio)
                self.servicios_by_tipo.setdefault(t_id, []).append({'id': None, 'nombre': servicio})
                nuevos += 1
            except Exception:
                existentes += 1

        self._refresh_cache_servicios()
        self.actualizar_servicios()
        messagebox.showinfo("Éxito", f"Servicios cargados.\nNuevos: {nuevos}\nExistentes: {existentes}")

    def exportar_excel_servicios(self):
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if not filename:
            return
        datos = []
        dname_by_id = {d_id: d['nombre'] for d_id, d in self.distritos_by_id.items()}
        for t_id, servicios in self.servicios_by_tipo.items():
            d_id = next((d for (tid, d, _desc) in self.tipos_flat if tid == t_id), None)
            d_name = dname_by_id.get(d_id, '')
            t_desc = next((desc for (tid, _d, desc) in self.tipos_flat if tid == t_id), '')
            for s in servicios:
                datos.append({'Distrito': d_name, 'Tipo de Servicio': t_desc, 'Servicio': s['nombre']})
        df = pd.DataFrame(datos).sort_values(by=['Distrito','Tipo de Servicio','Servicio'])
        df.to_excel(filename, index=False)
        messagebox.showinfo("Éxito", "Servicios exportados correctamente")

    def agregar_servicio(self):
        ventana = tk.Toplevel(self.parent)
        ventana.title("➕ Agregar Servicio")
        self._estilizar_toplevel(ventana)

        container = self._dialog_container(ventana, "➕ Agregar Servicio", "Complete los campos")
        body = container['body']

        tk.Label(body, text="Área:", bg=self.COLORS['white']).pack(pady=(0, 4), anchor='w')
        combo_area = ttk.Combobox(body, state="readonly", values=sorted(self.areas_by_name.keys()))
        combo_area.pack(fill='x')

        tk.Label(body, text="Distrito:", bg=self.COLORS['white']).pack(pady=(8, 4), anchor='w')
        combo_distrito = ttk.Combobox(body, state="readonly")
        combo_distrito.pack(fill='x')

        tk.Label(body, text="Tipo de Servicio:", bg=self.COLORS['white']).pack(pady=(8, 4), anchor='w')
        combo_tipo = ttk.Combobox(body, state="readonly")
        combo_tipo.pack(fill='x')

        def actualizar_distritos(event=None):
            area_nombre = combo_area.get()
            id_area = self.areas_by_name.get(area_nombre)
            distritos = self.distritos_by_area.get(id_area, [])
            combo_distrito['values'] = [d['nombre'] for d in distritos]
            combo_distrito.set('')
            combo_tipo.set('')
            combo_tipo['values'] = []

        def actualizar_tipos(event=None):
            d_id = self.distritos_by_name.get(combo_distrito.get())
            tipos = self.tipos_by_distrito.get(d_id, [])
            combo_tipo['values'] = [t['descripcion'] for t in tipos]
            combo_tipo.set('')

        combo_area.bind("<<ComboboxSelected>>", actualizar_distritos)
        combo_distrito.bind("<<ComboboxSelected>>", actualizar_tipos)

        tk.Label(body, text="Servicio:", bg=self.COLORS['white']).pack(pady=(8, 4), anchor='w')
        nombre = ttk.Entry(body, width=40)
        nombre.pack(fill='x')

        def guardar():
            if not combo_area.get() or not combo_distrito.get() or not combo_tipo.get() or not nombre.get().strip():
                messagebox.showwarning("Advertencia", "Complete todos los campos")
                return
            d_name = combo_distrito.get()
            t_desc = combo_tipo.get()
            t_id = self.obtener_id_tipo_servicio(t_desc, d_name)
            if any(s['nombre'] == nombre.get().strip() for s in self.servicios_by_tipo.get(t_id, [])):
                messagebox.showwarning("Advertencia", "Ya existe un servicio con ese nombre")
                return
            agregar_servicio(t_id, nombre.get().strip())
            self.servicios_by_tipo[t_id] = obtener_servicios_por_tipo(t_id) or []
            self._servicios_loaded = True
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

        tk.Label(body, text="Área:", bg=self.COLORS['white']).pack(pady=(0, 4), anchor='w')
        combo_area = ttk.Combobox(body, state="readonly", values=sorted(self.areas_by_name.keys()))
        combo_area.pack(fill='x')

        tk.Label(body, text="Distrito:", bg=self.COLORS['white']).pack(pady=(8, 4), anchor='w')
        combo_distrito = ttk.Combobox(body, state="readonly")
        combo_distrito.pack(fill='x')

        tk.Label(body, text="Tipo de Servicio:", bg=self.COLORS['white']).pack(pady=(8, 4), anchor='w')
        combo_tipo = ttk.Combobox(body, state="readonly")
        combo_tipo.pack(fill='x')

        def actualizar_distritos(event=None):
            area_nombre = combo_area.get()
            id_area = self.areas_by_name.get(area_nombre)
            distritos = self.distritos_by_area.get(id_area, [])
            combo_distrito['values'] = [d['nombre'] for d in distritos]
            if item['values'][0] not in [d['nombre'] for d in distritos]:
                combo_distrito.set('')

        def actualizar_tipos(event=None):
            d_id = self.distritos_by_name.get(combo_distrito.get())
            tipos = self.tipos_by_distrito.get(d_id, [])
            combo_tipo['values'] = [t['descripcion'] for t in tipos]
            if item['values'][1] not in [t['descripcion'] for t in tipos]:
                combo_tipo.set('')

        combo_area.bind("<<ComboboxSelected>>", actualizar_distritos)
        combo_distrito.bind("<<ComboboxSelected>>", actualizar_tipos)

        d_name = item['values'][0]
        t_desc = item['values'][1]
        s_name = item['values'][2]
        area_actual = self.distritos_by_id.get(self.distritos_by_name.get(d_name), {}).get('area_nombre', '')
        combo_area.set(area_actual or '')
        actualizar_distritos(None)
        combo_distrito.set(d_name)
        actualizar_tipos(None)
        combo_tipo.set(t_desc)

        tk.Label(body, text="Servicio:", bg=self.COLORS['white']).pack(pady=(8, 4), anchor='w')
        nombre = ttk.Entry(body, width=40)
        nombre.insert(0, s_name)
        nombre.pack(fill='x')

        def guardar():
            new_name = nombre.get().strip()
            if not combo_area.get() or not combo_distrito.get() or not combo_tipo.get() or not new_name:
                messagebox.showwarning("Advertencia", "Complete todos los campos")
                return
            s_id = self.obtener_id_servicio(s_name, t_desc, d_name)
            actualizar_servicio(s_id, new_name)
            t_id = self.obtener_id_tipo_servicio(combo_tipo.get(), combo_distrito.get())
            self.servicios_by_tipo[t_id] = obtener_servicios_por_tipo(t_id) or []
            self.actualizar_servicios()
            ventana.destroy()
            messagebox.showinfo("Éxito", "Servicio actualizado correctamente")

    def eliminar_servicio(self):
        selected = self.tree_servicios.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un servicio para eliminar")
            return
        item = self.tree_servicios.item(selected[0])
        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este servicio?"):
            s_id = self.obtener_id_servicio(item['values'][2], item['values'][1], item['values'][0])
            eliminar_servicio(s_id)
            t_id = self.obtener_id_tipo_servicio(item['values'][1], item['values'][0])
            self.servicios_by_tipo[t_id] = [s for s in self.servicios_by_tipo.get(t_id, []) if s.get('id') != s_id and s.get('nombre') != item['values'][2]]
            self.actualizar_servicios()
            messagebox.showinfo("Éxito", "Servicio eliminado correctamente")

    def actualizar_servicios(self):
        self.tree_servicios.configure(displaycolumns=())
        self.tree_servicios.delete(*self.tree_servicios.get_children())
        rows = []
        dname_by_id = {d_id: d['nombre'] for d_id, d in self.distritos_by_id.items()}
        tdesc_by_id = {t_id: desc for (t_id, _d, desc) in self.tipos_flat}
        d_by_tipo = {t_id: d_id for (t_id, d_id, _desc) in self.tipos_flat}
        for t_id, servicios in self.servicios_by_tipo.items():
            d_id = d_by_tipo.get(t_id)
            d_name = dname_by_id.get(d_id, '')
            t_desc = tdesc_by_id.get(t_id, '')
            for s in servicios:
                rows.append((d_name, t_desc, s['nombre']))
        for dname, tdesc, sname in sorted(rows, key=lambda r: (r[0].lower(), r[1].lower(), r[2].lower())):
            self.tree_servicios.insert('', 'end', values=(dname, tdesc, sname))
        self.tree_servicios.configure(displaycolumns=('distrito', 'tipo', 'nombre'))
        self.tree_servicios.update_idletasks()

    def _actualizar_scrollbars(self):
        """Método para forzar la actualización de todos los scrollbars"""
        if hasattr(self, 'tree_areas'):
            self.tree_areas.update_idletasks()
        if hasattr(self, 'tree_distritos'):
            self.tree_distritos.update_idletasks()
        if hasattr(self, 'tree_tipos'):
            self.tree_tipos.update_idletasks()
        if hasattr(self, 'tree_servicios'):
            self.tree_servicios.update_idletasks()
    
    # ---------- Diálogos y Toplevel estilizados (local) ----------
    def _estilizar_toplevel(self, ventana):
        try:
            ventana.configure(bg=self.COLORS['light'])
        except Exception:
            pass
        ventana.geometry("420x320")
        self.centrar_ventana(ventana)

    def _dialog_container(self, ventana, title_text, subtitle_text):
        outer = tk.Frame(ventana, bg=self.COLORS['light'])
        outer.pack(fill='both', expand=True, padx=10, pady=10)

        header = tk.Frame(outer, bg=self.COLORS['primary'])
        header.pack(fill='x', pady=(0, 8))
        tk.Label(header, text=title_text, font=('Segoe UI', 10, 'bold'),
                 fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(side='left', padx=10, pady=4)
        tk.Label(header, text=subtitle_text, font=('Segoe UI', 8),
                 fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(side='left', padx=10)

        body = tk.Frame(outer, bg=self.COLORS['white'])
        body.pack(fill='both', expand=True, padx=10, pady=8)

        buttons = tk.Frame(outer, bg=self.COLORS['light'])
        buttons.pack(fill='x', pady=(8, 0), anchor='e')

        return {'outer': outer, 'body': body, 'buttons': buttons}

    def _dialog_buttons(self, container_buttons, on_accept, on_cancel):
        tk.Button(container_buttons, text="✔️ Aceptar",
                  bg=self.COLORS['accent'], fg='white', relief='flat', padx=10, pady=5,
                  command=on_accept).pack(side='right', padx=6)
        tk.Button(container_buttons, text="✖️ Cancelar",
                  bg=self.COLORS['accent'], fg='white', relief='flat', padx=10, pady=5,
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