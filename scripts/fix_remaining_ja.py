# -*- coding: utf-8 -*-
"""残存英語 UI 文字列を UIS / HelpJa に置換するワンショットスクリプト。"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALGS = ROOT / "algs"

REPLACEMENTS = [
    (
        "self.ENTRY_COST_CALCULATION_METHODS = [self.tr('Ellipsoidal'),\n                                               self.tr('Planar (only use with projected CRS)')]",
        "self.ENTRY_COST_CALCULATION_METHODS = entry_cost_labels(self.tr, include_ellipsoidal=True)",
    ),
    (
        "from QNEAT3.Qneat3ProcessingParams import add_advanced_network_params, strategy_labels",
        "from QNEAT3.Qneat3ProcessingParams import add_advanced_network_params, strategy_labels, entry_cost_labels",
    ),
    ("self.tr('Optimization criterion')", "self.tr(UIS.OPTIMIZATION_CRITERION)"),
    ("self.tr('Optimization Criterion')", "self.tr(UIS.OPTIMIZATION_CRITERION)"),
    ("self.tr('Output Pointcloud')", "ja(UIS.OUTPUT_POINTCLOUD)"),
    ("self.tr('Output Contours')", "ja(UIS.OUTPUT_CONTOURS)"),
    ("self.tr('Output Polygon')", "ja(UIS.OUTPUT_POLYGONS)"),
    ("self.tr('Output Polygons')", "ja(UIS.OUTPUT_POLYGONS)"),
    ("self.tr('Start Point')", "self.tr(UIS.START_POINT)"),
    ("self.tr('Startpoint Layer')", "self.tr(UIS.STARTPOINT_LAYER)"),
    (
        "self.tr('Vector layer representing network')",
        "self.tr(UIS.NETWORK_LAYER_DESC)",
    ),
    ("self.tr('Path type to calculate')", "self.tr(UIS.PATH_TYPE)"),
    (
        "return self.tr('Iso-Area as Polygons (from Point)')",
        "return self.tr(UIS.ISO_POLYGONS_FROM_POINT)",
    ),
    (
        "self.METHODS = [self.tr('QGIS TIN-Interpolation (faster but not exact)'),\n                        self.tr('QNEAT-Interpolation (slower but more exact')]",
        "self.METHODS = [self.tr(UIS.INTERP_TIN), self.tr(UIS.INTERP_QNEAT)]",
    ),
    ("self.tr('Interpolation Method')", "self.tr(UIS.INTERP_METHOD)"),
]

HELP_IMPORT = "from QNEAT3.Qneat3HelpJa import help_iso_qneat_interpolation_from_point"

DISPLAY_FIX = {
    "IsoAreaAsPolygonsFromPoint.py": "UIS.ISO_POLYGONS_FROM_POINT",
}


def patch_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    orig = text
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    if path.name == "OdMatrixFromLayersAsTable.py" and "entry_cost_labels" not in text:
        text = text.replace(
            "from QNEAT3.Qneat3ProcessingParams import add_advanced_network_params, strategy_labels\n",
            "from QNEAT3.Qneat3ProcessingParams import add_advanced_network_params, strategy_labels, entry_cost_labels\n",
        )
    if path.name == "IsoAreaAsQneatInterpolationFromPoint.py":
        if "help_iso_qneat_interpolation_from_point" not in text:
            if "from QNEAT3.Qneat3HelpJa import" in text:
                text = text.replace(
                    "from QNEAT3.Qneat3HelpJa import",
                    "from QNEAT3.Qneat3HelpJa import help_iso_qneat_interpolation_from_point, ",
                )
            else:
                text = text.replace(
                    "from QNEAT3.Qneat3Strings import UIS\n",
                    "from QNEAT3.Qneat3Strings import UIS\nfrom QNEAT3.Qneat3HelpJa import help_iso_qneat_interpolation_from_point\n",
                )
        if "def shortHelpString" in text and "help_iso_qneat" not in text.split("def shortHelpString")[1].split("def ")[0]:
            text = text.replace(
                "def shortHelpString(self):\n        return",
                "def shortHelpString(self):\n        return help_iso_qneat_interpolation_from_point()\n\n    def _shortHelpString_unused(self):\n        return",
                1,
            )
    if path.name in DISPLAY_FIX and f"return self.tr({DISPLAY_FIX[path.name]})" not in text:
        import re

        text = re.sub(
            r"def displayName\(self\):\s*\n\s*return self\.tr\([^)]+\)",
            f"def displayName(self):\n        return self.tr({DISPLAY_FIX[path.name]})",
            text,
            count=1,
        )
    if path.name == "OdMatrixFromPointsAsCsv.py":
        text = text.replace("        feedback.pushInfo(pluginPath)\n", "")
    if path.name == "DummyAlgorithm.py":
        text = text.replace(
            'self.tr("<b>[matplotlib not installed]</b><br>Some QNEAT3',
            'self.tr(UIS.DUMMY_MATPLOTLIB_PARAM)',
        )
        if "DUMMY_MATPLOTLIB_PARAM" in text and "from QNEAT3.Qneat3Strings import UIS" not in text:
            text = text.replace(
                "from qgis.PyQt.QtCore import QCoreApplication",
                "from qgis.PyQt.QtCore import QCoreApplication\nfrom QNEAT3.Qneat3Strings import UIS",
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
    print("patched:", ", ".join(changed) or "(none)")


if __name__ == "__main__":
    main()
