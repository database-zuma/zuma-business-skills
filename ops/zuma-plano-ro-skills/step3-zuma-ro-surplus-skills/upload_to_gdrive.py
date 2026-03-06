#!/usr/bin/env python3
"""
Upload file to Google Drive and set sharing: anyone with link = editor.

Uses GWS CLI (primary) or Google API Python client (fallback).

Usage:
    python3 upload_to_gdrive.py --file /path/to/file.xlsx
    python3 upload_to_gdrive.py --file /path/to/file.xlsx --folder "Zuma RO Requests"

Output: prints the shareable GDrive link on the last line as GDRIVE_LINK=<url>
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

# ── config ────────────────────────────────────────────────────────────
DEFAULT_FOLDER = "Zuma RO Requests"
GWS_BIN = shutil.which("gws") or os.path.expanduser("~/bin/gws")


# ══════════════════════════════════════════════════════════════════════
#  METHOD 1: GWS CLI (primary — already authenticated, no setup needed)
# ══════════════════════════════════════════════════════════════════════


def gws_available():
    """Check if gws CLI is installed and authenticated."""
    if not os.path.exists(GWS_BIN):
        return False
    try:
        r = subprocess.run(
            [
                GWS_BIN,
                "drive",
                "files",
                "list",
                "--params",
                '{"pageSize": 1, "fields": "files(id)"}',
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return r.returncode == 0 and "files" in r.stdout
    except Exception:
        return False


def gws_run(args_list):
    """Run a gws command and return parsed JSON output."""
    r = subprocess.run(
        [GWS_BIN] + args_list,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if r.returncode != 0:
        raise RuntimeError(f"gws error: {r.stderr.strip() or r.stdout.strip()}")
    return json.loads(r.stdout)


def gws_find_or_create_folder(folder_name):
    """Find or create a GDrive folder. Returns folder ID."""
    q = f'name="{folder_name}" and mimeType="application/vnd.google-apps.folder" and trashed=false'
    result = gws_run(
        [
            "drive",
            "files",
            "list",
            "--params",
            json.dumps({"q": q, "fields": "files(id,name)", "pageSize": 1}),
        ]
    )
    files = result.get("files", [])
    if files:
        fid = files[0]["id"]
        print(f"  Using existing folder: {folder_name} ({fid})")
        return fid

    # Create
    result = gws_run(
        [
            "drive",
            "files",
            "create",
            "--json",
            json.dumps(
                {"name": folder_name, "mimeType": "application/vnd.google-apps.folder"}
            ),
            "--params",
            '{"fields": "id,name"}',
        ]
    )
    fid = result["id"]
    print(f"  Created folder: {folder_name} ({fid})")

    # Share folder
    gws_set_anyone_editor(fid)
    return fid


def gws_upload(file_path, folder_id):
    """Upload file to GDrive folder. Returns file ID and webViewLink."""
    file_name = os.path.basename(file_path)
    result = gws_run(
        [
            "drive",
            "files",
            "create",
            "--upload",
            file_path,
            "--json",
            json.dumps({"name": file_name, "parents": [folder_id]}),
            "--params",
            '{"fields": "id,name,webViewLink"}',
        ]
    )
    print(f"  Uploaded: {file_name} ({result['id']})")
    return result["id"], result.get("webViewLink", "")


def gws_set_anyone_editor(file_id):
    """Set sharing: anyone with link = editor."""
    gws_run(
        [
            "drive",
            "permissions",
            "create",
            "--params",
            json.dumps({"fileId": file_id, "fields": "id,role,type"}),
            "--json",
            '{"type": "anyone", "role": "writer"}',
        ]
    )


def upload_via_gws(file_path, folder_name):
    """Full upload flow using GWS CLI. Returns shareable link."""
    folder_id = gws_find_or_create_folder(folder_name)
    file_id, link = gws_upload(file_path, folder_id)
    gws_set_anyone_editor(file_id)
    print("  Sharing set: anyone with link = editor")

    # If webViewLink wasn't in create response, fetch it
    if not link:
        result = gws_run(
            [
                "drive",
                "files",
                "get",
                "--params",
                json.dumps({"fileId": file_id, "fields": "webViewLink"}),
            ]
        )
        link = result.get(
            "webViewLink", f"https://drive.google.com/file/d/{file_id}/view"
        )

    return link


# ══════════════════════════════════════════════════════════════════════
#  METHOD 2: Python Google API (fallback)
# ══════════════════════════════════════════════════════════════════════

SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = os.path.expanduser(
    "~/.openclaw/workspace/google-oauth-credentials.json"
)
TOKEN_FILE = os.path.expanduser("~/.openclaw/workspace/google-drive-token.json")


def upload_via_python_api(file_path, folder_name):
    """Full upload flow using google-api-python-client. Returns shareable link."""
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        print("  FALLBACK FAILED: google-api-python-client not installed.")
        print(
            "  Run: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"
        )
        sys.exit(1)

    # Auth
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"  ERROR: No credentials at {CREDENTIALS_FILE}")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    service = build("drive", "v3", credentials=creds)

    # Find or create folder
    q = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q=q, spaces="drive", fields="files(id)").execute()
    files = results.get("files", [])
    if files:
        folder_id = files[0]["id"]
        print(f"  Using existing folder: {folder_name}")
    else:
        folder = (
            service.files()
            .create(
                body={
                    "name": folder_name,
                    "mimeType": "application/vnd.google-apps.folder",
                },
                fields="id",
            )
            .execute()
        )
        folder_id = folder["id"]
        print(f"  Created folder: {folder_name}")
        service.permissions().create(
            fileId=folder_id,
            body={"type": "anyone", "role": "writer"},
            fields="id",
        ).execute()

    # Upload
    file_name = os.path.basename(file_path)
    media = MediaFileUpload(file_path, resumable=True)
    uploaded = (
        service.files()
        .create(
            body={"name": file_name, "parents": [folder_id]},
            media_body=media,
            fields="id,webViewLink",
        )
        .execute()
    )
    file_id = uploaded["id"]
    print(f"  Uploaded: {file_name}")

    # Share
    service.permissions().create(
        fileId=file_id,
        body={"type": "anyone", "role": "writer"},
        fields="id",
    ).execute()
    print("  Sharing set: anyone with link = editor")

    link = uploaded.get(
        "webViewLink", f"https://drive.google.com/file/d/{file_id}/view"
    )
    return link


# ══════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(
        description="Upload to Google Drive (anyone with link = editor)"
    )
    parser.add_argument("--file", required=True, help="Path to file to upload")
    parser.add_argument(
        "--folder",
        default=DEFAULT_FOLDER,
        help=f"GDrive folder name (default: '{DEFAULT_FOLDER}')",
    )
    args = parser.parse_args()

    file_path = os.path.expanduser(args.file)
    if not os.path.exists(file_path):
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)

    file_size = os.path.getsize(file_path)
    print(f"\n{'=' * 60}")
    print(f"  GOOGLE DRIVE UPLOAD")
    print(f"  File: {os.path.basename(file_path)} ({file_size:,} bytes)")
    print(f"  Folder: {args.folder}")
    print(f"{'=' * 60}")

    # Try GWS CLI first, fallback to Python API
    if gws_available():
        print(f"\n  [Method: gws CLI]")
        link = upload_via_gws(file_path, args.folder)
    else:
        print(f"\n  [Method: Python Google API (gws not found)]")
        link = upload_via_python_api(file_path, args.folder)

    print(f"\n{'=' * 60}")
    print(f"  ✅ UPLOAD COMPLETE")
    print(f"  Link: {link}")
    print(f"  Sharing: Anyone with link = Editor")
    print(f"{'=' * 60}\n")

    # Last line: machine-parseable link
    print(f"GDRIVE_LINK={link}")


if __name__ == "__main__":
    main()
