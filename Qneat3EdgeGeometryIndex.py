# -*- coding: utf-8 -*-
"""
グラフ辺 → 元リンク形状の索引（経路出力をリンク形状に沿わせるため）。

QGIS の QgsGraphEdge はジオメトリを保持しないため、ネットワークレイヤの
各リンク（パート単位）を端点座標のグリッドハッシュで登録し、
グラフ辺の両端頂点座標から元リンク形状を引く。

QGIS 非依存（座標は (x, y) タプル）。接着は Qneat3Framework /
Qneat3Utilities が担当する。

マッチ規則:
- レコードの両端点が、クエリの両端点に（向きは問わず）許容差内で一致
- 複数候補（同一端点の並行リンク）は、登録コストとグラフ辺コストの
  差が最小のものを選ぶ（link_len が異なる並行リンクの区別用）
"""

import math

from QNEAT3.Qneat3NetworkPrep import dist


class EdgeGeometryIndex:
    """リンク端点のグリッドハッシュ索引。"""

    def __init__(self, tolerance=0.0):
        # グリッドのセル幅。tol=0（厳密一致運用）でも float 丸め誤差を
        # 吸収できるよう小さなセルを使う
        self._cell = tolerance if tolerance > 0 else 1e-7
        self._tol = tolerance
        self._grid = {}
        self._records = []

    def __len__(self):
        return len(self._records)

    def _quantize(self, p):
        # floor 量子化: 許容差内の 2 点のセル差を最大 1 に抑え、
        # 3x3 近傍検索で取りこぼさない（Qneat3NetworkPrep と同じ規約）
        return (math.floor(p[0] / self._cell), math.floor(p[1] / self._cell))

    def _cells_around(self, p):
        cx, cy = self._quantize(p)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                yield (cx + dx, cy + dy)

    def _near(self, p, q):
        return dist(p, q) <= max(self._tol, 1e-9)

    def add(self, points, cost):
        """
        リンク（パート）を登録する。

        Args:
            points: (x, y) タプル列（2 点以上）。
            cost: グラフ辺コストと同じ計算式の値（link_len または link_len/速度）。
        """
        pts = tuple(points)
        record_id = len(self._records)
        self._records.append((pts, float(cost)))
        for p in (pts[0], pts[-1]):
            self._grid.setdefault(self._quantize(p), set()).add(record_id)

    def lookup(self, a, b, edge_cost):
        """
        グラフ辺（端点 a → b）に対応する元リンク形状を返す。

        Args:
            a, b: グラフ辺の両端頂点座標（向きつき）。
            edge_cost: グラフ辺のコスト（criterion 0）。候補絞り込みに使用。

        Returns:
            list | None: a → b 向きの (x, y) タプル列。見つからなければ None。
        """
        candidates = set()
        for cell in self._cells_around(a):
            candidates.update(self._grid.get(cell, ()))

        best = None  # (スコア, 向き付き座標列)
        for record_id in candidates:
            pts, cost = self._records[record_id]
            oriented = None
            if self._near(pts[0], a) and self._near(pts[-1], b):
                oriented = list(pts)
            elif self._near(pts[-1], a) and self._near(pts[0], b):
                oriented = list(reversed(pts))
            if oriented is None:
                continue
            score = abs(cost - edge_cost)
            if best is None or score < best[0]:
                best = (score, oriented)
        if best is None:
            return None
        return best[1]
