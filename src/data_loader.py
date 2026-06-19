"""
data_loader.py — Modul pembaca & validator semua file input eksternal.

Bertanggung jawab untuk:
  - Membaca locations.json   → list node {id, name, is_hub}
  - Membaca distance_matrix.csv → list 2D (adjacency matrix)
  - Membaca packages.json   → dict {customer_id: weight_kg} + motor_capacity_kg
  - Membaca scenarios.json  → config harga BBM & fuel model
  - Validasi: simetri matriks, nilai non-negatif, jumlah node konsisten
"""

import json
import csv
import os


class DataValidationError(Exception):
    """Exception khusus untuk error validasi data input."""
    pass


def load_locations(data_dir: str) -> list:
    """
    Baca locations.json dan kembalikan list node.

    Returns:
        list[dict]: Setiap dict berisi keys: 'id', 'name', 'is_hub'.

    Raises:
        FileNotFoundError: Jika file tidak ditemukan.
        DataValidationError: Jika format data tidak valid.
    """
    filepath = os.path.join(data_dir, "locations.json")

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Validasi struktur
    if "nodes" not in data:
        raise DataValidationError("locations.json harus memiliki key 'nodes'.")

    nodes = data["nodes"]
    if len(nodes) < 2:
        raise DataValidationError("Minimal 2 node diperlukan (1 hub + 1 pelanggan).")

    # Pastikan ada minimal 1 hub
    hub_count = sum(1 for n in nodes if n.get("is_hub", False))
    if hub_count != 1:
        raise DataValidationError(
            f"Harus ada tepat 1 node dengan is_hub=true, ditemukan: {hub_count}."
        )

    # Validasi field wajib per node
    for node in nodes:
        for key in ("id", "name", "is_hub"):
            if key not in node:
                raise DataValidationError(
                    f"Node ID {node.get('id', '?')} tidak memiliki field '{key}'."
                )

    return nodes


def load_distance_matrix(data_dir: str) -> list:
    """
    Baca distance_matrix.csv dan bangun list 2D adjacency matrix.

    Format CSV:
        Baris pertama: header (node_id, 0, 1, 2, ...)
        Baris berikutnya: row_id, jarak_ke_0, jarak_ke_1, ...

    Returns:
        list[list[float]]: Adjacency matrix simetris dengan diagonal 0.

    Raises:
        DataValidationError: Jika matriks tidak simetris atau ada nilai negatif.
    """
    filepath = os.path.join(data_dir, "distance_matrix.csv")

    matrix = []
    with open(filepath, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)  # skip header row (node_id, 0, 1, 2, ...)
        _ = header  # header tidak dipakai, tapi dibaca untuk di-skip

        for row in reader:
            if not row:
                continue
            # Kolom pertama adalah node_id (label), skip — ambil sisa sebagai jarak
            distances = [float(val) for val in row[1:]]
            matrix.append(distances)

    n = len(matrix)

    # Validasi dimensi (harus matriks persegi)
    for i, row in enumerate(matrix):
        if len(row) != n:
            raise DataValidationError(
                f"Baris {i} memiliki {len(row)} kolom, harusnya {n} (matriks persegi)."
            )

    # Validasi nilai non-negatif
    for i in range(n):
        for j in range(n):
            if matrix[i][j] < 0:
                raise DataValidationError(
                    f"Nilai negatif terdeteksi: matrix[{i}][{j}] = {matrix[i][j]}."
                )

    # Validasi diagonal = 0
    for i in range(n):
        if matrix[i][i] != 0.0:
            raise DataValidationError(
                f"Diagonal tidak nol: matrix[{i}][{i}] = {matrix[i][i]}."
            )

    # Validasi simetri: matrix[i][j] == matrix[j][i]
    tolerance = 1e-9  # toleransi floating point
    for i in range(n):
        for j in range(i + 1, n):
            if abs(matrix[i][j] - matrix[j][i]) > tolerance:
                raise DataValidationError(
                    f"Matriks tidak simetris: matrix[{i}][{j}]={matrix[i][j]} "
                    f"!= matrix[{j}][{i}]={matrix[j][i]}."
                )

    return matrix


