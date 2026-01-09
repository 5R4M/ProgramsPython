"""
GENERADOR DE QR PARA REPORTES DE INSUMOS POR COLOR
Genera 3 QR especiales: Rojo (Crítico), Amarillo (Alerta), Verde (Óptimo)
"""

import qrcode
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from tkinter import Tk, messagebox
import sys
import time
import json
import os

# =====================================================
# CONFIGURACIÓN
# =====================================================

# Archivo para guardar el usuario
ARCHIVO_USUARIO = "config_usuario_pythonanywhere.json"

# Variable global para manejar la ventana raíz
root = None

def inicializar_tkinter():
    """Inicializa la ventana principal de Tkinter"""
    global root
    if root is None:
        root = Tk()
        root.withdraw()

def cerrar_tkinter():
    """Cierra completamente Tkinter"""
    global root
    if root is not None:
        try:
            root.quit()
            root.destroy()
            root = None
        except:  # noqa: E722
            pass

def cargar_usuario():
    """Carga el usuario guardado desde el archivo JSON"""
    try:
        if os.path.exists(ARCHIVO_USUARIO):
            with open(ARCHIVO_USUARIO, 'r', encoding='utf-8') as f:
                config = json.load(f)
                usuario = config.get('usuario', '')
                if usuario:
                    print(f"\n✅ Usuario encontrado: {usuario}")
                    return usuario
        return None
    except Exception as e:
        print(f"⚠️ Error al cargar usuario: {e}")
        return None

def obtener_usuario():
    """Obtiene el usuario de PythonAnywhere"""
    
    print("="*60)
    print("📊 GENERADOR DE QR PARA REPORTES")
    print("="*60)
    
    # Intentar cargar usuario guardado
    usuario_guardado = cargar_usuario()
    
    if usuario_guardado:
        usar_guardado = messagebox.askyesno(
            "Usuario encontrado",
            f"Se encontró el usuario guardado:\n\n"
            f"Usuario: {usuario_guardado}\n"
            f"URL: https://{usuario_guardado}.pythonanywhere.com\n\n"
            "¿Deseas usar este usuario?"
        )
        
        if usar_guardado:
            print(f"   ✅ Usando usuario guardado: {usuario_guardado}")
            return usuario_guardado
    
    # Si no hay usuario o no quiere usarlo
    messagebox.showinfo(
        "Usuario no encontrado",
        "Por favor, primero genera los códigos QR normales\n"
        "con el generador principal para guardar tu usuario."
    )
    return None

def generar_qr_reportes(usuario):
    """Genera los 3 QR especiales para reportes"""
    
    print("\n" + "="*60)
    print("🎯 GENERANDO CÓDIGOS QR DE REPORTES")
    print("="*60)
    print(f"\n   Usuario: {usuario}")
    print(f"   URL Base: https://{usuario}.pythonanywhere.com")
    print("\n" + "="*60)
    
    # URLs de los reportes
    reportes = [
        {
            'tipo': 'ROJO',
            'url': f"https://{usuario}.pythonanywhere.com/reporte/rojo",
            'color': '#ff6b6b',
            'nombre_archivo': 'QR_REPORTE_CRITICO_ROJO.png',
            'descripcion': 'INSUMOS CRÍTICOS (1-12 MESES)'
        },
        {
            'tipo': 'AMARILLO',
            'url': f"https://{usuario}.pythonanywhere.com/reporte/amarillo",
            'color': '#ffd93d',
            'nombre_archivo': 'QR_REPORTE_ALERTA_AMARILLO.png',
            'descripcion': 'INSUMOS EN ALERTA (13-17 MESES)'
        },
        {
            'tipo': 'VERDE',
            'url': f"https://{usuario}.pythonanywhere.com/reporte/verde",
            'color': '#51cf66',
            'nombre_archivo': 'QR_REPORTE_OPTIMO_VERDE.png',
            'descripcion': 'INSUMOS ÓPTIMOS (18+ MESES)'
        }
    ]
    
    # Crear carpeta
    carpeta_salida = "codigos_qr_reportes"
    Path(carpeta_salida).mkdir(exist_ok=True)
    
    print("\n🎯 Generando 3 códigos QR de reportes...")
    print("="*60)
    
    codigos_generados = []
    
    for reporte in reportes:
        print(f"\n📊 Generando QR: {reporte['tipo']}")
        print(f"   URL: {reporte['url']}")
        print(f"   Descripción: {reporte['descripcion']}")
        
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
            'color': reporte['color']
        })
        
        print(f"   ✅ Guardado: {reporte['nombre_archivo']}")
    
    print("\n" + "="*60)
    print("✅ COMPLETADO: 3 códigos QR de reportes generados")
    print(f"📁 Ubicación: {Path(carpeta_salida).absolute()}")
    
    # Preguntar si generar PDF
    respuesta = messagebox.askyesno(
        "Generar PDF",
        f"✅ 3 códigos QR de reportes generados exitosamente\n\n"
        f"📁 Carpeta: {carpeta_salida}\n\n"
        "¿Deseas generar un PDF con los 3 QR?"
    )
    
    if respuesta:
        generar_pdf(codigos_generados, usuario)
    
    # Mostrar información final
    print("\n" + "="*60)
    print("📊 INFORMACIÓN DE LOS REPORTES")
    print("="*60)
    print("\n✅ QR ROJO - Insumos Críticos:")
    print(f"   URL: https://{usuario}.pythonanywhere.com/reporte/rojo")
    print("   Muestra: Medicamentos con 1-12 meses de existencia")
    
    print("\n✅ QR AMARILLO - Insumos en Alerta:")
    print(f"   URL: https://{usuario}.pythonanywhere.com/reporte/amarillo")
    print("   Muestra: Medicamentos con 13-17 meses de existencia")
    
    print("\n✅ QR VERDE - Insumos Óptimos:")
    print(f"   URL: https://{usuario}.pythonanywhere.com/reporte/verde")
    print("   Muestra: Medicamentos con 18+ meses de existencia")
    
    print("\n💡 IMPORTANTE:")
    print("   Los reportes se generan automáticamente desde tu Excel")
    print("   Actualiza tu Excel y sincroniza para ver cambios")
    print("="*60 + "\n")
    
    messagebox.showinfo(
        "¡Completado!",
        f"✅ 3 códigos QR de reportes generados\n\n"
        f"📁 Ubicación: {carpeta_salida}\n\n"
        f"🔴 ROJO: Insumos críticos (1-12 meses)\n"
        f"🟡 AMARILLO: Insumos en alerta (13-17 meses)\n"
        f"🟢 VERDE: Insumos óptimos (18+ meses)\n\n"
        "💡 Escanea cada QR para ver el reporte correspondiente"
    )
    
    return True

