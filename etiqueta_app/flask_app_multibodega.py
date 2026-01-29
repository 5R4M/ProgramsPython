from flask import Flask, request
import pandas as pd
from datetime import datetime
import pytz
import os

app = Flask(__name__)

# Configuración de zona horaria
TIMEZONE = pytz.timezone('America/Guatemala')

def obtener_hora_actual():
    """Obtiene la hora actual en zona horaria de Guatemala"""
    return datetime.now(TIMEZONE)

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
        'nombre': 'Mixto',
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
    """Carga datos desde Excel para una bodega específica"""
    try:
        # Si el archivo no existe, retornar diccionario vacío
        if not os.path.exists(archivo_excel):
            print(f"⚠️  Archivo no encontrado: {archivo_excel}")
            return {}, set()
        
        df = pd.read_excel(
            archivo_excel,
            sheet_name="Inventario General",
            header=4
        )
        df = df.dropna(how='all')
        df = df[df['Código'].notna()]
        df = df[df['Saldo'] > 0]
        
        inventario_bodega = {}
        tipos_encontrados = set()
        
        for idx, row in df.iterrows():
            codigo = str(row.get('Código', ''))
            if not codigo or codigo == 'nan':
                continue
            
            lotes = []
            columnas_inicio = [6, 9, 12, 15, 18]
            columnas_med = [22, 23, 24, 25, 26]
            
            for i, col_inicio in enumerate(columnas_inicio, start=1):
                try:
                    fv = row.iloc[col_inicio]
                    lote = row.iloc[col_inicio + 1]
                    saldo = row.iloc[col_inicio + 2]
                    
                    fv_str = str(fv) if pd.notna(fv) and str(fv) != 'nan' else 'S/D'
                    lote_str = str(lote) if pd.notna(lote) and str(lote) != 'nan' else 'S/D'
                    
                    med_valor = 'S/D'
                    
                    try:
                        med_excel = row.iloc[columnas_med[i-1]]
                        
                        if pd.notna(med_excel):
                            try:
                                med_float = float(med_excel)
                                if med_float >= 1000:
                                    med_valor = 'S/D'
                                else:
                                    med_valor = med_float
                            except:
                                med_valor = 'S/D'
                        else:
                            med_valor = 'S/D'
                    except:
                        med_valor = 'S/D'
                    
                    if pd.notna(saldo) and saldo > 0:
                        lotes.append({
                            'numero': i,
                            'fv': fv_str,
                            'lote': lote_str,
                            'saldo': int(saldo) if saldo == int(saldo) else saldo,
                            'med': med_valor
                        })
                except Exception as e:
                    continue
            
            if lotes:
                # Obtener tipo de insumo si la bodega lo tiene
                tipo_insumo = ''
                if BODEGAS[codigo_bodega].get('tiene_tipos', False):
                    tipo_insumo = str(row.get('Tipo de Insumo', '')) if pd.notna(row.get('Tipo de Insumo')) else ''
                    if tipo_insumo and tipo_insumo != 'nan':
                        tipos_encontrados.add(tipo_insumo)
                
                inventario_bodega[codigo] = {
                    'codigo': codigo,
                    'medicamento': str(row.get('Medicamento', '')),
                    'tipo': tipo_insumo,
                    'presentacion': str(row.get('Presentación Primaria', '')) if pd.notna(row.get('Presentación Primaria')) else '',
                    'lotes': lotes,
                    'saldo_total': row.get('Saldo', 0),
                    'bodega': codigo_bodega
                }
        
        print(f"✅ Bodega '{codigo_bodega}': {len(inventario_bodega)} productos con {sum(len(d['lotes']) for d in inventario_bodega.values())} lotes")
        if tipos_encontrados:
            print(f"   Tipos encontrados: {', '.join(sorted(tipos_encontrados))}")
        
        return inventario_bodega, tipos_encontrados
        
    except Exception as e:
        print(f"❌ Error cargando bodega '{codigo_bodega}': {e}")
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

@app.route('/')
def inicio():
    """Página de inicio con selector de bodegas"""
    total_bodegas = len(datos_inventario)
    total_productos = sum(len(inv) for inv in datos_inventario.values())
    total_lotes = sum(sum(len(d['lotes']) for d in inv.values()) for inv in datos_inventario.values())
    
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
            🕐 Actualizado: {obtener_hora_actual().strftime("%d/%m/%Y %H:%M:%S")}
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
            🕐 {obtener_hora_actual().strftime("%d/%m/%Y %H:%M:%S")}
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
    
    html += """
        </div>
        
        <div class="saldo-total">
            📊 Saldo Total: {saldo_total} unidades
        </div>
""".format(saldo_total=datos.get('saldo_total', 0))
    
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
    
    html += """
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
            🕐 Actualizado: {obtener_hora_actual().strftime("%d/%m/%Y %H:%M:%S")}
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

@app.route('/reporte/<color>')
def reporte_por_color(color):
    """Muestra reporte de medicamentos filtrados por color con opción de seleccionar tipo"""
    bodega_param = request.args.get('bodega', '')
    tipo_param = request.args.get('tipo', '')
    
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
    
    # HTML del reporte (mismo código que antes, manteniendo el diseño)
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
            🕐 Actualizado: {obtener_hora_actual().strftime("%d/%m/%Y %H:%M:%S")}
        </div>
    </div>
</body>
</html>
"""
    return html

def mostrar_selector_tipo(color, bodega_param, codigo_bodega):
    """Muestra una página de selección de tipo de insumo dinámica según la bodega"""
    
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
            🕐 {obtener_hora_actual().strftime("%d/%m/%Y %H:%M:%S")}
        </div>
    </div>
</body>
</html>
"""
    return html

if __name__ == '__main__':
    app.run()