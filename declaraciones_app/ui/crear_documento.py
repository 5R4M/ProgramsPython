import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk
import os
import shutil
import tempfile
from docx import Document
from datetime import datetime
from PIL import Image, ImageTk
import fitz  # PyMuPDF
from docx2pdf import convert
from config import PLANTILLAS_DIR, COLOR_SUCCESS, COLOR_WARNING, DOCUMENTOS_DIR
from utils import NumeroATexto
import subprocess
import platform


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
        
        self.cargar_iconos()
        
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
                self.center_window_tamano(740, 625)
            else:
                # Modo NORMAL: con visor
                self.center_window_tamano(1400, 900)
                self.ventana.after(100, self.maximizar_ventana)
    
    def cargar_iconos(self):
        """Carga los iconos PNG para los botones"""
        try:
            # Ruta absoluta a la carpeta de iconos
            ruta_base = os.path.dirname(os.path.abspath(__file__))  # declaraciones_app/ui
            ruta_proyecto = os.path.dirname(ruta_base)  # declaraciones_app
            ruta_iconos = os.path.join(ruta_proyecto, "utils", "iconos")
            
            print(f"🔍 Buscando iconos en: {ruta_iconos}")
            
            # Verificar que la carpeta existe
            if not os.path.exists(ruta_iconos):
                print(f"⚠️ La carpeta de iconos no existe: {ruta_iconos}")
                raise FileNotFoundError(f"No existe la carpeta: {ruta_iconos}")
            
            # Cargar iconos para botones
            self.icono_guardar = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "guardar.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "guardar.png")),
                size=(24, 24)
            )
            
            self.icono_preview = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "preview.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "preview.png")),
                size=(24, 24)
            )
            
            self.icono_imprimir = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "imprimir.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "imprimir.png")),
                size=(24, 24)
            )
            
            self.icono_generar = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "generar.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "generar.png")),
                size=(24, 24)
            )
            
            self.icono_buscar = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "buscar.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "buscar.png")),
                size=(20, 20)
            )
            
            self.icono_limpiar = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "limpiar.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "limpiar.png")),
                size=(20, 20)
            )
            
            self.icono_plantilla = ctk.CTkImage(
                light_image=Image.open(os.path.join(ruta_iconos, "plantilla.png")),
                dark_image=Image.open(os.path.join(ruta_iconos, "plantilla.png")),
                size=(20, 20)
            )
            
            print("✅ Iconos cargados correctamente en crear_documento")
            
        except Exception as e:
            print(f"⚠️ Error al cargar iconos: {e}")
            import traceback
            traceback.print_exc()
            
            # Si falla, los iconos serán None
            self.icono_guardar = None
            self.icono_preview = None
            self.icono_imprimir = None
            self.icono_generar = None
            self.icono_buscar = None
            self.icono_limpiar = None
            self.icono_plantilla = None
    
    def capitalizar_texto(self, texto):
        """Convierte texto a formato título (Primera Letra Mayúscula)"""
        return ' '.join(word.capitalize() for word in texto.split())

    def _capitalizar_entry(self, entry_widget):
        """Capitaliza el contenido de un entry solo si cambió"""
        texto_actual = entry_widget.get().strip()
        if texto_actual:
            texto_capitalizado = self.capitalizar_texto(texto_actual)
            if texto_actual != texto_capitalizado:
                entry_widget.delete(0, "end")
                entry_widget.insert(0, texto_capitalizado)
            
    def formatear_dpi_automatico(self, event=None):
        """
        Formatea el DPI automáticamente mientras se escribe.
        Formato: 1234 12345 1234 (13 dígitos con espacios)
        """
        # Obtener texto actual
        texto = self.entry_dpi.get()
        
        # Guardar posición del cursor
        cursor_pos = self.entry_dpi.index(tk.INSERT)
        
        # Eliminar todo excepto dígitos
        solo_digitos = ''.join(filter(str.isdigit, texto))
        
        # Limitar a 13 dígitos
        solo_digitos = solo_digitos[:13]
        
        # Aplicar formato: 1234 12345 1234
        if len(solo_digitos) <= 4:
            texto_formateado = solo_digitos
        elif len(solo_digitos) <= 9:
            texto_formateado = f"{solo_digitos[:4]} {solo_digitos[4:]}"
        else:
            texto_formateado = f"{solo_digitos[:4]} {solo_digitos[4:9]} {solo_digitos[9:]}"
        
        # Actualizar entry solo si cambió
        if texto != texto_formateado:
            self.entry_dpi.delete(0, tk.END)
            self.entry_dpi.insert(0, texto_formateado)
            
            # Ajustar posición del cursor
            # Si se agregó un espacio, mover cursor una posición extra
            espacios_antes = texto[:cursor_pos].count(' ')
            espacios_despues = texto_formateado[:cursor_pos].count(' ')
            
            if espacios_despues > espacios_antes:
                cursor_pos += 1
            
            # Asegurar que el cursor no se salga del texto
            cursor_pos = min(cursor_pos, len(texto_formateado))
            self.entry_dpi.icursor(cursor_pos)

    def validar_dpi_completo(self):
        """
        Valida que el DPI tenga exactamente 13 dígitos.
        Retorna: (es_valido: bool, dpi_limpio: str, mensaje_error: str)
        """
        dpi = self.entry_dpi.get().strip()
        
        # Eliminar espacios
        dpi_limpio = dpi.replace(" ", "")
        
        # Validar longitud
        if len(dpi_limpio) != 13:
            return False, dpi_limpio, f"El DPI debe tener exactamente 13 dígitos.\nActualmente tiene: {len(dpi_limpio)} dígitos"
        
        # Validar que solo contenga números
        if not dpi_limpio.isdigit():
            return False, dpi_limpio, "El DPI solo debe contener números"
        
        return True, dpi_limpio, ""

    def formatear_fecha_auto(self, event):
        """Formatea la fecha automáticamente mientras se escribe"""
        widget = event.widget
        texto = widget.get().replace("/", "")  # Elimina barras existentes
        
        # Solo permite números
        if not texto.isdigit():
            texto = ''.join(filter(str.isdigit, texto))
        
        # Limita a 8 dígitos
        texto = texto[:8]
        
        # Formatea con barras
        if len(texto) >= 2:
            texto = texto[:2] + '/' + texto[2:]
        if len(texto) >= 5:
            texto = texto[:5] + '/' + texto[5:]
        
        # Actualizar entry
        widget.delete(0, "end")
        widget.insert(0, texto)
    
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
            tipo_palabra: 'nombre', 'apellido', 'nacionalidad', 'domicilio', 'nivel_academico'
            """
            self.parent = parent_ventana
            self.entry = entry
            self.tipo_palabra = tipo_palabra

            self.popup = None
            self.frame_scroll = None  # NUEVO
            self.botones_popup = []   # NUEVO
            self.idx_seleccionado = -1  # NUEVO
            self.sugerencias = []
            self.cerrando_popup = False

            # Enlazar eventos
            self.entry.bind("<KeyRelease>", self._on_key_release)
            self.entry.bind("<FocusOut>", self._on_focus_out)
            self.entry.bind("<Down>", self._on_down_key)
            self.entry.bind("<Up>", self._on_up_key)      # NUEVO
            self.entry.bind("<Return>", self._on_return_key)  # NUEVO
            self.entry.bind("<Escape>", lambda e: self._cerrar_popup())

        def _obtener_palabra_actual(self):
            """
            Obtiene la palabra que se está escribiendo actualmente.
            Para nombres: detecta la palabra donde está el cursor.
            Para otros campos: usa el texto completo.
            """
            try:
                texto_completo = self.entry.get().strip()
                
                if not texto_completo:
                    return ""
                
                # Para nombres, detectar palabra actual según posición del cursor
                if self.tipo_palabra == "nombre":
                    try:
                        cursor_pos = self.entry.index(tk.INSERT)
                        
                        # Asegurar que cursor_pos esté dentro del rango
                        if cursor_pos > len(texto_completo):
                            cursor_pos = len(texto_completo)
                        
                        # Encontrar inicio de la palabra actual
                        inicio = cursor_pos
                        while inicio > 0 and inicio <= len(texto_completo):
                            # Verificar que podemos acceder al índice
                            if inicio - 1 < 0:
                                break
                            if texto_completo[inicio - 1] in (' ', '\t', '\n'):
                                break
                            inicio -= 1
                        
                        # Encontrar fin de la palabra actual
                        fin = cursor_pos
                        while fin < len(texto_completo):
                            if texto_completo[fin] in (' ', '\t', '\n'):
                                break
                            fin += 1
                        
                        # Extraer palabra con validación de índices
                        if inicio >= 0 and fin <= len(texto_completo) and inicio <= fin:
                            palabra_actual = texto_completo[inicio:fin].strip()
                            return palabra_actual if len(palabra_actual) >= 2 else ""
                        else:
                            return ""
                            
                    except Exception as e:
                        print(f"⚠️ Error detectando palabra (usando fallback): {e}")
                        # Fallback: usar última palabra
                        palabras = texto_completo.split()
                        if palabras and len(palabras[-1]) >= 2:
                            return palabras[-1]
                        return ""
                else:
                    # Para otros campos, usar texto completo
                    return texto_completo if len(texto_completo) >= 2 else ""
                    
            except Exception as e:
                print(f"❌ Error crítico en _obtener_palabra_actual: {e}")
                return ""

        def _on_key_release(self, event):
            """Maneja la liberación de teclas para actualizar sugerencias"""
            # Ignorar teclas de navegación
            if event.keysym in ("Up", "Down", "Left", "Right", "Return", "Escape", "Tab", "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R"):
                return

            try:
                palabra_buscar = self._obtener_palabra_actual()
                
                if len(palabra_buscar) < 2:
                    self._cerrar_popup()
                    return

                # Obtener sugerencias desde la BD (case-insensitive)
                self.sugerencias = self.parent.db.obtener_sugerencias_palabra(
                    self.tipo_palabra, 
                    palabra_buscar
                )

                if not self.sugerencias:
                    self._cerrar_popup()
                    return

                self._mostrar_popup()
                
            except Exception as e:
                print(f"❌ Error en _on_key_release: {e}")
                self._cerrar_popup()

        def _mostrar_popup(self):
            """Muestra el popup con sugerencias"""
            try:
                # Cerrar popup anterior si existe
                self._cerrar_popup()
                
                # Verificar que hay sugerencias
                if not self.sugerencias:
                    return

                # Crear nueva ventana flotante
                self.popup = ctk.CTkToplevel(self.parent.ventana)
                self.popup.overrideredirect(True)
                self.popup.attributes("-topmost", True)

                # Posicionar debajo del Entry
                try:
                    self.popup.update_idletasks()
                    x = self.entry.winfo_rootx()
                    y = self.entry.winfo_rooty() + self.entry.winfo_height()
                    
                    ancho = max(self.entry.winfo_width(), 200)
                    
                    # CAMBIO: Calcular altura según cantidad de sugerencias
                    if len(self.sugerencias) == 1:
                        altura = 50  # Altura fija para una sola palabra
                    else:
                        altura = min(len(self.sugerencias) * 38 + 15, 250)  # Más espacio por botón
                    
                    self.popup.geometry(f"{ancho}x{altura}+{x}+{y}")
                except Exception as e:
                    print(f"⚠️ Error al posicionar popup: {e}")
                    self._cerrar_popup()
                    return

                # Frame con scroll
                self.frame_scroll = ctk.CTkScrollableFrame(
                    self.popup, 
                    width=ancho-20,
                    height=altura-10,
                    fg_color=("white", "gray20")
                )
                self.frame_scroll.pack(fill="both", expand=True, padx=5, pady=5)

                # Obtener palabra actual con manejo de errores
                try:
                    palabra_actual = self._obtener_palabra_actual().lower()
                except Exception:
                    palabra_actual = ""

                # Lista para almacenar los botones
                self.botones_popup = []

                for sugerencia in self.sugerencias:
                    # Resaltar coincidencia con color SUCCESS (verde)
                    if palabra_actual and palabra_actual in sugerencia.lower():
                        texto_mostrar = f"💡 {sugerencia}"
                        text_color = COLOR_SUCCESS
                    else:
                        texto_mostrar = f"   {sugerencia}"
                        text_color = ("gray20", "gray90")
                    
                    btn = ctk.CTkButton(
                        self.frame_scroll,
                        text=texto_mostrar,
                        anchor="w",
                        command=lambda s=sugerencia: self._usar_sugerencia(s),
                        height=35,  # CAMBIO: Aumentar altura de botón a 35
                        fg_color="transparent",
                        hover_color=("gray85", "gray30"),
                        text_color=text_color,
                        corner_radius=5,
                        font=("Segoe UI", 11)
                    )
                    btn.pack(fill="x", padx=2, pady=2)
                    
                    btn.bind("<Enter>", lambda e: self._cancelar_cierre())
                    btn.bind("<Leave>", lambda e: None)
                    
                    # Guardar referencia al botón
                    self.botones_popup.append(btn)
                
                # Índice del botón actualmente seleccionado
                self.idx_seleccionado = -1
                
            except Exception as e:
                print(f"❌ Error al mostrar popup: {e}")
                self._cerrar_popup()

        def _actualizar_seleccion(self):
            """Actualiza visualmente el botón seleccionado y hace scroll"""
            try:
                # Resetear todos los botones
                for btn in self.botones_popup:
                    btn.configure(
                        fg_color="transparent",
                        text_color=("gray20", "gray90")
                    )
                
                # Resaltar el botón seleccionado
                if 0 <= self.idx_seleccionado < len(self.botones_popup):
                    btn_seleccionado = self.botones_popup[self.idx_seleccionado]
                    btn_seleccionado.configure(
                        fg_color=COLOR_WARNING,
                        text_color="white"
                    )
                    
                    # CAMBIO: Hacer scroll DESPUÉS de actualizar el widget
                    self.popup.update_idletasks()
                    self.frame_scroll.update_idletasks()
                    btn_seleccionado.update_idletasks()
                    
                    # Pequeño delay para asegurar que el widget se actualizó
                    self.popup.after(10, lambda: self._scroll_to_button(btn_seleccionado))
                    
            except Exception as e:
                print(f"Error al actualizar selección: {e}")

        def _scroll_to_button(self, button):
            """Hace scroll en el frame para mostrar el botón seleccionado"""
            try:
                # Forzar actualización de widgets
                self.frame_scroll._parent_canvas.update_idletasks()
                button.update_idletasks()
                
                # El CTkScrollableFrame tiene un método interno _parent_canvas
                # que es el canvas real que podemos controlar
                if hasattr(self.frame_scroll, '_parent_canvas'):
                    canvas = self.frame_scroll._parent_canvas
                else:
                    # Buscar el canvas manualmente si no está disponible
                    canvas = None
                    for widget in self.frame_scroll.winfo_children():
                        if isinstance(widget, tk.Canvas):
                            canvas = widget
                            break
                
                if not canvas:
                    return
                
                # Obtener posición del botón relativa al frame scrollable
                button_y = button.winfo_y()
                button_height = button.winfo_height()
                
                # Altura visible del canvas
                canvas_height = canvas.winfo_height()
                
                # Obtener el scrollregion total
                scrollregion = canvas.cget('scrollregion')
                if not scrollregion:
                    return
                
                # Parsear scrollregion: "x1 y1 x2 y2"
                coords = scrollregion.split()
                if len(coords) < 4:
                    return
                
                total_height = float(coords[3])
                
                # Si todo cabe en la vista, no hacer scroll
                if total_height <= canvas_height:
                    return
                
                # Calcular centro del botón
                button_center = button_y + (button_height / 2)
                
                # Calcular posición de scroll para centrar el botón
                # Queremos que el centro del botón esté en el centro de la vista
                target_scroll = (button_center - (canvas_height / 2)) / total_height
                
                # Limitar entre 0 y 1
                target_scroll = max(0.0, min(1.0, target_scroll))
                
                # Aplicar scroll
                canvas.yview_moveto(target_scroll)
                
            except Exception as e:
                print(f"Error al hacer scroll: {e}")
                import traceback
                traceback.print_exc()

        def _on_down_key(self, event):
            """Navegar al popup con flecha abajo"""
            if self.popup and self.popup.winfo_exists() and self.botones_popup:
                try:
                    # Si no hay botón seleccionado, seleccionar el primero
                    if self.idx_seleccionado == -1:
                        self.idx_seleccionado = 0
                    else:
                        # Avanzar al siguiente botón
                        self.idx_seleccionado = (self.idx_seleccionado + 1) % len(self.botones_popup)
                    
                    self._actualizar_seleccion()
                    
                except Exception as e:
                    print(f"Error en navegación: {e}")
            return "break"

        def _on_up_key(self, event):
            """Navegar hacia arriba en el popup"""
            if self.popup and self.popup.winfo_exists() and self.botones_popup:
                try:
                    # Si no hay botón seleccionado, seleccionar el último
                    if self.idx_seleccionado == -1:
                        self.idx_seleccionado = len(self.botones_popup) - 1
                    else:
                        # Retroceder al botón anterior
                        self.idx_seleccionado = (self.idx_seleccionado - 1) % len(self.botones_popup)
                    
                    self._actualizar_seleccion()
                    
                except Exception as e:
                    print(f"Error en navegación: {e}")
            return "break"

        def _on_return_key(self, event):
            """Seleccionar sugerencia con Enter"""
            if self.popup and self.popup.winfo_exists() and self.botones_popup:
                if 0 <= self.idx_seleccionado < len(self.botones_popup):
                    # Usar la sugerencia correspondiente
                    sugerencia = self.sugerencias[self.idx_seleccionado]
                    self._usar_sugerencia(sugerencia)
                return "break"
        
        def _usar_sugerencia(self, texto):
            """Reemplaza la palabra actual con la sugerencia seleccionada"""
            try:
                if self.tipo_palabra == "nombre":
                    # Para nombres, reemplazar solo la palabra actual
                    try:
                        texto_completo = self.entry.get()
                        cursor_pos = self.entry.index(tk.INSERT)
                        
                        # Validar cursor_pos
                        if cursor_pos > len(texto_completo):
                            cursor_pos = len(texto_completo)
                        
                        # Encontrar inicio de la palabra actual
                        inicio = cursor_pos
                        while inicio > 0:
                            if inicio - 1 < 0 or texto_completo[inicio - 1] in (' ', '\t', '\n'):
                                break
                            inicio -= 1
                        
                        # Encontrar fin de la palabra actual
                        fin = cursor_pos
                        while fin < len(texto_completo):
                            if texto_completo[fin] in (' ', '\t', '\n'):
                                break
                            fin += 1
                        
                        # Validar índices antes de usar
                        if inicio < 0:
                            inicio = 0
                        if fin > len(texto_completo):
                            fin = len(texto_completo)
                        
                        # Construir nuevo texto
                        nuevo_texto = texto_completo[:inicio] + texto
                        
                        # Agregar texto después de la palabra solo si existe
                        if fin < len(texto_completo):
                            nuevo_texto += texto_completo[fin:]
                        
                        # Actualizar entry
                        self.entry.delete(0, "end")
                        self.entry.insert(0, nuevo_texto)
                        
                        # Posicionar cursor después de la palabra insertada
                        nueva_pos = inicio + len(texto)
                        
                        # Agregar espacio automáticamente si no hay texto después o si no es un espacio
                        if nueva_pos >= len(nuevo_texto) or nuevo_texto[nueva_pos:nueva_pos+1] != ' ':
                            self.entry.insert(nueva_pos, ' ')
                            self.entry.icursor(nueva_pos + 1)
                        else:
                            self.entry.icursor(nueva_pos)
                        
                    except Exception as e:
                        print(f"⚠️ Error al usar sugerencia en nombre (usando fallback): {e}")
                        # Fallback: reemplazar todo
                        self.entry.delete(0, "end")
                        self.entry.insert(0, texto + " ")
                        self.entry.icursor("end")
                else:
                    # Para otros campos, reemplazar todo el contenido
                    self.entry.delete(0, "end")
                    self.entry.insert(0, texto)
                    self.entry.icursor("end")
                
                self._cerrar_popup()
                self.entry.focus_set()
                
            except Exception as e:
                print(f"❌ Error crítico al usar sugerencia: {e}")
                self._cerrar_popup()
    
        def _cancelar_cierre(self):
            """Cancela el cierre programado del popup"""
            self.cerrando_popup = False

        def _on_focus_out(self, event):
            """Cerrar popup cuando el entry pierde foco (con retraso para permitir clic)"""
            self.cerrando_popup = True
            self.entry.after(200, self._verificar_y_cerrar)

        def _verificar_y_cerrar(self):
            """Verifica si debe cerrar el popup"""
            if self.cerrando_popup:
                self._cerrar_popup()

        def _cerrar_popup(self):
            if self.popup and self.popup.winfo_exists():
                try:
                    self.popup.destroy()
                except:  # noqa: E722
                    pass
            self.popup = None
            self.cerrando_popup = False
        
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
            text="Plantilla",
            image=self.icono_plantilla,
            compound="left",
            command=self.cargar_plantilla,
            width=140,
            height=26,
            fg_color="#1E88E5",
            hover_color="#1565C0"
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
            text="",
            image=self.icono_buscar,
            command=self.buscar_persona,
            width=40,
            height=26,
            fg_color="#1E88E5",
            hover_color="#1565C0"
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
            text="",
            image=self.icono_buscar,
            command=self.buscar_por_nombre,
            width=40,
            height=26,
            fg_color="#1E88E5",
            hover_color="#1565C0"
        )
        btn_buscar_nombre.grid(row=0, column=2, padx=(2, 3))

        btn_limpiar = ctk.CTkButton(
            self.frame_busqueda,
            text="Limpiar",
            image=self.icono_limpiar,
            compound="left",
            command=self.limpiar_campos,
            width=100,
            height=26,
            fg_color="#1E88E5",
            hover_color="#1565C0"
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
        self.entry_nombre.bind("<FocusOut>", lambda e: self._capitalizar_entry(self.entry_nombre))
        self.combo_sexo = crear_campo(frame_datos, "Sexo:", es_combo=True,
                                      valores_combo=["masculino", "femenino"])
        self.combo_sexo.set("masculino")

        self.entry_fecha_nac = crear_campo(
            frame_datos,
            "Fec. Nacimiento:",
            "DD/MM/AAAA",
            validar=vcmd_fecha
        )
        # REEMPLAZAR las líneas existentes de bind por estas:
        self.entry_fecha_nac.bind("<KeyRelease>", self.formatear_fecha_auto)
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
            valores_combo=["soltero", "soltera", "casado", "casada"]
        )
        self.combo_estado.set("soltero")

        self.entry_casada = crear_campo(frame_datos, "Apell. Casada:", "de López")
        self.entry_casada.bind("<FocusOut>", lambda e: self._capitalizar_entry(self.entry_casada))

        self.entry_nacionalidad = crear_campo(frame_datos, "Nacionalidad:", "guatemalteco")
        self.entry_nacionalidad.bind("<FocusOut>", lambda e: self._capitalizar_entry(self.entry_nacionalidad))

        self.entry_nivel = crear_campo(frame_datos, "Nivel Académico:", "Bachiller")
        self.entry_nivel.bind("<FocusOut>", lambda e: self._capitalizar_entry(self.entry_nivel))

        self.entry_domicilio = crear_campo(frame_datos, "Domicilio:", "Guatemala")
        self.entry_domicilio.bind("<FocusOut>", lambda e: self._capitalizar_entry(self.entry_domicilio))

        self.entry_dpi = crear_campo(
            frame_datos,
            "DPI:",
            "2008 22829 0101",
            validar=vcmd_dpi
        )
        # Configurar formato automático de DPI (solo números, máximo 13 dígitos)
        self.entry_dpi.bind('<KeyRelease>', self.formatear_dpi_automatico)

        # === AUTOCOMPLETADO desde BD de sugerencias ===
        # Usamos la clase interna AutoCompleter
        self.autocomplete_nombre = self.AutoCompleter(self, self.entry_nombre, "nombre")
        self.autocomplete_casada = self.AutoCompleter(self, self.entry_casada, "apellido")
        self.autocomplete_nacionalidad = self.AutoCompleter(self, self.entry_nacionalidad, "nacionalidad")
        self.autocomplete_domicilio = self.AutoCompleter(self, self.entry_domicilio, "domicilio")
        self.autocomplete_nivel = self.AutoCompleter(self, self.entry_nivel, "nivel_academico")
        
        # ----- Botones -----
        frame_botones = ctk.CTkFrame(panel_izquierdo)
        frame_botones.pack(pady=5, padx=8)

        frame_botones.grid_columnconfigure(0, weight=1, uniform="button")
        frame_botones.grid_columnconfigure(1, weight=1, uniform="button")
        frame_botones.grid_columnconfigure(2, weight=1, uniform="button")
        frame_botones.grid_columnconfigure(3, weight=1, uniform="button")

        btn_guardar = ctk.CTkButton(
            frame_botones,
            text="Guardar y Generar",
            image=self.icono_guardar,
            compound="left",
            command=self.guardar_persona,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#1E88E5",
            hover_color="#1565C0"
        )
        btn_guardar.grid(row=0, column=0, padx=3, sticky="ew")

        btn_preview = ctk.CTkButton(
            frame_botones,
            text="Preview",
            image=self.icono_preview,
            compound="left",
            command=self.generar_preview,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#1E88E5",
            hover_color="#1565C0"
        )
        btn_preview.grid(row=0, column=1, padx=3, sticky="ew")

        btn_imprimir = ctk.CTkButton(
            frame_botones,
            text="Imprimir",
            image=self.icono_imprimir,
            compound="left",
            command=self.imprimir_documento_temporal,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#1E88E5",
            hover_color="#1565C0"
        )
        btn_imprimir.grid(row=0, column=2, padx=3, sticky="ew")

        btn_generar = ctk.CTkButton(
            frame_botones,
            text="Generar en Otra Ubicación",
            image=self.icono_generar,
            compound="left",
            command=self.generar_documento_otra_ubicacion,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#1E88E5",
            hover_color="#1565C0"
        )
        btn_generar.grid(row=0, column=3, padx=3, sticky="ew")

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
            
            # Domicilio (solo mostrar nombre del departamento, sin "departamento de")
            self.entry_domicilio.delete(0, "end")
            if resultado[6]:
                domicilio_bd = resultado[6].strip()
                # Remover "departamento de" si existe
                if domicilio_bd.lower().startswith("departamento de "):
                    domicilio_bd = domicilio_bd[16:]  # Quitar "departamento de "
                self.entry_domicilio.insert(0, domicilio_bd)
            
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
        
        # Configurar ventana modal
        ventana.transient(self.ventana)
        ventana.grab_set()  # Bloquear interacción con ventana padre
        
        # IMPORTANTE: Actualizar geometría ANTES de calcular posición
        ventana.update_idletasks()
        
        # Dimensiones
        width = 600
        height = 500
        
        # Calcular posición centrada
        screen_width = ventana.winfo_screenwidth()
        screen_height = ventana.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        
        # Establecer geometría con posición centrada
        ventana.geometry(f"{width}x{height}+{x}+{y}")
        
        # Traer al frente
        ventana.lift()
        ventana.focus_force()
        
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
            domicilio_bd = resultado[6].strip()
            # Remover "departamento de" si existe
            if domicilio_bd.lower().startswith("departamento de "):
                domicilio_bd = domicilio_bd[16:]  # Quitar "departamento de "
            self.entry_domicilio.insert(0, domicilio_bd)
        
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
        Guarda la persona en BD, genera documento en DOCUMENTOS_DIR y abre carpeta.
        """
        # Validar campos obligatorios
        nombre = self.entry_nombre.get().strip()
        dpi = self.entry_dpi.get().strip()
        
        if not nombre:
            messagebox.showerror("Error", "El nombre es obligatorio")
            self.entry_nombre.focus()
            return
        
        # ✅ VALIDAR DPI CON 13 DÍGITOS
        es_valido, dpi_limpio, mensaje_error = self.validar_dpi_completo()
        if not es_valido:
            messagebox.showerror("DPI Inválido", mensaje_error)
            self.entry_dpi.focus()
            return
        
        # Verificar plantilla activa
        plantilla = self.db.obtener_plantilla_activa()
        if not plantilla:
            messagebox.showerror("Error", "No hay ninguna plantilla activa.\n\nPor favor, carga una plantilla primero.")
            return
        
        try:
            # Recopilar datos
            self.entry_edad.configure(state="normal")
            edad_str = self.entry_edad.get().strip()
            self.entry_edad.configure(state="readonly")
            
            datos_persona = {
                'nombre': self.capitalizar_texto(nombre),
                'sexo': self.combo_sexo.get(),
                'fecha_nacimiento': self.entry_fecha_nac.get().strip(),
                'edad': int(edad_str) if edad_str else None,
                'estado_civil': self.combo_estado.get(),
                'apellido_casada': self.capitalizar_texto(self.entry_casada.get().strip()),
                'nacionalidad': self.capitalizar_texto(self.entry_nacionalidad.get().strip()),
                'nivel_academico': self.capitalizar_texto(self.entry_nivel.get().strip()),
                'domicilio': self.capitalizar_texto(self.entry_domicilio.get().strip()),
                'dpi': dpi
            }
            
            # Guardar en base de datos
            persona_id, accion = self.db.guardar_persona(datos_persona)
            
            # Aprender sugerencias
            self.db.aprender_sugerencias_desde_persona(datos_persona)
            
            # Generar documento en DOCUMENTOS_DIR con formato completo
            nombre_limpio = self.capitalizar_texto(nombre).replace(" ", "_")
            nombre_archivo = f"{dpi_limpio}_acta_{nombre_limpio}.docx"
            ruta_destino = os.path.join(DOCUMENTOS_DIR, nombre_archivo)

            # Si existe un archivo anterior con el mismo DPI, eliminarlo
            archivos_existentes = [f for f in os.listdir(DOCUMENTOS_DIR) if f.startswith(f"{dpi_limpio}_acta_")]
            for archivo_viejo in archivos_existentes:
                try:
                    os.remove(os.path.join(DOCUMENTOS_DIR, archivo_viejo))
                except Exception as e:
                    print(f"No se pudo eliminar archivo anterior: {e}")
            
            # Generar documento con datos actuales
            doc = self.crear_documento_con_datos()
            doc.save(ruta_destino)
            
            # Registrar en BD
            self.db.guardar_documento(
                persona_id=persona_id,
                nombre_archivo=nombre_archivo,
                ruta_archivo=ruta_destino,
                tipo_documento="acta"
            )
            
            # Actualizar referencias internas
            self.persona_actual_id = persona_id
            self.ruta_documento_actual = ruta_destino
            
            # Mensaje de éxito
            messagebox.showinfo(
                "Éxito",
                f"Persona {accion} correctamente.\n\n"
                f"Documento generado:\n{nombre_archivo}"
            )
            
            # Abrir carpeta
            self.abrir_carpeta_documento(ruta_destino)
            
            # Limpiar formulario
            self.limpiar_campos()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar:\n{str(e)}")
            print(f"Error completo: {e}")

    def generar_documento_otra_ubicacion(self):
        """
        Guarda en BD, genera en DOCUMENTOS_DIR, genera en ubicación personalizada y abre carpeta personalizada.
        """
        # Validar campos obligatorios
        nombre = self.entry_nombre.get().strip()
        dpi = self.entry_dpi.get().strip()
        
        if not nombre:
            messagebox.showerror("Error", "El nombre es obligatorio")
            self.entry_nombre.focus()
            return
        
        # ✅ VALIDAR DPI CON 13 DÍGITOS
        es_valido, dpi_limpio, mensaje_error = self.validar_dpi_completo()
        if not es_valido:
            messagebox.showerror("DPI Inválido", mensaje_error)
            self.entry_dpi.focus()
            return
        
        # Verificar plantilla activa
        plantilla = self.db.obtener_plantilla_activa()
        if not plantilla:
            messagebox.showerror("Error", "No hay ninguna plantilla activa.\n\nPor favor, carga una plantilla primero.")
            return
        
        # Seleccionar carpeta de destino
        carpeta_destino = filedialog.askdirectory(
            title="Seleccionar carpeta para guardar el documento"
        )
        
        if not carpeta_destino:
            return  # Usuario canceló
        
        try:
            # Recopilar datos
            self.entry_edad.configure(state="normal")
            edad_str = self.entry_edad.get().strip()
            self.entry_edad.configure(state="readonly")
            
            datos_persona = {
                'nombre': self.capitalizar_texto(nombre),
                'sexo': self.combo_sexo.get(),
                'fecha_nacimiento': self.entry_fecha_nac.get().strip(),
                'edad': int(edad_str) if edad_str else None,
                'estado_civil': self.combo_estado.get(),
                'apellido_casada': self.capitalizar_texto(self.entry_casada.get().strip()),
                'nacionalidad': self.capitalizar_texto(self.entry_nacionalidad.get().strip()),
                'nivel_academico': self.capitalizar_texto(self.entry_nivel.get().strip()),
                'domicilio': self.capitalizar_texto(self.entry_domicilio.get().strip()),
                'dpi': dpi
            }
            
            # Guardar en base de datos
            persona_id, accion = self.db.guardar_persona(datos_persona)
            
            # Aprender sugerencias
            self.db.aprender_sugerencias_desde_persona(datos_persona)
            
            # Generar nombre de archivo con formato completo
            nombre_limpio = self.capitalizar_texto(nombre).replace(" ", "_")
            nombre_archivo = f"{dpi_limpio}_acta_{nombre_limpio}.docx"

            # Eliminar archivos anteriores con el mismo DPI
            archivos_existentes = [f for f in os.listdir(DOCUMENTOS_DIR) if f.startswith(f"{dpi_limpio}_acta_")]
            for archivo_viejo in archivos_existentes:
                try:
                    os.remove(os.path.join(DOCUMENTOS_DIR, archivo_viejo))
                except Exception as e:
                    print(f"No se pudo eliminar archivo anterior: {e}")
            
            # ===== 1) GENERAR EN DOCUMENTOS_DIR =====
            ruta_documentos_dir = os.path.join(DOCUMENTOS_DIR, nombre_archivo)
            doc_principal = self.crear_documento_con_datos()
            doc_principal.save(ruta_documentos_dir)
            
            # Registrar en BD
            self.db.guardar_documento(
                persona_id=persona_id,
                nombre_archivo=nombre_archivo,
                ruta_archivo=ruta_documentos_dir,
                tipo_documento="acta"
            )
            
            # ===== 2) GENERAR EN UBICACIÓN PERSONALIZADA =====
            ruta_personalizada = os.path.join(carpeta_destino, nombre_archivo)
            doc_personalizado = self.crear_documento_con_datos()
            doc_personalizado.save(ruta_personalizada)
            
            # Actualizar referencias internas
            self.persona_actual_id = persona_id
            self.ruta_documento_actual = ruta_documentos_dir
            
            # Mensaje de éxito
            messagebox.showinfo(
                "Éxito",
                f"Persona {accion} correctamente.\n\n"
                f"Documentos generados:\n"
                f"1. {DOCUMENTOS_DIR}\n"
                f"2. {carpeta_destino}\n\n"
                f"Archivo: {nombre_archivo}"
            )
            
            # Abrir carpeta personalizada
            self.abrir_carpeta_documento(ruta_personalizada)
            
            # Limpiar formulario
            self.limpiar_campos()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar documento:\n{str(e)}")
            print(f"Error completo: {e}")
    
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
    
    def imprimir_documento_temporal(self):
        """Abre el documento en el visor de PDF predeterminado para impresión manual"""
        if not self.documento_preview or not os.path.exists(self.documento_preview):
            messagebox.showwarning(
                "Sin documento",
                "Primero genere una vista previa del documento."
            )
            return
        
        try:
            # Convertir a PDF temporal para imprimir
            temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_pdf.close()
            
            # Convertir DOCX a PDF
            convert(self.documento_preview, temp_pdf.name)
            
            # Abrir con el visor predeterminado
            messagebox.showinfo(
                "Abrir documento",
                "📄 Se abrirá el visor de PDF para la impresión del documento."
            )
            
            # Abrir el PDF con el programa predeterminado
            os.startfile(temp_pdf.name)
            
            # Limpiar PDF temporal después de 30 segundos
            # (tiempo suficiente para que se abra el visor)
            self.ventana.after(30000, lambda: self._limpiar_pdf_temp(temp_pdf.name))
            
        except Exception as e:
            messagebox.showerror(
                "Error al abrir documento",
                f"No se pudo procesar el documento:\n{str(e)}"
            )


    def _limpiar_pdf_temp(self, pdf_path):
        """Limpia archivo PDF temporal después de imprimir"""
        try:
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)
        except Exception as e:
            # Ignorar errores de limpieza (archivo puede estar en uso)
            print(f"No se pudo eliminar archivo temporal: {e}")
            pass
    
    def abrir_carpeta_documento(self, ruta_archivo):
        """Abre la carpeta donde se guardó el documento y selecciona el archivo"""
        try:
            if platform.system() == "Windows":
                subprocess.run(['explorer', '/select,', os.path.abspath(ruta_archivo)])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(['open', '-R', ruta_archivo])
            else:  # Linux
                subprocess.run(['xdg-open', os.path.dirname(ruta_archivo)])
        except Exception as e:
            messagebox.showwarning("Advertencia", f"No se pudo abrir la carpeta:\n{str(e)}")
    
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
        nombre = self.capitalizar_texto(self.entry_nombre.get().strip())
        sexo = self.combo_sexo.get().strip()
        
        # Obtener edad
        self.entry_edad.configure(state="normal")
        edad = self.entry_edad.get().strip()
        self.entry_edad.configure(state="readonly")
        
        estado_civil = self.combo_estado.get().strip()
        apellido_casada = self.capitalizar_texto(self.entry_casada.get().strip())
        nacionalidad = self.capitalizar_texto(self.entry_nacionalidad.get().strip())
        nivel_academico = self.capitalizar_texto(self.entry_nivel.get().strip())
        domicilio = self.capitalizar_texto(self.entry_domicilio.get().strip())
        dpi = self.entry_dpi.get().strip()
        
        # Construir nombre completo con apellido de casada
        nombre_completo = nombre

        apellido_casada_limpio = apellido_casada.strip() if apellido_casada else ""

        # Solo aplicar apellido de casada si:
        # - hay valor
        # - sexo femenino
        # - estado civil corresponde
        if (
            apellido_casada_limpio
            and sexo.lower() == "femenino"
            and estado_civil.lower() in ["casada", "divorciada", "viuda"]
        ):
            # Caso especial: si el nombre YA contiene la frase de apellido de casada
            # (por ejemplo: "Juana Garcia de la Mata de Gonzalez"), no duplicamos.
            nombre_lower = nombre.lower()
            ap_lower = apellido_casada_limpio.lower()
            if ap_lower not in nombre_lower:
                # Regla general: apellido de casada va al final del nombre completo
                # Ej: "Juana Garcia Lopez Guevara" + "de Sosos"
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
            # Agregar "departamento de" si no lo tiene
            domicilio_completo = domicilio
            if not domicilio.lower().startswith("departamento de "):
                domicilio_completo = f"departamento de {domicilio}"
            reemplazos.append(("con domicilio en el departamento de Guatemala", f"con domicilio en el {domicilio_completo}"))
        
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
    
    @staticmethod
    def generar_documento_para_persona(db, datos_persona, ruta_destino):
        """
        Genera un documento Word para una persona específica usando la plantilla activa.
        USA LA MISMA LÓGICA QUE crear_documento_con_datos() para asegurar consistencia.
        
        Args:
            db: Instancia de DatabaseManager
            datos_persona: Diccionario con los datos de la persona
            ruta_destino: Ruta donde se guardará el documento (.docx)
        """
        from docx import Document
        from datetime import datetime
        import os
        
        # Obtener plantilla activa
        plantilla_activa = db.obtener_plantilla_activa()
        
        if not plantilla_activa:
            raise Exception("No hay plantilla activa configurada.")
        
        ruta_plantilla = plantilla_activa[2]
        
        if not os.path.exists(ruta_plantilla):
            raise Exception(f"La plantilla no existe en: {ruta_plantilla}")
        
        # Cargar plantilla ORIGINAL (no un documento modificado)
        try:
            doc = Document(ruta_plantilla)
        except Exception as e:
            raise Exception(f"Error al cargar la plantilla: {str(e)}")
        
        # ===== EXTRAER DATOS (con validación de None) =====
        nombre = (datos_persona.get('nombre') or '').strip()
        dpi = (datos_persona.get('dpi') or '').strip()
        edad = datos_persona.get('edad')
        estado_civil = (datos_persona.get('estado_civil') or 'soltero').strip()
        nacionalidad = (datos_persona.get('nacionalidad') or 'guatemalteco').strip()
        domicilio = (datos_persona.get('domicilio') or 'Guatemala').strip()
        nivel_academico = (datos_persona.get('nivel_academico') or '').strip()
        apellido_casada = (datos_persona.get('apellido_casada') or '').strip()
        sexo = (datos_persona.get('sexo') or 'masculino').strip()
        
        # Fecha/hora (usar valores custom o actuales)
        ahora = datetime.now()
        hora = datos_persona.get('hora', str(ahora.hour))
        minutos = datos_persona.get('minutos', f"{ahora.minute:02d}")
        dia = datos_persona.get('dia', str(ahora.day))
        
        meses_es = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        mes = datos_persona.get('mes', meses_es[ahora.month - 1])
        anio = datos_persona.get('anio', str(ahora.year))
        
        # ===== CONSTRUIR NOMBRE COMPLETO CON APELLIDO DE CASADA =====
        nombre_completo = nombre
        apellido_casada_limpio = apellido_casada.strip() if apellido_casada else ""
        
        if (apellido_casada_limpio 
            and sexo.lower() == "femenino" 
            and estado_civil.lower() in ["casada", "divorciada", "viuda"]):
            
            nombre_lower = nombre.lower()
            ap_lower = apellido_casada_limpio.lower()
            
            if ap_lower not in nombre_lower:
                nombre_completo = f"{nombre} {apellido_casada_limpio}"
        
        # ===== REEMPLAZOS DE GÉNERO =====
        # Crear instancia temporal de VentanaCrearDocumento para usar sus métodos
        # (necesitamos acceso a reemplazar_genero_documento y otros métodos)
        class TempVentana:
            @staticmethod
            def reemplazar_genero_documento(doc, buscar, reemplazar):
                """Reemplaza texto de género en el documento"""
                reemplazos_totales = 0
                
                for paragraph in doc.paragraphs:
                    while buscar in ''.join(run.text for run in paragraph.runs):
                        if TempVentana.reemplazar_preservando_formato(paragraph, buscar, reemplazar):
                            reemplazos_totales += 1
                        else:
                            break
                        if reemplazos_totales > 100:
                            return
                
                for table in doc.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            for paragraph in cell.paragraphs:
                                while buscar in ''.join(run.text for run in paragraph.runs):
                                    if TempVentana.reemplazar_preservando_formato(paragraph, buscar, reemplazar):
                                        reemplazos_totales += 1
                                    else:
                                        break
                                    if reemplazos_totales > 100:
                                        return
            
            @staticmethod
            def clonar_formato_run(run_origen, run_destino):
                """Clona formato de un run a otro"""
                try:
                    if run_origen.bold is not None:
                        run_destino.bold = run_origen.bold
                    if run_origen.italic is not None:
                        run_destino.italic = run_origen.italic
                    if run_origen.underline is not None:
                        run_destino.underline = run_origen.underline
                    
                    if run_origen.font.name:
                        run_destino.font.name = run_origen.font.name
                    if run_origen.font.size:
                        run_destino.font.size = run_origen.font.size
                    if run_origen.font.color.rgb:
                        run_destino.font.color.rgb = run_origen.font.color.rgb
                    
                    if run_origen.font.strike is not None:
                        run_destino.font.strike = run_origen.font.strike
                    if run_origen.font.all_caps is not None:
                        run_destino.font.all_caps = run_origen.font.all_caps
                    if run_origen.font.small_caps is not None:
                        run_destino.font.small_caps = run_origen.font.small_caps
                    if run_origen.font.highlight_color is not None:
                        run_destino.font.highlight_color = run_origen.font.highlight_color
                except Exception as e:
                    print("Error al clonar formato:", e)
            
            @staticmethod
            def reemplazar_preservando_formato(paragraph, buscar, reemplazar):
                """Reemplaza texto preservando formato"""
                texto_completo = ''.join(run.text for run in paragraph.runs)
                
                if buscar not in texto_completo:
                    return False
                
                pos_inicio = texto_completo.find(buscar)
                pos_fin = pos_inicio + len(buscar)
                
                mapa_runs = []
                pos_actual = 0
                
                for i, run in enumerate(paragraph.runs):
                    for char in run.text:
                        mapa_runs.append((char, i, run))
                        pos_actual += 1
                
                nuevos_runs = []
                pos = 0
                
                while pos < len(mapa_runs):
                    if pos == pos_inicio:
                        if pos_inicio < len(mapa_runs):
                            run_formato = mapa_runs[pos_inicio][2]
                            nuevos_runs.append((reemplazar, run_formato))
                        else:
                            run_formato = paragraph.runs[-1] if paragraph.runs else None
                            nuevos_runs.append((reemplazar, run_formato))
                        
                        pos = pos_fin
                    else:
                        char, run_idx, run_orig = mapa_runs[pos]
                        
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
                
                for i in range(len(paragraph.runs) - 1, -1, -1):
                    paragraph._element.remove(paragraph.runs[i]._element)
                
                for texto, run_formato in nuevos_runs:
                    if texto:
                        nuevo_run = paragraph.add_run(texto)
                        if run_formato:
                            TempVentana.clonar_formato_run(run_formato, nuevo_run)
                
                return True
            
            @staticmethod
            def reemplazar_texto_completo(paragraph, buscar, reemplazar):
                """Reemplaza TODAS las ocurrencias preservando formato"""
                texto_completo = ''.join(run.text for run in paragraph.runs)
                ocurrencias = texto_completo.count(buscar)
                
                if ocurrencias == 0:
                    return False
                
                reemplazos_hechos = 0
                while reemplazos_hechos < ocurrencias:
                    if not TempVentana.reemplazar_preservando_formato(paragraph, buscar, reemplazar):
                        break
                    reemplazos_hechos += 1
                
                return reemplazos_hechos > 0
        
        # ===== APLICAR REEMPLAZOS DE GÉNERO =====
        if sexo == "femenino":
            TempVentana.reemplazar_genero_documento(doc, "al requirente", "a la requirente")
            TempVentana.reemplazar_genero_documento(doc, "el requirente", "la requirente")
            TempVentana.reemplazar_genero_documento(doc, "El requirente", "La requirente")
            TempVentana.reemplazar_genero_documento(doc, "el señor", "la señora")
            TempVentana.reemplazar_genero_documento(doc, "El señor", "La señora")
            TempVentana.reemplazar_genero_documento(doc, " advertido ", " advertida ")
            TempVentana.reemplazar_genero_documento(doc, " enterado ", " enterada ")
            TempVentana.reemplazar_genero_documento(doc, " deudor ", " deudora ")
            TempVentana.reemplazar_genero_documento(doc, " moroso ", " morosa ")
            TempVentana.reemplazar_genero_documento(doc, " incluido ", " incluida ")
        else:
            TempVentana.reemplazar_genero_documento(doc, "a la requirente", "al requirente")
            TempVentana.reemplazar_genero_documento(doc, "la requirente", "el requirente")
            TempVentana.reemplazar_genero_documento(doc, "La requirente", "El requirente")
            TempVentana.reemplazar_genero_documento(doc, "la señora", "el señor")
            TempVentana.reemplazar_genero_documento(doc, "La señora", "El señor")
            TempVentana.reemplazar_genero_documento(doc, " advertida ", " advertido ")
            TempVentana.reemplazar_genero_documento(doc, " enterada ", " enterado ")
            TempVentana.reemplazar_genero_documento(doc, " deudora ", " deudor ")
            TempVentana.reemplazar_genero_documento(doc, " morosa ", " moroso ")
            TempVentana.reemplazar_genero_documento(doc, " incluida ", " incluido ")
        
        # ===== PREPARAR REEMPLAZOS DE DATOS =====
        from utils import NumeroATexto  # Importar la clase para convertir números
        
        reemplazos = []
        
        # Hora y minutos
        if hora and minutos:
            hora_num = int(hora)
            min_num = int(minutos)
            
            hora_t = NumeroATexto.convertir(hora_num)
            min_t = NumeroATexto.convertir(min_num)
            
            # Normalizar "uno" -> "un"
            if hora_t.endswith(" y uno"):
                hora_t = hora_t[:-3] + " un"
            elif hora_t == "uno":
                hora_t = "un"
            
            if min_t.endswith(" y uno"):
                min_t = min_t[:-3] + " un"
            elif min_t == "uno":
                min_t = "un"
            
            reemplazos.append((
                "diecisiete horas con veinte minutos",
                f"{hora_t} horas con {min_t} minutos"
            ))
        
        # Día
        if dia:
            dia_num = int(dia)
            dia_t = NumeroATexto.convertir(dia_num)
            
            if dia_t.endswith(" y uno"):
                dia_t = dia_t[:-3] + " un"
            elif dia_t == "uno":
                dia_t = "un"
            
            reemplazos.append(("veintiocho", dia_t))
            reemplazos.append(("(28)", f"({dia})"))
        
        # Mes
        if mes:
            reemplazos.append(("noviembre", mes))
        
        # Año
        if anio:
            anio_num = int(anio)
            if 2000 <= anio_num < 2100:
                resto = anio_num - 2000
                if resto == 0:
                    anio_texto = "dos mil"
                else:
                    anio_texto = "dos mil " + NumeroATexto.convertir(resto)
            else:
                anio_texto = str(anio)
            
            reemplazos.append(("dos mil veinticinco", anio_texto))
            reemplazos.append(("(2025)", f"({anio})"))
        
        # Nombre
        if nombre_completo:
            reemplazos.append(("Abner Aníbal Ajpop González", nombre_completo))
        
        # Edad
        if edad:
            edad_num = int(edad)
            edad_t = NumeroATexto.convertir(edad_num)
            
            if edad_t.endswith(" y uno"):
                edad_t = edad_t[:-3] + " un"
            elif edad_t == "uno":
                edad_t = "un"
            
            reemplazos.append(("veintiún", edad_t))
            reemplazos.append(("(21)", f"({edad})"))
        
        # Estado civil
        if estado_civil:
            reemplazos.append(("soltero", estado_civil))
        
        # Nacionalidad
        if nacionalidad:
            reemplazos.append(("guatemalteco", nacionalidad))
        
        # Nivel académico
        if nivel_academico:
            reemplazos.append(("Bachiller en Ciencias y Letras con Orientación en Computación", nivel_academico))
        
        # Domicilio
        if domicilio:
            domicilio_completo = domicilio
            if not domicilio.lower().startswith("departamento de "):
                domicilio_completo = f"departamento de {domicilio}"
            reemplazos.append(("con domicilio en el departamento de Guatemala", f"con domicilio en el {domicilio_completo}"))
        
        # DPI
        if dpi:
            dpi_formateado = dpi.replace(" ", "")
            if len(dpi_formateado) == 13:
                dpi_con_espacios = f"{dpi_formateado[:4]} {dpi_formateado[4:9]} {dpi_formateado[9:13]}"
            else:
                dpi_con_espacios = dpi
            
            dpi_texto = NumeroATexto.convertir_dpi(dpi)
            reemplazos.append((
                "dos mil ocho espacio veintidós mil ochocientos veintinueve espacio cero ciento uno",
                dpi_texto
            ))
            reemplazos.append(("(2008 22829 0101)", f"({dpi_con_espacios})"))
        
        # ===== APLICAR REEMPLAZOS =====
        for paragraph in doc.paragraphs:
            for buscar, reemplazar in reemplazos:
                TempVentana.reemplazar_texto_completo(paragraph, buscar, reemplazar)
        
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        for buscar, reemplazar in reemplazos:
                            TempVentana.reemplazar_texto_completo(paragraph, buscar, reemplazar)
        
        # ===== GUARDAR DOCUMENTO =====
        try:
            doc.save(ruta_destino)
        except Exception as e:
            raise Exception(f"Error al guardar el documento: {str(e)}")