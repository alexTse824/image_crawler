import os
from django.http import FileResponse
from django.contrib import admin, messages
from django.contrib.admin.views.main import ChangeList
from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.shortcuts import render, HttpResponseRedirect
from django.core.files.base import ContentFile

from .models import Image, Keyword, Task, Spider
from .tasks import crawl_image, delete_redundant_files
from .forms import SelectFilesForm
from utils.utils import zip_files, get_file_md5_postfix


class InlineChangeList:
    can_show_all = True
    multi_page = True
    get_query_string = ChangeList.__dict__['get_query_string']

    def __init__(self, request, page_num, paginator):
        self.show_all = 'all' in request.GET
        self.page_num = page_num
        self.paginator = paginator
        self.result_count = paginator.count
        self.params = dict(request.GET.items())


class PaginationInline(admin.TabularInline):
    template = 'admin/edit_inline/tabular_paginated.html'
    per_page = 10

    def get_formset(self, request, obj=None, **kwargs):
        formset_class = super(PaginationInline, self).get_formset(
            request, obj, **kwargs)

        class PaginationFormSet(formset_class):
            def __init__(self, *args, **kwargs):
                super(PaginationFormSet, self).__init__(*args, **kwargs)

                qs = self.queryset
                paginator = Paginator(qs, self.per_page)
                try:
                    page_num = int(request.GET.get('p', '0'))
                except ValueError:
                    page_num = 0

                try:
                    page = paginator.page(page_num + 1)
                except (EmptyPage, InvalidPage):
                    page = paginator.page(paginator.num_pages)

                self.cl = InlineChangeList(request, page_num, paginator)
                self.paginator = paginator

                if self.cl.show_all:
                    self._queryset = qs
                else:
                    self._queryset = page.object_list

        PaginationFormSet.per_page = self.per_page
        return PaginationFormSet


class ImageInline(PaginationInline):
    model = Image
    fields = ['md5', 'keyword', 'task', 'status']
    readonly_fields = ['md5', 'keyword', 'task', 'status']
    extra = 0
    list_per_page = 10


class BlankCheckboxModelAdmin(admin.ModelAdmin):
    registered_actions = [
        'delete_redundant_files_action',
        'batch_insert_keywords_action',
    ]

    def changelist_view(self, request, extra_context=None):
        if 'action' in request.POST and request.POST['action'] in self.registered_actions:
            if not request.POST.getlist(admin.ACTION_CHECKBOX_NAME):
                post = request.POST.copy()
                for u in Keyword.objects.all():
                    post.update({admin.ACTION_CHECKBOX_NAME: str(u.id)})
                request._set_post(post)
        return super(BlankCheckboxModelAdmin, self).changelist_view(request, extra_context)


# TODO: 批量导入关键字
@admin.register(Keyword)
class KeywordAdmin(BlankCheckboxModelAdmin):
    list_display = ['name', 'images_count']
    search_fields = ['name']
    actions = [
        'download_packed_images_action',
        'images_upload_action',
        'batch_generate_tasks_action',
    ]
    inlines = [ImageInline]

    def images_count(self, obj):
        return len(Image.objects.filter(keyword=obj.id))

    images_count.short_description = '图片数量'

    def download_packed_images_action(self, request, queryset):
        filename_dict = {}
        for keyword_obj in queryset:
            img_objs = Image.objects.filter(keyword=keyword_obj)
            filename_dict[keyword_obj.name] = [obj.image_file.name for obj in img_objs]
        zip_path = zip_files(filename_dict)
        response = FileResponse(open(zip_path, 'rb'))
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = f'attachment;filename="{os.path.split(zip_path)[-1]}"'
        return response

    download_packed_images_action.short_description = '下载所选关键字图片库'

    def batch_generate_tasks_action(self, request, queryset):
        for keyword_obj in queryset:
            task_obj = Task(keyword=keyword_obj)
            task_obj.save()
            crawl_image.delay(task_obj.keyword.name, task_obj.id)
        return HttpResponseRedirect('/admin/crawler/task/')

    batch_generate_tasks_action.short_description = '批量生成所选关键字任务'

    # TODO: 将批量上传转为celery任务
    # TODO: 文件选择后显示文件列表，save后二次确认页面
    def images_upload_action(self, request, queryset):
        if len(queryset) > 1:
            messages.error(request, '不能上传同时至多个图片库')
        else:
            form = None
            if 'apply' in request.POST:
                form = SelectFilesForm(request.POST, request.FILES)
                files = request.FILES.getlist('file_field')
                if form.is_valid():
                    keyword = request.POST['keyword']
                    for file in files:
                        file_content = file.read()
                        md5_filename, postfix = get_file_md5_postfix(file_content)
                        if not Image.objects.filter(md5=md5_filename):
                            img_obj = Image(
                                md5=md5_filename,
                                keyword=Keyword.objects.get(name=keyword)
                            )
                            img_obj.image_file.save(f'{md5_filename}.{postfix}', ContentFile(file_content))
                return HttpResponseRedirect(request.get_full_path())

            if not form:
                form = SelectFilesForm(initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
            return render(request, 'select_file.html', {'keyword': queryset[0].name, 'form': form, 'title': '上传本地图片'})

    images_upload_action.short_description = '批量上传图片至图片库'


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display_links = ['md5']
    list_display = ['md5', 'keyword', 'download_time', 'status']
    list_filter = ('keyword', 'status')
    readonly_fields = ['image_element']
    actions = ['delete_redundant_files_action']
    list_per_page = 20

    def download_time(self, instance):
        if not instance.task:
            return None
        else:
            return Task.objects.get(id=instance.task.id).start_time

    download_time.short_description = '下载时间'

    def delete_redundant_files_action(self, request, queryset):
        delete_redundant_files.delay()

    delete_redundant_files_action.short_description = '删除图片库冗余文件'


# TODO: Task save 生成任务机制优化，通过model.save()实现
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'keyword', 'spider', 'scanned_images_count', 'images_count', 'download_rate', 'start_time', 'end_time')
    list_display_links = ('id',)
    date_hierarchy = 'start_time'
    fields = ['keyword', 'spider']

    def images_count(self, obj):
        return len(Image.objects.filter(task=obj.id))

    images_count.short_description = '图片下载数量'

    def download_rate(self, obj):
        if obj.scanned_images_count:
            return '{:.2%}'.format(len(Image.objects.filter(task=obj.id)) / obj.scanned_images_count)

    download_rate.short_description = '下载率'

    def save_model(self, request, obj, form, change):
        # 新增task_obj保存前无id, 修改task_obj是id已存在, 用以判断是否执行任务
        execute_flag = True if obj.id else False
        obj.save()
        if execute_flag:
            crawl_image.delay(obj.keyword.name, obj.id)
        super().save_model(request, obj, form, change)


@admin.register(Spider)
class SpiderAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    list_display_links = ['id', 'name']


admin.site.site_header = '图片搜集管理平台'
admin.site.site_title = '图片搜集管理平台'
admin.site.index_title = '管理首页'
