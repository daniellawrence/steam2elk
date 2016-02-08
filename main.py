#!/usr/bin/env python

import os
import re
import math
import argparse
import time
import requests


kill_str = r'L (.*?) - (.*?): "(.+?)<.+?" \[(.+?)\].+?"(.+?)<.+?" \[(.+?)\].+?"(.+?)"(.*)'
kill_re = re.compile(kill_str)

purchase_str = r'L (.*?) - (.*?): "(.+?)<.+?" purchased "(.+?)"'
purchase_re = re.compile(purchase_str)

assist_str = r'L (.*?) - (.*?): "(.+?)<.+?" assisted killing "(.+?)<.+?"'
assist_re = re.compile(assist_str)


def search_for_new_logfile(path):
    if not os.path.exists("{}".format(path)):
        return None
    all_logs = sorted(os.listdir(path))
    most_recent_log = all_logs[-1]
    log_path = os.path.join(path, most_recent_log)
    return open(log_path)


def calc_distance(killer_position, victim_position):
    (x1, y1, z1) = [int(x) for x in killer_position.split()]
    (x2, y2, z2) = [int(x) for x in victim_position.split()]

    distance = math.sqrt(
        ((x1-x2)**2) + ((y1-y2)**2) + ((z1-z2)**2)
    )

    return {
        'killer_position': {'x': x1, 'y': y1, 'z': z1},
        'victim_position': {'x': x2, 'y': y2, 'z': z2},
        'distance': distance
    }


def process_log_line(line):

    if 'server_cvar' in line:
        return {}

    if '" = "' in line:
        return {}

    purchase_match = purchase_re.match(line)
    if purchase_match:
        (daystamp, timestamp, player, item) = purchase_match.groups()
        return {
            'type': 'purchase',
            'timestamp': '{} {}'.format(daystamp, timestamp),
            'player': player,
            'item': item
        }

    assist_match = assist_re.match(line)
    if assist_match:
        (daystamp, timestamp, player, victim) = assist_match.groups()
        return {
            'type': 'assist',
            'timestamp': '{} {}'.format(daystamp, timestamp),
            'player': player,
            'victim': victim
        }

    kill_match = kill_re.match(line)
    if kill_match:
        (daystamp, timestamp, killer, killer_position,
         victim, victim_position, weapon, raw_tags) =  kill_match.groups()
    
        tags = []
        if raw_tags:
            raw_tags = re.match(' \((.+?)\)', raw_tags)
            tags = list(raw_tags.groups())
            if ' ' in tags[0]:
                tags += tags[0].split()

        event = {
            'type': 'kill',
            'timestamp': '{} {}'.format(daystamp, timestamp),
            'player': killer,
            'victim': victim,
            'weapon': weapon,
            'tags': tags,
        }
        event.update(calc_distance(killer_position, victim_position))
        return event


def post_event_to_elasticsearch(event, elasticsearch_url):
    return requests.post(elasticsearch_url, data=event)


def main(log_dir, elasticsearch_url=None, interval=1):
    file_position = -1
    current_log = search_for_new_logfile(log_dir)

    while True:
        new_lines = current_log.readlines()
        for line in new_lines:
            event = process_log_line(line)
            if not event:
                continue

            if elasticsearch_url:
                post_event_to_elasticsearch(event, elasticsearch_url)
            else:
                print(event)
                pass

        print(".")
        time.sleep(interval)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--log-dir", type=str, required=True)
    parser.add_argument("-e", "--elasticsearch-url", type=str, default=None)
    parser.add_argument("-i", "--interval", type=int, default=1)
    args = parser.parse_args()
    main(log_dir=args.log_dir, elasticsearch_url=args.elasticsearch_url, interval=args.interval)
