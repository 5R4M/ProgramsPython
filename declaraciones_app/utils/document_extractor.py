import re
from docx import Document

class DocumentExtractor:
    """Clase para extraer datos de documentos Word"""
    
    @staticmethod
    def extraer_datos(archivo_docx):
        """Extrae datos de un documento Word"""
        try:
            doc = Document(archivo_docx)
            
            # Extraer todo el texto del documento
            texto_completo = []
            for paragraph in doc.paragraphs:
                texto_completo.append(paragraph.text)
            
            # También extraer texto de tablas
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            texto_completo.append(paragraph.text)
            
            texto = "\n".join(texto_completo)
            
            # Extraer datos usando expresiones regulares
            datos = {}
            
            # Extraer DPI
            dpi_match = re.search(r'\b(\d{4})\s*(\d{5})\s*(\d{4})\b', texto)
            if dpi_match:
                datos['dpi'] = f"{dpi_match.group(1)} {dpi_match.group(2)} {dpi_match.group(3)}"
            else:
                dpi_match = re.search(r'\b(\d{13})\b', texto)
                if dpi_match:
                    dpi_str = dpi_match.group(1)
                    datos['dpi'] = f"{dpi_str[:4]} {dpi_str[4:9]} {dpi_str[9:13]}"
            
            # Extraer edad
            edad_match = re.search(r'\b(\d{1,3})\s*años?\b', texto, re.IGNORECASE)
            if edad_match:
                datos['edad'] = int(edad_match.group(1))
            else:
                edad_match = re.search(r'\((\d{1,3})\)', texto)
                if edad_match:
                    datos['edad'] = int(edad_match.group(1))
            
            # Extraer estado civil
            estados_civiles = ['soltero', 'soltera', 'casado', 'casada', 
                             'divorciado', 'divorciada', 'viudo', 'viuda']
            for estado in estados_civiles:
                if re.search(r'\b' + estado + r'\b', texto, re.IGNORECASE):
                    datos['estado_civil'] = estado.lower()
                    break
            
            # Extraer nacionalidad
            nacionalidades = ['guatemalteco', 'guatemalteca', 'salvadoreño', 'salvadoreña', 
                            'hondureño', 'hondureña', 'nicaragüense', 'costarricense', 
                            'panameño', 'panameña', 'mexicano', 'mexicana']
            for nac in nacionalidades:
                if re.search(r'\b' + nac + r'\b', texto, re.IGNORECASE):
                    datos['nacionalidad'] = nac.lower()
                    break
            
            # Extraer domicilio
            domicilio_match = re.search(r'(?:con\s+)?domicilio\s+(?:en\s+)?(?:el\s+)?(.+?)(?:\.|,|\n)', 
                                       texto, re.IGNORECASE)
            if domicilio_match:
                datos['domicilio'] = domicilio_match.group(1).strip()
            
            # Extraer nivel académico
            nivel_match = re.search(r'(Bachiller[^.,\n]+|Licenciado[^.,\n]+|Ingeniero[^.,\n]+|Doctor[^.,\n]+|Maestro[^.,\n]+|Perito[^.,\n]+)', 
                                   texto, re.IGNORECASE)
            if nivel_match:
                datos['nivel_academico'] = nivel_match.group(1).strip()
            
            # Extraer nombre completo
            nombre_match = re.search(r'(?:comparece|compareció)\s+(?:el\s+señor|la\s+señora|el|la)?\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+)', 
                                    texto, re.IGNORECASE)
            if nombre_match:
                datos['nombre'] = nombre_match.group(1).strip()
            else:
                nombre_match = re.search(r'\b([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?)\b', 
                                        texto)
                if nombre_match:
                    nombre_candidato = nombre_match.group(1).strip()
                    if not any(palabra in nombre_candidato.lower() for palabra in 
                             ['departamento', 'municipio', 'zona', 'avenida', 'calle', 
                              'bachiller', 'licenciado']):
                        datos['nombre'] = nombre_candidato
            
            # Extraer apellido de casada
            casada_match = re.search(r'(?:de\s+casada\s+)?([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+de\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)', 
                                    texto)
            if casada_match:
                datos['apellido_casada'] = casada_match.group(1).strip()
            
            return datos if datos else None
            
        except Exception as e:
            print(f"Error al extraer datos: {str(e)}")
            return None