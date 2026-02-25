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

# --- START BOTH ---
if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    bot.run(os.environ.get("DISCORD_TOKEN"))