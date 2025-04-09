import pandas as pd
import os
import tkinter as tk
from tkinter import ttk, messagebox
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Side, Font

# Función para aplicar formato a la tabla
def aplicar_formato_excel(archivo_excel, hoja):
    wb = load_workbook(archivo_excel)
    if hoja in wb.sheetnames:
        ws = wb[hoja]

        # Aplicar formato a los encabezados
        font_bold = Font(bold=True)
        alignment_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

        for col in ws.iter_cols(min_row=1, max_row=1):  # Encabezados
            for cell in col:
                cell.font = font_bold
                cell.alignment = alignment_center
                cell.border = thin_border

        # Aplicar formato a las celdas de datos
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
            for cell in row:
                cell.alignment = alignment_center
                cell.border = thin_border

        # Ajustar el ancho de las columnas
        columnas_fijas = ["Saldo Anterior", "Entrada Nivel Superior", "Entregado", "No Entregado", "Reajuste", "Saldo Final"]
        for col in ws.columns:
            col_letter = col[0].column_letter  # Obtener la letra de la columna
            if col[0].value in columnas_fijas:  # Si el título está en las columnas fijas
                ws.column_dimensions[col_letter].width = 20  # Ancho fijo
            else:
                # Ajuste automático para las demás columnas
                max_length = 0
                for cell in col:
                    try:
                        if cell.value:  # Si la celda tiene un valor
                            max_length = max(max_length, len(str(cell.value)))
                    except:
                        pass
                adjusted_width = max_length + 2  # Agregar un poco de espacio adicional
                ws.column_dimensions[col_letter].width = adjusted_width

        # Eliminar cuadrícula de fondo
        ws.sheet_view.showGridLines = False

        wb.save(archivo_excel)
    wb.close()

# Función principal
def gestionar_insumos():
    # Nombre del archivo Excel
    archivo_excel = "insumos_movimientos.xlsx"

    # Verificar si el archivo ya existe
    if not os.path.exists(archivo_excel):
        # Crear un archivo inicial con una pestaña de insumos vacía
        df_insumos = pd.DataFrame({"Insumo": []})  # Crear un DataFrame vacío para insumos
        df_distritos = pd.DataFrame({"Distrito": ["Distrito 1", "Distrito 2", "Distrito 3"]})  # Ejemplo de distritos
        with pd.ExcelWriter(archivo_excel, engine="openpyxl") as writer:
            df_insumos.to_excel(writer, sheet_name="Listado de Insumos", index=False)
            df_distritos.to_excel(writer, sheet_name="Distritos", index=False)

    # Verificar si las pestañas necesarias existen
    try:
        listado_insumos = pd.read_excel(archivo_excel, sheet_name="Listado de Insumos")
    except ValueError:
        listado_insumos = pd.DataFrame({"Insumo": []})

    try:
        distritos = pd.read_excel(archivo_excel, sheet_name="Distritos")
    except ValueError:
        distritos = pd.DataFrame({"Distrito": ["Distrito 1", "Distrito 2", "Distrito 3"]})

    # Crear la ventana principal
    ventana = tk.Tk()
    ventana.title("Gestión de Insumos")
    ventana.geometry("600x800")  # Aumentar la altura para que todo sea visible
    ventana.resizable(False, False)

    # Sección: Selección de distrito
    frame_distrito = tk.LabelFrame(ventana, text="Seleccionar Distrito", padx=10, pady=10)
    frame_distrito.pack(fill="x", padx=10, pady=10)
    tk.Label(frame_distrito, text="Selecciona un distrito:").pack(anchor="w")
    distrito_var = tk.StringVar()
    distrito_combobox = ttk.Combobox(frame_distrito, textvariable=distrito_var, state="readonly")
    distrito_combobox["values"] = distritos["Distrito"].tolist()
    distrito_combobox.pack(fill="x", pady=5)

    # Sección: Selección de insumo
    frame_insumo = tk.LabelFrame(ventana, text="Seleccionar Insumo", padx=10, pady=10)
    frame_insumo.pack(fill="x", padx=10, pady=10)
    tk.Label(frame_insumo, text="Selecciona un insumo:").pack(anchor="w")
    insumo_var = tk.StringVar()
    insumo_combobox = ttk.Combobox(frame_insumo, textvariable=insumo_var, state="readonly")
    insumo_combobox["values"] = listado_insumos["Insumo"].tolist()
    insumo_combobox.pack(fill="x", pady=5)

    # Función para abrir la ventana emergente de agregar insumo
    def abrir_ventana_agregar_insumo():
        ventana_agregar = tk.Toplevel(ventana)
        ventana_agregar.title("Agregar Nuevo Insumo")
        ventana_agregar.geometry("400x200")
        ventana_agregar.resizable(False, False)

        tk.Label(ventana_agregar, text="Nombre del nuevo insumo:").pack(pady=10)
        nuevo_insumo_entry = tk.Entry(ventana_agregar)
        nuevo_insumo_entry.pack(fill="x", padx=20, pady=10)

        def agregar_insumo():
            nuevo_insumo = nuevo_insumo_entry.get()
            if not nuevo_insumo:
                messagebox.showerror("Error", "Debes ingresar un nombre para el insumo.")
                return

            if nuevo_insumo in listado_insumos["Insumo"].values:
                messagebox.showerror("Error", "El insumo ya existe en el listado.")
                return

            # Agregar el nuevo insumo al listado
            nuevo_insumo_df = pd.DataFrame({"Insumo": [nuevo_insumo]})
            listado_insumos_actualizado = pd.concat([listado_insumos, nuevo_insumo_df], ignore_index=True)

            # Ordenar el listado alfabéticamente
            listado_insumos_actualizado = listado_insumos_actualizado.sort_values(by="Insumo").reset_index(drop=True)

            # Guardar el listado actualizado en el archivo Excel
            with pd.ExcelWriter(archivo_excel, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
                listado_insumos_actualizado.to_excel(writer, sheet_name="Listado de Insumos", index=False)
                distritos.to_excel(writer, sheet_name="Distritos", index=False)

            # Actualizar el combobox
            insumo_combobox["values"] = listado_insumos_actualizado["Insumo"].tolist()
            messagebox.showinfo("Éxito", "El insumo se ha agregado correctamente.")
            nuevo_insumo_entry.delete(0, tk.END)
            ventana_agregar.destroy()

        tk.Button(ventana_agregar, text="Guardar Insumo", command=agregar_insumo).pack(pady=10)

    # Botón para abrir la ventana emergente
    tk.Button(ventana, text="Agregar Insumo", command=abrir_ventana_agregar_insumo).pack(pady=10)

    # Sección: Formulario de movimiento
    frame_movimiento = tk.LabelFrame(ventana, text="Registrar Movimiento", padx=10, pady=10)
    frame_movimiento.pack(fill="x", padx=10, pady=10)
    entradas = {}
    campos = ["Saldo Anterior", "Entrada Nivel Superior", "Entregado", "No Entregado", "Reajuste"]
    for campo in campos:
        tk.Label(frame_movimiento, text=campo + ":").pack(anchor="w")
        entrada = tk.Entry(frame_movimiento)
        entrada.pack(fill="x", pady=5)
        entradas[campo] = entrada

    def guardar_movimiento():
        distrito_seleccionado = distrito_var.get()
        insumo_seleccionado = insumo_var.get()
        if not distrito_seleccionado:
            messagebox.showerror("Error", "Debes seleccionar un distrito.")
            return
        if not insumo_seleccionado:
            messagebox.showerror("Error", "Debes seleccionar un insumo.")
            return

        try:
            # Leer la pestaña del distrito si ya existe
            try:
                movimientos_distrito = pd.read_excel(archivo_excel, sheet_name=distrito_seleccionado)
            except ValueError:
                movimientos_distrito = pd.DataFrame()

            # Verificar si el insumo ya existe en el distrito
            if not movimientos_distrito.empty and insumo_seleccionado in movimientos_distrito["Insumo"].values:
                messagebox.showwarning("Advertencia", f"El insumo '{insumo_seleccionado}' ya ha sido ingresado en el distrito '{distrito_seleccionado}'.")
                return

            # Obtener los valores ingresados
            saldo_anterior = float(entradas["Saldo Anterior"].get())
            entrada_nivel_superior = float(entradas["Entrada Nivel Superior"].get())
            entregado = float(entradas["Entregado"].get())
            no_entregado = float(entradas["No Entregado"].get())
            reajuste = float(entradas["Reajuste"].get())

            # Calcular saldo final
            saldo_final = saldo_anterior + entrada_nivel_superior - entregado + reajuste

            # Crear un DataFrame con los datos del movimiento
            datos_movimiento = {
                "Insumo": [insumo_seleccionado],
                "Saldo Anterior": [saldo_anterior],
                "Entrada Nivel Superior": [entrada_nivel_superior],
                "Entregado": [entregado],
                "No Entregado": [no_entregado],
                "Reajuste": [reajuste],
                "Saldo Final": [saldo_final]
            }
            df_movimiento = pd.DataFrame(datos_movimiento)

            # Agregar el nuevo movimiento
            movimientos_actualizados = pd.concat([movimientos_distrito, df_movimiento], ignore_index=True)
            with pd.ExcelWriter(archivo_excel, engine="openpyxl", mode="a", if_sheet_exists="overlay") as writer:
                movimientos_actualizados.to_excel(writer, sheet_name=distrito_seleccionado, index=False)

            # Aplicar formato a la pestaña del distrito
            aplicar_formato_excel(archivo_excel, distrito_seleccionado)

            messagebox.showinfo("Éxito", f"El movimiento se ha registrado en la pestaña '{distrito_seleccionado}'.")
            ventana.destroy()

        except ValueError:
            messagebox.showerror("Error", "Todos los campos deben contener valores numéricos válidos.")

    # Botón para guardar el movimiento
    tk.Button(frame_movimiento, text="Guardar Movimiento", command=guardar_movimiento).pack(pady=10)

    # Ejecutar la ventana
    ventana.mainloop()

# Ejecutar el programa
gestionar_insumos()