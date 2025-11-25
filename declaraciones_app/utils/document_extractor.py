# utils/document_extractor.py

import re
from docx import Document
from config import NOMBRES_NOTARIOS

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
            
            # ===== EXTRAER DPI =====
            dpi_match = re.search(r'\b(\d{4})\s*(\d{5})\s*(\d{4})\b', texto)
            if dpi_match:
                datos['dpi'] = f"{dpi_match.group(1)} {dpi_match.group(2)} {dpi_match.group(3)}"
            else:
                dpi_match = re.search(r'\b(\d{13})\b', texto)
                if dpi_match:
                    dpi_str = dpi_match.group(1)
                    datos['dpi'] = f"{dpi_str[:4]} {dpi_str[4:9]} {dpi_str[9:13]}"
            
            # ===== EXTRAER NOMBRE COMPLETO (MEJORADO) =====
            nombre_encontrado = DocumentExtractor._extraer_nombre_persona(texto, datos.get('dpi'))
            
            if nombre_encontrado:
                datos['nombre'] = nombre_encontrado
                print(f"✅ Nombre extraído: {datos['nombre']}")
            else:
                print("⚠️ No se pudo extraer el nombre")
            
            # ===== EXTRAER EDAD =====
            edad_encontrada = DocumentExtractor._extraer_edad(texto, datos.get('nombre'))
            if edad_encontrada:
                datos['edad'] = edad_encontrada
            
            # ===== EXTRAER ESTADO CIVIL =====
            estados_civiles = ['soltero', 'soltera', 'casado', 'casada', 
                             'divorciado', 'divorciada', 'viudo', 'viuda']
            for estado in estados_civiles:
                if re.search(r'\b' + estado + r'\b', texto, re.IGNORECASE):
                    datos['estado_civil'] = estado.lower()
                    break
            
            # ===== EXTRAER NACIONALIDAD =====
            nacionalidades = ['guatemalteco', 'guatemalteca', 'salvadoreño', 'salvadoreña', 
                            'hondureño', 'hondureña', 'nicaragüense', 'costarricense', 
                            'panameño', 'panameña', 'mexicano', 'mexicana']
            for nac in nacionalidades:
                if re.search(r'\b' + nac + r'\b', texto, re.IGNORECASE):
                    datos['nacionalidad'] = nac.lower()
                    break
            
            # ===== EXTRAER DOMICILIO =====
            domicilio_match = re.search(r'(?:con\s+)?domicilio\s+(?:en\s+)?(?:el\s+)?(.+?)(?:\.|,|\n)', 
                                       texto, re.IGNORECASE)
            if domicilio_match:
                datos['domicilio'] = domicilio_match.group(1).strip()
            
            # ===== EXTRAER NIVEL ACADÉMICO =====
            nivel_match = re.search(r'(Bachiller[^.,\n]+|Licenciado[^.,\n]+|Ingeniero[^.,\n]+|Doctor[^.,\n]+|Maestro[^.,\n]+|Perito[^.,\n]+)', 
                                   texto, re.IGNORECASE)
            if nivel_match:
                datos['nivel_academico'] = nivel_match.group(1).strip()
            
            # ===== EXTRAER APELLIDO DE CASADA =====
            casada_match = re.search(r'(?:de\s+casada\s+)?([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+de\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)', 
                                    texto)
            if casada_match:
                datos['apellido_casada'] = casada_match.group(1).strip()
            
            # Debug: Mostrar datos extraídos
            print("\n📋 Datos extraídos del documento:")
            print(f"   Nombre: {datos.get('nombre', 'No encontrado')}")
            print(f"   DPI: {datos.get('dpi', 'No encontrado')}")
            print(f"   Edad: {datos.get('edad', 'No encontrado')}")
            print(f"   Estado Civil: {datos.get('estado_civil', 'No encontrado')}")
            print(f"   Nacionalidad: {datos.get('nacionalidad', 'No encontrado')}")
            
            return datos if datos else None
            
        except Exception as e:
            print(f"❌ Error al extraer datos: {str(e)}")
            return None
    
    @staticmethod
    def _extraer_nombre_persona(texto, dpi=None):
        """Extrae el nombre de la persona que comparece (NO del notario)"""
        
        # Lista de palabras que NO deben estar en un nombre válido
        palabras_excluir = [
            'departamento', 'municipio', 'zona', 'avenida', 'calle',
            'república', 'guatemala', 'centroamérica', 'notarial', 'notario',
            'ante', 'comparece', 'identificado', 'identificada'
        ]
        
        # Normalizar nombres de notarios para comparación
        nombres_notarios_lower = [n.lower() for n in NOMBRES_NOTARIOS]
        
        def es_nombre_valido(nombre):
            """Verifica si un nombre es válido (no es notario ni palabra común)"""
            if not nombre or len(nombre.strip()) < 5:
                return False
            
            nombre_lower = nombre.lower().strip()
            
            # Verificar que no sea un notario
            for notario in nombres_notarios_lower:
                if notario in nombre_lower or nombre_lower in notario:
                    return False
            
            # Verificar que no contenga palabras a excluir
            for palabra in palabras_excluir:
                if palabra in nombre_lower:
                    return False
            
            # Verificar que tenga al menos 2 palabras (nombre y apellido)
            palabras = nombre.strip().split()
            if len(palabras) < 2:
                return False
            
            return True
        
        # ESTRATEGIA 1: Buscar nombre asociado al DPI
        if dpi:
            dpi.replace(' ', '')
            # Buscar: "NOMBRE, identificado con DPI"
            patron_dpi = r'([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){2,5}),?\s+identificad[oa]\s+con\s+(?:DPI|CUI|Documento)'
            match_dpi = re.search(patron_dpi, texto, re.IGNORECASE)
            if match_dpi:
                nombre = match_dpi.group(1).strip()
                if es_nombre_valido(nombre):
                    print(f"   ✓ Nombre encontrado (patrón DPI): {nombre}")
                    return nombre.title()
        
        # ESTRATEGIA 2: Buscar después de "compareció" o "comparece"
        # Buscar el texto DESPUÉS de mencionar al notario
        patrones_comparece = [
            # "compareció: NOMBRE, de X años"
            r'comparec(?:ió|e)[:\s]+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){2,5}),?\s+de\s+\d+\s+años',
            
            # "compareció el señor/la señora NOMBRE"
            r'comparec(?:ió|e)\s+(?:el\s+señor|la\s+señora|el|la)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){2,5})',
            
            # "ante mí ... compareció NOMBRE"
            r'ante\s+m[íi].*?comparec(?:ió|e)[:\s]+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){2,5})',
        ]
        
        for patron in patrones_comparece:
            matches = re.finditer(patron, texto, re.IGNORECASE | re.DOTALL)
            for match in matches:
                nombre = match.group(1).strip()
                if es_nombre_valido(nombre):
                    print(f"   ✓ Nombre encontrado (patrón comparece): {nombre}")
                    return nombre.title()
        
        # ESTRATEGIA 3: Buscar "Yo, NOMBRE, de X años"
        patron_yo = r'Yo,?\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){2,5}),?\s+de\s+\d+\s+años'
        match_yo = re.search(patron_yo, texto, re.IGNORECASE)
        if match_yo:
            nombre = match_yo.group(1).strip()
            if es_nombre_valido(nombre):
                print(f"   ✓ Nombre encontrado (patrón Yo): {nombre}")
                return nombre.title()
        
        # ESTRATEGIA 4: Buscar todos los nombres y filtrar
        # Buscar todos los nombres completos (3-5 palabras capitalizadas)
        patron_nombres = r'\b([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){2,4})\b'
        todos_nombres = re.findall(patron_nombres, texto)
        
        # Filtrar nombres válidos
        nombres_validos = []
        for nombre in todos_nombres:
            if es_nombre_valido(nombre):
                if nombre not in nombres_validos:
                    nombres_validos.append(nombre)
        
        # Tomar el primer nombre válido (después de filtrar notarios)
        if nombres_validos:
            print(f"   ✓ Nombre encontrado (búsqueda general): {nombres_validos[0]}")
            return nombres_validos[0].title()
        
        return None
    
    @staticmethod
    def _extraer_edad(texto, nombre_persona=None):
        """Extrae la edad de la persona (en número o en letras)"""
        
        # ESTRATEGIA 1: Buscar edad en formato "(número)" después del nombre
        if nombre_persona:
            # Buscar "NOMBRE ... (XX)" donde XX es la edad
            patron_parentesis = re.escape(nombre_persona) + r'.*?\((\d{1,3})\)'
            match_parentesis = re.search(patron_parentesis, texto, re.IGNORECASE | re.DOTALL)
            if match_parentesis:
                edad = int(match_parentesis.group(1))
                if 18 <= edad <= 120:
                    print(f"   ✓ Edad encontrada (paréntesis): {edad}")
                    return edad
            
            # Buscar "NOMBRE, de X años"
            patron_edad_nombre = re.escape(nombre_persona) + r'.*?de\s+(\d{1,3})\s+años'
            match_edad = re.search(patron_edad_nombre, texto, re.IGNORECASE | re.DOTALL)
            if match_edad:
                edad = int(match_edad.group(1))
                if 18 <= edad <= 120:
                    print(f"   ✓ Edad encontrada (cerca del nombre): {edad}")
                    return edad
        
        # ESTRATEGIA 2: Buscar edad después de "compareció" en formato "(número)"
        patron_comparece_parentesis = r'comparec(?:ió|e).*?\((\d{1,3})\)'
        match_comparece = re.search(patron_comparece_parentesis, texto, re.IGNORECASE | re.DOTALL)
        if match_comparece:
            edad = int(match_comparece.group(1))
            if 18 <= edad <= 120:
                print(f"   ✓ Edad encontrada (compareció + paréntesis): {edad}")
                return edad
        
        # ESTRATEGIA 3: Buscar edad después de "compareció" en formato "de X años"
        patron_edad_comparece = r'comparec(?:ió|e).*?de\s+(\d{1,3})\s+años'
        match_edad = re.search(patron_edad_comparece, texto, re.IGNORECASE | re.DOTALL)
        if match_edad:
            edad = int(match_edad.group(1))
            if 18 <= edad <= 120:
                print(f"   ✓ Edad encontrada (compareció): {edad}")
                return edad
        
        # ESTRATEGIA 4: Buscar edad en formato "X años de edad"
        patron_edad_general = r'de\s+(\d{1,3})\s+años\s+de\s+edad'
        match_edad = re.search(patron_edad_general, texto, re.IGNORECASE)
        if match_edad:
            edad = int(match_edad.group(1))
            if 18 <= edad <= 120:
                print(f"   ✓ Edad encontrada (general): {edad}")
                return edad
        
        # ESTRATEGIA 5: Buscar cualquier número entre paréntesis que sea una edad válida
        # (esto es más general y puede capturar la edad si está en paréntesis en cualquier parte)
        patron_parentesis_general = r'\((\d{1,3})\)\s*años'
        match_parentesis = re.search(patron_parentesis_general, texto, re.IGNORECASE)
        if match_parentesis:
            edad = int(match_parentesis.group(1))
            if 18 <= edad <= 120:
                print(f"   ✓ Edad encontrada (paréntesis general): {edad}")
                return edad
        
        # ESTRATEGIA 6: Buscar solo número entre paréntesis cerca de "años"
        patron_solo_parentesis = r'\((\d{1,3})\)'
        matches_parentesis = re.finditer(patron_solo_parentesis, texto)
        for match in matches_parentesis:
            edad = int(match.group(1))
            if 18 <= edad <= 120:
                # Verificar que esté cerca de palabras relacionadas con edad
                contexto_antes = texto[max(0, match.start()-50):match.start()]
                contexto_despues = texto[match.end():min(len(texto), match.end()+50)]
                contexto = contexto_antes + contexto_despues
                
                if any(palabra in contexto.lower() for palabra in ['año', 'edad', 'comparece', 'compareció']):
                    print(f"   ✓ Edad encontrada (contexto): {edad}")
                    return edad
        
        print("   ⚠️ No se pudo extraer la edad")
        return None