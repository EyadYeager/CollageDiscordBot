from PIL import Image, ImageDraw, ImageFont, ImageOps # Don't forget ImageOps!

def create_collage(img_list, names_list):
    """Stitches images and draws text labels at the bottom"""
    # 1. Create the empty list first!
    imgs = [] 
    
    # 2. Process each image and add it to the list
    for i in img_list:
        img = Image.open(io.BytesIO(i)).convert("RGB")
        # This crops the poster to a square without stretching it
        img = ImageOps.fit(img, (300, 300), centering=(0.5, 0.5))
        imgs.append(img) # Now imgs is defined, so this works!

    collage = Image.new("RGB", (900, 900))
    draw = ImageDraw.Draw(collage)
    
    try:
        font = ImageFont.load_default()
    except:
        font = None

    for i in range(3):
        for j in range(3):
            index = i * 3 + j
            collage.paste(imgs[index], (j * 300, i * 300))
            
            # Label box
            draw.rectangle([j*300, i*300 + 265, j*300 + 300, i*300 + 300], fill=(0, 0, 0))
            draw.text((j*300 + 10, i*300 + 275), names_list[index][:30], fill="white", font=font)
            
    img_byte_arr = io.BytesIO()
    collage.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr