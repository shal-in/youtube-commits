import youtube

api_key = youtube.get_api_key()
youtube_service = youtube.get_youtube(api_key)

url = "https://www.youtube.com/@jjolatunji"
channel_id = youtube.get_channel_id(youtube_service, url)

def get_channel_info(youtube_service, channel_id):
    channel_info = youtube.get_channel_details(youtube_service, channel_id)

    uploads_playlist_id = channel_info["uploads_playlist_id"]
    video_ids = youtube.get_video_ids(youtube_service, uploads_playlist_id)

    all_video_info = youtube.get_video_details(youtube_service, video_ids)

    channel_info["uploads"] = all_video_info

    return channel_info

channel_info = get_channel_info(youtube_service, channel_id)

for key in channel_info:
    if key == "uploads":
        print (f'{key}: {len(channel_info["uploads"])}')
    else:
        print (f'{key} - {channel_info[key]}')