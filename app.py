import os
import sys
import datetime
from base64 import b64encode, b64decode
import requests
import re
import threading
import urllib.request
import getpass
import zipfile
from bs4 import BeautifulSoup
from progress.spinner import PixelSpinner
from progress.bar import Bar
from tqdm import tqdm
from os import environ


session = requests.Session()
globalError = False
semestres_final = []
dirname = os.path.dirname(__file__)


class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


def download_url(url, output_path):
    with DownloadProgressBar(unit='B', unit_scale=True,
                             miniters=1, desc=url.split('/')[-1]) as t:
        urllib.request.urlretrieve(url, filename=output_path, reporthook=t.update_to)

def print_error(msg):
    global globalError
    globalError = True
    print("\n\nERROR: " + msg)
    sys.exit(2)

def td_login(username, password):
    global session
    # Obtiene los tokens de login iniciales
    initial_request = requests.get('https://tecdigital.tec.ac.cr/register/?return_url=%2fdotlrn%2f', timeout=10)

    try:
        soup = BeautifulSoup(initial_request.content, features='lxml')

        time = soup.find('input', {'name': 'time'}).get('value')

        token_id = soup.find('input', {'name': 'token_id'}).get('value')

        tdhash = soup.find('input', {'name': 'hash'}).get('value')
    except:
        print_error('No se ha podido iniciar sesión, el TEC Digital debe estar caído. Por favor inténtelo de nuevo más tarde.')


    # Ahora sí hace el request del login
    data = f'form%3Aid=login&return_url=%2Fdotlrn%2F&time={time}&token_id={token_id}&hash={tdhash}&retoken=allow&username={username}&password={password}'

    session.post('https://tecdigital.tec.ac.cr/register/', data=data, allow_redirects=False, timeout=10)

    # Verifica login
    response = session.get('https://tecdigital.tec.ac.cr/dotlrn/courses', allow_redirects=False, timeout=10)
    if response.status_code != 200:
        print_error('Los datos son incorrectos o el TEC Digital está caído.')

    return session


def obtener_cursos():
    global session, globalError, semestres_final

    base = "https://tecdigital.tec.ac.cr"

    cursos_page = session.get('https://tecdigital.tec.ac.cr/dotlrn/courses', allow_redirects=True, timeout=10)
    
    soup = BeautifulSoup(cursos_page.content, features='lxml')
    cursos_html = soup.select_one("#main-content .portlet ul")
    semestres_html = cursos_html.find_all("li")


    for semestre in tqdm(semestres_html):
        titulo_semestre = semestre.find(text=True, recursive=False).strip()

        if "2020" in titulo_semestre or not titulo_semestre:
            continue

        cursos = []

        cursos_soup = semestre.find_all("li")

        for curso in cursos_soup:
            titulo_curso = curso.text.strip()
            url = base + curso.find("a", href=True)['href'].strip() + "file-storage"

            folder_page = session.get(url, allow_redirects=True, timeout=10)
            regex = re.compile(r"\$rootScope\.GL_FOLDER_ID = ([0-9]*);")
            folder_id = re.search(regex, folder_page.content.decode('utf-8')).group(1)


            cursos.append({"titulo": titulo_curso, "url": url, "folder_id": folder_id})


        data_semestre = {"titulo": titulo_semestre, "cursos": cursos}
        semestres_final.append(data_semestre)
        

# Obtenido de https://stackoverflow.com/questions/3041986/apt-command-line-interface-like-yes-no-input     
def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Responda con 'yes' o 'no' "
                             "(o 'y' o 'n').\n")



def cli_login():
    global session, globalError, semestres_final
    art = """
_____ __     __   __ ___           ___    __  __  ________ __  
||__ /  `   |  \|/ _`|| /\ |      |__ \_/|__)/  \|__)||__ |__) 
||___\__,   |__/|\__>||/~~\|___   |___/ \|   \__/|  \||___|  \ """
    print(art)
    print("Exportador de archivos del TEC Digital")
    print("Creado por Joseph Vargas - https://twitter.com/JosephTico\n\n")
    print("Ingrese sus credenciales del TEC Digital y presione Enter.")
    if "USERNAME" in environ:
        username = environ.get('USERNAME')
    else:
        username = input("Usuario: ").strip()

    if "PASSWORD" in environ:
        password = environ.get('PASSWORD')
    else:
        password = getpass.getpass("Contraseña: ")
   

    spinner = PixelSpinner('Iniciando sesión... ')

    thread = threading.Thread(target=td_login,args=(username,password))
    thread.start()

    while thread.is_alive() and globalError == False:
        spinner.next()
    
    thread.join()

    if globalError:
        return

    print("\n")


    print('Obteniendo cursos... ')

    thread = threading.Thread(target=obtener_cursos)
    thread.start()

    thread.join()

    if globalError:
        return

    print("\n")

    print("Se han cargado satisfactoriamente los siguientes cursos:")

    for semestre in semestres_final:
        print("# " + semestre["titulo"])

        for curso in semestre["cursos"]:
            print("-- " + curso["titulo"])

        print("\n")

    if "AUTO_DOWNLOAD" not in environ and not query_yes_no("¿Desea iniciar la descarga de todos los archivos en la carpeta actual?"):
        return


    for semestre in semestres_final:
        print("Descargando cursos de " + semestre["titulo"] + "...")
        
        if not os.path.exists(semestre["titulo"]):
            os.makedirs(semestre["titulo"])

        for curso in semestre["cursos"]:
            print("Descargando archivos de " + curso["titulo"] + "...")

            url = curso["url"] + "/download-archive?object_id=" + curso["folder_id"]
            response = session.get(url, stream=True)
            total_size_in_bytes= int(response.headers.get('content-length', 0))
            block_size = 1024 #1 Kibibyte
            progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
            filename = os.path.join(dirname, semestre["titulo"], curso["titulo"] + ".zip")
            with open(filename, 'wb') as file:
                for data in response.iter_content(block_size):
                    progress_bar.update(len(data))
                    file.write(data)
            if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
                print_error("Ha ocurrido un error al descargar el archivo.")

            with zipfile.ZipFile(filename,"r") as zip_ref:
                zip_ref.extractall(os.path.join(dirname, semestre["titulo"]))

            os.remove(filename)

            progress_bar.close()




        print("\n")
        print("Proceso finalizado.")


if __name__ == '__main__':
    cli_login()
