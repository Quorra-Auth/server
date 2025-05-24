FROM docker.io/library/python:latest

COPY . /src
RUN pip install /src
ENTRYPOINT ["quorra-server"]