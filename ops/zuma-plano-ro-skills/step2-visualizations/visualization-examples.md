# Visualization Examples & Store Layout Configs

> Referenced from `SKILL.md`. Contains worked examples, store layout configs, parsing strategies, and how to add new stores.

---

## 1. Reference Format — Royal Plaza ASCII Example

Format visual existing menggunakan grid. Contoh layout Royal Plaza:

```
+---------+  +----+----+----+----+----+----+----+----+  +----+----+----+----+----+----+----+----+
|         |  |      BACKWALL MEN FASHION (8X7)       |  |       BACKWALL LADIES FASHION (8X7)    |
| CLASSIC |  | ZORRO | ZORRO |DALLAS|DALLAS| SLIDE  |  |  FLO | FLO  | FLO |PUFFY|PUFFY| ELSA  |
|    &    |  | ZORRO | ZORRO |DALLAS|DALLAS| SLIDE  |  |  FLO | FLO  | FLO |PUFFY|PUFFY| ELSA  |
| BLACK   |  | ZORRO | ZORRO |DALLAS|DALLAS| SLIDE  |  |  FLO | FLO  | FLO |PUFFY|PUFFY| ELSA  |
| SERIES  |  | ... (7 rows)                          |  |  ... (7 rows)                          |
| (7X7)   |  |                                       |  |                                        |
+---------+  +---------------------------------------+  +----------------------------------------+
                                                               +--------+
                                                               | KASIR  |
                  +-------------+  +-------------+             +--------+
                  | BABY CLASSIC|  | BABY VELCRO |
                  | BABY KARAK. |  | BABY VELCRO |    +---+---+---+---+---+
                  | BABY KARAK. |  | BABY VELCRO |    | CLASSIC       |7X7|
                  +-------------+  +-------------+    | CLASSIC       |   |
                                                      | KIDS CLASSIC  |   |
                        +----------+                  | KIDS CLASSIC  |   |
                        | AIRMOVE  |                  | KIDS KARAKTER |   |
                        |          |                  | KIDS KARAKTER |   |
                        +----------+                  +---+---+---+---+---+
```

Visual elements:
1. **RECTANGLES** — Setiap display unit = blok rectangle
2. **GRID CELLS** — Setiap hook/slot = 1 cell, berisi nama series
3. **COLOR-CODED** per series — Setiap series punya warna background
4. **MERGED CELLS** — Header, label area, objek non-display (kasir)
5. **DIMENSION LABELS** — "8X7" = 8 kolom x 7 baris
6. **SPACING** — Jarak antar unit menunjukkan layout fisik toko

---

## 2. Store Layout Config Format

### Generic Config Structure

```python
# Coordinates: (x, y) = top-left corner of each display unit
# Size: (width, height) in grid units
STORE_LAYOUT = {
    "store_name": "Zuma [Store Name]",
    "canvas_size": (40, 25),  # grid units
    "display_units": [
        {
            "id": "BW-1",
            "type": "backwall",
            "label": "CLASSIC & BLACKSERIES",
            "position": (0, 2),    # (x, y) top-left
            "size": (2, 14),       # (width, height) in cells
            "orientation": "vertical",  # vertical = tall & narrow
            "articles_flow": "top-to-bottom",
        },
        {
            "id": "BW-2",
            "type": "backwall",
            "label": "MEN FASHION (8X7)",
            "position": (4, 0),
            "size": (16, 2),       # 8 articles x 2 rows
            "orientation": "horizontal",
            "articles_flow": "left-to-right",
        },
        {
            "id": "RK-1",
            "type": "rak_baby",
            "label": "RAK BABY",
            "position": (14, 8),
            "size": (6, 3),
        },
        {
            "id": "KASIR",
            "type": "landmark",
            "label": "KASIR",
            "position": (28, 5),
            "size": (3, 3),
        },
        {
            "id": "ENTRANCE",
            "type": "landmark",
            "label": "ENTRANCE",
            "position": (18, 22),
            "size": (4, 1),
        },
    ],
}
```

### Deriving Layout from Portal Planogram

Jika layout bisa diambil dari `portal_planogram_jatim.xlsx`:

```python
# From merged cells, derive physical positions:
# BA3:BH3 = "8X7" -> columns BA-BH (8 cols), starting row 3
# BJ3:BQ3 = "8X7" -> columns BJ-BQ (8 cols), starting row 3
# AY6:AY12 = "7X7" -> column AY, rows 6-12 (7 rows)
# These map to physical display positions in the store
```

**GOTCHA**: Portal format uses column letters (BA, BB, etc.) for X position and row numbers for Y position. Translate to (x,y) coordinates.

---

## 3. Royal Plaza Layout Config (Complete)

Derived from `portal_planogram_jatim.xlsx` "Zuma Royal Plaza" sheet:

