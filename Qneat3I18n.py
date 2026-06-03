# -*- coding: utf-8 -*-
"""
QNEAT3_NEO ロケール初期化。
QGIS の UI 言語が日本語のとき i18n/qneat3_ja.qm を読み込む。
qm が無い場合も、ソース文字列が日本語のため UI は日本語のまま動作する。
"""

import os

from qgis.PyQt.QtCore import QCoreApplication, QLocale, QTranslator


_TRANSLATOR = None


def plugin_dir():
    return os.path.dirname(os.path.abspath(__file__))


def install_plugin_translator():
    """プラグイン読み込み時に一度だけ呼ぶ。"""
    global _TRANSLATOR
    if _TRANSLATOR is not None:
        return

    # NEO: パラメータは ja() で日本語固定。qm があれば追加で上書き可能。
    trans = QTranslator()
    i18n_path = os.path.join(plugin_dir(), "i18n")
    for name in ("qneat3_ja", "QNEAT3_ja"):
        if trans.load(name, i18n_path):
            QCoreApplication.installTranslator(trans)
            _TRANSLATOR = trans
            break


def tr(context, message):
    """コンテキスト付き翻訳（qm がある場合のみ上書き）。"""
    return QCoreApplication.translate(context, message)
