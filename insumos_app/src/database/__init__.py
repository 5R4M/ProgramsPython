import sqlite3
import os

# Ruta donde se creará la base de datos
DB_PATH = os.path.join(os.path.dirname(__file__), '../../data/insumos.db')
DB_PATH = os.path.abspath(DB_PATH)

def crear_base_datos():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabla de Distritos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS distrito (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        );
    """)

    # Tabla de Tipo de Servicio (relacionada con Distrito)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tipo_servicio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_distrito INTEGER NOT NULL,
            descripcion TEXT NOT NULL,
            FOREIGN KEY (id_distrito) REFERENCES distrito(id),
            UNIQUE(id_distrito, descripcion)
        );
    """)

    # Tabla de Servicios (relacionada con Tipo de Servicio)
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

    # Tabla de Insumo (relacionada con Tipo de Insumo)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS insumo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            lote TEXT,
            presentacion TEXT,
            fecha_vencimiento TEXT,
            id_tipo_insumo INTEGER NOT NULL,
            FOREIGN KEY (id_tipo_insumo) REFERENCES tipo_insumo(id)
        );
    """)

    # Tabla de Tipo de Movimiento
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tipo_movimiento (
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

    # Tabla de Insumo (modificada para relacionarse con presentacion)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS insumo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            lote TEXT,
            id_presentacion INTEGER NOT NULL,
            fecha_vencimiento TEXT,
            id_tipo_insumo INTEGER NOT NULL,
            FOREIGN KEY (id_tipo_insumo) REFERENCES tipo_insumo(id),
            FOREIGN KEY (id_presentacion) REFERENCES presentacion(id)
        );
    """)
    
    # Tabla de Tipo de Movimiento
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tipo_movimiento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL UNIQUE
        );
    """)

    # Tabla de Movimiento (relacionada con Insumo, Servicio y Tipo de Movimiento)
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
    conn.close()
    print(f"Base de datos creada correctamente en: {DB_PATH}")

if __name__ == "__main__":
    crear_base_datos()