# dewey
A simple script for managing your Spotify library

# Requirements
1. Python 3.7+
2. spotipy
 - pip3 install spotipy

# Instructions
1. Check out the repository
2. In the [Spotify Developer dashboard](https://developer.spotify.com/dashboard/applications), create a new application
3. In the application settings, add a Redirect URI. This URI will be used to log in and grant access to the script
- It is recommended to use "http://localhost:8888/callback"
4. Add your CLIENT_ID, CLIENT_SECRET, and REDIRECT_URI to the config.ini file
5. run the application
- python dewey.py config.ini
