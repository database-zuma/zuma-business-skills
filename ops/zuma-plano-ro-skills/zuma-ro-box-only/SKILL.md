---
name: zuma-ro-box-only
description: Zuma RO Box-Only — RO triggered by Max Stock (planogram + storage_new) vs On Hand selisih. Box-only, no protol. Jatim only (temp_portal_plannogram). T4 included, T5/T6/T7 excluded.
user-invocable: true
---

# Zuma RO Box-Only

## Overview

RO Box-Only untuk toko Jatim (11 toko). Logic: hitung **Max Stock** per artikel → bandingkan dengan **On Hand** → jika kurang, RO selisihnya dalam satuan Box.

**Changelog:**
- v2 (2026-02-25): Logic diganti dari "≥50% size variations kosong" → "Max Stock vs On Hand selisih"
- v2 juga: T4 sekarang included, WH Qty split DDD/LJBB, Box Qty = ceil(selisih/12)

---

## Data Source

### Table: `portal.temp_portal_plannogram`

Tabel temporary planogram untuk 11 toko Jatim.

**Key Columns:**
| Column | Type | Description |
|--------|------|-------------|
| `store_name` | text | Nama toko (e.g., "Zuma Royal Plaza") |
| `gender` | text | MEN / WOMEN / KIDS |
| `series` | text | Nama series (AIRMOVE, CHRONOS, dll) |
| `article` | text | Full article name |
| `tier` | text | Tier: '1','2','3','4','8' |
| `article_mix` | text | Kode Mix (UPPERCASE, e.g., M1AMVMV102) |
| `size_*` | text | Target qty per size (NULL = not in assortment) |
| `total_planogram` | text | Sum of all size_* targets (cast to int) |
| `storage_new` | text | Storage capacity toko (cast to int) |

**Stores Available (Jatim — 11 toko):**
- ZUMA PTC
- Zuma City Of Tomorrow Mall
- Zuma Galaxy Mall
- Zuma Icon Gresik
- Zuma Lippo Batu
- Zuma Lippo Sidoarjo
- Zuma Mall Olympic Garden
- Zuma Matos
- Zuma Royal Plaza
- Zuma Sunrise Mall
- Zuma Tunjungan Plaza

**IMPORTANT — DB quirks:**
- `article_mix` di planogram adalah **UPPERCASE** (e.g., `M1AMVMV102`)
- `kode_mix` di `core.stock_with_product` bisa mixed case → selalu `LOWER()` saat join
- Kolom `total_planogram`, `storage_new` tipe **text** → harus `::int` saat query
- Jangan JOIN dengan `dim_product` — tidak ada `product_id` di `stock_with_product`. Gunakan `kode_mix` langsung.

---

## RO Logic — v2 (Max Stock vs On Hand)

### Flow

```
PER ARTIKEL DI TOKO:
│
├─ Max Stock = total_planogram::int + storage_new::int
│
├─ On Hand = SUM(quantity) dari core.stock_with_product
│            WHERE nama_gudang ILIKE '%{store}%'
│            GROUP BY kode_mix (all sizes summed)
│
├─ Selisih = Max Stock - On Hand
│
└─ Decision:
   ├─ Selisih ≤ 0 → SURPLUS — skip, tidak di-RO
   │
   └─ Selisih > 0 → RO CANDIDATE
      ├─ Box Qty = ceil(selisih / 12)
      └─ Cek WH Pusat stock >= 12 pairs
         ├─ YES → masuk daftar RO ✅
         └─ NO  → exclude (WH tidak cukup) ❌
```

### Tier Rules

| Tier | Include? | Notes |
|------|----------|-------|
| T1 | ✅ | Priority 1 |
| T8 | ✅ | Priority 2 |
| T2 | ✅ | Priority 3 |
| T3 | ✅ | Priority 4 |
| T4 | ✅ | Priority 5 — included jika ada selisih |
| T5 | ❌ | Excluded |
| T6 | ❌ | Excluded |
| T7 | ❌ | Excluded |

**Sort order:** tier_order (T1→T8→T2→T3→T4), lalu DDD qty DESC dalam tier yang sama.

### WH Stock Rules

- Source: `nama_gudang = 'Warehouse Pusat'` (exact match — exclude Protol, Reject)
- Entitas: `warehouse_code IN ('DDD', 'LJBB')` ONLY
- Prioritas DDD: jika DDD > 0, DDD yang dipakai dulu
- Eligibility threshold: `wh_qty_ddd + wh_qty_ljbb >= 12 pairs`
- Display: tampilkan DDD dan LJBB qty secara terpisah di Excel

---

## Excel Output

### Sheet 1: "RO Request" (Cover)

Summary + metadata: store, tanggal, total articles, total boxes, total pairs, WH source, logic description, tier priority.

### Sheet 2: "Daftar RO Box"

