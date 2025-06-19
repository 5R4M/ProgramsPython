import tkinter as tk
import sqlite3
from tkinter import ttk
from tkinter import messagebox
import sys
import os
from PIL import Image, ImageTk
from ttkthemes import ThemedStyle

# Agregar el directorio raíz del proyecto al PATH de Python
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# Importar las funciones de la base de datos
from src.database import DB_PATH, crear_base_datos, verificar_tablas
from src.gui.ingreso_insumos import IngresoInsumos
from src.gui.gestion_insumos import GestionInsumos
from src.gui.gestion_servicios import GestionServicios
from src.gui.gestion_movimientos import GestionMovimientos
from src.gui.reporte_kardex import ReporteKardex
from src.gui.reporte_demanda_real import ReporteDemandaReal
from src.gui.reporte_bres import ReporteBres
from src.gui.importar_exportar_manager import ImportarExportarManager, crear_gestor_importar_exportar

class MainWindow:
    def __init__(self, usuario):
        self.usuario = usuario

        # **CONFIGURACIÓN DE TAMAÑO ESTÁNDAR PARA TODAS LAS VENTANAS**
        self.ANCHO_VENTANA = 1200  # Ancho estándar
        self.ALTO_VENTANA = 900    # Alto estándar

        # Inicializar la base de datos antes de crear la ventana
        if not self.initialize_database():
            messagebox.showerror("Error Fatal",
                "No se pudo inicializar la base de datos. El programa se cerrará.")
            sys.exit(1)

        self.root = tk.Tk()
        self.root.title("Sistema de Gestión de Insumos")

        # Aplicar tema moderno
        style = ThemedStyle(self.root)
        style.set_theme("arc")  # Otros temas disponibles: 'equilux', 'breeze', etc.

        self.setup_window()
        self.load_icons()
        self.create_menu()

        # Crear el frame principal que contendrá el contenido
        self.main_content_frame = ttk.Frame(self.root, style='Card.TFrame')
        self.main_content_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # Mostrar la pantalla de bienvenida inicial
        self.show_welcome_screen()

        # Agregar barra de estado en la parte inferior
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

        # Etiqueta para mostrar el usuario logueado
        nombre_usuario = self.usuario.get('nombre_completo', self.usuario.get('username', 'Usuario'))
        rol_usuario = self.usuario.get('rol', '')

        self.user_label = ttk.Label(
            self.status_bar,
            text=f"Usuario: {nombre_usuario} ({rol_usuario})",
            anchor="w",
            padding=(10, 5)
        )
        self.user_label.pack(side="left", fill="x")

        # Manejar el cierre de la ventana principal
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_icons(self):
        """Carga los iconos para los botones del menú"""
        self.icons = {}
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'icons')
        
        # Crear directorio de iconos si no existe
        if not os.path.exists(icon_path):
            os.makedirs(icon_path)
        
        # Mapeo de iconos
        icon_files = {
            'usuarios': 'usuario.png',
            'insumos': 'insumo.png',
            'servicios': 'servicio.png',
            'movimientos': 'movimiento.png',
            'import_export': 'importar-exportar.png',
            'ingreso': 'ingreso.png',
            'kardex': 'kardex.png',
            'demanda': 'demanda-real.png',
            'correcciones': 'correcion.png',
            'bres': 'bres.png',
            'salir': 'salir.png'
        }
        
        # Cargar iconos
        for key, filename in icon_files.items():
            try:
                icon_full_path = os.path.join(icon_path, filename)
                if os.path.exists(icon_full_path):
                    image = Image.open(icon_full_path)
                    image = image.resize((16, 16), Image.Resampling.LANCZOS)
                    self.icons[key] = ImageTk.PhotoImage(image)
                else:
                    self.icons[key] = None
            except Exception as e:
                print(f"Error cargando icono {filename}: {e}")
                self.icons[key] = None
    
    def setup_window(self):
        """Configura la ventana principal con tamaño estándar"""
        # Configurar tamaño y centrar ventana
        self.center_window(self.ANCHO_VENTANA, self.ALTO_VENTANA)

        # Configurar tamaño mínimo
        self.root.minsize(1200, 700)

        # Permitir redimensionamiento
        self.root.resizable(True, True)

        # Configurar el grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        # Agregar una fila para la barra de estado
        self.root.grid_rowconfigure(1, weight=0)

    def center_window(self, width, height):
        """Centra la ventana en la pantalla tanto horizontal como verticalmente"""
        # Forzar actualización para obtener dimensiones reales de la pantalla
        self.root.update_idletasks()

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Calcular posición para centrar horizontal y verticalmente
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        # Asegurar que la ventana no se posicione fuera de los límites de la pantalla
        x = max(0, x)
        y = max(0, y)

        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def resize_window_for_content(self, extra_height=0):
        """Redimensiona la ventana cuando se necesita espacio adicional"""
        nuevo_alto = self.ALTO_VENTANA + extra_height

        # Obtener posición actual
        self.root.update_idletasks()
        x = self.root.winfo_x()

        # Recalcular posición Y para mantener centrado verticalmente
        screen_height = self.root.winfo_screenheight()
        y = (screen_height - nuevo_alto) // 2

        # Ajustar posición Y si es necesario para que no se salga de la pantalla
        if y + nuevo_alto > screen_height:
            y = max(0, screen_height - nuevo_alto)
        elif y < 0:
            y = 0

        self.root.geometry(f"{self.ANCHO_VENTANA}x{nuevo_alto}+{x}+{y}")

    def reset_window_size(self):
        """Restaura el tamaño original de la ventana y la centra"""
        self.center_window(self.ANCHO_VENTANA, self.ALTO_VENTANA)

    def initialize_database(self):
        """Inicializa la base de datos y verifica su estructura"""
        try:
            # Verificar si la base de datos existe
            if not os.path.exists(DB_PATH):
                print("La base de datos no existe. Creándola...")
                if not crear_base_datos():
                    raise Exception("No se pudo crear la base de datos")
                print("Base de datos creada correctamente")

            # Verificar la estructura de la base de datos
            if not verificar_tablas():
                print("La estructura de la base de datos es incorrecta. Recreándola...")
                # Eliminar la base de datos existente
                if os.path.exists(DB_PATH):
                    os.remove(DB_PATH)
                # Crear nueva base de datos
                if not crear_base_datos():
                    raise Exception("No se pudo recrear la base de datos")
                print("Base de datos recreada correctamente")

            return True

        except Exception as e:
            print(f"Error al inicializar la base de datos: {e}")
            messagebox.showerror("Error",
                f"Error al inicializar la base de datos: {str(e)}")
            return False

    def verify_database_connection(self):
        """Verifica la conexión a la base de datos"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            conn.close()
            return True
        except Exception as e:
            print(f"Error al verificar conexión a la base de datos: {e}")
            return False

    def on_closing(self):
        """Maneja el cierre de la ventana principal"""
        if messagebox.askokcancel("Salir", "¿Desea salir del sistema?"):
            self.root.quit()
            self.root.destroy()

    def clear_content_frame(self):
        """Limpia el contenido del frame principal de forma segura"""
        try:
            # Limpiar referencia a pantalla actual
            if hasattr(self, 'pantalla_actual') and self.pantalla_actual:
                # Llamar método destroy si existe
                if hasattr(self.pantalla_actual, 'destroy'):
                    try:
                        self.pantalla_actual.destroy()
                    except:
                        pass
                self.pantalla_actual = None
            
            # Verificar que el frame principal existe
            if hasattr(self, 'main_content_frame') and self.main_content_frame.winfo_exists():
                # Destruir todos los widgets hijos
                for widget in self.main_content_frame.winfo_children():
                    try:
                        widget.destroy()
                    except:
                        pass
                
                # Forzar actualización
                self.main_content_frame.update_idletasks()
            
        except Exception as e:
            print(f"Error limpiando frame: {e}")

    def show_welcome_screen(self):
        """Muestra la pantalla de bienvenida"""
        # Limpiar el contenido actual y restaurar tamaño
        self.clear_content_frame()
        self.reset_window_size()

        # Contenido de bienvenida
        welcome_frame = ttk.Frame(self.main_content_frame, style='Card.TFrame')
        welcome_frame.place(relx=0.5, rely=0.5, anchor='center')

        ttk.Label(welcome_frame,
                text="Bienvenido al Sistema de Gestión",
                font=('Helvetica', 24, 'bold'),
                background='white',
                anchor='center').pack(pady=10)

        ttk.Label(welcome_frame,
                text="DIRECCIÓN DEPARTAMENTAL DE REDES INTEGRADAS\n" +
                      "DE SERVICIOS DE SALUD DE GUATEMALA\n" +
                      "ÁREA NOR ORIENTE",
                font=('Helvetica', 14),
                justify='center',
                background='white',
                anchor='center').pack(pady=20)

        info_frame = ttk.Frame(welcome_frame, style='Card.TFrame')
        info_frame.pack(pady=30)

        info_text = """
        Este sistema permite:
        • Gestionar el ingreso y control de insumos
        • Administrar servicios y tipos de servicio
        • Registrar movimientos de insumos
        • Generar reportes y tarjetas Kardex
        • Mantener un registro detallado de movimientos

        Seleccione una opción del menú para comenzar.
        """

        ttk.Label(info_frame,
                text=info_text,
                font=('Helvetica', 12),
                justify='left',
                background='white',
                anchor='w').pack(padx=10)

    # Métodos para cargar módulos (modificados para usar el tamaño estándar)
    def load_ingreso_insumos(self):
        if not self.verify_database_connection():
            messagebox.showerror("Error", "No se puede conectar a la base de datos")
            return
        self.clear_content_frame()
        self.reset_window_size()  # Restaurar tamaño estándar
        self.pantalla_actual = IngresoInsumos(self.main_content_frame, self)

    def load_gestion_insumos(self):
        if not self.verify_database_connection():
            messagebox.showerror("Error", "No se puede conectar a la base de datos")
            return
        self.clear_content_frame()
        self.reset_window_size()
        self.pantalla_actual = GestionInsumos(self.main_content_frame, self)

    def load_gestion_servicios(self):
        if not self.verify_database_connection():
            messagebox.showerror("Error", "No se puede conectar a la base de datos")
            return
        self.clear_content_frame()
        self.reset_window_size()
        self.pantalla_actual = GestionServicios(self.main_content_frame, self)

    def load_gestion_movimientos(self):
        if not self.verify_database_connection():
            messagebox.showerror("Error", "No se puede conectar a la base de datos")
            return
        self.clear_content_frame()
        self.reset_window_size()
        self.pantalla_actual = GestionMovimientos(self.main_content_frame, self)

    def load_reporte_kardex(self):
        """Carga la pantalla de reporte Kardex"""
        try:
            if not self.verify_database_connection():
                messagebox.showerror("Error", "No se puede conectar a la base de datos")
                return
                
            # Limpiar pantalla actual
            self.clear_content_frame()
            
            # Verificar que el frame principal existe
            if not hasattr(self, 'main_content_frame') or not self.main_content_frame.winfo_exists():
                messagebox.showerror("Error", "Frame principal no disponible")
                return
                
            # Restaurar tamaño de ventana
            self.reset_window_size()
            
            # Crear nueva pantalla
            self.pantalla_actual = ReporteKardex(self.main_content_frame, self)
            
        except Exception as e:
            print(f"Error cargando reporte Kardex: {e}")
            messagebox.showerror("Error", f"Error al cargar reporte Kardex: {str(e)}")

    def load_gestion_usuarios(self):
        if not self.verify_database_connection():
            messagebox.showerror("Error", "No se puede conectar a la base de datos")
            return
        self.clear_content_frame()
        self.reset_window_size()
        from src.gui.gestion_usuarios import GestionUsuarios
        self.pantalla_actual = GestionUsuarios(self.main_content_frame, self)

    def load_correccion_movimientos(self):
        if not self.verify_database_connection():
            messagebox.showerror("Error", "No se puede conectar a la base de datos")
            return
        self.clear_content_frame()
        self.reset_window_size()
        from src.gui.correccion_movimientos import CorreccionMovimientos
        self.pantalla_actual =CorreccionMovimientos(self.main_content_frame, self)
        
    def load_reporte_demanda_real(self):
        if not self.verify_database_connection():
            messagebox.showerror("Error", "No se puede conectar a la base de datos")
            return
        self.clear_content_frame()
        self.reset_window_size()
        self.pantalla_actual = ReporteDemandaReal(self.main_content_frame, self)
        
    def load_reporte_bres(self):
        if not self.verify_database_connection():
            messagebox.showerror("Error", "No se puede conectar a la base de datos")
            return
        self.clear_content_frame()
        self.reset_window_size()
        self.pantalla_actual = ReporteBres(self.main_content_frame, self)
        
    def load_importar_exportar(self):
        """Carga la interfaz de gestión de importación/exportación integrada"""
        if not self.verify_database_connection():
            messagebox.showerror("Error", "No se puede conectar a la base de datos")
            return
        
        self.clear_content_frame()
        self.reset_window_size()
        
        # Obtener la ruta de la base de datos desde el módulo database
        try:
            from src.database import DB_PATH
            db_path = DB_PATH
        except:
            db_path = 'database.db'  # Fallback
        
        # Crear la instancia del gestor integrado
        self.pantalla_actual = ImportarExportarManager(self.main_content_frame, self)
        # Pasar la ruta de la base de datos
        self.pantalla_actual.db_path = db_path

    def create_menu(self):
        # Frame para el menú lateral
        self.menu_frame = ttk.Frame(self.root)
        self.menu_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Estilo para los botones del menú
        style = ttk.Style()
        style.configure('White.TFrame',
                   background='white',
                   relief='flat',
                   borderwidth=0)

        style.configure('Menu.TButton',
                    font=('Helvetica', 11),
                    padding=(10, 5),
                    width=20,
                    relief='flat',
                    borderwidth=0,
                    background='white')  # Color de fondo normal

        # Mapeo de estados para el hover
        style.map('Menu.TButton',
                background=[('active', '#e1e1e1'), ('!active', 'white')],
                relief=[('pressed', 'flat'), ('!pressed', 'flat')],
                borderwidth=[('pressed', '0'), ('!pressed', '0')])

        # Estilo para el título (sin fondo ni borde)
        style.configure('Title.TLabel',
                    font=('Helvetica', 12, 'bold'),
                    background='white',  # O el color de fondo de tu menú
                    borderwidth=0,
                    relief='flat')

        # Frame simple para el título, sin borde y con ancho reducido
        title_frame = tk.Frame(self.menu_frame, bd=0, highlightthickness=0)
        title_frame.pack(pady=20)

        tk.Label(
            title_frame,
            text="SISTEMA DE GESTIÓN",
            font=('Helvetica', 12, 'bold'),
            bd=0,
            relief='flat',
            width=18,  # Ajusta este valor según lo que desees
            anchor="center",
            justify="center"
        ).pack(padx=5)

        tk.Label(
            title_frame,
            text="DE INSUMOS",
            font=('Helvetica', 12, 'bold'),
            bd=0,
            relief='flat',
            width=18,  # Igual que arriba
            anchor="center",
            justify="center"
        ).pack(padx=5)

        # Botones según rol
        rol = self.usuario['rol']
        if rol in ("admin", "super_admin"):
            self.create_menu_button("Gestión de Usuarios", self.load_gestion_usuarios, 'usuarios')
            self.create_menu_button("Gestión de Insumos", self.load_gestion_insumos, 'insumos')
            self.create_menu_button("Gestión de Servicios", self.load_gestion_servicios, 'servicios')
            self.create_menu_button("Gestión de Movimientos", self.load_gestion_movimientos, 'movimientos')
            self.create_menu_button("Import/Export Datos", self.load_importar_exportar, 'import_export')
        if rol in ("usuario", "admin", "super_admin"):
            self.create_menu_button("Ingreso de Insumos", self.load_ingreso_insumos, 'ingreso')
            self.create_menu_button("Reporte Kardex", self.load_reporte_kardex, 'kardex')
            self.create_menu_button("Reporte Demanda Real", self.load_reporte_demanda_real, 'demanda')
            self.create_menu_button("Correcciones", self.load_correccion_movimientos, 'correcciones')
            self.create_menu_button("Reporte BRES", self.load_reporte_bres, 'bres')

        # Botón de salir
        btn_salir = ttk.Button(self.menu_frame,
            text="Salir",
            style='Menu.TButton',
            image=self.icons.get('salir'),
            compound='left',
            command=self.on_closing)
        btn_salir.pack(pady=10, padx=10, side='bottom')

    def create_menu_button(self, text, command, icon_key=None):
        btn_frame = ttk.Frame(self.menu_frame)
        btn_frame.pack(fill='x', pady=2)

        # Obtener icono si existe
        icon = self.icons.get(icon_key) if icon_key else None

        btn = ttk.Button(btn_frame,
                        text=text,
                        style='Menu.TButton',
                        command=command,
                        image=icon,
                        compound='left')  # Icono a la izquierda del texto
        btn.pack(padx=5)

        # Efectos hover
        def on_enter(e):
            btn.state(['active'])
        def on_leave(e):
            btn.state(['!active'])

        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)

    def run(self):
        # Configurar estilos adicionales
        style = ttk.Style()

        # Estilo para frames tipo tarjeta
        style.configure('Card.TFrame',
                    background='white',
                    relief='flat',
                    borderwidth=0)

        # Estilo para etiquetas
        style.configure('TLabel',
                    font=('Helvetica', 10))

        # Estilo para la barra de estado
        style.configure('Status.TFrame',
                    background='#f0f0f0',
                    relief='sunken',
                    borderwidth=1)

        style.configure('Status.TLabel',
                    font=('Helvetica', 9),
                    background='#f0f0f0')

        self.root.mainloop()