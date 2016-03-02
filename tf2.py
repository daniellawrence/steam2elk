#!/usr/bin/env python

import os
import re
import math
import argparse
import time
import requests
import collections
import json
from datetime import date


DATE_TIME = "(?P<date>.+?) - (?P<time>.*):"
PLAYER = '"(?P<player_name>.+?)<(?P<player_id>\\d+)><(?P<player_steam>.+?)><(?P<player_team>.+?)>"'
PLAYER_ATTACKER = PLAYER.replace('player', 'attacker')
PLAYER_VICTIM = PLAYER.replace('player', 'victim')
TEAM = '"(?P<team_name>.+?)"'
ROLE = '"(?P<role>.+?)"'
WEAPON = '"(?P<weapon>.+?)"'
TRIGGER_NAME = '"(?P<trigger_name>.+?)"'
OBJECT = '\(object "(?P<object>.+?)"\)'
OBJECT_WEAPON = '\(weapon "(?P<weapon>.+?)"\)'
OBJECT_OWNER = "\(objectowner {PLAYER_VICTIM}\)".format(**locals())

player_re = re.compile(PLAYER)

# postion's
_POSITION = '\(__position "(?P<__position_x>[-+]?\\d+) (?P<__position_y>[-+]?\\d+) (?P<__position_z>[-+]?\\d+)"\)'
POSITION = _POSITION.replace('__', '')
ASSISTER_POSITION =  _POSITION.replace('__', 'assister_')
VICTIM_POSITION = _POSITION.replace('__', 'victim_')
ATTACKER_POSITION = _POSITION.replace('__', 'attacker_')

position_re = re.compile(POSITION)
assister_position_re = re.compile(POSITION)
victim_position_re = re.compile(POSITION)
attacker_position_re = re.compile(POSITION)

CP = '\(cp "(?P<cp_id>.+?)"\) \(cpname "(?P<cp_name>.+?)"\)'
CUSTOM_KILL = '\(customkill "(?P<custom_kill>.+?)"\)'
HEALING = '\(healing "(?P<healing>\\d+)"\) \(ubercharge "(?P<ubercharge>\\d+)"\)'
ASSIST_KILL = '"kill assist"'

healing_re = re.compile(HEALING)

# -------------------------------------------------------------------------

# Team switching
# L 03/01/2016 - 23:28:10: "Numnutz<3><BOT><Unassigned>" joined team "Red
team_switch_string = "L {DATE_TIME} {PLAYER} joined team {TEAM}".format(**locals())
team_switch_re = re.compile(team_switch_string)

# Role switching
# L 03/01/2016 - 23:28:10: "Numnutz<3><BOT><Red>" changed role to "scout"
role_switch_string = "L {DATE_TIME} {PLAYER} changed role to {ROLE}".format(**locals())
role_switch_re = re.compile(role_switch_string)

# Triggers
# L 03/01/2016 - 23:28:28: "Freakin' Unbelievable<52><BOT><Blue>" triggered "player_builtobject" (object "OBJ_TELEPORTER") (position "-299 -4294 192")
trigger_string = "L {DATE_TIME} {PLAYER_ATTACKER} triggered {TRIGGER_NAME} {OBJECT} {POSITION}".format(**locals())
trigger_re = re.compile(trigger_string)

# Killed
# L 03/01/2016 - 23:29:07: "GLaDOS<33><BOT><Red>" killed "Aperture Science Prototype XR7<35><BOT><Blue>" with "scattergun" (attacker_position "-82 -167 296") (victim_position "-196 150 296")
killed_string = "L {DATE_TIME} {PLAYER_ATTACKER} killed {PLAYER_VICTIM} with {WEAPON} {ATTACKER_POSITION} {VICTIM_POSITION}".format(**locals())
killed_re = re.compile(killed_string)

