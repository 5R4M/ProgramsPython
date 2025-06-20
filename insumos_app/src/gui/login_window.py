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
from src.database.db_manager import verificar_credenciales, crear_tabla_usuarios

class LoginWindow:
    def __init__(self):
        crear_tabla_usuarios()
        
        self.root = tk.Tk()
        self.root.title("Sistema de Gestión de Insumos")
        self.root.geometry("800x450")
        self.root.configure(bg='#f8f9fa')
        self.root.resizable(False, False)

        # Centrar la ventana
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 800) // 2
        y = (screen_height - 450) // 2
        self.root.geometry(f"800x450+{x}+{y}")

        # Cargar iconos
        self.load_icons()
        
        # Variable para mostrar/ocultar contraseña
        self.show_password = False
        
        self.setup_ui()

    def load_icons(self):
        """Carga los iconos para la ventana de login"""
        self.icons = {}
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'icons')
        
        if not os.path.exists(icon_path):
            os.makedirs(icon_path)
        
        icon_files = {
            'user': 'user.png',
            'password': 'lock.png',
            'login': 'log-in.png',
            'eye': 'eye.png',
            'eye_off': 'eye-off.png',
            'medical': 'medical-box.png'
        }
        
        for key, filename in icon_files.items():
            try:
                icon_full_path = os.path.join(icon_path, filename)
                if os.path.exists(icon_full_path):
                    image = Image.open(icon_full_path)
                    # Diferentes tamaños - AQUÍ AUMENTAS LOS TAMAÑOS
                    self.icons[f'{key}_20'] = ImageTk.PhotoImage(image.resize((20, 20), Image.Resampling.LANCZOS))  # Iconos pequeños (ojo)
                    self.icons[f'{key}_24'] = ImageTk.PhotoImage(image.resize((24, 24), Image.Resampling.LANCZOS))  # Iconos campos de entrada
                    self.icons[f'{key}_18'] = ImageTk.PhotoImage(image.resize((18, 18), Image.Resampling.LANCZOS))  # Icono botón login
                    self.icons[f'{key}_120'] = ImageTk.PhotoImage(image.resize((120, 120), Image.Resampling.LANCZOS))  # Icono principal
                else:
                    print(f"Icono no encontrado: {filename}")
            except Exception as e:
                print(f"Error cargando icono {filename}: {e}")

    def setup_ui(self):
        # Frame principal que contiene todo
        main_container = tk.Frame(self.root, bg='#f8f9fa')
        main_container.pack(fill='both', expand=True)

        # Panel izquierdo (información)
        left_panel = tk.Frame(main_container, bg='#2c3e50', width=400)
        left_panel.pack(side='left', fill='y')
        left_panel.pack_propagate(False)

        # Contenido del panel izquierdo
        left_content = tk.Frame(left_panel, bg='#2c3e50')
        left_content.place(relx=0.5, rely=0.5, anchor='center')

        # Icono principal más grande
        if hasattr(self, 'icons') and 'medical_80' in self.icons:
            icon_label = tk.Label(left_content, image=self.icons['medical_80'], bg='#2c3e50')
            icon_label.pack(pady=(0, 15))

        # Título principal más pequeño
        title_label = tk.Label(
            left_content,
            text="SISTEMA DE GESTIÓN\nDE INSUMOS",
            font=('Segoe UI', 18, 'bold'),
            bg='#2c3e50',
            fg='#ffffff',
            justify='center'
        )
        title_label.pack(pady=(0, 8))

        # Subtítulo más pequeño
        subtitle_label = tk.Label(
            left_content,
            text="ÁREA NOR ORIENTE",
            font=('Segoe UI', 12),
            bg='#2c3e50',
            fg='#bdc3c7'
        )
        subtitle_label.pack(pady=(0, 20))

        # Información adicional más pequeña
        info_text = """• Control de inventario
                    • Gestión de movimientos
                    • Reportes detallados
                    • Sistema seguro"""

        info_label = tk.Label(
            left_content,
            text=info_text,
            font=('Segoe UI', 9),
            bg='#2c3e50',
            fg='#95a5a6',
            justify='left'
        )
        info_label.pack()

        # Panel derecho (formulario)
        right_panel = tk.Frame(main_container, bg='#ffffff', width=350)
        right_panel.pack(side='right', fill='both', expand=True)
        right_panel.pack_propagate(False)

        # Contenedor del formulario
        form_container = tk.Frame(right_panel, bg='#ffffff')
        form_container.place(relx=0.5, rely=0.5, anchor='center')

        # Título del formulario
        form_title = tk.Label(
            form_container,
            text="Iniciar Sesión",
            font=('Segoe UI', 20, 'bold'),
            bg='#ffffff',
            fg='#2c3e50'
        )
        form_title.pack(pady=(0, 30))

        # Campo Usuario
        self.create_input_field(form_container, "Usuario", "user", False)
        
        # Campo Contraseña
        self.create_input_field(form_container, "Contraseña", "password", True)

        # Botón de login con icono
        login_btn_frame = tk.Frame(form_container, bg='#ffffff')
        login_btn_frame.pack(pady=(25, 15), fill='x')

        # Crear botón con icono
        if hasattr(self, 'icons') and 'login_20' in self.icons:
            login_btn = tk.Button(
                login_btn_frame,
                text="  INICIAR SESIÓN",
                font=('Segoe UI', 11, 'bold'),
                bg='#3498db',
                fg='white',
                relief='flat',
                padx=30,
                pady=10,
                cursor='hand2',
                image=self.icons['login_20'],
                compound='left',
                command=self.login
            )
        else:
            login_btn = tk.Button(
                login_btn_frame,
                text="INICIAR SESIÓN",
                font=('Segoe UI', 11, 'bold'),
                bg='#3498db',
                fg='white',
                relief='flat',
                padx=30,
                pady=10,
                cursor='hand2',
                command=self.login
            )
        
        login_btn.pack(fill='x')

        # Efectos hover para el botón
        def on_enter(e):
            login_btn.configure(bg='#2980b9')
        def on_leave(e):
            login_btn.configure(bg='#3498db')
        
        login_btn.bind('<Enter>', on_enter)
        login_btn.bind('<Leave>', on_leave)

        # Información de ayuda
        help_label = tk.Label(
            form_container,
            text="¿Problemas para acceder? Contacte al administrador",
            font=('Segoe UI', 8),
            bg='#ffffff',
            fg='#7f8c8d'
        )
        help_label.pack(pady=(15, 0))

        # Vincular Enter a login
        self.root.bind('<Return>', lambda e: self.login())

        # Dar foco al primer campo
        if hasattr(self, 'username_entry'):
            self.username_entry.focus()

    def create_input_field(self, parent, label_text, icon_key, is_password):
        """Crear un campo de entrada con icono y estilo moderno"""
        # Frame contenedor
        field_frame = tk.Frame(parent, bg='#ffffff')
        field_frame.pack(fill='x', pady=(0, 15))

        # Label
        label = tk.Label(
            field_frame,
            text=label_text,
            font=('Segoe UI', 10, 'bold'),
            bg='#ffffff',
            fg='#34495e'
        )
        label.pack(anchor='w', pady=(0, 6))

        # Frame para el input con borde
        input_frame = tk.Frame(field_frame, bg='#ecf0f1', relief='solid', bd=1)
        input_frame.pack(fill='x')

        # Icono
        if hasattr(self, 'icons') and f'{icon_key}_24' in self.icons:
            icon_label = tk.Label(
                input_frame,
                image=self.icons[f'{icon_key}_24'],
                bg='#ecf0f1'
            )
            icon_label.pack(side='left', padx=(10, 6), pady=10)

        # Entry
        if is_password:
            self.password_entry = tk.Entry(
                input_frame,
                font=('Segoe UI', 10),
                bg='#ecf0f1',
                fg='#2c3e50',
                relief='flat',
                bd=0,
                show='•'
            )
            self.password_entry.pack(side='left', fill='x', expand=True, pady=10)
            
            # Botón para mostrar/ocultar contraseña
            if hasattr(self, 'icons') and 'eye_24' in self.icons:
                self.toggle_btn = tk.Button(
                    input_frame,
                    image=self.icons['eye_24'],
                    bg='#ecf0f1',
                    relief='flat',
                    bd=0,
                    cursor='hand2',
                    command=self.toggle_password_visibility
                )
                self.toggle_btn.pack(side='right', padx=(6, 10), pady=10)
        else:
            self.username_entry = tk.Entry(
                input_frame,
                font=('Segoe UI', 10),
                bg='#ecf0f1',
                fg='#2c3e50',
                relief='flat',
                bd=0
            )
            self.username_entry.pack(side='left', fill='x', expand=True, pady=10, padx=(0, 10))

    def toggle_password_visibility(self):
        """Alterna la visibilidad de la contraseña"""
        self.show_password = not self.show_password
        
        if self.show_password:
            self.password_entry.configure(show="")
            if hasattr(self, 'icons') and 'eye_off_24' in self.icons:
                self.toggle_btn.configure(image=self.icons['eye_off_24'])
        else:
            self.password_entry.configure(show="•")
            if hasattr(self, 'icons') and 'eye_24' in self.icons:
                self.toggle_btn.configure(image=self.icons['eye_24'])

    def login(self):
        username = self.username_entry.get().strip().lower()
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