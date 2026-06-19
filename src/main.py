"""
main.py — Entry Point CLI Pipeline Simulasi Last-Mile Delivery.

Cara Menjalankan:
    python src/main.py --scenario subsidi
    python src/main.py --scenario krisis
    python src/main.py --scenario all
    python src/main.py --scenario all --data-dir ./data/custom/

Alur Eksekusi:
    1. Parse argumen CLI (--scenario, --data-dir)
    2. Load semua data eksternal via data_loader
    3. Bangun adjacency matrix (graph)
    4. Jalankan Algoritma A (Greedy) + ukur waktu
    5. Jalankan Algoritma B (DFS Backtracking + Pruning) + ukur waktu
    6. Hitung biaya BBM, server, TCO untuk setiap kombinasi algo × skenario
    7. Cetak laporan komparasi ke terminal
    8. Hitung dan cetak Break-Even Point
"""

import argparse
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from data_loader      import load_all, DataValidationError
from graph            import build_graph
from algo_greedy      import greedy_nearest_neighbor
from algo_backtrack   import backtrack_dfs
from cost_calculator  import calculate_all_costs, calculate_break_even_price
from reporter         import (
    print_scenario_header,
    print_algo_result,
    print_comparison,
    print_tco_matrix,
    print_break_even,
)


