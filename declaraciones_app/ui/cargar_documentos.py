import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import shutil
import tempfile
from PIL import Image, ImageTk
import fitz  # PyMuPDF
from docx2pdf import convert
from config import DOCUMENTOS_DIR, COLOR_SUCCESS, COLOR_PRIMARY
from utils import convertir_doc_a_docx, DocumentExtractor

class VentanaCargarDocumentos:
    def __init__(self, parent, db, es_integrado=False):
        self.db = db
        self.es_integrado = es_integrado
        self.callback_actualizar = None
        self.documentos_seleccionados = []
        self.documento_actual_index = 0
        
        if es_integrado:
            # Crear como Frame integrado
            self.ventana = ctk.CTkFrame(parent)
            self.ventana.pack(fill="both", expand=True)
        else:
            # Crear como ventana separada (Toplevel)
            self.ventana = ctk.CTkToplevel(parent)
            self.ventana.title("📥 Cargar Documentos a la Base de Datos")
            self.center_window()
            self.ventana.after(100, self.maximizar_ventana)
        
        self.crear_interfaz()
        self.cargar_documentos_existentes()
    
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
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def crear_interfaz(self):
        """Crea la interfaz de carga de documentos"""
        
        # Frame principal con dos columnas
        container = ctk.CTkFrame(self.ventana)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)
        
        # ===== PANEL IZQUIERDO: Lista y controles =====
        panel_izquierdo = ctk.CTkFrame(container)
        panel_izquierdo.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Título
        ctk.CTkLabel(
            panel_izquierdo,
            text="📥 Cargar Documentos",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=20)
        
        # Botones de acción
        frame_botones = ctk.CTkFrame(panel_izquierdo)
        frame_botones.pack(pady=10, padx=20, fill="x")
        
        btn_seleccionar = ctk.CTkButton(
            frame_botones,
            text="📁 Seleccionar Documentos",
            command=self.seleccionar_documentos,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        btn_seleccionar.pack(pady=5, fill="x")
        
        btn_procesar = ctk.CTkButton(
            frame_botones,
            text="⚙️ Procesar y Cargar Todos",
            command=self.procesar_todos_documentos,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLOR_SUCCESS,
            hover_color="#27ae60"
        )
        btn_procesar.pack(pady=5, fill="x")
        
        # Pestañas para documentos nuevos y existentes
        self.tabview = ctk.CTkTabview(panel_izquierdo)
        self.tabview.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Pestaña: Documentos a cargar
        self.tabview.add("📤 Nuevos")
        tab_nuevos = self.tabview.tab("📤 Nuevos")
        
        ctk.CTkLabel(
            tab_nuevos,
            text="Documentos seleccionados:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 5), padx=10, anchor="w")
        
        # Frame scrollable para la lista de nuevos
        self.lista_frame = ctk.CTkScrollableFrame(tab_nuevos, height=400)
        self.lista_frame.pack(pady=5, padx=10, fill="both", expand=True)
        
        self.lbl_lista_vacia = ctk.CTkLabel(
            self.lista_frame,
            text="No hay documentos seleccionados",
            text_color="gray",
            font=ctk.CTkFont(size=14)
        )
        self.lbl_lista_vacia.pack(pady=50)
        
        # Controles de navegación para nuevos
        frame_navegacion = ctk.CTkFrame(tab_nuevos)
        frame_navegacion.pack(pady=10, padx=10, fill="x")
        
        self.btn_anterior = ctk.CTkButton(
            frame_navegacion,
            text="◀ Anterior",
            command=self.documento_anterior,
            width=150,
            state="disabled"
        )
        self.btn_anterior.pack(side="left", padx=5)
        
        self.lbl_contador = ctk.CTkLabel(
            frame_navegacion,
            text="0 / 0",
            font=ctk.CTkFont(size=14)
        )
        self.lbl_contador.pack(side="left", expand=True)
        
        self.btn_siguiente = ctk.CTkButton(
            frame_navegacion,
            text="Siguiente ▶",
            command=self.documento_siguiente,
            width=150,
            state="disabled"
        )
        self.btn_siguiente.pack(side="right", padx=5)
        
        # Pestaña: Documentos existentes
        self.tabview.add("📚 Cargados")
        tab_existentes = self.tabview.tab("📚 Cargados")
        
        # Barra de búsqueda
        frame_busqueda = ctk.CTkFrame(tab_existentes)
        frame_busqueda.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkLabel(
            frame_busqueda,
            text="🔍 Buscar:",
            font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=5)
        
        self.entry_buscar = ctk.CTkEntry(
            frame_busqueda,
            placeholder_text="Buscar por nombre o DPI...",
            font=ctk.CTkFont(size=12)
        )
        self.entry_buscar.pack(side="left", padx=5, expand=True, fill="x")
        self.entry_buscar.bind("<KeyRelease>", lambda e: self.filtrar_documentos_existentes())
        
        btn_refrescar = ctk.CTkButton(
            frame_busqueda,
            text="🔄",
            command=self.cargar_documentos_existentes,
            width=40
        )
        btn_refrescar.pack(side="left", padx=5)
        
        # Frame scrollable para documentos existentes
        self.lista_existentes_frame = ctk.CTkScrollableFrame(tab_existentes, height=500)
        self.lista_existentes_frame.pack(pady=5, padx=10, fill="both", expand=True)
        
        self.lbl_sin_existentes = ctk.CTkLabel(
            self.lista_existentes_frame,
            text="No hay documentos cargados",
            text_color="gray",
            font=ctk.CTkFont(size=14)
        )
        self.lbl_sin_existentes.pack(pady=50)
        
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
    
    def cargar_documentos_existentes(self):
        """Carga todos los documentos existentes en la base de datos"""
        # Limpiar lista
        for widget in self.lista_existentes_frame.winfo_children():
            widget.destroy()
        
        # Obtener todos los documentos
        self.documentos_existentes = self.db.obtener_todos_documentos()
        
        if not self.documentos_existentes:
            self.lbl_sin_existentes = ctk.CTkLabel(
                self.lista_existentes_frame,
                text="No hay documentos cargados en la base de datos",
                text_color="gray",
                font=ctk.CTkFont(size=14)
            )
            self.lbl_sin_existentes.pack(pady=50)
            return
        
        # Mostrar documentos
        self.mostrar_documentos_existentes(self.documentos_existentes)
    
    def mostrar_documentos_existentes(self, documentos):
        """Muestra la lista de documentos existentes"""
        # Limpiar lista
        for widget in self.lista_existentes_frame.winfo_children():
            widget.destroy()
        
        if not documentos:
            self.lbl_sin_existentes = ctk.CTkLabel(
                self.lista_existentes_frame,
                text="No se encontraron documentos",
                text_color="orange",
                font=ctk.CTkFont(size=14)
            )
            self.lbl_sin_existentes.pack(pady=50)
            return
        
        for doc in documentos:
            # Formato: id, nombre_archivo, ruta_archivo, fecha_carga, nombre_completo, dpi
            doc[0]
            nombre_archivo = doc[1]
            ruta_archivo = doc[2]
            fecha_carga = doc[3]
            nombre_persona = doc[4] if doc[4] else "Desconocido"
            dpi_persona = doc[5] if doc[5] else "N/A"
            
            frame_doc = ctk.CTkFrame(self.lista_existentes_frame)
            frame_doc.pack(pady=5, padx=10, fill="x")
            
            # Información del documento
            info_text = f"📄 {nombre_archivo}\n👤 {nombre_persona}\n📋 DPI: {dpi_persona}\n📅 {fecha_carga}"
            
            ctk.CTkLabel(
                frame_doc,
                text=info_text,
                anchor="w",
                justify="left",
                font=ctk.CTkFont(size=11)
            ).pack(side="left", padx=10, pady=10, expand=True, fill="x")
            
            btn_ver = ctk.CTkButton(
                frame_doc,
                text="👁️ Ver",
                command=lambda r=ruta_archivo: self.ver_documento_existente(r),
                width=80,
                fg_color=COLOR_PRIMARY,
                hover_color="#2980b9"
            )
            btn_ver.pack(side="right", padx=5)
    
    def filtrar_documentos_existentes(self):
        """Filtra los documentos existentes según el texto de búsqueda"""
        texto_busqueda = self.entry_buscar.get().strip().lower()
        
        if not texto_busqueda:
            self.mostrar_documentos_existentes(self.documentos_existentes)
            return
        
        # Filtrar documentos
        documentos_filtrados = []
        for doc in self.documentos_existentes:
            nombre_archivo = doc[1].lower()
            nombre_persona = doc[4].lower() if doc[4] else ""
            dpi_persona = doc[5].lower() if doc[5] else ""
            
            # Buscar en nombre de archivo, nombre de persona o DPI
            if (texto_busqueda in nombre_archivo or
                texto_busqueda in nombre_persona or
                texto_busqueda in dpi_persona):
                documentos_filtrados.append(doc)
        
        self.mostrar_documentos_existentes(documentos_filtrados)
    
    def ver_documento_existente(self, ruta_archivo):
        """Visualiza un documento existente"""
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
    
    def seleccionar_documentos(self):
        """Permite seleccionar múltiples documentos"""
        archivos = filedialog.askopenfilenames(
            title="Seleccionar documentos Word",
            filetypes=[("Documentos Word", "*.doc *.docx")]
        )
        
        if not archivos:
            return
        
        self.documentos_seleccionados = list(archivos)
        self.documento_actual_index = 0
        
        # Cambiar a la pestaña de nuevos
        self.tabview.set("📤 Nuevos")
        
        self.actualizar_lista_documentos()
        self.actualizar_navegacion()
        
        if self.documentos_seleccionados:
            self.mostrar_documento_actual()
    
    def actualizar_lista_documentos(self):
        """Actualiza la lista de documentos en el panel izquierdo"""
        # Limpiar lista
        for widget in self.lista_frame.winfo_children():
            widget.destroy()
        
        if not self.documentos_seleccionados:
            self.lbl_lista_vacia = ctk.CTkLabel(
                self.lista_frame,
                text="No hay documentos seleccionados",
                text_color="gray",
                font=ctk.CTkFont(size=14)
            )
            self.lbl_lista_vacia.pack(pady=50)
            return
        
        # Mostrar documentos
        for i, archivo in enumerate(self.documentos_seleccionados):
            nombre_archivo = os.path.basename(archivo)
            
            frame_item = ctk.CTkFrame(self.lista_frame)
            frame_item.pack(pady=5, padx=10, fill="x")
            
            # Resaltar documento actual
            if i == self.documento_actual_index:
                frame_item.configure(fg_color=COLOR_SUCCESS)
            
            ctk.CTkLabel(
                frame_item,
                text=f"{i + 1}. {nombre_archivo}",
                anchor="w",
                font=ctk.CTkFont(size=12)
            ).pack(side="left", padx=10, pady=5, expand=True, fill="x")
            
            btn_ver = ctk.CTkButton(
                frame_item,
                text="👁️",
                command=lambda idx=i: self.ver_documento(idx),
                width=40
            )
            btn_ver.pack(side="right", padx=5)
    
    def actualizar_navegacion(self):
        """Actualiza los controles de navegación"""
        total = len(self.documentos_seleccionados)
        
        if total == 0:
            self.lbl_contador.configure(text="0 / 0")
            self.btn_anterior.configure(state="disabled")
            self.btn_siguiente.configure(state="disabled")
            return
        
        self.lbl_contador.configure(text=f"{self.documento_actual_index + 1} / {total}")
        
        # Habilitar/deshabilitar botones
        if self.documento_actual_index > 0:
            self.btn_anterior.configure(state="normal")
        else:
            self.btn_anterior.configure(state="disabled")
        
        if self.documento_actual_index < total - 1:
            self.btn_siguiente.configure(state="normal")
        else:
            self.btn_siguiente.configure(state="disabled")
    
    def documento_anterior(self):
        """Muestra el documento anterior"""
        if self.documento_actual_index > 0:
            self.documento_actual_index -= 1
            self.mostrar_documento_actual()
            self.actualizar_lista_documentos()
            self.actualizar_navegacion()
    
    def documento_siguiente(self):
        """Muestra el documento siguiente"""
        if self.documento_actual_index < len(self.documentos_seleccionados) - 1:
            self.documento_actual_index += 1
            self.mostrar_documento_actual()
            self.actualizar_lista_documentos()
            self.actualizar_navegacion()
    
    def ver_documento(self, index):
        """Muestra un documento específico"""
        self.documento_actual_index = index
        self.mostrar_documento_actual()
        self.actualizar_lista_documentos()
        self.actualizar_navegacion()
    
    def mostrar_documento_actual(self):
        """Muestra el documento actual en el visor"""
        if not self.documentos_seleccionados:
            return
        
        archivo = self.documentos_seleccionados[self.documento_actual_index]
        
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
            # Convertir .doc a .docx si es necesario
            if archivo.lower().endswith('.doc'):
                archivo_docx = convertir_doc_a_docx(archivo)
                if not archivo_docx:
                    raise Exception("No se pudo convertir el archivo .doc")
            else:
                archivo_docx = archivo
            
            # Convertir a PDF temporal para visualización
            temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_pdf.close()
            
            convert(archivo_docx, temp_pdf.name)
            
            # Mostrar PDF
            self.mostrar_pdf_en_visor(temp_pdf.name)
            
            # Limpiar archivos temporales
            os.unlink(temp_pdf.name)
            if archivo.lower().endswith('.doc') and archivo_docx != archivo:
                os.unlink(archivo_docx)
        
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
    
    def procesar_todos_documentos(self):
        """Procesa y carga todos los documentos a la base de datos"""
        if not self.documentos_seleccionados:
            messagebox.showwarning("Advertencia", "No hay documentos seleccionados")
            return
        
        respuesta = messagebox.askyesno(
            "Confirmar",
            f"¿Desea procesar y cargar {len(self.documentos_seleccionados)} documento(s) a la base de datos?"
        )
        
        if not respuesta:
            return
        
        # Crear ventana de progreso
        ventana_progreso = ctk.CTkToplevel(self)
        ventana_progreso.title("Procesando documentos...")
        ventana_progreso.geometry("700x500")
        ventana_progreso.grab_set()
        
        ctk.CTkLabel(
            ventana_progreso,
            text="⚙️ Procesando documentos...",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=20)
        
        progreso_label = ctk.CTkLabel(
            ventana_progreso,
            text="0 / 0",
            font=ctk.CTkFont(size=14)
        )
        progreso_label.pack(pady=10)
        
        log_text = ctk.CTkTextbox(ventana_progreso, width=650, height=350)
        log_text.pack(pady=10, padx=20)
        
        btn_cerrar = ctk.CTkButton(
            ventana_progreso,
            text="Cerrar",
            command=ventana_progreso.destroy,
            state="disabled"
        )
        btn_cerrar.pack(pady=10)
        
        self.ventana.update()
        
        importados = 0
        errores = 0
        actualizados = 0
        
        for i, archivo in enumerate(self.documentos_seleccionados):
            try:
                progreso_label.configure(text=f"Procesando {i + 1} / {len(self.documentos_seleccionados)}")
                self.ventana.update()
                
                nombre_archivo = os.path.basename(archivo)
                log_text.insert("end", f"\n📄 Procesando: {nombre_archivo}\n")
                log_text.see("end")
                self.ventana.update()
                
                # Convertir .doc a .docx si es necesario
                if archivo.lower().endswith('.doc'):
                    log_text.insert("end", "   Convirtiendo .doc a .docx...\n")
                    log_text.see("end")
                    self.ventana.update()
                    
                    archivo_docx = convertir_doc_a_docx(archivo)
                    if not archivo_docx:
                        raise Exception("No se pudo convertir el archivo .doc")
                else:
                    archivo_docx = archivo
                
                # Extraer datos del documento
                log_text.insert("end", "   Extrayendo datos...\n")
                log_text.see("end")
                self.ventana.update()
                
                datos = DocumentExtractor.extraer_datos(archivo_docx)
                
                if not datos or not datos.get('dpi'):
                    raise Exception("No se pudo extraer el DPI del documento")
                
                # Copiar documento a carpeta de documentos
                nombre_destino = f"{datos.get('dpi', 'sin_dpi').replace(' ', '_')}_acta_{datos.get('nombre', 'sin_nombre').replace(' ', '_')}.docx"
                ruta_destino = os.path.join(DOCUMENTOS_DIR, nombre_destino)
                
                # Si es .doc convertido, copiar el .docx
                if archivo.lower().endswith('.doc'):
                    shutil.copy2(archivo_docx, ruta_destino)
                else:
                    shutil.copy2(archivo, ruta_destino)
                
                # Guardar persona en la base de datos
                log_text.insert("end", f"   Guardando: {datos.get('nombre', 'Sin nombre')}\n")
                log_text.see("end")
                self.ventana.update()
                
                # Asegurar que todos los campos estén presentes
                datos_persona = {
                    'nombre': datos.get('nombre', ''),
                    'dpi': datos.get('dpi', ''),
                    'edad': datos.get('edad'),
                    'estado_civil': datos.get('estado_civil', ''),
                    'nacionalidad': datos.get('nacionalidad', ''),
                    'domicilio': datos.get('domicilio', ''),
                    'nivel_academico': datos.get('nivel_academico', ''),
                    'apellido_casada': datos.get('apellido_casada', '')
                }
                
                persona_id, resultado = self.db.guardar_persona(datos_persona)
                
                # Guardar documento en la base de datos
                self.db.guardar_documento(persona_id, nombre_destino, ruta_destino, "acta")
                
                if resultado == "guardado":
                    log_text.insert("end", "   ✅ Importado correctamente\n", "success")
                    importados += 1
                elif resultado == "actualizado":
                    log_text.insert("end", "   ✅ Actualizado (ya existía)\n", "success")
                    actualizados += 1
                
                # Limpiar archivo temporal si se convirtió
                if archivo.lower().endswith('.doc') and archivo_docx != archivo:
                    try:
                        os.unlink(archivo_docx)
                    except:  # noqa: E722
                        pass
                
            except Exception as e:
                errores += 1
                log_text.insert("end", f"   ❌ Error: {str(e)}\n", "error")
                log_text.see("end")
        
        # Resumen final
        log_text.insert("end", f"\n{'='*50}\n")
        log_text.insert("end", "📊 RESUMEN DE IMPORTACIÓN\n")
        log_text.insert("end", f"{'='*50}\n")
        log_text.insert("end", f"✅ Nuevos importados: {importados}\n", "success")
        log_text.insert("end", f"🔄 Actualizados: {actualizados}\n", "success")
        log_text.insert("end", f"❌ Errores: {errores}\n", "error")
        log_text.insert("end", f"📁 Total procesados: {len(self.documentos_seleccionados)}\n")
        log_text.see("end")
        
        # Configurar colores para el texto
        log_text.tag_config("success", foreground="#2ecc71")
        log_text.tag_config("error", foreground="#e74c3c")
        
        btn_cerrar.configure(state="normal")
        
        messagebox.showinfo(
            "Importación completada",
            f"✅ Nuevos: {importados}\n"
            f"🔄 Actualizados: {actualizados}\n"
            f"❌ Errores: {errores}\n\n"
            f"Total procesados: {len(self.documentos_seleccionados)}"
        )
        
        # Recargar documentos existentes
        self.cargar_documentos_existentes()
        if self.callback_actualizar:
            self.callback_actualizar()
        
        # Cambiar a la pestaña de documentos cargados
        self.tabview.set("📚 Cargados")
        
        # Limpiar lista de nuevos documentos
        self.documentos_seleccionados = []
        self.actualizar_lista_documentos()
        self.actualizar_navegacion()