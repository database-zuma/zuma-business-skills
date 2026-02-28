#!/usr/bin/env python3
"""
build_deck.py — Template-Locked Deck Builder for Zuma Presentations
====================================================================
TWO MODES — choose based on how structured the content is:

  Mode A (--content): Deterministic build from structured content JSON.
      Best for: standard decks with known data (sales reports, tier analysis).
      Eos generates content JSON → builder generates HTML.

  Mode B (--wrap): Shell wrapper around free-form Eos HTML.
      Best for: creative/custom decks, any content Eos wants.
      Eos writes slide <div> blocks + chart scripts → builder wraps with locked CSS.
      *** THIS IS THE PRIMARY/DEFAULT MODE ***

Both modes:
  - CSS/head from locked TEMPLATE.html (never touched by LLM)
  - Logo base64 auto-injected from file
  - IntersectionObserver always included
  - Print CSS, print button, gradient blobs always present
  - validate_deck.py runs as final QA gate

Usage:
    # Mode B — Wrap Eos's free-form HTML (PRIMARY)
    python3 build_deck.py --wrap eos-output.html --output deck.html --validate

    # Mode A — Build from structured content JSON
    python3 build_deck.py --content content.json --output deck.html --validate

    # Print schema for Mode A
    python3 build_deck.py --schema

Author: Claude Code (for Iris pipeline)
Version: 2.0 (2026-02-28) — Added --wrap mode for flexible content
"""

import argparse
import json
import os
import re
import sys
from html import escape

# ── PATHS ──
DEFAULT_TEMPLATE = os.path.expanduser(
    "~/.openclaw/workspace/zuma-business-skills/general/zuma-ppt-design/TEMPLATE.html"
)
LOGO_BASE64_PATH = "/tmp/zuma-logo-base64.txt"
LOGO_PNG_PATH = os.path.expanduser(
    "~/.openclaw/workspace/zuma-business-skills/general/zuma-ppt-design/assets/zuma-logo-white-200.png"
)


def load_logo_base64():
    """Load ZUMA logo base64 from file. Try txt first, then generate from PNG."""
    if os.path.exists(LOGO_BASE64_PATH):
        with open(LOGO_BASE64_PATH, "r") as f:
            b64 = f.read().strip()
        if len(b64) > 4000:
            return b64

    if os.path.exists(LOGO_PNG_PATH):
        import base64

        with open(LOGO_PNG_PATH, "rb") as f:
            png_data = f.read()
        return base64.b64encode(png_data).decode("ascii")

    print(
        "WARNING: Logo base64 not found. Cover/closing will have no logo.",
        file=sys.stderr,
    )
    return None


def extract_css_from_template(template_path):
    """Extract the <style> block from TEMPLATE.html."""
    if not os.path.exists(template_path):
        print(
            f"WARNING: Template not found at {template_path}, using built-in CSS.",
            file=sys.stderr,
        )
        return None

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    match = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
    if match:
        return match.group(1)
    return None


# ═══════════════════════════════════════════════════════════════
# MODE B: SHELL WRAPPER (PRIMARY MODE — flexible content)
# Eos writes slide body + chart scripts → we wrap with locked shell
# ═══════════════════════════════════════════════════════════════


