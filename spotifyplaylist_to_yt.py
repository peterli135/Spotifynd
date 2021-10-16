"""
What We Want the Program to Do:
1. Enter in a Spotify Playlist URL
2. Converts Spotify Playlist to Youtube Playlist

How does this Work:
1. Must have a Spotify Playlist URL
2. Login to YouTube
3. Create a new playlist
4. Search for the song and add it to playlist.
"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json
import requests
from pyyoutube import Api
import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors


with open("secrets.json", encoding="utf-8-sig") as json_file:
    secrets = json.load(json_file)


# Disable OAuthlib's HTTPS verification when running locally.
# *DO NOT* leave this option enabled in production.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

api_service_name = "youtube"
api_version = "v3"
client_secrets_file = "client_secrets.json"

# Get credentials and create an API client
scopes = ["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.force-ssl"]
flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
credentials = flow.run_console()
youtube = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)


#Converts the URL link to only the ID part that we need to use
def url_convert_id(playlist_url):
    url_parts = playlist_url.split("/")
    return url_parts[4].split("?")[0]


def spotify_playlist(playlist_url):

    playlist_id = url_convert_id(playlist_url)

    #Aunthenticates the Spotify Application w/ spotipy library
    client_credentials_manager = SpotifyClientCredentials(secrets["spotify_client_id"], secrets["spotify_client_secret"])
    spotify_api = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    results = spotify_api.user_playlist_tracks(user=None, playlist_id=playlist_id)

    tracklist = []

    for song in results["items"]:
        track_name = song["track"]["name"]
        track_artist = song["track"]["artists"][0]["name"]
        if len(song["track"]["artists"]) == 1:
            tracklist.append(track_name + " - " + track_artist)
        else:
            other_artists = ""
            for index, artists in enumerate(song["track"]["artists"]):
                other_artists += (artists["name"])
                if len(song["track"]["artists"]) - 1 != index:
                    other_artists += ", "
            tracklist.append(song["track"]["name"] + " - " + other_artists)
    
    create_youtube_playlist()
    for track in tracklist:
        print(track)
        search_youtube_song(track)

    return tracklist


def create_youtube_playlist():
    request = youtube.playlists().insert(
        part="snippet,status",
        body={
          "snippet": {
            "title": "Spotify Playlist to YouTube",
            "description": "My songs imported from a playlist from my Spotify account.",
            "tags": ["70s Music", "Old School"],
            "defaultLanguage": "en"
          },
          "status": {
            "privacyStatus": "private"
          }
        }
    )
    response = request.execute()
    
    global youtube_playlist_id
    youtube_playlist_id = response["id"]
    return(youtube_playlist_id)


def search_youtube_song(song):
    request = youtube.search().list(
        part="snippet",
        maxResults=1,
        type="video",
        q=song
    )
    response = request.execute()

    for item in response["items"]:
        video_title = item["snippet"]["title"]
        video_id = item["id"]["videoId"]
        print(video_title)
    
    add_to_playlist(video_id, youtube_playlist_id)
    return(video_id)


def add_to_playlist(videoId, playlistId):
    request = youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlistId,
                "position": 0,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": videoId,
                }
            }
        }
    )
    response = request.execute()

spotify_playlist(input("Enter the Spotify Playlist URL Link: "))