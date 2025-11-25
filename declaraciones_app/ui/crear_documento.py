import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import shutil
import tempfile
from docx import Document
from datetime import datetime
from PIL import Image, ImageTk
import fitz  # PyMuPDF
from docx2pdf import convert
from config import PLANTILLAS_DIR, COLOR_SUCCESS, COLOR_PRIMARY, COLOR_WARNING
from utils import NumeroATexto

class VentanaCrearDocumento(ctk.CTkToplevel):
    def __init__(self, parent, db):
        super().__init__(parent)
        
        self.db = db
        self.persona_actual_id = None
        self.documento_preview = None
        
        self.title("➕ Crear Nuevo Documento")
        
        self.crear_interfaz()
        
        # Centrar y maximizar ventana
        self.center_window()
        self.after(100, self.maximizar_ventana)
        
        self.verificar_plantilla()
    
    def maximizar_ventana(self):
        """Maximiza la ventana"""
        self.state('zoomed')
    
    def center_window(self):
        """Centra la ventana en la pantalla"""
        self.geometry("1400x900")
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def verificar_plantilla(self):
        """Verifica si hay una plantilla activa"""
        plantilla = self.db.obtener_plantilla_activa()
        
        if not plantilla:
            respuesta = messagebox.askyesno(
                "Sin plantilla",
                "No hay ninguna plantilla activa.\n\n"
                "¿Desea cargar una plantilla ahora?"
            )
            
            if respuesta:
                self.cargar_plantilla()
            else:
                self.lbl_plantilla.configure(
                    text="⚠️ No hay plantilla activa",
                    text_color="orange"
                )
        else:
            self.lbl_plantilla.configure(
                text=f"✅ Plantilla activa: {plantilla[1]}",
                text_color="green"
            )
    
    def cargar_plantilla(self):
        """Permite cargar una nueva plantilla"""
        archivo = filedialog.askopenfilename(
            title="Seleccionar plantilla Word",
            filetypes=[("Documento Word", "*.docx")]
        )
        
        if not archivo:
            return
        
        try:
            # Verificar que sea un archivo válido
            _ = Document(archivo)
            
            # Copiar archivo a carpeta de plantillas
            nombre_archivo = os.path.basename(archivo)
            ruta_destino = os.path.join(PLANTILLAS_DIR, nombre_archivo)
            shutil.copy2(archivo, ruta_destino)
            
            # Guardar en base de datos
            self.db.guardar_plantilla(nombre_archivo, ruta_destino, activar=True)
            
            self.lbl_plantilla.configure(
                text=f"✅ Plantilla activa: {nombre_archivo}",
                text_color="green"
            )
            
            messagebox.showinfo(
                "Éxito",
                f"Plantilla '{nombre_archivo}' cargada correctamente."
            )
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo cargar la plantilla:\n{str(e)}"
            )
    
    def crear_interfaz(self):
        """Crea la interfaz de creación de documentos"""
        
        # Frame principal con dos columnas
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)
        
        # ===== PANEL IZQUIERDO: Formulario =====
        panel_izquierdo = ctk.CTkScrollableFrame(container, width=650)
        panel_izquierdo.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Título
        ctk.CTkLabel(
            panel_izquierdo,
            text="➕ Crear Nuevo Documento",
            font=ctk.CTkFont(size=28, weight="bold")
        ).pack(pady=20)
        
        # Estado de plantilla
        self.lbl_plantilla = ctk.CTkLabel(
            panel_izquierdo,
            text="Verificando plantilla...",
            font=ctk.CTkFont(size=14)
        )
        self.lbl_plantilla.pack(pady=10)
        
        btn_cambiar_plantilla = ctk.CTkButton(
            panel_izquierdo,
            text="📋 Cambiar Plantilla",
            command=self.cargar_plantilla,
            width=200
        )
        btn_cambiar_plantilla.pack(pady=5)
        
        # Separador
        ctk.CTkLabel(panel_izquierdo, text="").pack(pady=10)
        
        # ----- Sección de Búsqueda Rápida -----
        frame_busqueda = ctk.CTkFrame(panel_izquierdo)
        frame_busqueda.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(
            frame_busqueda,
            text="🔍 Búsqueda Rápida (Opcional)",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)
        
        ctk.CTkLabel(
            frame_busqueda,
            text="Si la persona ya existe, búsquela por DPI para autocompletar los datos",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(pady=5)
        
        frame_buscar_dpi = ctk.CTkFrame(frame_busqueda)
        frame_buscar_dpi.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(frame_buscar_dpi, text="DPI:", width=100).pack(side="left", padx=5)
        self.entry_buscar_dpi = ctk.CTkEntry(
            frame_buscar_dpi,
            placeholder_text="Ej: 2008 22829 0101"
        )
        self.entry_buscar_dpi.pack(side="left", padx=5, expand=True, fill="x")
        self.entry_buscar_dpi.bind("<Return>", lambda e: self.buscar_persona())
        
        btn_buscar = ctk.CTkButton(
            frame_buscar_dpi,
            text="🔍 Buscar",
            command=self.buscar_persona,
            width=100
        )
        btn_buscar.pack(side="left", padx=5)
        
        btn_limpiar = ctk.CTkButton(
            frame_buscar_dpi,
            text="🔄 Limpiar",
            command=self.limpiar_campos,
            width=100,
            fg_color=COLOR_WARNING,
            hover_color="#e67e22"
        )
        btn_limpiar.pack(side="left", padx=5)
        
        # ----- Fecha y Hora -----
        frame_fecha = ctk.CTkFrame(panel_izquierdo)
        frame_fecha.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(
            frame_fecha,
            text="🕐 Fecha y Hora del Acta",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)
        
        frame_hora = ctk.CTkFrame(frame_fecha)
        frame_hora.pack(pady=5, fill="x", padx=20)
        
        ctk.CTkLabel(frame_hora, text="Hora:", width=100).pack(side="left", padx=5)
        self.entry_hora = ctk.CTkEntry(frame_hora, placeholder_text="Ej: 17")
        self.entry_hora.pack(side="left", padx=5, expand=True, fill="x")
        
        ctk.CTkLabel(frame_hora, text="Minutos:", width=100).pack(side="left", padx=5)
        self.entry_minutos = ctk.CTkEntry(frame_hora, placeholder_text="Ej: 20")
        self.entry_minutos.pack(side="left", padx=5, expand=True, fill="x")
        
        frame_fecha_dia = ctk.CTkFrame(frame_fecha)
        frame_fecha_dia.pack(pady=5, fill="x", padx=20)
        
        ctk.CTkLabel(frame_fecha_dia, text="Día:", width=100).pack(side="left", padx=5)
        self.entry_dia = ctk.CTkEntry(frame_fecha_dia, placeholder_text="Ej: 28")
        self.entry_dia.pack(side="left", padx=5, expand=True, fill="x")
        
        ctk.CTkLabel(frame_fecha_dia, text="Mes:", width=100).pack(side="left", padx=5)
        self.combo_mes = ctk.CTkComboBox(
            frame_fecha_dia,
            values=["enero", "febrero", "marzo", "abril", "mayo", "junio",
                    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        )
        self.combo_mes.set("noviembre")
        self.combo_mes.pack(side="left", padx=5, expand=True, fill="x")
        
        ctk.CTkLabel(frame_fecha_dia, text="Año:", width=100).pack(side="left", padx=5)
        self.entry_anio = ctk.CTkEntry(frame_fecha_dia, placeholder_text="Ej: 2025")
        self.entry_anio.pack(side="left", padx=5, expand=True, fill="x")
        
        # ----- Datos personales -----
        frame_datos = ctk.CTkFrame(panel_izquierdo)
        frame_datos.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(
            frame_datos,
            text="👤 Datos Personales",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)
        
        frame_nombre = ctk.CTkFrame(frame_datos)
        frame_nombre.pack(pady=5, fill="x", padx=20)
        ctk.CTkLabel(frame_nombre, text="Nombre Completo:", width=150).pack(side="left", padx=5)
        self.entry_nombre = ctk.CTkEntry(
            frame_nombre,
            placeholder_text="Ej: Juan Carlos Pérez López"
        )
        self.entry_nombre.pack(side="left", padx=5, expand=True, fill="x")
        
        # Sexo
        frame_sexo = ctk.CTkFrame(frame_datos)
        frame_sexo.pack(pady=5, fill="x", padx=20)
        ctk.CTkLabel(frame_sexo, text="Sexo:", width=150).pack(side="left", padx=5)
        self.combo_sexo = ctk.CTkComboBox(
            frame_sexo,
            values=["masculino", "femenino"]
        )
        self.combo_sexo.set("masculino")
        self.combo_sexo.pack(side="left", padx=5, expand=True, fill="x")
        
        # Fecha de nacimiento
        frame_fecha_nac = ctk.CTkFrame(frame_datos)
        frame_fecha_nac.pack(pady=5, fill="x", padx=20)
        ctk.CTkLabel(frame_fecha_nac, text="Fecha de Nacimiento:", width=150).pack(side="left", padx=5)
        self.entry_fecha_nac = ctk.CTkEntry(
            frame_fecha_nac,
            placeholder_text="DD/MM/AAAA (Ej: 15/03/1995)"
        )
        self.entry_fecha_nac.pack(side="left", padx=5, expand=True, fill="x")
        self.entry_fecha_nac.bind("<FocusOut>", self.calcular_edad)
        self.entry_fecha_nac.bind("<Return>", self.calcular_edad)
        
        frame_edad = ctk.CTkFrame(frame_datos)
        frame_edad.pack(pady=5, fill="x", padx=20)
        ctk.CTkLabel(frame_edad, text="Edad:", width=150).pack(side="left", padx=5)
        self.entry_edad = ctk.CTkEntry(frame_edad, placeholder_text="Se calcula automáticamente")
        self.entry_edad.configure(state="readonly")
        self.entry_edad.pack(side="left", padx=5, expand=True, fill="x")
        
        frame_estado = ctk.CTkFrame(frame_datos)
        frame_estado.pack(pady=5, fill="x", padx=20)
        ctk.CTkLabel(frame_estado, text="Estado Civil:", width=150).pack(side="left", padx=5)
        self.combo_estado = ctk.CTkComboBox(
            frame_estado,
            values=["soltero", "soltera", "casado", "casada",
                    "divorciado", "divorciada", "viudo", "viuda"]
        )
        self.combo_estado.set("soltero")
        self.combo_estado.pack(side="left", padx=5, expand=True, fill="x")
        
        frame_casada = ctk.CTkFrame(frame_datos)
        frame_casada.pack(pady=5, fill="x", padx=20)
        ctk.CTkLabel(frame_casada, text="Apellido de casada:", width=150).pack(side="left", padx=5)
        self.entry_casada = ctk.CTkEntry(
            frame_casada,
            placeholder_text="(Opcional) Ej: de López"
        )
        self.entry_casada.pack(side="left", padx=5, expand=True, fill="x")
        
        frame_nacionalidad = ctk.CTkFrame(frame_datos)
        frame_nacionalidad.pack(pady=5, fill="x", padx=20)
        ctk.CTkLabel(frame_nacionalidad, text="Nacionalidad:", width=150).pack(side="left", padx=5)
        self.entry_nacionalidad = ctk.CTkEntry(
            frame_nacionalidad,
            placeholder_text="Ej: guatemalteco / guatemalteca"
        )
        self.entry_nacionalidad.pack(side="left", padx=5, expand=True, fill="x")
        
        frame_nivel = ctk.CTkFrame(frame_datos)
        frame_nivel.pack(pady=5, fill="x", padx=20)
        ctk.CTkLabel(frame_nivel, text="Nivel Académico:", width=150).pack(side="left", padx=5)
        self.entry_nivel = ctk.CTkEntry(
            frame_nivel,
            placeholder_text="Ej: Bachiller en Ciencias y Letras"
        )
        self.entry_nivel.pack(side="left", padx=5, expand=True, fill="x")
        
        frame_domicilio = ctk.CTkFrame(frame_datos)
        frame_domicilio.pack(pady=5, fill="x", padx=20)
        ctk.CTkLabel(frame_domicilio, text="Domicilio:", width=150).pack(side="left", padx=5)
        self.entry_domicilio = ctk.CTkEntry(
            frame_domicilio,
            placeholder_text="Ej: departamento de Guatemala"
        )
        self.entry_domicilio.pack(side="left", padx=5, expand=True, fill="x")
        
        # ----- DPI -----
        frame_dpi = ctk.CTkFrame(frame_datos)
        frame_dpi.pack(pady=5, fill="x", padx=20)
        ctk.CTkLabel(frame_dpi, text="DPI (CUI):", width=150).pack(side="left", padx=5)
        self.entry_dpi = ctk.CTkEntry(
            frame_dpi,
            placeholder_text="Ej: 2008 22829 0101"
        )
        self.entry_dpi.pack(side="left", padx=5, expand=True, fill="x")
        
        # ----- Botones -----
        frame_botones = ctk.CTkFrame(panel_izquierdo)
        frame_botones.pack(pady=30)
        
        btn_guardar = ctk.CTkButton(
            frame_botones,
            text="💾 Guardar Persona",
            command=self.guardar_persona,
            height=45,
            width=200,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=COLOR_PRIMARY,
            hover_color="#2980b9"
        )
        btn_guardar.pack(side="left", padx=10)
        
        btn_preview = ctk.CTkButton(
            frame_botones,
            text="👁️ Vista Previa",
            command=self.generar_preview,
            height=45,
            width=200,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=COLOR_WARNING,
            hover_color="#e67e22"
        )
        btn_preview.pack(side="left", padx=10)
        
        btn_generar = ctk.CTkButton(
            frame_botones,
            text="✅ Generar Documento",
            command=self.generar_documento,
            height=45,
            width=200,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=COLOR_SUCCESS,
            hover_color="#27ae60"
        )
        btn_generar.pack(side="left", padx=10)
        
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
            text="Haga clic en 'Vista Previa' para visualizar el documento",
            text_color="gray",
            font=ctk.CTkFont(size=14)
        )
        self.lbl_visor_estado.pack(pady=200)
    
    def calcular_edad(self, event=None):
        """Calcula la edad a partir de la fecha de nacimiento"""
        fecha_nac_str = self.entry_fecha_nac.get().strip()
        
        if not fecha_nac_str:
            return
        
        try:
            # Intentar parsear la fecha
            if '/' in fecha_nac_str:
                partes = fecha_nac_str.split('/')
                if len(partes) == 3:
                    dia, mes, anio = int(partes[0]), int(partes[1]), int(partes[2])
                    fecha_nac = datetime(anio, mes, dia)
                else:
                    return
            else:
                return
            
            # Calcular edad
            hoy = datetime.now()
            edad = hoy.year - fecha_nac.year
            
            # Ajustar si aún no ha cumplido años este año
            if (hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day):
                edad -= 1
            
            # Actualizar campo de edad
            self.entry_edad.configure(state="normal")
            self.entry_edad.delete(0, "end")
            self.entry_edad.insert(0, str(edad))
            self.entry_edad.configure(state="readonly")
            
        except ValueError:
            messagebox.showwarning(
                "Fecha inválida",
                "Por favor ingrese una fecha válida en formato DD/MM/AAAA"
            )
    
    def buscar_persona(self):
        """Busca una persona por DPI y autocompleta los campos"""
        dpi = self.entry_buscar_dpi.get().strip()
        
        if not dpi:
            messagebox.showwarning("Advertencia", "Ingrese un DPI para buscar")
            return
        
        resultado = self.db.buscar_persona_por_dpi(dpi)
        
        if resultado:
            # Formato: id, nombre_completo, dpi, edad, estado_civil, 
            #          nacionalidad, domicilio, nivel_academico, 
            #          apellido_casada, fecha_registro, sexo, fecha_nacimiento
            
            self.persona_actual_id = resultado[0]  # id
            
            # Nombre completo
            self.entry_nombre.delete(0, "end")
            if resultado[1]:
                self.entry_nombre.insert(0, resultado[1])
            
            # Sexo
            if resultado[10]:
                self.combo_sexo.set(resultado[10])
            
            # Fecha de nacimiento
            self.entry_fecha_nac.delete(0, "end")
            if resultado[11]:
                self.entry_fecha_nac.insert(0, resultado[11])
                self.calcular_edad()
            elif resultado[3]:
                # Si no hay fecha de nacimiento pero sí edad
                self.entry_edad.configure(state="normal")
                self.entry_edad.delete(0, "end")
                self.entry_edad.insert(0, str(resultado[3]))
                self.entry_edad.configure(state="readonly")
            
            # Estado civil
            if resultado[4]:
                self.combo_estado.set(resultado[4])
            
            # Nacionalidad
            self.entry_nacionalidad.delete(0, "end")
            if resultado[5]:
                self.entry_nacionalidad.insert(0, resultado[5])
            
            # Domicilio
            self.entry_domicilio.delete(0, "end")
            if resultado[6]:
                self.entry_domicilio.insert(0, resultado[6])
            
            # Nivel académico
            self.entry_nivel.delete(0, "end")
            if resultado[7]:
                self.entry_nivel.insert(0, resultado[7])
            
            # Apellido de casada (limpiar si contiene texto no válido)
            self.entry_casada.delete(0, "end")
            if resultado[8]:
                apellido_casada = resultado[8].strip()
                
                # Lista de textos que NO son apellidos de casada válidos
                textos_invalidos = [
                    "personal de identificación",
                    "documento personal",
                    "identificación",
                    "dpi",
                    "cui",
                    "código único",
                    "renap",
                    "registro nacional"
                ]
                
                # Verificar que no contenga texto inválido
                es_valido = True
                apellido_lower = apellido_casada.lower()
                
                for texto_invalido in textos_invalidos:
                    if texto_invalido in apellido_lower:
                        es_valido = False
                        break
                
                # Solo insertar si es válido y no está vacío
                if es_valido and len(apellido_casada) > 0:
                    self.entry_casada.insert(0, apellido_casada)
            
            # DPI
            self.entry_dpi.delete(0, "end")
            if resultado[2]:
                self.entry_dpi.insert(0, resultado[2])
            
            messagebox.showinfo("Éxito", f"Persona encontrada: {resultado[1]}\n\nDatos autocompletados.")
        else:
            messagebox.showinfo(
                "No encontrado",
                "No se encontró ninguna persona con ese DPI.\n\n"
                "Complete los campos para crear un nuevo registro."
            )
    
    def guardar_persona(self):
        """Guarda o actualiza una persona en la base de datos"""
        nombre = self.entry_nombre.get().strip()
        dpi = self.entry_dpi.get().strip()
        
        if not nombre or not dpi:
            messagebox.showwarning("Advertencia", "Debe ingresar al menos el nombre y DPI")
            return
        
        try:
            # Obtener edad del campo (puede ser calculada o manual)
            self.entry_edad.configure(state="normal")
            edad_str = self.entry_edad.get().strip()
            self.entry_edad.configure(state="readonly")
            
            datos = {
                'nombre': nombre,
                'sexo': self.combo_sexo.get(),
                'fecha_nacimiento': self.entry_fecha_nac.get().strip(),
                'edad': int(edad_str) if edad_str else None,
                'estado_civil': self.combo_estado.get(),
                'apellido_casada': self.entry_casada.get().strip(),
                'nacionalidad': self.entry_nacionalidad.get().strip(),
                'nivel_academico': self.entry_nivel.get().strip(),
                'domicilio': self.entry_domicilio.get().strip(),
                'dpi': dpi
            }
            
            persona_id, resultado = self.db.guardar_persona(datos)
            self.persona_actual_id = persona_id
            
            if resultado == "guardado":
                messagebox.showinfo("Éxito", "Persona registrada correctamente")
            else:
                messagebox.showinfo("Éxito", "Persona actualizada correctamente")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar persona:\n{str(e)}")
    
    def generar_preview(self):
        """Genera una vista previa del documento"""
        # Verificar plantilla
        plantilla = self.db.obtener_plantilla_activa()
        if not plantilla:
            messagebox.showwarning("Advertencia", "No hay plantilla activa")
            return
        
        # Validar datos mínimos
        if not self.entry_nombre.get().strip() or not self.entry_dpi.get().strip():
            messagebox.showwarning("Advertencia", "Debe ingresar al menos el nombre y DPI")
            return
        
        # Limpiar visor
        for widget in self.visor_scroll.winfo_children():
            widget.destroy()
        
        self.lbl_visor_estado = ctk.CTkLabel(
            self.visor_scroll,
            text="Generando vista previa...",
            text_color="orange",
            font=ctk.CTkFont(size=14)
        )
        self.lbl_visor_estado.pack(pady=20)
        self.update()
        
        try:
            # Generar documento temporal
            doc = self.crear_documento_con_datos()
            
            # Guardar temporalmente
            temp_docx = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
            temp_docx.close()
            doc.save(temp_docx.name)
            
            # Convertir a PDF
            temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_pdf.close()
            
            convert(temp_docx.name, temp_pdf.name)
            
            # Mostrar PDF
            self.mostrar_pdf_en_visor(temp_pdf.name)
            
            # Guardar referencia para generar después
            self.documento_preview = temp_docx.name
            
            # Limpiar PDF temporal
            os.unlink(temp_pdf.name)
            
        except Exception as e:
            self.lbl_visor_estado.configure(
                text=f"Error al generar vista previa:\n{str(e)}",
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
    
    def crear_documento_con_datos(self):
        """Crea un documento con los datos del formulario"""
        plantilla = self.db.obtener_plantilla_activa()
        doc = Document(plantilla[2])
        
        # Obtener datos
        hora = self.entry_hora.get().strip()
        minutos = self.entry_minutos.get().strip()
        dia = self.entry_dia.get().strip()
        mes = self.combo_mes.get().strip()
        anio = self.entry_anio.get().strip()
        nombre = self.entry_nombre.get().strip()
        sexo = self.combo_sexo.get().strip()
        
        # Obtener edad
        self.entry_edad.configure(state="normal")
        edad = self.entry_edad.get().strip()
        self.entry_edad.configure(state="readonly")
        
        estado_civil = self.combo_estado.get().strip()
        apellido_casada = self.entry_casada.get().strip()
        nacionalidad = self.entry_nacionalidad.get().strip()
        nivel_academico = self.entry_nivel.get().strip()
        domicilio = self.entry_domicilio.get().strip()
        dpi = self.entry_dpi.get().strip()
        
        # Determinar artículos y pronombres según el sexo
        if sexo == "femenino":
            # Reemplazos de masculino a femenino
            reemplazos_genero = [
                ("el señor", "la señora"),
                ("el requirente", "la requirente")
            ]
        else:
            # Reemplazos de femenino a masculino
            reemplazos_genero = [
                ("la señora", "el señor"),
                ("la requirente", "el requirente")
            ]
        
        # Construir nombre completo con apellido de casada
        nombre_completo = nombre
        if apellido_casada and estado_civil == "casada":
            partes = nombre.split()
            if len(partes) >= 2:
                nombre_completo = f"{partes[0]} {partes[1]} {apellido_casada}"
                if len(partes) > 2:
                    nombre_completo += " " + " ".join(partes[2:])
        
        # Convertir año a texto
        anio_texto = None
        if anio.isdigit():
            anio_num = int(anio)
            if 2000 <= anio_num < 2100:
                resto = anio_num - 2000
                if resto == 0:
                    anio_texto = "dos mil"
                else:
                    anio_texto = "dos mil " + NumeroATexto.convertir(resto)
            else:
                anio_texto = str(anio)
        
        # Preparar reemplazos
        reemplazos = []
        
        # Primero agregar los reemplazos de género (IMPORTANTE: antes que otros)
        reemplazos.extend(reemplazos_genero)
        
        if hora and minutos:
            hora_t = NumeroATexto.convertir(int(hora))
            min_t = NumeroATexto.convertir(int(minutos))
            reemplazos.append(("diecisiete horas con veinte minutos", f"{hora_t} horas con {min_t} minutos"))
        
        if dia:
            dia_t = NumeroATexto.convertir(int(dia))
            reemplazos.append(("veintiocho", dia_t))
            reemplazos.append(("(28)", f"({dia})"))
        
        if mes:
            reemplazos.append(("noviembre", mes))
        
        if anio and anio_texto:
            reemplazos.append(("dos mil veinticinco", anio_texto))
            reemplazos.append(("(2025)", f"({anio})"))
        
        if nombre:
            reemplazos.append(("Abner Aníbal Ajpop González", nombre_completo))
        
        if edad:
            edad_num = int(edad)
            edad_t = NumeroATexto.convertir(edad_num)
            
            if edad_t.endswith(" y uno"):
                edad_t = edad_t[:-3] + " un"
            elif edad_t == "uno":
                edad_t = "un"
            
            reemplazos.append(("veintiún", edad_t))
            reemplazos.append(("(21)", f"({edad})"))
        
        if estado_civil:
            reemplazos.append(("soltero", estado_civil))
        
        if nacionalidad:
            reemplazos.append(("guatemalteco", nacionalidad))
        
        if nivel_academico:
            reemplazos.append(("Bachiller en Ciencias y Letras con Orientación en Computación", nivel_academico))
        
        if domicilio:
            reemplazos.append(("con domicilio en el departamento de Guatemala", f"con domicilio en el {domicilio}"))
        
        if dpi:
            dpi_formateado = dpi.replace(" ", "")
            if len(dpi_formateado) == 13:
                dpi_con_espacios = f"{dpi_formateado[:4]} {dpi_formateado[4:9]} {dpi_formateado[9:13]}"
            else:
                dpi_con_espacios = dpi
            
            dpi_texto = NumeroATexto.convertir_dpi(dpi)
            reemplazos.append(("dos mil ocho espacio veintidós mil ochocientos veintinueve espacio cero ciento uno", dpi_texto))
            reemplazos.append(("(2008 22829 0101)", f"({dpi_con_espacios})"))
        
        # Aplicar reemplazos
        for paragraph in doc.paragraphs:
            for buscar, reemplazar in reemplazos:
                # Reemplazar todas las ocurrencias para nombre y género
                if buscar == "Abner Aníbal Ajpop González":
                    self.reemplazar_en_parrafo(paragraph, buscar, reemplazar, reemplazar_todas=True)
                elif buscar in ["el señor", "la señora", "el requirente", "la requirente"]:
                    self.reemplazar_en_parrafo(paragraph, buscar, reemplazar, reemplazar_todas=True)
                else:
                    self.reemplazar_en_parrafo(paragraph, buscar, reemplazar, reemplazar_todas=False)
        
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        for buscar, reemplazar in reemplazos:
                            if buscar == "Abner Aníbal Ajpop González":
                                self.reemplazar_en_parrafo(paragraph, buscar, reemplazar, reemplazar_todas=True)
                            elif buscar in ["el señor", "la señora", "el requirente", "la requirente"]:
                                self.reemplazar_en_parrafo(paragraph, buscar, reemplazar, reemplazar_todas=True)
                            else:
                                self.reemplazar_en_parrafo(paragraph, buscar, reemplazar, reemplazar_todas=False)
        
        return doc
    
    def generar_documento(self):
        """Genera el documento con los datos ingresados"""
        # Verificar plantilla
        plantilla = self.db.obtener_plantilla_activa()
        if not plantilla:
            messagebox.showwarning("Advertencia", "No hay plantilla activa")
            return
        
        # Validar datos mínimos
        if not self.entry_nombre.get().strip() or not self.entry_dpi.get().strip():
            messagebox.showwarning("Advertencia", "Debe ingresar al menos el nombre y DPI")
            return
        
        try:
            # Crear documento
            doc = self.crear_documento_con_datos()
            
            # Verificar si ya existe un documento para esta persona en este año
            anio = self.entry_anio.get().strip()
            archivo_salida = None
            
            if self.persona_actual_id and anio:
                # Buscar si ya existe un documento
                self.db.cursor.execute('''
                    SELECT ruta_documento FROM historial_actas
                    WHERE persona_id = ? AND anio = ?
                    ORDER BY id DESC LIMIT 1
                ''', (self.persona_actual_id, int(anio)))
                
                resultado = self.db.cursor.fetchone()
                
                if resultado and os.path.exists(resultado[0]):
                    # Preguntar si desea sobrescribir
                    respuesta = messagebox.askyesno(
                        "Documento existente",
                        f"Ya existe un documento para esta persona en el año {anio}.\n\n"
                        f"¿Desea actualizar el documento existente?\n\n"
                        f"Ruta: {resultado[0]}"
                    )
                    
                    if respuesta:
                        archivo_salida = resultado[0]
            
            # Si no hay archivo existente o no se quiere sobrescribir, crear uno nuevo
            if not archivo_salida:
                nombre = self.entry_nombre.get().strip()
                fecha_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
                archivo_salida = filedialog.asksaveasfilename(
                    defaultextension=".docx",
                    filetypes=[("Documento Word", "*.docx")],
                    initialfile=f"acta_{nombre.replace(' ', '_')}_{fecha_hora}.docx"
                )
            
            if archivo_salida:
                doc.save(archivo_salida)
                
                # Guardar en historial si hay persona registrada
                if self.persona_actual_id and anio:
                    dia = self.entry_dia.get().strip()
                    mes = self.combo_mes.get().strip()
                    hora = self.entry_hora.get().strip()
                    minutos = self.entry_minutos.get().strip()
                    
                    fecha_acta = f"{dia}/{mes}/{anio}" if dia and mes else datetime.now().strftime("%d/%m/%Y")
                    
                    # Verificar si ya existe un registro para actualizar
                    self.db.cursor.execute('''
                        SELECT id FROM historial_actas
                        WHERE persona_id = ? AND anio = ?
                    ''', (self.persona_actual_id, int(anio)))
                    
                    existe = self.db.cursor.fetchone()
                    
                    if existe:
                        # Actualizar
                        self.db.cursor.execute('''
                            UPDATE historial_actas
                            SET fecha_acta = ?, hora = ?, minutos = ?, ruta_documento = ?
                            WHERE id = ?
                        ''', (fecha_acta, hora, minutos, archivo_salida, existe[0]))
                        self.db.conn.commit()
                    else:
                        # Insertar nuevo
                        self.db.guardar_historial_acta(
                            self.persona_actual_id,
                            fecha_acta,
                            hora,
                            minutos,
                            int(anio),
                            archivo_salida
                        )
                
                messagebox.showinfo(
                    "Éxito",
                    f"✅ Documento generado correctamente:\n\n{archivo_salida}"
                )
        
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar el documento:\n{str(e)}")
    
    def reemplazar_en_parrafo(self, paragraph, buscar, reemplazar, reemplazar_todas=False):
        """Reemplaza texto en un párrafo manteniendo el formato"""
        reemplazos_realizados = 0
        
        while True:
            texto_completo = ''.join(run.text for run in paragraph.runs)
            
            if buscar not in texto_completo:
                break
            
            pos_inicio = texto_completo.find(buscar)
            pos_fin = pos_inicio + len(buscar)
            
            pos_actual = 0
            run_inicio = None
            run_fin = None
            pos_en_run_inicio = 0
            pos_en_run_fin = 0
            
            for i, run in enumerate(paragraph.runs):
                len_run = len(run.text)
                
                if pos_actual <= pos_inicio < pos_actual + len_run:
                    run_inicio = i
                    pos_en_run_inicio = pos_inicio - pos_actual
                
                if pos_actual < pos_fin <= pos_actual + len_run:
                    run_fin = i
                    pos_en_run_fin = pos_fin - pos_actual
                    break
                
                pos_actual += len_run
            
            if run_inicio is None or run_fin is None:
                break
            
            if run_inicio == run_fin:
                run = paragraph.runs[run_inicio]
                run.text = run.text[:pos_en_run_inicio] + reemplazar + run.text[pos_en_run_fin:]
            else:
                paragraph.runs[run_inicio].text = paragraph.runs[run_inicio].text[:pos_en_run_inicio] + reemplazar
                
                runs_a_eliminar = []
                for i in range(run_inicio + 1, run_fin + 1):
                    if i == run_fin:
                        paragraph.runs[i].text = paragraph.runs[i].text[pos_en_run_fin:]
                        if not paragraph.runs[i].text:
                            runs_a_eliminar.append(i)
                    else:
                        runs_a_eliminar.append(i)
                
                for i in reversed(runs_a_eliminar):
                    paragraph._element.remove(paragraph.runs[i]._element)
            
            reemplazos_realizados += 1
            
            if not reemplazar_todas:
                break
        
        return reemplazos_realizados > 0
    
    def limpiar_campos(self):
        """Limpia todos los campos del formulario"""
        self.entry_buscar_dpi.delete(0, "end")
        self.entry_hora.delete(0, "end")
        self.entry_minutos.delete(0, "end")
        self.entry_dia.delete(0, "end")
        self.combo_mes.set("noviembre")
        self.entry_anio.delete(0, "end")
        self.entry_nombre.delete(0, "end")
        self.combo_sexo.set("masculino")
        self.entry_fecha_nac.delete(0, "end")
        self.entry_edad.configure(state="normal")
        self.entry_edad.delete(0, "end")
        self.entry_edad.configure(state="readonly")
        self.combo_estado.set("soltero")
        self.entry_casada.delete(0, "end")
        self.entry_nacionalidad.delete(0, "end")
        self.entry_nivel.delete(0, "end")
        self.entry_domicilio.delete(0, "end")
        self.entry_dpi.delete(0, "end")
        self.persona_actual_id = None
        
        # Limpiar visor
        for widget in self.visor_scroll.winfo_children():
            widget.destroy()
        
        self.lbl_visor_estado = ctk.CTkLabel(
            self.visor_scroll,
            text="Haga clic en 'Vista Previa' para visualizar el documento",
            text_color="gray",
            font=ctk.CTkFont(size=14)
        )
        self.lbl_visor_estado.pack(pady=200)