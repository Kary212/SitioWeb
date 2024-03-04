from flask import Flask, render_template, request, redirect, url_for, flash,session
import mysql.connector
import pdfkit
import smtplib

import os 
from dotenv import load_dotenv
from email.message import EmailMessage
import ssl

import bcrypt


app = Flask(__name__, static_folder='static')
app.secret_key = "tu_clave_secreta"

# Configuración de la conexión a la base de datos
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="ticketturno"
)
cursor = db.cursor()

# Configuración de PDFKit
config = pdfkit.configuration(wkhtmltopdf='C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe')


load_dotenv()

email_sender = "karialexa2000@gmail.com"
password = os.getenv("PASSWORD")

def enviar_correo(correo_destino, cuerpo, asunto, adjunto_pdf):
    em = EmailMessage()
    em["From"] = email_sender
    em["To"] = correo_destino
    em["Subject"] = asunto
    em.set_content(cuerpo)

    with open(adjunto_pdf, "rb") as archivo_pdf:
        em.add_attachment(archivo_pdf.read(), maintype="application", subtype="octet-stream", filename="comprobante.pdf")

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
        smtp.login(email_sender, password)
        smtp.send_message(em)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registrar_turno', methods=['POST'])
def registrar_turno():
    if request.method == 'POST':
        area = request.form['area']
        nombreUsuario = request.form['nombreUsuario']
        correo = request.form['correo']
        fecha = request.form['fecha']
        hora = request.form['hora']
        problema = request.form['problema']
        estado = 'En proceso'
        try:
            cursor.execute("INSERT INTO turnos (area, nombreUsuario,correo, fechaServicio, horaServicio, problema, estado) VALUES (%s, %s, %s, %s, %s,%s,%s)", (area, nombreUsuario, correo, fecha, hora, problema, estado))
            db.commit()
            flash('Turno registrado correctamente.', 'success')

            cursor.execute("SELECT LAST_INSERT_ID()")
            numero_turno = cursor.fetchone()[0]

            html = render_template('comprobante.html', data={
                'Número de Turno': numero_turno,
                'Nombre de Usuario': nombreUsuario,
                'Correo': correo,
                'Área de Servicio': area,
                'Fecha de Servicio': fecha,
                'Hora de Servicio': hora,
                'Problema': problema
            })

            pdf_content = pdfkit.from_string(html, False, configuration=config, options={'encoding': 'utf-8'})

            # Guardar el PDF temporalmente en el servidor
            with open('comprobante_temp.pdf', 'wb') as archivo_pdf:
                archivo_pdf.write(pdf_content)

            # Enviar el correo electrónico con el PDF adjunto
            enviar_correo(correo, "En el Adjunto encontrarás tu comprobante de turno.", 'Confirmación de registro de turno', 'comprobante_temp.pdf')

            # Eliminar el PDF temporal después de enviarlo por correo electrónico
            os.remove('comprobante_temp.pdf')

            # return "Correo electrónico enviado satisfactoriamente a {}".format(correo)
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error al registrar el turno: {str(e)}', 'error')
            return redirect('/')


def enviar_correo_modificacion(correo_destino, cuerpo, asunto, adjunto_pdf):
    try:
        em = EmailMessage()
        em["From"] = email_sender
        em["To"] = correo_destino
        em["Subject"] = asunto
        em.set_content(cuerpo)

        with open(adjunto_pdf, "rb") as archivo_pdf:
            em.add_attachment(archivo_pdf.read(), maintype="application", subtype="octet-stream", filename="comprobante.pdf")

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
            smtp.login(email_sender, password)
            smtp.send_message(em)
        
        print("Correo electrónico enviado satisfactoriamente a", correo_destino)
    except Exception as e:
        print("Error al enviar el correo electrónico:", str(e))

