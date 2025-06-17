import sqlite3
import pandas as pd
import json
import os
from datetime import datetime
from tkinter import messagebox, filedialog
import tkinter as tk
from tkinter import ttk

class ImportarExportarManager:
    """Clase para manejar importación y exportación de datos de la base de datos"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        
        # Definir las tablas y su orden de dependencias
        self.tablas_orden = [
            'area',
            'distrito', 
            'tipo_servicio',
            'servicio',
            'tipo_insumo',
            'presentacion',
            'insumo',
            'insumo_presentacion',
            'tipo_movimiento',
            'movimiento',
            'usuarios'
        ]
        
        # Mapeo de tablas con sus columnas principales
        self.estructura_tablas = {
            'area': ['id', 'nombre'],
            'distrito': ['id', 'nombre', 'id_area'],
            'tipo_servicio': ['id', 'id_distrito', 'descripcion'],
            'servicio': ['id', 'id_tipo_servicio', 'nombre'],
            'tipo_insumo': ['id', 'descripcion'],
            'presentacion': ['id', 'nombre'],
            'insumo': ['id', 'nombre', 'lote', 'fecha_vencimiento', 'id_tipo_insumo'],
            'insumo_presentacion': ['insumo_id', 'presentacion_id'],
            'tipo_movimiento': ['id', 'descripcion'],
            'movimiento': ['id', 'fecha_registro', 'referencia', 'tipo_movimiento_id', 
                          'area_id', 'distrito_id', 'servicio_id', 'insumo_id', 
                          'presentacion_id', 'lote', 'fecha_vencimiento', 'cantidad', 
                          'observaciones', 'salida_distrito_id', 'salida_servicio_id'],
            'usuarios': ['id', 'username', 'password', 'nombre_completo', 'rol', 
                        'activo', 'fecha_creacion']
        }

    def exportar_datos_completos(self, ruta_archivo=None):
        """Exporta todos los datos de la base de datos a un archivo JSON"""
        try:
            if not ruta_archivo:
                nombre_archivo = f"backup_completo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                ruta_archivo = filedialog.asksaveasfilename(
                    title="Guardar exportación completa",
                    defaultextension=".json",
                    filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")],
                    initialfile=nombre_archivo
                )
                
            if not ruta_archivo:
                return False
                
            conn = sqlite3.connect(self.db_path)
            datos_exportacion = {
                'metadata': {
                    'fecha_exportacion': datetime.now().isoformat(),
                    'version': '1.0',
                    'tipo': 'backup_completo'
                },
                'datos': {}
            }
            
            total_registros = 0
            
            # Exportar cada tabla en orden
            for tabla in self.tablas_orden:
                try:
                    # Verificar si la tabla existe
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tabla,))
                    if not cursor.fetchone():
                        print(f"Tabla {tabla} no existe, omitiendo...")
                        datos_exportacion['datos'][tabla] = []
                        continue
                    
                    # Usar cursor en lugar de pandas para mejor compatibilidad
                    cursor.execute(f"SELECT * FROM {tabla}")
                    columnas = [desc[0] for desc in cursor.description]
                    filas = cursor.fetchall()
                    
                    # Convertir a lista de diccionarios
                    registros = []
                    for fila in filas:
                        registro = {}
                        for i, valor in enumerate(fila):
                            registro[columnas[i]] = valor
                        registros.append(registro)
                    
                    datos_exportacion['datos'][tabla] = registros
                    total_registros += len(registros)
                    print(f"Exportada tabla {tabla}: {len(registros)} registros")
                    
                except Exception as e:
                    print(f"Error exportando tabla {tabla}: {e}")
                    datos_exportacion['datos'][tabla] = []
            
            conn.close()
            
            # Guardar archivo JSON
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                json.dump(datos_exportacion, f, indent=2, ensure_ascii=False, default=str)
            
            messagebox.showinfo("Exportación Exitosa", 
                f"Datos exportados correctamente:\n\n"
                f"📁 Archivo: {os.path.basename(ruta_archivo)}\n"
                f"📊 Total de registros: {total_registros}\n"
                f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            return True
            
        except Exception as e:
            messagebox.showerror("Error de Exportación", 
                f"Error al exportar datos:\n\n{str(e)}")
            return False

    def importar_datos_completos(self, ruta_archivo=None, limpiar_antes=False):
        """Importa datos desde un archivo JSON"""
        try:
            if not ruta_archivo:
                ruta_archivo = filedialog.askopenfilename(
                    title="Seleccionar archivo de importación",
                    filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
                )
                
            if not ruta_archivo:
                return False
                
            # Leer archivo JSON
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                datos_importacion = json.load(f)
            
            if 'datos' not in datos_importacion:
                messagebox.showerror("Error", "Formato de archivo inválido")
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Deshabilitar foreign keys temporalmente
            cursor.execute("PRAGMA foreign_keys = OFF")
            
            try:
                # Limpiar datos existentes si se solicita
                if limpiar_antes:
                    if messagebox.askyesno("⚠️ Confirmación Crítica", 
                        "¿Está COMPLETAMENTE SEGURO de eliminar todos los datos existentes?\n\n"
                        "⚠️ ESTA ACCIÓN NO SE PUEDE DESHACER ⚠️\n\n"
                        "Se perderán TODOS los datos actuales del sistema.\n"
                        "Asegúrese de tener un respaldo antes de continuar."):
                        
                        # Eliminar en orden inverso para respetar foreign keys
                        for tabla in reversed(self.tablas_orden):
                            try:
                                cursor.execute(f"DELETE FROM {tabla}")
                                print(f"Limpiada tabla {tabla}")
                            except:
                                pass  # Tabla puede no existir
                    else:
                        return False
                
                # Importar datos en orden correcto
                registros_importados = 0
                errores = []
                
                for tabla in self.tablas_orden:
                    if tabla in datos_importacion['datos']:
                        registros = datos_importacion['datos'][tabla]
                        
                        if registros:
                            try:
                                # Obtener columnas de la primera fila
                                columnas = list(registros[0].keys())
                                placeholders = ', '.join(['?' for _ in columnas])
                                columnas_str = ', '.join(columnas)
                                
                                # Preparar query de inserción
                                if limpiar_antes:
                                    query = f"INSERT INTO {tabla} ({columnas_str}) VALUES ({placeholders})"
                                else:
                                    query = f"INSERT OR REPLACE INTO {tabla} ({columnas_str}) VALUES ({placeholders})"
                                
                                # Insertar registros
                                for registro in registros:
                                    valores = [registro.get(col) for col in columnas]
                                    cursor.execute(query, valores)
                                    registros_importados += 1
                                
                                print(f"Importada tabla {tabla}: {len(registros)} registros")
                            except Exception as e:
                                errores.append(f"Error en tabla {tabla}: {str(e)}")
                
                # Rehabilitar foreign keys
                cursor.execute("PRAGMA foreign_keys = ON")
                conn.commit()
                
                mensaje = f"✅ Importación Completada\n\n"
                mensaje += f"📊 Registros importados: {registros_importados}\n"
                mensaje += f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
                
                if errores:
                    mensaje += f"\n\n⚠️ Errores encontrados: {len(errores)}"
                    if len(errores) <= 3:
                        mensaje += "\n" + "\n".join(errores[:3])
                    else:
                        mensaje += "\n" + "\n".join(errores[:3]) + f"\n... y {len(errores)-3} errores más"
                
                if errores:
                    messagebox.showwarning("Importación con Advertencias", mensaje)
                else:
                    messagebox.showinfo("Importación Exitosa", mensaje)
                
                return True
                
            except Exception as e:
                conn.rollback()
                raise e
                
        except Exception as e:
            messagebox.showerror("Error de Importación", 
                f"Error al importar datos:\n\n{str(e)}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()

    def exportar_tabla_excel(self, tabla, ruta_archivo=None):
        """Exporta una tabla específica a Excel"""
        try:
            if tabla not in self.tablas_orden:
                messagebox.showerror("Error", f"Tabla '{tabla}' no válida")
                return False
                
            if not ruta_archivo:
                nombre_archivo = f"{tabla}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                ruta_archivo = filedialog.asksaveasfilename(
                    title=f"Exportar tabla {tabla}",
                    defaultextension=".xlsx",
                    filetypes=[("Archivos Excel", "*.xlsx"), ("Todos los archivos", "*.*")],
                    initialfile=nombre_archivo
                )
                
            if not ruta_archivo:
                return False
                
            conn = sqlite3.connect(self.db_path)
            
            # Obtener datos con información relacionada si es posible
            if tabla == 'movimiento':
                query = """
                SELECT 
                    m.*,
                    a.nombre as area_nombre,
                    d.nombre as distrito_nombre,
                    s.nombre as servicio_nombre,
                    i.nombre as insumo_nombre,
                    p.nombre as presentacion_nombre,
                    tm.descripcion as tipo_movimiento_desc
                FROM movimiento m
                LEFT JOIN area a ON m.area_id = a.id
                LEFT JOIN distrito d ON m.distrito_id = d.id
                LEFT JOIN servicio s ON m.servicio_id = s.id
                LEFT JOIN insumo i ON m.insumo_id = i.id
                LEFT JOIN presentacion p ON m.presentacion_id = p.id
                LEFT JOIN tipo_movimiento tm ON m.tipo_movimiento_id = tm.id
                """
            else:
                query = f"SELECT * FROM {tabla}"
                
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            # Exportar a Excel
            with pd.ExcelWriter(ruta_archivo, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name=tabla, index=False)
                
                # Formatear el Excel
                workbook = writer.book
                worksheet = writer.sheets[tabla]
                
                # Formato para encabezados
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#4472C4',
                    'font_color': 'white',
                    'border': 1
                })
                
                # Aplicar formato a encabezados
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Ajustar ancho de columnas
                for i, col in enumerate(df.columns):
                    max_len = max(
                        df[col].astype(str).map(len).max(),
                        len(str(col))
                    ) + 2
                    worksheet.set_column(i, i, min(max_len, 50))
            
            messagebox.showinfo("Exportación Exitosa", 
                f"✅ Tabla exportada correctamente\n\n"
                f"📁 Tabla: {tabla}\n"
                f"📊 Registros: {len(df)}\n"
                f"💾 Archivo: {os.path.basename(ruta_archivo)}")
            return True
            
        except Exception as e:
            messagebox.showerror("Error de Exportación", 
                f"Error al exportar tabla:\n\n{str(e)}")
            return False

    def importar_tabla_excel(self, tabla, ruta_archivo=None):
        """Importa datos de Excel a una tabla específica"""
        try:
            if tabla not in self.tablas_orden:
                messagebox.showerror("Error", f"Tabla '{tabla}' no válida")
                return False
                
            if not ruta_archivo:
                ruta_archivo = filedialog.askopenfilename(
                    title=f"Importar datos para tabla {tabla}",
                    filetypes=[("Archivos Excel", "*.xlsx"), ("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
                )
                
            if not ruta_archivo:
                return False
            
            # Leer archivo
            if ruta_archivo.endswith('.csv'):
                df = pd.read_csv(ruta_archivo)
            else:
                df = pd.read_excel(ruta_archivo)
            
            if df.empty:
                messagebox.showwarning("Advertencia", "El archivo está vacío")
                return False
            
            # Validar columnas requeridas
            columnas_requeridas = self.estructura_tablas.get(tabla, [])
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns and col != 'id']
            
            if columnas_faltantes:
                messagebox.showerror("Error de Validación", 
                    f"Faltan columnas requeridas:\n\n{', '.join(columnas_faltantes)}")
                return False
            
            # Confirmar importación
            if not messagebox.askyesno("Confirmar Importación", 
                f"¿Desea importar {len(df)} registros a la tabla '{tabla}'?\n\n"
                "Los registros existentes con el mismo ID serán reemplazados."):
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                registros_importados = 0
                errores = []
                
                for index, row in df.iterrows():
                    try:
                        # Preparar datos para inserción
                        columnas = [col for col in df.columns if col in columnas_requeridas]
                        valores = [row[col] if pd.notna(row[col]) else None for col in columnas]
                        
                        placeholders = ', '.join(['?' for _ in columnas])
                        columnas_str = ', '.join(columnas)
                        
                        query = f"INSERT OR REPLACE INTO {tabla} ({columnas_str}) VALUES ({placeholders})"
                        cursor.execute(query, valores)
                        registros_importados += 1
                        
                    except Exception as e:
                        errores.append(f"Fila {index + 2}: {str(e)}")
                
                conn.commit()
                
                mensaje = f"✅ Importación Completada\n\n"
                mensaje += f"📊 Registros importados: {registros_importados}\n"
                mensaje += f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
                
                if errores:
                    mensaje += f"\n\n⚠️ Errores: {len(errores)}"
                    if len(errores) <= 5:
                        mensaje += "\n" + "\n".join(errores[:5])
                    else:
                        mensaje += "\n" + "\n".join(errores[:5]) + f"\n... y {len(errores)-5} errores más"
                
                if errores:
                    messagebox.showwarning("Importación con Advertencias", mensaje)
                else:
                    messagebox.showinfo("Importación Exitosa", mensaje)
                
                return True
                
            except Exception as e:
                conn.rollback()
                raise e
                
        except Exception as e:
            messagebox.showerror("Error de Importación", 
                f"Error al importar tabla:\n\n{str(e)}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()

    def crear_ventana_gestion(self, parent=None):
        """Crea una ventana para gestionar importación/exportación con diseño profesional"""
        ventana = tk.Toplevel(parent) if parent else tk.Tk()
        ventana.title("Gestión de Importación y Exportación de Datos")
        ventana.geometry("800x700")
        ventana.resizable(True, True)
        
        # Configurar icono y estilo
        ventana.configure(bg='#f0f0f0')
        
        # Centrar ventana
        ventana.update_idletasks()
        x = (ventana.winfo_screenwidth() - 800) // 2
        y = (ventana.winfo_screenheight() - 700) // 2
        ventana.geometry(f"800x700+{x}+{y}")
        
        # Crear notebook para pestañas
        notebook = ttk.Notebook(ventana)
        notebook.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Configurar estilos
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'))
        style.configure('Subtitle.TLabel', font=('Segoe UI', 12, 'bold'))
        style.configure('Info.TLabel', font=('Segoe UI', 10))
        style.configure('Action.TButton', font=('Segoe UI', 10), padding=(20, 10))
        
        # PESTAÑA 1: BACKUP COMPLETO
        frame_backup = ttk.Frame(notebook)
        notebook.add(frame_backup, text="🗄️ Backup Completo")
        
        # Título principal
        title_frame = ttk.Frame(frame_backup)
        title_frame.pack(fill='x', padx=20, pady=20)
        
        ttk.Label(title_frame, text="Gestión de Backup Completo", 
                 style='Title.TLabel').pack()
        
        ttk.Label(title_frame, text="Exportar e importar todos los datos del sistema", 
                 style='Info.TLabel').pack(pady=(5,0))
        
        # Sección de exportación
        export_frame = ttk.LabelFrame(frame_backup, text="📤 Exportación", padding=20)
        export_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(export_frame, text="Crear un archivo de respaldo con todos los datos del sistema", 
                 style='Info.TLabel').pack(anchor='w', pady=(0,10))
        
        ttk.Button(export_frame, text="🗄️ Exportar Backup Completo", 
                  style='Action.TButton',
                  command=self.exportar_datos_completos).pack(anchor='w')
        
        # Sección de importación
        import_frame = ttk.LabelFrame(frame_backup, text="📥 Importación", padding=20)
        import_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(import_frame, text="Restaurar datos desde un archivo de respaldo", 
                 style='Info.TLabel').pack(anchor='w', pady=(0,10))
        
        button_frame = ttk.Frame(import_frame)
        button_frame.pack(fill='x')
        
        ttk.Button(button_frame, text="📥 Importar (Mantener Datos)", 
                  style='Action.TButton',
                  command=lambda: self.importar_datos_completos(limpiar_antes=False)).pack(side='left', padx=(0,10))
        
        ttk.Button(button_frame, text="⚠️ Importar (Reemplazar Todo)", 
                  style='Action.TButton',
                  command=lambda: self.importar_datos_completos(limpiar_antes=True)).pack(side='left')
        
        # Información de seguridad
        warning_frame = ttk.LabelFrame(frame_backup, text="⚠️ Información Importante", padding=20)
        warning_frame.pack(fill='x', padx=20, pady=10)
        
        warning_text = """• Mantener Datos: Agrega/actualiza registros sin eliminar datos existentes
