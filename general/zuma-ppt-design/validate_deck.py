#!/usr/bin/env python3
"""
validate_deck.py — Post-Processor QA for Eos-generated HTML decks
=================================================================
Validates HTML deck output against Zuma golden template requirements.
Run AFTER Eos writes a deck, BEFORE deploying to Vercel.

Usage:
    python3 validate_deck.py <deck.html>
    python3 validate_deck.py <deck.html> --json          # JSON output
    python3 validate_deck.py <deck.html> --fix            # Auto-fix what's possible
    python3 validate_deck.py <deck.html> --fix --output fixed.html

Exit codes:
    0 = PASS (all checks OK)
    1 = FAIL (critical violations found)
    2 = WARN (non-critical issues, deck usable but imperfect)

Author: Claude Code (for Iris pipeline)
Version: 1.0 (2026-02-28)
"""

import argparse
import json
import os
import re
import sys

# ── CHECK DEFINITIONS ──
# Each check: (id, severity, description, check_function)
# Severity: CRITICAL (blocks deploy), WARNING (deploy OK but flag), INFO (nice-to-have)

LOGO_BASE64_MIN_LENGTH = 4000  # Correct logo is ~4318 chars
MIN_SLIDE_COUNT = 3
MIN_FILE_SIZE_KB = 10  # Deck < 10KB is almost certainly broken


def check_tailwind_cdn(html):
    """Check Tailwind CSS CDN is loaded."""
    if "cdn.tailwindcss.com" in html:
        return True, "Tailwind CDN found"
    return False, "MISSING: <script src='https://cdn.tailwindcss.com'></script>"


def check_chartjs_cdn(html):
    """Check Chart.js CDN is loaded."""
    if "chart.js" in html.lower() or "chart.umd" in html:
        return True, "Chart.js CDN found"
    return False, "MISSING: Chart.js CDN (https://cdn.jsdelivr.net/npm/chart.js)"


def check_scroll_layout(html):
    """Check deck uses scroll-based layout (NOT overlay/absolute positioning)."""
    # Check for correct pattern: slides use min-height (scroll)
    has_min_height = (
        bool(re.search(r"min-height\s*:\s*\d+px", html)) or "min-height:" in html
    )

    # Check for BANNED pattern: .slide with position:absolute (overlay)
    # Match CSS rule where .slide has position: absolute
    has_overlay = bool(re.search(r"\.slide\s*\{[^}]*position\s*:\s*absolute", html))
    # Also check for .slide.active pattern (overlay indicator)
    has_active_pattern = bool(re.search(r"\.slide\.active", html))

    if has_overlay or has_active_pattern:
        return (
            False,
            "BANNED: Overlay layout detected (.slide { position: absolute } or .slide.active). Must use scroll-based layout.",
        )

    if has_min_height or "min-height" in html:
        return True, "Scroll-based layout confirmed"

    return (
        False,
        "WARNING: Could not confirm scroll-based layout (missing min-height on .slide)",
    )


def check_print_css(html):
    """Check print CSS exists for Ctrl+P printing."""
    if "@media print" in html:
        has_page_break = "page-break" in html or "break-after" in html
        if has_page_break:
            return True, "@media print with page-break rules found"
        return (
            True,
            "@media print found (but no page-break rules — may not paginate correctly)",
        )
    return False, "MISSING: @media print CSS block (Ctrl+P won't work properly)"


def check_logo_base64(html):
    """Check ZUMA logo is present and not truncated."""
    # Find all base64 image data URIs
    b64_matches = re.findall(r"data:image/png;base64,[A-Za-z0-9+/=]+", html)

    if not b64_matches:
        return False, "MISSING: No inline base64 logo found"

    # Check the longest base64 string (should be the logo)
    longest = max(b64_matches, key=len)
    logo_len = len(longest)

    if logo_len < LOGO_BASE64_MIN_LENGTH:
        return (
            False,
            f"TRUNCATED: Logo base64 is {logo_len} chars (expected >{LOGO_BASE64_MIN_LENGTH}). Source: /tmp/zuma-logo-base64.txt",
        )

    # Count how many slides have the logo
    logo_count = len(b64_matches)
    if logo_count >= 2:
        return (
            True,
            f"Logo found in {logo_count} locations, length={logo_len} chars (OK)",
        )
    return (
        True,
        f"Logo found in {logo_count} location(s), length={logo_len} chars (consider adding to closing slide too)",
    )


