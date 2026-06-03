import os
from PIL import Image

def generate_card_wallpaper(src_path, dest_path, col_idx, width, height, bg_color):
    if not os.path.exists(src_path):
        print(f"Skipping: {src_path} (not found)")
        return
        
    print(f"Cropping vertical card {col_idx} from {os.path.basename(src_path)} and centering on {width}x{height}...")
    master_img = Image.open(src_path).convert("RGBA")
    m_w, m_h = master_img.size
    
    # Calculate column bounds (4 columns side-by-side)
    col_w = m_w // 4
    left = col_idx * col_w
    right = left + col_w
    top = 0
    bottom = m_h
    
    # Crop the exact vertical card
    card = master_img.crop((left, top, right, bottom))
    
    # Scale card to fit the target height
    scale_factor = height / card.height
    new_h = height
    new_w = int(card.width * scale_factor)
    scaled_card = card.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Create target canvas filled with deep brand color
    canvas = Image.new("RGBA", (width, height), bg_color)
    
    # Place scaled vertical card in the center
    offset_x = (width - new_w) // 2
    canvas.paste(scaled_card, (offset_x, 0), scaled_card)
    
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    canvas.convert("RGB").save(dest_path, "PNG")
    print(f"   ✅ Saved centered card wallpaper: {dest_path}")

def run_widen():
    root = "/Users/bj90-m1/PhoenixCore-/HomeAurelia-Theme-Pack"
    
    # Visual guide with the four gorgeous vertical panels
    master_board = "/Users/bj90-m1/PhoenixCore-/HomeAurelia-Full-Pack-SOURCE-TRUTH/Shared/Reference-Boards/01_APPROVED_REFERENCE_BOARDS/epic_phoenix_legacy_theme_art.png"
    
    colors = {
        "aurelia": (8, 20, 38, 255),       # Deep Navy
        "arcwyre": (5, 7, 13, 255),       # Deep Obsidian
        "thundergod": (15, 30, 58, 255),   # Storm Blue
        "native": (5, 7, 13, 255),         # Deep Obsidian
        "home_aurelia_main": (8, 20, 38, 255) # Deep Navy
    }
    
    resolutions = [
        ("4K", 3840, 2160),
        ("QHD", 2560, 1440),
        ("FHD", 1920, 1080),
        ("Ultrawide", 3440, 1440)
    ]
    
    # Map editions to their respective column indices in the master board
    # Aurelia = Col 0, Arcwyre = Col 1, Thundergod = Col 2, Native = Col 3
    editions = [
        ("aurelia", 0),
        ("arcwyre", 1),
        ("thundergod", 2),
        ("native", 3),
        ("home_aurelia_main", 0) # Fallback to Aurelia for main
    ]
    
    for ed, col_idx in editions:
        bg = colors[ed]
        for res_name, w, h in resolutions:
            dest_name = f"ha_wallpaper_{ed}_{w}x{h}.png"
            dest_path = os.path.join(root, "02-Wallpapers", res_name, dest_name)
            
            generate_card_wallpaper(master_board, dest_path, col_idx, w, h, bg)
            
            # Sync to YES-GO-SOURCE and live-build directories
            sync_paths = [
                os.path.join("/Users/bj90-m1/PhoenixCore-/HomeAurelia-Full-Pack-YES-GO-SOURCE/Editions", ed.capitalize(), "Wallpapers", f"wallpaper_{w}x{h}.png"),
                os.path.join("/Users/bj90-m1/PhoenixCore-/os/phoenix-os/live-build/config/includes.chroot/usr/share/home-aurelia-theme-pack/02-Wallpapers", res_name, dest_name)
            ]
            for s_path in sync_paths:
                os.makedirs(os.path.dirname(s_path), exist_ok=True)
                shutil.copy2(dest_path, s_path)
                
    print("\n✨ SUCCESS: All wallpapers cropped and centered as clean premium vertical cards!")

if __name__ == "__main__":
    import shutil
    run_widen()
