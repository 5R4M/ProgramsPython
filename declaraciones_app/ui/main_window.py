import customtkinter as ctk
from config import APP_NAME, APP_VERSION, WINDOW_SIZE, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING
from database import DatabaseManager
from .cargar_documentos import VentanaCargarDocumentos
from .buscar_documento import VentanaBuscarDocumento
from .crear_documento import VentanaCrearDocumento

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title(f"{APP_NAME} - v{APP_VERSION}")
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Inicializar base de datos
        self.db = DatabaseManager()
        
        self.info_frame = None
        self.panel_contenido = None
        
        # Crear interfaz
        self.crear_interfaz()
        
        # Centrar y maximizar ventana
        self.center_window()
        self.after(100, self.maximizar_ventana)
        
        # Configurar el protocolo de cierre
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def maximizar_ventana(self):
        """Maximiza la ventana"""
        self.state('zoomed')
    
    def center_window(self):
        """Centra la ventana en la pantalla"""
        self.geometry(WINDOW_SIZE)
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def crear_interfaz(self):
        """Crea la interfaz principal con menú lateral"""
        
        # Container principal
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True)
        
        # Configurar grid
        container.grid_columnconfigure(0, weight=0)  # Menú lateral (fijo)
        container.grid_columnconfigure(1, weight=1)  # Panel contenido (expandible)
        container.grid_rowconfigure(0, weight=1)
        
        # ===== MENÚ LATERAL IZQUIERDO =====
        menu_lateral = ctk.CTkFrame(container, width=280, corner_radius=0)
        menu_lateral.grid(row=0, column=0, sticky="nsew")
        menu_lateral.grid_propagate(False)
        
        # Logo/Título del menú
        frame_logo = ctk.CTkFrame(menu_lateral, fg_color="transparent", corner_radius=0)
        frame_logo.pack(fill="x", pady=20)

        ctk.CTkLabel(
            frame_logo,
            text="📋",
            font=ctk.CTkFont(size=40)
        ).pack(pady=10)

        ctk.CTkLabel(
            frame_logo,
            text="Sistema de Actas\nNotariales",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(0, 15))
        
        # Frame para estadísticas
        stats_frame = ctk.CTkFrame(menu_lateral)
        stats_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(
            stats_frame,
            text="📊 Estadísticas",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=10)
        
        self.lbl_personas = ctk.CTkLabel(
            stats_frame,
            text="👥 Personas: 0",
            font=ctk.CTkFont(size=12)
        )
        self.lbl_personas.pack(pady=5, anchor="w", padx=10)
        
        self.lbl_documentos = ctk.CTkLabel(
            stats_frame,
            text="📄 Documentos: 0",
            font=ctk.CTkFont(size=12)
        )
        self.lbl_documentos.pack(pady=5, anchor="w", padx=10)
        
        self.lbl_plantilla = ctk.CTkLabel(
            stats_frame,
            text="📋 Plantilla: ❌",
            font=ctk.CTkFont(size=12)
        )
        self.lbl_plantilla.pack(pady=5, anchor="w", padx=10)
        
        # Separador
        ctk.CTkFrame(menu_lateral, height=2, fg_color="gray30").pack(fill="x", padx=15, pady=10)
        
        # Botones del menú
        ctk.CTkLabel(
            menu_lateral,
            text="⚙️ Opciones",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 15), padx=15, anchor="w")
        
        btn_inicio = ctk.CTkButton(
            menu_lateral,
            text="🏠  Inicio",
            command=self.mostrar_inicio,
            height=45,
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            corner_radius=8
        )
        btn_inicio.pack(pady=5, padx=15, fill="x")
        
        btn_cargar = ctk.CTkButton(
            menu_lateral,
            text="📥  Cargar Documentos",
            command=self.mostrar_cargar_documentos,
            height=45,
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            corner_radius=8
        )
        btn_cargar.pack(pady=5, padx=15, fill="x")
        
        btn_buscar = ctk.CTkButton(
            menu_lateral,
            text="🔍  Buscar Documento",
            command=self.mostrar_buscar_documento,
            height=45,
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            corner_radius=8
        )
        btn_buscar.pack(pady=5, padx=15, fill="x")
        
        btn_crear = ctk.CTkButton(
            menu_lateral,
            text="➕  Crear Documento",
            command=self.mostrar_crear_documento,
            height=45,
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            corner_radius=8
        )
        btn_crear.pack(pady=5, padx=15, fill="x")
        
        # Espaciador
        ctk.CTkFrame(menu_lateral, fg_color="transparent").pack(fill="both", expand=True)
        
        # Footer del menú
        footer_menu = ctk.CTkFrame(menu_lateral, fg_color="transparent")
        footer_menu.pack(fill="x", pady=15, padx=15)
        
        ctk.CTkLabel(
            footer_menu,
            text=f"v{APP_VERSION}",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        ).pack()
        
        # ===== PANEL DE CONTENIDO DERECHO =====
        self.panel_contenido = ctk.CTkFrame(container, corner_radius=0)
        self.panel_contenido.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        
        # Mostrar pantalla de inicio por defecto
        self.mostrar_inicio()
        
        # Actualizar estadísticas iniciales
        self.actualizar_estadisticas_menu()
    
    def limpiar_panel_contenido(self):
        """Limpia el panel de contenido"""
        for widget in self.panel_contenido.winfo_children():
            widget.destroy()
    
    def mostrar_inicio(self):
        """Muestra la pantalla de inicio"""
        self.limpiar_panel_contenido()
        
        frame_inicio = ctk.CTkFrame(self.panel_contenido)
        frame_inicio.pack(fill="both", expand=True, padx=40, pady=40)
        
        ctk.CTkLabel(
            frame_inicio,
            text="📋 Sistema de Actas Notariales",
            font=ctk.CTkFont(size=42, weight="bold")
        ).pack(pady=(60, 20))
        
        ctk.CTkLabel(
            frame_inicio,
            text="Gestión integral de documentos notariales",
            font=ctk.CTkFont(size=20),
            text_color="gray"
        ).pack(pady=10)
        
        # Tarjetas de acceso rápido
        cards_frame = ctk.CTkFrame(frame_inicio, fg_color="transparent")
        cards_frame.pack(pady=60, fill="both", expand=True)
        
        cards_frame.grid_columnconfigure(0, weight=1)
        cards_frame.grid_columnconfigure(1, weight=1)
        cards_frame.grid_columnconfigure(2, weight=1)
        
        # Card 1
        card1 = ctk.CTkFrame(cards_frame, corner_radius=15)
        card1.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        ctk.CTkLabel(
            card1,
            text="📥",
            font=ctk.CTkFont(size=50)
        ).pack(pady=20)
        
        ctk.CTkLabel(
            card1,
            text="Cargar Documentos",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)
        
        ctk.CTkLabel(
            card1,
            text="Importar documentos .doc/.docx\na la base de datos",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(pady=10)
        
        ctk.CTkButton(
            card1,
            text="Abrir",
            command=self.mostrar_cargar_documentos,
            fg_color=COLOR_PRIMARY,
            hover_color="#2980b9"
        ).pack(pady=20)
        
        # Card 2
        card2 = ctk.CTkFrame(cards_frame, corner_radius=15)
        card2.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        ctk.CTkLabel(
            card2,
            text="🔍",
            font=ctk.CTkFont(size=50)
        ).pack(pady=20)
        
        ctk.CTkLabel(
            card2,
            text="Buscar Documento",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)
        
        ctk.CTkLabel(
            card2,
            text="Buscar por nombre o DPI\nen la base de datos",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(pady=10)
        
        ctk.CTkButton(
            card2,
            text="Abrir",
            command=self.mostrar_buscar_documento,
            fg_color=COLOR_SUCCESS,
            hover_color="#27ae60"
        ).pack(pady=20)
        
        # Card 3
        card3 = ctk.CTkFrame(cards_frame, corner_radius=15)
        card3.grid(row=0, column=2, padx=20, pady=20, sticky="nsew")
        
        ctk.CTkLabel(
            card3,
            text="➕",
            font=ctk.CTkFont(size=50)
        ).pack(pady=20)
        
        ctk.CTkLabel(
            card3,
            text="Crear Documento",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)
        
        ctk.CTkLabel(
            card3,
            text="Generar nuevo documento\ncon plantilla",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(pady=10)
        
        ctk.CTkButton(
            card3,
            text="Abrir",
            command=self.mostrar_crear_documento,
            fg_color=COLOR_WARNING,
            hover_color="#e67e22"
        ).pack(pady=20)
        
        self.actualizar_estadisticas_menu()
    
    def mostrar_cargar_documentos(self):
        """Muestra el módulo de carga de documentos en el panel"""
        self.limpiar_panel_contenido()
        
        # Crear instancia integrada en el panel
        try:
            # Frame contenedor con padding
            container = ctk.CTkFrame(self.panel_contenido, fg_color="transparent")
            container.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Crear la ventana como frame integrado
            ventana = VentanaCargarDocumentos(container, self.db, es_integrado=True)
            
            # Agregar callback para actualizar estadísticas
            if hasattr(ventana, 'set_callback_actualizar'):
                ventana.set_callback_actualizar(self.actualizar_estadisticas_menu)
                
        except Exception as e:
            print(f"Error al mostrar cargar documentos: {e}")
            # Mostrar mensaje de error en el panel
            error_frame = ctk.CTkFrame(self.panel_contenido)
            error_frame.pack(fill="both", expand=True, padx=40, pady=40)
            ctk.CTkLabel(
                error_frame,
                text=f"⚠️ Error al cargar módulo\n{str(e)}",
                font=ctk.CTkFont(size=16),
                text_color="red"
            ).pack(pady=40)
    
    def mostrar_buscar_documento(self):
        """Muestra el módulo de búsqueda en el panel"""
        self.limpiar_panel_contenido()
        
        try:
            container = ctk.CTkFrame(self.panel_contenido, fg_color="transparent")
            container.pack(fill="both", expand=True, padx=20, pady=20)
            
            ventana = VentanaBuscarDocumento(container, self.db, es_integrado=True)
            
            if hasattr(ventana, 'set_callback_actualizar'):
                ventana.set_callback_actualizar(self.actualizar_estadisticas_menu)
                
        except Exception as e:
            print(f"Error al mostrar buscar documento: {e}")
            error_frame = ctk.CTkFrame(self.panel_contenido)
            error_frame.pack(fill="both", expand=True, padx=40, pady=40)
            ctk.CTkLabel(
                error_frame,
                text=f"⚠️ Error al cargar módulo\n{str(e)}",
                font=ctk.CTkFont(size=16),
                text_color="red"
            ).pack(pady=40)
    
    def mostrar_crear_documento(self):
        """Muestra el módulo de creación en el panel"""
        self.limpiar_panel_contenido()
        
        try:
            container = ctk.CTkFrame(self.panel_contenido, fg_color="transparent")
            container.pack(fill="both", expand=True, padx=20, pady=20)
            
            ventana = VentanaCrearDocumento(container, self.db, es_integrado=True)
            
            if hasattr(ventana, 'set_callback_actualizar'):
                ventana.set_callback_actualizar(self.actualizar_estadisticas_menu)
                
        except Exception as e:
            print(f"Error al mostrar crear documento: {e}")
            error_frame = ctk.CTkFrame(self.panel_contenido)
            error_frame.pack(fill="both", expand=True, padx=40, pady=40)
            ctk.CTkLabel(
                error_frame,
                text=f"⚠️ Error al cargar módulo\n{str(e)}",
                font=ctk.CTkFont(size=16),
                text_color="red"
            ).pack(pady=40)
    
    def actualizar_estadisticas_menu(self):
        """Actualiza las estadísticas en el menú lateral"""
        try:
            # Obtener estadísticas
            self.db.cursor.execute('SELECT COUNT(*) FROM personas')
            total_personas = self.db.cursor.fetchone()[0]
            
            self.db.cursor.execute('SELECT COUNT(*) FROM documentos')
            total_documentos = self.db.cursor.fetchone()[0]
            
            self.db.cursor.execute('SELECT COUNT(*) FROM plantillas WHERE activa = 1')
            plantilla_activa = self.db.cursor.fetchone()[0]
            
            # Actualizar labels
            self.lbl_personas.configure(text=f"👥 Personas: {total_personas}")
            self.lbl_documentos.configure(text=f"📄 Documentos: {total_documentos}")
            
            estado = "✅" if plantilla_activa > 0 else "❌"
            self.lbl_plantilla.configure(text=f"📋 Plantilla: {estado}")
            
        except Exception as e:
            print(f"Error al actualizar estadísticas: {e}")
    
    def on_closing(self):
        """Maneja el cierre de la aplicación"""
        try:
            self.db.cerrar()
        except:  # noqa: E722
            pass
        finally:
            self.destroy()