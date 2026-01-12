"""
GENERADOR DE QR ONLINE - VERSIÓN CONSOLA
Genera QR desde consola sin ventanas emergentes
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

ARCHIVO_CONFIG = "config_generador_qr.json"

def cargar_configuracion():
    """Carga la configuración guardada"""
    try:
        if os.path.exists(ARCHIVO_CONFIG):
            with open(ARCHIVO_CONFIG, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print("\n✅ Configuración encontrada")
                print(f"   Usuario: {config.get('usuario', 'No guardado')}")
                if config.get('ruta_excel'):
                    print(f"   Excel: {Path(config['ruta_excel']).name}")
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
    """Configuración inicial o actualización"""
    print("\n" + "="*70)
    print("⚙️  CONFIGURACIÓN DEL GENERADOR DE QR")
    print("="*70)
    
    # Usuario
    print("\n1. Usuario de PythonAnywhere:")
    usuario = input("   Ingresa tu usuario: ").strip()
    
    if not usuario:
        print("❌ Usuario requerido")
        return None
    
    print(f"   ✅ Usuario: {usuario}")
    print(f"   ✅ URL: https://{usuario}.pythonanywhere.com")
    
    # Ruta del Excel
    print("\n2. Ruta del archivo Excel:")
    print("   (Opcional - puedes dejarlo vacío y seleccionarlo cada vez)")
    print("   Ejemplo: C:\\Users\\TuNombre\\Documents\\FORMATO_INSUMOS_ENERO_2026.xlsx")
    ruta_excel = input("   Ruta: ").strip()
    
    if ruta_excel and not os.path.exists(ruta_excel):
        print(f"   ⚠️  Archivo no encontrado: {ruta_excel}")
        print("   Se guardará pero deberás verificar la ruta")
    elif ruta_excel:
        print(f"   ✅ Excel: {Path(ruta_excel).name}")
    else:
        print("   ℹ️  No se guardó ruta de Excel")
    
    # Opciones de PDF
    print("\n3. ¿Generar PDF automáticamente? (s/n)")
    generar_pdf_auto = input("   Opción: ").strip().lower() == 's'
    
    config = {
        'usuario': usuario,
        'ruta_excel': ruta_excel if ruta_excel else '',
        'url_base': f'https://{usuario}.pythonanywhere.com/medicamento?codigo=',
        'generar_pdf_auto': generar_pdf_auto
    }
    
    if guardar_configuracion(config):
        print("\n✅ Configuración completada")
        return config
    
    return None

def seleccionar_excel(config):
    """Selecciona el archivo Excel a usar"""
    
    # Si hay ruta guardada, preguntar si usarla
    if config.get('ruta_excel') and os.path.exists(config['ruta_excel']):
        print(f"\n📂 Excel guardado: {Path(config['ruta_excel']).name}")
        usar = input("   ¿Usar este archivo? (s/n): ").strip().lower()
        
        if usar == 's':
            return config['ruta_excel']
    
    # Solicitar nueva ruta
    print("\n📂 Ingresa la ruta completa del archivo Excel:")
    print("   (Puedes arrastrar el archivo a esta ventana)")
    ruta = input("   Ruta: ").strip()
    
    # Limpiar comillas si las arrastraron
    ruta = ruta.strip('"').strip("'")
    
    if not os.path.exists(ruta):
        print(f"❌ Archivo no encontrado: {ruta}")
        return None
    
    print(f"✅ Excel seleccionado: {Path(ruta).name}")
    
    # Preguntar si guardar
    guardar = input("\n¿Guardar esta ruta para futuras generaciones? (s/n): ").strip().lower()
    if guardar == 's':
        config['ruta_excel'] = ruta
        guardar_configuracion(config)
    
    return ruta

def generar_qr_online(config, ruta_excel):
    """Genera QR con URLs de internet"""
    
    usuario = config['usuario']
    URL_BASE = config['url_base']
    
    print("\n" + "="*70)
    print("🎯 GENERANDO CÓDIGOS QR")
    print("="*70)
    print(f"\n📝 Usuario: {usuario}")
    print(f"🌐 URL Base: {URL_BASE}")
    print(f"📂 Excel: {Path(ruta_excel).name}")
    print("="*70)
    
    # Cargar Excel
    try:
        print("\n📂 Cargando datos del Excel...")
        df = pd.read_excel(ruta_excel, sheet_name="Inventario General Enero", header=4)
        df = df.dropna(how='all')
        df = df[df['Código'].notna()]
        df = df[df['Saldo'] > 0]
        print(f"✅ {len(df)} medicamentos con saldo encontrados")
    except Exception as e:
        print(f"\n❌ ERROR al leer Excel: {e}")
        print("\nVerifica que:")
        print("  - El archivo esté cerrado (no abierto en Excel)")
        print("  - Tenga la hoja 'Inventario General Enero'")
        print("  - Los datos empiecen en la fila 5")
        return False
    
    if len(df) == 0:
        print("\n⚠️  No se encontraron medicamentos con saldo > 0")
        return False
    
    # Crear carpeta
    carpeta_salida = "codigos_qr"
    Path(carpeta_salida).mkdir(exist_ok=True)
    
    # Generar QR
    print(f"\n🎯 Generando {len(df)} códigos QR...")
    print("="*70)
    
    codigos_generados = []
    
    for idx, (index, row) in enumerate(df.iterrows()):
        codigo = str(row.get('Código', ''))
        medicamento = str(row.get('Medicamento', ''))
        
        # URL completa
        url = f"{URL_BASE}{codigo}"
        
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
        nombre_archivo = f"QR_{codigo}.png"
        caracteres_invalidos = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in caracteres_invalidos:
            nombre_archivo = nombre_archivo.replace(char, '-')
        
        ruta_completa = Path(carpeta_salida) / nombre_archivo
        img.save(ruta_completa)
        
        codigos_generados.append({
            'ruta': str(ruta_completa),
            'codigo': codigo,
            'medicamento': medicamento
        })
        
        # Mostrar progreso cada 10%
        if (idx + 1) % max(1, len(df) // 10) == 0 or idx == 0:
            porcentaje = int((idx + 1) / len(df) * 100)
            print(f"  {porcentaje:3d}% completado ({idx + 1:3d}/{len(df)})")
    
    print("="*70)
    print(f"\n✅ COMPLETADO: {len(df)} códigos QR generados")
    print(f"📁 Ubicación: {Path(carpeta_salida).absolute()}")
    
    # Generar PDF si está configurado
    if config.get('generar_pdf_auto', False):
        print("\n📄 Generando PDF automáticamente...")
        generar_pdf(codigos_generados, usuario)
    else:
        print("\n¿Deseas generar un PDF con todos los QR? (s/n): ", end='')
        respuesta = input().strip().lower()
        if respuesta == 's':
            generar_pdf(codigos_generados, usuario)
    
    # Información final
    print("\n" + "="*70)
    print("🌐 INFORMACIÓN DEL SERVIDOR")
    print("="*70)
    print(f"\n✅ Los QR apuntan a: {URL_BASE}CODIGO")
    print("\n📱 Accesible desde:")
    print("   ✅ Android, iPhone, tablets, computadoras")
    print("   ✅ Cualquier lugar del mundo con internet")
    print("\n💡 PRÓXIMOS PASOS:")
    print("   1. Sube tu Excel: python sincronizador_pythonanywhere.py")
    print(f"   2. Prueba: https://{usuario}.pythonanywhere.com")
    print("="*70 + "\n")
    
    return True

def generar_pdf(codigos_generados, usuario):
    """Genera PDF con los QR"""
    try:
        pdf_path = "codigos_qr.pdf"
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        
        cols, rows = 2, 3
        qr_size = 1.6 * inch
        margin = 0.5 * inch
        spacing_x = (width - 2 * margin) / cols
        spacing_y = (height - 2 * margin) / rows
        
        contador = 0
        total = len(codigos_generados)
        
        print("\n📄 Generando PDF...")
        
        for idx, qr_data in enumerate(codigos_generados):
            if contador >= (cols * rows):
                c.showPage()
                contador = 0
            
            col = contador % cols
            row = contador // cols
            
            x = margin + col * spacing_x + (spacing_x - qr_size) / 2
            y = height - margin - (row + 1) * spacing_y + (spacing_y - qr_size) / 2 + 0.3 * inch
            
            # Dibujar QR
            c.drawImage(qr_data['ruta'], x, y, qr_size, qr_size)
            
            # Información
            text_y = y - 12
            text_x = margin + col * spacing_x + 5
            
            c.setFont("Helvetica-Bold", 7)
            c.drawString(text_x, text_y, f"Cod: {qr_data['codigo']}")
            
            text_y -= 9
            c.setFont("Helvetica", 6)
            medicamento = str(qr_data['medicamento'])[:60]
            c.drawString(text_x, text_y, medicamento)
            
            # Marca online
            text_y -= 9
            c.setFont("Helvetica-Bold", 5)
            c.setFillColorRGB(0, 0.5, 0)
            c.drawString(text_x, text_y, f"✓ ONLINE - {usuario}.pythonanywhere.com")
            c.setFillColorRGB(0, 0, 0)
            
            contador += 1
            
            # Progreso
            if (idx + 1) % 10 == 0 or idx == total - 1:
                porcentaje = int((idx + 1) / total * 100)
                print(f"  {porcentaje:3d}% completado ({idx + 1:3d}/{total})")
        
        c.save()
        
        print(f"\n✅ PDF generado: {pdf_path}")
        
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
    print("🌐 GENERADOR DE CÓDIGOS QR ONLINE")
    print("="*70)
    
    try:
        # Cargar o crear configuración
        config = cargar_configuracion()
        
        if not config:
            print("\n⚙️  No hay configuración guardada")
            print("    Configuremos el generador...")
            config = configurar()
            
            if not config:
                print("\n❌ Configuración fallida")
                input("\nPresiona Enter para salir...")
                return
        else:
            # Mostrar configuración actual
            print(f"\n✅ Usuario: {config['usuario']}")
            print(f"🌐 URL: https://{config['usuario']}.pythonanywhere.com")
            
            # Preguntar si reconfigurar
            print("\n¿Deseas cambiar la configuración? (s/n): ", end='')
            cambiar = input().strip().lower()
            
            if cambiar == 's':
                config = configurar()
                if not config:
                    print("\n❌ Configuración fallida")
                    input("\nPresiona Enter para salir...")
                    return
        
        # Seleccionar Excel
        ruta_excel = seleccionar_excel(config)
        
        if not ruta_excel:
            print("\n❌ No se seleccionó archivo Excel")
            input("\nPresiona Enter para salir...")
            return
        
        # Generar QR
        print("\n" + "="*70)
        exito = generar_qr_online(config, ruta_excel)
        
        if exito:
            print("\n✅ Proceso completado exitosamente")
        else:
            print("\n❌ El proceso no se completó correctamente")
    
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