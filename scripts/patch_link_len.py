# -*- coding: utf-8 -*-
"""link_len 対応: 全アルゴリズムに LINK_LENGTH_FIELD と Qneat3Network 引数を追加。"""
import re
from pathlib import Path

ALG = Path(__file__).resolve().parent.parent / "algs"

PARAMS_BLOCK = re.compile(
    r"\n        params = \[\].*?\n        for p in params:\n"
    r"            p\.setFlags\(p\.flags\(\) \| QgsProcessingParameterDefinition\.FlagAdvanced\)\n"
    r"            self\.addParameter\(p\)\n",
    re.DOTALL,
)

NETWORK_CALL = re.compile(
    r"net = Qneat3Network\((.*?), tolerance, feedback\)",
    re.DOTALL,
)


def patch_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    orig = text

    if "LINK_LENGTH_FIELD" not in text and "TOLERANCE = " in text:
        text = text.replace(
            "    TOLERANCE = 'TOLERANCE'\n",
            "    TOLERANCE = 'TOLERANCE'\n    LINK_LENGTH_FIELD = 'LINK_LENGTH_FIELD'\n",
        )

    if PARAMS_BLOCK.search(text) and "add_advanced_network_params(self" not in text.split("def processAlgorithm")[0]:
        text = PARAMS_BLOCK.sub(
            "\n        add_advanced_network_params(self, self.tr, self.INPUT)\n",
            text,
            count=1,
        )

    if "link_length_field" not in text and "tolerance = self.parameterAsDouble" in text:
        text = text.replace(
            "tolerance = self.parameterAsDouble(parameters, self.TOLERANCE, context) #float",
            "tolerance = self.parameterAsDouble(parameters, self.TOLERANCE, context) #float\n"
            "        link_length_field = self.parameterAsString(parameters, self.LINK_LENGTH_FIELD, context)",
        )
        text = text.replace(
            "tolerance = self.parameterAsDouble(parameters, self.TOLERANCE, context)",
            "tolerance = self.parameterAsDouble(parameters, self.TOLERANCE, context)\n"
            "        link_length_field = self.parameterAsString(parameters, self.LINK_LENGTH_FIELD, context)",
            1,
        )

    def repl_net(m):
        inner = m.group(1).strip()
        if "link_length_field" in inner:
            return m.group(0)
        return "net = Qneat3Network({}, link_length_field, feedback)".format(inner + ", tolerance")

    text = NETWORK_CALL.sub(repl_net, text)

    if path.name == "ShortestPathBetweenPoints.py":
        if "LINK_LENGTH_FIELD" not in text:
            text = text.replace(
                "    TOLERANCE = 'TOLERANCE'\n    OUTPUT",
                "    TOLERANCE = 'TOLERANCE'\n    LINK_LENGTH_FIELD = 'LINK_LENGTH_FIELD'\n    OUTPUT",
            )
        text = text.replace(
            "        tolerance = self.parameterAsDouble(parameters, self.TOLERANCE, context)\n\n        analysisCrs",
            "        tolerance = self.parameterAsDouble(parameters, self.TOLERANCE, context)\n"
            "        link_length_field = self.parameterAsString(parameters, self.LINK_LENGTH_FIELD, context)\n\n        analysisCrs",
        )
        text = re.sub(
            r"net = Qneat3Network\(\s*network, input_qgspointxy_list, strategy,.*?tolerance, feedback\s*\)",
            lambda m: m.group(0).replace("tolerance, feedback", "tolerance, link_length_field, feedback")
            if "link_length_field" not in m.group(0)
            else m.group(0),
            text,
            count=1,
            flags=re.DOTALL,
        )

    if text != orig:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main():
    for py in sorted(ALG.glob("*.py")):
        if py.name == "DummyAlgorithm.py":
            continue
        if patch_file(py):
            print("patched", py.name)


if __name__ == "__main__":
    main()
