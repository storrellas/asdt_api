FROM node:10.14.2-alpine
MAINTAINER Sergi Torrellas

# Add dependencies
RUN apk add --no-cache --update python3 bash build-base mariadb-dev python3-dev libffi-dev jpeg-dev
RUN apk add --no-cache --update mongodb

# Install dependencies
ADD ./requirements.txt /repo/
WORKDIR /repo/
RUN pip3 install -r requirements.txt && pip3 install gunicorn && pip3 install mysqlclient
# RUN pip3 install -r requirements.txt
# RUN pip3 install gunicorn
# RUN pip3 install mysqlclient  

# Configure Django
ADD . /repo/
ADD ./docker/localsettings_docker.py /repo/asdt_api/localsettings.py
WORKDIR /repo/

EXPOSE 8000

# Run container
CMD gunicorn --access-logfile=- --bind 0.0.0.0:8080 asdt_api.wsgi
