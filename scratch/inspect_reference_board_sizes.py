import os
from PIL import Image

def inspect():
    ref_dir = "/Users/bj90-m1/PhoenixCore-/HomeAurelia-Full-Pack-SOURCE-TRUTH/Shared/Reference-Boards/01_APPROVED_REFERENCE_BOARDS/"
    files = os.listdir(ref_dir)
    for f in files:
        if f.endswith(".png") or f.endswith(".jpg"):
            img = Image.open(os.path.join(ref_dir, f))
            print(f"File: {f} | Size: {img.size}")

if __name__ == "__main__":
    inspect()
