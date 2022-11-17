# syntax=docker/dockerfile:1
FROM python:3-alpine
RUN pip install --upgrade pip
RUN pip install waitress

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD waitress-serve --listen=*:8080 --call --url-scheme=https wsgi:setup_app