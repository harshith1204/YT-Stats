from googleapiclient.discovery import build
import pandas as pd
from datetime import datetime, timedelta


API_KEY = 'AIzaSyC0N5VbFCt8dazfrTU9J7f9kBK2yH26uXQ'
youtube = build('youtube', 'v3', developerKey=API_KEY)

def convert_utc_to_ist(utc_time_str):
    """
    Converts the given UTC time string (ISO 8601 format) to IST.
    """
    utc_time = datetime.strptime(utc_time_str, "%Y-%m-%dT%H:%M:%SZ")
    ist_time = utc_time + timedelta(hours=5, minutes=30)
    return ist_time.strftime("%Y-%m-%d %H:%M:%S")

def get_channel_stats(channel_ids, start_datetime, end_datetime):
    """
    Fetches subscriber count, view count, video count, and number of videos uploaded
    within the specified date and time range, and their details.
    """
    request = youtube.channels().list(
        part='statistics,snippet,contentDetails',
        id=','.join(channel_ids)
    )
    response = request.execute()

    channels_data = []
    for channel in response['items']:
        channel_name = channel['snippet']['title']
        channel_url = f"https://www.youtube.com/channel/{channel['id']}"
        uploads_playlist_id = channel['contentDetails']['relatedPlaylists']['uploads']
        recent_videos_data = get_recent_videos(uploads_playlist_id, start_datetime, end_datetime)
        total_views_in_duration = sum(int(video['views']) for video in recent_videos_data)

        subscriber_count = channel['statistics'].get('subscriberCount', 'N/A')
        if subscriber_count != 'N/A':
            subscriber_count = int(subscriber_count)

        stats = {
            'channel_name': channel_name,
            'channel_url': channel_url,
            'subscriber_count': subscriber_count,
            'view_count': channel['statistics'].get('viewCount', 'N/A'),
            'video_count': channel['statistics'].get('videoCount', 'N/A'),
            'videos_last_duration': len(recent_videos_data),
            'views_obtained_in_duration': total_views_in_duration,
            'recent_videos_data': recent_videos_data
        }
        channels_data.append(stats)

    return channels_data

def get_recent_videos(playlist_id, start_datetime, end_datetime):
    """
    Gets video URLs and their details uploaded within the given start and end date-time range from the playlist.
    """
    request = youtube.playlistItems().list(
        part='snippet',
        playlistId=playlist_id,
        maxResults=50
    )
    response = request.execute()

    recent_videos_data = []
    for item in response['items']:
        video_published_at = item['snippet']['publishedAt']
        video_datetime_ist = convert_utc_to_ist(video_published_at)
        video_datetime = datetime.strptime(video_published_at, "%Y-%m-%dT%H:%M:%SZ")

        if start_datetime <= video_datetime <= end_datetime:
            video_id = item['snippet']['resourceId']['videoId']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            video_details = get_video_details(video_id)
            recent_videos_data.append({
                'video_url': video_url,
                'title': item['snippet']['title'],
                'uploaded_at': video_datetime_ist,
                **video_details
            })

    return recent_videos_data

def get_video_details(video_id):
    """
    Fetches video details including number of likes, views, and comments.
    """
    request = youtube.videos().list(
        part='statistics',
        id=video_id
    )
    response = request.execute()

    if response['items']:
        stats = response['items'][0]['statistics']
        return {
            'likes': stats.get('likeCount', 0),
            'views': stats.get('viewCount', 0),
            'comments': stats.get('commentCount', 0),
        }
    return {'likes': 0, 'views': 0, 'comments': 0}

def generate_excel_output(channel_statistics, extraction_time_ist):
    """
    This function will prepare the data in the same format as the provided Excel example
    and save it in a new Excel file. It adds the 'Time of Extraction in IST' column and
    'Views Obtained in Duration'.
    """
    data_to_export = []
    for index, channel in enumerate(channel_statistics):
        for video_index, video in enumerate(channel['recent_videos_data']):
            data_to_export.append({
                'Extracted Date and Time': extraction_time_ist,
                'Date & Time Uploaded': video.get('uploaded_at', 'N/A'),
                'Channel Name': channel['channel_name'],
                'Channel URL': channel['channel_url'],
                'Subscriber Count': channel['subscriber_count'],
                'Total View Count': channel['view_count'],
                'Number of Videos uploaded in Duration': channel['videos_last_duration'],
                'Views Obtained in Duration': channel['views_obtained_in_duration'],
                'Video URL': video['video_url'],
                'Video Title': video['title'],
                'Video Likes': video['likes'],
                'Video Views': video['views'],
                'Comments': video['comments'],
            })

    df = pd.DataFrame(data_to_export)
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M")
    output_filename = f'youtube_channel_stats_{current_time}.xlsx'
    df.to_excel(output_filename, index=False)
    return output_filename
