import json
import os
from argparse import ArgumentParser
from datetime import datetime

import pandas as pd

import backup
from backup import (DATETIME_FORMAT_FILENAME, DATETIME_FORMAT_SHORT,
                    DATETIME_FORMAT_YR, DATETIME_FORMAT_YR_MTH,
                    get_spotify_instance, simple_output)

LISTENING_HISTORY_DIRECTORY = '_history'
SPOTIFY_LIBRARY_DIRECTORY = '_db'


def cli():
    parser = ArgumentParser()
    parser.add_argument('archive',
        type=str,
        choices=['DISCOVER', 'HISTORY', 'LIBRARY'])
    parser.add_argument('-d', '--forced-date',
        type=str,
        dest='date')
    parser.add_argument('-u', '--user_id',
        type=str,
        default='notbobbobby')
    return parser.parse_args()


def archive_discover_playlists(args):
    user_id = args.user_id
    date = datetime.now().strftime(DATETIME_FORMAT_SHORT)

    simple_output('-'*40)
    simple_output('Discover Identifier and Spotify Creation Observer (DISCO)')
    simple_output('User', user_id)
    simple_output('Date', date)

    sp = get_spotify_instance(user_id)
    playlists = sp.user_playlists(user_id, offset=0)
    
    discover_playlists = [
        playlist for playlist in playlists['items']
            if playlist['name'] == 'Discover Weekly']

    simple_output('Playlists Found', len(discover_playlists))
    simple_output('-'*40)

    # CREATE PLAYLISTS FOR EACH DISCOVER WEEKLY
    for i, playlist in enumerate(reversed(discover_playlists)):
        simple_output('Created: {}/{}'.format(i+1, len(discover_playlists)), flush=True)

        owner_id = playlist['owner']['id']
        playlist_id = playlist['id']

        tracks = sp.user_playlist_tracks(owner_id, playlist_id=playlist_id)
        uris = [track['track']['uri'] for track in tracks['items']]

        new_playlist = sp.user_playlist_create(user_id, date, public=False)
        new_playlist_id = new_playlist['id']
        sp.user_playlist_add_tracks(user_id, new_playlist_id, uris)
        
    simple_output('')
    simple_output('Done!')


def archive_spotify_library(args):
    user_id = args.user_id
    date = datetime.now().strftime(DATETIME_FORMAT_SHORT)

    simple_output('-'*40)
    simple_output('Archiving Spotify Library (ASL)')
    simple_output('User', user_id)
    simple_output('Date', date)
    simple_output('-'*40)

    playlists = backup.get_user_playlists(user_id, discover_database=False)
    tracks = backup.get_user_tracks(user_id, playlists=playlists)
    features = backup.get_user_unique_tracks_and_features(user_id, tracks=tracks)

    output_directory = os.path.join(
        os.path.dirname(__file__),
        SPOTIFY_LIBRARY_DIRECTORY,
        user_id, date)
    _chdir(output_directory)

    playlists_name = '{}_{}_playlists.json'.format(user_id, date)
    tracks_name = '{}_{}_tracks.json'.format(user_id, date)
    features_name = '{}_{}_features.json'.format(user_id, date)

    playlists.to_json(playlists_name, orient='records', lines=True)
    tracks.to_json(tracks_name, orient='records', lines=True)
    features.to_json(features_name, orient='records', lines=True)

    simple_output('Database Location', output_directory)
    simple_output('Playlists', playlists_name)
    simple_output('Tracks', tracks_name)
    simple_output('Features', features_name)
    simple_output('-'*40)

    simple_output('Done!')


def archive_listening_history(args):
    user_id = args.user_id
    date = datetime.now().strftime(DATETIME_FORMAT_FILENAME)

    simple_output('-'*40)
    simple_output('Listening Interval Tracker (LIT)')
    simple_output('User', user_id)
    simple_output('Date', date)
    simple_output('-'*40)
    
    history = backup.get_listening_history(user_id)

    output_directory = os.path.join(
        os.path.dirname(__file__),
        LISTENING_HISTORY_DIRECTORY,
        user_id)
    _chdir(output_directory)

    # STORE TO MONTHLY DIRECTORY
    current_month = datetime \
        .strptime(date, DATETIME_FORMAT_FILENAME) \
        .strftime(DATETIME_FORMAT_YR_MTH)
    history_month = '{}_{}_history.json'.format(user_id, current_month)

    if not os.path.exists(history_month):
        current_history = history
    else:
        current_history = pd.read_json(history_month, orient='records', lines=True)
        current_history = pd.concat([current_history, history])
        current_history.drop_duplicates(subset='played_at', inplace=True)
    
    current_history.to_json(history_month, orient='records', lines=True)

    # STORE TO YEARLY DIRECTORY
    current_year = datetime \
        .strptime(date, DATETIME_FORMAT_FILENAME) \
        .strftime(DATETIME_FORMAT_YR)
    history_year = '{}_{}_history.json'.format(user_id, current_year)

    if not os.path.exists(history_year):
        current_history = history
    else:
        current_history = pd.read_json(history_year, orient='records', lines=True)
        current_history = pd.concat([current_history, history])
        current_history.drop_duplicates(subset='played_at', inplace=True)

    current_history.to_json(history_year, orient='records', lines=True)

    simple_output('History Location', output_directory)
    simple_output('History (Month)', history_month)
    simple_output('History (Year)', history_year)

    simple_output('Done!')


def _chdir(path):
    if not os.path.exists(path):
        _mkdir(path)
    os.chdir(path)


def _mkdir(path):
    if not os.path.exists(path):
        _mkdir(os.path.split(path)[0])
        os.mkdir(path)
    return path


if __name__ == '__main__':
    ARCHIVE_POINTER = {
        'DISCOVER': archive_discover_playlists,
        'HISTORY': archive_listening_history,
        'LIBRARY': archive_spotify_library}

    args = cli()
    ARCHIVE_POINTER[args.archive](args)
