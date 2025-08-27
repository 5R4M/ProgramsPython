import configparser
import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime
import sys
import shutil
import socket

def resource_path(relative_path):
    """Obtiene la ruta absoluta al recurso, funciona para desarrollo y PyInstaller."""
    try:
        base_path = sys._MEIPASS  # PyInstaller
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_config_path(filename="mysql_config.ini"):
    """Devuelve la ruta del archivo de configuración junto al ejecutable (PyInstaller) o junto al script en desarrollo."""
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        return os.path.join(exe_dir, filename)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, filename)

def resolver_hostname_a_ip(hostname):
    """Resuelve un hostname a dirección IP"""
    try:
        ip = socket.gethostbyname(hostname)
        print(f"Hostname '{hostname}' resuelto a IP: {ip}")
        return ip
    except socket.gaierror as e:
        print(f"Error al resolver hostname '{hostname}': {e}")
        print(f"Usando hostname original: {hostname}")
        return hostname

def create_default_config(config_path):
    """Crea un archivo de configuración por defecto si no existe"""
    try:
        config = configparser.ConfigParser()
        config['MySQL'] = {
            'host': 'DESKTOP-KVJ8QQ3',
            'port': '3306',
            'admin_user': 'root',
            'admin_pass': '0.5735', 
            'bind_address': '0.0.0.0',
            'max_connections': '100',
            'timeout': '28800',
            'database': 'insumos'
        }
        
        # Crear directorio si no existe
        config_dir = os.path.dirname(config_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
        
        # Escribir archivo
        with open(config_path, 'w', encoding='utf-8') as f:
            config.write(f)
        
        print(f"Archivo de configuración por defecto creado en: {config_path}")
        
    except Exception as e:
        print(f"Error creando configuración por defecto: {e}")
        raise

def get_config():
    config_path = get_config_path("mysql_config.ini")
    
    # DEBUG: Imprimir la ruta del archivo
    print(f"🔍 DEBUG: Leyendo configuración desde: {config_path}")
    
    # Crear config por defecto si no existe
    if not os.path.exists(config_path):
        create_default_config(config_path)

    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    
    # DEBUG: Imprimir el contenido RAW del archivo
    if 'MySQL' in config:
        raw_host = config['MySQL'].get('host', 'DESKTOP-KVJ8QQ3')
        print(f"🔍 DEBUG: Host RAW del archivo: '{raw_host}'")
    
    if 'MySQL' not in config:
        raise Exception("No se encontró la configuración MySQL")

    host = config['MySQL'].get('host', 'DESKTOP-KVJ8QQ3').strip()
    print(f"🔍 DEBUG: Host después de .strip(): '{host}'")
    
    if host.lower() in ('127.0.0.1', 'localhost', ''):
        print(f"🔍 DEBUG: Host '{host}' está en la lista de reemplazo, cambiando a DESKTOP-KVJ8QQ3")
        host = 'DESKTOP-KVJ8QQ3'
    
    print(f"🔍 DEBUG: Host final: '{host}'")
    
    return {
        'host': host,
        'port': int(config['MySQL'].get('port', 3306)),
        'user': config['MySQL'].get('admin_user', 'root'),
        'password': config['MySQL'].get('admin_pass', ''),
        'database': config['MySQL'].get('database', 'insumos'),
        'charset': 'utf8mb4',
        'autocommit': False,
        'use_unicode': True
    }

def crear_base_datos_si_no_existe():
    """Crea la base de datos si no existe"""
    config = get_config()
    database_name = config['database']
    
    conn = None
    cursor = None
    
    try:
        # CORRECCIÓN: Especificar parámetros individualmente para evitar concatenación incorrecta
        print(f"Intentando conectar a MySQL en {config['host']}:{config['port']} con usuario {config['user']}")
        
        # Conectar SIN especificar base de datos para poder crearla
        conn = mysql.connector.connect(
            host=config['host'],
            port=config['port'],  # Asegurar que sea int
            user=config['user'],
            password=config['password'],
            charset='utf8mb4',
            use_unicode=True,
            autocommit=True,
            connection_timeout=10
        )
        
        cursor = conn.cursor()
        
        # Crear base de datos si no existe
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        
        print(f"Base de datos '{database_name}' verificada/creada exitosamente.")
    
    except Error as e:
        print(f"Error al crear/verificar base de datos: {e}")
        print(f"Detalles del error:")
        print(f"  - Código de error: {e.errno}")
        print(f"  - Mensaje: {e.msg}")
        print(f"  - Host: {config['host']}")
        print(f"  - Puerto: {config['port']} (tipo: {type(config['port'])})")
        print(f"  - Usuario: {config['user']}")
        
        # Proporcionar más información sobre el error
        if "Access denied" in str(e):
            print("SOLUCIÓN: Verifique que:")
            print("1. MySQL esté ejecutándose")
            print("2. El usuario y contraseña sean correctos")
            print("3. El usuario tenga permisos para crear bases de datos")
        elif "Can't connect" in str(e):
            print("SOLUCIÓN: Verifique que:")
            print("1. El servidor MySQL esté ejecutándose")
            print("2. El host y puerto sean correctos")
            print("3. No haya firewall bloqueando la conexión")
            print("4. El servidor permita conexiones remotas")
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def conectar_db():
    """Conecta a la base de datos MySQL"""
    conn = None
    try:
        config = get_config()
        
        # Verificar que el puerto sea entero
        if not isinstance(config['port'], int):
            config['port'] = int(config['port'])
        
        print(f"Conectando a base de datos {config['database']} en {config['host']}:{config['port']}")
        
        # Primero intentar crear la base de datos si no existe
        try:
            crear_base_datos_si_no_existe()
        except Error as db_create_error:
            print(f"Advertencia: No se pudo crear/verificar la base de datos: {db_create_error}")
            # Continuar intentando conectar de todas formas
        
        # Conectar con la base de datos
        conn = mysql.connector.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            charset=config['charset'],
            autocommit=config['autocommit'],
            use_unicode=config['use_unicode'],
            connection_timeout=10
        )
        
        print("✅ Conexión a base de datos exitosa")
        
        # Crear tablas si no existen
        try:
            crear_tablas_si_no_existen(conn)
        except Error as table_error:
            print(f"Advertencia: Error al crear tablas: {table_error}")
        
        return conn
        
    except Error as e:
        print(f"❌ Error al conectar a la base de datos: {e}")
        print(f"Detalles del error:")
        print(f"  - Código de error: {e.errno}")
        print(f"  - Mensaje: {e.msg}")
        
        # Diagnóstico específico del error localhost3306
        if "localhost3306" in str(e) or "3306" in config['host']:
            print("\n🔍 PROBLEMA DETECTADO: Concatenación incorrecta de host+puerto")
            print(f"Host actual: '{config['host']}'")
            print(f"Puerto actual: {config['port']} (tipo: {type(config['port'])})")
            
            # Intentar limpiar el host si contiene el puerto
            if "3306" in config['host']:
                clean_host = config['host'].replace("3306", "").replace(":", "")
                print(f"Intentando con host limpio: '{clean_host}'")
                try:
                    conn = mysql.connector.connect(
                        host=clean_host,
                        port=config['port'],
                        user=config['user'],
                        password=config['password'],
                        database=config['database'],
                        charset=config['charset'],
                        autocommit=config['autocommit'],
                        use_unicode=config['use_unicode'],
                        connection_timeout=10
                    )
                    print("✅ Conexión exitosa con host limpio")
                    return conn
                except Error as clean_error:
                    print(f"❌ Error incluso con host limpio: {clean_error}")
        
        if "Access denied" in str(e):
            print("\n=== DIAGNÓSTICO DE CONEXIÓN ===")
            print("El error indica problemas de autenticación.")
            print("Posibles soluciones:")
            print("1. Verificar que MySQL esté ejecutándose")
            print("2. Configurar credenciales correctas en la aplicación")
            print("3. Verificar permisos del usuario en MySQL")
            print("====\n")
        elif "Can't connect" in str(e):
            print("\n=== DIAGNÓSTICO DE CONEXIÓN ===")
            print("No se puede conectar al servidor MySQL.")
            print("Posibles soluciones:")
            print("1. Verificar que MySQL esté ejecutándose")
            print("2. Verificar host y puerto")
            print("3. Verificar firewall")
            print("4. Verificar que el servidor permita conexiones remotas")
            print("====\n")
            
            # Ejecutar diagnóstico automático
            debug_mysql_connection()
        
        return None

