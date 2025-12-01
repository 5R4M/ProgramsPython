# ventana_login.py
import customtkinter as ctk
from tkinter import messagebox
from database import DatabaseManager  # ajusta si el nombre difiere

class VentanaLogin:
    def __init__(self, root, callback_login_exitoso):
        """
        root: ventana CTk principal (de login, NO el MainWindow)
        callback_login_exitoso: función(info_usuario) a ejecutar cuando el login es correcto
        """
        self.root = root
        self.db = DatabaseManager()
        self.callback_login_exitoso = callback_login_exitoso

        self.win = ctk.CTkToplevel(root)
        self.win.title("Inicio de sesión")
        self.win.resizable(False, False)

        # Tamaño más grande (vertical)
        w, h = 360, 420
        self.win.geometry(f"{w}x{h}")
        self.win.transient(root)
        self.win.grab_set()

        # Centrar
        self.win.update_idletasks()
        x = (self.win.winfo_screenwidth() // 2) - (w // 2)
        y = (self.win.winfo_screenheight() // 2) - (h // 2)
        self.win.geometry(f"{w}x{h}+{x}+{y}")

        self.crear_interfaz()

    def crear_interfaz(self):
        frame = ctk.CTkFrame(self.win)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        titulo = ctk.CTkLabel(
            frame,
            text="🔐 Iniciar Sesión",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        titulo.pack(pady=(0, 20))

        # Usuario
        ctk.CTkLabel(frame, text="Usuario:").pack(anchor="w")
        self.entry_user = ctk.CTkEntry(frame, placeholder_text="admin")
        self.entry_user.pack(fill="x", pady=(0, 15))

        # Password
        ctk.CTkLabel(frame, text="Contraseña:").pack(anchor="w")
        self.entry_pass = ctk.CTkEntry(frame, placeholder_text="******", show="*")
        self.entry_pass.pack(fill="x", pady=(0, 15))

        # Mostrar / ocultar contraseña
        self.var_mostrar = ctk.BooleanVar(value=False)
        chk = ctk.CTkCheckBox(
            frame,
            text="Mostrar contraseña",
            variable=self.var_mostrar,
            command=self.toggle_password
        )
        chk.pack(anchor="w", pady=(0, 20))

        # Botón ingresar
        btn_login = ctk.CTkButton(
            frame,
            text="Ingresar",
            command=self.intentar_login,
            height=36
        )
        btn_login.pack(fill="x", pady=(5, 0))

        self.entry_pass.bind("<Return>", lambda e: self.intentar_login())
        self.entry_user.focus_set()

    def toggle_password(self):
        if self.var_mostrar.get():
            self.entry_pass.configure(show="")
        else:
            self.entry_pass.configure(show="*")

    def intentar_login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()

        if not username or not password:
            messagebox.showwarning("Campos vacíos", "Ingrese usuario y contraseña")
            return

        info_usuario = self.db.autenticar_usuario(username, password)
        if not info_usuario:
            messagebox.showerror(
                "Error",
                "Usuario o contraseña incorrectos, o usuario inactivo."
            )
            return

        messagebox.showinfo(
            "Bienvenido",
            f"Hola, {info_usuario.get('nombre_completo') or info_usuario['username']}"
        )

        # Cerrar la ventana de login
        self.win.destroy()
        # Llamar callback con info de usuario
        if self.callback_login_exitoso:
            self.callback_login_exitoso(info_usuario)