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

def analyze_news_with_ai(title, full_text, category):
    """
    Analizează știrea pentru a determina dacă este MAJORĂ și generează
    conținut structurat pentru site și Instagram, cu reguli stricte de formatare.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={ "type": "json_object" },
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
                        "3. 'social_headline': 'ONE single, punchy sentence under 120 chars providing the crucial data point or impact. STRICT RULES: Use standard sentence case (NOT ALL CAPS), NO exclamation marks, and DO NOT repeat the exact words from the title.'"
                    )
                },
                {"role": "user", "content": f"Title: {title}\nNews Category: {category}\nContent excerpt: {full_text[:1500]}"}
            ],
            temperature=0.3
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"AI Analysis Error: {e}")
        return None

def generate_intelligence_report(all_news):
    """Generează un rezumat global al zilei pentru site"""
    today_str = (datetime.utcnow() + timedelta(hours=2)).strftime("%Y-%m-%d")
    print(f"--- Attempting to generate Intelligence Report for {today_str} ---")
    
    summaries = []
    if os.path.exists(SUMMARY_FILE):
        try:
            with open(SUMMARY_FILE, "r", encoding="utf-8") as f:
                summaries = json.load(f)
        except:
            summaries = []

    if any(s.get('date') == today_str for s in summaries):
        print("Report for today already exists. Skipping.")
        return

    if not all_news: return
        
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
        summaries.insert(0, {"date": today_str, "content": report_content})
        
        with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
            json.dump(summaries[:7], f, indent=4, ensure_ascii=False)
        print(f"Successfully created/updated {SUMMARY_FILE}")
    except Exception as e:
        print(f"Intelligence Report Error: {e}")

def fetch_all_news():
    if not os.path.exists(JSON_FILE):
        with open(JSON_FILE, "w") as f: json.dump([], f)
    with open(JSON_FILE, "r") as f: old_data = json.load(f)

    existing_links = {item['link'] for item in old_data}
    existing_keywords_list = [get_keywords(item['title']) for item in old_data]
    new_items = []
    current_time_ro = (datetime.utcnow() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")

    print(f"--- Starting Scan at {current_time_ro} ---")

    for category, url in SOURCES.items():
        print(f"Scanning {category}...")
        feed = feedparser.parse(url)
        for entry in feed.entries[:7]:
            title = entry.title.strip()
            link = entry.link
            if link in existing_links or is_too_similar(title, existing_keywords_list): continue
            
            try:
                article = Article(link)
                article.download(); article.parse()
                if len(article.text) < 300: continue
                
                ai_analysis = analyze_news_with_ai(title, article.text, category)
                
                if ai_analysis:
                    status = "[MAJOR]" if ai_analysis.get('is_major') else "[Minor]"
                    print(f"   {status} {title[:50]}...")
                    
                    new_items.append({
                        "category": category,
                        "title": title,
                        "link": link,
                        "summary": ai_analysis.get('website_summary', ''),
                        "short_summary": ai_analysis.get('social_headline', ''),
                        "is_major": ai_analysis.get('is_major', False),
                        "date": current_time_ro
                    })
                    existing_keywords_list.append(get_keywords(title))
                    existing_links.add(link)
            except Exception as e:
                continue

    final_list = new_items + old_data
    with open(JSON_FILE, "w") as f: json.dump(final_list[:60], f, indent=4)
    print("Scan complete. Data saved.")
    
    generate_intelligence_report(final_list)

if __name__ == "__main__":
    if api_key: fetch_all_news()
