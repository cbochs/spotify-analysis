from datetime import datetime
from pprint import pprint

from constants import DATETIME_FORMAT_SHORT
from helper import get_spotify_instance


def archive(user_id, api_credentials, date=datetime.now()):

    sp = get_spotify_instance(user_id, **api_credentials)

    playlists = sp.user_playlists(user_id, limit=50, offset=0)

    discover_playlists = [playlist for playlist in playlists['items']
                            if playlist['name'] == 'Discover Weekly']

    playlist_name = datetime.strftime(date, DATETIME_FORMAT_SHORT)
    
    # Create playlists in reverse order because new playlists appear at the top
    for playlist in reversed(discover_playlists):
        owner_id = playlist['owner']['id']
        playlist_id = playlist['id']

        tracks = sp.user_playlist_tracks(owner_id, playlist_id=playlist_id)
        track_uris = [track['track']['id'] for track in tracks['items']]

        new_playlist = sp.user_playlist_create(user_id, playlist_name, public=False)
        new_playlist_id = new_playlist['id']

        sp.user_playlist_add_tracks(user_id, new_playlist_id, track_uris)
