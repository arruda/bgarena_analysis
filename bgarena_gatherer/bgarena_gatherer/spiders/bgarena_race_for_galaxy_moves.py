# -*- coding: utf-8 -*-
import os
import datetime
from functools import partial
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
    assert(splash:wait(6.0))
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
        print ">>>>> Current crawling list len: %d" % len(self.final_list)

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

    def get_current_tables_to_craw_list(self):

        already_crawled_table_ids = self.session.query(GameTableMoveAction.game_table_id).distinct()
        tables_not_crawled = self.get_all_finished_tables_ids().filter(~GameTable.id.in_(already_crawled_table_ids))
        tables_not_crawled = tables_not_crawled.order_by(GameTable.id.desc()).with_entities(GameTable.id, GameTable.table_link)
        return tables_not_crawled


    def get_all_finished_tables_ids(self):
        return self.session.query(GameTable)\
                .filter(GameTable.game==self.game)\
                .filter(GameTable.game_status == GameTableItem.GAMESTATUS_OPTS['finished'])\
                .filter(GameTable.id > 277298) # ids smaller then this are of old tables and so with no logs


    def get_tables_with_id_smaller_than_given_id(self, table_id):

        return self.session.query(GameTable)\
                .filter(GameTable.game==self.game)\
                .filter(GameTable.game_status == GameTableItem.GAMESTATUS_OPTS['finished'])\
                .filter(GameTable.id < table_id)\
                .order_by(GameTable.id.desc()).with_entities(GameTable.id, GameTable.table_link)

    def load_list(self):
        table_list = list(self.get_current_tables_to_craw_list())
        self.session.close()
        self.final_list = [
            [tid, self.get_game_review_from_table_link(table_link)] for tid, table_link in table_list
        ]
        return self.final_list

    def get_game_review_from_table_link(self, table_link):
        table_id = table_link.split('?table=')[-1]
        base_game_review_url = "https://en.boardgamearena.com/#!gamereview?table=%s"
        return base_game_review_url % table_id


last_checked_manager = LastCheckedTableMoveManager("Race for the Galaxy")


class BGRaceMovesSpider(scrapy.Spider):
    name = "bgracemoves"
    allowed_domains = ["en.boardgamearena.com"]
    game_reviews_to_craw = last_checked_manager.final_list
    start_urls = ["https://en.boardgamearena.com/#!account",]

    game_name = "Race for the Galaxy"

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

    def replace_players_name_in_action(self, action, name_to_number):
        players_names = name_to_number.keys()

        order_by_len_names = sorted(players_names, key=len)
        for p_name in order_by_len_names:
            action = action.replace(p_name, 'player-%d' % name_to_number[p_name])
        return action

    def parse_move_info(self, div):
        move_number_txt = div.xpath('text()').extract()
        move_number_txt = move_number_txt[0] if move_number_txt else None
        move_number = move_number_txt.replace('Move', '').replace(':', '').replace(' ', '')

        time = div.xpath('span/text()').extract()
        time = time[0] if time else None

        return {'move_number': move_number, 'move_date': time}

    def parse_action_info(self, div, name_to_number):
        action = div.xpath('text()').extract()
        action = action[0] if action else None
        action = self.replace_players_name_in_action(action, name_to_number)
        return action

    def parse_real_request(self, tablemodel_id, response):


        name_to_number = self.get_player_name_to_number_mapping(response)
        divs = response.xpath('//*[@id="gamelogs"]/div')
        base_last_move = {
            'game': self.game_name,
            'game_table_id': tablemodel_id,
        }
        moves = []
        for div in divs:
            div_class = div.xpath('@class').extract()
            div_class = div_class[0] if div_class else None
            # info sobre o movimento (numero e hora)
            if div_class == 'smalltext':
                last_move = {}
                last_move.update(base_last_move)
                last_move.update(self.parse_move_info(div))
            else:
                new_move_action = last_move.copy()
                action = self.parse_action_info(div, name_to_number)
                new_move_action['action'] = action
                moves.append(new_move_action)
        return {'moves': moves}

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
        args = self.prepare_after_login_args(response)
        for tablemodel_id, url in self.game_reviews_to_craw:
            parser_with_table_id = partial(self.parse_real_request, tablemodel_id)
            yield SplashRequest(
                url,
                parser_with_table_id,
                endpoint='execute',
                args=args,
        )