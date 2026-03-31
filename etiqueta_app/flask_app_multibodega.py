from flask import Flask, request, jsonify, render_template_string, redirect, session
import pandas as pd
from functools import wraps
from datetime import datetime
import pytz
import os

import jwt
import hashlib
import sqlite3
from datetime import timedelta

from flask_cors import CORS

app = Flask(__name__)

app.secret_key = 'Admin2026!'

CORS(app,
     origins=['http://localhost:5173'],
     allow_headers=['Content-Type', 'X-API-Key', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])

# Configuración de zona horaria
TIMEZONE = pytz.timezone('America/Guatemala')

def obtener_hora_actual():
    """Obtiene la hora actual en zona horaria de Guatemala"""
    return datetime.now(TIMEZONE)

def convertir_valor_celda(valor):
    """
    Convierte valores de celdas de Excel a tipos serializables JSON
    Maneja ArrayFormula, fórmulas, y otros tipos especiales
    """
    if valor is None:
        return None

    # Manejar ArrayFormula (causa del error)
    if hasattr(valor, '__class__') and 'ArrayFormula' in valor.__class__.__name__:
        return None  # O convertir a string si necesitas el valor

    # Manejar objetos de fórmula
    if hasattr(valor, 'value'):
        return convertir_valor_celda(valor.value)

    # Convertir tipos básicos
    if isinstance(valor, (int, float, str, bool)):
        return valor

    # Convertir datetime
    if isinstance(valor, datetime):
        return valor.strftime('%d/%m/%Y')

    # Para cualquier otro tipo, convertir a string
    return str(valor)

# Definición de bodegas
BODEGAS = {
    'medico': {
        'nombre': 'Material Médico Quirúrgico e Insumos de Laboratorio',
        'archivo': '/home/salonso/mysite/inventario_medico.xlsx',
        'tiene_tipos': True
    },
    'medicamentos': {
        'nombre': 'Medicamentos',
        'archivo': '/home/salonso/mysite/inventario_medicamentos.xlsx',
        'tiene_tipos': False
    },
    'limpieza': {
        'nombre': 'Limpieza',
        'archivo': '/home/salonso/mysite/inventario_limpieza.xlsx',
        'tiene_tipos': False
    },
    'oficina': {
        'nombre': 'Oficina',
        'archivo': '/home/salonso/mysite/inventario_oficina.xlsx',
        'tiene_tipos': False
    },
    'varios': {
        'nombre': 'Varios',
        'archivo': '/home/salonso/mysite/inventario_varios.xlsx',
        'tiene_tipos': True
    },
    'programas': {
        'nombre': 'Programas',
        'archivo': '/home/salonso/mysite/inventario_programas.xlsx',
        'tiene_tipos': True  # Tiene tipos: Vacuna, VIH, T/B, S/R, etc.
    }
}

# Definición de tipos de insumo con sus nombres completos e iconos
TIPOS_INSUMO = {
    # Bodega Médico
    'MQ': {
        'nombre': 'Médico Quirúrgico',
        'icono': '🏥',
        'color': '#3498db'
    },
    'LAB': {
        'nombre': 'Laboratorio',
        'icono': '🔬',
        'color': '#9b59b6'
    },
    # Bodega Varios
    'VR': {
        'nombre': 'Varios',
        'icono': '📦',
        'color': '#95a5a6'
    },
    'VR/ALIM': {
        'nombre': 'Varios - Alimentos',
        'icono': '🍽️',
        'color': '#e67e22'
    },
    'VR/DON': {
        'nombre': 'Varios - Donaciones',
        'icono': '🎁',
        'color': '#e74c3c'
    },
    'VR/EQU': {
        'nombre': 'Varios - Equipos',
        'icono': '⚙️',
        'color': '#34495e'
    },
    'VR/GAS': {
        'nombre': 'Varios - Gases',
        'icono': '⛽',
        'color': '#16a085'
    },
    'VR/LLANT': {
        'nombre': 'Varios - Llantas',
        'icono': '🚗',
        'color': '#2c3e50'
    },
    'VR/VECT': {
        'nombre': 'Varios - Vectores',
        'icono': '🦟',
        'color': '#8e44ad'
    },
    # Bodega Programas
    'Vacuna': {
        'nombre': 'Vacunas',
        'icono': '💉',
        'color': '#3498db'
    },
    'VIH': {
        'nombre': 'Programa VIH',
        'icono': '🩺',
        'color': '#e74c3c'
    },
    'T/B': {
        'nombre': 'Tuberculosis',
        'icono': '🫁',
        'color': '#95a5a6'
    },
    'S/R': {
        'nombre': 'Salud Reproductiva',
        'icono': '👶',
        'color': '#e91e63'
    },
    'MX': {
        'nombre': 'Medicamento',
        'icono': '📋',
        'color': '#607d8b'
    },
    'Lab.': {
        'nombre': 'Laboratorio',
        'icono': '🔬',
        'color': '#9c27b0'
    }
}

# Variable global para almacenar datos de todas las bodegas
datos_inventario = {}
tipos_por_bodega = {}  # Nueva estructura para almacenar tipos disponibles por bodega

def cargar_datos_bodega(codigo_bodega, archivo_excel):
    try:
        if not os.path.exists(archivo_excel):
            print(f"⚠️  Archivo no encontrado: {archivo_excel}")
            return {}, set()

        df = pd.read_excel(archivo_excel, sheet_name="Inventario General", header=4)
        filas_iniciales = len(df)

        df = df.dropna(how='all')
        df = df[df['Código'].notna()]

        print(f"📊 Bodega '{codigo_bodega}': {len(df)} productos leídos del Excel")

        inventario_bodega = {}
        tipos_encontrados = set()
        productos_sin_lotes = 0

        for idx, row in df.iterrows():
            codigo = str(row.get('Código', ''))
            if not codigo or codigo == 'nan':
                continue

            lotes = []

            # (F/V, Lote, Saldo, PrecioUnit, PrecioTotal)
            columnas_lotes = [
                (6,  7,  8,  27, 32),   # Lote 1: G,H,I,AB,AG
                (9,  10, 11, 28, 33),   # Lote 2: J,K,L,AC,AH
                (12, 13, 14, 29, 34),   # Lote 3: M,N,O,AD,AI
                (15, 16, 17, 30, 35),   # Lote 4: P,Q,R,AE,AJ
                (18, 19, 20, 31, 36)    # Lote 5: S,T,U,AF,AK
            ]

            columnas_med = [22, 23, 24, 25, 26]

            for i, (col_fv, col_lote, col_saldo, col_pu, col_pt) in enumerate(columnas_lotes, start=1):
                try:
                    fv    = row.iloc[col_fv]
                    lote  = row.iloc[col_lote]
                    saldo = row.iloc[col_saldo]

                    fv_str   = str(fv)   if pd.notna(fv)   and str(fv)   != 'nan' else 'S/D'
                    lote_str = str(lote) if pd.notna(lote) and str(lote) != 'nan' else 'S/D'

                    if isinstance(fv, (pd.Timestamp, datetime)):
                        fv_str = fv.strftime('%d/%m/%Y')
                    elif fv_str != 'S/D':
                        # Limpiar strings con hora: "2025-01-15 00:00:00" → "15/01/2025"
                        try:
                            fv_str = datetime.strptime(fv_str.split(' ')[0], '%Y-%m-%d').strftime('%d/%m/%Y')
                        except (ValueError, AttributeError):
                            pass

                    # MED
                    med_valor = 'S/D'
                    try:
                        med_excel = row.iloc[columnas_med[i-1]]
                        if pd.notna(med_excel):
                            med_float = float(med_excel)
                            med_valor = 'S/D' if med_float >= 1000 else med_float
                    except:
                        med_valor = 'S/D'

                    # Precio Unitario por lote (AB–AF)
                    precio_unit = None
                    try:
                        pu = row.iloc[col_pu]
                        if pd.notna(pu):
                            precio_unit = float(pu)
                    except:
                        precio_unit = None

                    # Precio Total por lote (AG–AK)
                    precio_total_lote = None
                    try:
                        pt = row.iloc[col_pt]
                        if pd.notna(pt):
                            precio_total_lote = float(pt)
                    except:
                        precio_total_lote = None

                    if pd.notna(saldo) and saldo > 0:
                        lotes.append({
                            'numero':           i,
                            'fv':               fv_str,
                            'lote':             lote_str,
                            'saldo':            int(saldo) if saldo == int(saldo) else saldo,
                            'med':              med_valor,
                            'precio_unitario':  precio_unit,
                            'precio_total_lote': precio_total_lote
                        })
                except Exception as e:
                    print(f"⚠️ Error procesando lote {i} del código {codigo}: {e}")
                    continue

            # Tipo de insumo
            tipo_insumo = ''
            if BODEGAS[codigo_bodega].get('tiene_tipos', False):
                tipo_insumo = str(row.get('Tipo de Insumo', '')) if pd.notna(row.get('Tipo de Insumo')) else ''
                if tipo_insumo and tipo_insumo != 'nan':
                    tipos_encontrados.add(tipo_insumo)

            # Precio Total General (columna AL = índice 37)
            precio_total_general = None
            try:
                ptg = row.iloc[37]
                if pd.notna(ptg):
                    precio_total_general = float(ptg)
            except:
                precio_total_general = None

            # Saldo total CORREGIDO (columna AM = índice 38)
            saldo_total = row.iloc[38] if len(row) > 38 and pd.notna(row.iloc[38]) else 0

            if lotes:
                inventario_bodega[codigo] = {
                    'codigo':               codigo,
                    'medicamento':          str(row.get('Medicamento', '')),
                    'tipo':                 tipo_insumo,
                    'presentacion':         str(row.get('Presentación Primaria', '')) if pd.notna(row.get('Presentación Primaria')) else '',
                    'lotes':                lotes,
                    'saldo_total':          saldo_total,
                    'precio_total_general': precio_total_general,
                    'bodega':               codigo_bodega
                }
            else:
                productos_sin_lotes += 1

        print(f"✅ Bodega '{codigo_bodega}': {len(inventario_bodega)} productos con lotes, {productos_sin_lotes} sin lotes")

        if len(inventario_bodega) == 0:
            print(f"⚠️⚠️⚠️ ADVERTENCIA: Bodega '{codigo_bodega}' NO tiene productos con saldo > 0")
            print(f"   Archivo: {archivo_excel}")
            print(f"   Total filas: {filas_iniciales}, Productos sin lotes: {productos_sin_lotes}")

        return inventario_bodega, tipos_encontrados

    except Exception as e:
        print(f"❌ Error cargando bodega {codigo_bodega}: {e}")
        import traceback
        traceback.print_exc()
        return {}, set()

def cargar_datos():
    """Carga datos de todas las bodegas"""
    global datos_inventario, tipos_por_bodega
    datos_inventario = {}
    tipos_por_bodega = {}

    print("\n🔄 Cargando datos de todas las bodegas...")

    for codigo_bodega, info_bodega in BODEGAS.items():
        inventario, tipos = cargar_datos_bodega(codigo_bodega, info_bodega['archivo'])
        if inventario:
            datos_inventario[codigo_bodega] = inventario
            if tipos:
                tipos_por_bodega[codigo_bodega] = tipos

    total_productos = sum(len(inv) for inv in datos_inventario.values())
    total_lotes = sum(sum(len(d['lotes']) for d in inv.values()) for inv in datos_inventario.values())

    print(f"\n✅ Total cargado: {len(datos_inventario)} bodegas, {total_productos} productos, {total_lotes} lotes")
    print(f"📊 Bodegas con tipos: {list(tipos_por_bodega.keys())}")
    return True

def obtener_color_med(med_valor):
    """Determina el color según el valor de MED"""
    if med_valor == 'S/D' or med_valor is None:
        return 'green', 'S/D'

    try:
        med = float(med_valor)
        if 1 <= med <= 12:
            return 'red', f'{int(med)} meses'
        elif 13 <= med <= 17:
            return 'yellow', f'{int(med)} meses'
        elif med >= 18:
            return 'green', f'{int(med)} meses'
        else:
            return 'green', 'S/D'
    except:
        return 'green', 'S/D'

# Cargar datos al iniciar
cargar_datos()

# Token de autenticación simple (mejora con JWT en producción)
API_KEY = "b87ab7db392a14f215df04bf630d53eb2968a00a"

