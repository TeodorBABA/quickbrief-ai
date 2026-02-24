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

SOURCES = {
    "Markets": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=15839069",
    "Tech": "https://techcrunch.com/feed/",
    "Finance": "https://finance.yahoo.com/news/rssindex",
    "Business": "https://www.reutersagency.com/feed/?best-topics=business&post_type=best"
}

JSON_FILE = "news_data.json"

def get_keywords(text):
    """Extrage cuvintele principale pentru a detecta subiecte similare"""
    words = re.findall(r'\w{4,}', text.lower()) # Doar cuvinte de peste 4 litere
    return set(words)

def is_too_similar(new_title, existing_titles_keywords):
    """Verifică dacă subiectul a fost deja discutat (suprapunere de cuvinte cheie)"""
    new_keywords = get_keywords(new_title)
    for existing_keywords in existing_titles_keywords:
        # Dacă peste 70% din cuvintele cheie se suprapun, e același subiect
        intersection = new_keywords.intersection(existing_keywords)
        if len(new_keywords) > 0 and (len(intersection) / len(new_keywords)) > 0.7:
            return True
    return False

def summarize_with_ai(title, full_text, category):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"You are a premium business editor. Summarize this {category} news in 3 professional bullet points in English. Focus on facts and impact. Max 60 words total."},
                {"role": "user", "content": f"Title: {title}\nContent: {full_text}"}
            ],
            max_tokens=200
        )
        return response.choices[0].message.content
    except:
        return None

def fetch_all_news():
    if not os.path.exists(JSON_FILE):
        with open(JSON_FILE, "w") as f: json.dump([], f)
    
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        old_data = json.load(f)

    # Colectăm "amprentele" știrilor existente (titluri + keywords)
    existing_links = {item['link'] for item in old_data}
    existing_keywords_list = [get_keywords(item['title']) for item in old_data]
    
    new_items = []

    for category, url in SOURCES.items():
        print(f"Scanning {category}...")
        feed = feedparser.parse(url)
        
        # Scanăm ultimele 40 de intrări pentru a nu rata nimic
        for entry in feed.entries[:40]:
            title = entry.title.strip()
            link = entry.link
            
            # 1. Filtru Link
            if link in existing_links: continue
            
            # 2. Filtru Similitudine Subiect (Anti-Duplicat între surse)
            if is_too_similar(title, existing_keywords_list):
                print(f"   (Skipped similar topic: {title[:40]}...)")
                continue
                
            try:
                article = Article(link)
                article.download()
                article.parse()
                
                if len(article.text) < 300: continue
                
                summary = summarize_with_ai(title, article.text, category)
                if not summary: continue
                
                # Extragem data publicării
                raw_date = entry.get('published', entry.get('updated', 'Recent'))
                try:
                    clean_date = " ".join(raw_date.split(',')[1].strip().split()[:3]) + " " + ":".join(raw_date.split(',')[1].strip().split()[3].split(':')[:2])
                except:
                    clean_date = raw_date[:16]

                new_news = {
                    "id": int(time.time() + len(new_items)),
                    "category": category,
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "date": clean_date
                }
                
                new_items.append(new_news)
                existing_keywords_list.append(get_keywords(title))
                existing_links.add(link)
                print(f"   [ADDED] {title[:50]}")
                
                time.sleep(1) # Safety delay
            except:
                continue

    # Salvăm rezultatele: Cele mai noi la început, maxim 50 de articole total
    final_list = new_items + old_data
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(final_list[:50], f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    if api_key:
        fetch_all_news()
