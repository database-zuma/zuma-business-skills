---
name: markitdown
description: "Convert any file (PDF, Word, Excel, PPT, image, audio, HTML, CSV, JSON, XML, YouTube URL) to Markdown for LLM processing. Microsoft open-source tool, installed at ~/.local/bin/markitdown. Use as PRE-PROCESSING step when user sends/uploads a file that needs to be read, analyzed, or passed to another skill."
user-invocable: false
---

# MarkItDown — Document → Markdown Converter

**Author:** Microsoft AutoGen Team  
**Installed:** `~/.local/bin/markitdown` (v0.0.1a1)  
**Upgrade:** `pip3 install --upgrade 'markitdown[all]'`  
**GitHub:** https://github.com/microsoft/markitdown

---

## Kapan Digunakan

Setiap kali ada **file input dari user** yang perlu dibaca sebelum diproses skill lain:

- User kirim PDF laporan, kontrak, invoice via WA/email
- User upload file Excel untuk dianalisis (bukan dibuat)
- User kirim file Word/PPT untuk diextract isinya
- User kasih URL YouTube yang perlu diambil transcript-nya
- User kirim gambar yang berisi teks/tabel
- File CSV/JSON/XML perlu diconvert ke format LLM-friendly

**Pattern standar:**
```
User kirim file → markitdown convert → markdown string → skill analisis
```

---

## Supported Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| PDF | `.pdf` | Text-based PDF |
| Word | `.docx`, `.doc` | Preserves headings, lists, tables |
| Excel | `.xlsx`, `.xls` | Tiap sheet → tabel markdown |
| PowerPoint | `.pptx` | Tiap slide → section markdown |
| Images | `.jpg`, `.png`, `.gif`, `.bmp`, `.webp` | EXIF + OCR (butuh LLM untuk deskripsi) |
| Audio | `.wav`, `.mp3` | EXIF + speech transcription |
| HTML | `.html`, `.htm` | Strip tags, preserve structure |
| CSV | `.csv` | → tabel markdown |
| JSON | `.json` | → formatted markdown |
| XML | `.xml` | → readable markdown |
| ZIP | `.zip` | Iterates over contents |
| YouTube | URL | Ambil transcript otomatis |
| EPub | `.epub` | E-book content |

---

## CLI Usage

```bash
# Basic — output ke stdout
markitdown file.pdf

# Save ke file
markitdown file.pdf -o output.md
markitdown file.pdf > output.md

# Dari stdin
cat file.pdf | markitdown

# Dengan hint extension (kalau nama file tidak jelas)
markitdown somefile -x pdf

# Dengan Document Intelligence (Azure, lebih akurat untuk PDF kompleks)
markitdown file.pdf -d -e "https://your-endpoint.cognitiveservices.azure.com/"

# Lihat plugins yang terinstall
markitdown --list-plugins
```

---

## Python API

```python
from markitdown import MarkItDown

# Basic
md = MarkItDown()
result = md.convert("report.pdf")
print(result.text_content)

# Convert Excel — semua sheet ke markdown
result = md.convert("data.xlsx")
markdown_tables = result.text_content  # siap dikirim ke LLM

# Dengan LLM untuk deskripsi gambar (PPT dengan images)
from openai import OpenAI
client = OpenAI()
md = MarkItDown(llm_client=client, llm_model="gpt-4o")
result = md.convert("presentation.pptx")

# Convert dari URL YouTube
result = md.convert("https://www.youtube.com/watch?v=...")
transcript = result.text_content
```

---

## Integrasi dengan Skill Lain

### Pattern: File Input → Analisis

```python
# 1. User kirim file Excel untuk dianalisis
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert("sales_report.xlsx")
markdown_content = result.text_content

# 2. Pass ke statistical-analysis atau data-analyst-skill
# markdown_content sekarang bisa di-parse oleh LLM
```

### Pattern: PDF Invoice → Structured Data

```python
# 1. Convert PDF
result = md.convert("invoice_supplier.pdf")

# 2. LLM extract structured data dari markdown
# (pakai zuma-data-analyst-skill atau iris untuk parsing)
```

### Pattern: PPT Lama → Content untuk Deck Baru

```bash
# Extract content dari PPT existing
markitdown old_presentation.pptx > content.md
# Kirim content.md ke Eos untuk rebuild dengan style baru
```

---

## Output Format Notes

- **Excel:** Setiap sheet diconvert ke tabel Markdown. Formula tidak ikut, hanya nilai.
- **PDF:** Text-based PDF bekerja baik. Scanned PDF (gambar) butuh OCR — pakai flag `-d` (Azure Doc Intel) atau upgrade markitdown.
- **Images:** Default hanya EXIF metadata. Untuk OCR/deskripsi, butuh `llm_client` di Python API.
- **YouTube:** Ambil subtitle/transcript jika tersedia. Tidak transkripsi audio secara offline.

---

## Upgrade (Recommended)

Versi terinstall (v0.0.1a1) adalah alpha lama. Versi stabil saat ini ~0.1.x dengan lebih banyak format support:

```bash
pip3 install --upgrade 'markitdown[all]'

# Atau untuk format spesifik saja:
pip3 install 'markitdown[pdf,docx,xlsx,pptx]'
```

---

## Skills Yang Menggunakan Ini

- `xlsx-skill` — saat user upload Excel untuk dibaca (bukan dibuat)
- `statistical-analysis` — saat input data berasal dari file
- `zuma-data-analyst-skill` — saat user kirim file untuk dianalisis
- `iris-openclaw-data-analyst-guided` — saat user upload file untuk guided analysis
