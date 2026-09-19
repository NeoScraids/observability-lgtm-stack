#!/usr/bin/env python3
"""
scripts/bootstrap_dashboards.py
Automated provisioning script that pushes enterprise production dashboards
into a running Grafana instance via its REST API.
"""

import argparse
import base64
import glob
import json
import os
import sys
import time
import urllib.error
import urllib.request

GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")
GRAFANA_USER = os.getenv("GRAFANA_USER", "admin")
GRAFANA_PASS = os.getenv("GRAFANA_PASSWORD", "admin")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Push Grafana dashboards from JSON files via the REST API."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List dashboards that would be imported without actually pushing them.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Seconds to wait for Grafana to become healthy (default: 60).",
    )
    return parser.parse_args()


def get_auth_header() -> str:
    credentials = f"{GRAFANA_USER}:{GRAFANA_PASS}"
    encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
    return f"Basic {encoded}"


def wait_for_grafana(timeout: int = 60) -> bool:
    print(f"[*] Checking Grafana API health at {GRAFANA_URL}/api/health...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(f"{GRAFANA_URL}/api/health")
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    if data.get("database") == "ok":
                        print("[+] Grafana is healthy and ready.")
                        return True
        except Exception:
            pass
        time.sleep(2)
    print("[-] Timeout waiting for Grafana to become healthy.")
    return False


def import_dashboard(dashboard_path: str, dry_run: bool = False) -> bool:
    filename = os.path.basename(dashboard_path)

    with open(dashboard_path, "r", encoding="utf-8") as f:
        dashboard_content = json.load(f)

    title = dashboard_content.get("title", filename)

    if dry_run:
        print(f"[dry-run] Would import: '{title}' ({filename})")
        return True

    print(f"[*] Importing dashboard: {filename}...")
    payload = {
        "dashboard": dashboard_content,
        "overwrite": True,
        "folderId": 0,
        "message": "Automated import via bootstrap_dashboards.py"
    }

    req = urllib.request.Request(
        f"{GRAFANA_URL}/api/dashboards/db",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": get_auth_header(),
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                result = json.loads(resp.read().decode("utf-8"))
                uid = result.get("uid")
                url = result.get("url")
                print(f"[+] Successfully provisioned: '{dashboard_content.get('title')}'")
                print(f"    Dashboard UID: {uid} | Direct Link: {GRAFANA_URL}{url}")
                return True
            else:
                print(f"[-] Failed with HTTP status: {resp.status}")
                return False
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8")
        print(f"[-] HTTP Error {err.code}: {body}")
        return False
    except Exception as ex:
        print(f"[-] Error: {ex}")
        return False


def main():
    args = parse_args()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dashboards_dir = os.path.join(script_dir, "dashboards")

    if not args.dry_run and not wait_for_grafana(timeout=args.timeout):
        sys.exit(1)

    dashboard_files = glob.glob(os.path.join(dashboards_dir, "*.json"))
    if not dashboard_files:
        print(f"[-] No JSON dashboards found in {dashboards_dir}")
        sys.exit(1)

    print(f"[*] Found {len(dashboard_files)} dashboards to deploy.")
    if args.dry_run:
        print("[dry-run] No changes will be made to Grafana.")

    success_count = 0
    for file_path in dashboard_files:
        if import_dashboard(file_path, dry_run=args.dry_run):
            success_count += 1

    label = "listed" if args.dry_run else "active"
    print(f"\n[+] Done: {success_count}/{len(dashboard_files)} dashboards {label} in Grafana.")


if __name__ == "__main__":
    main()
