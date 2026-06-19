# Grafik Perbandingan Eksekusi dan Analisis TCO

Dokumen ini memuat perbandingan antara algoritma **Greedy Nearest Neighbor** dan **DFS Backtracking + Branch-and-Bound Pruning** berdasarkan output aktual program.

- **Tarif server**: Rp 0.0005/ms — dibaca dari [`data/scenarios.json`](../data/scenarios.json) field `server_cost_per_ms`, merepresentasikan biaya komputasi cloud per milidetik sesuai spesifikasi PRD §7.2.
- **Dataset**: 11 node (1 hub + 10 pelanggan area Bandung), total paket 26.0 kg

---

## 1. Perbandingan Waktu Eksekusi

Algoritma Greedy selesai dalam < 1 ms; Backtracking membutuhkan ~2.9 detik. Namun karena tarif server hanya Rp 0.0005/ms, selisih biaya servernya < Rp 2.

```
Waktu Eksekusi (ms)  — skala: setiap █ ≈ 85 ms
─────────────────────────────────────────────────────────────
Algo A (Greedy) │                                    │  0.04 ms
Algo B (Eksak)  │████████████████████████████████████│  2,889 ms
─────────────────────────────────────────────────────────────
```

---

## 2. Perbandingan Total Cost of Ownership (TCO)

TCO = **Biaya BBM** (model konsumsi dinamis berbasis beban) + **Biaya Server** (waktu × Rp 0.0005/ms).  
Dengan tarif server sekecil ini, penentu utama TCO adalah **efisiensi rute**, bukan kecepatan komputasi.

### Skenario: SUBSIDI (Harga BBM Rp 5.000/liter)

| Komponen       | Algoritma A (Greedy) | Algoritma B (Eksak) |
| :------------- | -------------------: | ------------------: |
| Jarak Tempuh   | 51.50 km             | **48.20 km**        |
| Konsumsi BBM   | 1.7343 liter         | **1.6476 liter**    |
| Biaya BBM      | Rp 8.671,48          | **Rp 8.237,98**     |
| Waktu Eksekusi | ~0.04 ms             | ~2.889 ms           |
| Biaya Server   | Rp 0,02              | Rp 1,44             |
| **TCO Total**  | Rp 8.671,62          | **✅ Rp 8.239,28**  |

```
TCO Skenario Subsidi (Rp)  — skala: setiap █ ≈ Rp 256
─────────────────────────────────────────────────────────────
Algo A (Greedy) │█████████████████████████████████████│  Rp 8.672
Algo B (Eksak)  │████████████████████████████████░░░░░│  Rp 8.239 ✅
─────────────────────────────────────────────────────────────
Hemat: Rp 432 menggunakan Algoritma B
```

### Skenario: KRISIS (Harga BBM Rp 20.000/liter)

| Komponen       | Algoritma A (Greedy) | Algoritma B (Eksak) |
| :------------- | -------------------: | ------------------: |
| Jarak Tempuh   | 51.50 km             | **48.20 km**        |
| Konsumsi BBM   | 1.7343 liter         | **1.6476 liter**    |
| Biaya BBM      | Rp 34.685,92         | **Rp 32.951,92**    |
| Waktu Eksekusi | ~0.03 ms             | ~2.907 ms           |
| Biaya Server   | Rp 0,01              | Rp 1,45             |
| **TCO Total**  | Rp 34.685,07         | **✅ Rp 32.952,81** |

```
TCO Skenario Krisis (Rp)  — skala: setiap █ ≈ Rp 1.021
─────────────────────────────────────────────────────────────
Algo A (Greedy) │█████████████████████████████████████│  Rp 34.685
Algo B (Eksak)  │████████████████████████████████░░░░░│  Rp 32.953 ✅
─────────────────────────────────────────────────────────────
Hemat: Rp 1.732 menggunakan Algoritma B
```

---

## 3. Matriks TCO Ringkasan

| Algoritma              | Skenario Subsidi (Rp 5.000/L) | Skenario Krisis (Rp 20.000/L) |
| :--------------------- | ----------------------------: | -----------------------------: |
| Algoritma A (Greedy)   | Rp 8.671,62                   | Rp 34.685,07                   |
| **Algoritma B (Eksak)**| **✅ Rp 8.239,28**            | **✅ Rp 32.952,81**            |

> [!IMPORTANT]
> **Rekomendasi Final: GUNAKAN ALGORITMA B (EKSAK) DI KEDUA SKENARIO**  
> Dengan tarif server Rp 0.0005/ms, biaya komputasi DFS Backtracking hanya **< Rp 2** per pengiriman. Penghematan rute 3.3 km menghasilkan penghematan TCO **Rp 432 – Rp 1.732** per rute — jauh lebih besar dari biaya servernya.

---

## 4. Analisis Break-Even Point

Break-even dihitung sebagai harga BBM di mana TCO Algoritma A = TCO Algoritma B:

```
P_breakeven = (Server_B - Server_A) / (Liter_A - Liter_B)
            = (1.447 - 0.00002) / (1.7343 - 1.6476)
            = 1.447 / 0.0867
            ≈ Rp 17 / liter
```

```
Break-Even Visualization
─────────────────────────────────────────────────────────────────────────
Rp 0      Rp 17      Rp 5.000               Rp 20.000
  │──────────┬──────────────────────────────────────│
             ▲                    ▲                  ▲
           BEP ≈              Skenario            Skenario
           Rp 17            SUBSIDI 📈           KRISIS 📈
                        (B lebih hemat)      (B lebih hemat)
─────────────────────────────────────────────────────────────────────────
```

| Kondisi Harga BBM         | Rekomendasi Algoritma   |
| :------------------------ | :---------------------- |
| **< Rp 17/liter**         | Algoritma A (Greedy)    |
| **≥ Rp 17/liter**         | **Algoritma B (Eksak)** |

Karena kedua skenario (Rp 5.000 dan Rp 20.000) berada **jauh di atas BEP Rp 17/liter**, Algoritma B (Eksak) lebih menguntungkan di semua kondisi yang disimulasikan.
