FROM docker.io/library/python:latest

COPY . /src
RUN pip install /src
HEALTHCHECK CMD curl -f http://localhost:8080/health || exit 1
ENTRYPOINT ["quorra-server"]