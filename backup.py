import csv
import json
import os
import sys
from datetime import datetime

import pandas as pd

import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials

from api_spotify import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI

# DEFINE USER INFORMATION
USER_LOOKUP = {
    'notbobbobby': 'Calvin',
    'deedanvy': 'Danvy',
    'c.bochulak': 'Charlotte',
    'eriica_k': 'Erica',
    '12180635139': 'Aiden',
    'danthemank': 'Danielle',
    'deanbo007': 'Dean',
    'chickenrox1': 'Derek',
    'indieairyt': 'IndieAir',
    'j_bus195': 'Jennifer',
    'liza_boch02': 'Liza'}

SCOPE = ','.join(['playlist-read-private',
                  'playlist-read-collaborative',
                  'playlist-modify-public',
                  # 'playlist=modify-private',
                  'user-library-read',
                  'user-read-recently-played'])

DATETIME_FORMAT_DEFAULT = '%Y-%m-%dT%H:%M:%SZ'
DATETIME_FORMAT_FILENAME = '%Y-%m-%dT%H-%M-%SZ'
DATETIME_FORMAT_SHORT = '%Y-%m-%d'


def get_spotify_instance(user_id, scope=SCOPE):
    token = util.prompt_for_user_token(
        user_id,
        scope=scope,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI)

    return spotipy.Spotify(auth=token)


def get_user_playlists(user_id):
    simple_output('Finding All Playlists')
    simple_output('User', user_id)
    sp = get_spotify_instance(user_id)

    discover_user = None
    playlists = []
    result = sp.user_playlists(user_id, offset=0)
    while True:
        for playlist in result['items']:
            if playlist['name'] == '.':
                discover_user = None
                continue
            try:
                _, discover_user = playlist['name'].split(',')
            except ValueError:
                playlist_name = '{} ({})'.format(playlist['name'], discover_user) \
                    if discover_user is not None else playlist['name']
                
                simple_output('Formatting Playlist', playlist_name, flush=True)

                playlists.append(_format_playlist(
                    playlist, sp, user_id, discover_user=discover_user))
        
        if not result['next']:
            break
        
        result = sp.next(result)
    
    saved_tracks = {
        'name': 'Saved Tracks',
        'owner': {'id': user_id},
        'id': None,
        'uri': None}
    playlists.append(_format_playlist(saved_tracks, sp, user_id))

    playlists = list(filter(None, playlists))

    simple_output('')
    simple_output('Playlists Found', len(playlists))
    simple_output('Done!')
    simple_output('-'*40)
    
    return pd.DataFrame(playlists)


def get_user_tracks(user_id, playlists=None):
    simple_output('Finding All Tracks')
    simple_output('User', user_id)    
    sp = get_spotify_instance(user_id)

    if playlists is None:
        playlists = get_user_playlists(user_id)

    tracks = []
    for _, playlist in playlists.iterrows():
        if playlist['name'] == 'Saved Tracks':
            result = sp.current_user_saved_tracks(limit=50)
        else:
            result = sp.user_playlist_tracks(user_id, playlist['id'])

        playlist_name = '{} ({})'.format(playlist['name'], playlist['discover_user']) \
            if playlist['discover_user'] is not None else playlist['name']

        simple_output('Getting Tracks', playlist_name, flush=True)

        tracks.extend(list(map(
            lambda t: _format_track(t, playlist, user_id), result['items'])))
        while result['next']:
            result = sp.next(result)
            tracks.extend(list(map(
                lambda t: _format_track(t, playlist, user_id), result['items'])))
    
    tracks = list(filter(None, tracks))

    simple_output('')
    simple_output('Tracks Found', len(tracks))
    simple_output('Done!')
    simple_output('-'*40)

    return pd.DataFrame(tracks)


def get_user_unique_tracks_and_features(user_id, tracks=None):
    simple_output('Filtering For Unique Tracks')
    simple_output('User', user_id)
    sp = get_spotify_instance(user_id)

    if tracks is None:
        tracks = get_user_tracks(user_id)

    unique_tracks = tracks.copy()
    unique_tracks.drop(['playlist_id', 'added_by', 'added_at'], axis=1, inplace=True)
    unique_tracks.drop_duplicates(subset='id', inplace=True)

    n = len(unique_tracks)
    features = []
    for i in range(0, n, 50):
        ii = (i + 50) if (i + 50) < n else n
        
        simple_output('{} / {}'.format(ii, n), flush=True)
        result = sp.audio_features(unique_tracks.id[i:ii].tolist())
        features.extend(list(map(_format_feature, result)))
    
    features = list(filter(None, features))
    features = pd.DataFrame(features)
    unique_tracks = unique_tracks.merge(features, how='outer', on='id')

    simple_output('')
    simple_output('Done!')
    simple_output('-'*40)

    return unique_tracks


