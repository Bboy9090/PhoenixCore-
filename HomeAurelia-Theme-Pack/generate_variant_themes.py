#!/usr/bin/env python3
import os
import shutil
from pathlib import Path

# Base Paths
THEME_DIR = Path(__file__).parent
WALLPAPERS_DIR = THEME_DIR / "02-Wallpapers" / "FHD"
COLOR_SCHEMES_DIR = THEME_DIR / "06-Color-Schemes"
KVANTUM_DIR = THEME_DIR / "07-Kvantum"
AURORAE_DIR = THEME_DIR / "08-Window-Decorations" / "Aurorae"
PLYMOUTH_DIR = THEME_DIR / "04-Plymouth"

# Source Image paths from the AI generation
IMAGE_SOURCES = {
    "Thundergod": "/Users/bj90-m1/.gemini/antigravity-ide/brain/3b8eb183-5722-447f-a820-2fe3ea8fc321/thundergod_flying_electric_concept_1780410405177.png",
    "Aurelia": "/Users/bj90-m1/.gemini/antigravity-ide/brain/3b8eb183-5722-447f-a820-2fe3ea8fc321/aurelia_uiue_concept_1780410432227.png",
    "Arcwyre": "/Users/bj90-m1/.gemini/antigravity-ide/brain/3b8eb183-5722-447f-a820-2fe3ea8fc321/arcwyre_concept_1780407890841.png",
    "Native": "/Users/bj90-m1/.gemini/antigravity-ide/brain/3b8eb183-5722-447f-a820-2fe3ea8fc321/native_ssbk_concept_1780410419258.png"
}

# Base Theme colors defining window, text, and selection styles per variant
VARIANTS = {
    "HomeAurelia-Thundergod": {
        "name_lower": "home-aurelia-thundergod",
        "name_kvantum": "HomeAurelia-Thundergod",
        "BackgroundNormal": "24,30,42",  # Deep Pristine Blue
        "BackgroundAlternate": "30,38,50",
        "ForegroundNormal": "255,255,255", # White
        "ForegroundInactive": "160,165,175",
        "ForegroundActive": "255,215,0", # Radiant Gold
        "ForegroundLink": "255,50,50", # Vivid Red
        "DecorationFocus": "255,50,50", # Red Scarf accent
        "DecorationHover": "255,215,0", # Gold Outline Hover
        "WindowBackground": "20,25,35",
        "CloseButton": "#ff3232",
        "MaxButton": "#ffd700",
        "MinButton": "#ffffff",
        "Wallpaper": "ha_wallpaper_thundergod_1920x1080.png"
    },
    "HomeAurelia-Aurelia": {
        "name_lower": "home-aurelia-aurelia",
        "name_kvantum": "HomeAurelia-Aurelia",
        "BackgroundNormal": "15,10,25",  # Cosmic Blue/Purple
        "BackgroundAlternate": "22,15,35",
        "ForegroundNormal": "245,245,255", # UI White
        "ForegroundInactive": "130,120,150",
        "ForegroundActive": "150,80,255", # UE Violet
        "ForegroundLink": "100,150,255",
        "DecorationFocus": "150,80,255", # UE Violet
        "DecorationHover": "230,230,255", # UI Silver
        "WindowBackground": "10,5,15",
        "CloseButton": "#a65cff",
        "MaxButton": "#e6e6ff",
        "MinButton": "#ffffff",
        "Wallpaper": "ha_wallpaper_aurelia_1920x1080.png"
    },
    "HomeAurelia-Arcwyre": {
        "name_lower": "home-aurelia-arcwyre",
        "name_kvantum": "HomeAurelia-Arcwyre",
        "BackgroundNormal": "8,10,12",  # Stargate Black
        "BackgroundAlternate": "12,15,18",
        "ForegroundNormal": "230,230,230",
        "ForegroundInactive": "100,110,120",
        "ForegroundActive": "255,40,40", # Striking Red
        "ForegroundLink": "0,200,200", # Glowing Teal
        "DecorationFocus": "0,200,200", # Glowing Teal
        "DecorationHover": "255,40,40", # Red Hover
        "WindowBackground": "5,6,8",
        "CloseButton": "#ff2828",
        "MaxButton": "#00c8c8",
        "MinButton": "#646e78",
        "Wallpaper": "ha_wallpaper_arcwyre_1920x1080.png"
    },
    "HomeAurelia-Native": {
        "name_lower": "home-aurelia-native",
        "name_kvantum": "HomeAurelia-Native",
        "BackgroundNormal": "15,20,45",  # Royal Divine Blue
        "BackgroundAlternate": "20,25,55",
        "ForegroundNormal": "255,255,255",
        "ForegroundInactive": "140,150,180",
        "ForegroundActive": "255,30,30", # Star Fire Red (SSBK)
        "ForegroundLink": "80,180,255", # Electric Blue
        "DecorationFocus": "255,30,30",
        "DecorationHover": "80,180,255",
        "WindowBackground": "10,12,30",
        "CloseButton": "#ff1e1e",
        "MaxButton": "#50b4ff",
        "MinButton": "#e6e6e6",
        "Wallpaper": "ha_wallpaper_native_1920x1080.png"
    }
}

