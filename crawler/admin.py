from django.contrib import admin

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


# TODO: 图片批量导出
@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display_links = ['md5']
    list_display = ['md5', 'keyword', 'download_time', 'status']
    list_filter = ('keyword', 'status')

    def download_time(self, instance):
        if not instance.task:
            return None
        else:
            return Task.objects.get(id=instance.task.id).start_time

    download_time.short_description = '下载时间'


# TODO: 批量生成任务
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'keyword', 'scanned_images_count', 'images_count', 'download_rate', 'start_time', 'end_time')
    list_display_links = ('id',)
    date_hierarchy = 'start_time'
    fields = ['keyword']

    def images_count(self, obj):
        return len(Image.objects.filter(task=obj.id))

    images_count.short_description = '图片下载数量'

    def download_rate(self, obj):
        if obj.scanned_images_count:
            return '{:.2%}'.format(len(Image.objects.filter(task=obj.id)) / obj.scanned_images_count)

    download_rate.short_description = '下载率'

    def save_model(self, request, obj, form, change):
        obj.save()
        crawl_image.delay(obj.keyword.name, obj.id)
        super().save_model(request, obj, form, change)


admin.site.site_header = '图片搜集管理平台'
admin.site.site_title = '图片搜集管理平台'
admin.site.index_title = '管理首页'
