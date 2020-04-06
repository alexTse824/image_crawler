import os
from datetime import datetime
from django.conf import settings
from celery import shared_task

from .models import Keyword, Image, Task
from utils.google_crawler import GoogleCrawler


@shared_task
def crawl_image(keyword, task_id):
    print(f'Start Crawling "{keyword}"')
    crawler = GoogleCrawler(keyword, task_id)
    crawler.start_crawl()
    task_obj = Task.objects.get(id=task_id)
    task_obj.end_time = datetime.now()
    task_obj.save()


# TODO: 更新图片库后台状态显示
# TODO: 关键字更新，关键字图库更新分部进行
@shared_task
def refresh_image_library():
    print('Start refresh image library')
    for keyword in os.listdir(settings.DATA_DIR):
        dir_path = os.path.join(settings.DATA_DIR, keyword)
        if not os.path.isdir(dir_path):
            continue

        try:
            keyword_obj = Keyword.objects.get(name=keyword.lower())
        except Exception:
            keyword_obj = Keyword(name=keyword.lower())
            keyword_obj.save()

        for filename in os.listdir(dir_path):
            file_path = os.path.join(dir_path, filename)
            Image.import_exist_file(file_path, keyword_obj)

    for obj in Image.objects.all():
        if not os.path.exists(obj.file_path):
            obj.delete()
