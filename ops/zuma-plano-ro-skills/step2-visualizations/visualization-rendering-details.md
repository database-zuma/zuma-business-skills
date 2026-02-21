# Visualization Rendering Details

> Referenced from `SKILL.md`. Contains full color palettes, rendering specs, grid system, matplotlib/openpyxl code, and gotchas.

---

## 1. Color Palette — Series Colors

Setiap series punya warna KONSISTEN di seluruh visualisasi:

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

### Tier Color Coding (Alternative Mode)

Color-by-tier sebagai alternatif color-by-series:

| Tier | Color | Hex |
|------|-------|-----|
| T1 | Green | `#C6EFCE` |
| T8 | Blue | `#BDD7EE` |
| T2 | Yellow | `#FFFFCC` |
| T3 | Grey | `#D9D9D9` |

---

## 2. Shelving, Table & Special Display Elements

| Element | Style | Notes |
|---------|-------|-------|
| SHELVING (Airmove, Puffy, etc.) | Light blue/green bg, dashed border | Label: "SHELVING [SERIES]", list articles inside |
| TABLE LUCA LUNA | White bg, thick border, centered | Label: "TABLE LUCA LUNA", list articles |
| TABLE BABY | Light yellow bg, thick border | Label: "TABLE BABY", list articles |
| MIXED-HOOK BW | Single block, internal divider line | Split sections with different colors per section |

**Rendering rules:**
- Shelving terintegrasi di BW: render sebagai kolom terakhir di BW dengan warna/style berbeda + label "SHELVING"
- Shelving standalone: render sebagai blok terpisah di layout
- Table: render sebagai rectangle dengan list artikel di dalamnya
- Mixed BW (e.g., BW-4a Elsa + Classic): render sebagai satu blok fisik, tapi beri garis pemisah antara section dan label per section

### Non-Display Elements

| Element | Style |
|---------|-------|
| KASIR (Cashier) | White bg, black border, centered text |
| KURSI (Chair/Seating) | White bg, thin border, centered text |
| ENTRANCE / Depan | Arrow/text marker |
| EMPTY HOOKS | Dotted border or light fill |
| WALLS | Thick black border on exterior |

---

## 3. Grid System & Dimensions

### Portal Layout Interpretation Guide

Portal planogram punya layout visual di kolom tinggi (biasanya AX-BW). Konvensi:

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

Dimensi "NxM":
- **N** = jumlah kolom (articles per baris horizontal)
- **M** = jumlah baris (rows, biasanya = 7 untuk standard backwall height)

Contoh:
- "8X7" = 8 article slots wide, 7 rows tall = display untuk 8 articles
- "7X7" = 7 article slots wide, 7 rows tall = display untuk 7 articles

**PENTING**: Baris (rows) menunjukkan DEPTH of display (tumpukan size), bukan jumlah artikel tambahan. 1 kolom = 1 artikel.

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

## 4. Matplotlib Drawing Code

### Core Drawing Logic

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
            rect = patches.Rectangle((x, y), w, h, 
                                     linewidth=2, edgecolor='black',
                                     facecolor='white')
            ax.add_patch(rect)
            ax.text(x + w/2, y + h/2, unit["label"],
                    ha='center', va='center', fontsize=8, fontweight='bold')
        
        elif unit["type"] in ("backwall", "gondola"):
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
    
    # Unit label (above)
    ax.text(x + w/2, y - 0.3, unit["label"],
            ha='center', va='bottom', fontsize=6, fontweight='bold')
```

### Series Color Function

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

---

## 5. Excel Visual Code (openpyxl)

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

---

## 6. Detail-Level Variants

Planogram visual bisa dibuat dalam beberapa level detail:

### Level 1: Series-Level (untuk overview cepat) — DEFAULT
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

---

## 7. Gotchas

### Data Flow Gotchas

| Gotcha | Penjelasan | Solusi |
|--------|-----------|--------|
| **Step 1 XLSX sheet naming** | Sheet names include gender-type (e.g., "BW-2 Ladies Fashion") | Split sheet name by first space to get BW-ID |
| **Series name from Step 1** | Step 1 output has `series` column in article data | Map series -> color using SERIES_COLORS dict |
| **Orientation depends on physical wall** | Left/right walls = vertical. Top/bottom = horizontal | Get from store layout config or portal reference |
| **Canvas size varies per store** | Small stores = smaller canvas. Mall stores = larger | Scale canvas_size proportionally |

### Drawing Gotchas

| Gotcha | Penjelasan | Solusi |
|--------|-----------|--------|
| **Text overflow in small cells** | Article names too long for cell width | Use series name (shorter) or abbreviate |
| **matplotlib text rotation** | Vertical orientation needs rotated text | Use `rotation=90` for narrow cells |
| **DPI for print quality** | Default 72 DPI too low for print | Use `dpi=150` minimum, `dpi=300` for A3 |
| **Windows font rendering** | Some fonts render differently | Use `fontfamily='sans-serif'` for consistency |
| **Color overlap** | Adjacent same-series cells look like 1 block | Add thin black border per cell |

### Excel Visual Gotchas

| Gotcha | Penjelasan | Solusi |
|--------|-----------|--------|
| **Merged cells** | openpyxl merged cells only keep value in top-left | Set value + style on top-left, then merge |
| **Column width** | Default too wide for grid cells | Set all grid columns to width=3.0 |
| **Row height** | Default too tall | Set grid rows to height=15 |
| **Color application** | PatternFill needs `fill_type="solid"` | Always include `fill_type="solid"` |

### Layout Config Gotchas

| Gotcha | Penjelasan | Solusi |
|--------|-----------|--------|
| **Portal format varies** | Beberapa stores punya layout, beberapa tidak | Check merged cells first. If none, build from scratch |
| **Coordinate system** | Excel = (col, row), matplotlib = (x, y). Both top-left | Keep consistent: (x, y) = (column, row) |
| **Display unit IDs must match** | BW-1 in layout config MUST match BW-1 in Step 1 | Verify IDs before rendering |

---

## 8. Output Specifications (Verified)

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

### Verified Output Stats (Royal Plaza)
```
BW-1 Men Jepit:      23/24 articles (1 empty slot)
BW-2 Ladies Fashion: 18/18 articles
BW-3 Men Fashion:    18/18 articles
BW-4 Baby & Kids:    26/26 articles
Rak Baby:            2/2 layers
Total:               87/88 slots (98.9% utilization)
Unique series:       23
```