| Col | Header | Keterangan |
|-----|--------|-----------|
| 1 | No | Nomor urut |
| 2 | Article | Nama artikel |
| 3 | Kode Mix | article_mix code |
| 4 | Gender | MEN/WOMEN/KIDS |
| 5 | Series | Nama series |
| 6 | Tier | 1/2/3/4/8 |
| 7 | Max Stock (Pairs) | total_planogram + storage_new |
| 8 | On Hand (Pairs) | Stok aktual toko saat ini (all sizes) |
| 9 | Selisih (Pairs) | Max Stock - On Hand |
| 10 | Box Qty | ceil(selisih / 12) |
| 11 | WH Qty DDD (Pairs) | Stok WH Pusat DDD |
| 12 | WH Qty LJBB (Pairs) | Stok WH Pusat LJBB |

Total row: sum Selisih (Pairs) + sum Box Qty.

### Sheet 3: "Reference"

Internal metadata: logic version, WH source, tiers excluded, artikel scanned, surplus count, no-WH count, final RO count.

---

## Script: `build_ro_box_only.py`

### Config (ubah per run)

```python
STORE_NAME       = "Zuma Royal Plaza"     # Display name (ILIKE match ke planogram)
STORE_DB_PATTERN = "zuma royal plaza"     # Lowercase, untuk ILIKE ke stock
EXCLUDED_TIERS   = ['5', '6', '7']        # Tier yang di-skip
TIER_ORDER       = {'1':0,'8':1,'2':2,'3':3,'4':4}
```

### Key Queries

**Planogram (Max Stock):**
```sql
SELECT
    store_name, gender, series, article, tier, article_mix,
    total_planogram::int   AS planogram_qty,
    storage_new::int       AS storage_qty,
    (total_planogram::int + storage_new::int) AS max_stock
FROM portal.temp_portal_plannogram
WHERE store_name ILIKE %s
ORDER BY tier, article
```

**Store On Hand (per article, all sizes):**
```sql
SELECT
    TRIM(LOWER(kode_mix)) AS article_mix,
    SUM(quantity)         AS on_hand
FROM core.stock_with_product
WHERE LOWER(nama_gudang) ILIKE %s
GROUP BY TRIM(LOWER(kode_mix))
```

**WH Pusat Stock (DDD + LJBB split):**
```sql
SELECT
    TRIM(LOWER(kode_mix)) AS article_mix,
    SUM(CASE WHEN warehouse_code = 'DDD'  THEN quantity ELSE 0 END) AS wh_qty_ddd,
    SUM(CASE WHEN warehouse_code = 'LJBB' THEN quantity ELSE 0 END) AS wh_qty_ljbb
FROM core.stock_with_product
WHERE nama_gudang = 'Warehouse Pusat'           -- exact match, no Protol/Reject
  AND warehouse_code IN ('DDD', 'LJBB')
  AND TRIM(LOWER(kode_mix)) = ANY(%s)           -- pass lowercase list
GROUP BY TRIM(LOWER(kode_mix))
```

**IMPORTANT:** Gunakan `= ANY(%s)` dengan `list` (bukan `IN %s` dengan tuple) — psycopg2 tidak support `IN %s` untuk array via `pd.read_sql`.

---

## DB Connection

```python
DB_CONFIG = {
    "host":     "76.13.194.120",
    "port":     5432,
    "database": "openclaw_ops",
    "user":     "openclaw_app",
    "password": "Zuma-0psCl4w-2026!",
}
```

---

## Output File Location

```
~/.claude/skills/zuma-plano-and-ro/zuma-ro-box-only/
└── RO_BoxOnly_{StoreName}_{YYYYMMDD}.xlsx
```

---

## GDrive + WA Delivery (standard flow)

```bash
# 1. Upload GDrive (always set anyone+editor)
ID=$(gog drive upload "RO_BoxOnly_*.xlsx" --account harveywayan@gmail.com --json | python3 -c "import sys,json; print(json.load(sys.stdin)['file']['id'])")
gog drive share "$ID" --account harveywayan@gmail.com --anyone --role writer

# 2. Send WA ke Wayan
openclaw message send --channel whatsapp --target "+628983539659" \
  --message "RO Box {Store}: https://docs.google.com/spreadsheets/d/$ID/edit?usp=drivesdk"

# 3. Send WA ke Nisa (jika diminta)
openclaw message send --channel whatsapp --target "+6285101726716" \
  --message "..."
```

**Notes:**
- Keychain perlu unlock dulu: `security unlock-keychain -p "database_2112" ~/Library/Keychains/login.keychain-db`
- Iris sering timeout untuk upload tasks — lebih reliable pakai gog CLI langsung
- Wayan = +628983539659, Nisa = +6285101726716 (dari .env)

---

## Comparison vs Transisi Skill

| Feature | Transisi | Box-Only v2 |
|---------|----------|-------------|
| RO Trigger | 3+ size kosong → Box / 1-2 → Protol | Max Stock vs On Hand selisih |
| Protol | Yes | **No** |
| Box Qty | Always 1 | **ceil(selisih/12)** |
| T4 | Excluded | **Included** |
| Surplus | Urgent (mandatory) + Regular | **Skip only** (no surplus sheet) |
| WH Display | Combined | **DDD + LJBB split** |
| Data Source | `portal.planogram` | `portal.temp_portal_plannogram` |
| Branch | All branches | **Jatim only** |
