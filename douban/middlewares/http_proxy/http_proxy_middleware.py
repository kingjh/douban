#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import logging
import random
import string
from datetime import datetime, timedelta
from twisted.web._newclient import ResponseNeverReceived
from twisted.internet.error import TimeoutError, ConnectionRefusedError, ConnectError
from .proxy_hunter import ProxyHunter
from scrapy.core.downloader.handlers.http11 import TunnelError
from scrapy.selector import Selector
import time

logger = logging.getLogger(__name__)


class HttpProxyMiddleware(object):
    # 遇到这些类型的错误直接当做代理不可用处理掉, 不再传给retrymiddleware
    DONT_RETRY_ERRORS = (TimeoutError, ConnectionRefusedError, ResponseNeverReceived, ConnectError, ValueError, TunnelError)

    def gen_bids(self):
        return "".join(random.sample(string.ascii_letters + string.digits, 11))

    def __init__(self, settings):
        # 保存上次不用代理直接连接的时间点
        self.last_no_proxy_time = datetime.now()
        # 一定分钟数后切换回不用代理, 因为用代理影响到速度
        # 设为10080，即永远使用代理
        self.recover_interval = 10080
        # 一个proxy如果没用到这个数字就被发现老是超时, 则永久移除该proxy. 设为0则不会修改代理文件.
        self.dump_count_threshold = 20
        # 存放代理列表的文件, 每行一个代理, 格式为ip:port, 注意没有http://, 而且这个文件会被修改, 注意备份
        self.proxy_file = "proxies.dat"
        # 是否在超时的情况下禁用代理
        self.invalid_proxy_flag = True
        # 当有效代理小于这个数时(包括直连), 从网上抓取新的代理, 可以将这个数设为为了满足每个ip被要求输入验证码后得到足够休息时间所需要的代理数
        # 例如爬虫在十个可用代理之间切换时, 每个ip经过数分钟才再一次轮到自己, 这样就能get一些请求而不用输入验证码
        # 如果这个数过小, 例如两个, 爬虫用A ip爬了没几个就被ban, 换了一个又爬了没几次就被ban, 这样整个爬虫就会处于一种忙等待的状态, 影响效率
        self.extend_proxy_threshold = 5
        # 初始化代理列表
        self.proxies = [{"proxy": False, "valid": False, "start_time": time.time(), "count": 0}]
        # self.proxies = []
        self.proxy_index = 0
        # 表示可信代理的数量(如自己搭建的HTTP代理)+1(不用代理直接连接)
        # 豆瓣特殊处理，永远不直联
        self.fixed_proxy = 0
        # 上一次抓新代理的时间
        self.last_fetch_proxy_time = datetime.now()
        # 每隔固定时间强制抓取新代理(min)
        self.fetch_proxy_interval = 10080
        # 一个将被设为invalid的代理如果已经成功爬取大于这个参数的页面， 将不会被invalid
        # 改为超过该参数就设为非法
        self.invalid_proxy_threshold = 50000
        # 对存在以下路径的url，不采用代理
        # self.direct_connect_resources = ['movie.douban.com/subject']
        self.direct_connect_resources = []
        # 一分钟内最多抓取多少页(豆瓣限制应该是40页，设置值要考虑并发情况所以设小一点)
        self.max_freq = 35
        # 初始化代理
        self.fetch_new_proxies()
        # if os.path.exists(self.proxy_file):
        #     # 从文件读取初始代理
        #     with open(self.proxy_file, "r") as fd:
        #         lines = fd.readlines()
        #         for line in lines:
        #             line = line.strip()
        #             if not line or self.url_in_proxies("http://" + line):
        #                 continue
        #             self.proxies.append({"proxy": "http://" + line,
        #                                  "valid": True,
        #                                  "start_time": time.time(),
        #                                  "count": 0})

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def url_in_proxies(self, url):
        """
        返回一个代理url是否在代理列表中
        """
        for p in self.proxies:
            if url == p["proxy"]:
                return True
        return False

    def reset_proxies(self):
        """
        将所有count>=指定阈值的代理重置为valid,
        """
        # 豆瓣特殊处理，不重置
        return None
        # logger.info("reset proxies to valid")
        # for p in self.proxies:
        #     if p["count"] >= self.dump_count_threshold:
        #         p["valid"] = True

    def fetch_new_proxies(self):
        """
        从网上抓取新的代理添加到代理列表中
        """
        logger.info("extending proxies using fetch_free_proxies.py")
        proxy_hunter = ProxyHunter(10)
        new_proxies = proxy_hunter.fetch_all()
        logger.info("new proxies: %s" % new_proxies)
        self.last_fetch_proxy_time = datetime.now()

        for np in new_proxies:
            if self.url_in_proxies(np):
                continue
            else:
                self.proxies.append({"proxy": np,
                                     "valid": True,
                                     "start_time": time.time(),
                                     "count": 0})
        if self.len_valid_proxy() < self.extend_proxy_threshold:  # 如果发现抓不到什么新的代理了, 缩小threshold以避免白费功夫
            self.extend_proxy_threshold -= 1

    def len_valid_proxy(self):
        """
        返回proxy列表中有效的代理数量
        """
        count = 0
        for p in self.proxies:
            if p["valid"]:
                count += 1
        return count

    def inc_proxy_index(self):
        """
        将代理列表的索引移到下一个有效代理的位置
        如果发现代理列表只有fixed_proxy项有效, 重置代理列表
        如果还发现已经距离上次抓代理过了指定时间, 则抓取新的代理
        """
        # 豆瓣特殊处理，不断言
        # assert self.proxies[0]["valid"]
        while True:
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
            if self.proxies[self.proxy_index]["valid"]:
                break

        # 两轮proxy_index==0的时间间隔过短， 说明出现了验证码抖动，扩展代理列表
        if self.proxy_index == 0 and datetime.now() < self.last_no_proxy_time + timedelta(minutes=2):
            logger.info("captcha thrashing")
            self.fetch_new_proxies()

        if self.len_valid_proxy() <= self.fixed_proxy or self.len_valid_proxy() < self.extend_proxy_threshold:  # 如果代理列表中有效的代理不足的话重置为valid
            self.reset_proxies()

        if self.len_valid_proxy() < self.extend_proxy_threshold:  # 代理数量仍然不足, 抓取新的代理
            logger.info("valid proxy < threshold: %d/%d" % (self.len_valid_proxy(), self.extend_proxy_threshold))
            self.fetch_new_proxies()

        logger.info("now using new proxy: %s" % self.proxies[self.proxy_index]["proxy"])

        # 一定时间没更新后可能出现了在目前的代理不断循环不断验证码错误的情况, 强制抓取新代理
        # 豆瓣特殊处理，不强制抓取
        # if datetime.now() > self.last_fetch_proxy_time + timedelta(minutes=self.fetch_proxy_interval):
        #    logger.info("%d munites since last fetch" % self.fetch_proxy_interval)
        #    self.fetch_new_proxies()

    def set_proxy(self, request):
        """
        将request设置使用为当前的或下一个有效代理
        """
        proxy = self.proxies[self.proxy_index]
        if not proxy["valid"]:
            self.inc_proxy_index()
            proxy = self.proxies[self.proxy_index]

        # if self.proxy_index == 0:  # 每次不用代理直接下载时更新self.last_no_proxy_time
        #     self.last_no_proxy_time = datetime.now()

        if proxy["proxy"]:
            request.meta["proxy"] = proxy["proxy"]
        elif "proxy" in request.meta.keys():
            del request.meta["proxy"]
        request.meta["proxy_index"] = self.proxy_index

        start_time = proxy["start_time"]
        freq = proxy["count"]
        curr_time = int(time.time())
        diff = int(curr_time - start_time)
        refresh_start_time = True
        print("freq:")
        print(freq)
        if diff < 60:
            # 记录时间在一分钟内，有效
            if freq > self.max_freq:
                # 抓取过于频繁，休息
                sleep_time = 60 - diff
                logger.debug('sleep:' + str(sleep_time))
                time.sleep(sleep_time)
                curr_time = int(time.time())
            else:
                proxy["count"] += 1
                refresh_start_time = False

        if refresh_start_time:
            proxy["start_time"] = curr_time
            proxy["count"] = 0

        if "Cookie" not in request.headers.keys():
            logger.debug("process_request")
            request.headers["Cookie"] = "bid=%s" % self.gen_bids() + '; ll="118281"'

        self.proxies[self.proxy_index] = proxy

    def invalid_proxy(self, index):
        """
        将index指向的proxy设置为invalid,
        并调整当前proxy_index到下一个有效代理的位置
        """
        if index < self.fixed_proxy:  # 可信代理永远不会设为invalid
            self.inc_proxy_index()
            return

        if self.proxies[index]["valid"]:
            logger.info("invalidate %s" % self.proxies[index])
            self.proxies[index]["valid"] = False
            if index == self.proxy_index:
                self.inc_proxy_index()

            # 豆瓣特殊处理
            # self.dump_valid_proxy()
            # if self.proxies[index]["count"] < self.dump_count_threshold:
            #     self.dump_valid_proxy()

    def dump_valid_proxy(self):
        """
        保存代理列表中有效的代理到文件
        """
        # 豆瓣特殊处理
        # if self.dump_count_threshold <= 0:
        #     return
        logger.info("dumping proxies to file")
        with open(self.proxy_file, "w") as fd:
            for i in range(self.fixed_proxy, len(self.proxies)):
                p = self.proxies[i]
                # 豆瓣特殊处理
                if p["valid"]:
                # if p["valid"] or p["count"] >= self.dump_count_threshold:
                    fd.write(p["proxy"] + "\n")  # 只保存有效的代理

    def process_request(self, request, spider):
        print(request.meta)
        direct_connect = False
        for direct_connect_resource in self.direct_connect_resources:
            if request.url.find(direct_connect_resource) != -1:
                direct_connect = True
                break

        if direct_connect:
            # 在直连链接的名单上，直连
            self.proxy_index = 0
        else:
            """
            将request设置为使用代理
            """
            # if self.proxy_index > 0 and datetime.now() > (
            #             self.last_no_proxy_time + timedelta(minutes=self.recover_interval)):
            #     logger.info("After %d minutes later, recover from using proxy" % self.recover_interval)
            #     self.last_no_proxy_time = datetime.now()
            #     self.proxy_index = 0
            request.meta["dont_redirect"] = True  # 有些代理会把请求重定向到一个莫名其妙的地址
            request.meta["handle_httpstatus_list"] = [301, 302]

            if "proxy_index" in request.meta.keys():
                # 豆瓣特殊处理
                # 以下情况要求更换代理
                # 1.spider发现parse error
                # 2.使用次数超过invalid_proxy_threshold
                change_proxy = False
                if "change_proxy" in request.meta.keys() and request.meta["change_proxy"]:
                    change_proxy = True

                request_proxy_index = request.meta["proxy_index"]
                if self.proxies[request_proxy_index]["count"] >= self.invalid_proxy_threshold:
                    change_proxy = True

                if change_proxy:
                    logger.info("change proxy request get by spider: %s" % request)
                    self.invalid_proxy(request.meta["proxy_index"])
                    request.meta["change_proxy"] = False
                    self.set_proxy(request)
            else:
                self.set_proxy(request)
                request.meta["proxy_index"] = self.proxy_index

    def process_response(self, request, response, spider):
        """
        检查response.status, 根据status是否在允许的状态码中决定是否切换到下一个proxy, 或者禁用proxy
        """
        if "proxy" in request.meta.keys():
            logger.debug("%s %s %s" % (request.meta["proxy"], response.status, request.url))
        else:
            logger.debug("None %s %s" % (response.status, request.url))

        # 豆瓣特殊处理
        # 以下情形认为代理无效, 切换代理
        # 1.status不是正常的200而且不在spider声明的正常爬取过程中可能出现的status列表中
        # 2.需要check_total但total非法
        # 3.需要check_director但director非法
        valid = True
        if response.status != 200 \
                and (not hasattr(spider,
                                 "website_possible_httpstatus_list") or response.status not in spider.website_possible_httpstatus_list):
            valid = False

        if "check_total" in request.meta.keys() and request.meta["check_total"]:
            hxs = Selector(response)
            try:
                total = hxs.xpath('//*[@id="content"]/div/div[1]/div[3]/a[10]/text()').extract()[0]
                print(total)
            except Exception as e:
                print(e)
                valid = False
                pass

        if "check_director" in request.meta.keys() and request.meta["check_director"]:
            hxs = Selector(response)
            try:
                director = hxs.xpath('//*[@id="info"]/span[1]/span[1]/text()').extract()[0]
                print(director)
            except Exception as e:
                print(e)
                valid = False
                pass

        if valid:
            return response
        else:
            logger.info("response status not in spider.website_possible_httpstatus_list")
            self.invalid_proxy(request.meta["proxy_index"])
            new_request = request.copy()
            new_request.dont_filter = True
            new_request.meta["change_proxy"] = True
            new_request.headers["Cookie"] = "bid=%s" % self.gen_bids() + '; ll="118281"'
            return new_request

    def process_exception(self, request, exception, spider):
        """
        处理由于使用代理导致的连接异常
        """
        request_proxy_index = request.meta["proxy_index"]
        logger.debug("%s exception: %s" % (self.proxies[request_proxy_index]["proxy"], exception))

        # 豆瓣特殊处理
        # 连接异常直接换代理
        self.invalid_proxy(request_proxy_index)
        new_request = request.copy()
        new_request.dont_filter = True
        new_request.meta["change_proxy"] = True
        new_request.headers["Cookie"] = "bid=%s" % self.gen_bids() + '; ll="118281"'
        return new_request

        # 只有当proxy_index>fixed_proxy-1时才进行比较, 这样能保证至少本地直连是存在的.
        # if isinstance(exception, self.DONT_RETRY_ERRORS):
        #     # 豆瓣特殊处理
        #     # 连接异常直接换代理
        #     self.invalid_proxy(request_proxy_index)
        #     # if request_proxy_index > self.fixed_proxy - 1 and self.invalid_proxy_flag:  # WARNING 直连时超时的话换个代理还是重试? 这是策略问题
        #     #     if self.proxies[request_proxy_index]["count"] < self.invalid_proxy_threshold:
        #     #         self.invalid_proxy(request_proxy_index)
        #     #     elif request_proxy_index == self.proxy_index:  # 虽然超时，但是如果之前一直很好用，也不设为invalid
        #     #         self.inc_proxy_index()
        #     # else:  # 简单的切换而不禁用
        #     #     if request.meta["proxy_index"] == self.proxy_index:
        #     #         self.inc_proxy_index()
        #     new_request = request.copy()
        #     new_request.dont_filter = True
        #     return new_request
