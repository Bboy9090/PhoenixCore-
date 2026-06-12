import os
import glob

css_injection = """
/* =========================================================
   ZENITH-LEVEL AESTHETIC OVERRIDE
   ========================================================= */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&family=Inter:wght@400;500;700&display=swap');

body {
    background: radial-gradient(circle at top right, rgba(0, 255, 65, 0.15), transparent 500px),
                radial-gradient(circle at bottom left, rgba(0, 150, 255, 0.1), transparent 500px),
                linear-gradient(135deg, #0d1117 0%, #000000 100%) !important;
    background-attachment: fixed !important;
    font-family: 'Outfit', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
    color: #e2e8f0 !important;
}

/* Glassmorphic Surfaces */
.container, .panel, .card, .toolbar, .shortcut-bar, .app-container, .main-content, .sidebar, header, footer {
    background: rgba(20, 25, 35, 0.45) !important;
    backdrop-filter: blur(16px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(16px) saturate(180%) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
    border-radius: 12px;
}

/* Interactive Elements */
button, .btn, .key, .action-btn {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    backdrop-filter: blur(4px) !important;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    border-radius: 8px;
    color: #e2e8f0 !important;
    cursor: pointer !important;
}

button:hover, .btn:hover, .key:hover, .action-btn:hover {
    background: rgba(0, 255, 65, 0.15) !important;
    border-color: rgba(0, 255, 65, 0.5) !important;
    box-shadow: 0 0 15px rgba(0, 255, 65, 0.3) !important;
    transform: translateY(-2px);
}

button:active, .btn:active, .key:active {
    transform: translateY(0);
}

/* Inputs and Textareas */
input, textarea, select {
    background: rgba(0, 0, 0, 0.4) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #fff !important;
    border-radius: 8px !important;
    transition: border-color 0.3s, box-shadow 0.3s !important;
    font-family: 'Inter', monospace !important;
}

input:focus, textarea:focus, select:focus {
    border-color: rgba(0, 255, 65, 0.6) !important;
    outline: none !important;
    box-shadow: 0 0 0 2px rgba(0, 255, 65, 0.25) !important;
}

/* Scrollbars */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 4px;
}
::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 255, 65, 0.5);
}
"""

html_files = glob.glob("/Users/bj90-m1/PhoenixCore-/apps/web/arcwyre-html-apps/*.html")

for file in html_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "ZENITH-LEVEL AESTHETIC OVERRIDE" in content:
        print(f"Skipping {os.path.basename(file)}, already polished.")
        continue
        
    # Inject just before </style>
    if "</style>" in content:
        new_content = content.replace("</style>", f"{css_injection}\n</style>")
        with open(file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Polished {os.path.basename(file)}!")
    else:
        # Inject just before </head>
        new_content = content.replace("</head>", f"<style>{css_injection}\n</style>\n</head>")
        with open(file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Polished {os.path.basename(file)} (Created <style>)!")

