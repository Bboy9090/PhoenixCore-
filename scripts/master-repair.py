import os
import glob
from PIL import Image, ImageDraw, ImageFont, ImageOps
import numpy as np
import shutil

editions = ['aurelia', 'arcwyre', 'thundergod', 'native']
base_dl = "/Users/bj90-m1/Downloads"
repaired_dir = os.path.join(base_dl, "Phoenix-Repaired")
artifact_dir = "/Users/bj90-m1/.gemini/antigravity-ide/brain/3b8eb183-5722-447f-a820-2fe3ea8fc321"

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

ensure_dir(repaired_dir)

def get_source_files(edition):
    files = {}
    for root, dirs, filenames in os.walk(base_dl):
        if edition.lower() not in root.lower() or "repaired" in root.lower():
            continue
        for fname in filenames:
            if not fname.endswith(".png"): continue
            if "raw-crop" in fname: continue
            fpath = os.path.join(root, fname)
            fname_lower = fname.lower()
            
            if "ksplash" in fname_lower: files['ksplash'] = fpath
            elif "avatar" in fname_lower: files['avatar'] = fpath
            elif "calamares-01" in fname_lower: files['calamares-01'] = fpath
            elif "calamares-02" in fname_lower: files['calamares-02'] = fpath
            elif "calamares-03" in fname_lower: files['calamares-03'] = fpath
            elif "calamares-04" in fname_lower: files['calamares-04'] = fpath
            elif "kickoff" in fname_lower: files['kickoff'] = fpath
            elif "fastfetch" in fname_lower: files['fastfetch'] = fpath
            elif "about" in fname_lower: files['about'] = fpath
            elif "icons" in root.lower() and "512x512" in root.lower():
                if 'icons' not in files: files['icons'] = []
                if fpath not in files['icons']:
                    files['icons'].append(fpath)
    return files

def resize_cover(img_path, out_path, target_size):
    try:
        img = Image.open(img_path).convert("RGBA")
        # ImageOps.fit does center-crop and resize without stretching
        img_fit = ImageOps.fit(img, target_size, method=Image.Resampling.LANCZOS)
        img_fit.save(out_path)
        return True
    except Exception as e:
        print(f"Error resizing {img_path}: {e}")
        return False

def remove_black_background(img_path, out_path, target_size):
    try:
        img = Image.open(img_path).convert("RGBA")
        if target_size:
            img = img.resize(target_size, Image.Resampling.LANCZOS)
            
        data = np.array(img).astype(float)
        r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
        
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
    except Exception as e:
        print(f"Error removing black bg for {img_path}: {e}")

def remove_fake_checkerboard(img_path, out_path_512, out_path_256=None):
    try:
        img = Image.open(img_path).convert("RGBA")
        img = img.resize((512, 512), Image.Resampling.LANCZOS)
        data = np.array(img)
        
        r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
        rgb_max = np.maximum.reduce([r, g, b])
        rgb_min = np.minimum.reduce([r, g, b])
        saturation = rgb_max - rgb_min
        
        y, x = np.ogrid[:512, :512]
        dist_from_center = np.sqrt((x - 256)**2 + (y - 256)**2)
        
        checkerboard_mask = (saturation < 15) & (rgb_max > 40) & (dist_from_center > 100)
        corner_mask = (dist_from_center > 240)
        
        data[:,:,3][checkerboard_mask | corner_mask] = 0
        
        clean_img = Image.fromarray(data)
        clean_img.save(out_path_512)
        if out_path_256:
            clean_img.resize((256, 256), Image.Resampling.LANCZOS).save(out_path_256)
    except Exception as e:
        print(f"Error removing checkerboard for {img_path}: {e}")

def get_latest_generated(prefix):
    files = glob.glob(os.path.join(artifact_dir, f"{prefix}*.png"))
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def generate_multi_bg_proof(edition, out_path):
    # Load sample assets for this edition
    ed_dir = os.path.join(repaired_dir, edition)
    assets = [
        os.path.join(ed_dir, "branding", f"{edition}-kickoff-start-menu-icon-256x256-transparent.png"),
        os.path.join(ed_dir, "branding", f"{edition}-fastfetch-terminal-image-512x512-transparent.png"),
        os.path.join(ed_dir, "branding", f"{edition}-about-this-system-logo-512x512-transparent.png"),
    ]
    # Add 3 random icons
    icons = glob.glob(os.path.join(ed_dir, "icons", "512x512", "*.png"))
    assets.extend(icons[:3])
    
    # 4 backgrounds: Black, White, Magenta, Checkerboard
    cols = len(assets)
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

    for c, img_path in enumerate(assets):
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

