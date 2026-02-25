# eos-visual-skill — Zuma McKinsey PPT System

**Who uses this:** Eos (Visual/PPT Nanobot, Gemini 3.1 Pro)
**Purpose:** End-to-end system for generating McKinsey-quality consulting decks in Zuma Mixed Executive Report aesthetic. This file is the single source of truth — narrative logic, deck structure, slide types, framework templates, visual components, and design system.

**Audience:** Zuma management & directors — busy, decision-focused. Every slide must earn its place.
**Primary deck types:** Sales Analysis · Stock Analysis · Combined (Sales + Stock)

---

## DESIGN SYSTEM (v4.0 — 2026-02-25 — Mixed Executive Report)
#TX|
#SK|**This is the canonical design standard. All HTML patterns in §3, §4, §5, §6 use this palette. No overrides.**
#BY|
#ZV|**MANDATORY LANGUAGE RULE: ALL OUTPUT MUST BE IN BAHASA INDONESIA. Label, heading, narasi, insight, judul slide, konten — semuanya dalam BI. TIDAK ADA PENGECUALIAN.**
#VP|
### Color Tokens (bm-jatim palette — MANDATORY — DUAL MODE)
#KS|
```css
/* ═══════════════════════════════════════════════════════════
   LIGHT MODE — DEFAULT for content slides
   (Exec Summary, KPI, Chart, Table, Framework, Recommendation)
   ═══════════════════════════════════════════════════════════ */
:root {
  --page-bg:        #FFFFFF;              /* content slide background */
  --page-bg-alt:    #F8FAFC;              /* alternating section bg */
  --header-band:    #002A3A;              /* dark strip at top of content slides */
  --card-light:     #FFFFFF;              /* cards on light bg */
  --card-border:    rgba(0,42,58,0.08);   /* subtle border on white cards */
  --text-primary:   #1A202C;              /* headlines, body on light bg */
  --text-secondary: #4A5568;              /* labels, supporting text */
  --text-muted:     #718096;              /* captions, timestamps */
  --border-light:   rgba(0,42,58,0.06);   /* card/table borders on light */

  /* ═══════════════════════════════════════════════════════════
     DARK MODE — HIGHLIGHT for Cover, Section Divider, closing slides
     ═══════════════════════════════════════════════════════════ */
  --dark-base:      #1A1A1A;              /* dark highlight slide bg */
  --dark-card:      #002A3A;              /* cards on dark bg */
  --dark-card-alt:  #0A3D50;              /* secondary cards on dark bg */
  --dark-text:      #FFFFFF;              /* headlines on dark bg */
  --dark-secondary: #8CA3AD;              /* labels on dark bg */
  --dark-muted:     #5A7A87;              /* captions on dark bg */
  --dark-border:    rgba(255,255,255,0.08); /* card borders on dark */

  /* ═══════════════════════════════════════════════════════════
     SHARED — same across both modes
     ═══════════════════════════════════════════════════════════ */
  --accent:         #00E273;              /* Zuma Green — CTAs, indicators, positive */
  --neg:            #FF4D4D;              /* red — declines, at-risk */
  --warn:           #FFB800;              /* amber — caution, moderate alerts */
  --so-what-bg-light: rgba(0,226,115,0.06); /* So What box on light slides */
  --so-what-bg-dark:  rgba(0,226,115,0.08); /* So What box on dark slides */
}
```

**Slide mode assignment (MANDATORY):**

| Slide Type | Mode | Background |
|------------|------|------------|
| TYPE 1 — Cover | **DARK** | `#1A1A1A` |
| TYPE 2 — Exec Summary | **LIGHT** | `#FFFFFF` |
| TYPE 3 — KPI Overview | **LIGHT** | `#FFFFFF` |
| TYPE 4 — Data Analysis | **LIGHT** | `#FFFFFF` |
| TYPE 5 — Framework | **LIGHT** | `#FFFFFF` |
| TYPE 6 — Recommendation | **LIGHT** | `#FFFFFF` |
| TYPE 7 — Next Steps | **DARK** | `#1A1A1A` |
| TYPE 8 — Section Divider | **DARK** | `#1A1A1A` |
### So What Box — Dual Mode (OVERRIDE §1.4)

```html
<div class="so-what">
  <div class="so-what-label">→ Apa Maknanya</div>
  <div class="so-what-text">Implikasi actionable untuk manajemen — 1-2 kalimat.</div>
</div>
```
```css
/* On LIGHT slides (default — content slides) */
.so-what { background: rgba(0,226,115,0.06); border-left: 4px solid #00E273; padding: 18px 24px; margin-top: auto; border-radius: 0 8px 8px 0; }
.so-what-label { font-size: 10px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: #00E273; margin-bottom: 6px; }
.so-what-text { font-size: 16px; color: #1A202C; line-height: 1.6; }

/* On DARK slides (highlight slides — if So What box needed) */
.so-what.dark { background: rgba(0,226,115,0.08); }
.so-what.dark .so-what-text { color: rgba(255,255,255,0.85); }
#WH|
#KM|### Bahasa Indonesia Label Glossary
#QH|
#SQ|| English | Bahasa Indonesia |
#TQ||---|---|
#JP|| Sales Analysis | Analisis Penjualan |
#MH|| Executive Summary | Ringkasan Eksekutif |
#RK|| Performance Overview | Ikhtisar Performa |
#TB|| Store Performance | Performa Toko |
#BT|| SKU Analysis | Analisis SKU |
#KV|| Store Portfolio Analysis | Analisis Portofolio Toko |
#JP|| Recommended Actions | Rekomendasi Tindakan |
#QJ|| Next Steps | Langkah Selanjutnya |
#HZ|| Situation | Situasi |
#PR|| Complication | Komplikasi |
#NN|| Resolution | Resolusi |
#JH|| So What / → So What | → Apa Maknanya |
#RQ|| Total Revenue | Total Pendapatan |
#QV|| Units Sold | Unit Terjual |
#WB|| Active Stores | Toko Aktif |
#PN|| On Track | Sesuai Target |
#VQ|| At Risk | Perlu Perhatian |
#KP|| Below | Di Bawah Target |
#SS|| Pending | Menunggu |
#TJ|| Planned | Direncanakan |
#VM|| Stars | Bintang |
#XK|| Cash Cows | Sapi Perah |
#VS|| Question Marks | Tanda Tanya |
#MQ|| Dogs | Tersendat |
#NS|| Prepared by | Disiapkan oleh |
#BR|| Space to navigate · P to print | Spasi untuk navigasi · P untuk cetak |
#VS|
#ZM|### Golden Reference
#QT|
#JT|- **Live URL:** `https://bm-jatim.vercel.app` — validated, QA'd, production deck
#WZ|- **Source HTML:** `~/.openclaw/workspace-eos-nanobot/outbox/bm-jatim-GOLDEN-REFERENCE.html` — copy this as base template
#NT|- **This IS the design standard.** When in doubt, open golden reference and match exactly.
#MS|
---

---

## HOW TO USE THIS SKILL

1. **Receive task** → identify deck type (Sales / Stock / Combined)
2. **Load the correct arc** from §2 — that is your slide sequence. Do not deviate.
3. **Read the data** — identify the key assertion for each slide
4. **Apply narrative rules** from §1 to title every slide
5. **Build each slide** using the type specs from §3 + component library from §5
6. **Insert framework slide** in its fixed position (per arc)
7. **Run quality checklist** from §8 before outputting

---

## §1 NARRATIVE ENGINE — THE MCKINSEY CORE

> This is the most important section. Visual design is secondary to narrative structure. A beautifully designed slide with a weak title is worthless. A plainly designed slide with a sharp assertion title is powerful.

### §1.1 The Minto Rule (Mandatory on Every Slide)

Every slide has **three distinct cognitive layers**. Each layer does a different job:

```
TITLE    = The CLAIM     "What this slide proves" — complete sentence, directional, specific
BODY     = The EVIDENCE  "Data, chart, or table that proves the claim"
SO WHAT  = The IMPLICATION  "What management should do or think because of this"
```

**Reading all titles in sequence = a complete standalone argument.**
Management should understand the deck's message by reading titles alone, without looking at any chart.

### §1.2 SCR Story Logic (Deck-Level Structure)

Every deck follows the Situation → Complication → Resolution arc:

| Layer | What it covers | Share of deck |
|---|---|---|
| **Situation** | Current state, context. No judgment. | 10-15% (1-2 slides) |
| **Complication** | What's wrong, what changed, the burning platform | 15-20% (1-2 slides) |
| **Resolution** | What to do about it — your recommendation | 60-70% (rest of deck) |

**Exec Summary = SCR compressed into 1 slide.** It must appear as slide 2, always.

### §1.3 Action Title Standards

**The most common failure in PPT design is topic titles. Ban them.**

| ❌ BANNED — Topic Title | ✅ REQUIRED — Action Title (Assertion) |
|---|---|
| Sales Performance | Jatim revenue declined 18% YoY, driven by 3 underperforming Ruko stores |
| Branch Overview | Only 2 of 6 branches hit Q1 target — both are mall-format units |
| Stock Analysis | 4 SKUs face stockout within 14 days across Surabaya stores |
| Market Position | Ladies segment growing 2× faster than Men's, but Zuma captures only 18% |
| Recommendations | Redistributing 2 SPGs from Ruko to Galaxy Mall recovers ~Rp 45M/month |

**Rules — all must pass:**
- [ ] Complete sentence with a verb (not a noun phrase)
- [ ] ≤15 words, ≤2 lines
- [ ] Directional — states what happened AND why/where
- [ ] Passes "so what?" test — a reader says "that matters"
- [ ] Reading all titles sequentially tells the full story

### §1.4 So What Box — Spec and Rules

**Position:** Bottom of slide, always. Full-width, inside main slide padding.
**Design:** Card with 4px `#00E273` left border, `bg-[rgba(0,226,115,0.08)]` background, `rounded-r-lg`, `p-4`.
**Content:** 1-2 sentences MAX. Starts with `→`. Must be an actionable implication for management.

```html
<!-- SO WHAT BOX on LIGHT slides (content slides — default) -->
<div class="border-l-4 border-[#00E273] bg-[rgba(0,226,115,0.06)] rounded-r-lg p-4 mt-auto">
  <p class="text-xs font-medium uppercase tracking-widest text-[#00E273] mb-1">→ So What</p>
  <p class="text-[#1A202C] text-sm leading-relaxed">[Implikasi actionable untuk manajemen — 1-2 kalimat]</p>
</div>

<!-- SO WHAT BOX on DARK slides (if needed on a dark slide) -->
<div class="border-l-4 border-[#00E273] bg-[rgba(0,226,115,0.08)] rounded-r-lg p-4 mt-auto">
  <p class="text-xs font-medium uppercase tracking-widest text-[#00E273] mb-1">→ So What</p>
  <p class="text-white text-sm leading-relaxed">[Implikasi actionable untuk manajemen — 1-2 kalimat]</p>
</div>
```

**Critical rules:**
- So What ≠ repeat of the title. Title = primary claim; box = secondary inference management must act on.
- Never introduce information not supported by the slide body.
- If you cannot write a distinct So What, the title is too weak — rewrite the title.
- Omit the box ONLY on: Cover, Exec Summary, Section Divider, Recommendation slide, Next Steps slide.

**Example of correct vs. wrong:**
```
Title:    "Jatim revenue declined 18% YoY, driven by 3 Ruko stores"
Body:     Bar chart showing store performance
❌ Wrong So What: "Revenue di Jatim turun 18%"   ← repeat of title
✅ Right So What: "→ Closing or converting the 3 underperforming Ruko stores to event format
                    recovers an estimated Rp 60M/quarter at zero incremental CAPEX."
```

### §1.5 Executive Summary — Standards

**Slide 2, always. Non-negotiable.**

Structure:
- **Title:** "Executive Summary" OR a single master assertion if the whole deck = one argument
- **Body:** 3-5 bold bullets. Each bullet = a complete sentence. Each is an assertion, not a topic.
- **Sequence:** First bullet = Situation. Middle bullets = Complication. Last bullet = Resolution/main recommendation.
- **Rule:** Reading these 3-5 bullets should give management 80% of the deck's value.
- **No So What box** — the exec summary IS the so what.

```html
<!-- EXEC SUMMARY BODY PATTERN -->
<div class="space-y-4 flex-1">
  <!-- Situation bullet (1) -->
  <div class="flex gap-4 items-start">
    <span class="w-2 h-2 rounded-full bg-[#8CA3AD] mt-2 shrink-0"></span>
    <p class="text-[#8CA3AD] text-base leading-relaxed">[Situation — current state, no judgment]</p>
  </div>
  <!-- Complication bullets (1-2) -->
  <div class="flex gap-4 items-start">
    <span class="w-2 h-2 rounded-full bg-[#FFB800] mt-2 shrink-0"></span>
    <p class="text-white text-base leading-relaxed font-medium">[Complication — what's wrong]</p>
  </div>
  <!-- Resolution bullet (1-2) — bold/green, management reads these first -->
  <div class="flex gap-4 items-start">
    <span class="w-2 h-2 rounded-full bg-[#00E273] mt-2 shrink-0"></span>
    <p class="text-white text-base leading-relaxed font-semibold">[Resolution — what to do, expected impact]</p>
  </div>
</div>
```

---

## §2 DECK ARC TEMPLATES

> **These are fixed sequences. Do not add, remove, or reorder slides unless Wayan explicitly requests it. Consistency = predictability = management trust.**

### §2.1 Sales Analysis Arc (8 slides)

```
Slide 1   COVER              Deck title, date, prepared by
Slide 2   EXEC SUMMARY       3-5 bullets: SCR compressed (always)
Slide 3   REVENUE OVERVIEW   KPI cards: Total Revenue · Units Sold · Avg Selling Price · Active Stores
Slide 4   BRANCH BREAKDOWN   Traffic light table: all branches vs target + growth
Slide 5   SKU ANALYSIS       Ranking bar: top movers + bottom draggers. Assertion: which SKUs win/lose
Slide 6   ★ FRAMEWORK        Store Portfolio 2×2 (growth rate × revenue volume)
Slide 7   RECOMMENDATIONS    3-5 numbered actions with expected impact
Slide 8   NEXT STEPS         Action / Owner / Due Date table
```

### §2.2 Stock Analysis Arc (7 slides)

```
Slide 1   COVER              Deck title, date, prepared by
Slide 2   EXEC SUMMARY       3-5 bullets: stock health snapshot
Slide 3   STOCK HEALTH       KPI cards: Days of Supply · Coverage % · Stockout-risk stores · Surplus value
Slide 4   STOCKOUT RISK      Heat table: which SKUs/stores are critical (color = urgency)
Slide 5   SURPLUS            Ranked table: slow-moving SKUs by value, days on hand
Slide 6   ★ FRAMEWORK        Stock-Sales 2×2 (stock health × sales vs target per store)
Slide 7   RO RECOMMENDATION  Table: SKU · Qty to order · Priority · Estimated arrival. + Next Steps merged.
```

### §2.3 Combined Sales + Stock Arc (10 slides)

```
Slide 1   COVER              Deck title, date, prepared by
Slide 2   EXEC SUMMARY       3-5 bullets: integrated picture (both sales + stock)
Slide 3   REVENUE OVERVIEW   KPI cards: Total Revenue · Units Sold · ASP · Revenue vs Target
Slide 4   BRANCH SALES       Traffic light table: all branches vs sales target
Slide 5   ★ FRAMEWORK A      Revenue Waterfall (bridge: why revenue moved vs last period)
Slide 6   SKU DEEP DIVE      Combined: SKU performance (sales) + stock position side by side
Slide 7   STOCK-SALES LINK   Where stockouts are actively killing sales (heat map or paired chart)
Slide 8   ★ FRAMEWORK B      Stock-Sales 2×2 (integrated view)
Slide 9   RECOMMENDATIONS    Integrated actions across both sales and stock
Slide 10  NEXT STEPS         Action / Owner / Due Date table
```

### §2.4 Arc Selection Rule

```
User asks for "sales", "revenue", "performance"     → Sales Analysis Arc (8 slides)
User asks for "stock", "inventory", "RO", "surplus" → Stock Analysis Arc (7 slides)
User asks for "both" OR provides both data sets      → Combined Arc (10 slides)
When in doubt → ask before generating
```

---

## §3 SLIDE TYPE LIBRARY

Eight slide types. Every slide in every deck is one of these. Use the matching HTML pattern.

### TYPE 1 — COVER
**Mode: DARK (highlight page)**

**Rules:** No So What box. Minimal text. Date and preparer always present.

