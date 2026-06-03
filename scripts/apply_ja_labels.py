# -*- coding: utf-8 -*-
"""self.tr(UIS.*) を ja(UIS.*) に一括置換。strategy_labels 等の API 更新。"""
from pathlib import Path

ALGS = Path(__file__).resolve().parents[1] / "algs"
ROOT = Path(__file__).resolve().parents[1]

REPLACEMENTS = [
    ("self.tr(UIS.", "ja(UIS."),
    ("strategy_labels(self.tr)", "strategy_labels()"),
    ("entry_cost_labels(self.tr, include_ellipsoidal=True)", "entry_cost_labels(include_ellipsoidal=True)"),
    ("entry_cost_labels(self.tr, include_ellipsoidal=False)", "entry_cost_labels(include_ellipsoidal=False)"),
    ("entry_cost_labels(self.tr)", "entry_cost_labels()"),
    ("add_advanced_network_params(self, self.tr, self.INPUT)", "add_advanced_network_params(self, self.INPUT)"),
    ("add_advanced_network_params(self, self.tr,", "add_advanced_network_params(self,"),
    ("from QNEAT3.Qneat3Strings import UIS, LOG", "from QNEAT3.Qneat3Strings import UIS, LOG, ja, NEO_PREFIX"),
    ("from QNEAT3.Qneat3Strings import UIS\n", "from QNEAT3.Qneat3Strings import UIS, ja, NEO_PREFIX\n"),
    (", entry_cost_labels, entry_cost_labels", ", entry_cost_labels"),
]

DISPLAY = {
    "ShortestPathBetweenPoints.py": "最短経路（点間）",
    "OdMatrixFromPointsAsTable.py": "OD 行列（ポイント・表 n:n）",
    "OdMatrixFromPointsAsLines.py": "OD 行列（ポイント・ライン n:n）",
    "OdMatrixFromPointsAsCsv.py": "OD 行列（ポイント・CSV n:n）",
    "OdMatrixFromLayersAsTable.py": "OD 行列（レイヤ間・表 m:n）",
    "OdMatrixFromLayersAsLines.py": "OD 行列（レイヤ間・ライン m:n）",
    "IsoAreaAsPointcloudFromPoint.py": "等時点クラウド（単一点）",
    "IsoAreaAsPointcloudFromLayer.py": "等時点クラウド（レイヤ）",
    "IsoAreaAsInterpolationFromPoint.py": "等時圏 TIN 補間（単一点）",
    "IsoAreaAsInterpolationFromLayer.py": "等時圏 TIN 補間（レイヤ）",
    "IsoAreaAsContoursFromPoint.py": "等時圏等値線（単一点）",
    "IsoAreaAsContoursFromLayer.py": "等時圏等値線（レイヤ）",
    "IsoAreaAsPolygonsFromPoint.py": None,  # uses UIS.ISO_POLYGONS_FROM_POINT
    "IsoAreaAsPolygonsFromLayer.py": "等時圏ポリゴン（レイヤ）",
    "IsoAreaAsQneatInterpolationFromPoint.py": "等時圏 QNEAT 補間（単一点）",
    "DummyAlgorithm.py": "等時圏ポリゴン（matplotlib 導入ヘルプ）",
}


def patch_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    orig = text
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    if "ja" in text and "from QNEAT3.Qneat3Strings import" in text and ", ja" not in text.split("initAlgorithm")[0]:
        text = text.replace(
            "from QNEAT3.Qneat3Strings import UIS, LOG, log_msg",
            "from QNEAT3.Qneat3Strings import UIS, LOG, log_msg, ja, NEO_PREFIX",
        )
    if path.name in DISPLAY and DISPLAY[path.name]:
        text = text.replace(
            f"return self.tr('{DISPLAY[path.name]}')",
            f"return ja(NEO_PREFIX + '{DISPLAY[path.name]}')",
        )
    if "def group(self):" in text and "NEO_PREFIX" in text:
        text = text.replace(
            "return self.tr(UIS.DISTANCE_MATRICES)",
            "return ja(NEO_PREFIX + UIS.DISTANCE_MATRICES)",
        )
        text = text.replace(
            "return self.tr(UIS.ISO_AREAS)",
            "return ja(NEO_PREFIX + UIS.ISO_AREAS)",
        )
        text = text.replace(
            "return self.tr(UIS.ROUTING)",
            "return ja(NEO_PREFIX + UIS.ROUTING)",
        )
    if path.name == "IsoAreaAsPolygonsFromPoint.py":
        text = text.replace(
            "return self.tr(UIS.ISO_POLYGONS_FROM_POINT)",
            "return ja(NEO_PREFIX + UIS.ISO_POLYGONS_FROM_POINT)",
        )
    if path.name == "DummyAlgorithm.py":
        text = text.replace(
            "return self.tr('[matplotlib 未導入]",
            "return ja(NEO_PREFIX + '[matplotlib 未導入]",
        )
    if text != orig:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main():
    changed = []
    for path in sorted(ALGS.glob("*.py")):
        if patch_file(path):
            changed.append(path.name)
    print("patched algs:", ", ".join(changed) or "(none)")


if __name__ == "__main__":
    main()
