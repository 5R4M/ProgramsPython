import mysql.connector
import os
import sys
import configparser

def get_config_path(filename):
    # Igual que en tu login_window: al lado del .exe si está "frozen"
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        return os.path.join(exe_dir, filename)
    else:
        # En desarrollo: al lado de este script o ajusta según tu estructura
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, filename)

def load_mysql_config():
    # Defaults seguros (tu servidor real, no localhost)
    cfg = {
        'host': 'DESKTOP-KVJ8QQ3',
        'port': 3306,
        'user': 'root',
        'password': '0.5735',
        'database': 'insumos'
    }
    ini_path = get_config_path("mysql_config.ini")
    if os.path.exists(ini_path):
        parser = configparser.ConfigParser()
        parser.read(ini_path, encoding='utf-8')
        if 'MySQL' in parser:
            section = parser['MySQL']
            cfg['host'] = section.get('host', cfg['host'])
            cfg['port'] = int(section.get('port', cfg['port']))
            cfg['user'] = section.get('admin_user', cfg['user'])
            cfg['password'] = section.get('admin_pass', cfg['password'])
            cfg['database'] = section.get('database', cfg['database'])
    return cfg

def get_db_config():
    # Mantener interfaz, pero ahora leyendo del ini
    return load_mysql_config()

def asegurar_base_datos():
    """Asegura que la base de datos exista, si no, la crea"""
    config = get_db_config()
    conn = None
    try:
        # Conexión sin especificar database para poder crearla
        conn = mysql.connector.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password']
        )
        cursor = conn.cursor()
        dbname = config['database']
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{dbname}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except mysql.connector.Error as e:
        print(f"Error al crear la base de datos: {e.errno} - {e.msg}")
        return False
    finally:
        try:
            if conn and conn.is_connected():
                conn.close()
        except:
            pass

