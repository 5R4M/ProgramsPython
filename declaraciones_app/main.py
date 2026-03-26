import sys
import io
# Ahora sí, imports normales
import customtkinter as ctk
import warnings

from ui import MainWindow
from ui.ventana_login import VentanaLogin  # ajusta si tu paquete es distinto

# ===== CONFIGURACIÓN CRÍTICA PARA EJECUTABLES =====
# DEBE estar ANTES de cualquier otro import
# Previene el error "NoneType has no attribute write" en ejecutables

def setup_streams():
    """Configura streams seguros para el ejecutable sin consola"""
    # Verificar si estamos en un ejecutable empaquetado
    if getattr(sys, 'frozen', False):
        # Crear streams dummy seguros si son None
        if sys.stdout is None:
            sys.stdout = io.StringIO()
        if sys.stderr is None:
            sys.stderr = io.StringIO()
        if sys.stdin is None:
            sys.stdin = io.StringIO()
    else:
        # En desarrollo, también proteger por si acaso
        if sys.stdout is None:
            sys.stdout = sys.__stdout__ if sys.__stdout__ else io.StringIO()
        if sys.stderr is None:
            sys.stderr = sys.__stderr__ if sys.__stderr__ else io.StringIO()
        if sys.stdin is None:
            sys.stdin = sys.__stdin__ if sys.__stdin__ else io.StringIO()

# Ejecutar configuración INMEDIATAMENTE
setup_streams()

# ===== FIN DE CONFIGURACIÓN CRÍTICA =====

warnings.filterwarnings("ignore", category=UserWarning, module="customtkinter")


def main():
    # Estilo global
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # Root para LOGIN
    root_login = ctk.CTk()
    root_login.title("Sistema de Declaraciones - Inicio de sesión")
    
    # Variable para guardar el usuario autenticado
    usuario_autenticado = {"data": None}

    def on_login_ok(info_usuario):
        usuario_autenticado["data"] = info_usuario
        # quit() detiene el mainloop limpiamente sin destruir la ventana todavía.
        # Esto evita que los callbacks "after" internos de customtkinter
        # (update, check_dpi_scaling) se disparen sobre widgets ya destruidos.
        root_login.quit()

    # Construir UI de login sobre root_login
    VentanaLogin(root_login, on_login_ok)

    # Loop SOLO del login
    root_login.mainloop()
    # Destruir DESPUÉS de que el mainloop haya salido completamente
    root_login.destroy()

    # Si se autenticó, abrir ventana principal
    if usuario_autenticado["data"] is not None:
        app = MainWindow(usuario_autenticado["data"])
        app.mainloop()


if __name__ == "__main__":
    main()