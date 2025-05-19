import tkinter as tk
from tkinter import ttk, messagebox
from ttkthemes import ThemedStyle
import sys
import os
from PIL import Image, ImageTk

# Agregar el directorio raíz del proyecto al PATH de Python
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from src.database.db_manager import verificar_credenciales
from src.gui.main_window import MainWindow

from src.database.db_manager import verificar_credenciales, crear_tabla_usuarios  # Añade crear_tabla_usuarios

class LoginWindow:
    def __init__(self):
        
        crear_tabla_usuarios()
        
        self.root = tk.Tk()
        self.root.title("Inicio de Sesión")
        self.root.geometry("500x600")
        self.root.configure(bg='#f0f0f0')  # Color de fondo suave

        # Hacer que la ventana no sea redimensionable
        self.root.resizable(False, False)

        # Centrar la ventana
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 500) // 2
        y = (screen_height - 600) // 2
        self.root.geometry(f"500x600+{x}+{y}")

        # Aplicar tema
        style = ThemedStyle(self.root)
        style.set_theme("arc")

        # Configurar estilos personalizados
        style.configure('Custom.TFrame', background='#ffffff')
        style.configure('Title.TLabel',
                       font=('Helvetica', 16, 'bold'),
                       background='#ffffff',
                       foreground='#2c3e50')
        style.configure('Subtitle.TLabel',
                       font=('Helvetica', 12),
                       background='#ffffff',
                       foreground='#34495e')
        style.configure('Custom.TButton',
                       font=('Helvetica', 11),
                       padding=10)

        self.setup_ui()

    def setup_ui(self):
        # Frame principal con fondo blanco y sombra
        main_frame = ttk.Frame(self.root, style='Custom.TFrame', padding="30")
        main_frame.place(relx=0.5, rely=0.5, anchor="center", width=400, height=500)

        # Configurar el grid para el frame principal
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)  # Para "ÁREA NOR ORIENTE"
        main_frame.grid_rowconfigure(3, weight=2)
        main_frame.grid_columnconfigure(0, weight=1)

        # Logo o Imagen
        try:
            logo_path = os.path.join(project_root, "assets", "logo.png")
            logo_image = Image.open(logo_path)
            logo_image = logo_image.resize((150, 150))
            logo_photo = ImageTk.PhotoImage(logo_image)
            logo_label = ttk.Label(main_frame, image=logo_photo, background='#ffffff')
            logo_label.image = logo_photo
            logo_label.grid(row=0, column=0, pady=(0, 10))
        except:
            title_label = ttk.Label(
                main_frame,
                text="BIENVENIDO",
                style='Title.TLabel'
            )
            title_label.grid(row=0, column=0, pady=(0, 10))

        # Título del sistema (dividido en dos líneas)
        system_title_frame = ttk.Frame(main_frame, style='Custom.TFrame')
        system_title_frame.grid(row=1, column=0, pady=(0, 5))

        system_title_line1 = ttk.Label(
            system_title_frame,
            text="SISTEMA DE GESTIÓN",
            style='Title.TLabel'
        )
        system_title_line1.pack()

        system_title_line2 = ttk.Label(
            system_title_frame,
            text="DE INSUMOS",
            style='Title.TLabel'
        )
        system_title_line2.pack()

        # "ÁREA NOR ORIENTE" arriba del formulario
        area_label = ttk.Label(
            main_frame,
            text="ÁREA NOR ORIENTE",
            font=('Helvetica', 14, 'bold'),
            background='#ffffff',
            foreground='#2c3e50'
        )
        area_label.grid(row=2, column=0, pady=20)

        # Frame para el formulario
        form_frame = ttk.Frame(main_frame, style='Custom.TFrame')
        form_frame.grid(row=3, column=0, sticky="nsew", pady=10)

        # Usuario
        username_frame = ttk.Frame(form_frame, style='Custom.TFrame')
        username_frame.pack(fill="x", pady=5)

        ttk.Label(username_frame,
                 text="Usuario:",
                 font=('Helvetica', 10),
                 background='#ffffff').pack(anchor="w")

        self.username_entry = ttk.Entry(username_frame,
                                      font=('Helvetica', 11),
                                      width=30)
        self.username_entry.pack(fill="x", pady=(5, 0))

        # Contraseña
        password_frame = ttk.Frame(form_frame, style='Custom.TFrame')
        password_frame.pack(fill="x", pady=15)

        ttk.Label(password_frame,
                 text="Contraseña:",
                 font=('Helvetica', 10),
                 background='#ffffff').pack(anchor="w")

        self.password_entry = ttk.Entry(password_frame,
                                      show="•",
                                      font=('Helvetica', 11),
                                      width=30)
        self.password_entry.pack(fill="x", pady=(5, 0))

        # Botón de inicio de sesión
        login_button = ttk.Button(
            form_frame,
            text="INICIAR SESIÓN",
            style='Custom.TButton',
            command=self.login
        )
        login_button.pack(fill="x", pady=(30, 0))

        # Vincular Enter a login
        self.root.bind('<Return>', lambda e: self.login())

        # Dar foco al campo de usuario
        self.username_entry.focus()

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Por favor ingrese usuario y contraseña")
            return

        usuario = verificar_credenciales(username, password)
        if usuario:
            self.root.destroy()
            app = MainWindow(usuario)
            app.run()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    login = LoginWindow()
    login.run()