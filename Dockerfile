FROM python:3.8

ENV AUTO_DOWNLOAD true

# set the working directory in the container
WORKDIR /download

# copy the dependencies file to the working directory
COPY requirements.txt /code/requirements.txt

# install dependencies
RUN pip install -r /code/requirements.txt

# copy the content of the local src directory to the working directory
COPY app.py /code

# command to run on container start
CMD [ "python", "/code/app.py" ] 