# kill assist
# L 03/01/2016 - 23:29:07: "One-Man Cheeseburger Apocalypse<43><BOT><Red>" triggered "kill assist" against "Aperture Science Prototype XR7<35><BOT><Blue>" (assister_position "856 28 297") (attacker_position "-82 -167 296") (victim_position "-196 150 296")
#  03/01/2016 - 23:46:53: "AimBot<107><BOT><Blue>" triggered "kill assist" against "One-Man Cheeseburger Apocalypse<114><BOT><Red>" (assister_position "-126 -540 53") (attacker_position "98 -537 0") (victim_position "8 -256 11")

kill_assist_string = "L {DATE_TIME} {PLAYER_ATTACKER} triggered {TRIGGER_NAME} against {PLAYER_VICTIM} {ASSISTER_POSITION} {ATTACKER_POSITION} {VICTIM_POSITION}".format(**locals())
kill_assist_re = re.compile(kill_assist_string)


# Captureblocked
# L 03/01/2016 - 23:29:15: "Companion Cube<42><BOT><Blue>" triggered "captureblocked" (cp "2") (cpname "#Badlands_cap_cp3") (position "-261 1 466")
captureblocked_string = "L {DATE_TIME} {PLAYER_ATTACKER} triggered {TRIGGER_NAME} {CP} {POSITION}".format(**locals())
captureblocked_re = re.compile(captureblocked_string)

# customkill
# L 03/01/2016 - 23:29:23: "Archimedes!<54><BOT><Red>" killed "Kill Me<56><BOT><Blue>" with "knife" (customkill "backstab") (attacker_position "483 380 276") (victim_position "435 351 254")
kill_custom_string = "L {DATE_TIME} {PLAYER_ATTACKER} killed {PLAYER_VICTIM} with {WEAPON} {CUSTOM_KILL} {ATTACKER_POSITION} {VICTIM_POSITION}".format(**locals())
kill_custom_re = re.compile(kill_custom_string)

# Trigger player
# L 03/01/2016 - 23:29:24: "Saxton Hale<38><BOT><Blue>" triggered "player_extinguished" against "Crazed Gunman<50><BOT><Blue>" with "tf_weapon_medigun" (attacker_position "-671 20 408") (victim_position "-748 -132 348")
trigger_player_string = "L {DATE_TIME} {PLAYER_ATTACKER} triggered {TRIGGER_NAME} against {PLAYER_VICTIM} with {WEAPON} {ATTACKER_POSITION} {VICTIM_POSITION}".format(**locals())
trigger_player_re = re.compile(trigger_player_string)

# Suicide
# L 03/01/2016 - 23:29:30: "The G-Man<61><BOT><Red>" committed suicide with "tf_projectile_rocket" (attacker_position "106 197 89")
suicide_string = "L {DATE_TIME} {PLAYER_VICTIM} committed suicide with {WEAPON} {ATTACKER_POSITION}".format(**locals())
suicide_re = re.compile(suicide_string)

# medic_death
# L 03/01/2016 - 23:29:34: "Divide by Zero<47><BOT><Red>" triggered "medic_death" against "Saxton Hale<38><BOT><Blue>" (healing "981") (ubercharge "0")
medic_death_string = "L {DATE_TIME} {PLAYER_ATTACKER} triggered {TRIGGER_NAME} against {PLAYER_VICTIM} {HEALING}".format(**locals())
medic_death_re = re.compile(medic_death_string)

# trigger self
# L 03/01/2016 - 23:31:54: "Saxton Hale<38><BOT><Blue>" triggered "chargedeployed"
trigger_self_string = "L {DATE_TIME} {PLAYER_ATTACKER} triggered {TRIGGER_NAME}".format(**locals())
trigger_self_re = re.compile(trigger_self_string)

# trigger_builds
# L 03/01/2016 - 23:28:28: "Freakin' Unbelievable<52><BOT><Blue>" triggered "player_builtobject" (object "OBJ_TELEPORTER") (position "-299 -4294 192")
build_string = "L {DATE_TIME} {PLAYER} triggered {TRIGGER_NAME} {OBJECT} {POSITION}".format(**locals())
build_re = re.compile(build_string)

