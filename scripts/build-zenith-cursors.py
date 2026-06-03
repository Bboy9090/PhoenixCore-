import os
import shutil

repo_editions = "/Users/bj90-m1/PhoenixCore-/editions"

# Mapping from edition name to the edition directory
editions = {
    "Aurelia": ("home", "#a78bfa", "#fbbf24"),      # Violet / Gold
    "Arcwyre": ("arcwyre", "#dc2626", "#22c55e"),    # Crimson / Cyber Green
    "Thundergod": ("thunder-god", "#eab308", "#0ea5e9"), # Electric Gold / Blue
    "Native": ("blue-phoenix", "#38bdf8", "#ef4444")     # Ancestral Blue / Red
}

def generate_svg_cursor(primary, accent):
    """
    Generates a sleek, geometric Zenith cursor SVG.
    It features a sharp arrowhead with a glowing inner core matching the edition's palette.
    """
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="48" height="48" viewBox="0 0 48 48" version="1.1" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <!-- Outer Glass Blur -->
    <filter id="glass-glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="1.5" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
    
    <!-- Core Energy Gradient -->
    <linearGradient id="core-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{primary}" />
      <stop offset="100%" stop-color="{accent}" />
    </linearGradient>
  </defs>

  <!-- Shadow -->
  <polygon points="12,12 12,38 20,30 26,38 30,34 24,26 34,26" fill="rgba(0,0,0,0.3)" filter="blur(2px)" transform="translate(1, 2)"/>
  
  <!-- Outer Glass Shell -->
  <polygon points="12,12 12,38 20,30 26,38 30,34 24,26 34,26" fill="rgba(255,255,255,0.1)" stroke="rgba(255,255,255,0.5)" stroke-width="1.5" filter="url(#glass-glow)" />

  <!-- Inner Glowing Core -->
  <polygon points="14,16 14,33 20,27 25,34 27,32 22,25 30,25" fill="url(#core-grad)" opacity="0.8" />
  
  <!-- Edge Highlight -->
  <polyline points="12,12 12,38 20,30" fill="none" stroke="rgba(255,255,255,0.8)" stroke-width="1" />
</svg>
"""
    return svg

def generate_index_theme(name):
    return f"""[Icon Theme]
Name=Zenith-{name}
Comment=Volumetric Zenith Edition Cursors for {name}
Inherits=core
"""

def main():
    for name, (folder, primary, accent) in editions.items():
        theme_dir = os.path.join(repo_editions, folder, "custom_icons", f"Zenith-{name}")
        cursor_dir = os.path.join(theme_dir, "cursors")
        
        if not os.path.exists(cursor_dir):
            os.makedirs(cursor_dir)
            
        # Write index.theme
        with open(os.path.join(theme_dir, "index.theme"), "w") as f:
            f.write(generate_index_theme(name))
            
        # Write cursor SVGs
        # In a real build, we'd compile these to X11 cursors using xcursorgen.
        # For now, we will drop the SVGs into the folder to serve as the raw Zenith pointer assets.
        pointers = ["left_ptr.svg", "arrow.svg", "default.svg", "pointer.svg"]
        svg_content = generate_svg_cursor(primary, accent)
        
        for p in pointers:
            with open(os.path.join(cursor_dir, p), "w") as f:
                f.write(svg_content)
                
        print(f"✅ Generated Zenith Cursor Pack for {name} in {folder}/custom_icons/Zenith-{name}")

if __name__ == "__main__":
    main()
