# Imports existentes
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import pandas as pd
from datetime import datetime
import sys
import os

# Nuevos imports para PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Agregar el directorio raíz del proyecto al PATH de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.db_manager import (
    obtener_distritos,
    obtener_tipos_servicio_por_distrito,
    obtener_servicios_por_tipo,
    obtener_tipos_insumo,
    obtener_insumos_por_tipo,
    obtener_presentaciones,
    obtener_movimientos_kardex
)

class Reportes:
    def __init__(self, parent_frame, main_window=None):
        self.parent = parent_frame
        self.main_window = main_window
        self.movimientos_data = None
        self.setup_ui()

    def setup_ui(self):
        # Frame principal
        self.frame_principal = ttk.LabelFrame(self.parent, text="Filtros de Reporte")
        self.frame_principal.pack(fill="both", expand=True, padx=10, pady=5)

        # Frame para fechas
        self.frame_fechas = ttk.Frame(self.frame_principal)
        self.frame_fechas.pack(fill="x", padx=5, pady=5)

        ttk.Label(self.frame_fechas, text="Fecha Inicial:").pack(side="left", padx=5)
        self.fecha_inicial = DateEntry(self.frame_fechas, width=12, date_pattern='dd/mm/yyyy')
        self.fecha_inicial.pack(side="left", padx=5)

        ttk.Label(self.frame_fechas, text="Fecha Final:").pack(side="left", padx=5)
        self.fecha_final = DateEntry(self.frame_fechas, width=12, date_pattern='dd/mm/yyyy')
        self.fecha_final.pack(side="left", padx=5)

        # Frame para combos
        self.frame_combos = ttk.Frame(self.frame_principal)
        self.frame_combos.pack(fill="x", padx=5, pady=5)

        # Primera fila de combos
        self.frame_combos1 = ttk.Frame(self.frame_combos)
        self.frame_combos1.pack(fill="x", pady=5)

        ttk.Label(self.frame_combos1, text="Distrito:").grid(row=0, column=0, padx=5)
        self.combo_distrito = ttk.Combobox(self.frame_combos1, state="readonly")
        self.combo_distrito.grid(row=0, column=1, padx=5)

        ttk.Label(self.frame_combos1, text="Tipo de Servicio:").grid(row=0, column=2, padx=5)
        self.combo_tipo_servicio = ttk.Combobox(self.frame_combos1, state="readonly")
        self.combo_tipo_servicio.grid(row=0, column=3, padx=5)

        ttk.Label(self.frame_combos1, text="Servicio:").grid(row=0, column=4, padx=5)
        self.combo_servicio = ttk.Combobox(self.frame_combos1, state="readonly")
        self.combo_servicio.grid(row=0, column=5, padx=5)

        # Segunda fila de combos
        self.frame_combos2 = ttk.Frame(self.frame_combos)
        self.frame_combos2.pack(fill="x", pady=5)

        ttk.Label(self.frame_combos2, text="Tipo de Insumo:").grid(row=0, column=0, padx=5)
        self.combo_tipo_insumo = ttk.Combobox(self.frame_combos2, state="readonly")
        self.combo_tipo_insumo.grid(row=0, column=1, padx=5)

        ttk.Label(self.frame_combos2, text="Insumo:").grid(row=0, column=2, padx=5)
        self.combo_insumo = ttk.Combobox(self.frame_combos2, state="readonly")
        self.combo_insumo.grid(row=0, column=3, padx=5)

        ttk.Label(self.frame_combos2, text="Presentación:").grid(row=0, column=4, padx=5)
        self.combo_presentacion = ttk.Combobox(self.frame_combos2, state="readonly")
        self.combo_presentacion.grid(row=0, column=5, padx=5)

        # Agregar frame para el Treeview
        self.tree_frame = ttk.Frame(self.frame_principal)
        self.tree_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Crear el Treeview con scrollbars
        self.tree = ttk.Treeview(self.tree_frame)
        self.scrolly = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.scrollx = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.scrolly.set, xscrollcommand=self.scrollx.set)

        # Colocar el Treeview y scrollbars
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.scrolly.grid(row=0, column=1, sticky="ns")
        self.scrollx.grid(row=1, column=0, sticky="ew")

        # Configurar el grid
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)

        # Frame para botones
        self.frame_botones = ttk.Frame(self.frame_principal)
        self.frame_botones.pack(fill="x", pady=10)

        # Botones
        ttk.Button(self.frame_botones, text="Generar Vista Previa",
                  command=self.generar_vista_previa).pack(side="left", padx=5)
        ttk.Button(self.frame_botones, text="Exportar a PDF",
                  command=self.generar_pdf).pack(side="left", padx=5)
        ttk.Button(self.frame_botones, text="Exportar a Excel",
                  command=self.generar_kardex).pack(side="left", padx=5)
        ttk.Button(self.frame_botones, text="Cerrar",
                  command=self.cerrar_ventana).pack(side="right", padx=5)
        
        # Vincular eventos de cambio
        self.combo_distrito.bind('<<ComboboxSelected>>', self.cargar_tipos_servicio)
        self.combo_tipo_servicio.bind('<<ComboboxSelected>>', self.cargar_servicios)
        self.combo_tipo_insumo.bind('<<ComboboxSelected>>', self.cargar_insumos)

        # Cargar datos iniciales
        self.cargar_distritos()
        self.cargar_tipos_insumo()
        self.cargar_presentaciones()

    def cargar_distritos(self):
        distritos = obtener_distritos()
        if distritos:
            self.combo_distrito['values'] = [''] + [d['nombre'] for d in distritos]

    def cargar_tipos_servicio(self, event=None):
        self.combo_tipo_servicio.set('')
        self.combo_servicio.set('')
        if self.combo_distrito.get():
            distritos = obtener_distritos()
            id_distrito = next(d['id'] for d in distritos if d['nombre'] == self.combo_distrito.get())
            tipos = obtener_tipos_servicio_por_distrito(id_distrito)
            if tipos:
                self.combo_tipo_servicio['values'] = [''] + [t['descripcion'] for t in tipos]

    def cargar_servicios(self, event=None):
        self.combo_servicio.set('')
        if self.combo_tipo_servicio.get():
            tipos = obtener_tipos_servicio_por_distrito(
                next(d['id'] for d in obtener_distritos()
                     if d['nombre'] == self.combo_distrito.get())
            )
            id_tipo = next(t['id'] for t in tipos
                         if t['descripcion'] == self.combo_tipo_servicio.get())
            servicios = obtener_servicios_por_tipo(id_tipo)
            if servicios:
                self.combo_servicio['values'] = [''] + [s['nombre'] for s in servicios]

    def cargar_tipos_insumo(self):
        tipos = obtener_tipos_insumo()
        if tipos:
            self.combo_tipo_insumo['values'] = [''] + [t['descripcion'] for t in tipos]

    def cargar_insumos(self, event=None):
        self.combo_insumo.set('')
        if self.combo_tipo_insumo.get():
            tipos = obtener_tipos_insumo()
            id_tipo = next(t['id'] for t in tipos
                         if t['descripcion'] == self.combo_tipo_insumo.get())
            insumos = obtener_insumos_por_tipo(id_tipo)
            if insumos:
                self.combo_insumo['values'] = [''] + [i['nombre'] for i in insumos]

    def cargar_presentaciones(self):
        presentaciones = obtener_presentaciones()
        if presentaciones:
            self.combo_presentacion['values'] = [''] + [p['nombre'] for p in presentaciones]

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

            # Limpiar Treeview
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Configurar columnas
            columns = list(self.movimientos_data[0].keys())
            self.tree["columns"] = columns

            # Configurar encabezados
            for col in columns:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=100)  # Ajusta el ancho según necesites

            # Insertar datos
            for row in self.movimientos_data:
                self.tree.insert("", "end", values=[row[col] for col in columns])

        except Exception as e:
            messagebox.showerror("Error", f"Error al generar vista previa: {str(e)}")

    def generar_pdf(self):
        if not self.movimientos_data:
            messagebox.showwarning("Advertencia", "Primero debe generar una vista previa")
            return

        try:
            # Crear el documento PDF
            doc = SimpleDocTemplate(
                "Kardex.pdf",
                pagesize=landscape(letter),
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )

            # Contenedor para los elementos del PDF
            elements = []

            # Estilos
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                alignment=1,  # Centrado
                spaceAfter=30
            )

            # Títulos
            elements.append(Paragraph(
                "DIRECCIÓN DEPARTAMENTAL DE REDES INTEGRADAS DE SERVICIOS DE SALUD DE GUATEMALA",
                title_style))
            elements.append(Paragraph("ÁREA NOR ORIENTE", title_style))
            elements.append(Paragraph("TARJETA DE CONTROL DE SUMINISTROS", title_style))
            elements.append(Spacer(1, 20))

            # Información de filtros
            filtros = [
                f"Distrito: {self.combo_distrito.get()}",
                f"Tipo de Servicio: {self.combo_tipo_servicio.get()}",
                f"Servicio: {self.combo_servicio.get()}",
                f"Tipo de Insumo: {self.combo_tipo_insumo.get()}",
                f"Insumo: {self.combo_insumo.get()}",
                f"Presentación: {self.combo_presentacion.get()}"
            ]

            for filtro in filtros:
                elements.append(Paragraph(filtro, styles['Normal']))
            elements.append(Spacer(1, 20))

            # Crear tabla de datos
            headers = list(self.movimientos_data[0].keys())
            data = [headers]  # Primera fila son los encabezados
            for row in self.movimientos_data:
                data.append([str(row[col]) for col in headers])

            # Crear tabla
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            elements.append(table)

            # Generar PDF
            doc.build(elements)
            messagebox.showinfo("Éxito", "PDF generado correctamente")
        
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar PDF: {str(e)}")
            print(f"Error detallado: {e}")

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
        # Crear DataFrame
        df = pd.DataFrame(movimientos)

        # Crear archivo Excel
        writer = pd.ExcelWriter('Kardex.xlsx', engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Kardex', startrow=7, index=False)

        # Obtener el objeto workbook y worksheet
        workbook = writer.book
        worksheet = writer.sheets['Kardex']

        # Formato para títulos
        titulo_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 14
        })

        # Escribir títulos
        worksheet.merge_range('A1:J1',
            'DIRECCION DEPARTAMENTAL DE REDES INTEGRADAS DE SERVICIOS DE SALUD DE GUATEMALA',
            titulo_format)
        worksheet.merge_range('A2:J2', 'AREA NOR ORIENTE', titulo_format)
        worksheet.merge_range('A3:J3', 'TARJETA DE CONTROL DE SUMINISTROS', titulo_format)

        # Escribir filtros
        filtros_format = workbook.add_format({'bold': True})
        worksheet.write('A5', f'Distrito: {self.combo_distrito.get()}', filtros_format)
        worksheet.write('C5', f'Tipo de Servicio: {self.combo_tipo_servicio.get()}', filtros_format)
        worksheet.write('E5', f'Servicio: {self.combo_servicio.get()}', filtros_format)
        worksheet.write('A6', f'Tipo de Insumo: {self.combo_tipo_insumo.get()}', filtros_format)
        worksheet.write('C6', f'Insumo: {self.combo_insumo.get()}', filtros_format)
        worksheet.write('E6', f'Presentación: {self.combo_presentacion.get()}', filtros_format)

        # Ajustar anchos de columna
        worksheet.set_column('A:J', 15)

        # Guardar archivo
        writer.close()
        messagebox.showinfo("Éxito", "Reporte generado correctamente")

    def cerrar_ventana(self):
        if messagebox.askyesno("Confirmar", "¿Está seguro que desea cerrar esta ventana?"):
            # Limpiar el frame principal
            for widget in self.parent.winfo_children():
                widget.destroy()
            # Mostrar la pantalla de bienvenida
            if self.main_window:
                self.main_window.show_welcome_screen()