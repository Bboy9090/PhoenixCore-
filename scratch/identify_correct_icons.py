import glob
import os
import numpy as np
from PIL import Image

def identify():
    dirs = glob.glob("scratch/cropped_media_*")
    print(f"Analyzing {len(dirs)} directories...")
    
    results = []
    for d in dirs:
        # Load settings.png or files.png
        icon_path = os.path.join(d, "settings.png")
        if os.path.exists(icon_path):
            img = Image.open(icon_path).convert("L") # Convert to grayscale
            arr = np.array(img)
            # Calculate standard deviation of pixels (higher means more contrast/detail)
            std = np.std(arr)
            # Calculate mean brightness
            mean = np.mean(arr)
            results.append((d, std, mean))
            print(f"Directory: {os.path.basename(d)} | settings.png STD: {std:.2f} | Mean: {mean:.2f}")
            
    # Sort by standard deviation descending
    results.sort(key=lambda x: x[1], reverse=True)
    correct_dir = results[0][0]
    print(f"\n🏆 CORRECT ICON SHEET DIRECTORY IDENTIFIED: {correct_dir} (STD: {results[0][1]:.2f})")
    
    # Let's check another icon to confirm, e.g. files.png
    print("\nConfirming with files.png:")
    for d in dirs:
        icon_path = os.path.join(d, "files.png")
        if os.path.exists(icon_path):
            img = Image.open(icon_path).convert("L")
            arr = np.array(img)
            std = np.std(arr)
            print(f"Directory: {os.path.basename(d)} | files.png STD: {std:.2f}")

if __name__ == "__main__":
    identify()
