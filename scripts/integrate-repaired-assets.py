import os
import shutil
import glob

base_dl = "/Users/bj90-m1/Downloads/Phoenix-Repaired"
repo_editions = "/Users/bj90-m1/PhoenixCore-/editions"

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
    "calamares-04-ascend-1920x1080.png": "calamares_4.png",
    "default-user-avatar-512x512.png": "avatar.png",
    "kickoff-start-menu-icon-256x256-transparent.png": "start_menu.png",
    "fastfetch-terminal-image-512x512-transparent.png": "fastfetch_logo.png",
    "about-this-system-logo-512x512-transparent.png": "about_logo.png"
}

def integrate():
    for source_ed, target_ed in edition_map.items():
        # Copy custom art
        source_art_dir = os.path.join(base_dl, source_ed, "branding")
        target_art_dir = os.path.join(repo_editions, target_ed, "custom_art")
        
        if not os.path.exists(target_art_dir):
            os.makedirs(target_art_dir)
            
        for src_name, tgt_name in art_mapping.items():
            prefixed_src = f"{source_ed}-{src_name}"
            src_path_branding = os.path.join(base_dl, source_ed, "branding", prefixed_src)
            src_path_backgrounds = os.path.join(base_dl, source_ed, "backgrounds", prefixed_src)
            tgt_path = os.path.join(target_art_dir, tgt_name)
            
            if os.path.exists(src_path_branding):
                shutil.copy2(src_path_branding, tgt_path)
                print(f"Copied {prefixed_src} to {target_ed}/custom_art/{tgt_name}")
            elif os.path.exists(src_path_backgrounds):
                shutil.copy2(src_path_backgrounds, tgt_path)
                print(f"Copied {prefixed_src} to {target_ed}/custom_art/{tgt_name}")
            else:
                print(f"MISSING: {src_name} in {source_ed}")
                
        # Copy app icons
        source_icons_dir = os.path.join(base_dl, source_ed, "icons", "512x512")
        target_icons_dir = os.path.join(repo_editions, target_ed, "custom_icons")
        
        if not os.path.exists(target_icons_dir):
            os.makedirs(target_icons_dir)
            
        # For app icons, we need to map the named singles to the linux icon names
        # We can just look at the mapping from a known list or just copy everything if the OS build script maps it.
        # But wait, earlier I saw custom_icons has 'folder.png', 'utilities-terminal.png'.
        # The named singles are like `aurelia-terminal-512x512.png`.
        # I'll build a mapping heuristic
        icon_mapping = {
            "calculator": "accessories-calculator.png",
            "text-editor": "accessories-text-editor.png",
            "browser": "firefox.png",
            "folder": "folder.png",
            "terminal": "utilities-terminal.png",
            "settings": "systemsettings.png",
            "calendar": "office-calendar.png",
            "firewall": "preferences-system-firewall.png",
            "bluetooth": "network-bluetooth.png",
            "wireless": "network-wireless.png",
            "harddisk": "drive-harddisk.png",
            "reboot": "system-reboot.png",
            "shutdown": "system-shutdown.png",
            "trash": "user-trash.png",
            "file-manager": "system-file-manager.png",
            "mail": "thunderbird.png",
            "software-install": "system-software-install.png",
            "software-update": "system-software-update.png"
        }
        
        for src_path in glob.glob(os.path.join(source_icons_dir, "*.png")):
            src_base = os.path.basename(src_path)
            for key, tgt_name in icon_mapping.items():
                if key in src_base:
                    tgt_path = os.path.join(target_icons_dir, tgt_name)
                    shutil.copy2(src_path, tgt_path)
                    print(f"Copied {src_base} to {target_ed}/custom_icons/{tgt_name}")
                    break

if __name__ == "__main__":
    integrate()
