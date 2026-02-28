---
name: zuma-ppt-design
description: Professional presentation design for Zuma Indonesia. frontend-slides visual system with Zuma brand colors (#002A3A teal, #00E273 green). 12 curated style presets, distinctive typography, animated HTML decks, Vercel deployment. Modern, expressive — NOT McKinsey/KBI Financial Report.
---

# Zuma PPT Design Guidelines

**Visual System:** frontend-slides (https://github.com/zarazhangrui/frontend-slides)
**Brand Colors:** Zuma Teal `#002A3A` + Zuma Green `#00E273`
**Tone:** Distinctive, expressive, modern — explicitly NOT generic AI slop

> 📁 **Role-specific deck references:** `zuma-business-skills/references/decks.md`

---

## ⚠️ MANDATORY: Start from TEMPLATE.html

**CRITICAL RULE:** ALL presentations MUST start from `TEMPLATE.html` in this folder.

**Workflow:**
1. Copy `TEMPLATE.html` to new project folder
2. Replace content — KEEP viewport fitting structure
3. Add/remove slides — COPY slide patterns from template
4. Deploy to Vercel

**DO NOT create HTML from scratch.** Always start from template.

**Location:** `/Users/database-zuma/.openclaw/workspace/zuma-business-skills/general/zuma-ppt-design/TEMPLATE.html`

---

## Color Palette

### Primary Brand Colors
- **Zuma Teal (Dark):** `#002A3A` — dark backgrounds, header bands, card fills on dark slides
- **Zuma Green (Bright):** `#00E273` — accents, CTAs, positive indicators, highlights

### Supporting Colors
- **Dark Base:** `#1A1A1A` — dark slide backgrounds
- **White:** `#FFFFFF` — light slide backgrounds, text on dark
- **Card Alt:** `#0A3D50` — secondary cards on dark backgrounds
- **Text Dark:** `#1A202C` — body text on light slides
- **Text Secondary:** `#4A5568` — labels on light slides
- **Text Muted:** `#718096` — captions on light slides
- **Text On Dark:** `#8CA3AD` — labels on dark slides
- **Red (negative):** `#FF4D4D`
- **Amber (warning):** `#FFB800`

### Color Rule in Style Presets
When adapting frontend-slides presets:
- All **dark accent colors** → `#002A3A` (Zuma Teal)
- All **bright accent colors** → `#00E273` (Zuma Green)
- Keep font pairings and layout patterns exactly as in preset

---

## ⚠️ CRITICAL: Viewport Fitting (Non-Negotiable)

**Every slide MUST fit exactly in the viewport. No scrolling within slides, ever.**

### Content Density Limits

| Slide Type | Maximum Content |
|------------|-----------------|
| Title slide | 1 heading + 1 subtitle |
| Content slide | 1 heading + 4-6 bullets (max 2 lines each) |
| Feature grid | 1 heading + 6 cards (2×3 or 3×2) |
| Code slide | 1 heading + 8-10 lines of code |
| Quote slide | 1 quote (max 3 lines) + attribution |

**Too much content? → Split into multiple slides. NEVER scroll.**

### Mandatory Viewport CSS (Include in ALL Presentations)

```css
/* ===========================================
   VIEWPORT FITTING — MANDATORY
   Copy into every presentation
   =========================================== */

html, body {
    height: 100%;
    overflow-x: hidden;
}

html {
    scroll-snap-type: y mandatory;
    scroll-behavior: smooth;
}

.slide {
    width: 100vw;
    height: 100vh;
    height: 100dvh; /* Dynamic viewport height for mobile */
    overflow: hidden; /* CRITICAL: No overflow ever */
    scroll-snap-align: start;
    display: flex;
    flex-direction: column;
    position: relative;
}

.slide-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    max-height: 100%;
    overflow: hidden;
    padding: var(--slide-padding);
}

:root {
    --title-size: clamp(1.5rem, 5vw, 4rem);
    --h2-size: clamp(1.25rem, 3.5vw, 2.5rem);
    --body-size: clamp(0.75rem, 1.5vw, 1.125rem);
    --small-size: clamp(0.65rem, 1vw, 0.875rem);
    --slide-padding: clamp(1rem, 4vw, 4rem);
    --content-gap: clamp(0.5rem, 2vw, 2rem);
}

.card, .container {
    max-width: min(90vw, 1000px);
    max-height: min(80vh, 700px);
}

img {
    max-width: 100%;
    max-height: min(50vh, 400px);
    object-fit: contain;
}

.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 220px), 1fr));
    gap: clamp(0.5rem, 1.5vw, 1rem);
}

@media (max-height: 700px) {
    :root {
        --slide-padding: clamp(0.75rem, 3vw, 2rem);
        --content-gap: clamp(0.4rem, 1.5vw, 1rem);
        --title-size: clamp(1.25rem, 4.5vw, 2.5rem);
    }
}

@media (max-height: 600px) {
    :root {
        --slide-padding: clamp(0.5rem, 2.5vw, 1.5rem);
        --title-size: clamp(1.1rem, 4vw, 2rem);
        --body-size: clamp(0.7rem, 1.2vw, 0.95rem);
    }
    .nav-dots, .keyboard-hint, .decorative { display: none; }
}

@media (max-height: 500px) {
    :root {
        --slide-padding: clamp(0.4rem, 2vw, 1rem);
        --title-size: clamp(1rem, 3.5vw, 1.5rem);
        --body-size: clamp(0.65rem, 1vw, 0.85rem);
    }
}

@media (max-width: 600px) {
    .grid { grid-template-columns: 1fr; }
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        transition-duration: 0.2s !important;
    }
}
```

### ⚠️ CSS Gotcha — Negating CSS Functions

**WRONG — silently ignored by browsers, no console error:**
```css
right: -clamp(28px, 3.5vw, 44px);   /* ❌ Browser discards this */
margin-left: -min(10vw, 100px);      /* ❌ Browser discards this */
```

**CORRECT — always wrap in calc():**
```css
right: calc(-1 * clamp(28px, 3.5vw, 44px));  /* ✅ */
margin-left: calc(-1 * min(10vw, 100px));     /* ✅ */
```

**Rule: ALWAYS use `calc(-1 * ...)` to negate CSS function values.**

---

## Style System — 12 Curated Presets

All 12 presets from frontend-slides, adapted with Zuma colors. Accent colors replaced:
- Dark accent → `#002A3A` (Zuma Teal)
- Bright accent → `#00E273` (Zuma Green)

Font pairings and layout patterns preserved exactly.

### Style Selection Guide

| Scenario | Recommended Preset |
|---|---|
| Executive pitch, keynote | **Bold Signal** |
| Agency/client presentation | **Electric Studio** |
| Creative product pitch | **Creative Voltage** |
| Premium brand review | **Dark Botanical** |
| Reports, editorial decks | **Notebook Tabs** |
| Product overviews, friendly | **Pastel Geometry** |
| Creative agencies, playful | **Split Pastel** |
| Personal brand, witty | **Vintage Editorial** |
| Tech products, startups | **Neon Cyber** |
| Dev tools, APIs | **Terminal Green** |
| Corporate, data-heavy | **Swiss Modern** |
| Storytelling, narrative | **Paper & Ink** |

---

### Preset 1: Bold Signal

**Vibe:** Confident, high-impact, bold — for keynotes and pitch decks

**Typography:**
- Display: `Archivo Black` (900)
- Body: `Space Grotesk` (400/500)

```css
:root {
    --bg-primary: #1a1a1a;
    --bg-gradient: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 50%, #1a1a1a 100%);
    --card-bg: #002A3A;           /* Zuma Teal replaces original orange */
    --accent: #00E273;            /* Zuma Green */
    --text-primary: #ffffff;
    --text-on-card: #00E273;
}
```

**Font import:**
```html
<link href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Space+Grotesk:wght@400;500&display=swap" rel="stylesheet">
```

**Signature:**
- Bold colored card as focal point (Zuma Teal background, Green text)
- Large section numbers (01, 02, 03…)
- Navigation breadcrumbs with opacity states
- Grid-based layout for precision

---

### Preset 2: Electric Studio

**Vibe:** Clean, professional, high contrast — agency presentations

**Typography:**
- Display: `Manrope` (800)
- Body: `Manrope` (400/500)

```css
:root {
    --bg-dark: #0a0a0a;
    --bg-white: #ffffff;
    --accent-blue: #002A3A;       /* Zuma Teal replaces blue */
    --accent-green: #00E273;      /* Zuma Green */
    --text-dark: #0a0a0a;
    --text-light: #ffffff;
}
```

**Font import:**
```html
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;800&display=swap" rel="stylesheet">
```

**Signature:**
- Two-panel vertical split (dark + light)
- Accent bar on panel edge using `#00E273`
- Quote typography as hero element
- Minimal, confident spacing

---

### Preset 3: Creative Voltage

**Vibe:** Bold, energetic, retro-modern — creative pitches

**Typography:**
- Display: `Syne` (700/800)
- Mono: `Space Mono` (400/700)

```css
:root {
    --bg-primary: #002A3A;        /* Zuma Teal replaces electric blue */
    --bg-dark: #0a0a14;
    --accent-neon: #00E273;       /* Zuma Green replaces neon yellow */
    --text-light: #ffffff;
}
```

**Font import:**
```html
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
```

**Signature:**
- Teal + Green high contrast split
- Halftone texture patterns
- Neon Green badges/callouts
- Script typography for creative flair

---

### Preset 4: Dark Botanical

**Vibe:** Elegant, sophisticated, artistic — premium brand reviews

**Typography:**
- Display: `Cormorant` (400/600) — elegant serif
- Body: `IBM Plex Sans` (300/400)

```css
:root {
    --bg-primary: #0f0f0f;
    --text-primary: #e8e4df;
    --text-secondary: #9a9590;
    --accent-warm: #002A3A;       /* Zuma Teal as warm accent */
    --accent-bright: #00E273;     /* Zuma Green as bright accent */
    --accent-gold: #8CA3AD;       /* Muted teal-gray */
}
```

**Font import:**
```html
<link href="https://fonts.googleapis.com/css2?family=Cormorant:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Sans:wght@300;400&display=swap" rel="stylesheet">
```

**Signature:**
- Abstract soft gradient circles (blurred, overlapping) in `#002A3A`
- `#00E273` accent lines (thin, vertical)
- Italic signature typography
- No illustrations — only abstract CSS shapes

---

### Preset 5: Notebook Tabs

**Vibe:** Editorial, organized, tactile — reports, structured decks

**Typography:**
- Display: `Bodoni Moda` (400/700) — classic editorial
- Body: `DM Sans` (400/500)

```css
:root {
    --bg-outer: #002A3A;          /* Zuma Teal as outer frame */
    --bg-page: #f8f6f1;           /* Cream paper */
    --text-primary: #1a1a1a;
    --tab-1: #00E273;             /* Zuma Green as primary tab */
    --tab-2: #8CA3AD;             /* Muted teal */
    --tab-3: #0A3D50;
    --tab-4: #004D5C;
    --tab-5: #002A3A;
}
```

**Font import:**
```html
<link href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:wght@400;700&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet">
```

**Signature:**
- Cream paper container with subtle shadow on Teal dark outer
- Teal/Green section tabs on right edge (vertical text)
- Tab text: `font-size: clamp(0.5rem, 1vh, 0.7rem)` (MUST scale)
- Binder hole decorations on left

---

### Preset 6: Pastel Geometry

**Vibe:** Friendly, approachable, modern — product overviews

**Typography:**
- Display: `Plus Jakarta Sans` (700/800)
- Body: `Plus Jakarta Sans` (400/500)

```css
:root {
    --bg-primary: #002A3A;        /* Zuma Teal as outer */
    --card-bg: #faf9f7;
    --pill-1: #00E273;            /* Zuma Green */
    --pill-2: #8CA3AD;
    --pill-3: #0A3D50;
    --pill-4: #004D5C;
    --pill-5: #002A3A;
}
```

**Font import:**
```html
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;700;800&display=swap" rel="stylesheet">
```

**Signature:**
- Rounded card with soft shadow on Teal background
- **Vertical pills on right edge** — varying heights (short→medium→tall→medium→short)
- Download/action icon corner using `#00E273`

---

### Preset 7: Split Pastel

**Vibe:** Playful, modern, friendly — creative agencies

**Typography:**
- Display: `Outfit` (700/800)
- Body: `Outfit` (400/500)

```css
:root {
    --bg-left: #002A3A;           /* Zuma Teal replaces peach */
    --bg-right: #0A3D50;          /* Teal alt replaces lavender */
    --text-on-dark: #ffffff;
    --badge-1: #00E273;           /* Zuma Green badge */
    --badge-2: rgba(0,226,115,0.3);
    --badge-3: rgba(0,226,115,0.15);
}
```

**Font import:**
```html
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;700;800&display=swap" rel="stylesheet">
```

**Signature:**
- Split background (Teal + Teal Alt)
- `#00E273` badge pills with icons
- Grid pattern overlay on right panel
- Rounded CTA buttons in Green

---

### Preset 8: Vintage Editorial

**Vibe:** Witty, editorial, personality-driven — personal brand, storytelling

**Typography:**
- Display: `Fraunces` (700/900) — distinctive serif
- Body: `Work Sans` (400/500)

```css
:root {
    --bg-cream: #f5f3ee;
    --text-primary: #1a1a1a;
    --text-secondary: #555;
    --accent: #002A3A;            /* Zuma Teal as warm accent */
    --highlight: #00E273;         /* Zuma Green for highlights */
}
```

**Font import:**
```html
<link href="https://fonts.googleapis.com/css2?family=Fraunces:wght@700;900&family=Work+Sans:wght@400;500&display=swap" rel="stylesheet">
```

**Signature:**
- Abstract geometric shapes in `#002A3A` (circle outline + line + dot)
- Bold bordered CTA boxes with `#00E273` fill
- Witty, conversational copy style
- No illustrations — geometric CSS shapes only

---

### Preset 9: Neon Cyber

**Vibe:** Futuristic, techy, confident — tech startups, SaaS

**Typography:**
- Display: `Clash Display` (Fontshare)
- Body: `Satoshi` (Fontshare)

```css
:root {
    --bg-primary: #0a0f1c;
    --accent-primary: #00E273;    /* Zuma Green replaces cyan */
    --accent-secondary: #002A3A;  /* Zuma Teal */
    --text-primary: #ffffff;
}
```

**Font import:**
```html
<link rel="stylesheet" href="https://api.fontshare.com/v2/css?f[]=clash-display@700&f[]=satoshi@400,500&display=swap">
```

**Signature:**
- Particle backgrounds (canvas)
- `#00E273` neon glow: `box-shadow: 0 0 20px rgba(0,226,115,0.4)`
- Grid patterns in `rgba(0,42,58,0.3)`
- Monospaced number accents

---

### Preset 10: Terminal Green

**Vibe:** Developer-focused, hacker aesthetic — dev tools, APIs, CLI apps

**Typography:**
- Display: `JetBrains Mono` (monospace only)
- Body: `JetBrains Mono`

```css
:root {
    --bg-primary: #0d1117;        /* GitHub dark */
    --accent: #00E273;            /* Zuma Green as terminal green */
    --text-primary: #ffffff;
    --text-secondary: #8CA3AD;
}
```

**Font import:**
```html
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
```

**Signature:**
- Scan lines effect with `rgba(0,226,115,0.03)` horizontal lines
- Blinking cursor `#00E273`
- Code syntax highlighting in Zuma Green
- ASCII-style borders

---

### Preset 11: Swiss Modern

**Vibe:** Clean, precise, Bauhaus-inspired — corporate, data-heavy

**Typography:**
- Display: `Archivo` (800)
- Body: `Nunito` (400)

```css
:root {
    --bg-primary: #ffffff;
    --bg-dark: #1a1a1a;
    --accent: #002A3A;            /* Zuma Teal replaces red */
    --accent-bright: #00E273;     /* Zuma Green */
    --text-primary: #000000;
}
```

**Font import:**
```html
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@800&family=Nunito:wght@400&display=swap" rel="stylesheet">
```

**Signature:**
- Visible grid system
- Asymmetric layouts with `#002A3A` geometric blocks
- `#00E273` rule lines
- Maximum whitespace, minimum decoration

---

### Preset 12: Paper & Ink

**Vibe:** Editorial, literary, thoughtful — storytelling decks, narrative reports

**Typography:**
- Display: `Cormorant Garamond` (serif)
- Body: `Source Serif 4`

```css
:root {
    --bg-cream: #faf9f7;
    --text-primary: #1a1a1a;
    --accent: #002A3A;            /* Zuma Teal as crimson equivalent */
    --highlight: #00E273;         /* Zuma Green for pull quotes */
}
```

**Font import:**
```html
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,600;1,400&family=Source+Serif+4:wght@400&display=swap" rel="stylesheet">
```

**Signature:**
- Drop caps in `#002A3A`
- Pull quotes with `#00E273` left border
- Elegant horizontal rules (`border-top: 1px solid #002A3A`)
- Literary spacing and margins

---

## Anti-AI-Slop Rules

**NEVER use these fonts as display fonts:**
- Inter, Roboto, Arial, system fonts

**NEVER use these colors/patterns:**
- `#6366f1` (generic indigo)
- Purple gradients on white
- Generic hero sections (centered logo + tagline + CTA button — only)
- Identical card grids with same height, same padding, same content type
- Everything centered (boring)

**INSTEAD use:**
- Distinctive font pairings from the 12 presets above
- Color themes with personality (Zuma Teal + Green has enough contrast to be distinctive)
- Atmospheric backgrounds (gradients, subtle patterns, depth)
- Asymmetric layouts, varied card sizes
- Signature animation moments

---

## Presentation Workflow

### Phase 1 — Content Discovery
Before designing, identify:
- Deck purpose (pitch / report / review / update)
- Target audience (CEO / BM / internal team / client)
- Slide count (5-10 short / 10-20 standard / 20+ deep dive)
- Content available (all ready / rough notes / topic only)

### Phase 2 — Style Selection
Choose preset based on context (see Style Selection Guide above).
If user wants to explore: generate 3 mini-preview HTML files in `.claude-design/slide-previews/`.

### Phase 3 — Generate
Build single HTML file. Apply selected preset's font + color system.
Apply Zuma color substitutions (dark accent → `#002A3A`, bright → `#00E273`).

### Phase 4 — Deploy to Vercel
See Deployment section below.

---

## Analytical Frameworks by Context

**Rule:** Pick framework based on the *type of question* being asked.

---

### 🛍️ Product Context → BCG Matrix + Product Life Cycle

**Use when:** Analyzing SKU performance, portfolio health, investment decisions.

**BCG Matrix** — classify articles by growth rate × sales volume:
| Quadrant | Criteria | Action |
|---|---|---|
| ⭐ Stars | High YoY growth + high volume | Invest, expand, ensure stock |
| 🐄 Cash Cows | Low/flat growth + high volume | Maintain, milk margin |
| ❓ Question Marks | High growth + low volume | Evaluate: scale up or cut? |
| 🐕 Dogs | Declining + low volume | Phase out or fix urgently |

**Axes:**
- X-axis: YTD volume = `SUM(now_jan_qty + now_feb_qty)`
- Y-axis: YoY same-period growth = `(ytd_now / ytd_last - 1) × 100`
- Bubble size: optional (stock, turnover)

---

### 🏪 Store Context → ABC Pareto + Growth × Revenue Matrix

**Use when:** Comparing store performance, prioritizing resources.

**ABC Pareto:**
- **A stores** (top 20% → ~80% revenue) → Full attention, premium assortment
- **B stores** (middle 50% → ~15% revenue) → Maintain, standard assortment
- **C stores** (bottom 30% → ~5% revenue) → Minimal investment, review viability

**Growth × Revenue Matrix:**
| Quadrant | Criteria | Action |
|---|---|---|
| ⭐ Star Stores | High YoY growth + high revenue | Invest, expand format |
| 🐄 Anchor Stores | Flat growth + high revenue | Protect, don't disrupt |
| 🌱 Rising Stores | High growth + low revenue | Nurture, increase assortment |
| ⚠️ At-Risk Stores | Declining + low revenue | Audit, restructure, or close |

---

### 💰 Finance Context → Revenue Bridge + Contribution Margin

**Use when:** Explaining why revenue changed, profitability analysis.

**Revenue Bridge (Waterfall Analysis):**
```
Revenue Change = Volume Effect + Price Effect + Mix Effect + New/Lost articles
```

**Contribution Margin per tier/store:**
```
Contribution Margin = Revenue - COGS - Direct selling costs
```

---

### 📐 Framework Selection Guide

| User's Question | Framework |
|---|---|
| "Artikel mana yang harus di-invest?" | BCG Matrix |
| "Kenapa artikel X declining?" | Product Life Cycle |
| "Toko mana yang performa paling bagus?" | ABC Pareto + Growth×Revenue |
| "Kenapa revenue bulan ini turun?" | Revenue Bridge (Waterfall) |
| "Toko mana yang actually profitable?" | Contribution Margin |
| "Strategi pertumbuhan Zuma ke mana?" | Ansoff Matrix |
| "Kompetitor environment kita?" | Porter's Five Forces |

---

## Narrative Structure & Data Storytelling

**Goal:** Transform descriptive data → compelling narrative with actionable insights

### Framework 1: SCQA (Situation-Complication-Question-Answer)

1. **Situation:** Where we are today (context, facts)
2. **Complication:** Problem/opportunity/tension (what's wrong?)
3. **Question:** What should we do about it?
4. **Answer:** Recommendation with rationale + data

**Key:** Open with complication (not situation) — grab attention immediately.

### Framework 2: Pyramid Principle (Barbara Minto)

- **Top:** Main conclusion/recommendation (answer first!)
- **Layer 1:** 3-4 key supporting arguments
- **Layer 2:** Data/evidence for each argument

**Golden rule:** Start with the answer, not the data.

**Headline examples:**
- ❌ "Top 20 SKU Performance" (topic)
- ✅ "Top 20 SKU face 80% decline — urgent product refresh needed" (conclusion)

### Framework 3: Narrative Arc

1. **Setup:** Where we are (brief context)
2. **Conflict:** What's wrong or at stake (tension is key!)
3. **Journey:** What we discovered in the data
4. **Resolution:** What we should do
5. **Call to Action:** Next steps with urgency

### Framework 4: SMART Recommendations

Every recommendation must be:
- **Specific:** Not "improve products" but "launch 10-15 new SKU in Men's & Baby"
- **Measurable:** "Recover Rp 500M revenue by Q3"
- **Achievable:** Within resource/time constraints
- **Relevant:** Addresses root cause identified
- **Time-bound:** "By end of Q2 2025"

---

## Deployment Workflow

### Option A: HTML Deck (Primary — MANDATORY default)

**Format 1: Slide-Based (Prev/Next Navigation)**
Reference: https://bm-jatim.vercel.app
Use for: Formal presentations, BM decks, executive reviews

```css
.slide { height: 100vh; width: 100%; display: none; }
.slide.active { display: flex; flex-direction: column; }
```

**Format 2: Scroll-Down (Card Layout)**
Reference: https://ladies-wedges-deck.vercel.app
Use for: Product analysis, detailed reports, content-heavy decks

```css
.deck { display: flex; flex-direction: column; gap: 2rem; }
.slide { aspect-ratio: 16/10; width: 100%; border-radius: 1rem; }
```

### Deploy to Vercel

```bash
# Setup
mkdir ~/Desktop/project-name-vercel
cp ~/Desktop/deck.html ~/Desktop/project-name-vercel/index.html

# Deploy (use full node + vercel path — 'vercel' not in PATH)
source ~/.openclaw/workspace/.env
cd ~/Desktop/project-name-vercel
~/homebrew/Cellar/node/25.6.0/bin/node \
  ~/homebrew/lib/node_modules/vercel/dist/index.js \
  --prod --yes --token "$VERCEL_TOKEN"
```

⚠️ `vercel` command not in $PATH on this machine. Always use full node + vercel paths above.

### Print to PDF

⚠️ **MANDATORY: Include `@media print` CSS in every deck.**

```css
@media print {
    @page { size: A4 landscape; margin: 0; }
    .slide { page-break-after: always; height: 190mm; overflow: hidden; }
    print-color-adjust: exact;
    .gradient-blob, #print-btn { display: none; }
}
```

User instructions:
- Open Vercel URL in Chrome
- Cmd+P → Background graphics: ✅ ON → Layout: Landscape → Margins: None → Save as PDF

### Option B: python-pptx (Only when .pptx explicitly requested)

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

ZUMA_TEAL = RGBColor(0, 42, 58)      # #002A3A
ZUMA_GREEN = RGBColor(0, 226, 115)    # #00E273
```

---

## Implementation Decision: Direct vs Delegate

### ✅ DIRECT CODING (write HTML directly):
- Single file HTML updates (content, layout, styling)
- Clear requirements
- Pure HTML + Tailwind CSS (no complex logic)
- Quick iterations

### ⚠️ DELEGATE TO OPENCODE/CLAUDE CODE:
- Multi-file projects (backend + frontend)
- Complex algorithms or calculations
- Python scripts with dependencies
- Database operations

---

## Standard Workflow

🚨 **CRITICAL: DEFAULT FOR ALL PPT REQUESTS** 🚨

1. Generate HTML deck (single file, chosen preset, Zuma colors)
2. Deploy to Vercel
3. Share permanent URL — NOT static file download

**ONLY use python-pptx if:**
- User explicitly requests .pptx file format
- HTML approach fails multiple times

**Quality bar:** Corporate presentation-ready, web-first, shareable, distinctive visual design that reflects Zuma brand personality.
