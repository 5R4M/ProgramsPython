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
            
            # Verificar cache
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # Extraer año rápido (solo del documento, no fecha modificación primero)
            año = self._extraer_año_rapido(ruta_archivo)
            
            # Guardar en cache
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
                
                # Buscar solo en los primeros 5 párrafos (mucho más rápido)
                texto_busqueda = ""
                for i, para in enumerate(doc.paragraphs[:5]):
                    texto_busqueda += para.text + " "
                    if i >= 4:  # Solo 5 párrafos máximo
                        break
                
                # Buscar patrón de año (2020-2099)
                matches = re.findall(r'\b(20\d{2})\b', texto_busqueda)
                
                if matches:
                    año = int(matches[0])
        
        except Exception as e:
            print(f"Error extrayendo año: {e}")
        
        # Fallback: fecha de modificación
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
        
        # ✅ INICIALIZAR FLAGS DE CONTROL
        self._carga_activa = False
        
        self._cache_años = CacheAños()
        
        # ✅ CARGAR ICONOS ANTES DE CREAR INTERFAZ
        self.cargar_iconos()
        
        if es_integrado:
            # Crear como Frame integrado
            self.ventana = ctk.CTkFrame(parent)
            self.ventana.pack(fill="both", expand=True)
        else:
            # Crear como ventana separada (Toplevel)
            self.ventana = ctk.CTkToplevel(parent)
            self.ventana.title("🔍 Buscar Documento")
            
            # ✅ CONFIGURAR CIERRE SEGURO
            self.ventana.protocol("WM_DELETE_WINDOW", self.cerrar_ventana)
            
            self.ventana.after(100, self.maximizar_ventana)
        
        self.crear_interfaz()
        
        # Cargar documentos iniciales
        self.cargar_todos_documentos_iniciales()
        
    def cargar_iconos(self):
        """Carga los iconos PNG para los botones"""
        try:
            # Ruta absoluta a la carpeta de iconos
            # __file__ apunta a: declaraciones_app/ui/buscar_documento.py
            # Necesitamos ir a: declaraciones_app/utils/iconos
            
            ruta_base = os.path.dirname(os.path.abspath(__file__))  # declaraciones_app/ui
            ruta_proyecto = os.path.dirname(ruta_base)  # declaraciones_app
            ruta_iconos = os.path.join(ruta_proyecto, "utils", "iconos")
            
            print(f"🔍 Buscando iconos en: {ruta_iconos}")
            
            # Verificar que la carpeta existe
            if not os.path.exists(ruta_iconos):
                print(f"⚠️ La carpeta de iconos no existe: {ruta_iconos}")
                raise FileNotFoundError(f"No existe la carpeta: {ruta_iconos}")
            
            # Cargar iconos
            self.icono_buscar = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "buscar.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "buscar.png")),
                size=(24, 24)
            )
            
            self.icono_seleccionar = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "seleccionar.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "seleccionar.png")),
                size=(24, 24)
            )
            
            self.icono_editar = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "editar.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "editar.png")),
                size=(24, 24)
            )
            
            self.icono_ver = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "ver.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "ver.png")),
                size=(24, 24)
            )
            
            print("✅ Iconos cargados correctamente en buscar_documento")
            
        except Exception as e:
            print(f"⚠️ Error al cargar iconos: {e}")
            # Si falla, los iconos serán None
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
            text="Buscar",
            image=self.icono_buscar,
            compound="left",
            command=self.buscar_por_dpi,
            width=100,
            fg_color="#1E88E5",  # ✅ Azul fuerte
            hover_color="#1565C0"
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
            text="Buscar",
            image=self.icono_buscar,
            compound="left",
            command=self.buscar_por_nombre,
            width=100,
            fg_color="#1E88E5",  # ✅ Azul fuerte
            hover_color="#1565C0"
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
        """
        VERSIÓN OPTIMIZADA - Carga todos los documentos al iniciar la ventana.
        Usa cache y carga progresiva para no bloquear la UI.
        """
        import datetime
        
        # ✅ FLAG DE CONTROL
        self._carga_activa = True
        
        # Inicializar cache si no existe
        if not hasattr(self, '_cache_años'):
            self._cache_años = CacheAños()
        
        self.todos_documentos = []
        documentos_por_año_temp = {}
        
        directorio_docs = DOCUMENTOS_DIR
        
        if not os.path.exists(directorio_docs):
            self._carga_activa = False
            return
        
        try:
            # OPTIMIZACIÓN 1: Obtener todas las personas UNA SOLA VEZ
            todas_personas = self.db.obtener_todas_personas()
            
            if not todas_personas:
                self._carga_activa = False
                return
            
            # OPTIMIZACIÓN 2: Crear mapa de búsqueda rápida (O(1) lookup)
            personas_por_dpi = {}
            for persona in todas_personas:
                persona_id = persona[0]
                nombre_completo = persona[1]
                dpi = persona[2]
                dpi_normalizado = self.normalizar_dpi(dpi)
                personas_por_dpi[dpi_normalizado.lower()] = (persona_id, nombre_completo, dpi)
            
            # OPTIMIZACIÓN 3: Listar archivos UNA SOLA VEZ
            archivos = [
                f for f in os.listdir(directorio_docs)
                if f.lower().endswith(('.docx', '.pdf'))
            ]
            
            # OPTIMIZACIÓN 4: Procesar archivos en batch (sin bloquear UI)
            BATCH_SIZE = 10  # Procesar de 10 en 10
            total_archivos = len(archivos)
            
            def procesar_batch(inicio):
                """Procesa un lote de documentos"""
                try:
                    # ✅ VERIFICAR FLAG Y EXISTENCIA
                    if not self._carga_activa:
                        return
                    
                    if not hasattr(self, 'ventana') or not self.ventana.winfo_exists():
                        self._carga_activa = False
                        return
                    
                    fin = min(inicio + BATCH_SIZE, total_archivos)
                    
                    for archivo in archivos[inicio:fin]:
                        if not self._carga_activa:  # ✅ VERIFICAR EN CADA ITERACIÓN
                            return
                        
                        # Normalizar nombre del archivo
                        archivo_normalizado = archivo.replace(" ", "").replace("_", "").replace("-", "").lower()
                        
                        # Buscar coincidencia de DPI
                        persona_info = None
                        for dpi_norm, info in personas_por_dpi.items():
                            if dpi_norm in archivo_normalizado:
                                persona_info = info
                                break
                        
                        if not persona_info:
                            continue
                        
                        persona_id, nombre_completo, dpi = persona_info
                        ruta_completa = os.path.join(directorio_docs, archivo)
                        
                        # OPTIMIZACIÓN 5: Usar cache para años (NO extraer datos completos)
                        año = self._cache_años.obtener_año(ruta_completa)
                        
                        # OPTIMIZACIÓN 6: Obtener solo mtime (sin datetime completo todavía)
                        try:
                            mtime = os.path.getmtime(ruta_completa)
                            fecha_obj = datetime.datetime.fromtimestamp(mtime)
                            fecha_str = fecha_obj.strftime("%Y-%m-%d %H:%M:%S")
                        except OSError:
                            fecha_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Obtener extensión
                        extension = archivo.lower().split('.')[-1].upper()
                        
                        # Formato: (doc_id, nombre_archivo, ruta_archivo, fecha_carga, tipo_documento, persona_id, año, nombre_persona)
                        doc_info = (None, archivo, ruta_completa, fecha_str, extension, persona_id, año, nombre_completo)
                        self.todos_documentos.append(doc_info)
                        
                        # Agrupar por año
                        if año not in documentos_por_año_temp:
                            documentos_por_año_temp[año] = []
                        documentos_por_año_temp[año].append(doc_info)
                    
                    # Actualizar progreso
                    if self._carga_activa and hasattr(self, 'lbl_progreso_carga') and self.lbl_progreso_carga.winfo_exists():
                        progreso = int((fin / total_archivos) * 100)
                        self.lbl_progreso_carga.configure(
                            text=f"⏳ Cargando documentos... {progreso}% ({fin}/{total_archivos})"
                        )
                    
                    # Update UI
                    if self._carga_activa and hasattr(self, 'ventana') and self.ventana.winfo_exists():
                        self.ventana.update_idletasks()
                    
                    # Si hay más archivos, procesar siguiente batch (sin bloquear UI)
                    if fin < total_archivos and self._carga_activa:
                        if hasattr(self, 'ventana') and self.ventana.winfo_exists():
                            self.ventana.after(50, lambda: procesar_batch(fin))
                    else:
                        # FINALIZAR: Actualizar UI
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
            
            # Mostrar indicador de carga
            if hasattr(self, 'resultados_frame'):
                for widget in self.resultados_frame.winfo_children():
                    widget.destroy()
                
                self.lbl_progreso_carga = ctk.CTkLabel(
                    self.resultados_frame,
                    text="⏳ Cargando documentos... 0%",
                    font=ctk.CTkFont(size=14),
                    text_color="orange"
                )
                self.lbl_progreso_carga.pack(pady=50)
            
            # Iniciar procesamiento por batches
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
            
            # Eliminar indicador de progreso
            if hasattr(self, 'lbl_progreso_carga') and self.lbl_progreso_carga.winfo_exists():
                self.lbl_progreso_carga.destroy()
                delattr(self, 'lbl_progreso_carga')
            
            # Actualizar ComboBox de año
            if documentos_por_año_temp:
                años_disponibles = sorted(documentos_por_año_temp.keys(), reverse=True)
                valores_combo = ["Todos"] + [str(año) for año in años_disponibles]
                
                if hasattr(self, 'combo_año_busqueda') and self.combo_año_busqueda.winfo_exists():
                    self.combo_año_busqueda.configure(values=valores_combo)
                    self.combo_año_busqueda.set("Todos")
                
                # Guardar referencia
                self.documentos_por_año_busqueda = documentos_por_año_temp
                
                # Mostrar documentos
                self.mostrar_documentos_iniciales(documentos_por_año_temp)
            else:
                # No hay documentos
                if hasattr(self, 'resultados_frame') and self.resultados_frame.winfo_exists():
                    for widget in self.resultados_frame.winfo_children():
                        widget.destroy()
                    
                    ctk.CTkLabel(
                        self.resultados_frame,
                        text="No hay documentos registrados",
                        text_color="gray",
                        font=ctk.CTkFont(size=14)
                    ).pack(pady=50)
                
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
                    text="Seleccionar",
                    image=self.icono_seleccionar,
                    compound="left",
                    command=lambda pid=persona_id: self.seleccionar_persona_por_id(pid),
                    width=130,
                    fg_color="#1E88E5",  # ✅ Azul fuerte
                    hover_color="#1565C0"
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
        """
        VERSIÓN OPTIMIZADA - Carga documentos de las personas encontradas.
        """
        import datetime
        
        # Inicializar cache si no existe
        if not hasattr(self, '_cache_años'):
            self._cache_años = CacheAños()
        
        self.todos_documentos = []
        documentos_por_año_temp = {}
        
        directorio_docs = DOCUMENTOS_DIR
        
        if not os.path.exists(directorio_docs):
            return
        
        try:
            # Crear mapa de personas por DPI normalizado
            personas_map = {}
            for resultado in resultados:
                persona = Persona.from_tuple(resultado)
                dpi_normalizado = self.normalizar_dpi(persona.dpi)
                personas_map[dpi_normalizado.lower()] = persona
            
            # Listar archivos válidos una sola vez
            archivos = [
                f for f in os.listdir(directorio_docs)
                if f.lower().endswith(('.docx', '.pdf'))
            ]
            
            # Procesar archivos (usar cache)
            for archivo in archivos:
                archivo_normalizado = archivo.replace(" ", "").replace("_", "").replace("-", "").lower()
                
                # Buscar coincidencia
                persona_encontrada = None
                for dpi_norm, persona in personas_map.items():
                    if dpi_norm in archivo_normalizado:
                        persona_encontrada = persona
                        break
                
                if not persona_encontrada:
                    continue
                
                ruta_completa = os.path.join(directorio_docs, archivo)
                
                # USAR CACHE para año (NO extraer todos los datos)
                año = self._cache_años.obtener_año(ruta_completa)
                
                # Fecha de modificación
                try:
                    fecha_modificacion = os.path.getmtime(ruta_completa)
                    fecha_obj = datetime.datetime.fromtimestamp(fecha_modificacion)
                    fecha_str = fecha_obj.strftime("%Y-%m-%d %H:%M:%S")
                except OSError:
                    fecha_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                extension = archivo.lower().split('.')[-1].upper()
                
                doc_info = (None, archivo, ruta_completa, fecha_str, extension, persona_encontrada.id, año, persona_encontrada.nombre_completo)
                self.todos_documentos.append(doc_info)
                
                # Agrupar por año
                if año not in documentos_por_año_temp:
                    documentos_por_año_temp[año] = []
                documentos_por_año_temp[año].append(doc_info)
            
            # Actualizar ComboBox y mostrar
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
                        image=self.icono_seleccionar,
                        compound="left",
                        command=lambda pid=persona_id: self.seleccionar_persona_por_id(pid),
                        width=130,
                        fg_color="#1E88E5",  # ✅ Azul fuerte
                        hover_color="#1565C0"
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
                        image=self.icono_seleccionar,
                        compound="left",
                        command=lambda pid=persona_id: self.seleccionar_persona_por_id(pid),
                        width=130,
                        fg_color="#1E88E5",  # ✅ Azul fuerte
                        hover_color="#1565C0"
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
                text="✅ Seleccionar",  
                image=self.icono_seleccionar,
                compound="left",
                command=lambda p=persona: self.seleccionar_persona(p),
                width=130,
                fg_color="#1E88E5",  # ✅ Azul fuerte
                hover_color="#1565C0"
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
        """
        VERSIÓN OPTIMIZADA - Carga documentos de la persona seleccionada.
        """
        # Limpiar frame
        for widget in self.documentos_frame.winfo_children():
            widget.destroy()
        
        directorio_docs = DOCUMENTOS_DIR
        
        if not os.path.exists(directorio_docs):
            ctk.CTkLabel(
                self.documentos_frame,
                text="No existe el directorio de documentos",
                text_color="red",
                font=ctk.CTkFont(size=12)
            ).pack(pady=30)
            return
        
        # Inicializar cache
        if not hasattr(self, '_cache_años'):
            self._cache_años = CacheAños()
        
        # Normalizar DPI
        dpi_normalizado = self.normalizar_dpi(self.persona_seleccionada.dpi).lower()
        
        self.documentos_persona = []
        self.documentos_por_año = {}
        
        try:
            import datetime
            
            # Filtrar archivos al listar
            archivos = [
                f for f in os.listdir(directorio_docs)
                if f.lower().endswith(('.docx', '.pdf'))
            ]
            
            for archivo in archivos:
                archivo_normalizado = archivo.replace(" ", "").replace("_", "").replace("-", "").lower()
                
                if dpi_normalizado not in archivo_normalizado:
                    continue
                
                ruta_completa = os.path.join(directorio_docs, archivo)
                
                # USAR CACHE para año
                año = self._cache_años.obtener_año(ruta_completa)
                
                # Fecha
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
                font=ctk.CTkFont(size=12)
            ).pack(pady=30)
            return
        
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
                    text="Ver",
                    image=self.icono_ver,
                    compound="left",
                    command=lambda idx=index: self.ver_documento(idx),
                    width=100,
                    fg_color="#1E88E5",  # ✅ Azul fuerte
                    hover_color="#1565C0"
                )
                btn_ver.pack(side="right", padx=5)

                # Botón EDITAR
                btn_editar_doc = ctk.CTkButton(
                    frame_doc,
                    text="Editar",
                    image=self.icono_editar,
                    compound="left",
                    command=lambda idx=index: self.editar_documento(idx),
                    width=100,
                    fg_color="#1E88E5",  # ✅ Azul fuerte
                    hover_color="#1565C0"
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
    
    def cerrar_ventana(self):
        """Cierra la ventana de forma segura"""
        try:
            # ✅ DETENER CUALQUIER CARGA EN PROGRESO
            if hasattr(self, '_carga_activa'):
                self._carga_activa = False
            
            # Destruir ventana
            if hasattr(self, 'ventana') and self.ventana.winfo_exists():
                self.ventana.destroy()
        
        except Exception as e:
            print(f"Error al cerrar ventana: {e}")