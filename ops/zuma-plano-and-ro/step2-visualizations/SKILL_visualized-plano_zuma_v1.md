---
name: visualized-planogram-zuma
description: Tool untuk membuat VISUALISASI planogram (bird's-eye floor plan) toko Zuma dari output XLSX planogram Step 1. Menghasilkan gambar layout fisik toko dengan penempatan artikel per hook, color-coded per series/tier. Gunakan setelah SKILL_planogram_zuma_v3.md selesai menghasilkan XLSX.
user-invocable: true
---

# Planogram Visualization Engine — Zuma

Kamu adalah PLANOGRAM VISUALIZER untuk ZUMA Footwear Retail. Tugasmu mengubah output data planogram (XLSX dari Step 1) menjadi **gambar visual bird's-eye floor plan** yang menunjukkan penempatan fisik setiap artikel di toko.

**Prerequisite:** Step 1 harus sudah selesai — yaitu XLSX planogram dari `SKILL_planogram_zuma_v3.md` / `build_*_planogram.py` sudah dihasilkan.

---

# SECTION 1: KONSEP & FORMAT VISUAL

## 1.1 Apa itu Visualisasi Planogram

Visualisasi planogram adalah **peta bird's-eye** dari layout fisik toko. Setiap display unit (backwall, gondola, rak, table) digambar sebagai area persegi/rectangle di peta, dan setiap hook/slot di dalam display unit diisi dengan nama artikel + warna series.

Output berupa gambar PNG (atau embedded di Excel sheet) yang bisa langsung dicetak/ditampilkan di toko sebagai panduan penempatan produk oleh SPG.

## 1.2 Referensi Format Existing

Format visual existing (lihat `portal_planogram_jatim.xlsx`) menggunakan grid di Excel sheet yang terletak di sisi kanan data (sekitar kolom AX-BX):

```
Elemen visual yang digunakan:
1. RECTANGLES — Setiap display unit digambar sebagai blok rectangle
2. GRID CELLS — Setiap hook/slot = 1 cell di grid, berisi nama series
3. COLOR-CODED per series — Setiap series punya warna background tersendiri
4. MERGED CELLS — Untuk header, label area, dan objek non-display (kasir, dll)
5. DIMENSION LABELS — "8X7" = 8 kolom x 7 baris (= jumlah hook per sisi)
6. SPACING — Jarak antar display unit menunjukkan layout fisik toko
```

### Contoh Layout Royal Plaza (dari portal_planogram_jatim.xlsx):

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

## 1.3 Elemen Visual & Warna

### 1.3.1 Color Palette per Series

Setiap series punya warna yang KONSISTEN di seluruh visualisasi. Ambil dari existing portal planogram:

| Series | Background Color | Hex Code |
|--------|-----------------|----------|
| ZORRO | Light Pink | `#EAD1DC` |
| DALLAS | Light Salmon | `#E6B8AF` |
| SLIDE | Light Yellow | `#FFF2CC` |
| FLO | Light Orange | `#F9CB9C` |
| PUFFY | Light Blue | `#A4C2F4` |
| ELSA | Light Grey | `#CCCCCC` |
| CLASSIC & BLACKSERIES (Jepit) | Yellow | `#FFF2CC` / `#F1C232` |
| BABY CLASSIC | Cyan | `#00FFFF` |
| BABY KARAKTER | Light Green | `#B7E1CD` |
| BABY VELCRO | Red/Pink | `#E06666` |
| KIDS CLASSIC | Sage Green | `#B6D7A8` |
| KIDS KARAKTER | Sage Green | `#B6D7A8` |
| MERCI | Light Purple | `#D9D2E9` |
| STITCH | Light Teal | `#B4E7CE` |
| WEDGES | Light Brown | `#D7CCC8` |
| LUNA | Light Lavender | `#D5A6BD` |

**Jika series baru belum ada warnanya**: Generate warna pastel otomatis yang distinct dari warna yang sudah ada.

### 1.3.2 Tier Color Coding (Alternative Mode)

Selain color-by-series, bisa juga color-by-tier:

| Tier | Color | Hex |
|------|-------|-----|
| T1 | Green | `#C6EFCE` |
| T8 | Blue | `#BDD7EE` |
| T2 | Yellow | `#FFFFCC` |
| T3 | Grey | `#D9D9D9` |

### 1.3.3 Shelving & Table Display Elements

| Element | Style | Notes |
|---------|-------|-------|
| SHELVING (Airmove, Puffy, etc.) | Light blue/green bg, dashed border | Label: "SHELVING [SERIES]", list articles inside |
| TABLE LUCA LUNA | White bg, thick border, centered | Label: "TABLE LUCA LUNA", list articles |
| TABLE BABY | Light yellow bg, thick border | Label: "TABLE BABY", list articles |
| MIXED-HOOK BW | Single block, internal divider line | Split sections with different colors per section |

**Rendering:**
- Shelving terintegrasi di BW: render sebagai kolom terakhir di BW dengan warna/style berbeda + label "SHELVING"
- Shelving standalone: render sebagai blok terpisah di layout
- Table: render sebagai rectangle dengan list artikel di dalamnya
- Mixed BW (e.g., BW-4a Elsa + Classic): render sebagai satu blok fisik, tapi beri garis pemisah antara section dan label per section

### 1.3.4 Non-Display Elements

| Element | Style |
|---------|-------|
| KASIR (Cashier) | White bg, black border, centered text |
| KURSI (Chair/Seating) | White bg, thin border, centered text |
| ENTRANCE / Depan | Arrow/text marker |
| EMPTY HOOKS | Dotted border or light fill |
| WALLS | Thick black border on exterior |

## 1.4 Dimensi & Grid System

### Portal Layout Interpretation Guide

**Cara membaca layout dari portal_planogram_[region].xlsx:**

Portal planogram punya layout visual di kolom tinggi (biasanya AX-BW). Beberapa konvensi:

```
"7 BARIS" = 7 rows of hooks (kedalaman/tinggi backwall), BUKAN jumlah artikel
"8X7"     = 8 kolom artikel × 7 baris hook = display 8 artikel, setiap artikel menempati 7 hook vertikal

Merged cells = satu display unit (backwall/landmark)
Warna cell   = series assignment existing
Text di cell = series name atau label landmark
```

**Estimasi hooks dari layout portal:**
```
Jika layout menunjukkan N kolom artikel:
  Fashion (3 hook/artikel): total hooks = N × 7 (baris) — tapi yg relevan = N artikel × 3 hpa
  Jepit (2 hook/artikel):   total hooks = N × 7 (baris) — tapi yg relevan = N artikel × 2 hpa

Actual capacity (artikel) = jumlah kolom di layout visual
  → Bukan dihitung dari total hooks ÷ hpa
  → Karena layout sudah menunjukkan berapa artikel muat

Jika ragu: tanyakan user, atau hitung dari denah fisik
```

### Backwall/Gondola Dimensions

Dalam portal existing, dimensi ditulis sebagai "NxM" dimana:
- **N** = jumlah kolom (articles per baris horizontal)
- **M** = jumlah baris (rows, biasanya = 7 untuk standard backwall height)

Contoh:
- "8X7" = 8 article slots wide, 7 rows tall = display untuk 8 articles
- "7X7" = 7 article slots wide, 7 rows tall = display untuk 7 articles

**PENTING**: Baris (rows) menunjukkan DEPTH of display (tumpukan size), bukan jumlah artikel tambahan. 1 kolom = 1 artikel (atau 1 group hooks untuk fashion).

### Mapping dari Step 1 ke Grid

```
Step 1 output: "BW-1: Men Jepit, 48 hooks, 24 slots (2 hooks per article)"
Grid equivalent: 1 kolom per artikel = 24 kolom (atau di-wrap menjadi beberapa baris jika terlalu panjang)

Step 1 output: "BW-2: Ladies Fashion, 56 hooks, 18 slots (3 hooks per article)"
Grid equivalent: 1 kolom per artikel = 18 kolom
```

### Rak Baby Dimensions

- 1 layer = 1 row di visual
- Per row: jumlah articles (1 jika full mode, 2 jika compact mode)

---

# SECTION 2: INPUT & OUTPUT

## 2.1 Input yang Dibutuhkan

| No | Data | Source | Keterangan |
|----|------|--------|------------|
| 1 | **PLANOGRAM XLSX (Step 1 output)** | `PLANOGRAM_[StoreName].xlsx` | Sheet per backwall + Rak Baby + Summary |
| 2 | **Store layout reference** | `portal_planogram_jatim.xlsx` atau `Data Option By Region.xlsx` | Posisi fisik display units di toko |
| 3 | **Series color mapping** | Section 1.3.1 di atas | Warna per series |

### Data yang Diambil dari PLANOGRAM XLSX:

Per backwall sheet:
- Backwall ID, Gender-Type, jumlah hooks
- Daftar artikel + posisi hook (baris: Artikel, Tier & Avg, Series)
- Mode (Full Box / Compact)

Per Rak Baby sheet:
- Layer assignments
- Artikel per layer

### Data yang Diambil dari Store Layout Reference:

- **Posisi relatif** display units (mana yang di kiri, kanan, depan, belakang)
- **Adjacency** — display mana yang bersebelahan
- **Non-display landmarks** — posisi kasir, pintu masuk, area airmove/luca

## 2.2 Output

### Output Option A: Excel Floor Plan (IMPLEMENTED)

File XLSX terpisah (`VISUAL_PLANOGRAM_[Store].xlsx`) dengan single sheet "Layout Visual":
- Bird's eye floor plan menggunakan grid cells
- Narrow columns (width=4), short rows (height=18) untuk efek grid
- Setiap display unit sebagai colored rectangle block
- Setiap artikel = 1 cell, colored by series (PatternFill)
- Horizontal backwalls: 2 rows per block (series name + article short name)
- Vertical backwalls: 1 row per article, 3 cols (series + article + tier)
- Landmarks (KASIR, AIRMOVE): merged cells dengan thick border
- Legend: series name dengan colored background cell
- Header: nama toko + planogram period + generated date

**Library**: `openpyxl` (no matplotlib/PIL needed)

### Output Option B: ASCII Floor Plan (IMPLEMENTED)

File text (`VISUAL_PLANOGRAM_[Store].txt`), ~115 chars wide:
- Box-drawing characters (standard ASCII: +, -, |)
- Top section: horizontal backwalls side-by-side
- Middle section: vertical backwalls (left/right) + center area (landmarks)
- Bottom: ENTRANCE label
- Legend: 3-char series abbreviations mapped to full names
- Summary: slot utilization per backwall + total

**Library**: built-in Python string formatting (no external deps)

### Output Option C: Both (DEFAULT)

Generate Excel + ASCII simultaneously. Kedua output dihasilkan dari satu kali parsing.

---

# SECTION 3: STEP-BY-STEP GENERATION

## 3.1 Parse Step 1 Output

```python
# Read the planogram XLSX from Step 1
import openpyxl

wb = openpyxl.load_workbook('PLANOGRAM_[Store].xlsx', data_only=True)

# Extract per-backwall data
for sheet_name in wb.sheetnames:
    if sheet_name.startswith('BW-'):
        ws = wb[sheet_name]
        # Row 6 = Article names (per slot)
        # Row 7 = Tier & Avg
        # Row 5 = Series names
        # Config: gender_type, hooks, mode from title row
```

## 3.2 Define Store Layout Coordinates

Setiap toko punya layout fisik yang BERBEDA. Posisi display units harus di-define per toko.

### Layout Config Format:

```python
# Coordinates: (x, y) = top-left corner of each display unit
# Size: (width, height) in grid units
STORE_LAYOUT = {
    "store_name": "Zuma Royal Plaza",
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
            "size": (16, 2),       # 8 articles x 2 rows (fashion 3-hook = wider)
            "orientation": "horizontal",
            "articles_flow": "left-to-right",
        },
        {
            "id": "BW-3",
            "type": "backwall",
            "label": "LADIES FASHION (8X7)",
            "position": (22, 0),
            "size": (16, 2),
            "orientation": "horizontal",
            "articles_flow": "left-to-right",
        },
        {
            "id": "BW-4",
            "type": "backwall",
            "label": "BABY & KIDS (7X7)",
            "position": (35, 2),
            "size": (2, 14),
            "orientation": "vertical",
            "articles_flow": "top-to-bottom",
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

Jika layout bisa diambil dari `portal_planogram_jatim.xlsx`, extract posisi dari merged cells:

```python
# From merged cells, derive physical positions:
# BA3:BH3 = "8X7" -> columns BA-BH (8 cols), starting row 3
# BJ3:BQ3 = "8X7" -> columns BJ-BQ (8 cols), starting row 3
# AY6:AY12 = "7X7" -> column AY, rows 6-12 (7 rows)
# These map to physical display positions in the store
```

**GOTCHA**: Portal format uses column letters (BA, BB, etc.) for X position and row numbers for Y position. Translate to (x,y) coordinates for the visualization.

## 3.3 Generate Floor Plan Image (Option A: matplotlib)

### Core Drawing Logic:

```python
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import to_rgba
import numpy as np

def draw_planogram_floorplan(store_layout, planogram_data, output_path):
    """
    Draw a bird's-eye floor plan of the store with article placements.
    """
    canvas_w, canvas_h = store_layout["canvas_size"]
    
    # Figure size proportional to canvas
    fig, ax = plt.subplots(1, 1, figsize=(canvas_w * 0.6, canvas_h * 0.6), dpi=150)
    ax.set_xlim(-1, canvas_w + 1)
    ax.set_ylim(-1, canvas_h + 1)
    ax.set_aspect('equal')
    ax.invert_yaxis()  # (0,0) = top-left like Excel
    ax.axis('off')
    
    # Title
    fig.suptitle(f"LAYOUT {store_layout['store_name'].upper()}", 
                 fontsize=16, fontweight='bold', y=0.98)
    
    # Draw each display unit
    for unit in store_layout["display_units"]:
        x, y = unit["position"]
        w, h = unit["size"]
        
        if unit["type"] == "landmark":
            # Non-display: simple bordered rectangle
            rect = patches.Rectangle((x, y), w, h, 
                                     linewidth=2, edgecolor='black',
                                     facecolor='white')
            ax.add_patch(rect)
            ax.text(x + w/2, y + h/2, unit["label"],
                    ha='center', va='center', fontsize=8, fontweight='bold')
        
        elif unit["type"] in ("backwall", "gondola"):
            # Get articles assigned to this unit from planogram_data
            bw_data = planogram_data.get(unit["id"], {})
            articles = bw_data.get("articles", [])
            
            draw_display_unit(ax, unit, articles)
        
        elif unit["type"] == "rak_baby":
            draw_rak_baby(ax, unit, planogram_data.get("rak_baby", []))
    
    # Legend
    draw_legend(ax, canvas_w, canvas_h)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()


def draw_display_unit(ax, unit, articles):
    """Draw a single backwall/gondola with article cells."""
    x, y = unit["position"]
    w, h = unit["size"]
    orientation = unit.get("orientation", "horizontal")
    
    n_articles = len(articles)
    if n_articles == 0:
        # Empty unit
        rect = patches.Rectangle((x, y), w, h, linewidth=2,
                                 edgecolor='black', facecolor='#F5F5F5')
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, f"{unit['label']}\n(EMPTY)",
                ha='center', va='center', fontsize=6)
        return
    
    if orientation == "horizontal":
        cell_w = w / n_articles
        cell_h = h
        for i, art in enumerate(articles):
            cx = x + i * cell_w
            cy = y
            color = get_series_color(art.get("series", ""))
            
            rect = patches.Rectangle((cx, cy), cell_w, cell_h,
                                     linewidth=0.5, edgecolor='black',
                                     facecolor=color)
            ax.add_patch(rect)
            
            # Series name (short, fits in cell)
            label = art.get("series", "?")
            ax.text(cx + cell_w/2, cy + cell_h/2, label,
                    ha='center', va='center', fontsize=4,
                    rotation=90 if cell_w < 1.5 else 0)
    
    elif orientation == "vertical":
        cell_w = w
        cell_h = h / n_articles
        for i, art in enumerate(articles):
            cx = x
            cy = y + i * cell_h
            color = get_series_color(art.get("series", ""))
            
            rect = patches.Rectangle((cx, cy), cell_w, cell_h,
                                     linewidth=0.5, edgecolor='black',
                                     facecolor=color)
            ax.add_patch(rect)
            
            label = art.get("series", "?")
            ax.text(cx + cell_w/2, cy + cell_h/2, label,
                    ha='center', va='center', fontsize=4)
    
    # Unit label (above or left)
    ax.text(x + w/2, y - 0.3, unit["label"],
            ha='center', va='bottom', fontsize=6, fontweight='bold')
