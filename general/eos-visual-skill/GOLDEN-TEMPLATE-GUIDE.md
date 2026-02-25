# GOLDEN TEMPLATE — Usage Guide for Eos 🌅

**File:** `GOLDEN-TEMPLATE.html`  
**Purpose:** Copy-paste foundation for ALL Zuma decks. Never design from scratch again.

---

## 🎯 Golden Rule

**DON'T design. COPY this template and SWAP the placeholders.**

This template is pixel-perfect **Mixed Executive Report** design. It already has:
- ✅ Correct colors (light bg `#FFFFFF` for content, dark `#1A1A1A` for highlights)
- ✅ Dark header band `#002A3A` on every content slide
- ✅ Proper spacing (generous padding, 16px rounded corners)
- ✅ Chart.js dual-mode setup (light for content slides, dark for highlight slides)
- ✅ Responsive navigation
- ✅ Print-friendly CSS

Your job: Replace `{{PLACEHOLDERS}}` with actual data. That's it.

---

## 📋 Slide Types (5 Templates)

### 1. COVER SLIDE (Slide 1)
**Mode: DARK** — highlight page  
**Use for:** Title page, report introduction

**Placeholders to swap:**
```
{{DECK_TITLE}}        → "Ladies Merci Sales Performance"
{{DECK_SUBTITLE}}     → "Analysis by color variant — February 2026"
{{PERIOD}}            → "February 2026"
{{AUTHOR}}            → "Iris / Argus"
```

**When to use:** Every deck starts here. Always.

---

### 2. METRICS SLIDE (Slide 2)
**Mode: LIGHT** — content page  
**Use for:** KPI overview, key numbers

**Placeholders to swap:**
```
{{SECTION_LABEL}}     → "Sales Summary"
{{SLIDE_HEADLINE}}    → "Top-Line Metrics"

{{METRIC_1_LABEL}}    → "Total Volume"
{{METRIC_1_VALUE}}    → "1,784"
{{METRIC_1_UNIT}}     → "pairs"
{{METRIC_1_DELTA}}    → "+12%" (use z-badge-success/warning/danger)
{{METRIC_1_CONTEXT}}  → "Strong growth vs January"

{{KEY_INSIGHT_TEXT}}  → "Mocca variant driving 35% of total volume"
```

**Grid options:**
- 2 cards: `grid-cols-2`
- 3 cards: `grid-cols-3`
- 4 cards: `grid-cols-2` with 2 rows (copy card template)

---

### 3. CHART BREAKDOWN (Slide 3)
**Mode: LIGHT** — content page  
**Use for:** Composition data (color breakdown, category share, etc.)

**Placeholders to swap:**
```
{{SECTION_LABEL}}     → "Color Breakdown"
{{SLIDE_HEADLINE}}    → "Performance by Color"
{{TOTAL_VALUE}}       → "1,784"
{{TOTAL_LABEL}}       → "Total Pairs"

{{ITEM_1_NAME}}       → "Mocca"
{{ITEM_1_VALUE}}      → "627"
{{ITEM_1_VALUE_RAW}}  → 627 (number for chart)
{{ITEM_1_PERCENT}}    → "35.15"
{{ITEM_1_COLOR}}      → "#8B6F47" (actual product color!)
{{ITEM_1_RANK}}       → "#1 Bestseller"

{{ITEM_2_NAME}}       → "Wine"
{{ITEM_2_VALUE}}      → "402"
{{ITEM_2_COLOR}}      → "#722F37"

{{ITEM_3_NAME}}       → "Black"
{{ITEM_3_VALUE}}      → "322"
{{ITEM_3_COLOR}}      → "#1A1A1A"
```

**Chart colors — USE ACTUAL PRODUCT COLORS:**
- Mocca (brown shoe) → `#8B6F47`
- Wine (maroon shoe) → `#722F37`
- Black (black shoe) → `#1A1A1A`
- White (white shoe) → `#E8E8E8`
- Navy (blue shoe) → `#1E3A5F`

