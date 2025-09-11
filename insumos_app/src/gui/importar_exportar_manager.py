import os
import sys
import json
import configparser
from datetime import datetime
from tkinter import messagebox, filedialog
import tkinter as tk
from tkinter import ttk

import pandas as pd
import mysql.connector


def get_config_path(filename):
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        return os.path.join(exe_dir, filename)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)


def get_mysql_conn():
    ini = get_config_path("mysql_config.ini")
    cfg = {'host': 'DESKTOP-KVJ8QQ3', 'port': 3306, 'user': 'root', 'password': '', 'database': 'insumos'}
    p = configparser.ConfigParser()
    p.read(ini, encoding='utf-8')
    if 'MySQL' in p:
        s = p['MySQL']
        cfg['host'] = s.get('host', cfg['host'])
        cfg['port'] = int(s.get('port', cfg['port']))
        cfg['user'] = s.get('admin_user', cfg['user'])
        cfg['password'] = s.get('admin_pass', cfg['password'])
        cfg['database'] = s.get('database', cfg['database'])
    return mysql.connector.connect(**cfg)


# ===== Estilos y paleta (unificados con Configurar Servidor) =====
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

    try:
        root.configure(bg=COLORS['light'])
    except Exception:
        pass

    style.configure('.', font=('Segoe UI', 9))

    style.configure('Light.TFrame', background=COLORS['light'])
    style.configure('Card.TFrame', background=COLORS['white'], relief='solid', borderwidth=1)

    style.configure('Header.TFrame', background=COLORS['primary'])
    style.configure('Header.TLabel', background=COLORS['primary'], foreground=COLORS['white'], font=('Segoe UI', 10, 'bold'))

    style.configure('Light.TLabel', background=COLORS['light'], foreground=COLORS['text_dark'], font=('Segoe UI', 9))
    style.configure('Card.TLabel', background=COLORS['white'], foreground=COLORS['text_dark'], font=('Segoe UI', 9))

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

    style.configure('TNotebook', background=COLORS['light'], borderwidth=0)
    style.configure('TNotebook.Tab',
                    background=COLORS['light'],
                    foreground=COLORS['text_dark'],
                    font=('Segoe UI', 9))
    style.map('TNotebook.Tab',
              background=[('selected', COLORS['white'])],
              foreground=[('selected', COLORS['text_dark'])])

    return COLORS, style


