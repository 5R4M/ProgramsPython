import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from src.database.db_manager import (
    obtener_usuarios, crear_usuario, actualizar_usuario,
    cambiar_password_usuario, eliminar_usuario, existe_usuario
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
        'text_light':'#7f8c8d'
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

    # Card EXTERIOR con borde (si quieres ver solo el header y el borde externo)
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

    # Combobox y Entry
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

    # Treeview totalmente plano (sin contornos)
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

    # Frame sin contorno (para contenedores internos y botoneras)
    style.configure('NoBorder.TFrame', background=COLORS['white'], relief='flat', borderwidth=0)

    return COLORS, style


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class GestionUsuarios:
    def __init__(self, parent_frame, main_window=None):
        self.parent = parent_frame
        self.main_window = main_window

        self.COLORS, self._style = setup_styles(self.parent.winfo_toplevel())

        # Cache en memoria para minimizar lecturas repetidas
        self._usuarios_cache = []

        self._build_once = False
        self.setup_ui()
        self.cargar_usuarios()

    # Header (título + subtítulo)
    def _header_title_sub(self, parent, title_text, subtitle_text):
        header_frame = tk.Frame(parent, bg=self.COLORS['primary'], height=55)
        header_frame.pack(fill='x', padx=0, pady=(6, 6))
        header_frame.pack_propagate(False)

        header_inner = tk.Frame(header_frame, bg=self.COLORS['primary'])
        header_inner.pack(fill='both', expand=True, padx=15, pady=4)

        tk.Label(header_inner, text=title_text, font=('Segoe UI', 11, 'bold'),
                 fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(anchor='w')
        tk.Label(header_inner, text=subtitle_text, font=('Segoe UI', 8),
                 fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(anchor='w', pady=(1, 0))

    # Card con header azul e icono
    def _card_section(self, parent, title, icon):
        container = ttk.Frame(parent, style='Light.TFrame')
        container.pack(fill='x', padx=10, pady=6)

        card = ttk.Frame(container, style='Card.TFrame')
        card.pack(fill='both', expand=True)

        header = ttk.Frame(card, style='Header.TFrame', height=24)
        header.pack(fill='x')
        header.pack_propagate(False)

        ttk.Label(header, text=f"{icon} {title}", style='Header.TLabel').pack(side='left', padx=10)

        # El contenido AHORA ES SIN BORDE para que no haya recuadro gris interno
        content = ttk.Frame(card, style='NoBorder.TFrame')
        content.pack(fill='both', expand=True, padx=12, pady=8)

        return content

    def setup_ui(self):
        if not self._build_once:
            for widget in self.parent.winfo_children():
                widget.destroy()

            self.root_light = ttk.Frame(self.parent, style='Light.TFrame')
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

            # Contenedor de la tabla: SIN borde (el único borde debe ser el del card exterior)
            self.table_outer = ttk.Frame(frame, style='NoBorder.TFrame')
            self.table_outer.pack(fill="both", expand=True, pady=(4, 8))

            # Wrapper interior SIN borde y con padding simétrico
            self.table_wrap = ttk.Frame(self.table_outer, style='NoBorder.TFrame')
            self.table_wrap.pack(fill="both", expand=True, padx=12, pady=8)

            # Grid interno
            self.table_wrap.grid_columnconfigure(0, weight=1)
            self.table_wrap.grid_rowconfigure(0, weight=1)

            self.tree = ttk.Treeview(
                self.table_wrap,
                columns=columns,
                show="headings",
                style="Custom.Treeview"
            )
            # Quitar contornos/foco nativo del Treeview (por si el tema agrega filetes)
            try:
                self.tree['highlightthickness'] = 0
            except Exception:
                pass
            try:
                self.tree['borderwidth'] = 0
            except Exception:
                pass
            try:
                self.tree['relief'] = 'flat'
            except Exception:
                pass

            scrolly = ttk.Scrollbar(self.table_wrap, orient="vertical", command=self.tree.yview, style='Vertical.TScrollbar')
            scrollx = ttk.Scrollbar(self.table_wrap, orient="horizontal", command=self.tree.xview, style='Horizontal.TScrollbar')
            self.tree.configure(yscrollcommand=scrolly.set, xscrollcommand=scrollx.set)

            self.tree.grid(row=0, column=0, sticky="nsew")
            scrolly.grid(row=0, column=1, sticky="ns")
            scrollx.grid(row=1, column=0, sticky="ew")

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
                    width = 100
                elif col == "username":
                    width = 160
                else:
                    width = 220
                self.tree.column(col, width=width, anchor="w", stretch=True)

            # Botones (en frame sin contorno)
            btn_frame = ttk.Frame(frame, style='NoBorder.TFrame')
            btn_frame.pack(pady=4, anchor='w')

            ttk.Button(btn_frame, text="➕ Crear Usuario", style="Primary.TButton",
                       command=self.crear_usuario).pack(side="left", padx=(0, 8))
            ttk.Button(btn_frame, text="✏️ Editar Usuario", style="Primary.TButton",
                       command=self.editar_usuario).pack(side="left", padx=(0, 8))
            ttk.Button(btn_frame, text="🔐 Cambiar Contraseña", style="Primary.TButton",
                       command=self.cambiar_password).pack(side="left", padx=(0, 8))
            ttk.Button(btn_frame, text="🗑️ Eliminar Usuario", style="Primary.TButton",
                       command=self.eliminar_usuario).pack(side="left", padx=(0, 8))
            ttk.Button(btn_frame, text="↩️ Volver", style="Primary.TButton",
                       command=self.volver).pack(side="left", padx=(0, 8))

            self._build_once = True

    # =============== Rendimiento: carga eficiente ===============
    def cargar_usuarios(self):
        # Traer de DB una sola vez y cachear
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
                'Sí' if int(usuario.get('activo', 0)) == 1 else 'No'
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

# =============== Diálogo optimizado ===============
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

        self.COLORS, self._style = setup_styles(parent.winfo_toplevel())
        super().__init__(parent, title)

    def body(self, master):
        try:
            self.configure(bg=self.COLORS['light'])
        except Exception:
            pass

        container = ttk.Frame(master, style='Light.TFrame', padding=(10, 8))
        container.grid(row=0, column=0, sticky="nsew")
        master.grid_columnconfigure(0, weight=1)
        master.grid_rowconfigure(0, weight=1)

        # Header del diálogo
        header = tk.Frame(container, bg=self.COLORS['primary'])
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        tk.Label(header, text=("➕ Crear Usuario" if self.modo == "crear" else "✏️ Editar Usuario"),
                 font=('Segoe UI', 10, 'bold'),
                 fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(side='left', padx=10, pady=4)
        tk.Label(header, text="Complete los campos y confirme",
                 font=('Segoe UI', 8),
                 fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(side='left', padx=10)

        # Grid
        container.grid_columnconfigure(0, weight=1, minsize=140)
        container.grid_columnconfigure(1, weight=2, minsize=220)
        r = 1

        # Usuario
        ttk.Label(container, text="Usuario:", style='Light.TLabel').grid(row=r, column=0, sticky="w", pady=(0, 5))
        self.username_entry = ttk.Entry(container, width=30)
        self.username_entry.grid(row=r, column=1, sticky="ew", pady=(0, 5))
        self.username_entry.insert(0, self.username)
        if self.modo == "editar":
            self.username_entry.config(state="disabled")
        r += 1

        # Sección de contraseña
        if self.modo == "crear":
            ttk.Label(container, text="Contraseña:", style='Light.TLabel').grid(row=r, column=0, sticky="w", pady=(0, 5))
            self.password_entry = ttk.Entry(container, show="•", width=30)
            self.password_entry.grid(row=r, column=1, sticky="ew", pady=(0, 5))
            r += 1

            ttk.Label(container, text="Confirmar contraseña:", style='Light.TLabel').grid(row=r, column=0, sticky="w", pady=(0, 5))
            self.confirm_password_entry = ttk.Entry(container, show="•", width=30)
            self.confirm_password_entry.grid(row=r, column=1, sticky="ew", pady=(0, 5))
            r += 1
        else:
            self.cambiar_password_var = tk.BooleanVar(value=False)
            chk = ttk.Checkbutton(container, text="Cambiar contraseña", variable=self.cambiar_password_var,
                                  command=self.toggle_password_fields)
            chk.grid(row=r, column=0, columnspan=2, sticky="w", pady=(0, 5))
            r += 1

            self.password_frame = ttk.Frame(container, style='Light.TFrame')
            self.password_frame.grid(row=r, column=0, columnspan=2, sticky="ew")
            self.password_frame.grid_columnconfigure(0, weight=1, minsize=140)
            self.password_frame.grid_columnconfigure(1, weight=2, minsize=220)

            ttk.Label(self.password_frame, text="Nueva contraseña:", style='Light.TLabel').grid(row=0, column=0, sticky="w", pady=(0, 5))
            self.password_entry = ttk.Entry(self.password_frame, show="•", width=30)
            self.password_entry.grid(row=0, column=1, sticky="ew", pady=(0, 5))

            ttk.Label(self.password_frame, text="Confirmar contraseña:", style='Light.TLabel').grid(row=1, column=0, sticky="w", pady=(0, 5))
            self.confirm_password_entry = ttk.Entry(self.password_frame, show="•", width=30)
            self.confirm_password_entry.grid(row=1, column=1, sticky="ew", pady=(0, 5))

            self.password_frame.grid_remove()
            r += 1

        # Nombre completo
        ttk.Label(container, text="Nombre completo:", style='Light.TLabel').grid(row=r, column=0, sticky="w", pady=(0, 5))
        self.nombre_entry = ttk.Entry(container, width=30)
        self.nombre_entry.grid(row=r, column=1, sticky="ew", pady=(0, 5))
        self.nombre_entry.insert(0, self.nombre)
        r += 1

        # Rol
        ttk.Label(container, text="Rol:", style='Light.TLabel').grid(row=r, column=0, sticky="w", pady=(0, 5))
        self.rol_var = tk.StringVar(value=self.rol)
        self.rol_combo = ttk.Combobox(container, textvariable=self.rol_var,
                                      values=["admin", "usuario"], state="readonly", width=28)
        self.rol_combo.grid(row=r, column=1, sticky="ew", pady=(0, 5))
        r += 1

        # Activo
        ttk.Label(container, text="Activo:", style='Light.TLabel').grid(row=r, column=0, sticky="w", pady=(0, 5))
        self.activo_var = tk.IntVar(value=int(self.activo))
        ttk.Checkbutton(container, variable=self.activo_var).grid(row=r, column=1, sticky="w", pady=(0, 5))
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

        # Validación de contraseña cuando corresponde
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
        # Usar un frame sin bordes para quitar el contorno donde están los botones
        box = ttk.Frame(self, style='NoBorder.TFrame')
        box.pack(pady=10)

        ttk.Button(box, text="✔️ Aceptar", width=12, style='Primary.TButton',
                   command=self.ok).pack(side=tk.LEFT, padx=6)
        ttk.Button(box, text="✖️ Cancelar", width=12, style='Primary.TButton',
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

        # Devolver la tupla limpia (sin coma extra ni texto)
        self.result = (username, password, nombre, rol, activo)