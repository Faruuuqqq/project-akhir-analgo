# Last-Mile Delivery — Algorithm Cost Simulation Pipeline

> **ANALGO-UAS-2026** · Pipeline simulasi CLI untuk membandingkan **Greedy Nearest Neighbor** vs **DFS Backtracking + Branch-and-Bound Pruning** dalam konteks pengantaran paket lokal area Bandung, lengkap dengan model biaya BBM dinamis dan analisis Break-Even Point.

---
### Anggota Kelompok:
1. **Raissa Christable Sebayang** (140810240008) 
2. **Vivian Azarine Widyatna** (140810240014) 
3. **Ibnaty Farah Rabbany** (140810240022) 
4. **Achmad Faruq Mahdison** (140810240080)

## 1. Cara Menjalankan Program

### Prasyarat

- Python 3.8 atau lebih baru
- Tidak ada library eksternal yang diperlukan (hanya library standar Python: `json`, `csv`, `time`, `argparse`, `os`)

### Perintah Eksekusi

```bash
# Jalankan skenario BBM subsidi (Rp 5.000/liter)
python src/main.py --scenario subsidi

# Jalankan skenario BBM krisis (Rp 20.000/liter)
python src/main.py --scenario krisis

# Jalankan KEDUA skenario sekaligus + tampilkan matriks TCO & break-even
python src/main.py --scenario all

# Gunakan direktori data kustom
python src/main.py --scenario all --data-dir ./data/custom/
```

### Struktur Direktori

```
project-akhir-analgo/
├── src/
│   ├── main.py              # Entry point CLI + argparse
│   ├── data_loader.py       # Baca & validasi JSON/CSV input
│   ├── graph.py             # Adjacency matrix builder (list 2D)
│   ├── algo_greedy.py       # Algoritma A: Greedy Nearest Neighbor
│   ├── algo_backtrack.py    # Algoritma B: DFS + Branch-and-Bound
│   ├── cost_calculator.py   # Fuel + server cost + TCO calculator
│   └── reporter.py          # Format & print output CLI
│
├── data/
│   ├── locations.json       # 1 hub + 12 titik pelanggan area Bandung
│   ├── distance_matrix.csv  # Matriks jarak 13×13 (km), simetris, diagonal 0
│   ├── packages.json        # Berat paket per pelanggan + kapasitas motor
│   └── scenarios.json       # Harga BBM skenario & parameter fuel model
│
├── docs/
│   ├── terminal_subsidi.png # Screenshot output CLI skenario subsidi
│   └── terminal_krisis.png  # Screenshot output CLI skenario krisis
│
├── README.md
└── .gitignore
```

### Dataset

- **Hub**: Gudang Pusat - Kiaracondong, Bandung
- **10 Titik Pelanggan**: Dago, Antapani, Cicadas, Buah Batu, Margahayu, Coblong, Sukajadi, Setiabudhi, Ujungberung, Gedebage
- **Total node**: 11 (1 hub + 10 pelanggan)
- **Total berat paket**: 26.0 kg | **Kapasitas motor**: 30.0 kg

---

## 2. Pemilihan Algoritma & Trade-Off

### Algoritma A: Greedy Nearest Neighbor (Heuristik)

**Mengapa Greedy Nearest Neighbor?**

Greedy Nearest Neighbor dipilih karena memiliki keunggulan implementasi yang jelas untuk konteks last-mile delivery:

1. **Deterministic & Intuitif**: Kurir secara natural cenderung bergerak ke titik terdekat berikutnya — pendekatan ini merefleksikan perilaku dunia nyata.
2. **Performa O(n²)**: Dengan 12 pelanggan, algoritma ini selesai dalam hitungan mikrodetik, menjadikan biaya server hampir nol.
3. **Implementasi sederhana**: Tidak memerlukan struktur data kompleks — hanya `set` untuk visited dan `list` untuk route.

**Dibandingkan alternatif:**
- **Random Insertion**: Lebih mahal O(n³) dan hasil tidak konsisten (non-deterministic tanpa seed).
- **Savings Algorithm (Clarke-Wright)**: Cocok untuk multi-vehicle routing (VRP), over-engineered untuk kasus single-vehicle ini.

**Kelemahan jujur**: Greedy tidak menjamin optimalitas — bisa menghasilkan rute >20% lebih jauh dari optimal karena tidak melihat ke depan (*myopic decision*).

---

### Algoritma B: DFS Backtracking + Branch-and-Bound Pruning (Eksak)

**Mengapa DFS Backtracking + Pruning?**

