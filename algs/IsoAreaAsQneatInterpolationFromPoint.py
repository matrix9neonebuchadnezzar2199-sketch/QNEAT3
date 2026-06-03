# -*- coding: utf-8 -*-
"""
***************************************************************************
    IsoAreaAsQneatInterpolationPoint.py
    ---------------------
    
    Partially based on QGIS3 network analysis algorithms. 
    Copyright 2016 Alexander Bruy    
    
    Date                 : July 2018
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

import osgeo.gdal as gdal
from osgeo import osr

from numpy import array, meshgrid, linspace, zeros

from qgis.PyQt.QtGui import QIcon

from qgis.core import (QgsFeatureSink,
                       QgsPointXY,
                       QgsVectorLayer,
                       QgsSpatialIndex,
                       QgsFeatureRequest,
                       QgsGeometry,
                       QgsProcessing,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterPoint,
                       QgsProcessingParameterField,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterString,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterDefinition)

from qgis.analysis import QgsVectorLayerDirector

from QNEAT3.Qneat3Framework import Qneat3Network, Qneat3AnalysisPoint
from QNEAT3.Qneat3Utilities import getFeatureFromPointParameter, getFeaturesFromQgsIterable

from QNEAT3.Qneat3Strings import UIS, LOG, ja, NEO_PREFIX, log_msg
from QNEAT3.Qneat3HelpJa import help_iso_qneat_interpolation_from_point
from QNEAT3.Qneat3ProcessingParams import add_advanced_network_params, strategy_labels, entry_cost_labels

from QNEAT3.Qneat3Paths import icon_path
from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm


class IsoAreaAsQneatInterpolationFromPoint(QgisAlgorithm):

    INPUT = 'INPUT'
    START_POINT = 'START_POINT'
    MAX_DIST = "MAX_DIST"
    CELL_SIZE = "CELL_SIZE"
    STRATEGY = 'STRATEGY'
    METHOD = 'METHOD'
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
        return QIcon(icon_path('icon_servicearea_points.svg'))

    def group(self):
        return ja(NEO_PREFIX + UIS.ISO_AREAS)

    def groupId(self):
        return 'isoareas'
    
    def name(self):
        return 'isoareaasqneatinterpolationfrompoint'

    def displayName(self):
        return ja(NEO_PREFIX + '等時圏 QNEAT 補間（単一点）')

    def shortHelpString(self):
        return help_iso_qneat_interpolation_from_point()

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
        
        self.METHODS = [ja(UIS.INTERP_TIN), ja(UIS.INTERP_QNEAT)]

        self.ENTRY_COST_CALCULATION_METHODS = entry_cost_labels(include_ellipsoidal=True)
            

        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT,
                                                              ja(UIS.NETWORK_LAYER),
                                                              [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterPoint(self.START_POINT,
                                                      ja(UIS.START_POINT)))
        self.addParameter(QgsProcessingParameterNumber(self.MAX_DIST,
                                                   ja(UIS.ISO_SIZE),
                                                   QgsProcessingParameterNumber.Double,
                                                   2500.0, False, 0, 99999999.99))
        self.addParameter(QgsProcessingParameterNumber(self.CELL_SIZE,
                                                    ja(UIS.ISO_CELLSIZE),
                                                    QgsProcessingParameterNumber.Integer,
                                                    10, False, 1, 99999999))
        self.addParameter(QgsProcessingParameterEnum(self.STRATEGY,
                                                     ja(UIS.OPTIMIZATION_CRITERION),
                                                     self.STRATEGIES,
                                                     defaultValue=0))
        self.addParameter(QgsProcessingParameterEnum(self.METHOD,
                                                     ja(UIS.INTERP_METHOD),
                                                     self.METHODS,
                                                     defaultValue=1))

        add_advanced_network_params(self, self.INPUT)
        
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT, ja(UIS.OUTPUT_INTERPOLATION)))

    def processAlgorithm(self, parameters, context, feedback):
        log_msg(feedback, LOG.ALG_START, name=self.displayName())
        network = self.parameterAsVectorLayer(parameters, self.INPUT, context) #QgsVectorLayer
        startPoint = self.parameterAsPoint(parameters, self.START_POINT, context, network.sourceCrs()) #QgsPointXY
        max_dist = self.parameterAsDouble(parameters, self.MAX_DIST, context)#float
        cell_size = self.parameterAsInt(parameters, self.CELL_SIZE, context)#int
        strategy = self.parameterAsEnum(parameters, self.STRATEGY, context) #int
        interpolation_method = self.parameterAsEnum(parameters, self.METHOD, context)#int

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
        output_path = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)

        analysisCrs = network.sourceCrs()
        input_coordinates = [startPoint]
        input_point = getFeatureFromPointParameter(startPoint)
        
        log_msg(feedback, LOG.ALG_BUILD_GRAPH)
        feedback.setProgress(10)  
        net = Qneat3Network(network, input_coordinates, strategy, directionFieldName, forwardValue, backwardValue, bothValue, defaultDirection, analysisCrs, speedFieldName, defaultSpeed, tolerance, link_length_field, feedback)
        feedback.setProgress(40)
        
        analysis_point = Qneat3AnalysisPoint("point", input_point, "point_id", net, net.list_tiedPoints[0], entry_cost_calc_method, feedback)
        
        log_msg(feedback, LOG.ISO_PC)
        iso_pointcloud = net.calcIsoPoints([analysis_point], max_dist)
        feedback.setProgress(70)
        
        uri = "Point?crs={}&field=vertex_id:int(254)&field=cost:double(254,7)&field=origin_point_id:string(254)&index=yes".format(analysisCrs.authid())
        
        iso_pointcloud_layer = QgsVectorLayer(uri, "iso_pointcloud_layer", "memory")
        iso_pointcloud_provider = iso_pointcloud_layer.dataProvider()
        iso_pointcloud_provider.addFeatures(iso_pointcloud, QgsFeatureSink.FastInsert)
        
        log_msg(feedback, LOG.ISO_TIN)
        if interpolation_method == 0:
            log_msg(feedback, LOG.ISO_TIN)
            net.calcIsoTinInterpolation(iso_pointcloud_layer, cell_size, output_path)
            feedback.setProgress(99)
        else:


            #prepare numpy coordinate grids
            NoData_value = -9999
            raster_rectangle = iso_pointcloud_layer.extent()
            
            #implement spatial index for lines (closest line, etc...)
            spt_idx = QgsSpatialIndex(iso_pointcloud_layer.getFeatures(QgsFeatureRequest()), feedback)
            
            #top left point
            xmin = raster_rectangle.xMinimum()
            ymin = raster_rectangle.yMinimum()
            xmax = raster_rectangle.xMaximum()
            ymax = raster_rectangle.yMaximum()
            
            cols = int((xmax - xmin) / cell_size)
            rows = int((ymax - ymin) / cell_size)
            
            output_interpolation_raster = gdal.GetDriverByName('GTiff').Create(output_path, cols, rows, 1, gdal.GDT_Float64 )
            output_interpolation_raster.SetGeoTransform((xmin, cell_size, 0, ymax, 0, -cell_size))
            
            band = output_interpolation_raster.GetRasterBand(1)
            band.SetNoDataValue(NoData_value)
            
            #initialize zero array with 2 dimensions (according to rows and cols)
            raster_routingcost_data = zeros(shape=(rows, cols))
            
            #compute raster cell MIDpoints
            x_pos = linspace(xmin+(cell_size/2), xmax -(cell_size/2), raster_routingcost_data.shape[1])
            y_pos = linspace(ymax-(cell_size/2), ymin + (cell_size/2), raster_routingcost_data.shape[0])
            x_grid, y_grid = meshgrid(x_pos, y_pos) 
            
            log_msg(feedback, LOG.INTERP_BEGIN)
            total_work = rows * cols
            counter = 0

            log_msg(feedback, LOG.INTERP_WORKLOAD, n=total_work)
            feedback.setProgress(0)
            for i in range(rows):
                for j in range(cols):
                    current_pixel_midpoint = QgsPointXY(x_grid[i,j],y_grid[i,j])
    
                    nearest_vertex_fid = spt_idx.nearestNeighbor(current_pixel_midpoint, 1)[0]
    
                    nearest_feature = iso_pointcloud_layer.getFeature(nearest_vertex_fid)
    
                    nearest_vertex = net.network.vertex(nearest_feature['vertex_id'])
    
                    #yields a list of all incoming and outgoing edges    
                    edges = nearest_vertex.incomingEdges() + nearest_vertex.outgoingEdges() 
                    
                    vertex_found = False
                    nearest_counter = 2
                    while vertex_found == False:
                        #find the second nearest vertex (eg, the vertex with least cost of all edges incoming to the first nearest vertex)
                        second_nearest_feature_fid = spt_idx.nearestNeighbor(current_pixel_midpoint, nearest_counter)[nearest_counter-1] 
                        second_nearest_feature = iso_pointcloud_layer.getFeature(second_nearest_feature_fid)
                        second_nearest_vertex_id = second_nearest_feature['vertex_id']
    
                        for edge_id in edges:
                            from_vertex_id = net.network.edge(edge_id).fromVertex()
                            to_vertex_id = net.network.edge(edge_id).toVertex()
    
                            if second_nearest_vertex_id == from_vertex_id: 
                                vertex_found = True
                                vertex_type = "from_vertex"
                                from_point = second_nearest_feature.geometry().asPoint()
                                from_vertex_cost = second_nearest_feature['cost']
                                
                            if second_nearest_vertex_id == to_vertex_id:
                                vertex_found = True
                                vertex_type = "to_vertex"
                                to_point = second_nearest_feature.geometry().asPoint()
                                to_vertex_cost = second_nearest_feature['cost']
                                
    
                        nearest_counter = nearest_counter + 1
                        """
                        if nearest_counter == 5:
                            vertex_found = True
                            vertex_type = "end_vertex"
                        """
    
                    if vertex_type == "from_vertex":
                        nearest_edge_geometry = QgsGeometry().fromPolylineXY([from_point, nearest_vertex.point()])
                        res = nearest_edge_geometry.closestSegmentWithContext(current_pixel_midpoint)
                        segment_point = res[1] #[0: distance, 1: point, 2: left_of, 3: epsilon for snapping]
                        dist_to_segment = segment_point.distance(current_pixel_midpoint)
                        dist_edge = from_point.distance(segment_point)
                        #feedback.pushInfo("dist_to_segment = {}".format(dist_to_segment))
                        #feedback.pushInfo("dist_on_edge = {}".format(dist_edge))
                        #feedback.pushInfo("cost = {}".format(from_vertex_cost))
                        pixel_cost = from_vertex_cost + dist_edge + dist_to_segment
                        raster_routingcost_data[i,j] = pixel_cost
                    elif vertex_type == "to_vertex":
                        nearest_edge_geometry = QgsGeometry().fromPolylineXY([nearest_vertex.point(), to_point])
                        res = nearest_edge_geometry.closestSegmentWithContext(current_pixel_midpoint)
                        segment_point = res[1] #[0: distance, 1: point, 2: left_of, 3: epsilon for snapping]
                        dist_to_segment = segment_point.distance(current_pixel_midpoint)
                        dist_edge = to_point.distance(segment_point)
                        #feedback.pushInfo("dist_to_segment = {}".format(dist_to_segment))
                        #feedback.pushInfo("dist_on_edge = {}".format(dist_edge))
                        #feedback.pushInfo("cost = {}".format(from_vertex_cost))
                        pixel_cost = to_vertex_cost + dist_edge + dist_to_segment
                        raster_routingcost_data[i,j] = pixel_cost
                    else:
                        pixel_cost = -99999#nearest_feature['cost'] + (nearest_vertex.point().distance(current_pixel_midpoint))
    
    
                    """
                    nearest_feature_pointxy = nearest_feature.geometry().asPoint()
                    nearest_feature_cost = nearest_feature['cost']
                    
                    dist_to_vertex = current_pixel_midpoint.distance(nearest_feature_pointxy)
                    #implement time cost
                    pixel_cost = dist_to_vertex + nearest_feature_cost
                    
                    raster_data[i,j] = pixel_cost
                    """
                    counter = counter+1
                    if counter%1000 == 0:
                        log_msg(feedback, LOG.INTERP_PROGRESS, n=counter)
                    feedback.setProgress((counter/total_work)*100)
    
    
            band.WriteArray(raster_routingcost_data)
            outRasterSRS = osr.SpatialReference()
            outRasterSRS.ImportFromWkt(net.AnalysisCrs.toWkt())
            output_interpolation_raster.SetProjection(outRasterSRS.ExportToWkt())
            band.FlushCache()

        
        log_msg(feedback, LOG.ALG_END)
        feedback.setProgress(100)           
        
        results = {}
        results[self.OUTPUT] = output_path
        return results