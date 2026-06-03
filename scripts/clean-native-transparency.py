import os
import glob
from PIL import Image, ImageDraw, ImageFont
import numpy as np

base_dl = "/Users/bj90-m1/Downloads"
editions_dir = "/Users/bj90-m1/PhoenixCore-/editions/native/custom_art"
icons_dir = "/Users/bj90-m1/PhoenixCore-/editions/native/custom_icons"

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

# Ensure output dirs
out_branding = os.path.join(base_dl, "Native-Repaired-Branding")
out_icons = os.path.join(base_dl, "Native-Repaired-Icons")
ensure_dir(out_branding)
ensure_dir(out_icons)
ensure_dir(os.path.join(out_icons, "256x256"))
ensure_dir(os.path.join(out_icons, "512x512"))

def remove_black_background(img_path, out_path, target_size=None):
    """
    Removes pure solid black background by using luminance as alpha,
    perfect for neon on black.
    """
    img = Image.open(img_path).convert("RGBA")
    if target_size:
        img = img.resize(target_size, Image.Resampling.LANCZOS)
        
    data = np.array(img).astype(float)
    r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
    
    # Calculate luminance or max channel for alpha
    alpha = np.maximum.reduce([r, g, b])
    
    # Optional: Boost RGB values so they remain bright when alpha is applied
    # (Additive blending simulation)
    # Prevent division by zero
    alpha_safe = np.where(alpha == 0, 1, alpha)
    r = np.clip(r * 255.0 / alpha_safe, 0, 255)
    g = np.clip(g * 255.0 / alpha_safe, 0, 255)
    b = np.clip(b * 255.0 / alpha_safe, 0, 255)
    
    # We want a stronger alpha for neon so it doesn't look too ghosted
    alpha = np.clip(alpha * 1.5, 0, 255)

    data[:,:,0] = r
    data[:,:,1] = g
    data[:,:,2] = b
    data[:,:,3] = alpha
    
    Image.fromarray(np.uint8(data)).save(out_path)

def remove_fake_checkerboard(img_path, out_path_512, out_path_256):
    """
    Removes the grey checkerboard from the Native app icons.
    The checkerboard is usually #cccccc and #ffffff blocks.
    We detect grayscale pixels (R~=G~=B) that are not black, 
    and make them transparent, but only if they are not in the very center (to protect white neon cores).
    """
    img = Image.open(img_path).convert("RGBA")
    img = img.resize((512, 512), Image.Resampling.LANCZOS) # Ensure exactly 512x512
    data = np.array(img)
    
    r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
    
    # Calculate difference between min and max RGB to find grayscale
    rgb_max = np.maximum.reduce([r, g, b])
    rgb_min = np.minimum.reduce([r, g, b])
    saturation = rgb_max - rgb_min
    
    # Calculate distance from center
    y, x = np.ogrid[:512, :512]
    dist_from_center = np.sqrt((x - 256)**2 + (y - 256)**2)
    
    # Mask: if saturation is very low (grayscale), and it's somewhat bright (grey/white), 
    # AND it's outside a radius of ~120px (protecting the white hot center of the icon)
    checkerboard_mask = (saturation < 15) & (rgb_max > 40) & (dist_from_center > 100)
    
    # Also we should completely wipe the corners (radius > 240) to be safe since icons are rounded/circular
    corner_mask = (dist_from_center > 240)
    
    final_mask = checkerboard_mask | corner_mask
    
    data[:,:,3][final_mask] = 0
    
    clean_img = Image.fromarray(data)
    clean_img.save(out_path_512)
    clean_img.resize((256, 256), Image.Resampling.LANCZOS).save(out_path_256)

