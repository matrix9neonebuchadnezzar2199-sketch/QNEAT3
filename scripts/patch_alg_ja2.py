# -*- coding: utf-8 -*-
import re
from pathlib import Path

ALG_DIR = Path(__file__).resolve().parent.parent / "algs"

DISPLAY = {
    "OdMatrixFromPointsAsTable.py": "OD 行列（ポイント・表 n:n）",
    "OdMatrixFromPointsAsLines.py": "OD 行列（ポイント・ライン n:n）",
    "OdMatrixFromPointsAsCsv.py": "OD 行列（ポイント・CSV n:n）",
    "OdMatrixFromLayersAsTable.py": "OD 行列（レイヤ間・表 m:n）",
    "OdMatrixFromLayersAsLines.py": "OD 行列（レイヤ間・ライン m:n）",
    "IsoAreaAsPointcloudFromPoint.py": "等時点クラウド（単一点）",
    "IsoAreaAsPointcloudFromLayer.py": "等時点クラウド（レイヤ）",
    "IsoAreaAsInterpolationFromPoint.py": "等時圏補間ラスタ（単一点）",
    "IsoAreaAsInterpolationFromLayer.py": "等時圏補間ラスタ（レイヤ）",
    "IsoAreaAsContoursFromPoint.py": "等時圏等値線（単一点）",
    "IsoAreaAsContoursFromLayer.py": "等時圏等値線（レイヤ）",
    "IsoAreaAsPolygonsFromPoint.py": "等時圏ポリゴン（単一点）",
    "IsoAreaAsPolygonsFromLayer.py": "等時圏ポリゴン（レイヤ）",
    "IsoAreaAsQneatInterpolationFromPoint.py": "等時圏 QNEAT 補間（単一点）",
}

HELP_IMPORT = {
    "OdMatrixFromPointsAsTable.py": "help_od_matrix_points_table",
    "OdMatrixFromPointsAsLines.py": "help_od_matrix_points_lines",
    "OdMatrixFromPointsAsCsv.py": "help_od_matrix_points_csv",
    "OdMatrixFromLayersAsTable.py": "help_od_matrix_layers_table",
    "OdMatrixFromLayersAsLines.py": "help_od_matrix_layers_lines",
    "IsoAreaAsPointcloudFromPoint.py": "help_iso_pointcloud_from_point",
    "IsoAreaAsPointcloudFromLayer.py": "help_iso_pointcloud_from_layer",
    "IsoAreaAsInterpolationFromPoint.py": "help_iso_interpolation_from_point",
    "IsoAreaAsInterpolationFromLayer.py": "help_iso_interpolation_from_layer",
    "IsoAreaAsContoursFromPoint.py": "help_iso_contours_from_point",
    "IsoAreaAsContoursFromLayer.py": "help_iso_contours_from_layer",
    "IsoAreaAsPolygonsFromPoint.py": "help_iso_polygons_from_point",
    "IsoAreaAsPolygonsFromLayer.py": "help_iso_polygons_from_layer",
}

SUBS = [
    ("self.tr('Forward direction')", "self.tr(UIS.DIR_FORWARD)"),
    ("self.tr('Backward direction')", "self.tr(UIS.DIR_BACKWARD)"),
    ("self.tr('Both directions')", "self.tr(UIS.DIR_BOTH)"),
    ("self.tr('Entry Cost calculation method')", "self.tr(UIS.ENTRY_COST_METHOD)"),
    ("self.tr('Direction field')", "self.tr(UIS.DIRECTION_FIELD)"),
    ("self.tr('Value for forward direction')", "self.tr(UIS.VALUE_FORWARD)"),
    ("self.tr('Value for backward direction')", "self.tr(UIS.VALUE_BACKWARD)"),
    ("self.tr('Value for both directions')", "self.tr(UIS.VALUE_BOTH)"),
    ("self.tr('Default direction')", "self.tr(UIS.DEFAULT_DIRECTION)"),
    ("self.tr('Speed field')", "self.tr(UIS.SPEED_FIELD)"),
    ("self.tr('Default speed (km/h)')", "self.tr(UIS.DEFAULT_SPEED_KMH)"),
    ("self.tr('Topology tolerance')", "self.tr(UIS.TOPOLOGY_TOLERANCE)"),
    (
        "self.tr('Size of Iso-Area (distance or time value)')",
        "self.tr(UIS.ISO_SIZE)",
    ),
    (
        "self.tr('Contour Interval (distance or time value)')",
        "self.tr(UIS.ISO_INTERVAL)",
    ),
    (
        "self.tr('Cellsize of interpolation raster')",
        "self.tr(UIS.ISO_CELLSIZE)",
    ),
    (
        "self.tr('Size of Iso-Area (distance or seconds depending on strategy)')",
        "self.tr(UIS.ISO_SIZE)",
    ),
    (
        "self.tr('Size of Iso-Area (Distance or Seconds depending on Strategy)')",
        "self.tr(UIS.ISO_SIZE)",
    ),
    (
        "self.tr('Generated matrix geometry style')",
        "self.tr('行列ジオメトリの形式')",
    ),
    (
        "self.tr('Matrix geometry follows straight lines (as the crow flies)')",
        "self.tr(UIS.MATRIX_GEOM_STRAIGHT)",
    ),
    (
        "self.tr('Matrix geometry follows routes')",
        "self.tr(UIS.MATRIX_GEOM_ROUTE)",
    ),
    ("self.tr('CSV files (*.csv)')", "self.tr(UIS.CSV_FILES_FILTER)"),
    ("self.tr('Output OD Matrix')", "self.tr(UIS.OUTPUT_OD_MATRIX)"),
    (
        "self.tr('Output Interpolation')",
        "self.tr(UIS.OUTPUT_INTERPOLATION)",
    ),
    (
        "self.tr('Output Iso-Area Contours')",
        "self.tr(UIS.OUTPUT_CONTOURS)",
    ),
    (
        "self.tr('Output Iso-Area Polygons')",
        "self.tr(UIS.OUTPUT_POLYGONS)",
    ),
    (
        "self.tr('Output Iso-Area Pointcloud')",
        "self.tr(UIS.OUTPUT_POINTCLOUD)",
    ),
]


