import os
import shutil
import time
import hashlib

def calculate_sha256(filepath):
    """Calculate SHA256 of a file block-by-block."""
    sha256 = hashlib.sha256()
    total_size = os.path.getsize(filepath)
    bytes_read = 0
    start_time = time.time()
    
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(1024 * 1024)  # 1MB chunk
            if not chunk:
                break
            sha256.update(chunk)
            bytes_read += len(chunk)
            # Print progress every 100MB or at completion
            if bytes_read % (100 * 1024 * 1024) == 0 or bytes_read == total_size:
                elapsed = time.time() - start_time
                speed = (bytes_read / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                pct = (bytes_read / total_size) * 100
                print(f"      Calculated SHA256: {pct:.1f}% ({bytes_read / (1024*1024*1024):.2f} GB / {total_size / (1024*1024*1024):.2f} GB) at {speed:.2f} MB/s", end='\r')
    print()
    return sha256.hexdigest()

def copy_with_progress(src, dst):
    """Copy file and print progress."""
    total_size = os.path.getsize(src)
    bytes_copied = 0
    start_time = time.time()
    
    with open(src, 'rb') as fsrc:
        with open(dst, 'wb') as fdst:
            while True:
                chunk = fsrc.read(1024 * 1024)  # 1MB chunk
                if not chunk:
                    break
                fdst.write(chunk)
                bytes_copied += len(chunk)
                if bytes_copied % (100 * 1024 * 1024) == 0 or bytes_copied == total_size:
                    elapsed = time.time() - start_time
                    speed = (bytes_copied / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                    pct = (bytes_copied / total_size) * 100
                    print(f"      Copying: {pct:.1f}% ({bytes_copied / (1024*1024*1024):.2f} GB / {total_size / (1024*1024*1024):.2f} GB) at {speed:.2f} MB/s", end='\r')
    print()

def main():
    src_dir = "/Users/bj90-m1/PhoenixCore-/os/phoenix-os/build"
    dst_dir = "/Volumes/Ventoy/BWOS-PR41A"
    
    isos_to_copy = [
        "bwos-home.iso",
        "bwos-arcwyre.iso",
        "bwos-thunder-god.iso",
        "bwos-blue-phoenix.iso",
        "bwos-aurelia.iso"
    ]
    
    print("🚀 Starting copy of latest flagship ISOs to Ventoy external drive...")
    print(f"   Source directory: {src_dir}")
    print(f"   Destination directory: {dst_dir}")
    print(f"   Target ISOs: {', '.join(isos_to_copy)}")
    print()
    
    if not os.path.exists(dst_dir):
        print(f"❌ Error: Destination directory {dst_dir} does not exist. Creating it...")
        os.makedirs(dst_dir, exist_ok=True)
        
    for iso in isos_to_copy:
        src_path = os.path.join(src_dir, iso)
        dst_path = os.path.join(dst_dir, iso)
        
        if not os.path.exists(src_path):
            print(f"⚠️  Warning: Source ISO {src_path} does not exist. Skipping.")
            continue
            
        print(f"📂 Processing: {iso}")
        
        # Check if identical already
        if os.path.exists(dst_path):
            print("   Comparing file sizes...")
            src_size = os.path.getsize(src_path)
            dst_size = os.path.getsize(dst_path)
            if src_size == dst_size:
                print("   Sizes match! Calculating and comparing SHA256 checksums to verify if update is needed...")
                print("   Calculating source hash...")
                src_hash = calculate_sha256(src_path)
                print("   Calculating destination hash...")
                dst_hash = calculate_sha256(dst_path)
                
                if src_hash == dst_hash:
                    print("   ✅ File on Ventoy is already identical to the latest build. No copy needed!")
                    continue
                else:
                    print("   ❌ Hashes differ! Overwriting the old file...")
            else:
                print(f"   ❌ Size mismatch! Source: {src_size} bytes, Destination: {dst_size} bytes. Overwriting...")
        
        print(f"   📥 Copying new version to Ventoy...")
        temp_dst = dst_path + ".tmp"
        try:
            copy_with_progress(src_path, temp_dst)
            if os.path.exists(dst_path):
                os.remove(dst_path)
            os.rename(temp_dst, dst_path)
            print("   ✅ Copy completed successfully!")
        except Exception as e:
            print(f"   ❌ Copy failed: {e}")
            if os.path.exists(temp_dst):
                os.remove(temp_dst)
                
        # Clean up potential Apple double metadata files if they are created by macOS ExFAT handler
        double_file = os.path.join(dst_dir, f"._{iso}")
        if os.path.exists(double_file):
            print(f"   🧹 Cleaning up macOS dot-underscore metadata file: {os.path.basename(double_file)}")
            try:
                os.remove(double_file)
            except Exception as e:
                print(f"   ⚠️ Failed to remove metadata file: {e}")
                
    print("\n🎉 All target ISO files processed and synchronized onto the Ventoy drive!")

if __name__ == '__main__':
    main()
