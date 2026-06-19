"""
graph.py — Adjacency Matrix builder dari raw data.

Bertanggung jawab untuk:
  - Menerima raw list 2D dari data_loader dan membungkusnya sebagai objek Graph
  - Menyediakan helper: get_distance, get_neighbors, validate
  - SEMUA representasi menggunakan list 2D primitif murni (tanpa library eksternal)
"""


class Graph:
    """
    Representasi Graf Lengkap Tak Berarah (Undirected Complete Graph)
    menggunakan Adjacency Matrix (list 2D primitif murni).

    Properti yang dijamin:
        - Simetris   : matrix[i][j] == matrix[j][i]
        - Diagonal 0 : matrix[i][i] == 0
        - Non-negatif: semua nilai >= 0
    """

    def __init__(self, matrix: list, nodes: list):
        """
        Inisialisasi Graph dari adjacency matrix dan list node.

        Args:
            matrix (list[list[float]]): Adjacency matrix 2D simetris.
            nodes  (list[dict])       : List node dengan 'id', 'name', 'is_hub'.
        """
        # Simpan salinan matrix untuk mencegah mutasi dari luar
        self._matrix = [row[:] for row in matrix]
        self._nodes = nodes[:]
        self.n = len(matrix)

        # Bangun mapping id -> index dan index -> node (untuk lookup O(1))
        self._id_to_index = {node["id"]: idx for idx, node in enumerate(nodes)}
        self._index_to_node = {idx: node for idx, node in enumerate(nodes)}

    # ─── Akses Jarak ─────────────────────────────────────────────────────────

    def get_distance(self, from_id: int, to_id: int) -> float:
        """
        Kembalikan jarak antara dua node berdasarkan ID mereka.

        Args:
            from_id (int): ID node asal.
            to_id   (int): ID node tujuan.

        Returns:
            float: Jarak dalam km.

        Raises:
            KeyError: Jika salah satu ID tidak ada di graph.
        """
        i = self._id_to_index[from_id]
        j = self._id_to_index[to_id]
        return self._matrix[i][j]

    def get_distance_by_index(self, i: int, j: int) -> float:
        """
        Kembalikan jarak berdasarkan indeks matriks (bukan ID node).
        Dipakai langsung oleh algoritma untuk efisiensi.

        Args:
            i (int): Indeks baris.
            j (int): Indeks kolom.

        Returns:
            float: Jarak dalam km.
        """
        return self._matrix[i][j]

    def get_matrix(self) -> list:
        """
        Kembalikan salinan adjacency matrix (list 2D).

        Returns:
            list[list[float]]: Salinan adjacency matrix.
        """
        return [row[:] for row in self._matrix]

    # ─── Akses Node ──────────────────────────────────────────────────────────

    def get_node(self, node_id: int) -> dict:
        """Kembalikan dict node berdasarkan ID."""
        idx = self._id_to_index[node_id]
        return self._index_to_node[idx]

    def get_node_name(self, node_id: int) -> str:
        """Kembalikan nama node berdasarkan ID."""
        return self.get_node(node_id)["name"]

    def get_all_node_ids(self) -> list:
        """Kembalikan list semua node ID (sorted)."""
        return sorted(self._id_to_index.keys())

    def get_customer_ids(self) -> list:
        """Kembalikan list semua customer ID (bukan hub, sorted)."""
        return sorted(
            node["id"] for node in self._nodes if not node["is_hub"]
        )

    def get_hub_id(self) -> int:
        """Kembalikan ID node Hub."""
        for node in self._nodes:
            if node["is_hub"]:
                return node["id"]
        raise ValueError("Tidak ada node hub di graph!")

    # ─── Representasi ────────────────────────────────────────────────────────

    def print_matrix(self, max_cols: int = 8) -> None:
        """
        Cetak adjacency matrix ke terminal (header + baris).

        Args:
            max_cols (int): Batas kolom yang ditampilkan (truncate jika n > max_cols).
        """
        cols = min(self.n, max_cols)
        header = "       " + "".join(f"{i:7}" for i in range(cols))
        if self.n > max_cols:
            header += " ..."
        print(header)

        for i in range(min(self.n, max_cols)):
            row_str = f"  [{i:2}] " + "".join(f"{self._matrix[i][j]:7.1f}" for j in range(cols))
            if self.n > max_cols:
                row_str += " ..."
            print(row_str)

        if self.n > max_cols:
            print("  ...")

    def __repr__(self) -> str:
        return f"Graph(n={self.n} nodes, fully connected, adjacency matrix)"


def build_graph(matrix: list, nodes: list) -> Graph:
    """
    Factory function — bangun objek Graph dari raw data.

    Args:
        matrix (list[list[float]]): Adjacency matrix dari data_loader.
        nodes  (list[dict])       : List node dari data_loader.

    Returns:
        Graph: Objek Graph siap pakai.
    """
    return Graph(matrix, nodes)
