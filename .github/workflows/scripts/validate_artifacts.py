import glob
import json
import sys


def main():
    print("[*] Verifying Manifest JSON Files...")
    files = glob.glob("**/*.json", recursive=True)
    for f in files:
        if "node_modules" in f or "package" in f or "eslint" in f:
            continue
        try:
            with open(f, "r", encoding="utf-8") as fh:
                json.load(fh)
            print(f"[+] Validated JSON structure: {f}")
        except Exception as e:
            print(f"[-] Invalid JSON file: {f}. Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
