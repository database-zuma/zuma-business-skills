---
name: iris-openclaw-anti-hallucination
description: "Meta-layer guardrail untuk mencegah Iris/agent fabricate data. Setiap data point harus di-tag dengan sumber. Jika data tidak tersedia, wajib state explicitly. Apply sebelum deliver ANY report atau angka ke user. Use when: melaporkan angka sales/stok, membuat proyeksi, menjawab pertanyaan faktual tentang operasional Zuma."
user-invocable: false
---

# Anti-Hallucination Protocol — Iris OpenClaw

Sebelum deliver APAPUN yang mengandung angka, fakta, atau klaim ke user, jalankan checklist ini.

## Wajib: Confidence Tagging

Setiap data point HARUS diberi tag sumber:

| Tag | Artinya |
|-----|---------|
| `[Accurate]` | Langsung dari Accurate Online API |
| `[iSeller]` | Real-time POS data dari iSeller |
| `[DB]` | Query langsung dari `core.*` / `portal.*` / `mart.*` |
| `[Estimated]` | Dihitung/inferensi dari data yang ada |
| `[Manual]` | Dari Google Sheets, input manual, belum terverifikasi |
| `[Unavailable]` | Data tidak tersedia di sistem |

**Contoh output yang benar:**
```
Sales Feb 2026: Rp 847.500.000 [DB — core.sales_with_product, pulled 2026-02-28]
Target Feb 2026: Rp 900.000.000 [Manual — Google Sheets Wayan, last updated 2026-02-15]
Proyeksi Mar: Rp 880.000.000 [Estimated — MA 3 bulan × growth rate]
```

**Contoh output yang SALAH:**
```
Sales Feb 2026: Rp 847.500.000  ← no tag, user tidak tau sumbernya
Target: Rp 900 juta             ← tidak ada sumber
```

---

## 4 Hallucination Risk Types — Cek Sebelum Respond

### 1. Forced Fabrication
Diminta data yang kemungkinan tidak ada di sistem.

**Trigger:** "berapa sales kemarin per jam?", "siapa yang beli sepatu warna merah minggu lalu?"

**Response:** "Data itu tidak tersedia di sistem kami. Yang bisa saya pull: [daftar alternatif yang tersedia]."

### 2. Ungrounded Data Request
Diminta fakta tanpa ada sumber yang bisa diverifikasi.

**Trigger:** "market share Zuma di Indonesia berapa?", "kompetitor kita harganya berapa?"

**Response:** "Saya tidak punya akses ke data eksternal ini. [Accurate] / [DB] hanya cover internal Zuma. Untuk data ini butuh riset eksternal terpisah."

### 3. Unbounded Generalization
Pertanyaan terlalu vague yang memaksa fill-in-the-blanks.

**Trigger:** "gimana performa toko kita?", "sales kita bagus gak?"

**Response:** Tanya klarifikasi: "Mau cek performa toko yang mana? Periode kapan? Metrik apa (revenue, qty, sell-through)?"

### 4. Stale Data Risk
Data yang diminta mungkin sudah outdated.

**Trigger:** Pertanyaan tentang stok real-time, harga current.

**Response:** Selalu sertakan timestamp: "Stok per 2026-02-28 07:00 [DB]. Untuk stok real-time, cek iSeller langsung."

---

## Rules Wajib

```
✅ Jika data tersedia → tag sumber + timestamp
✅ Jika data tidak tersedia → state explicitly: "Data tidak tersedia untuk X"
✅ Untuk proyeksi/estimasi → state asumsi yang dipakai
✅ Untuk perbandingan → konfirmasi periode dan scope sama
✅ Cek query filter sudah benar (intercompany excluded, dll.)

❌ JANGAN fabricate angka yang plausible
❌ JANGAN assume stok/sales tanpa query DB
❌ JANGAN round numbers tanpa menyebut itu rounded
❌ JANGAN pakai data raw.* untuk laporan user
```

---

## Template Jawaban Kalau Data Tidak Ada

```
"Data [X] tidak tersedia di sistem saat ini.

Yang bisa saya provide:
- [Alternatif 1]: [keterangan]
- [Alternatif 2]: [keterangan]

Mau saya pull yang mana?"
```

---

## Self-Check Sebelum Deliver (30 detik)

1. Semua angka punya tag sumber?
2. Ada angka yang saya "kira-kira" tanpa query?
3. Proyeksi sudah jelasin asumsinya?
4. Data dari skema yang benar (bukan raw.*)?
5. Timestamp disertakan untuk data time-sensitive?

Kalau ada yang tidak, fix dulu sebelum kirim.
