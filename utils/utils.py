import os
import time
import zipfile
import hashlib
import imghdr
from django.conf import settings


def zip_files(file_dict):
    # 使用临时文件下载速度10MB/s, 使用BytesIO下载速度400kb/s
    TIMESTAMP = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    zip_file_path = os.path.join('temp', f'{TIMESTAMP}.zip')
    zip_abs_file_path = os.path.join(settings.MEDIA_ROOT, zip_file_path)
    zf = zipfile.ZipFile(zip_abs_file_path, 'w')

    for keyword, fpaths in file_dict.items():
        print(f'Packing {keyword} images')
        for fpath in fpaths:
            abs_fpath = os.path.join(settings.MEDIA_ROOT, fpath)
            arcname = os.path.join(keyword, os.path.split(fpath)[-1])
            zf.write(abs_fpath, arcname)
    zf.close()
    return zip_abs_file_path


def get_file_md5_postfix(file_content):
    return hashlib.md5(file_content).hexdigest(), imghdr.what(None, file_content)
