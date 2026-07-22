import os
import re
import json
import urllib.request
import urllib.error


def make_github_request(url, token, data=None, method="GET"):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8") if data else None,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "BWOS-Planning-Layer-Importer",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode("utf-8")), res.status
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode("utf-8")
        try:
            parsed_error = json.loads(error_msg)
            message = parsed_error.get("message", error_msg)
        except Exception:
            message = error_msg
        print(f"[-] HTTP Error {e.code} on {method} {url}: {message}")
        return None, e.code
    except Exception as e:
        print(f"[-] Network Error on {method} {url}: {e}")
        return None, 500


def parse_markdown_epics(filepath):
    """
    Parses epics_and_issues.md into a structured hierarchy for import.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    epics = []
    epic_blocks = content.split("## Epic ")

    for block in epic_blocks[1:]:
        lines = block.strip().split("\n")
        epic_id = lines[0].split(":")[0].strip()

        title_match = re.search(r"\*\*Title:\*\*\s*(.*)", block)
        milestone_match = re.search(r"\*\*Milestone:\*\*\s*`(.*)`", block)
        labels_match = re.search(r"\*\*Labels:\*\*\s*(.*)", block)

        epic_title = title_match.group(1).strip() if title_match else f"Epic {epic_id}"
        epic_milestone = milestone_match.group(1).strip() if milestone_match else None
        epic_labels = (
            [l.strip().strip("`") for l in labels_match.group(1).split(",")]
            if labels_match
            else []
        )

        # Find child issues inside block
        issue_blocks = block.split("### Issue ")
        child_issues = []

        for issue_block in issue_blocks[1:]:
            issue_lines = issue_block.strip().split("\n")
            issue_title = issue_lines[0].split(":")[1].strip()

            scope_match = re.search(r"-\s*\*\*Scope:\*\*\s*(.*)", issue_block)
            dod_match = re.search(
                r"-\s*\*\*Definition of Done:\*\*\s*(.*)", issue_block
            )
            val_match = re.search(
                r"-\s*\*\*Validation Commands:\*\*\s*```bash\s*(.*?)\s*```",
                issue_block,
                re.DOTALL,
            )
            dep_match = re.search(
                r"-\s*\*\*Blocked-by Dependencies:\*\*\s*(.*)", issue_block
            )
            safety_match = re.search(r"-\s*\*\*Safety Notes:\*\*\s*(.*)", issue_block)

            scope = scope_match.group(1).strip() if scope_match else ""
            dod = dod_match.group(1).strip() if dod_match else ""
            val = val_match.group(1).strip() if val_match else ""
            dep = dep_match.group(1).strip() if dep_match else ""
            safety = safety_match.group(1).strip() if safety_match else ""

            body = f"""### Crate / Stack Scope
{scope}

### Definition of Done (DoD)
{dod}

### Validation Commands
```bash
{val}
```

### Blocked-by Dependencies
{dep}

### Safety Notes
> [!WARNING]
> {safety}
"""
            child_issues.append(
                {"title": issue_title, "body": body, "epic_labels": epic_labels}
            )

        epics.append(
            {
                "title": f"epic({epic_id}): {epic_title}",
                "body": f"Strategic planning layer for active BWOS stack: {epic_title}.\n\nMilestone: {epic_milestone}",
                "labels": epic_labels,
                "milestone": epic_milestone,
                "child_issues": child_issues,
            }
        )

    return epics


def main():
    print("=" * 60)
    print("      BWOS Platform Factory: GitHub Importer Utility")
    print("=" * 60)

    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPO", "Bboy9090/PhoenixCore-")

    if not token:
        print("[!] GITHUB_TOKEN environment variable not set.")
        token = input(
            "[?] Enter your GitHub Personal Access Token (classic, with repo scope): "
        ).strip()
        if not token:
            print("[-] No token provided. Exiting.")
            return

    base_url = f"https://api.github.com/repos/{repo}"

    # 1. Create Labels
    print("\n[*] Processing Labels...")
    labels_file = os.path.join(os.path.dirname(__file__), "labels.json")
    if os.path.exists(labels_file):
        with open(labels_file, "r") as f:
            labels_data = json.load(f)

        for label in labels_data:
            print(f"[*] Creating/Updating label: {label['name']}...")
            url = f"{base_url}/labels"
            # Try creating
            res, code = make_github_request(url, token, label, method="POST")
            if code == 422:  # Already exists, try updating
                url = f"{base_url}/labels/{urllib.parse.quote(label['name'])}"
                make_github_request(url, token, label, method="PATCH")
                print(f"[+] Updated label: {label['name']}")
            elif res:
                print(f"[+] Created label: {label['name']}")
    else:
        print("[-] labels.json not found!")

    # 2. Create Milestones
    print("\n[*] Processing Milestones...")
    milestones_file = os.path.join(os.path.dirname(__file__), "milestones.json")
    milestone_map = {}
    if os.path.exists(milestones_file):
        with open(milestones_file, "r") as f:
            milestones_data = json.load(f)

        for ms in milestones_data:
            print(f"[*] Creating milestone: {ms['title']}...")
            url = f"{base_url}/milestones"
            res, code = make_github_request(url, token, ms, method="POST")
            if code == 422:  # Already exists, retrieve it
                url = f"{base_url}/milestones?state=all"
                all_ms, _ = make_github_request(url, token, method="GET")
                if all_ms:
                    for m in all_ms:
                        if m["title"] == ms["title"]:
                            milestone_map[ms["title"]] = m["number"]
                            print(
                                f"[~] Found existing milestone {ms['title']} (Number: {m['number']})"
                            )
                            break
            elif res:
                milestone_map[ms["title"]] = res["number"]
                print(f"[+] Created milestone {ms['title']} (Number: {res['number']})")
    else:
        print("[-] milestones.json not found!")

    # 3. Create Epics and Issues
    print("\n[*] Processing Epics and Issues...")
    epics_file = os.path.join(os.path.dirname(__file__), "epics_and_issues.md")
    if os.path.exists(epics_file):
        epics = parse_markdown_epics(epics_file)

        for epic in epics:
            print(f"\n[*] Creating Epic Issue: {epic['title']}...")
            # Match milestone number
            ms_number = milestone_map.get(epic["milestone"])

            epic_payload = {
                "title": epic["title"],
                "body": epic["body"],
                "labels": epic["labels"],
            }
            if ms_number:
                epic_payload["milestone"] = ms_number

            epic_issue, _ = make_github_request(
                f"{base_url}/issues", token, epic_payload, method="POST"
            )

            if epic_issue:
                epic_number = epic_issue["number"]
                print(f"[+] Created Epic: #{epic_number}")

                # Create child issues
                for child in epic.get("child_issues", []):
                    print(f"    [*] Creating Child Issue: {child['title']}...")
                    child_body = (
                        child["body"]
                        + f"\n\n---\n**Blocked-by / Epic Reference**: #{epic_number}"
                    )
                    child_labels = child["epic_labels"] + ["status:ready"]

                    child_payload = {
                        "title": child["title"],
                        "body": child_body,
                        "labels": child_labels,
                    }
                    if ms_number:
                        child_payload["milestone"] = ms_number

                    child_issue, _ = make_github_request(
                        f"{base_url}/issues", token, child_payload, method="POST"
                    )
                    if child_issue:
                        print(f"    [+] Created Child: #{child_issue['number']}")
            else:
                print(f"[-] Failed to create Epic: {epic['title']}")
    else:
        print("[-] epics_and_issues.md not found!")

    print("\n" + "=" * 60)
    print("      Provisioning Completed Successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
