# -*- coding: utf-8 -*-
"""アルゴリズムファイルに日本語 UI 用 import と共通置換を適用（一回限り）。"""

import re
from pathlib import Path

ALG_DIR = Path(__file__).resolve().parent.parent / "algs"

IMPORT_BLOCK = """from QNEAT3.Qneat3Strings import UIS, LOG, log_msg
from QNEAT3.Qneat3ProcessingParams import add_advanced_network_params, strategy_labels, entry_cost_labels
"""

REPLACEMENTS = [
    ("return self.tr('Distance Matrices')", "return self.tr(UIS.DISTANCE_MATRICES)"),
    ("return self.tr('Iso-Areas')", "return self.tr(UIS.ISO_AREAS)"),
    ("return self.tr('Routing')", "return self.tr(UIS.ROUTING)"),
    ("self.tr('Network Layer')", "self.tr(UIS.NETWORK_LAYER)"),
    ("self.tr('Network layer')", "self.tr(UIS.NETWORK_LAYER)"),
    ("self.tr('Point Layer')", "self.tr(UIS.POINT_LAYER)"),
    ("self.tr('Start point')", "self.tr(UIS.START_POINT)"),
    ("self.tr('Start Points')", "self.tr(UIS.START_POINTS)"),
    ("self.tr('From-Point Layer')", "self.tr(UIS.FROM_POINT_LAYER)"),
    ("self.tr('To-Point Layer')", "self.tr(UIS.TO_POINT_LAYER)"),
    ("self.tr('Unique Point ID Field')", "self.tr(UIS.UNIQUE_POINT_ID)"),
    ("self.tr('Optimization Criterion')", "self.tr(UIS.OPTIMIZATION_CRITERION)"),
    ("self.tr('Output OD Matrix')", "self.tr(UIS.OUTPUT_OD_MATRIX)"),
    ("self.tr('Output Interpolation')", "self.tr(UIS.OUTPUT_INTERPOLATION)"),
    (
        "feedback.pushInfo(self.tr(\"[QNEAT3Algorithm] This is a QNEAT3 Algorithm: '{}'\".format(self.displayName())))",
        "log_msg(feedback, LOG.ALG_START, name=self.displayName())",
    ),
    ('feedback.pushInfo("[QNEAT3Algorithm] Building Graph...")', "log_msg(feedback, LOG.ALG_BUILD_GRAPH)"),
    ('feedback.pushInfo("[QNEAT3Algorithm] Ending Algorithm")', "log_msg(feedback, LOG.ALG_END)"),
    (
        'feedback.pushInfo("[QNEAT3Algorithm] Expecting total workload of {} iterations".format(int(total_workload)))',
        "log_msg(feedback, LOG.OD_WORKLOAD, n=int(total_workload))",
    ),
    (
        'feedback.pushInfo("[QNEAT3Algorithm] {} OD-pairs processed...".format(current_workstep_number))',
        "log_msg(feedback, LOG.OD_PROGRESS, n=current_workstep_number)",
    ),
    (
        'feedback.pushInfo("[QNEAT3Algorithm] Total number of OD-pairs processed: {}".format(current_workstep_number))',
        "log_msg(feedback, LOG.OD_TOTAL, n=current_workstep_number)",
    ),
]


def patch_file(path: Path) -> bool:
    if path.name in ("ShortestPathBetweenPoints.py", "DummyAlgorithm.py"):
        return False
    text = path.read_text(encoding="utf-8")
    orig = text
    if "from QNEAT3.Qneat3Strings import UIS" not in text:
        marker = "from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm"
        if marker in text:
            text = text.replace(marker, IMPORT_BLOCK + "\n" + marker)
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    if text != orig:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main():
    changed = []
    for py in sorted(ALG_DIR.glob("*.py")):
        if patch_file(py):
            changed.append(py.name)
    print("patched:", ", ".join(changed) or "(none)")


if __name__ == "__main__":
    main()
