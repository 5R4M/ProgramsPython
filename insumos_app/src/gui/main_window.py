import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sys
import os
from PIL import Image, ImageTk
from ttkthemes import ThemedStyle

# Agregar el directorio raíz del proyecto al PATH de Python
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from insumos import IngresoInsumos
from gestion import GestionInsumos
from servicios import GestionServicios
from reportes import Reportes

class MainWindow:
    def __init__(self):
        
        self.root = tk.Tk()
        self.root.title("Sistema de Gestión de Insumos")
        self.root.geometry("1200x800")

        # Aplicar tema moderno
        style = ThemedStyle(self.root)
        style.set_theme("arc")  # Otros temas disponibles: 'equilux', 'breeze', etc.

        self.setup_window()
        self.create_menu()
        
        # Crear el frame principal que contendrá el contenido
        self.main_content_frame = ttk.Frame(self.root, style='Card.TFrame')
        self.main_content_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # Mostrar la pantalla de bienvenida inicial
        self.show_welcome_screen()

        
        # Manejar el cierre de la ventana principal
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
      
    def on_closing(self):
        """Maneja el cierre de la ventana principal"""
        if messagebox.askokcancel("Salir", "¿Desea salir del sistema?"):
            self.root.quit()
            self.root.destroy()   

    def setup_window(self):
        # Centrar la ventana
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 1200) // 2
        y = (screen_height - 800) // 2
        self.root.geometry(f"1200x800+{x}+{y}")

        # Configurar el grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
    
    def show_welcome_screen(self):
        # Limpiar el contenido actual
        for widget in self.main_content_frame.winfo_children():
            widget.destroy()

        # Contenido de bienvenida
        welcome_frame = ttk.Frame(self.main_content_frame)
        welcome_frame.place(relx=0.5, rely=0.5, anchor='center')

        ttk.Label(welcome_frame,
                 text="Bienvenido al Sistema de Gestión",
                 font=('Helvetica', 24, 'bold')).pack(pady=10)

        ttk.Label(welcome_frame,
                 text="DIRECCIÓN DEPARTAMENTAL DE REDES INTEGRADAS\n" +
                      "DE SERVICIOS DE SALUD DE GUATEMALA\n" +
                      "ÁREA NOR ORIENTE",
                 font=('Helvetica', 14),
                 justify='center').pack(pady=20)

        info_frame = ttk.Frame(welcome_frame)
        info_frame.pack(pady=30)

        info_text = """
        Este sistema permite:
        • Gestionar el ingreso y control de insumos
        • Administrar servicios y tipos de servicio
        • Generar reportes y tarjetas Kardex
        • Mantener un registro detallado de movimientos

        Seleccione una opción del menú para comenzar.
        """

        ttk.Label(info_frame,
                 text=info_text,
                 font=('Helvetica', 12),
                 justify='left').pack()

    def load_ingreso_insumos(self):
        # Limpiar el contenido actual
        for widget in self.main_content_frame.winfo_children():
            widget.destroy()
        IngresoInsumos(self.main_content_frame, self)

    def load_gestion_insumos(self):
        # Limpiar el contenido actual
        for widget in self.main_content_frame.winfo_children():
            widget.destroy()
        GestionInsumos(self.main_content_frame, self)

    def load_gestion_servicios(self):
        # Limpiar el contenido actual
        for widget in self.main_content_frame.winfo_children():
            widget.destroy()
        # Cargar el contenido de gestión de servicios
        GestionServicios(self.main_content_frame, self)

    def load_reportes(self):
        # Limpiar el contenido actual
        for widget in self.main_content_frame.winfo_children():
            widget.destroy()
        Reportes(self.main_content_frame, self)

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
        title_frame = tk.Frame(self.menu_frame, bg='white', bd=0, highlightthickness=0)
        title_frame.pack(pady=20)

        tk.Label(
            title_frame,
            text="SISTEMA DE GESTIÓN",
            font=('Helvetica', 12, 'bold'),
            bg='white',
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
            bg='white',
            bd=0,
            relief='flat',
            width=18,  # Igual que arriba
            anchor="center",
            justify="center"
        ).pack(padx=5)


        # Botones del menú
        self.create_menu_button("Ingreso de Insumos",
                              self.load_ingreso_insumos)
        self.create_menu_button("Gestión de Insumos",
                              self.load_gestion_insumos)
        self.create_menu_button("Gestión de Servicios",
                              self.load_gestion_servicios)
        self.create_menu_button("Reportes",
                              self.load_reportes)


        # Botón de salir en la parte inferior
        ttk.Button(self.menu_frame,
                  text="Salir",
                  style='Menu.TButton',
                  command=self.root.quit).pack(pady=10, padx=10, side='bottom')

    def create_menu_button(self, text, command):
        btn_frame = ttk.Frame(self.menu_frame)
        btn_frame.pack(fill='x', pady=2)

        btn = ttk.Button(btn_frame,
                        text=text,
                        style='Menu.TButton',
                        command=command)
        btn.pack(padx=5)

        # Efectos hover usando el estado active
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

        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = MainWindow()
        app.run()
    except KeyboardInterrupt:
        print("\nPrograma terminado por el usuario")
    except Exception as e:
        print(f"Error inesperado: {e}")
    finally:
        try:
            app.root.destroy()
        except:
            pass