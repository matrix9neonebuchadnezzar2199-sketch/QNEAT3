# -*- coding: utf-8 -*-
"""
***************************************************************************
    DummyAlgorithm.py
    ---------------------
    Date                 : February 2018
    Copyright            : (C) 2018 by Clemens Raffler
    Email                : clemens dot raffler at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Clemens Raffler'
__date__ = 'February 2018'
__copyright__ = '(C) 2018, Clemens Raffler'

__revision__ = '$Format:%H$'

from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProcessingParameterString
from QNEAT3.Qneat3Strings import UIS, ja, NEO_PREFIX
from QNEAT3.Qneat3HelpJa import help_dummy_matplotlib
from QNEAT3.Qneat3Paths import icon_path
from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm


class DummyAlgorithm(QgisAlgorithm):

    MESSAGE1 = 'MESSAGE1'
    MESSAGE2 = 'MESSAGE2'

    def icon(self):
        return QIcon(icon_path('icon_servicearea_polygon_missing_import.svg'))

    def group(self):
        return ja(NEO_PREFIX + UIS.ISO_AREAS)

    def groupId(self):
        return 'isoareas'

    def name(self):
        return 'DummyAlgorithmIsoAreas'

    def displayName(self):
        return ja(NEO_PREFIX + '[matplotlib 未導入] 等時圏ポリゴン（導入ヘルプ）')

    def shortHelpString(self):
        return help_dummy_matplotlib()

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterString(
                self.MESSAGE1,
                ja(UIS.DUMMY_MATPLOTLIB_PARAM),
                ja(UIS.DUMMY_CMD_DEFAULT),
                False,
                False,
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.MESSAGE2,
                ja("<br><b>Linux</b><br>ターミナルで下のコマンドを実行してください。"),
                ja("pip install matplotlib"),
                False,
                False,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        feedback.pushInfo(ja(UIS.DUMMY_RESULT))
        return {self.MESSAGE1: ja(UIS.DUMMY_RESULT)}
