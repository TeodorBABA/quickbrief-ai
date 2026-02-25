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
    """Generează un rezumat global al zilei și asigură existența fișierului"""
    # Ora României pentru ID-ul raportului
    today_str = (datetime.utcnow() + timedelta(hours=2)).strftime("%Y-%m-%d")
    print(f"--- Attempting to generate Intelligence Report for {today_str} ---")
    
    summaries = []
    
    # 1. Încercăm să citim fișierul existent
    if os.path.exists(SUMMARY_FILE):
        try:
            with open(SUMMARY_FILE, "r", encoding="utf-8") as f:
                summaries = json.load(f)
        except Exception as e:
            print(f"Error reading summary file: {e}")
            summaries = []

    # 2. Verificăm dacă raportul de azi există deja
    if any(s.get('date') == today_str for s in summaries):
        print("Report for today already exists. Skipping.")
        return

    # 3. Luăm contextul pentru AI (doar dacă avem știri)
    if not all_news:
        print("No news available to summarize.")
        return
        
    context = "\n".join([f"- {n['title']}" for n in all_news[:20]])
    
    try:
        print("Calling OpenAI for Daily Synthesis...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a Chief Business Analyst. Summarize the top 3 global business/tech trends of the last 24 hours in 3 sharp, impactful paragraphs. Use professional, executive English."},
                {"role": "user", "content": f"Context headlines:\n{context}"}
            ]
        )
        
        report_content = response.choices[0].message.content
        new_summary = {"date": today_str, "content": report_content}
        
        # Inserăm la începutul listei
        summaries.insert(0, new_summary)
        
        # 4. SALVARE FORȚATĂ
        with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
            json.dump(summaries[:7], f, indent=4, ensure_ascii=False)
            
        print(f"Successfully created/updated {SUMMARY_FILE}")

    except Exception as e:
        print(f"Critical AI Report Error: {e}")
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
