import tkinter as tk
from tkinter import ttk
from tkinter import PhotoImage
import sqlite3
import os

# Función para inicializar la base de datos SQLite
def inicializar_base_datos():
    conexion = sqlite3.connect("insumos.db")
    cursor = conexion.cursor()

    # Crear tablas si no existen
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Distritos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ListadoInsumos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Presentaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            distrito TEXT NOT NULL,
            insumo TEXT NOT NULL,
            presentacion TEXT NOT NULL,
            saldo_anterior REAL,
            entrada_nivel_superior REAL,
            entregado REAL,
            no_entregado REAL,
            reajuste REAL,
            saldo_final REAL
        )
    """)
    conexion.commit()
    conexion.close()

# Función para cargar datos desde SQLite en un combobox
def cargar_datos_combobox(combobox, tabla):
    conexion = sqlite3.connect("insumos.db")
    cursor = conexion.cursor()

    # Obtener los datos de la tabla correspondiente
    cursor.execute(f"SELECT nombre FROM {tabla}")
    datos = [fila[0] for fila in cursor.fetchall()]

    # Cargar los datos en el combobox
    combobox["values"] = datos

    # Mostrar advertencia si no hay datos
    if not datos:
        print(f"Advertencia: No hay datos disponibles en la tabla '{tabla}'.")
        combobox.set("No hay datos disponibles")

    conexion.close()

# Función para abrir la ventana de "Ingreso de Insumos"
def abrir_ingreso_insumos():
    import tkinter as tk
    from tkinter import ttk, messagebox
    from tkinter import ttk, PhotoImage

    # Función principal
    def gestionar_insumos():

        # Crear la ventana principal
        ventana = tk.Toplevel()
        ventana.title("Ingreso de Insumos")
        ventana.geometry("800x1000")
        ventana.resizable(False, False)
        
        tk.Label(ventana, text="Ingreso de Insumos", font=("Arial", 14)).pack(pady=10)
        
        # Sección: Selección de distrito
        frame_distrito = tk.LabelFrame(ventana, text="Seleccionar Distrito", padx=10, pady=10)
        frame_distrito.pack(fill="x", padx=10, pady=10)
        tk.Label(frame_distrito, text="Selecciona un distrito:").pack(anchor="w")
        distrito_var = tk.StringVar()
        distrito_combobox = ttk.Combobox(frame_distrito, textvariable=distrito_var, state="readonly")
        cargar_datos_combobox(distrito_combobox, "Distritos")
        distrito_combobox.pack(fill="x", pady=5)
        
        # Sección: Selección de insumo
        frame_insumo = tk.LabelFrame(ventana, text="Seleccionar Insumo", padx=10, pady=10)
        frame_insumo.pack(fill="x", padx=10, pady=10)
        tk.Label(frame_insumo, text="Selecciona un insumo:").pack(anchor="w")
        insumo_var = tk.StringVar()
        insumo_combobox = ttk.Combobox(frame_insumo, textvariable=insumo_var, state="readonly")
        cargar_datos_combobox(insumo_combobox, "ListadoInsumos")
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

                # Verificar si el insumo ya existe en la base de datos
                conexion = sqlite3.connect("insumos.db")
                cursor = conexion.cursor()
                cursor.execute("SELECT COUNT(*) FROM ListadoInsumos WHERE nombre = ?", (nuevo_insumo,))
                if cursor.fetchone()[0] > 0:
                    messagebox.showerror("Error", "El insumo ya existe en el listado.")
                    conexion.close()
                    return

                # Insertar el nuevo insumo en la base de datos
                cursor.execute("INSERT INTO ListadoInsumos (nombre) VALUES (?)", (nuevo_insumo,))
                conexion.commit()
                conexion.close()

                # Actualizar el combobox
                cargar_datos_combobox(insumo_combobox, "ListadoInsumos")
                messagebox.showinfo("Éxito", "El insumo se ha agregado correctamente.")
                nuevo_insumo_entry.delete(0, tk.END)
                ventana_agregar.destroy()

            tk.Button(
            ventana_agregar,
            text=" Guardar Insumo",  # Texto del botón
            image=iconos["icono_guardar_otro"],  # Ícono
            compound="left",  # Posición del texto (a la derecha del ícono)
            command=agregar_insumo,  # Acción al hacer clic
            bd=0,  # Sin bordes
            highlightthickness=0  # Sin borde de enfoque
            ).pack(pady=10)
            
            tk.Button(
                ventana_agregar,
                text="Cerrar",
                image=iconos["icono_cerrar"],
                compound="left",
                command=ventana_agregar.destroy,
                padx=10,
                pady=5,
                bd=0,
                highlightthickness=0
            ).pack(pady=10)

        tk.Button(
        ventana,
        text=" Agregar Nuevo Insumo",  # Texto del botón
        image=iconos["icono_agregar_nuevo"],  # Ícono
        compound="left",  # Posición del texto (a la derecha del ícono)
        command=abrir_ventana_agregar_insumo,  # Acción al hacer clic
        bd=0,  # Sin bordes
        highlightthickness=0  # Sin borde de enfoque
        ).pack(pady=10)
        
        # Sección: Selección de presentación
        frame_presentacion = tk.LabelFrame(ventana, text="Seleccionar Presentación", padx=10, pady=10)
        frame_presentacion.pack(fill="x", padx=10, pady=10)
        tk.Label(frame_presentacion, text="Selecciona una presentación:").pack(anchor="w")
        presentacion_var = tk.StringVar()
        presentacion_combobox = ttk.Combobox(frame_presentacion, textvariable=presentacion_var, state="readonly")
        cargar_datos_combobox(presentacion_combobox, "Presentaciones")
        presentacion_combobox.pack(fill="x", pady=5)

        # Función para abrir la ventana emergente de agregar presentación
        def abrir_ventana_agregar_presentacion():
            ventana_agregar_presentacion = tk.Toplevel(ventana)
            ventana_agregar_presentacion.title("Agregar Nueva Presentación")
            ventana_agregar_presentacion.geometry("400x200")
            ventana_agregar_presentacion.resizable(False, False)

            tk.Label(ventana_agregar_presentacion, text="Nombre de la nueva presentación:").pack(pady=10)
            nueva_presentacion_entry = tk.Entry(ventana_agregar_presentacion)
            nueva_presentacion_entry.pack(fill="x", padx=20, pady=10)

            def agregar_presentacion():
                nueva_presentacion = nueva_presentacion_entry.get().strip()
                if not nueva_presentacion:
                    messagebox.showerror("Error", "Debes ingresar un nombre para la presentación.")
                    return

                # Verificar si la presentación ya existe en la base de datos
                conexion = sqlite3.connect("insumos.db")
                cursor = conexion.cursor()
                cursor.execute("SELECT COUNT(*) FROM Presentaciones WHERE nombre = ?", (nueva_presentacion,))
                if cursor.fetchone()[0] > 0:
                    messagebox.showerror("Error", "La presentación ya existe en el listado.")
                    conexion.close()
                    return

                # Insertar la nueva presentación en la base de datos
                cursor.execute("INSERT INTO Presentaciones (nombre) VALUES (?)", (nueva_presentacion,))
                conexion.commit()
                conexion.close()

                # Actualizar el combobox
                cargar_datos_combobox(presentacion_combobox, "Presentaciones")
                messagebox.showinfo("Éxito", "La presentación se ha agregado correctamente.")
                nueva_presentacion_entry.delete(0, tk.END)
                ventana_agregar_presentacion.destroy()

            tk.Button(
                ventana_agregar_presentacion,
                text=" Guardar Presentación",  # Texto del botón
                image=iconos["icono_guardar_otro"],  # Ícono
                compound="left",  # Posición del texto (a la derecha del ícono)
                command=agregar_presentacion,  # Acción al hacer clic
                bd=0,  # Sin bordes
                highlightthickness=0  # Sin borde de enfoque
            ).pack(pady=10)
            
            tk.Button(
                ventana_agregar_presentacion,
                text="Cerrar",
                image=iconos["icono_cerrar"],
                compound="left",
                command=ventana_agregar_presentacion.destroy,
                padx=10,
                pady=5,
                bd=0,
                highlightthickness=0
            ).pack(pady=10)  

        # Botón para abrir la ventana emergente de agregar presentación
        tk.Button(
        ventana,
        text=" Agregar Nueva Presentación",  # Texto del botón
        image=iconos["icono_agregar_otro"],  # Ícono
        compound="left",  # Posición del texto (a la derecha del ícono)
        command=abrir_ventana_agregar_presentacion,  # Acción al hacer clic
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
            columns=("Insumo", "Presentación", "Saldo Anterior", "Entrada Nivel Superior", "Entregado", "No Entregado", "Reajuste", "Saldo Final"),
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
            image=iconos["icono_modificar"],  # Ícono
            compound="left",  # Posición del texto (a la derecha del ícono)
            command=lambda: modificar_movimiento(tree),
            bd=0,  # Sin bordes
            highlightthickness=0  # Sin borde de enfoque
        ).pack(side="left", padx=5)

        # Botón "Eliminar Movimiento" con ícono
        tk.Button(
            frame_botones,
            text=" Eliminar Movimiento",  # Texto del botón
            image=iconos["icono_eliminar"],  # Ícono
            compound="left",  # Posición del texto (a la derecha del ícono)
            command=lambda: eliminar_movimiento(tree),
            bd=0,  # Sin bordes
            highlightthickness=0  # Sin borde de enfoque
        ).pack(side="left", padx=5)

        # Botón "Guardar Movimientos" con ícono
        tk.Button(
            frame_botones,
            text=" Guardar Movimientos",  # Texto del botón
            image=iconos["icono_guardar"],  # Ícono
            compound="left",  # Posición del texto (a la derecha del ícono)
            command=lambda: guardar_movimientos(tree, distrito_var),
            bd=0,  # Sin bordes
            highlightthickness=0  # Sin borde de enfoque
        ).pack(side="left", padx=5)
        
        # Función para agregar un movimiento al DataGridView
        def agregar_movimiento():
            distrito_seleccionado = distrito_var.get()
            insumo_seleccionado = insumo_var.get()
            presentacion_seleccionada = presentacion_var.get()
            if not distrito_seleccionado:
                messagebox.showerror("Error", "Debes seleccionar un distrito.")
                return
            if not insumo_seleccionado:
                messagebox.showerror("Error", "Debes seleccionar un insumo.")
                return
            if not presentacion_seleccionada:
                messagebox.showerror("Error", "Debes seleccionar una presentación.")
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
                tree.insert("", "end", values=(insumo_seleccionado, presentacion_seleccionada, saldo_anterior, entrada_nivel_superior, entregado, no_entregado, reajuste, saldo_final))

                # Limpiar los campos de entrada
                for entrada in entradas.values():
                    entrada.delete(0, tk.END)

            except ValueError:
                messagebox.showerror("Error", "Todos los campos deben contener valores numéricos válidos.")

        # Función para modificar un movimiento seleccionado
        def modificar_movimiento(tree):
            # Verificar si hay movimientos en el Treeview
            if not tree.get_children():
                messagebox.showerror("Error", "No hay movimientos para modificar.")
                return

            # Verificar si se ha seleccionado un movimiento
            seleccion = tree.selection()
            if not seleccion:
                messagebox.showerror("Error", "Debes seleccionar un movimiento para modificar.")
                return

            # Obtener el elemento seleccionado
            item = seleccion[0]
            valores = tree.item(item, "values")

            # Crear ventana emergente para modificar el movimiento
            ventana_modificar = tk.Toplevel()
            ventana_modificar.title("Modificar Movimiento")
            ventana_modificar.geometry("400x600")
            ventana_modificar.resizable(False, False)

            # Obtener insumos y presentaciones desde SQLite
            conexion = sqlite3.connect("insumos.db")
            cursor = conexion.cursor()
            cursor.execute("SELECT nombre FROM ListadoInsumos")
            insumos = [fila[0] for fila in cursor.fetchall()]
            cursor.execute("SELECT nombre FROM Presentaciones")
            presentaciones = [fila[0] for fila in cursor.fetchall()]
            conexion.close()

            # Crear entradas para modificar los valores
            entradas_modificar = {}
            for i, col in enumerate(tree["columns"]):
                if col == "Insumo":
                    tk.Label(ventana_modificar, text=col).pack(anchor="w", padx=10, pady=5)
                    insumo_modificar_combobox = ttk.Combobox(ventana_modificar, state="readonly")
                    insumo_modificar_combobox["values"] = insumos
                    insumo_modificar_combobox.set(valores[i])
                    insumo_modificar_combobox.pack(fill="x", padx=10, pady=5)
                    entradas_modificar[col] = insumo_modificar_combobox
                elif col == "Presentación":
                    tk.Label(ventana_modificar, text=col).pack(anchor="w", padx=10, pady=5)
                    presentacion_modificar_combobox = ttk.Combobox(ventana_modificar, state="readonly")
                    presentacion_modificar_combobox["values"] = presentaciones
                    presentacion_modificar_combobox.set(valores[i])
                    presentacion_modificar_combobox.pack(fill="x", padx=10, pady=5)
                    entradas_modificar[col] = presentacion_modificar_combobox
                else:
                    tk.Label(ventana_modificar, text=col).pack(anchor="w", padx=10, pady=5)
                    entrada = tk.Entry(ventana_modificar)
                    entrada.insert(0, valores[i])
                    entrada.pack(fill="x", padx=10, pady=5)
                    entradas_modificar[col] = entrada

            # Función para guardar los cambios
            def guardar_cambios():
                nuevos_valores = [
                    entrada.get() if isinstance(entrada, tk.Entry) else entrada.get()
                    for entrada in entradas_modificar.values()
                ]
                tree.item(item, values=nuevos_valores)
                ventana_modificar.destroy()

            # Botón para guardar los cambios
            tk.Button(
                ventana_modificar,
                text=" Guardar Cambios",
                image=iconos.get("icono_editar_otro"),  # Verificar si el ícono existe
                compound="left",
                command=guardar_cambios,
                bd=0,
                highlightthickness=0
            ).pack(pady=10)
            
            tk.Button(
                ventana_modificar,
                text="Cerrar",
                image=iconos["icono_cerrar"],
                compound="left",
                command=ventana_modificar.destroy,
                padx=10,
                pady=5,
                bd=0,
                highlightthickness=0
            ).pack(pady=10)

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
        def guardar_movimientos(tree, distrito_var):
            distrito_seleccionado = distrito_var.get()
            if not distrito_seleccionado:
                messagebox.showerror("Error", "Debes seleccionar un distrito.")
                return

            # Obtener los datos del Treeview
            movimientos = [tree.item(item, "values") for item in tree.get_children()]
            if not movimientos:
                messagebox.showerror("Error", "No hay movimientos para guardar.")
                return

            # Guardar los movimientos en la base de datos
            conexion = sqlite3.connect("insumos.db")
            cursor = conexion.cursor()

            # Crear una tabla para movimientos si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Movimientos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    distrito TEXT NOT NULL,
                    insumo TEXT NOT NULL,
                    presentacion TEXT NOT NULL,
                    saldo_anterior REAL,
                    entrada_nivel_superior REAL,
                    entregado REAL,
                    no_entregado REAL,
                    reajuste REAL,
                    saldo_final REAL
                )
            """)

            # Insertar los movimientos en la tabla, evitando duplicados
            for movimiento in movimientos:
                cursor.execute("""
                    SELECT COUNT(*) FROM Movimientos
                    WHERE distrito = ? AND insumo = ? AND presentacion = ?
                """, (distrito_seleccionado, movimiento[0], movimiento[1]))
                if cursor.fetchone()[0] > 0:
                    messagebox.showwarning("Advertencia", f"El movimiento con insumo '{movimiento[0]}' y presentación '{movimiento[1]}' ya existe.")
                    continue

                cursor.execute("""
                    INSERT INTO Movimientos (
                        distrito, insumo, presentacion, saldo_anterior, entrada_nivel_superior,
                        entregado, no_entregado, reajuste, saldo_final
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (distrito_seleccionado, *movimiento))

            conexion.commit()
            conexion.close()

            # Limpiar el Treeview después de guardar
            tree.delete(*tree.get_children())
            messagebox.showinfo("Éxito", f"Los movimientos se han guardado en el distrito '{distrito_seleccionado}'.")

        # Botón para agregar
        boton_agregar = tk.Button(
            frame_movimiento,
            text=" Agregar Movimiento",  # Texto del botón
            image=iconos["icono_agregar"],  # Ícono
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
    
    pass

import pandas as pd
from tkinter import filedialog, messagebox
# Función para abrir la ventana de "Gestión de Insumos"
def abrir_gestion_insumos():
    ventana_gestion_insumos = tk.Toplevel()
    ventana_gestion_insumos.title("Gestión de Insumos")
    ventana_gestion_insumos.geometry("400x300")
    ventana_gestion_insumos.resizable(False, False)

    tk.Label(ventana_gestion_insumos, text="Gestión de Insumos", font=("Arial", 14)).pack(pady=10)
    
    frame_gestion_insumos = tk.LabelFrame(ventana_gestion_insumos, text="Gestion de Insumos", padx=5, pady=5, font=("Arial", 10))
    frame_gestion_insumos.pack(fill="x", padx=10, pady=10)
    
    # Función genérica para cargar datos desde un archivo de Excel
    def cargar_datos_desde_excel(tabla, columna_esperada):
        archivo = filedialog.askopenfilename(
            title="Seleccionar archivo de Excel",
            filetypes=[("Archivos de Excel", "*.xlsx *.xls")]
        )
        if not archivo:
            return  # Si no se selecciona un archivo, salir de la función

        try:
            # Leer el archivo de Excel
            df = pd.read_excel(archivo)

            # Verificar que la columna esperada exista
            if columna_esperada not in df.columns:
                messagebox.showerror("Error", f"El archivo debe contener una columna llamada '{columna_esperada}'.")
                return

            # Conectar a la base de datos
            conexion = sqlite3.connect("insumos.db")
            cursor = conexion.cursor()

            # Insertar los datos en la base de datos, evitando duplicados
            for dato in df[columna_esperada]:
                dato = str(dato).strip()  # Limpiar espacios en blanco
                if dato:  # Verificar que no esté vacío
                    cursor.execute(f"SELECT COUNT(*) FROM {tabla} WHERE nombre = ?", (dato,))
                    if cursor.fetchone()[0] == 0:  # Si no existe, insertarlo
                        cursor.execute(f"INSERT INTO {tabla} (nombre) VALUES (?)", (dato,))

            conexion.commit()
            conexion.close()

            messagebox.showinfo("Éxito", f"Los datos se han cargado correctamente desde el archivo.")
        except Exception as e:
            messagebox.showerror("Error", f"Hubo un problema al cargar el archivo: {e}")

    # Botón para cargar listado de insumos    
    tk.Button(
        frame_gestion_insumos,
        text="Cargar Listado de Insumos",  # Texto del botón
        image=iconos["icono_subir1"],  # Ícono
        compound="left",  # Posición del texto (a la derecha del ícono)
        font=("Arial", 12),  # Fuente del texto
        command=lambda: cargar_datos_desde_excel("ListadoInsumos", "Insumo"),  # Acción al hacer clic
        padx=10,  # Espaciado horizontal entre ícono y texto
        pady=5,  # Espaciado vertical
        bd=0,  # Sin bordes
        highlightthickness=0  # Sin borde de enfoque
    ).pack(pady=5)

    # Botón para cargar listado de presentaciones    
    tk.Button(
        frame_gestion_insumos,
        text="Cargar Listado de Presentaciones",  # Texto del botón
        image=iconos["icono_subir2"],  # Ícono
        compound="left",  # Posición del texto (a la derecha del ícono)
        font=("Arial", 12),  # Fuente del texto
        command=lambda: cargar_datos_desde_excel("Presentaciones", "Presentación"),  # Acción al hacer clic
        padx=10,  # Espaciado horizontal entre ícono y texto
        pady=5,  # Espaciado vertical
        bd=0,  # Sin bordes
        highlightthickness=0  # Sin borde de enfoque
    ).pack(pady=5)

    # Ejemplo de botón para cerrar la ventana
    tk.Button(
        frame_gestion_insumos,
       text="Cerrar",
        image=iconos["icono_cerrar"],
        compound="left",
        command=ventana_gestion_insumos.destroy,
        font=("Arial", 12),
        padx=10,
        pady=5,
        bd=0,
        highlightthickness=0
    ).pack(pady=20)
    
# Función para abrir la ventana de "Gestión de Servicios"
def abrir_gestion_servicios():
    ventana_gestion_servicios = tk.Toplevel()
    ventana_gestion_servicios.title("Gestión de Servicios")
    ventana_gestion_servicios.geometry("400x300")
    ventana_gestion_servicios.resizable(False, False)

    tk.Label(ventana_gestion_servicios, text="Gestión de Servicios", font=("Arial", 14)).pack(pady=10)
    
    frame_gestion_servicios = tk.LabelFrame(ventana_gestion_servicios, text="Gestion de Servicios", padx=5, pady=5, font=("Arial", 10))
    frame_gestion_servicios.pack(fill="x", padx=10, pady=10)
    
    # Función para cargar distritos desde un archivo de Excel
    def cargar_distritos_desde_excel():
        archivo = filedialog.askopenfilename(
            title="Seleccionar archivo de Excel",
            filetypes=[("Archivos de Excel", "*.xlsx *.xls")]
        )
        if not archivo:
            return  # Si no se selecciona un archivo, salir de la función

        try:
            # Leer el archivo de Excel
            df = pd.read_excel(archivo)

            # Verificar que la columna "Distrito" exista
            if "Distrito" not in df.columns:
                messagebox.showerror("Error", "El archivo debe contener una columna llamada 'Distrito'.")
                return

            # Conectar a la base de datos
            conexion = sqlite3.connect("insumos.db")
            cursor = conexion.cursor()

            # Insertar los distritos en la base de datos, evitando duplicados
            for distrito in df["Distrito"]:
                distrito = str(distrito).strip()  # Limpiar espacios en blanco
                if distrito:  # Verificar que no esté vacío
                    cursor.execute("SELECT COUNT(*) FROM Distritos WHERE nombre = ?", (distrito,))
                    if cursor.fetchone()[0] == 0:  # Si no existe, insertarlo
                        cursor.execute("INSERT INTO Distritos (nombre) VALUES (?)", (distrito,))

            conexion.commit()
            conexion.close()

            messagebox.showinfo("Éxito", "Los distritos se han cargado correctamente desde el archivo.")
        except Exception as e:
            messagebox.showerror("Error", f"Hubo un problema al cargar el archivo: {e}")

    # Botón para cargar listado de distritos   
    tk.Button(
        frame_gestion_servicios,
        text="Cargar Listado de Distritos",  # Texto del botón
        image=iconos["icono_subir1"],  # Ícono
        compound="left",  # Posición del texto (a la derecha del ícono)
        font=("Arial", 12),  # Fuente del texto
        command=cargar_distritos_desde_excel,  # Acción al hacer clic
        padx=10,  # Espaciado horizontal entre ícono y texto
        pady=5,  # Espaciado vertical
        bd=0,  # Sin bordes
        highlightthickness=0  # Sin borde de enfoque
    ).pack(pady=5)

    # Ejemplo de botón para cerrar la ventana
    tk.Button(
        frame_gestion_servicios,
        text="Cerrar",
        image=iconos["icono_cerrar"],
        compound="left",
        command=ventana_gestion_servicios.destroy,
        font=("Arial", 12),
        padx=10,
        pady=5,
        bd=0,
        highlightthickness=0
    ).pack(pady=20)

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def abrir_reportes():
    ventana_reportes = tk.Toplevel()
    ventana_reportes.title("Reportes")
    ventana_reportes.geometry("400x300")
    ventana_reportes.resizable(False, False)

    tk.Label(ventana_reportes, text="Reporte de Movimientos", font=("Arial", 14)).pack(pady=10)
    
    frame_reportes = tk.LabelFrame(ventana_reportes, text="Generar Reporte", padx=5, pady=5, font=("Arial", 10))
    frame_reportes.pack(fill="x", padx=10, pady=10)
    
    # Combobox para seleccionar el distrito
    tk.Label(frame_reportes, text="Selecciona un distrito:").pack(anchor="w", padx=10, pady=5)
    distrito_var = tk.StringVar()
    distrito_combobox = ttk.Combobox(frame_reportes, textvariable=distrito_var, state="readonly")
    cargar_datos_combobox(distrito_combobox, "Distritos")
    distrito_combobox.pack(fill="x", padx=10, pady=5)

    # Función para generar el reporte en Excel
    def generar_reporte():
        distrito_seleccionado = distrito_var.get()
        if not distrito_seleccionado:
            messagebox.showerror("Error", "Debes seleccionar un distrito.")
            return

        # Conectar a la base de datos y obtener los movimientos del distrito seleccionado
        conexion = sqlite3.connect("insumos.db")
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT insumo, presentacion, saldo_anterior, entrada_nivel_superior, entregado,
                   no_entregado, reajuste, saldo_final
            FROM Movimientos
            WHERE distrito = ?
        """, (distrito_seleccionado,))
        movimientos = cursor.fetchall()
        conexion.close()

        if not movimientos:
            messagebox.showerror("Error", f"No hay movimientos registrados para el distrito '{distrito_seleccionado}'.")
            return

        # Crear un DataFrame con los datos
        columnas = ["Insumo", "Presentación", "Saldo Anterior", "Entrada Nivel Superior",
                    "Entregado", "No Entregado", "Reajuste", "Saldo Final"]
        df = pd.DataFrame(movimientos, columns=columnas)

        # Crear un archivo de Excel
        archivo_excel = f"Reporte_{distrito_seleccionado}.xlsx"
        with pd.ExcelWriter(archivo_excel, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=distrito_seleccionado)

            # Obtener la hoja de trabajo
            workbook = writer.book
            worksheet = writer.sheets[distrito_seleccionado]

            # Ocultar las líneas de cuadrícula
            worksheet.sheet_view.showGridLines = False

            # Aplicar formato a los encabezados
            header_font = Font(bold=True)
            thin_border = Border(
                left=Side(style="thin"),
                right=Side(style="thin"),
                top=Side(style="thin"),
                bottom=Side(style="thin")
            )
            for col_num, column_title in enumerate(df.columns, 1):
                cell = worksheet.cell(row=1, column=col_num)
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = thin_border

            # Ajustar el ancho de las columnas
            for col_num, column_title in enumerate(df.columns, 1):
                max_length = max(
                    len(str(column_title)),  # Longitud del encabezado
                    *(len(str(value)) for value in df[column_title])  # Longitud de los valores
                )
                worksheet.column_dimensions[get_column_letter(col_num)].width = max_length + 2

            # Aplicar bordes a las celdas
            for row in worksheet.iter_rows(min_row=2, max_row=worksheet.max_row,
                                           min_col=1, max_col=worksheet.max_column):
                for cell in row:
                    cell.border = thin_border

        messagebox.showinfo("Éxito", f"El reporte se ha generado correctamente: {archivo_excel}")
    
    # Botón para generar el reporte    
    tk.Button(
        frame_reportes,
        text="Generar Reporte",  # Texto del botón
        image=iconos["icono_reporte_excel"],  # Ícono
        compound="left",  # Posición del texto (a la derecha del ícono)
        font=("Arial", 12),  # Fuente del texto
        command=generar_reporte,  # Acción al hacer clic
        padx=10,  # Espaciado horizontal entre ícono y texto
        pady=5,  # Espaciado vertical
        bd=0,  # Sin bordes
        highlightthickness=0  # Sin borde de enfoque
    ).pack(pady=5)

    # Botón para cerrar la ventana
    tk.Button(
        frame_reportes,
        text="Cerrar",
        image=iconos["icono_cerrar"],
        compound="left",
        command=ventana_reportes.destroy,
        font=("Arial", 12),
        padx=10,
        pady=5,
        bd=0,
        highlightthickness=0
    ).pack(pady=10)

