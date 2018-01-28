# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import time
from scrapy.conf import settings
from douban.items import DoubanItem
import pymysql.cursors


class DoubanPipeline(object):
    def __init__(self):
        host = settings['MYSQL_HOST']
        port = settings['MYSQL_PORT']
        db = settings['MYSQL_DB']
        user = settings['MYSQL_USER']
        password = settings['MYSQL_PASSWORD']
        charset = settings['MYSQL_CHARSET']
        self.conn = pymysql.connect(host=host, port=port, user=user, password=password, db=db, charset=charset)
        self.cursor = self.conn.cursor()
        self.table = settings['MYSQL_TABLE_DOUBAN']

    def process_item(self, item, spider):
        if isinstance(item, DoubanItem):
            try:
                # append type
                sql = "select 1 from `{table}` where {columns} = {values};".format(table=self.table,
                                                                                        columns='film_id',
                                                                                        values=item['film_id'])
                self.cursor.execute(sql)
                ret = self.cursor.fetchone()
                if ret:
                    type = ret[0]
                    if type != 0:
                        # 避免错误重写类型
                        item['type'] = type
                    item['updated_at'] = time.time()
                else:
                    item['created_at'] = time.time()
                    item['updated_at'] = time.time()

                dictionary = dict(item)
                placeholder = ", ".join(["%s"] * len(dictionary))
                sql = "replace into `{table}` ({columns}) values ({values});".format(table=self.table, columns=",".join(
                    dictionary.keys()), values=placeholder)
                self.cursor.execute(sql, list(dictionary.values()))
                self.conn.commit()
            except Exception as e:
                print(e)
                pass
        return item
