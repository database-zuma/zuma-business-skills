# 🖼️ Skill: Image Generation via Gemini 3 Pro Image

**Skill ID:** `zuma-image-gen-skill`
**Category:** General
**Owner:** Iris 🌸 (maintained by Daedalus)
**Last Updated:** 2026-02-19

---

## Description

Generate images using **Gemini 3 Pro Image** via the `google-genai` Python SDK.  
Sub-agents (Metis, Hermes, etc.) can use this skill to generate images autonomously **without asking Iris**.

Default model: `gemini-3-pro-image-preview`

**Model capability:** Multimodal — accepts **text and/or image as input**, produces **image output**.  
Unlike Imagen (text-only prompt), Gemini 3 Pro Image can edit/transform existing images or generate from pure text descriptions.  
Uses the `generate_content` API with `response_modalities=["IMAGE"]`.

---

## Dependencies

```bash
pip install google-genai Pillow
```

Both packages must be available in the Python environment. Run the pip command if unsure.

---

## Environment Variables

| Variable | Description | Where |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API key | `/Users/database-zuma/.openclaw/workspace/.env` |

Load it before running:
```bash
source /Users/database-zuma/.openclaw/workspace/.env
```

Or in Python:
```python
from dotenv import load_dotenv
load_dotenv("/Users/database-zuma/.openclaw/workspace/.env")
```

---

## Python Script Template

Save as e.g. `generate_image.py` and run it, or paste inline in your exec tool call.

```python
#!/usr/bin/env python3
"""
Zuma Image Generation Skill
Model: gemini-3-pro-image-preview (Google Gemini 3 Pro Image)
Multimodal: text and/or image in → image out
Requires: GEMINI_API_KEY env var, google-genai, Pillow
"""

import os
import io
from pathlib import Path
from dotenv import load_dotenv

# --- Load env ---
load_dotenv("/Users/database-zuma/.openclaw/workspace/.env")
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise EnvironmentError("GEMINI_API_KEY not found. Check .env file.")

# --- Config ---
PROMPT = "A futuristic city skyline at sunset, photorealistic"  # ← CHANGE THIS
OUTPUT_PATH = "/tmp/output_image.png"                           # ← CHANGE THIS
MODEL = "gemini-3-pro-image-preview"                            # Default model

# --- Generate ---
from google import genai
from google.genai import types
from PIL import Image

client = genai.Client(api_key=API_KEY)

response = client.models.generate_content(
    model=MODEL,
    contents=PROMPT,
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
    ),
)

# --- Save ---
saved = []
img_index = 0
for part in response.candidates[0].content.parts:
    if part.inline_data is not None:
        image_bytes = part.inline_data.data
        img = Image.open(io.BytesIO(image_bytes))

        out = OUTPUT_PATH if img_index == 0 else OUTPUT_PATH.replace(".png", f"_{img_index}.png")
        img.save(out)
        print(f"✅ Image saved: {out}")
        saved.append(out)
        img_index += 1

if not saved:
    # Print any text response for debugging
    for part in response.candidates[0].content.parts:
        if part.text:
            print(f"[Model text response]: {part.text}")
    raise RuntimeError("No image parts found in response.")
```

---

## Multimodal Input (Image Editing / Image-to-Image)

Gemini 3 Pro Image can also take an **existing image** as input (edit, transform, or re-style):

```python
from google import genai
from google.genai import types
from PIL import Image
import io, os, base64

load_dotenv("/Users/database-zuma/.openclaw/workspace/.env")
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Load source image
with open("/path/to/source_image.png", "rb") as f:
    image_bytes = f.read()

response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=[
        types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
        types.Part.from_text("Make the background a white studio backdrop"),
    ],
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
    ),
)

for part in response.candidates[0].content.parts:
    if part.inline_data is not None:
        img = Image.open(io.BytesIO(part.inline_data.data))
        img.save("/tmp/edited_image.png")
        print("✅ Saved: /tmp/edited_image.png")
```

---

## How to Use (Step-by-Step for Sub-Agents)

### Option A: Inline via `exec` tool

```python
# Paste directly into exec command (adjust PROMPT and OUTPUT_PATH)
import os, io
os.environ.setdefault("GEMINI_API_KEY", open("/Users/database-zuma/.openclaw/workspace/.env").read().split("GEMINI_API_KEY=")[1].split("\n")[0].strip())

from google import genai
from google.genai import types
from PIL import Image

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents="YOUR PROMPT HERE",
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
    ),
)

for part in response.candidates[0].content.parts:
    if part.inline_data is not None:
        img = Image.open(io.BytesIO(part.inline_data.data))
        img.save("/tmp/result.png")
        print("✅ Saved to /tmp/result.png")
```

### Option B: Write a script file then run it

1. Use the `write` tool to create `generate_image.py` with the template above
2. Fill in `PROMPT` and `OUTPUT_PATH`
3. Use `exec` to run: `cd /tmp && source ~/.openclaw/workspace/.env && python3 generate_image.py`

---

## Parameters Reference

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `model` | string | `gemini-3-pro-image-preview` | Gemini 3 Pro Image (multimodal) |
| `contents` | string or list | — | Text prompt, or list of `Part` (text + image for multimodal) |
| `response_modalities` | list | `["IMAGE"]` | Must include `"IMAGE"` to get image output |

---

## Model Options

| Model ID | Tier | Notes |
|---|---|---|
| `gemini-3-pro-image-preview` | **Default** ✅ | Multimodal: text/image in → image out. Best quality & versatility |
| `imagen-4.0-generate-001` | Legacy Standard | Text-only prompt → image. Uses `generate_images` API |
| `imagen-4.0-ultra-001` | Legacy Ultra | Text-only, highest Imagen quality. Uses `generate_images` API |

> **Note:** For Imagen models, use `client.models.generate_images()` with `types.GenerateImagesConfig`.  
> For Gemini 3 Pro Image, use `client.models.generate_content()` with `types.GenerateContentConfig(response_modalities=["IMAGE"])`.

---

## Output

- Image saved as `.png` (or `.jpeg`) to the specified `OUTPUT_PATH`
- To send via WhatsApp: use `message` tool with `media: "/path/to/image.png"`
- To upload to Drive: use `gog` CLI

---

## Example Prompts

```
"A minimalist logo for a fashion brand called Zuma, white background, clean lines"
"Product mockup of a sneaker on a white pedestal, studio lighting, photorealistic"
"Infographic layout template, modern flat design, blue and white color scheme"
"A warm cozy coffee shop interior, golden hour lighting, cinematic"
```

---

## Troubleshooting

| Error | Fix |
|---|---|
| `GEMINI_API_KEY not found` | Source `.env` file or export the variable manually |
| `ModuleNotFoundError: google.genai` | Run `pip install google-genai` |
| `ModuleNotFoundError: PIL` | Run `pip install Pillow` |
| `400 / safety block` | Rephrase prompt; avoid policy-violating content |
| `quota exceeded` | Wait or check Google Cloud quota dashboard |
| `No image parts in response` | Check `response_modalities=["IMAGE"]` is set; check prompt is not blocked |

---

*This skill is maintained by Daedalus on behalf of Iris. Update this file when the API or SDK changes.*
