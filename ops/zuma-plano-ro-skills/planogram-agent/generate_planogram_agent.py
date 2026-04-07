#!/usr/bin/env python3
"""
Planogram Agent Generator — Paperclip
Full algorithm: adjusted avg per tier → ranking → gender-type assignment →
slot capacity (full/compact) → storage allocation → visual Excel → DB write.

Based on: step0.5-pre-planogram + step1-planogram algorithm docs.
"""

import argparse
import math
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import psycopg2

# ============================================================
# CONSTANTS
# ============================================================
PAIRS_PER_BOX = 12
NHOOKS = 7
HOOKS_PER_ARTICLE = {"jepit": 2, "fashion": 3}
COMPACT_HOOKS = {"jepit": 1, "fashion": 2}
PAIRS_PER_HOOK = {"jepit": 6, "fashion": 4}

# Tier priority: lower = must display first
TIER_PRIORITY = {"1": 1, "8": 2, "2": 3, "3": 4, "4": 99, "5": 99}
TIER_LABELS = {"1": "MUST DISPLAY", "8": "PRIORITY (New)", "2": "FILL IF SLOT", "3": "FILLER", "4": "DO NOT DISPLAY", "5": "DO NOT DISPLAY"}

JEPIT_SERIES = {"CLASSIC", "CLASSICEARTH", "CLASSIC EARTH", "BLACKSERIES", "BLACK SERIES", "STRIPE", "SJ-CLASSIC"}
SPECIAL_DISPLAY = {"LUCA", "LUNA", "AIRMOVE"}  # Table/VM only
NON_PRODUCTS = {"SHOPPING BAG", "HANGER", "PAPER BAG", "THERMAL", "BOX LUCA"}

SERIES_COLORS = {
    "ZORRO": "EAD1DC", "DALLAS": "E6B8AF", "SLIDE": "FFF2CC",
    "FLO": "F9CB9C", "PUFFY": "A4C2F4", "ELSA": "CCCCCC",
    "CLASSIC": "FFF2CC", "CLASSICEARTH": "F0E6C0", "CLASSIC EARTH": "F0E6C0",
    "BLACKSERIES": "D9D9D9", "BLACK SERIES": "D9D9D9", "STRIPE": "FFE0B2",
    "ONYX": "CFD8DC", "STITCH": "B4E7CE", "WEDGES": "D7CCC8",
    "LUCA": "FFCCBC", "AIRMOVE": "E0E0E0", "LUNA": "D5A6BD",
    "DISNEY": "FFAB91", "BATMAN": "90A4AE", "MICKEY": "FFCC80",
    "MICKEY & FRIENDS": "FFCC80", "POOH": "FFE082", "TOY STORY": "81D4FA",
    "WBB": "80DEEA", "VELCRO": "E8F5E9", "MERCI": "D9D2E9",
    "SPIDER-MAN": "CE93D8", "LOTSO": "F48FB1", "(KOSONG)": "F5F5F5",
}

STORE_LAYOUT_GSHEET = "1rQCC93t6f7HY1Dnoliplu2Mg61i-nnAupErn_U0fPhw"
DATA_OPTION_GSHEET = "1FweMqoNikHB7F9efH0xv5rOtpt4mxnuxqzbPqb41eCo"
DATA_OPTION_XLSX = "/tmp/data_option_jatim.xlsx"

THIN = Border(left=Side(style="thin"), right=Side(style="thin"),
              top=Side(style="thin"), bottom=Side(style="thin"))
CELL_ALIGN = Alignment(horizontal="center", vertical="center", wrap_text=True)

def get_color(series):
    s = series.upper().strip()
    if s in SERIES_COLORS: return SERIES_COLORS[s]
    for k, v in SERIES_COLORS.items():
        if k in s or s in k: return v
    import hashlib
    h = int(hashlib.md5(s.encode()).hexdigest()[:6], 16)
    return f"{180+(h%75):02x}{180+((h>>8)%75):02x}{180+((h>>16)%75):02x}"

def get_tipe(series):
    return "jepit" if series.upper().strip() in JEPIT_SERIES else "fashion"

def get_gender_type(gender, tipe):
    g = gender.upper().strip()
    t = tipe.lower().strip()
    if g in ("BABY", "BOYS", "GIRLS", "JUNIOR"):
        return "Baby & Kids"
    return f"{gender.title()} {tipe.title()}"

def get_db():
    return psycopg2.connect(
        host=os.environ.get("PGHOST", "76.13.194.120"),
        port=os.environ.get("PGPORT", "5432"),
        dbname=os.environ.get("PGDATABASE", "openclaw_ops"),
        user=os.environ.get("PGUSER", "openclaw_app"),
        password=os.environ.get("PGPASSWORD", ""),
    )

