#!/usr/bin/env python3
"""
FF/FA/FS Daily Fill Rate Calculator

Reads planogram from portal.temp_portal_plannogram + stock from core.stock_with_product.
Calculates FF, FA, FS per store. Inserts into mart.ff_fa_fs_daily.
Writes status JSON to logs directory for Atlas monitoring.

Usage:
    # From VPS (localhost DB, after stock ETL):
    /opt/openclaw/venv/bin/python3 /opt/openclaw/scripts/calculate_ff_fa_fs.py

    # From Mac Mini (remote DB, manual run):
    python3 calculate_ff_fa_fs.py --db-host 76.13.194.120

    # Dry run (calculate + print, don't insert):
    python3 calculate_ff_fa_fs.py --dry-run
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone, timedelta

import re

import psycopg2
import psycopg2.extras

# ==============================================================================
# CONFIG
# ==============================================================================

WIB = timezone(timedelta(hours=7))

DB_DEFAULTS = {
    "host": "127.0.0.1",
    "port": "5432",
    "dbname": "openclaw_ops",
    "user": "openclaw_app",
    "password": os.getenv("OPENCLAW_DB_PASS", ""),
}

LOG_DIR = "/opt/openclaw/logs"


# ==============================================================================
# SIZE COLUMN MAPPING
# ==============================================================================


def build_size_map(planogram_columns):
    """
    Dynamically build size mapping from planogram columns.

    Rules:
    - Column 'size_X_Y' (e.g., size_39_40) -> stock size 'X/Y' (e.g., '39/40')
    - Column 'size_X' (e.g., size_39) -> stock size 'X' (e.g., '39')

    Only includes columns that actually exist in the planogram table.
    """
    size_map = {}  # {planogram_col_name: stock_size_value}

    for col in planogram_columns:
        if not col.startswith("size_"):
            continue
        suffix = col[5:]  # strip 'size_' prefix

        # Check if it's a paired column: digits_digits
        parts = suffix.split("_")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            # Paired: size_39_40 -> '39/40'
            size_map[col] = f"{parts[0]}/{parts[1]}"
        elif len(parts) == 1 and parts[0].isdigit():
            # Individual: size_39 -> '39'
            size_map[col] = parts[0]

    return size_map


# ==============================================================================
# STORE MAP AUTO-SYNC
# ==============================================================================


def _normalize(name):
    return re.sub(r"\s+", " ", name.lower().strip())


def _word_set(name):
    words = _normalize(name).split()
    return set(w for w in words if w != "zuma")


def _find_best_match(plano_name, stock_names):
    """
    Try to match a planogram store name to a stock nama_gudang.

    Strategy (ordered by confidence):
    1. Exact match (case-insensitive)
    2. One is substring of the other (single candidate only)
    3. High word overlap >= 75% (single candidate only)

    Returns (stock_name, match_method) or (None, None).
    """
    plano_norm = _normalize(plano_name)

    # --- Pass 1: Exact match ---
    for stock in stock_names:
        if _normalize(stock) == plano_norm:
            return stock, "auto_exact"

    # --- Pass 2: Substring match (one contains the other) ---
    substring_candidates = []
    for stock in stock_names:
        stock_norm = _normalize(stock)
        if plano_norm in stock_norm or stock_norm in plano_norm:
            substring_candidates.append(stock)

    if len(substring_candidates) == 1:
        return substring_candidates[0], "auto_fuzzy"

    # --- Pass 3: Word overlap >= 75% ---
    plano_words = _word_set(plano_name)
    if not plano_words:
        return None, None

    overlap_candidates = []
    for stock in stock_names:
        stock_words = _word_set(stock)
        if not stock_words:
            continue
        # Overlap relative to the SMALLER set (planogram names are usually shorter)
        smaller = min(len(plano_words), len(stock_words))
        if smaller == 0:
            continue
        overlap = len(plano_words & stock_words) / smaller
        if overlap >= 0.75:
            overlap_candidates.append((stock, overlap))

    if len(overlap_candidates) == 1:
        return overlap_candidates[0][0], "auto_fuzzy"

    return None, None


def _lookup_branch(conn, stock_nama_gudang):
    cur = conn.cursor()
    cur.execute(
        "SELECT branch FROM portal.store WHERE LOWER(TRIM(nama_accurate)) = LOWER(TRIM(%s)) LIMIT 1",
        (stock_nama_gudang,),
    )
    row = cur.fetchone()
    cur.close()
    if row and row[0]:
        return row[0].strip()

    cur = conn.cursor()
    cur.execute(
        "SELECT branch FROM portal.store WHERE LOWER(TRIM(nama_department_old)) = LOWER(TRIM(%s)) LIMIT 1",
        (stock_nama_gudang,),
    )
    row = cur.fetchone()
    cur.close()
    return row[0].strip() if row and row[0] else None


def sync_store_map(conn):
    """
    Auto-sync portal.store_name_map from planogram vs stock data.

    - New planogram stores get auto-matched (exact → fuzzy) and inserted.
    - Existing mappings are NEVER overwritten (preserves manual overrides).
    - Unmapped stores are returned for logging/alerting.
    """
    cur = conn.cursor()

    cur.execute("SELECT planogram_name FROM portal.store_name_map")
    existing = set(row[0] for row in cur.fetchall())

    cur.execute(
        "SELECT DISTINCT store_name FROM portal.temp_portal_plannogram WHERE store_name IS NOT NULL"
    )
    plano_stores = [row[0] for row in cur.fetchall()]

    cur.execute(
        "SELECT DISTINCT nama_gudang FROM core.stock_with_product WHERE nama_gudang IS NOT NULL"
    )
    stock_names = [row[0] for row in cur.fetchall()]

    cur.close()

    new_stores = [s for s in plano_stores if s not in existing]
    if not new_stores:
        return [], []

    auto_matched = []
    unmapped = []

    for plano_name in new_stores:
        stock_name, method = _find_best_match(plano_name, stock_names)
        if stock_name:
            branch = _lookup_branch(conn, stock_name)
            auto_matched.append(
                {
                    "planogram_name": plano_name,
                    "stock_nama_gudang": stock_name,
                    "branch": branch or "",
                    "match_method": method,
                }
            )
        else:
            unmapped.append(plano_name)

    # ON CONFLICT DO NOTHING preserves manual overrides
    if auto_matched:
        cur = conn.cursor()
        for m in auto_matched:
            cur.execute(
                """
                INSERT INTO portal.store_name_map
                    (planogram_name, stock_nama_gudang, branch, match_method, updated_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (planogram_name) DO NOTHING
                """,
                (
                    m["planogram_name"],
                    m["stock_nama_gudang"],
                    m["branch"],
                    m["match_method"],
                ),
            )
        conn.commit()
        cur.close()

    return auto_matched, unmapped


# ==============================================================================
# DATA LOADING
# ==============================================================================


def load_store_map(conn):
    """Load planogram->stock store name mapping from portal.store_name_map."""
    cur = conn.cursor()
    cur.execute(
        "SELECT planogram_name, stock_nama_gudang, branch FROM portal.store_name_map"
    )
    rows = cur.fetchall()
    cur.close()

    store_map = {}  # planogram_name -> {db_name, branch}
    for plano, db_name, branch in rows:
        store_map[plano] = {"db_name": db_name, "branch": branch}

    return store_map


def load_planogram(conn):
    """Load planogram from portal.temp_portal_plannogram."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM portal.temp_portal_plannogram")
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    cur.close()
    return rows, columns


