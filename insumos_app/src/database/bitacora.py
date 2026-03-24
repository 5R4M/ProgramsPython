# -*- coding: utf-8 -*-
"""
Módulo de bitácora de auditoría.
Registra todas las acciones de agregar, modificar y eliminar datos.
"""
from datetime import datetime
from src.database.db_manager import conectar_db as get_connection


def crear_tabla_bitacora():
    """Crea la tabla bitacora si no existe."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS `bitacora` (
                `id`             INT AUTO_INCREMENT PRIMARY KEY,
                `fecha_hora`     DATETIME        NOT NULL,
                `usuario`        VARCHAR(100)    NOT NULL,
                `nombre_usuario` VARCHAR(200)    NOT NULL DEFAULT '',
                `accion`         VARCHAR(20)     NOT NULL COMMENT 'AGREGAR, MODIFICAR, ELIMINAR, IMPORTAR',
                `modulo`         VARCHAR(100)    NOT NULL,
                `descripcion`    TEXT            NOT NULL,
                `datos_antes`    TEXT            NULL,
                `datos_despues`  TEXT            NULL,
                INDEX idx_fecha  (`fecha_hora`),
                INDEX idx_usuario (`usuario`),
                INDEX idx_accion  (`accion`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        print(f"[bitacora] Error creando tabla: {e}")
        return False
    finally:
        try:
            if conn and conn.is_connected():
                conn.close()
        except Exception:
            pass


def registrar(usuario_dict, accion, modulo, descripcion,
              datos_antes=None, datos_despues=None):
    """
    Registra una acción en la bitácora.

    Parámetros
    ----------
    usuario_dict : dict  – objeto usuario de la sesión (con claves 'username', 'nombre_completo')
    accion       : str   – 'AGREGAR' | 'MODIFICAR' | 'ELIMINAR' | 'IMPORTAR'
    modulo       : str   – nombre del módulo (ej. 'Insumos', 'Movimientos')
    descripcion  : str   – texto libre que describe qué cambió
    datos_antes  : str|None – representación del registro antes del cambio
    datos_despues: str|None – representación del registro después del cambio
    """
    conn = None
    try:
        username = usuario_dict.get('username', 'desconocido') if usuario_dict else 'desconocido'
        nombre   = usuario_dict.get('nombre_completo', username) if usuario_dict else username

        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO `bitacora`
                (fecha_hora, usuario, nombre_usuario, accion, modulo, descripcion, datos_antes, datos_despues)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            datetime.now(),
            username,
            nombre,
            accion.upper(),
            modulo,
            descripcion,
            datos_antes,
            datos_despues
        ))
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"[bitacora] Error registrando acción: {e}")
    finally:
        try:
            if conn and conn.is_connected():
                conn.close()
        except Exception:
            pass


def obtener_registros(filtro_usuario=None, filtro_accion=None,
                      filtro_modulo=None, filtro_fecha_desde=None,
                      filtro_fecha_hasta=None, limite=500):
    """
    Devuelve lista de registros de la bitácora como lista de dicts.
    """
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)

        where  = []
        params = []

        if filtro_usuario:
            where.append("(usuario LIKE %s OR nombre_usuario LIKE %s)")
            params += [f"%{filtro_usuario}%", f"%{filtro_usuario}%"]
        if filtro_accion and filtro_accion != "TODAS":
            where.append("accion = %s")
            params.append(filtro_accion.upper())
        if filtro_modulo and filtro_modulo != "TODOS":
            where.append("modulo = %s")
            params.append(filtro_modulo)
        if filtro_fecha_desde:
            where.append("DATE(fecha_hora) >= %s")
            params.append(filtro_fecha_desde)
        if filtro_fecha_hasta:
            where.append("DATE(fecha_hora) <= %s")
            params.append(filtro_fecha_hasta)

        sql = "SELECT * FROM `bitacora`"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY fecha_hora DESC LIMIT %s"
        params.append(limite)

        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        return rows
    except Exception as e:
        print(f"[bitacora] Error obteniendo registros: {e}")
        return []
    finally:
        try:
            if conn and conn.is_connected():
                conn.close()
        except Exception:
            pass


def obtener_modulos_usados():
    """Retorna lista de módulos distintos registrados en bitácora."""
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("SELECT DISTINCT modulo FROM `bitacora` ORDER BY modulo")
        rows = [r[0] for r in cur.fetchall()]
        cur.close()
        return rows
    except Exception:
        return []
    finally:
        try:
            if conn and conn.is_connected():
                conn.close()
        except Exception:
            pass
