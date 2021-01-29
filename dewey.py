import time
import sys
import configparser
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# API Thresholds
THROTTLE_BUFFER = 3 # if a query fails, seconds to wait before retrying
MAX_RETRIES     = 3 # try requests up to this many times
MAX_QUERY_SIZE  = 50 # API limits this many keys per request

# given a spotify object with user-library-read scope, get a list of user's tracks
def getSavedTracks(sp):
    # send first request for songs to confirm account can be reached
    print('I\'m looking up your account...')
    total = 0
    try:
        results = sp.current_user_saved_tracks()
        total = results['total']
        print('You\'ve saved {} tracks. Fetching track info...'.format(total))
    except:
        print('Sorry, I couldn\'t look up your account. Please try again later.')
        return

    # fetch track objects and save in list. paginate requests
    tracks = []
    offset = 0
    while offset < total:
        # try request up to MAX_RETRIES times
        tries = 0
        results = None
        while tries < MAX_RETRIES and not results:
            try:
                tries = tries + 1
                results = sp_user.current_user_saved_tracks(limit=MAX_QUERY_SIZE, offset=offset)
            except Exception as e:
                print('request failed. waiting {} seconds before retrying...'.format(THROTTLE_BUFFER))
                results = None
                time.sleep(THROTTLE_BUFFER)

        # request successful, parse results
        offset = offset + len(results['items'])
        for idx, item in enumerate(results['items']):
            track = item['track']
            tracks.append(track)
        # print status
        if offset % 1000 == 0:
            print('\t{} remaining. Currenty fetching {}'.format(results['total'] - offset, tracks[-1]['name']))
    # print completion
    print('OK, I fetched {} tracks.'.format(len(tracks)))

    return tracks

# based on liked tracks and user thresholds, find artists and albums to like
def findArtistsAndAlbumsToLike(tracks, artist_threshold, album_threshold):
    dict_artists_from_tracks = {}
    dict_albums_from_tracks = {}
    lookup_dictionary = {}
    # build dictionaries of albums and artists, keeping count of songs liked belonging to them
    for track in tracks:
        for artist in track['artists']:
            artist_id = artist['id']
            artist_name = artist['name']
            lookup_dictionary[artist_id] = artist_name
            if artist_id in dict_artists_from_tracks:
                dict_artists_from_tracks[artist_id] = dict_artists_from_tracks[artist_id] + 1
            else:
                dict_artists_from_tracks[artist_id] = 1
        album_id = track['album']['id']
        album_name = track['album']['name']
        lookup_dictionary[album_id] = album_name
        if album_id in dict_albums_from_tracks:
            dict_albums_from_tracks[album_id] = dict_albums_from_tracks[album_id] + 1
        else:
            dict_albums_from_tracks[album_id] = 1

    # apply thresholds to dictionary and produce lists of artists and albums
    artists_to_like = []
    albums_to_like = []
    for artist_id, songs in dict_artists_from_tracks.items():
        if songs >= artist_threshold:
            artists_to_like.append(artist_id)
    for album_id, songs in dict_albums_from_tracks.items():
        if songs >= album_threshold:
            albums_to_like.append(album_id)

    artist_names = [lookup_dictionary[id] for id in artists_to_like]
    artist_names.sort()
    album_names = [lookup_dictionary[id] for id in albums_to_like]
    album_names.sort()
    print('Looks like you like the following artists. This is who I plan on adding to your library:')
    for artist in artist_names: print('\t{}'.format(artist))
    print('Looks like you like the following albums. This is what I plan on adding to your library:')
    for album in album_names: print('\t{}'.format(album))
    return artists_to_like, albums_to_like

# given a list of artist and list of albums, add to user's library
def addArtistsAndAlbums(sp, artists, albums):
    print('Adding artists to library...')
    artist_batches = [artists[i:i + MAX_QUERY_SIZE] for i in range(0, len(artists), MAX_QUERY_SIZE)]
    for batch in artist_batches:
        sp.user_follow_artists(batch)
    print('Adding albums to library...')
    album_batches = [albums[i:i + MAX_QUERY_SIZE] for i in range(0, len(albums), MAX_QUERY_SIZE)]
    for batch in album_batches:
        sp.current_user_saved_albums_add(batch)

def parseConfig():
    if len(sys.argv) != 2:
        print('Usage: python dewey.py /path/to/config.ini')
        quit()
    config = configparser.ConfigParser()
    config.read(sys.argv[1])
    if 'CREDENTIALS' not in config or 'CLIENT_ID' not in config['CREDENTIALS'] \
            or 'CLIENT_SECRET' not in config['CREDENTIALS'] or 'REDIRECT_URI' not in config['CREDENTIALS']:
        print('config file missing required param(s)')
        quit()
    return config


if __name__ == '__main__':
    config = parseConfig()

    # get user thresholds
    print('\nHi, I\'m Dewey.\nI\'m here to add artists and albums to your library based on already liked tracks.\n')
    artist_threshold = input("How many tracks should I look for per artist?: ")
    album_threshold = input("How many tracks should I look for per album?: ")
    try:
        artist_threshold = int(artist_threshold)
        album_threshold = int(album_threshold)
    except:
        print('Sorry, please enter numeric thresholds.')
        quit()
    print('\nThanks! I\'ll save artists to your library if you\'ve liked at least {} of their tracks.'.format(artist_threshold))
    print('I\'ll save albums from which you\'ve liked at least {} tracks.\n'.format(album_threshold))


    # login to account. if no user currently logged in, browser will open
    # prompting for user credentials
    sp_user = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=config['CREDENTIALS']['CLIENT_ID'],
                                                        client_secret=config['CREDENTIALS']['CLIENT_SECRET'],
                                                        redirect_uri=config['CREDENTIALS']['REDIRECT_URI'],
                                                        scope="user-library-read user-follow-modify user-library-modify"))
    tracks = getSavedTracks(sp_user)

    # Get list of albums and artists to add, and check with user to make sure they're OK to proceed
    artists_to_like, albums_to_like = findArtistsAndAlbumsToLike(tracks, artist_threshold, album_threshold)
    response = input('Would you like me to proceed with adding these to your library (Y/N)? ')
    if response.lower() not in ['y', 'yes']:
        print('OK, quitting...')
        quit()
    print('OK, adding...')

    # add entities to user's library
    addArtistsAndAlbums(sp_user, artists_to_like, albums_to_like)
    print('All Done! Bye for now.\n')