# Configuración de autenticación
SECRET_KEY = 'Selso@1'
DATABASE_PATH = '/home/salonso/mysite/inventario_usuarios.db'

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != API_KEY:
            return jsonify({'error': 'No autorizado'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Funciones base de datos
def get_db_connection():
    """Crea una conexión a la base de datos SQLite"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    ✅ CORREGIDO: Inicializa la base de datos de usuarios con mejor manejo de errores
    """
    try:
        print("\n" + "="*70)
        print("🔄 INICIANDO BASE DE DATOS DE USUARIOS")
        print("="*70)
        print(f"📂 Ruta: {DATABASE_PATH}")

        # Verificar que el directorio existe
        import os
        directorio = os.path.dirname(DATABASE_PATH)
        if directorio and not os.path.exists(directorio):
            print(f"⚠️ Creando directorio: {directorio}")
            os.makedirs(directorio, exist_ok=True)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Crear tabla
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                nombre_completo TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                rol TEXT NOT NULL CHECK(rol IN ('Admin', 'User')),
                bodega_asignada TEXT,
                activo BOOLEAN NOT NULL DEFAULT 1,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_ultimo_acceso TIMESTAMP
            )
        ''')
        print("✅ Tabla 'usuarios' creada/verificada")

        # Verificar si admin existe
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'admin'")
        admin_exists = cursor.fetchone()[0] > 0

        if not admin_exists:
            print("\n👤 Creando usuarios predeterminados...")

            # Crear admin
            admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
            cursor.execute('''
                INSERT INTO usuarios (username, password, nombre_completo, email, rol, activo)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('admin', admin_password, 'Administrador del Sistema', 'admin@bodega.com', 'Admin', True))
            print("   ✅ Usuario 'admin' creado (password: admin123)")

            # Crear user1
            user1_password = hashlib.sha256('user123'.encode()).hexdigest()
            cursor.execute('''
                INSERT INTO usuarios (username, password, nombre_completo, email, rol, bodega_asignada, activo)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('user1', user1_password, 'Usuario de Prueba', 'user@bodega.com', 'User', 'BODEGA_MEDICAMENTOS', True))
            print("   ✅ Usuario 'user1' creado (password: user123)")
        else:
            print("\nℹ️ Usuarios ya existen, no se crean duplicados")

        conn.commit()

        # Mostrar usuarios existentes
        cursor.execute("SELECT id, username, rol, activo FROM usuarios ORDER BY id")
        usuarios = cursor.fetchall()

        print(f"\n{'='*70}")
        print(f"👥 USUARIOS REGISTRADOS:")
        print(f"{'='*70}")
        for user in usuarios:
            user_id, username, rol, activo = user
            estado = "✅" if activo else "❌"
            print(f"   {estado} ID:{user_id} | {username:<15} | Rol: {rol}")
        print(f"{'='*70}")
        print(f"Total: {len(usuarios)} usuario(s)\n")

        conn.close()

        # Verificar que el archivo existe
        import os
        if os.path.exists(DATABASE_PATH):
            file_size = os.path.getsize(DATABASE_PATH)
            print(f"✅ Base de datos inicializada correctamente")
            print(f"   Tamaño: {file_size} bytes")
            print("="*70 + "\n")
            return True
        else:
            print(f"❌ ERROR: Archivo de base de datos no encontrado después de crear")
            return False

    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO en init_db(): {e}")
        import traceback
        traceback.print_exc()
        print("="*70 + "\n")
        return False

def usuario_dict_from_row(row):
    """Convierte una fila de la base de datos en un diccionario"""
    return {
        'id': row['id'],
        'username': row['username'],
        'nombre_completo': row['nombre_completo'],
        'email': row['email'],
        'rol': row['rol'],
        'bodega_asignada': row['bodega_asignada'],
        'activo': bool(row['activo']),
        'fecha_creacion': row['fecha_creacion'],
        'fecha_ultimo_acceso': row['fecha_ultimo_acceso']
    }

def verificar_token(token):
    """Verifica y decodifica el token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except:
        return None

def verificar_admin(f):
    """
    ✅ CORREGIDO: Decorator para verificar que el usuario sea administrador
    Ahora con mejor logging
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')

        print(f"🔐 verificar_admin - Header: {auth_header[:50]}..." if auth_header else "🔐 verificar_admin - Sin header")

        if not auth_header.startswith('Bearer '):
            print("❌ Token no proporcionado o formato incorrecto")
            return jsonify({'success': False, 'message': 'Token no proporcionado'}), 401

        token = auth_header.replace('Bearer ', '')
        payload = verificar_token(token)

        if not payload:
            print("❌ Token inválido o expirado")
            return jsonify({'success': False, 'message': 'Token inválido o expirado'}), 401

        conn = get_db_connection()
        usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (payload['user_id'],)).fetchone()
        conn.close()

        if not usuario:
            print(f"❌ Usuario ID {payload['user_id']} no encontrado")
            return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 403

        if usuario['rol'] != 'Admin':
            print(f"❌ Usuario {usuario['username']} no es Admin (rol: {usuario['rol']})")
            return jsonify({'success': False, 'message': 'Acceso denegado - Se requiere rol Admin'}), 403

        print(f"✅ Usuario {usuario['username']} autenticado como Admin")
        kwargs['usuario_actual_id'] = usuario['id']
        return f(*args, **kwargs)

    return decorated_function

# Inicializar base de datos de usuarios
init_db()

@app.route('/api/medicamento')
def api_medicamento():
    codigo      = request.args.get('codigo', '')
    bodega_param = request.args.get('bodega', '')

    if not codigo:
        return jsonify({'error': 'Código requerido'}), 400

    datos = None
    bodega_encontrada = None

    if bodega_param and bodega_param in datos_inventario:
        if codigo in datos_inventario[bodega_param]:
            datos = datos_inventario[bodega_param][codigo]
            bodega_encontrada = bodega_param
    else:
        for codigo_bodega, inventario in datos_inventario.items():
            if codigo in inventario:
                datos = inventario[codigo]
                bodega_encontrada = codigo_bodega
                break

    if not datos:
        return jsonify({'error': 'Producto no encontrado'}), 404

    import time
    return jsonify({
        'codigo':               datos['codigo'],
        'medicamento':          datos['medicamento'],
        'tipo':                 datos.get('tipo', ''),
        'presentacion':         datos.get('presentacion', ''),
        'saldo_total':          datos.get('saldo_total', 0),
        'precio_total_general': datos.get('precio_total_general', 0),
        'bodega':               bodega_encontrada,
        'bodega_nombre':        BODEGAS[bodega_encontrada]['nombre'],
        'lotes':                datos['lotes'],
        'timestamp':            int(time.time()),
        'actualizado':          obtener_hora_actual().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/buscar')
def api_buscar():
    """Busca insumos por nombre o código (búsqueda parcial, todas las bodegas)"""
    nombre = request.args.get('nombre', '').strip()

    if not nombre or len(nombre) < 2:
        return jsonify([])

    nombre_lower = nombre.lower()
    resultados = []

    for codigo_bodega, inventario in datos_inventario.items():
        for codigo, datos in inventario.items():
            medicamento = datos.get('medicamento', '')
            if nombre_lower in medicamento.lower() or nombre_lower in codigo.lower():
                resultados.append({
                    'codigo':      datos['codigo'],
                    'medicamento': medicamento,
                    'tipo':        datos.get('tipo', ''),
                    'bodega':      codigo_bodega
                })

    resultados.sort(key=lambda x: x['medicamento'].lower())
    return jsonify(resultados[:50])

@app.route('/')
def inicio():
    """Página de inicio con selector de bodegas"""
    total_bodegas = len(datos_inventario)
    total_productos = sum(len(inv) for inv in datos_inventario.values())
    total_lotes = sum(sum(len(d['lotes']) for d in inv.values()) for inv in datos_inventario.values())

    # Obtener la hora actual
    hora_actual = obtener_hora_actual().strftime('%d/%m/%Y %H:%M:%S')

    # Generar lista de bodegas
    lista_bodegas = ""
    for codigo_bodega, inventario in datos_inventario.items():
        nombre_bodega = BODEGAS[codigo_bodega]['nombre']
        num_productos = len(inventario)
        num_lotes = sum(len(d['lotes']) for d in inventario.values())

        # Mostrar si tiene tipos
        tipos_info = ""
        if codigo_bodega in tipos_por_bodega and tipos_por_bodega[codigo_bodega]:
            num_tipos = len(tipos_por_bodega[codigo_bodega])
            tipos_info = f" • {num_tipos} tipos"

        lista_bodegas += f"""
        <div class="bodega-card">
            <div class="bodega-icon">📦</div>
            <div class="bodega-info">
                <div class="bodega-nombre">{nombre_bodega}</div>
                <div class="bodega-stats">
                    <span>{num_productos} productos</span>
                    <span>•</span>
                    <span>{num_lotes} lotes</span>
                    {tipos_info}
                </div>
            </div>
        </div>
"""

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema de Inventario Multi-Bodega</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            background: rgba(255,255,255,0.1);
            padding: 30px;
            border-radius: 20px;
            backdrop-filter: blur(10px);
            margin-bottom: 30px;
        }}
        h1 {{ font-size: 32px; margin: 0 0 10px 0; }}
        .badge {{
            background: #4CAF50;
            padding: 8px 16px;
            border-radius: 20px;
            display: inline-block;
            margin: 15px 0;
            font-weight: bold;
            font-size: 14px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.2);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .stat-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .bodegas-section {{
            background: rgba(255,255,255,0.1);
            padding: 25px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }}
        .section-title {{
            font-size: 20px;
            margin-bottom: 20px;
            font-weight: bold;
        }}
        .bodega-card {{
            background: rgba(255,255,255,0.15);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            transition: transform 0.2s;
        }}
        .bodega-card:hover {{
            transform: translateX(5px);
            background: rgba(255,255,255,0.2);
        }}
        .bodega-icon {{
            font-size: 28px;
            margin-right: 15px;
        }}
        .bodega-info {{
            flex: 1;
        }}
        .bodega-nombre {{
            font-weight: bold;
            font-size: 16px;
            margin-bottom: 5px;
        }}
        .bodega-stats {{
            font-size: 13px;
            opacity: 0.9;
        }}
        .bodega-stats span {{
            margin: 0 5px;
        }}
        .actualizado {{
            text-align: center;
            margin-top: 20px;
            font-size: 12px;
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏥 Sistema de Inventario Multi-Bodega</h1>
            <div class="badge">✅ EN LÍNEA</div>

            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{total_bodegas}</div>
                    <div class="stat-label">Bodegas</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{total_productos}</div>
                    <div class="stat-label">Productos</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{total_lotes}</div>
                    <div class="stat-label">Lotes</div>
                </div>
            </div>
        </div>

        <div class="bodegas-section">
            <div class="section-title">📦 Bodegas Activas</div>
            {lista_bodegas}
        </div>

        <div class="actualizado">
            🕐 Actualizado: {hora_actual}
        </div>
    </div>
</body>
</html>
"""
    return html

@app.route('/medicamento')
def medicamento():
    """Muestra información del medicamento"""
    codigo = request.args.get('codigo', '')
    bodega_param = request.args.get('bodega', '')

    # Obtener la hora actual
    hora_actual = obtener_hora_actual().strftime('%d/%m/%Y %H:%M:%S')

    if not codigo:
        return "Error: Código requerido", 400

    # Buscar el medicamento en la bodega especificada o en todas
    datos = None
    bodega_encontrada = None

    if bodega_param and bodega_param in datos_inventario:
        # Buscar solo en la bodega especificada
        if codigo in datos_inventario[bodega_param]:
            datos = datos_inventario[bodega_param][codigo]
            bodega_encontrada = BODEGAS[bodega_param]['nombre']
    else:
        # Buscar en todas las bodegas
        for codigo_bodega, inventario in datos_inventario.items():
            if codigo in inventario:
                datos = inventario[codigo]
                bodega_encontrada = BODEGAS[codigo_bodega]['nombre']
                break

    if not datos:
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Código no encontrado</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            margin: 0;
        }}
        .container {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            max-width: 400px;
        }}
        .icon {{ font-size: 60px; margin-bottom: 20px; }}
        h1 {{ color: #e74c3c; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">❌</div>
        <h1>Código no encontrado</h1>
        <p>El código <strong>{codigo}</strong> no existe en el inventario o no tiene saldo disponible.</p>
        <p style="margin-top: 20px; color: #666; font-size: 14px;">
            🕐 {hora_actual}
        </p>
    </div>
</body>
</html>
""", 404

    # Mostrar tipo de insumo si aplica
    tipo_insumo_html = ""
    if datos.get('tipo') and str(datos.get('tipo')) != 'nan' and datos.get('tipo'):
        tipo_info = TIPOS_INSUMO.get(datos['tipo'], {'nombre': datos['tipo'], 'icono': '📋'})
        tipo_insumo_html = f"""
            <div class="field">
                <div class="field-label">{tipo_info['icono']} Tipo de Insumo</div>
                <div class="field-value">{tipo_info['nombre']}</div>
            </div>
"""

    # HTML optimizado para móvil
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{datos['codigo']} - {datos['medicamento'][:30]}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 15px;
        }}
        .container {{
            background: white;
            border-radius: 15px;
            padding: 20px;
            max-width: 600px;
            margin: 0 auto;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 20px;
        }}
        .header h1 {{ font-size: 20px; margin-bottom: 5px; }}
        .badge {{
            display: inline-block;
            background: #4caf50;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 10px;
            margin-top: 10px;
            font-weight: bold;
        }}
        .bodega-tag {{
            background: #ff9800;
            color: white;
            padding: 6px 12px;
            border-radius: 15px;
            font-size: 11px;
            margin-top: 8px;
            display: inline-block;
            font-weight: bold;
        }}
        .info-section {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
        }}
        .field {{ margin: 12px 0; }}
        .field-label {{
            font-weight: bold;
            color: #667eea;
            font-size: 11px;
            text-transform: uppercase;
        }}
        .field-value {{
            color: #333;
            font-size: 15px;
            word-wrap: break-word;
        }}
        .lote-section {{
            background: linear-gradient(to right, #e8f5e9, #ffffff);
            padding: 12px;
            border-radius: 8px;
            margin: 12px 0;
            border-left: 3px solid #4caf50;
            position: relative;
        }}
        .lote-title {{
            font-weight: bold;
            color: #4caf50;
            margin-bottom: 8px;
            font-size: 13px;
        }}
        .lote-detail {{
            color: #555;
            font-size: 13px;
            margin: 5px 0;
        }}
        .med-indicator {{
            position: absolute;
            top: 12px;
            right: 12px;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 11px;
            color: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }}
        .med-indicator.red {{
            background: linear-gradient(135deg, #ff6b6b, #ee5a6f);
        }}
        .med-indicator.yellow {{
            background: linear-gradient(135deg, #ffd93d, #f6b93b);
            color: #333;
        }}
        .med-indicator.green {{
            background: linear-gradient(135deg, #51cf66, #37b24d);
        }}
        .med-info {{
            margin-top: 8px;
            padding: 8px;
            background: rgba(255,255,255,0.7);
            border-radius: 5px;
            font-size: 12px;
            font-weight: bold;
        }}
        .med-info.red {{ color: #c92a2a; border-left: 3px solid #ff6b6b; }}
        .med-info.yellow {{ color: #e67700; border-left: 3px solid #ffd93d; }}
        .med-info.green {{ color: #2b8a3e; border-left: 3px solid #51cf66; }}
        .warning {{
            background: #fff3cd;
            border-left: 3px solid #ffc107;
            padding: 12px;
            margin-top: 15px;
            border-radius: 6px;
            color: #856404;
            font-size: 12px;
        }}
        .actualizado {{
            text-align: center;
            color: #666;
            font-size: 10px;
            margin-top: 15px;
            padding-top: 12px;
            border-top: 1px solid #e0e0e0;
        }}
        h3 {{
            color: #667eea;
            margin: 20px 0 12px 0;
            font-size: 16px;
        }}
        .saldo-total {{
            background: #667eea;
            color: white;
            padding: 10px;
            border-radius: 8px;
            text-align: center;
            margin: 15px 0;
            font-size: 16px;
            font-weight: bold;
        }}
        .leyenda {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }}
        .leyenda-title {{
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
            font-size: 13px;
        }}
        .leyenda-item {{
            display: flex;
            align-items: center;
            margin: 8px 0;
            font-size: 12px;
        }}
        .leyenda-circulo {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        .leyenda-circulo.red {{ background: linear-gradient(135deg, #ff6b6b, #ee5a6f); }}
        .leyenda-circulo.yellow {{ background: linear-gradient(135deg, #ffd93d, #f6b93b); }}
        .leyenda-circulo.green {{ background: linear-gradient(135deg, #51cf66, #37b24d); }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏥 Inventario Médico</h1>
            <div class="badge">✅ EN LÍNEA</div>
            <div class="bodega-tag">📦 {bodega_encontrada}</div>
        </div>

        <div class="info-section">
            <div class="field">
                <div class="field-label">📋 Código</div>
                <div class="field-value">{datos['codigo']}</div>
            </div>

            <div class="field">
                <div class="field-label">💊 Medicamento/Producto</div>
                <div class="field-value">{datos['medicamento']}</div>
            </div>

            {tipo_insumo_html}
"""

    if datos.get('presentacion') and str(datos.get('presentacion')) != 'nan' and datos.get('presentacion'):
        html += f"""
            <div class="field">
                <div class="field-label">📦 Presentación</div>
                <div class="field-value">{datos['presentacion']}</div>
            </div>
"""

    saldo_total = datos.get('saldo_total', 0)
    html += f"""
        </div>

        <div class="saldo-total">
            📊 Saldo Total: {saldo_total} unidades
        </div>
"""

    if datos.get('lotes'):
        html += """
        <h3>📦 Lotes Disponibles</h3>
"""
        for lote in datos['lotes']:
            color, texto_med = obtener_color_med(lote.get('med'))

            if lote.get('med') == 'S/D' or texto_med == 'S/D':
                valor_circulo = 'S/D'
            else:
                try:
                    valor_circulo = int(float(lote.get('med', 0)))
                except:
                    valor_circulo = 'S/D'

            pu = lote.get('precio_unitario')
            pt = lote.get('precio_total_lote')
            precio_unit_html = f'<div class="lote-detail"><strong>Precio Unitario:</strong> Q{pu:,.2f}</div>' if pu is not None else ''
            precio_total_html = f'<div class="lote-detail"><strong>Total Lote:</strong> <strong style="color: #1a5276;">Q{pt:,.2f}</strong></div>' if pt is not None else ''

            html += f"""
        <div class="lote-section">
            <div class="med-indicator {color}">
                {valor_circulo}
            </div>
            <div class="lote-title">🔹 LOTE {lote['numero']}</div>
            <div class="lote-detail"><strong>F/V:</strong> {lote['fv']}</div>
            <div class="lote-detail"><strong>Lote:</strong> {lote['lote']}</div>
            <div class="lote-detail"><strong>Saldo:</strong> <strong style="color: #4caf50; font-size: 16px;">{lote['saldo']} unidades</strong></div>
            {precio_unit_html}
            {precio_total_html}
            <div class="med-info {color}">
                📅 Existencia disponible: {texto_med}
            </div>
        </div>
"""


    html += f"""
        <div class="leyenda">
            <div class="leyenda-title">📊 Leyenda - Meses de Existencia Disponible</div>
            <div class="leyenda-item">
                <div class="leyenda-circulo red"></div>
                <span><strong>Rojo:</strong> 1-12 meses (Crítico - Reabastecer pronto)</span>
            </div>
            <div class="leyenda-item">
                <div class="leyenda-circulo yellow"></div>
                <span><strong>Amarillo:</strong> 13-17 meses (Alerta - Monitorear)</span>
            </div>
            <div class="leyenda-item">
                <div class="leyenda-circulo green"></div>
                <span><strong>Verde:</strong> 18+ meses (Óptimo - Stock suficiente)</span>
            </div>
        </div>

        <div class="warning">
            ⚠️ <strong>Importante:</strong> Verificar fecha de vencimiento antes de usar
        </div>

        <div class="actualizado">
            🕐 Actualizado: {hora_actual}
        </div>
    </div>
</body>
</html>
"""
    return html

@app.route('/recargar')
def recargar():
    """Endpoint para recargar datos manualmente"""
    if cargar_datos():
        total_bodegas = len(datos_inventario)
        total_productos = sum(len(inv) for inv in datos_inventario.values())
        total_lotes = sum(sum(len(d['lotes']) for d in inv.values()) for inv in datos_inventario.values())
        return f"✅ Datos recargados: {total_bodegas} bodegas, {total_productos} productos, {total_lotes} lotes"
    else:
        return "❌ Error al recargar datos", 500

@app.route('/test')
def test():
    """Endpoint de prueba"""
    html = "<h1>Test - Inventario Multi-Bodega</h1>"

    for codigo_bodega, inventario in datos_inventario.items():
        nombre_bodega = BODEGAS[codigo_bodega]['nombre']
        html += f"<h2>📦 {nombre_bodega}</h2>"

        # Mostrar tipos si los tiene
        if codigo_bodega in tipos_por_bodega and tipos_por_bodega[codigo_bodega]:
            html += f"<p><strong>Tipos:</strong> {', '.join(sorted(tipos_por_bodega[codigo_bodega]))}</p>"

        html += "<ul>"
        for i, (codigo, datos) in enumerate(list(inventario.items())[:3]):
            html += f"<li><strong>{codigo}</strong>: {datos['medicamento']} - {len(datos['lotes'])} lotes"
            if datos.get('tipo'):
                html += f" - Tipo: {datos['tipo']}"
            for lote in datos['lotes']:
                med = lote.get('med')
                color, texto = obtener_color_med(med)
                html += f"<br>&nbsp;&nbsp;Lote {lote['numero']}: {texto} ({color})"
            html += "</li>"

        html += "</ul>"

    return html

# ============================================
# ENDPOINT PARA ACTUALIZAR DATOS DE PRODUCTO
# ============================================

@app.route('/api/actualizar_datos_producto', methods=['POST'])
@require_api_key
def api_actualizar_datos_producto():
    """
    ✅ Endpoint para actualizar datos de un producto en el Excel
    Actualiza: Fecha Vencimiento (G-U), Número de Lote (G-U), Saldo (G-U), Precio Unitario (AB)
    """
    try:
        datos = request.get_json()

        # Validar datos requeridos
        if not all(k in datos for k in ['codigo', 'bodega', 'lote_numero']):
            return jsonify({
                'success': False,
                'error': 'Faltan datos requeridos: codigo, bodega, lote_numero'
            }), 400

        codigo = str(datos['codigo'])
        bodega = datos['bodega']
        lote_numero = int(datos['lote_numero'])

        # Validar bodega
        if bodega not in BODEGAS:
            return jsonify({
                'success': False,
                'error': f'Bodega no válida: {bodega}'
            }), 400

        # Validar número de lote (1-5)
        if lote_numero < 1 or lote_numero > 5:
            return jsonify({
                'success': False,
                'error': 'Número de lote debe estar entre 1 y 5'
            }), 400

        archivo_excel = BODEGAS[bodega]['archivo']

        if not os.path.exists(archivo_excel):
            return jsonify({
                'success': False,
                'error': f'Archivo no encontrado: {archivo_excel}'
            }), 404

        # Leer el Excel con openpyxl para mantener formato
        from openpyxl import load_workbook

        wb = load_workbook(archivo_excel)
        ws = wb["Inventario General"]

        # Buscar la fila del producto (empezando desde fila 6 porque header está en fila 5)
        fila_producto = None
        for row_idx, row in enumerate(ws.iter_rows(min_row=6, max_row=ws.max_row), start=6):
            if str(row[0].value) == codigo:  # Columna A = Código
                fila_producto = row_idx
                break

        if fila_producto is None:
            wb.close()
            return jsonify({
                'success': False,
                'error': f'Producto con código {codigo} no encontrado'
            }), 404

        # Mapeo de columnas por número de lote

        columnas_lotes = {
            1: {'fv': 7,  'lote': 8,  'saldo': 9,  'precio_unit': 28},
            2: {'fv': 10, 'lote': 11, 'saldo': 12, 'precio_unit': 29},
            3: {'fv': 13, 'lote': 14, 'saldo': 15, 'precio_unit': 30},
            4: {'fv': 16, 'lote': 17, 'saldo': 18, 'precio_unit': 31},
            5: {'fv': 19, 'lote': 20, 'saldo': 21, 'precio_unit': 32}
        }

        cols = columnas_lotes[lote_numero]
        cambios_realizados = []

        # Actualizar campos según lo que se envió
        if 'saldo' in datos:
            nuevo_saldo = float(datos['saldo'])
            ws.cell(row=fila_producto, column=cols['saldo']).value = nuevo_saldo
            cambios_realizados.append(f"Saldo: {nuevo_saldo}")

        if 'fecha_vencimiento' in datos:
            nueva_fv = datos['fecha_vencimiento']
            ws.cell(row=fila_producto, column=cols['fv']).value = nueva_fv
            cambios_realizados.append(f"F/V: {nueva_fv}")

        if 'numero_lote' in datos:
            nuevo_num_lote = datos['numero_lote']
            ws.cell(row=fila_producto, column=cols['lote']).value = nuevo_num_lote
            cambios_realizados.append(f"Número Lote: {nuevo_num_lote}")

        if 'precio_unitario' in datos:
            nuevo_precio = float(datos['precio_unitario'])
            ws.cell(row=fila_producto, column=cols['precio_unit']).value = nuevo_precio
            cambios_realizados.append(f"Precio Lote {lote_numero}: Q{nuevo_precio:.2f}")


        # Guardar cambios en el Excel
        wb.save(archivo_excel)
        wb.close()

        # ✅ CRÍTICO: Recargar datos en memoria INMEDIATAMENTE
        print(f"🔄 Recargando datos de bodega {bodega}...")
        inventario_actualizado, tipos = cargar_datos_bodega(bodega, archivo_excel)

        if inventario_actualizado:
            datos_inventario[bodega] = inventario_actualizado
            print(f"✅ Datos actualizados en memoria: {len(inventario_actualizado)} productos")

            if tipos:
                tipos_por_bodega[bodega] = tipos
                print(f"✅ Tipos actualizados: {len(tipos)} tipos")
        else:
            print(f"⚠️ ERROR: No se pudo recargar la bodega {bodega}")
            return jsonify({
                'success': False,
                'error': 'Error al recargar datos después de guardar'
            }), 500

        print(f"✅ Producto {codigo} actualizado en bodega {bodega}, lote {lote_numero}")
        print(f"   Cambios: {', '.join(cambios_realizados)}")

        return jsonify({
            'success': True,
            'mensaje': f'Datos del producto actualizados correctamente',
            'cambios': cambios_realizados,
            'lote_numero': lote_numero
        }), 200

    except Exception as e:
        print(f"❌ Error en actualizar_datos_producto: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/actualizar_datos_multiples', methods=['POST'])
@require_api_key
def api_actualizar_datos_multiples():
    """
    ✅ Endpoint para actualizar múltiples lotes de un producto en una sola llamada
    """
    try:
        datos = request.get_json()

        if not all(k in datos for k in ['codigo', 'bodega', 'lotes']):
            return jsonify({
                'success': False,
                'error': 'Faltan datos requeridos: codigo, bodega, lotes'
            }), 400

        codigo = str(datos['codigo'])
        bodega = datos['bodega']
        lotes_modificados = datos['lotes']  # Lista de lotes con cambios

        if bodega not in BODEGAS:
            return jsonify({
                'success': False,
                'error': f'Bodega no válida: {bodega}'
            }), 400

        archivo_excel = BODEGAS[bodega]['archivo']

        if not os.path.exists(archivo_excel):
            return jsonify({
                'success': False,
                'error': f'Archivo no encontrado: {archivo_excel}'
            }), 404

        from openpyxl import load_workbook

        wb = load_workbook(archivo_excel)
        ws = wb["Inventario General"]

        # Buscar la fila del producto
        fila_producto = None
        for row_idx, row in enumerate(ws.iter_rows(min_row=6, max_row=ws.max_row), start=6):
            if str(row[0].value) == codigo:
                fila_producto = row_idx
                break

        if fila_producto is None:
            wb.close()
            return jsonify({
                'success': False,
                'error': f'Producto con código {codigo} no encontrado'
            }), 404

        columnas_lotes = {
            1: {'fv': 7,  'lote': 8,  'saldo': 9,  'precio_unit': 28},
            2: {'fv': 10, 'lote': 11, 'saldo': 12, 'precio_unit': 29},
            3: {'fv': 13, 'lote': 14, 'saldo': 15, 'precio_unit': 30},
            4: {'fv': 16, 'lote': 17, 'saldo': 18, 'precio_unit': 31},
            5: {'fv': 19, 'lote': 20, 'saldo': 21, 'precio_unit': 32}
        }


        todos_cambios = []
        precio_actualizado = False

        # Procesar cada lote modificado
        for lote_data in lotes_modificados:
            lote_numero = int(lote_data['lote_numero'])

            if lote_numero < 1 or lote_numero > 5:
                continue

            cols = columnas_lotes[lote_numero]
            cambios_lote = []

            if 'saldo' in lote_data:
                ws.cell(row=fila_producto, column=cols['saldo']).value = float(lote_data['saldo'])
                cambios_lote.append(f"Saldo: {lote_data['saldo']}")

            if 'fecha_vencimiento' in lote_data:
                ws.cell(row=fila_producto, column=cols['fv']).value = lote_data['fecha_vencimiento']
                cambios_lote.append(f"F/V: {lote_data['fecha_vencimiento']}")

            if 'numero_lote' in lote_data:
                ws.cell(row=fila_producto, column=cols['lote']).value = lote_data['numero_lote']
                cambios_lote.append(f"Lote: {lote_data['numero_lote']}")

            if cambios_lote:
                todos_cambios.append(f"Lote {lote_numero}: {', '.join(cambios_lote)}")

            # Precio unitario (solo se actualiza una vez por producto)
            if 'precio_unitario' in lote_data:
                ws.cell(row=fila_producto, column=cols['precio_unit']).value = float(lote_data['precio_unitario'])
                todos_cambios.append(f"Precio Lote {lote_numero}: Q{lote_data['precio_unitario']:.2f}")


        # Guardar cambios
        wb.save(archivo_excel)
        wb.close()

        # ✅ CRÍTICO: Recargar datos en memoria INMEDIATAMENTE
        print(f"🔄 Recargando datos de bodega {bodega}...")
        inventario_actualizado, tipos = cargar_datos_bodega(bodega, archivo_excel)

        if inventario_actualizado:
            datos_inventario[bodega] = inventario_actualizado
            print(f"✅ Datos actualizados en memoria: {len(inventario_actualizado)} productos")

            if tipos:
                tipos_por_bodega[bodega] = tipos
                print(f"✅ Tipos actualizados: {len(tipos)} tipos")
        else:
            print(f"⚠️ ERROR: No se pudo recargar la bodega {bodega}")
            return jsonify({
                'success': False,
                'error': 'Error al recargar datos después de guardar'
            }), 500

        print(f"✅ Múltiples lotes actualizados para producto {codigo} en bodega {bodega}")
        print(f"   Cambios totales: {len(todos_cambios)}")

        return jsonify({
            'success': True,
            'mensaje': f'{len(todos_cambios)} cambios realizados correctamente',
            'cambios': todos_cambios
        }), 200

    except Exception as e:
        print(f"❌ Error en actualizar_datos_multiples: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/reporte/<color>')
def reporte_por_color(color):
    """Muestra reporte de medicamentos filtrados por color con opción de seleccionar tipo"""
    bodega_param = request.args.get('bodega', '')
    tipo_param = request.args.get('tipo', '')

    # Obtener la hora actual
    hora_actual = obtener_hora_actual().strftime('%d/%m/%Y %H:%M:%S')

    # Validar color
    colores_validos = ['rojo', 'amarillo', 'verde']
    if color.lower() not in colores_validos:
        return "Color no válido. Usa: rojo, amarillo o verde", 400

    color = color.lower()

    # Convertir español a inglés
    color_map = {
        'rojo': 'red',
        'amarillo': 'yellow',
        'verde': 'green'
    }
    color_ingles = color_map.get(color, 'green')

    # Determinar qué bodegas filtrar
    bodegas_a_filtrar = {}
    if bodega_param and bodega_param in datos_inventario:
        bodegas_a_filtrar[bodega_param] = datos_inventario[bodega_param]
        nombre_filtro = f" - {BODEGAS[bodega_param]['nombre']}"
        codigo_bodega_actual = bodega_param
    else:
        bodegas_a_filtrar = datos_inventario
        nombre_filtro = " - Todas las Bodegas"
        codigo_bodega_actual = None

    # Verificar si la bodega actual tiene tipos Y no se ha seleccionado tipo
    bodega_tiene_tipos = False
    if codigo_bodega_actual and codigo_bodega_actual in tipos_por_bodega:
        if tipos_por_bodega[codigo_bodega_actual]:
            bodega_tiene_tipos = True

    # Si la bodega tiene tipos Y no se ha seleccionado, mostrar selector
    if bodega_tiene_tipos and not tipo_param:
        return mostrar_selector_tipo(color, bodega_param, codigo_bodega_actual)

    # Filtrar medicamentos por color y tipo si aplica
    medicamentos_filtrados = []

    for codigo_bodega, inventario in bodegas_a_filtrar.items():
        nombre_bodega = BODEGAS[codigo_bodega]['nombre']

        for codigo, datos in inventario.items():
            # Filtrar por tipo si está especificado y no es "TODOS"
            if tipo_param and tipo_param != 'TODOS' and datos.get('tipo') != tipo_param:
                continue

            for lote in datos['lotes']:
                med_color, texto_med = obtener_color_med(lote.get('med'))

                if med_color == color_ingles:
                    medicamentos_filtrados.append({
                        'codigo':          codigo,
                        'medicamento':     datos['medicamento'],
                        'bodega':          nombre_bodega,
                        'tipo':            datos.get('tipo', ''),
                        'lote_numero':     lote['numero'],
                        'fv':              lote['fv'],
                        'lote':            lote['lote'],
                        'saldo':           lote['saldo'],
                        'med':             lote.get('med'),
                        'med_texto':       texto_med,
                        'precio_unitario':   lote.get('precio_unitario'),
                        'precio_total_lote': lote.get('precio_total_lote')
                    })

    # Ordenar por bodega y medicamento
    medicamentos_filtrados.sort(key=lambda x: (x['bodega'], x['medicamento']))

    # Configuración según el color
    if color == 'rojo':
        color_hex   = '#ff6b6b'
        titulo      = 'INSUMOS CRÍTICOS'
        subtitulo   = 'Existencia: 1-12 meses'
        icono       = '🔴'
        descripcion = 'Estos insumos requieren reabastecimiento URGENTE'
        bg_gradient = 'linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)'
    elif color == 'amarillo':
        color_hex   = '#ffd93d'
        titulo      = 'INSUMOS EN ALERTA'
        subtitulo   = 'Existencia: 13-17 meses'
        icono       = '🟡'
        descripcion = 'Estos insumos requieren monitoreo constante'
        bg_gradient = 'linear-gradient(135deg, #ffd93d 0%, #f6b93b 100%)'
    else:  # verde
        color_hex   = '#51cf66'
        titulo      = 'INSUMOS ÓPTIMOS'
        subtitulo   = 'Existencia: 18+ meses o S/D'
        icono       = '🟢'
        descripcion = 'Estos insumos tienen stock suficiente'
        bg_gradient = 'linear-gradient(135deg, #51cf66 0%, #37b24d 100%)'

    # Añadir info de tipo si está filtrado
    if tipo_param and tipo_param != 'TODOS' and tipo_param in TIPOS_INSUMO:
        tipo_info    = TIPOS_INSUMO[tipo_param]
        titulo      += f" - {tipo_info['nombre']}"
        nombre_filtro += f" ({tipo_info['icono']} {tipo_info['nombre']})"
    elif tipo_param == 'TODOS':
        nombre_filtro += " (Todos los tipos)"

    # HTML del reporte
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{titulo} - Reporte Multi-Bodega</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, Arial, sans-serif;
            background: {bg_gradient};
            min-height: 100vh;
            padding: 15px;
        }}
        .container {{
            background: white;
            border-radius: 15px;
            padding: 20px;
            max-width: 900px;
            margin: 0 auto;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}
        .header {{
            background: {bg_gradient};
            color: white;
            padding: 30px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        .header h1 {{
            font-size: 26px;
            margin-bottom: 8px;
            font-weight: bold;
        }}
        .header .subtitulo {{
            font-size: 15px;
            opacity: 0.95;
            margin-top: 8px;
        }}
        .header .bodega-filtro {{
            background: rgba(255,255,255,0.25);
            padding: 10px 20px;
            border-radius: 25px;
            margin-top: 15px;
            display: inline-block;
            font-size: 14px;
            font-weight: bold;
            backdrop-filter: blur(10px);
        }}
        .stats {{
            display: flex;
            justify-content: space-around;
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .stat-item {{ text-align: center; }}
        .stat-number {{
            font-size: 32px;
            font-weight: bold;
            color: {color_hex};
        }}
        .stat-label {{
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }}
        .descripcion {{
            background: #fff3cd;
            border-left: 4px solid {color_hex};
            padding: 12px;
            margin-bottom: 20px;
            border-radius: 6px;
            color: #856404;
            font-size: 13px;
        }}
        .medicamento-card {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 18px;
            margin-bottom: 18px;
            border-left: 5px solid {color_hex};
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .medicamento-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        }}
        .med-header {{
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-bottom: 12px;
            padding-bottom: 12px;
            border-bottom: 2px solid #e0e0e0;
        }}
        .med-top-row {{
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .med-icono {{ font-size: 28px; }}
        .med-codigo {{
            background: {color_hex};
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: bold;
            letter-spacing: 0.5px;
        }}
        .bodega-tag {{
            background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: bold;
            box-shadow: 0 2px 6px rgba(255, 152, 0, 0.3);
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .tipo-tag {{
            background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: bold;
            box-shadow: 0 2px 6px rgba(155, 89, 182, 0.3);
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .bodega-icon {{ font-size: 16px; }}
        .med-nombre {{
            font-weight: bold;
            color: #2c3e50;
            font-size: 17px;
            line-height: 1.4;
            margin-bottom: 12px;
        }}
        .med-detalle {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #e0e0e0;
        }}
        .detalle-item {{ font-size: 12px; }}
        .detalle-label {{
            font-weight: bold;
            color: #666;
            display: block;
        }}
        .detalle-valor {{
            color: #333;
            margin-top: 2px;
        }}
        .precio-badge {{
            display: inline-block;
            background: linear-gradient(135deg, #1a5276 0%, #2980b9 100%);
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-weight: bold;
            font-size: 12px;
        }}
        .no-data {{
            text-align: center;
            padding: 40px;
            color: #666;
        }}
        .actualizado {{
            text-align: center;
            color: #666;
            font-size: 10px;
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid #e0e0e0;
        }}
        .btn-volver {{
            display: block;
            text-align: center;
            background: {bg_gradient};
            color: white;
            padding: 12px;
            border-radius: 8px;
            text-decoration: none;
            margin-top: 20px;
            font-weight: bold;
        }}
        @media (max-width: 768px) {{
            .header h1 {{ font-size: 22px; }}
            .bodega-filtro {{ font-size: 13px; padding: 8px 16px; }}
            .medicamento-card {{ padding: 15px; }}
            .med-top-row {{ flex-wrap: wrap; }}
            .bodega-tag, .tipo-tag {{ width: 100%; justify-content: center; }}
            .med-nombre {{ font-size: 15px; }}
            .med-detalle {{ grid-template-columns: 1fr; gap: 12px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="med-icono">{icono}</div>
            <h1>{titulo}</h1>
            <div class="subtitulo">{subtitulo}</div>
            <div class="bodega-filtro">📦 {nombre_filtro.replace(' - ', '')}</div>
        </div>

        <div class="stats">
            <div class="stat-item">
                <div class="stat-number">{len(medicamentos_filtrados)}</div>
                <div class="stat-label">Lotes</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{len(set(m['codigo'] for m in medicamentos_filtrados))}</div>
                <div class="stat-label">Productos</div>
            </div>
        </div>

        <div class="descripcion">
            ⚠️ <strong>Estado:</strong> {descripcion}
        </div>
"""

    if medicamentos_filtrados:
        html += """
        <h3 style="color: #333; margin-bottom: 15px;">📋 Listado de Insumos</h3>
"""
        for med in medicamentos_filtrados:
            tipo_html = ""
            if med['tipo'] and med['tipo'] in TIPOS_INSUMO:
                tipo_info = TIPOS_INSUMO[med['tipo']]
                tipo_html = f"""
                <div class="tipo-tag">
                    <span class="bodega-icon">{tipo_info['icono']}</span>
                    <span><strong>{tipo_info['nombre']}</strong></span>
                </div>
"""
            # Precio unitario: mostrar solo si existe
            pu = med.get('precio_unitario')
            pt = med.get('precio_total_lote')
            precio_html = f'<div class="detalle-item"><span class="detalle-label">💲 Precio Unitario</span><span class="detalle-valor"><span class="precio-badge">Q{pu:,.2f}</span></span></div>' if pu is not None else ''
            precio_total_html = f'<div class="detalle-item"><span class="detalle-label">💰 Total Lote</span><span class="detalle-valor"><span class="precio-badge">Q{pt:,.2f}</span></span></div>' if pt is not None else ''

            html += f"""
        <div class="medicamento-card">
            <div class="med-header">
                <div class="med-top-row">
                    <span class="med-icono">💊</span>
                    <span class="med-codigo">📋 {med['codigo']}</span>
                </div>
                <div class="bodega-tag">
                    <span class="bodega-icon">🏥</span>
                    <span><strong>BODEGA:</strong> {med['bodega']}</span>
                </div>
                {tipo_html}
            </div>

            <div class="med-nombre">{med['medicamento']}</div>

            <div class="med-detalle">
                <div class="detalle-item">
                    <span class="detalle-label">📦 Lote</span>
                    <span class="detalle-valor">{med['lote']}</span>
                </div>
                <div class="detalle-item">
                    <span class="detalle-label">📅 F/V</span>
                    <span class="detalle-valor">{med['fv']}</span>
                </div>
                <div class="detalle-item">
                    <span class="detalle-label">📊 Saldo</span>
                    <span class="detalle-valor"><strong>{med['saldo']} unidades</strong></span>
                </div>
                <div class="detalle-item">
                    <span class="detalle-label">⏱️ Existencia</span>
                    <span class="detalle-valor"><strong>{med['med_texto']}</strong></span>
                </div>
                {precio_html}
                {precio_total_html}
            </div>
        </div>
"""
    else:
        html += """
        <div class="no-data">
            <div style="font-size: 48px; margin-bottom: 15px;">📭</div>
            <h3>No hay insumos en esta categoría</h3>
            <p style="margin-top: 10px; color: #999;">
                Todos los productos están en otras categorías
            </p>
        </div>
"""

    html += f"""
        <a href="/" class="btn-volver">🏠 Volver al Inicio</a>

        <div class="actualizado">
            🕐 Actualizado: {hora_actual}
        </div>
    </div>
</body>
</html>
"""
    return html

def mostrar_selector_tipo(color, bodega_param, codigo_bodega):
    """Muestra una página de selección de tipo de insumo dinámica según la bodega"""

    # Obtener la hora actual
    hora_actual = obtener_hora_actual().strftime('%d/%m/%Y %H:%M:%S')

    # Configuración según el color
    if color == 'rojo':
        color_hex = '#ff6b6b'
        titulo = 'INSUMOS CRÍTICOS'
        icono = '🔴'
        bg_gradient = 'linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)'
    elif color == 'amarillo':
        color_hex = '#ffd93d'
        titulo = 'INSUMOS EN ALERTA'
        icono = '🟡'
        bg_gradient = 'linear-gradient(135deg, #ffd93d 0%, #f6b93b 100%)'
    else:
        color_hex = '#51cf66'
        titulo = 'INSUMOS ÓPTIMOS'
        icono = '🟢'
        bg_gradient = 'linear-gradient(135deg, #51cf66 0%, #37b24d 100%)'

    # Obtener tipos de la bodega actual
    tipos_bodega = sorted(tipos_por_bodega.get(codigo_bodega, set()))

    # Construir opciones dinámicamente
    opciones_html = ""
    for tipo_codigo in tipos_bodega:
        tipo_info = TIPOS_INSUMO.get(tipo_codigo, {
            'nombre': tipo_codigo,
            'icono': '📋',
            'color': '#95a5a6'
        })

        opciones_html += f"""
            <a href="/reporte/{color}?tipo={tipo_codigo}&bodega={bodega_param}" class="option-card">
                <div class="option-icon">{tipo_info['icono']}</div>
                <div class="option-content">
                    <div class="option-title">{tipo_info['nombre']}</div>
                    <div class="option-description">Código: {tipo_codigo}</div>
                </div>
                <div class="option-arrow">→</div>
            </a>
"""

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Seleccionar Tipo de Insumo - {titulo}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, Arial, sans-serif;
            background: {bg_gradient};
            min-height: 100vh;
            padding: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .container {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            max-width: 500px;
            width: 100%;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            max-height: 90vh;
            overflow-y: auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .header-icon {{
            font-size: 60px;
            margin-bottom: 15px;
        }}
        .header h1 {{
            color: #2c3e50;
            font-size: 24px;
            margin-bottom: 10px;
        }}
        .header p {{
            color: #666;
            font-size: 14px;
        }}
        .selector-options {{
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-bottom: 20px;
        }}
        .option-card {{
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 3px solid transparent;
            border-radius: 12px;
            padding: 15px;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 12px;
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        .option-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.15);
            border-color: {color_hex};
        }}
        .option-card:active {{
            transform: translateY(-1px);
        }}
        .option-icon {{
            font-size: 32px;
            min-width: 40px;
            text-align: center;
        }}
        .option-content {{
            flex: 1;
        }}
        .option-title {{
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 3px;
        }}
        .option-description {{
            font-size: 12px;
            color: #666;
        }}
        .option-arrow {{
            font-size: 20px;
            color: #999;
        }}
        .divider {{
            text-align: center;
            margin: 20px 0;
            position: relative;
        }}
        .divider::before {{
            content: '';
            position: absolute;
            top: 50%;
            left: 0;
            right: 0;
            height: 1px;
            background: #e0e0e0;
        }}
        .divider span {{
            background: white;
            padding: 0 15px;
            position: relative;
            color: #999;
            font-size: 12px;
            font-weight: bold;
        }}
        .btn-todos {{
            background: {bg_gradient};
            color: white;
            border: none;
            border-radius: 12px;
            padding: 15px;
            font-size: 16px;
            font-weight: bold;
            text-decoration: none;
            display: block;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        .btn-todos:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}
        .btn-todos:active {{
            transform: translateY(0);
        }}
        .footer {{
            text-align: center;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            font-size: 11px;
            color: #999;
        }}

        @media (max-width: 480px) {{
            .container {{
                padding: 20px;
            }}
            .header h1 {{
                font-size: 20px;
            }}
            .option-title {{
                font-size: 14px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-icon">{icono}</div>
            <h1>Selecciona el Tipo de Insumo</h1>
            <p>Reporte: {titulo}</p>
            <p style="font-size: 12px; margin-top: 5px; color: #999;">
                {BODEGAS[codigo_bodega]['nombre']}
            </p>
        </div>

        <div class="selector-options">
            {opciones_html}
        </div>

        <div class="divider">
            <span>O VER TODOS</span>
        </div>

        <a href="/reporte/{color}?tipo=TODOS&bodega={bodega_param}" class="btn-todos">
            📋 Ver Todos los Insumos
        </a>

        <div class="footer">
            🕐 {hora_actual}
        </div>
    </div>
</body>
</html>
"""
    return html

@app.route('/api/debug/verificar_datos')
def debug_verificar_datos():
    """Endpoint para verificar qué datos tiene el servidor en memoria"""
    codigo = request.args.get('codigo', '')
    bodega = request.args.get('bodega', '')

    if not codigo or not bodega:
        return jsonify({'error': 'Código y bodega requeridos'}), 400

    # Verificar en memoria
    datos_memoria = None
    if bodega in datos_inventario and codigo in datos_inventario[bodega]:
        datos_memoria = datos_inventario[bodega][codigo]

    # Leer directamente del Excel
    datos_excel = None
    try:
        archivo = BODEGAS[bodega]['archivo']
        if os.path.exists(archivo):
            df = pd.read_excel(archivo, sheet_name="Inventario General", header=4)
            df = df.dropna(how='all')
            fila = df[df['Código'] == codigo]

            if not fila.empty:
                lotes_excel = []
                columnas_lotes = [(6,7,8), (9,10,11), (12,13,14), (15,16,17), (18,19,20)]

                for i, (col_fv, col_lote, col_saldo) in enumerate(columnas_lotes, 1):
                    saldo = fila.iloc[0, col_saldo]
                    if pd.notna(saldo) and saldo > 0:
                        lotes_excel.append({
                            'lote': i,
                            'fv': str(fila.iloc[0, col_fv]),
                            'numero_lote': str(fila.iloc[0, col_lote]),
                            'saldo': float(saldo)
                        })

                datos_excel = {
                    'codigo': codigo,
                    'lotes': lotes_excel
                }
    except Exception as e:
        datos_excel = {'error': str(e)}

    return jsonify({
        'codigo': codigo,
        'bodega': bodega,
        'datos_en_memoria': datos_memoria if datos_memoria else 'NO ENCONTRADO',
        'datos_en_excel': datos_excel if datos_excel else 'ERROR AL LEER',
        'coinciden': datos_memoria is not None and datos_excel is not None
    })

#ENDPOINTS Autenticacion
@app.route('/api/auth/login', methods=['POST'])
@require_api_key
def login():
    """Endpoint para autenticación de usuarios"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'success': False, 'message': 'Usuario y contraseña son requeridos'}), 400

        conn = get_db_connection()
        usuario = conn.execute('SELECT * FROM usuarios WHERE username = ?', (username,)).fetchone()

        if not usuario:
            conn.close()
            return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 401

        password_hash = hashlib.sha256(password.encode()).hexdigest()

        if password_hash != usuario['password']:
            conn.close()
            return jsonify({'success': False, 'message': 'Contraseña incorrecta'}), 401

        if not usuario['activo']:
            conn.close()
            return jsonify({'success': False, 'message': 'Usuario inactivo'}), 403

        conn.execute('UPDATE usuarios SET fecha_ultimo_acceso = ? WHERE id = ?',
                    (datetime.now(), usuario['id']))
        conn.commit()
        conn.close()

        token_payload = {
            'user_id': usuario['id'],
            'username': usuario['username'],
            'rol': usuario['rol'],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(token_payload, SECRET_KEY, algorithm='HS256')

        return jsonify({
            'success': True,
            'message': f'Bienvenido {usuario["nombre_completo"]}',
            'token': token,
            'usuario': usuario_dict_from_row(usuario)
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/auth/verify', methods=['POST'])
@require_api_key
def verify_token_endpoint():
    """Verifica si un token es válido"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')

        if not token:
            return jsonify({'success': False, 'message': 'Token no proporcionado'}), 401

        payload = verificar_token(token)

        if not payload:
            return jsonify({'success': False, 'message': 'Token inválido o expirado'}), 401

        return jsonify({
            'success': True,
            'user_id': payload['user_id'],
            'username': payload['username'],
            'rol': payload['rol']
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/auth/usuarios', methods=['GET'])
@require_api_key
@verificar_admin
def listar_usuarios(**kwargs):
    """Lista todos los usuarios (Solo admins)"""
    try:
        conn = get_db_connection()
        usuarios = conn.execute('SELECT * FROM usuarios ORDER BY id').fetchall()
        conn.close()

        usuarios_lista = [usuario_dict_from_row(u) for u in usuarios]

        return jsonify({
            'success': True,
            'usuarios': usuarios_lista,
            'total': len(usuarios_lista)
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/auth/crear-usuario', methods=['POST'])
@require_api_key
@verificar_admin
def crear_usuario(**kwargs):
    """✅ CORREGIDO: Crea un nuevo usuario (Solo admins) con mejor logging"""
    try:
        print("\n" + "="*70)
        print("📝 ENDPOINT: /api/auth/crear-usuario")
        print("="*70)

        data = request.get_json()
        print(f"📥 Datos recibidos: {data}")

        username = data.get('username', '').strip()
        nombre_completo = data.get('nombre_completo', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        rol = data.get('rol', 'User')
        bodega_asignada = data.get('bodega_asignada')
        activo = data.get('activo', True)

        # Validaciones
        if not username or len(username) < 3:
            print(f"❌ Validación falló: username inválido")
            return jsonify({'success': False, 'message': 'Username debe tener al menos 3 caracteres'}), 400

        if not nombre_completo:
            print(f"❌ Validación falló: nombre_completo vacío")
            return jsonify({'success': False, 'message': 'Nombre completo es requerido'}), 400

        if not email or '@' not in email:
            print(f"❌ Validación falló: email inválido")
            return jsonify({'success': False, 'message': 'Email inválido'}), 400

        if not password or len(password) < 6:
            print(f"❌ Validación falló: password muy corto")
            return jsonify({'success': False, 'message': 'Contraseña debe tener al menos 6 caracteres'}), 400

        if rol not in ['Admin', 'User']:
            print(f"❌ Validación falló: rol inválido '{rol}'")
            return jsonify({'success': False, 'message': 'Rol inválido'}), 400

        print("✅ Validaciones pasadas")

        conn = get_db_connection()

        # Verificar duplicados
        existe = conn.execute('SELECT COUNT(*) FROM usuarios WHERE username = ?', (username,)).fetchone()[0]
        if existe:
            conn.close()
            print(f"❌ Username '{username}' ya existe")
            return jsonify({'success': False, 'message': f'El usuario "{username}" ya existe'}), 400

        existe_email = conn.execute('SELECT COUNT(*) FROM usuarios WHERE email = ?', (email,)).fetchone()[0]
        if existe_email:
            conn.close()
            print(f"❌ Email '{email}' ya registrado")
            return jsonify({'success': False, 'message': 'El email ya está registrado'}), 400

        # Crear usuario
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        print(f"🔐 Password hasheado correctamente")

        cursor = conn.execute('''
            INSERT INTO usuarios (username, password, nombre_completo, email, rol, bodega_asignada, activo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, password_hash, nombre_completo, email, rol,
              bodega_asignada if rol == 'User' else None, activo))

        nuevo_id = cursor.lastrowid
        conn.commit()
        print(f"✅ Usuario insertado con ID: {nuevo_id}")

        # Obtener usuario creado
        nuevo_usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (nuevo_id,)).fetchone()
        conn.close()

        usuario_dict = {
            'id': nuevo_usuario['id'],
            'username': nuevo_usuario['username'],
            'nombre_completo': nuevo_usuario['nombre_completo'],
            'email': nuevo_usuario['email'],
            'rol': nuevo_usuario['rol'],
            'bodega_asignada': nuevo_usuario['bodega_asignada'],
            'activo': bool(nuevo_usuario['activo']),
            'fecha_creacion': nuevo_usuario['fecha_creacion'],
            'fecha_ultimo_acceso': nuevo_usuario['fecha_ultimo_acceso']
        }

        print(f"✅ Usuario '{username}' creado exitosamente")
        print("="*70 + "\n")

        return jsonify({
            'success': True,
            'message': f'Usuario "{username}" creado exitosamente',
            'usuario': usuario_dict
        }), 201

    except Exception as e:
        print(f"❌ ERROR en crear_usuario: {e}")
        import traceback
        traceback.print_exc()
        print("="*70 + "\n")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/auth/actualizar-usuario', methods=['PUT'])
