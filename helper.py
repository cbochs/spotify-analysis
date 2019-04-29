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