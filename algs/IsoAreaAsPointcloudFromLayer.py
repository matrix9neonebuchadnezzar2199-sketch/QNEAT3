# -*- coding: utf-8 -*-
"""
***************************************************************************
    IsoAreaAsPointcloudFromLayer.py
    ---------------------
    
    Partially based on QGIS3 network analysis algorithms. 
    Copyright 2016 Alexander Bruy    
    
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

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
from collections import OrderedDict

from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QIcon

from qgis.core import (QgsWkbTypes,
                       QgsFeatureSink,
                       QgsFields,
                       QgsField,
                       QgsProcessing,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterField,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterString,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterDefinition)

from qgis.analysis import QgsVectorLayerDirector

from QNEAT3.Qneat3Framework import Qneat3Network, Qneat3AnalysisPoint
from QNEAT3.Qneat3Utilities import getListOfPoints, getFeaturesFromQgsIterable, getFieldDatatype

from QNEAT3.Qneat3Strings import UIS, LOG, ja, NEO_PREFIX, log_msg
from QNEAT3.Qneat3HelpJa import help_iso_pointcloud_from_layer
from QNEAT3.Qneat3ProcessingParams import add_advanced_network_params, strategy_labels, entry_cost_labels

from QNEAT3.Qneat3Paths import icon_path
from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm


class IsoAreaAsPointcloudFromLayer(QgisAlgorithm):

    INPUT = 'INPUT'
    START_POINTS = 'START_POINTS'
    ID_FIELD = 'ID_FIELD'
    MAX_DIST = "MAX_DIST"
    STRATEGY = 'STRATEGY'
    ENTRY_COST_CALCULATION_METHOD = 'ENTRY_COST_CALCULATION_METHOD'
    DIRECTION_FIELD = 'DIRECTION_FIELD'
    VALUE_FORWARD = 'VALUE_FORWARD'
    VALUE_BACKWARD = 'VALUE_BACKWARD'
    VALUE_BOTH = 'VALUE_BOTH'
    DEFAULT_DIRECTION = 'DEFAULT_DIRECTION'
    SPEED_FIELD = 'SPEED_FIELD'
    DEFAULT_SPEED = 'DEFAULT_SPEED'
    TOLERANCE = 'TOLERANCE'
    LINK_LENGTH_FIELD = 'LINK_LENGTH_FIELD'
    OUTPUT = 'OUTPUT'

    def icon(self):
        return QIcon(icon_path('icon_servicearea_points_multiple.svg'))

    def group(self):
        return ja(NEO_PREFIX + UIS.ISO_AREAS)

    def groupId(self):
        return 'isoareas'
    
    def name(self):
        return 'isoareaaspointcloudfromlayer'

    def displayName(self):
        return ja(NEO_PREFIX + '等時点クラウド（レイヤ）')

    def shortHelpString(self):
        return help_iso_pointcloud_from_layer()

    
    def msg(self, var):
        return "Type:"+str(type(var))+" repr: "+var.__str__()

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        self.DIRECTIONS = OrderedDict([
            (ja(UIS.DIR_FORWARD), QgsVectorLayerDirector.DirectionForward),
            (ja(UIS.DIR_BACKWARD), QgsVectorLayerDirector.DirectionBackward),
            (ja(UIS.DIR_BOTH), QgsVectorLayerDirector.DirectionBoth)])

        self.STRATEGIES = strategy_labels()

        self.ENTRY_COST_CALCULATION_METHODS = entry_cost_labels(include_ellipsoidal=True)
    
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT,
                                                              ja(UIS.NETWORK_LAYER),
                                                              [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.START_POINTS,
                                                              ja(UIS.STARTPOINT_LAYER),
                                                              [QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterField(self.ID_FIELD,
                                                       ja(UIS.UNIQUE_POINT_ID),
                                                       None,
                                                       self.START_POINTS,
                                                       optional=False))
        self.addParameter(QgsProcessingParameterNumber(self.MAX_DIST,
                                                   ja(UIS.ISO_SIZE),
                                                   QgsProcessingParameterNumber.Double,
                                                   2500.0, False, 0, 99999999.99))
        self.addParameter(QgsProcessingParameterEnum(self.STRATEGY,
                                                     ja(UIS.OPTIMIZATION_CRITERION),
                                                     self.STRATEGIES,
                                                     defaultValue=0))

        add_advanced_network_params(self, self.INPUT)
        
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT,
                                                            ja(UIS.OUTPUT_ISO_POINTCLOUD),
                                                            QgsProcessing.TypeVectorPoint))

    def processAlgorithm(self, parameters, context, feedback):
        log_msg(feedback, LOG.ALG_START, name=self.displayName())
        network = self.parameterAsSource(parameters, self.INPUT, context) #QgsProcessingFeatureSource
        startPoints = self.parameterAsSource(parameters, self.START_POINTS, context) #QgsProcessingFeatureSource
        id_field = self.parameterAsString(parameters, self.ID_FIELD, context) #str
        max_dist = self.parameterAsDouble(parameters, self.MAX_DIST, context)#float
        strategy = self.parameterAsEnum(parameters, self.STRATEGY, context) #int

        entry_cost_calc_method = self.parameterAsEnum(parameters, self.ENTRY_COST_CALCULATION_METHOD, context) #int
        directionFieldName = self.parameterAsString(parameters, self.DIRECTION_FIELD, context) #str (empty if no field given)
        forwardValue = self.parameterAsString(parameters, self.VALUE_FORWARD, context) #str
        backwardValue = self.parameterAsString(parameters, self.VALUE_BACKWARD, context) #str
        bothValue = self.parameterAsString(parameters, self.VALUE_BOTH, context) #str
        defaultDirection = self.parameterAsEnum(parameters, self.DEFAULT_DIRECTION, context) #int
        speedFieldName = self.parameterAsString(parameters, self.SPEED_FIELD, context) #str
        defaultSpeed = self.parameterAsDouble(parameters, self.DEFAULT_SPEED, context) #float
        tolerance = self.parameterAsDouble(parameters, self.TOLERANCE, context)
        link_length_field = self.parameterAsString(parameters, self.LINK_LENGTH_FIELD, context)

        analysisCrs = network.sourceCrs()
        input_coordinates = getListOfPoints(startPoints)
        
        log_msg(feedback, LOG.ALG_BUILD_GRAPH)
        feedback.setProgress(10)  
        net = Qneat3Network(network, input_coordinates, strategy, directionFieldName, forwardValue, backwardValue, bothValue, defaultDirection, analysisCrs, speedFieldName, defaultSpeed, tolerance, link_length_field, feedback)
        feedback.setProgress(40)
        
        list_apoints = [Qneat3AnalysisPoint("from", feature, id_field, net, net.list_tiedPoints[i], entry_cost_calc_method, feedback) for i, feature in enumerate(getFeaturesFromQgsIterable(startPoints))]
        
        fields = QgsFields()
        fields.append(QgsField('vertex_id', QVariant.Int, '', 254, 0))
        fields.append(QgsField('cost', QVariant.Double, '', 254, 7))
        fields.append(QgsField('origin_point_id', getFieldDatatype(startPoints, id_field)))
        
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, fields, QgsWkbTypes.Point, network.sourceCrs())
        
        log_msg(feedback, LOG.ISO_PC)
        iso_pointcloud = net.calcIsoPoints(list_apoints, max_dist)
        feedback.setProgress(90)
        
        sink.addFeatures(iso_pointcloud, QgsFeatureSink.FastInsert)
        
        log_msg(feedback, LOG.ALG_END)
        feedback.setProgress(100)          
        
        results = {}
        results[self.OUTPUT] = dest_id
        return results

