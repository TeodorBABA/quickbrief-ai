import os
import requests
import json

# Configurare din GitHub Secrets
DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK_URL')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')

IMAGE_PATH = "last_news_post.jpg"
JSON_FILE = "news_data.json"

def get_latest_posted_news():
    try:
        if not os.path.exists(JSON_FILE):
            return None
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            news_list = json.load(f)
            # Căutăm ultima știre marcată ca majoră
            for item in reversed(news_list):
                if item.get('is_major') == True:
                    return item
    except Exception as e:
        print(f"Eroare citire JSON: {e}")
    return None

def send_to_discord(news):
    if not DISCORD_WEBHOOK: return
    
    # Folosim .get() pentru a evita KeyError
    social_description = news.get('social_text', "Detailed strategic briefing available in the link below.")
    
    payload = {
        "embeds": [{
            "title": f"🚨 {news.get('title', 'Intelligence Update')}",
            "description": social_description,
            "url": news.get('link', 'https://briefly.life'),
            "color": 3869166,
            "footer": {"text": "Briefly Intelligence Sync • Executive Briefing"}
        }]
    }
    
    try:
        requests.post(DISCORD_WEBHOOK, json=payload)
        if os.path.exists(IMAGE_PATH):
            with open(IMAGE_PATH, 'rb') as f:
                requests.post(DISCORD_WEBHOOK, files={'file': f})
    except Exception as e:
        print(f"Discord Error: {e}")

def send_to_telegram(news):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    
    title = news.get('title', 'Intelligence Update')
    social = news.get('social_text', 'New strategic update available.')
    link = news.get('link', 'https://briefly.life')
    
    caption = f"🚀 *NEW CONTENT READY*\n\n*{title}*\n\n{social}\n\n🔗 {link}"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    
    try:
        if os.path.exists(IMAGE_PATH):
            with open(IMAGE_PATH, 'rb') as f:
                data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "parse_mode": "Markdown"}
                requests.post(url, data=data, files={'photo': f})
    except Exception as e:
        print(f"Telegram Error: {e}")

def send_to_x(news):
    if not TWITTER_BEARER_TOKEN: return
    
    url = "https://api.twitter.com/2/tweets"
    headers = {
        "Authorization": f"Bearer {TWITTER_BEARER_TOKEN}",
        "Content-Type": "application/json"
    }
    title = news.get('title', 'No Title')
    link = news.get('link', '')
    
    tweet_text = f"🚨 {title}\n\nRead more: {link}\n#BrieflyIntelligence #TechNews"
    
    try:
        payload = {"text": tweet_text[:280]}
        requests.post(url, json=payload, headers=headers)
    except Exception as e:
        print(f"X Error: {e}")

if __name__ == "__main__":
    news_item = get_latest_posted_news()
    if news_item:
        print(f"Distribuim: {news_item.get('title', 'Unknown')}")
        send_to_discord(news_item)
        send_to_telegram(news_item)
        send_to_x(news_item)
    else:
        print("Nu există știre majoră nouă de distribuit.")
