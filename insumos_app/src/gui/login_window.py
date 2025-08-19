import ctypes
import socket
import tkinter as tk
from tkinter import messagebox
import mysql.connector
import sys
import os
from PIL import Image, ImageTk
import configparser
import threading

def get_executable_dir():
    """Obtiene el directorio donde está el ejecutable o el script"""
    if getattr(sys, 'frozen', False):
        # Ejecutable de PyInstaller - usar directorio del ejecutable
        return os.path.dirname(os.path.abspath(sys.executable))
    else:
        # En desarrollo - obtener el directorio src/gui donde están los archivos
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return current_dir

def get_config_path(filename):
    """Obtiene la ruta correcta para archivos de configuración"""
    if getattr(sys, 'frozen', False):
        # En ejecutable con PyInstaller, usar el directorio temporal interno
        try:
            # Primero intentar desde el directorio temporal de PyInstaller
            temp_path = os.path.join(sys._MEIPASS, filename)
            if os.path.exists(temp_path):
                return temp_path
        except AttributeError:
            pass
        
        # Fallback: junto al ejecutable
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        return os.path.join(exe_dir, filename)
    else:
        # En desarrollo, están en el mismo directorio del script (src/gui)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, filename)

def get_bat_path():
    """Obtiene la ruta correcta para el archivo .bat"""
    if getattr(sys, 'frozen', False):
        # En ejecutable con PyInstaller, usar el directorio temporal interno
        try:
            # Primero intentar desde el directorio temporal de PyInstaller
            temp_path = os.path.join(sys._MEIPASS, "modificar_mysql.bat")
            if os.path.exists(temp_path):
                return temp_path
        except AttributeError:
            pass
        
        # Fallback: junto al ejecutable
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        return os.path.join(exe_dir, "modificar_mysql.bat")
    else:
        # En desarrollo - el .bat está en src/gui
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, "modificar_mysql.bat")

def resource_path(relative_path):
    """Obtiene la ruta correcta para recursos (iconos, etc.)"""
    try:
        # En ejecutable de PyInstaller
        base_path = sys._MEIPASS
    except AttributeError:
        # En desarrollo - desde src/gui, subir a la raíz del proyecto
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    return os.path.join(base_path, relative_path)

def debug_paths():
    """Función de debug para mostrar todas las rutas que se están usando"""
    try:
        print("=== DEBUG: RUTAS DE ARCHIVOS ===")
        print(f"Script actual: {__file__}")
        print(f"Directorio del script: {os.path.dirname(os.path.abspath(__file__))}")
        print(f"¿Es ejecutable?: {getattr(sys, 'frozen', False)}")
        
        # Información específica de PyInstaller
        if getattr(sys, 'frozen', False):
            print(f"Ejecutable: {sys.executable}")
            try:
                print(f"Directorio temporal PyInstaller: {sys._MEIPASS}")
                if os.path.exists(sys._MEIPASS):
                    print("Contenido del directorio temporal:")
                    for item in os.listdir(sys._MEIPASS):
                        print(f"  {item}")
                else:
                    print("El directorio _MEIPASS no existe")
            except AttributeError:
                print("Sin directorio temporal _MEIPASS")
            except Exception as e:
                print(f"Error listando _MEIPASS: {e}")
        
        config_path = get_config_path("mysql_config.ini")
        bat_path = get_bat_path()
        
        print(f"Ruta config: {config_path}")
        print(f"¿Existe config?: {os.path.exists(config_path) if config_path else False}")
        print(f"Ruta bat: {bat_path}")
        print(f"¿Existe bat?: {os.path.exists(bat_path) if bat_path else False}")
        
        # Mostrar contenido del directorio actual solo en desarrollo
        if not getattr(sys, 'frozen', False):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            print(f"Contenido de {script_dir}:")
            try:
                for item in os.listdir(script_dir):
                    item_path = os.path.join(script_dir, item)
                    print(f"  {'[D]' if os.path.isdir(item_path) else '[F]'} {item}")
            except Exception as e:
                print(f"  Error listando directorio: {e}")
        print("================================")
    except Exception as e:
        print(f"Error en debug_paths: {e}")
        import traceback
        traceback.print_exc()

# CORRECCIÓN 2: Manejo seguro de importaciones
# Agregar el directorio raíz del proyecto al PATH de Python
if not getattr(sys, 'frozen', False):
    # Solo en desarrollo
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sys.path.append(project_root)
    except Exception:
        pass

# Agregar el directorio raíz del proyecto al PATH de Python
if not getattr(sys, 'frozen', False):
    # Solo en desarrollo
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.append(project_root)

try:
    from src.database.db_manager import verificar_credenciales, crear_tabla_usuarios
except ImportError:
    # En caso de que no se pueda importar, definir funciones básicas
    def verificar_credenciales(username, password):
        # Implementación básica para el ejecutable
        pass
    def crear_tabla_usuarios():
        pass

