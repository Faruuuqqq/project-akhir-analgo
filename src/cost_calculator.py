def calculate_fuel_cost(
    route: list,
    matrix: list,
    packages: dict,
    fuel_model: dict,
    fuel_price_per_liter: float,
) -> dict:
    # Parameter fuel model (dibaca dari data — ZERO HARDCODED)
    r_full  = float(fuel_model["consumption_full_liter_per_km"])
    r_empty = float(fuel_model["consumption_empty_liter_per_km"])

    # Hitung W_total: total berat semua paket yang dibawa sejak awal
    w_total = sum(
        packages.get(node_id, 0.0)
        for node_id in route
        if node_id != route[0]  # skip hub (hub tidak punya paket)
        and node_id != route[-1]  # skip hub di akhir
    )

    # Beban aktual motor saat berangkat = seluruh paket yang akan diantar
    w_current = w_total

    total_liters = 0.0
    segment_details = []

    # Iterasi per segmen rute: (route[0], route[1]), (route[1], route[2]), dst.
    for i in range(len(route) - 1):
        from_node = route[i]
        to_node   = route[i + 1]

        # Jarak segmen ini (km)
        d_ij = matrix[from_node][to_node]

        # ── Formula Rasio Konsumsi Dinamis ──────────────────────────────────
        # Beban saat melintasi segmen ini = w_current (SEBELUM delivery di to_node)
        # Jika w_total = 0 (tidak ada paket), gunakan r_empty
        if w_total > 0:
            fuel_ratio = r_empty + (w_current / w_total) * (r_full - r_empty)
        else:
            fuel_ratio = r_empty

        # Konsumsi BBM segmen ini (liter)
        liter_segmen = d_ij * fuel_ratio

        # Biaya segmen ini (Rp)
        biaya_segmen = liter_segmen * fuel_price_per_liter

        total_liters += liter_segmen

        # Simpan detail segmen untuk transparansi output
        segment_details.append({
            "from":       from_node,
            "to":         to_node,
            "distance_km": d_ij,
            "w_current":  w_current,
            "fuel_ratio": fuel_ratio,
            "liters":     liter_segmen,
            "cost":       biaya_segmen,
        })

        # ── BEBAN BERKURANG SETELAH DELIVERY ────────────────────────────────
        # Setelah tiba di to_node, kurir mengantar paket di sana.
        # Kurangi beban motor dengan berat paket yang diantar.
        # (Hanya jika to_node adalah customer dengan paket)
        w_current -= packages.get(to_node, 0.0)

        # Pastikan beban tidak negatif (floating point edge case)
        if w_current < 0:
            w_current = 0.0

    fuel_cost = total_liters * fuel_price_per_liter

    return {
        "total_liters":    total_liters,
        "fuel_cost":       fuel_cost,
        "segment_details": segment_details,
        "w_total":         w_total,
    }

def calculate_server_cost(exec_time_ms: float, server_cost_per_ms: float) -> float:
    # Hitung biaya komputasi server berdasarkan waktu eksekusi algoritma.
    return exec_time_ms * server_cost_per_ms

def calculate_tco(fuel_cost: float, server_cost: float) -> float:
    # Hitung Total Cost of Ownership (TCO).
    return fuel_cost + server_cost