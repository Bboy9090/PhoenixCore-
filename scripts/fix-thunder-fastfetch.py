import os
import glob
from PIL import Image, ImageDraw, ImageFont
import numpy as np

base_dl = "/Users/bj90-m1/Downloads/Phoenix-Repaired"
artifact_dir = "/Users/bj90-m1/.gemini/antigravity-ide/brain/3b8eb183-5722-447f-a820-2fe3ea8fc321"

def get_latest_generated(prefix):
    files = glob.glob(os.path.join(artifact_dir, f"{prefix}*.png"))
    if not files: return None
    return max(files, key=os.path.getmtime)

def remove_black_background(img_path, out_path, target_size):
    img = Image.open(img_path).convert("RGBA")
    if target_size:
        img = img.resize(target_size, Image.Resampling.LANCZOS)
        
    data = np.array(img).astype(float)
    r, g, b = data[:,:,0], data[:,:,1], data[:,:,2]
    
    alpha = np.maximum.reduce([r, g, b])
    alpha_safe = np.where(alpha == 0, 1, alpha)
    
    r = np.clip(r * 255.0 / alpha_safe, 0, 255)
    g = np.clip(g * 255.0 / alpha_safe, 0, 255)
    b = np.clip(b * 255.0 / alpha_safe, 0, 255)
    
    alpha = np.clip(alpha * 1.5, 0, 255)
    
    data[:,:,0] = r
    data[:,:,1] = g
    data[:,:,2] = b
    data[:,:,3] = alpha
    
    Image.fromarray(np.uint8(data)).save(out_path)

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
    
    try: font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 12)
    except: font = ImageFont.load_default()

    for c, img_path in enumerate(images):
        if not os.path.exists(img_path): continue
        img = Image.open(img_path).convert("RGBA")
        img.thumbnail((cell_size-20, cell_size-20))
        ox = c * cell_size + (cell_size - img.width) // 2
        
        for r in range(rows):
            oy = r * cell_size + (cell_size - img.height) // 2 - 10
            proof.paste(img, (ox, oy), img)
            label = "Black BG" if r==0 else ("White BG" if r==1 else ("Magenta BG" if r==2 else "Checker BG"))
            fname = os.path.basename(img_path)[:20]
            draw.text((c*cell_size + 5, (r+1)*cell_size - 15), f"{fname} ({label})", fill=(0,255,0), font=font)
            
    proof.save(out_path)

def main():
    print("Fixing Thundergod Fastfetch...")
    tg_dir = os.path.join(base_dl, "thundergod", "branding")
    
    clean_src = get_latest_generated("thundergod_fastfetch_clean")
    out_path = os.path.join(tg_dir, "thundergod-fastfetch-terminal-image-512x512-transparent.png")
    
    remove_black_background(clean_src, out_path, (512, 512))
    
    print("Updating proof sheet...")
    generate_multi_bg_proof(
        [os.path.join(tg_dir, "thundergod-kickoff-start-menu-icon-256x256-transparent.png"),
         out_path,
         os.path.join(tg_dir, "thundergod-about-this-system-logo-512x512-transparent.png")],
        "/Users/bj90-m1/Downloads/thundergod-core-branding-repaired-proof.png"
    )
    
    # re-zip
    os.system(f"cd /Users/bj90-m1/Downloads/Phoenix-Repaired && zip -q -r HomeAurelia-thundergod-FailOnly-Repaired.zip thundergod")
    
    print("Done!")

if __name__ == "__main__":
    main()
