---
name: visualized-planogram-zuma
version: "1.0"
description: >
  Tool untuk membuat VISUALISASI planogram (bird's-eye floor plan) toko Zuma dari output XLSX planogram Step 1.
  Menghasilkan gambar layout fisik toko dengan penempatan artikel per hook, color-coded per series/tier.
  Gunakan setelah planogram Step 1 selesai menghasilkan XLSX.
  Use when asked to visualize planogram, create store layout image, generate floor plan, or render planogram visually.
dependencies:
  - zuma-plano-and-ro/step1-planogram/planogram-zuma
user-invocable: true
---

# Planogram Visualization Engine — Zuma

Kamu adalah PLANOGRAM VISUALIZER untuk ZUMA Footwear Retail. Tugasmu mengubah output data planogram (XLSX dari Step 1) menjadi **gambar visual bird's-eye floor plan** yang menunjukkan penempatan fisik setiap artikel di toko.

**Prerequisite:** Step 1 harus sudah selesai — yaitu XLSX planogram dari `planogram-zuma` skill / `build_*_planogram.py` sudah dihasilkan.

---

## Reference Files

| File | Contents |
|------|----------|
| `visualization-rendering-details.md` | Full color palettes, matplotlib/openpyxl code, grid system, positioning formulas, gotchas |
| `visualization-examples.md` | Worked examples, store layout configs (Royal Plaza), parsing strategy, how to add stores |
| `visualize_planogram.py` | **Main script** — generates Excel + ASCII floor plan for Royal Plaza |
| `visualize_tunjungan_planogram.py` | **Tunjungan variant** — store-specific visualization script |

---

# SECTION 1: KONSEP & FORMAT VISUAL

## 1.1 Apa itu Visualisasi Planogram

Visualisasi planogram adalah **peta bird's-eye** dari layout fisik toko. Setiap display unit (backwall, gondola, rak, table) digambar sebagai rectangle di peta, dan setiap hook/slot diisi dengan nama artikel + warna series.

Output berupa gambar PNG atau Excel sheet yang bisa langsung dicetak/ditampilkan di toko sebagai panduan penempatan produk oleh SPG.

> For ASCII layout example and visual element reference, see `visualization-examples.md` Section 1.

## 1.2 Color Coding Rules

### Series Colors (Summary)

Setiap series punya warna KONSISTEN. Key mappings:

| Series | Hex | Series | Hex |
|--------|-----|--------|-----|
| ZORRO | `#EAD1DC` | FLO | `#F9CB9C` |
| DALLAS | `#E6B8AF` | PUFFY | `#A4C2F4` |
| SLIDE | `#FFF2CC` | ELSA | `#CCCCCC` |
| CLASSIC | `#FFF2CC` | MERCI | `#D9D2E9` |
| BABY CLASSIC | `#00FFFF` | BABY KARAKTER | `#B7E1CD` |
| KIDS CLASSIC | `#B6D7A8` | LUNA | `#D5A6BD` |

**Series baru tanpa warna** → auto-generate pastel via MD5 hash.

> For COMPLETE color palette (30+ series), tier colors, shelving/table styles, and non-display elements, see `visualization-rendering-details.md` Sections 1-2.

## 1.3 Display Element Types

| Type | Description |
|------|------------|
| **Backwall/Gondola** | Main display — colored cells per article, horizontal or vertical orientation |
| **Rak Baby** | Layer-based display — 1 layer = 1 row |
| **Shelving** | Integrated in BW (last column) or standalone block |
| **Table** | Rectangle with article list inside (Luca Luna, Baby) |
| **Mixed-hook BW** | Single physical block with divider lines between sections |
| **Landmarks** | KASIR, KURSI, ENTRANCE, AIRMOVE — bordered rectangles, no articles |

> For detailed rendering rules per element type, see `visualization-rendering-details.md` Section 2.

## 1.4 Dimensions & Grid

- **"NxM"** format: N = article columns, M = hook rows (usually 7)
- **1 column = 1 article** — rows show depth/stacking, NOT additional articles
- Fashion: 3 hooks/article → N articles = N×3 hooks
- Jepit: 2 hooks/article → N articles = N×2 hooks

> For full grid system, portal interpretation guide, and Step 1→grid mapping, see `visualization-rendering-details.md` Section 3.

---

# SECTION 2: INPUT & OUTPUT

## 2.1 Input yang Dibutuhkan

| No | Data | Source |
|----|------|--------|
| 1 | **PLANOGRAM XLSX (Step 1 output)** | `PLANOGRAM_[StoreName].xlsx` — sheets per backwall + Rak Baby + Summary |
| 2 | **Store layout reference** | `portal_planogram_jatim.xlsx` atau manual config |
| 3 | **Series color mapping** | SERIES_COLORS dict (see rendering-details) |

### From PLANOGRAM XLSX (per backwall sheet):
- Backwall ID, Gender-Type, jumlah hooks
- Daftar artikel + posisi hook (rows: Artikel, Tier & Avg, Series)
- Mode (Full Box / Compact)

### From Store Layout Reference:
- Posisi relatif display units (kiri, kanan, depan, belakang)
- Adjacency — display mana yang bersebelahan
- Non-display landmarks — kasir, pintu masuk, airmove

## 2.2 Output Formats

### Option A: Excel Floor Plan (IMPLEMENTED)

File `VISUAL_PLANOGRAM_[Store].xlsx` — single sheet "Layout Visual":
- Bird's eye floor plan with grid cells
- Narrow columns (width=4), short rows (height=18)
- Colored rectangle per display unit (PatternFill by series)
- Horizontal BW: 2 rows (series name + article short name)
- Vertical BW: 1 row per article, 3 cols (series + article + tier)
- Landmarks as merged cells with thick border
- Legend + header + entrance label
- **Library**: `openpyxl` only

### Option B: ASCII Floor Plan (IMPLEMENTED)

File `VISUAL_PLANOGRAM_[Store].txt` — ~115 chars wide:
- Box-drawing with ASCII (+, -, |)
- Top: horizontal BW side-by-side → Middle: vertical BW + landmarks → Bottom: ENTRANCE
- 3-char series abbreviations + tier (e.g., "ZRO T1")
- Legend + summary stats

### Option C: Both (DEFAULT)

Generate Excel + ASCII simultaneously from single parse pass.

> For detailed output specs and verified stats, see `visualization-rendering-details.md` Section 8.

---

# SECTION 3: VISUALIZATION PIPELINE

## 3.1 Execution Order

```
1. PARSE: Read Step 1 PLANOGRAM XLSX
   → Extract articles per backwall (slot-index iteration, stride = hooks_per_article)
   → Extract rak baby assignments
   → Extract summary stats from Summary Report sheet

2. LAYOUT: Load store layout config
   → Grid coordinates for each display unit
   → Orientation (horizontal/vertical) per backwall
   → Landmark positions (KASIR, AIRMOVE)

3. EXCEL VISUAL: generate_excel_visual()
   → Create workbook with "Layout Visual" sheet
   → Draw each backwall as colored cell grid
   → Draw landmarks as bordered merged cells
   → Add title, entrance, legend, summary

4. ASCII VISUAL: generate_ascii_visual()
   → Render horizontal BW as top blocks (side-by-side)
   → Render vertical BW as side columns
   → Render center area with landmarks
   → Add legend (abbreviation mapping) + summary stats

5. SAVE:
   → XLSX: VISUAL_PLANOGRAM_[Store].xlsx
   → TXT:  VISUAL_PLANOGRAM_[Store].txt
   → Print ASCII preview to stdout
```

## 3.2 Implementation Scripts

### Main Script: `visualize_planogram.py`

Architecture:
```
CONFIG → PARSE → LAYOUT CONFIG → EXCEL VISUAL → ASCII VISUAL → OUTPUT
```

Key functions:
- `parse_planogram_xlsx(filepath)` — main parser
- `parse_backwall_sheet(ws, bw_id)` — per-BW sheet parser
- `generate_excel_visual()` — Excel floor plan generator
- `generate_ascii_visual()` — ASCII floor plan generator

### Tunjungan Variant: `visualize_tunjungan_planogram.py`

Store-specific script with Tunjungan layout config.

> For full script architecture tree, parsing strategy (slot-index iteration), and code examples, see `visualization-examples.md` Sections 4-5.

## 3.3 File Naming Convention

```
Input:  ../PLANOGRAM_Royal_Plaza.xlsx         (from Step 1, parent dir)
Output: VISUAL_PLANOGRAM_Royal_Plaza.xlsx     (Excel floor plan)
Output: VISUAL_PLANOGRAM_Royal_Plaza.txt      (ASCII floor plan)
```

## 3.4 Detail-Level Variants

| Level | Cell Content | Color By | Use Case |
|-------|-------------|----------|----------|
| **Level 1** (DEFAULT) | Series name | Series | Overview, portal format |
| **Level 2** | Full article name | Series | Detail placement, print A3/A2 |
| **Level 3** | Article + tier + avg | Tier | Internal analysis review |

> For full detail-level descriptions, see `visualization-rendering-details.md` Section 6.

---

# SECTION 4: STORE LAYOUT MANAGEMENT

## 4.1 Layout Config per Store

Each store needs a layout config dict defining:
- `store_name`, `canvas_size` (grid units)
- `display_units[]` — each with `id`, `type`, `label`, `position`, `size`, `orientation`
- Landmarks — KASIR, ENTRANCE, AIRMOVE positions

**Currently implemented:**
- Royal Plaza — in `visualize_planogram.py`
- Tunjungan — in `visualize_tunjungan_planogram.py`

> For complete Royal Plaza config and generic config template, see `visualization-examples.md` Sections 2-3.

## 4.2 Adding a New Store

1. Update `INPUT_FILE` to new store's PLANOGRAM XLSX
2. Create new layout config (copy existing and modify positions)
3. Derive positions from `portal_planogram_[region].xlsx` merged cells
4. If portal unavailable — ask BM/AS for floor photo and approximate

> For step-by-step guide with code template, see `visualization-examples.md` Section 6.

---

# SECTION 5: KEY GOTCHAS (Summary)

| Area | Key Issue | Quick Fix |
|------|-----------|-----------|
| **Parsing** | Sheet names include gender-type ("BW-2 Ladies Fashion") | Split by first space for BW-ID |
| **Parsing** | Merged cells only store value in top-left | Iterate by slot index, not cell-by-cell |
| **Drawing** | Text overflow in small cells | Use series name (shorter) or abbreviate |
| **Drawing** | DPI too low for print | Min `dpi=150`, use `dpi=300` for A3 |
| **Excel** | PatternFill needs `fill_type="solid"` | Always include parameter |
| **Excel** | Column width too wide for grid | Set all to width=3.0 |
| **Layout** | BW IDs must match between layout config and Step 1 | Verify before rendering |
| **Layout** | Portal format varies per store | Check merged cells first; build from scratch if none |

> For COMPLETE gotcha tables (data flow, drawing, Excel, layout), see `visualization-rendering-details.md` Section 7.

---

# SECTION 6: CARA MENJAWAB

## Jika user minta buatkan visualisasi planogram:

### Step 1: Validasi Input
- Pastikan Step 1 XLSX sudah ada (`PLANOGRAM_[Store].xlsx`)
- Pastikan store layout reference tersedia (portal file atau manual config)

### Step 2: Parse Data
- Jalankan `parse_planogram_xlsx()` untuk extract per-backwall article assignments
- Load store layout config (existing atau buat baru untuk toko lain)

### Step 3: Generate Visual
- **Default**: Generate BOTH Excel + ASCII (kedua output sekaligus)
- Use `visualize_planogram.py` as base (or `visualize_tunjungan_planogram.py` for Tunjungan)
- Excel: `generate_excel_visual()` — colored grid cells, series-level labels
- ASCII: `generate_ascii_visual()` — box-drawing layout, series abbreviations + tier

### Step 4: Output & Validate
- Verify semua display units ter-render
- Verify warna series konsisten (check SERIES_COLORS dict)
- Verify artikel count matches Step 1 data
- Verify spatial layout matches physical store layout

## Jika layout config belum ada untuk toko:

1. Cek portal_planogram file untuk region tersebut
2. Jika ada: extract layout positions dari sheet toko (merged cells = display unit boundaries)
3. Jika tidak ada: buat default layout dari `Data Option By Region.xlsx` display components
4. Tanyakan user jika posisi fisik tidak jelas

> For layout derivation details, see `visualization-examples.md` Section 6.

## Jika user tanya soal format/rules:

Jawab berdasarkan skill ini + reference files. Jangan mengarang format baru — ikuti existing portal planogram convention.

## Jika user minta tambah series baru:

1. Tambahkan ke `SERIES_COLORS` dict di script
2. Tambahkan ke `SERIES_ABBREV` dict (max 3 chars)
3. Script auto-generates pastel color jika series tidak ditemukan

---

*Version: 1.3 — Split to reference files for maintainability*
*Last Updated: 21 February 2026*
*Prerequisite: planogram-zuma skill (Step 1 must complete first)*
*Changelog:*
- *v1.3: Split 921-line SKILL.md → core SKILL.md + visualization-rendering-details.md + visualization-examples.md*
- *v1.2: Fixed v2→v3 reference in description/prerequisite*
- *v1.2: Added Shelving & Table display visual elements*
- *v1.2: Added KURSI to non-display elements*
- *v1.2: Added Portal Layout Interpretation Guide*
- *v1.1: Implementation reference and verified output specs*
