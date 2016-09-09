#! -*- coding: utf-8 -*-

from sqlalchemy.orm import sessionmaker
from models import GameTablePlayerScore, GameTable, db_connect, create_tables


class BGArenaPipeline(object):
    def __init__(self):
        """
        Initializes database connection and sessionmaker.
        Creates all tables.
        """
        engine = db_connect()
        create_tables(engine)
        self.Session = sessionmaker(bind=engine)

    def save_models_to_db(self, game_table, players_scores=[]):
        session = self.Session()
        try:
            session.add(game_table)
            session.commit()
            if players_scores:
                for player_score in players_scores:
                    player_score.game_table_id = game_table.id
                    session.add(player_score)
                session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def process_item(self, item, spider):
        """
        Save game information in the database.
        This method is called for every item pipeline component.
        """
        if 'testando' in item.keys():
            return item

        if 'error' in item.keys():
            game_table_item = {
                'game': 'ERROR',
                'table_link': item.get('error')
            }
        else:
            game_table_item = item

        players_scores_item = game_table_item.get('players_scores', None)

        game_table = GameTable(**{k: v for k, v in game_table_item.items() if k != 'players_scores'})

        players_scores = []
        if players_scores_item:
            for player_score_item in players_scores_item:
                players_scores.append(GameTablePlayerScore(**player_score_item))

        self.save_models_to_db(game_table, players_scores)

        return item