**Don't use generic chart colors for fashion data!** Use the actual shoe colors.

---

### 4. DATA TABLE (Slide 4)
**Mode: LIGHT** — content page  
**Use for:** Rankings, comparisons, detailed lists

**Placeholders to swap:**
```
{{SECTION_LABEL}}     → "Store Performance"
{{SLIDE_HEADLINE}}    → "Top Performing Stores"

{{COL_1_HEADER}}      → "Store"
{{COL_2_HEADER}}      → "Revenue"
{{COL_3_HEADER}}      → "Units"
{{COL_4_HEADER}}      → "Growth"
{{COL_5_HEADER}}      → "Progress"

{{ROW_1_COL_1}}       → "Zuma Galaxy Mall"
{{ROW_1_COL_2}}       → "Rp 89.2M"
{{ROW_1_COL_3}}       → "412"
{{ROW_1_COL_4}}       → "+24%"
{{ROW_1_PROGRESS}}    → 85 (percentage for bar)

{{TABLE_FOOTNOTE}}    → "Data includes retail channels only"
```

**Badges:**
- Positive: `z-badge-success` (green)
- Warning: `z-badge-warning` (amber)
- Negative: `z-badge-danger` (red)

---

### 5. INSIGHTS / ACTION ITEMS (Slide 5)
**Mode: DARK** — closing highlight page  
**Use for:** Final slide, conclusions, next steps

**Placeholders to swap:**
```
{{SLIDE_HEADLINE}}    → "Strategic Directives"

{{INSIGHT_1_TITLE}}   → "Mocca Dominates"
{{INSIGHT_1_TEXT}}    → "Earth tones continue to outperform..."

{{INSIGHT_2_TITLE}}   → "Wine as Alternative"
{{INSIGHT_2_TEXT}}    → "Bold colors drive secondary volume..."

{{INSIGHT_3_TITLE}}   → "Restocking Priority"
{{INSIGHT_3_TEXT}}    → "Focus inventory investment on top 2 colors"

{{ACTION_1}}          → "Increase Mocca stock by 25%"
{{ACTION_1_OWNER}}    → "Ops Team"
{{ACTION_1_DEADLINE}} → "March 15"

{{DECK_FOOTER}}       → "Zuma Indonesia • February 2026 • Confidential"
```

---

## 🎨 Color Reference

### Light Mode (DEFAULT — content slides: KPI, Chart, Table, Framework, Recommendation)

| Token | Value | Usage |
|-------|-------|-------|
| Page BG | `#FFFFFF` | Content slide backgrounds |
| Page BG Alt | `#F8FAFC` | Alternating section bg |
| Header Band | `#002A3A` | Dark strip at top of each content slide |
| Card BG | `#FFFFFF` | Cards on light bg |
| Card Border | `rgba(0,42,58,0.08)` | Subtle border on white cards |
| Text Primary | `#1A202C` | Headlines, body on light bg |
| Text Secondary | `#4A5568` | Labels, supporting text |
| Text Muted | `#718096` | Captions, timestamps |
| Accent | `#00E273` | CTAs, indicators, positive |
| Negative | `#FF4D4D` | Declines, at-risk |
| Warning | `#FFB800` | Caution, moderate alerts |
| Border | `rgba(0,42,58,0.06)` | Card/table borders on light |

### Dark Mode (HIGHLIGHT — Cover, Section Divider, closing slides only)

| Token | Value | Usage |
|-------|-------|-------|
| Page BG | `#1A1A1A` | Dark highlight slide backgrounds |
| Card BG | `#002A3A` | Cards on dark bg |
| Card Alt | `#0A3D50` | Secondary cards, So What box |
| Text Primary | `#FFFFFF` | Headlines on dark bg |
| Text Secondary | `#8CA3AD` | Labels on dark bg |
| Text Muted | `#5A7A87` | Captions on dark bg |
| Accent | `#00E273` | Same green — consistent |
| Border | `rgba(255,255,255,0.08)` | Card borders on dark |

---

## 🚫 Never Do This

❌ **Don't freestyle colors** — Always use the tokens above  
❌ **Don't use shadows** — Depth comes from brightness only  
❌ **Don't use gradients** — Flat colors only  
❌ **Don't put green (#00E273) on body text** — Use for fills, borders, CTAs only  
❌ **Don't make ALL slides dark** — Dark is ONLY for Cover, Section Divider, and closing slides (Next Steps). Content slides MUST be light.  
❌ **Don't use dark bg on content slides** (KPI, Chart, Table, Framework, Recommendation) — those are LIGHT mode  
❌ **Don't use default Chart.js colors** — Set theme properly (light or dark depending on slide mode)  
❌ **Don't use random chart colors for fashion** — Match actual product colors  

---

## ✅ Always Do This

✅ **Copy GOLDEN-TEMPLATE.html** — Never start blank  
✅ **Replace all {{PLACEHOLDERS}}** — Don't leave template text  
✅ **Use tabular-nums** — For all numbers (aligns decimals)  
✅ **Use uppercase labels** — `z-label` class for all headers  
✅ **Round corners 12-16px** — `rounded-xl` on all cards  
✅ **Generous padding** — `p-6` minimum, `p-8` preferred  
✅ **Test navigation** — Arrow keys should work  
✅ **Dark header band on content slides** — `bg-[#002A3A]` strip at top, rest is white  
✅ **Cover + closing slides = dark** — `bg-[#1A1A1A]` for highlight pages only  

---

## 📁 Workflow

1. **Read data** from Argus handoff JSON or user request
2. **Copy** `GOLDEN-TEMPLATE.html` to `outbox/[deck-name].html`
3. **Replace** all `{{PLACEHOLDERS}}` with real data
4. **Adjust** slide count (add/remove slides as needed)
5. **Test** in browser — check all 5 slides
6. **Deploy** to Vercel
7. **Report** URL to Iris

---

## 🆘 Fallback Plan

If golden template produces bad output → **Use old design style:**

Reference: https://zuma-bm-jatim.vercel.app/

That design has:
- Dark teal cards (#0A3D50)
- White section headers
- Clean data tables
- Simple, proven layout

Don't reinvent. Copy what works.

---

## 📝 Example: Ladies Merci Data Mapping

**Given data:**
- Total: 1,784 pairs, Rp 314.1M revenue
- Mocca: 627 (35.15%), #1
- Wine: 402 (22.53%), #2
- Black: 322 (18.05%), #3

**Mapped to template:**

Slide 1 (Cover — DARK):
- Title: "Ladies Merci Sales Performance"
- Subtitle: "Analysis by color variant — February 2026"

Slide 2 (Metrics — LIGHT):
- Card 1: "Total Volume" / "1,784" / "pairs" / "Retail Only"
- Card 2: "Gross Revenue" / "Rp 314.1" / "M" / "+15% vs Jan"

Slide 3 (Chart — LIGHT):
- ITEM_1: Mocca / 627 / 35.15% / #8B6F47
- ITEM_2: Wine / 402 / 22.53% / #722F37
- ITEM_3: Black / 322 / 18.05% / #1A1A1A

Slide 5 (Insights — DARK):
- "Earth tones dominate consumer preference"
- "Wine shows strong demand for bold alternatives"
- "Restock Mocca + Wine first"

---

## 🎓 Key Takeaway

**You're not a designer. You're a data mapper.**

The template is already beautiful. Your job is to put the right data in the right boxes. When in doubt, look at the template. When still in doubt, look at https://zuma-bm-jatim.vercel.app/ for fallback style.

**Rule of thumb:** Cover = dark. Content = light. Closing = dark. Everything else follows from there.

Golden template = reliable, repeatable, pixel-perfect output.
