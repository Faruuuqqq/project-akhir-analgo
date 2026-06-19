"""
reporter.py — Format & Print Output Terminal CLI.

Bertanggung jawab untuk menghasilkan output terminal yang:
  - Rapi, terstruktur, dan mudah dibaca
  - Menampilkan semua metrik per algoritma: rute, jarak, waktu, BBM, TCO
  - Menyajikan tabel komparasi TCO dua skenario
  - Memberikan rekomendasi bisnis berbasis data
"""
import sys
import io

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
elif hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


# Helper Format Angka
def _fmt_rp(amount: float) -> str:
    """Format angka sebagai Rupiah Indonesia: Rp 42.800,16"""
    integer_part = int(amount)
    decimal_part = amount - integer_part

    int_str = f"{integer_part:,}".replace(",", ".")
    dec_str = f"{decimal_part:.2f}"[1:].replace(".", ",")

    return f"Rp {int_str}{dec_str}"


def _fmt_km(distance: float) -> str:
    """Format jarak dalam km: 47.30 km"""
    return f"{distance:.2f} km"


def _fmt_ms(ms: float) -> str:
    """Format waktu dalam milidetik: 1.842,70 ms"""
    integer_part = int(ms)
    decimal_part = ms - integer_part
    int_str = f"{integer_part:,}".replace(",", ".")
    dec_str = f"{decimal_part:.2f}"[1:].replace(".", ",")
    return f"{int_str}{dec_str} ms"


def _fmt_liter(liters: float) -> str:
    """Format volume dalam liter: 2.14 liter"""
    return f"{liters:.4f} liter"


def _route_to_names(route: list, nodes: list) -> str:
    """Konversi list ID node menjadi string nama: Hub → Dago → Antapani → Hub"""
    id_to_name = {node["id"]: node["name"].split(" - ")[-1] for node in nodes}
    return " → ".join(id_to_name.get(nid, str(nid)) for nid in route)


# Separator Lines
_LINE_DOUBLE = "=" * 78
_LINE_SINGLE = "-" * 78
_ARROW       = ">>"

# Main Reporter Functions
def print_scenario_header(scenario_name: str, scenario_config: dict) -> None:
    """
    Cetak header skenario simulasi.

    Args:
        scenario_name   (str) : Nama skenario ('SUBSIDI' atau 'KRISIS').
        scenario_config (dict): Config skenario {'fuel_price_per_liter': ..., ...}.
    """
    fuel_price   = float(scenario_config["fuel_price_per_liter"])
    server_rate  = float(scenario_config["server_cost_per_ms"])

    print()
    print(_LINE_DOUBLE)
    print(f"  SIMULASI RUTE LAST-MILE DELIVERY - Skenario: {scenario_name.upper()}")
    print(f"  Harga BBM: Rp {int(fuel_price):,}/liter  |  Server: Rp {server_rate}/ms".replace(",", "."))
    print(_LINE_DOUBLE)


def print_algo_result(
    algo_label: str,
    algo_name: str,
    algo_result: dict,
    cost_result: dict,
    nodes: list,
) -> None:
    """
    Cetak hasil satu algoritma: rute, jarak, waktu, BBM, server, TCO.

    Args:
        algo_label   (str) : Label singkat, misal 'ALGORITMA A'.
        algo_name    (str) : Nama lengkap algoritma.
        algo_result  (dict): Output dari algo_greedy / algo_backtrack.
        cost_result  (dict): Output dari cost_calculator.calculate_all_costs().
        nodes        (list): List node untuk konversi ID → nama.
    """
    route          = algo_result["route"]
    total_dist     = algo_result["total_distance"]
    exec_ms        = algo_result["exec_time_ms"]
    fuel_data      = cost_result["fuel"]
    server_cost    = cost_result["server_cost"]
    tco            = cost_result["tco"]

    route_str = _route_to_names(route, nodes)

    print()
    print(f"  >> {algo_label}: {algo_name}")
    print(f"    Rute         : {route_str}")
    print(f"    Jarak Total  : {_fmt_km(total_dist)}")
    print(f"    Waktu Eksek  : {_fmt_ms(exec_ms)}")
    print(f"    Konsumsi BBM : {_fmt_liter(fuel_data['total_liters'])}")
    print(f"    Biaya BBM    : {_fmt_rp(fuel_data['fuel_cost'])}")
    print(f"    Biaya Server : {_fmt_rp(server_cost)}")
    print(f"    TCO          : {_fmt_rp(tco)}")

    # Tampilkan statistik pruning jika tersedia (Algoritma B)
    if "nodes_evaluated" in algo_result:
        print(f"    Node Dievaluasi : {algo_result['nodes_evaluated']:,}".replace(",", "."))
        print(f"    Node Dipangkas  : {algo_result['nodes_pruned']:,} (pruning aktif)".replace(",", "."))


