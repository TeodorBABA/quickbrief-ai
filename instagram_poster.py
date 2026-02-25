import os
import json
import requests

JSON_FILE = "news_data.json"
LOG_FILE = "posted_ids.txt"

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

def post_to_make():
    webhook_url = os.getenv("MAKE_WEBHOOK_URL")
    if not webhook_url:
        print("Eroare: Lipsește MAKE_WEBHOOK_URL din GitHub Secrets.")
        return

    news_item = get_latest_news_item()
    if not news_item:
        print("Eroare: Nu am putut găsi știrea.")
        return

    # Extragem ID-ul unic al actualizării pentru a evita cache-ul
    commit_hash = os.getenv("COMMIT_HASH", "main")
    
    # Construim link-ul public către imaginea ta din GitHub
    image_url = f"https://raw.githubusercontent.com/TeodorBABA/quickbrief-ai/{commit_hash}/last_news_post.jpg"

    caption = f"🚨 {news_item.get('title')}\n\n📊 {news_item.get('social_text')}\n\n💼 Categorie: {news_item.get('category').upper()}\n.\n.\n.\n#businessintelligence #executivebriefing #markets #tech #finance #brieflylife #news"

    payload = {
        "image_url": image_url,
        "caption": caption
    }

    print(f"Trimitem datele către Make.com folosind imaginea: {image_url}")
    
    # Trimitem datele către Webhook-ul tău
    response = requests.post(webhook_url, json=payload)
    
    if response.status_code == 200:
        print("✅ Datele au fost transmise cu succes către Make.com!")
    else:
        print(f"❌ Eroare la transmitere: {response.status_code} - {response.text}")

if __name__ == "__main__":
    post_to_make()
