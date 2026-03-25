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
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return current_dir

def get_config_path(filename="mysql_config.ini"):
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        return os.path.join(exe_dir, filename)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, filename)

def get_bat_path():
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        return os.path.join(exe_dir, "modificar_mysql.bat")
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, "modificar_mysql.bat")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(base_path, relative_path)

APP_ICO = os.path.join('utils', 'icons', 'app.ico')
APP_PNG = os.path.join('utils', 'icons', 'app.png')
CFG_ICO = os.path.join('utils', 'icons', 'app1.ico')
CFG_PNG = os.path.join('utils', 'icons', 'app1.png')

def apply_window_icons(win, ico_rel, png_rel):
    try:
        ico_path = resource_path(ico_rel)
        if os.path.exists(ico_path):
            win.iconbitmap(ico_path)
    except Exception as e:
        log(f"iconbitmap fallo: {e}")
    try:
        png_path = resource_path(png_rel)
        if os.path.exists(png_path):
            img16 = ImageTk.PhotoImage(Image.open(png_path).resize((16, 16), Image.Resampling.LANCZOS))
            img32 = ImageTk.PhotoImage(Image.open(png_path).resize((32, 32), Image.Resampling.LANCZOS))
            if not hasattr(win, '_icon_imgs'):
                win._icon_imgs = []
            win._icon_imgs.extend([img16, img32])
            win.wm_iconphoto(True, img16, img32)
    except Exception as e:
        log(f"iconphoto fallo: {e}")

def debug_paths():
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

        config_path = get_config_path("mysql_config.ini")
        bat_path = get_bat_path()

        log(f"   Ruta config: {config_path}")
        log(f"   ¿Existe config?: {os.path.exists(config_path) if config_path else False}")
        log(f"   Ruta bat: {bat_path}")
        log(f"   ¿Existe bat?: {os.path.exists(bat_path) if bat_path else False}")

    except Exception as e:
        log(f"❌ Error en debug_paths: {e}")
        log_exc()

def test_network_connectivity(host, port, timeout=10):
    try:
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
    try:
        log("   🔄 Intentando conexión MySQL...")
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            connection_timeout=10,
            autocommit=True,
            auth_plugin='mysql_native_password',
                use_pure=True
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
        return False
    except Exception as e:
        log(f"   ❌ Error inesperado: {e}")
        return False

def check_mysql_dependencies():
    try:
        log(f"   ✅ mysql.connector disponible (versión: {mysql.connector.__version__})")
    except ImportError as e:
        log(f"   ❌ mysql.connector NO disponible: {e}")

def check_windows_firewall():
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
            else:
                log("   ✅ Firewall de Windows está INACTIVO")
    except Exception as e:
        log(f"   ⚠️ Error verificando firewall: {e}")

def check_network_config():
    try:
        import platform
        import subprocess
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        log(f"   🖥️ Nombre del equipo: {hostname}")
        log(f"   🌐 IP local: {local_ip}")
    except Exception as e:
        log(f"   ⚠️ Error verificando configuración de red: {e}")

# Manejo de PATH de proyecto en desarrollo
if not getattr(sys, 'frozen', False):
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sys.path.append(project_root)
    except Exception:
        pass

# ── LOG DE ARRANQUE ─────────────────────────────────────────────────────────
def _get_startup_log_path():
    """Ruta del log siempre junto al .exe (o junto al script en desarrollo)."""
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "insumos_startup.log")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "insumos_startup.log")

def _startup_log(msg):
    """Escribe en consola Y en archivo SIEMPRE (sin depender de LOG_PATH global)."""
    import datetime
    linea = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}"
    try:
        print(linea, flush=True)
    except Exception:
        pass
    try:
        with open(_get_startup_log_path(), "a", encoding="utf-8") as f:
            f.write(linea + "\n")
    except Exception:
        pass