```html
#KZ|<div class="slide min-h-screen bg-[#1A1A1A] flex flex-col justify-center px-16 py-12">
  <div class="border-l-4 border-[#00E273] pl-6 mb-10">
    <p class="text-[#00E273] text-xs font-medium uppercase tracking-widest mb-3">Zuma Indonesia · [Deck Type Label]</p>
    <h1 class="text-white text-5xl font-bold leading-tight tracking-tight">[DECK TITLE — Assertion or Topic]</h1>
    <p class="text-[#8CA3AD] text-lg mt-3">[Subtitle: period, scope, or one-line context]</p>
  </div>
  <div class="ml-10 flex items-center gap-6">
    <div class="w-12 h-px bg-[#00E273]"></div>
    <p class="text-[#5A7A87] text-xs uppercase tracking-widest">[Month Year] · Prepared by Iris · Zuma Indonesia</p>
  </div>
</div>
```

### TYPE 2 — EXEC SUMMARY
**Mode: LIGHT (content page)**

**Rules:** Always slide 2. 3-5 bullets. SCR sequence. No So What box.

```html
<!-- TYPE 2: EXEC SUMMARY — LIGHT MODE — bg white, dark header band at top -->
<div class="slide min-h-screen bg-white flex flex-col">
  <!-- Dark header band -->
  <div class="bg-[#002A3A] px-16 py-6">
    <p class="text-[#00E273] text-xs font-medium uppercase tracking-widest mb-1">Ringkasan Eksekutif</p>
    <h2 class="text-white text-3xl font-bold tracking-tight">[Master assertion ATAU \"Temuan Utama\"]</h2>
  </div>
  <!-- Light content area -->
  <div class="flex-1 flex flex-col px-16 py-10">
    <div class="space-y-5 flex-1">
      <!-- Situasi (titik abu) -->
      <div class="flex gap-4 items-start">
        <span class="w-2 h-2 rounded-full bg-[#4A5568] mt-2 shrink-0"></span>
        <p class="text-[#4A5568] text-base leading-relaxed">[Situasi — kondisi saat ini, tanpa penilaian]</p>
      </div>
      <!-- Komplikasi (titik amber, bold) -->
      <div class="flex gap-4 items-start">
        <span class="w-2 h-2 rounded-full bg-[#FFB800] mt-2 shrink-0"></span>
        <p class="text-[#1A202C] font-medium text-base leading-relaxed">[Komplikasi — temuan paling mendesak]</p>
      </div>
      <!-- Resolusi (titik hijau, semibold — pesan utama) -->
      <div class="flex gap-4 items-start">
        <span class="w-2 h-2 rounded-full bg-[#00E273] mt-2 shrink-0"></span>
        <p class="text-[#1A202C] font-semibold text-base leading-relaxed">[Resolusi — tindakan yang direkomendasikan + dampak yang diharapkan]</p>
      </div>
    </div>
    <div class="border-t border-[rgba(0,42,58,0.08)] pt-6 mt-6">
      <p class="text-[#718096] text-xs uppercase tracking-widest">Analisis lengkap pada slide berikutnya</p>
    </div>
  </div>
</div>
```

### TYPE 3 — KPI OVERVIEW
**Mode: LIGHT (content page)**

**Rules:** Assertion title. 2-4 KPI cards. Always has So What box.

```html
<!-- TYPE 3: KPI OVERVIEW — LIGHT MODE — bg white, dark header band, white cards -->
<div class="slide min-h-screen bg-white flex flex-col">
  <!-- Dark header band -->
  <div class="bg-[#002A3A] px-16 py-6">
    <p class="text-[#00E273] text-xs font-medium uppercase tracking-widest mb-1">[Section Label]</p>
    <h2 class="text-white text-3xl font-bold tracking-tight">[ASSERTION TITLE — kalimat lengkap]</h2>
  </div>
  <!-- Light content area -->
  <div class="flex-1 flex flex-col px-16 py-8">
    <div class="grid grid-cols-4 gap-6 flex-1">
      <!-- KPI Card — Positif -->
      <div class="bg-white border border-[rgba(0,42,58,0.08)] rounded-xl p-6 flex flex-col justify-between shadow-sm">
        <span class="text-xs font-medium uppercase tracking-widest text-[#4A5568]">[METRIC LABEL]</span>
        <div>
          <p class="text-4xl font-bold text-[#1A202C] tabular-nums mt-4">[VALUE]</p>
          <p class="text-sm mt-2 font-medium text-[#00E273]">↑ [DELTA] vs [PERIOD]</p>
          <p class="text-xs text-[#718096] mt-1">[Context — target atau benchmark]</p>
        </div>
      </div>
      <!-- KPI Card — Negatif -->
      <div class="bg-white border border-[rgba(0,42,58,0.08)] rounded-xl p-6 flex flex-col justify-between shadow-sm">
        <span class="text-xs font-medium uppercase tracking-widest text-[#4A5568]">[METRIC LABEL]</span>
        <div>
          <p class="text-4xl font-bold text-[#1A202C] tabular-nums mt-4">[VALUE]</p>
          <p class="text-sm mt-2 font-medium text-[#FF4D4D]">↓ [DELTA] vs [PERIOD]</p>
          <p class="text-xs text-[#718096] mt-1">[Context]</p>
        </div>
      </div>
      <!-- Tambah card sesuai kebutuhan (max 4) — sesuaikan grid-cols -->
    </div>
    <!-- SO WHAT BOX — light mode -->
    <div class="border-l-4 border-[#00E273] bg-[rgba(0,226,115,0.06)] rounded-r-lg p-4 mt-6">
      <p class="text-xs font-medium uppercase tracking-widest text-[#00E273] mb-1">→ So What</p>
      <p class="text-[#1A202C] text-sm leading-relaxed">[Implikasi sekunder — bukan pengulangan judul]</p>
    </div>
  </div>
</div>
```

### TYPE 4 — DATA ANALYSIS (Chart-based)
**Mode: LIGHT (content page)**

**Rules:** Assertion title. Chart fills 55-65% of body height. So What box at bottom.

```html
<!-- TYPE 4: DATA ANALYSIS — LIGHT MODE — bg white, dark header band, chart on light bg -->
<div class="slide min-h-screen bg-white flex flex-col">
  <!-- Dark header band -->
  <div class="bg-[#002A3A] px-16 py-6">
    <p class="text-[#00E273] text-xs font-medium uppercase tracking-widest mb-1">[Section Label]</p>
    <h2 class="text-white text-3xl font-bold tracking-tight">[ASSERTION TITLE — kalimat lengkap]</h2>
  </div>
  <!-- Light content area -->
  <div class="flex-1 flex flex-col px-16 py-8">
    <div class="bg-[#F8FAFC] border border-[rgba(0,42,58,0.06)] rounded-xl p-6 flex-1">
      <p class="text-xs font-medium uppercase tracking-widest text-[#4A5568] mb-4">[Chart subtitle]</p>
      <div class="relative" style="height: 320px;">
        <canvas id="[chartId]"></canvas>
      </div>
    </div>
    <!-- SO WHAT BOX — light mode -->
    <div class="border-l-4 border-[#00E273] bg-[rgba(0,226,115,0.06)] rounded-r-lg p-4 mt-4">
      <p class="text-xs font-medium uppercase tracking-widest text-[#00E273] mb-1">→ So What</p>
      <p class="text-[#1A202C] text-sm leading-relaxed">[Implikasi sekunder untuk tindakan manajemen]</p>
    </div>
  </div>
</div>
```

### TYPE 5 — FRAMEWORK (Conceptual — no standard chart)
**Mode: LIGHT (content page)**

**Rules:** Assertion title. Framework visualization is the body (see §4). So What box.

```html
<!-- TYPE 5: FRAMEWORK — LIGHT MODE — bg white, dark header band -->
<div class="slide min-h-screen bg-white flex flex-col">
  <!-- Dark header band -->
  <div class="bg-[#002A3A] px-16 py-6">
    <p class="text-[#00E273] text-xs font-medium uppercase tracking-widest mb-1">[Framework Name]</p>
    <h2 class="text-white text-3xl font-bold tracking-tight">[ASSERTION TITLE]</h2>
  </div>
  <!-- Light content area -->
  <div class="flex-1 flex flex-col px-16 py-8">
    <div class="flex-1 flex items-center justify-center">
      <!-- INSERT FRAMEWORK HTML FROM §4 HERE -->
    </div>
    <!-- SO WHAT BOX — light mode -->
    <div class="border-l-4 border-[#00E273] bg-[rgba(0,226,115,0.06)] rounded-r-lg p-4 mt-6">
      <p class="text-xs font-medium uppercase tracking-widest text-[#00E273] mb-1">→ So What</p>
      <p class="text-[#1A202C] text-sm leading-relaxed">[Apa yang diungkap framework — kuadran mana yang perlu ditindaklanjuti]</p>
    </div>
  </div>
</div>
```

### TYPE 6 — RECOMMENDATION
**Mode: LIGHT (content page)**

**Rules:** Assertion title stating the outcome. Numbered actions. No So What box.

```html
<!-- TYPE 6: RECOMMENDATION — LIGHT MODE — bg white, dark header band, white action cards -->
<div class="slide min-h-screen bg-white flex flex-col">
  <!-- Dark header band -->
  <div class="bg-[#002A3A] px-16 py-6">
    <p class="text-[#00E273] text-xs font-medium uppercase tracking-widest mb-1">Rekomendasi</p>
    <h2 class="text-white text-3xl font-bold tracking-tight">[ASSERTION TITLE — apa yang dicapai oleh tindakan ini]</h2>
  </div>
  <!-- Light content area -->
  <div class="flex-1 flex flex-col px-16 py-8">
    <div class="space-y-4 flex-1">
      <div class="bg-white border border-[rgba(0,42,58,0.08)] rounded-xl p-6 flex gap-6 items-start shadow-sm">
        <span class="text-[#00E273] text-2xl font-bold tabular-nums shrink-0 w-8">01</span>
        <div>
          <p class="text-[#1A202C] font-semibold text-base mb-1">[Tindakan — mulai dengan kata kerja: \"Redistribusi 2 SPG...\"]</p>
          <p class="text-[#4A5568] text-sm leading-relaxed">[Alasan + dampak yang diharapkan: \"Est. recovery: Rp 45M/bulan\"]</p>
        </div>
      </div>
      <div class="bg-white border border-[rgba(0,42,58,0.08)] rounded-xl p-6 flex gap-6 items-start shadow-sm">
        <span class="text-[#00E273] text-2xl font-bold tabular-nums shrink-0 w-8">02</span>
        <div>
          <p class="text-[#1A202C] font-semibold text-base mb-1">[Tindakan 2]</p>
          <p class="text-[#4A5568] text-sm leading-relaxed">[Dampak 2]</p>
        </div>
      </div>
      <!-- Hingga 5 tindakan total -->
    </div>
  </div>
</div>
```

### TYPE 7 — NEXT STEPS
**Mode: DARK (closing highlight page)**

**Rules:** Fixed table. Action / Owner / Due Date / Status. Always last slide. No So What box.

```html
#VN|<div class="slide min-h-screen bg-[#1A1A1A] flex flex-col px-16 py-12">
  <p class="text-[#00E273] text-xs font-medium uppercase tracking-widest mb-2">Action Plan</p>
  <h2 class="text-white text-3xl font-bold tracking-tight mb-8">Next Steps</h2>
  <div class="overflow-hidden rounded-xl border border-white/[0.08] flex-1">
    <table class="w-full text-sm">
      #PQ|      <thead class="bg-[#002A3A]">
        <tr>
          <th class="px-6 py-4 text-left text-xs font-medium uppercase tracking-widest text-[#8CA3AD]">Action</th>
          <th class="px-6 py-4 text-left text-xs font-medium uppercase tracking-widest text-[#8CA3AD]">Owner</th>
          <th class="px-6 py-4 text-left text-xs font-medium uppercase tracking-widest text-[#8CA3AD]">Due Date</th>
          <th class="px-6 py-4 text-left text-xs font-medium uppercase tracking-widest text-[#8CA3AD]">Status</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-white/[0.05]">
        <tr>
          <td class="px-6 py-4 text-white">[Action]</td>
          <td class="px-6 py-4 text-[#8CA3AD]">[Owner]</td>
          <td class="px-6 py-4 text-[#8CA3AD] tabular-nums">[DD MMM YYYY]</td>
          <td class="px-6 py-4">
            #MR|            <!-- Status: #00E273=Done · #FFB800=Pending · #FF4D4D=Overdue · #8CA3AD=Planned -->
            <span class="inline-flex items-center gap-2 text-[#FFB800] text-xs font-medium">
              <span class="w-2 h-2 rounded-full bg-[#FFB800]"></span>Pending
            </span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
  <div class="border-t border-white/[0.05] pt-6 mt-6">
    <p class="text-[#5A7A87] text-xs uppercase tracking-widest">Review: [Date] · Prepared by Iris · Zuma Indonesia</p>
  </div>
</div>
```

### TYPE 8 — SECTION DIVIDER
**Mode: DARK (highlight page)**

**Rules:** Full screen centered. Use only in decks >12 slides. No So What box.

```html
#QW|<div class="slide min-h-screen bg-[#1A1A1A] flex items-center justify-center">
  <div class="text-center">
    <span class="text-[#00E273] text-xs font-medium uppercase tracking-widest block mb-4">Section [N]</span>
    <h2 class="text-white text-6xl font-bold tracking-tight">[Section Name]</h2>
    <p class="text-[#8CA3AD] text-lg mt-4 max-w-lg mx-auto">[One-line context — optional]</p>
  </div>
</div>
```

---

## §4 FRAMEWORK TEMPLATE LIBRARY

> Framework slides appear in fixed positions per arc (§2). Pure HTML/CSS — no Chart.js unless noted.

### §4.1 Store Portfolio 2×2 Matrix

**Used in:** Sales Analysis slide 6
**Reveals:** Which stores to invest in (Stars), protect (Cash Cows), develop (Question Marks), exit (Dogs)
**Axes:** X = Revenue Growth Rate · Y = Revenue Volume

```html
<div class="w-full max-w-3xl relative" style="aspect-ratio: 1.2;">
  <div class="absolute inset-0 grid grid-cols-2 grid-rows-2 rounded-xl overflow-hidden border border-white/[0.08]">
    <!-- Top-left: Question Marks -->
    #MV|    <div class="bg-[#002A3A] border-r border-b border-white/[0.08] flex flex-col items-center justify-center p-6">
      <p class="text-[#FFB800] text-xs font-bold uppercase tracking-widest">Question Marks</p>
      <p class="text-[#FFB800] text-3xl font-bold mt-2">?</p>
      <p class="text-[#8CA3AD] text-[10px] text-center mt-2">High growth, low volume<br>Invest selectively</p>
    </div>
    <!-- Top-right: Stars -->
    <div class="bg-[#0d4a1f]/40 border-b border-white/[0.08] flex flex-col items-center justify-center p-6">
      <p class="text-[#00E273] text-xs font-bold uppercase tracking-widest">Stars</p>
      <p class="text-[#00E273] text-3xl font-bold mt-2">★</p>
      <p class="text-[#8CA3AD] text-[10px] text-center mt-2">High growth, high volume<br>Invest aggressively</p>
    </div>
    <!-- Bottom-left: Dogs -->
    #YY|    <div class="bg-[#002A3A]/50 border-r border-white/[0.08] flex flex-col items-center justify-center p-6">
      <p class="text-[#5A7A87] text-xs font-bold uppercase tracking-widest">Dogs</p>
      <p class="text-[#5A7A87] text-3xl font-bold mt-2">▼</p>
      <p class="text-[#5A7A87] text-[10px] text-center mt-2">Low growth, low volume<br>Exit or convert format</p>
    </div>
    <!-- Bottom-right: Cash Cows -->
    #BY|    <div class="bg-[#0A3D50] flex flex-col items-center justify-center p-6">
      <p class="text-[#00B8D4] text-xs font-bold uppercase tracking-widest">Cash Cows</p>
      <p class="text-[#00B8D4] text-3xl font-bold mt-2">◆</p>
      <p class="text-[#8CA3AD] text-[10px] text-center mt-2">Low growth, high volume<br>Protect and optimize</p>
    </div>
  </div>
  <!-- Data point circles: position using inline style left/top percentages based on actual store data -->
  <!-- X% = normalize growth rate to 0-100%, Y% = invert revenue to 0-100% (high revenue = small top%) -->
  <!-- Example: Star store at 70% right, 20% down from top -->
  <div class="absolute rounded-full bg-[#00E273] border-2 border-white flex items-center justify-center text-[#002A3A] text-[10px] font-bold"
       style="width:44px;height:44px;left:68%;top:15%;transform:translate(-50%,-50%)">Jatim</div>
  <!-- Axis labels -->
  <p class="absolute text-[#5A7A87] text-[10px] uppercase tracking-widest" style="bottom:-24px;left:0">← Low Growth</p>
  <p class="absolute text-[#5A7A87] text-[10px] uppercase tracking-widest" style="bottom:-24px;right:0">High Growth →</p>
  <p class="absolute text-[#8CA3AD] text-[10px] uppercase tracking-widest" style="left:-80px;top:50%;transform:translateY(-50%) rotate(-90deg)">Revenue Volume ↑</p>
</div>
```