def generate_comparison_proof():
    # Show kickoff and fastfetch for all 4 editions
    cols = 4
    rows = 2
    cell_size = 300
    proof = Image.new("RGB", (cols * cell_size, rows * cell_size), color=(30, 30, 30))
    draw = ImageDraw.Draw(proof)
    try: font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    except: font = ImageFont.load_default()
    
    for c, edition in enumerate(editions):
        ed_dir = os.path.join(repaired_dir, edition, "branding")
        kickoff = os.path.join(ed_dir, f"{edition}-kickoff-start-menu-icon-256x256-transparent.png")
        fastfetch = os.path.join(ed_dir, f"{edition}-fastfetch-terminal-image-512x512-transparent.png")
        
        for r, img_path in enumerate([kickoff, fastfetch]):
            if os.path.exists(img_path):
                img = Image.open(img_path).convert("RGBA")
                img.thumbnail((cell_size-40, cell_size-40))
                ox = c * cell_size + (cell_size - img.width) // 2
                oy = r * cell_size + (cell_size - img.height) // 2 - 20
                
                # Draw checkerboard background for the icon
                for cy in range(0, img.height, 20):
                    for cx in range(0, img.width, 20):
                        color = (150, 150, 150) if (cx//20 + cy//20) % 2 == 0 else (100, 100, 100)
                        bx, by = ox + cx, oy + cy
                        ex, ey = min(bx+20, ox+img.width), min(by+20, oy+img.height)
                        draw.rectangle([bx, by, ex, ey], fill=color)
                
                proof.paste(img, (ox, oy), img)
                draw.text((c*cell_size + 10, (r+1)*cell_size - 25), f"{edition.upper()} - {os.path.basename(img_path)[:10]}", fill=(255,255,255), font=font)
    
    proof.save(os.path.join(base_dl, "all-editions-repaired-comparison.png"))

def main():
    print("Starting Master Asset Repair Pipeline...")
    summary = ["HOME AURELIA REPAIR SUMMARY", "==========================="]
    
    for edition in editions:
        print(f"Processing {edition.upper()}...")
        src_files = get_source_files(edition)
        ed_dir = os.path.join(repaired_dir, edition)
        
        bg_dir = os.path.join(ed_dir, "backgrounds")
        brand_dir = os.path.join(ed_dir, "branding")
        icon_512 = os.path.join(ed_dir, "icons", "512x512")
        icon_256 = os.path.join(ed_dir, "icons", "256x256")
        
        ensure_dir(bg_dir)
        ensure_dir(brand_dir)
        ensure_dir(icon_512)
        ensure_dir(icon_256)
        
        # 1. Resize Backgrounds to EXACTLY 1920x1080
        for key in ['ksplash', 'calamares-01', 'calamares-02', 'calamares-03', 'calamares-04']:
            if key in src_files:
                out_name = os.path.basename(src_files[key])
                resize_cover(src_files[key], os.path.join(bg_dir, out_name), (1920, 1080))
                
        if 'avatar' in src_files:
            out_name = os.path.basename(src_files['avatar'])
            resize_cover(src_files['avatar'], os.path.join(bg_dir, out_name), (512, 512))
            
        # 2. Branding Icons (Rebuild Native & Arcwyre from AI gens, clean others)
        if edition == 'native':
            remove_black_background(get_latest_generated("native_kickoff"), os.path.join(brand_dir, "native-kickoff-start-menu-icon-256x256-transparent.png"), (256,256))
            remove_black_background(get_latest_generated("native_fastfetch"), os.path.join(brand_dir, "native-fastfetch-terminal-image-512x512-transparent.png"), (512,512))
            remove_black_background(get_latest_generated("native_about"), os.path.join(brand_dir, "native-about-this-system-logo-512x512-transparent.png"), (512,512))
        elif edition == 'arcwyre':
            remove_black_background(get_latest_generated("arcwyre_kickoff"), os.path.join(brand_dir, "arcwyre-kickoff-start-menu-icon-256x256-transparent.png"), (256,256))
            remove_black_background(get_latest_generated("arcwyre_fastfetch"), os.path.join(brand_dir, "arcwyre-fastfetch-terminal-image-512x512-transparent.png"), (512,512))
            remove_black_background(get_latest_generated("arcwyre_about"), os.path.join(brand_dir, "arcwyre-about-this-system-logo-512x512-transparent.png"), (512,512))
        else:
            # Aurelia & Thundergod passed size/alpha, just strip any potential checkerboard
            for key in ['kickoff', 'fastfetch', 'about']:
                if key in src_files:
                    size = 256 if 'kickoff' in key else 512
                    remove_fake_checkerboard(src_files[key], os.path.join(brand_dir, os.path.basename(src_files[key])))
                    
        # 3. Clean App/System Icons
        if 'icons' in src_files:
            for icon_path in src_files['icons']:
                fname = os.path.basename(icon_path)
                remove_fake_checkerboard(icon_path, os.path.join(icon_512, fname), os.path.join(icon_256, fname.replace("512x512", "256x256")))
                
        # 4. Generate Edition Proof
        generate_multi_bg_proof(edition, os.path.join(base_dl, f"{edition}-repaired-proof.png"))
        summary.append(f"[{edition.upper()}] Repaired backgrounds (1920x1080), generated true-alpha branding, stripped app icon checkerboards.")

    # 5. Generate Comparison Proof
    generate_comparison_proof()
    
    with open(os.path.join(base_dl, "HomeAurelia-Repair-Summary.txt"), "w") as f:
        f.write("\n".join(summary))
        
    print("Repair pipeline complete!")

if __name__ == "__main__":
    main()