@require_api_key
@verificar_admin
def actualizar_usuario(**kwargs):
    """Actualiza un usuario (Solo admins)"""
    try:
        data = request.get_json()
        user_id = data.get('id')

        if not user_id:
            return jsonify({'success': False, 'message': 'ID requerido'}), 400

        conn = get_db_connection()
        usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,)).fetchone()

        if not usuario:
            conn.close()
            return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404

        campos = []
        valores = []

        if 'nombre_completo' in data and data['nombre_completo']:
            campos.append('nombre_completo = ?')
            valores.append(data['nombre_completo'].strip())

        if 'email' in data and data['email']:
            nuevo_email = data['email'].strip()
            if '@' not in nuevo_email:
                conn.close()
                return jsonify({'success': False, 'message': 'Email inválido'}), 400

            existe_email = conn.execute(
                'SELECT COUNT(*) FROM usuarios WHERE email = ? AND id != ?',
                (nuevo_email, user_id)
            ).fetchone()[0]

            if existe_email:
                conn.close()
                return jsonify({'success': False, 'message': 'Email ya está en uso'}), 400

            campos.append('email = ?')
            valores.append(nuevo_email)

        if 'nueva_password' in data and data['nueva_password']:
            if len(data['nueva_password']) < 6:
                conn.close()
                return jsonify({'success': False, 'message': 'Contraseña debe tener al menos 6 caracteres'}), 400

            password_hash = hashlib.sha256(data['nueva_password'].encode()).hexdigest()
            campos.append('password = ?')
            valores.append(password_hash)

        if 'rol' in data and data['rol']:
            if data['rol'] not in ['Admin', 'User']:
                conn.close()
                return jsonify({'success': False, 'message': 'Rol inválido'}), 400
            campos.append('rol = ?')
            valores.append(data['rol'])

        if 'bodega_asignada' in data:
            campos.append('bodega_asignada = ?')
            valores.append(data['bodega_asignada'])

        if 'activo' in data:
            campos.append('activo = ?')
            valores.append(1 if data['activo'] else 0)

        if campos:
            valores.append(user_id)
            query = f"UPDATE usuarios SET {', '.join(campos)} WHERE id = ?"
            conn.execute(query, valores)
            conn.commit()

        usuario_actualizado = conn.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,)).fetchone()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Usuario actualizado exitosamente',
            'usuario': usuario_dict_from_row(usuario_actualizado)
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/auth/toggle-activo/<int:user_id>', methods=['PATCH'])
@require_api_key
@verificar_admin
def toggle_usuario_activo(user_id, **kwargs):
    """Activa/Desactiva un usuario (Solo admins)"""
    try:
        conn = get_db_connection()
        usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,)).fetchone()

        if not usuario:
            conn.close()
            return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404

        if usuario['rol'] == 'Admin' and usuario['activo']:
            admins_activos = conn.execute(
                'SELECT COUNT(*) FROM usuarios WHERE rol = "Admin" AND activo = 1'
            ).fetchone()[0]

            if admins_activos <= 1:
                conn.close()
                return jsonify({'success': False, 'message': 'No se puede desactivar el último admin'}), 400

        nuevo_estado = 0 if usuario['activo'] else 1
        conn.execute('UPDATE usuarios SET activo = ? WHERE id = ?', (nuevo_estado, user_id))
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'Usuario {"activado" if nuevo_estado else "desactivado"}',
            'activo': bool(nuevo_estado)
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/auth/eliminar-usuario/<int:user_id>', methods=['DELETE'])
@require_api_key
@verificar_admin
def eliminar_usuario(user_id, **kwargs):
    """Elimina un usuario (Solo admins)"""
    try:
        usuario_actual_id = kwargs.get('usuario_actual_id')

        if usuario_actual_id == user_id:
            return jsonify({'success': False, 'message': 'No puedes eliminar tu propio usuario'}), 400

        conn = get_db_connection()
        usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,)).fetchone()

        if not usuario:
            conn.close()
            return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404

        if usuario['rol'] == 'Admin':
            admins_count = conn.execute('SELECT COUNT(*) FROM usuarios WHERE rol = "Admin"').fetchone()[0]
            if admins_count <= 1:
                conn.close()
                return jsonify({'success': False, 'message': 'No se puede eliminar el último admin'}), 400

        username = usuario['username']
        conn.execute('DELETE FROM usuarios WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'Usuario "{username}" eliminado'
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# ============================================================
# ENDPOINT PDF
# ============================================================

from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                Paragraph, Spacer, PageBreak)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# ── Colores globales ──────────────────────────────────────────────
_C_DARK  = colors.HexColor('#1A3A5C')
_C_MID   = colors.HexColor('#2980B9')
_C_LIGHT = colors.HexColor('#D6EAF8')
_C_BAND  = colors.HexColor('#EBF5FB')
_C_GRAY  = colors.HexColor('#F0F3F4')
_C_LINE  = colors.HexColor('#CCCCCC')


