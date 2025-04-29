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
        conn.execute("PRAGMA foreign_keys = ON")  # Habilitar foreign keys
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
    """Elimina un distrito y todos sus servicios relacionados."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            # Primero obtener todos los tipos de servicio del distrito
            cursor.execute("SELECT id FROM tipo_servicio WHERE id_distrito = ?", (id_distrito,))
            tipos_servicio = cursor.fetchall()

            # Eliminar servicios de cada tipo de servicio
            for tipo in tipos_servicio:
                cursor.execute("DELETE FROM servicio WHERE id_tipo_servicio = ?", (tipo['id'],))

            # Eliminar tipos de servicio
            cursor.execute("DELETE FROM tipo_servicio WHERE id_distrito = ?", (id_distrito,))

            # Finalmente eliminar el distrito
            cursor.execute("DELETE FROM distrito WHERE id = ?", (id_distrito,))

            conn.commit()
            return True
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

def actualizar_tipo_servicio(id_tipo_servicio, nueva_descripcion):
    """Actualiza la descripción de un tipo de servicio."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tipo_servicio
                SET descripcion = ?
                WHERE id = ?""", (nueva_descripcion, id_tipo_servicio))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error al actualizar tipo de servicio: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

def eliminar_tipo_servicio(id_tipo_servicio):
    """Elimina un tipo de servicio y sus servicios relacionados."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            # Primero eliminar servicios relacionados
            cursor.execute("DELETE FROM servicio WHERE id_tipo_servicio = ?",
                         (id_tipo_servicio,))
            # Luego eliminar el tipo de servicio
            cursor.execute("DELETE FROM tipo_servicio WHERE id = ?",
                         (id_tipo_servicio,))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error al eliminar tipo de servicio: {e}")
            conn.rollback()
            return False
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
            return cursor.fetchall() or []  # Retorna lista vacía si no hay resultados
        except sqlite3.Error as e:
            print(f"Error al obtener servicios: {e}")
            return []  # Retorna lista vacía en caso de error
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

def actualizar_servicio(id_servicio, nuevo_nombre):
    """Actualiza el nombre de un servicio."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE servicio
                SET nombre = ?
                WHERE id = ?""", (nuevo_nombre, id_servicio))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error al actualizar servicio: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

def eliminar_servicio(id_servicio):
    """Elimina un servicio."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM servicio WHERE id = ?", (id_servicio,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error al eliminar servicio: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

# -------------------- FUNCIONES DE BÚSQUEDA POR NOMBRE --------------------

def obtener_tipo_servicio_por_descripcion(descripcion, id_distrito):
    """Obtiene un tipo de servicio por su descripción y distrito."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, descripcion
                FROM tipo_servicio
                WHERE descripcion = ? AND id_distrito = ?""",
                (descripcion, id_distrito))
            return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Error al obtener tipo de servicio: {e}")
            return None
        finally:
            conn.close()

def obtener_servicio_por_nombre(nombre, id_tipo_servicio):
    """Obtiene un servicio por su nombre y tipo de servicio."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, nombre
                FROM servicio
                WHERE nombre = ? AND id_tipo_servicio = ?""",
                (nombre, id_tipo_servicio))
            return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Error al obtener servicio: {e}")
            return None
        finally:
            conn.close()

def obtener_distrito_por_nombre(nombre):
    """Obtiene un distrito por su nombre."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, nombre
                FROM distrito
                WHERE nombre = ?""", (nombre,))
            return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Error al obtener distrito: {e}")
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
            return []  # Retornar lista vacía en lugar de None
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

def actualizar_tipo_insumo(id_tipo_insumo, nueva_descripcion):
    """Actualiza la descripción de un tipo de insumo."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tipo_insumo
                SET descripcion = ?
                WHERE id = ?""", (nueva_descripcion, id_tipo_insumo))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error al actualizar tipo de insumo: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

def eliminar_tipo_insumo(id_tipo_insumo):
    """Elimina un tipo de insumo y sus insumos relacionados."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            # Primero eliminar insumos relacionados
            cursor.execute("DELETE FROM insumo WHERE id_tipo_insumo = ?", (id_tipo_insumo,))
            # Luego eliminar el tipo de insumo
            cursor.execute("DELETE FROM tipo_insumo WHERE id = ?", (id_tipo_insumo,))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error al eliminar tipo de insumo: {e}")
            conn.rollback()
            return False
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
            return cursor.fetchall() or []  # Retorna lista vacía si no hay resultados
        except sqlite3.Error as e:
            print(f"Error al obtener presentaciones: {e}")
            return []  # Retorna lista vacía en caso de error
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

