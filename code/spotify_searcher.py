#from ..private import config_spotipy
import sys
from configspy import *
import spotipy
import json
import pandas as pd
import time

from spotipy.oauth2 import SpotifyClientCredentials

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

def extract_song_id(uri):
    # Split the URI by ':'
    parts = uri.split(':')
    # The song ID is the last part
    song_id = parts[-1]
    return song_id
	
def get_audio_features(list_of_song_ids):
    audio_features = []
    chunk_size = 50  # Define the chunk size

    try:
        for i in range(0, len(list_of_song_ids), chunk_size):
            chunk = list_of_song_ids[i:i+chunk_size]
            # Get audio features for the chunk of song_ids
            features = sp.audio_features(tracks=chunk)
            audio_features.extend(features)
            if i + chunk_size < len(list_of_song_ids):
                time.sleep(20)  # Add a 20-second timeout between chunks
    except Exception as e:
        print(f"Error: {e}")

    return audio_features
	

def extract_audio_feature_keys(features):
    # Extract the keys (audio feature names) from the first item in the list
    return list(features[0].keys())
	
	
# Function to search for a song and return its URIs (Spotify IDs)
def search_song(title, artist, limit=1):
    song_uris = []  # Initialize a list to store song URIs

    try:
        if artist:
            # Search for the song using both title and artist
            query = f"track:{title} artist:{artist}"
        else:
            # Search for the song using title alone
            query = f"track:{title}"

        # Add a delay before making the API call
        # Perform the search
        results = sp.search(q=query, type='track', limit=limit)

        # Check if any tracks were found
        if results['tracks']['items']:
            # Create a set to keep track of unique artist names
            unique_artists = set()
            
            for track in results['tracks']['items']:
                uri = track['uri']
                artist_name = track['artists'][0]['name']

                if artist_name not in unique_artists:
                    # Append the URI if it's the first instance of the artist
                    song_uris.append(uri)
                    unique_artists.add(artist_name)

        # Create a dictionary to store song data
        song_data = {
            'song_name': [],
            'artist': [],
            'spotify_id': []
        }

        for uri in song_uris:
            # Find the corresponding track in the search results
            track = next(item for item in results['tracks']['items'] if item['uri'] == uri)
            song_data['song_name'].append(track['name'])
            song_data['artist'].append(track['artists'][0]['name'])
            song_data['spotify_id'].append(extract_song_id(track['uri']))

        # Create a DataFrame from the song data
        song_df = pd.DataFrame(song_data)

    except Exception as e:
        # Handle exceptions, e.g., if there's an issue with the Spotify API
        print(f"Error: {e}")
        song_df = pd.DataFrame()

    return song_uris, song_df


# Function to get song info with audio features
def get_song_info_with_features(title, artist, limit):
    # Search for song URIs and song_df
    song_uris, song_df = search_song(title, artist, limit)

    if not song_uris:
        return pd.DataFrame()  # Return an empty DataFrame if no song URIs are found

    # Retrieve audio features for all song URIs
    audio_features = get_audio_features(song_uris)

    # Convert the audio features into a DataFrame
    audio_features_df = pd.DataFrame(audio_features)

    # Concatenate the two DataFrames
    song_info_df = pd.concat([song_df, audio_features_df], axis=1)

    return song_info_df
	

#add to the existing dataset
def add_audio_features(df, audio_features_df):
    # Check if both dataframes have the same length
    if len(df) != len(audio_features_df):
        raise ValueError("Dataframes must have the same length.")

    # Concatenate the dataframes horizontally
    extended_df = pd.concat([df, audio_features_df], axis=1)

    return extended_df
	
	
	
