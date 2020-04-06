import os
import imghdr
import hashlib
from django.db import models


# TODO: 任务执行结束时间，下载/扫描图片数量，任务执行状态
class Image(models.Model):
    id = models.AutoField(primary_key=True)
    url = models.CharField(max_length=128, null=True, blank=True)
    file_path = models.CharField(verbose_name='图片路径', max_length=128)
    md5 = models.CharField(verbose_name='MD5', max_length=32, unique=True)
    task = models.ForeignKey('Task', verbose_name='任务', related_name='images', on_delete=models.PROTECT, null=True,
                             blank=True)
    keyword = models.ForeignKey('Keyword', verbose_name='关键字', related_name='images', on_delete=models.PROTECT)
    status = models.BooleanField(verbose_name='筛选状态', null=True, blank=True)

    class Meta:
        verbose_name = '图片'
        verbose_name_plural = '图片'

    def __str__(self):
        return str(self.id)

    @staticmethod
    def import_exist_file(file_path, keyword_obj):
        with open(file_path, 'rb') as f:
            img = f.read()
        md5_filename = hashlib.md5(img).hexdigest()
        postfix = imghdr.what(None, img)

        if not Image.objects.filter(md5=md5_filename):
            dir_path, keyword = os.path.split(file_path)
            md5_file_path = os.path.join(dir_path, f'{md5_filename}.{postfix}')
            os.rename(file_path, md5_file_path)
            Image(file_path=md5_file_path, md5=md5_filename, keyword=keyword_obj).save()


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
    time = models.DateTimeField(verbose_name='开始时间', auto_now_add=True)
    keyword = models.ForeignKey('Keyword', verbose_name='关键字', related_name='tasks', on_delete=models.PROTECT)

    class Meta:
        verbose_name = '任务'
        verbose_name_plural = '任务'

    def __str__(self):
        return str(self.id)
