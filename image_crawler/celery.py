import os
import time
import pymysql
from django.conf import settings
from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'image_crawler.settings')
app = Celery('image_crawler')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task
def db_backup():
    TIMESTAMP = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    conn = pymysql.connect(
        settings.DATABASES['default']['HOST'],
        settings.DATABASES['default']['USER'],
        settings.DATABASES['default']['PASSWORD'],
        settings.DATABASES['default']['NAME']
    )
    cur = conn.cursor()
    cmd = 'docker exec -i 0355 mysqldump -u{} -p{} {} > {}'
    os.system(cmd.format(
        settings.DATABASES['default']['USER'],
        settings.DATABASES['default']['PASSWORD'],
        settings.DATABASES['default']['NAME'],
        os.path.join(settings.DB_BACKUP_DIR, f'bak_{TIMESTAMP}.sql'),

    ))
    conn.close()
