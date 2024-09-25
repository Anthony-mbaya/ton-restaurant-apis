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
# rm - remove -rf - r# rsively and forceful del
# add user in image
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ $DEV = "true" ]; \
        then /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi && \
    rm -rf /tmp && \
    adduser \
        --disabled-password \
        --no-create-home \
        django-user

ENV PATH="/py/bin:$PATH"

USER django-user