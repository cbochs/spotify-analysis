import spotipy
import spotipy.util as util

def get_spotify_instance(user_id, scope=None, client_id=None, client_secret=None, redirect_uri=None):
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


def get_user_recently_played(user_id, api_credentials):

    sp = get_spotify_instance(user_id, **api_credentials)

    result = sp._get('me/player/recently-played', limit=50)
    tracks = result['items']

    return tracks


def get_user_playlists(user_id, api_credentials):

    sp = get_spotify_instance(user_id, **api_credentials)

    print(f'Finding {user_id}\'s playlists.')

    extra_fields = 'description,followers'
    
    count = 0
    database_playlists = False
    playlists = []
    result = sp.user_playlists(user_id, offset=0)
    while True:
        playlists.extend(result['items'])

        if result['next'] is None:
            break

        result = sp.next(result)

    print(f'Found {len(playlists)} playlists in {user_id}\'s library')

    return playlists


def get_user_playlist_tracks(playlists, user_id, api_credentials):

    sp = get_spotify_instance(user_id, **api_credentials)

    if not isinstance(playlists, list):
        playlists = [playlists]

    # print(f'Finding tracks for {len(playlists)} playlists')

    all_tracks = []
    for playlist in playlists:
        # print(f'Playlist: {playlist["name"]}')

        tracks = []
        result = sp.user_playlist_tracks(user_id, playlist['id'], offset=0, market='CA')
        while True:
            tracks.extend(result['items'])

            if result['next'] is None:
                break
            
            result = sp.next(result)

        all_tracks.extend(tracks)

        # print(f'\tFound a total of {len(tracks)} tracks in {playlist["name"]}.')

    # print(f'Found a total of {len(all_tracks)} tracks in {len(playlists)} playlists')

    return all_tracks


def get_user_saved_tracks(user_id, api_credentials):

    sp = get_spotify_instance(user_id, **api_credentials)

    tracks = []
    result = sp.current_user_saved_tracks(limit=50, offset=0)
    while True:
        tracks.extend(result['items'])

        if result['next'] is None:
            break

        result = sp.next(result)

    return tracks


def get_current_user_saved_tracks(user_id, api_credentials):

    sp = get_spotify_instance(user_id, **api_credentials)

    tracks = []
    result = sp.current_user_saved_tracks(limit=50)
    tracks.extend(result['items'])
    while result['next']:
        result = sp.next(result)
        tracks.extend(result['items'])
    
    return tracks


def get_audio_features(tracks, user_id, api_credentials):

    sp = get_spotify_instance(user_id, **api_credentials)

    if not isinstance(tracks, list):
        tracks = [tracks]

    n = len(tracks)
    features = []
    for i in range(0, n, 50):
        ii = (i + 50) if (i + 50) < n else n
        ids = [track['id'] for track in tracks[i:ii]]

        result = sp.audio_features(ids)
        features.extend(result)

    return features


def get_audio_analysis(tracks, user_id, api_credentials):

    sp = get_spotify_instance(user_id, **api_credentials)

    if not isinstance(tracks, list):
        tracks = [tracks]

    analysis = []
    for track in tracks:
        result = sp.audio_analysis(track['id'])
        analysis.append(result)

    return analysis