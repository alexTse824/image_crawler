import os
from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'image_crawler.settings')
app = Celery('image_crawler')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()