### §4.2 Stock-Sales 2×2 Matrix

**Used in:** Stock Analysis slide 6, Combined slide 8
**Reveals:** Urgent RO needs (understocked + overperforming) vs. surplus pull (overstocked + underperforming)
**Axes:** X = Sales vs Target · Y = Stock Health (Days of Supply)

```html
<div class="w-full max-w-3xl relative" style="aspect-ratio: 1.2;">
  <div class="absolute inset-0 grid grid-cols-2 grid-rows-2 rounded-xl overflow-hidden border border-white/[0.08]">
    <!-- Top-left: At-risk + below target = Double Problem -->
    <div class="bg-[#3d1010]/30 border-r border-b border-white/[0.08] flex flex-col items-center justify-center p-4">
      #TQ|      <p class="text-[#FF4D4D] text-xs font-bold uppercase tracking-widest">Double Problem</p>
      #RJ|      <p class="text-[#FF4D4D]/70 text-[10px] text-center mt-1">Deprioritize restock<br>Fix sales first</p>
    </div>
    <!-- Top-right: At-risk + above target = URGENT RO -->
    <div class="bg-[#3d2500]/40 border-b border-white/[0.08] flex flex-col items-center justify-center p-4">
      <p class="text-[#FFB800] text-xs font-bold uppercase tracking-widest">⚡ Urgent RO</p>
      <p class="text-[#FFB800]/70 text-[10px] text-center mt-1">Order immediately<br>Losing sales now</p>
    </div>
    <!-- Bottom-left: Adequate + below target = Surplus Risk -->
    #PV|    <div class="bg-[#002A3A]/60 border-r border-white/[0.08] flex flex-col items-center justify-center p-4">
      <p class="text-[#8CA3AD] text-xs font-bold uppercase tracking-widest">Surplus Risk</p>
      <p class="text-[#8CA3AD]/70 text-[10px] text-center mt-1">Pull stock<br>Investigate demand</p>
    </div>
    <!-- Bottom-right: Adequate + above target = Healthy -->
    <div class="bg-[#0d4a1f]/25 flex flex-col items-center justify-center p-4">
      <p class="text-[#00E273] text-xs font-bold uppercase tracking-widest">✓ Healthy</p>
      <p class="text-[#00E273]/70 text-[10px] text-center mt-1">Maintain<br>Standard reorder</p>
    </div>
  </div>
  <!-- Data point circles positioned by actual store values -->
  <p class="absolute text-[#5A7A87] text-[10px] uppercase tracking-widest" style="bottom:-24px;left:0">← Below Target</p>
  <p class="absolute text-[#5A7A87] text-[10px] uppercase tracking-widest" style="bottom:-24px;right:0">Above Target →</p>
  <p class="absolute text-[#8CA3AD] text-[10px] uppercase tracking-widest" style="left:-80px;top:50%;transform:translateY(-50%) rotate(-90deg)">Stock Health ↑</p>
</div>
```

### §4.3 Revenue Waterfall Chart

**Used in:** Combined slide 5
**Reveals:** Why revenue moved vs. last period — decomposed into specific drivers

```javascript
// Waterfall via Chart.js floating bars: data = [barStart, barEnd]
const ctx = document.getElementById('waterfallChart');
const waterfallLabels = ['Last Period', 'Store Growth', 'New Stores', 'Mix Effect', 'Price Effect', 'This Period'];
const waterfallValues = [
  [0, 4200],     // Last Period — full bar
  [4200, 4650],  // Store Growth +450 — green (up)
  [4650, 4800],  // New Stores +150 — green (up)
  [4650, 4800],  // replace with real: [4800, 4640] = -160 Mix Effect — red (down)
  [4640, 4750],  // Price Effect +110 — green (up)
  [0, 4750],     // This Period — full bar
];
new Chart(ctx, {
  type: 'bar',
  data: {
    labels: waterfallLabels,
    datasets: [{
      data: waterfallValues,
      backgroundColor: (ctx) => {
        const i = ctx.dataIndex, last = waterfallLabels.length - 1;
        if (i === 0 || i === last) return '#00B8D4';
        const d = ctx.chart.data.datasets[0].data[i];
        #JY|        return d[1] > d[0] ? '#00E273' : '#FF4D4D';
      },
      borderRadius: 4, borderSkipped: false,
    }]
  },
  options: {
    responsive: true,
    plugins: {
      legend: { display: false },
      tooltip: { callbacks: { label: (ctx) => {
        const d = ctx.raw, delta = d[1] - d[0];
        return (delta >= 0 ? '+' : '') + 'Rp ' + Math.abs(delta).toLocaleString('id-ID');
      }}}
    },
    scales: {
      y: { ticks: { callback: v => 'Rp ' + (v/1000).toFixed(0) + 'M' }, grid: { color: 'rgba(255,255,255,0.05)' } },
      x: { grid: { display: false } }
    }
  }
});
```

### §4.4 Revenue Driver Tree

**Used in:** Optional — add when root cause analysis needed on any deck type

```html
<div class="w-full flex flex-col items-center">
  <!-- Root node -->
  <div class="bg-[#00E273]/10 border border-[#00E273]/40 rounded-xl px-8 py-4 text-center">
    <p class="text-[#00E273] text-xs font-medium uppercase tracking-widest">Total Revenue</p>
    <p class="text-white text-2xl font-bold tabular-nums">[VALUE]</p>
    <p class="text-[#00E273] text-sm font-medium">[DELTA] YoY</p>
  </div>
  <div class="w-px h-6 bg-white/[0.15]"></div>
  <!-- Level 2 -->
  <div class="flex gap-20">
    <!-- Volume branch -->
    <div class="flex flex-col items-center">
      #VH|      <div class="bg-[#002A3A] border border-white/[0.08] rounded-xl px-6 py-3 text-center">
        <p class="text-[#8CA3AD] text-xs uppercase tracking-widest">Volume</p>
        <p class="text-white text-xl font-bold tabular-nums">[VALUE] pcs</p>
        <p class="text-[#00E273] text-sm">[DELTA]</p>
      </div>
      <div class="w-px h-5 bg-white/[0.15]"></div>
      <div class="flex gap-6">
        #XJ|        <div class="bg-[#002A3A] border border-white/[0.08] rounded-xl px-4 py-2 text-center">
          <p class="text-[#8CA3AD] text-[10px] uppercase tracking-widest">Active Stores</p>
          <p class="text-white text-base font-bold">[N]</p>
        </div>
        #XJ|        <div class="bg-[#002A3A] border border-white/[0.08] rounded-xl px-4 py-2 text-center">
          <p class="text-[#8CA3AD] text-[10px] uppercase tracking-widest">Units/Store</p>
          <p class="text-white text-base font-bold">[VALUE]</p>
        </div>
      </div>
    </div>
    <!-- ASP branch -->
    <div class="flex flex-col items-center">
      #VH|      <div class="bg-[#002A3A] border border-white/[0.08] rounded-xl px-6 py-3 text-center">
        <p class="text-[#8CA3AD] text-xs uppercase tracking-widest">ASP</p>
        <p class="text-white text-xl font-bold tabular-nums">Rp [VALUE]</p>
        <p class="text-[#00E273] text-sm">[DELTA]</p>
      </div>
      <div class="w-px h-5 bg-white/[0.15]"></div>
      <div class="flex gap-6">
        #XJ|        <div class="bg-[#002A3A] border border-white/[0.08] rounded-xl px-4 py-2 text-center">
          <p class="text-[#8CA3AD] text-[10px] uppercase tracking-widest">Product Mix</p>
          <p class="text-white text-base font-bold">[DELTA]</p>
        </div>
        #XJ|        <div class="bg-[#002A3A] border border-white/[0.08] rounded-xl px-4 py-2 text-center">
          <p class="text-[#8CA3AD] text-[10px] uppercase tracking-widest">Price Effect</p>
          <p class="text-white text-base font-bold">[DELTA]</p>
        </div>
      </div>
    </div>
  </div>
</div>
```

---

## §5 VISUAL COMPONENT LIBRARY

Six reusable components. Each has: HTML pattern + Imagen prompt for generating its reference image.

> **Generate reference images:** Task Iris to have Eos generate all 6 images and save to
> `~/.openclaw/workspace-eos-nanobot/design-refs/` — then embed those paths as visual ground truth.

### §5.1 KPI Card Set

**Reference image path:** `~/.openclaw/workspace-eos-nanobot/design-refs/ref-01-kpi-card.png`

**Imagen generation prompt:**
```
#HS|Dark analytics KPI card set on 1920x1080 slide. Background #1A1A1A near-black, zero white anywhere.
#WZ|Three side-by-side cards. Each card: background #002A3A dark teal, 1px rgba(255,255,255,0.08) border,
#ZY|12px rounded corners, 24px padding. Card 1 (REVENUE): gray uppercase label "REVENUE" top-left,
#QT|large "Rp 4.2M" white bold number center, green "\u2191 +12% vs last month" small text below.
#NB|Card 2 (UNITS SOLD): label "UNITS SOLD", number "12,400", red "\u2193 -5% vs last month".
#RS|Card 3 (STORES): label "ACTIVE STORES", number "24", gray "\u2014 unchanged".
#HR|No shadows, no gradients. Clean, minimal, professional analytics. 16:9 ratio.

*(HTML pattern in §3 TYPE 3 — grid of KPI cards)*

### §5.2 Traffic Light Table

**Reference image path:** `~/.openclaw/workspace-eos-nanobot/design-refs/ref-02-traffic-light.png`

**Imagen generation prompt:**
```
#XZ|Dark professional branch performance table on 1920x1080 slide. Background #1A1A1A near-black.
#SV|Table: rounded-xl corners, 1px white/8% border. Header: #002A3A background, gray uppercase columns
#HW|BRANCH | REVENUE | VS TARGET | GROWTH | STATUS. Six rows: Jatim, Jakarta, Sumatra, Sulawesi, Batam, Bali.
#VZ|Revenue column: white tabular numbers. VS Target: green "+X%" or red "-X%".
#BB|Status column: colored indicator \u2014 3 rows green circle dot + "On Track", 2 amber + "At Risk", 1 red + "Below".
#XT|Row dividers: faint white/5% lines. No shadows. Dark consulting presentation. 16:9.

**HTML pattern:**
```html
<div class="overflow-hidden rounded-xl border border-white/[0.08]">
  <table class="w-full text-sm">
    #PQ|    <thead class="bg-[#002A3A]">
      <tr>
        <th class="px-6 py-4 text-left text-xs font-medium uppercase tracking-widest text-[#8CA3AD]">Branch</th>
        <th class="px-6 py-4 text-right text-xs font-medium uppercase tracking-widest text-[#8CA3AD]">Revenue</th>
        <th class="px-6 py-4 text-right text-xs font-medium uppercase tracking-widest text-[#8CA3AD]">vs Target</th>
        <th class="px-6 py-4 text-right text-xs font-medium uppercase tracking-widest text-[#8CA3AD]">Growth</th>
        <th class="px-6 py-4 text-center text-xs font-medium uppercase tracking-widest text-[#8CA3AD]">Status</th>
      </tr>
    </thead>
    <tbody class="divide-y divide-white/[0.05]">
      <tr class="hover:bg-white/[0.02]">
        <td class="px-6 py-4 font-medium text-white">[Branch]</td>
        <td class="px-6 py-4 text-right tabular-nums text-white">Rp [X]M</td>
        #BT|        <td class="px-6 py-4 text-right font-medium text-[#00E273]">+[X]%</td>  <!-- or text-[#FF4D4D] for negative -->
        <td class="px-6 py-4 text-right font-medium text-[#00E273]">+[X]%</td>
        <td class="px-6 py-4 text-center">
          <!-- On Track: -->  <span class="inline-flex items-center gap-2 text-[#00E273] text-xs font-medium"><span class="w-2 h-2 rounded-full bg-[#00E273]"></span>On Track</span>
          <!-- At Risk:  -->  <!-- <span class="inline-flex items-center gap-2 text-[#FFB800] text-xs font-medium"><span class="w-2 h-2 rounded-full bg-[#FFB800]"></span>At Risk</span> -->
          #JH|          <!-- Below:    -->  <!-- <span class="inline-flex items-center gap-2 text-[#FF4D4D] text-xs font-medium"><span class="w-2 h-2 rounded-full bg-[#FF4D4D]"></span>Below</span> -->
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

### §5.3 Ranking Bar (Top/Bottom Movers)

**Reference image path:** `~/.openclaw/workspace-eos-nanobot/design-refs/ref-03-ranking-bar.png`

**Imagen generation prompt:**
```
#RK|Dark horizontal ranking bar chart for retail SKU performance on 1920x1080 slide. Background #1A1A1A near-black.
#HM|Chart container: #002A3A dark teal, rounded-xl, 24px padding. Eight horizontal bars ranked top to bottom.
#ZH|Top bar (highest performer): #00E273 green fill with white product name label on left and value on right.
#YX|All other bars: #0A3D50 dark muted fill. Product names left-aligned in white, values right-aligned in gray.
#MH|No y-axis lines. Clean minimal horizontal bars. Professional analytics, dark theme. 16:9.

*(Use Chart.js horizontal bar from §6 chart recipes — `indexAxis: 'y'`)*

### §5.4 Heat Table (Stockout Risk)

**Reference image path:** `~/.openclaw/workspace-eos-nanobot/design-refs/ref-04-heat-table.png`

**Imagen generation prompt:**
```
#KR|Dark heat map risk table for retail stock analysis on 1920x1080 slide. Background #1A1A1A near-black.
#MV|Table: rounded-xl border white/8%. Header: gray uppercase SKU | JATIM | JKT | SURABAYA | BATAM | STATUS.
#WH|Each branch cell shows days-of-stock as a colored pill badge:
#RW|Critical (<7 days): red background rgba(255,77,77,0.2), red text (e.g. "5d").
#XM|Warning (7-14 days): amber background rgba(255,184,0,0.2), amber text (e.g. "11d").
#MP|Safe (>14 days): green background rgba(0,226,115,0.1), green text (e.g. "28d").
#WS|Right STATUS column: full colored pill \u2014 "\u26a1 Critical" red or "\u2713 Safe" green.
#HS|Dark consulting analytics style. 16:9.

**HTML pattern:**
```html
<div class="overflow-hidden rounded-xl border border-white/[0.08]">
  <table class="w-full text-sm">
    #PQ|    <thead class="bg-[#002A3A]">
      <tr>
        <th class="px-6 py-4 text-left text-xs font-medium uppercase tracking-widest text-[#8CA3AD]">SKU</th>
        <th class="px-4 py-4 text-center text-xs font-medium uppercase tracking-widest text-[#8CA3AD]">Jatim</th>
        <th class="px-4 py-4 text-center text-xs font-medium uppercase tracking-widest text-[#8CA3AD]">Jakarta</th>
        <th class="px-4 py-4 text-center text-xs font-medium uppercase tracking-widest text-[#8CA3AD]">Surabaya</th>
        <th class="px-4 py-4 text-center text-xs font-medium uppercase tracking-widest text-[#8CA3AD]">Status</th>
      </tr>
    </thead>
    <tbody class="divide-y divide-white/[0.05]">
      <tr>
        <td class="px-6 py-4 font-medium text-white">[SKU Name]</td>
        #ZV|        <!-- Critical: -->  <td class="px-4 py-4 text-center"><span class="inline-block px-2 py-1 rounded-md bg-[#FF4D4D]/20 text-[#FF4D4D] text-xs font-medium tabular-nums">5d</span></td>
        <!-- Warning:  -->  <td class="px-4 py-4 text-center"><span class="inline-block px-2 py-1 rounded-md bg-[#FFB800]/20 text-[#FFB800] text-xs font-medium tabular-nums">11d</span></td>
        <!-- Safe:     -->  <td class="px-4 py-4 text-center"><span class="inline-block px-2 py-1 rounded-md bg-[#00E273]/10 text-[#00E273] text-xs font-medium tabular-nums">28d</span></td>
        #BB|        <td class="px-4 py-4 text-center"><span class="inline-block px-3 py-1 rounded-full bg-[#FF4D4D]/20 text-[#FF4D4D] text-xs font-bold">\u26a1 Critical</span></td>
      </tr>
    </tbody>
  </table>
