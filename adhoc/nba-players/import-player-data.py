#!/usr/local/bin/python3

from doltpy.core import Dolt

import pandas
import random
import time
import os
import csv

from pprint import pprint

from nba_api.stats.static import teams
from nba_api.stats.static import players

from nba_api.stats.endpoints import playercareerstats

table_map = {
    'CareerTotalsAllStarSeason': 'career_totals_allstar',
    'CareerTotalsPostSeason': 'career_totals_post_season',
    'CareerTotalsRegularSeason': 'career_totals_regular_season',
    'SeasonRankingsPostSeason': 'rankings_post_season',
    'SeasonRankingsRegularSeason': 'rankings_regular_season',
    'SeasonTotalsAllStarSeason': 'season_totals_allstar',
    'SeasonTotalsPostSeason': 'season_totals_post_season',
    'SeasonTotalsRegularSeason': 'season_totals_regular_season'
    }

repo = Dolt('.')

count = 1
base = 'player-data'
player_ids = os.listdir(base)
total = len(player_ids)
for player_id in player_ids:
    print(f'{count}/{total}: {player_id}')

    for csvfile in os.listdir(f'{base}/{player_id}'):
        table_lookup = csvfile.split('.')[0]
        table_name = table_map.get(table_lookup)

        if not table_name: continue

        csvpath = f'{base}/{player_id}/{csvfile}'

        with open(csvpath, newline='') as csvhandle:
            csvreader = csv.reader(csvhandle)

            header = next(csvreader)

            pks = [col for col in header if '_id' in col]

            repo.bulk_import(table_name,
                             open(csvpath),
                             pks,
                             'update')
    count += 1