def _pdf_color_med(med_valor):
    """(color_fondo, color_texto) según meses de existencia."""
    if med_valor in ('S/D', None, ''):
        return colors.HexColor('#27AE60'), colors.white
    try:
        m = float(med_valor)
        if 1 <= m <= 12:    return colors.HexColor('#E74C3C'), colors.white
        elif 13 <= m <= 17: return colors.HexColor('#E67E22'), colors.white
        else:               return colors.HexColor('#27AE60'), colors.white
    except Exception:
        return colors.HexColor('#27AE60'), colors.white


def _fmt_n(n):
    try:    return f'{int(n):,}'
    except: return str(n)


def _med_txt(v):
    try:
        return 'S/D' if v == 'S/D' else f'{int(float(v))} meses'
    except Exception:
        return 'S/D'


def _make_pdf_styles():
    base = getSampleStyleSheet()
    def s(name, **kw):
        return ParagraphStyle(name, parent=base['Normal'], **kw)
    return {
        # encabezado documento
        'titulo':   s('PT', fontSize=18, textColor=colors.white,
                      alignment=TA_CENTER, fontName='Helvetica-Bold'),
        'subfecha': s('PF', fontSize=8,  textColor=colors.HexColor('#B0C4DE'),
                      alignment=TA_CENTER, fontName='Helvetica'),
        # cabecera de bodega
        'bod_t':    s('BT', fontSize=12, textColor=colors.white,
                      fontName='Helvetica-Bold', leftIndent=8),
        'bod_s':    s('BS', fontSize=8,  textColor=colors.HexColor('#B0C4DE'),
                      fontName='Helvetica', leftIndent=8),
        # separador de tipo
        'tipo_s':   s('TS', fontSize=8.5, textColor=_C_DARK,
                      fontName='Helvetica-Bold', leftIndent=8),
        # columnas
        'col_hdr':  s('CH', fontSize=8,  textColor=colors.white,
                      alignment=TA_CENTER, fontName='Helvetica-Bold', leading=10),
        'c_izq':    s('CI', fontSize=7.5, textColor=colors.HexColor('#1A1A1A'),
                      fontName='Helvetica', leading=10),
        'c_izq_b':  s('CB', fontSize=7.5, textColor=_C_DARK,
                      fontName='Helvetica-Bold', leading=10),
        'c_cnt':    s('CC', fontSize=7.5, textColor=colors.HexColor('#333333'),
                      alignment=TA_CENTER, fontName='Helvetica', leading=10),
        'c_sal':    s('CS', fontSize=8,   textColor=colors.HexColor('#1A5276'),
                      alignment=TA_RIGHT,  fontName='Helvetica-Bold', leading=10),
        'c_med':    s('CM', fontSize=7.5, textColor=colors.white,
                      alignment=TA_CENTER, fontName='Helvetica-Bold', leading=10),
        # resumen
        'res_hdr':  s('RH', fontSize=8.5, textColor=colors.white,
                      alignment=TA_CENTER, fontName='Helvetica-Bold'),
        'res_val':  s('RV', fontSize=8.5, textColor=_C_DARK,
                      alignment=TA_CENTER, fontName='Helvetica'),
        'res_tot':  s('RT', fontSize=9,   textColor=_C_DARK,
                      alignment=TA_CENTER, fontName='Helvetica-Bold'),
        # totales
        'tot_lbl':  s('TL', fontSize=8.5, textColor=_C_DARK,
                      alignment=TA_RIGHT,  fontName='Helvetica-Bold'),
        'tot_val':  s('TV', fontSize=9,   textColor=colors.HexColor('#1A5276'),
                      alignment=TA_RIGHT,  fontName='Helvetica-Bold'),
        # leyenda
        'ley_txt':  s('LT', fontSize=8,   textColor=colors.white,
                      fontName='Helvetica-Bold'),
        'ley_desc': s('LD', fontSize=8,   textColor=_C_DARK,
                      fontName='Helvetica'),
        'pie':      s('PP', fontSize=7,   textColor=colors.HexColor('#888888'),
                      alignment=TA_CENTER, fontName='Helvetica'),
    }


# Proporciones de columna compartidas entre resumen y tablas de bodega (con tipos)
_CW_PROPS = [2.0, 6.5, 2.2, 2.8, 1.3, 1.5, 2.2, 2.8, 1.7]


def _build_resumen(S, W, datos_inventario, fecha_str):
    """Construye la tabla de Resumen General con el mismo ancho que las tablas de bodega."""
    total_cw = sum(_CW_PROPS)
    CW = [W * (w / total_cw) for w in _CW_PROPS]

    # Encabezado: col 0-4 → "Bodega / Almacén", cols 5-8 → métricas
    hdr = [
        Paragraph('Bodega / Almacén',   S['res_hdr']),
        Paragraph('', S['res_hdr']),
        Paragraph('', S['res_hdr']),
        Paragraph('', S['res_hdr']),
        Paragraph('', S['res_hdr']),
        Paragraph('Productos', S['res_hdr']),
        Paragraph('Lotes',     S['res_hdr']),
        Paragraph('Saldo Total', S['res_hdr']),
        Paragraph('',          S['res_hdr']),
    ]
    rows = [hdr]

    resumen_info = []
    for cb, inv in datos_inventario.items():
        nb   = BODEGAS[cb]['nombre']
        prds = [p for p in inv.values() if p.get('lotes')]
        tl   = sum(len(p['lotes']) for p in prds)
        ts   = sum(l['saldo'] for p in prds for l in p['lotes'])
        resumen_info.append({'bodega': nb, 'productos': len(prds),
                              'lotes': tl, 'saldo': ts})

    tot_p = sum(r['productos'] for r in resumen_info)
    tot_l = sum(r['lotes']     for r in resumen_info)
    tot_s = sum(r['saldo']     for r in resumen_info)

    for r in resumen_info:
        rows.append([
            Paragraph(r['bodega'],        S['res_val']),
            Paragraph('', S['res_val']),
            Paragraph('', S['res_val']),
            Paragraph('', S['res_val']),
            Paragraph('', S['res_val']),
            Paragraph(str(r['productos']), S['res_val']),
            Paragraph(_fmt_n(r['lotes']),  S['res_val']),
            Paragraph(_fmt_n(r['saldo']),  S['res_val']),
            Paragraph('', S['res_val']),
        ])

    rows.append([
        Paragraph('TOTALES GENERALES', S['res_tot']),
        Paragraph('', S['res_tot']),
        Paragraph('', S['res_tot']),
        Paragraph('', S['res_tot']),
        Paragraph('', S['res_tot']),
        Paragraph(str(tot_p),   S['res_tot']),
        Paragraph(_fmt_n(tot_l), S['res_tot']),
        Paragraph(_fmt_n(tot_s), S['res_tot']),
        Paragraph('', S['res_tot']),
    ])

    n_r = len(rows)
    style_cmds = [
        # encabezado
        ('BACKGROUND',     (0, 0),      (-1, 0),       _C_DARK),
        ('SPAN',           (0, 0),      (4, 0)),
        # filas de datos
        ('ROWBACKGROUNDS', (0, 1),      (-1, n_r - 2), [_C_LIGHT, colors.white]),
        # fila de totales
        ('BACKGROUND',     (0, n_r-1),  (-1, n_r-1),   _C_DARK),
        # bordes
        ('GRID',           (0, 0),      (-1, -1),       0.5, _C_LINE),
        ('BOX',            (0, 0),      (-1, -1),       1.2, _C_DARK),
        ('LINEBELOW',      (0, 0),      (-1, 0),        1.5, _C_MID),
        # padding
        ('TOPPADDING',     (0, 0),      (-1, -1),       6),
        ('BOTTOMPADDING',  (0, 0),      (-1, -1),       6),
        ('LEFTPADDING',    (0, 0),      (-1, -1),       6),
        ('RIGHTPADDING',   (0, 0),      (-1, -1),       6),
        ('VALIGN',         (0, 0),      (-1, -1),       'MIDDLE'),
    ]
    # span bodega por cada fila de datos y totales
    for ri in range(1, n_r):
        style_cmds.append(('SPAN', (0, ri), (4, ri)))

    tbl = Table(rows, colWidths=CW)
    tbl.setStyle(TableStyle(style_cmds))
    return tbl


def _build_bodega_section(codigo_bodega, inv, S, W):
    """Retorna lista de flowables para una bodega. Empieza con título."""
    items = []
    nombre_bodega = BODEGAS[codigo_bodega]['nombre']
    tiene_tipos   = BODEGAS[codigo_bodega].get('tiene_tipos', False)

    prods = sorted(
        [p for p in inv.values() if p.get('lotes')],
        key=lambda d: (d.get('tipo', ''), d.get('medicamento', ''))
    )
    if not prods:
        return items

    total_s_b = sum(l['saldo'] for p in prods for l in p['lotes'])
    total_l_b = sum(len(p['lotes']) for p in prods)

    # ── Encabezado de bodega ──────────────────────────────────────
    tbl_bh = Table([
        [Paragraph(f'  {nombre_bodega.upper()}', S['bod_t'])],
        [Paragraph(
            f'  {len(prods)} productos  |  {_fmt_n(total_l_b)} lotes  |  '
            f'Saldo total: {_fmt_n(total_s_b)} unidades',
            S['bod_s'])],
    ], colWidths=[W])
    tbl_bh.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), _C_DARK),
        ('TOPPADDING',    (0, 0), (-1, 0),  10),
        ('BOTTOMPADDING', (0, 0), (-1, 0),  2),
        ('TOPPADDING',    (0, 1), (-1, 1),  2),
        ('BOTTOMPADDING', (0, 1), (-1, 1),  8),
        ('LINEBELOW',     (0, 1), (-1, 1),  2, _C_MID),
    ]))
    items.append(tbl_bh)
    items.append(Spacer(1, 6))

    # ── Definición de columnas ────────────────────────────────────
    if tiene_tipos:
        hdrs  = ['Código', 'Medicamento / Producto', 'Tipo', 'Presentación',
                 'Lote #', 'Saldo', 'F. Vencimiento', 'No. Lote', 'MED']
        CW_B  = _CW_PROPS                    # mismas proporciones que el resumen
    else:
        hdrs  = ['Código', 'Medicamento / Producto', 'Presentación',
                 'Lote #', 'Saldo', 'F. Vencimiento', 'No. Lote', 'MED']
        CW_B  = [2.0, 7.5, 2.8, 1.3, 1.5, 2.2, 2.8, 1.7]

    tcw   = sum(CW_B)
    cw    = [W * (w / tcw) for w in CW_B]
    n_col = len(hdrs)
    c_med = n_col - 1

    rows      = [[Paragraph(h, S['col_hdr']) for h in hdrs]]
    s_cmds    = []
    row_idx   = 1
    tipo_act  = '__INIT__'

    for pi, prod in enumerate(prods):
        tipo  = prod.get('tipo', '')
        lotes = prod.get('lotes', [])

        # separador de tipo
        if tiene_tipos and tipo != tipo_act:
            tipo_act = tipo
            ti  = TIPOS_INSUMO.get(tipo, {'nombre': tipo or 'Sin clasificar'})
            sep = ([Paragraph(f'   {ti.get("nombre", tipo)}', S['tipo_s'])]
                   + [Paragraph('', S['tipo_s'])] * (n_col - 1))
            rows.append(sep)
            s_cmds += [
                ('BACKGROUND', (0, row_idx), (-1, row_idx), _C_BAND),
                ('SPAN',       (0, row_idx), (-1, row_idx)),
                ('LINEABOVE',  (0, row_idx), (-1, row_idx), 0.8, _C_MID),
                ('LINEBELOW',  (0, row_idx), (-1, row_idx), 0.4, _C_LINE),
            ]
            row_idx += 1

        bg = _C_LIGHT if pi % 2 == 0 else colors.white

        for i_l, lote in enumerate(lotes):
            bg_med, _ = _pdf_color_med(lote.get('med', 'S/D'))
            md = _med_txt(lote.get('med', 'S/D'))

            if tiene_tipos:
                ti  = TIPOS_INSUMO.get(tipo, {'nombre': tipo or '—'})
                row = [
                    Paragraph(prod['codigo']                if i_l == 0 else '', S['c_izq_b']),
                    Paragraph(prod['medicamento']            if i_l == 0 else '', S['c_izq']),
                    Paragraph(ti.get('nombre', tipo)        if i_l == 0 else '', S['c_cnt']),
                    Paragraph(prod.get('presentacion', '')  if i_l == 0 else '', S['c_cnt']),
                    Paragraph(f'Lote {lote["numero"]}',     S['c_cnt']),
                    Paragraph(_fmt_n(lote['saldo']),         S['c_sal']),
                    Paragraph(str(lote.get('fv',  'S/D')),  S['c_cnt']),
                    Paragraph(str(lote.get('lote','S/D')),  S['c_cnt']),
                    Paragraph(md, S['c_med']),
                ]
            else:
                row = [
                    Paragraph(prod['codigo']                if i_l == 0 else '', S['c_izq_b']),
                    Paragraph(prod['medicamento']            if i_l == 0 else '', S['c_izq']),
                    Paragraph(prod.get('presentacion', '')  if i_l == 0 else '', S['c_cnt']),
                    Paragraph(f'Lote {lote["numero"]}',     S['c_cnt']),
                    Paragraph(_fmt_n(lote['saldo']),         S['c_sal']),
                    Paragraph(str(lote.get('fv',  'S/D')),  S['c_cnt']),
                    Paragraph(str(lote.get('lote','S/D')),  S['c_cnt']),
                    Paragraph(md, S['c_med']),
                ]

            rows.append(row)
            s_cmds.append(('BACKGROUND', (0,      row_idx), (c_med-1, row_idx), bg))
            s_cmds.append(('BACKGROUND', (c_med,  row_idx), (c_med,   row_idx), bg_med))
            row_idx += 1

    # fila total
    empty = [Paragraph('', S['c_izq'])] * (n_col - 3)
    rows.append(
        [Paragraph('TOTAL ALMACÉN', S['tot_lbl'])]
        + empty
        + [Paragraph(_fmt_n(total_s_b), S['tot_val'])]
        + [Paragraph('', S['c_cnt'])] * 2
    )
    s_cmds += [
        ('BACKGROUND', (0, row_idx), (-1, row_idx), _C_GRAY),
        ('LINEABOVE',  (0, row_idx), (-1, row_idx), 1.2, _C_DARK),
    ]

    base_cmds = [
        ('BACKGROUND',    (0, 0), (-1, 0),  _C_MID),
        ('GRID',          (0, 0), (-1, -1),  0.4, _C_LINE),
        ('BOX',           (0, 0), (-1, -1),  1.2, _C_DARK),
        ('LINEBELOW',     (0, 0), (-1, 0),   1.2, _C_DARK),
        ('TOPPADDING',    (0, 0), (-1, -1),  3),
        ('BOTTOMPADDING', (0, 0), (-1, -1),  3),
        ('LEFTPADDING',   (0, 0), (-1, -1),  4),
        ('RIGHTPADDING',  (0, 0), (-1, -1),  4),
        ('VALIGN',        (0, 0), (-1, -1),  'MIDDLE'),
    ]
    tbl = Table(rows, colWidths=cw, repeatRows=1)
    tbl.setStyle(TableStyle(base_cmds + s_cmds))
    items.append(tbl)
    return items


