"""
GENERADOR DE QR MULTI-BODEGA
Genera QR para múltiples bodegas (Medicamentos, Material Médico, Limpieza, etc.)
Con registro JSON para evitar duplicados entre sesiones.
"""

import pandas as pd
import qrcode
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import json
import os
import hashlib
from datetime import datetime

# =====================================================
# CONFIGURACIÓN
# =====================================================

ARCHIVO_CONFIG = "config_generador_qr_multibodega.json"

# ── Carpeta fija donde están los Excel ───────────────────────────────────────
# Cambia esta ruta si mueves la carpeta en el futuro.
CARPETA_EXCEL = r"C:\Users\SELSO\OneDrive - DIRECCION DE AREA DE SALUD GUATEMALA NOR ORIENTE\Escritorio\Etiquetas Bodegas"

# Definición de bodegas
BODEGAS = {
    '1': {
        'nombre': 'Material Médico Quirúrgico e Insumos de Laboratorio',
        'codigo': 'medico',
        'hoja_excel': 'Inventario General',
        'header_row': 4
    },
    '2': {
        'nombre': 'Medicamentos',
        'codigo': 'medicamentos',
        'hoja_excel': 'Inventario General',
        'header_row': 4
    },
    '3': {
        'nombre': 'Limpieza',
        'codigo': 'limpieza',
        'hoja_excel': 'Inventario General',
        'header_row': 4
    },
    '4': {
        'nombre': 'Oficina',
        'codigo': 'oficina',
        'hoja_excel': 'Inventario General',
        'header_row': 4
    },
    '5': {
        'nombre': 'Varios',
        'codigo': 'varios',
        'hoja_excel': 'Inventario General',
        'header_row': 4
    },
    '6': {
        'nombre': 'Programas',
        'codigo': 'programas',
        'hoja_excel': 'Inventario General',
        'header_row': 4
    }
}

# =====================================================
# REGISTRO JSON - NÚCLEO ANTI-DUPLICADOS
# =====================================================

def _ruta_registro(codigo_bodega: str) -> str:
    """Devuelve la ruta del archivo JSON de registro para una bodega."""
    return f"registro_qr_{codigo_bodega}.json"


def cargar_registro(codigo_bodega: str) -> dict:
    """
    Carga el registro JSON de una bodega.
    Estructura del registro:
    {
        "bodega": "varios",
        "ultima_actualizacion": "2025-03-17T10:00:00",
        "codigos": {
            "VAR-0001": {
                "url": "https://...",
                "hash_url": "abc123",
                "fecha_generado": "2025-01-10T08:30:00",
                "archivo_png": "codigos_qr_varios/QR_varios_VAR-0001.png",
                "incluido_en_pdfs": ["codigos_qr_varios_20250110.pdf"]
            },
            ...
        }
    }
    """
    ruta = _ruta_registro(codigo_bodega)
    if os.path.exists(ruta):
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                registro = json.load(f)
                total = len(registro.get('codigos', {}))
                print(f"   📋 Registro encontrado: {total} código(s) previo(s)")
                return registro
        except Exception as e:
            print(f"   ⚠️  Error al leer registro, se creará uno nuevo: {e}")

    # Registro vacío si no existe
    return {
        "bodega": codigo_bodega,
        "ultima_actualizacion": None,
        "codigos": {}
    }


def guardar_registro(codigo_bodega: str, registro: dict) -> bool:
    """Persiste el registro JSON actualizado en disco."""
    ruta = _ruta_registro(codigo_bodega)
    try:
        registro["ultima_actualizacion"] = datetime.now().isoformat()
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(registro, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"   ⚠️  Error al guardar registro: {e}")
        return False


def _hash_url(url: str) -> str:
    """Genera un hash MD5 corto de la URL para detectar cambios."""
    return hashlib.md5(url.encode()).hexdigest()[:12]


def codigo_necesita_regenerarse(entrada_registro: dict, url_actual: str) -> bool:
    """
    Retorna True si el QR debe regenerarse porque:
    - La URL cambió (el producto fue reasignado o el usuario cambió)
    - El archivo PNG ya no existe en disco
    """
    hash_actual = _hash_url(url_actual)

    # ¿La URL cambió?
    if entrada_registro.get("hash_url") != hash_actual:
        return True

    # ¿El PNG fue borrado manualmente?
    archivo_png = entrada_registro.get("archivo_png", "")
    if archivo_png and not os.path.exists(archivo_png):
        return True

    return False


# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================

