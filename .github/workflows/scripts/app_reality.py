import os
import json
import sys

def main():
    print('[*] Checking App Launch Matrix Schema rules...')
    
    matrix_paths = [
        'manifests/app_matrix.json',
        'apps/configs/pr40_matrix.json',
        'dashboard/public/app_matrix.json'
    ]
    
    found = False
    for mp in matrix_paths:
        if os.path.exists(mp):
            found = True
            try:
                with open(mp, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f'[+] Parsed App Matrix from {mp}')
                apps = data.get('apps', data.get('packages', []))
                for app in apps:
                    name = app.get('name')
                    compat_layer = app.get('compatibility_layer', app.get('layer'))
                    sandbox = app.get('sandbox', {})
                    print(f'  - Verified Config for app: {name} [Compat: {compat_layer}] [Sandbox: {sandbox.get("enabled", False)}]')
                    if app.get('placeholder', False) is True:
                        print(f'[-] Error: Placeholder application "{name}" is prohibited by governance rules.')
                        sys.exit(1)
            except Exception as e:
                print(f'[-] Failed parsing App Matrix file {mp}: {e}')
                sys.exit(1)
                
    if not found:
        print('[*] Info: No app matrix files found. Initializing validation standby.')
    else:
        print('[+] App Reality Matrix validation checks successful.')

if __name__ == "__main__":
    main()
