import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
from ttkwidgets.autocomplete import AutocompleteCombobox

# ReportLab para PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

import pandas as pd
import fitz  # PyMuPDF
from PIL import Image, ImageTk
from ttkwidgets.autocomplete import AutocompleteCombobox

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.db_manager import (
    obtener_areas,
    obtener_distritos_por_area,
    obtener_tipos_servicio_por_distrito,
    obtener_servicios_por_tipo,
    obtener_tipos_insumo,
    obtener_insumos_por_tipo,
    obtener_presentaciones,
    obtener_movimientos_kardex,
    obtener_id_area,
    obtener_id_distrito,
    obtener_id_tipo_servicio,
    obtener_id_tipo_insumo
)

class ReporteDemandaReal:
    def __init__(self, parent_frame, main_window=None):
        self.parent = parent_frame
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        self.frame_principal = ttk.LabelFrame(self.parent, text="Filtros de Reporte Demanda Real")
        self.frame_principal.pack(fill="both", expand=True, padx=10, pady=5)

        # Filtros: Área, Distrito, Tipo Servicio, Servicio, Tipo Insumo, Insumo, Presentación
        self.frame_filtros = ttk.Frame(self.frame_principal)
        self.frame_filtros.pack(fill="x", padx=5, pady=5)

        # Primera fila de filtros
        ttk.Label(self.frame_filtros, text="Área:").grid(row=0, column=0, padx=5, pady=2, sticky='w')
        self.area_var = tk.StringVar()
        self.combo_area = AutocompleteCombobox(self.frame_filtros, textvariable=self.area_var, width=20, state="normal")
        self.combo_area.grid(row=0, column=1, padx=5, pady=2, sticky='w')

        ttk.Label(self.frame_filtros, text="Distrito:").grid(row=0, column=2, padx=5, pady=2, sticky='w')
        self.distrito_var = tk.StringVar()
        self.combo_distrito = AutocompleteCombobox(self.frame_filtros, textvariable=self.distrito_var, width=20, state="normal")
        self.combo_distrito.grid(row=0, column=3, padx=5, pady=2, sticky='w')

        ttk.Label(self.frame_filtros, text="Tipo de Servicio:").grid(row=0, column=4, padx=5, pady=2, sticky='w')
        self.tipo_servicio_var = tk.StringVar()
        self.combo_tipo_servicio = AutocompleteCombobox(self.frame_filtros, textvariable=self.tipo_servicio_var, width=20, state="normal")
        self.combo_tipo_servicio.grid(row=0, column=5, padx=5, pady=2, sticky='w')

        ttk.Label(self.frame_filtros, text="Servicio:").grid(row=0, column=6, padx=5, pady=2, sticky='w')
        self.servicio_var = tk.StringVar()
        self.combo_servicio = AutocompleteCombobox(self.frame_filtros, textvariable=self.servicio_var, width=20, state="normal")
        self.combo_servicio.grid(row=0, column=7, padx=5, pady=2, sticky='w')

        # Segunda fila de filtros
        ttk.Label(self.frame_filtros, text="Tipo de Insumo:").grid(row=1, column=0, padx=5, pady=2, sticky='w')
        self.tipo_insumo_var = tk.StringVar()
        self.combo_tipo_insumo = AutocompleteCombobox(self.frame_filtros, textvariable=self.tipo_insumo_var, width=20, state="normal")
        self.combo_tipo_insumo.grid(row=1, column=1, padx=5, pady=2, sticky='w')

        ttk.Label(self.frame_filtros, text="Insumo:").grid(row=1, column=2, padx=5, pady=2, sticky='w')
        self.insumo_var = tk.StringVar()
        self.combo_insumo = AutocompleteCombobox(self.frame_filtros, textvariable=self.insumo_var, width=20, state="normal")
        self.combo_insumo.grid(row=1, column=3, padx=5, pady=2, sticky='w')

        ttk.Label(self.frame_filtros, text="Presentación:").grid(row=1, column=4, padx=5, pady=2, sticky='w')
        self.presentacion_var = tk.StringVar()
        self.combo_presentacion = AutocompleteCombobox(self.frame_filtros, textvariable=self.presentacion_var, width=20, state="normal")
        self.combo_presentacion.grid(row=1, column=5, padx=5, pady=2, sticky='w')
        
        # Frame para visor PDF (nuevo)
        self.pdf_frame = ttk.Frame(self.frame_principal)
        self.pdf_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Botones
        self.frame_botones = ttk.Frame(self.frame_principal)
        self.frame_botones.pack(fill="x", pady=10)

        # Crear un frame interno para organizar los botones en una fila
        botones_grid = ttk.Frame(self.frame_botones)
        botones_grid.pack(fill="x")

        # Botones
        ttk.Button(botones_grid, text="Generar Vista Previa", command=self.generar_reporte).grid(row=0, column=0, padx=5)
        ttk.Button(botones_grid, text="Exportar a PDF", command=self.exportar_pdf).grid(row=0, column=1, padx=5)
        ttk.Button(botones_grid, text="Exportar a Excel", command=self.exportar_excel).grid(row=0, column=2, padx=5)
        ttk.Button(botones_grid, text="Cerrar", command=self.cerrar_ventana).grid(row=0, column=3, padx=5)

        # Vincular eventos para cargar combos dependientes
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
        areas = obtener_areas()
        lista_areas = [a['nombre'] for a in areas]
        self.combo_area.set_completion_list(lista_areas)

    def cargar_distritos_por_area(self, event=None):
        area_seleccionada = self.combo_area.get()
        if not area_seleccionada:
            self.combo_distrito.set_completion_list([])
            return
        id_area = obtener_id_area(area_seleccionada)
        distritos = obtener_distritos_por_area(id_area)
        lista_distritos = [d['nombre'] for d in distritos]
        self.combo_distrito.set_completion_list(lista_distritos)
        self.combo_distrito.set('')

    def cargar_tipos_servicio(self, event=None):
        distrito_seleccionado = self.combo_distrito.get()
        if not distrito_seleccionado:
            self.combo_tipo_servicio.set_completion_list([])
            return
        id_distrito = obtener_id_distrito(distrito_seleccionado)
        tipos_servicio = obtener_tipos_servicio_por_distrito(id_distrito)
        lista_tipos = [t['descripcion'] for t in tipos_servicio]
        self.combo_tipo_servicio.set_completion_list(lista_tipos)
        self.combo_tipo_servicio.set('')

    def cargar_servicios(self, event=None):
        tipo_servicio_seleccionado = self.combo_tipo_servicio.get()
        if not tipo_servicio_seleccionado:
            self.combo_servicio.set_completion_list([])
            return
        id_tipo_servicio = obtener_id_tipo_servicio(tipo_servicio_seleccionado)
        servicios = obtener_servicios_por_tipo(id_tipo_servicio)
        lista_servicios = [s['nombre'] for s in servicios]
        self.combo_servicio.set_completion_list(lista_servicios)
        self.combo_servicio.set('')

    def cargar_tipos_insumo(self):
        tipos_insumo = obtener_tipos_insumo()
        lista_tipos = [t['descripcion'] for t in tipos_insumo]
        self.combo_tipo_insumo.set_completion_list(lista_tipos)

    def cargar_insumos(self, event=None):
        tipo_insumo_seleccionado = self.combo_tipo_insumo.get()
        if not tipo_insumo_seleccionado:
            self.combo_insumo.set_completion_list([])
            return
        id_tipo_insumo = obtener_id_tipo_insumo(tipo_insumo_seleccionado)
        insumos = obtener_insumos_por_tipo(id_tipo_insumo)
        lista_insumos = [i['nombre'] for i in insumos]
        self.combo_insumo.set_completion_list(lista_insumos)
        self.combo_insumo.set('')

    def cargar_presentaciones(self):
        presentaciones = obtener_presentaciones()
        lista_presentaciones = [p['nombre'] for p in presentaciones]
        self.combo_presentacion.set_completion_list(lista_presentaciones)

    def actualizar_presentacion(self, event=None):
        insumo_seleccionado = self.combo_insumo.get()
        if not insumo_seleccionado:
            self.combo_presentacion.set('')
            return
        tipo_insumo_seleccionado = self.combo_tipo_insumo.get()
        id_tipo_insumo = obtener_id_tipo_insumo(tipo_insumo_seleccionado)
        insumos = obtener_insumos_por_tipo(id_tipo_insumo)
        for insumo in insumos:
            if insumo['nombre'] == insumo_seleccionado:
                self.combo_presentacion.set(insumo['nombre_presentacion'] if 'nombre_presentacion' in insumo else '')
                return
        self.combo_presentacion.set('')

    def procesar_datos(self, movimientos, fecha_ini, fecha_fin):
        datos_procesados = []
        for mov in movimientos:
            datos_procesados.append({
                'codigo': mov.get('codigo', ''),
                'nombre_insumo': mov.get('insumo_nombre', ''),
                'presentacion': mov.get('nombre_presentacion', ''),
                'fecha': mov.get('fecha', ''),
                'tipo_movimiento': mov.get('tipo_movimiento', ''),
                'cantidad': mov.get('cantidad', 0),
                'existencia': mov.get('existencia', 0),  # Asegúrate de tener este dato
                'reajuste': mov.get('reajuste', 0)      # Asegúrate de tener este dato
            })
        return datos_procesados

    def exportar_excel(self):
        if not hasattr(self, 'dias') or not hasattr(self, 'datos'):
            messagebox.showerror("Error", "Primero debe generar la vista previa del reporte.")
            return

        df = pd.DataFrame.from_dict(self.datos, orient='index')
        df.insert(0, 'Insumo', df.index)
        df.reset_index(drop=True, inplace=True)

        downloads_path = os.path.expanduser("~/Downloads")
        full_path = os.path.join(downloads_path, f"Reporte_Demanda_Real_{self.periodo_str}.xlsx")

        try:
            df.to_excel(full_path, index=False)
            messagebox.showinfo("Éxito", f"Reporte exportado a Excel: {full_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar Excel: {str(e)}")

    def exportar_pdf(self):
        if not hasattr(self, 'temp_pdf_path') or not self.temp_pdf_path:
            messagebox.showerror("Error", "Primero debe generar la vista previa del reporte.")
            return

        downloads_path = os.path.expanduser("~/Downloads")
        full_path = os.path.join(downloads_path, f"Reporte_Demanda_Real_{self.periodo_str}.pdf")

        try:
            import shutil
            shutil.copy2(self.temp_pdf_path, full_path)
            messagebox.showinfo("Éxito", f"Reporte exportado a PDF: {full_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar PDF: {str(e)}")

    def generar_pdf(self, datos_movimientos, ruta_pdf):
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import legal, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from datetime import datetime, timedelta

        # Calcular rango fechas: 26 mes anterior a 25 mes actual
        hoy = datetime.now()
        if hoy.day >= 26:
            fecha_inicio = datetime(hoy.year, hoy.month, 26) - timedelta(days=30)
            fecha_fin = datetime(hoy.year, hoy.month, 25) + timedelta(days=30)
        else:
            mes_actual = hoy.month
            anio_actual = hoy.year
            if mes_actual == 1:
                mes_anterior = 12
                anio_anterior = anio_actual - 1
            else:
                mes_anterior = mes_actual - 1
                anio_anterior = anio_actual
            fecha_inicio = datetime(anio_anterior, mes_anterior, 26)
            fecha_fin = datetime(anio_actual, mes_actual, 25)

        # Generar lista de días hábiles (lunes a viernes) para columnas
        dias = []
        fecha_iter = fecha_inicio
        while fecha_iter <= fecha_fin:
            if fecha_iter.weekday() < 5:  # 0=lunes, ..., 4=viernes
                dias.append(fecha_iter.day)
            fecha_iter += timedelta(days=1)

        # Agrupar datos por insumo (codigo, nombre+presentacion)
        insumos = {}
        for mov in datos_movimientos:
            codigo = mov.get('codigo', '')
            nombre = mov.get('nombre_insumo', '')
            presentacion = mov.get('presentacion', '')
            key = (codigo, f"{nombre} {presentacion}".strip())
            if key not in insumos:
                insumos[key] = {
                    'entregado': {d:0 for d in dias},
                    'no_entregado': {d:0 for d in dias},
                    'existencia': mov.get('existencia', 0),
                    'reajuste': mov.get('reajuste', 0)
                }
            fecha_mov = datetime.strptime(mov['fecha'], '%Y-%m-%d')
            dia_mov = fecha_mov.day
            if fecha_inicio <= fecha_mov <= fecha_fin:
                tipo = mov.get('tipo_movimiento', '').upper()
                cantidad = mov.get('cantidad', 0)
                if tipo == 'ENTREGADO':
                    insumos[key]['entregado'][dia_mov] += cantidad
                elif tipo == 'NO ENTREGADO':
                    insumos[key]['no_entregado'][dia_mov] += cantidad

        # Construir tabla
        doc = SimpleDocTemplate(
            ruta_pdf,
            pagesize=landscape(legal),
            topMargin=0.5*inch, bottomMargin=0.5*inch,
            leftMargin=0.5*inch, rightMargin=0.5*inch
        )
        elementos = []
        estilos = getSampleStyleSheet()

        # Estilo de título personalizado
        estilo_titulo = ParagraphStyle(
            'CustomTitle',
            parent=estilos['Title'],
            alignment=1,
            fontSize=16,
            textColor=colors.white,
            backColor=colors.HexColor("#0070C0"),
            spaceAfter=14,
            fontName='Helvetica-Bold'
        )
        # Título principal
        elementos.append(Paragraph("REPORTE DEMANDA REAL", estilo_titulo))
        elementos.append(Spacer(1, 10))

        # Encabezados
        encabezado1 = [
            'Código',
            'MEDICAMENTO',
            'DIA DEL MES',
            f'CANTIDAD DE MEDICAMENTOS Y/O PRODUCTOS A FIN'
        ] + [''] * (len(dias) - 1) + [
            'Total\nEntregado',
            'Total\nNo\nEntregado',
            'Demanda',
            'Existencia',
            'Reajuste (+) (-)'
        ]
        encabezado2 = [
            '',
            'Nombre, Concentración\ny Presentación',
            ''
        ] + [str(d) for d in dias] + ['', '', '', '', '']

        data = [encabezado1, encabezado2]

        for (codigo, nombre_pres), valores in insumos.items():
            total_entregado = sum(valores['entregado'].get(d, 0) for d in dias)
            total_no_entregado = sum(valores['no_entregado'].get(d, 0) for d in dias)

            # Fila Entregado (nombre_pres aquí)
            fila_entregado = [
                codigo,              # Código
                nombre_pres,         # Medicamento (nombre del insumo, aquí va el texto)
                'Entregado'
            ]
            for d in dias:
                fila_entregado.append(valores['entregado'].get(d, 0))
            fila_entregado += [
                total_entregado,     # Total Entregado
                total_no_entregado,  # Total No Entregado (mostrar aquí, SPAN)
                total_entregado,     # Demanda
                valores['existencia'],
                valores['reajuste']
            ]

            # Fila No Entregado (vacío en las celdas con SPAN)
            fila_no_entregado = [
                '',                  # Código (vacío, SPAN)
                '',                  # Medicamento (vacío, SPAN)
                'No Entregado'
            ]
            for d in dias:
                fila_no_entregado.append(valores['no_entregado'].get(d, 0))
            fila_no_entregado += [
                '',                  # Total Entregado (vacío, SPAN)
                '',                  # Total No Entregado (vacío, SPAN)
                '',                  # Demanda (vacío, SPAN)
                '',                  # Existencia (vacío, SPAN)
                ''                   # Reajuste (vacío, SPAN)
            ]

            data.append(fila_entregado)
            data.append(fila_no_entregado)

        # Anchos de columna
        col_widths = [0.5*inch, 1.5*inch, 0.8*inch] + [0.3*inch] * len(dias) + [0.5*inch, 0.5*inch, 0.5*inch, 0.5*inch, 0.7*inch]

        tabla = Table(data, repeatRows=2, colWidths=col_widths)

        estilos_tabla = [
            ('SPAN', (0,0), (0,1)),  # Código encabezado
            ('SPAN', (2,0), (2,1)),  # Movimientos encabezado
            ('SPAN', (3,0), (len(dias)+2,0)),  # Días encabezado
            ('SPAN', (len(dias)+3,0), (len(dias)+3,1)),  # Total Entregado encabezado
            ('SPAN', (len(dias)+4,0), (len(dias)+4,1)),  # Total No Entregado encabezado
            ('SPAN', (len(dias)+5,0), (len(dias)+5,1)),  # Demanda encabezado
            ('SPAN', (len(dias)+6,0), (len(dias)+6,1)),  # Existencia encabezado
            ('SPAN', (len(dias)+7,0), (len(dias)+7,1)),  # Reajuste encabezado
            # Encabezados: fondo azul claro y texto negro
            ('BACKGROUND', (0,0), (-1,1), colors.lightblue),
            ('TEXTCOLOR', (0,0), (-1,1), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.25, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]

        # SPAN dinámico para las celdas vacías de cada insumo
        fila_inicio = 2  # porque las dos primeras filas son encabezados
        while fila_inicio < len(data):
            fila_fin = fila_inicio + 1  # la fila de No Entregado
            estilos_tabla.append(('SPAN', (0, fila_inicio), (0, fila_fin)))  # Código
            estilos_tabla.append(('SPAN', (1, fila_inicio), (1, fila_fin)))  # Medicamento (nombre_pres)
            estilos_tabla.append(('SPAN', (len(dias)+3, fila_inicio), (len(dias)+3, fila_fin)))  # Total Entregado
            estilos_tabla.append(('SPAN', (len(dias)+4, fila_inicio), (len(dias)+4, fila_fin)))  # Total No Entregado
            estilos_tabla.append(('SPAN', (len(dias)+5, fila_inicio), (len(dias)+5, fila_fin)))  # Demanda
            estilos_tabla.append(('SPAN', (len(dias)+6, fila_inicio), (len(dias)+6, fila_fin)))  # Existencia
            estilos_tabla.append(('SPAN', (len(dias)+7, fila_inicio), (len(dias)+7, fila_fin)))  # Reajuste
            fila_inicio += 2

        tabla.setStyle(TableStyle(estilos_tabla))
        elementos.append(tabla)
        doc.build(elementos)
        
    def generar_reporte(self):
        # Validar filtros obligatorios hasta servicio
        if not all([
            self.combo_area.get(),
            self.combo_distrito.get(),
            self.combo_tipo_servicio.get(),
            self.combo_servicio.get(),
            self.combo_tipo_insumo.get(),
            self.combo_insumo.get(),
            self.combo_presentacion.get()
        ]):
            messagebox.showerror("Error", "Debe seleccionar todos los filtros hasta Servicio, Insumo y Presentación")
            return

        # Rango fijo de fechas (puedes adaptar)
        fecha_ini = datetime.now() - timedelta(days=30)
        fecha_fin = datetime.now()

        if fecha_fin < fecha_ini:
            messagebox.showerror("Error", "La fecha final debe ser mayor a la inicial")
            return

        # Obtener nombres de los combos
        distrito_nombre = self.combo_distrito.get()
        tipo_servicio_desc = self.combo_tipo_servicio.get()
        servicio_nombre = self.combo_servicio.get()
        tipo_insumo_desc = self.combo_tipo_insumo.get()
        insumo_nombre = self.combo_insumo.get()
        presentacion_nombre = self.combo_presentacion.get()

        # Obtener movimientos sin filtrar tipo movimiento
        movimientos_raw = obtener_movimientos_kardex(
            fecha_ini.strftime('%Y-%m-%d'),
            fecha_fin.strftime('%Y-%m-%d'),
            distrito_nombre,
            tipo_servicio_desc,
            servicio_nombre,
            tipo_insumo_desc,
            insumo_nombre,
            presentacion_nombre
        )

        if not movimientos_raw:
            messagebox.showinfo("Info", "No hay datos para mostrar")
            return

        # Filtrar movimientos relevantes para demanda real
        movimientos_filtrados = [m for m in movimientos_raw if m.get('tipo_movimiento', '').upper() in [
            'ENTREGADO', 'NO ENTREGADO', 'REAJUSTE POSITIVO', 'REAJUSTE NEGATIVO', 'INVENTARIO INICIAL', 'ENTRADA NIVEL SUPERIOR', 'SALDO ANTERIOR'
        ]]

        datos_movimientos = self.procesar_datos(movimientos_filtrados, fecha_ini, fecha_fin)

        periodo_str = f"{fecha_ini.strftime('%d%m%Y')}_{fecha_fin.strftime('%d%m%Y')}"
        self.periodo_str = periodo_str

        import tempfile
        temp_dir = tempfile.gettempdir()
        self.temp_pdf_path = os.path.join(temp_dir, f"vista_previa_demanda_real_{periodo_str}.pdf")
        self.generar_pdf(datos_movimientos, self.temp_pdf_path)

        self.generar_vista_previa_pdf()

    def generar_vista_previa_pdf(self):
        try:
            # Limpiar frame pdf si ya existe
            for widget in self.pdf_frame.winfo_children():
                widget.destroy()

            # Crear frame contenedor con tamaño fijo para el canvas
            canvas_container = ttk.Frame(self.pdf_frame)
            canvas_container.pack(fill="both", expand=True)

            # Crear canvas
            canvas = tk.Canvas(canvas_container, bg='white')
            canvas.pack(side="left", fill="both", expand=True)

            # Scrollbars
            v_scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)
            v_scrollbar.pack(side="right", fill="y")
            h_scrollbar = ttk.Scrollbar(self.pdf_frame, orient="horizontal", command=canvas.xview)
            h_scrollbar.pack(fill="x")

            canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

            # Abrir PDF con PyMuPDF
            doc = fitz.open(self.temp_pdf_path)
            self.current_page = 0
            self.total_pages = len(doc)

            # Frame para controles de página
            control_frame = ttk.Frame(self.pdf_frame)
            control_frame.pack(fill="x", pady=5)

            def change_page(delta):
                self.current_page = max(0, min(self.current_page + delta, self.total_pages - 1))
                display_page()
                page_label.config(text=f"Página {self.current_page + 1} de {self.total_pages}")

            ttk.Button(control_frame, text="<<", command=lambda: change_page(-1)).pack(side="left", padx=5)
            page_label = ttk.Label(control_frame, text=f"Página 1 de {self.total_pages}")
            page_label.pack(side="left", padx=10)
            ttk.Button(control_frame, text=">>", command=lambda: change_page(1)).pack(side="left", padx=5)

            def display_page():
                canvas.delete("all")
                page = doc.load_page(self.current_page)
                pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))  # Ajusta zoom si quieres
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                tk_img = ImageTk.PhotoImage(img)
                canvas.image = tk_img  # evitar GC
                canvas.create_image(0, 0, anchor="nw", image=tk_img)
                # Configurar scrollregion al tamaño de la imagen
                canvas.config(scrollregion=(0, 0, pix.width, pix.height))

            display_page()

        except Exception as e:
            messagebox.showerror("Error", f"Error al mostrar vista previa PDF: {str(e)}")
    
    def cerrar_ventana(self):
        if hasattr(self, 'temp_pdf_path') and self.temp_pdf_path and os.path.exists(self.temp_pdf_path):
            try:
                os.remove(self.temp_pdf_path)
            except:
                pass

        if self.main_window:
            self.main_window.destroy()
        else:
            self.parent.destroy()
    
    def destroy(self):
        if hasattr(self, 'frame_principal'):
            self.frame_principal.destroy()