def load_stock(conn, store_db_names):
    """
    Load current stock snapshot from core.stock_with_product.
    Returns dict: (nama_gudang_lower, kode_mix_lower, size) -> total_quantity
    """
    placeholders = ",".join(["%s"] * len(store_db_names))
    query = f"""
        SELECT nama_gudang, kode_mix, size, SUM(quantity) AS qty
        FROM core.stock_with_product
        WHERE nama_gudang IN ({placeholders})
          AND quantity IS NOT NULL
        GROUP BY nama_gudang, kode_mix, size
    """
    cur = conn.cursor()
    cur.execute(query, store_db_names)
    rows = cur.fetchall()
    cur.close()

    stock = {}
    for nama_gudang, kode_mix, size, qty in rows:
        if kode_mix is None or size is None:
            continue
        key = (nama_gudang.lower().strip(), kode_mix.lower().strip(), size.strip())
        stock[key] = int(qty) if qty else 0

    return stock


# ==============================================================================
# CALCULATION
# ==============================================================================


def calculate_all(planogram_rows, plano_columns, size_map, stock, store_map):
    """
    Calculate FF, FA, FS per store.

    Returns list of dicts:
    [{"store_label": ..., "store_db_name": ..., "branch": ..., "ff": ..., "fa": ..., "fs": ...}, ...]
    """
    # Accumulators per store_label
    stores = {}  # store_label -> {plan_pos, stock_pos, art_plan, art_stock, total_plan, total_stock}

    unmapped_stores = set()

    for row in planogram_rows:
        store_label = row["store_name"]
        if store_label is None:
            continue

        mapping = store_map.get(store_label)
        if not mapping:
            unmapped_stores.add(store_label)
            continue

        db_name = mapping["db_name"]
        article_mix = row["article_mix"]
        if article_mix is None:
            continue
        article_mix_lower = article_mix.strip().lower()

        if store_label not in stores:
            stores[store_label] = {
                "db_name": db_name,
                "branch": mapping["branch"],
                "plan_pos": 0,
                "stock_pos": 0,
                "art_plan": 0,
                "art_stock": 0,
                "total_plan": 0,
                "total_stock": 0,
            }

        acc = stores[store_label]
        article_total_plan = 0
        article_total_stock = 0

        for plano_col, stock_size in size_map.items():
            raw_val = row[plano_col] if plano_col in dict(row).keys() else None
            plan_qty = 0
            if raw_val is not None and str(raw_val).strip() != "":
                try:
                    plan_qty = max(0, round(float(raw_val)))
                except (ValueError, TypeError):
                    plan_qty = 0

            # Look up stock
            stock_key = (db_name.lower().strip(), article_mix_lower, stock_size)
            stock_qty = stock.get(stock_key, 0)

            article_total_plan += plan_qty
            article_total_stock += stock_qty

            # FF counters (size-level)
            if plan_qty > 0:
                acc["plan_pos"] += 1
                if stock_qty > 0:
                    acc["stock_pos"] += 1

        acc["total_plan"] += article_total_plan
        acc["total_stock"] += article_total_stock

        # FA counters (article-level)
        if article_total_plan > 0:
            acc["art_plan"] += 1
            if article_total_stock > 0:
                acc["art_stock"] += 1

    if unmapped_stores:
        print(
            f"  WARNING: {len(unmapped_stores)} stores not in portal.store_name_map: {unmapped_stores}"
        )

    # Calculate metrics
    results = []
    for store_label, acc in sorted(stores.items()):
        ff = round(acc["stock_pos"] / acc["plan_pos"], 4) if acc["plan_pos"] > 0 else 0
        fa = round(acc["art_stock"] / acc["art_plan"], 4) if acc["art_plan"] > 0 else 0
        fs = (
            round(acc["total_stock"] / acc["total_plan"], 4)
            if acc["total_plan"] > 0
            else 0
        )

        results.append(
            {
                "store_label": store_label,
                "store_db_name": acc["db_name"],
                "branch": acc["branch"],
                "ff": ff,
                "fa": fa,
                "fs": fs,
            }
        )

    return results