```

### Series Color Function:

```python
SERIES_COLORS = {
    "ZORRO": "#EAD1DC",
    "DALLAS": "#E6B8AF",
    "SLIDE": "#FFF2CC",
    "FLO": "#F9CB9C",
    "PUFFY": "#A4C2F4",
    "ELSA": "#CCCCCC",
    "CLASSIC": "#FFF2CC",
    "BLACKSERIES": "#FFF2CC",
    "STRIPE": "#FFE0B2",
    "ONYX": "#CFD8DC",
    "BLACK SERIES": "#FFF2CC",
    "MERCI": "#D9D2E9",
    "STITCH": "#B4E7CE",
    "WEDGES": "#D7CCC8",
    "LUNA": "#D5A6BD",
    "LUCA": "#FFCCBC",
    "AIRMOVE": "#E0E0E0",
    "BABY CLASSIC": "#00FFFF",
    "BABY KARAKTER": "#B7E1CD",
    "BABY VELCRO": "#E06666",
    "WBB": "#80DEEA",
    "DISNEY": "#FFAB91",
    "BATMAN": "#90A4AE",
    "POOH": "#FFE082",
    "LOTSO": "#F48FB1",
    "COLLAB": "#CE93D8",
    "TOY STORY": "#81D4FA",
    "VELCRO BRICKS": "#A5D6A7",
    "VELCRO STITCH": "#B4E7CE",
    "KIDS CLASSIC": "#B6D7A8",
    "KIDS KARAKTER": "#B6D7A8",
}

