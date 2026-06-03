import base64
import os

def embed_logo():
    logo_path = "HomeAurelia-Theme-Pack/14-Branding/logo.png"
    if not os.path.exists(logo_path):
        print(f"❌ Logo file not found at {logo_path}")
        return
        
    with open(logo_path, "rb") as f:
        img_data = f.read()
        b64_str = base64.b64encode(img_data).decode("utf-8")
        
    # 1. start-here-kde.svg (The glorious circular gold-and-blue Aurelia Crest shield from Sheet 1)
    start_here_svg = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="512" height="512" viewBox="0 0 512 512" version="1.1">
  <defs>
    <!-- Soft blue aura backing glow as specified in the style guides -->
    <radialGradient id="logoGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#00C3FF" stop-opacity="0.45" />
      <stop offset="100%" stop-color="#1E6BFF" stop-opacity="0" />
    </radialGradient>
  </defs>
  
  <!-- Backing Glow -->
  <circle cx="256" cy="256" r="240" fill="url(#logoGlow)"/>
  
  <!-- The exact High-Fidelity Sovereign Gold-and-Blue Crest from the design sheet -->
  <image xlink:href="data:image/png;base64,{b64_str}" width="490" height="490" x="11" y="11"/>
</svg>
"""

    # 2. folder.svg (The "Files" icon from Sheet 1 - Glossy navy-blue folder with centered gold-blue crest)
    folder_svg = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="512" height="512" viewBox="0 0 512 512" version="1.1">
  <defs>
    <!-- Folder Back Flap Gradient (Deepest Navy) -->
    <linearGradient id="backFlapGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0F1E3A" />
      <stop offset="100%" stop-color="#05070D" />
    </linearGradient>

    <!-- Folder Front Flap Gradient (Glossy Premium Blue-Navy) -->
    <linearGradient id="frontFlapGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#1A2E5C" />
      <stop offset="40%" stop-color="#0F1E3A" />
      <stop offset="100%" stop-color="#070D1A" />
    </linearGradient>

    <!-- Active Base Glow Gradient (Electric Blue) -->
    <linearGradient id="baseGlowGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00C3FF" stop-opacity="0" />
      <stop offset="25%" stop-color="#00C3FF" stop-opacity="1" />
      <stop offset="75%" stop-color="#00C3FF" stop-opacity="1" />
      <stop offset="100%" stop-color="#00C3FF" stop-opacity="0" />
    </linearGradient>

    <!-- Gold Edge Trim Gradient -->
    <linearGradient id="goldTrimGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#D4AF37" />
      <stop offset="50%" stop-color="#FFC857" />
      <stop offset="100%" stop-color="#D4AF37" />
    </linearGradient>
  </defs>

  <!-- [Back Flap and Tab] -->
  <path d="M 40,90 C 40,75 55,65 70,65 L 180,65 C 195,65 205,80 215,95 L 235,120 L 442,120 C 457,120 472,135 472,150 L 472,410 C 472,425 457,440 442,440 L 70,440 C 55,440 40,425 40,410 Z" 
        fill="url(#backFlapGrad)" stroke="#1E6BFF" stroke-width="3" />

  <!-- [Front Flap with shorter rounded profile] -->
  <path d="M 40,150 C 40,135 55,125 70,125 L 442,125 C 457,125 472,135 472,150 L 472,410 C 472,425 457,440 442,440 L 70,440 C 55,440 40,425 40,410 Z" 
        fill="url(#frontFlapGrad)" stroke="#1E6BFF" stroke-width="2" />

  <!-- [Thin Gold Border Accent Trim on the top edge of the front flap] -->
  <path d="M 70,125 L 442,125" stroke="url(#goldTrimGrad)" stroke-width="2.5" stroke-linecap="round" />

  <!-- [Electric Blue Glowing highlight line at the bottom] -->
  <path d="M 70,434 L 442,434" stroke="url(#baseGlowGrad)" stroke-width="4.5" stroke-linecap="round" />

  <!-- [The exact High-Fidelity Sovereign Gold-and-Blue Crest centered in the middle of the flap] -->
  <image xlink:href="data:image/png;base64,{b64_str}" width="220" height="220" x="146" y="165"/>
</svg>
"""

    # 3. folder-home.svg (The "Home" folder - Circular Crest overlay with nested gold house outline in center)
    folder_home_svg = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="512" height="512" viewBox="0 0 512 512" version="1.1">
  <defs>
    <!-- Folder Back Flap Gradient (Deepest Navy) -->
    <linearGradient id="backFlapGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0F1E3A" />
      <stop offset="100%" stop-color="#05070D" />
    </linearGradient>

    <!-- Folder Front Flap Gradient (Glossy Premium Blue-Navy) -->
    <linearGradient id="frontFlapGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#1A2E5C" />
      <stop offset="40%" stop-color="#0F1E3A" />
      <stop offset="100%" stop-color="#070D1A" />
    </linearGradient>

    <!-- Active Base Glow Gradient (Electric Blue) -->
    <linearGradient id="baseGlowGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00C3FF" stop-opacity="0" />
      <stop offset="25%" stop-color="#00C3FF" stop-opacity="1" />
      <stop offset="75%" stop-color="#00C3FF" stop-opacity="1" />
      <stop offset="100%" stop-color="#00C3FF" stop-opacity="0" />
    </linearGradient>

    <!-- Gold Edge Trim Gradient -->
    <linearGradient id="goldTrimGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#D4AF37" />
      <stop offset="50%" stop-color="#FFC857" />
      <stop offset="100%" stop-color="#D4AF37" />
    </linearGradient>
  </defs>

  <!-- [Back Flap and Tab] -->
  <path d="M 40,90 C 40,75 55,65 70,65 L 180,65 C 195,65 205,80 215,95 L 235,120 L 442,120 C 457,120 472,135 472,150 L 472,410 C 472,425 457,440 442,440 L 70,440 C 55,440 40,425 40,410 Z" 
        fill="url(#backFlapGrad)" stroke="#1E6BFF" stroke-width="3" />

  <!-- [Front Flap with shorter rounded profile] -->
  <path d="M 40,150 C 40,135 55,125 70,125 L 442,125 C 457,125 472,135 472,150 L 472,410 C 472,425 457,440 442,440 L 70,440 C 55,440 40,425 40,410 Z" 
        fill="url(#frontFlapGrad)" stroke="#1E6BFF" stroke-width="2" />

  <!-- [Thin Gold Border Accent Trim on the top edge of the front flap] -->
  <path d="M 70,125 L 442,125" stroke="url(#goldTrimGrad)" stroke-width="2.5" stroke-linecap="round" />

  <!-- [Electric Blue Glowing highlight line at the bottom] -->
  <path d="M 70,434 L 442,434" stroke="url(#baseGlowGrad)" stroke-width="4.5" stroke-linecap="round" />

  <!-- [The exact High-Fidelity Sovereign Gold-and-Blue Crest centered in the middle of the flap] -->
  <image xlink:href="data:image/png;base64,{b64_str}" width="220" height="220" x="146" y="165"/>
  
  <!-- [Overlay a glowing gold house/home vector badge in the lower-right area of the folder flap] -->
  <g transform="translate(300, 270) scale(0.6)">
    <!-- Backing shield badge -->
    <path d="M 60,15 C 80,15 90,25 90,45 C 90,75 60,105 60,110 C 60,105 30,75 30,45 C 30,25 40,15 60,15 Z" fill="#05070D" stroke="#D4AF37" stroke-width="3" />
    <!-- Golden House outline -->
    <path d="M 60,30 L 75,45 L 70,45 L 70,70 L 50,70 L 50,45 L 45,45 Z" fill="none" stroke="#FFC857" stroke-width="3.5" stroke-linejoin="round" />
    <!-- Electric blue house heart -->
    <circle cx="60" cy="53" r="3.5" fill="#00C3FF" />
  </g>