# ============================================================
# STEP 0.5: PULL & COMPUTE ADJUSTED AVERAGE
# ============================================================
def pull_monthly_sales(store_db, months=12):
    """Query monthly sales per kode_mix for the store."""
    conn = get_db()
    cur = conn.cursor()
    date_start = (datetime.now() - timedelta(days=months*30)).strftime("%Y-%m-%d")

    cur.execute("""
        SELECT kode_mix, article, gender, series,
               COALESCE(NULLIF(TRIM(tipe),''), 'Fashion') as tipe,
               COALESCE(NULLIF(TRIM(tier),''), '3') as tier,
               TO_CHAR(transaction_date, 'YYYY-MM') as bulan,
               SUM(quantity) as qty
        FROM core.sales_with_product
        WHERE UPPER(TRIM(matched_store_name)) = UPPER(TRIM(%s))
          AND transaction_date >= %s
          AND quantity > 0
          AND kode_mix IS NOT NULL
          AND (is_intercompany IS NULL OR is_intercompany = FALSE)
        GROUP BY kode_mix, article, gender, series, tipe, tier, bulan
        ORDER BY kode_mix, bulan
    """, (store_db, date_start))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    # Organize: {kode_mix: {meta, monthly: {bulan: qty}}}
    articles = {}
    for kode_mix, article, gender, series, tipe, tier, bulan, qty in rows:
        km = kode_mix.strip()
        if any(np in (article or "").upper() for np in NON_PRODUCTS):
            continue
        if km not in articles:
            articles[km] = {
                "kode_mix": km, "article": (article or km).strip(),
                "gender": (gender or "").strip(), "series": (series or "").strip(),
                "tipe": tipe.strip() if tipe else "Fashion",
                "tier": (tier or "3").strip(),
                "monthly": {}
            }
        articles[km]["monthly"][bulan] = articles[km]["monthly"].get(bulan, 0) + int(qty)

    print(f"Pulled {len(articles)} articles with monthly sales data")
    return articles

def compute_adjusted_avg(articles, months=12):
    """Compute tier-specific adjusted average."""
    for km, art in articles.items():
        monthly = art["monthly"]
        tier = art["tier"]
        values = list(monthly.values())
        all_months = sorted(monthly.keys())

        if not values:
            art["adj_avg"] = 0
            continue

        if tier == "1":
            # T1: exclude zero months (likely OOS)
            nonzero = [v for v in values if v > 0]
            art["adj_avg"] = sum(nonzero) / len(nonzero) if nonzero else 0

        elif tier == "8":
            # T8 (new launch): find first sale month, exclude pre-launch
            nonzero = [v for v in values if v > 0]
            art["adj_avg"] = sum(nonzero) / len(nonzero) if nonzero else 0

        elif tier in ("2", "3"):
            # T2/T3: include zeros (genuine decline), but exclude obvious OOS
            if len(values) >= 3:
                overall_avg = sum(values) / len(values)
                filtered = []
                for v in values:
                    if v == 0 and overall_avg > 5:
                        # Likely OOS if surrounding months are high
                        filtered.append(None)  # exclude
                    else:
                        filtered.append(v)
                actual = [v for v in filtered if v is not None]
                art["adj_avg"] = sum(actual) / len(actual) if actual else 0
            else:
                art["adj_avg"] = sum(values) / max(len(values), 1)

        else:
            # T4/T5: straight average, zeros included (genuinely slow)
            art["adj_avg"] = sum(values) / max(months, 1)

    # Compute total store sales for sales_mix
    total_avg = sum(a["adj_avg"] for a in articles.values())
    for art in articles.values():
        art["sales_mix"] = art["adj_avg"] / total_avg if total_avg > 0 else 0

    return articles

def compute_rekomendasi(articles, total_display_pairs):
    """Compute recommended box count proportional to sales mix."""
    for art in articles.values():
        reko_pairs = art["sales_mix"] * total_display_pairs
        reko_box = max(1, round(reko_pairs / PAIRS_PER_BOX))
        # Cap: T4/T5 get 0
        if art["tier"] in ("4", "5"):
            reko_box = 0
        art["reko_pairs"] = reko_pairs
        art["reko_box"] = reko_box
    return articles

# ============================================================
# BACKWALL CONFIG LOADER
# ============================================================
def ensure_cache(xlsx_path, gsheet_id):
    if os.path.exists(xlsx_path):
        age_hours = (datetime.now().timestamp() - os.path.getmtime(xlsx_path)) / 3600
        if age_hours < 24: return
    import subprocess
    subprocess.run(["curl", "-sL",
        f"https://docs.google.com/spreadsheets/d/{gsheet_id}/export?format=xlsx",
        "-o", xlsx_path], check=True)

