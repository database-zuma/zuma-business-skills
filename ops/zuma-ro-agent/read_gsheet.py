#!/usr/bin/env python3
"""
Read data from a Google Sheet. Shared helper for picking list + SOPB generators.
Returns rows as list of dicts with column headers as keys.

Usage:
    from read_gsheet import read_gsheet_data
    rows = read_gsheet_data("SPREADSHEET_ID", "SheetName!A4:J100")
"""
import json
import os

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

TOKEN_FILE = os.path.expanduser("~/.config/gspread/authorized_user.json")
SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]


def get_sheets_service():
    with open(TOKEN_FILE) as f:
        td = json.load(f)
    creds = Credentials(
        token=td.get("token"),
        refresh_token=td.get("refresh_token"),
        token_uri=td.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=td.get("client_id"),
        client_secret=td.get("client_secret"),
        scopes=SCOPES,
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        td["token"] = creds.token
        with open(TOKEN_FILE, "w") as f:
            json.dump(td, f, indent=2)
    return build("sheets", "v4", credentials=creds)


def extract_spreadsheet_id(url_or_id):
    """Extract spreadsheet ID from URL or return as-is if already an ID."""
    if "/" in url_or_id:
        # URL format: https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit...
        parts = url_or_id.split("/d/")
        if len(parts) > 1:
            return parts[1].split("/")[0]
    return url_or_id


def read_gsheet_data(spreadsheet_id, range_name=None):
    """Read data from GSheet. Returns list of dicts (first row = headers).

    If range_name is None, reads the first sheet from A1:Z1000.
    """
    service = get_sheets_service()
    sid = extract_spreadsheet_id(spreadsheet_id)

    if range_name is None:
        # Get sheet names first
        meta = service.spreadsheets().get(spreadsheetId=sid, fields="sheets.properties.title").execute()
        first_sheet = meta["sheets"][0]["properties"]["title"]
        range_name = f"'{first_sheet}'!A1:Z1000"

    result = service.spreadsheets().values().get(
        spreadsheetId=sid, range=range_name
    ).execute()
    rows = result.get("values", [])

    if len(rows) < 2:
        return []

    headers = rows[0]
    data = []
    for row in rows[1:]:
        # Pad row to match header length
        padded = row + [""] * (len(headers) - len(row))
        data.append(dict(zip(headers, padded)))

    return data


def read_robox_actual_ro(spreadsheet_id):
    """Read ROBOX GSheet and return {kode_kecil: actual_ro_qty} dict.

    ROBOX columns (row 4 = headers):
    A=Kode Kecil, B=Artikel, C=Tier, D=Stock WHS, E=Stock LJBB,
    F=Stock Total, G=On-Hand, H=Planogram, I=Recomms RO, J=Actual RO
    """
    service = get_sheets_service()
    sid = extract_spreadsheet_id(spreadsheet_id)

    # Read from row 4 (headers) onwards
    result = service.spreadsheets().values().get(
        spreadsheetId=sid, range="A4:J500"
    ).execute()
    rows = result.get("values", [])

    if not rows:
        return {}

    headers = rows[0]
    data = {}
    for row in rows[1:]:
        if not row or not row[0] or row[0] == "TOTAL":
            continue
        padded = row + [""] * (len(headers) - len(row))
        kode = padded[0]  # Kode Kecil
        artikel = padded[1] if len(padded) > 1 else ""
        # Actual RO is column J (index 9)
        actual_ro = padded[9] if len(padded) > 9 else padded[8] if len(padded) > 8 else "0"
        try:
            qty = int(float(actual_ro)) if actual_ro else 0
        except (ValueError, TypeError):
            qty = 0
        if qty > 0:
            data[kode] = {"qty": qty, "artikel": artikel}

    return data


def read_picking_list_actual(spreadsheet_id, store_short):
    """Read Picking List GSheet and return {kode_kecil: actual_qty} dict.

    Picking list columns (from row after header):
    A=No, B=ARTIKEL (kode_kecil), C=NAMA ARTIKEL, D=empty, E=REQ, F=ACTUAL
    """
    service = get_sheets_service()
    sid = extract_spreadsheet_id(spreadsheet_id)

    # Get sheet names
    meta = service.spreadsheets().get(spreadsheetId=sid, fields="sheets.properties.title").execute()
    sheet_names = [s["properties"]["title"] for s in meta["sheets"]]

    # Find the matching store sheet
    target_sheet = None
    for name in sheet_names:
        if store_short.upper() in name.upper():
            target_sheet = name
            break

    if not target_sheet:
        return {}

    result = service.spreadsheets().values().get(
        spreadsheetId=sid, range=f"'{target_sheet}'!A10:F200"
    ).execute()
    rows = result.get("values", [])

    data = {}
    for row in rows:
        if not row or not row[0] or row[0] == "TOTAL":
            continue
        padded = row + [""] * (6 - len(row))
        kode = padded[1]  # ARTIKEL (kode_kecil)
        artikel = padded[2]  # NAMA ARTIKEL
        # REQ = col E (index 4), ACTUAL = col F (index 5)
        actual = padded[5] if padded[5] else padded[4]  # fallback to REQ if ACTUAL empty
        try:
            qty = int(float(actual)) if actual else 0
        except (ValueError, TypeError):
            qty = 0
        if qty > 0 and kode:
            data[kode] = {"qty": qty, "artikel": artikel}

    return data
