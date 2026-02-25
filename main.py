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

SOURCES = {
    "Markets": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=15839069",
    "Tech": "https://techcrunch.com/feed/",
    "Finance": "https://finance.yahoo.com/news/rssindex",
    "Business": "https://www.cnbc.com/id/10001147/device/rss/rss.html"
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

def analyze_news_with_ai(title, full_text, category):
    """
    Analizează știrea pentru a determina dacă este MAJORĂ și generează
    conținut structurat pentru site și Instagram.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={ "type": "json_object" }, # Forțăm răspuns JSON strict
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are an elite Business Intelligence Analyst. Your job is to filter noise."
                        "Determine if this news constitutes a MAJOR GLOBAL BUSINESS EVENT "
                        "(e.g., M&A >$500M, C-suite change at Fortune 500, significant policy shift, major breakthrough)."
                        "\n\nReturn a JSON object with exactly these fields:\n"
                        "1. 'is_major': boolean (true ONLY if it's a huge, impactful deal/event)\n"
                        "2. 'website_summary': 'A professional 3-bullet point summary for a website (max 60 words total).'\n"
                        "3. 'social_headline': 'ONE single, powerful, uppercase sentence under 120 chars that encapsulates the impact for an Instagram image. Do NOT use bullet points.'"
                    )
                },
                {"role": "user", "content": f"Title: {title}\nNews Category: {category}\nContent excerpt: {full_text[:1500]}"}
            ],
            temperature=0.3 # Mai puțin creativ, mai analitic
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"AI Analysis Error: {e}")
        return None

def fetch_all_news():
    if not os.path.exists(JSON_FILE):
        with open(JSON_FILE, "w") as f: json.dump([], f)
    with open(JSON_FILE, "r") as f: old_data = json.load(f)

    existing_links = {item['link'] for item in old_data}
    existing_keywords_list = [get_keywords(item['title']) for item in old_data]
    new_items = []
    # Ora României
    current_time_ro = (datetime.utcnow() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")

    print(f"--- Starting Scan at {current_time_ro} ---")

    for category, url in SOURCES.items():
        print(f"Scanning {category}...")
        feed = feedparser.parse(url)
        # Scanăm doar primele 7 pentru eficiență, căutăm doar "crema"
        for entry in feed.entries[:7]:
            title = entry.title.strip()
            link = entry.link
            if link in existing_links or is_too_similar(title, existing_keywords_list): continue
            
            try:
                article = Article(link)
                article.download(); article.parse()
                if len(article.text) < 300: continue
                
                # Analizăm cu AI
                ai_analysis = analyze_news_with_ai(title, article.text, category)
                
                if ai_analysis:
                    status = "[MAJOR]" if ai_analysis['is_major'] else "[Minor]"
                    print(f"   {status} {title[:50]}...")
                    
                    new_items.append({
                        "category": category,
                        "title": title,
                        "link": link,
                        # Salvăm datele structurate
                        "summary": ai_analysis['website_summary'],
                        "short_summary": ai_analysis['social_headline'], # Asta merge pe poză
                        "is_major": ai_analysis['is_major'],
                        "date": current_time_ro
                    })
                    existing_keywords_list.append(get_keywords(title))
                    existing_links.add(link)
            except Exception as e:
                print(f"Error processing {link}: {e}")
                continue

    # Adăugăm cele noi la începutul listei
    final_list = new_items + old_data
    # Păstrăm doar ultimele 50 de știri în JSON pentru a nu-l aglomera
    with open(JSON_FILE, "w") as f: json.dump(final_list[:50], f, indent=4)
    print("Scan complete. Data saved.")

if __name__ == "__main__":
    if api_key: fetch_all_news()
