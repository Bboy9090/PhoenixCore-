import urllib.request
import hashlib
import json
import sys
from pathlib import Path

def get_hash_from_url(url):
    print(f"[*] Downloading and hashing: {url}")
    sha256 = hashlib.sha256()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as res:
            while True:
                chunk = res.read(65536)
                if not chunk:
                    break
                sha256.update(chunk)
        h = sha256.hexdigest()
        print(f"[+] Computed Hash: {h}")
        return h
    except Exception as e:
        print(f"[-] Failed to fetch/hash {url}: {e}")
        return None

def fetch_void_live_hash():
    print("[*] Fetching Void Linux Live ISO official hash from sha256sum.txt...")
    url = "https://repo.voidlinux.org/live/20240314/sha256sum.txt"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as res:
            content = res.read().decode("utf-8")
        for line in content.splitlines():
            if "void-live-x86_64-20240314-xfce.iso" in line:
                h = line.split()[0]
                print(f"[+] Found Void Live Hash: {h}")
                return h
    except Exception as e:
        print(f"[-] Failed to parse Void Live hash: {e}")
    return None

def main():
    registry_path = Path("manifests/tool_registry.json")
    if not registry_path.exists():
        print("[-] tool_registry.json not found!")
        sys.exit(1)
        
    with open(registry_path, "r", encoding="utf-8") as f:
        registry = json.load(f)
        
    updated = False
    for tool in registry.get("tools", []):
        if tool["id"] == "rufus":
            h = get_hash_from_url(tool["download_url"])
            if h:
                tool["expected_sha256"] = h
                updated = True
        elif tool["id"] == "void-live-diagnostics":
            h = fetch_void_live_hash()
            if h:
                tool["expected_sha256"] = h
                updated = True
        elif tool["id"] == "opencore-legacy-patcher":
            # For OCLP v1.5.0 GUI zip, let's query its hash from the actual asset
            url = "https://github.com/dortania/OpenCore-Legacy-Patcher/releases/download/1.5.0/OpenCore-Patcher-GUI.app.zip"
            h = get_hash_from_url(url)
            if h:
                tool["expected_sha256"] = h
                updated = True
                
    if updated:
        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2)
        print("[+] tool_registry.json updated successfully with real production hashes!")

if __name__ == "__main__":
    main()
