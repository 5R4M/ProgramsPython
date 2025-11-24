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
        
        # Crear interfaz
        self.crear_interfaz()
        
        # Centrar y maximizar ventana
        self.center_window()
        self.after(100, self.maximizar_ventana)
    
    def maximizar_ventana(self):
        """Maximiza la ventana"""
        self.state('zoomed')  # Para Windows
        # self.attributes('-zoomed', True)  # Para Linux
        # self.state('zoomed')  # Para macOS también funciona
    
    def center_window(self):
        """Centra la ventana en la pantalla"""
        # Establecer tamaño inicial antes de centrar
        self.geometry(WINDOW_SIZE)
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def crear_interfaz(self):
        """Crea la interfaz principal"""
        
        # Frame principal
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        titulo = ctk.CTkLabel(
            main_frame,
            text="📋 Sistema de Actas Notariales",
            font=ctk.CTkFont(size=36, weight="bold")
        )
        titulo.pack(pady=40)
        
        # Subtítulo
        subtitulo = ctk.CTkLabel(
            main_frame,
            text="Gestión integral de documentos notariales",
            font=ctk.CTkFont(size=18),
            text_color="gray"
        )
        subtitulo.pack(pady=10)
        
        # Frame para los botones principales
        botones_frame = ctk.CTkFrame(main_frame)
        botones_frame.pack(pady=60, padx=100, fill="both", expand=True)
        
        # Configurar grid
        botones_frame.grid_columnconfigure(0, weight=1)
        botones_frame.grid_columnconfigure(1, weight=1)
        botones_frame.grid_columnconfigure(2, weight=1)
        
        # Botón 1: Cargar Documentos
        btn_cargar = ctk.CTkButton(
            botones_frame,
            text="📥\n\nCargar Documentos\n\nImportar documentos .doc/.docx\na la base de datos",
            command=self.abrir_cargar_documentos,
            height=250,
            width=300,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color=COLOR_PRIMARY,
            hover_color="#2980b9",
            corner_radius=15
        )
        btn_cargar.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        # Botón 2: Buscar Documento
        btn_buscar = ctk.CTkButton(
            botones_frame,
            text="🔍\n\nBuscar Documento\n\nBuscar por nombre o DPI\nen la base de datos",
            command=self.abrir_buscar_documento,
            height=250,
            width=300,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color=COLOR_SUCCESS,
            hover_color="#27ae60",
            corner_radius=15
        )
        btn_buscar.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        # Botón 3: Crear Documento Nuevo
        btn_crear = ctk.CTkButton(
            botones_frame,
            text="➕\n\nCrear Documento\n\nGenerar nuevo documento\ncon plantilla",
            command=self.abrir_crear_documento,
            height=250,
            width=300,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color=COLOR_WARNING,
            hover_color="#e67e22",
            corner_radius=15
        )
        btn_crear.grid(row=0, column=2, padx=20, pady=20, sticky="nsew")
        
        # Frame inferior con información
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(pady=20, fill="x")
        
        # Estadísticas
        self.actualizar_estadisticas(info_frame)
        
        # Pie de página
        footer = ctk.CTkLabel(
            main_frame,
            text=f"© 2025 {APP_NAME} - Versión {APP_VERSION}",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        footer.pack(pady=10)
    
    def actualizar_estadisticas(self, parent_frame):
        """Actualiza las estadísticas en la ventana principal"""
        
        # Limpiar frame
        for widget in parent_frame.winfo_children():
            widget.destroy()
        
        # Obtener estadísticas
        self.db.cursor.execute('SELECT COUNT(*) FROM personas')
        total_personas = self.db.cursor.fetchone()[0]
        
        self.db.cursor.execute('SELECT COUNT(*) FROM documentos')
        total_documentos = self.db.cursor.fetchone()[0]
        
        self.db.cursor.execute('SELECT COUNT(*) FROM plantillas WHERE activa = 1')
        plantilla_activa = self.db.cursor.fetchone()[0]
        
        # Crear labels de estadísticas
        stats_frame = ctk.CTkFrame(parent_frame)
        stats_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(
            stats_frame,
            text=f"👥 Personas registradas: {total_personas}",
            font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=20)
        
        ctk.CTkLabel(
            stats_frame,
            text=f"📄 Documentos cargados: {total_documentos}",
            font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=20)
        
        estado_plantilla = "✅ Activa" if plantilla_activa > 0 else "❌ No configurada"
        color_plantilla = "green" if plantilla_activa > 0 else "red"
        
        ctk.CTkLabel(
            stats_frame,
            text=f"📋 Plantilla: {estado_plantilla}",
            font=ctk.CTkFont(size=14),
            text_color=color_plantilla
        ).pack(side="left", padx=20)
    
    def abrir_cargar_documentos(self):
        """Abre la ventana de carga de documentos"""
        ventana = VentanaCargarDocumentos(self, self.db)
        ventana.grab_set()
    
    def abrir_buscar_documento(self):
        """Abre la ventana de búsqueda de documentos"""
        ventana = VentanaBuscarDocumento(self, self.db)
        ventana.grab_set()
    
    def abrir_crear_documento(self):
        """Abre la ventana de creación de documentos"""
        ventana = VentanaCrearDocumento(self, self.db)
        ventana.grab_set()
    
    def on_closing(self):
        """Maneja el cierre de la aplicación"""
        self.db.cerrar()
        self.destroy()