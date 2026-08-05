# -*- coding: utf-8 -*-
"""
ネットワーク前処理（接続・link_len 補完）の純粋計算コア。

QGIS に依存しない（import なし）設計。座標は (x, y) タプルのリストとして扱い、
test_quality.py の QGIS スタブ環境で単体テスト可能にする。
QGIS との接着は algs/NetworkPrepareLinks.py が担当する。

主な仕様:
- 端点スナップ: 他リンク端点が許容差内で別リンクの途中に突き当たる場合、
  射影点でリンクを分割し、端点を射影点に吸着させる。
- 端点同士の近接: 許容差内なら座標を完全一致させる。
- 途中×途中の交差分割は行わない（立体交差＝非接続の意味を保持）。
"""

import math

# 分割パラメータ t の両端判定（この範囲の t は既存頂点とみなす）
EPS_T = 1e-9

# 同一セグメント上で分割点をマージする t の幅
MERGE_T = 1e-6


def dist(a, b):
    """2 点間のユークリッド距離。"""
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def polyline_length(pts):
    """ポリラインの平面長（CRS 単位）。link_len 按分比率の計算に使う。"""
    total = 0.0
    for i in range(len(pts) - 1):
        total += dist(pts[i], pts[i + 1])
    return total


def _project_on_segment(p, a, b):
    """点 p の線分 ab への射影。(t, 射影点) を返す（t は 0..1 にクランプ）。"""
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    len2 = dx * dx + dy * dy
    if len2 == 0.0:
        return 0.0, a
    t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / len2
    t = max(0.0, min(1.0, t))
    return t, (a[0] + dx * t, a[1] + dy * t)


def closest_on_polyline(p, pts):
    """
    ポリライン上の最近点を返す。

    Returns:
        tuple | None: (セグメント番号, t, 射影点, 距離)。頂点 2 未満なら None。
    """
    best = None
    for seg in range(len(pts) - 1):
        t, proj = _project_on_segment(p, pts[seg], pts[seg + 1])
        d = dist(p, proj)
        if best is None or d < best[3]:
            best = (seg, t, proj, d)
    return best


def split_polyline(pts, cuts):
    """
    ポリラインを指定カットで分割する。

    Args:
        pts: (x, y) のリスト。
        cuts: (セグメント番号, t) の iterable。既存頂点上のカットは無視する。

    Returns:
        list[list]: 分割後のポリライン列（カット無しなら [pts] のコピー）。
    """
    n = len(pts)
    per_seg = {}
    for seg, t in cuts:
        if seg < 0 or seg >= n - 1:
            continue
        if t <= EPS_T or t >= 1.0 - EPS_T:
            continue
        per_seg.setdefault(seg, []).append(t)
    if not per_seg:
        return [list(pts)]

    for ts in per_seg.values():
        ts.sort()
        deduped = []
        for t in ts:
            if not deduped or t - deduped[-1] > MERGE_T:
                deduped.append(t)
        ts[:] = deduped

    parts = []
    current = [pts[0]]
    for seg in range(n - 1):
        a = pts[seg]
        b = pts[seg + 1]
        ts = per_seg.get(seg)
        if not ts:
            current.append(b)
            continue
        for t in ts:
            cut_pt = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            current.append(cut_pt)
            parts.append(current)
            current = [cut_pt]
        current.append(b)
    parts.append(current)
    return parts


def _bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def _bbox_distance_to_point(bbox, p):
    """バウンディングボックスと点の最短距離（粗フィルタ用）。"""
    dx = max(bbox[0] - p[0], 0.0, p[0] - bbox[2])
    dy = max(bbox[1] - p[1], 0.0, p[1] - bbox[3])
    return (dx * dx + dy * dy) ** 0.5


