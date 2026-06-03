import os
import glob
from PIL import Image, ImageDraw, ImageFont

base_dl = "/Users/bj90-m1/Downloads/Phoenix-Repaired"
artifact_dir = "/Users/bj90-m1/.gemini/antigravity-ide/brain/3b8eb183-5722-447f-a820-2fe3ea8fc321"

editions = ['aurelia', 'arcwyre', 'thundergod', 'native']

def make_bg_proof(edition):
    ed_bg_dir = os.path.join(base_dl, edition, "backgrounds")
    out_path = os.path.join(artifact_dir, f"{edition}-uncropped-backgrounds-proof.jpg")
    
    # We have 5 images: ksplash, calamares-01, 02, 03, 04
    images = []
    for pattern in ["*ksplash*", "*calamares-01*", "*calamares-02*", "*calamares-03*", "*calamares-04*"]:
        matches = glob.glob(os.path.join(ed_bg_dir, pattern))
        if matches:
            images.append(matches[0])
            
    if not images:
        return
        
    cols = 2
    rows = 3
    thumb_w = 480
    thumb_h = 270
    
    proof = Image.new("RGB", (cols * thumb_w, rows * thumb_h), color=(30, 30, 30))
    draw = ImageDraw.Draw(proof)
    try: font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    except: font = ImageFont.load_default()
    
    for i, img_path in enumerate(images):
        c = i % cols
        r = i // cols
        
        img = Image.open(img_path).convert("RGB")
        img.thumbnail((thumb_w - 20, thumb_h - 20))
        
        ox = c * thumb_w + (thumb_w - img.width) // 2
        oy = r * thumb_h + (thumb_h - img.height) // 2 - 10
        
        proof.paste(img, (ox, oy))
        
        fname = os.path.basename(img_path)
        # short name
        if "ksplash" in fname: label = "KSplash"
        else: label = fname.split("-calamares-")[-1].replace(".png", "").replace("-transparent", "")
        
        draw.text((c * thumb_w + 10, (r+1) * thumb_h - 25), label, fill=(255, 255, 255), font=font)
        
    proof.save(out_path, quality=90)
    print(f"Generated proof for {edition}")

def main():
    for edition in editions:
        make_bg_proof(edition)

if __name__ == "__main__":
    main()
