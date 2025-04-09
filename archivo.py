import pandas as pd
from tkinter import Tk, filedialog

def seleccionar_archivo():
    """Abre un cuadro de diálogo para seleccionar un archivo."""
    Tk().withdraw()  # Oculta la ventana principal de Tkinter
    archivo = filedialog.askopenfilename(
        title="Seleccionar archivo de Excel",
        filetypes=[("Archivos de Excel", "*.xlsx *.xls")]
    )
    return archivo

def extraer_datos():
    print("Selecciona el primer archivo de Excel (archivo base):")
    archivo1 = seleccionar_archivo()
    print("Selecciona el segundo archivo de Excel (archivo de comparación):")
    archivo2 = seleccionar_archivo()

    # Cargar los archivos de Excel
    df1 = pd.read_excel(archivo1)
    df2 = pd.read_excel(archivo2)

    print("\nColumnas del primer archivo:")
    print(df1.columns)
    columna_base = input("Escribe el nombre de la columna del primer archivo para comparar: ")

    print("\nColumnas del segundo archivo:")
    print(df2.columns)
    columna_comparar = input("Escribe el nombre de la columna del segundo archivo para comparar: ")

    # Validar que las columnas existen
    if columna_base not in df1.columns or columna_comparar not in df2.columns:
        print("Error: Una o ambas columnas no existen en los archivos seleccionados.")
        return

    # Filtrar los datos que coinciden
    valores_a_comparar = df1[columna_base].unique()
    datos_filtrados = df2[df2[columna_comparar].isin(valores_a_comparar)]

    # Guardar los datos filtrados en un nuevo archivo de Excel
    archivo_salida = filedialog.asksaveasfilename(
        title="Guardar archivo de resultados",
        defaultextension=".xlsx",
        filetypes=[("Archivos de Excel", "*.xlsx")]
    )
    if archivo_salida:
        datos_filtrados.to_excel(archivo_salida, index=False)
        print(f"Archivo guardado exitosamente en: {archivo_salida}")
    else:
        print("No se guardó el archivo.")

if __name__ == "__main__":
    extraer_datos()