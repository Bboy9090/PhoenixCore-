import os

def create_vector_icons():
    # ------------------ DEFINE COLOR AND STYLE TEMPLATES ------------------
    GOLD_DEF = """
    <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFC857" />
      <stop offset="50%" stop-color="#D4AF37" />
      <stop offset="100%" stop-color="#8A6600" />
    </linearGradient>
    <linearGradient id="goldTrim" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#D4AF37" />
      <stop offset="50%" stop-color="#FFC857" />
      <stop offset="100%" stop-color="#D4AF37" />
    </linearGradient>
    """
    
    BLUE_DEF = """
    <linearGradient id="blueGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#1E6BFF" />
      <stop offset="100%" stop-color="#00C3FF" />
    </linearGradient>
    <linearGradient id="folderGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0F1E3A" />
      <stop offset="100%" stop-color="#081426" />
    </linearGradient>
    <linearGradient id="frontFlapGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#1A2E5C" />
      <stop offset="40%" stop-color="#0F1E3A" />
      <stop offset="100%" stop-color="#070D1A" />
    </linearGradient>
    <radialGradient id="electricGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#00C3FF" stop-opacity="0.5" />
      <stop offset="100%" stop-color="#1E6BFF" stop-opacity="0" />
    </radialGradient>
    <linearGradient id="baseGlow" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00C3FF" stop-opacity="0" />
      <stop offset="25%" stop-color="#00C3FF" stop-opacity="1" />
      <stop offset="75%" stop-color="#00C3FF" stop-opacity="1" />
      <stop offset="100%" stop-color="#00C3FF" stop-opacity="0" />
    </linearGradient>
    """
    
    # ------------------ BASE SVGS GENERATORS ------------------
    
    def get_shield_svg(content):
        return f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512" version="1.1">
  <defs>
    {GOLD_DEF}
    {BLUE_DEF}
  </defs>
  <!-- Background Glow -->
  <circle cx="256" cy="256" r="230" fill="url(#electricGlow)" />
  <!-- Outer double ring -->
  <circle cx="256" cy="256" r="200" fill="none" stroke="url(#goldGrad)" stroke-width="6" />
  <circle cx="256" cy="256" r="188" fill="none" stroke="url(#goldGrad)" stroke-width="2" stroke-opacity="0.6" />
  <!-- Shield base -->
  <path d="M 256,90 C 315,90 350,115 350,185 C 350,265 256,370 256,390 C 256,370 162,265 162,185 C 162,115 197,90 256,90 Z" 
        fill="#05070D" stroke="url(#goldGrad)" stroke-width="4.5" />
  <!-- Inner Blue core -->
  <path d="M 256,105 C 300,105 330,125 330,180 C 330,245 256,340 256,355 C 256,340 182,245 182,180 C 182,125 212,105 256,105 Z" 
        fill="url(#blueGrad)" fill-opacity="0.15" stroke="#00C3FF" stroke-width="1.5" stroke-dasharray="4,2" />
  <!-- Content overlay -->
  {content}
