# -*- coding: utf-8 -*-
import os
import datetime
import json

import scrapy
from scrapy_splash import SplashRequest

from sqlalchemy.orm import sessionmaker

from bgarena_gatherer.items import GameTableItem
from bgarena_gatherer.models import GameTable, GameTableMoveAction, db_connect

ACC = os.environ.get('ACC', None)
PASS = os.environ.get('PASS', None)

if ACC is None or PASS is None:
    raise Exception('Need ACC and PASS envvars')


script_test_using_cookies = """
function main(splash)

   local phpsessid = splash.args.phpsessid
   local tournoienligne_sso_user = splash.args.tournoienligne_sso_user
   local tournoienligne_sso_id = splash.args.tournoienligne_sso_id
   local tournoienligneuser = splash.args.tournoienligneuser
   local tournoienligneauth = splash.args.tournoienligneauth
   local io = splash.args.io


   splash:init_cookies(
        {
            { domain="en.boardgamearena.com",
             secure=false,
             value=phpsessid,
             path="/",
             httpOnly=false,
             name="PHPSESSID",
            },
            { domain=".boardgamearena.com",
             secure=false,
             value=tournoienligne_sso_user,
             path="/",
             httpOnly=false,
             name="TournoiEnLigne_sso_user",
            },
            { domain=".boardgamearena.com",
             secure=false,
             value=tournoienligne_sso_id,
             path="/",
             httpOnly=false,
             name="TournoiEnLigne_sso_id",
            },
            { domain=".boardgamearena.com",
             name="TournoiEnLigneuser",
             expires="2026-09-05T16:10:34Z",
             value=tournoienligneuser,
             path="/",
             httpOnly=false,
             secure=false,
            },
            { domain=".boardgamearena.com",
             name="TournoiEnLigneauth",
             expires="2026-09-05T16:10:34Z",
             value=tournoienligneauth,
             path="/",
             httpOnly=false,
             secure=
            false,
            },
            { domain="c.boardgamearena.net",
             secure=false,
             value=io,
             path="/socket.io/",
             httpOnly=false,
             name="io",
            },
        }
    )

    local url = splash.args.url
    assert(splash:go(url))
    assert(splash:wait(4.0))
    return splash:html()
end
"""
script_login_cookies = """
function main(splash)
    local url = splash.args.url
    assert(splash:go(url))
    assert(splash:wait(5.0))

    assert(splash:runjs("document.getElementById('username_input').value = '%s';"))
    assert(splash:runjs("document.getElementById('password_input').value = '%s';"))
    local get_dimensions = splash:jsfunc([[
        function () {
            var rect = document.getElementById('login_button').getBoundingClientRect();
            return {"x": rect.left, "y": rect.top}
        }
    ]])
    splash:set_viewport_full()
    splash:wait(0.1)
    local dimensions = get_dimensions()
    splash:mouse_click(dimensions.x, dimensions.y)

    splash:wait(5.0)
    return splash:get_cookies()
end
""" % (ACC, PASS)


class LastCheckedTableMoveManager(object):
    """
        Manage what was the last crawled table move of a given game
    """
    def __init__(self, game):
        super(LastCheckedTableMoveManager, self).__init__()
        self.game = game
        self.session = self.start_session()
        self.final_list = []
        self.load_list()

    def start_session(self):
        engine = db_connect()
        Session = sessionmaker(bind=engine)
        session = Session()
        return session

    def get_table_moves_for_game(self):
        return self.session.query(GameTableMoveAction).filter(GameTableMoveAction.game==self.game)

    def get_last_crawled_move(self):
        last_move = list(self.get_table_moves_for_game().order_by(GameTableMoveAction.id.desc()).limit(1))
        if len(last_move) == 0:
            return None

        return last_move[0]

    def get_all_finished_tables(self):
        return self.session.query(GameTable)\
                .filter(GameTable.game==self.game)\
                .filter(GameTable.game_status == GameTableItem.GAMESTATUS_OPTS['finished'])\
                .order_by(GameTable.id.desc()).with_entities(GameTable.id, GameTable.table_link)

    def get_tables_with_id_smaller_than_given_id(self, table_id):

        return self.session.query(GameTable)\
                .filter(GameTable.game==self.game)\
                .filter(GameTable.game_status == GameTableItem.GAMESTATUS_OPTS['finished'])\
                .filter(GameTable.id < table_id)\
                .order_by(GameTable.id.desc()).with_entities(GameTable.id, GameTable.table_link)

    def get_current_tables_to_craw_list(self):
        last_move = self.get_last_crawled_move()
        table_list = []
        if not last_move:
            table_list = self.get_all_finished_tables()
        else:
            last_table_id = last_move.game_table_id
            table_list = self.get_tables_with_id_smaller_than_given_id(last_table_id)
        return table_list

    def load_list(self):
        table_list = list(self.get_current_tables_to_craw_list())
        self.session.close()
        self.final_list = [
            self.get_game_review_from_table_link(table_link) for id, table_link in table_list
        ]
        return self.final_list

    def get_game_review_from_table_link(self, table_link):
        table_id = table_link.split('?table=')[-1]
        base_game_review_url = "https://en.boardgamearena.com/#!gamereview?table=%s"
        return base_game_review_url % table_id


# last_checked_manager = LastCheckedTableMoveManager("Race for the Galaxy")


class BGRaceMovesSpider(scrapy.Spider):
    name = "bgracemoves"
    allowed_domains = ["en.boardgamearena.com"]
    # game_reviews_urls = last_checked_manager.final_list
    start_urls = ["https://en.boardgamearena.com/#!account",]

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(
                url,
                self.after_login,
                endpoint='execute',
                args={'lua_source': script_login_cookies},
            )

    def get_player_name_to_number_mapping(self, response):
        name_to_number = {}
        players_names = response.xpath('//*[@id="game_result"]/div/div[@class="name"]/text()')
        for i, name in enumerate(players_names):
            name_to_number[name.extract()] = i+1
        return name_to_number

    def parse_real_request(self, response):

        import ipdb; ipdb.set_trace()
        p_name_to_number = self.get_player_name_to_number_mapping(response)
        divs = response.xpath('//*[@id="gamelogs"]/div')
        for div in divs:
            div_class = div.xpath('@class').extract()
            div_class = div_class[0] if div_class else None

            # info sobre o movimento (numero e hora)
            if div_class == 'smalltext':
                move_number_txt = div.xpath('text()').extract()
                move_number_txt = move_number_txt[0] if move_number_txt else None
                move_number = move_number_txt.replace('Move').replace(':').replace(' ')

                time = div.xpath('span/text()').extract()
                time = time[0] of time else None
                pass
            else:

                pass


        yield {'testando':response.url}

    def prepare_after_login_args(self, response):
        python_response =  json.loads(response.body)
        bg_cookies_names = [
            'phpsessid',
            'tournoienligne_sso_user',
            'tournoienligne_sso_id',
            'tournoienligneuser',
            'tournoienligneauth',
            'io'
        ]
        args_cookies_dict = {}
        for d in python_response:
            ckname  = d.get('name', None).lower()
            if ckname in bg_cookies_names:
                args_cookies_dict[ckname] = d.get('value', None)

        args = {'lua_source': script_test_using_cookies}
        args.update(args_cookies_dict)
        return args

    def after_login(self, response):
        urls = [
            "https://en.boardgamearena.com/#!gamereview?table=22791725",
            "https://en.boardgamearena.com/#!gamereview?table=22713855"
        ]

        args = self.prepare_after_login_args(response)
        for url in urls:
            yield SplashRequest(
                url,
                self.parse_real_request,
                endpoint='execute',
                args=args,
        )