def check_intersection_observer(html):
    """Check IntersectionObserver is present for chart animations."""
    if "IntersectionObserver" in html:
        return True, "IntersectionObserver found for chart lazy-loading"
    # If no charts, this is OK
    if "<canvas" not in html:
        return True, "No charts found — IntersectionObserver not needed"
    return False, "MISSING: IntersectionObserver (charts won't animate on scroll)"


def check_inter_font(html):
    """Check Inter font is loaded."""
    if "Inter" in html:
        return True, "Inter font reference found"
    return False, "MISSING: Inter font — deck will use system fallback"


def check_slide_count(html):
    """Check minimum number of slides."""
    # Count slide divs (class="slide" or class="slide slide-dark")
    slides = re.findall(r'<div\s+class="slide[^"]*"', html)
    count = len(slides)

    if count < MIN_SLIDE_COUNT:
        return (
            False,
            f"Only {count} slide(s) found (minimum: {MIN_SLIDE_COUNT}). Deck is incomplete.",
        )
    return True, f"{count} slides found"


def check_file_size(html):
    """Check file isn't suspiciously small."""
    size_kb = len(html.encode("utf-8")) / 1024

    if size_kb < MIN_FILE_SIZE_KB:
        return (
            False,
            f"File is only {size_kb:.1f}KB (minimum: {MIN_FILE_SIZE_KB}KB). Likely truncated or incomplete.",
        )
    return True, f"File size: {size_kb:.1f}KB"


def check_print_button(html):
    """Check floating print button exists."""
    if "print-btn" in html or "window.print()" in html:
        return True, "Print button found"
    return False, "MISSING: Floating print button (🖨️ Print All Slides)"


def check_gradient_blobs(html):
    """Check gradient blobs on dark slides."""
    if "gradient-blob" in html or "gradient_blob" in html or "radial-gradient" in html:
        return True, "Gradient blobs found on dark slides"
    return False, "MISSING: Gradient blobs on dark slides (premium feel)"


def check_so_what_boxes(html):
    """Check So-What boxes exist on content slides."""
    so_what_count = (
        html.count("so-what") + html.count("So What") + html.count("so_what")
    )

    if so_what_count == 0:
        return (
            False,
            "MISSING: No So-What boxes found (mandatory on every content slide)",
        )
    return True, f"{so_what_count} So-What references found"


def check_zuma_colors(html):
    """Check Zuma brand colors are used."""
    has_teal = "#002A3A" in html or "#002a3a" in html
    has_green = "#00E273" in html or "#00e273" in html

    if has_teal and has_green:
        return True, "Zuma brand colors (#002A3A teal, #00E273 green) found"
    missing = []
    if not has_teal:
        missing.append("#002A3A (teal)")
    if not has_green:
        missing.append("#00E273 (green)")
    return False, f"MISSING brand colors: {', '.join(missing)}"


def check_dark_slides(html):
    """Check cover and closing slides use dark background."""
    has_dark = (
        "slide-dark" in html
        or "background: var(--zuma-teal)" in html
        or "background:#002A3A" in html
    )
    if has_dark:
        return True, "Dark slides present (cover/closing)"
    return False, "MISSING: No dark slides found — cover and closing should be dark"


def check_no_overlay_patterns(html):
    """Deep check for overlay/SPA anti-patterns that prevent Ctrl+P."""
    violations = []

    # Check for overflow:hidden on body (prevents scrolling)
    if re.search(r"body\s*\{[^}]*overflow\s*:\s*hidden", html):
        violations.append("body { overflow: hidden } — prevents scrolling")

    # Check for display:none on slides (overlay pattern)
    if re.search(r"\.slide\s*\{[^}]*display\s*:\s*none", html):
        violations.append(".slide { display: none } — overlay pattern")

    # Check for z-index manipulation on slides
    if re.search(r"\.slide\.active\s*\{[^}]*z-index", html):
        violations.append(".slide.active { z-index } — overlay navigation")

    # Check for opacity:0 on base .slide (overlay)
    if re.search(r"\.slide\s*\{[^}]*opacity\s*:\s*0", html):
        violations.append(".slide { opacity: 0 } — overlay fade pattern")

    # Check for JavaScript slide navigation (prev/next buttons)
    if re.search(r"(currentSlide|slideIndex|showSlide|nextSlide|prevSlide)", html):
        violations.append(
            "JavaScript slide navigation detected — should be scroll-based"
        )

    if violations:
        return False, "BANNED overlay patterns: " + "; ".join(violations)
    return True, "No overlay anti-patterns detected"


