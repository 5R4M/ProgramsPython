"""
GENERADOR DE QR MULTI-BODEGA
Genera QR para múltiples bodegas (Medicamentos, Material Médico, Limpieza, etc.)
"""

import pandas as pd
import qrcode
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import json
import os

# =====================================================
# CONFIGURACIÓN
# =====================================================

ARCHIVO_CONFIG = "config_generador_qr_multibodega.json"

# Definición de bodegas
BODEGAS = {
    '1': {
        'nombre': 'Material Médico Quirúrgico e Insumos de Laboratorio',
        'codigo': 'medico',
        'hoja_excel': 'Inventario General',
        'header_row': 4
    },
    '2': {
        'nombre': 'Medicamentos',
        'codigo': 'medicamentos',
        'hoja_excel': 'Inventario General',
        'header_row': 4
    },
    '3': {
        'nombre': 'Limpieza',
        'codigo': 'limpieza',
        'hoja_excel': 'Inventario General',
        'header_row': 4
    },
    '4': {
        'nombre': 'Oficina',
        'codigo': 'oficina',
        'hoja_excel': 'Inventario General',
        'header_row': 4
    },
    '5': {
        'nombre': 'Varios',
        'codigo': 'varios',
        'hoja_excel': 'Inventario General',
        'header_row': 4
    },
    '6': {
        'nombre': 'Programas',
        'codigo': 'programas',
        'hoja_excel': 'Inventario General',
        'header_row': 4
    }
}

