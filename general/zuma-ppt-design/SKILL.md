---
name: zuma-ppt-design
description: Professional presentation design guidelines for Zuma Indonesia. KBI Finance Report-inspired layout with Zuma brand colors (Teal #002A3A + Green #00E273). Modern, data-focused, clean composition.
---

# Zuma PPT Design Guidelines

**Style Inspiration:** Korea Banking Institute Finance Report layout
**Brand Colors:** Zuma Teal #002A3A + Zuma Green #00E273
**Tone:** Modern, professional, data-driven

---

## ⚠️ MANDATORY: Use Canonical Template (2026-02-17)

**CRITICAL RULE:** ALL presentations MUST start from `TEMPLATE.html` in this folder.

**Why:** Ensures visual consistency across all decks. Proven layout from "Zuma Performance Analysis" deck.

**Workflow:**
1. Copy `TEMPLATE.html` to new project folder
2. Replace content (titles, data, stats) — KEEP structure
3. Add/remove slides as needed — COPY slide patterns from template
4. Deploy to Vercel

**DO NOT create HTML from scratch.** Always start from template.

**Template Features:**
- Dark background (#1a1a1a) + white cards (.slide)
- Gradient blob accents
- Slide variants: `.slide`, `.slide-teal`, `.slide-red`, `.slide-green`
- Grid layouts for stats
- Proper spacing & typography
- Print-friendly CSS

**Location:** `/Users/database-zuma/.openclaw/workspace/zuma-business-skills/general/zuma-ppt-design/TEMPLATE.html`

---

## Color Palette

### Primary Colors
- **Zuma Teal (Dark):** `#002A3A` — Headers, primary backgrounds, emphasis
- **Zuma Green (Bright):** `#00E273` — Accents, highlights, success indicators, CTAs

### Supporting Colors
- **White:** `#FFFFFF` — Backgrounds, text on dark
- **Light Gray:** `#F5F7FA` — Alternate backgrounds, subtle sections
- **Dark Gray:** `#2C3E50` — Body text, secondary headers
- **Mid Gray:** `#7F8C8D` — Captions, metadata

### Gradients (Optional)
- Teal gradient: `#002A3A → #004D5C` (subtle depth)
- Green accent: Use sparingly for highlights/callouts

---

## Typography

**Font Family:** Sans-serif modern (Calibri, Arial, Montserrat, Open Sans)

**Hierarchy:**
1. **Hero Numbers:** 72-96pt, bold, Zuma Teal
2. **Section Titles:** 36-44pt, bold, ALL CAPS, Zuma Teal
3. **Slide Titles:** 28-32pt, bold, Zuma Teal
4. **Headers:** 18-20pt, semi-bold, Dark Gray
5. **Body Text:** 14-16pt, regular, Dark Gray
6. **Captions:** 10-12pt, regular, Mid Gray

**Style:**
- Bold headers for emphasis
- ALL CAPS for section dividers
- Regular weight for body/readability

---

## Layout Principles (KBI-Inspired)

### 1. Grid-Based Structure
- Most slides: **2-column layout** (60/40 or 50/50)
- Left: Text/context | Right: Visual/data
- Consistent alignment across slides

### 2. White Space
- **Generous margins** (min 1 inch all sides)
- Clear section breaks
- Don't overcrowd — breathable layouts
- Use white space to guide eye flow

### 3. Data-Focused Composition
- **Big numbers** as focal points (center or top-right)
- Charts integrated with text (not floating)
- Tables with Teal headers, white/light gray rows
- Mix visual types: avoid repetition

### 4. Visual Balance
- Align elements to grid
- Even spacing between sections
- Symmetry where appropriate
- Use contrast (dark Teal vs white) for drama

---

## Narrative Structure & Data Storytelling

**Goal:** Transform descriptive data → compelling narrative with actionable insights

**Critical:** Design beautiful slides ≠ effective presentation. Story first, visuals second.

---

### Framework 1: SCQA (Situation-Complication-Question-Answer)

**McKinsey/consulting standard structure:**

1. **Situation:** Where we are today (context, facts)
2. **Complication:** Problem/opportunity/tension (what's wrong?)
3. **Question:** What should we do about it?
4. **Answer:** Recommendation with rationale + data

**Application:**
- **Open with complication** (not situation) — grab attention
- **Every slide answers one question** in the Q→A flow
- **Tension is key** — no conflict = boring presentation

**Example:**
- ❌ "Zuma has 598 SKU across 6 branches" (situation, boring)
- ✅ "19 of top 20 SKU declining -70% YoY — revenue at risk" (complication, urgent)

---

### Framework 2: Pyramid Principle (Barbara Minto)

**Structure:**
- **Top:** Main conclusion/recommendation (answer first!)
- **Layer 1:** 3-4 key supporting arguments
- **Layer 2:** Data/evidence for each argument
- **Layer 3:** Detailed analysis (appendix)

**Golden rule:** Start with the answer, not the data.

**Slide application:**
- Headline = conclusion (not topic)
- Body = supporting evidence
- Footer = "So what?" implication

**Example headlines:**
- ❌ "Top 20 SKU Performance" (topic)
- ✅ "Top 20 SKU face 80% decline — urgent product refresh needed" (conclusion)

---

### Framework 3: Insight Hierarchy (Gartner Model)

**4 levels of analysis:**

1. **Descriptive:** What happened? (data reporting)
   - "Revenue is Rp 27.6B"
   - Charts, tables, metrics
   
2. **Diagnostic:** Why did it happen? (root cause)
   - "Revenue declining because of product lifecycle maturity + competition"
   - Analysis, comparisons, breakdowns
   
3. **Predictive:** What will happen? (forecast)
   - "If trend continues, we lose Rp 2.3B by Q4"
   - Scenarios, projections, trend lines
   
4. **Prescriptive:** What should we do? (action)
   - "Launch 10-15 new SKU per quarter to recover Rp 500M by Q3"
   - Recommendations, roadmap, metrics

**Most presentations fail at Diagnostic/Predictive/Prescriptive — they just report data (Descriptive).**

**Quality bar:** Every insight must answer "So what?" and progress through hierarchy.

---

### Framework 4: Narrative Arc for Business

**Classic story structure:**

1. **Setup:** Where we are (brief, establishes context)
2. **Conflict/Challenge:** What's wrong or at stake (tension!)
3. **Journey:** What we discovered in the data (insights)
4. **Resolution:** What we should do (recommendations)
5. **Call to action:** Next steps with urgency

**Critical:** Without conflict, presentation is flat. Find the "villain":
- Market threat
- Declining performance
- Missed opportunity
- Resource constraint

**Example narrative:**
- Setup: "Zuma operates 6 branches across Indonesia"
- Conflict: "But 19 of top 20 SKU declining -80% YoY — revenue collapsing"
- Journey: "We analyzed the data and found 3 patterns..."
- Resolution: "We can reverse decline with 3-play strategy"
- CTA: "Approve product pipeline by end of Q2"

---

### Best Practices: McKinsey Slide Structure

**Every slide must have:**

1. **Insight headline** (not topic title)
   - Answer "So what?" in the headline itself
   - Make it actionable/decision-oriented
   
2. **Supporting visual** (chart/table/diagram)
   - Data that proves the headline
   - Annotate key points
   
3. **Bottom-line implication** (1-2 sentences)
   - What this means for the business
   - Call to action or next question

**Example slide:**
```
[Headline] Top 20 SKU face 80% YoY decline — urgent product refresh needed

[Visual] Bar chart showing YoY decline by SKU
         - 19/20 declining
         - Avg decline -83%
         - Only 1 SKU growing (Merci +31%)

[Implication] Without new product pipeline, we risk Rp 2.3B revenue loss by Q4.
              Recommend launching 10-15 new SKU per quarter starting Q2.
```

---

### Actionable Recommendations: SMART Format

**Every recommendation must be:**

- **Specific:** Not "improve products" but "launch 10-15 new SKU in Men's & Baby"
- **Measurable:** "Recover Rp 500M revenue by Q3"
- **Achievable:** Within resource/time constraints
- **Relevant:** Addresses root cause identified
- **Time-bound:** "By end of Q2 2025"

**Template:**
1. **What:** The action (clear, specific)
2. **Why:** Rationale tied to insight (diagnostic)
3. **How:** Implementation approach (high-level)
4. **When:** Timeline with milestones
5. **Impact:** Expected outcome (quantified)
6. **Investment:** Resources needed (budget, headcount)
7. **Owner:** Who's accountable

---

### Common Pitfalls

**❌ Descriptive-only presentation:**
- Just shows data without interpretation
- "Revenue is X, Cost is Y, Profit is Z"
- Audience reaction: "So what?"

**❌ Missing "why" analysis:**
- Shows WHAT happened but not WHY
- "Sales declined 80%" → But why? Competition? Product? Market?

**❌ No forecast/projection:**
- Doesn't answer "What if we don't act?"
- No sense of urgency

**❌ Generic recommendations:**
- "Improve products", "Expand market", "Increase sales"
- Not specific, measurable, or time-bound

**❌ No prioritization:**
- Lists 10 recommendations without ranking
- Everything seems equally important = nothing is

**✅ Good presentation:**
- Answers WHY (diagnostic)
- Shows WHAT IF (predictive)
- Recommends WHAT TO DO (prescriptive)
- Quantifies everything (metrics, timelines, investment, ROI)
- Prioritizes actions (urgent vs important)
- Creates urgency (deadline, risk, opportunity cost)

---

### Quality Checklist

Before finalizing deck, verify:

- [ ] **Headline = insight** (not topic) on every slide
- [ ] **Story arc clear:** Setup → Conflict → Journey → Resolution → CTA
- [ ] **Diagnostic level:** WHY analysis included (not just WHAT)
- [ ] **Predictive level:** Forecast/scenario analysis (what if we don't act?)
- [ ] **Prescriptive level:** SMART recommendations with metrics
- [ ] **Quantified impact:** Investment, ROI, timeline for each recommendation
- [ ] **Prioritization:** Urgent vs important, sequenced roadmap
- [ ] **Risk mitigation:** What could go wrong? How do we address it?
- [ ] **Success criteria:** How do we measure progress?
- [ ] **Call to action:** Clear next steps with ownership + deadline

---

## Slide Templates

### Template 1: Title Slide
**Layout:**
- Full background: Zuma Teal (#002A3A) with subtle gradient
- Title: Large, white, left-aligned or centered
- Subtitle: Smaller, white or light gray
- Footer: Date, presenter, logo (small, bottom-right)

**Example:**
```
[Full Teal Background]

TITLE IN WHITE
72pt Bold

Subtitle or Context
28pt Regular

Date | Presenter | Small Zuma logo
```

### Template 2: Section Divider
**Layout:**
- 50% Teal (#002A3A) | 50% White
- Section title: ALL CAPS, white on Teal side
- Optional: Green accent line on white side

**Example:**
```
[Left 50%: Teal]        [Right 50%: White]
SECTION TITLE           [Green accent bar]
ALL CAPS WHITE
```

### Template 3: Data Slide (2-Column)
**Layout:**
- Left (40%): Context, headline, key takeaway
- Right (60%): Chart/visual
- Header: Slide title (Teal, top)

**Example:**
```
SLIDE TITLE (Teal, 32pt)

[Left Column]           [Right Column]
Key Insight Text        [Chart/Graph]
Supporting details      - Blue bars
Call-to-action          - Green highlights
                        - Clean axes
```

### Template 4: Metrics Highlight
**Layout:**
- Hero number: Center or top-right, huge (72-96pt), Teal
- Context below: What the number means
- Optional: Comparison (YoY, vs target) in Green

**Example:**
```
METRIC TITLE

       194,498
       [Teal, 96pt Bold]

Description of metric
+25% YoY [Green accent]
```

### Template 5: Table + Insight
**Layout:**
- Top: Brief intro/headline
- Middle: Clean table (Teal header, white rows, borders)
- Bottom: Key insight or action item

**Example:**
```
TABLE TITLE

[Table]
| Header 1 [Teal bg] | Header 2 | Header 3 |
| Data row 1         | ...      | ...      |
| Data row 2         | ...      | ...      |

→ Key Insight: [Green arrow] Brief takeaway
```

---

## Visual Guidelines

### ⚠️ IMPORTANT: Match Visuals to Content

**Use charts ONLY when presenting data/metrics.**
**Use flowcharts/diagrams for processes/workflows/concepts.**

Don't force charts where they don't belong!

### Data Visualization (Charts)
Use when presenting: sales numbers, performance metrics, comparisons, trends

- **Bar Charts:** Solid Teal bars, Green for highlights/comparison
- **Line Charts:** Teal primary line, Green secondary/target line
- **Area Charts:** Teal fill with gradient (semi-transparent)
- **Pie/Donut:** Teal shades (light to dark), Green for key segment
- **Tables:** Teal header row, alternating white/light gray rows

### Process Visualization (Flowcharts/Diagrams)
Use when presenting: workflows, decision trees, system architecture, timelines

- **Flowcharts:** Teal boxes/shapes, Green arrows for flow, white text
- **Timelines:** Horizontal with Teal milestones, Green current phase
- **Org Charts:** Teal header boxes, white/light gray sub-boxes
- **Decision Trees:** Teal decision nodes, Green paths
- **Process Flows:** Simple boxes + arrows (Teal/Green palette)

### Chart Styling
- **Clean axes** (no heavy borders)
- **Minimal gridlines** (light gray, subtle)
- **Data labels** where helpful (not cluttered)
- **Legends** simple (top-right or bottom)
- **Consistent colors** across all charts

### Avoid
- 3D effects
- Drop shadows (unless very subtle)
- Overly decorative elements
- Chart junk (excessive borders, backgrounds)
- **Forcing charts when content is conceptual** (use flowcharts instead)

---

## Do's & Don'ts

### ✅ DO
- Use Teal for authority, Green for highlights
- Keep white space generous
- Align everything to grid
- Use big numbers for impact
- **Match visuals to content** (charts for data, flowcharts for processes)
- Mix visual types for variety (when appropriate)
- Stay consistent with typography
- Use gradients sparingly (Teal only)

### ❌ DON'T
- Mix too many colors (stick to Teal + Green palette)
- Crowd slides (less is more)
- Use decorative fonts
- Add random shapes/icons
- Make text too small (<14pt body)
- Center-align body text (left-align for readability)
- Use animations (unless specifically requested)

---

## Implementation (python-pptx)

### Key Libraries
```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
```

### Color Definitions
```python
ZUMA_TEAL = RGBColor(0, 42, 58)      # #002A3A
ZUMA_GREEN = RGBColor(0, 226, 115)    # #00E273
WHITE = RGBColor(255, 255, 255)
LIGHT_GRAY = RGBColor(245, 247, 250)
DARK_GRAY = RGBColor(44, 62, 80)
MID_GRAY = RGBColor(127, 140, 141)
```

### Slide Sizing
```python
prs = Presentation()
prs.slide_width = Inches(16)   # 16:9 aspect ratio
prs.slide_height = Inches(9)
```

### Typography Helper
```python
def set_text_format(text_frame, font_size, bold=False, color=DARK_GRAY, align=PP_ALIGN.LEFT):
    for paragraph in text_frame.paragraphs:
        paragraph.font.size = Pt(font_size)
        paragraph.font.bold = bold
        paragraph.font.color.rgb = color
        paragraph.alignment = align
```

---

## Reference Examples

**Style Inspiration:** KBI Finance Report (layout, composition, spacing)
**Brand Colors:** Zuma Teal #002A3A + Green #00E273
**Adaptability:** Chart types flex based on data (not exact replica)

**Key Elements from KBI to Adopt:**
- Grid-based 2-column layouts
- Big metric callouts
- Clean chart integration
- Generous white space
- Data-first composition

**Zuma Customizations:**
- Replace blue → Teal (#002A3A)
- Replace accent → Green (#00E273)
- Add Zuma logo/branding where appropriate
- Adjust charts to match data needs (not force KBI chart types)

---

## Alternative Approach: HTML Deck (Vercel)

**When to use:** When python-pptx struggles with complex layouts or user wants web-based deck

### Workflow

**1. Generate HTML Deck**
- Single HTML file with Tailwind CSS
- Swiss Style / Bold typography (Inter font)
- Grid-based card layouts (3-column for overview)
- Absolute positioning for precise element placement
- Zuma colors: Green #00E273 accent, Teal #002A3A text, off-white #F5F5F0 backgrounds

**2. Deploy to Vercel**
```bash
# Setup
mkdir ~/Desktop/project-name-vercel
cp ~/Desktop/deck.html ~/Desktop/project-name-vercel/index.html

# Deploy
cd ~/Desktop/project-name-vercel
export PATH=~/homebrew/bin:$PATH
export VERCEL_TOKEN=<from .env>
vercel --prod --yes
```

**3. Print to PDF (from web)**
- Open Vercel URL in browser
- Cmd+P (Print)
- Settings:
  - **Background graphics:** ON (CRITICAL!)
  - **Layout:** Landscape
  - **Margins:** None
  - **Scale:** 100%
  - **Paper size:** A4 or Letter
- Save as PDF

### Benefits
- ✅ Web-shareable link (permanent URL)
- ✅ Better print fidelity (browser render > headless Chrome)
- ✅ Interactive (scrollable, responsive)
- ✅ Easy iteration (re-deploy in seconds)
- ✅ No python-pptx layout struggles

### HTML Template Structure
```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');
        /* Custom styles with Zuma colors */
    </style>
</head>
<body class="bg-[#1a1a1a] p-10">
    <div class="max-w-7xl mx-auto grid grid-cols-3 gap-5">
        <!-- Slide cards -->
        <div class="bg-[#f5f5f0] rounded-2xl p-12 aspect-[16/10] relative">
            <!-- Content -->
        </div>
    </div>
</body>
</html>
```

### Reference
**Example:** RO Benchmark deck → https://ro-benchmark-vercel.vercel.app
**Style:** Swiss Design (bold Grotesk, high contrast, generous whitespace, grid system)
**Deployment date:** 2026-02-16
**Deployment time:** ~10 seconds (Vercel)

### ⚙️ Implementation Decision: Direct Coding vs Delegation

**✅ DIRECT CODING (Iris writes code herself):**
Use when task is simple and straightforward:
- Single file HTML updates (content, layout, styling)
- Clear requirements (add screenshot, change text to Bahasa, fix grid)
- Pure HTML + Tailwind CSS (no complex logic)
- Quick iterations (user feedback loop)
- **Speed advantage:** Write → deploy → done (no AI interpretation layer)

**Example tasks:**
- Update deck content (slide text, add images)
- Fix layout (grid → scrollable, responsive tweaks)
- Add Bahasa Indonesia translation
- Insert screenshots into existing slides

**⚠️ DELEGATE TO OPENCODE/CLAUDE CODE:**
Use when task requires exploration or complex logic:
- Multi-file projects (backend + frontend)
- Large codebases (need to explore structure)
- Complex algorithms or calculations
- Python scripts with dependencies/imports
- Database operations (multi-step queries, schema changes)
- **When python-pptx fails repeatedly:** Switch to direct HTML scripting

**Example tasks:**
- Full app development
- Data pipelines with error handling
- Interactive charts with libraries
- Backend API integration

**Rule of thumb:** Simple HTML/CSS = Direct (faster). Everything else = Delegate (leverage AI reasoning).

**Proven workflow (2026-02-16):**
- RO Benchmark deck updates: Direct coding → 3 iterations → 10 sec deploys ✓
- Complex PPT generation: OpenCode → multiple failures → switched to direct scripting ✓

---

## Usage

🚨 **CRITICAL: DEFAULT WORKFLOW FOR ALL PPT REQUESTS** 🚨

**When ANY user requests PPT/presentation:**
1. **Generate HTML deck** (single file with Tailwind CSS)
2. **Deploy to Vercel** (web-based, permanent URL)
3. **Share link** — NOT static file download

**Why HTML + Vercel is mandatory:**
- ✅ Web-shareable (permanent URL, accessible anywhere)
- ✅ Better print quality (user can print to PDF themselves)
- ✅ Fast iteration (re-deploy in 10 seconds)
- ✅ No python-pptx layout struggles
- ✅ Scrollable, responsive, modern UX

**ONLY use python-pptx if:**
- User explicitly requests .pptx file format
- Or: HTML approach fails multiple times

---

**Standard workflow:**

1. Read this SKILL.md for design guidelines
2. Use Zuma colors (Teal #002A3A + Green #00E273, NOT other palettes)
3. Follow KBI-inspired or Swiss Style layout principles
4. Generate HTML with Tailwind CSS (scrollable vertical slides)
5. Deploy to Vercel (`vercel --prod --yes`)
6. Share permanent URL

**Output specifications:**
- Format: Scrollable HTML (vertical 1-column layout)
- Responsive: Works on desktop/mobile/tablet
- Printable: User can Cmd+P → Save as PDF (with background graphics ON)
- Shareable: Permanent Vercel URL
- Professional quality: CEO-level audience ready

**Tools:**
- **Primary (MANDATORY):** HTML + Tailwind CSS → Vercel deployment
- **Fallback:** python-pptx → gog CLI for Google Drive upload (only when explicitly requested)

**Quality Bar:** Corporate presentation-ready, web-first, shareable