• Reemplazar Todo: ELIMINA todos los datos actuales antes de importar
• Siempre haga un backup antes de importar datos importantes
• Los archivos de backup incluyen información sensible (usuarios y contraseñas)"""
        
        ttk.Label(warning_frame, text=warning_text, 
                 style='Info.TLabel', justify='left').pack(anchor='w')
        
        # PESTAÑA 2: TABLAS INDIVIDUALES
        frame_tablas = ttk.Frame(notebook)
        notebook.add(frame_tablas, text="📊 Tablas Individuales")
        
        # Título
        title_frame2 = ttk.Frame(frame_tablas)
        title_frame2.pack(fill='x', padx=20, pady=20)
        
        ttk.Label(title_frame2, text="Gestión de Tablas Individuales", 
                 style='Title.TLabel').pack()
        
        ttk.Label(title_frame2, text="Exportar e importar datos de tablas específicas", 
                 style='Info.TLabel').pack(pady=(5,0))
        
        # Selección de tabla
        selection_frame = ttk.LabelFrame(frame_tablas, text="🎯 Selección de Tabla", padding=20)
        selection_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(selection_frame, text="Seleccionar tabla:", 
                 style='Info.TLabel').pack(anchor='w', pady=(0,5))
        
        self.combo_tabla = ttk.Combobox(selection_frame, values=self.tablas_orden, 
                                       state="readonly", font=('Segoe UI', 10))
        self.combo_tabla.pack(fill='x', pady=(0,10))
        self.combo_tabla.set(self.tablas_orden[0])
        
        # Botones de acción
        action_frame = ttk.Frame(selection_frame)
        action_frame.pack(fill='x')
        
        ttk.Button(action_frame, text="📤 Exportar a Excel", 
                  style='Action.TButton',
                  command=self.exportar_tabla_seleccionada).pack(side='left', padx=(0,10))
        
        ttk.Button(action_frame, text="📥 Importar desde Excel/CSV", 
                  style='Action.TButton',
                  command=self.importar_tabla_seleccionada).pack(side='left')
        
        # Información de tablas
        info_tablas_frame = ttk.LabelFrame(frame_tablas, text="ℹ️ Información de Tablas", padding=20)
        info_tablas_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        info_tablas_text = """Descripción de las principales tablas:

