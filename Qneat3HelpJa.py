# -*- coding: utf-8 -*-
"""アルゴリズムヘルプ（HTML・日本語）"""


def _cost_modes_note():
    """距離・時間のコスト式（全アルゴリズム共通）。"""
    return (
        "<br><b>コストの考え方（NEO）</b><ul>"
        "<li><b>距離最適化</b>: 道路区間 = <code>link_len</code> [m] の合計。"
        "形状長は使いません。</li>"
        "<li><b>時間最適化</b>: 道路区間 = <code>link_len</code> ÷ 速度 [km/h] → 秒。"
        "形状長は使いません。</li>"
        "<li><b>接続コスト</b>（点→道路）: 実測直線距離。"
        "時間モードでは ÷ 速度で秒に換算。</li>"
        "</ul>"
        "実行ログに計算式が表示されます。詳細はリポジトリ内 "
        "<code>docs/COST_FORMULAS.md</code> を参照。"
    )


def _link_len_required():
    return (
        "<br><b>リンク長</b>: 高度パラメータで指定（既定 <code>link_len</code>）。"
        "全道路リンクに正の数値が必須。未設定・NULL・0 以下はエラーで停止します。"
    )


def _advanced_params_note():
    return (
        "<br><b>高度パラメータ</b>: 方向フィールド、速度、トポロジ許容差、"
        "接続コスト算定（楕円体/平面）、リンク長フィールド。"
    )


def help_shortest_path_point_to_point():
    return (
        "<b>概要</b><br>"
        "2 点間の<b>最短経路</b>を Dijkstra 法で求め、1 本のラインを出力します。"
        "ネットワーク外の点には<b>接続コスト</b>（entry / exit）を加算します。"
        + _cost_modes_note()
        + _link_len_required()
        + "<br><br><b>必須</b><ul>"
        "<li>ネットワークレイヤ（線）</li>"
        "<li>始点・終点</li>"
        "<li>最適化基準（距離 / 時間）</li>"
        "</ul>"
        + _advanced_params_note()
        + "<br><br><b>出力属性</b><ul>"
        "<li>始点・終点座標</li>"
        "<li><code>start_entry_cost</code> … 始点の接続コスト</li>"
        "<li><code>end_exit_cost</code> … 終点の接続コスト</li>"
        "<li><code>cost_on_graph</code> … 道路上のコスト（link_len または link_len÷速度 の合計）</li>"
        "<li><code>total_cost</code> … 上記の合計</li>"
        "</ul>"
    )


def _od_output_attrs_table():
    return (
        "<b>出力属性（表）</b><ul>"
        "<li><code>from_id</code> / <code>to_id</code> … 出発・到着 ID</li>"
        "<li><code>entry_cost</code> … 出発点の接続コスト</li>"
        "<li><code>network_cost</code> … グラフ上（道路上）のコスト</li>"
        "<li><code>exit_cost</code> … 到着点の接続コスト</li>"
        "<li><code>total_cost</code> … 合計（到達不能時は NULL）</li>"
        "</ul>"
    )


def help_od_matrix_points_table():
    return (
        "<b>概要</b><br>"
        "1 つのポイントレイヤ内の全組み合わせ (n:n) について、"
        "ネットワーク上の OD コストを表形式で出力します。"
        + _cost_modes_note()
        + _link_len_required()
        + "<br><br><b>必須</b><ul>"
        "<li>ネットワークレイヤ</li>"
        "<li>ポイントレイヤ</li>"
        "<li>ポイント ID フィールド</li>"
        "<li>最適化基準</li>"
        "</ul>"
        + _advanced_params_note()
        + "<br><br>"
        + _od_output_attrs_table()
    )


def help_od_matrix_points_lines():
    return (
        "<b>概要</b><br>"
        "OD 行列を<b>ライン</b>で出力します。"
        "ジオメトリは「直線（空中線）」または「ネットワーク経路」を選択できます。"
        + _cost_modes_note()
        + _link_len_required()
        + "<br><br><b>必須</b><ul>"
        "<li>ネットワークレイヤ・ポイントレイヤ・ID フィールド・最適化基準</li>"
        "<li>行列ジオメトリの形式</li>"
        "</ul>"
        + _advanced_params_note()
        + "<br><br>"
        + _od_output_attrs_table()
    )


def help_od_matrix_points_csv():
    return (
        "<b>概要</b><br>"
        "OD 行列を CSV ファイルに出力します（列名は表出力と同じ）。"
        + help_od_matrix_points_table().split("<b>必須</b>")[1]
    )


