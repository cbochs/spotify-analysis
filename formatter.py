from datetime import datetime

from constants import (DATETIME_FORMAT_LONG, DATETIME_FORMAT_SHORT,
                       DATETIME_FORMAT_YEAR, DATETIME_FORMAT_YR_MTH)


def format_album(result):
    album = {
        'album_type': result['album_type'],
        'id': result['id'],
        'name': result['name'],
        'release_date': format_datetime(result['release_date'],
                                        result['release_date_precision']),
        'total_tracks': result['total_tracks'],
        'type': result['type']}

    return album


def format_artists(result):
    return list(map(format_artist, result))


def format_artist(result):
    artist = {
        'id': result['id'],
        'name': result['name'],
        'type': result['type']}

    return artist


def format_tracks(result, historical=False):
    return list(map(lambda r: format_track(r, historical), result['items']))


def format_track(result, historical=False):
    
    track = {}

    if historical:
        track['played_at'] = format_datetime(result['played_at'], 'ms')
        result = result['track']
    
    track['album'] = format_album(result['album'])
    track['artists'] = format_artists(result['artists'])
    track['disc_number'] = result['disc_number']
    track['duration_ms'] = result['duration_ms']
    track['explicit'] = result['explicit']
    track['external_ids'] = result['external_ids']
    track['id'] = result['id']
    track['name'] = result['name']
    track['popularity'] = result['popularity']
    track['track_number'] = result['track_number']
    track['type'] = result['type']

    return track


def format_features(result):
    if result is None:
        return None

    features =  {
        'acousticness': result['acousticness'],
        'danceability': result['danceability'],
        'energy': result['energy'],
        'instrumentalness': result['instrumentalness'],
        'key': result['key'],
        'liveness': result['liveness'],
        'loudness': result['loudness'],
        'mode': result['mode'],
        'speechiness': result['speechiness'],
        'tempo': result['tempo'],
        'time_signature': result['time_signature'],
        'type': result['type'],
        'valence': result['valence']}

    return features

def format_all_features(result):
    return list(map(format_features, result))

def format_datetime(date_string, precision):
    if precision == 'ms':
        date = datetime.strptime(date_string, DATETIME_FORMAT_LONG)
    elif precision == 'day':
        date = datetime.strptime(date_string, DATETIME_FORMAT_SHORT)
    elif precision == 'month':
        date = datetime.strptime(date_string, DATETIME_FORMAT_YR_MTH)
    elif precision == 'year':
        date = datetime.strptime(date_string, DATETIME_FORMAT_YEAR)
    else:
        print(f'NO DATETIME FOUND FOR {date_string}')
        date = None
    return date
