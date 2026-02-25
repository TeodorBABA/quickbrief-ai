import feedparser
import os
import time
import json
import re
from datetime import datetime, timedelta
from newspaper import Article
from openai import OpenAI

# --- CONFIGURARE ---
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Surse testate și stabile
SOURCES = {
    "Markets": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=15839069",
    "Tech": "https://techcrunch.com/feed/",
    "Finance": "https://finance.yahoo.com/news/rssindex",
    "Business": "https://finance.yahoo.com/news/rssbusiness" # Schimbat pentru stabilitate
}

JSON_FILE = "news_data.json"

def get_keywords(text):
    words = re.findall(r'\w{4,}', text.lower())
    return set(words)

def is_too_similar(new_title, existing_titles_keywords):
    new_keywords = get_keywords(new_title)
    if not new_keywords: return False
    for existing_keywords in existing_titles_keywords:
        intersection = new_keywords.intersection(existing_keywords)
        if len(new_keywords) > 0 and (len(intersection) / len(new_keywords)) > 0.7:
            return True
    return False

def summarize_with_ai(title, full_text, category):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"You are a premium business editor. Summarize this {category} news in 3 professional bullet points in English. Focus on facts. Max 60 words total."},
                {"role": "user", "content": f"Title: {title}\nContent: {full_text}"}
            ],
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except:
        return None

def fetch_all_news():
    if not os.path.exists(JSON_FILE):
        with open(JSON_FILE, "w") as f: json.dump([], f)
    
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        old_data = json.load(f)

    existing_links = {item['link'] for item in old_data}
    existing_keywords_list = [get_keywords(item['title']) for item in old_data]
    new_items = []

    # REGLARE ORĂ ROMÂNIA (UTC + 2)
    # Vercel e pe UTC, așa că adunăm 2 ore manual pentru a salva ora RO în JSON
    romania_time = datetime.utcnow() + timedelta(hours=2)
    clean_date = romania_time.strftime("%Y-%m-%d %H:%M")

    for category, url in SOURCES.items():
        print(f"Scanning {category}...")
        feed = feedparser.parse(url)
        
        for entry in feed.entries[:10]:
            title = entry.title.strip()
            link = entry.link
            
            if link in existing_links: continue
            if is_too_similar(title, existing_keywords_list): continue
                
            try:
                article = Article(link)
                article.download()
                article.parse()
                
                if len(article.text) < 300: continue
                
                summary = summarize_with_ai(title, article.text, category)
                if not summary: continue

                new_news = {
                    "category": category,
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "date": clean_date # Ora României salvată direct
                }
                
                new_items.append(new_news)
                existing_keywords_list.append(get_keywords(title))
                existing_links.add(link)
                print(f"   [ADDED] {category}")
                time.sleep(1) 
            except:
                continue

    # Combinăm, sortăm și păstrăm doar ultimele 24h în JSON (opțional, dar recomandat)
    final_list = new_items + old_data
    # Sortare descrescătoare
    final_list.sort(key=lambda x: x['date'], reverse=True)

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(final_list[:50], f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    if api_key:
        fetch_all_news()
