# -*- coding: utf-8 -*-
"""アルゴリズムヘルプ（HTML・日本語）"""


def help_shortest_path_point_to_point():
    return (
        "<b>概要</b><br>"
        "2 点間の<b>最短経路</b>を Dijkstra 法で求めます。<b>ネットワークレイヤ</b>上で動作します。<br>"
        "ネットワーク外の点は<b>接続コスト（entry / exit）</b>として別途加算します。"
        "距離は楕円体または平面で計測できます。<br><br>"
        "<b>距離最適化時</b>: エッジコストは形状長ではなく <b>link_len</b>（リンク長フィールド）の値。"
        "全リンクに正の数値が必須。NULL・未設定はエラーで停止します。<br><br>"
        "<b>必須パラメータ</b><ul>"
        "<li>ネットワークレイヤ</li><li>始点・終点</li><li>最適化基準（距離 / 時間）</li>"
        "<li>距離最適化時: リンク長フィールド（既定 link_len）</li>"
        "</ul><br>"
        "<b>任意（高度）</b><ul>"
        "<li>方向フィールド・速度・トポロジ許容差・接続コスト算定方法</li>"
        "</ul><br>"
        "<b>出力</b><ul>"
        "<li>1 本のラインと、始終点座標・接続コスト・グラフ上コスト・合計コスト</li>"
        "</ul>"
    )


_LINK_LEN_NOTE = (
    "<br><b>距離最適化</b>: コストは <code>link_len</code> 必須（全リンク正の数値、異常時はエラー）。"
)


def help_od_matrix_points_table():
    return (
        "<b>概要</b><br>"
        "1 つのポイントレイヤ内の全組み合わせ (n:n) について、"
        "ネットワーク上の<b>OD コスト</b>を表形式で出力します。"
        + _LINK_LEN_NOTE
        + "<br><br>"
        "<b>必須</b><ul>"
        "<li>ネットワークレイヤ・ポイントレイヤ・ID フィールド・最適化基準</li>"
        "</ul>"
        "<b>出力</b><ul><li>origin_id, destination_id, entry / network / exit / total_cost</li></ul>"
    )


def help_od_matrix_points_lines():
    return (
        "<b>概要</b><br>OD 行列を<b>ラインジオメトリ付き</b>で出力します。"
        "ジオメトリは直線またはネットワーク経路を選択できます。<br>"
        + help_od_matrix_points_table().split("<b>必須</b>")[1]
    )


def help_od_matrix_points_csv():
    return (
        "<b>概要</b><br>OD 行列を CSV ファイルに出力します。<br>"
        + help_od_matrix_points_table().split("<b>必須</b>")[1]
    )


def help_od_matrix_layers_table():
    return (
        "<b>概要</b><br>"
        "出発点レイヤと到着点レイヤの全組み合わせ (m:n) について OD コストを表で出力します。<br>"
        "<b>必須</b><ul>"
        "<li>ネットワーク・From/To レイヤ・各 ID フィールド・最適化基準</li></ul>"
    )


def help_od_matrix_layers_lines():
    return help_od_matrix_layers_table() + (
        "<br>ライン出力では経路形状のスタイルを選択できます。"
    )


def help_iso_pointcloud_from_point():
    return (
        "<b>概要</b><br>手動指定の始点から<b>等時圏・到達圏</b>に含まれる"
        "ネットワーク頂点をポイントクラウドとして出力します。<br>"
        "<b>必須</b><ul><li>ネットワーク・始点・到達サイズ・最適化基準</li></ul>"
    )


def help_iso_pointcloud_from_layer():
    return (
        "<b>概要</b><br>始点レイヤの各点から等時点クラウドを出力します。"
        "<b>必須</b><ul><li>ネットワーク・始点レイヤ・ID・到達サイズ</li></ul>"
    )


def help_iso_interpolation_from_point():
    return (
        "<b>概要</b><br>始点からの到達コストを<b>TIN 補間ラスタ</b>で出力します。"
        "投影 CRS が必要です。<br>"
        "<b>必須</b><ul><li>ネットワーク・始点・最大コスト・セルサイズ</li></ul>"
    )


def help_iso_interpolation_from_layer():
    return help_iso_interpolation_from_point().replace("始点から", "始点レイヤ各点から")


def help_iso_contours_from_point():
    return (
        "<b>概要</b><br>補間ラスタから<b>等値線</b>を生成します（matplotlib 必須）。<br>"
        "<b>必須</b><ul><li>ネットワーク・始点・最大コスト・間隔・セルサイズ</li></ul>"
    )


def help_iso_contours_from_layer():
    return help_iso_contours_from_point().replace("始点", "始点レイヤ")


def help_iso_polygons_from_point():
    return (
        "<b>概要</b><br>到達コストの<b>ポリゴン等時圏</b>を出力します（matplotlib 必須）。<br>"
        + help_iso_contours_from_point().split("<b>必須</b>")[1]
    )


def help_iso_polygons_from_layer():
    return help_iso_polygons_from_point().replace("始点", "始点レイヤ")


def help_iso_qneat_interpolation_from_point():
    return (
        "<b>概要</b><br>始点からの到達コストを<b>QNEAT 補間</b>でラスタ出力します。"
        "TIN より遅いですがネットワーク上のコストに沿った精度が高いです。<br>"
        "<b>必須</b><ul><li>ネットワーク・始点・最大コスト・セルサイズ・補間方法</li></ul>"
        + _LINK_LEN_NOTE
    )


def help_dummy_matplotlib():
    return (
        "<b>[matplotlib 未インストール]</b><br>"
        "一部の等時圏アルゴリズムには matplotlib が必要です。<br>"
        "<b>Windows</b>: OSGeo4W Shell で <code>python-qgis -m pip install matplotlib</code><br>"
        "<b>Linux</b>: <code>pip install matplotlib</code>"
    )
