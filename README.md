# TEC Digital Calendar Exporter

Disponible en: [https://tdcal.josvar.com/](https://tdcal.josvar.com/)

Servicio que permite exportar el calendario personal disponible en la plataforma [TEC Digital](https://tecdigital.tec.ac.cr/) del Instituto Tecnológico de Costa Rica al formato iCalendar para su uso en otros servicios, como por ejemplo Google Calendar, Outlook, calendarios de Apple, etc.


[![Run on Google Cloud](https://storage.googleapis.com/cloudrun/button.svg)](https://console.cloud.google.com/cloudshell/editor?shellonly=true&cloudshell_image=gcr.io/cloudrun/button&cloudshell_git_repo=https://github.com/JosephTico/TEC-Digital-Calendar-Exporter.git)

Programado en Python 3. Para instalar todos los requerimientos de la aplicación ejecute el comando:

```
pip  install  -r  requirements.txt
```
Además debe configurar un string aleatorio critpográficamente seguro en la variable de entorno `SECRET` que será por la generación de tokens JWT.

Para correr la herramienta de forma local simplemente  ejecute `app.py` con su instalación de Python, versión 3.7 o superior.
