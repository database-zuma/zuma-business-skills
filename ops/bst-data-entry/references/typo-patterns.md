# Pola Typo Tulisan Tangan BST

Dokumen BST ditulis tangan sehingga sering mengandung kesalahan baca. Referensi ini berisi pola-pola koreksi yang sudah terverifikasi.

## Pola Kode Artikel

### Aturan Umum
1. **Angka ekstra di akhir** — penulis sering menambahkan digit terakhir dari kode yang lebih panjang. Hapus digit ekstra.
2. **Huruf mirip angka** — `I` ↔ `1`, `O` ↔ `0`, `S` ↔ `5`, `Z` ↔ `2`
3. **Huruf mirip huruf** — `Y` ↔ `V`, `U` ↔ `V`, `P` ↔ `R`, `N` ↔ `M`
4. **Penambahan huruf/angka** — kadang ada karakter ekstra yang harus dihapus

### Contoh Koreksi Terverifikasi

| Tulisan Tangan BST | Kode Benar | Penjelasan |
|--------------------|-----------|------------|
| M1SPV2162 | M1SPV216 | Angka `2` ekstra di akhir |
| LIEAV2102 | L1EAV210 | `L` dibaca `L` (ok), `I`→`1`, `E` ok, `A` ok, `V` ok, angka `2` ekstra |
| LISAV2082 | L1SPV208 | `I`→`1`, `SA`→`SP` (huruf A mirip P di tulisan tangan), angka `2` ekstra |
| Z2YB022 | Z2VB02 | `Y`→`V`, angka `2` ekstra |
| L1MR042 | L1MR04 | Angka `2` ekstra di akhir |

### Pola Prefix Kode

| Prefix | Gender/Kategori | Contoh |
|--------|----------------|--------|
| M1 | Men (Pria) | M1SPV216, M1BL03, M1BLV211 |
| L1 | Ladies (Wanita) | L1EAV210, L1SPV208, L1MR04, L1CA26 |
| Z2 | Baby (Bayi) | Z2VB02, Z2CA01, Z2MF01 |
| G2 | Girls (Anak Perempuan) | G2CAV207 |
| B2 | Boys (Anak Laki-laki) | B2TS01, B2TS02 |
| BB2 | Baby Boys | BB2CA01 |

### Pola Seri Kode

| Kode Tengah | Seri | Contoh Lengkap |
|-------------|------|----------------|
| SPV | Stripe (V-series) | M1SPV216 = MEN STRIPE 16 |
| SP | Stripe | M1SP07 = MEN STRIPE 7 |
| BL | Black Series | M1BL03 = MEN BLACK SERIES 3 |
| BLV | Black Series (V) | M1BLV211 = MEN BLACK SERIES 11 |
| CA | Classic | L1CA26 = LADIES CLASSIC 26 |
| CAV | Classic (V) | G2CAV207 = GIRLS CLASSIC 7 |
| CM | Classic Metalic | L1CM03 = LADIES CLASSIC METALIC 3 |
| EA/EAV | Elsa | L1EAV210 = LADIES ELSA 10 |
| MR | Merci | L1MR04 = LADIES MERCI 4 |
| WG | Wedges | L1WG02 = LADIES WEDGES 2 |
| VB | Velcro | Z2VB02 = BABY VELCRO 2 |
| MF | Mickey & Friends | Z2MF01 = BABY COLLAB 1 DISNEY MICKEY & FRIENDS |
| TS | Toy Story | B2TS01 = BOYS TOY STORY 1 |

## Pola Nomor PO

### Aturan Umum Koreksi PO
Tulisan tangan PO sering sulit dibaca. Pola koreksi:

| Tulisan BST | Koreksi | Penjelasan |
|-------------|---------|-----------|
| DNN | DDD | Huruf `N` mirip `D` di tulisan tangan |
| HUS | HJS | Huruf `U` mirip `J`, `S` ok |
| 2S | 25 | Huruf `S` mirip `5` |
| PO(DNN | PO/DDD | Tanda `(` dibaca `/`, `N`→`D` |

### Contoh Lengkap

| Tulisan BST | PO Benar |
|-------------|----------|
| PO(DNN/HUS/2S/XI/021 | PO/DDD/HJS/25/XI/021 |
| PO(DNN/HUS/25/X1/026 | PO/DDD/HJS/25/XI/026 |
| PO(DNN(HUS/25/XI/083 | PO/DDD/HJS/25/XI/083 |
| PO(DNN(HUS/2S/XI/005 | PO/DDD/HJS/25/XI/005 |
| PO(DDD/HJS/25/X/112 | PO/DDD/HJS/25/X/112 |

## Pola Quantity

| Tulisan BST | Interpretasi |
|-------------|-------------|
| 191 + 50 | Total: 241 (dijumlahkan) |
| 50 + 48 | Total: 98 (dijumlahkan) |
| 97 | Total: 97 (angka tunggal) |
| (39/44) | BUKAN qty — ini progress pengiriman, abaikan |
| (38/40) | BUKAN qty — progress, abaikan |
| (36/40) | BUKAN qty — progress, abaikan |

## Cross-Check Warna

Selalu gunakan nama warna di BST untuk konfirmasi kode sudah benar:

| Warna di BST | Kode | Nama Lengkap di Excel |
|-------------|------|----------------------|
| Cocoa White Tan | M1SPV216 | MEN STRIPE 16, COCOA WHITE TAN |
| Silver Navy | L1EAV210 | LADIES ELSA 10, SILVER NAVY |
| Bronze | L1SPV208 | LADIES SLIDE PUFFY 8, BRONZE |
| Cocoa | Z2VB02 | BABY VELCRO 2, COCOA |
| Sage | L1MR04 | LADIES MERCI 4, SAGE |

Jika warna tidak cocok dengan nama artikel di database, kemungkinan kode salah — coba cari kode lain yang cocok warnanya.
