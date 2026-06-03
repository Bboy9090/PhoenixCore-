import os
from PIL import Image

def inspect():
    scratch_dir = "/Users/bj90-m1/PhoenixCore-/scratch"
    dirs = [
        "cropped_media_5f4d5834-c312-4ce9-9ea6-1cca6432bd54_1780186723650.png",
        "cropped_media_5f4d5834-c312-4ce9-9ea6-1cca6432bd54_1780186727410.png"
    ]
    
    for d in dirs:
        full_path = os.path.join(scratch_dir, d)
        print(f"\n📁 Directory: {d}")
        files = sorted(os.listdir(full_path))
        for f in files:
            if f.endswith(".png"):
                img = Image.open(os.path.join(full_path, f))
                print(f"   Icon: {f:<15} | Size: {img.size[0]:>4}x{img.size[1]:<4}")

if __name__ == "__main__":
    inspect()
