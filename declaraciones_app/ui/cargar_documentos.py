import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import shutil
import tempfile
from PIL import Image, ImageTk
import fitz  # PyMuPDF
from config import (
    DOCUMENTOS_DIR, 
    COLOR_SUCCESS, 
    COLOR_PRIMARY,
    es_pantalla_pequena,
    # ✅ AGREGAR CONSTANTES DE FUENTE:
    escalar
)
from utils import convertir_doc_a_docx, DocumentExtractor
import time
from .crear_documento import VentanaCrearDocumento
import datetime
import json
from pathlib import Path

class CacheAños:
    """Cache persistente para años de documentos"""
    
    def __init__(self, cache_file="cache_años.json"):
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
    
    def obtener_año(self, ruta_archivo, force_update=False):
        """
        Obtiene el año de un documento.
        Usa cache si está disponible, sino extrae y guarda.
        """
        import datetime
        
        # Clave del cache: nombre_archivo + mtime
        nombre = os.path.basename(ruta_archivo)
        
        try:
            mtime = os.path.getmtime(ruta_archivo)
            cache_key = f"{nombre}_{int(mtime)}"
            
            # Verificar cache
            if not force_update and cache_key in self.cache:
                return self.cache[cache_key]
            
            # OPTIMIZACIÓN: Extraer SOLO el año, no todos los datos
            año = self._extraer_año_rapido(ruta_archivo)
            
            # Guardar en cache
            self.cache[cache_key] = año
            self._guardar_cache()
            
            return año
            
        except Exception as e:
            print(f"Error obteniendo año de {nombre}: {e}")
            return datetime.datetime.now().year
    
    def _extraer_año_rapido(self, ruta_archivo):
        """
        Extrae SOLO el año del documento de forma rápida.
        Evita extraer todos los datos.
        """
        import datetime
        import re
        from docx import Document
        
        año = None
        
        try:
            # Para archivos DOCX: buscar solo el año en el texto
            if ruta_archivo.lower().endswith('.docx'):
                doc = Document(ruta_archivo)
                
                # Buscar en los primeros 3 párrafos (más rápido)
                texto_busqueda = ""
                for i, para in enumerate(doc.paragraphs[:5]):
                    texto_busqueda += para.text + " "
                
                # Buscar patrón de año (2020-2099)
                patron_año = r'\b(20\d{2})\b'
                matches = re.findall(patron_año, texto_busqueda)
                
                if matches:
                    # Tomar el primer año encontrado
                    año = int(matches[0])
        
        except Exception as e:
            print(f"Error extrayendo año rápido: {e}")
        
        # Fallback: fecha de modificación
        if not año:
            try:
                mtime = os.path.getmtime(ruta_archivo)
                año = datetime.datetime.fromtimestamp(mtime).year
            except:  # noqa: E722
                año = datetime.datetime.now().year
        
        return año

def cancelar_callbacks_widget(widget):
    """Cancela todos los callbacks after de un widget y sus hijos recursivamente"""
    try:
        # Intentar cancelar callbacks del widget actual
        try:
            afters = widget.tk.call("after", "info")
            if afters:
                for aid in str(afters).split():
                    try:
                        widget.after_cancel(aid)
                    except:  # noqa: E722
                        pass
        except:  # noqa: E722
            pass
        
        # Recursivamente para todos los hijos
        try:
            for child in widget.winfo_children():
                cancelar_callbacks_widget(child)
        except:  # noqa: E722
            pass
    except:  # noqa: E722
        pass


def update_seguro(ventana):
    """Actualiza la ventana de forma segura, capturando errores"""
    try:
        ventana.update_idletasks()
        ventana.update()
        return True
    except Exception as e:
        # Si falla el update, probablemente la ventana fue cerrada
        error_msg = str(e).lower()
        if 'invalid command' in error_msg or 'application has been destroyed' in error_msg:
            return False
        return True

