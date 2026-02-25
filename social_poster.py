import json
from PIL import Image, ImageDraw, ImageFont
import os

def create_post_image(title, category, date_str):
    # 1. Setări dimensiuni (Instagram Square: 1080x1080)
    width, height = 1080, 1080
    background_color = (10, 10, 10) # Aproape negru
    accent_color = (59, 130, 246)    # Albastru Briefly
    
    img = Image.new('RGB', (width, height), color=background_color)
    draw = ImageDraw.Draw(img)
    
    # 2. Încărcare Font (Folosim unul standard de sistem dacă nu ai .ttf)
    try:
        # Dacă urci un fișier .ttf în GitHub, pune drumul spre el aici
        font_title = ImageFont.truetype("Arial.ttf", 60)
        font_meta = ImageFont.truetype("Arial.ttf", 30)
    except:
        font_title = ImageFont.load_default()
        font_meta = ImageFont.load_default()

    # 3. Desenează Categoria (chenar albastru)
    draw.rectangle([50, 50, 200, 100], outline=accent_color, width=3)
    draw.text((75, 65), category.upper(), fill=accent_color, font=font_meta)
    
    # 4. Adaugă Data
    draw.text((850, 65), date_str, fill=(100, 100, 100), font=font_meta)

    # 5. Adaugă Titlul (cu wrap pentru text lung)
    import textwrap
    lines = textwrap.wrap(title, width=25)
    y_text = 250
    for line in lines:
        draw.text((50, y_text), line, fill=(255, 255, 255), font=font_title)
        y_text += 80

    # Salvează imaginea
    img.save("last_news_post.jpg")
    print("Imaginea a fost generată cu succes: last_news_post.jpg")

if __name__ == "__main__":
    # Testăm cu ultima știre din JSON
    with open("news_data.json", "r") as f:
        data = json.load(f)
        if data:
            latest = data[0]
            create_post_image(latest['title'], latest['category'], latest['date'])
