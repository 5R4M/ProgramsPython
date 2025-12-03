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
from config import PLANTILLAS_DIR, COLOR_SUCCESS, COLOR_PRIMARY, COLOR_WARNING, DOCUMENTOS_DIR
from utils import NumeroATexto


class VentanaCrearDocumento:
    def __init__(self, parent, db, es_integrado=False, solo_formulario=False, modo_edicion=False):
        self.db = db
        self.es_integrado = es_integrado
        self.solo_formulario = solo_formulario
        self.modo_edicion = modo_edicion

        self.callback_actualizar = None
        self.callback_guardado = None
        self.persona_actual_id = None
        self.documento_preview = None
        self.ruta_documento_actual = None

        self.ruta_original = None
        self.nombre_original = None
        self.persona_id_original = None

        self.fecha_fija_var = ctk.BooleanVar(value=False)
        
        if es_integrado:
            # Como frame embebido en otra ventana
            self.ventana = ctk.CTkFrame(parent)
            self.ventana.pack(fill="both", expand=True)
        else:
            # Como ventana emergente
            self.ventana = ctk.CTkToplevel(parent)

            # Título según modo
            if self.solo_formulario or self.modo_edicion:
                self.ventana.title("✏️ Editar Documento")
            else:
                self.ventana.title("➕ Crear Documento")

            # Que salga activa y encima del padre
            self.ventana.transient(parent)
            self.ventana.lift()
            self.ventana.focus_force()
            self.ventana.grab_set()

        # Construir interfaz
        self.crear_interfaz()

        # Verificar plantilla
        self.verificar_plantilla()

        # Ajustar tamaño y centrar
        if not self.es_integrado:
            self.ventana.update_idletasks()
            if self.solo_formulario:
                # Modo EDICIÓN: solo formulario
                self.center_window_tamano(650, 625)
            else:
                # Modo NORMAL: con visor
                self.center_window_tamano(1400, 900)
                self.ventana.after(100, self.maximizar_ventana)
    
    # =================== VALIDADORES ===================

    def _validar_entero(self, nuevo_valor):
        """Permite solo números enteros (o vacío)."""
        if nuevo_valor == "":
            return True
        return nuevo_valor.isdigit()

    def _validar_dpi(self, nuevo_valor):
        """
        Permite solo dígitos y espacios.
        Dato final se valida con longitud en guardar/generar.
        """
        if nuevo_valor == "":
            return True
        for ch in nuevo_valor:
            if not (ch.isdigit() or ch == " "):
                return False
        return True

    def _validar_fecha_ddmmaaaa(self, nuevo_valor):
        """
        Validar SOLO al perder foco: permite vacío o una fecha DD/MM/AAAA correcta.
        """
        nuevo_valor = nuevo_valor.strip()
        if not nuevo_valor:
            return True  # permitir vacío

        if len(nuevo_valor) != 10:
            return False

        try:
            dia, mes, anio = nuevo_valor.split("/")
            if len(dia) != 2 or len(mes) != 2 or len(anio) != 4:
                return False
            dia, mes, anio = int(dia), int(mes), int(anio)
            datetime(anio, mes, dia)  # levanta error si es inválida
            return True
        except Exception:
            return False
    
    # =================== AUTOCOMPLETADO DESDE BD ===================

    class AutoCompleter:
        def __init__(self, parent_ventana, entry: ctk.CTkEntry, tipo_palabra: str):
            """
            parent_ventana: instancia de VentanaCrearDocumento (para acceder a db y ventana principal)
            entry: CTkEntry donde se escribe
            tipo_palabra: 'nombre', 'apellido', 'nacionalidad', 'domicilio', etc.
            """
            self.parent = parent_ventana
            self.entry = entry
            self.tipo_palabra = tipo_palabra

            self.popup = None  # CTkToplevel con las sugerencias
            self.sugerencias = []

            # Enlazar eventos
            self.entry.bind("<KeyRelease>", self._on_key_release)
            self.entry.bind("<FocusOut>", self._on_focus_out)
            self.entry.bind("<Down>", self._on_down_key)

        def _on_key_release(self, event):
            # Ignorar algunas teclas de navegación
            if event.keysym in ("Up", "Down", "Left", "Right", "Return", "Escape", "Tab"):
                return

            texto = self.entry.get().strip()
            if len(texto) < 2:
                self._cerrar_popup()
                return

            # Obtener sugerencias desde la BD
            self.sugerencias = self.parent.db.obtener_sugerencias_palabra(self.tipo_palabra, texto)

            if not self.sugerencias:
                self._cerrar_popup()
                return

            self._mostrar_popup()

        def _mostrar_popup(self):
            # Cerrar popup anterior si existe
            self._cerrar_popup()

            # Crear nueva ventana flotante
            self.popup = ctk.CTkToplevel(self.parent.ventana)
            self.popup.overrideredirect(True)  # sin bordes
            self.popup.attributes("-topmost", True)

            # Posicionar debajo del Entry
            self.popup.update_idletasks()
            x = self.entry.winfo_rootx()
            y = self.entry.winfo_rooty() + self.entry.winfo_height()
            self.popup.geometry(f"+{x}+{y}")

            frame = ctk.CTkFrame(self.popup)
            frame.pack(fill="both", expand=True)

            for sugerencia in self.sugerencias:
                btn = ctk.CTkButton(
                    frame,
                    text=sugerencia,
                    anchor="w",
                    command=lambda s=sugerencia: self._usar_sugerencia(s),
                    height=24
                )
                btn.pack(fill="x", padx=2, pady=1)

        def _usar_sugerencia(self, texto):
            # Reemplazar contenido del entry
            self.entry.delete(0, "end")
            self.entry.insert(0, texto)
            self._cerrar_popup()
            self.entry.focus_set()

        def _on_focus_out(self, event):
            # Cerrar popup cuando el entry pierde foco (ligero retraso para permitir clic)
            self.entry.after(150, self._cerrar_popup)

        def _on_down_key(self, event):
            # Si hay popup, enfocar el primer botón
            if self.popup and self.popup.winfo_children():
                frame = self.popup.winfo_children()[0]
                if frame.winfo_children():
                    frame.winfo_children()[0].focus_set()
            return "break"

        def _cerrar_popup(self):
            if self.popup and self.popup.winfo_exists():
                self.popup.destroy()
            self.popup = None
    
    # ==================== CONFIGURACIONES ====================

    def set_callback_actualizar(self, callback):
        """Permite establecer un callback para actualizar estadísticas"""
        self.callback_actualizar = callback

    def set_callback_guardado(self, callback):
        """Callback a llamar cuando se guarda/actualiza un documento (modo edición)."""
        self.callback_guardado = callback

    def establecer_documento_original(self, ruta_archivo, nombre_archivo, persona_id):
        """
        Define el documento original que se está editando.
        """
        self.ruta_original = ruta_archivo
        self.nombre_original = nombre_archivo
        self.persona_id_original = persona_id

        # Sincronizar con la lógica ya existente
        self.ruta_documento_actual = ruta_archivo
        self.persona_actual_id = persona_id

    def center_window_tamano(self, width, height):
        """Centra la ventana con un tamaño específico."""
        if not self.es_integrado:
            self.ventana.geometry(f"{width}x{height}")
            self.ventana.update_idletasks()
            x = (self.ventana.winfo_screenwidth() // 2) - (width // 2)
            y = (self.ventana.winfo_screenheight() // 2) - (height // 2)
            self.ventana.geometry(f"{width}x{height}+{x}+{y}")

    def maximizar_ventana(self):
        """Maximiza la ventana (solo modo normal)."""
        if not self.es_integrado:
            self.ventana.state("zoomed")

    def verificar_plantilla(self):
        """Verifica la existencia/estado de la plantilla."""
        # En modo solo_formulario no mostramos nada de plantilla.
        if self.solo_formulario:
            return

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

        # Necesario para validatecommand
        vcmd_entero = (self.ventana.register(self._validar_entero), "%P")
        vcmd_dpi = (self.ventana.register(self._validar_dpi), "%P")
        vcmd_fecha = (self.ventana.register(self._validar_fecha_ddmmaaaa), "%P")

        container = ctk.CTkFrame(self.ventana)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        container.grid_columnconfigure(0, weight=0, minsize=450)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)

        # ==== PANEL IZQUIERDO: Formulario ====
        panel_izquierdo = ctk.CTkFrame(container)
        panel_izquierdo.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        # Título
        titulo_texto = "✏️ Editar Documento" if self.solo_formulario else "➕ Crear Documento"
        ctk.CTkLabel(
            panel_izquierdo,
            text=titulo_texto,
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=5)

        # ======= SECCIÓN PLANTILLA =======
        self.lbl_plantilla = ctk.CTkLabel(
            panel_izquierdo,
            text="Verificando plantilla...",
            font=ctk.CTkFont(size=11)
        )
        self.lbl_plantilla.pack(pady=2)

        self.btn_cambiar_plantilla = ctk.CTkButton(
            panel_izquierdo,
            text="📋 Plantilla",
            command=self.cargar_plantilla,
            width=140,
            height=26
        )
        self.btn_cambiar_plantilla.pack(pady=2)

        # ----- Sección de Búsqueda Rápida -----
        self.frame_busqueda = ctk.CTkFrame(panel_izquierdo)
        self.frame_busqueda.pack(pady=3, padx=8, fill="x")

        ctk.CTkLabel(
            self.frame_busqueda,
            text="🔍 Búsqueda Rápida",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(pady=2)

        ctk.CTkLabel(
            self.frame_busqueda,
            text="Buscar persona existente",
            font=ctk.CTkFont(size=9),
            text_color="gray"
        ).pack(pady=1)

        # Búsqueda por DPI
        frame_buscar_dpi = ctk.CTkFrame(self.frame_busqueda)
        frame_buscar_dpi.pack(pady=1, padx=8, fill="x")

        frame_buscar_dpi.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frame_buscar_dpi, text="DPI:", width=55).grid(row=0, column=0, padx=(3, 2), sticky="w")
        self.entry_buscar_dpi = ctk.CTkEntry(
            frame_buscar_dpi,
            placeholder_text="2008 22829 0101",
            height=26,
            validate="key",
            validatecommand=vcmd_dpi
        )
        self.entry_buscar_dpi.grid(row=0, column=1, padx=2, sticky="ew")
        self.entry_buscar_dpi.bind("<Return>", lambda e: self.buscar_persona())

        btn_buscar = ctk.CTkButton(
            frame_buscar_dpi,
            text="🔍",
            command=self.buscar_persona,
            width=40,
            height=26
        )
        btn_buscar.grid(row=0, column=2, padx=(2, 3))

        # Búsqueda por Nombre
        frame_buscar_nombre = ctk.CTkFrame(self.frame_busqueda)
        frame_buscar_nombre.pack(pady=1, padx=8, fill="x")

        frame_buscar_nombre.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frame_buscar_nombre, text="Nombre:", width=55).grid(row=0, column=0, padx=(3, 2), sticky="w")
        self.entry_buscar_nombre = ctk.CTkEntry(
            frame_buscar_nombre,
            placeholder_text="Juan Pérez",
            height=26
        )
        self.entry_buscar_nombre.grid(row=0, column=1, padx=2, sticky="ew")
        self.entry_buscar_nombre.bind("<Return>", lambda e: self.buscar_por_nombre())

        btn_buscar_nombre = ctk.CTkButton(
            frame_buscar_nombre,
            text="🔍",
            command=self.buscar_por_nombre,
            width=40,
            height=26
        )
        btn_buscar_nombre.grid(row=0, column=2, padx=(2, 3))

        btn_limpiar = ctk.CTkButton(
            self.frame_busqueda,
            text="🔄 Limpiar",
            command=self.limpiar_campos,
            width=100,
            height=26,
            fg_color=COLOR_WARNING,
            hover_color="#e67e22"
        )
        btn_limpiar.pack(pady=2)

        # ----- Fecha y Hora -----
        frame_fecha = ctk.CTkFrame(panel_izquierdo)
        frame_fecha.pack(pady=2, padx=8, fill="x")

        ctk.CTkLabel(
            frame_fecha,
            text="🕐 Fecha y Hora",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(pady=(2, 0))

        # Check: fijar fecha manualmente
        self.chk_fecha_fija = ctk.CTkCheckBox(
            frame_fecha,
            text="Fijar fecha manualmente",
            variable=self.fecha_fija_var,
            command=self._on_cambiar_modo_fecha
        )
        self.chk_fecha_fija.pack(pady=(0, 4), padx=8, anchor="w")

        # Hora y Minutos
        frame_hora = ctk.CTkFrame(frame_fecha)
        frame_hora.pack(pady=1, fill="x", padx=8)

        frame_hora.grid_columnconfigure(1, weight=1)
        frame_hora.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(frame_hora, text="Hora:", width=55).grid(row=0, column=0, padx=(3, 2), sticky="w")
        self.entry_hora = ctk.CTkEntry(
            frame_hora,
            placeholder_text="17",
            height=26,
            validate="key",
            validatecommand=vcmd_entero
        )
        self.entry_hora.grid(row=0, column=1, padx=2, sticky="ew")

        ctk.CTkLabel(frame_hora, text="Min:", width=40).grid(row=0, column=2, padx=(8, 2), sticky="w")
        self.entry_minutos = ctk.CTkEntry(
            frame_hora,
            placeholder_text="20",
            height=26,
            validate="key",
            validatecommand=vcmd_entero
        )
        self.entry_minutos.grid(row=0, column=3, padx=(2, 3), sticky="ew")

        # Día, Mes, Año
        frame_fecha_dia = ctk.CTkFrame(frame_fecha)
        frame_fecha_dia.pack(pady=1, fill="x", padx=8)

        frame_fecha_dia.grid_columnconfigure(1, weight=1)
        frame_fecha_dia.grid_columnconfigure(3, weight=2)
        frame_fecha_dia.grid_columnconfigure(5, weight=1)

        ctk.CTkLabel(frame_fecha_dia, text="Día:", width=55).grid(row=0, column=0, padx=(3, 2), sticky="w")
        self.entry_dia = ctk.CTkEntry(
            frame_fecha_dia,
            placeholder_text="28",
            height=26,
            validate="key",
            validatecommand=vcmd_entero
        )
        self.entry_dia.grid(row=0, column=1, padx=2, sticky="ew")

        ctk.CTkLabel(frame_fecha_dia, text="Mes:", width=40).grid(row=0, column=2, padx=(8, 2), sticky="w")
        self.combo_mes = ctk.CTkComboBox(
            frame_fecha_dia,
            values=["enero", "febrero", "marzo", "abril", "mayo", "junio",
                    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
            height=26
        )
        self.combo_mes.grid(row=0, column=3, padx=2, sticky="ew")

        ctk.CTkLabel(frame_fecha_dia, text="Año:", width=40).grid(row=0, column=4, padx=(8, 2), sticky="w")
        self.entry_anio = ctk.CTkEntry(
            frame_fecha_dia,
            placeholder_text="2025",
            height=26,
            validate="key",
            validatecommand=vcmd_entero
        )
        self.entry_anio.grid(row=0, column=5, padx=(2, 3), sticky="ew")

        # Inicializar campos de fecha/hora con la fecha actual y deshabilitados (modo automático)
        self._establecer_fecha_hora_actual()
        self._actualizar_estado_campos_fecha()

        # ----- Datos personales -----
        frame_datos = ctk.CTkFrame(panel_izquierdo)
        frame_datos.pack(pady=2, padx=8, fill="x")

        ctk.CTkLabel(
            frame_datos,
            text="👤 Datos Personales",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(pady=2)

        # FUNCIÓN AUXILIAR para crear campos uniformes
        def crear_campo(parent, label_text, placeholder="", es_combo=False, valores_combo=None,
                        validar=None):
            frame = ctk.CTkFrame(parent)
            frame.pack(pady=1, fill="x", padx=8)
            frame.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(frame, text=label_text, width=100).grid(row=0, column=0, padx=(3, 2), sticky="w")

            kwargs = {"height": 26}
            if validar is not None:
                kwargs.update({"validate": "focusout", "validatecommand": validar})

            if es_combo:
                widget = ctk.CTkComboBox(frame, values=valores_combo or [], height=26)
                widget.grid(row=0, column=1, padx=(2, 3), sticky="ew")
            else:
                widget = ctk.CTkEntry(frame, placeholder_text=placeholder, **kwargs)
                widget.grid(row=0, column=1, padx=(2, 3), sticky="ew")

            return widget

        # Crear todos los campos con la función auxiliar
        self.entry_nombre = crear_campo(frame_datos, "Nombre:", "Juan Carlos Pérez López")
        self.combo_sexo = crear_campo(frame_datos, "Sexo:", es_combo=True,
                                      valores_combo=["masculino", "femenino"])
        self.combo_sexo.set("masculino")

        self.entry_fecha_nac = crear_campo(
            frame_datos,
            "Fec. Nacimiento:",
            "DD/MM/AAAA",
            validar=vcmd_fecha
        )
        self.entry_fecha_nac.bind("<FocusOut>", self.calcular_edad)
        self.entry_fecha_nac.bind("<Return>", self.calcular_edad)

        self.entry_edad = crear_campo(
            frame_datos,
            "Edad:",
            "Automático",
            validar=vcmd_entero
        )
        self.entry_edad.configure(state="readonly")

        self.combo_estado = crear_campo(
            frame_datos,
            "Estado Civil:",
            es_combo=True,
            valores_combo=["soltero", "soltera", "casado", "casada",
                           "divorciado", "divorciada", "viudo", "viuda"]
        )
        self.combo_estado.set("soltero")

        self.entry_casada = crear_campo(frame_datos, "Apell. Casada:", "de López")
        self.entry_nacionalidad = crear_campo(frame_datos, "Nacionalidad:", "guatemalteco")
        self.entry_nivel = crear_campo(frame_datos, "Nivel Académico:", "Bachiller")
        self.entry_domicilio = crear_campo(frame_datos, "Domicilio:", "departamento de Guatemala")
        self.entry_dpi = crear_campo(
            frame_datos,
            "DPI:",
            "2008 22829 0101",
            validar=vcmd_dpi
        )

        # === AUTOCOMPLETADO desde BD de sugerencias ===
        # Usamos la clase interna AutoCompleter
        self.autocomplete_nombre = self.AutoCompleter(self, self.entry_nombre, "nombre")
        self.autocomplete_casada = self.AutoCompleter(self, self.entry_casada, "apellido")
        self.autocomplete_nacionalidad = self.AutoCompleter(self, self.entry_nacionalidad, "nacionalidad")
        self.autocomplete_domicilio = self.AutoCompleter(self, self.entry_domicilio, "domicilio")
        
        # ----- Botones -----
        frame_botones = ctk.CTkFrame(panel_izquierdo)
        frame_botones.pack(pady=5, padx=8)

        frame_botones.grid_columnconfigure(0, weight=1, uniform="button")
        frame_botones.grid_columnconfigure(1, weight=1, uniform="button")
        frame_botones.grid_columnconfigure(2, weight=1, uniform="button")

        btn_guardar = ctk.CTkButton(
            frame_botones,
            text="💾 Guardar",
            command=self.guardar_persona,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLOR_PRIMARY,
            hover_color="#2980b9"
        )
        btn_guardar.grid(row=0, column=0, padx=3, sticky="ew")

        btn_preview = ctk.CTkButton(
            frame_botones,
            text="👁️ Preview",
            command=self.generar_preview,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLOR_WARNING,
            hover_color="#e67e22"
        )
        btn_preview.grid(row=0, column=1, padx=3, sticky="ew")

        btn_generar = ctk.CTkButton(
            frame_botones,
            text="✅ Generar",
            command=self.generar_documento,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLOR_SUCCESS,
            hover_color="#27ae60"
        )
        btn_generar.grid(row=0, column=2, padx=3, sticky="ew")

        # ==== PANEL DERECHO: Visor de documento ====
        if not self.solo_formulario:
            panel_derecho = ctk.CTkFrame(container)
            panel_derecho.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

            ctk.CTkLabel(
                panel_derecho,
                text="📄 Vista Previa del Documento",
                font=ctk.CTkFont(size=18, weight="bold")
            ).pack(pady=8)

            self.visor_scroll = ctk.CTkScrollableFrame(panel_derecho, width=650, height=750)
            self.visor_scroll.pack(pady=10, padx=10, fill="both", expand=True)

            self.lbl_visor_estado = ctk.CTkLabel(
                self.visor_scroll,
                text="Haga clic en 'Vista Previa' para visualizar el documento",
                text_color="gray",
                font=ctk.CTkFont(size=14)
            )
            self.lbl_visor_estado.pack(pady=200)
        else:
            self.visor_scroll = ctk.CTkFrame(container)
            self.visor_scroll.grid_forget()
            self.lbl_visor_estado = None

        # === AL FINAL: si estamos en modo solo_formulario, ocultar partes ===
        if self.solo_formulario:
            if self.frame_busqueda.winfo_manager():
                self.frame_busqueda.pack_forget()

            if self.lbl_plantilla.winfo_manager():
                self.lbl_plantilla.pack_forget()
            if self.btn_cambiar_plantilla.winfo_manager():
                self.btn_cambiar_plantilla.pack_forget()

    # ==================== LÓGICA ====================

    def _validar_fecha_nacimiento_logica(self):
        """Valida que la fecha de nacimiento (si se ingresó) tenga formato real DD/MM/AAAA."""
        fecha_nac_str = self.entry_fecha_nac.get().strip()
        if not fecha_nac_str:
            return True  # opcional

        try:
            if '/' in fecha_nac_str:
                partes = fecha_nac_str.split('/')
                if len(partes) != 3:
                    raise ValueError
                dia, mes, anio = int(partes[0]), int(partes[1]), int(partes[2])
                datetime(anio, mes, dia)
                return True
            else:
                raise ValueError
        except Exception:
            messagebox.showwarning(
                "Fecha de nacimiento inválida",
                "Por favor ingrese una fecha de nacimiento válida en formato DD/MM/AAAA."
            )
            self.entry_fecha_nac.focus_set()
            return False

    def _validar_dpi_logico(self):
        """Valida que el DPI tenga 13 dígitos (permitiendo espacios)."""
        dpi = self.entry_dpi.get().strip()
        if not dpi:
            messagebox.showwarning("Advertencia", "Debe ingresar el DPI.")
            self.entry_dpi.focus_set()
            return False

        solo_digitos = dpi.replace(" ", "")
        if not solo_digitos.isdigit() or len(solo_digitos) != 13:
            messagebox.showwarning(
                "DPI inválido",
                "El DPI debe contener exactamente 13 dígitos (puede llevar espacios)."
            )
            self.entry_dpi.focus_set()
            return False

        return True

    def _validar_fecha_hora_acta(self):
        """
        Valida que día, mes (combo), año, hora y minutos sean coherentes
        antes de generar documento/preview.
        """
        dia = self.entry_dia.get().strip()
        mes_nombre = self.combo_mes.get().strip()
        anio = self.entry_anio.get().strip()
        hora = self.entry_hora.get().strip()
        minutos = self.entry_minutos.get().strip()

        # Día y año requeridos para acta
        if not dia or not anio:
            messagebox.showwarning(
                "Fecha incompleta",
                "Debe ingresar Día y Año del acta."
            )
            return False

        # Validar enteros
        try:
            dia_int = int(dia)
            anio_int = int(anio)
        except ValueError:
            messagebox.showwarning(
                "Fecha inválida",
                "Día y Año deben ser números válidos."
            )
            return False

        # Validar rango de día (1-31) de forma genérica
        if not (1 <= dia_int <= 31):
            messagebox.showwarning("Día inválido", "El día debe estar entre 1 y 31.")
            return False

        # Validar año simple (ejemplo: >= 1900)
        if anio_int < 1900 or anio_int > 2100:
            messagebox.showwarning("Año inválido", "Ingrese un año razonable (1900-2100).")
            return False

        # Hora/minutos opcionales, pero si se ingresan que tengan formato correcto
        if hora:
            try:
                h = int(hora)
                if not (0 <= h <= 23):
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Hora inválida", "La hora debe estar entre 0 y 23.")
                return False

        if minutos:
            try:
                m = int(minutos)
                if not (0 <= m <= 59):
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Minutos inválidos", "Los minutos deben estar entre 0 y 59.")
                return False

        # Mes solo puede ser texto válido del combo (ya lo es), pero aseguramos que no esté vacío
        if not mes_nombre:
            messagebox.showwarning("Mes inválido", "Seleccione un mes válido.")
            return False

        return True

    def calcular_edad(self, event=None):
        """Calcula la edad a partir de la fecha de nacimiento"""
        fecha_nac_str = self.entry_fecha_nac.get().strip()

        if not fecha_nac_str:
            return

        try:
            if '/' in fecha_nac_str:
                partes = fecha_nac_str.split('/')
                if len(partes) == 3:
                    dia, mes, anio = int(partes[0]), int(partes[1]), int(partes[2])
                    fecha_nac = datetime(anio, mes, dia)
                else:
                    return
            else:
                return

            hoy = datetime.now()
            edad = hoy.year - fecha_nac.year

            if (hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day):
                edad -= 1

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
        
    def buscar_por_nombre(self):
        """Busca personas por nombre y permite seleccionar"""
        nombre_busqueda = self.entry_buscar_nombre.get().strip()
        
        if not nombre_busqueda:
            messagebox.showwarning("Advertencia", "Ingrese un nombre para buscar")
            return
        
        # Buscar en la base de datos
        resultados = self.db.buscar_personas_por_nombre(nombre_busqueda)
        
        if not resultados:
            messagebox.showinfo(
                "No encontrado",
                "No se encontraron personas con ese nombre.\n\n"
                "Complete los campos para crear un nuevo registro."
            )
            return
        
        if len(resultados) == 1:
            # Si solo hay un resultado, cargarlo directamente
            self.cargar_datos_persona(resultados[0])
        else:
            # Si hay múltiples resultados, mostrar ventana de selección
            self.mostrar_ventana_seleccion(resultados)

    def mostrar_ventana_seleccion(self, resultados):
        """Muestra una ventana para seleccionar entre múltiples personas"""
        ventana = ctk.CTkToplevel(self.ventana)
        ventana.title("Seleccionar Persona")
        ventana.geometry("600x400")
        ventana.transient(self.ventana)
        ventana.grab_set()
        
        ctk.CTkLabel(
            ventana,
            text=f"Se encontraron {len(resultados)} personas",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        # Frame scrollable para la lista
        frame_scroll = ctk.CTkScrollableFrame(ventana, width=560, height=280)
        frame_scroll.pack(pady=10, padx=20, fill="both", expand=True)
        
        for persona in resultados:
            # persona: (id, nombre_completo, dpi, edad, estado_civil, ...)
            frame_persona = ctk.CTkFrame(frame_scroll)
            frame_persona.pack(pady=5, padx=5, fill="x")
            
            texto = f"👤 {persona[1]}\n📋 DPI: {persona[2]}"
            if persona[3]:
                texto += f" | Edad: {persona[3]}"
            
            btn_seleccionar = ctk.CTkButton(
                frame_persona,
                text=texto,
                command=lambda p=persona: [self.cargar_datos_persona(p), ventana.destroy()],
                height=50,
                anchor="w"
            )
            btn_seleccionar.pack(fill="x", padx=5, pady=5)
        
        # Botón cancelar
        ctk.CTkButton(
            ventana,
            text="Cancelar",
            command=ventana.destroy,
            width=150
        ).pack(pady=10)

    def cargar_datos_persona(self, resultado):
        """Carga los datos de una persona en el formulario"""
        self.persona_actual_id = resultado[0]
        
        # Obtener documento existente
        self.ruta_documento_actual = None
        try:
            ruta_doc = self.db.obtener_ultimo_documento_acta(self.persona_actual_id)
            if ruta_doc and os.path.exists(ruta_doc):
                self.ruta_documento_actual = ruta_doc
        except Exception as e:
            print("Error al obtener documento:", e)
        
        # Cargar datos en los campos
        self.entry_nombre.delete(0, "end")
        if resultado[1]:
            self.entry_nombre.insert(0, resultado[1])
        
        if resultado[10]:
            self.combo_sexo.set(resultado[10])
        
        self.entry_fecha_nac.delete(0, "end")
        if resultado[11]:
            self.entry_fecha_nac.insert(0, resultado[11])
            self.calcular_edad()
        elif resultado[3]:
            self.entry_edad.configure(state="normal")
            self.entry_edad.delete(0, "end")
            self.entry_edad.insert(0, str(resultado[3]))
            self.entry_edad.configure(state="readonly")
        
        if resultado[4]:
            self.combo_estado.set(resultado[4])
        
        self.entry_nacionalidad.delete(0, "end")
        if resultado[5]:
            self.entry_nacionalidad.insert(0, resultado[5])
        
        self.entry_domicilio.delete(0, "end")
        if resultado[6]:
            self.entry_domicilio.insert(0, resultado[6])
        
        self.entry_nivel.delete(0, "end")
        if resultado[7]:
            self.entry_nivel.insert(0, resultado[7])
        
        self.entry_casada.delete(0, "end")
        if resultado[8]:
            apellido_casada = resultado[8].strip()
            textos_invalidos = ["personal de identificación", "documento personal", 
                            "identificación", "dpi", "cui"]
            es_valido = True
            apellido_lower = apellido_casada.lower()
            for texto_invalido in textos_invalidos:
                if texto_invalido in apellido_lower:
                    es_valido = False
                    break
            if es_valido and len(apellido_casada) > 0:
                self.entry_casada.insert(0, apellido_casada)
        
        self.entry_dpi.delete(0, "end")
        if resultado[2]:
            self.entry_dpi.insert(0, resultado[2])
        
        mensaje_doc = "\n\nDocumento existente cargado." if self.ruta_documento_actual else "\n\nSin documento previo."
        messagebox.showinfo("Éxito", f"Persona cargada: {resultado[1]}{mensaje_doc}")
    
    def guardar_persona(self):
        """
        Guarda o actualiza una persona en la base de datos y
        actualiza/crea su documento en la carpeta DOCUMENTOS_DIR.
        """
        if not self._validar_dpi_logico():
            return
        if not self._validar_fecha_nacimiento_logica():
            return
        
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

            # 1) Guardar/actualizar persona
            persona_id, resultado = self.db.guardar_persona(datos)
            self.persona_actual_id = persona_id

            # 1.b) Aprender sugerencias para autocompletado a partir de estos datos
            self.db.aprender_sugerencias_desde_persona(datos)

            # 2) Asegurarnos de tener un documento generado con los datos actuales
            if not self.documento_preview or not os.path.exists(self.documento_preview):
                try:
                    doc = self.crear_documento_con_datos()
                    temp_docx = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
                    temp_docx.close()
                    doc.save(temp_docx.name)
                    self.documento_preview = temp_docx.name
                except Exception as e:
                    messagebox.showwarning(
                        "Advertencia",
                        f"Persona guardada pero no se pudo generar documento automático:\n{str(e)}"
                    )
                    self.documento_preview = None

            # 3) Decidir ruta de documento en carpeta central
            os.makedirs(DOCUMENTOS_DIR, exist_ok=True)
            nombre_archivo = self._construir_nombre_archivo(nombre, dpi)
            ruta_destino = os.path.join(DOCUMENTOS_DIR, nombre_archivo)

            # CASO A: ya teníamos documento previo asociado
            if self.ruta_documento_actual and os.path.exists(self.ruta_documento_actual):
                try:
                    # Si la ruta anterior no coincide con la estándar, copiamos al estándar
                    if os.path.abspath(os.path.dirname(self.ruta_documento_actual)) != os.path.abspath(DOCUMENTOS_DIR) \
                       or os.path.basename(self.ruta_documento_actual) != nombre_archivo:

                        shutil.copy2(self.documento_preview or self.ruta_documento_actual, ruta_destino)
                        self.ruta_documento_actual = ruta_destino
                    else:
                        # Misma carpeta/nombre: sobrescribir
                        shutil.copy2(self.documento_preview or self.ruta_documento_actual, self.ruta_documento_actual)

                    # Actualizar fila de documentos en BD
                    self.db.cursor.execute(
                        "SELECT id FROM documentos WHERE persona_id = ? AND nombre_archivo = ?",
                        (persona_id, nombre_archivo)
                    )
                    fila = self.db.cursor.fetchone()
                    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    if fila:
                        self.db.cursor.execute(
                            "UPDATE documentos SET ruta_archivo = ?, fecha_carga = ? WHERE id = ?",
                            (self.ruta_documento_actual, fecha_actual, fila[0])
                        )
                    else:
                        self.db.guardar_documento(persona_id, nombre_archivo, self.ruta_documento_actual, "acta")

                    self.db.conn.commit()

                except Exception as e:
                    messagebox.showwarning(
                        "Advertencia",
                        f"Persona guardada pero no se pudo actualizar el documento en carpeta:\n{str(e)}"
                    )
            else:
                # CASO B: persona sin documento previo -> crear nuevo archivo en DOCUMENTOS_DIR
                try:
                    if self.documento_preview and os.path.exists(self.documento_preview):
                        shutil.copy2(self.documento_preview, ruta_destino)
                        self.ruta_documento_actual = ruta_destino

                        # Registrar en tabla documentos
                        self.db.guardar_documento(persona_id, nombre_archivo, ruta_destino, "acta")
                    else:
                        self.ruta_documento_actual = None
                except Exception as e:
                    messagebox.showwarning(
                        "Advertencia",
                        f"Persona guardada pero no se pudo crear el documento en carpeta:\n{str(e)}"
                    )

            # 4) Mensajes finales
            if resultado == "guardado":
                msg = "Persona registrada correctamente"
            else:
                msg = "Persona actualizada correctamente"

            if self.ruta_documento_actual:
                msg += f"\n\n✓ Documento en carpeta actualizado:\n{self.ruta_documento_actual}"

            messagebox.showinfo("Éxito", msg)

            # Actualizar estadísticas del menú principal
            if self.callback_actualizar:
                self.callback_actualizar()

        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar persona:\n{str(e)}")
    
    def generar_preview(self):
        """Genera una vista previa del documento"""
        if not self._validar_dpi_logico():
            return
        if not self._validar_fecha_nacimiento_logica():
            return
        if not self._validar_fecha_hora_acta():
            return
        
        if self.solo_formulario:
            # En modo solo_formulario no mostramos visor.
            messagebox.showinfo("Info", "En modo edición rápida no se muestra la vista previa.")
            return
        
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
                    separador.pack(pady=3)
            
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
            hora_num = int(hora)
            min_num = int(minutos)

            hora_t = NumeroATexto.convertir(hora_num)
            min_t = NumeroATexto.convertir(min_num)

            # Normalizar "uno" -> "un" en hora
            if hora_t.endswith(" y uno"):
                hora_t = hora_t[:-3] + " un"
            elif hora_t == "uno":
                hora_t = "un"

            # Normalizar "uno" -> "un" en minutos (por si lo necesitas)
            if min_t.endswith(" y uno"):
                min_t = min_t[:-3] + " un"
            elif min_t == "uno":
                min_t = "un"

            reemplazos.append((
                "diecisiete horas con veinte minutos",
                f"{hora_t} horas con {min_t} minutos"
            ))

        if dia:
            dia_num = int(dia)
            dia_t = NumeroATexto.convertir(dia_num)

            # Normalizar "uno" -> "un" en día
            if dia_t.endswith(" y uno"):
                dia_t = dia_t[:-3] + " un"
            elif dia_t == "uno":
                dia_t = "un"

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
                # Usamos reemplazar_texto_completo que ya preserva formato
                self.reemplazar_texto_completo(paragraph, buscar, reemplazar)
        
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        for buscar, reemplazar in reemplazos:
                            self.reemplazar_texto_completo(paragraph, buscar, reemplazar)
        
        return doc

    class _FakeEntry:
        def __init__(self, value=""):
            self._value = str(value)

        def get(self):
            return self._value

        def insert(self, index, value):
            # ignoramos index, simplemente reemplazamos o concatenamos
            self._value = str(value)

        def delete(self, start, end=None):
            self._value = ""

        def configure(self, **kwargs):
            # para aceptar state="readonly", etc., sin hacer nada
            pass


    class _FakeCombo:
        def __init__(self, value=""):
            self._value = str(value)

        def get(self):
            return self._value

        def set(self, value):
            self._value = str(value)

        def configure(self, **kwargs):
            pass
    
    def generar_documento(self):
        """
        Genera o actualiza el documento en la carpeta DOCUMENTOS_DIR.

        - En modo_edicion:
            * Sobrescribe el archivo existente.
            * Si cambia el nombre lógico (por nombre/DPI), renombra el archivo
              y actualiza la fila en 'documentos'.
        - En modo normal:
            * Crea/actualiza archivo estándar en DOCUMENTOS_DIR y su registro.
        """
        if not self._validar_dpi_logico():
            return
        if not self._validar_fecha_nacimiento_logica():
            return
        if not self._validar_fecha_hora_acta():
            return
        
        # Validar datos mínimos
        if not self.entry_nombre.get().strip() or not self.entry_dpi.get().strip():
            messagebox.showwarning("Advertencia", "Debe ingresar al menos el nombre y DPI")
            return

        # 1) Guardar/actualizar persona
        try:
            nombre = self.entry_nombre.get().strip()
            dpi = self.entry_dpi.get().strip()

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

            persona_id, _ = self.db.guardar_persona(datos)
            self.persona_actual_id = persona_id

        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar los datos:\n{str(e)}")
            return

        # 2) Asegurar DOCX temporal actualizado (aunque no haya visor)
        if not self.documento_preview or not os.path.exists(self.documento_preview):
            try:
                doc = self.crear_documento_con_datos()
                temp_docx = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
                temp_docx.close()
                doc.save(temp_docx.name)
                self.documento_preview = temp_docx.name
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo generar el documento:\n{str(e)}")
                return

        try:
            anio = self.entry_anio.get().strip()
            dia = self.entry_dia.get().strip()
            mes = self.combo_mes.get().strip()
            hora = self.entry_hora.get().strip()
            minutos = self.entry_minutos.get().strip()

            os.makedirs(DOCUMENTOS_DIR, exist_ok=True)

            # ======================================================
            # MODO EDICIÓN
            # ======================================================
            if self.modo_edicion and self.ruta_documento_actual:
                # 1) Sobrescribir contenido
                shutil.copy2(self.documento_preview, self.ruta_documento_actual)

                # 2) Comprobar si el nombre lógico cambia
                nombre_archivo_nuevo = self._construir_nombre_archivo(nombre, dpi)
                carpeta_actual = os.path.dirname(self.ruta_documento_actual)
                nombre_actual = os.path.basename(self.ruta_documento_actual)

                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if nombre_archivo_nuevo != nombre_actual:
                    ruta_nueva = os.path.join(carpeta_actual, nombre_archivo_nuevo)

                    # Renombrar en disco
                    os.rename(self.ruta_documento_actual, ruta_nueva)
                    self.ruta_documento_actual = ruta_nueva

                    # Actualizar fila en 'documentos'
                    # Intentar localizar por persona_id_original + nombre_original
                    if self.persona_id_original and self.nombre_original:
                        self.db.cursor.execute(
                            "SELECT id FROM documentos WHERE persona_id = ? AND nombre_archivo = ?",
                            (self.persona_id_original, self.nombre_original)
                        )
                        fila_doc = self.db.cursor.fetchone()
                    else:
                        # Fallback: buscar por persona_actual_id + ruta_original
                        self.db.cursor.execute(
                            "SELECT id FROM documentos WHERE persona_id = ? AND ruta_archivo = ?",
                            (self.persona_actual_id, self.ruta_original or self.ruta_documento_actual)
                        )
                        fila_doc = self.db.cursor.fetchone()

                    if fila_doc:
                        self.db.cursor.execute(
                            """
                            UPDATE documentos
                            SET nombre_archivo = ?, ruta_archivo = ?, fecha_carga = ?
                            WHERE id = ?
                            """,
                            (nombre_archivo_nuevo, self.ruta_documento_actual, fecha_actual, fila_doc[0])
                        )
                    else:
                        # Si no la encontramos, la insertamos nueva
                        self.db.guardar_documento(
                            self.persona_actual_id,
                            nombre_archivo_nuevo,
                            self.ruta_documento_actual,
                            "acta"
                        )
                else:
                    # Mismo nombre, solo actualizar ruta/fecha en BD
                    self.db.cursor.execute(
                        "SELECT id FROM documentos WHERE persona_id = ? AND nombre_archivo = ?",
                        (self.persona_actual_id, nombre_actual)
                    )
                    fila_doc = self.db.cursor.fetchone()
                    if fila_doc:
                        self.db.cursor.execute(
                            "UPDATE documentos SET ruta_archivo = ?, fecha_carga = ? WHERE id = ?",
                            (self.ruta_documento_actual, fecha_actual, fila_doc[0])
                        )

                # 3) Actualizar historial_actas para ese año
                if anio:
                    fecha_acta = f"{dia}/{mes}/{anio}" if dia and mes else datetime.now().strftime("%d/%m/%Y")
                    self.db.cursor.execute(
                        "SELECT id FROM historial_actas WHERE persona_id = ? AND anio = ?",
                        (self.persona_actual_id, int(anio))
                    )
                    existe = self.db.cursor.fetchone()
                    if existe:
                        self.db.cursor.execute(
                            """
                            UPDATE historial_actas
                            SET fecha_acta = ?, hora = ?, minutos = ?, ruta_documento = ?
                            WHERE id = ?
                            """,
                            (fecha_acta, hora, minutos, self.ruta_documento_actual, existe[0])
                        )
                    else:
                        self.db.guardar_historial_acta(
                            self.persona_actual_id,
                            fecha_acta,
                            hora,
                            minutos,
                            int(anio),
                            self.ruta_documento_actual
                        )

                self.db.conn.commit()

                messagebox.showinfo(
                    "Éxito",
                    f"✅ Documento editado y guardado sobre el original:\n{self.ruta_documento_actual}\n\n"
                    f"💾 Datos actualizados en la base de datos"
                )

                # Callbacks de actualización
                if self.callback_guardado:
                    self.callback_guardado()
                if self.callback_actualizar:
                    self.callback_actualizar()

                # Cerrar ventana en modo edición
                if not self.es_integrado and self.ventana:
                    self.ventana.destroy()

                return

            # ======================================================
            # MODO NORMAL (CREAR / ACTUALIZAR ESTÁNDAR)
            # ======================================================
            nombre_archivo = self._construir_nombre_archivo(nombre, dpi)
            ruta_destino = os.path.join(DOCUMENTOS_DIR, nombre_archivo)

            # CASO 1: ya tenía documento previo
            if self.persona_actual_id and self.ruta_documento_actual and os.path.exists(self.ruta_documento_actual):
                if os.path.abspath(os.path.dirname(self.ruta_documento_actual)) != os.path.abspath(DOCUMENTOS_DIR) \
                   or os.path.basename(self.ruta_documento_actual) != nombre_archivo:
                    shutil.copy2(self.documento_preview, ruta_destino)
                    self.ruta_documento_actual = ruta_destino
                else:
                    shutil.copy2(self.documento_preview, self.ruta_documento_actual)
            else:
                # CASO 2: persona nueva o sin documento previo
                shutil.copy2(self.documento_preview, ruta_destino)
                self.ruta_documento_actual = ruta_destino

            # Actualizar/crear fila en 'documentos'
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db.cursor.execute(
                "SELECT id FROM documentos WHERE persona_id = ? AND nombre_archivo = ?",
                (self.persona_actual_id, nombre_archivo)
            )
            fila = self.db.cursor.fetchone()

            if fila:
                self.db.cursor.execute(
                    "UPDATE documentos SET ruta_archivo = ?, fecha_carga = ? WHERE id = ?",
                    (self.ruta_documento_actual, fecha_actual, fila[0])
                )
            else:
                self.db.guardar_documento(self.persona_actual_id, nombre_archivo, self.ruta_documento_actual, "acta")

            # Historial por año
            if anio:
                fecha_acta = f"{dia}/{mes}/{anio}" if dia and mes else datetime.now().strftime("%d/%m/%Y")
                self.db.cursor.execute(
                    "SELECT id FROM historial_actas WHERE persona_id = ? AND anio = ?",
                    (self.persona_actual_id, int(anio))
                )
                existe = self.db.cursor.fetchone()
                if existe:
                    self.db.cursor.execute(
                        """
                        UPDATE historial_actas
                        SET fecha_acta = ?, hora = ?, minutos = ?, ruta_documento = ?
                        WHERE id = ?
                        """,
                        (fecha_acta, hora, minutos, self.ruta_documento_actual, existe[0])
                    )
                else:
                    self.db.guardar_historial_acta(
                        self.persona_actual_id,
                        fecha_acta,
                        hora,
                        minutos,
                        int(anio),
                        self.ruta_documento_actual
                    )

            self.db.conn.commit()

            messagebox.showinfo(
                "Éxito",
                f"✅ Documento generado/actualizado en carpeta central:\n{self.ruta_documento_actual}\n\n"
                f"💾 Datos guardados en la base de datos"
            )

            # Preguntar por copia
            respuesta = messagebox.askyesno(
                "Guardar copia",
                "¿Desea guardar una COPIA del documento en otra ubicación?"
            )
            if respuesta:
                archivo_copia = filedialog.asksaveasfilename(
                    defaultextension=".docx",
                    filetypes=[("Documento Word", "*.docx")],
                    initialfile=nombre_archivo
                )
                if archivo_copia:
                    try:
                        shutil.copy2(self.ruta_documento_actual, archivo_copia)
                        messagebox.showinfo(
                            "Copia guardada",
                            f"Se ha guardado una copia en:\n{archivo_copia}"
                        )
                    except Exception as e:
                        messagebox.showwarning(
                            "Advertencia",
                            f"El documento central fue generado, pero no se pudo guardar la copia:\n{str(e)}"
                        )

            if self.callback_actualizar:
                self.callback_actualizar()

        except Exception as e:
            messagebox.showerror("Error", f"Error al generar el documento:\n{str(e)}")
    
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
    
    def _construir_nombre_archivo(self, nombre, dpi):
        """
        Construye el nombre de archivo estándar:
        DPI_sinespacios_acta_Nombre_sin_espacios.docx
        """
        dpi_sin_espacios = dpi.replace(" ", "") if dpi else "sin_dpi"
        nombre_limpio = (nombre or "sin_nombre").replace(" ", "_")
        return f"{dpi_sin_espacios}_acta_{nombre_limpio}.docx"
    
    def _on_cambiar_modo_fecha(self):
        """
        Callback del CheckBox 'Fijar fecha manualmente'.
        Si está desmarcado: usar siempre fecha/hora actual (campos deshabilitados).
        Si está marcado: permitir modificar los campos manualmente.
        """
        if not self.fecha_fija_var.get():
            # Volver a la fecha actual y bloquear campos
            self._establecer_fecha_hora_actual()
        self._actualizar_estado_campos_fecha()

    def _establecer_fecha_hora_actual(self):
        """Rellena Día, Mes, Año, Hora y Min con la fecha/hora actual."""
        ahora = datetime.now()

        # Día
        self.entry_dia.delete(0, "end")
        self.entry_dia.insert(0, str(ahora.day))

        # Mes (nombre en español en minúsculas)
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                 "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        self.combo_mes.set(meses[ahora.month - 1])

        # Año
        self.entry_anio.delete(0, "end")
        self.entry_anio.insert(0, str(ahora.year))

        # Hora
        self.entry_hora.delete(0, "end")
        self.entry_hora.insert(0, str(ahora.hour))

        # Minutos (con dos dígitos opcionalmente)
        self.entry_minutos.delete(0, "end")
        self.entry_minutos.insert(0, f"{ahora.minute:02d}")

    def _actualizar_estado_campos_fecha(self):
        """
        Habilita o deshabilita los campos de fecha/hora
        según el valor de self.fecha_fija_var.
        """
        estado = "normal" if self.fecha_fija_var.get() else "disabled"

        # Hora / Min
        self.entry_hora.configure(state=estado)
        self.entry_minutos.configure(state=estado)

        # Día / Mes / Año
        self.entry_dia.configure(state=estado)
        self.combo_mes.configure(state=estado)
        self.entry_anio.configure(state=estado)
      
    def limpiar_campos(self):
        """Limpia todos los campos del formulario"""
        self.entry_buscar_dpi.delete(0, "end")
        self.entry_buscar_nombre.delete(0, "end")  # NUEVO
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