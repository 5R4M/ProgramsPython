import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '../../data/insumos.db')
DB_PATH = os.path.abspath(DB_PATH)

def conectar_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

# -------------------- OPERACIONES ÁREA --------------------

def obtener_areas():
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre FROM area ORDER BY nombre")
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener áreas: {e}")
            return []
        finally:
            conn.close()

def agregar_area(nombre):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM area WHERE nombre = ?", (nombre,))
            existente = cursor.fetchone()
            if existente:
                return existente['id']
            cursor.execute("INSERT INTO area (nombre) VALUES (?)", (nombre,))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error al agregar área: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

def actualizar_area(id_area, nuevo_nombre):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE area SET nombre = ? WHERE id = ?", (nuevo_nombre, id_area))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error al actualizar área: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

def eliminar_area(id_area):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            # Eliminar distritos y cascada servicios
            cursor.execute("SELECT id FROM distrito WHERE id_area = ?", (id_area,))
            distritos = cursor.fetchall()
            for distrito in distritos:
                eliminar_distrito(distrito['id'])
            cursor.execute("DELETE FROM area WHERE id = ?", (id_area,))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error al eliminar área: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

# -------------------- OPERACIONES DISTRITO --------------------

def obtener_distritos():
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.id, d.nombre, a.nombre AS area_nombre
                FROM distrito d
                LEFT JOIN area a ON d.id_area = a.id
                ORDER BY d.nombre
            """)
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener distritos: {e}")
            return []
        finally:
            conn.close()

def obtener_distritos_por_area(id_area):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, nombre FROM distrito WHERE id_area = ? ORDER BY nombre
            """, (id_area,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener distritos por área: {e}")
            return []
        finally:
            conn.close()

def agregar_distrito(nombre, id_area=None):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM distrito WHERE nombre = ? AND id_area IS ?", (nombre, id_area))
            existente = cursor.fetchone()
            if existente:
                return existente['id']
            cursor.execute("INSERT INTO distrito (nombre, id_area) VALUES (?, ?)", (nombre, id_area))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error al agregar distrito: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

def actualizar_distrito(id_distrito, nuevo_nombre, id_area=None):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            if id_area is not None:
                cursor.execute("UPDATE distrito SET nombre = ?, id_area = ? WHERE id = ?", (nuevo_nombre, id_area, id_distrito))
            else:
                cursor.execute("UPDATE distrito SET nombre = ? WHERE id = ?", (nuevo_nombre, id_distrito))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error al actualizar distrito: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

def eliminar_distrito(id_distrito):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM tipo_servicio WHERE id_distrito = ?", (id_distrito,))
            tipos_servicio = cursor.fetchall()
            for tipo in tipos_servicio:
                eliminar_tipo_servicio(tipo['id'])
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
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, descripcion FROM tipo_servicio WHERE id_distrito = ? ORDER BY descripcion", (id_distrito,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener tipos de servicio: {e}")
            return []
        finally:
            conn.close()

def agregar_tipo_servicio(id_distrito, descripcion):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO tipo_servicio (id_distrito, descripcion) VALUES (?, ?)", (id_distrito, descripcion))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error al agregar tipo de servicio: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

def actualizar_tipo_servicio(id_tipo_servicio, nueva_descripcion):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE tipo_servicio SET descripcion = ? WHERE id = ?", (nueva_descripcion, id_tipo_servicio))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error al actualizar tipo de servicio: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

def eliminar_tipo_servicio(id_tipo_servicio):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM servicio WHERE id_tipo_servicio = ?", (id_tipo_servicio,))
            cursor.execute("DELETE FROM tipo_servicio WHERE id = ?", (id_tipo_servicio,))
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
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre FROM servicio WHERE id_tipo_servicio = ? ORDER BY nombre", (id_tipo_servicio,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener servicios: {e}")
            return []
        finally:
            conn.close()

def agregar_servicio(id_tipo_servicio, nombre):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO servicio (id_tipo_servicio, nombre) VALUES (?, ?)", (id_tipo_servicio, nombre))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error al agregar servicio: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

def actualizar_servicio(id_servicio, nuevo_nombre):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE servicio SET nombre = ? WHERE id = ?", (nuevo_nombre, id_servicio))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error al actualizar servicio: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

def eliminar_servicio(id_servicio):
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

# -------------------- OPERACIONES TIPO INSUMO --------------------

