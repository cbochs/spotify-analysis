from pprint import pprint

from pymongo.bulk import BulkWriteError

from db_formatter import format_all_play_history
from helper import connect_mongodb, get_spotify_instance, get_new_tracks
from spotipy_wrapper import get_user_recently_played, get_audio_features


def backup(user_id, api_credentials, db):
    
    recently_played = get_user_recently_played(user_id, api_credentials)
    recently_played = format_all_play_history(recently_played)

    for play_history in recently_played:
        play_history['user_id'] = user_id

    try:
        db.history.insert_many(recently_played, ordered=True)
    except BulkWriteError as e:
        pprint(e.details)

    tracks = [track['track'] for track in recently_played]
    tracks_new = get_new_tracks(tracks, user_id, api_credentials, db)

    if len(tracks_new) > 0:
        audio_features_new = get_audio_features(tracks_new, user_id, api_credentials)

        for track, features in zip(tracks_new, audio_features_new):
            track['features'] = features

        try:
            db.tracks.insert_many(tracks_new)
        except BulkWriteError as e:
            pprint(e.details)


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

    # db.playlists.delete_many({})
    # db.history.delete_many({})
    backup('deedanvy', api_credentials, db)