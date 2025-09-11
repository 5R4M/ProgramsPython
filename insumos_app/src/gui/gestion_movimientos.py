import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import sys
import os

# Agregar el directorio raíz del proyecto al PATH de Python
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from src.database.db_manager import (
    obtener_tipos_movimiento,
    agregar_tipo_movimiento,
    actualizar_tipo_movimiento,
    eliminar_tipo_movimiento,
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


class GestionMovimientos:
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

        content = ttk.Frame(card, style='Card.TFrame')
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
            "🔄 Gestión de Movimientos del Sistema",
            "Administre los tipos de movimiento"
        )

        # Notebook
        nb_container = ttk.Frame(self.parent, style='Light.TFrame')
        nb_container.pack(fill="both", expand=True, padx=10, pady=5)

        self.notebook = ttk.Notebook(nb_container)
        self.notebook.pack(fill="both", expand=True)

        self.tab_tipos = ttk.Frame(self.notebook, style='Light.TFrame')
        self.notebook.add(self.tab_tipos, text="🧾 Tipos de Movimiento")

        self.setup_tipos_tab()

        # Botón cerrar
        button_frame = ttk.Frame(self.parent, style='Light.TFrame')
        button_frame.pack(fill='x', pady=10, padx=10)
        ttk.Button(button_frame, text="↩️ Cerrar", style='Primary.TButton',
                   command=self.cerrar_ventana).pack(anchor='e')

        self.actualizar_tipos()

    def setup_tipos_tab(self):
        # Card: Excel
        frame_excel = self._card_section(self.tab_tipos, "Carga desde Excel", "📥")
        ttk.Button(frame_excel, text="📂 Cargar Excel", style='Primary.TButton',
                   command=self.cargar_excel_tipos).pack(side="left", padx=(0, 8), pady=2)
        ttk.Button(frame_excel, text="📤 Exportar a Excel", style='Primary.TButton',
                   command=self.exportar_excel_tipos).pack(side="left", padx=(0, 8), pady=2)

        # Card: Lista
        frame_lista = self._card_section(self.tab_tipos, "Tipos de Movimiento", "🧾")

        table_wrap = ttk.Frame(frame_lista, style='Card.TFrame')
        table_wrap.pack(fill='both', expand=True)

        self.tree_tipos = ttk.Treeview(table_wrap, columns=('descripcion',), show='headings', style="Custom.Treeview")
        self.tree_tipos.heading('descripcion', text='Tipo de Movimiento', anchor='w')
        self.tree_tipos.column('descripcion', anchor='w', width=380)
        self.tree_tipos.pack(fill='both', expand=True, side='left', padx=(0, 5), pady=2)

        scrolly = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree_tipos.yview)
        self.tree_tipos.configure(yscrollcommand=scrolly.set)
        scrolly.pack(side='left', fill='y')

        # Botonera horizontal
        btns = ttk.Frame(frame_lista, style='Card.TFrame')
        btns.pack(fill='x', padx=0, pady=(6, 0))
        ttk.Button(btns, text="➕ Agregar", style='Primary.TButton',
                   command=self.agregar_tipo).pack(side='left', padx=(0, 6))
        ttk.Button(btns, text="✏️ Editar", style='Primary.TButton',
                   command=self.editar_tipo).pack(side='left', padx=(0, 6))
        ttk.Button(btns, text="🗑️ Eliminar", style='Primary.TButton',
                   command=self.eliminar_tipo).pack(side='left')

    def cargar_excel_tipos(self):
        filename = filedialog.askopenfilename(title="Seleccionar archivo Excel", filetypes=[("Excel files", "*.xlsx *.xls")])
        if not filename:
            return
        try:
            df = pd.read_excel(filename)
            required_columns = ['Tipo de Movimiento']
            if not all(col in df.columns for col in required_columns):
                messagebox.showerror("Error", "El archivo debe tener la columna: Tipo de Movimiento")
                return

            registros_procesados = 0
            registros_existentes = 0
            tipos_existentes = [t['descripcion'].lower() for t in (obtener_tipos_movimiento() or [])]

            for _, row in df.iterrows():
                descripcion = str(row['Tipo de Movimiento']).strip()
                if not descripcion:
                    continue
                if descripcion.lower() in tipos_existentes:
                    registros_existentes += 1
                    continue
                try:
                    agregar_tipo_movimiento(descripcion)
                    registros_procesados += 1
                    tipos_existentes.append(descripcion.lower())
                except Exception:
                    # Continuar con el siguiente sin romper el flujo
                    pass

            self.actualizar_tipos()
            mensaje = (f"Proceso completado:\n- Registros nuevos agregados: {registros_procesados}\n"
                       f"- Registros existentes omitidos: {registros_existentes}")
            messagebox.showinfo("Éxito", mensaje)
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar el archivo: {str(e)}")

    def exportar_excel_tipos(self):
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if not filename:
            return
        tipos = obtener_tipos_movimiento() or []
        df = pd.DataFrame([{'Tipo de Movimiento': t['descripcion']} for t in tipos])
        try:
            df.to_excel(filename, index=False)
            messagebox.showinfo("Éxito", "Tipos de movimiento exportados correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar el archivo: {str(e)}")

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

    def agregar_tipo(self):
        ventana = tk.Toplevel(self.parent)
        ventana.title("➕ Agregar Tipo de Movimiento")
        try:
            ventana.configure(bg=self.COLORS['light'])
        except Exception:
            pass
        ventana.geometry("420x200")
        self.centrar_ventana(ventana)

        container = self._dialog_container(ventana, "➕ Agregar Tipo de Movimiento", "Ingrese la descripción")
        body = container['body']

        ttk.Label(body, text="Tipo de Movimiento:", style='Light.TLabel').pack(pady=(0, 4), anchor='w')
        descripcion = ttk.Entry(body, width=40)
        descripcion.pack(fill='x')

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

        self._dialog_buttons(container['buttons'], guardar, ventana.destroy)

    def editar_tipo(self):
        selected = self.tree_tipos.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un tipo de movimiento para editar")
            return
        item = self.tree_tipos.item(selected[0])

        ventana = tk.Toplevel(self.parent)
        ventana.title("✏️ Editar Tipo de Movimiento")
        try:
            ventana.configure(bg=self.COLORS['light'])
        except Exception:
            pass
        ventana.geometry("420x200")
        self.centrar_ventana(ventana)

        container = self._dialog_container(ventana, "✏️ Editar Tipo de Movimiento", "Actualice la descripción")
        body = container['body']

        ttk.Label(body, text="Descripción:", style='Light.TLabel').pack(pady=(0, 4), anchor='w')
        descripcion = ttk.Entry(body, width=40)
        descripcion.insert(0, item['values'][0])
        descripcion.pack(fill='x')

        def guardar():
            try:
                tipos = obtener_tipos_movimiento() or []
                id_tipo = next((tipo['id'] for tipo in tipos if tipo['descripcion'] == item['values'][0]), None)
                if id_tipo:
                    actualizar_tipo_movimiento(id_tipo, descripcion.get().strip())
                    self.actualizar_tipos()
                    ventana.destroy()
                    messagebox.showinfo("Éxito", "Tipo de movimiento actualizado correctamente")
                else:
                    messagebox.showerror("Error", "No se encontró el registro seleccionado")
            except Exception as e:
                messagebox.showerror("Error", f"Error al actualizar tipo de movimiento: {str(e)}")

        self._dialog_buttons(container['buttons'], guardar, ventana.destroy)

    def eliminar_tipo(self):
        selected = self.tree_tipos.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un tipo de movimiento para eliminar")
            return
        item = self.tree_tipos.item(selected[0])
        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este tipo de movimiento?"):
            try:
                tipos = obtener_tipos_movimiento() or []
                id_tipo = next((tipo['id'] for tipo in tipos if tipo['descripcion'] == item['values'][0]), None)
                if id_tipo:
                    eliminar_tipo_movimiento(id_tipo)
                    self.actualizar_tipos()
                    messagebox.showinfo("Éxito", "Tipo de movimiento eliminado correctamente")
                else:
                    messagebox.showerror("Error", "No se encontró el registro seleccionado")
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar tipo de movimiento: {str(e)}")

    def actualizar_tipos(self):
        try:
            self.tree_tipos.delete(*self.tree_tipos.get_children())
            tipos = obtener_tipos_movimiento()
            if not tipos:
                return
            for tipo in tipos:
                self.tree_tipos.insert('', 'end', values=(tipo['descripcion'],))
        except Exception as e:
            messagebox.showerror("Error", f"Error al actualizar tipos de movimiento: {str(e)}")

    def cerrar_ventana(self):
        try:
            if messagebox.askyesno("Confirmar", "¿Está seguro que desea cerrar esta ventana?"):
                for widget in self.parent.winfo_children():
                    widget.destroy()
                if hasattr(self.main_window, 'show_welcome_screen'):
                    self.main_window.show_welcome_screen()
                else:
                    self.parent.destroy()
        except Exception:
            try:
                self.parent.destroy()
            except:
                pass