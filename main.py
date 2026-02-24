import feedparser
import os
import time
import json
from datetime import datetime
from newspaper import Article
from openai import OpenAI

# --- CONFIGURARE ---
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Surse organizate pe categorii
SOURCES = {
    "Markets": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=15839069",
    "Tech": "https://techcrunch.com/feed/",
    "Finance": "https://finance.yahoo.com/news/rssindex",
    "Business": "https://www.reutersagency.com/feed/?best-topics=business&post_type=best"
}

JSON_FILE = "news_data.json"

def summarize_with_ai(title, full_text, category):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"You are a premium business editor for the {category} section. Summarize this in 3 punchy, executive bullet points in English. Focus on the 'so what?'."},
                {"role": "user", "content": f"Title: {title}\nContent: {full_text}"}
            ],
            max_tokens=250
        )
        return response.choices[0].message.content
    except:
        return "Summary unavailable."

def fetch_all_news():
    news_list = [] # Începem cu o listă goală pentru a păstra doar ce e proaspăt
    # Luăm totuși datele vechi pentru a nu repeta titlurile procesate vreodată
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            old_data = json.load(f)
            processed_titles = {item['title'].lower()[:50] for item in old_data}
    else:
        processed_titles = set()

    new_items = []

    for category, url in SOURCES.items():
        print(f"Scanning {category}...")
        feed = feedparser.parse(url)
        
        for entry in feed.entries[:8]:
            title = entry.title.strip()
            # Detectăm duplicate prin primele 50 de caractere ale titlului
            title_id = title.lower()[:50]
            
            if title_id not in processed_titles:
                try:
                    article = Article(entry.link)
                    article.download()
                    article.parse()
                    
                    if len(article.text) < 300: continue
                    
                    summary = summarize_with_ai(title, article.text, category)
                    
                    new_items.append({
                        "id": int(time.time() + len(new_items)),
                        "category": category,
                        "source": "Global Source",
                        "title": title,
                        "link": entry.link,
                        "summary": summary,
                        "date": "Just now"
                    })
                    processed_titles.add(title_id)
                    time.sleep(1)
                except: continue

    # Combinăm știrile noi cu cele vechi și păstrăm top 40
    final_list = new_items + (old_data if os.path.exists(JSON_FILE) else [])
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(final_list[:40], f, indent=4)

if __name__ == "__main__":
    if api_key: fetch_all_news()
