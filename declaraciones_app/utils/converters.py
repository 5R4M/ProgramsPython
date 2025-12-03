def convertir_doc_a_docx(doc_path):
    """
    Convierte un archivo .doc a .docx usando win32com con manejo ultra-robusto.
    
    Args:
        doc_path: Ruta al archivo .doc
        
    Returns:
        str: Ruta al archivo .docx convertido, o None si falla
    """
    import os
    import sys
    import io
    import tempfile
    import time
    
    # Proteger streams
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    old_stdin = sys.stdin
    
    dummy_buffer = io.StringIO()
    
    try:
        # Redirigir streams
        sys.stdout = dummy_buffer
        sys.stderr = dummy_buffer
        sys.stdin = dummy_buffer
        
        import win32com.client
        import pythoncom
        
        # Verificar que el archivo existe
        if not os.path.exists(doc_path):
            return None
        
        # Crear ruta temporal para el .docx
        temp_dir = tempfile.gettempdir()
        nombre_base = os.path.splitext(os.path.basename(doc_path))[0]
        
        # Limpiar nombre de caracteres problemáticos
        nombre_base = "".join(c for c in nombre_base if c.isalnum() or c in (' ', '-', '_'))
        nombre_base = nombre_base[:50]  # Limitar longitud
        
        docx_path = os.path.join(temp_dir, f"{nombre_base}_temp_{int(time.time())}.docx")
        
        # Si ya existe, eliminarlo
        if os.path.exists(docx_path):
            try:
                os.remove(docx_path)
                time.sleep(0.1)
            except:  # noqa: E722
                pass
        
        # Inicializar COM en este thread
        pythoncom.CoInitialize()
        
        word = None
        doc = None
        
        try:
            # Crear instancia de Word (DispatchEx para nueva instancia)
            try:
                word = win32com.client.DispatchEx("Word.Application")
            except:  # noqa: E722
                # Si falla, intentar con Dispatch normal
                word = win32com.client.Dispatch("Word.Application")
            
            word.Visible = False
            word.DisplayAlerts = 0  # wdAlertsNone = 0
            
            # Configurar para evitar diálogos
            try:
                word.Options.SavePropertiesPrompt = False
                word.Options.ConfirmConversions = False
                word.DisplayRecentFiles = False
            except:  # noqa: E722
                pass
            
            # Abrir documento .doc con parámetros seguros
            doc_abs_path = os.path.abspath(doc_path)
            
            try:
                # Parámetros: FileName, ConfirmConversions, ReadOnly, AddToRecentFiles
                doc = word.Documents.Open(
                    doc_abs_path,
                    False,  # ConfirmConversions
                    True,   # ReadOnly
                    False   # AddToRecentFiles
                )
            except Exception as open_err:
                raise Exception(f"No se pudo abrir el documento: {open_err}")
            
            # Dar tiempo a que Word abra el documento
            time.sleep(0.2)
            
            # Guardar como .docx
            docx_abs_path = os.path.abspath(docx_path)
            
            # Intentar diferentes métodos de guardado
            guardado_exitoso = False
            
            # Método 1: SaveAs2 con FileFormat
            try:
                doc.SaveAs2(
                    FileName=docx_abs_path,
                    FileFormat=16  # wdFormatXMLDocument = 16 (DOCX)
                )
                guardado_exitoso = True
            except AttributeError:
                # SaveAs2 no existe en versiones antiguas
                pass
            except Exception:
                pass
            
            # Método 2: SaveAs con FileFormat
            if not guardado_exitoso:
                try:
                    doc.SaveAs(
                        FileName=docx_abs_path,
                        FileFormat=16
                    )
                    guardado_exitoso = True
                except Exception:
                    pass
            
            # Método 3: SaveAs sin parámetros adicionales
            if not guardado_exitoso:
                try:
                    doc.SaveAs(docx_abs_path)
                    guardado_exitoso = True
                except Exception:
                    pass
            
            if not guardado_exitoso:
                raise Exception("No se pudo guardar el documento en ningún formato")
            
            # Dar tiempo a que Word guarde
            time.sleep(0.3)
            
        finally:
            # Cerrar documento sin guardar cambios
            try:
                if doc is not None:
                    doc.Close(SaveChanges=False)
                    time.sleep(0.1)
            except:  # noqa: E722
                pass
            
            # Cerrar Word
            try:
                if word is not None:
                    word.Quit()
                    time.sleep(0.1)
            except:  # noqa: E722
                pass
            
            # Limpiar referencias COM
            doc = None
            word = None
            
            # Desinicalizar COM
            try:
                pythoncom.CoUninitialize()
            except:  # noqa: E722
                pass
        
        # Verificar que se creó el archivo
        time.sleep(0.2)
        
        if os.path.exists(docx_path) and os.path.getsize(docx_path) > 0:
            return docx_path
        else:
            return None
    
    except Exception:
        return None
        
    finally:
        # Restaurar streams SIEMPRE
        try:
            sys.stdout = old_stdout if old_stdout is not None else sys.__stdout__
            sys.stderr = old_stderr if old_stderr is not None else sys.__stderr__
            sys.stdin = old_stdin if old_stdin is not None else sys.__stdin__
        except:  # noqa: E722
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            sys.stdin = sys.__stdin__