def obtener_id_distrito(nombre_distrito):
    """Obtiene el ID de un distrito por su nombre."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM distrito WHERE nombre = ?", (nombre_distrito,))
            resultado = cursor.fetchone()
            return resultado['id'] if resultado else None
        except sqlite3.Error as e:
            print(f"Error al obtener ID del distrito: {e}")
            return None
        finally:
            conn.close()

def obtener_id_tipo_servicio(descripcion):
    """Obtiene el ID de un tipo de servicio por su descripción."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM tipo_servicio WHERE descripcion = ?", (descripcion,))
            resultado = cursor.fetchone()
            return resultado['id'] if resultado else None
        except sqlite3.Error as e:
            print(f"Error al obtener ID del tipo de servicio: {e}")
            return None
        finally:
            conn.close()

def obtener_id_servicio(nombre):
    """Obtiene el ID de un servicio por su nombre."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM servicio WHERE nombre = ?", (nombre,))
            resultado = cursor.fetchone()
            return resultado['id'] if resultado else None
        except sqlite3.Error as e:
            print(f"Error al obtener ID del servicio: {e}")
            return None
        finally:
            conn.close()

def obtener_id_tipo_insumo(descripcion):
    """Obtiene el ID de un tipo de insumo por su descripción."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM tipo_insumo WHERE descripcion = ?", (descripcion,))
            resultado = cursor.fetchone()
            return resultado['id'] if resultado else None
        except sqlite3.Error as e:
            print(f"Error al obtener ID del tipo de insumo: {e}")
            return None
        finally:
            conn.close()

def obtener_id_insumo(nombre):
    """Obtiene el ID de un insumo por su nombre."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM insumo WHERE nombre = ?", (nombre,))
            resultado = cursor.fetchone()
            return resultado['id'] if resultado else None
        except sqlite3.Error as e:
            print(f"Error al obtener ID del insumo: {e}")
            return None
        finally:
            conn.close()

def obtener_id_presentacion(nombre):
    """Obtiene el ID de una presentación por su nombre."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM presentacion WHERE nombre = ?", (nombre,))
            resultado = cursor.fetchone()
            return resultado['id'] if resultado else None
        except sqlite3.Error as e:
            print(f"Error al obtener ID de la presentación: {e}")
            return None
        finally:
            conn.close()

