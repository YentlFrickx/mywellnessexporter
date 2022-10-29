# syntax=docker/dockerfile:1

FROM tecktron/python-waitress:latest

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .