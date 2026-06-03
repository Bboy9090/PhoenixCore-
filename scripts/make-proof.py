import os
from PIL import Image, ImageDraw, ImageFont
import glob
import math

def create_proof_sheet(output_path):
    files = []
    # Collect all native images
    files.extend(glob.glob('/Users/bj90-m1/Downloads/Native-Singles/HomeAurelia-Native-Named-Singles/native-*.png'))
    files.extend(glob.glob('/Users/bj90-m1/Downloads/Core-Branding-native/HomeAurelia-Native-Core-Branding-Icons/*.png'))
    files.extend(glob.glob('/Users/bj90-m1/Downloads/Native-Icons/HomeAurelia-Native-App-System-Icons-Named-Singles/512x512/*.png'))

    # filter out raw crops
    files = [f for f in files if "raw-crop" not in f]

    # Grid config
    cols = 5
    rows = math.ceil(len(files) / cols)
    cell_w = 400
    cell_h = 450
    
    img_w = cols * cell_w
    img_h = rows * cell_h
    
    proof = Image.new('RGB', (img_w, img_h), color=(40, 40, 40))
    draw = ImageDraw.Draw(proof)
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    except:
        font = ImageFont.load_default()

    for idx, fpath in enumerate(files):
        try:
            with Image.open(fpath) as img:
                # Convert to RGBA to ensure we have alpha
                img = img.convert("RGBA")
                # Create a checkerboard background for transparency check
                bg = Image.new('RGB', (cell_w, cell_h-50), color=(100, 100, 100))
                # Resize keeping aspect ratio
                img.thumbnail((cell_w - 20, cell_h - 70))
                x_offset = (cell_w - img.width) // 2
                y_offset = (cell_h - 50 - img.height) // 2
                
                # Paste with alpha
                bg.paste(img, (x_offset, y_offset), img)
                
                # Paste onto proof
                px = (idx % cols) * cell_w
                py = (idx // cols) * cell_h
                proof.paste(bg, (px, py))
                
                # Draw filename
                fname = os.path.basename(fpath)
                draw.text((px + 10, py + cell_h - 40), fname[:45], fill=(255,255,255), font=font)
                if len(fname) > 45:
                    draw.text((px + 10, py + cell_h - 20), fname[45:], fill=(255,255,255), font=font)
        except Exception as e:
            print(f"Error on {fpath}: {e}")

    proof.save(output_path)
    print(f"Saved proof sheet to {output_path}")

create_proof_sheet('/Users/bj90-m1/Downloads/Native-Audit-ProofSheet.jpg')
