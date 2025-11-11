import ctypes
import socket
import tkinter as tk
from tkinter import messagebox
import mysql.connector
import sys
import os

import hashlib

from PIL import Image, ImageTk
import configparser
import threading

# Modo silencioso: no imprime nada en consola cuando está en True
SILENT = True

def log(*args, **kwargs):
    if not SILENT:
        print(*args, **kwargs)

def log_exc():
    if not SILENT:
        import traceback
        traceback.print_exc()

def get_executable_dir():
    """Obtiene el directorio donde está el ejecutable o el script"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return current_dir

def get_config_path(filename="mysql_config.ini"):
    """
    UNA ÚNICA ubicación para el archivo de configuración:
    - Desarrollo: src/gui/
    - Ejecutable: junto al .exe
    """
    if getattr(sys, 'frozen', False):
        # Ejecutable: junto al .exe
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        return os.path.join(exe_dir, filename)
    else:
        # Desarrollo: src/gui/ (donde está login_window.py)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, filename)

def get_bat_path():
    """Siempre apunta al lado del ejecutable en modo frozen; en desarrollo al lado del script (src/gui)."""
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        return os.path.join(exe_dir, "modificar_mysql.bat")
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, "modificar_mysql.bat")

def resource_path(relative_path):
    """
    Devuelve ruta absoluta a un recurso tanto en dev como en ejecutable (PyInstaller).
    - En ejecutable usa sys._MEIPASS.
    - En desarrollo este archivo está en src/gui, así que subimos un nivel a src/.
    """
    try:
        base_path = sys._MEIPASS  # PyInstaller (onefile/onedir)
    except Exception:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # -> src/
    return os.path.join(base_path, relative_path)

# Constantes de iconos: usamos prefijo utils/icons (coincidir con lo empaquetado)
APP_ICO = os.path.join('utils', 'icons', 'app.ico')
APP_PNG = os.path.join('utils', 'icons', 'app.png')
CFG_ICO = os.path.join('utils', 'icons', 'app1.ico')
CFG_PNG = os.path.join('utils', 'icons', 'app1.png')

def apply_window_icons(win, ico_rel, png_rel):
    """
    Aplica iconos a una ventana Tk/Toplevel.
    - Intenta .ico (Windows) con iconbitmap.
    - Aplica PNG como wm_iconphoto (conservar referencias para evitar GC).
    """
    # .ico (Windows)
    try:
        ico_path = resource_path(ico_rel)
        if os.path.exists(ico_path):
            win.iconbitmap(ico_path)
    except Exception as e:
        log(f"iconbitmap fallo: {e}")
    # PNG fallback / multi-size
    try:
        png_path = resource_path(png_rel)
        if os.path.exists(png_path):
            img16 = ImageTk.PhotoImage(Image.open(png_path).resize((16, 16), Image.Resampling.LANCZOS))
            img32 = ImageTk.PhotoImage(Image.open(png_path).resize((32, 32), Image.Resampling.LANCZOS))
            if not hasattr(win, '_icon_imgs'):
                win._icon_imgs = []
            win._icon_imgs.extend([img16, img32])  # evitar GC
            win.wm_iconphoto(True, img16, img32)
    except Exception as e:
        log(f"iconphoto fallo: {e}")

def debug_paths():
    """Función de debug: neutralizada para modo silencioso"""
    if SILENT:
        return
    try:
        log("=" * 80)
        log("=== DEBUG: RUTAS DE ARCHIVOS Y CONECTIVIDAD ===")
        log("=" * 80)

        import platform
        log("\n🖥️  INFORMACIÓN DEL SISTEMA:")
        log(f"   Sistema: {platform.system()} {platform.release()}")
        log(f"   Arquitectura: {platform.architecture()[0]}")
        log(f"   Nombre del equipo: {platform.node()}")
        log(f"   Usuario actual: {os.getenv('USERNAME', 'N/A')}")

        log("\n📁 RUTAS DE ARCHIVOS:")
        log(f"   Script actual: {__file__}")
        log(f"   Directorio del script: {os.path.dirname(os.path.abspath(__file__))}")
        log(f"   ¿Es ejecutable?: {getattr(sys, 'frozen', False)}")

        if getattr(sys, 'frozen', False):
            log(f"   Ejecutable: {sys.executable}")
            try:
                log(f"   Directorio temporal PyInstaller: {sys._MEIPASS}")
                if os.path.exists(sys._MEIPASS):
                    log("   Contenido del directorio temporal:")
                    for item in os.listdir(sys._MEIPASS):
                        log(f"     {item}")
                else:
                    log("   El directorio _MEIPASS no existe")
            except AttributeError:
                log("   Sin directorio temporal _MEIPASS")
            except Exception as e:
                log(f"   Error listando _MEIPASS: {e}")

        config_path = get_config_path("mysql_config.ini")
        bat_path = get_bat_path()

        log(f"   Ruta config: {config_path}")
        log(f"   ¿Existe config?: {os.path.exists(config_path) if config_path else False}")
        log(f"   Ruta bat: {bat_path}")
        log(f"   ¿Existe bat?: {os.path.exists(bat_path) if bat_path else False}")

        if not getattr(sys, 'frozen', False):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            log(f"   Contenido de {script_dir}:")
            try:
                for item in os.listdir(script_dir):
                    item_path = os.path.join(script_dir, item)
                    log(f"     {'[D]' if os.path.isdir(item_path) else '[F]'} {item}")
            except Exception as e:
                log(f"     Error listando directorio: {e}")

        log("\n🌐 DIAGNÓSTICO DE CONECTIVIDAD:")

        mysql_host = None
        mysql_port = 3306
        mysql_user = None
        mysql_password = None

        if config_path and os.path.exists(config_path):
            try:
                import configparser
                config = configparser.ConfigParser()
                config.read(config_path)
                if 'MySQL' in config:
                    mysql_host = config['MySQL'].get('host')
                    mysql_port = int(config['MySQL'].get('port', 3306))
                    mysql_user = config['MySQL'].get('admin_user')
                    mysql_password = config['MySQL'].get('admin_pass')
                    
                    if mysql_host and mysql_user:
                        log(f"   ✅ Configuración leída desde: {config_path}")
                    else:
                        log("   ⚠️ Configuración incompleta en archivo")
                else:
                    log("   ⚠️ Archivo config existe pero sin sección [MySQL]")
            except Exception as e:
                log(f"   ⚠️ Error leyendo configuración: {e}")
        else:
            log("   ⚠️ No existe archivo de configuración")

        # Validar antes de continuar
        if not mysql_host or not mysql_user or not mysql_password:
            log("   ⚠️ No se puede realizar diagnóstico sin configuración válida")
            return

        log(f"   Servidor objetivo: {mysql_host}:{mysql_port}")
        log(f"   Usuario: {mysql_user}")

        log("\n🔍 1. RESOLUCIÓN DNS:")
        try:
            import socket
            ip_address = socket.gethostbyname(mysql_host)
            log(f"   ✅ {mysql_host} resuelve a: {ip_address}")
        except socket.gaierror as e:
            log(f"   ❌ Error resolviendo {mysql_host}: {e}")
            log("   💡 Sugerencia: Usar IP directa en lugar del nombre")
            mysql_host = "192.168.1.100"
            log(f"   🔄 Intentando con IP: {mysql_host}")

        log(f"\n🔍 2. CONECTIVIDAD DE RED (Puerto {mysql_port}):")
        network_ok = test_network_connectivity(mysql_host, mysql_port)

        log("\n🔍 3. VERIFICACIÓN DE PUERTOS ADICIONALES:")
        test_ports = [80, 443, 53, 8080]
        for port in test_ports:
            result = test_network_connectivity("8.8.8.8", port, timeout=3)
            if result:
                log(f"   ✅ Conectividad general OK (puerto {port})")
                break
        else:
            log("   ⚠️ Posibles problemas de conectividad general")

        log("\n🔍 4. VERIFICACIÓN DE FIREWALL:")
        check_windows_firewall()

        log("\n🔍 5. DEPENDENCIAS MYSQL:")
        check_mysql_dependencies()

        if network_ok:
            log("\n🔍 6. CONEXIÓN MYSQL COMPLETA:")
            mysql_ok = test_mysql_connection(mysql_host, mysql_port, mysql_user, mysql_password)
        else:
            mysql_ok = False
            log("\n⚠️ 6. SALTANDO PRUEBA MYSQL (sin conectividad de red)")

        log("\n🔍 7. CONFIGURACIÓN DE RED LOCAL:")
        check_network_config()

        log("\n" + "=" * 80)
        log("📋 RESUMEN DEL DIAGNÓSTICO")
        log("=" * 80)
        log(f"🌐 Conectividad de red: {'✅ OK' if network_ok else '❌ FALLA'}")
        log(f"🗄️  Conexión MySQL: {'✅ OK' if mysql_ok else '❌ FALLA'}")

        log("\n💡 SUGERENCIAS:")
        if not network_ok:
            log("   🔧 PROBLEMAS DE RED:")
            log("   1. Verificar que el servidor MySQL esté ejecutándose")
            log("   2. Verificar firewall en servidor y cliente")
            log("   3. Verificar que el puerto 3306 esté abierto")
            log("   4. Probar con la IP del servidor en lugar del nombre")
            log("   5. Verificar conectividad de red general")
        elif not mysql_ok:
            log("   🔧 PROBLEMAS DE MYSQL:")
            log("   1. Instalar MySQL Connector/C++ Redistributable")
            log("   2. Instalar Visual C++ Redistributable (todas las versiones)")
            log("   3. Verificar usuario y contraseña")
            log("   4. Verificar permisos del usuario en MySQL")
        else:
            log("   ✅ Todo parece estar funcionando correctamente")

        log("=" * 80)

    except Exception as e:
        log(f"❌ Error en debug_paths: {e}")
        log_exc()

def test_network_connectivity(host, port, timeout=10):
    """Prueba conectividad de red básica"""
    try:
        import socket
        import time
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        start_time = time.time()
        result = sock.connect_ex((host, port))
        end_time = time.time()
        sock.close()

        if result == 0:
            log(f"   ✅ Puerto {port} accesible en {host} ({end_time - start_time:.2f}s)")
            return True
        else:
            log(f"   ❌ Puerto {port} NO accesible en {host} (código: {result})")
            return False
    except Exception as e:
        log(f"   ❌ Error de conectividad a {host}:{port} - {e}")
        return False

def test_mysql_connection(host, port, user, password):
    """Prueba conexión MySQL completa"""
    try:
        import mysql.connector
        log("   🔄 Intentando conexión MySQL...")
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
        cursor.execute("SHOW DATABASES")
        databases = [db[0] for db in cursor.fetchall()]
        cursor.close()
        connection.close()

        log("   ✅ Conexión MySQL exitosa")
        log(f"   📊 Versión MySQL: {version}")
        if databases:
            log(f"   🗄️  Bases de datos disponibles: {', '.join(databases[:5])}")
        return True

    except mysql.connector.Error as e:
        log(f"   ❌ Error MySQL: {e.errno} - {e.msg}")
        if e.errno == 1045:
            log("   💡 Usuario o contraseña incorrectos")
        elif e.errno == 2003:
            log("   💡 No se puede conectar al servidor MySQL")
        elif e.errno == 1130:
            log("   💡 Host no autorizado para conectar")
        elif e.errno == 2013:
            log("   💡 Conexión perdida con el servidor MySQL")
        return False
    except Exception as e:
        log(f"   ❌ Error inesperado: {e}")
        return False

def check_mysql_dependencies():
    """Verifica si las dependencias de MySQL están disponibles"""
    try:
        import mysql.connector
        log(f"   ✅ mysql.connector disponible (versión: {mysql.connector.__version__})")

        import platform
        if platform.system() == "Windows":
            common_mysql_paths = [
                "C:\\Program Files\\MySQL\\MySQL Server 8.0\\lib\\libmysql.dll",
                "C:\\Program Files\\MySQL\\MySQL Server 5.7\\lib\\libmysql.dll",
                "C:\\Windows\\System32\\libmysql.dll",
                "C:\\Windows\\SysWOW64\\libmysql.dll"
            ]

            found_dll = False
            for dll_path in common_mysql_paths:
                if os.path.exists(dll_path):
                    log(f"   ✅ MySQL DLL encontrada: {dll_path}")
                    found_dll = True
                    break

            if not found_dll:
                log("   ⚠️ No se encontraron DLLs de MySQL en ubicaciones comunes")
                log("   💡 Instalar MySQL Connector/C++ Redistributable")

    except ImportError as e:
        log(f"   ❌ mysql.connector NO disponible: {e}")
        log("   💡 Instalar: pip install mysql-connector-python")

def check_windows_firewall():
    """Verifica configuración básica del firewall de Windows"""
    import platform
    if platform.system() != "Windows":
        log("   ℹ️ No es Windows, saltando verificación de firewall")
        return

    try:
        import subprocess
        result = subprocess.run(
            ["netsh", "advfirewall", "show", "allprofiles", "state"],
            capture_output=True, text=True, timeout=10
        )

        if result.returncode == 0:
            if "ON" in result.stdout:
                log("   ⚠️ Firewall de Windows está ACTIVO")
                log("   💡 Verificar reglas para puerto 3306")
            else:
                log("   ✅ Firewall de Windows está INACTIVO")
        else:
            log("   ⚠️ No se pudo verificar estado del firewall")

    except Exception as e:
        log(f"   ⚠️ Error verificando firewall: {e}")

def check_network_config():
    """Verifica configuración básica de red"""
    try:
        import socket
        import platform
        import subprocess

        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)

        log(f"   🖥️ Nombre del equipo: {hostname}")
        log(f"   🌐 IP local: {local_ip}")

        if platform.system() == "Windows":
            try:
                result = subprocess.run(
                    ["ipconfig", "/all"],
                    capture_output=True, text=True, timeout=10
                )

                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if "Default Gateway" in line or "Puerta de enlace predeterminada" in line:
                            gateway = line.split(':')[-1].strip()
                            if gateway and gateway != "":
                                log(f"   🚪 Gateway: {gateway}")
                                break
            except Exception as e:
                log(f"   ⚠️ Error obteniendo gateway: {e}")

    except Exception as e:
        log(f"   ⚠️ Error verificando configuración de red: {e}")

# Manejo de PATH de proyecto en desarrollo
if not getattr(sys, 'frozen', False):
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sys.path.append(project_root)
    except Exception:
        pass

try:
    from src.database.db_manager import verificar_credenciales, crear_tabla_usuarios
except ImportError:
    def verificar_credenciales(username, password):
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
        log(f"Script .bat creado en: {ruta_bat}")
    except Exception as e:
        log(f"Error creando script .bat: {e}")

def verificar_credenciales_fallback(username, password):
    """Función fallback para verificar credenciales cuando no se puede importar el módulo"""
    try:
        config_file = get_config_path("mysql_config.ini")
        if not os.path.exists(config_file):
            log("❌ No existe archivo de configuración")
            return None

        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')

        if 'MySQL' not in config:
            log("❌ Configuración MySQL no encontrada")
            return None

        mysql_config = config['MySQL']
        
        # ✅ SIN valores por defecto hardcodeados
        host = mysql_config.get('host')
        port = int(mysql_config.get('port', 3306))
        user = mysql_config.get('admin_user')
        password_db = mysql_config.get('admin_pass')
        database = mysql_config.get('database', 'insumos')
        
        # Validar que existan los valores requeridos
        if not host or not user or not password_db:
            log("❌ Configuración incompleta")
            return None

        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password_db,
            connection_timeout=10
        )
        cursor = connection.cursor()

        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
        cursor.execute(f"USE {database}")

        create_table_query = """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            nombre_completo VARCHAR(255),
            rol ENUM('admin', 'usuario', 'super_admin') NOT NULL,
            activo BOOLEAN DEFAULT TRUE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_table_query)

        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            admin_pass = "admin123"
            password_hash = hashlib.sha256(admin_pass.encode()).hexdigest()
            cursor.execute(
                "INSERT INTO usuarios (username, password, nombre_completo, rol, activo) VALUES (%s, %s, %s, %s, %s)",
                ('admin', password_hash, 'Administrador del Sistema', 'super_admin', True)
            )
            connection.commit()

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute(
            "SELECT id, username, nombre_completo, rol FROM usuarios WHERE username = %s AND password = %s AND activo = TRUE",
            (username, password_hash)
        )

        result = cursor.fetchone()
        cursor.close()
        connection.close()

        if result:
            return {
                'id': result[0],
                'username': result[1],
                'nombre_completo': result[2],
                'rol': result[3]
            }
        else:
            return None

    except Exception as e:
        log(f"Error en verificar_credenciales_fallback: {e}")
        return None

