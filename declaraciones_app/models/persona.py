class Persona:
    def __init__(self, id=None, nombre_completo="", edad=None, estado_civil="",
                 apellido_casada="", nacionalidad="", nivel_academico="",
                 domicilio="", dpi=""):
        self.id = id
        self.nombre_completo = nombre_completo
        self.edad = edad
        self.estado_civil = estado_civil
        self.apellido_casada = apellido_casada
        self.nacionalidad = nacionalidad
        self.nivel_academico = nivel_academico
        self.domicilio = domicilio
        self.dpi = dpi
    
    def to_dict(self):
        """Convierte el objeto a diccionario"""
        return {
            'id': self.id,
            'nombre': self.nombre_completo,
            'edad': self.edad,
            'estado_civil': self.estado_civil,
            'apellido_casada': self.apellido_casada,
            'nacionalidad': self.nacionalidad,
            'nivel_academico': self.nivel_academico,
            'domicilio': self.domicilio,
            'dpi': self.dpi
        }
    
    @staticmethod
    def from_tuple(data):
        """Crea un objeto Persona desde una tupla de la base de datos"""
        if not data:
            return None
        return Persona(
            id=data[0],
            nombre_completo=data[1],
            edad=data[2],
            estado_civil=data[3],
            apellido_casada=data[4],
            nacionalidad=data[5],
            nivel_academico=data[6],
            domicilio=data[7],
            dpi=data[8]
        )
    
    def __str__(self):
        return f"{self.nombre_completo} - DPI: {self.dpi}"