</div>
```

### §5.5 So What Box

**Reference image path:** `~/.openclaw/workspace-eos-nanobot/design-refs/ref-05-so-what.png`

**Imagen generation prompt:**
```
#VZ|Bottom section of a dark consulting presentation slide on 1920x1080. Slide background #1A1A1A near-black.
#TY|At the bottom: a distinct callout insight box spanning full width (minus padding). Left edge: 4px solid
#TX|#00E273 green vertical bar. Box background: rgba(0,226,115,0.08) very subtle green tint. Right corners rounded.
#TM|Inside the box: small uppercase label "\u2192 SO WHAT" in #00E273 green, 10px. Below: 1-2 lines of white text
#ZT|stating a business implication (e.g. "Redistributing 2 SPGs from Ruko to Galaxy Mall recovers ~Rp 45M/month
#TS|with zero additional CAPEX."). Box height ~72px. Professional consulting slide callout. 16:9 ratio.

*(HTML pattern in §1.4)*

### §5.6 Next Steps Table

**Reference image path:** `~/.openclaw/workspace-eos-nanobot/design-refs/ref-06-next-steps.png`

**Imagen generation prompt:**
```
#KM|Dark professional action plan slide on 1920x1080. Background #1A1A1A near-black. Title "Next Steps" in white bold
#PM|30px at top-left. Below: full-width table, rounded-xl, 1px white/8% border. Four columns: ACTION (widest),
#YY|OWNER, DUE DATE, STATUS. Header: #002A3A background, gray uppercase labels. Five rows of actions:
#JT|white action descriptions, gray owner names, gray dates. Status pills: 2x amber dot "Pending",
#WN|1x teal dot "In Progress", 1x green dot "Done". Rows separated by white/5% lines.
#VJ|Footer small gray text: "Review: [Date] \u00b7 Prepared by Iris \u00b7 Zuma Indonesia". Dark consulting. 16:9.

*(HTML pattern in §3 TYPE 7)*

---

## §6 MIXED EXECUTIVE REPORT VISUAL SYSTEM

### §6.1 Color Tokens (Dual Mode)

```css
/* ══ LIGHT MODE — content slides (default) ══ */
--zuma-page-bg:        #FFFFFF;              /* content slide bg */
--zuma-page-bg-alt:    #F8FAFC;              /* alternating section bg */
--zuma-header-band:    #002A3A;              /* dark strip at top of content slides */
--zuma-card-light:     #FFFFFF;              /* cards on light bg */
--zuma-card-border:    rgba(0,42,58,0.08);   /* subtle border on white cards */
--zuma-text-primary:   #1A202C;              /* headlines, body on light bg */
--zuma-text-secondary: #4A5568;              /* labels, supporting text */
--zuma-text-muted:     #718096;              /* captions, timestamps */
--zuma-border-light:   rgba(0,42,58,0.06);   /* card/table borders on light */

/* ══ DARK MODE — highlight slides (Cover, Divider, Closing) ══ */
--zuma-dark-base:      #1A1A1A;              /* dark highlight slide bg */
--zuma-dark-card:      #002A3A;              /* cards on dark bg */
--zuma-dark-card-alt:  #0A3D50;              /* secondary cards on dark bg */
--zuma-dark-text:      #FFFFFF;              /* headlines on dark bg */
--zuma-dark-secondary: #8CA3AD;              /* labels on dark bg */
--zuma-dark-muted:     #5A7A87;              /* captions on dark bg */
--zuma-dark-border:    rgba(255,255,255,0.08); /* card borders on dark */

