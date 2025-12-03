import customtkinter as ctk
import warnings

from ui import MainWindow
from ui.ventana_login import VentanaLogin  # ajusta si tu paquete es distinto

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

        # Cancelar afters internos del root_login antes de destruirlo
        try:
            afters = root_login.tk.call("after", "info")
            if afters:
                for aid in str(afters).split():
                    try:
                        root_login.after_cancel(aid)
                    except Exception:
                        pass
        except Exception:
            pass

        root_login.destroy()

    # Construir UI de login sobre root_login
    VentanaLogin(root_login, on_login_ok)

    # Loop SOLO del login
    root_login.mainloop()

    # Si se autenticó, abrir ventana principal
    if usuario_autenticado["data"] is not None:
        app = MainWindow(usuario_autenticado["data"])
        app.mainloop()


if __name__ == "__main__":
    main()