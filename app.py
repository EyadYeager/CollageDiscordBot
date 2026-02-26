import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import os
import io
import threading
import requests
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

# --- FLASK SETUP ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

# --- DISCORD BOT SETUP ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def create_collage(img_list, names_list):
    """Stitches images and draws text labels at the bottom"""
    imgs = [Image.open(io.BytesIO(i)).convert("RGB").resize((300, 300)) for i in img_list]
    collage = Image.new("RGB", (900, 900))
    draw = ImageDraw.Draw(collage)
    
    # Try to load a basic font
    try:
        font = ImageFont.load_default()
    except:
        font = None

    for i in range(3):
        for j in range(3):
            index = i * 3 + j
            # Paste the image
            collage.paste(imgs[index], (j * 300, i * 300))
            
            # Draw a semi-transparent black bar for the name
            draw.rectangle([j*300, i*300 + 265, j*300 + 300, i*300 + 300], fill=(0, 0, 0))
            # Write the anime name
            draw.text((j*300 + 10, i*300 + 275), names_list[index][:30], fill="white", font=font)
            
    img_byte_arr = io.BytesIO()
    collage.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def search_image(query):
    """Searches Pixabay for more 'Official' looking art"""
    api_key = os.environ.get("PIXABAY_API_KEY")
    if not api_key:
        return None

    # Changed search to 'official art' and 'photo' type for cleaner results
    search_query = f"{query} anime official art"
    url = f"https://pixabay.com/api/?key={api_key}&q={search_query}&image_type=photo&per_page=3"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("hits"):
            img_url = data["hits"][0]["webformatURL"]
            img_res = requests.get(img_url, timeout=5)
            if img_res.status_code == 200:
                return img_res.content
    except:
        pass
    return None

@bot.command()
async def list(ctx, *, text: str):
    names = [name.strip() for name in text.split(',')]
    if len(names) != 9:
        return await ctx.send(f"I need exactly 9 names! You gave me {len(names)}.")

    status_msg = await ctx.send("Searching for official-style art... 🚀")
    images = []
    
    for name in names:
        await status_msg.edit(content=f"Searching for: **{name}**... ({len(images)}/9)")
        img_data = search_image(name)
        
        if img_data:
            images.append(img_data)
        else:
            # Fallback placeholder if no image found
            placeholder = Image.new('RGB', (300, 300), color=(40, 40, 40))
            img_byte_arr = io.BytesIO()
            placeholder.save(img_byte_arr, format='PNG')
            images.append(img_byte_arr.getvalue())

    await status_msg.edit(content="Generating your labeled 3x3... 🎨")
    final_img = create_collage(images, names)
    await ctx.send(file=discord.File(fp=final_img, filename="anime_list.png"))
    await status_msg.delete()

# --- START BOTH ---
if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    bot.run(os.environ.get("DISCORD_TOKEN"))