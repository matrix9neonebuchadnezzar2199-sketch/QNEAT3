# -*- coding: utf-8 -*-
"""プラグイン版・ビルド ID（プロバイダ表示・更新確認用）。"""

import os

from QNEAT3.Qneat3Paths import plugin_root

# 機能変更のたびに更新（プロバイダ名の区別に使う）
BUILD_ID = "20260805-segment-proration"
NEO_LINK_LEN_FEATURE = True


def read_metadata_version():
    """metadata.txt の version= を読む。失敗時は unknown。"""
    meta_path = os.path.join(plugin_root(), "metadata.txt")
    try:
        with open(meta_path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line.startswith("version="):
                    return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return "unknown"


def push_build_banner(feedback):
    """実行ログ先頭にバージョンと案内を出す。"""
    from QNEAT3.Qneat3Strings import log_run_intro

    version = read_metadata_version()
    feedback.pushInfo(
        "[QNEAT3 NEO] バージョン: {} | ビルドID: {}".format(version, BUILD_ID)
    )
    log_run_intro(feedback)
