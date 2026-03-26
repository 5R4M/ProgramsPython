import customtkinter as ctk
from tkinter import messagebox
import os
from PIL import Image, ImageTk
import fitz  # PyMuPDF
import tempfile
from docx2pdf import convert
from config import (
    COLOR_SUCCESS,
    COLOR_PRIMARY,
    DOCUMENTOS_DIR,
    # ✅ CONSTANTES RESPONSIVAS
    FONT_SIZE_TITLE,
    FONT_SIZE_SUBTITLE,
    FONT_SIZE_NORMAL,
    FONT_SIZE_SMALL,
    FONT_SIZE_TINY,
    FONT_SIZE_BUTTON,
    ICON_SIZE_BUTTON,
    PADDING_LARGE,
    PADDING_MEDIUM,
    PADDING_SMALL,
    PADDING_TINY,
    BUTTON_HEIGHT_SMALL,
    INPUT_HEIGHT,
    CARD_CORNER_RADIUS,
    VISOR_WIDTH,
    VISOR_HEIGHT,
    # ✅ FUNCIONES AUXILIARES RESPONSIVAS
    escalar,
    es_pantalla_pequena,
)
from models import Persona
from ui.crear_documento import VentanaCrearDocumento
import json
from pathlib import Path
import re
from docx import Document

class CacheAños:
    """Cache persistente para años de documentos"""
  
    def __init__(self, cache_file="cache_años_busqueda.json"):
        self.cache_file = Path(DOCUMENTOS_DIR) / cache_file
        self.cache = self._cargar_cache()
  
    def _cargar_cache(self):
        """Carga el cache desde disco"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:  # noqa: E722
                return {}
        return {}
  
    def _guardar_cache(self):
        """Guarda el cache a disco"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error al guardar cache: {e}")
  
    def obtener_año(self, ruta_archivo):
        """Obtiene el año de un documento usando cache"""
        import datetime
      
        nombre = os.path.basename(ruta_archivo)
      
        try:
            mtime = os.path.getmtime(ruta_archivo)
            cache_key = f"{nombre}_{int(mtime)}"
          
            if cache_key in self.cache:
                return self.cache[cache_key]
          
            año = self._extraer_año_rapido(ruta_archivo)
          
            self.cache[cache_key] = año
            self._guardar_cache()
          
            return año
          
        except Exception as e:
            print(f"Error obteniendo año de {nombre}: {e}")
            return datetime.datetime.now().year
  
    def _extraer_año_rapido(self, ruta_archivo):
        """Extrae SOLO el año del documento de forma rápida"""
        import datetime
      
        año = None
      
        try:
            if ruta_archivo.lower().endswith('.docx'):
                doc = Document(ruta_archivo)
              
                texto_busqueda = ""
                for i, para in enumerate(doc.paragraphs[:5]):
                    texto_busqueda += para.text + " "
                    if i >= 4:
                        break
              
                matches = re.findall(r'\b(20\d{2})\b', texto_busqueda)
              
                if matches:
                    año = int(matches[0])
      
        except Exception as e:
            print(f"Error extrayendo año: {e}")
      
        if not año:
            try:
                mtime = os.path.getmtime(ruta_archivo)
                año = datetime.datetime.fromtimestamp(mtime).year
            except:  # noqa: E722
                año = datetime.datetime.now().year
      
        return año

