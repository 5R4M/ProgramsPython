import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
import sys
import os
from ttkwidgets.autocomplete import AutocompleteCombobox

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.db_manager import (
    obtener_areas,
    obtener_distritos_por_area,
    obtener_distritos,
    obtener_tipos_servicio_por_distrito,
    obtener_servicios_por_tipo,
    obtener_tipos_insumo,
    obtener_insumos_por_tipo,
    obtener_presentaciones,
    obtener_tipos_movimiento,
    buscar_movimientos_por_filtros,
    actualizar_movimiento,
    eliminar_movimiento,
    obtener_id_tipo_movimiento
)

class CorreccionMovimientos:
    def __init__(self, parent_frame, main_window):
        self.parent = parent_frame
        self.main_window = main_window

        # Variables de filtro
        self.fecha_inicio_var = tk.StringVar()
        self.fecha_final_var = tk.StringVar()
        self.tipo_movimiento_var = tk.StringVar()
        self.area_var = tk.StringVar()
        self.distrito_var = tk.StringVar()
        self.tipo_servicio_var = tk.StringVar()
        self.servicio_var = tk.StringVar()
        self.tipo_insumo_var = tk.StringVar()
        self.insumo_var = tk.StringVar()
        self.presentacion_var = tk.StringVar()

        self.setup_ui()

    def setup_ui(self):
        # Frame principal de filtros
        filtros_frame = ttk.LabelFrame(self.parent, text="Filtros de Búsqueda")
        filtros_frame.pack(fill="x", padx=10, pady=10)

        # Frame de fechas
        fechas_frame = ttk.LabelFrame(filtros_frame, text="Fechas")
        fechas_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(fechas_frame, text="Fecha Inicio:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.fecha_inicio = DateEntry(fechas_frame, width=12, date_pattern='dd/mm/yyyy')
        self.fecha_inicio.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(fechas_frame, text="Fecha Final:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.fecha_final = DateEntry(fechas_frame, width=12, date_pattern='dd/mm/yyyy')
        self.fecha_final.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # Frame de ubicación
        ubicacion_frame = ttk.LabelFrame(filtros_frame, text="Ubicación")
        ubicacion_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(ubicacion_frame, text="Área:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.area_cb = AutocompleteCombobox(ubicacion_frame, textvariable=self.area_var, width=20, state="normal")
        self.area_cb.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.area_cb.set_completion_list([a['nombre'] for a in obtener_areas() or []])

        ttk.Label(ubicacion_frame, text="Distrito:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.distrito_cb = AutocompleteCombobox(ubicacion_frame, textvariable=self.distrito_var, width=20, state="normal")
        self.distrito_cb.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.distrito_cb.set_completion_list([d['nombre'] for d in obtener_distritos() or []])

        ttk.Label(ubicacion_frame, text="Tipo de Servicio:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.tipo_servicio_cb = AutocompleteCombobox(ubicacion_frame, textvariable=self.tipo_servicio_var, width=20, state="normal")
        self.tipo_servicio_cb.grid(row=0, column=5, padx=5, pady=5, sticky="w")

        ttk.Label(ubicacion_frame, text="Servicio:").grid(row=0, column=6, padx=5, pady=5, sticky="w")
        self.servicio_cb = AutocompleteCombobox(ubicacion_frame, textvariable=self.servicio_var, width=20, state="normal")
        self.servicio_cb.grid(row=0, column=7, padx=5, pady=5, sticky="w")

        # Frame de insumo
        insumo_frame = ttk.LabelFrame(filtros_frame, text="Insumo")
        insumo_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(insumo_frame, text="Tipo de Insumo:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.tipo_insumo_cb = AutocompleteCombobox(insumo_frame, textvariable=self.tipo_insumo_var, width=20, state="normal")
        self.tipo_insumo_cb.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.tipo_insumo_cb.set_completion_list([ti['descripcion'] for ti in obtener_tipos_insumo() or []])

        ttk.Label(insumo_frame, text="Insumo:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.insumo_cb = AutocompleteCombobox(insumo_frame, textvariable=self.insumo_var, width=20, state="normal")
        self.insumo_cb.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        ttk.Label(insumo_frame, text="Presentación:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.presentacion_cb = AutocompleteCombobox(insumo_frame, textvariable=self.presentacion_var, width=20, state="normal")
        self.presentacion_cb.grid(row=0, column=5, padx=5, pady=5, sticky="w")
        self.presentacion_cb.set_completion_list([p['nombre'] for p in obtener_presentaciones() or []])

        ttk.Label(insumo_frame, text="Tipo de Movimiento:").grid(row=0, column=6, padx=5, pady=5, sticky="w")
        self.tipo_movimiento_cb = AutocompleteCombobox(insumo_frame, textvariable=self.tipo_movimiento_var, width=20, state="normal")
        self.tipo_movimiento_cb.grid(row=0, column=7, padx=5, pady=5, sticky="w")
        self.tipo_movimiento_cb.set_completion_list([tm['descripcion'] for tm in obtener_tipos_movimiento() or []])

        # Botón buscar
        ttk.Button(filtros_frame, text="Buscar", command=self.buscar_movimientos).pack(pady=10)

        # Treeview para mostrar resultados
        self.tree_frame = ttk.Frame(self.parent)
        self.tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(self.tree_frame, columns=("id", "fecha", "referencia", "tipo_movimiento", "insumo", "cantidad", "observaciones"), show="headings")
        self.tree.pack(side="left", fill="both", expand=True)

        self.yscrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.yscrollbar.pack(side="right", fill="y")

        self.xscrollbar = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.tree.xview)
        self.xscrollbar.pack(side="bottom", fill="x")

        self.tree.configure(yscrollcommand=self.yscrollbar.set, xscrollcommand=self.xscrollbar.set)

        for col, txt in zip(self.tree["columns"], ["ID", "Fecha", "Referencia", "Tipo Movimiento", "Insumo", "Cantidad", "Observaciones"]):
            self.tree.heading(col, text=txt)
            self.tree.column(col, width=120)

        # Botones de acción
        frame_botones = ttk.Frame(self.parent)
        frame_botones.pack(fill="x", padx=10, pady=5)
        ttk.Button(frame_botones, text="Editar", command=self.editar_movimiento).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Eliminar", command=self.eliminar_movimiento).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Cerrar", command=self.cerrar_ventana).pack(side="right", padx=5)

        # Bindings para combos dependientes
        self.area_var.trace_add('write', self.on_area_selected)
        self.distrito_var.trace_add('write', self.actualizar_tipos_servicio)
        self.tipo_servicio_var.trace_add('write', self.actualizar_servicios)
        self.tipo_insumo_var.trace_add('write', self.actualizar_insumos)

    def on_area_selected(self, *args):
        area_nombre = self.area_var.get()
        areas = obtener_areas() or []
        area_id = next((a['id'] for a in areas if a['nombre'] == area_nombre), None)
        if area_id:
            distritos = obtener_distritos_por_area(area_id) or []
            self.distrito_cb.set_completion_list([d['nombre'] for d in distritos])
            self.distrito_var.set('')
        else:
            self.distrito_cb.set_completion_list([])
            self.distrito_var.set('')

    def actualizar_tipos_servicio(self, *args):
        distrito_nombre = self.distrito_var.get()
        distritos = obtener_distritos() or []
        distrito_id = next((d['id'] for d in distritos if d['nombre'] == distrito_nombre), None)
        if distrito_id:
            tipos_servicio = obtener_tipos_servicio_por_distrito(distrito_id) or []
            self.tipo_servicio_cb.set_completion_list([ts['descripcion'] for ts in tipos_servicio])
            self.tipo_servicio_var.set('')
            self.servicio_var.set('')
        else:
            self.tipo_servicio_cb.set_completion_list([])
            self.tipo_servicio_var.set('')
            self.servicio_cb.set_completion_list([])
            self.servicio_var.set('')

    def actualizar_servicios(self, *args):
        distrito_nombre = self.distrito_var.get()
        tipo_servicio_desc = self.tipo_servicio_var.get()
        distritos = obtener_distritos() or []
        distrito_id = next((d['id'] for d in distritos if d['nombre'] == distrito_nombre), None)
        if distrito_id:
            tipos_servicio = obtener_tipos_servicio_por_distrito(distrito_id) or []
            tipo_servicio_id = next((ts['id'] for ts in tipos_servicio if ts['descripcion'] == tipo_servicio_desc), None)
            if tipo_servicio_id:
                servicios = obtener_servicios_por_tipo(tipo_servicio_id) or []
                self.servicio_cb.set_completion_list([s['nombre'] for s in servicios])
                self.servicio_var.set('')
                return
        self.servicio_cb.set_completion_list([])
        self.servicio_var.set('')

    def actualizar_insumos(self, *args):
        tipo_insumo_desc = self.tipo_insumo_var.get()
        tipos_insumo = obtener_tipos_insumo() or []
        tipo_insumo_id = next((ti['id'] for ti in tipos_insumo if ti['descripcion'] == tipo_insumo_desc), None)
        if tipo_insumo_id:
            insumos = obtener_insumos_por_tipo(tipo_insumo_id) or []
            self.insumo_cb.set_completion_list([i['nombre'] for i in insumos])
            self.insumo_var.set('')
        else:
            self.insumo_cb.set_completion_list([])
            self.insumo_var.set('')

    def buscar_movimientos(self):
        try:
            fecha_ini = self.fecha_inicio.get_date().strftime('%Y-%m-%d')
            fecha_fin = self.fecha_final.get_date().strftime('%Y-%m-%d')
            resultados = buscar_movimientos_por_filtros(
                fecha_ini, fecha_fin,
                self.area_var.get(),
                self.distrito_var.get(),
                self.tipo_servicio_var.get(),
                self.servicio_var.get(),
                self.tipo_insumo_var.get(),
                self.insumo_var.get(),
                self.presentacion_var.get(),
                self.tipo_movimiento_var.get()
            )
            self.tree.delete(*self.tree.get_children())
            if resultados:
                for mov in resultados:
                    self.tree.insert('', 'end', values=(
                        mov['id'], mov['fecha'], mov['referencia'], mov['tipo_movimiento'],
                        mov['insumo'], mov['cantidad'], mov['observaciones']
                    ))
            else:
                messagebox.showinfo("Info", "No se encontraron movimientos con los filtros seleccionados.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al buscar movimientos: {str(e)}")

    def editar_movimiento(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Seleccione un movimiento para editar")
            return
        mov_values = self.tree.item(selected_item)['values']
        EditarMovimientoDialog(self.parent, mov_values, self.actualizar_movimiento_callback)

    def actualizar_movimiento_callback(self, mov_id, nuevos_datos):
        try:
            actualizar_movimiento(mov_id, nuevos_datos)
            self.buscar_movimientos()
            messagebox.showinfo("Éxito", "Movimiento actualizado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar el movimiento: {str(e)}")

    def eliminar_movimiento(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Seleccione un movimiento para eliminar")
            return
        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este movimiento?"):
            mov_id = self.tree.item(selected_item)['values'][0]
            try:
                eliminar_movimiento(mov_id)
                self.tree.delete(selected_item)
                messagebox.showinfo("Eliminado", "Movimiento eliminado correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar: {str(e)}")

    def cerrar_ventana(self):
        if messagebox.askyesno("Confirmar", "¿Está seguro que desea cerrar esta ventana?"):
            for widget in self.parent.winfo_children():
                widget.destroy()
            self.main_window.show_welcome_screen()

class EditarMovimientoDialog(tk.Toplevel):
    def __init__(self, parent, mov_values, callback):
        super().__init__(parent)
        self.title("Editar Movimiento")
        self.callback = callback
        self.mov_id = mov_values[0]
        self.geometry("400x400")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.center_window()

        # Campos editables
        frame = ttk.Frame(self)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        label_width = 18
        entry_width = 25

        ttk.Label(frame, text="Fecha:", anchor="w", width=label_width).grid(row=0, column=0, sticky="w", pady=5)
        self.fecha_entry = DateEntry(frame, width=entry_width, date_pattern='dd/mm/yyyy')
        self.fecha_entry.set_date(datetime.strptime(mov_values[1], "%Y-%m-%d"))
        self.fecha_entry.grid(row=0, column=1, pady=5)

        ttk.Label(frame, text="Referencia:", anchor="w", width=label_width).grid(row=1, column=0, sticky="w", pady=5)
        self.referencia_entry = ttk.Entry(frame, width=entry_width)
        self.referencia_entry.insert(0, mov_values[2])
        self.referencia_entry.grid(row=1, column=1, pady=5)

        ttk.Label(frame, text="Tipo Movimiento:", anchor="w", width=label_width).grid(row=2, column=0, sticky="w", pady=5)
        self.tipo_movimiento_cb = ttk.Combobox(frame, width=entry_width, state="readonly")
        from src.database.db_manager import obtener_tipos_movimiento
        self.tipo_movimiento_cb['values'] = [tm['descripcion'] for tm in obtener_tipos_movimiento()]
        self.tipo_movimiento_cb.set(mov_values[3])
        self.tipo_movimiento_cb.grid(row=2, column=1, pady=5)

        ttk.Label(frame, text="Insumo:", anchor="w", width=label_width).grid(row=3, column=0, sticky="w", pady=5)
        self.insumo_entry = ttk.Entry(frame, width=entry_width)
        self.insumo_entry.insert(0, mov_values[4])
        self.insumo_entry.grid(row=3, column=1, pady=5)

        ttk.Label(frame, text="Cantidad:", anchor="w", width=label_width).grid(row=4, column=0, sticky="w", pady=5)
        self.cantidad_entry = ttk.Entry(frame, width=entry_width)
        self.cantidad_entry.insert(0, mov_values[5])
        self.cantidad_entry.grid(row=4, column=1, pady=5)

        ttk.Label(frame, text="Observaciones:", anchor="w", width=label_width).grid(row=5, column=0, sticky="w", pady=5)
        self.observaciones_entry = ttk.Entry(frame, width=entry_width)
        self.observaciones_entry.insert(0, mov_values[6])
        self.observaciones_entry.grid(row=5, column=1, pady=5)

        ttk.Button(frame, text="Guardar", command=self.guardar).grid(row=6, column=0, columnspan=2, pady=15)
        ttk.Button(frame, text="Cancelar", command=self.destroy).grid(row=7, column=0, columnspan=2, pady=5)

    def center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws // 2) - (w // 2)
        y = (hs // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")

    def guardar(self):
        try:
            nuevos_datos = {
                "fecha": self.fecha_entry.get_date().strftime('%Y-%m-%d'),
                "referencia": self.referencia_entry.get(),
                "tipo_movimiento": self.tipo_movimiento_cb.get(),
                "insumo": self.insumo_entry.get(),
                "cantidad": float(self.cantidad_entry.get()),
                "observaciones": self.observaciones_entry.get()
            }
            self.callback(self.mov_id, nuevos_datos)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Datos inválidos: {str(e)}")