def obtener_id_tipo_movimiento(descripcion):
    """Obtiene el ID de un tipo de movimiento por su descripción."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM tipo_movimiento WHERE descripcion = ?", (descripcion,))
            resultado = cursor.fetchone()
            return resultado['id'] if resultado else None
        except sqlite3.Error as e:
            print(f"Error al obtener ID del tipo de movimiento: {e}")
            return None
        finally:
            conn.close()

def guardar_movimiento(movimiento_data):
    """
    Guarda un nuevo movimiento en la base de datos.

    Args:
        movimiento_data (dict): Diccionario con los datos del movimiento
    """
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
            INSERT INTO movimiento (
                fecha_registro,
                referencia,
                id_tipo_movimiento,
                id_distrito,
                id_tipo_servicio,
                id_servicio,
                id_tipo_insumo,
                id_insumo,
                id_presentacion,
                lote,
                fecha_vencimiento,
                cantidad,
                observaciones
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            cursor.execute(query, (
                movimiento_data['fecha_registro'],
                movimiento_data['referencia'],
                movimiento_data['tipo_movimiento_id'],
                movimiento_data['distrito_id'],
                movimiento_data['tipo_servicio_id'],
                movimiento_data['servicio_id'],
                movimiento_data['tipo_insumo_id'],
                movimiento_data['insumo_id'],
                movimiento_data['presentacion_id'],
                movimiento_data['lote'],
                movimiento_data['fecha_vencimiento'],
                movimiento_data['cantidad'],
                movimiento_data['observaciones']
            ))

            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error al guardar el movimiento: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

def obtener_insumos_por_tipo(id_tipo_insumo):
    """Obtiene todos los insumos de un tipo específico."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT i.id, i.nombre, i.lote, i.fecha_vencimiento,
                   p.nombre as nombre_presentacion
            FROM insumo i
            LEFT JOIN presentacion p ON i.id_presentacion = p.id
            WHERE i.id_tipo_insumo = ?
        """, (id_tipo_insumo,))

        insumos = [dict(row) for row in cursor.fetchall()]
        return insumos

    except sqlite3.Error as e:
        print(f"Error al obtener insumos: {e}")
        return None
    finally:
        if conn:
            conn.close()

def agregar_insumo(nombre, lote, id_presentacion, fecha_vencimiento, id_tipo_insumo):
    """Agrega un nuevo insumo."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO insumo (nombre, lote, id_presentacion, fecha_vencimiento, id_tipo_insumo)
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

def eliminar_insumo(id_insumo):
    """Elimina un insumo."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM insumo WHERE id = ?", (id_insumo,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error al eliminar insumo: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

# -------------------- FUNCIONES DE BÚSQUEDA POR NOMBRE (ADICIONALES) --------------------

def obtener_tipo_insumo_por_descripcion(descripcion):
    """Obtiene un tipo de insumo por su descripción."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, descripcion
                FROM tipo_insumo
                WHERE descripcion = ?""", (descripcion,))
            return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Error al obtener tipo de insumo: {e}")
            return None
        finally:
            conn.close()

def obtener_insumo_por_nombre(nombre, id_tipo_insumo):
    """Obtiene un insumo por su nombre y tipo de insumo."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, nombre
                FROM insumo
                WHERE nombre = ? AND id_tipo_insumo = ?""",
                (nombre, id_tipo_insumo))
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
            return cursor.fetchall() or []  # Retorna lista vacía si no hay resultados
        except sqlite3.Error as e:
            print(f"Error al obtener tipos de movimiento: {e}")
            return []  # Retorna lista vacía en caso de error
        finally:
            conn.close()

def registrar_movimiento(id_insumo, id_servicio, cantidad, id_tipo_movimiento, referencia, observaciones=None):
    """Registra un nuevo movimiento."""
    conn = conectar_db()
    if conn:
        try:
            fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO movimiento (
                    id_insumo,
                    id_servicio,
                    fecha_registro,
                    cantidad,
                    id_tipo_movimiento,
                    referencia,
                    observaciones
                ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (id_insumo, id_servicio, fecha_actual, cantidad,
                 id_tipo_movimiento, referencia, observaciones))
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
            
def obtener_movimientos_kardex(fecha_inicial, fecha_final, distrito=None, tipo_servicio=None,
                             servicio=None, tipo_insumo=None, insumo=None, presentacion=None):
    """Obtiene los movimientos para el reporte Kardex."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()

            # Construir la consulta base
            query = """
                SELECT
                    strftime('%d/%m/%Y', m.fecha_registro) as fecha,
                    m.id as numero_referencia,
                    tm.descripcion as remitente_destinatario,
                    CASE
                        WHEN tm.descripcion = 'Entrada' THEN m.cantidad
                        ELSE NULL
                    END as entrada,
                    i.lote,
                    CASE
                        WHEN i.fecha_vencimiento IS NOT NULL
                        THEN strftime('%d/%m/%Y', i.fecha_vencimiento)
                        ELSE NULL
                    END as fecha_vencimiento,
                    CASE
                        WHEN tm.descripcion IN ('Salida', 'Entregado') THEN m.cantidad
                        ELSE NULL
                    END as salida,
                    CASE
                        WHEN tm.descripcion = 'Reajuste Negativo' THEN -m.cantidad
                        WHEN tm.descripcion = 'Reajuste Positivo' THEN m.cantidad
                        ELSE NULL
                    END as reajuste,
                    m.observaciones,
                    i.nombre as insumo,
                    p.nombre as presentacion,
                    ti.descripcion as tipo_insumo,
                    s.nombre as servicio,
                    ts.descripcion as tipo_servicio,
                    d.nombre as distrito
                FROM movimiento m
                JOIN insumo i ON m.id_insumo = i.id
                JOIN tipo_movimiento tm ON m.id_tipo_movimiento = tm.id
                JOIN servicio s ON m.id_servicio = s.id
                JOIN tipo_servicio ts ON s.id_tipo_servicio = ts.id
                JOIN distrito d ON ts.id_distrito = d.id
                JOIN tipo_insumo ti ON i.id_tipo_insumo = ti.id
                LEFT JOIN presentacion p ON i.id_presentacion = p.id
                WHERE m.fecha_registro BETWEEN ? AND ?
            """

            params = [fecha_inicial, fecha_final]

            # Agregar filtros adicionales si se proporcionan
            if distrito:
                query += " AND d.nombre = ?"
                params.append(distrito)
            if tipo_servicio:
                query += " AND ts.descripcion = ?"
                params.append(tipo_servicio)
            if servicio:
                query += " AND s.nombre = ?"
                params.append(servicio)
            if tipo_insumo:
                query += " AND ti.descripcion = ?"
                params.append(tipo_insumo)
            if insumo:
                query += " AND i.nombre = ?"
                params.append(insumo)
            if presentacion:
                query += " AND p.nombre = ?"
                params.append(presentacion)

            query += " ORDER BY m.fecha_registro"

            cursor.execute(query, params)
            movimientos = cursor.fetchall()

            # Calcular saldos acumulados
            saldo = 0
            movimientos_con_saldo = []

            for mov in movimientos:
                mov_dict = dict(mov)
                # Calcular el saldo
                entrada = mov_dict['entrada'] or 0
                salida = mov_dict['salida'] or 0
                reajuste = mov_dict['reajuste'] or 0

                saldo += entrada - salida + reajuste
                mov_dict['saldo'] = saldo

                movimientos_con_saldo.append(mov_dict)

            return movimientos_con_saldo

        except sqlite3.Error as e:
            print(f"Error al obtener movimientos Kardex: {e}")
            return None
        finally:
            conn.close()

