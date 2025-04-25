import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sys
import os
from PIL import Image, ImageTk
from ttkthemes import ThemedStyle

# Agregar el directorio raíz del proyecto al PATH de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from insumos import abrir_ingreso_insumos
from gestion import abrir_gestion_insumos
from servicios import abrir_gestion_servicios
from reportes import abrir_reportes

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
        self.create_main_content()
        
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

    def create_menu(self):
        # Frame para el menú lateral
        self.menu_frame = ttk.Frame(self.root, style='Card.TFrame')
        self.menu_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Estilo para los botones del menú
        style = ttk.Style()
        style.configure('Menu.TButton',
                    font=('Helvetica', 11),
                    padding=10,
                    width=20)

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

        # Separador
        ttk.Separator(self.menu_frame).pack(fill='x', padx=10, pady=10)

        # Botones del menú
        self.create_menu_button("Ingreso de Insumos",
                              lambda: abrir_ingreso_insumos(self.root))
        self.create_menu_button("Gestión de Insumos",
                              lambda: abrir_gestion_insumos(self.root))
        self.create_menu_button("Gestión de Servicios",
                              lambda: abrir_gestion_servicios(self.root))
        self.create_menu_button("Reportes",
                              lambda: abrir_reportes(self.root))

        # Separador
        ttk.Separator(self.menu_frame).pack(fill='x', padx=10, pady=10)

        # Botón de salir en la parte inferior
        ttk.Button(self.menu_frame,
                  text="Salir",
                  style='Menu.TButton',
                  command=self.root.quit).pack(pady=10, padx=10, side='bottom')

    def create_menu_button(self, text, command):
        btn_frame = ttk.Frame(self.menu_frame)
        btn_frame.pack(fill='x', pady=5)

        btn = ttk.Button(btn_frame,
                        text=text,
                        style='Menu.TButton',
                        command=command)
        btn.pack(padx=10, fill='x')

        # Efectos hover
        def on_enter(e):
            btn.state(['pressed'])
        def on_leave(e):
            btn.state(['!pressed'])

        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)

    def create_main_content(self):
        # Frame principal para el contenido
        main_frame = ttk.Frame(self.root, style='Card.TFrame')
        main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # Contenido de bienvenida
        welcome_frame = ttk.Frame(main_frame)
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

        # Información del sistema
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

    def run(self):
        # Configurar estilos adicionales
        style = ttk.Style()

        # Estilo para frames tipo tarjeta
        style.configure('Card.TFrame',
                       background='white',
                       relief='solid',
                       borderwidth=1)

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