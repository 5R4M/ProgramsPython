from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
from models import db, Paciente
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

# Crear las tablas
with app.app_context():
    db.create_all()

# Rutas
@app.route('/')
def index():
    pacientes = Paciente.query.order_by(Paciente.fecha_registro.desc()).all()
    return render_template('index.html', pacientes=pacientes)

@app.route('/crear', methods=['GET', 'POST'])
def crear_paciente():
    if request.method == 'POST':
        try:
            nuevo_paciente = Paciente(
                nombre=request.form['nombre'],
                apellido=request.form['apellido'],
                cedula=request.form['cedula'],
                fecha_nacimiento=datetime.strptime(request.form['fecha_nacimiento'], '%Y-%m-%d'),
                telefono=request.form.get('telefono'),
                email=request.form.get('email'),
                direccion=request.form.get('direccion'),
                tipo_sangre=request.form.get('tipo_sangre'),
                alergias=request.form.get('alergias'),
                enfermedades_cronicas=request.form.get('enfermedades_cronicas'),
                medicamentos_actuales=request.form.get('medicamentos_actuales')
            )
            db.session.add(nuevo_paciente)
            db.session.commit()
            flash('✅ Paciente creado exitosamente', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'❌ Error al crear paciente: {str(e)}', 'danger')
    
    return render_template('form.html', titulo='➕ Nuevo Paciente', paciente=None)

@app.route('/ver/<int:id>')
def ver_paciente(id):
    paciente = Paciente.query.get_or_404(id)
    return render_template('detalle.html', paciente=paciente)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_paciente(id):
    paciente = Paciente.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            paciente.nombre = request.form['nombre']
            paciente.apellido = request.form['apellido']
            paciente.cedula = request.form['cedula']
            paciente.fecha_nacimiento = datetime.strptime(request.form['fecha_nacimiento'], '%Y-%m-%d')
            paciente.telefono = request.form.get('telefono')
            paciente.email = request.form.get('email')
            paciente.direccion = request.form.get('direccion')
            paciente.tipo_sangre = request.form.get('tipo_sangre')
            paciente.alergias = request.form.get('alergias')
            paciente.enfermedades_cronicas = request.form.get('enfermedades_cronicas')
            paciente.medicamentos_actuales = request.form.get('medicamentos_actuales')
            
            db.session.commit()
            flash('✅ Paciente actualizado exitosamente', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'❌ Error al actualizar paciente: {str(e)}', 'danger')
    
    return render_template('form.html', titulo='✏️ Editar Paciente', paciente=paciente)

@app.route('/eliminar/<int:id>')
def eliminar_paciente(id):
    paciente = Paciente.query.get_or_404(id)
    try:
        db.session.delete(paciente)
        db.session.commit()
        flash('✅ Paciente eliminado exitosamente', 'success')
    except Exception as e:
        flash(f'❌ Error al eliminar paciente: {str(e)}', 'danger')
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)