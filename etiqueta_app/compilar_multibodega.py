"""
COMPILADOR MULTI-BODEGA
Genera ejecutables del sistema multi-bodega
"""

import subprocess
import sys
import os
from pathlib import Path

def verificar_pyinstaller():
    """Verifica si PyInstaller está instalado"""
    try:
        import PyInstaller  # noqa: F401
        print("✅ PyInstaller está instalado")
        return True
    except ImportError:
        print("❌ PyInstaller no está instalado")
        print("\n📦 Instalando PyInstaller...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✅ PyInstaller instalado correctamente")
            return True
        except:  # noqa: E722
            print("❌ Error al instalar PyInstaller")
            return False

def generar_ejecutable(script, nombre_exe):
    """Genera un ejecutable desde un script Python"""
    
    print(f"\n{'='*70}")
    print(f"🔨 Generando: {nombre_exe}.exe")
    print(f"{'='*70}")
    
    if not os.path.exists(script):
        print(f"❌ Error: No se encontró {script}")
        return False
    
    # Comando PyInstaller
    cmd = [
        "pyinstaller",
        "--onefile",
        "--console",
        "--name", nombre_exe,
        "--hidden-import", "pandas",
        "--hidden-import", "openpyxl",
        "--hidden-import", "qrcode",
        "--hidden-import", "PIL",
        "--hidden-import", "reportlab",
        "--hidden-import", "requests",
        "--hidden-import", "psutil",
        "--hidden-import", "schedule",
        script
    ]
    
    print("\n📝 Compilando...")
    print(f"   Script: {script}")
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {nombre_exe}.exe generado correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print("❌ Error en la compilación")
        if e.stderr:
            print("\nDetalles del error:")
            print(e.stderr[:500])
        return False

def limpiar_archivos_temporales():
    """Limpia archivos temporales de PyInstaller"""
    print("\n🧹 Limpiando archivos temporales...")
    
    carpetas_temporales = ["build", "__pycache__"]
    
    for carpeta in carpetas_temporales:
        if os.path.exists(carpeta):
            import shutil
            try:
                shutil.rmtree(carpeta)
                print(f"   ✅ Eliminado: {carpeta}/")
            except:  # noqa: E722
                print(f"   ⚠️  No se pudo eliminar: {carpeta}/")
    
    # Eliminar archivos .spec
    import glob
    for archivo in glob.glob("*.spec"):
        try:
            os.remove(archivo)
            print(f"   ✅ Eliminado: {archivo}")
        except:  # noqa: E722
            pass

