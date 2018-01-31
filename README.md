# 基于python3 scrapy框架抓取豆瓣影视资料
## 思路
* * 资料分类策略：参考了：https://zhuanlan.zhihu.com/p/24771128?refer=pythoncrawl

添加了“电影”、“电视剧”标签以区分影视是电影还是电视剧

* * 代理、cookie等策略：参考了：https://zhuanlan.zhihu.com/p/24035574
但现在换bid的策略的好像不行了；用代理服务器又太慢（可在setting.py中取消HttpProxyMiddleware那行的注释以用代理服务器，会自
动抓取代理）。因此本项目用的是：
1.单ip连续抓取，40次/分钟（超过的话很快会被封）
2.遇到302错误（ip被封）就等待3.5小时再抓取的策略（ip被豆瓣封后3-3.5小时解封）

完整抓取64000条影视数据需时7-8天，可用多机分开抓取不同分类以提高速度

## 所需软件
* * Anaconda + mysql，Windows和Linux皆可

## 使用方法
* * 请先安装Anaconda，把其中的python3可执行文件设为系统默认的python可执行文件
* * 在setting.py补充db相关信息（MYSQWL_开头那几行）
* * 在db执行init.sql
* * 执行python run.py，爬虫就会启动，把抓取到的资料写进pz_douban_movie表中

## 运行效果
* * 请参考（资料可导出）：http://www.17pz.top/frontend/web/info/douban-movie/index.html