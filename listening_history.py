from formatter import format_tracks, format_all_features
from pprint import pprint

from pymongo.bulk import BulkWriteError

from helper import connect_mongodb, get_spotify_instance


def get_listening_history(user_id, api_credentials):

    sp = get_spotify_instance(user_id, **api_credentials)

    result = sp._get('me/player/recently-played', limit=50)
    tracks = format_tracks(result, historical=True)
        
    return tracks


def get_track_features(tracks, user_id, api_credentials):

    sp = get_spotify_instance(user_id, **api_credentials)

    n = len(tracks)
    features = []
    for i in range(0, n, 50):
        ii = (i + 50) if (i + 50) < n else n
        ids = [track['id'] for track in tracks[i:ii]]

        result = sp.audio_features(ids)
        features.extend(format_all_features(result))

    return features



def backup(user_id, api_credentials, db_collection):
    
    tracks = get_listening_history(user_id, api_credentials)
    features = get_track_features(tracks, user_id, api_credentials)

    documents = []
    for t, f in zip(tracks, features):
        document = {
            'played_at': t['played_at'],
            'user_id': user_id,
            'track': t,
            'features': f}
        documents.append(document)

    try:
        db_collection.insert_many(documents, ordered=True)
    except BulkWriteError as bwe:
        pprint(bwe.details)
