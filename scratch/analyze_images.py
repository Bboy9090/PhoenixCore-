import glob
import os
from PIL import Image

def analyze():
    # Let's inspect the images in tempmediaStorage
    files = glob.glob("/Users/bj90-m1/.gemini/antigravity-ide/brain/5f4d5834-c312-4ce9-9ea6-1cca6432bd54/.tempmediaStorage/*.png")
    print(f"Found {len(files)} png files in tempmediaStorage")
    
    for f in files:
        img = Image.open(f)
        w, h = img.size
        # Crop the top-center area where the titles usually are
        # Let's say top 15% of the height, and middle 50% of the width
        crop_w = int(w * 0.5)
        crop_h = int(h * 0.15)
        left = int(w * 0.25)
        top = 0
        
        cropped = img.crop((left, top, left + crop_w, crop_h))
        # Let's save these cropped titles for identification or look at their unique color patterns
        # We can also compute average color of the image or search for the word 'ICON SET' using basic OCR
        # Or print image info
        print(f"File: {os.path.basename(f)} size: {w}x{h}")

if __name__ == "__main__":
    analyze()
