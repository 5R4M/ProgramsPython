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
import time
from .crear_documento import VentanaCrearDocumento
import datetime

class VentanaCargarDocumentos:
    def __init__(self, parent, db, es_integrado=False):
        self.db = db
        self.es_integrado = es_integrado
        self.callback_actualizar = None
        self.documentos_seleccionados = []
        self.documento_actual_index = 0
        
        # Asegurar que existe el directorio de documentos (sin print)
        if not os.path.exists(DOCUMENTOS_DIR):
            os.makedirs(DOCUMENTOS_DIR, exist_ok=True)
        
        if es_integrado:
            # Crear como Frame integrado
            self.ventana = ctk.CTkFrame(parent)
            self.ventana.pack(fill="both", expand=True)
        else:
            # Crear como ventana separada (Toplevel)
            self.ventana = ctk.CTkToplevel(parent)
            self.ventana.title("📥 Cargar Documentos a la Base de Datos")

            # Asociar al padre, traer al frente y bloquearlo
            self.ventana.transient(parent)
            self.ventana.lift()
            self.ventana.focus_force()
            self.ventana.grab_set()   # bloquea interacciones con el padre

        # Crear UI
        self.crear_interfaz()
        self.cargar_documentos_existentes()
        self.verificar_personas_sin_documento()

        # IMPORTANTE: centrar DESPUÉS de crear la interfaz
        if not self.es_integrado:
            self.center_window()
            # Recentrar una vez que todo terminó de dibujarse
            self.ventana.after(50, self.center_window)
    
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
            # Tamaño inicial razonable
            self.ventana.geometry("1400x900")
            self.ventana.update_idletasks()

            width = self.ventana.winfo_width()
            height = self.ventana.winfo_height()
            x = (self.ventana.winfo_screenwidth() // 2) - (width // 2)
            y = (self.ventana.winfo_screenheight() // 2) - (height // 2)

            self.ventana.geometry(f"{width}x{height}+{x}+{y}")
    
    def center_toplevel(self, win, w=400, h=200):
        """Centra una ventana CTkToplevel en la pantalla."""
        win.update_idletasks()

        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()

        x = (screen_width // 2) - (w // 2)
        y = (screen_height // 2) - (h // 2)

        win.geometry(f"{w}x{h}+{x}+{y}")
    
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
        """Carga documentos existentes basados en los archivos de la carpeta.
        Ordena por fecha de modificación (más reciente primero) y guarda mtime.
        """
        # Limpiar lista visual
        for widget in self.lista_existentes_frame.winfo_children():
            widget.destroy()

        # Archivos físicos en la carpeta
        archivos_carpeta = []
        if os.path.exists(DOCUMENTOS_DIR):
            archivos_carpeta = [
                f for f in os.listdir(DOCUMENTOS_DIR)
                if f.lower().endswith(('.doc', '.docx'))
            ]

        # Obtener todos los documentos de la BD
        documentos_bd = self.db.obtener_todos_documentos()

        # Mapa por nombre_archivo -> fila de BD (si existe)
        mapa_doc_por_nombre = {}
        for doc in documentos_bd:
            # Formato esperado:
            # (id, nombre_archivo, ruta_archivo, fecha_carga, nombre_persona, dpi, persona_id)
            nombre_archivo = doc[1]
            mapa_doc_por_nombre[nombre_archivo] = doc

        # Lista de (doc_con_mtime, mtime)
        docs_con_mtime = []

        for nombre_archivo in archivos_carpeta:
            ruta_archivo = os.path.join(DOCUMENTOS_DIR, nombre_archivo)

            if nombre_archivo in mapa_doc_por_nombre:
                doc = mapa_doc_por_nombre[nombre_archivo]
            else:
                # Si no existe en BD, construimos una fila mínima:
                doc = (
                    None,                 # id_documento
                    nombre_archivo,       # nombre_archivo
                    ruta_archivo,         # ruta_archivo
                    "",                   # fecha_carga (BD)
                    "Desconocido",        # nombre_persona
                    "N/A",                # dpi
                    None                  # persona_id
                )

            # Obtener fecha de modificación del archivo
            try:
                mtime = os.path.getmtime(ruta_archivo)
            except OSError:
                mtime = 0  # si falla, que aparezca al final

            # Extendemos la tupla doc añadiendo mtime como último campo
            doc_con_mtime = doc + (mtime,)
            docs_con_mtime.append((doc_con_mtime, mtime))

        # Ordenar por mtime descendente (más reciente primero)
        docs_con_mtime.sort(key=lambda x: x[1], reverse=True)

        # Guardar solo la parte doc (ya con mtime dentro)
        self.documentos_existentes = [item[0] for item in docs_con_mtime]

        # Encabezado con contador
        header_frame = ctk.CTkFrame(self.lista_existentes_frame, fg_color="transparent")
        header_frame.pack(pady=10, padx=10, fill="x")

        contador_text = (
            f"📊 Documentos mostrados: {len(self.documentos_existentes)} "
            f"| 📁 Archivos en carpeta: {len(archivos_carpeta)} "
            f"(Ordenados por fecha de modificación, más reciente primero)"
        )
        ctk.CTkLabel(
            header_frame,
            text=contador_text,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#3498db"
        ).pack(pady=5)

        if not self.documentos_existentes:
            self.lbl_sin_existentes = ctk.CTkLabel(
                self.lista_existentes_frame,
                text="No hay documentos en la carpeta de documentos.",
                text_color="gray",
                font=ctk.CTkFont(size=14)
            )
            self.lbl_sin_existentes.pack(pady=50)
            return

        self.mostrar_documentos_existentes(self.documentos_existentes)
            
    def mostrar_documentos_existentes(self, documentos):
        """Muestra la lista de documentos existentes (solo filas, sin limpiar el header)."""
        # Limpiar SOLO los items existentes debajo del header,
        # manteniendo el primer frame (header_frame) si existe.
        children = self.lista_existentes_frame.winfo_children()
        start_idx = 1 if children else 0
        for widget in children[start_idx:]:
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
            # doc: (id, nombre_archivo, ruta_archivo, fecha_carga, nombre_persona, dpi, persona_id, mtime)
            doc_id = doc[0]
            nombre_archivo = doc[1]
            ruta_archivo = doc[2]
            fecha_carga_bd = doc[3]
            nombre_persona = doc[4] if doc[4] else "Desconocido"
            dpi_persona = doc[5] if doc[5] else "N/A"
            mtime = doc[7] if len(doc) > 7 else 0

            # Convertir mtime a texto amigable
            if mtime:
                dt = datetime.datetime.fromtimestamp(mtime)
                fecha_mod_str = dt.strftime("%Y-%m-%d %H:%M")
            else:
                fecha_mod_str = "Desconocida"

            frame_doc = ctk.CTkFrame(self.lista_existentes_frame)
            frame_doc.pack(pady=5, padx=10, fill="x")

            info_text = (
                f"📄 {nombre_archivo}\n"
                f"👤 {nombre_persona}\n"
                f"📋 DPI: {dpi_persona}\n"
                f"📅 BD: {fecha_carga_bd}\n"
                f"🕒 Última modificación: {fecha_mod_str}"
            )

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

            btn_eliminar = ctk.CTkButton(
                frame_doc,
                text="🗑 Eliminar",
                command=lambda i=doc_id, r=ruta_archivo, n=nombre_archivo: self.eliminar_documento_existente(i, r, n),
                width=90,
                fg_color="#e74c3c",
                hover_color="#c0392b"
            )
            btn_eliminar.pack(side="right", padx=5)
        
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
        
        pdf_document = None
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
            
        except Exception as e:
            self.lbl_visor_estado = ctk.CTkLabel(
                self.visor_scroll,
                text=f"Error al mostrar PDF:\n{str(e)}",
                text_color="red"
            )
            self.lbl_visor_estado.pack(pady=20)
        
        finally:
            # Cerrar el documento PDF
            if pdf_document:
                pdf_document.close()
    
    def procesar_todos_documentos(self):
        """Procesa y carga todos los documentos a la base de datos (versión simple, sin log detallado)."""
        if not self.documentos_seleccionados:
            messagebox.showwarning("Advertencia", "No hay documentos seleccionados")
            return
        
        # Verificar documentos duplicados
        duplicados = []
        for archivo in self.documentos_seleccionados:
            nombre_archivo = os.path.basename(archivo)
            
            # Extraer DPI temporal para verificar
            try:
                archivo_temp = archivo
                if archivo.lower().endswith('.doc'):
                    archivo_temp = convertir_doc_a_docx(archivo)
                
                datos_temp = DocumentExtractor.extraer_datos(archivo_temp)
                dpi = datos_temp.get('dpi', '')
                
                # Verificar si ya existe en la BD
                existe = self.db.verificar_dpi_existe(dpi)
                if existe:
                    duplicados.append((nombre_archivo, dpi))
                
                # Limpiar archivo temporal
                if archivo.lower().endswith('.doc') and archivo_temp != archivo:
                    try:
                        os.unlink(archivo_temp)
                    except:  # noqa: E722
                        pass
            except:  # noqa: E722
                pass
        
        # Mostrar advertencia de duplicados
        if duplicados:
            mensaje = "Se encontraron documentos con DPIs ya existentes:\n\n"
            for nombre, dpi in duplicados[:5]:
                mensaje += f"• {nombre} (DPI: {dpi})\n"
            if len(duplicados) > 5:
                mensaje += f"\n... y {len(duplicados) - 5} más.\n"
            mensaje += "\n¿Desea reemplazar la información existente?"
            
            respuesta = messagebox.askyesnocancel(
                "Documentos Duplicados",
                mensaje,
                icon='warning'
            )
            
            if respuesta is None:
                return
        
        respuesta = messagebox.askyesno(
            "Confirmar",
            f"¿Desea procesar y cargar {len(self.documentos_seleccionados)} documento(s) a la base de datos?"
        )
        
        if not respuesta:
            return
        
        # Crear ventana de progreso SIMPLE
        ventana_progreso = ctk.CTkToplevel(self.ventana)
        ventana_progreso.title("Procesando documentos...")
        ventana_progreso.grab_set()
        self.center_toplevel(ventana_progreso, 400, 200)

        ctk.CTkLabel(
            ventana_progreso,
            text="⚙️ Procesando documentos...",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)

        progreso_label = ctk.CTkLabel(
            ventana_progreso,
            text="0 / 0 | Éxito: 0",
            font=ctk.CTkFont(size=13)
        )
        progreso_label.pack(pady=5)

        barra = ctk.CTkProgressBar(ventana_progreso)
        barra.pack(pady=5, padx=20, fill="x")
        barra.set(0)

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

        total_docs = len(self.documentos_seleccionados)
        
        for i, archivo in enumerate(self.documentos_seleccionados):
            archivo_docx = None
            
            try:
                # Actualizar progreso visual
                progreso_label.configure(
                    text=f"Procesando {i + 1} / {total_docs} | Éxito: {importados + actualizados}"
                )
                barra.set((i + 1) / total_docs)
                ventana_progreso.update_idletasks()

                nombre_archivo = os.path.basename(archivo)
                
                # Convertir .doc a .docx si es necesario
                if archivo.lower().endswith('.doc'):
                    archivo_docx = convertir_doc_a_docx(archivo)
                    if not archivo_docx:
                        raise Exception("No se pudo convertir el archivo .doc")
                else:
                    archivo_docx = archivo
                
                # Extraer datos del documento
                datos = DocumentExtractor.extraer_datos(archivo_docx)
                
                if not datos or not datos.get('dpi'):
                    raise Exception("No se pudo extraer el DPI del documento")
                
                # Asegurar que existe la carpeta de documentos
                if not os.path.exists(DOCUMENTOS_DIR):
                    os.makedirs(DOCUMENTOS_DIR, exist_ok=True)
                
                # Verificar que el archivo fuente existe
                archivo_fuente = archivo_docx if archivo.lower().endswith('.doc') else archivo
                if not os.path.exists(archivo_fuente):
                    raise Exception(f"Archivo fuente no encontrado: {archivo_fuente}")
                
                # Copiar documento a carpeta de documentos
                dpi_limpio = datos.get('dpi', 'sin_dpi').replace(' ', '').replace('_', '')
                nombre_limpio = datos.get('nombre', 'sin_nombre').replace(' ', '_')
                
                nombre_destino = f"{dpi_limpio}_acta_{nombre_limpio}.docx"
                ruta_destino = os.path.join(DOCUMENTOS_DIR, nombre_destino)
                
                # Cerrar cualquier archivo abierto y esperar
                time.sleep(0.1)
                
                # Si existe el archivo destino, eliminarlo primero
                if os.path.exists(ruta_destino):
                    try:
                        os.remove(ruta_destino)
                        time.sleep(0.1)
                    except PermissionError:
                        time.sleep(0.5)
                        try:
                            os.remove(ruta_destino)
                        except:  # noqa: E722
                            pass
                
                # Copiar el archivo
                try:
                    shutil.copy2(archivo_fuente, ruta_destino)
                except Exception as copy_error:
                    raise Exception(f"Error al copiar archivo: {copy_error}")
                
                # Guardar persona en la base de datos
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
                    importados += 1
                elif resultado == "actualizado":
                    actualizados += 1
                
            except Exception:
                errores += 1
            
            finally:
                # Limpiar archivos temporales
                if archivo.lower().endswith('.doc') and archivo_docx and archivo_docx != archivo:
                    try:
                        time.sleep(0.1)
                        if os.path.exists(archivo_docx):
                            os.unlink(archivo_docx)
                    except:  # noqa: E722
                        pass
            
            # Pequeña pausa entre documentos
            time.sleep(0.05)
        
        # Habilitar botón cerrar
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
    
    def eliminar_documento_existente(self, doc_id, ruta_archivo, nombre_archivo):
        """
        Elimina un documento de la BD y del sistema de archivos,
        y opcionalmente también a la persona asociada.
        """
        # Buscar la fila completa del documento para obtener persona_id y datos de la persona
        persona_id = None
        nombre_persona = "Desconocido"
        dpi_persona = "N/A"

        for doc in self.documentos_existentes:
            # doc: (id_documento, nombre_archivo, ruta_archivo, fecha_carga, nombre_persona, dpi, persona_id)
            if doc[0] == doc_id:
                nombre_persona = doc[4] if doc[4] else "Desconocido"
                dpi_persona = doc[5] if doc[5] else "N/A"
                persona_id = doc[6] if len(doc) > 6 else None
                break

        # 1) Confirmar eliminación del documento
        mensaje_doc = (
            f"¿Está seguro de eliminar el documento?\n\n"
            f"📄 {nombre_archivo}\n\n"
            f"👤 {nombre_persona}\n"
            f"📋 DPI: {dpi_persona}"
        )

        resp_doc = messagebox.askyesno(
            "Confirmar eliminación de documento",
            mensaje_doc,
            icon='warning'
        )
        if not resp_doc:
            return

        # Eliminar archivo físico
        try:
            if ruta_archivo and os.path.exists(ruta_archivo):
                os.remove(ruta_archivo)
        except Exception as e:
            messagebox.showwarning(
                "Advertencia",
                f"No se pudo eliminar el archivo físico:\n{str(e)}"
            )

        # Eliminar registro del documento en BD
        try:
            self.db.eliminar_documento_por_id(doc_id)
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo eliminar el registro del documento en la base de datos:\n{str(e)}"
            )
            return

        # 2) Si no hay persona asociada, terminamos aquí
        if not persona_id:
            messagebox.showinfo("Éxito", "Documento eliminado correctamente.")
            self.cargar_documentos_existentes()
            if self.callback_actualizar:
                self.callback_actualizar()
            return

        # 3) Preguntar si también desea eliminar a la persona de la base de datos
        mensaje_persona = (
            f"El documento estaba asociado a la siguiente persona:\n\n"
            f"👤 {nombre_persona}\n"
            f"📋 DPI: {dpi_persona}\n\n"
            f"¿Desea eliminar TAMBIÉN a esta persona de la base de datos?"
        )

        resp_persona = messagebox.askyesno(
            "Eliminar persona asociada",
            mensaje_persona,
            icon='warning'
        )

        if resp_persona:
            try:
                self.db.eliminar_persona_por_id(persona_id)
                messagebox.showinfo(
                    "Éxito",
                    "Documento y persona asociada eliminados correctamente."
                )
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"El documento se eliminó, pero no se pudo eliminar a la persona:\n{str(e)}"
                )
        else:
            messagebox.showinfo(
                "Éxito",
                "Documento eliminado.\n"
                "La persona asociada se mantiene en la base de datos."
            )

        # 4) Recargar lista y estadísticas
        self.cargar_documentos_existentes()
        if self.callback_actualizar:
            self.callback_actualizar()
        
    def verificar_personas_sin_documento(self):
        """
        Verifica qué personas en la BD no tienen documento en la carpeta
        (coincidiendo con lo que se muestra en '📚 Cargados').
        Solo muestra mensaje si realmente hay personas sin documento.
        """
        # Obtener todas las personas
        try:
            personas = self.db.obtener_todas_personas()
        except Exception as e:
            # Si no existe el método o falla, no molestamos al usuario
            print(f"Error al obtener personas: {e}")
            return

        # Personas con documento (por persona_id) según documentos_filtrados
        documentos_bd = self.db.obtener_todos_documentos()

        # Construir set de persona_id que tienen documento válido en carpeta
        personas_con_doc = set()

        # Archivos válidos en carpeta (mismo criterio que cargar_documentos_existentes)
        archivos_carpeta = set()
        if os.path.exists(DOCUMENTOS_DIR):
            archivos_carpeta = {
                f for f in os.listdir(DOCUMENTOS_DIR)
                if f.lower().endswith(('.doc', '.docx'))
            }

        for doc in documentos_bd:
            # Ajusta índices según tu estructura real:
            # Ejemplo asumido: (id, nombre_archivo, ruta_archivo, fecha_carga, nombre_persona, dpi, persona_id)
            nombre_archivo = doc[1]
            ruta_archivo = doc[2]
            persona_id = doc[6] if len(doc) > 6 else None

            if not persona_id:
                continue

            # Validar igual que en cargar_documentos_existentes
            if nombre_archivo not in archivos_carpeta:
                continue
            if not ruta_archivo or not os.path.exists(ruta_archivo):
                continue

            personas_con_doc.add(persona_id)

        # Construir lista de personas sin documento
        personas_sin_doc = []
        for p in personas:
            # Asumo formato: (id, nombre_completo, dpi, edad, estado_civil,
            #                nacionalidad, domicilio, nivel_academico,
            #                apellido_casada, fecha_registro, sexo, fecha_nacimiento)
            persona_id = p[0]

            if persona_id not in personas_con_doc:
                personas_sin_doc.append(p)

        # Si no hay personas sin documento, no mostramos nada
        if not personas_sin_doc:
            return

        # Si hay, preguntar si quiere generar en bloque
        respuesta = messagebox.askyesno(
            "Personas sin documento",
            f"Se encontraron {len(personas_sin_doc)} persona(s) en la base de datos "
            "que no tienen documento en la carpeta.\n\n"
            "¿Desea generar automáticamente los documentos para ellas?"
        )

        if respuesta:
            # Llamar a la función de generación masiva (que ya tienes)
            self.generar_documentos_faltantes(personas_sin_doc)
    
    def generar_documentos_faltantes(self, personas_sin_doc):
        """
        Genera documentos de forma masiva para las personas que no tienen.
        Reutiliza VentanaCrearDocumento.generar_documento_para_persona (con runs/helpers).
        """
        if not personas_sin_doc:
            messagebox.showinfo("Información", "No hay personas sin documento.")
            return

        respuesta = messagebox.askyesno(
            "Confirmar generación masiva",
            f"Se generarán documentos para {len(personas_sin_doc)} persona(s).\n\n¿Desea continuar?"
        )
        if not respuesta:
            return

        import time
        import traceback

        errores = 0
        generados = 0

        ventana_progreso = ctk.CTkToplevel(self.ventana)
        ventana_progreso.title("Generando documentos faltantes...")
        ventana_progreso.geometry("700x500")
        ventana_progreso.grab_set()

        ctk.CTkLabel(
            ventana_progreso,
            text="⚙️ Generando documentos para personas sin documento...",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)

        progreso_label = ctk.CTkLabel(
            ventana_progreso,
            text="0 / 0",
            font=ctk.CTkFont(size=13)
        )
        progreso_label.pack(pady=5)

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

        for i, persona in enumerate(personas_sin_doc):
            # persona: (id, nombre_completo, dpi, edad, estado_civil, nacionalidad, domicilio,
            #           nivel_academico, apellido_casada, fecha_registro, sexo, fecha_nacimiento)
            try:
                progreso_label.configure(text=f"Procesando {i + 1} / {len(personas_sin_doc)}")
                self.ventana.update()

                persona_id = persona[0]
                nombre = persona[1] or ""
                dpi = persona[2] or ""
                edad = persona[3]
                estado_civil = persona[4] or ""
                nacionalidad = persona[5] or ""
                domicilio = persona[6] or ""
                nivel_academico = persona[7] or ""
                apellido_casada = persona[8] or ""
                sexo = persona[10] or "masculino"
                fecha_nacimiento = persona[11] or ""

                log_text.insert("end", f"\n👤 {nombre} | DPI: {dpi}\n")
                log_text.see("end")
                self.ventana.update()

                datos_persona = {
                    'nombre': nombre,
                    'sexo': sexo,
                    'fecha_nacimiento': fecha_nacimiento,
                    'edad': edad,
                    'estado_civil': estado_civil,
                    'apellido_casada': apellido_casada,
                    'nacionalidad': nacionalidad,
                    'nivel_academico': nivel_academico,
                    'domicilio': domicilio,
                    'dpi': dpi,
                    'hora': '17',
                    'minutos': '20',
                    'dia': '28',
                    'mes': 'noviembre',
                    'anio': '2025',
                }

                dpi_limpio = dpi.replace(' ', '').replace('_', '') if dpi else 'sin_dpi'
                nombre_limpio = nombre.replace(' ', '_') if nombre else 'sin_nombre'
                nombre_destino = f"{dpi_limpio}_acta_{nombre_limpio}.docx"
                ruta_destino = os.path.join(DOCUMENTOS_DIR, nombre_destino)

                if os.path.exists(ruta_destino):
                    try:
                        os.remove(ruta_destino)
                    except Exception:
                        pass

                # AQUÍ se reutilizan runs/helpers internos
                VentanaCrearDocumento.generar_documento_para_persona(
                    self.db,
                    datos_persona,
                    ruta_destino
                )

                self.db.guardar_documento(persona_id, nombre_destino, ruta_destino, "acta")

                generados += 1
                log_text.insert("end", f"   ✅ Documento generado: {nombre_destino}\n", "success")
                log_text.see("end")
                self.ventana.update()

            except Exception as e:
                errores += 1
                log_text.insert("end", f"   ❌ Error: {str(e)}\n", "error")
                log_text.insert("end", traceback.format_exc() + "\n")
                log_text.see("end")

            time.sleep(0.1)

        log_text.insert("end", f"\n{'='*50}\n")
        log_text.insert("end", "📊 RESUMEN GENERACIÓN MASIVA\n")
        log_text.insert("end", f"{'='*50}\n")
        log_text.insert("end", f"✅ Generados: {generados}\n", "success")
        log_text.insert("end", f"❌ Errores: {errores}\n", "error")
        log_text.insert("end", f"Total personas procesadas: {len(personas_sin_doc)}\n")
        log_text.see("end")

        log_text.tag_config("success", foreground="#2ecc71")
        log_text.tag_config("error", foreground="#e74c3c")

        btn_cerrar.configure(state="normal")

        messagebox.showinfo(
            "Proceso terminado",
            f"✅ Generados: {generados}\n"
            f"❌ Errores: {errores}\n\n"
            f"Total procesadas: {len(personas_sin_doc)}"
        )

        self.cargar_documentos_existentes()
        if self.callback_actualizar:
            self.callback_actualizar()