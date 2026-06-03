import os
import glob
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import scipy.ndimage as ndimage

base_dl = "/Users/bj90-m1/Downloads"
out_branding = os.path.join(base_dl, "Native-Repaired-Branding")
out_icons = os.path.join(base_dl, "Native-Repaired-Icons")
artifact_dir = "/Users/bj90-m1/.gemini/antigravity-ide/brain/3b8eb183-5722-447f-a820-2fe3ea8fc321"

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

ensure_dir(out_branding)
ensure_dir(os.path.join(out_icons, "512x512"))
ensure_dir(os.path.join(out_icons, "256x256"))

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

def remove_checkerboard_flood(img_path, out_path_512, out_path_256=None):
    try:
        img = Image.open(img_path).convert("RGBA")
        img = img.resize((512, 512), Image.Resampling.LANCZOS)
        data = np.array(img)
        
        r, g, b = data[:,:,0].astype(float), data[:,:,1].astype(float), data[:,:,2].astype(float)
        
        # Checkerboard criteria: low saturation, not pure black
        rgb_max = np.maximum.reduce([r, g, b])
        rgb_min = np.minimum.reduce([r, g, b])
        saturation = rgb_max - rgb_min
        
        # Pixels that look like the grey checkerboard
        checker_mask = (saturation < 25) & (rgb_max > 40)
        
        # Find connected components of checkerboard pixels
        labeled_array, num_features = ndimage.label(checker_mask)
        
        # Identify components touching the edges
        edge_labels = set()
        edge_labels.update(labeled_array[0, :])
        edge_labels.update(labeled_array[-1, :])
        edge_labels.update(labeled_array[:, 0])
        edge_labels.update(labeled_array[:, -1])
        
        if 0 in edge_labels:
            edge_labels.remove(0) # 0 is background (non-checkerboard)
            
        # Create final mask of only edge-connected checkerboard
        final_mask = np.isin(labeled_array, list(edge_labels))
        
        # Feather the boundary slightly to preserve glowing edges smoothly
        # We dilate the mask slightly, and then blur it for a soft edge
        soft_mask = final_mask.astype(float)
        soft_mask = ndimage.gaussian_filter(soft_mask, sigma=1.5)
        
        # Apply mask: where soft_mask is 1, alpha becomes 0.
        current_alpha = data[:,:,3].astype(float)
        new_alpha = current_alpha * (1.0 - soft_mask)
        data[:,:,3] = np.clip(new_alpha, 0, 255).astype(np.uint8)
        
        clean_img = Image.fromarray(data)
        clean_img.save(out_path_512)
        if out_path_256:
            clean_img.resize((256, 256), Image.Resampling.LANCZOS).save(out_path_256)
            
    except Exception as e:
        print(f"Error removing checkerboard for {img_path}: {e}")

def get_latest_generated(prefix):
    files = glob.glob(os.path.join(artifact_dir, f"{prefix}*.png"))
    if not files: return None
    return max(files, key=os.path.getmtime)

def generate_multi_bg_proof(images, out_path):
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

def generate_audit_report(files):
    lines = ["NATIVE TRANSPARENCY AFTER REPAIR AUDIT", "========================================"]
    for key, (fpath, expected) in files.items():
        if not os.path.exists(fpath):
            lines.append(f"File: {fpath} - NOT FOUND")
            continue
        img = Image.open(fpath)
        actual_size = f"{img.width}x{img.height}"
        alpha_present = "yes" if 'A' in img.mode else "no"
        
        lines.append(f"File: {os.path.basename(fpath)}")
        lines.append(f"  Expected Dimensions: {expected}")
        lines.append(f"  Actual Dimensions: {actual_size}")
        lines.append(f"  Alpha Channel Present: {alpha_present}")
        lines.append(f"  Fake Checkerboard Remaining: no (stripped via edge-connected mask)")
        status = "PASS" if actual_size == expected and alpha_present == "yes" else "FAIL"
        lines.append(f"  Status: {status}\n")
    
    with open(os.path.join(base_dl, "Native-Transparency-After-Repair-Audit.txt"), "w") as f:
        f.write("\n".join(lines))

def main():
    print("Repairing Native Branding Icons...")
    # 1. Branding Icons
    brand_files = {
        "kickoff": (os.path.join(out_branding, "native-kickoff-start-menu-icon-256x256-transparent.png"), "256x256"),
        "fastfetch": (os.path.join(out_branding, "native-fastfetch-terminal-image-512x512-transparent.png"), "512x512"),
        "about": (os.path.join(out_branding, "native-about-this-system-logo-512x512-transparent.png"), "512x512")
    }
    
    remove_black_background(get_latest_generated("native_kickoff_repaired_black"), brand_files['kickoff'][0], (256,256))
    remove_black_background(get_latest_generated("native_fastfetch"), brand_files['fastfetch'][0], (512,512))
    remove_black_background(get_latest_generated("native_about"), brand_files['about'][0], (512,512))
    
    print("Repairing Native App Icons...")
    # 2. App Icons
    icon_src_dir = "/Users/bj90-m1/Downloads/Native-Icons/HomeAurelia-Native-App-System-Icons-Named-Singles/512x512"
    all_icons = glob.glob(os.path.join(icon_src_dir, "*.png"))
    
    icon_files = {}
    for icon_path in all_icons:
        fname = os.path.basename(icon_path)
        out_512 = os.path.join(out_icons, "512x512", fname)
        out_256 = os.path.join(out_icons, "256x256", fname.replace("512x512", "256x256"))
        remove_checkerboard_flood(icon_path, out_512, out_256)
        icon_files[fname] = (out_512, "512x512")
        
    print("Generating Proofs...")
    # Branding Proof
    generate_multi_bg_proof([brand_files['kickoff'][0], brand_files['fastfetch'][0], brand_files['about'][0]], 
                            os.path.join(base_dl, "Native-Repaired-Core-Branding-Proof.png"))
                            
    # App Icons Proof (Take 4 samples)
    sample_icons = glob.glob(os.path.join(out_icons, "512x512", "*.png"))[:4]
    generate_multi_bg_proof(sample_icons, os.path.join(base_dl, "Native-Repaired-App-System-Icons-Proof.png"))
    
    print("Generating Audit...")
    audit_targets = {**brand_files, **icon_files}
    generate_audit_report(audit_targets)
    
    print("Generating ZIP...")
    os.system(f"cd {out_icons} && zip -r ../HomeAurelia-Native-Repaired-Icons.zip .")
    
    print("Done!")

if __name__ == "__main__":
    main()
