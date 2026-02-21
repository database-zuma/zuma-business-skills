# RO & Surplus TRANSISI — Output Format & Reference

> Supporting reference for [`SKILL.md`](SKILL.md). Contains the full cycle diagram, Excel output specifications, styling, worked examples, and known limitations.

---

## SIKLUS LENGKAP — TRANSISI (Urgent -> RO Budget-Capped -> Surplus)

```
┌─────────────────────────────────────────────────────────────┐
│                    ALLOCATION PLANNER                        │
│              (Control & Approve semua flow)                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
         ══════════════════════════════════════════
         ║  TAHAP 0: IDENTIFIKASI URGENT SURPLUS  ║
         ══════════════════════════════════════════
                           │
                           ▼
              ┌──────────────────────────────┐
              │ Scan semua artikel di toko    │
              │ vs planogram baru             │
              └──────────────┬───────────────┘
                             │
                 ┌───── ada di plano? ─────┐
                 │                         │
                 YES                       NO
                 (on-plano)                (off-plano)
                 │                         │
                 ▼                         ▼
              OK, lanjut              URGENT SURPLUS
              ke TAHAP 1              Total = N pairs
                                      = RO BUDGET
                           │
         ══════════════════════════════════════════
         ║  TAHAP 1: RESTOCK (Budget = Urgent)    ║
         ══════════════════════════════════════════
                           │
                           ▼
                  ┌────────────────┐
                  │ Hitung size    │
                  │ kosong per     │
                  │ artikel        │
                  └──┬──────────┬──┘
                     │          │
               3+ size │    1-2 size │
               kosong  │    kosong   │
                     ▼          ▼
              ⭐ RO BOX    RO PROTOL
              (DEFAULT)    (minor gap)
                     │          │
                     └────┬─────┘
                          ▼
              ┌─────────────────────────────┐
              │ CAP RO TO BUDGET            │
              │ Priority:                   │
              │ 1. ≥50% sizes empty FIRST   │
              │ 2. Best sellers SECOND      │
              │ Total RO ≈ urgent pairs     │
              └────────────┬────────────────┘
                           │
                           ▼
              ┌──────────┐  ┌──────────────┐
              │ GUDANG   │  │ GUDANG       │
              │ BOX      │  │ PROTOL       │
              └────┬─────┘  └──────┬───────┘
                   │               │
                   ▼               ▼
              ┌─────────────────────────────────────┐
              │              TOKO                    │
              │   Restock masuk → display lengkap    │
              │   Pairs IN ≈ Pairs OUT (urgent)     │
              └──────────────────┬──────────────────┘
                                 │
         ══════════════════════════════════════════
         ║  TAHAP 2: SURPLUS (URGENT + REGULAR)   ║
         ══════════════════════════════════════════
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
        URGENT SURPLUS             REGULAR SURPLUS
        (off-planogram)            (on-plano, over-capacity)
        HARUS ditarik              Visibility/planning only
                    │                         │
                    └────────────┬─────────────┘
                                 ▼
              ┌─────────────────┐
              │  GUDANG PROTOL   │◄── Semua surplus masuk sini
              │  (pool per size) │
              └────────┬────────┘
                       │
                       ▼
              Ada toko lain butuh?
              ├── Ya ──► Kirim protol
              └── Tidak ──► Stay di gudang
```

---

## Output Format: Excel (.xlsx) — 5 Sheets

The output is an official document format with cover page and signature block.

### Sheet 1: "RO Request" (Cover Page)

```
Row 2:  WEEKLY RO REQUEST                          (bold, 16pt, green fill)
Row 3:  {Store Name}                               (bold, 14pt)
Row 5:  Week of:          {date}
Row 6:  Stock Snapshot:   {date}
Row 7:  Storage Capacity: {N} boxes
Row 9:  From:  Area Supervisor     ___________________________
Row 10: To:    Warehouse Supervisor ___________________________

Row 12: REQUEST SUMMARY                            (bold, green fill)
Row 13: Type | Articles | Total | Source/Destination | See Sheet  (header row, bold)
Row 14: RO PROTOL                   | {N} | {N} pairs | FROM: WH Pusat Protol | Daftar RO Protol
Row 15: RO BOX                      | {N} | {N} boxes | FROM: WH Pusat Box    | Daftar RO Box
Row 16: SURPLUS — URGENT (off-plano) | {N} | {N} pairs | TO: WH Pusat Protol   | Daftar Surplus
Row 17: SURPLUS — REGULAR (over-cap) | {N} | {N} pairs | (visibility only)     | Daftar Surplus
Row 18: SURPLUS TOTAL                | {N} | {N} pairs | TO: WH Pusat Protol   | Daftar Surplus

Row 19: INSTRUCTIONS
Row 20-24: (numbered instructions — restock+surplus same day, priority protol first)

Row 27: SIGNATURES
Row 28: [Prepared by] [Approved by] [Received by]
Row 29-31: Name/Date/Signature lines
```

### Sheet 2: "Daftar RO Protol" (One Row Per Article)

```
Header rows 1-4: title, store, date, source info
Row 6 (header): No | Article | Kode Mix | Tier | Sizes Needed (size:qty) | Total Pairs
Row 7+: numbered data rows

Example row:
  1 | LADIES FLO 1, BLACK | L1FL0LV101 | 1 | 36:1, 37:2, 38:4, 39:3, 40:2 | 12

Last row: TOTAL PAIRS = {sum}
```

