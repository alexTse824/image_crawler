import os
import imghdr
import hashlib
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
def delete_redundant_files():
    print('Start refresh image library')
    IMAGES_ROOT = os.path.join(settings.MEDIA_ROOT, 'images')

    # 删除库中文件夹或非图像文件
    for filename in os.listdir(IMAGES_ROOT):
        path = os.path.join(IMAGES_ROOT, filename)

        if os.path.isdir(path) or not imghdr.what(path):
            print(f'Invalid item for image library: {path}')
            os.remove(path)
            continue

        # 图片路径在数据库中未找到
        file_relative_path = f'images/{filename}'
        if not Image.objects.filter(image_file=file_relative_path):
            print(f'File not found in database: {path}')
            os.remove(path)

    # 数据库校验文件库
    for obj in Image.objects.all():
        if not os.path.exists(obj.image_file.path):
            print(f'Database item not found: {obj.image_file.path}')
            obj.delete()
