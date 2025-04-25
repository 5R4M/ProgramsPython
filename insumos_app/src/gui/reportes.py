import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import pandas as pd
from datetime import datetime
import sys
import os

# Agregar el directorio raíz del proyecto al PATH de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.db_manager import (
    obtener_distritos,
    obtener_tipos_servicio_por_distrito,
    obtener_servicios_por_tipo,
    obtener_tipos_insumo,
    obtener_insumos_por_tipo,
    obtener_presentaciones,
    obtener_movimientos_kardex  # Necesitarás crear esta función
)

def abrir_reportes(ventana_principal):
    ventana = tk.Toplevel()
    ventana.title("Reportes")
    ventana.geometry("800x600")

    def centrar_ventana(ventana):
        ventana.update_idletasks()
        width = ventana.winfo_width()
        height = ventana.winfo_height()
        x = (ventana.winfo_screenwidth() // 2) - (width // 2)
        y = (ventana.winfo_screenheight() // 2) - (height // 2)
        ventana.geometry(f'{width}x{height}+{x}+{y}')

    centrar_ventana(ventana)

    # Frame principal
    frame_principal = ttk.LabelFrame(ventana, text="Filtros de Reporte")
    frame_principal.pack(fill="both", expand=True, padx=10, pady=5)

    # Frame para fechas
    frame_fechas = ttk.Frame(frame_principal)
    frame_fechas.pack(fill="x", padx=5, pady=5)

    ttk.Label(frame_fechas, text="Fecha Inicial:").pack(side="left", padx=5)
    fecha_inicial = DateEntry(frame_fechas, width=12, date_pattern='dd/mm/yyyy')
    fecha_inicial.pack(side="left", padx=5)

    ttk.Label(frame_fechas, text="Fecha Final:").pack(side="left", padx=5)
    fecha_final = DateEntry(frame_fechas, width=12, date_pattern='dd/mm/yyyy')
    fecha_final.pack(side="left", padx=5)

    # Frame para combos
    frame_combos = ttk.Frame(frame_principal)
    frame_combos.pack(fill="x", padx=5, pady=5)

    # Primera fila de combos
    frame_combos1 = ttk.Frame(frame_combos)
    frame_combos1.pack(fill="x", pady=5)

    ttk.Label(frame_combos1, text="Distrito:").grid(row=0, column=0, padx=5)
    combo_distrito = ttk.Combobox(frame_combos1, state="readonly")
    combo_distrito.grid(row=0, column=1, padx=5)

    ttk.Label(frame_combos1, text="Tipo de Servicio:").grid(row=0, column=2, padx=5)
    combo_tipo_servicio = ttk.Combobox(frame_combos1, state="readonly")
    combo_tipo_servicio.grid(row=0, column=3, padx=5)

    ttk.Label(frame_combos1, text="Servicio:").grid(row=0, column=4, padx=5)
    combo_servicio = ttk.Combobox(frame_combos1, state="readonly")
    combo_servicio.grid(row=0, column=5, padx=5)

    # Segunda fila de combos
    frame_combos2 = ttk.Frame(frame_combos)
    frame_combos2.pack(fill="x", pady=5)

    ttk.Label(frame_combos2, text="Tipo de Insumo:").grid(row=0, column=0, padx=5)
    combo_tipo_insumo = ttk.Combobox(frame_combos2, state="readonly")
    combo_tipo_insumo.grid(row=0, column=1, padx=5)

    ttk.Label(frame_combos2, text="Insumo:").grid(row=0, column=2, padx=5)
    combo_insumo = ttk.Combobox(frame_combos2, state="readonly")
    combo_insumo.grid(row=0, column=3, padx=5)

    ttk.Label(frame_combos2, text="Presentación:").grid(row=0, column=4, padx=5)
    combo_presentacion = ttk.Combobox(frame_combos2, state="readonly")
    combo_presentacion.grid(row=0, column=5, padx=5)

    def cargar_distritos():
        distritos = obtener_distritos()
        if distritos:
            combo_distrito['values'] = [''] + [d['nombre'] for d in distritos]

    def cargar_tipos_servicio(event=None):
        combo_tipo_servicio.set('')
        combo_servicio.set('')
        if combo_distrito.get():
            distritos = obtener_distritos()
            id_distrito = next(d['id'] for d in distritos if d['nombre'] == combo_distrito.get())
            tipos = obtener_tipos_servicio_por_distrito(id_distrito)
            if tipos:
                combo_tipo_servicio['values'] = [''] + [t['descripcion'] for t in tipos]

    def cargar_servicios(event=None):
        combo_servicio.set('')
        if combo_tipo_servicio.get():
            tipos = obtener_tipos_servicio_por_distrito(
                next(d['id'] for d in obtener_distritos()
                     if d['nombre'] == combo_distrito.get())
            )
            id_tipo = next(t['id'] for t in tipos
                         if t['descripcion'] == combo_tipo_servicio.get())
            servicios = obtener_servicios_por_tipo(id_tipo)
            if servicios:
                combo_servicio['values'] = [''] + [s['nombre'] for s in servicios]

    def cargar_tipos_insumo():
        tipos = obtener_tipos_insumo()
        if tipos:
            combo_tipo_insumo['values'] = [''] + [t['descripcion'] for t in tipos]

    def cargar_insumos(event=None):
        combo_insumo.set('')
        if combo_tipo_insumo.get():
            tipos = obtener_tipos_insumo()
            id_tipo = next(t['id'] for t in tipos
                         if t['descripcion'] == combo_tipo_insumo.get())
            insumos = obtener_insumos_por_tipo(id_tipo)
            if insumos:
                combo_insumo['values'] = [''] + [i['nombre'] for i in insumos]

    def cargar_presentaciones():
        presentaciones = obtener_presentaciones()
        if presentaciones:
            combo_presentacion['values'] = [''] + [p['nombre'] for p in presentaciones]

    def generar_kardex():
        try:
            # Validar fechas
            fecha_ini = datetime.strptime(fecha_inicial.get(), '%d/%m/%Y')
            fecha_fin = datetime.strptime(fecha_final.get(), '%d/%m/%Y')

            if fecha_fin < fecha_ini:
                messagebox.showerror("Error", "La fecha final debe ser mayor a la inicial")
                return

            # Validar selección de insumo
            if not combo_insumo.get():
                messagebox.showerror("Error", "Debe seleccionar un insumo")
                return

            # Obtener datos para el reporte
            movimientos = obtener_movimientos_kardex(
                fecha_ini.strftime('%Y-%m-%d'),
                fecha_fin.strftime('%Y-%m-%d'),
                combo_distrito.get(),
                combo_tipo_servicio.get(),
                combo_servicio.get(),
                combo_tipo_insumo.get(),
                combo_insumo.get(),
                combo_presentacion.get()
            )

            if not movimientos:
                messagebox.showinfo("Info", "No hay datos para mostrar")
                return

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
            worksheet.write('A5', f'Distrito: {combo_distrito.get()}', filtros_format)
            worksheet.write('C5', f'Tipo de Servicio: {combo_tipo_servicio.get()}', filtros_format)
            worksheet.write('E5', f'Servicio: {combo_servicio.get()}', filtros_format)
            worksheet.write('A6', f'Tipo de Insumo: {combo_tipo_insumo.get()}', filtros_format)
            worksheet.write('C6', f'Insumo: {combo_insumo.get()}', filtros_format)
            worksheet.write('E6', f'Presentación: {combo_presentacion.get()}', filtros_format)

            # Ajustar anchos de columna
            worksheet.set_column('A:J', 15)

            # Guardar archivo
            writer.close()

            messagebox.showinfo("Éxito", "Reporte generado correctamente")

        except Exception as e:
            messagebox.showerror("Error", f"Error al generar reporte: {str(e)}")

    # Botones
    frame_botones = ttk.Frame(frame_principal)
    frame_botones.pack(fill="x", pady=10)

    ttk.Button(frame_botones, text="Generar Kardex",
               command=generar_kardex).pack(side="left", padx=5)
    ttk.Button(frame_botones, text="Cerrar",
               command=ventana.destroy).pack(side="right", padx=5)

    # Vincular eventos de cambio
    combo_distrito.bind('<<ComboboxSelected>>', cargar_tipos_servicio)
    combo_tipo_servicio.bind('<<ComboboxSelected>>', cargar_servicios)
    combo_tipo_insumo.bind('<<ComboboxSelected>>', cargar_insumos)

    # Cargar datos iniciales
    cargar_distritos()
    cargar_tipos_insumo()
    cargar_presentaciones()

    ventana.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    abrir_reportes(root)