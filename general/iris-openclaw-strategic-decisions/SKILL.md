---
name: iris-openclaw-strategic-decisions
description: "Framework untuk bantu Wayan buat keputusan strategis. Apply saat user tanya 'should we...?', 'worth it gak...?', 'lebih baik mana...?'. Bukan sekadar pros/cons list — pakai 10-min/10-month/10-year analysis, regret matrix, dan pre-mortem. Use when: keputusan buka toko baru, discontinue produk, ganti supplier, perubahan strategi distribusi."
user-invocable: false
---

# Strategic Decisions Framework — Iris OpenClaw

Untuk keputusan besar yang tidak bisa dijawab dengan data saja. Apply ketika Wayan atau management minta rekomendasi strategis.

## Kapan Pakai

Trigger phrases:
- "worth it gak buka toko di X?"
- "lebih baik mana, A atau B?"
- "kita harusnya lanjut atau stop [initiative]?"
- "gimana menurutmu soal [strategic decision]?"

Jangan pakai untuk: pertanyaan operasional harian, permintaan data, tasks yang punya jawaban jelas.

---

## Framework: 5-Layer Analysis

### Layer 1: Clarify the Real Question

Sering kali pertanyaan yang diajukan bukan pertanyaan yang sebenarnya perlu dijawab.

```
User: "Worth it gak buka toko di Bali?"

Real question mungkin: 
- "Apakah Bali ROI-positive dalam 12 bulan?"
- "Apakah Bali fit dengan brand positioning Zuma?"
- "Apakah kita punya kapasitas operasional untuk ekspansi?"
```

Konfirmasi dulu: "Mau gue analisis dari sudut pandang apa — finansial, operasional, strategic fit, atau semua?"

---

### Layer 2: Second + Third Order Analysis (10/10/10)

Untuk setiap opsi, tanya:

```
10 MENIT ke depan (immediate):
- Apa yang langsung terjadi kalau keputusan ini diambil?
- Resource apa yang langsung dibutuhkan?
- Siapa yang terdampak pertama?

10 BULAN ke depan (medium-term):
- Apa impact-nya di Q3-Q4 tahun ini?
- Apakah membuka atau menutup opsi lain?
- Bagaimana cash flow-nya?

10 TAHUN ke depan (long-term):
- Apakah ini sejalan dengan direction jangka panjang Zuma?
- Opportunity cost-nya apa?
- Kalau gagal, seberapa reversal/recoverable?
```

---

### Layer 3: Regret Matrix

Buat 2x2 matrix:

```
                    AMBIL keputusan | TIDAK ambil
Berhasil:          [outcome A]      | [outcome B — missed opportunity]
Gagal:             [outcome C]      | [outcome D — dodged bullet]
```

Pertanyaan: "Di scenario mana kamu paling bisa hidup dengan keputusannya?"

Regret minimization: Pilih opsi yang, kalau gagal, rasa nyeselnya paling bisa diterima.

---

### Layer 4: Pre-Mortem (Devil's Advocate)

Bayangkan keputusan sudah diambil dan gagal total 6 bulan kemudian.

```
"Kita sudah buka toko Bali, dan sekarang 6 bulan kemudian rugi terus. 
Kenapa ini bisa terjadi?"

Top 5 kemungkinan failure:
1. [Alasan paling likely] → Mitigasi: [...]
2. [Alasan kedua] → Mitigasi: [...]
3. ...
```

Kalau failure modes-nya semuanya mitigatable → proceed. Kalau ada yang tidak bisa dimitigasi → reconsider.

---

### Layer 5: Recommendation

Setelah analisis, deliver rekomendasi yang konkret — jangan fence-sitting.

**Format:**
```
🎯 REKOMENDASI: [Opsi yang disarankan]

ALASAN UTAMA:
• [Alasan 1 — yang paling weight]
• [Alasan 2]
• [Alasan 3]

KONDISI YANG HARUS TERPENUHI:
• [Deal-breaker 1 kalau tidak terpenuhi, jangan proceed]
• [Deal-breaker 2]

LANGKAH PERTAMA (kalau setuju):
• [Action item konkret, siapa yang responsible, kapan]
```

Selalu ada opsi untuk push back: "Kalau [kondisi X] berubah, rekomendasinya bisa berbeda."

---

## Quick Version (untuk keputusan kecil)

Kalau scope-nya tidak terlalu besar, cukup:

```
PRO (konkret, data-backed):
• [Pro 1]
• [Pro 2]

CON (konkret, terutama yang tidak obvious):
• [Con 1]
• [Con 2]

BOTTOM LINE: [Rekomendasi 1 kalimat]
```

---

## Notes

- Selalu acknowledge uncertainty: "Ini analisis dengan data yang ada sekarang. Kalau [asumsi X] berubah, kesimpulannya mungkin berbeda."
- Jangan pretend punya data yang tidak ada (lihat `iris-openclaw-anti-hallucination`)
- Rekomendasi harus konkret — hindari "tergantung situasi" tanpa penjelasan situasi mana yang dimaksud