def load_backwall_config(store_code, area):
    ensure_cache(DATA_OPTION_XLSX, DATA_OPTION_GSHEET)
    wb = openpyxl.load_workbook(DATA_OPTION_XLSX, data_only=True)
    sheet_name = f"{area} New" if f"{area} New" in wb.sheetnames else area
    if sheet_name not in wb.sheetnames:
        wb.close()
        return {"backwalls": [], "gondolas": [], "rak_baby": 0, "basket": 0, "meja": 0, "gudang": 0}

    ws = wb[sheet_name]
    store_col = None
    for search_row in [1, 2, 3]:
        for c in range(1, ws.max_column + 1):
            val = ws.cell(row=search_row, column=c).value
            if val and store_code.upper() in str(val).upper():
                store_col = c
                break
        if store_col: break

    if not store_col:
        wb.close()
        return {"backwalls": [], "gondolas": [], "rak_baby": 0, "basket": 0, "meja": 0, "gudang": 0}

    is_new = "new" in sheet_name.lower()
    config = {"backwalls": [], "gondolas": [], "rak_baby": 0, "basket": 0, "meja": 0, "gudang": 0}
    bw_idx = 0

    for r in range(3, ws.max_row + 1):
        label = str(ws.cell(row=r, column=1).value or "").strip().lower()
        if is_new:
            gender = str(ws.cell(row=r, column=store_col).value or "").strip()
            kategori = str(ws.cell(row=r, column=store_col + 1).value or "").strip()
            try: hooks = int(float(ws.cell(row=r, column=store_col + 2).value or 0))
            except: hooks = 0
        else:
            gender, kategori = "", ""
            try: hooks = int(float(ws.cell(row=r, column=store_col).value or 0))
            except: hooks = 0

        if "back wall" in label or "backwall" in label:
            bw_idx += 1
            if hooks > 0:
                config["backwalls"].append({"id": f"BW-{bw_idx}", "hooks": hooks, "gender": gender, "kategori": kategori})
        elif "gondola" in label and hooks > 0:
            config["gondolas"].append({"id": f"GD-{len(config['gondolas'])+1}", "hooks": hooks, "gender": gender, "kategori": kategori})
        elif "rak baby" in label: config["rak_baby"] = hooks
        elif "basket" in label: config["basket"] = hooks
        elif "meja" in label or "table" in label: config["meja"] = hooks
        elif "gudang" in label or "storage" in label: config["gudang"] = hooks

    wb.close()
    print(f"Config: {len(config['backwalls'])} BW, {len(config['gondolas'])} gondola, rak_baby={config['rak_baby']}, gudang={config['gudang']}")
    return config

