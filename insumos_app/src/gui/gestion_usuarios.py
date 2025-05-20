import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from src.database.db_manager import (
    obtener_usuarios, crear_usuario, actualizar_usuario, cambiar_password_usuario, eliminar_usuario, existe_usuario, existe_usuario_otro
)

class GestionUsuarios:
    def __init__(self, parent_frame, main_window=None):
        self.parent = parent_frame
        self.main_window = main_window
        self.setup_ui()
        self.cargar_usuarios()

    def setup_ui(self):
        for widget in self.parent.winfo_children():
            widget.destroy()
        frame = ttk.LabelFrame(self.parent, text="Gestión de Usuarios")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Tabla de usuarios
        columns = ("id", "username", "nombre", "rol", "activo")
        self.tree_frame = ttk.Frame(frame)
        self.tree_frame.pack(fill="both", expand=True, pady=10)

        self.tree_scroll_y = ttk.Scrollbar(self.tree_frame, orient="vertical")
        self.tree_scroll_x = ttk.Scrollbar(self.tree_frame, orient="horizontal")

        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=self.tree_scroll_y.set,
            xscrollcommand=self.tree_scroll_x.set
        )

        self.tree_scroll_y.config(command=self.tree.yview)
        self.tree_scroll_x.config(command=self.tree.xview)

        self.tree_scroll_y.pack(side="right", fill="y")
        self.tree_scroll_x.pack(side="bottom", fill="x")

        for col in columns:
            self.tree.heading(col, text=col.capitalize(), anchor="center")
            self.tree.column(col, width=80, anchor="center")  # Reducido el tamaño
        self.tree.pack(fill="both", expand=True)

        # Botones
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Crear Usuario", command=self.crear_usuario).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Editar Usuario", command=self.editar_usuario).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cambiar Contraseña", command=self.cambiar_password).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Eliminar Usuario", command=self.eliminar_usuario).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Volver", command=self.volver).pack(side="left", padx=5)

    def cargar_usuarios(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for usuario in obtener_usuarios():
            # Acceder a los valores por índice o nombre de columna
            values = (
                usuario['id'],         # o usuario[0]
                usuario['username'],   # o usuario[1]
                usuario['nombre_completo'],  # o usuario[2]
                usuario['rol'],        # o usuario[3]
                usuario['activo']       # o usuario[4]
            )
            self.tree.insert("", "end", values=values)

    def crear_usuario(self):
        dialog = UsuarioDialog(self.parent, "Crear Usuario", modo="crear")
        if dialog.result:
            username, password, nombre, rol, activo = dialog.result

            # Verificar si el usuario ya existe
            if existe_usuario(username):
                messagebox.showerror("Error", "El nombre de usuario ya existe")
                return

            if crear_usuario(username, password, nombre, rol, activo):
                messagebox.showinfo("Éxito", "Usuario creado correctamente")
                self.cargar_usuarios()
            else:
                messagebox.showerror("Error", "No se pudo crear el usuario")

    def editar_usuario(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Seleccione", "Seleccione un usuario para editar")
            return

        item = self.tree.item(selected[0])["values"]
        id_usuario, username, nombre, rol, activo = item

        dialog = UsuarioDialog(
            self.parent,
            "Editar Usuario",
            username=username,
            nombre=nombre,
            rol=rol,
            activo=activo,
            modo="editar"
        )

        if dialog.result:
            _, password, nombre, rol, activo = dialog.result

            # Si hay contraseña, actualizarla
            if password:
                cambiar_password_usuario(id_usuario, password)

            # Actualizar resto de datos
            if actualizar_usuario(id_usuario, nombre, rol, int(activo)):
                messagebox.showinfo("Éxito", "Usuario actualizado correctamente")
                self.cargar_usuarios()
            else:
                messagebox.showerror("Error", "No se pudo actualizar el usuario")

    def cambiar_password(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Seleccione", "Seleccione un usuario")
            return
        item = self.tree.item(selected[0])["values"]
        id_usuario = item[0]
        new_pass = simpledialog.askstring("Nueva Contraseña", "Ingrese la nueva contraseña:", show="*")
        if new_pass:
            if cambiar_password_usuario(id_usuario, new_pass):
                messagebox.showinfo("Éxito", "Contraseña actualizada")
            else:
                messagebox.showerror("Error", "No se pudo cambiar la contraseña")

    def eliminar_usuario(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Seleccione", "Seleccione un usuario")
            return
        item = self.tree.item(selected[0])["values"]
        id_usuario = item[0]
        if messagebox.askyesno("Confirmar", "¿Eliminar este usuario?"):
            if eliminar_usuario(id_usuario):
                messagebox.showinfo("Éxito", "Usuario eliminado")
                self.cargar_usuarios()
            else:
                messagebox.showerror("Error", "No se pudo eliminar el usuario")

    def volver(self):
        if self.main_window:
            self.main_window.show_welcome_screen()

class UsuarioDialog(simpledialog.Dialog):
    def __init__(self, parent, title, username="", password=None, nombre="", rol="usuario", activo=1, modo="crear"):
        self.username = username
        self.password = password  # No se usa para mostrar, solo para verificar si es edición
        self.nombre = nombre
        self.rol = rol
        self.activo = activo
        self.modo = modo  # "crear" o "editar"
        self.result = None
        super().__init__(parent, title)

    def body(self, master):
        # Configurar el padding y tamaño
        master.configure(padx=15, pady=10)

        # Configurar el grid para que las columnas tengan el ancho adecuado
        master.grid_columnconfigure(0, weight=1, minsize=120)
        master.grid_columnconfigure(1, weight=2, minsize=200)

        # Usuario
        ttk.Label(master, text="Usuario:", anchor="w").grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.username_entry = ttk.Entry(master, width=30)
        self.username_entry.grid(row=0, column=1, sticky="ew", pady=(0, 5))
        self.username_entry.insert(0, self.username)
        if self.modo == "editar":
            self.username_entry.config(state="disabled")

        # Sección de contraseña
        if self.modo == "crear":
            # Para creación, mostrar campos de contraseña normal
            ttk.Label(master, text="Contraseña:", anchor="w").grid(row=1, column=0, sticky="w", pady=(0, 5))
            self.password_entry = ttk.Entry(master, show="•", width=30)
            self.password_entry.grid(row=1, column=1, sticky="ew", pady=(0, 5))

            ttk.Label(master, text="Confirmar contraseña:", anchor="w").grid(row=2, column=0, sticky="w", pady=(0, 5))
            self.confirm_password_entry = ttk.Entry(master, show="•", width=30)
            self.confirm_password_entry.grid(row=2, column=1, sticky="ew", pady=(0, 5))

            row_offset = 3
        else:
            # Para edición, mostrar checkbox para cambiar contraseña
            self.cambiar_password_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(
                master,
                text="Cambiar contraseña",
                variable=self.cambiar_password_var,
                command=self.toggle_password_fields
            ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 5))

            # Crear contenedor para los campos de contraseña (inicialmente ocultos)
            self.password_frame = ttk.Frame(master)
            self.password_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
            self.password_frame.grid_columnconfigure(0, weight=1, minsize=120)
            self.password_frame.grid_columnconfigure(1, weight=2, minsize=200)

            ttk.Label(self.password_frame, text="Nueva contraseña:", anchor="w").grid(row=0, column=0, sticky="w", pady=(0, 5))
            self.password_entry = ttk.Entry(self.password_frame, show="•", width=30)
            self.password_entry.grid(row=0, column=1, sticky="ew", pady=(0, 5))

            ttk.Label(self.password_frame, text="Confirmar contraseña:", anchor="w").grid(row=1, column=0, sticky="w", pady=(0, 5))
            self.confirm_password_entry = ttk.Entry(self.password_frame, show="•", width=30)
            self.confirm_password_entry.grid(row=1, column=1, sticky="ew", pady=(0, 5))

            # Ocultar inicialmente los campos de contraseña
            self.password_frame.grid_remove()

            row_offset = 3

        # Nombre completo
        ttk.Label(master, text="Nombre completo:", anchor="w").grid(row=row_offset, column=0, sticky="w", pady=(0, 5))
        self.nombre_entry = ttk.Entry(master, width=30)
        self.nombre_entry.grid(row=row_offset, column=1, sticky="ew", pady=(0, 5))
        self.nombre_entry.insert(0, self.nombre)

        # Rol
        ttk.Label(master, text="Rol:", anchor="w").grid(row=row_offset+1, column=0, sticky="w", pady=(0, 5))
        self.rol_var = tk.StringVar(value=self.rol)
        self.rol_combo = ttk.Combobox(master, textvariable=self.rol_var, values=["admin", "usuario"], state="readonly", width=28)
        self.rol_combo.grid(row=row_offset+1, column=1, sticky="ew", pady=(0, 5))

        # Activo
        ttk.Label(master, text="Activo:", anchor="w").grid(row=row_offset+2, column=0, sticky="w", pady=(0, 5))
        self.activo_var = tk.IntVar(value=int(self.activo))
        ttk.Checkbutton(master, variable=self.activo_var).grid(row=row_offset+2, column=1, sticky="w", pady=(0, 5))

        # Dar foco al primer campo
        return self.username_entry

    def toggle_password_fields(self):
        """Muestra u oculta los campos de contraseña según el estado del checkbox"""
        if self.cambiar_password_var.get():
            self.password_frame.grid()
        else:
            self.password_frame.grid_remove()

    def validate(self):
        """Valida los datos del formulario antes de aceptar"""
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showerror("Error", "El nombre de usuario es obligatorio")
            return False

        # Validar contraseña
        if self.modo == "crear" or (self.modo == "editar" and self.cambiar_password_var.get()):
            password = self.password_entry.get()
            confirm_password = self.confirm_password_entry.get()

            if not password:
                messagebox.showerror("Error", "La contraseña es obligatoria")
                return False

            if password != confirm_password:
                messagebox.showerror("Error", "Las contraseñas no coinciden")
                return False

            # Opcional: validar complejidad de contraseña
            if len(password) < 6:
                messagebox.showerror("Error", "La contraseña debe tener al menos 6 caracteres")
                return False

        return True

    def apply(self):
        """Procesa los datos del formulario cuando se acepta"""
        username = self.username_entry.get().strip()
        nombre = self.nombre_entry.get().strip()
        rol = self.rol_var.get()
        activo = self.activo_var.get()

        # Obtener contraseña solo si es necesario
        password = None
        if self.modo == "crear" or (self.modo == "editar" and self.cambiar_password_var.get()):
            password = self.password_entry.get()

        self.result = (username, password, nombre, rol, activo)

    def show(self, *args, **kwargs):
        """Centra la ventana antes de mostrarla."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        self.geometry(f"+{x}+{y}")
        super().show(*args, **kwargs)

    def buttonbox(self):
        # Personalizar los botones
        box = ttk.Frame(self)

        w = ttk.Button(box, text="Aceptar", width=10, command=self.ok, default=tk.ACTIVE)
        w.pack(side=tk.LEFT, padx=5, pady=5)

        w = ttk.Button(box, text="Cancelar", width=10, command=self.cancel)
        w.pack(side=tk.LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack(pady=10)

    def apply(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        nombre = self.nombre_entry.get()
        rol = self.rol_var.get()
        activo = self.activo_var.get()

        if not username or (not password and not self.username):
            messagebox.showerror("Error", "Usuario y contraseña requeridos")
            self.result = None
        else:
            self.result = (username, password, nombre, rol, activo)