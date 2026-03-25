# -*- coding: utf-8 -*-
"""
Ventana de Bitácora — solo accesible para administradores.
Muestra el historial de acciones: agregar, modificar y eliminar datos.
"""
import calendar
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

from src.gui import styles
from src.database import bitacora as bdb


# ── Colores / íconos por tipo de acción ─────────────────────────────────────
ACCION_COLORS = {
    'AGREGAR':   '#27ae60',
    'MODIFICAR': '#e67e22',
    'ELIMINAR':  '#e74c3c',
    'IMPORTAR':  '#8e44ad',
}
ACCION_ICONS = {
    'AGREGAR':   '➕',
    'MODIFICAR': '✏️',
    'ELIMINAR':  '🗑️',
    'IMPORTAR':  '📥',
}

MESES_ES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']


# ── Calendario emergente ─────────────────────────────────────────────────────
class _CalendarioDialog(tk.Toplevel):
    """Calendario simple. Devuelve fecha en 'dd/mm/yyyy' en self.result."""

    def __init__(self, parent, fecha_actual_str=None):
        super().__init__(parent)
        self.result = None
        self.title("Seleccionar fecha")
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()
        self.configure(bg='white')

        # Parsear fecha inicial
        try:
            dt = datetime.strptime(fecha_actual_str, '%d/%m/%Y')
        except Exception:
            dt = datetime.now()
        self._año = dt.year
        self._mes = dt.month
        self._dia_sel = dt.day

        self._build_header()
        self._build_cabecera_dias()
        self.grid_frame = tk.Frame(self, bg='white')
        self.grid_frame.pack(fill='both', expand=True, padx=6, pady=(0, 6))
        self._render_mes()

        # Centrar
        self.update_idletasks()
        w, h = 252, 240
        px = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{max(0, px)}+{max(0, py)}")
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _build_header(self):
        nav = tk.Frame(self, bg='#2c3e50', height=36)
        nav.pack(fill='x')
        nav.pack_propagate(False)

        tk.Button(nav, text='◀', bg='#2c3e50', fg='white', relief='flat',
                  activebackground='#34495e', activeforeground='white',
                  font=('Segoe UI', 11), cursor='hand2',
                  command=self._prev_mes).pack(side='left', padx=6)

        self.lbl_mes = tk.Label(nav, bg='#2c3e50', fg='white',
                                font=('Segoe UI', 10, 'bold'))
        self.lbl_mes.pack(side='left', expand=True)

        tk.Button(nav, text='▶', bg='#2c3e50', fg='white', relief='flat',
                  activebackground='#34495e', activeforeground='white',
                  font=('Segoe UI', 11), cursor='hand2',
                  command=self._next_mes).pack(side='right', padx=6)

    def _build_cabecera_dias(self):
        hdr = tk.Frame(self, bg='#ecf0f1')
        hdr.pack(fill='x', padx=6, pady=(4, 0))
        for d in ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa', 'Do']:
            tk.Label(hdr, text=d, width=3, bg='#ecf0f1',
                     fg='#7f8c8d', font=('Segoe UI', 8, 'bold')
                     ).pack(side='left', expand=True)

    def _render_mes(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self.lbl_mes.config(text=f"{MESES_ES[self._mes - 1]}  {self._año}")

        hoy = datetime.now()
        for semana in calendar.monthcalendar(self._año, self._mes):
            fila = tk.Frame(self.grid_frame, bg='white')
            fila.pack(fill='x')
            for dia in semana:
                if dia == 0:
                    tk.Label(fila, text='', width=3, bg='white').pack(
                        side='left', expand=True)
                else:
                    es_sel = (dia == self._dia_sel and
                              self._mes == self._mes and
                              self._año == self._año)
                    es_hoy = (dia == hoy.day and self._mes == hoy.month
                              and self._año == hoy.year)
                    if dia == self._dia_sel:
                        bg, fg = '#3498db', 'white'
                    elif es_hoy:
                        bg, fg = '#d6eaf8', '#2c3e50'
                    else:
                        bg, fg = 'white', '#2c3e50'

                    btn = tk.Button(
                        fila, text=str(dia), width=3,
                        bg=bg, fg=fg, relief='flat', cursor='hand2',
                        font=('Segoe UI', 9),
                        activebackground='#5dade2', activeforeground='white',
                        command=lambda d=dia: self._seleccionar(d)
                    )
                    btn.pack(side='left', expand=True, padx=1, pady=1)

    def _seleccionar(self, dia):
        self.result = f"{dia:02d}/{self._mes:02d}/{self._año:04d}"
        self.destroy()

    def _prev_mes(self):
        self._mes -= 1
        if self._mes < 1:
            self._mes = 12
            self._año -= 1
        self._dia_sel = 0
        self._render_mes()

    def _next_mes(self):
        self._mes += 1
        if self._mes > 12:
            self._mes = 1
            self._año += 1
        self._dia_sel = 0
        self._render_mes()


# ── Widget de entrada de fecha con botón calendario ──────────────────────────
class _FechaEntry(tk.Frame):
    """Entry que muestra fecha en dd/mm/yyyy con botón para abrir calendario."""

    def __init__(self, parent, bg='white', **kw):
        super().__init__(parent, bg=bg)
        self._var = tk.StringVar()
        self._entry = tk.Entry(self, textvariable=self._var, width=10,
                               font=('Segoe UI', 9), relief='solid', bd=1)
        self._entry.pack(side='left')
        tk.Button(self, text='📅', relief='flat', bg=bg, cursor='hand2',
                  font=('Segoe UI', 9), padx=2,
                  command=self._abrir_calendario).pack(side='left', padx=(2, 0))

    def _abrir_calendario(self):
        dlg = _CalendarioDialog(self, self._var.get())
        self.wait_window(dlg)
        if dlg.result:
            self._var.set(dlg.result)

    def get(self):
        return self._var.get()

    def set(self, valor):
        self._var.set(valor)

    def get_yyyy_mm_dd(self):
        """Convierte dd/mm/yyyy → yyyy-mm-dd para la BD. Devuelve None si vacío."""
        v = self._var.get().strip()
        if not v:
            return None
        try:
            return datetime.strptime(v, '%d/%m/%Y').strftime('%Y-%m-%d')
        except ValueError:
            return None


# ── Ventana principal de Bitácora ────────────────────────────────────────────
class Bitacora:
    def __init__(self, parent_frame, main_window=None):
        self.parent = parent_frame
        self.main_window = main_window
        self.COLORS = styles.COLORS

        # Solo admin / super_admin
        if main_window and main_window.usuario.get('rol') not in ('admin', 'super_admin'):
            tk.Label(parent_frame,
                     text="⛔ Acceso denegado.\nEsta sección es exclusiva para administradores.",
                     font=('Segoe UI', 16, 'bold'), fg=self.COLORS['danger'],
                     bg=self.COLORS['light']).pack(expand=True)
            return

        self._build_ui()
        self._cargar()

    # ─────────────────────────────────────────────────────────────
    # UI
    # ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.main_frame = tk.Frame(self.parent, bg=self.COLORS['light'])
        self.main_frame.pack(fill='both', expand=True)

        tk.Frame(self.main_frame, bg=self.COLORS['primary'], height=6).pack(fill='x')

        styles.make_header(self.main_frame,
                           "📋 Bitácora de Auditoría",
                           "Registro de todas las acciones realizadas en el sistema")

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

        # ── Filtros ──────────────────────────────────────────────
        filter_card = styles.make_card_section(self.main_frame, "Filtros de búsqueda", "🔍")

        # Fila 1: Usuario | Acción | Módulo
        row1 = tk.Frame(filter_card, bg=self.COLORS['white'])
        row1.pack(fill='x', pady=(0, 8))

        # — Usuario —
        tk.Label(row1, text="Usuario / Nombre:", font=('Segoe UI', 9, 'bold'),
                 bg=self.COLORS['white'], fg=self.COLORS['text_dark']
                 ).pack(side='left', padx=(0, 4))
        self.var_usuario = tk.StringVar()
        ent_usuario = ttk.Entry(row1, textvariable=self.var_usuario, width=20,
                                font=('Segoe UI', 9))
        ent_usuario.pack(side='left', padx=(0, 20))
        ent_usuario.bind('<Return>', lambda _: self._cargar())

        # — Acción —
        tk.Label(row1, text="Acción:", font=('Segoe UI', 9, 'bold'),
                 bg=self.COLORS['white'], fg=self.COLORS['text_dark']
                 ).pack(side='left', padx=(0, 4))
        self.var_accion = tk.StringVar(value="TODAS")
        ttk.Combobox(row1, textvariable=self.var_accion, state='readonly', width=14,
                     values=["TODAS", "AGREGAR", "MODIFICAR", "ELIMINAR", "IMPORTAR"]
                     ).pack(side='left', padx=(0, 20))

        # — Módulo —
        tk.Label(row1, text="Módulo:", font=('Segoe UI', 9, 'bold'),
                 bg=self.COLORS['white'], fg=self.COLORS['text_dark']
                 ).pack(side='left', padx=(0, 4))
        self.var_modulo = tk.StringVar(value="TODOS")
        self.combo_modulo = ttk.Combobox(row1, textvariable=self.var_modulo,
                                         state='readonly', width=20)
        self.combo_modulo.pack(side='left')

        # Fila 2: Fechas
        row2 = tk.Frame(filter_card, bg=self.COLORS['white'])
        row2.pack(fill='x', pady=(0, 8))

        tk.Label(row2, text="Desde:", font=('Segoe UI', 9, 'bold'),
                 bg=self.COLORS['white'], fg=self.COLORS['text_dark']
                 ).pack(side='left', padx=(0, 4))
        hace7 = (datetime.now() - timedelta(days=7)).strftime('%d/%m/%Y')
        self.fe_desde = _FechaEntry(row2, bg=self.COLORS['white'])
        self.fe_desde.set(hace7)
        self.fe_desde.pack(side='left', padx=(0, 20))

        tk.Label(row2, text="Hasta:", font=('Segoe UI', 9, 'bold'),
                 bg=self.COLORS['white'], fg=self.COLORS['text_dark']
                 ).pack(side='left', padx=(0, 4))
        hoy = datetime.now().strftime('%d/%m/%Y')
        self.fe_hasta = _FechaEntry(row2, bg=self.COLORS['white'])
        self.fe_hasta.set(hoy)
        self.fe_hasta.pack(side='left', padx=(0, 20))

        tk.Label(row2, text="(formato dd/mm/yyyy  —  búsqueda de usuario indiferente a mayúsculas)",
                 font=('Segoe UI', 8), bg=self.COLORS['white'],
                 fg=self.COLORS['text_light']).pack(side='left')

        # Fila 3: Botones
        btn_row = tk.Frame(filter_card, bg=self.COLORS['white'])
        btn_row.pack(fill='x')
        styles.make_primary_button(btn_row, "🔍 Buscar", self._cargar).pack(side='left', padx=(0, 8))
        styles.make_primary_button(btn_row, "♻️ Limpiar", self._limpiar_filtros).pack(side='left', padx=(0, 8))
        styles.make_primary_button(btn_row, "🔄 Actualizar", self._cargar).pack(side='left')

        self.lbl_total = tk.Label(btn_row, text="",
                                  font=('Segoe UI', 9, 'italic'),
                                  bg=self.COLORS['white'], fg=self.COLORS['text_light'])
        self.lbl_total.pack(side='right', padx=10)

        # ── Tabla ────────────────────────────────────────────────
        tabla_frame = tk.Frame(self.main_frame, bg=self.COLORS['light'])
        tabla_frame.pack(fill='both', expand=True, padx=10, pady=(4, 0))

        cols = ('id', 'fecha_hora', 'usuario', 'nombre_usuario',
                'accion', 'modulo', 'descripcion')
        self.tree = ttk.Treeview(tabla_frame, columns=cols, show='headings',
                                 selectmode='browse')

        anchos  = {'id': 50, 'fecha_hora': 140, 'usuario': 100,
                   'nombre_usuario': 160, 'accion': 100,
                   'modulo': 120, 'descripcion': 400}
        titulos = {'id': 'ID', 'fecha_hora': 'Fecha y Hora',
                   'usuario': 'Usuario', 'nombre_usuario': 'Nombre',
                   'accion': 'Acción', 'modulo': 'Módulo',
                   'descripcion': 'Descripción'}

        for col in cols:
            self.tree.heading(col, text=titulos[col],
                              command=lambda c=col: self._ordenar(c))
            self.tree.column(col, width=anchos[col], minwidth=40,
                             stretch=(col == 'descripcion'))

        for accion, color in ACCION_COLORS.items():
            self.tree.tag_configure(accion, foreground=color)

        vsb = ttk.Scrollbar(tabla_frame, orient='vertical',   command=self.tree.yview)
        hsb = ttk.Scrollbar(tabla_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        tabla_frame.rowconfigure(0, weight=1)
        tabla_frame.columnconfigure(0, weight=1)

        self.tree.bind('<Double-1>', self._ver_detalle)

        # ── Panel de detalle ─────────────────────────────────────
        det_card = styles.make_card_section(self.main_frame,
                                            "Detalle del registro  (doble clic en una fila)", "📄")
        self.txt_detalle = tk.Text(det_card, height=5, font=('Consolas', 9),
                                   bg='#f8f9fa', relief='flat',
                                   wrap='word', state='disabled')
        self.txt_detalle.pack(fill='both', expand=True)

    # ─────────────────────────────────────────────────────────────
    # Lógica
    # ─────────────────────────────────────────────────────────────
    def _cargar(self):
        self.tree.delete(*self.tree.get_children())
        try:
            rows = bdb.obtener_registros(
                filtro_usuario=self.var_usuario.get().strip() or None,
                filtro_accion=self.var_accion.get(),
                filtro_modulo=self.var_modulo.get(),
                filtro_fecha_desde=self.fe_desde.get_yyyy_mm_dd(),
                filtro_fecha_hasta=self.fe_hasta.get_yyyy_mm_dd(),
                limite=1000
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la bitácora:\n{e}")
            return

        # Refrescar módulos disponibles
        modulos = ["TODOS"] + bdb.obtener_modulos_usados()
        self.combo_modulo['values'] = modulos

        for r in rows:
            accion = r.get('accion', '')
            icon   = ACCION_ICONS.get(accion, '')
            fecha  = r['fecha_hora'].strftime('%d/%m/%Y  %H:%M:%S') \
                     if isinstance(r['fecha_hora'], datetime) else str(r['fecha_hora'])
            self.tree.insert('', 'end',
                             iid=str(r['id']),
                             values=(r['id'], fecha,
                                     r['usuario'], r['nombre_usuario'],
                                     f"{icon} {accion}", r['modulo'],
                                     r['descripcion']),
                             tags=(accion,))

        total = len(rows)
        self.lbl_total.config(
            text=f"{total} registro{'s' if total != 1 else ''} encontrado{'s' if total != 1 else ''}")

    def _limpiar_filtros(self):
        self.var_usuario.set('')
        self.var_accion.set('TODAS')
        self.var_modulo.set('TODOS')
        self.fe_desde.set((datetime.now() - timedelta(days=7)).strftime('%d/%m/%Y'))
        self.fe_hasta.set(datetime.now().strftime('%d/%m/%Y'))
        self._cargar()

    def _ver_detalle(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        row_id = sel[0]
        try:
            rows = bdb.obtener_registros(limite=2000)
            fila = next((r for r in rows if str(r['id']) == row_id), None)
        except Exception:
            fila = None

        self.txt_detalle.config(state='normal')
        self.txt_detalle.delete(1.0, 'end')
        if fila:
            fecha_str = (fila['fecha_hora'].strftime('%d/%m/%Y  %H:%M:%S')
                         if isinstance(fila['fecha_hora'], datetime)
                         else str(fila['fecha_hora']))
            texto = (
                f"ID:           {fila['id']}\n"
                f"Fecha/hora:   {fecha_str}\n"
                f"Usuario:      {fila['usuario']}  ({fila['nombre_usuario']})\n"
                f"Acción:       {fila['accion']}\n"
                f"Módulo:       {fila['modulo']}\n"
                f"Descripción:  {fila['descripcion']}\n"
            )
            if fila.get('datos_antes'):
                texto += f"\nAntes:\n{fila['datos_antes']}\n"
            if fila.get('datos_despues'):
                texto += f"\nDespués:\n{fila['datos_despues']}\n"
            self.txt_detalle.insert('end', texto)
        self.txt_detalle.config(state='disabled')

    def _ordenar(self, col):
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        items.sort(reverse=getattr(self, '_sort_reverse', False))
        for i, (_, k) in enumerate(items):
            self.tree.move(k, '', i)
        self._sort_reverse = not getattr(self, '_sort_reverse', False)

    def _volver(self):
        if self.main_window and hasattr(self.main_window, 'show_welcome_screen'):
            self.main_window.show_welcome_screen()

    def destroy(self):
        try:
            if hasattr(self, 'main_frame') and self.main_frame.winfo_exists():
                self.main_frame.destroy()
        except Exception:
            pass
