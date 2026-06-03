import os
import glob
from PIL import Image, ImageDraw, ImageFont

repo_editions = "/Users/bj90-m1/PhoenixCore-/editions"
artifact_dir = "/Users/bj90-m1/.gemini/antigravity-ide/brain/3b8eb183-5722-447f-a820-2fe3ea8fc321"

edition_map = {
    "Aurelia": "home",
    "Arcwyre": "arcwyre",
    "Thundergod": "thunder-god",
    "Native": "blue-phoenix"
}

def generate_master_proof(edition_name, folder_name):
    art_dir = os.path.join(repo_editions, folder_name, "custom_art")
    icon_dir = os.path.join(repo_editions, folder_name, "custom_icons")
    out_path = os.path.join(artifact_dir, f"{edition_name}-Master-Integration-Proof.jpg")
    
    # 1. Collect Backgrounds
    backgrounds = []
    for bg_name in ["ksplash_bg.png", "calamares_1.png", "calamares_2.png", "calamares_3.png", "calamares_4.png"]:
        p = os.path.join(art_dir, bg_name)
        if os.path.exists(p): backgrounds.append(p)
        
    # 2. Collect Branding
    branding = []
    for br_name in ["start_menu.png", "fastfetch_logo.png", "about_logo.png"]:
        p = os.path.join(art_dir, br_name)
        if os.path.exists(p): branding.append(p)
        
    # 3. Collect Icons (pick first 8)
    icons = []
    all_icons = glob.glob(os.path.join(icon_dir, "*.png"))
    all_icons.sort()
    for ic in all_icons[:8]:
        icons.append(ic)
        
    if not backgrounds and not branding and not icons:
        return
        
    # Layout:
    # Row 1: 3 Backgrounds (thumb_w=480, thumb_h=270)
    # Row 2: 2 Backgrounds (thumb_w=480, thumb_h=270)
    # Row 3: 3 Branding (thumb=256x256)
    # Row 4: 8 Icons (thumb=128x128)
    
    canvas_w = 480 * 3
    canvas_h = 270 * 2 + 300 + 150
    
    proof = Image.new("RGB", (canvas_w, canvas_h), color=(30, 30, 30))
    draw = ImageDraw.Draw(proof)
    try: font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    except: font = ImageFont.load_default()
    
    # Draw Backgrounds
    for i, p in enumerate(backgrounds):
        img = Image.open(p).convert("RGB")
        img.thumbnail((460, 250))
        r = i // 3
        c = i % 3
        ox = c * 480 + (480 - img.width) // 2
        oy = r * 270 + (270 - img.height) // 2 - 10
        proof.paste(img, (ox, oy))
        draw.text((c * 480 + 10, (r+1) * 270 - 25), os.path.basename(p), fill=(255, 255, 255), font=font)
        
    # Draw Branding
    y_offset = 270 * 2
    for i, p in enumerate(branding):
        img = Image.open(p).convert("RGBA")
        img.thumbnail((256, 256))
        
        ox = i * 480 + (480 - img.width) // 2
        oy = y_offset + (300 - img.height) // 2 - 10
        
        # Checkerboard bg for transparency check
        for cy in range(0, img.height, 16):
            for cx in range(0, img.width, 16):
                color = (150,150,150) if (cx//16 + cy//16) % 2 == 0 else (100,100,100)
                bx, by = ox + cx, oy + cy
                ex, ey = min(bx+16, ox+img.width), min(by+16, oy+img.height)
                draw.rectangle([bx, by, ex, ey], fill=color)
                
        proof.paste(img, (ox, oy), img)
        draw.text((i * 480 + 10, y_offset + 300 - 25), os.path.basename(p), fill=(255, 255, 255), font=font)
        
    # Draw Icons
    y_offset += 300
    icon_w = canvas_w // 8
    for i, p in enumerate(icons):
        img = Image.open(p).convert("RGBA")
        img.thumbnail((icon_w-20, icon_w-20))
        
        ox = i * icon_w + (icon_w - img.width) // 2
        oy = y_offset + (150 - img.height) // 2 - 20
        
        proof.paste(img, (ox, oy), img)
        label = os.path.basename(p)[:12]
        draw.text((i * icon_w + 5, y_offset + 150 - 25), label, fill=(255, 255, 255), font=font)
        
    proof.save(out_path, quality=90)
    print(f"Generated master proof for {edition_name}")

def main():
    for ed_name, folder in edition_map.items():
        generate_master_proof(ed_name, folder)

if __name__ == "__main__":
    main()