def _run_startup_diagnostics():
    """Diagnóstico completo al iniciar la app. Resultado siempre en insumos_startup.log."""
    import datetime
    _startup_log("=" * 60)
    _startup_log(f"INICIO APP  v1.1  —  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    _startup_log("=" * 60)

    # ── Entorno ────────────────────────────────────────────────
    _startup_log(f"[ENV] frozen       : {getattr(sys, 'frozen', False)}")
    _startup_log(f"[ENV] Python       : {sys.version}")
    _startup_log(f"[ENV] executable   : {sys.executable}")
    _startup_log(f"[ENV] LOG_PATH     : {_get_startup_log_path()}")
    try:
        _startup_log(f"[ENV] cwd          : {os.getcwd()}")
    except Exception as e:
        _startup_log(f"[ENV] cwd ERROR    : {e}")

    # ── mysql_config.ini ──────────────────────────────────────
    config_path = get_config_path("mysql_config.ini")
    _startup_log(f"[CFG] ruta ini     : {config_path}")
    _startup_log(f"[CFG] ini existe   : {os.path.exists(config_path)}")
    if os.path.exists(config_path):
        try:
            import configparser as _cp
            cfg = _cp.ConfigParser()
            cfg.read(config_path, encoding="utf-8")
            if "MySQL" in cfg:
                _startup_log(f"[CFG] host         : {cfg['MySQL'].get('host','—')}")
                _startup_log(f"[CFG] port         : {cfg['MySQL'].get('port','—')}")
                _startup_log(f"[CFG] admin_user   : {cfg['MySQL'].get('admin_user','—')}")
                _startup_log(f"[CFG] admin_pass   : {'(ok)' if cfg['MySQL'].get('admin_pass') else '(vacío!)'}")
                _startup_log(f"[CFG] database     : {cfg['MySQL'].get('database','—')}")
            else:
                _startup_log("[CFG] ERROR: sección [MySQL] no encontrada en el ini")
        except Exception as e:
            _startup_log(f"[CFG] ERROR leyendo ini: {e}")
    else:
        _startup_log("[CFG] ERROR: archivo mysql_config.ini NO ENCONTRADO")

    # ── modificar_mysql.bat ───────────────────────────────────
    bat_path = get_bat_path()
    _startup_log(f"[BAT] ruta bat     : {bat_path}")
    _startup_log(f"[BAT] bat existe   : {os.path.exists(bat_path)}")

    # ── mysql.connector ───────────────────────────────────────
    try:
        import mysql.connector as _mc
        _startup_log(f"[PKG] mysql.connector: {_mc.__version__}")
    except ImportError as e:
        _startup_log(f"[PKG] mysql.connector FALTA: {e}")

    # ── Conectividad TCP ──────────────────────────────────────
    try:
        import configparser as _cp
        cfg = _cp.ConfigParser()
        cfg.read(config_path, encoding="utf-8")
        host = cfg['MySQL'].get('host', '').strip() if 'MySQL' in cfg else ''
        port = int(cfg['MySQL'].get('port', '3306')) if 'MySQL' in cfg else 3306
        if host:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                _startup_log(f"[NET] TCP {host}:{port} → ABIERTO ✓")
            else:
                _startup_log(f"[NET] TCP {host}:{port} → CERRADO/INACCESIBLE (código {result})")
        else:
            _startup_log("[NET] host vacío, no se probó TCP")
    except Exception as e:
        _startup_log(f"[NET] ERROR prueba TCP: {e}")

    # ── Conexión MySQL ────────────────────────────────────────
    try:
        import configparser as _cp
        import mysql.connector as _mc
        import traceback as _tb
        cfg = _cp.ConfigParser()
        cfg.read(config_path, encoding="utf-8")
        if 'MySQL' in cfg:
            _host = cfg['MySQL'].get('host','').strip()
            _port = int(cfg['MySQL'].get('port','3306'))
            _user = cfg['MySQL'].get('admin_user','').strip()
            _pass = cfg['MySQL'].get('admin_pass','')
            _db   = cfg['MySQL'].get('database','').strip()
            _startup_log(f"[SQL] Intentando conectar a {_user}@{_host}:{_port}/{_db} ...")
            try:
                conn = _mc.connect(
                    host=_host,
                    port=_port,
                    user=_user,
                    password=_pass,
                    connection_timeout=8,
                    auth_plugin='mysql_native_password',
                    use_pure=True
                )
                cur = conn.cursor()
                cur.execute("SELECT VERSION()")
                ver = cur.fetchone()[0]
                cur.close()
                conn.close()
                _startup_log(f"[SQL] Conexion OK — MySQL {ver}")
            except _mc.Error as e:
                _startup_log(f"[SQL] ERROR mysql.connector => errno={e.errno} msg={e.msg}")
                _startup_log(f"[SQL] TRACEBACK:\n{_tb.format_exc()}")
            except Exception as e:
                _startup_log(f"[SQL] ERROR inesperado => {type(e).__name__}: {e}")
                _startup_log(f"[SQL] TRACEBACK:\n{_tb.format_exc()}")
        else:
            _startup_log("[SQL] Sin seccion [MySQL] en el ini, conexion omitida")
    except Exception as e:
        import traceback as _tb
        _startup_log(f"[SQL] FALLO CRITICO: {type(e).__name__}: {e}")
        _startup_log(f"[SQL] TRACEBACK:\n{_tb.format_exc()}")

    _startup_log("=" * 60)

# Ejecutar diagnóstico siempre al arrancar
try:
    _run_startup_diagnostics()
except Exception:
    pass
# ── FIN LOG DE ARRANQUE ──────────────────────────────────────────────────────

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
        host = mysql_config.get('host')
        port = int(mysql_config.get('port', 3306))
        user = mysql_config.get('admin_user')
        password_db = mysql_config.get('admin_pass')
        database = mysql_config.get('database', 'insumos')

        if not host or not user or not password_db:
            log("❌ Configuración incompleta")
            return None

        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password_db,
            connection_timeout=10,
            auth_plugin='mysql_native_password',
                use_pure=True
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
    return True

try:
    if getattr(sys, 'frozen', False):
        verificar_credenciales = verificar_credenciales_fallback
        crear_tabla_usuarios = crear_tabla_usuarios_fallback
except ImportError:
    log("Usando funciones fallback para manejo de base de datos")
    verificar_credenciales = verificar_credenciales_fallback
    crear_tabla_usuarios = crear_tabla_usuarios_fallback

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
    if SILENT:
        return False
    try:
        log("=== DEBUG: Probando conexión MySQL ===")
        config = configparser.ConfigParser()
        config_file = get_config_path("mysql_config.ini")
        log(f"Buscando archivo de configuración en: {config_file}")

        if not os.path.exists(config_file):
            log(f"❌ No existe archivo de configuración MySQL en: {config_file}")
            return False

        try:
            config.read(config_file, encoding='utf-8')
        except Exception as e:
            log(f"❌ Error leyendo configuración: {e}")
            return False

        if 'MySQL' in config:
            mysql_config = config['MySQL']
            host = mysql_config.get('host')
            port_str = mysql_config.get('port')
            user = mysql_config.get('admin_user')
            password = mysql_config.get('admin_pass')

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
                autocommit=True,
                auth_plugin='mysql_native_password',
                use_pure=True
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
    try:
        from tkinter import simpledialog

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
            return False

    except socket.gaierror:
        log(f"❌ Error DNS: No se pudo resolver {host}")
        return False
    except Exception as e:
        log(f"❌ Error de conectividad: {e}")
        return False


# ─────────────────────────────────────────────
# Helper de log para archivo (siempre activo)
# ─────────────────────────────────────────────
def _get_log_path():
    """Siempre junto al .exe (o junto al script en desarrollo)."""
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "insumos_startup.log")
    else:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "insumos_startup.log")