def get_series_color(series_name):
    """Get color for a series. Auto-generate pastel if not found."""
    series_upper = series_name.upper().strip()
    for key, color in SERIES_COLORS.items():
        if key in series_upper:
            return color
    # Auto-generate pastel
    import hashlib
    h = int(hashlib.md5(series_upper.encode()).hexdigest()[:6], 16)
    r = 180 + (h % 75)
    g = 180 + ((h >> 8) % 75)
    b = 180 + ((h >> 16) % 75)
    return f'#{r:02x}{g:02x}{b:02x}'
```

## 3.4 Generate Excel Visual Sheet (Option B: openpyxl)

```python
def add_visual_sheet_to_xlsx(wb, store_layout, planogram_data):
    """
    Add a visual layout sheet to existing planogram XLSX.
    Matches portal_planogram_jatim.xlsx format.
    """
    ws = wb.create_sheet(title="Layout Visual")
    
    # Title
    ws.merge_cells('A1:Z1')
    ws.cell(row=1, column=1, value=f"LAYOUT {store_layout['store_name'].upper()}")
    ws.cell(row=1, column=1).font = Font(bold=True, size=14)
    
    # For each display unit, place articles in grid cells with colors
    for unit in store_layout["display_units"]:
        place_unit_in_excel(ws, unit, planogram_data)