1. **Menjamin optimalitas absolut**: Menjelajahi semua kemungkinan rute (TSP exact), sehingga hasilnya adalah jarak terpendek yang dijamin secara matematis.
2. **Pruning efektif**: Branch-and-Bound memangkas cabang yang partial cost-nya sudah ≥ best known cost. Untuk dataset Bandung ini, pruning memangkas >90% cabang potensial.
3. **Implementasi rekursi murni**: Mudah diverifikasi kekoherensiannya tanpa library eksternal.
4. **Praktis untuk n ≤ 13**: Dengan pruning aktif, n=12 pelanggan bisa diselesaikan dalam waktu wajar.

**Dibandingkan alternatif:**
- **Held-Karp DP**: Kompleksitas waktu O(2ⁿ × n) — lebih cepat secara teoritis, tapi membutuhkan O(2ⁿ × n) memori yang tidak praktis untuk implementasi from-scratch dan sulit diverifikasi.
- **Branch-and-Bound penuh** (dengan lower bound LP): Jauh lebih kompleks untuk diimplementasi dari scratch, membutuhkan pemahaman LP relaxation yang di luar scope project ini.

**Trade-off utama**: DFS Backtracking menghasilkan rute optimal dengan biaya komputasi eksponensial yang signifikan — disinilah inti dilema bisnis project ini.

---

### Ringkasan Trade-Off

| Aspek | Algoritma A (Greedy) | Algoritma B (DFS + Pruning) |
|-------|---------------------|-----------------------------|
| **Kualitas Rute** | Sub-optimal (~10-25% lebih jauh) | **Optimal (terpendek absolut)** |
| **Kecepatan** | **Sangat cepat (< 1 ms)** | Lambat (puluhan–ribuan ms) |
| **Biaya Server** | **Hampir nol** | Signifikan |
| **Biaya BBM** | Tinggi (rute lebih jauh) | **Rendah (rute optimal)** |
| **Rekomendasi** | BBM murah (Subsidi) | BBM mahal (Krisis) |

---

## 3. Analisis Kompleksitas (Big-O)

### Algoritma A — Greedy Nearest Neighbor

**Waktu: O(n²)**

Derivasi:
```
Loop luar  : Berjalan n kali (n = jumlah customer yang belum dikunjungi)
             → Saat iterasi pertama: n node kandidat
             → Saat iterasi ke-i: (n - i + 1) node kandidat

Inner loop : Cari minimum dari sisa unvisited
             → Setiap iterasi: scan O(n) node untuk temukan minimum

Total operasi: n + (n-1) + (n-2) + ... + 1 = n(n+1)/2 = O(n²)
```

Dengan n = 12 pelanggan: 12 × 13 / 2 = **78 operasi perbandingan**.

**Ruang: O(n)**
- `visited` set: menyimpan maksimal n+1 elemen → O(n)
- `route` list: menyimpan n+2 elemen (termasuk hub di awal & akhir) → O(n)

---

### Algoritma B — DFS Backtracking + Branch-and-Bound Pruning

**Waktu: O(n!) worst case — jauh lebih kecil dengan pruning aktif**

Derivasi (worst case tanpa pruning):
```
Pohon rekursi DFS:
  Level 0 (Hub)     : 1 pilihan start
  Level 1           : n pilihan (semua customer)
  Level 2           : n-1 pilihan
  Level 3           : n-2 pilihan
  ...
  Level n           : 1 pilihan

Total permutasi = n × (n-1) × (n-2) × ... × 1 = n!
Untuk n = 12: 12! = 479.001.600 permutasi (tanpa pruning)
```

**Dengan Branch-and-Bound Pruning:**
```
Efektivitas pruning bergantung pada kualitas upper bound awal.
Semakin baik solusi awal yang ditemukan (mis. dari greedy pre-seeding),
semakin agresif pruning dapat memangkas cabang.

Dalam praktiknya untuk dataset Bandung ini:
  - Nodes dievaluasi  : jauh lebih kecil dari 479 juta
  - Nodes dipangkas   : >90% cabang dipangkas sebelum dieksplorasi
```

**Ruang: O(n)**
- Call stack rekursi: kedalaman maksimal = n → O(n) stack frames
- `visited` set: maksimal n+1 elemen → O(n)
- `best_route` storage: n+2 elemen → O(n)
- `route` saat rekursi: dibuat baru tiap level (GC setelah backtrack) → O(n)

---

## 4. Summary & Break-Even Analysis

### Hasil Simulasi Aktual

**Dataset**: 11 node (1 hub + 10 pelanggan area Bandung), total paket 26 kg, kapasitas motor 30 kg.

**Parameter Fuel Model**:
- Konsumsi muatan penuh (r_full): 0.05 liter/km
- Konsumsi motor kosong (r_empty): 0.02 liter/km