def obtener_tipos_insumo():
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, descripcion FROM tipo_insumo ORDER BY descripcion")
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener tipos de insumo: {e}")
            return []
        finally:
            conn.close()

def agregar_tipo_insumo(descripcion):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM tipo_insumo WHERE descripcion = ?", (descripcion,))
            existente = cursor.fetchone()
            if existente:
                return existente['id']
            cursor.execute("INSERT INTO tipo_insumo (descripcion) VALUES (?)", (descripcion,))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error al agregar tipo de insumo: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

def actualizar_tipo_insumo(id_tipo_insumo, nueva_descripcion):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE tipo_insumo SET descripcion = ? WHERE id = ?", (nueva_descripcion, id_tipo_insumo))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error al actualizar tipo de insumo: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

def eliminar_tipo_insumo(id_tipo_insumo):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            # Eliminar insumos relacionados y sus relaciones con presentaciones
            cursor.execute("SELECT id FROM insumo WHERE id_tipo_insumo = ?", (id_tipo_insumo,))
            insumos = cursor.fetchall()
            for insumo in insumos:
                eliminar_insumo(insumo['id'])
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
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre FROM presentacion ORDER BY nombre")
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener presentaciones: {e}")
            return []
        finally:
            conn.close()

def agregar_presentacion(nombre):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM presentacion WHERE nombre = ?", (nombre,))
            existente = cursor.fetchone()
            if existente:
                return existente['id']
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
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE presentacion SET nombre = ? WHERE id = ?", (nuevo_nombre, id_presentacion))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error al actualizar presentación: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

def eliminar_presentacion(id_presentacion):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            # Verificar si hay insumos asociados en la tabla intermedia
            cursor.execute("SELECT COUNT(*) as count FROM insumo_presentacion WHERE presentacion_id = ?", (id_presentacion,))
            resultado = cursor.fetchone()
            if resultado['count'] > 0:
                print(f"No se puede eliminar la presentación porque hay {resultado['count']} insumos asociados.")
                return False
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
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            # Obtener insumos y sus presentaciones concatenadas
            cursor.execute("""
                SELECT i.id, i.nombre, i.lote, i.fecha_vencimiento, t.descripcion as tipo_insumo,
                    GROUP_CONCAT(p.nombre, ', ') as nombre_presentacion
                FROM insumo i
                JOIN tipo_insumo t ON i.id_tipo_insumo = t.id
                LEFT JOIN insumo_presentacion ip ON i.id = ip.insumo_id
                LEFT JOIN presentacion p ON ip.presentacion_id = p.id
                WHERE i.id_tipo_insumo = ?
                GROUP BY i.id
                ORDER BY i.nombre
            """, (id_tipo_insumo,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener insumos: {e}")
            return []
        finally:
            conn.close()

def agregar_insumo(nombre, lote, id_presentacion, fecha_vencimiento, id_tipo_insumo):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO insumo (nombre, lote, fecha_vencimiento, id_tipo_insumo)
                VALUES (?, ?, ?, ?)""", (nombre, lote, fecha_vencimiento, id_tipo_insumo))
            id_insumo = cursor.lastrowid
            # Insertar relación con presentación
            if id_presentacion:
                cursor.execute("""
                    INSERT INTO insumo_presentacion (insumo_id, presentacion_id)
                    VALUES (?, ?)""", (id_insumo, id_presentacion))
            conn.commit()
            return id_insumo
        except sqlite3.Error as e:
            print(f"Error al agregar insumo: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

def actualizar_insumo(id_insumo, nombre, lote, id_presentacion, fecha_vencimiento, id_tipo_insumo):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE insumo
                SET nombre = ?, lote = ?, fecha_vencimiento = ?, id_tipo_insumo = ?
                WHERE id = ?""", (nombre, lote, fecha_vencimiento, id_tipo_insumo, id_insumo))
            # Actualizar relación con presentación: eliminar anteriores y agregar la nueva
            cursor.execute("DELETE FROM insumo_presentacion WHERE insumo_id = ?", (id_insumo,))
            if id_presentacion:
                cursor.execute("INSERT INTO insumo_presentacion (insumo_id, presentacion_id) VALUES (?, ?)", (id_insumo, id_presentacion))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error al actualizar insumo: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

def obtener_insumo_por_id(id_insumo):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT i.id, i.nombre, i.lote, i.fecha_vencimiento, i.id_tipo_insumo,
                    t.descripcion as tipo_insumo,
                    GROUP_CONCAT(p.nombre, ', ') as nombre_presentacion
                FROM insumo i
                JOIN tipo_insumo t ON i.id_tipo_insumo = t.id
                LEFT JOIN insumo_presentacion ip ON i.id = ip.insumo_id
                LEFT JOIN presentacion p ON ip.presentacion_id = p.id
                WHERE i.id = ?
                GROUP BY i.id
            """, (id_insumo,))
            return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Error al obtener insumo: {e}")
            return None
        finally:
            conn.close()

def obtener_insumo_por_nombre(nombre, id_tipo_insumo):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, nombre FROM insumo WHERE nombre = ? AND id_tipo_insumo = ?
            """, (nombre, id_tipo_insumo))
            return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Error al obtener insumo por nombre: {e}")
            return None
        finally:
            conn.close()

