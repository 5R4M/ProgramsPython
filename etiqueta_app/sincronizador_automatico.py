"""
SINCRONIZADOR DE INVENTARIO CON PYTHONANYWHERE
Sube automáticamente tu Excel actualizado al servidor
"""

import requests
from pathlib import Path
from tkinter import Tk, filedialog, simpledialog, messagebox
import sys
import time
import json
import os

# =====================================================
# CONFIGURACIÓN
# =====================================================

# Archivo para guardar credenciales
ARCHIVO_CREDENCIALES = "credenciales_pythonanywhere.json"

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

def cargar_credenciales():
    """Carga las credenciales guardadas desde el archivo JSON"""
    try:
        if os.path.exists(ARCHIVO_CREDENCIALES):
            with open(ARCHIVO_CREDENCIALES, 'r', encoding='utf-8') as f:
                credenciales = json.load(f)
                print("\n✅ Credenciales encontradas")
                print(f"   Usuario: {credenciales.get('usuario', 'No guardado')}")
                return credenciales.get('usuario'), credenciales.get('api_token')
        return None, None
    except Exception as e:
        print(f"⚠️ Error al cargar credenciales: {e}")
        return None, None

def guardar_credenciales(usuario, api_token):
    """Guarda las credenciales en un archivo JSON"""
    try:
        credenciales = {
            'usuario': usuario,
            'api_token': api_token
        }
        with open(ARCHIVO_CREDENCIALES, 'w', encoding='utf-8') as f:
            json.dump(credenciales, f, indent=4)
        print(f"\n💾 Credenciales guardadas en: {ARCHIVO_CREDENCIALES}")
        return True
    except Exception as e:
        print(f"⚠️ Error al guardar credenciales: {e}")
        return False

def borrar_credenciales():
    """Elimina el archivo de credenciales"""
    try:
        if os.path.exists(ARCHIVO_CREDENCIALES):
            os.remove(ARCHIVO_CREDENCIALES)
            print("\n🗑️ Credenciales eliminadas")
            return True
        return False
    except Exception as e:
        print(f"⚠️ Error al borrar credenciales: {e}")
        return False

def obtener_credenciales():
    """Obtiene las credenciales del usuario"""
    
    print("="*60)
    print("🔄 SINCRONIZADOR DE INVENTARIO")
    print("="*60)
    
    # Intentar cargar credenciales guardadas
    usuario_guardado, api_token_guardado = cargar_credenciales()
    
    if usuario_guardado and api_token_guardado:
        # Preguntar si desea usar las credenciales guardadas
        usar_guardadas = messagebox.askyesno(
            "Credenciales encontradas",
            f"Se encontraron credenciales guardadas:\n\n"
            f"Usuario: {usuario_guardado}\n\n"
            "¿Deseas usar estas credenciales?"
        )
        
        if usar_guardadas:
            print(f"   ✅ Usando credenciales guardadas para: {usuario_guardado}")
            return usuario_guardado, api_token_guardado
        else:
            # Preguntar si desea eliminar las credenciales guardadas
            eliminar = messagebox.askyesno(
                "Eliminar credenciales",
                "¿Deseas eliminar las credenciales guardadas?"
            )
            if eliminar:
                borrar_credenciales()
    
    # Solicitar nuevas credenciales
    print("\n📝 Paso 1: Credenciales de PythonAnywhere")
    usuario = simpledialog.askstring(
        "Usuario de PythonAnywhere",
        "Ingresa tu usuario de PythonAnywhere:\n\n"
        "Ejemplo: salonso"
    )
    
    if not usuario:
        messagebox.showerror("Error", "Debes ingresar un usuario")
        return None, None
    
    print(f"   Usuario: {usuario}")
    
    # 2. Solicitar API Token
    print("\n🔑 Paso 2: API Token")
    messagebox.showinfo(
        "API Token requerido",
        "Necesitas tu API Token de PythonAnywhere\n\n"
        "¿Cómo obtenerlo?\n"
        "1. Ve a: www.pythonanywhere.com\n"
        "2. Inicia sesión\n"
        "3. Ve a 'Account' (esquina superior derecha)\n"
        "4. Busca 'API token'\n"
        "5. Haz clic en 'Create a new API token'\n"
        "6. Copia el token generado"
    )
    
    api_token = simpledialog.askstring(
        "API Token",
        "Pega aquí tu API Token:\n\n"
        "(Es una clave larga, como: 1a2b3c4d5e6f7g8h9i0j...)",
        show='*'
    )
    
    if not api_token:
        messagebox.showerror("Error", "Debes ingresar el API Token")
        return None, None
    
    print(f"   Token: {'*' * 20}")
    
    # Preguntar si desea guardar las credenciales
    guardar = messagebox.askyesno(
        "Guardar credenciales",
        "¿Deseas guardar estas credenciales\n"
        "para futuras sincronizaciones?\n\n"
        "⚠️ Las credenciales se guardarán en un archivo\n"
        "local en tu computadora"
    )
    
    if guardar:
        guardar_credenciales(usuario, api_token)
        messagebox.showinfo(
            "Credenciales guardadas",
            f"✅ Credenciales guardadas correctamente\n\n"
            f"📁 Archivo: {ARCHIVO_CREDENCIALES}\n\n"
            "En la próxima sincronización no tendrás\n"
            "que ingresar tus credenciales nuevamente"
        )
    
    return usuario, api_token

