"""
GENERADOR DE QR CON URL ONLINE - VERSIÓN MEJORADA
Genera QR que apuntan a tu servidor en PythonAnywhere
"""

import pandas as pd
import qrcode
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from tkinter import Tk, filedialog, simpledialog, messagebox
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
        root.withdraw()  # Ocultar ventana principal

def cerrar_tkinter():
    """Cierra completamente Tkinter"""
    global root
    if root is not None:
        try:
            root.quit()  # Detener el mainloop
            root.destroy()  # Destruir la ventana
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

def guardar_usuario(usuario):
    """Guarda el usuario en un archivo JSON"""
    try:
        config = {
            'usuario': usuario
        }
        with open(ARCHIVO_USUARIO, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        print(f"\n💾 Usuario guardado: {usuario}")
        return True
    except Exception as e:
        print(f"⚠️ Error al guardar usuario: {e}")
        return False

def borrar_usuario():
    """Elimina el archivo de configuración del usuario"""
    try:
        if os.path.exists(ARCHIVO_USUARIO):
            os.remove(ARCHIVO_USUARIO)
            print("\n🗑️ Usuario eliminado")
            return True
        return False
    except Exception as e:
        print(f"⚠️ Error al borrar usuario: {e}")
        return False

def obtener_configuracion():
    """Obtiene la configuración del usuario mediante diálogos"""
    
    print("="*60)
    print("🌐 GENERADOR DE QR ONLINE")
    print("="*60)
    
    # Intentar cargar usuario guardado
    usuario_guardado = cargar_usuario()
    
    if usuario_guardado:
        # Preguntar si desea usar el usuario guardado
        usar_guardado = messagebox.askyesno(
            "Usuario encontrado",
            f"Se encontró el usuario guardado:\n\n"
            f"Usuario: {usuario_guardado}\n"
            f"URL: https://{usuario_guardado}.pythonanywhere.com\n\n"
            "¿Deseas usar este usuario?"
        )
        
        if usar_guardado:
            print(f"   ✅ Usando usuario guardado: {usuario_guardado}")
            usuario = usuario_guardado
        else:
            # Preguntar si desea eliminar el usuario guardado
            eliminar = messagebox.askyesno(
                "Cambiar usuario",
                "¿Deseas eliminar el usuario guardado\n"
                "y configurar uno nuevo?"
            )
            if eliminar:
                borrar_usuario()
            
            # Solicitar nuevo usuario
            usuario = solicitar_usuario()
            if usuario:
                # Preguntar si desea guardar el nuevo usuario
                guardar = messagebox.askyesno(
                    "Guardar usuario",
                    f"¿Deseas guardar el usuario '{usuario}'\n"
                    "para futuras generaciones de QR?\n\n"
                    "No tendrás que ingresarlo nuevamente"
                )
                if guardar:
                    guardar_usuario(usuario)
    else:
        # No hay usuario guardado, solicitar
        usuario = solicitar_usuario()
        if usuario:
            # Preguntar si desea guardar
            guardar = messagebox.askyesno(
                "Guardar usuario",
                f"¿Deseas guardar el usuario '{usuario}'\n"
                "para futuras generaciones de QR?\n\n"
                "No tendrás que ingresarlo nuevamente"
            )
            if guardar:
                guardar_usuario(usuario)
    
    if not usuario:
        return None, None
    
    # 2. Seleccionar archivo Excel
    print("\n📂 Paso 2: Selecciona tu archivo Excel")
    messagebox.showinfo(
        "Seleccionar Excel",
        "Ahora selecciona tu archivo Excel\n"
        "con el inventario de medicamentos"
    )
    
    archivo_excel = filedialog.askopenfilename(
        title="Seleccionar archivo Excel",
        filetypes=[
            ("Excel files", "*.xlsx *.xls"),
            ("All files", "*.*")
        ]
    )
    
    if not archivo_excel:
        messagebox.showerror("Error", "Debes seleccionar un archivo Excel")
        return None, None
    
    print(f"   Archivo: {Path(archivo_excel).name}")
    
    return usuario, archivo_excel

def solicitar_usuario():
    """Solicita el usuario de PythonAnywhere"""
    print("\n📝 Configuración de PythonAnywhere")
    usuario = simpledialog.askstring(
        "Usuario de PythonAnywhere",
        "Ingresa tu usuario de PythonAnywhere:\n\n"
        "(El que usaste para registrarte)\n"
        "Ejemplo: salonso"
    )
    
    if not usuario:
        messagebox.showerror("Error", "Debes ingresar un usuario")
        return None
    
    print(f"   Usuario: {usuario}")
    print(f"   URL: https://{usuario}.pythonanywhere.com")
    
    return usuario

def generar_qr_online(usuario, archivo_excel):
    """Genera QR con URLs de internet"""
    
    URL_BASE = f"https://{usuario}.pythonanywhere.com/medicamento?codigo="
    
    print("\n" + "="*60)
    print("🎯 GENERANDO CÓDIGOS QR")
    print("="*60)
    print("\n📝 Configuración:")
    print(f"   Usuario: {usuario}")
    print(f"   URL Base: {URL_BASE}")
    print(f"   Excel: {Path(archivo_excel).name}")
    print("\n" + "="*60)
    
    # Cargar Excel
    try:
        print("\n📂 Cargando datos del Excel...")
        df = pd.read_excel(archivo_excel, sheet_name="Inventario General Enero", header=4)
        df = df.dropna(how='all')
        df = df[df['Código'].notna()]
        df = df[df['Saldo'] > 0]
        print(f"✅ {len(df)} medicamentos con saldo encontrados")
    except Exception as e:
        print(f"\n❌ ERROR al leer Excel: {e}")
        messagebox.showerror(
            "Error al leer Excel",
            f"No se pudo leer el archivo Excel:\n\n{str(e)}\n\n"
            "Verifica que:\n"
            "- El archivo esté cerrado (no abierto en Excel)\n"
            "- Tenga la hoja 'Inventario General Enero'\n"
            "- Los datos empiecen en la fila 5 (header=4)"
        )
        return False
    
    if len(df) == 0:
        messagebox.showwarning(
            "Sin datos",
            "No se encontraron medicamentos con saldo > 0"
        )
        return False
    
    # Crear carpeta
    carpeta_salida = "codigos_qr_online"
    Path(carpeta_salida).mkdir(exist_ok=True)
    
    # Generar QR
    print(f"\n🎯 Generando {len(df)} códigos QR...")
    print("="*60)
    
    codigos_generados = []
    
    for idx, (index, row) in enumerate(df.iterrows()):
        codigo = str(row.get('Código', ''))
        medicamento = str(row.get('Medicamento', ''))
        
        # URL completa de internet
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
        nombre_archivo = f"QR_ONLINE_{codigo}.png"
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
            print(f"  {porcentaje}% completado ({idx + 1}/{len(df)})")
    
    print("="*60)
    print(f"\n✅ COMPLETADO: {len(df)} códigos QR generados")
    print(f"📁 Ubicación: {Path(carpeta_salida).absolute()}")
    
    # Preguntar si generar PDF
    respuesta = messagebox.askyesno(
        "Generar PDF",
        f"✅ {len(df)} códigos QR generados exitosamente\n\n"
        f"📁 Carpeta: {carpeta_salida}\n\n"
        "¿Deseas generar un PDF con todos los QR?"
    )
    
    if respuesta:
        generar_pdf(codigos_generados, usuario)
    
    # Mostrar información final
    print("\n" + "="*60)
    print("🌐 INFORMACIÓN DEL SERVIDOR")
    print("="*60)
    print("\n✅ Los QR apuntan a:")
    print(f"   {URL_BASE}CODIGO")
    print("\n📱 Accesible desde:")
    print("   ✅ Android, iPhone, tablets")
    print("   ✅ Computadoras")
    print("   ✅ Cualquier lugar del mundo con internet")
    print("\n💡 PRÓXIMOS PASOS:")
    print("   1. Ve a: https://www.pythonanywhere.com")
    print(f"   2. Inicia sesión con usuario: {usuario}")
    print("   3. Usa el sincronizador para subir tu Excel")
    print(f"   4. Prueba: https://{usuario}.pythonanywhere.com")
    print("="*60 + "\n")
    
    messagebox.showinfo(
        "¡Completado!",
        f"✅ {len(df)} códigos QR generados\n\n"
        f"📁 Ubicación: {carpeta_salida}\n\n"
        f"🌐 URL del servidor:\n"
        f"https://{usuario}.pythonanywhere.com\n\n"
        "💡 Usa el sincronizador para subir\n"
        "tu Excel actualizado al servidor"
    )
    
    return True

def generar_pdf(codigos_generados, usuario):
    """Genera PDF con los QR"""
    try:
        pdf_path = "codigos_qr_online.pdf"
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
            
            # Información del medicamento
            text_y = y - 12
            text_x = margin + col * spacing_x + 5
            
            c.setFont("Helvetica-Bold", 7)
            c.drawString(text_x, text_y, f"Cod: {qr_data['codigo']}")
            
            text_y -= 9
            c.setFont("Helvetica", 6)
            medicamento = str(qr_data['medicamento'])[:60]
            c.drawString(text_x, text_y, medicamento)
            
            # Marca de agua online
            text_y -= 9
            c.setFont("Helvetica-Bold", 5)
            c.setFillColorRGB(0, 0.5, 0)
            c.drawString(text_x, text_y, f"✓ ONLINE - {usuario}.pythonanywhere.com")
            c.setFillColorRGB(0, 0, 0)
            
            contador += 1
            
            # Progreso
            if (idx + 1) % 10 == 0 or idx == total - 1:
                porcentaje = int((idx + 1) / total * 100)
                print(f"  {porcentaje}% completado ({idx + 1}/{total})")
        
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
        
        # Obtener configuración
        usuario, archivo_excel = obtener_configuracion()
        
        if not usuario or not archivo_excel:
            print("\n❌ Operación cancelada")
            return
        
        # Generar QR
        exito = generar_qr_online(usuario, archivo_excel)
        
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
        # Asegurar que Tkinter se cierre siempre
        print("\n🔄 Cerrando aplicación...")
        cerrar_tkinter()
        time.sleep(0.3)

if __name__ == "__main__":
    main()
    # Forzar salida del programa
    print("👋 Programa finalizado")
    sys.exit(0)