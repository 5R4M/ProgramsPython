import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from src.database.db_manager import (
    obtener_usuarios, crear_usuario, actualizar_usuario, cambiar_password_usuario, eliminar_usuario
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
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col.capitalize())
        self.tree.pack(fill="both", expand=True, pady=10)

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
            self.tree.insert("", "end", values=usuario)

    def crear_usuario(self):
        dialog = UsuarioDialog(self.parent, "Crear Usuario")
        if dialog.result:
            username, password, nombre, rol = dialog.result
            if crear_usuario(username, password, nombre, rol):
                messagebox.showinfo("Éxito", "Usuario creado")
                self.cargar_usuarios()
            else:
                messagebox.showerror("Error", "No se pudo crear el usuario")

    def editar_usuario(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Seleccione", "Seleccione un usuario")
            return
        item = self.tree.item(selected[0])["values"]
        id_usuario, username, nombre, rol, activo = item
        dialog = UsuarioDialog(self.parent, "Editar Usuario", username, None, nombre, rol, activo)
        if dialog.result:
            _, _, nombre, rol, activo = dialog.result
            if actualizar_usuario(id_usuario, nombre, rol, int(activo)):
                messagebox.showinfo("Éxito", "Usuario actualizado")
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
    def __init__(self, parent, title, username="", password="", nombre="", rol="usuario", activo=1):
        self.username = username
        self.password = password
        self.nombre = nombre
        self.rol = rol
        self.activo = activo
        super().__init__(parent, title)

    def body(self, master):
        ttk.Label(master, text="Usuario:").grid(row=0, column=0)
        self.username_entry = ttk.Entry(master)
        self.username_entry.grid(row=0, column=1)
        self.username_entry.insert(0, self.username)
        if self.username:
            self.username_entry.config(state="disabled")

        ttk.Label(master, text="Contraseña:").grid(row=1, column=0)
        self.password_entry = ttk.Entry(master, show="*")
        self.password_entry.grid(row=1, column=1)
        if self.password:
            self.password_entry.insert(0, self.password)

        ttk.Label(master, text="Nombre completo:").grid(row=2, column=0)
        self.nombre_entry = ttk.Entry(master)
        self.nombre_entry.grid(row=2, column=1)
        self.nombre_entry.insert(0, self.nombre)

        ttk.Label(master, text="Rol:").grid(row=3, column=0)
        self.rol_var = tk.StringVar(value=self.rol)
        self.rol_combo = ttk.Combobox(master, textvariable=self.rol_var, values=["admin", "usuario"], state="readonly")
        self.rol_combo.grid(row=3, column=1)

        ttk.Label(master, text="Activo:").grid(row=4, column=0)
        self.activo_var = tk.IntVar(value=int(self.activo))
        ttk.Checkbutton(master, variable=self.activo_var).grid(row=4, column=1)

        return self.username_entry

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