import ctypes
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import subprocess
import configparser
import socket
import threading

# Asegúrate de tener mysql-connector-python instalado si usas la parte de MySQL
try:
    import mysql.connector
except Exception:
    mysql = None


# =========================
# Estilos y paleta unificados
# =========================
def setup_styles(root):
    COLORS = {
        'primary':   '#2c3e50',
        'secondary': '#34495e',
        'accent':    '#3498db',
        'success':   '#27ae60',
        'warning':   '#f39c12',
        'danger':    '#e74c3c',
        'light':     '#ecf0f1',
        'white':     '#ffffff',
        'text_dark': '#2c3e50',
        'text_light':'#7f8c8d'
    }

    style = ttk.Style(root)
    try:
        style.theme_use('clam')
    except Exception:
        pass

    # Fondo general “light”
    try:
        root.configure(bg=COLORS['light'])
    except Exception:
        pass

    # Tipografía
    style.configure('.', font=('Segoe UI', 9))

    # Frames
    style.configure('Light.TFrame', background=COLORS['light'])
    style.configure('Card.TFrame', background=COLORS['white'], relief='solid', borderwidth=1)

    # Encabezados
    style.configure('Header.TFrame', background=COLORS['primary'])
    style.configure('Header.TLabel', background=COLORS['primary'], foreground=COLORS['white'], font=('Segoe UI', 10, 'bold'))

    # Labels
    style.configure('Light.TLabel', background=COLORS['light'], foreground=COLORS['text_dark'], font=('Segoe UI', 9))
    style.configure('Card.TLabel', background=COLORS['white'], foreground=COLORS['text_dark'], font=('Segoe UI', 9))

    # Botón primario
    style.configure('Primary.TButton',
                    font=('Segoe UI', 9, 'bold'),
                    padding=(10, 5),
                    relief='flat',
                    borderwidth=0,
                    background=COLORS['accent'],
                    foreground=COLORS['white'])
    style.map('Primary.TButton',
              background=[('active', '#2980b9'), ('pressed', '#117a8b')],
              foreground=[('active', '#ffffff'), ('pressed', '#ffffff')])

    # Entradas/combos
    style.configure('TCombobox',
                    fieldbackground=COLORS['white'],
                    background=COLORS['white'],
                    foreground=COLORS['text_dark'])
    style.configure('TEntry',
                    fieldbackground=COLORS['white'],
                    foreground=COLORS['text_dark'])

    root.option_add('*TCombobox*Listbox.background', COLORS['white'])
    root.option_add('*TCombobox*Listbox.foreground', COLORS['text_dark'])
    root.option_add('*TCombobox*Listbox.selectBackground', COLORS['accent'])
    root.option_add('*TCombobox*Listbox.selectForeground', COLORS['white'])
    root.option_add('*TCombobox*Listbox.font', '{Segoe UI} 9')

    # Treeview
    style.configure("Custom.Treeview",
                    background=COLORS['white'],
                    foreground=COLORS['text_dark'],
                    rowheight=20,
                    fieldbackground=COLORS['white'],
                    font=('Segoe UI', 9),
                    borderwidth=1,
                    relief='solid')
    HEADER_BG = '#e5e7eb'
    HEADER_FG = '#111827'
    style.configure("Custom.Treeview.Heading",
                    background=HEADER_BG,
                    foreground=HEADER_FG,
                    font=('Segoe UI', 8, 'bold'),
                    relief='flat',
                    borderwidth=1,
                    padding=(3, 6, 3, 6),
                    anchor='center',
                    justify='center')
    style.map("Custom.Treeview",
              background=[('selected', COLORS['accent'])],
              foreground=[('selected', '#ffffff')])

    # Notebook
    style.configure('TNotebook', background=COLORS['light'], borderwidth=0)
    style.configure('TNotebook.Tab',
                    background=COLORS['light'],
                    foreground=COLORS['text_dark'],
                    font=('Segoe UI', 9))
    style.map('TNotebook.Tab',
              background=[('selected', COLORS['white'])],
              foreground=[('selected', COLORS['text_dark'])])

    return COLORS, style


def crear_script_bat(bind_address, port, max_connections, ruta_bat):
    contenido = f"""@echo off
setlocal enabledelayedexpansion

set CONFIG_FILE="C:\\ProgramData\\MySQL\\MySQL Server 8.0\\my.ini"
set BACKUP_FILE=%CONFIG_FILE%.backup

copy %CONFIG_FILE% %BACKUP_FILE%

powershell -Command "((Get-Content -LiteralPath \\"%CONFIG_FILE%\\") -replace 'bind-address=.*', 'bind-address = {bind_address}') | Set-Content -LiteralPath \\"%CONFIG_FILE%\\""
powershell -Command "((Get-Content -LiteralPath \\"%CONFIG_FILE%\\") -replace 'port=.*', 'port = {port}') | Set-Content -LiteralPath \\"%CONFIG_FILE%\\""
powershell -Command "((Get-Content -LiteralPath \\"%CONFIG_FILE%\\") -replace 'max_connections=.*', 'max_connections = {max_connections}') | Set-Content -LiteralPath \\"%CONFIG_FILE%\\""

echo Configuración actualizada.

echo Reiniciando servicio MySQL...
net stop MySQL80
net start MySQL80

echo Servicio MySQL reiniciado.
pause
"""
    with open(ruta_bat, 'w', encoding='utf-8') as f:
        f.write(contenido)


