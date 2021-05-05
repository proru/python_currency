FROM python:3.9.2-slim-buster

ARG DEBUG=1
ARG PERIOD=60
ARG NEXT_PARAMS="--usd 10 --rub 20 --eur 30"

ENV DEBUG=${DEBUG}
ENV PERIOD=${PERIOD}
ENV NEXT_PARAMS=${NEXT_PARAMS}

WORKDIR app
COPY . /app

RUN pip install -U wheel
RUN pip install  -U setuptools
RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

#ENTRYPOINT ["/usr/bin/tini", "--"]
EXPOSE 8080
CMD ["sh", "-c", "python3 rest_framework.py --debug ${DEBUG} --period ${PERIOD} $NEXT_PARAMS "]