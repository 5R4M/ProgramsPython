import tkinter as tk
from tkinter import ttk, messagebox
from ttkthemes import ThemedStyle
import sys
import os
from PIL import Image, ImageTk
import pymysql
import configparser
import socket
import threading

# Agregar el directorio raíz del proyecto al PATH de Python
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from src.database.db_manager import verificar_credenciales
from src.gui.main_window import MainWindow
from src.database.db_manager import verificar_credenciales, crear_tabla_usuarios

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        # En desarrollo, base_path es la raíz del proyecto (subir un nivel desde gui)
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(base_path, relative_path)

class ConfiguracionMySQL:
    def __init__(self, parent):
        self.parent = parent
        self.config_file = "mysql_config.ini"
        self.result = None
        
        # Crear ventana de configuración
        self.config_window = tk.Toplevel(parent)
        self.config_window.title("Configuración de Conexión MySQL")
        self.config_window.geometry("500x400")
        self.config_window.configure(bg='#f8f9fa')
        self.config_window.resizable(False, False)
        self.config_window.transient(parent)
        self.config_window.grab_set()
        
        # Centrar la ventana
        self.center_window()
        
        self.setup_ui()
        self.cargar_configuracion()

    def center_window(self):
        """Centra la ventana en la pantalla"""
        screen_width = self.config_window.winfo_screenwidth()
        screen_height = self.config_window.winfo_screenheight()
        x = (screen_width - 500) // 2
        y = (screen_height - 400) // 2
        self.config_window.geometry(f"500x400+{x}+{y}")

    def setup_ui(self):
        # Frame principal
        main_frame = tk.Frame(self.config_window, bg='#f8f9fa')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Título
        title_label = tk.Label(
            main_frame,
            text="Configuración de MySQL",
            font=('Segoe UI', 16, 'bold'),
            bg='#f8f9fa',
            fg='#2c3e50'
        )
        title_label.pack(pady=(0, 10))

        # Subtítulo
        subtitle_label = tk.Label(
            main_frame,
            text="Configure la conexión al servidor MySQL",
            font=('Segoe UI', 10),
            bg='#f8f9fa',
            fg='#7f8c8d'
        )
        subtitle_label.pack(pady=(0, 20))

        # Frame de configuración
        config_frame = tk.LabelFrame(
            main_frame,
            text="Datos de Conexión",
            font=('Segoe UI', 10, 'bold'),
            bg='#ffffff',
            fg='#2c3e50',
            padx=15,
            pady=15
        )
        config_frame.pack(fill='x', pady=(0, 20))

        # Host/IP
        tk.Label(config_frame, text="Host/IP del servidor:", font=('Segoe UI', 10), 
                bg='#ffffff', fg='#2c3e50').grid(row=0, column=0, sticky="w", pady=5)
        self.host_var = tk.StringVar(value="localhost")
        self.host_entry = tk.Entry(config_frame, textvariable=self.host_var, width=25,
                                  font=('Segoe UI', 10))
        self.host_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=(10, 0))

        # Puerto
        tk.Label(config_frame, text="Puerto:", font=('Segoe UI', 10), 
                bg='#ffffff', fg='#2c3e50').grid(row=1, column=0, sticky="w", pady=5)
        self.puerto_var = tk.StringVar(value="3306")
        self.puerto_entry = tk.Entry(config_frame, textvariable=self.puerto_var, width=25,
                                    font=('Segoe UI', 10))
        self.puerto_entry.grid(row=1, column=1, sticky="ew", pady=5, padx=(10, 0))

        # Usuario admin
        tk.Label(config_frame, text="Usuario Admin:", font=('Segoe UI', 10), 
                bg='#ffffff', fg='#2c3e50').grid(row=2, column=0, sticky="w", pady=5)
        self.admin_user_var = tk.StringVar(value="root")
        self.admin_user_entry = tk.Entry(config_frame, textvariable=self.admin_user_var, width=25,
                                        font=('Segoe UI', 10))
        self.admin_user_entry.grid(row=2, column=1, sticky="ew", pady=5, padx=(10, 0))

        # Contraseña admin
        tk.Label(config_frame, text="Contraseña Admin:", font=('Segoe UI', 10), 
                bg='#ffffff', fg='#2c3e50').grid(row=3, column=0, sticky="w", pady=5)
        self.admin_pass_var = tk.StringVar()
        self.admin_pass_entry = tk.Entry(config_frame, textvariable=self.admin_pass_var, 
                                        show="*", width=25, font=('Segoe UI', 10))
        self.admin_pass_entry.grid(row=3, column=1, sticky="ew", pady=5, padx=(10, 0))

        # Configurar grid
        config_frame.grid_columnconfigure(1, weight=1)

        # Estado de conexión
        self.status_frame = tk.Frame(main_frame, bg='#f8f9fa')
        self.status_frame.pack(fill='x', pady=(0, 10))

        self.status_label = tk.Label(
            self.status_frame,
            text="Estado: No conectado",
            font=('Segoe UI', 10, 'bold'),
            bg='#f8f9fa',
            fg='#e74c3c'
        )
        self.status_label.pack()

        # Frame de botones
        btn_frame = tk.Frame(main_frame, bg='#f8f9fa')
        btn_frame.pack(fill='x')

        # Botón probar conexión
        self.test_btn = tk.Button(
            btn_frame,
            text="Probar Conexión",
            font=('Segoe UI', 10, 'bold'),
            bg='#f39c12',
            fg='white',
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2',
            command=self.probar_conexion_threaded
        )
        self.test_btn.pack(side='left', padx=(0, 10))

        # Botón guardar y continuar
        self.save_btn = tk.Button(
            btn_frame,
            text="Guardar y Continuar",
            font=('Segoe UI', 10, 'bold'),
            bg='#27ae60',
            fg='white',
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2',
            command=self.guardar_y_continuar,
            state='disabled'
        )
        self.save_btn.pack(side='left', padx=(0, 10))

        # Botón cancelar
        cancel_btn = tk.Button(
            btn_frame,
            text="Cancelar",
            font=('Segoe UI', 10, 'bold'),
            bg='#e74c3c',
            fg='white',
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2',
            command=self.cancelar
        )
        cancel_btn.pack(side='right')

        # Efectos hover para botones
        self.add_button_hover_effects()

        # Focus inicial
        self.host_entry.focus()

    def add_button_hover_effects(self):
        """Añade efectos hover a los botones"""
        def create_hover_effect(button, normal_color, hover_color):
            def on_enter(e):
                if button['state'] != 'disabled':
                    button.configure(bg=hover_color)
            def on_leave(e):
                if button['state'] != 'disabled':
                    button.configure(bg=normal_color)
            button.bind('<Enter>', on_enter)
            button.bind('<Leave>', on_leave)

        create_hover_effect(self.test_btn, '#f39c12', '#e67e22')
        create_hover_effect(self.save_btn, '#27ae60', '#2ecc71')

    def probar_conexion_threaded(self):
        """Ejecuta la prueba de conexión en un hilo separado"""
        self.test_btn.config(state='disabled')
        self.status_label.config(text="Probando conexión...", fg='#f39c12')
        
        def test_connection():
            try:
                host = self.host_var.get().strip()
                port = int(self.puerto_var.get().strip())
                user = self.admin_user_var.get().strip()
                password = self.admin_pass_var.get()

                if not host or not user:
                    raise Exception("Host y usuario son obligatorios")

                connection = pymysql.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    connect_timeout=10
                )
                
                with connection.cursor() as cursor:
                    cursor.execute("SELECT VERSION()")
                    version = cursor.fetchone()[0]
                
                connection.close()
                
                # Actualizar UI en el hilo principal
                self.config_window.after(0, lambda: self.connection_success(version))
                
            except Exception as e:
                # Actualizar UI en el hilo principal
                self.config_window.after(0, lambda: self.connection_error(str(e)))

        threading.Thread(target=test_connection, daemon=True).start()

    def connection_success(self, version):
        """Maneja la conexión exitosa"""
        self.status_label.config(
            text=f"✅ Conexión exitosa - MySQL {version}", 
            fg='#27ae60'
        )
        self.save_btn.config(state='normal')
        self.test_btn.config(state='normal')

    def connection_error(self, error_msg):
        """Maneja el error de conexión"""
        self.status_label.config(
            text=f"❌ Error: {error_msg}", 
            fg='#e74c3c'
        )
        self.save_btn.config(state='disabled')
        self.test_btn.config(state='normal')

    def guardar_y_continuar(self):
        """Guarda la configuración y continúa"""
        self.guardar_configuracion()
        self.result = {
            'host': self.host_var.get().strip(),
            'port': int(self.puerto_var.get().strip()),
            'user': self.admin_user_var.get().strip(),
            'password': self.admin_pass_var.get()
        }
        self.config_window.destroy()

    def cancelar(self):
        """Cancela la configuración"""
        self.result = None
        self.config_window.destroy()

    def guardar_configuracion(self):
        """Guarda la configuración en archivo"""
        config = configparser.ConfigParser()
        config['MySQL'] = {
            'host': self.host_var.get().strip(),
            'port': self.puerto_var.get().strip(),
            'admin_user': self.admin_user_var.get().strip()
            # No guardamos la contraseña por seguridad
        }
        
        try:
            with open(self.config_file, 'w') as f:
                config.write(f)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la configuración: {str(e)}")

    def cargar_configuracion(self):
        """Carga la configuración desde archivo si existe"""
        if os.path.exists(self.config_file):
            try:
                config = configparser.ConfigParser()
                config.read(self.config_file)
                
                if 'MySQL' in config:
                    mysql_config = config['MySQL']
                    self.host_var.set(mysql_config.get('host', 'localhost'))
                    self.puerto_var.set(mysql_config.get('port', '3306'))
                    self.admin_user_var.set(mysql_config.get('admin_user', 'root'))
                    
            except Exception as e:
                pass  # Si no se puede cargar, usar valores por defecto

