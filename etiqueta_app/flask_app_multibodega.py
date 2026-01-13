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
        'archivo': '/home/salonso/mysite/inventario_medico.xlsx'
    },
    'medicamentos': {
        'nombre': 'Medicamentos',
        'archivo': '/home/salonso/mysite/inventario_medicamentos.xlsx'
    },
    'limpieza': {
        'nombre': 'Limpieza',
        'archivo': '/home/salonso/mysite/inventario_limpieza.xlsx'
    },
    'oficina': {
        'nombre': 'Oficina',
        'archivo': '/home/salonso/mysite/inventario_oficina.xlsx'
    },
    'varios': {
        'nombre': 'Varios',
        'archivo': '/home/salonso/mysite/inventario_varios.xlsx'
    },
    'programas': {
        'nombre': 'Programas',
        'archivo': '/home/salonso/mysite/inventario_programas.xlsx'
    }
}

# Variable global para almacenar datos de todas las bodegas
datos_inventario = {}

def cargar_datos_bodega(codigo_bodega, archivo_excel):
    """Carga datos desde Excel para una bodega específica"""
    try:
        # Si el archivo no existe, retornar diccionario vacío
        if not os.path.exists(archivo_excel):
            print(f"⚠️  Archivo no encontrado: {archivo_excel}")
            return {}
        
        df = pd.read_excel(
            archivo_excel,
            sheet_name="Inventario General Enero",
            header=4
        )
        df = df.dropna(how='all')
        df = df[df['Código'].notna()]
        df = df[df['Saldo'] > 0]
        
        inventario_bodega = {}
        
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
                            except:  # noqa: E722
                                med_valor = 'S/D'
                        else:
                            med_valor = 'S/D'
                    except:  # noqa: E722
                        med_valor = 'S/D'
                    
                    if pd.notna(saldo) and saldo > 0:
                        lotes.append({
                            'numero': i,
                            'fv': fv_str,
                            'lote': lote_str,
                            'saldo': int(saldo) if saldo == int(saldo) else saldo,
                            'med': med_valor
                        })
                except Exception:
                    continue
            
            if lotes:
                inventario_bodega[codigo] = {
                    'codigo': codigo,
                    'medicamento': str(row.get('Medicamento', '')),
                    'tipo': str(row.get('Tipo de Insumo', '')) if pd.notna(row.get('Tipo de Insumo')) else '',
                    'presentacion': str(row.get('Presentación Primaria', '')) if pd.notna(row.get('Presentación Primaria')) else '',
                    'lotes': lotes,
                    'saldo_total': row.get('Saldo', 0),
                    'bodega': codigo_bodega
                }
        
        print(f"✅ Bodega '{codigo_bodega}': {len(inventario_bodega)} productos con {sum(len(d['lotes']) for d in inventario_bodega.values())} lotes")
        return inventario_bodega
        
    except Exception as e:
        print(f"❌ Error cargando bodega '{codigo_bodega}': {e}")
        import traceback
        traceback.print_exc()
        return {}

def cargar_datos():
    """Carga datos de todas las bodegas"""
    global datos_inventario
    datos_inventario = {}
    
    print("\n🔄 Cargando datos de todas las bodegas...")
    
    for codigo_bodega, info_bodega in BODEGAS.items():
        inventario = cargar_datos_bodega(codigo_bodega, info_bodega['archivo'])
        if inventario:
            datos_inventario[codigo_bodega] = inventario
    
    total_productos = sum(len(inv) for inv in datos_inventario.values())
    total_lotes = sum(sum(len(d['lotes']) for d in inv.values()) for inv in datos_inventario.values())
    
    print(f"\n✅ Total cargado: {len(datos_inventario)} bodegas, {total_productos} productos, {total_lotes} lotes")
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
    except:  # noqa: E722
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
        
        lista_bodegas += f"""
        <div class="bodega-card">
            <div class="bodega-icon">📦</div>
            <div class="bodega-info">
                <div class="bodega-nombre">{nombre_bodega}</div>
                <div class="bodega-stats">
                    <span>{num_productos} productos</span>
                    <span>•</span>
                    <span>{num_lotes} lotes</span>
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
"""
    
    if datos.get('tipo') and str(datos.get('tipo')) != 'nan' and datos.get('tipo'):
        html += f"""
            <div class="field">
                <div class="field-label">🏥 Tipo</div>
                <div class="field-value">{datos['tipo']}</div>
            </div>
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
                except:  # noqa: E722
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
        html += f"<h2>📦 {nombre_bodega}</h2><ul>"
        
        for i, (codigo, datos) in enumerate(list(inventario.items())[:3]):
            html += f"<li><strong>{codigo}</strong>: {datos['medicamento']} - {len(datos['lotes'])} lotes"
            for lote in datos['lotes']:
                med = lote.get('med')
                color, texto = obtener_color_med(med)
                html += f"<br>&nbsp;&nbsp;Lote {lote['numero']}: {texto} ({color})"
            html += "</li>"
        
        html += "</ul>"
    
    return html

@app.route('/reporte/<color>')
def reporte_por_color(color):
    """Muestra reporte de medicamentos filtrados por color"""
    bodega_param = request.args.get('bodega', '')
    
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
    else:
        bodegas_a_filtrar = datos_inventario
        nombre_filtro = " - Todas las Bodegas"
    
    # Filtrar medicamentos por color
    medicamentos_filtrados = []
    
    for codigo_bodega, inventario in bodegas_a_filtrar.items():
        nombre_bodega = BODEGAS[codigo_bodega]['nombre']
        
        for codigo, datos in inventario.items():
            for lote in datos['lotes']:
                med_color, texto_med = obtener_color_med(lote.get('med'))
                
                if med_color == color_ingles:
                    medicamentos_filtrados.append({
                        'codigo': codigo,
                        'medicamento': datos['medicamento'],
                        'bodega': nombre_bodega,
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
            padding: 25px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 20px;
        }}
        .header h1 {{
            font-size: 24px;
            margin-bottom: 5px;
        }}
        .header .subtitulo {{
            font-size: 14px;
            opacity: 0.95;
            margin-top: 5px;
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
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid {color_hex};
        }}
        .med-header {{
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }}
        .med-icono {{
            font-size: 24px;
            margin-right: 10px;
        }}
        .med-nombre {{
            font-weight: bold;
            color: #333;
            font-size: 15px;
            flex: 1;
        }}
        .med-codigo {{
            background: {color_hex};
            color: white;
            padding: 4px 10px;
            border-radius: 15px;
            font-size: 11px;
            font-weight: bold;
        }}
        .bodega-tag {{
            background: #ff9800;
            color: white;
            padding: 3px 8px;
            border-radius: 10px;
            font-size: 10px;
            margin-left: 8px;
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="med-icono">{icono}</div>
            <h1>{titulo}{nombre_filtro}</h1>
            <div class="subtitulo">{subtitulo}</div>
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
            html += f"""
        <div class="medicamento-card">
            <div class="med-header">
                <span class="med-icono">💊</span>
                <span class="med-nombre">{med['medicamento']}</span>
                <span class="bodega-tag">📦 {med['bodega'][:20]}</span>
                <span class="med-codigo">{med['codigo']}</span>
            </div>
            
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

if __name__ == '__main__':
    app.run()