# @app.route('/modificar_turno', methods=['POST'])
# def modificar_turno():
#     if request.method == 'POST':
#         numero_turno = request.form['numero_turno']
#         nombre_usuario = request.form['nombreUsuario']
#         area = request.form['area']
#         fecha = request.form['fecha']
#         hora = request.form['hora']
#         problema = request.form['problema']

#         # Realiza la actualización en la base de datos
#         try:
#             cursor.execute("UPDATE turnos SET area = %s, nombreUsuario = %s, fechaServicio = %s, horaServicio = %s, problema = %s WHERE numeroTurno = %s", (area, nombre_usuario, fecha, hora, problema, numero_turno))
#             db.commit()
#             flash('Turno modificado correctamente.', 'success')


#            # Generar comprobante en PDF con los datos modificados
#             html = render_template('comprobante.html', data={
#                 'Número de Turno': numero_turno, 
#                 'Nombre de Usuario': nombre_usuario,
#                  'Área de Servicio': area,
#                 'Fecha de Servicio': fecha, 
#                 'Hora de Servicio': hora,
#                 'Problema': problema
#             })
#             pdf_content = pdfkit.from_string(html, False, configuration=config) #genera el pdf en memoria

#             #devolver pdf como parte de la repsuesta HTTP 
#             response = make_response(pdf_content)
#             response.headers['Content-Type'] = 'application/pdf'
#             response.headers['Content-Disposition'] = 'attachment; filename=comprobante.pdf'
#             return response
#         except Exception as e:
#             # flash(f'Error al modificar el turno: {str(e)}', 'error')
#             return render_template('modificarTurno.html', turno=request.form)
@app.route('/modificar_turno', methods=['POST'])
def modificar_turno():
    if request.method == 'POST':
        numero_turno = request.form['numero_turno']
        nombre_usuario = request.form['nombreUsuario']
        correo = request.form['correo']
        area = request.form['area']
        fecha = request.form['fecha']
        hora = request.form['hora']
        problema = request.form['problema']

        try:
            # Verifica qué campos se están actualizando
            campos_actualizados = request.form.keys()

            # Si el campo 'correo' está presente y se está actualizando, usa el nuevo correo,
            # de lo contrario, consulta el correo existente en la base de datos
            if 'correo' in campos_actualizados:
                correo = request.form['correo']
            else:
                cursor.execute("SELECT correo FROM turnos WHERE numeroTurno = %s", (numero_turno,))
                correo = cursor.fetchone()[0]

            # Realiza la actualización en la base de datos
            cursor.execute("UPDATE turnos SET area = %s, nombreUsuario = %s, correo = %s, fechaServicio = %s, horaServicio = %s, problema = %s WHERE numeroTurno = %s", (area, nombre_usuario, correo, fecha, hora, problema, numero_turno))
            db.commit()
            flash('Turno modificado correctamente.', 'success')

            # Genera comprobante en PDF con los datos modificados
            html = render_template('comprobante.html', data={
                'Número de Turno': numero_turno, 
                'Nombre de Usuario': nombre_usuario,
                'Correo': correo,
                'Área de Servicio': area,
                'Fecha de Servicio': fecha, 
                'Hora de Servicio': hora,
                'Problema': problema
            })
            pdf_content = pdfkit.from_string(html, False, configuration=config)  # Genera el PDF en memoria

            # Guarda el PDF temporalmente en el servidor
            pdf_temp_path = 'comprobante_temp.pdf'
            with open(pdf_temp_path, 'wb') as archivo_pdf:
                archivo_pdf.write(pdf_content)

            # Envía el correo electrónico con el PDF adjunto utilizando la función enviar_correo_modificacion
            enviar_correo_modificacion(correo, "En el Adjunto encontrarás tu comprobante de turno modificado.", 'Confirmación de modificación de turno', pdf_temp_path)

            # Elimina el PDF temporal después de enviarlo por correo electrónico
            os.remove(pdf_temp_path)

            # Devuelve el PDF como parte de la respuesta HTTP
            response = make_response(pdf_content)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = 'attachment; filename=comprobante.pdf'
            return response
        except Exception as e:
            flash(f'Error al modificar el turno: {str(e)}', 'error')
            return render_template('modificarTurno.html', turno=request.form)