def crear_tabla_usuarios_fallback():
    """Función fallback para crear tabla usuarios"""
    return True

try:
    if getattr(sys, 'frozen', False):
        verificar_credenciales = verificar_credenciales_fallback
        crear_tabla_usuarios = crear_tabla_usuarios_fallback
except ImportError:
    log("Usando funciones fallback para manejo de base de datos")
    verificar_credenciales = verificar_credenciales_fallback
    crear_tabla_usuarios = crear_tabla_usuarios_fallback

def verificar_mysql_y_continuar(self):
    """Verifica la conexión MySQL y decide qué mostrar - VERSIÓN CORREGIDA"""
    def verificar_conexion():
        try:
            log("Iniciando verificación de conexión MySQL...")

            debug_paths()

            config_file = get_config_path("mysql_config.ini")
            log(f"Buscando archivo de configuración en: {config_file}")

            if not os.path.exists(config_file):
                error_msg = f"Archivo de configuración no encontrado: {config_file}"
                self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                return

            config = configparser.ConfigParser()
            try:
                config.read(config_file, encoding='utf-8')
                log("✅ Archivo de configuración leído correctamente")
            except Exception as e:
                error_msg = f"Error leyendo archivo de configuración: {str(e)}"
                self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                return

            if 'MySQL' not in config:
                error_msg = "Configuración MySQL no válida en archivo mysql_config.ini"
                self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                return

            mysql_config = config['MySQL']

            # SIN valores por defecto hardcodeados
            host = mysql_config.get('host')
            port_str = mysql_config.get('port')
            user = mysql_config.get('admin_user')
            password = mysql_config.get('admin_pass')

            # Validar que existan
            if not host or not port_str or not user:
                error_msg = "Configuración MySQL incompleta (falta host, port o user)"
                self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                return

            try:
                port = int(port_str)
            except ValueError:
                error_msg = f"Puerto inválido: {port_str}"
                self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                return

            log(f"Configuración cargada: {user}@{host}:{port}")

            if not password:
                error_msg = "Contraseña de MySQL no configurada"
                self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                return

            log(f"Probando conexión a {user}@{host}:{port}")

            if not verificar_conectividad_red(host, port):
                error_msg = f"No se puede acceder al puerto {port} en {host}. Verifique que MySQL esté ejecutándose."
                self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                return

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
                log(f"✅ Conexión MySQL exitosa - Versión: {version}")
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

                self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                return

            try:
                crear_tabla_usuarios()
                log("✅ Tablas verificadas/creadas")
            except Exception as e:
                log(f"⚠️ Error creando tablas: {e} - continuando...")

            log("✅ Conexión MySQL exitosa, mostrando login...")
            self.root.after(0, self.mostrar_login)

        except Exception as e:
            error_msg = f"Error inesperado en verificación: {str(e)}"
            log(error_msg)
            log_exc()
            self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))

    self.mostrar_mensaje_carga()
    self.root.after(500, lambda: threading.Thread(target=verificar_conexion, daemon=True).start())

