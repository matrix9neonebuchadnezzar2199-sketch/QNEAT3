# -*- coding: utf-8 -*-
"""
QNEAT3 NEO 統合品質チェック（QGIS 不要）。

起動時の SyntaxError・文字コード破損・シンボル未定義・欠落アイコン等の
「つまらないミス」をパック／コミット前に検出する。

使い方:
  python scripts/test_quality.py
  python TEST.py   # リポジトリルートから同等
"""
from __future__ import print_function

import ast
import compileall
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SKIP_DIRS = {"scripts", "__pycache__", "dist", ".git"}
PACKAGE_DIRS = {ROOT, ROOT / "algs"}

ICON_PATTERN = re.compile(
    r"icon_path\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
)


def _fail(msg):
    print("FAIL:", msg)
    return False


def check_compileall():
    """全 .py のバイトコードコンパイル。"""
    ok = compileall.compile_dir(
        str(ROOT),
        quiet=1,
        force=True,
        rx=re.compile(r"(\\|/)(\.git|dist|__pycache__)(\\|/|$)"),
    )
    if not ok:
        return _fail("compileall: syntax error in one or more .py files")
    print("OK: compileall (all .py)")
    return True


def check_utf8_no_bom():
    """UTF-8 デコード可能・BOM なし（プラグイン本体のみ）。"""
    errors = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix not in (".py", ".txt", ".md", ".html", ".svg", ".cpg", ".prj", ".qpj"):
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix == ".py" and "scripts" in path.parts:
            continue
        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            errors.append("{}: UTF-8 BOM detected".format(path.relative_to(ROOT)))
            continue
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            errors.append("{}: {}".format(path.relative_to(ROOT), exc))
    if errors:
        for line in errors:
            print(" ", line)
        return _fail("utf-8: {} file(s)".format(len(errors)))
    print("OK: utf-8 decode, no BOM (package files)")
    return True