@app.route('/buscar_turno', methods=['GET', 'POST'])
def buscar_turno():
    if request.method == 'POST':
        numero_turno = request.form['numero_turno']
        area = request.form['area']
        
        # Buscar el turno en la base de datos
        cursor.execute("SELECT * FROM turnos WHERE numeroTurno = %s AND area = %s", (numero_turno, area))
        turno = cursor.fetchone()

        if turno:
            # Renderizar la plantilla modificar_turno.html con los datos del turno
            # Asegurar que turno contenga los datos esperados antes de pasarlos a la plantilla
            if len(turno) >= 6:
                return render_template('modificarTurno.html', turno=turno)
               
            else:
                flash('Los datos del turno son incompletos.', 'error')
                return redirect(url_for('index'))
               
        else:
            flash('No se encontró el turno.', 'error')
            return redirect(url_for('index'))

            
    return render_template('buscarTurno.html')




@app.route('/autenticar_admin', methods=['POST'])
def autenticar_admin():
    usuario = request.form.get('nombre_usuario')
    contrasena = request.form.get('contraseña')

    # Verifica las credenciales en la base de datos
    cursor.execute("SELECT * FROM usuarios WHERE nombre_usuario = %s AND contraseña = %s", (usuario, contrasena))
    usuario = cursor.fetchone()

    if usuario:
        # Si las credenciales son válidas, establece la variable de sesión para indicar que el usuario está autenticado como administrador
        session['admin_logged_in'] = True
           # Obtener los últimos 10 tickets de la base de datos
        cursor.execute("SELECT * FROM turnos ORDER BY numeroTurno DESC LIMIT 5")
        turnos = cursor.fetchall()
        # flash('Inicio de sesion exitoso')
        return render_template('panel_admin.html', turnos=turnos)
    else:
        # flash('Credenciales incorrectas', 'error') 
        return render_template('iniciar_sesion.html', error_message='Credenciales incorrectas')
        
        

@app.route('/tickets')
def tickets():
    # Obtener los tickets de la base de datos
    cursor.execute("SELECT * FROM turnos ORDER BY numeroTurno DESC")
    turnos = cursor.fetchall()

    print(turnos)  # Imprimir los resultados en la consola del servidor Flask

    return render_template('tickets.html', turnos=turnos)

# @app.route('/modificar_turno_admin/<int:numero_turno>', methods=['GET', 'POST'])
# def modificar_turno_admin(numero_turno):
#     # Consulta SQL para obtener los detalles del turno con el número de turno proporcionado
#     cursor.execute("SELECT * FROM turnos WHERE numeroTurno = %s", (numero_turno,))
#     detalles_turno = cursor.fetchone()

#     # Verifica si los detalles del turno existen
#     if detalles_turno:
#         if request.method == 'POST':
#             # Obtener los datos modificados del formulario
#             area = request.form['area']
#             nombre_usuario = request.form['nombreUsuario']
#             fecha = request.form['fecha']
#             hora = request.form['hora']
#             problema = request.form['problema']
#             numero_turno = request.form['numero_turno']

#             try:
#                 # Actualizar los detalles del turno en la base de datos
#                 cursor.execute("UPDATE turnos SET area = %s, nombreUsuario = %s, fechaServicio = %s, horaServicio = %s, problema = %s WHERE numeroTurno = %s",
#                                (area, nombre_usuario, fecha, hora, problema, numero_turno))
#                 db.commit()
#                 flash('Turno modificado correctamente.', 'success')
                
