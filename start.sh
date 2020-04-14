#! /bin/bash

SHELL_FOLDER=$(dirname "$0")
cd $SHELL_FOLDER

source $SHELL_FOLDER'/venv/bin/activate'

nohup gunicorn -c gunicorn.conf.py image_crawler.wsgi >/dev/null 2>&1 &
echo gunicorn initialized...

nohup celery -A image_crawler worker -l info --beat --scheduler django_celery_beat.schedulers:DatabaseScheduler >/dev/null 2>&1 &
echo celery initialized...