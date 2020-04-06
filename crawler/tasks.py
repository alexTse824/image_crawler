import os
from django.conf import settings
from celery import shared_task

from .models import Keyword, Image
from utils.google_crawler import GoogleCrawler


@shared_task
def crawl_image(keyword, task_id):
    print(f'Start Crawling "{keyword}"')
    crawler = GoogleCrawler(keyword, task_id)
    crawler.start_crawl()


@shared_task
def refresh_image_library():
    print('Start refresh image library')
    for keyword in os.listdir(settings.DATA_DIR):
        dir_path = os.path.join(settings.DATA_DIR, keyword)
        if not os.path.isdir(dir_path):
            continue
        elif not Keyword.objects.filter(name=keyword.lower()):
            keyword_obj = Keyword(name=keyword.lower())
            keyword_obj.save()

        for filename in os.listdir(dir_path):
            file_path = os.path.join(dir_path, filename)
            Image.import_exist_file(file_path, keyword_obj)