# -*- coding: utf-8 -*-
"""
QNEAT3 NEO プラグインエントリ。
読み込み失敗時はプラグインフォルダに NEO_load_error.txt を書き出す。
"""

import os
import traceback


def classFactory(iface):
    try:
        from QNEAT3.Qneat3Plugin import Qneat3Plugin

        return Qneat3Plugin(iface)
    except Exception:
        err_path = os.path.join(os.path.dirname(__file__), "NEO_load_error.txt")
        try:
            with open(err_path, "w", encoding="utf-8") as handle:
                handle.write("QNEAT3 NEO プラグイン読み込みエラー\n")
                handle.write("=" * 60 + "\n")
                traceback.print_exc(file=handle)
                handle.write(
                    "\n対処: README.html の「プラグインが壊れている」を参照。"
                    "公式の「再インストール」は使わないでください。\n"
                )
        except OSError:
            pass
        raise