#                 # Redirigir a alguna página de confirmación o a la lista de tickets
#                 return redirect(url_for('tickets'))  # Por ejemplo, redirige a la lista de tickets
#             except Exception as e:
#                 # Manejar errores de base de datos
#                 flash(f'Error al modificar el turno: {str(e)}', 'error')
#                 return render_template('modificarEstadoAdmin.html', turno=detalles_turno)
#         else:
#             # Renderizar la plantilla para modificar el turno, pasando los detalles del turno
#             return render_template('modificarEstadoAdmin.html', turno=detalles_turno)
#     else:
#         # Manejar el caso donde el turno no se encuentra (puedes mostrar un mensaje de error o redirigir a una página adecuada)
#         flash('El turno no se encontró.', 'error')
#         return redirect(url_for('index'))  # Redirigir a la página de inicio u otra página apropiada

@app.route('/cambiar_estado_ticket/<int:numero_turno>', methods=['POST'])
def cambiar_estado_ticket(numero_turno):
    if request.method == 'POST':
        nuevo_estado = request.form['estado']
        
        try:
            # Actualizar el estado del ticket en la base de datos
            cursor.execute("UPDATE turnos SET estado = %s WHERE numeroTurno = %s", (nuevo_estado, numero_turno))
            db.commit()
            flash('Estado del ticket actualizado correctamente.', 'success')
            return redirect(url_for('tickets'))  # Redirige a la página de tickets después de actualizar el estado
        except Exception as e:
            # Manejar errores de base de datos
            flash(f'Error al cambiar el estado del ticket: {str(e)}', 'error')
            return redirect(url_for('tickets'))  # Redirige a la página de tickets en caso de error


@app.route('/ocultar_ticket/<int:numero_turno>', methods=['POST'])
def ocultar_ticket(numero_turno):
    # Aquí puedes actualizar el estado del ticket a "oculto" en la base de datos
    # Implementa la lógica para actualizar la base de datos según tus necesidades
    # Por ejemplo, puedes usar una sentencia SQL UPDATE
    # UPDATE turnos SET estado = 'Oculto' WHERE numeroTurno = numero_turno

    # Después de actualizar, puedes redirigir a la página principal o a donde sea necesario
    return redirect(url_for('tickets'))  # Redirigir a la página de tickets u otra página apropiada


@app.route('/buscar_por_nombre', methods=['GET'])
def buscar_por_nombre():
    nombre_usuario = request.args.get('nombre_usuario')
    # Lógica para buscar en la base de datos por nombre de usuario
    turnos_encontrados = tu_modulo_de_base_de_datos.buscar_turnos_por_nombre(nombre_usuario)
    return render_template('resultado_busqueda.html', turnos=turnos_encontrados)

@app.route('/panel_admin')
def panel_admin():
    # Obtener los últimos 10 tickets de la base de datos
    cursor.execute("SELECT * FROM turnos ORDER BY numeroTurno DESC LIMIT 10")
    turnos = cursor.fetchall()

    return render_template('panel_admin.html', turnos=turnos)

        

@app.route('/usuarios')
def usuarios():
    # Obtener los usuarios de la base de datos
    cursor.execute("SELECT * FROM usuarios")
    usuarios_db = cursor.fetchall()  # Cambia el nombre de la variable

    print(usuarios_db)  # Imprimir los resultados en la consola del servidor Flask

    return render_template('usuarios.html', usuarios=usuarios_db)  # Cambia el nombre del argumento

