import os
from PIL import Image
import numpy as np

def analyze():
    editions = ["Aurelia", "Arcwyre", "Thundergod", "Native"]
    for ed in editions:
        path = f"/Users/bj90-m1/PhoenixCore-/HomeAurelia-Full-Pack-YES-GO-SOURCE/Editions/{ed}/Icons/HomeAurelia-{ed}-Icons/512x512/places/folder.png"
        if os.path.exists(path):
            img = Image.open(path).convert("RGBA")
            arr = np.array(img)
            # Filter out transparent pixels
            pixels = arr[arr[:, :, 3] > 50]
            if len(pixels) > 0:
                avg_color = np.mean(pixels[:, :3], axis=0)
                print(f"Edition: {ed} | Path exists: True | Avg Color (R,G,B): {avg_color}")
            else:
                print(f"Edition: {ed} | Path exists: True | Empty/Transparent Image")
        else:
            print(f"Edition: {ed} | Path exists: False")

if __name__ == "__main__":
    analyze()
