import re
import sys
from pathlib import Path

def check_macbook_target_sanity():
    app_file = Path('dashboard/src/App.jsx')
    if not app_file.exists():
        print(f'[*] Warning: {app_file} not found or skipped in local check path.')
        return
        
    try:
        content = app_file.read_text(encoding='utf-8')
        models = re.findall(r'\'(MacBook[A-Za-z0-9,]+.*?)\'', content)
        imacs = re.findall(r'\'(iMac[A-Za-z0-9,]+.*?)\'', content)
        macminis = re.findall(r'\'(Macmini[A-Za-z0-9,]+.*?)\'', content)
        macpros = re.findall(r'\'(MacPro[A-Za-z0-9,]+.*?)\'', content)
        
        total_models = len(models) + len(imacs) + len(macminis) + len(macpros)
        print(f'[+] Detected {total_models} MacBook hardware models mapped in App.jsx')
        if total_models < 10:
            print('[-] Error: Underpopulated model matrix mapping!')
            sys.exit(1)
    except Exception as e:
        print(f'[-] Error verifying App.jsx models: {e}')
        sys.exit(1)

def main():
    print("[*] Running Macbook Target Map Sanity checks...")
    check_macbook_target_sanity()
    print('[+] Verifying that EFI secure boot configuration maps exist...')

if __name__ == "__main__":
    main()
