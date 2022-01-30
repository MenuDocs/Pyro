FROM python:3.8-slim
COPY . /pyro
WORKDIR pyro
RUN pip3 install -r requirements.txt

CMD python3 main.py