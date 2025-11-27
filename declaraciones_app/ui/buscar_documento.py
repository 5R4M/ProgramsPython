import customtkinter as ctk
from tkinter import messagebox
import os
from PIL import Image, ImageTk
import fitz  # PyMuPDF
import tempfile
from docx2pdf import convert
from config import COLOR_SUCCESS
from models import Persona

class VentanaBuscarDocumento:
    def __init__(self, parent, db, es_integrado=False):
        self.db = db
        self.es_integrado = es_integrado
        self.callback_actualizar = None
        self.persona_seleccionada = None
        self.documentos_persona = []
        self.documento_actual_index = 0
        
        if es_integrado:
            # Crear como Frame integrado
            self.ventana = ctk.CTkFrame(parent)
            self.ventana.pack(fill="both", expand=True)
        else:
            # Crear como ventana separada (Toplevel)
            self.ventana = ctk.CTkToplevel(parent)
            self.ventana.title("🔍 Buscar Documento")
            self.center_window()
            self.ventana.after(100, self.maximizar_ventana)
        
        self.crear_interfaz()
    
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
        
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)
        
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
        
        # Frame de resultados
        ctk.CTkLabel(
            panel_izquierdo,
            text="Resultados de búsqueda:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 10), padx=20, anchor="w")
        
        self.resultados_frame = ctk.CTkScrollableFrame(panel_izquierdo, height=300)
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
        
        self.documentos_frame = ctk.CTkScrollableFrame(panel_izquierdo, height=200)
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
        
        resultados = self.db.buscar_persona_por_nombre(nombre)
        
        if resultados:
            self.mostrar_resultados(resultados)
        else:
            self.mostrar_sin_resultados()
            messagebox.showinfo(
                "No encontrado",
                "No se encontraron personas con ese nombre.\n\n"
                "Puede crear un nuevo documento desde el menú principal."
            )
    
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
            
            btn_seleccionar = ctk.CTkButton(
                frame_resultado,
                text="Seleccionar",
                command=lambda p=persona: self.seleccionar_persona(p),
                width=120,
                fg_color=COLOR_SUCCESS,
                hover_color="#27ae60"
            )
            btn_seleccionar.pack(side="right", padx=10)
    
    def seleccionar_persona(self, persona):
        """Selecciona una persona y muestra su información"""
        self.persona_seleccionada = persona
        
        # Mostrar información detallada
        self.mostrar_info_persona()
        
        # Cargar documentos de la persona
        self.cargar_documentos_persona()
    
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
    
    def cargar_documentos_persona(self):
        """Carga los documentos de la persona seleccionada"""
        # Limpiar frame de documentos
        for widget in self.documentos_frame.winfo_children():
            widget.destroy()
        
        # Obtener documentos
        self.documentos_persona = self.db.obtener_documentos_persona(self.persona_seleccionada.id)
        
        if not self.documentos_persona:
            self.lbl_sin_documentos = ctk.CTkLabel(
                self.documentos_frame,
                text="Esta persona no tiene documentos cargados",
                text_color="orange",
                font=ctk.CTkFont(size=12)
            )
            self.lbl_sin_documentos.pack(pady=30)
            return
        
        # Mostrar documentos
        for i, doc in enumerate(self.documentos_persona):
            doc_id, nombre_archivo, ruta_archivo, fecha_carga, tipo_documento = doc
            
            frame_doc = ctk.CTkFrame(self.documentos_frame)
            frame_doc.pack(pady=5, padx=10, fill="x")
            
            info_doc = f"📄 {nombre_archivo}\n📅 {fecha_carga}"
            
            ctk.CTkLabel(
                frame_doc,
                text=info_doc,
                anchor="w",
                justify="left",
                font=ctk.CTkFont(size=11)
            ).pack(side="left", padx=10, pady=5, expand=True, fill="x")
            
            btn_ver = ctk.CTkButton(
                frame_doc,
                text="👁️ Ver",
                command=lambda idx=i: self.ver_documento(idx),
                width=80
            )
            btn_ver.pack(side="right", padx=5)
    
    def ver_documento(self, index):
        """Muestra un documento en el visor"""
        if not self.documentos_persona or index >= len(self.documentos_persona):
            return
        
        doc = self.documentos_persona[index]
        doc_id, nombre_archivo, ruta_archivo, fecha_carga, tipo_documento = doc
        
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