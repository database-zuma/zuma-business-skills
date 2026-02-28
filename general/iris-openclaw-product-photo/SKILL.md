---
name: iris-openclaw-product-photo
description: "Generate prompt spec untuk product photography Zuma — sandal, footwear, apparel. Produces structured JSON/text prompt yang bisa dipakai di Midjourney, DALL-E, Flux, atau brief ke fotografer. Use when: user minta foto produk untuk Shopee/Tokopedia listing, Instagram feed, brand catalog, atau white background e-commerce shots."
user-invocable: false
---

# Product Photography Prompt Generator — Iris OpenClaw

Generate prompt spec untuk foto produk Zuma yang konsisten, professional, dan e-commerce-ready.

## Output Format

Generate dalam 2 format sekaligus:
1. **JSON spec** — untuk AI image gen (Flux, DALL-E, Midjourney)
2. **Brief teks** — untuk fotografer manusia

---

## Template JSON Spec (E-Commerce White Background)

```json
{
  "subject": {
    "product": "[Nama produk + kode SKU]",
    "colorway": "[Warna utama + accent]",
    "size_shown": "[Ukuran yang difoto, misal: 39]",
    "condition": "brand new, clean, unworn"
  },
  "composition": {
    "angle": "[45-degree three-quarter / side profile / top-down / front-facing]",
    "framing": "product fills 75-90% of frame",
    "pair": "[single / paired / stacked]",
    "props": "none (clean product-only shot)"
  },
  "background": {
    "color": "#FFFFFF",
    "pure_white": true,
    "texture": "seamless, no shadows on bg"
  },
  "lighting": {
    "style": "studio three-point lighting",
    "key_light": "soft box, 45-degree from upper left",
    "fill_light": "reflector, right side, 50% intensity",
    "rim_light": "backlight to separate product from background",
    "shadows": "soft drop shadow directly below product"
  },
  "camera": {
    "focal_length": "85mm equivalent",
    "aperture": "f/8 (product fully sharp)",
    "depth_of_field": "deep, all product in focus"
  },
  "quality": {
    "resolution": "4096x4096",
    "format": "PNG",
    "commercial_quality": true,
    "ecommerce_ready": true,
    "catalog_ready": true
  },
  "constraints": {
    "do_not_modify_product_design": true,
    "do_not_hallucinate_details": true,
    "keep_colorway_exact": true,
    "no_watermarks": true,
    "no_text_overlay": true
  }
}
```

---

## Template JSON Spec (Brand / Lifestyle)

```json
{
  "subject": {
    "product": "[Nama produk]",
    "colorway": "[Warna]"
  },
  "scene": {
    "setting": "[Urban street / minimalist studio / outdoor concrete / indoor wood floor]",
    "mood": "[Clean & modern / editorial / street culture]",
    "time_of_day": "golden hour / overcast (for even light)"
  },
  "background": {
    "color": "#002A3A",
    "style": "Zuma brand teal, clean gradient or solid"
  },
  "composition": {
    "angle": "dynamic 45-degree three-quarter",
    "framing": "product center, slight negative space"
  },
  "brand_elements": {
    "color_palette": ["#002A3A", "#00E273", "#FFFFFF"],
    "style": "clean, modern, premium without being luxury"
  },
  "quality": {
    "resolution": "4096x4096",
    "commercial_quality": true
  },
  "constraints": {
    "do_not_modify_product_design": true,
    "maintain_brand_aesthetic": true
  }
}
```

---

## Brief Teks untuk Fotografer

Gunakan template ini kalau brief ke fotografer:

```
BRIEF: [Nama Produk] — E-Commerce Shot

TUJUAN: Foto untuk listing [Shopee/Tokopedia/Instagram feed]

SETUP:
- Background: Pure white seamless (#FFFFFF)
- Lighting: 3-point studio (soft box kiri atas, reflector kanan, rim light belakang)
- Lens: 85mm, f/8 (semua bagian produk sharp)

KOMPOSISI:
- Angle: [45 derajat / side profile / front]
- Produk mengisi 80% frame
- [Single / pair / stacked]
- No props kecuali diminta

WARNA HARUS AKURAT:
- Warna utama: [X]
- Accent: [Y]
- Jangan adjust warna di edit — akurasi warna prioritas

DELIVERABLES:
- Format: PNG, min 2000x2000px
- Retouching: Background bersih, dust/scratch dihilangkan, warna natural
- Jangan tambah teks atau watermark

DEADLINE: [Tanggal]
```

---

## Angle Guide per Platform

| Platform | Recommended Angle | Notes |
|----------|------------------|-------|
| Shopee main listing | 45° three-quarter | Paling convert |
| Shopee detail | Side profile + top-down | Show sole + upper |
| Tokopedia | Same as Shopee | |
| Instagram feed | Lifestyle / editorial | Zuma teal bg |
| Instagram story | Front-facing atau top-down | Vertical crop |
| Brand catalog | Multiple angles | Min 4 shots per SKU |

---

## Variasi Shot per Produk (Rekomendasi)

Untuk satu SKU, idealnya 5 shots:
1. **Hero** — 45° three-quarter, white bg (main listing)
2. **Side profile** — lateral view, show sole
3. **Top-down** — flat lay, see upper pattern
4. **Pair** — kedua sandal/sepatu, styled
5. **Lifestyle** — editorial, Zuma brand bg teal #002A3A

---

## Quick Generate — Input yang Dibutuhkan

Kalau user minta generate prompt, tanya dulu:
1. Nama + kode produk?
2. Warna/colorway?
3. Platform tujuan (Shopee/Tokopedia/Instagram/catalog)?
4. Angle preference?
5. White background atau brand background (teal)?

Lalu generate JSON spec + brief teks sesuai input.
