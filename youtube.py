import requests
from bs4 import BeautifulSoup
import re
import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from collections import defaultdict

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

api_key = get_api_key()
youtube_service = get_youtube(api_key)

def get_channel_id(youtube_url):
    if not youtube_url:
        raise ValueError("URL is required")

    if "/@" in youtube_url:
        # Extract the custom name from the URL
        custom_name = youtube_url.split("/@")[-1]
        channel_id = get_channel_id_from_custom_name(custom_name)
    elif "/watch" in youtube_url:
        # Get the channel ID from a video URL
        channel_id = get_channel_id_from_video(youtube_url)
    elif "/channel/" in youtube_url:
        # Extract the channel ID from the URL directly
        channel_id = youtube_url.split("/channel/")[-1]
    else:
        raise ValueError("Invalid YouTube URL format")

    return channel_id

def get_channel_id_from_video(youtube_url):
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

def get_channel_id_from_custom_name(custom_name):
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



def get_channel_details(channel_id):
    try:
        # Make API request
        request = youtube_service.channels().list(
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
                "channel_id": channel_id,
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

def get_video_ids(playlist_id):
    video_ids = []
    
    request = youtube_service.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=playlist_id,
        maxResults = 50
    )
    response = request.execute()
    
    for item in response['items']:
        video_ids.append(item['contentDetails']['videoId'])
        
    next_page_token = response.get('nextPageToken')
    while next_page_token is not None:
        request = youtube_service.playlistItems().list(
                    part='contentDetails',
                    playlistId = playlist_id,
                    maxResults = 50,
                    pageToken = next_page_token)
        response = request.execute()

        for item in response['items']:
            video_ids.append(item['contentDetails']['videoId'])

        next_page_token = response.get('nextPageToken')
        
    return video_ids

def get_video_details(video_ids):
    all_video_info = []

    for i in range(0, len(video_ids), 50):
        request = youtube_service.videos().list(
            part="snippet,contentDetails,statistics",
            id=','.join(video_ids[i:i+50])
        )

        response = request.execute()

        for video in response["items"]:
            stats_to_keep = {
                "snippet": ["title", "thumbnails", "publishedAt"]
            }

            video_info = {}
            video_info["id"] = video["id"]

            for k in stats_to_keep.keys():
                for v in stats_to_keep[k]:
                    try :
                        video_info[v] = video[k][v]
                    except:
                        video_info[v] = None

            all_video_info.append(video_info)

    return all_video_info

def preprocess_video_details(video_info):
    for video in video_info:
        published_at = video["publishedAt"]
        published_at_obj = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")

        date = published_at_obj.date()  # Get the date part
        year = date.year                # Year
        month = date.month              # Month
        day = date.day                  # Day
        weekday = date.weekday()        # Weekday (0 = Monday, 6 = Sunday)
        week_number = published_at_obj.isocalendar()[1]  # Week number

        date = {"year": year, "month": month, "day": day, "weekday": weekday, "week_number": week_number}

        video["date"] = date

        for quality in ["maxres", "standard", "high", "medium", "default"]:
            if quality in video["thumbnails"]:
                video["thumbnail"] = video["thumbnails"][quality]
                del video["thumbnails"]
                break

    return video_info


def query_data_by_year(data_objects):
    # Create a dictionary to store results grouped by year
    year_groups = defaultdict(list)

    # Group data by year
    for obj in data_objects:
        year = obj['date']['year']
        year_groups[year].append(obj)

    # Find the range of years from the data
    min_year = min(year_groups.keys())
    max_year = max(year_groups.keys())

    # Ensure all years in the range are included in the dictionary
    for year in range(min_year, max_year + 1):
        if year not in year_groups:
            year_groups[year] = []  # Add empty list for missing years

    # Sort each year group by date (year, month, day)
    for year in year_groups:
        year_groups[year] = sorted(year_groups[year], key=lambda obj: (obj['date']['month'], obj['date']['day']))

    return dict(year_groups)  # Convert defaultdict to a regular dict for final output