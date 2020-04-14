import os
import multiprocessing

from image_crawler.settings import BASE_DIR


bind = '0.0.0.0:8000'
backlog = 512
workers = multiprocessing.cpu_count() * 2 + 1
chdir = BASE_DIR

pidfile = os.path.join(BASE_DIR, 'gunicorn.pid')

# log
loglevel = 'info'
accesslog = os.path.join(BASE_DIR, 'log', 'gunicorn.access.log')
errorlog = os.path.join(BASE_DIR, 'log', 'gunicorn.error.log')