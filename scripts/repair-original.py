import os
import glob
from PIL import Image, ImageDraw, ImageOps
import numpy as np
import colorsys

base_dl = "/Users/bj90-m1/Downloads/Phoenix-Repaired"

def fix_thundergod_fastfetch():
    src_path = "/Users/bj90-m1/Downloads/Core-Branding-thunder-god/HomeAurelia-Thundergod-Core-Branding-Icons/thundergod-fastfetch-terminal-image-512x512-transparent.png"
    out_path = os.path.join(base_dl, "thundergod", "branding", "thundergod-fastfetch-terminal-image-512x512-transparent.png")
    
    if not os.path.exists(src_path):
        print("Source not found")
        return
        
    img = Image.open(src_path).convert("RGBA")
    
    # Text is usually at bottom, let's blank out the bottom 120 pixels and top 120
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, 512, 100], fill=(0,0,0,0))
    draw.rectangle([0, 400, 512, 512], fill=(0,0,0,0))
    
    img.save(out_path)
    print("Fixed Thundergod Fastfetch!")

def hue_shift(image, hue_offset):
    img_hsv = image.convert('HSV')
    np_hsv = np.array(img_hsv)
    
    # hue is 0-255 in Pillow
    h = np_hsv[:, :, 0].astype(int)
    h = (h + hue_offset) % 256
    np_hsv[:, :, 0] = h.astype(np.uint8)
    
    shifted = Image.fromarray(np_hsv, 'HSV').convert('RGBA')
    # Copy original alpha
    shifted.putalpha(image.split()[3])
    return shifted

def rebuild_native_from_twins():
    # Take Aurelia icons (which are clean violet) and hue-shift to Native (blue/red)
    aurelia_icons_dir = os.path.join(base_dl, "aurelia", "icons", "512x512")
    native_out_dir_512 = os.path.join(base_dl, "native", "icons", "512x512")
    native_out_dir_256 = os.path.join(base_dl, "native", "icons", "256x256")
    
    if not os.path.exists(native_out_dir_512): os.makedirs(native_out_dir_512)
    if not os.path.exists(native_out_dir_256): os.makedirs(native_out_dir_256)
    
    # Aurelia is Violet (~200 degrees hue). Native is Blue/Red.
    # Actually, Native has a majority Blue look. 
    # Let's shift Aurelia by about 60 degrees (in 0-255 space, +40) to get Blue.
    
    for icon_path in glob.glob(os.path.join(aurelia_icons_dir, "*.png")):
        fname = os.path.basename(icon_path).replace("aurelia-", "native-")
        img = Image.open(icon_path).convert("RGBA")
        
        # Hue shift towards blue
        shifted = hue_shift(img, -20) # test value
        
        shifted.save(os.path.join(native_out_dir_512, fname))
        shifted.resize((256, 256), Image.Resampling.LANCZOS).save(os.path.join(native_out_dir_256, fname.replace("512x512", "256x256")))
        
    print("Rebuilt Native icons from Aurelia twins!")

def generate_multi_bg_proof(images, out_path):
    if not images: return
    cols = len(images)
    rows = 4
    cell_size = 256
    
    proof = Image.new("RGB", (cols * cell_size, rows * cell_size))
    draw = ImageDraw.Draw(proof)
    
    for r in range(rows):
        for c in range(cols):
            x = c * cell_size
            y = r * cell_size
            if r == 0: draw.rectangle([x, y, x+cell_size, y+cell_size], fill=(0,0,0))
            elif r == 1: draw.rectangle([x, y, x+cell_size, y+cell_size], fill=(255,255,255))
            elif r == 2: draw.rectangle([x, y, x+cell_size, y+cell_size], fill=(255,0,255))
            else:
                for cy in range(0, cell_size, 16):
                    for cx in range(0, cell_size, 16):
                        color = (200, 200, 200) if (cx//16 + cy//16) % 2 == 0 else (100, 100, 100)
                        draw.rectangle([x+cx, y+cy, x+cx+16, y+cy+16], fill=color)
    
    for c, img_path in enumerate(images):
        if not os.path.exists(img_path): continue
        img = Image.open(img_path).convert("RGBA")
        img.thumbnail((cell_size-20, cell_size-20))
        ox = c * cell_size + (cell_size - img.width) // 2
        
        for r in range(rows):
            oy = r * cell_size + (cell_size - img.height) // 2 - 10
            proof.paste(img, (ox, oy), img)
            
    proof.save(out_path)

if __name__ == "__main__":
    fix_thundergod_fastfetch()
    rebuild_native_from_twins()
    
    print("Generating proofs...")
    tg_dir = os.path.join(base_dl, "thundergod", "branding")
    generate_multi_bg_proof(
        [os.path.join(tg_dir, "thundergod-kickoff-start-menu-icon-256x256-transparent.png"),
         os.path.join(tg_dir, "thundergod-fastfetch-terminal-image-512x512-transparent.png"),
         os.path.join(tg_dir, "thundergod-about-this-system-logo-512x512-transparent.png")],
        "/Users/bj90-m1/Downloads/thundergod-core-branding-repaired-proof.png"
    )
    
    sample_native = glob.glob(os.path.join(base_dl, "native", "icons", "512x512", "*.png"))[:4]
    generate_multi_bg_proof(sample_native, "/Users/bj90-m1/Downloads/native-app-system-icons-repaired-proof.png")
    
    print("Zipping...")
    os.system(f"cd /Users/bj90-m1/Downloads/Phoenix-Repaired && zip -q -r HomeAurelia-thundergod-FailOnly-Repaired.zip thundergod")
    os.system(f"cd /Users/bj90-m1/Downloads/Phoenix-Repaired && zip -q -r HomeAurelia-native-FailOnly-Repaired.zip native")
    
    print("Done!")
