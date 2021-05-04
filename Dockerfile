FROM python:3.9.2-slim-buster

WORKDIR app
COPY . /app

RUN pip install -U wheel
RUN pip install  -U setuptools
RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

#ENTRYPOINT ["/usr/bin/tini", "--"]
EXPOSE 8080
CMD ["sh", "-c", "python3 rest_framework.py --debug 1 --usd 10 --rub 20 --eur 30 --period 60"]