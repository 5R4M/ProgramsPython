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

from src.gui import styles
from src.database import bitacora as bdb


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

        # Paleta compartida del sistema
        self.COLORS = styles.COLORS

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
    # Helpers de UI — delegan a styles.py
    # ------------------------
    def _header_title_sub(self, parent, title_text, subtitle_text):
        styles.make_header(parent, title_text, subtitle_text)

    def _card(self, parent, title, icon_text):
        return styles.make_card_section(parent, title, icon_text)

    def _primary_button(self, parent, text, command):
        return styles.make_primary_button(parent, text, command)

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

        # Barra de acciones superior (Volver)
        top_actions = tk.Frame(self.main_frame, bg=self.COLORS['light'])
        top_actions.pack(fill='x', padx=10, pady=(4, 0))
        tk.Button(
            top_actions,
            text="🏠  Ir a ventana principal",
            font=('Segoe UI', 9, 'bold'),
            bg=self.COLORS['secondary'], fg='white',
            activebackground=self.COLORS['primary'], activeforeground='white',
            relief='flat', padx=12, pady=5, cursor='hand2',
            command=self._volver
        ).pack(side='left')

        # Notebook local sin padding externo
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill='both', expand=True, padx=0, pady=(6, 0))

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
    # Diálogos de advertencia
    # ------------------------
    def _dialogo_confirmar_reemplazar(self, nombre_archivo):
        """Muestra un diálogo de advertencia crítica para importación con reemplazo total.
        Devuelve True si el usuario confirma, False si cancela."""
        resultado = {'ok': False}

        dlg = tk.Toplevel()
        dlg.title("⚠️  ADVERTENCIA CRÍTICA — Reemplazar todos los datos")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.focus_set()

        # Centrar en pantalla
        dlg.update_idletasks()
        w, h = 580, 560
        x = (dlg.winfo_screenwidth() - w) // 2
        y = (dlg.winfo_screenheight() - h) // 2
        dlg.geometry(f"{w}x{h}+{x}+{y}")
        dlg.configure(bg=self.COLORS['light'])

        # Cabecera roja
        header = tk.Frame(dlg, bg='#c0392b', height=70)
        header.pack(fill='x')
        header.pack_propagate(False)
        tk.Label(header, text="⚠️  ACCIÓN DESTRUCTIVA E IRREVERSIBLE",
                 font=('Segoe UI', 13, 'bold'), bg='#c0392b', fg='white'
                 ).pack(expand=True)

        # Cuerpo
        body = tk.Frame(dlg, bg=self.COLORS['light'], padx=20, pady=10)
        body.pack(fill='both', expand=True)

        # Archivo seleccionado
        tk.Label(body, text="Archivo seleccionado:",
                 font=('Segoe UI', 9, 'bold'), bg=self.COLORS['light'],
                 fg=self.COLORS['text_dark']).pack(anchor='w', pady=(6, 0))
        tk.Label(body, text=os.path.basename(nombre_archivo),
                 font=('Segoe UI', 9), bg='#fdecea', fg='#c0392b',
                 relief='solid', bd=1, padx=6, pady=3
                 ).pack(anchor='w', pady=(2, 10), fill='x')

        # Qué pasará
        tk.Label(body, text="¿Qué ocurrirá si continúa?",
                 font=('Segoe UI', 10, 'bold'), bg=self.COLORS['light'],
                 fg='#c0392b').pack(anchor='w')

        consecuencias = (
            "  1. Se ELIMINARÁN permanentemente TODOS los registros actuales\n"
            "     de las siguientes tablas:\n\n"
            "       área · distrito · tipo_servicio · servicio · tipo_insumo\n"
            "       presentación · insumo · insumo_presentación · tipo_movimiento\n"
            "       movimiento · usuarios\n\n"
            "  2. Los datos se reemplazarán con el contenido del archivo seleccionado.\n\n"
            "  3. Esta operación NO puede deshacerse. No existe forma de\n"
            "     recuperar los datos borrados si no cuenta con otro respaldo."
        )
        cons_frame = tk.Frame(body, bg='#fdecea', relief='solid', bd=1)
        cons_frame.pack(fill='x', pady=(4, 10))
        tk.Label(cons_frame, text=consecuencias,
                 font=('Segoe UI', 9), bg='#fdecea', fg='#7b241c',
                 justify='left', padx=10, pady=8
                 ).pack(anchor='w')

        # Responsabilidad
        resp_frame = tk.Frame(body, bg='#fef9e7', relief='solid', bd=1)
        resp_frame.pack(fill='x', pady=(0, 10))
        resp_text = (
            "⚖️  Responsabilidad del usuario\n"
            "Al continuar, usted asume plena responsabilidad sobre la pérdida de\n"
            "datos que pueda producirse. Se recomienda exportar un backup completo\n"
            "ANTES de ejecutar esta acción."
        )
        tk.Label(resp_frame, text=resp_text,
                 font=('Segoe UI', 9), bg='#fef9e7', fg='#7d6608',
                 justify='left', padx=10, pady=8
                 ).pack(anchor='w')

        # Checkbox de confirmación
        check_var = tk.BooleanVar(value=False)
        check_frame = tk.Frame(body, bg=self.COLORS['light'])
        check_frame.pack(fill='x', pady=(0, 6))

        def _toggle_btn(*_):
            btn_confirmar.config(
                state='normal' if check_var.get() else 'disabled',
                bg='#c0392b' if check_var.get() else '#bdc3c7',
                activebackground='#a93226' if check_var.get() else '#bdc3c7'
            )

        chk = tk.Checkbutton(
            check_frame,
            text="Entiendo que se eliminarán TODOS los datos actuales y acepto\n"
                 "la responsabilidad de esta acción.",
            variable=check_var, command=_toggle_btn,
            font=('Segoe UI', 9, 'bold'), bg=self.COLORS['light'],
            fg='#c0392b', activebackground=self.COLORS['light'],
            wraplength=520, justify='left', anchor='w'
        )
        chk.pack(anchor='w')

        # Botones
        btn_frame = tk.Frame(dlg, bg=self.COLORS['light'], pady=10)
        btn_frame.pack(fill='x', padx=20)

        def _cancelar():
            resultado['ok'] = False
            dlg.destroy()

        def _confirmar():
            resultado['ok'] = True
            dlg.destroy()

        tk.Button(btn_frame, text="Cancelar — No hacer nada",
                  font=('Segoe UI', 10), bg=self.COLORS['secondary'],
                  fg='white', relief='flat', padx=14, pady=6,
                  cursor='hand2', command=_cancelar,
                  activebackground=self.COLORS['primary'], activeforeground='white'
                  ).pack(side='left')

        btn_confirmar = tk.Button(
            btn_frame,
            text="⚠️  Sí, eliminar todo e importar",
            font=('Segoe UI', 10, 'bold'), bg='#bdc3c7',
            fg='white', relief='flat', padx=14, pady=6,
            cursor='hand2', state='disabled', command=_confirmar,
            activebackground='#a93226', activeforeground='white'
        )
        btn_confirmar.pack(side='right')

        dlg.protocol("WM_DELETE_WINDOW", _cancelar)
        dlg.wait_window()
        return resultado['ok']

    def _dialogo_confirmar_mantener(self, nombre_archivo, total_registros):
        """Advertencia para importación que mantiene datos (REPLACE INTO)."""
        resultado = {'ok': False}

        dlg = tk.Toplevel()
        dlg.title("⚠️  Confirmar importación")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.focus_set()

        dlg.update_idletasks()
        w, h = 520, 380
        x = (dlg.winfo_screenwidth() - w) // 2
        y = (dlg.winfo_screenheight() - h) // 2
        dlg.geometry(f"{w}x{h}+{x}+{y}")
        dlg.configure(bg=self.COLORS['light'])

        # Cabecera naranja
        header = tk.Frame(dlg, bg='#e67e22', height=60)
        header.pack(fill='x')
        header.pack_propagate(False)
        tk.Label(header, text="⚠️  Importar datos (modo: mantener existentes)",
                 font=('Segoe UI', 11, 'bold'), bg='#e67e22', fg='white'
                 ).pack(expand=True)

        body = tk.Frame(dlg, bg=self.COLORS['light'], padx=20, pady=12)
        body.pack(fill='both', expand=True)

        tk.Label(body, text=f"Archivo:  {os.path.basename(nombre_archivo)}",
                 font=('Segoe UI', 9, 'bold'), bg=self.COLORS['light'],
                 fg=self.COLORS['text_dark']).pack(anchor='w', pady=(0, 8))

        info_text = (
            f"Se procesarán {total_registros} registros del archivo.\n\n"
            "• Los registros nuevos (ID no existente) se INSERTARÁN.\n"
            "• Los registros con ID ya existente se SOBREESCRIBIRÁN\n"
            "  con los valores del archivo (REPLACE INTO).\n\n"
            "⚠️  Los datos actuales con el mismo ID serán reemplazados.\n"
            "     Esta acción no puede deshacerse.\n\n"
            "Se recomienda exportar un backup antes de continuar."
        )
        info_frame = tk.Frame(body, bg='#fef9e7', relief='solid', bd=1)
        info_frame.pack(fill='x', pady=(0, 14))
        tk.Label(info_frame, text=info_text,
                 font=('Segoe UI', 9), bg='#fef9e7', fg='#7d6608',
                 justify='left', padx=10, pady=8
                 ).pack(anchor='w')

        btn_frame = tk.Frame(dlg, bg=self.COLORS['light'], pady=10)
        btn_frame.pack(fill='x', padx=20)

        def _cancelar():
            resultado['ok'] = False
            dlg.destroy()

        def _confirmar():
            resultado['ok'] = True
            dlg.destroy()

        tk.Button(btn_frame, text="Cancelar",
                  font=('Segoe UI', 10), bg=self.COLORS['secondary'],
                  fg='white', relief='flat', padx=14, pady=6,
                  cursor='hand2', command=_cancelar,
                  activebackground=self.COLORS['primary'], activeforeground='white'
                  ).pack(side='left')

        tk.Button(btn_frame, text="Sí, importar",
                  font=('Segoe UI', 10, 'bold'), bg='#e67e22',
                  fg='white', relief='flat', padx=14, pady=6,
                  cursor='hand2', command=_confirmar,
                  activebackground='#ca6f1e', activeforeground='white'
                  ).pack(side='right')

        dlg.protocol("WM_DELETE_WINDOW", _cancelar)
        dlg.wait_window()
        return resultado['ok']

    def _dialogo_confirmar_tabla(self, tabla, nombre_archivo, total_registros):
        """Advertencia para importación de tabla individual."""
        resultado = {'ok': False}

        dlg = tk.Toplevel()
        dlg.title("⚠️  Confirmar importación de tabla")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.focus_set()

        dlg.update_idletasks()
        w, h = 500, 340
        x = (dlg.winfo_screenwidth() - w) // 2
        y = (dlg.winfo_screenheight() - h) // 2
        dlg.geometry(f"{w}x{h}+{x}+{y}")
        dlg.configure(bg=self.COLORS['light'])

        header = tk.Frame(dlg, bg='#e67e22', height=60)
        header.pack(fill='x')
        header.pack_propagate(False)
        tk.Label(header, text=f"⚠️  Importar tabla: {tabla}",
                 font=('Segoe UI', 11, 'bold'), bg='#e67e22', fg='white'
                 ).pack(expand=True)

        body = tk.Frame(dlg, bg=self.COLORS['light'], padx=20, pady=12)
        body.pack(fill='both', expand=True)

        info_text = (
            f"Archivo:   {os.path.basename(nombre_archivo)}\n"
            f"Registros: {total_registros}\n"
            f"Tabla:     {tabla}\n\n"
            "• Los registros nuevos se INSERTARÁN en la tabla.\n"
            "• Los registros con clave duplicada se SOBREESCRIBIRÁN.\n\n"
            "⚠️  Los datos actuales con el mismo ID serán reemplazados.\n"
            "     Esta acción no puede deshacerse.\n\n"
            "Exporte un backup antes de continuar si tiene dudas."
        )
        info_frame = tk.Frame(body, bg='#fef9e7', relief='solid', bd=1)
        info_frame.pack(fill='x', pady=(0, 14))
        tk.Label(info_frame, text=info_text,
                 font=('Segoe UI', 9), bg='#fef9e7', fg='#7d6608',
                 justify='left', padx=10, pady=8
                 ).pack(anchor='w')

        btn_frame = tk.Frame(dlg, bg=self.COLORS['light'], pady=10)
        btn_frame.pack(fill='x', padx=20)

        def _cancelar():
            resultado['ok'] = False
            dlg.destroy()

        def _confirmar():
            resultado['ok'] = True
            dlg.destroy()

        tk.Button(btn_frame, text="Cancelar",
                  font=('Segoe UI', 10), bg=self.COLORS['secondary'],
                  fg='white', relief='flat', padx=14, pady=6,
                  cursor='hand2', command=_cancelar,
                  activebackground=self.COLORS['primary'], activeforeground='white'
                  ).pack(side='left')

        tk.Button(btn_frame, text="Sí, importar",
                  font=('Segoe UI', 10, 'bold'), bg='#e67e22',
                  fg='white', relief='flat', padx=14, pady=6,
                  cursor='hand2', command=_confirmar,
                  activebackground='#ca6f1e', activeforeground='white'
                  ).pack(side='right')

        dlg.protocol("WM_DELETE_WINDOW", _cancelar)
        dlg.wait_window()
        return resultado['ok']

    # ------------------------
    # Lógica de exportación/importación
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

            # ── Advertencia antes de conectar ────────────────────────────────
            if limpiar_antes:
                if not self._dialogo_confirmar_reemplazar(ruta_archivo):
                    return False
            else:
                # Contar registros totales del archivo para mostrar en advertencia
                total_prev = sum(len(v) for v in datos['datos'].values())
                if not self._dialogo_confirmar_mantener(ruta_archivo, total_prev):
                    return False

            conn = get_mysql_conn()
            cur = conn.cursor()
            cur.execute("SET FOREIGN_KEY_CHECKS=0")

            try:
                if limpiar_antes:
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
                modo = 'Reemplazar Todo' if limpiar_antes else 'Mantener Datos'
                try:
                    usuario = getattr(self.main_window, 'usuario', None)
                    bdb.registrar(usuario, 'IMPORTAR', 'Importar/Exportar',
                                  f'Backup importado ({modo}): {os.path.basename(ruta_archivo)} — {total} registros')
                except Exception:
                    pass
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

            if not self._dialogo_confirmar_tabla(tabla, ruta_archivo, len(df)):
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

    def _volver(self):
        if self.main_window and hasattr(self.main_window, 'show_welcome_screen'):
            self.main_window.show_welcome_screen()

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