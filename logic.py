from PIL import Image

def create_3x3_collage(image_paths, output_path="collage.png"):
    # Open images and resize them to a uniform size (e.g., 300x300)
    imgs = [Image.open(i).resize((300, 300)) for i in image_paths]
    
    # Create a blank canvas (900x900 for a 3x3 grid of 300px images)
    collage = Image.new("RGB", (900, 900))

    # Paste images into the grid
    for i in range(3): # Rows
        for j in range(3): # Columns
            index = i * 3 + j
            collage.paste(imgs[index], (j * 300, i * 300))
    
    collage.save(output_path)
    return output_path