@app.route('/modificar_usuario_admin/<int:id>', methods=['GET', 'POST'])
def modificar_usuario_admin(id):
    # Consulta SQL para obtener los detalles del usuario con el ID proporcionado
    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id,))
    detalles_usuario = cursor.fetchone()

    # Verifica si los detalles del usuario existen
    if detalles_usuario:
        if request.method == 'POST':
            nombre_usuario = request.form['nombre_usuario']
            contrasena = request.form['contraseña']

            try:
                # Actualizar los detalles del usuario en la base de datos
                cursor.execute("UPDATE usuarios SET nombre_usuario = %s, contraseña = %s WHERE id = %s",
                               (nombre_usuario, contrasena, id))
                db.commit()
                flash('Usuario modificado correctamente.', 'success')
                
                # Redirigir a alguna página de confirmación o a la lista de usuarios
                return redirect(url_for('usuarios'))  # Por ejemplo, redirige a la lista de usuarios
            except Exception as e:
                # Manejar errores de base de datos
                flash(f'Error al modificar el usuario: {str(e)}', 'error')
                return render_template('modificarUsuarioAdmin.html', detalles_usuario=detalles_usuario)
        else:
            # Renderizar la plantilla para modificar el usuario, pasando los detalles del usuario
            return render_template('modificarUsuarioAdmin.html', detalles_usuario=detalles_usuario)
    else:
        # Manejar el caso donde el usuario no se encuentra (puedes mostrar un mensaje de error o redirigir a una página adecuada)
        flash('El usuario no se encontró.', 'error')
        return redirect(url_for('index'))  # Redirigir a la página de inicio o a otra página apropiada

@app.route('/reportes')
def reportes():
    try:
        # Consulta para obtener el total de solicitudes
        cursor.execute("SELECT COUNT(*) FROM turnos")
        total_solicitudes = cursor.fetchone()[0]

        # Consulta para obtener el número de solicitudes en proceso
        cursor.execute("SELECT COUNT(*) FROM turnos WHERE estado = 'En proceso'")
        solicitudes_en_proceso = cursor.fetchone()[0]

        # Consulta para obtener el número de solicitudes resueltas
        cursor.execute("SELECT COUNT(*) FROM turnos WHERE estado = 'Terminado'")
        solicitudes_resueltas = cursor.fetchone()[0]

        # Calcular porcentajes
        porcentaje_en_proceso = (solicitudes_en_proceso / total_solicitudes) * 100
        porcentaje_resueltas = (solicitudes_resueltas / total_solicitudes) * 100

        # Devolver los datos en formato JSON
        data = {
            'total_solicitudes': total_solicitudes,
            'solicitudes_en_proceso': solicitudes_en_proceso,
            'solicitudes_resueltas': solicitudes_resueltas,
            'porcentaje_en_proceso': porcentaje_en_proceso,
            'porcentaje_resueltas': porcentaje_resueltas
        }

        return render_template('reportes.html', data=data)
    except Exception as e:
        # Manejar errores de base de datos
        flash(f'Error al obtener los datos de las solicitudes: {str(e)}', 'error')
        return redirect(url_for('index'))

from flask import jsonify

@app.route('/datos_reportes')
def datos_reportes():
    try:
        # Consulta para obtener el total de solicitudes
        cursor.execute("SELECT COUNT(*) FROM turnos")
        total_solicitudes = cursor.fetchone()[0]

        # Consulta para obtener el número de solicitudes en proceso
        cursor.execute("SELECT COUNT(*) FROM turnos WHERE estado = 'En proceso'")
        solicitudes_en_proceso = cursor.fetchone()[0]

        # Consulta para obtener el número de solicitudes resueltas
        cursor.execute("SELECT COUNT(*) FROM turnos WHERE estado = 'Terminado'")
        solicitudes_resueltas = cursor.fetchone()[0]

        # Calcular porcentajes
        porcentaje_en_proceso = (solicitudes_en_proceso / total_solicitudes) * 100
        porcentaje_resueltas = (solicitudes_resueltas / total_solicitudes) * 100

        # Devolver los datos en formato JSON
        data = {
            'total_solicitudes': total_solicitudes,
            'solicitudes_en_proceso': solicitudes_en_proceso,
            'solicitudes_resueltas': solicitudes_resueltas,
            'porcentaje_en_proceso': porcentaje_en_proceso,
            'porcentaje_resueltas': porcentaje_resueltas
        }

        return jsonify(data)
    except Exception as e:
        # Manejar errores de base de datos
        return jsonify({'error': str(e)}), 500  # Devuelve el error como respuesta JSON con código de estado 500

