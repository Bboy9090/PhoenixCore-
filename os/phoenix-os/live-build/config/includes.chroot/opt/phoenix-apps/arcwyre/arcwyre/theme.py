"""
Arcwyre Visual Identity — macOS Native "Steve Jobs" Tier
The absolute highest tier of UI polish. Pixel-perfect macOS styling.
"""

COLORS = {
    # Base OS Colors (macOS Dark Mode exact hexes)
    "bg_window":     "#1E1E1E",   # macOS dark mode background
    "bg_sidebar":    "#282828",   # macOS slightly elevated sidebar
    
    # Surface & Cards
    "surface":       "#2C2C2E",   # macOS elevated card surface
    "surface_hover": "#3A3A3C",   
    "surface_active":"#48484A",   
    
    # Primary Accent (Sleek Apple-esque Cyan)
    "primary":       "#00D0E5",   
    "primary_glow":  "rgba(0, 208, 229, 0.15)",
    
    # Borders
    "border":        "rgba(255, 255, 255, 0.05)",
    "border_light":  "rgba(255, 255, 255, 0.1)",
    
    # Text (macOS Standard)
    "text_primary":  "#FFFFFF",   # Crisp white for titles
    "text_secondary":"#98989D",   # macOS secondary text gray
    "text_tertiary": "#636366",   # macOS tertiary text gray
    
    # Semantic Metrics (Make the colors mean something)
    "metric_cpu":    "#0A84FF",   # Apple Blue
    "metric_ram":    "#BF5AF2",   # Apple Purple
    "metric_disk":   "#32D74B",   # Apple Green
    "metric_temp":   "#FF9F0A",   # Apple Orange
    
    # Legacy aliases
    "text_dim":      "#98989D",
    "text_muted":    "#636366",
    "panel":         "#3A3A3C",
    "text":          "#FFFFFF",
    
    # Standard Status
    "success":       "#30D158",   
    "warning":       "#FF9F0A",   
    "danger":        "#FF453A",   
}

def get_stylesheet() -> str:
    c = COLORS
    return f"""
    QMainWindow {{
        background-color: {c['bg_window']};
    }}
    
    QWidget {{
        color: {c['text_primary']};
        font-family: "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", sans-serif;
        font-size: 13px;
        font-weight: 400;
    }}

    #sidebar {{
        background-color: {c['bg_sidebar']};
        border-right: 1px solid {c['border']};
    }}

    QListWidget {{
        background-color: transparent;
        border: none;
        outline: none;
    }}
    
    QListWidget::item {{
        padding: 8px 12px;
        margin: 2px 12px;
        border-radius: 6px;
        color: {c['text_primary']};
        background-color: transparent;
        font-weight: 500;
        font-size: 13px;
    }}

    QListWidget::item:hover {{
        background-color: rgba(255, 255, 255, 0.05);
    }}

    QListWidget::item:selected {{
        background-color: {c['primary']};
        color: #000000;
        font-weight: 600;
    }}

    QStackedWidget, #content_area {{
        background-color: {c['bg_window']};
    }}

    QFrame#card, QGroupBox {{
        background-color: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 10px;
        padding: 20px;
        margin-top: 10px;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 4px;
        color: {c['text_secondary']};
        font-weight: 600;
        font-size: 12px;
    }}

    QLabel {{ background-color: transparent; }}
    
    QLabel#title {{
        color: {c['text_primary']};
        font-size: 26px;
        font-weight: 700;
        letter-spacing: -0.5px;
    }}

    QLabel#subtitle {{
        color: {c['text_secondary']};
        font-size: 14px;
        font-weight: 400;
    }}

    QTableWidget {{
        background-color: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 10px;
        gridline-color: transparent;
        color: {c['text_primary']};
        font-size: 13px;
        selection-background-color: {c['primary_glow']};
        selection-color: {c['primary']};
        outline: none;
    }}

    QTableWidget::item {{
        padding: 10px;
        border-bottom: 1px solid {c['border']};
    }}

    QHeaderView::section {{
        background-color: transparent;
        color: {c['text_secondary']};
        border: none;
        border-bottom: 1px solid {c['border']};
        padding: 10px;
        font-size: 12px;
        font-weight: 600;
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 14px;
        border: none;
        margin: 2px;
    }}
    QScrollBar::handle:vertical {{
        background: rgba(255, 255, 255, 0.2);
        border-radius: 7px;
        min-height: 40px;
        margin: 2px;
        border: 2px solid transparent;
        background-clip: padding-box;
    }}
    QScrollBar::handle:vertical:hover {{
        background: rgba(255, 255, 255, 0.4);
        border: 2px solid transparent;
        background-clip: padding-box;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}

    QProgressBar {{
        background-color: {c['surface_hover']};
        border: none;
        border-radius: 7px;
        text-align: center;
        color: transparent;
        height: 14px;
    }}
    QProgressBar::chunk {{
        background-color: {c['primary']};
        border-radius: 7px;
    }}

    QPushButton {{
        background-color: {c['surface']};
        color: {c['text_primary']};
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 6px;
        padding: 6px 14px;
        font-size: 13px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {c['surface_hover']};
        border-color: rgba(255, 255, 255, 0.15);
    }}
    QPushButton:pressed {{
        background-color: {c['surface_active']};
    }}
    QPushButton#primary {{
        background-color: {c['primary']};
        color: #000000;
        border: none;
        font-weight: 600;
    }}
    QPushButton#danger {{
        background-color: {c['danger']};
        color: white;
        border: none;
    }}

    QLineEdit {{
        background-color: rgba(0,0,0,0.15);
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 13px;
    }}
    QLineEdit:focus {{
        border: 2px solid {c['primary']};
        background-color: {c['surface']};
        padding: 5px 9px;
    }}

    QTabWidget::pane {{ border: none; }}
    QTabBar::tab {{
        background-color: transparent;
        color: {c['text_secondary']};
        border: none;
        padding: 6px 12px;
        font-size: 13px;
        font-weight: 500;
        margin-right: 16px;
        border-bottom: 2px solid transparent;
    }}
    QTabBar::tab:selected {{
        color: {c['text_primary']};
        border-bottom: 2px solid {c['primary']};
    }}

    QTreeWidget {{
        background-color: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 10px;
        color: {c['text_primary']};
        outline: none;
    }}
    QTreeWidget::item {{
        padding: 8px;
        border-bottom: 1px solid {c['border']};
    }}
    """
