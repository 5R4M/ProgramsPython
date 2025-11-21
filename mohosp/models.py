from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Paciente(db.Model):
    __tablename__ = 'pacientes'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    cedula = db.Column(db.String(20), unique=True, nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    direccion = db.Column(db.String(200))
    tipo_sangre = db.Column(db.String(5))
    alergias = db.Column(db.Text)
    enfermedades_cronicas = db.Column(db.Text)
    medicamentos_actuales = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Paciente {self.nombre} {self.apellido}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'apellido': self.apellido,
            'cedula': self.cedula,
            'fecha_nacimiento': self.fecha_nacimiento.strftime('%Y-%m-%d'),
            'telefono': self.telefono,
            'email': self.email,
            'direccion': self.direccion,
            'tipo_sangre': self.tipo_sangre,
            'alergias': self.alergias,
            'enfermedades_cronicas': self.enfermedades_cronicas,
            'medicamentos_actuales': self.medicamentos_actuales,
            'fecha_registro': self.fecha_registro.strftime('%Y-%m-%d %H:%M:%S')
        }