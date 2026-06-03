import os
from PIL import Image

def inspect():
    src_dir = "/Users/bj90-m1/PhoenixCore-/HomeAurelia-Theme-Pack/02-Wallpapers/Source"
    files = ["ha_wallpaper_arcwyre.png", "ha_wallpaper_aurelia.png", "ha_wallpaper_thundergod.png", "ha_wallpaper_native.png"]
    
    for f in files:
        path = os.path.join(src_dir, f)
        if os.path.exists(path):
            img = Image.open(path)
            w, h = img.size
            print(f"File: {f} | Size: {w}x{h}")
        else:
            print(f"File: {f} | Exist: False")

if __name__ == "__main__":
    inspect()
