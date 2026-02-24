import feedparser
import os
import time
import json
from datetime import datetime
from newspaper import Article
from openai import OpenAI

# --- CONFIGURARE ---
# Luăm cheia din "seiful" GitHub (Secrets)
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Sursele globale pentru piața de business/tech
SOURCES = {
    "Reuters Business": "https://www.reutersagency.com/feed/?best-topics=business&post_type=best",
    "CNBC Top News": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
    "TechCrunch": "https://techcrunch.com/feed/",
    "Yahoo Finance": "https://finance.yahoo.com/news/rssindex"
}

JSON_FILE = "news_data.json"

def summarize_with_ai(title, full_text):
    """Trimite textul la AI pentru un rezumat executiv în engleză"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a world-class business editor. Summarize the following news for a high-level executive. Use 3 professional, punchy bullet points in English. Focus on the impact. No fluff."
                },
                {"role": "user", "content": f"Title: {title}\n\nContent: {full_text}"}
            ],
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI Error: {str(e)}"

def load_existing_data():
    """Încarcă știrile deja salvate în JSON"""
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return []
    return []

def save_data(data):
    """Salvează lista actualizată în JSON"""
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def fetch_all_news():
    """Funcția principală de colectare și filtrare"""
    news_list = load_existing_data()
    
    # Seturi pentru filtrare duplicate (titlu normalizat și link)
    processed_titles = {str(item['title']).lower().strip().strip('!?.') for item in news_list}
    processed_links = {item['link'] for item in news_list}
    
    new_found = False
    timestamp_now = datetime.now().strftime("%b %d, %H:%M")

    for name, url in SOURCES.items():
        print(f"Scanning {name}...")
        feed = feedparser.parse(url)
        
        # Luăm ultimele 5 știri din fiecare feed pentru verificare
        for entry in feed.entries[:5]:
            title = entry.title.strip()
            norm_title = title.lower().strip().strip('!?.')
            link = entry.link
            
            # Verificăm dacă știrea e deja procesată
            if norm_title not in processed_titles and link not in processed_links:
                print(f"   --> Found New: {title[:50]}...")
                try:
                    article = Article(link)
                    article.download()
                    article.parse()
                    
                    # Verificăm dacă am reușit să extragem text (minim 200 caractere)
                    if len(article.text) < 200:
                        continue

                    summary = summarize_with_ai(title, article.text)
                    
                    new_item = {
                        "id": int(time.time()),
                        "source": name,
                        "title": title,
                        "link": link,
                        "summary": summary,
                        "date": timestamp_now
                    }
                    
                    news_list.insert(0, new_item) # Cele mai noi apar primele
                    processed_titles.add(norm_title)
                    processed_links.add(link)
                    new_found = True
                    
                    # Mică pauză între cereri pentru a fi "politicoși" cu serverele
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"       Error processing article: {e}")

    if new_found:
        # Păstrăm un istoric de 30 de știri pentru a menține site-ul rapid
        save_data(news_list[:30])
        print(">>> JSON file updated with new summaries.")
    else:
        print(">>> No new updates found at this time.")

if __name__ == "__main__":
    # Verificăm dacă avem cheia API setată în mediu
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in environment variables!")
    else:
        print("--- QUICKBRIEF ENGINE RUNNING ---")
        fetch_all_news()
        print("--- RUN COMPLETED ---")
