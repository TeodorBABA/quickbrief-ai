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
SUMMARY_FILE = "daily_summaries.json"

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

def generate_intelligence_report(all_news):
    """Generează un rezumat global al zilei"""
    today_str = (datetime.utcnow() + timedelta(hours=2)).strftime("%Y-%m-%d")
    
    try:
        if os.path.exists(SUMMARY_FILE):
            with open(SUMMARY_FILE, "r") as f: summaries = json.load(f)
        else: summaries = []
        
        if any(s['date'] == today_str for s in summaries): return

        # Luăm primele 15 titluri pentru context
        context = "\n".join([f"- {n['title']}" for n in all_news[:15]])
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a Chief Analyst. Summarize the top 3 global business/tech trends of the last 24 hours in impactful paragraphs. Be executive and sharp."},
                {"role": "user", "content": f"Analyze these headlines:\n{context}"}
            ]
        )
        
        new_summary = {"date": today_str, "content": response.choices[0].message.content}
        summaries.insert(0, new_summary)
        with open(SUMMARY_FILE, "w") as f: json.dump(summaries[:7], f, indent=4)
    except Exception as e: print(f"Report Error: {e}")

def fetch_all_news():
    if not os.path.exists(JSON_FILE):
        with open(JSON_FILE, "w") as f: json.dump([], f)
    with open(JSON_FILE, "r") as f: old_data = json.load(f)

    existing_links = {item['link'] for item in old_data}
    existing_keywords_list = [get_keywords(item['title']) for item in old_data]
    new_items = []
    
    # Ora României
    current_time_ro = (datetime.utcnow() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")

    for category, url in SOURCES.items():
        print(f"Scanning {category}...")
        feed = feedparser.parse(url)
        for entry in feed.entries[:15]:
            title = entry.title.strip()
            link = entry.link
            if link in existing_links or is_too_similar(title, existing_keywords_list): continue
            
            try:
                article = Article(link)
                article.download(); article.parse()
                if len(article.text) < 300: continue
                
                summary = summarize_with_ai(title, article.text, category)
                if summary:
                    new_items.append({
                        "category": category,
                        "title": title,
                        "link": link,
                        "summary": summary,
                        "date": current_time_ro
                    })
                    existing_keywords_list.append(get_keywords(title))
                    existing_links.add(link)
                    print(f"   [+] {title[:40]}")
            except: continue

    final_list = new_items + old_data
    final_list.sort(key=lambda x: x['date'], reverse=True)
    
    with open(JSON_FILE, "w") as f: json.dump(final_list[:60], f, indent=4)
    generate_intelligence_report(final_list)

if __name__ == "__main__":
    if api_key: fetch_all_news()
