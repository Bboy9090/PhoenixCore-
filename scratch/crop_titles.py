import glob
import os
from PIL import Image

def crop_titles():
    files = glob.glob("/Users/bj90-m1/.gemini/antigravity-ide/brain/5f4d5834-c312-4ce9-9ea6-1cca6432bd54/.tempmediaStorage/*.png")
    os.makedirs("scratch/debug_titles", exist_ok=True)
    
    for f in files:
        img = Image.open(f)
        w, h = img.size
        if w == 1280 and h == 896:
            # Crop top title area
            # x: 300 to 980, y: 10 to 180
            cropped = img.crop((300, 10, 980, 180))
            out_name = f"scratch/debug_titles/{os.path.basename(f)}"
            cropped.save(out_name)
            print(f"Saved cropped title for {os.path.basename(f)} to {out_name}")

if __name__ == "__main__":
    crop_titles()
