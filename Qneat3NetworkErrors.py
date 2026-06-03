# -*- coding: utf-8 -*-
"""
ネットワーク解析（リンク長フィールド）の検証とエラー報告。

方針 B: 距離・時間の両最適化で link_len（または指定フィールド）が必須。
未設定・NULL・非数値・0 以下はフォールバックせず処理を中断する。
ユーザー向け文言は Qneat3Strings.ERR の単一ソース。
"""

from enum import IntEnum

from qgis.core import QgsProcessingException
from qgis.PyQt.QtCore import QVariant

from QNEAT3.Qneat3Strings import ERR
from QNEAT3.Qneat3Utilities import (
    getFeaturesFromQgsIterable,
    getFieldIndexFromQgsProcessingFeatureSource,
)

# 距離最適化で想定するデフォルトフィールド名（UI の初期選択用）
DEFAULT_LINK_LENGTH_FIELD = "link_len"

# 一覧表示する不正フィーチャ件数の上限
MAX_REPORTED_FEATURES = 10


class LinkLengthErrorCode(IntEnum):
    """エラー種別（ログ・テスト用）。"""

    FIELD_NAME_EMPTY = 1
    FIELD_NOT_IN_LAYER = 2
    VALUE_NULL = 3
    VALUE_NOT_NUMERIC = 4
    VALUE_NOT_POSITIVE = 5


class LinkLengthValidationIssue:
    """1 フィーチャ分の検証問題。"""

    def __init__(self, code, feature_id, field_name, raw_value=None, detail=""):
        self.code = code
        self.feature_id = feature_id
        self.field_name = field_name
        self.raw_value = raw_value
        self.detail = detail

    def format_line(self):
        """ERR テンプレートから 1 行の説明を生成。"""
        fid = self.feature_id if self.feature_id is not None else "?"
        field = self.field_name or ""

        if self.code == LinkLengthErrorCode.FIELD_NAME_EMPTY:
            return ERR.LINK_LEN_FIELD_EMPTY
        if self.code == LinkLengthErrorCode.FIELD_NOT_IN_LAYER:
            return ERR.LINK_LEN_FIELD_MISSING.format(
                field=field,
                available=self.detail or "(なし)",
            )
        if self.code == LinkLengthErrorCode.VALUE_NULL:
            return ERR.LINK_LEN_VALUE_NULL.format(fid=fid, field=field)
        if self.code == LinkLengthErrorCode.VALUE_NOT_NUMERIC:
            return ERR.LINK_LEN_VALUE_NOT_NUMERIC.format(
                fid=fid, field=field, value=self.raw_value
            )
        if self.code == LinkLengthErrorCode.VALUE_NOT_POSITIVE:
            return ERR.LINK_LEN_VALUE_NOT_POSITIVE.format(
                fid=fid, field=field, value=self.raw_value
            )
        return "不明なリンク長検証エラー（コード={}）".format(int(self.code))


def _is_null_variant(value):
    if value is None:
        return True
    if isinstance(value, QVariant):
        return value.isNull() or value in (QVariant(),)
    try:
        return value != value  # NaN
    except TypeError:
        return False


def parse_positive_link_length(raw_value, feature_id, field_name):
    """
    リンク長を float に変換。不正なら LinkLengthValidationIssue を返す。

    Returns:
        tuple: (length: float|None, issue: LinkLengthValidationIssue|None)
    """
    if _is_null_variant(raw_value):
        return None, LinkLengthValidationIssue(
            LinkLengthErrorCode.VALUE_NULL, feature_id, field_name, raw_value
        )

    if isinstance(raw_value, str) and raw_value.strip() == "":
        return None, LinkLengthValidationIssue(
            LinkLengthErrorCode.VALUE_NULL, feature_id, field_name, raw_value
        )

    try:
        length = float(raw_value)
    except (TypeError, ValueError):
        return None, LinkLengthValidationIssue(
            LinkLengthErrorCode.VALUE_NOT_NUMERIC,
            feature_id,
            field_name,
            raw_value,
        )

    if length <= 0.0:
        return None, LinkLengthValidationIssue(
            LinkLengthErrorCode.VALUE_NOT_POSITIVE,
            feature_id,
            field_name,
            raw_value,
        )

    return length, None


