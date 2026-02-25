import json
import os
import textwrap
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURARE DESIGN ---
CANVAS_SIZE = (1080, 1350) 
BG_COLOR = (10, 10, 10)    
ACCENT_COLOR = (59, 130, 246) 
TEXT_WHITE = (255, 255, 255)
TEXT_GRAY = (180, 180, 180)

def get_fonts():
    f_path = "/usr/share/fonts/truetype/dejavu/"
    try:
        return {
            'title_big': ImageFont.truetype(f"{f_path}DejaVuSans-Bold.ttf", 75),
            'title_med': ImageFont.truetype(f"{f_path}DejaVuSans-Bold.ttf", 60),
            'headline': ImageFont.truetype(f"{f_path}DejaVuSans.ttf", 45), # Un pic mai mic sa incapa o fraza plina
            'meta_bold': ImageFont.truetype(f"{f_path}DejaVuSans-Bold.ttf", 32)
        }
    except:
        default = ImageFont.load_default()
        return {'title_big': default, 'title_med': default, 'headline': default, 'meta_bold': default}

def create_post_image(news_item):
    title = news_item.get('title', '')
    
    # Luăm noua cheie 'social_insight'
    headline = news_item.get('social_insight', news_item.get('short_summary', ''))
    
    # 🛡️ PROTECȚIE ANTI-TABLOID: Dacă AI-ul a scris 50% sau mai mult cu MAJUSCULE, îl forțăm la normal
    upper_count = sum(1 for c in headline if c.isupper())
    if len(headline) > 0 and (upper_count / len(headline)) > 0.4:
        headline = headline.capitalize()

    category = news_item.get('category', 'NEWS')
    date_str = news_item.get('date', '')

    img = Image.new('RGB', CANVAS_SIZE, color=BG_COLOR)
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()

    # --- 1. HEADER ---
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        clean_date = dt.strftime("%d %b").upper()
    except: clean_date = "RECENT"

    draw.rectangle([60, 70, 260, 130], fill=ACCENT_COLOR)
    draw.text((85, 85), category.upper(), fill=TEXT_WHITE, font=fonts['meta_bold'])
    
    date_w = draw.textlength(clean_date, font=fonts['meta_bold'])
    draw.text((1080 - date_w - 60, 85), clean_date, fill=TEXT_GRAY, font=fonts['meta_bold'])

    # --- 2. TITLU PRINCIPAL ---
    y_cursor = 360 
    
    active_title_font = fonts['title_big'] if len(title) < 60 else fonts['title_med']
    wrap_width = 20 if len(title) < 60 else 25
    
    title_lines = textwrap.wrap(title, width=wrap_width)
    for line in title_lines[:5]: 
        draw.text((60, y_cursor), line, fill=TEXT_WHITE, font=active_title_font)
        y_cursor += active_title_font.size + 15

    # --- 3. LINIE SEPARATOR ---
    y_cursor += 70 
    draw.line([60, y_cursor, 300, y_cursor], fill=ACCENT_COLOR, width=8)
    y_cursor += 100 

    # --- 4. HEADLINE DE IMPACT (Curățat) ---
    headline_lines = textwrap.wrap(headline, width=42)
    for line in headline_lines[:4]:
        draw.text((60, y_cursor), line, fill=TEXT_GRAY, font=fonts['headline'])
        y_cursor += fonts['headline'].size + 20

    # --- 5. FOOTER ---
    draw.rectangle([0, 1250, 1080, 1350], fill=(18, 18, 18))
    draw.text((60, 1285), "BRIEFLY.LIFE | STRATEGIC INSIGHT", fill=ACCENT_COLOR, font=fonts['meta_bold'])

    # --- SALVARE ---
    if not os.path.exists("posts"): os.makedirs("posts")
    img.save("last_news_post.jpg", quality=100)
    
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
            
            major_news_item = next((item for item in data if item.get('is_major') == True), None)
            
            if major_news_item:
                print(f"Major news found: {major_news_item['title']}")
                create_post_image(major_news_item)
            else:
                print("No MAJOR news detected in the current database. Skipping image generation.")
                if os.path.exists("last_news_post.jpg"):
                    os.remove("last_news_post.jpg")
                    print("Removed outdated image file.")

        except Exception as e:
            print(f"Error reading JSON data: {e}")
    else:
        print("news_data.json not found.")
