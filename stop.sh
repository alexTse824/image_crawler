#! /bin/bash

SHELL_FOLDER=$(dirname "$0")
cd $SHELL_FOLDER

kill `cat $SHELL_FOLDER/gunicorn.pid`
echo gunicorn processes killed...

ps auxww | grep 'image_crawler worker' | awk '{print $2}' | xargs kill -9
echo celery processes killed...