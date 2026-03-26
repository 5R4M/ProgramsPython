import customtkinter as ctk
from tkinter import messagebox
from database import DatabaseManager
import os
from config import (
    # Constantes de fuente
    FONT_SIZE_TITLE,
    FONT_SIZE_NORMAL,
    FONT_SIZE_SMALL,
    FONT_SIZE_BUTTON,
    # Constantes de padding
    PADDING_LARGE,
    PADDING_MEDIUM,
    PADDING_SMALL,
    PADDING_TINY,
    # Constantes de altura
    BUTTON_HEIGHT,
    INPUT_HEIGHT,
    # Constantes de iconos
    ICON_SIZE_LARGE,
    ICON_SIZE_MEDIUM,
    ICON_SIZE_SMALL,
    # Función de escalado
    escalar
)

class VentanaLogin:
    def __init__(self, root, callback_login_exitoso):
        self.root = root
        self.db = DatabaseManager()
        self.callback_login_exitoso = callback_login_exitoso
        
        self._configurar_icono_ventana() 
        
        self.root.title("Inicio de sesión")
        self.root.resizable(False, False)
        # ✅ Color de fondo oscuro
        self.root.configure(fg_color="#001a33")

        # Tamaño y centrado - responsivo según resolución
        w = escalar(400)
        if self._es_pantalla_pequena():
            h = escalar(560)  # Más altura para pantallas pequeñas
        else:
            h = escalar(520)  # Altura normal
            
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

        self.cargar_iconos()
        
        self.crear_interfaz()

    def _es_pantalla_pequena(self):
        """Detecta si la pantalla es pequeña (menos de 800px de alto)"""
        altura_pantalla = self.root.winfo_screenheight()
        return altura_pantalla < 800
    
    def _configurar_icono_ventana(self):
        """Configura el icono .ico de la ventana"""
        try:
            ruta_base = os.path.dirname(os.path.abspath(__file__))
            ruta_proyecto = os.path.dirname(ruta_base)
            icon_path = os.path.join(ruta_proyecto, "utils", "app_icono.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass
    
    def cargar_iconos(self):
        """Carga los iconos PNG para los botones y labels"""
        try:
            ruta_base = os.path.dirname(os.path.abspath(__file__))
            ruta_proyecto = os.path.dirname(ruta_base)
            ruta_iconos = os.path.join(ruta_proyecto, "utils", "iconos")

            if not os.path.exists(ruta_iconos):
                raise FileNotFoundError(f"No existe la carpeta: {ruta_iconos}")

            from PIL import Image

            self.icono_login = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "procesar.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "procesar.png")),
                size=ICON_SIZE_MEDIUM
            )
            self.icono_titulo = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "cargado.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "cargado.png")),
                size=ICON_SIZE_LARGE
            )
            self.icono_usuario = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "usuario.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "usuario.png")),
                size=ICON_SIZE_SMALL
            )
            self.icono_password = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "candado.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "candado.png")),
                size=ICON_SIZE_SMALL
            )
        except Exception:
            self.icono_login = None
            self.icono_titulo = None
            self.icono_usuario = None
            self.icono_password = None
    
    def crear_interfaz(self):
        # Frame principal
        frame = ctk.CTkFrame(self.root, fg_color="#001a33")
        frame.pack(fill="both", expand=True, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)

        # ===== Encabezado CENTRADO =====
        header = ctk.CTkFrame(frame, fg_color="#001a33")
        header.pack(fill="x", pady=(PADDING_SMALL, PADDING_MEDIUM))

        # Frame para título con icono (CENTRADO)
        titulo_frame = ctk.CTkFrame(header, fg_color="#001a33")
        titulo_frame.pack(anchor="center")  # ✅ Centrado

        # Icono del título
        if hasattr(self, 'icono_titulo') and self.icono_titulo:
            ctk.CTkLabel(
                titulo_frame,
                image=self.icono_titulo,
                text=""
            ).pack(side="left", padx=(0, PADDING_MEDIUM))

        # ✅ Título con FONT_SIZE_TITLE
        titulo = ctk.CTkLabel(
            titulo_frame,
            text="Inicio de sesión",
            font=ctk.CTkFont(size=FONT_SIZE_TITLE, weight="bold"),
            text_color="white"
        )
        titulo.pack(side="left")

        # ✅ Subtítulo con FONT_SIZE_SMALL
        subtitulo = ctk.CTkLabel(
            header,
            text="Ingrese sus credenciales para acceder al sistema.",
            font=ctk.CTkFont(size=FONT_SIZE_SMALL),
            text_color="#c4dafa",
        )
        subtitulo.pack(anchor="center", pady=(PADDING_SMALL, 0))  # ✅ Centrado

        # Separador
        ctk.CTkFrame(frame, fg_color="#005187", height=1).pack(fill="x", pady=(PADDING_MEDIUM, PADDING_LARGE))

        # ===== Card del formulario =====
        card_form = ctk.CTkFrame(frame, fg_color="#003d66", corner_radius=escalar(10))
        card_form.pack(fill="x", pady=(0, PADDING_MEDIUM))

        form = ctk.CTkFrame(card_form, fg_color="transparent")
        form.pack(fill="x", expand=False, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)

        # ===== Label Usuario con icono =====
        usuario_label_frame = ctk.CTkFrame(form, fg_color="#001a33")
        usuario_label_frame.pack(anchor="w", pady=(0, PADDING_TINY))

        if hasattr(self, 'icono_usuario') and self.icono_usuario:
            ctk.CTkLabel(
                usuario_label_frame,
                image=self.icono_usuario,
                text=""
            ).pack(side="left", padx=(0, PADDING_SMALL))

        ctk.CTkLabel(
            usuario_label_frame,
            text="Usuario",
            font=ctk.CTkFont(size=FONT_SIZE_NORMAL, weight="bold"),
            text_color="white"
        ).pack(side="left")

        # ✅ Entry Usuario con INPUT_HEIGHT
        self.entry_user = ctk.CTkEntry(
            form,
            placeholder_text="admin",
            height=INPUT_HEIGHT,
            fg_color="#003d66",  # ✅ Fondo oscuro
            border_color="#005187",  # ✅ Borde azul
            text_color="white",
            placeholder_text_color="#84b6f4",
            font=ctk.CTkFont(size=FONT_SIZE_NORMAL)
        )
        self.entry_user.pack(fill="x", pady=(0, PADDING_LARGE))

        # ===== Label Contraseña con icono =====
        password_label_frame = ctk.CTkFrame(form, fg_color="#001a33")
        password_label_frame.pack(anchor="w", pady=(0, PADDING_TINY))

        if hasattr(self, 'icono_password') and self.icono_password:
            ctk.CTkLabel(
                password_label_frame,
                image=self.icono_password,
                text=""
            ).pack(side="left", padx=(0, PADDING_SMALL))

        ctk.CTkLabel(
            password_label_frame,
            text="Contraseña",
            font=ctk.CTkFont(size=FONT_SIZE_NORMAL, weight="bold"),
            text_color="white"
        ).pack(side="left")

        # ✅ Entry Contraseña con INPUT_HEIGHT
        self.entry_pass = ctk.CTkEntry(
            form,
            placeholder_text="******",
            show="*",
            height=INPUT_HEIGHT,
            fg_color="#003d66",  # ✅ Fondo oscuro
            border_color="#005187",  # ✅ Borde azul
            text_color="white",
            placeholder_text_color="#84b6f4",
            font=ctk.CTkFont(size=FONT_SIZE_NORMAL)
        )
        self.entry_pass.pack(fill="x", pady=(0, PADDING_SMALL))

        # ✅ Checkbox con FONT_SIZE_SMALL
        self.var_mostrar = ctk.BooleanVar(value=False)
        chk = ctk.CTkCheckBox(
            form,
            text="Mostrar contraseña",
            variable=self.var_mostrar,
            command=self.toggle_password,
            fg_color="#005187",  # ✅ Color azul cuando está marcado
            hover_color="#2d5f8d",  # ✅ Color hover
            text_color="white",
            font=ctk.CTkFont(size=FONT_SIZE_SMALL)
        )
        chk.pack(anchor="w", pady=(0, PADDING_MEDIUM))

        # ✅ Nota con FONT_SIZE_SMALL
        nota = ctk.CTkLabel(
            form,
            text="ℹ️ Use el usuario asignado por el administrador.",
            font=ctk.CTkFont(size=FONT_SIZE_SMALL),
            text_color="#c4dafa",
            justify="left",
        )
        nota.pack(anchor="w", pady=(0, PADDING_LARGE))

        # Zona de carga / mensajes bajo el formulario
        # ✅ Ajuste condicional para pantallas pequeñas
        if self._es_pantalla_pequena():
            self.loading_frame = ctk.CTkFrame(frame, fg_color="#001a33", height=escalar(35))
            self.loading_frame.pack(fill="x", pady=(PADDING_TINY, PADDING_TINY))
            self.loading_frame.pack_propagate(False)
        else:
            self.loading_frame = ctk.CTkFrame(frame, fg_color="#001a33")
            self.loading_frame.pack(fill="x", pady=(0, PADDING_SMALL))

        self.loading_label = ctk.CTkLabel(
            self.loading_frame,
            text="",  # se rellenará cuando inicie la animación
            font=ctk.CTkFont(size=FONT_SIZE_SMALL),
            text_color="#c4dafa",
        )
        self.loading_label.pack(anchor="center")

        # ✅ Botón ingresar con BUTTON_HEIGHT y FONT_SIZE_BUTTON
        self.btn_login = ctk.CTkButton(
            frame,
            text="  Ingresar",
            image=self.icono_login if hasattr(self, 'icono_login') and self.icono_login else None,
            compound="left",
            command=self.intentar_login,
            height=BUTTON_HEIGHT,
            fg_color="#005187",  # ✅ Color azul oscuro
            hover_color="#2d5f8d",  # ✅ Color hover más claro
            font=ctk.CTkFont(size=FONT_SIZE_BUTTON, weight="bold")
        )
        self.btn_login.pack(fill="x", pady=(PADDING_SMALL, 0))

        # Pie
        footer = ctk.CTkFrame(frame, fg_color="#001a33")
        footer.pack(fill="x", pady=(PADDING_LARGE, 0))

        lbl_footer = ctk.CTkLabel(
            footer,
            text="🔒 Acceso restringido a personal autorizado.",
            font=ctk.CTkFont(size=FONT_SIZE_SMALL),
            text_color="#84b6f4",
        )
        lbl_footer.pack(anchor="center")

        # Atajos de teclado
        self.entry_user.bind("<Return>", lambda e: self.entry_pass.focus_set())
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
            messagebox.showwarning("⚠️ Campos vacíos", "Ingrese usuario y contraseña.")
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
                "❌ Error de autenticación",
                "Usuario o contraseña incorrectos, o usuario inactivo.",
            )
            return

        # Si es correcto, mostrar unos milisegundos de "Accediendo..."
        self.loading_label.configure(text="✅ Accediendo al sistema...")
        # Breve pausa visual antes de cerrar login y abrir el MainWindow
        self.root.after(400, lambda: self._finalizar_login(info_usuario))
    
    def _finalizar_login(self, info_usuario):
        # Detener animación por si sigue
        self.detener_animacion_carga()

        # Llamar al callback que cerrará el login y abrirá el MainWindow
        if self.callback_login_exitoso:
            self.callback_login_exitoso(info_usuario)