import sqlite3
import os
from datetime import datetime

# Ruta de la base de datos
DB_PATH = os.path.join(os.path.dirname(__file__), '../../data/insumos.db')
DB_PATH = os.path.abspath(DB_PATH)

def conectar_db():
    """Establece una conexión a la base de datos."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Permite acceder a las columnas por nombre
        return conn
    except sqlite3.Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

# -------------------- OPERACIONES DISTRITO --------------------

def obtener_distritos():
    """Obtiene todos los distritos."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre FROM distrito ORDER BY nombre")
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener distritos: {e}")
            return None
        finally:
            conn.close()

def agregar_distrito(nombre):
    """Agrega un nuevo distrito."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO distrito (nombre) VALUES (?)", (nombre,))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error al agregar distrito: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

def actualizar_distrito(id_distrito, nuevo_nombre):
    """Actualiza el nombre de un distrito."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE distrito SET nombre = ? WHERE id = ?",
                         (nuevo_nombre, id_distrito))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error al actualizar distrito: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

def eliminar_distrito(id_distrito):
    """Elimina un distrito."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM distrito WHERE id = ?", (id_distrito,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error al eliminar distrito: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

# -------------------- OPERACIONES TIPO SERVICIO --------------------

def obtener_tipos_servicio_por_distrito(id_distrito):
    """Obtiene todos los tipos de servicio de un distrito específico."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, descripcion
                FROM tipo_servicio
                WHERE id_distrito = ?
                ORDER BY descripcion""", (id_distrito,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener tipos de servicio: {e}")
            return None
        finally:
            conn.close()

def agregar_tipo_servicio(id_distrito, descripcion):
    """Agrega un nuevo tipo de servicio."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tipo_servicio (id_distrito, descripcion)
                VALUES (?, ?)""", (id_distrito, descripcion))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error al agregar tipo de servicio: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

# -------------------- OPERACIONES SERVICIO --------------------

def obtener_servicios_por_tipo(id_tipo_servicio):
    """Obtiene todos los servicios de un tipo de servicio específico."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, nombre
                FROM servicio
                WHERE id_tipo_servicio = ?
                ORDER BY nombre""", (id_tipo_servicio,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener servicios: {e}")
            return None
        finally:
            conn.close()

def agregar_servicio(id_tipo_servicio, nombre):
    """Agrega un nuevo servicio."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO servicio (id_tipo_servicio, nombre)
                VALUES (?, ?)""", (id_tipo_servicio, nombre))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error al agregar servicio: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

# -------------------- OPERACIONES TIPO INSUMO --------------------

def obtener_tipos_insumo():
    """Obtiene todos los tipos de insumo."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, descripcion FROM tipo_insumo ORDER BY descripcion")
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener tipos de insumo: {e}")
            return None
        finally:
            conn.close()

def agregar_tipo_insumo(descripcion):
    """Agrega un nuevo tipo de insumo."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO tipo_insumo (descripcion) VALUES (?)",
                         (descripcion,))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error al agregar tipo de insumo: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

# -------------------- OPERACIONES PRESENTACION --------------------

def obtener_presentaciones():
    """Obtiene todas las presentaciones."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre FROM presentacion ORDER BY nombre")
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener presentaciones: {e}")
            return None
        finally:
            conn.close()

def agregar_presentacion(nombre):
    """Agrega una nueva presentación."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO presentacion (nombre) VALUES (?)", (nombre,))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error al agregar presentación: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

def actualizar_presentacion(id_presentacion, nuevo_nombre):
    """Actualiza el nombre de una presentación."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE presentacion SET nombre = ? WHERE id = ?",
                         (nuevo_nombre, id_presentacion))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error al actualizar presentación: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

def eliminar_presentacion(id_presentacion):
    """Elimina una presentación."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM presentacion WHERE id = ?", (id_presentacion,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error al eliminar presentación: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

# -------------------- OPERACIONES INSUMO --------------------

def obtener_insumos_por_tipo(id_tipo_insumo):
    """Obtiene todos los insumos de un tipo específico."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT i.id, i.nombre, i.lote, p.nombre as presentacion,
                       i.fecha_vencimiento
                FROM insumo i
                JOIN presentacion p ON i.id_presentacion = p.id
                WHERE i.id_tipo_insumo = ?
                ORDER BY i.nombre""", (id_tipo_insumo,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener insumos: {e}")
            return None
        finally:
            conn.close()

def agregar_insumo(nombre, lote, id_presentacion, fecha_vencimiento, id_tipo_insumo):
    """Agrega un nuevo insumo."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO insumo (nombre, lote, id_presentacion,
                                  fecha_vencimiento, id_tipo_insumo)
                VALUES (?, ?, ?, ?, ?)""",
                (nombre, lote, id_presentacion, fecha_vencimiento, id_tipo_insumo))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error al agregar insumo: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

def actualizar_insumo(id_insumo, nombre, lote, id_presentacion, fecha_vencimiento, id_tipo_insumo):
    """Actualiza un insumo existente."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE insumo
                SET nombre = ?,
                    lote = ?,
                    id_presentacion = ?,
                    fecha_vencimiento = ?,
                    id_tipo_insumo = ?
                WHERE id = ?""",
                (nombre, lote, id_presentacion, fecha_vencimiento, id_tipo_insumo, id_insumo))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error al actualizar insumo: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

def obtener_insumo_por_id(id_insumo):
    """Obtiene un insumo específico por su ID."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT i.id, i.nombre, i.lote, i.id_presentacion,
                       p.nombre as nombre_presentacion,
                       i.fecha_vencimiento, i.id_tipo_insumo,
                       t.descripcion as tipo_insumo
                FROM insumo i
                JOIN presentacion p ON i.id_presentacion = p.id
                JOIN tipo_insumo t ON i.id_tipo_insumo = t.id
                WHERE i.id = ?""", (id_insumo,))
            return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Error al obtener insumo: {e}")
            return None
        finally:
            conn.close()

# -------------------- OPERACIONES MOVIMIENTO --------------------

def obtener_tipos_movimiento():
    """Obtiene todos los tipos de movimiento."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, descripcion FROM tipo_movimiento ORDER BY descripcion")
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener tipos de movimiento: {e}")
            return None
        finally:
            conn.close()

def registrar_movimiento(id_insumo, id_servicio, cantidad, id_tipo_movimiento):
    """Registra un nuevo movimiento."""
    conn = conectar_db()
    if conn:
        try:
            fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO movimiento (id_insumo, id_servicio, fecha_registro,
                                      cantidad, id_tipo_movimiento)
                VALUES (?, ?, ?, ?, ?)""",
                (id_insumo, id_servicio, fecha_actual, cantidad, id_tipo_movimiento))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error al registrar movimiento: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

def obtener_movimientos_por_servicio(id_servicio):
    """Obtiene todos los movimientos de un servicio específico."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.id, m.fecha_registro, i.nombre as insumo,
                       m.cantidad, tm.descripcion as tipo_movimiento
                FROM movimiento m
                JOIN insumo i ON m.id_insumo = i.id
                JOIN tipo_movimiento tm ON m.id_tipo_movimiento = tm.id
                WHERE m.id_servicio = ?
                ORDER BY m.fecha_registro DESC""", (id_servicio,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener movimientos: {e}")
            return None
        finally:
            conn.close()