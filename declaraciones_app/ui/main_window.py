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
)
from database import DatabaseManager
from .cargar_documentos import VentanaCargarDocumentos
from .buscar_documento import VentanaBuscarDocumento
from .crear_documento import VentanaCrearDocumento
from .ventana_usuarios import VentanaGestionUsuarios


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
        """Crea la interfaz principal con menú lateral"""

        # ===== BARRA DE ESTADO INFERIOR =====
        self.status_bar = ctk.CTkFrame(self, height=28, fg_color="gray15")
        self.status_bar.pack(fill="x", side="bottom")

        self.lbl_status_personas = ctk.CTkLabel(
            self.status_bar, text="👥 Personas: 0", font=ctk.CTkFont(size=11)
        )
        self.lbl_status_personas.pack(side="left", padx=10)

        self.lbl_status_documentos = ctk.CTkLabel(
            self.status_bar, text="📄 Documentos: 0", font=ctk.CTkFont(size=11)
        )
        self.lbl_status_documentos.pack(side="left", padx=10)

        self.lbl_status_plantilla = ctk.CTkLabel(
            self.status_bar, text="📋 Plantilla: ❌", font=ctk.CTkFont(size=11)
        )
        self.lbl_status_plantilla.pack(side="left", padx=10)

        # Mensaje de estado / usuario a la derecha
        if self.usuario_actual:
            texto_status = f"Usuario: {self.usuario_actual['username']} ({self.usuario_actual.get('rol', '')})"
        else:
            texto_status = "Listo"

        self.lbl_status_msg = ctk.CTkLabel(
            self.status_bar,
            text=texto_status,
            font=ctk.CTkFont(size=11),
            text_color="gray80",
        )
        self.lbl_status_msg.pack(side="right", padx=10)

        # ===== CONTENEDOR PRINCIPAL =====
        # Misma paleta de color, sin bordes, para que no se vea línea entre paneles
        container = ctk.CTkFrame(
            self,
            fg_color="gray10",
            corner_radius=0,
            border_width=0,
        )
        container.pack(fill="both", expand=True)

        # Configurar grid
        container.grid_columnconfigure(0, weight=0)  # Menú lateral (fijo)
        container.grid_columnconfigure(1, weight=1)  # Panel contenido (expandible)
        container.grid_rowconfigure(0, weight=1)

        # ===== MENÚ LATERAL IZQUIERDO =====
        menu_lateral = ctk.CTkFrame(
            container,
            width=280,
            corner_radius=0,
            fg_color="gray10",
            border_width=0,
        )
        menu_lateral.grid(row=0, column=0, sticky="nsew")
        menu_lateral.grid_propagate(False)

        # Logo/Título del menú
        frame_logo = ctk.CTkFrame(
            menu_lateral, fg_color="transparent", corner_radius=0
        )
        frame_logo.pack(fill="x", pady=25)

        # Icono principal más grande
        ctk.CTkLabel(
            frame_logo, text="📋", font=ctk.CTkFont(size=60)
        ).pack(pady=5)

        ctk.CTkLabel(
            frame_logo,
            text="Sistema de Actas\nNotariales",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(0, 15))

        # Botones del menú
        ctk.CTkLabel(
            menu_lateral,
            text="⚙️ Opciones",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(pady=(10, 15), padx=15, anchor="w")

        btn_inicio = ctk.CTkButton(
            menu_lateral,
            text="🏠  Inicio",
            command=self.mostrar_inicio,
            height=48,
            font=ctk.CTkFont(size=16),
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            corner_radius=8,
        )
        btn_inicio.pack(pady=5, padx=15, fill="x")

        btn_cargar = ctk.CTkButton(
            menu_lateral,
            text="📥  Cargar Documentos",
            command=self.mostrar_cargar_documentos,
            height=48,
            font=ctk.CTkFont(size=16),
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            corner_radius=8,
        )
        btn_cargar.pack(pady=5, padx=15, fill="x")

        btn_buscar = ctk.CTkButton(
            menu_lateral,
            text="🔍  Buscar Documento",
            command=self.mostrar_buscar_documento,
            height=48,
            font=ctk.CTkFont(size=16),
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            corner_radius=8,
        )
        btn_buscar.pack(pady=5, padx=15, fill="x")

        btn_crear = ctk.CTkButton(
            menu_lateral,
            text="➕  Crear Documento",
            command=self.mostrar_crear_documento,
            height=48,
            font=ctk.CTkFont(size=16),
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            corner_radius=8,
        )
        btn_crear.pack(pady=5, padx=15, fill="x")

        # Botón de Backup (se coloca también en el menú lateral)
        self.btn_backup = ctk.CTkButton(
            menu_lateral,
            text="🧾  Backup",
            command=self._mostrar_dialogo_backup,
            height=48,
            font=ctk.CTkFont(size=16),
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            corner_radius=8,
        )
        self.btn_backup.pack(pady=5, padx=15, fill="x")
        
        # Botón de gestión de usuarios (irá DEBAJO de "Crear Documento")
        self.btn_usuarios = ctk.CTkButton(
            menu_lateral,
            text="👥  Usuarios",
            command=self.mostrar_gestion_usuarios,
            height=48,
            font=ctk.CTkFont(size=16),
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            corner_radius=8,
        )
        # Lo empaquetamos ya en la posición deseada
        self.btn_usuarios.pack(pady=5, padx=15, fill="x")

        # Espaciador
        ctk.CTkFrame(menu_lateral, fg_color="transparent").pack(
            fill="both", expand=True
        )

        # Botón Salir del sistema
        btn_salir = ctk.CTkButton(
            menu_lateral,
            text="🚪  Salir del sistema",
            command=self.on_closing,
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#c0392b",
            hover_color="#e74c3c",
            text_color="white",
            corner_radius=8,
        )
        btn_salir.pack(pady=(0, 10), padx=15, fill="x")

        # Footer del menú
        footer_menu = ctk.CTkFrame(menu_lateral, fg_color="transparent")
        footer_menu.pack(fill="x", pady=5, padx=15)

        ctk.CTkLabel(
            footer_menu,
            text=f"v{APP_VERSION}",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        ).pack()

        # ===== PANEL DE CONTENIDO DERECHO =====
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
        """Muestra la pantalla de inicio"""
        self.limpiar_panel_contenido()

        frame_inicio = ctk.CTkFrame(self.panel_contenido)
        frame_inicio.pack(fill="both", expand=True, padx=40, pady=40)

        ctk.CTkLabel(
            frame_inicio,
            text="📋 Sistema de Actas Notariales",
            font=ctk.CTkFont(size=42, weight="bold"),
        ).pack(pady=(60, 20))

        ctk.CTkLabel(
            frame_inicio,
            text="Gestión integral de documentos notariales",
            font=ctk.CTkFont(size=20),
            text_color="gray",
        ).pack(pady=10)

        # Tarjetas de acceso rápido
        cards_frame = ctk.CTkFrame(frame_inicio, fg_color="transparent")
        cards_frame.pack(pady=60, fill="both", expand=True)

        # Ahora soportamos 4 columnas (la 3 será para Backup)
        cards_frame.grid_columnconfigure(0, weight=1)
        cards_frame.grid_columnconfigure(1, weight=1)
        cards_frame.grid_columnconfigure(2, weight=1)
        cards_frame.grid_columnconfigure(3, weight=1)

        # Card 1 - Cargar documentos
        card1 = ctk.CTkFrame(cards_frame, corner_radius=15)
        card1.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        ctk.CTkLabel(card1, text="📥", font=ctk.CTkFont(size=50)).pack(pady=20)

        ctk.CTkLabel(
            card1,
            text="Cargar Documentos",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=10)

        ctk.CTkLabel(
            card1,
            text="Importar documentos .doc/.docx\na la base de datos",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        ).pack(pady=10)

        ctk.CTkButton(
            card1,
            text="Abrir",
            command=self.mostrar_cargar_documentos,
            fg_color=COLOR_PRIMARY,
            hover_color="#2980b9",
        ).pack(pady=20)

        # Card 2 - Buscar documento
        card2 = ctk.CTkFrame(cards_frame, corner_radius=15)
        card2.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        ctk.CTkLabel(card2, text="🔍", font=ctk.CTkFont(size=50)).pack(pady=20)

        ctk.CTkLabel(
            card2,
            text="Buscar Documento",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=10)

        ctk.CTkLabel(
            card2,
            text="Buscar por nombre o DPI\nen la base de datos",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        ).pack(pady=10)

        ctk.CTkButton(
            card2,
            text="Abrir",
            command=self.mostrar_buscar_documento,
            fg_color=COLOR_SUCCESS,
            hover_color="#27ae60",
        ).pack(pady=20)

        # Card 3 - Crear documento
        card3 = ctk.CTkFrame(cards_frame, corner_radius=15)
        card3.grid(row=0, column=2, padx=20, pady=20, sticky="nsew")

        ctk.CTkLabel(card3, text="➕", font=ctk.CTkFont(size=50)).pack(pady=20)

        ctk.CTkLabel(
            card3,
            text="Crear Documento",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=10)

        ctk.CTkLabel(
            card3,
            text="Generar nuevo documento\ncon plantilla",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        ).pack(pady=10)

        ctk.CTkButton(
            card3,
            text="Abrir",
            command=self.mostrar_crear_documento,
            fg_color=COLOR_WARNING,
            hover_color="#e67e22",
        ).pack(pady=20)

        # Card 4 - Backup
        card4 = ctk.CTkFrame(cards_frame, corner_radius=15)
        card4.grid(row=0, column=3, padx=20, pady=20, sticky="nsew")

        ctk.CTkLabel(card4, text="🧾", font=ctk.CTkFont(size=50)).pack(pady=20)

        ctk.CTkLabel(
            card4,
            text="Backup",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=10)

        ctk.CTkLabel(
            card4,
            text="Crear copia de seguridad\nde documentos y base de datos",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            justify="center",
        ).pack(pady=10)

        ctk.CTkButton(
            card4,
            text="Abrir gestor de backup",
            command=self._mostrar_dialogo_backup,
            fg_color=COLOR_PRIMARY,
            hover_color="#2980b9",
        ).pack(pady=20)
        
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
        """Muestra una ventana emergente para elegir Exportar / Importar backup."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Backup del sistema")

        # Hacer la ventana modal: bloquear la principal
        dialog.transient(self)      # asociar al main window
        dialog.grab_set()           # captura de foco

        dialog.resizable(False, False)

        # Tamaño deseado
        ancho, alto = 420, 260
        # Centrar respecto a la ventana principal
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (ancho // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (alto // 2)
        dialog.geometry(f"{ancho}x{alto}+{x}+{y}")

        frame = ctk.CTkFrame(dialog)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            frame,
            text="Gestión de backup",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=(10, 5))

        ctk.CTkLabel(
            frame,
            text="Seleccione si desea exportar un nuevo backup\n"
                 "o importar/restaurar uno existente.",
            font=ctk.CTkFont(size=13),
            text_color="gray80",
            justify="center",
        ).pack(pady=(0, 20))

        btn_exportar = ctk.CTkButton(
            frame,
            text="⬆️  Exportar backup",
            fg_color=COLOR_PRIMARY,
            hover_color="#2980b9",
            command=lambda: (dialog.destroy(), self._accion_exportar_backup()),
        )
        btn_exportar.pack(pady=5, fill="x")

        btn_importar = ctk.CTkButton(
            frame,
            text="⬇️  Importar backup",
            fg_color=COLOR_SUCCESS,
            hover_color="#27ae60",
            command=lambda: (dialog.destroy(), self._accion_importar_backup()),
        )
        btn_importar.pack(pady=5, fill="x")

        ctk.CTkButton(
            frame,
            text="Cancelar",
            fg_color="#555555",
            hover_color="#666666",
            command=dialog.destroy,
        ).pack(pady=(20, 5), fill="x")

        # Esperar hasta que se cierre el diálogo (mantiene el bloqueo modal)
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