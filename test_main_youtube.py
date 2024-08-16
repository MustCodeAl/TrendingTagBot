from collections import Counter
from unittest import TestCase
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build

# Constants
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
REGION_CODE = 'US'  # Change this to your preferred region
CLIENT_SECRETS_FILE = 'client_secret.json'  # Path to your client secrets file
VIDEO_ID = 'W_HDjqL-Z3M'


class YouTubeAPI:
    def __init__(self, api_key):
        self.youtube = build(API_SERVICE_NAME, API_VERSION, developerKey=api_key)

    def get_video_snippet(self, video_id):
        try:
            response = self.youtube.videos().list(
                part='snippet',
                id=video_id
            ).execute()
            return response['items'][0]['snippet'] if response['items'] else None
        except Exception as e:
            print(f"An error occurred while fetching video snippet: {e}")
            return None

    def update_video_snippet(self, video_id, snippet):
        try:
            update_response = self.youtube.videos().update(
                part='snippet',
                body=dict(
                    snippet=snippet,
                    id=video_id
                )
            ).execute()
            print(f"Video {video_id} updated successfully.")
        except Exception as e:
            print(f"An error occurred while updating video: {e}")

    def get_trending_videos(self, region_code=REGION_CODE, max_results=10):
        try:
            response = self.youtube.videos().list(
                part='snippet,statistics',
                chart='mostPopular',
                regionCode=region_code,
                maxResults=max_results
            ).execute()

            return [
                {
                    'title': item['snippet']['title'],
                    'channel': item['snippet']['channelTitle'],
                    'views': item['statistics']['viewCount'],
                    'likes': item['statistics'].get('likeCount', 'N/A'),
                    'url': f"https://www.youtube.com/watch?v={item['id']}"
                } for item in response['items']
            ]
        except Exception as e:
            print(f"An error occurred while fetching trending videos: {e}")
            return []


class VideoTagManager:
    def __init__(self, youtube_api):
        self.youtube_api = youtube_api

    def get_video_tags_from_url(self, vid_url):
        if ".com" in vid_url:
            request = requests.get(vid_url)
            soup = BeautifulSoup(request.content, 'html5lib')
            tags = ', '.join(
                [meta_tag.attrs.get("content") for meta_tag in soup.find_all("meta", {"property": "og:video:tag"})]
            )
            return tags if tags else None
        else:
            print("No tags found")
            return None

    def update_video_tags(self, video_id, new_tags):
        snippet = self.youtube_api.get_video_snippet(video_id)
        if snippet:
            snippet['tags'] = new_tags
            self.youtube_api.update_video_snippet(video_id, snippet)
        else:
            print(f"Failed to update tags for video {video_id}")


class TagAnalysis:
    def __init__(self):
        self.vid_tag_trends = {}

    def set_keywords_dictionary(self, video_tag_manager, tube_urls):
        self.vid_tag_trends = {
            url: video_tag_manager.get_video_tags_from_url(url) for url in tube_urls
        }

    def get_average_keywords(self):
        vid_count = self.vid_count()
        tag_total = self.tag_total()

        print(f"Total videos: {vid_count}")
        print(f"Total number of tags: {tag_total}")
        print(f"Average number of tags: {tag_total / vid_count if vid_count else 0}")

    def most_frequent_tags(self):
        all_tags = self.all_tags().lstrip(' ').split(',')
        return Counter(all_tags).most_common(int(self.tag_total() / self.vid_count()))

    def vid_count(self):
        return len(self.vid_tag_trends)

    def all_tags(self):
        return ','.join(tag.strip() for tag in self.vid_tag_trends.values())

    def tag_total(self):
        return sum(len(tags.lstrip().split(',')) for tags in self.vid_tag_trends.values())


class TestYouTubeTagManager(TestCase):
    def setUp(self):
        self.api_key = 'YOUR_API_KEY'  # Replace with your YouTube Data API key
        self.youtube_api = YouTubeAPI(self.api_key)
        self.video_tag_manager = VideoTagManager(self.youtube_api)
        self.tag_analysis = TagAnalysis()

    def test_update_tags(self):
        urls = [
            "https://www.youtube.com/watch?v=gim2kprjL50",
            "https://www.youtube.com/watch?v=nY3O_gIjCP8"
        ]
        self.tag_analysis.set_keywords_dictionary(self.video_tag_manager, urls)
        self.tag_analysis.get_average_keywords()

        common_keys = self.tag_analysis.most_frequent_tags()
        print("Most common tags:", common_keys)

        # Update the tags on the target video
        new_tags = [tag for tag, _ in common_keys]
        self.video_tag_manager.update_video_tags(VIDEO_ID, new_tags)

    def test_get_trending_videos(self):
        trending_videos = self.youtube_api.get_trending_videos(max_results=10)

        print("Top 10 Trending Videos:")
        for i, video in enumerate(trending_videos, start=1):
            print(f"{i}. {video['title']} by {video['channel']}")
            print(f"   Views: {video['views']}, Likes: {video['likes']}")
            print(f"   Watch here: {video['url']}\n")