# ============================================================
# STEP 1: ASSIGNMENT ALGORITHM
# ============================================================
def assign_planogram(articles, config):
    """Full assignment: special display → rak baby → gender-type optimization → backwall → storage."""
    art_list = [a for a in articles.values() if a["reko_box"] > 0]

    assigned = []    # (art, display_id, mode, zone)
    excluded = []    # (art, reason)
    warnings = []

    # Track what's been assigned (prevent duplication)
    assigned_kodes = set()
    storage_used = 0
    storage_cap = config.get("gudang", 0)

    # ── Phase 1: Luca/Luna/Airmove → Table/VM ──
    special_arts = [a for a in art_list if a["series"].upper() in SPECIAL_DISPLAY]
    table_slots = config.get("meja", 0)
    placed_special = 0
    for art in sorted(special_arts, key=lambda a: -a["adj_avg"]):
        if placed_special < table_slots:
            assigned.append((art, "TABLE DISPLAY", "full", art["series"]))
            assigned_kodes.add(art["kode_mix"])
            storage_used += 1  # 1 box backup per special article
            placed_special += 1
        else:
            if storage_cap == 0:
                excluded.append((art, "No Table/VM display + no storage"))
            else:
                excluded.append((art, "Table/VM display full"))
            assigned_kodes.add(art["kode_mix"])  # Don't try to assign to BW

    # ── Phase 2: Baby & Kids → Rak Baby ──
    baby_arts = [a for a in art_list if a["kode_mix"] not in assigned_kodes
                 and a["gender"].upper() in ("BABY", "BOYS", "GIRLS", "JUNIOR")]
    baby_arts.sort(key=lambda a: (-TIER_PRIORITY.get(a["tier"], 99), -a["adj_avg"]))

    rak_slots = config.get("rak_baby", 0) * 1  # 1 article per layer (full mode)
    basket_slots = config.get("basket", 0)
    placed_baby_rak = 0
    for art in baby_arts:
        if placed_baby_rak < rak_slots + basket_slots:
            display = "RAK BABY" if placed_baby_rak < rak_slots else "KERANJANG"
            assigned.append((art, display, "full", art["series"]))
            assigned_kodes.add(art["kode_mix"])
            placed_baby_rak += 1

    # ── Phase 3: Gender-type sales share → assign to BW/Gondola ──
    remaining = [a for a in art_list if a["kode_mix"] not in assigned_kodes]

    # Compute gender-type shares
    gt_sales = defaultdict(float)
    gt_articles = defaultdict(list)
    for art in remaining:
        gt = get_gender_type(art["gender"], get_tipe(art["series"]))
        gt_sales[gt] += art["adj_avg"]
        gt_articles[gt].append(art)

    # Sort gender-types by sales share desc
    gt_ranked = sorted(gt_sales.keys(), key=lambda g: -gt_sales[g])

    # Sort display units by hooks desc
    display_units = []
    for bw in config["backwalls"]:
        display_units.append(bw)
    for gd in config["gondolas"]:
        display_units.append(gd)
    display_units.sort(key=lambda u: -u["hooks"])

    # Assign gender-type → display unit
    # If config has gender/kategori hints, respect them; otherwise assign by sales share
    gt_to_display = {}  # gender_type → [display_unit]
    used_units = set()

    # First pass: respect existing config hints
    for unit in display_units:
        cfg_gender = unit.get("gender", "").lower()
        cfg_kat = unit.get("kategori", "").lower()
        if cfg_gender and cfg_kat:
            # Find matching gender-type
            for gt in gt_ranked:
                if gt in gt_to_display and len(gt_to_display[gt]) >= 2:
                    continue  # Don't over-assign
                gt_lower = gt.lower()
                gender_match = any(g in cfg_gender for g in gt_lower.split())
                kat_match = any(k in cfg_kat for k in ["jepit", "fashion"]) and any(k in gt_lower for k in ["jepit", "fashion"])
                baby_match = "baby" in cfg_gender and "baby" in gt_lower

                if gender_match and (kat_match or baby_match or "all" in cfg_kat):
                    gt_to_display.setdefault(gt, []).append(unit)
                    used_units.add(unit["id"])
                    break

    # Second pass: unassigned units → unassigned gender-types by sales share
    for gt in gt_ranked:
        if gt not in gt_to_display:
            for unit in display_units:
                if unit["id"] not in used_units:
                    gt_to_display[gt] = [unit]
                    used_units.add(unit["id"])
                    break

    # ── Phase 4: Assign articles to display units ──
    for gt, units in gt_to_display.items():
        arts = sorted(gt_articles.get(gt, []), key=lambda a: (-TIER_PRIORITY.get(a["tier"], 99) * -1, -a["adj_avg"]))
        # Sort: T1 first (priority 1), then T8 (2), then T2 (3), then T3 (4). Within tier, by adj_avg desc.
        arts.sort(key=lambda a: (TIER_PRIORITY.get(a["tier"], 99), -a["adj_avg"]))

        # Calculate total slots across all units for this gender-type
        total_hooks = sum(u["hooks"] for u in units)
        tipe = "jepit" if any("jepit" in gt.lower() for _ in [1]) else "fashion"
        # Detect tipe from articles
        if arts:
            tipe = get_tipe(arts[0]["series"])
        hpa = HOOKS_PER_ARTICLE.get(tipe, 2)
        slots_full = total_hooks // hpa

        # Count must-display (T1 + T8)
        must_display = [a for a in arts if a["tier"] in ("1", "8")]
        fillers = [a for a in arts if a["tier"] in ("2", "3")]

        # Decide mode
        if len(must_display) <= slots_full:
            mode = "full"
            to_place = must_display[:slots_full]
            remaining_slots = slots_full - len(to_place)
            to_place.extend(fillers[:remaining_slots])
        else:
            # Try compact mode
            hpa_compact = COMPACT_HOOKS.get(tipe, 1)
            slots_compact = total_hooks // hpa_compact
            if len(must_display) <= slots_compact and storage_cap > 0:
                mode = "compact"
                to_place = must_display[:slots_compact]
                remaining_slots = slots_compact - len(to_place)
                to_place.extend(fillers[:remaining_slots])
                # Storage impact
                compact_count = len(to_place)
                pairs_per_compact = PAIRS_PER_HOOK.get(tipe, 4)
                storage_used += math.ceil(compact_count * pairs_per_compact / PAIRS_PER_BOX)
            else:
                mode = "full"
                to_place = must_display[:slots_full]
                # Flag unplaced T1
                for a in must_display[slots_full:]:
                    warnings.append(f"T1/T8 not displayed: {a['kode_mix']} ({a['series']}) adj_avg={a['adj_avg']:.1f}")

        for art in to_place:
            if art["kode_mix"] not in assigned_kodes:
                # Determine which unit
                unit_id = units[0]["id"] if units else gt
                assigned.append((art, unit_id, mode, art["series"]))
                assigned_kodes.add(art["kode_mix"])

        # Exclude rest
        for art in arts:
            if art["kode_mix"] not in assigned_kodes:
                reason = "Display full" if art["tier"] in ("1", "8") else \
                         "Lower priority (T2/T3)" if art["tier"] in ("2", "3") else \
                         "Do not display (T4/T5)"
                excluded.append((art, reason))
                assigned_kodes.add(art["kode_mix"])

    # ── Phase 5: Catch unassigned (no matching display) ──
    for art in art_list:
        if art["kode_mix"] not in assigned_kodes:
            excluded.append((art, "No matching display unit for gender-type"))
            assigned_kodes.add(art["kode_mix"])

    # Storage summary
    storage_remaining = max(0, storage_cap - storage_used)
    print(f"Assignment: {len(assigned)} placed, {len(excluded)} excluded, {len(warnings)} warnings")
    print(f"Storage: used={storage_used} box, remaining={storage_remaining} box")
    for w in warnings[:5]:
        print(f"  WARNING: {w}")

    return assigned, excluded, warnings

# ============================================================
# VISUAL EXCEL (v4 format) — same as before but with mode info
# ============================================================
def build_stacked_grid(articles, hooks_per_article, nhooks=7):
    articles_per_col = nhooks // hooks_per_article
    boxes = []
    for art in articles:
        for i in range(art["reko_box"]):
            boxes.append((art, i))
    ncols = max(1, math.ceil(len(boxes) / articles_per_col)) if boxes else 1
    grid = [[None for _ in range(ncols)] for _ in range(nhooks)]
    bi = 0
    for col in range(ncols):
        for slot in range(articles_per_col):
            if bi >= len(boxes): break
            art, box_idx = boxes[bi]
            start_hook = slot * hooks_per_article
            for h in range(hooks_per_article):
                if start_hook + h < nhooks:
                    label = f"{art['kode_mix']}\n({art['series']})"
                    if box_idx == 0: label += f"\nx{art['reko_box']}box"
                    grid[start_hook + h][col] = (art["kode_mix"], art["series"], label)
            bi += 1
    return grid, ncols

