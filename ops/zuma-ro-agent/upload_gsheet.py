#!/usr/bin/env python3
"""
Upload xlsx to Google Drive as Google Sheet, into a dedicated folder.
Uses service account credentials.

Usage:
    python3 upload_gsheet.py --file /path/to/file.xlsx [--folder "ROBOX/2026-03-31"]

Output: prints GSHEET_LINK=<url> on last line
"""
import argparse
import os
import sys

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import json

TOKEN_FILE = os.path.expanduser("~/.config/gspread/authorized_user.json")
SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]


def get_drive_service():
    with open(TOKEN_FILE) as f:
        token_data = json.load(f)
    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=SCOPES,
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_data["token"] = creds.token
        with open(TOKEN_FILE, "w") as f:
            json.dump(token_data, f, indent=2)
    return build("drive", "v3", credentials=creds)


def find_or_create_folder(drive, folder_path):
    """Find or create nested folder path (e.g. 'ROBOX/2026-03-31')."""
    parent_id = None  # root
    for part in folder_path.split("/"):
        q = f"name='{part}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            q += f" and '{parent_id}' in parents"
        results = drive.files().list(q=q, fields="files(id)", pageSize=1).execute()
        files = results.get("files", [])
        if files:
            parent_id = files[0]["id"]
        else:
            meta = {
                "name": part,
                "mimeType": "application/vnd.google-apps.folder",
            }
            if parent_id:
                meta["parents"] = [parent_id]
            folder = drive.files().create(body=meta, fields="id").execute()
            parent_id = folder["id"]
            pass  # folder created
    return parent_id


def upload_as_gsheet(drive, filepath, folder_id):
    """Upload xlsx as Google Sheet."""
    filename = os.path.splitext(os.path.basename(filepath))[0]  # strip .xlsx
    meta = {
        "name": filename,
        "mimeType": "application/vnd.google-apps.spreadsheet",  # convert to GSheet
    }
    if folder_id:
        meta["parents"] = [folder_id]

    media = MediaFileUpload(filepath, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    gsheet = drive.files().create(body=meta, media_body=media, fields="id,webViewLink").execute()

    return gsheet["id"], gsheet["webViewLink"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Path to xlsx file")
    parser.add_argument("--folder", default="ROBOX", help="GDrive folder path (e.g. ROBOX/2026-03-31)")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"File not found: {args.file}")
        sys.exit(1)

    drive = get_drive_service()

    print(f"Creating folder: {args.folder}")
    folder_id = find_or_create_folder(drive, args.folder)

    print(f"Uploading as GSheet: {os.path.basename(args.file)}")
    file_id, link = upload_as_gsheet(drive, args.file, folder_id)

    print(f"File ID: {file_id}")
    print(f"GSHEET_LINK={link}")


if __name__ == "__main__":
    main()