def ejecutar_bat_con_elevacion(ruta_bat):
    ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", ruta_bat, None, None, 1)
    if ret <= 32:
        log(f"Error al ejecutar el script con elevación, código: {ret}")
        return False
    return True

def es_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:  # noqa: E722
        return False

def ejecutar_como_admin():
    if es_admin():
        return True

    executable = sys.executable
    params = ' '.join([f'"{arg}"' for arg in sys.argv])

    ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, params, None, 1)

    if ret <= 32:
        log(f"Error al pedir elevación, código: {ret}")
        return False
    else:
        return True

def debug_mysql_connection():
    """Función de debug: neutralizada para modo silencioso salvo SILENT=False"""
    if SILENT:
        return False
    try:
        log("=== DEBUG: Probando conexión MySQL ===")

        import mysql.connector

        config = configparser.ConfigParser()
        config_file = get_config_path("mysql_config.ini")
        log(f"Buscando archivo de configuración en: {config_file}")

        if not os.path.exists(config_file):
            log(f"❌ No existe archivo de configuración MySQL en: {config_file}")

            if getattr(sys, 'frozen', False):
                log("⚠️ Es ejecutable, intentando crear configuración básica...")
                try:
                    temp_login = type('TempLogin', (), {})()
                    temp_login.crear_config_basico = lambda self, path: crear_config_basico(temp_login, path)
                    temp_login.crear_config_basico(config_file)

                    if os.path.exists(config_file):
                        log("✅ Configuración básica creada")
                    else:
                        return False
                except Exception as e:
                    log(f"❌ Error creando configuración: {e}")
                    return False
            else:
                return False

        try:
            config.read(config_file, encoding='utf-8')
        except Exception as e:
            log(f"❌ Error leyendo configuración: {e}")
            return False

        if 'MySQL' in config:
            mysql_config = config['MySQL']
            
            # ✅ SIN valores por defecto hardcodeados
            host = mysql_config.get('host')
            port_str = mysql_config.get('port')
            user = mysql_config.get('admin_user')
            password = mysql_config.get('admin_pass')
            
            # Validar que existan
            if not host or not port_str or not user:
                log("❌ Configuración MySQL incompleta en archivo")
                return False
            
            try:
                port = int(port_str)
            except ValueError:
                log(f"❌ Puerto inválido: {port_str}")
                return False

            if not password:
                log("❌ Contraseña no configurada en archivo de configuración")
                return False

            log(f"Intentando conectar a: {user}@{host}:{port}")

            if not verificar_conectividad_red(host, port):
                log("❌ Sin conectividad de red al servidor MySQL")
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
            log(f"✅ Conexión exitosa - MySQL {version}")
            cursor.close()
            connection.close()

            return True
        else:
            log("❌ No hay configuración MySQL en el archivo")

    except mysql.connector.Error as e:
        log(f"❌ Error MySQL: {e.errno} - {e.msg}")
        return False
    except Exception as e:
        log(f"❌ Error en debug de conexión: {e}")
        log_exc()
        return False

    return False

