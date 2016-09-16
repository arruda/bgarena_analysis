#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy.orm import sessionmaker
from models import GameTablePlayerScore, GameTable, db_connect, create_tables

def get_session():
    engine = db_connect()
    Session = sessionmaker(bind=engine)
    session = Session()

    return session

def get_table_id(game_table):
    return int(game_table.table_link.split('table=')[-1])


def get_latest_crawled():
    session = get_session()
    game_tables = list(session.query(GameTable).order_by(GameTable.id.desc()).limit(10))
    session.close()

    return game_tables

def last_crawled_table_id():
    game_tables_list = get_latest_crawled()

    table_ids = set()
    for game_table in game_tables_list:
        table_ids.add(
            get_table_id(game_table)
        )

    #first time running spider, wont have any table saved, so
    #return a given recent id, ex: 23972804
    if len(table_ids) == 0:
        return 23972804
    return sorted(table_ids)[0]

if __name__ == '__main__':
    print last_crawled_table_id()