def write_grid(ws, start_row, start_col, title, grid, ncols, nhooks):
    ZONE_FILL = PatternFill(start_color="2E75B6", end_color="2E75B6", fill_type="solid")
    COL_FILL = PatternFill(start_color="D6E4F0", end_color="D6E4F0", fill_type="solid")
    HOOK_FILL = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    r = start_row
    cell = ws.cell(row=r, column=start_col, value=title)
    cell.font = Font(bold=True, size=10, color="FFFFFF")
    cell.fill = ZONE_FILL
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.merge_cells(start_row=r, start_column=start_col, end_row=r, end_column=start_col + ncols)
    for cc in range(start_col, start_col + ncols + 1):
        ws.cell(row=r, column=cc).border = THIN
    r += 1
    ws.cell(row=r, column=start_col, value="").border = THIN
    for ci in range(ncols):
        cell = ws.cell(row=r, column=start_col + 1 + ci, value=f"Kol {ci+1}")
        cell.font = Font(bold=True, size=8)
        cell.fill = COL_FILL
        cell.alignment = CELL_ALIGN
        cell.border = THIN
    r += 1
    for ri in range(nhooks):
        cell = ws.cell(row=r + ri, column=start_col, value=f"Hook {ri+1}")
        cell.font = Font(size=8, italic=True)
        cell.alignment = CELL_ALIGN
        cell.border = THIN
        cell.fill = HOOK_FILL
        for ci in range(ncols):
            cell = ws.cell(row=r + ri, column=start_col + 1 + ci)
            cell.border = THIN
            cell.alignment = CELL_ALIGN
            if grid[ri][ci]:
                _, series, label = grid[ri][ci]
                cell.value = label
                cell.font = Font(size=7)
                hx = get_color(series)
                cell.fill = PatternFill(start_color=hx, end_color=hx, fill_type="solid")
            else:
                cell.value = "(KOSONG)"
                cell.font = Font(size=7, color="999999")
                cell.fill = PatternFill(start_color="F5F5F5", end_color="F5F5F5", fill_type="solid")
    return r + nhooks