# CLI Argument Parser
def parse_args() -> argparse.Namespace:
    """
    Parse argumen command-line.
    Returns:
        argparse.Namespace: Objek args dengan atribut scenario dan data_dir.
    """
    parser = argparse.ArgumentParser(
        prog="main.py",
        description=(
            "Pipeline Simulasi Algoritma Rute Last-Mile Delivery\n"
            "Membandingkan Greedy Nearest Neighbor vs DFS Backtracking + Pruning\n"
            "dengan model biaya BBM dinamis berbasis beban paket."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--scenario",
        type=str,
        choices=["subsidi", "krisis", "all"],
        required=True,
        help=(
            "Skenario harga BBM yang akan disimulasikan.\n"
            "  subsidi : Rp 5.000/liter (BBM bersubsidi pemerintah)\n"
            "  krisis  : Rp 20.000/liter (lonjakan harga global)\n"
            "  all     : Jalankan kedua skenario sekaligus"
        ),
    )

    parser.add_argument(
        "--data-dir",
        type=str,
        default="./data",
        help="Direktori data input (default: ./data). Harus berisi locations.json, "
             "distance_matrix.csv, packages.json, scenarios.json.",
    )

    return parser.parse_args()

# Core Simulation
def run_simulation(data: dict, scenario_name: str, scenario_config: dict) -> dict:
    """
    Jalankan satu simulasi untuk satu skenario ekonomi.

    Args:
        data           (dict): Bundle data dari data_loader.load_all().
        scenario_name  (str) : Nama skenario ('subsidi' atau 'krisis').
        scenario_config (dict): Config skenario {'fuel_price_per_liter': ..., ...}.

    Returns:
        dict: Hasil lengkap skenario (algo results + costs).
    """
    matrix      = data["matrix"]
    nodes       = data["nodes"]
    packages    = data["packages"]
    fuel_model  = data["fuel_model"]
    hub_id      = data["hub_id"]

    # Semua customer ID (bukan hub)
    customer_ids = [node["id"] for node in nodes if not node["is_hub"]]

    # Cetak Header Skenario
    print_scenario_header(scenario_name, scenario_config)

    # Algoritma A: Greedy Nearest Neighbor
    greedy_result = greedy_nearest_neighbor(matrix, hub_id, customer_ids)
    greedy_cost   = calculate_all_costs(
        algo_result=greedy_result,
        route=greedy_result["route"],
        matrix=matrix,
        packages=packages,
        scenario_config=scenario_config,
        fuel_model=fuel_model,
    )

    print_algo_result(
        algo_label="ALGORITMA A",
        algo_name="Greedy Nearest Neighbor",
        algo_result=greedy_result,
        cost_result=greedy_cost,
        nodes=nodes,
    )

    # Algoritma B: DFS Backtracking + Pruning
    backtrack_result = backtrack_dfs(matrix, hub_id, customer_ids)
    backtrack_cost   = calculate_all_costs(
        algo_result=backtrack_result,
        route=backtrack_result["route"],
        matrix=matrix,
        packages=packages,
        scenario_config=scenario_config,
        fuel_model=fuel_model,
    )

    print_algo_result(
        algo_label="ALGORITMA B",
        algo_name="Backtracking DFS + Branch-and-Bound Pruning",
        algo_result=backtrack_result,
        cost_result=backtrack_cost,
        nodes=nodes,
    )
    print_comparison(
        scenario_name=scenario_name,
        greedy_result=greedy_result,
        backtrack_result=backtrack_result,
        greedy_cost=greedy_cost,
        backtrack_cost=backtrack_cost,
    )

    return {
        "greedy_result":    greedy_result,
        "backtrack_result": backtrack_result,
        "greedy_cost":      greedy_cost,
        "backtrack_cost":   backtrack_cost,
        "greedy_tco":       greedy_cost["tco"],
        "backtrack_tco":    backtrack_cost["tco"],
    }


# Entry Point
def main():
    """Fungsi utama — orkestrasi keseluruhan pipeline simulasi."""
    args = parse_args()
    data_dir = args.data_dir
    
    if not os.path.isabs(data_dir):
        data_dir = os.path.abspath(data_dir)

    print(f"\n  [INFO] Memuat data dari: {data_dir}")

    try:
        data = load_all(data_dir)
    except FileNotFoundError as e:
        print(f"\n  [ERROR] File tidak ditemukan: {e}")
        print(f"  Pastikan direktori data '{data_dir}' berisi semua file yang diperlukan.")
        sys.exit(1)
    except DataValidationError as e:
        print(f"\n  [ERROR] Validasi data gagal: {e}")
        sys.exit(1)

    n_nodes = data["n_nodes"]
    n_customers = len(data["packages"])
    print(f"  [INFO] Data dimuat: {n_nodes} node ({n_customers} pelanggan + 1 hub)")
    print(f"  [INFO] Total berat paket: {sum(data['packages'].values()):.1f} kg")
    print(f"  [INFO] Kapasitas motor  : {data['motor_capacity']:.1f} kg")

    scenarios_to_run = []
    if args.scenario == "all":
        scenarios_to_run = list(data["scenarios"].items())
    else:
        if args.scenario not in data["scenarios"]:
            print(f"\n  [ERROR] Skenario '{args.scenario}' tidak ditemukan di scenarios.json.")
            print(f"  Skenario tersedia: {list(data['scenarios'].keys())}")
            sys.exit(1)
        scenarios_to_run = [(args.scenario, data["scenarios"][args.scenario])]

    all_results = {}
    for sc_name, sc_config in scenarios_to_run:
        result = run_simulation(data, sc_name, sc_config)
        all_results[sc_name] = result

    if args.scenario == "all" and len(all_results) > 1:
        print_tco_matrix(all_results)

        ref_scenario = list(all_results.values())[0]
        greedy_r     = ref_scenario["greedy_result"]
        bt_r         = ref_scenario["backtrack_result"]
        greedy_f     = ref_scenario["greedy_cost"]["fuel"]
        bt_f         = ref_scenario["backtrack_cost"]["fuel"]

        p_bep = calculate_break_even_price(
            greedy_result=greedy_r,
            backtrack_result=bt_r,
            greedy_fuel=greedy_f,
            backtrack_fuel=bt_f,
            server_cost_per_ms=list(data["scenarios"].values())[0]["server_cost_per_ms"],
        )
        print_break_even(p_bep)

    print()


if __name__ == "__main__":
    main()