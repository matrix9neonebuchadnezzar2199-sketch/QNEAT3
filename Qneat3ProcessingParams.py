# -*- coding: utf-8 -*-
"""
Processing アルゴリズム共通の高度パラメータ登録。
"""

from collections import OrderedDict

from qgis.analysis import QgsVectorLayerDirector
from qgis.core import (
    QgsProcessingParameterDefinition,
    QgsProcessingParameterEnum,
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
)

from QNEAT3.Qneat3Strings import UIS, ja
from QNEAT3.Qneat3NetworkErrors import DEFAULT_LINK_LENGTH_FIELD

_PARAM_HELP = {
    "ENTRY_COST_CALCULATION_METHOD": UIS.ENTRY_COST_METHOD,
    "DIRECTION_FIELD": UIS.DIRECTION_FIELD,
    "SPEED_FIELD": UIS.HELP_SPEED_FIELD,
    "DEFAULT_SPEED": UIS.HELP_DEFAULT_SPEED,
    "LINK_LENGTH_FIELD": UIS.HELP_LINK_LEN_FIELD,
    "TOLERANCE": UIS.TOPOLOGY_TOLERANCE,
}


def directions_dict():
    return OrderedDict(
        [
            (ja(UIS.DIR_FORWARD), QgsVectorLayerDirector.DirectionForward),
            (ja(UIS.DIR_BACKWARD), QgsVectorLayerDirector.DirectionBackward),
            (ja(UIS.DIR_BOTH), QgsVectorLayerDirector.DirectionBoth),
        ]
    )


def strategy_labels():
    return [ja(UIS.STRATEGY_DISTANCE), ja(UIS.STRATEGY_TIME)]


def entry_cost_labels(include_ellipsoidal=True):
    """Framework: 0=楕円体, 1=平面。"""
    if include_ellipsoidal:
        return [ja(UIS.ENTRY_ELLIPSOIDAL), ja(UIS.ENTRY_PLANAR)]
    return [ja(UIS.ENTRY_PLANAR)]


def add_advanced_network_params(algorithm, input_param_name="INPUT"):
    """方向・速度・トポロジ・接続コスト・リンク長（将来用）を Advanced として追加。"""
    params = []
    params.append(
        QgsProcessingParameterEnum(
            algorithm.ENTRY_COST_CALCULATION_METHOD,
            ja(UIS.ENTRY_COST_METHOD),
            entry_cost_labels(include_ellipsoidal=True),
            defaultValue=0,
        )
    )
    params.append(
        QgsProcessingParameterField(
            algorithm.DIRECTION_FIELD,
            ja(UIS.DIRECTION_FIELD),
            None,
            input_param_name,
            optional=True,
        )
    )
    params.append(
        QgsProcessingParameterString(
            algorithm.VALUE_FORWARD, ja(UIS.VALUE_FORWARD), optional=True
        )
    )
    params.append(
        QgsProcessingParameterString(
            algorithm.VALUE_BACKWARD, ja(UIS.VALUE_BACKWARD), optional=True
        )
    )
    params.append(
        QgsProcessingParameterString(
            algorithm.VALUE_BOTH, ja(UIS.VALUE_BOTH), optional=True
        )
    )
    directions = directions_dict()
    params.append(
        QgsProcessingParameterEnum(
            algorithm.DEFAULT_DIRECTION,
            ja(UIS.DEFAULT_DIRECTION),
            list(directions.keys()),
            defaultValue=2,
        )
    )
    params.append(
        QgsProcessingParameterField(
            algorithm.SPEED_FIELD,
            ja(UIS.SPEED_FIELD),
            None,
            input_param_name,
            optional=True,
        )
    )
    params.append(
        QgsProcessingParameterNumber(
            algorithm.DEFAULT_SPEED,
            ja(UIS.DEFAULT_SPEED_KMH),
            QgsProcessingParameterNumber.Double,
            5.0,
            False,
            0,
            99999999.99,
        )
    )
    params.append(
        QgsProcessingParameterNumber(
            algorithm.TOLERANCE,
            ja(UIS.TOPOLOGY_TOLERANCE),
            QgsProcessingParameterNumber.Double,
            0.0,
            False,
            0,
            99999999.99,
        )
    )
    link_attr = getattr(algorithm, "LINK_LENGTH_FIELD", "LINK_LENGTH_FIELD")
    params.append(
        QgsProcessingParameterField(
            link_attr,
            ja(UIS.LINK_LENGTH_FIELD),
            DEFAULT_LINK_LENGTH_FIELD,
            input_param_name,
            optional=True,
        )
    )
    for param in params:
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        help_text = _PARAM_HELP.get(param.name())
        if help_text and hasattr(param, "setHelp"):
            param.setHelp(ja(help_text))
        algorithm.addParameter(param)

    return directions