def _build_leyenda(S, W):
    """Tabla de leyenda del semáforo MED."""
    ley_rows = [[
        Paragraph('Semáforo MED — Meses de Existencia Disponible', S['res_hdr']),
        Paragraph('', S['res_hdr']),
        Paragraph('', S['res_hdr']),
    ]]
    datos_ley = [
        (colors.HexColor('#E74C3C'), '  1 – 12 meses',   'CRÍTICO — Reabastecer urgente'),
        (colors.HexColor('#E67E22'), '  13 – 17 meses',  'ALERTA — Monitorear'),
        (colors.HexColor('#27AE60'), '  18+ meses / S/D','ÓPTIMO — Stock suficiente'),
    ]
    for bg, rng, desc in datos_ley:
        ley_rows.append([
            Paragraph(rng,  S['ley_txt']),
            Paragraph(desc, S['ley_desc']),
            Paragraph('',   S['pie']),
        ])

    tbl = Table(ley_rows, colWidths=[W * 0.22, W * 0.52, W * 0.26])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  _C_DARK),
        ('SPAN',          (0, 0), (-1, 0)),
        ('BACKGROUND',    (0, 1), (0, 1),   colors.HexColor('#E74C3C')),
        ('BACKGROUND',    (0, 2), (0, 2),   colors.HexColor('#E67E22')),
        ('BACKGROUND',    (0, 3), (0, 3),   colors.HexColor('#27AE60')),
        ('GRID',          (0, 0), (-1, -1), 0.5, _C_LINE),
        ('BOX',           (0, 0), (-1, -1), 1.2, _C_DARK),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return tbl


# ── Endpoint Flask ────────────────────────────────────────────────