def print_comparison(
    scenario_name: str,
    greedy_result: dict,
    backtrack_result: dict,
    greedy_cost: dict,
    backtrack_cost: dict,
) -> str:
    """
    Cetak tabel komparasi TCO antara dua algoritma dan beri rekomendasi.

    Args:
        scenario_name    (str): Nama skenario.
        greedy_result    (dict): Hasil algo greedy.
        backtrack_result (dict): Hasil algo backtrack.
        greedy_cost      (dict): Biaya greedy.
        backtrack_cost   (dict): Biaya backtrack.

    Returns:
        str: 'greedy' atau 'backtrack' — rekomendasi algoritma.
    """
    dist_a = greedy_result["total_distance"]
    dist_b = backtrack_result["total_distance"]
    tco_a  = greedy_cost["tco"]
    tco_b  = backtrack_cost["tco"]

    # Hitung selisih jarak (persentase greedy lebih jauh dari optimal)
    if dist_b > 0:
        selisih_jarak_pct = ((dist_a - dist_b) / dist_b) * 100.0
    else:
        selisih_jarak_pct = 0.0

    selisih_tco = abs(tco_a - tco_b)

    # Tentukan rekomendasi berdasarkan TCO lebih rendah
    if tco_a <= tco_b:
        rekomendasi = "greedy"
        algo_rekomendasi = "GUNAKAN ALGORITMA A (Greedy)"
        alasan = (
            f"Di harga BBM ini, kecepatan komputasi greedy\n"
            f"                       lebih hemat biaya server dari penghematan rute eksak."
        )
    else:
        rekomendasi = "backtrack"
        algo_rekomendasi = "GUNAKAN ALGORITMA B (Eksak)"
        alasan = (
            f"Di harga BBM ini, penghematan rute eksak\n"
            f"                       jauh mengalahkan biaya server tambahan."
        )

    print()
    print(_LINE_DOUBLE)
    print(f"  KOMPARASI TCO - Skenario {scenario_name.upper()}")
    print(_LINE_SINGLE)
    print(f"    Selisih Jarak   : Greedy {selisih_jarak_pct:+.1f}% lebih jauh dari rute optimal")
    print(f"    Selisih TCO     : {_fmt_rp(selisih_tco)} ({'Backtracking' if rekomendasi == 'backtrack' else 'Greedy'} lebih hemat)")
    print(f"    Rekomendasi     : {algo_rekomendasi}")
    print(f"    Alasan          : {alasan}")
    print(_LINE_DOUBLE)

    return rekomendasi


def print_tco_matrix(results_by_scenario: dict) -> None:
    """
    Cetak matriks TCO 2×2 (Algoritma × Skenario) sebagai ringkasan akhir.
    """
    print()
    print(_LINE_DOUBLE)
    print("  RINGKASAN MATRIKS TCO (Total Cost of Ownership)")
    print(_LINE_SINGLE)

    # Header tabel
    print(f"  {'':20s}  {'Skenario SUBSIDI':22s}  {'Skenario KRISIS':22s}")
    print(f"  {'':20s}  {'─' * 22}  {'─' * 22}")

    # Baris Algoritma A
    tco_a_sub = results_by_scenario.get("subsidi", {}).get("greedy_tco", 0.0)
    tco_a_kri = results_by_scenario.get("krisis", {}).get("greedy_tco", 0.0)
    print(f"  {'Algoritma A (Greedy)':20s}  {_fmt_rp(tco_a_sub):22s}  {_fmt_rp(tco_a_kri):22s}")

    # Baris Algoritma B
    tco_b_sub = results_by_scenario.get("subsidi", {}).get("backtrack_tco", 0.0)
    tco_b_kri = results_by_scenario.get("krisis", {}).get("backtrack_tco", 0.0)
    print(f"  {'Algoritma B (Eksak)':20s}  {_fmt_rp(tco_b_sub):22s}  {_fmt_rp(tco_b_kri):22s}")

    print(_LINE_DOUBLE)


def print_break_even(p_breakeven: float) -> None:
    """
    Cetak analisis Break-Even Point.

    Args:
        p_breakeven (float): Harga BBM break-even (Rp/liter).
    """
    print()
    print("  ANALISIS BREAK-EVEN POINT")
    print(_LINE_SINGLE)

    if p_breakeven == float("inf"):
        print("  Break-Even : Tidak ada (kedua rute identik — jarak sama)")
    elif p_breakeven <= 0:
        print("  Break-Even : Algoritma B SELALU lebih hemat di semua harga BBM")
    else:
        print(f"  Break-Even : Rp {int(p_breakeven):,}/liter".replace(",", "."))
        print(f"  Artinya    : Di atas Rp {int(p_breakeven):,}/liter, ".replace(",", ".") +
              "Algoritma B (Eksak) lebih menguntungkan.")
        print(f"               Di bawah Rp {int(p_breakeven):,}/liter, ".replace(",", ".") +
              "Algoritma A (Greedy) lebih ekonomis.")
    print(_LINE_SINGLE)
