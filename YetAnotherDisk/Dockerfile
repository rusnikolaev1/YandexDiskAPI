###########
# BUILDER #
###########

FROM python:3.10.3-alpine as builder

WORKDIR /usr/src/diskapi

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install psycopg2 dependencies
RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev

RUN pip install --upgrade pip

COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/diskapi/wheels -r requirements.txt

#########
# FINAL #
#########

FROM python:3.10.3-alpine

RUN mkdir -p /home/diskapi
# create the diskapi user
RUN addgroup -S diskapi && adduser -S diskapi -G diskapi

# create the appropriate directories
ENV HOME=/home/diskapi
ENV APP_HOME=/home/diskapi/web
RUN mkdir $APP_HOME
WORKDIR $APP_HOME

# install dependencies
RUN apk update && apk add libpq
COPY --from=builder /usr/src/diskapi/wheels /wheels
COPY --from=builder /usr/src/diskapi/requirements.txt .
RUN pip install --no-cache /wheels/*

# copy project
COPY . $APP_HOME

RUN chown -R diskapi:diskapi $APP_HOME

# change to the diskapi user
USER diskapi

LABEL author='rusnikolaev1@gmail.ru' version=1 