@app.route('/tickets')
def tickets_recientes():
    # Obtener los últimos 10 tickets de la base de datos
    cursor.execute("SELECT * FROM turnos ORDER BY id DESC LIMIT 10")
    turnos = cursor.fetchall()

    print(turnos)  # Imprimir los resultados en la consola del servidor Flask

    return render_template('panel_admin.html', turnos=turnos)


# @app.route('/admin/registrar_turno', methods=['GET', 'POST'])
# def admin_registrar_turno():
#     if request.method == 'POST':
#         area = request.form['area']
#         nombreUsuario = request.form['nombreUsuario']
#         correo=request.form['correo']
#         fecha = request.form['fecha']
#         hora = request.form['hora']
#         problema = request.form['problema']
#         estado = 'En proceso'  # Por defecto, establecemos el estado del turno como 'En proceso'
#         try:
#             # Insertar el nuevo turno en la base de datos
#             cursor.execute("INSERT INTO turnos (area, nombreUsuario,correo, fechaServicio, horaServicio, problema, estado) VALUES (%s, %s, %s, %s, %s, %s,%s)", (area, nombreUsuario,correo, fecha, hora, problema, estado))
#             db.commit()
#             flash('Turno registrado correctamente.', 'success')
#             return redirect(url_for('panel_admin'))
#         except Exception as e:
#             # Manejar errores de base de datos
#             flash(f'Error al registrar el turno: {str(e)}', 'error')
#             return redirect(url_for('admin'))
#     else:
#         # Si es una solicitud GET, simplemente renderiza el formulario para registrar el turno
#         return render_template('agregar_turnoAdmin.html')

@app.route('/admin/registrar_turno', methods=['GET', 'POST'])
def admin_registrar_turno():
    if request.method == 'POST':
        area = request.form['area']
        nombreUsuario = request.form['nombreUsuario']
        correo = request.form['correo']
        fecha = request.form['fecha']
        hora = request.form['hora']
        problema = request.form['problema']
        estado = 'En proceso'  # Por defecto, establecemos el estado del turno como 'En proceso'
        try:
            # Insertar el nuevo turno en la base de datos
            cursor.execute("INSERT INTO turnos (area, nombreUsuario, correo, fechaServicio, horaServicio, problema, estado) VALUES (%s, %s, %s, %s, %s, %s, %s)", (area, nombreUsuario, correo, fecha, hora, problema, estado))
            db.commit()
            flash('Turno registrado correctamente.', 'success')

            # Obtener el número de turno recién insertado
            cursor.execute("SELECT LAST_INSERT_ID()")
            numero_turno = cursor.fetchone()[0]

            # Generar el contenido HTML para el comprobante
            html = render_template('comprobante.html', data={
                'Número de Turno': numero_turno,
                'Nombre de Usuario': nombreUsuario,
                'Correo': correo,
                'Área de Servicio': area,
                'Fecha de Servicio': fecha,
                'Hora de Servicio': hora,
                'Problema': problema
            })

            # Convertir el HTML a PDF
            pdf_content = pdfkit.from_string(html, False, configuration=config, options={'encoding': 'utf-8'})

            # Guardar el PDF temporalmente en el servidor
            with open('comprobante_temp.pdf', 'wb') as archivo_pdf:
                archivo_pdf.write(pdf_content)

            # Enviar el correo electrónico con el PDF adjunto
            enviar_correo(correo, "En el Adjunto encontrarás tu comprobante de turno.", 'Confirmación de registro de turno', 'comprobante_temp.pdf')

            # Eliminar el PDF temporal después de enviarlo por correo electrónico
            os.remove('comprobante_temp.pdf')

            # Redirigir a la página de inicio
            return redirect(url_for('panel_admin'))
        except Exception as e:
            # Manejar errores de base de datos u otros errores
            flash(f'Error al registrar el turno: {str(e)}', 'error')
            return redirect(url_for('admin_registrar_turno'))
    else:
        # Si es una solicitud GET, simplemente renderiza el formulario para registrar el turno
        return render_template('agregar_turnoAdmin.html')


