import glob
import os
from PIL import Image

def crop_icons():
    files = glob.glob("/Users/bj90-m1/.gemini/antigravity-ide/brain/5f4d5834-c312-4ce9-9ea6-1cca6432bd54/.tempmediaStorage/*.png")
    
    # We want to identify the Icon Set sheet among the 1280x896 images.
    # In Sheet 1 (Icon Set), there are 21 system icons arranged in a clean grid.
    # Let's define the centers for the columns and rows:
    col_centers = [248, 340, 432, 524, 616, 708, 800, 892]
    row_centers = [350, 530, 710]
    
    # Names for the icons in each row
    row1_names = ["home", "files", "documents", "downloads", "music", "pictures", "videos", "trash"]
    row2_names = ["settings", "terminal", "browser", "mail", "calendar", "network", "bluetooth", "user"]
    row3_names = ["power", "software", "help", "drive", "system"] # Aligned to col_centers 1 to 5 (i.e. index 1 to 5)
    
    # Let's crop from all three 1280x896 images into separate folders so we can find the correct one!
    for f in files:
        img = Image.open(f)
        w, h = img.size
        if w == 1280 and h == 896:
            img_name = os.path.basename(f)
            folder_name = f"scratch/cropped_{img_name}"
            os.makedirs(folder_name, exist_ok=True)
            print(f"Slicing image {img_name} into {folder_name}...")
            
            # Row 1 (8 icons)
            for col_idx, name in enumerate(row1_names):
                cx = col_centers[col_idx]
                cy = row_centers[0]
                # Crop a 96x96 box around center
                box = (cx - 48, cy - 48, cx + 48, cy + 48)
                cropped = img.crop(box)
                cropped.save(f"{folder_name}/{name}.png")
                
            # Row 2 (8 icons)
            for col_idx, name in enumerate(row2_names):
                cx = col_centers[col_idx]
                cy = row_centers[1]
                box = (cx - 48, cy - 48, cx + 48, cy + 48)
                cropped = img.crop(box)
                cropped.save(f"{folder_name}/{name}.png")
                
            # Row 3 (5 icons centered)
            for col_idx, name in enumerate(row3_names):
                # Aligned to column index 1 to 5 (i.e. col_centers 1, 2, 3, 4, 5)
                cx = col_centers[col_idx + 1]
                cy = row_centers[2]
                box = (cx - 48, cy - 48, cx + 48, cy + 48)
                cropped = img.crop(box)
                cropped.save(f"{folder_name}/{name}.png")
                
            print(f"✅ Sliced 21 icons from {img_name}")

if __name__ == "__main__":
    crop_icons()