# ==============================================================================
# INSERT
# ==============================================================================


def insert_results(conn, results, report_date):
    """Insert results into mart.ff_fa_fs_daily. Upsert on conflict."""
    cur = conn.cursor()
    query = """
        INSERT INTO mart.ff_fa_fs_daily (report_date, branch, store_label, store_db_name, ff, fa, fs)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_date, store_db_name)
        DO UPDATE SET
            ff = EXCLUDED.ff,
            fa = EXCLUDED.fa,
            fs = EXCLUDED.fs,
            calculated_at = NOW()
    """
    for r in results:
        cur.execute(
            query,
            (
                report_date,
                r["branch"],
                r["store_label"],
                r["store_db_name"],
                r["ff"],
                r["fa"],
                r["fs"],
            ),
        )
    conn.commit()
    cur.close()


# ==============================================================================
# STATUS LOG
# ==============================================================================


def write_status(
    results, report_date, duration_sec, error_msg=None, unmapped_stores=None
):
    if not os.path.isdir(LOG_DIR):
        return

    status = {
        "job": "ff_fa_fs_daily",
        "report_date": str(report_date),
        "calculated_at": datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S WIB"),
        "status": "error" if error_msg else "success",
        "duration_seconds": round(duration_sec, 1),
        "stores_calculated": len(results) if results else 0,
        "error_message": error_msg or "",
    }

    if results:
        status["summary"] = {
            "avg_ff": round(sum(r["ff"] for r in results) / len(results) * 100, 1),
            "avg_fa": round(sum(r["fa"] for r in results) / len(results) * 100, 1),
            "avg_fs": round(sum(r["fs"] for r in results) / len(results) * 100, 1),
            "stores_below_ff_70": sum(1 for r in results if r["ff"] < 0.70),
        }

    if unmapped_stores:
        status["unmapped_stores"] = unmapped_stores

    filepath = os.path.join(LOG_DIR, "ff_fa_fs_latest_status.json")
    with open(filepath, "w") as f:
        json.dump(status, f, indent=2)

    # Also write dated log
    dated_path = os.path.join(
        LOG_DIR, f"ff_fa_fs_{report_date.strftime('%Y%m%d')}.json"
    )
    with open(dated_path, "w") as f:
        json.dump(status, f, indent=2)


