import json
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont

def create_post_image(title, summary, category, date_str):
    # 1. Format Instagram Portrait (4:5 Ratio)
    width, height = 1080, 1350
    bg_color = (15, 15, 15)       # Fundal negru texturat
    accent_color = (59, 130, 246)  # Albastru Briefly
    text_white = (255, 255, 255)
    text_gray = (180, 180, 180)

    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # 2. Incarcare Fonturi (Fallback pentru GitHub Actions)
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
        font_summary = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
        font_meta = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    except:
        font_title = ImageFont.load_default()
        font_summary = font_title
        font_meta = font_title

    # 3. Header: Categorie (Pila albastra)
    draw.rectangle([60, 80, 250, 130], fill=accent_color)
    draw.text((80, 90), category.upper(), fill=text_white, font=font_meta)
    
    # Data (Sus in dreapta)
    draw.text((820, 90), date_str.split(' ')[0], fill=text_gray, font=font_meta)

    # 4. Titlu (Wrap lat)
    margin = 60
    y_cursor = 220
    title_lines = textwrap.wrap(title, width=20)
    for line in title_lines:
        draw.text((margin, y_cursor), line, fill=text_white, font=font_title)
        y_cursor += 90

    # 5. Linie de separare fină
    y_cursor += 40
    draw.line([60, y_cursor, 400, y_cursor], fill=accent_color, width=5)
    y_cursor += 60

    # 6. Rezumat (Summary)
    summary_lines = textwrap.wrap(summary, width=45)
    for line in summary_lines:
        draw.text((margin, y_cursor), line, fill=text_gray, font=font_summary)
        y_cursor += 55

    # 7. Footer: Branding
    draw.rectangle([0, 1250, 1080, 1350], fill=(25, 25, 25))
    draw.text((60, 1285), "BRIEFLY.LIFE | Intelligence Report", fill=accent_color, font=font_meta)

    # 8. Salvare in folderul 'posts'
    if not os.path.exists("posts"):
        os.makedirs("posts")
    
    filename = f"posts/post_{date_str.replace(':', '-').replace(' ', '_')}.jpg"
    img.save(filename, quality=95)
    img.save("last_news_post.jpg", quality=95) # Copie pentru acces rapid
    
    print(f"Imagine generata: {filename}")

if __name__ == "__main__":
    if os.path.exists("news_data.json"):
        with open("news_data.json", "r", encoding="utf-8") as f:
            news_list = json.load(f)
            if news_list:
                latest = news_list[0]
                # Extragem si 'summary' din JSON-ul tau
                create_post_image(
                    title=latest.get('title', 'No Title'),
                    summary=latest.get('summary', 'No summary available.'),
                    category=latest.get('category', 'News'),
                    date_str=latest.get('date', '2026-02-25')
                )
