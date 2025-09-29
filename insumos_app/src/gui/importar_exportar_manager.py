# -*- coding: utf-8 -*-
# Importar/Exportar - sin estilos globales ni scroll (ni vertical ni horizontal)
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


class ImportarExportarManager:
    """Gestor de importación/exportación sin alterar estilos globales y sin scroll."""
    def __init__(self, parent_frame, main_window=None):
        self.parent_frame = parent_frame
        self.main_window = main_window

        # Paleta local
        self.COLORS = {
            'primary':   '#2c3e50',
            'accent':    '#3498db',
            'danger':    '#e74c3c',
            'light':     '#ecf0f1',
            'white':     '#ffffff',
            'text_dark': '#2c3e50',
        }

        # Orden de dependencias
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

        # Estructura básica
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

    # ------------------------
    # Helpers de UI locales
    # ------------------------
    def _header_title_sub(self, parent, title_text, subtitle_text):
        header_frame = tk.Frame(parent, bg=self.COLORS['primary'], height=55)
        header_frame.pack(fill='x', padx=0, pady=(0, 6))  # sin margen superior
        header_frame.pack_propagate(False)

        inner = tk.Frame(header_frame, bg=self.COLORS['primary'])
        inner.pack(fill='both', expand=True, padx=15, pady=6)

        tk.Label(inner, text=title_text,
                font=('Segoe UI', 11, 'bold'),
                fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(anchor='w')
        tk.Label(inner, text=subtitle_text,
                font=('Segoe UI', 8),
                fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(anchor='w', pady=(2, 0))

    def _card(self, parent, title, icon_text):
        container = tk.Frame(parent, bg=self.COLORS['light'])
        container.pack(fill='x', padx=10, pady=6)

        card = tk.Frame(container, bg=self.COLORS['white'], bd=1, relief='solid', highlightthickness=0)
        card.pack(fill='x')

        header = tk.Frame(card, bg=self.COLORS['primary'], height=26)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(header, text=f"{icon_text} {title}",
                 font=('Segoe UI', 9, 'bold'),
                 fg=self.COLORS['white'], bg=self.COLORS['primary']).pack(side='left', padx=10)

        content = tk.Frame(card, bg=self.COLORS['white'])
        content.pack(fill='x', padx=12, pady=8)

        return content

    def _primary_button(self, parent, text, command):
        btn = tk.Button(parent, text=text, command=command,
                        font=('Segoe UI', 9, 'bold'),
                        bg=self.COLORS['accent'], fg='white',
                        relief='flat', borderwidth=0, padx=12, pady=6, cursor='hand2',
                        activebackground='#2980b9', activeforeground='white')
        return btn

    # ------------------------
    # Interfaz
    # ------------------------
    def crear_interfaz(self):
        self.main_frame = tk.Frame(self.parent_frame, bg=self.COLORS['light'])
        # Quitar padding externo para cubrir ancho/alto total
        self.main_frame.pack(fill='both', expand=True)

        # Franja superior azul para pegar el header al tope
        top_strip = tk.Frame(self.main_frame, bg=self.COLORS['primary'], height=6)
        top_strip.pack(fill='x', padx=0, pady=0)
        top_strip.pack_propagate(False)

        self._header_title_sub(
            self.main_frame,
            "🗄️ Gestión de Importación y Exportación de Datos",
            "Administre los respaldos y transferencias de datos del sistema"
        )

        # Notebook local sin padding externo
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill='both', expand=True, padx=0, pady=0)

        self._crear_pestana_backup()
        self._crear_pestana_tablas()

    def _crear_pestana_backup(self):
        frame_backup = tk.Frame(self.notebook, bg=self.COLORS['light'])
        self.notebook.add(frame_backup, text="🗄️ Backup Completo")

        # Franja superior azul dentro de la pestaña
        top_strip = tk.Frame(frame_backup, bg=self.COLORS['primary'], height=6)
        top_strip.pack(fill='x', padx=0, pady=0)
        top_strip.pack_propagate(False)
        
        self._header_title_sub(frame_backup, "🗄️ Backup Completo", "Cree y restaure respaldos completos del sistema")

        # Contenido directo, sin scroll
        content = tk.Frame(frame_backup, bg=self.COLORS['light'])
        content.pack(fill='both', expand=True)

        # Exportación
        export_frame = self._card(content, "Exportación de Backup", "📤")
        tk.Label(export_frame,
                 text="Crear un archivo de respaldo con todos los datos del sistema",
                 font=('Segoe UI', 9), fg=self.COLORS['text_dark'], bg=self.COLORS['white']
                 ).pack(anchor='w', pady=(0, 10))
        self._primary_button(export_frame, "🗄️ Exportar Backup Completo", self.exportar_datos_completos).pack(anchor='w')

        # Importación
        import_frame = self._card(content, "Importación de Backup", "📥")
        tk.Label(import_frame,
                 text="Restaurar datos desde un archivo de respaldo",
                 font=('Segoe UI', 9), fg=self.COLORS['text_dark'], bg=self.COLORS['white']
                 ).pack(anchor='w', pady=(0, 10))

        button_row = tk.Frame(import_frame, bg=self.COLORS['white'])
        button_row.pack(fill='x')
        self._primary_button(button_row, "📥 Importar (Mantener Datos)",
                             lambda: self.importar_datos_completos(limpiar_antes=False)).pack(side='left', padx=(0, 10))
        self._primary_button(button_row, "⚠️ Importar (Reemplazar Todo)",
                             lambda: self.importar_datos_completos(limpiar_antes=True)).pack(side='left')

        # Info
        warning_frame = self._card(content, "Información Importante", "⚠️")
        warning_text = (
            "• Mantener Datos: Agrega/actualiza registros sin eliminar datos existentes\n"
            "• Reemplazar Todo: ELIMINA todos los datos actuales antes de importar\n"
            "• Siempre haga un backup antes de importar datos importantes\n"
            "• Los archivos de backup incluyen información sensible (usuarios y contraseñas)\n"
            "• El proceso puede tomar varios minutos dependiendo del tamaño de los datos"
        )
        tk.Label(warning_frame, text=warning_text,
                 font=('Segoe UI', 9), justify='left',
                 fg=self.COLORS['text_dark'], bg=self.COLORS['white']
                 ).pack(anchor='nw', fill='both', expand=True)

    def _crear_pestana_tablas(self):
        frame_tablas = tk.Frame(self.notebook, bg=self.COLORS['light'])
        self.notebook.add(frame_tablas, text="📊 Tablas Individuales")

        # Franja superior azul dentro de la pestaña
        top_strip = tk.Frame(frame_tablas, bg=self.COLORS['primary'], height=6)
        top_strip.pack(fill='x', padx=0, pady=0)
        top_strip.pack_propagate(False)
        
        self._header_title_sub(frame_tablas, "📊 Tablas Individuales", "Exportar/Importar datos por tabla")

        # Contenido directo, sin scroll
        content = tk.Frame(frame_tablas, bg=self.COLORS['light'])
        content.pack(fill='both', expand=True)

        # Selección
        selection = self._card(content, "Selección de Tabla", "🎯")
        tk.Label(selection, text="Seleccionar tabla para exportar/importar:",
                 font=('Segoe UI', 9), fg=self.COLORS['text_dark'], bg=self.COLORS['white']
                 ).pack(anchor='w', pady=(0, 8))

        self.combo_tabla = ttk.Combobox(selection, values=self.tablas_orden, state="readonly", width=30)
        self.combo_tabla.pack(fill='x', pady=(0, 10))
        if self.tablas_orden:
            self.combo_tabla.set(self.tablas_orden[0])

        action_row = tk.Frame(selection, bg=self.COLORS['white'])
        action_row.pack(fill='x')
        self._primary_button(action_row, "📤 Exportar a Excel", self.exportar_tabla_seleccionada).pack(side='left', padx=(0, 10))
        self._primary_button(action_row, "📥 Importar desde Excel/CSV", self.importar_tabla_seleccionada).pack(side='left')

        # Información
        info = self._card(content, "Información de Tablas", "ℹ️")
        info_text = (
            "Descripción de las principales tablas del sistema:\n\n"
            "• area, distrito, tipo_servicio, servicio, tipo_insumo, presentacion, insumo, movimiento, usuarios\n"
            "Formatos soportados: Excel (.xlsx), CSV (.csv), JSON (.json)"
        )
        tk.Label(info, text=info_text, font=('Segoe UI', 9),
                 justify='left', fg=self.COLORS['text_dark'], bg=self.COLORS['white']
                 ).pack(anchor='nw', fill='both', expand=True)

    # ------------------------
    # Lógica de exportación/importación (sin cambios funcionales)
    # ------------------------
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
        tabla = getattr(self, 'combo_tabla', None).get() if hasattr(self, 'combo_tabla') else None
        if tabla:
            self.exportar_tabla_excel(tabla)

    def importar_tabla_seleccionada(self):
        tabla = getattr(self, 'combo_tabla', None).get() if hasattr(self, 'combo_tabla') else None
        if tabla:
            self.importar_tabla_excel(tabla)

    # Limpieza local
    def destroy(self):
        try:
            if hasattr(self, 'main_frame') and self.main_frame.winfo_exists():
                self.main_frame.destroy()
        except Exception:
            pass


def crear_gestor_importar_exportar(parent_frame, main_window):
    gestor = ImportarExportarManager(parent_frame, main_window)
    return gestor