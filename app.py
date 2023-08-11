#Importamos las librerias necesarias para el proyecto
from flask import Flask, render_template, request, redirect, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField
from wtforms.validators import DataRequired, Length
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import os 
from werkzeug.utils import secure_filename

#Creamos la aplicacion 
app = Flask(__name__)
#Config para especificar la ruta donde almacenaremos los archivos
app.config['UPLOAD_FOLDER'] = 'static/uploads'
# le damos una secret key a nuestra DB
app.config['SECRET_KEY'] = 'Hufflepuff'
# Agregamos la DB a la app y le decimos que utilice sqlite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
#iniciamos la DB en la app 
db = SQLAlchemy(app)
#Apartado para el bcrypt 
bcrypt = Bcrypt(app)
#Pasmos la clase flask login para acceder a sus funciones
login_manager = LoginManager()
#Inicializamos login manager 
login_manager.init_app(app)
# Creamos la vista de inicio de sesion, para que los usuarios que quieren acceder a cietas paginas de la web tengan que loggearse
login_manager.login_view = "login"
##Creamos el decorador que se encarga de cargar el usuario segun su id
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


#Crear un modelo para nuestros usuarios 
#Creamos las columanas para la base de datos 
class User(db.Model,UserMixin):
    #Especificamos que el dato de la columna sera un entero, y le damos True a primary key para especificar que el id sera unico.
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(100), unique = True, nullable = False) # le damos unique para que no se pueda repetir el nombre, nullable False para que no pueda dejar el campo vacio. 
    correo = db.Column(db.String(100), unique = True, nullable = False)
    nombre = db.Column(db.String(100), nullable = False)
    apellido = db.Column(db.String(100), nullable = False)
    rol = db.Column(db.String(20), nullable = False)
    password = db.Column(db.String(100), nullable = False)

    #Instanciamos la DB
    def __init__(self, username, correo, nombre, apellido, rol, password):
        self.username = username
        self.correo = correo
        self.nombre = nombre
        self.apellido = apellido
        self.rol = rol
        self.password = password
#Creamos la DB para los materiales que se subiran a la pagina
class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    tema = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    archivo = db.Column(db.String(200), nullable=False)  # Nombre del archivo PDF
    id_profesor = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, titulo, tema,  descripcion, archivo, id_profesor):
        self.titulo = titulo
        self.tema = tema 
        self.descripcion = descripcion
        self.archivo = archivo
        self.id_profesor = id_profesor

#Le decimos que la siguiente accion sera en contexto de la app para que al crear la DB no hayan problemas
with app.app_context():
    #creamos la DB
    db.create_all()

