import os
import glob
from PIL import Image, ImageDraw, ImageFont

editions = ['aurelia', 'arcwyre', 'thundergod', 'native']

# Directories based on previous steps
base_dl = "/Users/bj90-m1/Downloads/Phoenix-Repaired"
report_out = "/Users/bj90-m1/Downloads/HomeAurelia-Transparency-Size-Audit-AFTER.txt"

def check_checkerboard(img):
    """
    Heuristic check for fake transparency checkerboards baked into RGB.
    Checkerboards usually have #CCCCCC and #FFFFFF or similar greys.
    We just check the bottom right corner (last 20x20 pixels) for high variance in grayscale.
    """
    if img.mode != 'RGBA' and img.mode != 'RGB':
        img = img.convert('RGBA')
    
    width, height = img.size
    if width < 20 or height < 20: return False
    
    # Crop bottom right corner 20x20
    corner = img.crop((width-20, height-20, width, height)).convert('L')
    pixels = list(corner.getdata())
    
    # If the variance is high and the colors are greyish
    std_dev = __import__('statistics').pstdev(pixels)
    if 20 < std_dev < 80:
        return True
    return False

def audit_file(filepath, expected_size, expected_alpha):
    filename = os.path.basename(filepath)
    try:
        with Image.open(filepath) as img:
            actual_size = f"{img.width}x{img.height}"
            actual_mode = img.mode
            
            alpha_present = False
            if 'A' in img.mode:
                # Check if any pixel has alpha < 255
                extrema = img.getextrema()
                if extrema[3][0] < 255:
                    alpha_present = True
            
            has_checkerboard = check_checkerboard(img)
            
            # Logic for PASS / FAIL
            status = "PASS"
            visual_issue = "no"
            
            if actual_size != expected_size:
                status = "NEEDS RESIZE"
                visual_issue = "yes (wrong size)"
            elif expected_alpha and not alpha_present:
                status = "NEEDS REPLACEMENT"
                visual_issue = "yes (no true alpha)"
            elif expected_alpha and has_checkerboard:
                status = "NEEDS TRANSPARENCY CLEANUP"
                visual_issue = "yes (fake checkerboard)"
            elif "kickoff" in filename and ("native" in filename.lower() or "arcwyre" in filename.lower() or "thundergod" in filename.lower()):
                 status = "NEEDS REPLACEMENT" # From previous visual audit knowledge
                 visual_issue = "yes (collage/generic)"
            elif "fastfetch" in filename and ("native" in filename.lower() or "arcwyre" in filename.lower() or "thundergod" in filename.lower()):
                 status = "NEEDS REPLACEMENT"
                 visual_issue = "yes (collage/generic)"
            elif "about" in filename and ("native" in filename.lower() or "arcwyre" in filename.lower() or "thundergod" in filename.lower()):
                 status = "NEEDS REPLACEMENT"
                 visual_issue = "yes (collage/generic)"
                 
            return {
                "filename": filename,
                "expected_size": expected_size,
                "actual_size": actual_size,
                "expected_alpha": "yes" if expected_alpha else "no",
                "actual_mode": actual_mode,
                "alpha_present": "yes" if alpha_present else "no",
                "visual_issue": visual_issue,
                "status": status,
                "img_obj": img.copy() # Store for proof sheet
            }
    except Exception as e:
        return {
            "filename": filename,
            "expected_size": expected_size,
            "actual_size": "ERROR",
            "expected_alpha": "yes" if expected_alpha else "no",
            "actual_mode": "ERROR",
            "alpha_present": "ERROR",
            "visual_issue": str(e),
            "status": "FAIL",
            "img_obj": None
        }

