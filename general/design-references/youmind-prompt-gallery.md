# YouMind — Nano Banana Pro Prompt Gallery

> Source: https://youmind.com/nano-banana-pro-prompts
> Scraped: 2026-02-21
> Purpose: Design reference for Eos, Codex, and sub-agents

---

## Website Visual Style

### Color Palette
| Role | Color | Hex |
|------|-------|-----|
| Primary (CTA) | Warm Yellow | `#FFE66D` |
| Accent / Links | Coral Red | `#FF6B6B` |
| Background | Light Gray | `#F0F0F0` |
| Text Primary | Black | `#000000` |
| Button Secondary | Black + Gray Shadow | `#000000` with `rgb(128,128,128) 2px 2px 0px 0px` |

### Typography
| Element | Font | Size |
|---------|------|------|
| Heading | Cereal (fallback: system-ui) | 72px (h1), 30px (h2) |
| Body | Inter (fallback: system-ui) | 16px |
| CJK Fallback | Microsoft YaHei, PingFang SC, Source Han Sans SC, Noto Sans SC | — |

### Design System
- **Framework:** Tailwind CSS
- **Border Radius:** 4px (sharp, minimal rounding)
- **Spacing Base Unit:** 4px
- **Tone:** Playful, high energy
- **Target Audience:** Creative professionals & hobbyists
- **Buttons:** Flat, no border-radius (0px all corners). Primary = yellow bg + black text + black border. Secondary = black bg + white text + offset gray shadow (brutalist style).

### Visual Identity Notes
- Brutalist-meets-playful aesthetic — sharp edges, bold colors, no soft gradients
- Yellow + coral as accent duo creates energetic, creative feel
- Shadow on secondary buttons is a brutalist design pattern (offset solid shadow instead of soft box-shadow)
- Good reference for: creative tool UIs, gallery layouts, prompt builder interfaces

---

## Prompt Engineering Patterns

### Pattern 1: Parameterized Templates (Reusable Prompts)
Use variable substitution for reusable prompts:
```
{argument name="quote" default="Stay hungry, stay foolish"}
{argument name="style" default="watercolor"}
{argument name="aspect_ratio" default="16:9"}
```
**Use case for Iris:** Build nanobot instruction templates with dynamic fields. Instead of writing a new prompt per task, swap variables.

### Pattern 2: Conditional Branching (Context-Aware Output)
Single prompt, different output based on input category:
```
IF product_type == "Food":
  → Show: Calories, Carbs, Protein per 100g
  → Style: Warm tones, appetizing lighting
IF product_type == "Medicine":
  → Show: Dosage, Interactions, Active ingredients
  → Style: Clinical, trust-building blues/whites
IF product_type == "Tech":
  → Show: Specs, Benchmarks, Compatibility
  → Style: Dark mode, neon accents, futuristic
```
**Use case for Eos:** Slide templates that auto-adapt to content type (sales deck vs operational report vs product launch).

### Pattern 3: Multi-Step Reasoning Chain
Force structured thinking before generation:
```
Step 1: Product Analysis → extract key attributes
Step 2: Color Palette → derive hero color from product image/brand
Step 3: Visual Style → match palette to design language
Step 4: Module Content → fill each card/section with data
Step 5: Composition → arrange into final layout
```
**Use case for Pipeline:** Matches Pattern A (Argus data → Eos render). Each step has clear input/output.

### Pattern 4: Precise Layout Control
Specify exact proportions and composition:
```
Layout: Bento Grid (8 modules)
- Hero image: 28-30% of total area
- Info section: 70-72% of total area
- Module grid: 2x4 or 3x3, 8px gap
- Card corners: 12px radius
- Padding: 16px inner, 24px outer
```
**Use case for Eos:** HTML deck slides with pixel-perfect layouts.

### Pattern 5: Photography/Rendering Specs
Control visual quality with camera-like parameters:
```
Camera: 85mm f/1.4
Lighting: Soft key light (5500K), fill at 2:1 ratio
Depth of Field: Shallow, subject sharp, background bokeh
Color Grade: Desaturated shadows, warm highlights (+10 orange)
Post: Subtle grain (ISO 400 simulation), slight vignette
```
**Use case for Eos:** Image generation prompts, product photography mockups.

### Pattern 6: Color Palette Derivation
Auto-generate complementary palettes from a seed:
```
1. Extract hero color from product/brand
2. Generate triadic palette (120° rotation on color wheel)
3. Set saturation: primary 100%, secondary 70%, tertiary 40%
4. Derive neutral: desaturate primary to 5%, use as card bg
5. Text: auto-contrast (WCAG AA minimum)
```
**Use case for Eos:** Auto-theming slides based on brand colors without manual design.

---

## Prompt Taxonomy (9,602 prompts organized by)

### Use Cases (10)
Profile/Avatar, Social Media Post, Infographic/Edu Visual, YouTube Thumbnail, Comic/Storyboard, Product Marketing, E-commerce Main Image, Game Asset, Poster/Flyer, App/Web Design

### Styles (16)
Photography, Cinematic/Film Still, Anime/Manga, Illustration, Sketch/Line Art, Comic/Graphic Novel, 3D Render, Chibi/Q-Style, Isometric, Pixel Art, Oil Painting, Watercolor, Ink/Chinese Style, Retro/Vintage, Cyberpunk/Sci-Fi, Minimalism

### Subjects (15)
Portrait/Selfie, Influencer/Model, Character, Group/Couple, Product, Food/Drink, Fashion Item, Animal/Creature, Vehicle, Architecture/Interior, Landscape/Nature, Cityscape/Street, Diagram/Chart, Text/Typography, Abstract/Background

---

## Resources
- **Web Gallery (searchable):** https://youmind.com/en-US/nano-banana-pro-prompts
- **GitHub Repo:** https://github.com/YouMind-OpenLab/awesome-nano-banana-pro-prompts
- **Prompt Recommender Skill:** https://github.com/YouMind-OpenLab/nano-banana-pro-prompts-recommend-skill
- **License:** CC BY 4.0 (free to reuse)