class LoginWindow:
    def __init__(self):
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
        
        # Verificar conexión MySQL antes de mostrar login
        self.verificar_mysql_y_continuar()

    def verificar_mysql_y_continuar(self):
        """Verifica la conexión MySQL y decide qué mostrar"""
        def verificar_conexion():
            try:
                # Intentar crear las tablas - esto verificará la conexión
                crear_tabla_usuarios()
                
                # Si llegamos aquí, la conexión funciona
                self.root.after(0, self.mostrar_login)
                
            except Exception as e:
                # Error de conexión - mostrar configuración
                self.root.after(0, lambda: self.mostrar_configuracion_mysql(str(e)))

        # Mostrar mensaje de carga
        self.mostrar_mensaje_carga()
        
        # Ejecutar verificación en hilo separado
        threading.Thread(target=verificar_conexion, daemon=True).start()

    def mostrar_mensaje_carga(self):
        """Muestra un mensaje de carga mientras verifica la conexión"""
        # Limpiar la ventana
        for widget in self.root.winfo_children():
            widget.destroy()

        # Frame de carga
        loading_frame = tk.Frame(self.root, bg='#f8f9fa')
        loading_frame.pack(fill='both', expand=True)

        # Contenedor centrado
        center_frame = tk.Frame(loading_frame, bg='#f8f9fa')
        center_frame.place(relx=0.5, rely=0.5, anchor='center')

        # Icono de carga
        if hasattr(self, 'icons') and 'medical_120' in self.icons:
            icon_label = tk.Label(center_frame, image=self.icons['medical_120'], bg='#f8f9fa')
            icon_label.pack(pady=(0, 20))

        # Mensaje
        tk.Label(
            center_frame,
            text="Verificando conexión MySQL...",
            font=('Segoe UI', 14, 'bold'),
            bg='#f8f9fa',
            fg='#2c3e50'
        ).pack()

        # Actualizar la ventana
        self.root.update()

    def mostrar_configuracion_mysql(self, error_msg):
        """Muestra la ventana de configuración MySQL"""
        # Limpiar la ventana
        for widget in self.root.winfo_children():
            widget.destroy()

        # Mensaje de error
        error_frame = tk.Frame(self.root, bg='#f8f9fa')
        error_frame.pack(fill='x', padx=20, pady=10)

        tk.Label(
            error_frame,
            text="⚠️ No se pudo conectar a MySQL",
            font=('Segoe UI', 12, 'bold'),
            bg='#f8f9fa',
            fg='#e74c3c'
        ).pack()

        tk.Label(
            error_frame,
            text=f"Error: {error_msg}",
            font=('Segoe UI', 9),
            bg='#f8f9fa',
            fg='#7f8c8d',
            wraplength=600
        ).pack(pady=(5, 0))

        # Mostrar configuración
        config_mysql = ConfiguracionMySQL(self.root)
        
        # Esperar resultado
        self.root.wait_window(config_mysql.config_window)
        
        if config_mysql.result:
            # Reintentar conexión con nueva configuración
            self.verificar_mysql_y_continuar()
        else:
            # Usuario canceló - cerrar aplicación
            self.root.quit()

    def mostrar_login(self):
        """Muestra la pantalla de login"""
        # Limpiar la ventana
        for widget in self.root.winfo_children():
            widget.destroy()

        # Configurar el login normal
        self.setup_ui()

    def load_icons(self):
        """Carga los iconos para la ventana de login"""
        self.icons = {}
        icon_path = resource_path(os.path.join('utils', 'icons'))
        
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
                    # Diferentes tamaños
                    self.icons[f'{key}_20'] = ImageTk.PhotoImage(image.resize((20, 20), Image.Resampling.LANCZOS))
                    self.icons[f'{key}_24'] = ImageTk.PhotoImage(image.resize((24, 24), Image.Resampling.LANCZOS))
                    self.icons[f'{key}_18'] = ImageTk.PhotoImage(image.resize((18, 18), Image.Resampling.LANCZOS))
                    self.icons[f'{key}_120'] = ImageTk.PhotoImage(image.resize((120, 120), Image.Resampling.LANCZOS))
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

        # Icono principal
        if hasattr(self, 'icons') and 'medical_120' in self.icons:
            icon_label = tk.Label(left_content, image=self.icons['medical_120'], bg='#2c3e50')
            icon_label.pack(pady=(0, 15))

        # Título principal
        title_label = tk.Label(
            left_content,
            text="SISTEMA DE GESTIÓN\nDE INSUMOS",
            font=('Segoe UI', 18, 'bold'),
            bg='#2c3e50',
            fg='#ffffff',
            justify='center'
        )
        title_label.pack(pady=(0, 8))

        # Subtítulo
        subtitle_label = tk.Label(
            left_content,
            text="ÁREA NOR ORIENTE",
            font=('Segoe UI', 12),
            bg='#2c3e50',
            fg='#bdc3c7'
        )
        subtitle_label.pack(pady=(0, 20))

        # Información adicional
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

        try:
            usuario = verificar_credenciales(username, password)
            if usuario:
                self.root.destroy()
                app = MainWindow(usuario)
                app.run()
            else:
                messagebox.showerror("Error", "Usuario o contraseña incorrectos")
                self.password_entry.delete(0, tk.END)
                self.password_entry.focus()
        except Exception as e:
            messagebox.showerror("Error de Conexión", 
                               f"Error al verificar credenciales:\n{str(e)}\n\nVerifique la configuración de MySQL")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    login = LoginWindow()
    login.run()