def replace_in_file(filepath, replacements):
    if not filepath.exists():
        return
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    for old, new in replacements.items():
        content = content.replace(old, new)
        
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    print("⚡ Generating Full Theme Packages for Variants...")
    
    # 1. Wallpapers
    print("-> Staging Wallpapers")
    os.makedirs(WALLPAPERS_DIR, exist_ok=True)
    for variant, v_data in VARIANTS.items():
        base_name = variant.split("-")[1]
        src_image = IMAGE_SOURCES.get(base_name)
        if src_image and Path(src_image).exists():
            dest_image = WALLPAPERS_DIR / v_data["Wallpaper"]
            shutil.copy(src_image, dest_image)
            print(f"   [+] Copied {base_name} Wallpaper")

    for variant_name, v_data in VARIANTS.items():
        print(f"-> Generating Variant: {variant_name}")
        
        # 2. Color Schemes
        # We will write a robust .colors file based on a standard template.
        colors_file = COLOR_SCHEMES_DIR / f"{variant_name}.colors"
        colors_content = f"""[ColorEffects:Disabled]
Color=56,56,56
ColorAmount=0
ColorEffect=0
ContrastAmount=0.65
ContrastEffect=1
IntensityAmount=0.1
IntensityEffect=2

[ColorEffects:Inactive]
ChangeSelectionColor=true
Color=112,111,111
ColorAmount=0.025
ColorEffect=2
ContrastAmount=0.1
ContrastEffect=2
Enable=false
IntensityAmount=0
IntensityEffect=0

[Colors:Button]
BackgroundAlternate={v_data['BackgroundAlternate']}
BackgroundNormal={v_data['BackgroundNormal']}
DecorationFocus={v_data['DecorationFocus']}
DecorationHover={v_data['DecorationHover']}
ForegroundActive={v_data['ForegroundActive']}
ForegroundInactive={v_data['ForegroundInactive']}
ForegroundLink={v_data['ForegroundLink']}
ForegroundNormal={v_data['ForegroundNormal']}

[Colors:Selection]
BackgroundAlternate={v_data['DecorationFocus']}
BackgroundNormal={v_data['DecorationFocus']}
DecorationFocus={v_data['DecorationFocus']}
DecorationHover={v_data['DecorationHover']}
ForegroundActive={v_data['ForegroundNormal']}
ForegroundInactive={v_data['ForegroundInactive']}
ForegroundLink={v_data['ForegroundLink']}
ForegroundNormal={v_data['ForegroundNormal']}

[Colors:View]
BackgroundAlternate={v_data['BackgroundAlternate']}
BackgroundNormal={v_data['BackgroundNormal']}
DecorationFocus={v_data['DecorationFocus']}
DecorationHover={v_data['DecorationHover']}
ForegroundActive={v_data['ForegroundActive']}
ForegroundInactive={v_data['ForegroundInactive']}
ForegroundLink={v_data['ForegroundLink']}
ForegroundNormal={v_data['ForegroundNormal']}

[Colors:Window]
BackgroundAlternate={v_data['WindowBackground']}
BackgroundNormal={v_data['WindowBackground']}
DecorationFocus={v_data['DecorationFocus']}
DecorationHover={v_data['DecorationHover']}
ForegroundActive={v_data['ForegroundActive']}
ForegroundInactive={v_data['ForegroundInactive']}
ForegroundLink={v_data['ForegroundLink']}
ForegroundNormal={v_data['ForegroundNormal']}

[General]
ColorScheme={variant_name}
Name={variant_name}
"""
        with open(colors_file, "w") as f:
            f.write(colors_content)
        
        # 3. Kvantum
        base_kvantum = KVANTUM_DIR / "HomeAurelia"
        target_kvantum = KVANTUM_DIR / v_data["name_kvantum"]
        if base_kvantum.exists() and not target_kvantum.exists():
            shutil.copytree(base_kvantum, target_kvantum)
            # rename inner file
            if (target_kvantum / "HomeAurelia.kvconfig").exists():
                (target_kvantum / "HomeAurelia.kvconfig").rename(target_kvantum / f"{v_data['name_kvantum']}.kvconfig")
        
        # 4. Aurorae (Window Decorations)
        base_aurorae = AURORAE_DIR / "HomeAurelia"
        target_aurorae = AURORAE_DIR / v_data["name_kvantum"]
        if base_aurorae.exists() and not target_aurorae.exists():
            shutil.copytree(base_aurorae, target_aurorae)
            replace_in_file(target_aurorae / "metadata.desktop", {
                "Name=HomeAurelia": f"Name={v_data['name_kvantum']}",
                "X-KDE-PluginInfo-Name=HomeAurelia": f"X-KDE-PluginInfo-Name={v_data['name_kvantum']}"
            })
            # To actually color the buttons inside decoration.svg we would do hex code replacements
            # For this MVP, we rely on the colorscheme to style the window contents, but we can do a naive replace
            replace_in_file(target_aurorae / "decoration.svg", {
                "#ff5555": v_data["CloseButton"],
                "#ffb86c": v_data["MaxButton"],
                "#f8f8f2": v_data["MinButton"],
                "#282a36": f"rgb({v_data['WindowBackground']})"
            })

        # 5. Plymouth
        base_plymouth = PLYMOUTH_DIR / "home-aurelia"
        target_plymouth = PLYMOUTH_DIR / v_data["name_lower"]
        if base_plymouth.exists() and not target_plymouth.exists():
            shutil.copytree(base_plymouth, target_plymouth)
            if (target_plymouth / "home-aurelia.plymouth").exists():
                (target_plymouth / "home-aurelia.plymouth").rename(target_plymouth / f"{v_data['name_lower']}.plymouth")
            if (target_plymouth / "home-aurelia.script").exists():
                (target_plymouth / "home-aurelia.script").rename(target_plymouth / f"{v_data['name_lower']}.script")
            
            replace_in_file(target_plymouth / f"{v_data['name_lower']}.plymouth", {
                "Name=Home Aurelia": f"Name={variant_name}",
                "ModuleName=script": "ModuleName=script",
                "home-aurelia": v_data["name_lower"]
            })
            
            # Map the splash image
            base_img = target_plymouth / "splash.png"
            variant_img = target_plymouth / f"splash-{variant_name.split('-')[1].lower()}.png"
            if variant_img.exists():
                shutil.copy(variant_img, base_img)

    print("✅ All themes generated successfully!")

if __name__ == "__main__":
    main()
