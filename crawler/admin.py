from django.contrib import admin

from .models import Image, Keyword, Task, Crawler
from .tasks import crawl_image


class ImageInline(admin.TabularInline):
    model = Image
    readonly_fields = ('url', 'file_path', 'md5')


@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    fields = ('name',)


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('file_path', 'url', 'md5', 'task' )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'keyword', 'time', 'images_count')
    list_display_links = ('keyword',)
    inlines = [ImageInline]

    @staticmethod
    def images_count(task_id):
        return len(Image.objects.filter(task_id=task_id))

    def save_model(self, request, obj, form, change):
        obj.save()
        crawl_image.delay(str(obj.keyword), obj.id)
        super().save_model(request, obj, form, change)


@admin.register(Crawler)
class CrawlerAdmin(admin.ModelAdmin):
    list_display = ('ip', 'status', 'browser_version', 'driver_version')


admin.site.site_header = '图片搜集管理平台'
admin.site.site_title = '图片搜集管理平台'
admin.site.index_title = '管理首页'