def plan_endpoint_attachments(lines, tol):
    """
    端点の接続計画を立てる（計画は常に元ジオメトリ基準。適用は apply_plan）。

    各ラインの両端点について、他ラインとの関係を許容差 tol で判定:
    - 他ラインの途中に近い → そのラインに分割カットを記録し、端点は射影点に吸着
    - 他ラインの端点に近い → 端点をその端点座標に吸着（分割なし）

    Args:
        lines: ポリラインのリスト（各要素は (x, y) のリスト）。
        tol: 接続スナップ許容差（CRS 単位）。

    Returns:
        tuple: (cuts, snaps, stats)
            cuts: {ライン index: {(seg, t), ...}}
            snaps: {(ライン index, 端): 吸着先点}（端は 0=始点, 1=終点）
            stats: {"snaps": int, "split_links": int, "split_events": int}
    """
    cuts = {}
    snaps = {}
    bboxes = [_bbox(pts) if pts else (0, 0, 0, 0) for pts in lines]
    n_snaps = 0
    n_split_events = 0

    for i, pts in enumerate(lines):
        if len(pts) < 2:
            continue
        for end_idx, p in ((0, pts[0]), (1, pts[-1])):
            best = None  # (d, j, seg, t, proj, j_end)
            for j, other in enumerate(lines):
                if j == i or len(other) < 2:
                    continue
                if _bbox_distance_to_point(bboxes[j], p) > tol:
                    continue
                hit = closest_on_polyline(p, other)
                if hit is None:
                    continue
                seg, t, proj, d = hit
                if d > tol:
                    continue
                j_end = None
                if seg == 0 and t <= EPS_T:
                    j_end = 0
                elif seg == len(other) - 2 and t >= 1.0 - EPS_T:
                    j_end = 1
                if best is None or d < best[0]:
                    best = (d, j, seg, t, proj, j_end)
            if best is None:
                continue
            _, j, seg, t, proj, j_end = best
            if j_end is not None:
                target = lines[j][0] if j_end == 0 else lines[j][-1]
                if dist(p, target) > EPS_T:
                    snaps[(i, end_idx)] = target
                    n_snaps += 1
            else:
                cuts.setdefault(j, set()).add((seg, round(t, 12)))
                snaps[(i, end_idx)] = proj
                n_split_events += 1

    stats = {
        "snaps": n_snaps,
        "split_links": len(cuts),
        "split_events": n_split_events,
    }
    return cuts, snaps, stats


def apply_plan(lines, cuts, snaps):
    """
    接続計画を適用する（スナップ → 分割の順）。

    Returns:
        tuple: (parts_per_line, snapped_lines)
            parts_per_line: 元ライン index ごとの分割後ポリライン列
            snapped_lines: スナップ適用後の元ライン（按分の分母に使う）
    """
    snapped_lines = []
    for i, pts in enumerate(lines):
        pts = list(pts)
        if (i, 0) in snaps:
            pts[0] = snaps[(i, 0)]
        if (i, 1) in snaps:
            pts[-1] = snaps[(i, 1)]
        snapped_lines.append(pts)

    parts_per_line = []
    for i, pts in enumerate(snapped_lines):
        line_cuts = sorted(cuts.get(i, ()))
        parts_per_line.append(split_polyline(pts, line_cuts))
    return parts_per_line, snapped_lines


def prorate_value(total_value, whole_pts, parts):
    """
    link_len 等の値を分割後パートに平面長比率で按分する。

    退化（全長 0）の場合は均等割り。合計は常に total_value に一致する。
    """
    whole = polyline_length(whole_pts)
    if whole <= 0.0:
        share = total_value / max(len(parts), 1)
        return [share for _ in parts]
    return [total_value * (polyline_length(p) / whole) for p in parts]


def _quantize(p, cell):
    # floor なら |p1-p2| <= cell の 2 点のセル差は最大 1 になり、
    # 3x3 近傍検索で取りこぼさない（round だと境界またぎで 2 離れうる）
    return (math.floor(p[0] / cell), math.floor(p[1] / cell))


class _UnionFind:
    def __init__(self, size):
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, x):
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1


def connected_components(lines, tol):
    """
    端点座標の一致（tol 以内）から連結成分を求める（孤立リンク検出用）。

    グリッドセル + 3x3 近傍で端点を照合する。セル境界またぎの誤判定は
    実距離チェックで排除する。

    Returns:
        list[list[int]]: ライン index のグループ（連結成分ごと）。
    """
    if tol > 0:
        cell = tol
    else:
        cell = 1e-9
    eps = max(tol, 1e-9)

    endpoint_cells = {}
    uf = _UnionFind(len(lines))

    def endpoint_near(line, p):
        return min(dist(line[0], p), dist(line[-1], p)) <= eps

    for i, pts in enumerate(lines):
        if len(pts) < 2:
            continue
        for p in (pts[0], pts[-1]):
            c = _quantize(p, cell)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    neighbor = (c[0] + dx, c[1] + dy)
                    for j in endpoint_cells.get(neighbor, ()):
                        if endpoint_near(lines[j], p):
                            uf.union(i, j)
            endpoint_cells.setdefault(c, set()).add(i)

    comps = {}
    for i in range(len(lines)):
        comps.setdefault(uf.find(i), []).append(i)
    return list(comps.values())
