import os
import imghdr
import time
import hashlib
import traceback
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from concurrent.futures import ThreadPoolExecutor

from crawler.models import Image, Task


MAX_THREAD = 4
DST_DIR = '/Users/xie/Downloads/data'
DRIVER = '/Users/xie/code/image_crawler/utils/geckodriver'
PROXY = 'https://xgjpac.com/houxudonggis/5300657.pac'


class GoogleCrawler:
    def __init__(self, keyword, task_id):
        self.keyword = keyword.lower()
        self.task_id = task_id
        self.dst_dir = os.path.join(DST_DIR, self.keyword)
        os.makedirs(self.dst_dir, exist_ok=True)

        self.browser = self.get_browser()

    @staticmethod
    def get_browser():
        profile = webdriver.FirefoxProfile()
        profile.set_preference("network.proxy.type", 2)
        profile.set_preference('network.proxy.autoconfig_url', PROXY)

        options = Options()
        options.headless = True

        return webdriver.Firefox(executable_path=DRIVER, firefox_profile=profile, options=options)

    @staticmethod
    def scorll_to_element_by_js(browser, tag):
        js = "arguments[0].scrollIntoView();"
        browser.execute_script(js, tag)

    def get_screenshot(self, src):
        try:
            browser = self.get_browser()
            browser.get(src)
            img = browser.find_element_by_tag_name('img').screenshot_as_png

            md5_filename = hashlib.md5(img).hexdigest()
            postfix = imghdr.what(None, img)
            file_path = os.path.join(self.dst_dir, f'{md5_filename}.{postfix}')

            with open(file_path, 'wb') as f:
                f.write(img)
            browser.quit()

            if not Image.objects.filter(md5=md5_filename):
                Image(
                    url=src if src.startswith('http') and len(src) <= 128 else None,
                    file_path=file_path,
                    md5=md5_filename,
                    task=Task.objects.get(id=self.task_id)
                ).save()
        except Exception:
            print(traceback.print_exc())

    def start_crawl(self):
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
        pool = ThreadPoolExecutor(MAX_THREAD)
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
        self.browser.quit()
