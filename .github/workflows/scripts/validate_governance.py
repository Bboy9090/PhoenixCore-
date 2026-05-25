import os
import re
import sys
import json
import argparse

def check_naming():
    print('[*] Validating Tauri App IDs, Crate Packages and Naming systems...')
    tauri_configs = ['src-tauri/tauri.conf.json', 'dashboard/src-tauri/tauri.conf.json']
    for tc in tauri_configs:
        if os.path.exists(tc):
            try:
                with open(tc, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    identifier = data.get('tauri', {}).get('bundle', {}).get('identifier', '')
                    print(f'[+] Found Tauri Bundle Identifier: {identifier}')
                    if 'com.example' in identifier:
                        print('[-] Error: Found unapproved example Tauri ID!')
                        sys.exit(1)
            except Exception as e:
                print(f'[-] Error parsing {tc}: {e}')
                sys.exit(1)
    print('[+] Tauri / Crate naming boundaries validated successfully.')

def check_safety():
    print('[*] Scanning codebase for dangerous or destructive partition commands...')
    unsafe_patterns = [
        r'dd\s+if=.*?of=\/dev\/[a-z]{3}(?!\d)', # raw dev overrides
        r'mkfs\..*?\s+\/dev\/[a-z]{3}(?!\d)',
        r'rm\s+-rf\s+\/\s',
        r'shred\s',
        r'diskpart.*?clean'
    ]
    
    for root, dirs, files in os.walk('.'):
        if 'node_modules' in root or '.git' in root or '.github' in root:
            continue
        for file in files:
            if file.endswith(('.py', '.js', '.jsx', '.sh', '.bat', '.ps1')):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    for pattern in unsafe_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            print(f'[-] DANGER: Prohibited destructive code pattern "{pattern}" found in {filepath}!')
                            print(f'    Matches: {matches}')
                            sys.exit(1)
                except Exception as e:
                    print(f'[*] Warning: Could not read {filepath}: {e}')
    print('[+] Governance safety scan complete. Zero destructive operations found.')

def main():
    parser = argparse.ArgumentParser(description="Governance Validation Utility")
    parser.add_argument("--check", choices=["naming", "safety", "all"], default="all")
    args = parser.parse_args()
    
    if args.check in ("naming", "all"):
        check_naming()
    if args.check in ("safety", "all"):
        check_safety()

if __name__ == "__main__":
    main()