</svg>"""

    def get_folder_svg(content):
        return f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512" version="1.1">
  <defs>
    {GOLD_DEF}
    {BLUE_DEF}
  </defs>
  <!-- Back Flap -->
  <path d="M 40,90 C 40,75 55,65 70,65 L 180,65 C 195,65 205,80 215,95 L 235,120 L 442,120 C 457,120 472,135 472,150 L 472,410 C 472,425 457,440 442,440 L 70,440 C 55,440 40,425 40,410 Z" 
        fill="url(#folderGrad)" stroke="#1E6BFF" stroke-width="3" />
  <!-- Front Flap -->
  <path d="M 40,150 C 40,135 55,125 70,125 L 442,125 C 457,125 472,135 472,150 L 472,410 C 472,425 457,440 442,440 L 70,440 C 55,440 40,425 40,410 Z" 
        fill="url(#frontFlapGrad)" stroke="#1E6BFF" stroke-width="2" />
  <!-- Gold Top Trim -->
  <path d="M 70,125 L 442,125" stroke="url(#goldTrim)" stroke-width="2.5" stroke-linecap="round" />
  <!-- Blue Glow Base -->
  <path d="M 70,434 L 442,434" stroke="url(#baseGlow)" stroke-width="4.5" stroke-linecap="round" />
  <!-- Content overlay -->
  {content}
</svg>"""

    # ------------------ EMBLEM AND CONTENT GRAPHICS ------------------
    
    # 1. Circular Aurelia Crest (Pure Gold-Blue Soaring Phoenix - extremely detailed)
    crest_content = """
    <g transform="translate(0, 15)">
      <!-- Phoenix outline and soaring wings -->
      <path d="M 256,230 C 220,180 160,160 110,180 C 140,210 170,230 200,240 C 170,245 140,240 120,225 C 145,255 180,265 210,268 C 180,275 160,275 140,265 C 170,290 210,290 230,282 Z" fill="url(#goldGrad)" />
      <path d="M 256,230 C 292,180 352,160 402,180 C 372,210 342,230 312,240 C 342,245 372,240 392,225 C 367,255 332,265 302,268 C 332,275 352,275 372,265 C 342,290 302,290 282,282 Z" fill="url(#goldGrad)" />
      <!-- Beak / Head / Crown -->
      <path d="M 256,120 L 263,140 L 260,150 L 256,145 L 252,150 L 249,140 Z" fill="url(#goldGrad)" />
      <path d="M 256,110 C 265,115 272,125 275,135 M 256,110 C 247,115 240,125 237,135" stroke="url(#goldGrad)" stroke-width="2.5" fill="none" stroke-linecap="round" />
      <!-- Torso blue sapphire gem -->
      <path d="M 256,165 L 274,195 L 256,235 L 238,195 Z" fill="#00C3FF" stroke="#F7F7FF" stroke-width="2" />
      <circle cx="256" cy="195" r="3.5" fill="#F7F7FF" />
      <!-- Tails -->
      <path d="M 256,245 C 262,280 268,320 256,350 C 244,320 250,280 256,245 Z" fill="url(#goldGrad)" />
      <path d="M 245,245 C 230,275 220,310 205,335 C 215,310 230,280 245,245 Z" fill="url(#goldGrad)" opacity="0.8" />
      <path d="M 267,245 C 282,275 292,310 307,335 C 297,310 282,280 267,245 Z" fill="url(#goldGrad)" opacity="0.8" />
    </g>
    """
    
    # 2. Documents (Filing sheet with golden phoenix print)
    docs_content = """
    <g transform="translate(136, 150)">
      <!-- Sheet background -->
      <rect x="20" y="20" width="200" height="240" rx="10" fill="#05070D" stroke="url(#goldGrad)" stroke-width="3" />
      <!-- Text lines -->
      <line x1="45" y1="60" x2="195" y2="60" stroke="#00C3FF" stroke-width="4.5" stroke-linecap="round" />
      <line x1="45" y1="90" x2="195" y2="90" stroke="#00C3FF" stroke-width="4.5" stroke-linecap="round" />
      <line x1="45" y1="120" x2="160" y2="120" stroke="#00C3FF" stroke-width="4.5" stroke-linecap="round" />
      <line x1="45" y1="150" x2="130" y2="150" stroke="#00C3FF" stroke-width="4.5" stroke-linecap="round" />
      <!-- Golden crest in the corner -->
      <path d="M 170,180 C 150,180 140,195 140,215 C 140,240 170,250 170,250 C 170,250 200,240 200,215 C 200,195 190,180 170,180 Z" fill="none" stroke="url(#goldGrad)" stroke-width="2" />
    </g>
    """
    
    # 3. Downloads (Glossy down arrow)
    downloads_content = """
    <g transform="translate(0, 0)">
      <!-- Glossy Arrow pointing down -->
      <path d="M 256,140 L 256,310 M 256,310 L 200,250 M 256,310 L 312,250" stroke="url(#blueGrad)" stroke-width="16" stroke-linecap="round" stroke-linejoin="round" />
      <!-- Gold bottom bar -->
      <line x1="180" y1="340" x2="332" y2="340" stroke="url(#goldGrad)" stroke-width="8" stroke-linecap="round" />
    </g>
    """
    
    # 4. Music (Dual eighth notes)
    music_content = """
    <g transform="translate(136, 150)">
      <!-- Double eighth note -->
      <path d="M 90,60 L 170,40 L 170,180 L 140,180 C 120,180 110,190 110,205 C 110,220 125,230 145,230 C 165,230 175,215 175,200 L 175,80 L 95,100 L 95,200 L 65,200 C 45,200 35,210 35,225 C 35,240 50,250 70,250 C 90,250 100,235 100,220 L 100,60 Z" 
            fill="url(#blueGrad)" stroke="url(#goldGrad)" stroke-width="2.5" />
    </g>
    """
    
    # 5. Pictures (Mountain crest frame)
    pictures_content = """
    <g transform="translate(136, 150)">
      <!-- Picture frame -->
      <rect x="20" y="30" width="200" height="200" rx="8" fill="#05070D" stroke="url(#goldGrad)" stroke-width="3" />
      <!-- Glowing Blue mountains -->
      <path d="M 30,210 L 100,100 L 150,170 L 190,110 L 210,210 Z" fill="url(#blueGrad)" fill-opacity="0.3" stroke="#00C3FF" stroke-width="3" stroke-linejoin="round" />
      <!-- Sun of gold -->
      <circle cx="170" cy="80" r="20" fill="url(#goldGrad)" />
    </g>
    """
    
    # 6. Videos (Play shield frame)
    videos_content = """
    <g transform="translate(136, 150)">
      <!-- Outer Frame -->
      <rect x="20" y="30" width="200" height="200" rx="8" fill="#05070D" stroke="url(#goldGrad)" stroke-width="3" />
      <!-- Inside play triangle -->
      <path d="M 90,90 L 160,130 L 90,170 Z" fill="url(#blueGrad)" stroke="url(#goldGrad)" stroke-width="3" stroke-linejoin="round" />
      <!-- Top and bottom film strip indicators -->
      <rect x="35" y="45" width="20" height="15" fill="#1E6BFF" opacity="0.6" />
      <rect x="75" y="45" width="20" height="15" fill="#1E6BFF" opacity="0.6" />
      <rect x="115" y="45" width="20" height="15" fill="#1E6BFF" opacity="0.6" />
      <rect x="155" y="45" width="20" height="15" fill="#1E6BFF" opacity="0.6" />
    </g>
    """
    
    # 7. Trash (Waste bin)
    trash_content = """
    <g transform="translate(136, 140)">
      <!-- Trash Can base -->
      <path d="M 40,60 L 60,240 C 60,250 70,260 80,260 L 160,260 C 170,260 180,250 180,240 L 200,60 Z" fill="#081426" stroke="url(#blueGrad)" stroke-width="4.5" />
      <!-- Lid -->
      <rect x="25" y="40" width="190" height="20" rx="5" fill="#0F1E3A" stroke="url(#goldGrad)" stroke-width="3" />
      <rect x="90" y="22" width="60" height="20" rx="3" fill="none" stroke="url(#goldGrad)" stroke-width="3" />
      <!-- Vertical rib lines -->
      <line x1="85" y1="80" x2="95" y2="230" stroke="url(#goldGrad)" stroke-width="2.5" />
      <line x1="120" y1="80" x2="120" y2="230" stroke="url(#goldGrad)" stroke-width="2.5" />
      <line x1="155" y1="80" x2="145" y2="230" stroke="url(#goldGrad)" stroke-width="2.5" />
    </g>
    """
    
    # 8. Settings (Premium Gear with Crest in center)
    settings_content = """
    <g transform="translate(0, 0)">
      <!-- Gear wheel body -->
      <path d="M 256,120 L 256,145 M 256,367 L 256,392 M 120,256 L 145,256 M 367,256 L 392,256 M 160,160 L 178,178 M 334,334 L 352,352 M 160,334 L 178,316 M 334,160 L 352,178" 
            stroke="url(#goldGrad)" stroke-width="22" stroke-linecap="round" />
      <!-- Gear Ring -->
      <circle cx="256" cy="256" r="110" fill="none" stroke="url(#goldGrad)" stroke-width="12" />
      <circle cx="256" cy="256" r="85" fill="#05070D" stroke="#00C3FF" stroke-width="3" />
      <!-- Inner settings indicator (blue lightning icon) -->
      <path d="M 256,206 C 228,206 206,228 206,256 C 206,284 228,306 256,306 C 284,306 306,284 306,256" fill="none" stroke="url(#blueGrad)" stroke-width="4.5" />
      <polygon points="256,226 266,256 246,256" fill="#D4AF37" />
    </g>
    """
    
    # 9. Terminal (Command Prompt with prompt caret)
    terminal_content = """
    <g transform="translate(136, 150)">
      <!-- Terminal Box -->
      <rect x="15" y="30" width="210" height="190" rx="8" fill="#05070D" stroke="url(#goldGrad)" stroke-width="3" />
      <!-- Prompt symbols -->
      <path d="M 40,80 L 80,105 L 40,130" fill="none" stroke="#00C3FF" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" />
      <line x1="95" y1="130" x2="160" y2="130" stroke="url(#goldGrad)" stroke-width="6" stroke-linecap="round" />
    </g>
    """
    
    # 10. Browser (Glowing Globe)
    browser_content = """
    <g transform="translate(0, 0)">
      <!-- Globe outline -->
      <circle cx="256" cy="256" r="95" fill="none" stroke="url(#blueGrad)" stroke-width="6" />
      <!-- Grid lines -->
      <path d="M 161,256 C 161,210 203,161 256,161 C 309,161 351,210 351,256 C 351,302 309,351 256,351 C 203,351 161,302 161,256 Z" fill="none" stroke="#00C3FF" stroke-width="2.5" />
      <path d="M 216,256 C 216,190 234,161 256,161 C 278,161 296,190 296,256 C 296,322 278,351 256,351 C 234,351 216,322 216,256 Z" fill="none" stroke="#00C3FF" stroke-width="2.5" />
      <line x1="161" y1="256" x2="351" y2="256" stroke="url(#goldGrad)" stroke-width="4.5" />
      <path d="M 183,196 L 329,196 M 183,316 L 329,316" stroke="#00C3FF" stroke-width="2" />
    </g>
    """
    
    # 11. Mail (Double Envelope)
    mail_content = """
    <g transform="translate(136, 160)">
      <!-- Mail envelope -->
      <rect x="15" y="30" width="210" height="150" rx="8" fill="#081426" stroke="url(#goldGrad)" stroke-width="3" />
      <!-- Chevron indicator -->
      <path d="M 15,30 L 120,115 L 225,30" fill="none" stroke="url(#blueGrad)" stroke-width="4.5" stroke-linejoin="round" />
    </g>
    """
    
    # 12. Calendar ("25" Desk Calendar)
    calendar_content = """
    <g transform="translate(136, 140)">
      <!-- Calendar Backing -->
      <rect x="25" y="40" width="190" height="200" rx="10" fill="#0F1E3A" stroke="url(#blueGrad)" stroke-width="3.5" />
      <!-- Red/Gold header pad -->
      <path d="M 25,40 C 25,30 35,20 45,20 L 195,20 C 205,20 215,30 215,40 L 215,80 L 25,80 Z" fill="url(#goldGrad)" />
      <!-- Rings -->
      <circle cx="65" cy="20" r="10" fill="none" stroke="#F7F7FF" stroke-width="3.5" />
      <circle cx="120" cy="20" r="10" fill="none" stroke="#F7F7FF" stroke-width="3.5" />
      <circle cx="175" cy="20" r="10" fill="none" stroke="#F7F7FF" stroke-width="3.5" />
      <!-- Number 25 -->
      <text x="120" y="195" font-family="'Inter', sans-serif" font-size="95" font-weight="900" fill="#F7F7FF" text-anchor="middle">25</text>
    </g>
    """
    
    # 13. Network (Wi-Fi Wave Concentric Circles)
    network_content = """
    <g transform="translate(0, 0)">
      <!-- Wi-Fi Concentric waves -->
      <circle cx="256" cy="326" r="18" fill="url(#goldGrad)" />
      <path d="M 210,280 C 235,255 277,255 302,280" fill="none" stroke="url(#blueGrad)" stroke-width="6" stroke-linecap="round" />
      <path d="M 174,244 C 219,199 293,199 338,244" fill="none" stroke="url(#blueGrad)" stroke-width="8" stroke-linecap="round" />
      <path d="M 138,208 C 203,143 309,143 374,208" fill="none" stroke="url(#goldGrad)" stroke-width="9" stroke-linecap="round" />
    </g>
    """
    
    # 14. Bluetooth (Circular Bluetooth Rune)
    bluetooth_content = """
    <g transform="translate(0, 0)">
      <!-- Rune path -->
      <path d="M 256,150 L 256,362 M 256,150 L 312,206 L 200,318 M 256,362 L 312,306 L 200,194" 
            fill="none" stroke="url(#goldGrad)" stroke-width="8.5" stroke-linecap="round" stroke-linejoin="round" />
    </g>
    """
    
    # 15. User (Avatar head and shoulders)
    user_content = """
    <g transform="translate(0, -10)">
      <!-- Human head -->
      <circle cx="256" cy="180" r="42" fill="url(#blueGrad)" stroke="url(#goldGrad)" stroke-width="2.5" />
      <!-- Shoulders -->
      <path d="M 176,320 C 176,260 212,240 256,240 C 300,240 336,260 336,320 Z" fill="url(#blueGrad)" stroke="url(#goldGrad)" stroke-width="2.5" />
    </g>
    """
    
    # 16. Power (Glowing Power Ring)
    power_content = """
    <g transform="translate(0, 0)">
      <!-- Power symbol -->
      <path d="M 216,186 C 182,216 182,270 216,300 C 250,330 304,330 338,300 C 372,270 372,216 338,186" fill="none" stroke="url(#blueGrad)" stroke-width="9" stroke-linecap="round" />
      <line x1="277" y1="130" x2="277" y2="230" stroke="url(#goldGrad)" stroke-width="9.5" stroke-linecap="round" />
    </g>
    """
    
    # 17. Software (Package box with gold lid)
    software_content = """
    <g transform="translate(136, 140)">
      <!-- 3D Box front -->
      <polygon points="25,90 120,40 215,90 215,220 120,265 25,220" fill="url(#folderGrad)" stroke="url(#blueGrad)" stroke-width="3" />
      <!-- Gold Lid top -->
      <polygon points="25,90 120,40 215,90 120,135" fill="url(#goldGrad)" />
      <!-- Inside gold markings -->
      <path d="M 120,135 L 120,265 M 25,90 L 120,135 L 215,90" fill="none" stroke="#05070D" stroke-width="2.5" />
    </g>
    """
    
    # 18. Help (Glossy circular question mark)
    help_content = """
    <g transform="translate(0, -10)">
      <!-- Question mark text shape -->
      <text x="256" y="285" font-family="'Cinzel', 'Georgia', serif" font-size="160" font-weight="bold" fill="url(#goldGrad)" text-anchor="middle">?</text>
    </g>
    """
    
    # 19. Drive (Hard disk rack drive)
    drive_content = """
    <g transform="translate(136, 160)">
      <!-- Server disk case -->
      <rect x="15" y="30" width="210" height="150" rx="8" fill="#081426" stroke="url(#goldGrad)" stroke-width="4.5" />
      <!-- Disk slot blue glow -->
      <rect x="35" y="80" width="170" height="20" rx="4" fill="#05070D" stroke="#00C3FF" stroke-width="2" />
      <line x1="45" y1="90" x2="150" y2="90" stroke="#00C3FF" stroke-width="3.5" stroke-linecap="round" />
      <!-- Status lights -->
      <circle cx="175" cy="90" r="4" fill="#00C3FF" />
      <circle cx="190" cy="90" r="4" fill="#FFC857" />
    </g>
    """
    
    # 20. System (Microchip layout)
    system_content = """
    <g transform="translate(136, 140)">
      <!-- Microchip processor base -->
      <rect x="35" y="35" width="170" height="170" rx="14" fill="#05070D" stroke="url(#goldGrad)" stroke-width="4.5" />
      <!-- Gold pins on sides -->
      <!-- Left side pins -->
      <rect x="15" y="60" width="20" height="8" rx="2" fill="url(#goldGrad)" />
      <rect x="15" y="90" width="20" height="8" rx="2" fill="url(#goldGrad)" />
      <rect x="15" y="120" width="20" height="8" rx="2" fill="url(#goldGrad)" />
      <rect x="15" y="150" width="20" height="8" rx="2" fill="url(#goldGrad)" />
      <!-- Right side pins -->
      <rect x="205" y="60" width="20" height="8" rx="2" fill="url(#goldGrad)" />
      <rect x="205" y="90" width="20" height="8" rx="2" fill="url(#goldGrad)" />
      <rect x="205" y="120" width="20" height="8" rx="2" fill="url(#goldGrad)" />
      <rect x="205" y="150" width="20" height="8" rx="2" fill="url(#goldGrad)" />
      <!-- Top/bottom pins -->
      <rect x="60" y="15" width="8" height="20" rx="2" fill="url(#goldGrad)" />
      <rect x="90" y="15" width="8" height="20" rx="2" fill="url(#goldGrad)" />
      <rect x="120" y="15" width="8" height="20" rx="2" fill="url(#goldGrad)" />
      <rect x="150" y="15" width="8" height="20" rx="2" fill="url(#goldGrad)" />
      <rect x="60" y="205" width="8" height="20" rx="2" fill="url(#goldGrad)" />
      <rect x="90" y="205" width="8" height="20" rx="2" fill="url(#goldGrad)" />
      <rect x="120" y="205" width="8" height="20" rx="2" fill="url(#goldGrad)" />
      <rect x="150" y="205" width="8" height="20" rx="2" fill="url(#goldGrad)" />
      <!-- Blue core crest -->
      <circle cx="120" cy="120" r="30" fill="url(#blueGrad)" stroke="url(#goldGrad)" stroke-width="2" />
      <polygon points="120,105 125,120 115,120" fill="#F7F7FF" />
    </g>
    """
    
    # 21. Firewall (Defense Gate shield)
    firewall_content = """
    <g transform="translate(0, 0)">
      <!-- Fortress castle top overlay -->
      <path d="M 210,180 L 210,230 L 230,230 L 230,200 L 250,200 L 250,230 L 270,230 L 270,200 L 290,200 L 290,230 L 310,230 L 310,180 Z" fill="url(#blueGrad)" stroke="url(#goldGrad)" stroke-width="3" />
      <!-- Wall body grid -->
      <rect x="210" y="230" width="100" height="60" fill="url(#blueGrad)" fill-opacity="0.3" stroke="url(#goldGrad)" stroke-width="3" />
      <line x1="210" y1="260" x2="310" y2="260" stroke="url(#goldGrad)" stroke-width="2" />
      <line x1="243" y1="230" x2="243" y2="290" stroke="url(#goldGrad)" stroke-width="2" />
      <line x1="277" y1="230" x2="277" y2="290" stroke="url(#goldGrad)" stroke-width="2" />
    </g>
    """
    
    # 22. Calculator (Calendar/Calculator grid)
    calculator_content = """
    <g transform="translate(136, 140)">
      <!-- Calculator casing -->
      <rect x="25" y="30" width="190" height="220" rx="8" fill="#0F1E3A" stroke="url(#blueGrad)" stroke-width="4.5" />
      <!-- Screen -->
      <rect x="40" y="50" width="160" height="40" rx="4" fill="#05070D" stroke="url(#goldGrad)" stroke-width="2" />
      <line x1="50" y1="70" x2="120" y2="70" stroke="#00C3FF" stroke-width="4.5" stroke-linecap="round" />
      <!-- Buttons grid -->
      <circle cx="65" cy="120" r="12" fill="url(#goldGrad)" />
      <circle cx="120" cy="120" r="12" fill="url(#goldGrad)" />
      <circle cx="175" cy="120" r="12" fill="url(#blueGrad)" />
      <circle cx="65" cy="170" r="12" fill="url(#goldGrad)" />
      <circle cx="120" cy="170" r="12" fill="url(#goldGrad)" />
      <circle cx="175" cy="170" r="12" fill="url(#blueGrad)" />
      <circle cx="65" cy="220" r="12" fill="url(#goldGrad)" />
      <circle cx="120" cy="220" r="12" fill="url(#goldGrad)" />
      <circle cx="175" cy="220" r="12" fill="url(#blueGrad)" />
    </g>
    """

    # 23. Text Editor (Notebook and Gold feather stylus)
    text_editor_content = """
    <g transform="translate(136, 140)">
      <!-- Pad background -->
      <rect x="20" y="40" width="180" height="210" rx="6" fill="#0F1E3A" stroke="url(#blueGrad)" stroke-width="3" />
      <line x1="45" y1="80" x2="150" y2="80" stroke="#00C3FF" stroke-width="3.5" />
      <line x1="45" y1="120" x2="130" y2="120" stroke="#00C3FF" stroke-width="3.5" />
      <line x1="45" y1="160" x2="110" y2="160" stroke="#00C3FF" stroke-width="3.5" />
      <!-- Golden feather writing -->
      <path d="M 180,50 C 160,80 130,130 110,180 C 105,190 100,205 95,215 M 180,50 C 170,80 150,110 135,130" 
            fill="none" stroke="url(#goldGrad)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
    </g>
    """

    # ------------------ GENERATION MAP ------------------
    icon_map = {
        # Shield base icons
        "scalable/apps/start-here-kde.svg": get_shield_svg(crest_content),
        "scalable/places/folder-home.svg": get_shield_svg(crest_content), # Shield directly matches Home from Sheet 1
        "scalable/places/downloads.svg": get_shield_svg(downloads_content),
        "scalable/places/settings.svg": get_shield_svg(settings_content),
        "scalable/apps/system-settings.svg": get_shield_svg(settings_content),
        "scalable/apps/preferences-system.svg": get_shield_svg(settings_content),
        "scalable/apps/internet-web-browser.svg": get_shield_svg(browser_content),
        "scalable/apps/bluetooth.svg": get_shield_svg(bluetooth_content),
        "scalable/apps/user.svg": get_shield_svg(user_content),
        "scalable/apps/system-shutdown.svg": get_shield_svg(power_content),
        "scalable/apps/system-reboot.svg": get_shield_svg(power_content),
        "scalable/apps/dialog-question.svg": get_shield_svg(help_content),
        "scalable/apps/network-wireless.svg": get_shield_svg(network_content),
        "scalable/apps/network-workgroup.svg": get_shield_svg(network_content),
        "scalable/apps/network-firewall.svg": get_shield_svg(firewall_content),

        # Folder base icons
        "scalable/places/folder.svg": get_folder_svg(crest_content),
        "scalable/places/folder-documents.svg": get_folder_svg(docs_content),
        "scalable/places/folder-downloads.svg": get_folder_svg(downloads_content),
        "scalable/places/folder-music.svg": get_folder_svg(music_content),
        "scalable/places/folder-pictures.svg": get_folder_svg(pictures_content),
        "scalable/places/folder-videos.svg": get_folder_svg(videos_content),

        # Custom shapes
        "scalable/places/user-trash.svg": get_shield_svg(trash_content),
        "scalable/places/user-trash-full.svg": get_shield_svg(trash_content),
        "scalable/apps/utilities-terminal.svg": get_shield_svg(terminal_content),
        "scalable/apps/internet-mail.svg": get_shield_svg(mail_content),
        "scalable/apps/office-calendar.svg": get_shield_svg(calendar_content),
        "scalable/apps/system-software-install.svg": get_shield_svg(software_content),
        "scalable/devices/drive-harddisk.svg": get_shield_svg(drive_content),
        "scalable/devices/drive-removable-media.svg": get_shield_svg(drive_content),
        "scalable/devices/computer.svg": get_shield_svg(system_content),
        "scalable/apps/accessories-calculator.svg": get_shield_svg(calculator_content),
        "scalable/apps/accessories-text-editor.svg": get_shield_svg(text_editor_content),
    }

    # Staging roots to copy to
    targets = [
        "HomeAurelia-Theme-Pack/09-Icons/",
        "os/phoenix-os/live-build/config/includes.chroot/usr/share/icons/home-aurelia/",
        "os/phoenix-os/live-build/config/includes.chroot/usr/share/home-aurelia-theme-pack/09-Icons/"
    ]

    for root_dir in targets:
        for rel_path, svg_data in icon_map.items():
            full_path = os.path.join(root_dir, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w") as f:
                f.write(svg_data)
            # Make sure all sizes folders have matching copies so they load flawlessly
            # Copy scalable SVG to standard sized folders as fallback targets
            # (Settings, places folders etc. are copied to relevant sizing hierarchies)
            if "places/" in rel_path:
                for size in ["32x32", "48x48", "64x64", "128x128", "256x256", "512x512"]:
                    size_path = os.path.join(root_dir, size, "places", os.path.basename(rel_path))
                    os.makedirs(os.path.dirname(size_path), exist_ok=True)
                    with open(size_path, "w") as f:
                        f.write(svg_data)
            elif "apps/" in rel_path:
                for size in ["32x32", "48x48", "64x64", "128x128", "256x256", "512x512"]:
                    size_path = os.path.join(root_dir, size, "apps", os.path.basename(rel_path))
                    os.makedirs(os.path.dirname(size_path), exist_ok=True)
                    with open(size_path, "w") as f:
                        f.write(svg_data)
            elif "devices/" in rel_path:
                for size in ["32x32", "48x48", "64x64", "128x128", "256x256", "512x512"]:
                    size_path = os.path.join(root_dir, size, "devices", os.path.basename(rel_path))
                    os.makedirs(os.path.dirname(size_path), exist_ok=True)
                    with open(size_path, "w") as f:
                        f.write(svg_data)
            
    print(f"🎉 MATHEMATICALLY GENERATED 32+ HIGH-FIDELITY VECTOR ICONS SUCCESSFULLY!")

if __name__ == "__main__":
    create_vector_icons()