def generar_pdf(codigos_generados, usuario):
    """Genera PDF con los 3 QR de reportes"""
    try:
        pdf_path = "codigos_qr_reportes.pdf"
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        
        print("\n📄 Generando PDF...")
        
        # Título principal
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(width/2, height - 60, "REPORTES DE INVENTARIO")
        
        c.setFont("Helvetica", 14)
        c.drawCentredString(width/2, height - 85, f"Usuario: {usuario}")
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
            
            # Descripción
            y_text -= 30
            c.setFont("Helvetica-Bold", 14)
            c.drawString(x_text, y_text, qr_data['descripcion'])
            
            # Detalles con viñetas
            c.setFont("Helvetica", 11)
            y_text -= 28
            
            if qr_data['tipo'] == 'ROJO':
                c.drawString(x_text, y_text, "• Medicamentos con 1-12 meses de existencia")
                y_text -= 18
                c.drawString(x_text, y_text, "• Estado: CRÍTICO")
                y_text -= 18
                c.drawString(x_text, y_text, "• Acción: Reabastecimiento urgente")
            elif qr_data['tipo'] == 'AMARILLO':
                c.drawString(x_text, y_text, "• Medicamentos con 13-17 meses de existencia")
                y_text -= 18
                c.drawString(x_text, y_text, "• Estado: ALERTA")
                y_text -= 18
                c.drawString(x_text, y_text, "• Acción: Monitorear inventario")
            else:  # VERDE
                c.drawString(x_text, y_text, "• Medicamentos con 18+ meses o S/D")
                y_text -= 18
                c.drawString(x_text, y_text, "• Estado: ÓPTIMO")
                y_text -= 18
                c.drawString(x_text, y_text, "• Acción: Stock suficiente")
            
            # URL en recuadro
            y_text -= 25
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.setLineWidth(0.5)
            c.rect(x_text - 5, y_text - 15, 280, 18)
            
            c.setFont("Courier", 9)
            c.setFillColorRGB(0.2, 0.2, 0.2)
            url = f"{usuario}.pythonanywhere.com/reporte/{qr_data['tipo'].lower()}"
            c.drawString(x_text, y_text - 12, url)
            
            # Instrucción de escaneo
            y_text -= 30
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
        c.drawCentredString(width/2, 35, "Sistema de Gestión de Inventario Médico")
        
        c.save()
        
        print(f"✅ PDF generado: {pdf_path}")
        
        # Preguntar si abrir
        respuesta = messagebox.askyesno(
            "PDF Generado",
            f"✅ PDF generado exitosamente\n\n"
            f"📄 Archivo: {pdf_path}\n\n"
            "¿Deseas abrirlo ahora?"
        )
        
        if respuesta:
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
            except Exception as e:
                print(f"No se pudo abrir el PDF automáticamente: {e}")
        
    except Exception as e:
        print(f"❌ Error generando PDF: {e}")
        messagebox.showerror("Error", f"Error al generar PDF:\n\n{str(e)}")

def main():
    """Función principal"""
    try:
        inicializar_tkinter()
        
        # Mostrar información
        messagebox.showinfo(
            "Generador de QR de Reportes",
            "📊 GENERADOR DE QR PARA REPORTES\n\n"
            "Este programa genera 3 códigos QR especiales:\n\n"
            "🔴 ROJO: Insumos críticos (1-12 meses)\n"
            "🟡 AMARILLO: Insumos en alerta (13-17 meses)\n"
            "🟢 VERDE: Insumos óptimos (18+ meses)\n\n"
            "Cada QR mostrará un listado filtrado\n"
            "con todos los medicamentos de esa categoría."
        )
        
        # Obtener usuario
        usuario = obtener_usuario()
        
        if not usuario:
            print("\n❌ No se pudo obtener el usuario")
            messagebox.showerror(
                "Error",
                "No se encontró usuario guardado.\n\n"
                "Por favor, ejecuta primero el generador\n"
                "de QR normal para configurar tu usuario."
            )
            return
        
        # Generar QR
        exito = generar_qr_reportes(usuario)
        
        if exito:
            print("\n✅ Proceso completado exitosamente")
        else:
            print("\n❌ El proceso no se completó correctamente")
    
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        messagebox.showerror(
            "Error",
            f"Ocurrió un error inesperado:\n\n{str(e)}"
        )
    
    finally:
        print("\n🔄 Cerrando aplicación...")
        cerrar_tkinter()
        time.sleep(0.3)

if __name__ == "__main__":
    main()
    print("👋 Programa finalizado")
    sys.exit(0)