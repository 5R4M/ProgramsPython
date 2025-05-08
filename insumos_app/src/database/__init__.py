import sqlite3
import os

# Ruta donde se creará la base de datos
DB_PATH = os.path.join(os.path.dirname(__file__), '../../data/insumos.db')
DB_PATH = os.path.abspath(DB_PATH)

def asegurar_directorio():
    """Asegura que el directorio para la base de datos exista"""
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        return True
    except Exception as e:
        print(f"Error al crear el directorio: {e}")
        return False

def verificar_tablas():
    """Verifica que todas las tablas necesarias existan"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        tablas_requeridas = [
            'distrito',
            'tipo_servicio',
            'servicio',
            'tipo_insumo',
            'presentacion',
            'insumo',
            'tipo_movimiento',
            'movimiento'
        ]

        for tabla in tablas_requeridas:
            cursor.execute(f"""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='{tabla}'
            """)
            if not cursor.fetchone():
                return False
        return True

    except sqlite3.Error as e:
        print(f"Error al verificar tablas: {e}")
        return False
    finally:
        if conn:
            conn.close()

def crear_base_datos():
    """Crea la base de datos y sus tablas"""
    if not asegurar_directorio():
        raise Exception("No se pudo crear el directorio para la base de datos")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Habilitar las foreign keys
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Tabla ÁREA (se mantiene igual)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS area (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE
            );
        """)

        # Tabla DISTRICTO (se mantiene igual)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS distrito (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                id_area INTEGER NOT NULL,
                FOREIGN KEY (id_area) REFERENCES area(id),
                UNIQUE(id_area, nombre)
            );
        """)

        # Tabla TIPO_SERVICIO (se mantiene igual)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tipo_servicio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_distrito INTEGER NOT NULL,
                descripcion TEXT NOT NULL,
                FOREIGN KEY (id_distrito) REFERENCES distrito(id),
                UNIQUE(id_distrito, descripcion)
            );
        """)

        # Tabla SERVICIO (se mantiene igual)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS servicio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_tipo_servicio INTEGER NOT NULL,
                nombre TEXT NOT NULL,
                FOREIGN KEY (id_tipo_servicio) REFERENCES tipo_servicio(id),
                UNIQUE(id_tipo_servicio, nombre)
            );
        """)

        # Tabla TIPO_INSUMO (se mantiene igual)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tipo_insumo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL UNIQUE
            );
        """)

        # Tabla PRESENTACION (se mantiene igual)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS presentacion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE
            );
        """)

        # NUEVA TABLA INTERMEDIA INSUMO_PRESENTACION (nueva)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS insumo_presentacion (
                insumo_id INTEGER NOT NULL,
                presentacion_id INTEGER NOT NULL,
                PRIMARY KEY (insumo_id, presentacion_id),
                FOREIGN KEY (insumo_id) REFERENCES insumo(id),
                FOREIGN KEY (presentacion_id) REFERENCES presentacion(id)
            );
        """)

        # Tabla INSUMO (eliminamos id_presentacion)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS insumo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                lote TEXT,
                fecha_vencimiento DATE,
                id_tipo_insumo INTEGER NOT NULL,
                FOREIGN KEY (id_tipo_insumo) REFERENCES tipo_insumo(id)
            );
        """)

        # Tabla TIPO_MOVIMIENTO (se mantiene igual)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tipo_movimiento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL UNIQUE
            );
        """)

        # Tabla MOVIMIENTO (se mantiene igual, pero ahora debe referenciar presentacion_id si es necesario)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movimiento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_registro DATE NOT NULL,
                referencia TEXT NOT NULL,
                tipo_movimiento_id INTEGER NOT NULL,
                servicio_id INTEGER NOT NULL,
                insumo_id INTEGER NOT NULL,
                lote TEXT NOT NULL,
                fecha_vencimiento DATE NOT NULL,
                cantidad REAL NOT NULL,
                observaciones TEXT,
                FOREIGN KEY (tipo_movimiento_id) REFERENCES tipo_movimiento(id),
                FOREIGN KEY (servicio_id) REFERENCES servicio(id),
                FOREIGN KEY (insumo_id) REFERENCES insumo(id)
            );
        """)

        conn.commit()
        print(f"Base de datos creada correctamente en: {DB_PATH}")
        return True

    except sqlite3.Error as e:
        print(f"Error al crear la base de datos: {e}")
        return False
    finally:
        if conn:
            conn.close()

# Exportar las funciones necesarias
__all__ = ['DB_PATH', 'crear_base_datos', 'verificar_tablas', 'asegurar_directorio']