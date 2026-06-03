# -*- coding: utf-8 -*-
from pathlib import Path

algs = Path(__file__).resolve().parents[1] / "algs"
for p in algs.glob("*.py"):
    t = p.read_text(encoding="utf-8")
    o = t
    for u in ("DISTANCE_MATRICES", "ISO_AREAS", "ROUTING"):
        t = t.replace(f"return ja(UIS.{u})", f"return ja(NEO_PREFIX + UIS.{u})")
    t = t.replace(
        "return ja(UIS.ISO_POLYGONS_FROM_POINT)",
        "return ja(NEO_PREFIX + UIS.ISO_POLYGONS_FROM_POINT)",
    )
    t = t.replace(
        "return self.tr('等時圏補間ラスタ（単一点）')",
        "return ja(NEO_PREFIX + '等時圏補間ラスタ（単一点）')",
    )
    t = t.replace(
        "return self.tr('等時圏補間ラスタ（レイヤ）')",
        "return ja(NEO_PREFIX + '等時圏補間ラスタ（レイヤ）')",
    )
    if "ja, NEO_PREFIX" not in t and "from QNEAT3.Qneat3Strings import" in t:
        t = t.replace(
            "from QNEAT3.Qneat3Strings import UIS, LOG, log_msg",
            "from QNEAT3.Qneat3Strings import UIS, LOG, log_msg, ja, NEO_PREFIX",
        )
    if t != o:
        p.write_text(t, encoding="utf-8")
        print(p.name)
