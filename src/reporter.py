"""
reporter.py — Format & Print Output Terminal CLI.

Bertanggung jawab untuk menghasilkan output terminal yang:
  - Rapi, terstruktur, dan mudah dibaca
  - Menampilkan semua metrik per algoritma: rute, jarak, waktu, BBM, TCO
  - Menyajikan tabel komparasi TCO dua skenario dengan ASCII bar chart
  - Memberikan rekomendasi bisnis berbasis data
  - Mendukung warna ANSI dan mode --verbose untuk detail per segmen
"""
import sys
import io

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
elif hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


# ─── ANSI Color Codes (tanpa library eksternal) ───────────────────────────────
_RESET   = "\033[0m"
_BOLD    = "\033[1m"
_DIM     = "\033[2m"
_YELLOW  = "\033[93m"
_GREEN   = "\033[92m"
_BLUE    = "\033[94m"
_CYAN    = "\033[96m"
_RED     = "\033[91m"

# ─── Global Settings ──────────────────────────────────────────────────────────
_USE_COLOR = True


def configure(use_color: bool = True) -> None:
    """Konfigurasi reporter: aktifkan/nonaktifkan warna ANSI output."""
    global _USE_COLOR
    _USE_COLOR = use_color


def _c(code: str, text: str) -> str:
    """Terapkan kode warna jika warna diaktifkan, reset setelahnya."""
    if _USE_COLOR:
        return f"{code}{text}{_RESET}"
    return text


# Shortcut warna
def _bold(t: str)   -> str: return _c(_BOLD, t)
def _yellow(t: str) -> str: return _c(_YELLOW + _BOLD, t)
def _green(t: str)  -> str: return _c(_GREEN, t)
def _blue(t: str)   -> str: return _c(_BLUE, t)
def _cyan(t: str)   -> str: return _c(_CYAN, t)
def _red(t: str)    -> str: return _c(_RED + _BOLD, t)
def _dim(t: str)    -> str: return _c(_DIM, t)


# ─── Helper Format Angka ──────────────────────────────────────────────────────

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
    """Format volume dalam liter: 2.1343 liter"""
    return f"{liters:.4f} liter"


def _route_to_names(route: list, nodes: list) -> str:
    """Konversi list ID node menjadi string nama: Hub → Dago → Antapani → Hub"""
    id_to_name = {node["id"]: node["name"].split(" - ")[-1] for node in nodes}
    return " → ".join(id_to_name.get(nid, str(nid)) for nid in route)


def _ascii_bar(value: float, max_val: float, width: int = 32) -> str:
    """
    Buat ASCII progress bar proporsional.

    Args:
        value   (float): Nilai yang direpresentasikan.
        max_val (float): Nilai maksimum (setara 100% bar).
        width   (int)  : Lebar bar dalam karakter.

    Returns:
        str: String bar ASCII, misal '█████████████░░░░░░░░░░░░░░░░░░░'
    """
    if max_val <= 0:
        return "░" * width
    filled = min(int((value / max_val) * width), width)
    return "█" * filled + "░" * (width - filled)


# ─── Separator Lines ──────────────────────────────────────────────────────────
_LINE_DOUBLE = "=" * 78
_LINE_SINGLE = "-" * 78

# ─── Main Reporter Functions ──────────────────────────────────────────────────

def print_scenario_header(scenario_name: str, scenario_config: dict) -> None:
    """
    Cetak header skenario simulasi dengan warna kuning.

    Args:
        scenario_name   (str) : Nama skenario ('subsidi' atau 'krisis').
        scenario_config (dict): Config skenario {'fuel_price_per_liter': ..., ...}.
    """
    fuel_price  = float(scenario_config["fuel_price_per_liter"])
    server_rate = float(scenario_config["server_cost_per_ms"])

    print()
    print(_yellow(_LINE_DOUBLE))
    print(_yellow(f"  SIMULASI RUTE LAST-MILE DELIVERY - Skenario: {scenario_name.upper()}"))
    print(_dim(f"  Harga BBM: Rp {int(fuel_price):,}/liter  |  Server: Rp {server_rate}/ms".replace(",", ".")))
    print(_yellow(_LINE_DOUBLE))


