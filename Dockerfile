FROM python:3.12.12-trixie

LABEL maintainer="preyumkr"
LABEL author="preyumkr"

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt