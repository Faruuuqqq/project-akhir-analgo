"""
algo_greedy.py — Algoritma A: Greedy Nearest Neighbor Heuristic.

Kompleksitas:
    Waktu  : O(n²) — loop luar O(n) iterasi, inner cari minimum O(n)
    Ruang  : O(n)  — visited set + route list

Karakteristik:
    [+] Sangat cepat, deterministik, biaya server ≈ 0
    [-] Tidak menjamin rute terpendek — bisa >20% lebih jauh dari optimal

Cara kerja:
    Mulai dari Hub, selalu pergi ke node yang BELUM dikunjungi dan TERDEKAT
    dari posisi saat ini. Ulangi sampai semua node dikunjungi, lalu kembali Hub.
"""

import time


def greedy_nearest_neighbor(matrix: list, hub_id: int, customer_ids: list) -> dict:
    """
    Cari rute pengantaran menggunakan strategi Greedy Nearest Neighbor.

    Algoritma:
        1. Mulai dari hub_id, tambahkan ke visited dan route.
        2. Dari posisi saat ini, cari node terdekat yang belum dikunjungi.
        3. Pindah ke node tersebut, catat ke route dan visited.
        4. Ulangi (2–3) sampai semua customer dikunjungi.
        5. Kembali ke hub_id, tambahkan ke akhir route.

    PENTING: Timing diukur HANYA di sekitar blok algoritma,
             tidak mencakup inisialisasi variabel atau I/O.

    Args:
        matrix       (list[list[float]]): Adjacency matrix jarak (km).
        hub_id       (int)              : ID node Hub (indeks awal & akhir).
        customer_ids (list[int])        : List ID semua customer yang harus dikunjungi.

    Returns:
        dict dengan keys:
            - 'route'         : list[int] — urutan node ID dari Hub ke Hub
            - 'total_distance': float     — total jarak tempuh (km)
            - 'exec_time_ms'  : float     — waktu eksekusi (milidetik)
    """
    # ── START TIMING — hanya sekitar blok algoritma ────────────────────────
    t_start = time.perf_counter()

    # Inisialisasi state
    visited = {hub_id}         # Set node yang sudah dikunjungi (O(1) lookup)
    route   = [hub_id]         # Urutan rute yang dibangun
    current = hub_id           # Posisi kurir saat ini

    # Semua node yang perlu dikunjungi (selain hub)
    all_targets = set(customer_ids)

    # Loop utama: terus bergerak sampai semua customer dikunjungi
    # Kompleksitas: O(n) iterasi luar × O(n) cari minimum = O(n²)
    while len(visited) - 1 < len(all_targets):  # -1 karena hub di visited
        nearest_node = -1
        nearest_dist = float("inf")

        # Inner loop O(n): cari node terdekat yang belum dikunjungi
        for node_id in customer_ids:
            if node_id not in visited:
                dist = matrix[current][node_id]
                # Update jika ditemukan yang lebih dekat
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest_node = node_id

        # Pindah ke node terdekat
        route.append(nearest_node)
        visited.add(nearest_node)
        current = nearest_node

    # Kembali ke Hub setelah semua customer selesai
    route.append(hub_id)

    # ── STOP TIMING ────────────────────────────────────────────────────────
    t_end = time.perf_counter()
    exec_time_ms = (t_end - t_start) * 1000.0

    # Hitung total jarak rute
    total_distance = _calculate_route_distance(matrix, route)

    return {
        "route":          route,
        "total_distance": total_distance,
        "exec_time_ms":   exec_time_ms,
    }


def _calculate_route_distance(matrix: list, route: list) -> float:
    """
    Hitung total jarak dari list rute (urutan node ID).

    Args:
        matrix (list[list[float]]): Adjacency matrix.
        route  (list[int])        : Urutan node ID.

    Returns:
        float: Total jarak (km).
    """
    total = 0.0
    for i in range(len(route) - 1):
        # Jarak dari node ke node berikutnya dalam rute
        total += matrix[route[i]][route[i + 1]]
    return total