def help_od_matrix_layers_table():
    return (
        "<b>概要</b><br>"
        "出発点レイヤと到着点レイヤの全組み合わせ (m:n) について OD コストを表で出力します。"
        + _cost_modes_note()
        + _link_len_required()
        + "<br><br><b>必須</b><ul>"
        "<li>ネットワークレイヤ</li>"
        "<li>出発点レイヤ・到着点レイヤ</li>"
        "<li>各 ID フィールド</li>"
        "<li>最適化基準</li>"
        "</ul>"
        + _advanced_params_note()
        + "<br><br>"
        + _od_output_attrs_table()
    )


def help_od_matrix_layers_lines():
    return (
        "<b>概要</b><br>"
        "出発・到着レイヤ間の OD をラインで出力します。"
        "直線またはネットワーク経路を選択できます。"
        + help_od_matrix_layers_table().split("<b>必須</b>")[1]
    )


def help_iso_pointcloud_from_point():
    return (
        "<b>概要</b><br>"
        "指定した始点から、到達コストが閾値以内のネットワーク頂点を"
        "<b>ポイントクラウド</b>として出力します。"
        + _cost_modes_note()
        + _link_len_required()
        + "<br><br><b>必須</b><ul>"
        "<li>ネットワークレイヤ・始点・等時圏サイズ・最適化基準</li>"
        "</ul>"
        + _advanced_params_note()
    )


def help_iso_pointcloud_from_layer():
    return (
        "<b>概要</b><br>"
        "始点レイヤの各点から等時点クラウドを出力します。"
        + help_iso_pointcloud_from_point().split("<b>必須</b>")[1]
    )


def help_iso_interpolation_from_point():
    return (
        "<b>概要</b><br>"
        "始点からの到達コストを <b>TIN 補間ラスタ</b>で出力します。"
        "<b>投影 CRS</b>（メートル単位）が必要です。地理座標系ではエラーになります。"
        + _cost_modes_note()
        + _link_len_required()
        + "<br><br><b>必須</b><ul>"
        "<li>ネットワーク・始点・最大コスト（等時圏サイズ）・セルサイズ・最適化基準</li>"
        "</ul>"
        + _advanced_params_note()
    )


def help_iso_interpolation_from_layer():
    return help_iso_interpolation_from_point().replace(
        "始点からの到達コスト", "始点レイヤ各点からの到達コスト"
    )


def help_iso_contours_from_point():
    return (
        "<b>概要</b><br>"
        "到達コストの <b>TIN 補間ラスタ</b>から <b>等値線</b>を生成します。"
        "<b>matplotlib</b> が必須です。"
        + _cost_modes_note()
        + _link_len_required()
        + "<br><br><b>必須</b><ul>"
        "<li>ネットワーク・始点・最大コスト・等値線間隔・セルサイズ・最適化基準</li>"
        "</ul>"
        + _advanced_params_note()
    )


def help_iso_contours_from_layer():
    return help_iso_contours_from_point().replace(
        "ネットワーク・始点・", "ネットワーク・始点レイヤ・"
    )


def help_iso_polygons_from_point():
    return (
        "<b>概要</b><br>"
        "到達コストの<b>ポリゴン等時圏</b>を出力します（<b>matplotlib</b> 必須）。"
        + help_iso_contours_from_point().split("<b>必須</b>")[1]
    )


def help_iso_polygons_from_layer():
    return help_iso_polygons_from_point().replace(
        "到達コストの<b>ポリゴン等時圏</b>", "始点レイヤ各点からの<b>ポリゴン等時圏</b>"
    )


def help_iso_qneat_interpolation_from_point():
    return (
        "<b>概要</b><br>"
        "始点からの到達コストを <b>QNEAT 補間</b>でラスタ出力します。"
        "TIN より遅いですが、ネットワーク上のコストに沿った精度が高いです。"
        + _cost_modes_note()
        + _link_len_required()
        + "<br><br><b>必須</b><ul>"
        "<li>ネットワーク・始点・最大コスト・セルサイズ・補間方法・最適化基準</li>"
        "</ul>"
        + _advanced_params_note()
    )


def help_dummy_matplotlib():
    return (
        "<b>[matplotlib 未導入]</b><br>"
        "等時圏のポリゴン・等値線アルゴリズムには <b>matplotlib</b> が必要です。"
        "インストール後、QGIS を再起動してください。<br><br>"
        "<b>Windows</b>（OSGeo4W Shell）:<br>"
        "<code>python-qgis -m pip install matplotlib</code><br><br>"
        "<b>Linux</b>:<br>"
        "<code>pip install matplotlib</code>"
    )
