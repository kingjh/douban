# 基于python3 scrapy框架抓取豆瓣影视资料
## 思路
* * 抓取路径参考：https://zhuanlan.zhihu.com/p/24771128?refer=pythoncrawl
* * 抓取策略参考：https://zhuanlan.zhihu.com/p/24035574
但现在换bid的策略的好像不行了；用代理服务器又太慢（可在setting.py中取消HttpProxyMiddleware那行的注释以用代理服务器，会自
动抓取代理）。因此本项目用的是单ip连续抓取，遇到302错误就等待3.5小时再抓取的策略（ip被豆瓣封后3-3.5小时解封），完整抓取
64000条影视数据需时7-8天

## 使用方法
* * 请先安装Anaconda，把其中的python3可执行文件设为默认的python可执行文件
* * 在setting.py补充db相关信息（MYSQWL_开头那几行）
* * 在db执行init.sql
* * 执行python run.py，爬虫就会启动
