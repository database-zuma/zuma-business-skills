---
name: zuma-ppt-design
description: Professional presentation design guidelines for Zuma Indonesia. KBI Finance Report-inspired layout with Zuma brand colors (Teal #002A3A + Green #00E273). Modern, data-focused, clean composition.
---

# Zuma PPT Design Guidelines

**Style Inspiration:** Korea Banking Institute Finance Report layout
**Brand Colors:** Zuma Teal #002A3A + Zuma Green #00E273
**Tone:** Modern, professional, data-driven

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

---

## Usage

When generating PPT for Zuma Indonesia:
1. Read this SKILL.md for design guidelines
2. Use Zuma colors (Teal + Green, NOT other palettes)
3. Follow KBI-inspired layout principles (grid, white space, data focus)
4. Adapt chart types to fit data (don't force exact KBI charts)
5. Maintain brand consistency across all slides
6. Output: 16:9 ratio, professional quality, A4-printable

**Tools:**
- **Primary:** python-pptx for generation, gog CLI for Google Drive upload
- **Alternative:** HTML deck + Vercel deployment (when python-pptx fails or web output preferred)

**Quality Bar:** Corporate presentation-ready, CEO-level audience
