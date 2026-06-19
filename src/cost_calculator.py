"""
cost_calculator.py — Engine Perhitungan Biaya (Fuel + Server + TCO).

Model Biaya:
    Konsumsi BBM bersifat DINAMIS terhadap beban paket yang tersisa di motor.
    Beban berkurang setiap kali kurir berhasil mengantar di satu titik.

Formula Rasio Konsumsi Dinamis:
    fuel_ratio(W_current) = r_empty + (W_current / W_total) × (r_full - r_empty)

    Contoh: beban 15 kg dari total 30 kg, r_full=0.05, r_empty=0.02:
        fuel_ratio = 0.02 + (15/30) × (0.05 - 0.02) = 0.035 liter/km

TCO (Total Cost of Ownership):
    TCO = Biaya_BBM + Biaya_Server

Break-Even Point:
    Titik harga BBM di mana TCO_Greedy = TCO_Backtracking.
    Di atas titik ini, algoritma eksak lebih menguntungkan.
"""


def calculate_fuel_cost(
    route: list,
    matrix: list,
    packages: dict,
    fuel_model: dict,
    fuel_price_per_liter: float,
) -> dict:
    """
    Hitung biaya BBM dinamis berbasis beban paket per segmen rute.

    NOTES:
        - Beban motor BERKURANG setiap kali kurir mengantar paket (per stop).
        - Ini adalah model DINAMIS — bukan rasio tetap.
        - Segmen terakhir (kembali ke Hub) menggunakan beban = 0 (motor kosong).

    Args:
        route                (list[int])        : Urutan node ID rute (Hub→...→Hub).
        matrix               (list[list[float]]): Adjacency matrix jarak (km).
        packages             (dict)             : {customer_id (int): weight_kg (float)}.
        fuel_model           (dict)             : {'consumption_full_liter_per_km': float,
                                                   'consumption_empty_liter_per_km': float}.
        fuel_price_per_liter (float)            : Harga BBM (Rp/liter).

    Returns:
        dict dengan keys:
            - 'total_liters'     : float — total konsumsi BBM (liter)
            - 'fuel_cost'        : float — total biaya BBM (Rp)
            - 'segment_details'  : list[dict] — detail per segmen (debug/audit)
            - 'w_total'          : float — total berat awal (kg)
    """
    # Parameter fuel model (dibaca dari data — ZERO HARDCODED)
    r_full  = float(fuel_model["consumption_full_liter_per_km"])
    r_empty = float(fuel_model["consumption_empty_liter_per_km"])

    # Hitung W_total: total berat semua paket yang dibawa sejak awal
    # Hanya customer yang ada di rute (sesuai packages)
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

        # ── Beban Berkurang Setelah Delivery ────────────────────────────────
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