```

## 3.5 Detail-Level Variants

Planogram visual bisa dibuat dalam beberapa level detail:

### Level 1: Series-Level (untuk overview cepat)
- Setiap cell = nama SERIES (bukan individual article)
- 1 warna per series
- Cepat dibuat, mudah dibaca dari jauh
- **Ini yang dipakai di portal_planogram_jatim.xlsx existing**

### Level 2: Article-Level (untuk detail penempatan)
- Setiap cell = nama ARTICLE lengkap (e.g., "MEN ZORRO 1, BLACK")
- Warna by series
- Font lebih kecil, butuh resolusi tinggi
- Cocok untuk cetak ukuran besar (A3/A2)

### Level 3: Article + Metadata (untuk analisis)
- Setiap cell = article name + tier + adj avg
- Warna by tier (bukan series)
- Info padat, untuk internal review

**DEFAULT**: Level 1 (series-level) untuk visual utama. Level 2/3 sebagai additional output.

---

# SECTION 4: STORE-SPECIFIC LAYOUT CONFIGS

## 4.1 Royal Plaza Layout Config

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
        # Airmove display area (if applicable)
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

## 4.2 How to Create Layout Config for Other Stores

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

# SECTION 5: AI AGENT GOTCHAS

## 5.1 Data Flow Gotchas

| Gotcha | Penjelasan | Solusi |
|--------|-----------|--------|
| **Step 1 XLSX sheet naming** | Sheet names in Step 1 output include gender-type (e.g., "BW-2 Ladies Fashion"). Parse carefully | Split sheet name by first space to get BW-ID |
| **Series name from Step 1** | Step 1 output has `series` column in article data. Use for color mapping | Map series -> color using SERIES_COLORS dict |
| **Orientation depends on physical wall** | Left/right walls = vertical. Top/bottom walls = horizontal | Get from store layout config or portal reference |
| **Canvas size varies per store** | Small stores = smaller canvas. Mall stores with many gondolas = larger | Scale canvas_size proportionally |

## 5.2 Drawing Gotchas

| Gotcha | Penjelasan | Solusi |
|--------|-----------|--------|
| **Text overflow in small cells** | Article names too long for cell width | Use series name (shorter) or abbreviate: "MEN ZORRO 1" -> "ZORRO" |
| **matplotlib text rotation** | Vertical orientation needs rotated text | Use `rotation=90` for narrow cells |
| **DPI for print quality** | Default 72 DPI too low for print | Use `dpi=150` minimum, `dpi=300` for A3 print |
| **Windows font rendering** | Some fonts render differently on Windows | Use `fontfamily='sans-serif'` for consistency |
| **Color overlap** | Adjacent same-series cells look like 1 block (intended!) | Add thin black border per cell to maintain grid structure |

## 5.3 Excel Visual Gotchas

| Gotcha | Penjelasan | Solusi |
|--------|-----------|--------|
| **Merged cells are tricky** | openpyxl merged cells only keep value in top-left cell | Set value + style on top-left, then merge |
| **Column width for grid** | Default Excel column width too wide for grid cells | Set all grid columns to width=3.0 for compact visual |
| **Row height** | Default too tall | Set grid rows to height=15 for compact visual |
| **Color application** | openpyxl PatternFill needs `fill_type="solid"` | Always include `fill_type="solid"` parameter |

## 5.4 Layout Config Gotchas

| Gotcha | Penjelasan | Solusi |
|--------|-----------|--------|
| **Portal planogram format varies** | Beberapa stores punya layout section, beberapa tidak | Check merged cells first. If no layout section, build from scratch |
| **Coordinate system** | Excel = (col, row), matplotlib = (x, y). Both start top-left in our system | Keep consistent: (x, y) = (column, row) = (horizontal, vertical) |
| **Display unit IDs must match** | BW-1 in layout config MUST match BW-1 in Step 1 XLSX | Verify IDs before rendering |

---

# SECTION 6: EXECUTION ORDER

```
1. Read Step 1 PLANOGRAM XLSX (parse_planogram_xlsx)
   -> Extract articles per backwall via slot-index iteration (stride = hooks_per_article)
   -> Extract rak baby assignments
   -> Extract summary stats from Summary Report sheet

