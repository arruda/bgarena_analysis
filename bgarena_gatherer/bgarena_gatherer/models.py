#! -*- coding: utf-8 -*-
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.engine.url import URL


DeclarativeBase = declarative_base()


def db_connect():
    import settings
    return create_engine(URL(**settings.DATABASE))


def create_tables(engine):
    DeclarativeBase.metadata.create_all(engine)


class GameTable(DeclarativeBase):
    __tablename__ = "gametable"
    id = Column(Integer, primary_key=True)
    game = Column('game', String)
    table_link = Column('table_link', String, nullable=True)
    creation_time = Column('creation_time', String, nullable=True)
    estimated_duration = Column('estimated_duration', String, nullable=True)
    is_elo_rating = Column('is_elo_rating', Integer, nullable=True)
    game_speed = Column('game_speed', String, nullable=True)
    game_status = Column('game_status', Integer, nullable=True)
    players_scores = relationship("GameTablePlayerScore")


class GameTablePlayerScore(DeclarativeBase):
    __tablename__ = "gametableplayerscore"
    id = Column(Integer, primary_key=True)
    game_table_id = Column(Integer, ForeignKey('gametable.id'))
    game_table = relationship("GameTable", back_populates="players_scores")
    player_id = Column('player_id', Integer, nullable=True)
    score = Column('score', Integer, nullable=True)
