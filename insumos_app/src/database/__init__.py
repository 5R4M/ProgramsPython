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

def crear_base_datos():
    """Crea la base de datos y sus tablas"""
    if not asegurar_directorio():
        raise Exception("No se pudo crear el directorio para la base de datos")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Habilitar las foreign keys
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Tabla de Distritos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS distrito (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE
            );
        """)

        # Tabla de Tipo de Servicio
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tipo_servicio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_distrito INTEGER NOT NULL,
                descripcion TEXT NOT NULL,
                FOREIGN KEY (id_distrito) REFERENCES distrito(id),
                UNIQUE(id_distrito, descripcion)
            );
        """)

        # Tabla de Servicios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS servicio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_tipo_servicio INTEGER NOT NULL,
                nombre TEXT NOT NULL,
                FOREIGN KEY (id_tipo_servicio) REFERENCES tipo_servicio(id),
                UNIQUE(id_tipo_servicio, nombre)
            );
        """)

        # Tabla de Tipo de Insumo
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tipo_insumo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL UNIQUE
            );
        """)

        # Tabla de Presentación
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS presentacion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE
            );
        """)

        # Tabla de Tipo de Movimiento
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tipo_movimiento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL UNIQUE
            );
        """)

        # Tabla de Insumo
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS insumo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                lote TEXT,
                fecha_vencimiento DATE,
                id_tipo_insumo INTEGER NOT NULL,
                id_presentacion INTEGER NOT NULL,
                FOREIGN KEY (id_tipo_insumo) REFERENCES tipo_insumo(id),
                FOREIGN KEY (id_presentacion) REFERENCES presentacion(id)
            );
        """)

        # Tabla de Movimiento
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movimiento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_insumo INTEGER NOT NULL,
                id_servicio INTEGER NOT NULL,
                fecha_registro TEXT NOT NULL,
                referencia TEXT NOT NULL,
                cantidad REAL NOT NULL,
                observaciones TEXT,
                id_tipo_movimiento INTEGER NOT NULL,
                FOREIGN KEY (id_insumo) REFERENCES insumo(id),
                FOREIGN KEY (id_servicio) REFERENCES servicio(id),
                FOREIGN KEY (id_tipo_movimiento) REFERENCES tipo_movimiento(id)
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

if __name__ == "__main__":
    crear_base_datos()