def crear_script_bat(bind_address, port, max_connections, ruta_bat):
    contenido = f"""@echo off
setlocal enabledelayedexpansion

set CONFIG_FILE="C:\\ProgramData\\MySQL\\MySQL Server 8.0\\my.ini"
set BACKUP_FILE=%CONFIG_FILE%.backup

copy %CONFIG_FILE% %BACKUP_FILE%

powershell -Command "((Get-Content -LiteralPath \\"%CONFIG_FILE%\\") -replace 'bind-address=.*', 'bind-address = {bind_address}') | Set-Content -LiteralPath \\"%CONFIG_FILE%\\""
powershell -Command "((Get-Content -LiteralPath \\"%CONFIG_FILE%\\") -replace 'port=.*', 'port = {port}') | Set-Content -LiteralPath \\"%CONFIG_FILE%\\""
powershell -Command "((Get-Content -LiteralPath \\"%CONFIG_FILE%\\") -replace 'max_connections=.*', 'max_connections = {max_connections}') | Set-Content -LiteralPath \\"%CONFIG_FILE%\\""

echo Configuración actualizada.

echo Reiniciando servicio MySQL...
net stop MySQL80
net start MySQL80

echo Servicio MySQL reiniciado.
pause
"""
    try:
        os.makedirs(os.path.dirname(ruta_bat), exist_ok=True)
        with open(ruta_bat, 'w', encoding='utf-8') as f:
            f.write(contenido)
        print(f"Script .bat creado en: {ruta_bat}")
    except Exception as e:
        print(f"Error creando script .bat: {e}")

