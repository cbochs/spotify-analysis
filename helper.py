import spotipy
import spotipy.util as util
from pymongo import MongoClient


def connect_mongodb(client_url, db_name):
    client = MongoClient(client_url)
    db = client[db_name]
    return db


def get_spotify_instance(user_id, scope, client_id, client_secret, redirect_uri):
    """ Obtains a Spotify token with a specified USER_ID, SCOPE, CLIENT_ID,
        CLIENT_SECRET, and REDIRECT_URi. Returns a Spotipy object for querying
        the API directly
    
    Arguments:
        user_id (str): The users' id
        scope (str): A comma-delimited list of scopes which the token should contain
        client_id (str): Client ID obtained from the Spotify API Developer Dashboard
        client_secret (str): Client Secret obtained from the Spotify API Developer Dashboard
        redirect_uri (str): An authorized redirect uri
    
    Returns:
        (spotipy.Spotipy) Spotipy object
    """

    token = util.prompt_for_user_token(
        user_id,
        scope=scope,
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri)

    return spotipy.Spotify(auth=token)


def filter_user_playlists(playlists, static_only=True, discover_database=False):

    print(f'Filtering playlists - static playlists: {static_only}, database playlists: {discover_database}')

    exclude_playlists = discover_database
    discover_user_id = None
    filtered_playlists = []
    for playlist in playlists:
        if static_only and playlist['name'] in ['Discover Weekly', 'Release Radar']:
            continue

        if playlist['name'] == '.':
            exclude_playlists = not exclude_playlists
            continue

        if exclude_playlists:
            continue

        if discover_database:
            try:
                discover_user_id = playlist['name'].split(',')[1]
                continue
            except ValueError:
                playlist['discover_user_id'] = discover_user_id
        
        filtered_playlists.append(playlist)
    
    num_found = len(playlists)
    num_filtered = len(filtered_playlists)
    num_removed = len(playlists) - num_filtered
    per_remaining = (num_filtered / num_found) * 100
    print(f'Filtered {num_removed} playlists. {num_filtered} ({per_remaining:.2f}%) remaining.')

    return filtered_playlists


def get_new_tracks(tracks, user_id, api_credentials, db):
    track_ids = set([track['id'] for track in tracks])

    track_ids_cursor = db.tracks.find({'id': {'$in': list(track_ids)}}, {'id': 1})
    track_ids_old = set([track['id'] for track in track_ids_cursor])

    track_ids_new = track_ids.difference(track_ids_old)
    tracks_new = [track for track in tracks if track['id'] in track_ids_new]

    return tracks_new