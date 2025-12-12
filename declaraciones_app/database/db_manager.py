import sqlite3
from datetime import datetime
from config import DB_PATH
import bcrypt

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.crear_tablas()
        
        self.verificar_tabla_sugerencias()
        
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
        
        # Tabla de usuarios (autenticación)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                nombre_completo TEXT,
                rol TEXT DEFAULT 'usuario',
                activo INTEGER DEFAULT 1,
                creado_en TEXT NOT NULL,
                ultimo_login TEXT
            )
        ''')
        
        # Tabla de sugerencias de palabras (nombres, apellidos, etc.)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sugerencias_palabras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                palabra TEXT NOT NULL,
                frecuencia INTEGER DEFAULT 1,
                UNIQUE(tipo, palabra)
            )
        ''')
        
        # Crear usuario admin por defecto si no existe
        self.cursor.execute("SELECT COUNT(*) FROM usuarios")
        total_usuarios = self.cursor.fetchone()[0]
        if total_usuarios == 0:
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # usuario: admin / password por defecto: admin
            self.cursor.execute('''
                INSERT INTO usuarios (username, password, nombre_completo, rol, activo, creado_en)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ("admin", "admin", "Administrador", "admin", 1, ahora))
            self.conn.commit()
        
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
        
       # Validar y normalizar apellido de casada (solo para sexo femenino)
        apellido_casada = self._normalizar_apellido_casada(datos)
        
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
    
    def buscar_personas_por_nombre(self, nombre):
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
        
        except Exception as e:
            print(f"Error en buscar_personas_por_nombre: {e}")
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
    
    def obtener_ultimo_documento_acta(self, persona_id):
        """Devuelve la ruta del último documento tipo 'acta' de una persona, o None si no hay."""
        try:
            self.cursor.execute('''
                SELECT ruta_archivo
                FROM documentos
                WHERE persona_id = ? AND (tipo_documento IS NULL OR tipo_documento = 'acta')
                ORDER BY fecha_carga DESC, id DESC
                LIMIT 1
            ''', (persona_id,))
            row = self.cursor.fetchone()
            return row[0] if row and row[0] else None
        except Exception as e:
            print("Error en obtener_ultimo_documento_acta:", e)
            return None
    
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
    
    def verificar_dpi_existe(self, dpi):
        """Verifica si un DPI ya existe en la base de datos"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM personas WHERE dpi = ?", (dpi,))
            resultado = cursor.fetchone()
            return resultado[0] > 0
        except Exception as e:
            print(f"Error al verificar DPI: {e}")
            return False
    
    def obtener_todas_personas(self):
        """
        Devuelve todas las personas registradas en la tabla 'personas'.
        Formato esperado por la UI:
            (id, nombre_completo, dpi, edad, estado_civil,
            nacionalidad, domicilio, nivel_academico,
            apellido_casada, fecha_registro, sexo, fecha_nacimiento)
        Ajusta los nombres de columnas si es necesario.
        """
        self.cursor.execute("""
            SELECT
                id,
                nombre_completo,
                dpi,
                edad,
                estado_civil,
                nacionalidad,
                domicilio,
                nivel_academico,
                apellido_casada,
                fecha_registro,
                sexo,
                fecha_nacimiento
            FROM personas
        """)
        return self.cursor.fetchall()
    
    def obtener_todos_documentos(self):
        """
        Devuelve todos los documentos ÚNICOS (un documento por persona).
        Si una persona tiene múltiples documentos, devuelve solo el más reciente.
        
        VERSIÓN MEJORADA: Limpia automáticamente registros duplicados antiguos.
        """
        try:
            # Primero, limpiar registros duplicados (mantener solo el más reciente por persona)
            self.cursor.execute("""
                DELETE FROM documentos
                WHERE id NOT IN (
                    SELECT MAX(id)
                    FROM documentos
                    GROUP BY persona_id
                )
            """)
            self.conn.commit()
            
            # Ahora obtener todos los documentos (ya sin duplicados)
            self.cursor.execute("""
                SELECT
                    d.id,
                    d.nombre_archivo,
                    d.ruta_archivo,
                    d.fecha_carga,
                    p.nombre_completo,
                    p.dpi,
                    d.persona_id
                FROM documentos d
                LEFT JOIN personas p ON d.persona_id = p.id
                ORDER BY d.fecha_carga DESC, d.id DESC
            """)
            return self.cursor.fetchall()
        
        except Exception as e:
            print(f"Error al obtener documentos: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def eliminar_documento_por_id(self, documento_id):
        """Elimina un documento por su ID."""
        try:
            self.cursor.execute("DELETE FROM documentos WHERE id = ?", (documento_id,))
            self.conn.commit()
        except Exception as e:
            print(f"Error al eliminar documento: {e}")
            raise

    def eliminar_persona_por_id(self, persona_id):
        """Elimina una persona por su ID (y opcionalmente documentos, si quieres en cascada)."""
        try:
            # Si quieres, antes puedes borrar sus documentos:
            # self.cursor.execute("DELETE FROM documentos WHERE persona_id = ?", (persona_id,))

            self.cursor.execute("DELETE FROM personas WHERE id = ?", (persona_id,))
            self.conn.commit()
        except Exception as e:
            print(f"Error al eliminar persona: {e}")
            raise

    # ===== MÉTODOS PARA USUARIOS (LOGIN + CRUD CON BCRYPT) =====

    def autenticar_usuario(self, username, password):
        """
        Verifica credenciales de usuario con bcrypt (case-insensitive para username).
        Devuelve:
            - dict con info del usuario si es correcto y está activo
            - None si no es válido.
        """
        # Buscar usuario (case-insensitive)
        self.cursor.execute('''
            SELECT id, username, password, nombre_completo, rol, activo
            FROM usuarios
            WHERE LOWER(username) = LOWER(?)
        ''', (username,))
        row = self.cursor.fetchone()

        if not row:
            return None

        # Verificar si está activo
        if row[5] != 1:  # activo = 1
            return None

        # Verificar contraseña con bcrypt
        password_hash = row[2]
        
        try:
            # Intentar verificar con bcrypt
            if not bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                return None
        except Exception:
            # Si falla (contraseña en texto plano antigua), verificar directamente
            # Esto es para compatibilidad con usuarios antiguos
            if password != password_hash:
                return None
            
            # MIGRACIÓN AUTOMÁTICA: actualizar a bcrypt
            try:
                nuevo_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                self.cursor.execute('UPDATE usuarios SET password = ? WHERE id = ?', (nuevo_hash, row[0]))
                self.conn.commit()
                print(f"✅ Contraseña migrada a bcrypt para usuario: {row[1]}")
            except Exception as e:
                print(f"⚠️ No se pudo migrar contraseña a bcrypt: {e}")

        # Actualizar último login
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute('UPDATE usuarios SET ultimo_login = ? WHERE id = ?', (ahora, row[0]))
        self.conn.commit()

        return {
            "id": row[0],
            "username": row[1],
            "nombre_completo": row[3],
            "rol": row[4],
            "activo": row[5]
        }

    def crear_usuario(self, username, password, nombre_completo="", rol="usuario", activo=True):
        """
        Crea un nuevo usuario con contraseña encriptada usando bcrypt.
        Username es case-insensitive (se guarda como fue escrito pero se valida en minúsculas).
        """
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Encriptar contraseña con bcrypt
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        self.cursor.execute('''
            INSERT INTO usuarios (username, password, nombre_completo, rol, activo, creado_en)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, password_hash, nombre_completo, rol, 1 if activo else 0, ahora))
        self.conn.commit()
        return self.cursor.lastrowid, "ok"

    def actualizar_usuario(self, user_id, username, nombre_completo, rol, activo):
        """
        Actualiza datos de un usuario (no cambia la contraseña aquí).
        """
        self.cursor.execute('''
            UPDATE usuarios
            SET username = ?, nombre_completo = ?, rol = ?, activo = ?
            WHERE id = ?
        ''', (username, nombre_completo, rol, 1 if activo else 0, user_id))
        self.conn.commit()

    def cambiar_password_usuario(self, user_id, nuevo_password):
        """Cambia la contraseña de un usuario (encriptada con bcrypt)."""
        password_hash = bcrypt.hashpw(nuevo_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self.cursor.execute('UPDATE usuarios SET password = ? WHERE id = ?', (password_hash, user_id))
        self.conn.commit()

    def eliminar_usuario(self, user_id):
        """Elimina un usuario por ID."""
        self.cursor.execute('DELETE FROM usuarios WHERE id = ?', (user_id,))
        self.conn.commit()

    def obtener_todos_usuarios(self):
        """Devuelve lista de todos los usuarios."""
        self.cursor.execute('''
            SELECT id, username, nombre_completo, rol, activo, creado_en, ultimo_login
            FROM usuarios
            ORDER BY username
        ''')
        return self.cursor.fetchall()

    def obtener_usuario_por_id(self, user_id):
        """Devuelve un usuario por ID."""
        self.cursor.execute('''
            SELECT id, username, nombre_completo, rol, activo, creado_en, ultimo_login
            FROM usuarios
            WHERE id = ?
        ''', (user_id,))
        return self.cursor.fetchone()

    def verificar_usuario_existe_case_insensitive(self, username, excluir_id=None):
        """
        Verifica si existe un usuario con ese nombre (case-insensitive).
        Si se proporciona excluir_id, no cuenta ese usuario (útil para edición).
        Retorna True si existe, False si no.
        """
        if excluir_id is None:
            self.cursor.execute('''
                SELECT COUNT(*) FROM usuarios 
                WHERE LOWER(username) = LOWER(?)
            ''', (username,))
        else:
            self.cursor.execute('''
                SELECT COUNT(*) FROM usuarios 
                WHERE LOWER(username) = LOWER(?) AND id != ?
            ''', (username, excluir_id))
        
        count = self.cursor.fetchone()[0]
        return count > 0


    # ===== MÉTODOS PARA SUGERENCIAS DE PALABRAS =====

    def obtener_sugerencias_palabra(self, tipo_palabra, texto_parcial):
        """
        Obtiene sugerencias de palabras desde la tabla de sugerencias.
        
        Args:
            tipo_palabra: 'nombre', 'apellido', 'nacionalidad', 'domicilio', 'nivel_academico'
            texto_parcial: Texto que el usuario está escribiendo
        
        Returns:
            Lista de sugerencias ordenadas por frecuencia
        """
        try:
            # Buscar sugerencias que coincidan (case-insensitive)
            self.cursor.execute("""
                SELECT palabra, frecuencia
                FROM sugerencias_palabras
                WHERE tipo = ? AND LOWER(palabra) LIKE LOWER(?)
                ORDER BY frecuencia DESC, palabra ASC
                LIMIT 10
            """, (tipo_palabra, f"{texto_parcial}%"))
            
            resultados = self.cursor.fetchall()
            return [r[0] for r in resultados]
        
        except Exception as e:
            print(f"Error al obtener sugerencias: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def aprender_sugerencias_desde_persona(self, datos_persona):
        """
        Aprende sugerencias desde los datos de una persona guardada.
        
        Args:
            datos_persona: Diccionario con los datos de la persona
        """
        try:
            # Crear tabla si no existe
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS sugerencias_palabras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL,
                    palabra TEXT NOT NULL,
                    frecuencia INTEGER DEFAULT 1,
                    UNIQUE(tipo, palabra)
                )
            """)
            
            # Mapeo de campos a tipos de sugerencias
            mapeo = {
                'nombre': 'nombre',
                'apellido_casada': 'apellido',
                'nacionalidad': 'nacionalidad',
                'domicilio': 'domicilio',
                'nivel_academico': 'nivel_academico'
            }
            
            for campo, tipo in mapeo.items():
                valor = datos_persona.get(campo, '').strip()
                
                if not valor:
                    continue
                
                # Para nombres, aprender cada palabra por separado
                if tipo == 'nombre':
                    palabras = valor.split()
                    for palabra in palabras:
                        if len(palabra) >= 2:
                            self._incrementar_sugerencia(tipo, palabra)
                else:
                    # Para otros campos, aprender la frase completa
                    if len(valor) >= 2:
                        self._incrementar_sugerencia(tipo, valor)
            
            self.conn.commit()
        
        except Exception as e:
            print(f"Error al aprender sugerencias: {e}")
            import traceback
            traceback.print_exc()

    def _incrementar_sugerencia(self, tipo, palabra):
        """Incrementa la frecuencia de una sugerencia o la crea si no existe"""
        try:
            self.cursor.execute("""
                INSERT INTO sugerencias_palabras (tipo, palabra, frecuencia)
                VALUES (?, ?, 1)
                ON CONFLICT(tipo, palabra) DO UPDATE SET
                    frecuencia = frecuencia + 1
            """, (tipo, palabra))
        except Exception as e:
            print(f"Error al incrementar sugerencia: {e}")
    
    def verificar_tabla_sugerencias(self):
        """Verifica y repara la tabla de sugerencias si es necesario"""
        # Verificar si la tabla existe
        self.cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='sugerencias_palabras'
        """)
        
        tabla_existe = self.cursor.fetchone()
        
        if tabla_existe:
            # Verificar estructura de la tabla
            self.cursor.execute("PRAGMA table_info(sugerencias_palabras)")
            columnas = {col[1] for col in self.cursor.fetchall()}
            
            # Si no tiene la columna 'frecuencia', recrear la tabla
            if 'frecuencia' not in columnas:
                # Respaldar datos si existen
                self.cursor.execute("SELECT * FROM sugerencias_palabras")
                datos_antiguos = self.cursor.fetchall()
                
                # Eliminar tabla antigua
                self.cursor.execute("DROP TABLE sugerencias_palabras")
                
                # Crear tabla nueva
                self.cursor.execute("""
                    CREATE TABLE sugerencias_palabras (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tipo TEXT NOT NULL,
                        palabra TEXT NOT NULL,
                        frecuencia INTEGER DEFAULT 1,
                        UNIQUE(tipo, palabra)
                    )
                """)
                
                # Restaurar datos si había
                if datos_antiguos:
                    for dato in datos_antiguos:
                        try:
                            # Intentar insertar con frecuencia 1
                            # dato[0] = id, dato[1] = palabra, dato[2] = tipo (orden antiguo)
                            self.cursor.execute("""
                                INSERT INTO sugerencias_palabras (tipo, palabra, frecuencia)
                                VALUES (?, ?, 1)
                            """, (dato[2], dato[1]))
                        except:  # noqa: E722
                            pass
                
                self.conn.commit()
        else:
            # Crear tabla desde cero
            self.cursor.execute("""
                CREATE TABLE sugerencias_palabras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL,
                    palabra TEXT NOT NULL,
                    frecuencia INTEGER DEFAULT 1,
                    UNIQUE(tipo, palabra)
                )
            """)
            self.conn.commit()
    
    def _es_valor_invalido(self, valor):
        """Verifica si un valor es inválido y no debe aprenderse"""
        if not valor or valor == 'None':
            return True
        
        textos_invalidos = [
            'personal de identificación',
            'documento personal',
            'identificación',
            'dpi',
            'cui',
            'código único',
            'renap',
            'registro nacional',
            'notario',
            'notarial',
            'abogado',
            'licenciado'
        ]
        
        valor_lower = valor.lower()
        for texto_invalido in textos_invalidos:
            if texto_invalido in valor_lower:
                return True
        
        return False

    def _es_palabra_invalida(self, palabra):
        """Verifica si una palabra individual es inválida"""
        if len(palabra) < 2:
            return True
        
        palabras_invalidas = [
            'de', 'del', 'la', 'el', 'los', 'las', 'con', 'por', 'para',
            'documento', 'personal', 'identificación', 'dpi', 'cui'
        ]
        
        return palabra.lower() in palabras_invalidas
    
    def _normalizar_apellido_casada(self, datos):
        """
        Valida y normaliza el apellido de casada.

        Reglas:
        - Solo se acepta si:
            * sexo = femenino
            * estado_civil = casada
        - Se limpia texto basura.
        - Se intenta dejar en formato 'de Apellido...' sin romper casos especiales.
        """
        apellido_casada = datos.get('apellido_casada', '')
        if not apellido_casada:
            return None

        apellido_casada = apellido_casada.strip()
        if not apellido_casada:
            return None

        # 1) Solo sexo F y estado civil CASADA
        sexo = (datos.get('sexo') or '').strip().lower()
        estado_civil = (datos.get('estado_civil') or '').strip().lower()

        es_femenino = sexo in ('femenino', 'f', 'mujer')
        es_casada = estado_civil == 'casada'

        if not (es_femenino and es_casada):
            # No se guarda apellido de casada para otros casos
            return None

        # 2) Descartar textos inválidos
        textos_invalidos = [
            "personal de identificación",
            "documento personal",
            "identificación",
            "dpi",
            "cui",
            "código único",
            "renap",
            "registro nacional",
            "notario",
            "notarial",
            "abogado",
            "licenciado"
        ]
        ap_lower = apellido_casada.lower()
        for t in textos_invalidos:
            if t in ap_lower:
                return None

        # 3) Casos especiales que se respetan tal cual
        casos_especiales = [
            "de la mata de gonzalez",
            # aquí puedes agregar más patrones especiales
        ]
        for ce in casos_especiales:
            if ce in ap_lower:
                return apellido_casada.title()

        # 4) Normalizar:
        #    - Si ya tiene 'de', capitalizamos y listo.
        #    - Si no, asumimos que es solo el apellido del esposo: "Gonzalez" -> "de Gonzalez"
        import re

        if re.search(r'\bde\b', ap_lower):
            return apellido_casada.strip().title()

        return f"de {apellido_casada.strip().title()}"
    
    def contar_personas(self):
        """Cuenta el total de personas en la base de datos"""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM personas")
            return self.cursor.fetchone()[0]
        except Exception as e:
            print(f"Error al contar personas: {e}")
            return 0

    def obtener_documentos_huerfanos(self):
        """
        Obtiene documentos registrados en BD cuyo archivo físico ya no existe.
        VERSIÓN MEJORADA: Compara solo por nombre de archivo, no por ruta completa.
        Retorna: lista de tuplas (id_documento, persona_id, nombre_archivo, ruta_archivo)
        """
        try:
            import os
            from config import DOCUMENTOS_DIR
            
            # Obtener todos los archivos físicos (solo nombres)
            archivos_fisicos = set()
            if os.path.exists(DOCUMENTOS_DIR):
                archivos_fisicos = {
                    f for f in os.listdir(DOCUMENTOS_DIR)
                    if f.lower().endswith(('.pdf', '.doc', '.docx'))
                }
            
            # Obtener todos los documentos de la BD
            self.cursor.execute("""
                SELECT id, persona_id, nombre_archivo, ruta_archivo
                FROM documentos
            """)
            
            todos_documentos = self.cursor.fetchall()
            huerfanos = []
            
            # Verificar cuáles no existen físicamente
            for doc in todos_documentos:
                nombre_archivo = doc[2]  # nombre_archivo
                
                # Verificar si el archivo existe físicamente
                if nombre_archivo not in archivos_fisicos:
                    huerfanos.append(doc)
            
            return huerfanos
        
        except Exception as e:
            print(f"Error al obtener documentos huérfanos: {e}")
            import traceback
            traceback.print_exc()
            return []

    def actualizar_ruta_documento(self, documento_id, nuevo_nombre, nueva_ruta):
        """Actualiza el nombre y ruta de un documento en la BD"""
        try:
            self.cursor.execute("""
                UPDATE documentos 
                SET nombre_archivo = ?, ruta_archivo = ?
                WHERE id = ?
            """, (nuevo_nombre, nueva_ruta, documento_id))
            self.conn.commit()
        except Exception as e:
            print(f"Error al actualizar ruta de documento: {e}")
            raise

    def obtener_persona_por_dpi(self, dpi):
        """
        Obtiene una persona por su DPI (normalizado sin espacios).
        Retorna la tupla completa de la persona o None.
        """
        try:
            dpi_limpio = dpi.replace(" ", "").replace("_", "")
            self.cursor.execute("""
                SELECT id, nombre_completo, dpi, edad, estado_civil, 
                    nacionalidad, domicilio, nivel_academico, 
                    apellido_casada, fecha_registro, sexo, fecha_nacimiento
                FROM personas
                WHERE REPLACE(REPLACE(dpi, ' ', ''), '_', '') = ?
            """, (dpi_limpio,))
            return self.cursor.fetchone()
        except Exception as e:
            print(f"Error al obtener persona por DPI: {e}")
            return None

    def obtener_documentos_por_persona(self, persona_id):
        """
        Obtiene todos los documentos de una persona específica.
        Retorna lista de tuplas (id, nombre_archivo, ruta_archivo, fecha_carga, tipo_documento)
        """
        try:
            self.cursor.execute("""
                SELECT id, nombre_archivo, ruta_archivo, fecha_carga, tipo_documento
                FROM documentos
                WHERE persona_id = ?
                ORDER BY fecha_carga DESC
            """, (persona_id,))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener documentos por persona: {e}")
            return []
      
    def cerrar(self):
        """Cierra la conexión a la base de datos"""
        self.conn.close()