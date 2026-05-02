#!/usr/bin/env bash
set -o errexit

cd src
python3 manage.py migrate --noinput
gunicorn cfehome.wsgi:application --bind 0.0.0.0:${PORT:-10000} --log-file -
