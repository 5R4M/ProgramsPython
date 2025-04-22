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
        CREATE TABLE IF NOT EXISTS Servicios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            distrito_id INTEGER NOT NULL,
            FOREIGN KEY (distrito_id) REFERENCES Distritos (id)
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

    # Obtener los datos de la tabla correspondiente en orden alfabético
    cursor.execute(f"SELECT nombre FROM {tabla} ORDER BY nombre ASC")
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

    # Función principal
    def gestionar_insumos():

        # Crear la ventana principal
        ventana = tk.Toplevel()
        ventana.title("Ingreso de Insumos")
        ventana.geometry("550x850")
        ventana.resizable(False, False)
        
        tk.Label(ventana, text="Ingreso de Insumos", font=("Arial", 14)).pack(pady=10)
        
        # Crear un marco para organizar los elementos en dos filas y dos columnas
        frame_seleccion = tk.LabelFrame(ventana, text="Información Servicios", padx=10, pady=10)
        frame_seleccion.pack(fill="x", padx=10, pady=10)
        
        frame_seleccion1 = tk.LabelFrame(ventana, text="Información Insumos", padx=10, pady=10)
        frame_seleccion1.pack(fill="x", padx=10, pady=10)

        # Variables para los combobox
        distrito_var = tk.StringVar()
        servicio_var = tk.StringVar()
        insumo_var = tk.StringVar()
        presentacion_var = tk.StringVar()
        
        # Función para cargar servicios relacionados con el distrito seleccionado
        def cargar_servicios():
            distrito_seleccionado = distrito_var.get()
            if not distrito_seleccionado:
                servicio_combobox["values"] = []
                servicio_combobox.set("Selecciona un distrito primero")
                return

            conexion = sqlite3.connect("insumos.db")
            cursor = conexion.cursor()
            cursor.execute("""
                SELECT Servicios.nombre
                FROM Servicios
                INNER JOIN Distritos ON Servicios.distrito_id = Distritos.id
                WHERE Distritos.nombre = ?
            """, (distrito_seleccionado,))
            servicios = [fila[0] for fila in cursor.fetchall()]
            conexion.close()

            servicio_combobox["values"] = servicios
            if servicios:
                servicio_combobox.set(servicios[0])
            else:
                servicio_combobox.set("No hay servicios disponibles")

        # Cargar servicios cuando se seleccione un distrito
        def on_distrito_selected(event):
            cargar_servicios()      
        
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
            columns=("Distrito", "Servicio", "Insumo", "Presentación", "Saldo Anterior",
                    "Entrada Nivel Superior", "Entregado", "No Entregado", "Reajuste", "Saldo Final"),
            show="headings",
            height=5
        )

        # Configurar las columnas del Treeview
        columnas = ["Distrito", "Servicio", "Insumo", "Presentación", "Saldo Anterior",
                    "Entrada Nivel Superior", "Entregado", "No Entregado", "Reajuste", "Saldo Final"]

        for col in columnas:
            tree.heading(col, text=col)  # Encabezado de la columna
            tree.column(col, width=150, anchor="center")  # Ancho y alineación de la columna

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
        
       # Función para agregar un movimiento al Treeview
        def agregar_movimiento():
            distrito_seleccionado = distrito_var.get()
            servicio_seleccionado = servicio_var.get()
            insumo_seleccionado = insumo_var.get()
            presentacion_seleccionada = presentacion_var.get()

            # Validaciones
            if not distrito_seleccionado:
                messagebox.showerror("Error", "Debes seleccionar un distrito.")
                return
            if not servicio_seleccionado:
                messagebox.showerror("Error", "Debes seleccionar un servicio.")
                return
            if not insumo_seleccionado:
                messagebox.showerror("Error", "Debes seleccionar un insumo.")
                return
            if not presentacion_seleccionada:
                messagebox.showerror("Error", "Debes seleccionar una presentación.")
                return

            try:
                # Obtener los valores numéricos de las entradas
                saldo_anterior = float(entradas["Saldo Anterior"].get())
                entrada_nivel_superior = float(entradas["Entrada Nivel Superior"].get())
                entregado = float(entradas["Entregado"].get())
                no_entregado = float(entradas["No Entregado"].get())
                reajuste = float(entradas["Reajuste"].get())

                # Calcular saldo final
                saldo_final = saldo_anterior + entrada_nivel_superior - entregado + reajuste

                # Agregar el movimiento al Treeview
                tree.insert("", "end", values=(distrito_seleccionado, servicio_seleccionado, insumo_seleccionado,
                                            presentacion_seleccionada, saldo_anterior, entrada_nivel_superior,
                                            entregado, no_entregado, reajuste, saldo_final))

                # Limpiar los campos de entrada
                for entrada in entradas.values():
                    entrada.delete(0, tk.END)

                messagebox.showinfo("Éxito", "El movimiento se ha agregado al listado.")
            except ValueError:
                messagebox.showerror("Error", "Todos los campos deben contener valores numéricos válidos.")
            except Exception as e:
                messagebox.showerror("Error", f"Hubo un problema al agregar el movimiento: {e}")

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
            ventana_modificar.geometry("600x550")
            ventana_modificar.resizable(False, False)

            # Variables para los combobox
            distrito_var = tk.StringVar(value=valores[0])  # Distrito actual
            servicio_var = tk.StringVar(value=valores[1])  # Servicio actual
            insumo_var = tk.StringVar(value=valores[2])    # Insumo actual
            presentacion_var = tk.StringVar(value=valores[3])  # Presentación actual

            # Obtener datos desde SQLite
            conexion = sqlite3.connect("insumos.db")
            cursor = conexion.cursor()

            # Obtener distritos
            cursor.execute("SELECT nombre FROM Distritos ORDER BY nombre ASC")
            distritos = [fila[0] for fila in cursor.fetchall()]

            # Obtener insumos
            cursor.execute("SELECT nombre FROM ListadoInsumos ORDER BY nombre ASC")
            insumos = [fila[0] for fila in cursor.fetchall()]

            # Obtener presentaciones
            cursor.execute("SELECT nombre FROM Presentaciones ORDER BY nombre ASC")
            presentaciones = [fila[0] for fila in cursor.fetchall()]

            conexion.close()

            # Función para cargar servicios relacionados con el distrito seleccionado
            def cargar_servicios():
                distrito_seleccionado = distrito_var.get()
                if not distrito_seleccionado:
                    servicio_combobox["values"] = []
                    servicio_combobox.set("Selecciona un distrito primero")
                    return

                conexion = sqlite3.connect("insumos.db")
                cursor = conexion.cursor()
                cursor.execute("""
                    SELECT Servicios.nombre
                    FROM Servicios
                    INNER JOIN Distritos ON Servicios.distrito_id = Distritos.id
                    WHERE Distritos.nombre = ?
                """, (distrito_seleccionado,))
                servicios = [fila[0] for fila in cursor.fetchall()]
                conexion.close()

                servicio_combobox["values"] = servicios
                if servicios:
                    servicio_combobox.set(servicios[0])
                else:
                    servicio_combobox.set("No hay servicios disponibles")

            # Frame para Distrito y Servicio
            frame_distrito_servicio = tk.LabelFrame(ventana_modificar, text="Distrito y Servicio", padx=10, pady=10)
            frame_distrito_servicio.pack(fill="x", padx=10, pady=10)

            # Distrito
            tk.Label(frame_distrito_servicio, text="Distrito:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
            distrito_combobox = ttk.Combobox(frame_distrito_servicio, textvariable=distrito_var, state="readonly")
            distrito_combobox["values"] = distritos
            distrito_combobox.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
            distrito_combobox.bind("<<ComboboxSelected>>", lambda event: cargar_servicios())

            # Servicio
            tk.Label(frame_distrito_servicio, text="Servicio:").grid(row=0, column=1, sticky="w", padx=5, pady=5)
            servicio_combobox = ttk.Combobox(frame_distrito_servicio, textvariable=servicio_var, state="readonly")
            cargar_servicios()  # Cargar servicios relacionados con el distrito actual
            servicio_combobox.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

            # Ajustar las columnas
            frame_distrito_servicio.columnconfigure(0, weight=1)
            frame_distrito_servicio.columnconfigure(1, weight=1)

            # Frame para Insumo y Presentación
            frame_insumo_presentacion = tk.LabelFrame(ventana_modificar, text="Insumo y Presentación", padx=10, pady=10)
            frame_insumo_presentacion.pack(fill="x", padx=10, pady=10)

            # Insumo
            tk.Label(frame_insumo_presentacion, text="Insumo:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
            insumo_combobox = ttk.Combobox(frame_insumo_presentacion, textvariable=insumo_var, state="readonly")
            insumo_combobox["values"] = insumos
            insumo_combobox.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

            # Presentación
            tk.Label(frame_insumo_presentacion, text="Presentación:").grid(row=0, column=1, sticky="w", padx=5, pady=5)
            presentacion_combobox = ttk.Combobox(frame_insumo_presentacion, textvariable=presentacion_var, state="readonly")
            presentacion_combobox["values"] = presentaciones
            presentacion_combobox.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

            # Ajustar las columnas
            frame_insumo_presentacion.columnconfigure(0, weight=1)
            frame_insumo_presentacion.columnconfigure(1, weight=1)

            # Frame para los datos de los movimientos
            frame_datos_movimientos = tk.LabelFrame(ventana_modificar, text="Datos del Movimiento", padx=10, pady=10)
            frame_datos_movimientos.pack(fill="x", padx=10, pady=10)

            # Crear entradas para los valores numéricos en dos columnas
            entradas_modificar = {}
            campos_numericos = ["Saldo Anterior", "Entrada Nivel Superior", "Entregado", "No Entregado", "Reajuste"]
            for i, campo in enumerate(campos_numericos):
                fila = i // 2  # Dividir en filas de 2 columnas
                columna = i % 2  # Calcular la columna
                tk.Label(frame_datos_movimientos, text=campo + ":").grid(row=fila, column=columna * 2, sticky="w", padx=5, pady=5)
                entrada = tk.Entry(frame_datos_movimientos)
                entrada.insert(0, valores[i + 4])  # Insertar el valor actual
                entrada.grid(row=fila, column=columna * 2 + 1, sticky="ew", padx=5, pady=5)
                entradas_modificar[campo] = entrada

            # Campo de solo lectura para "Saldo Final" en la tercera fila, segunda columna
            tk.Label(frame_datos_movimientos, text="Saldo Final:").grid(row=2, column=2, sticky="w", padx=5, pady=5)
            saldo_final_label = tk.Label(frame_datos_movimientos, text=valores[-1], relief="sunken", anchor="w")
            saldo_final_label.grid(row=2, column=3, sticky="ew", padx=5, pady=5)

            # Ajustar las columnas
            frame_datos_movimientos.columnconfigure(0, weight=1)
            frame_datos_movimientos.columnconfigure(1, weight=1)
            frame_datos_movimientos.columnconfigure(2, weight=1)
            frame_datos_movimientos.columnconfigure(3, weight=1)

            # Botón para guardar los cambios
            tk.Button(
                ventana_modificar,
                text=" Guardar Cambios",
                image=iconos["icono_editar_otro"],  # Ícono
                compound="left",
                command=lambda: guardar_cambios(tree, item, entradas_modificar, distrito_var, servicio_var, insumo_var, presentacion_var),
                bd=0,
                highlightthickness=0
            ).pack(pady=10)

            # Botón para cerrar la ventana
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

        # Función para guardar los cambios
        def guardar_cambios(tree, item, entradas_modificar, distrito_var, servicio_var, insumo_var, presentacion_var):
            nuevos_valores = [
                distrito_var.get(),
                servicio_var.get(),
                insumo_var.get(),
                presentacion_var.get(),
            ] + [entrada.get() for entrada in entradas_modificar.values()]

            # Validar que todos los campos estén completos
            if not all(nuevos_valores):
                messagebox.showerror("Error", "Todos los campos deben estar completos.")
                return

            # Actualizar el Treeview con los nuevos valores
            tree.item(item, values=nuevos_valores)
            messagebox.showinfo("Éxito", "El movimiento ha sido modificado correctamente.")
    
        # Función para eliminar un movimiento seleccionado
        def eliminar_movimiento(tree):
            seleccion = tree.selection()
            if not seleccion:
                messagebox.showerror("Error", "Debes seleccionar un movimiento para eliminar.")
                return

            confirmacion = messagebox.askyesno("Confirmación", "¿Estás seguro de que deseas eliminar este movimiento?")
            if confirmacion:
                tree.delete(seleccion[0])

        # Función para guardar los movimientos en la base de datos
        def guardar_movimientos(tree, distrito_var):
            # Obtener todos los movimientos del Treeview
            movimientos = [tree.item(item, "values") for item in tree.get_children()]

            if not movimientos:
                messagebox.showerror("Error", "No hay movimientos para guardar.")
                return

            try:
                # Conectar a la base de datos
                conexion = sqlite3.connect("insumos.db")
                cursor = conexion.cursor()

                # Insertar cada movimiento en la base de datos
                for movimiento in movimientos:
                    distrito, servicio, insumo, presentacion, saldo_anterior, entrada_nivel_superior, entregado, no_entregado, reajuste, saldo_final = movimiento

                    # Verificar si el servicio está relacionado con el distrito
                    cursor.execute("""
                        SELECT id FROM Servicios
                        WHERE nombre = ? AND distrito_id = (
                            SELECT id FROM Distritos WHERE nombre = ?
                        )
                    """, (servicio, distrito))
                    servicio_id = cursor.fetchone()

                    if not servicio_id:
                        messagebox.showerror("Error", f"El servicio '{servicio}' no está relacionado con el distrito '{distrito}'.")
                        conexion.close()
                        return

                    # Insertar el movimiento en la tabla Movimientos
                    cursor.execute("""
                        INSERT INTO Movimientos (
                            distrito, servicio, insumo, presentacion, saldo_anterior, entrada_nivel_superior,
                            entregado, no_entregado, reajuste, saldo_final
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (distrito, servicio, insumo, presentacion, saldo_anterior, entrada_nivel_superior,
                        entregado, no_entregado, reajuste, saldo_final))

                # Confirmar los cambios
                conexion.commit()
                conexion.close()

                # Limpiar el Treeview después de guardar
                tree.delete(*tree.get_children())

                messagebox.showinfo("Éxito", "Todos los movimientos se han guardado correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"Hubo un problema al guardar los movimientos: {e}")
        
        # Crear los elementos en dos filas y dos columnas
        # Fila 1, Columna 1: Distrito
        tk.Label(frame_seleccion, text="Distrito:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        distrito_combobox = ttk.Combobox(frame_seleccion, textvariable=distrito_var, state="readonly")
        cargar_datos_combobox(distrito_combobox, "Distritos")
        distrito_combobox.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        distrito_combobox.bind("<<ComboboxSelected>>", on_distrito_selected)

        # Fila 1, Columna 2: Servicio
        tk.Label(frame_seleccion, text="Servicio:").grid(row=0, column=1, sticky="w", padx=5, pady=5)
        servicio_combobox = ttk.Combobox(frame_seleccion, textvariable=servicio_var, state="readonly")
        servicio_combobox.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        # Fila 2, Columna 1: Insumo
        tk.Label(frame_seleccion1, text="Insumo:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        insumo_combobox = ttk.Combobox(frame_seleccion1, textvariable=insumo_var, state="readonly")
        cargar_datos_combobox(insumo_combobox, "ListadoInsumos")
        insumo_combobox.grid(row=3, column=0, sticky="ew", padx=5, pady=5)

        # Botón para agregar un nuevo insumo (debajo del combobox de insumo)
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
                text=" Guardar Insumo",
                image=iconos["icono_guardar_otro"],
                compound="left",
                command=agregar_insumo,
                bd=0,
                highlightthickness=0
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
            frame_seleccion1,
            text=" Agregar Insumo",
            image=iconos["icono_agregar_nuevo"],
            compound="left",
            command=abrir_ventana_agregar_insumo,
            bd=0,
            highlightthickness=0
        ).grid(row=4, column=0, sticky="ew", padx=5, pady=5)

        # Fila 2, Columna 2: Presentación
        tk.Label(frame_seleccion1, text="Presentación:").grid(row=2, column=1, sticky="w", padx=5, pady=5)
        presentacion_combobox = ttk.Combobox(frame_seleccion1, textvariable=presentacion_var, state="readonly")
        cargar_datos_combobox(presentacion_combobox, "Presentaciones")
        presentacion_combobox.grid(row=3, column=1, sticky="ew", padx=5, pady=5)

        # Botón para agregar una nueva presentación (debajo del combobox de presentación)
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
                text=" Guardar Presentación",
                image=iconos["icono_guardar_otro"],
                compound="left",
                command=agregar_presentacion,
                bd=0,
                highlightthickness=0
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

        tk.Button(
            frame_seleccion1,
            text=" Agregar Presentación",
            image=iconos["icono_agregar_otro"],
            compound="left",
            command=abrir_ventana_agregar_presentacion,
            bd=0,
            highlightthickness=0
        ).grid(row=4, column=1, sticky="ew", padx=5, pady=5)

        # Ajustar las columnas para que se expandan uniformemente
        frame_seleccion.columnconfigure(0, weight=1)
        frame_seleccion.columnconfigure(1, weight=1)
        
        frame_seleccion1.columnconfigure(0, weight=1)
        frame_seleccion1.columnconfigure(1, weight=1)

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

    frame_gestion_servicios = tk.LabelFrame(ventana_gestion_servicios, text="Gestión de Servicios", padx=5, pady=5, font=("Arial", 10))
    frame_gestion_servicios.pack(fill="x", padx=10, pady=10)

    # Función para cargar servicios desde un archivo de Excel
    def cargar_servicios_desde_excel():
        archivo = filedialog.askopenfilename(
            title="Seleccionar archivo de Excel",
            filetypes=[("Archivos de Excel", "*.xlsx *.xls")]
        )
        if not archivo:
            return  # Si no se selecciona un archivo, salir de la función

        try:
            # Leer el archivo de Excel
            df = pd.read_excel(archivo)

            # Conectar a la base de datos
            conexion = sqlite3.connect("insumos.db")
            cursor = conexion.cursor()

            # Procesar cada columna del archivo
            for distrito, servicios in df.items():
                distrito = str(distrito).strip()  # Limpiar el nombre del distrito
                if not distrito:
                    continue  # Saltar columnas sin encabezado válido

                # Verificar si el distrito ya existe en la base de datos
                cursor.execute("SELECT id FROM Distritos WHERE nombre = ?", (distrito,))
                resultado = cursor.fetchone()
                if resultado:
                    distrito_id = resultado[0]
                else:
                    # Insertar el distrito si no existe
                    cursor.execute("INSERT INTO Distritos (nombre) VALUES (?)", (distrito,))
                    distrito_id = cursor.lastrowid

                # Insertar los servicios relacionados con el distrito
                for servicio in servicios.dropna():  # Ignorar valores nulos
                    servicio = str(servicio).strip()  # Limpiar el nombre del servicio
                    if servicio:  # Verificar que no esté vacío
                        cursor.execute("""
                            SELECT COUNT(*) FROM Servicios
                            WHERE nombre = ? AND distrito_id = ?
                        """, (servicio, distrito_id))
                        if cursor.fetchone()[0] == 0:  # Si no existe, insertarlo
                            cursor.execute("""
                                INSERT INTO Servicios (nombre, distrito_id)
                                VALUES (?, ?)
                            """, (servicio, distrito_id))

            # Ordenar los distritos alfabéticamente en la base de datos
            cursor.execute("SELECT nombre FROM Distritos ORDER BY nombre ASC")
            distritos_ordenados = [fila[0] for fila in cursor.fetchall()]

            conexion.commit()
            conexion.close()

            messagebox.showinfo("Éxito", "Los servicios se han cargado correctamente desde el archivo.")
            print("Distritos ordenados alfabéticamente:", distritos_ordenados)  # Opcional: para depuración
        except Exception as e:
            messagebox.showerror("Error", f"Hubo un problema al cargar el archivo: {e}")

    # Botón para cargar servicios desde un archivo de Excel
    tk.Button(
        frame_gestion_servicios,
        text="Cargar Servicios desde Excel",  # Texto del botón
        image=iconos["icono_subir2"],  # Ícono
        compound="left",  # Posición del texto (a la derecha del ícono)
        font=("Arial", 12),  # Fuente del texto
        command=cargar_servicios_desde_excel,  # Acción al hacer clic
        padx=10,  # Espaciado horizontal entre ícono y texto
        pady=5,  # Espaciado vertical
        bd=0,  # Sin bordes
        highlightthickness=0  # Sin borde de enfoque
    ).pack(pady=5)

    # Botón para cerrar la ventana
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

# Función para abrir la ventana de "Reportes"
def abrir_reportes():
    ventana_reportes = tk.Toplevel()
    ventana_reportes.title("Reportes")
    ventana_reportes.geometry("400x400")
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

    # Combobox para seleccionar el servicio
    tk.Label(frame_reportes, text="Selecciona un servicio (opcional):").pack(anchor="w", padx=10, pady=5)
    servicio_var = tk.StringVar()
    servicio_combobox = ttk.Combobox(frame_reportes, textvariable=servicio_var, state="readonly")
    servicio_combobox.pack(fill="x", padx=10, pady=5)

    # Función para cargar servicios relacionados con el distrito seleccionado
    def cargar_servicios():
        distrito_seleccionado = distrito_var.get()
        if not distrito_seleccionado:
            servicio_combobox["values"] = []
            servicio_combobox.set("Selecciona un distrito primero")
            return

        conexion = sqlite3.connect("insumos.db")
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT Servicios.nombre
            FROM Servicios
            INNER JOIN Distritos ON Servicios.distrito_id = Distritos.id
            WHERE Distritos.nombre = ?
        """, (distrito_seleccionado,))
        servicios = [fila[0] for fila in cursor.fetchall()]
        conexion.close()

        servicio_combobox["values"] = servicios
        if servicios:
            servicio_combobox.set(servicios[0])
        else:
            servicio_combobox.set("No hay servicios disponibles")

    # Cargar servicios cuando se seleccione un distrito
    distrito_combobox.bind("<<ComboboxSelected>>", lambda event: cargar_servicios())

   # Función para abrir la ventana de "Reportes"
def abrir_reportes():
    ventana_reportes = tk.Toplevel()
    ventana_reportes.title("Reportes")
    ventana_reportes.geometry("400x400")
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

    # Combobox para seleccionar el servicio
    tk.Label(frame_reportes, text="Selecciona un servicio (opcional):").pack(anchor="w", padx=10, pady=5)
    servicio_var = tk.StringVar()
    servicio_combobox = ttk.Combobox(frame_reportes, textvariable=servicio_var, state="readonly")
    servicio_combobox.pack(fill="x", padx=10, pady=5)

    # Función para cargar servicios relacionados con el distrito seleccionado
    def cargar_servicios():
        distrito_seleccionado = distrito_var.get()
        if not distrito_seleccionado:
            servicio_combobox["values"] = []
            servicio_combobox.set("")  # Limpiar selección del combobox de servicios
            return

        conexion = sqlite3.connect("insumos.db")
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT Servicios.nombre
            FROM Servicios
            INNER JOIN Distritos ON Servicios.distrito_id = Distritos.id
            WHERE Distritos.nombre = ?
        """, (distrito_seleccionado,))
        servicios = [fila[0] for fila in cursor.fetchall()]
        conexion.close()

        servicio_combobox["values"] = servicios
        servicio_combobox.set("")  # No seleccionar automáticamente ningún servicio

    # Cargar servicios cuando se seleccione un distrito
    distrito_combobox.bind("<<ComboboxSelected>>", lambda event: cargar_servicios())

    # Función para generar el reporte en Excel
    def generar_reporte():
        distrito_seleccionado = distrito_var.get()
        servicio_seleccionado = servicio_var.get()

        if not distrito_seleccionado:
            messagebox.showerror("Error", "Debes seleccionar un distrito.")
            return

        # Conectar a la base de datos y obtener los movimientos
        conexion = sqlite3.connect("insumos.db")
        cursor = conexion.cursor()

        if servicio_seleccionado:
            # Obtener los datos del distrito y servicio seleccionados
            cursor.execute("""
                SELECT insumo, presentacion, saldo_anterior, entrada_nivel_superior, entregado,
                    no_entregado, reajuste, saldo_final
                FROM Movimientos
                WHERE distrito = ? AND servicio = ?
            """, (distrito_seleccionado, servicio_seleccionado))
            movimientos = cursor.fetchall()
            nombre_pestana = f"{distrito_seleccionado[:3]}_{servicio_seleccionado[:6]}"
            # Nombre del archivo para un reporte específico
            archivo_excel = f"Reporte_{distrito_seleccionado}_{servicio_seleccionado}.xlsx"
        else:
            # Obtener los datos del distrito seleccionado (consolidado de todos los servicios)
            cursor.execute("""
                SELECT insumo, presentacion, saldo_anterior, entrada_nivel_superior, entregado,
                    no_entregado, reajuste, saldo_final
                FROM Movimientos
                WHERE distrito = ?
            """, (distrito_seleccionado,))
            movimientos = cursor.fetchall()
            nombre_pestana = f"{distrito_seleccionado[:3]}_Consolidado"
            # Nombre del archivo para un reporte consolidado
            archivo_excel = f"Reporte_{distrito_seleccionado}_Consolidado.xlsx"

        conexion.close()

        if not movimientos:
            messagebox.showerror("Error", f"No hay movimientos registrados para el distrito '{distrito_seleccionado}' y servicio '{servicio_seleccionado}'.")
            return

        # Crear un DataFrame con los datos
        columnas = ["Insumo", "Presentación", "Saldo Anterior", "Entrada Nivel Superior",
                    "Entregado", "No Entregado", "Reajuste", "Saldo Final"]
        df = pd.DataFrame(movimientos, columns=columnas)

        # Crear un archivo de Excel
        with pd.ExcelWriter(archivo_excel, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=nombre_pestana)

            # Obtener la hoja de trabajo
            workbook = writer.book
            worksheet = writer.sheets[nombre_pestana]

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

# Ejecutar la función para limpiar la base de datos
inicializar_base_datos()

# Ejecutar el programa
ventana_principal()