def debug_mysql_connection():
    """Función específica para diagnosticar problemas de conexión MySQL"""
    print("=" * 60)
    print("=== DIAGNÓSTICO ESPECÍFICO MYSQL ===")
    print("=" * 60)
    
    try:
        # Leer configuración
        config = get_config()
        
        print(f"Host: '{config['host']}' (tipo: {type(config['host'])})")
        print(f"Port: {config['port']} (tipo: {type(config['port'])})")
        print(f"User: '{config['user']}'")
        print(f"Database: '{config['database']}'")
        
        # Verificar que el puerto sea entero
        if not isinstance(config['port'], int):
            print(f"⚠️ ADVERTENCIA: Puerto no es entero, convirtiendo...")
            config['port'] = int(config['port'])
        
        # Probar conexión básica de red
        print(f"\n1. Probando conectividad de red a {config['host']}:{config['port']}...")
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((config['host'], config['port']))
        sock.close()
        
        if result == 0:
            print("✅ Conectividad de red OK")
        else:
            print(f"❌ No se puede conectar al puerto {config['port']} en {config['host']}")
            print(f"   Código de error: {result}")
            return
        
        # Probar conexión MySQL sin base de datos
        print(f"\n2. Probando conexión MySQL sin base de datos...")
        try:
            conn = mysql.connector.connect(
                host=config['host'],
                port=config['port'],
                user=config['user'],
                password=config['password'],
                connection_timeout=5
            )
            print("✅ Conexión MySQL básica exitosa")
            conn.close()
            
        except mysql.connector.Error as e:
            print(f"❌ Error MySQL básico: {e.errno} - {e.msg}")
            if "localhost3306" in str(e):
                print("🔍 PROBLEMA IDENTIFICADO: Se está concatenando host+puerto incorrectamente")
            return
        
        # Probar conexión completa
        print(f"\n3. Probando conexión completa con base de datos...")
        try:
            conn = mysql.connector.connect(
                host=config['host'],
                port=config['port'],
                user=config['user'],
                password=config['password'],
                database=config['database'],
                connection_timeout=5
            )
            print("✅ Conexión completa exitosa")
            
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            print(f"📊 Versión MySQL: {version}")
            cursor.close()
            conn.close()
            
        except mysql.connector.Error as e:
            print(f"❌ Error MySQL completo: {e.errno} - {e.msg}")
            if e.errno == 1049:  # Base de datos no existe
                print("💡 La base de datos no existe, se creará automáticamente")
            
    except Exception as e:
        print(f"❌ Error en diagnóstico: {e}")
        import traceback
        traceback.print_exc()
    
