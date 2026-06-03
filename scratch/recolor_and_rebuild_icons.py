import os
import colorsys
import shutil
import zipfile
from PIL import Image

def recolor_pixel(r, g, b, a, edition):
    if a < 10:
        return (r, g, b, a)
        
    # Convert RGB to HSV
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    
    # Identify blue/cyan pixels (Hue roughly between 160 and 260 degrees)
    is_blue = (0.45 <= h <= 0.72)
    
    if edition == "Arcwyre":
        # Shift blue highlights to Crimson Red (Hue around 0.98 -> 350 degrees)
        if is_blue:
            h = 0.98
            s = min(1.0, s * 1.2) # Enhance saturation
        return tuple(int(c * 255) for c in colorsys.hsv_to_rgb(h, s, v)) + (a,)
        
    elif edition == "Thundergod":
        # Shift blue to silver-white (Desaturate and increase brightness)
        if is_blue:
            s = max(0.0, s * 0.1) # Desaturate heavily
            v = min(1.0, v * 1.3) # Increase brightness
        return tuple(int(c * 255) for c in colorsys.hsv_to_rgb(h, s, v)) + (a,)
        
    elif edition == "Native":
        # Create dual red-blue highlights: shift half of the blue pixels to crimson red
        if is_blue:
            # Shift cyan/light-blue to crimson red, keep deep royal blue
            if h < 0.58:
                h = 0.98
                s = min(1.0, s * 1.1)
        return tuple(int(c * 255) for c in colorsys.hsv_to_rgb(h, s, v)) + (a,)
        
    return (r, g, b, a)

def recolor_image(src_path, dest_path, edition):
    img = Image.open(src_path).convert("RGBA")
    pixels = img.load()
    w, h = img.size
    
    for x in range(w):
        for y in range(h):
            r, g, b, a = pixels[x, y]
            pixels[x, y] = recolor_pixel(r, g, b, a, edition)
            
    img.save(dest_path, "PNG")

def rebuild():
    root = "/Users/bj90-m1/PhoenixCore-/HomeAurelia-Full-Pack-YES-GO-SOURCE"
    editions = ["Arcwyre", "Thundergod", "Native"]
    
    aurelia_icons_dir = os.path.join(root, "Editions/Aurelia/Icons/HomeAurelia-Aurelia-Icons")
    sizes = ["16x16", "22x22", "24x24", "32x32", "48x48", "64x64", "128x128", "256x256", "512x512"]
    categories = ["places", "apps", "actions", "devices", "status", "mimetypes", "categories"]
    
    for ed in editions:
        print(f"\n🎨 Recoloring hand-cropped PNGs for {ed}...")
        dest_icons_dir = os.path.join(root, f"Editions/{ed}/Icons/HomeAurelia-{ed}-Icons")
        
        if os.path.exists(dest_icons_dir):
            shutil.rmtree(dest_icons_dir)
        os.makedirs(dest_icons_dir, exist_ok=True)
        
        # 1. Recolor and distribute PNG files recursively
        for sz in sizes:
            for cat in categories:
                src_sz_dir = os.path.join(aurelia_icons_dir, sz, cat)
                if not os.path.exists(src_sz_dir):
                    continue
                    
                dest_sz_dir = os.path.join(dest_icons_dir, sz, cat)
                os.makedirs(dest_sz_dir, exist_ok=True)
                
                for f in os.listdir(src_sz_dir):
                    if f.endswith(".png"):
                        src_png = os.path.join(src_sz_dir, f)
                        dest_png = os.path.join(dest_sz_dir, f)
                        
                        # Recolor using HSL shift
                        recolor_image(src_png, dest_png, ed)
                        
        # 2. Sync scalable SVGs wrappers
        dest_scalable = os.path.join(dest_icons_dir, "scalable")
        os.makedirs(dest_scalable, exist_ok=True)
        for cat in categories:
            src_scal_dir = os.path.join(aurelia_icons_dir, "scalable", cat)
            if os.path.exists(src_scal_dir):
                dest_scal_dir = os.path.join(dest_scalable, cat)
                os.makedirs(dest_scal_dir, exist_ok=True)
                for f in os.listdir(src_scal_dir):
                    if f.endswith(".svg"):
                        shutil.copy2(os.path.join(src_scal_dir, f), os.path.join(dest_scal_dir, f))
                        
        # 3. Copy index.theme and reports
        shutil.copy2(os.path.join(aurelia_icons_dir, "README.md"), dest_icons_dir)
        shutil.copy2(os.path.join(aurelia_icons_dir, "missing-file-report.txt"), dest_icons_dir)
        
        # Update visual audit report
        audit_text = f"""HomeAurelia {ed} icon set
Identity: {ed} hand-cropped pixel recolorway
SVG audit rule: no <image> tags, no data:image base64 wrappers.
"""
        with open(os.path.join(dest_icons_dir, "visual-audit-report.txt"), "w") as f:
            f.write(audit_text)
            
        # Update index.theme name
        with open(os.path.join(aurelia_icons_dir, "index.theme"), "r") as f:
            theme_content = f.read()
        theme_content = theme_content.replace("Home Aurelia Icons (Aurelia)", f"Home Aurelia Icons ({ed})")
        with open(os.path.join(dest_icons_dir, "index.theme"), "w") as f:
            f.write(theme_content)
            
        # 4. Compile ZIP releases
        print(f"   📦 Compressing release archives for {ed}...")
        icon_zip_dest = os.path.join(root, f"HomeAurelia-{ed}-Icons.zip")
        edition_zip_dest = os.path.join(root, f"HomeAurelia-{ed}-Edition.zip")
        
        # Zip Icons
        if os.path.exists(icon_zip_dest):
            os.remove(icon_zip_dest)
        with zipfile.ZipFile(icon_zip_dest, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root_dir, _, files in os.walk(dest_icons_dir):
                for file in files:
                    filepath = os.path.join(root_dir, file)
                    rel_p = os.path.relpath(filepath, dest_icons_dir)
                    zipf.write(filepath, os.path.join(f"HomeAurelia-{ed}-Icons", rel_p))
                    
        # Update ZIP folder in Edition's directory
        shutil.copy2(icon_zip_dest, os.path.join(root, f"Editions/{ed}/Icons"))
        
        # Re-pack Edition Zip (which contains Icons, Splash-Screens, Plymouth, Wallpapers, etc.)
        if os.path.exists(edition_zip_dest):
            os.remove(edition_zip_dest)
        edition_src_dir = os.path.join(root, f"Editions/{ed}")
        with zipfile.ZipFile(edition_zip_dest, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root_dir, _, files in os.walk(edition_src_dir):
                for file in files:
                    filepath = os.path.join(root_dir, file)
                    rel_p = os.path.relpath(filepath, edition_src_dir)
                    zipf.write(filepath, os.path.join(f"HomeAurelia-{ed}-Edition", rel_p))
                    
        # Update ZIP folder in Edition's directory
        shutil.copy2(edition_zip_dest, os.path.join(root, f"Editions/{ed}/ZIP"))
        
    print("\n✨ SUCCESS: All 3 editions successfully recolored from your approved hand-cropped PNGs!")

if __name__ == "__main__":
    rebuild()