LOG_PATH = _get_log_path()

def escribir_log_archivo(texto):
    """Escribe en error_main.log independientemente del modo SILENT."""
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            import datetime
            f.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {texto}\n")
    except Exception:
        pass


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

    def center_window(self):
        screen_width = self.config_window.winfo_screenwidth()
        screen_height = self.config_window.winfo_screenheight()
        x = (screen_width - 500) // 2
        y = (screen_height - 400) // 2
        self.config_window.geometry(f"500x400+{x}+{y}")

    def setup_ui(self):
        main_frame = tk.Frame(self.config_window, bg='#f8f9fa')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        tk.Label(main_frame, text="Configuración de MySQL",
                 font=('Segoe UI', 16, 'bold'), bg='#f8f9fa', fg='#2c3e50').pack(pady=(0, 10))

        tk.Label(main_frame, text="Configure la conexión al servidor MySQL",
                 font=('Segoe UI', 10), bg='#f8f9fa', fg='#7f8c8d').pack(pady=(0, 20))

        config_frame = tk.LabelFrame(
            main_frame, text="Datos de Conexión",
            font=('Segoe UI', 10, 'bold'), bg='#ffffff', fg='#2c3e50', padx=15, pady=15
        )
        config_frame.pack(fill='x', pady=(0, 20))

        tk.Label(config_frame, text="Host/IP del servidor:", font=('Segoe UI', 10),
                 bg='#ffffff', fg='#2c3e50').grid(row=0, column=0, sticky="w", pady=5)
        self.host_var = tk.StringVar(value="")
        self.host_entry = tk.Entry(config_frame, textvariable=self.host_var, width=25, font=('Segoe UI', 10))
        self.host_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=(10, 0))

        tk.Label(config_frame, text="Puerto:", font=('Segoe UI', 10),
                 bg='#ffffff', fg='#2c3e50').grid(row=1, column=0, sticky="w", pady=5)
        self.puerto_var = tk.StringVar(value="3306")
        self.puerto_entry = tk.Entry(config_frame, textvariable=self.puerto_var, width=25, font=('Segoe UI', 10))
        self.puerto_entry.grid(row=1, column=1, sticky="ew", pady=5, padx=(10, 0))

        tk.Label(config_frame, text="Usuario Admin:", font=('Segoe UI', 10),
                 bg='#ffffff', fg='#2c3e50').grid(row=2, column=0, sticky="w", pady=5)
        self.admin_user_var = tk.StringVar(value="root")
        self.admin_user_entry = tk.Entry(config_frame, textvariable=self.admin_user_var, width=25, font=('Segoe UI', 10))
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
            self.status_frame, text="Estado: No conectado",
            font=('Segoe UI', 10, 'bold'), bg='#f8f9fa', fg='#e74c3c'
        )
        self.status_label.pack()

        btn_frame = tk.Frame(main_frame, bg='#f8f9fa')
        btn_frame.pack(fill='x')

        self.test_btn = tk.Button(
            btn_frame, text="Probar Conexión",
            font=('Segoe UI', 10, 'bold'), bg='#f39c12', fg='white',
            relief='flat', padx=20, pady=8, cursor='hand2',
            command=self.probar_conexion_threaded
        )
        self.test_btn.pack(side='left', padx=(0, 10))

        self.save_btn = tk.Button(
            btn_frame, text="Guardar y Continuar",
            font=('Segoe UI', 10, 'bold'), bg='#27ae60', fg='white',
            relief='flat', padx=20, pady=8, cursor='hand2',
            command=self.guardar_y_continuar, state='disabled'
        )
        self.save_btn.pack(side='left', padx=(0, 10))

        cancel_btn = tk.Button(
            btn_frame, text="Cancelar",
            font=('Segoe UI', 10, 'bold'), bg='#e74c3c', fg='white',
            relief='flat', padx=20, pady=8, cursor='hand2',
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
                    autocommit=True,
                    auth_plugin='mysql_native_password',
                use_pure=True
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
        self.status_label.config(text=f"✅ Conexión exitosa - MySQL {version}", fg='#27ae60')
        self.save_btn.config(state='normal')
        self.test_btn.config(state='normal')

    def connection_error(self, error_msg):
        self.status_label.config(text=f"❌ Error: {error_msg}", fg='#e74c3c')
        self.save_btn.config(state='disabled')
        self.test_btn.config(state='normal')

    def guardar_y_continuar(self):
        self.guardar_configuracion()
        self.aplicar_configuracion_red()

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

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 800) // 2
        y = (screen_height - 450) // 2
        self.root.geometry(f"800x450+{x}+{y}")

        apply_window_icons(self.root, APP_ICO, APP_PNG)

        self.load_icons()

        self.show_password = False
        self.loading_active = False
        self.animation_job = None

        self.verificar_mysql_y_continuar()

    def verificar_mysql_y_continuar(self):
        def verificar_conexion():
            try:
                log("Iniciando verificación de conexión MySQL...")

                if not SILENT and not getattr(sys, 'frozen', False):
                    debug_paths()

                config_file = get_config_path("mysql_config.ini")
                log(f"Buscando archivo de configuración en: {config_file}")

                if not os.path.exists(config_file):
                    if getattr(sys, 'frozen', False):
                        try:
                            self.crear_config_basico(config_file)
                            if not os.path.exists(config_file):
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
                except Exception as e:
                    error_msg = f"Error leyendo archivo de configuración: {str(e)}"
                    self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                    return

                if 'MySQL' not in config:
                    error_msg = "Configuración MySQL no válida en archivo mysql_config.ini"
                    self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                    return

                mysql_config = config['MySQL']
                host = mysql_config.get('host')
                port_str = mysql_config.get('port')
                user = mysql_config.get('admin_user')
                password = mysql_config.get('admin_pass')

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

                if not password:
                    error_msg = "Contraseña de MySQL no configurada"
                    self.root.after(0, lambda: self.mostrar_configuracion_mysql(error_msg))
                    return

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
                        autocommit=True,
                        auth_plugin='mysql_native_password',
                use_pure=True
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
        try:
            from tkinter import simpledialog

            host = simpledialog.askstring(
                "Configuración MySQL", "Ingrese el hostname o IP del servidor MySQL:",
                initialvalue="localhost"
            )
            if not host:
                raise Exception("Debe ingresar un hostname")

            port = simpledialog.askinteger(
                "Configuración MySQL", "Ingrese el puerto MySQL:",
                initialvalue=3306, minvalue=1, maxvalue=65535
            )

            user = simpledialog.askstring(
                "Configuración MySQL", "Ingrese el usuario MySQL:",
                initialvalue="root"
            )
            if not user:
                raise Exception("Debe ingresar un usuario")

            password = simpledialog.askstring(
                "Configuración MySQL", "Ingrese la contraseña MySQL:", show='*'
            )
            if password is None:
                raise Exception("Debe ingresar una contraseña")

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

        tk.Label(center_frame, text="Verificando conexión MySQL...",
                 font=('Segoe UI', 14, 'bold'), bg='#f8f9fa', fg='#2c3e50').pack(pady=(0, 10))

        tk.Label(center_frame, text="Por favor espere un momento",
                 font=('Segoe UI', 10), bg='#f8f9fa', fg='#7f8c8d').pack()

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
        log(f"Mostrando configuración MySQL debido a error: {error_msg}")

        for widget in self.root.winfo_children():
            widget.destroy()

        config_frame = tk.Frame(self.root, bg='#f8f9fa')
        config_frame.pack(fill='both', expand=True, padx=20, pady=20)

        title_frame = tk.Frame(config_frame, bg='#f8f9fa')
        title_frame.pack(fill='x', pady=(0, 20))

        tk.Label(title_frame, text="⚠️ Error de Conexión MySQL",
                 font=('Segoe UI', 16, 'bold'), bg='#f8f9fa', fg='#e74c3c').pack()

        tk.Label(title_frame, text="No se pudo conectar a la base de datos:",
                 font=('Segoe UI', 10), bg='#f8f9fa', fg='#7f8c8d').pack(pady=(5, 0))

        error_frame = tk.Frame(config_frame, bg='#fff5f5', relief='solid', bd=1)
        error_frame.pack(fill='x', pady=(0, 20), padx=10)

        tk.Label(error_frame, text=error_msg, font=('Segoe UI', 9),
                 bg='#fff5f5', fg='#c53030', wraplength=700, justify='left').pack(padx=15, pady=10)

        btn_frame = tk.Frame(config_frame, bg='#f8f9fa')
        btn_frame.pack(fill='x', pady=10)

        config_btn = tk.Button(
            btn_frame, text="Configurar Conexión MySQL",
            font=('Segoe UI', 11, 'bold'), bg='#3498db', fg='white',
            relief='flat', padx=20, pady=10, cursor='hand2',
            command=self.abrir_configuracion_mysql
        )
        config_btn.pack(side='left', padx=(0, 10))

        retry_btn = tk.Button(
            btn_frame, text="Reintentar Conexión",
            font=('Segoe UI', 11, 'bold'), bg='#27ae60', fg='white',
            relief='flat', padx=20, pady=10, cursor='hand2',
            command=self.reintentar_conexion
        )
        retry_btn.pack(side='left', padx=(0, 10))

        exit_btn = tk.Button(
            btn_frame, text="Salir",
            font=('Segoe UI', 11, 'bold'), bg='#e74c3c', fg='white',
            relief='flat', padx=20, pady=10, cursor='hand2',
            command=self.root.quit
        )
        exit_btn.pack(side='right')

        def create_hover_effect(button, normal_color, hover_color):
            def on_enter(e): button.configure(bg=hover_color)
            def on_leave(e): button.configure(bg=normal_color)
            button.bind('<Enter>', on_enter)
            button.bind('<Leave>', on_leave)

        create_hover_effect(config_btn, '#3498db', '#2980b9')
        create_hover_effect(retry_btn, '#27ae60', '#2ecc71')
        create_hover_effect(exit_btn, '#e74c3c', '#c0392b')

    def abrir_configuracion_mysql(self):
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
        log("Reintentando conexión...")
        self.verificar_mysql_y_continuar()

    def mostrar_login(self):
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

        tk.Label(left_content, text="MÓDULO DE PRODUCTOS\nAFINES",
                 font=('Segoe UI', 18, 'bold'), bg='#2c3e50', fg='#ffffff', justify='center').pack(pady=(0, 8))

        tk.Label(left_content, text="ÁREA NOR ORIENTE",
                 font=('Segoe UI', 12), bg='#2c3e50', fg='#bdc3c7').pack(pady=(0, 20))

        info_text = """• Control de inventario
• Gestión de movimientos
• Reportes detallados
• Sistema seguro"""

        tk.Label(left_content, text=info_text, font=('Segoe UI', 9),
                 bg='#2c3e50', fg='#95a5a6', justify='left').pack()

        right_panel = tk.Frame(main_container, bg='#ffffff', width=350)
        right_panel.pack(side='right', fill='both', expand=True)
        right_panel.pack_propagate(False)

        form_container = tk.Frame(right_panel, bg='#ffffff')
        form_container.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(form_container, text="Iniciar Sesión",
                 font=('Segoe UI', 20, 'bold'), bg='#ffffff', fg='#2c3e50').pack(pady=(0, 30))

        self.create_input_field(form_container, "Usuario", "user", False)
        self.create_input_field(form_container, "Contraseña", "password", True)

        login_btn_frame = tk.Frame(form_container, bg='#ffffff')
        login_btn_frame.pack(pady=(25, 15), fill='x')

        if hasattr(self, 'icons') and 'login_20' in self.icons:
            login_btn = tk.Button(
                login_btn_frame, text="  INICIAR SESIÓN",
                font=('Segoe UI', 11, 'bold'), bg='#3498db', fg='white',
                relief='flat', padx=30, pady=10, cursor='hand2',
                image=self.icons['login_20'], compound='left',
                command=self.login
            )
        else:
            login_btn = tk.Button(
                login_btn_frame, text="INICIAR SESIÓN",
                font=('Segoe UI', 11, 'bold'), bg='#3498db', fg='white',
                relief='flat', padx=30, pady=10, cursor='hand2',
                command=self.login
            )

        login_btn.pack(fill='x')

        def on_enter(e): login_btn.configure(bg='#2980b9')
        def on_leave(e): login_btn.configure(bg='#3498db')
        login_btn.bind('<Enter>', on_enter)
        login_btn.bind('<Leave>', on_leave)

        tk.Label(form_container, text="¿Problemas para acceder? Contacte al administrador",
                 font=('Segoe UI', 8), bg='#ffffff', fg='#7f8c8d').pack(pady=(15, 0))

        self.root.bind('<Return>', lambda e: self.login())

        if hasattr(self, 'username_entry'):
            self.username_entry.focus()

    def create_input_field(self, parent, label_text, icon_key, is_password):
        field_frame = tk.Frame(parent, bg='#ffffff')
        field_frame.pack(fill='x', pady=(0, 15))

        tk.Label(field_frame, text=label_text, font=('Segoe UI', 10, 'bold'),
                 bg='#ffffff', fg='#34495e').pack(anchor='w', pady=(0, 6))

        input_frame = tk.Frame(field_frame, bg='#ecf0f1', relief='solid', bd=1)
        input_frame.pack(fill='x')

        if hasattr(self, 'icons') and f'{icon_key}_24' in self.icons:
            tk.Label(input_frame, image=self.icons[f'{icon_key}_24'],
                     bg='#ecf0f1').pack(side='left', padx=(10, 6), pady=10)

        if is_password:
            self.password_entry = tk.Entry(
                input_frame, font=('Segoe UI', 10),
                bg='#ecf0f1', fg='#2c3e50', relief='flat', bd=0, show='•'
            )
            self.password_entry.pack(side='left', fill='x', expand=True, pady=10)

            if hasattr(self, 'icons') and 'eye_24' in self.icons:
                self.toggle_btn = tk.Button(
                    input_frame, image=self.icons['eye_24'],
                    bg='#ecf0f1', relief='flat', bd=0, cursor='hand2',
                    command=self.toggle_password_visibility
                )
                self.toggle_btn.pack(side='right', padx=(6, 10), pady=10)
        else:
            self.username_entry = tk.Entry(
                input_frame, font=('Segoe UI', 10),
                bg='#ecf0f1', fg='#2c3e50', relief='flat', bd=0
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
                    host = mysql_config.get('host')
                    port_str = mysql_config.get('port')

                    if not host or not port_str:
                        self.root.after(0, lambda: messagebox.showerror(
                            "Error de Configuración", "Configuración MySQL incompleta"))
                        return

                    try:
                        port = int(port_str)
                    except ValueError:
                        self.root.after(0, lambda: messagebox.showerror(
                            "Error de Configuración", f"Puerto inválido: {port_str}"))
                        return

                    if not verificar_conectividad_red(host, port):
                        self.root.after(0, lambda: messagebox.showerror(
                            "Error de Conexión", "No se puede conectar al servidor MySQL"))
                        return

                try:
                    from src.database.db_manager import verificar_credenciales
                    usuario = verificar_credenciales(username, password)
                except ImportError:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Error", "Error al cargar módulo de base de datos"))
                    return

                if usuario:
                    def abrir_aplicacion():
                        import traceback

                        escribir_log_archivo("=== INICIANDO abrir_aplicacion ===")

                        try:
                            escribir_log_archivo("Paso 1: Intentando importar MainWindow...")
                            from src.gui.main_window import MainWindow
                            escribir_log_archivo("Paso 2: Import exitoso, destruyendo login...")
                            self.root.destroy()  # destruir ANTES de crear nuevo tk.Tk()
                            escribir_log_archivo("Paso 3: Creando MainWindow...")
                            app = MainWindow(usuario)
                            escribir_log_archivo("Paso 4: MainWindow creado, ejecutando app.run()...")
                            app.run()
                            escribir_log_archivo("Paso 6: app.run() terminó")
                        except Exception as e:
                            escribir_log_archivo(f"ERROR: {type(e).__name__}: {str(e)}")
                            escribir_log_archivo(traceback.format_exc())
                            try:
                                # login ya fue destruido — crear Tk temporal solo para el error
                                err_root = tk.Tk()
                                err_root.withdraw()
                                messagebox.showerror(
                                    "Error al cargar aplicación",
                                    f"Tipo: {type(e).__name__}\n"
                                    f"Mensaje: {str(e)}\n\n"
                                    f"Detalle guardado en:\n{LOG_PATH}",
                                    parent=err_root
                                )
                                err_root.destroy()
                            except Exception:
                                pass

                    self.root.after(0, abrir_aplicacion)
                else:
                    def mostrar_error_login():
                        messagebox.showerror("Error", "Usuario o contraseña incorrectos")
                        self.password_entry.delete(0, tk.END)
                        self.password_entry.focus()
                    self.root.after(0, mostrar_error_login)

            except Exception as e:
                error_msg = f"Error al verificar credenciales:\n{str(e)}\n\nVerifique la configuración de MySQL"
                self.root.after(0, lambda: messagebox.showerror("Error de Conexión", error_msg))

        threading.Thread(target=login_thread, daemon=True).start()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    try:
        login = LoginWindow()
        login.run()
    except Exception as e:
        messagebox.showerror("Error fatal", f"Ocurrió un error iniciando la aplicación:\n{str(e)}")