# -*- coding: utf-8 -*-
"""
QNEAT3_NEO 共通 UI 文言（日本語ソース）。
Processing の self.tr() に渡す文字列の単一ソース。
"""


def ja(text):
    """
    Processing パラメータ用ラベル（日本語をそのまま返す）。
    self.tr() は QGIS / 公式プラグインの翻訳カタログと干渉しうるため NEO では使わない。
    """
    return text


NEO_PREFIX = "[NEO] "


class UIS:
    """アルゴリズムパラメータ・グループ名"""

    # グループ
    ROUTING = "経路"
    DISTANCE_MATRICES = "距離行列"
    ISO_AREAS = "等時圏・到達圏"

    # 共通パラメータ
    NETWORK_LAYER = "ネットワークレイヤ"
    NETWORK_LAYER_LOWER = "ネットワークレイヤ"
    START_POINT = "始点"
    END_POINT = "終点"
    START_POINTS = "始点レイヤ"
    POINT_LAYER = "ポイントレイヤ"
    FROM_POINT_LAYER = "出発点レイヤ"
    TO_POINT_LAYER = "到着点レイヤ"
    UNIQUE_POINT_ID = "ポイント ID フィールド"
    OPTIMIZATION_CRITERION = "最適化基準"
    ENTRY_COST_METHOD = "ネットワーク接続コストの算定方法"
    DIRECTION_FIELD = "方向フィールド"
    VALUE_FORWARD = "順方向の値"
    VALUE_BACKWARD = "逆方向の値"
    VALUE_BOTH = "双方向の値"
    DEFAULT_DIRECTION = "デフォルト方向"
    SPEED_FIELD = "速度フィールド"
    DEFAULT_SPEED_KMH = "デフォルト速度 (km/h)"
    TOPOLOGY_TOLERANCE = "トポロジ許容差"
    LINK_LENGTH_FIELD = "リンク長フィールド（距離最適化時必須・時間最適化時は未使用）"

    # 列挙ラベル
    STRATEGY_DISTANCE = "最短経路（距離最適化）"
    STRATEGY_TIME = "最速経路（時間最適化）"
    ENTRY_ELLIPSOIDAL = "楕円体距離"
    ENTRY_PLANAR = "平面距離（投影 CRS のみ）"
    DIR_FORWARD = "順方向"
    DIR_BACKWARD = "逆方向"
    DIR_BOTH = "双方向"
    MATRIX_GEOM_STRAIGHT = "行列ジオメトリ: 直線（空中線）"
    MATRIX_GEOM_ROUTE = "行列ジオメトリ: ネットワーク経路"
    MATRIX_GEOM_STYLE = "行列ジオメトリの形式"

    # 出力
    OUTPUT_SHORTEST_PATH = "最短経路レイヤ"
    OUTPUT_OD_MATRIX = "OD 行列出力"
    OUTPUT_INTERPOLATION = "補間ラスタ出力"
    OUTPUT_CONTOURS = "等値線出力"
    OUTPUT_POLYGONS = "ポリゴン出力"
    OUTPUT_POINTCLOUD = "到達点クラウド出力"
    # fix_remaining_ja.py 等が参照する別名（定義漏れで AttributeError にならないよう同期）
    OUTPUT_ISO_CONTOURS = OUTPUT_CONTOURS
    OUTPUT_ISO_POLYGONS = OUTPUT_POLYGONS
    OUTPUT_ISO_POINTCLOUD = OUTPUT_POINTCLOUD
    CSV_FILES_FILTER = "CSV ファイル (*.csv)"

    # Iso 専用
    ISO_SIZE = "等時圏・到達圏のサイズ（距離または時間）"
    ISO_INTERVAL = "等値線・帯の間隔（距離または時間）"
    ISO_CELLSIZE = "補間ラスタのセルサイズ"
    INTERP_METHOD = "補間方法"
    INTERP_TIN = "QGIS TIN 補間（高速・近似）"
    INTERP_QNEAT = "QNEAT 補間（低速・高精度）"
    STARTPOINT_LAYER = "始点レイヤ"
    NETWORK_LAYER_DESC = "ネットワーク（線レイヤ）"
    PATH_TYPE = "経路タイプ"
    ISO_POLYGONS_FROM_POINT = "等時圏ポリゴン（単一点）"
    DUMMY_MATPLOTLIB_PARAM = (
        "<b>[matplotlib 未導入]</b><br>"
        "一部の等時圏アルゴリズムには <b>matplotlib</b> が必要です。<br>"
        "<b>Windows</b>: OSGeo4W Shell を開き、下のコマンドを貼り付けて実行し、"
        "プロンプトで <code>yes</code> と入力してください。<br>"
        "<b>Linux</b>: ターミナルで <code>pip install matplotlib</code>"
    )
    DUMMY_CMD_DEFAULT = "python-qgis -m pip install matplotlib"
    DUMMY_RESULT = "matplotlib が未インストールのため、このアルゴリズムは実行できません。"
    HELP_SPEED_FIELD = (
        "時間最適化時: グラフ辺は link_len÷速度。無効値はデフォルト速度を使用。"
        "距離最適化では無視（0 可）。"
    )
    HELP_DEFAULT_SPEED = (
        "時間最適化時必須（正の km/h）。グラフ辺・接続コストのフォールバック速度。"
        "距離最適化では無視（0 可）。"
    )
    HELP_LINK_LEN_FIELD = (
        "距離・時間の両モードで必須。全リンクに正の link_len。"
        "形状長はコストに使いません。"
    )


