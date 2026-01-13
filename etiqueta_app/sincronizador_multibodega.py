"""
SINCRONIZADOR AUTOMÁTICO MULTI-BODEGA
Sincroniza múltiples archivos Excel (una por bodega)
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

ARCHIVO_CONFIG = "config_sincronizacion_multibodega.json"

# Definición de bodegas
BODEGAS = {
    'medico': 'Material Médico Quirúrgico e Insumos de Laboratorio',
    'medicamentos': 'Medicamentos',
    'limpieza': 'Limpieza',
    'oficina': 'Oficina',
    'varios': 'Varios',
    'programas': 'Programas'
}

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
    print("⚙️  CONFIGURACIÓN INICIAL - SINCRONIZADOR MULTI-BODEGA")
    print("="*70)
    
    print("\n📝 Información general:")
    
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
    
    # Intervalo
    print("\n3. Intervalo de sincronización:")
    print("   a) Cada hora")
    print("   b) Cada 30 minutos")
    print("   c) Cada 2 horas")
    opcion = input("   Opción (a/b/c): ").strip().lower()
    
    intervalos = {'a': 60, 'b': 30, 'c': 120}
    intervalo_minutos = intervalos.get(opcion, 60)
    
    # Configurar bodegas
    print("\n" + "="*70)
    print("📦 CONFIGURACIÓN DE BODEGAS")
    print("="*70)
    print("\nAhora configura cada bodega que quieras sincronizar.")
    print("Presiona Enter (vacío) para saltar una bodega.")
    
    bodegas_config = {}
    
    for codigo, nombre in BODEGAS.items():
        print(f"\n📁 Bodega: {nombre}")
        ruta = input("   Ruta del Excel: ").strip().strip('"').strip("'")
        
        if ruta and os.path.exists(ruta):
            bodegas_config[codigo] = {
                'nombre': nombre,
                'ruta_excel': ruta,
                'ruta_destino': f'/home/{usuario}/mysite/inventario_{codigo}.xlsx'
            }
            print(f"   ✅ Configurada: {Path(ruta).name}")
        elif ruta:
            print("   ⚠️  Archivo no encontrado, saltando...")
        else:
            print("   ℹ️  Saltada")
    
    if not bodegas_config:
        print("\n❌ Debes configurar al menos una bodega")
        return None
    
    config = {
        'usuario': usuario,
        'api_token': api_token,
        'intervalo_minutos': intervalo_minutos,
        'url_servidor': f'https://{usuario}.pythonanywhere.com',
        'bodegas': bodegas_config
    }
    
    print("\n✅ Configuración guardada:")
    print(f"   Usuario: {usuario}")
    print(f"   Intervalo: Cada {intervalo_minutos} minutos")
    print(f"   Bodegas configuradas: {len(bodegas_config)}")
    
    if guardar_configuracion(config):
        return config
    else:
        return None

def subir_archivo(config, codigo_bodega, bodega_info):
    """Sube un archivo específico a PythonAnywhere"""
    try:
        usuario = config['usuario']
        api_token = config['api_token']
        ruta_excel = bodega_info['ruta_excel']
        
        # Verificar que el archivo existe
        if not os.path.exists(ruta_excel):
            print(f"   ❌ Archivo no encontrado: {ruta_excel}")
            return False
        
        # URL de la API
        ruta_destino = bodega_info['ruta_destino']
        url = f"https://www.pythonanywhere.com/api/v0/user/{usuario}/files/path{ruta_destino}"
        
        print(f"   📤 Subiendo {bodega_info['nombre']}...")
        
        # Leer archivo
        with open(ruta_excel, 'rb') as f:
            contenido = f.read()
        
        # Headers
        headers = {
            'Authorization': f'Token {api_token}'
        }
        
        # Subir con POST
        files = {
            'content': (f'inventario_{codigo_bodega}.xlsx', contenido, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        response = requests.post(url, headers=headers, files=files, timeout=60)
        
        if response.status_code in [200, 201, 204]:
            print(f"   ✅ {bodega_info['nombre']} - Subido")
            return True
        else:
            print(f"   ❌ Error {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def sincronizar_todas_bodegas(config):
    """Sincroniza todas las bodegas configuradas"""
    print("\n" + "="*70)
    print(f"🔄 SINCRONIZACIÓN - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    exitosas = 0
    fallidas = 0
    
    for codigo_bodega, bodega_info in config['bodegas'].items():
        exito = subir_archivo(config, codigo_bodega, bodega_info)
        if exito:
            exitosas += 1
        else:
            fallidas += 1
    
    # Recargar datos en Flask
    try:
        reload_url = f"{config['url_servidor']}/recargar"
        reload_response = requests.get(reload_url, timeout=30)
        if reload_response.status_code == 200:
            print("\n   ✅ Datos recargados en servidor")
    except:  # noqa: E722
        pass
    
    print(f"\n📊 Resultado: {exitosas} exitosas, {fallidas} fallidas")
    print(f"⏰ Próxima sincronización en {config['intervalo_minutos']} minutos")
    print("="*70)
    
    return exitosas > 0

def main():
    """Función principal"""
    print("="*70)
    print("🔄 SINCRONIZADOR AUTOMÁTICO MULTI-BODEGA")
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
        print(f"   Intervalo: Cada {config['intervalo_minutos']} minutos")
        print(f"   Bodegas: {len(config['bodegas'])}")
        for codigo, info in config['bodegas'].items():
            print(f"      • {info['nombre']}: {Path(info['ruta_excel']).name}")
    
    # Preguntar si hacer sincronización inicial
    print("\n¿Deseas hacer una sincronización inicial ahora? (s/n): ", end='')
    respuesta = input().strip().lower()
    
    if respuesta == 's':
        sincronizar_todas_bodegas(config)
    
    # Programar sincronizaciones automáticas
    intervalo = config['intervalo_minutos']
    
    if intervalo == 60:
        schedule.every().hour.do(lambda: sincronizar_todas_bodegas(config))
    elif intervalo == 30:
        schedule.every(30).minutes.do(lambda: sincronizar_todas_bodegas(config))
    elif intervalo == 120:
        schedule.every(2).hours.do(lambda: sincronizar_todas_bodegas(config))
    else:
        schedule.every(intervalo).minutes.do(lambda: sincronizar_todas_bodegas(config))
    
    print("\n" + "="*70)
    print("✅ SINCRONIZADOR MULTI-BODEGA ACTIVO")
    print("="*70)
    print(f"\n📅 Sincronización programada cada {intervalo} minutos")
    print(f"📦 Bodegas configuradas: {len(config['bodegas'])}")
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
