import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import subprocess
import configparser
import socket
import pymysql
import threading

def resource_path(relative_path):
    """Obtiene la ruta absoluta al recurso, funciona en dev y en PyInstaller."""
    try:
        base_path = sys._MEIPASS  # PyInstaller crea esta carpeta temporal
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class ConfigurarServidor:
    def __init__(self, parent_frame, main_window=None):
        self.parent = parent_frame
        self.main_window = main_window
        self.config_file = "mysql_config.ini"
        self.setup_ui()
        self.cargar_configuracion()

    def setup_ui(self):
        for widget in self.parent.winfo_children():
            widget.destroy()
            
        # Agregar título principal
        title_frame = ttk.Frame(self.parent)
        title_frame.pack(fill='x', padx=10, pady=(10, 5))

        ttk.Label(title_frame, text="Configuración de MySQL para Acceso en Red",
                font=('Segoe UI', 16, 'bold')).pack(anchor='w')

        ttk.Label(title_frame, text="Configure el servidor MySQL para permitir conexiones remotas",
                font=('Segoe UI', 10)).pack(anchor='w', pady=(2, 0))

        # Separador
        ttk.Separator(self.parent, orient='horizontal').pack(fill='x', padx=10, pady=5)

        # Notebook para organizar las pestañas
        self.notebook = ttk.Notebook(self.parent)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Pestaña de Configuración General
        self.setup_config_tab()
        
        # Pestaña de Usuarios Remotos
        self.setup_users_tab()
        
        # Pestaña de Estado y Pruebas
        self.setup_status_tab()

    def setup_config_tab(self):
        """Configuración general del servidor MySQL"""
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="Configuración Servidor")

        # Configuración básica
        basic_frame = ttk.LabelFrame(config_frame, text="Configuración Básica")
        basic_frame.pack(fill="x", padx=10, pady=10)

        # Host/IP
        ttk.Label(basic_frame, text="Host/IP del servidor:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.host_var = tk.StringVar(value="localhost")
        self.host_entry = ttk.Entry(basic_frame, textvariable=self.host_var, width=20)
        self.host_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        # Puerto
        ttk.Label(basic_frame, text="Puerto:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.puerto_var = tk.StringVar(value="3306")
        self.puerto_entry = ttk.Entry(basic_frame, textvariable=self.puerto_var, width=10)
        self.puerto_entry.grid(row=0, column=3, sticky="w", padx=5, pady=5)

        # Usuario admin
        ttk.Label(basic_frame, text="Usuario Admin:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.admin_user_var = tk.StringVar(value="root")
        self.admin_user_entry = ttk.Entry(basic_frame, textvariable=self.admin_user_var, width=20)
        self.admin_user_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        # Contraseña admin
        ttk.Label(basic_frame, text="Contraseña Admin:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.admin_pass_var = tk.StringVar()
        self.admin_pass_entry = ttk.Entry(basic_frame, textvariable=self.admin_pass_var, show="*", width=20)
        self.admin_pass_entry.grid(row=1, column=3, sticky="w", padx=5, pady=5)

        # Configuración de red
        network_frame = ttk.LabelFrame(config_frame, text="Configuración de Red")
        network_frame.pack(fill="x", padx=10, pady=10)

        # Bind address
        ttk.Label(network_frame, text="Bind Address:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.bind_address_var = tk.StringVar(value="0.0.0.0")
        self.bind_address_combo = ttk.Combobox(network_frame, textvariable=self.bind_address_var, 
                                             values=["0.0.0.0", "127.0.0.1", self.obtener_ip_local()], width=15)
        self.bind_address_combo.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(network_frame, text="(0.0.0.0 = todas las interfaces)").grid(row=0, column=2, sticky="w", padx=5, pady=5)

        # Máximo de conexiones
        ttk.Label(network_frame, text="Máx. Conexiones:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.max_connections_var = tk.StringVar(value="100")
        self.max_connections_entry = ttk.Entry(network_frame, textvariable=self.max_connections_var, width=10)
        self.max_connections_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        # Timeout de conexión
        ttk.Label(network_frame, text="Timeout (seg):").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.timeout_var = tk.StringVar(value="28800")
        self.timeout_entry = ttk.Entry(network_frame, textvariable=self.timeout_var, width=10)
        self.timeout_entry.grid(row=1, column=3, sticky="w", padx=5, pady=5)

        # Botones de configuración
        btn_config_frame = ttk.Frame(config_frame)
        btn_config_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(btn_config_frame, text="Probar Conexión", command=self.probar_conexion).pack(side="left", padx=5)
        ttk.Button(btn_config_frame, text="Aplicar Configuración", command=self.aplicar_configuracion).pack(side="left", padx=5)
        ttk.Button(btn_config_frame, text="Reiniciar MySQL", command=self.reiniciar_mysql).pack(side="left", padx=5)
        ttk.Button(btn_config_frame, text="Guardar Config", command=self.guardar_configuracion).pack(side="left", padx=5)

    def setup_users_tab(self):
        """Gestión de usuarios remotos"""
        users_frame = ttk.Frame(self.notebook)
        self.notebook.add(users_frame, text="Usuarios Remotos")

        # Lista de usuarios remotos
        list_frame = ttk.LabelFrame(users_frame, text="Usuarios con Acceso Remoto")
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Tabla de usuarios
        columns = ("usuario", "host", "privilegios", "activo")
        self.users_tree_frame = ttk.Frame(list_frame)
        self.users_tree_frame.pack(fill="both", expand=True, pady=10)

        self.users_tree_scroll_y = ttk.Scrollbar(self.users_tree_frame, orient="vertical")
        self.users_tree_scroll_x = ttk.Scrollbar(self.users_tree_frame, orient="horizontal")

        self.users_tree = ttk.Treeview(
            self.users_tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=self.users_tree_scroll_y.set,
            xscrollcommand=self.users_tree_scroll_x.set
        )

        self.users_tree_scroll_y.config(command=self.users_tree.yview)
        self.users_tree_scroll_x.config(command=self.users_tree.xview)

        self.users_tree_scroll_y.pack(side="right", fill="y")
        self.users_tree_scroll_x.pack(side="bottom", fill="x")

        # Configurar columnas
        for col in columns:
            self.users_tree.heading(col, text=col.replace("_", " ").title(), anchor="center")
            self.users_tree.column(col, width=120, anchor="center")
        
        self.users_tree.pack(fill="both", expand=True)

        # Botones para usuarios
        btn_users_frame = ttk.Frame(users_frame)
        btn_users_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(btn_users_frame, text="Crear Usuario Remoto", command=self.crear_usuario_remoto).pack(side="left", padx=5)
        ttk.Button(btn_users_frame, text="Modificar Privilegios", command=self.modificar_privilegios).pack(side="left", padx=5)
        ttk.Button(btn_users_frame, text="Eliminar Usuario", command=self.eliminar_usuario_remoto).pack(side="left", padx=5)
        ttk.Button(btn_users_frame, text="Actualizar Lista", command=self.cargar_usuarios_remotos).pack(side="left", padx=5)

    def setup_status_tab(self):
        """Estado del servidor y pruebas"""
        status_frame = ttk.Frame(self.notebook)
        self.notebook.add(status_frame, text="Estado y Pruebas")

        # Estado del servicio
        service_frame = ttk.LabelFrame(status_frame, text="Estado del Servicio MySQL")
        service_frame.pack(fill="x", padx=10, pady=10)

        self.status_label = ttk.Label(service_frame, text="Verificando estado...", font=('Segoe UI', 10, 'bold'))
        self.status_label.pack(pady=10)

        # Información de conexiones
        conn_frame = ttk.LabelFrame(status_frame, text="Información de Conexiones")
        conn_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Text widget para mostrar información
        self.info_text = tk.Text(conn_frame, height=15, width=80)
        info_scroll = ttk.Scrollbar(conn_frame, orient="vertical", command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=info_scroll.set)
        
        self.info_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        info_scroll.pack(side="right", fill="y")

        # Botones de estado
        btn_status_frame = ttk.Frame(status_frame)
        btn_status_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(btn_status_frame, text="Verificar Estado", command=self.verificar_estado).pack(side="left", padx=5)
        ttk.Button(btn_status_frame, text="Ver Conexiones Activas", command=self.ver_conexiones_activas).pack(side="left", padx=5)
        ttk.Button(btn_status_frame, text="Probar desde IP Externa", command=self.probar_ip_externa).pack(side="left", padx=5)
        ttk.Button(btn_status_frame, text="Ver Log de Errores", command=self.ver_log_errores).pack(side="left", padx=5)

        # Botón volver
        ttk.Button(btn_status_frame, text="Volver", command=self.volver).pack(side="right", padx=5)

    def obtener_ip_local(self):
        """Obtiene la IP local de la máquina"""
        try:
            hostname = socket.gethostname()
            ip_local = socket.gethostbyname(hostname)
            return ip_local
        except:
            return "192.168.1.100"

    def probar_conexion(self):
        """Prueba la conexión al servidor MySQL"""
        def test_connection():
            try:
                host = self.host_var.get()
                port = int(self.puerto_var.get())
                user = self.admin_user_var.get()
                password = self.admin_pass_var.get()

                self.info_text.insert(tk.END, f"Probando conexión a {host}:{port} como {user}...\n")
                
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
                
                self.info_text.insert(tk.END, f"✅ Conexión exitosa! Versión MySQL: {version}\n")
                messagebox.showinfo("Éxito", f"Conexión exitosa!\nVersión MySQL: {version}")
                
            except Exception as e:
                error_msg = f"❌ Error de conexión: {str(e)}\n"
                self.info_text.insert(tk.END, error_msg)
                messagebox.showerror("Error de Conexión", str(e))

        # Ejecutar en hilo separado para no bloquear la UI
        threading.Thread(target=test_connection, daemon=True).start()

    def aplicar_configuracion(self):
        """Aplica la configuración de red al servidor MySQL"""
        try:
            host = self.host_var.get()
            port = int(self.puerto_var.get())
            user = self.admin_user_var.get()
            password = self.admin_pass_var.get()
            bind_address = self.bind_address_var.get()
            max_connections = self.max_connections_var.get()
            timeout = self.timeout_var.get()

            connection = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password
            )

            with connection.cursor() as cursor:
                # Configurar variables de sistema
                queries = [
                    f"SET GLOBAL max_connections = {max_connections}",
                    f"SET GLOBAL wait_timeout = {timeout}",
                    f"SET GLOBAL interactive_timeout = {timeout}"
                ]
                
                for query in queries:
                    cursor.execute(query)
                    self.info_text.insert(tk.END, f"Ejecutado: {query}\n")

            connection.close()
            
            # Mensaje sobre my.cnf
            msg = f"""Configuración aplicada parcialmente.

Para aplicar completamente la configuración de red, debe:

1. Editar el archivo my.cnf (o my.ini en Windows)
2. Agregar/modificar estas líneas en [mysqld]:
   bind-address = {bind_address}
   port = {port}
   max_connections = {max_connections}

3. Reiniciar el servicio MySQL

¿Desea que intente localizar y editar el archivo de configuración automáticamente?"""
            
            if messagebox.askyesno("Configuración", msg):
                self.editar_archivo_configuracion(bind_address, port, max_connections)
            
            messagebox.showinfo("Éxito", "Variables de configuración aplicadas")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo aplicar la configuración: {str(e)}")

    def editar_archivo_configuracion(self, bind_address, port, max_connections):
        """Intenta editar el archivo de configuración MySQL"""
        # Posibles ubicaciones del archivo de configuración
        possible_paths = [
            "/etc/mysql/my.cnf",
            "/etc/my.cnf",
            "/usr/local/etc/my.cnf",
            "C:\\ProgramData\\MySQL\\MySQL Server 8.0\\my.ini",
            "C:\\Program Files\\MySQL\\MySQL Server 8.0\\my.ini",
            "C:\\xampp\\mysql\\bin\\my.ini"
        ]
        
        config_file = None
        for path in possible_paths:
            if os.path.exists(path):
                config_file = path
                break
        
        if not config_file:
            # Permitir selección manual
            config_file = filedialog.askopenfilename(
                title="Seleccionar archivo de configuración MySQL",
                filetypes=[("Archivos de configuración", "*.cnf *.ini"), ("Todos", "*.*")]
            )
        
        if config_file and os.path.exists(config_file):
            try:
                # Hacer backup
                backup_file = config_file + ".backup"
                with open(config_file, 'r') as f:
                    with open(backup_file, 'w') as b:
                        b.write(f.read())
                
                # Leer configuración actual
                config = configparser.ConfigParser(allow_no_value=True)
                config.read(config_file)
                
                # Asegurar que existe la sección [mysqld]
                if 'mysqld' not in config:
                    config.add_section('mysqld')
                
                # Actualizar configuración
                config['mysqld']['bind-address'] = bind_address
                config['mysqld']['port'] = str(port)
                config['mysqld']['max_connections'] = str(max_connections)
                
                # Escribir configuración actualizada
                with open(config_file, 'w') as f:
                    config.write(f)
                
                self.info_text.insert(tk.END, f"Archivo de configuración actualizado: {config_file}\n")
                self.info_text.insert(tk.END, f"Backup creado: {backup_file}\n")
                messagebox.showinfo("Éxito", f"Archivo de configuración actualizado:\n{config_file}\n\nBackup: {backup_file}\n\nReinicie MySQL para aplicar cambios.")
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo editar el archivo de configuración: {str(e)}")
        else:
            messagebox.showwarning("Advertencia", "No se encontró el archivo de configuración MySQL")

    def reiniciar_mysql(self):
        """Reinicia el servicio MySQL"""
        def restart_service():
            try:
                self.info_text.insert(tk.END, "Intentando reiniciar el servicio MySQL...\n")
                
                # Comandos según el sistema operativo
                import platform
                system = platform.system()
                
                if system == "Linux":
                    # Intentar diferentes comandos para Linux
                    commands = [
                        ["sudo", "systemctl", "restart", "mysql"],
                        ["sudo", "service", "mysql", "restart"],
                        ["sudo", "/etc/init.d/mysql", "restart"]
                    ]
                elif system == "Windows":
                    commands = [
                        ["net", "stop", "MySQL80"],
                        ["net", "start", "MySQL80"]
                    ]
                else:  # macOS
                    commands = [
                        ["brew", "services", "restart", "mysql"]
                    ]
                
                success = False
                for cmd in commands:
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                        if result.returncode == 0:
                            success = True
                            self.info_text.insert(tk.END, f"✅ Comando exitoso: {' '.join(cmd)}\n")
                            break
                        else:
                            self.info_text.insert(tk.END, f"❌ Falló: {' '.join(cmd)} - {result.stderr}\n")
                    except subprocess.TimeoutExpired:
                        self.info_text.insert(tk.END, f"⏱️ Timeout: {' '.join(cmd)}\n")
                    except Exception as e:
                        self.info_text.insert(tk.END, f"❌ Error: {' '.join(cmd)} - {str(e)}\n")
                
                if success:
                    messagebox.showinfo("Éxito", "Servicio MySQL reiniciado correctamente")
                else:
                    messagebox.showwarning("Advertencia", "No se pudo reiniciar automáticamente.\nReinicie manualmente el servicio MySQL.")
                    
            except Exception as e:
                error_msg = f"Error al reiniciar MySQL: {str(e)}"
                self.info_text.insert(tk.END, f"❌ {error_msg}\n")
                messagebox.showerror("Error", error_msg)

        threading.Thread(target=restart_service, daemon=True).start()

    def crear_usuario_remoto(self):
        """Crear un nuevo usuario con acceso remoto"""
        dialog = UsuarioRemotoDialog(self.parent, "Crear Usuario Remoto")
        if dialog.result:
            username, password, host, privilegios = dialog.result
            
            try:
                connection = pymysql.connect(
                    host=self.host_var.get(),
                    port=int(self.puerto_var.get()),
                    user=self.admin_user_var.get(),
                    password=self.admin_pass_var.get()
                )
                
                with connection.cursor() as cursor:
                    # Crear usuario
                    cursor.execute(f"CREATE USER '{username}'@'{host}' IDENTIFIED BY '{password}'")
                    
                    # Otorgar privilegios
                    if privilegios == "ALL":
                        cursor.execute(f"GRANT ALL PRIVILEGES ON *.* TO '{username}'@'{host}' WITH GRANT OPTION")
                    else:
                        cursor.execute(f"GRANT {privilegios} ON *.* TO '{username}'@'{host}'")
                    
                    cursor.execute("FLUSH PRIVILEGES")
                
                connection.close()
                
                messagebox.showinfo("Éxito", f"Usuario '{username}@{host}' creado correctamente")
                self.cargar_usuarios_remotos()
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear el usuario: {str(e)}")

    def cargar_usuarios_remotos(self):
        """Carga la lista de usuarios con acceso remoto"""
        try:
            # Limpiar tabla actual
            for row in self.users_tree.get_children():
                self.users_tree.delete(row)
            
            connection = pymysql.connect(
                host=self.host_var.get(),
                port=int(self.puerto_var.get()),
                user=self.admin_user_var.get(),
                password=self.admin_pass_var.get(),
                database="mysql"
            )
            
            with connection.cursor() as cursor:
                # Obtener usuarios remotos (no localhost)
                cursor.execute("""
                    SELECT User, Host, 
                           IF(Select_priv='Y' AND Insert_priv='Y' AND Update_priv='Y' AND Delete_priv='Y', 'FULL', 'LIMITED') as Privilegios,
                           IF(account_locked='N', 'Sí', 'No') as Activo
                    FROM user 
                    WHERE Host != 'localhost' AND Host != '127.0.0.1'
                    ORDER BY User, Host
                """)
                
                usuarios = cursor.fetchall()
                
                for usuario in usuarios:
                    self.users_tree.insert("", "end", values=usuario)
            
            connection.close()
            self.info_text.insert(tk.END, f"Lista de usuarios actualizada: {len(usuarios)} usuarios remotos\n")
            
        except Exception as e:
            error_msg = f"Error al cargar usuarios: {str(e)}"
            self.info_text.insert(tk.END, f"❌ {error_msg}\n")

    def verificar_estado(self):
        """Verifica el estado del servidor MySQL"""
        def check_status():
            try:
                # Limpiar área de información
                self.info_text.delete(1.0, tk.END)
                
                # Probar conexión
                connection = pymysql.connect(
                    host=self.host_var.get(),
                    port=int(self.puerto_var.get()),
                    user=self.admin_user_var.get(),
                    password=self.admin_pass_var.get()
                )
                
                with connection.cursor() as cursor:
                    # Información básica
                    cursor.execute("SELECT VERSION()")
                    version = cursor.fetchone()[0]
                    self.info_text.insert(tk.END, f"🔄 Estado del Servidor MySQL\n")
                    self.info_text.insert(tk.END, f"✅ Servidor ACTIVO\n")
                    self.info_text.insert(tk.END, f"📊 Versión: {version}\n\n")
                    
                    # Variables importantes
                    variables = [
                        'max_connections', 'port', 'bind_address', 
                        'wait_timeout', 'interactive_timeout'
                    ]
                    
                    self.info_text.insert(tk.END, "🔧 Configuración Actual:\n")
                    for var in variables:
                        cursor.execute(f"SHOW VARIABLES LIKE '{var}'")
                        result = cursor.fetchone()
                        if result:
                            self.info_text.insert(tk.END, f"  • {var}: {result[1]}\n")
                    
                    # Estadísticas de conexiones
                    self.info_text.insert(tk.END, "\n📈 Estadísticas de Conexión:\n")
                    status_vars = ['Threads_connected', 'Connections', 'Max_used_connections']
                    for var in status_vars:
                        cursor.execute(f"SHOW STATUS LIKE '{var}'")
                        result = cursor.fetchone()
                        if result:
                            self.info_text.insert(tk.END, f"  • {var}: {result[1]}\n")
                
                connection.close()
                self.status_label.config(text="✅ MySQL Server ACTIVO", foreground="green")
                
            except Exception as e:
                self.info_text.insert(tk.END, f"❌ Error: {str(e)}\n")
                self.status_label.config(text="❌ MySQL Server NO DISPONIBLE", foreground="red")

        threading.Thread(target=check_status, daemon=True).start()

    def ver_conexiones_activas(self):
        """Muestra las conexiones activas al servidor"""
        try:
            connection = pymysql.connect(
                host=self.host_var.get(),
                port=int(self.puerto_var.get()),
                user=self.admin_user_var.get(),
                password=self.admin_pass_var.get()
            )
            
            with connection.cursor() as cursor:
                cursor.execute("SHOW PROCESSLIST")
                procesos = cursor.fetchall()
                
                self.info_text.insert(tk.END, f"\n🔗 Conexiones Activas ({len(procesos)}):\n")
                self.info_text.insert(tk.END, "-" * 80 + "\n")
                self.info_text.insert(tk.END, f"{'ID':<8}{'Usuario':<15}{'Host':<25}{'DB':<15}{'Estado':<15}\n")
                self.info_text.insert(tk.END, "-" * 80 + "\n")
                
                for proceso in procesos:
                    id_proc = proceso[0] or 0
                    user = proceso[1] or "N/A"
                    host = proceso[2] or "N/A"
                    db = proceso[3] or "N/A"
                    state = proceso[4] or "N/A"
                    
                    self.info_text.insert(tk.END, f"{id_proc:<8}{user:<15}{host:<25}{db:<15}{state:<15}\n")
            
            connection.close()
            
        except Exception as e:
            self.info_text.insert(tk.END, f"❌ Error al obtener conexiones: {str(e)}\n")

    def probar_ip_externa(self):
        """Permite probar conexión desde una IP externa específica"""
        ip_externa = simpledialog.askstring("Prueba IP Externa", 
                                           "Ingrese la IP desde la cual probar la conexión:")
        if ip_externa:
            usuario_prueba = simpledialog.askstring("Usuario de Prueba", 
                                                   "Usuario para la prueba:")
            if usuario_prueba:
                password_prueba = simpledialog.askstring("Contraseña", 
                                                        "Contraseña:", show="*")
                if password_prueba:
                    self.info_text.insert(tk.END, f"\n🌐 Simulando conexión desde {ip_externa}...\n")
                    self.info_text.insert(tk.END, f"Usuario: {usuario_prueba}\n")
                    self.info_text.insert(tk.END, f"⚠️  Nota: Esta es una simulación local.\n")
                    self.info_text.insert(tk.END, f"Para una prueba real, ejecute desde {ip_externa}:\n")
                    self.info_text.insert(tk.END, f"mysql -h {self.host_var.get()} -P {self.puerto_var.get()} -u {usuario_prueba} -p\n\n")

    def ver_log_errores(self):
        """Muestra el log de errores de MySQL"""
        def show_log():
            try:
                connection = pymysql.connect(
                    host=self.host_var.get(),
                    port=int(self.puerto_var.get()),
                    user=self.admin_user_var.get(),
                    password=self.admin_pass_var.get()
                )
                
                with connection.cursor() as cursor:
                    # Obtener la ubicación del log de errores
                    cursor.execute("SHOW VARIABLES LIKE 'log_error'")
                    result = cursor.fetchone()
                    
                    if result and result[1]:
                        log_path = result[1]
                        self.info_text.insert(tk.END, f"\n📋 Log de Errores: {log_path}\n")
                        self.info_text.insert(tk.END, "-" * 80 + "\n")
                        
                        try:
                            # Intentar leer las últimas líneas del log
                            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                                lines = f.readlines()
                                # Mostrar las últimas 20 líneas
                                for line in lines[-20:]:
                                    self.info_text.insert(tk.END, line)
                        except Exception as e:
                            self.info_text.insert(tk.END, f"No se puede leer el archivo: {str(e)}\n")
                            self.info_text.insert(tk.END, f"Archivo ubicado en: {log_path}\n")
                    else:
                        self.info_text.insert(tk.END, "\n📋 Log de errores no configurado o no disponible\n")
                
                connection.close()
                
            except Exception as e:
                self.info_text.insert(tk.END, f"❌ Error al acceder al log: {str(e)}\n")

        threading.Thread(target=show_log, daemon=True).start()

    def modificar_privilegios(self):
        """Modifica los privilegios de un usuario remoto"""
        selected = self.users_tree.selection()
        if not selected:
            messagebox.showwarning("Seleccione", "Seleccione un usuario para modificar")
            return
        
        item = self.users_tree.item(selected[0])["values"]
        usuario, host = item[0], item[1]
        
        dialog = PrivilegiosDialog(self.parent, f"Privilegios para {usuario}@{host}")
        if dialog.result:
            nuevos_privilegios = dialog.result
            
            try:
                connection = pymysql.connect(
                    host=self.host_var.get(),
                    port=int(self.puerto_var.get()),
                    user=self.admin_user_var.get(),
                    password=self.admin_pass_var.get()
                )
                
                with connection.cursor() as cursor:
                    # Revocar privilegios existentes
                    cursor.execute(f"REVOKE ALL PRIVILEGES ON *.* FROM '{usuario}'@'{host}'")
                    
                    # Otorgar nuevos privilegios
                    if nuevos_privilegios == "ALL":
                        cursor.execute(f"GRANT ALL PRIVILEGES ON *.* TO '{usuario}'@'{host}' WITH GRANT OPTION")
                    else:
                        cursor.execute(f"GRANT {nuevos_privilegios} ON *.* TO '{usuario}'@'{host}'")
                    
                    cursor.execute("FLUSH PRIVILEGES")
                
                connection.close()
                
                messagebox.showinfo("Éxito", f"Privilegios actualizados para {usuario}@{host}")
                self.cargar_usuarios_remotos()
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudieron modificar los privilegios: {str(e)}")

    def eliminar_usuario_remoto(self):
        """Elimina un usuario remoto"""
        selected = self.users_tree.selection()
        if not selected:
            messagebox.showwarning("Seleccione", "Seleccione un usuario para eliminar")
            return
        
        item = self.users_tree.item(selected[0])["values"]
        usuario, host = item[0], item[1]
        
        if messagebox.askyesno("Confirmar", f"¿Eliminar el usuario '{usuario}@{host}'?"):
            try:
                connection = pymysql.connect(
                    host=self.host_var.get(),
                    port=int(self.puerto_var.get()),
                    user=self.admin_user_var.get(),
                    password=self.admin_pass_var.get()
                )
                
                with connection.cursor() as cursor:
                    cursor.execute(f"DROP USER '{usuario}'@'{host}'")
                    cursor.execute("FLUSH PRIVILEGES")
                
                connection.close()
                
                messagebox.showinfo("Éxito", f"Usuario {usuario}@{host} eliminado correctamente")
                self.cargar_usuarios_remotos()
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el usuario: {str(e)}")

    def guardar_configuracion(self):
        """Guarda la configuración actual en un archivo"""
        config = configparser.ConfigParser()
        config['MySQL'] = {
            'host': self.host_var.get(),
            'port': self.puerto_var.get(),
            'admin_user': self.admin_user_var.get(),
            'bind_address': self.bind_address_var.get(),
            'max_connections': self.max_connections_var.get(),
            'timeout': self.timeout_var.get()
        }
        
        try:
            with open(self.config_file, 'w') as f:
                config.write(f)
            messagebox.showinfo("Éxito", f"Configuración guardada en {self.config_file}")
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
                    self.bind_address_var.set(mysql_config.get('bind_address', '0.0.0.0'))
                    self.max_connections_var.set(mysql_config.get('max_connections', '100'))
                    self.timeout_var.set(mysql_config.get('timeout', '28800'))
                    
            except Exception as e:
                pass  # Si no se puede cargar, usar valores por defecto

    def volver(self):
        """Vuelve a la pantalla principal"""
        if self.main_window:
            self.main_window.show_welcome_screen()

class UsuarioRemotoDialog(tk.Toplevel):
    def __init__(self, parent, title):
        super().__init__(parent)
        self.title(title)
        self.result = None
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
        self.center_window()

    def setup_ui(self):
        # Configurar el padding
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill="both", expand=True)

        # Usuario
        ttk.Label(main_frame, text="Nombre de usuario:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(main_frame, textvariable=self.username_var, width=30)
        self.username_entry.grid(row=0, column=1, sticky="ew", pady=(0, 5), padx=(5, 0))

        # Contraseña
        ttk.Label(main_frame, text="Contraseña:").grid(row=1, column=0, sticky="w", pady=(0, 5))
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(main_frame, textvariable=self.password_var, show="*", width=30)
        self.password_entry.grid(row=1, column=1, sticky="ew", pady=(0, 5), padx=(5, 0))

        # Host/IP
        ttk.Label(main_frame, text="Host permitido:").grid(row=2, column=0, sticky="w", pady=(0, 5))
        self.host_var = tk.StringVar(value="%")
        self.host_combo = ttk.Combobox(main_frame, textvariable=self.host_var, 
                                      values=["%", "192.168.1.%", "10.0.0.%", "172.16.0.%"], width=28)
        self.host_combo.grid(row=2, column=1, sticky="ew", pady=(0, 5), padx=(5, 0))

        # Nota sobre hosts
        ttk.Label(main_frame, text="(% = cualquier IP, 192.168.1.% = subnet específica)", 
                 font=('Segoe UI', 8)).grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 10))

        # Privilegios
        ttk.Label(main_frame, text="Privilegios:").grid(row=4, column=0, sticky="w", pady=(0, 5))
        self.privilegios_var = tk.StringVar(value="SELECT,INSERT,UPDATE,DELETE")
        self.privilegios_combo = ttk.Combobox(main_frame, textvariable=self.privilegios_var, 
                                             values=[
                                                 "SELECT,INSERT,UPDATE,DELETE",
                                                 "SELECT",
                                                 "ALL",
                                                 "SELECT,INSERT,UPDATE,DELETE,CREATE,DROP,ALTER"
                                             ], width=28)
        self.privilegios_combo.grid(row=4, column=1, sticky="ew", pady=(0, 5), padx=(5, 0))

        # Configurar el grid
        main_frame.grid_columnconfigure(1, weight=1)

        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=(20, 0))

        ttk.Button(btn_frame, text="Aceptar", command=self.aceptar).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Cancelar", command=self.cancelar).pack(side="left")

        # Focus inicial
        self.username_entry.focus()

    def center_window(self):
        """Centra la ventana en la pantalla"""
        self.update_idletasks()
        width = 400
        height = 250
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def aceptar(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()
        host = self.host_var.get().strip()
        privilegios = self.privilegios_var.get()

        if not username or not password or not host:
            messagebox.showerror("Error", "Todos los campos son obligatorios")
            return

        self.result = (username, password, host, privilegios)
        self.destroy()

    def cancelar(self):
        self.result = None
        self.destroy()

class PrivilegiosDialog(tk.Toplevel):
    def __init__(self, parent, title):
        super().__init__(parent)
        self.title(title)
        self.result = None
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
        self.center_window()

    def setup_ui(self):
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="Seleccione los privilegios a otorgar:", 
                 font=('Segoe UI', 10, 'bold')).pack(anchor="w", pady=(0, 10))

        # Variables para checkboxes
        self.privs = {
            'SELECT': tk.BooleanVar(value=True),
            'INSERT': tk.BooleanVar(value=True),
            'UPDATE': tk.BooleanVar(value=True),
            'DELETE': tk.BooleanVar(value=True),
            'CREATE': tk.BooleanVar(value=False),
            'DROP': tk.BooleanVar(value=False),
            'ALTER': tk.BooleanVar(value=False),
            'INDEX': tk.BooleanVar(value=False),
            'GRANT': tk.BooleanVar(value=False)
        }

        # Frame para checkboxes
        check_frame = ttk.Frame(main_frame)
        check_frame.pack(fill="x", pady=(0, 10))

        row, col = 0, 0
        for priv_name, var in self.privs.items():
            ttk.Checkbutton(check_frame, text=priv_name, variable=var).grid(
                row=row, column=col, sticky="w", padx=(0, 15), pady=2)
            col += 1
            if col > 2:
                col = 0
                row += 1

        # Opción para todos los privilegios
        ttk.Separator(main_frame, orient='horizontal').pack(fill="x", pady=10)
        
        self.all_privs = tk.BooleanVar(value=False)
        ttk.Checkbutton(main_frame, text="Otorgar TODOS los privilegios (ALL)", 
                       variable=self.all_privs, command=self.toggle_all).pack(anchor="w")

        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=(20, 0))

        ttk.Button(btn_frame, text="Aceptar", command=self.aceptar).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Cancelar", command=self.cancelar).pack(side="left")

    def toggle_all(self):
        """Habilita/deshabilita checkboxes individuales según ALL"""
        enabled = not self.all_privs.get()
        for var in self.privs.values():
            if not enabled:
                var.set(False)

    def center_window(self):
        self.update_idletasks()
        width = 350
        height = 300
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def aceptar(self):
        if self.all_privs.get():
            self.result = "ALL"
        else:
            selected_privs = [name for name, var in self.privs.items() if var.get()]
            if not selected_privs:
                messagebox.showerror("Error", "Debe seleccionar al menos un privilegio")
                return
            self.result = ",".join(selected_privs)
        
        self.destroy()

    def cancelar(self):
        self.result = None
        self.destroy()

# Ejemplo de uso
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Configurador MySQL Red")
    root.geometry("900x700")
    
    # Aplicar estilo
    style = ttk.Style()
    style.theme_use('clam')
    
    app = ConfigurarServidor(root)
    root.mainloop()