class VentanaBuscarDocumento:
    def __init__(self, parent, db, es_integrado=False):
        self.db = db
        self.es_integrado = es_integrado
        self.callback_actualizar = None
        self.persona_seleccionada = None
      
        self.todos_documentos = []    
        self.resultados_busqueda = [] 
      
        self._carga_activa = False
        self._cache_años = CacheAños()
      
        self.cargar_iconos()
      
        if es_integrado:
            self.ventana = ctk.CTkFrame(parent, fg_color="#001a33")
            self.ventana.pack(fill="both", expand=True)
        else:
            self.ventana = ctk.CTkToplevel(parent)
            self.ventana.title("🔍 Buscar Documento")
            self.ventana.configure(fg_color="#001a33")
            self.ventana.protocol("WM_DELETE_WINDOW", self.cerrar_ventana)
            
            # ✅ Solo maximizar si no es pantalla pequeña
            if not es_pantalla_pequena():
                self.ventana.after(100, self.maximizar_ventana)
            else:
                self.ventana.after(100, self.center_window)
      
        self.crear_interfaz()
        self.cargar_todos_documentos_iniciales()
      
    def cargar_iconos(self):
        """Carga los iconos PNG para los botones - ✅ USANDO CONSTANTES RESPONSIVAS"""
        try:
            ruta_base = os.path.dirname(os.path.abspath(__file__))
            ruta_proyecto = os.path.dirname(ruta_base)
            ruta_iconos = os.path.join(ruta_proyecto, "utils", "iconos")
          
            print(f"🔍 Buscando iconos en: {ruta_iconos}")
          
            if not os.path.exists(ruta_iconos):
                print(f"⚠️ La carpeta de iconos no existe: {ruta_iconos}")
                raise FileNotFoundError(f"No existe la carpeta: {ruta_iconos}")
          
            # ✅ USAR ICON_SIZE_BUTTON (tamaño escalado automáticamente)
            self.icono_buscar = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "buscar.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "buscar.png")),
                size=ICON_SIZE_BUTTON
            )
          
            self.icono_seleccionar = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "seleccionar.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "seleccionar.png")),
                size=ICON_SIZE_BUTTON
            )
          
            self.icono_editar = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "editar.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "editar.png")),
                size=ICON_SIZE_BUTTON
            )
          
            self.icono_ver = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "ver.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "ver.png")),
                size=ICON_SIZE_BUTTON
            )
          
            print("✅ Iconos cargados correctamente en buscar_documento")
          
        except Exception as e:
            print(f"⚠️ Error al cargar iconos: {e}")
            self.icono_buscar = None
            self.icono_seleccionar = None
            self.icono_editar = None
            self.icono_ver = None
  
    def set_callback_actualizar(self, callback):
        """Permite establecer un callback para actualizar estadísticas"""
        self.callback_actualizar = callback
  
    def maximizar_ventana(self):
        """Maximiza la ventana"""
        if not self.es_integrado:
            self.ventana.state('zoomed')
  
    def center_window(self):
        """Centra la ventana en la pantalla - ✅ USANDO CONSTANTES ESCALADAS"""
        if not self.es_integrado:
            # ✅ Usar valores escalados automáticamente
            from config import WINDOW_WIDTH, WINDOW_HEIGHT
            width = int(WINDOW_WIDTH * 0.9)
            height = int(WINDOW_HEIGHT * 0.9)
            
            self.ventana.geometry(f"{width}x{height}")
            self.ventana.update_idletasks()
            x = (self.ventana.winfo_screenwidth() // 2) - (width // 2)
            y = (self.ventana.winfo_screenheight() // 2) - (height // 2)
            self.ventana.geometry(f'{width}x{height}+{x}+{y}')
  
    def crear_interfaz(self):
        """Versión FINAL con altura limitada en resultados"""
        
        # Frame principal con dos columnas
        container = ctk.CTkFrame(self.ventana, fg_color="#001a33")
        container.pack(fill="both", expand=True, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
        
        container.grid_columnconfigure(0, weight=3) 
        container.grid_columnconfigure(1, weight=2)
        container.grid_rowconfigure(0, weight=1)
        
        # ===== PANEL IZQUIERDO - SCROLLABLE =====
        panel_izquierdo = ctk.CTkScrollableFrame(
            container, 
            fg_color="#003d66",
            width=escalar(750)
        )
        panel_izquierdo.grid(row=0, column=0, sticky="nsew", padx=(0, PADDING_TINY))
        
        # Título
        ctk.CTkLabel(
            panel_izquierdo,
            text="🔍 Buscar Documento",
            font=ctk.CTkFont(size=FONT_SIZE_TITLE, weight="bold")
        ).pack(pady=PADDING_MEDIUM)
        
        # ===== FRAME DE BÚSQUEDA (COMPACTO) =====
        frame_busqueda = ctk.CTkFrame(panel_izquierdo, fg_color="#003d66")
        frame_busqueda.pack(pady=PADDING_SMALL, padx=PADDING_MEDIUM, fill="x")
        
        # Búsqueda por DPI
        ctk.CTkLabel(
            frame_busqueda,
            text="Buscar por DPI:",
            font=ctk.CTkFont(size=FONT_SIZE_NORMAL, weight="bold")
        ).pack(pady=(PADDING_SMALL, PADDING_TINY), anchor="w", padx=PADDING_SMALL)
        
        frame_dpi = ctk.CTkFrame(frame_busqueda, fg_color="#003d66")
        frame_dpi.pack(pady=PADDING_TINY, padx=PADDING_SMALL, fill="x")
        
        self.entry_dpi = ctk.CTkEntry(
            frame_dpi,
            placeholder_text="Ej: 2008 22829 0101",
            font=ctk.CTkFont(size=FONT_SIZE_NORMAL),
            height=INPUT_HEIGHT,
            fg_color="#001a33",
            border_color="#005187"
        )
        self.entry_dpi.pack(side="left", padx=PADDING_TINY, expand=True, fill="x")
        self.entry_dpi.bind("<Return>", lambda e: self.buscar_por_dpi())
        
        btn_buscar_dpi = ctk.CTkButton(
            frame_dpi,
            text="Buscar",
            image=self.icono_buscar,
            compound="left",
            command=self.buscar_por_dpi,
            width=escalar(100),
            height=BUTTON_HEIGHT_SMALL,
            font=ctk.CTkFont(size=FONT_SIZE_BUTTON),
            fg_color="#005187",
            hover_color="#2d5f8d"
        )
        btn_buscar_dpi.pack(side="left", padx=PADDING_TINY)
        
        # Separador
        ctk.CTkLabel(
            frame_busqueda,
            text="O",
            font=ctk.CTkFont(size=FONT_SIZE_SMALL),
            text_color="gray"
        ).pack(pady=PADDING_SMALL)
        
        # Búsqueda por nombre
        ctk.CTkLabel(
            frame_busqueda,
            text="Buscar por Nombre:",
            font=ctk.CTkFont(size=FONT_SIZE_NORMAL, weight="bold")
        ).pack(pady=(PADDING_SMALL, PADDING_TINY), anchor="w", padx=PADDING_SMALL)
        
        frame_nombre = ctk.CTkFrame(frame_busqueda, fg_color="#003d66")
        frame_nombre.pack(pady=PADDING_TINY, padx=PADDING_SMALL, fill="x")
        
        self.entry_nombre = ctk.CTkEntry(
            frame_nombre,
            placeholder_text="Ej: Juan Pérez",
            font=ctk.CTkFont(size=FONT_SIZE_NORMAL),
            height=INPUT_HEIGHT,
            fg_color="#001a33",
            border_color="#005187"
        )
        self.entry_nombre.pack(side="left", padx=PADDING_TINY, expand=True, fill="x")
        self.entry_nombre.bind("<Return>", lambda e: self.buscar_por_nombre())
        
        btn_buscar_nombre = ctk.CTkButton(
            frame_nombre,
            text="Buscar",
            image=self.icono_buscar,
            compound="left",
            command=self.buscar_por_nombre,
            width=escalar(100),
            height=BUTTON_HEIGHT_SMALL,
            font=ctk.CTkFont(size=FONT_SIZE_BUTTON),
            fg_color="#005187",
            hover_color="#2d5f8d"
        )
        btn_buscar_nombre.pack(side="left", padx=PADDING_TINY)

        # Selector de año
        frame_filtro_año = ctk.CTkFrame(frame_busqueda, fg_color="transparent")
        frame_filtro_año.pack(pady=(PADDING_SMALL, PADDING_TINY), padx=PADDING_SMALL, fill="x")

        ctk.CTkLabel(
            frame_filtro_año,
            text="📅 Año:",
            font=ctk.CTkFont(size=FONT_SIZE_SMALL, weight="bold")
        ).pack(side="left", padx=(0, PADDING_SMALL))

        self.combo_año_busqueda = ctk.CTkComboBox(
            frame_filtro_año,
            values=["Todos"],
            command=self.filtrar_busqueda_por_año,
            width=escalar(100),
            height=INPUT_HEIGHT - escalar(5),
            font=ctk.CTkFont(size=FONT_SIZE_SMALL),
            fg_color="#001a33",
            border_color="#005187",
            button_color="#005187",
            button_hover_color="#2d5f8d",
            state="readonly"
        )
        self.combo_año_busqueda.pack(side="left")
        self.combo_año_busqueda.set("Todos")

        # ===== RESULTADOS (CON ALTURA LIMITADA Y SCROLL) =====
        ctk.CTkLabel(
            panel_izquierdo,
            text="Resultados de búsqueda:",
            font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight="bold")
        ).pack(pady=(PADDING_SMALL, PADDING_TINY), padx=PADDING_MEDIUM, anchor="w")
        
        # ✅ CLAVE: ScrollableFrame con altura fija (5-6 resultados visibles)
        if es_pantalla_pequena():
            altura_resultados = escalar(250)  # ~4-5 resultados
        else:
            altura_resultados = escalar(320)  # ~5-6 resultados
        
        self.resultados_frame = ctk.CTkScrollableFrame(
            panel_izquierdo, 
            fg_color="#001a33",
            height=altura_resultados  # ✅ ALTURA FIJA
        )
        self.resultados_frame.pack(pady=PADDING_TINY, padx=PADDING_MEDIUM, fill="x", expand=False)

        self.lbl_sin_resultados = ctk.CTkLabel(
            self.resultados_frame,
            text="Realice una búsqueda para ver resultados",
            text_color="gray",
            font=ctk.CTkFont(size=FONT_SIZE_NORMAL)
        )
        self.lbl_sin_resultados.pack(pady=escalar(50))

        # ===== INFO DE PERSONA (VISIBLE CON PLACEHOLDER) =====
        self.info_frame = ctk.CTkFrame(
            panel_izquierdo, 
            fg_color="#003d66",
            corner_radius=8
        )
        self.info_frame.pack(pady=PADDING_SMALL, padx=PADDING_MEDIUM, fill="x")
        
        # Placeholder inicial
        self.lbl_info_placeholder = ctk.CTkLabel(
            self.info_frame,
            text="Seleccione una persona para ver su información",
            text_color="gray",
            font=ctk.CTkFont(size=FONT_SIZE_SMALL)
        )
        self.lbl_info_placeholder.pack(pady=PADDING_SMALL)

        # ===== DOCUMENTOS (SIN ALTURA FIJA - SE ADAPTA) =====
        ctk.CTkLabel(
            panel_izquierdo,
            text="Documentos de la persona:",
            font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight="bold")
        ).pack(pady=(PADDING_SMALL, PADDING_TINY), padx=PADDING_MEDIUM, anchor="w")

        # ✅ Frame normal sin altura fija (usa el scroll del panel)
        self.documentos_frame = ctk.CTkFrame(
            panel_izquierdo, 
            fg_color="#001a33"
        )
        self.documentos_frame.pack(pady=PADDING_TINY, padx=PADDING_MEDIUM, fill="x")

        self.lbl_sin_documentos = ctk.CTkLabel(
            self.documentos_frame,
            text="Seleccione una persona para ver sus documentos",
            text_color="gray",
            font=ctk.CTkFont(size=FONT_SIZE_SMALL)
        )
        self.lbl_sin_documentos.pack(pady=escalar(30))
        
        # ===== PANEL DERECHO: Visor =====
        panel_derecho = ctk.CTkFrame(container, fg_color="#003d66")
        panel_derecho.grid(row=0, column=1, sticky="nsew", padx=(PADDING_TINY, 0))
        
        ctk.CTkLabel(
            panel_derecho,
            text="📄 Vista Previa del Documento",
            font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight="bold")
        ).pack(pady=PADDING_MEDIUM)
        
        self.visor_scroll = ctk.CTkScrollableFrame(
            panel_derecho, 
            width=VISOR_WIDTH, 
            height=VISOR_HEIGHT,
            fg_color="#001a33"
        )
        self.visor_scroll.pack(pady=PADDING_MEDIUM, padx=PADDING_MEDIUM, fill="both", expand=True)
        
        self.lbl_visor_estado = ctk.CTkLabel(
            self.visor_scroll,
            text="Seleccione un documento para visualizar",
            text_color="gray",
            font=ctk.CTkFont(size=FONT_SIZE_NORMAL)
        )
        self.lbl_visor_estado.pack(pady=escalar(200))

    def cargar_todos_documentos_iniciales(self):
        """VERSIÓN OPTIMIZADA - Carga todos los documentos al iniciar"""
        import datetime
      
        self._carga_activa = True
      
        if not hasattr(self, '_cache_años'):
            self._cache_años = CacheAños()
      
        self.todos_documentos = []
        documentos_por_año_temp = {}
      
        directorio_docs = DOCUMENTOS_DIR
      
        if not os.path.exists(directorio_docs):
            self._carga_activa = False
            return
      
        try:
            todas_personas = self.db.obtener_todas_personas()
          
            if not todas_personas:
                self._carga_activa = False
                return
          
            personas_por_dpi = {}
            for persona in todas_personas:
                persona_id = persona[0]
                nombre_completo = persona[1]
                dpi = persona[2]
                dpi_normalizado = self.normalizar_dpi(dpi)
                personas_por_dpi[dpi_normalizado.lower()] = (persona_id, nombre_completo, dpi)
          
            archivos = [
                f for f in os.listdir(directorio_docs)
                if f.lower().endswith(('.docx', '.pdf'))
            ]
          
            BATCH_SIZE = 10
            total_archivos = len(archivos)
          
            def procesar_batch(inicio):
                try:
                    if not self._carga_activa:
                        return
                  
                    if not hasattr(self, 'ventana') or not self.ventana.winfo_exists():
                        self._carga_activa = False
                        return
                  
                    fin = min(inicio + BATCH_SIZE, total_archivos)
                  
                    for archivo in archivos[inicio:fin]:
                        if not self._carga_activa:
                            return
                      
                        archivo_normalizado = archivo.replace(" ", "").replace("_", "").replace("-", "").lower()
                      
                        persona_info = None
                        for dpi_norm, info in personas_por_dpi.items():
                            if dpi_norm in archivo_normalizado:
                                persona_info = info
                                break
                      
                        if not persona_info:
                            continue
                      
                        persona_id, nombre_completo, dpi = persona_info
                        ruta_completa = os.path.join(directorio_docs, archivo)
                      
                        año = self._cache_años.obtener_año(ruta_completa)
                      
                        try:
                            mtime = os.path.getmtime(ruta_completa)
                            fecha_obj = datetime.datetime.fromtimestamp(mtime)
                            fecha_str = fecha_obj.strftime("%Y-%m-%d %H:%M:%S")
                        except OSError:
                            fecha_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                      
                        extension = archivo.lower().split('.')[-1].upper()
                      
                        doc_info = (None, archivo, ruta_completa, fecha_str, extension, persona_id, año, nombre_completo)
                        self.todos_documentos.append(doc_info)
                      
                        if año not in documentos_por_año_temp:
                            documentos_por_año_temp[año] = []
                        documentos_por_año_temp[año].append(doc_info)
                  
                    if self._carga_activa and hasattr(self, 'lbl_progreso_carga') and self.lbl_progreso_carga.winfo_exists():
                        progreso = int((fin / total_archivos) * 100)
                        self.lbl_progreso_carga.configure(
                            text=f"⏳ Cargando documentos... {progreso}% ({fin}/{total_archivos})"
                        )
                  
                    if self._carga_activa and hasattr(self, 'ventana') and self.ventana.winfo_exists():
                        self.ventana.update_idletasks()
                  
                    if fin < total_archivos and self._carga_activa:
                        if hasattr(self, 'ventana') and self.ventana.winfo_exists():
                            self.ventana.after(50, lambda: procesar_batch(fin))
                    else:
                        if self._carga_activa:
                            self._finalizar_carga_inicial(documentos_por_año_temp)
              
                except Exception as e:
                    print(f"Error en procesar_batch: {e}")
                    import traceback
                    traceback.print_exc()
                    self._carga_activa = False
                    try:
                        self._finalizar_carga_inicial(documentos_por_año_temp)
                    except:  # noqa: E722
                        pass
          
            if hasattr(self, 'resultados_frame'):
                for widget in self.resultados_frame.winfo_children():
                    widget.destroy()
              
                self.lbl_progreso_carga = ctk.CTkLabel(
                    self.resultados_frame,
                    text="⏳ Cargando documentos... 0%",
                    font=ctk.CTkFont(size=FONT_SIZE_NORMAL),
                    text_color="orange"
                )
                self.lbl_progreso_carga.pack(pady=escalar(50))
          
            procesar_batch(0)
      
        except Exception as e:
            print(f"Error al cargar documentos iniciales: {e}")
            import traceback
            traceback.print_exc()
            self._carga_activa = False

    def _finalizar_carga_inicial(self, documentos_por_año_temp):
        """Finaliza la carga y actualiza la UI"""
        try:
            if not self._carga_activa:
                return
          
            if hasattr(self, 'lbl_progreso_carga') and self.lbl_progreso_carga.winfo_exists():
                self.lbl_progreso_carga.destroy()
                delattr(self, 'lbl_progreso_carga')
          
            if documentos_por_año_temp:
                años_disponibles = sorted(documentos_por_año_temp.keys(), reverse=True)
                valores_combo = ["Todos"] + [str(año) for año in años_disponibles]
              
                if hasattr(self, 'combo_año_busqueda') and self.combo_año_busqueda.winfo_exists():
                    self.combo_año_busqueda.configure(values=valores_combo)
                    self.combo_año_busqueda.set("Todos")
              
                self.documentos_por_año_busqueda = documentos_por_año_temp
                self.mostrar_documentos_iniciales(documentos_por_año_temp)
            else:
                if hasattr(self, 'resultados_frame') and self.resultados_frame.winfo_exists():
                    for widget in self.resultados_frame.winfo_children():
                        widget.destroy()
                  
                    ctk.CTkLabel(
                        self.resultados_frame,
                        text="No hay documentos registrados",
                        text_color="gray",
                        font=ctk.CTkFont(size=FONT_SIZE_NORMAL)
                    ).pack(pady=escalar(50))
              
                if hasattr(self, 'combo_año_busqueda') and self.combo_año_busqueda.winfo_exists():
                    self.combo_año_busqueda.configure(values=["Todos"])
                    self.combo_año_busqueda.set("Todos")
          
            self._carga_activa = False
      
        except Exception as e:
            print(f"Error en _finalizar_carga_inicial: {e}")
            import traceback
            traceback.print_exc()
            self._carga_activa = False
    
    def mostrar_documentos_iniciales(self, documentos_por_año_temp):
        """Muestra todos los documentos iniciales agrupados por año"""
        for widget in self.resultados_frame.winfo_children():
            widget.destroy()
      
        años_ordenados = sorted(documentos_por_año_temp.keys(), reverse=True)
      
        for año in años_ordenados:
            ctk.CTkLabel(
                self.resultados_frame,
                text=f"📅 Documentos de {año}",
                font=ctk.CTkFont(size=FONT_SIZE_NORMAL, weight="bold"),
                text_color=COLOR_PRIMARY
            ).pack(pady=(PADDING_MEDIUM, PADDING_MEDIUM), padx=PADDING_MEDIUM, anchor="w")
          
            documentos_año = sorted(
                documentos_por_año_temp[año],
                key=lambda x: x[3],
                reverse=True
            )
          
            for doc in documentos_año:
                doc_id, nombre_archivo, ruta_archivo, fecha_carga, tipo_documento, persona_id, año_doc, nombre_persona = doc
              
                frame_doc = ctk.CTkFrame(self.resultados_frame, corner_radius=CARD_CORNER_RADIUS, fg_color="#003d66")
                frame_doc.pack(pady=PADDING_TINY, padx=PADDING_MEDIUM, fill="x")
              
                info_doc = f"📄 {nombre_archivo}\n👤 {nombre_persona}\n📅 {fecha_carga} | {tipo_documento}"
              
                ctk.CTkLabel(
                    frame_doc,
                    text=info_doc,
                    anchor="w",
                    justify="left",
                    font=ctk.CTkFont(size=FONT_SIZE_TINY)
                ).pack(side="left", padx=PADDING_MEDIUM, pady=PADDING_TINY, expand=True, fill="x")
              
                btn_seleccionar = ctk.CTkButton(
                    frame_doc,
                    text="Seleccionar",
                    image=self.icono_seleccionar,
                    compound="left",
                    command=lambda pid=persona_id: self.seleccionar_persona_por_id(pid),
                    width=escalar(130),
                    height=BUTTON_HEIGHT_SMALL,
                    font=ctk.CTkFont(size=FONT_SIZE_BUTTON),
                    fg_color="#005187",
                    hover_color="#2d5f8d"
                )
                btn_seleccionar.pack(side="right", padx=PADDING_TINY)
          
            if año != años_ordenados[-1]:
                ctk.CTkFrame(
                    self.resultados_frame,
                    height=2,
                    fg_color="gray"
                ).pack(pady=PADDING_MEDIUM, padx=PADDING_LARGE, fill="x")

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
            self.resultados_busqueda = resultados
            self.cargar_todos_documentos_busqueda(resultados)
            self.mostrar_resultados(resultados)
        else:
            self.mostrar_sin_resultados()
            messagebox.showinfo(
                "No encontrado",
                "No se encontraron personas con ese nombre.\n\n"
                "Puede crear un nuevo documento desde el menú principal."
            )
    
    def cargar_todos_documentos_busqueda(self, resultados):
        """VERSIÓN OPTIMIZADA - Carga documentos de las personas encontradas"""
        import datetime
        
        if not hasattr(self, '_cache_años'):
            self._cache_años = CacheAños()
        
        self.todos_documentos = []
        documentos_por_año_temp = {}
        
        directorio_docs = DOCUMENTOS_DIR
        
        if not os.path.exists(directorio_docs):
            return
        
        try:
            personas_map = {}
            for resultado in resultados:
                persona = Persona.from_tuple(resultado)
                dpi_normalizado = self.normalizar_dpi(persona.dpi)
                personas_map[dpi_normalizado.lower()] = persona
            
            archivos = [
                f for f in os.listdir(directorio_docs)
                if f.lower().endswith(('.docx', '.pdf'))
            ]
            
            for archivo in archivos:
                archivo_normalizado = archivo.replace(" ", "").replace("_", "").replace("-", "").lower()
                
                persona_encontrada = None
                for dpi_norm, persona in personas_map.items():
                    if dpi_norm in archivo_normalizado:
                        persona_encontrada = persona
                        break
                
                if not persona_encontrada:
                    continue
                
                ruta_completa = os.path.join(directorio_docs, archivo)
                año = self._cache_años.obtener_año(ruta_completa)
                
                try:
                    fecha_modificacion = os.path.getmtime(ruta_completa)
                    fecha_obj = datetime.datetime.fromtimestamp(fecha_modificacion)
                    fecha_str = fecha_obj.strftime("%Y-%m-%d %H:%M:%S")
                except OSError:
                    fecha_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                extension = archivo.lower().split('.')[-1].upper()
                
                doc_info = (None, archivo, ruta_completa, fecha_str, extension, persona_encontrada.id, año, persona_encontrada.nombre_completo)
                self.todos_documentos.append(doc_info)
                
                if año not in documentos_por_año_temp:
                    documentos_por_año_temp[año] = []
                documentos_por_año_temp[año].append(doc_info)
            
            if documentos_por_año_temp:
                años_disponibles = sorted(documentos_por_año_temp.keys(), reverse=True)
                valores_combo = ["Todos"] + [str(año) for año in años_disponibles]
                self.combo_año_busqueda.configure(values=valores_combo)
                self.combo_año_busqueda.set("Todos")
                
                self.documentos_por_año_busqueda = documentos_por_año_temp
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
        
        if hasattr(self, 'documentos_por_año_busqueda'):
            self.mostrar_documentos_busqueda_por_año(año_str, self.documentos_por_año_busqueda)
        else:
            documentos_por_año_temp = {}
            for doc in self.todos_documentos:
                año = doc[6]
                if año not in documentos_por_año_temp:
                    documentos_por_año_temp[año] = []
                documentos_por_año_temp[año].append(doc)
            
            self.mostrar_documentos_busqueda_por_año(año_str, documentos_por_año_temp)
    
    def mostrar_documentos_busqueda_por_año(self, año_str, documentos_por_año_temp):
        """Muestra los documentos de búsqueda filtrados por año"""
        for widget in self.resultados_frame.winfo_children():
            widget.destroy()
        
        if año_str == "Todos":
            años_ordenados = sorted(documentos_por_año_temp.keys(), reverse=True)
            
            for año in años_ordenados:
                ctk.CTkLabel(
                    self.resultados_frame,
                    text=f"📅 Documentos de {año}",
                    font=ctk.CTkFont(size=FONT_SIZE_NORMAL, weight="bold"),
                    text_color=COLOR_PRIMARY
                ).pack(pady=(PADDING_MEDIUM, PADDING_SMALL), padx=PADDING_SMALL, anchor="w")
                
                documentos_año = sorted(
                    documentos_por_año_temp[año],
                    key=lambda x: x[3],
                    reverse=True
                )
                
                for doc in documentos_año:
                    doc_id, nombre_archivo, ruta_archivo, fecha_carga, tipo_documento, persona_id, año_doc, nombre_persona = doc
                    
                    frame_doc = ctk.CTkFrame(self.resultados_frame, fg_color="#003d66", corner_radius=CARD_CORNER_RADIUS)
                    frame_doc.pack(pady=PADDING_TINY, padx=PADDING_SMALL, fill="x")
                    
                    info_doc = f"📄 {nombre_archivo}\n👤 {nombre_persona}\n📅 {fecha_carga} | {tipo_documento}"
                    
                    ctk.CTkLabel(
                        frame_doc,
                        text=info_doc,
                        anchor="w",
                        justify="left",
                        font=ctk.CTkFont(size=FONT_SIZE_TINY)
                    ).pack(side="left", padx=PADDING_SMALL, pady=PADDING_TINY, expand=True, fill="x")
                    
                    btn_seleccionar = ctk.CTkButton(
                        frame_doc,
                        text="Seleccionar",
                        image=self.icono_seleccionar,
                        compound="left",
                        command=lambda pid=persona_id: self.seleccionar_persona_por_id(pid),
                        width=escalar(130),
                        height=BUTTON_HEIGHT_SMALL,
                        font=ctk.CTkFont(size=FONT_SIZE_BUTTON),
                        fg_color="#005187",
                        hover_color="#2d5f8d"
                    )
                    btn_seleccionar.pack(side="right", padx=PADDING_TINY)
                
                ctk.CTkFrame(
                    self.resultados_frame,
                    height=2,
                    fg_color="gray"
                ).pack(pady=PADDING_SMALL, padx=PADDING_MEDIUM, fill="x")
        
        else:
            año = int(año_str)
            
            if año in documentos_por_año_temp:
                ctk.CTkLabel(
                    self.resultados_frame,
                    text=f"📅 Documentos de {año}",
                    font=ctk.CTkFont(size=FONT_SIZE_NORMAL, weight="bold"),
                    text_color=COLOR_PRIMARY
                ).pack(pady=(PADDING_SMALL, PADDING_MEDIUM), padx=PADDING_SMALL, anchor="w")
                
                documentos_año = sorted(
                    documentos_por_año_temp[año],
                    key=lambda x: x[3],
                    reverse=True
                )
                
                for doc in documentos_año:
                    doc_id, nombre_archivo, ruta_archivo, fecha_carga, tipo_documento, persona_id, año_doc, nombre_persona = doc
                    
                    frame_doc = ctk.CTkFrame(self.resultados_frame, fg_color="#003d66", corner_radius=CARD_CORNER_RADIUS)
                    frame_doc.pack(pady=PADDING_TINY, padx=PADDING_SMALL, fill="x")
                    
                    info_doc = f"📄 {nombre_archivo}\n👤 {nombre_persona}\n📅 {fecha_carga} | {tipo_documento}"
                    
                    ctk.CTkLabel(
                        frame_doc,
                        text=info_doc,
                        anchor="w",
                        justify="left",
                        font=ctk.CTkFont(size=FONT_SIZE_TINY)
                    ).pack(side="left", padx=PADDING_SMALL, pady=PADDING_TINY, expand=True, fill="x")
                    
                    btn_seleccionar = ctk.CTkButton(
                        frame_doc,
                        text="Seleccionar",
                        image=self.icono_seleccionar,
                        compound="left",
                        command=lambda pid=persona_id: self.seleccionar_persona_por_id(pid),
                        width=escalar(130),
                        height=BUTTON_HEIGHT_SMALL,
                        font=ctk.CTkFont(size=FONT_SIZE_BUTTON),
                        fg_color="#005187",
                        hover_color="#2d5f8d"
                    )
                    btn_seleccionar.pack(side="right", padx=PADDING_TINY)
        
    def mostrar_sin_resultados(self):
        """Muestra mensaje cuando no hay resultados"""
        for widget in self.resultados_frame.winfo_children():
            widget.destroy()
        
        self.lbl_sin_resultados = ctk.CTkLabel(
            self.resultados_frame,
            text="No se encontraron resultados",
            text_color="orange",
            font=ctk.CTkFont(size=FONT_SIZE_NORMAL)
        )
        self.lbl_sin_resultados.pack(pady=escalar(50))
        
        # ✅ REEMPLAZAR CON:
        for widget in self.info_frame.winfo_children():
            widget.destroy()

        self.lbl_info_placeholder = ctk.CTkLabel(
            self.info_frame,
            text="Seleccione una persona para ver su información",
            text_color="gray",
            font=ctk.CTkFont(size=FONT_SIZE_SMALL)
        )
        self.lbl_info_placeholder.pack(pady=PADDING_SMALL)
        
        self.persona_seleccionada = None
        self.limpiar_documentos()
    
    def mostrar_resultados(self, resultados):
        """Muestra los resultados de la búsqueda - ✅ VERSIÓN MEJORADA PARA PANTALLAS PEQUEÑAS"""
        from config import es_pantalla_pequena
        
        for widget in self.resultados_frame.winfo_children():
            widget.destroy()
        
        # ✅ Detectar si es pantalla pequeña
        pantalla_pequena = es_pantalla_pequena()
        
        for resultado in resultados:
            persona = Persona.from_tuple(resultado)
            
            frame_resultado = ctk.CTkFrame(
                self.resultados_frame, 
                fg_color="#003d66", 
                corner_radius=CARD_CORNER_RADIUS
            )
            frame_resultado.pack(pady=PADDING_SMALL, padx=PADDING_SMALL, fill="x")
            
            if pantalla_pequena:
                # ===== LAYOUT VERTICAL PARA PANTALLAS PEQUEÑAS =====
                # Configurar grid
                frame_resultado.grid_columnconfigure(0, weight=1)
                
                # ✅ Información más legible (fuente más grande)
                info_text = f"👤 {persona.nombre_completo}\n📋 {persona.dpi}"
                if persona.edad:
                    info_text += f"\n🎂 {persona.edad} años"
                
                lbl_info = ctk.CTkLabel(
                    frame_resultado,
                    text=info_text,
                    anchor="w",
                    justify="left",
                    font=ctk.CTkFont(size=FONT_SIZE_NORMAL),  # ✅ Fuente más grande
                    wraplength=escalar(550)  # ✅ Wrap text para evitar corte
                )
                lbl_info.grid(row=0, column=0, sticky="ew", padx=PADDING_MEDIUM, pady=PADDING_SMALL)
                
                # Botón abajo
                btn_seleccionar = ctk.CTkButton(
                    frame_resultado,
                    text="Seleccionar Persona",
                    image=self.icono_seleccionar,
                    compound="left",
                    command=lambda p=persona: self.seleccionar_persona(p),
                    height=BUTTON_HEIGHT_SMALL + escalar(5),
                    font=ctk.CTkFont(size=FONT_SIZE_BUTTON),
                    fg_color="#005187",
                    hover_color="#2d5f8d"
                )
                btn_seleccionar.grid(row=1, column=0, sticky="ew", padx=PADDING_MEDIUM, pady=(0, PADDING_SMALL))
            
            else:
                # ===== LAYOUT HORIZONTAL PARA PANTALLAS NORMALES =====
                frame_resultado.grid_columnconfigure(0, weight=1)
                frame_resultado.grid_columnconfigure(1, weight=0)
                
                info_text = f"👤 {persona.nombre_completo}\n📋 DPI: {persona.dpi}"
                if persona.edad:
                    info_text += f"\n🎂 Edad: {persona.edad} años"
                
                lbl_info = ctk.CTkLabel(
                    frame_resultado,
                    text=info_text,
                    anchor="w",
                    justify="left",
                    font=ctk.CTkFont(size=FONT_SIZE_SMALL)
                )
                lbl_info.grid(row=0, column=0, sticky="ew", padx=PADDING_SMALL, pady=PADDING_SMALL)
                
                btn_seleccionar = ctk.CTkButton(
                    frame_resultado,
                    text="Seleccionar",
                    image=self.icono_seleccionar,
                    compound="left",
                    command=lambda p=persona: self.seleccionar_persona(p),
                    width=escalar(130),
                    height=BUTTON_HEIGHT_SMALL,
                    font=ctk.CTkFont(size=FONT_SIZE_BUTTON),
                    fg_color="#005187",
                    hover_color="#2d5f8d"
                )
                btn_seleccionar.grid(row=0, column=1, sticky="ns", padx=PADDING_TINY, pady=PADDING_TINY)
    
    def seleccionar_persona(self, persona):
        """Selecciona una persona y muestra su información"""
        self.persona_seleccionada = persona
        
        # ✅ Mostrar información de la persona
        self.mostrar_info_persona()  # ← Este método debe llamar pack()
        
        # Cargar documentos de la persona
        self.cargar_documentos_persona()
    
    def seleccionar_persona_por_id(self, persona_id):
        """Selecciona una persona por su ID y muestra su información"""
        try:
            resultado_persona = self.db.obtener_persona_por_id(persona_id)
            
            if not resultado_persona:
                messagebox.showerror("Error", "No se pudo obtener la información de la persona.")
                return
            
            persona = Persona.from_tuple(resultado_persona)
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
        """Versión súper compacta para pantallas pequeñas"""
        for widget in self.info_frame.winfo_children():
            widget.destroy()
        
        self.info_frame.pack(pady=PADDING_SMALL, padx=PADDING_MEDIUM, fill="x")
        
        from config import es_pantalla_pequena
        
        if es_pantalla_pequena():
            # ✅ Versión MINI - Una sola línea
            info_text = f"✅ {self.persona_seleccionada.nombre_completo} | DPI: {self.persona_seleccionada.dpi}"
            
            ctk.CTkLabel(
                self.info_frame,
                text=info_text,
                font=ctk.CTkFont(size=FONT_SIZE_NORMAL, weight="bold"),  # ✅ Más grande
                text_color=COLOR_SUCCESS,
                wraplength=escalar(600)
            ).pack(pady=PADDING_SMALL, padx=PADDING_SMALL)
        else:
            # Versión normal (igual que antes)
            ctk.CTkLabel(
                self.info_frame,
                text="✅ Persona Seleccionada",
                font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight="bold"),
                text_color=COLOR_SUCCESS
            ).pack(pady=PADDING_SMALL)
            
            info_text = f"""👤 Nombre: {self.persona_seleccionada.nombre_completo}
    📋 DPI: {self.persona_seleccionada.dpi}
    🎂 Edad: {self.persona_seleccionada.edad if self.persona_seleccionada.edad else 'N/A'}
    💍 Estado Civil: {self.persona_seleccionada.estado_civil if self.persona_seleccionada.estado_civil else 'N/A'}
    🌍 Nacionalidad: {self.persona_seleccionada.nacionalidad if self.persona_seleccionada.nacionalidad else 'N/A'}
    🎓 Nivel Académico: {self.persona_seleccionada.nivel_academico if self.persona_seleccionada.nivel_academico else 'N/A'}
    🏠 Domicilio: {self.persona_seleccionada.domicilio if self.persona_seleccionada.domicilio else 'N/A'}"""
            
            ctk.CTkLabel(
                self.info_frame,
                text=info_text.strip(),
                anchor="w",
                justify="left",
                font=ctk.CTkFont(size=FONT_SIZE_NORMAL)  # ✅ Más legible
            ).pack(pady=PADDING_TINY, padx=PADDING_MEDIUM, fill="x")
    
    def normalizar_dpi(self, dpi):
        """Convierte DPI con espacios o guiones a formato sin separadores"""
        return dpi.replace(" ", "").replace("_", "").replace("-", "")
    
    def cargar_documentos_persona(self):
        """VERSIÓN OPTIMIZADA - Carga documentos de la persona seleccionada"""
        for widget in self.documentos_frame.winfo_children():
            widget.destroy()
        
        directorio_docs = DOCUMENTOS_DIR
        
        if not os.path.exists(directorio_docs):
            ctk.CTkLabel(
                self.documentos_frame,
                text="No existe el directorio de documentos",
                text_color="red",
                font=ctk.CTkFont(size=FONT_SIZE_SMALL)
            ).pack(pady=escalar(30))
            return
        
        if not hasattr(self, '_cache_años'):
            self._cache_años = CacheAños()
        
        dpi_normalizado = self.normalizar_dpi(self.persona_seleccionada.dpi).lower()
        
        self.documentos_persona = []
        self.documentos_por_año = {}
        
        try:
            import datetime
            
            archivos = [
                f for f in os.listdir(directorio_docs)
                if f.lower().endswith(('.docx', '.pdf'))
            ]
            
            for archivo in archivos:
                archivo_normalizado = archivo.replace(" ", "").replace("_", "").replace("-", "").lower()
                
                if dpi_normalizado not in archivo_normalizado:
                    continue
                
                ruta_completa = os.path.join(directorio_docs, archivo)
                año = self._cache_años.obtener_año(ruta_completa)
                
                try:
                    fecha_modificacion = os.path.getmtime(ruta_completa)
                    fecha_obj = datetime.datetime.fromtimestamp(fecha_modificacion)
                    fecha_str = fecha_obj.strftime("%Y-%m-%d %H:%M:%S")
                except OSError:
                    fecha_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                extension = archivo.lower().split('.')[-1].upper()
                
                doc_info = (None, archivo, ruta_completa, fecha_str, extension, self.persona_seleccionada.id, año)
                self.documentos_persona.append(doc_info)
                
                if año not in self.documentos_por_año:
                    self.documentos_por_año[año] = []
                self.documentos_por_año[año].append(doc_info)
        
        except Exception as e:
            print(f"Error al listar archivos: {e}")
            import traceback
            traceback.print_exc()
        
        if not self.documentos_persona:
            ctk.CTkLabel(
                self.documentos_frame,
                text=f"No se encontraron documentos para el DPI: {self.persona_seleccionada.dpi}",
                text_color="orange",
                font=ctk.CTkFont(size=FONT_SIZE_SMALL)
            ).pack(pady=escalar(30))
            return
        
        self.mostrar_todos_documentos_persona()
    
    def mostrar_todos_documentos_persona(self):
        """Muestra todos los documentos - ✅ VERSIÓN MEJORADA PARA PANTALLAS PEQUEÑAS"""
        from config import es_pantalla_pequena
        
        for widget in self.documentos_frame.winfo_children():
            widget.destroy()
        
        pantalla_pequena = es_pantalla_pequena()
        años_ordenados = sorted(self.documentos_por_año.keys(), reverse=True)
        
        for año in años_ordenados:
            ctk.CTkLabel(
                self.documentos_frame,
                text=f"📅 {año}",
                font=ctk.CTkFont(size=FONT_SIZE_NORMAL, weight="bold"),
                text_color=COLOR_PRIMARY
            ).pack(pady=(PADDING_MEDIUM, PADDING_SMALL), padx=PADDING_SMALL, anchor="w")
            
            documentos_año = sorted(
                self.documentos_por_año[año],
                key=lambda x: x[3],
                reverse=True
            )
            
            for doc in documentos_año:
                doc_id, nombre_archivo, ruta_archivo, fecha_carga, tipo_documento, persona_id, año_doc = doc
                index = next(i for i, d in enumerate(self.documentos_persona) if d[2] == ruta_archivo)
                
                frame_doc = ctk.CTkFrame(
                    self.documentos_frame, 
                    fg_color="#003d66", 
                    corner_radius=CARD_CORNER_RADIUS
                )
                frame_doc.pack(pady=PADDING_SMALL, padx=PADDING_SMALL, fill="x")
                
                if pantalla_pequena:
                    # ===== LAYOUT VERTICAL PARA PANTALLAS PEQUEÑAS =====
                    frame_doc.grid_columnconfigure(0, weight=1)
                    
                    # ✅ Información más legible
                    info_doc = f"📄 {nombre_archivo}\n📅 {fecha_carga}\n📑 {tipo_documento}"
                    
                    lbl_info = ctk.CTkLabel(
                        frame_doc,
                        text=info_doc,
                        anchor="w",
                        justify="left",
                        font=ctk.CTkFont(size=FONT_SIZE_NORMAL),  # ✅ Fuente más grande
                        wraplength=escalar(550)  # ✅ Wrap text
                    )
                    lbl_info.grid(row=0, column=0, sticky="ew", padx=PADDING_MEDIUM, pady=PADDING_SMALL)
                    
                    # Botones en fila horizontal
                    btn_frame = ctk.CTkFrame(frame_doc, fg_color="transparent")
                    btn_frame.grid(row=1, column=0, sticky="ew", padx=PADDING_SMALL, pady=(0, PADDING_SMALL))
                    
                    btn_frame.grid_columnconfigure(0, weight=1)
                    btn_frame.grid_columnconfigure(1, weight=1)
                    
                    btn_ver = ctk.CTkButton(
                        btn_frame,
                        text="👁️ Ver",
                        image=self.icono_ver if self.icono_ver else None,
                        compound="left",
                        command=lambda idx=index: self.ver_documento(idx),
                        height=BUTTON_HEIGHT_SMALL,
                        font=ctk.CTkFont(size=FONT_SIZE_BUTTON),
                        fg_color="#005187",
                        hover_color="#2d5f8d"
                    )
                    btn_ver.grid(row=0, column=0, sticky="ew", padx=PADDING_TINY)

                    btn_editar_doc = ctk.CTkButton(
                        btn_frame,
                        text="✏️ Editar",
                        image=self.icono_editar if self.icono_editar else None,
                        compound="left",
                        command=lambda idx=index: self.editar_documento(idx),
                        height=BUTTON_HEIGHT_SMALL,
                        font=ctk.CTkFont(size=FONT_SIZE_BUTTON),
                        fg_color="#005187",
                        hover_color="#2d5f8d"
                    )
                    btn_editar_doc.grid(row=0, column=1, sticky="ew", padx=PADDING_TINY)
                
                else:
                    # ===== LAYOUT HORIZONTAL PARA PANTALLAS NORMALES =====
                    frame_doc.grid_columnconfigure(0, weight=1)
                    
                    info_doc = f"📄 {nombre_archivo}\n📅 {fecha_carga} | {tipo_documento}"
                    
                    lbl_info = ctk.CTkLabel(
                        frame_doc,
                        text=info_doc,
                        anchor="w",
                        justify="left",
                        font=ctk.CTkFont(size=FONT_SIZE_TINY)
                    )
                    lbl_info.grid(row=0, column=0, sticky="ew", padx=PADDING_SMALL, pady=PADDING_TINY)
                    
                    btn_ver = ctk.CTkButton(
                        frame_doc,
                        text="Ver",
                        image=self.icono_ver,
                        compound="left",
                        command=lambda idx=index: self.ver_documento(idx),
                        width=escalar(100),
                        height=BUTTON_HEIGHT_SMALL,
                        font=ctk.CTkFont(size=FONT_SIZE_BUTTON),
                        fg_color="#005187",
                        hover_color="#2d5f8d"
                    )
                    btn_ver.grid(row=0, column=1, sticky="ns", padx=PADDING_TINY)

                    btn_editar_doc = ctk.CTkButton(
                        frame_doc,
                        text="Editar",
                        image=self.icono_editar,
                        compound="left",
                        command=lambda idx=index: self.editar_documento(idx),
                        width=escalar(100),
                        height=BUTTON_HEIGHT_SMALL,
                        font=ctk.CTkFont(size=FONT_SIZE_BUTTON),
                        fg_color="#005187",
                        hover_color="#2d5f8d"
                    )
                    btn_editar_doc.grid(row=0, column=2, sticky="ns", padx=PADDING_TINY)
            
            if año != años_ordenados[-1]:
                ctk.CTkFrame(
                    self.documentos_frame,
                    height=2,
                    fg_color="gray"
                ).pack(pady=PADDING_SMALL, padx=PADDING_MEDIUM, fill="x")
                    
    def ver_documento(self, index):
        """Muestra un documento en el visor"""
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
        
        for widget in self.visor_scroll.winfo_children():
            widget.destroy()
        
        self.lbl_visor_estado = ctk.CTkLabel(
            self.visor_scroll,
            text="Cargando documento...",
            text_color="orange",
            font=ctk.CTkFont(size=FONT_SIZE_NORMAL)
        )
        self.lbl_visor_estado.pack(pady=escalar(20))
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
    
    def mostrar_pdf_en_visor(self, pdf_path):
        """Muestra el PDF renderizado como imágenes en el visor"""
        for widget in self.visor_scroll.winfo_children():
            widget.destroy()
        
        try:
            pdf_document = fitz.open(pdf_path)
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # ✅ Ajustar zoom según tamaño de pantalla
                zoom = 1.5 if not es_pantalla_pequena() else 1.2
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # ✅ Usar ancho escalado
                max_width = int(VISOR_WIDTH * 0.9)
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                
                photo = ImageTk.PhotoImage(img)
                
                label = ctk.CTkLabel(self.visor_scroll, image=photo, text="")
                label.image = photo
                label.pack(pady=PADDING_SMALL)
                
                if page_num < len(pdf_document) - 1:
                    separador = ctk.CTkLabel(
                        self.visor_scroll,
                        text=f"--- Página {page_num + 1} ---",
                        font=ctk.CTkFont(size=FONT_SIZE_SMALL),
                        text_color="gray"
                    )
                    separador.pack(pady=PADDING_TINY)
            
            pdf_document.close()
            
        except Exception as e:
            self.lbl_visor_estado = ctk.CTkLabel(
                self.visor_scroll,
                text=f"Error al mostrar PDF:\n{str(e)}",
                text_color="red"
            )
            self.lbl_visor_estado.pack(pady=escalar(20))
    
    def editar_documento(self, index):
        """Abre el editor para modificar el documento existente y los datos de la persona"""
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
            resultado_persona = self.db.obtener_persona_por_id(persona_id)
            if not resultado_persona:
                messagebox.showerror(
                    "Error",
                    "No se pudo obtener la información completa de la persona asociada."
                )
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
                editor.set_callback_guardado(self._callback_despues_edicion)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el editor:\n{str(e)}")

    def _callback_despues_edicion(self):
        """Se llama después de guardar cambios en el editor"""
        if self.persona_seleccionada:
            self.cargar_documentos_persona()
        if self.callback_actualizar:
            self.callback_actualizar()
    
    def ver_documento_directo(self, ruta_archivo):
        """Muestra un documento directamente desde la ruta"""
        if not os.path.exists(ruta_archivo):
            messagebox.showerror("Error", f"El archivo no existe:\n{ruta_archivo}")
            return
        
        for widget in self.visor_scroll.winfo_children():
            widget.destroy()
        
        self.lbl_visor_estado = ctk.CTkLabel(
            self.visor_scroll,
            text="Cargando documento...",
            text_color="orange",
            font=ctk.CTkFont(size=FONT_SIZE_NORMAL)
        )
        self.lbl_visor_estado.pack(pady=escalar(20))
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
        if self.resultados_busqueda:
            self.cargar_todos_documentos_busqueda(self.resultados_busqueda)
        
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
            font=ctk.CTkFont(size=FONT_SIZE_SMALL)
        )
        self.lbl_sin_documentos.pack(pady=escalar(30))
    
    def cerrar_ventana(self):
        """Cierra la ventana de forma segura"""
        try:
            if hasattr(self, '_carga_activa'):
                self._carga_activa = False
          
            if hasattr(self, 'ventana') and self.ventana.winfo_exists():
                self.ventana.destroy()
      
        except Exception as e:
            print(f"Error al cerrar ventana: {e}")