class LOG:
    """ログメッセージ（プレースホルダは format 用）"""

    ALG_START = "[QNEAT3] アルゴリズム: '{name}'"
    ALG_INIT = "[QNEAT3] 変数を初期化しています"
    ALG_BUILD_GRAPH = "[QNEAT3] グラフを構築しています"
    ALG_END = "[QNEAT3] アルゴリズムを終了します"

    NET_SETUP = "[QNEAT3Network] パラメータを設定しています"
    NET_DIRECTION = "[QNEAT3Network] 方向パラメータを設定しています"
    NET_POINTS = "[QNEAT3Network] 解析点を設定しています"
    NET_STRATEGY = "[QNEAT3Network] 解析戦略: {strategy}"
    NET_LINK_FIELD = "[QNEAT3Network] エッジコスト: フィールド '{field}'（形状長は使用しません）"
    NET_DISTANCE_SKIPS_SPEED = (
        "[QNEAT3Network] 距離最適化: 速度フィールド・デフォルト速度は使用しません"
        "（グラフ辺は link_len、接続コストは距離のまま）。"
    )
    NET_LINK_LEN_VALIDATED = (
        "[QNEAT3Network] リンク長フィールド '{field}' を {count} 件のフィーチャで検証しました。"
    )
    STRATEGY_UI_NOTE = (
        "[QNEAT3] UI 注記: 高度パラメータの表示は最適化基準に連動して変化しません。"
        "距離→link_len [m] / 時間→link_len÷速度 [s]（ログの計算式・コストモードを確認）。"
    )
    NET_STRATEGY_MODE = "[QNEAT3Network] コストモード: {mode}"
    NET_TIME_USES_LINK_LEN = (
        "[QNEAT3Network] 時間最適化: リンク長 '{field}'、速度 '{speed_field}'"
    )
    FORMULA_EDGE_DISTANCE = (
        "[QNEAT3] 計算式（グラフ辺）: link_len [m]  ※形状長は使用しません"
    )
    FORMULA_CONN_DISTANCE = (
        "[QNEAT3] 計算式（接続）: 実測直線距離 [m]（楕円体/平面）"
    )
    FORMULA_EDGE_TIME = (
        "[QNEAT3] 計算式（グラフ辺）: link_len [m] ÷ 速度 [km/h] → 時間 [s]"
        "  ※形状長は使用しません"
    )
    FORMULA_CONN_TIME = (
        "[QNEAT3] 計算式（接続）: 実測直線距離 [m] ÷ 速度 [km/h] → 時間 [s]"
    )
    NET_TIE_START = "[QNEAT3Network] 解析点をグラフに結線し、グラフを構築します"
    NET_TIE_HEAVY = "[QNEAT3Network] 計算負荷が高い処理です。ネットワーク規模により時間がかかります"
    NET_START_TIME = "[QNEAT3Network] 開始時刻: {time}"
    NET_BUILDING = "[QNEAT3Network] 構築中..."
    NET_END_TIME = "[QNEAT3Network] 終了時刻: {time}"
    NET_BUILD_SEC = "[QNEAT3Network] 構築時間（秒）: {sec}"
    NET_DONE = "[QNEAT3Network] 解析の準備が完了しました"

    PATH_CALC = "[QNEAT3] 最短経路を計算しています..."
    PATH_TRAVERSE = "[QNEAT3] {count} 頂点を通過しました..."
    PATH_TOTAL_NODES = "[QNEAT3] 通過頂点数: {count}"
    PATH_WRITE = "[QNEAT3] 経路フィーチャを書き出しています..."
    PATH_COST_NOTE_DISTANCE = (
        "[QNEAT3] コスト内訳 [m]: entry/exit=実測直線、graph=通過 link_len の合計"
    )
    PATH_COST_NOTE_TIME = (
        "[QNEAT3] コスト内訳 [s]: entry/exit=実測÷速度、graph=通過 link_len÷速度 の合計"
    )
    PATH_COST_VALUES = (
        "[QNEAT3] コスト値: entry={entry:.4f} graph={graph:.4f} exit={exit:.4f} total={total:.4f}"
    )

    ISO_POINTCLOUD = "[QNEAT3] 等時点クラウドを計算しています..."
    ISO_INTERP = "[QNEAT3] TIN 補間ラスタを計算しています..."
    ISO_PROCESS_POINT = "[QNEAT3Network] 点 {counter} を処理中"
    ISO_NODES_ADDED = "[QNEAT3Network] 等時点クラウドに {n} 頂点を追加..."

    ENTRY_ELLIP = "[QNEAT3Network] 楕円体接続コスト → 頂点 {vid} = {dist}"
    ENTRY_PLANAR = "[QNEAT3Network] 平面接続コスト → 頂点 {vid} = {dist}"

    OD_WORKLOAD = "[QNEAT3] 予想反復数: {n}"
    OD_PROGRESS = "[QNEAT3] {n} 組の OD を処理しました..."
    OD_TOTAL = "[QNEAT3] 処理した OD 組数: {n}"

    ISO_PC = "[QNEAT3] 等時点クラウドを計算しています..."
    ISO_TIN = "[QNEAT3] TIN 補間ラスタを計算しています..."
    ISO_CONTOURS = "[QNEAT3] 等値線を生成しています（matplotlib）..."
    ISO_POLYGONS = "[QNEAT3] 等時圏ポリゴンを生成しています（matplotlib）..."
    INTERP_BEGIN = "[QNEAT3Network] 補間を開始します"
    INTERP_WORKLOAD = "[QNEAT3Network] 補間セル数: {n}"
    INTERP_PROGRESS = "[QNEAT3Network] {n} セルを補間しました..."
    ISO_CONTOUR_LEVEL = "[QNEAT3Network] 等値線レベル {level} を計算中"
    ISO_POLYGON_COUNT = "[QNEAT3Network] ポリゴン要素数: {n}"


