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
import tkinter as tk
from tkinter import filedialog

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

def seleccionar_archivos_multiples():
    """Abre diálogo para seleccionar múltiples archivos Excel"""
    try:
        # Crear ventana raíz oculta
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        print("\n📂 Abriendo selector de archivos...")
        print("   💡 Mantén presionado Ctrl para seleccionar múltiples archivos")
        
        # Abrir diálogo de selección
        archivos = filedialog.askopenfilenames(
            title="Selecciona los archivos Excel de las bodegas",
            filetypes=[
                ("Archivos Excel", "*.xlsx *.xls"),
                ("Todos los archivos", "*.*")
            ],
            multiple=True
        )
        
        root.destroy()
        
        if archivos:
            print(f"\n✅ {len(archivos)} archivo(s) seleccionado(s):")
            for archivo in archivos:
                print(f"   • {Path(archivo).name}")
            return list(archivos)
        else:
            print("\n⚠️  No se seleccionaron archivos")
            return []
            
    except Exception as e:
        print(f"\n❌ Error al abrir selector: {e}")
        print("   Usa el método manual (arrastrar archivos)")
        return None

def asignar_archivos_a_bodegas(config, archivos_seleccionados):
    """Asigna archivos seleccionados a las bodegas correspondientes"""
    print("\n" + "="*70)
    print("🔗 ASIGNAR ARCHIVOS A BODEGAS")
    print("="*70)
    
    archivos_disponibles = archivos_seleccionados.copy()
    archivos_asignados = {}
    
    for codigo, info in config['bodegas'].items():
        print(f"\n📁 Bodega: {info['nombre']}")
        print(f"   Archivo actual: {Path(info['ruta_excel']).name}")
        
        if not archivos_disponibles:
            print("   ⚠️  No quedan archivos por asignar")
            print("   ℹ️  Manteniendo archivo actual")
            continue
        
        print("\n   Archivos disponibles:")
        for i, archivo in enumerate(archivos_disponibles, 1):
            print(f"   {i}. {Path(archivo).name}")
        print("   0. Mantener archivo actual")
        
        opcion = input("\n   Selecciona archivo (0-{}): ".format(len(archivos_disponibles))).strip()
        
        try:
            opcion_num = int(opcion)
            if opcion_num == 0:
                print(f"   ℹ️  Manteniendo: {Path(info['ruta_excel']).name}")
            elif 1 <= opcion_num <= len(archivos_disponibles):
                archivo_seleccionado = archivos_disponibles[opcion_num - 1]
                archivos_asignados[codigo] = archivo_seleccionado
                archivos_disponibles.remove(archivo_seleccionado)
                print(f"   ✅ Asignado: {Path(archivo_seleccionado).name}")
            else:
                print("   ❌ Opción inválida, manteniendo actual")
        except ValueError:
            print("   ❌ Entrada inválida, manteniendo actual")
    
    # Actualizar configuración
    if archivos_asignados:
        for codigo, archivo in archivos_asignados.items():
            config['bodegas'][codigo]['ruta_excel'] = archivo
        
        print(f"\n✅ {len(archivos_asignados)} bodega(s) actualizada(s)")
        return True
    else:
        print("\n⚠️  No se actualizó ninguna bodega")
        return False

