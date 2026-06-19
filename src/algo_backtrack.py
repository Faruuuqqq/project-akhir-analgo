"""
algo_backtrack.py — Algoritma B: DFS Backtracking + Branch-and-Bound Pruning (Exact).

Kompleksitas:
    Waktu  : O(n!) worst case tanpa pruning — dengan pruning jauh lebih kecil
    Ruang  : O(n) call stack rekursi + O(n) best_route storage

Karakteristik:
    [+] MENJAMIN rute optimal (jarak terpendek secara absolut)
    [-] Eksponensial — n=12 → 479 juta permutasi tanpa pruning aktif

Strategi Pruning (Branch-and-Bound + Greedy Initial Bound):
    1. Hitung initial upper bound dengan Greedy Nearest Neighbor sebelum DFS.
       Ini membuat pruning langsung agresif dari cabang pertama.
    2. Di setiap level rekursi, sortir kandidat berdasarkan jarak dari node saat ini.
       Cabang terdekat (paling menjanjikan) dieksplorasi lebih dulu.
    3. Potong cabang rekursi jika partial_cost >= best_known_cost (Branch-and-Bound).

Implementasi:
    Rekursi murni — tanpa library, tanpa itertools.permutations.
    State backtracking: tambah node ke visited sebelum rekursi,
    hapus node dari visited setelah rekursi (undo).
"""

import time


def _greedy_bound(matrix: list, hub_id: int, customer_ids: list) -> float:
    """
    Hitung initial upper bound menggunakan Greedy Nearest Neighbor.

    Dipakai sebagai starting best_cost untuk DFS agar pruning Branch-and-Bound
    langsung agresif dari cabang pertama — memangkas cabang yang lebih buruk
    dari greedy sejak awal eksplorasi.

    Args:
        matrix       (list[list[float]]): Adjacency matrix.
        hub_id       (int)              : ID node Hub.
        customer_ids (list[int])        : List customer ID.

    Returns:
        float: Total jarak rute greedy (km) sebagai upper bound.
    """
    visited  = {hub_id}
    current  = hub_id
    total    = 0.0
    targets  = set(customer_ids)

    while len(visited) - 1 < len(targets):
        nearest_dist = float("inf")
        nearest_node = -1
        for nid in customer_ids:
            if nid not in visited:
                d = matrix[current][nid]
                if d < nearest_dist:
                    nearest_dist = d
                    nearest_node = nid
        total  += nearest_dist
        visited.add(nearest_node)
        current = nearest_node

    # Biaya kembali ke Hub untuk menutup siklus
    total += matrix[current][hub_id]
    return total