def extract_body_content(raw_html):
    """Extract slide content from Eos's raw HTML output.

    Extracts:
      1. All <div class="slide..."> blocks (the visible slide content)
      2. Any <script> blocks containing Chart.js init code
      3. Title from <title> tag (if present)

    Discards:
      - <head>, <style>, CDN script tags (replaced by locked versions)
      - <!DOCTYPE>, <html>, <body> wrappers (replaced by locked shell)
    """
    # Extract title
    title_match = re.search(r"<title>(.*?)</title>", raw_html, re.DOTALL)
    title = title_match.group(1).strip() if title_match else "ZUMA Presentation"

    # Extract body content (between <body> and </body>)
    body_match = re.search(
        r"<body[^>]*>(.*?)</body>", raw_html, re.DOTALL | re.IGNORECASE
    )
    body = body_match.group(1) if body_match else raw_html

    # Extract inline <script> blocks that contain Chart.js code (NOT CDN references)
    # Keep scripts that have actual code (Chart init, IntersectionObserver, etc.)
    script_blocks = []
    for match in re.finditer(r"<script(?:\s[^>]*)?>(.*?)</script>", body, re.DOTALL):
        full_tag = match.group(0)
        script_content = match.group(1).strip()
        # Skip CDN script tags (they have src= attribute) and empty scripts
        if not script_content:
            continue
        # Skip if the <script> tag itself has a src= attribute (CDN reference)
        if re.match(r'<script\s+[^>]*src\s*=', full_tag, re.IGNORECASE):
            continue
        # Skip if content is just a CDN URL reference that somehow leaked inline
        if (
            "cdn.tailwindcss.com" in script_content
            and len(script_content) < 200
        ):
            continue
        script_blocks.append(script_content)

    # ── STRIP NAVIGATION CODE from scripts (BANNED overlay pattern) ──
    # Eos often mixes navigation JS with chart init in the same <script> block.
    # We strip lines containing overlay navigation patterns while keeping chart code.
    cleaned_scripts = []
    nav_patterns = re.compile(
        r'(let\s+cur\s*=|function\s+show\s*\(|function\s+nextSlide|function\s+prevSlide|'
        r'currentSlide|slideIndex|showSlide|nextSlide|prevSlide|'
        r'\.classList\.remove\(.*active|'
        r'\.classList\.add\(.*active|'
        r'ArrowRight.*nextSlide|ArrowLeft.*prevSlide|'
        r'getElementById.*counter.*textContent)',
        re.IGNORECASE
    )
    for script in script_blocks:
        # Split into lines, filter out navigation lines, rejoin
        lines = script.split('\n')
        kept = [line for line in lines if not nav_patterns.search(line)]
        cleaned = '\n'.join(kept).strip()
        if cleaned and len(cleaned) > 50:  # Only keep non-trivial scripts
            cleaned_scripts.append(cleaned)

    # Remove all <script> blocks from body (we'll re-inject the good ones)
    body_no_scripts = re.sub(
        r"<script(?:\s[^>]*)?>(.*?)</script>", "", body, flags=re.DOTALL
    )

    # Also remove any standalone <script src="..."></script> CDN tags
    body_no_scripts = re.sub(
        r'<script\s+src="[^"]*"[^>]*></script>', "", body_no_scripts
    )

    # Remove navigation HTML elements (prev/next buttons, nav divs)
    body_no_scripts = re.sub(
        r'<div\s+class="nav"[^>]*>.*?</div>', "", body_no_scripts, flags=re.DOTALL
    )
    # Also remove standalone nav buttons with onclick="prevSlide/nextSlide"
    body_no_scripts = re.sub(
        r'<button[^>]*onclick="(?:prev|next)Slide\(\)"[^>]*>.*?</button>',
        "", body_no_scripts, flags=re.DOTALL
    )

    # Remove stray <link>, <meta> tags that don't belong in body
    body_no_scripts = re.sub(r"<link\s[^>]*>", "", body_no_scripts)
    body_no_scripts = re.sub(r"<meta\s[^>]*>", "", body_no_scripts)

    # Clean up excessive whitespace but preserve structure
    body_clean = re.sub(r"\n{3,}", "\n\n", body_no_scripts).strip()

    return {
        "title": title,
        "body": body_clean,
        "scripts": cleaned_scripts,
    }


def inject_logo_if_missing(body_html, logo_b64):
    """If Eos output has no logo or truncated logo, inject the correct one."""
    if not logo_b64:
        return body_html

    # Check for existing base64 images
    existing = re.findall(r"data:image/png;base64,[A-Za-z0-9+/=]+", body_html)

    if not existing:
        # No logo at all — inject into first slide-dark (cover)
        # Find the first slide-dark's first child div
        cover_match = re.search(r'(<div\s+class="slide\s+slide-dark"[^>]*>)', body_html)
        if cover_match:
            logo_tag = f'\n        <img src="data:image/png;base64,{logo_b64}" alt="ZUMA" style="width:36px;height:36px;object-fit:contain;position:absolute;top:2rem;left:2rem;z-index:2;">'
            body_html = body_html.replace(
                cover_match.group(0),
                cover_match.group(0) + logo_tag,
                1,  # Only first match (cover)
            )
        return body_html

    # Check for truncated logos (< 4000 chars) and replace
    for existing_b64 in existing:
        if len(existing_b64) < 4000:
            # Truncated — replace with correct one
            body_html = body_html.replace(
                existing_b64, f"data:image/png;base64,{logo_b64}"
            )

    return body_html