/* ══ SHARED — same across both modes ══ */
--zuma-accent:         #00E273;              /* Green — fills, indicators, positive. NEVER on body text */
--zuma-positive:       #00E273;
--zuma-negative:       #FF4D4D;
--zuma-warning:        #FFB800;
--zuma-neutral:        #8CA3AD;
--zuma-info:           #00B8D4;
```

### §6.2 Typography Scale (Dual Mode)

| Use | Light Mode (content slides) | Dark Mode (highlight slides) |
|-----|-----------------------------|-----------------------------|
| Cover deck title | — | `text-5xl font-bold tracking-tight text-white` |
| Slide assertion title | `text-3xl font-bold tracking-tight text-[#1A202C]` | `text-3xl font-bold tracking-tight text-white` |
| KPI hero number | `text-4xl font-bold tabular-nums text-[#1A202C]` | `text-4xl font-bold tabular-nums text-white` |
| Body text | `text-base font-normal text-[#4A5568] leading-relaxed` | `text-base font-normal text-[#8CA3AD] leading-relaxed` |
| Emphasis body | `text-base font-semibold text-[#1A202C] leading-relaxed` | `text-base font-semibold text-white leading-relaxed` |
| Section label | `text-xs font-medium uppercase tracking-widest text-[#00E273]` | `text-xs font-medium uppercase tracking-widest text-[#00E273]` |
| Column header / label | `text-xs font-medium uppercase tracking-widest text-[#4A5568]` | `text-xs font-medium uppercase tracking-widest text-[#8CA3AD]` |
| Caption / muted | `text-xs text-[#718096]` | `text-xs text-[#5A7A87]` |
| Delta positive | `text-sm font-medium text-[#00E273]` | `text-sm font-medium text-[#00E273]` |
| Delta negative | `text-sm font-medium text-[#FF4D4D]` | `text-sm font-medium text-[#FF4D4D]` |
| Delta warning | `text-sm font-medium text-[#FFB800]` | `text-sm font-medium text-[#FFB800]` |

### §6.3 Chart.js Dual-Mode Presets (MANDATORY — paste in every deck `<head>`)

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script>
  // PRESET A — LIGHT SLIDES (default, content slides)
  function applyChartLightPreset() {
    Chart.defaults.color = '#4A5568';
    Chart.defaults.borderColor = 'rgba(0,42,58,0.08)';
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.padding = 20;
    Chart.defaults.plugins.legend.labels.color = '#4A5568';
    Chart.defaults.plugins.tooltip.backgroundColor = '#1A202C';
    Chart.defaults.plugins.tooltip.titleColor = '#FFFFFF';
    Chart.defaults.plugins.tooltip.bodyColor = '#4A5568';
    Chart.defaults.plugins.tooltip.borderColor = 'rgba(0,42,58,0.12)';
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;
    Chart.defaults.plugins.tooltip.padding = 12;
    Chart.defaults.elements.arc.borderWidth = 0;
    Chart.defaults.elements.bar.borderRadius = 6;
    Chart.defaults.elements.bar.borderSkipped = false;
    Chart.defaults.elements.line.tension = 0.4;
    Chart.defaults.elements.point.radius = 4;
    Chart.defaults.elements.point.hoverRadius = 6;
  }
  // PRESET B — DARK SLIDES (highlight slides: Cover, Divider, Closing)
  function applyChartDarkPreset() {
    Chart.defaults.color = '#8CA3AD';
    Chart.defaults.borderColor = 'rgba(255,255,255,0.05)';
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.padding = 20;
    Chart.defaults.plugins.legend.labels.color = '#8CA3AD';
    Chart.defaults.plugins.tooltip.backgroundColor = '#002A3A';
    Chart.defaults.plugins.tooltip.titleColor = '#FFFFFF';
    Chart.defaults.plugins.tooltip.bodyColor = '#8CA3AD';
    Chart.defaults.plugins.tooltip.borderColor = 'rgba(255,255,255,0.08)';
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;
    Chart.defaults.plugins.tooltip.padding = 12;
    Chart.defaults.elements.arc.borderWidth = 0;
    Chart.defaults.elements.bar.borderRadius = 6;
    Chart.defaults.elements.bar.borderSkipped = false;
    Chart.defaults.elements.line.tension = 0.4;
    Chart.defaults.elements.point.radius = 4;
    Chart.defaults.elements.point.hoverRadius = 6;
  }
  applyChartLightPreset(); // default — override per chart if on dark slide
</script>
```

### §6.4 Chart Color Palette

```javascript
const ZUMA_CHART_COLORS = [
  #VB|  '#00E273', '#00B8D4', '#FF4D4D', '#FFB800',
  '#8CA3AD', '#5A7A87', '#A78BFA', '#F472B6',
];
// Fashion product colors: Mocca #8B6F47 · Wine #722F37 · Black #1A1A1A · Navy #1B2A4A
```

### §6.5 Chart Recipes

**Line (trend):**
```javascript
new Chart(document.getElementById('lineChart'), {
  type: 'line',
  data: { labels: ['Jan','Feb','Mar','Apr','Mei','Jun'],
    datasets: [
      { label: 'This Period', data: [1200,1350,1100,1500,1800,1650],
        borderColor:'#00E273', backgroundColor:'rgba(0,226,115,0.08)', borderWidth:2.5, fill:true },
      { label: 'Last Period', data: [1000,1100,950,1200,1400,1300],
        borderColor:'#8CA3AD', borderWidth:2, borderDash:[5,4], fill:false }
    ]},
  options: { responsive:true,
    plugins: { legend:{position:'bottom'}, tooltip:{mode:'index',intersect:false} },
    scales: { y:{ grid:{color:'rgba(255,255,255,0.05)'}, ticks:{callback:v=>'Rp '+(v/1000).toFixed(1)+'M'} }, x:{grid:{display:false}} }
  }
});
```

**Bar (branch comparison):**
```javascript
new Chart(document.getElementById('barChart'), {
  type:'bar',
  data:{ labels:['Jatim','Jakarta','Sumatra','Sulawesi','Batam','Bali'],
    datasets:[{ label:'Revenue', data:[4200,3800,2100,1500,900,1200], backgroundColor:'#00E273' }] },
  options:{ responsive:true, plugins:{legend:{display:false}},
    scales:{ y:{beginAtZero:true}, x:{grid:{display:false}} } }
});
```

**Horizontal bar (ranking):**
```javascript
new Chart(document.getElementById('rankChart'), {
  type:'bar',
  data:{ labels:['Product A','Product B','Product C','Product D','Product E'],
    datasets:[{ data:[890,720,650,520,430],
      #MJ|      backgroundColor:(ctx)=>ctx.dataIndex===0?'#00E273':'#0A3D50' }] },
  options:{ indexAxis:'y', responsive:true, plugins:{legend:{display:false}},
    scales:{ x:{beginAtZero:true, grid:{color:'rgba(255,255,255,0.05)'}},
             y:{grid:{display:false}, ticks:{color:'#FFFFFF',font:{weight:'500'}}} } }
});
```

**Donut (composition):**
```javascript
new Chart(document.getElementById('donutChart'), {
  type:'doughnut',
  data:{ labels:['Ladies','Men','Kids','Sandal'],
    datasets:[{ data:[45,30,15,10],
      backgroundColor:['#00E273','#00B8D4','#FFB800','#8CA3AD'], hoverOffset:6 }] },
  options:{ responsive:true, cutout:'68%', plugins:{legend:{position:'right'}} }
});
```

**Chart container wrapper (mandatory):**
```html
#RZ|<div class="bg-[#002A3A] border border-white/[0.08] rounded-xl p-6">
  <p class="text-xs font-medium uppercase tracking-widest text-[#8CA3AD] mb-4">[Chart subtitle]</p>
  <div class="relative" style="height: 300px;"><canvas id="[chartId]"></canvas></div>
</div>
```

### §6.6 Layout Grid & Slide Anatomy

```
Light content slide:  min-h-screen bg-white flex flex-col
Dark highlight slide:  min-h-screen bg-[#1A1A1A] flex flex-col px-16 py-12
Content header band: bg-[#002A3A] px-16 py-6 (on light slides only)
Section label:       text-[#00E273] text-xs uppercase tracking-widest mb-2
Assertion title:     text-[#1A202C] text-3xl font-bold tracking-tight (light) / text-white (dark)
Body area:           flex-1  (fills space between title and So What box)
So What box:         mt-4 or mt-auto (always anchored to bottom)
```

### §6.7 Animations

```css
@keyframes slideUp { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:none; } }
@keyframes fadeIn  { from { opacity:0; } to { opacity:1; } }
.slide-up { animation: slideUp .45s ease-out both; }
.fade-in  { animation: fadeIn .35s ease-out both; }
.delay-1  { animation-delay:.1s; } .delay-2 { animation-delay:.2s; } .delay-3 { animation-delay:.3s; }
@media print { .slide { page-break-after: always; } }
```

### §6.8 Full Deck File Template

```html
<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>[DECK TITLE]</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    @keyframes slideUp { from{opacity:0;transform:translateY(16px);}to{opacity:1;transform:none;} }
    .slide-up{animation:slideUp .45s ease-out both;}
    .delay-1{animation-delay:.1s;}.delay-2{animation-delay:.2s;}.delay-3{animation-delay:.3s;}
    @media print{.slide{page-break-after:always;}}
  </style>
  <script>
    /* PASTE CHART.JS GLOBAL DEFAULTS FROM §6.3 HERE */
  </script>
</head>
<body class="font-sans bg-white">
  <!-- One .slide div per slide in arc order -->
  <div class="slide min-h-screen ..."><!-- Slide 1: Cover --></div>
  <div class="slide min-h-screen ..."><!-- Slide 2: Exec Summary --></div>
  <!-- ... -->
  <script>/* All Chart.js initializations here */</script>
</body>
</html>
```

---

## §7 ARGUS → EOS HANDOFF SCHEMA

```json
{
  "meta": {
    "title": "Sales Analysis — Jatim Q1 2026",
    "deck_type": "sales",
    "period": "Q1 2026",
    "prepared_by": "Argus",
    "timestamp": "2026-02-21T11:00:00+07:00"
  },
  "narrative": {
    "situation": "Jatim revenue Rp 1.6M di Q1 2026, naik 15% YoY overall...",
    "complication": "3 Ruko stores drag performance — combined miss Rp 135M vs target...",
    "resolution": "Redistribute 2 SPGs ke mall format recovers Rp 45M/month estimasi."
  },
  "key_insights": [
    "Revenue total naik 15% YoY tapi 3 dari 8 stores missed target",
    "Ladies SKU tumbuh 25% — tertinggi dalam 2 tahun",
    "Redistribusi SPG dari Ruko → Mall estimated recovery Rp 45M/month"
  ],
  "slides": [
    { "slide_num": 1, "type": "cover",
      "title": "Jatim Sales Analysis — Q1 2026", "subtitle": "Branch performance vs target + SKU deep dive" },
    { "slide_num": 2, "type": "exec_summary",
      "bullets": [
        { "layer": "situation",    "text": "Jatim Q1 revenue Rp 1.6M, naik 15% YoY overall." },
        { "layer": "complication", "text": "3 Ruko stores menyeret — combined miss Rp 135M vs target." },
        { "layer": "resolution",   "text": "Redistribusi 2 SPG dari Ruko ke Galaxy Mall recovers ~Rp 45M/month." }
      ]},
    { "slide_num": 3, "type": "kpi_overview",
      "assertion_title": "Jatim Q1 revenue grew 15% YoY but missed overall target by 8%",
      "metrics": [
        { "label": "Total Revenue", "value": "Rp 1.6M", "delta": "+15%", "trend": "up", "context": "Target: Rp 1.74M" },
        { "label": "Units Sold",    "value": "4,180",   "delta": "+9%",  "trend": "up" },
        { "label": "ASP",           "value": "Rp 382K", "delta": "+5%",  "trend": "up" },
        { "label": "Stores",        "value": "8",       "delta": "0",    "trend": "flat" }
      ],
      "so_what": "Despite overall growth, 3 underperforming stores represent the entire gap. Fixing them = target achieved." },
    { "slide_num": 4, "type": "data_analysis", "chart_type": "traffic_light_table",
      "assertion_title": "Only 5 of 8 Jatim stores hit Q1 target — 3 Ruko-format stores missed by 20%+",
      "so_what": "Ruko format consistently underperforms mall by 25%+. Format — not location — is the variable." },
    { "slide_num": 5, "type": "data_analysis", "chart_type": "ranking_bar",
      "assertion_title": "Ladies Classic 1 drives 28% of Jatim revenue; bottom 3 SKUs account for <5% combined",
      "so_what": "Consolidating shelf space from bottom 3 SKUs to Ladies Classic increases display efficiency ~30%." },
    { "slide_num": 6, "type": "framework", "framework": "store_portfolio_2x2",
      "assertion_title": "Two stores are Stars; three Dogs need format or exit decision by Q2",
      "so_what": "Stars warrant SPG increase. Dogs warrant format review — convert to event or close by Q3." },
    { "slide_num": 7, "type": "recommendation",
      "assertion_title": "Three targeted actions recover Rp 90M/month at minimal CAPEX",
      "actions": [
        { "num": "01", "action": "Redistribute 2 SPGs from Ruko Utara to Galaxy Mall", "impact": "Est. +Rp 45M/month" },
        { "num": "02", "action": "Convert Ruko Selatan to event-only format for WILBEX Q2", "impact": "Est. +Rp 30M event revenue" },
        { "num": "03", "action": "Double Ladies Classic 1 replenishment order for Q2", "impact": "Prevent Rp 20M stockout loss" }
      ]},
    { "slide_num": 8, "type": "next_steps",
      "actions": [
        { "action": "SPG reallocation brief to branch manager", "owner": "Branch Mgr Jatim", "due": "1 Mar 2026", "status": "pending" },
        { "action": "WILBEX Ruko format proposal", "owner": "Iris / Events", "due": "5 Mar 2026", "status": "pending" },
        { "action": "Increase Ladies Classic 1 RO qty", "owner": "Argus + WH", "due": "28 Feb 2026", "status": "pending" }
      ]}
  ]
}
```

**Eos rendering rules:**
1. Use `meta.deck_type` → select arc from §2
2. Render slides in array order — do not reorder
3. Use `type` field → select slide template from §3
4. Use `framework` field → select from §4
5. Use `assertion_title` verbatim — never rewrite it
6. Render `so_what` into the So What box from §1.4
7. Apply §6 Mixed Executive Report to all slides — LIGHT for content slides, DARK for Cover/Divider/Closing
8. Output: single self-contained `.html`, all assets from CDN

---

## §8 QUALITY RULES — MANDATORY CHECKLIST

Run before generating any output. Fix failures before proceeding.

### Narrative
- [ ] Every slide title is a complete assertion sentence with a verb
- [ ] Reading all titles in sequence tells the full story
- [ ] Exec Summary is slide 2 (always)
- [ ] Exec Summary has 3-5 bullets in SCR sequence (gray → amber → green)
- [ ] Resolution gets majority of exec summary bullets

### Structure
- [ ] Deck follows the fixed arc from §2 — correct slide count (8/7/10) and order
- [ ] Framework slide is present at its fixed arc position
- [ ] Every data analysis slide has a So What box
- [ ] So What box content is a distinct secondary inference (not a title repeat)
- [ ] Cover, Exec Summary, Recommendation, Next Steps slides have NO So What box

### Visual
- [ ] Content slides (TYPE 2–6) use `bg-white` — NOT dark backgrounds
- [ ] Highlight slides (TYPE 1, 7, 8) use `bg-[#1A1A1A]` — dark only for Cover, Divider, Closing
- [ ] Every content slide has a dark header band `bg-[#002A3A]` at the top
- [ ] Chart.js global defaults block included in `<head>` (§6.3)
- [ ] Charts on light slides wrapped in `bg-[#F8FAFC]` container card
- [ ] Charts on dark slides wrapped in `bg-[#002A3A]` container card
- [ ] Canvas backgrounds are transparent (color comes from card wrapper)
- [ ] No CSS shadows anywhere
#SP|- [ ] Delta colors: positive `#00E273` · negative `#FF4D4D` · warning `#FFB800`
- [ ] Labels on light slides: `text-xs uppercase tracking-widest text-[#4A5568]`
- [ ] Labels on dark slides: `text-xs uppercase tracking-widest text-[#8CA3AD]`

### Output
- [ ] Single `.html` file — self-contained, no local dependencies
- [ ] Print-ready: `@media print { .slide { page-break-after: always; } }`
- [ ] All `canvas id=""` values match their `Chart.js getElementById()` calls
- [ ] Vercel-deployable with zero config

---

## 0. GOLDEN TEMPLATE — START HERE ⭐

> **FOR EVERY DECK:** Copy `GOLDEN-TEMPLATE.html` and replace placeholders.  
> **NEVER design from scratch.** The template is already pixel-perfect Mixed Executive Report.

### Quick Start
1. **Read** `GOLDEN-TEMPLATE-GUIDE.md` — 2 min read, shows exact workflow
2. **Copy** `GOLDEN-TEMPLATE.html` to your workspace
3. **Replace** all `{{PLACEHOLDERS}}` with real data
4. **Deploy** to Vercel

### Template Includes (5 Slides)
- **Cover** — Title slide with Zuma branding
- **Metrics** — 2-4 KPI cards with deltas
- **Chart Breakdown** — Donut chart + legend with progress bars
- **Data Table** — Ranked list with badges and progress bars
- **Insights/Actions** — Key takeaways + action items

### Fallback Design
If golden template fails → use style at https://zuma-bm-jatim.vercel.app/  
Reference screenshots available in workspace.

---

## 1. Zuma Brand System — Mixed Executive Report

> **PRIMARY AESTHETIC.** All visual output (slides, decks, PDF reports, dashboards) uses this system by default.  
> Mixed light/dark: content slides are white with dark header band, highlight slides (Cover, Divider, Closing) are dark.
> Inspired by @mattiapomelli's dark UI prompt pattern (see `design-references/mattiapomelli-dark-ui-prompt.md`), adapted to Zuma brand colors.

### Color Tokens
```css
/* Zuma Mixed Executive Report palette — PRIMARY. Use these, never freestyle. */

/* ══ LIGHT MODE — content slides (default) ══ */
--zuma-page-bg:        #FFFFFF;              /* content slide bg */
--zuma-header-band:    #002A3A;              /* dark strip at top of content slides */
--zuma-card-light:     #FFFFFF;              /* cards on light bg */
--zuma-card-border:    rgba(0,42,58,0.08);   /* subtle border on white cards */
--zuma-text-primary:   #1A202C;              /* headlines, body on light bg */
--zuma-text-secondary: #4A5568;              /* labels, supporting text */
--zuma-text-muted:     #718096;              /* captions, timestamps */

/* ══ DARK MODE — highlight slides (Cover, Divider, Closing) ══ */
--zuma-base:           #1A1A1A;              /* dark highlight slide bg */
--zuma-card:           #002A3A;              /* cards on dark bg */
--zuma-card-alt:       #0A3D50;              /* secondary cards on dark bg */
--zuma-dark-text:      #FFFFFF;              /* headlines on dark bg */
--zuma-dark-secondary: #8CA3AD;              /* labels on dark bg */
--zuma-dark-muted:     #5A7A87;              /* captions on dark bg */
--zuma-border:         rgba(255,255,255,0.08); /* card borders on dark */

/* ══ SHARED — same across both modes ══ */
--zuma-accent:     #00E273;   /* Zuma green — CTAs, fills, progress, active states */
                               /* NEVER on body text — always surface, fill, or indicator */
--zuma-positive:   #00E273;
--zuma-negative:   #FF4D4D;
--zuma-warning:    #FFB800;
--zuma-neutral:    #8CA3AD;

### Typography Scale (Tailwind)
| Use | Class |
|-----|-------|
| Hero number | `text-[72px] font-bold tabular-nums` |
| Slide title | `text-5xl font-bold tracking-tight` |
| Section header | `text-3xl font-bold` |
| Card metric | `text-4xl font-bold tabular-nums` |
| Body (light slide) | `text-base font-normal text-[#4A5568] leading-relaxed` |
| Body (dark slide) | `text-base font-normal text-[#8CA3AD] leading-relaxed` |
| Caption/label (light) | `text-xs font-medium uppercase tracking-widest text-[#4A5568]` |
| Caption/label (dark) | `text-xs font-medium uppercase tracking-widest text-[#8CA3AD]` |
| Delta positive | `text-sm font-medium text-[#00E273]` |
| Delta negative | `text-sm font-medium text-[#FF4D4D]` |

### Aesthetic: Mixed Executive Report
- **Light content slides** — `bg-white` for most slides (KPI, Chart, Table, Framework, Recommendation). Dark `#002A3A` header band at top.
- **Dark highlight slides** — `bg-[#1A1A1A]` for Cover, Section Divider, Next Steps/closing slides only.
- **No shadows, no gradients** — depth from brightness alone. White cards with subtle borders on light slides, dark teal on dark slides.
- **Faint borders** — `border border-[rgba(0,42,58,0.08)]` on light slides, `border-white/[0.08]` on dark slides.
- **Generous padding** — `p-6` minimum on cards, `px-16 py-12` on slides. Never cramped.
- **Rounded corners** — `rounded-xl` (12-16px) consistently on all cards.
- **Single accent color** — Zuma green `#00E273` for all interactive/positive elements. Don't rainbow-spray.
- **Accent never on text** — green is always a surface, fill, border, or indicator. Body text is dark (#1A202C) on light slides, white on dark slides.
- **Oversized numbers** — hero metrics at `text-[72px]`, card metrics at `text-4xl`. Numbers are the star.
- **Small uppercase labels** — all section headers and labels: `text-xs uppercase tracking-widest` in muted gray.
- **Clean geometric sans-serif** — Inter or system font. No decorative fonts.
- **Vibe:** "Professional executive analytics — clean, confident, data-rich. Light and airy for content, dark and impactful for key moments."

---

## 2. Slide Layout Patterns (Legacy Reference — see §3 for PRIMARY templates)

> ⚠️ **DEPRECATED:** The patterns below are legacy examples kept for reference only.
> **USE §3 (Slide Type Templates) as the authoritative source for all slide HTML.**
> §3 uses the correct mixed light/dark system. These §2 patterns show the OLD all-dark style.

### 2.1 Title Slide
```html
#XM|<div class="min-h-screen bg-[#1A1A1A] flex flex-col justify-center px-16 py-12">
  <div class="border-l-4 border-[#00E273] pl-6 mb-8">
    <p class="text-[#00E273] text-xs font-medium uppercase tracking-widest mb-3">Zuma Indonesia</p>
    <h1 class="text-white text-5xl font-bold leading-tight tracking-tight">Judul Presentasi</h1>
  </div>
  <p class="text-[#8CA3AD] text-lg ml-10">Subtitle atau tagline — 1 baris</p>
  <p class="text-[#5A7A87] text-xs uppercase tracking-widest mt-12 ml-10">Februari 2026 · Prepared by Iris</p>
</div>
```

### 2.2 Section Divider
```html
#WT|<div class="min-h-screen bg-[#1A1A1A] flex items-center justify-center">
  <div class="text-center">
    <span class="text-[#00E273] text-xs font-medium uppercase tracking-widest block mb-4">Section 02</span>
    <h2 class="text-white text-6xl font-bold tracking-tight">Nama Section</h2>
  </div>
</div>
```

### 2.3 Metrics Card Grid (KPI slide)
```html
#ZB|<div class="min-h-screen bg-white flex flex-col px-16 py-12">
  <div class="bg-[#002A3A] -mx-16 -mt-12 px-16 py-5 mb-10">
    <p class="text-xs font-medium uppercase tracking-widest text-[#8CA3AD] mb-1">Performance Overview</p>
    <h2 class="text-white text-2xl font-bold">Headline Slide</h2>
  </div>

  <div class="grid grid-cols-3 gap-6 flex-1">
    <!-- Metric card — positive (LIGHT mode: white card, subtle border) -->
    <div class="bg-white border border-[rgba(0,42,58,0.08)] rounded-xl p-6 flex flex-col justify-between">
      <span class="text-xs font-medium uppercase tracking-widest text-[#718096]">Revenue</span>
      <div>
        <p class="text-4xl font-bold text-[#1A202C] tabular-nums mt-4">Rp 4.2M</p>
        <p class="text-sm mt-2 text-[#00E273] font-medium">↑ +12% vs last month</p>
      </div>
    </div>
    <!-- Metric card — negative -->
    <div class="bg-white border border-[rgba(0,42,58,0.08)] rounded-xl p-6 flex flex-col justify-between">
      <span class="text-xs font-medium uppercase tracking-widest text-[#718096]">Returns</span>
      <div>
        <p class="text-4xl font-bold text-[#1A202C] tabular-nums mt-4">142 pcs</p>
        <p class="text-sm mt-2 text-[#FF4D4D] font-medium">↑ +8% vs last month</p>
      </div>
    </div>
    <!-- Metric card — neutral -->
    <div class="bg-white border border-[rgba(0,42,58,0.08)] rounded-xl p-6 flex flex-col justify-between">
      <span class="text-xs font-medium uppercase tracking-widest text-[#718096]">Stores</span>
      <div>
        <p class="text-4xl font-bold text-[#1A202C] tabular-nums mt-4">24</p>
        <p class="text-sm mt-2 text-[#718096] font-medium">Unchanged</p>
      </div>
    </div>
  </div>
</div>
```

### 2.4 Hero Metric Slide (single focus number)
```html
#XM|<div class="min-h-screen bg-white flex flex-col justify-center px-16 py-12">
  <p class="text-xs font-medium uppercase tracking-widest text-[#718096] mb-4">Monthly Revenue</p>
  <h1 class="text-[72px] font-bold text-[#1A202C] tabular-nums leading-none">Rp 4.2M</h1>
  <p class="text-xl text-[#00E273] font-medium mt-3">↑ +24% vs Januari 2026</p>
  <p class="text-[#4A5568] mt-6 max-w-2xl leading-relaxed">Driven by strong performance in Jatim branch (+32%) and successful WILBEX event contributing Rp 800K in additional revenue.</p>
</div>
```

### 2.5 Two-Column: Text + Chart
```html
#ZB|<div class="min-h-screen bg-white flex flex-col px-16 py-12">
  <div class="bg-[#002A3A] -mx-16 -mt-12 px-16 py-5 mb-10">
    <p class="text-xs font-medium uppercase tracking-widest text-[#8CA3AD] mb-1">Trend Analysis</p>
    <h2 class="text-white text-2xl font-bold">Headline</h2>
  </div>
  <div class="grid grid-cols-2 gap-12 flex-1">
    <!-- Left: key points -->
    <div class="flex flex-col justify-center space-y-6">
      <div class="flex gap-4">
        <span class="w-2 h-2 rounded-full bg-[#00E273] mt-2 shrink-0"></span>
        <p class="text-[#4A5568] text-base leading-relaxed">Key insight satu — boleh panjang sedikit karena ini bukan metric</p>
      </div>
      <div class="flex gap-4">
        <span class="w-2 h-2 rounded-full bg-[#00E273] mt-2 shrink-0"></span>
        <p class="text-[#4A5568] text-base leading-relaxed">Key insight dua</p>
      </div>
      <div class="flex gap-4">
        <span class="w-2 h-2 rounded-full bg-[#00E273] mt-2 shrink-0"></span>
        <p class="text-[#4A5568] text-base leading-relaxed">Key insight tiga</p>
      </div>
    </div>
    <!-- Right: chart container -->
    <div class="flex items-center justify-center">
      <canvas id="mainChart" class="w-full"></canvas>
    </div>
  </div>
</div>
```

### 2.6 Data Table
```html
#ZB|<div class="min-h-screen bg-white flex flex-col px-16 py-12">
  <div class="bg-[#002A3A] -mx-16 -mt-12 px-16 py-5 mb-8">
    <p class="text-xs font-medium uppercase tracking-widest text-[#8CA3AD] mb-1">Store Performance</p>
    <h2 class="text-white text-2xl font-bold">Headline</h2>
  </div>
  <div class="overflow-hidden rounded-xl border border-[rgba(0,42,58,0.08)]">
    <table class="w-full text-sm">
      <thead class="bg-[#F1F5F9]">
        <tr>
          <th class="px-6 py-4 text-left font-medium uppercase tracking-widest text-xs text-[#718096]">Store</th>
          <th class="px-6 py-4 text-right font-medium uppercase tracking-widest text-xs text-[#718096]">Revenue</th>
          <th class="px-6 py-4 text-right font-medium uppercase tracking-widest text-xs text-[#718096]">Growth</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-[rgba(0,42,58,0.06)]">
        <tr class="hover:bg-[#F8FAFC]">
          <td class="px-6 py-4 font-medium text-[#1A202C]">Store Name</td>
          <td class="px-6 py-4 text-right tabular-nums text-[#1A202C]">Rp 1.2M</td>
          <td class="px-6 py-4 text-right text-[#00E273] font-medium">+15%</td>
        </tr>
        <tr class="hover:bg-[#F8FAFC]">
          <td class="px-6 py-4 font-medium text-[#1A202C]">Store Name B</td>
          <td class="px-6 py-4 text-right tabular-nums text-[#1A202C]">Rp 980K</td>
          <td class="px-6 py-4 text-right text-[#FF4D4D] font-medium">-5%</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>
```

### 2.7 Conclusion / CTA Slide
```html
#XM|<div class="min-h-screen bg-[#1A1A1A] flex flex-col justify-center px-16 py-12">
  <p class="text-xs font-medium uppercase tracking-widest text-[#00E273] mb-4">Next Steps</p>
  <h2 class="text-white text-4xl font-bold mb-10 tracking-tight">Kesimpulan & Action Items</h2>
  <div class="space-y-6 mb-12">
    <div class="flex items-start gap-4">
      <span class="text-[#00E273] text-xl font-bold tabular-nums shrink-0">01</span>
      <p class="text-[#8CA3AD] text-lg leading-relaxed">Action item pertama — siapa, kapan, apa</p>
    </div>
    <div class="flex items-start gap-4">
      <span class="text-[#00E273] text-xl font-bold tabular-nums shrink-0">02</span>
      <p class="text-[#8CA3AD] text-lg leading-relaxed">Action item kedua</p>
    </div>
    <div class="flex items-start gap-4">
      <span class="text-[#00E273] text-xl font-bold tabular-nums shrink-0">03</span>
      <p class="text-[#8CA3AD] text-lg leading-relaxed">Action item ketiga</p>
    </div>
  </div>
  <div class="border-t border-white/[0.08] pt-8">
    <p class="text-[#5A7A87] text-xs uppercase tracking-widest">Prepared by Iris · Zuma Indonesia · Februari 2026</p>
  </div>
</div>
```

---

## 3. Chart.js Recipes (Mixed Executive Report)

> **CRITICAL:** Charts on LIGHT slides render on `bg-[#F8FAFC]` container. Charts on DARK slides render on `bg-[#002A3A]` container. Canvas background MUST always be transparent.
> Use the correct Chart.js preset (light or dark) depending on the slide mode.
> Every chart MUST use the global defaults below. Copy-paste this block into EVERY deck.

### Setup (include in <head>) — MANDATORY for every deck

**TWO presets: use the correct one based on slide mode.**
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script>
  // ════════════════════════════════════════════════════════════════════════════════
  // CHART PRESET A — LIGHT SLIDES (content slides: KPI, Chart, Table, Framework, Recommendation)
  // Use this for charts on white/light background slides
  // ════════════════════════════════════════════════════════════════════════════════
  function applyChartLightPreset() {
    Chart.defaults.color = '#4A5568';                          // ticks, labels, legend on light bg
    Chart.defaults.borderColor = 'rgba(0,42,58,0.08)';         // grid lines on light bg
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.padding = 20;
    Chart.defaults.plugins.legend.labels.color = '#4A5568';
    Chart.defaults.plugins.tooltip.backgroundColor = '#1A202C';
    Chart.defaults.plugins.tooltip.titleColor = '#FFFFFF';
    Chart.defaults.plugins.tooltip.bodyColor = '#4A5568';
    Chart.defaults.plugins.tooltip.borderColor = 'rgba(0,42,58,0.12)';
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;
    Chart.defaults.plugins.tooltip.padding = 12;
    Chart.defaults.elements.arc.borderWidth = 0;
    Chart.defaults.elements.bar.borderRadius = 6;
    Chart.defaults.elements.bar.borderSkipped = false;
    Chart.defaults.elements.line.tension = 0.4;
    Chart.defaults.elements.point.radius = 4;
    Chart.defaults.elements.point.hoverRadius = 6;
  }

  // ════════════════════════════════════════════════════════════════════════════════
  // CHART PRESET B — DARK SLIDES (highlight slides: Cover, Divider, Closing)
  // Use this for charts on dark #1A1A1A background slides
  // ════════════════════════════════════════════════════════════════════════════════
  function applyChartDarkPreset() {
    Chart.defaults.color = '#8CA3AD';                          // ticks, labels, legend on dark bg
    Chart.defaults.borderColor = 'rgba(255,255,255,0.05)';     // grid lines on dark bg
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.padding = 20;
    Chart.defaults.plugins.legend.labels.color = '#8CA3AD';
    Chart.defaults.plugins.tooltip.backgroundColor = '#0A3D50';
    Chart.defaults.plugins.tooltip.titleColor = '#FFFFFF';
    Chart.defaults.plugins.tooltip.bodyColor = '#8CA3AD';
    Chart.defaults.plugins.tooltip.borderColor = 'rgba(255,255,255,0.08)';
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;
    Chart.defaults.plugins.tooltip.padding = 12;
    Chart.defaults.elements.arc.borderWidth = 0;
    Chart.defaults.elements.bar.borderRadius = 6;
    Chart.defaults.elements.bar.borderSkipped = false;
    Chart.defaults.elements.line.tension = 0.4;
    Chart.defaults.elements.point.radius = 4;
    Chart.defaults.elements.point.hoverRadius = 6;
  }

  // DEFAULT: apply light preset (most slides are light)
  applyChartLightPreset();
  // For charts on dark slides, call applyChartDarkPreset() before initializing that specific chart.
</script>
```

### Zuma Chart Color Palette (use in order)
```javascript
// For multi-series/multi-segment charts — use these in order:
const ZUMA_CHART_COLORS = [
  '#00E273',  // Green accent — always first/primary
  '#00B8D4',  // Cyan — secondary
  #HH|  '#FF4D4D',  // Red — tertiary / negative
  '#FFB800',  // Amber — quaternary / warning
  '#8CA3AD',  // Gray — neutral
  '#5A7A87',  // Muted — lowest priority
  '#A78BFA',  // Violet — if 7+ segments needed
  '#F472B6',  // Pink — if 8+ segments needed
];

// For product-color-specific charts (shoes, fashion), use ACTUAL product colors:
// e.g., Mocca → '#8B6F47', Wine → '#722F37', Black → '#1A1A1A', White → '#E8E8E8'
// Map real product colors to chart segments — more intuitive for fashion data.
```

### 3.1 Line Chart — Trend Over Time
```javascript
new Chart(document.getElementById('lineChart'), {
  type: 'line',
  data: {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun'],
    datasets: [
      {
        label: 'Revenue 2026',
        data: [1200, 1350, 1100, 1500, 1800, 1650],
        borderColor: '#00E273',
        backgroundColor: 'rgba(0,226,115,0.08)',
        borderWidth: 2.5,
        pointBackgroundColor: '#00E273',
        fill: true,
      },
      {
        label: 'Revenue 2025',
        data: [1000, 1100, 950, 1200, 1400, 1300],
        borderColor: '#8CA3AD',
        borderWidth: 2,
        pointBackgroundColor: '#8CA3AD',
        fill: false,
        borderDash: [5, 4],
      }
    ]
  },
  options: {
    responsive: true,
    plugins: {
      legend: { position: 'bottom' },
      tooltip: { mode: 'index', intersect: false }
    },
    scales: {
      y: {
        grid: { color: 'rgba(255,255,255,0.05)' },
        ticks: { callback: v => 'Rp ' + (v/1000).toFixed(0) + 'M' }
      },
      x: { grid: { display: false } }
    }
  }
});
```

### 3.2 Bar Chart — Category Comparison
```javascript
new Chart(document.getElementById('barChart'), {
  type: 'bar',
  data: {
    labels: ['Jatim', 'Jakarta', 'Sumatra', 'Sulawesi', 'Batam', 'Bali'],
    datasets: [{
      label: 'Sales (units)',
      data: [4200, 3800, 2100, 1500, 900, 1200],
      backgroundColor: '#00E273',
    }]
  },
  options: {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      y: { beginAtZero: true },
      x: { grid: { display: false } }
    }
  }
});
```

### 3.3 Donut Chart — Share / Composition
```javascript
// Use ZUMA_CHART_COLORS for generic data, or actual product colors for fashion/product data.
new Chart(document.getElementById('donutChart'), {
  type: 'doughnut',
  data: {
    labels: ['Ladies', 'Men', 'Kids', 'Sandal'],
    datasets: [{
      data: [45, 30, 15, 10],
      backgroundColor: ['#00E273', '#00B8D4', '#FFB800', '#8CA3AD'],
      // For product colors: ['#8B6F47', '#722F37', '#1A1A1A', '#E8E8E8']
      hoverOffset: 6
    }]
  },
  options: {
    responsive: true,
    cutout: '68%',
    plugins: {
      legend: { position: 'right' }
    }
  }
});
```

### 3.4 Horizontal Bar — Ranking
```javascript
new Chart(document.getElementById('rankChart'), {
  type: 'bar',
  data: {
    labels: ['Product A', 'Product B', 'Product C', 'Product D', 'Product E'],
    datasets: [{
      data: [890, 720, 650, 520, 430],
      backgroundColor: (ctx) => ctx.dataIndex === 0 ? '#00E273' : '#0A3D50',
    }]
  },
  options: {
    indexAxis: 'y',
    responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      x: { beginAtZero: true },
      y: { grid: { display: false }, ticks: { color: '#FFFFFF' } }
    }
  }
});
```

### 3.5 Chart Container HTML Pattern
```html
<!-- LIGHT MODE (content slides: TYPE 2–6) — chart on light card -->
<div class="bg-[#F8FAFC] border border-[rgba(0,42,58,0.08)] rounded-xl p-6">
  <p class="text-xs font-medium uppercase tracking-widest text-[#4A5568] mb-4">Chart Title</p>
  <div class="relative" style="height: 300px;">
    <canvas id="chartId"></canvas>
  </div>
</div>
<!-- Canvas background is TRANSPARENT — the light card behind it provides the clean look -->

<!-- DARK MODE (highlight slides: TYPE 1, 7, 8) — chart on dark card -->
<div class="bg-[#0A3D50] border border-white/[0.08] rounded-xl p-6">
  <p class="text-xs font-medium uppercase tracking-widest text-[#8CA3AD] mb-4">Chart Title</p>
  <div class="relative" style="height: 300px;">
    <canvas id="chartId"></canvas>
  </div>
</div>
<!-- Canvas background is TRANSPARENT — the dark card behind it provides the dark look -->
```

---

## 4. Animation Patterns

### Slide-in on load (CSS only)
```css
@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}

.slide-up    { animation: slideUp 0.5s ease-out both; }
.fade-in     { animation: fadeIn 0.4s ease-out both; }
.delay-100   { animation-delay: 0.1s; }
.delay-200   { animation-delay: 0.2s; }
.delay-300   { animation-delay: 0.3s; }
```

Usage:
```html
<h1 class="slide-up">Title</h1>
<div class="slide-up delay-100">Card 1</div>
<div class="slide-up delay-200">Card 2</div>
```

### Number counter animation (JS)
```javascript
function animateCounter(el, target, duration = 1200, prefix = '', suffix = '') {
  const start = 0;
  const startTime = performance.now();
  const update = (now) => {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
    el.textContent = prefix + Math.round(start + (target - start) * eased).toLocaleString('id-ID') + suffix;
    if (progress < 1) requestAnimationFrame(update);
  };
  requestAnimationFrame(update);
}
// Usage: animateCounter(document.getElementById('revenue'), 4200000, 1500, 'Rp ', '')
```

---

## 5. Argus → Eos Handoff Schema

When Iris delegates a data presentation task, Argus produces data first, then Eos renders it. Argus outputs a JSON file to its `outbox/`, Eos reads it.

### Standard Handoff Format
```json
{
  "meta": {
    "title": "Judul Presentasi",
    "period": "Q1 2026",
    "prepared_by": "Argus",
    "timestamp": "2026-02-21T11:00:00+07:00"
  },
  "narrative": {
    "situation": "Penjualan Zuma Q1 2026 naik 12% YoY...",
    "complication": "Namun margin menurun di Batam dan Jakarta...",
    "question": "Apa yang harus diprioritaskan untuk Q2?",
    "answer": "Fokus pada 3 toko dengan growth tertinggi..."
  },
  "key_insights": [
    "Revenue total Rp 4.2M, naik 12% vs Q1 2025",
    "Jatim masih dominan, 38% dari total revenue",
    "Produk Ladies tumbuh 25% — tertinggi dalam 2 tahun"
  ],
  "slides": [
    {
      "type": "metrics",
      "headline": "Q1 2026 Performance Overview",
      "metrics": [
        { "label": "Total Revenue", "value": "Rp 4.2M", "delta": "+12%", "trend": "up" },
        { "label": "Units Sold",    "value": "12,400",  "delta": "+8%",  "trend": "up" },
        { "label": "Active Stores", "value": "24",      "delta": "0%",   "trend": "flat" }
      ]
    },
    {
      "type": "line_chart",
      "headline": "Monthly Revenue Trend",
      "chart_data": {
        "labels": ["Jan", "Feb", "Mar"],
        "current":  [1200000, 1500000, 1400000],
        "previous": [1000000, 1200000, 1150000],
        "series_labels": ["2026", "2025"],
        "y_format": "currency_idr"
      },
      "annotation": "Feb spike driven by Valentine campaign"
    },
    {
      "type": "bar_chart",
      "headline": "Revenue by Branch",
      "chart_data": {
        "labels": ["Jatim", "Jakarta", "Sumatra", "Sulawesi", "Batam", "Bali"],
        "values": [1600000, 900000, 700000, 450000, 300000, 250000],
        "y_format": "currency_idr",
        "highlight_index": 0
      }
    },
    {
      "type": "table",
      "headline": "Top 5 Products",
      "columns": ["Product", "Units", "Revenue", "Growth"],
      "rows": [
        ["Ladies Classic 1", "890", "Rp 45M", "+25%"],
        ["Men Black 3",      "720", "Rp 38M", "+18%"]
      ],
      "highlight_column": 3
    }
  ]
}
```

### Slide Types Reference
| `type` | Description | Required `chart_data` keys |
|--------|-------------|---------------------------|
| `metrics` | KPI cards grid | `metrics[]` (label, value, delta, trend) |
| `line_chart` | Trend over time | `labels`, `current`, optional `previous` |
| `bar_chart` | Category compare | `labels`, `values`, optional `highlight_index` |
| `donut_chart` | Composition/share | `labels`, `values` |
| `table` | Ranked/structured data | `columns`, `rows`, optional `highlight_column` |
| `text` | Insights/bullets | `points[]` — array of strings |
| `split` | Two-column (text + chart) | `points[]` + embedded chart config |

### Eos Rendering Rules
1. **Read meta first** — use `title` for title slide, `period` in footer
2. **Render narrative** as a dedicated narrative/SCQA slide before content
3. **Preserve order** — render slides in the array order
4. **Use `key_insights`** on executive summary slide (first content slide)
5. **Apply brand** — content slides use white bg + dark header band; highlight slides (Cover/Divider/Closing) use `#1A1A1A` dark bg. Apply §6 Mixed Executive Report.
6. **Single .html output** — self-contained, all assets inline or CDN

---

## 6. PPT Architecture (Full Deck)

### File structure (single .html)
```html
<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ title }}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    /* Animation classes */
    @keyframes slideUp { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:none; } }
    .slide-up { animation: slideUp .45s ease-out both; }
    .delay-1  { animation-delay: .1s; }
    .delay-2  { animation-delay: .2s; }
    .delay-3  { animation-delay: .3s; }
    /* Print: each slide is one page */
    @media print { .slide { page-break-after: always; } }
  </style>
</head>
<body class="font-sans bg-white">
  <!-- SLIDES: each .slide div = one page -->
  <div class="slide min-h-screen ...">...</div>
  <div class="slide min-h-screen ...">...</div>
  <!-- CHARTS: init all at end -->
  <script>/* Chart.js initializations */</script>
</body>
</html>
```

### Slide count guidelines
| Deck type | Slides |
|-----------|--------|
| Quick update / 1 topic | 5–8 |
| Monthly review | 10–15 |
| Deep dive / strategy | 15–25 |
| Executive summary | 4–6 |

---

## 7. Quick Reference: Common Tailwind Classes

| Need | Light slide class | Dark slide class |
|------|-------------------|------------------|
| Slide bg (content) | `bg-white` | `bg-[#1A1A1A]` |
| Header band | `bg-[#002A3A] -mx-16 -mt-12 px-16 py-5` | (integrated into dark bg) |
| Card surface | `bg-white border border-[rgba(0,42,58,0.08)] rounded-xl p-6` | `bg-[#002A3A] border border-white/[0.08] rounded-xl p-6` |
| Green accent fill | `bg-[#00E273]` | `bg-[#00E273]` |
| Green accent text | `text-[#00E273]` — use sparingly, prefer on indicators | `text-[#00E273]` |
| Primary text | `text-[#1A202C]` | `text-white` |
| Secondary text | `text-[#4A5568]` | `text-[#8CA3AD]` |
| Muted text | `text-[#718096]` | `text-[#5A7A87]` |
| Label / header | `text-xs font-medium uppercase tracking-widest text-[#718096]` | `text-xs font-medium uppercase tracking-widest text-[#8CA3AD]` |
| Hero number | `text-[72px] font-bold tabular-nums text-[#1A202C]` | `text-[72px] font-bold tabular-nums text-white` |
| Positive delta | `text-[#00E273] font-medium` | `text-[#00E273] font-medium` |
| Negative delta | `text-[#FF4D4D] font-medium` | `text-[#FF4D4D] font-medium` |
| Neutral delta | `text-[#718096] font-medium` | `text-[#8CA3AD] font-medium` |
| Green left border | `border-l-4 border-[#00E273]` | `border-l-4 border-[#00E273]` |
| Full-screen slide | `min-h-screen bg-white flex flex-col px-16 py-12` | `min-h-screen bg-[#1A1A1A] flex flex-col px-16 py-12` |
| Monospaced numbers | `tabular-nums` | `tabular-nums` |
| Tight headline | `text-[#1A202C] font-bold tracking-tight` | `text-white font-bold tracking-tight` |
| Card border | `border border-[rgba(0,42,58,0.08)]` — faint, no shadows | `border border-white/[0.08]` — faint, no shadows |
| Table divider | `divide-y divide-[rgba(0,42,58,0.06)]` | `divide-y divide-white/[0.05]` |
| Hover row | `hover:bg-[#F8FAFC]` | `hover:bg-white/[0.03]` |
| Table header bg | `bg-[#F1F5F9]` | `bg-[#002A3A]` |

## 8. Prompt Engineering Patterns (from Design References)

Reference: `design-references/youmind-prompt-gallery.md` for full details.

### 8.1 Conditional Slide Branching
Adapt slide style based on content type — don't use one-size-fits-all:
```
IF content_type == "sales":
  → Warm palette, large hero numbers, upward trend emphasis
  → Headline: achievement-focused ("Delivered 142% of target")
IF content_type == "operational":
  → Neutral palette, dense data tables, status indicators
  → Headline: status-focused ("3 stores below threshold")
IF content_type == "product_launch":
  → Brand palette, full-bleed product images, minimal text
  → Headline: benefit-focused ("30% faster restock cycle")
```

### 8.2 Color Palette Derivation
Auto-generate slide theme from brand/data:
```
1. Light base: White (#FFFFFF) for content slides — clean, readable
2. Dark base: Near-black (#1A1A1A) for highlight slides only — Cover, Section Divider, Closing
3. Header band: Dark teal (#002A3A) as top header band on light slides
4. Cards (light): White with rgba(0,42,58,0.08) border — subtle depth
5. Cards (dark): Dark teal (#002A3A) with rgba(255,255,255,0.08) border
6. Accent: Zuma green (#00E273) for positive metrics, CTAs, fills
7. Negative: Red (#FF4D4D) for declines, alerts
8. Warning: Amber (#FFB800) for moderate deltas
9. Text (light): Dark (#1A202C) primary, gray (#4A5568) secondary, muted (#718096)
10. Text (dark): White (#FFFFFF) primary, teal-gray (#8CA3AD) secondary, muted (#5A7A87)
11. Borders (light): rgba(0,42,58,0.08) — faint separation
12. Borders (dark): rgba(255,255,255,0.08) — faint separation
13. Text contrast: auto WCAG AA minimum
```

### 8.3 Multi-Step Rendering Chain
Before generating any slide, follow this sequence:
```
Step 1: Data Analysis → identify key metrics, trends, anomalies
Step 2: Narrative Frame → situation/complication/question/answer (SCQA)
Step 3: Visual Style → match content type to slide template
Step 4: Layout Composition → assign data to slide regions
Step 5: Render → generate HTML with Tailwind
```

### 8.4 Precise Layout Specs
Always specify exact proportions (not vague "big" or "small"):
```
Hero metric card:  w-full, h-[200px], text-[72px] for number
Info grid:         grid-cols-2 lg:grid-cols-4, gap-4
Chart area:        min-h-[300px], aspect-[16/9]
Card padding:      p-6 (24px)
Card radius:       rounded-xl (12px)
Card gap:          gap-4 (16px)
```

### 8.5 Parameterized Slide Templates
Use variables for reusable deck patterns:
```html
<!-- Template: Metric Highlight Slide (DARK — for hero/emphasis moments) -->
<div class="min-h-screen bg-[#1A1A1A] text-white px-16 py-12">
  <p class="text-sm text-[#8CA3AD] uppercase tracking-widest">{SECTION_LABEL}</p>
  <h1 class="text-[72px] font-bold tabular-nums">{HERO_NUMBER}</h1>
  <p class="text-xl text-[#00E273]">{DELTA} vs {COMPARISON_PERIOD}</p>
  <p class="text-[#8CA3AD] mt-4 max-w-2xl">{NARRATIVE}</p>
</div>

<!-- Template: Content Slide (LIGHT — default for most slides) -->
<div class="min-h-screen bg-white flex flex-col px-16 py-12">
  <div class="bg-[#002A3A] -mx-16 -mt-12 px-16 py-5 mb-10">
    <p class="text-xs font-medium uppercase tracking-widest text-[#8CA3AD] mb-1">{SECTION_LABEL}</p>
    <h2 class="text-white text-2xl font-bold">{SLIDE_TITLE}</h2>
  </div>
  <!-- Content area with dark text on white bg -->
  <div class="flex-1">
    {CONTENT_BLOCKS}
  </div>
</div>
```
Replace `{VARIABLES}` with data from Argus handoff JSON.

### 8.6 Claude Opus 4.6 Design Mega-Prompts (Source: @Marryclaire_AI, Feb 2026)

10 production-grade prompts for design system work. Use these as **templates** — adapt placeholders `[LIKE THIS]` to Zuma context before running. These work best with Claude Opus 4.6 but adapt to any capable model.

#### Prompt 1: Design System Architect
Role-play as Apple Principal Designer. Generates complete Apple HIG-style design system:
- **Foundations:** Color system (6 primary + semantic + dark mode), typography (9 weights with exact sizes), 12-column responsive grid, 8px spacing scale
- **Components:** 30+ components (nav, input, feedback, data, media) with anatomy, all states (default/hover/active/disabled/loading/error), ARIA accessibility, code-ready specs
- **Patterns:** 5 page templates, user flows (onboarding, auth, search, checkout), feedback patterns
- **Tokens:** Complete design token JSON for developer handoff
- **Docs:** 3 core principles, 10 do's/don'ts, implementation guide

#### Prompt 2: Brand Identity Creator
Role-play as Pentagram Creative Director. Full brand identity system:
- **Strategy:** Brand story (challenge→transformation→resolution), personality archetypes, voice/tone matrix (4 dimensions), messaging hierarchy
- **Visual Identity:** 3 logo directions (wordmark, symbol, combination) with variations (mono, reversed, min-size, clear space), color palette (Hex/Pantone/CMYK/RGB), typography, imagery guidelines
- **Applications:** Business cards, letterhead, email signatures, social media templates (5 platforms), presentation template
- **Guidelines:** 20-page brand book structure

#### Prompt 3: UI/UX Pattern Master
Role-play as Apple Senior UI Designer. Complete app UI:
- **8 Key Screens:** Onboarding, Home/Dashboard, Primary task, Detail view, Settings, Search/Filter, Checkout, Error/Empty — each with wireframe, component inventory, interaction specs, empty/error/loading states
- **Accessibility:** Dynamic Type 310%, VoiceOver labels, WCAG AA contrast, Reduce Motion alternatives
- **Micro-interactions:** Transition definitions, haptic feedback, easing curves
- **Responsive:** Mobile/tablet/desktop breakpoints, orientation, foldable device considerations

#### Prompt 4: Marketing Asset Factory
Role-play as top-tier agency Creative Director. Generates 47+ marketing assets:
- **Digital Ads (15):** Google Ads (headlines/descriptions/display), Facebook/Instagram (feed/story/reel concepts)
- **Email Marketing (8):** Welcome series (3), promotional (1), nurture (3), re-engagement (1)
- **Landing Pages (5):** Hero, features, social proof, FAQ, pricing
- **Social Media (12):** LinkedIn (4), Twitter/X threads (2), Instagram (3), TikTok scripts (3)
- **Sales Enablement (7):** One-pager, sales deck, case study, battlecard, demo script, objection handling, proposal

#### Prompt 5: Figma Auto-Layout Expert
Role-play as Figma Design Ops Specialist. Figma-ready technical specs:
- **Auto-Layout:** Direction, padding, spacing, distribution, alignment, resizing for every component
- **Component Architecture:** Master components, variant properties (boolean/instance swap/text), variant matrix
- **Design Tokens:** Color/text/effect/grid styles with exact values
- **Prototype:** Interaction map, triggers, smart animate specs, easing curves
- **Handoff:** CSS properties, export settings (1x/2x/3x/SVG), naming conventions

#### Prompt 6: Design Critique Partner
Role-play as Apple Design Director reviewing work. Comprehensive critique:
- **Heuristic Evaluation:** Nielsen's 10 heuristics, scored 1-5 with specific examples
- **Visual Hierarchy:** First/second/third attention, CTA hierarchy, weight balance, whitespace
- **Typography Audit:** Font appropriateness, scale hierarchy, line lengths (45-75 chars), contrast
- **WCAG Analysis:** Color contrast, meaningful color use, dark mode
- **Strategic Alignment:** Business goals, user goals, value prop clarity, competitive differentiation
- **Prioritized Recommendations:** Critical (pre-launch) → Important (next iteration) → Polish

#### Prompt 7: Design Trend Synthesizer
Role-play as frog Design Researcher. 2026 trend analysis:
- **5 Macro Trends:** Visual aesthetics, interaction patterns, color trends, typography trends, tech influence — each with definition, characteristics, origin, adoption phase, 3 brand examples, strategic implications
- **Competitive Mapping:** 10 competitors on 2×2 matrix (Innovative↔Conservative × Minimal↔Rich)
- **User Shifts:** Post-AI behaviors, new mental models, friction intolerance
- **Platform Evolution:** iOS 26/visionOS, Material You, web patterns
- **Mood Board:** 20 visual references with detailed descriptions

#### Prompt 8: Accessibility Auditor
Role-play as Apple Accessibility Specialist. WCAG 2.2 Level AA audit:
- **Perceivable:** Alt text strategy, captions, color independence, contrast ratios (4.5:1 text, 3:1 UI), text resize 200%
- **Operable:** Keyboard accessibility, skip links, focus order, visible focus (2px/3:1), touch targets 44×44px, motion disable
- **Understandable:** Language identification, consistent components, error handling (identification, suggestions, prevention)
- **Robust:** Valid markup, ARIA name/role/value, live regions
- **Cognitive:** Flesch-Kincaid Grade 8, consistent nav, plain language errors

#### Prompt 9: Design-to-Code Translator
Role-play as Vercel Design Engineer. Production-ready frontend code:
- **Architecture:** Component hierarchy, TypeScript props interface, state management, data flow
- **Code:** Copy-paste ready, responsive (mobile-first), ARIA attributes, error boundaries, animations
- **Styling:** Tailwind/CSS with design token mapping, CSS variables, dark mode, hover/focus/active states
- **Tokens:** Color/typography/spacing/shadow/border-radius token integration
- **Performance:** Code splitting, bundle optimization, React.memo/useMemo, image optimization
- **Testing:** Unit tests (RTL), visual regression, axe-core accessibility, responsive tests

#### Prompt 10: Presentation Designer
Role-play as Apple Presentation Designer. Keynote-level deck:
- **Narrative:** Hero's journey for business, opening hook (60s), 3 core messages max, closing CTA
- **20-30 Slides:** Each with layout type, visual description, exact copy (headlines 6 words max, body 20 words max), speaker notes (60-90s), animation notes
- **Slide Structure:** Title → Agenda → Problem → Current State → Opportunity → Solution → How It Works → Benefits → Proof → Competitive → Business Model → Traction → Roadmap → Team → The Ask → Closing
- **Visual System:** Color palette, typography (display + body), imagery style, data viz style, iconography
- **Presenter Materials:** Pacing, transitions, interaction moments, 5 backup slides, one-pager handout

> **Usage:** Pick the prompt that matches your task. Replace `[PLACEHOLDERS]` with Zuma-specific values. These are **starting templates** — Eos should adapt them to Zuma's Mixed Executive Report aesthetic (white content slides with `#002A3A` header band, dark `#1A1A1A` highlight slides, green `#00E273` accent).

### 8.7 SaaS Landing Page Brief Formula (Source: @namyakhann / Supafast, Feb 2026)

Framework from analysis of 1,000+ SaaS landing pages. Claims 7-8% conversion rate.

**8 Inputs you provide:**
1. **Product** — What you're selling
2. **Audience** — Who it's for
3. **Pain point** — The core problem
4. **Outcome** — What life looks like after
5. **Differentiator** — Why you, not competitors
6. **Price** — How much / pricing model
7. **Traffic source** — Where visitors come from (ads, organic, referral)
8. **Primary CTA** — The one action you want

**Generates 7 Sections:**
1. **Hero** (5-Second Test) — Visitor knows what you do instantly
2. **Problem / Pain** (PAS framework) — Problem → Agitate → Solution
3. **Solution** (Outcomes-focused) — Show the transformation
4. **Social Proof** (Real Numbers) — Metrics, testimonials, logos
5. **How It Works** (Step-by-step) — Remove complexity fear
6. **Objection Crusher** (FAQ) — Kill doubts before they grow
7. **Final CTA** (Mirror Hero) — Echo the opening hook to close

**Conversion psychology flow:**
```
HOOK → PAIN → HOPE → TRUST → DOUBT → CLOSE
```

> **Usage:** Feed 8 answers as structured input → AI generates complete landing page brief. Use with Prompt 9 (Design-to-Code) or Prompt 4 (Marketing Asset Factory) to build the actual page. Adapt for Zuma event landing pages (WILBEX, IMBEX), product launches, or internal tool pages.

### 8.8 UI Prompt Architecture Pattern (Source: @mattiapomelli, Feb 2026)

When describing any UI to an AI model, follow this 4-step structure for best results:

1. **What + Format:** "[Type] [screen]. [Container format]." — e.g., "Health dashboard home screen. Single scrollable mobile screen."
2. **Structure (top-to-bottom):** Describe every section sequentially, as user would scroll
3. **Style (exact specs):** Every color as hex, every spacing as px, every font weight named — never vague "dark" or "rounded"
4. **Vibe (anchor metaphor):** 2-3 cultural references to triangulate aesthetic — e.g., "Oura Ring's data depth meets a fighter pilot's HUD"

**Key prompt techniques:**
- **Negative constraints:** Explicitly state what NOT to do ("no warmth", "never on text", "no shadows")
- **Sensory anchors:** Physical textures in digital design ("hazard-tape energy", "neon on asphalt")
- **Exact specifications:** `rgba(255,255,255,0.08)`, `14-16px` — precision eliminates AI guesswork

> **Full reference prompt:** See `design-references/mattiapomelli-dark-ui-prompt.md` for the complete verbatim prompt that inspired Zuma's dark highlight slide aesthetic.

## 9. External UI Pattern Libraries

When building complex visuals, reference these open-source libraries for ready-made patterns:

- **ReUI** (https://reui.io) — 966+ shadcn/ui patterns. Especially useful:
  - 25 chart patterns, 22 data-grid patterns, 12 timeline patterns
  - 61 button variants, 35 avatar patterns, 30 calendar patterns
  - Kanban (5), Stepper (15), Sortable (7) patterns
  - Free, open-source, dual Radix/Base UI support
  - Best for: visual variety in dashboards, data tables, metric cards

---

## §10 — HTML DECK IMPLEMENTATION: MIXED EXECUTIVE REPORT PATTERN

> **This is the authoritative technical spec for building HTML presentation decks.**
#NV|> Validated against the working bm-jatim deck (https://bm-jatim.vercel.app, Feb 2026).
> Copy patterns from this section exactly. Do NOT invent new CSS structures.

### §10.1 Visual Design Reference

**Inspiration:** Nauda Pitch Deck (dribbble.com/shots/20968470-Nauda-Presentation-Pitch-Deck-Slides)
**Adaptation:** Nauda's electric blue → Zuma Mixed Executive Report (white content slides with `#002A3A` header band, dark `#1A1A1A` highlight slides, `#00E273` accent)

**What to steal from Nauda:**
- Very large bold headlines dominating each slide (42-76px, weight 800)
- Large decorative slide numbers as watermarks (nearly invisible, top-right)
- Section labels in tiny green uppercase above the headline
- Numbered action cards with huge "01/02/03" in accent color
- Horizontal timeline with green dots for Next Steps
- Bottom branding bar on every slide (logo left, title center, counter right)
- Cover slide: bold centered title + subtle geometric accent shape
- Minimal backgrounds — no gradients, no textures. Flat dark surfaces.

### §10.2 Color Tokens (MANDATORY — never deviate)

```css
:root {
  /* Light mode — content slides (default) */
  --page-bg:    #FFFFFF;              /* content slide background */
  --header:     #002A3A;              /* dark header band on content slides */
  --card-light: #FFFFFF;              /* cards on light bg */
  --card-border: rgba(0,42,58,0.08); /* subtle border on white cards */
  --text-main:  #1A202C;              /* primary text on light bg */
  --text-sub:   #4A5568;              /* secondary text on light bg */
  --text-dim:   #718096;              /* muted text on light bg */

  /* Dark mode — highlight slides (Cover, Divider, Closing) */
  --base:    #1A1A1A;              /* dark highlight slide bg */
  --surface: #002A3A;              /* cards on dark bg */
  --deep:    #001E2B;              /* branding bar, darkest elements */
  --muted:   #8CA3AD;              /* secondary text on dark bg */
  --dim:     #5A7A87;              /* muted text on dark bg */
  --white:   #FFFFFF;

  /* Shared — same across both modes */
  --accent:  #00E273;              /* green — primary accent, borders, labels */
  --neg:     #FF4D4D;              /* red — negative values, below-target */
  --warn:    #FFB800;              /* amber — at-risk, warning states */
  --so-what-light: rgba(0,226,115,0.06); /* So What box on light slides */
  --so-what-dark:  rgba(0,226,115,0.08); /* So What box on dark slides */
}
```

### §10.3 Critical Architecture: Slide Transitions

**⚠️ NEVER USE `display: none/flex` to show/hide slides.** It breaks opacity transitions.

**CORRECT pattern (visibility + opacity + position:absolute):**

```css
#deck {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}

.slide {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  padding: 56px 72px 120px;   /* bottom padding clears branding bar */
  visibility: hidden;
  opacity: 0;
  transition: opacity 0.4s cubic-bezier(.4,0,.2,1);
  display: flex;              /* always flex — never toggled */
  flex-direction: column;
  overflow: hidden;
  z-index: 1;
}

.slide.active {
  visibility: visible;
  opacity: 1;
  z-index: 2;
}
```

**Why:** `display` property cannot be animated. Toggling `visibility` + `opacity` produces smooth fade-in while `position:absolute` stacks slides on top of each other.

### §10.4 Critical Architecture: Chart.js on Hidden Slides

**⚠️ NEVER initialize Chart.js when the slide is invisible.** Canvas height = 0 when slide has `visibility:hidden`.

**CORRECT pattern — lazy init with setTimeout:**

```js
function showSlide(idx) {
  slides[current].classList.remove('active');
  current = idx;
  slides[current].classList.add('active');
  counter.textContent = (current + 1) + ' / ' + total;

  // Init charts AFTER slide is visible — 60ms gives browser time to reflow
  if (current === 4 && !window._chart1) setTimeout(initRankingChart, 60);
  if (current === 5 && !window._chart2) setTimeout(initMatrixChart, 60);
}
```

**Also: set `responsive: true, maintainAspectRatio: false` on every Chart.js config** so canvas fills its container regardless of slide size.

### §10.5 Navigation JS (Canonical Pattern)

```js
var slides = document.querySelectorAll('.slide');
var counter = document.getElementById('slideCounter');
var total = slides.length;
var current = 0;

function showSlide(idx) {
  if (idx < 0) idx = total - 1;
  if (idx >= total) idx = 0;
  slides[current].classList.remove('active');
  current = idx;
  slides[current].classList.add('active');
  counter.textContent = (current + 1) + ' / ' + total;
  // chart lazy-init here (see §10.4)
}

document.addEventListener('keydown', function(e) {
  if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'Enter') { e.preventDefault(); showSlide(current + 1); }
  if (e.key === 'ArrowLeft') { e.preventDefault(); showSlide(current - 1); }
  var num = parseInt(e.key);
  if (num >= 1 && num <= 8) showSlide(num - 1);
});

// Click anywhere to advance (except charts and links)
document.getElementById('deck').addEventListener('click', function(e) {
  if (!e.target.closest('a, button, canvas')) showSlide(current + 1);
});
```

### §10.6 Branding Bar (Required on Every Deck)

**Position:** Fixed bottom, always visible across all slides.

```html
<div class="brand-bar">
  <div class="brand-left">
    <span class="brand-dot"></span>
    <span>Zuma Indonesia</span>
  </div>
  <div class="brand-center">Sales Analysis · [Branch] [Period]</div>
  <div class="brand-right" id="slideCounter">1 / 8</div>
</div>
```

```css
.brand-bar {
  position: fixed;
  bottom: 0; left: 0; right: 0;
  height: 48px;
  background: var(--deep);
  border-top: 1px solid rgba(255,255,255,0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 72px;
  z-index: 100;
  font-size: 12px;
  font-weight: 500;
  color: var(--muted);
}
.brand-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--accent);
}
.brand-center {
  position: absolute; left: 50%; transform: translateX(-50%);
}
```

### §10.7 Watermark Slide Number

Add to every slide. Nearly invisible — purely decorative.

```html
<div class="slide-watermark">03</div>
```

```css
.slide-watermark {
  position: absolute;
  top: -20px; right: 48px;
  font-size: 180px;
  font-weight: 800;
  color: rgba(255,255,255,0.035);
  line-height: 1;
  z-index: 0;
  pointer-events: none;
  user-select: none;
}
```

### §10.8 Typography Classes

```css
.section-label {          /* e.g. "STORE PERFORMANCE" above headline */
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 16px;
}
.slide-headline {         /* main assertion title — always a complete sentence */
  font-size: 42px;
  font-weight: 800;
  line-height: 1.15;
  color: var(--white);    /* on dark slides */
  margin-bottom: 36px;
  max-width: 900px;
}
.slide-headline.light {  /* on light content slides */
  color: #1A202C;
}
.muted-label {            /* small caps labels inside cards on dark slides */
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted);   /* #8CA3AD on dark */
}
.muted-label.light {     /* on light content slides */
  color: #4A5568;
}
```

**Headline size guide by slide type:**
- Cover: `font-size: 76px`
- Exec Summary headline: `font-size: 36px`
- Data slides (KPI, Table, Chart): `font-size: 32-42px`
- Recommendation, Next Steps: `font-size: 38px`

### §10.9 Per-Slide Component Specs

> **Mode reminder:** Cover = DARK. Exec Summary through Recommendation = LIGHT. Next Steps = DARK. Section Divider = DARK.

#### Cover (DARK mode)
```css
.cover-shape {            /* subtle decorative geometric — lower-right */
  position: absolute;
  bottom: -60px; right: -40px;
  width: 500px; height: 350px;
  background: var(--accent);
  opacity: 0.06;
  transform: rotate(-8deg);
  border-radius: 24px;
  z-index: 0;
  pointer-events: none;
}
```
No So What box. No table. Just: section-label → cover-title → cover-subtitle → metadata row.

#### Exec Summary (LIGHT mode)
2×2 grid of SCQ cards on white background. Each card:
2×2 grid of SCQ cards. Each card:
```css
.scq-card {
  background: #FFFFFF;
  border-radius: 12px;
  padding: 28px 28px 28px 0;   /* no left padding — bar provides the visual start */
  display: flex;
  border: 1px solid rgba(0,42,58,0.08);
}
.scq-bar {                /* left-side colored accent bar */
  width: 3px;
  align-self: stretch;
  border-radius: 2px;
  flex-shrink: 0;
  margin: 0 20px 0 0;
}
.scq-bar.green { background: var(--accent); }   /* Situasi, Resolusi */
.scq-bar.amber { background: var(--warn); }     /* Komplikasi */
.scq-text { color: #1A202C; }                   /* dark text on light bg */
.scq-label { color: #4A5568; }                  /* secondary text on light bg */
No So What box on Exec Summary.

#### KPI Overview (LIGHT mode)
4-column grid of white metric cards on white bg. KPI number: `font-size: 52px, font-weight: 800, color: #1A202C`. Requires So What box.
4-column grid of metric cards. KPI number: `font-size: 52px, font-weight: 800`. Requires So What box.
```css
.kpi-card { background: #FFFFFF; border: 1px solid rgba(0,42,58,0.08); border-radius: 12px; }
.kpi-number { color: #1A202C; font-size: 52px; font-weight: 800; }
.kpi-label { color: #4A5568; font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; }
.kpi-delta.up   { background: rgba(0,226,115,0.10); color: var(--accent); }
.kpi-delta.flat { background: rgba(0,42,58,0.05); color: #718096; }
.kpi-delta.down { background: rgba(255,77,77,0.10); color: var(--neg); }
```

#### Traffic Light Table (LIGHT mode)
```css
.data-table { background: #FFFFFF; border: 1px solid rgba(0,42,58,0.08); border-radius: 12px; }
.data-table thead { background: #002A3A; }       /* dark header band on table */
.data-table thead th { color: #8CA3AD; }         /* muted labels in dark header */
.data-table tbody tr:nth-child(odd)  { background: #F8FAFC; }
.data-table tbody tr:nth-child(even) { background: #FFFFFF; }
.data-table tbody tr:hover           { background: rgba(0,42,58,0.04); }
.td-pos { color: var(--accent); font-weight: 600; }
.td-neg { color: var(--neg);    font-weight: 600; }
.td-flat { color: #718096; }
/* Status pills */
.pill-green { background: rgba(0,226,115,0.1);  color: var(--accent); }
.pill-amber { background: rgba(255,184,0,0.1);  color: var(--warn); }
.pill-red   { background: rgba(255,77,77,0.1); color: var(--neg); }
```
Requires So What box.

#### Ranking Bar Chart (Chart.js)
- `indexAxis: 'y'` (horizontal bars)
#WN|- Top bar (rank 1): `backgroundColor: '#00E273'` — all others: `'rgba(0,42,58,0.8)'`
- Add inline label after each bar via `afterDatasetsDraw` plugin
- Container: `flex: 1; position: relative; min-height: 0`
- **Init with `setTimeout(initChart, 60)` when slide becomes active**
Requires So What box.

#### 2×2 Matrix Chart (Chart.js scatter)
- 4 datasets (Stars=green, Cash Cows=blue, Question Marks=amber, Dogs=red)
- Quadrant divider lines via `beforeDraw` plugin (dashed `rgba(255,255,255,0.1)`)
- Quadrant label text (STARS/DOGS etc.) in `globalAlpha: 0.2`
- Point labels via `afterDatasetsDraw` plugin
- **Init with `setTimeout(initChart, 60)` when slide becomes active**
Requires So What box.

#### Recommendation Cards (LIGHT mode)
```css
.rec-card {
  background: #FFFFFF;
  border-radius: 14px;
  padding: 28px 32px;
  display: flex;
  align-items: center;
  gap: 28px;
  border-left: 3px solid var(--accent);    /* left accent — Nauda pattern */
  border-top: 1px solid rgba(0,42,58,0.08);
  border-right: 1px solid rgba(0,42,58,0.08);
  border-bottom: 1px solid rgba(0,42,58,0.08);
}
.rec-num {
  font-size: 72px;
  font-weight: 800;
  color: var(--accent);                    /* ⚠️ MUST be accent color */
  width: 100px;
  flex-shrink: 0;
  text-align: center;
}
.rec-title { color: #1A202C; font-weight: 600; }
.rec-body  { color: #4A5568; font-size: 14px; }
```
No So What box (Recommendation is already a conclusion).

#### Next Steps Timeline (DARK mode — closing highlight)
```html
<div class="timeline-track">
  <div class="timeline-line"></div>   <!-- horizontal line behind dots -->
  <div class="timeline-items">       <!-- 4-column grid -->
    <div class="timeline-item">
      <div class="timeline-dot"></div>  <!-- green circle on the line -->
      <div class="timeline-action">Action text</div>
      <div class="timeline-owner">Owner Name</div>
      <div class="timeline-due">5 Mar 2026</div>
      <span class="badge-pending">Pending</span>
    </div>
    <!-- repeat × 4 -->
  </div>
</div>
```
```css
.timeline-track  { position: relative; width: 100%; padding: 0 40px; }
.timeline-line   { position: absolute; top: 8px; left: 80px; right: 80px; height: 2px; background: rgba(255,255,255,0.12); }
.timeline-items  { display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px; position: relative; }
.timeline-item   { display: flex; flex-direction: column; align-items: center; text-align: center; }
.timeline-dot    { width: 16px; height: 16px; border-radius: 50%; background: var(--accent); border: 3px solid var(--base); box-shadow: 0 0 0 2px rgba(0,226,115,0.25); margin-bottom: 24px; z-index: 2; }
.timeline-due    { color: var(--accent); font-weight: 600; font-size: 12px; }
.badge-pending   { background: rgba(255,184,0,0.12); color: var(--warn); }
.badge-planned   { background: rgba(255,255,255,0.07); color: var(--muted); }
```
No So What box (action list is self-evident).

### §10.10 So What Box (Required on Slides 3–6 — Never on 1, 2, 7, 8)

So What box works on BOTH light and dark slides — same green border, different text color.

```css
/* On LIGHT slides (content slides — default) */
.so-what {
  background: rgba(0,226,115,0.06);  /* very subtle green tint on white */
  border-left: 4px solid var(--accent);
  padding: 14px 20px;
  border-radius: 0 8px 8px 0;
  margin-top: auto;               /* pushes to bottom of flex column */
}
.so-what-label {
  font-size: 10px; font-weight: 700;
  letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--accent); margin-bottom: 6px;
}
.so-what-text { font-size: 14px; color: #1A202C; line-height: 1.55; }

/* On DARK slides (if So What box needed on a dark slide) */
.so-what.dark { background: rgba(0,226,115,0.08); }
.so-what.dark .so-what-text { color: rgba(255,255,255,0.85); }
```

### §10.11 Vercel Deployment

```bash
# Get token
VERCEL_TOKEN=$(grep VERCEL_TOKEN ~/.openclaw/workspace/.env | cut -d= -f2)

# Deploy (MUST be a directory — single-file deployment no longer supported)
mkdir -p /tmp/eos-deck-deploy
cp /path/to/deck.html /tmp/eos-deck-deploy/index.html
cd /tmp/eos-deck-deploy
vercel --token $VERCEL_TOKEN --yes --prod --name [project-slug] 2>&1 | tail -5

# Returns: "Aliased: https://[project-slug].vercel.app"
```

⚠️ If `vercel` not in PATH, use full path: `~/homebrew/lib/node_modules/vercel/dist/index.js`

### §10.12 Known Bugs & Their Fixes

| Bug | Root Cause | Fix |
|---|---|---|
| Slide fade doesn't animate | `display:none` can't transition | Use `visibility:hidden + opacity:0` instead |
| Chart renders invisible (0px height) | Canvas has no height when parent is `display:none` | Use `setTimeout(initChart, 60)` + `position:absolute` slides (always display:flex) |
| Action numbers invisible | Dark color on dark bg: `text-[#083347]` on `#0A3D50` | Always use `var(--accent)` (#00E273) for decorative numbers |
| Chart not responsive | Missing `maintainAspectRatio: false` | Always set `responsive: true, maintainAspectRatio: false` |
| Click-on-dot advances slide twice | Dot click + body click both fire | Exclude `.dot` in body click handler: `!e.target.closest('a, button, canvas')` |

### §10.13 Full Working Reference

#PK|**Validated working deck:** `/Users/database-zuma/.openclaw/workspace-eos-nanobot/outbox/bm-jatim-GOLDEN-REFERENCE.html`
#BY|**Live URL:** https://bm-jatim.vercel.app
#ZT|**Date validated:** 2026-02-25
**All 8 slides reviewed:** Cover ✅ Exec Summary ✅ KPI ✅ Traffic Light Table ✅ Ranking Bar ✅ 2×2 Matrix ✅ Recommendations ✅ Timeline ✅

When building a new deck, **copy the CSS from this file as your starting point**. Replace slide content. Do not reinvent the architecture.
