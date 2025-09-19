# -*- coding: utf-8 -*-
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from src.database.db_manager import (
    obtener_usuarios, crear_usuario, actualizar_usuario,
    cambiar_password_usuario, eliminar_usuario, existe_usuario
)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # type: ignore
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class GestionUsuarios:
    def __init__(self, parent_frame, main_window=None):
        self.parent = parent_frame
        self.main_window = main_window

        # Paleta local solo para esta vista (no toca estilos globales)
        self.COLORS = {
            'primary':   '#2c3e50',
            'accent':    '#3498db',
            'light':     '#ecf0f1',
            'white':     '#ffffff',
            'text_dark': '#2c3e50'
        }

        # Cache en memoria para minimizar lecturas repetidas
        self._usuarios_cache = []

        self._build_once = False
        self.setup_ui()
        self.cargar_usuarios()

    # Header (título + subtítulo) — local, sin estilos globales
    def _header_title_sub(self, parent, title_text, subtitle_text):
        # Header azul a todo el ancho, pegado arriba, sin separadores laterales
        header_frame = tk.Frame(parent, bg=self.COLORS['primary'], height=55)
        header_frame.pack(fill='x', padx=0, pady=(0, 6))  # sin margen superior ni laterales
        header_frame.pack_propagate(False)

        header_inner = tk.Frame(header_frame, bg=self.COLORS['primary'])
        header_inner.pack(fill='both', expand=True, padx=15, pady=4)  # padding interno para el contenido (conserva tus 15 px)

        tk.Label(header_inner, text=title_text, font=('Segoe UI', 11, 'bold'),
                fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(anchor='w')
        tk.Label(header_inner, text=subtitle_text, font=('Segoe UI', 8),
                fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(anchor='w', pady=(1, 0))

    # Card con header azul e icono — todo con tk Frames/Labels locales
    def _card_section(self, parent, title, icon):
        container = tk.Frame(parent, bg=self.COLORS['light'])
        container.pack(fill='x', padx=10, pady=6)

        card = tk.Frame(container, bg=self.COLORS['white'], bd=1, relief='solid', highlightthickness=0)
        card.pack(fill='both', expand=True)

        header = tk.Frame(card, bg=self.COLORS['primary'], height=26)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(header, text=f"{icon} {title}", font=('Segoe UI', 9, 'bold'),
                 fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(side='left', padx=10)

        content = tk.Frame(card, bg=self.COLORS['white'])
        content.pack(fill='both', expand=True, padx=12, pady=8)

        return content

    def _primary_button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command,
                         font=('Segoe UI', 9, 'bold'),
                         bg=self.COLORS['accent'], fg='white',
                         relief='flat', borderwidth=0, padx=10, pady=5, cursor='hand2',
                         activebackground='#2980b9', activeforeground='white')

    def setup_ui(self):
        if not self._build_once:
            for widget in self.parent.winfo_children():
                widget.destroy()

            # Raíz local de esta vista
            self.root_light = tk.Frame(self.parent, bg=self.COLORS['light'])
            self.root_light.pack(fill='both', expand=True)

            # Header principal
            self._header_title_sub(
                self.root_light,
                "👥 Gestión de Usuarios del Sistema",
                "Administre los usuarios y sus permisos de acceso"
            )

            # Card principal
            frame = self._card_section(self.root_light, "Gestión de Usuarios", "📋")

            # Tabla de usuarios
            columns = ("id", "username", "nombre", "rol", "activo")

            table_outer = tk.Frame(frame, bg=self.COLORS['white'])
            table_outer.pack(fill="both", expand=True, pady=(4, 8))

            table_wrap = tk.Frame(table_outer, bg=self.COLORS['white'])
            table_wrap.pack(fill="both", expand=True, padx=12, pady=8)

            table_wrap.grid_columnconfigure(0, weight=1)
            table_wrap.grid_rowconfigure(0, weight=1)

            self.tree = ttk.Treeview(
                table_wrap,
                columns=columns,
                show="headings"
            )

            # Scroll vertical solamente (removemos horizontal)
            scrolly = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
            self.tree.configure(yscrollcommand=scrolly.set)

            self.tree.grid(row=0, column=0, sticky="nsew")
            scrolly.grid(row=0, column=1, sticky="ns")

            # Encabezados y columnas
            headings = {
                "id": "ID",
                "username": "Usuario",
                "nombre": "Nombre",
                "rol": "Rol",
                "activo": "Activo"
            }
            for col in columns:
                self.tree.heading(col, text=headings.get(col, col.capitalize()), anchor="w")
                if col == "id":
                    width = 60
                elif col in ("rol", "activo"):
                    width = 110
                elif col == "username":
                    width = 180
                else:
                    width = 260
                # anchor left y permitir stretch para evitar scroll horizontal
                self.tree.column(col, width=width, anchor="w", stretch=True)

            # Botones (en frame sin contorno)
            btn_frame = tk.Frame(frame, bg=self.COLORS['white'])
            btn_frame.pack(pady=4, anchor='w')

            self._primary_button(btn_frame, "➕ Crear Usuario", self.crear_usuario).pack(side="left", padx=(0, 8))
            self._primary_button(btn_frame, "✏️ Editar Usuario", self.editar_usuario).pack(side="left", padx=(0, 8))
            self._primary_button(btn_frame, "🔐 Cambiar Contraseña", self.cambiar_password).pack(side="left", padx=(0, 8))
            self._primary_button(btn_frame, "🗑️ Eliminar Usuario", self.eliminar_usuario).pack(side="left", padx=(0, 8))
            self._primary_button(btn_frame, "↩️ Volver", self.volver).pack(side="left", padx=(0, 8))

            self._build_once = True

    # =============== Rendimiento: carga eficiente ===============
    def cargar_usuarios(self):
        try:
            data = obtener_usuarios() or []
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron obtener usuarios: {e}")
            data = []

        self._usuarios_cache = data

        # Congelar el tree para minimizar repaints
        self.tree.configure(displaycolumns=())  # ocultar durante la carga
        self.tree.delete(*self.tree.get_children())

        rows = []
        for usuario in data:
            values = (
                usuario.get('id', ''),
                usuario.get('username', ''),
                usuario.get('nombre_completo', ''),
                usuario.get('rol', ''),
                'Sí' if str(usuario.get('activo', '0')) in ('1', 'True', 'true', 'SI', 'Si', 'sí', 'Sí') else 'No'
            )
            rows.append(values)

        for vals in rows:
            self.tree.insert("", "end", values=vals)

        self.tree.configure(displaycolumns=("id", "username", "nombre", "rol", "activo"))

    # =============== Acciones ===============
    def crear_usuario(self):
        dialog = UsuarioDialog(self.parent, "➕ Crear Usuario", modo="crear")
        if dialog.result:
            username, password, nombre, rol, activo = dialog.result
            try:
                if existe_usuario(username):
                    messagebox.showerror("Error", "El nombre de usuario ya existe")
                    return
                ok = crear_usuario(username, password, nombre, rol, activo)
            except Exception as e:
                ok = False
                messagebox.showerror("Error", f"No se pudo crear el usuario: {e}")
            if ok:
                messagebox.showinfo("Éxito", "Usuario creado correctamente")
                self.cargar_usuarios()

    def editar_usuario(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Seleccione", "Seleccione un usuario para editar")
            return
        item = self.tree.item(selected[0])["values"]
        id_usuario, username, nombre, rol, activo_txt = item
        activo_val = 1 if str(activo_txt).lower().startswith('s') else 0

        dialog = UsuarioDialog(
            self.parent,
            "✏️ Editar Usuario",
            username=username,
            nombre=nombre,
            rol=rol,
            activo=activo_val,
            modo="editar"
        )

        if dialog.result:
            _, password, nombre, rol, activo = dialog.result
            try:
                if password:
                    cambiar_password_usuario(id_usuario, password)
                ok = actualizar_usuario(id_usuario, nombre, rol, int(activo))
            except Exception as e:
                ok = False
                messagebox.showerror("Error", f"No se pudo actualizar: {e}")
            if ok:
                messagebox.showinfo("Éxito", "Usuario actualizado correctamente")
                self.cargar_usuarios()

    def cambiar_password(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Seleccione", "Seleccione un usuario")
            return
        item = self.tree.item(selected[0])["values"]
        id_usuario = item[0]
        new_pass = simpledialog.askstring("🔐 Nueva Contraseña", "Ingrese la nueva contraseña:", show="*")
        if new_pass:
            try:
                ok = cambiar_password_usuario(id_usuario, new_pass)
            except Exception as e:
                ok = False
                messagebox.showerror("Error", f"No se pudo cambiar la contraseña: {e}")
            if ok:
                messagebox.showinfo("Éxito", "Contraseña actualizada")

    def eliminar_usuario(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Seleccione", "Seleccione un usuario")
            return
        item = self.tree.item(selected[0])["values"]
        id_usuario = item[0]
        if messagebox.askyesno("Confirmar", "¿Eliminar este usuario?"):
            try:
                ok = eliminar_usuario(id_usuario)
            except Exception as e:
                ok = False
                messagebox.showerror("Error", f"No se pudo eliminar el usuario: {e}")
            if ok:
                messagebox.showinfo("Éxito", "Usuario eliminado")
                self.cargar_usuarios()

    def volver(self):
        if self.main_window and hasattr(self.main_window, "show_welcome_screen"):
            self.main_window.show_welcome_screen()


# =============== Diálogo ===============
class UsuarioDialog(simpledialog.Dialog):
    def __init__(self, parent, title, username="", password=None, nombre="", rol="usuario", activo=1, modo="crear"):
        self.parent_ref = parent
        self.username = username
        self.password = password
        self.nombre = nombre
        self.rol = rol
        self.activo = activo
        self.modo = modo
        self.result = None

        # Paleta local del diálogo (no global)
        self.COLORS = {
            'primary':   '#2c3e50',
            'accent':    '#3498db',
            'light':     '#ecf0f1',
            'white':     '#ffffff',
            'text_dark': '#2c3e50'
        }
        super().__init__(parent, title)

    def body(self, master):
        # Fondo general del diálogo
        try:
            self.configure(bg=self.COLORS['light'])
        except Exception:
            pass

        container = tk.Frame(master, bg=self.COLORS['white'])
        container.grid(row=0, column=0, sticky="nsew")
        master.grid_columnconfigure(0, weight=1)
        master.grid_rowconfigure(0, weight=1)

        # Card-like: header azul
        header = tk.Frame(container, bg=self.COLORS['primary'])
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        tk.Label(header, text=("➕ Crear Usuario" if self.modo == "crear" else "✏️ Editar Usuario"),
                 font=('Segoe UI', 10, 'bold'),
                 fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(side='left', padx=10, pady=4)
        tk.Label(header, text="Complete los campos y confirme",
                 font=('Segoe UI', 8),
                 fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(side='left', padx=10)

        body = tk.Frame(container, bg=self.COLORS['white'])
        body.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=12, pady=8)

        body.grid_columnconfigure(0, weight=1, minsize=140)
        body.grid_columnconfigure(1, weight=2, minsize=220)
        r = 0

        # Usuario
        tk.Label(body, text="Usuario:", bg=self.COLORS['white'], fg=self.COLORS['text_dark']).grid(row=r, column=0, sticky="w", pady=(0, 5))
        self.username_entry = ttk.Entry(body, width=30)
        self.username_entry.grid(row=r, column=1, sticky="ew", pady=(0, 5))
        self.username_entry.insert(0, self.username)
        if self.modo == "editar":
            self.username_entry.config(state="disabled")
        r += 1

        # Sección de contraseña
        if self.modo == "crear":
            tk.Label(body, text="Contraseña:", bg=self.COLORS['white'], fg=self.COLORS['text_dark']).grid(row=r, column=0, sticky="w", pady=(0, 5))
            self.password_entry = ttk.Entry(body, show="•", width=30)
            self.password_entry.grid(row=r, column=1, sticky="ew", pady=(0, 5))
            r += 1

            tk.Label(body, text="Confirmar contraseña:", bg=self.COLORS['white'], fg=self.COLORS['text_dark']).grid(row=r, column=0, sticky="w", pady=(0, 5))
            self.confirm_password_entry = ttk.Entry(body, show="•", width=30)
            self.confirm_password_entry.grid(row=r, column=1, sticky="ew", pady=(0, 5))
            r += 1
        else:
            self.cambiar_password_var = tk.BooleanVar(value=False)
            chk = ttk.Checkbutton(body, text="Cambiar contraseña", variable=self.cambiar_password_var,
                                  command=self.toggle_password_fields)
            chk.grid(row=r, column=0, columnspan=2, sticky="w", pady=(0, 5))
            r += 1

            self.password_frame = tk.Frame(body, bg=self.COLORS['white'])
            self.password_frame.grid(row=r, column=0, columnspan=2, sticky="ew")
            self.password_frame.grid_columnconfigure(0, weight=1, minsize=140)
            self.password_frame.grid_columnconfigure(1, weight=2, minsize=220)

            tk.Label(self.password_frame, text="Nueva contraseña:", bg=self.COLORS['white'], fg=self.COLORS['text_dark']).grid(row=0, column=0, sticky="w", pady=(0, 5))
            self.password_entry = ttk.Entry(self.password_frame, show="•", width=30)
            self.password_entry.grid(row=0, column=1, sticky="ew", pady=(0, 5))

            tk.Label(self.password_frame, text="Confirmar contraseña:", bg=self.COLORS['white'], fg=self.COLORS['text_dark']).grid(row=1, column=0, sticky="w", pady=(0, 5))
            self.confirm_password_entry = ttk.Entry(self.password_frame, show="•", width=30)
            self.confirm_password_entry.grid(row=1, column=1, sticky="ew", pady=(0, 5))

            self.password_frame.grid_remove()
            r += 1

        # Nombre completo
        tk.Label(body, text="Nombre completo:", bg=self.COLORS['white'], fg=self.COLORS['text_dark']).grid(row=r, column=0, sticky="w", pady=(0, 5))
        self.nombre_entry = ttk.Entry(body, width=30)
        self.nombre_entry.grid(row=r, column=1, sticky="ew", pady=(0, 5))
        self.nombre_entry.insert(0, self.nombre)
        r += 1

        # Rol
        tk.Label(body, text="Rol:", bg=self.COLORS['white'], fg=self.COLORS['text_dark']).grid(row=r, column=0, sticky="w", pady=(0, 5))
        self.rol_var = tk.StringVar(value=self.rol)
        self.rol_combo = ttk.Combobox(body, textvariable=self.rol_var,
                                      values=["admin", "usuario"], state="readonly", width=28)
        self.rol_combo.grid(row=r, column=1, sticky="ew", pady=(0, 5))
        r += 1

        # Activo
        tk.Label(body, text="Activo:", bg=self.COLORS['white'], fg=self.COLORS['text_dark']).grid(row=r, column=0, sticky="w", pady=(0, 5))
        self.activo_var = tk.IntVar(value=int(self.activo))
        ttk.Checkbutton(body, variable=self.activo_var).grid(row=r, column=1, sticky="w", pady=(0, 5))
        r += 1

        return self.username_entry

    def toggle_password_fields(self):
        if getattr(self, 'cambiar_password_var', None) and self.cambiar_password_var.get():
            self.password_frame.grid()
        else:
            self.password_frame.grid_remove()

    def validate(self):
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showerror("Error", "El nombre de usuario es obligatorio")
            return False

        if self.modo == "crear" or (self.modo == "editar" and getattr(self, 'cambiar_password_var', tk.BooleanVar(value=False)).get()):
            password = self.password_entry.get()
            confirm_password = self.confirm_password_entry.get()

            if not password:
                messagebox.showerror("Error", "La contraseña es obligatoria")
                return False
            if password != confirm_password:
                messagebox.showerror("Error", "Las contraseñas no coinciden")
                return False
            if len(password) < 6:
                messagebox.showerror("Error", "La contraseña debe tener al menos 6 caracteres")
                return False

        return True

    def buttonbox(self):
        box = tk.Frame(self, bg=self.COLORS['light'])
        box.pack(pady=10)

        tk.Button(box, text="✔️ Aceptar", width=12,
                  bg=self.COLORS['accent'], fg='white', relief='flat', padx=10, pady=5,
                  command=self.ok).pack(side=tk.LEFT, padx=6)
        tk.Button(box, text="✖️ Cancelar", width=12,
                  bg=self.COLORS['accent'], fg='white', relief='flat', padx=10, pady=5,
                  command=self.cancel).pack(side=tk.LEFT, padx=6)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

    def apply(self):
        username = self.username_entry.get().strip()
        nombre = self.nombre_entry.get().strip()
        rol = self.rol_var.get()
        activo = self.activo_var.get()

        password = None
        if self.modo == "crear":
            password = self.password_entry.get()
        elif self.modo == "editar" and getattr(self, 'cambiar_password_var', tk.BooleanVar(value=False)).get():
            password = self.password_entry.get()

        # Devolver la tupla limpia
        self.result = (username, password, nombre, rol, activo)