| Metrik | Algoritma A (Greedy) | Algoritma B (Eksak) |
|--------|---------------------|---------------------|
| **Rute** | Hub→Cicadas→Antapani→Buah Batu→Margahayu→Gedebage→Ujungberung→Coblong→Dago→Setiabudhi→Sukajadi→Hub | Hub→Cicadas→Buah Batu→Margahayu→Gedebage→Ujungberung→Antapani→Coblong→Sukajadi→Setiabudhi→Dago→Hub |
| **Jarak Total** | 51.50 km | **48.20 km** |
| **Konsumsi BBM** | 1.7343 liter | **1.6476 liter** |
| **Waktu Eksekusi** | **~0.03 ms** | ~2.993 ms |
| **Node Dievaluasi** | N/A | 468.555 |
| **Node Dipruned** | N/A | **884.217 (65.3%)** |

---

### Matriks TCO Aktual

| | Skenario SUBSIDI (Rp 5.000/liter) | Skenario KRISIS (Rp 20.000/liter) |
|---|---|---|
| **Algoritma A (Greedy)** | Rp 8.671,48 | Rp 34.685,92 |
| **Algoritma B (Eksak)** | **Rp 8.239,61** | **Rp 32.953,42** |

---

### Skenario SUBSIDI (BBM Rp 5.000/liter)

- Selisih TCO: **Rp 431,87** — Backtracking lebih hemat
- Meski BBM murah, penghematan 3.3 km rute (×Rp 5.000/liter) lebih besar dari biaya server 3 detik komputasi
- **Rekomendasi: Algoritma B (Eksak)** — lebih hemat meskipun di BBM murah

---

### Skenario KRISIS (BBM Rp 20.000/liter)

- Selisih TCO: **Rp 1.732,50** — Backtracking jauh lebih hemat
- Penghematan rute 3.3 km × Rp 20.000/liter = Rp 1.734 penghematan BBM
- **Rekomendasi: Algoritma B (Eksak)** — penghematan rute optimal mengalahkan biaya server

---

### Break-Even Analysis

**Derivasi Formula Break-Even:**

```
TCO_A(P) = Liter_A × P + Server_A
TCO_B(P) = Liter_B × P + Server_B

Titik break-even adalah P di mana TCO_A = TCO_B:

Liter_A × P + Server_A  =  Liter_B × P + Server_B
(Liter_A - Liter_B) × P  =  Server_B - Server_A

                    Server_B - Server_A
P_breakeven  =  ─────────────────────────────
                    Liter_A - Liter_B
```

**Kalkulasi dari data aktual:**
```
Liter_A     = 1.7343 liter
Liter_B     = 1.6476 liter
Server_A    = 0.03 ms × 0.0005 = Rp 0.000015
Server_B    = 2993.98 ms × 0.0005 = Rp 1.497

Delta_Liter  = 1.7343 - 1.6476 = 0.0867 liter
Delta_Server = 1.497 - 0.000015 = Rp 1.497

P_breakeven = 1.497 / 0.0867 ≈ Rp 17.26/liter  → dibulatkan ~Rp 18/liter
```

**Interpretasi hasil nyata:**
- Break-Even Point: **Rp 18/liter**
- Skenario SUBSIDI (Rp 5.000) → **di bawah break-even** → seharusnya Greedy lebih hemat
- Skenario KRISIS (Rp 20.000) → **di atas break-even** → Backtracking lebih hemat

> **Catatan Penting**: Dalam kasus dataset ini, meskipun Rp 5.000 di bawah break-even teoritis (Rp 18), selisih TCO aktual sangat kecil (Rp 431). Di implementasi nyata dengan beban kurir yang lebih berat dan rute lebih panjang, break-even point akan berubah. Jalankan `python src/main.py --scenario all` untuk mendapatkan break-even dari data terkini.

---

### Implikasi Bisnis

| Kondisi | Rekomendasi | Alasan |
|---------|-------------|--------|
| BBM < Rp 18/liter (di bawah break-even) | **Greedy** | Penghematan komputasi > penghematan rute |
| BBM > Rp 18/liter (di atas break-even) | **Eksak** | Penghematan rute > biaya komputasi tambahan |

**Kesimpulan**: Dengan dataset area Bandung ini, Break-Even Point berada di **Rp 18/liter**. Karena kedua skenario simulasi (Rp 5.000 dan Rp 20.000) berdampak berbeda di sekitar titik ini, manajemen dapat menggunakan angka ini sebagai threshold keputusan algoritmik yang objektif.

---

## Lisensi

Dibuat untuk keperluan akademis — ANALGO-UAS-2026.