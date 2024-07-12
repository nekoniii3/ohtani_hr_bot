import os
import datetime
from zoneinfo import ZoneInfo
from openai import OpenAI
from yt_dlp import YoutubeDL
import deepl
import tweepy

# 独自モジュール
from module import news, youtube

# 定数宣言
LIMIT_MIN = 180
# LOG_FILE = "./post_log.txt"
LOG_FILE = os.path.dirname(__file__) + "/post_log.txt"
# AUDIO_DIR = "./audio/"
AUDIO_DIR = os.path.dirname(__file__) + "/audio/"

YOUTUBE_URL = "https://www.youtube.com/watch?v="
SRC_RANG = 'EN'
TRG_RANG = 'JA'
GPT_MODEL = "gpt-4o"

# 検索用変数
channel_id = "UCoLrcjPV5PbUrUyXq5mjc_A" # MLB
# q_list = ["Ohtani home", "Ohtan HR", "Shohei Ohtani"]
q_list = ["大谷 翔平"]
word_list = ["本塁打", "ホームラン", "号", "弾"]
ng_word_list = ["全ホームラン", "なるか"]

# X APIKEYを設定
BEARER_TOKEN = os.environ['BR_TOKEN_OH']
API_KEY = os.environ['API_KEY_OH']
API_SECRET = os.environ['API_SC_OH']
ACCESS_TOKEN = os.environ['AC_TOKEN_OH']
ACCESS_SECRET = os.environ['AC_SECRET_OH']

def main():

    # 今日の日付取得（日本時間）
    dt = datetime.datetime.now(ZoneInfo("Asia/Tokyo"))
    date_str = dt.strftime("%Y%m%d")
    time_str = dt.strftime("%H%M")

    # UTC時間取得
    dt_utc = datetime.datetime.now(ZoneInfo("UTC"))

    # 今日ポストしていれば終了
    if post_check() == date_str:
        return

    # ニュースチェック
    news_count = news.get_news_nikkan(date_str, time_str, LIMIT_MIN, word_list, ng_word_list)

    if news_count == 0:
        return

    # テスト用
    # dt = dt - datetime.timedelta(days=1)

    # YouTube動画チェック（今の時間から5時間前までの動画）
    # dt_today = dt.replace(hour=0, second=0, microsecond=0)
    dt_bf5 = dt_utc - datetime.timedelta(hours=5)
    date = datetime.datetime.strftime(dt_bf5, '%Y-%m-%dT%H:%M:%S.%fZ')
    video_id = youtube.get_video(channel_id, date, q_list)

    if not video_id:
        return

    # 作業フォルダ作成
    work_dir = AUDIO_DIR +  date_str + "/"
    os.makedirs(work_dir, exist_ok=True)

    # YouTubeをMP3に
    mp3_file = youtube_mp3(video_id, work_dir)

    # OpenAIクライアント作成
    client = OpenAI()

    # MP3を文字起こし
    live_text = whisper_audio(client, mp3_file)

    # 大谷の実況だけ抽出
    live_text_ex = extract_live(OpenAI(), live_text)

     # 翻訳
    live_text_ja = trans_text(live_text_ex)

    # ポスト
    url = YOUTUBE_URL + video_id

    post_text = live_text_ja[0:120] + "\n\n#大谷ホームラン\n" +url

    rep_text = "(英語原文)\n\n" + live_text_ex[0:268-len(url)-1]

    # クライアント作成
    Client = tweepy.Client(BEARER_TOKEN,API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)

    # 翻訳ポスト
    response = Client.create_tweet(text = post_text)

    # 原文ポスト
    Client.create_tweet(text = rep_text,in_reply_to_tweet_id = response.data['id'])

    # ログ書き込み
    write_log(date_str)

    return

def extract_live(client, text):

    err_msg = ""

    try:

        messages=[

              # 次はMLBの試合でのアナウンサーの実況を文字に起こしています。大谷翔平がホームランを打っているシーンだけ実況を切り取ってください。
              {"role": "system", "content": "The following is a transcription of the announcer's commentary at an MLB game. Please cut out the commentary only for the scene where Shohei Otani is hitting a home run."},
              # 大谷翔平がホームランを打っているシーンだけ実況を切り取ってください
              {"role": "user", "content": "Please only cut out after Shohei Ohtani hits a home run.「" + text + "」"},
          ]

        # GPTに問い合わせ
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=messages,
            # max_tokens=MAX_TOKENS,
        )

        cutout_text = response.choices[0].message.content

        return cutout_text

    except Exception as e:
        print(e)
        return ""

# 今日のポストチェック
def post_check():
    with open(LOG_FILE, 'r') as f:

        post_date = f.read()

    return post_date

def write_log(date):
    with open(LOG_FILE, 'w') as f:
        f.write(date)

def youtube_mp3(id, work_dir):

    # ファイル名は動画のIDに
    mp3_path = work_dir + id

    # フォーマット設定
    ydl_opts = {
        'outtmpl': mp3_path,
        "format": "mp3/bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
            }
        ],
    }

    try :

        url = "https://www.youtube.com/watch?v=" + id

        # yt-dlpでmp3に
        with YoutubeDL(ydl_opts) as ydl:
            result = ydl.download([url])

        return mp3_path + ".mp3"

    except Exception as e:
        print(e)
        return None

def whisper_audio(client, audio_path):

    try:

        audio_file= open(audio_path, "rb")

        trans_text = client.audio.transcriptions.create(model="whisper-1", file=audio_file, response_format="text")

        return trans_text

    except Exception as e:

        print(e)
        return None

def trans_text(text):
    try:

        translator = deepl.Translator(os.environ["DL_API_KEY"])
        tran_text = str(translator.translate_text(text, source_lang=SRC_RANG, target_lang=TRG_RANG))

        return tran_text

    except Exception as e:

        print(e)
        return None

if __name__ == "__main__":
    main()