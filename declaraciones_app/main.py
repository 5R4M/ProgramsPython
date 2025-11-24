"""
Sistema de Declaraciones
Versión 1.0.0

Aplicación para gestión de documentos notariales con base de datos.
"""

from ui import MainWindow
import warnings

# Ignorar advertencias de customtkinter
warnings.filterwarnings("ignore", category=UserWarning, module="customtkinter")

def main():
    """Función principal de la aplicación"""
    app = MainWindow()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()

if __name__ == "__main__":
    main()