def patch_help(path: Path, text: str) -> str:
    fn = HELP_IMPORT.get(path.name)
    if not fn:
        return text
    if f"from QNEAT3.Qneat3HelpJa import {fn}" in text:
        return text
    text = text.replace(
        "from QNEAT3.Qneat3ProcessingParams import",
        f"from QNEAT3.Qneat3HelpJa import {fn}\nfrom QNEAT3.Qneat3ProcessingParams import",
    )
    pattern = re.compile(
        r"    def shortHelpString\(self\):\s*return\s+.*?(\n    \n    def |\n    def )",
        re.DOTALL,
    )
    repl = f"    def shortHelpString(self):\n        return {fn}()\n\\1"
    text, n = pattern.subn(repl, text, count=1)
    return text


def main():
    for path in ALG_DIR.glob("*.py"):
        if path.name == "ShortestPathBetweenPoints.py":
            continue
        text = path.read_text(encoding="utf-8")
        orig = text
        if path.name in DISPLAY:
            text = re.sub(
                r"return self\.tr\('[^']+'\)\s*\n\s*def shortHelpString",
                f"return self.tr('{DISPLAY[path.name]}')\n\n    def shortHelpString",
                text,
                count=1,
            )
        text = re.sub(
            r"self\.STRATEGIES = \[self\.tr\('Shortest Path \(distance optimization\)'\),[^\]]+\]",
            "self.STRATEGIES = strategy_labels(self.tr)",
            text,
        )
        text = text.replace(
            "self.ENTRY_COST_CALCULATION_METHODS = [self.tr('Ellipsoidal'),\n                                       self.tr('Planar (only use with projected CRS)')]",
            "self.ENTRY_COST_CALCULATION_METHODS = entry_cost_labels(self.tr, include_ellipsoidal=True)",
        )
        text = text.replace(
            "self.ENTRY_COST_CALCULATION_METHODS = [self.tr('Planar (only use with projected CRS)')]",
            "self.ENTRY_COST_CALCULATION_METHODS = entry_cost_labels(self.tr, include_ellipsoidal=True)",
        )
        for old, new in SUBS:
            text = text.replace(old, new)
        text = patch_help(path, text)
        if path.name == "DummyAlgorithm.py":
            text = text.replace(
                "return self.tr('Iso-Areas')", "return self.tr(UIS.ISO_AREAS)"
            )
            text = text.replace(
                "return self.tr('[matplotlib not installed] Iso-Area as Polygon (open for install help)')",
                "return self.tr('[matplotlib 未導入] 等時圏ポリゴン（導入ヘルプ）')",
            )
            if "from QNEAT3.Qneat3Strings import UIS" not in text:
                text = text.replace(
                    "from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm",
                    "from QNEAT3.Qneat3Strings import UIS\nfrom QNEAT3.Qneat3HelpJa import help_dummy_matplotlib\nfrom processing.algs.qgis.QgisAlgorithm import QgisAlgorithm",
                )
            text = re.sub(
                r"    def shortHelpString\(self\):.*?(?=\n    def )",
                "    def shortHelpString(self):\n        return help_dummy_matplotlib()\n",
                text,
                count=1,
                flags=re.DOTALL,
            )
            text = text.replace(
                'feedback.pushInfo("You need to install matplotlib to enable this algorithm.")',
                'feedback.pushInfo("このアルゴリズムを使用するには matplotlib のインストールが必要です。")',
            )
        if text != orig:
            path.write_text(text, encoding="utf-8")
            print("ok", path.name)


if __name__ == "__main__":
    main()