**Key format**: Sizes Needed uses `size:qty` format, comma-separated. This shows the WH picker exactly which sizes and how many pairs to pick.

**Sorting**: By Tier ASC, then by Article name ASC within each tier.

### Sheet 3: "Daftar RO Box" (One Row Per Article, 1 Box)

```
Header rows 1-4: title, store, date, source info + "Total: {N} boxes"
Row 6 (header): No | Article | Kode Mix | Tier | Box Qty | WH Available
Row 7+: numbered data rows

Example row:
  1 | LADIES CLASSIC 1, JET BLACK | SJ2ACAV201 | 1 | 1 | NO

Last row: TOTAL BOXES = {sum}
```

**Key format**: Box Qty is always 1 (1 box = 12 pairs, all sizes). WH Available shows YES/NO based on warehouse stock check.

**Sorting**: By Tier ASC, then by Article name ASC within each tier.

### Sheet 4: "Daftar Surplus" (Two Sections — URGENT + REGULAR)

```
Header rows 1-4: title, store, date, destination info

=== SECTION 1: URGENT SURPLUS (Off-Planogram) — Orange highlight ===
Row N (section header): "URGENT SURPLUS — Off-Planogram (HARUS DITARIK)"
Row N+1 (header): No | Article | Kode Mix | Tier | Avg Monthly Sales | Size | Pairs to Pull
Row N+2+: data rows (one row per article+size)
Subtotal row: URGENT SUBTOTAL: {N} articles, {N} pairs

=== SECTION 2: REGULAR SURPLUS (Over-Capacity) — Purple highlight ===
Row M (section header): "REGULAR SURPLUS — Over-Capacity (Visibility Only)"
Row M+1 (header): No | Article | Kode Mix | Size | Pairs to Pull
Row M+2+: data rows (one row per article+size)
Subtotal row: REGULAR SUBTOTAL: {N} articles, {N} pairs

=== GRAND TOTAL ===
Grand total row: GRAND TOTAL: {N} articles, {N} pairs
```

**Key changes from old format**:
- Two distinct sections with different colors (orange = urgent/action, purple = regular/info)
- URGENT section has extra columns: Tier, Avg Monthly Sales (for planner context)
- REGULAR surplus is **visibility/planning only** — not actioned this week
- Grand total combines both sections

**Sorting**: URGENT by avg_monthly_sales ASC (slowest first). REGULAR by avg_monthly_sales ASC.

### Sheet 5: "Reference" (Internal Use Only)

```
Row 1: REFERENCE DATA (Internal Use)

Section 1 — Tier Capacity Analysis:
  Tier | Ideal (Planogram) | Ideal % | Actual (Stock) | Actual % | Diff | Status

Section 2 — Full Article Status:
  Article | Kode Mix | Gender | Series | Tier | Target | Actual | Gap | % Kosong | RO Type | Avg Monthly Sales | Stock Coverage

Section 3 — Off-Planogram Articles (if any):
  Articles found in store stock but NOT in planogram — flagged for review.
```

---

## Styling Reference (openpyxl)

The Excel output uses consistent branding:

| Element | Style |
|---------|-------|
| Title row | Font 16pt bold, fill `#00E273` (Zuma Green), white text |
| Store name | Font 14pt bold |
| Section headers | Font 12pt bold, fill `#00E273` |
| Table headers | Font 10pt bold, fill `#2E7D32` (dark green), white text |
| Data rows | Font 10pt, alternating white/`#E8F5E9` (light green) |
| Borders | Thin borders on all data cells |
| Column widths | Auto-fit with min/max constraints |
| Summary values | Bold, right-aligned |
| Total row | Bold, top border |

---

## Example Output (Royal Plaza, 10 Feb 2026)

| Metric | Count |
|--------|-------|
| RO Protol articles | 47 |
| RO Protol total pairs | 208 |
| RO Box articles | 42 |
| RO Box total boxes | 42 |
| Surplus articles | 24 |
| Surplus total pairs | 179 |
| Off-Planogram articles | 41 |

---

## Known Limitations & Pending Clarifications

1. **TO Metric** — Two definitions coexist in Zuma:
   - (a) Stock Coverage = stock / monthly_sales (months of stock remaining). High = slow.
   - (b) Turnover Rate = monthly_sales / stock (sales velocity). Low = slow.
   Script outputs both. Surplus sorts by `avg_monthly_sales ASC` which is unambiguous.
   -> **PENDING**: Ask Allocation Planner team which label to standardize on.

2. **Ideal Tier Capacity %** — No official per-store tier targets exist yet. Script derives ideal from planogram article count per tier.
   -> **PENDING**: Ask Planner for real per-store tier capacity targets.

3. **RO Protol Total Pairs accuracy** — Some `Total Pairs` show 0 because WH Protol stock for those sizes is 0. The "Sizes Needed" column still shows what's needed, but total reflects what can actually be fulfilled.

4. **Storage = 0 stores** — Every RO Box creates immediate surplus for sizes already in stock. In TRANSISI logic this is **accepted behavior** — surplus is automatically calculated and pulled in TAHAP 2. No pre-plan needed.