# ── MASTER CHECK LIST ──
CHECKS = [
    # (id, severity, description, function)
    ("tailwind_cdn", "CRITICAL", "Tailwind CSS CDN", check_tailwind_cdn),
    ("chartjs_cdn", "WARNING", "Chart.js CDN", check_chartjs_cdn),
    ("scroll_layout", "CRITICAL", "Scroll-based layout", check_scroll_layout),
    ("no_overlay", "CRITICAL", "No overlay anti-patterns", check_no_overlay_patterns),
    ("print_css", "CRITICAL", "Print CSS (@media print)", check_print_css),
    ("logo_base64", "CRITICAL", "ZUMA logo (not truncated)", check_logo_base64),
    (
        "intersection_obs",
        "WARNING",
        "IntersectionObserver",
        check_intersection_observer,
    ),
    ("inter_font", "INFO", "Inter font", check_inter_font),
    ("slide_count", "CRITICAL", "Minimum slide count", check_slide_count),
    ("file_size", "CRITICAL", "Minimum file size", check_file_size),
    ("print_button", "WARNING", "Floating print button", check_print_button),
    (
        "gradient_blobs",
        "WARNING",
        "Gradient blobs on dark slides",
        check_gradient_blobs,
    ),
    ("so_what_boxes", "WARNING", "So-What boxes", check_so_what_boxes),
    ("zuma_colors", "CRITICAL", "Zuma brand colors", check_zuma_colors),
    ("dark_slides", "WARNING", "Dark cover/closing slides", check_dark_slides),
]


def validate(html_content):
    """Run all checks and return results."""
    results = []
    for check_id, severity, description, check_fn in CHECKS:
        passed, message = check_fn(html_content)
        results.append(
            {
                "id": check_id,
                "severity": severity,
                "description": description,
                "passed": passed,
                "message": message,
            }
        )
    return results


def summarize(results):
    """Summarize results into overall verdict."""
    critical_fails = [
        r for r in results if not r["passed"] and r["severity"] == "CRITICAL"
    ]
    warnings = [r for r in results if not r["passed"] and r["severity"] == "WARNING"]
    infos = [r for r in results if not r["passed"] and r["severity"] == "INFO"]
    passed = [r for r in results if r["passed"]]

    if critical_fails:
        verdict = "FAIL"
        exit_code = 1
    elif warnings:
        verdict = "WARN"
        exit_code = 2
    else:
        verdict = "PASS"
        exit_code = 0

    return {
        "verdict": verdict,
        "exit_code": exit_code,
        "total": len(results),
        "passed": len(passed),
        "critical_fails": len(critical_fails),
        "warnings": len(warnings),
        "infos": len(infos),
        "details": results,
    }


def print_report(summary, filename):
    """Print human-readable validation report."""
    v = summary["verdict"]
    icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}[v]

    print(f"\n{'=' * 60}")
    print(f"  DECK VALIDATION: {icon} {v}")
    print(f"  File: {filename}")
    print(f"  Checks: {summary['passed']}/{summary['total']} passed")
    print(f"{'=' * 60}")

    # Print failures first
    for r in summary["details"]:
        if not r["passed"]:
            sev_icon = {"CRITICAL": "❌", "WARNING": "⚠️", "INFO": "ℹ️"}[r["severity"]]
            print(f"\n  {sev_icon} [{r['severity']}] {r['description']}")
            print(f"    → {r['message']}")

    # Print passes
    if summary["passed"] > 0:
        print(f"\n  ✅ Passed ({summary['passed']}):")
        for r in summary["details"]:
            if r["passed"]:
                print(f"    • {r['description']}: {r['message']}")

    print(f"\n{'=' * 60}")

    if v == "FAIL":
        print("  🚫 DO NOT DEPLOY — fix critical issues first.")
        print("  Run with --fix to attempt auto-repair.")
    elif v == "WARN":
        print("  ⚡ Deploy OK but consider fixing warnings.")
    else:
        print("  🚀 Ready to deploy!")

    print(f"{'=' * 60}\n")


