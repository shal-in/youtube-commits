import requests
from bs4 import BeautifulSoup
import re
import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Helper functions
def get_api_key():
    file_path = "api_key.txt"  # File containing the API key

    # Check if the file exists
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            api_key = file.read().strip()  # Read and remove any extra whitespace
            return api_key

    # If file doesn't exist, check environment variable
    api_key = os.getenv("YOUTUBE_API_KEY")
    if api_key:
        return api_key

    # If neither file nor environment variable contains the key
    return None

# Main functions
def get_youtube(api_key):
    try:
        api_service_name = "youtube"
        api_version = "v3"

        youtube = build(
            api_service_name, api_version, developerKey=api_key
        )
        return youtube

    except HttpError as e:
        print(f"An HTTP error occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

    return None

def get_channel_id(youtube_service, youtube_url):
    if "/@" in youtube_url:
        # Extract the custom name from the URL
        custom_name = youtube_url.split("/@")[-1]
        channel_id = get_channel_id_from_custom_name(youtube_service, custom_name)
    elif "/watch" in youtube_url:
        # Get the channel ID from a video URL
        channel_id = get_channel_id_from_video(youtube_service, youtube_url)
    elif "/channel/" in youtube_url:
        # Extract the channel ID from the URL directly
        channel_id = youtube_url.split("/channel/")[-1]
    else:
        return "Invalid YouTube URL"
    
    return channel_id

def get_channel_id_from_video(youtube_service, youtube_url):
    try:
        # Extract the video ID from the watch URL
        video_id = youtube_url.split("/watch?v=")[-1]
        video_id = video_id.split("&t")[0]
        
        # Use the YouTube API to get video details and extract the channel ID
        request = youtube_service.videos().list(
            part="snippet",
            id=video_id
        )
        response = request.execute()
        
        # Extract the channel ID from the response
        if "items" in response and len(response["items"]) > 0:
            channel_id = response["items"][0]["snippet"]["channelId"]
            return channel_id
        else:
            return "Channel ID not found for the video."
    except Exception as e:
        return f"Error: {e}"

def get_channel_id_from_custom_name(youtube_service, custom_name):
    try:
        # Make API call to search for a channel using the custom name
        request = youtube_service.search().list(
            part="snippet",
            q=custom_name,
            type="channel",
            maxResults=1  # Only one result expected
        )
        response = request.execute()

        # Extract channel ID from the response
        if "items" in response and len(response["items"]) > 0:
            channel_id = response["items"][0]["snippet"]["channelId"]
            return channel_id
        else:
            return "Channel not found."
    except Exception as e:
        return f"Error: {e}"



def get_channel_details(youtube, channel_id):
    try:
        # Make API request
        request = youtube.channels().list(
            part="snippet,contentDetails",
            id=channel_id
        )
        response = request.execute()

        # Extract relevant data
        if "items" in response and len(response["items"]) > 0:
            channel_data = response["items"][0]

            # Channel Name
            channel_name = channel_data["snippet"]["title"]

            # Profile Picture URL
            profile_pic = channel_data["snippet"]["thumbnails"]["default"]["url"]

            # Uploads Playlist ID
            uploads_playlist_id = channel_data["contentDetails"]["relatedPlaylists"]["uploads"]

            return {
                "channel_name": channel_name,
                "profile_pic": profile_pic,
                "uploads_playlist_id": uploads_playlist_id
            }
        else:
            print("Channel not found.")
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_video_ids(youtube, playlist_id):
    
    video_ids = []
    
    request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=playlist_id,
        maxResults = 50
    )
    response = request.execute()
    
    for item in response['items']:
        video_ids.append(item['contentDetails']['videoId'])
        
    next_page_token = response.get('nextPageToken')
    while next_page_token is not None:
        request = youtube.playlistItems().list(
                    part='contentDetails',
                    playlistId = playlist_id,
                    maxResults = 50,
                    pageToken = next_page_token)
        response = request.execute()

        for item in response['items']:
            video_ids.append(item['contentDetails']['videoId'])

        next_page_token = response.get('nextPageToken')
        
    return video_ids

def get_video_details(youtube, video_ids):
    all_video_info = []

    for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=','.join(video_ids[i:i+50])
        )

        response = request.execute()

        for video in response["items"]:
            stats_to_keep = {
                "snippet": ["title", "thumbnails", "publishedAt"]
            }

            video_info = {}
            video_info["video_id"] = video["id"]

            for k in stats_to_keep.keys():
                for v in stats_to_keep[k]:
                    try :
                        video_info[v] = video[k][v]
                    except:
                        video_info[v] = None

            all_video_info.append(video_info)

    return all_video_info