def parse_speed_kmh(feature, speed_field_index, default_speed_kmh, feature_id):
    """
    フィーチャの速度 [km/h] を返す。速度フィールドが無効・NULL のときは default を使う。

    Returns:
        float | None: 正の速度。フィールドに 0 以下が明示されているとき None。
    """
    default = float(default_speed_kmh)
    if speed_field_index < 0:
        return default

    raw = feature.attribute(speed_field_index)
    if _is_null_variant(raw):
        return default
    if isinstance(raw, str) and raw.strip() == "":
        return default

    try:
        speed = float(raw)
    except (TypeError, ValueError):
        return default

    if speed <= 0.0:
        return None
    return speed


def validate_link_length_field_name(field_name):
    """フィールド名の事前チェック。問題があれば issue を 1 件返す。"""
    if not field_name or not str(field_name).strip():
        return LinkLengthValidationIssue(
            LinkLengthErrorCode.FIELD_NAME_EMPTY,
            None,
            field_name or "",
        )
    return None


def validate_link_length_field_exists(feature_source, field_name):
    """レイヤにフィールドがあるか。"""
    field_index = getFieldIndexFromQgsProcessingFeatureSource(
        feature_source, field_name
    )
    if field_index < 0:
        available = ", ".join(f.name() for f in feature_source.fields())
        return None, LinkLengthValidationIssue(
            LinkLengthErrorCode.FIELD_NOT_IN_LAYER,
            None,
            field_name,
            detail=available or "(なし)",
        )
    return field_index, None


def scan_network_link_lengths(feature_source, field_name, feedback=None):
    """
    ネットワーク全フィーチャの link_len を検証。

    Raises:
        QgsProcessingException: 1 件以上の問題がある場合
    """
    name_issue = validate_link_length_field_name(field_name)
    if name_issue:
        raise_processing_exception([name_issue])

    field_index, layer_issue = validate_link_length_field_exists(
        feature_source, field_name
    )
    if layer_issue:
        raise_processing_exception([layer_issue])

    issues = []
    feature_count = 0
    for feature in getFeaturesFromQgsIterable(feature_source):
        feature_count += 1
        raw = feature.attribute(field_index)
        fid = feature.id()
        _, issue = parse_positive_link_length(raw, fid, field_name)
        if issue:
            issues.append(issue)
            if len(issues) >= MAX_REPORTED_FEATURES:
                break

    if issues:
        extra = ""
        if feature_count > 0 and len(issues) >= MAX_REPORTED_FEATURES:
            extra = ERR.LINK_LEN_TRUNCATED.format(max=MAX_REPORTED_FEATURES)
        raise_processing_exception(issues, extra=extra)

    if feedback is not None:
        from QNEAT3.Qneat3Strings import LOG, log_msg

        log_msg(
            feedback,
            LOG.NET_LINK_LEN_VALIDATED,
            field=field_name,
            count=feature_count,
        )

    return field_index


def raise_processing_exception(issues, extra=""):
    """検証問題リストから QgsProcessingException を送出。"""
    lines = [issue.format_line() for issue in issues]
    body = "\n".join(lines)
    raise QgsProcessingException(ERR.LINK_LEN_HEADER + "\n" + body + extra)


def require_positive_default_speed(default_speed_kmh):
    """
    時間最適化用: デフォルト速度が正であること。

    Raises:
        QgsProcessingException: 0 以下または未設定
    """
    try:
        speed = float(default_speed_kmh)
    except (TypeError, ValueError):
        speed = 0.0
    if speed <= 0:
        raise QgsProcessingException(ERR.DEFAULT_SPEED_INVALID)


def require_link_length_field(link_length_field):
    """
    距離・時間の両モードでリンク長フィールド名が有効か確認。

    Raises:
        QgsProcessingException: フィールド名が空のとき
    """
    name_issue = validate_link_length_field_name(link_length_field)
    if name_issue:
        raise_processing_exception([name_issue])


# 後方互換（スクリプト・旧 import）
def require_link_length_for_distance_strategy(strategy_int, link_length_field):
    """非推奨: require_link_length_field を使用。"""
    if strategy_int != 0:
        return False
    require_link_length_field(link_length_field)
    return True
