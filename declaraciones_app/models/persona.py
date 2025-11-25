# models.py

class Persona:
    def __init__(self, id=None, nombre_completo="", dpi="", edad=None, 
                 estado_civil="", nacionalidad="", domicilio="", 
                 nivel_academico="", apellido_casada="", fecha_registro=None):
        self.id = id
        self.nombre_completo = nombre_completo
        self.dpi = dpi
        self.edad = edad
        self.estado_civil = estado_civil
        self.nacionalidad = nacionalidad
        self.domicilio = domicilio
        self.nivel_academico = nivel_academico
        self.apellido_casada = apellido_casada
        self.fecha_registro = fecha_registro
    
    def to_dict(self):
        """Convierte el objeto a diccionario"""
        return {
            'id': self.id,
            'nombre': self.nombre_completo,
            'dpi': self.dpi,
            'edad': self.edad,
            'estado_civil': self.estado_civil,
            'nacionalidad': self.nacionalidad,
            'domicilio': self.domicilio,
            'nivel_academico': self.nivel_academico,
            'apellido_casada': self.apellido_casada,
            'fecha_registro': self.fecha_registro
        }
    
    @staticmethod
    def from_tuple(data):
        """Crea un objeto Persona desde una tupla de la base de datos
        
        Orden esperado de la tupla (según db_manager.py):
        (id, nombre_completo, dpi, edad, estado_civil, 
         nacionalidad, domicilio, nivel_academico, 
         apellido_casada, fecha_registro)
        
        Índices:
        0: id
        1: nombre_completo
        2: dpi
        3: edad
        4: estado_civil
        5: nacionalidad
        6: domicilio
        7: nivel_academico
        8: apellido_casada
        9: fecha_registro
        """
        if not data:
            return None
        
        return Persona(
            id=data[0],
            nombre_completo=data[1] if data[1] else "Sin nombre",
            dpi=data[2] if len(data) > 2 else "",
            edad=data[3] if len(data) > 3 else None,
            estado_civil=data[4] if len(data) > 4 else "",
            nacionalidad=data[5] if len(data) > 5 else "",
            domicilio=data[6] if len(data) > 6 else "",
            nivel_academico=data[7] if len(data) > 7 else "",
            apellido_casada=data[8] if len(data) > 8 else "",
            fecha_registro=data[9] if len(data) > 9 else None
        )
    
    def __str__(self):
        return f"{self.nombre_completo} - DPI: {self.dpi}"