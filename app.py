import discord
from discord.ext import commands
from PIL import Image
import os
import io
import threading
from flask import Flask

# --- FLASK SETUP (To keep Render happy) ---
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

def create_collage(img_list):
    # Resize all to 300x300
    imgs = [Image.open(io.BytesIO(i)).resize((300, 300)) for i in img_list]
    collage = Image.new("RGB", (900, 900))
    
    for i in range(3):
        for j in range(3):
            collage.paste(imgs[i * 3 + j], (j * 300, i * 300))
            
    img_byte_arr = io.BytesIO()
    collage.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

@bot.command()
async def collage(ctx):
    """Wait for 9 images to be sent or grab the last 9 images in chat"""
    await ctx.send("Send me 9 images (or I will try to grab the last 9 sent here)!")
    
    images = []
    async for message in ctx.channel.history(limit=20):
        if message.attachments:
            for attachment in message.attachments:
                if any(ext in attachment.url.lower() for ext in ['jpg', 'jpeg', 'png']):
                    img_data = await attachment.read()
                    images.append(img_data)
        if len(images) >= 9:
            break

    if len(images) < 9:
        return await ctx.send(f"I only found {len(images)} images. I need 9!")

    await ctx.send("Generating 3x3 collage... 🎨")
    final_img = create_collage(images[:9])
    await ctx.send(file=discord.File(fp=final_img, filename="collage.png"))

# --- START BOTH ---
if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    bot.run(os.environ.get("DISCORD_