def cargar_configuracion():
    try:
        if os.path.exists(ARCHIVO_CONFIG):
            with open(ARCHIVO_CONFIG, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"\n✅ Configuración encontrada")
                print(f"   Usuario: {config.get('usuario', 'No guardado')}")
                return config
        return None
    except Exception as e:
        print(f"⚠️  Error al cargar configuración: {e}")
        return None


def guardar_configuracion(config):
    try:
        with open(ARCHIVO_CONFIG, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print("\n💾 Configuración guardada")
        return True
    except Exception as e:
        print(f"⚠️  Error al guardar configuración: {e}")
        return False


def configurar():
    print("\n" + "="*70)
    print("⚙️  CONFIGURACIÓN DEL GENERADOR MULTI-BODEGA")
    print("="*70)

    print("\n1. Usuario de PythonAnywhere:")
    usuario = input("   Ingresa tu usuario: ").strip()

    if not usuario:
        print("❌ Usuario requerido")
        return None

    print(f"   ✅ Usuario: {usuario}")
    print(f"   ✅ URL: https://{usuario}.pythonanywhere.com")

    config = {'usuario': usuario, 'bodegas': {}}

    if guardar_configuracion(config):
        print("\n✅ Configuración completada")
        return config
    return None


# =====================================================
# MENÚ DE SELECCIÓN
# =====================================================

def seleccionar_bodega():
    print("\n" + "="*70)
    print("📦 SELECCIONA LA BODEGA")
    print("="*70)
    print("\nBodegas disponibles:")
    for key, bodega in BODEGAS.items():
        print(f"   {key}. {bodega['nombre']}")
    print("\n   0. Salir")

    opcion = input("\nSelecciona una bodega (0-6): ").strip()
    if opcion == '0':
        return None
    if opcion not in BODEGAS:
        print("❌ Opción inválida")
        return None
    return BODEGAS[opcion]


def seleccionar_excel_bodega(bodega):
    """
    Busca archivos Excel (.xlsx / .xls) en CARPETA_EXCEL y presenta
    un menú numerado. El usuario solo escribe un número.
    Si la carpeta no existe o está vacía, pide la ruta manualmente.
    """
    print(f"\n📂 Buscando archivos Excel para: {bodega['nombre']}")

    carpeta = Path(CARPETA_EXCEL)

    # ── Verificar que la carpeta existe ───────────────────────────────────────
    if not carpeta.exists():
        print(f"   ⚠️  Carpeta no encontrada: {CARPETA_EXCEL}")
        print("   Ingresa la ruta del archivo manualmente:")
        ruta = input("   Ruta: ").strip().strip('"').strip("'")
        if not os.path.exists(ruta):
            print(f"❌ Archivo no encontrado: {ruta}")
            return None
        return ruta

    # ── Escanear Excel en la carpeta (no recursivo) ───────────────────────────
    archivos = sorted(
        [f for f in carpeta.iterdir()
         if f.suffix.lower() in ('.xlsx', '.xls') and not f.name.startswith('~$')],
        key=lambda f: f.name.lower()
    )

    if not archivos:
        print(f"   ⚠️  No se encontraron archivos Excel en:\n   {CARPETA_EXCEL}")
        print("   Ingresa la ruta del archivo manualmente:")
        ruta = input("   Ruta: ").strip().strip('"').strip("'")
        if not os.path.exists(ruta):
            print(f"❌ Archivo no encontrado: {ruta}")
            return None
        return ruta

    # ── Mostrar menú ──────────────────────────────────────────────────────────
    print(f"\n   Archivos encontrados en: ...{carpeta.name}")
    print("   " + "─"*50)
    for i, archivo in enumerate(archivos, start=1):
        # Tamaño en KB para orientar al usuario
        kb = archivo.stat().st_size / 1024
        print(f"   {i:2d}. {archivo.name:<45} ({kb:,.0f} KB)")
    print("   " + "─"*50)
    print(f"    0. Ingresar ruta manualmente")

    while True:
        opcion = input(f"\n   Selecciona un archivo (0-{len(archivos)}): ").strip()

        if opcion == '0':
            ruta = input("   Ruta: ").strip().strip('"').strip("'")
            if not os.path.exists(ruta):
                print(f"   ❌ Archivo no encontrado: {ruta}")
                return None
            return ruta

        if opcion.isdigit() and 1 <= int(opcion) <= len(archivos):
            seleccionado = archivos[int(opcion) - 1]
            print(f"\n   ✅ Seleccionado: {seleccionado.name}")
            return str(seleccionado)

        print(f"   ❌ Opción inválida. Ingresa un número entre 0 y {len(archivos)}.")


# =====================================================
# GENERACIÓN DE QR CON CONTROL DE DUPLICADOS
# =====================================================

def generar_qr_bodega(config, bodega, ruta_excel):
    """
    Genera QR para una bodega.
    - Lee el registro JSON existente.
    - Solo genera PNGs para códigos nuevos o cuya URL cambió.
    - Actualiza el registro al finalizar.
    """
    usuario       = config['usuario']
    codigo_bodega = bodega['codigo']
    URL_BASE      = f"https://{usuario}.pythonanywhere.com/medicamento?codigo="
    carpeta_salida = f"codigos_qr_{codigo_bodega}"

    print("\n" + "="*70)
    print(f"🎯 GENERANDO QR - {bodega['nombre'].upper()}")
    print("="*70)
    print(f"\n📝 Usuario : {usuario}")
    print(f"📦 Bodega  : {bodega['nombre']}")
    print(f"🌐 URL Base: {URL_BASE}")
    print(f"📂 Excel   : {Path(ruta_excel).name}")
    print("="*70)

    # ── Cargar Excel ──────────────────────────────────────────────────────────
    try:
        print("\n📂 Cargando datos del Excel...")
        df = pd.read_excel(
            ruta_excel,
            sheet_name=bodega['hoja_excel'],
            header=bodega['header_row']
        )
        df = df.dropna(how='all')
        df = df[df['Código'].notna()]
        df = df[df['Saldo'] > 0]
        print(f"✅ {len(df)} productos con saldo encontrados")
    except Exception as e:
        print(f"\n❌ ERROR al leer Excel: {e}")
        return False

    if len(df) == 0:
        print("\n⚠️  No se encontraron productos con saldo > 0")
        return False

    # ── Cargar registro JSON ──────────────────────────────────────────────────
    print("\n🔍 Verificando registro de códigos previos...")
    registro = cargar_registro(codigo_bodega)
    codigos_previos = registro["codigos"]

    Path(carpeta_salida).mkdir(exist_ok=True)

    # ── Clasificar filas ──────────────────────────────────────────────────────
    filas_nuevas      = []   # código no existe en el registro
    filas_regenerar   = []   # URL cambió o PNG fue borrado
    filas_omitidas    = []   # ya existen y no cambiaron → se omiten

    for _, row in df.iterrows():
        codigo   = str(row.get('Código', '')).strip()
        producto = str(row.get('Medicamento', row.get('Producto', ''))).strip()
        url      = f"{URL_BASE}{codigo}&bodega={codigo_bodega}"

        if codigo not in codigos_previos:
            filas_nuevas.append((codigo, producto, url))
        elif codigo_necesita_regenerarse(codigos_previos[codigo], url):
            filas_regenerar.append((codigo, producto, url))
        else:
            filas_omitidas.append(codigo)

    # ── Resumen antes de procesar ─────────────────────────────────────────────
    print("\n" + "─"*50)
    print(f"  🆕 Nuevos a generar      : {len(filas_nuevas)}")
    print(f"  🔄 A regenerar (cambios) : {len(filas_regenerar)}")
    print(f"  ⏭️  Omitidos (sin cambios): {len(filas_omitidas)}")
    print("─"*50)

    filas_a_procesar = filas_nuevas + filas_regenerar

    if not filas_a_procesar:
        print("\n✅ Todos los QR ya están actualizados. No hay nada nuevo que generar.")
        _ofrecer_pdf(registro, codigos_previos, carpeta_salida, usuario, bodega)
        return True

    # ── Generar PNGs ──────────────────────────────────────────────────────────
    print(f"\n🎯 Procesando {len(filas_a_procesar)} código(s)...\n")
    codigos_generados_ahora = []

    for idx, (codigo, producto, url) in enumerate(filas_a_procesar):
        # Construir nombre de archivo (igual que antes)
        nombre_archivo = f"QR_{codigo_bodega}_{codigo}.png"
        for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
            nombre_archivo = nombre_archivo.replace(char, '-')

        ruta_png = Path(carpeta_salida) / nombre_archivo

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
        img.save(ruta_png)

        # Actualizar registro para este código
        codigos_previos[codigo] = {
            "url"             : url,
            "hash_url"        : _hash_url(url),
            "producto"        : producto,
            "fecha_generado"  : datetime.now().isoformat(),
            "archivo_png"     : str(ruta_png),
            "incluido_en_pdfs": codigos_previos.get(codigo, {}).get("incluido_en_pdfs", [])
        }

        codigos_generados_ahora.append({
            'ruta'   : str(ruta_png),
            'codigo' : codigo,
            'producto': producto,
            'bodega' : bodega['nombre']
        })

        # Progreso
        if (idx + 1) % max(1, len(filas_a_procesar) // 10) == 0 or idx == 0:
            pct = int((idx + 1) / len(filas_a_procesar) * 100)
            print(f"  {pct:3d}% ({idx + 1:3d}/{len(filas_a_procesar)})  ➜  {codigo}")

    # ── Persistir registro actualizado ────────────────────────────────────────
    registro["codigos"] = codigos_previos
    if guardar_registro(codigo_bodega, registro):
        print(f"\n💾 Registro actualizado: {_ruta_registro(codigo_bodega)}")

    print(f"\n✅ {len(codigos_generados_ahora)} QR generado(s) correctamente")
    print(f"📁 Carpeta: {Path(carpeta_salida).absolute()}")

    # ── Ofrecer PDF ───────────────────────────────────────────────────────────
    _ofrecer_pdf(registro, codigos_previos, carpeta_salida,
                 usuario, bodega, codigos_generados_ahora)

    return True


def _ofrecer_pdf(registro, codigos_previos, carpeta_salida,
                 usuario, bodega, codigos_nuevos=None):
    """Pregunta qué incluir en el PDF y lo genera."""
    if codigos_nuevos:
        print("\n¿Qué deseas incluir en el PDF?")
        print("  1. Solo los QR nuevos/modificados")
        print("  2. Todos los QR de la bodega")
        opcion = input("Selecciona (1/2) o Enter para omitir: ").strip()
    else:
        print("\n¿Deseas generar un PDF con todos los QR? (s/n): ", end='')
        opcion = '2' if input().strip().lower() == 's' else ''

    if opcion == '1' and codigos_nuevos:
        generar_pdf(codigos_nuevos, usuario, bodega, registro)
    elif opcion == '2':
        todos = _todos_los_codigos(codigos_previos, carpeta_salida, bodega['nombre'])
        generar_pdf(todos, usuario, bodega, registro)
    else:
        print("⏭️  PDF omitido")


def _todos_los_codigos(codigos_previos, carpeta_salida, nombre_bodega):
    """Construye la lista completa de QR desde el registro + archivos PNG."""
    resultado = []
    for codigo, info in sorted(codigos_previos.items()):
        ruta_png = info.get("archivo_png", "")
        if ruta_png and os.path.exists(ruta_png):
            resultado.append({
                'ruta'   : ruta_png,
                'codigo' : codigo,
                'producto': info.get("producto", ""),
                'bodega' : nombre_bodega
            })
    return resultado


# =====================================================
# GENERACIÓN DE PDF
# =====================================================

def _nombre_pdf(bodega_codigo: str) -> str:
    """Nombre de archivo PDF con fecha para no sobreescribir versiones anteriores."""
    fecha = datetime.now().strftime("%Y%m%d_%H%M")
    return f"codigos_qr_{bodega_codigo}_{fecha}.pdf"


def generar_pdf(codigos_generados, usuario, bodega, registro=None):
    """Genera PDF con los QR - actualiza el registro con el PDF generado."""
    try:
        pdf_path = _nombre_pdf(bodega['codigo'])
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter

        cols, rows    = 2, 3
        qr_size       = 1.7 * inch
        margin        = 0.4 * inch
        spacing_x     = (width  - 2 * margin) / cols
        spacing_y     = (height - 2 * margin) / rows

        COLOR_BORDE  = (0.2, 0.2, 0.2)
        COLOR_FONDO  = (0.98, 0.98, 0.98)
        COLOR_BODEGA = (0, 0.5, 0)

        contador = 0
        total    = len(codigos_generados)

        print(f"\n📄 Generando PDF '{pdf_path}' con {total} QR(s)...")

        for idx, qr_data in enumerate(codigos_generados):
            if contador >= (cols * rows):
                c.showPage()
                contador = 0

            col = contador % cols
            row = contador // cols

            x_recuadro   = margin + col * spacing_x + 10
            y_recuadro   = height - margin - (row + 1) * spacing_y + 10
            ancho_recuadro = spacing_x - 20
            alto_recuadro  = spacing_y - 20

            # Fondo y borde
            c.setFillColorRGB(*COLOR_FONDO)
            c.setStrokeColorRGB(*COLOR_BORDE)
            c.setLineWidth(2)
            c.roundRect(x_recuadro, y_recuadro, ancho_recuadro, alto_recuadro,
                        8, fill=1, stroke=1)

            # QR centrado
            x_qr = x_recuadro + (ancho_recuadro - qr_size) / 2
            y_qr = y_recuadro + alto_recuadro - qr_size - 15
            c.drawImage(qr_data['ruta'], x_qr, y_qr, qr_size, qr_size)

            text_x = x_recuadro + 8
            text_y = y_qr - 10

            # Código
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(text_x, text_y, f"CÓDIGO: {qr_data['codigo']}")
            text_y -= 18

            # Producto (máx. 3 líneas)
            c.setFont("Helvetica", 9)
            palabras    = str(qr_data['producto']).split()
            lineas, linea_actual = [], ""
            for palabra in palabras:
                if len(linea_actual + " " + palabra) <= 45:
                    linea_actual += (" " if linea_actual else "") + palabra
                else:
                    if linea_actual:
                        lineas.append(linea_actual)
                    linea_actual = palabra
            if linea_actual:
                lineas.append(linea_actual)

            for linea in lineas[:3]:
                c.drawString(text_x, text_y, linea)
                text_y -= 12

            # Bodega
            text_y -= 5
            c.setFont("Helvetica-Bold", 7)
            c.setFillColorRGB(*COLOR_BODEGA)
            c.drawString(text_x, text_y, f"📦 {bodega['nombre']}")

            # URL
            text_y -= 10
            c.setFont("Helvetica", 5)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawString(text_x, text_y,
                         f"https://{usuario}.pythonanywhere.com")

            contador += 1

            if (idx + 1) % 10 == 0 or idx == total - 1:
                pct = int((idx + 1) / total * 100)
                print(f"  {pct:3d}% ({idx + 1}/{total})")

        c.save()
        print(f"\n✅ PDF generado: {pdf_path}")

        # ── Registrar PDF en cada código incluido ─────────────────────────────
        if registro:
            for qr_data in codigos_generados:
                codigo = qr_data['codigo']
                if codigo in registro["codigos"]:
                    pdfs = registro["codigos"][codigo].get("incluido_en_pdfs", [])
                    if pdf_path not in pdfs:
                        pdfs.append(pdf_path)
                    registro["codigos"][codigo]["incluido_en_pdfs"] = pdfs
            guardar_registro(bodega['codigo'], registro)
            print(f"💾 Registro actualizado con el PDF generado")

        # ── Abrir PDF ─────────────────────────────────────────────────────────
        print("\n¿Deseas abrir el PDF? (s/n): ", end='')
        if input().strip().lower() == 's':
            import platform, subprocess
            sistema = platform.system()
            try:
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


# =====================================================
# UTILIDADES EXTRA
# =====================================================

def mostrar_estado_registro(codigo_bodega: str):
    """Muestra un resumen del registro JSON de una bodega."""
    registro = cargar_registro(codigo_bodega)
    codigos  = registro.get("codigos", {})

    if not codigos:
        print("   (Sin registros aún)")
        return

    print(f"\n{'─'*60}")
    print(f"  Total de códigos registrados : {len(codigos)}")
    print(f"  Última actualización         : {registro.get('ultima_actualizacion', 'N/A')}")

    # Contar cuántos PNGs siguen existiendo
    existentes = sum(1 for v in codigos.values()
                     if os.path.exists(v.get("archivo_png", "")))
    print(f"  PNGs presentes en disco      : {existentes}/{len(codigos)}")
    print(f"{'─'*60}")


# =====================================================
# MAIN
# =====================================================

def main():
    print("="*70)
    print("🏥 GENERADOR DE QR MULTI-BODEGA  (con control de duplicados JSON)")
    print("="*70)

    try:
        config = cargar_configuracion()

        if not config:
            print("\n⚙️  No hay configuración guardada")
            config = configurar()
            if not config:
                print("\n❌ Configuración fallida")
                input("\nPresiona Enter para salir...")
                return
        else:
            print(f"\n✅ Usuario: {config['usuario']}")
            print(f"🌐 URL    : https://{config['usuario']}.pythonanywhere.com")

        while True:
            bodega = seleccionar_bodega()
            if not bodega:
                print("\n👋 Saliendo...")
                break

            # Mostrar estado del registro antes de procesar
            print(f"\n📊 Estado actual del registro para '{bodega['nombre']}':")
            mostrar_estado_registro(bodega['codigo'])

            ruta_excel = seleccionar_excel_bodega(bodega)
            if not ruta_excel:
                continue

            exito = generar_qr_bodega(config, bodega, ruta_excel)

            if exito:
                print("\n✅ Proceso completado para esta bodega")

            print("\n¿Deseas procesar otra bodega? (s/n): ", end='')
            if input().strip().lower() != 's':
                break

        print("\n✅ Programa finalizado")

    except KeyboardInterrupt:
        print("\n\n🛑 Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPresiona Enter para cerrar...")


if __name__ == "__main__":
    main()