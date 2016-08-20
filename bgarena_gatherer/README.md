# BGArena Gatherer
Collects information from pt.boardgamearena and saves them in a Postgres database.

## Spiders
### bgarenatables
Spider that collects basic information about all game tables, from id=1 to X (configurable in the spider).

#### Information Gathered:

Example:

```python
{
'creation_time': u'11/02/2011',
 'estimated_duration': u'10 mn',
 'game': u"Can't Stop",
 'game_speed': u'Em tempo real : Velocidade normal',
 'game_status': 2,
 'is_elo_rating': -1,
 'players_scores': [{'player_id': u'43189', 'score': u'3'},
                    {'player_id': u'132592', 'score': u'2'},
                    {'player_id': u'171293', 'score': u'2'}],
 'table_link': 'https://pt.boardgamearena.com/#!table?table=66782'
 }
```

And, if the table actually doent exist, just save some simple information, ex:
```python
{'error': 'https://pt.boardgamearena.com/#!table?table=66893'}
```

### gbarenaXreplay
**TODO**: Spider specific for a given `X` game, that will gather information abount it's game replay.
This spider can make use of the basic information gathered by the `bgarenatables` spider, to know which table of the given game is OK to be crawled (many old tables are using some pretty old version so they won't load the replay of the game).

The idea is to gather information, about the moves (maybe just the texts instead of really going through the replay it self) that each player made.


# Installation
**TODO**: run spiders in a docker container.

*OBS:* You sould be inside `gbarena_gatherer` directory to follow this instructions.

## Ensure you have lxml libs installed in your OS, ex (ubuntu 14.04):
```bash
$ sudo apt-get install libxml2-dev libxslt1-dev python-lxml
```

## Install python packages (preferably inside a python virtualenv)
```bash
$ pip install -r requirements.txt
```

# Running spider

## Start containers:
```bash
$ docker-compose up -d
```
## Run spider
```bash
$ scrapy crawl <spidername>
```
