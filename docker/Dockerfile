FROM alpine:3.8
LABEL maintainer="dek@iono.me"

ARG git_branch=v0.1-rc1

RUN mkdir /synapse-room-logger
WORKDIR /synapse-room-logger
RUN apk update &&\
    apk add python3 python3-dev git postgresql-dev build-base gcc&&\
    pip3 install pipenv &&\
    git clone -b ${git_branch} https://github.com/dekonnection/synapse-room-logger.git /synapse-room-logger &&\
    apk del git &&\
    pipenv install --system --deploy &&\
    adduser -D srl &&\
    chown -R srl: /synapse-room-logger &&\
    apk del python3-dev git build-base gcc &&\
    rm -rf /var/cache/apk

COPY start.sh /start.sh
USER srl
ENTRYPOINT ["/start.sh"]
