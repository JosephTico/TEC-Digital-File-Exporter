# TEC Digital Files Exporter

Script que permite exportar los archivos de cursos del [TEC Digital](https://tecdigital.tec.ac.cr/) del Instituto Tecnológico de Costa Rica, debido al borrado masivo de archivos que va a ocurrir el 31 de enero de 2021.

## Versión precompilada para Windows 10

Puede descargar una versión ejecutable, lista para usar, [haciendo clic acá](https://github.com/JosephTico/TEC-Digital-File-Exporter/releases/latest). No ocupa instalar nada más, solo descomprimir el ZIP y ejecutar `app.exe`.

Si puede usar Python, se recomienda seguir las instrucciones para la ejecución manual.

## Instrucciones para ejecución manual con Python

Para podere ejecutar este script necesita tener instalado Python 3.7 o superior. Clone este repositorio en la carpeta que desee trabajar e instale los requerimientos, ejecutando el comando:

```
pip  install  -r  requirements.txt
```
(Nota: Dependiendo de su instalación puede requerir correr `pip3` en lugar de `pip`)

Para correr el script simplemente ejecute el script `app.py` con su instalación de Python.
```
python app.py
```

Este script fue programado rápidamente en una hora. Ignore las posibles malas prácticas de programación :)

## Docker (La manera mas rapida si tiene Linux)

```bash
docker run -it -v $(pwd)/download:/download -e TEC_USERNAME=<CARNE> -e TEC_PASSWORD=<PIN> paroque28/tecdigitialsync
```
Sus archivos se guardaran en la carpeta actual dentro del directorio download.

Si necesita instalar docker: https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository

## Docker paso por paso
```bash
docker build . -t tecdigitalsync
docker run -it git pius-v $(pwd)/download:/download -e TEC_USERNAME=<CARNE> -e TEC_PASSWORD=<PIN> tecdigitalsync
```