• area: Áreas geográficas del sistema
• distrito: Distritos organizados por área
• tipo_servicio: Tipos de servicios médicos
• servicio: Servicios específicos por tipo
• tipo_insumo: Categorías de insumos médicos
• presentacion: Formas de presentación de insumos
• insumo: Insumos médicos registrados
• movimiento: Registro de todos los movimientos de insumos
• usuarios: Usuarios del sistema (requiere permisos especiales)

Formatos soportados: Excel (.xlsx) y CSV (.csv)
La exportación incluye información relacionada cuando es posible."""
        
        ttk.Label(info_tablas_frame, text=info_tablas_text, 
                 style='Info.TLabel', justify='left').pack(anchor='nw', fill='both', expand=True)
        
        return ventana
    
    def exportar_tabla_seleccionada(self):
        """Exporta la tabla seleccionada en el combobox"""
        tabla = self.combo_tabla.get()
        if tabla:
            self.exportar_tabla_excel(tabla)
    
    def importar_tabla_seleccionada(self):
        """Importa datos a la tabla seleccionada en el combobox"""
        tabla = self.combo_tabla.get()
        if tabla:
            self.importar_tabla_excel(tabla)

# Función para integrar con el sistema principal
def crear_gestor_importar_exportar(db_path, parent=None):
    """Función helper para crear el gestor desde el sistema principal"""
    gestor = ImportarExportarManager(db_path)
    return gestor.crear_ventana_gestion(parent)

# Ejemplo de uso
if __name__ == "__main__":
    # Para pruebas independientes
    try:
        from src.database import DB_PATH
    except:
        DB_PATH = "test.db"
    
    root = tk.Tk()
    root.withdraw()  # Ocultar ventana principal
    
    gestor = ImportarExportarManager(DB_PATH)
    ventana = gestor.crear_ventana_gestion()
    
    root.mainloop()