# sync_automatico.py
# Versión silenciosa para Programador de Tareas de Windows
# No requiere input del usuario - solo sincroniza y termina

import requests
import json
import os
import sys
import logging
from pathlib import Path

# =====================================================
# RUTAS BASE - Compatible con PyInstaller y script .py
# =====================================================

def obtener_directorio_base():
    """
    Retorna la carpeta donde está el .exe o el .py.
    - Con PyInstaller (.exe): usa sys.executable
    - Con Python normal (.py): usa __file__
    """
    if getattr(sys, 'frozen', False):
        # Ejecutando como .exe compilado con PyInstaller
        return Path(sys.executable).parent
    else:
        # Ejecutando como script .py normal
        return Path(__file__).parent

BASE_DIR = obtener_directorio_base()

# =====================================================
# CONFIGURACIÓN DE LOGS
# =====================================================

LOG_DIR = BASE_DIR / "logs"

try:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
except Exception as e:
    # Si no puede crear logs/, usar el directorio temporal del sistema
    import tempfile
    LOG_DIR = Path(tempfile.gettempdir()) / "InventarioQR_logs"
    LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "sync_log.txt"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger(__name__)

ARCHIVO_CONFIG = BASE_DIR / "config_sincronizacion_multibodega.json"


def cargar_configuracion():
    try:
        if ARCHIVO_CONFIG.exists():
            with open(ARCHIVO_CONFIG, 'r', encoding='utf-8') as f:
                return json.load(f)
        log.error(f"No se encontró config en: {ARCHIVO_CONFIG}")
        return None
    except Exception as e:
        log.error(f"Error cargando configuración: {e}")
        return None


def subir_archivo(config, codigo_bodega, bodega_info):
    try:
        usuario    = config['usuario']
        api_token  = config['api_token']
        ruta_excel = bodega_info['ruta_excel']

        if not os.path.exists(ruta_excel):
            log.warning(f"[{codigo_bodega}] Archivo no encontrado: {ruta_excel}")
            return False

        ruta_destino = bodega_info['ruta_destino']
        url = f"https://www.pythonanywhere.com/api/v0/user/{usuario}/files/path{ruta_destino}"

        with open(ruta_excel, 'rb') as f:
            contenido = f.read()

        headers = {'Authorization': f'Token {api_token}'}
        files = {
            'content': (
                f'inventario_{codigo_bodega}.xlsx',
                contenido,
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        }

        response = requests.post(url, headers=headers, files=files, timeout=60)

        if response.status_code in [200, 201, 204]:
            log.info(f"[{codigo_bodega}] ✅ Subido correctamente - {Path(ruta_excel).name}")
            return True
        else:
            log.error(f"[{codigo_bodega}] ❌ Error HTTP {response.status_code}: {response.text[:200]}")
            return False

    except Exception as e:
        log.error(f"[{codigo_bodega}] ❌ Excepción: {e}")
        return False


def recargar_servidor(config):
    try:
        url = f"{config['url_servidor']}/recargar"
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            log.info("✅ Servidor recargado correctamente")
        else:
            log.warning(f"⚠️ Recarga respondió HTTP {resp.status_code}")
    except Exception as e:
        log.warning(f"⚠️ No se pudo recargar servidor: {e}")


def main():
    log.info("=" * 60)
    log.info("🔄 INICIO SINCRONIZACIÓN AUTOMÁTICA")
    log.info(f"📁 Directorio base : {BASE_DIR}")
    log.info(f"📋 Config          : {ARCHIVO_CONFIG}")
    log.info(f"📝 Log             : {LOG_FILE}")
    log.info("=" * 60)

    config = cargar_configuracion()
    if not config:
        log.error("No hay configuración disponible. Ejecuta primero el sincronizador principal.")
        sys.exit(1)

    bodegas = config.get('bodegas', {})
    if not bodegas:
        log.error("No hay bodegas configuradas.")
        sys.exit(1)

    log.info(f"Usuario: {config['usuario']} | Bodegas: {len(bodegas)}")

    exitosas = 0
    fallidas = 0

    for codigo, info in bodegas.items():
        ok = subir_archivo(config, codigo, info)
        if ok:
            exitosas += 1
        else:
            fallidas += 1

    recargar_servidor(config)

    log.info(f"📊 Resultado: {exitosas} exitosas | {fallidas} fallidas")
    log.info("=" * 60)

    # Código de salida: 0=éxito, 1=algunas fallidas, 2=todas fallidas
    if fallidas == 0:
        sys.exit(0)
    elif exitosas > 0:
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()