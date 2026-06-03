import os
from PIL import Image, ImageDraw

def render_plymouth_graphics():
    plymouth_dir = "/Users/bj90-m1/PhoenixCore-/HomeAurelia-Theme-Pack/04-Plymouth/home-aurelia"
    
    # 1. Render progress-box.png (Golden border outline, dark translucent fill)
    box_w, box_h = 400, 24
    box_img = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(box_img)
    
    # Draw rounded rectangle border
    # Fill: Deep Obsidian/Navy semi-transparent
    # Outline: Royal Gold (#D4AF37 -> 212, 175, 55)
    draw.rounded_rectangle(
        [(0, 0), (box_w - 1, box_h - 1)],
        radius=6,
        fill=(8, 15, 22, 180),
        outline=(212, 175, 55, 255),
        width=2
    )
    
    box_dest = os.path.join(plymouth_dir, "progress-box.png")
    box_img.save(box_dest, "PNG")
    print(f"✅ Rendered premium progress-box.png: {box_dest}")
    
    # 2. Render progress-bar.png (Glowing blue gradient fill)
    bar_w, bar_h = 394, 18
    bar_img = Image.new("RGBA", (bar_w, bar_h), (0, 0, 0, 0))
    
    # Create horizontal blue gradient (Electric Blue to Aurelia Blue)
    # Electric Blue: (0, 195, 255), Aurelia Blue: (28, 107, 255)
    for x in range(bar_w):
        alpha = x / (bar_w - 1)
        r = int(0 * (1 - alpha) + 28 * alpha)
        g = int(195 * (1 - alpha) + 107 * alpha)
        b = int(255 * (1 - alpha) + 255 * alpha)
        
        for y in range(bar_h):
            bar_img.putpixel((x, y), (r, g, b, 255))
            
    # Apply rounded corners to the bar using a mask
    mask = Image.new("L", (bar_w, bar_h), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([(0, 0), (bar_w - 1, bar_h - 1)], radius=4, fill=255)
    
    final_bar = Image.new("RGBA", (bar_w, bar_h), (0, 0, 0, 0))
    final_bar.paste(bar_img, (0, 0), mask=mask)
    
    bar_dest = os.path.join(plymouth_dir, "progress-bar.png")
    final_bar.save(bar_dest, "PNG")
    print(f"✅ Rendered premium progress-bar.png: {bar_dest}")
    
    # 3. Sync these assets to chroot environments
    chroot_dest = "/Users/bj90-m1/PhoenixCore-/os/phoenix-os/live-build/config/includes.chroot/usr/share/home-aurelia-theme-pack/04-Plymouth/home-aurelia"
    os.makedirs(chroot_dest, exist_ok=True)
    shutil.copy2(box_dest, chroot_dest)
    shutil.copy2(bar_dest, chroot_dest)
    print(f"✅ Synced assets to live-build chroot.")

if __name__ == "__main__":
    import shutil
    render_plymouth_graphics()
