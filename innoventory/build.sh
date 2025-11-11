#!/usr/bin/env bash

set -e

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py makemigrations --merge
python manage.py migrate
