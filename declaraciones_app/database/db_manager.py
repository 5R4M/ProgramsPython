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
                palabra TEXT NOT NULL,
                tipo   TEXT NOT NULL   -- 'nombre', 'apellido', 'nacionalidad', 'domicilio', etc.
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
        Devuelve todos los documentos con los datos básicos de la persona asociada.

        Formato de cada fila:
            (
                id_documento,      # 0
                nombre_archivo,    # 1
                ruta_archivo,      # 2
                fecha_carga,       # 3
                nombre_persona,    # 4
                dpi_persona,       # 5
                persona_id         # 6
            )
        """
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
    
    # ===== MÉTODOS PARA USUARIOS (LOGIN + CRUD) =====

    def autenticar_usuario(self, username, password):
        """
        Verifica credenciales de usuario.
        Devuelve:
            - dict con info del usuario si es correcto y está activo
            - None si no es válido.
        """
        self.cursor.execute('''
            SELECT id, username, nombre_completo, rol, activo
            FROM usuarios
            WHERE username = ? AND password = ?
        ''', (username, password))
        row = self.cursor.fetchone()

        if not row:
            return None

        if row[4] != 1:  # activo = 1
            return None

        # Actualizar último login
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute('UPDATE usuarios SET ultimo_login = ? WHERE id = ?', (ahora, row[0]))
        self.conn.commit()

        return {
            "id": row[0],
            "username": row[1],
            "nombre_completo": row[2],
            "rol": row[3],
            "activo": row[4]
        }

    def crear_usuario(self, username, password, nombre_completo="", rol="usuario", activo=True):
        """
        Crea un nuevo usuario. Devuelve (id, 'ok') o lanza excepción si hay error (por ejemplo username duplicado).
        """
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute('''
            INSERT INTO usuarios (username, password, nombre_completo, rol, activo, creado_en)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, password, nombre_completo, rol, 1 if activo else 0, ahora))
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
        """Cambia la contraseña de un usuario."""
        self.cursor.execute('UPDATE usuarios SET password = ? WHERE id = ?', (nuevo_password, user_id))
        self.conn.commit()

    def eliminar_usuario(self, user_id):
        """Elimina un usuario por ID (no permite borrar el último admin, si quieres puedes extender)."""
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
    
    # ===== MÉTODOS PARA SUGERENCIAS DE PALABRAS =====

    def obtener_sugerencias_palabra(self, tipo, prefijo, limite=10):
        """
        Devuelve hasta 'limite' palabras de la tabla sugerencias_palabras
        cuyo texto inicie con el prefijo (case-insensitive).
        tipo: 'nombre', 'apellido', 'nacionalidad', 'domicilio', etc.
        """
        try:
            prefijo = prefijo.strip()
            if not prefijo:
                return []

            like_pat = prefijo + "%"
            self.cursor.execute(
                """
                SELECT palabra
                FROM sugerencias_palabras
                WHERE tipo = ? AND LOWER(palabra) LIKE LOWER(?)
                ORDER BY palabra ASC
                LIMIT ?
                """,
                (tipo, like_pat, limite)
            )
            filas = self.cursor.fetchall()
            return [f[0] for f in filas]
        except Exception as e:
            print(f"Error en obtener_sugerencias_palabra: {e}")
            return []

    def agregar_sugerencia_si_no_existe(self, palabra, tipo):
        """
        Inserta 'palabra' en sugerencias_palabras si no existe para ese 'tipo'.
        No distingue mayúsculas/minúsculas al verificar existencia.
        """
        try:
            palabra = palabra.strip()
            if not palabra:
                return

            # Verificar si ya existe (case-insensitive)
            self.cursor.execute(
                """
                SELECT 1 FROM sugerencias_palabras
                WHERE tipo = ? AND LOWER(palabra) = LOWER(?)
                LIMIT 1
                """,
                (tipo, palabra)
            )
            existe = self.cursor.fetchone()
            if existe:
                return

            self.cursor.execute(
                "INSERT INTO sugerencias_palabras (palabra, tipo) VALUES (?, ?)",
                (palabra, tipo)
            )
            self.conn.commit()
        except Exception as e:
            print(f"Error en agregar_sugerencia_si_no_existe: {e}")

    def aprender_sugerencias_desde_persona(self, datos_persona: dict):
        """
        A partir de los datos de una persona, registra sugerencias en la tabla.
        Espera un dict con claves como:
        - nombre       (campo de la GUI con nombre completo)
        - apellido_casada
        - nacionalidad
        - domicilio
        """
        try:
            conectores = {"de", "del", "la", "las", "los", "y"}

            # ===== 1) Nombres y apellidos desde 'nombre' =====
            nombre_completo = (datos_persona.get("nombre") or "").strip()
            if nombre_completo:
                partes = nombre_completo.split()
                n = len(partes)

                # Normalización rápida (para lógica interna, no para guardar):
                partes_lower = [p.lower() for p in partes]

                # Heurística:
                # - Si solo hay 1 palabra: la consideramos nombre.
                # - Si hay 2 palabras: 1 nombre + 1 apellido.
                # - Si hay 3 o más:
                #     * Tomamos típicamente 2-3 tokens iniciales como nombres
                #     * Y 1-2 tokens finales como apellidos (incluyendo conectores anteriores).

                nombres_tokens = []
                apellidos_tokens = []

                if n == 1:
                    nombres_tokens = [partes[0]]
                elif n == 2:
                    nombres_tokens = [partes[0]]
                    apellidos_tokens = [partes[1]]
                else:
                    # n >= 3
                    # Regla básica inicial: 2 primeros tokens como nombres
                    idx_fin_nombres = 2

                    # Si el tercer token parece también parte del nombre (por conector o nombre compuesto),
                    # lo añadimos a nombres.
                    if n >= 3:
                        # Si el tercer token es un conector o un nombre típico de pila, lo sumamos
                        if partes_lower[2] in conectores:
                            idx_fin_nombres = 3
                        else:
                            # Si el segundo token es un conector ("del Carmen"): también sumamos el tercero
                            if partes_lower[1] in conectores:
                                idx_fin_nombres = 3

                    # Definir nombres
                    nombres_tokens = partes[:idx_fin_nombres]

                    # El resto lo consideramos zona de apellidos
                    resto = partes[idx_fin_nombres:]
                    partes_lower[idx_fin_nombres:]

                    # Si en el resto hay conectores tipo "de la Cruz", mantenerlos con el apellido
                    # pero para registrar sugerencias, generaremos:
                    #  - tokens individuales
                    #  - algunas combinaciones consecutivas
                    apellidos_tokens = resto

                # Registrar nombres como sugerencias tipo "nombre"
                for token in nombres_tokens:
                    token = token.strip()
                    if token:
                        self.agregar_sugerencia_si_no_existe(token, "nombre")

                # Registrar apellidos
                if apellidos_tokens:
                    # 1) Tokens individuales
                    for token in apellidos_tokens:
                        t = token.strip()
                        if t:
                            self.agregar_sugerencia_si_no_existe(t, "apellido")

                    # 2) Combinaciones consecutivas (máximo 3 en cadena) para apellidos compuestos
                    #    Ej: ["de", "la", "Cruz", "García"] -> "de la Cruz", "Cruz García", "de la Cruz García"
                    m = len(apellidos_tokens)
                    for i in range(m):
                        # Longitud 2
                        if i + 1 < m:
                            combo2 = f"{apellidos_tokens[i]} {apellidos_tokens[i+1]}".strip()
                            self.agregar_sugerencia_si_no_existe(combo2, "apellido")
                        # Longitud 3
                        if i + 2 < m:
                            combo3 = f"{apellidos_tokens[i]} {apellidos_tokens[i+1]} {apellidos_tokens[i+2]}".strip()
                            self.agregar_sugerencia_si_no_existe(combo3, "apellido")

            # ===== 2) Apellido de casada (texto completo) =====
            ap_casada = (datos_persona.get("apellido_casada") or "").strip()
            if ap_casada:
                # Registrar texto completo
                self.agregar_sugerencia_si_no_existe(ap_casada, "apellido")
                # Y también tokens individuales
                partes_casada = ap_casada.split()
                for t in partes_casada:
                    t = t.strip()
                    if t:
                        self.agregar_sugerencia_si_no_existe(t, "apellido")

            # ===== 3) Nacionalidad =====
            nacionalidad = (datos_persona.get("nacionalidad") or "").strip()
            if nacionalidad:
                self.agregar_sugerencia_si_no_existe(nacionalidad, "nacionalidad")

            # ===== 4) Domicilio =====
            domicilio = (datos_persona.get("domicilio") or "").strip()
            if domicilio:
                self.agregar_sugerencia_si_no_existe(domicilio, "domicilio")

        except Exception as e:
            print(f"Error en aprender_sugerencias_desde_persona: {e}")
     
    def cerrar(self):
        """Cierra la conexión a la base de datos"""
        self.conn.close()