# ==============================================================================
# MAIN
# ==============================================================================


def main():
    parser = argparse.ArgumentParser(description="FF/FA/FS Daily Calculator")
    parser.add_argument("--db-host", default=DB_DEFAULTS["host"])
    parser.add_argument("--db-port", default=DB_DEFAULTS["port"])
    parser.add_argument("--db-name", default=DB_DEFAULTS["dbname"])
    parser.add_argument("--db-user", default=DB_DEFAULTS["user"])
    parser.add_argument("--db-pass", default=DB_DEFAULTS["password"])
    parser.add_argument(
        "--dry-run", action="store_true", help="Calculate + print, don't insert"
    )
    args = parser.parse_args()

    start = datetime.now(WIB)
    report_date = start.date()

    print("=" * 60)
    print("  FF/FA/FS Daily Calculator")
    print(f"  Date: {report_date}  |  Started: {start.strftime('%H:%M:%S WIB')}")
    print("=" * 60)

    results = None
    unmapped = []
    try:
        conn = psycopg2.connect(
            host=args.db_host,
            port=args.db_port,
            dbname=args.db_name,
            user=args.db_user,
            password=args.db_pass,
        )
        print(f"\n  DB connected: {args.db_host}")

        print("  Syncing store name map...")
        auto_matched, unmapped = sync_store_map(conn)
        if auto_matched:
            for m in auto_matched:
                print(
                    f"    NEW {m['match_method']}: '{m['planogram_name']}' -> '{m['stock_nama_gudang']}' [{m['branch']}]"
                )
        if unmapped:
            print(f"    UNMAPPED ({len(unmapped)}): {unmapped}")

        store_map = load_store_map(conn)
        print(f"  Store mappings: {len(store_map)} stores")

        # Load planogram
        print("  Loading planogram...")
        plano_rows, plano_cols = load_planogram(conn)
        print(f"  Planogram: {len(plano_rows)} rows")

        # Build size map from actual columns
        size_map = build_size_map(plano_cols)
        print(
            f"  Size columns: {len(size_map)} ({sum(1 for v in size_map.values() if '/' in v)} paired, {sum(1 for v in size_map.values() if '/' not in v)} individual)"
        )

        # Load stock
        store_db_names = [m["db_name"] for m in store_map.values()]
        print("  Loading stock...")
        stock = load_stock(conn, store_db_names)
        print(f"  Stock entries: {len(stock):,}")

        # Calculate
        print("\n  Calculating FF/FA/FS...")
        results = calculate_all(plano_rows, plano_cols, size_map, stock, store_map)

        # Print results
        print(f"\n  {'Store':<35s} {'FF':>7s} {'FA':>7s} {'FS':>7s}")
        print(f"  {'-' * 35} {'-' * 7} {'-' * 7} {'-' * 7}")
        for r in results:
            print(
                f"  {r['store_label']:<35s} {r['ff'] * 100:>6.1f}% {r['fa'] * 100:>6.1f}% {r['fs'] * 100:>6.1f}%"
            )

        # Averages
        if results:
            avg_ff = sum(r["ff"] for r in results) / len(results)
            avg_fa = sum(r["fa"] for r in results) / len(results)
            avg_fs = sum(r["fs"] for r in results) / len(results)
            print(f"  {'-' * 35} {'-' * 7} {'-' * 7} {'-' * 7}")
            print(
                f"  {'AVG':<35s} {avg_ff * 100:>6.1f}% {avg_fa * 100:>6.1f}% {avg_fs * 100:>6.1f}%"
            )

        # Insert
        if not args.dry_run and results:
            print(f"\n  Inserting {len(results)} rows into mart.ff_fa_fs_daily...")
            insert_results(conn, results, report_date)
            print("  Done.")
        elif args.dry_run:
            print("\n  [DRY RUN] Skipping insert.")

        conn.close()
        duration = (datetime.now(WIB) - start).total_seconds()
        print(f"\n  Completed in {duration:.1f}s")
        write_status(results, report_date, duration, unmapped_stores=unmapped)

    except Exception as e:
        duration = (datetime.now(WIB) - start).total_seconds()
        print(f"\n  ERROR: {e}", file=sys.stderr)
        write_status(results, report_date, duration, str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