def crear_config_basico(self, config_file):
    """Solicita al usuario la configuración en lugar de usar valores hardcodeados"""
    try:
        from tkinter import simpledialog
        
        # Solicitar datos al usuario
        host = simpledialog.askstring(
            "Configuración MySQL",
            "Ingrese el hostname o IP del servidor MySQL:",
            initialvalue="localhost"
        )
        
        if not host:
            raise Exception("Debe ingresar un hostname")
        
        port = simpledialog.askinteger(
            "Configuración MySQL",
            "Ingrese el puerto MySQL:",
            initialvalue=3306,
            minvalue=1,
            maxvalue=65535
        )
        
        user = simpledialog.askstring(
            "Configuración MySQL",
            "Ingrese el usuario MySQL:",
            initialvalue="root"
        )
        
        if not user:
            raise Exception("Debe ingresar un usuario")
        
        password = simpledialog.askstring(
            "Configuración MySQL",
            "Ingrese la contraseña MySQL:",
            show='*'
        )
        
        if password is None:
            raise Exception("Debe ingresar una contraseña")
        
        # Crear configuración con datos del usuario
        config = configparser.ConfigParser()
        config['MySQL'] = {
            'host': host,
            'port': str(port or 3306),
            'admin_user': user,
            'admin_pass': password,
            'bind_address': '0.0.0.0',
            'max_connections': '100',
            'timeout': '28800',
            'database': 'insumos'
        }

        config_dir = os.path.dirname(config_file)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)

        with open(config_file, 'w', encoding='utf-8') as f:
            config.write(f)

        log(f"✅ Archivo de configuración creado en: {config_file}")

    except Exception as e:
        log(f"❌ Error creando configuración: {e}")
        raise

