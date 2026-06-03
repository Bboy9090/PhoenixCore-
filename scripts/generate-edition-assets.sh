#!/bin/bash
# generate-edition-assets.sh
# Automates the creation of edition-specific Kvantum and Icon themes by recoloring master SVG assets.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
THEME_PACK_DIR="$REPO_ROOT/HomeAurelia-Theme-Pack"
ICONS_DIR="$THEME_PACK_DIR/09-Icons"
MASTERS_DIR="$ICONS_DIR/masters"
KVANTUM_DIR="$THEME_PACK_DIR/07-Kvantum"

# Master Colors (from HomeAurelia default theme)
MASTER_PRIMARY="#1A6FFF"
MASTER_SECONDARY="#7AC8FF"
MASTER_ACCENT="#D4AF37"
MASTER_SURFACE="#0F1E3A"
MASTER_BACKGROUND="#081326"

function manifest_color() {
    local key="$1"
    local file="$2"
    awk -v k="$key" '
        $1 ~ ("^" k ":") {
            if (match($0, /#[0-9A-Fa-f]{6}/)) {
                print substr($0, RSTART, RLENGTH)
                exit
            }
        }
    ' "$file"
}

function normalize_color() {
    local raw="${1:-}"
    local fallback="${2:-}"
    raw="$(echo "$raw" | tr -d '[:space:]')"
    if [[ "$raw" =~ ^#[0-9A-Fa-f]{6}$ ]]; then
        # Return uppercase hex
        echo "$raw" | tr '[:lower:]' '[:upper:]'
    else
        echo "$fallback"
    fi
}

echo "🎨 Phoenix OS Edition Asset Generator"
echo "======================================"

for edition_manifest in "$REPO_ROOT"/editions/*/edition.yaml; do
    if [ ! -f "$edition_manifest" ]; then
        continue
    fi

    edition_id=$(sed -n "s/^id:[[:space:]]*//p" "$edition_manifest" | sed 's/^"//;s/"$//' | head -n 1)
    display_name=$(sed -n "s/^display_name:[[:space:]]*//p" "$edition_manifest" | sed 's/^"//;s/"$//' | head -n 1)
    
    if [ "$edition_id" == "home" ]; then
        # Home defaults to masters, skip
        continue
    fi

    echo "⚙️  Processing Edition: $display_name ($edition_id)"

    # Extract target colors
    primary=$(normalize_color "$(manifest_color primary "$edition_manifest")" "$MASTER_PRIMARY")
    secondary=$(normalize_color "$(manifest_color secondary "$edition_manifest")" "$MASTER_SECONDARY")
    accent=$(normalize_color "$(manifest_color accent "$edition_manifest")" "$MASTER_ACCENT")
    surface=$(normalize_color "$(manifest_color surface "$edition_manifest")" "$MASTER_SURFACE")
    background=$(normalize_color "$(manifest_color background "$edition_manifest")" "$MASTER_BACKGROUND")

    echo "   Primary: $primary, Secondary: $secondary, Accent: $accent"

    # --- 1. Generate Icons ---
    icon_theme_name="home-aurelia-${edition_id}"
    target_icon_dir="$ICONS_DIR/$icon_theme_name"
    
    echo "   📦 Generating Icon Set: $icon_theme_name"
    mkdir -p "$target_icon_dir"
    
    # We copy the masters and rewrite colors directly
    # To keep it lightweight for now we just recolor the masters folder as a flat directory structure
    # that the user can later convert to PNGs or use directly in SVGs.
    rm -rf "$target_icon_dir"
    cp -R "$MASTERS_DIR" "$target_icon_dir"

    # Recolor all SVGs in the target icon directory
    find "$target_icon_dir" -type f -name "*.svg" -print0 | while IFS= read -r -d '' file; do
        sed -i.bak -e "s/$MASTER_PRIMARY/$primary/g" \
                   -e "s/$(echo $MASTER_PRIMARY | tr '[:upper:]' '[:lower:]')/$primary/g" \
                   -e "s/$MASTER_SECONDARY/$secondary/g" \
                   -e "s/$(echo $MASTER_SECONDARY | tr '[:upper:]' '[:lower:]')/$secondary/g" \
                   -e "s/$MASTER_ACCENT/$accent/g" \
                   -e "s/$(echo $MASTER_ACCENT | tr '[:upper:]' '[:lower:]')/$accent/g" \
                   -e "s/$MASTER_SURFACE/$surface/g" \
                   -e "s/$(echo $MASTER_SURFACE | tr '[:upper:]' '[:lower:]')/$surface/g" \
                   -e "s/$MASTER_BACKGROUND/$background/g" \
                   -e "s/$(echo $MASTER_BACKGROUND | tr '[:upper:]' '[:lower:]')/$background/g" \
                   "$file"
        rm -f "${file}.bak"
    done

    # Create basic theme index if missing
    if [ ! -f "$target_icon_dir/index.theme" ]; then
        cat <<EOF > "$target_icon_dir/index.theme"
[Icon Theme]
Name=$icon_theme_name
Comment=Icons for Phoenix OS $display_name
Inherits=home-aurelia,breeze
Directories=places
[places]
Size=512
Context=Places
Type=Scalable
EOF
    fi

    # --- 2. Generate Kvantum Theme ---
    # Kvantum names usually CamelCase derived from display name
    kvantum_theme_name="HomeAurelia-$(echo $edition_id | awk -F'-' '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)} 1' | tr -d ' ')"
    target_kv_dir="$KVANTUM_DIR/$kvantum_theme_name"
    
    echo "   📦 Generating Kvantum Theme: $kvantum_theme_name"
    rm -rf "$target_kv_dir"
    mkdir -p "$target_kv_dir"
    
    # Copy base HomeAurelia config
    if [ -f "$KVANTUM_DIR/HomeAurelia/HomeAurelia.kvconfig" ]; then
        cp "$KVANTUM_DIR/HomeAurelia/HomeAurelia.kvconfig" "$target_kv_dir/${kvantum_theme_name}.kvconfig"
        
        # Modify the theme name inside the file
        sed -i.bak -e "s/theme=HomeAurelia/theme=$kvantum_theme_name/g" "$target_kv_dir/${kvantum_theme_name}.kvconfig"

        # Replace color hexes
        sed -i.bak -e "s/$MASTER_PRIMARY/$primary/g" \
                   -e "s/$(echo $MASTER_PRIMARY | tr '[:upper:]' '[:lower:]')/$primary/g" \
                   -e "s/$MASTER_SECONDARY/$secondary/g" \
                   -e "s/$(echo $MASTER_SECONDARY | tr '[:upper:]' '[:lower:]')/$secondary/g" \
                   -e "s/$MASTER_ACCENT/$accent/g" \
                   -e "s/$(echo $MASTER_ACCENT | tr '[:upper:]' '[:lower:]')/$accent/g" \
                   -e "s/$MASTER_SURFACE/$surface/g" \
                   -e "s/$(echo $MASTER_SURFACE | tr '[:upper:]' '[:lower:]')/$surface/g" \
                   -e "s/$MASTER_BACKGROUND/$background/g" \
                   -e "s/$(echo $MASTER_BACKGROUND | tr '[:upper:]' '[:lower:]')/$background/g" \
                   "$target_kv_dir/${kvantum_theme_name}.kvconfig"

        rm -f "$target_kv_dir/${kvantum_theme_name}.kvconfig.bak"
    fi

    # Recolor Kvantum SVG if present
    if [ -f "$KVANTUM_DIR/HomeAurelia/HomeAurelia.svg" ]; then
        cp "$KVANTUM_DIR/HomeAurelia/HomeAurelia.svg" "$target_kv_dir/${kvantum_theme_name}.svg"
        sed -i.bak -e "s/$MASTER_PRIMARY/$primary/g" \
                   -e "s/$(echo $MASTER_PRIMARY | tr '[:upper:]' '[:lower:]')/$primary/g" \
                   -e "s/$MASTER_SECONDARY/$secondary/g" \
                   -e "s/$(echo $MASTER_SECONDARY | tr '[:upper:]' '[:lower:]')/$secondary/g" \
                   -e "s/$MASTER_ACCENT/$accent/g" \
                   -e "s/$(echo $MASTER_ACCENT | tr '[:upper:]' '[:lower:]')/$accent/g" \
                   -e "s/$MASTER_SURFACE/$surface/g" \
                   -e "s/$(echo $MASTER_SURFACE | tr '[:upper:]' '[:lower:]')/$surface/g" \
                   -e "s/$MASTER_BACKGROUND/$background/g" \
                   -e "s/$(echo $MASTER_BACKGROUND | tr '[:upper:]' '[:lower:]')/$background/g" \
                   "$target_kv_dir/${kvantum_theme_name}.svg"
        rm -f "$target_kv_dir/${kvantum_theme_name}.svg.bak"
    fi

    echo "   ✅ Generated assets for $edition_id"
    echo ""

done

echo "🎉 All automated edition assets generated!"