def verificar_tablas():
    """Verifica que todas las tablas necesarias existan"""
    config = get_db_config()
    conn = None
    try:
        conn = mysql.connector.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database']
        )
        cursor = conn.cursor()

        tablas_requeridas = [
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

        for tabla in tablas_requeridas:
            cursor.execute(f"SHOW TABLES LIKE %s;", (tabla,))
            if not cursor.fetchone():
                return False
        return True

    except mysql.connector.Error as e:
        print(f"Error al verificar tablas: {e.errno} - {e.msg}")
        return False
    finally:
        try:
            if conn and conn.is_connected():
                conn.close()
        except:
            pass

def agregar_columna_codigo_prefijo():
    """Agrega la columna codigo_prefijo a tipo_insumo si no existe"""
    config = get_db_config()
    conn = None
    try:
        conn = mysql.connector.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database']
        )
        cursor = conn.cursor()
        
        # Verificar si la columna ya existe
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = 'tipo_insumo'
            AND COLUMN_NAME = 'codigo_prefijo'
        """, (config['database'],))
        
        resultado = cursor.fetchone()
        
        if resultado[0] == 0:
            # La columna no existe, agregarla
            cursor.execute("""
                ALTER TABLE tipo_insumo
                ADD COLUMN codigo_prefijo VARCHAR(10) DEFAULT 'TEMP'
            """)
            conn.commit()
            return True
        else:
            return True
            
    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        return False
    finally:
        try:
            if conn and conn.is_connected():
                conn.close()
        except:
            pass

def crear_base_datos():
    """Crea las tablas en la base de datos MySQL"""
    if not asegurar_base_datos():
        raise Exception("No se pudo crear la base de datos")

    config = get_db_config()
    conn = None
    try:
        conn = mysql.connector.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database']
        )
        cursor = conn.cursor()

        # Tabla ÁREA
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS area (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(255) NOT NULL UNIQUE
            ) ENGINE=InnoDB;
        """)

        # Tabla DISTRITO
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS distrito (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(255) NOT NULL,
                id_area INT NOT NULL,
                UNIQUE KEY unique_area_nombre (id_area, nombre),
                FOREIGN KEY (id_area) REFERENCES area(id) ON DELETE CASCADE
            ) ENGINE=InnoDB;
        """)

        # Tabla TIPO_SERVICIO
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tipo_servicio (
                id INT AUTO_INCREMENT PRIMARY KEY,
                id_distrito INT NOT NULL,
                descripcion VARCHAR(255) NOT NULL,
                UNIQUE KEY unique_distrito_descripcion (id_distrito, descripcion),
                FOREIGN KEY (id_distrito) REFERENCES distrito(id) ON DELETE CASCADE
            ) ENGINE=InnoDB;
        """)

        # Tabla SERVICIO
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS servicio (
                id INT AUTO_INCREMENT PRIMARY KEY,
                id_tipo_servicio INT NOT NULL,
                nombre VARCHAR(255) NOT NULL,
                UNIQUE KEY unique_tipo_servicio_nombre (id_tipo_servicio, nombre),
                FOREIGN KEY (id_tipo_servicio) REFERENCES tipo_servicio(id) ON DELETE CASCADE
            ) ENGINE=InnoDB;
        """)

        # Tabla TIPO_INSUMO
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tipo_insumo (
                id INT AUTO_INCREMENT PRIMARY KEY,
                descripcion VARCHAR(255) NOT NULL UNIQUE,
                codigo_prefijo VARCHAR(10) DEFAULT 'TEMP'
            ) ENGINE=InnoDB;
        """)

        # Tabla PRESENTACION
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS presentacion (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(255) NOT NULL UNIQUE
            ) ENGINE=InnoDB;
        """)

        # Tabla INSUMO
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS insumo (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(255) NOT NULL,
                lote VARCHAR(255),
                fecha_vencimiento DATE,
                id_tipo_insumo INT NOT NULL,
                FOREIGN KEY (id_tipo_insumo) REFERENCES tipo_insumo(id) ON DELETE CASCADE
            ) ENGINE=InnoDB;
        """)

        # Tabla INSUMO_PRESENTACION
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS insumo_presentacion (
                insumo_id INT NOT NULL,
                presentacion_id INT NOT NULL,
                PRIMARY KEY (insumo_id, presentacion_id),
                FOREIGN KEY (insumo_id) REFERENCES insumo(id) ON DELETE CASCADE,
                FOREIGN KEY (presentacion_id) REFERENCES presentacion(id) ON DELETE CASCADE
            ) ENGINE=InnoDB;
        """)

        # Tabla TIPO_MOVIMIENTO
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tipo_movimiento (
                id INT AUTO_INCREMENT PRIMARY KEY,
                descripcion VARCHAR(255) NOT NULL UNIQUE
            ) ENGINE=InnoDB;
        """)

        # Tabla MOVIMIENTO
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movimiento (
                id INT AUTO_INCREMENT PRIMARY KEY,
                fecha_registro DATE NOT NULL,
                referencia VARCHAR(255) NOT NULL,
                tipo_movimiento_id INT NOT NULL,
                area_id INT,
                distrito_id INT,
                servicio_id INT,
                insumo_id INT NOT NULL,
                presentacion_id INT,
                lote VARCHAR(255),
                fecha_vencimiento DATE,
                cantidad DECIMAL(10,2) NOT NULL,
                observaciones TEXT,
                salida_distrito_id INT,
                salida_servicio_id INT,
                FOREIGN KEY (tipo_movimiento_id) REFERENCES tipo_movimiento(id) ON DELETE CASCADE,
                FOREIGN KEY (area_id) REFERENCES area(id) ON DELETE SET NULL,
                FOREIGN KEY (distrito_id) REFERENCES distrito(id) ON DELETE SET NULL,
                FOREIGN KEY (servicio_id) REFERENCES servicio(id) ON DELETE SET NULL,
                FOREIGN KEY (insumo_id) REFERENCES insumo(id) ON DELETE CASCADE,
                FOREIGN KEY (presentacion_id) REFERENCES presentacion(id) ON DELETE SET NULL,
                FOREIGN KEY (salida_distrito_id) REFERENCES distrito(id) ON DELETE SET NULL,
                FOREIGN KEY (salida_servicio_id) REFERENCES servicio(id) ON DELETE SET NULL
            ) ENGINE=InnoDB;
        """)

        # Tabla USUARIOS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                nombre_completo VARCHAR(255),
                rol ENUM('admin', 'usuario', 'super_admin') NOT NULL,
                activo BOOLEAN DEFAULT TRUE,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB;
        """)

        # Índices (ignora si ya existen)
        for index_sql in [
            "CREATE INDEX idx_mov_area ON movimiento(area_id);",
            "CREATE INDEX idx_mov_distrito ON movimiento(distrito_id);",
            "CREATE INDEX idx_mov_servicio ON movimiento(servicio_id);",
            "CREATE INDEX idx_mov_fecha ON movimiento(fecha_registro);"
        ]:
            try:
                cursor.execute(index_sql)
            except mysql.connector.Error as err:
                if err.errno == 1061:
                    pass
                else:
                    raise

        conn.commit()
        cursor.close()
        conn.close()
        
        # Agregar columna codigo_prefijo si no existe
        agregar_columna_codigo_prefijo()
        
        return True

    except mysql.connector.Error as e:
        return False
    finally:
        try:
            if conn and conn.is_connected():
                conn.close()
        except:
            pass

__all__ = ['crear_base_datos', 'verificar_tablas', 'asegurar_base_datos', 'agregar_columna_codigo_prefijo']

if __name__ == "__main__":
    if crear_base_datos():
        print("Base de datos creada con éxito")
    else:
        print("Error al crear la base de datos")