import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
from ttkwidgets.autocomplete import AutocompleteCombobox

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

class ReporteDemandaReal:
    def __init__(self, parent_frame, main_window=None):
        self.parent = parent_frame
        self.main_window = main_window
        self.movimientos_data = None
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

        # Botones
        self.frame_botones = ttk.Frame(self.frame_principal)
        self.frame_botones.pack(fill="x", pady=10)

        ttk.Button(self.frame_botones, text="Generar y Exportar Reporte", command=self.generar_reporte_y_exportar).pack(side="left", padx=5)
        ttk.Button(self.frame_botones, text="Cerrar", command=self.cerrar_ventana).pack(side="right", padx=5)

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

    # Métodos para cargar combos (igual que en ReporteKardex)
    def cargar_areas(self):
        self.areas = obtener_areas()
        if self.areas:
            opciones = [''] + [a['nombre'] for a in self.areas]
            self.combo_area.set_completion_list(opciones)

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
                self.combo_presentacion.set(insumo.get('nombre_presentacion', ''))
            else:
                self.combo_presentacion.set('')
        else:
            self.combo_presentacion.set('')

    def cargar_presentaciones(self):
        self.presentaciones = obtener_presentaciones()
        if self.presentaciones:
            opciones = [''] + [p['nombre'] for p in self.presentaciones]
            self.combo_presentacion.set_completion_list(opciones)

    def cerrar_ventana(self):
        if self.main_window:
            self.main_window.show_main_menu()

    def obtener_rango_fechas(self, anio, mes):
        # Rango del 26 del mes anterior al 25 del mes actual
        fecha_fin = datetime(anio, mes, 25)
        if mes == 1:
            fecha_ini = datetime(anio -1, 12, 26)
        else:
            fecha_ini = datetime(anio, mes -1, 26)
        return fecha_ini, fecha_fin

    def procesar_datos(self, movimientos, fecha_ini, fecha_fin):
        # Crear lista de días del 26 al 25
        dias = []
        current = fecha_ini
        while current <= fecha_fin:
            dias.append(current.day)
            current += timedelta(days=1)

        # Obtener lista única de insumos (por descripción)
        insumos = sorted(set(m['descripcion_insumo'] for m in movimientos if 'descripcion_insumo' in m))

        # Inicializar estructura de datos:
        # { insumo: { 'entregado': {dia: cantidad}, 'no_entregado': {dia: cantidad}, 'reajuste': total, 'saldo_anterior': valor, 'entrada_nivel_superior': valor } }
        datos = {}
        for insumo in insumos:
            datos[insumo] = {
                'entregado': {d:0 for d in dias},
                'no_entregado': {d:0 for d in dias},
                'reajuste': 0,
                'saldo_anterior': 0,
                'entrada_nivel_superior': 0
            }

        # Llenar datos
        for mov in movimientos:
            insumo = mov.get('descripcion_insumo')
            if insumo not in datos:
                continue
            fecha = mov.get('fecha')
            if not fecha:
                continue
            if isinstance(fecha, str):
                try:
                    fecha = datetime.strptime(fecha[:10], '%Y-%m-%d')
                except:
                    continue
            dia = fecha.day
            tipo = mov.get('tipo_movimiento', '').upper()
            cantidad = 0
            for campo in ['cantidad', 'cantidad_movimiento', 'cantidad_entrada', 'cantidad_salida', 'qty', 'quantity', 'cant', 'cantidades', 'valor_cantidad']:
                if campo in mov and mov[campo] is not None:
                    try:
                        cantidad = float(mov[campo])
                        break
                    except:
                        pass

            if tipo == 'ENTREGADO':
                if dia in datos[insumo]['entregado']:
                    datos[insumo]['entregado'][dia] += cantidad
            elif tipo == 'NO ENTREGADO':
                if dia in datos[insumo]['no_entregado']:
                    datos[insumo]['no_entregado'][dia] += cantidad
            elif tipo == 'REAJUSTE POSITIVO':
                datos[insumo]['reajuste'] += cantidad
            elif tipo == 'REAJUSTE NEGATIVO':
                datos[insumo]['reajuste'] -= cantidad
            elif tipo == 'INVENTARIO INICIAL' or tipo == 'ENTRADA NIVEL SUPERIOR':
                datos[insumo]['entrada_nivel_superior'] += cantidad
            elif tipo == 'SALDO ANTERIOR':
                datos[insumo]['saldo_anterior'] += cantidad

        # Calcular totales y demanda real, existencia
        for insumo in datos:
            total_entregado = sum(datos[insumo]['entregado'].values())
            total_no_entregado = sum(datos[insumo]['no_entregado'].values())
            demanda_real = total_entregado + total_no_entregado
            existencia = datos[insumo]['saldo_anterior'] + datos[insumo]['entrada_nivel_superior'] - total_entregado + datos[insumo]['reajuste']
            datos[insumo]['total_entregado'] = total_entregado
            datos[insumo]['total_no_entregado'] = total_no_entregado
            datos[insumo]['demanda_real'] = demanda_real
            datos[insumo]['existencia'] = existencia

        return dias, datos

    def exportar_excel(self, dias, datos, periodo_str):
        import pandas as pd
        import os
        from datetime import datetime

        # Crear DataFrame con multiíndice para filas: descripción insumo + 'Entregado'/'No Entregado'
        filas = []
        for insumo, info in datos.items():
            filas.append((insumo, 'Entregado'))
            filas.append((insumo, 'No Entregado'))

        columnas_dias = [str(d) for d in dias]
        columnas_totales = ['Total Entregado', 'Total No Entregado', 'Demanda Real', 'Existencia', 'Reajuste']

        columnas = ['Descripción Insumo'] + columnas_dias + columnas_totales

        data = []
        for insumo, info in datos.items():
            # Fila entregado
            fila_entregado = [insumo] + [info['entregado'][d] for d in dias] + [info['total_entregado'], '', info['demanda_real'], info['existencia'], info['reajuste']]
            # Fila no entregado
            fila_no_entregado = ['', ] + [info['no_entregado'][d] for d in dias] + ['', info['total_no_entregado'], '', '', '']
            data.append(fila_entregado)
            data.append(fila_no_entregado)

        df = pd.DataFrame(data, columns=columnas)

        # Guardar Excel
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"Reporte_Demanda_Real_{periodo_str}_{timestamp}.xlsx"
        downloads_path = os.path.expanduser("~/Downloads")
        full_path = os.path.join(downloads_path, file_name)

        writer = pd.ExcelWriter(full_path, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='Demanda Real')

        workbook = writer.book
        worksheet = writer.sheets['Demanda Real']

        # Formatos
        header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#ADD8E6', 'border': 1, 'text_wrap': True})
        center_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})
        bold_format = workbook.add_format({'bold': True, 'border': 1})

        # Formatear encabezados
        worksheet.set_row(0, 40, header_format)

        # Ajustar ancho columnas
        worksheet.set_column(0, 0, 30)  # Descripción insumo
        worksheet.set_column(1, len(columnas)-1, 5)  # Días y totales

        # Aplicar formato a filas
        for row_num in range(1, len(df)+1):
            worksheet.set_row(row_num, 20, center_format)
            # Poner negrita en filas "Entregado"
            if df.iloc[row_num-1, 0] != '':
                worksheet.set_row(row_num, 20, bold_format)

        writer.close()
        messagebox.showinfo("Éxito", f"Reporte guardado en:\n{full_path}")
        return full_path
    
    def generar_reporte_y_exportar(self):
        # Validar filtros
        if not all([self.combo_area.get(), self.combo_distrito.get(), self.combo_tipo_servicio.get(),
                    self.combo_servicio.get(), self.combo_tipo_insumo.get(), self.combo_insumo.get(),
                    self.combo_presentacion.get()]):
            messagebox.showerror("Error", "Debe seleccionar todos los filtros")
            return

        # Obtener año y mes actuales
        hoy = datetime.now()
        anio = hoy.year
        mes = hoy.month

        fecha_ini, fecha_fin = self.obtener_rango_fechas(anio, mes)

        # Obtener movimientos sin filtrar tipo movimiento
        movimientos_raw = obtener_movimientos_kardex(
            fecha_ini.strftime('%Y-%m-%d'),
            fecha_fin.strftime('%Y-%m-%d'),
            self.combo_distrito.get(),
            self.combo_tipo_servicio.get(),
            self.combo_servicio.get(),
            self.combo_tipo_insumo.get(),
            self.combo_insumo.get(),
            self.combo_presentacion.get()
        )

        if not movimientos_raw:
            messagebox.showinfo("Info", "No hay datos para mostrar")
            return

        # Filtrar solo entregado y no entregado
        movimientos_filtrados = [m for m in movimientos_raw if m.get('tipo_movimiento', '').upper() in ['ENTREGADO', 'NO ENTREGADO', 'REAJUSTE POSITIVO', 'REAJUSTE NEGATIVO', 'INVENTARIO INICIAL', 'ENTRADA NIVEL SUPERIOR', 'SALDO ANTERIOR']]

        dias, datos = self.procesar_datos(movimientos_filtrados, fecha_ini, fecha_fin)

        periodo_str = f"{fecha_ini.strftime('%d%m%Y')}_{fecha_fin.strftime('%d%m%Y')}"

        self.exportar_excel(dias, datos, periodo_str)

    def cerrar_ventana(self):
        if self.main_window:
            self.main_window.show_main_menu()