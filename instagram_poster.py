import os
import json
from instagrapi import Client

# --- CONFIGURARE ---
JSON_FILE = "news_data.json"
LOG_FILE = "posted_ids.txt"
IMAGE_FILE = "last_news_post.jpg"

def get_latest_news_item():
    """Găsește informațiile textuale pentru ultima poză generată."""
    if not os.path.exists(LOG_FILE) or not os.path.exists(JSON_FILE):
        return None
    
    with open(LOG_FILE, "r") as f:
        lines = f.read().splitlines()
        if not lines: return None
        last_link = lines[-1] # Ultima știre procesată de social_poster.py

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        news_list = json.load(f)
        
    for item in news_list:
        if item.get("link") == last_link:
            return item
    return None

def post_to_instagram():
    # Preluăm datele de logare din GitHub Secrets
    username = os.getenv("IG_USERNAME")
    password = os.getenv("IG_PASSWORD")

    if not username or not password:
        print("Eroare: Lipsesc credențiale Instagram (IG_USERNAME sau IG_PASSWORD) din GitHub Secrets.")
        return

    if not os.path.exists(IMAGE_FILE):
        print("Nu există nicio imagine nouă de postat. Se pare că social_poster nu a generat nimic acum.")
        return

    news_item = get_latest_news_item()
    if not news_item:
        print("Eroare: Nu am putut găsi textul corespunzător imaginii.")
        return

    # 1. Construim descrierea (Caption-ul)
    caption = f"🚨 {news_item.get('title')}\n\n"
    caption += f"📊 {news_item.get('social_text')}\n\n"
    caption += f"💼 Categorie: {news_item.get('category').upper()}\n"
    caption += ".\n.\n.\n"
    caption += "#businessintelligence #executivebriefing #markets #tech #finance #brieflylife #news"

    # 2. Conectarea la Instagram
    print(f"Încercăm conectarea pe contul: {username}...")
    cl = Client()
    
    try:
        # Logarea pe cont
        cl.login(username, password)
        print("Login reușit! Încărcăm imaginea...")
        
        # Postarea propriu-zisă
        media = cl.photo_upload(IMAGE_FILE, caption)
        print(f"✅ Postare reușită! Link: https://www.instagram.com/p/{media.code}/")
        
        # Ștergem poza de pe server pentru a nu fi postată de două ori accidental
        os.remove(IMAGE_FILE)
        
    except Exception as e:
        print(f"❌ Eroare la postarea pe Instagram: {e}")

if __name__ == "__main__":
    post_to_instagram()
