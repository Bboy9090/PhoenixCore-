import os
import shutil
from PIL import Image

def process_uploaded():
    brain_dir = "/Users/bj90-m1/.gemini/antigravity-ide/brain/9b2350a5-72dc-4161-9f86-9adc3db2a108"
    theme_pack_root = "/Users/bj90-m1/PhoenixCore-/HomeAurelia-Theme-Pack"
    yes_go_root = "/Users/bj90-m1/PhoenixCore-/HomeAurelia-Full-Pack-YES-GO-SOURCE"
    
    # Map the exact uploaded media files to their respective editions
    # media__1780263988505.jpg -> Arcwyre
    # media__1780263990444.jpg -> Aurelia / Main (sapphire blue with violet/pink electricity)
    # media__1780263992118.jpg -> Thundergod / Native fallback
    
    mapping = {
        "arcwyre": os.path.join(brain_dir, "media__1780263988505.jpg"),
        "aurelia": os.path.join(brain_dir, "media__1780263990444.jpg"),
        "home_aurelia_main": os.path.join(brain_dir, "media__1780263990444.jpg"),
        "thundergod": os.path.join(brain_dir, "media__1780263992118.jpg"),
        "native": os.path.join(brain_dir, "media__1780263988505.jpg") # Native matches Arcwyre/rebel layout with different colors, fallback to uploaded
    }
    
    resolutions = [
        ("4K", 3840, 2160),
        ("QHD", 2560, 1440),
        ("FHD", 1920, 1080),
        ("Ultrawide", 3440, 1440)
    ]
    
    for ed, src_p in mapping.items():
        if os.path.exists(src_p):
            print(f"\n🖼️  Processing authentic widescreen uploaded wallpaper for: {ed}...")
            img = Image.open(src_p).convert("RGB")
            
            # Copy as source wallpaper
            src_dest = os.path.join(theme_pack_root, "02-Wallpapers/Source", f"ha_wallpaper_{ed}.png")
            os.makedirs(os.path.dirname(src_dest), exist_ok=True)
            img.save(src_dest, "PNG")
            
            for res_name, w, h in resolutions:
                dest_name = f"ha_wallpaper_{ed}_{w}x{h}.png"
                dest_path = os.path.join(theme_pack_root, "02-Wallpapers", res_name, dest_name)
                
                # Resize keeping ratio or clean fill
                resized = img.resize((w, h), Image.Resampling.LANCZOS)
                resized.save(dest_path, "PNG")
                
                # Sync to YES-GO-SOURCE and live-build directories
                sync_paths = [
                    os.path.join(yes_go_root, "Editions", ed.capitalize(), "Wallpapers", f"wallpaper_{w}x{h}.png"),
                    os.path.join("/Users/bj90-m1/PhoenixCore-/os/phoenix-os/live-build/config/includes.chroot/usr/share/home-aurelia-theme-pack/02-Wallpapers", res_name, dest_name)
                ]
                for s_path in sync_paths:
                    os.makedirs(os.path.dirname(s_path), exist_ok=True)
                    shutil.copy2(dest_path, s_path)
                    
            print(f"   ✅ Successfully scaled and distributed all resolutions for {ed}!")
        else:
            print(f"⚠️  Uploaded file not found for: {ed} ({src_p})")

if __name__ == "__main__":
    process_uploaded()