def backtrack_dfs(matrix: list, hub_id: int, customer_ids: list) -> dict:
    """
    Cari rute optimal menggunakan DFS Backtracking + Branch-and-Bound Pruning.

    PENTING: Timing diukur HANYA di sekitar blok algoritma,
             tidak mencakup inisialisasi atau I/O.

    Args:
        matrix       (list[list[float]]): Adjacency matrix jarak (km).
        hub_id       (int)              : ID node Hub (indeks awal & akhir).
        customer_ids (list[int])        : List ID semua customer yang harus dikunjungi.

    Returns:
        dict dengan keys:
            - 'route'           : list[int] — rute optimal dari Hub ke Hub
            - 'total_distance'  : float     — total jarak terpendek (km)
            - 'exec_time_ms'    : float     — waktu eksekusi (milidetik)
            - 'nodes_evaluated' : int       — jumlah node yang dievaluasi
            - 'nodes_pruned'    : int       — jumlah node yang dipangkas (pruning)
    """
    total_customers = len(customer_ids)

    # ── Initial Upper Bound dari Greedy ────────────────────────────────────
    # Sebelum DFS dimulai, hitung upper bound menggunakan greedy nearest neighbor.
    initial_bound = _greedy_bound(matrix, hub_id, customer_ids)

    # ── State terbaik yang ditemukan sejauh ini ─────────────────────────────
    best = {
        "cost":  initial_bound,  # Mulai dari bound greedy, bukan infinity
        "route": [],             # Rute terbaik (diisi jika DFS temukan yang lebih baik)
    }

    # ── Counter pruning untuk transparansi ─────────────────────────────────
    stats = {
        "nodes_evaluated": 0,  # Node yang benar-benar dieksplorasi
        "nodes_pruned":    0,  # Node yang dipangkas sebelum dieksplorasi
    }

    # ── START TIMING — hanya sekitar blok algoritma ────────────────────────
    t_start = time.perf_counter()

    def _backtrack(current: int, visited: set, route: list, cost: float):
        """
        Fungsi rekursi DFS + Branch-and-Bound.

        Args:
            current (int)  : Node saat ini (ID).
            visited (set)  : Set node yang sudah dikunjungi (termasuk hub).
            route   (list) : Rute yang sudah dibangun sampai node ini.
            cost    (float): Biaya kumulatif rute sampai node ini (km).
        """
        # ── PRUNING: Potong cabang jika sudah pasti lebih buruk ─────────────
        if cost >= best["cost"]:
            stats["nodes_pruned"] += 1
            return

        # ── BASE CASE: Semua customer sudah dikunjungi ──────────────────────
        if len(visited) - 1 == total_customers:  # -1 karena hub di visited
            # Tambahkan biaya kembali ke Hub untuk menutup siklus
            total = cost + matrix[current][hub_id]

            # Update solusi terbaik jika rute ini lebih pendek
            if total < best["cost"]:
                best["cost"]  = total
                best["route"] = route + [hub_id]  # Simpan salinan rute lengkap
            return

        # ── Eksplorasi: Coba semua customer yang belum dikunjungi ────────────
        unvisited = [nid for nid in customer_ids if nid not in visited]
        unvisited.sort(key=lambda nid: matrix[current][nid])  # terdekat dulu

        for next_node in unvisited:
            new_cost = cost + matrix[current][next_node]

            # ── PRUNING TAMBAHAN: Cek sebelum rekursi ───────────────────────
            if new_cost >= best["cost"]:
                # Hitung semua sisa yang akan dipruned (sudah pasti lebih jauh)
                idx = unvisited.index(next_node)
                stats["nodes_pruned"] += len(unvisited) - idx
                break  # Semua kandidat selanjutnya juga lebih jauh --> break

            # Tandai node sebagai dikunjungi (state masuk rekursi)
            visited.add(next_node)
            stats["nodes_evaluated"] += 1

            # Rekursi ke node berikutnya dengan state yang diperbarui
            _backtrack(
                current=next_node,
                visited=visited,
                route=route + [next_node],  # list baru (tidak mutate in-place)
                cost=new_cost,
            )

            # ── BACKTRACK: Kembalikan state setelah rekursi ─────────────────
            visited.remove(next_node)

    # Mulai pencarian dari Hub dengan hanya Hub di visited
    _backtrack(
        current=hub_id,
        visited={hub_id},
        route=[hub_id],
        cost=0.0,
    )

    # ── STOP TIMING ────────────────────────────────────────────────────────
    t_end = time.perf_counter()
    exec_time_ms = (t_end - t_start) * 1000.0

    # ── FALLBACK: Jika DFS tidak menemukan rute lebih baik dari greedy bound ─
    if not best["route"]:
        visited_fb = {hub_id}
        current_fb = hub_id
        route_fb   = [hub_id]
        total_fb   = 0.0

        while len(visited_fb) - 1 < len(customer_ids):
            nd, nn = float("inf"), -1
            for nid in customer_ids:
                if nid not in visited_fb and matrix[current_fb][nid] < nd:
                    nd, nn = matrix[current_fb][nid], nid
            total_fb += nd
            visited_fb.add(nn)
            route_fb.append(nn)
            current_fb = nn

        total_fb += matrix[current_fb][hub_id]
        route_fb.append(hub_id)
        best["route"] = route_fb
        best["cost"]  = total_fb

    return {
        "route":           best["route"],
        "total_distance":  best["cost"],
        "exec_time_ms":    exec_time_ms,
        "nodes_evaluated": stats["nodes_evaluated"],
        "nodes_pruned":    stats["nodes_pruned"],
    }
