import os
import re
import sys
from pathlib import Path

def audit_workflows():
    print("[*] Auditing GitHub Actions YAML workflow files for inline Python syntax correctness...")
    workflows_dir = Path(".github/workflows")
    if not workflows_dir.exists():
        print("[-] Workflows directory not found!")
        sys.exit(1)
        
    yaml_files = list(workflows_dir.glob("*.yml"))
    print(f"[+] Found {len(yaml_files)} workflow files.")
    
    for yf in yaml_files:
        print(f"[*] Auditing: {yf.name}")
        content = yf.read_text(encoding="utf-8")
        
        # Regex to extract multi-line python inline scripts
        # Finds: python -c "..." or python -c '...'
        python_blocks = re.findall(r'python\s+-c\s+"""(.*?)"""', content, re.DOTALL)
        python_blocks += re.findall(r'python\s+-c\s+"(.*?)"', content, re.DOTALL)
        
        for idx, block in enumerate(python_blocks):
            # Clean up the script block (unescape quotes or YAML indentations if needed)
            cleaned_block = block.strip()
            # Try compiling the block to catch syntax errors
            try:
                compile(cleaned_block, f"{yf.name}_inline_{idx}", "exec")
                print(f"    [+] Inline Python Block {idx+1}: Syntax OK")
            except SyntaxError as e:
                print(f"    [-] Inline Python Syntax Error in {yf.name} Block {idx+1}: {e}")
                sys.exit(1)

if __name__ == "__main__":
    audit_workflows()
