from celery import shared_task

from utils.google_crawler import GoogleCrawler


@shared_task
def crawl_image(keyword, task_id):
    print(f'Start Crawling "{keyword}"')
    crawler = GoogleCrawler(keyword, task_id)
    crawler.start_crawl()