import json
import os
import textwrap
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURARE ȘI MEMORIE ---
POSTED_LOG = "posted_ids.txt"
JSON_FILE = "news_data.json"
# Culorile tale premium
BG_COLOR = (10, 10, 10)    
ACCENT_COLOR = (59, 130, 246) 
TEXT_WHITE = (250, 250, 250)
TEXT_GRAY = (163, 163, 163)

def get_fonts():
    # Acum va găsi garantat fontul datorită instalării din fișierul .yml
    f_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    f_path_reg = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    try:
        return {
            'title': ImageFont.truetype(f_path, 72),
            'body': ImageFont.truetype(f_path_reg, 42),
            'meta': ImageFont.truetype(f_path, 30)
        }
    except:
        print("Avertisment: Fonturile custom nu au fost găsite. Se folosește fontul default.")
        return {'title': ImageFont.load_default(), 'body': ImageFont.load_default(), 'meta': ImageFont.load_default()}

def generate_social_image(news_item):
    # Dimensiune Portrait Instagram (4:5)
    img = Image.new('RGB', (1080, 1350), color=BG_COLOR)
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()

    # Margini și layout
    margin = 80
    y_cursor = 100

    # 1. Header: Categorie și "MAJOR"
    category_text = f"{news_item.get('category', 'ALERT').upper()} • EXECUTIVE INTELLIGENCE"
    draw.text((margin, y_cursor), category_text, fill=ACCENT_COLOR, font=fonts['meta'])
    
    # 2. Titlu
    y_cursor += 80
    title_lines = textwrap.wrap(news_item.get('title', 'No Title'), width=22)
    for line in title_lines[:3]:
        draw.text((margin, y_cursor), line, fill=TEXT_WHITE, font=fonts['title'])
        y_cursor += 90

    # 3. Linie Accent
    y_cursor += 60
    draw.line([margin, y_cursor, margin + 150, y_cursor], fill=ACCENT_COLOR, width=10)
    
    # 4. Body (social_text generat de AI)
    y_cursor += 100
    body_text = news_item.get('social_text', "No strategic briefing available.")
    body_lines = textwrap.wrap(body_text, width=40)
    for line in body_lines[:8]:
        draw.text((margin, y_cursor), line, fill=TEXT_GRAY, font=fonts['body'])
        y_cursor += 55

    # 5. Footer Branding
    draw.rectangle([0, 1230, 1080, 1350], fill=(15, 15, 15))
    draw.text((margin, 1270), "BRIEFLY.LIFE", fill=TEXT_WHITE, font=fonts['meta'])
    draw.text((800, 1270), "TERMINAL LIVE", fill=ACCENT_COLOR, font=fonts['meta'])

    img.save("last_news_post.jpg", quality=95)
    return True

if __name__ == "__main__":
    if not os.path.exists(JSON_FILE):
        print("Eroare: news_data.json nu există.")
        exit()

    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            news_list = json.load(f)
    except Exception as e:
        print(f"Eroare la citirea JSON: {e}")
        exit()

    # Căutăm cea mai recentă știre MAJORĂ care nu a fost încă postată
    target_news = None
    posted_ids = []
    
    if os.path.exists(POSTED_LOG):
        with open(POSTED_LOG, "r") as f:
            posted_ids = f.read().splitlines()

    for item in news_list:
        if item.get('is_major') == True and item.get('link') not in posted_ids:
            target_news = item
            break 

    if target_news:
        print(f"Postăm știrea majoră: {target_news.get('title', 'Unknown')}")
        if generate_social_image(target_news):
            with open(POSTED_LOG, "a") as f:
                f.write(target_news.get('link', '') + "\n")
    else:
        print("Nu s-a găsit nicio știre majoră nouă în ultimele 4 ore.")
