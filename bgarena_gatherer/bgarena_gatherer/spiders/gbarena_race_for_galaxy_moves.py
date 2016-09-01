# -*- coding: utf-8 -*-
import datetime

import scrapy
from scrapy_splash import SplashRequest

from bgarena_gatherer.items import GameTableItem, GameTablePlayerScoreItem

script = """
function main(splash)
  local url = splash.args.url
  assert(splash:go(url))
  assert(splash:wait(3.9))
  return {
    html = splash:html(),
    har = splash:har(),
  }
end
"""



def get_last_checked_table_id():
    from bgarena_gatherer.get_latest_crawled import last_crawled_table_id
    last_checked_table_id = last_crawled_table_id()
    return last_checked_table_id

class BGArenaTablesSpider(scrapy.Spider):
    name = "bgarenatables"
    allowed_domains = ["pt.boardgamearena.com"]
    final_table_id = 280482
    tables_base_url = "https://pt.boardgamearena.com/#!table?table=%d"

    last_checked_table_id = get_last_checked_table_id()

    # start_urls = [
    #     tables_base_url % i for i in xrange(last_checked_table_id + 1, final_table_id)
    # ]

    start_urls = [
        tables_base_url % i for i in xrange(last_checked_table_id, final_table_id, -1)
    ]

    # start_urls = [
    #     tables_base_url % 85151
    # ]




    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(
                url,
                self.parse,
                endpoint='execute',
                args={'lua_source': script},
            )

    def check_table_exists(self, response):
        return len(response.xpath('//*[@id="bga_fatal_error_descr"]')) == 0

    def get_creation_time_calculated(self, creation_time_txt):
        today = datetime.date.today()
        if 'ontem' in creation_time_txt:
            yesterday = today - datetime.timedelta(days=1)
            return yesterday.strftime('%d/%m/%Y')
        else:
            return today.strftime('%d/%m/%Y')

    def get_creating_time(self, response):
        creation_time_div = response.xpath('//*[@id="creationtime"]')
        if not creation_time_div:
            return ''

        creation_time_txt = creation_time_div.xpath('text()')
        if creation_time_txt.extract()[0].count('/') != 2:
            creation_time = self.get_creation_time_calculated(creation_time_txt)
        else:
            creation_time = creation_time_txt.re('[0-9][0-9]\/[0-9][0-9]\/[0-9][0-9][0-9][0-9]')[0]
        return creation_time

    def get_elo_rating(self, response):
        elo_rating_opt = response.xpath('//*[@id="gameoption_201_displayed_value"]/text()')
        # return -1 if there is no option information available
        if len(elo_rating_opt) == 0:
            return -1

        return 1 if 'Ligado' in elo_rating_opt.extract()[0] else 0

    def get_gamespeed(self, response):
        get_gamespeed_opt = response.xpath('//*[@id="gameoption_200_displayed_value"]/text()')

        if len(get_gamespeed_opt) == 0:
            return ''

        return get_gamespeed_opt[0].extract().replace(u'\u2022', ':')

    def get_gamestatus(self, response):
        game_abandonned_sel = response.xpath('//*[@id="game_abandonned"]').xpath('@style').extract()[0]
        was_abandonned = 'block' in game_abandonned_sel
        game_cancelled_sel = response.xpath('//*[@id="game_cancelled"]').xpath('@style').extract()[0]
        was_cancelled = 'block' in game_cancelled_sel
        if was_abandonned:
            return GameTableItem.GAMESTATUS_OPTS['abandonned']
        else:
            if was_cancelled:
                return GameTableItem.GAMESTATUS_OPTS['cancelled']

            game_status = response.xpath('//*[@id="status_detailled"]/text()').extract()[0]
            if 'terminou' in game_status:
                return GameTableItem.GAMESTATUS_OPTS['finished']
            else:
                return GameTableItem.GAMESTATUS_OPTS['open']

    def get_score(self, player):
        score = player.xpath('div[@class="score"]/text()').extract()
        if len(score) == 0:
            score = 0
        else:
            score = score[0].replace(' ', '')
            if score == '':
                score = 0
        return score

    def parse(self, response):
        table_id = response.url.split('table=')[-1]
        if not self.check_table_exists(response):
            self.last_checked_table_id = int(table_id)
            yield {'error': response.url}
        else:

            table_item = GameTableItem()
            table_item['game'] = response.xpath('//*[@id="table_name"]/text()').extract()[-1].split(" #%s" % table_id)[0]
            table_item['table_link'] = response.url
            table_item['creation_time'] = self.get_creating_time(response)
            table_item['estimated_duration'] = response.xpath('//*[@id="estimated_duration"]/text()').extract()[0]
            table_item['is_elo_rating'] = self.get_elo_rating(response)
            table_item['game_speed'] = self.get_gamespeed(response)
            table_item['game_status'] = self.get_gamestatus(response)

            players = response.xpath('//*[@class="score-entry"]')
            players_scores_items = []
            for player in players:
                player_score_item = GameTablePlayerScoreItem()
                player_score_item['player_id'] = player.xpath('div/a/@href').extract()[0].split('=')[-1]
                player_score_item['score'] = self.get_score(player)
                players_scores_items.append(player_score_item)

            table_item['players_scores'] = players_scores_items

            yield table_item

        # filename = 'last_checked_table_id.txt'
        # with open(filename, 'wb') as f:
        #     f.write(table_id)