class ImportarExportarManager:
    """Clase para manejar importación y exportación de datos de la base de datos MySQL"""

    def __init__(self, parent_frame, main_window):
        self.parent_frame = parent_frame
        self.main_window = main_window

        # Estilos/paleta
        self.COLORS, self._style = setup_styles(self.parent_frame.winfo_toplevel())

        # Definir las tablas y su orden de dependencias
        self.tablas_orden = [
            'area',
            'distrito',
            'tipo_servicio',
            'servicio',
            'tipo_insumo',
            'presentacion',
            'insumo',
            'insumo_presentacion',
            'tipo_movimiento',
            'movimiento',
            'usuarios'
        ]

        # Mapeo de tablas con sus columnas principales
        self.estructura_tablas = {
            'area': ['id', 'nombre'],
            'distrito': ['id', 'nombre', 'id_area'],
            'tipo_servicio': ['id', 'id_distrito', 'descripcion'],
            'servicio': ['id', 'id_tipo_servicio', 'nombre'],
            'tipo_insumo': ['id', 'descripcion'],
            'presentacion': ['id', 'nombre'],
            'insumo': ['id', 'nombre', 'lote', 'fecha_vencimiento', 'id_tipo_insumo'],
            'insumo_presentacion': ['insumo_id', 'presentacion_id'],
            'tipo_movimiento': ['id', 'descripcion'],
            'movimiento': [
                'id', 'fecha_registro', 'referencia', 'tipo_movimiento_id',
                'area_id', 'distrito_id', 'servicio_id', 'insumo_id',
                'presentacion_id', 'lote', 'fecha_vencimiento', 'cantidad',
                'observaciones', 'salida_distrito_id', 'salida_servicio_id'
            ],
            'usuarios': ['id', 'username', 'password', 'nombre_completo', 'rol', 'activo', 'fecha_creacion']
        }

        self.crear_interfaz()

    # Card con header azul e icono como en Configurar Servidor
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

    # Header superior (título + subtítulo) solicitado
    def _header_title_sub(self, parent, title_text, subtitle_text):
        header_frame = tk.Frame(parent, bg=self.COLORS['primary'], height=55)
        header_frame.pack(fill='x', padx=0, pady=(6, 6))
        header_frame.pack_propagate(False)

        header_inner = tk.Frame(header_frame, bg=self.COLORS['primary'])
        header_inner.pack(fill='both', expand=True, padx=15, pady=4)

        title_label = tk.Label(header_inner,
                               text=title_text,
                               font=('Segoe UI', 11, 'bold'),
                               fg=self.COLORS['white'],
                               bg=self.COLORS['primary'])
        title_label.pack(anchor='w')

        subtitle_label = tk.Label(header_inner,
                                  text=subtitle_text,
                                  font=('Segoe UI', 8),
                                  fg=self.COLORS['white'],
                                  bg=self.COLORS['primary'])
        subtitle_label.pack(anchor='w', pady=(1, 0))

    def crear_interfaz(self):
        """Crea la interfaz integrada en el panel principal"""
        main_frame = ttk.Frame(self.parent_frame, style='Light.TFrame')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Header de la vista general
        self._header_title_sub(
            main_frame,
            "🗄️ Gestión de Importación y Exportación de Datos",
            "Administre los respaldos y transferencias de datos del sistema"
        )

        # Notebook con estilo light
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True, pady=5)

        self.crear_pestana_backup()
        self.crear_pestana_tablas()

    def _make_scrollable(self, parent):
        """Crea un contenedor scrollable que respeta paleta y devuelve (canvas, scrollable_frame)."""
        outer = ttk.Frame(parent, style='Light.TFrame')
        outer.pack(fill='both', expand=True)

        # Canvas con fondo light
        canvas = tk.Canvas(outer, bg=self.COLORS['light'], highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        # Frame interior con estilo Light
        scrollable_frame = ttk.Frame(canvas, style='Light.TFrame')
        scrollable_frame_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Ajustar ancho del frame interior al canvas
            canvas_width = event.width
            canvas.itemconfig(scrollable_frame_id, width=canvas_width)

        def _on_canvas_configure(event):
            # Mantener ancho del contenido igual al canvas
            canvas.itemconfig(scrollable_frame_id, width=event.width)

        scrollable_frame.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        return scrollable_frame

    def crear_pestana_backup(self):
        frame_backup = ttk.Frame(self.notebook, style='Light.TFrame')
        self.notebook.add(frame_backup, text="🗄️ Backup Completo")

        # Header de pestaña
        self._header_title_sub(
            frame_backup,
            "🗄️ Backup Completo",
            "Cree y restaure respaldos completos del sistema"
        )

        scrollable = self._make_scrollable(frame_backup)

        # Exportación
        export_frame = self._card_section(scrollable, "📤 Exportación de Backup", "📤")
        ttk.Label(export_frame,
                  text="Crear un archivo de respaldo con todos los datos del sistema",
                  style='Card.TLabel').pack(anchor='w', pady=(0, 10))
        ttk.Button(export_frame,
                   text="🗄️ Exportar Backup Completo",
                   style='Primary.TButton',
                   command=self.exportar_datos_completos).pack(anchor='w')

        # Importación
        import_frame = self._card_section(scrollable, "📥 Importación de Backup", "📥")
        ttk.Label(import_frame,
                  text="Restaurar datos desde un archivo de respaldo",
                  style='Card.TLabel').pack(anchor='w', pady=(0, 10))

        button_frame = ttk.Frame(import_frame, style='Card.TFrame')
        button_frame.pack(fill='x')
        ttk.Button(button_frame, text="📥 Importar (Mantener Datos)",
                   style='Primary.TButton',
                   command=lambda: self.importar_datos_completos(limpiar_antes=False)).pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="⚠️ Importar (Reemplazar Todo)",
                   style='Primary.TButton',
                   command=lambda: self.importar_datos_completos(limpiar_antes=True)).pack(side='left')

        # Información Importante
        warning_frame = self._card_section(scrollable, "⚠️ Información Importante", "⚠️")
        warning_text = (
            "• Mantener Datos: Agrega/actualiza registros sin eliminar datos existentes\n"
            "• Reemplazar Todo: ELIMINA todos los datos actuales antes de importar\n"
            "• Siempre haga un backup antes de importar datos importantes\n"
            "• Los archivos de backup incluyen información sensible (usuarios y contraseñas)\n"
            "• El proceso puede tomar varios minutos dependiendo del tamaño de los datos"
        )
        ttk.Label(warning_frame, text=warning_text, style='Card.TLabel',
                  justify='left').pack(anchor='nw', fill='both', expand=True)

    def crear_pestana_tablas(self):
        frame_tablas = ttk.Frame(self.notebook, style='Light.TFrame')
        self.notebook.add(frame_tablas, text="📊 Tablas Individuales")

        # Header de pestaña
        self._header_title_sub(
            frame_tablas,
            "📊 Tablas Individuales",
            "Exportar/Importar datos por tabla"
        )

        scrollable = self._make_scrollable(frame_tablas)

        # Selección de tabla
        selection_frame = self._card_section(scrollable, "🎯 Selección de Tabla", "🎯")
        ttk.Label(selection_frame, text="Seleccionar tabla para exportar/importar:",
                  style='Card.TLabel').pack(anchor='w', pady=(0, 8))

        self.combo_tabla = ttk.Combobox(selection_frame, values=self.tablas_orden,
                                        state="readonly", width=30)
        self.combo_tabla.pack(fill='x', pady=(0, 10))
        self.combo_tabla.set(self.tablas_orden[0])

        action_frame = ttk.Frame(selection_frame, style='Card.TFrame')
        action_frame.pack(fill='x')
        ttk.Button(action_frame, text="📤 Exportar a Excel",
                   style='Primary.TButton', command=self.exportar_tabla_seleccionada).pack(side='left', padx=(0, 10))
        ttk.Button(action_frame, text="📥 Importar desde Excel/CSV",
                   style='Primary.TButton', command=self.importar_tabla_seleccionada).pack(side='left')

        # Información de Tablas
        info_tablas_frame = self._card_section(scrollable, "ℹ️ Información de Tablas", "ℹ️")
        info_tablas_text = (
            "Descripción de las principales tablas del sistema:\n\n"
            "• area, distrito, tipo_servicio, servicio, tipo_insumo, presentacion, insumo, movimiento, usuarios\n"
            "Formatos soportados: Excel (.xlsx), CSV (.csv), JSON (.json)"
        )
        ttk.Label(info_tablas_frame, text=info_tablas_text, style='Card.TLabel',
                  justify='left').pack(anchor='nw', fill='both', expand=True)

    def exportar_datos_completos(self, ruta_archivo=None):
        try:
            if not ruta_archivo:
                nombre_archivo = f"backup_completo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                ruta_archivo = filedialog.asksaveasfilename(
                    title="Guardar exportación completa",
                    defaultextension=".json",
                    filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")],
                    initialfile=nombre_archivo
                )
            if not ruta_archivo:
                return False

            conn = get_mysql_conn()
            cur = conn.cursor()
            database_name = conn.database

            datos_exportacion = {
                'metadata': {
                    'fecha_exportacion': datetime.now().isoformat(),
                    'version': '1.0',
                    'tipo': 'backup_completo'
                },
                'datos': {}
            }
            total = 0

            for tabla in self.tablas_orden:
                try:
                    cur.execute(
                        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=%s AND table_name=%s",
                        (database_name, tabla)
                    )
                    if cur.fetchone()[0] == 0:
                        datos_exportacion['datos'][tabla] = []
                        continue

                    cur.execute(f"SELECT * FROM `{tabla}`")
                    cols = [d[0] for d in cur.description]
                    filas = cur.fetchall()
                    registros = [dict(zip(cols, fila)) for fila in filas]
                    datos_exportacion['datos'][tabla] = registros
                    total += len(registros)
                    print(f"Exportada {tabla}: {len(registros)} registros")
                except Exception as e:
                    print(f"Error exportando {tabla}: {e}")
                    datos_exportacion['datos'][tabla] = []

            cur.close()
            conn.close()

            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                json.dump(datos_exportacion, f, indent=2, ensure_ascii=False, default=str)

            messagebox.showinfo(
                "Exportación Exitosa",
                f"Datos exportados correctamente:\n\nArchivo: {os.path.basename(ruta_archivo)}\nTotal de registros: {total}"
            )
            return True

        except Exception as e:
            messagebox.showerror("Error de Exportación", f"{e}")
            return False

    def importar_datos_completos(self, ruta_archivo=None, limpiar_antes=False):
        try:
            if not ruta_archivo:
                ruta_archivo = filedialog.askopenfilename(
                    title="Seleccionar archivo de importación",
                    filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
                )
            if not ruta_archivo:
                return False

            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                datos = json.load(f)
            if 'datos' not in datos:
                messagebox.showerror("Error", "Formato inválido")
                return False

            conn = get_mysql_conn()
            cur = conn.cursor()
            cur.execute("SET FOREIGN_KEY_CHECKS=0")

            try:
                if limpiar_antes:
                    if not messagebox.askyesno(
                        "Confirmación",
                        "Esto eliminará TODOS los datos actuales antes de importar. ¿Continuar?"
                    ):
                        cur.execute("SET FOREIGN_KEY_CHECKS=1")
                        cur.close()
                        conn.close()
                        return False
                    for tabla in reversed(self.tablas_orden):
                        try:
                            cur.execute(f"TRUNCATE TABLE `{tabla}`")
                        except Exception as e:
                            print(f"No se pudo truncar {tabla}: {e}")

                total = 0
                errores = []

                for tabla in self.tablas_orden:
                    registros = datos['datos'].get(tabla, [])
                    if not registros:
                        continue

                    columnas = list(registros[0].keys())
                    cols_str = ", ".join(f"`{c}`" for c in columnas)
                    placeholders = ", ".join(["%s"] * len(columnas))

                    if limpiar_antes:
                        sql = f"INSERT INTO `{tabla}` ({cols_str}) VALUES ({placeholders})"
                    else:
                        sql = f"REPLACE INTO `{tabla}` ({cols_str}) VALUES ({placeholders})"

                    for r in registros:
                        try:
                            vals = [r.get(c) for c in columnas]
                            cur.execute(sql, vals)
                            total += 1
                        except Exception as e:
                            errores.append(f"{tabla}: {e}")

                cur.execute("SET FOREIGN_KEY_CHECKS=1")
                conn.commit()
                cur.close()
                conn.close()

                msg = f"Importación completada. Registros procesados: {total}"
                if errores:
                    msg += f"\nAdvertencias/errores: {len(errores)} (ver consola)"
                    print("\n".join(errores[:100]))
                    messagebox.showwarning("Importación con advertencias", msg)
                else:
                    messagebox.showinfo("Importación exitosa", msg)
                return True

            except Exception as e:
                conn.rollback()
                try:
                    cur.execute("SET FOREIGN_KEY_CHECKS=1")
                    cur.close()
                finally:
                    conn.close()
                raise e

        except Exception as e:
            messagebox.showerror("Error de Importación", f"{e}")
            return False

    def exportar_tabla_excel(self, tabla, ruta_archivo=None):
        try:
            if tabla not in self.tablas_orden:
                messagebox.showerror("Error", f"Tabla '{tabla}' no válida")
                return False
            if not ruta_archivo:
                nombre = f"{tabla}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                ruta_archivo = filedialog.asksaveasfilename(
                    title=f"Exportar tabla {tabla}",
                    defaultextension=".xlsx",
                    filetypes=[("Archivos Excel", "*.xlsx"), ("Todos los archivos", "*.*")],
                    initialfile=nombre
                )
            if not ruta_archivo:
                return False

            conn = get_mysql_conn()
            if tabla == 'movimiento':
                query = """
                SELECT m.*,
                       a.nombre AS area_nombre,
                       d.nombre AS distrito_nombre,
                       s.nombre AS servicio_nombre,
                       i.nombre AS insumo_nombre,
                       p.nombre AS presentacion_nombre,
                       tm.descripcion AS tipo_movimiento_desc
                FROM movimiento m
                LEFT JOIN area a ON m.area_id = a.id
                LEFT JOIN distrito d ON m.distrito_id = d.id
                LEFT JOIN servicio s ON m.servicio_id = s.id
                LEFT JOIN insumo i ON m.insumo_id = i.id
                LEFT JOIN presentacion p ON m.presentacion_id = p.id
                LEFT JOIN tipo_movimiento tm ON m.tipo_movimiento_id = tm.id
                """
            else:
                query = f"SELECT * FROM `{tabla}`"

            df = pd.read_sql_query(query, conn)
            conn.close()

            with pd.ExcelWriter(ruta_archivo, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name=tabla, index=False)
                wb = writer.book
                ws = writer.sheets[tabla]
                header = wb.add_format({'bold': True, 'fg_color': '#4472C4', 'font_color': 'white', 'border': 1})
                for col_num, value in enumerate(df.columns.values):
                    ws.write(0, col_num, value, header)
                    if df.empty:
                        width = len(str(value)) + 2
                    else:
                        width = min(max(df[value].astype(str).map(len).max(), len(str(value))) + 2, 50)
                    ws.set_column(col_num, col_num, width)

            messagebox.showinfo(
                "Exportación Exitosa",
                f"Tabla exportada correctamente\nTabla: {tabla}\nRegistros: {len(df)}\nArchivo: {os.path.basename(ruta_archivo)}"
            )
            return True

        except Exception as e:
            messagebox.showerror("Error de Exportación", f"{e}")
            return False

    def importar_tabla_excel(self, tabla, ruta_archivo=None):
        try:
            if tabla not in self.estructura_tablas:
                messagebox.showerror("Error", f"Tabla '{tabla}' no válida")
                return False
            if not ruta_archivo:
                ruta_archivo = filedialog.askopenfilename(
                    title=f"Importar datos para tabla {tabla}",
                    filetypes=[("Archivos Excel", "*.xlsx"), ("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
                )
            if not ruta_archivo:
                return False

            df = pd.read_csv(ruta_archivo) if ruta_archivo.lower().endswith('.csv') else pd.read_excel(ruta_archivo)
            if df.empty:
                messagebox.showwarning("Advertencia", "El archivo está vacío")
                return False

            req_cols = [c for c in self.estructura_tablas[tabla] if c != 'id']
            faltan = [c for c in req_cols if c not in df.columns]
            if faltan:
                messagebox.showerror("Error de Validación", f"Faltan columnas requeridas: {', '.join(faltan)}")
                return False

            if not messagebox.askyesno(
                "Confirmar",
                f"¿Importar {len(df)} registros en '{tabla}'?\nSi hay claves duplicadas, se reemplazarán."
            ):
                return False

            conn = get_mysql_conn()
            cur = conn.cursor()
            cur.execute("SET FOREIGN_KEY_CHECKS=0")

            try:
                columnas = [c for c in df.columns if c in self.estructura_tablas[tabla]]
                cols_str = ", ".join(f"`{c}`" for c in columnas)
                placeholders = ", ".join(["%s"] * len(columnas))
                sql = f"REPLACE INTO `{tabla}` ({cols_str}) VALUES ({placeholders})"

                count = 0
                errores = []
                for idx, row in df.iterrows():
                    try:
                        vals = [None if pd.isna(row[c]) else row[c] for c in columnas]
                        cur.execute(sql, vals)
                        count += 1
                    except Exception as e:
                        errores.append(f"Fila {idx + 2}: {e}")

                cur.execute("SET FOREIGN_KEY_CHECKS=1")
                conn.commit()
                cur.close()
                conn.close()

                msg = f"Importación completada. Registros: {count}"
                if errores:
                    msg += f"\nErrores: {len(errores)} (ver consola)"
                    print("\n".join(errores[:100]))
                    messagebox.showwarning("Importación con advertencias", msg)
                else:
                    messagebox.showinfo("Importación exitosa", msg)
                return True

            except Exception as e:
                conn.rollback()
                try:
                    cur.execute("SET FOREIGN_KEY_CHECKS=1")
                    cur.close()
                finally:
                    conn.close()
                raise e

        except Exception as e:
            messagebox.showerror("Error de Importación", f"{e}")
            return False

    def exportar_tabla_seleccionada(self):
        tabla = self.combo_tabla.get()
        if tabla:
            self.exportar_tabla_excel(tabla)

    def importar_tabla_seleccionada(self):
        tabla = self.combo_tabla.get()
        if tabla:
            self.importar_tabla_excel(tabla)


def crear_gestor_importar_exportar(parent_frame, main_window):
    gestor = ImportarExportarManager(parent_frame, main_window)
    return gestor