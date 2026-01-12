"""
SINCRONIZADOR AUTOMÁTICO CADA HORA
Monitorea tu archivo Excel y lo sube automáticamente cada hora
"""

import requests
import time
import json
import os
from datetime import datetime
from pathlib import Path
import schedule

# =====================================================
# CONFIGURACIÓN
# =====================================================

ARCHIVO_CONFIG = "config_sincronizacion_automatica.json"

def cargar_configuracion():
    """Carga la configuración guardada"""
    try:
        if os.path.exists(ARCHIVO_CONFIG):
            with open(ARCHIVO_CONFIG, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"❌ Error cargando configuración: {e}")
        return None

def guardar_configuracion(config):
    """Guarda la configuración"""
    try:
        with open(ARCHIVO_CONFIG, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Error guardando configuración: {e}")
        return False

def configurar_primera_vez():
    """Configuración inicial interactiva"""
    print("="*70)
    print("⚙️  CONFIGURACIÓN INICIAL DEL SINCRONIZADOR AUTOMÁTICO")
    print("="*70)
    
    print("\n📝 Ingresa la siguiente información:")
    
    # Usuario
    usuario = input("\n1. Usuario de PythonAnywhere: ").strip()
    if not usuario:
        print("❌ Usuario requerido")
        return None
    
    # API Token
    api_token = input("2. API Token: ").strip()
    if not api_token:
        print("❌ API Token requerido")
        return None
    
    # Ruta del Excel
    print("\n3. Ruta completa del archivo Excel:")
    print("   Ejemplo: C:\\Users\\TuNombre\\Documents\\FORMATO_INSUMOS_ENERO_2026.xlsx")
    ruta_excel = input("   Ruta: ").strip()
    
    if not ruta_excel or not os.path.exists(ruta_excel):
        print("❌ Archivo no encontrado")
        return None
    
    # Intervalo
    print("\n4. Intervalo de sincronización:")
    print("   a) Cada hora")
    print("   b) Cada 30 minutos")
    print("   c) Cada 2 horas")
    opcion = input("   Opción (a/b/c): ").strip().lower()
    
    intervalos = {
        'a': 60,
        'b': 30,
        'c': 120
    }
    
    intervalo_minutos = intervalos.get(opcion, 60)
    
    config = {
        'usuario': usuario,
        'api_token': api_token,
        'ruta_excel': ruta_excel,
        'intervalo_minutos': intervalo_minutos,
        'url_servidor': f'https://{usuario}.pythonanywhere.com',
        'ruta_destino': f'/home/{usuario}/mysite/inventario.xlsx'
    }
    
    print("\n✅ Configuración guardada:")
    print(f"   Usuario: {usuario}")
    print(f"   Excel: {Path(ruta_excel).name}")
    print(f"   Intervalo: Cada {intervalo_minutos} minutos")
    
    if guardar_configuracion(config):
        return config
    else:
        return None

def subir_archivo(config):
    """Sube el archivo a PythonAnywhere"""
    try:
        usuario = config['usuario']
        api_token = config['api_token']
        ruta_excel = config['ruta_excel']
        
        # Verificar que el archivo existe
        if not os.path.exists(ruta_excel):
            print(f"❌ Archivo no encontrado: {ruta_excel}")
            return False
        
        # URL de la API
        ruta_destino = config['ruta_destino']
        url = f"https://www.pythonanywhere.com/api/v0/user/{usuario}/files/path{ruta_destino}"
        
        print(f"\n📤 Subiendo archivo... [{datetime.now().strftime('%H:%M:%S')}]")
        
        # Leer archivo
        with open(ruta_excel, 'rb') as f:
            contenido = f.read()
        
        # Headers
        headers = {
            'Authorization': f'Token {api_token}'
        }
        
        # Subir con POST (multipart/form-data)
        files = {
            'content': ('inventario.xlsx', contenido, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        response = requests.post(url, headers=headers, files=files, timeout=60)
        
        if response.status_code in [200, 201, 204]:
            print("✅ Archivo subido exitosamente")
            
            # Recargar datos
            try:
                reload_url = f"{config['url_servidor']}/recargar"
                reload_response = requests.get(reload_url, timeout=30)
                if reload_response.status_code == 200:
                    print("✅ Datos recargados en servidor")
                    return True
            except:  # noqa: E722
                pass
            
            return True
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def sincronizar_ahora(config):
    """Ejecuta una sincronización inmediata"""
    print("\n" + "="*70)
    print(f"🔄 SINCRONIZACIÓN AUTOMÁTICA - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    exito = subir_archivo(config)
    
    if exito:
        print("✅ Sincronización completada")
    else:
        print("❌ Sincronización fallida")
    
    print(f"\n⏰ Próxima sincronización en {config['intervalo_minutos']} minutos")
    print("="*70)
    
    return exito

def main():
    """Función principal del sincronizador automático"""
    print("="*70)
    print("🔄 SINCRONIZADOR AUTOMÁTICO DE INVENTARIO")
    print("="*70)
    
    # Cargar o crear configuración
    config = cargar_configuracion()
    
    if not config:
        print("\n⚙️  No hay configuración guardada")
        config = configurar_primera_vez()
        
        if not config:
            print("\n❌ No se pudo completar la configuración")
            input("\nPresiona Enter para salir...")
            return
    else:
        print("\n✅ Configuración cargada:")
        print(f"   Usuario: {config['usuario']}")
        print(f"   Excel: {Path(config['ruta_excel']).name}")
        print(f"   Intervalo: Cada {config['intervalo_minutos']} minutos")
    
    # Preguntar si hacer sincronización inicial
    print("\n¿Deseas hacer una sincronización inicial ahora? (s/n): ", end='')
    respuesta = input().strip().lower()
    
    if respuesta == 's':
        sincronizar_ahora(config)
    
    # Programar sincronizaciones automáticas
    intervalo = config['intervalo_minutos']
    
    if intervalo == 60:
        schedule.every().hour.do(lambda: sincronizar_ahora(config))
    elif intervalo == 30:
        schedule.every(30).minutes.do(lambda: sincronizar_ahora(config))
    elif intervalo == 120:
        schedule.every(2).hours.do(lambda: sincronizar_ahora(config))
    else:
        schedule.every(intervalo).minutes.do(lambda: sincronizar_ahora(config))
    
    print("\n" + "="*70)
    print("✅ SINCRONIZADOR ACTIVO")
    print("="*70)
    print(f"\n📅 Sincronización programada cada {intervalo} minutos")
    print(f"📂 Archivo: {config['ruta_excel']}")
    print(f"🌐 Servidor: {config['url_servidor']}")
    print("\n💡 Este programa seguirá ejecutándose en segundo plano")
    print("💡 Mantenlo abierto para que las sincronizaciones continúen")
    print("\n⚠️  Para detener el sincronizador, cierra esta ventana")
    print("="*70)
    
    # Ejecutar el scheduler
    try:
        contador = 0
        while True:
            schedule.run_pending()
            time.sleep(1)
            
            # Mostrar punto cada 60 segundos para saber que sigue activo
            contador += 1
            if contador >= 60:
                print(".", end='', flush=True)
                contador = 0
                
    except KeyboardInterrupt:
        print("\n\n🛑 Sincronizador detenido por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    main()