from flask import Flask, request, jsonify
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
    """
    ✅ Lee datos directamente del Excel (sin SQLite)
    """
    try:
        if not os.path.exists(archivo_excel):
            print(f"⚠️  Archivo no encontrado: {archivo_excel}")
            return {}, set()

        df = pd.read_excel(archivo_excel, sheet_name="Inventario General", header=4)
        filas_iniciales = len(df)

        df = df.dropna(how='all')
        df = df[df['Código'].notna()]

        print(f"📊 Bodega '{codigo_bodega}': {len(df)} productos leídos del Excel")

        # ⚠️ REMOVIDO: No filtrar por saldo_total aquí
        # El filtro se aplica a nivel de LOTE, no de producto completo
        # if len(df.columns) > 29:
        #     df = df[df.iloc[:, 29] > 0]

        inventario_bodega = {}
        tipos_encontrados = set()
        productos_sin_lotes = 0  # Contador de productos sin lotes válidos

        for idx, row in df.iterrows():
            codigo = str(row.get('Código', ''))
            if not codigo or codigo == 'nan':
                continue

            # ✅ Precio desde Excel (columna AB = índice 27)
            precio_unitario_producto = None
            try:
                precio_val = row.iloc[27]
                if pd.notna(precio_val):
                    precio_unitario_producto = float(precio_val)
            except:
                precio_unitario_producto = None

            lotes = []
            # Columnas por lote: (F/V, Lote, Saldo)
            columnas_lotes = [
                (6, 7, 8),      # Lote 1: G, H, I
                (9, 10, 11),    # Lote 2: J, K, L
                (12, 13, 14),   # Lote 3: M, N, O
                (15, 16, 17),   # Lote 4: P, Q, R
                (18, 19, 20)    # Lote 5: S, T, U
            ]

            columnas_med = [22, 23, 24, 25, 26]

            for i, (col_fv, col_lote, col_saldo) in enumerate(columnas_lotes, start=1):
                try:
                    # ✅ Leer DIRECTAMENTE del Excel
                    fv = row.iloc[col_fv]
                    lote = row.iloc[col_lote]
                    saldo = row.iloc[col_saldo]

                    # Convertir a string o 'S/D' si está vacío
                    fv_str = str(fv) if pd.notna(fv) and str(fv) != 'nan' else 'S/D'
                    lote_str = str(lote) if pd.notna(lote) and str(lote) != 'nan' else 'S/D'

                    # Formatear fecha si viene como datetime
                    if isinstance(fv, pd.Timestamp):
                        fv_str = fv.strftime('%d/%m/%Y')

                    # MED (Meses de Existencia)
                    med_valor = 'S/D'
                    try:
                        med_excel = row.iloc[columnas_med[i-1]]
                        if pd.notna(med_excel):
                            try:
                                med_float = float(med_excel)
                                med_valor = 'S/D' if med_float >= 1000 else med_float
                            except:
                                med_valor = 'S/D'
                    except:
                        med_valor = 'S/D'

                    # Solo agregar lotes con saldo > 0
                    if pd.notna(saldo) and saldo > 0:
                        lotes.append({
                            'numero': i,
                            'fv': fv_str,
                            'lote': lote_str,
                            'saldo': int(saldo) if saldo == int(saldo) else saldo,
                            'med': med_valor,
                            'precio_unitario': precio_unitario_producto
                        })
                except Exception as e:
                    print(f"⚠️ Error procesando lote {i} del código {codigo}: {e}")
                    continue

            # ✅ CAMBIO CRÍTICO: Agregar productos INCLUSO SIN LOTES
            # para diagnóstico, pero marcarlo
            tipo_insumo = ''
            if BODEGAS[codigo_bodega].get('tiene_tipos', False):
                tipo_insumo = str(row.get('Tipo de Insumo', '')) if pd.notna(row.get('Tipo de Insumo')) else ''
                if tipo_insumo and tipo_insumo != 'nan':
                    tipos_encontrados.add(tipo_insumo)

            # Saldo total (columna AD = índice 29)
            saldo_total = row.iloc[29] if len(row) > 29 and pd.notna(row.iloc[29]) else 0

            if lotes:
                # Producto con lotes válidos
                inventario_bodega[codigo] = {
                    'codigo': codigo,
                    'medicamento': str(row.get('Medicamento', '')),
                    'tipo': tipo_insumo,
                    'presentacion': str(row.get('Presentación Primaria', '')) if pd.notna(row.get('Presentación Primaria')) else '',
                    'lotes': lotes,
                    'saldo_total': saldo_total,
                    'bodega': codigo_bodega
                }
            else:
                # Producto sin lotes válidos (para diagnóstico)
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
    """Endpoint JSON para la aplicación móvil"""
    codigo = request.args.get('codigo', '')
    bodega_param = request.args.get('bodega', '')

    if not codigo:
        return jsonify({'error': 'Código requerido'}), 400

    # Buscar el medicamento
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

    # ✅ Agregar timestamp para evitar cache
    import time

    # Retornar JSON con timestamp
    return jsonify({
        'codigo': datos['codigo'],
        'medicamento': datos['medicamento'],
        'tipo': datos.get('tipo', ''),
        'presentacion': datos.get('presentacion', ''),
        'saldo_total': datos.get('saldo_total', 0),
        'bodega': bodega_encontrada,
        'bodega_nombre': BODEGAS[bodega_encontrada]['nombre'],
        'lotes': datos['lotes'],
        'timestamp': int(time.time()),  # ✅ Evita cache
        'actualizado': obtener_hora_actual().strftime('%Y-%m-%d %H:%M:%S')
    })

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

            html += f"""
        <div class="lote-section">
            <div class="med-indicator {color}">
                {valor_circulo}
            </div>
            <div class="lote-title">🔹 LOTE {lote['numero']}</div>
            <div class="lote-detail"><strong>F/V:</strong> {lote['fv']}</div>
            <div class="lote-detail"><strong>Lote:</strong> {lote['lote']}</div>
            <div class="lote-detail"><strong>Saldo:</strong> <strong style="color: #4caf50; font-size: 16px;">{lote['saldo']} unidades</strong></div>
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
        # Lote 1: G(7), H(8), I(9)
        # Lote 2: J(10), K(11), L(12)
        # Lote 3: M(13), N(14), O(15)
        # Lote 4: P(16), Q(17), R(18)
        # Lote 5: S(19), T(20), U(21)
        columnas_lotes = {
            1: {'fv': 7, 'lote': 8, 'saldo': 9},
            2: {'fv': 10, 'lote': 11, 'saldo': 12},
            3: {'fv': 13, 'lote': 14, 'saldo': 15},
            4: {'fv': 16, 'lote': 17, 'saldo': 18},
            5: {'fv': 19, 'lote': 20, 'saldo': 21}
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
            # Columna AB = 28
            ws.cell(row=fila_producto, column=28).value = nuevo_precio
            cambios_realizados.append(f"Precio Unitario: Q{nuevo_precio:.2f}")

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
            1: {'fv': 7, 'lote': 8, 'saldo': 9},
            2: {'fv': 10, 'lote': 11, 'saldo': 12},
            3: {'fv': 13, 'lote': 14, 'saldo': 15},
            4: {'fv': 16, 'lote': 17, 'saldo': 18},
            5: {'fv': 19, 'lote': 20, 'saldo': 21}
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
            if 'precio_unitario' in lote_data and not precio_actualizado:
                ws.cell(row=fila_producto, column=28).value = float(lote_data['precio_unitario'])
                todos_cambios.append(f"Precio Unitario: Q{lote_data['precio_unitario']:.2f}")
                precio_actualizado = True

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
                        'codigo': codigo,
                        'medicamento': datos['medicamento'],
                        'bodega': nombre_bodega,
                        'tipo': datos.get('tipo', ''),
                        'lote_numero': lote['numero'],
                        'fv': lote['fv'],
                        'lote': lote['lote'],
                        'saldo': lote['saldo'],
                        'med': lote.get('med'),
                        'med_texto': texto_med
                    })

    # Ordenar por bodega y medicamento
    medicamentos_filtrados.sort(key=lambda x: (x['bodega'], x['medicamento']))

    # Configuración según el color
    if color == 'rojo':
        color_hex = '#ff6b6b'
        titulo = 'INSUMOS CRÍTICOS'
        subtitulo = 'Existencia: 1-12 meses'
        icono = '🔴'
        descripcion = 'Estos insumos requieren reabastecimiento URGENTE'
        bg_gradient = 'linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)'
    elif color == 'amarillo':
        color_hex = '#ffd93d'
        titulo = 'INSUMOS EN ALERTA'
        subtitulo = 'Existencia: 13-17 meses'
        icono = '🟡'
        descripcion = 'Estos insumos requieren monitoreo constante'
        bg_gradient = 'linear-gradient(135deg, #ffd93d 0%, #f6b93b 100%)'
    else:  # verde
        color_hex = '#51cf66'
        titulo = 'INSUMOS ÓPTIMOS'
        subtitulo = 'Existencia: 18+ meses o S/D'
        icono = '🟢'
        descripcion = 'Estos insumos tienen stock suficiente'
        bg_gradient = 'linear-gradient(135deg, #51cf66 0%, #37b24d 100%)'

    # Añadir info de tipo si está filtrado
    if tipo_param and tipo_param != 'TODOS' and tipo_param in TIPOS_INSUMO:
        tipo_info = TIPOS_INSUMO[tipo_param]
        titulo += f" - {tipo_info['nombre']}"
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
        .stat-item {{
            text-align: center;
        }}
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
        .med-icono {{
            font-size: 28px;
        }}
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
        .bodega-icon {{
            font-size: 16px;
        }}
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
        .detalle-item {{
            font-size: 12px;
        }}
        .detalle-label {{
            font-weight: bold;
            color: #666;
            display: block;
        }}
        .detalle-valor {{
            color: #333;
            margin-top: 2px;
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

if __name__ == '__main__':
    app.run()