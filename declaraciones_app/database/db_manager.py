import sqlite3
from datetime import datetime
from config import DB_PATH

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.crear_tablas()
        
        self.verificar_y_cargar_plantillas_existentes()
    
    def crear_tablas(self):
        """Crea las tablas necesarias en la base de datos"""
        
        # Tabla de plantillas
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS plantillas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                ruta_archivo TEXT NOT NULL,
                fecha_creacion TEXT NOT NULL,
                activa INTEGER DEFAULT 0
            )
        ''')
        
        # Tabla de personas
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS personas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_completo TEXT NOT NULL,
                sexo TEXT,
                fecha_nacimiento TEXT,
                edad INTEGER,
                estado_civil TEXT,
                apellido_casada TEXT,
                nacionalidad TEXT,
                nivel_academico TEXT,
                domicilio TEXT,
                dpi TEXT UNIQUE NOT NULL,
                fecha_registro TEXT NOT NULL,
                ultima_modificacion TEXT
            )
        ''')
        
        # Verificar si necesitamos agregar las columnas nuevas a tablas existentes
        self.cursor.execute("PRAGMA table_info(personas)")
        columnas = [col[1] for col in self.cursor.fetchall()]
        
        if 'sexo' not in columnas:
            self.cursor.execute('ALTER TABLE personas ADD COLUMN sexo TEXT')
        
        if 'fecha_nacimiento' not in columnas:
            self.cursor.execute('ALTER TABLE personas ADD COLUMN fecha_nacimiento TEXT')
        
        # Tabla de documentos cargados
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS documentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                persona_id INTEGER,
                nombre_archivo TEXT NOT NULL,
                ruta_archivo TEXT NOT NULL,
                fecha_carga TEXT NOT NULL,
                tipo_documento TEXT,
                FOREIGN KEY (persona_id) REFERENCES personas (id)
            )
        ''')
        
        # Tabla de historial de actas generadas
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS historial_actas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                persona_id INTEGER,
                fecha_acta TEXT NOT NULL,
                hora TEXT,
                minutos TEXT,
                anio INTEGER,
                ruta_documento TEXT,
                FOREIGN KEY (persona_id) REFERENCES personas (id)
            )
        ''')
        
        self.conn.commit()
    
    # ===== MÉTODOS PARA PLANTILLAS =====
    
    def guardar_plantilla(self, nombre, ruta_archivo, activar=True):
        """Guarda una nueva plantilla"""
        if activar:
            self.cursor.execute('UPDATE plantillas SET activa = 0')
        
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute('''
            INSERT INTO plantillas (nombre, ruta_archivo, fecha_creacion, activa)
            VALUES (?, ?, ?, ?)
        ''', (nombre, ruta_archivo, fecha_actual, 1 if activar else 0))
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def obtener_plantilla_activa(self):
        """Obtiene la plantilla activa"""
        self.cursor.execute('SELECT id, nombre, ruta_archivo FROM plantillas WHERE activa = 1')
        return self.cursor.fetchone()
    
    def obtener_todas_plantillas(self):
        """Obtiene todas las plantillas"""
        self.cursor.execute('SELECT id, nombre, fecha_creacion, activa FROM plantillas ORDER BY fecha_creacion DESC')
        return self.cursor.fetchall()
    
    def activar_plantilla(self, id_plantilla):
        """Activa una plantilla específica"""
        self.cursor.execute('UPDATE plantillas SET activa = 0')
        self.cursor.execute('UPDATE plantillas SET activa = 1 WHERE id = ?', (id_plantilla,))
        self.conn.commit()
    
    def eliminar_plantilla(self, id_plantilla):
        """Elimina una plantilla"""
        self.cursor.execute('SELECT ruta_archivo FROM plantillas WHERE id = ?', (id_plantilla,))
        resultado = self.cursor.fetchone()
        
        self.cursor.execute('DELETE FROM plantillas WHERE id = ?', (id_plantilla,))
        self.conn.commit()
        
        return resultado[0] if resultado else None
    
    # ===== MÉTODOS PARA PERSONAS =====
    
    def guardar_persona(self, datos):
        """Guarda o actualiza una persona"""
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Limpiar apellido de casada si contiene texto inválido
        apellido_casada = datos.get('apellido_casada', '').strip()
        
        if apellido_casada:
            textos_invalidos = [
                "personal de identificación",
                "documento personal",
                "identificación",
                "dpi",
                "cui",
                "código único",
                "renap"
            ]
            
            apellido_lower = apellido_casada.lower()
            for texto_invalido in textos_invalidos:
                if texto_invalido in apellido_lower:
                    apellido_casada = None
                    break
        else:
            apellido_casada = None
        
        # Verificar si existe
        dpi_limpio = datos['dpi'].replace(" ", "")
        self.cursor.execute('''
            SELECT id FROM personas WHERE REPLACE(dpi, ' ', '') = ?
        ''', (dpi_limpio,))
        
        resultado = self.cursor.fetchone()
        
        if resultado:
            # Actualizar
            persona_id = resultado[0]
            self.cursor.execute('''
                UPDATE personas
                SET nombre_completo = ?, sexo = ?, fecha_nacimiento = ?, edad = ?, 
                    estado_civil = ?, apellido_casada = ?, nacionalidad = ?, 
                    nivel_academico = ?, domicilio = ?, dpi = ?, ultima_modificacion = ?
                WHERE id = ?
            ''', (
                datos.get('nombre', ''),
                datos.get('sexo'),
                datos.get('fecha_nacimiento'),
                datos.get('edad'),
                datos.get('estado_civil'),
                apellido_casada,
                datos.get('nacionalidad'),
                datos.get('nivel_academico'),
                datos.get('domicilio'),
                datos['dpi'],
                fecha_actual,
                persona_id
            ))
            self.conn.commit()
            return persona_id, "actualizado"
        else:
            # Insertar
            self.cursor.execute('''
                INSERT INTO personas (
                    nombre_completo, sexo, fecha_nacimiento, edad, estado_civil, 
                    apellido_casada, nacionalidad, nivel_academico, domicilio, 
                    dpi, fecha_registro
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datos.get('nombre', ''),
                datos.get('sexo'),
                datos.get('fecha_nacimiento'),
                datos.get('edad'),
                datos.get('estado_civil'),
                apellido_casada,
                datos.get('nacionalidad'),
                datos.get('nivel_academico'),
                datos.get('domicilio'),
                datos['dpi'],
                fecha_actual
            ))
            self.conn.commit()
            return self.cursor.lastrowid, "guardado"
    
    def buscar_persona_por_dpi(self, dpi):
        """Busca una persona por DPI"""
        try:
            # Normalizar DPI (quitar espacios)
            dpi_limpio = dpi.replace(" ", "")
            
            self.cursor.execute('''
                SELECT id, nombre_completo, dpi, edad, estado_civil, 
                       nacionalidad, domicilio, nivel_academico, 
                       apellido_casada, fecha_registro, sexo, fecha_nacimiento
                FROM personas
                WHERE REPLACE(dpi, ' ', '') = ?
            ''', (dpi_limpio,))
            
            return self.cursor.fetchone()
        
        except Exception:
            return None
    
    def buscar_persona_por_nombre(self, nombre):
        """Busca personas por nombre (búsqueda parcial mejorada)"""
        try:
            # Normalizar nombre
            nombre = nombre.strip()
            
            if not nombre:
                return []
            
            # Búsqueda más flexible: divide el nombre en palabras
            palabras = nombre.split()
            
            # Construir consulta dinámica para buscar todas las palabras
            condiciones = []
            parametros = []
            
            for palabra in palabras:
                condiciones.append("LOWER(nombre_completo) LIKE ?")
                parametros.append(f'%{palabra.lower()}%')
            
            consulta = f'''
                SELECT id, nombre_completo, dpi, edad, estado_civil, 
                       nacionalidad, domicilio, nivel_academico, 
                       apellido_casada, fecha_registro, sexo, fecha_nacimiento
                FROM personas
                WHERE nombre_completo IS NOT NULL
                AND ({' AND '.join(condiciones)})
                ORDER BY nombre_completo
            '''
            
            self.cursor.execute(consulta, parametros)
            resultados = self.cursor.fetchall()
            
            # Si no encuentra con todas las palabras, buscar con cualquier palabra
            if not resultados and len(palabras) > 1:
                condiciones = []
                parametros = []
                
                for palabra in palabras:
                    condiciones.append("LOWER(nombre_completo) LIKE ?")
                    parametros.append(f'%{palabra.lower()}%')
                
                consulta = f'''
                    SELECT id, nombre_completo, dpi, edad, estado_civil, 
                           nacionalidad, domicilio, nivel_academico, 
                           apellido_casada, fecha_registro, sexo, fecha_nacimiento
                    FROM personas
                    WHERE nombre_completo IS NOT NULL
                    AND ({' OR '.join(condiciones)})
                    ORDER BY nombre_completo
                '''
                
                self.cursor.execute(consulta, parametros)
                resultados = self.cursor.fetchall()
            
            return resultados
        
        except Exception:
            return []
    
    def obtener_persona_por_id(self, persona_id):
        """Obtiene una persona por ID"""
        try:
            self.cursor.execute('''
                SELECT id, nombre_completo, dpi, edad, estado_civil, 
                       nacionalidad, domicilio, nivel_academico, 
                       apellido_casada, fecha_registro, sexo, fecha_nacimiento
                FROM personas
                WHERE id = ?
            ''', (persona_id,))
            
            return self.cursor.fetchone()
        
        except Exception:
            return None
    
    # ===== MÉTODOS PARA DOCUMENTOS =====
    
    def guardar_documento(self, persona_id, nombre_archivo, ruta_archivo, tipo_documento="acta"):
        """Guarda un documento en la base de datos"""
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute('''
            INSERT INTO documentos (persona_id, nombre_archivo, ruta_archivo, fecha_carga, tipo_documento)
            VALUES (?, ?, ?, ?, ?)
        ''', (persona_id, nombre_archivo, ruta_archivo, fecha_actual, tipo_documento))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def obtener_documentos_persona(self, persona_id):
        """Obtiene todos los documentos de una persona"""
        try:
            self.cursor.execute('''
                SELECT id, nombre_archivo, ruta_archivo, fecha_carga, tipo_documento
                FROM documentos
                WHERE persona_id = ?
                ORDER BY fecha_carga DESC
            ''', (persona_id,))
            
            return self.cursor.fetchall()
        
        except Exception:
            return []
    
    def obtener_estadisticas(self):
        """Obtiene estadísticas de la base de datos"""
        try:
            # Total de documentos
            self.cursor.execute('SELECT COUNT(*) FROM documentos')
            total_documentos = self.cursor.fetchone()[0]
            
            # Total de personas registradas
            self.cursor.execute('SELECT COUNT(*) FROM personas')
            total_personas = self.cursor.fetchone()[0]
            
            # Total de personas con nombre (no NULL)
            self.cursor.execute('SELECT COUNT(*) FROM personas WHERE nombre_completo IS NOT NULL')
            personas_con_nombre = self.cursor.fetchone()[0]
            
            # Total de plantillas activas
            self.cursor.execute('SELECT COUNT(*) FROM plantillas WHERE activa = 1')
            plantillas_activas = self.cursor.fetchone()[0]
            
            return {
                'total_documentos': total_documentos,
                'total_personas': total_personas,
                'personas_con_nombre': personas_con_nombre,
                'plantillas_activas': plantillas_activas
            }
        
        except Exception:
            return {
                'total_documentos': 0,
                'total_personas': 0,
                'personas_con_nombre': 0,
                'plantillas_activas': 0
            }
    
    def obtener_todos_documentos(self):
        """Obtiene todos los documentos cargados"""
        self.cursor.execute('''
            SELECT d.id, d.nombre_archivo, d.ruta_archivo, d.fecha_carga, 
                   p.nombre_completo, p.dpi
            FROM documentos d
            LEFT JOIN personas p ON d.persona_id = p.id
            ORDER BY d.fecha_carga DESC
        ''')
        return self.cursor.fetchall()
    
    def obtener_documento_por_id(self, documento_id):
        """Obtiene un documento por ID"""
        self.cursor.execute('''
            SELECT d.id, d.nombre_archivo, d.ruta_archivo, d.fecha_carga,
                   d.persona_id, p.nombre_completo, p.dpi
            FROM documentos d
            LEFT JOIN personas p ON d.persona_id = p.id
            WHERE d.id = ?
        ''', (documento_id,))
        return self.cursor.fetchone()
    
    # ===== MÉTODOS PARA HISTORIAL =====
    
    def guardar_historial_acta(self, persona_id, fecha_acta, hora, minutos, anio, ruta_documento):
        """Guarda un registro en el historial de actas"""
        self.cursor.execute('''
            INSERT INTO historial_actas (persona_id, fecha_acta, hora, minutos, anio, ruta_documento)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (persona_id, fecha_acta, hora, minutos, anio, ruta_documento))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def verificar_y_cargar_plantillas_existentes(self):
        """Verifica si hay plantillas en la carpeta que no están en la BD"""
        from config import PLANTILLAS_DIR
        import os
        
        # Verificar si hay plantilla activa
        plantilla_activa = self.obtener_plantilla_activa()
        
        if not plantilla_activa:
            # Buscar archivos .docx en la carpeta de plantillas
            if os.path.exists(PLANTILLAS_DIR):
                archivos = [f for f in os.listdir(PLANTILLAS_DIR) if f.endswith('.docx')]
                
                if archivos:
                    # Tomar el primer archivo encontrado
                    archivo = archivos[0]
                    ruta_completa = os.path.join(PLANTILLAS_DIR, archivo)
                    
                    # Registrar en la base de datos
                    self.guardar_plantilla(archivo, ruta_completa, activar=True)
    
    def corregir_nombres_notario(self):
        """Marca como NULL los nombres que corresponden al notario"""
        from config import NOMBRES_NOTARIOS
        
        try:
            filas_afectadas = 0
            
            for nombre_notario in NOMBRES_NOTARIOS:
                self.cursor.execute('''
                    UPDATE personas
                    SET nombre_completo = NULL
                    WHERE LOWER(nombre_completo) LIKE ?
                ''', (f'%{nombre_notario.lower()}%',))
                
                filas_afectadas += self.cursor.rowcount
            
            self.conn.commit()
            return filas_afectadas
        
        except Exception:
            return 0
    
    def cerrar(self):
        """Cierra la conexión a la base de datos"""
        self.conn.close()