def verificar_credenciales_fallback(username, password):
    """Función fallback para verificar credenciales cuando no se puede importar el módulo"""
    try:
        config_file = get_config_path("mysql_config.ini")
        if not os.path.exists(config_file):
            return None
            
        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')
        
        if 'MySQL' not in config:
            return None
            
        mysql_config = config['MySQL']
        host = mysql_config.get('host', 'localhost')
        port = int(mysql_config.get('port', '3306'))
        user = mysql_config.get('admin_user', 'root')
        password_db = mysql_config.get('admin_pass', '')
        database = mysql_config.get('database', 'insumos')
        
        # Conectar a MySQL y verificar/crear tabla
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password_db,
            connection_timeout=10
        )
        
        cursor = connection.cursor()
        
        # Crear database si no existe
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
        cursor.execute(f"USE {database}")
        
        # Crear tabla usuarios si no existe
        create_table_query = """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            nombre VARCHAR(100) NOT NULL,
            cargo VARCHAR(100),
            activo BOOLEAN DEFAULT TRUE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_table_query)
        
        # Insertar usuario admin por defecto si no existe
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO usuarios (username, password, nombre, cargo) VALUES (%s, %s, %s, %s)",
                ('admin', 'admin123', 'Administrador', 'Administrador del Sistema')
            )
            connection.commit()
        
        # Verificar credenciales del usuario
        cursor.execute(
            "SELECT id, username, nombre, cargo FROM usuarios WHERE username = %s AND password = %s AND activo = TRUE",
            (username, password)
        )
        
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if result:
            return {
                'id': result[0],
                'username': result[1],
                'nombre': result[2],
                'cargo': result[3]
            }
        else:
            return None
            
    except Exception as e:
        print(f"Error en verificar_credenciales_fallback: {e}")
        return None

def crear_tabla_usuarios_fallback():
    """Función fallback para crear tabla usuarios"""
    return True  # Ya se maneja en verificar_credenciales_fallback

# Intentar importar funciones del módulo, usar fallback si falla
try:
    if not getattr(sys, 'frozen', False):
        from src.database.db_manager import verificar_credenciales, crear_tabla_usuarios
    else:
        # En ejecutable, usar funciones fallback
        verificar_credenciales = verificar_credenciales_fallback
        crear_tabla_usuarios = crear_tabla_usuarios_fallback
except ImportError:
    print("Usando funciones fallback para manejo de base de datos")
    verificar_credenciales = verificar_credenciales_fallback
    crear_tabla_usuarios = crear_tabla_usuarios_fallback

# CORRECCIÓN 3: Función verificar_mysql_y_continuar más robusta
def verificar_mysql_y_continuar(self):
    """Verifica la conexión MySQL y decide qué mostrar - VERSIÓN CORREGIDA"""
    def verificar_conexion():
        try:
            print("Iniciando verificación de conexión MySQL...")
            
            # Debug completo de rutas con manejo de errores
            try:
                debug_paths()
            except Exception as e:
                print(f"Error en debug_paths: {e}")
            
            # Usar la nueva función para obtener la ruta del config
            config_file = get_config_path("mysql_config.ini")
            print(f"Buscando archivo de configuración en: {config_file}")
            
            if not config_file or not os.path.exists(config_file):
                # En ejecutable, intentar crear un archivo de configuración básico
                if getattr(sys, 'frozen', False):
                    print("⚠️ Archivo config no encontrado en ejecutable, intentando crear uno básico...")
                    try:
                        self.crear_config_basico(config_file)
                        if os.path.exists(config_file):
                            print("✅ Archivo de configuración básico creado")
                        else:
                            error_msg = f"No se pudo crear archivo de configuración en: {config_file}"
                            print(f"❌ {error_msg}")
                            self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                            return
                    except Exception as e:
                        error_msg = f"Error creando configuración básica: {str(e)}"
                        print(f"❌ {error_msg}")
                        self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                        return
                else:
                    error_msg = f"Archivo de configuración MySQL no encontrado en: {config_file}"
                    print(f"❌ {error_msg}")
                    self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                    return
            
            # Cargar configuración usando la ruta correcta
            config = configparser.ConfigParser()
            try:
                config.read(config_file, encoding='utf-8')
                print(f"✅ Archivo de configuración leído correctamente")
            except Exception as e:
                error_msg = f"Error leyendo archivo de configuración: {str(e)}"
                print(f"❌ {error_msg}")
                self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                return
            
            if 'MySQL' not in config:
                error_msg = "Configuración MySQL no válida en archivo mysql_config.ini"
                print(f"❌ {error_msg}")
                self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                return
            
            mysql_config = config['MySQL']
            host = mysql_config.get('host', 'localhost')
            port = int(mysql_config.get('port', '3306'))
            user = mysql_config.get('admin_user', 'root')
            password = mysql_config.get('admin_pass', '')
            
            print(f"Configuración cargada: {user}@{host}:{port}")
            
            if not password:
                error_msg = "Contraseña de MySQL no configurada"
                print(f"❌ {error_msg}")
                self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                return
            
            print(f"Probando conexión a {user}@{host}:{port}")
            
            # Verificar conectividad de red
            if not verificar_conectividad_red(host, port):
                error_msg = f"No se puede acceder al puerto {port} en {host}. Verifique que MySQL esté ejecutándose."
                print(f"❌ {error_msg}")
                self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                return
            
            # Intentar conexión MySQL básica
            try:
                connection = mysql.connector.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    connection_timeout=10,
                    autocommit=True
                )
                
                cursor = connection.cursor()
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                print(f"✅ Conexión MySQL exitosa - Versión: {version}")
                cursor.close()
                connection.close()
                
            except mysql.connector.Error as e:
                error_msg = f"Error MySQL {e.errno}: {e.msg}"
                if e.errno == 1045:
                    error_msg = "Usuario o contraseña incorrectos en configuración MySQL"
                elif e.errno == 2003:
                    error_msg = "No se puede conectar al servidor MySQL. Verifique que esté ejecutándose."
                elif e.errno == 1049:
                    error_msg = "Base de datos no existe. Se creará automáticamente."
                
                print(f"❌ Error de conexión MySQL: {error_msg}")
                self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                return
            
            # Intentar crear las tablas si es posible
            try:
                crear_tabla_usuarios()
                print("✅ Tablas verificadas/creadas")
            except Exception as e:
                print(f"⚠️ Error creando tablas: {e} - continuando...")
            
            print("✅ Conexión MySQL exitosa, mostrando login...")
            # Si llegamos aquí, la conexión funciona
            self.root.after(0, self.mostrar_login)
            
        except Exception as e:
            error_msg = f"Error inesperado en verificación: {str(e)}"
            print(f"❌ {error_msg}")
            # Imprimir stack trace completo para debug
            import traceback
            traceback.print_exc()
            self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))

    # Mostrar mensaje de carga
    self.mostrar_mensaje_carga()
    
    # Agregar un pequeño delay antes de ejecutar la verificación
    self.root.after(500, lambda: threading.Thread(target=verificar_conexion, daemon=True).start())

def ejecutar_bat_con_elevacion(ruta_bat):
    import ctypes
    ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", ruta_bat, None, None, 1)
    if ret <= 32:
        print(f"Error al ejecutar el script con elevación, código: {ret}")
        return False
    return True

def es_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def ejecutar_como_admin():
    if es_admin():
        return True  # Ya es admin

    executable = sys.executable
    params = ' '.join([f'"{arg}"' for arg in sys.argv])

    ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, params, None, 1)

    if ret <= 32:
        print(f"Error al pedir elevación, código: {ret}")
        return False
    else:
        return True

def debug_mysql_connection():
    """Función de debug para probar la conexión MySQL directamente - MEJORADA PARA EJECUTABLE"""
    try:
        print("=== DEBUG: Probando conexión MySQL ===")
        
        import mysql.connector
        
        # Cargar configuración usando la ruta correcta
        config = configparser.ConfigParser()
        config_file = get_config_path("mysql_config.ini")
        print(f"Buscando archivo de configuración en: {config_file}")
        
        if not os.path.exists(config_file):
            print(f"❌ No existe archivo de configuración MySQL en: {config_file}")
            
            # Si es ejecutable, intentar crear uno básico
            if getattr(sys, 'frozen', False):
                print("⚠️ Es ejecutable, intentando crear configuración básica...")
                try:
                    # Crear configuración básica temporalmente para la clase
                    temp_login = type('TempLogin', (), {})()
                    temp_login.crear_config_basico = lambda self, path: crear_config_basico(temp_login, path)
                    temp_login.crear_config_basico(config_file)
                    
                    if os.path.exists(config_file):
                        print("✅ Configuración básica creada")
                    else:
                        return False
                except Exception as e:
                    print(f"❌ Error creando configuración: {e}")
                    return False
            else:
                return False
        
        try:
            config.read(config_file, encoding='utf-8')
        except Exception as e:
            print(f"❌ Error leyendo configuración: {e}")
            return False
            
        if 'MySQL' in config:
            mysql_config = config['MySQL']
            host = mysql_config.get('host', 'localhost')
            port = int(mysql_config.get('port', '3306'))
            user = mysql_config.get('admin_user', 'root')
            password = mysql_config.get('admin_pass', '')
            
            if not password:
                print("❌ Contraseña no configurada en archivo de configuración")
                return False
            
            print(f"Intentando conectar a: {user}@{host}:{port}")
            
            # Verificar conectividad de red primero
            if not verificar_conectividad_red(host, port):
                print("❌ Sin conectividad de red al servidor MySQL")
                return False
            
            connection = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                connection_timeout=10,
                autocommit=True
            )
            
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            print(f"✅ Conexión exitosa - MySQL {version}")
            cursor.close()
            connection.close()
            
            return True
        else:
            print("❌ No hay configuración MySQL en el archivo")
            
    except mysql.connector.Error as e:
        print(f"❌ Error MySQL: {e.errno} - {e.msg}")
        return False
    except Exception as e:
        print(f"❌ Error en debug de conexión: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return False

def crear_config_basico(self, config_file):
        """Crea un archivo de configuración básico si no existe"""
        try:
            config = configparser.ConfigParser()
            config['MySQL'] = {
                'host': '127.0.0.1',
                'port': '3306',
                'admin_user': 'root',
                'admin_pass': '0.5735',
                'bind_address': '0.0.0.0',
                'max_connections': '100',
                'timeout': '28800',
                'database': 'insumos'
            }
            
            # Crear directorio si no existe
            config_dir = os.path.dirname(config_file)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
            
            # Escribir archivo
            with open(config_file, 'w', encoding='utf-8') as f:
                config.write(f)
            
            print(f"✅ Archivo de configuración básico creado en: {config_file}")
            
        except Exception as e:
            print(f"❌ Error creando configuración básica: {e}")
            raise

def verificar_conectividad_red(host, port):
    """Verifica si el puerto MySQL está accesible - NUEVA FUNCIÓN"""
    try:
        # Resolver DNS primero
        if host.lower() == 'localhost':
            host = '127.0.0.1'
        
        ip = socket.gethostbyname(host)
        print(f"DNS resuelto: {host} -> {ip}")
        
        # Probar conexión TCP
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 10 segundos timeout
        result = sock.connect_ex((ip, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Puerto {port} accesible en {host}")
            return True
        else:
            print(f"❌ Puerto {port} NO accesible en {host}")
            print("💡 Posibles causas:")
            print("   - MySQL no está ejecutándose")
            print("   - Firewall bloqueando el puerto")
            print("   - bind-address configurado incorrectamente")
            return False
            
    except socket.gaierror as e:
        print(f"❌ Error DNS: No se pudo resolver {host}")
        return False
    except Exception as e:
        print(f"❌ Error de conectividad: {e}")
        return False

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
        self.config_file = get_config_path("mysql_config.ini")
        self.max_connections_var = tk.StringVar(value="100")
        self.timeout_var = tk.StringVar(value="28800")
        
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
        
    def aplicar_configuracion_red(self):
        try:
            import platform
            if platform.system() != "Windows":
                messagebox.showerror("Error", "Esta función solo está implementada para Windows.")
                return

            bind_address = '0.0.0.0'
            port = int(self.puerto_var.get())
            max_connections = 100

            # Usar la nueva función para obtener la ruta del .bat
            ruta_bat = get_bat_path()  # CAMBIO AQUÍ
            crear_script_bat(bind_address, port, max_connections, ruta_bat)

            messagebox.showinfo("Permisos", "Se solicitarán permisos de administrador para modificar el archivo my.ini.")

            if ejecutar_bat_con_elevacion(ruta_bat):
                messagebox.showinfo("Éxito", "Archivo de configuración modificado correctamente.\nRecuerde reiniciar MySQL para aplicar cambios.")
            else:
                messagebox.showerror("Error", "No se pudo ejecutar el script con permisos de administrador.")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo aplicar la configuración: {str(e)}")

    def editar_y_ejecutar_bat(self, bind_address, port, max_connections):
        import platform
        if platform.system() != "Windows":
            messagebox.showerror("Error", "Esta función solo está implementada para Windows.")
            return

        ruta_bat = os.path.join(os.path.abspath(os.path.dirname(__file__)), "modificar_mysql.bat")
        self.crear_script_bat(bind_address, port, max_connections, ruta_bat)

        messagebox.showinfo("Permisos", "Se solicitarán permisos de administrador para modificar el archivo my.ini.")

        if self.ejecutar_bat_con_elevacion(ruta_bat):
            messagebox.showinfo("Éxito", "Archivo de configuración modificado correctamente.\nRecuerde reiniciar MySQL para aplicar cambios.")
        else:
            messagebox.showerror("Error", "No se pudo ejecutar el script con permisos de administrador.")

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
        """Usar threading mejorado para probar conexión"""
        self.test_btn.config(state='disabled')
        self.status_label.config(text="Probando conexión...", fg='#f39c12')

        def test_connection():
            try:
                host = self.host_var.get().strip()
                port = int(self.puerto_var.get().strip())
                user = self.admin_user_var.get().strip()
                password = self.admin_pass_var.get()

                if not password:
                    self.config_window.after(0, lambda: self.connection_error("Debe ingresar la contraseña del usuario root"))
                    return

                if host.lower() == 'localhost':
                    host = '127.0.0.1'

                print(f"Probando conexión a {user}@{host}:{port}")
                
                # Verificar conectividad de red primero
                if not verificar_conectividad_red(host, port):
                    self.config_window.after(0, lambda: self.connection_error("Puerto MySQL no accesible. Verifique que MySQL esté ejecutándose."))
                    return

                # Intentar conexión MySQL
                connection = mysql.connector.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    connection_timeout=10,
                    autocommit=True
                )

                cursor = connection.cursor()
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                cursor.close()
                connection.close()

                self.config_window.after(0, lambda: self.connection_success(version))

            except mysql.connector.Error as e:
                error_msg = f"Error {e.errno}: {e.msg}"
                if e.errno == 1045:  # Access denied
                    error_msg = "Usuario o contraseña incorrectos"
                elif e.errno == 2003:  # Can't connect
                    error_msg = "No se puede conectar al servidor MySQL. Verifique que esté ejecutándose."
                elif e.errno == 1130:  # Host not allowed
                    error_msg = "Host no autorizado para conectar"
                
                print(f"❌ Error MySQL: {error_msg}")
                self.config_window.after(0, lambda: self.connection_error(error_msg))
                
            except Exception as e:
                error_msg = f"Error inesperado: {str(e)}"
                print(f"❌ {error_msg}")
                self.config_window.after(0, lambda: self.connection_error(error_msg))
            finally:
                self.config_window.after(0, lambda: self.test_btn.config(state='normal'))

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
        self.guardar_configuracion()
        self.aplicar_configuracion_red()  # Aplica configuración y reinicia MySQL

        host = self.host_var.get().strip()
        if host.lower() == 'localhost':
            host = '127.0.0.1'

        self.result = {
            'host': host,
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
        config = configparser.ConfigParser()
        
        host = self.host_var.get().strip()
        if host.lower() == 'localhost':
            host = '127.0.0.1'
            
        config['MySQL'] = {
            'host': host,
            'port': self.puerto_var.get().strip(),
            'admin_user': self.admin_user_var.get().strip(),
            'admin_pass': self.admin_pass_var.get(),
            'bind_address': '0.0.0.0',
            'max_connections': '100',
            'timeout': '28800',
            'database': 'insumos'
        }
        
        try:
            # Usar la nueva función para obtener la ruta
            config_dir = os.path.dirname(self.config_file)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
                
            with open(self.config_file, 'w') as f:
                config.write(f)
            print(f"Configuración guardada en: {os.path.abspath(self.config_file)}")
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
                    self.host_var.set(mysql_config.get('host', '127.0.0.1'))
                    self.puerto_var.set(mysql_config.get('port', '3306'))
                    self.admin_user_var.set(mysql_config.get('admin_user', 'root'))
                    self.admin_pass_var.set(mysql_config.get('admin_pass', ''))
                    print("Configuración cargada desde archivo")
                    
            except Exception as e:
                print(f"Error cargando configuración: {e}")

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
        self.loading_active = False
        self.animation_job = None
        
        # Verificar conexión MySQL antes de mostrar login
        self.verificar_mysql_y_continuar()

    
    def verificar_mysql_y_continuar(self):
        """Verifica la conexión MySQL y decide qué mostrar - MEJORADA PARA EJECUTABLE"""
        def verificar_conexion():
            try:
                print("Iniciando verificación de conexión MySQL...")
                
                # Debug completo de rutas
                debug_paths()
                
                # Usar la nueva función para obtener la ruta del config
                config_file = get_config_path("mysql_config.ini")
                print(f"Buscando archivo de configuración en: {config_file}")
                
                if not os.path.exists(config_file):
                    # En ejecutable, intentar crear un archivo de configuración básico
                    if getattr(sys, 'frozen', False):
                        print("⚠️ Archivo config no encontrado en ejecutable, intentando crear uno básico...")
                        try:
                            self.crear_config_basico(config_file)
                            if os.path.exists(config_file):
                                print("✅ Archivo de configuración básico creado")
                            else:
                                error_msg = f"No se pudo crear archivo de configuración en: {config_file}"
                                print(f"❌ {error_msg}")
                                self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                                return
                        except Exception as e:
                            error_msg = f"Error creando configuración básica: {str(e)}"
                            print(f"❌ {error_msg}")
                            self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                            return
                    else:
                        error_msg = f"Archivo de configuración MySQL no encontrado en: {config_file}"
                        print(f"❌ {error_msg}")
                        self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                        return
                
                # Cargar configuración usando la ruta correcta
                config = configparser.ConfigParser()
                try:
                    config.read(config_file, encoding='utf-8')
                    print(f"✅ Archivo de configuración leído correctamente")
                except Exception as e:
                    error_msg = f"Error leyendo archivo de configuración: {str(e)}"
                    print(f"❌ {error_msg}")
                    self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                    return
                
                if 'MySQL' not in config:
                    error_msg = "Configuración MySQL no válida en archivo mysql_config.ini"
                    print(f"❌ {error_msg}")
                    self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                    return
                
                mysql_config = config['MySQL']
                host = mysql_config.get('host', 'localhost')
                port = int(mysql_config.get('port', '3306'))
                user = mysql_config.get('admin_user', 'root')
                password = mysql_config.get('admin_pass', '')
                
                print(f"Configuración cargada: {user}@{host}:{port}")
                
                if not password:
                    error_msg = "Contraseña de MySQL no configurada"
                    print(f"❌ {error_msg}")
                    self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                    return
                
                print(f"Probando conexión a {user}@{host}:{port}")
                
                # Verificar conectividad de red
                if not verificar_conectividad_red(host, port):
                    error_msg = f"No se puede acceder al puerto {port} en {host}. Verifique que MySQL esté ejecutándose."
                    print(f"❌ {error_msg}")
                    self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                    return
                
                # Intentar conexión MySQL básica
                try:
                    import mysql.connector
                    connection = mysql.connector.connect(
                        host=host,
                        port=port,
                        user=user,
                        password=password,
                        connection_timeout=10,
                        autocommit=True
                    )
                    
                    cursor = connection.cursor()
                    cursor.execute("SELECT VERSION()")
                    version = cursor.fetchone()[0]
                    print(f"✅ Conexión MySQL exitosa - Versión: {version}")
                    cursor.close()
                    connection.close()
                    
                except mysql.connector.Error as e:
                    error_msg = f"Error MySQL {e.errno}: {e.msg}"
                    if e.errno == 1045:
                        error_msg = "Usuario o contraseña incorrectos en configuración MySQL"
                    elif e.errno == 2003:
                        error_msg = "No se puede conectar al servidor MySQL. Verifique que esté ejecutándose."
                    elif e.errno == 1049:
                        error_msg = "Base de datos no existe. Se creará automáticamente."
                    
                    print(f"❌ Error de conexión MySQL: {error_msg}")
                    self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                    return
                
                # Intentar crear las tablas si es posible
                try:
                    if not getattr(sys, 'frozen', False):
                        # Solo en desarrollo
                        from src.database.db_manager import crear_tabla_usuarios
                        crear_tabla_usuarios()
                        print("✅ Tablas verificadas/creadas")
                except ImportError:
                    print("⚠️ No se pudo importar crear_tabla_usuarios - continuando...")
                except Exception as e:
                    print(f"⚠️ Error creando tablas: {e} - continuando...")
                
                print("✅ Conexión MySQL exitosa, mostrando login...")
                # Si llegamos aquí, la conexión funciona
                self.root.after(0, self.mostrar_login)
                
            except Exception as e:
                error_msg = f"Error inesperado en verificación: {str(e)}"
                print(f"❌ {error_msg}")
                # Imprimir stack trace completo para debug
                import traceback
                traceback.print_exc()
                self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))

        # Mostrar mensaje de carga
        self.mostrar_mensaje_carga()
        
        # Agregar un pequeño delay antes de ejecutar la verificación
        self.root.after(500, lambda: threading.Thread(target=verificar_conexion, daemon=True).start())

    def crear_config_basico(self, config_file):
        """Crea un archivo de configuración básico si no existe"""
        try:
            config = configparser.ConfigParser()
            config['MySQL'] = {
                'host': '127.0.0.1',
                'port': '3306',
                'admin_user': 'root',
                'admin_pass': '0.5735',
                'bind_address': '0.0.0.0',
                'max_connections': '100',
                'timeout': '28800',
                'database': 'insumos'
            }
            
            # Crear directorio si no existe
            config_dir = os.path.dirname(config_file)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
            
            # Escribir archivo
            with open(config_file, 'w', encoding='utf-8') as f:
                config.write(f)
            
            print(f"✅ Archivo de configuración básico creado en: {config_file}")
            
        except Exception as e:
            print(f"❌ Error creando configuración básica: {e}")
            raise
    
    def mostrar_mensaje_carga(self):
        """Muestra un mensaje de carga mientras verifica la conexión"""
        print("Mostrando mensaje de carga...")
        
        # Detener animaciones previas
        self.loading_active = False
        if self.animation_job:
            try:
                self.root.after_cancel(self.animation_job)
            except:
                pass

        # Activar modo de carga
        self.loading_active = True
        
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

        # Mensaje principal
        tk.Label(
            center_frame,
            text="Verificando conexión MySQL...",
            font=('Segoe UI', 14, 'bold'),
            bg='#f8f9fa',
            fg='#2c3e50'
        ).pack(pady=(0, 10))

        # Mensaje secundario
        tk.Label(
            center_frame,
            text="Por favor espere un momento",
            font=('Segoe UI', 10),
            bg='#f8f9fa',
            fg='#7f8c8d'
        ).pack()

        # Barra de progreso simulada (opcional)
        progress_frame = tk.Frame(center_frame, bg='#f8f9fa')
        progress_frame.pack(pady=(20, 0))

        # Crear una barra de progreso simple
        canvas = tk.Canvas(progress_frame, width=200, height=4, bg='#f8f9fa', highlightthickness=0)
        canvas.pack()

        # Animar la barra de progreso
        def animate_progress():
            canvas.delete("all")
            canvas.create_rectangle(0, 0, 200, 4, fill='#ecf0f1', outline='')
            
            import time
            start_time = time.time()
            
            def update_progress():
                if not self.loading_active:
                    return
                    
                try:
                    if not canvas.winfo_exists():
                        return
                        
                    elapsed = (time.time() - start_time) % 2
                    progress = (elapsed / 2) * 200
                    
                    canvas.delete("progress")
                    canvas.create_rectangle(0, 0, progress, 4, fill='#3498db', outline='', tags="progress")
                    
                    if self.loading_active:
                        self.animation_job = self.root.after(50, update_progress)
                        
                except Exception as e:
                    self.loading_active = False
            
            update_progress()

        animate_progress()

        # Actualizar la ventana
        self.root.update()

    def mostrar_configuracion_mysql(self, error_msg):
        """Muestra la ventana de configuración MySQL"""
        print(f"Mostrando configuración MySQL debido a error: {error_msg}")
        
        # Limpiar la ventana
        for widget in self.root.winfo_children():
            widget.destroy()

        # Frame principal para la configuración
        config_frame = tk.Frame(self.root, bg='#f8f9fa')
        config_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Título de error
        title_frame = tk.Frame(config_frame, bg='#f8f9fa')
        title_frame.pack(fill='x', pady=(0, 20))

        tk.Label(
            title_frame,
            text="⚠️ Error de Conexión MySQL",
            font=('Segoe UI', 16, 'bold'),
            bg='#f8f9fa',
            fg='#e74c3c'
        ).pack()

        tk.Label(
            title_frame,
            text=f"No se pudo conectar a la base de datos:",
            font=('Segoe UI', 10),
            bg='#f8f9fa',
            fg='#7f8c8d'
        ).pack(pady=(5, 0))

        # Frame para el mensaje de error
        error_frame = tk.Frame(config_frame, bg='#fff5f5', relief='solid', bd=1)
        error_frame.pack(fill='x', pady=(0, 20), padx=10)

        tk.Label(
            error_frame,
            text=error_msg,
            font=('Segoe UI', 9),
            bg='#fff5f5',
            fg='#c53030',
            wraplength=700,
            justify='left'
        ).pack(padx=15, pady=10)

        # Botones de acción
        btn_frame = tk.Frame(config_frame, bg='#f8f9fa')
        btn_frame.pack(fill='x', pady=10)

        # Botón para configurar MySQL
        config_btn = tk.Button(
            btn_frame,
            text="Configurar Conexión MySQL",
            font=('Segoe UI', 11, 'bold'),
            bg='#3498db',
            fg='white',
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2',
            command=self.abrir_configuracion_mysql
        )
        config_btn.pack(side='left', padx=(0, 10))

        # Botón para reintentar
        retry_btn = tk.Button(
            btn_frame,
            text="Reintentar Conexión",
            font=('Segoe UI', 11, 'bold'),
            bg='#27ae60',
            fg='white',
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2',
            command=self.reintentar_conexion
        )
        retry_btn.pack(side='left', padx=(0, 10))

        # Botón para salir
        exit_btn = tk.Button(
            btn_frame,
            text="Salir",
            font=('Segoe UI', 11, 'bold'),
            bg='#e74c3c',
            fg='white',
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2',
            command=self.root.quit
        )
        exit_btn.pack(side='right')

        # Efectos hover
        def create_hover_effect(button, normal_color, hover_color):
            def on_enter(e):
                button.configure(bg=hover_color)
            def on_leave(e):
                button.configure(bg=normal_color)
            button.bind('<Enter>', on_enter)
            button.bind('<Leave>', on_leave)

        create_hover_effect(config_btn, '#3498db', '#2980b9')
        create_hover_effect(retry_btn, '#27ae60', '#2ecc71')
        create_hover_effect(exit_btn, '#e74c3c', '#c0392b')

    def abrir_configuracion_mysql(self):
        """Abre la ventana de configuración MySQL"""
        print("Abriendo configuración MySQL...")
        
        try:
            config_mysql = ConfiguracionMySQL(self.root)
            
            # Esperar resultado
            self.root.wait_window(config_mysql.config_window)
            
            if hasattr(config_mysql, 'result') and config_mysql.result:
                print("Configuración guardada, reintentando conexión...")
                # Reintentar conexión con nueva configuración
                self.reintentar_conexion()
            else:
                print("Configuración cancelada")
                # Usuario canceló - mostrar opciones nuevamente
                
        except Exception as e:
            print(f"Error en configuración MySQL: {e}")
            messagebox.showerror("Error", f"Error al abrir configuración: {str(e)}")

    def reintentar_conexion(self):
        """Reintenta la verificación de conexión"""
        print("Reintentando conexión...")
        self.verificar_mysql_y_continuar()

    def mostrar_login(self):
        """Muestra la pantalla de login"""
        # Detener todas las animaciones primero
        self.loading_active = False
        if hasattr(self, 'animation_job') and self.animation_job:
            try:
                self.root.after_cancel(self.animation_job)
            except:
                pass
        
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
        """Función de login mejorada con mejor manejo de errores"""
        username = self.username_entry.get().strip().lower()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Por favor ingrese usuario y contraseña")
            return

        def login_thread():
            try:
                # Usar la nueva función para obtener la ruta del config
                config_file = get_config_path("mysql_config.ini")  # CAMBIO AQUÍ
                
                config = configparser.ConfigParser()
                config.read(config_file)
                
                if 'MySQL' in config:
                    mysql_config = config['MySQL']
                    host = mysql_config.get('host', 'localhost')
                    port = int(mysql_config.get('port', '3306'))
                    
                    if not verificar_conectividad_red(host, port):
                        self.root.after(0, lambda: messagebox.showerror("Error de Conexión", 
                            "No se puede conectar al servidor MySQL.\nVerifique que esté ejecutándose y accesible."))
                        return
                
                # Verificar credenciales
                try:
                    from src.database.db_manager import verificar_credenciales
                    usuario = verificar_credenciales(username, password)
                except ImportError:
                    # Fallback si no se puede importar el módulo
                    messagebox.showerror("Error", "Error al cargar módulo de base de datos")
                    return
                
                if usuario:
                    def abrir_aplicacion():
                        self.root.destroy()
                        try:
                            from src.gui.main_window import MainWindow
                            app = MainWindow(usuario)
                            app.run()
                        except ImportError:
                            messagebox.showerror("Error", "Error al cargar la aplicación principal")
                    
                    self.root.after(0, abrir_aplicacion)
                else:
                    self.root.after(0, lambda: [
                        messagebox.showerror("Error", "Usuario o contraseña incorrectos"),
                        self.password_entry.delete(0, tk.END),
                        self.password_entry.focus()
                    ])
                    
            except Exception as e:
                error_msg = f"Error al verificar credenciales:\n{str(e)}\n\nVerifique la configuración de MySQL"
                self.root.after(0, lambda: messagebox.showerror("Error de Conexión", error_msg))

        threading.Thread(target=login_thread, daemon=True).start()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    # Debug completo al inicio
    print("=" * 50)
    print("INICIANDO SISTEMA DE GESTIÓN DE INSUMOS")
    print("=" * 50)
    
    # Información del entorno
    print(f"Python: {sys.version}")
    print(f"Ejecutable: {getattr(sys, 'frozen', False)}")
    if getattr(sys, 'frozen', False):
        print(f"Ruta ejecutable: {sys.executable}")
        try:
            print(f"Directorio temporal PyInstaller: {sys._MEIPASS}")
        except AttributeError:
            print("Sin directorio temporal _MEIPASS")
    
    # Debug de rutas
    print("\n" + "-" * 30)
    debug_paths()
    
    # Prueba de conexión
    print("\n" + "-" * 30)
    print("Probando conexión MySQL directamente...")
    try:
        connection_ok = debug_mysql_connection()
        if connection_ok:
            print("✅ Conexión MySQL OK, iniciando aplicación normal")
        else:
            print("❌ Conexión MySQL falló, se mostrará configuración")
    except Exception as e:
        print(f"❌ Error en debug de conexión: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("INICIANDO INTERFAZ GRÁFICA...")
    print("=" * 50)
    
    try:
        login = LoginWindow()
        login.run()
    except Exception as e:
        print(f"❌ Error fatal iniciando aplicación: {e}")
        import traceback
        traceback.print_exc()
        input("Presione Enter para salir...")