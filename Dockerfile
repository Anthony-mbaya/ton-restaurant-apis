# Base image tag
FROM python:3.9-alpine3.13
LABEL maintainer="cruxton"
# see logs immediately as running
ENV PYTHONUNBUFFERED 1
# Install dependencies
# copy req from loval machine to /tmp/ req file
COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
# copy our app to /ton-res in the container
COPY ./ton-restaurant /ton-restaurant
# gonna run all cmds from this dir
WORKDIR /ton-restaurant
# expose port from cont to mach - dj dex server
EXPOSE 8000
# override DEV arg - default not running in dev mode
ARG DEV=false
# new venv
# install helper packages of postgres in alpine image
# rm - remove -rf - r# rsively and forceful del
# add user in image
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache postgresql-client && \
    apk add --update --no-cache --virtual .tmp-build-deps \
        build-base postgresql-dev musl-dev && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ $DEV = "true" ]; \
        then /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi && \
    rm -rf /tmp && \
    apk del .tmp-build-deps && \
    adduser \
        --disabled-password \
        --no-create-home \
        django-user

ENV PATH="/py/bin:$PATH"

USER django-user