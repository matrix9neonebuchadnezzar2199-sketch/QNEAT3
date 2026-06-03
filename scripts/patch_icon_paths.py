# -*- coding: utf-8 -*-
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
ALG = ROOT / "algs"

OLD_BLOCK = re.compile(
    r"pluginPath = os\.path\.split\(os\.path\.split\(os\.path\.dirname\(__file__\)\)\[0\]\)\[0\]\n\n",
)

ICON_LINE = re.compile(
    r"return QIcon\(os\.path\.join\(pluginPath, 'QNEAT3', 'icons', '([^']+)'\)\)"
)


def patch_alg(path: Path):
    text = path.read_text(encoding="utf-8")
    if "Qneat3Paths import icon_path" in text:
        return False
    if "pluginPath = os.path.split" not in text:
        return False
    text = OLD_BLOCK.sub("", text)
    if "from QNEAT3.Qneat3Paths import icon_path" not in text:
        text = text.replace(
            "from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm",
            "from QNEAT3.Qneat3Paths import icon_path\nfrom processing.algs.qgis.QgisAlgorithm import QgisAlgorithm",
        )
    text = ICON_LINE.sub(r"return QIcon(icon_path('\1'))", text)
    path.write_text(text, encoding="utf-8")
    return True


def main():
    for py in ALG.glob("*.py"):
        if patch_alg(py):
            print(py.name)


if __name__ == "__main__":
    main()
