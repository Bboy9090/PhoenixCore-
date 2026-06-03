import os
import sys
import argparse
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

def create_radial_mask(size, feather_radius):
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size[0], size[1]), fill=255)
    return mask.filter(ImageFilter.GaussianBlur(feather_radius))

def generate_sequence(source_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Load source image
    try:
        src = Image.open(source_path).convert("RGBA")
    except Exception as e:
        print(f"Error loading {source_path}: {e}")
        return

    # 2. Create the deep cosmic background (heavily blurred and darkened source)
    bg_size = (3840, 2160)
    bg = src.resize(bg_size, Image.Resampling.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(150))
    bg_enhancer = ImageEnhance.Brightness(bg)
    bg = bg_enhancer.enhance(0.15) # Very dark, subtle cosmic glow

    # 3. Create the minimal center logo (crop to square, scale down, feather)
    w, h = src.size
    min_dim = min(w, h)
    left = (w - min_dim) / 2
    top = (h - min_dim) / 2
    right = (w + min_dim) / 2
    bottom = (h + min_dim) / 2
    
    bird = src.crop((left, top, right, bottom))
    logo_size = 900
    bird = bird.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
    
    # Apply radial mask for seamless blending
    mask = create_radial_mask((logo_size, logo_size), feather_radius=150)
    bird.putalpha(mask)

    # 4. Composite the bird onto the cosmic background
    base_canvas = Image.new("RGBA", bg_size, (0, 0, 0, 255))
    base_canvas.paste(bg, (0, 0))
    
    paste_x = (bg_size[0] - logo_size) // 2
    paste_y = (bg_size[1] - logo_size) // 2 - 100 # Shift slightly up for the boot progress bar
    base_canvas.paste(bird, (paste_x, paste_y), bird)
    
    base_canvas = base_canvas.convert("RGB")

    # 5. Output the 3 stages with brightness adjustments
    enhancer = ImageEnhance.Brightness(base_canvas)
    
    # Stage 1: GRUB (Dormant)
    grub_img = enhancer.enhance(0.4)
    grub_img.save(os.path.join(out_dir, "grub_splash.png"))
    print(f"Generated {out_dir}/grub_splash.png")

    # Stage 2: Plymouth (Charging)
    plymouth_img = enhancer.enhance(0.75)
    plymouth_img.save(os.path.join(out_dir, "plymouth_splash.png"))
    print(f"Generated {out_dir}/plymouth_splash.png")

    # Stage 3: SDDM (Awake)
    sddm_img = enhancer.enhance(1.0)
    sddm_img.save(os.path.join(out_dir, "sddm_splash.png"))
    print(f"Generated {out_dir}/sddm_splash.png")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate 3-stage minimal boot sequence.")
    parser.add_argument("source", help="Path to the high-res concept art.")
    parser.add_argument("out_dir", help="Output directory for the generated images.")
    args = parser.parse_args()
    
    generate_sequence(args.source, args.out_dir)