# Ventana principal
def ventana_principal():
    ventana = tk.Tk()
    ventana.title("Menú Principal")
    ventana.geometry("400x700")
    ventana.resizable(False, False)
    
    # Cargar los íconos como variables globales

    def cargar_icono(ruta):
        if os.path.exists(ruta):
            return PhotoImage(file=ruta)
        else:
            print(f"Advertencia: El archivo {ruta} no existe.")
            return None  # O un ícono predeterminado
    
    global iconos
    iconos = {
        "icono_ingreso_insumos": PhotoImage(file="icon_ingreso_insumos.png"),
        "icono_gestion_insumos": PhotoImage(file="icon_gestion_insumos.png"),
        "icono_gestion_servicios": PhotoImage(file="icon_gestion_servicios.png"),
        "icono_reporte": PhotoImage(file="report.png"),
        "icono_agregar": PhotoImage(file="add.png"),
        "icono_agregar_nuevo": PhotoImage(file="add_new.png"),
        "icono_modificar": PhotoImage(file="edit.png"),
        "icono_eliminar": PhotoImage(file="delete.png"),
        "icono_guardar": PhotoImage(file="save.png"),
        "icono_guardar_otro": PhotoImage(file="save_other.png"),
        "icono_agregar_otro": PhotoImage(file="add_other.png"),
        "icono_editar_otro": PhotoImage(file="edit_other.png"),
        "icono_reporte_excel": PhotoImage(file="excel.png"),
        "icono_cerrar": PhotoImage(file="exit.png"),
        "icono_subir1": PhotoImage(file="up_1.png"),
        "icono_subir2": PhotoImage(file="up_2.png")
    }

    # Título
    tk.Label(ventana, text="Menú Principal", font=("Arial", 14)).pack(pady=10)

    # Sección 1: Ingreso de Insumos
    frame_insumos = tk.LabelFrame(ventana, text="Ingreso de Insumos", padx=5, pady=5, font=("Arial", 10))
    frame_insumos.pack(fill="x", padx=10, pady=10)

    boton_insumos = tk.Button(
        frame_insumos,
        text="Ingreso de Insumos",  # Texto del botón
        image=iconos["icono_ingreso_insumos"],  # Ícono
        compound="left",  # Posición del texto (a la derecha del ícono)
        font=("Arial", 14),  # Fuente del texto
        command=abrir_ingreso_insumos,  # Acción al hacer clic
        padx=10,  # Espaciado horizontal entre ícono y texto
        pady=5,  # Espaciado vertical
        bd=0,  # Sin bordes
        highlightthickness=0  # Sin borde de enfoque
    )
    boton_insumos.pack(pady=5)

    # Sección 2: Gestión de Insumos
    frame_gestion = tk.LabelFrame(ventana, text="Gestión de Insumos", padx=5, pady=5, font=("Arial", 10))
    frame_gestion.pack(fill="x", padx=10, pady=10)

    boton_gestion = tk.Button(
        frame_gestion,
        text="Gestión de Insumos",  # Texto del botón
        image=iconos["icono_gestion_insumos"],  # Ícono
        compound="left",  # Posición del texto (a la derecha del ícono)
        font=("Arial", 14),  # Fuente del texto
        command=abrir_gestion_insumos,  # Acción al hacer clic
        padx=10,  # Espaciado horizontal entre ícono y texto
        pady=5,  # Espaciado vertical
        bd=0,  # Sin bordes
        highlightthickness=0  # Sin borde de enfoque
    )
    boton_gestion.pack(pady=5)

    # Sección 3: Gestión de Servicios
    frame_servicios = tk.LabelFrame(ventana, text="Gestión de Servicios", padx=5, pady=5, font=("Arial", 10))
    frame_servicios.pack(fill="x", padx=10, pady=10)

    boton_servicios = tk.Button(
        frame_servicios,
        text="Gestión de Servicios",  # Texto del botón
        image=iconos["icono_gestion_servicios"],  # Ícono
        compound="left",  # Posición del texto (a la derecha del ícono)
        font=("Arial", 14),  # Fuente del texto
        command=abrir_gestion_servicios,  # Acción al hacer clic
        padx=10,  # Espaciado horizontal entre ícono y texto
        pady=5,  # Espaciado vertical
        bd=0,  # Sin bordes
        highlightthickness=0  # Sin borde de enfoque
    )
    boton_servicios.pack(pady=5)
    
    # Botón para abrir la sección de reportes
    frame_reportes = tk.LabelFrame(ventana, text="Reportes de Movimientos", padx=5, pady=5, font=("Arial", 10))
    frame_reportes.pack(fill="x", padx=10, pady=10)
    
    boton_reportes = tk.Button(
        frame_reportes,
        text="Reportes de Movimientos",  # Texto del botón
        image=iconos["icono_reporte"],  # Puedes agregar un ícono si lo deseas
        compound="left",  # Posición del texto (a la derecha del ícono)
        font=("Arial", 14),  # Fuente del texto
        command=abrir_reportes,  # Acción al hacer clic
        padx=10,  # Espaciado horizontal entre ícono y texto
        pady=5,  # Espaciado vertical
        bd=0,  # Sin bordes
        highlightthickness=0  # Sin borde de enfoque
    )
    boton_reportes.pack(pady=5)

    # Ejecutar la ventana principal
    ventana.mainloop()

inicializar_base_datos()
# Ejecutar el programa
ventana_principal()