def reconfigurar_completa(config_actual):
    """Permite modificar toda la configuración (usuario, token, intervalo, bodegas)"""
    print("\n" + "="*70)
    print("⚙️  RECONFIGURACIÓN COMPLETA")
    print("="*70)
    print("\nPresiona Enter (vacío) para mantener el valor actual.")
    
    # Usuario
    print("\n1. Usuario de PythonAnywhere")
    print(f"   Actual: {config_actual.get('usuario', 'No configurado')}")
    usuario = input("   Nuevo usuario (Enter para mantener): ").strip()
    if not usuario:
        usuario = config_actual.get('usuario')
    
    # API Token
    print("\n2. API Token")
    token_actual = config_actual.get('api_token', '')
    token_oculto = token_actual[:8] + "..." if len(token_actual) > 8 else "No configurado"
    print(f"   Actual: {token_oculto}")
    api_token = input("   Nuevo token (Enter para mantener): ").strip()
    if not api_token:
        api_token = config_actual.get('api_token')
    
    # Intervalo
    print("\n3. Intervalo de sincronización")
    print(f"   Actual: Cada {config_actual.get('intervalo_minutos', 60)} minutos")
    print("   a) Cada hora (60 min)")
    print("   b) Cada 30 minutos")
    print("   c) Cada 2 horas (120 min)")
    print("   d) Mantener actual")
    opcion = input("   Opción (a/b/c/d): ").strip().lower()
    
    intervalos = {'a': 60, 'b': 30, 'c': 120, 'd': config_actual.get('intervalo_minutos', 60)}
    intervalo_minutos = intervalos.get(opcion, config_actual.get('intervalo_minutos', 60))
    
    # Bodegas
    print("\n4. Configuración de bodegas")
    print(f"   Actual: {len(config_actual.get('bodegas', {}))} bodega(s) configurada(s)")
    print("\n¿Deseas reconfigurar las bodegas? (s/n): ", end='')
    reconfig_bodegas = input().strip().lower()
    
    if reconfig_bodegas == 's':
        print("\n" + "="*70)
        print("📦 RECONFIGURACIÓN DE BODEGAS")
        print("="*70)
        print("\nPresiona Enter (vacío) para mantener la bodega actual.")
        print("Escribe 'eliminar' para quitar una bodega de la configuración.")
        
        bodegas_config = {}
        bodegas_actuales = config_actual.get('bodegas', {})
        
        for codigo, nombre in BODEGAS.items():
            print(f"\n📁 Bodega: {nombre}")
            
            if codigo in bodegas_actuales:
                print(f"   Actual: {bodegas_actuales[codigo]['ruta_excel']}")
                ruta = input("   Nueva ruta (Enter=mantener, 'eliminar'=quitar): ").strip().strip('"').strip("'")
                
                if ruta.lower() == 'eliminar':
                    print("   ❌ Bodega eliminada de la configuración")
                    continue
                elif not ruta:
                    # Mantener actual
                    bodegas_config[codigo] = bodegas_actuales[codigo]
                    print(f"   ℹ️  Mantenida: {Path(bodegas_actuales[codigo]['ruta_excel']).name}")
                    continue
            else:
                ruta = input("   Ruta del Excel (Enter para saltar): ").strip().strip('"').strip("'")
            
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
                if codigo in bodegas_actuales:
                    print("   ℹ️  Mantenida")
                else:
                    print("   ℹ️  Saltada")
    else:
        # Mantener bodegas actuales pero actualizar rutas de destino por si cambió el usuario
        bodegas_config = config_actual.get('bodegas', {})
        for codigo in bodegas_config:
            bodegas_config[codigo]['ruta_destino'] = f'/home/{usuario}/mysite/inventario_{codigo}.xlsx'
    
    # Crear nueva configuración
    nueva_config = {
        'usuario': usuario,
        'api_token': api_token,
        'intervalo_minutos': intervalo_minutos,
        'url_servidor': f'https://{usuario}.pythonanywhere.com',
        'bodegas': bodegas_config
    }
    
    # Mostrar resumen
    print("\n" + "="*70)
    print("📋 RESUMEN DE NUEVA CONFIGURACIÓN")
    print("="*70)
    print(f"   Usuario: {usuario}")
    print(f"   Intervalo: Cada {intervalo_minutos} minutos")
    print(f"   Bodegas: {len(bodegas_config)}")
    for codigo, info in bodegas_config.items():
        print(f"      • {info['nombre']}: {Path(info['ruta_excel']).name}")
    
    print("\n¿Deseas guardar esta configuración? (s/n): ", end='')
    confirmar = input().strip().lower()
    
    if confirmar == 's':
        if guardar_configuracion(nueva_config):
            print("\n✅ Configuración actualizada y guardada")
            return nueva_config
        else:
            print("\n❌ Error al guardar configuración")
            return None
    else:
        print("\n⚠️  Configuración no guardada, manteniendo anterior")
        return config_actual

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
        
        # Menú de opciones
        print("\n" + "="*70)
        print("⚙️  ¿QUÉ DESEAS HACER?")
        print("="*70)
        print("\n   1. Solo actualizar rutas de archivos Excel")
        print("   2. Reconfigurar TODO (usuario, token, intervalo, bodegas)")
        print("   3. Continuar sin cambios")
        
        opcion = input("\nOpción (1/2/3): ").strip()
        
        if opcion == '1':
            # Solo actualizar archivos
            print("\n¿Deseas actualizar las rutas de los archivos Excel? (s/n): ", end='')
            reconfigurar = input().strip().lower()
            
            if reconfigurar == 's':
                print("\n" + "="*70)
                print("📂 MÉTODO DE ACTUALIZACIÓN")
                print("="*70)
                print("\n¿Cómo deseas seleccionar los archivos?")
                print("   1. Selector múltiple (GUI) - Selecciona varios archivos a la vez")
                print("   2. Uno por uno (Manual) - Arrastra cada archivo individualmente")
                
                metodo = input("\nMétodo (1/2): ").strip()
                
                if metodo == '1':
                    # Método GUI - Selección múltiple
                    archivos = seleccionar_archivos_multiples()
                    
                    if archivos:
                        if asignar_archivos_a_bodegas(config, archivos):
                            if guardar_configuracion(config):
                                print("\n✅ Configuración actualizada y guardada")
                            else:
                                print("\n⚠️  Error al guardar, pero continuando con cambios en memoria")
                        else:
                            print("\n⚠️  No se realizaron cambios")
                    elif archivos is None:
                        print("\n⚠️  Selector no disponible, usando método manual...")
                        metodo = '2'
                
                if metodo == '2':
                    # Método manual - Uno por uno
                    print("\n" + "="*70)
                    print("📂 ACTUALIZAR RUTAS DE ARCHIVOS")
                    print("="*70)
                    print("\nPresiona Enter (vacío) para mantener el archivo actual.")
                    
                    for codigo, info in config['bodegas'].items():
                        print(f"\n📁 Bodega: {info['nombre']}")
                        print(f"   Archivo actual: {info['ruta_excel']}")
                        nueva_ruta = input("   Nueva ruta (Enter para mantener): ").strip().strip('"').strip("'")
                        
                        if nueva_ruta:
                            if os.path.exists(nueva_ruta):
                                config['bodegas'][codigo]['ruta_excel'] = nueva_ruta
                                print(f"   ✅ Actualizada: {Path(nueva_ruta).name}")
                            else:
                                print("   ❌ Archivo no encontrado, manteniendo actual")
                        else:
                            print(f"   ℹ️  Manteniendo: {Path(info['ruta_excel']).name}")
                    
                    # Guardar configuración actualizada
                    if guardar_configuracion(config):
                        print("\n✅ Configuración actualizada y guardada")
                    else:
                        print("\n⚠️  Error al guardar, pero continuando con cambios en memoria")
        
        elif opcion == '2':
            # Reconfigurar todo
            config_nueva = reconfigurar_completa(config)
            if config_nueva:
                config = config_nueva
        
        elif opcion == '3':
            # Continuar sin cambios
            print("\n✅ Manteniendo configuración actual")
        else:
            print("\n⚠️  Opción inválida, manteniendo configuración actual")
    
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