def main():
    """Función principal"""
    print("="*70)
    print("🔨 COMPILADOR SISTEMA MULTI-BODEGA")
    print("="*70)
    
    # Verificar PyInstaller
    if not verificar_pyinstaller():
        print("\n❌ No se puede continuar sin PyInstaller")
        input("\nPresiona Enter para salir...")
        return
    
    # Programas a compilar
    programas = [
        {
            "script": "generador_qr_multibodega.py",
            "nombre": "GeneradorQR_MultiBodega",
            "descripcion": "Generador de QR por bodega"
        },
        {
            "script": "generador_qr_reportes_multibodega.py",
            "nombre": "GeneradorQR_Reportes_MultiBodega",
            "descripcion": "Generador de QR de reportes (general y por bodega)"
        },
        {
            "script": "sincronizador_multibodega.py",
            "nombre": "Sincronizador_MultiBodega",
            "descripcion": "Sincronizador automático multi-bodega"
        }
    ]
    
    print("\n📋 Programas a compilar:")
    for i, prog in enumerate(programas, 1):
        existe = "✅" if os.path.exists(prog["script"]) else "❌"
        print(f"   {i}. {existe} {prog['nombre']} - {prog['descripcion']}")
    
    # Verificar que todos los archivos existen
    faltantes = [p for p in programas if not os.path.exists(p["script"])]
    if faltantes:
        print("\n❌ Faltan archivos:")
        for p in faltantes:
            print(f"   • {p['script']}")
        print("\n⚠️  Asegúrate de tener todos los archivos .py en esta carpeta")
        input("\nPresiona Enter para salir...")
        return
    
    print("\n¿Deseas compilar estos 3 programas? (s/n): ", end='')
    respuesta = input().strip().lower()
    
    if respuesta != 's':
        print("\n👋 Compilación cancelada")
        input("\nPresiona Enter para salir...")
        return
    
    # Compilar todos
    print(f"\n{'='*70}")
    print("🔨 INICIANDO COMPILACIÓN MULTI-BODEGA")
    print(f"{'='*70}")
    print("\n⏱️  Esto puede tomar 3-5 minutos...")
    
    exitosos = []
    fallidos = []
    
    for prog in programas:
        exito = generar_ejecutable(prog["script"], prog["nombre"])
        if exito:
            exitosos.append(prog["nombre"])
        else:
            fallidos.append(prog["nombre"])
    
    # Limpiar archivos temporales
    limpiar_archivos_temporales()
    
    # Resumen
    print(f"\n{'='*70}")
    print("📊 RESUMEN DE COMPILACIÓN")
    print(f"{'='*70}")
    
    if exitosos:
        print(f"\n✅ Exitosos ({len(exitosos)}):")
        for nombre in exitosos:
            exe_path = Path("dist") / f"{nombre}.exe"
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"   • {nombre}.exe ({size_mb:.1f} MB)")
            else:
                print(f"   • {nombre}.exe")
        print(f"\n📁 Ubicación: {Path('dist').absolute()}")
    
    if fallidos:
        print(f"\n❌ Fallidos ({len(fallidos)}):")
        for nombre in fallidos:
            print(f"   • {nombre}")
    
    print(f"\n{'='*70}")
    
    if exitosos and not fallidos:
        print("\n🎉 ¡TODOS LOS EJECUTABLES GENERADOS EXITOSAMENTE!")
        
        print("\n📦 Archivos generados:")
        print("   1. GeneradorQR_MultiBodega.exe")
        print("      → Genera QR individuales por bodega")
        print("      → Menú interactivo para seleccionar bodega")
        print("      → Carpetas separadas por bodega")
        
        print("\n   2. GeneradorQR_Reportes_MultiBodega.exe")
        print("      → Genera QR de reportes (Rojo, Amarillo, Verde)")
        print("      → Reportes generales o por bodega específica")
        print("      → Menú interactivo con múltiples opciones")
        
        print("\n   3. Sincronizador_MultiBodega.exe")
        print("      → Sincroniza múltiples archivos Excel")
        print("      → Sincronización automática cada hora")
        print("      → Configura solo las bodegas que necesites")
        
        print("\n💡 IMPORTANTE:")
        print("   • Los .exe NO necesitan Python instalado")
        print("   • Puedes copiarlos a cualquier PC Windows")
        print("   • Los archivos .json se crean automáticamente")
        
        print("\n🚀 PRÓXIMOS PASOS:")
        print("   1. Ve a la carpeta: dist/")
        print("   2. Copia los 2 archivos .exe donde los necesites")
        print("   3. Sube flask_app_multibodega.py a PythonAnywhere")
        print("   4. Ejecuta los .exe para configurar el sistema")
        
        print("\n¿Deseas abrir la carpeta 'dist/'? (s/n): ", end='')
        abrir = input().strip().lower()
        
        if abrir == 's':
            try:
                if os.name == 'nt':
                    os.startfile("dist")
                else:
                    subprocess.run(["open", "dist"])
                print("✅ Carpeta abierta")
            except:  # noqa: E722
                print("⚠️  No se pudo abrir la carpeta automáticamente")
                print(f"   Abre manualmente: {Path('dist').absolute()}")
    
    elif exitosos:
        print("\n⚠️  Algunos programas no se compilaron correctamente")
        print("   Revisa los mensajes de error arriba")
    else:
        print("\n❌ No se pudo compilar ningún programa")
        print("\n🔍 Soluciones:")
        print("   1. Verifica que PyInstaller esté instalado: pip show pyinstaller")
        print("   2. Actualiza PyInstaller: pip install --upgrade pyinstaller")
        print("   3. Instala dependencias: pip install pandas qrcode reportlab requests schedule")
    
    print("\n" + "="*70)
    input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    main()
