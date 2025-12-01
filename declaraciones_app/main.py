"""
Sistema de Declaraciones
Versión 1.0.0

Aplicación para gestión de documentos notariales con base de datos.
"""

import customtkinter as ctk
import warnings

from ui import MainWindow
from ui.ventana_login import VentanaLogin  # ajusta el import según tu estructura real

# Ignorar advertencias de customtkinter
warnings.filterwarnings("ignore", category=UserWarning, module="customtkinter")


def main():
    """Función principal de la aplicación"""

    # Root SOLO para el login
    root_login = ctk.CTk()
    root_login.withdraw()  # opcional: ocultar esta ventana base

    def on_login_ok(info_usuario):
        # Cuando el login es correcto:
        # 1. Cerrar la raíz del login (con su Toplevel)
        root_login.destroy()

        # 2. Crear y mostrar la ventana principal con el usuario autenticado
        app = MainWindow(info_usuario)
        # app.protocol("WM_DELETE_WINDOW", app.on_closing)  # ya lo configuras dentro de MainWindow
        app.mainloop()

    # Crear la ventana de login (Toplevel sobre root_login)
    VentanaLogin(root_login, on_login_ok)

    # Loop principal SOLO para el login
    root_login.mainloop()


if __name__ == "__main__":
    main()