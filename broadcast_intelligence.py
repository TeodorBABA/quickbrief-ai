import os
import requests
import json
from requests_oauthlib import OAuth1Session # Necesar pentru postarea pe X

# Configurare din GitHub Secrets
DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK_URL')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Cheile corecte pentru X (OAuth 1.0a)
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_SECRET = os.getenv('TWITTER_ACCESS_SECRET')

IMAGE_PATH = "last_news_post.jpg"
JSON_FILE = "news_data.json"
POSTED_LOG = "posted_ids.txt"

def get_latest_posted_news():
    # Sincronizare perfectă: Luăm EXACT știrea pentru care s-a generat imaginea
    try:
        if not os.path.exists(POSTED_LOG) or not os.path.exists(JSON_FILE):
            return None
            
        with open(POSTED_LOG, "r") as f:
            lines = f.read().splitlines()
            if not lines: return None
            last_posted_link = lines[-1] # Extragem link-ul ultimei imagini generate
            
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            news_list = json.load(f)
            for item in news_list:
                if item.get('link') == last_posted_link:
                    return item # Am găsit perechea corectă
    except Exception as e:
        print(f"Eroare sincronizare: {e}")
    return None

def send_to_discord(news):
    if not DISCORD_WEBHOOK: return
    social_desc = news.get('social_text', "Strategic briefing available in the link below.")
    payload = {
        "embeds": [{
            "title": f"🚨 {news.get('title', 'Intelligence Update')}",
            "description": social_desc,
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
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET]):
        print("Lipsesc cheile X.")
        return
        
    title = news.get('title', 'Intelligence Update')
    desc = news.get('social_text', 'Strategic briefing available.')[:130]
    link = news.get('link', '')
    tags = news.get('hashtags', '#BrieflyIntelligence #Business')
    tweet_text = f"🚨 {title}\n\n{desc}...\n\nRead more: {link}\n{tags}"
    
    try:
        # Autentificare sigură pentru a putea POSTA
        twitter = OAuth1Session(TWITTER_API_KEY, client_secret=TWITTER_API_SECRET,
                                resource_owner_key=TWITTER_ACCESS_TOKEN,
                                resource_owner_secret=TWITTER_ACCESS_SECRET)
        url = "https://api.twitter.com/2/tweets"
        payload = {"text": tweet_text[:280]}
        
        response = twitter.post(url, json=payload)
        if response.status_code == 201:
            print("Postat cu succes pe X.")
        else:
            print(f"Eroare X API: {response.text}")
    except Exception as e:
        print(f"Eroare X: {e}")

if __name__ == "__main__":
    news_item = get_latest_posted_news()
    if news_item:
        print(f"Distribuim Sincronizat: {news_item.get('title', 'Unknown')}")
        send_to_discord(news_item)
        send_to_telegram(news_item)
        send_to_x(news_item)
    else:
        print("Nu există știre nouă de distribuit.")
