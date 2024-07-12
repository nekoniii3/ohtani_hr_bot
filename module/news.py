import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
from zoneinfo import ZoneInfo
import re

# 定数
URL = "https://www.nikkansports.com/baseball/mlb/japanese/ohtani/news/"

# 正規表紙パターン
pt_day = r"(\d+)月(\d+)日"
pt_time = r".*\[(\d+):(\d+)\]"


def get_news_nikkan(date, time, limit_min, word_list, ng_word_list):

    # HTMLの取得・変換
    response = requests.get(URL)
    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text,'html.parser')

    # 今日のニュースかチェック
    news_day = soup.find("h3", class_=False)
    rs_day = re.search(pt_day, news_day.text)
    month = rs_day.group(1)
    day = rs_day.group(2)

    if int(month)*100 + int(day) != int(date[4:8]):
        return 0

    # 大谷ニュース一覧の取得
    newslist = soup.find("ul", class_="newslist")
    newslist_li = newslist.findAll("li")

    # ニュース数用変数
    news_count = 0

    for li in newslist_li:

        # 見出し・URL・日付を取得
        heading = li.find("a").text
        url = li.find("a").get("href")

        # 投稿された時間を取得
        rs_time = re.search(pt_time, heading)
        hour, minute = rs_time.group(1), rs_time.group(2)
        head_time = hour + minute

        # 指定時間より前なら終了
        if int(head_time) < int(time) - limit_min:
            break

        for word in ng_word_list:

            # NGワードがあれば次の見出しへ
            if word in heading:
                NG_FLAG = True
                break
            else:
                NG_FLAG = False

        if NG_FLAG:
            continue

        for word in word_list:

            # キーワードがあるか探す
            if word in heading:

                # デバッグ用
                print(heading)

                # あればホームランを打ってるので終了
                news_count += 1
                break

    return news_count