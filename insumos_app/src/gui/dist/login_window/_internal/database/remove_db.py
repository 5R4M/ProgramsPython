import os
    
# Ruta donde se creará la base de datos
DB_PATH = os.path.join(os.path.dirname(__file__), '../../data/insumos.db')
DB_PATH = os.path.abspath(DB_PATH)

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)