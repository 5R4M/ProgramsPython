import os
import shutil
import zipfile
from datetime import datetime

# -------------------------------------------------------------------
# CONFIGURACIÓN: RUTAS ESPECÍFICAS DE TU PROYECTO
# -------------------------------------------------------------------

# Ruta base del proyecto (directorio donde está este archivo: declaraciones_app)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ruta de la base de datos (actas_notariales.db está en declaraciones_app\)
DATABASE_PATH = os.path.join(BASE_DIR, "actas_notariales.db")

# Carpeta donde se guardan los documentos generados
# (según indicas: declaraciones_app\data\documentos)
DOCUMENTOS_DIR = os.path.join(BASE_DIR, "data", "documentos")


# -------------------------------------------------------------------
# EXPORTAR DOCUMENTOS A ZIP
# -------------------------------------------------------------------
def exportar_documentos_a_zip(destino_dir: str) -> str:
    """
    Crea un ZIP con todos los documentos de DOCUMENTOS_DIR
    y lo guarda en destino_dir. Devuelve la ruta del ZIP.
    """
    if not os.path.isdir(DOCUMENTOS_DIR):
        raise FileNotFoundError(f"La carpeta de documentos no existe: {DOCUMENTOS_DIR}")

    if not os.path.isdir(destino_dir):
        raise FileNotFoundError(f"La carpeta destino no existe: {destino_dir}")

    fecha_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"backup_documentos_{fecha_str}.zip"
    zip_path = os.path.join(destino_dir, zip_name)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(DOCUMENTOS_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                # Estructura relativa dentro del ZIP
                arcname = os.path.relpath(file_path, DOCUMENTOS_DIR)
                zf.write(file_path, arcname)

    return zip_path


# -------------------------------------------------------------------
# BACKUP DE BASE DE DATOS
# -------------------------------------------------------------------
def backup_base_datos(destino_dir: str) -> str:
    """
    Copia la base de datos SQLite a destino_dir con un nombre único.
    Devuelve la ruta del archivo de backup.
    """
    if not os.path.isfile(DATABASE_PATH):
        raise FileNotFoundError(f"La base de datos no existe: {DATABASE_PATH}")

    if not os.path.isdir(destino_dir):
        raise FileNotFoundError(f"La carpeta destino no existe: {destino_dir}")

    fecha_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.basename(DATABASE_PATH)
    backup_name = f"backup_{os.path.splitext(base_name)[0]}_{fecha_str}.db"
    backup_path = os.path.join(destino_dir, backup_name)

    shutil.copy2(DATABASE_PATH, backup_path)
    return backup_path


# -------------------------------------------------------------------
# FUNCIÓN PRINCIPAL: HACER BACKUP COMPLETO (EXPORTAR)
# -------------------------------------------------------------------
def hacer_backup_completo(carpeta_destino: str):
    """
    Recibe la carpeta de destino elegida por el usuario.
    1. Exporta documentos a ZIP en esa carpeta.
    2. Realiza backup de la base de datos en esa carpeta.
    Devuelve (ruta_zip_docs, ruta_backup_db).
    """
    if not carpeta_destino or not os.path.isdir(carpeta_destino):
        raise FileNotFoundError(f"Carpeta destino inválida: {carpeta_destino}")

    # 1) Exportar documentos
    zip_docs = exportar_documentos_a_zip(carpeta_destino)

    # 2) Backup base de datos
    backup_db = backup_base_datos(carpeta_destino)

    return zip_docs, backup_db


# -------------------------------------------------------------------
# RESTAURAR BASE DE DATOS DESDE UN BACKUP .DB
# -------------------------------------------------------------------
def restaurar_base_datos(desde_backup_db: str):
    """
    Restaura la base de datos principal (DATABASE_PATH) desde un archivo
    de backup .db (desde_backup_db).

    ATENCIÓN: Sobrescribe la base de datos actual.
    """
    if not os.path.isfile(desde_backup_db):
        raise FileNotFoundError(f"Archivo de backup DB no existe: {desde_backup_db}")

    # Nos aseguramos de que la carpeta de la DB exista
    db_dir = os.path.dirname(DATABASE_PATH)
    os.makedirs(db_dir, exist_ok=True)

    # Copia el backup sobre la DB actual
    shutil.copy2(desde_backup_db, DATABASE_PATH)


# -------------------------------------------------------------------
# RESTAURAR DOCUMENTOS DESDE ZIP
# -------------------------------------------------------------------
def restaurar_documentos_desde_zip(zip_path: str, limpiar_destino: bool = False):
    """
    Restaura los documentos desde un ZIP (zip_path) hacia DOCUMENTOS_DIR.

    - Si limpiar_destino=True, borra el contenido de DOCUMENTOS_DIR antes
      de extraer.
    """
    if not os.path.isfile(zip_path):
        raise FileNotFoundError(f"Archivo ZIP de documentos no existe: {zip_path}")

    # Nos aseguramos de que la carpeta de documentos exista
    os.makedirs(DOCUMENTOS_DIR, exist_ok=True)

    if limpiar_destino:
        # Eliminar TODO lo que haya dentro de DOCUMENTOS_DIR
        for root, dirs, files in os.walk(DOCUMENTOS_DIR):
            for file in files:
                try:
                    os.remove(os.path.join(root, file))
                except Exception:
                    pass
            # (si quieres, también puedes limpiar subdirectorios)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(DOCUMENTOS_DIR)


# -------------------------------------------------------------------
# RESTAURAR BACKUP COMPLETO (ALTO NIVEL)
# -------------------------------------------------------------------
def restaurar_backup_completo(zip_docs: str | None = None,
                              backup_db: str | None = None,
                              limpiar_docs: bool = False):
    """
    Restaura todo el sistema desde los archivos de backup.

    - zip_docs: ruta del ZIP de documentos (o None para no tocar documentos).
    - backup_db: ruta del .db de backup (o None para no tocar la base).
    - limpiar_docs: si True, limpia DOCUMENTOS_DIR antes de extraer el ZIP.
    """
    if zip_docs:
        restaurar_documentos_desde_zip(zip_docs, limpiar_destino=limpiar_docs)

    if backup_db:
        restaurar_base_datos(backup_db)


# -------------------------------------------------------------------
# SI SE EJECUTA DIRECTAMENTE ESTE ARCHIVO (PRUEBA SIMPLE)
# -------------------------------------------------------------------
if __name__ == "__main__":
    try:
        destino = BASE_DIR
        hacer_backup_completo(destino)
    except Exception as e:
        print(f"❌ Ocurrió un error durante el backup: {e}")