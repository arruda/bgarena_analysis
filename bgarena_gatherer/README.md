# BGArena Gatherer
Collects information from pt.boardgamearena and saves them in a Postgres database.

## Spiders
### bgarenatables
Spider that collects basic information about all game tables, from a recent game table ID to  the  id `280482` (this was one very old table that was still working the gasic info page).

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

### bgarena_race_for_galaxy_moves
Spider specific for a Race for The galaxy tables that gathers information abount the moves of the crawled tables (only works with recent tables since old ones dont have play log).

This spider can make use of the basic information gathered by the `bgarenatables` spider, to know which table of the given game is OK to be crawled (many old tables are using some pretty old version so they won't load the replay of the game).

It will basically get only the most recent crawled tables that have a `Finished` game status.
The idea is to gather information, about the actions in each move of the game (yes, some games have many actions that occour during a single move).

Just to have an idea, in about one month, this infos on the Race for the Galaxy game, where saved as about 9MM actions in the database.

In the spider code I've already replaced the player names for player-X to make a bit more easy when needed to analyse the actions.

#### Requirements for this spider
You'll need to create a account in the boardgamearena.com site, to be able to access the page that contains the game replay (where the spider gets the actions information).

After you've created an account, **YOU HAVE TO LOG IN TO IT AND PLAY ONE GAME IN THIS ACCOUNT** (you can abandon it, but you need to start one game). If you don't do this, each time the crawler enters a game page, it will actually be redirected to a page that sugest it to play the first game, and so it won't gather any info.

#### Running this spider:
You need to set you boardgamearena account and password as environment variables (`ACC` and `PASS` envvars) before running the crawler, ex:

```bash
$ ACC="mycrawleraccount@domain.com" PASS="verysecret" scrapy crawl bgracemoves
```

#### Information Gathered:

Example:

```python
{
'creation_time': u'11/02/2011',
 'estimated_duration': u'10 mn',
 'game': u"Race for the Galaxy",
 'game_table_id': 123456, # id refering to the gametable in this database, not in the site
 'move_number': 6,
 'move_date': "8:18:21 PM GMT",
 'action': "player-2 gains 4 with Galactic Federation"
 }
```

# Installation
**TODO**: run spiders in a docker container.

*OBS:* You sould be inside `bgarena_gatherer` directory to follow this instructions.

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
