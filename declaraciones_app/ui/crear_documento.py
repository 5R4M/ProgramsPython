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

class VentanaCrearDocumento:
    def __init__(self, parent, db, es_integrado=False):
        self.db = db
        self.es_integrado = es_integrado
        self.callback_actualizar = None
        self.persona_actual_id = None
        self.documento_preview = None
        self.ruta_documento_actual = None
        
        if es_integrado:
            # Crear como Frame integrado
            self.ventana = ctk.CTkFrame(parent)
            self.ventana.pack(fill="both", expand=True)
        else:
            # Crear como ventana separada (Toplevel)
            self.ventana = ctk.CTkToplevel(parent)
            self.ventana.title("➕ Crear Nuevo Documento")
            self.center_window()
            self.ventana.after(100, self.maximizar_ventana)
        
        self.crear_interfaz()
        self.verificar_plantilla()
    
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
        container = ctk.CTkFrame(self.ventana)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)
        
        # ===== PANEL IZQUIERDO: Formulario =====
        panel_izquierdo = ctk.CTkFrame(container)
        panel_izquierdo.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Título
        ctk.CTkLabel(
            panel_izquierdo,
            text="➕ Crear Nuevo Documento",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=10)
        
        # Estado de plantilla
        self.lbl_plantilla = ctk.CTkLabel(
            panel_izquierdo,
            text="Verificando plantilla...",
            font=ctk.CTkFont(size=14)
        )
        self.lbl_plantilla.pack(pady=5)
        
        btn_cambiar_plantilla = ctk.CTkButton(
            panel_izquierdo,
            text="📋 Cambiar Plantilla",
            command=self.cargar_plantilla,
            width=200
        )
        btn_cambiar_plantilla.pack(pady=3)
        
        # Separador
        ctk.CTkLabel(panel_izquierdo, text="").pack(pady=5)
        
        # ----- Sección de Búsqueda Rápida -----
        frame_busqueda = ctk.CTkFrame(panel_izquierdo)
        frame_busqueda.pack(pady=5, padx=20, fill="x")
        
        ctk.CTkLabel(
            frame_busqueda,
            text="🔍 Búsqueda Rápida (Opcional)",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=5)
        
        ctk.CTkLabel(
            frame_busqueda,
            text="Si la persona ya existe, búsquela por DPI para autocompletar los datos",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(pady=2)
        
        frame_buscar_dpi = ctk.CTkFrame(frame_busqueda)
        frame_buscar_dpi.pack(pady=3, padx=20, fill="x")
        
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
        frame_fecha.pack(pady=3, padx=20, fill="x")
        
        ctk.CTkLabel(
            frame_fecha,
            text="🕐 Fecha y Hora del Acta",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=5)
        
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
        frame_datos.pack(pady=5, padx=20, fill="x")
        
        ctk.CTkLabel(
            frame_datos,
            text="👤 Datos Personales",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=5)
        
        frame_nombre = ctk.CTkFrame(frame_datos)
        frame_nombre.pack(pady=2, fill="x", padx=20)
        ctk.CTkLabel(frame_nombre, text="Nombre Completo:", width=150).pack(side="left", padx=5)
        self.entry_nombre = ctk.CTkEntry(
            frame_nombre,
            placeholder_text="Ej: Juan Carlos Pérez López"
        )
        self.entry_nombre.pack(side="left", padx=5, expand=True, fill="x")
        
        # Sexo
        frame_sexo = ctk.CTkFrame(frame_datos)
        frame_sexo.pack(pady=2, fill="x", padx=20)
        ctk.CTkLabel(frame_sexo, text="Sexo:", width=150).pack(side="left", padx=5)
        self.combo_sexo = ctk.CTkComboBox(
            frame_sexo,
            values=["masculino", "femenino"]
        )
        self.combo_sexo.set("masculino")
        self.combo_sexo.pack(side="left", padx=5, expand=True, fill="x")
        
        # Fecha de nacimiento
        frame_fecha_nac = ctk.CTkFrame(frame_datos)
        frame_fecha_nac.pack(pady=2, fill="x", padx=20)
        ctk.CTkLabel(frame_fecha_nac, text="Fecha de Nacimiento:", width=150).pack(side="left", padx=5)
        self.entry_fecha_nac = ctk.CTkEntry(
            frame_fecha_nac,
            placeholder_text="DD/MM/AAAA (Ej: 15/03/1995)"
        )
        self.entry_fecha_nac.pack(side="left", padx=5, expand=True, fill="x")
        self.entry_fecha_nac.bind("<FocusOut>", self.calcular_edad)
        self.entry_fecha_nac.bind("<Return>", self.calcular_edad)
        
        frame_edad = ctk.CTkFrame(frame_datos)
        frame_edad.pack(pady=2, fill="x", padx=20)
        ctk.CTkLabel(frame_edad, text="Edad:", width=150).pack(side="left", padx=5)
        self.entry_edad = ctk.CTkEntry(frame_edad, placeholder_text="Se calcula automáticamente")
        self.entry_edad.configure(state="readonly")
        self.entry_edad.pack(side="left", padx=5, expand=True, fill="x")
        
        frame_estado = ctk.CTkFrame(frame_datos)
        frame_estado.pack(pady=2, fill="x", padx=20)
        ctk.CTkLabel(frame_estado, text="Estado Civil:", width=150).pack(side="left", padx=5)
        self.combo_estado = ctk.CTkComboBox(
            frame_estado,
            values=["soltero", "soltera", "casado", "casada",
                    "divorciado", "divorciada", "viudo", "viuda"]
        )
        self.combo_estado.set("soltero")
        self.combo_estado.pack(side="left", padx=5, expand=True, fill="x")
        
        frame_casada = ctk.CTkFrame(frame_datos)
        frame_casada.pack(pady=2, fill="x", padx=20)
        ctk.CTkLabel(frame_casada, text="Apellido de casada:", width=150).pack(side="left", padx=5)
        self.entry_casada = ctk.CTkEntry(
            frame_casada,
            placeholder_text="(Opcional) Ej: de López"
        )
        self.entry_casada.pack(side="left", padx=5, expand=True, fill="x")
        
        frame_nacionalidad = ctk.CTkFrame(frame_datos)
        frame_nacionalidad.pack(pady=2, fill="x", padx=20)
        ctk.CTkLabel(frame_nacionalidad, text="Nacionalidad:", width=150).pack(side="left", padx=5)
        self.entry_nacionalidad = ctk.CTkEntry(
            frame_nacionalidad,
            placeholder_text="Ej: guatemalteco / guatemalteca"
        )
        self.entry_nacionalidad.pack(side="left", padx=5, expand=True, fill="x")
        
        frame_nivel = ctk.CTkFrame(frame_datos)
        frame_nivel.pack(pady=2, fill="x", padx=20)
        ctk.CTkLabel(frame_nivel, text="Nivel Académico:", width=150).pack(side="left", padx=5)
        self.entry_nivel = ctk.CTkEntry(
            frame_nivel,
            placeholder_text="Ej: Bachiller en Ciencias y Letras"
        )
        self.entry_nivel.pack(side="left", padx=5, expand=True, fill="x")
        
        frame_domicilio = ctk.CTkFrame(frame_datos)
        frame_domicilio.pack(pady=2, fill="x", padx=20)
        ctk.CTkLabel(frame_domicilio, text="Domicilio:", width=150).pack(side="left", padx=5)
        self.entry_domicilio = ctk.CTkEntry(
            frame_domicilio,
            placeholder_text="Ej: departamento de Guatemala"
        )
        self.entry_domicilio.pack(side="left", padx=5, expand=True, fill="x")
        
        # ----- DPI -----
        frame_dpi = ctk.CTkFrame(frame_datos)
        frame_dpi.pack(pady=2, fill="x", padx=20)
        ctk.CTkLabel(frame_dpi, text="DPI (CUI):", width=150).pack(side="left", padx=5)
        self.entry_dpi = ctk.CTkEntry(
            frame_dpi,
            placeholder_text="Ej: 2008 22829 0101"
        )
        self.entry_dpi.pack(side="left", padx=5, expand=True, fill="x")
        
        # ----- Botones -----
        frame_botones = ctk.CTkFrame(panel_izquierdo)
        frame_botones.pack(pady=10, padx=20)
        
        btn_guardar = ctk.CTkButton(
            frame_botones,
            text="💾 Guardar Persona",
            command=self.guardar_persona,
            height=35,
            width=200,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLOR_PRIMARY,
            hover_color="#2980b9"
        )
        btn_guardar.pack(side="left", padx=5)
        
        btn_preview = ctk.CTkButton(
            frame_botones,
            text="👁️ Vista Previa",
            command=self.generar_preview,
            height=35,
            width=200,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLOR_WARNING,
            hover_color="#e67e22"
        )
        btn_preview.pack(side="left", padx=5)
        
        btn_generar = ctk.CTkButton(
            frame_botones,
            text="✅ Generar Documento",
            command=self.generar_documento,
            height=35,
            width=200,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLOR_SUCCESS,
            hover_color="#27ae60"
        )
        btn_generar.pack(side="left", padx=5)
        
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

            # ==== NUEVO: obtener DOCX de esta persona desde la tabla 'documentos' ====
            self.ruta_documento_actual = None
            try:
                ruta_doc = self.db.obtener_ultimo_documento_acta(self.persona_actual_id)
                if ruta_doc and os.path.exists(ruta_doc):
                    self.ruta_documento_actual = ruta_doc

            except Exception as e:
                print("Error al obtener documento desde tabla documentos:", e)
            # ===========================================================

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
                
                es_valido = True
                apellido_lower = apellido_casada.lower()
                for texto_invalido in textos_invalidos:
                    if texto_invalido in apellido_lower:
                        es_valido = False
                        break
                
                if es_valido and len(apellido_casada) > 0:
                    self.entry_casada.insert(0, apellido_casada)
            
            # DPI
            self.entry_dpi.delete(0, "end")
            if resultado[2]:
                self.entry_dpi.insert(0, resultado[2])
            
            mensaje_doc = "\n\nDocumento existente cargado." if self.ruta_documento_actual else "\n\nSin documento previo."
            messagebox.showinfo("Éxito", f"Persona encontrada: {resultado[1]}{mensaje_doc}")
        else:
            self.persona_actual_id = None
            self.ruta_documento_actual = None
            messagebox.showinfo(
                "No encontrado",
                "No se encontró ninguna persona con ese DPI.\n\n"
                "Complete los campos para crear un nuevo registro."
            )
    
    def guardar_persona(self):
        """Guarda o actualiza una persona en la base de datos y actualiza el documento si existe"""
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
            
            # ==== ACTUALIZAR DOCUMENTO ORIGINAL SI EXISTE ====
            if self.ruta_documento_actual and os.path.exists(self.ruta_documento_actual):
                try:
                    # Crear documento con los datos actualizados
                    doc_actualizado = self.crear_documento_con_datos()
                    
                    # Guardar directamente sobre el archivo original
                    doc_actualizado.save(self.ruta_documento_actual)
                    
                    # Actualizar el preview para que refleje los cambios
                    if self.documento_preview and os.path.exists(self.documento_preview):
                        os.unlink(self.documento_preview)
                    self.documento_preview = None
                    
                except Exception as e:
                    messagebox.showwarning("Advertencia", f"Persona guardada pero no se pudo actualizar el documento:\n{str(e)}")
            # =================================================
            
            if resultado == "guardado":
                messagebox.showinfo("Éxito", "Persona registrada correctamente")
            else:
                msg = "Persona actualizada correctamente"
                if self.ruta_documento_actual and os.path.exists(self.ruta_documento_actual):
                    msg += "\n\n✓ Documento actualizado con los nuevos datos"
                messagebox.showinfo("Éxito", msg)
            
            # Actualizar estadísticas del menú principal
            if self.callback_actualizar:
                self.callback_actualizar()
                        
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
        self.ventana.update()
        
        try:
            # Generar documento con datos actualizados
            doc = self.crear_documento_con_datos()
            
            # Limpiar preview anterior si existe
            if self.documento_preview and os.path.exists(self.documento_preview):
                try:
                    os.unlink(self.documento_preview)
                except:  # noqa: E722
                    pass
            
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
            
            # Guardar referencia del DOCX temporal para usar después
            self.documento_preview = temp_docx.name
            
            # Limpiar PDF temporal
            try:
                os.unlink(temp_pdf.name)
            except:  # noqa: E722
                pass
                        
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
        """Crea un documento con los datos del formulario SIEMPRE desde la plantilla original"""
        
        # CAMBIO CRÍTICO: Siempre usar la plantilla original, nunca el documento modificado
        plantilla = self.db.obtener_plantilla_activa()
        if not plantilla:
            raise RuntimeError("No hay plantilla activa")
        
        doc = Document(plantilla[2])
        
        # Obtener datos del formulario
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
        
        # Construir nombre completo con apellido de casada
        nombre_completo = nombre
        if apellido_casada:
            # Verificar que el apellido de casada no esté vacío o solo espacios
            apellido_casada_limpio = apellido_casada.strip()
            if apellido_casada_limpio and estado_civil in ["casada", "divorciada", "viuda"]:
                partes = nombre.split()
                if len(partes) >= 4:
                    # Insertar apellido de casada después del segundo apellido
                    # Formato: Nombre1 Nombre2 Apellido1 Apellido2 → Nombre1 Nombre2 Apellido1 Apellido2 de_Casada
                    nombre_completo = f"{partes[0]} {partes[1]} {partes[2]} {partes[3]} {apellido_casada_limpio}"
                    # Agregar apellidos adicionales si existen
                    if len(partes) > 4:
                        nombre_completo += " " + " ".join(partes[4:])
                elif len(partes) >= 2:
                    # Si no tiene suficientes partes, agregar al final
                    nombre_completo = f"{nombre} {apellido_casada_limpio}"
        
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
        
        # PRIMERO: Hacer reemplazos de género en todo el documento
        # IMPORTANTE: Hacer los reemplazos más específicos primero
        if sexo == "femenino":
            # Frases completas primero
            self.reemplazar_genero_documento(doc, "al requirente", "a la requirente")
            self.reemplazar_genero_documento(doc, "el requirente", "la requirente")
            self.reemplazar_genero_documento(doc, "El requirente", "La requirente")
            self.reemplazar_genero_documento(doc, "el señor", "la señora")
            self.reemplazar_genero_documento(doc, "El señor", "La señora")
            
            # Palabras individuales - IMPORTANTE: usar palabras completas con espacios
            self.reemplazar_genero_documento(doc, " advertido ", " advertida ")
            self.reemplazar_genero_documento(doc, " enterado ", " enterada ")
            self.reemplazar_genero_documento(doc, " deudor ", " deudora ")
            self.reemplazar_genero_documento(doc, " moroso ", " morosa ")
            self.reemplazar_genero_documento(doc, " incluido ", " incluida ")
        else:
            # Frases completas primero
            self.reemplazar_genero_documento(doc, "a la requirente", "al requirente")
            self.reemplazar_genero_documento(doc, "la requirente", "el requirente")
            self.reemplazar_genero_documento(doc, "La requirente", "El requirente")
            self.reemplazar_genero_documento(doc, "la señora", "el señor")
            self.reemplazar_genero_documento(doc, "La señora", "El señor")
            
            # Palabras individuales - con espacios
            self.reemplazar_genero_documento(doc, " advertida ", " advertido ")
            self.reemplazar_genero_documento(doc, " enterada ", " enterado ")
            self.reemplazar_genero_documento(doc, " deudora ", " deudor ")
            self.reemplazar_genero_documento(doc, " morosa ", " moroso ")
            self.reemplazar_genero_documento(doc, " incluida ", " incluido ")
        
        # SEGUNDO: Preparar otros reemplazos
        reemplazos = []
        
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
                
        # Aplicar otros reemplazos
        for paragraph in doc.paragraphs:
            for buscar, reemplazar in reemplazos:
                if buscar == "Abner Aníbal Ajpop González":
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
                            else:
                                self.reemplazar_en_parrafo(paragraph, buscar, reemplazar, reemplazar_todas=False)
        
        return doc

    def reemplazar_genero_documento(self, doc, buscar, reemplazar):
        """Reemplaza la PRIMERA ocurrencia de un texto de género en cada párrafo del documento"""
        reemplazos_totales = 0
        
        # Reemplazar en párrafos
        for paragraph in doc.paragraphs:
            ''.join(run.text for run in paragraph.runs)
            # Reemplazar TODAS las ocurrencias en este párrafo
            while buscar in ''.join(run.text for run in paragraph.runs):
                if self.reemplazar_preservando_formato(paragraph, buscar, reemplazar):
                    reemplazos_totales += 1
                else:
                    break
                # Prevenir loops infinitos
                if reemplazos_totales > 100:
                    return
        
        # Reemplazar en tablas
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        while buscar in ''.join(run.text for run in paragraph.runs):
                            if self.reemplazar_preservando_formato(paragraph, buscar, reemplazar):
                                reemplazos_totales += 1
                            else:
                                break
                            # Prevenir loops infinitos
                            if reemplazos_totales > 100:
                                return
        
    def clonar_formato_run(self, run_origen, run_destino):
        """Clona TODO el formato de un run a otro"""
        try:
            # Formato de caracteres
            if run_origen.bold is not None:
                run_destino.bold = run_origen.bold
            if run_origen.italic is not None:
                run_destino.italic = run_origen.italic
            if run_origen.underline is not None:
                run_destino.underline = run_origen.underline
            
            # Formato de fuente
            if run_origen.font.name:
                run_destino.font.name = run_origen.font.name
            if run_origen.font.size:
                run_destino.font.size = run_origen.font.size
            if run_origen.font.color.rgb:
                run_destino.font.color.rgb = run_origen.font.color.rgb
            
            # Otros formatos
            if run_origen.font.strike is not None:
                run_destino.font.strike = run_origen.font.strike
            if run_origen.font.all_caps is not None:
                run_destino.font.all_caps = run_origen.font.all_caps
            if run_origen.font.small_caps is not None:
                run_destino.font.small_caps = run_origen.font.small_caps
            if run_origen.font.highlight_color is not None:
                run_destino.font.highlight_color = run_origen.font.highlight_color
        except Exception as e:
            print("Error al clonar formato de run:", e)

    def reemplazar_preservando_formato(self, paragraph, buscar, reemplazar):
        """
        Reemplaza texto preservando el formato EXACTO de cada fragmento.
        Esta función NO destruye runs, sino que reconstruye el párrafo manteniendo los formatos.
        """
        # Obtener texto completo y verificar si contiene el texto buscado
        texto_completo = ''.join(run.text for run in paragraph.runs)
        
        if buscar not in texto_completo:
            return False
        
        # Encontrar la posición del texto a reemplazar
        pos_inicio = texto_completo.find(buscar)
        pos_fin = pos_inicio + len(buscar)
        
        # Mapear cada carácter a su run correspondiente
        mapa_runs = []  # [(caracter, run_index, formato)]
        pos_actual = 0
        
        for i, run in enumerate(paragraph.runs):
            for char in run.text:
                mapa_runs.append((char, i, run))
                pos_actual += 1
        
        # Construir nuevo contenido preservando formatos
        nuevos_runs = []
        pos = 0
        
        while pos < len(mapa_runs):
            if pos == pos_inicio:
                # Insertar el reemplazo con el formato del primer carácter reemplazado
                if pos_inicio < len(mapa_runs):
                    run_formato = mapa_runs[pos_inicio][2]
                    nuevos_runs.append((reemplazar, run_formato))
                else:
                    # Usar formato del último run disponible
                    run_formato = paragraph.runs[-1] if paragraph.runs else None
                    nuevos_runs.append((reemplazar, run_formato))
                
                # Saltar los caracteres que estamos reemplazando
                pos = pos_fin
            else:
                # Mantener el carácter original con su formato
                char, run_idx, run_orig = mapa_runs[pos]
                
                # Agrupar caracteres consecutivos con el mismo formato
                texto_grupo = char
                run_grupo = run_orig
                pos += 1
                
                while pos < len(mapa_runs) and pos != pos_inicio:
                    next_char, next_run_idx, next_run = mapa_runs[pos]
                    if next_run_idx == run_idx:
                        texto_grupo += next_char
                        pos += 1
                    else:
                        break
                
                nuevos_runs.append((texto_grupo, run_grupo))
        
        # Reconstruir el párrafo
        # Eliminar todos los runs existentes
        for i in range(len(paragraph.runs) - 1, -1, -1):
            paragraph._element.remove(paragraph.runs[i]._element)
        
        # Crear nuevos runs con el contenido y formato correspondiente
        for texto, run_formato in nuevos_runs:
            if texto:  # Solo agregar si hay texto
                nuevo_run = paragraph.add_run(texto)
                if run_formato:
                    self.clonar_formato_run(run_formato, nuevo_run)
        
        return True
    
    def reemplazar_texto_completo(self, paragraph, buscar, reemplazar):
        """Reemplaza TODAS las ocurrencias preservando formato (con protección contra loops)"""
        texto_completo = ''.join(run.text for run in paragraph.runs)
        
        # Contar cuántas veces aparece el texto a buscar
        ocurrencias = texto_completo.count(buscar)
        
        if ocurrencias == 0:
            return False
        
        # Reemplazar exactamente el número de ocurrencias encontradas
        reemplazos_hechos = 0
        while reemplazos_hechos < ocurrencias:
            if not self.reemplazar_preservando_formato(paragraph, buscar, reemplazar):
                break
            reemplazos_hechos += 1
        
        return reemplazos_hechos > 0
    
    def generar_documento(self):
        """Genera o actualiza el documento usando el archivo de vista previa"""
        # Validar datos mínimos
        if not self.entry_nombre.get().strip() or not self.entry_dpi.get().strip():
            messagebox.showwarning("Advertencia", "Debe ingresar al menos el nombre y DPI")
            return

        # Asegurarnos de tener una vista previa actualizada
        if not self.documento_preview or not os.path.exists(self.documento_preview):
            self.generar_preview()
            if not self.documento_preview or not os.path.exists(self.documento_preview):
                messagebox.showerror("Error", "No se pudo generar la vista previa del documento.")
                return

        try:
            anio = self.entry_anio.get().strip()

            # CASO 1: la persona ya tiene documento -> sobrescribir ese archivo
            if self.persona_actual_id and self.ruta_documento_actual:
                shutil.copy2(self.documento_preview, self.ruta_documento_actual)

                # Actualizar historial (fecha, hora, minutos) si se maneja año
                if anio:
                    dia = self.entry_dia.get().strip()
                    mes = self.combo_mes.get().strip()
                    hora = self.entry_hora.get().strip()
                    minutos = self.entry_minutos.get().strip()
                    
                    fecha_acta = f"{dia}/{mes}/{anio}" if dia and mes else datetime.now().strftime("%d/%m/%Y")
                    
                    self.db.cursor.execute('''
                        SELECT id FROM historial_actas
                        WHERE persona_id = ? AND anio = ?
                    ''', (self.persona_actual_id, int(anio)))
                    existe = self.db.cursor.fetchone()
                    
                    if existe:
                        self.db.cursor.execute('''
                            UPDATE historial_actas
                            SET fecha_acta = ?, hora = ?, minutos = ?, ruta_documento = ?
                            WHERE id = ?
                        ''', (fecha_acta, hora, minutos, self.ruta_documento_actual, existe[0]))
                        self.db.conn.commit()

                messagebox.showinfo(
                    "Éxito",
                    f"✅ Documento actualizado correctamente:\n\n{self.ruta_documento_actual}"
                )
                return

            # CASO 2: persona nueva o sin documento previo -> pedir dónde guardar
            nombre = self.entry_nombre.get().strip()
            dpi = self.entry_dpi.get().strip()

            # Formatear DPI sin espacios
            dpi_sin_espacios = dpi.replace(" ", "")

            # Crear nombre de archivo con formato: DPI_acta_Nombre.docx
            archivo_salida = filedialog.asksaveasfilename(
                defaultextension=".docx",
                filetypes=[("Documento Word", "*.docx")],
                initialfile=f"{dpi_sin_espacios}_acta_{nombre.replace(' ', '_')}.docx"
            )

            if not archivo_salida:
                return

            shutil.copy2(self.documento_preview, archivo_salida)
            self.ruta_documento_actual = archivo_salida

            # Guardar/actualizar historial
            if self.persona_actual_id and anio:
                dia = self.entry_dia.get().strip()
                mes = self.combo_mes.get().strip()
                hora = self.entry_hora.get().strip()
                minutos = self.entry_minutos.get().strip()
                
                fecha_acta = f"{dia}/{mes}/{anio}" if dia and mes else datetime.now().strftime("%d/%m/%Y")
                
                self.db.cursor.execute('''
                    SELECT id FROM historial_actas
                    WHERE persona_id = ? AND anio = ?
                ''', (self.persona_actual_id, int(anio)))
                existe = self.db.cursor.fetchone()
                
                if existe:
                    self.db.cursor.execute('''
                        UPDATE historial_actas
                        SET fecha_acta = ?, hora = ?, minutos = ?, ruta_documento = ?
                        WHERE id = ?
                    ''', (fecha_acta, hora, minutos, archivo_salida, existe[0]))
                    self.db.conn.commit()
                else:
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

            # Actualizar estadísticas del menú principal
            if self.callback_actualizar:
                self.callback_actualizar()
        
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar el documento:\n{str(e)}")
    
    def reemplazar_en_parrafo(self, paragraph, buscar, reemplazar, reemplazar_todas=False):
        """Reemplaza texto preservando formato (una o todas las ocurrencias)"""
        if reemplazar_todas:
            return self.reemplazar_texto_completo(paragraph, buscar, reemplazar)
        else:
            return self.reemplazar_preservando_formato(paragraph, buscar, reemplazar)
    
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
        self.ruta_documento_actual = None
        
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