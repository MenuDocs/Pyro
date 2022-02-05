FROM python:3.9-slim

# Set pip to have cleaner logs and no saved cache
ENV PIP_NO_CACHE_DIR=false

RUN mkdir -p /pyro
WORKDIR pyro

COPY ./requirements.txt /pyro/requirements.txt
RUN pip3 install -r requirements.txt

COPY . /pyro

CMD python3 main.py