def verificar_conectividad_red(host, port):
    """Verifica si el puerto MySQL está accesible - NUEVA FUNCIÓN"""
    try:
        ip = socket.gethostbyname(host)
        log(f"DNS resuelto: {host} -> {ip}")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((ip, port))
        sock.close()

        if result == 0:
            log(f"✅ Puerto {port} accesible en {host}")
            return True
        else:
            log(f"❌ Puerto {port} NO accesible en {host}")
            if not SILENT:
                log("💡 Posibles causas:")
                log("   - MySQL no está ejecutándose")
                log("   - Firewall bloqueando el puerto")
                log("   - bind-address configurado incorrectamente")
            return False

    except socket.gaierror:
        log(f"❌ Error DNS: No se pudo resolver {host}")
        return False
    except Exception as e:
        log(f"❌ Error de conectividad: {e}")
        return False

class ConfiguracionMySQL:
    def __init__(self, parent):
        self.parent = parent
        self.config_file = get_config_path("mysql_config.ini")
        self.max_connections_var = tk.StringVar(value="100")
        self.timeout_var = tk.StringVar(value="28800")

        self.config_window = tk.Toplevel(parent)
        self.config_window.title("Configuración de Conexión MySQL")
        self.config_window.geometry("500x400")
        self.config_window.configure(bg='#f8f9fa')
        self.config_window.resizable(False, False)
        self.config_window.transient(parent)
        self.config_window.grab_set()

        # Iconos del Toplevel (helper unificado)
        apply_window_icons(self.config_window, CFG_ICO, CFG_PNG)

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

            ruta_bat = get_bat_path()
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
        screen_width = self.config_window.winfo_screenwidth()
        screen_height = self.config_window.winfo_screenheight()
        x = (screen_width - 500) // 2
        y = (screen_height - 400) // 2
        self.config_window.geometry(f"500x400+{x}+{y}")

    def setup_ui(self):
        main_frame = tk.Frame(self.config_window, bg='#f8f9fa')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        title_label = tk.Label(
            main_frame,
            text="Configuración de MySQL",
            font=('Segoe UI', 16, 'bold'),
            bg='#f8f9fa',
            fg='#2c3e50'
        )
        title_label.pack(pady=(0, 10))

        subtitle_label = tk.Label(
            main_frame,
            text="Configure la conexión al servidor MySQL",
            font=('Segoe UI', 10),
            bg='#f8f9fa',
            fg='#7f8c8d'
        )
        subtitle_label.pack(pady=(0, 20))

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

        tk.Label(config_frame, text="Host/IP del servidor:", font=('Segoe UI', 10),
            bg='#ffffff', fg='#2c3e50').grid(row=0, column=0, sticky="w", pady=5)
        
        self.host_var = tk.StringVar(value="")
        self.host_entry = tk.Entry(config_frame, textvariable=self.host_var, width=25,
                                font=('Segoe UI', 10))
        self.host_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=(10, 0))

        tk.Label(config_frame, text="Puerto:", font=('Segoe UI', 10),
                bg='#ffffff', fg='#2c3e50').grid(row=1, column=0, sticky="w", pady=5)
        self.puerto_var = tk.StringVar(value="3306")  # Este puede quedarse
        self.puerto_entry = tk.Entry(config_frame, textvariable=self.puerto_var, width=25,
                                    font=('Segoe UI', 10))
        self.puerto_entry.grid(row=1, column=1, sticky="ew", pady=5, padx=(10, 0))

        tk.Label(config_frame, text="Usuario Admin:", font=('Segoe UI', 10),
                bg='#ffffff', fg='#2c3e50').grid(row=2, column=0, sticky="w", pady=5)
        self.admin_user_var = tk.StringVar(value="root")  # Este puede quedarse
        self.admin_user_entry = tk.Entry(config_frame, textvariable=self.admin_user_var, width=25,
                                        font=('Segoe UI', 10))
        self.admin_user_entry.grid(row=2, column=1, sticky="ew", pady=5, padx=(10, 0))

        tk.Label(config_frame, text="Contraseña Admin:", font=('Segoe UI', 10),
                bg='#ffffff', fg='#2c3e50').grid(row=3, column=0, sticky="w", pady=5)
       
        self.admin_pass_var = tk.StringVar(value="")
        self.admin_pass_entry = tk.Entry(config_frame, textvariable=self.admin_pass_var,
                                        show="*", width=25, font=('Segoe UI', 10))
        self.admin_pass_entry.grid(row=3, column=1, sticky="ew", pady=5, padx=(10, 0))

        config_frame.grid_columnconfigure(1, weight=1)

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

        btn_frame = tk.Frame(main_frame, bg='#f8f9fa')
        btn_frame.pack(fill='x')

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

        self.add_button_hover_effects()
        self.host_entry.focus()

    def add_button_hover_effects(self):
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
        self.test_btn.config(state='disabled')
        self.status_label.config(text="Probando conexión...", fg='#f39c12')

        def test_connection():
            try:
                host = self.host_var.get().strip()
                port = int(self.puerto_var.get().strip())
                user = self.admin_user_var.get().strip()
                password = self.admin_pass_var.get()
                
                # ✅ Validar que no estén vacíos
                if not host:
                    self.config_window.after(0, lambda: self.connection_error("Debe ingresar el host/IP del servidor"))
                    return
                
                if not user:
                    self.config_window.after(0, lambda: self.connection_error("Debe ingresar el usuario"))
                    return

                if not password:
                    self.config_window.after(0, lambda: self.connection_error("Debe ingresar la contraseña"))
                    return

                log(f"Probando conexión a {user}@{host}:{port}")

                if not verificar_conectividad_red(host, port):
                    self.config_window.after(0, lambda: self.connection_error("Puerto MySQL no accesible"))
                    return

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
                if e.errno == 1045:
                    error_msg = "Usuario o contraseña incorrectos"
                elif e.errno == 2003:
                    error_msg = "No se puede conectar al servidor MySQL. Verifique que esté ejecutándose."
                elif e.errno == 1130:
                    error_msg = "Host no autorizado para conectar"

                log(f"❌ Error MySQL: {error_msg}")
                self.config_window.after(0, lambda: self.connection_error(error_msg))

            except Exception as e:
                error_msg = f"Error inesperado: {str(e)}"
                log(f"❌ {error_msg}")
                self.config_window.after(0, lambda: self.connection_error(error_msg))
            finally:
                self.config_window.after(0, lambda: self.test_btn.config(state='normal'))

        threading.Thread(target=test_connection, daemon=True).start()

    def connection_success(self, version):
        self.status_label.config(
            text=f"✅ Conexión exitosa - MySQL {version}",
            fg='#27ae60'
        )
        self.save_btn.config(state='normal')
        self.test_btn.config(state='normal')

    def connection_error(self, error_msg):
        self.status_label.config(
            text=f"❌ Error: {error_msg}",
            fg='#e74c3c'
        )
        self.save_btn.config(state='disabled')
        self.test_btn.config(state='normal')

    def guardar_y_continuar(self):
        self.guardar_configuracion()
        self.aplicar_configuracion_red()

        # ✅ SIN reemplazo automático
        host = self.host_var.get().strip()
        
        if not host:
            messagebox.showerror("Error", "Debe ingresar un host")
            return

        self.result = {
            'host': host,
            'port': int(self.puerto_var.get().strip()),
            'user': self.admin_user_var.get().strip(),
            'password': self.admin_pass_var.get()
        }
        self.config_window.destroy()

    def cancelar(self):
        self.result = None
        self.config_window.destroy()

    def guardar_configuracion(self):
        config = configparser.ConfigParser()

        # SIN reemplazo automático
        host = self.host_var.get().strip()
        
        if not host:
            messagebox.showerror("Error", "Debe ingresar un host")
            return

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
            config_dir = os.path.dirname(self.config_file)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)

            with open(self.config_file, 'w') as f:
                config.write(f)
            log(f"Configuración guardada en: {os.path.abspath(self.config_file)}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la configuración: {str(e)}")

    def cargar_configuracion(self):
        if os.path.exists(self.config_file):
            try:
                config = configparser.ConfigParser()
                config.read(self.config_file)

                if 'MySQL' in config:
                    mysql_config = config['MySQL']
                    # ✅ SIN valores por defecto hardcodeados
                    self.host_var.set(mysql_config.get('host', ''))
                    self.puerto_var.set(mysql_config.get('port', '3306'))
                    self.admin_user_var.set(mysql_config.get('admin_user', 'root'))
                    self.admin_pass_var.set(mysql_config.get('admin_pass', ''))
                    log("Configuración cargada desde archivo")

            except Exception as e:
                log(f"Error cargando configuración: {e}")

class LoginWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Módulo de Productos Afines")
        self.root.geometry("800x450")
        self.root.configure(bg='#f8f9fa')
        self.root.resizable(False, False)

        # Centrar
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 800) // 2
        y = (screen_height - 450) // 2
        self.root.geometry(f"800x450+{x}+{y}")

        # Iconos de la ventana principal (helper unificado)
        apply_window_icons(self.root, APP_ICO, APP_PNG)

        self.load_icons()

        self.show_password = False
        self.loading_active = False
        self.animation_job = None

        self.verificar_mysql_y_continuar()

    def verificar_mysql_y_continuar(self):
        """Verifica la conexión MySQL y decide qué mostrar - MEJORADA PARA EJECUTABLE"""
        def verificar_conexion():
            try:
                log("Iniciando verificación de conexión MySQL...")

                debug_paths()

                config_file = get_config_path("mysql_config.ini")
                log(f"Buscando archivo de configuración en: {config_file}")

                if not os.path.exists(config_file):
                    if getattr(sys, 'frozen', False):
                        log("⚠️ Archivo config no encontrado en ejecutable, intentando crear uno básico...")
                        try:
                            self.crear_config_basico(config_file)
                            if os.path.exists(config_file):
                                log("✅ Archivo de configuración básico creado")
                            else:
                                error_msg = f"No se pudo crear archivo de configuración en: {config_file}"
                                self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                                return
                        except Exception as e:
                            error_msg = f"Error creando configuración básica: {str(e)}"
                            self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                            return
                    else:
                        error_msg = f"Archivo de configuración MySQL no encontrado en: {config_file}"
                        self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                        return

                config = configparser.ConfigParser()
                try:
                    config.read(config_file, encoding='utf-8')
                    log("✅ Archivo de configuración leído correctamente")
                except Exception as e:
                    error_msg = f"Error leyendo archivo de configuración: {str(e)}"
                    self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                    return

                if 'MySQL' not in config:
                    error_msg = "Configuración MySQL no válida en archivo mysql_config.ini"
                    self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                    return

                mysql_config = config['MySQL']
                
                # ✅ SIN valores por defecto hardcodeados
                host = mysql_config.get('host')
                port_str = mysql_config.get('port')
                user = mysql_config.get('admin_user')
                password = mysql_config.get('admin_pass')
                
                # Validar que existan los valores requeridos
                if not host or not port_str or not user:
                    error_msg = "Configuración MySQL incompleta (falta host, port o user)"
                    self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                    return
                
                try:
                    port = int(port_str)
                except ValueError:
                    error_msg = f"Puerto inválido en configuración: {port_str}"
                    self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                    return

                log(f"Configuración cargada: {user}@{host}:{port}")

                if not password:
                    error_msg = "Contraseña de MySQL no configurada"
                    self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                    return

                log(f"Probando conexión a {user}@{host}:{port}")

                if not verificar_conectividad_red(host, port):
                    error_msg = f"No se puede acceder al puerto {port} en {host}. Verifique que MySQL esté ejecutándose."
                    self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                    return

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
                    log(f"✅ Conexión MySQL exitosa - Versión: {version}")
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

                    self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                    return

                try:
                    if not getattr(sys, 'frozen', False):
                        from src.database.db_manager import crear_tabla_usuarios
                        crear_tabla_usuarios()
                        log("✅ Tablas verificadas/creadas")
                except ImportError:
                    log("⚠️ No se pudo importar crear_tabla_usuarios - continuando...")
                except Exception as e:
                    log(f"⚠️ Error creando tablas: {e} - continuando...")

                log("✅ Conexión MySQL exitosa, mostrando login...")
                self.root.after(0, self.mostrar_login)

            except Exception as e:
                error_msg = f"Error inesperado en verificación: {str(e)}"
                log(error_msg)
                log_exc()
                self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))

        self.mostrar_mensaje_carga()
        self.root.after(500, lambda: threading.Thread(target=verificar_conexion, daemon=True).start())

    def crear_config_basico(self, config_file):
        """Solicita al usuario la configuración en lugar de usar valores hardcodeados"""
        try:
            from tkinter import simpledialog
            
            # Solicitar datos al usuario
            host = simpledialog.askstring(
                "Configuración MySQL",
                "Ingrese el hostname o IP del servidor MySQL:",
                initialvalue="localhost"
            )
            
            if not host:
                raise Exception("Debe ingresar un hostname")
            
            port = simpledialog.askinteger(
                "Configuración MySQL",
                "Ingrese el puerto MySQL:",
                initialvalue=3306,
                minvalue=1,
                maxvalue=65535
            )
            
            user = simpledialog.askstring(
                "Configuración MySQL",
                "Ingrese el usuario MySQL:",
                initialvalue="root"
            )
            
            if not user:
                raise Exception("Debe ingresar un usuario")
            
            password = simpledialog.askstring(
                "Configuración MySQL",
                "Ingrese la contraseña MySQL:",
                show='*'
            )
            
            if password is None:
                raise Exception("Debe ingresar una contraseña")
            
            # Crear configuración con datos del usuario
            config = configparser.ConfigParser()
            config['MySQL'] = {
                'host': host,
                'port': str(port or 3306),
                'admin_user': user,
                'admin_pass': password,
                'bind_address': '0.0.0.0',
                'max_connections': '100',
                'timeout': '28800',
                'database': 'insumos'
            }

            config_dir = os.path.dirname(config_file)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)

            with open(config_file, 'w', encoding='utf-8') as f:
                config.write(f)

            log(f"✅ Archivo de configuración creado en: {config_file}")

        except Exception as e:
            log(f"❌ Error creando configuración: {e}")
            raise

    def mostrar_mensaje_carga(self):
        """Muestra un mensaje de carga mientras verifica la conexión"""
        log("Mostrando mensaje de carga...")

        self.loading_active = False
        if self.animation_job:
            try:
                self.root.after_cancel(self.animation_job)
            except:  # noqa: E722
                pass

        self.loading_active = True

        for widget in self.root.winfo_children():
            widget.destroy()

        loading_frame = tk.Frame(self.root, bg='#f8f9fa')
        loading_frame.pack(fill='both', expand=True)

        center_frame = tk.Frame(loading_frame, bg='#f8f9fa')
        center_frame.place(relx=0.5, rely=0.5, anchor='center')

        if hasattr(self, 'icons') and 'medical_120' in self.icons:
            icon_label = tk.Label(center_frame, image=self.icons['medical_120'], bg='#f8f9fa')
            icon_label.pack(pady=(0, 20))

        tk.Label(
            center_frame,
            text="Verificando conexión MySQL...",
            font=('Segoe UI', 14, 'bold'),
            bg='#f8f9fa',
            fg='#2c3e50'
        ).pack(pady=(0, 10))

        tk.Label(
            center_frame,
            text="Por favor espere un momento",
            font=('Segoe UI', 10),
            bg='#f8f9fa',
            fg='#7f8c8d'
        ).pack()

        progress_frame = tk.Frame(center_frame, bg='#f8f9fa')
        progress_frame.pack(pady=(20, 0))

        canvas = tk.Canvas(progress_frame, width=200, height=4, bg='#f8f9fa', highlightthickness=0)
        canvas.pack()

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

                except Exception:
                    self.loading_active = False

            update_progress()

        animate_progress()
        self.root.update()

    def mostrar_configuracion_mysql(self, error_msg):
        """Muestra la ventana de configuración MySQL"""
        log(f"Mostrando configuración MySQL debido a error: {error_msg}")

        for widget in self.root.winfo_children():
            widget.destroy()

        config_frame = tk.Frame(self.root, bg='#f8f9fa')
        config_frame.pack(fill='both', expand=True, padx=20, pady=20)

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
            text="No se pudo conectar a la base de datos:",
            font=('Segoe UI', 10),
            bg='#f8f9fa',
            fg='#7f8c8d'
        ).pack(pady=(5, 0))

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

        btn_frame = tk.Frame(config_frame, bg='#f8f9fa')
        btn_frame.pack(fill='x', pady=10)

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
        log("Abriendo configuración MySQL...")

        try:
            config_mysql = ConfiguracionMySQL(self.root)
            self.root.wait_window(config_mysql.config_window)

            if hasattr(config_mysql, 'result') and config_mysql.result:
                log("Configuración guardada, reintentando conexión...")
                self.reintentar_conexion()
            else:
                log("Configuración cancelada")

        except Exception as e:
            log(f"Error en configuración MySQL: {e}")
            messagebox.showerror("Error", f"Error al abrir configuración: {str(e)}")

    def reintentar_conexion(self):
        """Reintenta la verificación de conexión"""
        log("Reintentando conexión...")
        self.verificar_mysql_y_continuar()

    def mostrar_login(self):
        """Muestra la pantalla de login"""
        self.loading_active = False
        if hasattr(self, 'animation_job') and self.animation_job:
            try:
                self.root.after_cancel(self.animation_job)
            except:  # noqa: E722
                pass

        for widget in self.root.winfo_children():
            widget.destroy()

        self.setup_ui()

    def load_icons(self):
        """Carga los iconos para la ventana de login"""
        self.icons = {}
        # Usamos utils/icons (coherente con resource_path y empaquetado)
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
                    self.icons[f'{key}_20'] = ImageTk.PhotoImage(image.resize((20, 20), Image.Resampling.LANCZOS))
                    self.icons[f'{key}_24'] = ImageTk.PhotoImage(image.resize((24, 24), Image.Resampling.LANCZOS))
                    self.icons[f'{key}_18'] = ImageTk.PhotoImage(image.resize((18, 18), Image.Resampling.LANCZOS))
                    self.icons[f'{key}_120'] = ImageTk.PhotoImage(image.resize((120, 120), Image.Resampling.LANCZOS))
                else:
                    log(f"Icono no encontrado: {icon_full_path}")
            except Exception as e:
                log(f"Error cargando icono {filename}: {e}")

    def setup_ui(self):
        main_container = tk.Frame(self.root, bg='#f8f9fa')
        main_container.pack(fill='both', expand=True)

        left_panel = tk.Frame(main_container, bg='#2c3e50', width=400)
        left_panel.pack(side='left', fill='y')
        left_panel.pack_propagate(False)

        left_content = tk.Frame(left_panel, bg='#2c3e50')
        left_content.place(relx=0.5, rely=0.5, anchor='center')

        if hasattr(self, 'icons') and 'medical_120' in self.icons:
            icon_label = tk.Label(left_content, image=self.icons['medical_120'], bg='#2c3e50')
            icon_label.pack(pady=(0, 15))

        title_label = tk.Label(
            left_content,
            text="MÓDULO DE PRODUCTOS\nAFINES",
            font=('Segoe UI', 18, 'bold'),
            bg='#2c3e50',
            fg='#ffffff',
            justify='center'
        )
        title_label.pack(pady=(0, 8))

        subtitle_label = tk.Label(
            left_content,
            text="ÁREA NOR ORIENTE",
            font=('Segoe UI', 12),
            bg='#2c3e50',
            fg='#bdc3c7'
        )
        subtitle_label.pack(pady=(0, 20))

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

        right_panel = tk.Frame(main_container, bg='#ffffff', width=350)
        right_panel.pack(side='right', fill='both', expand=True)
        right_panel.pack_propagate(False)

        form_container = tk.Frame(right_panel, bg='#ffffff')
        form_container.place(relx=0.5, rely=0.5, anchor='center')

        form_title = tk.Label(
            form_container,
            text="Iniciar Sesión",
            font=('Segoe UI', 20, 'bold'),
            bg='#ffffff',
            fg='#2c3e50'
        )
        form_title.pack(pady=(0, 30))

        self.create_input_field(form_container, "Usuario", "user", False)
        self.create_input_field(form_container, "Contraseña", "password", True)

        login_btn_frame = tk.Frame(form_container, bg='#ffffff')
        login_btn_frame.pack(pady=(25, 15), fill='x')

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

        def on_enter(e):
            login_btn.configure(bg='#2980b9')
        def on_leave(e):
            login_btn.configure(bg='#3498db')

        login_btn.bind('<Enter>', on_enter)
        login_btn.bind('<Leave>', on_leave)

        help_label = tk.Label(
            form_container,
            text="¿Problemas para acceder? Contacte al administrador",
            font=('Segoe UI', 8),
            bg='#ffffff',
            fg='#7f8c8d'
        )
        help_label.pack(pady=(15, 0))

        self.root.bind('<Return>', lambda e: self.login())

        if hasattr(self, 'username_entry'):
            self.username_entry.focus()

    def create_input_field(self, parent, label_text, icon_key, is_password):
        field_frame = tk.Frame(parent, bg='#ffffff')
        field_frame.pack(fill='x', pady=(0, 15))

        label = tk.Label(
            field_frame,
            text=label_text,
            font=('Segoe UI', 10, 'bold'),
            bg='#ffffff',
            fg='#34495e'
        )
        label.pack(anchor='w', pady=(0, 6))

        input_frame = tk.Frame(field_frame, bg='#ecf0f1', relief='solid', bd=1)
        input_frame.pack(fill='x')

        if hasattr(self, 'icons') and f'{icon_key}_24' in self.icons:
            icon_label = tk.Label(
                input_frame,
                image=self.icons[f'{icon_key}_24'],
                bg='#ecf0f1'
            )
            icon_label.pack(side='left', padx=(10, 6), pady=10)

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
                config_file = get_config_path("mysql_config.ini")

                config = configparser.ConfigParser()
                config.read(config_file)

                if 'MySQL' in config:
                    mysql_config = config['MySQL']
                    # SIN valores por defecto
                    host = mysql_config.get('host')
                    port_str = mysql_config.get('port')
                    
                    if not host or not port_str:
                        self.root.after(0, lambda: messagebox.showerror("Error de Configuración",
                            "Configuración MySQL incompleta"))
                        return
                    
                    try:
                        port = int(port_str)
                    except ValueError:
                        self.root.after(0, lambda: messagebox.showerror("Error de Configuración",
                            f"Puerto inválido: {port_str}"))
                        return

                    if not verificar_conectividad_red(host, port):
                        self.root.after(0, lambda: messagebox.showerror("Error de Conexión",
                            "No se puede conectar al servidor MySQL"))
                        return

                try:
                    from src.database.db_manager import verificar_credenciales
                    usuario = verificar_credenciales(username, password)
                except ImportError:
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
    # Inicio silencioso: no imprimir encabezados; solo ejecutar GUI
    try:
        login = LoginWindow()
        login.run()
    except Exception as e:
        # Mostrar dialogo crítico
        messagebox.showerror("Error fatal", f"Ocurrió un error iniciando la aplicación:\n{str(e)}")