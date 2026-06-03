import os
import glob
import shutil
from PIL import Image

base_dl = "/Users/bj90-m1/Downloads"
repaired_dir = os.path.join(base_dl, "Phoenix-Repaired")
repo_editions = "/Users/bj90-m1/PhoenixCore-/editions"

editions = ['aurelia', 'arcwyre', 'thundergod', 'native']

edition_map = {
    "aurelia": "home",
    "arcwyre": "arcwyre",
    "thundergod": "thunder-god",
    "native": "blue-phoenix"
}

art_mapping = {
    "ksplash-1920x1080.png": "ksplash_bg.png",
    "calamares-01-welcome-1920x1080.png": "calamares_1.png",
    "calamares-02-philosophy-1920x1080.png": "calamares_2.png",
    "calamares-03-features-1920x1080.png": "calamares_3.png",
    "calamares-04-ascend-1920x1080.png": "calamares_4.png"
}

def get_source_files(edition):
    files = {}
    for root, dirs, filenames in os.walk(base_dl):
        if edition.lower() not in root.lower() or "repaired" in root.lower():
            continue
        for fname in filenames:
            if not fname.endswith(".png"): continue
            if "raw-crop" in fname: continue
            fpath = os.path.join(root, fname)
            fname_lower = fname.lower()
            
            if "ksplash" in fname_lower: files['ksplash'] = fpath
            elif "calamares-01" in fname_lower: files['calamares-01'] = fpath
            elif "calamares-02" in fname_lower: files['calamares-02'] = fpath
            elif "calamares-03" in fname_lower: files['calamares-03'] = fpath
            elif "calamares-04" in fname_lower: files['calamares-04'] = fpath
    return files

def resize_strict(img_path, target_size):
    try:
        img = Image.open(img_path).convert("RGBA")
        # STRICT RESIZE - NO CROPPING AT ALL
        return img.resize(target_size, Image.Resampling.LANCZOS)
    except Exception as e:
        print(f"Error resizing {img_path}: {e}")
        return None

def main():
    for edition in editions:
        src_files = get_source_files(edition)
        ed_dir = os.path.join(repaired_dir, edition, "backgrounds")
        target_ed = edition_map[edition]
        target_art_dir = os.path.join(repo_editions, target_ed, "custom_art")
        
        for key in ['ksplash', 'calamares-01', 'calamares-02', 'calamares-03', 'calamares-04']:
            if key in src_files:
                original_path = src_files[key]
                out_name = os.path.basename(original_path)
                
                # 1. Resize strictly to 1920x1080
                img = resize_strict(original_path, (1920, 1080))
                if img:
                    # 2. Save to Phoenix-Repaired
                    repaired_path = os.path.join(ed_dir, out_name)
                    img.save(repaired_path)
                    
                    # 3. Copy to PhoenixCore-/editions
                    tgt_name = None
                    for k, v in art_mapping.items():
                        if key in k:
                            tgt_name = v
                            break
                            
                    if tgt_name:
                        tgt_path = os.path.join(target_art_dir, tgt_name)
                        shutil.copy2(repaired_path, tgt_path)
                        print(f"Fixed crop for {edition.upper()} -> {tgt_name}")

if __name__ == "__main__":
    main()
