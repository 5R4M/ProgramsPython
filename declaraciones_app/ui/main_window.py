import os
import customtkinter as ctk
from tkinter import messagebox
from backup_util import (
    hacer_backup_completo,
    restaurar_backup_completo,
)
from tkinter import filedialog

from config import (
    APP_NAME,
    APP_VERSION,
    WINDOW_SIZE,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_WARNING,
    DOCUMENTOS_DIR,
    # Nuevas constantes adaptadas
    FONT_SIZE_TITLE_MAIN,
    FONT_SIZE_SUBTITLE,
    FONT_SIZE_NORMAL,
    FONT_SIZE_SMALL,
    FONT_SIZE_TINY,
    FONT_SIZE_CARD_TITLE,
    FONT_SIZE_BUTTON,
    ICON_SIZE_MENU,
    ICON_SIZE_MENU_SMALL,
    ICON_SIZE_CARD,
    ICON_SIZE_LOGO,
    PADDING_LARGE,
    PADDING_MEDIUM,
    PADDING_SMALL,
    PADDING_TINY,
    MENU_WIDTH,
    BUTTON_HEIGHT,
    BUTTON_HEIGHT_SMALL,
    STATUS_BAR_HEIGHT,
    CARD_CORNER_RADIUS,
    CARD_PADDING,
    DIALOG_WIDTH,
    DIALOG_HEIGHT,
)
from database import DatabaseManager
from .cargar_documentos import VentanaCargarDocumentos
from .buscar_documento import VentanaBuscarDocumento
from .crear_documento import VentanaCrearDocumento
from .ventana_usuarios import VentanaGestionUsuarios
from PIL import Image


