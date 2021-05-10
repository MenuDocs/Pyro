FROM python:3.9.5-alpine
COPY . /pyro
WORKDIR pyro
RUN apk add build-base
RUN pip3 install -r requirements.txt

CMD python3 main.py