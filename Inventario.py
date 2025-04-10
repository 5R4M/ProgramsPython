import pandas as pd
import os
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import ttk, PhotoImage
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
    ventana.geometry("600x800")
    ventana.resizable(False, False)

    # Cargar los íconos
    icono_agregar = PhotoImage(file="add.png")  # Ícono para "Agregar Nuevo Insumo"
    icono_agregar_nuevo = PhotoImage(file="add_new.png")  # Ícono para "Agregar Nuevo Insumo"
    icono_modificar = PhotoImage(file="edit.png")  # Ícono para "Modificar Movimiento"
    icono_eliminar = PhotoImage(file="delete.png")  # Ícono para "Eliminar Movimiento"
    icono_guardar = PhotoImage(file="save.png")  # Ícono para "Guardar Movimientos"
    
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

    # Botón para abrir la ventana emergente de agregar insumo
    def abrir_ventana_agregar_insumo():
        ventana_agregar = tk.Toplevel(ventana)
        ventana_agregar.title("Agregar Nuevo Insumo")
        ventana_agregar.geometry("400x200")
        ventana_agregar.resizable(False, False)

        tk.Label(ventana_agregar, text="Nombre del nuevo insumo:").pack(pady=10)
        nuevo_insumo_entry = tk.Entry(ventana_agregar)
        nuevo_insumo_entry.pack(fill="x", padx=20, pady=10)

        def agregar_insumo():
            nuevo_insumo = nuevo_insumo_entry.get().strip()
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

    tk.Button(
    ventana,
    text=" Agregar Nuevo Insumo",  # Texto del botón
    image=icono_agregar_nuevo,  # Ícono
    compound="left",  # Posición del texto (a la derecha del ícono)
    command=abrir_ventana_agregar_insumo,  # Acción al hacer clic
    bd=0,  # Sin bordes
    highlightthickness=0  # Sin borde de enfoque
    ).pack(pady=10)

    # Sección: Formulario de movimiento
    frame_movimiento = tk.LabelFrame(ventana, text="Registrar Movimiento", padx=10, pady=10)
    frame_movimiento.pack(fill="x", padx=10, pady=10)

    entradas = {}
    campos = ["Saldo Anterior", "Entrada Nivel Superior", "Entregado", "No Entregado", "Reajuste"]

    # Organizar los inputs en 3 columnas y 2 filas
    for i, campo in enumerate(campos):
        fila = i // 3  # Dividir en filas de 3 columnas
        columna = i % 3  # Calcular la columna
        tk.Label(frame_movimiento, text=campo + ":").grid(row=fila * 2, column=columna, sticky="w", padx=5, pady=5)  # Etiqueta
        entrada = tk.Entry(frame_movimiento)
        entrada.grid(row=fila * 2 + 1, column=columna, padx=5, pady=5, sticky="ew")  # Input
        entradas[campo] = entrada

    # Ajustar las columnas para que se expandan uniformemente
    for col in range(3):
        frame_movimiento.columnconfigure(col, weight=1)

    # Sección: DataGridView para movimientos temporales
    frame_tabla = tk.LabelFrame(ventana, text="Movimientos", padx=10, pady=10)
    frame_tabla.pack(fill="both", expand=False, padx=10, pady=10)

    # Crear un contenedor para el Treeview y las barras de desplazamiento
    frame_tree = tk.Frame(frame_tabla)
    frame_tree.pack(fill="both", expand=False)

    # Crear el Treeview
    tree = ttk.Treeview(
        frame_tree,
        columns=("Insumo", "Saldo Anterior", "Entrada Nivel Superior", "Entregado", "No Entregado", "Reajuste", "Saldo Final"),
        show="headings",
        height=5
    )

    # Configurar las columnas del Treeview
    for col in tree["columns"]:
        tree.heading(col, text=col)
        tree.column(col, width=150, anchor="center")

    # Crear barra de desplazamiento vertical
    scrollbar_vertical = tk.Scrollbar(frame_tree, orient="vertical", command=tree.yview)
    scrollbar_vertical.pack(side="right", fill="y")

    # Crear barra de desplazamiento horizontal
    scrollbar_horizontal = tk.Scrollbar(frame_tree, orient="horizontal", command=tree.xview)
    scrollbar_horizontal.pack(side="bottom", fill="x")

    # Vincular las barras de desplazamiento al Treeview
    tree.configure(yscrollcommand=scrollbar_vertical.set, xscrollcommand=scrollbar_horizontal.set)

    # Empaquetar el Treeview
    tree.pack(fill="both", expand=False)

    # Sección: Botones debajo del Treeview
    frame_botones = tk.Frame(ventana)
    frame_botones.pack(fill="x", padx=10, pady=20)

    # Botón "Modificar Movimiento" con ícono
    tk.Button(
        frame_botones,
        text=" Modificar Movimiento",  # Texto del botón
        image=icono_modificar,  # Ícono
        compound="left",  # Posición del texto (a la derecha del ícono)
        command=lambda: modificar_movimiento(tree, listado_insumos),
        bd=0,  # Sin bordes
        highlightthickness=0  # Sin borde de enfoque
    ).pack(side="left", padx=5)

    # Botón "Eliminar Movimiento" con ícono
    tk.Button(
        frame_botones,
        text=" Eliminar Movimiento",  # Texto del botón
        image=icono_eliminar,  # Ícono
        compound="left",  # Posición del texto (a la derecha del ícono)
        command=lambda: eliminar_movimiento(tree),
        bd=0,  # Sin bordes
        highlightthickness=0  # Sin borde de enfoque
    ).pack(side="left", padx=5)

    # Botón "Guardar Movimientos" con ícono
    tk.Button(
        frame_botones,
        text=" Guardar Movimientos",  # Texto del botón
        image=icono_guardar,  # Ícono
        compound="left",  # Posición del texto (a la derecha del ícono)
        command=lambda: guardar_movimientos(tree, distrito_var, archivo_excel),
        bd=0,  # Sin bordes
        highlightthickness=0  # Sin borde de enfoque
    ).pack(side="left", padx=5)
    
    # Función para agregar un movimiento al DataGridView
    def agregar_movimiento():
        distrito_seleccionado = distrito_var.get()
        insumo_seleccionado = insumo_var.get()
        if not distrito_seleccionado:
            messagebox.showerror("Error", "Debes seleccionar un distrito.")
            return
        if not insumo_seleccionado:
            messagebox.showerror("Error", "Debes seleccionar un insumo.")
            return

        try:
            saldo_anterior = float(entradas["Saldo Anterior"].get())
            entrada_nivel_superior = float(entradas["Entrada Nivel Superior"].get())
            entregado = float(entradas["Entregado"].get())
            no_entregado = float(entradas["No Entregado"].get())
            reajuste = float(entradas["Reajuste"].get())

            # Calcular saldo final
            saldo_final = saldo_anterior + entrada_nivel_superior - entregado + reajuste

            # Agregar el movimiento al Treeview
            tree.insert("", "end", values=(insumo_seleccionado, saldo_anterior, entrada_nivel_superior, entregado, no_entregado, reajuste, saldo_final))

            # Limpiar los campos de entrada
            for entrada in entradas.values():
                entrada.delete(0, tk.END)

        except ValueError:
            messagebox.showerror("Error", "Todos los campos deben contener valores numéricos válidos.")

    # Función para modificar un movimiento seleccionado
    def modificar_movimiento(tree, listado_insumos):
        seleccion = tree.selection()
        if not seleccion:
            messagebox.showerror("Error", "Debes seleccionar un movimiento para modificar.")
            return

        item = seleccion[0]
        valores = tree.item(item, "values")

        # Crear ventana emergente para modificar el movimiento
        ventana_modificar = tk.Toplevel(ventana)
        ventana_modificar.title("Modificar Movimiento")
        ventana_modificar.geometry("400x500")
        ventana_modificar.resizable(False, False)

        entradas_modificar = {}
        for i, col in enumerate(tree["columns"]):
            if col == "Insumo":
                tk.Label(ventana_modificar, text=col).pack(anchor="w", padx=10, pady=5)
                insumo_modificar_combobox = ttk.Combobox(ventana_modificar, state="readonly")
                insumo_modificar_combobox["values"] = listado_insumos["Insumo"].tolist()
                insumo_modificar_combobox.set(valores[i])
                insumo_modificar_combobox.pack(fill="x", padx=10, pady=5)
                entradas_modificar[col] = insumo_modificar_combobox
            else:
                tk.Label(ventana_modificar, text=col).pack(anchor="w", padx=10, pady=5)
                entrada = tk.Entry(ventana_modificar)
                entrada.insert(0, valores[i])
                entrada.pack(fill="x", padx=10, pady=5)
                entradas_modificar[col] = entrada

        def guardar_cambios():
            nuevos_valores = [entrada.get() if isinstance(entrada, tk.Entry) else entrada.get() for entrada in entradas_modificar.values()]
            tree.item(item, values=nuevos_valores)
            ventana_modificar.destroy()

        tk.Button(ventana_modificar, text="Guardar Cambios", command=guardar_cambios).pack(pady=10)

    # Función para eliminar un movimiento seleccionado
    def eliminar_movimiento(tree):
        seleccion = tree.selection()
        if not seleccion:
            messagebox.showerror("Error", "Debes seleccionar un movimiento para eliminar.")
            return

        confirmacion = messagebox.askyesno("Confirmación", "¿Estás seguro de que deseas eliminar este movimiento?")
        if confirmacion:
            tree.delete(seleccion[0])

    # Función para guardar los movimientos en el archivo Excel
    def guardar_movimientos(tree, distrito_var, archivo_excel):
        distrito_seleccionado = distrito_var.get()
        if not distrito_seleccionado:
            messagebox.showerror("Error", "Debes seleccionar un distrito.")
            return

        # Obtener los datos del Treeview
        movimientos = [tree.item(item, "values") for item in tree.get_children()]
        if not movimientos:
            messagebox.showerror("Error", "No hay movimientos para guardar.")
            return

        # Crear un DataFrame con los movimientos
        columnas = ["Insumo", "Saldo Anterior", "Entrada Nivel Superior", "Entregado", "No Entregado", "Reajuste", "Saldo Final"]
        df_movimientos = pd.DataFrame(movimientos, columns=columnas)

        # Guardar en el archivo Excel
        try:
            with pd.ExcelWriter(archivo_excel, engine="openpyxl", mode="a", if_sheet_exists="overlay") as writer:
                df_movimientos.to_excel(writer, sheet_name=distrito_seleccionado, index=False)

            aplicar_formato_excel(archivo_excel, distrito_seleccionado)
            messagebox.showinfo("Éxito", f"Los movimientos se han guardado en el distrito '{distrito_seleccionado}'.")
            tree.delete(*tree.get_children())  # Limpiar el Treeview después de guardar
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")

    # Botón para agregar
    boton_agregar = tk.Button(
        frame_movimiento,
        text=" Agregar Movimiento",  # Texto del botón
        image=icono_agregar,  # Ícono
        compound="left",  # Posición del texto (a la derecha del ícono)
        command=agregar_movimiento,  # Acción al hacer clic
        bd=0,  # Sin bordes
        highlightthickness=0  # Sin borde de enfoque
    )
    boton_agregar.grid(row=4, column=0, columnspan=3, pady=10)  # Colocar el botón en la fila 4, ocupando las 3 columnas

    # Ejecutar la ventana
    ventana.mainloop()

# Ejecutar el programa
gestionar_insumos()