FROM python:3.7.1-alpine3.8
LABEL maintainer="dek@iono.me"

ARG git_branch=v0.1-rc1

RUN mkdir /synapse-room-logger
WORKDIR /synapse-room-logger
RUN apk update &&\
    apk add git postgresql-dev build-base gcc&&\
    pip install pipenv &&\
    git clone -b ${git_branch} https://github.com/dekonnection/synapse-room-logger.git /synapse-room-logger &&\
    pipenv install --system --deploy &&\
    adduser -D srl &&\
    chown -R srl: /synapse-room-logger &&\
    apk del git build-base gcc &&\
    rm -rf /var/cache/apk

COPY start.sh /start.sh
USER srl
ENTRYPOINT ["/start.sh"]