def ejecutar_bat_con_elevacion(ruta_bat):
    ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", ruta_bat, None, None, 1)
    if ret <= 32:
        print(f"Error al ejecutar el script con elevación, código: {ret}")
        return False
    return True


def es_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def ejecutar_como_admin():
    if es_admin():
        return True  # Ya es admin
    executable = sys.executable
    params = ' '.join([f'"{arg}"' for arg in sys.argv])
    ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, params, None, 1)
    if ret <= 32:
        print(f"Error al pedir elevación, código: {ret}")
        return False
    else:
        return True


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # type: ignore
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class ConfigurarServidor:
    def __init__(self, parent_frame, main_window=None):
        self.parent = parent_frame
        self.main_window = main_window
        self.config_file = "mysql_config.ini"

        self.COLORS, self.style = setup_styles(self.parent.winfo_toplevel())

        self.setup_ui()
        self.cargar_configuracion()

    # Sección "card" con header azul e icono
    def _card_section(self, parent, title, icon):
        container = ttk.Frame(parent, style='Light.TFrame')
        container.pack(fill='x', padx=10, pady=6)

        card = ttk.Frame(container, style='Card.TFrame')
        card.pack(fill='x')

        header = ttk.Frame(card, style='Header.TFrame', height=24)
        header.pack(fill='x')
        header.pack_propagate(False)

        ttk.Label(header, text=f"{icon} {title}", style='Header.TLabel').pack(side='left', padx=10)

        content = ttk.Frame(card, style='Card.TFrame')
        content.pack(fill='x', padx=12, pady=8)

        return content

    def setup_ui(self):
        # Header (título + subtítulo) con el mismo estilo
        container_for_header = getattr(self, 'scrollable_frame', self.parent)

        header_frame = tk.Frame(container_for_header, bg=self.COLORS['primary'], height=55)
        header_frame.pack(fill='x', padx=0, pady=(6, 6))
        header_frame.pack_propagate(False)

        header_inner = tk.Frame(header_frame, bg=self.COLORS['primary'])
        header_inner.pack(fill='both', expand=True, padx=15, pady=4)

        title_label = tk.Label(
            header_inner,
            text="🗄️ Configuración de MySQL para Acceso en Red",
            font=('Segoe UI', 11, 'bold'),
            fg=self.COLORS['white'],
            bg=self.COLORS['primary']
        )
        title_label.pack(anchor='w')

        subtitle_label = tk.Label(
            header_inner,
            text="Configure el servidor MySQL para permitir conexiones remotas",
            font=('Segoe UI', 8),
            fg=self.COLORS['white'],
            bg=self.COLORS['primary']
        )
        subtitle_label.pack(anchor='w', pady=(1, 0))

        # Notebook
        self.notebook = ttk.Notebook(self.parent)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Tabs
        self.config_tab = ttk.Frame(self.notebook, style='Light.TFrame')
        self.users_tab = ttk.Frame(self.notebook, style='Light.TFrame')
        self.status_tab = ttk.Frame(self.notebook, style='Light.TFrame')

        self.notebook.add(self.config_tab, text="⚙️ Configuración Servidor")
        self.notebook.add(self.users_tab, text="👤 Usuarios Remotos")
        self.notebook.add(self.status_tab, text="📊 Estado y Pruebas")

        # Pestañas
        self.setup_config_tab(self.config_tab)
        self.setup_users_tab(self.users_tab)
        self.setup_status_tab(self.status_tab)

    def setup_config_tab(self, tab):
        # Sección Configuración Básica
        basic = self._card_section(tab, "Configuración Básica", "🔧")

        ttk.Label(basic, text="Host/IP del servidor:", style='Card.TLabel').grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.host_var = tk.StringVar(value="localhost")
        ttk.Entry(basic, textvariable=self.host_var, width=20).grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(basic, text="Puerto:", style='Card.TLabel').grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.puerto_var = tk.StringVar(value="3306")
        ttk.Entry(basic, textvariable=self.puerto_var, width=10).grid(row=0, column=3, sticky="w", padx=5, pady=5)

        ttk.Label(basic, text="Usuario Admin:", style='Card.TLabel').grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.admin_user_var = tk.StringVar(value="root")
        ttk.Entry(basic, textvariable=self.admin_user_var, width=20).grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(basic, text="Contraseña Admin:", style='Card.TLabel').grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.admin_pass_var = tk.StringVar()
        ttk.Entry(basic, textvariable=self.admin_pass_var, show="*", width=20).grid(row=1, column=3, sticky="w", padx=5, pady=5)

        # Sección Red
        net = self._card_section(tab, "Configuración de Red", "🌐")

        ttk.Label(net, text="Bind Address:", style='Card.TLabel').grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.bind_address_var = tk.StringVar(value="0.0.0.0")
        self.bind_address_combo = ttk.Combobox(net, textvariable=self.bind_address_var,
                                               values=["0.0.0.0", "127.0.0.1", self.obtener_ip_local()], width=15, state="readonly")
        self.bind_address_combo.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        ttk.Label(net, text="(0.0.0.0 = todas las interfaces)", style='Card.TLabel').grid(row=0, column=2, sticky="w", padx=5, pady=5)

        ttk.Label(net, text="Máx. Conexiones:", style='Card.TLabel').grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.max_connections_var = tk.StringVar(value="100")
        ttk.Entry(net, textvariable=self.max_connections_var, width=10).grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(net, text="Timeout (seg):", style='Card.TLabel').grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.timeout_var = tk.StringVar(value="28800")
        ttk.Entry(net, textvariable=self.timeout_var, width=10).grid(row=1, column=3, sticky="w", padx=5, pady=5)

        # Botones
        btns = ttk.Frame(tab, style='Light.TFrame')
        btns.pack(fill="x", padx=10, pady=5)

        self.test_btn = ttk.Button(btns, text="🔌 Probar Conexión", style="Primary.TButton", command=self.probar_conexion)
        self.test_btn.pack(side="left", padx=5)
        self.apply_btn = ttk.Button(btns, text="💾 Aplicar Configuración", style="Primary.TButton", command=self.aplicar_configuracion)
        self.apply_btn.pack(side="left", padx=5)
        self.restart_btn = ttk.Button(btns, text="🔄 Reiniciar MySQL", style="Primary.TButton", command=self.reiniciar_mysql)
        self.restart_btn.pack(side="left", padx=5)
        self.save_btn = ttk.Button(btns, text="📝 Guardar Config", style="Primary.TButton", command=self.guardar_configuracion)
        self.save_btn.pack(side="left", padx=5)

    def setup_users_tab(self, tab):
        # Header para la pestaña Usuarios
        container_for_header = tab  # el header pertenece a la pestaña
        header_frame = tk.Frame(container_for_header, bg=self.COLORS['primary'], height=55)
        header_frame.pack(fill='x', padx=0, pady=(6, 6))
        header_frame.pack_propagate(False)

        header_inner = tk.Frame(header_frame, bg=self.COLORS['primary'])
        header_inner.pack(fill='both', expand=True, padx=15, pady=4)

        title_label = tk.Label(
            header_inner,
            text="👤 Usuarios Remotos",
            font=('Segoe UI', 11, 'bold'),
            fg=self.COLORS['white'],
            bg=self.COLORS['primary']
        )
        title_label.pack(anchor='w')

        subtitle_label = tk.Label(
            header_inner,
            text="Gestione usuarios y privilegios de acceso remoto",
            font=('Segoe UI', 8),
            fg=self.COLORS['white'],
            bg=self.COLORS['primary']
        )
        subtitle_label.pack(anchor='w', pady=(1, 0))

        # Sección lista de usuarios
        list_frame = self._card_section(tab, "Usuarios con Acceso Remoto", "👤")

        # Tabla
        columns = ("usuario", "host", "privilegios", "activo")

        tree_frame = ttk.Frame(list_frame, style='Card.TFrame')
        tree_frame.pack(fill="both", expand=True, pady=4)

        scroll_y = ttk.Scrollbar(tree_frame, orient="vertical")
        scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal")

        self.users_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set,
            style="Custom.Treeview",
            height=10
        )
        scroll_y.config(command=self.users_tree.yview)
        scroll_x.config(command=self.users_tree.xview)

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.users_tree.pack(fill="both", expand=True)

        for col in columns:
            self.users_tree.heading(col, text=col.replace("_", " ").title(), anchor="center")
            self.users_tree.column(col, width=150, anchor="center")

        # Botones
        btns = ttk.Frame(tab, style='Light.TFrame')
        btns.pack(fill="x", padx=10, pady=5)
        ttk.Button(btns, text="➕ Crear Usuario Remoto", style="Primary.TButton", command=self.crear_usuario_remoto).pack(side="left", padx=5)
        ttk.Button(btns, text="🛂 Modificar Privilegios", style="Primary.TButton", command=self.modificar_privilegios).pack(side="left", padx=5)
        ttk.Button(btns, text="🗑️ Eliminar Usuario", style="Primary.TButton", command=self.eliminar_usuario_remoto).pack(side="left", padx=5)
        ttk.Button(btns, text="🔁 Actualizar Lista", style="Primary.TButton", command=self.cargar_usuarios_remotos).pack(side="left", padx=5)

    def setup_status_tab(self, tab):
        # Header para la pestaña Estado
        container_for_header = tab
        header_frame = tk.Frame(container_for_header, bg=self.COLORS['primary'], height=55)
        header_frame.pack(fill='x', padx=0, pady=(6, 6))
        header_frame.pack_propagate(False)

        header_inner = tk.Frame(header_frame, bg=self.COLORS['primary'])
        header_inner.pack(fill='both', expand=True, padx=15, pady=4)

        title_label = tk.Label(
            header_inner,
            text="📊 Estado y Pruebas",
            font=('Segoe UI', 11, 'bold'),
            fg=self.COLORS['white'],
            bg=self.COLORS['primary']
        )
        title_label.pack(anchor='w')

        subtitle_label = tk.Label(
            header_inner,
            text="Verifique estado del servicio y conexiones",
            font=('Segoe UI', 8),
            fg=self.COLORS['white'],
            bg=self.COLORS['primary']
        )
        subtitle_label.pack(anchor='w', pady=(1, 0))

        # Estado del Servicio
        service_frame = self._card_section(tab, "Estado del Servicio MySQL", "🛰️")
        self.status_label = ttk.Label(service_frame, text="Verificando estado...", style='Card.TLabel')
        self.status_label.pack(pady=6, anchor='w')

        # Información de Conexiones
        conn_frame = self._card_section(tab, "Información de Conexiones", "🔗")
        self.info_text = tk.Text(
            conn_frame,
            height=15,
            width=80,
            bg=self.COLORS['white'],
            fg=self.COLORS['text_dark'],
            relief='flat',
            borderwidth=0,
            highlightthickness=0
        )
        info_scroll = ttk.Scrollbar(conn_frame, orient="vertical", command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=info_scroll.set)
        self.info_text.pack(side="left", fill="both", expand=True, padx=0, pady=0)
        info_scroll.pack(side="right", fill="y")

        # Botones de estado
        btns = ttk.Frame(tab, style='Light.TFrame')
        btns.pack(fill="x", padx=10, pady=5)
        ttk.Button(btns, text="🩺 Verificar Estado", style="Primary.TButton", command=self.verificar_estado).pack(side="left", padx=5)
        ttk.Button(btns, text="🧵 Ver Conexiones Activas", style="Primary.TButton", command=self.ver_conexiones_activas).pack(side="left", padx=5)
        ttk.Button(btns, text="🌍 Probar desde IP Externa", style="Primary.TButton", command=self.probar_ip_externa).pack(side="left", padx=5)
        ttk.Button(btns, text="🪵 Ver Log de Errores", style="Primary.TButton", command=self.ver_log_errores).pack(side="left", padx=5)
        ttk.Button(btns, text="↩️ Volver", style="Primary.TButton", command=self.volver).pack(side="right", padx=5)

    def obtener_ip_local(self):
        try:
            hostname = socket.gethostname()
            ip_local = socket.gethostbyname(hostname)
            return ip_local
        except:
            return "192.168.1.100"

    def probar_conexion(self):
        if mysql is None or mysql.connector is None:
            messagebox.showerror("MySQL", "mysql-connector-python no está disponible.")
            return

        def test_connection():
            try:
                host = self.host_var.get().strip()
                port = int(self.puerto_var.get().strip())
                user = self.admin_user_var.get().strip()
                password = self.admin_pass_var.get()

                if not password:
                    try:
                        self.info_text.insert(tk.END, "❌ Error: Debe ingresar la contraseña del usuario root\n")
                    except Exception:
                        pass
                    messagebox.showerror("Error", "Debe ingresar la contraseña del usuario root")
                    self.test_btn.config(state='normal')
                    return

                try:
                    self.info_text.insert(tk.END, f"Intentando conectar a MySQL en {host}:{port} con usuario {user}\n")
                except Exception:
                    pass

                connection = mysql.connector.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    connection_timeout=10
                )

                cursor = connection.cursor()
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                cursor.close()
                connection.close()

                try:
                    self.info_text.insert(tk.END, f"✅ Conexión exitosa! Versión MySQL: {version}\n")
                except Exception:
                    pass
                messagebox.showinfo("Éxito", f"Conexión exitosa!\nVersión MySQL: {version}")

            except Exception as e:
                try:
                    self.info_text.insert(tk.END, f"❌ Error de conexión: {str(e)}\n")
                except Exception:
                    pass
                messagebox.showerror("Error de Conexión", f"{str(e)}")
            finally:
                self.test_btn.config(state='normal')

        self.test_btn.config(state='disabled')
        threading.Thread(target=test_connection, daemon=True).start()

    def aplicar_configuracion(self):
        if mysql is None or mysql.connector is None:
            messagebox.showerror("MySQL", "mysql-connector-python no está disponible.")
            return
        try:
            host = self.host_var.get()
            port = int(self.puerto_var.get())
            user = self.admin_user_var.get()
            password = self.admin_pass_var.get()
            bind_address = self.bind_address_var.get()
            max_connections = self.max_connections_var.get()
            timeout = self.timeout_var.get()

            connection = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password
            )
            cursor = connection.cursor()

            queries = [
                f"SET GLOBAL max_connections = {max_connections}",
                f"SET GLOBAL wait_timeout = {timeout}",
                f"SET GLOBAL interactive_timeout = {timeout}"
            ]
            for query in queries:
                cursor.execute(query)
                try:
                    self.info_text.insert(tk.END, f"Ejecutado: {query}\n")
                except Exception:
                    pass

            cursor.close()
            connection.close()

            msg = f"""Configuración aplicada parcialmente.

Para aplicar completamente la configuración de red, debe:

1. Editar el archivo my.cnf (o my.ini en Windows)
2. Agregar/modificar estas líneas en [mysqld]:
bind-address = {bind_address}
port = {port}
max_connections = {max_connections}

3. Reiniciar el servicio MySQL

¿Desea que intente localizar y editar el archivo de configuración automáticamente?"""

            if messagebox.askyesno("Configuración", msg):
                self.editar_archivo_configuracion(bind_address, port, max_connections)

            messagebox.showinfo("Éxito", "Variables de configuración aplicadas")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo aplicar la configuración: {str(e)}")

    def editar_archivo_configuracion(self, bind_address, port, max_connections):
        import platform
        if platform.system() != "Windows":
            messagebox.showerror("Error", "Esta función solo está implementada para Windows.")
            return

        ruta_bat = os.path.join(os.path.abspath(os.path.dirname(__file__)), "modificar_mysql.bat")
        crear_script_bat(bind_address, port, max_connections, ruta_bat)

        messagebox.showinfo("Permisos", "Se solicitarán permisos de administrador para modificar el archivo my.ini.")

        if ejecutar_bat_con_elevacion(ruta_bat):
            messagebox.showinfo("Éxito", "Archivo de configuración modificado correctamente.\nRecuerde reiniciar MySQL para aplicar cambios.")
        else:
            messagebox.showerror("Error", "No se pudo ejecutar el script con permisos de administrador.")

    def reiniciar_mysql(self):
        def restart_service():
            try:
                try:
                    self.info_text.insert(tk.END, "Intentando reiniciar el servicio MySQL...\n")
                except Exception:
                    pass
                import platform
                system = platform.system()
                if system == "Linux":
                    commands = [
                        ["sudo", "systemctl", "restart", "mysql"],
                        ["sudo", "service", "mysql", "restart"],
                        ["sudo", "/etc/init.d/mysql", "restart"]
                    ]
                elif system == "Windows":
                    commands = [
                        ["net", "stop", "MySQL80"],
                        ["net", "start", "MySQL80"]
                    ]
                else:
                    commands = [
                        ["brew", "services", "restart", "mysql"]
                    ]

                success = False
                for cmd in commands:
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                        if result.returncode == 0:
                            success = True
                            try:
                                self.info_text.insert(tk.END, f"✅ Comando exitoso: {' '.join(cmd)}\n")
                            except Exception:
                                pass
                            break
                        else:
                            try:
                                self.info_text.insert(tk.END, f"❌ Falló: {' '.join(cmd)} - {result.stderr}\n")
                            except Exception:
                                pass
                    except subprocess.TimeoutExpired:
                        try:
                            self.info_text.insert(tk.END, f"⏱️ Timeout: {' '.join(cmd)}\n")
                        except Exception:
                            pass
                    except Exception as e:
                        try:
                            self.info_text.insert(tk.END, f"❌ Error: {' '.join(cmd)} - {str(e)}\n")
                        except Exception:
                            pass

                if success:
                    messagebox.showinfo("Éxito", "Servicio MySQL reiniciado correctamente")
                else:
                    messagebox.showwarning("Advertencia", "No se pudo reiniciar automáticamente.\nReinicie manualmente el servicio MySQL.")

            except Exception as e:
                error_msg = f"Error al reiniciar MySQL: {str(e)}"
                try:
                    self.info_text.insert(tk.END, f"❌ {error_msg}\n")
                except Exception:
                    pass
                messagebox.showerror("Error", error_msg)

        threading.Thread(target=restart_service, daemon=True).start()

    def crear_usuario_remoto(self):
        if mysql is None or mysql.connector is None:
            messagebox.showerror("MySQL", "mysql-connector-python no está disponible.")
            return

        dialog = UsuarioRemotoDialog(self.parent, "Crear Usuario Remoto", self.COLORS)
        if dialog.result:
            username, password, host, privilegios = dialog.result
            try:
                connection = mysql.connector.connect(
                    host=self.host_var.get(),
                    port=int(self.puerto_var.get()),
                    user=self.admin_user_var.get(),
                    password=self.admin_pass_var.get()
                )

                cursor = connection.cursor()
                cursor.execute(f"CREATE USER '{username}'@'{host}' IDENTIFIED BY '{password}'")
                if privilegios == "ALL":
                    cursor.execute(f"GRANT ALL PRIVILEGES ON *.* TO '{username}'@'{host}' WITH GRANT OPTION")
                else:
                    cursor.execute(f"GRANT {privilegios} ON *.* TO '{username}'@'{host}'")
                cursor.execute("FLUSH PRIVILEGES")
                cursor.close()
                connection.close()

                messagebox.showinfo("Éxito", f"Usuario '{username}@{host}' creado correctamente")
                self.cargar_usuarios_remotos()

            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear el usuario: {str(e)}")

    def cargar_usuarios_remotos(self):
        if mysql is None or mysql.connector is None:
            messagebox.showerror("MySQL", "mysql-connector-python no está disponible.")
            return
        try:
            for row in self.users_tree.get_children():
                self.users_tree.delete(row)

            connection = mysql.connector.connect(
                host=self.host_var.get(),
                port=int(self.puerto_var.get()),
                user=self.admin_user_var.get(),
                password=self.admin_pass_var.get(),
                database="mysql"
            )

            cursor = connection.cursor()
            cursor.execute("""
                SELECT User, Host, 
                    IF(Select_priv='Y' AND Insert_priv='Y' AND Update_priv='Y' AND Delete_priv='Y', 'FULL', 'LIMITED') as Privilegios,
                    IF(account_locked='N', 'Sí', 'No') as Activo
                FROM user 
                WHERE Host != 'localhost' AND Host != '127.0.0.1'
                ORDER BY User, Host
            """)
            usuarios = cursor.fetchall()
            for usuario in usuarios:
                self.users_tree.insert("", "end", values=usuario)

            cursor.close()
            connection.close()
            try:
                self.info_text.insert(tk.END, f"Lista de usuarios actualizada: {len(usuarios)} usuarios remotos\n")
            except Exception:
                pass

        except Exception as e:
            try:
                self.info_text.insert(tk.END, f"❌ Error al cargar usuarios: {str(e)}\n")
            except Exception:
                pass

    def verificar_estado(self):
        if mysql is None or mysql.connector is None:
            messagebox.showerror("MySQL", "mysql-connector-python no está disponible.")
            return

        def check_status():
            try:
                try:
                    self.info_text.delete(1.0, tk.END)
                except Exception:
                    pass
                connection = mysql.connector.connect(
                    host=self.host_var.get(),
                    port=int(self.puerto_var.get()),
                    user=self.admin_user_var.get(),
                    password=self.admin_pass_var.get()
                )
                cursor = connection.cursor()
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                try:
                    self.info_text.insert(tk.END, f"🔄 Estado del Servidor MySQL\n")
                    self.info_text.insert(tk.END, f"✅ Servidor ACTIVO\n")
                    self.info_text.insert(tk.END, f"📊 Versión: {version}\n\n")
                except Exception:
                    pass

                variables = ['max_connections', 'port', 'bind_address', 'wait_timeout', 'interactive_timeout']
                try:
                    self.info_text.insert(tk.END, "🔧 Configuración Actual:\n")
                except Exception:
                    pass
                for var in variables:
                    cursor.execute(f"SHOW VARIABLES LIKE '{var}'")
                    result = cursor.fetchone()
                    if result:
                        try:
                            self.info_text.insert(tk.END, f"  • {var}: {result[1]}\n")
                        except Exception:
                            pass

                try:
                    self.info_text.insert(tk.END, "\n📈 Estadísticas de Conexión:\n")
                except Exception:
                    pass
                status_vars = ['Threads_connected', 'Connections', 'Max_used_connections']
                for var in status_vars:
                    cursor.execute(f"SHOW STATUS LIKE '{var}'")
                    result = cursor.fetchone()
                    if result:
                        try:
                            self.info_text.insert(tk.END, f"  • {var}: {result[1]}\n")
                        except Exception:
                            pass

                cursor.close()
                connection.close()
                self.status_label.config(text="✅ MySQL Server ACTIVO")

            except Exception as e:
                try:
                    self.info_text.insert(tk.END, f"❌ Error: {str(e)}\n")
                except Exception:
                    pass
                self.status_label.config(text="❌ MySQL Server NO DISPONIBLE")

        threading.Thread(target=check_status, daemon=True).start()

    def ver_conexiones_activas(self):
        if mysql is None or mysql.connector is None:
            messagebox.showerror("MySQL", "mysql-connector-python no está disponible.")
            return
        try:
            connection = mysql.connector.connect(
                host=self.host_var.get(),
                port=int(self.puerto_var.get()),
                user=self.admin_user_var.get(),
                password=self.admin_pass_var.get()
            )
            cursor = connection.cursor()
            cursor.execute("SHOW PROCESSLIST")
            procesos = cursor.fetchall()

            try:
                self.info_text.insert(tk.END, f"\n🔗 Conexiones Activas ({len(procesos)}):\n")
                self.info_text.insert(tk.END, "-" * 80 + "\n")
                self.info_text.insert(tk.END, f"{'ID':<8}{'Usuario':<15}{'Host':<25}{'DB':<15}{'Estado':<15}\n")
                self.info_text.insert(tk.END, "-" * 80 + "\n")
            except Exception:
                pass

            for proceso in procesos:
                id_proc = proceso[0] or 0
                user = proceso[1] or "N/A"
                host = proceso[2] or "N/A"
                db = proceso[3] or "N/A"
                state = proceso[4] or "N/A"
                try:
                    self.info_text.insert(tk.END, f"{id_proc:<8}{user:<15}{host:<25}{db:<15}{state:<15}\n")
                except Exception:
                    pass

            cursor.close()
            connection.close()

        except Exception as e:
            try:
                self.info_text.insert(tk.END, f"❌ Error al obtener conexiones: {str(e)}\n")
            except Exception:
                pass

    def probar_ip_externa(self):
        ip_externa = simpledialog.askstring("Prueba IP Externa", "Ingrese la IP desde la cual probar la conexión:")
        if ip_externa:
            usuario_prueba = simpledialog.askstring("Usuario de Prueba", "Usuario para la prueba:")
            if usuario_prueba:
                password_prueba = simpledialog.askstring("Contraseña", "Contraseña:", show="*")
                if password_prueba:
                    try:
                        self.info_text.insert(tk.END, f"\n🌍 Simulando conexión desde {ip_externa}...\n")
                        self.info_text.insert(tk.END, f"Usuario: {usuario_prueba}\n")
                        self.info_text.insert(tk.END, f"⚠️  Nota: Esta es una simulación local.\n")
                        self.info_text.insert(tk.END, f"Para una prueba real, ejecute desde {ip_externa}:\n")
                        self.info_text.insert(tk.END, f"mysql -h {self.host_var.get()} -P {self.puerto_var.get()} -u {usuario_prueba} -p\n\n")
                    except Exception:
                        pass

    def ver_log_errores(self):
        if mysql is None or mysql.connector is None:
            messagebox.showerror("MySQL", "mysql-connector-python no está disponible.")
            return

        def show_log():
            try:
                connection = mysql.connector.connect(
                    host=self.host_var.get(),
                    port=int(self.puerto_var.get()),
                    user=self.admin_user_var.get(),
                    password=self.admin_pass_var.get()
                )
                cursor = connection.cursor()
                cursor.execute("SHOW VARIABLES LIKE 'log_error'")
                result = cursor.fetchone()
                if result and result[1]:
                    log_path = result[1]
                    try:
                        self.info_text.insert(tk.END, f"\n📋 Log de Errores: {log_path}\n")
                        self.info_text.insert(tk.END, "-" * 80 + "\n")
                    except Exception:
                        pass
                    try:
                        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            for line in lines[-20:]:
                                try:
                                    self.info_text.insert(tk.END, line)
                                except Exception:
                                    pass
                    except Exception as e:
                        try:
                            self.info_text.insert(tk.END, f"No se puede leer el archivo: {str(e)}\n")
                            self.info_text.insert(tk.END, f"Archivo ubicado en: {log_path}\n")
                        except Exception:
                            pass
                else:
                    try:
                        self.info_text.insert(tk.END, "\n📋 Log de errores no configurado o no disponible\n")
                    except Exception:
                        pass

                cursor.close()
                connection.close()
            except Exception as e:
                try:
                    self.info_text.insert(tk.END, f"❌ Error al acceder al log: {str(e)}\n")
                except Exception:
                    pass

        threading.Thread(target=show_log, daemon=True).start()

    def modificar_privilegios(self):
        selected = getattr(self, 'users_tree', None).selection()
        if not selected:
            messagebox.showwarning("Seleccione", "Seleccione un usuario para modificar")
            return
        item = self.users_tree.item(selected[0])["values"]
        usuario, host = item[0], item[1]
        dialog = PrivilegiosDialog(self.parent, f"Privilegios para {usuario}@{host}", self.COLORS)
        if dialog.result:
            nuevos_privilegios = dialog.result
            if mysql is None or mysql.connector is None:
                messagebox.showerror("MySQL", "mysql-connector-python no está disponible.")
                return
            try:
                connection = mysql.connector.connect(
                    host=self.host_var.get(),
                    port=int(self.puerto_var.get()),
                    user=self.admin_user_var.get(),
                    password=self.admin_pass_var.get()
                )
                cursor = connection.cursor()
                cursor.execute(f"REVOKE ALL PRIVILEGES ON *.* FROM '{usuario}'@'{host}'")
                if nuevos_privilegios == "ALL":
                    cursor.execute(f"GRANT ALL PRIVILEGES ON *.* TO '{usuario}'@'{host}' WITH GRANT OPTION")
                else:
                    cursor.execute(f"GRANT {nuevos_privilegios} ON *.* TO '{usuario}'@'{host}'")
                cursor.execute("FLUSH PRIVILEGES")
                cursor.close()
                connection.close()
                messagebox.showinfo("Éxito", f"Privilegios actualizados para {usuario}@{host}")
                self.cargar_usuarios_remotos()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudieron modificar los privilegios: {str(e)}")

    def eliminar_usuario_remoto(self):
        selected = getattr(self, 'users_tree', None).selection()
        if not selected:
            messagebox.showwarning("Seleccione", "Seleccione un usuario para eliminar")
            return
        item = self.users_tree.item(selected[0])["values"]
        usuario, host = item[0], item[1]
        if messagebox.askyesno("Confirmar", f"¿Eliminar el usuario '{usuario}@{host}'?"):
            if mysql is None or mysql.connector is None:
                messagebox.showerror("MySQL", "mysql-connector-python no está disponible.")
                return
            try:
                connection = mysql.connector.connect(
                    host=self.host_var.get(),
                    port=int(self.puerto_var.get()),
                    user=self.admin_user_var.get(),
                    password=self.admin_pass_var.get()
                )
                cursor = connection.cursor()
                cursor.execute(f"DROP USER '{usuario}'@'{host}'")
                cursor.execute("FLUSH PRIVILEGES")
                cursor.close()
                connection.close()
                messagebox.showinfo("Éxito", f"Usuario {usuario}@{host} eliminado correctamente")
                self.cargar_usuarios_remotos()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el usuario: {str(e)}")

    def guardar_configuracion(self):
        config = configparser.ConfigParser()
        config['MySQL'] = {
            'host': self.host_var.get(),
            'port': self.puerto_var.get(),
            'admin_user': self.admin_user_var.get(),
            'admin_pass': self.admin_pass_var.get(),
            'bind_address': self.bind_address_var.get(),
            'max_connections': self.max_connections_var.get(),
            'timeout': self.timeout_var.get()
        }
        try:
            with open(self.config_file, 'w') as f:
                config.write(f)
            messagebox.showinfo("Éxito", f"Configuración guardada en {self.config_file}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la configuración: {str(e)}")

    def cargar_configuracion(self):
        if os.path.exists(self.config_file):
            try:
                config = configparser.ConfigParser()
                config.read(self.config_file)
                if 'MySQL' in config:
                    mysql_config = config['MySQL']
                    self.host_var.set(mysql_config.get('host', 'localhost'))
                    self.puerto_var.set(mysql_config.get('port', '3306'))
                    self.admin_user_var.set(mysql_config.get('admin_user', 'root'))
                    self.admin_pass_var.set(mysql_config.get('admin_pass', ''))
                    self.bind_address_var.set(mysql_config.get('bind_address', '0.0.0.0'))
                    self.max_connections_var.set(mysql_config.get('max_connections', '100'))
                    self.timeout_var.set(mysql_config.get('timeout', '28800'))
            except Exception:
                pass

    def volver(self):
        if self.main_window:
            self.main_window.show_welcome_screen()


