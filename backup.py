import os
import sys
from datetime import datetime

import pandas as pd

import spotipy
import spotipy.util as util

from api_spotify import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI

# DEFINE USER INFORMATION
USER_LOOKUP = {
    'notbobbobby': 'Calvin',
    'deedanvy': 'Danvy',
    'c.bochulak': 'Charlotte',
    'eriica_k': 'Erica',
    'zzalan': 'Alan',
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
                  # 'playlist-modify-private',
                  'user-library-read',
                  'user-read-recently-played'])

DATETIME_FORMAT_DEFAULT = '%Y-%m-%dT%H:%M:%SZ'
DATETIME_FORMAT_FILENAME = '%Y-%m-%dT%H-%M-%SZ'
DATETIME_FORMAT_SHORT = '%Y-%m-%d'
DATETIME_FORMAT_YR_MTH = '%Y-%m'
DATETIME_FORMAT_YR = '%Y'


def get_spotify_instance(user_id, scope=SCOPE):
    token = util.prompt_for_user_token(
        user_id,
        scope=scope,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI)

    return spotipy.Spotify(auth=token)
    

def get_user_playlists(user_id, discover_database=False):
    simple_output('Finding All Playlists')
    simple_output('User', user_id)
    sp = get_spotify_instance(user_id)

    skipping = discover_database
    discover_id = None
    playlists = []
    result = sp.user_playlists(user_id, offset=0)
    while True:
        for playlist in result['items']:
            # We want to obtain the library OR the database (exclusive)
            if playlist['name'] == '.':
                skipping = not skipping
                continue
            if skipping:
                continue
                
            # We don't want to keep weekly/daily playlists in our library backup
            if playlist['name'] in ['Discover Weekly', 'Release Radar']:
                continue
            
            # Only try to parse the discover_id if we're looking through the database
            if discover_database:
                try:
                    _, discover_id = playlist['name'].split(',')
                    continue
                except ValueError:
                    pass
            
            # Some nice logging. Nothing special
            playlist_name = '{} ({})'.format(playlist['name'], discover_id) \
                if discover_id is not None else playlist['name']
            simple_output('Formatting Playlist', playlist_name, flush=True)

            # Add the playlist to the list
            playlists.append(_format_playlist(
                playlist, sp, user_id, discover_id=discover_id))
        
        if not result['next']:
            break
        
        result = sp.next(result)
    
    if not discover_database:
        saved_tracks = {
            'id': 'saved_tracks',
            'name': 'Saved Tracks',
            'owner': {'id': user_id, 'display_name': USER_LOOKUP[user_id]},
            'collaborative': False,
            'public': False,
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
        if playlist['playlist_name'] == 'Saved Tracks':
            result = sp.current_user_saved_tracks(limit=50)
        else:
            result = sp.user_playlist_tracks(user_id, playlist['playlist_id'])

        playlist_name = '{} ({})'.format(playlist['playlist_name'], playlist['discover_id']) \
            if 'discover_id' in playlist else playlist['playlist_name']
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
    unique_tracks.drop_duplicates(subset='track_id', inplace=True)
    unique_tracks = unique_tracks[['track_id', 'track_name']]

    n = len(unique_tracks)
    features = []
    for i in range(0, n, 50):
        ii = (i + 50) if (i + 50) < n else n
        
        simple_output('{} / {}'.format(ii, n), flush=True)
        result = sp.audio_features(unique_tracks.track_id[i:ii].tolist())
        features.extend(list(map(_format_feature, result)))
    
    features = list(filter(None, features))
    features = pd.DataFrame(features)
    unique_tracks = unique_tracks.merge(features, how='outer', on='track_id')

    simple_output('')
    simple_output('Done!')
    simple_output('-'*40)

    return unique_tracks


def get_listening_history(user_id):
    simple_output('Gathering Listening History')
    simple_output('User', user_id)
    sp = get_spotify_instance(user_id, SCOPE)

    result = sp._get('me/player/recently-played', limit=50)
    tracks = list(map(
        lambda h: _format_historical_track(h, sp, user_id), result['items']))
    tracks = pd.DataFrame(tracks)

    features = get_user_unique_tracks_and_features(user_id, tracks)

    history = pd.merge(tracks, features, how='outer', on=['track_id', 'track_name'])
    history['played_at'] = pd.to_datetime(history['played_at'])
    
    simple_output('Done!')
    simple_output('-'*40)

    return history


def simple_output(*args, flush=False):
    end = '' if flush else '\n'
    if len(args) == 1:
        print('\r' + args[0] + ' '*24, end=end, flush=flush)
    elif len(args) == 2:
        print('\r' + '{:<24}{}'.format(args[0] + ':', args[1]) + ' '*24, end=end, flush=flush)
    

def _format_playlist(playlist, sp, user_id, discover_id=None):
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

    if discover_id is not None:
        date_created = datetime \
            .strptime(playlist['name'], DATETIME_FORMAT_SHORT) \
            .strftime(DATETIME_FORMAT_DEFAULT)
    else:
        date_created = min(track_dates).strftime(DATETIME_FORMAT_DEFAULT)

    if playlist['name'] == 'Saved Tracks':
        total_tracks = result['total']
    else:
        total_tracks = playlist['tracks']['total']

    # FORMAT PLAYLIST OBJECT
    owner_id = playlist['owner']['id']
    new_playlist = {
        'playlist_id': playlist['id'],
        'playlist_name': playlist['name'],
        'owner_id': playlist['owner']['id'],
        'owner_display_name':USER_LOOKUP[owner_id] if owner_id in USER_LOOKUP else owner_id,
        'user_id': user_id,
        'user_display_name': USER_LOOKUP[user_id] if user_id in USER_LOOKUP else user_id,
        'collaborative': playlist['collaborative'],
        'public': playlist['public'],
        'total_tracks': total_tracks,
        'is_original': (user_id == playlist['owner']['id']),
        'created_at': date_created,
        'playlist_uri': playlist['uri']}
    if discover_id is not None:
        new_playlist['discover_id'] = discover_id
        new_playlist['discover_display_name'] = USER_LOOKUP[discover_id] \
            if discover_id in USER_LOOKUP else discover_id

    return new_playlist


def _format_track(track, playlist, user_id):
    if track['track'] is None:
        print('No track found for playlist', playlist['playlist_name'])
        return None
    if track['track']['id'] is None:
        print('No track found for playlist', playlist['playlist_name'])
        return None
    
    track_details = track['track']
    new_track = {
        'track_id': track_details['id'],
        'track_name': track_details['name'],
        'playlist_id': playlist['playlist_id'],
        'playlist_name': playlist['playlist_name'],
        'album': track_details['album']['name'],
        'artists': ', '.join([artist['name'] for artist in track_details['artists']]),
        'added_at': track['added_at'] if 'added_at' in track else None,
        'added_by': track['added_by']['id'] if 'added_by' in track else None,
        'release_date': track_details['album']['release_date'],
        'track_uri': track_details['uri'],
        'isrc': track_details['external_ids']['isrc'] if 'isrc' in track_details['external_ids'] else None}
    if 'discover_id' in playlist:
        new_track['added_at'] = playlist['created_at']
    
    return new_track


def _format_feature(feature):
    if feature is None:
        simple_output('No feature found')
        return None

    new_feature = {'track_id': feature['id']}
    del feature['type']
    del feature['id']
    del feature['uri']
    del feature['track_href']
    del feature['analysis_url']
    new_feature.update(feature)

    return new_feature


def _format_historical_track(track, sp, user_id):
    track_details = track['track']
    context = track.pop('context')
    if context is not None:
        context_id = context['uri'].split(':')[-1]
        
        if 'playlist' in context['uri']:
            context_type = 'playlist'
            context_name = sp.user_playlist(user_id, context_id)['name']
        elif 'album' in context['uri']:
            context_type = 'album'
            context_name = sp.album(context_id)['name']
        elif 'artist' in context['uri']:
            context_type = 'artist'
            context_name = sp.artist(context_id)['name']
        else:
            context_type = None
            context_name = None
    else:
        context_id = None
        context_type = None
        context_name = None
    
    return {
        'track_id': track_details['id'],
        'track_name': track_details['name'],
        'context_id': context_id,
        'context_name': context_name,
        'context_type': context_type,
        'album': track_details['album']['name'],
        'artists': ', '.join([artist['name'] for artist in track_details['artists']]),
        'user_id': user_id,
        'user_display_name': USER_LOOKUP[user_id] if user_id in USER_LOOKUP else None,
        'track_uri': track_details['uri'],
        'played_at': track['played_at']}


if __name__ == '__main__':
    USER_ID = 'notbobbobby'
    playlists = get_user_playlists(USER_ID)
    playlists.to_json('{}_playlists.json'.format(USER_ID), orient='records', lines=True)
    tracks = get_user_tracks(USER_ID, playlists=playlists)
    tracks.to_json('{}_tracks.json'.format(USER_ID), orient='records', lines=True)
    features = get_user_unique_tracks_and_features(USER_ID, tracks=tracks)
    features.to_json('{}_features.json'.format(USER_ID), orient='records', lines=True)
    pass