def generate_excel(assigned, excluded, warnings, store_name, config, output_path):
    """Generate v4 visual Excel with 3 sheets."""
    wb = openpyxl.Workbook()
    HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    HEADER_FONT = Font(color="FFFFFF", bold=True, size=9)

    # ── Sheet 1: Layout Visual ──
    ws = wb.active
    ws.title = "Layout Visual"
    for ci in range(1, 50): ws.column_dimensions[get_column_letter(ci)].width = 18
    ws.column_dimensions['A'].width = 8

    ws.cell(row=1, column=1, value=f"LAYOUT PLANOGRAM — {store_name.upper()}").font = Font(bold=True, size=14)
    ws.cell(row=2, column=1, value=f"Generated by Plano-Agent — {datetime.now().strftime('%d %B %Y')}").font = Font(size=10, italic=True, color="666666")
    ws.cell(row=3, column=1, value="Full algorithm: adjusted avg per tier + tier-priority ranking + gender-type optimization").font = Font(size=8, color="888888")

    # Group by display unit
    bw_groups = defaultdict(list)
    for art, display_id, mode, zone in assigned:
        bw_groups[display_id].append(art)

    cur_row, cur_col, max_row = 5, 1, 5
    for bw in config["backwalls"] + config["gondolas"]:
        if bw["id"] not in bw_groups: continue
        arts = bw_groups[bw["id"]]
        tipe = get_tipe(arts[0]["series"]) if arts else "jepit"
        hpa = HOOKS_PER_ARTICLE.get(tipe, 2)
        grid, ncols = build_stacked_grid(arts, hpa, NHOOKS)
        total_box = sum(a["reko_box"] for a in arts)
        gender_info = f"{bw.get('gender','')} {bw.get('kategori','')}".strip()
        title = f"{bw['id']} — {gender_info} ({ncols}x{NHOOKS}, {len(arts)} SKU, {total_box} box)"
        end_row = write_grid(ws, cur_row, cur_col, title, grid, ncols, NHOOKS)
        max_row = max(max_row, end_row)
        cur_col += ncols + 3
        if cur_col > 30:
            cur_col = 1
            cur_row = max_row + 2

    # Baby/Table/Keranjang
    for special in ["RAK BABY", "KERANJANG", "TABLE DISPLAY"]:
        if special in bw_groups:
            arts = bw_groups[special]
            grid, ncols = build_stacked_grid(arts, 1, 2)
            total_box = sum(a["reko_box"] for a in arts)
            title = f"{special} ({len(arts)} SKU, {total_box} box)"
            cur_row = max_row + 2
            max_row = write_grid(ws, cur_row, 1, title, grid, ncols, 2)

    # ── Sheet 2: Summary ──
    ws2 = wb.create_sheet("Summary")
    ws2.column_dimensions['A'].width = 5
    ws2.column_dimensions['B'].width = 22
    ws2.column_dimensions['C'].width = 18
    ws2.column_dimensions['D'].width = 18
    ws2.column_dimensions['E'].width = 6
    ws2.column_dimensions['F'].width = 8
    ws2.column_dimensions['G'].width = 10

    ws2.cell(row=1, column=1, value=f"SUMMARY — {store_name.upper()}").font = Font(bold=True, size=14)
    ws2.cell(row=2, column=1, value=f"Generated by Plano-Agent — {datetime.now().strftime('%d %B %Y')}").font = Font(size=10, italic=True, color="666666")

    headers = ["No", "Zone", "Kode Artikel", "Series", "Tier", "Box", "Pairs"]
    for ci, h in enumerate(headers):
        cell = ws2.cell(row=4, column=ci+1, value=h)
        cell.font = HEADER_FONT; cell.fill = HEADER_FILL; cell.alignment = CELL_ALIGN; cell.border = THIN

    r, no = 5, 1
    grand_sku = grand_box = grand_pairs = 0
    zone_data = defaultdict(list)
    for art, display_id, mode, zone in assigned:
        zone_data[f"{display_id}: {zone}"].append(art)

    for zone_name, arts in zone_data.items():
        zone_start = r
        zone_box = zone_pairs = 0
        for art in arts:
            pairs = art["reko_box"] * PAIRS_PER_BOX
            ws2.cell(row=r, column=1, value=no).alignment = CELL_ALIGN; ws2.cell(row=r, column=1).border = THIN
            ws2.cell(row=r, column=2, value=zone_name).border = THIN
            ws2.cell(row=r, column=3, value=art["kode_mix"]).border = THIN; ws2.cell(row=r, column=3).font = Font(size=9)
            cell = ws2.cell(row=r, column=4, value=art["series"]); cell.border = THIN
            hx = get_color(art["series"]); cell.fill = PatternFill(start_color=hx, end_color=hx, fill_type="solid")
            ws2.cell(row=r, column=5, value=art["tier"]).alignment = CELL_ALIGN; ws2.cell(row=r, column=5).border = THIN
            ws2.cell(row=r, column=6, value=art["reko_box"]).alignment = CELL_ALIGN; ws2.cell(row=r, column=6).border = THIN
            ws2.cell(row=r, column=7, value=pairs).alignment = CELL_ALIGN; ws2.cell(row=r, column=7).border = THIN
            zone_box += art["reko_box"]; zone_pairs += pairs; no += 1; r += 1

        if len(arts) > 1:
            ws2.merge_cells(start_row=zone_start, start_column=2, end_row=r-1, end_column=2)
            ws2.cell(row=zone_start, column=2).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        sub_fill = PatternFill(start_color="E8E8E8", end_color="E8E8E8", fill_type="solid")
        for cc in range(1, 8): ws2.cell(row=r, column=cc).border = THIN; ws2.cell(row=r, column=cc).fill = sub_fill
        ws2.cell(row=r, column=2, value=f"Subtotal {zone_name}").font = Font(bold=True, size=9)
        ws2.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
        ws2.cell(row=r, column=6, value=zone_box).font = Font(bold=True, size=9); ws2.cell(row=r, column=6).alignment = CELL_ALIGN
        ws2.cell(row=r, column=7, value=zone_pairs).font = Font(bold=True, size=9); ws2.cell(row=r, column=7).alignment = CELL_ALIGN
        r += 1; grand_sku += len(arts); grand_box += zone_box; grand_pairs += zone_pairs

    # Grand total
    r += 1
    GT_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    GT_FONT = Font(bold=True, size=10, color="FFFFFF")
    for cc in range(1, 8): ws2.cell(row=r, column=cc).border = THIN; ws2.cell(row=r, column=cc).fill = GT_FILL
    ws2.cell(row=r, column=1, value="GRAND TOTAL").font = GT_FONT
    ws2.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
    ws2.cell(row=r, column=5, value=f"{grand_sku} SKU").font = GT_FONT; ws2.cell(row=r, column=5).fill = GT_FILL; ws2.cell(row=r, column=5).alignment = CELL_ALIGN
    ws2.cell(row=r, column=6, value=grand_box).font = GT_FONT; ws2.cell(row=r, column=6).alignment = CELL_ALIGN
    ws2.cell(row=r, column=7, value=grand_pairs).font = GT_FONT; ws2.cell(row=r, column=7).alignment = CELL_ALIGN

    # Excluded + Warnings
    if excluded:
        r += 3
        ws2.cell(row=r, column=1, value="EXCLUDED").font = Font(bold=True, size=11, color="CC0000"); r += 1
        EXC_FILL = PatternFill(start_color="CC0000", end_color="CC0000", fill_type="solid")
        for ci, h in enumerate(["No", "Kode Artikel", "Series", "Tier", "Adj Avg", "Box", "Alasan"]):
            cell = ws2.cell(row=r, column=ci+1, value=h)
            cell.font = Font(bold=True, size=9, color="FFFFFF"); cell.fill = EXC_FILL; cell.alignment = CELL_ALIGN; cell.border = THIN
        ws2.column_dimensions['G'].width = 30; r += 1
        for i, (art, reason) in enumerate(excluded):
            ws2.cell(row=r, column=1, value=i+1).alignment = CELL_ALIGN; ws2.cell(row=r, column=1).border = THIN
            ws2.cell(row=r, column=2, value=art["kode_mix"]).border = THIN
            cell = ws2.cell(row=r, column=3, value=art["series"]); cell.border = THIN
            hx = get_color(art["series"]); cell.fill = PatternFill(start_color=hx, end_color=hx, fill_type="solid")
            ws2.cell(row=r, column=4, value=art["tier"]).alignment = CELL_ALIGN; ws2.cell(row=r, column=4).border = THIN
            ws2.cell(row=r, column=5, value=round(art.get("adj_avg", 0), 1)).alignment = CELL_ALIGN; ws2.cell(row=r, column=5).border = THIN
            ws2.cell(row=r, column=6, value=art.get("reko_box", 0)).alignment = CELL_ALIGN; ws2.cell(row=r, column=6).border = THIN
            ws2.cell(row=r, column=7, value=reason).border = THIN; ws2.cell(row=r, column=7).font = Font(size=9, italic=True)
            r += 1

    # ── Sheet 3: Data Detail ──
    ws3 = wb.create_sheet("Data Detail")
    ws3.cell(row=1, column=1, value=f"DATA DETAIL — {store_name.upper()}").font = Font(bold=True, size=14)
    ws3.cell(row=2, column=1, value="Adjusted avg per tier + tier-priority ranking. Data stored in portal.planogram_paperclip.").font = Font(size=9, italic=True, color="666666")

    detail_headers = ["No", "Kode Artikel", "Gender", "Series", "Tipe", "Tier", "Priority",
                      "Adj Avg (pairs/mo)", "Sales Mix %", "Reko Pairs", "Reko Box",
                      "Status", "Zone / BW", "Mode", "Alasan"]
    widths = [5, 18, 10, 16, 10, 6, 16, 18, 12, 12, 10, 10, 18, 8, 30]
    for ci, h in enumerate(detail_headers):
        cell = ws3.cell(row=4, column=ci+1, value=h)
        cell.font = HEADER_FONT; cell.fill = HEADER_FILL; cell.alignment = CELL_ALIGN; cell.border = THIN
        ws3.column_dimensions[get_column_letter(ci+1)].width = widths[ci]

    r3, no3 = 5, 1
    # Placed
    for art, display_id, mode, zone in sorted(assigned, key=lambda x: (TIER_PRIORITY.get(x[0]["tier"], 99), -x[0]["adj_avg"])):
        ws3.cell(row=r3, column=1, value=no3).alignment = CELL_ALIGN; ws3.cell(row=r3, column=1).border = THIN
        ws3.cell(row=r3, column=2, value=art["kode_mix"]).border = THIN; ws3.cell(row=r3, column=2).font = Font(size=9)
        ws3.cell(row=r3, column=3, value=art["gender"]).border = THIN
        cell = ws3.cell(row=r3, column=4, value=art["series"]); cell.border = THIN
        hx = get_color(art["series"]); cell.fill = PatternFill(start_color=hx, end_color=hx, fill_type="solid")
        ws3.cell(row=r3, column=5, value=get_tipe(art["series"])).border = THIN
        ws3.cell(row=r3, column=6, value=art["tier"]).alignment = CELL_ALIGN; ws3.cell(row=r3, column=6).border = THIN
        ws3.cell(row=r3, column=7, value=TIER_LABELS.get(art["tier"], "")).border = THIN; ws3.cell(row=r3, column=7).font = Font(size=8)
        ws3.cell(row=r3, column=8, value=round(art["adj_avg"], 2)).alignment = CELL_ALIGN; ws3.cell(row=r3, column=8).border = THIN
        ws3.cell(row=r3, column=9, value=f"{art['sales_mix']*100:.2f}%").alignment = CELL_ALIGN; ws3.cell(row=r3, column=9).border = THIN
        ws3.cell(row=r3, column=10, value=round(art["reko_pairs"], 1)).alignment = CELL_ALIGN; ws3.cell(row=r3, column=10).border = THIN
        ws3.cell(row=r3, column=11, value=art["reko_box"]).alignment = CELL_ALIGN; ws3.cell(row=r3, column=11).border = THIN
        cs = ws3.cell(row=r3, column=12, value="PLACED"); cs.font = Font(size=9, bold=True, color="006100")
        cs.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid"); cs.alignment = CELL_ALIGN; cs.border = THIN
        ws3.cell(row=r3, column=13, value=f"{display_id}: {zone}").border = THIN
        ws3.cell(row=r3, column=14, value=mode).border = THIN
        ws3.cell(row=r3, column=15, value="").border = THIN
        no3 += 1; r3 += 1

    # Excluded
    for art, reason in sorted(excluded, key=lambda x: (TIER_PRIORITY.get(x[0]["tier"], 99), -x[0].get("adj_avg", 0))):
        ws3.cell(row=r3, column=1, value=no3).alignment = CELL_ALIGN; ws3.cell(row=r3, column=1).border = THIN
        ws3.cell(row=r3, column=2, value=art["kode_mix"]).border = THIN; ws3.cell(row=r3, column=2).font = Font(size=9)
        ws3.cell(row=r3, column=3, value=art["gender"]).border = THIN
        cell = ws3.cell(row=r3, column=4, value=art["series"]); cell.border = THIN
        hx = get_color(art["series"]); cell.fill = PatternFill(start_color=hx, end_color=hx, fill_type="solid")
        ws3.cell(row=r3, column=5, value=get_tipe(art["series"])).border = THIN
        ws3.cell(row=r3, column=6, value=art["tier"]).alignment = CELL_ALIGN; ws3.cell(row=r3, column=6).border = THIN
        ws3.cell(row=r3, column=7, value=TIER_LABELS.get(art["tier"], "")).border = THIN; ws3.cell(row=r3, column=7).font = Font(size=8)
        ws3.cell(row=r3, column=8, value=round(art.get("adj_avg", 0), 2)).alignment = CELL_ALIGN; ws3.cell(row=r3, column=8).border = THIN
        ws3.cell(row=r3, column=9, value=f"{art.get('sales_mix',0)*100:.2f}%").alignment = CELL_ALIGN; ws3.cell(row=r3, column=9).border = THIN
        ws3.cell(row=r3, column=10, value=round(art.get("reko_pairs", 0), 1)).alignment = CELL_ALIGN; ws3.cell(row=r3, column=10).border = THIN
        ws3.cell(row=r3, column=11, value=art.get("reko_box", 0)).alignment = CELL_ALIGN; ws3.cell(row=r3, column=11).border = THIN
        cs = ws3.cell(row=r3, column=12, value="EXCLUDED"); cs.font = Font(size=9, bold=True, color="9C0006")
        cs.fill = PatternFill(start_color="F4CCCC", end_color="F4CCCC", fill_type="solid"); cs.alignment = CELL_ALIGN; cs.border = THIN
        ws3.cell(row=r3, column=13, value="").border = THIN
        ws3.cell(row=r3, column=14, value="").border = THIN
        ws3.cell(row=r3, column=15, value=reason).border = THIN; ws3.cell(row=r3, column=15).font = Font(size=9, italic=True)
        no3 += 1; r3 += 1

    ws3.auto_filter.ref = f"A4:O{r3-1}"
    wb.save(output_path)
    print(f"Excel saved: {output_path}")
    return grand_sku, grand_box, grand_pairs