class MainWindow(ctk.CTk):
    def __init__(self, info_usuario):
        """
        info_usuario: dict con
            {
                "id": ...,
                "username": ...,
                "nombre_completo": ...,
                "rol": "admin" | "usuario",
                "activo": 1/0
            }
        """
        super().__init__()

        # ===== ICONO DE LA VENTANA PRINCIPAL =====
        try:
            # Ruta base del proyecto (carpeta donde está este archivo)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            # Ir un nivel arriba (porque este archivo está en ui/) y entrar a utils/
            project_root = os.path.dirname(base_dir)
            icon_path = os.path.join(project_root, "utils", "app_icono.ico")

            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
            else:
                print(f"[MainWindow] Icono no encontrado: {icon_path}")
        except Exception as e:
            print(f"[MainWindow] No se pudo establecer icono: {e}")

        self.title(f"{APP_NAME} - v{APP_VERSION}")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Fondo de la ventana principal para que coincida
        self.configure(fg_color="gray10")
        
        # Inicializar base de datos
        self.db = DatabaseManager()

        # Usuario autenticado (llega desde el login)
        self.usuario_actual = info_usuario

        self.info_frame = None
        self.panel_contenido = None

        # Referencia al botón de usuarios para poder ocultarlo según rol
        self.btn_usuarios = None

        # Cargar iconos antes de crear la interfaz
        self.cargar_iconos()

        # Crear interfaz
        self.crear_interfaz()

        # Centrar y maximizar ventana
        self.center_window()
        self.after(100, self.maximizar_ventana)

        # Ajustar visibilidad del botón usuarios según rol
        self.actualizar_visibilidad_boton_usuarios()

        # Mostrar pantalla de inicio y estadísticas ya con usuario logueado
        self.mostrar_inicio()
        self.actualizar_estadisticas_menu()

        # Configurar el protocolo de cierre
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def cargar_iconos(self):
        """Carga todos los iconos con tamaños adaptados automáticamente"""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(base_dir)
            ruta_iconos = os.path.join(project_root, "utils", "iconos")
            
            print(f"🔍 Cargando iconos desde: {ruta_iconos}")
            
            if not os.path.exists(ruta_iconos):
                print(f"⚠️ Carpeta de iconos no encontrada: {ruta_iconos}")
                raise FileNotFoundError(f"No existe la carpeta: {ruta_iconos}")
            
            # Iconos para menú lateral (usando ICON_SIZE_MENU)
            self.icono_inicio = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "inicio.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "inicio.png")),
                size=ICON_SIZE_MENU
            )
            
            self.icono_cargar = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "cargado.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "cargado.png")),
                size=ICON_SIZE_MENU
            )
            
            self.icono_buscar = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "buscar.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "buscar.png")),
                size=ICON_SIZE_MENU
            )
            
            self.icono_crear = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "agregar.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "agregar.png")),
                size=ICON_SIZE_MENU
            )
            
            self.icono_backup = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "backup.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "backup.png")),
                size=ICON_SIZE_MENU
            )
            
            self.icono_usuarios = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "usuario.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "usuario.png")),
                size=ICON_SIZE_MENU
            )
            
            self.icono_salir = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "salir.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "salir.png")),
                size=ICON_SIZE_MENU
            )
            
            self.icono_opciones = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "opciones.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "opciones.png")),
                size=ICON_SIZE_MENU_SMALL
            )
            
            # Iconos para tarjetas de inicio (usando ICON_SIZE_CARD)
            self.icono_cargar_grande = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "cargado.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "cargado.png")),
                size=ICON_SIZE_CARD
            )
            
            self.icono_buscar_grande = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "buscar.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "buscar.png")),
                size=ICON_SIZE_CARD
            )
            
            self.icono_crear_grande = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "agregar.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "agregar.png")),
                size=ICON_SIZE_CARD
            )
            
            self.icono_backup_grande = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "backup.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "backup.png")),
                size=ICON_SIZE_CARD
            )
            
            # Icono para logo principal (usando ICON_SIZE_LOGO)
            self.icono_logo = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "logo.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "logo.png")),
                size=ICON_SIZE_LOGO
            )
            
            print("✅ Todos los iconos cargados correctamente")
            
        except Exception as e:
            print(f"⚠️ Error al cargar iconos: {e}")
            import traceback
            traceback.print_exc()
            
            # Establecer todos los iconos como None si falla
            for attr in ['icono_inicio', 'icono_cargar', 'icono_buscar', 'icono_crear',
                        'icono_backup', 'icono_usuarios', 'icono_salir', 'icono_opciones',
                        'icono_cargar_grande', 'icono_buscar_grande', 'icono_crear_grande',
                        'icono_backup_grande', 'icono_logo']:
                setattr(self, attr, None)

    def maximizar_ventana(self):
        """Maximiza la ventana"""
        self.state("zoomed")

    def center_window(self):
        """Centra la ventana en la pantalla"""
        self.geometry(WINDOW_SIZE)
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def actualizar_visibilidad_boton_usuarios(self):
        """
        Oculta el botón de gestión de usuarios según el rol:
        - admin: visible (ya está empaquetado en crear_interfaz)
        - usuario (u otro): oculto
        """
        if not self.btn_usuarios:
            return

        rol = None
        if self.usuario_actual:
            rol = self.usuario_actual.get("rol")

        if rol == "admin":
            # Nada que hacer: el botón ya está empaquetado debajo de "Crear Documento"
            pass
        else:
            # Ocultar botón para usuario normal o si no hay usuario
            self.btn_usuarios.pack_forget()

    # =============== INTERFAZ PRINCIPAL ===============

    def crear_interfaz(self):
        """Crea la interfaz principal - USA CONSTANTES ADAPTADAS"""

        # Barra de estado inferior
        self.status_bar = ctk.CTkFrame(self, height=STATUS_BAR_HEIGHT, fg_color="gray15")
        self.status_bar.pack(fill="x", side="bottom")

        self.lbl_status_personas = ctk.CTkLabel(
            self.status_bar, text="👥 Personas: 0", font=ctk.CTkFont(size=FONT_SIZE_TINY)
        )
        self.lbl_status_personas.pack(side="left", padx=PADDING_SMALL)

        self.lbl_status_documentos = ctk.CTkLabel(
            self.status_bar, text="📄 Documentos: 0", font=ctk.CTkFont(size=FONT_SIZE_TINY)
        )
        self.lbl_status_documentos.pack(side="left", padx=PADDING_SMALL)

        self.lbl_status_plantilla = ctk.CTkLabel(
            self.status_bar, text="📋 Plantilla: ❌", font=ctk.CTkFont(size=FONT_SIZE_TINY)
        )
        self.lbl_status_plantilla.pack(side="left", padx=PADDING_SMALL)

        if self.usuario_actual:
            texto_status = f"Usuario: {self.usuario_actual['username']} ({self.usuario_actual.get('rol', '')})"
        else:
            texto_status = "Listo"

        self.lbl_status_msg = ctk.CTkLabel(
            self.status_bar,
            text=texto_status,
            font=ctk.CTkFont(size=FONT_SIZE_TINY),
            text_color="gray80",
        )
        self.lbl_status_msg.pack(side="right", padx=PADDING_SMALL)

        # Contenedor principal
        container = ctk.CTkFrame(self, fg_color="gray10", corner_radius=0, border_width=0)
        container.pack(fill="both", expand=True)

        container.grid_columnconfigure(0, weight=0)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)

        # Menú lateral izquierdo
        menu_lateral = ctk.CTkFrame(
            container,
            width=MENU_WIDTH,
            corner_radius=0,
            fg_color="gray10",
            border_width=0,
        )
        menu_lateral.grid(row=0, column=0, sticky="nsew")
        menu_lateral.grid_propagate(False)

        # Logo/Título del menú
        frame_logo = ctk.CTkFrame(menu_lateral, fg_color="transparent", corner_radius=0)
        frame_logo.pack(fill="x", pady=PADDING_LARGE)

        if hasattr(self, 'icono_logo') and self.icono_logo:
            ctk.CTkLabel(frame_logo, image=self.icono_logo, text="").pack(pady=PADDING_TINY)
        else:
            ctk.CTkLabel(
                frame_logo, text="📋", font=ctk.CTkFont(size=ICON_SIZE_LOGO[0])
            ).pack(pady=PADDING_TINY)

        ctk.CTkLabel(
            frame_logo,
            text="Sistema de Actas\nNotariales",
            font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight="bold"),
        ).pack(pady=(0, PADDING_MEDIUM))

        # Label "Opciones"
        label_opciones = ctk.CTkLabel(
            menu_lateral,
            text="  Opciones",
            image=self.icono_opciones if hasattr(self, 'icono_opciones') and self.icono_opciones else None,
            compound="left",
            font=ctk.CTkFont(size=FONT_SIZE_NORMAL, weight="bold"),
        )
        label_opciones.pack(pady=(PADDING_SMALL, PADDING_MEDIUM), padx=PADDING_MEDIUM, anchor="w")

        # Botones del menú (usando función helper para no repetir código)
        botones_config = [
            ("  Inicio", "icono_inicio", self.mostrar_inicio, "transparent"),
            ("  Cargar Documentos", "icono_cargar", self.mostrar_cargar_documentos, "transparent"),
            ("  Buscar Documento", "icono_buscar", self.mostrar_buscar_documento, "transparent"),
            ("  Crear Documento", "icono_crear", self.mostrar_crear_documento, "transparent"),
            ("  Backup", "icono_backup", self._mostrar_dialogo_backup, "transparent"),
        ]

        for texto, icono_attr, comando, fg_color in botones_config:
            btn = ctk.CTkButton(
                menu_lateral,
                text=texto,
                image=getattr(self, icono_attr) if hasattr(self, icono_attr) else None,
                compound="left",
                command=comando,
                height=BUTTON_HEIGHT,
                font=ctk.CTkFont(size=FONT_SIZE_BUTTON),
                fg_color=fg_color,
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                anchor="w",
                corner_radius=8,
            )
            btn.pack(pady=PADDING_TINY, padx=PADDING_MEDIUM, fill="x")
            
            # Guardar referencia al botón de backup
            if "Backup" in texto:
                self.btn_backup = btn
        
        # Botón de usuarios (guardamos referencia)
        self.btn_usuarios = ctk.CTkButton(
            menu_lateral,
            text="  Usuarios",
            image=self.icono_usuarios if hasattr(self, 'icono_usuarios') else None,
            compound="left",
            command=self.mostrar_gestion_usuarios,
            height=BUTTON_HEIGHT,
            font=ctk.CTkFont(size=FONT_SIZE_BUTTON),
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            corner_radius=8,
        )
        self.btn_usuarios.pack(pady=PADDING_TINY, padx=PADDING_MEDIUM, fill="x")

        # Espaciador
        ctk.CTkFrame(menu_lateral, fg_color="transparent").pack(fill="both", expand=True)

        # Botón Salir
        btn_salir = ctk.CTkButton(
            menu_lateral,
            text="  Salir del sistema",
            image=self.icono_salir if hasattr(self, 'icono_salir') else None,
            compound="left",
            command=self.on_closing,
            height=BUTTON_HEIGHT - 2,
            font=ctk.CTkFont(size=FONT_SIZE_BUTTON, weight="bold"),
            fg_color="#c0392b",
            hover_color="#e74c3c",
            text_color="white",
            corner_radius=8,
        )
        btn_salir.pack(pady=(0, PADDING_SMALL), padx=PADDING_MEDIUM, fill="x")

        # Footer del menú
        footer_menu = ctk.CTkFrame(menu_lateral, fg_color="transparent")
        footer_menu.pack(fill="x", pady=PADDING_TINY, padx=PADDING_MEDIUM)

        ctk.CTkLabel(
            footer_menu,
            text=f"v{APP_VERSION}",
            font=ctk.CTkFont(size=FONT_SIZE_TINY - 1),
            text_color="gray",
        ).pack()

        # Panel de contenido derecho
        self.panel_contenido = ctk.CTkFrame(
            container,
            corner_radius=0,
            fg_color="gray10",
            border_width=0,
        )
        self.panel_contenido.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)


    def limpiar_panel_contenido(self):
        """Limpia el panel de contenido"""
        for widget in self.panel_contenido.winfo_children():
            widget.destroy()

    # ================== VISTAS ==================

    def mostrar_inicio(self):
        """Muestra la pantalla de inicio - ADAPTADA AUTOMÁTICAMENTE"""
        self.limpiar_panel_contenido()

        frame_inicio = ctk.CTkFrame(self.panel_contenido)
        frame_inicio.pack(fill="both", expand=True, padx=PADDING_LARGE + 10, pady=PADDING_LARGE + 10)

        ctk.CTkLabel(
            frame_inicio,
            text="📋 Sistema de Actas Notariales",
            font=ctk.CTkFont(size=FONT_SIZE_TITLE_MAIN, weight="bold"),
        ).pack(pady=(PADDING_LARGE * 2 + 10, PADDING_LARGE))

        ctk.CTkLabel(
            frame_inicio,
            text="Gestión integral de documentos notariales",
            font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE),
            text_color="gray",
        ).pack(pady=PADDING_SMALL)

        # Tarjetas de acceso rápido
        cards_frame = ctk.CTkFrame(frame_inicio, fg_color="transparent")
        cards_frame.pack(pady=PADDING_LARGE * 2 + 10, fill="both", expand=True)

        cards_frame.grid_columnconfigure(0, weight=1)
        cards_frame.grid_columnconfigure(1, weight=1)
        cards_frame.grid_columnconfigure(2, weight=1)
        cards_frame.grid_columnconfigure(3, weight=1)

        # Configuración de tarjetas
        cards_info = [
            {
                "titulo": "Cargar Documentos",
                "descripcion": "Importar documentos .doc/.docx\na la base de datos",
                "icono_grande": "icono_cargar_grande",
                "emoji": "📥",
                "comando": self.mostrar_cargar_documentos,
                "color": COLOR_PRIMARY,
                "hover": "#2980b9"
            },
            {
                "titulo": "Buscar Documento",
                "descripcion": "Buscar por nombre o DPI\nen la base de datos",
                "icono_grande": "icono_buscar_grande",
                "emoji": "🔍",
                "comando": self.mostrar_buscar_documento,
                "color": COLOR_SUCCESS,
                "hover": "#27ae60"
            },
            {
                "titulo": "Crear Documento",
                "descripcion": "Generar nuevo documento\ncon plantilla",
                "icono_grande": "icono_crear_grande",
                "emoji": "➕",
                "comando": self.mostrar_crear_documento,
                "color": COLOR_WARNING,
                "hover": "#e67e22"
            },
            {
                "titulo": "Backup",
                "descripcion": "Crear copia de seguridad\nde documentos y base de datos",
                "icono_grande": "icono_backup_grande",
                "emoji": "🧾",
                "comando": self._mostrar_dialogo_backup,
                "color": COLOR_PRIMARY,
                "hover": "#2980b9"
            }
        ]

        # Crear tarjetas usando loop
        for idx, card_data in enumerate(cards_info):
            card = ctk.CTkFrame(cards_frame, corner_radius=CARD_CORNER_RADIUS)
            card.grid(row=0, column=idx, padx=CARD_PADDING, pady=PADDING_LARGE, sticky="nsew")

            # Icono
            if hasattr(self, card_data["icono_grande"]) and getattr(self, card_data["icono_grande"]):
                ctk.CTkLabel(
                    card, 
                    image=getattr(self, card_data["icono_grande"]),
                    text=""
                ).pack(pady=CARD_PADDING)
            else:
                ctk.CTkLabel(
                    card, 
                    text=card_data["emoji"], 
                    font=ctk.CTkFont(size=ICON_SIZE_CARD[0])
                ).pack(pady=CARD_PADDING)

            # Título
            ctk.CTkLabel(
                card,
                text=card_data["titulo"],
                font=ctk.CTkFont(size=FONT_SIZE_CARD_TITLE, weight="bold"),
            ).pack(pady=PADDING_SMALL)

            # Descripción
            ctk.CTkLabel(
                card,
                text=card_data["descripcion"],
                font=ctk.CTkFont(size=FONT_SIZE_SMALL),
                text_color="gray",
                justify="center",
            ).pack(pady=PADDING_SMALL + 1)

            # Botón
            ctk.CTkButton(
                card,
                text="Abrir" if idx < 3 else "Abrir gestor de backup",
                command=card_data["comando"],
                fg_color=card_data["color"],
                hover_color=card_data["hover"],
                height=BUTTON_HEIGHT_SMALL,
            ).pack(pady=CARD_PADDING)
        
    def mostrar_cargar_documentos(self):
        """Muestra el módulo de carga de documentos en el panel"""
        self.limpiar_panel_contenido()

        try:
            container = ctk.CTkFrame(self.panel_contenido, fg_color="transparent")
            container.pack(fill="both", expand=True, padx=20, pady=20)

            ventana = VentanaCargarDocumentos(container, self.db, es_integrado=True)

            if hasattr(ventana, "set_callback_actualizar"):
                ventana.set_callback_actualizar(self.actualizar_estadisticas_menu)

        except Exception as e:
            print(f"Error al mostrar cargar documentos: {e}")
            error_frame = ctk.CTkFrame(self.panel_contenido)
            error_frame.pack(fill="both", expand=True, padx=40, pady=40)
            ctk.CTkLabel(
                error_frame,
                text=f"⚠️ Error al cargar módulo\n{str(e)}",
                font=ctk.CTkFont(size=16),
                text_color="red",
            ).pack(pady=40)

    def mostrar_buscar_documento(self):
        """Muestra el módulo de búsqueda en el panel"""
        self.limpiar_panel_contenido()

        try:
            container = ctk.CTkFrame(self.panel_contenido, fg_color="transparent")
            container.pack(fill="both", expand=True, padx=20, pady=20)

            ventana = VentanaBuscarDocumento(container, self.db, es_integrado=True)

            if hasattr(ventana, "set_callback_actualizar"):
                ventana.set_callback_actualizar(self.actualizar_estadisticas_menu)

        except Exception as e:
            print(f"Error al mostrar buscar documento: {e}")
            error_frame = ctk.CTkFrame(self.panel_contenido)
            error_frame.pack(fill="both", expand=True, padx=40, pady=40)
            ctk.CTkLabel(
                error_frame,
                text=f"⚠️ Error al cargar módulo\n{str(e)}",
                font=ctk.CTkFont(size=16),
                text_color="red",
            ).pack(pady=40)

    def mostrar_crear_documento(self):
        """Muestra el módulo de creación en el panel"""
        self.limpiar_panel_contenido()

        try:
            container = ctk.CTkFrame(self.panel_contenido, fg_color="transparent")
            container.pack(fill="both", expand=True, padx=20, pady=20)

            ventana = VentanaCrearDocumento(container, self.db, es_integrado=True)

            if hasattr(ventana, "set_callback_actualizar"):
                ventana.set_callback_actualizar(self.actualizar_estadisticas_menu)

        except Exception as e:
            print(f"Error al mostrar crear documento: {e}")
            error_frame = ctk.CTkFrame(self.panel_contenido)
            error_frame.pack(fill="both", expand=True, padx=40, pady=40)
            ctk.CTkLabel(
                error_frame,
                text=f"⚠️ Error al cargar módulo\n{str(e)}",
                font=ctk.CTkFont(size=16),
                text_color="red",
            ).pack(pady=40)

    def mostrar_gestion_usuarios(self):
        """Muestra el módulo de gestión de usuarios en el panel (solo admin)."""
        # Restringir a admin
        if not self.usuario_actual or self.usuario_actual.get("rol") != "admin":
            messagebox.showwarning(
                "Acceso restringido",
                "Solo un administrador puede gestionar usuarios.",
            )
            return

        self.limpiar_panel_contenido()

        try:
            container = ctk.CTkFrame(self.panel_contenido, fg_color="transparent")
            container.pack(fill="both", expand=True, padx=20, pady=20)

            VentanaGestionUsuarios(container, self.db)

        except Exception as e:
            print(f"Error al mostrar gestión de usuarios: {e}")
            error_frame = ctk.CTkFrame(self.panel_contenido)
            error_frame.pack(fill="both", expand=True, padx=40, pady=40)
            ctk.CTkLabel(
                error_frame,
                text=f"⚠️ Error al cargar módulo de usuarios\n{str(e)}",
                font=ctk.CTkFont(size=16),
                text_color="red",
            ).pack(pady=40)

    # =============== ESTADÍSTICAS / CIERRE ===============

    def actualizar_estadisticas_menu(self):
        """Actualiza las estadísticas en la barra de estado inferior."""
        try:
            # Personas desde la BD
            self.db.cursor.execute("SELECT COUNT(*) FROM personas")
            total_personas = self.db.cursor.fetchone()[0]

            # Documentos REALES en la carpeta
            total_documentos = 0
            if os.path.exists(DOCUMENTOS_DIR):
                archivos = os.listdir(DOCUMENTOS_DIR)
                total_documentos = sum(
                    1
                    for f in archivos
                    if f.lower().endswith((".doc", ".docx"))
                )

            # Plantilla activa desde la BD
            self.db.cursor.execute(
                "SELECT COUNT(*) FROM plantillas WHERE activa = 1"
            )
            plantilla_activa = self.db.cursor.fetchone()[0]

            # Actualizar labels de barra de estado
            self.lbl_status_personas.configure(
                text=f"👥 Personas: {total_personas}"
            )
            self.lbl_status_documentos.configure(
                text=f"📄 Documentos: {total_documentos}"
            )
            estado = "✅" if plantilla_activa > 0 else "❌"
            self.lbl_status_plantilla.configure(
                text=f"📋 Plantilla: {estado}"
            )

        except Exception as e:
            if hasattr(self, "lbl_status_msg"):
                self.lbl_status_msg.configure(text=f"Error estadísticas: {e}")
            else:
                print(f"Error al actualizar estadísticas: {e}")

    # ================== BACKUP / RESTAURACIÓN ==================

    def _mostrar_dialogo_backup(self):
        """Muestra una ventana emergente para elegir Exportar / Importar backup - ADAPTADO"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Backup del sistema")

        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)

        # Centrar respecto a la ventana principal
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (DIALOG_WIDTH // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (DIALOG_HEIGHT // 2)
        dialog.geometry(f"{DIALOG_WIDTH}x{DIALOG_HEIGHT}+{x}+{y}")

        frame = ctk.CTkFrame(dialog)
        frame.pack(fill="both", expand=True, padx=PADDING_LARGE, pady=PADDING_LARGE)

        ctk.CTkLabel(
            frame,
            text="Gestión de backup",
            font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight="bold"),
        ).pack(pady=(PADDING_MEDIUM, PADDING_TINY))

        ctk.CTkLabel(
            frame,
            text="Seleccione si desea exportar un nuevo backup\n"
                "o importar/restaurar uno existente.",
            font=ctk.CTkFont(size=FONT_SIZE_BUTTON),
            text_color="gray80",
            justify="center",
        ).pack(pady=(0, PADDING_LARGE))

        btn_exportar = ctk.CTkButton(
            frame,
            text="⬆️  Exportar backup",
            fg_color=COLOR_PRIMARY,
            hover_color="#2980b9",
            height=BUTTON_HEIGHT_SMALL,
            command=lambda: (dialog.destroy(), self._accion_exportar_backup()),
        )
        btn_exportar.pack(pady=PADDING_TINY, fill="x")

        btn_importar = ctk.CTkButton(
            frame,
            text="⬇️  Importar backup",
            fg_color=COLOR_SUCCESS,
            hover_color="#27ae60",
            height=BUTTON_HEIGHT_SMALL,
            command=lambda: (dialog.destroy(), self._accion_importar_backup()),
        )
        btn_importar.pack(pady=PADDING_TINY, fill="x")

        ctk.CTkButton(
            frame,
            text="Cancelar",
            fg_color="#555555",
            hover_color="#666666",
            height=BUTTON_HEIGHT_SMALL,
            command=dialog.destroy,
        ).pack(pady=(PADDING_LARGE, PADDING_TINY), fill="x")

        dialog.wait_window()

    def _accion_exportar_backup(self):
        """Exporta documentos + base de datos a la carpeta elegida."""
        carpeta = filedialog.askdirectory(
            title="Seleccionar carpeta para guardar el backup"
        )

        if not carpeta:
            # Usuario canceló
            return

        try:
            zip_docs, backup_db = hacer_backup_completo(carpeta)
            messagebox.showinfo(
                "Backup",
                "Backup generado correctamente en:\n\n"
                f"{carpeta}\n\n"
                f"- Documentos: {os.path.basename(zip_docs)}\n"
                f"- Base de datos: {os.path.basename(backup_db)}"
            )
        except Exception as e:
            messagebox.showerror(
                "Error de backup",
                f"Ocurrió un error al realizar el backup:\n{e}"
            )

    def _accion_importar_backup(self):
        """Importa/restaura documentos + base de datos desde archivos de backup."""
        # Seleccionar archivo ZIP de documentos
        zip_docs = filedialog.askopenfilename(
            title="Seleccionar ZIP de documentos",
            filetypes=[("Archivos ZIP", "*.zip"), ("Todos los archivos", "*.*")]
        )

        if not zip_docs:
            # Usuario canceló
            return

        # Seleccionar archivo .db de backup
        backup_db = filedialog.askopenfilename(
            title="Seleccionar archivo de backup de base de datos",
            filetypes=[("SQLite DB", "*.db"), ("Todos los archivos", "*.*")]
        )

        if not backup_db:
            # Usuario canceló
            return

        # Confirmación fuerte (puede sobrescribir datos)
        if not messagebox.askyesno(
            "Confirmar restauración",
            "Esta acción sobrescribirá la base de datos actual y puede\n"
            "reemplazar documentos existentes.\n\n"
            "¿Desea continuar?"
        ):
            return

        try:
            restaurar_backup_completo(
                zip_docs=zip_docs,
                backup_db=backup_db,
                limpiar_docs=True
            )
            messagebox.showinfo(
                "Restauración completa",
                "Backup restaurado correctamente.\n"
                "Se han restaurado documentos y base de datos."
            )
            # Actualizar estadísticas tras restaurar
            self.actualizar_estadisticas_menu()
        except Exception as e:
            messagebox.showerror(
                "Error de restauración",
                f"Ocurrió un error al restaurar el backup:\n{e}"
            )
    
    def _accion_backup(self):
        # Seleccionar carpeta destino para el backup
        carpeta = filedialog.askdirectory(
            title="Seleccionar carpeta para guardar el backup"
        )

        if not carpeta:
            # Usuario canceló
            return

        try:
            zip_docs, backup_db = hacer_backup_completo(carpeta)
            messagebox.showinfo(
                "Backup",
                "Backup generado correctamente en:\n\n"
                f"{carpeta}\n\n"
                f"- Documentos: {os.path.basename(zip_docs)}\n"
                f"- Base de datos: {os.path.basename(backup_db)}"
            )
        except Exception as e:
            messagebox.showerror(
                "Error de backup",
                f"Ocurrió un error al realizar el backup:\n{e}"
            )
    
    def on_closing(self):
        """Maneja el cierre de la aplicación y limpia callbacks pendientes."""
        # Cerrar DB
        try:
            self.db.cerrar()
        except Exception:
            pass

        # Cancelar afters pendientes asociados a esta ventana
        try:
            afters = self.tk.call("after", "info")
            if afters:
                for aid in str(afters).split():
                    try:
                        self.after_cancel(aid)
                    except Exception:
                        pass
        except Exception:
            pass

        # Destruir ventana principal
        self.destroy()