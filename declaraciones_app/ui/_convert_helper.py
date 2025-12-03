"""
Script auxiliar para conversión DOCX a PDF
Coloca este archivo en la misma carpeta que cargar_documentos.py
"""
import sys

def convert_safe(docx_path, pdf_path):
    """Conversión segura con manejo de streams"""
    try:
        # Redirigir completamente los streams
        import io
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        sys.stdin = io.StringIO()
        
        # Importar y convertir
        from docx2pdf import convert
        convert(docx_path, pdf_path)
        
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.__stderr__)
        return 1

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: _convert_helper.py <docx_path> <pdf_path>", file=sys.__stderr__)
        sys.exit(1)
    
    docx_path = sys.argv[1]
    pdf_path = sys.argv[2]
    
    sys.exit(convert_safe(docx_path, pdf_path))