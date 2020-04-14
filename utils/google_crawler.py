import os
import time
import traceback
import configparser
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from concurrent.futures import ThreadPoolExecutor
from django.core.files.base import ContentFile
from django.conf import settings

from crawler.models import Image, Keyword, Task
from utils.utils import get_file_md5_postfix

config = configparser.ConfigParser()
config.read(settings.CONFIG_FILE)


class GoogleCrawler:
    def __init__(self, keyword, task_id):
        self.keyword = keyword.lower()
        self.task_id = task_id
        self.browser = self.get_browser()

    @staticmethod
    def get_browser():
        profile = webdriver.FirefoxProfile()
        profile.set_preference("network.proxy.type", 2)
        profile.set_preference('network.proxy.autoconfig_url', config.get('crawler', 'pac_url'))

        options = Options()
        options.headless = True

        return webdriver.Firefox(
            executable_path=settings.WEBDRIVER_PATH,
            firefox_profile=profile,
            log_path=os.path.join(settings.BASE_DIR, 'log', 'geckodriver.log'),
            options=options
        )

    @staticmethod
    def scorll_to_element_by_js(browser, tag):
        js = "arguments[0].scrollIntoView();"
        browser.execute_script(js, tag)

    # TODO: 降低图片下载等待延时
    def get_screenshot(self, src):
        try:
            browser = self.get_browser()
            browser.get(src)
            img = browser.find_element_by_tag_name('img').screenshot_as_png

            md5_filename, postfix = get_file_md5_postfix(img)

            if not Image.objects.filter(md5=md5_filename):
                img_obj = Image(
                    url=src if src.startswith('http') and len(src) <= 128 else None,
                    md5=md5_filename,
                    task=Task.objects.get(id=self.task_id),
                    keyword=Keyword.objects.get(name=self.keyword)
                )
                img_obj.image_file.save(f'{md5_filename}.{postfix}', ContentFile(img))
        except Exception:
            print(traceback.print_exc())
        finally:
            browser.quit()

    def start_crawl(self):
        try:
            url = 'https://www.google.com/search?q={}&tbm=isch'.format(self.keyword)
            self.browser.get(url)

            more_result_btn_xpath = '//input[@value="显示更多搜索结果"]'
            scroll_flag = 0
            last_scroll_distance = 0
            while scroll_flag <= 10:
                self.browser.execute_script("window.scrollTo(0,document.body.scrollHeight)")
                scroll_distance = self.browser.execute_script('return window.pageYOffset;')
                if scroll_distance == last_scroll_distance:
                    more_result_btn = self.browser.find_element_by_xpath(more_result_btn_xpath)
                    try:
                        more_result_btn.click()
                        continue
                    except Exception:
                        scroll_flag += 1
                        time.sleep(1)
                else:
                    time.sleep(.2)
                    last_scroll_distance = scroll_distance
                    scroll_flag = 0

            ele_list = self.browser.find_elements_by_class_name('rg_i')
            print(f'Scanned {len(ele_list)} {self.keyword} images.')
            task_obj = Task.objects.get(id=self.task_id)
            task_obj.scanned_images_count = len(ele_list)
            task_obj.save()

            pool = ThreadPoolExecutor(config.getint('crawler', 'threads'))
            for element in ele_list:
                self.scorll_to_element_by_js(self.browser, element)
                webdriver.ActionChains(self.browser).move_to_element(element).click(element).perform()
                time.sleep(2)
                thumbnail_label = element.get_attribute('alt')
                for detail_element in self.browser.find_elements_by_class_name('n3VNCb'):
                    if detail_element.get_attribute('alt') == thumbnail_label:
                        src = detail_element.get_attribute('src')
                        pool.submit(self.get_screenshot, src)
            pool.shutdown(wait=True)
        except Exception:
            print(traceback.print_exc())
        finally:
            self.browser.quit()
