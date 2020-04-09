import os
import imghdr
import hashlib
from django.utils.html import mark_safe
from django.db import models


# TODO: 优化celery进程协程线程
class Image(models.Model):
    id = models.AutoField(primary_key=True)
    url = models.CharField(max_length=128, null=True, blank=True)
    md5 = models.CharField(verbose_name='MD5', max_length=32, unique=True)
    task = models.ForeignKey('Task', verbose_name='任务', related_name='images', on_delete=models.PROTECT, null=True,
                             blank=True)
    keyword = models.ForeignKey('Keyword', verbose_name='关键字', related_name='images', on_delete=models.PROTECT)
    status = models.BooleanField(verbose_name='筛选状态', null=True, blank=True)
    image_file = models.ImageField(verbose_name='图片', upload_to='images/')

    class Meta:
        verbose_name = '图片'
        verbose_name_plural = '图片'

    def __str__(self):
        return str(self.id)

    def delete(self, using=None, keep_parents=False):
        self.image_file.delete(self.image_file.name)
        super().delete()

    def image_element(self, height=250):
        return mark_safe(f'<img src="{self.image_file.url}" height="{height}" />')

    def image_icon(self):
        return self.image_element(50)


# TODO: 化石演化树
class Keyword(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(verbose_name='关键字', max_length=128, null=False, blank=False, unique=True)

    class Meta:
        verbose_name = '关键字'
        verbose_name_plural = '关键字'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super(Keyword, self).save()


class Task(models.Model):
    id = models.AutoField(primary_key=True)
    start_time = models.DateTimeField(verbose_name='开始时间', auto_now_add=True)
    end_time = models.DateTimeField(verbose_name='结束时间', null=True, blank=True)
    keyword = models.ForeignKey('Keyword', verbose_name='关键字', related_name='tasks', on_delete=models.PROTECT)
    scanned_images_count = models.IntegerField(verbose_name='图片扫描数量', null=True, blank=True)

    class Meta:
        verbose_name = '任务'
        verbose_name_plural = '任务'

    def __str__(self):
        return str(self.id)
