#!/usr/bin/env python3
"""
scripts/bootstrap_dashboards.py
Automated provisioning script that pushes enterprise production dashboards
into a running Grafana instance via its REST API.
"""

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


def import_dashboard(dashboard_path: str) -> bool:
    filename = os.path.basename(dashboard_path)
    print(f"[*] Importing dashboard: {filename}...")

    with open(dashboard_path, "r", encoding="utf-8") as f:
        dashboard_content = json.load(f)

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
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dashboards_dir = os.path.join(script_dir, "dashboards")

    if not wait_for_grafana(timeout=60):
        sys.exit(1)

    dashboard_files = glob.glob(os.path.join(dashboards_dir, "*.json"))
    if not dashboard_files:
        print(f"[-] No JSON dashboards found in {dashboards_dir}")
        sys.exit(1)

    print(f"[*] Found {len(dashboard_files)} dashboards to deploy.")
    success_count = 0
    for file_path in dashboard_files:
        if import_dashboard(file_path):
            success_count += 1

    print(f"\n[+] Provisioning complete: {success_count}/{len(dashboard_files)} dashboards active in Grafana.")


if __name__ == "__main__":
    main()
