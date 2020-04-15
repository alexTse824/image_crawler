import os
import time
import logging
import configparser
from django.conf import settings
from celery import Celery
from celery.signals import after_setup_logger

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'image_crawler.settings')

config = configparser.ConfigParser()
config.read(settings.CONFIG_FILE)

app = Celery('image_crawler')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@after_setup_logger.connect
def setup_loggers(logger, *args, **kwargs):
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s][%(module)s]%(message)s')

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(os.path.join(settings.BASE_DIR, 'log', 'celery.log'))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


@app.task
def db_backup():
    TIMESTAMP = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    cmd = 'echo {} | sudo -S docker exec -i mysql mysqldump -u{} -p{} {} > {}'
    os.system(cmd.format(
        config.get('celery', 'sudo_password'),
        settings.DATABASES['default']['USER'],
        settings.DATABASES['default']['PASSWORD'],
        settings.DATABASES['default']['NAME'],
        os.path.join(settings.DB_BACKUP_DIR, f'bak_{TIMESTAMP}.sql'),

    ))