2. Load store layout config (ROYAL_PLAZA_LAYOUT dict)
   -> Grid coordinates for each display unit
   -> Orientation (horizontal/vertical) per backwall
   -> Landmark positions (KASIR, AIRMOVE)

3. Generate Excel visual (generate_excel_visual)
   -> Create new workbook with "Layout Visual" sheet
   -> Draw each backwall as colored cell grid
   -> Draw landmarks as bordered merged cells
   -> Add title, entrance label, legend, summary

4. Generate ASCII visual (generate_ascii_visual)
   -> Render horizontal backwalls as top blocks (side-by-side)
   -> Render vertical backwalls as side columns
   -> Render center area with landmarks
   -> Add legend (abbreviation mapping) and summary stats

5. Save outputs
   -> XLSX: VISUAL_PLANOGRAM_[Store].xlsx (new file, separate from Step 1)
   -> TXT:  VISUAL_PLANOGRAM_[Store].txt
   -> Print ASCII preview to stdout for verification
```

---

# SECTION 7: REFERENCE IMPLEMENTATION

## 7.1 Implementation Status: COMPLETE

Implementasi menggunakan **separate script** (`visualize_planogram.py`) yang membaca Step 1 XLSX output. Keputusan ini karena:
- Step 1 bisa dijalankan tanpa visual (lightweight)
- Visual bisa di-regenerate tanpa re-running Step 1
- Layout config per toko bisa di-maintain terpisah

### File Structure:
```
step 2 - plannogram visualizations/
  visualize_planogram.py              # Main script (generates both outputs)
  SKILL_visualized-plano_zuma_v1.md   # This skill document
  portal_planogram_jatim.xlsx         # Reference layout source
  visual_plannogram-royal_plaza_example_previous_plano.png  # Reference screenshot
  VISUAL_PLANOGRAM_Royal_Plaza.xlsx   # OUTPUT: Excel floor plan
  VISUAL_PLANOGRAM_Royal_Plaza.txt    # OUTPUT: ASCII floor plan