def find_files_for_edition(edition):
    files = {}
    
    # We will just walk the base_dl directory and match edition name
    for root, dirs, filenames in os.walk(base_dl):
        # Only look in directories that contain the edition name
        if edition.lower() not in root.lower():
            continue
            
        for fname in filenames:
            if not fname.endswith(".png"): continue
            if "raw-crop" in fname: continue
            
            fpath = os.path.join(root, fname)
            fname_lower = fname.lower()
            
            if "ksplash" in fname_lower: files['ksplash'] = fpath
            if "avatar" in fname_lower: files['avatar'] = fpath
            if "calamares-01" in fname_lower: files['calamares-01'] = fpath
            if "calamares-02" in fname_lower: files['calamares-02'] = fpath
            if "calamares-03" in fname_lower: files['calamares-03'] = fpath
            if "calamares-04" in fname_lower: files['calamares-04'] = fpath
            
            # For branding
            if "kickoff" in fname_lower: files['kickoff'] = fpath
            if "fastfetch" in fname_lower: files['fastfetch'] = fpath
            if "about" in fname_lower: files['about'] = fpath
            
            # For icons
            if "icons" in root.lower() and "512x512" in root.lower() and not any(x in fname_lower for x in ['kickoff', 'fastfetch', 'about']):
                if 'icon_1' not in files: files['icon_1'] = fpath
                elif 'icon_2' not in files: files['icon_2'] = fpath
                elif 'icon_3' not in files: files['icon_3'] = fpath
                
    return files

def create_proof_sheet(edition, results, output_path):
    # We want a bright magenta background so transparency (and checkerboards) stand out
    img_w, img_h = 1600, 1200
    proof = Image.new('RGB', (img_w, img_h), color=(255, 0, 255))
    draw = ImageDraw.Draw(proof)
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    except:
        font = ImageFont.load_default()

    x, y = 20, 20
    max_h = 0
    for res in results:
        if not res['img_obj']: continue
        
        img = res['img_obj']
        img.thumbnail((300, 300))
        
        if x + 300 > img_w:
            x = 20
            y += max_h + 80
            max_h = 0
            
        proof.paste(img, (x, y), img if 'A' in img.mode else None)
        
        text = f"{res['filename'][:30]}\nSize: {res['actual_size']} (Exp: {res['expected_size']})\nAlpha: {res['alpha_present']} (Exp: {res['expected_alpha']})\nStatus: {res['status']}"
        draw.text((x, y + img.height + 5), text, fill=(0,0,0), font=font)
        draw.text((x-1, y + img.height + 4), text, fill=(255,255,255), font=font) # shadow
        
        max_h = max(max_h, img.height)
        x += 320
        
    proof.save(output_path)

def main():
    report_lines = []
    report_lines.append("HOME AURELIA TRANSPARENCY & SIZE AUDIT")
    report_lines.append("=======================================\n")
    
    for edition in editions:
        report_lines.append(f"--- {edition.upper()} EDITION ---")
        files = find_files_for_edition(edition)
        
        expected_specs = {
            'kickoff': ('256x256', True),
            'fastfetch': ('512x512', True),
            'about': ('512x512', True),
            'avatar': ('512x512', False),
            'ksplash': ('1920x1080', False),
            'calamares-01': ('1920x1080', False),
            'calamares-02': ('1920x1080', False),
            'calamares-03': ('1920x1080', False),
            'calamares-04': ('1920x1080', False),
            'icon_1': ('512x512', True),
            'icon_2': ('512x512', True),
            'icon_3': ('512x512', True)
        }
        
        results = []
        for key, spec in expected_specs.items():
            fpath = files.get(key)
            if fpath and os.path.exists(fpath):
                res = audit_file(fpath, spec[0], spec[1])
                results.append(res)
                
                report_lines.append(f"File: {res['filename']}")
                report_lines.append(f"  Expected Size: {res['expected_size']}")
                report_lines.append(f"  Actual Size: {res['actual_size']}")
                report_lines.append(f"  Expected Alpha: {res['expected_alpha']}")
                report_lines.append(f"  Actual Mode: {res['actual_mode']}")
                report_lines.append(f"  Alpha Present: {res['alpha_present']}")
                report_lines.append(f"  Visual Issue: {res['visual_issue']}")
                report_lines.append(f"  Status: {res['status']}\n")
            else:
                report_lines.append(f"File for {key} NOT FOUND\n")
                
        # Generate proof sheet
        proof_path = os.path.join(base_dl, f"{edition}-transparency-size-proof.png")
        create_proof_sheet(edition, results, proof_path)
        report_lines.append(f"Generated Proof Sheet: {proof_path}\n")
        
    with open(report_out, 'w') as f:
        f.write('\n'.join(report_lines))
        
    print(f"Audit complete. Report saved to {report_out}")

if __name__ == "__main__":
    main()