def get_listening_history(user_id):
    simple_output('Gathering Listening History')
    simple_output('User', user_id)
    sp = get_spotify_instance(user_id, SCOPE)

    result = sp._get('me/player/recently-played', limit=50)
    history = list(map(
        lambda h: _format_historical_track(h, user_id), result['items']))
    
    simple_output('Done!')
    simple_output('-'*40)

    return pd.DataFrame(history)


def simple_output(*args, flush=False):
    end = '' if flush else '\n'
    if len(args) == 1:
        print('\r' + args[0] + ' '*24, end=end, flush=flush)
    elif len(args) == 2:
        print('\r' + '{:<24}{}'.format(args[0] + ':', args[1]) + ' '*24, end=end, flush=flush)
    

def _format_playlist(playlist, sp, user_id, discover_user=None):
    # DETERMINE THE PLAYLIST CREATION DATE
    if playlist['name'] == 'Saved Tracks':
        result = sp.current_user_saved_tracks(limit=50)
    else:
        result = sp.user_playlist_tracks(user_id, playlist['id'])
    
    tracks = result['items']
    while result['next']:
        result = sp.next(result)
        tracks.extend(result['items'])

    track_ids = [{'track_id': track['track']['id']}
        for track in tracks if track['track'] is not None]
    track_dates = [datetime.strptime(track['added_at'], DATETIME_FORMAT_DEFAULT)
        for track in tracks]

    if len(track_ids) == 0:
        return None

    date_created = min(track_dates).strftime(DATETIME_FORMAT_DEFAULT)

    # FORMAT PLAYLIST OBJECT
    new_playlist = {
        'name': playlist['name'],
        'display_name': USER_LOOKUP[user_id] if user_id in USER_LOOKUP else None,
        'user_id': user_id,
        'owner_id': playlist['owner']['id'],
        'discover_user': discover_user,
        'id': playlist['id'],
        'uri': playlist['uri'],
        'is_original': (user_id == playlist['owner']['id']),
        'tracks': track_ids,
        'created': date_created}

    return new_playlist


def _format_track(track, playlist, user_id):
    if track['track'] is None:
        return None
    if track['track']['id'] is None:
        return None
    
    track_details = track['track']
    return {
        'name': track_details['name'],
        'playlist_id': playlist['id'],
        'display_name': USER_LOOKUP[user_id] if user_id in USER_LOOKUP else None,
            'user_id': user_id,
        'id': track_details['id'],
        'uri': track_details['uri'],
        'album': {
            'name': track_details['album']['name'], 
            'release_date': track_details['album']['release_date'], 
            'uri': track_details['album']['uri']},
        'artists': [{'name': artist['name'], 'uri': artist['uri']} for artist in track_details['artists']],
        'isrc': track_details['external_ids']['isrc'] if 'isrc' in track_details['external_ids'] else None,
        'added_by': track['added_by']['id'] if 'added_by' in track else None,
        'added_at': track['added_at'] if 'added_at' in track else None}


def _format_feature(feature):
    if feature is None:
        return None

    new_feature = {'id': feature['id']}
    del feature['id']
    del feature['uri']
    del feature['track_href']
    del feature['type']
    del feature['analysis_url']
    new_feature['features'] = feature
    return new_feature


def _format_historical_track(track, user_id):
    track_details = track['track']
    context = track.pop('context')
    playlist_id = context['uri'].split('.')[-1] if context is not None else None
    return {
        'name': track_details['name'],
        'playlist_id': playlist_id,
        'display_name': USER_LOOKUP[user_id] if user_id in USER_LOOKUP else None,
        'user_id': user_id,
        'id': track_details['id'],
        'uri': track_details['uri'],
        'album': {
            'name': track_details['album']['name'], 
            'uri': track_details['album']['uri']},
        'artists': [{'name': artist['name'], 'uri': artist['uri']} for artist in track_details['artists']],
        'isrc': track_details['external_ids']['isrc'] if 'isrc' in track_details['external_ids'] else None,
        'played_at': track['played_at'] if 'played_at' in track else None}


if __name__ == '__main__':
    USER_ID = 'notbobbobby'
    playlists = get_user_playlists(USER_ID)
    playlists.to_json('{}_playlists.json'.format(USER_ID), orient='records', lines=True)
    tracks = get_user_tracks(USER_ID, playlists=playlists)
    tracks.to_json('{}_tracks.json'.format(USER_ID), orient='records', lines=True)
    features = get_user_unique_tracks_and_features(USER_ID, tracks=tracks)
    features.to_json('{}_features.json'.format(USER_ID), orient='records', lines=True)
    pass