class UsuarioRemotoDialog(tk.Toplevel):
    def __init__(self, parent, title, COLORS):
        super().__init__(parent)
        self.title(title)
        self.result = None
        self.COLORS = COLORS
        self.configure(bg=self.COLORS['light'])
        self.transient(parent)
        self.grab_set()

        # Header
        header = ttk.Frame(self, style='Header.TFrame', height=40)
        header.pack(fill='x')
        header.pack_propagate(False)
        ttk.Label(header, text=f"👤 {title}", style='Header.TLabel').pack(side='left', padx=10, pady=6)

        # Contenido
        content = ttk.Frame(self, style='Card.TFrame', padding=12)
        content.pack(fill='both', expand=True, padx=12, pady=12)

        ttk.Label(content, text="Nombre de usuario:", style='Card.TLabel').grid(row=0, column=0, sticky="w", pady=5)
        self.username_var = tk.StringVar()
        ttk.Entry(content, textvariable=self.username_var, width=30).grid(row=0, column=1, sticky="ew", pady=5, padx=(5,0))

        ttk.Label(content, text="Contraseña:", style='Card.TLabel').grid(row=1, column=0, sticky="w", pady=5)
        self.password_var = tk.StringVar()
        ttk.Entry(content, textvariable=self.password_var, show="*", width=30).grid(row=1, column=1, sticky="ew", pady=5, padx=(5,0))

        ttk.Label(content, text="Host permitido:", style='Card.TLabel').grid(row=2, column=0, sticky="w", pady=5)
        self.host_var = tk.StringVar(value="%")
        ttk.Combobox(content, textvariable=self.host_var, values=["%", "192.168.1.%", "10.0.0.%", "172.16.0.%"], width=28, state="readonly").grid(row=2, column=1, sticky="ew", pady=5, padx=(5,0))

        ttk.Label(content, text="(% = cualquier IP, 192.168.1.% = subnet específica)", style='Card.TLabel').grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 10))

        ttk.Label(content, text="Privilegios:", style='Card.TLabel').grid(row=4, column=0, sticky="w", pady=5)
        self.privilegios_var = tk.StringVar(value="SELECT,INSERT,UPDATE,DELETE")
        ttk.Combobox(content, textvariable=self.privilegios_var,
                     values=[
                         "SELECT,INSERT,UPDATE,DELETE",
                         "SELECT",
                         "ALL",
                         "SELECT,INSERT,UPDATE,DELETE,CREATE,DROP,ALTER"
                     ], width=28, state="readonly").grid(row=4, column=1, sticky="ew", pady=5, padx=(5,0))

        content.grid_columnconfigure(1, weight=1)

        btns = ttk.Frame(self, style='Light.TFrame')
        btns.pack(fill='x', pady=(0, 12))
        ttk.Button(btns, text="✔️ Aceptar", style='Primary.TButton', command=self.aceptar).pack(side="left", padx=6)
        ttk.Button(btns, text="✖️ Cancelar", style='Primary.TButton', command=self.cancelar).pack(side="left", padx=6)

        self.update_idletasks()
        w, h = 420, 260
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def aceptar(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()
        host = self.host_var.get().strip()
        privilegios = self.privilegios_var.get()
        if not username or not password or not host:
            messagebox.showerror("Error", "Todos los campos son obligatorios")
            return
        self.result = (username, password, host, privilegios)
        self.destroy()

    def cancelar(self):
        self.result = None
        self.destroy()


class PrivilegiosDialog(tk.Toplevel):
    def __init__(self, parent, title, COLORS):
        super().__init__(parent)
        self.title(title)
        self.result = None
        self.COLORS = COLORS
        self.configure(bg=self.COLORS['light'])
        self.transient(parent)
        self.grab_set()

        header = ttk.Frame(self, style='Header.TFrame', height=40)
        header.pack(fill='x')
        header.pack_propagate(False)
        ttk.Label(header, text=f"🛂 {title}", style='Header.TLabel').pack(side='left', padx=10, pady=6)

        content = ttk.Frame(self, style='Card.TFrame', padding=12)
        content.pack(fill='both', expand=True, padx=12, pady=12)

        ttk.Label(content, text="Seleccione los privilegios a otorgar:", style='Card.TLabel').pack(anchor="w", pady=(0, 8))

        # Checkboxes
        self.vars = {}
        options = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'INDEX', 'GRANT']
        grid = ttk.Frame(content, style='Card.TFrame')
        grid.pack(fill='x', pady=5)
        for i, name in enumerate(options):
            var = tk.BooleanVar(value=(name in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']))
            self.vars[name] = var
            ttk.Checkbutton(grid, text=name, variable=var).grid(row=i//3, column=i%3, padx=8, pady=2, sticky="w")

        self.all_privs = tk.BooleanVar(value=False)
        ttk.Checkbutton(content, text="Otorgar TODOS los privilegios (ALL)", variable=self.all_privs,
                        command=self.toggle_all).pack(anchor="w", pady=(8, 0))

        btns = ttk.Frame(self, style='Light.TFrame')
        btns.pack(fill='x', pady=(8, 12))
        ttk.Button(btns, text="✔️ Aceptar", style='Primary.TButton', command=self.aceptar).pack(side="left", padx=6)
        ttk.Button(btns, text="✖️ Cancelar", style='Primary.TButton', command=self.cancelar).pack(side="left", padx=6)

        self.update_idletasks()
        w, h = 420, 300
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def toggle_all(self):
        enabled = not self.all_privs.get()
        if not enabled:
            for var in self.vars.values():
                var.set(False)

    def aceptar(self):
        if self.all_privs.get():
            self.result = "ALL"
        else:
            selected = [name for name, var in self.vars.items() if var.get()]
            if not selected:
                messagebox.showerror("Error", "Debe seleccionar al menos un privilegio")
                return
            self.result = ",".join(selected)
        self.destroy()

    def cancelar(self):
        self.result = None
        self.destroy()


# Ejemplo de uso
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Configurador MySQL Red")
    root.geometry("1000x740")

    setup_styles(root)

    app = ConfigurarServidor(root)
    root.mainloop()