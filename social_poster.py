import json
import os
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
    # Căutăm fontul; am lăsat fallback-urile adăugate anterior pentru siguranță
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf"
    ]
    font_path = next((p for p in paths if os.path.exists(p)), None)
    
    try:
        if font_path:
            return {
                'title': ImageFont.truetype(font_path, 72),
                'body': ImageFont.truetype(font_path.replace("-Bold", "").replace("bd", ""), 42),
                'meta': ImageFont.truetype(font_path, 30)
            }
    except Exception as e:
        print(f"Eroare la încărcarea fontului: {e}")
        
    print("Avertisment: Fonturile custom nu au fost găsite. Se folosește fontul default.")
    return {'title': ImageFont.load_default(), 'body': ImageFont.load_default(), 'meta': ImageFont.load_default()}

def wrap_text_by_pixels(text, font, max_width):
    """
    Împarte textul în rânduri bazându-se pe lățimea reală a pixelilor, nu pe numărul de caractere.
    """
    if not text:
        return []
    
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        # Testăm cum ar arăta linia dacă am adăuga cuvântul curent
        test_line = current_line + " " + word if current_line else word
        
        # Măsurăm lățimea în pixeli a liniei de test
        length = font.getlength(test_line) if hasattr(font, 'getlength') else font.getsize(test_line)[0]
        
        if length <= max_width:
            current_line = test_line
        else:
            # Dacă depășește lățimea maximă, salvăm linia curentă și începem una nouă
            if current_line:
                lines.append(current_line)
            current_line = word
            
    if current_line:
        lines.append(current_line)
        
    return lines

def generate_social_image(news_item):
    # Dimensiune Portrait Instagram (4:5)
    img = Image.new('RGB', (1080, 1350), color=BG_COLOR)
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()

    # Margini și layout
    margin = 80
    max_text_width = 1080 - (margin * 2) # Lățimea maximă disponibilă pentru text (920px)
    y_cursor = 100

    # 1. Header: Categorie și "MAJOR"
    category_text = f"{news_item.get('category', 'ALERT').upper()} • EXECUTIVE INTELLIGENCE"
    draw.text((margin, y_cursor), category_text, fill=ACCENT_COLOR, font=fonts['meta'])
    
    # 2. Titlu (Încadrare dinamică în funcție de pixeli)
    y_cursor += 80
    title_text = news_item.get('title', 'No Title')
    title_lines = wrap_text_by_pixels(title_text, fonts['title'], max_text_width)
    
    for line in title_lines[:4]: # Permitem până la 4 rânduri pentru titlu
        draw.text((margin, y_cursor), line, fill=TEXT_WHITE, font=fonts['title'])
        # Calculăm înălțimea rândului pentru a coborî cursorul exact cât trebuie + padding
        bbox = fonts['title'].getbbox(line) if hasattr(fonts['title'], 'getbbox') else (0,0,0,72)
        line_height = bbox[3] - bbox[1] if bbox[3] > 0 else 72
        y_cursor += line_height + 20

    # 3. Linie Accent
    y_cursor += 40
    draw.line([margin, y_cursor, margin + 150, y_cursor], fill=ACCENT_COLOR, width=10)
    
    # 4. Body (social_text generat de AI)
    y_cursor += 80
    body_text = news_item.get('social_text', "No strategic briefing available.")
    body_lines = wrap_text_by_pixels(body_text, fonts['body'], max_text_width)
    
    for line in body_lines[:10]: # Permitem până la 10 rânduri pentru textul principal
        draw.text((margin, y_cursor), line, fill=TEXT_GRAY, font=fonts['body'])
        bbox = fonts['body'].getbbox(line) if hasattr(fonts['body'], 'getbbox') else (0,0,0,42)
        line_height = bbox[3] - bbox[1] if bbox[3] > 0 else 42
        y_cursor += line_height + 15

    # 5. Footer Branding
    draw.rectangle([0, 1230, 1080, 1350], fill=(15, 15, 15))
    draw.text((margin, 1270), "BRIEFLY.LIFE", fill=TEXT_WHITE, font=fonts['meta'])
    
    # Aliniem "TERMINAL LIVE" exact la marginea din dreapta
    terminal_text = "TERMINAL LIVE"
    w = fonts['meta'].getlength(terminal_text) if hasattr(fonts['meta'], 'getlength') else fonts['meta'].getsize(terminal_text)[0]
    draw.text((1080 - margin - w, 1270), terminal_text, fill=ACCENT_COLOR, font=fonts['meta'])

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
        print("Nu s-a găsit nicio știre majoră nouă.")