def print_algo_result(
    algo_label: str,
    algo_name: str,
    algo_result: dict,
    cost_result: dict,
    nodes: list,
    verbose: bool = False,
) -> None:
    """
    Cetak hasil satu algoritma: rute, jarak, waktu, BBM, server, TCO.

    Args:
        algo_label   (str) : Label singkat, misal 'ALGORITMA A'.
        algo_name    (str) : Nama lengkap algoritma.
        algo_result  (dict): Output dari algo_greedy / algo_backtrack.
        cost_result  (dict): Output dari cost_calculator.calculate_all_costs().
        nodes        (list): List node untuk konversi ID → nama.
        verbose      (bool): Jika True, tampilkan breakdown biaya BBM per segmen.
    """
    route       = algo_result["route"]
    total_dist  = algo_result["total_distance"]
    exec_ms     = algo_result["exec_time_ms"]
    fuel_data   = cost_result["fuel"]
    server_cost = cost_result["server_cost"]
    tco         = cost_result["tco"]

    # Pilih warna berdasarkan algoritma: hijau = A (Greedy), biru = B (Eksak)
    is_a = "ALGORITMA A" in algo_label.upper()
    colorize = _green if is_a else _blue
    label_str = colorize(f"  >> {algo_label}: {algo_name}")

    route_str = _route_to_names(route, nodes)

    print()
    print(label_str)
    print(f"    Rute         : {route_str}")
    print(f"    Jarak Total  : {_bold(_fmt_km(total_dist))}")
    print(f"    Waktu Eksek  : {_fmt_ms(exec_ms)}")
    print(f"    Konsumsi BBM : {_fmt_liter(fuel_data['total_liters'])}")
    print(f"    Biaya BBM    : {_fmt_rp(fuel_data['fuel_cost'])}")
    print(f"    Biaya Server : {_fmt_rp(server_cost)}")
    print(f"    TCO          : {_bold(_fmt_rp(tco))}")

    # Statistik pruning jika tersedia (Algoritma B)
    if "nodes_evaluated" in algo_result:
        ev  = algo_result['nodes_evaluated']
        pru = algo_result['nodes_pruned']
        print(f"    Node Dievaluasi : {_cyan(f'{ev:,}'.replace(',', '.'))}")
        print(f"    Node Dipangkas  : {_cyan(f'{pru:,} (pruning aktif)'.replace(',', '.'))}")

    # ── Verbose: breakdown biaya BBM per segmen ──────────────────────────────
    if verbose and "segment_details" in fuel_data:
        id_to_name = {node["id"]: node["name"].split(" - ")[-1] for node in nodes}
        segs = fuel_data["segment_details"]
        print()
        print(_dim("    ┌─ Detail Biaya BBM Per Segmen " + "─" * 43 + "┐"))
        header = f"    {'Segmen':<30}  {'Jarak':>7}  {'Rasio L/km':>10}  {'Liter':>8}  {'Biaya':>13}"
        print(_dim(header))
        print(_dim("    " + "─" * 75))
        for seg in segs:
            frm  = id_to_name.get(seg["from"], str(seg["from"]))
            to   = id_to_name.get(seg["to"],   str(seg["to"]))
            name = f"{frm} → {to}"
            line = (
                f"    {name:<30}  "
                f"{seg['distance_km']:>6.2f}km  "
                f"{seg['fuel_ratio']:>10.4f}  "
                f"{seg['liters']:>7.4f}L  "
                f"{_fmt_rp(seg['cost']):>13}"
            )
            print(line)
        print(_dim("    └" + "─" * 75 + "┘"))


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
    selisih_jarak_pct = ((dist_a - dist_b) / dist_b * 100.0) if dist_b > 0 else 0.0
    selisih_tco = abs(tco_a - tco_b)

    # Tentukan rekomendasi berdasarkan TCO lebih rendah
    if tco_a <= tco_b:
        rekomendasi = "greedy"
        algo_rekomendasi = _green("GUNAKAN ALGORITMA A (Greedy)")
        alasan = (
            "Di harga BBM ini, kecepatan komputasi greedy\n"
            "                       lebih hemat biaya server dari penghematan rute eksak."
        )
    else:
        rekomendasi = "backtrack"
        algo_rekomendasi = _red("GUNAKAN ALGORITMA B (Eksak)")
        alasan = (
            "Di harga BBM ini, penghematan rute eksak\n"
            "                       jauh mengalahkan biaya server tambahan."
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
    Cetak matriks TCO 2×2 (Algoritma × Skenario) + ASCII bar chart perbandingan.

    Args:
        results_by_scenario (dict): {
            'subsidi': {'greedy_tco': ..., 'backtrack_tco': ...},
            'krisis':  {'greedy_tco': ..., 'backtrack_tco': ...},
        }
    """
    print()
    print(_LINE_DOUBLE)
    print(_bold("  RINGKASAN MATRIKS TCO (Total Cost of Ownership)"))
    print(_LINE_SINGLE)

    # Header tabel
    print(f"  {'':20s}  {'Skenario SUBSIDI':22s}  {'Skenario KRISIS':22s}")
    print(f"  {'':20s}  {'─' * 22}  {'─' * 22}")

    # Ambil nilai TCO
    tco_a_sub = results_by_scenario.get("subsidi", {}).get("greedy_tco",    0.0)
    tco_a_kri = results_by_scenario.get("krisis",  {}).get("greedy_tco",    0.0)
    tco_b_sub = results_by_scenario.get("subsidi", {}).get("backtrack_tco", 0.0)
    tco_b_kri = results_by_scenario.get("krisis",  {}).get("backtrack_tco", 0.0)

    # Baris tabel — gunakan padding ekstra untuk kompensasi ANSI codes
    print(f"  {_green('Algoritma A (Greedy)'):29s}  {_fmt_rp(tco_a_sub):22s}  {_fmt_rp(tco_a_kri):22s}")
    print(f"  {_blue('Algoritma B (Eksak)'):29s}  {_fmt_rp(tco_b_sub):22s}  {_fmt_rp(tco_b_kri):22s}")

    print(_LINE_SINGLE)

    # ── ASCII Bar Chart ───────────────────────────────────────────────────────
    # Visualisasikan selisih TCO A vs B untuk setiap skenario secara proporsional
    bar_width = 34
    print()
    print(_bold("  TCO Bar Chart (perbandingan proporsional):"))
    print()

    for sc_label, tco_a, tco_b in [
        ("SUBSIDI", tco_a_sub, tco_b_sub),
        ("KRISIS",  tco_a_kri, tco_b_kri),
    ]:
        max_val = max(tco_a, tco_b, 1.0)
        bar_a = _ascii_bar(tco_a, max_val, bar_width)
        bar_b = _ascii_bar(tco_b, max_val, bar_width)

        print(f"  {_yellow('[ ' + sc_label + ' ]')}")
        print(f"  {_green('Algo A')} │{_green(bar_a)}│ {_fmt_rp(tco_a)}")
        print(f"  {_blue('Algo B')} │{_blue(bar_b)}│ {_fmt_rp(tco_b)}")
        # Hitung winner
        winner = _green("← A lebih hemat") if tco_a <= tco_b else _red("← B lebih hemat")
        print(f"         {'':34s}  {winner}")
        print()

    print(_LINE_DOUBLE)


def print_break_even(p_breakeven: float) -> None:
    """
    Cetak analisis Break-Even Point harga BBM.

    Args:
        p_breakeven (float): Harga BBM break-even (Rp/liter).
    """
    print()
    print(_bold("  ANALISIS BREAK-EVEN POINT"))
    print(_LINE_SINGLE)

    if p_breakeven == float("inf"):
        print("  Break-Even : Tidak ada (kedua rute identik — jarak sama)")
    elif p_breakeven <= 0:
        print(f"  Break-Even : {_red('Algoritma B SELALU lebih hemat di semua harga BBM')}")
    else:
        bep_str = f"Rp {int(p_breakeven):,}/liter".replace(",", ".")
        print(f"  Break-Even : {_cyan(_bold(bep_str))}")
        print(f"  Artinya    : Di atas {bep_str}, {_red('Algoritma B (Eksak) lebih menguntungkan')}.")
        print(f"               Di bawah {bep_str}, {_green('Algoritma A (Greedy) lebih ekonomis')}.")

    print(_LINE_SINGLE)
