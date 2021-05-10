FROM python:3.9.5-slim
COPY . /pyro
WORKDIR pyro
RUN pip3 install -r requirements.txt

CMD python3 main.py