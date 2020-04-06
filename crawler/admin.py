import os
from django.contrib import admin
from django.conf import settings

from .models import Image, Keyword, Task
from .tasks import crawl_image, refresh_image_library


@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    list_display = ['name', 'images_count']
    actions = ['refresh_images']
    search_fields = ['name']

    def images_count(self, obj):
        return len(Image.objects.filter(keyword=obj.id))

    images_count.short_description = '图片数量'

    def changelist_view(self, request, extra_context=None):
        if 'action' in request.POST and request.POST['action'] == 'refresh_images':
            if not request.POST.getlist(admin.ACTION_CHECKBOX_NAME):
                post = request.POST.copy()
                for u in Keyword.objects.all():
                    post.update({admin.ACTION_CHECKBOX_NAME: str(u.id)})
                request._set_post(post)
        return super(KeywordAdmin, self).changelist_view(request, extra_context)

    def refresh_images(self, request, queryset):
        refresh_image_library.delay()

    refresh_images.short_description = '更新图片库'


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display_links = ['md5']
    list_display = ['md5', 'keyword', 'download_time', 'status']
    list_filter = ('keyword', 'status')

    def download_time(self, instance):
        if not instance.task:
            return None
        else:
            return instance.task.time

    download_time.short_description = '下载时间'


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'keyword', 'time', 'images_count')
    list_display_links = ('time',)
    date_hierarchy = 'time'

    def images_count(self, obj):
        return len(Image.objects.filter(task=obj.id))

    images_count.short_description = '图片数量'

    def save_model(self, request, obj, form, change):
        obj.save()
        crawl_image.delay(str(obj.keyword), obj.id)
        super().save_model(request, obj, form, change)


admin.site.site_header = '图片搜集管理平台'
admin.site.site_title = '图片搜集管理平台'
admin.site.index_title = '管理首页'