```

### File naming convention:
```
Input:  ../PLANOGRAM_Royal_Plaza.xlsx (from Step 1, parent dir)
Output: VISUAL_PLANOGRAM_Royal_Plaza.xlsx (Excel floor plan)
Output: VISUAL_PLANOGRAM_Royal_Plaza.txt  (ASCII floor plan)
```

## 7.2 Script Architecture

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
│   └── _ascii_center_block()              # Center area (Rak Baby, KASIR, AIRMOVE)
└── MAIN
    └── Parse → Excel → ASCII → Print preview
```

## 7.3 Parsing Strategy

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

## 7.4 Output Specifications (Verified)

### Option A: Excel Floor Plan
- **Format**: Separate `.xlsx` file with single sheet "Layout Visual"
- **Grid**: Narrow columns (width=4), short rows (height=18)
- **Backwall rendering**:
  - Horizontal (BW-2, BW-3): 1 col per article, 2 rows (series name + article short name)
  - Vertical (BW-1, BW-4): 1 row per article, 3 cols (series + article name + tier)
- **Colors**: PatternFill per series from SERIES_COLORS dict (fill_type="solid")
- **Landmarks**: Merged cells with thick border (KASIR, AIRMOVE)
- **Legend**: Series name with colored background cell, 8 per row
- **Library**: openpyxl only (no matplotlib/PIL)

