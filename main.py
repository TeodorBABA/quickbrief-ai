import feedparser
import os
import time
import json
import re
from datetime import datetime
from newspaper import Article
from openai import OpenAI

# --- CONFIGURARE ---
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Am păstrat sursele, dar am ales fluxuri RSS mai stabile unde a fost cazul
SOURCES = {
    "Markets": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=15839069",
    "Tech": "https://techcrunch.com/feed/",
    "Finance": "https://finance.yahoo.com/news/rssindex",
    "Business": "https://www.reutersagency.com/feed/?best-topics=business&post_type=best"
}

JSON_FILE = "news_data.json"

def get_keywords(text):
    """Extrage cuvintele principale pentru a detecta subiecte similare"""
    words = re.findall(r'\w{4,}', text.lower())
    return set(words)

def is_too_similar(new_title, existing_titles_keywords):
    """Verifică dacă subiectul a fost deja discutat"""
    new_keywords = get_keywords(new_title)
    if not new_keywords: return False
    for existing_keywords in existing_titles_keywords:
        intersection = new_keywords.intersection(existing_keywords)
        if (len(intersection) / len(new_keywords)) > 0.7:
            return True
    return False

def summarize_with_ai(title, full_text, category):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"You are a premium business editor. Summarize this {category} news in 3 professional bullet points in English. Focus on facts and impact. Use '•' for bullets. Max 60 words total."},
                {"role": "user", "content": f"Title: {title}\nContent: {full_text}"}
            ],
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI Error: {e}")
        return None

def fetch_all_news():
    # Inițializare fișier dacă nu există
    if not os.path.exists(JSON_FILE):
        with open(JSON_FILE, "w") as f: json.dump([], f)
    
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        old_data = json.load(f)

    existing_links = {item['link'] for item in old_data}
    existing_keywords_list = [get_keywords(item['title']) for item in old_data]
    
    new_items = []

    for category, url in SOURCES.items():
        print(f"Scanning {category}...")
        feed = feedparser.parse(url)
        
        for entry in feed.entries[:15]: # Redus la 15 per sursă pentru viteză și relevanță
            title = entry.title.strip()
            link = entry.link
            
            if link in existing_links: continue
            if is_too_similar(title, existing_keywords_list): continue
                
            try:
                article = Article(link)
                article.download()
                article.parse()
                
                if len(article.text) < 400: continue
                
                summary = summarize_with_ai(title, article.text, category)
                if not summary: continue
                
                # --- LOGICA DE DATĂ REPARATĂ ---
                # Folosim data curentă în format ISO 8601 (YYYY-MM-DD HH:MM)
                # Asta asigură că JavaScript poate sorta corect știrile.
                clean_date = datetime.now().strftime("%Y-%m-%d %H:%M")

                new_news = {
                    "category": category,
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "date": clean_date
                }
                
                new_items.append(new_news)
                existing_keywords_list.append(get_keywords(title))
                existing_links.add(link)
                print(f"   [ADDED] {category}: {title[:50]}...")
                
                time.sleep(1) 
            except Exception as e:
                print(f"Error processing {link}: {e}")
                continue

    # --- SALVARE ȘI SORTARE ---
    # Combinăm știrile noi cu cele vechi
    all_data = new_items + old_data
    
    # Sortăm toată lista după dată (cele mai noi primele) înainte de salvare
    # Astfel JSON-ul este ordonat chiar și înainte de a ajunge în browser
    all_data.sort(key=lambda x: x['date'], reverse=True)

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data[:50], f, indent=4, ensure_ascii=False)
    print(f"Task complete. Total articles: {len(all_data[:50])}")

if __name__ == "__main__":
    if api_key:
        fetch_all_news()
    else:
        print("Error: OPENAI_API_KEY not found.")
