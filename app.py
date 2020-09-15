import os
import datetime
from base64 import b64encode, b64decode
import requests
import jwt
from bs4 import BeautifulSoup
from ics import Calendar, Event
from flask import Flask, request, render_template
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import arrow

# ASEGÚRESE DE CONFIGURAR LA VARIABLE DE ENTORNO 'SECRET' CON UN STRING ALEATORIO CRIPTOGRÁFICAMENTE SEGURO
SECRET = os.environ.get('SECRET')



def td_login(username, password):

    # Obtiene los tokens de login iniciales
    try:
        initial_request = requests.get('https://tecdigital.tec.ac.cr/register/?return_url=%2fdotlrn%2f', timeout=10)
    except requests.exceptions.Timeout:
        raise Exception('El TEC Digital está caído. Por favor inténtelo de nuevo más tarde.')
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

    soup = BeautifulSoup(initial_request.content, features='lxml')

    time = soup.find('input', {'name': 'time'}).get('value')

    token_id = soup.find('input', {'name': 'token_id'}).get('value')

    tdhash = soup.find('input', {'name': 'hash'}).get('value')


    # Ahora sí hace el request del login
    data = f'form%3Aid=login&return_url=%2Fdotlrn%2F&time={time}&token_id={token_id}&hash={tdhash}&retoken=allow&username={username}&password={password}'

    session = requests.Session()
    try:
        session.post('https://tecdigital.tec.ac.cr/register/', data=data, allow_redirects=False, timeout=10)
    except requests.exceptions.Timeout:
        raise Exception('El TEC Digital está caído. Por favor inténtelo de nuevo más tarde.')
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

    return session

def get_calendar(user, password):
    # Verifica inicio de sesión correcto
    session = td_login(user, password)
    date = datetime.datetime.today()
    try:
        response = session.get('https://tecdigital.tec.ac.cr/dotlrn/?date=' + date.strftime('%Y-%m-%d') + '&view=list&page_num=1&period_days=90',
                               allow_redirects=False, timeout=10)
    except requests.exceptions.Timeout:
        raise Exception('El TEC Digital está caído. Por favor inténtelo de nuevo más tarde.')
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

    if response.status_code != 200:
        raise Exception('Los datos son incorrectos o el TEC Digital está caído.')


    # Parsea eventos del HTML
    events = []

    soup = BeautifulSoup(response.content, features='lxml')
    table = soup.find('table', attrs={'class':'list-table'})
    table_body = table.find('tbody')

    rows = table_body.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        events.append([ele for ele in cols if ele]) #elimina elementos vacíos

    # Crea el iCal
    cal = Calendar()

    for event_data in events:
        e = Event()
        e.name = f'{event_data[2]} - {event_data[3]}'
        # HOTFIX: eventos sin descripción
        try:
            e.description = event_data[4].replace('Pulse aquí para ir a', 'Puede encontrar más detalles en')
        except IndexError:
            e.description = ""
        date = arrow.get(event_data[0], 'DD MMMM YYYY', locale='es').replace(tzinfo='America/Costa_Rica')
        e.begin = date
        if event_data[1] == 'Evento para todo el día':
            e.make_all_day()
        else:
            # HOTFIX: el TEC Digital de alguna forma permite horas inválidas, hace eventos all_day si no puede parsear
            try:
                e.begin = arrow.get(event_data[0] + ' ' + event_data[1][0:5], 'DD MMMM YYYY HH:mm', locale='es').replace(tzinfo='America/Costa_Rica')
                e.end = arrow.get(event_data[0] + ' ' + event_data[1][8:], 'DD MMMM YYYY HH:mm', locale='es').replace(tzinfo='America/Costa_Rica')
            except:
                e.make_all_day()
        cal.events.add(e)

    return cal


# Carga Flask
app = Flask(__name__)


# Página principal
@app.route("/")
def index():
    return render_template("index.html")

# Generación de tokens JWT
@app.route('/tokens', methods=['POST'])
def create_token():
    try:
        if not SECRET:
            raise Exception("La variable de entorno SECRET no se ha inicializado.")

        user = request.form['user'].strip()
        password = request.form['password'].strip()

        # Intenta obtener el calendario para verificar los datos de inicio de sesión
        get_calendar(user, password)

        iv = get_random_bytes(16)
        cipher = AES.new(SECRET[0:32].encode('utf-8'), AES.MODE_CFB, iv)

        # Prepara strings seguros
        user = b64encode(cipher.encrypt(user.encode('utf-8'))).decode('utf-8')
        password = b64encode(cipher.encrypt(password.encode('utf-8'))).decode('utf-8')
        iv = b64encode(iv).decode('utf-8')


        encoded_jwt = jwt.encode({'user': user, 'password': password, 'iv': iv}, SECRET, algorithm='HS256')


        return f'https://tdcal.josvar.com/{encoded_jwt.decode("utf-8")}/cal.ics'

    except Exception as e:
        return f'Ha ocurrido un error: {e}', 500

# Routa para descargar el calendario tomando un token JWT
@app.route('/<token>/cal.ics', methods=['GET'])
def read_calendar(token):
    try:
        if not SECRET:
            raise Exception("La variable de entorno SECRET no se ha inicializado.")

        data = jwt.decode(token, SECRET, algorithms=['HS256'])
        if "iv" in data:
            cipher = AES.new(SECRET[0:32].encode('utf-8'), AES.MODE_CFB, b64decode(data['iv']))
            user = cipher.decrypt(b64decode(data['user'])).decode('utf-8')
            password = cipher.decrypt(b64decode(data['password'])).decode('utf-8')
        else:
            user = data['user']
            password = data['password']

        print(user)
        print(password)

        cal = get_calendar(user, password)

        cal = str(cal).replace('PRODID:ics.py - http://git.io/lLljaA', 'X-WR-CALNAME:TEC Digital')

        return str(cal), 200, {'Content-Type': 'text/calendar; charset=utf-8'}

    except Exception as e:
        return f'Ha ocurrido un error: {e}', 500


# Inicialización Flask
port = int(os.environ.get('PORT', 8080))
if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=port)
