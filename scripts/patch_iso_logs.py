# -*- coding: utf-8 -*-
from pathlib import Path

ALG = Path(__file__).resolve().parent.parent / "algs"
SUBS = [
    (
        'feedback.pushInfo("[QNEAT3Algorithm] Calculating Iso-Pointcloud...")',
        "log_msg(feedback, LOG.ISO_PC)",
    ),
    (
        'feedback.pushInfo("[QNEAT3Algorithm] Calculating Iso-Interpolation-Raster using QGIS TIN-Interpolator...")',
        "log_msg(feedback, LOG.ISO_TIN)",
    ),
    (
        'feedback.pushInfo("[QNEAT3Algorithm] Calculating Iso-Contours using numpy and matplotlib...")',
        "log_msg(feedback, LOG.ISO_CONTOURS)",
    ),
    (
        'feedback.pushInfo("[QNEAT3Algorithm] Calculating Iso-Polygons using numpy and matplotlib...")',
        "log_msg(feedback, LOG.ISO_POLYGONS)",
    ),
]

for path in ALG.glob("Iso*.py"):
    text = path.read_text(encoding="utf-8")
    orig = text
    if "LOG, log_msg" not in text and "from QNEAT3.Qneat3Strings import UIS" in text:
        text = text.replace(
            "from QNEAT3.Qneat3Strings import UIS, LOG, log_msg",
            "from QNEAT3.Qneat3Strings import UIS, LOG, log_msg",
        )
        if "LOG, log_msg" not in text:
            text = text.replace(
                "from QNEAT3.Qneat3Strings import UIS",
                "from QNEAT3.Qneat3Strings import UIS, LOG, log_msg",
            )
    for old, new in SUBS:
        text = text.replace(old, new)
    if text != orig:
        path.write_text(text, encoding="utf-8")
        print(path.name)
