# ventana_login.py
import customtkinter as ctk
from tkinter import messagebox
from database import DatabaseManager

class VentanaLogin:
    def __init__(self, root, callback_login_exitoso):
        self.root = root
        self.db = DatabaseManager()
        self.callback_login_exitoso = callback_login_exitoso
        
        self.root.title("Inicio de sesión")
        self.root.resizable(False, False)

        # Tamaño y centrado
        w, h = 380, 460
        self.root.geometry(f"{w}x{h}")
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        # Referencias para animación
        self.btn_login = None
        self.loading_frame = None
        self.loading_label = None
        self.loading_dots = ""
        self.loading_job = None

        self.crear_interfaz()

    def crear_interfaz(self):
        # Frame principal
        frame = ctk.CTkFrame(self.root)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # ===== Encabezado =====
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", pady=(5, 10))

        titulo = ctk.CTkLabel(
            header,
            text="🔐 Inicio de sesión",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        titulo.pack(anchor="w")

        subtitulo = ctk.CTkLabel(
            header,
            text="Ingrese sus credenciales para acceder al sistema.",
            font=ctk.CTkFont(size=11),
            text_color="gray70",
        )
        subtitulo.pack(anchor="w", pady=(2, 0))

        separator = ctk.CTkFrame(frame, fg_color="gray25", height=1)
        separator.pack(fill="x", pady=(5, 15))

        # ===== Formulario =====
        form = ctk.CTkFrame(frame, fg_color="transparent")
        form.pack(fill="x", expand=False, pady=(0, 10))

        # Usuario
        ctk.CTkLabel(
            form,
            text="Usuario",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", pady=(0, 2))

        self.entry_user = ctk.CTkEntry(
            form,
            placeholder_text="admin",
        )
        self.entry_user.pack(fill="x", pady=(0, 12))

        # Contraseña
        ctk.CTkLabel(
            form,
            text="Contraseña",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", pady=(0, 2))

        self.entry_pass = ctk.CTkEntry(
            form,
            placeholder_text="******",
            show="*",
        )
        self.entry_pass.pack(fill="x", pady=(0, 8))

        # Mostrar / ocultar contraseña
        self.var_mostrar = ctk.BooleanVar(value=False)
        chk = ctk.CTkCheckBox(
            form,
            text="Mostrar contraseña",
            variable=self.var_mostrar,
            command=self.toggle_password,
        )
        chk.pack(anchor="w", pady=(0, 12))

        # Nota
        nota = ctk.CTkLabel(
            form,
            text="Use el usuario asignado por el administrador.",
            font=ctk.CTkFont(size=10),
            text_color="gray70",
            justify="left",
        )
        nota.pack(anchor="w", pady=(0, 15))

        # Zona de carga / mensajes bajo el formulario
        self.loading_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self.loading_frame.pack(fill="x", pady=(0, 5))

        self.loading_label = ctk.CTkLabel(
            self.loading_frame,
            text="",  # se rellenará cuando inicie la animación
            font=ctk.CTkFont(size=11),
            text_color="gray80",
        )
        self.loading_label.pack(anchor="center")

        # Botón ingresar
        self.btn_login = ctk.CTkButton(
            frame,
            text="Ingresar",
            command=self.intentar_login,
            height=40,
        )
        self.btn_login.pack(fill="x", pady=(5, 0))

        # Pie
        footer = ctk.CTkFrame(frame, fg_color="transparent")
        footer.pack(fill="x", pady=(15, 0))

        lbl_footer = ctk.CTkLabel(
            footer,
            text="Acceso restringido a personal autorizado.",
            font=ctk.CTkFont(size=10),
            text_color="gray60",
        )
        lbl_footer.pack(anchor="center")

        # Atajos
        self.entry_pass.bind("<Return>", lambda e: self.intentar_login())

        # Dar foco al campo de usuario una vez que la ventana esté lista
        self.root.after(100, lambda: self.entry_user.focus_set())

    def toggle_password(self):
        if self.var_mostrar.get():
            self.entry_pass.configure(show="")
        else:
            self.entry_pass.configure(show="*")

    # ======== Animación de carga ========

    def iniciar_animacion_carga(self, texto_base="Verificando credenciales"):
        """Muestra una etiqueta de carga con puntos animados."""
        self.loading_dots = ""
        self.loading_label.configure(text=texto_base)
        self._actualizar_animacion(texto_base)

    def _actualizar_animacion(self, texto_base):
        # Alternar entre 0, 1, 2, 3 puntos
        if len(self.loading_dots) >= 3:
            self.loading_dots = ""
        else:
            self.loading_dots += "."

        self.loading_label.configure(text=f"{texto_base}{self.loading_dots}")
        # Guardamos el id del after para poder cancelarlo si hiciera falta
        self.loading_job = self.root.after(250, self._actualizar_animacion, texto_base)

    def detener_animacion_carga(self):
        """Detiene la animación y limpia el texto."""
        if self.loading_job is not None:
            try:
                self.root.after_cancel(self.loading_job)
            except Exception:
                pass
            self.loading_job = None

        self.loading_label.configure(text="")

    # ======== Lógica de login ========

    def intentar_login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()

        if not username or not password:
            messagebox.showwarning("Campos vacíos", "Ingrese usuario y contraseña.")
            return

        # Deshabilitar botón mientras se valida
        self.btn_login.configure(state="disabled")
        self.iniciar_animacion_carga("Verificando credenciales")

        # Validar de forma "simulada" con un pequeño delay para que se note la animación
        # Si tu autenticación fuera pesada (red, etc.), aquí podrías dejarla directa.
        self.root.after(200, lambda: self._validar_credenciales(username, password))

    def _validar_credenciales(self, username, password):
        info_usuario = self.db.autenticar_usuario(username, password)

        if not info_usuario:
            # Error: detener animación, reactivar botón y mostrar mensaje
            self.detener_animacion_carga()
            self.btn_login.configure(state="normal")
            messagebox.showerror(
                "Error de autenticación",
                "Usuario o contraseña incorrectos, o usuario inactivo.",
            )
            return

        # Si es correcto, mostrar unos milisegundos de "Accediendo..."
        self.loading_label.configure(text="Accediendo al sistema...")
        # Breve pausa visual antes de cerrar login y abrir el MainWindow
        self.root.after(400, lambda: self._finalizar_login(info_usuario))

    def _finalizar_login(self, info_usuario):
        # Detener animación por si sigue
        self.detener_animacion_carga()

        # Llamar al callback que cerrará el login y abrirá el MainWindow
        if self.callback_login_exitoso:
            self.callback_login_exitoso(info_usuario)