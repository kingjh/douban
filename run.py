import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from douban.spiders.spider import DoubanSpider

process = CrawlerProcess(get_project_settings())

process.crawl(DoubanSpider)
process.start()  # the script will block here until the crawling is finished
