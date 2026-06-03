# -*- coding: utf-8 -*-
"""
***************************************************************************
    IsoAreaAsPolygonFromLayer.py
    ---------------------
    
    Partially based on QGIS3 network analysis algorithms. 
    Copyright 2016 Alexander Bruy    
    
    Date                 : April 2018
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
__date__ = 'April 2018'
__copyright__ = '(C) 2018, Clemens Raffler'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
from collections import OrderedDict

from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QIcon

from qgis.core import (QgsWkbTypes,
                       QgsVectorLayer,
                       QgsFeatureSink,
                       QgsFields,
                       QgsField,
                       QgsProcessing,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterField,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterString,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterDefinition)

from qgis.analysis import QgsVectorLayerDirector

from QNEAT3.Qneat3Framework import Qneat3Network, Qneat3AnalysisPoint
from QNEAT3.Qneat3Utilities import getFeaturesFromQgsIterable, getListOfPoints

from QNEAT3.Qneat3Strings import UIS, LOG, ja, NEO_PREFIX, log_msg
from QNEAT3.Qneat3HelpJa import help_iso_polygons_from_layer
from QNEAT3.Qneat3ProcessingParams import add_advanced_network_params, strategy_labels, entry_cost_labels

from QNEAT3.Qneat3Paths import icon_path
from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm


class IsoAreaAsPolygonsFromLayer(QgisAlgorithm):

    INPUT = 'INPUT'
    START_POINTS = 'START_POINTS'
    ID_FIELD = 'ID_FIELD'
    MAX_DIST = "MAX_DIST"
    CELL_SIZE = "CELL_SIZE"
    INTERVAL = "INTERVAL"
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
    OUTPUT_INTERPOLATION = 'OUTPUT_INTERPOLATION'
    OUTPUT_POLYGONS = 'OUTPUT_POLYGONS'

    def icon(self):
        return QIcon(icon_path('icon_servicearea_polygon_multiple.svg'))

    def group(self):
        return ja(NEO_PREFIX + UIS.ISO_AREAS)

    def groupId(self):
        return 'isoareas'
    
    def name(self):
        return 'isoareaaspolygonsfromlayer'

    def displayName(self):
        return ja(NEO_PREFIX + '等時圏ポリゴン（レイヤ）')

    def shortHelpString(self):
        return help_iso_polygons_from_layer()

    
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
                                                              ja(UIS.NETWORK_LAYER_DESC),
                                                              [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.START_POINTS,
                                                              ja(UIS.START_POINTS),
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
        self.addParameter(QgsProcessingParameterNumber(self.INTERVAL,
                                                   ja(UIS.ISO_INTERVAL),
                                                   QgsProcessingParameterNumber.Double,
                                                   500.0, False, 0, 99999999.99))
        self.addParameter(QgsProcessingParameterNumber(self.CELL_SIZE,
                                                    ja(UIS.ISO_CELLSIZE),
                                                    QgsProcessingParameterNumber.Integer,
                                                    10, False, 1, 99999999))
        self.addParameter(QgsProcessingParameterEnum(self.STRATEGY,
                                                     ja(UIS.OPTIMIZATION_CRITERION),
                                                     self.STRATEGIES,
                                                     defaultValue=0))

        add_advanced_network_params(self, self.INPUT)

        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT_INTERPOLATION, ja(UIS.OUTPUT_INTERPOLATION)))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT_POLYGONS, ja(UIS.OUTPUT_ISO_POLYGONS), QgsProcessing.TypeVectorPolygon))
        
    def processAlgorithm(self, parameters, context, feedback):
        log_msg(feedback, LOG.ALG_START, name=self.displayName())
        network = self.parameterAsSource(parameters, self.INPUT, context) #QgsProcessingFeatureSource
        startPoints = self.parameterAsSource(parameters, self.START_POINTS, context) #QgsProcessingFeatureSource
        id_field = self.parameterAsString(parameters, self.ID_FIELD, context) #str
        interval = self.parameterAsDouble(parameters, self.INTERVAL, context)#float
        max_dist = self.parameterAsDouble(parameters, self.MAX_DIST, context)#float
        cell_size = self.parameterAsInt(parameters, self.CELL_SIZE, context)#int
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
        output_path = self.parameterAsOutputLayer(parameters, self.OUTPUT_INTERPOLATION, context) #string

        analysisCrs = network.sourceCrs()
        input_coordinates = getListOfPoints(startPoints)
        
        log_msg(feedback, LOG.ALG_BUILD_GRAPH)
        feedback.setProgress(10)
        net = Qneat3Network(network, input_coordinates, strategy, directionFieldName, forwardValue, backwardValue, bothValue, defaultDirection, analysisCrs, speedFieldName, defaultSpeed, tolerance, link_length_field, feedback)
        feedback.setProgress(40)
        
        list_apoints = [Qneat3AnalysisPoint("from", feature, id_field, net, net.list_tiedPoints[i], entry_cost_calc_method, feedback) for i, feature in enumerate(getFeaturesFromQgsIterable(startPoints))]
        
        log_msg(feedback, LOG.ISO_PC)
        iso_pointcloud = net.calcIsoPoints(list_apoints, max_dist+(max_dist*0.1))
        feedback.setProgress(50)
        
        uri = "Point?crs={}&field=vertex_id:int(254)&field=cost:double(254,7)&field=origin_point_id:string(254)&index=yes".format(analysisCrs.authid())
        
        iso_pointcloud_layer = QgsVectorLayer(uri, "iso_pointcloud_layer", "memory")
        iso_pointcloud_provider = iso_pointcloud_layer.dataProvider()
        iso_pointcloud_provider.addFeatures(iso_pointcloud, QgsFeatureSink.FastInsert)
        
        log_msg(feedback, LOG.ISO_TIN)
        net.calcIsoTinInterpolation(iso_pointcloud_layer, cell_size, output_path)
        feedback.setProgress(70)
            
        fields = QgsFields()
        fields.append(QgsField('id', QVariant.Int, '', 254, 0))
        fields.append(QgsField('cost_level', QVariant.Double, '', 20, 7))
        
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT_POLYGONS, context, fields, QgsWkbTypes.Polygon, network.sourceCrs())   
        
        log_msg(feedback, LOG.ISO_POLYGONS)
        polygon_featurelist = net.calcIsoPolygons(max_dist, interval, output_path)
        feedback.setProgress(90)
        
        sink.addFeatures(polygon_featurelist, QgsFeatureSink.FastInsert)
        log_msg(feedback, LOG.ALG_END)
        feedback.setProgress(100)
        
        results = {}
        results[self.OUTPUT_INTERPOLATION] = output_path
        results[self.OUTPUT_POLYGONS] = dest_id
        return results


