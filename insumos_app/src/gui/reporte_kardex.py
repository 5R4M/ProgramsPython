# Imports existentes
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import pandas as pd
from datetime import datetime
import sys
import os
from ttkwidgets.autocomplete import AutocompleteCombobox

# Nuevos imports para PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


# Agregar el directorio raíz del proyecto al PATH de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.db_manager import (
    obtener_areas,
    obtener_distritos,
    obtener_tipos_servicio_por_distrito,
    obtener_servicios_por_tipo,
    obtener_tipos_insumo,
    obtener_insumos_por_tipo,
    obtener_presentaciones,
    obtener_movimientos_kardex
)

class ReporteKardex:
    # Definir las columnas como atributo de la clase
    COLUMNAS = [
        'Fecha', 'Referencia', 'Remitente/Destinatario', 'Entrada',
        'Precio Unitario', 'Valor Total', 'Lote', 'Fecha Vencimiento', 
        'Salidas', 'Reajustes', 'Saldo', 'Observaciones'
    ]
    
    def formato_float(self, valor):
        try:
            return f"{float(valor):.2f}"
        except (ValueError, TypeError):
            return ""
    
    def __init__(self, parent_frame, main_window=None):
        self.parent = parent_frame
        self.main_window = main_window
        self.movimientos_data = None
        
        self.areas = []
        self.distritos = []       
        self.tipos_servicio = []  
        self.tipos_insumo = []
        self.insumos = []
        self.presentaciones = []
        
        self.setup_ui()

    def setup_ui(self):
        # Frame principal - USAR PACK PARA TODO
        self.frame_principal = ttk.LabelFrame(self.parent, text="Filtros de Reporte")
        self.frame_principal.pack(fill="both", expand=True, padx=10, pady=5)

        # Frame para fechas
        self.frame_fechas = ttk.Frame(self.frame_principal)
        self.frame_fechas.pack(fill="x", padx=5, pady=5)
        
        # Grid DENTRO del frame_fechas (esto es válido)
        ttk.Label(self.frame_fechas, text="Fecha Inicial:").grid(row=0, column=0, padx=5)
        self.fecha_inicial = DateEntry(self.frame_fechas, width=12, date_pattern='dd/mm/yyyy')
        self.fecha_inicial.grid(row=0, column=1, padx=5)
        ttk.Label(self.frame_fechas, text="Fecha Final:").grid(row=0, column=2, padx=5)
        self.fecha_final = DateEntry(self.frame_fechas, width=12, date_pattern='dd/mm/yyyy')
        self.fecha_final.grid(row=0, column=3, padx=5)

        # Frame para combos
        self.frame_combos = ttk.Frame(self.frame_principal)
        self.frame_combos.pack(fill="x", padx=5, pady=5)

        # Primera fila de combos
        self.frame_combos1 = ttk.Frame(self.frame_combos)
        self.frame_combos1.pack(fill="x", pady=5)
        
        # Grid DENTRO del frame_combos1 (esto es válido)
        ttk.Label(self.frame_combos1, text="Área:").grid(row=0, column=0, padx=5, sticky='w')
        self.area_var = tk.StringVar()
        self.combo_area = AutocompleteCombobox(self.frame_combos1, textvariable=self.area_var, state="normal", width=20)
        self.combo_area.grid(row=0, column=1, padx=5, sticky='w')
        ttk.Label(self.frame_combos1, text="Distrito:").grid(row=0, column=2, padx=5, sticky='w')
        self.distrito_var = tk.StringVar()
        self.combo_distrito = AutocompleteCombobox(self.frame_combos1, textvariable=self.distrito_var, state="normal", width=20)
        self.combo_distrito.grid(row=0, column=3, padx=5, sticky='w')
        ttk.Label(self.frame_combos1, text="Tipo de Servicio:").grid(row=0, column=4, padx=5, sticky='w')
        self.tipo_servicio_var = tk.StringVar()
        self.combo_tipo_servicio = AutocompleteCombobox(self.frame_combos1, textvariable=self.tipo_servicio_var, state="normal", width=20)
        self.combo_tipo_servicio.grid(row=0, column=5, padx=5, sticky='w')
        ttk.Label(self.frame_combos1, text="Servicio:").grid(row=0, column=6, padx=5, sticky='w')
        self.servicio_var = tk.StringVar()
        self.combo_servicio = AutocompleteCombobox(self.frame_combos1, textvariable=self.servicio_var, state="normal", width=20)
        self.combo_servicio.grid(row=0, column=7, padx=5, sticky='w')

        # Segunda fila de combos
        self.frame_combos2 = ttk.Frame(self.frame_combos)
        self.frame_combos2.pack(fill="x", pady=5)
        
        # Grid DENTRO del frame_combos2 (esto es válido)
        ttk.Label(self.frame_combos2, text="Tipo de Insumo:").grid(row=0, column=0, padx=5, sticky='w')
        self.tipo_insumo_var = tk.StringVar()
        self.combo_tipo_insumo = AutocompleteCombobox(self.frame_combos2, textvariable=self.tipo_insumo_var, state="normal", width=20)
        self.combo_tipo_insumo.grid(row=0, column=1, padx=5, sticky='w')
        ttk.Label(self.frame_combos2, text="Insumo:").grid(row=0, column=2, padx=5, sticky='w')
        self.insumo_var = tk.StringVar()
        self.combo_insumo = AutocompleteCombobox(self.frame_combos2, textvariable=self.insumo_var, state="normal", width=20)
        self.combo_insumo.grid(row=0, column=3, padx=5, sticky='w')
        ttk.Label(self.frame_combos2, text="Presentación:").grid(row=0, column=4, padx=5, sticky='w')
        self.presentacion_var = tk.StringVar()
        self.combo_presentacion = AutocompleteCombobox(self.frame_combos2, textvariable=self.presentacion_var, state="normal", width=20)
        self.combo_presentacion.grid(row=0, column=5, padx=5, sticky='w')

        # Frame para el visor PDF (SOLO pack aquí y en sus hijos)
        self.pdf_frame = ttk.Frame(self.frame_principal)
        self.pdf_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.pdf_viewer = None

        # Frame para botones
        self.frame_botones = ttk.Frame(self.frame_principal)
        self.frame_botones.pack(fill="x", pady=10)
        
        # Crear un frame para contener los botones y usar grid dentro de él
        botones_grid = ttk.Frame(self.frame_botones)
        botones_grid.pack(fill="x")
        
        ttk.Button(botones_grid, text="Generar Vista Previa", command=self.generar_vista_previa).grid(row=0, column=0, padx=5)
        ttk.Button(botones_grid, text="Exportar a PDF", command=self.generar_pdf).grid(row=0, column=1, padx=5)
        ttk.Button(botones_grid, text="Exportar a Excel", command=self.generar_kardex).grid(row=0, column=2, padx=5)
        ttk.Button(botones_grid, text="Cerrar", command=self.cerrar_ventana).grid(row=0, column=3, padx=5)

        # Vincular eventos de cambio
        self.combo_area.bind('<<ComboboxSelected>>', self.cargar_distritos_por_area)
        self.combo_distrito.bind('<<ComboboxSelected>>', self.cargar_tipos_servicio)
        self.combo_tipo_servicio.bind('<<ComboboxSelected>>', self.cargar_servicios)
        self.combo_tipo_insumo.bind('<<ComboboxSelected>>', self.cargar_insumos)
        self.combo_insumo.bind('<<ComboboxSelected>>', self.actualizar_presentacion)

        # Cargar datos iniciales
        self.cargar_areas()
        self.distritos = []
        self.combo_distrito.set_completion_list([''])
        self.cargar_tipos_insumo()
        self.cargar_presentaciones()
            
    def cargar_areas(self):
        self.areas = obtener_areas()
        if self.areas:
            opciones = [''] + [a['nombre'] for a in self.areas]
            self.combo_area.set_completion_list(opciones)

    def cargar_distritos(self):
        self.distritos = obtener_distritos()
        if self.distritos:
            opciones = [''] + [d['nombre'] for d in self.distritos]
            self.combo_distrito.set_completion_list(opciones)
    
    def cargar_distritos_por_area(self, event=None):
        area_nombre = self.combo_area.get().strip()
        if area_nombre:
            area = next((a for a in self.areas if a['nombre'] == area_nombre), None)
            if area:
                from src.database.db_manager import obtener_distritos_por_area
                distritos = obtener_distritos_por_area(area['id'])
                self.distritos = distritos or []
                opciones = [''] + [d['nombre'] for d in self.distritos]
                self.combo_distrito.set_completion_list(opciones)
                # No borrar texto actual para no interferir con la escritura del usuario
                # self.combo_distrito.set('')  # <-- comentar o eliminar esta línea
            else:
                self.distritos = []
                self.combo_distrito.set_completion_list([''])
                self.combo_distrito.set('')
        else:
            self.distritos = []
            self.combo_distrito.set_completion_list([''])
            self.combo_distrito.set('')

    def cargar_tipos_servicio(self, event=None):
        self.combo_tipo_servicio.set('')
        distrito_nombre = self.combo_distrito.get().strip()
        if distrito_nombre:
            distrito = next((d for d in self.distritos if d['nombre'] == distrito_nombre), None)
            if distrito:
                self.tipos_servicio = obtener_tipos_servicio_por_distrito(distrito['id'])
                opciones = [''] + [t['descripcion'] for t in self.tipos_servicio]
                self.combo_tipo_servicio.set_completion_list(opciones)

    def cargar_servicios(self, event=None):
        self.combo_servicio.set('')
        tipo_servicio_desc = self.combo_tipo_servicio.get().strip()
        if tipo_servicio_desc:
            tipo_servicio = next((t for t in self.tipos_servicio if t['descripcion'] == tipo_servicio_desc), None)
            if tipo_servicio:
                servicios = obtener_servicios_por_tipo(tipo_servicio['id'])
                opciones = [''] + [s['nombre'] for s in servicios]
                self.combo_servicio.set_completion_list(opciones)

    def cargar_tipos_insumo(self):
        self.tipos_insumo = obtener_tipos_insumo()
        if self.tipos_insumo:
            opciones = [''] + [t['descripcion'] for t in self.tipos_insumo]
            self.combo_tipo_insumo.set_completion_list(opciones)

    def cargar_insumos(self, event=None):
        self.combo_insumo.set('')
        self.combo_presentacion.set('')
        tipo_insumo_desc = self.combo_tipo_insumo.get().strip()
        if tipo_insumo_desc:
            tipo_insumo = next((t for t in self.tipos_insumo if t['descripcion'] == tipo_insumo_desc), None)
            if tipo_insumo:
                self.insumos = obtener_insumos_por_tipo(tipo_insumo['id'])
                opciones = [''] + [i['nombre'] for i in self.insumos]
                self.combo_insumo.set_completion_list(opciones)
           
    def actualizar_presentacion(self, event=None):
        insumo_nombre = self.combo_insumo.get().strip()
        if insumo_nombre and self.insumos:
            insumo = next((i for i in self.insumos if i['nombre'] == insumo_nombre), None)
            if insumo:
                self.combo_presentacion.set(insumo['nombre_presentacion'] if 'nombre_presentacion' in insumo.keys() else '')
            else:
                self.combo_presentacion.set('')
        else:
            self.combo_presentacion.set('')

    def cargar_presentaciones(self):
        self.presentaciones = obtener_presentaciones()
        if self.presentaciones:
            opciones = [''] + [p['nombre'] for p in self.presentaciones]
            self.combo_presentacion.set_completion_list(opciones)

    def generar_vista_previa(self):
        try:
            # Validar fechas
            fecha_ini = datetime.strptime(self.fecha_inicial.get(), '%d/%m/%Y')
            fecha_fin = datetime.strptime(self.fecha_final.get(), '%d/%m/%Y')

            if fecha_fin < fecha_ini:
                messagebox.showerror("Error", "La fecha final debe ser mayor a la inicial")
                return

            # Validar selección de insumo
            if not self.combo_insumo.get():
                messagebox.showerror("Error", "Debe seleccionar un insumo")
                return

            # Obtener datos
            self.movimientos_data = obtener_movimientos_kardex(
                fecha_ini.strftime('%Y-%m-%d'),
                fecha_fin.strftime('%Y-%m-%d'),
                self.combo_distrito.get(),
                self.combo_tipo_servicio.get(),
                self.combo_servicio.get(),
                self.combo_tipo_insumo.get(),
                self.combo_insumo.get(),
                self.combo_presentacion.get()
            )

            if not self.movimientos_data:
                messagebox.showinfo("Info", "No hay datos para mostrar")
                return

            # Generar PDF temporal
            import tempfile
            import os

            # Crear archivo temporal
            temp_dir = tempfile.gettempdir()
            self.temp_pdf_path = os.path.join(temp_dir, "vista_previa_kardex.pdf")

            # Generar el PDF en el archivo temporal
            self.generar_pdf(self.temp_pdf_path, es_vista_previa=True)

            # Importar las bibliotecas necesarias
            import fitz  # PyMuPDF
            from PIL import Image, ImageTk

            # Limpiar el frame PDF si existe
            if hasattr(self, 'pdf_frame'):
                for widget in self.pdf_frame.winfo_children():
                    widget.destroy()

            # Asegurarse de que el frame PDF existe
            if not hasattr(self, 'pdf_frame'):
                self.pdf_frame = ttk.Frame(self.frame_principal)
                self.pdf_frame.pack(fill="both", expand=True, padx=5, pady=5)

            # Crear un canvas con scrollbars dentro del pdf_frame
            canvas_frame = ttk.Frame(self.pdf_frame)
            canvas_frame.pack(fill="both", expand=True)

            # Scrollbars
            h_scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal")
            h_scrollbar.pack(side="bottom", fill="x")

            v_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical")
            v_scrollbar.pack(side="right", fill="y")

            # Canvas
            canvas = tk.Canvas(canvas_frame,
                            xscrollcommand=h_scrollbar.set,
                            yscrollcommand=v_scrollbar.set)
            canvas.pack(side="left", fill="both", expand=True)

            # Configurar scrollbars
            h_scrollbar.config(command=canvas.xview)
            v_scrollbar.config(command=canvas.yview)

            # Abrir el PDF con PyMuPDF
            doc = fitz.open(self.temp_pdf_path)

            # Variables para controlar la página actual
            self.current_page = 0
            self.total_pages = len(doc)

            # Frame para controles de navegación
            control_frame = ttk.Frame(self.pdf_frame)
            control_frame.pack(fill="x", pady=5)

            # Función para cambiar de página
            def change_page(delta):
                self.current_page = max(0, min(self.current_page + delta, self.total_pages - 1))
                display_page()
                page_label.config(text=f"Página {self.current_page + 1} de {self.total_pages}")

            def show_print_options():
                # Crear ventana de opciones de impresión
                print_window = tk.Toplevel(self.parent)
                print_window.title("Opciones de Impresión")
                print_window.geometry("450x470")
                print_window.resizable(False, False)
                print_window.transient(self.parent)  # Hacer que sea modal
                print_window.grab_set()  # Bloquear otras ventanas

                # Centrar la ventana
                print_window.update_idletasks()
                width = print_window.winfo_width()
                height = print_window.winfo_height()
                x = (print_window.winfo_screenwidth() // 2) - (width // 2)
                y = (print_window.winfo_screenheight() // 2) - (height // 2)
                print_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))

                # Frame principal
                main_frame = ttk.Frame(print_window, padding=20)
                main_frame.pack(fill="both", expand=True)

                # Título
                ttk.Label(main_frame, text="Configuración de Impresión", font=("Helvetica", 12, "bold")).pack(pady=10)

                # Frame para opciones de página
                page_frame = ttk.LabelFrame(main_frame, text="Opciones de Página", padding=10)
                page_frame.pack(fill="x", pady=10)

                # Variables para opciones de página
                orientation_var = tk.StringVar(value="Horizontal")
                copies_var = tk.StringVar(value="1")
                all_pages_var = tk.BooleanVar(value=True)
                page_range_var = tk.StringVar(value=f"1-{self.total_pages}")

                # Orientación
                ttk.Label(page_frame, text="Orientación:").grid(row=0, column=0, sticky="w", pady=5)
                ttk.Radiobutton(page_frame, text="Horizontal", variable=orientation_var, value="Horizontal").grid(row=0, column=1, sticky="w")
                ttk.Radiobutton(page_frame, text="Vertical", variable=orientation_var, value="Vertical").grid(row=0, column=2, sticky="w")

                # Copias
                ttk.Label(page_frame, text="Número de copias:").grid(row=1, column=0, sticky="w", pady=5)
                copies_spinbox = ttk.Spinbox(page_frame, from_=1, to=10, textvariable=copies_var, width=5)
                copies_spinbox.grid(row=1, column=1, sticky="w")

                # Rango de páginas
                ttk.Radiobutton(page_frame, text="Todas las páginas", variable=all_pages_var, value=True).grid(row=2, column=0, sticky="w", pady=5)
                ttk.Radiobutton(page_frame, text="Rango:", variable=all_pages_var, value=False).grid(row=3, column=0, sticky="w")

                range_entry = ttk.Entry(page_frame, textvariable=page_range_var, width=15)
                range_entry.grid(row=3, column=1, sticky="w")
                ttk.Label(page_frame, text="(ej: 1-5, 8, 11-13)").grid(row=3, column=2, sticky="w")

                # Frame para selección de impresora
                printer_frame = ttk.LabelFrame(main_frame, text="Impresora", padding=10)
                printer_frame.pack(fill="x", pady=10)

                # Obtener lista de impresoras disponibles
                import subprocess
                import re

                # Función para obtener impresoras en Windows
                def get_printers():
                    try:
                        # Intentar obtener impresoras con wmic (Windows)
                        result = subprocess.run(['wmic', 'printer', 'get', 'name'],
                                            capture_output=True, text=True, check=False)
                        if result.returncode == 0:
                            printers = result.stdout.strip().split('\n')[1:]  # Omitir la primera línea (encabezado)
                            return [p.strip() for p in printers if p.strip()]
                        else:
                            # Alternativa: usar lpstat (Linux/macOS)
                            result = subprocess.run(['lpstat', '-p'], capture_output=True, text=True, check=False)
                            if result.returncode == 0:
                                pattern = r'printer (.*) is'
                                printers = re.findall(pattern, result.stdout)
                                return printers
                    except Exception:
                        pass

                    # Si todo falla, devolver una lista predeterminada
                    return ["Impresora predeterminada"]

                # Obtener impresoras
                printers = get_printers()

                # Variable para la impresora seleccionada
                printer_var = tk.StringVar(value=printers[0] if printers else "Impresora predeterminada")

                # Combobox para seleccionar impresora
                ttk.Label(printer_frame, text="Seleccione impresora:").pack(anchor="w", pady=5)
                printer_combo = ttk.Combobox(printer_frame, textvariable=printer_var, state="readonly", width=40)
                printer_combo['values'] = printers
                printer_combo.pack(fill="x", pady=5)

                # Frame para botones
                button_frame = ttk.Frame(main_frame)
                button_frame.pack(fill="x", pady=20)

                # Función para imprimir
                def print_document():
                    try:
                        # Crear una copia temporal del PDF con la orientación correcta
                        import fitz  # PyMuPDF
                        import tempfile
                        import os
                        import subprocess
                        import shutil

                        # Crear un nuevo archivo temporal para el PDF modificado
                        temp_dir = tempfile.gettempdir()
                        modified_pdf_path = os.path.join(temp_dir, "modified_kardex.pdf")

                        # Abrir el PDF original
                        doc = fitz.open(self.temp_pdf_path)

                        # Modificar la orientación según la selección
                        for page in doc:
                            if orientation_var.get() == "Vertical":
                                # Rotar 90 grados si se seleccionó vertical (el PDF original es horizontal)
                                page.set_rotation(90)
                            else:
                                # Mantener orientación horizontal (predeterminada)
                                page.set_rotation(0)

                        # Guardar el PDF modificado
                        doc.save(modified_pdf_path)
                        doc.close()

                        # Obtener el número de copias
                        copies = int(copies_var.get())

                        # Obtener la impresora seleccionada
                        printer = printer_var.get()

                        # Mostrar mensaje de espera
                        wait_window = tk.Toplevel(print_window)
                        wait_window.title("Imprimiendo")
                        wait_window.geometry("300x100")
                        wait_window.transient(print_window)
                        wait_window.grab_set()

                        # Centrar ventana de espera
                        wait_window.update_idletasks()
                        w_width = wait_window.winfo_width()
                        w_height = wait_window.winfo_height()
                        w_x = (wait_window.winfo_screenwidth() // 2) - (w_width // 2)
                        w_y = (wait_window.winfo_screenheight() // 2) - (w_height // 2)
                        wait_window.geometry('{}x{}+{}+{}'.format(w_width, w_height, w_x, w_y))

                        ttk.Label(wait_window, text="Enviando documento a la impresora...\nPor favor espere.",
                                justify="center").pack(pady=20)
                        wait_window.update()

                        success = False
                        error_messages = []

                        # Lista de comandos de impresión a intentar
                        print_commands = [
                            # 1. lpr - Comando estándar de impresión en Linux
                            lambda: subprocess.run(
                                ['lpr', '-P', printer, '-#', str(copies), modified_pdf_path] if printer != "Impresora predeterminada"
                                else ['lpr', '-#', str(copies), modified_pdf_path],
                                check=True
                            ),

                            # 2. lp - Alternativa a lpr en algunos sistemas
                            lambda: subprocess.run(
                                ['lp', '-d', printer, '-n', str(copies), modified_pdf_path] if printer != "Impresora predeterminada"
                                else ['lp', '-n', str(copies), modified_pdf_path],
                                check=True
                            ),

                            # 3. cupsdoprint - Otra alternativa
                            lambda: subprocess.run(
                                ['cupsdoprint', '-P', printer, '-n', str(copies), modified_pdf_path] if printer != "Impresora predeterminada"
                                else ['cupsdoprint', '-n', str(copies), modified_pdf_path],
                                check=True
                            ),

                            # 4. Usar evince para imprimir (visor de PDF común en Linux)
                            lambda: subprocess.run(
                                ['evince', '--print-settings', f"copies={copies}", '--print', modified_pdf_path],
                                check=True
                            )
                        ]

                        # Intentar cada comando hasta que uno funcione
                        for cmd_func in print_commands:
                            try:
                                cmd_func()
                                success = True
                                break
                            except Exception as e:
                                error_messages.append(str(e))
                                continue

                        # Cerrar ventana de espera
                        wait_window.destroy()

                        if success:
                            messagebox.showinfo("Impresión", "Documento enviado a la impresora")
                            print_window.destroy()
                        else:
                            # Si todos los métodos fallan, ofrecer abrir el PDF manualmente
                            error_detail = "\n".join(error_messages)
                            if messagebox.askyesno("Error de impresión",
                                                f"No se pudo imprimir automáticamente.\n\n¿Desea abrir el PDF para imprimirlo manualmente?"):
                                # Intentar abrir con varios métodos
                                try:
                                    # Intentar con xdg-open primero (estándar en Linux)
                                    if shutil.which('xdg-open'):
                                        subprocess.run(['xdg-open', modified_pdf_path])
                                    # Si no está disponible, intentar con el módulo webbrowser
                                    else:
                                        import webbrowser
                                        webbrowser.open('file://' + os.path.abspath(modified_pdf_path))
                                except Exception as e:
                                    messagebox.showerror("Error", f"No se pudo abrir el PDF: {str(e)}")

                    except Exception as e:
                        messagebox.showerror("Error", f"Error al preparar el documento: {str(e)}")

                # Botones
                ttk.Button(button_frame, text="Imprimir", width=10, command=print_document).pack(side="right", padx=5)
                ttk.Button(button_frame, text="Cancelar", width=10, command=print_window.destroy).pack(side="right", padx=5)

            # Botones de navegación
            ttk.Button(control_frame, text="<<", command=lambda: change_page(-1)).pack(side="left", padx=5)
            page_label = ttk.Label(control_frame, text=f"Página 1 de {self.total_pages}")
            page_label.pack(side="left", padx=10)
            ttk.Button(control_frame, text=">>", command=lambda: change_page(1)).pack(side="left", padx=5)

            # Botón de impresión - Agregar texto junto al ícono
            print_button = ttk.Button(control_frame, text="🖨️ Imprimir", command=show_print_options)
            print_button.pack(side="right", padx=10)

            # Función para mostrar la página actual
            def display_page():
                # Limpiar canvas
                canvas.delete("all")

                # Obtener la página actual
                page = doc.load_page(self.current_page)

                # Renderizar a imagen
                pix = page.get_pixmap(matrix=fitz.Matrix(1.2, 1.2))  # Escala 1.2 para mejor calidad

                # Convertir a formato PIL
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # Convertir a formato Tkinter
                tk_img = ImageTk.PhotoImage(image=img)

                # Guardar referencia para evitar que sea eliminada por el recolector de basura
                canvas.image = tk_img

                # Mostrar en canvas
                canvas.create_image(0, 0, anchor="nw", image=tk_img)

                # Configurar región de desplazamiento
                canvas.config(scrollregion=canvas.bbox("all"))

            # Mostrar la primera página
            display_page()

        except Exception as e:
            # Capturar y mostrar cualquier error que ocurra
            import traceback
            error_detallado = traceback.format_exc()
            print(f"Error detallado:\n{error_detallado}")  # Para debugging
            messagebox.showerror(
                "Error",
                f"Error al generar vista previa:\n{str(e)}\n\nPor favor, verifique los datos e intente nuevamente."
            )

    def generar_pdf(self, ruta_pdf, es_vista_previa=False):
        if not self.movimientos_data:
            messagebox.showwarning("Advertencia", "No hay datos para mostrar")
            return

        try:
            doc = SimpleDocTemplate(
                ruta_pdf,
                pagesize=landscape(letter),
                rightMargin=36,
                leftMargin=36,
                topMargin=36,
                bottomMargin=36
            )

            elements = []
            styles = getSampleStyleSheet()

            # Estilos personalizados
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                alignment=1,
                spaceAfter=15,
                fontSize=12
            )
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading2'],
                alignment=1,
                spaceAfter=10,
                fontSize=10
            )
            timestamp_style = ParagraphStyle(
                'TimestampStyle',
                parent=styles['Normal'],
                alignment=1,
                spaceAfter=15,
                fontSize=9
            )

            # Títulos principales
            elements.append(Paragraph(
                "DIRECCIÓN DEPARTAMENTAL DE REDES INTEGRADAS DE SERVICIOS DE SALUD DE GUATEMALA,",
                title_style))
            elements.append(Paragraph("ÁREA NOR ORIENTE", subtitle_style))
            elements.append(Paragraph("TARJETA DE CONTROL DE SUMINISTROS", subtitle_style))
            elements.append(Paragraph(
                f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                timestamp_style))

            # Filtros en dos filas horizontales
            filtros = [
                f"Área: {self.combo_area.get()}",
                f"Distrito: {self.combo_distrito.get()}",
                f"Tipo de Servicio: {self.combo_tipo_servicio.get()}",
                f"Servicio: {self.combo_servicio.get()}",
                f"Insumo: {self.combo_insumo.get()}",
                f"Presentación: {self.combo_presentacion.get()}"
            ]

            # Crear estilo para alineación izquierda
            left_style = ParagraphStyle(
                name="LeftAlign",
                alignment=0,  # 0 = LEFT
                fontSize=9,
                fontName='Helvetica'
            )

            # Crear tabla con una sola fila y 5 columnas
            data_filtros = [[Paragraph(item, left_style) for item in filtros]]

            # Anchos de columna (ajustar según necesidad)
            col_widths = [125, 125, 125, 125, 125]

            table_filtros = Table(data_filtros, colWidths=col_widths)
            table_filtros.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey)
            ]))

            elements.append(table_filtros)
            elements.append(Spacer(1, 30))

            # Encabezados de la tabla
            headers = [
                'Fecha',
                'Referencia',
                'Remitente/\nDestinatario',
                'Entrada',
                'Precio\nUnitario',
                'Valor\nTotal',
                'Lote',
                'Fecha\nVencimiento',
                'Salidas',
                'Reajustes\n(+) (-)',
                'Cantidad',
                'Saldo',
                'Observaciones'
            ]

            # Datos del reporte
            data = [headers]
            for mov in self.movimientos_data:
                row = [
                    mov['fecha'],
                    mov['referencia'] or "",
                    mov['tipo_movimiento'],
                    self.formato_float(mov['entrada']),
                    self.formato_float(mov['precio_unitario']),
                    self.formato_float(mov['valor_total']),
                    mov['lote'] or "",
                    mov['fecha_vencimiento'] or "",
                    mov['salida'],
                    f"{mov['reajuste']:+.2f}" if mov['reajuste'] != 0 else "",
                    self.formato_float(mov['cantidad_col']),
                    self.formato_float(mov['saldo']),
                    mov['observaciones'] or ""
                ]
                data.append(row)

            # Crear tabla con formato y anchos ajustados
            colWidths = [
                0.7*inch,  # Fecha
                0.8*inch,  # Ref.
                1.5*inch,  # Remitente
                0.6*inch,  # Entrada
                0.7*inch,  # P.Unit.
                0.7*inch,  # V.Total
                0.8*inch,  # Lote
                0.7*inch,  # F.Venc.
                0.6*inch,  # Salidas
                0.6*inch,  # Reaj.
                0.6*inch,  # Cant.
                0.6*inch,  # Saldo
                1.1*inch   # Obs.
            ]

            # Modificar el estilo de la tabla
            table = Table(data, colWidths=colWidths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
                ('TEXTCOLOR', (0,0), (-1,0), colors.black),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 7),
                ('FONTSIZE', (0,1), (-1,-1), 7),
                ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING', (0,0), (-1,0), 6),
                ('BOTTOMPADDING', (0,0), (-1,0), 6),
                ('TOPPADDING', (0,1), (-1,-1), 2),
                ('BOTTOMPADDING', (0,1), (-1,-1), 2),
                ('LEFTPADDING', (0,0), (-1,-1), 2),
                ('RIGHTPADDING', (0,0), (-1,-1), 2),
                ('WORDWRAP', (0,0), (-1,0), True),
            ]))

            elements.append(table)
            doc.build(elements)

            if not es_vista_previa:
                messagebox.showinfo("Éxito", f"PDF guardado en:\n{ruta_pdf}")

        except Exception as e:
            messagebox.showerror("Error", f"Error al generar PDF: {str(e)}")

    def generar_kardex(self):
        try:
            # Validar fechas
            fecha_ini = datetime.strptime(self.fecha_inicial.get(), '%d/%m/%Y')
            fecha_fin = datetime.strptime(self.fecha_final.get(), '%d/%m/%Y')

            if fecha_fin < fecha_ini:
                messagebox.showerror("Error", "La fecha final debe ser mayor a la inicial")
                return

            # Validar selección de insumo
            if not self.combo_insumo.get():
                messagebox.showerror("Error", "Debe seleccionar un insumo")
                return

            # Obtener datos para el reporte
            movimientos = obtener_movimientos_kardex(
                fecha_ini.strftime('%Y-%m-%d'),
                fecha_fin.strftime('%Y-%m-%d'),
                self.combo_distrito.get(),
                self.combo_tipo_servicio.get(),
                self.combo_servicio.get(),
                self.combo_tipo_insumo.get(),
                self.combo_insumo.get(),
                self.combo_presentacion.get()
            )

            if not movimientos:
                messagebox.showinfo("Info", "No hay datos para mostrar")
                return

            # Crear DataFrame y generar Excel
            self.generar_excel(movimientos)

        except Exception as e:
            messagebox.showerror("Error", f"Error al generar reporte: {str(e)}")

    def generar_excel(self, movimientos):
        # Filtrar y renombrar columnas
        columnas_relevantes = [
            'fecha', 'referencia', 'tipo_movimiento', 'entrada',
            'precio_unitario', 'valor_total', 'lote', 'fecha_vencimiento',
            'salida', 'reajuste', 'cantidad_col', 'saldo', 'observaciones'
        ]
        df = pd.DataFrame(movimientos)[columnas_relevantes]
        df.columns = [
            'Fecha', 'Referencia', 'Remitente/Destinatario', 'Entrada',
            'Precio Unitario', 'Valor Total', 'Lote', 'Fecha Vencimiento',
            'Salidas', 'Reajustes', 'Cantidad', 'Saldo', 'Observaciones'
        ]
        
        # Generar nombre de archivo con fecha y hora
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"Reporte_Kardex_{timestamp}.xlsx"

        # Ruta a la carpeta Descargas
        downloads_path = os.path.expanduser("~/Downloads")
        full_path = os.path.join(downloads_path, file_name)

        # Crear archivo Excel
        writer = pd.ExcelWriter(full_path, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Kardex', startrow=8, index=False)

        # Obtener el objeto workbook y worksheet
        workbook = writer.book
        worksheet = writer.sheets['Kardex']

        # Mejorar el formato de los títulos
        title_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 12,
            'text_wrap': True
        })

        subtitle_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 10,
            'text_wrap': True
        })
        
        timestamp_format = workbook.add_format({ 
        'align': 'center',
        'font_size': 9
        })
        
        # Ajustar altura de las filas de títulos
        worksheet.set_row(0, 30)  # Título principal
        worksheet.set_row(1, 25)  # Subtítulo 1
        worksheet.set_row(2, 25)  # Subtítulo 2
        worksheet.set_row(3, 20)  # Fecha/hora
        worksheet.set_row(5, 25)  # Fila de filtros

        # Ajustar altura de la fila de encabezados
        worksheet.set_row(8, 40)  # Encabezados de columnas (aumentado a 40)

        # Formato para los datos con altura ajustada
        data_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'font_size': 9
        })

        # Aplicar formato a los datos
        for row in range(9, len(df) + 9):
            worksheet.set_row(row, 20, data_format)

        # Ajustar el rango de las celdas combinadas para los títulos
        worksheet.merge_range('A1:M1',
            'DIRECCIÓN DEPARTAMENTAL DE REDES INTEGRADAS DE SERVICIOS DE SALUD DE GUATEMALA,',
            title_format)
        worksheet.merge_range('A2:M2', 'ÁREA NOR ORIENTE', subtitle_format)
        worksheet.merge_range('A3:M3', 'TARJETA DE CONTROL DE SUMINISTROS', subtitle_format)
        worksheet.merge_range('A4:M4',
            f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            timestamp_format)

        # Filtros en filas separadas
        worksheet.merge_range('A6:B6', f"Área: {self.combo_area.get()}", subtitle_format)
        worksheet.merge_range('C6:D6', f"Distrito: {self.combo_distrito.get()}", subtitle_format)
        worksheet.merge_range('E6:F6', f"Tipo de Servicio: {self.combo_tipo_servicio.get()}", subtitle_format)
        worksheet.merge_range('G6:H6', f"Servicio: {self.combo_servicio.get()}", subtitle_format)
        worksheet.merge_range('I6:J6', f"Insumo: {self.combo_insumo.get()}", subtitle_format)
        worksheet.merge_range('K6:M6', f"Presentación: {self.combo_presentacion.get()}", subtitle_format)

        # Configuración de página
        worksheet.set_landscape()
        worksheet.set_paper(9) 
        worksheet.fit_to_pages(1, 1)
        
        # Formato para el contenido
        content_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 9,
            'text_wrap': True
        })

        # Formato para los encabezados
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 9,
            'bg_color': '#ADD8E6',  # Light blue
            'text_wrap': True,
            'border': 1
        })

        # Aplicar formato a los encabezados
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(8, col_num, value, header_format)

        # Ajustar anchos de columna
        worksheet.set_column('A:A', 9)     # Fecha
        worksheet.set_column('B:B', 11)    # Referencia
        worksheet.set_column('C:C', 18)    # Remitente/Destinatario
        worksheet.set_column('D:D', 8)     # Entrada
        worksheet.set_column('E:E', 9)     # Precio Unitario
        worksheet.set_column('F:F', 9)     # Valor Total
        worksheet.set_column('G:G', 10)    # Lote
        worksheet.set_column('H:H', 10)    # Fecha Vencimiento
        worksheet.set_column('I:I', 8)     # Salidas
        worksheet.set_column('J:J', 8)     # Reajustes
        worksheet.set_column('K:K', 8)     # Cantidad
        worksheet.set_column('L:L', 8)     # Saldo
        worksheet.set_column('M:M', 15)    # Observaciones
        
        # Aplicar formato al contenido
        worksheet.set_column('A:M', None, content_format)

        # Ajustar altura de las filas
        worksheet.set_default_row(20)  # Altura predeterminada para todas las filas

        # Guardar archivo
        writer.close()
        messagebox.showinfo("Éxito", f"Reporte guardado en:\n{full_path}")

    def cerrar_ventana(self):
        if messagebox.askyesno("Confirmar", "¿Está seguro que desea cerrar esta ventana?"):
            # Limpiar el frame principal
            for widget in self.parent.winfo_children():
                widget.destroy()
            # Mostrar la pantalla de bienvenida
            if self.main_window:
                self.main_window.show_welcome_screen()