@app.route('/reporte-excel/todas-bodegas')
def reporte_excel_todas_bodegas():
    """
    Genera y descarga un PDF con el inventario completo de todas las bodegas.
    - Página 1: portada + tabla resumen (mismas proporciones que tablas de bodega)
    - Página siguiente por cada bodega (título + tabla completa)
    - Última sección: leyenda del semáforo MED
    - Número de página centrado al pie en todas las páginas
    """
    from flask import send_file

    fecha_reporte = obtener_hora_actual().strftime('%d/%m/%Y %H:%M:%S')
    fecha_archivo = obtener_hora_actual().strftime('%Y%m%d_%H%M')

    S   = _make_pdf_styles()
    buf = BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=1.2 * cm, rightMargin=1.2 * cm,
        topMargin=1.4 * cm,  bottomMargin=1.6 * cm,
        title='Reporte Inventario Médico',
        author='Sistema de Inventario',
    )
    W = doc.width
    story = []

    # ── Encabezado del documento ──────────────────────────────────
    tbl_t = Table(
        [[Paragraph('REPORTE GENERAL DE INVENTARIO MEDICO', S['titulo'])]],
        colWidths=[W])
    tbl_t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), _C_DARK),
        ('TOPPADDING',    (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(tbl_t)

    tbl_f = Table(
        [[Paragraph(
            f'Generado: {fecha_reporte}  |  Guatemala (UTC\u20126)',
            S['subfecha'])]],
        colWidths=[W])
    tbl_f.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), _C_MID),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(tbl_f)
    story.append(Spacer(1, 14))

    # ── Tabla Resumen ─────────────────────────────────────────────
    story.append(_build_resumen(S, W, datos_inventario, fecha_reporte))
    story.append(Spacer(1, 10))

    # ── Sección por bodega (cada una en página nueva) ─────────────
    for codigo_bodega, inv in datos_inventario.items():
        story.append(PageBreak())
        for fl in _build_bodega_section(codigo_bodega, inv, S, W):
            story.append(fl)

    # ── Leyenda semáforo ──────────────────────────────────────────
    story.append(Spacer(1, 14))
    story.append(_build_leyenda(S, W))

    # ── Número de página al pie ───────────────────────────────────
    def _on_page(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(colors.HexColor('#AAAAAA'))
        canvas.drawCentredString(
            doc.pagesize[0] / 2, 0.65 * cm,
            f'Página {doc.page}  |  Sistema de Inventario Multi-Bodega  |  {fecha_reporte}'
        )
        canvas.restoreState()

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    buf.seek(0)

    return send_file(
        buf,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'inventario_todas_bodegas_{fecha_archivo}.pdf'
    )

# =============================================================================
# MÓDULO: EDITOR WEB DE INVENTARIO
# Pega este bloque completo al FINAL de tu flask_app.py
# =============================================================================

import secrets as _secrets_module

if not app.secret_key:
    app.secret_key = _secrets_module.token_hex(32)

# ─── Rutas y configuración ───────────────────────────────────────────────────
RUTA_DB = '/home/salonso/mysite/inventario_usuarios.db'

RUTA_EXCEL_BODEGAS = {
    'medico':       '/home/salonso/mysite/inventario_medico.xlsx',
    'medicamentos': '/home/salonso/mysite/inventario_medicamentos.xlsx',
    'limpieza':     '/home/salonso/mysite/inventario_limpieza.xlsx',
    'oficina':      '/home/salonso/mysite/inventario_oficina.xlsx',
    'varios':       '/home/salonso/mysite/inventario_varios.xlsx',
    'programas':    '/home/salonso/mysite/inventario_programas.xlsx',
}

BODEGAS_LABELS = {
    'medico':       'Material Médico / Quirúrgico',
    'medicamentos': 'Medicamentos',
    'limpieza':     'Limpieza',
    'oficina':      'Oficina',
    'varios':       'Varios',
    'programas':    'Programas',
}

# Mapeo BD → clave interna  (la BD guarda "BODEGA_LIMPIEZA", el código usa "limpieza")
_BODEGA_DB_MAP = {
    'BODEGA_MEDICO':       'medico',
    'BODEGA_MEDICAMENTOS': 'medicamentos',
    'BODEGA_LIMPIEZA':     'limpieza',
    'BODEGA_OFICINA':      'oficina',
    'BODEGA_VARIOS':       'varios',
    'BODEGA_PROGRAMAS':    'programas',
}
# Inverso: clave interna → valor para guardar en BD
_BODEGA_BD_INVERSO = {v: k for k, v in _BODEGA_DB_MAP.items()}

# Columnas Excel (base-1 para openpyxl)
COLS_LOTES = [
    {'fv': 7,  'lote': 8,  'saldo': 9,  'precio_uni': 28, 'precio_tot': 33},
    {'fv': 10, 'lote': 11, 'saldo': 12, 'precio_uni': 29, 'precio_tot': 34},
    {'fv': 13, 'lote': 14, 'saldo': 15, 'precio_uni': 30, 'precio_tot': 35},
    {'fv': 16, 'lote': 17, 'saldo': 18, 'precio_uni': 31, 'precio_tot': 36},
    {'fv': 19, 'lote': 20, 'saldo': 21, 'precio_uni': 32, 'precio_tot': 37},
]
EXCEL_FILA_INICIO_DATOS = 6
COL_NOMBRE      = 2    # col B
COL_CODIGO      = 1    # col A
COL_TIPO        = 3    # col C  (Tipo de Insumo: LAB, LAB-SAN, MQ, MQ-ODONT…)
COL_TARJETA     = 40   # col AN
HOJA_INVENTARIO = 'Inventario General'

# Columnas MED (Meses de Existencia Disponible) — base 1
COL_MED = [23, 24, 25, 26, 27]   # W=MED1, X=MED2, Y=MED3, Z=MED4, AA=MED5

# Umbrales semáforo por MED
MED_VERDE_MIN    = 18   # MED > 18  → 🟢 Óptimo
MED_AMARILLO_MIN = 13   # MED 13-17 → 🟡 En Alerta
                        # MED  1-12 → 🔴 Crítico
                        # MED  = 0  → sin saldo (excluir del semáforo)


# =============================================================================
# HELPERS
# =============================================================================

def _normalizar_bodega(valor_db):
    if not valor_db:
        return ''
    if valor_db in BODEGAS_LABELS:
        return valor_db
    norm = _BODEGA_DB_MAP.get(valor_db.upper().strip())
    if norm:
        return norm
    sin_pref = valor_db.upper().replace('BODEGA_', '').lower().strip()
    return sin_pref if sin_pref in BODEGAS_LABELS else ''


def _editor_requiere_login():
    if 'editor_usuario' not in session:
        return redirect('/editor/login')
    return None


def _editor_requiere_admin():
    redir = _editor_requiere_login()
    if redir:
        return redir
    if session.get('editor_rol') != 'Admin':
        return redirect('/editor/dashboard')
    return None


def _editor_puede_acceder_bodega(bodega):
    if session.get('editor_rol') == 'Admin':
        return True
    return bodega == session.get('editor_bodega_asignada', '')


def _leer_todos_productos_editor(bodega):
    """Lee TODOS los productos del Excel. Retorna [{codigo, nombre, tiene_saldo, saldo_total}]."""
    ruta = RUTA_EXCEL_BODEGAS.get(bodega)
    if not ruta:
        return []
    try:
        from openpyxl import load_workbook
        wb = load_workbook(ruta, read_only=True, data_only=True)
        if HOJA_INVENTARIO not in wb.sheetnames:
            wb.close(); return []
        ws = wb[HOJA_INVENTARIO]
        codigos_con_saldo = set(str(k).strip() for k in datos_inventario.get(bodega, {}).keys())
        productos = []
        for row in ws.iter_rows(min_row=EXCEL_FILA_INICIO_DATOS, values_only=True):
            codigo = row[COL_CODIGO - 1]
            nombre = row[COL_NOMBRE - 1]
            cod_s  = str(codigo).strip() if codigo is not None else ''
            nom_s  = str(nombre).strip() if nombre is not None else ''
            if not cod_s and not nom_s:
                continue
            tiene_saldo = cod_s in codigos_con_saldo
            saldo_total = 0.0
            if tiene_saldo:
                for lote in datos_inventario.get(bodega, {}).get(cod_s, {}).get('lotes', []):
                    s = lote.get('saldo')
                    if s is not None:
                        try: saldo_total += float(s)
                        except Exception: pass
            # Leer MED de las columnas W-AA (23-27, base-1 → índice 22-26 base-0)
            med_vals = []
            for col_1b in COL_MED:
                idx = col_1b - 1
                v   = row[idx] if idx < len(row) else None
                if v is not None:
                    try:
                        fv = float(v)
                        if fv > 0:
                            med_vals.append(fv)
                    except Exception:
                        pass
            # Usar el mínimo MED no-cero (lote más crítico)
            med_valor = round(min(med_vals), 1) if med_vals else 0.0
            # Leer Tipo de Insumo (col C)
            tipo_raw = row[COL_TIPO - 1]
            tipo = str(tipo_raw).strip() if tipo_raw is not None else ''
            productos.append({'codigo': cod_s, 'nombre': nom_s,
                               'tiene_saldo': tiene_saldo,
                               'saldo_total': round(saldo_total, 2),
                               'med_valor':   med_valor,
                               'tipo':        tipo})
        wb.close()
        productos.sort(key=lambda x: x['nombre'])
        return productos
    except Exception:
        return []


def _leer_lotes_editor(bodega, codigo):
    """Lee lotes de un producto buscando por código (col A). Retorna dict o None."""
    ruta = RUTA_EXCEL_BODEGAS.get(bodega)
    if not ruta:
        return None
    try:
        from openpyxl import load_workbook
        from datetime import datetime as _dt, date as _date
        wb = load_workbook(ruta, data_only=True)
        if HOJA_INVENTARIO not in wb.sheetnames:
            wb.close(); return None
        ws  = wb[HOJA_INVENTARIO]
        cod = str(codigo).strip()
        for fila in range(EXCEL_FILA_INICIO_DATOS, ws.max_row + 1):
            celda = ws.cell(row=fila, column=COL_CODIGO).value
            if celda is None or str(celda).strip() != cod:
                continue
            nombre  = ws.cell(row=fila, column=COL_NOMBRE).value or ''
            tarjeta = ws.cell(row=fila, column=COL_TARJETA).value
            lotes   = []
            for i, cols in enumerate(COLS_LOTES):
                fv_val  = ws.cell(row=fila, column=cols['fv']).value
                fv_str  = ''
                if fv_val is not None:
                    try:
                        fv_str = fv_val.strftime('%d/%m/%Y') if isinstance(fv_val, (_dt, _date)) \
                                 else str(fv_val).strip()
                    except Exception:
                        fv_str = str(fv_val)
                lotes.append({
                    'numero': i + 1,
                    'fv':     fv_str,
                    'lote':   str(ws.cell(row=fila, column=cols['lote']).value or '').strip(),
                    'saldo':  ws.cell(row=fila, column=cols['saldo']).value,
                    'precio_unitario':   ws.cell(row=fila, column=cols['precio_uni']).value,
                    'precio_total_lote': ws.cell(row=fila, column=cols['precio_tot']).value,
                })
            wb.close()
            return {'codigo': cod, 'nombre': str(nombre).strip(),
                    'tarjeta_kardex': str(tarjeta).strip() if tarjeta is not None else '',
                    'lotes': lotes}
        wb.close(); return None
    except Exception:
        return None


def _guardar_lotes_excel(bodega, codigo_producto, lotes_nuevos, tarjeta_kardex=None):
    """Guarda lotes buscando por código (col A). Retorna (True, None) o (False, msg)."""
    ruta = RUTA_EXCEL_BODEGAS.get(bodega)
    if not ruta:
        return False, f'Bodega "{bodega}" no reconocida'
    try:
        from openpyxl import load_workbook
        wb = load_workbook(ruta)
        if HOJA_INVENTARIO not in wb.sheetnames:
            return False, f'Hoja "{HOJA_INVENTARIO}" no encontrada'
        ws  = wb[HOJA_INVENTARIO]
        cod = str(codigo_producto).strip()
        fila_p = None
        for fila in range(EXCEL_FILA_INICIO_DATOS, ws.max_row + 1):
            v = ws.cell(row=fila, column=COL_CODIGO).value
            if v is not None and str(v).strip() == cod:
                fila_p = fila; break
        if fila_p is None:
            return False, f'Código "{codigo_producto}" no encontrado en bodega "{bodega}"'

        if tarjeta_kardex is not None:
            ws.cell(row=fila_p, column=COL_TARJETA).value = tarjeta_kardex or None

        def _f(v):
            if v is None or str(v).strip() == '': return None
            try: return float(str(v).replace(',', '.'))
            except: return None

        for i, ld in enumerate(lotes_nuevos[:5]):
            cols  = COLS_LOTES[i]
            fv    = ld.get('fv', '')
            if fv:
                try:
                    from datetime import datetime as _dt
                    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
                        try: fv = _dt.strptime(str(fv), fmt); break
                        except ValueError: pass
                except Exception: pass
            else:
                fv = None
            ws.cell(row=fila_p, column=cols['fv']).value         = fv
            ws.cell(row=fila_p, column=cols['lote']).value        = ld.get('lote', '') or None
            ws.cell(row=fila_p, column=cols['saldo']).value       = _f(ld.get('saldo'))
            ws.cell(row=fila_p, column=cols['precio_uni']).value  = _f(ld.get('precio_unitario'))
            ws.cell(row=fila_p, column=cols['precio_tot']).value  = _f(ld.get('precio_total_lote'))

        wb.save(ruta)
        return True, None
    except Exception as e:
        return False, str(e)


# =============================================================================
# RUTAS PRINCIPALES
# =============================================================================

@app.route('/editor')
def editor_inicio():
    if 'editor_usuario' not in session:
        return redirect('/editor/login')
    return redirect('/editor/dashboard')


@app.route('/editor/login', methods=['GET', 'POST'])
def editor_login():
    error = ''
    if request.method == 'POST':
        usuario_form  = request.form.get('usuario',  '').strip()
        password_form = request.form.get('password', '').strip()
        pw_hash = hashlib.sha256(password_form.encode()).hexdigest()
        try:
            conn = sqlite3.connect(RUTA_DB)
            cur  = conn.cursor()
            cur.execute(
                "SELECT id, nombre_completo, rol, bodega_asignada "
                "FROM usuarios WHERE username=? AND password=? AND activo=1",
                (usuario_form, pw_hash))
            user = cur.fetchone()
            conn.close()
        except Exception as e:
            error = f'Error de base de datos: {e}'; user = None

        if user:
            session['editor_usuario']         = usuario_form
            session['editor_nombre']          = user[1] or usuario_form
            session['editor_user_id']         = user[0]
            session['editor_rol']             = user[2] or 'User'
            session['editor_bodega_asignada'] = _normalizar_bodega(user[3])
            return redirect('/editor/dashboard')
        elif not error:
            error = 'Usuario o contraseña incorrectos'

    return render_template_string(_EDITOR_LOGIN_HTML, error=error)


@app.route('/editor/salir')
def editor_salir():
    for k in ['editor_usuario', 'editor_nombre', 'editor_user_id',
              'editor_rol', 'editor_bodega_asignada']:
        session.pop(k, None)
    return redirect('/editor/login')


@app.route('/editor/dashboard')
def editor_dashboard():
    redir = _editor_requiere_login()
    if redir: return redir
    nombre_usuario  = session.get('editor_nombre', session.get('editor_usuario', ''))
    rol             = session.get('editor_rol', 'User')
    bodega_asignada = session.get('editor_bodega_asignada', '')

    if rol == 'Admin':
        bodegas_usuario = BODEGAS_LABELS
        bodega_auto     = ''
    elif bodega_asignada and bodega_asignada in BODEGAS_LABELS:
        bodegas_usuario = {bodega_asignada: BODEGAS_LABELS[bodega_asignada]}
        bodega_auto     = bodega_asignada
    else:
        bodegas_usuario = {}
        bodega_auto     = ''

    return render_template_string(
        _EDITOR_DASHBOARD_HTML,
        nombre_usuario=nombre_usuario,
        bodegas=bodegas_usuario,
        es_admin=(rol == 'Admin'),
        bodega_auto=bodega_auto,
    )


# =============================================================================
# API JSON
# =============================================================================

@app.route('/editor/api/productos')
def editor_api_productos():
    redir = _editor_requiere_login()
    if redir: return jsonify({'error': 'No autenticado'}), 401
    bodega   = request.args.get('bodega', '').strip().lower()
    busqueda = request.args.get('q', '').strip().lower()
    if bodega not in RUTA_EXCEL_BODEGAS:
        return jsonify({'error': 'Bodega no válida'}), 400
    if not _editor_puede_acceder_bodega(bodega):
        return jsonify({'error': 'Acceso no autorizado'}), 403
    todos = _leer_todos_productos_editor(bodega)
    if busqueda:
        todos = [p for p in todos if busqueda in p['nombre'].lower() or busqueda in p['codigo'].lower()]
    return jsonify(todos)


@app.route('/editor/api/lotes')
def editor_api_lotes():
    redir = _editor_requiere_login()
    if redir: return jsonify({'error': 'No autenticado'}), 401
    bodega = request.args.get('bodega', '').strip().lower()
    codigo = request.args.get('codigo', '').strip()
    if bodega not in RUTA_EXCEL_BODEGAS:
        return jsonify({'error': 'Bodega no válida'}), 400
    if not _editor_puede_acceder_bodega(bodega):
        return jsonify({'error': 'Acceso no autorizado'}), 403
    if not codigo:
        return jsonify({'error': 'Parámetro "codigo" requerido'}), 400
    resultado = _leer_lotes_editor(bodega, codigo)
    if resultado is None:
        return jsonify({'error': f'Código "{codigo}" no encontrado'}), 404
    return jsonify(resultado)


@app.route('/editor/api/guardar', methods=['POST'])
def editor_api_guardar():
    redir = _editor_requiere_login()
    if redir: return jsonify({'error': 'No autenticado'}), 401
    data   = request.get_json(force=True) or {}
    bodega = data.get('bodega', '').strip().lower()
    codigo = data.get('codigo', '').strip()
    lotes  = data.get('lotes', [])
    tarjeta_kardex = data.get('tarjeta_kardex', None)
    if not bodega or not codigo:
        return jsonify({'error': 'bodega y codigo son requeridos'}), 400
    if bodega not in RUTA_EXCEL_BODEGAS:
        return jsonify({'error': 'Bodega no válida'}), 400
    if not _editor_puede_acceder_bodega(bodega):
        return jsonify({'error': 'Acceso no autorizado'}), 403
    ok, msg = _guardar_lotes_excel(bodega, codigo, lotes, tarjeta_kardex)
    if ok:
        try: cargar_datos_bodega(bodega, RUTA_EXCEL_BODEGAS[bodega])
        except Exception: pass
        return jsonify({'ok': True})
    return jsonify({'ok': False, 'error': msg}), 500


@app.route('/editor/api/dashboard')
def editor_api_dashboard():
    redir = _editor_requiere_login()
    if redir: return jsonify({'error': 'No autenticado'}), 401
    rol             = session.get('editor_rol', 'User')
    bodega_asignada = session.get('editor_bodega_asignada', '')
    bodegas_q = list(BODEGAS_LABELS.keys()) if rol == 'Admin' \
                else ([bodega_asignada] if bodega_asignada else [])
    resultado = {}
    tot = {'total': 0, 'verde': 0, 'amarillo': 0, 'rojo': 0}
    tipos_global = {}   # desglose por Tipo de Insumo (col C) a nivel global
    for bodega in bodegas_q:
        todos = _leer_todos_productos_editor(bodega)
        v = a = r = con_med = 0
        tipos_local = {}
        for p in todos:
            mv = p['med_valor']
            if mv == 0:
                continue          # sin saldo → no cuenta en semáforo
            con_med += 1
            if   mv > MED_VERDE_MIN:    v += 1; color = 'verde'
            elif mv >= MED_AMARILLO_MIN: a += 1; color = 'amarillo'
            else:                        r += 1; color = 'rojo'
            # desglose por tipo
            tipo = p.get('tipo', '') or 'Sin Tipo'
            if tipo not in tipos_local:
                tipos_local[tipo] = {'total': 0, 'verde': 0, 'amarillo': 0, 'rojo': 0}
            tipos_local[tipo]['total']  += 1
            tipos_local[tipo][color]    += 1
            if tipo not in tipos_global:
                tipos_global[tipo] = {'total': 0, 'verde': 0, 'amarillo': 0, 'rojo': 0}
            tipos_global[tipo]['total'] += 1
            tipos_global[tipo][color]   += 1
        resultado[bodega] = {'label':    BODEGAS_LABELS.get(bodega, bodega),
                             'total':    con_med,
                             'verde':    v, 'amarillo': a, 'rojo': r,
                             'tipos':    tipos_local}
        tot['total']    += con_med
        tot['verde']    += v
        tot['amarillo'] += a
        tot['rojo']     += r
    return jsonify({
        'bodegas':  resultado,
        'totales':  tot,
        'por_tipo': tipos_global,
        'umbrales': {'verde_min': MED_VERDE_MIN, 'amarillo_min': MED_AMARILLO_MIN},
    })


# =============================================================================
# GESTIÓN DE USUARIOS  (solo Admin)
# =============================================================================

@app.route('/editor/usuarios')
def editor_usuarios():
    redir = _editor_requiere_admin()
    if redir: return redir
    try:
        conn = sqlite3.connect(RUTA_DB)
        conn.row_factory = sqlite3.Row
        cur  = conn.cursor()
        cur.execute("SELECT id, username, nombre_completo, email, rol, "
                    "bodega_asignada, activo, fecha_creacion "
                    "FROM usuarios ORDER BY rol, username")
        usuarios = [dict(r) for r in cur.fetchall()]
        conn.close()
    except Exception:
        usuarios = []
    return render_template_string(
        _EDITOR_USUARIOS_HTML,
        usuarios=usuarios, bodegas=BODEGAS_LABELS,
        nombre_usuario=session.get('editor_nombre', ''),
        mensaje=request.args.get('msg', ''),
        error=request.args.get('err', ''),
    )


@app.route('/editor/usuarios/nuevo', methods=['GET', 'POST'])
def editor_usuario_nuevo():
    redir = _editor_requiere_admin()
    if redir: return redir
    error = ''
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        nombre   = request.form.get('nombre_completo', '').strip()
        email    = request.form.get('email', '').strip()
        rol      = request.form.get('rol', 'User').strip()
        bodega_c = request.form.get('bodega_asignada', '').strip()
        activo   = 1 if request.form.get('activo') else 0
        if not username or not password:
            error = 'Usuario y contraseña son obligatorios.'
        else:
            bodega_bd = _BODEGA_BD_INVERSO.get(bodega_c, '') if bodega_c else ''
            pw_hash   = hashlib.sha256(password.encode()).hexdigest()
            try:
                conn = sqlite3.connect(RUTA_DB)
                cur  = conn.cursor()
                cur.execute(
                    "INSERT INTO usuarios (username, password, nombre_completo, email, "
                    "rol, bodega_asignada, activo) VALUES (?,?,?,?,?,?,?)",
                    (username, pw_hash, nombre, email, rol, bodega_bd or None, activo))
                conn.commit(); conn.close()
                return redirect('/editor/usuarios?msg=Usuario+creado+correctamente')
            except sqlite3.IntegrityError:
                error = f'El usuario "{username}" ya existe.'
            except Exception as e:
                error = f'Error al crear usuario: {e}'
    return render_template_string(
        _EDITOR_USUARIO_FORM_HTML,
        accion='nuevo', usuario=None, bodegas=BODEGAS_LABELS,
        nombre_usuario=session.get('editor_nombre', ''), error=error)


@app.route('/editor/usuarios/editar/<int:uid>', methods=['GET', 'POST'])
def editor_usuario_editar(uid):
    redir = _editor_requiere_admin()
    if redir: return redir
    error = ''
    try:
        conn = sqlite3.connect(RUTA_DB)
        conn.row_factory = sqlite3.Row
        cur  = conn.cursor()
        cur.execute("SELECT * FROM usuarios WHERE id=?", (uid,))
        row = cur.fetchone(); conn.close()
        if not row: return redirect('/editor/usuarios?err=Usuario+no+encontrado')
        usuario = dict(row)
        usuario['bodega_asignada_clave'] = _normalizar_bodega(usuario.get('bodega_asignada') or '')
    except Exception as e:
        return redirect(f'/editor/usuarios?err=Error:+{e}')

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        nombre   = request.form.get('nombre_completo', '').strip()
        email    = request.form.get('email', '').strip()
        rol      = request.form.get('rol', 'User').strip()
        bodega_c = request.form.get('bodega_asignada', '').strip()
        activo   = 1 if request.form.get('activo') else 0
        if not username:
            error = 'El nombre de usuario es obligatorio.'
        else:
            bodega_bd = _BODEGA_BD_INVERSO.get(bodega_c, '') if bodega_c else ''
            try:
                conn = sqlite3.connect(RUTA_DB)
                cur  = conn.cursor()
                if password:
                    pw_hash = hashlib.sha256(password.encode()).hexdigest()
                    cur.execute(
                        "UPDATE usuarios SET username=?, password=?, nombre_completo=?, "
                        "email=?, rol=?, bodega_asignada=?, activo=? WHERE id=?",
                        (username, pw_hash, nombre, email, rol, bodega_bd or None, activo, uid))
                else:
                    cur.execute(
                        "UPDATE usuarios SET username=?, nombre_completo=?, email=?, "
                        "rol=?, bodega_asignada=?, activo=? WHERE id=?",
                        (username, nombre, email, rol, bodega_bd or None, activo, uid))
                conn.commit(); conn.close()
                return redirect('/editor/usuarios?msg=Usuario+actualizado+correctamente')
            except sqlite3.IntegrityError:
                error = f'El nombre "{username}" ya está en uso.'
            except Exception as e:
                error = f'Error al actualizar: {e}'
    return render_template_string(
        _EDITOR_USUARIO_FORM_HTML,
        accion='editar', usuario=usuario, bodegas=BODEGAS_LABELS,
        nombre_usuario=session.get('editor_nombre', ''), error=error)


@app.route('/editor/usuarios/eliminar/<int:uid>', methods=['POST'])
def editor_usuario_eliminar(uid):
    redir = _editor_requiere_admin()
    if redir: return redir
    if uid == session.get('editor_user_id'):
        return redirect('/editor/usuarios?err=No+puedes+eliminar+tu+propia+cuenta')
    try:
        conn = sqlite3.connect(RUTA_DB)
        cur  = conn.cursor()
        cur.execute("DELETE FROM usuarios WHERE id=?", (uid,))
        conn.commit(); conn.close()
        return redirect('/editor/usuarios?msg=Usuario+eliminado+correctamente')
    except Exception as e:
        return redirect(f'/editor/usuarios?err=Error+al+eliminar:+{e}')


# =============================================================================
# HTML: LOGIN
# =============================================================================
_EDITOR_LOGIN_HTML = '''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Editor de Inventario – Iniciar Sesión</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:linear-gradient(135deg,#0d4f2e,#1a7a45,#0d4f2e);min-height:100vh;display:flex;align-items:center;justify-content:center}
.card{background:#fff;border-radius:16px;box-shadow:0 20px 60px rgba(0,0,0,.35);padding:48px 40px 40px;width:100%;max-width:400px}
.logo{text-align:center;margin-bottom:32px}
.logo-icon{width:64px;height:64px;background:linear-gradient(135deg,#1a7a45,#0d4f2e);border-radius:16px;display:inline-flex;align-items:center;justify-content:center;font-size:30px;margin-bottom:12px}
.logo h1{font-size:22px;color:#0d4f2e;font-weight:700}
.logo p{font-size:13px;color:#666;margin-top:4px}
.fg{margin-bottom:20px}
label{display:block;font-size:13px;font-weight:600;color:#374151;margin-bottom:6px}
input[type=text],input[type=password]{width:100%;padding:12px 14px;border:2px solid #e5e7eb;border-radius:8px;font-size:15px;outline:none;transition:border-color .2s}
input:focus{border-color:#1a7a45}
.btn{width:100%;padding:13px;background:linear-gradient(135deg,#1a7a45,#0d4f2e);color:#fff;border:none;border-radius:8px;font-size:16px;font-weight:600;cursor:pointer;transition:opacity .2s;margin-top:8px}
.btn:hover{opacity:.9}
.err{background:#fef2f2;border:1px solid #fca5a5;color:#dc2626;border-radius:8px;padding:10px 14px;font-size:13px;margin-bottom:20px}
</style></head><body>
<div class="card">
  <div class="logo">
    <div class="logo-icon">🏥</div>
    <h1>Editor de Inventario</h1>
    <p>Sistema de gestión de lotes y precios</p>
  </div>
  {% if error %}<div class="err">⚠️ {{ error }}</div>{% endif %}
  <form method="POST" action="/editor/login">
    <div class="fg"><label>Usuario</label><input type="text" name="usuario" placeholder="Ingresa tu usuario" autocomplete="username" required></div>
    <div class="fg"><label>Contraseña</label><input type="password" name="password" placeholder="••••••••" autocomplete="current-password" required></div>
    <button type="submit" class="btn">Iniciar Sesión →</button>
  </form>
</div></body></html>'''


# =============================================================================
# HTML: DASHBOARD PRINCIPAL
# =============================================================================
_EDITOR_DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Editor de Inventario</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#f0f4f8;min-height:100vh}

/* NAV */
nav{background:linear-gradient(135deg,#0d4f2e,#1a7a45);color:#fff;padding:0 24px;
    display:flex;align-items:center;justify-content:space-between;height:56px;
    box-shadow:0 2px 8px rgba(0,0,0,.2)}
.nav-title{font-size:18px;font-weight:700;display:flex;align-items:center;gap:10px}
.nav-right{display:flex;align-items:center;gap:12px;font-size:13px}
.nav-user{background:rgba(255,255,255,.15);border-radius:20px;padding:4px 14px}
.nav-rol{font-size:11px;opacity:.75}
.nav-btn{background:rgba(255,255,255,.2);border:1px solid rgba(255,255,255,.4);color:#fff;
         border-radius:6px;padding:5px 14px;text-decoration:none;font-size:13px;transition:background .2s}
.nav-btn:hover{background:rgba(255,255,255,.35)}

/* LAYOUT */
.container{display:flex;height:calc(100vh - 56px)}

/* SIDEBAR */
.sidebar{width:320px;min-width:280px;background:#fff;border-right:1px solid #e2e8f0;
         display:flex;flex-direction:column;overflow:hidden}
.sb-header{padding:16px;border-bottom:1px solid #e2e8f0;background:#f8fafc}
.sb-header h2{font-size:14px;color:#374151;font-weight:600;margin-bottom:12px}
select,.search-input{width:100%;padding:9px 12px;border:1.5px solid #d1d5db;
  border-radius:8px;font-size:13px;outline:none;background:#fff;transition:border-color .2s}
select:focus,.search-input:focus{border-color:#1a7a45}
.search-wrap{margin-top:10px;position:relative}
.search-wrap input{padding-left:34px}
.search-icon{position:absolute;left:10px;top:50%;transform:translateY(-50%);color:#9ca3af;font-size:15px;pointer-events:none}
.product-list{flex:1;overflow-y:auto}

/* TREE */
details.tg summary{list-style:none;padding:8px 14px;cursor:pointer;font-size:11px;font-weight:700;
  text-transform:uppercase;letter-spacing:.6px;background:#f1f5f9;border-bottom:1px solid #e2e8f0;
  user-select:none;display:flex;align-items:center;gap:6px}
details.tg summary::-webkit-details-marker{display:none}
details.tg summary::marker{display:none}
details.tg summary:hover{background:#e8edf3}
.ta{transition:transform .2s;display:inline-block;font-size:9px}
details.tg[open] summary .ta{transform:rotate(90deg)}
.tc{margin-left:auto;background:#e2e8f0;border-radius:10px;padding:1px 8px;font-size:11px;color:#374151}
.tg-cs summary{color:#15803d}
.tg-ss summary{color:#6b7280}

/* PRODUCT ITEMS */
.pi{padding:10px 16px;cursor:pointer;border-bottom:1px solid #f3f4f6;transition:background .15s}
.pi:hover{background:#f0fdf4}
.pi.active{background:#dcfce7;border-left:3px solid #1a7a45}
.pi-name{font-size:13px;font-weight:600;color:#1f2937;display:flex;align-items:center}
.pi-code{font-size:11px;color:#6b7280;margin-top:2px;margin-left:14px}
.dot{width:8px;height:8px;min-width:8px;border-radius:50%;display:inline-block;margin-right:6px}
.list-empty{padding:24px 16px;text-align:center;color:#9ca3af;font-size:13px}
.list-loading{padding:24px 16px;text-align:center;color:#6b7280;font-size:13px}

/* MAIN PANEL */
.main-panel{flex:1;display:flex;flex-direction:column;overflow:hidden}

/* ── DASHBOARD ── */
.dash-scroll{flex:1;overflow-y:auto;padding:24px}
.dash-topbar{display:flex;align-items:flex-start;justify-content:space-between;
             margin-bottom:24px;gap:12px;flex-wrap:wrap}
.dash-topbar h2{font-size:20px;font-weight:800;color:#0d4f2e}
.dash-topbar p{font-size:12px;color:#6b7280;margin-top:3px}
.btn-refresh{background:#f1f5f9;border:1px solid #e2e8f0;border-radius:8px;
             padding:7px 16px;font-size:12px;font-weight:600;color:#374151;
             cursor:pointer;white-space:nowrap;transition:background .2s;flex-shrink:0}
.btn-refresh:hover{background:#e2e8f0}
.filtro-banner{background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;
               padding:10px 16px;margin-bottom:20px;display:none;
               align-items:center;gap:10px;font-size:13px;font-weight:600;color:#1e40af}
.filtro-banner button{background:none;border:none;cursor:pointer;font-size:18px;
                      color:#6b7280;margin-left:auto;line-height:1}
.filtro-banner button:hover{color:#374151}

/* SEMAPHORE CARDS */
.dash-cards{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}
.dc{background:#fff;border-radius:12px;padding:20px 18px;
    box-shadow:0 2px 8px rgba(0,0,0,.06);border:2px solid transparent;transition:all .2s}
.dc.clickable{cursor:pointer}
.dc.clickable:hover{transform:translateY(-3px);box-shadow:0 6px 20px rgba(0,0,0,.12)}
.dc.active-filter{border-color:currentColor;box-shadow:0 4px 16px rgba(0,0,0,.12)}
.dc-icon{font-size:28px;margin-bottom:10px}
.dc-num{font-size:38px;font-weight:800;line-height:1}
.dc-label{font-size:11px;color:#6b7280;margin-top:6px;text-transform:uppercase;letter-spacing:.6px;font-weight:600}
.dc-pct{font-size:12px;font-weight:700;margin-top:4px}
.dc-total .dc-num{color:#1e40af}
.dc-verde{color:#15803d} .dc-verde .dc-num{color:#15803d}
.dc-amar{color:#92400e}  .dc-amar .dc-num{color:#d97706}
.dc-rojo{color:#dc2626}  .dc-rojo .dc-num{color:#dc2626}

/* CHARTS */
.dash-charts{display:grid;grid-template-columns:1fr 1.6fr;gap:20px;margin-bottom:24px}
.chart-card{background:#fff;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,.06)}
.chart-card h3{font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;
               letter-spacing:.6px;margin-bottom:16px;transition:color .3s}
.chart-wrap{position:relative;height:200px}
.chart-wrap-bar{position:relative;height:200px;transition:height .3s}

/* BODEGA TABLE */
.bodega-card{background:#fff;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,.06);margin-bottom:16px}
.section-title{font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:.5px;margin-bottom:12px}
.bt{width:100%;border-collapse:collapse;font-size:13px}
.bt th{text-align:left;padding:8px 12px;font-size:11px;font-weight:700;text-transform:uppercase;
       letter-spacing:.5px;color:#6b7280;border-bottom:2px solid #f0f0f0;background:#f8fafc}
.bt td{padding:10px 12px;border-bottom:1px solid #f5f5f5;vertical-align:middle}
.bt tr:last-child td{border-bottom:none}
.bt tr:hover td{background:#f9fafb}
.semabar{display:flex;height:8px;border-radius:4px;overflow:hidden;min-width:80px}
.s-v{background:#22c55e} .s-a{background:#f59e0b} .s-r{background:#ef4444}
.umbral-note{font-size:11px;color:#9ca3af;margin-top:10px;text-align:right}

/* EDIT AREA */
.edit-scroll{flex:1;overflow-y:auto;padding:24px}
.back-bar{margin-bottom:16px}
.btn-back{background:#f1f5f9;border:1px solid #e2e8f0;border-radius:8px;
          padding:8px 18px;font-size:13px;font-weight:600;color:#374151;
          cursor:pointer;display:inline-flex;align-items:center;gap:6px;transition:background .2s}
.btn-back:hover{background:#e2e8f0}

/* EDIT CARD */
.edit-card{background:#fff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,.08);overflow:hidden}
.edit-header{background:linear-gradient(135deg,#0d4f2e,#1a7a45);color:#fff;padding:20px 24px}
.edit-header h2{font-size:18px;font-weight:700}
.edit-header .meta{font-size:12px;opacity:.8;margin-top:4px}
.edit-body{padding:24px}
.ftwrap{margin-bottom:20px}
.ftwrap label{display:block;font-size:12px;font-weight:600;color:#374151;
              text-transform:uppercase;letter-spacing:.4px;margin-bottom:6px}
.fi{width:100%;padding:7px 10px;border:1.5px solid #e5e7eb;border-radius:6px;
    font-size:13px;outline:none;transition:border-color .2s;background:#fff}
.fi:focus{border-color:#1a7a45;background:#f0fdf4}
.fi.num{text-align:right}
.lotes-table{width:100%;border-collapse:separate;border-spacing:0}
.lotes-table thead th{background:#f8fafc;color:#374151;font-size:12px;font-weight:600;
  text-transform:uppercase;letter-spacing:.5px;padding:10px 12px;text-align:left;
  border-bottom:2px solid #e2e8f0}
.lotes-table tbody td{padding:8px 6px;border-bottom:1px solid #f0f0f0;vertical-align:middle}
.lote-num{width:32px;height:32px;border-radius:50%;background:#dcfce7;color:#15803d;
          font-weight:700;font-size:13px;display:flex;align-items:center;justify-content:center}
.td-num{width:48px;text-align:center}
.actions-bar{display:flex;align-items:center;gap:12px;padding:16px 24px 24px;
             border-top:1px solid #f0f0f0;margin-top:8px}
.btn{padding:10px 24px;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;border:none;transition:all .2s}
.btn-save{background:linear-gradient(135deg,#1a7a45,#0d4f2e);color:#fff}
.btn-save:hover{opacity:.9;transform:translateY(-1px)}
.btn-save:disabled{opacity:.5;cursor:not-allowed;transform:none}
.btn-reset{background:#f3f4f6;color:#374151}
.btn-reset:hover{background:#e5e7eb}
.alert{padding:12px 16px;border-radius:8px;font-size:13px;display:none;margin-bottom:16px}
.alert.show{display:block}
.alert-ok{background:#dcfce7;border:1px solid #86efac;color:#15803d}
.alert-err{background:#fef2f2;border:1px solid #fca5a5;color:#dc2626}

@media(max-width:900px){.dash-cards{grid-template-columns:repeat(2,1fr)}.dash-charts{grid-template-columns:1fr}}
@media(max-width:768px){.container{flex-direction:column;height:auto}.sidebar{width:100%;min-width:unset;max-height:340px;border-right:none;border-bottom:1px solid #e2e8f0}.dash-cards{grid-template-columns:repeat(2,1fr)}}
</style>
</head>
<body>

<nav>
  <div class="nav-title">🏥 Editor de Inventario</div>
  <div class="nav-right">
    <span class="nav-user">
      👤 {{ nombre_usuario }}
      <span class="nav-rol">({{ 'Admin' if es_admin else 'Usuario' }})</span>
    </span>
    {% if es_admin %}<a href="/editor/usuarios" class="nav-btn">👥 Usuarios</a>{% endif %}
    <a href="/editor/salir" class="nav-btn">Salir</a>
  </div>
</nav>

<div class="container">

  <!-- ═══ SIDEBAR ═══ -->
  <aside class="sidebar">
    <div class="sb-header">
      <h2>📦 Seleccionar Producto</h2>
      {% if bodegas|length > 1 %}
      <select id="sel-bodega" onchange="cargarProductos()">
        <option value="">— Elige una bodega —</option>
        {% for key,label in bodegas.items() %}
        <option value="{{ key }}">{{ label }}</option>
        {% endfor %}
      </select>
      {% elif bodegas|length == 1 %}
      <select id="sel-bodega" onchange="cargarProductos()">
        {% for key,label in bodegas.items() %}
        <option value="{{ key }}" selected>{{ label }}</option>
        {% endfor %}
      </select>
      {% else %}
      <div style="font-size:12px;color:#dc2626;padding:6px 0;">Sin bodega asignada. Contacta al administrador.</div>
      <select id="sel-bodega" style="display:none"></select>
      {% endif %}
      <div class="search-wrap">
        <span class="search-icon">🔍</span>
        <input class="search-input" id="inp-buscar" type="text"
               placeholder="Buscar producto…" oninput="filtrarLista()" disabled>
      </div>
    </div>
    <div class="product-list" id="product-list">
      <div class="list-empty">Selecciona una bodega para comenzar.</div>
    </div>
  </aside>

  <!-- ═══ MAIN PANEL ═══ -->
  <main class="main-panel">

    <!-- ── DASHBOARD (default) ── -->
    <div id="dash-view" class="dash-scroll">
      <div id="dash-loading" style="display:flex;align-items:center;justify-content:center;height:200px;color:#6b7280;font-size:14px;">
        ⏳ Cargando estadísticas…
      </div>
      <div id="dash-content" style="display:none">

        <div class="dash-topbar">
          <div>
            <h2>📊 Panel de Control — Inventario</h2>
            <p id="dash-sub">Estado general de todas las bodegas</p>
          </div>
          <button class="btn-refresh" onclick="cargarDashboard()">🔄 Actualizar</button>
        </div>

        <div id="filtro-banner" class="filtro-banner">
          <span id="filtro-label"></span>
          <button onclick="limpiarFiltro()" title="Quitar filtro">✕</button>
        </div>

        <!-- Cards semáforo MED -->
        <div class="dash-cards">
          <div class="dc dc-total">
            <div class="dc-icon">📦</div>
            <div class="dc-num" id="cnt-total">—</div>
            <div class="dc-label">Con MED Disponible</div>
          </div>
          <div class="dc dc-verde clickable" id="card-verde"
               onclick="filtrarPorSemaforo(\'verde\')" title="Clic para filtrar lista">
            <div class="dc-icon">🟢</div>
            <div class="dc-num" id="cnt-verde">—</div>
            <div class="dc-label">Óptimos</div>
            <div class="dc-pct" id="pct-verde" style="font-size:10px;color:#15803d">&gt; 18 meses</div>
          </div>
          <div class="dc dc-amar clickable" id="card-amarillo"
               onclick="filtrarPorSemaforo(\'amarillo\')" title="Clic para filtrar lista">
            <div class="dc-icon">🟡</div>
            <div class="dc-num" id="cnt-amarillo">—</div>
            <div class="dc-label">En Alerta</div>
            <div class="dc-pct" id="pct-amarillo" style="font-size:10px;color:#92400e">13 – 17 meses</div>
          </div>
          <div class="dc dc-rojo clickable" id="card-rojo"
               onclick="filtrarPorSemaforo(\'rojo\')" title="Clic para filtrar lista">
            <div class="dc-icon">🔴</div>
            <div class="dc-num" id="cnt-rojo">—</div>
            <div class="dc-label">Críticos</div>
            <div class="dc-pct" id="pct-rojo" style="font-size:10px;color:#dc2626">1 – 12 meses</div>
          </div>
        </div>

        <!-- Gráficas -->
        <div class="dash-charts">
          <div class="chart-card">
            <h3 id="title-donut">📈 Distribución General</h3>
            <div class="chart-wrap"><canvas id="chart-donut"></canvas></div>
          </div>
          <div class="chart-card">
            <h3 id="title-bar">📊 Estado por Bodega</h3>
            <div class="chart-wrap chart-wrap-bar"><canvas id="chart-bar"></canvas></div>
          </div>
        </div>

        <!-- Tabla por bodega -->
        <div class="bodega-card">
          <div class="section-title">🏪 Resumen por Bodega</div>
          <table class="bt">
            <thead>
              <tr>
                <th>Bodega</th><th>Total</th>
                <th style="color:#15803d">🟢 Óptimos</th>
                <th style="color:#d97706">🟡 En Alerta</th>
                <th style="color:#dc2626">🔴 Críticos</th>
                <th>Distribución</th>
              </tr>
            </thead>
            <tbody id="bodega-tbody"></tbody>
          </table>
          <p class="umbral-note" id="umbral-note"></p>
        </div>

      </div><!-- /dash-content -->
    </div><!-- /dash-view -->

    <!-- ── FORMULARIO EDICIÓN (al seleccionar producto) ── -->
    <div id="edit-area" class="edit-scroll" style="display:none"></div>

  </main>
</div>

<script>
// ══ ESTADO ════════════════════════════════════════════════════════════════════
let todosLosProductos = [];
let bodegaActual   = '';
let codigoActual   = '';
let filtroColor    = null;
let dashData       = null;
let chartDonut     = null;
let chartBar       = null;
let modoBodega     = false;   // true cuando hay una bodega seleccionada
// Umbrales MED — se actualizan desde la API
let MED_VERDE    = 18;
let MED_AMAR_MIN = 13;

const bodegaAuto = '{{ bodega_auto }}';
const esAdmin    = {{ 'true' if es_admin else 'false' }};

// ══ INIT ══════════════════════════════════════════════════════════════════════
window.addEventListener('DOMContentLoaded', () => {
  cargarDashboard();
  if (bodegaAuto) {
    const sel = document.getElementById('sel-bodega');
    if (sel && sel.value) cargarProductos();
  }
});

// ══ DASHBOARD ════════════════════════════════════════════════════════════════
async function cargarDashboard() {
  document.getElementById('dash-loading').style.display = 'flex';
  document.getElementById('dash-content').style.display = 'none';
  try {
    const r = await fetch('/editor/api/dashboard');
    dashData = await r.json();
    if (dashData.error) throw new Error(dashData.error);
    if (dashData.umbrales) {
      MED_VERDE    = dashData.umbrales.verde_min    || 18;
      MED_AMAR_MIN = dashData.umbrales.amarillo_min || 13;
    }
    actualizarCards(dashData.totales);
    renderCharts(dashData);
    renderBodegaTabla(dashData);
    document.getElementById('dash-loading').style.display = 'none';
    document.getElementById('dash-content').style.display = 'block';
    document.getElementById('dash-sub').textContent = esAdmin
      ? 'Estado general de todas las bodegas'
      : (dashData.bodegas ? Object.values(dashData.bodegas)[0]?.label || '' : '');
  } catch(e) {
    document.getElementById('dash-loading').innerHTML =
      `<span style="color:#dc2626">⚠️ Error: ${e.message}</span>`;
  }
}

function actualizarCards(t) {
  const pct = n => t.total > 0 ? Math.round(n * 100 / t.total) + '%' : '—';
  document.getElementById('cnt-total').textContent    = t.total;
  document.getElementById('cnt-verde').textContent    = t.verde;
  document.getElementById('cnt-amarillo').textContent = t.amarillo;
  document.getElementById('cnt-rojo').textContent     = t.rojo;
  document.getElementById('pct-verde').textContent    = pct(t.verde);
  document.getElementById('pct-amarillo').textContent = pct(t.amarillo);
  document.getElementById('pct-rojo').textContent     = pct(t.rojo);
}

// ── Gráficas modo GLOBAL (todas las bodegas) ──────────────────────────────────
function renderCharts(data) {
  modoBodega = false;
  const bods   = data.bodegas;
  const labels = Object.values(bods).map(b => b.label);
  const verts  = Object.values(bods).map(b => b.verde);
  const amars  = Object.values(bods).map(b => b.amarillo);
  const rojos  = Object.values(bods).map(b => b.rojo);
  const t      = data.totales;

  document.getElementById('title-donut').textContent = '📈 Distribución General';
  document.getElementById('title-bar').textContent   = '📊 Estado por Bodega';

  _buildDonut(t.verde, t.amarillo, t.rojo);
  _buildBar(labels, verts, amars, rojos);
}

// ── Gráficas modo BODEGA (una sola bodega seleccionada) ───────────────────────
function renderChartsConBodega(bodega, productos) {
  modoBodega = true;
  // Calcular totales MED de la bodega
  let v = 0, a = 0, r = 0;
  productos.forEach(p => {
    const c = colorP(p);
    if (c === 'verde')    v++;
    else if (c === 'amarillo') a++;
    else if (c === 'rojo')     r++;
  });

  // Calcular desglose por Tipo de Insumo
  const tiposMap = {};
  productos.forEach(p => {
    const c = colorP(p);
    if (c === 'sin_saldo') return;          // excluir sin saldo
    const tipo = p.tipo || 'Sin Tipo';
    if (!tiposMap[tipo]) tiposMap[tipo] = { verde: 0, amarillo: 0, rojo: 0 };
    tiposMap[tipo][c]++;
  });

  const tiposOrden = Object.keys(tiposMap).sort();
  const tVerts = tiposOrden.map(t => tiposMap[t].verde);
  const tAmars = tiposOrden.map(t => tiposMap[t].amarillo);
  const tRojos = tiposOrden.map(t => tiposMap[t].rojo);

  const bodLabel = dashData?.bodegas?.[bodega]?.label || bodega;
  document.getElementById('title-donut').textContent = `📈 ${bodLabel}`;
  document.getElementById('title-bar').textContent   = '📊 Resumen por Tipo de Insumo';

  _buildDonut(v, a, r);
  // Ajustar altura de la barra según nº de tipos
  const barHeight = Math.max(160, tiposOrden.length * 52 + 60);
  document.querySelector('.chart-wrap-bar').style.height = barHeight + 'px';
  _buildBar(tiposOrden, tVerts, tAmars, tRojos);
}

// ── Constructores internos ────────────────────────────────────────────────────
function _buildDonut(v, a, r) {
  if (chartDonut) { chartDonut.destroy(); chartDonut = null; }
  chartDonut = new Chart(document.getElementById('chart-donut'), {
    type: 'doughnut',
    data: {
      labels: ['Óptimos (>18m)', 'En Alerta (13-17m)', 'Críticos (1-12m)'],
      datasets: [{ data: [v, a, r],
                   backgroundColor: ['#22c55e','#f59e0b','#ef4444'],
                   borderWidth: 3, borderColor: '#fff', hoverOffset: 6 }]
    },
    options: {
      responsive: true, maintainAspectRatio: false, cutout: '62%',
      plugins: {
        legend: { position: 'bottom', labels: { font: { size: 11 }, padding: 14 } },
        tooltip: { callbacks: { label: ctx => {
          const s = ctx.dataset.data.reduce((a,b)=>a+b,0);
          return ` ${ctx.label}: ${ctx.parsed} (${s>0?Math.round(ctx.parsed*100/s):0}%)`;
        }}}
      }
    }
  });
}

function _buildBar(labels, verts, amars, rojos) {
  if (chartBar) { chartBar.destroy(); chartBar = null; }
  chartBar = new Chart(document.getElementById('chart-bar'), {
    type: 'bar',
    data: {
      labels,
      datasets: [
        { label: 'Óptimos',   data: verts, backgroundColor: '#22c55e' },
        { label: 'En Alerta', data: amars, backgroundColor: '#f59e0b' },
        { label: 'Críticos',  data: rojos, backgroundColor: '#ef4444' },
      ]
    },
    options: {
      indexAxis: 'y', responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: 'bottom', labels: { font:{size:11}, padding:12 } },
                 tooltip: { mode: 'index' } },
      scales: {
        x: { stacked: true, grid: { color: '#f5f5f5' }, ticks: { font:{size:11} } },
        y: { stacked: true, ticks: { font:{size:11} } }
      }
    }
  });
}

function renderBodegaTabla(data) {
  const tbody = document.getElementById('bodega-tbody');
  tbody.innerHTML = Object.entries(data.bodegas).map(([,b]) => {
    const tot = b.total || 1;
    const wv  = Math.round(b.verde    * 100 / tot);
    const wa  = Math.round(b.amarillo * 100 / tot);
    const wr  = Math.max(100 - wv - wa, 0);
    return `<tr>
      <td><strong>${esc(b.label)}</strong></td>
      <td>${b.total}</td>
      <td style="color:#15803d;font-weight:700">${b.verde}</td>
      <td style="color:#d97706;font-weight:700">${b.amarillo}</td>
      <td style="color:#dc2626;font-weight:700">${b.rojo}</td>
      <td><div class="semabar" title="${wv}% / ${wa}% / ${wr}%">
        <div class="s-v" style="width:${wv}%"></div>
        <div class="s-a" style="width:${wa}%"></div>
        <div class="s-r" style="width:${wr}%"></div>
      </div></td>
    </tr>`;
  }).join('');
  const u = data.umbrales || {};
  document.getElementById('umbral-note').textContent =
    `🟢 Óptimo: MED > ${u.verde_min||18} meses  |  🟡 En Alerta: ${u.amarillo_min||13}–${u.verde_min||18} meses  |  🔴 Crítico: 1–${(u.amarillo_min||13)-1} meses`;
}

function actualizarEstadisticasLocales(productos) {
  let v=0, a=0, r=0, conMed=0;
  productos.forEach(p => {
    if (!p.tiene_saldo || p.med_valor === 0) return;  // excluir sin saldo
    conMed++;
    const c = colorP(p);
    if (c==='verde') v++; else if (c==='amarillo') a++; else r++;
  });
  actualizarCards({ total: conMed, verde: v, amarillo: a, rojo: r });
  const bodLabel = bodegaActual && dashData?.bodegas?.[bodegaActual]?.label
    ? dashData.bodegas[bodegaActual].label : bodegaActual;
  document.getElementById('dash-sub').textContent =
    `Bodega: ${bodLabel}  —  ${conMed} insumos con MED`;
  // Actualizar gráficas para la bodega seleccionada
  renderChartsConBodega(bodegaActual, productos);
  // Actualizar tabla de resumen para mostrar solo esta bodega
  if (dashData?.bodegas?.[bodegaActual]) {
    renderBodegaTabla({ bodegas: { [bodegaActual]: dashData.bodegas[bodegaActual] },
                        umbrales: dashData.umbrales });
  }
}

// ══ SEMÁFORO — basado en MED (Meses de Existencia Disponible) ════════════════
function colorP(p) {
  if (!p.tiene_saldo || p.med_valor === 0) return 'sin_saldo';
  if (p.med_valor > MED_VERDE)    return 'verde';     // > 18 meses
  if (p.med_valor >= MED_AMAR_MIN) return 'amarillo';  // 13-17 meses
  return 'rojo';                                        // 1-12 meses
}

function filtrarPorSemaforo(color) {
  filtroColor = filtroColor === color ? null : color;
  ['verde','amarillo','rojo'].forEach(c =>
    document.getElementById(`card-${c}`).classList.toggle('active-filter', c === filtroColor));
  const banner = document.getElementById('filtro-banner');
  if (filtroColor) {
    banner.style.display = 'flex';
    document.getElementById('filtro-label').textContent = {
      verde:    `🟢 Filtrando: Óptimos — MED > ${MED_VERDE} meses`,
      amarillo: `🟡 Filtrando: En Alerta — MED ${MED_AMAR_MIN}–${MED_VERDE} meses`,
      rojo:     `🔴 Filtrando: Críticos — MED 1–${MED_AMAR_MIN-1} meses`,
    }[filtroColor];
    // Abrir el grupo del color filtrado
    document.querySelectorAll(`details.tg-${filtroColor}`).forEach(d => d.open = true);
  } else {
    banner.style.display = 'none';
  }
  filtrarLista();
}

function limpiarFiltro() {
  filtroColor = null;
  ['verde','amarillo','rojo'].forEach(c =>
    document.getElementById(`card-${c}`).classList.remove('active-filter'));
  document.getElementById('filtro-banner').style.display = 'none';
  filtrarLista();
}

// ══ LISTA DE PRODUCTOS ════════════════════════════════════════════════════════
async function cargarProductos() {
  const bodega = document.getElementById('sel-bodega').value;
  const lista  = document.getElementById('product-list');
  const buscar = document.getElementById('inp-buscar');

  if (!bodega) {
    todosLosProductos = [];
    bodegaActual = '';
    lista.innerHTML = '<div class="list-empty">Selecciona una bodega para comenzar.</div>';
    buscar.disabled = true; buscar.value = '';
    if (dashData) {
      actualizarCards(dashData.totales);
      renderCharts(dashData);          // restaurar gráficas globales
      renderBodegaTabla(dashData);     // restaurar tabla completa
      // restaurar altura normal de la barra
      document.querySelector('.chart-wrap-bar').style.height = '200px';
      document.getElementById('dash-sub').textContent = esAdmin
        ? 'Estado general de todas las bodegas'
        : (Object.values(dashData.bodegas)[0]?.label || '');
    }
    return;
  }
  bodegaActual = bodega;
  lista.innerHTML = '<div class="list-loading">⏳ Cargando productos…</div>';
  buscar.disabled = true;
  try {
    const r = await fetch(`/editor/api/productos?bodega=${encodeURIComponent(bodega)}`);
    const data = await r.json();
    if (data.error) throw new Error(data.error);
    todosLosProductos = data;
    buscar.disabled = false; buscar.value = '';
    filtrarLista();
    actualizarEstadisticasLocales(data);
  } catch(e) {
    lista.innerHTML = `<div class="list-empty">⚠️ Error: ${e.message}</div>`;
  }
}

function filtrarLista() {
  const q = document.getElementById('inp-buscar').value.toLowerCase().trim();
  let f = todosLosProductos;
  if (q) f = f.filter(p => p.nombre.toLowerCase().includes(q) || p.codigo.toLowerCase().includes(q));
  // Al filtrar por semáforo solo se muestran productos CON MED (con saldo)
  if (filtroColor) f = f.filter(p => colorP(p) === filtroColor);
  renderLista(f);
}

const COLORS = { verde:'#22c55e', amarillo:'#f59e0b', rojo:'#ef4444', sin_saldo:'#d1d5db' };
function dot(p) {
  return `<span class="dot" style="background:${COLORS[colorP(p)]}"></span>`;
}

function medTag(p) {
  if (!p.tiene_saldo || p.med_valor === 0) return '';
  const c = colorP(p);
  const bg = { verde:'#dcfce7', amarillo:'#fef9c3', rojo:'#fee2e2' }[c];
  const fg = { verde:'#15803d', amarillo:'#92400e', rojo:'#dc2626' }[c];
  return `<span style="margin-left:6px;background:${bg};color:${fg};border-radius:4px;
                        padding:1px 5px;font-size:10px;font-weight:700;">
            MED ${p.med_valor}m</span>`;
}

function renderLista(productos) {
  const lista = document.getElementById('product-list');
  if (!productos.length) { lista.innerHTML = '<div class="list-empty">Sin resultados.</div>'; return; }

  const verdes   = productos.filter(p => colorP(p) === 'verde');
  const amarillos= productos.filter(p => colorP(p) === 'amarillo');
  const rojos    = productos.filter(p => colorP(p) === 'rojo');
  const sinS     = productos.filter(p => colorP(p) === 'sin_saldo');

  const items = arr => arr.map(p => `
    <div class="pi ${p.codigo===codigoActual?'active':''}"
         data-nombre="${esc(p.nombre)}" data-codigo="${esc(p.codigo)}"
         onclick="seleccionarProducto(this.dataset.nombre,this.dataset.codigo,this)">
      <div class="pi-name">${dot(p)}${esc(p.nombre)}${medTag(p)}</div>
      <div class="pi-code">Cód: ${esc(p.codigo)} | Saldo: ${p.saldo_total}</div>
    </div>`).join('');

  let html = '';
  // Si hay filtro activo sólo se muestra el grupo correspondiente abierto
  const soloColor = filtroColor;
  if (verdes.length && (!soloColor || soloColor==='verde'))
    html += `<details class="tg tg-verde" ${soloColor==='verde'?'open':''}>
      <summary><span class="ta">▶</span> 🟢 Óptimos <span class="tc">${verdes.length}</span></summary>
      ${items(verdes)}</details>`;
  if (amarillos.length && (!soloColor || soloColor==='amarillo'))
    html += `<details class="tg tg-amarillo" ${soloColor==='amarillo'?'open':''}>
      <summary><span class="ta">▶</span> 🟡 En Alerta <span class="tc">${amarillos.length}</span></summary>
      ${items(amarillos)}</details>`;
  if (rojos.length && (!soloColor || soloColor==='rojo'))
    html += `<details class="tg tg-rojo" ${soloColor==='rojo'?'open':''}>
      <summary><span class="ta">▶</span> 🔴 Críticos <span class="tc">${rojos.length}</span></summary>
      ${items(rojos)}</details>`;
  if (sinS.length && !soloColor)
    html += `<details class="tg tg-ss">
      <summary style="color:#6b7280"><span class="ta">▶</span> ⚫ Sin Saldo <span class="tc">${sinS.length}</span></summary>
      ${items(sinS)}</details>`;
  if (!html) html = '<div class="list-empty">Sin resultados.</div>';
  lista.innerHTML = html;
}

// ══ SELECCIÓN → FORMULARIO ════════════════════════════════════════════════════
async function seleccionarProducto(nombre, codigo, el) {
  codigoActual = codigo;
  document.querySelectorAll('.pi').forEach(i => i.classList.remove('active'));
  el.classList.add('active');

  document.getElementById('dash-view').style.display = 'none';
  const area = document.getElementById('edit-area');
  area.style.display = 'block';
  area.innerHTML = `
    <div class="back-bar">
      <button class="btn-back" onclick="volverDashboard()">← Volver al Dashboard</button>
    </div>
    <div class="list-loading" style="padding:40px;text-align:center">⏳ Cargando lotes…</div>`;
  try {
    const r = await fetch(`/editor/api/lotes?bodega=${encodeURIComponent(bodegaActual)}&codigo=${encodeURIComponent(codigo)}`);
    const data = await r.json();
    if (data.error) throw new Error(data.error);
    renderFormulario(data);
  } catch(e) {
    area.innerHTML = `
      <div class="back-bar"><button class="btn-back" onclick="volverDashboard()">← Volver al Dashboard</button></div>
      <div class="edit-card"><div class="edit-body" style="color:#dc2626">⚠️ Error: ${e.message}</div></div>`;
  }
}

function volverDashboard() {
  codigoActual = '';
  document.querySelectorAll('.pi').forEach(i => i.classList.remove('active'));
  document.getElementById('edit-area').style.display = 'none';
  document.getElementById('dash-view').style.display = 'block';
}

// ══ FORMULARIO DE EDICIÓN ═════════════════════════════════════════════════════
function renderFormulario(producto) {
  const lotes = producto.lotes || [];
  while (lotes.length < 5) lotes.push({ numero: lotes.length + 1 });

  const filas = lotes.slice(0,5).map((l,i) => `
    <tr>
      <td class="td-num"><div class="lote-num">${i+1}</div></td>
      <td><input class="fi" id="fv_${i}" type="text" placeholder="dd/mm/aaaa" value="${esc(l.fv||'')}"></td>
      <td><input class="fi" id="lote_${i}" type="text" placeholder="Cód. lote" value="${esc(l.lote||'')}"></td>
      <td><input class="fi num" id="saldo_${i}" type="number" placeholder="0" min="0" step="0.01" value="${l.saldo!=null?l.saldo:''}"></td>
      <td><input class="fi num" id="puni_${i}" type="number" placeholder="0.00" min="0" step="0.01"
          value="${l.precio_unitario!=null?l.precio_unitario:''}" oninput="calcTotal(${i})"></td>
      <td><input class="fi num" id="ptot_${i}" type="number" placeholder="0.00" min="0" step="0.01"
          value="${l.precio_total_lote!=null?l.precio_total_lote:''}"></td>
    </tr>`).join('');

  document.getElementById('edit-area').innerHTML = `
    <div class="back-bar">
      <button class="btn-back" onclick="volverDashboard()">← Volver al Dashboard</button>
    </div>
    <div class="edit-card">
      <div class="edit-header">
        <h2>✏️ ${esc(producto.nombre||'')}</h2>
        <div class="meta">Código: ${esc(producto.codigo||'—')} &nbsp;|&nbsp; Bodega: <strong>${esc(bodegaActual)}</strong></div>
      </div>
      <div class="edit-body">
        <div class="alert alert-ok"  id="alerta-ok">✅ Datos guardados correctamente en el Excel.</div>
        <div class="alert alert-err" id="alerta-err"></div>
        <div class="ftwrap">
          <label>No. Tarjeta Kardex</label>
          <input class="fi" id="tarjeta_kardex" type="text"
                 placeholder="Número de tarjeta Kardex" value="${esc(producto.tarjeta_kardex||'')}">
        </div>
        <div style="overflow-x:auto">
          <table class="lotes-table">
            <thead><tr>
              <th>Lote #</th><th>Fecha Vencimiento</th><th>Código de Lote</th>
              <th>Saldo (cant.)</th><th>Precio Unitario (Q)</th><th>Precio Total Lote (Q)</th>
            </tr></thead>
            <tbody>${filas}</tbody>
          </table>
        </div>
      </div>
      <div class="actions-bar">
        <button class="btn btn-save" id="btn-guardar" onclick="guardar()">💾 Guardar Cambios</button>
        <button class="btn btn-reset" onclick="recargarProducto()">↩ Recargar</button>
        <span id="saving-msg" style="font-size:13px;color:#6b7280;display:none">Guardando…</span>
      </div>
    </div>`;
}

function calcTotal(i) {
  const u = parseFloat(document.getElementById(`puni_${i}`)?.value) || 0;
  const s = parseFloat(document.getElementById(`saldo_${i}`)?.value) || 0;
  const el = document.getElementById(`ptot_${i}`);
  if (el && u > 0 && s > 0) el.value = (u * s).toFixed(2);
}

function recargarProducto() {
  const el = document.querySelector('.pi.active');
  if (el) seleccionarProducto(el.dataset.nombre, el.dataset.codigo, el);
}

async function guardar() {
  const btn   = document.getElementById('btn-guardar');
  const msg   = document.getElementById('saving-msg');
  const okEl  = document.getElementById('alerta-ok');
  const errEl = document.getElementById('alerta-err');
  okEl.classList.remove('show'); errEl.classList.remove('show');
  const lotes = [];
  for (let i = 0; i < 5; i++) {
    lotes.push({
      fv:                (document.getElementById(`fv_${i}`)?.value    || '').trim(),
      lote:              (document.getElementById(`lote_${i}`)?.value  || '').trim(),
      saldo:              document.getElementById(`saldo_${i}`)?.value || '',
      precio_unitario:    document.getElementById(`puni_${i}`)?.value  || '',
      precio_total_lote:  document.getElementById(`ptot_${i}`)?.value  || '',
    });
  }
  const tarjeta_kardex = (document.getElementById('tarjeta_kardex')?.value || '').trim();
  btn.disabled = true; msg.style.display = 'inline';
  try {
    const r = await fetch('/editor/api/guardar', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({bodega: bodegaActual, codigo: codigoActual, lotes, tarjeta_kardex})
    });
    const data = await r.json();
    if (data.ok) {
      okEl.classList.add('show');
      const savedCod = codigoActual;
      await cargarProductos();
      await cargarDashboard();
      document.querySelectorAll('.pi').forEach(el => {
        if (el.dataset.codigo === savedCod) el.classList.add('active');
      });
    } else {
      errEl.textContent = '⚠️ ' + (data.error || 'Error desconocido');
      errEl.classList.add('show');
    }
  } catch(e) {
    errEl.textContent = '⚠️ Error de conexión: ' + e.message;
    errEl.classList.add('show');
  } finally {
    btn.disabled = false; msg.style.display = 'none';
  }
}

function esc(str) {
  return String(str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
</script>
</body></html>'''


# =============================================================================
# HTML: LISTA DE USUARIOS
# =============================================================================
_EDITOR_USUARIOS_HTML = '''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Gestión de Usuarios</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#f0f4f8;min-height:100vh}
nav{background:linear-gradient(135deg,#0d4f2e,#1a7a45);color:#fff;padding:0 24px;
    display:flex;align-items:center;justify-content:space-between;height:56px;box-shadow:0 2px 8px rgba(0,0,0,.2)}
.nav-title{font-size:18px;font-weight:700}
.nav-right{display:flex;align-items:center;gap:12px;font-size:13px}
.nav-user{background:rgba(255,255,255,.15);border-radius:20px;padding:4px 14px}
a.nb{background:rgba(255,255,255,.2);border:1px solid rgba(255,255,255,.4);color:#fff;
     border-radius:6px;padding:5px 14px;text-decoration:none;font-size:13px;transition:background .2s}
a.nb:hover{background:rgba(255,255,255,.35)}
.body{max-width:1000px;margin:32px auto;padding:0 24px}
.ph{display:flex;align-items:center;justify-content:space-between;margin-bottom:24px}
.ph h1{font-size:22px;color:#0d4f2e;font-weight:700}
a.btn-new{background:linear-gradient(135deg,#1a7a45,#0d4f2e);color:#fff;border:none;
          border-radius:8px;padding:10px 20px;font-size:14px;font-weight:600;
          cursor:pointer;text-decoration:none;transition:opacity .2s}
a.btn-new:hover{opacity:.9}
.alert{padding:12px 16px;border-radius:8px;font-size:13px;margin-bottom:20px}
.alert-ok{background:#dcfce7;border:1px solid #86efac;color:#15803d}
.alert-err{background:#fef2f2;border:1px solid #fca5a5;color:#dc2626}
.card{background:#fff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,.08);overflow:hidden}
table{width:100%;border-collapse:collapse}
thead th{background:#f8fafc;color:#374151;font-size:12px;font-weight:700;text-transform:uppercase;
         letter-spacing:.5px;padding:12px 16px;text-align:left;border-bottom:2px solid #e2e8f0}
tbody tr{transition:background .15s}
tbody tr:hover{background:#f9fafb}
tbody td{padding:12px 16px;border-bottom:1px solid #f0f0f0;font-size:13px;color:#374151;vertical-align:middle}
tbody tr:last-child td{border-bottom:none}
.badge{display:inline-block;border-radius:10px;padding:2px 10px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.3px}
.ba{background:#fef3c7;color:#92400e} .bu{background:#dbeafe;color:#1e40af}
.bact{background:#dcfce7;color:#15803d} .binact{background:#f3f4f6;color:#6b7280}
.actions{display:flex;gap:8px}
.be,.bd{padding:5px 14px;border-radius:6px;font-size:12px;font-weight:600;cursor:pointer;border:none;text-decoration:none;transition:opacity .2s}
.be{background:#dbeafe;color:#1e40af} .be:hover{background:#bfdbfe}
.bd{background:#fee2e2;color:#dc2626} .bd:hover{background:#fecaca}
.empty{padding:32px;text-align:center;color:#9ca3af;font-size:14px}
</style></head>
<body>
<nav>
  <div class="nav-title">👥 Gestión de Usuarios</div>
  <div class="nav-right">
    <span class="nav-user">👤 {{ nombre_usuario }}</span>
    <a href="/editor/dashboard" class="nb">← Dashboard</a>
    <a href="/editor/salir" class="nb">Salir</a>
  </div>
</nav>
<div class="body">
  <div class="ph">
    <h1>Usuarios del Sistema</h1>
    <a href="/editor/usuarios/nuevo" class="btn-new">+ Nuevo Usuario</a>
  </div>
  {% if mensaje %}<div class="alert alert-ok">✅ {{ mensaje }}</div>{% endif %}
  {% if error   %}<div class="alert alert-err">⚠️ {{ error }}</div>{% endif %}
  <div class="card">
    {% if usuarios %}
    <table>
      <thead><tr>
        <th>#</th><th>Usuario</th><th>Nombre Completo</th><th>Email</th>
        <th>Rol</th><th>Bodega Asignada</th><th>Estado</th><th>Acciones</th>
      </tr></thead>
      <tbody>
        {% for u in usuarios %}
        <tr>
          <td style="color:#9ca3af">{{ u.id }}</td>
          <td><strong>{{ u.username }}</strong></td>
          <td>{{ u.nombre_completo or '—' }}</td>
          <td style="color:#6b7280">{{ u.email or '—' }}</td>
          <td><span class="badge {{ 'ba' if u.rol=='Admin' else 'bu' }}">{{ u.rol }}</span></td>
          <td>{% if u.bodega_asignada %}
            {% set ck = u.bodega_asignada.upper().replace('BODEGA_','').lower() %}
            {{ bodegas.get(ck, u.bodega_asignada) }}
          {% else %}—{% endif %}</td>
          <td><span class="badge {{ 'bact' if u.activo else 'binact' }}">{{ 'Activo' if u.activo else 'Inactivo' }}</span></td>
          <td>
            <div class="actions">
              <a href="/editor/usuarios/editar/{{ u.id }}" class="be">✏️ Editar</a>
              <form method="POST" action="/editor/usuarios/eliminar/{{ u.id }}"
                    onsubmit="return confirm('¿Eliminar al usuario {{ u.username }}?')">
                <button type="submit" class="bd">🗑 Eliminar</button>
              </form>
            </div>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    {% else %}<div class="empty">No hay usuarios registrados.</div>{% endif %}
  </div>
</div></body></html>'''


# =============================================================================
# HTML: FORMULARIO CREAR / EDITAR USUARIO
# =============================================================================
_EDITOR_USUARIO_FORM_HTML = '''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{% if accion=='nuevo' %}Nuevo Usuario{% else %}Editar Usuario{% endif %}</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#f0f4f8;min-height:100vh}
nav{background:linear-gradient(135deg,#0d4f2e,#1a7a45);color:#fff;padding:0 24px;
    display:flex;align-items:center;justify-content:space-between;height:56px;box-shadow:0 2px 8px rgba(0,0,0,.2)}
.nav-title{font-size:18px;font-weight:700}
.nav-right{display:flex;align-items:center;gap:12px}
a.nb{background:rgba(255,255,255,.2);border:1px solid rgba(255,255,255,.4);color:#fff;
     border-radius:6px;padding:5px 14px;text-decoration:none;font-size:13px;transition:background .2s}
a.nb:hover{background:rgba(255,255,255,.35)}
.body{max-width:560px;margin:32px auto;padding:0 24px 48px}
.card{background:#fff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,.08);overflow:hidden;margin-top:32px}
.ch{background:linear-gradient(135deg,#0d4f2e,#1a7a45);color:#fff;padding:20px 28px}
.ch h2{font-size:18px;font-weight:700}
.ch p{font-size:12px;opacity:.8;margin-top:4px}
.cb{padding:28px}
.fg{margin-bottom:18px}
label{display:block;font-size:13px;font-weight:600;color:#374151;margin-bottom:6px}
.hint{font-size:11px;color:#9ca3af;font-weight:400;margin-left:6px}
input[type=text],input[type=password],input[type=email],select{
  width:100%;padding:10px 14px;border:1.5px solid #d1d5db;border-radius:8px;
  font-size:14px;outline:none;background:#fff;transition:border-color .2s}
input:focus,select:focus{border-color:#1a7a45}
.cr{display:flex;align-items:center;gap:10px;margin-top:4px}
.cr input[type=checkbox]{width:18px;height:18px;cursor:pointer;accent-color:#1a7a45}
.cr label{margin:0;font-weight:500;cursor:pointer}
hr{border:none;border-top:1px solid #f0f0f0;margin:20px 0}
.ab{display:flex;gap:12px;margin-top:8px}
.btn-save{flex:1;padding:11px;background:linear-gradient(135deg,#1a7a45,#0d4f2e);color:#fff;
          border:none;border-radius:8px;font-size:15px;font-weight:600;cursor:pointer;transition:opacity .2s}
.btn-save:hover{opacity:.9}
a.btn-cancel{padding:11px 20px;background:#f3f4f6;color:#374151;border:none;border-radius:8px;
             font-size:15px;font-weight:600;cursor:pointer;text-decoration:none;display:flex;align-items:center}
a.btn-cancel:hover{background:#e5e7eb}
.err{background:#fef2f2;border:1px solid #fca5a5;color:#dc2626;border-radius:8px;
     padding:10px 14px;font-size:13px;margin-bottom:20px}
</style></head>
<body>
<nav>
  <div class="nav-title">{% if accion=='nuevo' %}➕ Nuevo Usuario{% else %}✏️ Editar Usuario{% endif %}</div>
  <div class="nav-right">
    <a href="/editor/usuarios" class="nb">← Volver</a>
    <a href="/editor/salir" class="nb">Salir</a>
  </div>
</nav>
<div class="body">
  <div class="card">
    <div class="ch">
      <h2>{% if accion=='nuevo' %}Crear nuevo usuario{% else %}Editar: {{ usuario.username }}{% endif %}</h2>
      <p>{% if accion=='nuevo' %}Completa los datos para registrar el usuario{% else %}Modifica los campos que deseas actualizar{% endif %}</p>
    </div>
    <div class="cb">
      {% if error %}<div class="err">⚠️ {{ error }}</div>{% endif %}
      <form method="POST">
        <div class="fg">
          <label>Usuario <span style="color:#dc2626">*</span></label>
          <input type="text" name="username" required
                 value="{{ usuario.username if usuario else '' }}" placeholder="nombre_usuario">
        </div>
        <div class="fg">
          <label>Contraseña{% if accion=='editar' %}<span class="hint">(dejar en blanco para no cambiar)</span>{% else %} <span style="color:#dc2626">*</span>{% endif %}</label>
          <input type="password" name="password"
                 {% if accion=='nuevo' %}required{% endif %}
                 placeholder="{% if accion=='editar' %}••••••• (sin cambios){% else %}Contraseña{% endif %}">
        </div>
        <hr>
        <div class="fg">
          <label>Nombre Completo</label>
          <input type="text" name="nombre_completo"
                 value="{{ usuario.nombre_completo if usuario else '' }}" placeholder="Nombre y apellido">
        </div>
        <div class="fg">
          <label>Correo Electrónico</label>
          <input type="email" name="email"
                 value="{{ usuario.email if usuario else '' }}" placeholder="correo@ejemplo.com">
        </div>
        <hr>
        <div class="fg">
          <label>Rol <span style="color:#dc2626">*</span></label>
          <select name="rol" id="sel-rol" onchange="toggleBodega(this.value)">
            <option value="User"  {% if not usuario or usuario.rol=='User'  %}selected{% endif %}>Usuario</option>
            <option value="Admin" {% if usuario and usuario.rol=='Admin' %}selected{% endif %}>Administrador</option>
          </select>
        </div>
        <div class="fg" id="bodega-row"
             style="{{ 'display:none' if (usuario and usuario.rol=='Admin') else '' }}">
          <label>Bodega Asignada</label>
          <select name="bodega_asignada">
            <option value="">— Sin bodega asignada —</option>
            {% for key,label in bodegas.items() %}
            <option value="{{ key }}"
              {% if usuario and usuario.get('bodega_asignada_clave')==key %}selected{% endif %}>
              {{ label }}
            </option>
            {% endfor %}
          </select>
        </div>
        <div class="fg">
          <label>Estado</label>
          <div class="cr">
            <input type="checkbox" id="activo" name="activo"
                   {% if not usuario or usuario.activo %}checked{% endif %}>
            <label for="activo">Usuario activo (puede iniciar sesión)</label>
          </div>
        </div>
        <div class="ab">
          <a href="/editor/usuarios" class="btn-cancel">Cancelar</a>
          <button type="submit" class="btn-save">
            {% if accion=='nuevo' %}➕ Crear Usuario{% else %}💾 Guardar Cambios{% endif %}
          </button>
        </div>
      </form>
    </div>
  </div>
</div>
<script>
function toggleBodega(rol) {
  document.getElementById('bodega-row').style.display = rol==='Admin' ? 'none' : '';
}
</script>
</body></html>'''

# =============================================================================
# FIN DEL MÓDULO EDITOR
# =============================================================================

if __name__ == '__main__':
    app.run()