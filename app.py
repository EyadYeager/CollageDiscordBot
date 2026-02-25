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
from duckduckgo_search import DDGS
import requests
import time 
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
    await ctx.send("Scanning for images and preparing to clean up... 🔍")
    
    images = []
    messages_to_delete = []
    
    async for message in ctx.channel.history(limit=50):
        if message.author == bot.user:
            continue
            
        if message.attachments:
            found_image_in_msg = False
            for attachment in message.attachments:
                if any(ext in attachment.url.lower() for ext in ['jpg', 'jpeg', 'png', 'webp']):
                    img_data = await attachment.read()
                    images.append(img_data)
                    found_image_in_msg = True
            
            # If this message had a valid image, save it for deletion later
            if found_image_in_msg:
                messages_to_delete.append(message)
        
        if len(images) >= 9:
            break

    if len(images) < 9:
        return await ctx.send(f"I found {len(images)} images, but I need 9. I won't delete anything yet!")

    processing_msg = await ctx.send("Creating masterpiece and cleaning up chat... 🎨")
    
    # Generate collage
    final_img = create_collage(images[:9])
    
    # Send the final result
    await ctx.send(file=discord.File(fp=final_img, filename="collage_result.png"))

    # Cleanup: Delete the source messages and the "Scanning" message
    try:
        for msg in messages_to_delete:
            await msg.delete()
        await processing_msg.delete()
    except discord.Forbidden:
        await ctx.send("I tried to delete the images but I don't have 'Manage Messages' permissions!")
    except discord.HTTPException:
        pass

def search_image(query):
    """Searches with a specific User-Agent to avoid blocks"""
    # Adding 'icon' or 'square' helps get better 3x3 results
    search_query = f"{query} anime square" 
    
    try:
        with DDGS() as ddgs:
            # We try to get the first 3 results as backups
            results = ddgs.images(search_query, max_results=3)
            if results:
                for res in results:
                    img_url = res['image']
                    # This header makes the bot look like a real person browsing
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}
                    img_res = requests.get(img_url, headers=headers, timeout=5)
                    if img_res.status_code == 200:
                        return img_res.content
        return None
    except Exception as e:
        print(f"Search error for {query}: {e}")
        return None

@bot.command()
async def list(ctx, *, text: str):
    names = [name.strip() for name in text.split(',')]
    if len(names) != 9:
        return await ctx.send(f"I need exactly 9 names! You gave me {len(names)}.")

    status_msg = await ctx.send("Starting your anime search... 🚀")
    images = []
    
    for name in names:
        await status_msg.edit(content=f"Searching for: **{name}**... ({len(images)}/9)")
        img_data = search_image(name)
        
        if img_data:
            images.append(img_data)
        else:
            # Fallback: If search fails, use a grey placeholder so the collage doesn't break
            placeholder = Image.new('RGB', (300, 300), color=(70, 70, 70))
            img_byte_arr = io.BytesIO()
            placeholder.save(img_byte_arr, format='PNG')
            images.append(img_byte_arr.getvalue())
            await ctx.send(f"⚠️ Could not find '{name}', using a placeholder.")
        
        time.sleep(1.5) # Wait 1.5 seconds between searches to avoid being banned

    await status_msg.edit(content="Stitching images together... 🎨")
    final_img = create_collage(images)
    await ctx.send(file=discord.File(fp=final_img, filename="my_list.png"))
    await status_msg.delete()

    
# --- START BOTH ---
if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    bot.run(os.environ.get("DISCORD_TOKEN"))