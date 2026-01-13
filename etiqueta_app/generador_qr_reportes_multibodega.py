"""
GENERADOR DE QR PARA REPORTES MULTI-BODEGA
Genera QR de reportes (Rojo, Amarillo, Verde) por bodega o combinados
"""

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
    '1': {'nombre': 'Material Médico Quirúrgico e Insumos de Laboratorio', 'codigo': 'medico'},
    '2': {'nombre': 'Medicamentos', 'codigo': 'medicamentos'},
    '3': {'nombre': 'Limpieza', 'codigo': 'limpieza'},
    '4': {'nombre': 'Oficina', 'codigo': 'oficina'},
    '5': {'nombre': 'Varios', 'codigo': 'varios'},
    '6': {'nombre': 'Programas', 'codigo': 'programas'}
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

def solicitar_usuario():
    """Solicita el usuario si no hay configuración"""
    print("\n📝 Ingresa tu usuario de PythonAnywhere:")
    usuario = input("   Usuario: ").strip()
    
    if not usuario:
        print("❌ Usuario requerido")
        return None
    
    print(f"✅ Usuario: {usuario}")
    
    # Guardar
    config = {
        'usuario': usuario
    }
    
    try:
        with open(ARCHIVO_CONFIG, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print("💾 Usuario guardado")
    except:  # noqa: E722
        pass
    
    return usuario

def seleccionar_opcion_generacion():
    """Permite seleccionar qué tipo de reportes generar"""
    print("\n" + "="*70)
    print("📊 TIPO DE REPORTES A GENERAR")
    print("="*70)
    
    print("\n¿Qué deseas generar?")
    print("   1. Reportes GENERALES (todas las bodegas combinadas)")
    print("   2. Reportes POR BODEGA (específicos de cada bodega)")
    print("   3. AMBOS (generales + individuales)")
    print("   0. Cancelar")
    
    opcion = input("\nOpción (0-3): ").strip()
    
    return opcion

def seleccionar_bodega():
    """Permite seleccionar una bodega"""
    print("\n" + "="*70)
    print("📦 SELECCIONA LA BODEGA")
    print("="*70)
    
    print("\nBodegas disponibles:")
    for key, bodega in BODEGAS.items():
        print(f"   {key}. {bodega['nombre']}")
    
    print("\n   0. Volver")
    
    opcion = input("\nSelecciona una bodega (0-6): ").strip()
    
    if opcion == '0':
        return None
    
    if opcion not in BODEGAS:
        print("❌ Opción inválida")
        return None
    
    return BODEGAS[opcion]

def generar_qr_reportes_generales(usuario):
    """Genera QR de reportes generales (todas las bodegas)"""
    
    print("\n" + "="*70)
    print("🎯 GENERANDO QR DE REPORTES GENERALES")
    print("="*70)
    print(f"\n📝 Usuario: {usuario}")
    print("📊 Tipo: Todas las bodegas combinadas")
    print("="*70)
    
    # URLs de los reportes generales
    reportes = [
        {
            'tipo': 'ROJO',
            'url': f"https://{usuario}.pythonanywhere.com/reporte/rojo",
            'color': '#ff6b6b',
            'nombre_archivo': 'QR_REPORTE_GENERAL_CRITICO_ROJO.png',
            'descripcion': 'INSUMOS CRÍTICOS (1-12 MESES)'
        },
        {
            'tipo': 'AMARILLO',
            'url': f"https://{usuario}.pythonanywhere.com/reporte/amarillo",
            'color': '#ffd93d',
            'nombre_archivo': 'QR_REPORTE_GENERAL_ALERTA_AMARILLO.png',
            'descripcion': 'INSUMOS EN ALERTA (13-17 MESES)'
        },
        {
            'tipo': 'VERDE',
            'url': f"https://{usuario}.pythonanywhere.com/reporte/verde",
            'color': '#51cf66',
            'nombre_archivo': 'QR_REPORTE_GENERAL_OPTIMO_VERDE.png',
            'descripcion': 'INSUMOS ÓPTIMOS (18+ MESES)'
        }
    ]
    
    # Crear carpeta
    carpeta_salida = "codigos_qr_reportes_generales"
    Path(carpeta_salida).mkdir(exist_ok=True)
    
    print("\n🎯 Generando 3 códigos QR de reportes generales...")
    
    codigos_generados = []
    
    for reporte in reportes:
        print(f"\n📊 Generando QR: {reporte['tipo']}")
        print(f"   URL: {reporte['url']}")
        
        # Crear QR
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(reporte['url'])
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Guardar
        ruta_completa = Path(carpeta_salida) / reporte['nombre_archivo']
        img.save(ruta_completa)
        
        codigos_generados.append({
            'ruta': str(ruta_completa),
            'tipo': reporte['tipo'],
            'descripcion': reporte['descripcion'],
            'color': reporte['color'],
            'url': reporte['url']
        })
        
        print(f"   ✅ Guardado: {reporte['nombre_archivo']}")
    
    print("\n✅ COMPLETADO: 3 QR de reportes generales")
    print(f"📁 Ubicación: {Path(carpeta_salida).absolute()}")
    
    # Preguntar si generar PDF
    print("\n¿Deseas generar un PDF con los 3 QR? (s/n): ", end='')
    respuesta = input().strip().lower()
    
    if respuesta == 's':
        generar_pdf(codigos_generados, usuario, "Reportes Generales", "codigos_qr_reportes_generales.pdf")
    
    return True

def generar_qr_reportes_bodega(usuario, bodega):
    """Genera QR de reportes para una bodega específica"""
    
    codigo_bodega = bodega['codigo']
    nombre_bodega = bodega['nombre']
    
    print("\n" + "="*70)
    print(f"🎯 GENERANDO QR DE REPORTES - {nombre_bodega.upper()}")
    print("="*70)
    print(f"\n📝 Usuario: {usuario}")
    print(f"📦 Bodega: {nombre_bodega}")
    print("="*70)
    
    # URLs de los reportes por bodega
    reportes = [
        {
            'tipo': 'ROJO',
            'url': f"https://{usuario}.pythonanywhere.com/reporte/rojo?bodega={codigo_bodega}",
            'color': '#ff6b6b',
            'nombre_archivo': f'QR_REPORTE_{codigo_bodega.upper()}_CRITICO_ROJO.png',
            'descripcion': 'INSUMOS CRÍTICOS (1-12 MESES)'
        },
        {
            'tipo': 'AMARILLO',
            'url': f"https://{usuario}.pythonanywhere.com/reporte/amarillo?bodega={codigo_bodega}",
            'color': '#ffd93d',
            'nombre_archivo': f'QR_REPORTE_{codigo_bodega.upper()}_ALERTA_AMARILLO.png',
            'descripcion': 'INSUMOS EN ALERTA (13-17 MESES)'
        },
        {
            'tipo': 'VERDE',
            'url': f"https://{usuario}.pythonanywhere.com/reporte/verde?bodega={codigo_bodega}",
            'color': '#51cf66',
            'nombre_archivo': f'QR_REPORTE_{codigo_bodega.upper()}_OPTIMO_VERDE.png',
            'descripcion': 'INSUMOS ÓPTIMOS (18+ MESES)'
        }
    ]
    
    # Crear carpeta específica para la bodega
    carpeta_salida = f"codigos_qr_reportes_{codigo_bodega}"
    Path(carpeta_salida).mkdir(exist_ok=True)
    
    print(f"\n🎯 Generando 3 códigos QR para {nombre_bodega}...")
    
    codigos_generados = []
    
    for reporte in reportes:
        print(f"\n📊 Generando QR: {reporte['tipo']}")
        print(f"   URL: {reporte['url']}")
        
        # Crear QR
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(reporte['url'])
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Guardar
        ruta_completa = Path(carpeta_salida) / reporte['nombre_archivo']
        img.save(ruta_completa)
        
        codigos_generados.append({
            'ruta': str(ruta_completa),
            'tipo': reporte['tipo'],
            'descripcion': reporte['descripcion'],
            'color': reporte['color'],
            'url': reporte['url'],
            'bodega': nombre_bodega
        })
        
        print(f"   ✅ Guardado: {reporte['nombre_archivo']}")
    
    print(f"\n✅ COMPLETADO: 3 QR para {nombre_bodega}")
    print(f"📁 Ubicación: {Path(carpeta_salida).absolute()}")
    
    # Preguntar si generar PDF
    print("\n¿Deseas generar un PDF con los 3 QR? (s/n): ", end='')
    respuesta = input().strip().lower()
    
    if respuesta == 's':
        pdf_nombre = f"codigos_qr_reportes_{codigo_bodega}.pdf"
        generar_pdf(codigos_generados, usuario, nombre_bodega, pdf_nombre)
    
    return True

def generar_pdf(codigos_generados, usuario, titulo_bodega, pdf_path):
    """Genera PDF con los QR de reportes"""
    try:
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        
        print("\n📄 Generando PDF...")
        
        # Título principal
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width/2, height - 60, "SEMÁFORO DE INVENTARIO")
        
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width/2, height - 85, titulo_bodega)
        
        c.setFont("Helvetica", 12)
        c.drawCentredString(width/2, height - 105, f"https://{usuario}.pythonanywhere.com")
        
        # Línea separadora
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.setLineWidth(2)
        c.line(50, height - 120, width - 50, height - 120)
        
        # Configuración para 3 QR verticalmente
        qr_size = 2.2 * inch
        y_start = height - 180
        spacing = 180
        
        for idx, qr_data in enumerate(codigos_generados):
            y_position = y_start - (idx * spacing)
            
            # Dibujar QR en la izquierda
            x_qr = 60
            c.drawImage(qr_data['ruta'], x_qr, y_position - qr_size, qr_size, qr_size)
            
            # Marco alrededor del QR
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.setLineWidth(1)
            c.rect(x_qr - 5, y_position - qr_size - 5, qr_size + 10, qr_size + 10)
            
            # Información del reporte en la derecha
            x_text = x_qr + qr_size + 40
            y_text = y_position - 20
            
            # Círculo de color
            c.setFillColorRGB(1, 1, 1)
            if qr_data['tipo'] == 'ROJO':
                c.setFillColorRGB(1, 0.42, 0.42)
            elif qr_data['tipo'] == 'AMARILLO':
                c.setFillColorRGB(1, 0.85, 0.24)
            else:  # VERDE
                c.setFillColorRGB(0.32, 0.81, 0.4)
            
            c.circle(x_text - 15, y_text + 5, 12, fill=1)
            
            # Título del reporte
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 20)
            c.drawString(x_text, y_text, f"REPORTE {qr_data['tipo']}")
            
            # Descripción (acortada para que quepa)
            y_text -= 30
            c.setFont("Helvetica-Bold", 12)
            desc_corta = qr_data['descripcion'][:50]
            if len(qr_data['descripcion']) > 50:
                desc_corta += "..."
            c.drawString(x_text, y_text, desc_corta)
            
            # Detalles con viñetas
            c.setFont("Helvetica", 10)
            y_text -= 25
            
            if qr_data['tipo'] == 'ROJO':
                c.drawString(x_text, y_text, "• Productos con 1-12 meses de existencia")
                y_text -= 16
                c.drawString(x_text, y_text, "• Estado: CRÍTICO")
                y_text -= 16
                c.drawString(x_text, y_text, "• Acción: Reabastecimiento urgente")
            elif qr_data['tipo'] == 'AMARILLO':
                c.drawString(x_text, y_text, "• Productos con 13-17 meses de existencia")
                y_text -= 16
                c.drawString(x_text, y_text, "• Estado: ALERTA")
                y_text -= 16
                c.drawString(x_text, y_text, "• Acción: Monitorear inventario")
            else:  # VERDE
                c.drawString(x_text, y_text, "• Productos con 18+ meses o S/D")
                y_text -= 16
                c.drawString(x_text, y_text, "• Estado: ÓPTIMO")
                y_text -= 16
                c.drawString(x_text, y_text, "• Acción: Stock suficiente")
            
            # URL en recuadro
            y_text -= 22
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.setLineWidth(0.5)
            c.rect(x_text - 5, y_text - 15, 280, 18)
            
            c.setFont("Courier", 8)
            c.setFillColorRGB(0.2, 0.2, 0.2)
            url_corta = qr_data['url'].replace('https://', '')
            if len(url_corta) > 40:
                url_corta = url_corta[:37] + "..."
            c.drawString(x_text, y_text - 12, url_corta)
            
            # Instrucción de escaneo
            y_text -= 28
            c.setFont("Helvetica-Oblique", 9)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawString(x_text, y_text, "Escanea el código QR para ver el reporte completo")
            
            # Línea separadora entre reportes
            if idx < len(codigos_generados) - 1:
                c.setStrokeColorRGB(0.9, 0.9, 0.9)
                c.setLineWidth(1)
                y_line = y_position - qr_size - 15
                c.line(50, y_line, width - 50, y_line)
        
        # Pie de página
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 9)
        footer_text = "Los reportes se actualizan automáticamente desde tu archivo Excel"
        c.drawCentredString(width/2, 50, footer_text)
        
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(width/2, 35, "Sistema de Gestión de Inventario Multi-Bodega")
        
        c.save()
        
        print(f"✅ PDF generado: {pdf_path}")
        
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
    print("📊 GENERADOR DE QR PARA REPORTES MULTI-BODEGA")
    print("="*70)
    
    try:
        # Cargar configuración o solicitar usuario
        config = cargar_configuracion()
        
        if config and config.get('usuario'):
            usuario = config['usuario']
            print(f"\n✅ Usuario encontrado: {usuario}")
            print(f"🌐 URL: https://{usuario}.pythonanywhere.com")
        else:
            print("\n⚙️  No hay configuración guardada")
            usuario = solicitar_usuario()
            
            if not usuario:
                print("\n❌ Usuario requerido")
                input("\nPresiona Enter para salir...")
                return
        
        while True:
            # Seleccionar tipo de generación
            opcion = seleccionar_opcion_generacion()
            
            if opcion == '0':
                print("\n👋 Saliendo...")
                break
            elif opcion == '1':
                # Reportes generales
                generar_qr_reportes_generales(usuario)
            elif opcion == '2':
                # Reportes por bodega
                bodega = seleccionar_bodega()
                if bodega:
                    generar_qr_reportes_bodega(usuario, bodega)
            elif opcion == '3':
                # Ambos
                print("\n🎯 Generando reportes generales y por bodega...")
                
                # Generales
                generar_qr_reportes_generales(usuario)
                
                # Por cada bodega
                print("\n" + "="*70)
                print("📦 Ahora genera reportes para cada bodega...")
                print("="*70)
                
                for key, bodega in BODEGAS.items():
                    print(f"\n¿Generar reportes para {bodega['nombre']}? (s/n): ", end='')
                    respuesta = input().strip().lower()
                    
                    if respuesta == 's':
                        generar_qr_reportes_bodega(usuario, bodega)
            else:
                print("\n❌ Opción inválida")
                continue
            
            # Preguntar si continuar
            print("\n¿Deseas generar más reportes? (s/n): ", end='')
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