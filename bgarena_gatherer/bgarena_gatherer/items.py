# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class GameTableItem(scrapy.Item):
    GAMESTATUS_OPTS = {
        'open': 0,
        'finished': 1,
        'abandonned': 2,
    }

    game = scrapy.Field()
    table_link = scrapy.Field()
    creation_time = scrapy.Field()
    estimated_duration = scrapy.Field()
    is_elo_rating = scrapy.Field()
    players_scores = scrapy.Field()
    game_status = scrapy.Field()
    game_speed = scrapy.Field()


class GameTablePlayerScoreItem(scrapy.Item):
    player_id = scrapy.Field()
    score = scrapy.Field()