def crear_tablas_si_no_existen(conn):
    """Crea todas las tablas necesarias si no existen"""
    try:
        cursor = conn.cursor()
        
        # Tabla area
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS area (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(255) NOT NULL UNIQUE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Tabla distrito
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS distrito (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(255) NOT NULL,
        id_area INT,
        FOREIGN KEY (id_area) REFERENCES area(id) ON DELETE SET NULL,
        INDEX idx_distrito_area (id_area)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Tabla tipo_servicio
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tipo_servicio (
        id INT AUTO_INCREMENT PRIMARY KEY,
        descripcion TEXT NOT NULL,
        id_distrito INT,
        FOREIGN KEY (id_distrito) REFERENCES distrito(id) ON DELETE CASCADE,
        INDEX idx_tipo_servicio_distrito (id_distrito)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Tabla servicio
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS servicio (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(255) NOT NULL,
        id_tipo_servicio INT,
        FOREIGN KEY (id_tipo_servicio) REFERENCES tipo_servicio(id) ON DELETE CASCADE,
        INDEX idx_servicio_tipo (id_tipo_servicio)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Tabla tipo_insumo
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tipo_insumo (
        id INT AUTO_INCREMENT PRIMARY KEY,
        descripcion VARCHAR(255) NOT NULL UNIQUE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Tabla presentacion
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS presentacion (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(255) NOT NULL UNIQUE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Tabla insumo
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS insumo (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(255) NOT NULL,
        lote VARCHAR(255),
        fecha_vencimiento DATE,
        id_tipo_insumo INT,
        FOREIGN KEY (id_tipo_insumo) REFERENCES tipo_insumo(id) ON DELETE CASCADE,
        INDEX idx_insumo_tipo (id_tipo_insumo)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Tabla insumo_presentacion (relación muchos a muchos)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS insumo_presentacion (
        insumo_id INT,
        presentacion_id INT,
        PRIMARY KEY (insumo_id, presentacion_id),
        FOREIGN KEY (insumo_id) REFERENCES insumo(id) ON DELETE CASCADE,
        FOREIGN KEY (presentacion_id) REFERENCES presentacion(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Tabla tipo_movimiento
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tipo_movimiento (
        id INT AUTO_INCREMENT PRIMARY KEY,
        descripcion VARCHAR(255) NOT NULL UNIQUE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Tabla movimiento
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimiento (
        id INT AUTO_INCREMENT PRIMARY KEY,
        fecha_registro DATE NOT NULL,
        referencia VARCHAR(255),
        tipo_movimiento_id INT NOT NULL,
        area_id INT,
        distrito_id INT,
        servicio_id INT,
        insumo_id INT NOT NULL,
        presentacion_id INT,
        lote VARCHAR(255),
        fecha_vencimiento DATE,
        cantidad DECIMAL(10,2) NOT NULL,
        salida_distrito_id INT,
        salida_servicio_id INT,
        observaciones TEXT,
        FOREIGN KEY (tipo_movimiento_id) REFERENCES tipo_movimiento(id),
        FOREIGN KEY (area_id) REFERENCES area(id) ON DELETE SET NULL,
        FOREIGN KEY (distrito_id) REFERENCES distrito(id) ON DELETE SET NULL,
        FOREIGN KEY (servicio_id) REFERENCES servicio(id) ON DELETE SET NULL,
        FOREIGN KEY (insumo_id) REFERENCES insumo(id),
        FOREIGN KEY (presentacion_id) REFERENCES presentacion(id) ON DELETE SET NULL,
        FOREIGN KEY (salida_distrito_id) REFERENCES distrito(id) ON DELETE SET NULL,
        FOREIGN KEY (salida_servicio_id) REFERENCES servicio(id) ON DELETE SET NULL,
        INDEX idx_movimiento_fecha (fecha_registro),
        INDEX idx_movimiento_insumo (insumo_id),
        INDEX idx_movimiento_tipo (tipo_movimiento_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Tabla usuarios
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        nombre_completo VARCHAR(255),
        rol ENUM('admin', 'usuario', 'super_admin') NOT NULL,
        activo BOOLEAN DEFAULT TRUE,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        conn.commit()
        print("Tablas verificadas/creadas exitosamente.")
    
    except Error as e:
        print(f"Error al crear tablas: {e}")
        conn.rollback()
    finally:
        cursor.close()

# ---- OPERACIONES ÁREA ----

def obtener_areas():
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, nombre FROM area ORDER BY nombre")
            return cursor.fetchall()
        except Error as e:
            print(f"Error al obtener áreas: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

def agregar_area(nombre):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM area WHERE nombre = %s", (nombre,))
            existente = cursor.fetchone()
            if existente:
                return existente['id']
            cursor.execute("INSERT INTO area (nombre) VALUES (%s)", (nombre,))
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error al agregar área: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()

def actualizar_area(id_area, nuevo_nombre):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE area SET nombre = %s WHERE id = %s", (nuevo_nombre, id_area))
            conn.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error al actualizar área: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

def eliminar_area(id_area):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            # Eliminar distritos y cascada servicios
            cursor.execute("SELECT id FROM distrito WHERE id_area = %s", (id_area,))
            distritos = cursor.fetchall()
            for distrito in distritos:
                eliminar_distrito(distrito['id'])
                cursor.execute("DELETE FROM area WHERE id = %s", (id_area,))
                conn.commit()
                return True
        except Error as e:
            print(f"Error al eliminar área: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

# ---- OPERACIONES DISTRITO ----

def obtener_distritos():
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
            SELECT d.id, d.nombre, a.nombre AS area_nombre
            FROM distrito d
            LEFT JOIN area a ON d.id_area = a.id
            ORDER BY d.nombre
            """)
            return cursor.fetchall()
        except Error as e:
            print(f"Error al obtener distritos: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

def obtener_distritos_por_area(id_area):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
            SELECT id, nombre FROM distrito WHERE id_area = %s ORDER BY nombre
            """, (id_area,))
            return cursor.fetchall()
        except Error as e:
            print(f"Error al obtener distritos por área: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

def agregar_distrito(nombre, id_area=None):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM distrito WHERE nombre = %s AND id_area = %s", (nombre, id_area))
            existente = cursor.fetchone()
            if existente:
                return existente['id']
            cursor.execute("INSERT INTO distrito (nombre, id_area) VALUES (%s, %s)", (nombre, id_area))
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error al agregar distrito: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()

def actualizar_distrito(id_distrito, nuevo_nombre, id_area=None):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            if id_area is not None:
                cursor.execute("UPDATE distrito SET nombre = %s, id_area = %s WHERE id = %s", (nuevo_nombre, id_area, id_distrito))
            else:
                cursor.execute("UPDATE distrito SET nombre = %s WHERE id = %s", (nuevo_nombre, id_distrito))
                conn.commit()
                return cursor.rowcount > 0
        except Error as e:
            print(f"Error al actualizar distrito: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

def eliminar_distrito(id_distrito):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM tipo_servicio WHERE id_distrito = %s", (id_distrito,))
            tipos_servicio = cursor.fetchall()
            for tipo in tipos_servicio:
                eliminar_tipo_servicio(tipo['id'])
                cursor.execute("DELETE FROM distrito WHERE id = %s", (id_distrito,))
                conn.commit()
                return True
        except Error as e:
            print(f"Error al eliminar distrito: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

# ---- OPERACIONES TIPO SERVICIO ----

def obtener_tipos_servicio_por_distrito(id_distrito):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, descripcion FROM tipo_servicio WHERE id_distrito = %s ORDER BY descripcion", (id_distrito,))
            return cursor.fetchall()
        except Error as e:
            print(f"Error al obtener tipos de servicio: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

def agregar_tipo_servicio(id_distrito, descripcion):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO tipo_servicio (id_distrito, descripcion) VALUES (%s, %s)", (id_distrito, descripcion))
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error al agregar tipo de servicio: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()

def actualizar_tipo_servicio(id_tipo_servicio, nueva_descripcion):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE tipo_servicio SET descripcion = %s WHERE id = %s", (nueva_descripcion, id_tipo_servicio))
            conn.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error al actualizar tipo de servicio: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

def eliminar_tipo_servicio(id_tipo_servicio):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM servicio WHERE id_tipo_servicio = %s", (id_tipo_servicio,))
            cursor.execute("DELETE FROM tipo_servicio WHERE id = %s", (id_tipo_servicio,))
            conn.commit()
            return True
        except Error as e:
            print(f"Error al eliminar tipo de servicio: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

# ---- OPERACIONES SERVICIO ----

def obtener_servicios_por_tipo(id_tipo_servicio):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, nombre FROM servicio WHERE id_tipo_servicio = %s ORDER BY nombre", (id_tipo_servicio,))
            return cursor.fetchall()
        except Error as e:
            print(f"Error al obtener servicios: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

def agregar_servicio(id_tipo_servicio, nombre):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO servicio (id_tipo_servicio, nombre) VALUES (%s, %s)", (id_tipo_servicio, nombre))
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error al agregar servicio: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()

def actualizar_servicio(id_servicio, nuevo_nombre):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE servicio SET nombre = %s WHERE id = %s", (nuevo_nombre, id_servicio))
            conn.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error al actualizar servicio: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

def eliminar_servicio(id_servicio):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM servicio WHERE id = %s", (id_servicio,))
            conn.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error al eliminar servicio: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

# ---- OPERACIONES TIPO INSUMO ----

def obtener_tipos_insumo():
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, descripcion FROM tipo_insumo ORDER BY descripcion")
            return cursor.fetchall()
        except Error as e:
            print(f"Error al obtener tipos de insumo: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

def agregar_tipo_insumo(descripcion):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM tipo_insumo WHERE descripcion = %s", (descripcion,))
            existente = cursor.fetchone()
            if existente:
                return existente['id']
            cursor.execute("INSERT INTO tipo_insumo (descripcion) VALUES (%s)", (descripcion,))
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error al agregar tipo de insumo: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()

def actualizar_tipo_insumo(id_tipo_insumo, nueva_descripcion):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE tipo_insumo SET descripcion = %s WHERE id = %s", (nueva_descripcion, id_tipo_insumo))
            conn.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error al actualizar tipo de insumo: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

def eliminar_tipo_insumo(id_tipo_insumo):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            # Eliminar insumos relacionados y sus relaciones con presentaciones
            cursor.execute("SELECT id FROM insumo WHERE id_tipo_insumo = %s", (id_tipo_insumo,))
            insumos = cursor.fetchall()
            for insumo in insumos:
                eliminar_insumo(insumo['id'])
                cursor.execute("DELETE FROM tipo_insumo WHERE id = %s", (id_tipo_insumo,))
                conn.commit()
                return True
        except Error as e:
            print(f"Error al eliminar tipo de insumo: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

# ---- OPERACIONES PRESENTACION ----

def obtener_presentaciones():
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, nombre FROM presentacion ORDER BY nombre")
            return cursor.fetchall()
        except Error as e:
            print(f"Error al obtener presentaciones: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

def agregar_presentacion(nombre):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM presentacion WHERE nombre = %s", (nombre,))
            existente = cursor.fetchone()
            if existente:
                return existente['id']
            cursor.execute("INSERT INTO presentacion (nombre) VALUES (%s)", (nombre,))
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error al agregar presentación: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()

def actualizar_presentacion(id_presentacion, nuevo_nombre):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE presentacion SET nombre = %s WHERE id = %s", (nuevo_nombre, id_presentacion))
            conn.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error al actualizar presentación: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

def eliminar_presentacion(id_presentacion):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            # Verificar si hay insumos asociados en la tabla intermedia
            cursor.execute("SELECT COUNT(*) as count FROM insumo_presentacion WHERE presentacion_id = %s", (id_presentacion,))
            resultado = cursor.fetchone()
            if resultado['count'] > 0:
                print(f"No se puede eliminar la presentación porque hay {resultado['count']} insumos asociados.")
                return False
            cursor.execute("DELETE FROM presentacion WHERE id = %s", (id_presentacion,))
            conn.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error al eliminar presentación: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

# ---- OPERACIONES INSUMO ----

def obtener_insumos_por_tipo(id_tipo_insumo):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            # Obtener insumos y sus presentaciones concatenadas
            cursor.execute("""
            SELECT i.id, i.nombre, i.lote, i.fecha_vencimiento, t.descripcion as tipo_insumo,
            GROUP_CONCAT(p.nombre SEPARATOR ', ') as nombre_presentacion
            FROM insumo i
            JOIN tipo_insumo t ON i.id_tipo_insumo = t.id
            LEFT JOIN insumo_presentacion ip ON i.id = ip.insumo_id
            LEFT JOIN presentacion p ON ip.presentacion_id = p.id
            WHERE i.id_tipo_insumo = %s
            GROUP BY i.id
            ORDER BY i.nombre
            """, (id_tipo_insumo,))
            return cursor.fetchall()
        except Error as e:
            print(f"Error al obtener insumos: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

def agregar_insumo(nombre, lote, id_presentacion, fecha_vencimiento, id_tipo_insumo):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO insumo (nombre, lote, fecha_vencimiento, id_tipo_insumo)
            VALUES (%s, %s, %s, %s)""", (nombre, lote, fecha_vencimiento, id_tipo_insumo))
            id_insumo = cursor.lastrowid
            # Insertar relación con presentación
            if id_presentacion:
                cursor.execute("""
            INSERT INTO insumo_presentacion (insumo_id, presentacion_id)
            VALUES (%s, %s)""", (id_insumo, id_presentacion))
            conn.commit()
            return id_insumo
        except Error as e:
            print(f"Error al agregar insumo: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()

def actualizar_insumo(id_insumo, nombre, lote, id_presentacion, fecha_vencimiento, id_tipo_insumo):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE insumo
            SET nombre = %s, lote = %s, fecha_vencimiento = %s, id_tipo_insumo = %s
            WHERE id = %s""", (nombre, lote, fecha_vencimiento, id_tipo_insumo, id_insumo))
            # Actualizar relación con presentación: eliminar anteriores y agregar la nueva
            cursor.execute("DELETE FROM insumo_presentacion WHERE insumo_id = %s", (id_insumo,))
            if id_presentacion:
                cursor.execute("INSERT INTO insumo_presentacion (insumo_id, presentacion_id) VALUES (%s, %s)", (id_insumo, id_presentacion))
                conn.commit()
                return cursor.rowcount > 0
        except Error as e:
            print(f"Error al actualizar insumo: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

def obtener_insumo_por_id(id_insumo):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
            SELECT i.id, i.nombre, i.lote, i.fecha_vencimiento, i.id_tipo_insumo,
            t.descripcion as tipo_insumo,
            GROUP_CONCAT(p.nombre SEPARATOR ', ') as nombre_presentacion
            FROM insumo i
            JOIN tipo_insumo t ON i.id_tipo_insumo = t.id
            LEFT JOIN insumo_presentacion ip ON i.id = ip.insumo_id
            LEFT JOIN presentacion p ON ip.presentacion_id = p.id
            WHERE i.id = %s
            GROUP BY i.id
            """, (id_insumo,))
            return cursor.fetchone()
        except Error as e:
            print(f"Error al obtener insumo: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

def obtener_insumo_por_nombre(nombre, id_tipo_insumo):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
            SELECT id, nombre FROM insumo WHERE nombre = %s AND id_tipo_insumo = %s
            """, (nombre, id_tipo_insumo))
            return cursor.fetchone()
        except Error as e:
            print(f"Error al obtener insumo por nombre: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

def eliminar_insumo(id_insumo):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM insumo_presentacion WHERE insumo_id = %s", (id_insumo,))
            cursor.execute("DELETE FROM insumo WHERE id = %s", (id_insumo,))
            conn.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error al eliminar insumo: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

# ---- OPERACIONES TIPO MOVIMIENTO ----

def obtener_tipos_movimiento():
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, descripcion FROM tipo_movimiento ORDER BY descripcion")
            return cursor.fetchall()
        except Error as e:
            print(f"Error al obtener tipos de movimiento: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

def agregar_tipo_movimiento(descripcion):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO tipo_movimiento (descripcion) VALUES (%s)", (descripcion,))
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error al agregar tipo de movimiento: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()

def actualizar_tipo_movimiento(id_tipo, descripcion):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE tipo_movimiento SET descripcion = %s WHERE id = %s", (descripcion, id_tipo))
            conn.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error al actualizar tipo de movimiento: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

def eliminar_tipo_movimiento(id_tipo):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tipo_movimiento WHERE id = %s", (id_tipo,))
            conn.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error al eliminar tipo de movimiento: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

# ---- OPERACIONES MOVIMIENTO ----

def guardar_movimiento(movimiento_data):
    """
    Guarda un movimiento en la base de datos.

    Args:
    movimiento_data (dict): Diccionario con los datos del movimiento

    Returns:
    int: ID del movimiento guardado
    """
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            fecha_registro = movimiento_data['fecha_registro'].strftime('%Y-%m-%d')
            fecha_vencimiento = (
            movimiento_data['fecha_vencimiento'].strftime('%Y-%m-%d')
            if movimiento_data['fecha_vencimiento'] is not None
            else None
            )
            # Usar el area_id directamente del diccionario
            area_id = movimiento_data.get('area_id')
            distrito_id = movimiento_data.get('distrito_id')

            # Imprimir para depuración
            print(f"Guardando movimiento con area_id={area_id}, distrito_id={distrito_id}, servicio_id={movimiento_data.get('servicio_id')}")

            cursor.execute("""
            INSERT INTO movimiento (
            fecha_registro,
            referencia,
            tipo_movimiento_id,
            area_id,
            distrito_id,
            servicio_id,
            insumo_id,
            presentacion_id,
            lote,
            fecha_vencimiento,
            cantidad,
            salida_distrito_id,
            salida_servicio_id,
            observaciones
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
            fecha_registro,
            movimiento_data['referencia'],
            movimiento_data['tipo_movimiento_id'],
            area_id,
            distrito_id,
            movimiento_data.get('servicio_id'),
            movimiento_data['insumo_id'],
            movimiento_data.get('presentacion_id'),
            movimiento_data['lote'],
            fecha_vencimiento,
            movimiento_data['cantidad'],
            movimiento_data.get('salida_distrito_id'),
            movimiento_data.get('salida_servicio_id'),
            movimiento_data.get('observaciones')
            ))
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error al guardar movimiento: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()

# ---- FUNCIONES PARA OBTENER IDS ----

def obtener_id_area(nombre_area):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM area WHERE nombre = %s", (nombre_area,))
            resultado = cursor.fetchone()
            return resultado['id'] if resultado else None
        except Error as e:
            print(f"Error al obtener id área: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

def obtener_id_distrito(nombre_distrito):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM distrito WHERE nombre = %s", (nombre_distrito,))
            resultado = cursor.fetchone()
            return resultado['id'] if resultado else None
        except Error as e:
            print(f"Error al obtener id distrito: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

def obtener_id_insumo(nombre_insumo, id_tipo_insumo):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM insumo WHERE nombre = %s AND id_tipo_insumo = %s", (nombre_insumo, id_tipo_insumo))
            resultado = cursor.fetchone()
            return resultado['id'] if resultado else None
        except Error as e:
            print(f"Error al obtener id insumo: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

def obtener_id_presentacion(nombre_presentacion):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM presentacion WHERE nombre = %s", (nombre_presentacion,))
            resultado = cursor.fetchone()
            return resultado['id'] if resultado else None
        except Error as e:
            print(f"Error al obtener id presentación: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

def obtener_id_servicio(nombre_servicio):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM servicio WHERE nombre = %s", (nombre_servicio,))
            resultado = cursor.fetchone()
            return resultado['id'] if resultado else None
        except Error as e:
            print(f"Error al obtener id servicio: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

def obtener_id_tipo_insumo(descripcion_tipo_insumo):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM tipo_insumo WHERE descripcion = %s", (descripcion_tipo_insumo,))
            resultado = cursor.fetchone()
            return resultado['id'] if resultado else None
        except Error as e:
            print(f"Error al obtener id tipo insumo: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

def obtener_id_tipo_movimiento(descripcion_tipo_movimiento):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM tipo_movimiento WHERE descripcion = %s", (descripcion_tipo_movimiento,))
            resultado = cursor.fetchone()
            return resultado['id'] if resultado else None
        except Error as e:
            print(f"Error al obtener id tipo movimiento: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

def obtener_id_tipo_servicio(descripcion_tipo_servicio):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM tipo_servicio WHERE descripcion = %s", (descripcion_tipo_servicio,))
            resultado = cursor.fetchone()
            return resultado['id'] if resultado else None
        except Error as e:
            print(f"Error al obtener id tipo servicio: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

# ---- FUNCIONES AUXILIARES ----

def verificar_conexion(return_error=False):
    try:
        conn = conectar_db()
        if not conn:
            raise Exception("conectar_db() devolvió None")
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        conn.close()
        return (True, None) if return_error else True
    except Exception as e:
        return (False, e) if return_error else False

def verificar_tablas():
    conn = conectar_db()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        tablas = [
            'area',
            'distrito',
            'tipo_servicio',
            'servicio',
            'tipo_insumo',
            'presentacion',
            'insumo',
            'insumo_presentacion',
            'tipo_movimiento',
            'movimiento',
            'usuarios'
        ]
        for tabla in tablas:
            cursor.execute("SHOW TABLES LIKE %s", (tabla,))
            if not cursor.fetchone():
                return False
        return True
    except Error as e:
        print(f"Error al verificar tablas: {e}")
        return False
    finally:
        cursor.close()
        conn.close()
        
# ---- OPERACIÓN REPORTE ----

def obtener_movimientos_kardex(fecha_inicio, fecha_fin, distrito_nombre=None, tipo_servicio_desc=None,
    servicio_nombre=None, tipo_insumo_desc=None, insumo_nombre=None,
    presentacion_nombre=None, area_nombre=None):
    conn = conectar_db()
    if not conn:
        return []

    try:
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT
        m.fecha_registro AS fecha,
        m.referencia,
        tm.descripcion AS tipo_movimiento,
        m.cantidad,
        m.lote,
        m.fecha_vencimiento,
        m.observaciones,
        d_salida.nombre AS distrito_destino,
        s_salida.nombre AS servicio_destino,
        i.id AS codigo_insumo,
        i.nombre AS nombre_insumo,
        COALESCE(i.lote, '') AS codigo,
        COALESCE(p.nombre, '') AS nombre_presentacion,
        0 AS existencia,
        0 AS reajuste,
        -- USAR LOS DATOS DIRECTOS DEL MOVIMIENTO, NO JOINS COMPLEJOS
        a_directa.nombre AS area_nombre,
        d_directa.nombre AS distrito_nombre,
        ts_directa.descripcion AS tipo_servicio_desc,
        s_directa.nombre AS servicio_nombre
        FROM movimiento m
        JOIN tipo_movimiento tm ON m.tipo_movimiento_id = tm.id
        -- JOINs directos con los IDs guardados en el movimiento
        LEFT JOIN area a_directa ON m.area_id = a_directa.id
        LEFT JOIN distrito d_directa ON m.distrito_id = d_directa.id
        LEFT JOIN servicio s_directa ON m.servicio_id = s_directa.id
        LEFT JOIN tipo_servicio ts_directa ON s_directa.id_tipo_servicio = ts_directa.id
        -- JOINs para salida nivel inferior
        LEFT JOIN distrito d_salida ON m.salida_distrito_id = d_salida.id
        LEFT JOIN servicio s_salida ON m.salida_servicio_id = s_salida.id
        -- JOINs para insumo y presentación
        LEFT JOIN insumo i ON m.insumo_id = i.id
        LEFT JOIN tipo_insumo ti ON i.id_tipo_insumo = ti.id
        LEFT JOIN insumo_presentacion ip ON i.id = ip.insumo_id
        LEFT JOIN presentacion p ON ip.presentacion_id = p.id
        WHERE m.fecha_registro BETWEEN %s AND %s
        """

        params = [fecha_inicio, fecha_fin]
        
        # SOLO filtrar por tipo de insumo, insumo y presentación (no por ubicación)
        # El filtrado por ubicación se hará después en filtrar_movimientos_por_nivel
        
        # Filtrar por tipo de insumo
        if tipo_insumo_desc and tipo_insumo_desc.strip():
            query += " AND ti.descripcion = %s"
            params.append(tipo_insumo_desc)
        
        # Filtrar por insumo
        if insumo_nombre and insumo_nombre.strip():
            query += " AND i.nombre = %s"
            params.append(insumo_nombre)
        
        # Filtrar por presentación
        if presentacion_nombre and presentacion_nombre.strip():
            query += " AND p.nombre = %s"
            params.append(presentacion_nombre)

        query += " ORDER BY m.fecha_registro ASC, m.id ASC"

        cursor.execute(query, params)
        resultados = cursor.fetchall()

        movimientos = []
        for row in resultados:
            movimientos.append({
            'fecha': row['fecha'],
            'referencia': row['referencia'],
            'tipo_movimiento': row['tipo_movimiento'],
            'cantidad': row['cantidad'],
            'lote': row['lote'],
            'fecha_vencimiento': row['fecha_vencimiento'],
            'observaciones': row['observaciones'],
            'distrito_destino': row['distrito_destino'],
            'servicio_destino': row['servicio_destino'],
            'nombre_insumo': row['nombre_insumo'],
            'codigo': row['codigo'],
            'nombre_presentacion': row['nombre_presentacion'],
            'existencia': row['existencia'],
            'reajuste': row['reajuste'],
            'area_nombre': row['area_nombre'],
            'distrito_nombre': row['distrito_nombre'],
            'tipo_servicio_desc': row['tipo_servicio_desc'],
            'servicio_nombre': row['servicio_nombre']
            })

        return movimientos

    except Error as e:
        print(f"Error al obtener movimientos kardex: {e}")
        return []
    finally:
        cursor.close()
        conn.close()
    
# ---- OPERACIÓN USUARIOS ----

def crear_tabla_usuarios():
    """Crea la tabla de usuarios si no existe y crea el super usuario"""
    try:
        # Primero verificar conexión
        conn = conectar_db()
        if conn:
            conn.close()
            print("Conexión a base de datos exitosa")
            # Crear super usuario
            crear_super_usuario_si_no_existe()
            return True
        else:
            print("ERROR: No se pudo conectar a MySQL para crear tablas")
            return False
    except Exception as e:
        print(f"Error en crear_tabla_usuarios: {e}")
        raise e  # Re-lanzar para que se maneje en login.py

def crear_super_usuario_si_no_existe():
    """Crea el super usuario si no existe"""
    import hashlib
    
    conn = None
    cursor = None
    
    # Credenciales del super usuario
    super_user = {
        'username': 'admin',
        'password': hashlib.sha256('admin123'.encode()).hexdigest(),
        'nombre_completo': 'Administrador del Sistema',
        'rol': 'super_admin'
    }

    try:
        # FORZAR EL HOST CORRECTO - NO USAR get_config() AQUÍ
        print("Creando super usuario en: DESKTOP-KVJ8QQ3:3306")
        
        # Conectar DIRECTAMENTE con valores hardcodeados para evitar problemas
        conn = mysql.connector.connect(
            host='DESKTOP-KVJ8QQ3',  # HARDCODEADO
            port=3306,              # HARDCODEADO
            user='root',            # HARDCODEADO
            password='0.5735',      # HARDCODEADO
            database='insumos',     # HARDCODEADO
            charset='utf8mb4',
            autocommit=False,
            use_unicode=True,
            connection_timeout=10
        )
        
        if not conn:
            print("No se pudo conectar a la base de datos para crear super usuario")
            return
            
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id FROM usuarios WHERE username = %s', (super_user['username'],))
        
        if not cursor.fetchone():
            # Crear super usuario
            cursor.execute("""
            INSERT INTO usuarios (username, password, nombre_completo, rol)
            VALUES (%s, %s, %s, %s)
            """, (
                super_user['username'],
                super_user['password'],
                super_user['nombre_completo'],
                super_user['rol']
            ))
            conn.commit()
            print("Super usuario creado exitosamente (usuario: admin, contraseña: admin123)")
        else:
            print("Super usuario ya existe")
    
    except Exception as e:
        print(f"Error creando super usuario: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
def existe_usuario(username):
    """Verifica si un nombre de usuario ya existe en la base de datos."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM usuarios WHERE username = %s", (username,))
            resultado = cursor.fetchone()
            return resultado is not None
        except Exception as e:
            print(f"Error al verificar la existencia del usuario: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

def verificar_credenciales(username, password):
    """Verifica las credenciales del usuario"""
    import hashlib
    
    conn = None
    cursor = None
    
    try:
        conn = conectar_db()
        if not conn:
            raise Exception("No se pudo establecer conexión con la base de datos MySQL. Verifique la configuración.")
        
        cursor = conn.cursor(dictionary=True)

        # Hash de la contraseña ingresada
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # Buscar usuario sin importar mayúsculas/minúsculas
        cursor.execute("""
        SELECT id, username, nombre_completo, rol, activo
        FROM usuarios
        WHERE LOWER(username) = LOWER(%s) AND password = %s
        """, (username, password_hash))

        usuario = cursor.fetchone()

        if usuario and usuario['activo']:
            return {
            'id': usuario['id'],
            'username': usuario['username'],
            'nombre_completo': usuario['nombre_completo'],
            'rol': usuario['rol'],
            'activo': usuario['activo']
            }
            return None

    except Exception as e:
        print(f"Error al verificar credenciales: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def obtener_usuarios():
    """Devuelve la lista de usuarios (excepto el super_admin)"""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, username, nombre_completo, rol, activo FROM usuarios WHERE rol != 'super_admin'")
            usuarios = cursor.fetchall()
            return usuarios
        finally:
            cursor.close()
            conn.close()

def crear_usuario(username, password, nombre_completo, rol, activo=1):
    import hashlib
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
            "INSERT INTO usuarios (username, password, nombre_completo, rol, activo) VALUES (%s, %s, %s, %s, %s)",
            (username, hashlib.sha256(password.encode()).hexdigest(), nombre_completo, rol, activo)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Error creando usuario: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

def actualizar_usuario(id_usuario, nombre_completo, rol, activo):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
            "UPDATE usuarios SET nombre_completo=%s, rol=%s, activo=%s WHERE id=%s",
            (nombre_completo, rol, activo, id_usuario)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Error actualizando usuario: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

def cambiar_password_usuario(id_usuario, new_password):
    import hashlib
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
            "UPDATE usuarios SET password=%s WHERE id=%s",
            (hashlib.sha256(new_password.encode()).hexdigest(), id_usuario)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Error cambiando contraseña: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

def eliminar_usuario(id_usuario):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM usuarios WHERE id=%s", (id_usuario,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error eliminando usuario: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

# ---- OPERACIÓN CORRECCIÓN ----

def buscar_movimientos_por_filtros(
    fecha_ini, fecha_fin, area, distrito, tipo_servicio,
    servicio, tipo_insumo, insumo, presentacion, tipo_movimiento
):
    conn = conectar_db()
    if not conn:
        return []

    try:
        cursor = conn.cursor(dictionary=True)

        # Manejar valores vacíos
        area = area if area else None
        distrito = distrito if distrito else None
        tipo_servicio = tipo_servicio if tipo_servicio else None
        servicio = servicio if servicio else None
        tipo_insumo = tipo_insumo if tipo_insumo else None
        insumo = insumo if insumo else None
        presentacion = presentacion if presentacion else None
        tipo_movimiento = tipo_movimiento if tipo_movimiento else None

        query = """
        SELECT
        m.id,
        m.fecha_registro AS fecha,
        a2.nombre AS area_nombre,
        d2.nombre AS distrito_nombre,
        ts.descripcion AS tipo_servicio_desc,
        m.referencia,
        s.nombre AS servicio_nombre,
        tm.descripcion AS tipo_movimiento,
        m.lote,
        m.fecha_vencimiento,
        m.cantidad,
        i.nombre AS insumo_nombre,
        d_salida.nombre AS distrito_salida,
        s_salida.nombre AS servicio_salida,
        m.observaciones
        FROM movimiento m
        JOIN tipo_movimiento tm ON m.tipo_movimiento_id = tm.id
        LEFT JOIN area a2 ON m.area_id = a2.id
        LEFT JOIN distrito d2 ON m.distrito_id = d2.id
        LEFT JOIN servicio s ON m.servicio_id = s.id
        LEFT JOIN tipo_servicio ts ON s.id_tipo_servicio = ts.id
        LEFT JOIN distrito d ON ts.id_distrito = d.id
        LEFT JOIN area a ON d.id_area = a.id
        LEFT JOIN distrito d_salida ON m.salida_distrito_id = d_salida.id
        LEFT JOIN servicio s_salida ON m.salida_servicio_id = s_salida.id
        LEFT JOIN insumo i ON m.insumo_id = i.id
        LEFT JOIN tipo_insumo ti ON i.id_tipo_insumo = ti.id
        LEFT JOIN insumo_presentacion ip ON i.id = ip.insumo_id
        LEFT JOIN presentacion p ON ip.presentacion_id = p.id
        WHERE m.fecha_registro BETWEEN %s AND %s
        """

        params = [fecha_ini, fecha_fin]

        # Filtrado estricto por nivel seleccionado
        if servicio:
            # Nivel servicio: solo movimientos con servicio específico
            query += " AND s.nombre = %s"
            params.append(servicio)
        elif tipo_servicio:
            # Nivel tipo servicio: movimientos con tipo servicio específico y sin servicio asignado
            query += " AND ts.descripcion = %s AND m.servicio_id IS NULL"
            params.append(tipo_servicio)
        elif distrito:
            # Nivel distrito: movimientos con distrito asignado y sin tipo servicio ni servicio
            query += " AND d2.nombre = %s AND ts.descripcion IS NULL AND m.servicio_id IS NULL"
            params.append(distrito)
        elif area:
            # Nivel área: movimientos con área asignada y sin distrito ni tipo servicio ni servicio
            query += " AND a2.nombre = %s AND d2.nombre IS NULL AND ts.descripcion IS NULL AND m.servicio_id IS NULL"
            params.append(area)

        # Filtros adicionales opcionales
        if tipo_insumo:
            query += " AND ti.descripcion = %s"
            params.append(tipo_insumo)
        if insumo:
            query += " AND i.nombre = %s"
            params.append(insumo)
        if presentacion:
            query += " AND p.nombre = %s"
            params.append(presentacion)
        if tipo_movimiento:
            query += " AND tm.descripcion = %s"
            params.append(tipo_movimiento)

        query += " ORDER BY m.fecha_registro ASC, m.id ASC"

        cursor.execute(query, params)
        resultados = cursor.fetchall()
        return resultados
    except Exception as e:
        print(f"Error en buscar_movimientos_por_filtros: {e}")
        return []
    finally:
        cursor.close()
        conn.close()
    
def actualizar_movimiento(mov_id, nuevos_datos):
    """
    Actualiza un movimiento existente con los nuevos datos proporcionados.

    Args:
    mov_id: ID del movimiento a actualizar
    nuevos_datos: Diccionario con los campos a actualizar

    Returns:
    bool: True si la actualización fue exitosa, False en caso contrario
    """
    conn = conectar_db()
    if not conn:
        return False

    try:
        cursor = conn.cursor(dictionary=True)

        # Primero obtenemos los datos actuales del movimiento
        cursor.execute("SELECT * FROM movimiento WHERE id = %s", (mov_id,))
        movimiento_actual = cursor.fetchone()
        if not movimiento_actual:
            return False

        # Preparamos los campos a actualizar
        campos_actualizables = []
        valores = []

        if 'fecha' in nuevos_datos:
            campos_actualizables.append("fecha_registro = %s")
            valores.append(nuevos_datos['fecha'])

        if 'referencia' in nuevos_datos:
            campos_actualizables.append("referencia = %s")
            valores.append(nuevos_datos['referencia'])

        if 'tipo_movimiento' in nuevos_datos:
            # Obtenemos el ID del tipo de movimiento
            cursor.execute("SELECT id FROM tipo_movimiento WHERE descripcion = %s",
            (nuevos_datos['tipo_movimiento'],))
            tipo_mov = cursor.fetchone()
        if tipo_mov:
            campos_actualizables.append("tipo_movimiento_id = %s")
            valores.append(tipo_mov['id'])

        if 'lote' in nuevos_datos:
            campos_actualizables.append("lote = %s")
            valores.append(nuevos_datos['lote'])

        if 'fecha_vencimiento' in nuevos_datos:
            campos_actualizables.append("fecha_vencimiento = %s")
            valores.append(nuevos_datos['fecha_vencimiento'])

        if 'cantidad' in nuevos_datos:
            campos_actualizables.append("cantidad = %s")
            valores.append(nuevos_datos['cantidad'])

        if 'observaciones' in nuevos_datos:
            campos_actualizables.append("observaciones = %s")
            valores.append(nuevos_datos['observaciones'])

        # Si no hay campos para actualizar, retornamos
        if not campos_actualizables:
            return False

        # Construimos la consulta SQL
        query = f"UPDATE movimiento SET {', '.join(campos_actualizables)} WHERE id = %s"
        valores.append(mov_id)

        # Ejecutamos la actualización
        cursor.execute(query, valores)
        conn.commit()

        return cursor.rowcount > 0

    except Error as e:
        print(f"Error al actualizar movimiento: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def eliminar_movimiento(mov_id):
    """
    Elimina un movimiento por su ID.

    Args:
    mov_id: ID del movimiento a eliminar

    Returns:
    bool: True si la eliminación fue exitosa, False en caso contrario
    """
    conn = conectar_db()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM movimiento WHERE id = %s", (mov_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Error as e:
        print(f"Error al eliminar movimiento: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()
    
# ---- OPERACIONES DEMANDA----

def obtener_movimientos_demanda_real(fecha_inicio, fecha_fin, distrito_nombre=None, tipo_servicio_desc=None,
    servicio_nombre=None, tipo_insumo_desc=None, insumo_nombre=None,
    presentacion_nombre=None):
    """
    Función específica para obtener movimientos para el reporte de demanda real
    Incluye todos los tipos de movimiento necesarios para el cálculo
    Maneja parámetros opcionales (pueden ser None)
    """
    conn = conectar_db()
    if not conn:
        return []

    try:
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT
        m.fecha_registro AS fecha,
        m.referencia,
        tm.descripcion AS tipo_movimiento,
        m.cantidad,
        m.lote,
        m.fecha_vencimiento,
        m.observaciones,
        d_salida.nombre AS distrito_destino,
        s_salida.nombre AS servicio_destino,
        i.id AS codigo_insumo,
        i.nombre AS nombre_insumo,
        COALESCE(i.lote, '') AS codigo,
        COALESCE(p.nombre, '') AS presentacion
        FROM movimiento m
        JOIN tipo_movimiento tm ON m.tipo_movimiento_id = tm.id
        LEFT JOIN servicio s ON m.servicio_id = s.id
        LEFT JOIN tipo_servicio ts ON s.id_tipo_servicio = ts.id
        LEFT JOIN distrito d ON ts.id_distrito = d.id
        LEFT JOIN distrito d_salida ON m.salida_distrito_id = d_salida.id
        LEFT JOIN servicio s_salida ON m.salida_servicio_id = s_salida.id
        LEFT JOIN insumo i ON m.insumo_id = i.id
        LEFT JOIN tipo_insumo ti ON i.id_tipo_insumo = ti.id
        LEFT JOIN insumo_presentacion ip ON i.id = ip.insumo_id
        LEFT JOIN presentacion p ON ip.presentacion_id = p.id
        WHERE m.fecha_registro BETWEEN %s AND %s
        AND tm.descripcion IN ('ENTREGADO', 'NO ENTREGADO', 'INVENTARIO INICIAL', 
        'ENTRADA NIVEL SUPERIOR', 'SALIDA NIVEL INFERIOR',
        'REAJUSTE POSITIVO', 'REAJUSTE NEGATIVO')
        """

        params = [fecha_inicio, fecha_fin]
        
        # Solo agregar filtros si los parámetros no son None y no están vacíos
        if distrito_nombre and distrito_nombre.strip():
            query += " AND d.nombre = %s"
            params.append(distrito_nombre)
        
        if tipo_servicio_desc and tipo_servicio_desc.strip():
            query += " AND ts.descripcion = %s"
            params.append(tipo_servicio_desc)
        
        if servicio_nombre and servicio_nombre.strip():
            query += " AND s.nombre = %s"
            params.append(servicio_nombre)
        
        if tipo_insumo_desc and tipo_insumo_desc.strip():
            query += " AND ti.descripcion = %s"
            params.append(tipo_insumo_desc)
        
        # Estos son opcionales - solo filtrar si se proporcionan
        if insumo_nombre and insumo_nombre.strip():
            query += " AND i.nombre = %s"
            params.append(insumo_nombre)
        
        if presentacion_nombre and presentacion_nombre.strip():
            query += " AND p.nombre = %s"
            params.append(presentacion_nombre)

        query += " ORDER BY m.fecha_registro ASC, m.id ASC"

        cursor.execute(query, params)
        resultados = cursor.fetchall()

        movimientos = []
        for row in resultados:
            movimientos.append({
            'fecha': row['fecha'],
            'referencia': row['referencia'],
            'tipo_movimiento': row['tipo_movimiento'],
            'cantidad': float(row['cantidad']) if row['cantidad'] else 0,
            'lote': row['lote'],
            'fecha_vencimiento': row['fecha_vencimiento'],
            'observaciones': row['observaciones'],
            'distrito_destino': row['distrito_destino'],
            'servicio_destino': row['servicio_destino'],
            'nombre_insumo': row['nombre_insumo'],
            'codigo': row['codigo'],
            'presentacion': row['presentacion']
            })

        return movimientos

    except Error as e:
        print(f"Error al obtener movimientos demanda real: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# ---- OPERACIONES BRES----

def obtener_movimientos_historicos(codigo_insumo, fecha_inicio, fecha_fin, distrito=None, tipo_servicio=None, servicio=None):
    """
    Obtiene los movimientos históricos de un insumo específico para calcular promedios
    """
    conn = conectar_db()
    if not conn:
        return []

    try:
        cursor = conn.cursor(dictionary=True)
        
        # Query base para obtener movimientos históricos
        query = """
        SELECT 
        tm.descripcion as tipo_movimiento,
        m.cantidad,
        m.fecha_registro as fecha,
        i.lote as codigo_insumo,
        i.nombre as nombre_insumo
        FROM movimiento m
        INNER JOIN insumo i ON m.insumo_id = i.id
        INNER JOIN tipo_movimiento tm ON m.tipo_movimiento_id = tm.id
        LEFT JOIN servicio s ON m.servicio_id = s.id
        LEFT JOIN tipo_servicio ts ON s.id_tipo_servicio = ts.id
        LEFT JOIN distrito d ON ts.id_distrito = d.id
        WHERE i.lote = %s
        AND m.fecha_registro BETWEEN %s AND %s
        AND tm.descripcion IN ('ENTREGADO', 'NO ENTREGADO')
        """
        
        params = [codigo_insumo, fecha_inicio, fecha_fin]
        
        # Agregar filtros opcionales
        if distrito:
            query += " AND d.nombre = %s"
            params.append(distrito)
        
        if tipo_servicio:
            query += " AND ts.descripcion = %s"
            params.append(tipo_servicio)
        
        if servicio:
            query += " AND s.nombre = %s"
            params.append(servicio)
        
        query += " ORDER BY m.fecha_registro"
        
        cursor.execute(query, params)
        resultados = cursor.fetchall()
        
        # Convertir a lista de diccionarios
        movimientos = []
        for row in resultados:
            movimientos.append({
            'tipo_movimiento': row['tipo_movimiento'],
            'cantidad': float(row['cantidad']) if row['cantidad'] else 0,
            'fecha': row['fecha'],
            'codigo_insumo': row['codigo_insumo'],
            'nombre_insumo': row['nombre_insumo']
            })
        
        return movimientos
    
    except Error as e:
        print(f"Error al obtener movimientos históricos: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def obtener_demanda_por_meses(codigo_insumo, fecha_inicio, fecha_fin, distrito=None, tipo_servicio=None, servicio=None):
    """
    Obtiene la demanda agrupada por mes para calcular promedios más precisos
    """
    conn = conectar_db()
    if not conn:
        return []

    try:
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT 
        YEAR(m.fecha_registro) as anio,
        MONTH(m.fecha_registro) as mes,
        SUM(m.cantidad) as demanda_total
        FROM movimiento m
        INNER JOIN insumo i ON m.insumo_id = i.id
        INNER JOIN tipo_movimiento tm ON m.tipo_movimiento_id = tm.id
        LEFT JOIN servicio s ON m.servicio_id = s.id
        LEFT JOIN tipo_servicio ts ON s.id_tipo_servicio = ts.id
        LEFT JOIN distrito d ON ts.id_distrito = d.id
        WHERE i.lote = %s
        AND m.fecha_registro BETWEEN %s AND %s
        AND tm.descripcion IN ('ENTREGADO', 'NO ENTREGADO')
        """
        
        params = [codigo_insumo, fecha_inicio, fecha_fin]
        
        # Agregar filtros opcionales
        if distrito:
            query += " AND d.nombre = %s"
            params.append(distrito)
        
        if tipo_servicio:
            query += " AND ts.descripcion = %s"
            params.append(tipo_servicio)
        
        if servicio:
            query += " AND s.nombre = %s"
            params.append(servicio)
        
        query += " GROUP BY YEAR(m.fecha_registro), MONTH(m.fecha_registro) ORDER BY anio, mes"
        
        cursor.execute(query, params)
        resultados = cursor.fetchall()
        
        # Convertir a lista de diccionarios
        demanda_mensual = []
        for row in resultados:
            demanda_mensual.append({
            'anio': int(row['anio']),
            'mes': int(row['mes']),
            'demanda_total': float(row['demanda_total']) if row['demanda_total'] else 0
            })
        
        return demanda_mensual
    
    except Error as e:
        print(f"Error al obtener demanda por meses: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def obtener_movimientos_bres(fecha_inicio, fecha_fin, area_nombre=None, distrito_nombre=None, tipo_servicio_desc=None,
    servicio_nombre=None, tipo_insumo_desc=None, insumo_nombre=None,
    presentacion_nombre=None):
    conn = conectar_db()
    if not conn:
        return []

    try:
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT
        m.fecha_registro AS fecha,
        m.referencia,
        tm.descripcion AS tipo_movimiento,
        m.cantidad,
        m.lote,
        m.fecha_vencimiento,
        m.observaciones,
        d_salida.nombre AS distrito_destino,
        s_salida.nombre AS servicio_destino,
        i.nombre AS nombre_insumo,
        i.id AS codigo_insumo,
        COALESCE(p.nombre, '') AS presentacion,
        a.nombre AS area_nombre,
        d.nombre AS distrito_nombre,
        ts.descripcion AS tipo_servicio_descripcion,
        s.nombre AS servicio_nombre
        FROM movimiento m
        JOIN tipo_movimiento tm ON m.tipo_movimiento_id = tm.id
        LEFT JOIN insumo i ON m.insumo_id = i.id
        LEFT JOIN tipo_insumo ti ON i.id_tipo_insumo = ti.id
        LEFT JOIN insumo_presentacion ip ON i.id = ip.insumo_id
        LEFT JOIN presentacion p ON ip.presentacion_id = p.id
        LEFT JOIN distrito d_salida ON m.salida_distrito_id = d_salida.id
        LEFT JOIN servicio s_salida ON m.salida_servicio_id = s_salida.id

        LEFT JOIN area a ON m.area_id = a.id
        LEFT JOIN distrito d ON m.distrito_id = d.id
        LEFT JOIN servicio s ON m.servicio_id = s.id
        LEFT JOIN tipo_servicio ts ON s.id_tipo_servicio = ts.id

        WHERE m.fecha_registro BETWEEN %s AND %s
        """

        params = [fecha_inicio, fecha_fin]

        # **LÓGICA DE FILTRADO MEJORADA PARA CONSOLIDACIÓN**
        if servicio_nombre:
            # Nivel SERVICIO: solo movimientos del servicio específico
            query += " AND s.nombre = %s"
            params.append(servicio_nombre)

        elif tipo_servicio_desc:
            # Nivel TIPO SERVICIO: todos los servicios del tipo
            query += " AND ts.descripcion = %s"
            params.append(tipo_servicio_desc)

        elif distrito_nombre:
            # Nivel DISTRITO: incluir movimientos del distrito Y de todos sus servicios
            query += """ AND (
            d.nombre = %s OR 
            s.id IN (
            SELECT serv.id 
            FROM servicio serv 
            INNER JOIN tipo_servicio ts_inner ON serv.id_tipo_servicio = ts_inner.id 
            INNER JOIN distrito d_inner ON ts_inner.id_distrito = d_inner.id 
            WHERE d_inner.nombre = %s
            )
            )"""
            params.extend([distrito_nombre, distrito_nombre])

        elif area_nombre:
            # Nivel ÁREA: incluir movimientos del área Y de todos sus distritos Y servicios
            query += """ AND (
            a.nombre = %s OR 
            d.id IN (
            SELECT dist.id 
            FROM distrito dist 
            INNER JOIN area a_inner ON dist.id_area = a_inner.id 
            WHERE a_inner.nombre = %s
            ) OR
            s.id IN (
            SELECT serv.id 
            FROM servicio serv 
            INNER JOIN tipo_servicio ts_inner ON serv.id_tipo_servicio = ts_inner.id 
            INNER JOIN distrito d_inner ON ts_inner.id_distrito = d_inner.id 
            INNER JOIN area a_inner ON d_inner.id_area = a_inner.id 
            WHERE a_inner.nombre = %s
            )
            )"""
            params.extend([area_nombre, area_nombre, area_nombre])

        # Filtros adicionales opcionales
        if tipo_insumo_desc:
            query += " AND ti.descripcion = %s"
            params.append(tipo_insumo_desc)

        if insumo_nombre:
            query += " AND i.nombre = %s"
            params.append(insumo_nombre)

        if presentacion_nombre:
            # Buscar la presentación en la tabla intermedia
            query += " AND p.nombre = %s"
            params.append(presentacion_nombre)

        query += " ORDER BY m.fecha_registro"

        cursor.execute(query, params)
        resultados = cursor.fetchall()

        movimientos = []
        for row in resultados:
            movimientos.append({
            'fecha': row['fecha'],
            'referencia': row['referencia'],
            'tipo_movimiento': row['tipo_movimiento'],
            'cantidad': float(row['cantidad']) if row['cantidad'] else 0,
            'lote': row['lote'],
            'fecha_vencimiento': row['fecha_vencimiento'],
            'observaciones': row['observaciones'],
            'distrito_destino': row['distrito_destino'],
            'servicio_destino': row['servicio_destino'],
            'nombre_insumo': row['nombre_insumo'],
            'codigo_insumo': row['codigo_insumo'],
            'presentacion': row['presentacion'],
            'area_nombre': row['area_nombre'],
            'distrito_nombre': row['distrito_nombre'],
            'tipo_servicio_descripcion': row['tipo_servicio_descripcion'],
            'servicio_nombre': row['servicio_nombre']
            })

        return movimientos

    except Exception as e:
        print(f"Error en obtener_movimientos_bres: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        cursor.close()
        conn.close()

def obtener_movimientos_balance(fecha_inicio, fecha_fin, area_nombre=None, distrito_nombre=None, tipo_servicio_desc=None,
    servicio_nombre=None, tipo_insumo_desc=None, insumo_nombre=None,
    presentacion_nombre=None):
    """
    Obtiene movimientos del balance filtrados por nivel exacto según cómo se guardan los datos
    """
    
    try:
        conn = conectar_db()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT
        m.fecha_registro AS fecha,
        m.referencia,
        tm.descripcion AS tipo_movimiento,
        m.cantidad,
        m.lote,
        m.fecha_vencimiento,
        m.observaciones,
        d_salida.nombre AS distrito_destino,
        s_salida.nombre AS servicio_destino,
        i.nombre AS nombre_insumo,
        i.id AS codigo_insumo,
        COALESCE(p.nombre, '') AS presentacion,
        a.nombre AS area_nombre,
        d.nombre AS distrito_nombre,
        ts.descripcion AS tipo_servicio_descripcion,
        s.nombre AS servicio_nombre
        FROM movimiento m
        JOIN tipo_movimiento tm ON m.tipo_movimiento_id = tm.id
        LEFT JOIN insumo i ON m.insumo_id = i.id
        LEFT JOIN tipo_insumo ti ON i.id_tipo_insumo = ti.id
        LEFT JOIN insumo_presentacion ip ON i.id = ip.insumo_id
        LEFT JOIN presentacion p ON ip.presentacion_id = p.id
        LEFT JOIN distrito d_salida ON m.salida_distrito_id = d_salida.id
        LEFT JOIN servicio s_salida ON m.salida_servicio_id = s_salida.id
        
        LEFT JOIN area a ON m.area_id = a.id
        LEFT JOIN distrito d ON m.distrito_id = d.id
        LEFT JOIN servicio s ON m.servicio_id = s.id
        LEFT JOIN tipo_servicio ts ON s.id_tipo_servicio = ts.id
        
        WHERE m.fecha_registro BETWEEN %s AND %s
        AND tm.descripcion IN ('INVENTARIO INICIAL', 'REAJUSTE POSITIVO', 'REAJUSTE NEGATIVO', 'ENTRADA NIVEL SUPERIOR', 'SALIDA NIVEL INFERIOR')
        """
        
        params = [fecha_inicio, fecha_fin]
        
        # Determinar el nivel más específico seleccionado
        if servicio_nombre:
            query += " AND s.nombre = %s"
            params.append(servicio_nombre)
        
        elif tipo_servicio_desc:
            query += " AND ts.descripcion = %s"
            params.append(tipo_servicio_desc)
        
        elif distrito_nombre:
            query += " AND d.nombre = %s AND m.servicio_id IS NULL"
            params.append(distrito_nombre)
        
        elif area_nombre:
            query += " AND a.nombre = %s AND m.distrito_id IS NULL"
            params.append(area_nombre)

        # Filtros adicionales opcionales
        if tipo_insumo_desc:
            query += " AND ti.descripcion = %s"
            params.append(tipo_insumo_desc)

        if insumo_nombre:
            query += " AND i.nombre = %s"
            params.append(insumo_nombre)

        if presentacion_nombre:
            query += " AND p.nombre = %s"
            params.append(presentacion_nombre)

        query += " ORDER BY m.fecha_registro"
        
        cursor.execute(query, params)
        resultados = cursor.fetchall()
        
        movimientos = []
        for row in resultados:
            movimientos.append({
                'fecha': row['fecha'],
                'referencia': row['referencia'],
                'tipo_movimiento': row['tipo_movimiento'],
                'cantidad': float(row['cantidad']) if row['cantidad'] else 0,
                'lote': row['lote'],
                'fecha_vencimiento': row['fecha_vencimiento'],
                'observaciones': row['observaciones'],
                'distrito_destino': row['distrito_destino'],
                'servicio_destino': row['servicio_destino'],
                'nombre_insumo': row['nombre_insumo'],
                'codigo_insumo': row['codigo_insumo'],
                'presentacion': row['presentacion'],
                'area_nombre': row['area_nombre'],
                'distrito_nombre': row['distrito_nombre'],
                'tipo_servicio_descripcion': row['tipo_servicio_descripcion'],
                'servicio_nombre': row['servicio_nombre']
            })

        return movimientos

    except Exception as e:
        print(f"Error en obtener_movimientos_balance: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        cursor.close()
        conn.close()