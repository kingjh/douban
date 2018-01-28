#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from bs4 import BeautifulSoup
import urllib.request, urllib.error, urllib.parse
import logging

logger = logging.getLogger(__name__)


class ProxyHunter:
    """
    测试代理线程类
    """
    def __init__(self, end_page):
        self.end_page = end_page

    def run(self):
        pass

    def get_html(self, url):
        request = urllib.request.Request(url)
        request.add_header("User-Agent",
                           "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.99 Safari/537.36")
        html = urllib.request.urlopen(request)
        return html.read()

    def get_soup(self, url):
        soup = BeautifulSoup(self.get_html(url), "lxml")
        return soup

    def fetch_kxdaili(self, page):
        """
        从www.kxdaili.com抓取免费代理
        """
        proxies = []
        try:
            url = "http://www.kxdaili.com/ipList/%d.html#ip" % page
            soup = self.get_soup(url)
            table_tag = soup.find("table", attrs={"class": "ui table segment"})
            trs = table_tag.tbody.find_all("tr")
            for tr in trs:
                tds = tr.find_all("td")
                ip = tds[0].text
                port = tds[1].text
                protocol = tds[3].text
                if len(protocol) > 4:
                    protocol = 'HTTPS'
                latency = tds[4].text.split(" ")[0]
                if float(latency) < 0.5:  # 输出延迟小于0.5秒的代理
                    # 筛选延迟
                    proxies.append("%s://%s:%s" % (protocol, ip, port))

        except:
            print(sys.exc_info())
            logger.warning("fail to fetch from kxdaili")
        return proxies

    def img2port(self, img_url):
        """
        mimvp.com的端口号用图片来显示, 本函数将图片url转为端口, 目前的临时性方法并不准确
        """
        code = img_url.split("=")[-1]
        switcher = {
            'NmDigm4vMpDgw': "8080",
            'NmTiUm4vMpDg4': "8088",
            'NmTiUm4vMpTIz': "8123",
            'NmTiUm4vOpDg4': "8888",
            'NmTiUm4vMpTE4': "8188",
            'NmTiUm4vMpQO0OO0O': "81",
            'NmDigmzvMpTI4': "3128",
            'NmTiUm4vMpDgO0O': "808",
            'NmTiUm4vMpAO0OO0O': "80",
            'NmTiUm4vMpDkw': "8090",
            'NmTiUm5vNpzk3': "9797",
            'NmTiUm5vOpTk5': "9999",
            'MmjiEm4vMpTE4': "8118",
            'MmjiEm5vMpDAw': "9000",
        }
        print('222' + switcher.get(code))
        return switcher.get(code)

    def fetch_mimvp(self):
        """
        从http://proxy.mimvp.com/free.php抓免费代理
        """
        proxies = []
        try:
            url = "http://proxy.mimvp.com/free.php?proxy=in_hp"
            soup = self.get_soup(url)
            table = soup.find("table", attrs={"class": "free-table"})
            trs = table.tbody.find_all("tr")
            for tr in trs:
                tds = tr.find_all("td")
                ip = tds[1].text
                port = self.img2port(tds[2].img["src"])
                response_time = tds[7]["title"][:-1]
                # if port is not None and float(response_time) < 1:
                if port is not None:
                    # 暂不筛选时间
                    proxy = "%s:%s" % (ip, port)
                    proxies.append(proxy)
        except:
            logger.warning("fail to fetch from mimvp")
        return proxies

    def fetch_xici(self):
        """
        http://www.xicidaili.com/nn/
        """
        proxies = []
        url = "http://www.xicidaili.com/nn/"
        try:
            soup = self.get_soup(url + str(1))
            table = soup.find("table", attrs={"id": "ip_list"})
            trs = table.find_all("tr")
            for j in range(1, len(trs)):
                tr = trs[j]
                tds = tr.find_all("td")
                ip = tds[1].text
                port = tds[2].text
                protocol = tds[5].text
                if len(protocol) > 4:
                    protocol = 'HTTPS'
                speed = tds[6].div["title"][:-1]
                latency = tds[7].div["title"][:-1]
                if float(speed) < 3 and float(latency) < 1:
                    # 筛选速度和延迟
                    proxies.append("%s://%s:%s" % (protocol, ip, port))

        except:
            logger.warning("fail to fetch from xici")
        return proxies

    def fetch_ip181(self):
        """
        http://www.ip181.com/
        """
        proxies = []
        try:
            url = "http://www.ip181.com/"
            soup = self.get_soup(url)
            table = soup.find("table")
            trs = table.find_all("tr")
            for i in range(1, len(trs)):
                tds = trs[i].find_all("td")
                ip = tds[0].text
                port = tds[1].text
                latency = tds[4].text[:-2]
                # if float(latency) < 1:
                # 暂不筛选时间
                proxies.append("%s:%s" % (ip, port))
        except Exception as e:
            logger.warning("fail to fetch from ip181: %s" % e)
        return proxies

    def fetch_httpdaili(self):
        """
        http://www.httpdaili.com/mfdl/
        更新比较频繁
        """
        proxies = []
        try:
            url = "http://www.httpdaili.com/mfdl/"
            soup = self.get_soup(url)
            table = soup.find("div", attrs={"kb-item-wrap11"}).table
            trs = table.find_all("tr")
            print('fetch_httpdaili' + str(trs))

            for i in range(1, len(trs)):
                try:
                    tds = trs[i].find_all("td")
                    ip = tds[0].text
                    port = tds[1].text
                    proxy_type = tds[2].text
                    if proxy_type == "匿名":
                        proxies.append("%s:%s" % (ip, port))
                except:
                    pass
        except Exception as e:
            logger.warning("fail to fetch from httpdaili: %s" % e)
        return proxies

    def fetch_66ip(self):
        """
        http://www.66ip.cn/
        每次打开此链接都能得到一批代理, 速度不保证
        """
        proxies = []
        try:
            # 修改getnum大小可以一次获取不同数量的代理
            url = "http://www.66ip.cn/nmtq.php?getnum=10&isp=0&anonymoustype=3&start=&ports=&export=&ipaddress=&area=1&proxytype=0&api=66ip"
            content = self.get_html(url).decode('gb2312')
            urls = content.split("</script>")[1].split("<br />")
            for u in urls:
                if u.strip():
                    proxies.append('http://' + u.strip())
            del proxies[len(proxies) - 1]
        except Exception as e:
            logger.warning("fail to fetch from 66ip: %s" % e)
        return proxies

    def check(self, proxy):
        import urllib.request, urllib.error, urllib.parse
        url = "http://www.baidu.com/js/bdsug.js?v=1.0.3.0"
        url = "https://movie.douban.com/tag/%E6%96%87%E8%89%BA"
        obj = {'http': proxy}
        if proxy.find('HTTPS') != -1:
            obj = {'https': proxy}
        proxy_handler = urllib.request.ProxyHandler(obj)
        opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPHandler)
        try:
            response = opener.open(url, timeout=3)
            return response.code == 200
        except Exception:
            return False

    def fetch_all(self):
        proxies = []
        for i in range(1, self.end_page):
            proxies += self.fetch_kxdaili(i)
        print("kxdaili:")
        print(proxies)
        proxies += self.fetch_xici()
        proxies += self.fetch_66ip()

        # 以下已不可用
        # proxies += self.fetch_mimvp()
        # proxies += self.fetch_ip181()
        # proxies += self.fetch_httpdaili()
        print('proxies')
        print(proxies)
        valid_proxies = []
        logger.info("checking proxies validation")
        for p in proxies:
            if self.check(p):
                valid_proxies.append(p)
        return valid_proxies


# if __name__ == '__main__':
#     import sys
#
#     root_logger = logging.getLogger("")
#     stream_handler = logging.StreamHandler(sys.stdout)
#     formatter = logging.Formatter('%(name)-8s %(asctime)s %(levelname)-8s %(message)s', '%a, %d %b %Y %H:%M:%S', )
#     stream_handler.setFormatter(formatter)
#     root_logger.addHandler(stream_handler)
#     logger = logging.getLogger(__name__)
#     logger.setLevel(logging.DEBUG)
#     proxies = self.fetch_all()
#     # print check("202.29.238.242:3128")
#     for p in proxies:
#         print(p)