def generate_proof_sheet(images, out_path):
    # Create proof sheet with Black, White, and Checkerboard backgrounds
    cols = len(images)
    rows = 3
    cell_size = 300
    
    proof = Image.new("RGB", (cols * cell_size, rows * cell_size))
    draw = ImageDraw.Draw(proof)
    
    # Draw backgrounds
    for r in range(rows):
        for c in range(cols):
            x = c * cell_size
            y = r * cell_size
            
            if r == 0:
                # Black
                draw.rectangle([x, y, x+cell_size, y+cell_size], fill=(0,0,0))
            elif r == 1:
                # White
                draw.rectangle([x, y, x+cell_size, y+cell_size], fill=(255,255,255))
            else:
                # Checkerboard
                for cy in range(0, cell_size, 20):
                    for cx in range(0, cell_size, 20):
                        color = (200, 200, 200) if (cx//20 + cy//20) % 2 == 0 else (100, 100, 100)
                        draw.rectangle([x+cx, y+cy, x+cx+20, y+cy+20], fill=color)
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    except:
        font = ImageFont.load_default()

    # Paste images
    for c, img_path in enumerate(images):
        if not os.path.exists(img_path): continue
        img = Image.open(img_path).convert("RGBA")
        img.thumbnail((cell_size-40, cell_size-40))
        
        ox = c * cell_size + (cell_size - img.width) // 2
        
        for r in range(rows):
            oy = r * cell_size + (cell_size - img.height) // 2 - 10
            proof.paste(img, (ox, oy), img)
            
            # Label
            label = "Black BG" if r==0 else ("White BG" if r==1 else "Checker BG")
            draw.text((c*cell_size + 10, (r+1)*cell_size - 25), f"{os.path.basename(img_path)[:20]} ({label})", fill=(0,255,0), font=font)
            
    proof.save(out_path)

if __name__ == "__main__":
    print("Repairing Core Branding Icons...")
    # Get the generated artifacts
    artifact_dir = "/Users/bj90-m1/.gemini/antigravity-ide/brain/3b8eb183-5722-447f-a820-2fe3ea8fc321"
    
    kickoff_gen = max(glob.glob(os.path.join(artifact_dir, "native_kickoff_repaired_black_*.png")), key=os.path.getmtime)
    fastfetch_gen = max(glob.glob(os.path.join(artifact_dir, "native_fastfetch_repaired_*.png")), key=os.path.getmtime)
    about_gen = max(glob.glob(os.path.join(artifact_dir, "native_about_repaired_*.png")), key=os.path.getmtime)
    
    remove_black_background(kickoff_gen, os.path.join(out_branding, "native-kickoff-start-menu-icon-256x256-transparent.png"), (256, 256))
    remove_black_background(fastfetch_gen, os.path.join(out_branding, "native-fastfetch-terminal-image-512x512-transparent.png"), (512, 512))
    remove_black_background(about_gen, os.path.join(out_branding, "native-about-this-system-logo-512x512-transparent.png"), (512, 512))
    
    print("Repairing App/System Icons...")
    icon_src_dir = "/Users/bj90-m1/Downloads/Native-Icons/HomeAurelia-Native-App-System-Icons-Named-Singles/512x512"
    all_icons = glob.glob(os.path.join(icon_src_dir, "*.png"))
    for icon_path in all_icons:
        fname = os.path.basename(icon_path)
        remove_fake_checkerboard(
            icon_path, 
            os.path.join(out_icons, "512x512", fname),
            os.path.join(out_icons, "256x256", fname.replace("512x512", "256x256"))
        )
        
    print("Generating Proofs...")
    branding_proof_files = glob.glob(os.path.join(out_branding, "*.png"))
    generate_proof_sheet(branding_proof_files, os.path.join(base_dl, "Native-Repaired-Core-Branding-Proof.png"))
    
    # Pick 4 sample icons for proof
    icon_proof_files = glob.glob(os.path.join(out_icons, "512x512", "*.png"))[:4]
    generate_proof_sheet(icon_proof_files, os.path.join(base_dl, "Native-Repaired-App-System-Icons-Proof.png"))
    
    print("Generating zip...")
    os.system(f"cd {out_icons} && zip -r ../HomeAurelia-Native-Repaired-Icons.zip .")
    
    print("Done!")
