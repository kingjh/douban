#!/usr/bin/env python
# encoding: utf-8
"""
@author: chenchuan@autohome.com.cn
@time: 2017/03/13
"""
import random
import string

import scrapy
import requests
import urllib.request
import time
from scrapy.http import Request
from scrapy.selector import Selector
from scrapy.spiders import Spider
from douban.items import DoubanItem

domain = 'https://movie.douban.com'


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False


def complete_url(_url):
    if not _url.startswith('http', 0, 4):
        _url = domain + _url
    return _url


class DoubanSpider(Spider):
    name = 'douban_spider'
    website_possible_httpstatus_list = [200]
    # 已经抓取的item不会重新抓取，故把电影和电视剧摆在最前
    tags = [u'电视剧', u'电影', u'爱情', u'喜剧', u'动画', u'剧情', u'科幻', u'动作', u'经典', u'悬疑', u'青春',
            u'犯罪', u'惊悚', u'文艺', u'搞笑', u'纪录片', u'励志', u'恐怖', u'战争', u'短片',
            u'黑色幽默', u'魔幻', u'传记', u'情色', u'感人', u'暴力', u'动画短片', u'家庭', u'音乐',
            u'童年', u'浪漫', u'黑帮', u'女性', u'同志', u'史诗', u'童话', u'烂片', u'cult', u'脱口秀']
    # tags = [u'电视剧', u'电影']

    def start_requests(self):
        """
        爬取标签列表页信息
        """
        tags = self.tags
        for tag in tags:
            url = complete_url("/tag/{}".format(urllib.request.quote(tag)))
            print("start_requests")
            yield Request(url=url, callback=self.parse_page, meta={"tag": tag, "check_total": True})

    def parse_page(self, response):
        print("parse_page")
        """
        爬取某标签电影分页信息
        """
        hxs = Selector(response)
        total = hxs.xpath('//*[@id="content"]/div/div[1]/div[3]/a[10]/text()').extract()[0]
        tag = response.meta["tag"]
        encoded_tag = format(tag)
        for i in range(int(total)):
            url = complete_url('/tag/{0}?start={1}&type=T'.format(encoded_tag, i * 20))
            yield Request(url=url, callback=self.parse_items, meta={"tag": tag, "check_total": True})

    # 电影详情
    def parse_items(self, response):
        print("parse_items")
        """
        爬取电影链接
        """
        tag = response.meta["tag"]
        type = 0
        # 若“电视剧”、“电影”存在于类型字符串，设定类型
        if tag == "电影":
            type = 1
        elif tag == "电视剧":
            type = 2
        try:
            hxs = Selector(response)
            texts = hxs.xpath('//div[contains(@class,"grid-16-8 clearfix")]/div[1]/div[2]/table')
            for text in texts:
                title = text.xpath('tr/td[2]/div/a/text()').extract()
                title = title[0].strip().replace('\n', "").replace(' ', "").replace('/', "") if title else ''
                score = text.xpath('tr/td[2]/div/div/span[2]/text()').extract()
                if score:
                    score = score[0].replace("'", "")
                    if not is_number(score):
                        score = 0
                else:
                    score = 0
                num = text.xpath('tr/td[2]/div/div/span[3]/text()').extract()
                if num:
                    num = num[0].replace('(', "").replace('人评价)', "")
                    if not is_number(num):
                        num = 0
                else:
                    num = 0
                url = text.xpath('tr/td/a/@href').extract()[0]
                yield Request(url=url, callback=self.parse_item, meta={"check_director": True, "type": type,
                                                                       "title": title,
                                                                       "score": score, "num": num,
                                                                       "url": url})
        except Exception as e:
            print(e)
            pass

    def parse_item(self, response):
        print("parse_item")
        """
        爬取电影信息
        """
        type = response.meta["type"]
        item = DoubanItem()
        directors = ''
        screenwriters = ''
        tags = ''
        actors = ''
        country = ''
        language = ''
        time = ''
        length = ''
        alias = ''
        try:
            title = response.meta["title"]
            score = response.meta["score"]
            num = response.meta["num"]
            url = response.meta["url"]
            hxs = Selector(response)
            # 存储非导演、编剧、主演的属性由哪行开始
            flex_start_row_idx = 3
            try:
                for i in range(3):
                    temp_attr = hxs.xpath('//*[@id="info"]/span[%s]/span[1]/text()' % (i + 1)).extract()[0]
                    if temp_attr == '导演':
                        director_list = hxs.xpath('//*[@id="info"]/span[%s]/span[2]/a/text()' % (i + 1)).extract()
                        directors = ''
                        for director_item in director_list:
                            directors += '/' + director_item

                        directors = directors if directors != '' else '/'
                        directors = directors.split('/', 1)[1]
                    elif temp_attr == '编剧':
                        screenwriter_list = hxs.xpath('//*[@id="info"]/span[%s]/span[2]/a/text()' % (i + 1)).extract()
                        screenwriters = ''
                        for screenwriter_item in screenwriter_list:
                            screenwriters += '/' + screenwriter_item

                        screenwriters = screenwriters if screenwriters != '' else '/'
                        screenwriters = screenwriters.split('/', 1)[1]
                    elif temp_attr == '主演':
                        actor_list = hxs.xpath('//*[@id="info"]/span[%s]/span[2]/a/text()' % (i + 1)).extract()
                        actors = ''
                        for actor_item in actor_list:
                            actors += '/' + actor_item

                        actors = actors if actors != '' else '/'
                        actors = actors.split('/', 1)[1]
                    else:
                        # 非导演、编剧、主演，存储并跳出循环
                        flex_start_row_idx = i
                        break
            except Exception as e:
                print(e)
                # 非导演、编剧、主演，存储并跳出循环
                flex_start_row_idx = i
                pass

            prev_attr_name = ''
            attr = ''
            last_attr = False
            for i in range(flex_start_row_idx, 30):
                try:
                    temp_attr = hxs.xpath('//*[@id="info"]/span[%s]/text()' % (i + 1)).extract()[0]
                    if temp_attr.find(':') != -1:
                        attr = attr if attr != '' else '/'
                        if prev_attr_name == '类型':
                            tags = attr.split('/', 1)[1]
                        elif prev_attr_name == '制片国家/地区':
                            # country = attr.split('/', 1)[1]
                            print(111)
                        elif prev_attr_name == '语言':
                            # language = attr.split('/', 1)[1]
                            print(222)
                        elif prev_attr_name == '上映日期':
                            time = attr.split('/', 1)[1]
                        elif prev_attr_name == '片长':
                            length = attr.split('/', 1)[1]
                        elif prev_attr_name == '又名':
                            # alias = attr.split('/', 1)[1]
                            print(333)
                            last_attr = True
                        prev_attr_name = temp_attr.split(':', 1)[0]
                        attr = ''
                    else:
                        attr += '/' + temp_attr
                except Exception as e:
                    print(e)
                    break

                if last_attr:
                    break

            item['film_id'] = url.split('/')[-2]
            item['title'] = title
            item['score'] = score
            item['num'] = num
            item['link'] = url
            item['type'] = type
            item['directors'] = directors
            item['screenwriters'] = screenwriters
            item['actors'] = actors
            item['tags'] = tags
            item['time'] = time
            item['length'] = length
            yield item

        except Exception as e:
            print(e)
            pass
