#! /bin/sh

SHELL_FOLDER=$(dirname "$0")
cd $SHELL_FOLDER

source $SHELL_FOLDER'/venv/bin/activate'
gunicorn -c gunicorn.conf.py image_crawler.wsgi