@app.route('/cerrar_sesion', methods=['GET'])
def cerrar_sesion():
    # Elimina la variable de sesión que indica que el usuario está autenticado como administrador
    session.pop('admin_logged_in', None)
    # Redirige al usuario a la página de inicio de sesión
    return render_template('iniciar_sesion.html')


@app.route('/admin/registrar_usuario', methods=['GET', 'POST'])
def admin_registrar_usuario():
    if request.method == 'POST':
        nombre_usuario = request.form['nombre_usuario']
        contrasena=request.form['contrasena']
       
        try:
            # Insertar el nuevo turno en la base de datos
            cursor.execute("INSERT INTO usuarios (nombre_usuario, contraseña) VALUES (%s, %s)", (nombre_usuario,contrasena))
            db.commit()
            flash('Usuario registrado correctamente.', 'success')
            return redirect(url_for('usuarios'))
        except Exception as e:
            # Manejar errores de base de datos
            flash(f'Error al registrar el usuario: {str(e)}', 'error')
            return redirect(url_for('panel_admin'))
    else:
        # Si es una solicitud GET, simplemente renderiza el formulario para registrar el turno
        return render_template('agregar_UsuarioAdmin.html')
        

@app.route('/visualizar_turno/<int:numero_turno>')
def visualizar_turno(numero_turno):
    # Consulta SQL para obtener los detalles del turno con el número de turno proporcionado
    cursor.execute("SELECT * FROM turnos WHERE numeroTurno = %s", (numero_turno,))
    detalles_turno = cursor.fetchone()

    # Verifica si los detalles del turno existen
    if detalles_turno:
        # Renderiza la plantilla para visualizar el turno, pasando los detalles del turno
        return render_template('detalles_turno.html', turno=detalles_turno)
    else:
        # Maneja el caso donde el turno no se encuentra (puedes mostrar un mensaje de error o redirigir a una página adecuada)
        flash('El turno no se encontró.', 'error')
        return redirect(url_for('index'))  # Redirige a la página de inicio u otra página apropiada



@app.route('/visualizar_turno_admin/<int:numero_turno>', methods=['GET'])
def visualizar_turno_admin(numero_turno):
    # Consulta SQL para obtener los detalles del turno con el número de turno proporcionado
    cursor.execute("SELECT * FROM turnos WHERE numeroTurno = %s", (numero_turno,))
    detalles_turno = cursor.fetchone()

    # Verifica si los detalles del turno existen
    if detalles_turno:
                return render_template('visualizarTurnoAdmin.html', turno=detalles_turno)
    else:
        # Manejar el caso donde el turno no se encuentra (puedes mostrar un mensaje de error o redirigir a una página adecuada)
        flash('El turno no se encontró.', 'error')
        return redirect(url_for('index'))  # Redirigir a la página de inicio u otra página apropiada


@app.route('/modificar_estado_admin/<int:numero_turno>', methods=['POST'])
def modificar_estado_admin(numero_turno):
    # Obtener el nuevo estado del formulario
    nuevo_estado = request.form['nuevo_estado']

    try:
        # Actualizar el estado del turno en la base de datos
        cursor.execute("UPDATE turnos SET estado = %s WHERE numeroTurno = %s",
                       (nuevo_estado, numero_turno))
        db.commit()

        # Aquí puedes devolver una respuesta JSON si lo prefieres
        # Por ejemplo, puedes devolver un mensaje de éxito
        return jsonify({'message': 'Estado del turno actualizado correctamente'})
    except Exception as e:
        # Manejar errores de base de datos
        return jsonify({'error': str(e)}), 500  # Devuelve el error como JSON con código de estado 500

if __name__ == '__main__':
    app.run(debug=True)
