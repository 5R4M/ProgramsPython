# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import sys
import os

from src.database.db_manager import (
    obtener_tipos_movimiento,
    agregar_tipo_movimiento,
    actualizar_tipo_movimiento,
    eliminar_tipo_movimiento,
)


# Agregar el directorio raíz del proyecto al PATH de Python
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

class GestionMovimientos:
    def __init__(self, parent_frame, main_window):
        self.parent = parent_frame
        self.main_window = main_window

        # Paleta local (no afecta estilos globales del Main Window)
        self.COLORS = {
            'primary':   '#2c3e50',
            'accent':    '#3498db',
            'light':     '#ecf0f1',
            'white':     '#ffffff',
            'text_dark': '#2c3e50',
        }

        self.setup_ui()
        self.actualizar_tipos()

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

    # ---------- UI principal ----------
    def setup_ui(self):
        # Header principal
        self._header_title_sub(
            self.parent,
            "🔄 Gestión de Movimientos del Sistema",
            "Administre los tipos de movimiento"
        )

        # Notebook
        nb_container = tk.Frame(self.parent, bg=self.COLORS['light'])
        nb_container.pack(fill="both", expand=True, padx=10, pady=5)

        self.notebook = ttk.Notebook(nb_container)
        self.notebook.pack(fill="both", expand=True)

        self.tab_tipos = tk.Frame(self.notebook, bg=self.COLORS['light'])
        self.notebook.add(self.tab_tipos, text="🧾 Tipos de Movimiento")

        self.setup_tipos_tab()

        # Botón cerrar
        button_frame = tk.Frame(self.parent, bg=self.COLORS['light'])
        button_frame.pack(fill='x', pady=10, padx=10)
        tk.Button(button_frame, text="↩️ Cerrar",
                  bg=self.COLORS['accent'], fg='white', relief='flat', padx=10, pady=5,
                  command=self.cerrar_ventana).pack(anchor='e')

    def setup_tipos_tab(self):
        # Card: Excel
        frame_excel = self._card_section(self.tab_tipos, "Carga desde Excel", "📥")
        tk.Button(frame_excel, text="📂 Cargar Excel",
                  bg=self.COLORS['accent'], fg='white', relief='flat', padx=10, pady=5,
                  command=self.cargar_excel_tipos).pack(side="left", padx=(0, 8), pady=2)
        tk.Button(frame_excel, text="📤 Exportar a Excel",
                  bg=self.COLORS['accent'], fg='white', relief='flat', padx=10, pady=5,
                  command=self.exportar_excel_tipos).pack(side="left", padx=(0, 8), pady=2)

        # Card: Lista
        frame_lista = self._card_section(self.tab_tipos, "Tipos de Movimiento", "🧾")

        table_wrap = tk.Frame(frame_lista, bg=self.COLORS['white'])
        table_wrap.pack(fill='both', expand=True)

        # Treeview con solo scroll vertical
        self.tree_tipos = ttk.Treeview(
            table_wrap,
            columns=('descripcion',),
            show='headings'
        )
        self.tree_tipos.heading('descripcion', text='Tipo de Movimiento', anchor='w')
        self.tree_tipos.column('descripcion', anchor='w', width=420, stretch=True)
        self.tree_tipos.configure(selectmode='browse')
        self.tree_tipos.pack(fill='both', expand=True, side='left', padx=(0, 5), pady=2)

        scrolly = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree_tipos.yview)
        self.tree_tipos.configure(yscrollcommand=scrolly.set)
        scrolly.pack(side='left', fill='y')

        # Botonera
        btns = tk.Frame(frame_lista, bg=self.COLORS['white'])
        btns.pack(fill='x', padx=0, pady=(6, 0))
        tk.Button(btns, text="➕ Agregar", bg=self.COLORS['accent'], fg='white',
                  relief='flat', padx=10, pady=5, command=self.agregar_tipo).pack(side='left', padx=(0, 6))
        tk.Button(btns, text="✏️ Editar", bg=self.COLORS['accent'], fg='white',
                  relief='flat', padx=10, pady=5, command=self.editar_tipo).pack(side='left', padx=(0, 6))
        tk.Button(btns, text="🗑️ Eliminar", bg=self.COLORS['accent'], fg='white',
                  relief='flat', padx=10, pady=5, command=self.eliminar_tipo).pack(side='left')

    # ---------- Importar / Exportar ----------
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

    # ---------- Diálogos ----------
    def _estilizar_toplevel(self, ventana, w=420, h=200):
        try:
            ventana.configure(bg=self.COLORS['light'])
        except Exception:
            pass
        ventana.geometry(f"{w}x{h}")
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

    # ---------- CRUD ----------
    def agregar_tipo(self):
        ventana = tk.Toplevel(self.parent)
        ventana.title("➕ Agregar Tipo de Movimiento")
        self._estilizar_toplevel(ventana)

        container = self._dialog_container(ventana, "➕ Agregar Tipo de Movimiento", "Ingrese la descripción")
        body = container['body']

        tk.Label(body, text="Tipo de Movimiento:", bg=self.COLORS['white']).pack(pady=(0, 4), anchor='w')
        descripcion = ttk.Entry(body, width=40)
        descripcion.pack(fill='x')

        def guardar():
            texto = descripcion.get().strip()
            if not texto:
                messagebox.showwarning("Advertencia", "Ingrese la descripción")
                return
            try:
                agregar_tipo_movimiento(texto)
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
        self._estilizar_toplevel(ventana)

        container = self._dialog_container(ventana, "✏️ Editar Tipo de Movimiento", "Actualice la descripción")
        body = container['body']

        tk.Label(body, text="Descripción:", bg=self.COLORS['white']).pack(pady=(0, 4), anchor='w')
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
            self.tree_tipos.configure(displaycolumns=())
            self.tree_tipos.delete(*self.tree_tipos.get_children())
            tipos = obtener_tipos_movimiento() or []
            for tipo in tipos:
                self.tree_tipos.insert('', 'end', values=(tipo['descripcion'],))
            self.tree_tipos.configure(displaycolumns=('descripcion',))
        except Exception as e:
            messagebox.showerror("Error", f"Error al actualizar tipos de movimiento: {str(e)}")

    # ---------- Cierre ----------
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
            except:  # noqa: E722
                pass