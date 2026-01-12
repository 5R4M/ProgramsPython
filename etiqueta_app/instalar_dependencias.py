"""
INSTALADOR DE DEPENDENCIAS
Instala todas las bibliotecas necesarias para compilar
"""

import subprocess
import sys

def instalar_paquete(paquete):
    """Instala un paquete con pip"""
    print(f"\n📦 Instalando {paquete}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", paquete])
        print(f"✅ {paquete} instalado correctamente")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Error al instalar {paquete}")
        return False

def main():
    """Función principal"""
    print("="*70)
    print("📦 INSTALADOR DE DEPENDENCIAS")
    print("="*70)
    
    print("\nEste script instalará todas las dependencias necesarias para:")
    print("  • Ejecutar los programas (.py)")
    print("  • Compilar los ejecutables (.exe)")
    
    print("\n¿Deseas continuar? (s/n): ", end='')
    respuesta = input().strip().lower()
    
    if respuesta != 's':
        print("\n❌ Instalación cancelada")
        return
    
    # Lista de paquetes necesarios
    paquetes = [
        "pandas",           # Para leer Excel
        "openpyxl",         # Para trabajar con .xlsx
        "qrcode",           # Para generar QR
        "pillow",           # Para imágenes
        "reportlab",        # Para generar PDF
        "requests",         # Para HTTP/API
        "psutil",           # Para monitorear procesos
        "schedule",         # Para tareas programadas
        "pyinstaller",      # Para generar ejecutables
    ]
    
    exitosos = []
    fallidos = []
    
    print("\n" + "="*70)
    print("📥 INSTALANDO PAQUETES")
    print("="*70)
    
    for paquete in paquetes:
        exito = instalar_paquete(paquete)
        if exito:
            exitosos.append(paquete)
        else:
            fallidos.append(paquete)
    
    # Resumen
    print("\n" + "="*70)
    print("📊 RESUMEN DE INSTALACIÓN")
    print("="*70)
    
    if exitosos:
        print(f"\n✅ Instalados correctamente ({len(exitosos)}):")
        for paquete in exitosos:
            print(f"   • {paquete}")
    
    if fallidos:
        print(f"\n❌ Fallidos ({len(fallidos)}):")
        for paquete in fallidos:
            print(f"   • {paquete}")
        print("\n⚠️  Intenta instalarlos manualmente:")
        for paquete in fallidos:
            print(f"   pip install {paquete}")
    
    if not fallidos:
        print("\n🎉 ¡Todas las dependencias instaladas correctamente!")
        print("\n💡 Ahora puedes:")
        print("   1. Ejecutar los programas: python generador_qr_consola.py")
        print("   2. Generar ejecutables: python generar_ejecutables.py")
    
    print("\n" + "="*70)
    input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    main()
