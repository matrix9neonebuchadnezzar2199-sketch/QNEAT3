# QNEAT3 NEO — コスト計算式（式のみ）

アルゴリズム全体のフローは [CODE_TRACE.md](CODE_TRACE.md) を参照。

## 記号

| 記号 | 意味 |
|------|------|
| `link_len` | ネットワーク線レイヤのリンク長属性（高度パラメータで指定、既定 `link_len`）[m] |
| `d_実測` | 解析点と最近傍ネットワーク頂点の直線距離（楕円体 or 平面）[m] |
| `v` | 速度 [km/h]（速度フィールド、無効時はデフォルト速度） |
| `v_mps` | `v × 1000 / 3600` [m/s] |

**共通:** QGIS の `QgsVectorLayerDirector` はポリラインを**セグメント（頂点→頂点）ごとの辺**に分割してグラフを構築し、セグメント辺ごとに `cost(distance, feature)` を呼ぶ（`distance` = セグメントの実測長）。`link_len` はフィーチャ全体の値なので、**セグメント長の比率で按分**する（按分しないとセグメント数だけ重複課金される — 1.0.23 初期の障害の原因）。

按分の全長 `L_link` はビルダと同条件（ソース CRS + WGS84 楕円体）で計測し、Σ `c_e` over 1 リンク = `link_len` を厳密に満たす。

## 距離最適化（strategy = 0）

| 要素 | 式 | 単位 |
|------|-----|------|
| グラフ辺（セグメント）`c_e` | `link_len × (d_seg / L_link)` | m |
| 接続 `c_entry`, `c_exit` | `d_実測` | m |
| 合計 `C` | `c_entry + Σ c_e + c_exit`（Σ c_e over 1 リンク = link_len） | m |

```mermaid
flowchart LR
  subgraph edge [グラフ辺（セグメント）]
    E["c_e = link_len × (d_seg / L_link)"]
  end
  subgraph conn [接続]
    EN["c_entry = d_実測"]
    EX["c_exit = d_実測"]
  end
  subgraph total [合計]
    T["C = c_entry + sum_c_e + c_exit"]
  end
  E --> T
  EN --> T
  EX --> T
```

## 時間最適化（strategy = 1）

| 要素 | 式 | 単位 |
|------|-----|------|
| グラフ辺（セグメント）`c_e` | `link_len × (d_seg / L_link) / v_mps` | s |
| 接続 `c_entry`, `c_exit` | `d_実測 / v_mps_default` | s |
| 合計 `C` | `c_entry + Σ c_e + c_exit` | s |

```mermaid
flowchart LR
  subgraph edge [グラフ辺（セグメント）]
    E["c_e = link_len × (d_seg / L_link) / v_mps"]
  end
  subgraph conn [接続]
    EN["c_entry = d_実測 / v_mps_default"]
    EX["c_exit = d_実測 / v_mps_default"]
  end
  subgraph total [合計]
    T["C = c_entry + sum_c_e + c_exit"]
  end
  E --> T
  EN --> T
  EX --> T
```

## 実装クラス

| モード | グラフ辺 | ファイル |
|--------|----------|----------|
| 0 | `Qneat3LinkLengthStrategy` | `Qneat3LinkLengthStrategy.py` |
| 1 | `Qneat3LinkLengthTimeStrategy` | `Qneat3LinkLengthTimeStrategy.py` |

## 経路ラインの形状

出力ラインジオメトリは Dijkstra 木の頂点チェーン（`reconstruct_path_geometry`）。
QGIS のグラフ辺はポリラインのセグメント（頂点→頂点）なので、頂点チェーンは
通過リンクの**実形状と厳密に一致**する（曲線リンクもそのまま描画）。
entry/exit（点↔最寄り頂点）は従来通り直線。

**数値コストの算出に出力ジオメトリは使わない**（コストは link_len 系属性のみ）。

## ネットワーク前処理（NetworkPrepareLinks、1.0.23〜）

架空・手描き道路の接続用。ルーティングのコスト式は変えない。

| 処理 | 式・規則 |
|------|----------|
| 端点スナップ | 他リンク端点が許容差内で別リンクの途中 → 射影点で分割＋吸着。端点同士 → 座標一致 |
| `link_len` 補完 | 未入力・不正のみ `実測長`（楕円体）で補完（既定 ON） |
| 分割時の按分 | `部分 link_len = 元 link_len × (部分の平面長 / 全体の平面長)`（合計は保存） |
| 交差分割 | 行わない（途中×途中の交差＝立体交差として非接続を保持） |
