# syntax=docker/dockerfile:1

FROM tecktron/python-waitress:latest

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD waitress-serve --listen=*:8080 --call wsgi:setup_app