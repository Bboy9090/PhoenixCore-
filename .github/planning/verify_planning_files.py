import os
import json
import sys
from import_to_github import parse_markdown_epics

def test_json_files():
    dir_path = os.path.dirname(__file__)
    for filename in ["labels.json", "milestones.json", "project.json"]:
        file_path = os.path.join(dir_path, filename)
        assert os.path.exists(file_path), f"{filename} does not exist!"
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                json.load(f)
            print(f"[+] Local verification passed for JSON: {filename}")
        except Exception as e:
            print(f"[-] JSON validation failed for {filename}: {e}")
            sys.exit(1)

def test_markdown_parsing():
    dir_path = os.path.dirname(__file__)
    md_file = os.path.join(dir_path, "epics_and_issues.md")
    assert os.path.exists(md_file), "epics_and_issues.md does not exist!"
    try:
        epics = parse_markdown_epics(md_file)
        print(f"[+] Local verification passed for Markdown parsing. Found {len(epics)} epics.")
        
        # Verify exactly 9 epics are found
        if len(epics) != 9:
            print(f"[-] Expected 9 epics, found {len(epics)}")
            sys.exit(1)
            
        for i, epic in enumerate(epics):
            num_issues = len(epic['child_issues'])
            print(f"    - Epic {i+1} \"{epic['title']}\": {num_issues} child issues parsed.")
            if not (3 <= num_issues <= 7):
                print(f"[-] Expected between 3 and 7 child issues for epic, found {num_issues}")
                sys.exit(1)
    except Exception as e:
        print(f"[-] Markdown parsing verification failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("[*] Running local planning structures verification...")
    test_json_files()
    test_markdown_parsing()
    print("[+] All verification checks completed successfully! Ready for remote deployment.")