def check_ast_parse():
    """ast.parse で構文木を構築（compileall 補完）。"""
    errors = []
    for path in sorted(ROOT.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            errors.append("{}: {}".format(path.relative_to(ROOT), exc))
    if errors:
        for line in errors:
            print(" ", line)
        return _fail("ast.parse: {} file(s)".format(len(errors)))
    print("OK: ast.parse (package .py)")
    return True


def check_coding_cookie():
    """日本語を含む .py には coding 宣言を推奨（欠落は警告）。"""
    warnings = []
    for path in sorted(ROOT.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        if not re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", text):
            continue
        head = "\n".join(text.splitlines()[:2])
        if "coding" not in head and "coding" not in text.splitlines()[0:3]:
            warnings.append(str(path.relative_to(ROOT)))
    if warnings:
        print("WARN: Japanese .py without coding cookie ({}): {}".format(
            len(warnings), ", ".join(warnings[:5])
        ))
        if len(warnings) > 5:
            print("  ... and", len(warnings) - 5, "more")
    else:
        print("OK: coding cookie on Japanese .py")
    return True


def check_icons_exist():
    """icon_path() / plugin アイコンが実ファイルを指す。"""
    errors = []
    icons_dir = ROOT / "icons"
    for path in sorted((ROOT / "algs").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for name in ICON_PATTERN.findall(text):
            target = icons_dir / name
            if not target.is_file():
                errors.append("{}: missing icons/{}".format(path.name, name))
    main_icon = ROOT / "icon_qneat3.svg"
    if not main_icon.is_file():
        errors.append("missing icon_qneat3.svg")
    if errors:
        for line in errors:
            print(" ", line)
        return _fail("icons: {} missing".format(len(errors)))
    print("OK: icon_path targets exist")
    return True


def check_provider_algs_sync():
    """Qneat3Provider.loadAlgorithms と algs/__init__.py の整合。"""
    provider = (ROOT / "Qneat3Provider.py").read_text(encoding="utf-8")
    init = (ROOT / "algs" / "__init__.py").read_text(encoding="utf-8")
    imports = re.findall(
        r"from QNEAT3\.algs import \(\s*([\s\S]*?)\)",
        provider,
    )
    if not imports:
        return _fail("provider: cannot parse algs import block")
    names = re.findall(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*,?\s*$", imports[0], re.M)
    for name in names:
        if name not in init or name not in init.split("__all__", 1)[-1]:
            return _fail("provider import {} not in algs/__init__.py".format(name))
    print("OK: Provider imports match algs/__init__.py")
    return True


def run_script(name):
    """scripts/ 配下の検証スクリプトを実行。"""
    path = SCRIPTS / name
    if not path.is_file():
        return _fail("missing script {}".format(name))
    proc = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(ROOT.parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        print(out.strip())
        return _fail("{} exited {}".format(name, proc.returncode))
    line = out.strip().splitlines()[-1] if out.strip() else "(no output)"
    print("OK:", name, "->", line)
    return True


def _install_qgis_stubs():
    """QGIS 無しで Qneat3NetworkErrors の純粋関数を import するための最小スタブ。"""
    if "qgis" in sys.modules and hasattr(sys.modules["qgis"].core, "QgsWkbTypes"):
        return

    class _FakeVariant:
        def __init__(self):
            self._null = True

        def isNull(self):
            return self._null

    class _FakeProcessingException(Exception):
        pass

    class _Stub:
        """未定義の Qgs* 参照用プレースホルダ。"""

        pass

    def _make_module(names):
        mod = _Stub()
        for name in names:
            setattr(mod, name, _Stub())
        return mod

    core_names = (
        "QgsProcessingException",
        "QgsWkbTypes",
        "QgsMessageLog",
        "QgsVectorLayer",
        "QgsFeature",
        "QgsGeometry",
        "QgsFields",
        "QgsField",
        "QgsFeatureRequest",
        "QgsPointXY",
        "QgsLineString",
        "QgsDistanceArea",
        "QgsUnitTypes",
        "QgsProject",
        "QgsPoint",
        "QgsRasterLayer",
        "QgsFeatureSink",
        "QgsProcessing",
    )
    core = _make_module(core_names)
    core.QgsProcessingException = _FakeProcessingException

    analysis_names = (
        "QgsVectorLayerDirector",
        "QgsGraphAnalyzer",
        "QgsGraphBuilder",
        "QgsNetworkStrategy",
        "QgsInterpolator",
        "QgsTinInterpolator",
        "QgsGridFileWriter",
    )
    analysis = _make_module(analysis_names)

    qt_core = _Stub()
    qt_core.QVariant = _FakeVariant

    qgis = _Stub()
    qgis.core = core
    qgis.analysis = analysis
    qgis.PyQt = _Stub()
    qgis.PyQt.QtCore = qt_core
    qgis.PyQt.QtGui = _make_module(("QIcon",))

    sys.modules["qgis"] = qgis
    sys.modules["qgis.core"] = core
    sys.modules["qgis.analysis"] = analysis
    sys.modules["qgis.PyQt"] = qgis.PyQt
    sys.modules["qgis.PyQt.QtCore"] = qt_core
    sys.modules["qgis.PyQt.QtGui"] = qgis.PyQt.QtGui


def check_link_len_parsers():
    """リンク長・速度パーサの単体チェック（QGIS スタブ）。"""
    _install_qgis_stubs()
    parent = str(ROOT.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)
    # 既存 import をクリアしてスタブ付きで再読込
    for key in list(sys.modules):
        if key.startswith("QNEAT3"):
            del sys.modules[key]

    from QNEAT3.Qneat3NetworkErrors import (  # noqa: E402
        LinkLengthErrorCode,
        parse_positive_link_length,
        parse_speed_kmh,
        require_positive_default_speed,
    )
    from QNEAT3.Qneat3Strings import ERR  # noqa: E402

    length, issue = parse_positive_link_length(100.5, 1, "link_len")
    if issue or length != 100.5:
        return _fail("parse_positive_link_length valid value")

    _, issue = parse_positive_link_length(None, 2, "link_len")
    if not issue or issue.code != LinkLengthErrorCode.VALUE_NULL:
        return _fail("parse_positive_link_length NULL")

    _, issue = parse_positive_link_length(-1, 3, "link_len")
    if not issue or issue.code != LinkLengthErrorCode.VALUE_NOT_POSITIVE:
        return _fail("parse_positive_link_length non-positive")

    class _Feat:
        def __init__(self, attrs):
            self._attrs = attrs

        def attribute(self, idx):
            return self._attrs.get(idx)

        def id(self):
            return 1

    speed = parse_speed_kmh(_Feat({0: 60.0}), 0, 50.0, 1)
    if speed != 60.0:
        return _fail("parse_speed_kmh field value")

    speed = parse_speed_kmh(_Feat({0: None}), 0, 50.0, 1)
    if speed != 50.0:
        return _fail("parse_speed_kmh default")

    try:
        require_positive_default_speed(0)
        return _fail("require_positive_default_speed should raise")
    except Exception as exc:
        if ERR.DEFAULT_SPEED_INVALID not in str(exc):
            return _fail("require_positive_default_speed message")

    print("OK: link_len / speed parsers (unit)")
    return True


def check_network_prep_core():
    """前処理コア（純粋関数・QGIS 不要）の単体チェック。"""
    parent = str(ROOT.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)
    from QNEAT3.Qneat3NetworkPrep import (  # noqa: E402
        apply_plan,
        connected_components,
        plan_endpoint_attachments,
        prorate_value,
        split_polyline,
    )

    parts = split_polyline([(0, 0), (10, 0)], [(0, 0.5)])
    if parts != [[(0, 0), (5.0, 0.0)], [(5.0, 0.0), (10, 0)]]:
        return _fail("split_polyline basic")

    # T 字接続: branch の終点 (5, 0.5) が main の途中 0.5 に突き当たる
    main = [(0, 0), (10, 0)]
    branch = [(5, 3), (5, 0.5)]
    lines = [main, branch]
    cuts, snaps, _stats = plan_endpoint_attachments(lines, 1.0)
    if 0 not in cuts:
        return _fail("plan_endpoint_attachments: no cut on main link")
    if snaps.get((1, 1)) != (5.0, 0.0):
        return _fail("plan_endpoint_attachments: branch endpoint not snapped")

    parts_per_line, snapped = apply_plan(lines, cuts, snaps)
    if len(parts_per_line[0]) != 2:
        return _fail("apply_plan: main link not split into 2 parts")

    values = prorate_value(100.0, snapped[0], parts_per_line[0])
    if abs(sum(values) - 100.0) > 1e-9 or abs(values[0] - 50.0) > 1e-9:
        return _fail("prorate_value: total not preserved")

    flat = [part for parts in parts_per_line for part in parts]
    if len(connected_components(flat, 1.0)) != 1:
        return _fail("connected_components: T junction should be connected")
    if len(connected_components(flat + [[(100, 100), (200, 100)]], 1.0)) != 2:
        return _fail("connected_components: isolated link not detected")

    # セル境界またぎ（round 量子化では取りこぼすケース）
    straddle = [[(0, 0), (4.5, 0)], [(5.5, 0), (10, 0)]]
    if len(connected_components(straddle, 1.0)) != 1:
        return _fail("connected_components: tolerance-edge straddle missed")

    print("OK: network prep core (unit)")
    return True


def check_classfactory_source():
    """__init__.py classFactory が存在し import パスが正しい。"""
    init_py = ROOT / "__init__.py"
    text = init_py.read_text(encoding="utf-8")
    if "def classFactory" not in text:
        return _fail("__init__.py: missing classFactory")
    if "Qneat3Plugin" not in text:
        return _fail("__init__.py: missing Qneat3Plugin import")
    print("OK: __init__.py classFactory")
    return True


def main():
    print("QNEAT3 NEO quality check:", ROOT)
    print("=" * 60)
    steps = [
        check_compileall,
        check_utf8_no_bom,
        check_ast_parse,
        check_coding_cookie,
        check_icons_exist,
        check_provider_algs_sync,
        check_classfactory_source,
        check_link_len_parsers,
        check_network_prep_core,
        lambda: run_script("validate_metadata.py"),
        lambda: run_script("validate_uis_refs.py"),
        lambda: run_script("validate_network_errors.py"),
        lambda: run_script("validate_all_symbol_refs.py"),
        lambda: run_script("verify_provider_register.py"),
    ]
    failed = 0
    for step in steps:
        if not step():
            failed += 1
    print("=" * 60)
    if failed:
        print("RESULT: FAIL ({} step(s))".format(failed))
        sys.exit(1)
    print("RESULT: PASS (all checks)")
    sys.exit(0)


if __name__ == "__main__":
    main()