### Option B: ASCII Floor Plan
- **Format**: UTF-8 text file, ~115 chars wide
- **Layout**:
  - Top: BW-3 + BW-2 side-by-side (horizontal blocks, 8 articles per row)
  - Middle: BW-1 (left) | Center (KASIR, Rak Baby, AIRMOVE) | BW-4 (right)
  - Bottom: ENTRANCE label
- **Article labels**: 3-char series abbreviation + tier (e.g., "ZRO T1", "FLO T2")
- **Box-drawing**: Standard ASCII (+, -, |) for maximum compatibility
- **Sections**: Layout, Legend (abbreviation mapping), Summary stats

### Verified Output Stats (Royal Plaza):
```
BW-1 Men Jepit:      23/24 articles (1 empty slot)
BW-2 Ladies Fashion: 18/18 articles
BW-3 Men Fashion:    18/18 articles
BW-4 Baby & Kids:    26/26 articles
Rak Baby:            2/2 layers
Total:               87/88 slots (98.9% utilization)
Unique series:       23
```

## 7.5 How to Add a New Store

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

### Reference files:
- `portal_planogram_jatim.xlsx` — Existing visual format for Jatim stores (source of truth for layout positions and color conventions)
- `visual_plannogram-royal_plaza_example_previous_plano.png` — Screenshot of existing portal planogram visual for Royal Plaza

