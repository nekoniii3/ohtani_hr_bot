from googleapiclient.discovery import build
import os

def get_video(channel_id, date, q_list):

  # 戻り値用変数
  videoId = None

  youtube = build('youtube', 'v3', developerKey=os.environ['YOUTUBE_API_KEY'])

  for q in q_list:

      response = youtube.search().list(
          part = "snippet",
          channelId = channel_id,
          type = "video",
          maxResults = 100,
          order = "date",
          publishedAfter=date,
          q = q
      ).execute()

      if len(response['items']) == 0:
          continue

      item = response['items'][0]

      date, title, videoId = item['snippet']['publishedAt'], item['snippet']['title'], item['id']['videoId']

      # print(date, title, videoId)

  return videoId