</svg>
"""

    targets = [
        ("HomeAurelia-Theme-Pack/09-Icons/scalable/places/folder-home.svg", start_here_svg), # Wait, let's also write start_here_svg directly to folder-home as shown in Sheet 1!
        ("HomeAurelia-Theme-Pack/09-Icons/scalable/places/folder.svg", folder_svg),
        ("HomeAurelia-Theme-Pack/09-Icons/scalable/apps/start-here-kde.svg", start_here_svg),
        ("os/phoenix-os/live-build/config/includes.chroot/usr/share/icons/home-aurelia/scalable/apps/start-here-kde.svg", start_here_svg),
        ("os/phoenix-os/live-build/config/includes.chroot/usr/share/icons/home-aurelia/scalable/places/folder.svg", folder_svg),
        ("os/phoenix-os/live-build/config/includes.chroot/usr/share/icons/home-aurelia/scalable/places/folder-home.svg", folder_home_svg),
        ("os/phoenix-os/live-build/config/includes.chroot/usr/share/home-aurelia-theme-pack/09-Icons/scalable/apps/start-here-kde.svg", start_here_svg),
        ("os/phoenix-os/live-build/config/includes.chroot/usr/share/home-aurelia-theme-pack/09-Icons/scalable/places/folder.svg", folder_svg),
        ("os/phoenix-os/live-build/config/includes.chroot/usr/share/home-aurelia-theme-pack/09-Icons/scalable/places/folder-home.svg", folder_home_svg)
    ]
    
    # Let's write them cleanly to both chroot and pack directories!
    # Wait, in Sheet 1, the icon named "Home" is exactly the circular gold-blue shield.
    # But folder-home can be the folder shape with the gold house badge overlayed, or it can be the circular shield directly!
    # To be extremely thorough, let's write folder_home_svg (with the navy folder + crest + home house badge) to places/folder-home.svg,
    # and write start_here_svg to apps/start-here-kde.svg!
    
    actual_targets = [
        ("HomeAurelia-Theme-Pack/09-Icons/scalable/apps/start-here-kde.svg", start_here_svg),
        ("HomeAurelia-Theme-Pack/09-Icons/scalable/places/folder.svg", folder_svg),
        ("HomeAurelia-Theme-Pack/09-Icons/scalable/places/folder-home.svg", folder_home_svg),
        
        ("os/phoenix-os/live-build/config/includes.chroot/usr/share/icons/home-aurelia/scalable/apps/start-here-kde.svg", start_here_svg),
        ("os/phoenix-os/live-build/config/includes.chroot/usr/share/icons/home-aurelia/scalable/places/folder.svg", folder_svg),
        ("os/phoenix-os/live-build/config/includes.chroot/usr/share/icons/home-aurelia/scalable/places/folder-home.svg", folder_home_svg),
        
        ("os/phoenix-os/live-build/config/includes.chroot/usr/share/home-aurelia-theme-pack/09-Icons/scalable/apps/start-here-kde.svg", start_here_svg),
        ("os/phoenix-os/live-build/config/includes.chroot/usr/share/home-aurelia-theme-pack/09-Icons/scalable/places/folder.svg", folder_svg),
        ("os/phoenix-os/live-build/config/includes.chroot/usr/share/home-aurelia-theme-pack/09-Icons/scalable/places/folder-home.svg", folder_home_svg)
    ]
    
    for path, content in actual_targets:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        print(f"✅ Generated high-fidelity visual matching design sheets at: {path}")

if __name__ == "__main__":
    embed_logo()
