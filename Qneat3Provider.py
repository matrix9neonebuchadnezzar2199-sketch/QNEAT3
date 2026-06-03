# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QNEAT3 - Qgis Network Analysis Toolbox 3
 A QGIS processing provider for network analysis
 
 Qneat3Provider.py
 
-------------------
        begin                : 2018-01-15
        copyright            : (C) 2018 by Clemens Raffler
        email                : clemens.raffler@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

from importlib import util

from QNEAT3.Qneat3Paths import plugin_icon_path, plugin_root


def _matplotlib_available():
    """matplotlib.pyplot が import 可能か（find_spec の誤用を避ける）。"""
    return util.find_spec("matplotlib.pyplot") is not None


_matplotlib_found = _matplotlib_available()

# 全アルゴリズムは algs/__init__.py 経由（相対 import と絶対 import の混在を避ける）
from QNEAT3.algs import (
    DummyAlgorithm,
    IsoAreaAsContoursFromLayer,
    IsoAreaAsContoursFromPoint,
    IsoAreaAsInterpolationFromLayer,
    IsoAreaAsInterpolationFromPoint,
    IsoAreaAsQneatInterpolationFromPoint,
    IsoAreaAsPointcloudFromLayer,
    IsoAreaAsPointcloudFromPoint,
    IsoAreaAsPolygonsFromLayer,
    IsoAreaAsPolygonsFromPoint,
    OdMatrixFromLayersAsLines,
    OdMatrixFromLayersAsTable,
    OdMatrixFromPointsAsCsv,
    OdMatrixFromPointsAsLines,
    OdMatrixFromPointsAsTable,
    ShortestPathBetweenPoints,
)

# 導入確認: この行が無い旧版では ShortestPathBetweenPoints.ShortestPathBetweenPoints() で落ちる
PROVIDER_REGISTER_FIX = "1.0.12-addAlgorithm-Class"


class Qneat3Provider(QgsProcessingProvider):
    def __init__(self):
        super().__init__()
        self.matplotlib_found = _matplotlib_available()


    def id(self, *args, **kwargs):
        return 'qneat3'

    def name(self, *args, **kwargs):
        from QNEAT3.Qneat3Strings import provider_display_name

        return provider_display_name()

    def icon(self):
        return QIcon(plugin_icon_path())

    def svgIconPath(self):
        return plugin_icon_path()

    def loadAlgorithms(self, *args, **kwargs):
        # algs/__init__.py からクラスを import しているため X.X() ではなく X() とする
        self.addAlgorithm(ShortestPathBetweenPoints())
        self.addAlgorithm(IsoAreaAsPointcloudFromPoint())
        self.addAlgorithm(IsoAreaAsPointcloudFromLayer())
        self.addAlgorithm(IsoAreaAsInterpolationFromPoint())
        self.addAlgorithm(IsoAreaAsQneatInterpolationFromPoint())
        self.addAlgorithm(IsoAreaAsInterpolationFromLayer())
        self.addAlgorithm(OdMatrixFromPointsAsCsv())
        self.addAlgorithm(OdMatrixFromPointsAsLines())
        self.addAlgorithm(OdMatrixFromPointsAsTable())
        self.addAlgorithm(OdMatrixFromLayersAsTable())
        self.addAlgorithm(OdMatrixFromLayersAsLines())

        if _matplotlib_found:
            self.addAlgorithm(IsoAreaAsContoursFromPoint())
            self.addAlgorithm(IsoAreaAsPolygonsFromPoint())
            self.addAlgorithm(IsoAreaAsPolygonsFromLayer())
            self.addAlgorithm(IsoAreaAsContoursFromLayer())
        else:
            self.addAlgorithm(DummyAlgorithm())