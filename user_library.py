
import time
from pprint import pprint

from pymongo.bulk import BulkWriteError

from db_formatter import (format_all_playlist_tracks, format_all_saved_tracks,
                          format_playlist, format_track)
from helper import filter_user_playlists, get_new_tracks
from spotipy_wrapper import (get_audio_analysis, get_audio_features,
                             get_spotify_instance, get_user_playlist_tracks,
                             get_user_playlists, get_user_saved_tracks)


def backup(user_id, api_credentials, db):

    user_playlists = get_user_playlists(user_id, api_credentials)
    filtered_playlists = filter_user_playlists(user_playlists)

    sp = get_spotify_instance(user_id, **api_credentials)
    saved_tracks = {
        'collaborative': False,
        'href': None,
        'id': f'{user_id}_saved_tracks',
        'images': [],
        'name': 'Saved Tracks',
        'owner': sp.current_user(),
        'public': False,
        'snapshot_id': None,
        'tracks': {'total': 0},
        'type': 'playlist'}

    filtered_playlists.append(saved_tracks)

    for playlist in filtered_playlists:
        playlist_new = format_playlist(playlist)
        playlist_old = db.playlists.find_one({'id': playlist['id']})

        if playlist_old is None:
            print(f'Playlist: {playlist_new["name"]} (NEW)')
            add_playlist_to_db(playlist_new, user_id, api_credentials, db)
        elif playlist_has_changed(playlist_new, playlist_old):
            print(f'Playlist: {playlist["name"]} (UPDATED)')
            changes = get_playlist_changes(playlist_new, playlist_old)
        else:
            print(f'Playlist: {playlist["name"]} (NOT CHANGED)')


def playlist_has_changed(playlist_new, playlist_old):
    return playlist_new['snapshot_id'] != playlist_old['snapshot_id']


def add_playlist_to_db(playlist_new, user_id, api_credentials, db):
    if playlist_new['name'] == 'Saved Tracks':
        playlist_tracks = get_user_saved_tracks(user_id, api_credentials)
        playlist_tracks = format_all_saved_tracks(playlist_tracks)
    else:
        playlist_tracks = get_user_playlist_tracks(playlist_new, user_id, api_credentials)
        playlist_tracks = format_all_playlist_tracks(playlist_tracks)

    playlist_new['total_tracks'] = len(playlist_tracks)
    playlist_new['tracks'] = playlist_tracks

    if len(playlist_tracks) > 0:
        playlist_new['created_at'] = get_playlist_creation_date(playlist_tracks)

        tracks = [track['track'] for track in playlist_tracks]
        tracks_new = get_new_tracks(tracks, user_id, api_credentials, db)

        add_tracks_to_db(tracks_new, user_id, api_credentials, db)

    db.playlists.insert_one(playlist_new)


def add_tracks_to_db(tracks_new, user_id, api_credentials, db):
    if len(tracks_new) > 0:
        audio_features_new = get_audio_features(tracks_new, user_id, api_credentials)

        for track, features in zip(tracks_new, audio_features_new):
            track['features'] = features

        try:
            db.tracks.insert_many(tracks_new)
        except BulkWriteError as e:
            pprint(e.details)


def get_playlist_creation_date(playlist_tracks):
    return min([t['added_at'] for t in playlist_tracks])


def get_playlist_changes(playlist_new, playlist_old):
    pass

if __name__ == '__main__':
    from api import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
    from constants import SCOPE

    api_credentials = {
        'scope': SCOPE,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI}

    from helper import connect_mongodb
    from db import DATABASE_HOST, DATABASE_NAME
    db = connect_mongodb(DATABASE_HOST, DATABASE_NAME)

    db.playlists.delete_many({})
    db.tracks.delete_many({})
    backup('deedanvy', api_credentials, db)
