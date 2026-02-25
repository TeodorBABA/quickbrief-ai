import os
import json
from instagrapi import Client

# --- CONFIGURARE ---
JSON_FILE = "news_data.json"
LOG_FILE = "posted_ids.txt"
IMAGE_FILE = "last_news_post.jpg"

def get_latest_news_item():
    if not os.path.exists(LOG_FILE) or not os.path.exists(JSON_FILE):
        return None
    
    with open(LOG_FILE, "r") as f:
        lines = f.read().splitlines()
        if not lines: return None
        last_link = lines[-1]

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        news_list = json.load(f)
        
    for item in news_list:
        if item.get("link") == last_link:
            return item
    return None

def post_to_instagram():
    # Preluăm Session ID-ul
    sessionid = os.getenv("IG_SESSIONID")

    if not sessionid:
        print("Eroare: Lipsește IG_SESSIONID din GitHub Secrets.")
        return

    if not os.path.exists(IMAGE_FILE):
        print("Nu există nicio imagine nouă de postat.")
        return

    news_item = get_latest_news_item()
    if not news_item:
        print("Eroare: Nu am putut găsi textul corespunzător imaginii.")
        return

    # Construim descrierea
    caption = f"🚨 {news_item.get('title')}\n\n"
    caption += f"📊 {news_item.get('social_text')}\n\n"
    caption += f"💼 Categorie: {news_item.get('category').upper()}\n"
    caption += ".\n.\n.\n"
    caption += "#businessintelligence #executivebriefing #markets #tech #finance #brieflylife #news"

    print("Încercăm conectarea folosind Session ID...")
    cl = Client()
    
    try:
        # Ne logăm folosind cookie-ul, trecând de blocajul IP-ului
        cl.login_by_sessionid(sessionid)
        print("Autentificare reușită! Încărcăm imaginea...")
        
        media = cl.photo_upload(IMAGE_FILE, caption)
        print(f"✅ Postare reușită! Link: https://www.instagram.com/p/{media.code}/")
        
        os.remove(IMAGE_FILE)
        
    except Exception as e:
        print(f"❌ Eroare la postarea pe Instagram: {e}")

if __name__ == "__main__":
    post_to_instagram()
