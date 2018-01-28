# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class DoubanItem(Item):
    film_id = Field()
    title = Field()
    score = Field()
    num = Field()
    link = Field()
    type = Field()
    directors = Field()
    screenwriters = Field()
    actors = Field()
    tags = Field()
    time = Field()
    length = Field()
    updated_at = Field()
    created_at = Field()
