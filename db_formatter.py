from datetime import datetime
import html

from constants import (DATETIME_FORMAT_LONG, DATETIME_FORMAT_MS,
                       DATETIME_FORMAT_SHORT, DATETIME_FORMAT_YEAR,
                       DATETIME_FORMAT_YR_MTH)


def format_list(result, formatter):
    return list(filter(None, list(map(formatter, result))))


def format_all_artists(result):
    return format_list(result, format_artist)


def format_all_tracks(result):
    return format_list(result, format_track)


def format_all_playlist_tracks(result):
    return format_list(result, format_playlist_track)


def format_all_saved_tracks(result):
    return format_list(result, format_saved_track)


def format_all_play_history(result):
    return format_list(result, format_play_history)


def format_all_track_features(result):
    return format_list(result, format_track_features)


def format_all_playlists(result):
    return format_list(result, format_playlist)


def format_album(result):
    album = {
        'album_type': result['album_type'],
        'id': result['id'],
        'href': result['href'],
        'name': result['name'],
        'release_date': format_datetime_string(result['release_date'],
                                        result['release_date_precision']),
        'release_date_precision': result['release_date_precision'],
        'total_tracks': result['total_tracks'],
        'type': result['type']}

    return album


def format_artist(result):
    artist = {
        'href': result['href'],
        'id': result['id'],
        'name': result['name'],
        'type': result['type']}

    return artist


def format_track(result):
    if result['is_local']:
        return None

    track = {
        'album': format_album(result['album']),
        'artists': format_all_artists(result['artists']),
        'disc_number': result['disc_number'],
        'duration_ms': result['duration_ms'],
        'explicit': result['explicit'],
        'external_ids': result['external_ids'],
        'href': result['href'],
        'id': result['id'],
        'name': result['name'],
        'popularity': result['popularity'],
        'track_number': result['track_number'],
        'type': result['type']}
    
    return track


def format_playlist_track(result):
    if result['track']['is_local']:
        return None

    playlist_track = {
        'added_at': format_datetime_string(result['added_at'], 'second'),
        'added_by': format_user(result['added_by']),
        'track': format_track(result['track'])}

    return playlist_track


def format_saved_track(result):
    if result['track']['is_local']:
        return None
    
    saved_track = {
        'added_at': format_datetime_string(result['added_at'], 'second'),
        'track': format_track(result['track'])}

    return saved_track

def format_play_history(result):
    play_history = {
        'context': result['context'],
        'played_at': format_datetime_string(result['played_at'], 'ms'),
        'track': format_track(result['track'])}

    return play_history


def format_track_features(result):
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


def format_playlist(result):
    playlist = {
        'collaborative': result['collaborative'],
        'href': result['href'],
        'id': result['id'],
        'images': result['images'],
        'name': result['name'],
        'owner': format_owner(result['owner']),
        'public': result['public'],
        'snapshot_id': result['snapshot_id'],
        'total_tracks': result['tracks']['total'],
        'type': result['type']}

    return playlist


def format_owner(result):
    owner = {
        'display_name': result['display_name'],
        'href': result['href'],
        'id': result['id'],
        'type': result['type']}

    return owner


def format_user(result):
    return result['id']


def format_datetime_string(date_string, precision):
    if precision == 'ms':
        date_obj = datetime.strptime(date_string, DATETIME_FORMAT_MS)
    elif precision == 'second':
        date_obj = datetime.strptime(date_string, DATETIME_FORMAT_LONG)
    elif precision == 'day':
        date_obj = datetime.strptime(date_string, DATETIME_FORMAT_SHORT)
    elif precision == 'month':
        date_obj = datetime.strptime(date_string, DATETIME_FORMAT_YR_MTH)
    elif precision == 'year' and date_string != '0000':
        date_obj = datetime.strptime(date_string, DATETIME_FORMAT_YEAR)
    else:
        print(f'NO DATETIME FOUND FOR {date_string}')
        date_obj = None
    return date_obj


def format_datetime(date_obj, precision):
    if precision == 'ms':
        date_string = datetime.strftime(date_obj, DATETIME_FORMAT_MS)
    elif precision == 'second':
        date_string = datetime.strftime(date_obj, DATETIME_FORMAT_LONG)
    elif precision == 'day':
        date_string = datetime.strftime(date_obj, DATETIME_FORMAT_SHORT)
    elif precision == 'month':
        date_string = datetime.strftime(date_obj, DATETIME_FORMAT_YR_MTH)
    elif precision == 'year':
        date_string = datetime.strftime(date_obj, DATETIME_FORMAT_YEAR)
    else:
        print(f'NO DATETIME FOUND FOR {date_string}')
        date_string = None
    return date_string