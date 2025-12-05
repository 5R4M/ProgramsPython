import customtkinter as ctk
from tkinter import messagebox
import os
from PIL import Image, ImageTk
import fitz  # PyMuPDF
import tempfile
from docx2pdf import convert
from config import COLOR_SUCCESS,COLOR_PRIMARY,DOCUMENTOS_DIR
from models import Persona
from ui.crear_documento import VentanaCrearDocumento

class VentanaBuscarDocumento:
    def __init__(self, parent, db, es_integrado=False):
        self.db = db
        self.es_integrado = es_integrado
        self.callback_actualizar = None
        self.persona_seleccionada = None
        
        self.todos_documentos = []      
        self.resultados_busqueda = []   
        
        if es_integrado:
            # Crear como Frame integrado
            self.ventana = ctk.CTkFrame(parent)
            self.ventana.pack(fill="both", expand=True)
        else:
            # Crear como ventana separada (Toplevel)
            self.ventana = ctk.CTkToplevel(parent)
            self.ventana.title("🔍 Buscar Documento")
            self.ventana.after(100, self.maximizar_ventana)
        
        self.crear_interfaz()
        
        # ✅ AGREGAR ESTA LÍNEA:
        self.cargar_todos_documentos_iniciales()
    
    def set_callback_actualizar(self, callback):
        """Permite establecer un callback para actualizar estadísticas"""
        self.callback_actualizar = callback
    
    def maximizar_ventana(self):
        """Maximiza la ventana"""
        if not self.es_integrado:
            self.ventana.state('zoomed')
    
    def center_window(self):
        """Centra la ventana en la pantalla"""
        if not self.es_integrado:
            self.ventana.geometry("1400x900")
            self.ventana.update_idletasks()
            width = self.ventana.winfo_width()
            height = self.ventana.winfo_height()
            x = (self.ventana.winfo_screenwidth() // 2) - (width // 2)
            y = (self.ventana.winfo_screenheight() // 2) - (height // 2)
            self.ventana.geometry(f'{width}x{height}+{x}+{y}')
    
    def crear_interfaz(self):
        """Crea la interfaz de búsqueda"""
        
        # Frame principal con dos columnas
        container = ctk.CTkFrame(self.ventana)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        container.grid_columnconfigure(0, weight=3) 
        container.grid_columnconfigure(1, weight=2)
        container.grid_rowconfigure(1, weight=1)
        
        # ===== PANEL IZQUIERDO: Búsqueda y resultados =====
        panel_izquierdo = ctk.CTkFrame(container)
        panel_izquierdo.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Título
        ctk.CTkLabel(
            panel_izquierdo,
            text="🔍 Buscar Documento",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=20)
        
        # Frame de búsqueda
        frame_busqueda = ctk.CTkFrame(panel_izquierdo)
        frame_busqueda.pack(pady=10, padx=20, fill="x")
        
        # Búsqueda por DPI
        ctk.CTkLabel(
            frame_busqueda,
            text="Buscar por DPI:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5), anchor="w", padx=10)
        
        frame_dpi = ctk.CTkFrame(frame_busqueda)
        frame_dpi.pack(pady=5, padx=10, fill="x")
        
        self.entry_dpi = ctk.CTkEntry(
            frame_dpi,
            placeholder_text="Ej: 2008 22829 0101",
            font=ctk.CTkFont(size=14)
        )
        self.entry_dpi.pack(side="left", padx=5, expand=True, fill="x")
        self.entry_dpi.bind("<Return>", lambda e: self.buscar_por_dpi())
        
        btn_buscar_dpi = ctk.CTkButton(
            frame_dpi,
            text="🔍",
            command=self.buscar_por_dpi,
            width=50
        )
        btn_buscar_dpi.pack(side="left", padx=5)
        
        # Separador
        ctk.CTkLabel(
            frame_busqueda,
            text="O",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(pady=10)
        
        # Búsqueda por nombre
        ctk.CTkLabel(
            frame_busqueda,
            text="Buscar por Nombre:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5), anchor="w", padx=10)
        
        frame_nombre = ctk.CTkFrame(frame_busqueda)
        frame_nombre.pack(pady=5, padx=10, fill="x")
        
        self.entry_nombre = ctk.CTkEntry(
            frame_nombre,
            placeholder_text="Ej: Juan Pérez",
            font=ctk.CTkFont(size=14)
        )
        self.entry_nombre.pack(side="left", padx=5, expand=True, fill="x")
        self.entry_nombre.bind("<Return>", lambda e: self.buscar_por_nombre())
        
        btn_buscar_nombre = ctk.CTkButton(
            frame_nombre,
            text="🔍",
            command=self.buscar_por_nombre,
            width=50
        )
        btn_buscar_nombre.pack(side="left", padx=5)

        # ✅ Selector de año para búsqueda
        frame_filtro_año = ctk.CTkFrame(frame_busqueda, fg_color="transparent")
        frame_filtro_año.pack(pady=(15, 5), padx=10, fill="x")

        ctk.CTkLabel(
            frame_filtro_año,
            text="Filtrar por año:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=(0, 10))

        self.combo_año_busqueda = ctk.CTkComboBox(
            frame_filtro_año,
            values=["Todos"],
            command=self.filtrar_busqueda_por_año,
            width=120,
            state="readonly"
        )
        self.combo_año_busqueda.pack(side="left")
        self.combo_año_busqueda.set("Todos")

        # Frame de resultados
        ctk.CTkLabel(
            panel_izquierdo,
            text="Resultados de búsqueda:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 10), padx=20, anchor="w")
        
        self.resultados_frame = ctk.CTkScrollableFrame(panel_izquierdo)
        self.resultados_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        self.lbl_sin_resultados = ctk.CTkLabel(
            self.resultados_frame,
            text="Realice una búsqueda para ver resultados",
            text_color="gray",
            font=ctk.CTkFont(size=14)
        )
        self.lbl_sin_resultados.pack(pady=50)
        
        # Frame de información de persona seleccionada
        self.info_frame = ctk.CTkFrame(panel_izquierdo)
        self.info_frame.pack(pady=10, padx=20, fill="x")
        self.info_frame.pack_forget()  # Ocultar inicialmente
        
        # Frame de documentos de la persona
        ctk.CTkLabel(
            panel_izquierdo,
            text="Documentos de la persona:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 5), padx=20, anchor="w")

        self.documentos_frame = ctk.CTkScrollableFrame(panel_izquierdo)
        self.documentos_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        self.lbl_sin_documentos = ctk.CTkLabel(
            self.documentos_frame,
            text="Seleccione una persona para ver sus documentos",
            text_color="gray",
            font=ctk.CTkFont(size=12)
        )
        self.lbl_sin_documentos.pack(pady=30)
        
        # ===== PANEL DERECHO: Visor de documento =====
        panel_derecho = ctk.CTkFrame(container)
        panel_derecho.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        # Título del visor
        ctk.CTkLabel(
            panel_derecho,
            text="📄 Vista Previa del Documento",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=10)
        
        # Frame scrollable para el visor
        self.visor_scroll = ctk.CTkScrollableFrame(panel_derecho, width=650, height=750)
        self.visor_scroll.pack(pady=10, padx=10, fill="both", expand=True)
        
        self.lbl_visor_estado = ctk.CTkLabel(
            self.visor_scroll,
            text="Seleccione un documento para visualizar",
            text_color="gray",
            font=ctk.CTkFont(size=14)
        )
        self.lbl_visor_estado.pack(pady=200)
    
    def cargar_todos_documentos_iniciales(self):
        """Carga todos los documentos al iniciar la ventana"""
        import datetime
        
        self.todos_documentos = []
        documentos_por_año_temp = {}
        
        directorio_docs = DOCUMENTOS_DIR
        
        if not os.path.exists(directorio_docs):
            return
        
        try:
            # Obtener todas las personas de la BD
            todas_personas = self.db.obtener_todas_personas()
            
            if not todas_personas:
                return
            
            archivos = os.listdir(directorio_docs)
            
            for resultado in todas_personas:
                # Extraer datos directamente de la tupla
                # Formato: (id, nombre_completo, dpi, edad, estado_civil, nacionalidad, 
                #           domicilio, nivel_academico, apellido_casada, fecha_registro, sexo, fecha_nacimiento)
                persona_id = resultado[0]
                nombre_completo = resultado[1]
                dpi = resultado[2]
                
                dpi_normalizado = self.normalizar_dpi(dpi)
                
                for archivo in archivos:
                    # Verificar extensión válida
                    if not (archivo.lower().endswith('.docx') or archivo.lower().endswith('.pdf')):
                        continue
                    
                    # Normalizar nombre del archivo
                    archivo_normalizado = archivo.replace(" ", "").replace("_", "").replace("-", "")
                    
                    # Verificar si contiene el DPI
                    if dpi_normalizado.lower() in archivo_normalizado.lower():
                        ruta_completa = os.path.join(directorio_docs, archivo)
                        
                        # Extraer año del documento
                        año = None
                        try:
                            from utils.document_extractor import DocumentExtractor
                            datos_extraidos = DocumentExtractor.extraer_datos(ruta_completa)
                            if datos_extraidos and 'año' in datos_extraidos:
                                año = datos_extraidos['año']
                        except Exception as e:
                            print(f"Error al extraer año de {archivo}: {e}")
                        
                        # Si no se pudo extraer, usar fecha de modificación
                        if not año:
                            fecha_modificacion = os.path.getmtime(ruta_completa)
                            fecha_obj = datetime.datetime.fromtimestamp(fecha_modificacion)
                            año = fecha_obj.year
                        
                        # Obtener fecha de modificación
                        fecha_modificacion = os.path.getmtime(ruta_completa)
                        fecha_obj = datetime.datetime.fromtimestamp(fecha_modificacion)
                        fecha_str = fecha_obj.strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Obtener extensión
                        extension = archivo.lower().split('.')[-1].upper()
                        
                        # Formato: (doc_id, nombre_archivo, ruta_archivo, fecha_carga, tipo_documento, persona_id, año, nombre_persona)
                        doc_info = (None, archivo, ruta_completa, fecha_str, extension, persona_id, año, nombre_completo)
                        self.todos_documentos.append(doc_info)
                        
                        # Agrupar por año
                        if año not in documentos_por_año_temp:
                            documentos_por_año_temp[año] = []
                        documentos_por_año_temp[año].append(doc_info)
            
            # Actualizar ComboBox de año
            if documentos_por_año_temp:
                años_disponibles = sorted(documentos_por_año_temp.keys(), reverse=True)
                valores_combo = ["Todos"] + [str(año) for año in años_disponibles]
                self.combo_año_busqueda.configure(values=valores_combo)
                self.combo_año_busqueda.set("Todos")
                
                # Guardar referencia
                self.documentos_por_año_busqueda = documentos_por_año_temp
                
                # Mostrar TODOS los documentos
                self.mostrar_documentos_iniciales(documentos_por_año_temp)
            else:
                # No hay documentos, mostrar mensaje
                for widget in self.resultados_frame.winfo_children():
                    widget.destroy()
                
                ctk.CTkLabel(
                    self.resultados_frame,
                    text="No hay documentos registrados",
                    text_color="gray",
                    font=ctk.CTkFont(size=14)
                ).pack(pady=50)
                
                self.combo_año_busqueda.configure(values=["Todos"])
                self.combo_año_busqueda.set("Todos")
        
        except Exception as e:
            print(f"Error al cargar documentos iniciales: {e}")
            import traceback
            traceback.print_exc()

    def mostrar_documentos_iniciales(self, documentos_por_año_temp):
        """Muestra todos los documentos iniciales agrupados por año"""
        # Limpiar frame de resultados
        for widget in self.resultados_frame.winfo_children():
            widget.destroy()
        
        # Ordenar años de más reciente a más antiguo
        años_ordenados = sorted(documentos_por_año_temp.keys(), reverse=True)
        
        for año in años_ordenados:
            # Título del año
            ctk.CTkLabel(
                self.resultados_frame,
                text=f"📅 Documentos de {año}",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=COLOR_PRIMARY
            ).pack(pady=(15, 10), padx=10, anchor="w")
            
            # Documentos del año ordenados por fecha
            documentos_año = sorted(
                documentos_por_año_temp[año],
                key=lambda x: x[3],  # fecha
                reverse=True
            )
            
            for doc in documentos_año:
                # Formato: (doc_id, nombre_archivo, ruta_archivo, fecha_carga, tipo_documento, persona_id, año, nombre_persona)
                doc_id, nombre_archivo, ruta_archivo, fecha_carga, tipo_documento, persona_id, año_doc, nombre_persona = doc
                
                frame_doc = ctk.CTkFrame(self.resultados_frame)
                frame_doc.pack(pady=5, padx=10, fill="x")
                
                info_doc = f"📄 {nombre_archivo}\n👤 {nombre_persona}\n📅 {fecha_carga} | {tipo_documento}"
                
                ctk.CTkLabel(
                    frame_doc,
                    text=info_doc,
                    anchor="w",
                    justify="left",
                    font=ctk.CTkFont(size=11)
                ).pack(side="left", padx=10, pady=5, expand=True, fill="x")
                
                # Botón SELECCIONAR
                btn_seleccionar = ctk.CTkButton(
                    frame_doc,
                    text="✅ Seleccionar",
                    command=lambda pid=persona_id: self.seleccionar_persona_por_id(pid),
                    width=120,
                    fg_color=COLOR_SUCCESS,
                    hover_color="#27ae60"
                )
                btn_seleccionar.pack(side="right", padx=5)
            
            # Separador entre años
            if año != años_ordenados[-1]:
                ctk.CTkFrame(
                    self.resultados_frame,
                    height=2,
                    fg_color="gray"
                ).pack(pady=10, padx=20, fill="x")
        
    def buscar_por_dpi(self):
        """Busca una persona por DPI"""
        dpi = self.entry_dpi.get().strip()
        
        if not dpi:
            messagebox.showwarning("Advertencia", "Ingrese un DPI para buscar")
            return
        
        resultado = self.db.buscar_persona_por_dpi(dpi)
        
        if resultado:
            self.mostrar_resultados([resultado])
        else:
            self.mostrar_sin_resultados()
            messagebox.showinfo(
                "No encontrado",
                "No se encontró ninguna persona con ese DPI.\n\n"
                "Puede crear un nuevo documento desde el menú principal."
            )
    
    def buscar_por_nombre(self):
        """Busca personas por nombre"""
        nombre = self.entry_nombre.get().strip()
        
        if not nombre:
            messagebox.showwarning("Advertencia", "Ingrese un nombre para buscar")
            return
        
        resultados = self.db.buscar_personas_por_nombre(nombre)
        
        if resultados:
            self.resultados_busqueda = resultados  # ✅ Guardar resultados
            self.cargar_todos_documentos_busqueda(resultados)  # ✅ Cargar documentos
            self.mostrar_resultados(resultados)
        else:
            self.mostrar_sin_resultados()
            messagebox.showinfo(
                "No encontrado",
                "No se encontraron personas con ese nombre.\n\n"
                "Puede crear un nuevo documento desde el menú principal."
            )
    
    def cargar_todos_documentos_busqueda(self, resultados):
        """Carga todos los documentos de las personas encontradas en la búsqueda"""
        import datetime
        
        self.todos_documentos = []
        documentos_por_año_temp = {}
        
        directorio_docs = DOCUMENTOS_DIR
        
        if not os.path.exists(directorio_docs):
            return
        
        try:
            archivos = os.listdir(directorio_docs)
            
            for resultado in resultados:
                persona = Persona.from_tuple(resultado)
                dpi_normalizado = self.normalizar_dpi(persona.dpi)
                
                for archivo in archivos:
                    # Verificar extensión válida
                    if not (archivo.lower().endswith('.docx') or archivo.lower().endswith('.pdf')):
                        continue
                    
                    # Normalizar nombre del archivo
                    archivo_normalizado = archivo.replace(" ", "").replace("_", "").replace("-", "")
                    
                    # Verificar si contiene el DPI
                    if dpi_normalizado.lower() in archivo_normalizado.lower():
                        ruta_completa = os.path.join(directorio_docs, archivo)
                        
                        # ✅ Extraer año del documento usando DocumentExtractor
                        año = None
                        try:
                            from utils.document_extractor import DocumentExtractor
                            datos_extraidos = DocumentExtractor.extraer_datos(ruta_completa)
                            if datos_extraidos and 'año' in datos_extraidos:
                                año = datos_extraidos['año']
                        except Exception as e:
                            print(f"Error al extraer año de {archivo}: {e}")
                        
                        # Si no se pudo extraer, usar fecha de modificación como fallback
                        if not año:
                            fecha_modificacion = os.path.getmtime(ruta_completa)
                            fecha_obj = datetime.datetime.fromtimestamp(fecha_modificacion)
                            año = fecha_obj.year
                        
                        # Obtener fecha de modificación para mostrar
                        fecha_modificacion = os.path.getmtime(ruta_completa)
                        fecha_obj = datetime.datetime.fromtimestamp(fecha_modificacion)
                        fecha_str = fecha_obj.strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Obtener fecha de modificación para mostrar
                        fecha_modificacion = os.path.getmtime(ruta_completa)
                        fecha_obj = datetime.datetime.fromtimestamp(fecha_modificacion)
                        fecha_str = fecha_obj.strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Obtener extensión
                        extension = archivo.lower().split('.')[-1].upper()
                        
                        doc_info = (None, archivo, ruta_completa, fecha_str, extension, persona.id, año, persona.nombre_completo)
                        self.todos_documentos.append(doc_info)
                        
                        # Agrupar por año
                        if año not in documentos_por_año_temp:
                            documentos_por_año_temp[año] = []
                        documentos_por_año_temp[año].append(doc_info)
            
            # Actualizar ComboBox de año en búsqueda
            if documentos_por_año_temp:
                años_disponibles = sorted(documentos_por_año_temp.keys(), reverse=True)
                valores_combo = ["Todos"] + [str(año) for año in años_disponibles]
                self.combo_año_busqueda.configure(values=valores_combo)
                
                # ✅ Seleccionar "Todos" por defecto
                self.combo_año_busqueda.set("Todos")
                
                # ✅ Guardar referencia para filtrado
                self.documentos_por_año_busqueda = documentos_por_año_temp
                
                # ✅ Mostrar TODOS los documentos por defecto
                self.mostrar_documentos_busqueda_por_año("Todos", documentos_por_año_temp)
            else:
                self.combo_año_busqueda.configure(values=["Todos"])
                self.combo_año_busqueda.set("Todos")
        
        except Exception as e:
            print(f"Error al cargar documentos de búsqueda: {e}")
            import traceback
            traceback.print_exc()
    
    def filtrar_busqueda_por_año(self, año_str):
        """Filtra los documentos de búsqueda por año"""
        if not self.todos_documentos:
            return
        
        # Usar la referencia guardada
        if hasattr(self, 'documentos_por_año_busqueda'):
            self.mostrar_documentos_busqueda_por_año(año_str, self.documentos_por_año_busqueda)
        else:
            # Reagrupar documentos por año si no existe la referencia
            documentos_por_año_temp = {}
            for doc in self.todos_documentos:
                año = doc[6]
                if año not in documentos_por_año_temp:
                    documentos_por_año_temp[año] = []
                documentos_por_año_temp[año].append(doc)
            
            self.mostrar_documentos_busqueda_por_año(año_str, documentos_por_año_temp)
    
    def mostrar_documentos_busqueda_por_año(self, año_str, documentos_por_año_temp):
        """Muestra los documentos de búsqueda filtrados por año"""
        # Limpiar frame de resultados
        for widget in self.resultados_frame.winfo_children():
            widget.destroy()
        
        if año_str == "Todos":
            # Mostrar todos los años
            años_ordenados = sorted(documentos_por_año_temp.keys(), reverse=True)
            
            for año in años_ordenados:
                # Título del año
                ctk.CTkLabel(
                    self.resultados_frame,
                    text=f"📅 Documentos de {año}",
                    font=ctk.CTkFont(size=14, weight="bold"),
                    text_color=COLOR_PRIMARY
                ).pack(pady=(15, 10), padx=10, anchor="w")
                
                # Documentos del año
                documentos_año = sorted(
                    documentos_por_año_temp[año],
                    key=lambda x: x[3],  # fecha
                    reverse=True
                )
                
                for doc in documentos_año:
                    # Formato: (doc_id, nombre_archivo, ruta_archivo, fecha_carga, tipo_documento, persona_id, año, nombre_persona)
                    doc_id, nombre_archivo, ruta_archivo, fecha_carga, tipo_documento, persona_id, año_doc, nombre_persona = doc
                    
                    frame_doc = ctk.CTkFrame(self.resultados_frame)
                    frame_doc.pack(pady=5, padx=10, fill="x")
                    
                    info_doc = f"📄 {nombre_archivo}\n👤 {nombre_persona}\n📅 {fecha_carga} | {tipo_documento}"
                    
                    ctk.CTkLabel(
                        frame_doc,
                        text=info_doc,
                        anchor="w",
                        justify="left",
                        font=ctk.CTkFont(size=11)
                    ).pack(side="left", padx=10, pady=5, expand=True, fill="x")
                    
                    # Botón SELECCIONAR
                    btn_seleccionar = ctk.CTkButton(
                        frame_doc,
                        text="✅ Seleccionar",
                        command=lambda pid=persona_id: self.seleccionar_persona_por_id(pid),
                        width=120,
                        fg_color=COLOR_SUCCESS,
                        hover_color="#27ae60"
                    )
                    btn_seleccionar.pack(side="right", padx=5)
                
                # Separador entre años
                ctk.CTkFrame(
                    self.resultados_frame,
                    height=2,
                    fg_color="gray"
                ).pack(pady=10, padx=20, fill="x")
        
        else:
            # Mostrar solo el año seleccionado
            año = int(año_str)
            
            if año in documentos_por_año_temp:
                # Título del año
                ctk.CTkLabel(
                    self.resultados_frame,
                    text=f"📅 Documentos de {año}",
                    font=ctk.CTkFont(size=14, weight="bold"),
                    text_color=COLOR_PRIMARY
                ).pack(pady=(10, 15), padx=10, anchor="w")
                
                # Documentos del año
                documentos_año = sorted(
                    documentos_por_año_temp[año],
                    key=lambda x: x[3],
                    reverse=True
                )
                
                for doc in documentos_año:
                    # Formato: (doc_id, nombre_archivo, ruta_archivo, fecha_carga, tipo_documento, persona_id, año, nombre_persona)
                    doc_id, nombre_archivo, ruta_archivo, fecha_carga, tipo_documento, persona_id, año_doc, nombre_persona = doc
                    
                    frame_doc = ctk.CTkFrame(self.resultados_frame)
                    frame_doc.pack(pady=5, padx=10, fill="x")
                    
                    info_doc = f"📄 {nombre_archivo}\n👤 {nombre_persona}\n📅 {fecha_carga} | {tipo_documento}"
                    
                    ctk.CTkLabel(
                        frame_doc,
                        text=info_doc,
                        anchor="w",
                        justify="left",
                        font=ctk.CTkFont(size=11)
                    ).pack(side="left", padx=10, pady=5, expand=True, fill="x")
                    
                    # Botón SELECCIONAR
                    btn_seleccionar = ctk.CTkButton(
                        frame_doc,
                        text="✅ Seleccionar",
                        command=lambda pid=persona_id: self.seleccionar_persona_por_id(pid),
                        width=120,
                        fg_color=COLOR_SUCCESS,
                        hover_color="#27ae60"
                    )
                    btn_seleccionar.pack(side="right", padx=5)
        
    def mostrar_sin_resultados(self):
        """Muestra mensaje cuando no hay resultados"""
        # Limpiar resultados
        for widget in self.resultados_frame.winfo_children():
            widget.destroy()
        
        self.lbl_sin_resultados = ctk.CTkLabel(
            self.resultados_frame,
            text="No se encontraron resultados",
            text_color="orange",
            font=ctk.CTkFont(size=14)
        )
        self.lbl_sin_resultados.pack(pady=50)
        
        # Ocultar info y documentos
        self.info_frame.pack_forget()
        self.persona_seleccionada = None
        self.limpiar_documentos()
    
    def mostrar_resultados(self, resultados):
        """Muestra los resultados de la búsqueda"""
        # Limpiar resultados anteriores
        for widget in self.resultados_frame.winfo_children():
            widget.destroy()
        
        for resultado in resultados:
            persona = Persona.from_tuple(resultado)
            
            frame_resultado = ctk.CTkFrame(self.resultados_frame)
            frame_resultado.pack(pady=5, padx=10, fill="x")
            
            # Información de la persona
            info_text = f"👤 {persona.nombre_completo}\n📋 DPI: {persona.dpi}"
            if persona.edad:
                info_text += f"\n🎂 Edad: {persona.edad} años"
            
            ctk.CTkLabel(
                frame_resultado,
                text=info_text,
                anchor="w",
                justify="left",
                font=ctk.CTkFont(size=12)
            ).pack(side="left", padx=10, pady=10, expand=True, fill="x")
            
            # Botón Seleccionar (solo carga la persona en el panel izquierdo de esta ventana)
            btn_seleccionar = ctk.CTkButton(
                frame_resultado,
                text="✅ Seleccionar",          # mini imagen como en "👁️ Ver"
                command=lambda p=persona: self.seleccionar_persona(p),
                width=120,
                fg_color=COLOR_SUCCESS,
                hover_color="#27ae60"
            )
            btn_seleccionar.pack(side="right", padx=5)
    
    def seleccionar_persona(self, persona):
        """Selecciona una persona y muestra su información"""
        self.persona_seleccionada = persona
        
        # Mostrar información detallada
        self.mostrar_info_persona()
        
        # Cargar documentos de la persona
        self.cargar_documentos_persona()
    
    def seleccionar_persona_por_id(self, persona_id):
        """Selecciona una persona por su ID y muestra su información"""
        try:
            # Obtener persona completa desde la BD
            resultado_persona = self.db.obtener_persona_por_id(persona_id)
            
            if not resultado_persona:
                messagebox.showerror("Error", "No se pudo obtener la información de la persona.")
                return
            
            # Convertir a objeto Persona
            persona = Persona.from_tuple(resultado_persona)
            
            # Usar el método existente
            self.seleccionar_persona(persona)
        
        except Exception as e:
            messagebox.showerror("Error", f"Error al seleccionar persona:\n{str(e)}")
            print(f"Error en seleccionar_persona_por_id: {e}")
            import traceback
            traceback.print_exc()
        
    def abrir_editor_persona(self, persona):
        try:
            editor = VentanaCrearDocumento(
                self.ventana,
                self.db,
                es_integrado=False,
                solo_formulario=True
            )

            resultado = self.db.obtener_persona_por_id(persona.id)
            if not resultado:
                messagebox.showerror("Error", "No se pudo obtener la información completa de la persona.")
                return

            editor.cargar_datos_persona(resultado)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el editor:\n{str(e)}")
    
    def mostrar_info_persona(self):
        """Muestra información detallada de la persona seleccionada"""
        # Limpiar frame de info
        for widget in self.info_frame.winfo_children():
            widget.destroy()
        
        self.info_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(
            self.info_frame,
            text="✅ Persona Seleccionada",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLOR_SUCCESS
        ).pack(pady=10)
        
        # Información
        info_text = f"""
👤 Nombre: {self.persona_seleccionada.nombre_completo}
📋 DPI: {self.persona_seleccionada.dpi}
🎂 Edad: {self.persona_seleccionada.edad if self.persona_seleccionada.edad else 'N/A'}
💍 Estado Civil: {self.persona_seleccionada.estado_civil if self.persona_seleccionada.estado_civil else 'N/A'}
🌍 Nacionalidad: {self.persona_seleccionada.nacionalidad if self.persona_seleccionada.nacionalidad else 'N/A'}
🎓 Nivel Académico: {self.persona_seleccionada.nivel_academico if self.persona_seleccionada.nivel_academico else 'N/A'}
🏠 Domicilio: {self.persona_seleccionada.domicilio if self.persona_seleccionada.domicilio else 'N/A'}
        """
        
        ctk.CTkLabel(
            self.info_frame,
            text=info_text.strip(),
            anchor="w",
            justify="left",
            font=ctk.CTkFont(size=12)
        ).pack(pady=5, padx=20, fill="x")
    
    def normalizar_dpi(self, dpi):
        """Convierte DPI con espacios o guiones a formato sin separadores"""
        return dpi.replace(" ", "").replace("_", "").replace("-", "")
    
    def cargar_documentos_persona(self):
        """Carga los documentos de la persona seleccionada y los agrupa por año"""
        # Limpiar frame de documentos
        for widget in self.documentos_frame.winfo_children():
            widget.destroy()
        
        # Directorio de documentos (centralizado)
        directorio_docs = DOCUMENTOS_DIR
        
        if not os.path.exists(directorio_docs):
            self.lbl_sin_documentos = ctk.CTkLabel(
                self.documentos_frame,
                text="No existe el directorio de documentos",
                text_color="red",
                font=ctk.CTkFont(size=12)
            )
            self.lbl_sin_documentos.pack(pady=30)
            return
                
        # Normalizar DPI de la persona seleccionada
        dpi_normalizado = self.normalizar_dpi(self.persona_seleccionada.dpi)
        
        # Buscar todos los archivos
        self.documentos_persona = []
        self.documentos_por_año = {}  # ✅ Reiniciar agrupación
        
        try:
            import datetime
            archivos = os.listdir(directorio_docs)
            
            for archivo in archivos:
                # Verificar extensión válida
                if not (archivo.lower().endswith('.docx') or archivo.lower().endswith('.pdf')):
                    continue
                
                # Normalizar nombre del archivo
                archivo_normalizado = archivo.replace(" ", "").replace("_", "").replace("-", "")
                
                # Verificar si contiene el DPI (sin separadores)
                if dpi_normalizado.lower() in archivo_normalizado.lower():
                    ruta_completa = os.path.join(directorio_docs, archivo)
                    
                    # ✅ Extraer año del documento usando DocumentExtractor
                    año = None
                    try:
                        from utils.document_extractor import DocumentExtractor
                        datos_extraidos = DocumentExtractor.extraer_datos(ruta_completa)
                        if datos_extraidos and 'año' in datos_extraidos:
                            año = datos_extraidos['año']
                    except Exception as e:
                        print(f"Error al extraer año de {archivo}: {e}")
                    
                    # Si no se pudo extraer, usar fecha de modificación como fallback
                    if not año:
                        fecha_modificacion = os.path.getmtime(ruta_completa)
                        fecha_obj = datetime.datetime.fromtimestamp(fecha_modificacion)
                        año = fecha_obj.year
                    
                    # Obtener fecha de modificación para mostrar
                    fecha_modificacion = os.path.getmtime(ruta_completa)
                    fecha_obj = datetime.datetime.fromtimestamp(fecha_modificacion)
                    fecha_str = fecha_obj.strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Obtener extensión
                    extension = archivo.lower().split('.')[-1].upper()
                    
                    doc_info = (None, archivo, ruta_completa, fecha_str, extension, self.persona_seleccionada.id, año)
                    self.documentos_persona.append(doc_info)
                    
                    # ✅ Agrupar por año
                    if año not in self.documentos_por_año:
                        self.documentos_por_año[año] = []
                    self.documentos_por_año[año].append(doc_info)
        
        except Exception as e:
            print(f"Error al listar archivos: {e}")
            import traceback
            traceback.print_exc()
        
        if not self.documentos_persona:
            self.lbl_sin_documentos = ctk.CTkLabel(
                self.documentos_frame,
                text=f"No se encontraron documentos para el DPI: {self.persona_seleccionada.dpi}",
                text_color="orange",
                font=ctk.CTkFont(size=12)
            )
            self.lbl_sin_documentos.pack(pady=30)
            return
        

        # ✅ Mostrar todos los documentos agrupados por año
        self.mostrar_todos_documentos_persona()
    
    def mostrar_todos_documentos_persona(self):
        """Muestra todos los documentos de la persona agrupados por año"""
        # Limpiar frame
        for widget in self.documentos_frame.winfo_children():
            widget.destroy()
        
        # Ordenar años de más reciente a más antiguo
        años_ordenados = sorted(self.documentos_por_año.keys(), reverse=True)
        
        for año in años_ordenados:
            # Título del año
            ctk.CTkLabel(
                self.documentos_frame,
                text=f"📅 {año}",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=COLOR_PRIMARY
            ).pack(pady=(15, 10), padx=10, anchor="w")
            
            # Documentos del año ordenados por fecha
            documentos_año = sorted(
                self.documentos_por_año[año],
                key=lambda x: x[3],  # fecha_carga
                reverse=True
            )
            
            for doc in documentos_año:
                doc_id, nombre_archivo, ruta_archivo, fecha_carga, tipo_documento, persona_id, año_doc = doc
                
                # Encontrar índice en la lista completa
                index = next(i for i, d in enumerate(self.documentos_persona) if d[2] == ruta_archivo)
                
                frame_doc = ctk.CTkFrame(self.documentos_frame)
                frame_doc.pack(pady=5, padx=10, fill="x")
                
                info_doc = f"📄 {nombre_archivo}\n📅 {fecha_carga} | {tipo_documento}"
                
                ctk.CTkLabel(
                    frame_doc,
                    text=info_doc,
                    anchor="w",
                    justify="left",
                    font=ctk.CTkFont(size=11)
                ).pack(side="left", padx=10, pady=5, expand=True, fill="x")
                
                # Botón VER
                btn_ver = ctk.CTkButton(
                    frame_doc,
                    text="👁️ Ver",
                    command=lambda idx=index: self.ver_documento(idx),
                    width=90,
                    fg_color="#4a4a4a",
                    hover_color="#6b6b6b"
                )
                btn_ver.pack(side="right", padx=5)
                
                # Botón EDITAR
                btn_editar_doc = ctk.CTkButton(
                    frame_doc,
                    text="✏️ Editar",
                    command=lambda idx=index: self.editar_documento(idx),
                    width=90,
                    fg_color=COLOR_PRIMARY,
                    hover_color="#2980b9"
                )
                btn_editar_doc.pack(side="right", padx=5)
            
            # Separador entre años
            if año != años_ordenados[-1]:  # No agregar separador después del último año
                ctk.CTkFrame(
                    self.documentos_frame,
                    height=2,
                    fg_color="gray"
                ).pack(pady=10, padx=20, fill="x")
                    
    def ver_documento(self, index):
        """Muestra un documento en el visor"""
        if not self.documentos_persona or index >= len(self.documentos_persona):
            return
        
        doc = self.documentos_persona[index]
        doc_id, nombre_archivo, ruta_archivo, fecha_carga, tipo_documento, persona_id, año_doc = doc
        
        # Verificar que el archivo existe
        if not os.path.exists(ruta_archivo):
            messagebox.showerror(
                "Error",
                f"El archivo no existe:\n{ruta_archivo}"
            )
            return
        
        # Limpiar visor
        for widget in self.visor_scroll.winfo_children():
            widget.destroy()
        
        self.lbl_visor_estado = ctk.CTkLabel(
            self.visor_scroll,
            text="Cargando documento...",
            text_color="orange",
            font=ctk.CTkFont(size=14)
        )
        self.lbl_visor_estado.pack(pady=20)
        self.ventana.update()
        
        try:
            # Convertir a PDF temporal para visualización
            temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_pdf.close()
            
            convert(ruta_archivo, temp_pdf.name)
            
            # Mostrar PDF
            self.mostrar_pdf_en_visor(temp_pdf.name)
            
            # Limpiar archivo temporal
            os.unlink(temp_pdf.name)
        
        except Exception as e:
            self.lbl_visor_estado.configure(
                text=f"Error al cargar documento:\n{str(e)}",
                text_color="red"
            )
    
    def mostrar_pdf_en_visor(self, pdf_path):
        """Muestra el PDF renderizado como imágenes en el visor"""
        # Limpiar visor
        for widget in self.visor_scroll.winfo_children():
            widget.destroy()
        
        try:
            pdf_document = fitz.open(pdf_path)
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # Renderizar página a imagen
                zoom = 1.5
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                
                # Convertir a PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Redimensionar para ajustar al visor
                max_width = 650
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                
                # Convertir a PhotoImage
                photo = ImageTk.PhotoImage(img)
                
                # Crear label para mostrar la imagen
                label = ctk.CTkLabel(self.visor_scroll, image=photo, text="")
                label.image = photo
                label.pack(pady=10)
                
                # Agregar separador entre páginas
                if page_num < len(pdf_document) - 1:
                    separador = ctk.CTkLabel(
                        self.visor_scroll,
                        text=f"--- Página {page_num + 1} ---",
                        font=ctk.CTkFont(size=12),
                        text_color="gray"
                    )
                    separador.pack(pady=5)
            
            pdf_document.close()
            
        except Exception as e:
            self.lbl_visor_estado = ctk.CTkLabel(
                self.visor_scroll,
                text=f"Error al mostrar PDF:\n{str(e)}",
                text_color="red"
            )
            self.lbl_visor_estado.pack(pady=20)
    
    def editar_documento(self, index):
        """Abre el editor para modificar el documento existente y los datos de la persona."""
        if not self.documentos_persona or index >= len(self.documentos_persona):
            return

        doc = self.documentos_persona[index]
        doc_id, nombre_archivo, ruta_archivo, fecha_carga, tipo_documento, persona_id, año_doc = doc

        if not os.path.exists(ruta_archivo):
            messagebox.showerror(
                "Error",
                f"El archivo no existe:\n{ruta_archivo}"
            )
            return

        try:
            # Obtener persona completa desde la BD
            resultado_persona = self.db.obtener_persona_por_id(persona_id)
            if not resultado_persona:
                messagebox.showerror(
                    "Error",
                    "No se pudo obtener la información completa de la persona asociada."
                )
                return

            # Crear ventana de edición usando la GUI de creación
            editor = VentanaCrearDocumento(
                self.ventana,
                self.db,
                es_integrado=False,
                solo_formulario=True,   # solo formulario
                modo_edicion=True       # IMPORTANTE: modo edición
            )

            # Cargar datos de persona en el formulario
            editor.cargar_datos_persona(resultado_persona)

            # Indicarle al editor qué documento está editando
            editor.establecer_documento_original(
                ruta_archivo=ruta_archivo,
                nombre_archivo=nombre_archivo,
                persona_id=persona_id
            )

            # Callback para refrescar documentos y estadísticas al guardar
            if hasattr(editor, "set_callback_guardado"):
                editor.set_callback_guardado(self._callback_despues_edicion)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el editor:\n{str(e)}")

    def _callback_despues_edicion(self):
        """Se llama después de guardar cambios en el editor."""
        # Recargar documentos de la persona seleccionada
        if self.persona_seleccionada:
            self.cargar_documentos_persona()
        # Actualizar estadísticas globales si hay callback
        if self.callback_actualizar:
            self.callback_actualizar()
    
    def ver_documento_directo(self, ruta_archivo):
        """Muestra un documento directamente desde la ruta"""
        if not os.path.exists(ruta_archivo):
            messagebox.showerror("Error", f"El archivo no existe:\n{ruta_archivo}")
            return
        
        # Limpiar visor
        for widget in self.visor_scroll.winfo_children():
            widget.destroy()
        
        self.lbl_visor_estado = ctk.CTkLabel(
            self.visor_scroll,
            text="Cargando documento...",
            text_color="orange",
            font=ctk.CTkFont(size=14)
        )
        self.lbl_visor_estado.pack(pady=20)
        self.ventana.update()
        
        try:
            temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_pdf.close()
            
            convert(ruta_archivo, temp_pdf.name)
            self.mostrar_pdf_en_visor(temp_pdf.name)
            os.unlink(temp_pdf.name)
        
        except Exception as e:
            self.lbl_visor_estado.configure(
                text=f"Error al cargar documento:\n{str(e)}",
                text_color="red"
            )

    def editar_documento_directo(self, ruta_archivo, persona_id, nombre_archivo):
        """Edita un documento directamente"""
        try:
            resultado_persona = self.db.obtener_persona_por_id(persona_id)
            if not resultado_persona:
                messagebox.showerror("Error", "No se pudo obtener la información de la persona.")
                return
            
            editor = VentanaCrearDocumento(
                self.ventana,
                self.db,
                es_integrado=False,
                solo_formulario=True,
                modo_edicion=True
            )
            
            editor.cargar_datos_persona(resultado_persona)
            editor.establecer_documento_original(
                ruta_archivo=ruta_archivo,
                nombre_archivo=nombre_archivo,
                persona_id=persona_id
            )
            
            if hasattr(editor, "set_callback_guardado"):
                editor.set_callback_guardado(self._callback_despues_edicion_busqueda)
        
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el editor:\n{str(e)}")

    def _callback_despues_edicion_busqueda(self):
        """Callback después de editar desde búsqueda"""
        # Recargar documentos de búsqueda
        if self.resultados_busqueda:
            self.cargar_todos_documentos_busqueda(self.resultados_busqueda)
        
        # Actualizar estadísticas
        if self.callback_actualizar:
            self.callback_actualizar()
    
    def limpiar_documentos(self):
        """Limpia la lista de documentos"""
        for widget in self.documentos_frame.winfo_children():
            widget.destroy()
        
        self.lbl_sin_documentos = ctk.CTkLabel(
            self.documentos_frame,
            text="Seleccione una persona para ver sus documentos",
            text_color="gray",
            font=ctk.CTkFont(size=12)
        )
        self.lbl_sin_documentos.pack(pady=30)