def has_intersection_observer(scripts):
    """Check if any script block contains IntersectionObserver."""
    for s in scripts:
        if "IntersectionObserver" in s:
            return True
    return False


def build_locked_observer():
    """Generate the locked IntersectionObserver code."""
    return """
        // ── IntersectionObserver — lazy chart init on scroll (LOCKED) ──
        var chartObserver = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    var canvases = entry.target.querySelectorAll('canvas');
                    canvases.forEach(function(canvas) {
                        var initFn = 'initChart_' + canvas.id;
                        if (typeof window[initFn] === 'function' && !canvas.dataset.initialized) {
                            canvas.dataset.initialized = 'true';
                            window[initFn]();
                        }
                    });
                    chartObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.3 });

        document.querySelectorAll('.slide').forEach(function(slide) {
            chartObserver.observe(slide);
        });"""


def wrap_with_shell(extracted, template_path, logo_b64):
    """Wrap extracted Eos content with locked visual shell."""
    css = extract_css_from_template(template_path)
    if not css:
        css = "/* Template CSS not found — using minimal styles */"

    title = escape(extracted["title"])
    body = extracted["body"]
    scripts = extracted["scripts"]

    # Inject/fix logo in body
    body = inject_logo_if_missing(body, logo_b64)

    # Check if body already has a print button
    has_print_btn = "print-btn" in body or "window.print()" in body
    print_btn = (
        ""
        if has_print_btn
        else '\n    <button class="print-btn" onclick="window.print()">🖨️ Print All Slides</button>'
    )

    # Build script section
    script_parts = [
        "        // ── Chart.js Global Defaults — Zuma brand (LOCKED) ──",
        "        Chart.defaults.font.family = \"'Inter', system-ui, sans-serif\";",
        "        Chart.defaults.color = '#4A5568';",
    ]

    # Add Eos's script blocks (chart init code, custom JS)
    for s in scripts:
        script_parts.append(s)

    # Add locked IntersectionObserver if not already present
    if not has_intersection_observer(scripts):
        script_parts.append(build_locked_observer())

    all_scripts = "\n".join(script_parts)

    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>{css}
    </style>
</head>
<body>
{print_btn}

{body}

    <script>
{all_scripts}
    </script>
</body>
</html>"""

    return html


# ═══════════════════════════════════════════════════════════════
# MODE A: CONTENT JSON → DETERMINISTIC BUILD (for structured data)
# ═══════════════════════════════════════════════════════════════

SCHEMA_BY_TYPE = """
SLIDE TYPES AND THEIR FIELDS:

1. cover
   - title: str
   - subtitle_green: str
   - description: str
   - kpis: [{value: str, label: str}, ...] (3-4 items)

2. exec_summary
   - title: str (assertion statement)
   - kpis: [{label: str, value: str}, ...] (4 items)
   - findings: [{bold: str, text: str}, ...] (3 items)
   - so_what: str

3. chart_trend (dual Y-axis bar chart)
   - title: str
   - labels: [str, ...] (month labels)
   - datasets: [{label: str, data: [num, ...], color: str, axis: "y"|"y1"}, ...]
   - so_what: str

4. chart_ranking (horizontal bar chart)
   - title: str
   - labels: [str, ...] (item labels, max 10)
   - data: [num, ...] (values)
   - data_label: str (e.g. "Revenue (Juta Rp)")
   - bar_color: str (optional, default "#002A3A")
   - so_what: str

