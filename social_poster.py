import json
import os
import textwrap
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURARE DESIGN ---
CANVAS_SIZE = (1080, 1350) # Instagram Portrait
BG_COLOR = (10, 10, 10)    # Negru "Premium"
ACCENT_COLOR = (59, 130, 246) # Albastru Briefly
TEXT_WHITE = (255, 255, 255)
TEXT_GRAY = (180, 180, 180)

def get_fonts():
    """Încearcă să încarce fonturi profesionale de pe serverul Linux"""
    f_path = "/usr/share/fonts/truetype/dejavu/"
    try:
        # Fonturi mari pentru titlu, medii pentru headline, mici pentru meta
        return {
            'title_big': ImageFont.truetype(f"{f_path}DejaVuSans-Bold.ttf", 75),
            'title_med': ImageFont.truetype(f"{f_path}DejaVuSans-Bold.ttf", 60),
            'headline': ImageFont.truetype(f"{f_path}DejaVuSans.ttf", 48),
            'meta_bold': ImageFont.truetype(f"{f_path}DejaVuSans-Bold.ttf", 32)
        }
    except:
        # Fallback de urgență
        default = ImageFont.load_default()
        return {'title_big': default, 'title_med': default, 'headline': default, 'meta_bold': default}

def create_post_image(news_item):
    title = news_item.get('title', '')
    # Folosim 'short_summary' care acum este un singur headline puternic
    headline = news_item.get('short_summary', '')
    category = news_item.get('category', 'NEWS')
    date_str = news_item.get('date', '')

    img = Image.new('RGB', CANVAS_SIZE, color=BG_COLOR)
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()

    # --- 1. HEADER (Dată și Categorie) ---
    # Formatare dată curată (ex: 25 FEB)
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        clean_date = dt.strftime("%d %b").upper()
    except: clean_date = "RECENT"

    # Tag Categorie
    draw.rectangle([60, 70, 260, 130], fill=ACCENT_COLOR)
    draw.text((85, 85), category.upper(), fill=TEXT_WHITE, font=fonts['meta_bold'])
    
    # Data în dreapta
    date_w = draw.textlength(clean_date, font=fonts['meta_bold'])
    draw.text((1080 - date_w - 60, 85), clean_date, fill=TEXT_GRAY, font=fonts['meta_bold'])

    # --- 2. TITLU PRINCIPAL (Dinamic) ---
    y_cursor = 250
    # Alegem fontul în funcție de lungimea titlului
    active_title_font = fonts['title_big'] if len(title) < 60 else fonts['title_med']
    wrap_width = 20 if len(title) < 60 else 25
    
    title_lines = textwrap.wrap(title, width=wrap_width)
    for line in title_lines[:5]: # Max 5 linii
        draw.text((60, y_cursor), line, fill=TEXT_WHITE, font=active_title_font)
        # Creștem cursorul în funcție de mărimea fontului folosit
        y_cursor += active_title_font.size + 15

    # --- 3. LINIE SEPARATOR ---
    y_cursor += 50
    draw.line([60, y_cursor, 300, y_cursor], fill=ACCENT_COLOR, width=8)
    y_cursor += 80

    # --- 4. HEADLINE DE IMPACT (O singură frază) ---
    # Aici era problema înainte. Acum desenăm o singură frază mare.
    headline_lines = textwrap.wrap(headline, width=38)
    for line in headline_lines[:4]:
        draw.text((60, y_cursor), line, fill=TEXT_GRAY, font=fonts['headline'])
        y_cursor += fonts['headline'].size + 20

    # --- 5. FOOTER ---
    draw.rectangle([0, 1250, 1080, 1350], fill=(18, 18, 18))
    draw.text((60, 1285), "BRIEFLY.LIFE | MAJOR DECISION BRIEF", fill=ACCENT_COLOR, font=fonts['meta_bold'])

    # --- SALVARE ---
    if not os.path.exists("posts"): os.makedirs("posts")
    # Salvarea principală
    img.save("last_news_post.jpg", quality=100)
    # Arhivă cu timestamp pentru unicitate
    archive_name = f"posts/major_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    img.save(archive_name, quality=95)
    print(f"Successfully generated Major News Image: {archive_name}")
    return True

if __name__ == "__main__":
    print("Searching for Major News to create post...")
    if os.path.exists("news_data.json"):
        try:
            with open("news_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # --- FILTRUL MAGIC ---
            # Căutăm prima știre care are 'is_major': true
            major_news_item = next((item for item in data if item.get('is_major') == True), None)
            
            if major_news_item:
                print(f"Major news found: {major_news_item['title']}")
                create_post_image(major_news_item)
            else:
                print("No MAJOR news detected in the current database. Skipping image generation.")
                # Putem șterge imaginea veche pentru a nu o reposta din greșeală
                if os.path.exists("last_news_post.jpg"):
                    os.remove("last_news_post.jpg")
                    print("Removed outdated image file.")

        except Exception as e:
            print(f"Error reading JSON data: {e}")
    else:
        print("news_data.json not found.")
