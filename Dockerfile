FROM ubuntu:xenial

MAINTAINER OPS <ops@nelen-schuurmans.nl>

# Change the date to force rebuilding the whole image
ENV REFRESHED_AT 20160531

# system dependencies
RUN apt-get update && apt-get install -y \
    python-software-properties \
    wget \
    build-essential \
    git \
    libevent-dev \
    libfreetype6-dev \
    libpng12-dev \
    python3-dev \
    python3-pip \
    python3-psycopg2 \
    gettext \
    postgresql-client \
&& apt-get clean -y && rm -rf /var/lib/apt/lists/*

RUN pip3 install -U zc.buildout setuptools

VOLUME /code
WORKDIR /code
