# -*- coding: utf-8 -*-
"""
Ventana de Bitácora — solo accesible para administradores.
Muestra el historial de acciones: agregar, modificar y eliminar datos.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

from src.gui import styles
from src.database import bitacora as bdb


# Colores por tipo de acción
ACCION_COLORS = {
    'AGREGAR':   '#27ae60',   # verde
    'MODIFICAR': '#e67e22',   # naranja
    'ELIMINAR':  '#e74c3c',   # rojo
    'IMPORTAR':  '#8e44ad',   # morado
}
ACCION_ICONS = {
    'AGREGAR':   '➕',
    'MODIFICAR': '✏️',
    'ELIMINAR':  '🗑️',
    'IMPORTAR':  '📥',
}


class Bitacora:
    def __init__(self, parent_frame, main_window=None):
        self.parent = parent_frame
        self.main_window = main_window
        self.COLORS = styles.COLORS

        # Verificar rol (solo admin / super_admin)
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

        # Franja superior
        tk.Frame(self.main_frame, bg=self.COLORS['primary'], height=6
                 ).pack(fill='x')

        styles.make_header(self.main_frame,
                           "📋 Bitácora de Auditoría",
                           "Registro de todas las acciones realizadas en el sistema")

        # ── Filtros ──────────────────────────────────────────────
        filter_card = styles.make_card_section(self.main_frame, "Filtros de búsqueda", "🔍")

        row1 = tk.Frame(filter_card, bg=self.COLORS['white'])
        row1.pack(fill='x', pady=(0, 6))

        # Usuario
        tk.Label(row1, text="Usuario:", font=('Segoe UI', 9),
                 bg=self.COLORS['white'], fg=self.COLORS['text_dark']
                 ).grid(row=0, column=0, sticky='w', padx=(0, 4))
        self.var_usuario = tk.StringVar()
        tk.Entry(row1, textvariable=self.var_usuario, width=18,
                 font=('Segoe UI', 9)
                 ).grid(row=0, column=1, padx=(0, 16))

        # Acción
        tk.Label(row1, text="Acción:", font=('Segoe UI', 9),
                 bg=self.COLORS['white'], fg=self.COLORS['text_dark']
                 ).grid(row=0, column=2, sticky='w', padx=(0, 4))
        self.var_accion = tk.StringVar(value="TODAS")
        ttk.Combobox(row1, textvariable=self.var_accion, state='readonly', width=14,
                     values=["TODAS", "AGREGAR", "MODIFICAR", "ELIMINAR", "IMPORTAR"]
                     ).grid(row=0, column=3, padx=(0, 16))

        # Módulo
        tk.Label(row1, text="Módulo:", font=('Segoe UI', 9),
                 bg=self.COLORS['white'], fg=self.COLORS['text_dark']
                 ).grid(row=0, column=4, sticky='w', padx=(0, 4))
        self.var_modulo = tk.StringVar(value="TODOS")
        self.combo_modulo = ttk.Combobox(row1, textvariable=self.var_modulo,
                                         state='readonly', width=18)
        self.combo_modulo.grid(row=0, column=5, padx=(0, 16))

        row2 = tk.Frame(filter_card, bg=self.COLORS['white'])
        row2.pack(fill='x', pady=(0, 4))

        # Fecha desde
        tk.Label(row2, text="Desde:", font=('Segoe UI', 9),
                 bg=self.COLORS['white'], fg=self.COLORS['text_dark']
                 ).grid(row=0, column=0, sticky='w', padx=(0, 4))
        hace7 = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        self.var_desde = tk.StringVar(value=hace7)
        tk.Entry(row2, textvariable=self.var_desde, width=12,
                 font=('Segoe UI', 9)
                 ).grid(row=0, column=1, padx=(0, 6))
        tk.Label(row2, text="(YYYY-MM-DD)", font=('Segoe UI', 8),
                 bg=self.COLORS['white'], fg=self.COLORS['text_light']
                 ).grid(row=0, column=2, padx=(0, 16))

        # Fecha hasta
        tk.Label(row2, text="Hasta:", font=('Segoe UI', 9),
                 bg=self.COLORS['white'], fg=self.COLORS['text_dark']
                 ).grid(row=0, column=3, sticky='w', padx=(0, 4))
        hoy = datetime.now().strftime('%Y-%m-%d')
        self.var_hasta = tk.StringVar(value=hoy)
        tk.Entry(row2, textvariable=self.var_hasta, width=12,
                 font=('Segoe UI', 9)
                 ).grid(row=0, column=4, padx=(0, 6))
        tk.Label(row2, text="(YYYY-MM-DD)", font=('Segoe UI', 8),
                 bg=self.COLORS['white'], fg=self.COLORS['text_light']
                 ).grid(row=0, column=5, padx=(0, 16))

        # Botones de filtro
        btn_row = tk.Frame(filter_card, bg=self.COLORS['white'])
        btn_row.pack(fill='x', pady=(4, 0))
        styles.make_primary_button(btn_row, "🔍 Buscar", self._cargar).pack(side='left', padx=(0, 8))
        styles.make_primary_button(btn_row, "♻️ Limpiar filtros", self._limpiar_filtros).pack(side='left', padx=(0, 8))
        styles.make_primary_button(btn_row, "🔄 Actualizar", self._cargar).pack(side='left')

        # Contador
        self.lbl_total = tk.Label(btn_row, text="",
                                  font=('Segoe UI', 9, 'italic'),
                                  bg=self.COLORS['white'],
                                  fg=self.COLORS['text_light'])
        self.lbl_total.pack(side='right', padx=10)

        # ── Tabla ────────────────────────────────────────────────
        tabla_frame = tk.Frame(self.main_frame, bg=self.COLORS['light'])
        tabla_frame.pack(fill='both', expand=True, padx=10, pady=(4, 0))

        cols = ('id', 'fecha_hora', 'usuario', 'nombre_usuario',
                'accion', 'modulo', 'descripcion')
        self.tree = ttk.Treeview(tabla_frame, columns=cols, show='headings',
                                 selectmode='browse')

        anchos = {'id': 50, 'fecha_hora': 140, 'usuario': 100,
                  'nombre_usuario': 160, 'accion': 90,
                  'modulo': 110, 'descripcion': 400}
        titulos = {'id': 'ID', 'fecha_hora': 'Fecha y Hora',
                   'usuario': 'Usuario', 'nombre_usuario': 'Nombre',
                   'accion': 'Acción', 'modulo': 'Módulo',
                   'descripcion': 'Descripción'}

        for col in cols:
            self.tree.heading(col, text=titulos[col],
                              command=lambda c=col: self._ordenar(c))
            self.tree.column(col, width=anchos[col], minwidth=40,
                             stretch=(col == 'descripcion'))

        # Tags de color por acción
        for accion, color in ACCION_COLORS.items():
            self.tree.tag_configure(accion, foreground=color)

        vsb = ttk.Scrollbar(tabla_frame, orient='vertical',
                            command=self.tree.yview)
        hsb = ttk.Scrollbar(tabla_frame, orient='horizontal',
                            command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set,
                            xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        tabla_frame.rowconfigure(0, weight=1)
        tabla_frame.columnconfigure(0, weight=1)

        self.tree.bind('<Double-1>', self._ver_detalle)

        # ── Panel de detalle ─────────────────────────────────────
        det_card = styles.make_card_section(self.main_frame,
                                            "Detalle del registro (doble clic en fila)", "📄")
        self.txt_detalle = tk.Text(det_card, height=5, font=('Consolas', 9),
                                   bg='#f8f9fa', relief='flat',
                                   wrap='word', state='disabled')
        self.txt_detalle.pack(fill='both', expand=True)

    # ─────────────────────────────────────────────────────────────
    # Lógica
    # ─────────────────────────────────────────────────────────────
    def _cargar(self):
        """Carga/recarga registros aplicando filtros."""
        self.tree.delete(*self.tree.get_children())

        try:
            desde = self.var_desde.get().strip() or None
            hasta = self.var_hasta.get().strip() or None
            rows = bdb.obtener_registros(
                filtro_usuario=self.var_usuario.get().strip() or None,
                filtro_accion=self.var_accion.get(),
                filtro_modulo=self.var_modulo.get(),
                filtro_fecha_desde=desde,
                filtro_fecha_hasta=hasta,
                limite=1000
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la bitácora:\n{e}")
            return

        # Actualizar combo de módulos
        modulos = ["TODOS"] + bdb.obtener_modulos_usados()
        self.combo_modulo['values'] = modulos

        for r in rows:
            accion = r.get('accion', '')
            icon   = ACCION_ICONS.get(accion, '')
            fecha  = r['fecha_hora'].strftime('%d/%m/%Y %H:%M:%S') \
                     if isinstance(r['fecha_hora'], datetime) else str(r['fecha_hora'])
            self.tree.insert('', 'end',
                             iid=str(r['id']),
                             values=(r['id'], fecha,
                                     r['usuario'], r['nombre_usuario'],
                                     f"{icon} {accion}", r['modulo'],
                                     r['descripcion']),
                             tags=(accion,))

        total = len(rows)
        self.lbl_total.config(text=f"{total} registro{'s' if total != 1 else ''} encontrado{'s' if total != 1 else ''}")

    def _limpiar_filtros(self):
        self.var_usuario.set('')
        self.var_accion.set('TODAS')
        self.var_modulo.set('TODOS')
        self.var_desde.set((datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
        self.var_hasta.set(datetime.now().strftime('%Y-%m-%d'))
        self._cargar()

    def _ver_detalle(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        row_id = sel[0]
        # Obtener fila completa de BD para datos_antes / datos_despues
        try:
            rows = bdb.obtener_registros(limite=1000)
            fila = next((r for r in rows if str(r['id']) == row_id), None)
        except Exception:
            fila = None

        self.txt_detalle.config(state='normal')
        self.txt_detalle.delete(1.0, 'end')
        if fila:
            texto = (
                f"ID:           {fila['id']}\n"
                f"Fecha/hora:   {fila['fecha_hora']}\n"
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
        """Ordena la tabla al hacer clic en encabezado."""
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        items.sort(reverse=getattr(self, '_sort_reverse', False))
        for i, (_, k) in enumerate(items):
            self.tree.move(k, '', i)
        self._sort_reverse = not getattr(self, '_sort_reverse', False)

    def destroy(self):
        try:
            if hasattr(self, 'main_frame') and self.main_frame.winfo_exists():
                self.main_frame.destroy()
        except Exception:
            pass