#Formulario de registro 
class Formulario_registro(FlaskForm):
    username = StringField('Nombre de usuario', validators=[DataRequired(), Length(min=4, max=100)])
    correo = StringField('correo', validators=[DataRequired(), Length(min=4, max=100)])
    nombre = StringField('Nombre', validators=[DataRequired(), Length(min=4, max=100)])
    apellido = StringField('Apellido', validators=[DataRequired(), Length(min=4, max=100)])
    rol = SelectField('Rol', choices=[('profesor', 'Profesor'), ('estudiante', 'Estudiante')], validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Registrarse')

#Formulario de login 
class Formulario_login(FlaskForm):
    username = StringField("Nombre de usuario", validators=[DataRequired()])
    password = PasswordField("Contraseña", validators=[DataRequired()])
    submit = SubmitField("Iniciar sesion")

#RUTAS DE LA PAGINA 
#Ruta de REGISTRO   
@app.route('/')
def landing():
    return render_template('landing.html')

#Ruta de REGISTRO 
@app.route('/registro', methods = ['GET', 'POST'])
def registro():
    form = Formulario_registro()

    #Si el metodo es POST quiero que hagas esto 
    if request.method == 'POST':

        #Hago un query en la DB a traves del email y username
        usuario = User.query.filter_by(correo = form.correo.data, username = form.username.data).first()
        #Si el usuario no existe hace esto 
        if usuario is None:
            username = request.form['username']
            correo = request.form['correo']
            nombre = request.form['nombre']
            apellido = request.form['apellido']
            rol = request.form['rol']
            password = request.form['password']
            password = bcrypt.generate_password_hash(password).decode('utf-8')

            #Creamos el nuevo usuario 
            nuevo_usuario = User(username, correo, nombre, apellido, rol, password)
            #le pasamos el usuario nuevo a la DB
            db.session.add(nuevo_usuario)
            db.session.commit()
            return redirect('login')
        
    return render_template('registro.html', form = form)

@app.route('/login', methods = ['GET', 'POST'])
def login():
    form = Formulario_login()

    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

    #Buscamos al usuario en la base de datos 
        usuario = User.query.filter_by(username=username).first()
        #si el usuario y su contraseña son correctas
        if usuario and bcrypt.check_password_hash(usuario.password, password):
            #inicia sesion
            login_user(usuario)
            return redirect('home')
        else:
            return render_template('login.html', form=form)

    return render_template('login.html', form=form)

#Ruta para la homepage
@app.route('/home')
def home():
    return render_template('home.html')

#Ruta del perfil 
@app.route('/perfil')
@login_required
def perfil():
    # Obtenemos los materiales subidos por el profesor actual
    materiales = Material.query.filter_by(id_profesor=current_user.id).all()

    return render_template('perfil.html', materiales=materiales)

#Ruta para cerrar sesion
@app.route('/logout')
def logout():
    logout_user()
    return render_template('landing.html')

#Ruta para los formularios pdf
@app.route("/formulario")
@login_required
def formulario():

    return render_template('formulario.html')
#Ruta para subir los archivos
@app.route("/upload", methods=['POST'])
def uploader():
    if request.method == 'POST':

        #Creamos una entrada en para el archivo en la base de datos.
        titulo = request.form['titulo']
        tema = request.form['tema']
        descripcion = request.form['descripcion']
        documento = request.files['archivo']
        #Usamos la funcion secure_filename para que no se pueda ingresar archivos con caracteres no deseados o poco seguros
        filename = secure_filename(documento.filename)
        
        # Guardamos el archivo en el directorio "Archivos PDF"
        documento.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        archivo = filename

        #Creamos el nuevo material
        nuevo_material = Material(titulo, tema, descripcion, archivo, id_profesor = current_user.id)

        #Agregamos el material a la base de datos
        db.session.add(nuevo_material)
        db.session.commit()
        return redirect('perfil')

#Ruta para descargar los archivos
@app.route('/download/<int:material_id>')
def download_material(material_id):
    material = Material.query.get_or_404(material_id)
    return send_from_directory(app.config['UPLOAD_FOLDER'], material.archivo, as_attachment=True)


#Ruta para realizar el test de VARK
@app.route('/test_vark')
def test_vark():

    preguntas = {
    1: "Te toca cocinar algo especial para tu familia. ¿Qué harías?",
    2: "Tienes que escoger un alimento en un restaurante o un café. ¿Qué harías?",
    3: "Aparte del precio, ¿qué más influiría para comprar un libro de ciencia ficción?",
    4: "Has terminado una competencia y te gustaría tener alguna retroalimentación. ¿Cómo te gustaría recibir esta retroalimentación?",
    5: "Estás teniendo un problema con la rodilla. ¿Qué preferirías que el doctor hiciera?",
    6: "Estás a punto de comprar una cámara digital o un teléfono móvil. Aparte del precio, ¿qué más influiría en tu decisión?",
    7: "No estás muy seguro de cuál palabra está bien escrita: ¿trascendente o trasendente?. ¿Qué harías en esta situación?",
    8: "Cuando ingresas a una página de internet, ¿qué cosas son las que te gustaría que tenga?",
    9: "Estás planeando unas vacaciones para un grupo de personas. Te gustaría comentar a ellos el plan que estás preparando. ¿Cómo lo harías?",
    10: "Estás usando un libro, disco compacto o página de Internet para aprender a tomar fotos con tu cámara digital nueva. ¿Qué opciones te gustaría tener?",
    11: "Quieres aprender un programa nuevo, habilidad o juego en una computadora. ¿Cómo lo harías?",
    12: "Estás ayudando a alguien que quiere ir al aeropuerto, al centro del pueblo o la estación del ferrocarril. ¿Cómo lo ayudas?",
    13: "Recuerda un momento en tu vida donde aprendiste a hacer algo nuevo. Trata de no escoger una destreza física, como andar en bicicleta. ¿De qué manera aprendiste en ese momento?",
    14: "¿Qué preferirías que un maestro o conferencista use durante su explicación o conferencia?",
    15: "Un grupo de amigos que están de turista quieren conocer más sobre parques o reservas naturales en tu ciudad. ¿Qué harías?",
    16: "Te toca hacer un discurso para una conferencia o una ocasión especial. ¿Cómo lo llevarías a cabo?"
}

    opciones = {
        1: {
            "a": "Preguntar a amigos por sugerencias.",
            "b": "Dar una vista al recetario para ver fotos de platos y decidir con eso.",
            "c": "Usar un libro de cocina donde hay una buena receta que ya conocés.",
            "d": "Cocinar algo que sabes preparar sin la necesidad de instrucciones."
        },
        2: {
            "a": "Escuchar al mesero o pedir que amigos recomienden opciones.",
            "b": "Mirar lo que otros comen o mirar las fotos de los platillos.",
            "c": "Escoger de las descripciones en el menú.",
            "d": "Escoger algo que ya has probado antes."
        },
        3: {
            "a": "Que un amigo te hable acerca de él y te lo recomiende.",
            "b": "Que tenga historias reales, experiencias y ejemplos.",
            "c": "Que puedas leer previamente partes del libro.",
            "d": "Que el diseño de la tapa sea atractivo o llamativo."
        },
        4: {
            "a": "Viendo descripciones escritas de los resultados.",
            "b": "Viendo ejemplos de los ejercicios que usted ha hecho.",
            "c": "Viendo gráficos que muestran lo que usted ha logrado.",
            "d": "Escuchando de alguien que habla sobre tu rendimiento."
        },
        5: {
            "a": "Que use un modelo de plástico y te enseñe lo que está mal.",
            "b": "Que te muestre una página de internet o algo para leer relacionado al problema.",
            "c": "Que te describa lo que está mal con tu rodilla él mismo.",
            "d": "Que te enseñe un diagrama lo que está mal en tu rodilla."
        },
        6: {
            "a": "Que lo hayas probado antes.",
            "b": "Que el diseño sea moderno y atractivo a la vista.",
            "c": "Haber leído antes los detalles acerca de sus características.",
            "d": "Que el vendedor te informe acerca de sus características."
        },
        7: {
            "a": "Escribir ambas palabras en un papel y escojer la que mejor se vea.",
            "b": "Pensar en cómo suena cada palabra y escoger una.",
            "c": "Buscar la palabra en un diccionario.",
            "d": "Ver la palabra en mi mente y escoger según como la veo."
        },
        8: {
            "a": "Interesantes descripciones escritas, listas y explicaciones.",
            "b": "Un diseño interesante y características visuales.",
            "c": "Cosas que con un click pueda cambiar o examinar.",
            "d": "Canales donde puedo oír música, programas de radio o entrevistas."
        },
        9: {
            "a": "Usa un mapa o página de Internet para mostrarles los lugares.",
            "b": "Describir algunos de los puntos más sobresalientes.",
            "c": "Darles una copia del itinerario impreso.",
            "d": "Llamarles por teléfono o mandar mensaje por correo electrónico explicando el plan de viaje."
        },
        10: {
            "a": "Una oportunidad de hacer preguntas acerca de la cámara y sus características.",
            "b": "Esquemas o diagramas que muestran la cámara y la función de cada parte.",
            "c": "Ejemplos de buenas y malas fotos y cómo mejorarlas.",
            "d": "Aclarar las instrucciones escritas con listas y puntos sobre qué hacer."
        },
        11: {
            "a": "Hablar con gente que sabe acerca del programa.",
            "b": "Leer las instrucciones que vienen en el programa.",
            "c": "Seguir los esquemas en el libro que acompaña el programa.",
            "d": "Usar los controles o el teclado y aprender sobre la marcha."
        },
        12: {
            "a": "Vas con la persona al lugar.",
            "b": "Anotar las direcciones en un papel (sin mapa) y darselas.",
            "c": "Le dices las direcciones.",
            "d": "Le dibujas un croquis o le das un mapa."
        },
        13: {
            "a": "Viendo una demostración o a alguien hacerlo.",
            "b": "Con instrucciones escritas, en un manual o libro de texto.",
            "c": "Escuchando a alguien explicarlo y haciendole preguntas.",
            "d": "Con esquemas y diagramas o pistas visuales."
        },
        14: {
            "a": "Demostraciones, modelos o sesiones prácticas.",
            "b": "Folletos, libros o lecturas.",
            "c": "Diagramas, esquemas o gráficos.",
            "d": "Preguntas y respuestas, pláticas y oradores invitados."
        },
        15: {
            "a": "Los acompañas a un parque o reserva natural.",
            "b": "Le das un libro o folleto acerca de parques o reservas naturales.",
            "c": "Le das una plática acerca de parques o reservas naturales.",
            "d": "Les muestra imágenes de Internet, fotos o libros con dibujos."
        },
        16: {
            "a": "Escribir el discurso y aprenderlo leyéndolo varias veces.",
            "b": "Reunir muchos ejemplos e historias para hacer el discurso verdadero y práctico.",
            "c": "Escribir algunas palabras claves y practicar el discurso repetidas veces.",
            "d": "Hacer diagramas o esquemas que te ayuden a explicar las cosas."
        }
    }

    valores_respuestas = {
        1 : {"a": "aural", "b": "visual", "c": "lector", "d": "kinestésico"},
        2: {"a": "aural", "b": "visual", "c": "lector", "d": "kinestésico"},
        3: {"a": "aural", "b": "kinestésico", "c": "lector", "d": "visual"},
        4: {"a": "lector", "b": "kinestésico", "c": "visual", "d": "aural"},
        5: {"a": "kinestésico", "b": "lector", "c": "aural", "d": "visual"},
        6: {"a": "kinestésico", "b": "visual", "c": "lector", "d": "aural"},
        7: {"a": "kinestésico", "b": "aural", "c": "lector", "d": "visual"},
        8: {"a": "lector", "b": "visual", "c": "kinestésico", "d": "aural"},
        9: {"a": "visual", "b": "aural", "c": "lector", "d": "kinestésico"},
        10: {"a": "aural", "b": "lector", "c": "lector", "d": "lector"},
        11: {"a": "aural", "b": "lector", "c": "visual", "d": "kinestésico"},
        12: {"a": "kinestésico", "b": "lector", "c": "aural", "d": "visual"},
        13: {"a": "kinestésico", "b": "lector", "c": "aural", "d": "visual"},
        14: {"a": "kinestésico", "b": "lector", "c": "visual", "d": "aural"},
        15: {"a": "kinestésico", "b": "lector", "c": "aural", "d": "visual"},
        16: {"a": "lector", "b": "kinestésico", "c": "aural", "d": "visual"}
    }

    return render_template('test_vark.html', preguntas=preguntas, opciones=opciones, valores_respuestas=valores_respuestas)

@app.route('/evaluar', methods=['POST'])
def evaluar():
        #Diccionario para almacenar los puntajes 
        #la opcion a: almacenara el puntaje en aural, 
        puntajes = {"aural": 0, "visual": 0, "lector": 0, "kinestésico": 0}
        #Iterare desde el numero 1 al  16
        for pregunta_num in range(1, 17):
            #Estiraremos los datos del formulario con "pregunta_1 iterando del 1 al 16"
            respuesta = request.form[f"pregunta_{pregunta_num}"]
            puntajes[respuesta] += 1
        
        preferencia_vark = max(puntajes, key=puntajes.get)


        return render_template('resultado.html', puntajes=puntajes, preferencia_vark=preferencia_vark)




#Para tener el modo debug siempre activo 
if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8000,debug=True)