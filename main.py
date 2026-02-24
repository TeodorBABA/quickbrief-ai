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
    """Funcția principală: Colectează știri, extrage ora SUA și rezumă cu AI"""
    news_list = load_existing_data()
    
    # Seturi pentru filtrare duplicate (titlu normalizat și link)
    processed_titles = {str(item['title']).lower().strip().strip('!?.') for item in news_list}
    processed_links = {item['link'] for item in news_list}
    
    new_found = False

    for name, url in SOURCES.items():
        print(f"Scanning {name}...")
        feed = feedparser.parse(url)
        
        # Luăm primele 5 știri din fiecare sursă
        for entry in feed.entries[:5]:
            title = entry.title.strip()
            norm_title = title.lower().strip().strip('!?.')
            link = entry.link
            
            # 1. Filtrare: Verificăm dacă știrea e deja în baza noastră
            if norm_title not in processed_titles and link not in processed_links:
                print(f"   --> New Global Story: {title[:50]}...")
                
                # 2. Extragere dată originală (Ora SUA/Sursă)
                # Majoritatea feed-urilor folosesc 'published' sau 'updated'
                raw_date = "Recent"
                if hasattr(entry, 'published'):
                    raw_date = entry.published
                elif hasattr(entry, 'updated'):
                    raw_date = entry.updated
                
                # Curățăm data: Din "Tue, 24 Feb 2026 15:30:00 GMT" în "Feb 24, 15:30"
                # Luăm doar partea relevantă pentru cititor
                try:
                    if "," in raw_date: # Format standard RSS
                        clean_date = raw_date.split(',')[1].strip()
                        clean_date = " ".join(clean_date.split()[:3]) + " " + ":".join(clean_date.split()[3].split(':')[:2])
                    else:
                        clean_date = raw_date[:16]
                except:
                    clean_date = raw_date

                try:
                    # 3. Procesare conținut articol
                    article = Article(link)
                    article.download()
                    article.parse()
                    
                    if len(article.text) < 250: # Sărim peste articolele prea scurte
                        continue

                    # 4. Rezumare AI
                    summary = summarize_with_ai(title, article.text)
                    
                    # 5. Creare obiect știre pentru JSON
                    new_item = {
                        "id": int(time.time()),
                        "source": name,
                        "title": title,
                        "link": link,
                        "summary": summary,
                        "date": clean_date # Acum avem ora reală a sursei
                    }
                    
                    news_list.insert(0, new_item)
                    processed_titles.add(norm_title)
                    processed_links.add(link)
                    new_found = True
                    
                    time.sleep(1) # Politicos cu serverele
                    
                except Exception as e:
                    print(f"       Error: {e}")

    if new_found:
        # Păstrăm ultimele 30 de știri pentru viteză
        save_data(news_list[:30])
        print(">>> Success: Database updated with US timestamps.")
    else:
        print(">>> No new stories found.")
if __name__ == "__main__":
    # Verificăm dacă avem cheia API setată în mediu
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in environment variables!")
    else:
        print("--- QUICKBRIEF ENGINE RUNNING ---")
        fetch_all_news()
        print("--- RUN COMPLETED ---")
