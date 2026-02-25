import feedparser
import os
import json
import re
from datetime import datetime, timedelta
from newspaper import Article, Config
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
MAX_AI_CALLS_PER_RUN = 10 # Salvăm resursele și prevenim blocajele

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
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={ "type": "json_object" },
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are an expert Business Intelligence Analyst.\n"
                        "Return a JSON object with EXACTLY these 3 fields:\n"
                        "1. 'is_major': boolean (true ONLY for massive global business events, M&A >$500M, or major policy shifts).\n"
                        "2. 'summary': A detailed, comprehensive 3-paragraph summary of the article for our website. Write at least 150 words.\n"
                        "3. 'social_text': A highly dense, information-packed paragraph (180-220 characters) for an image graphic. "
                        "MAXIMIZE information density: include exact numbers, key names, and the core strategic impact. "
                        "STRICT RULES: Use normal sentence case. NO ALL CAPS. Do not repeat the exact title."
                    )
                },
                {"role": "user", "content": f"Title: {title}\nCategory: {category}\nContent: {full_text[:2000]}"}
            ],
            temperature=0.2,
            timeout=15 # Timeout pentru OpenAI
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"AI Analysis Error: {e}")
        return None

def generate_intelligence_report(all_news):
    today_str = (datetime.utcnow() + timedelta(hours=2)).strftime("%Y-%m-%d")
    summaries = []
    if os.path.exists(SUMMARY_FILE):
        try:
            with open(SUMMARY_FILE, "r", encoding="utf-8") as f:
                summaries = json.load(f)
        except:
            summaries = []

    if any(s.get('date') == today_str for s in summaries):
        return

    if not all_news: return
        
    context = "\n".join([f"- {n['title']}" for n in all_news[:25]])
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Summarize the top global business trends of the last 24 hours in 3 detailed paragraphs."},
                {"role": "user", "content": f"Context:\n{context}"}
            ],
            timeout=20
        )
        summaries.insert(0, {"date": today_str, "content": response.choices[0].message.content})
        with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
            json.dump(summaries[:7], f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Report Error: {e}")

def fetch_all_news():
    if not os.path.exists(JSON_FILE):
        with open(JSON_FILE, "w") as f: json.dump([], f)
    with open(JSON_FILE, "r") as f: old_data = json.load(f)

    # Curățăm datele mai vechi de 24 de ore
    current_time_dt = datetime.utcnow() + timedelta(hours=2)
    cutoff_time = current_time_dt - timedelta(hours=24)
    
    recent_old_data = []
    for item in old_data:
        try:
            item_date = datetime.strptime(item['date'], "%Y-%m-%d %H:%M")
            if item_date >= cutoff_time:
                recent_old_data.append(item)
        except: pass

    existing_links = {item['link'] for item in recent_old_data}
    existing_keywords_list = [get_keywords(item['title']) for item in recent_old_data]
    new_items = []
    current_time_ro = current_time_dt.strftime("%Y-%m-%d %H:%M")

    # Configurare strictă pentru descărcare web
    news_config = Config()
    news_config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    news_config.request_timeout = 10 # Maxim 10 secunde de așteptare pe site

    print(f"--- Starting Scan at {current_time_ro} ---")
    ai_calls_made = 0

    for category, url in SOURCES.items():
        if ai_calls_made >= MAX_AI_CALLS_PER_RUN:
            break

        print(f"Scanning {category}...")
        feed = feedparser.parse(url)
        
        for entry in feed.entries[:25]:
            if ai_calls_made >= MAX_AI_CALLS_PER_RUN:
                print("Limita de siguranță AI atinsă. Restul știrilor vor fi preluate la următoarea rulare.")
                break

            title = entry.title.strip()
            link = entry.link
            if link in existing_links or is_too_similar(title, existing_keywords_list): continue
            
            try:
                # Folosim noua configurare cu timeout
                article = Article(link, config=news_config)
                article.download()
                article.parse()
                if len(article.text) < 300: continue
                
                ai_analysis = analyze_news_with_ai(title, article.text, category)
                ai_calls_made += 1 # Contorizăm apelul
                
                if ai_analysis:
                    print(f"   [+] {title[:50]}...")
                    new_items.append({
                        "category": category,
                        "title": title,
                        "link": link,
                        "summary": ai_analysis.get('summary', ''),
                        "social_text": ai_analysis.get('social_text', ''),
                        "is_major": ai_analysis.get('is_major', False),
                        "date": current_time_ro
                    })
                    existing_keywords_list.append(get_keywords(title))
                    existing_links.add(link)
            except Exception as e:
                print(f"   [SKIP] Timeout sau eroare la {link[:40]}...")
                continue

    final_list = new_items + recent_old_data
    with open(JSON_FILE, "w") as f: json.dump(final_list, f, indent=4)
    print(f"Scan complete. {len(final_list)} items currently in the 24h window.")
    
    generate_intelligence_report(final_list)

if __name__ == "__main__":
    if api_key: fetch_all_news()