class ERR:
    NO_PATH = "始点から終点への経路が見つかりません。グラフの接続や入力点を確認してください。"
    WRONG_GEOM = "ジオメトリ型が不正です。{given} ですが {expected} が必要です。"
    CRS_MISMATCH = "座標参照系が一致しません: {crs_list}。すべて同じ CRS に揃えてください。"
    TIN_GEOGRAPHIC = (
        "TIN 補間は投影座標系用です。WGS84 などの地理座標系ではなく UTM 等の投影 CRS を使用してください。"
    )

    # link_len 検証（Qneat3NetworkErrors.py — 距離最適化・方針 B）
    LINK_LEN_HEADER = (
        "リンク長の検証に失敗しました。"
        "距離・時間の両最適化で全リンクに正の link_len が必須です（フォールバックなし）。"
    )
    LINK_LEN_FIELD_EMPTY = (
        "リンク長フィールド名が未指定です。"
        "高度パラメータのリンク長フィールド（例: link_len）が必須です。"
    )
    LINK_LEN_FIELD_MISSING = (
        "レイヤにフィールド '{field}' がありません。"
        "利用可能なフィールド: {available}"
    )
    LINK_LEN_VALUE_NULL = (
        "フィーチャ ID={fid}, フィールド='{field}': 値が NULL / 空です。"
    )
    LINK_LEN_VALUE_NOT_NUMERIC = (
        "フィーチャ ID={fid}, フィールド='{field}': 数値に変換できません（値={value!r}）。"
    )
    LINK_LEN_VALUE_NOT_POSITIVE = (
        "フィーチャ ID={fid}, フィールド='{field}': 0 以下です。正の数が必要です（値={value!r}）。"
    )
    LINK_LEN_TRUNCATED = (
        "（表示は最初の {max} 件まで。全フィーチャを確認してください。）"
    )

    DEFAULT_SPEED_INVALID = (
        "時間最適化では「デフォルト速度 (km/h)」に正の値が必要です。\n"
        "最短経路（距離最適化）を選ぶ場合、速度パラメータは使用されません（0 でも可）。"
    )


class META:
    PLUGIN_NAME = "QNEAT3 - ネットワーク解析"
    PROVIDER_NAME = "QNEAT3 - QGIS ネットワーク解析ツールボックス"


def provider_display_name():
    """処理ツールボックスのプロバイダ名（バージョン付き）。"""
    try:
        from QNEAT3.Qneat3BuildInfo import BUILD_ID, read_metadata_version

        ver = read_metadata_version()
        return "QNEAT3 ({}, {})".format(ver, BUILD_ID)
    except Exception:
        return "QNEAT3 - QGIS ネットワーク解析ツールボックス"


def log_msg(feedback, template, **kwargs):
    """Processing ログ用（日本語固定）。"""
    feedback.pushInfo(template.format(**kwargs))


def log_cost_formulas(feedback, strategy_int):
    """グラフ構築前にコスト計算式をログへ明示する。"""
    if strategy_int == 0:
        feedback.pushInfo(LOG.FORMULA_EDGE_DISTANCE)
        feedback.pushInfo(LOG.FORMULA_CONN_DISTANCE)
    else:
        feedback.pushInfo(LOG.FORMULA_EDGE_TIME)
        feedback.pushInfo(LOG.FORMULA_CONN_TIME)


def log_path_cost_breakdown(feedback, strategy_int, entry, graph, exit_cost, total):
    """経路・OD 出力直前のコスト内訳ログ。"""
    if strategy_int == 0:
        feedback.pushInfo(LOG.PATH_COST_NOTE_DISTANCE)
    else:
        feedback.pushInfo(LOG.PATH_COST_NOTE_TIME)
    feedback.pushInfo(
        LOG.PATH_COST_VALUES.format(
            entry=entry, graph=graph, exit=exit_cost, total=total
        )
    )