```python
ROYAL_PLAZA_LAYOUT = {
    "store_name": "Zuma Royal Plaza",
    "canvas_size": (45, 28),
    "display_units": [
        # Left wall: Men Jepit (CLASSIC & BLACKSERIES) - vertical
        {
            "id": "BW-1",
            "type": "backwall",
            "label": "CLASSIC & BLACKSERIES\n(Men Jepit)",
            "position": (0, 3),
            "size": (3, 14),
            "orientation": "vertical",
            "dimension_label": "7X7",
        },
        # Top-left: Men Fashion backwall - horizontal
        {
            "id": "BW-3",
            "type": "backwall",
            "label": "MEN FASHION",
            "position": (5, 0),
            "size": (16, 3),
            "orientation": "horizontal",
            "dimension_label": "8X7",
        },
        # Top-right: Ladies Fashion backwall - horizontal
        {
            "id": "BW-2",
            "type": "backwall",
            "label": "LADIES FASHION",
            "position": (23, 0),
            "size": (16, 3),
            "orientation": "horizontal",
            "dimension_label": "8X7",
        },
        # Right wall: Baby & Kids + Kids - vertical
        {
            "id": "BW-4",
            "type": "backwall",
            "label": "KIDS",
            "position": (41, 3),
            "size": (3, 14),
            "orientation": "vertical",
            "dimension_label": "7X7",
        },
        # Center-left: Baby rak area
        {
            "id": "RK-1",
            "type": "rak_baby",
            "label": "RAK BABY",
            "position": (14, 9),
            "size": (8, 4),
        },
        # Kasir
        {
            "id": "KASIR",
            "type": "landmark",
            "label": "KASIR",
            "position": (30, 5),
            "size": (4, 4),
        },
        # Airmove display area
        {
            "id": "AIRMOVE",
            "type": "landmark",
            "label": "AIRMOVE\n(Display Area)",
            "position": (28, 12),
            "size": (4, 6),
        },
    ],
}
```

---

## 4. Script Architecture

```python
visualize_planogram.py
├── CONFIG (paths, colors, abbreviations)
├── PARSE
│   ├── parse_planogram_xlsx(filepath)     # Main parser
│   ├── parse_backwall_sheet(ws, bw_id)    # Per-BW sheet parser
│   ├── parse_rak_baby_sheet(ws)           # Rak Baby parser
│   └── extract_series_from_article(name)  # Series name extractor
├── LAYOUT CONFIG
│   └── ROYAL_PLAZA_LAYOUT dict            # Grid coordinates per display unit
├── EXCEL VISUAL (Option A)
│   ├── generate_excel_visual()            # Main Excel generator
│   ├── _excel_draw_backwall()             # Horizontal/vertical backwall
│   ├── _excel_draw_rak_baby()             # Rak Baby section
│   ├── _excel_draw_landmark()             # KASIR, AIRMOVE
│   └── _excel_draw_legend()               # Series color legend
├── ASCII VISUAL (Option B)
│   ├── generate_ascii_visual()            # Main ASCII generator
│   ├── _ascii_horizontal_block()          # Top backwalls (BW-2, BW-3)
│   ├── _ascii_vertical_block()            # Side backwalls (BW-1, BW-4)
│   └── _ascii_center_block()             # Center area (Rak Baby, KASIR, AIRMOVE)
└── MAIN
    └── Parse → Excel → ASCII → Print preview
```

---

## 5. Parsing Strategy

Iterate by **slot index** (not cell-by-cell) because merged cells in openpyxl only store value in the top-left cell:

```python
# Known stride per backwall type:
#   Fashion (3 hooks/article): col starts at 2, step by 3 → cols 2, 5, 8, 11...
#   Jepit/Kids (2 hooks/article): col starts at 2, step by 2 → cols 2, 4, 6, 8...
col = 2
for slot_idx in range(slots):
    series  = ws.cell(row=5, column=col).value  # Series name
    article = ws.cell(row=6, column=col).value  # Article name (main data)
    tier    = ws.cell(row=7, column=col).value  # "T1 | Avg: 6.3"
    col += hooks_per_article
```

---

## 6. How to Add a New Store

To visualize a different store, modify `visualize_planogram.py`:

1. **Update `INPUT_FILE`** to point to the new store's PLANOGRAM XLSX
2. **Create a new layout config** (copy `ROYAL_PLAZA_LAYOUT` and modify):
   ```python
   NEW_STORE_LAYOUT = {
       "store_name": "Zuma [Store Name]",
       "grid_width": ...,
       "grid_height": ...,
       "display_units": [
           {"bw_id": "BW-1", "label": "...", "orientation": "...",
            "grid_col": ..., "grid_row": ..., "label_row": ...},
           # ... more units
       ],
       "entrance": {"grid_col": ..., "grid_row": ..., "label": "ENTRANCE"},
   }
   ```
3. **Derive layout positions** from `portal_planogram_[region].xlsx` sheet for that store
4. If portal layout not available, ask BM/AS for floor photo and approximate

### How to Create Layout Config from Portal

1. Open `portal_planogram_jatim.xlsx` (or respective region file)
2. Go to the store's sheet
3. Find the LAYOUT section (right side, look for merged cells with "LAYOUT ZUMA [STORE NAME]")
4. Map each colored block to a display unit:
   - Note its column range (= X position + width)
   - Note its row range (= Y position + height)
   - Note the label (series name or dimension like "8X7")
5. Translate to the config dict format above

**OR** if portal planogram doesn't exist for the store:
1. Ask the store BM/AS for a photo or sketch of the store layout
2. Approximate positions from `Data Option By Region.xlsx` display component list
3. Use a simple left-to-right, top-to-bottom default layout

---

## 7. Reference Files

- `portal_planogram_jatim.xlsx` — Existing visual format for Jatim stores (source of truth for layout positions and color conventions)
- `visual_plannogram-royal_plaza_example_previous_plano.png` — Screenshot of existing portal planogram visual for Royal Plaza
- `visualize_planogram.py` — Main visualization script (Royal Plaza)
- `visualize_tunjungan_planogram.py` — Tunjungan store variant
