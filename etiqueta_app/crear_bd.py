import sqlite3
import hashlib
import os

# ✅ USAR LA MISMA RUTA QUE EN flask_app.py
DATABASE_PATH = '/home/salonso/mysite/inventario_usuarios.db'

def crear_base_datos():
    """Crea la base de datos y usuarios iniciales"""
    
    # Verificar si el directorio existe
    directorio = os.path.dirname(DATABASE_PATH)
    if not os.path.exists(directorio):
        print(f"⚠️ Creando directorio: {directorio}")
        os.makedirs(directorio, exist_ok=True)
    
    print(f"📂 Usando base de datos: {DATABASE_PATH}")
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Crear tabla
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nombre_completo TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            rol TEXT NOT NULL CHECK(rol IN ('Admin', 'User')),
            bodega_asignada TEXT,
            activo BOOLEAN NOT NULL DEFAULT 1,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_ultimo_acceso TIMESTAMP
        )
    ''')
    
    print("✅ Tabla 'usuarios' creada/verificada")
    
    # Verificar si admin existe
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'admin'")
    admin_exists = cursor.fetchone()[0] > 0
    
    if not admin_exists:
        print("👤 Creando usuarios predeterminados...")
        
        # Insertar admin
        admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
        cursor.execute('''
            INSERT INTO usuarios (username, password, nombre_completo, email, rol, activo)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('admin', admin_password, 'Administrador del Sistema', 'admin@bodega.com', 'Admin', True))
        print("   ✅ Usuario 'admin' creado (password: admin123)")
        
        # Insertar user1
        user1_password = hashlib.sha256('user123'.encode()).hexdigest()
        cursor.execute('''
            INSERT INTO usuarios (username, password, nombre_completo, email, rol, bodega_asignada, activo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('user1', user1_password, 'Usuario de Prueba', 'user@bodega.com', 'User', 'BODEGA_MEDICAMENTOS', True))
        print("   ✅ Usuario 'user1' creado (password: user123)")
    else:
        print("ℹ️ Usuario admin ya existe, no se crean duplicados")
    
    # Listar todos los usuarios
    cursor.execute("SELECT id, username, rol, activo, fecha_creacion FROM usuarios ORDER BY id")
    usuarios = cursor.fetchall()
    
    print(f"\n{'='*70}")
    print(f"👥 USUARIOS EN LA BASE DE DATOS ({DATABASE_PATH})")
    print(f"{'='*70}")
    print(f"{'ID':<5} {'USERNAME':<15} {'ROL':<10} {'ACTIVO':<10} {'FECHA CREACIÓN':<25}")
    print(f"{'-'*70}")
    
    for user in usuarios:
        user_id, username, rol, activo, fecha = user
        estado = "✅ Sí" if activo else "❌ No"
        print(f"{user_id:<5} {username:<15} {rol:<10} {estado:<10} {fecha:<25}")
    
    print(f"{'='*70}")
    print(f"Total: {len(usuarios)} usuario(s)")
    print(f"{'='*70}\n")
    
    conn.commit()
    conn.close()
    
    # Verificar permisos del archivo
    if os.path.exists(DATABASE_PATH):
        file_size = os.path.getsize(DATABASE_PATH)
        print(f"✅ Base de datos creada exitosamente")
        print(f"   📁 Ubicación: {DATABASE_PATH}")
        print(f"   📊 Tamaño: {file_size} bytes")
    else:
        print(f"❌ ERROR: No se pudo crear la base de datos en {DATABASE_PATH}")

if __name__ == '__main__':
    try:
        crear_base_datos()
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()