def eliminar_insumo(id_insumo):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM insumo_presentacion WHERE insumo_id = ?", (id_insumo,))
            cursor.execute("DELETE FROM insumo WHERE id = ?", (id_insumo,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error al eliminar insumo: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

# -------------------- OPERACIONES TIPO MOVIMIENTO --------------------

def obtener_tipos_movimiento():
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, descripcion FROM tipo_movimiento ORDER BY descripcion")
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener tipos de movimiento: {e}")
            return []
        finally:
            conn.close()

def agregar_tipo_movimiento(descripcion):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO tipo_movimiento (descripcion) VALUES (?)", (descripcion,))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error al agregar tipo de movimiento: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

def actualizar_tipo_movimiento(id_tipo, descripcion):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE tipo_movimiento SET descripcion = ? WHERE id = ?", (descripcion, id_tipo))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error al actualizar tipo de movimiento: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

def eliminar_tipo_movimiento(id_tipo):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tipo_movimiento WHERE id = ?", (id_tipo,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error al eliminar tipo de movimiento: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

# -------------------- OPERACIONES MOVIMIENTO --------------------

def guardar_movimiento(movimiento_data):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            fecha_registro = movimiento_data['fecha_registro'].strftime('%Y-%m-%d')
            fecha_vencimiento = movimiento_data['fecha_vencimiento'].strftime('%Y-%m-%d')
            cursor.execute("""
                INSERT INTO movimiento (
                    fecha_registro,
                    referencia,
                    tipo_movimiento_id,
                    servicio_id,
                    insumo_id,
                    lote,
                    fecha_vencimiento,
                    cantidad,
                    salida_distrito_id,
                    salida_servicio_id,
                    observaciones
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    fecha_registro,
                    movimiento_data['referencia'],
                    movimiento_data['tipo_movimiento_id'],
                    movimiento_data['servicio_id'],
                    movimiento_data['insumo_id'],
                    movimiento_data['lote'],
                    fecha_vencimiento,
                    movimiento_data['cantidad'],
                    movimiento_data.get('salida_distrito_id'),
                    movimiento_data.get('salida_servicio_id'),
                    movimiento_data['observaciones']
                ))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error al guardar movimiento: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

# -------------------- FUNCIONES PARA OBTENER IDS --------------------

def obtener_id_distrito(nombre_distrito):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM distrito WHERE nombre = ?", (nombre_distrito,))
            resultado = cursor.fetchone()
            return resultado['id'] if resultado else None
        except sqlite3.Error as e:
            print(f"Error al obtener id distrito: {e}")
            return None
        finally:
            conn.close()

def obtener_id_insumo(nombre_insumo, id_tipo_insumo):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM insumo WHERE nombre = ? AND id_tipo_insumo = ?", (nombre_insumo, id_tipo_insumo))
            resultado = cursor.fetchone()
            return resultado['id'] if resultado else None
        except sqlite3.Error as e:
            print(f"Error al obtener id insumo: {e}")
            return None
        finally:
            conn.close()

def obtener_id_presentacion(nombre_presentacion):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM presentacion WHERE nombre = ?", (nombre_presentacion,))
            resultado = cursor.fetchone()
            return resultado['id'] if resultado else None
        except sqlite3.Error as e:
            print(f"Error al obtener id presentación: {e}")
            return None
        finally:
            conn.close()

def obtener_id_servicio(nombre_servicio):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM servicio WHERE nombre = ?", (nombre_servicio,))
            resultado = cursor.fetchone()
            return resultado['id'] if resultado else None
        except sqlite3.Error as e:
            print(f"Error al obtener id servicio: {e}")
            return None
        finally:
            conn.close()

def obtener_id_tipo_insumo(descripcion_tipo_insumo):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM tipo_insumo WHERE descripcion = ?", (descripcion_tipo_insumo,))
            resultado = cursor.fetchone()
            return resultado['id'] if resultado else None
        except sqlite3.Error as e:
            print(f"Error al obtener id tipo insumo: {e}")
            return None
        finally:
            conn.close()

def obtener_id_tipo_movimiento(descripcion_tipo_movimiento):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM tipo_movimiento WHERE descripcion = ?", (descripcion_tipo_movimiento,))
            resultado = cursor.fetchone()
            return resultado['id'] if resultado else None
        except sqlite3.Error as e:
            print(f"Error al obtener id tipo movimiento: {e}")
            return None
        finally:
            conn.close()

def obtener_id_tipo_servicio(descripcion_tipo_servicio):
    conn = conectar_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM tipo_servicio WHERE descripcion = ?", (descripcion_tipo_servicio,))
            resultado = cursor.fetchone()
            return resultado['id'] if resultado else None
        except sqlite3.Error as e:
            print(f"Error al obtener id tipo servicio: {e}")
            return None
        finally:
            conn.close()

# -------------------- FUNCIONES AUXILIARES --------------------

def verificar_conexion():
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
    conn = conectar_db()
    if conn:
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
                'movimiento'
            ]
            for tabla in tablas:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tabla,))
                if not cursor.fetchone():
                    return False
            return True
        except sqlite3.Error as e:
            print(f"Error al verificar tablas: {e}")
            return False
        finally:
            conn.close()
    return False
# -------------------- OPERACIÓN REPORTE --------------------

def obtener_movimientos_kardex(fecha_inicio, fecha_fin, distrito_nombre=None, tipo_servicio_desc=None,
                               servicio_nombre=None, tipo_insumo_desc=None, insumo_nombre=None,
                               presentacion_nombre=None):
    conn = conectar_db()
    if not conn:
        return []

    try:
        cursor = conn.cursor()

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
                s_salida.nombre AS servicio_destino
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
            WHERE m.fecha_registro BETWEEN ? AND ?
        """

        params = [fecha_inicio, fecha_fin]
        if distrito_nombre:
            query += " AND d.nombre = ?"
            params.append(distrito_nombre)
        if tipo_servicio_desc:
            query += " AND ts.descripcion = ?"
            params.append(tipo_servicio_desc)
        if servicio_nombre:
            query += " AND s.nombre = ?"
            params.append(servicio_nombre)
        if tipo_insumo_desc:
            query += " AND ti.descripcion = ?"
            params.append(tipo_insumo_desc)
        if insumo_nombre:
            query += " AND i.nombre = ?"
            params.append(insumo_nombre)
        if presentacion_nombre:
            query += " AND p.nombre = ?"
            params.append(presentacion_nombre)

        query += " ORDER BY m.fecha_registro ASC, m.id ASC"

        cursor.execute(query, params)
        resultados = cursor.fetchall()

        # Cálculo de saldo acumulado
        saldo = 0
        movimientos = []
        for row in resultados:
            tipo = row['tipo_movimiento'].upper()
            cantidad = float(row['cantidad']) if row['cantidad'] else 0

            # Determinar el destinatario para SALIDA NIVEL INFERIOR
            destinatario = row['tipo_movimiento']
            if tipo == 'SALIDA NIVEL INFERIOR':
                if row['distrito_destino']:
                    destinatario = f"Distrito: {row['distrito_destino']}"
                elif row['servicio_destino']:
                    destinatario = f"Servicio: {row['servicio_destino']}"

            entrada = cantidad if tipo in ['INVENTARIO INICIAL', 'ENTRADA NIVEL SUPERIOR'] else 0

            # Formatear salida con tipo de movimiento
            if tipo in ['SALIDA NIVEL INFERIOR', 'ENTREGADO']:
                salida = f"{cantidad:.2f} ({tipo.title()})"
            else:
                salida = ""

            reajuste = cantidad if tipo == 'REAJUSTE POSITIVO' else (-cantidad if tipo == 'REAJUSTE NEGATIVO' else 0)
            cantidad_col = cantidad if tipo not in ['NO ENTREGADO'] else 0

            if tipo in ['INVENTARIO INICIAL', 'ENTRADA NIVEL SUPERIOR', 'REAJUSTE POSITIVO']:
                saldo += cantidad
            elif tipo in ['SALIDA NIVEL INFERIOR', 'ENTREGADO', 'REAJUSTE NEGATIVO']:
                saldo -= cantidad

            movimientos.append({
                'fecha': row['fecha'],
                'referencia': row['referencia'],
                'tipo_movimiento': destinatario,  
                'entrada': entrada,
                'precio_unitario': "",    
                'valor_total': "",       
                'lote': row['lote'],
                'fecha_vencimiento': row['fecha_vencimiento'],
                'salida': salida,         
                'reajuste': reajuste,
                'cantidad_col': cantidad_col,
                'saldo': saldo,
                'observaciones': row['observaciones']
            })
        return movimientos

    except sqlite3.Error as e:
        print(f"Error al obtener movimientos kardex: {e}")
        return []
    finally:
        conn.close()
# -------------------- OPERACIÓN USUARIOS --------------------

def crear_tabla_usuarios():
    """Crea la tabla de usuarios si no existe"""
    query = '''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        nombre_completo TEXT,
        rol TEXT CHECK(rol IN ('admin', 'usuario', 'super_admin')) NOT NULL,
        activo BOOLEAN DEFAULT 1,
        fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    '''
    try:
        conn = conectar_db()
        conn.execute(query)
        conn.commit()

        # Crear super usuario si no existe
        crear_super_usuario_si_no_existe()
        return True
    except Exception as e:
        print(f"Error creando tabla usuarios: {e}")
        return False
    finally:
        if conn:
            conn.close()

def crear_super_usuario_si_no_existe():
    """Crea el super usuario si no existe"""
    import hashlib

    # Credenciales del super usuario
    super_user = {
        'username': 'admin',
        'password': hashlib.sha256('admin123'.encode()).hexdigest(),
        'nombre_completo': 'Administrador del Sistema',
        'rol': 'super_admin'
    }

    try:
        conn = conectar_db()
        # Verificar si existe
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM usuarios WHERE username = ?', (super_user['username'],))
        if not cursor.fetchone():
            # Crear super usuario
            cursor.execute('''
                INSERT INTO usuarios (username, password, nombre_completo, rol)
                VALUES (?, ?, ?, ?)
            ''', (
                super_user['username'],
                super_user['password'],
                super_user['nombre_completo'],
                super_user['rol']
            ))
            conn.commit()
    except Exception as e:
        print(f"Error creando super usuario: {e}")
    finally:
        if conn:
            conn.close()
            
def existe_usuario(username):
    """Verifica si un nombre de usuario ya existe en la base de datos."""
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
        resultado = cursor.fetchone()
        return resultado is not None
    except Exception as e:
        print(f"Error al verificar la existencia del usuario: {e}")
        return False
    finally:
        conn.close()

def verificar_credenciales(username, password):
    """Verifica las credenciales del usuario"""
    import hashlib
    try:
        conn = conectar_db()
        cursor = conn.cursor()

        # Obtener usuario
        cursor.execute('''
            SELECT id, username, rol, activo
            FROM usuarios
            WHERE username = ? AND password = ? AND activo = 1
        ''', (
            username,
            hashlib.sha256(password.encode()).hexdigest()
        ))

        usuario = cursor.fetchone()
        if usuario:
            return {
                'id': usuario[0],
                'username': usuario[1],
                'rol': usuario[2],
                'activo': usuario[3]
            }
        return None
    except Exception as e:
        print(f"Error verificando credenciales: {e}")
        return None
    finally:
        if conn:
            conn.close()

def obtener_usuarios():
    """Devuelve la lista de usuarios (excepto el super_admin)"""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, nombre_completo, rol, activo FROM usuarios WHERE rol != 'super_admin'")
    usuarios = cursor.fetchall()
    conn.close()
    return usuarios

def crear_usuario(username, password, nombre_completo, rol, activo=1):
    import hashlib
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO usuarios (username, password, nombre_completo, rol, activo) VALUES (?, ?, ?, ?, ?)",
            (username, hashlib.sha256(password.encode()).hexdigest(), nombre_completo, rol, activo)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creando usuario: {e}")
        return False
    finally:
        conn.close()

def actualizar_usuario(id_usuario, nombre_completo, rol, activo):
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE usuarios SET nombre_completo=?, rol=?, activo=? WHERE id=?",
            (nombre_completo, rol, activo, id_usuario)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error actualizando usuario: {e}")
        return False
    finally:
        conn.close()

def cambiar_password_usuario(id_usuario, new_password):
    import hashlib
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE usuarios SET password=? WHERE id=?",
            (hashlib.sha256(new_password.encode()).hexdigest(), id_usuario)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error cambiando contraseña: {e}")
        return False
    finally:
        conn.close()

def eliminar_usuario(id_usuario):
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM usuarios WHERE id=?", (id_usuario,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error eliminando usuario: {e}")
        return False
    finally:
        conn.close()

# -------------------- OPERACIÓN CORRECCIÓN --------------------

def buscar_movimientos_por_filtros(
    fecha_ini, fecha_fin, area, distrito, tipo_servicio,
    servicio, tipo_insumo, insumo, presentacion, tipo_movimiento
):
    conn = conectar_db()
    if not conn:
        return []

    try:
        cursor = conn.cursor()

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
            m.referencia,
            tm.descripcion AS tipo_movimiento,
            m.lote,
            m.fecha_vencimiento,
            m.cantidad,
            d_salida.nombre AS distrito_salida,
            s_salida.nombre AS servicio_salida,
            m.observaciones
        FROM movimiento m
        JOIN tipo_movimiento tm ON m.tipo_movimiento_id = tm.id
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
        WHERE m.fecha_registro BETWEEN ? AND ?
        """

        params = [fecha_ini, fecha_fin]
        if area:
            query += " AND a.nombre = ?"
            params.append(area)
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
        if tipo_movimiento:
            query += " AND tm.descripcion = ?"
            params.append(tipo_movimiento)

        query += " ORDER BY m.fecha_registro ASC, m.id ASC"

        cursor.execute(query, params)
        resultados = [dict(row) for row in cursor.fetchall()]
        return resultados
    except Exception as e:
        return []
    finally:
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
        cursor = conn.cursor()

        # Primero obtenemos los datos actuales del movimiento
        cursor.execute("SELECT * FROM movimiento WHERE id = ?", (mov_id,))
        movimiento_actual = cursor.fetchone()
        if not movimiento_actual:
            return False

        # Preparamos los campos a actualizar
        campos_actualizables = []
        valores = []

        if 'fecha' in nuevos_datos:
            campos_actualizables.append("fecha_registro = ?")
            valores.append(nuevos_datos['fecha'])

        if 'referencia' in nuevos_datos:
            campos_actualizables.append("referencia = ?")
            valores.append(nuevos_datos['referencia'])

        if 'tipo_movimiento' in nuevos_datos:
            # Obtenemos el ID del tipo de movimiento
            cursor.execute("SELECT id FROM tipo_movimiento WHERE descripcion = ?",
                          (nuevos_datos['tipo_movimiento'],))
            tipo_mov = cursor.fetchone()
            if tipo_mov:
                campos_actualizables.append("tipo_movimiento_id = ?")
                valores.append(tipo_mov['id'])

        if 'lote' in nuevos_datos:
            campos_actualizables.append("lote = ?")
            valores.append(nuevos_datos['lote'])

        if 'fecha_vencimiento' in nuevos_datos:
            campos_actualizables.append("fecha_vencimiento = ?")
            valores.append(nuevos_datos['fecha_vencimiento'])

        if 'cantidad' in nuevos_datos:
            campos_actualizables.append("cantidad = ?")
            valores.append(nuevos_datos['cantidad'])

        if 'observaciones' in nuevos_datos:
            campos_actualizables.append("observaciones = ?")
            valores.append(nuevos_datos['observaciones'])

        # Si no hay campos para actualizar, retornamos
        if not campos_actualizables:
            return False

        # Construimos la consulta SQL
        query = f"UPDATE movimiento SET {', '.join(campos_actualizables)} WHERE id = ?"
        valores.append(mov_id)

        # Ejecutamos la actualización
        cursor.execute(query, valores)
        conn.commit()

        return cursor.rowcount > 0

    except sqlite3.Error as e:
        print(f"Error al actualizar movimiento: {e}")
        conn.rollback()
        return False
    finally:
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
        cursor.execute("DELETE FROM movimiento WHERE id = ?", (mov_id,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error al eliminar movimiento: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()