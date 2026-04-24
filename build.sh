#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
cd src
python manage.py collectstatic --noinput
