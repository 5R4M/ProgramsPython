import os
import tempfile

def convertir_doc_a_docx(archivo_doc):
    """Convierte un archivo .doc a .docx usando win32com"""
    try:
        import win32com.client
        import pythoncom
        
        # Inicializar COM
        pythoncom.CoInitialize()
        
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        
        # Abrir documento .doc
        doc = word.Documents.Open(os.path.abspath(archivo_doc))
        
        # Crear nombre para archivo .docx temporal
        archivo_docx = tempfile.NamedTemporaryFile(delete=False, suffix=".docx").name
        
        # Guardar como .docx (formato 16)
        doc.SaveAs2(archivo_docx, FileFormat=16)
        doc.Close()
        word.Quit()
        
        # Limpiar COM
        pythoncom.CoUninitialize()
        
        return archivo_docx
        
    except ImportError:
        print("Error: pywin32 no está instalado")
        return None
    except Exception as e:
        print(f"Error al convertir .doc: {str(e)}")
        return None