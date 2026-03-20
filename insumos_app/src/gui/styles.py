# -*- coding: utf-8 -*-
"""
styles.py — Estilos y componentes visuales compartidos para insumos_app.

Centraliza colores, fuentes y constructores de widgets para que todas
las vistas del sistema tengan un diseño uniforme y profesional.
"""
import tkinter as tk
from tkinter import ttk

# ──────────────────────────────────────────────
# PALETA DE COLORES OFICIAL
# ──────────────────────────────────────────────
COLORS = {
    'primary':      '#2c3e50',   # Azul oscuro — cabeceras, sidebar
    'secondary':    '#34495e',   # Gris azulado — barra de estado
    'accent':       '#3498db',   # Azul brillante — botones, selección
    'accent_dark':  '#2980b9',   # Azul oscuro — hover/active de accent
    'success':      '#27ae60',   # Verde — acciones de confirmación
    'success_dark': '#219a52',   # Verde oscuro — hover de success
    'warning':      '#f39c12',   # Naranja — advertencias
    'danger':       '#e74c3c',   # Rojo — eliminar / errores
    'danger_dark':  '#c0392b',   # Rojo oscuro — hover de danger
    'light':        '#ecf0f1',   # Gris muy claro — fondo de vistas
    'white':        '#ffffff',   # Blanco — fondo de tarjetas/campos
    'text_dark':    '#2c3e50',   # Texto principal
    'text_light':   '#7f8c8d',   # Texto secundario / placeholders
    'hover':        '#3498db',   # Color genérico de hover
    'active':       '#2980b9',   # Color genérico de active
    'exit_btn':     '#17a2b8',   # Celeste — botón salir
    'exit_hover':   '#138496',   # Celeste oscuro — hover salir
}

# ──────────────────────────────────────────────
# TIPOGRAFÍA ESTÁNDAR
# ──────────────────────────────────────────────
FONTS = {
    'header_title':    ('Segoe UI', 12, 'bold'),
    'header_subtitle': ('Segoe UI', 9),
    'card_title':      ('Segoe UI', 10, 'bold'),
    'label':           ('Segoe UI', 9),
    'label_bold':      ('Segoe UI', 9, 'bold'),
    'button':          ('Segoe UI', 9, 'bold'),
    'table':           ('Segoe UI', 9),
    'table_header':    ('Segoe UI', 9, 'bold'),
    'dialog_title':    ('Segoe UI', 11, 'bold'),
}


# ──────────────────────────────────────────────
# CONSTRUCTORES DE COMPONENTES
# ──────────────────────────────────────────────

def make_header(parent, title_text, subtitle_text):
    """
    Encabezado de sección: barra azul a todo el ancho con título y subtítulo.
    No retorna nada (se inserta automáticamente en `parent`).
    """
    header_frame = tk.Frame(parent, bg=COLORS['primary'], height=55)
    header_frame.pack(fill='x', padx=0, pady=(0, 6))
    header_frame.pack_propagate(False)

    inner = tk.Frame(header_frame, bg=COLORS['primary'])
    inner.pack(fill='both', expand=True, padx=12, pady=4)

    tk.Label(inner, text=title_text,
             font=FONTS['header_title'],
             fg=COLORS['white'], bg=COLORS['primary']).pack(anchor='w')
    tk.Label(inner, text=subtitle_text,
             font=FONTS['header_subtitle'],
             fg=COLORS['white'], bg=COLORS['primary']).pack(anchor='w', pady=(1, 0))


def make_card_section(parent, title, icon):
    """
    Tarjeta con barra azul superior y área de contenido blanca.
    Retorna el frame de contenido interior donde se agregan los widgets.
    """
    container = tk.Frame(parent, bg=COLORS['light'])
    container.pack(fill='x', padx=10, pady=6)

    card = tk.Frame(container, bg=COLORS['white'],
                    bd=1, relief='solid', highlightthickness=0)
    card.pack(fill='both', expand=True)

    header = tk.Frame(card, bg=COLORS['primary'], height=26)
    header.pack(fill='x')
    header.pack_propagate(False)

    tk.Label(header, text=f"{icon}  {title}",
             font=FONTS['card_title'],
             fg=COLORS['white'], bg=COLORS['primary']).pack(side='left', padx=10)

    content = tk.Frame(card, bg=COLORS['white'])
    content.pack(fill='both', expand=True, padx=12, pady=8)

    return content


def make_primary_button(parent, text, command):
    """Botón primario azul con efecto hover."""
    btn = tk.Button(
        parent, text=text, command=command,
        font=FONTS['button'],
        bg=COLORS['accent'], fg='white',
        relief='flat', borderwidth=0,
        padx=12, pady=5,
        cursor='hand2',
        activebackground=COLORS['accent_dark'],
        activeforeground='white',
    )
    btn.bind('<Enter>', lambda e: btn.config(bg=COLORS['accent_dark']))
    btn.bind('<Leave>', lambda e: btn.config(bg=COLORS['accent']))
    return btn


def make_danger_button(parent, text, command):
    """Botón de peligro (rojo) con efecto hover."""
    btn = tk.Button(
        parent, text=text, command=command,
        font=FONTS['button'],
        bg=COLORS['danger'], fg='white',
        relief='flat', borderwidth=0,
        padx=12, pady=5,
        cursor='hand2',
        activebackground=COLORS['danger_dark'],
        activeforeground='white',
    )
    btn.bind('<Enter>', lambda e: btn.config(bg=COLORS['danger_dark']))
    btn.bind('<Leave>', lambda e: btn.config(bg=COLORS['danger']))
    return btn


def make_success_button(parent, text, command):
    """Botón de éxito (verde) con efecto hover."""
    btn = tk.Button(
        parent, text=text, command=command,
        font=FONTS['button'],
        bg=COLORS['success'], fg='white',
        relief='flat', borderwidth=0,
        padx=12, pady=5,
        cursor='hand2',
        activebackground=COLORS['success_dark'],
        activeforeground='white',
    )
    btn.bind('<Enter>', lambda e: btn.config(bg=COLORS['success_dark']))
    btn.bind('<Leave>', lambda e: btn.config(bg=COLORS['success']))
    return btn


def configure_treeview():
    """
    Aplica el estilo estándar a todos los Treeview de la sesión.
    Llamar una vez en la ventana principal o antes de crear el primer Treeview.
    """
    style = ttk.Style()
    style.configure(
        'Treeview',
        background=COLORS['white'],
        fieldbackground=COLORS['white'],
        foreground=COLORS['text_dark'],
        rowheight=28,
        font=FONTS['table'],
    )
    style.configure(
        'Treeview.Heading',
        background=COLORS['secondary'],
        foreground=COLORS['white'],
        font=FONTS['table_header'],
        relief='flat',
    )
    style.map(
        'Treeview',
        background=[('selected', COLORS['accent'])],
        foreground=[('selected', COLORS['white'])],
    )
    style.map(
        'Treeview.Heading',
        background=[('active', COLORS['primary'])],
    )
