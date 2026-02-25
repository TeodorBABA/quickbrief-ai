import json
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont

def create_post_image(title, category, date_str):
    # 1. Configurare Canvas (1080x1080 pentru Instagram)
    width, height = 1080, 1080
    bg_color = (10, 10, 10)      # Negru mat
    accent_color = (59, 130, 246) # Albastru Briefly
    text_color = (255, 255, 255)  # Alb pur

    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # 2. Gestionare Fonturi (Soluție anti-eroare pentru GitHub Actions)
    try:
        # Încercăm să folosim un font de sistem dacă există, altfel fallback la 60px
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 65)
        font_meta = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 35)
    except:
        # Dacă nu sunt fonturi instalate pe serverul GitHub, Pillow va folosi fontul default
        # (Aici e problema de vizibilitate, dar codul nu va mai crăpa)
        font_title = ImageFont.load_default()
        font_meta = font_title

    # 3. Desenare Header (Categorie și Dată)
    # Chenar pentru categorie
    draw.rectangle([60, 60, 220, 110], outline=accent_color, width=3)
    draw.text((85, 72), category.upper(), fill=accent_color, font=font_meta)
    
    # Dată în dreapta
    draw.text((780, 72), date_str.split(' ')[0], fill=(150, 150, 150), font=font_meta)

    # 4. Desenare Titlu (cu auto-wrap pentru a nu ieși din cadru)
    margin = 60
    offset = 250
    # wrap la ~20 caractere pentru a păstra textul mare și lizibil
    wrapped_lines = textwrap.wrap(title, width=22) 

    for line in wrapped_lines:
        draw.text((margin, offset), line, fill=text_color, font=font_title)
        offset += 90 # Spațiere între rânduri

    # 5. Adăugare Branding Briefly.life jos
    draw.text((60, 950), "BRIEFLY.LIFE", fill=accent_color, font=font_meta)
    draw.rectangle([60, 930, 1020, 932], fill=(30, 30, 30)) # Linie separatoare fină

    # Salvare
    img.save("last_news_post.jpg", quality=95)
    print("Succes! Imaginea a fost generată: last_news_post.jpg")

if __name__ == "__main__":
    if os.path.exists("news_data.json"):
        with open("news_data.json", "r", encoding="utf-8") as f:
            news_list = json.load(f)
            if news_list:
                # Luăm cea mai proaspătă știre
                top_news = news_list[0]
                create_post_image(
                    title=top_news['title'],
                    category=top_news['category'],
                    date_str=top_news['date']
                )
    else:
        print("Eroare: news_data.json nu a fost găsit!")
