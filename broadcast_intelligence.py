import os
import requests
import json

# Configurare din GitHub Secrets
DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK_URL')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN') # Pentru X API v2 (Text Only)

IMAGE_PATH = "last_news_post.jpg"
JSON_FILE = "news_data.json"

def get_latest_posted_news():
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            news_list = json.load(f)
            # Luăm ultima știre care a fost marcată ca majoră (cea procesată de social_poster.py)
            for item in reversed(news_list):
                if item.get('is_major'):
                    return item
    except Exception as e:
        print(f"Eroare citire JSON: {e}")
    return None

def send_to_discord(news):
    if not DISCORD_WEBHOOK: return
    
    payload = {
        "embeds": [{
            "title": f"🚨 {news['title']}",
            "description": news['social_text'],
            "url": news['link'],
            "color": 3869166, # Albastru Accent (59, 130, 246)
            "footer": {"text": "Briefly Intelligence Sync • Executive Briefing"}
        }]
    }
    
    # Trimitem Textul
    requests.post(DISCORD_WEBHOOK, json=payload)
    # Trimitem Imaginea separat (Discord nu permite imagine locală direct în embed via URL simplu fără hosting)
    with open(IMAGE_PATH, 'rb') as f:
        requests.post(DISCORD_WEBHOOK, files={'file': f})

def send_to_telegram(news):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    
    caption = f"🚀 *NEW CONTENT READY*\n\n*{news['title']}*\n\n{news['social_text']}\n\n🔗 {news['link']}"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    
    with open(IMAGE_PATH, 'rb') as f:
        data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "parse_mode": "Markdown"}
        requests.post(url, data=data, files={'photo': f})

def send_to_x(news):
    # X API v2 Free permite postări text-only ușor
    if not TWITTER_BEARER_TOKEN: return
    
    url = "https://api.twitter.com/2/tweets"
    headers = {
        "Authorization": f"Bearer {TWITTER_BEARER_TOKEN}",
        "Content-Type": "application/json"
    }
    tweet_text = f"🚨 {news['title']}\n\nRead more: {news['link']}\n#BrieflyIntelligence #TechNews"
    
    payload = {"text": tweet_text[:280]} # Limită caractere X
    requests.post(url, json=payload, headers=headers)

if __name__ == "__main__":
    news_item = get_latest_posted_news()
    if news_item and os.path.exists(IMAGE_PATH):
        print(f"Distribuim: {news_item['title']}")
        send_to_discord(news_item)
        send_to_telegram(news_item)
        send_to_x(news_item)
    else:
        print("Nu există știre nouă de distribuit.")