5. chart_detail (vertical bar chart)
   - title: str
   - labels: [str, ...] (item labels, max 8)
   - data: [num, ...] (values)
   - data_label: str
   - bar_color: str (optional, default "#00E273")
   - so_what: str

6. breakdown (2-3 column card grid)
   - title: str
   - columns: [{icon: str, title: str, items: [{name: str, value: str}, ...]}, ...]
   - so_what: str

7. insights (2x2 card grid)
   - title: str
   - cards: [{icon: str, title: str, bullets: [str, ...]}, ...] (4 items)

8. table
   - title: str
   - headers: [str, ...]
   - rows: [[str, ...], ...]
   - footnote: str (optional)
   - so_what: str

9. closing
   - section_label: str
   - title: str
   - title_green: str
   - priorities: [{level: int, color: "green"|"amber"|"cyan"|"red", title: str, description: str, target: str}, ...]
   - footer_topic: str
   - footer_type: str
"""


def gen_cover(slide, deck, slide_num, total_slides, logo_b64):
    kpis_html = ""
    for kpi in slide.get("kpis", []):
        kpis_html += f"""
                <div>
                    <div style="font-size:2.75rem;font-weight:900;color:#00E273;line-height:1;">{escape(str(kpi["value"]))}</div>
                    <div style="color:rgba(255,255,255,0.5);font-size:0.85rem;margin-top:0.25rem;">{escape(kpi["label"])}</div>
                </div>"""
    logo_html = (
        f'<img src="data:image/png;base64,{logo_b64}" alt="ZUMA" style="width:36px;height:36px;object-fit:contain;">'
        if logo_b64
        else ""
    )
    return f"""
    <div class="slide slide-dark" id="slide-{slide_num}">
        <div class="gradient-blob gradient-blob-tr"></div>
        <div class="gradient-blob gradient-blob-bl" style="width:350px;height:350px;opacity:0.6"></div>
        <div style="position:relative;z-index:1;display:flex;flex-direction:column;height:100%;min-height:520px;">
            <div style="display:flex;align-items:center;gap:1rem;margin-bottom:3rem;">
                {logo_html}
                <div style="color:rgba(255,255,255,0.45);font-size:0.85rem;letter-spacing:0.04em;">Internal Review · {escape(deck.get("department", "Sales Analytics"))}</div>
            </div>
            <h1 style="font-size:3.5rem;font-weight:900;line-height:1.08;margin-bottom:1.25rem;">
                {escape(slide.get("title", deck.get("title", "Presentation")))}<br>
                <span style="color:#00E273;">{escape(slide.get("subtitle_green", deck.get("subtitle_green", deck.get("period", ""))))}</span>
            </h1>
            <p style="color:rgba(255,255,255,0.55);font-size:1rem;max-width:560px;line-height:1.7;margin-bottom:auto;">{escape(slide.get("description", deck.get("description", "")))}</p>
            <div style="display:flex;gap:3.5rem;margin-top:2.5rem;margin-bottom:1.5rem;">{kpis_html}
            </div>
            <div style="color:rgba(255,255,255,0.25);font-size:0.8rem;padding-top:1rem;border-top:1px solid rgba(255,255,255,0.08);">
                Prepared by Iris · {escape(deck.get("date", ""))} · {escape(deck.get("period", ""))} · Source: {escape(deck.get("source", "Portal Analytics"))}
            </div>
        </div>
        <div class="slide-number">{slide_num} / {total_slides}</div>
    </div>"""


def gen_exec_summary(slide, deck, slide_num, total_slides, logo_b64):
    kpis_html = "".join(
        f"""
            <div class="kpi-card">
                <p class="text-gray-500 text-sm uppercase">{escape(kpi["label"])}</p>
                <p class="text-3xl font-bold text-[#1A202C] mt-2">{escape(str(kpi["value"]))}</p>
            </div>"""
        for kpi in slide.get("kpis", [])
    )
    findings_html = "".join(
        f"""
            <li><strong class="text-[#002A3A]">{escape(f["bold"])}</strong> {escape(f["text"])}</li>"""
        for f in slide.get("findings", [])
    )
    return f"""
    <div class="slide" id="slide-{slide_num}" style="display:flex;flex-direction:column;">
        <div class="header-band"><h2 class="text-3xl font-bold">{escape(slide["title"])}</h2></div>
        <div class="grid grid-cols-4 gap-6 mb-6">{kpis_html}
        </div>
        <ul class="list-disc pl-6 text-lg text-gray-700 space-y-3">{findings_html}
        </ul>
        <div class="so-what">
            <p class="text-xs font-bold uppercase text-[#00E273] mb-1">→ So What</p>
            <p class="text-sm font-medium text-gray-800">{escape(slide.get("so_what", ""))}</p>
        </div>
        <div class="slide-number">{slide_num} / {total_slides}</div>
    </div>"""


def gen_chart_slide(slide, deck, slide_num, total_slides, logo_b64):
    """Generic chart slide (works for trend, ranking, detail)."""
    chart_id = f"chart_{slide_num}"
    return f'''
    <div class="slide" id="slide-{slide_num}" style="display:flex;flex-direction:column;">
        <div class="header-band"><h2 class="text-3xl font-bold">{escape(slide["title"])}</h2></div>
        <div class="chart-container" style="flex:1;"><canvas id="{chart_id}"></canvas></div>
        <div class="so-what">
            <p class="text-xs font-bold uppercase text-[#00E273] mb-1">→ So What</p>
            <p class="text-sm font-medium text-gray-800">{escape(slide.get("so_what", ""))}</p>
        </div>
        <div class="slide-number">{slide_num} / {total_slides}</div>
    </div>'''


def gen_breakdown(slide, deck, slide_num, total_slides, logo_b64):
    cols = slide.get("columns", [])
    cols_html = ""
    for col in cols:
        items = "".join(
            f'<li class="flex justify-between border-b pb-2"><span>{escape(i["name"])}</span> <strong>{escape(str(i["value"]))}</strong></li>'
            for i in col.get("items", [])
        )
        cols_html += f"""
            <div class="bg-gray-50 rounded-xl p-6 border border-gray-200">
                <h3 class="text-xl font-bold text-[#002A3A] mb-4">{escape(col.get("icon", "📍"))} {escape(col["title"])}</h3>
                <ul class="space-y-3 text-gray-700">{items}</ul>
            </div>"""
    return f"""
    <div class="slide" id="slide-{slide_num}" style="display:flex;flex-direction:column;">
        <div class="header-band"><h2 class="text-3xl font-bold">{escape(slide["title"])}</h2></div>
        <div class="grid grid-cols-{len(cols)} gap-6 mb-6">{cols_html}
        </div>
        <div class="so-what">
            <p class="text-xs font-bold uppercase text-[#00E273] mb-1">→ So What</p>
            <p class="text-sm font-medium text-gray-800">{escape(slide.get("so_what", ""))}</p>
        </div>
        <div class="slide-number">{slide_num} / {total_slides}</div>
    </div>"""


def gen_insights(slide, deck, slide_num, total_slides, logo_b64):
    cards = slide.get("cards", [])
    cards_html = ""
    for card in cards:
        bullets = "".join(f"<li>{b}</li>" for b in card.get("bullets", []))
        cards_html += f"""
            <div class="bg-gray-50 p-5 rounded-xl border border-gray-200" style="display:flex;flex-direction:column;">
                <h3 class="text-lg font-bold text-[#002A3A] mb-2">{escape(card.get("icon", "💡"))} {escape(card["title"])}</h3>
                <ul class="list-disc pl-5 space-y-1.5 text-gray-700 text-sm" style="flex:1;">{bullets}</ul>
            </div>"""
    return f"""
    <div class="slide" id="slide-{slide_num}" style="display:flex;flex-direction:column;height:640px;">
        <div class="header-band"><h2 class="text-3xl font-bold">{escape(slide["title"])}</h2></div>
        <div style="display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;gap:1rem;flex:1;">{cards_html}
        </div>
        <div class="slide-number">{slide_num} / {total_slides}</div>
    </div>"""


def gen_table(slide, deck, slide_num, total_slides, logo_b64):
    th = "".join(f"<th>{escape(h)}</th>" for h in slide.get("headers", []))
    rows = "".join(
        "<tr>" + "".join(f"<td>{escape(str(c))}</td>" for c in row) + "</tr>"
        for row in slide.get("rows", [])
    )
    fn = (
        f'<div class="footnote">{escape(slide["footnote"])}</div>'
        if slide.get("footnote")
        else ""
    )
    return f"""
    <div class="slide" id="slide-{slide_num}" style="display:flex;flex-direction:column;">
        <div class="header-band"><h2 class="text-3xl font-bold">{escape(slide["title"])}</h2></div>
        <div style="flex:1;overflow-y:auto;"><table><thead><tr>{th}</tr></thead><tbody>{rows}</tbody></table>{fn}</div>
        <div class="so-what">
            <p class="text-xs font-bold uppercase text-[#00E273] mb-1">→ So What</p>
            <p class="text-sm font-medium text-gray-800">{escape(slide.get("so_what", ""))}</p>
        </div>
        <div class="slide-number">{slide_num} / {total_slides}</div>
    </div>"""


def gen_closing(slide, deck, slide_num, total_slides, logo_b64):
    color_map = {
        "green": (
            "#00E273",
            "rgba(0,226,115,0.08)",
            "rgba(0,226,115,0.2)",
            "rgba(0,226,115,0.15)",
        ),
        "amber": (
            "#FFB800",
            "rgba(255,184,0,0.08)",
            "rgba(255,184,0,0.2)",
            "rgba(255,184,0,0.15)",
        ),
        "cyan": (
            "#00B8D4",
            "rgba(0,184,212,0.08)",
            "rgba(0,184,212,0.2)",
            "rgba(0,184,212,0.15)",
        ),
        "red": (
            "#FF4D4D",
            "rgba(255,77,77,0.08)",
            "rgba(255,77,77,0.2)",
            "rgba(255,77,77,0.15)",
        ),
    }
    cards = ""
    for p in slide.get("priorities", []):
        col, bg, bd, ln = color_map.get(p.get("color", "green"), color_map["green"])
        cards += f"""
                <div style="background:{bg};border:1px solid {bd};border-radius:12px;padding:2rem;display:flex;flex-direction:column;">
                    <div style="background:{col};color:#002A3A;font-weight:800;font-size:0.75rem;padding:0.3rem 0.75rem;border-radius:4px;width:fit-content;margin-bottom:1rem;">PRIORITAS {p.get("level", "")}</div>
                    <h3 style="font-size:1.25rem;font-weight:700;color:{col};margin-bottom:0.75rem;">{escape(p["title"])}</h3>
                    <p style="color:rgba(255,255,255,0.65);font-size:0.9rem;line-height:1.6;flex:1;">{escape(p["description"])}</p>
                    <div style="margin-top:1rem;padding-top:0.75rem;border-top:1px solid {ln};font-size:0.8rem;color:rgba(255,255,255,0.4);">Target: {escape(p.get("target", ""))}</div>
                </div>"""
    logo_html = (
        f'<img src="data:image/png;base64,{logo_b64}" alt="ZUMA" style="width:24px;height:24px;object-fit:contain;">'
        if logo_b64
        else ""
    )
    return f"""
    <div class="slide slide-dark" id="slide-{slide_num}">
        <div class="gradient-blob gradient-blob-tr" style="opacity:0.8"></div>
        <div class="gradient-blob gradient-blob-bl" style="width:300px;height:300px;opacity:0.5"></div>
        <div style="position:relative;z-index:1;display:flex;flex-direction:column;height:100%;min-height:520px;">
            <div style="margin-bottom:2rem;">
                <p style="color:#00E273;font-size:0.75rem;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;margin-bottom:0.75rem;">{escape(slide.get("section_label", "Rekomendasi & Tindak Lanjut"))}</p>
                <h2 style="font-size:2.5rem;font-weight:800;line-height:1.15;">{escape(slide.get("title", "Prioritas Aksi"))}<br><span style="color:#00E273;">{escape(slide.get("title_green", ""))}</span></h2>
            </div>
            <div class="grid grid-cols-3 gap-6" style="flex:1;">{cards}
            </div>
            <div style="margin-top:1.5rem;padding-top:1rem;border-top:1px solid rgba(255,255,255,0.08);display:flex;align-items:center;justify-content:space-between;">
                <div style="display:flex;align-items:center;gap:0.75rem;">{logo_html}<span style="color:rgba(255,255,255,0.35);font-size:0.8rem;">{escape(slide.get("footer_topic", ""))} · {escape(slide.get("footer_type", ""))}</span></div>
                <div style="color:rgba(255,255,255,0.25);font-size:0.75rem;">Prepared by Iris · {escape(deck.get("date", ""))}</div>
            </div>
        </div>
        <div class="slide-number">{slide_num} / {total_slides}</div>
    </div>"""


SLIDE_GENERATORS = {
    "cover": gen_cover,
    "exec_summary": gen_exec_summary,
    "chart_trend": gen_chart_slide,
    "chart_ranking": gen_chart_slide,
    "chart_detail": gen_chart_slide,
    "breakdown": gen_breakdown,
    "insights": gen_insights,
    "table": gen_table,
    "closing": gen_closing,
}


def gen_chart_js(slides):
    """Generate Chart.js init code for all chart slides in content JSON mode."""
    blocks = []
    for i, slide in enumerate(slides):
        n = i + 1
        cid = f"chart_{n}"
        st = slide.get("type", "")

        if st == "chart_trend":
            ds_js = ",".join(
                f"""{{label:'{d["label"]}',data:{json.dumps(d["data"])},backgroundColor:'{d.get("color", "#00E273")}',borderRadius:4,yAxisID:'{d.get("axis", "y")}'}}"""
                for d in slide.get("datasets", [])
            )
            ds0 = slide.get("datasets", [{}])[0].get("label", "Value")
            ds1 = (
                slide.get("datasets", [{}, {}])[1].get("label", "Volume")
                if len(slide.get("datasets", [])) > 1
                else "Volume"
            )
            blocks.append(
                f"window.initChart_{cid}=function(){{new Chart(document.getElementById('{cid}'),{{type:'bar',data:{{labels:{json.dumps(slide.get('labels', []))},datasets:[{ds_js}]}},options:{{responsive:true,maintainAspectRatio:false,animation:{{duration:800,easing:'easeOutQuart'}},plugins:{{legend:{{labels:{{padding:20,usePointStyle:true,pointStyleWidth:12}}}}}},scales:{{y:{{type:'linear',position:'left',title:{{display:true,text:'{ds0}',font:{{size:11,weight:'600'}}}},grid:{{color:'rgba(0,0,0,0.05)'}},border:{{display:false}}}},y1:{{type:'linear',position:'right',grid:{{drawOnChartArea:false}},title:{{display:true,text:'{ds1}',font:{{size:11,weight:'600'}}}},border:{{display:false}}}}}}}}}});}};"
            )
        elif st == "chart_ranking":
            blocks.append(
                f"window.initChart_{cid}=function(){{new Chart(document.getElementById('{cid}'),{{type:'bar',data:{{labels:{json.dumps(slide.get('labels', []))},datasets:[{{label:'{slide.get('data_label', 'Value')}',data:{json.dumps(slide.get('data', []))},backgroundColor:'{slide.get('bar_color', '#002A3A')}',borderRadius:4}}]}},options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,animation:{{duration:800,easing:'easeOutQuart'}},plugins:{{legend:{{display:false}}}},scales:{{x:{{grid:{{color:'rgba(0,0,0,0.05)'}},border:{{display:false}}}},y:{{grid:{{display:false}},border:{{display:false}}}}}}}}}});}};"
            )
        elif st == "chart_detail":
            blocks.append(
                f"window.initChart_{cid}=function(){{new Chart(document.getElementById('{cid}'),{{type:'bar',data:{{labels:{json.dumps(slide.get('labels', []))},datasets:[{{label:'{slide.get('data_label', 'Value')}',data:{json.dumps(slide.get('data', []))},backgroundColor:'{slide.get('bar_color', '#00E273')}',borderRadius:4}}]}},options:{{responsive:true,maintainAspectRatio:false,animation:{{duration:800,easing:'easeOutQuart'}},plugins:{{legend:{{display:false}}}},scales:{{x:{{grid:{{display:false}},border:{{display:false}}}},y:{{grid:{{color:'rgba(0,0,0,0.05)'}},border:{{display:false}}}}}}}}}});}};"
            )
    return "\n        ".join(blocks)


def build_from_json(content, template_path, logo_b64):
    """Mode A: Build from content JSON."""
    deck = content.get("deck", {})
    slides = content.get("slides", [])
    total = len(slides)
    css = extract_css_from_template(template_path) or ""
    if not logo_b64:
        logo_b64 = load_logo_base64()

    slides_html = []
    for i, s in enumerate(slides):
        fn = SLIDE_GENERATORS.get(s.get("type", ""))
        if fn:
            slides_html.append(fn(s, deck, i + 1, total, logo_b64))

    chart_js = gen_chart_js(slides)
    observer = build_locked_observer()

    return f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZUMA — {escape(deck.get("title", "Presentation"))}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>{css}
    </style>
</head>
<body>
    <button class="print-btn" onclick="window.print()">🖨️ Print All Slides</button>
{"".join(slides_html)}
    <script>
        Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
        Chart.defaults.color = '#4A5568';
        {chart_js}
{observer}
    </script>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(
        description="Build Zuma HTML deck — Mode A (content JSON) or Mode B (wrap Eos HTML)"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--content", "-c", help="[Mode A] Content JSON file → deterministic build"
    )
    group.add_argument(
        "--wrap",
        "-w",
        help="[Mode B] Eos raw HTML file → wrap with locked shell (PRIMARY)",
    )
    parser.add_argument("--output", "-o", help="Output HTML file path")
    parser.add_argument(
        "--template",
        "-t",
        default=DEFAULT_TEMPLATE,
        help="Template HTML for CSS extraction",
    )
    parser.add_argument(
        "--validate", "-v", action="store_true", help="Run validate_deck.py after build"
    )
    parser.add_argument(
        "--schema",
        action="store_true",
        help="Print content JSON schema (Mode A) and exit",
    )
    args = parser.parse_args()

    if args.schema:
        print("CONTENT JSON SCHEMA (Mode A)")
        print("=" * 60)
        print(SCHEMA_BY_TYPE)
        sys.exit(0)

    logo_b64 = load_logo_base64()

    if args.wrap:
        # ── MODE B: Shell Wrapper ──
        if not os.path.exists(args.wrap):
            print(f"Error: File not found: {args.wrap}", file=sys.stderr)
            sys.exit(1)
        with open(args.wrap, "r", encoding="utf-8") as f:
            raw = f.read()

        extracted = extract_body_content(raw)
        html = wrap_with_shell(extracted, args.template, logo_b64)
        mode_label = "Mode B (wrap)"

    elif args.content:
        # ── MODE A: Content JSON ──
        if not os.path.exists(args.content):
            print(f"Error: File not found: {args.content}", file=sys.stderr)
            sys.exit(1)
        with open(args.content, "r", encoding="utf-8") as f:
            content = json.load(f)

        html = build_from_json(content, args.template, logo_b64)
        mode_label = "Mode A (json)"
    else:
        parser.error(
            "Either --content (Mode A) or --wrap (Mode B) is required. Use --schema for help."
        )
        return

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(html)
        slide_count = len(re.findall(r'class="slide[\s"]', html))
        print(
            f"✅ [{mode_label}] Deck built: {args.output} ({len(html)} bytes, ~{slide_count} slides)"
        )
    else:
        print(html)

    if args.validate and args.output:
        print("\n🔍 Running post-build validation...")
        validator = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "validate_deck.py"
        )
        if os.path.exists(validator):
            exit_code = os.system(f"python3 {validator} {args.output}")
            sys.exit(exit_code >> 8)  # os.system returns shifted exit code
        else:
            print(f"WARNING: Validator not found at {validator}", file=sys.stderr)


if __name__ == "__main__":
    main()
