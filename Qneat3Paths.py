# -*- coding: utf-8 -*-
"""プラグインルート・アイコンパス（フォルダ名が QNEAT3 / QNEAT3_NEO どちらでも動作）。"""

import os

_PLUGIN_ROOT = os.path.dirname(os.path.abspath(__file__))


def plugin_root():
    return _PLUGIN_ROOT


def icon_path(filename):
    """icons/ 配下の SVG 等への絶対パス。"""
    return os.path.join(_PLUGIN_ROOT, "icons", filename)


def plugin_icon_path():
    return os.path.join(_PLUGIN_ROOT, "icon_qneat3.svg")