def seleccionar_excel():
    """Permite seleccionar el archivo Excel"""
    
    print("\n📂 Paso 3: Seleccionar archivo Excel")
    messagebox.showinfo(
        "Seleccionar Excel",
        "Selecciona tu archivo Excel actualizado\n"
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
        return None
    
    print(f"   Archivo: {Path(archivo_excel).name}")
    return archivo_excel

def validar_excel(archivo_excel):
    """Valida que el Excel tenga la estructura correcta"""
    try:
        import pandas as pd
        
        print("\n🔍 Validando estructura del Excel...")
        
        df = pd.read_excel(
            archivo_excel, 
            sheet_name="Inventario General Enero", 
            header=4
        )
        
        # Verificar columnas requeridas
        columnas_requeridas = ['Código', 'Medicamento', 'Saldo']
        columnas_faltantes = []
        
        for col in columnas_requeridas:
            if col not in df.columns:
                columnas_faltantes.append(col)
        
        if columnas_faltantes:
            print(f"   ❌ Faltan columnas: {', '.join(columnas_faltantes)}")
            return False
        
        # Contar registros válidos
        df = df.dropna(how='all')
        df = df[df['Código'].notna()]
        df = df[df['Saldo'] > 0]
        
        print("   ✅ Estructura válida")
        print(f"   ✅ {len(df)} medicamentos con saldo encontrados")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error validando Excel: {e}")
        return False

def subir_archivo_pythonanywhere(usuario, api_token, archivo_excel):
    """Sube el archivo a PythonAnywhere usando múltiples métodos"""
    
    print("\n" + "="*60)
    print("📤 SUBIENDO ARCHIVO A PYTHONANYWHERE")
    print("="*60)
    
    try:
        # URL de la API
        ruta_archivo = f"/home/{usuario}/mysite/inventario.xlsx"
        url = f"https://www.pythonanywhere.com/api/v0/user/{usuario}/files/path{ruta_archivo}"
        
        print("\n🌐 Conectando con el servidor...")
        print(f"   Usuario: {usuario}")
        print(f"   Destino: {ruta_archivo}")
        
        # Leer el archivo
        with open(archivo_excel, 'rb') as f:
            contenido = f.read()
        
        tamano_mb = len(contenido) / (1024 * 1024)
        print(f"   Tamaño: {tamano_mb:.2f} MB")
        
        # Headers con autenticación
        headers = {
            'Authorization': f'Token {api_token}'
        }
        
        print("\n📤 Subiendo archivo (Método 1: POST con files)...")
        
        # MÉTODO 1: POST con files
        files = {
            'content': ('inventario.xlsx', contenido, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        response = requests.post(
            url,
            headers=headers,
            files=files,
            timeout=60
        )
        
        # Si falla, intentar MÉTODO 2: PUT con data
        if response.status_code not in [200, 201]:
            print(f"   ⚠️ Método 1 falló ({response.status_code}), intentando Método 2...")
            
            headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            response = requests.put(
                url,
                headers=headers,
                data=contenido,
                timeout=60
            )
        
        # Verificar respuesta
        if response.status_code in [200, 201, 204]:
            print("✅ ¡Archivo subido exitosamente!")
            
            # Recargar datos en Flask
            print("\n🔄 Recargando datos en el servidor Flask...")
            try:
                reload_url = f"https://{usuario}.pythonanywhere.com/recargar"
                reload_response = requests.get(reload_url, timeout=30)
                
                if reload_response.status_code == 200:
                    print(f"✅ {reload_response.text}")
                else:
                    print("⚠️ No se pudo recargar automáticamente")
                    print("   Reinicia tu aplicación Flask manualmente")
            except Exception as e:
                print(f"⚠️ No se pudo recargar automáticamente: {e}")
                print("   Reinicia tu aplicación Flask manualmente")
            
            return True
            
        elif response.status_code == 401:
            print("❌ Error de autenticación")
            print("   Verifica tu API Token")
            print(f"   Respuesta: {response.text}")
            
            # Preguntar si desea eliminar credenciales incorrectas
            if os.path.exists(ARCHIVO_CREDENCIALES):
                eliminar = messagebox.askyesno(
                    "Credenciales incorrectas",
                    "Las credenciales guardadas parecen ser incorrectas.\n\n"
                    "¿Deseas eliminarlas para ingresar nuevas credenciales?"
                )
                if eliminar:
                    borrar_credenciales()
            
            return False
            
        elif response.status_code == 404:
            print("❌ Ruta no encontrada")
            print(f"   Verifica que el usuario '{usuario}' sea correcto")
            print(f"   Respuesta: {response.text}")
            return False
            
        else:
            print(f"❌ Error {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout: El servidor tardó demasiado en responder")
        print("   Intenta nuevamente en unos momentos")
        return False
        
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión")
        print("   Verifica tu conexión a internet")
        return False
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False

def mostrar_instrucciones_api_token():
    """Muestra instrucciones detalladas para obtener el API Token"""
    
    html_instrucciones = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Instrucciones API Token</title>
    <style>
        body { font-family: Arial; padding: 20px; }
        .paso { background: #f0f0f0; padding: 15px; margin: 10px 0; border-left: 4px solid #667eea; }
        .numero { background: #667eea; color: white; padding: 5px 12px; border-radius: 50%; }
    </style>
</head>
<body>
    <h1>🔑 Cómo obtener tu API Token de PythonAnywhere</h1>
    
    <div class="paso">
        <span class="numero">1</span>
        Ve a <a href="https://www.pythonanywhere.com" target="_blank">www.pythonanywhere.com</a>
        e inicia sesión con tu cuenta
    </div>
    
    <div class="paso">
        <span class="numero">2</span>
        Haz clic en tu nombre de usuario (esquina superior derecha)
        y selecciona "Account"
    </div>
    
    <div class="paso">
        <span class="numero">3</span>
        Busca la sección "API token" en la página
    </div>
    
    <div class="paso">
        <span class="numero">4</span>
        Haz clic en "Create a new API token"
    </div>
    
    <div class="paso">
        <span class="numero">5</span>
        Copia el token generado (es una cadena larga de letras y números)
    </div>
    
    <div class="paso">
        <span class="numero">6</span>
        Pégalo en el programa cuando te lo solicite
    </div>
    
    <p><strong>⚠️ Importante:</strong> Guarda tu API Token en un lugar seguro. 
    No lo compartas con nadie.</p>
</body>
</html>
"""
    
    # Guardar instrucciones
    archivo_instrucciones = "INSTRUCCIONES_API_TOKEN.html"
    with open(archivo_instrucciones, 'w', encoding='utf-8') as f:
        f.write(html_instrucciones)
    
    print(f"\n📄 Instrucciones guardadas en: {archivo_instrucciones}")
    
    # Preguntar si abrir
    respuesta = messagebox.askyesno(
        "Instrucciones API Token",
        "¿Deseas abrir las instrucciones detalladas\n"
        "para obtener tu API Token?"
    )
    
    if respuesta:
        import platform
        import subprocess
        
        try:
            sistema = platform.system()
            if sistema == "Windows":
                os.startfile(archivo_instrucciones)
            elif sistema == "Darwin":
                subprocess.run(["open", archivo_instrucciones])
            else:
                subprocess.run(["xdg-open", archivo_instrucciones])
        except:  # noqa: E722
            pass

def main():
    """Función principal"""
    try:
        inicializar_tkinter()
        
        # Mostrar instrucciones si es necesario
        respuesta = messagebox.askyesno(
            "Bienvenido",
            "🔄 SINCRONIZADOR DE INVENTARIO\n\n"
            "Este programa subirá tu archivo Excel\n"
            "actualizado a PythonAnywhere\n\n"
            "Necesitarás:\n"
            "✓ Usuario de PythonAnywhere\n"
            "✓ API Token\n"
            "✓ Archivo Excel actualizado\n\n"
            "¿Necesitas ayuda para obtener el API Token?"
        )
        
        if respuesta:
            mostrar_instrucciones_api_token()
        
        # Obtener credenciales (cargadas o nuevas)
        usuario, api_token = obtener_credenciales()
        
        if not usuario or not api_token:
            print("\n❌ Operación cancelada")
            return
        
        # Seleccionar Excel
        archivo_excel = seleccionar_excel()
        
        if not archivo_excel:
            print("\n❌ Operación cancelada")
            return
        
        # Validar Excel
        if not validar_excel(archivo_excel):
            messagebox.showerror(
                "Error de validación",
                "El archivo Excel no tiene la estructura correcta.\n\n"
                "Verifica que:\n"
                "- Tenga la hoja 'Inventario General Enero'\n"
                "- Los datos empiecen en la fila 5\n"
                "- Tenga las columnas: Código, Medicamento, Saldo"
            )
            return
        
        # Confirmar subida
        confirmacion = messagebox.askyesno(
            "Confirmar sincronización",
            f"¿Confirmas que deseas subir este archivo?\n\n"
            f"📄 Archivo: {Path(archivo_excel).name}\n"
            f"🌐 Destino: pythonanywhere.com\n"
            f"👤 Usuario: {usuario}\n\n"
            "Esto reemplazará el archivo actual en el servidor"
        )
        
        if not confirmacion:
            print("\n❌ Operación cancelada por el usuario")
            return
        
        # Subir archivo
        exito = subir_archivo_pythonanywhere(usuario, api_token, archivo_excel)
        
        if exito:
            print("\n" + "="*60)
            print("✅ SINCRONIZACIÓN COMPLETADA")
            print("="*60)
            print("\n🎉 Tu inventario está actualizado en el servidor")
            print("\n🌐 Prueba escaneando un QR o visitando:")
            print(f"   https://{usuario}.pythonanywhere.com")
            print("\n💡 Los QR ahora mostrarán la información actualizada")
            print("="*60 + "\n")
            
            messagebox.showinfo(
                "¡Sincronización exitosa!",
                f"✅ Archivo subido correctamente\n\n"
                f"🌐 URL: https://{usuario}.pythonanywhere.com\n\n"
                "Los códigos QR ahora mostrarán\n"
                "la información actualizada"
            )
        else:
            print("\n❌ La sincronización no se completó correctamente")
            messagebox.showerror(
                "Error",
                "No se pudo completar la sincronización.\n\n"
                "Verifica:\n"
                "- Tu conexión a internet\n"
                "- Tus credenciales de PythonAnywhere\n"
                "- Que el API Token sea correcto"
            )
    
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