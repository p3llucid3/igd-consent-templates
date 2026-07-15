#!/usr/bin/env python3
"""
Build script for igd-consent-templates.

Merges all per-package template files in sources/*.json into the single
igd-master.json file that the browser extension reads. This script is run
automatically by .github/workflows/build.yml whenever a file under sources/
changes, so contributors (including Claude) only ever need to edit small
per-package files, never the full merged file by hand.

Usage:
    python3 scripts/build.py
"""
import json
import glob
import os
import sys
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES_DIR = os.path.join(REPO_ROOT, "sources")
META_PATH = os.path.join(SOURCES_DIR, "_meta.json")
OUTPUT_PATH = os.path.join(REPO_ROOT, "igd-master.json")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    if not os.path.isfile(META_PATH):
        print(f"ERROR: metadata file not found at {META_PATH}", file=sys.stderr)
        sys.exit(1)

    meta = load_json(META_PATH)

    source_files = sorted(
        f for f in glob.glob(os.path.join(SOURCES_DIR, "*.json"))
        if os.path.basename(f) != "_meta.json"
    )

    if not source_files:
        print("ERROR: no source files found in sources/", file=sys.stderr)
        sys.exit(1)

    merged_templates = {}
    seen_in_file = {}
    duplicate_found = False

    for path in source_files:
        fname = os.path.basename(path)
        data = load_json(path)
        if not isinstance(data, dict):
            print(f"ERROR: {fname} does not contain a JSON object", file=sys.stderr)
            sys.exit(1)

        for template_name, template_obj in data.items():
            if template_name in merged_templates:
                print(
                    f"ERROR: duplicate template name '{template_name}' "
                    f"found in {fname} (already defined in {seen_in_file[template_name]})",
                    file=sys.stderr,
                )
                duplicate_found = True
                continue
            merged_templates[template_name] = template_obj
            seen_in_file[template_name] = fname

    if duplicate_found:
        sys.exit(1)

    output = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "version": meta["version"],
        "description": meta["description"],
        "templates": dict(sorted(merged_templates.items())),
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Built {OUTPUT_PATH}")
    print(f"  {len(source_files)} source files merged")
    print(f"  {len(merged_templates)} templates total")
    print(f"  version: {output['version']}")


if __name__ == "__main__":
    main()