def auto_fix(html_content, results):
    """Attempt to auto-fix known issues. Returns (fixed_html, fix_log)."""
    fixed = html_content
    fix_log = []

    for r in results:
        if r["passed"]:
            continue

        if r["id"] == "tailwind_cdn":
            # Inject Tailwind CDN before </head>
            if "</head>" in fixed:
                fixed = fixed.replace(
                    "</head>",
                    '    <script src="https://cdn.tailwindcss.com"></script>\n</head>',
                )
                fix_log.append("✅ Injected Tailwind CDN")

        elif r["id"] == "chartjs_cdn":
            if "</head>" in fixed:
                fixed = fixed.replace(
                    "</head>",
                    '    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>\n</head>',
                )
                fix_log.append("✅ Injected Chart.js CDN")

        elif r["id"] == "print_css":
            # Inject print CSS before </style>
            print_css = """
        @media print {
            @page { size: A4 landscape; margin: 0; }
            html, body { background: white !important; padding: 0 !important; margin: 0 !important; }
            .slide { page-break-after: always; break-after: page; height: 190mm !important; min-height: unset; margin-bottom: 0; border-radius: 0; box-shadow: none; padding: 2rem; overflow: hidden; }
            .slide:last-child { page-break-after: avoid; break-after: avoid; }
            * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
            .slide-dark { background: #002A3A !important; }
            .gradient-blob { display: none !important; }
            .print-btn { display: none !important; }
            canvas { max-height: 350px !important; }
        }"""
            if "</style>" in fixed:
                fixed = fixed.replace("</style>", print_css + "\n    </style>")
                fix_log.append("✅ Injected print CSS")

        elif r["id"] == "print_button":
            # Inject print button after <body>
            btn = '\n    <button class="print-btn" onclick="window.print()">🖨️ Print All Slides</button>\n'
            if "<body>" in fixed:
                fixed = fixed.replace("<body>", "<body>" + btn)
                fix_log.append("✅ Injected floating print button")

        elif r["id"] == "inter_font":
            if "</head>" in fixed:
                fixed = fixed.replace(
                    "</head>",
                    '    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">\n</head>',
                )
                fix_log.append("✅ Injected Inter font")

        elif r["id"] == "logo_base64":
            # Try to inject logo from file
            logo_path = "/tmp/zuma-logo-base64.txt"
            if os.path.exists(logo_path):
                with open(logo_path, "r") as f:
                    logo_b64 = f.read().strip()
                if len(logo_b64) > LOGO_BASE64_MIN_LENGTH:
                    # Find truncated logos and replace
                    truncated = re.findall(
                        r"data:image/png;base64,[A-Za-z0-9+/=]{100,3999}", fixed
                    )
                    for trunc in truncated:
                        fixed = fixed.replace(
                            trunc, f"data:image/png;base64,{logo_b64}"
                        )
                        fix_log.append(
                            f"✅ Replaced truncated logo ({len(trunc)} → {len(logo_b64) + 22} chars)"
                        )
                else:
                    fix_log.append(
                        f"⚠️ Logo file at {logo_path} is also truncated ({len(logo_b64)} chars)"
                    )
            else:
                fix_log.append(f"⚠️ Cannot fix logo — {logo_path} not found")

    return fixed, fix_log


def main():
    parser = argparse.ArgumentParser(
        description="Validate Zuma HTML deck against golden template requirements"
    )
    parser.add_argument("file", help="HTML deck file to validate")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--fix", action="store_true", help="Auto-fix known issues")
    parser.add_argument(
        "--output", "-o", help="Output path for fixed HTML (default: overwrite input)"
    )
    parser.add_argument(
        "--strict", action="store_true", help="Treat warnings as failures"
    )
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    with open(args.file, "r", encoding="utf-8") as f:
        html = f.read()

    results = validate(html)
    summary = summarize(results)

    # Strict mode: treat warnings as failures
    if args.strict and summary["warnings"] > 0:
        summary["verdict"] = "FAIL"
        summary["exit_code"] = 1

    if args.fix:
        fixed_html, fix_log = auto_fix(html, results)
        output_path = args.output or args.file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(fixed_html)

        # Re-validate after fix
        results_after = validate(fixed_html)
        summary_after = summarize(results_after)

        if not args.json:
            print("\n🔧 AUTO-FIX APPLIED:")
            for log in fix_log:
                print(f"  {log}")
            print(f"\n  Fixed file written to: {output_path}")
            print_report(summary_after, output_path)
        else:
            output = {
                "before": summary,
                "fixes_applied": fix_log,
                "after": summary_after,
                "output_path": output_path,
            }
            print(json.dumps(output, indent=2))

        sys.exit(summary_after["exit_code"])

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print_report(summary, args.file)

    sys.exit(summary["exit_code"])


if __name__ == "__main__":
    main()
