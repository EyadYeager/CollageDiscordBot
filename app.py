import discord
from discord.ext import commands
from PIL import Image
import os
import io
import threading
from flask import Flask
from dotenv import load_dotenv
load_dotenv()  
from logic import create_3x3_collage

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
    # 1. Look back at the last 50 messages (gives more room for errors)
    await ctx.send("Scanning for images... 🔍")
    
    images = []
    async for message in ctx.channel.history(limit=50):
        # 2. Skip the bot's own messages so they don't count towards the 'limit'
        if message.author == bot.user:
            continue
            
        if message.attachments:
            for attachment in message.attachments:
                if any(ext in attachment.url.lower() for ext in ['jpg', 'jpeg', 'png', 'webp']):
                    img_data = await attachment.read()
                    images.append(img_data)
        
        # Stop once we hit 9
        if len(images) >= 9:
            break

    if len(images) < 9:
        return await ctx.send(f"I found {len(images)} images in recent history, but I need 9. Try waiting 5 seconds for uploads to finish!")

    await ctx.send("Creating your 3x3 masterpiece... 🎨")
    
    # Run the processing in a separate thread so the bot doesn't "freeze"
    final_img = create_collage(images[:9])
    await ctx.send(file=discord.File(fp=final_img, filename="collage_result.png"))

# --- START BOTH ---
if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    bot.run(os.environ.get("DISCORD_TOKEN"))