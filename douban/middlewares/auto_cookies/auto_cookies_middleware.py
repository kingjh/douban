#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import logging
import random
import string

import time

logger = logging.getLogger(__name__)


class AutoCookiesMiddleware(object):
    def __init__(self):
        self.start_time_min = int(time.time())
        # self.start_time_hour = int(time.time())
        self.freq = 0
        # 一分钟内最多抓取多少页(豆瓣限制应该是40页，设置值要考虑并发情况所以设小一点)
        self.max_freq_min = 40
        # 连续抓取时间(不知道连续抓取多久后豆瓣才会重定向请求，故设99999999分钟)
        # self.max_freq_hour = 99999999
        # 休息大概3.8小时能解封
        self.sleep_hour = 3.8

    def gen_bids(self):
        return "".join(random.sample(string.ascii_letters + string.digits, 11))

    def process_request(self, request, spider):
        # 禁止重定向
        request.meta["dont_redirect"] = True
        request.meta["handle_httpstatus_list"] = [301, 302]

        curr_time = int(time.time())
        # start_time_hour = self.start_time_hour
        # diff_hour = int(curr_time - start_time_hour)
        # logger.debug('start_time_hour:' + str(start_time_hour))
        logger.debug('curr_time:' + str(curr_time))
        # logger.debug('diff_hour:' + str(diff_hour))
        # if diff_hour > 60 * self.max_freq_hour:
        #     # 连续抓取时间过长，休息
        #     time.sleep(60 * 60 * self.sleep_hour + 1)
        #     self.start_time_hour = int(time.time())

        start_time_min = self.start_time_min
        diff_min = int(curr_time - start_time_min)
        logger.debug('start_time_min:' + str(start_time_min))
        logger.debug('curr_time:' + str(curr_time))
        logger.debug('diff_min:' + str(diff_min))
        refresh_start_time_min = True
        if diff_min < 60:
            # 记录时间在一分钟内，有效
            freq = self.freq
            if freq > self.max_freq_min:
                # 抓取过于频繁，休息
                sleep_time = 61
                logger.debug('sleep:' + str(sleep_time))
                time.sleep(sleep_time)
            else:
                self.freq += 1
                freq = self.freq
                logger.debug('curr_time:' + str(curr_time) + 'freq:' + str(freq))
                refresh_start_time_min = False

        if refresh_start_time_min:
            self.start_time_min = int(time.time())
            self.freq = 0
            logger.debug('curr_time:' + str(curr_time) + 'freq:0')

        if "Cookie" not in request.headers.keys():
            logger.debug("process_request")
            request.headers["Cookie"] = "bid=%s" % self.gen_bids() + '; ll="118281"'

    def process_response(self, request, response, spider):
        # 当status不是正常的200而且不在spider声明的正常爬取过程中可能出现的status列表中，重新生成cookies
        logger.debug("process_response")
        logger.debug(response.status)
        if response.status != 200 \
                and (not hasattr(spider,
                                 "website_possible_httpstatus_list") or response.status not in spider.website_possible_httpstatus_list):
            if response.status == 302:
                # 连续抓取时间过长，被重定向了，休息
                time.sleep(60 * 60 * self.sleep_hour + 1)

            new_request = request.copy()
            new_request.dont_filter = True
            logger.debug(request.headers["Cookie"])
            s = str(request.headers["Cookie"])
            p = s.find('ll=')
            ll = s[p + 4:p + 10]
            new_request.headers["Cookie"] = 'bid=' + self.gen_bids() + '; ll="' + ll + '"'
            logger.debug(new_request.headers["Cookie"])
            return new_request
        else:
            return response
