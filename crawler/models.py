from django.db import models


class Image(models.Model):
    id = models.AutoField(primary_key=True)
    url = models.CharField(max_length=128, null=True, blank=True)
    file_path = models.CharField(max_length=128)
    md5 = models.CharField(max_length=32, unique=True)
    task = models.ForeignKey('Task', related_name='images', on_delete=models.PROTECT)

    def __str__(self):
        return str(self.id)


class Keyword(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=128, null=False, blank=False, unique=True)

    def __str__(self):
        return self.name


class Task(models.Model):
    id = models.AutoField(primary_key=True)
    time = models.DateTimeField(auto_now_add=True)
    keyword = models.ForeignKey('Keyword', related_name='keywords', on_delete=models.PROTECT)

    def __str__(self):
        return str(self.id)


class Crawler(models.Model):
    ip = models.CharField(max_length=16)
    status = models.BooleanField()
    browser_version = models.CharField(max_length=32)
    driver_version = models.CharField(max_length=32)