def obtener_tipos_movimiento():
    """Obtiene todos los tipos de movimiento."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, descripcion
                FROM tipo_movimiento
                ORDER BY descripcion
            """)
            tipos = cursor.fetchall()
            return [{'id': t['id'], 'descripcion': t['descripcion']} for t in tipos]
        except sqlite3.Error as e:
            print(f"Error al obtener tipos de movimiento: {e}")
            return None
        finally:
            conn.close()

def agregar_tipo_movimiento(descripcion):
    """Agrega un nuevo tipo de movimiento."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tipo_movimiento (descripcion)
                VALUES (?)
            """, (descripcion,))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error al agregar tipo de movimiento: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

def actualizar_tipo_movimiento(id_tipo, descripcion):
    """Actualiza un tipo de movimiento existente."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tipo_movimiento
                SET descripcion = ?
                WHERE id = ?
            """, (descripcion, id_tipo))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error al actualizar tipo de movimiento: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

def eliminar_tipo_movimiento(id_tipo):
    """Elimina un tipo de movimiento."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM tipo_movimiento WHERE id = ?
            """, (id_tipo,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error al eliminar tipo de movimiento: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

# -------------------- VERIFICACION DE DATOS BD --------------------

def verificar_conexion():
    """Verifica si se puede establecer conexión con la base de datos."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()
    return False

def verificar_tablas():
    """Verifica que todas las tablas necesarias existan."""
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            tablas = [
                'distrito',
                'tipo_servicio',
                'servicio',
                'tipo_insumo',
                'presentacion',
                'tipo_movimiento',
                'insumo',
                'movimiento'
            ]

            for tabla in tablas:
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
            conn.close()
    return False