def cargar_configuracion():
    """Carga la configuración guardada"""
    try:
        if os.path.exists(ARCHIVO_CONFIG):
            with open(ARCHIVO_CONFIG, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print("\n✅ Configuración encontrada")
                print(f"   Usuario: {config.get('usuario', 'No guardado')}")
                return config
        return None
    except Exception as e:
        print(f"⚠️ Error al cargar configuración: {e}")
        return None

def guardar_configuracion(config):
    """Guarda la configuración"""
    try:
        with open(ARCHIVO_CONFIG, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print("\n💾 Configuración guardada")
        return True
    except Exception as e:
        print(f"⚠️ Error al guardar configuración: {e}")
        return False

def configurar():
    """Configuración inicial"""
    print("\n" + "="*70)
    print("⚙️  CONFIGURACIÓN DEL GENERADOR MULTI-BODEGA")
    print("="*70)
    
    # Usuario
    print("\n1. Usuario de PythonAnywhere:")
    usuario = input("   Ingresa tu usuario: ").strip()
    
    if not usuario:
        print("❌ Usuario requerido")
        return None
    
    print(f"   ✅ Usuario: {usuario}")
    print(f"   ✅ URL: https://{usuario}.pythonanywhere.com")
    
    config = {
        'usuario': usuario,
        'bodegas': {}
    }
    
    if guardar_configuracion(config):
        print("\n✅ Configuración completada")
        return config
    
    return None

def seleccionar_bodega():
    """Permite seleccionar una bodega"""
    print("\n" + "="*70)
    print("📦 SELECCIONA LA BODEGA")
    print("="*70)
    
    print("\nBodegas disponibles:")
    for key, bodega in BODEGAS.items():
        print(f"   {key}. {bodega['nombre']}")
    
    print("\n   0. Salir")
    
    opcion = input("\nSelecciona una bodega (0-6): ").strip()
    
    if opcion == '0':
        return None
    
    if opcion not in BODEGAS:
        print("❌ Opción inválida")
        return None
    
    return BODEGAS[opcion]

def seleccionar_excel_bodega(bodega):
    """Selecciona el archivo Excel para una bodega específica"""
    print(f"\n📂 Selecciona el archivo Excel para: {bodega['nombre']}")
    print("   (Puedes arrastrar el archivo a esta ventana)")
    ruta = input("   Ruta: ").strip()
    
    # Limpiar comillas
    ruta = ruta.strip('"').strip("'")
    
    if not os.path.exists(ruta):
        print(f"❌ Archivo no encontrado: {ruta}")
        return None
    
    print(f"✅ Excel seleccionado: {Path(ruta).name}")
    return ruta

def generar_qr_bodega(config, bodega, ruta_excel):
    """Genera QR para una bodega específica"""
    
    usuario = config['usuario']
    codigo_bodega = bodega['codigo']
    URL_BASE = f"https://{usuario}.pythonanywhere.com/medicamento?codigo="
    
    print("\n" + "="*70)
    print(f"🎯 GENERANDO QR - {bodega['nombre'].upper()}")
    print("="*70)
    print(f"\n📝 Usuario: {usuario}")
    print(f"📦 Bodega: {bodega['nombre']}")
    print(f"🌐 URL Base: {URL_BASE}")
    print(f"📂 Excel: {Path(ruta_excel).name}")
    print("="*70)
    
    # Cargar Excel
    try:
        print("\n📂 Cargando datos del Excel...")
        df = pd.read_excel(
            ruta_excel, 
            sheet_name=bodega['hoja_excel'], 
            header=bodega['header_row']
        )
        df = df.dropna(how='all')
        df = df[df['Código'].notna()]
        df = df[df['Saldo'] > 0]
        print(f"✅ {len(df)} productos con saldo encontrados")
    except Exception as e:
        print(f"\n❌ ERROR al leer Excel: {e}")
        print("\nVerifica que:")
        print(f"  - El archivo tenga la hoja '{bodega['hoja_excel']}'")
        print(f"  - Los datos empiecen en la fila {bodega['header_row'] + 1}")
        return False
    
    if len(df) == 0:
        print("\n⚠️  No se encontraron productos con saldo > 0")
        return False
    
    # Crear carpeta específica para la bodega
    carpeta_salida = f"codigos_qr_{codigo_bodega}"
    Path(carpeta_salida).mkdir(exist_ok=True)
    
    # Generar QR
    print(f"\n🎯 Generando {len(df)} códigos QR...")
    print("="*70)
    
    codigos_generados = []
    
    for idx, (index, row) in enumerate(df.iterrows()):
        codigo = str(row.get('Código', ''))
        producto = str(row.get('Medicamento', ''))  # Puede ser Medicamento, Producto, etc.
        
        # URL completa - agregar parámetro de bodega
        url = f"{URL_BASE}{codigo}&bodega={codigo_bodega}"
        
        # Crear QR
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Guardar
        nombre_archivo = f"QR_{codigo_bodega}_{codigo}.png"
        caracteres_invalidos = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in caracteres_invalidos:
            nombre_archivo = nombre_archivo.replace(char, '-')
        
        ruta_completa = Path(carpeta_salida) / nombre_archivo
        img.save(ruta_completa)
        
        codigos_generados.append({
            'ruta': str(ruta_completa),
            'codigo': codigo,
            'producto': producto,
            'bodega': bodega['nombre']
        })
        
        # Mostrar progreso
        if (idx + 1) % max(1, len(df) // 10) == 0 or idx == 0:
            porcentaje = int((idx + 1) / len(df) * 100)
            print(f"  {porcentaje:3d}% completado ({idx + 1:3d}/{len(df)})")
    
    print("="*70)
    print(f"\n✅ COMPLETADO: {len(df)} códigos QR generados")
    print(f"📁 Ubicación: {Path(carpeta_salida).absolute()}")
    
    # Preguntar si generar PDF
    print("\n¿Deseas generar un PDF con todos los QR? (s/n): ", end='')
    respuesta = input().strip().lower()
    
    if respuesta == 's':
        generar_pdf(codigos_generados, usuario, bodega)
    
    return True

def generar_pdf(codigos_generados, usuario, bodega):
    """Genera PDF con los QR de una bodega - DISEÑO MEJORADO"""
    try:
        pdf_path = f"codigos_qr_{bodega['codigo']}.pdf"
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        
        # Configuración mejorada: 2 columnas x 3 filas
        cols, rows = 2, 3
        qr_size = 1.7 * inch  # QR optimizado
        margin = 0.4 * inch
        spacing_x = (width - 2 * margin) / cols
        spacing_y = (height - 2 * margin) / rows
        
        # Colores
        COLOR_BORDE = (0.2, 0.2, 0.2)  # Gris oscuro
        COLOR_FONDO = (0.98, 0.98, 0.98)  # Gris muy claro
        COLOR_BODEGA = (0, 0.5, 0)  # Verde
        
        contador = 0
        total = len(codigos_generados)
        
        print("\n📄 Generando PDF con diseño mejorado...")
        
        for idx, qr_data in enumerate(codigos_generados):
            if contador >= (cols * rows):
                c.showPage()
                contador = 0
            
            col = contador % cols
            row = contador // cols
            
            # Calcular posición del recuadro
            x_recuadro = margin + col * spacing_x + 10
            y_recuadro = height - margin - (row + 1) * spacing_y + 10
            ancho_recuadro = spacing_x - 20
            alto_recuadro = spacing_y - 20
            
            # Dibujar fondo del recuadro
            c.setFillColorRGB(*COLOR_FONDO)
            c.setStrokeColorRGB(*COLOR_BORDE)
            c.setLineWidth(2)
            c.roundRect(x_recuadro, y_recuadro, ancho_recuadro, alto_recuadro, 8, fill=1, stroke=1)
            
            # Posición del QR (centrado en el recuadro, parte superior)
            x_qr = x_recuadro + (ancho_recuadro - qr_size) / 2
            y_qr = y_recuadro + alto_recuadro - qr_size - 15
            
            # Dibujar QR
            c.drawImage(qr_data['ruta'], x_qr, y_qr, qr_size, qr_size)
            
            # Área de texto debajo del QR
            text_x = x_recuadro + 8
            text_y = y_qr - 10  # Más cerca del QR (antes -15)
            ancho_recuadro - 16
            
            # CÓDIGO (más grande y destacado)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 11)  # Antes: 7, Ahora: 11
            codigo_text = f"CÓDIGO: {qr_data['codigo']}"
            c.drawString(text_x, text_y, codigo_text)
            
            text_y -= 18
            
            # PRODUCTO/MEDICAMENTO (más grande y legible)
            c.setFont("Helvetica", 9)  # Antes: 6, Ahora: 9
            producto = str(qr_data['producto'])
            
            # Dividir texto en múltiples líneas si es muy largo
            max_chars = 45  # Caracteres por línea
            lineas = []
            palabras = producto.split()
            linea_actual = ""
            
            for palabra in palabras:
                if len(linea_actual + " " + palabra) <= max_chars:
                    linea_actual += (" " if linea_actual else "") + palabra
                else:
                    if linea_actual:
                        lineas.append(linea_actual)
                    linea_actual = palabra
            
            if linea_actual:
                lineas.append(linea_actual)
            
            # Limitar a 3 líneas máximo
            lineas = lineas[:3]
            
            # Dibujar cada línea
            for linea in lineas:
                c.drawString(text_x, text_y, linea)
                text_y -= 12
            
            # BODEGA (al final, destacada)
            text_y -= 5
            c.setFont("Helvetica-Bold", 7)
            c.setFillColorRGB(*COLOR_BODEGA)
            
            bodega_text = f"📦 {bodega['nombre']}"  # Nombre completo sin límite
            c.drawString(text_x, text_y, bodega_text)
            
            # URL (muy pequeña, al final)
            text_y -= 10
            c.setFont("Helvetica", 5)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            url_text = f"https://{usuario}.pythonanywhere.com"
            c.drawString(text_x, text_y, url_text)
            
            contador += 1
            
            # Progreso
            if (idx + 1) % 10 == 0 or idx == total - 1:
                porcentaje = int((idx + 1) / total * 100)
                print(f"  {porcentaje:3d}% completado ({idx + 1:3d}/{total})")
        
        c.save()
        
        print(f"\n✅ PDF generado: {pdf_path}")
        print("💡 Diseño mejorado: QR más grandes, texto legible, recuadros profesionales")
        
        # Preguntar si abrir
        print("\n¿Deseas abrir el PDF? (s/n): ", end='')
        respuesta = input().strip().lower()
        
        if respuesta == 's':
            import platform
            import subprocess
            
            try:
                sistema = platform.system()
                if sistema == "Windows":
                    os.startfile(pdf_path)
                elif sistema == "Darwin":
                    subprocess.run(["open", pdf_path])
                else:
                    subprocess.run(["xdg-open", pdf_path])
                print("✅ PDF abierto")
            except Exception as e:
                print(f"⚠️  No se pudo abrir automáticamente: {e}")
        
    except Exception as e:
        print(f"❌ Error generando PDF: {e}")

def main():
    """Función principal"""
    print("="*70)
    print("🏥 GENERADOR DE QR MULTI-BODEGA")
    print("="*70)
    
    try:
        # Cargar o crear configuración
        config = cargar_configuracion()
        
        if not config:
            print("\n⚙️  No hay configuración guardada")
            config = configurar()
            
            if not config:
                print("\n❌ Configuración fallida")
                input("\nPresiona Enter para salir...")
                return
        else:
            print(f"\n✅ Usuario: {config['usuario']}")
            print(f"🌐 URL: https://{config['usuario']}.pythonanywhere.com")
        
        while True:
            # Seleccionar bodega
            bodega = seleccionar_bodega()
            
            if not bodega:
                print("\n👋 Saliendo...")
                break
            
            # Seleccionar Excel
            ruta_excel = seleccionar_excel_bodega(bodega)
            
            if not ruta_excel:
                continue
            
            # Generar QR
            exito = generar_qr_bodega(config, bodega, ruta_excel)
            
            if exito:
                print("\n✅ Generación completada para esta bodega")
            
            # Preguntar si procesar otra bodega
            print("\n¿Deseas generar QR para otra bodega? (s/n): ", end='')
            continuar = input().strip().lower()
            
            if continuar != 's':
                break
        
        print("\n✅ Proceso completado")
    
    except KeyboardInterrupt:
        print("\n\n🛑 Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n👋 Programa finalizado")
        input("\nPresiona Enter para cerrar...")

if __name__ == "__main__":
    main()