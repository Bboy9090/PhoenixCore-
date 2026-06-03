import os
import shutil
import zipfile

def build_packages():
    print("🚀 Initializing Dynamic Flagship Icon Packaging Engine...")
    
    src_dir = "scratch/final_icon_set"
    clean_dir = "scratch/clean_icon_set"
    max_compat_dir = "scratch/max_compat_icon_set"
    
    os.makedirs(clean_dir, exist_ok=True)
    os.makedirs(max_compat_dir, exist_ok=True)
    
    sizes = ["16x16", "22x22", "24x24", "32x32", "48x48", "64x64", "128x128", "256x256", "512x512"]
    categories = ["places", "apps", "actions", "devices", "status", "mimetypes", "categories", "emblems"]
    
    # ------------------ DEFINE CLEAN PLACEMENT DIRECTIVES ------------------
    # Map icon names to their primary folder targets
    clean_rules = {
        # places/
        "folder": ["places"],
        "folder-home": ["places"],
        "folder-documents": ["places"],
        "folder-downloads": ["places"],
        "folder-music": ["places"],
        "folder-pictures": ["places"],
        "folder-videos": ["places"],
        "user-trash": ["places", "status"], # Allowed compatibility overlap
        "user-trash-full": ["places", "status"],
        # apps/
        "system-settings": ["apps"],
        "preferences-system": ["apps"],
        "utilities-terminal": ["apps"],
        "internet-web-browser": ["apps"],
        "internet-mail": ["apps"],
        "office-calendar": ["apps"],
        "system-software-install": ["apps"],
        "dialog-question": ["apps", "actions"],
        # actions/
        "system-shutdown": ["actions", "apps"],
        "system-reboot": ["actions", "apps"],
        # devices/
        "drive-harddisk": ["devices"],
        "drive-removable-media": ["devices"],
        "computer": ["devices"],
        # status/
        "network-wireless": ["status", "apps"],
        "network-workgroup": ["status", "apps"],
        "bluetooth": ["status", "apps"],
        # mimetypes/
        "text-x-generic": ["mimetypes"],
        "audio-x-generic": ["mimetypes"],
        "image-x-generic": ["mimetypes"],
        "video-x-generic": ["mimetypes"],
        # categories/
        "start-here-kde": ["categories", "places"],
        "accessories-calculator": ["apps"],
        "accessories-text-editor": ["apps"],
        "network-firewall": ["apps"]
    }
    
    # Clean up directories before building
    if os.path.exists(clean_dir):
        shutil.rmtree(clean_dir)
    if os.path.exists(max_compat_dir):
        shutil.rmtree(max_compat_dir)
        
    os.makedirs(clean_dir, exist_ok=True)
    os.makedirs(max_compat_dir, exist_ok=True)

    # ------------------ STAGE CLEAN VERSION ------------------
    print("🧹 Constructing HomeAurelia-Icons-Clean package...")
    clean_written = 0
    
    # 1. Copy Scalable SVGs
    for name, targets in clean_rules.items():
        src_svg_path = os.path.join(src_dir, "scalable/places", f"{name}.svg") # All SVGs exist in places in src_dir
        if not os.path.exists(src_svg_path):
            src_svg_path = os.path.join(src_dir, "scalable/apps", f"{name}.svg")
            
        if os.path.exists(src_svg_path):
            for t in targets:
                dest_svg_dir = os.path.join(clean_dir, "scalable", t)
                os.makedirs(dest_svg_dir, exist_ok=True)
                shutil.copy2(src_svg_path, os.path.join(dest_svg_dir, f"{name}.svg"))
                clean_written += 1
                
    # 2. Copy raster sizes
    for sz in sizes:
        for name, targets in clean_rules.items():
            src_png_path = os.path.join(src_dir, sz, "places", f"{name}.png")
            if not os.path.exists(src_png_path):
                src_png_path = os.path.join(src_dir, sz, "apps", f"{name}.png")
                
            if os.path.exists(src_png_path):
                for t in targets:
                    dest_png_dir = os.path.join(clean_dir, sz, t)
                    os.makedirs(dest_png_dir, exist_ok=True)
                    shutil.copy2(src_png_path, os.path.join(dest_png_dir, f"{name}.png"))
                    clean_written += 1
                    
    # Generate clean index.theme
    clean_dirs = set()
    for name, targets in clean_rules.items():
        for t in targets:
            clean_dirs.add(f"scalable/{t}")
            for sz in sizes:
                clean_dirs.add(f"{sz}/{t}")
                
    clean_theme_content = f"""[Icon Theme]
Name=Home Aurelia Icons (Clean)
Comment=Home Aurelia premium clean icon set focused on strict KDE category placements.
Inherits=breeze-dark,breeze,hicolor
Directories={','.join(sorted(list(clean_dirs)))}

"""
    # Scalable headers
    for t in sorted(categories):
        if f"scalable/{t}" in clean_dirs:
            clean_theme_content += f"""[scalable/{t}]
Size=512
Context={t.capitalize()}
Type=Scalable
MinSize=16
MaxSize=512

"""
    # Size headers
    for sz in sizes:
        w = sz.split("x")[0]
        for t in sorted(categories):
            if f"{sz}/{t}" in clean_dirs:
                clean_theme_content += f"""[{sz}/{t}]
Size={w}
Context={t.capitalize()}
Type=Fixed

"""
                
    with open(os.path.join(clean_dir, "index.theme"), "w") as f:
        f.write(clean_theme_content)
        
    print(f"   ✅ Constructed Clean package structure: {clean_written} assets.")

    # ------------------ STAGE MAX-COMPAT VERSION ------------------
    print("⚡ Constructing HomeAurelia-Icons-MaxCompat package...")
    # MaxCompat is a straight copy of final_icon_set since it already has maximum broad duplicates
    shutil.copytree(src_dir, max_compat_dir, dirs_exist_ok=True)
    # Rewrite index.theme to show MaxCompat comment
    max_dirs = []
    for cat in categories:
        max_dirs.append(f"scalable/{cat}")
    for sz in sizes:
        for cat in categories:
            max_dirs.append(f"{sz}/{cat}")
            
    max_theme_content = f"""[Icon Theme]
Name=Home Aurelia Icons (MaxCompat)
Comment=Home Aurelia premium maximum compatibility icon set with broad duplicate placement.
Inherits=breeze-dark,breeze,hicolor
Directories={','.join(max_dirs)}

"""
    for cat in categories:
        max_theme_content += f"""[scalable/{cat}]
Size=512
Context={cat.capitalize()}
Type=Scalable
MinSize=16
MaxSize=512

"""
    for sz in sizes:
        w = sz.split("x")[0]
        for cat in categories:
            max_theme_content += f"""[{sz}/{cat}]
Size={w}
Context={cat.capitalize()}
Type=Fixed

"""
            
    with open(os.path.join(max_compat_dir, "index.theme"), "w") as f:
        f.write(max_theme_content)
        
    print("   ✅ Constructed MaxCompat package structure.")

    # ------------------ ZIP BOTH PACKAGES ------------------
    print("📦 Compressing both flagship zips...")
    
    zip_clean = "HomeAurelia-Icons-Clean.zip"
    zip_max = "HomeAurelia-Icons-MaxCompat.zip"
    
    # 1. Zip Clean
    with zipfile.ZipFile(zip_clean, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(clean_dir):
            for file in files:
                filepath = os.path.join(root, file)
                rel_path = os.path.join("HomeAurelia-Icons-Clean", os.path.relpath(filepath, clean_dir))
                zipf.write(filepath, rel_path)
                
    # 2. Zip MaxCompat
    with zipfile.ZipFile(zip_max, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(max_compat_dir):
            for file in files:
                filepath = os.path.join(root, file)
                rel_path = os.path.join("HomeAurelia-Icons-MaxCompat", os.path.relpath(filepath, max_compat_dir))
                zipf.write(filepath, rel_path)
                
    print(f"   ✅ COMPRESSED: {zip_clean} & {zip_max}")

    # ------------------ GENERATE FILE LIST TEXTS ------------------
    print("📜 Exporting complete file tree text reports...")
    
    # Clean File list
    clean_list_path = "HomeAurelia-Icons-Clean-FileTree.txt"
    with open(clean_list_path, "w") as f:
        f.write("===================================================\n")
        f.write("👑 HOME AURELIA — CLEAN ICON SET COMPLETE FILE TREE\n")
        f.write("===================================================\n\n")
        for root, dirs, files in os.walk(clean_dir):
            for file in files:
                f.write(os.path.relpath(os.path.join(root, file), clean_dir) + "\n")
                
    # MaxCompat File list
    max_list_path = "HomeAurelia-Icons-MaxCompat-FileTree.txt"
    with open(max_list_path, "w") as f:
        f.write("===================================================\n")
        f.write("⚡ HOME AURELIA — MAX-COMPAT ICON SET COMPLETE FILE TREE\n")
        f.write("===================================================\n\n")
        for root, dirs, files in os.walk(max_compat_dir):
            for file in files:
                f.write(os.path.relpath(os.path.join(root, file), max_compat_dir) + "\n")
                
    # Also stage reports under Core Shared-Docs and workspace root
    shutil.copy2(clean_list_path, "HomeAurelia-Full-Pack/Core/Shared-Docs/")
    shutil.copy2(max_list_path, "HomeAurelia-Full-Pack/Core/Shared-Docs/")
    
    # ------------------ DISTRIBUTE PACKAGES ------------------
    print("🚀 Distributing ZIPs to theme packs and chroot environments...")
    target_roots = [
        "HomeAurelia-Theme-Pack/09-Icons/",
        "HomeAurelia-Full-Pack/Core/HomeAurelia-Icons/",
        "os/phoenix-os/live-build/config/includes.chroot/usr/share/icons/home-aurelia/",
        "os/phoenix-os/live-build/config/includes.chroot/usr/share/home-aurelia-theme-pack/09-Icons/"
    ]
    
    for r in target_roots:
        os.makedirs(r, exist_ok=True)
        shutil.copy2(zip_clean, r)
        shutil.copy2(zip_max, r)
        shutil.copy2(clean_list_path, r)
        shutil.copy2(max_list_path, r)
        
    print("✨ SUCCESS: Both Clean and MaxCompat visual sets compiled, packed, and distributed!")

if __name__ == "__main__":
    build_packages()
