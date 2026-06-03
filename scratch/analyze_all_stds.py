import glob
import os
import numpy as np
from PIL import Image

def analyze_all():
    dirs = glob.glob("scratch/cropped_media_*")
    
    for d in dirs:
        print(f"\n==================================================")
        print(f"📁 ANALYZING DIRECTORY: {os.path.basename(d)}")
        print(f"==================================================")
        
        stds = []
        for name in ["home", "files", "documents", "downloads", "music", "pictures", "videos", "trash", "settings", "terminal", "browser", "mail", "calendar", "network", "bluetooth", "user", "power", "software", "help", "drive", "system"]:
            p = os.path.join(d, f"{name}.png")
            if os.path.exists(p):
                img = Image.open(p).convert("L")
                std = np.std(np.array(img))
                stds.append(std)
                # print(f"  {name}.png STD: {std:.2f}")
                
        avg_std = np.mean(stds)
        print(f"🌟 AVERAGE ICON DETAIL (STD): {avg_std:.2f}")

if __name__ == "__main__":
    analyze_all()
