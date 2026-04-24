#!/usr/bin/env bash
set -o errexit

cd src
python manage.py migrate --noinput
gunicorn cfehome.wsgi:application --log-file -
