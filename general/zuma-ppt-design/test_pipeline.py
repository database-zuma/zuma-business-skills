#!/usr/bin/env python3
"""
test_pipeline.py — Automated End-to-End Pipeline Test for Zuma Presentation Decks
=================================================================================
Codifies the FULL debugging/QA process done manually on 2026-02-28 into a single
reusable script. Run after any Iris pipeline execution to verify correctness.

6 TEST LAYERS (matching the manual debug process):
  Layer 1: Build Script Integrity    — build_deck.py Mode A & Mode B produce valid output
  Layer 2: Validator Integrity       — validate_deck.py catches known bad patterns
  Layer 3: HTML Structural QA        — 15-check validator passes on final output
  Layer 4: Data Accuracy Verification — compare deck data against VPS database
  Layer 5: Visual Structure Check    — slides, charts, So-What boxes, brand elements
  Layer 6: Deployment Verification   — Vercel URL returns HTTP 200 with correct size

Usage:
    # Full pipeline test (all 6 layers)
    python3 test_pipeline.py --deck /tmp/baby-final.html

    # Test after Iris run (auto-finds latest outbox file)
    python3 test_pipeline.py --latest

    # Test specific layers only
    python3 test_pipeline.py --deck deck.html --layers 1,2,3

    # Test with data verification (needs DB access)
    python3 test_pipeline.py --deck deck.html --verify-data --gender BABY

    # Test with Vercel deployment check
    python3 test_pipeline.py --deck deck.html --vercel-url https://baby-nasional-vercel.vercel.app

    # Quick mode (skip DB + Vercel, just HTML/structural)
    python3 test_pipeline.py --deck deck.html --quick

    # JSON output for CI/automation
    python3 test_pipeline.py --deck deck.html --json

    # Generate test report file
    python3 test_pipeline.py --deck deck.html --report /tmp/test-report.md

Author: Claude Code (for Iris pipeline QA automation)
Version: 1.0 (2026-02-28) — Codified from manual debugging session
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime

# ── PATHS ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_DECK = os.path.join(SCRIPT_DIR, "build_deck.py")
VALIDATE_DECK = os.path.join(SCRIPT_DIR, "validate_deck.py")
OUTBOX_DIR = os.path.join(SCRIPT_DIR, "outbox")
TEMPLATE_PATH = os.path.expanduser(
    "~/.openclaw/workspace/zuma-business-skills/general/zuma-ppt-design/TEMPLATE.html"
)
LOGO_B64_PATH = "/tmp/zuma-logo-base64.txt"

# ── DB CONFIG (VPS PostgreSQL) ──
DB_CONFIG = {
    "host": "76.13.194.120",
    "port": "5432",
    "dbname": "openclaw_ops",
    "user": "openclaw_app",
    "password": "Zuma-0psCl4w-2026!",
}

# ── TEST DATA (for Mode A regression test) ──
SAMPLE_CONTENT_JSON = {
    "deck": {
        "title": "Pipeline Test",
        "subtitle_green": "Automated QA",
        "description": "Regression test deck",
        "department": "QA",
        "date": "2026-02-28",
        "period": "Test Run",
        "source": "test_pipeline.py",
    },
    "slides": [
        {
            "type": "cover",
            "title": "Pipeline Test",
            "subtitle_green": "Automated QA",
            "description": "Testing build_deck.py Mode A",
            "kpis": [
                {"value": "15/15", "label": "Checks"},
                {"value": "100%", "label": "Pass Rate"},
                {"value": "0", "label": "Bugs"},
            ],
        },
        {
            "type": "exec_summary",
            "title": "Semua Sistem Berfungsi Normal",
            "kpis": [
                {"label": "Mode A", "value": "✅"},
                {"label": "Mode B", "value": "✅"},
                {"label": "Validator", "value": "✅"},
                {"label": "Pipeline", "value": "✅"},
            ],
            "findings": [
                {
                    "bold": "Build:",
                    "text": "Mode A dan Mode B menghasilkan output valid",
                },
                {"bold": "Validate:", "text": "15 checks semua PASS"},
                {"bold": "Data:", "text": "Angka sesuai database VPS"},
            ],
            "so_what": "Pipeline siap untuk production deployment.",
        },
        {
            "type": "closing",
            "section_label": "Pipeline Status",
            "title": "All Systems",
            "title_green": "Operational",
            "priorities": [
                {
                    "level": 1,
                    "color": "green",
                    "title": "Pipeline Ready",
                    "description": "All 6 test layers pass",
                    "target": "Production",
                },
            ],
            "footer_topic": "QA",
            "footer_type": "Automated Test",
        },
    ],
}


class PipelineTestRunner:
    """Runs all 6 test layers and collects results."""

    def __init__(self, deck_path=None, vercel_url=None, gender=None, verify_data=False):
        self.deck_path = deck_path
        self.vercel_url = vercel_url
        self.gender = gender
        self.verify_data = verify_data
        self.results = []
        self.start_time = time.time()
        self.html_content = None

        if deck_path and os.path.exists(deck_path):
            with open(deck_path, "r", encoding="utf-8") as f:
                self.html_content = f.read()

    def add_result(self, layer, test_name, passed, message, severity="CRITICAL"):
        self.results.append(
            {
                "layer": layer,
                "test": test_name,
                "passed": passed,
                "message": message,
                "severity": severity,
                "timestamp": datetime.now().isoformat(),
            }
        )

    # ═══════════════════════════════════════════════════════════
    # LAYER 1: BUILD SCRIPT INTEGRITY
    # ═══════════════════════════════════════════════════════════

    def test_layer1_build_integrity(self):
        """Test that build_deck.py Mode A and Mode B both produce valid output."""
        print("\n📦 LAYER 1: Build Script Integrity")
        print("─" * 50)

        # 1a. Check build_deck.py exists
        if not os.path.exists(BUILD_DECK):
            self.add_result(
                1,
                "build_deck_exists",
                False,
                f"build_deck.py not found at {BUILD_DECK}",
            )
            return
        self.add_result(1, "build_deck_exists", True, "build_deck.py found")

        # 1b. Mode A regression test — content JSON → HTML
        tmp_json = "/tmp/_test_pipeline_content.json"
        tmp_html_a = "/tmp/_test_pipeline_mode_a.html"
        try:
            with open(tmp_json, "w") as f:
                json.dump(SAMPLE_CONTENT_JSON, f)
            result = subprocess.run(
                ["python3", BUILD_DECK, "--content", tmp_json, "--output", tmp_html_a],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and os.path.exists(tmp_html_a):
                size = os.path.getsize(tmp_html_a)
                self.add_result(
                    1, "mode_a_build", True, f"Mode A built OK ({size} bytes)"
                )

                # Validate Mode A output
                val_result = subprocess.run(
                    ["python3", VALIDATE_DECK, tmp_html_a, "--json"],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                if val_result.returncode == 0:
                    val_data = json.loads(val_result.stdout)
                    passed = val_data.get("passed", 0)
                    total = val_data.get("total", 0)
                    self.add_result(
                        1,
                        "mode_a_validate",
                        passed == total,
                        f"Mode A validation: {passed}/{total} checks passed",
                    )
                else:
                    self.add_result(
                        1,
                        "mode_a_validate",
                        False,
                        f"Validator returned exit code {val_result.returncode}",
                    )
            else:
                self.add_result(
                    1,
                    "mode_a_build",
                    False,
                    f"Mode A build failed: {result.stderr[:200]}",
                )
        except Exception as e:
            self.add_result(1, "mode_a_build", False, f"Mode A exception: {e}")
        finally:
            for f in [tmp_json, tmp_html_a]:
                if os.path.exists(f):
                    os.remove(f)

        # 1c. Mode B test — only if we have a deck file (wrapping)
        if self.deck_path and os.path.exists(self.deck_path):
            # Find the original Eos output (before wrapping) — or use the deck itself
            # Check if there's a raw Eos file in outbox
            eos_raw = self._find_eos_raw()
            if eos_raw:
                tmp_html_b = "/tmp/_test_pipeline_mode_b.html"
                try:
                    result = subprocess.run(
                        [
                            "python3",
                            BUILD_DECK,
                            "--wrap",
                            eos_raw,
                            "--output",
                            tmp_html_b,
                        ],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    if result.returncode == 0 and os.path.exists(tmp_html_b):
                        size = os.path.getsize(tmp_html_b)
                        self.add_result(
                            1, "mode_b_build", True, f"Mode B wrap OK ({size} bytes)"
                        )
                    else:
                        self.add_result(
                            1,
                            "mode_b_build",
                            False,
                            f"Mode B failed: {result.stderr[:200]}",
                        )
                except Exception as e:
                    self.add_result(1, "mode_b_build", False, f"Mode B exception: {e}")
                finally:
                    if os.path.exists(tmp_html_b):
                        os.remove(tmp_html_b)
            else:
                self.add_result(
                    1,
                    "mode_b_build",
                    True,
                    "Skipped — no raw Eos output found (deck may already be wrapped)",
                    severity="INFO",
                )

    # ═══════════════════════════════════════════════════════════
    # LAYER 2: VALIDATOR INTEGRITY
    # ═══════════════════════════════════════════════════════════

    def test_layer2_validator_integrity(self):
        """Test that validate_deck.py correctly catches known bad patterns."""
        print("\n🔍 LAYER 2: Validator Integrity")
        print("─" * 50)

        if not os.path.exists(VALIDATE_DECK):
            self.add_result(
                2,
                "validator_exists",
                False,
                f"validate_deck.py not found at {VALIDATE_DECK}",
            )
            return
        self.add_result(2, "validator_exists", True, "validate_deck.py found")

        # 2a. Known-bad HTML (overlay pattern) must FAIL
        bad_html = """<!DOCTYPE html><html><head><style>
        .slide { position: absolute; display: none; }
        .slide.active { display: flex; }
        </style></head><body>
        <div class="slide slide-dark active">Cover</div>
        <div class="slide">Slide 2</div>
        <script>function nextSlide(){}</script>
        </body></html>"""

        tmp_bad = "/tmp/_test_pipeline_bad.html"
        try:
            with open(tmp_bad, "w") as f:
                f.write(bad_html)
            result = subprocess.run(
                ["python3", VALIDATE_DECK, tmp_bad, "--json"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode != 0:
                self.add_result(
                    2, "catch_overlay", True, "Validator correctly rejects overlay HTML"
                )
            else:
                self.add_result(
                    2,
                    "catch_overlay",
                    False,
                    "Validator SHOULD have rejected overlay HTML but returned PASS",
                )
        except Exception as e:
            self.add_result(2, "catch_overlay", False, f"Exception: {e}")
        finally:
            if os.path.exists(tmp_bad):
                os.remove(tmp_bad)

        # 2b. Known-bad: truncated logo must be flagged
        bad_logo_html = """<!DOCTYPE html><html><head>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
        <style>
        .slide { min-height: 640px; }
        @media print { .slide { page-break-after: always; } }
        </style></head><body>
        <button class="print-btn" onclick="window.print()">Print</button>
        <div class="slide slide-dark"><div class="gradient-blob gradient-blob-tr"></div>
        <img src="data:image/png;base64,SHORT_LOGO" style="font-family:Inter">
        <span style="color:#002A3A">#00E273</span></div>
        <div class="slide">Content <div class="so-what">So What</div></div>
        <div class="slide slide-dark">Close</div>
        <script>var x = new IntersectionObserver(function(){});</script>
        </body></html>"""

        tmp_logo = "/tmp/_test_pipeline_badlogo.html"
        try:
            with open(tmp_logo, "w") as f:
                f.write(bad_logo_html)
            result = subprocess.run(
                ["python3", VALIDATE_DECK, tmp_logo, "--json"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            data = json.loads(result.stdout) if result.stdout.strip() else {}
            logo_check = next(
                (d for d in data.get("details", []) if d.get("id") == "logo_base64"),
                None,
            )
            if logo_check and not logo_check.get("passed"):
                self.add_result(
                    2,
                    "catch_truncated_logo",
                    True,
                    "Validator correctly flags truncated logo",
                )
            else:
                self.add_result(
                    2,
                    "catch_truncated_logo",
                    False,
                    "Validator should flag truncated logo but didn't",
                )
        except Exception as e:
            self.add_result(2, "catch_truncated_logo", False, f"Exception: {e}")
        finally:
            if os.path.exists(tmp_logo):
                os.remove(tmp_logo)

    # ═══════════════════════════════════════════════════════════
    # LAYER 3: HTML STRUCTURAL QA (validate_deck.py 15 checks)
    # ═══════════════════════════════════════════════════════════

    def test_layer3_html_qa(self):
        """Run validate_deck.py on the actual deck output."""
        print("\n✅ LAYER 3: HTML Structural QA (15 Checks)")
        print("─" * 50)

        if not self.deck_path or not os.path.exists(self.deck_path):
            self.add_result(
                3, "deck_exists", False, f"Deck file not found: {self.deck_path}"
            )
            return

        self.add_result(
            3,
            "deck_exists",
            True,
            f"Deck found: {self.deck_path} ({os.path.getsize(self.deck_path)} bytes)",
        )

        try:
            result = subprocess.run(
                ["python3", VALIDATE_DECK, self.deck_path, "--json"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            data = json.loads(result.stdout)
            passed = data.get("passed", 0)
            total = data.get("total", 0)
            verdict = data.get("verdict", "UNKNOWN")

            self.add_result(
                3,
                "validator_15_checks",
                passed == total,
                f"Validator: {passed}/{total} PASS (verdict: {verdict})",
            )

            # Log individual failures
            for detail in data.get("details", []):
                if not detail.get("passed"):
                    self.add_result(
                        3,
                        f"check_{detail['id']}",
                        False,
                        detail.get("message", "No message"),
                        severity=detail.get("severity", "CRITICAL"),
                    )
        except Exception as e:
            self.add_result(
                3, "validator_15_checks", False, f"Validator exception: {e}"
            )

    # ═══════════════════════════════════════════════════════════
    # LAYER 4: DATA ACCURACY VERIFICATION (DB comparison)
    # ═══════════════════════════════════════════════════════════

    def test_layer4_data_accuracy(self):
        """Compare data in deck against VPS database."""
        print("\n🔢 LAYER 4: Data Accuracy Verification")
        print("─" * 50)

        if not self.verify_data:
            self.add_result(
                4,
                "data_verify",
                True,
                "Skipped (use --verify-data to enable)",
                severity="INFO",
            )
            return

        if not self.html_content:
            self.add_result(4, "data_verify", False, "No HTML content to verify")
            return

        if not self.gender:
            # Try to auto-detect gender from HTML
            self.gender = self._detect_gender()
            if not self.gender:
                self.add_result(
                    4,
                    "data_verify",
                    False,
                    "Cannot detect gender. Use --gender BABY|MEN|LADIES|...",
                    severity="WARNING",
                )
                return

        print(f"  Querying DB for gender={self.gender}...")

        # Query DB for totals
        db_data = self._query_db_totals()
        if not db_data:
            self.add_result(4, "db_connection", False, "Cannot connect to VPS database")
            return
        self.add_result(4, "db_connection", True, "DB connection OK")

        # Extract numbers from HTML
        deck_data = self._extract_deck_numbers()

        # Compare rankings (series order)
        db_series = self._query_db_series()
        deck_series = self._extract_deck_series()

        if db_series and deck_series:
            # Compare top 5 series ranking order
            db_top5 = [s[0] for s in db_series[:5]]
            deck_top5 = deck_series[:5]
            ranking_match = db_top5 == deck_top5
            self.add_result(
                4,
                "series_ranking",
                ranking_match,
                f"Top 5 ranking: DB={db_top5} vs Deck={deck_top5}",
            )
        else:
            self.add_result(
                4,
                "series_ranking",
                True,
                "Series ranking check skipped (no series data in deck)",
                severity="INFO",
            )

        # Compare total volume (within 20% tolerance for retail-only filtering)
        if db_data.get("total_qty") and deck_data.get("volume"):
            db_vol = db_data["total_qty"]
            deck_vol = deck_data["volume"]
            ratio = deck_vol / db_vol if db_vol > 0 else 0
            # Deck typically shows retail-only (~70-90% of all-channel)
            within_tolerance = 0.5 < ratio < 1.1
            self.add_result(
                4,
                "volume_accuracy",
                within_tolerance,
                f"Volume: Deck={deck_vol:,} vs DB-All={db_vol:,} (ratio={ratio:.1%}). "
                f"{'OK — retail-only subset expected' if within_tolerance else 'MISMATCH — too far off'}",
            )

        # Compare revenue direction
        if db_data.get("total_rev") and deck_data.get("revenue"):
            db_rev = db_data["total_rev"]
            deck_rev = deck_data["revenue"]
            ratio = deck_rev / db_rev if db_rev > 0 else 0
            within_tolerance = 0.5 < ratio < 1.1
            self.add_result(
                4,
                "revenue_accuracy",
                within_tolerance,
                f"Revenue: Deck=Rp{deck_rev / 1e9:.2f}B vs DB-All=Rp{db_rev / 1e9:.2f}B (ratio={ratio:.1%})",
            )

    # ═══════════════════════════════════════════════════════════
    # LAYER 5: VISUAL STRUCTURE CHECK
    # ═══════════════════════════════════════════════════════════

    def test_layer5_visual_structure(self):
        """Deep structural check of slide content, charts, brand elements."""
        print("\n👁️ LAYER 5: Visual Structure Check")
        print("─" * 50)

        if not self.html_content:
            self.add_result(5, "html_loaded", False, "No HTML content to check")
            return

        html = self.html_content

        # 5a. Slide inventory — each slide has content
        slides = re.findall(r'<div\s+class="slide[^"]*"[^>]*id="([^"]*)"', html)
        self.add_result(
            5,
            "slide_ids",
            len(slides) >= 3,
            f"Found {len(slides)} slides with IDs: {slides}",
        )

        # 5b. Dark/Light distribution (cover+closing=dark, content=light)
        dark_slides = len(re.findall(r'class="slide\s+slide-dark', html))
        light_slides = len(slides) - dark_slides
        correct_distribution = dark_slides >= 2 and light_slides >= 1
        self.add_result(
            5,
            "dark_light_distribution",
            correct_distribution,
            f"Dark={dark_slides}, Light={light_slides} "
            f"(expect ≥2 dark for cover+closing, ≥1 light for content)",
        )

        # 5c. Chart canvases exist and have unique IDs
        canvases = re.findall(r'<canvas\s+id="([^"]+)"', html)
        unique_canvases = len(set(canvases)) == len(canvases)
        self.add_result(
            5,
            "chart_canvases",
            unique_canvases,
            f"Chart canvases: {canvases} (unique={unique_canvases})",
            severity="WARNING",
        )

        # 5d. Chart init functions match canvas IDs
        if canvases:
            chart_inits = re.findall(
                r'new Chart\(document\.getElementById\([\'"]([^\'"]+)', html
            )
            init_for_id = re.findall(r"initChart_(\w+)", html)
            # At least some charts should have init code
            has_chart_code = "new Chart" in html
            self.add_result(
                5,
                "chart_init_code",
                has_chart_code,
                f"Chart init code present: {has_chart_code}, "
                f"getElementById refs: {chart_inits}",
            )

        # 5e. So-What boxes on content slides (not cover/closing)
        so_what_count = html.count("so-what") + html.count("So What")
        min_expected = max(
            1, len(slides) - 3
        )  # At least N-3 (minus cover, closing, insights)
        self.add_result(
            5,
            "so_what_coverage",
            so_what_count >= min_expected,
            f"So-What references: {so_what_count} (expected ≥{min_expected})",
        )

        # 5f. No stray overlay patterns (JavaScript navigation leak)
        nav_patterns = [
            ("function nextSlide", "nextSlide() function"),
            ("function prevSlide", "prevSlide() function"),
            ("function showSlide", "showSlide() function"),
            ("currentSlide", "currentSlide variable"),
            (".classList.add('active')", "classList.add('active') pattern"),
        ]
        nav_leaks = []
        for pattern, name in nav_patterns:
            # Only check in <script> blocks, not in comments
            scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.DOTALL)
            for script in scripts:
                if pattern in script:
                    nav_leaks.append(name)
                    break
        self.add_result(
            5,
            "no_nav_leaks",
            len(nav_leaks) == 0,
            f"Navigation JS leaks: {nav_leaks if nav_leaks else 'None detected ✅'}",
        )

        # 5g. Header bands on content slides
        header_bands = re.findall(r'class="header-band"', html)
        self.add_result(
            5,
            "header_bands",
            len(header_bands) >= 1,
            f"Header bands found: {len(header_bands)}",
            severity="WARNING",
        )

        # 5h. Tables have proper structure
        tables = re.findall(r"<table", html)
        if tables:
            has_thead = "<thead>" in html
            has_tbody = "<tbody>" in html
            self.add_result(
                5,
                "table_structure",
                has_thead and has_tbody,
                f"Tables: {len(tables)} found, thead={has_thead}, tbody={has_tbody}",
                severity="WARNING",
            )

        # 5i. Bahasa Indonesia check — key UI elements should be in BI
        bi_indicators = [
            "Analisa",
            "Rekomendasi",
            "Insight",
            "Performa",
            "Total",
            "Revenue",
            "Volume",
            "Toko",
            "toko",
            "pasang",
            "psg",
            "Juta",
            "Miliar",
        ]
        bi_found = [ind for ind in bi_indicators if ind in html]
        self.add_result(
            5,
            "bahasa_indonesia",
            len(bi_found) >= 3,
            f"Bahasa Indonesia indicators: {bi_found[:8]}{'...' if len(bi_found) > 8 else ''}",
            severity="WARNING",
        )

    # ═══════════════════════════════════════════════════════════
    # LAYER 6: DEPLOYMENT VERIFICATION
    # ═══════════════════════════════════════════════════════════

    def test_layer6_deployment(self):
        """Verify Vercel deployment returns HTTP 200 with correct content."""
        print("\n🚀 LAYER 6: Deployment Verification")
        print("─" * 50)

        if not self.vercel_url:
            self.add_result(
                6,
                "deployment",
                True,
                "Skipped (use --vercel-url to check)",
                severity="INFO",
            )
            return

        try:
            result = subprocess.run(
                [
                    "curl",
                    "-s",
                    "-o",
                    "/dev/null",
                    "-w",
                    "%{http_code} %{size_download} %{time_total}",
                    self.vercel_url,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            parts = result.stdout.strip().split()
            if len(parts) >= 3:
                http_code = int(parts[0])
                size = int(float(parts[1]))
                response_time = float(parts[2])

                self.add_result(
                    6,
                    "http_status",
                    http_code == 200,
                    f"HTTP {http_code} (expected 200)",
                )
                self.add_result(
                    6,
                    "response_size",
                    size > 10000,
                    f"Response size: {size:,} bytes (expected >10KB)",
                )
                self.add_result(
                    6,
                    "response_time",
                    response_time < 10.0,
                    f"Response time: {response_time:.2f}s (expected <10s)",
                    severity="WARNING",
                )

                # Verify content matches local file
                if self.html_content:
                    local_size = len(self.html_content.encode("utf-8"))
                    size_match = abs(size - local_size) < 100  # Allow tiny diff
                    self.add_result(
                        6,
                        "size_match",
                        size_match,
                        f"Local={local_size:,} vs Remote={size:,} bytes "
                        f"(diff={abs(size - local_size)})",
                    )
            else:
                self.add_result(
                    6, "http_status", False, f"Unexpected curl output: {result.stdout}"
                )
        except Exception as e:
            self.add_result(6, "deployment", False, f"Deployment check failed: {e}")

    # ═══════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════════

    def _find_eos_raw(self):
        """Find the most recent raw Eos output in outbox/."""
        if not os.path.exists(OUTBOX_DIR):
            return None
        html_files = []
        for f in os.listdir(OUTBOX_DIR):
            path = os.path.join(OUTBOX_DIR, f)
            if f.endswith(".html") and os.path.isfile(path):
                # Skip vercel deploy dirs and wrapped files
                if "vercel" not in f and "wrapped" not in f:
                    html_files.append((os.path.getmtime(path), path))
        if html_files:
            html_files.sort(reverse=True)
            return html_files[0][1]
        return None

    def _detect_gender(self):
        """Try to detect gender category from HTML content."""
        if not self.html_content:
            return None
        genders = {
            "BABY": ["Baby", "BABY", "baby"],
            "MEN": ["Men ", "MEN ", "Pria"],
            "LADIES": ["Ladies", "LADIES", "Wanita"],
            "BOYS": ["Boys", "BOYS"],
            "GIRLS": ["Girls", "GIRLS"],
            "JUNIOR": ["Junior", "JUNIOR"],
            "KIDS": ["Kids", "KIDS", "Anak"],
        }
        for gender_key, patterns in genders.items():
            for p in patterns:
                if p in self.html_content:
                    return gender_key
        return None

    def _query_db_totals(self):
        """Query VPS DB for total sales data."""
        sql = f"""
        SELECT SUM(quantity) as total_qty,
               SUM(total_amount)::bigint as total_rev,
               ROUND(SUM(total_amount)/NULLIF(SUM(quantity),0)) as asp,
               COUNT(DISTINCT article) as num_articles,
               COUNT(DISTINCT matched_store_name) as num_stores
        FROM core.sales_with_product
        WHERE gender = '{self.gender}'
          AND is_intercompany = FALSE
          AND source_entity = 'DDD'
          AND transaction_date >= '2025-01-01'
          AND UPPER(article) NOT LIKE '%SHOPPING BAG%';
        """
        return self._run_sql(sql, single_row=True)

    def _query_db_series(self):
        """Query top series by volume from DB."""
        sql = f"""
        SELECT series, SUM(quantity) as total_qty
        FROM core.sales_with_product
        WHERE gender = '{self.gender}'
          AND is_intercompany = FALSE
          AND source_entity = 'DDD'
          AND transaction_date >= '2025-01-01'
          AND UPPER(article) NOT LIKE '%SHOPPING BAG%'
        GROUP BY series
        ORDER BY total_qty DESC
        LIMIT 10;
        """
        return self._run_sql(sql, single_row=False)

    def _run_sql(self, sql, single_row=False):
        """Execute SQL against VPS DB via psql."""
        try:
            env = os.environ.copy()
            env["PGPASSWORD"] = DB_CONFIG["password"]
            result = subprocess.run(
                [
                    "psql",
                    "-h",
                    DB_CONFIG["host"],
                    "-p",
                    DB_CONFIG["port"],
                    "-U",
                    DB_CONFIG["user"],
                    "-d",
                    DB_CONFIG["dbname"],
                    "-t",
                    "-A",
                    "-F",
                    "|",
                    "-c",
                    sql,
                ],
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
            )
            if result.returncode != 0:
                print(f"  ⚠️ SQL error: {result.stderr[:200]}")
                return None

            lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
            if not lines:
                return None

            if single_row:
                parts = lines[0].split("|")
                if len(parts) >= 5:
                    return {
                        "total_qty": int(parts[0]) if parts[0] else 0,
                        "total_rev": int(parts[1]) if parts[1] else 0,
                        "asp": int(parts[2]) if parts[2] else 0,
                        "num_articles": int(parts[3]) if parts[3] else 0,
                        "num_stores": int(parts[4]) if parts[4] else 0,
                    }
            else:
                rows = []
                for line in lines:
                    parts = line.split("|")
                    if len(parts) >= 2:
                        rows.append(
                            (parts[0].strip(), int(parts[1]) if parts[1].strip() else 0)
                        )
                return rows
        except FileNotFoundError:
            print("  ⚠️ psql not found — install PostgreSQL client or use SSH tunnel")
            return None
        except Exception as e:
            print(f"  ⚠️ DB query failed: {e}")
            return None

    def _extract_deck_numbers(self):
        """Extract key numbers from deck HTML."""
        data = {}
        if not self.html_content:
            return data

        # Try to extract volume (patterns: "52,079 psg", "52.079 pasang", etc.)
        vol_match = re.search(
            r"([\d.,]+)\s*(?:psg|pasang|pairs|prs)", self.html_content, re.IGNORECASE
        )
        if vol_match:
            vol_str = vol_match.group(1).replace(".", "").replace(",", "")
            try:
                data["volume"] = int(vol_str)
            except ValueError:
                pass

        # Try to extract revenue (patterns: "Rp 7.42 M", "Rp 7.42M", etc.)
        rev_match = re.search(
            r"Rp\s*([\d.,]+)\s*(M|Miliar|B|Jt|Juta)", self.html_content, re.IGNORECASE
        )
        if rev_match:
            num = float(rev_match.group(1).replace(",", "."))
            unit = rev_match.group(2).upper()
            if unit in ("M", "MILIAR", "B"):
                data["revenue"] = num * 1e9
            elif unit in ("JT", "JUTA"):
                data["revenue"] = num * 1e6

        return data

    def _extract_deck_series(self):
        """Extract series names from deck tables (in ranking order)."""
        if not self.html_content:
            return []

        # Look for series in table rows (pattern: <td>SERIES_NAME</td> or <strong>SERIES</strong>)
        series_pattern = re.findall(
            r"<td>(?:<strong>)?([A-Z][A-Z &]+?)(?:</strong>)?(?:\s*<span[^>]*>.*?</span>)?</td>",
            self.html_content,
        )
        # Filter to known Zuma series names
        known_series = {
            "VELCRO",
            "CLASSIC",
            "WBB",
            "MICKEY & FRIENDS",
            "DISNEY",
            "TOY STORY",
            "STITCH",
            "COCOMELON",
            "BATMAN",
            "PRINCESS",
            "POOH",
            "MICKEY",
            "LOTSO",
            "MINNIE",
            "MILTON",
            "OXFORD",
            "HELLOKITTY",
            "CLOG",
            "SLIDE",
            "AIRMOVE",
            "LUNA",
            "LUCA",
            "WEDGES",
            "FLIP FLOP",
        }
        return [s.strip() for s in series_pattern if s.strip().upper() in known_series]

    # ═══════════════════════════════════════════════════════════
    # REPORTING
    # ═══════════════════════════════════════════════════════════

    def run_all(self, layers=None):
        """Run specified layers (default: all)."""
        all_layers = {
            1: self.test_layer1_build_integrity,
            2: self.test_layer2_validator_integrity,
            3: self.test_layer3_html_qa,
            4: self.test_layer4_data_accuracy,
            5: self.test_layer5_visual_structure,
            6: self.test_layer6_deployment,
        }

        if layers is None:
            layers = list(all_layers.keys())

        print("=" * 60)
        print("  🧪 ZUMA PIPELINE TEST — Automated QA")
        print(f"  Deck: {self.deck_path or 'N/A'}")
        print(f"  Layers: {layers}")
        print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        for layer_num in layers:
            if layer_num in all_layers:
                all_layers[layer_num]()

        return self.summarize()

    def summarize(self):
        """Generate summary of all test results."""
        elapsed = time.time() - self.start_time
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = [
            r for r in self.results if not r["passed"] and r["severity"] == "CRITICAL"
        ]
        warnings = [
            r for r in self.results if not r["passed"] and r["severity"] == "WARNING"
        ]
        infos = [r for r in self.results if not r["passed"] and r["severity"] == "INFO"]

        if failed:
            verdict = "FAIL"
            icon = "❌"
        elif warnings:
            verdict = "WARN"
            icon = "⚠️"
        else:
            verdict = "PASS"
            icon = "✅"

        summary = {
            "verdict": verdict,
            "total": total,
            "passed": passed,
            "failed": len(failed),
            "warnings": len(warnings),
            "infos": len(infos),
            "elapsed_seconds": round(elapsed, 2),
            "timestamp": datetime.now().isoformat(),
            "deck_path": self.deck_path,
            "results": self.results,
        }

        # Print human-readable report
        print(f"\n{'=' * 60}")
        print(f"  {icon} PIPELINE TEST: {verdict}")
        print(
            f"  Results: {passed}/{total} passed ({len(failed)} critical, {len(warnings)} warnings)"
        )
        print(f"  Duration: {elapsed:.1f}s")
        print(f"{'=' * 60}")

        if failed:
            print(f"\n  ❌ CRITICAL FAILURES ({len(failed)}):")
            for r in failed:
                print(f"    L{r['layer']} {r['test']}: {r['message']}")

        if warnings:
            print(f"\n  ⚠️ WARNINGS ({len(warnings)}):")
            for r in warnings:
                print(f"    L{r['layer']} {r['test']}: {r['message']}")

        if passed > 0:
            print(f"\n  ✅ PASSED ({passed}):")
            for r in self.results:
                if r["passed"]:
                    print(f"    L{r['layer']} {r['test']}: {r['message'][:80]}")

        print(f"\n{'=' * 60}")
        if verdict == "PASS":
            print("  🚀 Pipeline output is production-ready!")
        elif verdict == "WARN":
            print("  ⚡ Deployable with noted warnings.")
        else:
            print("  🚫 DO NOT DEPLOY — fix critical issues first.")
        print(f"{'=' * 60}\n")

        return summary

    def write_report(self, path, summary):
        """Write detailed test report to markdown file."""
        lines = [
            f"# Zuma Pipeline Test Report",
            f"",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Deck:** `{self.deck_path}`",
            f"**Verdict:** {summary['verdict']}",
            f"**Results:** {summary['passed']}/{summary['total']} passed",
            f"**Duration:** {summary['elapsed_seconds']}s",
            f"",
            f"## Results by Layer",
            f"",
        ]

        for layer_num in range(1, 7):
            layer_results = [r for r in self.results if r["layer"] == layer_num]
            if not layer_results:
                continue
            layer_names = {
                1: "Build Script Integrity",
                2: "Validator Integrity",
                3: "HTML Structural QA",
                4: "Data Accuracy Verification",
                5: "Visual Structure Check",
                6: "Deployment Verification",
            }
            lines.append(
                f"### Layer {layer_num}: {layer_names.get(layer_num, 'Unknown')}"
            )
            lines.append("")
            lines.append("| Test | Status | Message |")
            lines.append("|------|--------|---------|")
            for r in layer_results:
                icon = (
                    "✅"
                    if r["passed"]
                    else ("❌" if r["severity"] == "CRITICAL" else "⚠️")
                )
                msg = (
                    r["message"][:60] + "..."
                    if len(r["message"]) > 60
                    else r["message"]
                )
                lines.append(f"| {r['test']} | {icon} | {msg} |")
            lines.append("")

        with open(path, "w") as f:
            f.write("\n".join(lines))
        print(f"📝 Report written to {path}")


def find_latest_deck():
    """Find the most recently modified HTML file in outbox/."""
    if not os.path.exists(OUTBOX_DIR):
        return None
    html_files = []
    for root, dirs, files in os.walk(OUTBOX_DIR):
        # Skip vercel deploy directories
        dirs[:] = [d for d in dirs if "vercel" not in d and ".vercel" not in d]
        for f in files:
            if f.endswith(".html"):
                path = os.path.join(root, f)
                html_files.append((os.path.getmtime(path), path))
    if html_files:
        html_files.sort(reverse=True)
        return html_files[0][1]
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Automated end-to-end pipeline test for Zuma presentation decks"
    )
    parser.add_argument("--deck", "-d", help="Path to deck HTML file to test")
    parser.add_argument(
        "--latest", action="store_true", help="Auto-find latest HTML in outbox/"
    )
    parser.add_argument(
        "--layers", help="Comma-separated layer numbers to test (default: all)"
    )
    parser.add_argument(
        "--verify-data",
        action="store_true",
        help="Enable Layer 4 data accuracy check (requires DB access)",
    )
    parser.add_argument(
        "--gender", help="Gender filter for data verification (BABY, MEN, LADIES, etc.)"
    )
    parser.add_argument("--vercel-url", help="Vercel URL to verify (Layer 6)")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode: layers 1,2,3,5 only (skip DB + Vercel)",
    )
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--report", help="Write markdown report to this path")

    args = parser.parse_args()

    # Resolve deck path
    deck_path = args.deck
    if args.latest:
        deck_path = find_latest_deck()
        if not deck_path:
            print("❌ No HTML files found in outbox/", file=sys.stderr)
            sys.exit(1)
        print(f"📂 Latest deck: {deck_path}")

    # Resolve layers
    layers = None
    if args.layers:
        layers = [int(l.strip()) for l in args.layers.split(",")]
    elif args.quick:
        layers = [1, 2, 3, 5]

    # Run tests
    runner = PipelineTestRunner(
        deck_path=deck_path,
        vercel_url=args.vercel_url,
        gender=args.gender,
        verify_data=args.verify_data,
    )

    summary = runner.run_all(layers=layers)

    if args.json:
        print(json.dumps(summary, indent=2, default=str))

    if args.report:
        runner.write_report(args.report, summary)

    # Exit code
    sys.exit(0 if summary["verdict"] in ("PASS", "WARN") else 1)


if __name__ == "__main__":
    main()
