import os
from django.contrib import admin
from django.conf import settings

from .models import Image, Keyword, Task, Crawler
from .tasks import crawl_image


# class ImageInline(admin.TabularInline):
#     model = Image
#     readonly_fields = ('url', 'file_path', 'md5')


@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    list_display = ['name', 'images_count']
    actions = ['refresh_images']

    @staticmethod
    def images_count(obj):
        return len(Image.objects.filter(keyword=obj.id))

    def changelist_view(self, request, extra_context=None):
        if 'action' in request.POST and request.POST['action'] == 'refresh_images':
            if not request.POST.getlist(admin.ACTION_CHECKBOX_NAME):
                post = request.POST.copy()
                for u in Keyword.objects.all():
                    post.update({admin.ACTION_CHECKBOX_NAME: str(u.id)})
                request._set_post(post)
        return super(KeywordAdmin, self).changelist_view(request, extra_context)

    def refresh_images(self, request, queryset):
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

    refresh_images.short_description = '更新图片库'


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('md5', 'keyword', 'url', 'task')
    list_filter = ('keyword',)

    @staticmethod
    def keyword(instance):
        return instance.task.keyword


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'keyword', 'time', 'images_count')
    list_display_links = ('time',)
    # inlines = [ImageInline]

    @staticmethod
    def images_count(obj):
        return len(Image.objects.filter(task=obj.id))

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
