#!/usr/bin/env python
import pytest
from tf2 import *

def test_date():
    line = '03/01/2016 - 23:28:10:'
    time_re = re.compile(DATE_TIME)
    d =  time_re.match(line).groupdict()
    assert d['date'] == '03/01/2016'
    assert d['time'] == '23:28:10'


def test_position():
    line = '(position "-299 -4294 192")'
    print(line)
    print(POSITION)

    d = position_re.match(line).groupdict()
    assert d['position_x'] == '-299'
    assert d['position_y'] == '-4294'
    assert d['position_z'] == '192'

def test_player():
    line = '"Numnutz<3><BOT><Red>"'
    print(line)
    print(PLAYER)
    d = player_re.match(line).groupdict()
    assert d
    assert d['player_name'] == 'Numnutz'
    assert d['player_id'] == '3'
    assert d['player_steam'] == 'BOT'
    assert d['player_team'] == 'Red'


def test_joined_test():
    line = 'L 03/01/2016 - 23:28:10: "Numnutz<3><BOT><Unassigned>" joined team "Red"'
    print(line)
    print(team_switch_string)
    d = team_switch_re.match(line).groupdict()
    assert d['date'] == '03/01/2016'
    assert d['time'] == '23:28:10'
    assert d['player_name'] == 'Numnutz'
    assert d['team_name'] == 'Red'

def test_role_switch():
    line = 'L 03/01/2016 - 23:28:10: "Numnutz<3><BOT><Red>" changed role to "scout"'
    print(line)
    print(role_switch_string)
    d = role_switch_re.match(line).groupdict()
    assert d['date'] == '03/01/2016'
    assert d['time'] == '23:28:10'
    assert d['player_name'] == 'Numnutz'
    assert d['role'] == 'scout'


def test_killed():
    line = 'L 03/01/2016 - 23:29:07: "GLaDOS<33><BOT><Red>" killed "Aperture Science Prototype XR7<35><BOT><Blue>" with "scattergun" (attacker_position "-82 -167 296") (victim_position "-196 150 296")'
    print(line)
    print(killed_string)
    d = killed_re.match(line).groupdict()
    assert d['date'] == '03/01/2016'
    assert d['time'] == '23:29:07'
    assert d['attacker_name'] == 'GLaDOS'
    assert d['victim_name'] == 'Aperture Science Prototype XR7'
    assert d['weapon'] == 'scattergun'
    #
    assert d['attacker_position_x'] == '-82'
    assert d['attacker_position_y'] == '-167'
    assert d['attacker_position_z'] == '296'
    #
    assert d['victim_position_x'] == '-196'
    assert d['victim_position_y'] == '150'
    assert d['victim_position_z'] == '296'


def testing_healing():
    line = '(healing "981") (ubercharge "0")'
    d = healing_re.match(line).groupdict()
    assert d['healing'] == '981'
    assert d['ubercharge'] == '0'


def test_medic_death():
    line = 'L 03/01/2016 - 23:29:34: "Divide by Zero<47><BOT><Red>" triggered "medic_death" against "Saxton Hale<38><BOT><Blue>" (healing "981") (ubercharge "0")'
    d = medic_death_re.match(line).groupdict()
    assert d
    assert d['trigger_name'] == 'medic_death'
    assert d['attacker_name'] == 'Divide by Zero'
    assert d['victim_name'] == 'Saxton Hale'
    assert d['healing'] == '981'
    assert d['ubercharge'] == '0'


def test_killedobject():
    line = 'L 03/01/2016 - 23:29:45: "Divide by Zero<47><BOT><Red>" triggered "killedobject" (object "OBJ_SENTRYGUN") (weapon "minigun") (objectowner "Freakin\' Unbelievable<52><BOT><Blue>") (attacker_position "-364 -327 201")'
    d = killobject_re.match(line).groupdict()
    print(d)
    assert d
    assert d['attacker_name'] == 'Divide by Zero'
    assert d['victim_name'] == 'Freakin\' Unbelievable'
    assert d['weapon'] == 'minigun'
    assert d['object'] == 'OBJ_SENTRYGUN'

