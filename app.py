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
import json 

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
    url = "https://google.serper.dev/images"
    api_key = os.environ.get("SERPER_API_KEY")
    
    if not api_key:
        print("❌ CRITICAL: SERPER_API_KEY is missing!")
        return None

    # We use 'anime portrait' or 'anime icon' for better results
    payload = json.dumps({"q": f"{query} anime icon", "num": 3})
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        data = response.json()
        
        # This will show up in your Render Logs so we can see what's wrong
        if "images" in data and len(data["images"]) > 0:
            img_url = data["images"][0]["imageUrl"]
            img_res = requests.get(img_url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
            if img_res.status_code == 200:
                return img_res.content
        else:
            print(f"❓ No search results for: {query}")
            
    except Exception as e:
        print(f"⚠️ Search Error: {e}")
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
            # Create a placeholder if image fails
            placeholder = Image.new('RGB', (300, 300), color=(50, 50, 50))
            img_byte_arr = io.BytesIO()
            placeholder.save(img_byte_arr, format='PNG')
            images.append(img_byte_arr.getvalue())
            await ctx.send(f"⚠️ Could not find '{name}', using a placeholder.")

    await status_msg.edit(content="Stitching images together... 🎨")
    final_img = create_collage(images)
    await ctx.send(file=discord.File(fp=final_img, filename="my_list.png"))
    await status_msg.delete()
    
# --- START BOTH ---
if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    bot.run(os.environ.get("DISCORD_TOKEN"))