# killl object
# L 03/01/2016 - 23:29:45: "Divide by Zero<47><BOT><Red>" triggered "killedobject" (object "OBJ_SENTRYGUN") (weapon "minigun") (objectowner "Freakin' Unbelievable<52><BOT><Blue>") (attacker_position "-364 -327 201")
killobject_string = "L {DATE_TIME} {PLAYER_ATTACKER} triggered {TRIGGER_NAME} {OBJECT} {OBJECT_WEAPON} {OBJECT_OWNER} {ATTACKER_POSITION}".format(**locals())
killobject_re = re.compile(killobject_string)

re_map = [
    killobject_re,
    team_switch_re,
    role_switch_re,
    trigger_re,
    trigger_player_re,
    killed_re,
    kill_assist_re,
    captureblocked_re,
    kill_custom_re,
    suicide_re,
    medic_death_re,
    trigger_self_re,
]



def search_for_new_logfile(path="tests/"):
    if not os.path.exists("{}".format(path)):
        return None
    all_logs = sorted(os.listdir(path))
    most_recent_log = all_logs[-1]
    log_path = os.path.join(path, most_recent_log)
    return open(log_path)


def calc_distance(killer_position, victim_position):
    (x1, y1, z1) = [int(x) for x in killer_position.split()]
    (x2, y2, z2) = [int(x) for x in victim_position.split()]

    distance_units = math.sqrt(
        ((x1-x2)**2) + ((y1-y2)**2) + ((z1-z2)**2)
    )

    # distance is measured in inches...
    distance_meters = (distance_units * 2.540) / 100

    return {
        'killer_position': {'x': x1, 'y': y1, 'z': z1},
        'victim_position': {'x': x2, 'y': y2, 'z': z2},
        'distance_units': distance_units,
        'distance_meters': distance_meters
    }


def process_log_line(line):

    if not line.startswith('L '):
        return {}

    if 'Log file started' in line:
        return {}

    if 'connected, address' in line:
        return {}
    if 'STEAM USERID' in line:
        return {}
    if 'entered the game' in line:
        return {}

    if ' disconnected ' in line:
        return {}

    if 'server_cvar:' in line:
        return {}
    if 'changed name to' in line:
        return {}

    if 'Round_Start' in line:
        return {}

    if ' stuck ' in line:
        return {}

    if 'Round_Win' in line:
        return {}

    if 'Round_' in line:
        return {}

    if 'current score' in line:
        return {}

    if 'Log file ' in line:
        return {}

    if 'Loading map' in line:
        return {}

    if 'cvars' in line:
        return {}

    if 'tf_' in line:
        return {}

    if 'sv_' in line:
        return {}

    if 'mp_' in line:
        return {}

    if '" = "' in line:
        return {}

    if 'numcappers' in line:
        return {}
    line = line.strip()

    m = None
    for re in re_map:
        m = re.match(line)
        if m:
            return m.groupdict()

    # raise Exception("lulz: >>{}<<".format(line))


def post_event_to_elasticsearch(event, elasticsearch_url):
    r = requests.post(elasticsearch_url, auth=('bb', 'bb'), data=json.dumps(event))
    print(r)
    print(r.text)
    return r


def main(log_dir, elasticsearch_url=None, interval=1):
    current_log = search_for_new_logfile(log_dir)

    # print "current_log: {0}".format(current_log)

    while True:
        new_lines = current_log.readlines()
        for line in new_lines:
            event = process_log_line(line)

            if not event:
                continue

            if elasticsearch_url:
                print("posting event to elasticsearch")
                post_event_to_elasticsearch(event, elasticsearch_url)
            else:
                print(json.dumps(event))
                pass

        print("... processed {0} lines".format(len(new_lines)))
        time.sleep(interval)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--log-dir", type=str, required=None)
    parser.add_argument("-e", "--elasticsearch-url", type=str, default=None)
    parser.add_argument("-i", "--interval", type=int, default=1)
    args = parser.parse_args()

    # Allow easy testing.
    if not args.log_dir:
        args.log_dir = "tests/"

    main(log_dir=args.log_dir,
         elasticsearch_url=args.elasticsearch_url,
         interval=args.interval
    )