class VentanaCargarDocumentos:
    def __init__(self, parent, db, es_integrado=False):
        self.db = db
        self.es_integrado = es_integrado
        self.callback_actualizar = None
        self.documentos_seleccionados = []
        self.documento_actual_index = 0
        
        self._cache_años = CacheAños()
        
        # Control de ventana activa para evitar actualizaciones fantasma
        self.ventana_activa = True
        self.after_ids = []
        
        # Asegurar que existe el directorio de documentos (sin print)
        if not os.path.exists(DOCUMENTOS_DIR):
            os.makedirs(DOCUMENTOS_DIR, exist_ok=True)
        
        if es_integrado:
            # Crear como Frame integrado
            self.ventana = ctk.CTkFrame(parent, fg_color="#001a33")
            self.ventana.pack(fill="both", expand=True)
        else:
            # Crear como ventana separada (Toplevel)
            self.ventana = ctk.CTkToplevel(parent)
            self.ventana.title("📥 Cargar Documentos a la Base de Datos")
            self.ventana.configure(fg_color="#001a33")

            # Asociar al padre, traer al frente y bloquearlo
            self.ventana.transient(parent)
            self.ventana.lift()
            self.ventana.focus_force()
            self.ventana.grab_set()   # bloquea interacciones con el padre
            
            # Manejar cierre de ventana
            self.ventana.protocol("WM_DELETE_WINDOW", self.cerrar_ventana)
        # Cargar iconos
        self.cargar_iconos()
        # Crear UI
        self.crear_interfaz()
        self.cargar_documentos_existentes_optimizado()
        # Sincronización automática al iniciar
        self.ventana.after(500, self.sincronizar_bd_con_archivos)
        
        self.verificar_e_inicializar_sugerencias()

        # IMPORTANTE: centrar DESPUÉS de crear la interfaz
        if not self.es_integrado:
            # ✅ Solo maximizar en pantallas grandes
            if not es_pantalla_pequena():
                self.ventana.after(100, self.maximizar_ventana)
            else:
                self.center_window()
                self.ventana.after(50, self.center_window)
    
    def cargar_iconos(self):
        """Carga los iconos PNG para los botones - ✅ USANDO CONSTANTES"""
        try:
            from config import ICON_SIZE_BUTTON
            
            ruta_base = os.path.dirname(os.path.abspath(__file__))
            ruta_proyecto = os.path.dirname(ruta_base)
            ruta_iconos = os.path.join(ruta_proyecto, "utils", "iconos")
            
            print(f"🔍 Buscando iconos en: {ruta_iconos}")
            
            if not os.path.exists(ruta_iconos):
                print(f"⚠️ La carpeta de iconos no existe: {ruta_iconos}")
                raise FileNotFoundError(f"No existe la carpeta: {ruta_iconos}")
            
            # ===== ICONOS PARA BOTONES PRINCIPALES - ✅ USAR ICON_SIZE_CARD =====
            self.icono_seleccionar = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "seleccionar.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "seleccionar.png")),
                size=(escalar(28), escalar(28))
            )
            
            self.icono_limpiar = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "limpiar.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "limpiar.png")),
                size=(escalar(28), escalar(28))
            )
            
            self.icono_procesar = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "procesar.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "procesar.png")),
                size=(escalar(28), escalar(28))
            )
            
            self.icono_huerfanos = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "huerfanos.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "huerfanos.png")),
                size=(escalar(28), escalar(28))
            )
            
            self.icono_generar = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "generar.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "generar.png")),
                size=(escalar(28), escalar(28))
            )
            
            self.icono_regenerar = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "regenerar.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "regenerar.png")),
                size=(escalar(28), escalar(28))
            )
            
            self.icono_sincronizar = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "sincronizar.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "sincronizar.png")),
                size=(escalar(28), escalar(28))
            )
            
            self.icono_corregir = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "corregir.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "corregir.png")),
                size=(escalar(28), escalar(28))
            )
            
            # ===== ICONOS PARA BOTONES DE TABLA - ✅ USAR ICON_SIZE_BUTTON =====
            self.icono_buscar = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "buscar.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "buscar.png")),
                size=ICON_SIZE_BUTTON
            )
            
            self.icono_eliminar = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "eliminar.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "eliminar.png")),
                size=ICON_SIZE_BUTTON
            )
            
            self.icono_ver = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "ver.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "ver.png")),
                size=ICON_SIZE_BUTTON
            )
            
            # ===== ICONOS PARA VIÑETAS DE ESTADO =====
            self.icono_nuevo = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "nuevo.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "nuevo.png")),
                size=(escalar(16), escalar(16))
            )
            
            self.icono_cargado = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "cargado.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "cargado.png")),
                size=(escalar(16), escalar(16))
            )
            
            print("✅ Iconos cargados correctamente en cargar_documento")
            
        except Exception as e:
            print(f"⚠️ Error al cargar iconos: {e}")
            import traceback
            traceback.print_exc()
            
            for attr in ['icono_seleccionar', 'icono_limpiar', 'icono_procesar', 'icono_huerfanos',
                        'icono_generar', 'icono_regenerar', 'icono_sincronizar', 'icono_corregir',
                        'icono_buscar', 'icono_eliminar', 'icono_ver', 'icono_nuevo', 'icono_cargado']:
                setattr(self, attr, None)
    
    def verificar_e_inicializar_sugerencias(self):
        """Verifica si la tabla de sugerencias está vacía y la alimenta si es necesario"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sugerencias_palabras")
            total_sugerencias = cursor.fetchone()[0]
            
            if total_sugerencias == 0:
                print("🔄 Tabla de sugerencias vacía. Alimentando desde datos existentes...")
                
                # Alimentar desde personas existentes
                total_alimentado = self.db.alimentar_sugerencias_desde_bd()
                
                if total_alimentado > 0:
                    print(f"✅ {total_alimentado} personas procesadas para sugerencias")
                else:
                    print("⚠️ No hay datos para alimentar sugerencias")
        except Exception as e:
            print(f"⚠️ Error al verificar sugerencias: {e}")
    
    def cerrar_ventana(self):
        """Maneja el cierre seguro de la ventana"""
        # Cancelar todos los callbacks pendientes
        self.ventana_activa = False
        try:
            # Cancelar todos los after callbacks
            for after_id in self.after_ids:
                self.ventana.after_cancel(after_id)
            self.after_ids.clear()
            
            # Destruir la ventana
            if not self.es_integrado:
                self.ventana.destroy()
        except Exception as e:
            print(f"Error al cerrar ventana: {e}")
    
    def set_callback_actualizar(self, callback):
        """Permite establecer un callback para actualizar estadísticas"""
        self.callback_actualizar = callback
    
    def maximizar_ventana(self):
        """Maximiza la ventana"""
        if not self.es_integrado:
            self.ventana.state('zoomed')
    
    def center_window(self):
        """Centra la ventana en la pantalla - ✅ USANDO ESCALAR"""
        from config import escalar
        
        if not self.es_integrado:
            width = escalar(1400)
            height = escalar(900)
            self.ventana.geometry(f"{width}x{height}")
            self.ventana.update_idletasks()
            x = (self.ventana.winfo_screenwidth() // 2) - (width // 2)
            y = (self.ventana.winfo_screenheight() // 2) - (height // 2)
            self.ventana.geometry(f"{width}x{height}+{x}+{y}")
    
    def center_toplevel(self, win, w=400, h=200):
        """Centra una ventana CTkToplevel - ✅ USANDO ESCALAR"""
        from config import escalar
        
        win.update_idletasks()
        
        # ✅ Aplicar escala a dimensiones
        w_scaled = escalar(w)
        h_scaled = escalar(h)
        
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        
        x = (screen_width // 2) - (w_scaled // 2)
        y = (screen_height // 2) - (h_scaled // 2)
        
        win.geometry(f"{w_scaled}x{h_scaled}+{x}+{y}")
    
    def crear_interfaz(self):
        """Crea la interfaz de carga de documentos - ✅ ADAPTADA CON COLORES OSCUROS"""
        from config import (
            FONT_SIZE_TITLE, FONT_SIZE_SUBTITLE, FONT_SIZE_NORMAL, FONT_SIZE_SMALL,
            FONT_SIZE_BUTTON, PADDING_LARGE, PADDING_MEDIUM, PADDING_TINY,
            BUTTON_HEIGHT_SMALL, INPUT_HEIGHT, VISOR_WIDTH, VISOR_HEIGHT, escalar
        )
        
        # Frame principal con dos columnas - ✅ COLOR OSCURO
        container = ctk.CTkFrame(self.ventana, fg_color="#001a33")
        container.pack(fill="both", expand=True, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
        
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)
        
        # ===== PANEL IZQUIERDO - ✅ COLOR OSCURO =====
        panel_izquierdo = ctk.CTkFrame(container, fg_color="#003d66")
        panel_izquierdo.grid(row=0, column=0, sticky="nsew", padx=(0, PADDING_TINY))
        
        # ✅ Título con FONT_SIZE_TITLE
        ctk.CTkLabel(
            panel_izquierdo,
            text="📥 Cargar Documentos",
            font=ctk.CTkFont(size=FONT_SIZE_TITLE, weight="bold")
        ).pack(pady=PADDING_LARGE)
        
        # Frame de botones con GRID - ✅ COLOR OSCURO
        frame_botones = ctk.CTkFrame(panel_izquierdo, fg_color="#003d66")
        frame_botones.pack(pady=PADDING_MEDIUM, padx=PADDING_LARGE, fill="x")
        
        frame_botones.grid_columnconfigure(0, weight=1)
        frame_botones.grid_columnconfigure(1, weight=1)
        
        # ✅ Botones con colores oscuros
        btn_seleccionar = ctk.CTkButton(
            frame_botones,
            text="Seleccionar\nDocumentos",
            image=self.icono_seleccionar,
            compound="left",
            command=self.seleccionar_documentos,
            height=escalar(70),
            font=ctk.CTkFont(size=FONT_SIZE_SMALL, weight="bold"),
            fg_color="#005187",
            hover_color="#2d5f8d"
        )
        btn_seleccionar.grid(row=0, column=0, padx=PADDING_TINY, pady=PADDING_TINY, sticky="ew")

        btn_limpiar_listado = ctk.CTkButton(
            frame_botones,
            text="Limpiar\nListado",
            image=self.icono_limpiar,
            compound="left",
            command=self.limpiar_listado_completo,
            height=escalar(70),
            font=ctk.CTkFont(size=FONT_SIZE_SMALL, weight="bold"),
            fg_color="#005187",
            hover_color="#2d5f8d"
        )
        btn_limpiar_listado.grid(row=0, column=1, padx=PADDING_TINY, pady=PADDING_TINY, sticky="ew")

        btn_procesar = ctk.CTkButton(
            frame_botones,
            text="Procesar y\nCargar Todos",
            image=self.icono_procesar,
            compound="left",
            command=self.procesar_todos_documentos,
            height=escalar(70),
            font=ctk.CTkFont(size=FONT_SIZE_SMALL, weight="bold"),
            fg_color="#005187",
            hover_color="#2d5f8d"
        )
        btn_procesar.grid(row=1, column=0, padx=PADDING_TINY, pady=PADDING_TINY, sticky="ew")

        btn_sincronizar = ctk.CTkButton(
            frame_botones,
            text="Sincronizar BD\ncon Archivos",
            image=self.icono_sincronizar,
            compound="left",
            command=self.sincronizar_bd_con_archivos,
            height=escalar(70),
            font=ctk.CTkFont(size=FONT_SIZE_SMALL, weight="bold"),
            fg_color="#005187",
            hover_color="#2d5f8d"
        )
        btn_sincronizar.grid(row=1, column=1, padx=PADDING_TINY, pady=PADDING_TINY, sticky="ew")

        btn_regenerar_docs = ctk.CTkButton(
            frame_botones,
            text="Regenerar todos\ndesde BD",
            image=self.icono_regenerar,
            compound="left",
            command=self.regenerar_todos_los_documentos_desde_bd,
            height=escalar(70),
            font=ctk.CTkFont(size=FONT_SIZE_SMALL, weight="bold"),
            fg_color="#005187",
            hover_color="#2d5f8d"
        )
        btn_regenerar_docs.grid(row=2, column=0, padx=PADDING_TINY, pady=PADDING_TINY, sticky="ew")

        btn_corregir_sync = ctk.CTkButton(
            frame_botones,
            text="Corregir Problemas\nde Sincronización",
            image=self.icono_corregir,
            compound="left",
            command=self.corregir_problemas_sincronizacion,
            height=escalar(70),
            font=ctk.CTkFont(size=FONT_SIZE_SMALL, weight="bold"),
            fg_color="#005187",
            hover_color="#2d5f8d"
        )
        btn_corregir_sync.grid(row=2, column=1, padx=PADDING_TINY, pady=PADDING_TINY, sticky="ew")
                
        # Pestañas - ✅ COLOR OSCURO
        self.tabview = ctk.CTkTabview(panel_izquierdo, fg_color="#003d66", segmented_button_fg_color="#005187", segmented_button_selected_color="#2d5f8d")
        self.tabview.pack(pady=PADDING_MEDIUM, padx=PADDING_LARGE, fill="both", expand=True)

        # Pestaña: Documentos a cargar
        self.tabview.add("Nuevos")
        tab_nuevos = self.tabview.tab("Nuevos")

        try:
            tab_button_nuevos = self.tabview._segmented_button._buttons_dict["Nuevos"]
            if self.icono_nuevo:
                tab_button_nuevos.configure(image=self.icono_nuevo, compound="left")
        except Exception as e:
            print(f"No se pudo agregar icono a pestaña Nuevos: {e}")

        ctk.CTkLabel(
            tab_nuevos,
            text="Documentos seleccionados:",
            font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight="bold")
        ).pack(pady=(PADDING_MEDIUM, PADDING_TINY), padx=PADDING_MEDIUM, anchor="w")

        self.lista_frame = ctk.CTkScrollableFrame(tab_nuevos, height=escalar(400), fg_color="#001a33")
        self.lista_frame.pack(pady=PADDING_TINY, padx=PADDING_MEDIUM, fill="both", expand=True)

        self.lbl_lista_vacia = ctk.CTkLabel(
            self.lista_frame,
            text="No hay documentos seleccionados",
            text_color="gray",
            font=ctk.CTkFont(size=FONT_SIZE_NORMAL)
        )
        self.lbl_lista_vacia.pack(pady=escalar(50))

        # Controles de navegación - ✅ COLOR OSCURO
        frame_navegacion = ctk.CTkFrame(tab_nuevos, fg_color="#003d66")
        frame_navegacion.pack(pady=PADDING_MEDIUM, padx=PADDING_MEDIUM, fill="x")

        self.btn_anterior = ctk.CTkButton(
            frame_navegacion,
            text="◀ Anterior",
            command=self.documento_anterior,
            width=escalar(150),
            height=BUTTON_HEIGHT_SMALL,
            font=ctk.CTkFont(size=FONT_SIZE_BUTTON),
            fg_color="#005187",
            hover_color="#2d5f8d",
            state="disabled"
        )
        self.btn_anterior.pack(side="left", padx=PADDING_TINY)

        self.lbl_contador = ctk.CTkLabel(
            frame_navegacion,
            text="0 / 0",
            font=ctk.CTkFont(size=FONT_SIZE_NORMAL)
        )
        self.lbl_contador.pack(side="left", expand=True)

        self.btn_siguiente = ctk.CTkButton(
            frame_navegacion,
            text="Siguiente ▶",
            command=self.documento_siguiente,
            width=escalar(150),
            height=BUTTON_HEIGHT_SMALL,
            font=ctk.CTkFont(size=FONT_SIZE_BUTTON),
            fg_color="#005187",
            hover_color="#2d5f8d",
            state="disabled"
        )
        self.btn_siguiente.pack(side="right", padx=PADDING_TINY)

        # Pestaña: Documentos existentes
        self.tabview.add("Cargados")
        tab_existentes = self.tabview.tab("Cargados")

        try:
            tab_button_cargados = self.tabview._segmented_button._buttons_dict["Cargados"]
            if self.icono_cargado:
                tab_button_cargados.configure(image=self.icono_cargado, compound="left")
        except Exception as e:
            print(f"No se pudo agregar icono a pestaña Cargados: {e}")
        
        # Barra de búsqueda - ✅ COLOR OSCURO
        frame_busqueda = ctk.CTkFrame(tab_existentes, fg_color="#003d66")
        frame_busqueda.pack(pady=PADDING_MEDIUM, padx=PADDING_MEDIUM, fill="x")

        self.entry_buscar = ctk.CTkEntry(
            frame_busqueda,
            placeholder_text="Buscar por nombre o DPI...",
            font=ctk.CTkFont(size=FONT_SIZE_SMALL),
            height=INPUT_HEIGHT,
            fg_color="#001a33",
            border_color="#005187"
        )
        self.entry_buscar.pack(side="left", padx=PADDING_TINY, expand=True, fill="x")
        self.entry_buscar.bind("<KeyRelease>", lambda e: self.filtrar_documentos_existentes())

        btn_refrescar = ctk.CTkButton(
            frame_busqueda,
            text="",
            image=self.icono_buscar if hasattr(self, 'icono_buscar') and self.icono_buscar else None,
            command=self.cargar_documentos_existentes_optimizado,
            width=escalar(40),
            height=INPUT_HEIGHT,
            fg_color="#005187",
            hover_color="#2d5f8d"
        )
        btn_refrescar.pack(side="left", padx=PADDING_TINY)
        
        # Selector de año
        ctk.CTkLabel(
            frame_busqueda,
            text="📅 Año:",
            font=ctk.CTkFont(size=FONT_SIZE_NORMAL)
        ).pack(side="left", padx=(PADDING_MEDIUM, PADDING_TINY))

        self.combo_año_filtro = ctk.CTkComboBox(
            frame_busqueda,
            values=["Todos"],
            command=lambda año: self.filtrar_documentos_existentes(),
            width=escalar(100),
            height=INPUT_HEIGHT,
            font=ctk.CTkFont(size=FONT_SIZE_SMALL),
            fg_color="#001a33",
            border_color="#005187",
            button_color="#005187",
            button_hover_color="#2d5f8d",
            state="readonly"
        )
        self.combo_año_filtro.pack(side="left", padx=PADDING_TINY)
        self.combo_año_filtro.set("Todos")
        
        # Frame scrollable para documentos existentes - ✅ COLOR OSCURO
        self.lista_existentes_frame = ctk.CTkScrollableFrame(tab_existentes, height=escalar(500), fg_color="#001a33")
        self.lista_existentes_frame.pack(pady=PADDING_TINY, padx=PADDING_MEDIUM, fill="both", expand=True)
        
        self.lbl_sin_existentes = ctk.CTkLabel(
            self.lista_existentes_frame,
            text="No hay documentos cargados",
            text_color="gray",
            font=ctk.CTkFont(size=FONT_SIZE_NORMAL)
        )
        self.lbl_sin_existentes.pack(pady=escalar(50))
        
        # ===== PANEL DERECHO: Visor - ✅ COLOR OSCURO =====
        panel_derecho = ctk.CTkFrame(container, fg_color="#003d66")
        panel_derecho.grid(row=0, column=1, sticky="nsew", padx=(PADDING_TINY, 0))
        
        ctk.CTkLabel(
            panel_derecho,
            text="📄 Vista Previa del Documento",
            font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight="bold")
        ).pack(pady=PADDING_MEDIUM)
        
        # ✅ Usar VISOR_WIDTH y VISOR_HEIGHT con color oscuro
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

    def cargar_documentos_existentes_optimizado(self):
        """
        Versión optimizada de cargar_documentos_existentes.
        Carga inicial rápida, luego completa los años en background.
        """
            
        # Limpiar lista visual
        for widget in self.lista_existentes_frame.winfo_children():
            widget.destroy()
        
        # Mostrar indicador de carga
        lbl_cargando = ctk.CTkLabel(
            self.lista_existentes_frame,
            text="⏳ Cargando documentos...",
            font=ctk.CTkFont(size=14),
            text_color="orange"
        )
        lbl_cargando.pack(pady=50)
        self.ventana.update()
        
        # Archivos físicos
        archivos_carpeta = []
        if os.path.exists(DOCUMENTOS_DIR):
            archivos_carpeta = [
                f for f in os.listdir(DOCUMENTOS_DIR)
                if f.lower().endswith(('.doc', '.docx'))
            ]
        
        # Obtener documentos BD (una sola vez)
        documentos_bd = self.db.obtener_todos_documentos()
        mapa_doc_por_nombre = {doc[1]: doc for doc in documentos_bd}
        
        # FASE 1: Carga rápida SIN años (solo metadata básica)
        docs_con_mtime = []
        
        for nombre_archivo in archivos_carpeta:
            ruta_archivo = os.path.join(DOCUMENTOS_DIR, nombre_archivo)
            
            try:
                mtime = os.path.getmtime(ruta_archivo)
            except OSError:
                mtime = 0
            
            if nombre_archivo in mapa_doc_por_nombre:
                doc = mapa_doc_por_nombre[nombre_archivo]
            else:
                doc = (
                    None, nombre_archivo, ruta_archivo, "",
                    "Desconocido", "N/A", None
                )
            
            # Agregar con año temporal (None)
            doc_con_mtime = doc + (mtime, None)  # año = None
            docs_con_mtime.append((doc_con_mtime, mtime))
        
        # Ordenar por mtime
        docs_con_mtime.sort(key=lambda x: x[1], reverse=True)
        self.documentos_existentes = [item[0] for item in docs_con_mtime]
        
        # Eliminar indicador de carga
        lbl_cargando.destroy()
        
        # Mostrar documentos inmediatamente (SIN años todavía)
        self._mostrar_documentos_sin_años()
        
        # FASE 2: Cargar años en background
        self.ventana.after(100, lambda: self._cargar_años_background())


    def _mostrar_documentos_sin_años(self):
        """Muestra documentos sin esperar a cargar los años"""
        # ✅ CONTAR SOLO ARCHIVOS FÍSICOS
        total_archivos_fisicos = 0
        if os.path.exists(DOCUMENTOS_DIR):
            archivos = [f for f in os.listdir(DOCUMENTOS_DIR) 
                    if f.lower().endswith(('.doc', '.docx'))]
            total_archivos_fisicos = len(archivos)
        
        # ✅ CONTAR PERSONAS EN BD
        total_personas = self.db.contar_personas()
        
        # Encabezado
        header_frame = ctk.CTkFrame(self.lista_existentes_frame, fg_color="transparent")
        header_frame.pack(pady=10, padx=10, fill="x")
        
        contador_text = (
            f"📊 Documentos físicos: {total_archivos_fisicos}\n"
            f"👥 Personas en BD: {total_personas}\n"
            f"⏳ Cargando información adicional..."
        )
        
        self.lbl_contador_docs = ctk.CTkLabel(
            header_frame,
            text=contador_text,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#3498db"
        )
        self.lbl_contador_docs.pack(pady=5)
        
        # Mostrar documentos
        self.mostrar_documentos_existentes(self.documentos_existentes)


    def _cargar_años_background(self):
        """Carga los años de documentos en background"""
        if not hasattr(self, '_cache_años'):
            self._cache_años = CacheAños()
        
        documentos_actualizados = []
        años_dict = {}
        
        # Procesar en lotes pequeños para no bloquear UI
        BATCH_SIZE = 5
        
        def procesar_lote(inicio):
            fin = min(inicio + BATCH_SIZE, len(self.documentos_existentes))
            
            for i in range(inicio, fin):
                doc = self.documentos_existentes[i]
                ruta_archivo = doc[2]
                
                # Obtener año (usa cache)
                año = self._cache_años.obtener_año(ruta_archivo)
                
                # Actualizar tupla
                doc_actualizado = doc[:-1] + (año,)
                documentos_actualizados.append(doc_actualizado)
                
                if año not in años_dict:
                    años_dict[año] = []
                años_dict[año].append(doc_actualizado)
            
            # Si hay más documentos, programar siguiente lote
            if fin < len(self.documentos_existentes):
                self.ventana.after(50, lambda: procesar_lote(fin))
            else:
                # Terminó: actualizar UI
                self._finalizar_carga_años(documentos_actualizados, años_dict)
        
        # Iniciar procesamiento
        procesar_lote(0)


    def _finalizar_carga_años(self, documentos_actualizados, años_dict):
        """Finaliza la carga actualizando la UI con los años"""
        self.documentos_existentes = documentos_actualizados
        
        # Actualizar ComboBox de años
        años_ordenados = sorted(años_dict.keys(), reverse=True)
        valores_combo = ["Todos"] + [str(año) for año in años_ordenados]
        self.combo_año_filtro.configure(values=valores_combo)
        
        # ✅ CONTAR ARCHIVOS FÍSICOS (NO REGISTROS EN MEMORIA)
        total_archivos_fisicos = 0
        if os.path.exists(DOCUMENTOS_DIR):
            archivos = [f for f in os.listdir(DOCUMENTOS_DIR) 
                    if f.lower().endswith(('.doc', '.docx'))]
            total_archivos_fisicos = len(archivos)
        
        # ✅ CONTAR PERSONAS EN BD
        total_personas = self.db.contar_personas()
        
        # Actualizar contador
        if hasattr(self, 'lbl_contador_docs'):
            self.lbl_contador_docs.configure(
                text=f"📊 Documentos físicos: {total_archivos_fisicos}\n"
                    f"👥 Personas en BD: {total_personas}\n"
                    f"✅ Información completa cargada"
            )
        
        # Refrescar vista con años
        self.mostrar_documentos_existentes(self.documentos_existentes)
    
    def mostrar_documentos_existentes(self, documentos):
        """Muestra la lista de documentos existentes - ✅ CON COLORES OSCUROS"""
        # Limpiar SOLO los items existentes debajo del header
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
            doc_id = doc[0]
            nombre_archivo = doc[1]
            ruta_archivo = doc[2]
            fecha_carga_bd = doc[3]
            nombre_persona = doc[4] if doc[4] else "Desconocido"
            dpi_persona = doc[5] if doc[5] else "N/A"
            mtime = doc[7] if len(doc) > 7 else 0
            año_doc = doc[8] if len(doc) > 8 else None 

            if mtime:
                dt = datetime.datetime.fromtimestamp(mtime)
                fecha_mod_str = dt.strftime("%Y-%m-%d %H:%M")
            else:
                fecha_mod_str = "Desconocida"

            # ✅ Frame con color oscuro
            frame_doc = ctk.CTkFrame(self.lista_existentes_frame, fg_color="#003d66")
            frame_doc.pack(pady=5, padx=10, fill="x")

            info_text = (
                f"📄 {nombre_archivo}\n"
                f"👤 {nombre_persona}\n"
                f"📋 DPI: {dpi_persona}\n"
                f"📅 Año: {año_doc if año_doc else 'N/A'}\n"
                f"📥 Cargado: {fecha_carga_bd}\n"
                f"🕒 Última modificación: {fecha_mod_str}"
            )

            ctk.CTkLabel(
                frame_doc,
                text=info_text,
                anchor="w",
                justify="left",
                font=ctk.CTkFont(size=11)
            ).pack(side="left", padx=10, pady=10, expand=True, fill="x")

            # ✅ Botones con colores oscuros
            btn_ver = ctk.CTkButton(
                frame_doc,
                text="",
                image=self.icono_ver,
                command=lambda r=ruta_archivo: self.ver_documento_existente(r),
                width=40,
                fg_color="#005187",
                hover_color="#2d5f8d"
            )
            btn_ver.pack(side="right", padx=5)

            btn_eliminar = ctk.CTkButton(
                frame_doc,
                text="",
                image=self.icono_eliminar,
                command=lambda i=doc_id, r=ruta_archivo, n=nombre_archivo: self.eliminar_documento_existente(i, r, n),
                width=40,
                fg_color="#005187",
                hover_color="#2d5f8d"
            )
            btn_eliminar.pack(side="right", padx=5)
        
    def filtrar_documentos_existentes(self):
        """Filtra los documentos existentes según el texto de búsqueda y año"""
        texto_busqueda = self.entry_buscar.get().strip().lower()
        año_seleccionado = self.combo_año_filtro.get()
        
        # Filtrar documentos
        documentos_filtrados = []
        for doc in self.documentos_existentes:
            nombre_archivo = doc[1].lower()
            nombre_persona = doc[4].lower() if doc[4] else ""
            dpi_persona = doc[5].lower() if doc[5] else ""
            año_doc = doc[8] if len(doc) > 8 else None
            
            # Filtro de texto
            coincide_texto = (
                not texto_busqueda or
                texto_busqueda in nombre_archivo or
                texto_busqueda in nombre_persona or
                texto_busqueda in dpi_persona
            )
            
            # Filtro de año
            coincide_año = (
                año_seleccionado == "Todos" or
                (año_doc and str(año_doc) == año_seleccionado)
            )
            
            if coincide_texto and coincide_año:
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

            # Intentar convertir; si falla, no seguimos
            if not self._convertir_docx_a_pdf_seguro(ruta_archivo, temp_pdf.name):
                try:
                    os.unlink(temp_pdf.name)
                except Exception:
                    pass
                return

            # Mostrar PDF
            self.mostrar_pdf_en_visor(temp_pdf.name)

            # Limpiar archivo temporal
            try:
                os.unlink(temp_pdf.name)
            except Exception:
                pass
        
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
            self.lbl_lista_vacia.pack(pady=escalar(50))
            return
        
        # Mostrar documentos
        for i, archivo in enumerate(self.documentos_seleccionados):
            nombre_archivo = os.path.basename(archivo)
            nombre_corto = self._acortar_nombre(nombre_archivo, max_len=40)

            frame_item = ctk.CTkFrame(self.lista_frame)
            frame_item.pack(pady=5, padx=10, fill="x")

            # Resaltar documento actual
            if i == self.documento_actual_index:
                frame_item.configure(fg_color=COLOR_SUCCESS)

            # ✅ Label con viñeta de estado "Nuevo" usando el icono
            lbl_numero = ctk.CTkLabel(
                frame_item,
                text=f" {i + 1}. {nombre_corto}",
                image=self.icono_nuevo if hasattr(self, 'icono_nuevo') and self.icono_nuevo else None,
                compound="left" if hasattr(self, 'icono_nuevo') and self.icono_nuevo else "none",
                anchor="w",
                justify="left",
                font=ctk.CTkFont(size=12)
            )
            lbl_numero.pack(side="left", padx=10, pady=5, fill="x", expand=True)

            # ✅ Botón Ver con icono
            btn_ver = ctk.CTkButton(
                frame_item,
                text="",
                image=self.icono_ver if hasattr(self, 'icono_ver') and self.icono_ver else None,
                command=lambda idx=i: self.ver_documento(idx),
                width=40,
                fg_color="#43A047",
                hover_color="#2E7D32"
            )
            btn_ver.pack(side="right", padx=2)
            
            # ✅ Botón Eliminar con icono
            btn_eliminar = ctk.CTkButton(
                frame_item,
                text="",
                image=self.icono_eliminar if hasattr(self, 'icono_eliminar') and self.icono_eliminar else None,
                command=lambda idx=i: self.eliminar_del_listado(idx),
                width=40,
                fg_color="#E53935",
                hover_color="#C62828"
            )
            btn_eliminar.pack(side="right", padx=2)
        
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
        self.lbl_visor_estado.pack(pady=escalar(20))
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

            if not self._convertir_docx_a_pdf_seguro(archivo_docx, temp_pdf.name):
                try:
                    os.unlink(temp_pdf.name)
                except Exception:
                    pass
                # Si era un .doc convertido temporalmente, intenta borrarlo
                if archivo.lower().endswith('.doc') and archivo_docx != archivo:
                    try:
                        os.unlink(archivo_docx)
                    except Exception:
                        pass
                return

            # Mostrar PDF
            self.mostrar_pdf_en_visor(temp_pdf.name)

            # Limpiar archivos temporales
            try:
                os.unlink(temp_pdf.name)
            except Exception:
                pass
            if archivo.lower().endswith('.doc') and archivo_docx != archivo:
                try:
                    os.unlink(archivo_docx)
                except Exception:
                    pass
        
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
            # Verificación extra: el archivo existe y tiene tamaño razonable
            if (not os.path.exists(pdf_path)) or (os.path.getsize(pdf_path) < 100):
                raise Exception("El PDF generado está vacío o es inválido.")
            
            pdf_document = fitz.open(pdf_path)
            num_pages = len(pdf_document)

            if num_pages == 0:
                raise Exception("El PDF no contiene páginas.")

            for page_num in range(num_pages):
                page = pdf_document[page_num]
                
                # ✅ Ajustar zoom según tamaño de pantalla
                from config import es_pantalla_pequena
                zoom = 1.2 if es_pantalla_pequena() else 1.5
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                
                # Convertir a PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # ✅ Usar ancho escalado del visor
                from config import VISOR_WIDTH
                max_width = int(VISOR_WIDTH * 0.9)
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
                if page_num < num_pages - 1:
                    separador = ctk.CTkLabel(
                        self.visor_scroll,
                        text=f"--- Página {page_num + 1} ---",
                        font=ctk.CTkFont(size=12),
                        text_color="gray"
                    )
                    separador.pack(pady=5)
            
        except Exception as e:
            # Mostrar mensaje claro en el visor
            for widget in self.visor_scroll.winfo_children():
                widget.destroy()
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
        """Procesa y carga todos los documentos a la base de datos con ventana de progreso detallada."""
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
        ventana_progreso = ctk.CTkToplevel(self.ventana)
        ventana_progreso.title("⚙️ Procesando documentos...")
        ventana_progreso.grab_set()
        ventana_progreso.resizable(False, False)
        ventana_progreso.protocol("WM_DELETE_WINDOW", lambda: None)  # Bloquear cierre con X

        # Frame principal
        main_frame = ctk.CTkFrame(ventana_progreso)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Título
        ctk.CTkLabel(
            main_frame,
            text="⚙️ Procesando documentos...",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(0, 10))

        # Frame de estadísticas
        stats_frame = ctk.CTkFrame(main_frame)
        stats_frame.pack(pady=10, fill="x")
        
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        total_label = ctk.CTkLabel(
            stats_frame,
            text="📊 Total\n0",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#3498db"
        )
        total_label.grid(row=0, column=0, padx=5, pady=10)
        
        success_label = ctk.CTkLabel(
            stats_frame,
            text="✅ Nuevos\n0",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#2ecc71"
        )
        success_label.grid(row=0, column=1, padx=5, pady=10)
        
        updated_label = ctk.CTkLabel(
            stats_frame,
            text="🔄 Actualizados\n0",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#f39c12"
        )
        updated_label.grid(row=0, column=2, padx=5, pady=10)
        
        error_label = ctk.CTkLabel(
            stats_frame,
            text="❌ Errores\n0",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#e74c3c"
        )
        error_label.grid(row=0, column=3, padx=5, pady=10)

        # Documento actual
        current_doc_label = ctk.CTkLabel(
            main_frame,
            text="Preparando...",
            font=ctk.CTkFont(size=13),
            wraplength=650
        )
        current_doc_label.pack(pady=10)

        # Barra de progreso
        progress_bar = ctk.CTkProgressBar(main_frame, width=650, height=20)
        progress_bar.pack(pady=10)
        progress_bar.set(0)

        # Porcentaje
        percent_label = ctk.CTkLabel(
            main_frame,
            text="0%",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        percent_label.pack(pady=5)

        # Separador
        separator = ctk.CTkFrame(main_frame, height=2, fg_color="gray")
        separator.pack(fill="x", pady=10)

        # Log de actividad
        ctk.CTkLabel(
            main_frame,
            text="📋 Registro de actividad:",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        ).pack(pady=(5, 5), fill="x")

        from config import TEXTBOX_WIDTH, TEXTBOX_HEIGHT
        log_text = ctk.CTkTextbox(main_frame, width=TEXTBOX_WIDTH, height=TEXTBOX_HEIGHT)
        log_text.pack(pady=5)

        # Configurar tags para colores
        log_text.tag_config("success", foreground="#2ecc71")
        log_text.tag_config("error", foreground="#e74c3c")
        log_text.tag_config("update", foreground="#f39c12")
        log_text.tag_config("info", foreground="#3498db")

        # Botón cerrar (deshabilitado al inicio)
        def cerrar_ventana_progreso():
            try:
                cancelar_callbacks_widget(ventana_progreso)
                ventana_progreso.destroy()
            except:  # noqa: E722
                pass
        
        btn_cerrar = ctk.CTkButton(
            main_frame,
            text="✓ Cerrar",
            command=cerrar_ventana_progreso,
            height=35,
            width=150,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLOR_PRIMARY,
            hover_color="#2980b9",
            state="disabled"
        )
        btn_cerrar.pack(pady=10)

        # Centrar ventana DESPUÉS de crear contenido
        self.center_toplevel(ventana_progreso, 750, 620)
        
        # Forzar actualización de la ventana
        ventana_progreso.update_idletasks()
        ventana_progreso.update()
        
        # Contadores
        importados = 0
        errores = 0
        actualizados = 0
        total_docs = len(self.documentos_seleccionados)
        
        # Actualizar total
        total_label.configure(text=f"📊 Total\n{total_docs}")
        
        # Log inicial
        log_text.insert("end", f"{'='*70}\n", "info")
        log_text.insert("end", f"Iniciando procesamiento de {total_docs} documento(s)\n", "info")
        log_text.insert("end", f"{'='*70}\n\n", "info")
        
        ventana_progreso.update_idletasks()
        ventana_progreso.update()
        
        # Procesar documentos
        for i, archivo in enumerate(self.documentos_seleccionados):
            archivo_docx = None
            nombre_archivo = os.path.basename(archivo)
            
            try:
                # Actualizar progreso visual
                progreso_actual = (i + 1) / total_docs
                progress_bar.set(progreso_actual)
                percent_label.configure(text=f"{int(progreso_actual * 100)}%")
                
                current_doc_label.configure(
                    text=f"📄 Procesando ({i + 1}/{total_docs}): {nombre_archivo}"
                )
                
                log_text.insert("end", f"[{i + 1}/{total_docs}] ", "info")
                log_text.insert("end", f"📄 {nombre_archivo}\n")
                log_text.see("end")
                
                ventana_progreso.update_idletasks()
                ventana_progreso.update()

                # Convertir .doc a .docx si es necesario
                if archivo.lower().endswith('.doc'):
                    log_text.insert("end", "   🔄 Convirtiendo .doc a .docx...\n")
                    log_text.see("end")
                    ventana_progreso.update()
                    
                    archivo_docx = convertir_doc_a_docx(archivo)
                    if not archivo_docx:
                        raise Exception("No se pudo convertir el archivo .doc")
                else:
                    archivo_docx = archivo
                
                # Extraer datos del documento
                log_text.insert("end", "   🔍 Extrayendo datos...\n")
                log_text.see("end")
                ventana_progreso.update()
                
                datos = DocumentExtractor.extraer_datos(archivo_docx)
                
                if not datos or not datos.get('dpi'):
                    raise Exception("No se pudo extraer el DPI del documento")
                
                dpi_extraido = datos.get('dpi', 'sin_dpi')
                nombre_extraido = datos.get('nombre', 'sin_nombre')
                
                # Asegurar que existe la carpeta de documentos
                if not os.path.exists(DOCUMENTOS_DIR):
                    os.makedirs(DOCUMENTOS_DIR, exist_ok=True)
                
                # Verificar que el archivo fuente existe
                archivo_fuente = archivo_docx if archivo.lower().endswith('.doc') else archivo
                if not os.path.exists(archivo_fuente):
                    raise Exception(f"Archivo fuente no encontrado: {archivo_fuente}")
                
                # Copiar documento a carpeta de documentos
                log_text.insert("end", "   💾 Copiando documento...\n")
                log_text.see("end")
                ventana_progreso.update()
                
                dpi_limpio = dpi_extraido.replace(' ', '').replace('_', '')
                nombre_limpio = nombre_extraido.replace(' ', '_')
                
                nombre_destino = f"{dpi_limpio}_acta_{nombre_limpio}.docx"
                ruta_destino = os.path.join(DOCUMENTOS_DIR, nombre_destino)
                
                time.sleep(0.05)
                
                # Si existe el archivo destino, eliminarlo primero
                if os.path.exists(ruta_destino):
                    try:
                        os.remove(ruta_destino)
                        time.sleep(0.05)
                    except PermissionError:
                        time.sleep(0.2)
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
                log_text.insert("end", "   💾 Guardando en base de datos...\n")
                log_text.see("end")
                ventana_progreso.update()
                
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

                # ✅ APRENDER SUGERENCIAS DE LOS DATOS EXTRAÍDOS
                self.db.aprender_sugerencias_desde_persona(datos_persona)

                # Guardar documento en la base de datos
                self.db.guardar_documento(persona_id, nombre_destino, ruta_destino, "acta")
                
                if resultado == "guardado":
                    importados += 1
                    log_text.insert("end", f"   ✅ Nuevo registro guardado | DPI: {dpi_extraido}\n\n", "success")
                    success_label.configure(text=f"✅ Nuevos\n{importados}")
                elif resultado == "actualizado":
                    actualizados += 1
                    log_text.insert("end", f"   🔄 Registro actualizado | DPI: {dpi_extraido}\n\n", "update")
                    updated_label.configure(text=f"🔄 Actualizados\n{actualizados}")
                
                log_text.see("end")
                ventana_progreso.update()
                
            except Exception as e:
                errores += 1
                error_label.configure(text=f"❌ Errores\n{errores}")
                log_text.insert("end", f"   ❌ ERROR: {str(e)}\n\n", "error")
                log_text.see("end")
                ventana_progreso.update()
            
            finally:
                # Limpiar archivos temporales
                if archivo.lower().endswith('.doc') and archivo_docx and archivo_docx != archivo:
                    try:
                        time.sleep(0.05)
                        if os.path.exists(archivo_docx):
                            os.unlink(archivo_docx)
                    except:  # noqa: E722
                        pass
        
        # Finalización
        progress_bar.set(1.0)
        percent_label.configure(text="100%")
        current_doc_label.configure(text="✅ Procesamiento completado")
        
        # Log final
        log_text.insert("end", f"\n{'='*70}\n", "info")
        log_text.insert("end", "📊 RESUMEN DEL PROCESAMIENTO\n", "info")
        log_text.insert("end", f"{'='*70}\n", "info")
        log_text.insert("end", f"✅ Nuevos registros: {importados}\n", "success")
        log_text.insert("end", f"🔄 Registros actualizados: {actualizados}\n", "update")
        log_text.insert("end", f"❌ Errores: {errores}\n", "error")
        log_text.insert("end", f"📊 Total procesados: {len(self.documentos_seleccionados)}\n", "info")
        log_text.insert("end", f"{'='*70}\n", "info")
        log_text.see("end")
        
        ventana_progreso.update()
        
        # Habilitar botón cerrar
        btn_cerrar.configure(state="normal")
        
        # Mostrar mensaje de éxito
        messagebox.showinfo(
            "Importación completada",
            f"✅ Nuevos: {importados}\n"
            f"🔄 Actualizados: {actualizados}\n"
            f"❌ Errores: {errores}\n\n"
            f"Total procesados: {len(self.documentos_seleccionados)}"
        )
        
        # Cerrar ventana automáticamente después del mensaje
        cerrar_ventana_progreso()
        
        # Recargar documentos existentes
        self.cargar_documentos_existentes_optimizado()
        if self.callback_actualizar:
            self.callback_actualizar()
        
        # Cambiar a la pestaña de documentos cargados
        self.tabview.set("📚 Cargados")
        
        # Limpiar lista de nuevos documentos
        self.documentos_seleccionados = []
        self.actualizar_lista_documentos()
        self.actualizar_navegacion()
        
        # ✅ SINCRONIZAR después de cargar documentos
        self.ventana.after(100, self.sincronizar_bd_con_archivos)
        
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
            self.cargar_documentos_existentes_optimizado()
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
        self.cargar_documentos_existentes_optimizado()
        if self.callback_actualizar:
            self.callback_actualizar()
        
        # ✅ SINCRONIZAR después de eliminar
        self.ventana.after(100, self.sincronizar_bd_con_archivos)
        
    def verificar_personas_sin_documento(self):
        """
        Verifica qué personas en la BD no tienen documento en la carpeta.
        VERSIÓN OPTIMIZADA.
        """
        try:
            personas = self.db.obtener_todas_personas()
        except Exception as e:
            print(f"Error al obtener personas: {e}")
            return

        # ✅ OPTIMIZACIÓN: Obtener archivos una sola vez
        archivos_carpeta = set()
        if os.path.exists(DOCUMENTOS_DIR):
            archivos_carpeta = {
                f for f in os.listdir(DOCUMENTOS_DIR)
                if f.lower().endswith(('.doc', '.docx'))
            }

        # ✅ OPTIMIZACIÓN: Obtener documentos BD una sola vez
        documentos_bd = self.db.obtener_todos_documentos()

        # Set de persona_id con documento válido
        personas_con_doc = set()

        for doc in documentos_bd:
            nombre_archivo = doc[1]
            persona_id = doc[6] if len(doc) > 6 else None

            if not persona_id:
                continue

            # Validar que existe físicamente
            if nombre_archivo not in archivos_carpeta:
                continue

            personas_con_doc.add(persona_id)

        # Personas sin documento
        personas_sin_doc = [p for p in personas if p[0] not in personas_con_doc]

        if not personas_sin_doc:
            return

        respuesta = messagebox.askyesno(
            "Personas sin documento",
            f"Se encontraron {len(personas_sin_doc)} persona(s) sin documento.\n\n"
            "¿Desea generar automáticamente los documentos?"
        )

        if respuesta:
            self.generar_documentos_faltantes(personas_sin_doc)
    
    def verificar_documentos_sin_registro_bd(self):
        """
        Verifica documentos físicos sin registro en BD.
        VERSIÓN OPTIMIZADA.
        """
        # ✅ OPTIMIZACIÓN: Obtener archivos una sola vez
        archivos_carpeta = []
        if os.path.exists(DOCUMENTOS_DIR):
            archivos_carpeta = [
                f for f in os.listdir(DOCUMENTOS_DIR)
                if f.lower().endswith(('.doc', '.docx'))
            ]
        
        if not archivos_carpeta:
            return
        
        # ✅ OPTIMIZACIÓN: Crear set de nombres en BD
        documentos_bd = self.db.obtener_todos_documentos()
        nombres_en_bd = {doc[1] for doc in documentos_bd}
        
        # Encontrar huérfanos
        documentos_huerfanos = [
            (nombre, os.path.join(DOCUMENTOS_DIR, nombre))
            for nombre in archivos_carpeta
            if nombre not in nombres_en_bd
        ]
        
        if not documentos_huerfanos:
            return
        
        respuesta = messagebox.askyesno(
            "Documentos sin registro",
            f"Se encontraron {len(documentos_huerfanos)} documento(s) sin registro en BD.\n\n"
            "¿Desea procesarlos y registrarlos?"
        )
        
        if respuesta:
            self.procesar_documentos_huerfanos(documentos_huerfanos)
    
    def procesar_documentos_huerfanos(self):
        """
        Procesa documentos huérfanos: registros en BD sin archivo físico.
        VERSIÓN MEJORADA: Actualiza nombres con apellido_casada o regenera.
        """
        import traceback
        
        try:
            # ✅ CORRECCIÓN: Obtener archivos físicos primero
            archivos_fisicos = set()
            if os.path.exists(DOCUMENTOS_DIR):
                archivos_fisicos = {
                    f for f in os.listdir(DOCUMENTOS_DIR)
                    if f.lower().endswith(('.doc', '.docx'))
                }
            
            # ✅ CORRECCIÓN: Obtener documentos de BD y verificar contra archivos físicos
            documentos_bd = self.db.obtener_todos_documentos()
            
            documentos_huerfanos = []
            for doc in documentos_bd:
                # doc: (id, nombre_archivo, ruta_archivo, fecha_carga, nombre_persona, dpi, persona_id, ...)
                nombre_archivo = doc[1]  # ✅ USAR NOMBRE_ARCHIVO, NO RUTA
                
                if nombre_archivo not in archivos_fisicos:
                    documentos_huerfanos.append(doc)
            
            if not documentos_huerfanos:
                messagebox.showinfo(
                    "Sin Huérfanos",
                    "✅ No hay documentos huérfanos.\n\n"
                    "Todos los registros de la base de datos tienen su archivo físico correspondiente."
                )
                return
            
            total_huerfanos = len(documentos_huerfanos)
            
            # Confirmar acción
            respuesta = messagebox.askyesno(
                "Procesar Documentos Huérfanos",
                f"Se encontraron {total_huerfanos} registros en la base de datos "
                f"cuyos archivos ya no existen.\n\n"
                f"¿Desea procesarlos?\n\n"
                f"El sistema intentará:\n"
                f"1. Actualizar nombres con apellido de casada\n"
                f"2. Regenerar documentos faltantes\n"
                f"3. Eliminar registros sin datos de persona",
                icon='question'
            )
            
            if not respuesta:
                return
            
            # Crear ventana de progreso
            ventana_progreso = ctk.CTkToplevel(self.ventana)
            ventana_progreso.title("Procesando Huérfanos")
            ventana_progreso.grab_set()
            ventana_progreso.resizable(False, False)
            
            # Flag para cancelar
            proceso_cancelado = {"cancelado": False}
            
            def cancelar_proceso():
                if proceso_cancelado["cancelado"]:
                    try:
                        cancelar_callbacks_widget(ventana_progreso)
                        ventana_progreso.destroy()
                    except:  # noqa: E722
                        pass
                    return
                
                resp = messagebox.askyesno(
                    "Cancelar proceso",
                    "¿Está seguro de que desea cancelar el proceso?",
                    parent=ventana_progreso
                )
                
                if resp:
                    proceso_cancelado["cancelado"] = True
                    try:
                        cancelar_callbacks_widget(ventana_progreso)
                        ventana_progreso.destroy()
                    except:  # noqa: E722
                        pass
            
            ventana_progreso.protocol("WM_DELETE_WINDOW", cancelar_proceso)
            
            # Frame principal
            main_frame = ctk.CTkFrame(ventana_progreso)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Título
            ctk.CTkLabel(
                main_frame,
                text="🔧 Procesando documentos huérfanos...",
                font=ctk.CTkFont(size=18, weight="bold")
            ).pack(pady=(0, 10))
            
            # Label de progreso
            label_progreso = ctk.CTkLabel(
                main_frame,
                text="Preparando...",
                font=ctk.CTkFont(size=12)
            )
            label_progreso.pack(pady=5)
            
            # Barra de progreso
            barra_progreso = ctk.CTkProgressBar(main_frame, width=500)
            barra_progreso.pack(pady=10)
            barra_progreso.set(0)
            
            # Porcentaje
            percent_label = ctk.CTkLabel(
                main_frame,
                text="0%",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            percent_label.pack(pady=5)
            
            # Log de actividad
            ctk.CTkLabel(
                main_frame,
                text="📋 Registro de actividad:",
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w"
            ).pack(pady=(10, 5), fill="x")
            
            from config import TEXTBOX_WIDTH, TEXTBOX_HEIGHT
            log_text = ctk.CTkTextbox(main_frame, width=TEXTBOX_WIDTH, height=TEXTBOX_HEIGHT)
            log_text.pack(pady=5)
            
            # Botón cancelar
            btn_cancelar = ctk.CTkButton(
                main_frame,
                text="❌ Cancelar",
                command=cancelar_proceso,
                height=35,
                width=150,
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color="#e74c3c",
                hover_color="#c0392b"
            )
            btn_cancelar.pack(pady=10)
            
            # Centrar ventana
            self.center_toplevel(ventana_progreso, 650, 620)
            ventana_progreso.update()
            
            # Contadores
            actualizados = 0
            regenerados = 0
            eliminados = 0
            errores = []
            
            log_text.insert("end", f"{'='*60}\n")
            log_text.insert("end", f"Total de huérfanos a procesar: {total_huerfanos}\n")
            log_text.insert("end", f"{'='*60}\n\n")
            ventana_progreso.update()
            
            # Procesar cada huérfano
            for i, doc in enumerate(documentos_huerfanos, 1):
                if proceso_cancelado["cancelado"]:
                    raise Exception("Proceso cancelado por el usuario")
                
                # Actualizar progreso
                if ventana_progreso.winfo_exists():
                    progreso_actual = i / total_huerfanos
                    barra_progreso.set(progreso_actual)
                    percent_label.configure(text=f"{int(progreso_actual * 100)}%")
                    
                    doc_id = doc[0]
                    persona_id = doc[6] if len(doc) > 6 else None
                    nombre_archivo_viejo = doc[1]
                    
                    label_progreso.configure(
                        text=f"Procesando {i}/{total_huerfanos}: {nombre_archivo_viejo}"
                    )
                    
                    log_text.insert("end", f"[{i}/{total_huerfanos}] {nombre_archivo_viejo}\n")
                    log_text.see("end")
                    ventana_progreso.update()
                
                try:
                    if not persona_id:
                        # Sin datos de persona, eliminar registro
                        self.db.eliminar_documento_por_id(doc_id)
                        eliminados += 1
                        log_text.insert("end", "   🗑️ Eliminado (sin persona asociada)\n\n")
                        log_text.see("end")
                        ventana_progreso.update()
                        continue
                    
                    # Obtener datos de la persona
                    persona = self.db.obtener_persona_por_id(persona_id)
                    
                    if not persona:
                        # Sin datos de persona, eliminar registro
                        self.db.eliminar_documento_por_id(doc_id)
                        eliminados += 1
                        log_text.insert("end", "   🗑️ Eliminado (sin persona asociada)\n\n")
                        log_text.see("end")
                        ventana_progreso.update()
                        continue
                    
                    # Extraer datos de la persona
                    nombre = persona[1] or ""
                    dpi = persona[2] or ""
                    edad = persona[3]
                    estado_civil = persona[4] or ""
                    nacionalidad = persona[5] or ""
                    domicilio = persona[6] or ""
                    nivel_academico = persona[7] or ""
                    apellido_casada = persona[8] or ""
                    sexo = persona[10] if len(persona) > 10 else "masculino"
                    fecha_nacimiento = persona[11] if len(persona) > 11 else ""
                    
                    # Generar nombre correcto con apellido de casada
                    dpi_limpio = dpi.replace(' ', '').replace('_', '') if dpi else 'sin_dpi'
                    nombre_limpio = nombre.replace(' ', '_') if nombre else 'sin_nombre'
                    
                    # ✅ INCLUIR APELLIDO DE CASADA EN EL NOMBRE DEL ARCHIVO
                    if apellido_casada:
                        apellido_casada_limpio = apellido_casada.replace(' ', '_')
                        nombre_archivo_nuevo = f"{dpi_limpio}_acta_{nombre_limpio}_{apellido_casada_limpio}.docx"
                    else:
                        nombre_archivo_nuevo = f"{dpi_limpio}_acta_{nombre_limpio}.docx"
                    
                    ruta_archivo_nuevo = os.path.join(DOCUMENTOS_DIR, nombre_archivo_nuevo)
                    
                    # 🔥 ELIMINAR ARCHIVO ANTIGUO ANTES DE ACTUALIZAR
                    ruta_archivo_viejo = doc[2]  # ruta del registro en BD
                    if os.path.exists(ruta_archivo_viejo) and ruta_archivo_viejo != ruta_archivo_nuevo:
                        try:
                            os.remove(ruta_archivo_viejo)
                            log_text.insert("end", f"   🗑️ Eliminado archivo antiguo: {os.path.basename(ruta_archivo_viejo)}\n")
                        except Exception as e:
                            log_text.insert("end", f"   ⚠️ No se pudo eliminar antiguo: {e}\n")
                    
                    # Verificar si el archivo con el nuevo nombre existe
                    if os.path.exists(ruta_archivo_nuevo):
                        # El archivo existe con el nuevo nombre, actualizar BD
                        self.db.actualizar_ruta_documento(doc_id, nombre_archivo_nuevo, ruta_archivo_nuevo)
                        actualizados += 1
                        log_text.insert("end", f"   ✅ Actualizado: {nombre_archivo_nuevo}\n\n")
                        log_text.see("end")
                        ventana_progreso.update()
                    else:
                        # El archivo no existe, regenerar
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
                        
                        # Asegurar carpeta
                        if not os.path.exists(DOCUMENTOS_DIR):
                            os.makedirs(DOCUMENTOS_DIR, exist_ok=True)
                        
                        # Generar documento
                        VentanaCrearDocumento.generar_documento_para_persona(
                            self.db,
                            datos_persona,
                            ruta_archivo_nuevo
                        )
                        
                        # Actualizar BD
                        self.db.actualizar_ruta_documento(doc_id, nombre_archivo_nuevo, ruta_archivo_nuevo)
                        regenerados += 1
                        log_text.insert("end", f"   🔄 Regenerado: {nombre_archivo_nuevo}\n\n")
                        log_text.see("end")
                        ventana_progreso.update()
                        
                except Exception as e:
                    errores.append(f"{nombre_archivo_viejo} - Error: {str(e)}")
                    log_text.insert("end", f"   ❌ Error: {str(e)}\n\n")
                    log_text.see("end")
                    ventana_progreso.update()
            
            # Finalización
            if ventana_progreso.winfo_exists():
                barra_progreso.set(1.0)
                percent_label.configure(text="100%")
                label_progreso.configure(text="✅ Proceso completado")
                
                # Log final
                log_text.insert("end", f"\n{'='*60}\n")
                log_text.insert("end", "📊 RESUMEN\n")
                log_text.insert("end", f"{'='*60}\n")
                log_text.insert("end", f"📝 Registros actualizados: {actualizados}\n")
                log_text.insert("end", f"🔄 Documentos regenerados: {regenerados}\n")
                log_text.insert("end", f"🗑️ Registros eliminados: {eliminados}\n")
                log_text.insert("end", f"❌ Errores: {len(errores)}\n")
                log_text.insert("end", f"📄 Total procesados: {total_huerfanos}\n")
                log_text.insert("end", f"{'='*60}\n")
                log_text.see("end")
                
                # Cambiar botón a "Cerrar"
                btn_cancelar.configure(
                    text="✓ Cerrar",
                    fg_color=COLOR_PRIMARY,
                    hover_color="#2980b9",
                    command=lambda: ventana_progreso.destroy()
                )
                
                ventana_progreso.update()
            
            # Mostrar resultados
            mensaje_resultado = (
                f"✅ Procesamiento completado\n\n"
                f"📝 Registros actualizados: {actualizados}\n"
                f"🔄 Documentos regenerados: {regenerados}\n"
                f"🗑️ Registros eliminados: {eliminados}\n"
                f"❌ Errores: {len(errores)}\n"
                f"📄 Total procesados: {total_huerfanos}"
            )
            
            if errores:
                mensaje_resultado += f"\n\n⚠️ Errores encontrados: {len(errores)}"
                if len(errores) <= 10:
                    mensaje_resultado += "\n\n" + "\n".join(errores[:10])
                else:
                    mensaje_resultado += f"\n\nMostrando primeros 10 de {len(errores)} errores:\n"
                    mensaje_resultado += "\n".join(errores[:10])
            
            messagebox.showinfo("Procesamiento Completado", mensaje_resultado)
            
            # Recargar documentos
            self.cargar_documentos_existentes_optimizado()
            if self.callback_actualizar:
                self.callback_actualizar()
            
        except Exception as e:
            if 'ventana_progreso' in locals() and ventana_progreso.winfo_exists():
                ventana_progreso.destroy()
            
            if "cancelado" in str(e).lower():
                messagebox.showinfo(
                    "Proceso Cancelado",
                    f"El procesamiento fue cancelado.\n\n"
                    f"Registros procesados: {actualizados + regenerados + eliminados}"
                )
            else:
                messagebox.showerror(
                    "Error en Procesamiento",
                    f"Error durante el procesamiento:\n{str(e)}\n\n{traceback.format_exc()}"
                )
    
    def generar_documentos_faltantes(self, personas_sin_doc):
        """
        Genera documentos de forma masiva para las personas que no tienen.
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
        ventana_progreso.grab_set()
        ventana_progreso.resizable(False, False)
        ventana_progreso.protocol("WM_DELETE_WINDOW", lambda: None)  # Bloquear cierre con X

        # Frame principal
        main_frame = ctk.CTkFrame(ventana_progreso)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            main_frame,
            text="⚙️ Generando documentos para personas sin documento...",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)

        progreso_label = ctk.CTkLabel(
            main_frame,
            text="0 / 0",
            font=ctk.CTkFont(size=13)
        )
        progreso_label.pack(pady=5)

        from config import TEXTBOX_WIDTH, TEXTBOX_HEIGHT
        log_text = ctk.CTkTextbox(main_frame, width=TEXTBOX_WIDTH, height=TEXTBOX_HEIGHT)
        log_text.pack(pady=10)
        
        log_text.tag_config("success", foreground="#2ecc71")
        log_text.tag_config("error", foreground="#e74c3c")
        log_text.tag_config("info", foreground="#3498db")

        def cerrar_ventana_progreso():
            try:
                cancelar_callbacks_widget(ventana_progreso)
                ventana_progreso.destroy()
            except:  # noqa: E722
                pass

        btn_cerrar = ctk.CTkButton(
            main_frame,
            text="✓ Cerrar",
            command=cerrar_ventana_progreso,
            height=35,
            width=150,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLOR_PRIMARY,
            hover_color="#2980b9",
            state="disabled"
        )
        btn_cerrar.pack(pady=10)

        # Centrar ventana
        self.center_toplevel(ventana_progreso, 750, 620)
        ventana_progreso.update_idletasks()
        ventana_progreso.update()

        # Log inicial
        log_text.insert("end", f"{'='*50}\n", "info")
        log_text.insert("end", f"Iniciando generación de {len(personas_sin_doc)} documento(s)\n", "info")
        log_text.insert("end", f"{'='*50}\n\n", "info")
        ventana_progreso.update()

        for i, persona in enumerate(personas_sin_doc):
            try:
                progreso_label.configure(text=f"Procesando {i + 1} / {len(personas_sin_doc)}")
                ventana_progreso.update()

                persona_id = persona[0]
                nombre = persona[1] or ""
                dpi = persona[2] or ""
                edad = persona[3]
                estado_civil = persona[4] or ""
                nacionalidad = persona[5] or ""
                domicilio = persona[6] or ""
                nivel_academico = persona[7] or ""
                apellido_casada = persona[8] or ""
                sexo = persona[10] if len(persona) > 10 else "masculino"
                fecha_nacimiento = persona[11] if len(persona) > 11 else ""

                log_text.insert("end", f"[{i + 1}/{len(personas_sin_doc)}] ", "info")
                log_text.insert("end", f"👤 {nombre} | DPI: {dpi}\n")
                log_text.see("end")
                ventana_progreso.update()

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

                # Eliminar archivo existente si lo hay
                if os.path.exists(ruta_destino):
                    try:
                        os.remove(ruta_destino)
                        time.sleep(0.05)
                    except Exception:
                        pass

                log_text.insert("end", "   📝 Generando documento...\n")
                log_text.see("end")
                ventana_progreso.update()

                # Generar documento
                VentanaCrearDocumento.generar_documento_para_persona(
                    self.db,
                    datos_persona,
                    ruta_destino
                )

                log_text.insert("end", "   💾 Guardando en base de datos...\n")
                log_text.see("end")
                ventana_progreso.update()

                # Guardar documento en BD
                self.db.guardar_documento(persona_id, nombre_destino, ruta_destino, "acta")

                # ✅ APRENDER SUGERENCIAS DE LOS DATOS GENERADOS
                self.db.aprender_sugerencias_desde_persona(datos_persona)

                generados += 1
                log_text.insert("end", f"   ✅ Documento generado: {nombre_destino}\n\n", "success")
                log_text.see("end")
                ventana_progreso.update()

            except Exception as e:
                errores += 1
                log_text.insert("end", f"   ❌ Error: {str(e)}\n", "error")
                log_text.insert("end", f"   Detalles: {traceback.format_exc()}\n\n", "error")
                log_text.see("end")
                ventana_progreso.update()

            time.sleep(0.1)

        # Resumen final
        log_text.insert("end", f"\n{'='*50}\n", "info")
        log_text.insert("end", "📊 RESUMEN GENERACIÓN MASIVA\n", "info")
        log_text.insert("end", f"{'='*50}\n", "info")
        log_text.insert("end", f"✅ Generados: {generados}\n", "success")
        log_text.insert("end", f"❌ Errores: {errores}\n", "error")
        log_text.insert("end", f"📊 Total procesadas: {len(personas_sin_doc)}\n", "info")
        log_text.insert("end", f"{'='*50}\n", "info")
        log_text.see("end")

        # Habilitar botón cerrar
        btn_cerrar.configure(state="normal")

        # Mostrar mensaje final
        messagebox.showinfo(
            "Proceso terminado",
            f"✅ Generados: {generados}\n"
            f"❌ Errores: {errores}\n\n"
            f"Total procesadas: {len(personas_sin_doc)}"
        )

        # Cerrar ventana automáticamente
        cerrar_ventana_progreso()

        # Recargar documentos existentes
        self.cargar_documentos_existentes_optimizado()
        if self.callback_actualizar:
            self.callback_actualizar()
        
    def _acortar_nombre(self, nombre, max_len=50):
        if len(nombre) <= max_len:
            return nombre
        return nombre[:max_len - 3] + "..."
          
    def _convertir_docx_a_pdf_seguro(self, docx_path, pdf_path):
        """
        Envuelve docx2pdf.convert con manejo de errores más robusto para
        evitar 'NoneType has no attribute write' en el ejecutable.
        """
        from tkinter import messagebox
        import os
        import sys
        import io
        import traceback
        import subprocess
        import warnings

        try:
            # Verificar que el DOCX existe
            if not os.path.exists(docx_path):
                raise FileNotFoundError(f"Archivo DOCX no encontrado: {docx_path}")

            # SOLUCIÓN MEJORADA: Proteger completamente stdout/stderr/stdin
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            old_stdin = sys.stdin

            # Crear buffer dummy seguro
            dummy_buffer = io.StringIO()

            try:
                # Reemplazar TODOS los streams con buffers seguros
                sys.stdout = dummy_buffer
                sys.stderr = dummy_buffer
                sys.stdin = dummy_buffer

                # Suprimir también warnings
                warnings.filterwarnings('ignore')

                # Ejecutar conversión en un contexto ultra-protegido
                try:
                    from docx2pdf import convert

                    # Intentar conversión normal
                    convert(docx_path, pdf_path)

                except (AttributeError, Exception) as conv_err:
                    # Si falla con AttributeError de SaveAs / Word COM
                    error_msg = str(conv_err).lower()

                    # Ruta 1: problema típico de Word COM (SaveAs / Open)
                    if 'saveas' in error_msg or 'open.' in error_msg:
                        try:
                            import win32com.client
                            import pythoncom

                            pythoncom.CoInitialize()
                            try:
                                word = win32com.client.DispatchEx("Word.Application")
                                word.Visible = False
                                word.DisplayAlerts = False

                                # Abrir documento
                                doc = word.Documents.Open(os.path.abspath(docx_path))

                                # Guardar como PDF (formato 17 = PDF)
                                doc.SaveAs(os.path.abspath(pdf_path), FileFormat=17)

                                # Cerrar
                                doc.Close()
                                word.Quit()
                            finally:
                                pythoncom.CoUninitialize()

                        except Exception as word_err:
                            raise Exception(f"Error al convertir con Word COM: {word_err}")

                    # Ruta 2: otro AttributeError relacionado con 'write' (bug típico en ejecutable)
                    elif isinstance(conv_err, AttributeError) and 'write' in error_msg:
                        # Intentar método alternativo con subprocess y _convert_helper.py
                        helper_locations = [
                            os.path.join(os.path.dirname(__file__), '_convert_helper.py'),
                            os.path.join(os.path.dirname(sys.executable), 'ui', '_convert_helper.py'),
                            os.path.join(sys._MEIPASS, 'ui', '_convert_helper.py') if getattr(sys, 'frozen', False) else None,
                        ]

                        script_path = None
                        for location in helper_locations:
                            if location and os.path.exists(location):
                                script_path = location
                                break

                        if script_path:
                            result = subprocess.run(
                                [sys.executable, script_path, docx_path, pdf_path],
                                capture_output=True,
                                text=True,
                                timeout=30
                            )
                            if result.returncode != 0:
                                raise Exception(
                                    f"Conversión fallida con método alternativo. "
                                    f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
                                )
                        else:
                            # No hay helper alternativo, relanzar el error original
                            raise conv_err
                    else:
                        # Cualquier otro error se relanza
                        raise conv_err

            finally:
                # Restaurar streams originales SIEMPRE
                try:
                    sys.stdout = old_stdout if old_stdout is not None else sys.__stdout__
                    sys.stderr = old_stderr if old_stderr is not None else sys.__stderr__
                    sys.stdin = old_stdin if old_stdin is not None else sys.__stdin__
                except Exception:
                    # Si falla la restauración, usar los streams por defecto del sistema
                    sys.stdout = sys.__stdout__
                    sys.stderr = sys.__stderr__
                    sys.stdin = sys.__stdin__

            # Verificar que el PDF realmente se creó
            if not os.path.exists(pdf_path):
                raise RuntimeError("No se pudo generar el PDF. Archivo de salida no encontrado.")

            if os.path.getsize(pdf_path) == 0:
                raise RuntimeError("El PDF generado está vacío.")

            return True

        except Exception as e:
            # Log seguro a consola si es posible
            try:
                print(f"Error en conversión DOCX->PDF: {e}")
                traceback.print_exc()
            except Exception:
                pass

            # Preparar mensaje de error amigable
            error_msg = str(e)
            low = error_msg.lower()

            if 'saveas' in low or 'open.' in low:
                error_msg = (
                    "Error de Microsoft Word (COM) al convertir el documento.\n\n"
                    "Posibles soluciones:\n"
                    "• Cierre Microsoft Word completamente.\n"
                    "• Reinicie la aplicación.\n"
                    "• Ejecute la aplicación como administrador.\n\n"
                    f"Detalle técnico: {error_msg}"
                )
            elif 'write' in low or 'nonetype' in low:
                error_msg = (
                    "Error de compatibilidad con Microsoft Word en el entorno del ejecutable.\n\n"
                    "Posibles soluciones:\n"
                    "• Asegúrese de que Microsoft Word esté instalado.\n"
                    "• Cierre Word si está abierto.\n"
                    "• Ejecute la aplicación como administrador.\n\n"
                    f"Detalle técnico: {error_msg}"
                )

            # Mostrar error al usuario
            messagebox.showerror(
                "Error al convertir a PDF",
                f"No se pudo convertir el documento a PDF para vista previa.\n\n{error_msg}"
            )
            return False
    
    def sincronizar_bd_con_archivos(self):
        """
        Sincroniza la base de datos con los archivos físicos.
        - Elimina registros de documentos que no existen físicamente
        - Identifica personas sin documentos
        - Identifica documentos sin registro en BD
        """
        # ✅ CORRECCIÓN: Obtener archivos físicos
        archivos_fisicos = set()
        if os.path.exists(DOCUMENTOS_DIR):
            archivos_fisicos = {
                f for f in os.listdir(DOCUMENTOS_DIR)
                if f.lower().endswith(('.doc', '.docx'))
            }
        
        # Obtener documentos en BD
        documentos_bd = self.db.obtener_todos_documentos()
        
        # ✅ CORRECCIÓN: Limpiar registros huérfanos en BD (documentos que no existen físicamente)
        registros_huerfanos = []
        for doc in documentos_bd:
            # doc: (id, nombre_archivo, ruta_archivo, fecha_carga, nombre_persona, dpi, persona_id, ...)
            nombre_archivo = doc[1]  # ✅ USAR NOMBRE_ARCHIVO, NO RUTA
            
            if nombre_archivo not in archivos_fisicos:
                registros_huerfanos.append(doc)
        
        if registros_huerfanos:
            respuesta = messagebox.askyesno(
                "Registros huérfanos en BD",
                f"Se encontraron {len(registros_huerfanos)} registro(s) en la base de datos "
                f"cuyos archivos ya no existen.\n\n"
                f"¿Desea eliminar estos registros de la base de datos?"
            )
            
            if respuesta:
                eliminados = 0
                for doc in registros_huerfanos:
                    try:
                        self.db.eliminar_documento_por_id(doc[0])
                        eliminados += 1
                    except Exception as e:
                        print(f"Error al eliminar registro {doc[0]}: {e}")
                
                messagebox.showinfo(
                    "Limpieza completada",
                    f"Se eliminaron {eliminados} registro(s) huérfano(s) de la base de datos."
                )
        
        # 2. Verificar consistencia personas-documentos
        self.verificar_consistencia_personas_documentos()

    def regenerar_todos_los_documentos_desde_bd(self):
        """
        Regenera TODOS los documentos desde la base de datos usando apellido_casada.
        VERSIÓN ADAPTADA A CUSTOMTKINTER.
        """
        import traceback
        
        # Confirmar acción
        respuesta = messagebox.askyesno(
            "Confirmar Regeneración",
            "⚠️ ADVERTENCIA ⚠️\n\n"
            "Esta acción:\n"
            "• Eliminará TODOS los archivos PDF/DOCX existentes\n"
            "• Regenerará todos los documentos desde la base de datos\n"
            "• Puede tardar varios minutos\n\n"
            "¿Desea continuar?",
            icon='warning'
        )
        
        if not respuesta:
            return
        
        # Crear ventana de progreso con CustomTkinter
        ventana_progreso = ctk.CTkToplevel(self.ventana)
        ventana_progreso.title("Regenerando Documentos")
        ventana_progreso.grab_set()
        ventana_progreso.resizable(False, False)
        
        # Flag para cancelar
        proceso_cancelado = {"cancelado": False}
        
        def cancelar_proceso():
            if proceso_cancelado["cancelado"]:
                try:
                    cancelar_callbacks_widget(ventana_progreso)
                    ventana_progreso.destroy()
                except:  # noqa: E722
                    pass
                return
            
            resp = messagebox.askyesno(
                "Cancelar proceso",
                "¿Está seguro de que desea cancelar el proceso?\n\n"
                "Los documentos ya generados se mantendrán.",
                parent=ventana_progreso
            )
            
            if resp:
                proceso_cancelado["cancelado"] = True
                try:
                    cancelar_callbacks_widget(ventana_progreso)
                    ventana_progreso.destroy()
                except:  # noqa: E722
                    pass
        
        # Configurar protocolo de cierre
        ventana_progreso.protocol("WM_DELETE_WINDOW", cancelar_proceso)
        
        # Frame principal
        main_frame = ctk.CTkFrame(ventana_progreso)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        ctk.CTkLabel(
            main_frame,
            text="♻️ Regenerando documentos desde la base de datos...",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(0, 10))
        
        # Label de progreso
        label_progreso = ctk.CTkLabel(
            main_frame,
            text="Preparando...",
            font=ctk.CTkFont(size=12)
        )
        label_progreso.pack(pady=5)
        
        # Barra de progreso
        barra_progreso = ctk.CTkProgressBar(main_frame, width=500)
        barra_progreso.pack(pady=10)
        barra_progreso.set(0)
        
        # Porcentaje
        percent_label = ctk.CTkLabel(
            main_frame,
            text="0%",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        percent_label.pack(pady=5)
        
        # Log de actividad
        ctk.CTkLabel(
            main_frame,
            text="📋 Registro de actividad:",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        ).pack(pady=(10, 5), fill="x")
        
        from config import TEXTBOX_WIDTH, TEXTBOX_HEIGHT
        log_text = ctk.CTkTextbox(main_frame, width=TEXTBOX_WIDTH, height=TEXTBOX_HEIGHT)
        log_text.pack(pady=5)
        
        # Botón cancelar
        btn_cancelar = ctk.CTkButton(
            main_frame,
            text="❌ Cancelar",
            command=cancelar_proceso,
            height=35,
            width=150,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#e74c3c",
            hover_color="#c0392b"
        )
        btn_cancelar.pack(pady=10)
        
        # Centrar ventana
        self.center_toplevel(ventana_progreso, 650, 620)
        
        try:
            ventana_progreso.update()
        except:  # noqa: E722
            return
        
        try:
            # 1. ELIMINAR TODOS LOS ARCHIVOS EXISTENTES
            if ventana_progreso.winfo_exists():
                label_progreso.configure(text="Eliminando archivos existentes...")
                ventana_progreso.update()
            
            archivos_eliminados = 0
            if os.path.exists(DOCUMENTOS_DIR):
                for archivo in os.listdir(DOCUMENTOS_DIR):
                    if proceso_cancelado["cancelado"]:
                        raise Exception("Proceso cancelado por el usuario")
                        
                    if archivo.lower().endswith(('.pdf', '.doc', '.docx')):
                        ruta_archivo = os.path.join(DOCUMENTOS_DIR, archivo)
                        try:
                            os.remove(ruta_archivo)
                            archivos_eliminados += 1
                        except Exception as e:
                            print(f"Error al eliminar {archivo}: {e}")
            
            # 2. OBTENER TODAS LAS PERSONAS DE LA BD
            if ventana_progreso.winfo_exists():
                label_progreso.configure(text="Obteniendo datos de la base de datos...")
                ventana_progreso.update()
            
            personas = self.db.obtener_todas_personas()
            total_personas = len(personas)
            
            if total_personas == 0:
                messagebox.showwarning(
                    "Sin Datos",
                    "No hay personas en la base de datos para regenerar documentos."
                )
                ventana_progreso.destroy()
                return
            
            # Log inicial
            log_text.insert("end", f"{'='*60}\n")
            log_text.insert("end", f"Archivos eliminados: {archivos_eliminados}\n")
            log_text.insert("end", f"Personas a procesar: {total_personas}\n")
            log_text.insert("end", f"{'='*60}\n\n")
            ventana_progreso.update()
            
            # 3. REGENERAR DOCUMENTOS
            documentos_generados = 0
            documentos_fallidos = 0
            errores = []
            
            for i, persona in enumerate(personas, 1):
                if proceso_cancelado["cancelado"]:
                    raise Exception("Proceso cancelado por el usuario")
                
                # Actualizar progreso visual
                if ventana_progreso.winfo_exists():
                    progreso_actual = i / total_personas
                    barra_progreso.set(progreso_actual)
                    percent_label.configure(text=f"{int(progreso_actual * 100)}%")
                    
                    persona_id = persona[0]
                    nombre = persona[1] or ""
                    dpi = persona[2] or ""
                    edad = persona[3]
                    estado_civil = persona[4] or ""
                    nacionalidad = persona[5] or ""
                    domicilio = persona[6] or ""
                    nivel_academico = persona[7] or ""
                    apellido_casada = persona[8] or ""
                    sexo = persona[10] if len(persona) > 10 else "masculino"
                    fecha_nacimiento = persona[11] if len(persona) > 11 else ""
                    
                    label_progreso.configure(
                        text=f"Generando documento {i}/{total_personas}: {nombre}"
                    )
                    
                    log_text.insert("end", f"[{i}/{total_personas}] {nombre} | DPI: {dpi}\n")
                    log_text.see("end")
                    ventana_progreso.update()
                
                try:
                    # Construir datos de la persona
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
                    
                    # GENERAR NOMBRE DE ARCHIVO CON APELLIDO DE CASADA
                    dpi_limpio = dpi.replace(' ', '').replace('_', '') if dpi else 'sin_dpi'
                    nombre_limpio = nombre.replace(' ', '_') if nombre else 'sin_nombre'
                    
                    # ✅ INCLUIR APELLIDO DE CASADA EN EL NOMBRE DEL ARCHIVO
                    if apellido_casada:
                        apellido_casada_limpio = apellido_casada.replace(' ', '_')
                        nombre_archivo = f"{dpi_limpio}_acta_{nombre_limpio}_{apellido_casada_limpio}.docx"
                    else:
                        nombre_archivo = f"{dpi_limpio}_acta_{nombre_limpio}.docx"
                    
                    ruta_destino = os.path.join(DOCUMENTOS_DIR, nombre_archivo)
                    
                    # Asegurar carpeta
                    if not os.path.exists(DOCUMENTOS_DIR):
                        os.makedirs(DOCUMENTOS_DIR, exist_ok=True)
                    
                    # Generar documento desde plantilla
                    VentanaCrearDocumento.generar_documento_para_persona(
                        self.db,
                        datos_persona,
                        ruta_destino
                    )
                    
                    # Registrar en BD
                    self.db.guardar_documento(
                        persona_id=persona_id,
                        nombre_archivo=nombre_archivo,
                        ruta_archivo=ruta_destino,
                        tipo_documento="acta"
                    )
                    
                    documentos_generados += 1
                    log_text.insert("end", f"   ✅ Generado: {nombre_archivo}\n\n")
                    log_text.see("end")
                    ventana_progreso.update()
                        
                except Exception as e:
                    documentos_fallidos += 1
                    errores.append(f"{nombre} (DPI: {dpi}) - Error: {str(e)}")
                    log_text.insert("end", f"   ❌ Error: {str(e)}\n\n")
                    log_text.see("end")
                    ventana_progreso.update()
            
            # 4. FINALIZACIÓN
            if ventana_progreso.winfo_exists():
                barra_progreso.set(1.0)
                percent_label.configure(text="100%")
                label_progreso.configure(text="✅ Proceso completado")
                
                # Log final
                log_text.insert("end", f"\n{'='*60}\n")
                log_text.insert("end", "📊 RESUMEN\n")
                log_text.insert("end", f"{'='*60}\n")
                log_text.insert("end", f"📄 Archivos eliminados: {archivos_eliminados}\n")
                log_text.insert("end", f"✅ Documentos generados: {documentos_generados}\n")
                log_text.insert("end", f"❌ Documentos fallidos: {documentos_fallidos}\n")
                log_text.insert("end", f"👥 Total personas: {total_personas}\n")
                log_text.insert("end", f"{'='*60}\n")
                log_text.see("end")
                
                # Cambiar botón a "Cerrar"
                btn_cancelar.configure(
                    text="✓ Cerrar",
                    fg_color=COLOR_PRIMARY,
                    hover_color="#2980b9",
                    command=lambda: ventana_progreso.destroy()
                )
                
                ventana_progreso.update()
            
            # 5. MOSTRAR RESULTADOS
            mensaje_resultado = (
                f"✅ Regeneración completada\n\n"
                f"📄 Archivos eliminados: {archivos_eliminados}\n"
                f"✅ Documentos generados: {documentos_generados}\n"
                f"❌ Documentos fallidos: {documentos_fallidos}\n"
                f"👥 Total personas: {total_personas}"
            )
            
            if errores:
                mensaje_resultado += f"\n\n⚠️ Errores encontrados: {len(errores)}"
                if len(errores) <= 10:
                    mensaje_resultado += "\n\n" + "\n".join(errores[:10])
                else:
                    mensaje_resultado += f"\n\nMostrando primeros 10 de {len(errores)} errores:\n"
                    mensaje_resultado += "\n".join(errores[:10])
            
            messagebox.showinfo("Regeneración Completada", mensaje_resultado)
            
            # 6. RECARGAR DOCUMENTOS
            self.cargar_documentos_existentes_optimizado()
            if self.callback_actualizar:
                self.callback_actualizar()
            
        except Exception as e:
            if ventana_progreso.winfo_exists():
                ventana_progreso.destroy()
            
            if "cancelado" in str(e).lower():
                messagebox.showinfo(
                    "Proceso Cancelado",
                    f"La regeneración fue cancelada.\n\n"
                    f"Documentos generados antes de cancelar: {documentos_generados}"
                )
            else:
                messagebox.showerror(
                    "Error en Regeneración",
                    f"Error durante la regeneración:\n{str(e)}\n\n{traceback.format_exc()}"
                )

    def verificar_consistencia_personas_documentos(self):
        """
        Verifica la consistencia entre personas y documentos (relación 1:1).
        NO maneja duplicados - solo verifica cantidades.
        """
        try:
            # Obtener totales
            total_personas = self.db.contar_personas()
            
            # Contar archivos físicos (no registros de BD)
            total_documentos_fisicos = 0
            if os.path.exists(DOCUMENTOS_DIR):
                archivos = [f for f in os.listdir(DOCUMENTOS_DIR) 
                        if f.lower().endswith(('.pdf', '.doc', '.docx'))]
                total_documentos_fisicos = len(archivos)
            
            # Verificar consistencia
            if total_personas == total_documentos_fisicos:
                messagebox.showinfo(
                    "✅ Consistencia Verificada",
                    f"La base de datos está consistente:\n\n"
                    f"👥 Personas: {total_personas}\n"
                    f"📄 Documentos: {total_documentos_fisicos}\n\n"
                    f"✓ Relación 1:1 correcta"
                )
            else:
                diferencia = abs(total_personas - total_documentos_fisicos)
                
                if total_documentos_fisicos > total_personas:
                    tipo_problema = "documentos de más"
                    icono = "⚠️"
                else:
                    tipo_problema = "documentos faltantes"
                    icono = "❌"
                
                respuesta = messagebox.askyesno(
                    f"{icono} Inconsistencia Detectada",
                    f"Se detectó una inconsistencia:\n\n"
                    f"👥 Personas en BD: {total_personas}\n"
                    f"📄 Documentos físicos: {total_documentos_fisicos}\n"
                    f"⚠️ Diferencia: {diferencia} {tipo_problema}\n\n"
                    f"¿Desea corregir los problemas de sincronización?",
                    icon='warning'
                )
                
                if respuesta:
                    self.corregir_problemas_sincronizacion()
        
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error al verificar consistencia:\n{str(e)}"
            )
    
    def corregir_problemas_sincronizacion(self):
        """
        Corrige problemas de sincronización entre BD y archivos físicos.
        """
        try:
            # ✅ CORRECCIÓN: Obtener archivos físicos
            archivos_fisicos = set()
            if os.path.exists(DOCUMENTOS_DIR):
                archivos_fisicos = {
                    f for f in os.listdir(DOCUMENTOS_DIR)
                    if f.lower().endswith(('.doc', '.docx'))
                }
            
            # Obtener documentos de BD
            documentos_bd = self.db.obtener_todos_documentos()
            
            # ✅ CORRECCIÓN: Identificar huérfanos usando nombre_archivo
            documentos_huerfanos = []
            for doc in documentos_bd:
                nombre_archivo = doc[1]  # ✅ USAR NOMBRE_ARCHIVO
                if nombre_archivo not in archivos_fisicos:
                    documentos_huerfanos.append(doc)
            
            # ✅ CORRECCIÓN: Obtener archivos sin registro en BD
            nombres_bd = {doc[1] for doc in documentos_bd}  # ✅ USAR NOMBRE_ARCHIVO
            archivos_sin_registro = list(archivos_fisicos - nombres_bd)
            
            total_huerfanos = len(documentos_huerfanos)
            total_sin_registro = len(archivos_sin_registro)
            
            if total_huerfanos == 0 and total_sin_registro == 0:
                messagebox.showinfo(
                    "✅ Sin Problemas",
                    "No se encontraron problemas de sincronización."
                )
                return
            
            # Mostrar resumen de problemas
            mensaje = "Se encontraron los siguientes problemas:\n\n"
            
            if total_huerfanos > 0:
                mensaje += f"📝 {total_huerfanos} registros en BD sin archivo físico\n"
            
            if total_sin_registro > 0:
                mensaje += f"📄 {total_sin_registro} archivos sin registro en BD\n"
            
            mensaje += "\n¿Qué desea hacer?"
            
            # Crear ventana de opciones - ✅ CORRECCIÓN: usar self.ventana
            ventana_opciones = ctk.CTkToplevel(self.ventana)
            ventana_opciones.title("Corregir Problemas de Sincronización")
            ventana_opciones.transient(self.ventana)
            ventana_opciones.grab_set()
            
            self.center_toplevel(ventana_opciones, 700, 450)
            
            # Frame principal con padding
            frame_principal = ctk.CTkFrame(ventana_opciones, fg_color="transparent")
            frame_principal.pack(fill="both", expand=True, padx=30, pady=30)
            
            # Título
            lbl_titulo = ctk.CTkLabel(
                frame_principal,
                text="Seleccione una opción para corregir problemas:",
                font=("Segoe UI", 16, "bold")
            )
            lbl_titulo.pack(pady=(0, 25))
            
            # Frame para los botones con grid
            frame_botones = ctk.CTkFrame(frame_principal, fg_color="transparent")
            frame_botones.pack(fill="both", expand=True)
            
            # Configurar columnas para que tengan el mismo peso
            frame_botones.grid_columnconfigure(0, weight=1, uniform="botones")
            frame_botones.grid_columnconfigure(1, weight=1, uniform="botones")
            
            # Configurar filas
            frame_botones.grid_rowconfigure(0, weight=1)
            frame_botones.grid_rowconfigure(1, weight=1)
            frame_botones.grid_rowconfigure(2, weight=1)
            
            # Botón 1: Procesar documentos huérfanos (Fila 0, Columna 0)
            btn_huerfanos = ctk.CTkButton(
                frame_botones,
                text="Procesar Documentos Huérfanos\n(Archivos sin registro en BD)",
                font=("Segoe UI", 13),
                height=70,
                command=lambda: [ventana_opciones.destroy(), self.procesar_documentos_huerfanos()]
            )
            btn_huerfanos.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
            
            # Botón 2: Registrar archivos sin BD (Fila 0, Columna 1)
            btn_registrar = ctk.CTkButton(
                frame_botones,
                text="Registrar Archivos sin BD\n(Crear registros faltantes)",
                font=("Segoe UI", 13),
                height=70,
                command=lambda: [ventana_opciones.destroy(), self.registrar_archivos_sin_bd(archivos_sin_registro)]
            )
            btn_registrar.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
            
            # Botón 3: Regenerar documentos desde BD (Fila 1, Columna 0)
            btn_regenerar = ctk.CTkButton(
                frame_botones,
                text="Regenerar Todos los Documentos\n(Desde registros en BD)",
                font=("Segoe UI", 13),
                height=70,
                command=lambda: [ventana_opciones.destroy(), self.regenerar_todos_los_documentos_desde_bd()]
            )
            btn_regenerar.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
            
            # Botón 4: Limpiar duplicados (Fila 1, Columna 1)
            btn_limpiar = ctk.CTkButton(
                frame_botones,
                text="Limpiar Documentos Duplicados\n(Eliminar registros antiguos)",
                font=("Segoe UI", 13),
                height=70,
                command=lambda: [ventana_opciones.destroy(), self.limpiar_duplicados_bd()]
            )
            btn_limpiar.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
            
            # Botón 5: Sincronización completa (Fila 2, Columna 0)
            btn_sincronizar = ctk.CTkButton(
                frame_botones,
                text="Sincronización Completa\n(BD ↔ Archivos)",
                font=("Segoe UI", 13),
                height=70,
                command=lambda: [ventana_opciones.destroy(), self.sincronizar_bd_con_archivos()]
            )
            btn_sincronizar.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
            
            # Botón 6: Cancelar (Fila 2, Columna 1)
            btn_cancelar = ctk.CTkButton(
                frame_botones,
                text="Cancelar",
                font=("Segoe UI", 13),
                height=70,
                fg_color="#666666",
                hover_color="#555555",
                command=ventana_opciones.destroy
            )
            btn_cancelar.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")
        
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error al corregir sincronización:\n{str(e)}"
            )

    def registrar_archivos_sin_bd(self, archivos):
        """
        Registra archivos físicos que no tienen registro en la BD.
        """
        if not archivos:
            messagebox.showinfo("Sin Archivos", "No hay archivos para registrar.")
            return
        
        try:
            registrados = 0
            no_registrados = 0
            errores = []
            
            for nombre_archivo in archivos:
                try:
                    ruta_archivo = os.path.join(DOCUMENTOS_DIR, nombre_archivo)
                    
                    # Extraer DPI del nombre del archivo
                    # Formato esperado: DPI_acta_NOMBRE.docx
                    partes = nombre_archivo.split('_')
                    if len(partes) >= 2:
                        dpi = partes[0]
                        
                        # Buscar persona por DPI
                        persona = self.db.obtener_persona_por_dpi(dpi)
                        
                        if persona:
                            persona_id = persona[0]
                            
                            # Verificar si ya existe un registro para esta persona
                            docs_persona = self.db.obtener_documentos_por_persona(persona_id)
                            
                            if not docs_persona:
                                # Registrar documento
                                self.db.guardar_documento(
                                    persona_id=persona_id,
                                    nombre_archivo=nombre_archivo,  # ✅ PASAR NOMBRE_ARCHIVO
                                    ruta_archivo=ruta_archivo,
                                    tipo_documento="acta"
                                )
                                registrados += 1
                            else:
                                no_registrados += 1
                                errores.append(f"{nombre_archivo} - Ya existe registro para esta persona")
                        else:
                            no_registrados += 1
                            errores.append(f"{nombre_archivo} - No se encontró persona con DPI {dpi}")
                    else:
                        no_registrados += 1
                        errores.append(f"{nombre_archivo} - Formato de nombre inválido")
                
                except Exception as e:
                    no_registrados += 1
                    errores.append(f"{nombre_archivo} - Error: {str(e)}")
            
            # Mostrar resultados
            mensaje = (
                f"✅ Archivos registrados: {registrados}\n"
                f"❌ No registrados: {no_registrados}\n"
                f"📄 Total procesados: {len(archivos)}"
            )
            
            if errores and len(errores) <= 10:
                mensaje += "\n\nErrores:\n" + "\n".join(errores)
            elif errores:
                mensaje += f"\n\n⚠️ {len(errores)} errores (mostrando primeros 10):\n"
                mensaje += "\n".join(errores[:10])
            
            messagebox.showinfo("Registro Completado", mensaje)
            
            # Recargar documentos
            self.cargar_documentos_existentes_optimizado()
            if self.callback_actualizar:
                self.callback_actualizar()
        
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error al registrar archivos:\n{str(e)}"
            )
    
    def limpiar_documentos_duplicados(self, personas_con_multiples):
        """
        Elimina documentos duplicados, conservando solo el más reciente por persona.
        """
        # Crear ventana de progreso
        ventana_progreso = ctk.CTkToplevel(self.ventana)
        ventana_progreso.title("🧹 Limpiando documentos duplicados...")
        ventana_progreso.grab_set()
        ventana_progreso.resizable(False, False)
        ventana_progreso.protocol("WM_DELETE_WINDOW", lambda: None)
        
        main_frame = ctk.CTkFrame(ventana_progreso)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            main_frame,
            text="🧹 Limpiando documentos duplicados...",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)
        
        # Estadísticas
        stats_frame = ctk.CTkFrame(main_frame)
        stats_frame.pack(pady=10, fill="x")
        stats_frame.grid_columnconfigure((0, 1), weight=1)
        
        conservados_label = ctk.CTkLabel(
            stats_frame,
            text="✅ Conservados\n0",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#2ecc71"
        )
        conservados_label.grid(row=0, column=0, padx=5, pady=10)
        
        eliminados_label = ctk.CTkLabel(
            stats_frame,
            text="🗑️ Eliminados\n0",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#e74c3c"
        )
        eliminados_label.grid(row=0, column=1, padx=5, pady=10)
        
        # Progreso
        progreso_label = ctk.CTkLabel(
            main_frame,
            text="Preparando...",
            font=ctk.CTkFont(size=13)
        )
        progreso_label.pack(pady=10)
        
        # Log
        from config import TEXTBOX_WIDTH, TEXTBOX_HEIGHT
        log_text = ctk.CTkTextbox(main_frame, width=TEXTBOX_WIDTH, height=TEXTBOX_HEIGHT)
        log_text.pack(pady=10)
        
        log_text.tag_config("success", foreground="#2ecc71")
        log_text.tag_config("error", foreground="#e74c3c")
        log_text.tag_config("info", foreground="#3498db")
        log_text.tag_config("warning", foreground="#f39c12")
        
        def cerrar_ventana():
            try:
                cancelar_callbacks_widget(ventana_progreso)
                ventana_progreso.destroy()
            except:  # noqa: E722
                pass
        
        btn_cerrar = ctk.CTkButton(
            main_frame,
            text="✓ Cerrar",
            command=cerrar_ventana,
            height=35,
            width=150,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLOR_PRIMARY,
            hover_color="#2980b9",
            state="disabled"
        )
        btn_cerrar.pack(pady=10)
        
        self.center_toplevel(ventana_progreso, 750, 620)
        ventana_progreso.update()
        
        # Contadores
        total_conservados = 0
        total_eliminados = 0
        errores = 0
        
        log_text.insert("end", f"{'='*70}\n", "info")
        log_text.insert("end", f"Procesando {len(personas_con_multiples)} persona(s) con documentos duplicados\n", "info")
        log_text.insert("end", f"{'='*70}\n\n", "info")
        ventana_progreso.update()
        
        # Obtener todos los documentos de BD
        documentos_bd = self.db.obtener_todos_documentos()
        
        for i, (persona, nombres_docs) in enumerate(personas_con_multiples):
            try:
                persona_id = persona[0]
                nombre_persona = persona[1]
                dpi_persona = persona[2]

                progreso_label.configure(
                    text=f"Procesando {i + 1} / {len(personas_con_multiples)}: {nombre_persona}"
                )
                ventana_progreso.update()

                log_text.insert("end", f"[{i + 1}/{len(personas_con_multiples)}] ", "info")
                log_text.insert("end", f"👤 {nombre_persona} (DPI: {dpi_persona}) [ID: {persona_id}]\n")
                log_text.insert("end", f"   📄 Encontrados {len(nombres_docs)} documentos\n", "warning")
                log_text.see("end")
                ventana_progreso.update()
                
                # Buscar información completa de cada documento
                docs_persona = []
                for doc in documentos_bd:
                    if doc[1] in nombres_docs:  # doc[1] = nombre_archivo
                        ruta_archivo = os.path.join(DOCUMENTOS_DIR, doc[1])
                        if os.path.exists(ruta_archivo):
                            try:
                                mtime = os.path.getmtime(ruta_archivo)
                                docs_persona.append({
                                    'id': doc[0],
                                    'nombre': doc[1],
                                    'ruta': ruta_archivo,
                                    'mtime': mtime
                                })
                            except OSError:
                                log_text.insert("end", f"   ⚠️ No se pudo obtener fecha de: {doc[1]}\n", "warning")
                
                if not docs_persona:
                    log_text.insert("end", "   ⚠️ No se encontraron archivos físicos\n\n", "warning")
                    continue
                
                # Ordenar por fecha de modificación (más reciente primero)
                docs_persona.sort(key=lambda x: x['mtime'], reverse=True)
                
                # El primero es el más reciente (se conserva)
                doc_conservar = docs_persona[0]
                docs_eliminar = docs_persona[1:]
                
                # Mostrar documento a conservar
                fecha_conservar = datetime.datetime.fromtimestamp(doc_conservar['mtime']).strftime("%Y-%m-%d %H:%M:%S")
                log_text.insert("end", f"   ✅ CONSERVAR: {doc_conservar['nombre']}\n", "success")
                log_text.insert("end", f"      Fecha: {fecha_conservar}\n", "success")
                
                total_conservados += 1
                conservados_label.configure(text=f"✅ Conservados\n{total_conservados}")
                
                # Eliminar los demás documentos
                for doc_elim in docs_eliminar:
                    try:
                        fecha_elim = datetime.datetime.fromtimestamp(doc_elim['mtime']).strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Eliminar archivo físico
                        if os.path.exists(doc_elim['ruta']):
                            os.remove(doc_elim['ruta'])
                            log_text.insert("end", f"   🗑️ ELIMINADO: {doc_elim['nombre']}\n", "error")
                            log_text.insert("end", f"      Fecha: {fecha_elim}\n", "error")
                        
                        # Eliminar registro de BD
                        self.db.eliminar_documento_por_id(doc_elim['id'])
                        
                        total_eliminados += 1
                        eliminados_label.configure(text=f"🗑️ Eliminados\n{total_eliminados}")
                        
                    except Exception as e:
                        log_text.insert("end", f"   ❌ Error al eliminar {doc_elim['nombre']}: {str(e)}\n", "error")
                        errores += 1
                
                log_text.insert("end", "\n")
                log_text.see("end")
                ventana_progreso.update()
                
            except Exception as e:
                log_text.insert("end", f"   ❌ Error general: {str(e)}\n\n", "error")
                errores += 1
                log_text.see("end")
                ventana_progreso.update()
        
        # Resumen final
        log_text.insert("end", f"\n{'='*70}\n", "info")
        log_text.insert("end", "📊 RESUMEN DE LIMPIEZA\n", "info")
        log_text.insert("end", f"{'='*70}\n", "info")
        log_text.insert("end", f"✅ Documentos conservados: {total_conservados}\n", "success")
        log_text.insert("end", f"🗑️ Documentos eliminados: {total_eliminados}\n", "error")
        if errores > 0:
            log_text.insert("end", f"❌ Errores: {errores}\n", "error")
        log_text.insert("end", f"📊 Personas procesadas: {len(personas_con_multiples)}\n", "info")
        log_text.insert("end", f"{'='*70}\n", "info")
        log_text.see("end")
        
        # Habilitar botón cerrar
        btn_cerrar.configure(state="normal")
        
        # Mensaje final
        mensaje_final = (
            f"✅ Documentos conservados: {total_conservados}\n"
            f"🗑️ Documentos eliminados: {total_eliminados}\n"
            f"📊 Personas procesadas: {len(personas_con_multiples)}"
        )
        
        if errores > 0:
            mensaje_final += f"\n❌ Errores: {errores}"
        
        messagebox.showinfo("Limpieza completada", mensaje_final)
        
        # Cerrar ventana
        cerrar_ventana()
    
    def eliminar_del_listado(self, index):
        """
        Elimina un documento del listado de documentos a procesar (antes de cargar a BD).
        """
        if index < 0 or index >= len(self.documentos_seleccionados):
            return
        
        nombre_archivo = os.path.basename(self.documentos_seleccionados[index])
        
        respuesta = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Desea eliminar este documento del listado?\n\n"
            f"📄 {nombre_archivo}\n\n"
            f"Nota: El documento NO se procesará ni se cargará a la base de datos.",
            icon='warning'
        )
        
        if not respuesta:
            return
        
        # Eliminar del listado
        self.documentos_seleccionados.pop(index)
        
        # Ajustar índice actual si es necesario
        if self.documento_actual_index >= len(self.documentos_seleccionados):
            self.documento_actual_index = max(0, len(self.documentos_seleccionados) - 1)
        
        # Actualizar UI
        self.actualizar_lista_documentos()
        self.actualizar_navegacion()
        
        # Mostrar documento actual si hay documentos
        if self.documentos_seleccionados:
            self.mostrar_documento_actual()
        else:
            # Limpiar visor si no hay más documentos
            for widget in self.visor_scroll.winfo_children():
                widget.destroy()
            
            self.lbl_visor_estado = ctk.CTkLabel(
                self.visor_scroll,
                text="Seleccione documentos para visualizar",
                text_color="gray",
                font=ctk.CTkFont(size=14)
            )
            self.lbl_visor_estado.pack(pady=200)
        
        # Mensaje de confirmación
        messagebox.showinfo(
            "Eliminado",
            f"Documento eliminado del listado:\n{nombre_archivo}\n\n"
            f"Documentos restantes: {len(self.documentos_seleccionados)}"
        )
    
    def limpiar_listado_completo(self):
        """
        Limpia completamente el listado de documentos a procesar.
        """
        if not self.documentos_seleccionados:
            messagebox.showinfo("Información", "No hay documentos en el listado.")
            return
        
        respuesta = messagebox.askyesno(
            "Confirmar limpieza",
            f"¿Desea eliminar TODOS los documentos del listado?\n\n"
            f"📊 Total: {len(self.documentos_seleccionados)} documento(s)\n\n"
            f"Nota: Los documentos NO se procesarán ni se cargarán a la base de datos.",
            icon='warning'
        )
        
        if not respuesta:
            return
        
        # Limpiar todo
        self.documentos_seleccionados = []
        self.documento_actual_index = 0
        
        # Actualizar UI
        self.actualizar_lista_documentos()
        self.actualizar_navegacion()
        
        # Limpiar visor
        for widget in self.visor_scroll.winfo_children():
            widget.destroy()
        
        self.lbl_visor_estado = ctk.CTkLabel(
            self.visor_scroll,
            text="Seleccione documentos para visualizar",
            text_color="gray",
            font=ctk.CTkFont(size=14)
        )
        self.lbl_visor_estado.pack(pady=200)
        
        messagebox.showinfo("Limpieza completada", "Se eliminaron todos los documentos del listado.")
    
    def limpiar_duplicados_bd(self):
        """
        Wrapper para limpiar duplicados desde el menú de sincronización.
        """
        try:
            # Obtener personas con múltiples documentos
            documentos_bd = self.db.obtener_todos_documentos()
            
            # Agrupar por persona_id
            docs_por_persona = {}
            for doc in documentos_bd:
                persona_id = doc[6] if len(doc) > 6 else None
                if persona_id:
                    if persona_id not in docs_por_persona:
                        docs_por_persona[persona_id] = []
                    docs_por_persona[persona_id].append(doc[1])  # nombre_archivo
            
            # Filtrar personas con múltiples documentos
            personas_con_multiples = []
            for persona_id, nombres_docs in docs_por_persona.items():
                if len(nombres_docs) > 1:
                    persona = self.db.obtener_persona_por_id(persona_id)
                    if persona:
                        personas_con_multiples.append((persona, nombres_docs))
            
            if not personas_con_multiples:
                messagebox.showinfo(
                    "Sin Duplicados",
                    "✅ No se encontraron documentos duplicados."
                )
                return
            
            # Llamar al método de limpieza
            self.limpiar_documentos_duplicados(personas_con_multiples)
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error al buscar duplicados:\n{str(e)}"
            )
    