# ============================================================
# DB WRITE
# ============================================================
def write_to_db(assigned, excluded, store_db, area):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM portal.planogram_paperclip WHERE store_name = %s", (store_db,))
    print(f"Deleted {cur.rowcount} old rows for {store_db}")

    for art, display_id, mode, zone in assigned:
        cur.execute("""
            INSERT INTO portal.planogram_paperclip
            (store_name, gender, series, article, tier, article_mix, kode_kecil,
             grand_total_pairs, box, area, tipe, avg_sales_3mo, sales_mix,
             rekomendasi_pairs, rekomendasi_box, updated_at, generated_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),'paperclip-plano-agent')
        """, (store_db, art["gender"], art["series"], art["article"], art["tier"],
              art["kode_mix"], art["kode_mix"],
              str(art["reko_box"] * PAIRS_PER_BOX), str(art["reko_box"]),
              area, get_tipe(art["series"]),
              str(round(art["adj_avg"], 2)), str(round(art["sales_mix"], 6)),
              str(round(art["reko_pairs"], 1)), str(art["reko_box"])))

    conn.commit()
    print(f"Inserted {len(assigned)} rows for {store_db}")
    cur.close()
    conn.close()

# ============================================================
# MAIN
# ============================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--store-code", required=True)
    parser.add_argument("--store-name", required=True)
    parser.add_argument("--store-db", required=True)
    parser.add_argument("--area", default="Jatim")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    print(f"=== Planogram Agent: {args.store_name} ({args.store_code}) ===")

    # Step 0.5: Pull sales + compute adjusted avg
    articles = pull_monthly_sales(args.store_db, months=12)
    if not articles:
        print(f"ERROR: No sales data for {args.store_db}")
        sys.exit(1)

    articles = compute_adjusted_avg(articles)

    # Load config
    config = load_backwall_config(args.store_code, args.area)
    total_hooks = sum(bw["hooks"] for bw in config["backwalls"] + config["gondolas"])
    # Estimate total display pairs (rough: hooks * avg pairs per hook)
    total_display_pairs = total_hooks * 5  # ~5 pairs per hook average
    articles = compute_rekomendasi(articles, total_display_pairs)

    # Step 1: Assignment
    assigned, excluded, warnings = assign_planogram(articles, config)

    # Step 2: Generate Excel
    sku, box, pairs = generate_excel(assigned, excluded, warnings, args.store_name, config, args.output)
    print(f"Output: {sku} SKU, {box} box, {pairs} pairs")

    # Write to DB
    write_to_db(assigned, excluded, args.store_db, args.area)

    print(f"=== Done: {args.store_name} ===")

if __name__ == "__main__":
    main()