---

# CARA MENJAWAB

## Jika user minta buatkan visualisasi planogram:

### Step 1: Validasi Input
- Pastikan Step 1 XLSX sudah ada (PLANOGRAM_[Store].xlsx)
- Pastikan store layout reference tersedia (portal file atau manual config)

### Step 2: Parse Data
- Jalankan `parse_planogram_xlsx()` untuk extract per-backwall article assignments
- Load store layout config (ROYAL_PLAZA_LAYOUT atau buat baru untuk toko lain)

### Step 3: Generate Visual
- **Default**: Generate BOTH Excel + ASCII (kedua output sekaligus)
- Excel: `generate_excel_visual()` — colored grid cells, series-level labels
- ASCII: `generate_ascii_visual()` — box-drawing layout, series abbreviations + tier

### Step 4: Output & Validate
- Verify semua display units ter-render
- Verify warna series konsisten (check SERIES_COLORS dict)
- Verify artikel count matches Step 1 data
- Verify spatial layout matches physical store layout

## Jika layout config belum ada untuk toko:

1. Cek portal_planogram file untuk region tersebut
2. Jika ada: extract layout positions dari sheet toko tersebut (merged cells = display unit boundaries)
3. Jika tidak ada: buat default layout berdasarkan display component list dari `Data Option By Region.xlsx`
4. Tanyakan user jika posisi fisik tidak jelas

## Jika user tanya soal format/rules:

Jawab berdasarkan Section 1-3 di atas. Jangan mengarang format baru — ikuti existing portal planogram convention.

## Jika user minta tambah series baru:

1. Tambahkan ke `SERIES_COLORS` dict (hex tanpa #, untuk openpyxl)
2. Tambahkan ke `SERIES_ABBREV` dict (max 3 chars)
3. Script akan auto-generate pastel color jika series tidak ditemukan di dict

---

*Version: 1.2 — Updated v3 references, added shelving/table/mixed-BW visual elements, portal interpretation guide*
*Last Updated: 10 February 2026*
*Prerequisite: SKILL_planogram_zuma_v3.md v3.2 (Step 1 must complete first)*
*Changelog:*
- *v1.2: Fixed v2→v3 reference in description/prerequisite*
- *v1.2: Added Section 1.3.3 Shelving & Table display visual elements*
- *v1.2: Added Section 1.3.4 KURSI to non-display elements*
- *v1.2: Added Portal Layout Interpretation Guide (how to read "7 BARIS", "8X7")*
- *v1.1: Implementation reference and verified output specs*
