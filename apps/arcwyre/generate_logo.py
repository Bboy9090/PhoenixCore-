import os

SVG_DIR = "/Users/bj90-m1/PhoenixCore-/apps/arcwyre/arcwyre/icons"
os.makedirs(SVG_DIR, exist_ok=True)

arcwyre_logo = '''<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#00D0E5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <!-- Glowing Hexagon Shield (Protection/System) -->
    <path d="M12 2L3 7l0 10 9 5 9-5 0-10L12 2Z" fill="rgba(0,208,229,0.15)" stroke="#00D0E5"></path>
    <!-- Lightning Bolt (Revival/Power/Boot) -->
    <polygon points="13 6 7 14 12 14 11 18 17 10 12 10 13 6" fill="#00D0E5" stroke="none"></polygon>
</svg>'''

with open(os.path.join(SVG_DIR, "arcwyre-logo.svg"), "w") as f:
    f.write(arcwyre_logo)
print("Logo created.")
