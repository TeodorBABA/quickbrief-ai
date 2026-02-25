import json
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont

def create_post_image(title, short_summary, category, date_str):
    width, height = 1080, 1350
    bg_color = (10, 10, 10)
    accent_color = (59, 130, 246)
    
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Curățăm data (YYYY-MM-DD)
    clean_date = date_str.split(' ')[0]

    # Fonturi
    try:
        f_path = "/usr/share/fonts/truetype/dejavu/"
        font_title = ImageFont.truetype(f"{f_path}DejaVuSans-Bold.ttf", 75)
        font_body = ImageFont.truetype(f"{f_path}DejaVuSans.ttf", 45) # Puțin mai mare pentru că e text puțin
        font_meta = ImageFont.truetype(f"{f_path}DejaVuSans-Bold.ttf", 32)
    except:
        font_title = font_body = font_meta = ImageFont.load_default()

    # --- HEADER ---
    draw.rectangle([60, 70, 260, 125], fill=accent_color)
    draw.text((85, 82), category.upper(), fill=(255,255,255), font=font_meta)
    
    # Aliniere dată la dreapta
    date_w = draw.textlength(clean_date, font=font_meta)
    draw.text((1020 - date_w, 82), clean_date, fill=(150, 150, 150), font=font_meta)

    # --- TITLU ---
    y_cursor = 220
    title_lines = textwrap.wrap(title, width=20)
    for line in title_lines[:3]:
        draw.text((60, y_cursor), line, fill=(255, 255, 255), font=font_title)
        y_cursor += 95

    # Linie decorativă
    y_cursor += 50
    draw.line([60, y_cursor, 400, y_cursor], fill=accent_color, width=7)
    y_cursor += 80

    # --- REZUMAT SCURT (INSTAGRAM VERSION) ---
    # Folosim direct varianta scurtă
    # Dacă AI-ul a pus deja bullet points, le lăsăm, dacă nu, le punem noi
    lines = textwrap.wrap(short_summary, width=40)
    for line in lines[:6]: # Siguranță: max 6 rânduri
        draw.text((60, y_cursor), f"• {line.strip('• ')}", fill=(220, 220, 220), font=font_body)
        y_cursor += 65

    # --- FOOTER ---
    draw.rectangle([0, 1250, 1080, 1350], fill=(20, 20, 20))
    draw.text((60, 1285), "BRIEFLY.LIFE | INSIGHTS", fill=accent_color, font=font_meta)

    # Salvare
    img.save("last_news_post.jpg", quality=95)

if __name__ == "__main__":
    if os.path.exists("news_data.json"):
        with open("news_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            if data:
                item = data[0]
                # AICI E CHEIA: Luăm 'short_summary', dacă nu există facem fallback pe 'summary' tăiat
                s_summary = item.get('short_summary', item.get('summary', ''))[:200]
                
                create_post_image(
                    item.get('title', 'N/A'),
                    s_summary,
                    item.get('category', 'TECH'),
                    item.get('date', '2026-02-25')
                )