def load_packages(data_dir: str) -> tuple:
    """
    Baca packages.json.

    Returns:
        tuple:
            - dict: {customer_id (int): weight_kg (float)}
            - float: motor_capacity_kg

    Raises:
        DataValidationError: Jika format tidak valid atau berat negatif.
    """
    filepath = os.path.join(data_dir, "packages.json")

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Validasi field wajib
    if "motor_capacity_kg" not in data:
        raise DataValidationError("packages.json harus memiliki 'motor_capacity_kg'.")
    if "packages" not in data:
        raise DataValidationError("packages.json harus memiliki 'packages'.")

    motor_capacity = float(data["motor_capacity_kg"])
    if motor_capacity <= 0:
        raise DataValidationError(f"motor_capacity_kg harus positif, dapat: {motor_capacity}.")

    packages = {}
    total_weight = 0.0
    for pkg in data["packages"]:
        cid = int(pkg["customer_id"])
        wkg = float(pkg["weight_kg"])
        if wkg < 0:
            raise DataValidationError(
                f"Berat paket pelanggan {cid} negatif: {wkg}."
            )
        packages[cid] = wkg
        total_weight += wkg

    # Peringatan jika total berat melebihi kapasitas
    if total_weight > motor_capacity:
        print(
            f"[PERINGATAN] Total berat paket ({total_weight:.1f} kg) "
            f"melebihi kapasitas motor ({motor_capacity:.1f} kg). "
            "Perhitungan tetap berjalan (single-trip assumption)."
        )

    return packages, motor_capacity


def load_scenarios(data_dir: str) -> dict:
    """
    Baca scenarios.json.

    Returns:
        dict dengan struktur:
            {
                "scenarios": {
                    "subsidi": {"fuel_price_per_liter": ..., "server_cost_per_ms": ...},
                    "krisis":  {"fuel_price_per_liter": ..., "server_cost_per_ms": ...}
                },
                "fuel_model": {
                    "consumption_full_liter_per_km":  ...,
                    "consumption_empty_liter_per_km": ...
                }
            }

    Raises:
        DataValidationError: Jika skenario tidak lengkap atau nilai tidak valid.
    """
    filepath = os.path.join(data_dir, "scenarios.json")

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Validasi struktur level atas
    for key in ("scenarios", "fuel_model"):
        if key not in data:
            raise DataValidationError(f"scenarios.json harus memiliki key '{key}'.")

    # Validasi setiap skenario
    for sc_name, sc_data in data["scenarios"].items():
        for field in ("fuel_price_per_liter", "server_cost_per_ms"):
            if field not in sc_data:
                raise DataValidationError(
                    f"Skenario '{sc_name}' tidak memiliki field '{field}'."
                )
            if float(sc_data[field]) < 0:
                raise DataValidationError(
                    f"Skenario '{sc_name}'.{field} tidak boleh negatif."
                )

    # Validasi fuel model
    fm = data["fuel_model"]
    for field in ("consumption_full_liter_per_km", "consumption_empty_liter_per_km"):
        if field not in fm:
            raise DataValidationError(
                f"fuel_model tidak memiliki field '{field}'."
            )

    r_full = float(fm["consumption_full_liter_per_km"])
    r_empty = float(fm["consumption_empty_liter_per_km"])
    if r_empty > r_full:
        raise DataValidationError(
            f"Konsumsi kosong ({r_empty}) tidak boleh lebih besar dari penuh ({r_full})."
        )

    return data


def load_all(data_dir: str = "./data") -> dict:
    """
    Load semua file input sekaligus dan kembalikan sebagai satu bundle dict.

    Returns:
        dict dengan keys:
            - 'nodes'          : list node dari locations.json
            - 'matrix'         : adjacency matrix 2D dari distance_matrix.csv
            - 'packages'       : dict {customer_id: weight_kg}
            - 'motor_capacity' : float kapasitas motor (kg)
            - 'scenarios'      : dict skenario ekonomi
            - 'fuel_model'     : dict parameter fuel model
            - 'hub_id'         : int id node hub
            - 'n_nodes'        : int total jumlah node

    Raises:
        DataValidationError: Jika ada inkonsistensi antar file.
    """
    nodes = load_locations(data_dir)
    matrix = load_distance_matrix(data_dir)
    packages, motor_capacity = load_packages(data_dir)
    scenario_data = load_scenarios(data_dir)

    n_nodes = len(nodes)

    # Validasi konsistensi: jumlah node di locations harus cocok dengan ukuran matriks
    if len(matrix) != n_nodes:
        raise DataValidationError(
            f"Jumlah node di locations.json ({n_nodes}) tidak cocok dengan "
            f"ukuran matriks ({len(matrix)}x{len(matrix)})."
        )

    # Validasi: semua customer_id di packages harus ada di nodes
    node_ids = {node["id"] for node in nodes}
    for cid in packages:
        if cid not in node_ids:
            raise DataValidationError(
                f"customer_id {cid} di packages.json tidak ada di locations.json."
            )

    # Temukan hub_id
    hub_id = next(node["id"] for node in nodes if node["is_hub"])

    return {
        "nodes":          nodes,
        "matrix":         matrix,
        "packages":       packages,
        "motor_capacity": motor_capacity,
        "scenarios":      scenario_data["scenarios"],
        "fuel_model":     scenario_data["fuel_model"],
        "hub_id":         hub_id,
        "n_nodes":        n_nodes,
    }
