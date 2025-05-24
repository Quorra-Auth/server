FROM docker.io/library/python:latest
LABEL org.opencontainers.image.source=https://github.com/Quorra-Auth/server

COPY . /src
RUN pip install /src
HEALTHCHECK CMD curl -f http://localhost:8080/health || exit 1
ENTRYPOINT ["quorra-server"]