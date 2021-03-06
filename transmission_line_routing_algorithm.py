# -*- coding: utf-8 -*-

"""
/***************************************************************************
 TransmissionLineRouting
                                 A QGIS plugin
 This software will be able to design the best route of one transmission line on a map.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-02-08
        copyright            : (C) 2020 by Ander Gutiérrez
        email                : angutiu@unirioja.es
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

__author__ = 'Ander Gutiérrez'
__date__ = '2020-02-08'
__copyright__ = '(C) 2020 by Ander Gutiérrez'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qgis.core import *

import processing
from .LineVectorLayer import *

#********************************************************************************************
#********************************************************************************************
class TransmissionLineRoutingAlgorithm(QgsProcessingAlgorithm):
                                                    #Definición de los parámetros Entradas y Salida para el Plugin
    IN_RASTER = 'IN_RASTER'                             #Entrada de la Capa Ráster   
    IN_ORIG_POINT = 'IN_ORIG_POINT'           #Entrada de la Capa Vectorial con el Punto Origen
    IN_MID_POINT = 'IN_MID_POINT'                       #Entrada de la Capa Vectorial con los Puntos Intermedios
    IN_END_POINT = 'IN_END_POINT'                       #Entrada de la Capa Vectorial con el Punto Final
    IN_EXIST_LINE = 'IN_EXIST_LINE'                     #Entrada de una Capa Vectorial existente de una o más líneas
    IN_LINE_INFO = 'IN_LINE_INFO'                       #Entrada con información la línea que se pretende trazar
    IN_COST_CONDUCTOR = 'IN_COST_CONDUCTOR'             #Entrada de el valor del coste del cable conductor
    IN_VOLTLINE = 'IN_VOLTLINE'                         #Entrada de el valor de la tensión que circulará por la línea        
    IN_SIST_2CIR = 'IN_SIST_2CIR'                       #Entrada para saber si será un sistema de doble circuito
    IN_GND = 'IN_GND'                                   #Entrada para saber si llevará conductor de tierra
    IN_GND_INFO = 'IN_GND_INFO'                         #Entrada con información del cable conductor de tierra
    IN_LINE_ID = 'IN_LINE_ID'                           #Entrada de la identificación de la línea
    OUT_LINE = 'OUT_LINE'                               #Salida con la Capa Vectorial de la línea eléctrica trazada

    def initAlgorithm(self, config):                
                                                    #Declaración de las Entradas y Salidas en el Plugin
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.IN_RASTER,
                self.tr('Capa ráster'),
                None,
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.IN_ORIG_POINT,
                self.tr('Apoyo Origen'),
                [QgsProcessing.TypeVectorPoint],
                None,
            )
        )
        
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.IN_MID_POINT,
                self.tr('Apoyo(s) intermedio(s)'),
                [QgsProcessing.TypeVectorPoint],
                None,
                True
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.IN_END_POINT,
                self.tr('Apoyo Final'),
                [QgsProcessing.TypeVectorPoint],
                None,
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.IN_EXIST_LINE,
                self.tr('Proyecto existente de línea(s) eléctrica(s)'),
                [QgsProcessing.TypeVectorLine],
                None,
                True
            )
        )
        
        self.addParameter(
            QgsProcessingParameterString(
                self.IN_LINE_INFO,
                self.tr('Características del cable de la línea'),
                None,
                False,
                True
            )
        )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.IN_COST_CONDUCTOR,
                self.tr('Precio unitario del conductor (€/km)'),
                QgsProcessingParameterNumber.Integer,
                None,
            )
        )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.IN_VOLTLINE,
                self.tr('Tensión de la línea (kV)'),
                QgsProcessingParameterNumber.Integer,
                None,
            )
        )
        
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.IN_SIST_2CIR,
                self.tr('Indique si el sistema es de doble circuito')
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.IN_GND,
                self.tr('Indique si también habrá cable de tierra')
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.IN_GND_INFO,
                self.tr('Características del cable de tierra'),
                None,
                False,
                True
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.IN_LINE_ID,
                self.tr('Identificación de la línea eléctrica'),
                None,
                False,
            )
        )
            
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUT_LINE,
                self.tr('Recorrido de la línea eléctrica')
            )
        )
#********************************************************************************************
#********************************************************************************************
    def processAlgorithm(self, parameters, context, feedback):
                                                    #Relación de cada Entrada y Salida del Plugin 
                                                    # a una Variable para el software
        raster = self.parameterAsRasterLayer(   # Variable Raster
            parameters,
            self.IN_RASTER,
            context)                                        

        orig_point = self.parameterAsSource(    # Variable Vectorial, Punto de Origen
            parameters,
            self.IN_ORIG_POINT,
            context)

        mid_point = self.parameterAsSource(     # Variable Vectorial, Punto(s) Intermedio(s)
            parameters,
            self.IN_MID_POINT,
            context)

        end_point = self.parameterAsSource(     # Variable Vectorial, Punto Final
            parameters,
            self.IN_END_POINT,
            context)

        exist_line = self.parameterAsSource(    # Variable para un archivo existente
            parameters,
            self.IN_EXIST_LINE,
            context)
        
        info_line = self.parameterAsString(     # Variable que almacenerá la información de la línea
            parameters,
            self.IN_LINE_INFO,
            context)
        
        cost_conductor = self.parameterAsInt(   # Variable que almacenerá el coste del conductor
            parameters,
            self.IN_COST_CONDUCTOR,
            context)
        
        volt_line = self.parameterAsInt(        # Variable que almacenerá la tensión
            parameters,
            self.IN_VOLTLINE,
            context)
        
        sist_doble_circ = self.parameterAsBool( # Variable que indicará si el sistema es DC o no
            parameters,
            self.IN_SIST_2CIR,
            context)

        ground_line = self.parameterAsBool(     # Variable que indicará si habrá conductor de tierra o no
            parameters,
            self.IN_GND,
            context)

        info_ground = self.parameterAsString(   # Variable  que almacenerá información del conductor tierra
            parameters,
            self.IN_GND_INFO,
            context)

        Id_Line = self.parameterAsString(       # Variable para el identificación de la línea
            parameters,
            self.IN_LINE_ID,
            context)
                                                      # Mensajes de Error por si el usuario comete algun fallo,
                                                      # que no se ejecute                                      
        if raster is None:                                                  
            raise QgsProcessingException(self.invalidSourceError(parameters, self.IN_RASTER))
        if ((orig_point is None) or (len(list(orig_point.getFeatures())) != 1)):
            raise QgsProcessingException(self.invalidSourceError(parameters, self.IN_ORIG_POINT))
        if ((end_point is None) or (len(list(end_point.getFeatures())) != 1)):
            raise QgsProcessingException(self.invalidSourceError(parameters, self.IN_END_POINT))
        if mid_point is None:
            feedback.pushInfo(self.tr("No se ha especificiado ningún apoyo intermedio por el que pasar el trazado."))
            boolMid_Points = False
        elif (len(list(mid_point.getFeatures())) > 0):
            boolMid_Points = True
            if raster.crs() != mid_point.sourceCrs():
                raise QgsProcessingException(self.tr("Error! El CRS de la capa vectorial de Apoyos intermedios es distinto a la del ráster."))
        else:
            raise QgsProcessingException(self.tr("Error! La capa vectorial de Apoyos intermedios no tiene ningún punto."))
        if cost_conductor is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.IN_COST_CONDUCTOR))
        if volt_line is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.IN_VOLTLINE))
        if ((volt_line < 0) and (volt_line > 400)):
            raise QgsProcessingException(self.tr("Error! Tensión de línea incorrecta, debe estar entre 0 y 400 kV."))
        
        if raster.rasterType() not in [raster.Multiband, raster.GrayOrUndefined]:
            raise QgsProcessingException(self.tr("Error! El raster no es numérico."))

        if raster.crs() != orig_point.sourceCrs() or orig_point.sourceCrs() != end_point.sourceCrs():
            raise QgsProcessingException(self.tr("Error! La capa vectorial de Apoyo Origen o Final no tiene el mismo CRS que el ráster."))

                                                                    # Mensajes de Incio que se mostrará por pantalla

        feedback.pushInfo(self.tr(""))
        feedback.pushInfo(self.tr("Se está procesando los datos de entrada."))
        feedback.pushInfo(self.tr(""))
        feedback.pushInfo(self.tr("El coste del cable conductor es de %d €/km")%(cost_conductor))
        feedback.pushInfo(self.tr("La tensión que tendrá el cable conductor es de %d kV")%(volt_line))
        if sist_doble_circ == True:
            feedback.pushInfo(self.tr("Circuito de Doble Circuito"))
        feedback.pushInfo(self.tr(""))
#*****************************************************************************************************************************        
#*****************************************************************************************************************************
                                                                                # A continuación se obtendrá las coordenadas de todos ...
                                                                                # .. los puntos a trabajar, y se convertirán en Filas y Columnas

        orig_point_features = list(orig_point.getFeatures())                    # Se pasa a una variable el punto del Apoyo Origen

        orig_point_feature = orig_point_features[0]                             # Se queda con el primer punto, en caso de haber más por error
        if orig_point_feature.hasGeometry:                                      # Si tiene geometría, y a continuación..
            orig_point_geom = orig_point_feature.geometry()
            if orig_point_geom.wkbType() == QgsWkbTypes.Point:                  # .. y es tipo Punto
                PointXY = orig_point_geom.asPoint()                             # Guardamos las coordenadas X e Y del Punto
                CoordX_Start = PointXY[0]
                CoordY_Start = PointXY[1]                                       # En la siguiente línea se transformará las coordenadas en
                                                                                # Filas y Columnas del Ráster
                Start_RowCol_List = LineVectorLayer.ConvertPoint2RowCol(CoordX_Start, CoordY_Start, raster)         #[Fil,Col]
                Start_RowCol = Start_RowCol_List[0]                             # La variable es un tuple            
            else:
                raise QgsProcessingException(self.tr("Error! La geometría de la capa vectorial del Apoyo origen debe ser Point."))                    
        else:                                                                   # Mensajes de Error
            raise QgsProcessingException(self.tr("Error! La capa vectorial del Apoyo origen no tiene ninguna geometría."))

        List_RowCols = []                                                       # Lista que almacenará los puntos en orden
        List_Coords = []                                                        # Lista que almacenará las coordenadas en orden
        List_RowCols.append(Start_RowCol)                                       # Se almacena la fila y columana Origen
        List_Coords.append((CoordX_Start, CoordY_Start))                        # Se almacena las coordenadas Origen

       
        if boolMid_Points == True:              # Si hay Apoyos intermedios se procede (Solo entra si se introdujo puntos intermedios)                                                                           
            mid_point_features = list(mid_point.getFeatures())                  # Y se sigue el mismo proceso que con el punto Origen
            for Ite in range(len(mid_point_features)):
                mid_point_feature = mid_point_features[Ite]
                if mid_point_feature.hasGeometry:
                    mid_point_geom = mid_point_feature.geometry()
                    if mid_point_geom.wkbType() == QgsWkbTypes.Point:
                        PointXY = mid_point_geom.asPoint()
                        CoordX_Mid = PointXY[0]
                        CoordY_Mid = PointXY[1]
                        Mid_RowCol_List = LineVectorLayer.ConvertPoint2RowCol(CoordX_Mid, CoordY_Mid, raster)   #[Fil,Col]
                        List_RowCols.append(Mid_RowCol_List[0])                     # Se queda con las Filas y Columna y Coordenadas..
                        List_Coords.append((CoordX_Mid, CoordY_Mid))                # .. de un punto de la capa Intermedia
                    else:
                       raise QgsProcessingException(self.tr("Error! La geometría de la capa vectorial de Apoyo(s) intermedio(s) debe ser Point."))                    
                else:                                                           # Mensajes de Error
                    raise QgsProcessingException(self.tr("Error! La capa vectorial de Apoyo(s) intermedio(s) no tiene ninguna geometría."))


        end_point_features = list(end_point.getFeatures())                      # Se procede igual, con el Punto final

        end_point_feature = end_point_features[0]
        if end_point_feature.hasGeometry:
            end_point_geom = end_point_feature.geometry()
            if end_point_geom.wkbType() == QgsWkbTypes.Point:
                PointXY = end_point_geom.asPoint()
                CoordX_End = PointXY[0]
                CoordY_End = PointXY[1]
                End_RowCol_List = LineVectorLayer.ConvertPoint2RowCol(CoordX_End, CoordY_End, raster)       #[Fil,Col]
                End_RowCol = End_RowCol_List[0]
            else:
                raise QgsProcessingException(self.tr("Error! La geometría de la capa vectorial del Apoyo final debe ser Point."))                    
        else:                                                                   # Mensajes de Error
            raise QgsProcessingException(self.tr("Error! La capa vectorial del Apoyo final no tiene ninguna geometría."))

           
        List_RowCols.append(End_RowCol)                             # Se almacena la fila y columana Final
        List_Coords.append((CoordX_End, CoordY_End))                # Se almacena las coordenadas del Final
#*****************************************************************************************************************************        
#*****************************************************************************************************************************                               
        if feedback.isCanceled():                                   # Se para la ejecución si el proceso se cancela
            raise QgsProcessingException(self.tr("Proceso cancelado."))
                            
                                                                        #Se queda el numero de bloques del raster  
        BlocksRaster = LineVectorLayer.GetBlocksRaster(raster)                           
        feedback.pushInfo(self.tr("Las dimensiones del raster son: %d Filas x %d Columnas") % (BlocksRaster.height(), BlocksRaster.width()))
        
        feedback.pushInfo(self.tr("Construyendo la matriz con los valores de la capa raster."))     # En la siguiente línea se construye la Matriz
        MatrizRaster, ValueNegative = LineVectorLayer.ConvertBlock2Matriz(BlocksRaster, feedback)                    # Matriz con valores del raster y   

        if ((MatrizRaster == None) and (ValueNegative == None)):            # Si ambos tienen None, es que el programa fue cancelado
            raise QgsProcessingException(self.tr("Proceso cancelado."))     # Y se para el programa

        if ValueNegative:                                                                           #  si contiene valores negativos.. Error
            raise QgsProcessingException(self.tr("Error! Existe al menos un bloque con valor negativo. No se puede ejecutar correctamente."))
        feedback.pushInfo(self.tr(" "))
        feedback.pushInfo(self.tr("Matriz construida."))
        feedback.pushInfo(self.tr(" "))
#*****************************************************************************************************************************        
#*****************************************************************************************************************************      
        feedback.pushInfo(self.tr("Comienza a trazarse el recorrido de la línea eléctrica."))
        MinPath_Points = []
        for Iter in range(len(List_RowCols) - 1):                   # En este bucle se crea el recorrido mínimo ...
            From = Iter
            To = Iter + 1                                               #Cada Iteración es un Tramo de la línea
                                                                    # ... primero con Filas y Columnas del Ráster, ...
                                                                    
            MinPath = LineVectorLayer.LeastPath(self, MatrizRaster, List_RowCols[From], List_RowCols[To], End_RowCol, feedback)

            if MinPath is None:                                     # Mensajes de Error por si no se trazase bien el recorrido
                if feedback.isCanceled():
                    raise QgsProcessingException(self.tr("Error! Proceso cancelado."))
                else:
                    raise QgsProcessingException(self.tr(" Error! El punto número %d es inalcanzable desde el punto número %d.") % (To, From))
                
                                                                    # ... luego ese camino lo convierte en coordenadas
                                                                    
            MinPath_Points_Prev = LineVectorLayer.ConvertPath2Points(raster, MinPath, QgsPointXY((List_Coords[From])[0],(List_Coords[From])[1]), QgsPointXY((List_Coords[To])[0],(List_Coords[To])[1])) #Guarda el camino de la linea pero en coordenadas

            MinPath_Points.extend(MinPath_Points_Prev)              # Aquí se guarda en la Lista el recorrido del tramo trazado, en Coordenadas
            if Iter == len(List_RowCols) - 2:
                break

            MinPath_Points.pop(-1)
            feedback.pushInfo(self.tr("Tramo hasta el punto intermedio %d completado con éxito.")% (To))


        feedback.pushInfo(self.tr("Recorrido completado. Guardando línea..."))          # Al llegar aquí, se habrá salido del bucle..
                                                                                        # .. lo que quiere decir que el recorrido está trazado..
                                                                                        # .. al completo
#*****************************************************************************************************************************        
#*****************************************************************************************************************************

                                                                # Una vez se tiene en una lista el recorrido mínimo con
                                                                # coordenadas en el ráster, se procede a crear la línea en
                                                                # una capa vectorial, y sus características.

                                                                # En QGIS..
                                                                # ..Cada Feature corresponde a un elemento geométrico (Punto, línea o polígono)
                                                                # ..Cada Field es el nombre de una característica o campo de un Feature
                                                                # ..Cada Atributo es el contenido de un Field
                                                                                                                                                        
        SinkFieldsLine = QgsFields()                            # Se instancia un Field                                                                    
        Line = QgsFeature(SinkFieldsLine)                       # Se atribuye dicho Field a un Feature que llamo Line
        PolyLine = QgsGeometry.fromPolyline(MinPath_Points)     # A esta variable le guardo la linea formada por lo puntos del recorrido
        Line.setGeometry(PolyLine)                              # A la Feature Line, le modifico la geometría añadiéndole la línea
                                                                # Hablo de línea por la línea eléctrica, pero geométricamente se trata de una polilínea
        
                                                                                    #Aquí la línea ha sido creada aunque no dibujada
        
                                                                # Se va a proceder a calcular la longitud en metros aproximadamente real de la línea
        Line_geom = Line.geometry()                             # Se guarda la geometría         
        Var_DistArea = QgsDistanceArea()                        # Se instancia una variable con los métodos de Áreas y Distancias
        LengthLine = Var_DistArea.measureLength(Line_geom)      # Se obtiene la medida del longitud de la geometría, este caso la línea, en metros
        
        CostLine = (LengthLine / 1000) * cost_conductor         #Coste del recorrido aproximado en € / km


                                                                # Ahora se va a calcular todos los Fields que tendrá la línea vectorial diseñada
        SinkFieldsLine = Line.fields()                                                  
        SinkFieldsLine.append(QgsField("Identificador ", QVariant.String, "str", 255, 0, " Identificación de la línea eléctrica"))
        SinkFieldsLine.append(QgsField("Características del conductor ",QVariant.String, "str", 500, 0,"(Material del cable, sección, ..."))
        SinkFieldsLine.append(QgsField("Tensión de línea (kV) ",QVariant.Double, "double", 6, 3, "Tensión de la línea en kilovoltios"))
        SinkFieldsLine.append(QgsField("Sistema doble circuito ",QVariant.String, "text", 3))
        SinkFieldsLine.append(QgsField("Precio unitario (€/km) ",QVariant.Double, "double", 18, 3, "Precio en euros por el cada kilómetro del conductor"))
        SinkFieldsLine.append(QgsField("Distancia aproximada (m) ",QVariant.Double, "double", 27, 6, "Distancia aproximada de la línea eléctrica en metros"))
        SinkFieldsLine.append(QgsField("Coste por fase (€) ",QVariant.Double, "double", 18, 3, "Coste aproximado del conductor de una fase"))
        SinkFieldsLine.append(QgsField("Conductor de tierra ",QVariant.String, "str", 3))
        SinkFieldsLine.append(QgsField("Tipo de conductor de tierra ",QVariant.String, "str",500, 0))
        Line.setFields(SinkFieldsLine)

                                                                # Y aquí se rellena los Fields con sus Atributos
        Index_Attr = Line.fieldNameIndex("Identificador ")
        Line.setAttribute(Index_Attr, Id_Line)
        Index_Attr = Line.fieldNameIndex("Características del conductor ")
        Line.setAttribute(Index_Attr, info_line)
        Index_Attr = Line.fieldNameIndex("Tensión de línea (kV) ")
        Line.setAttribute(Index_Attr,volt_line)
        Index_Attr = Line.fieldNameIndex("Sistema doble circuito ")
        if sist_doble_circ == True:
            Line.setAttribute(Index_Attr,"Sí")
        else:
            Line.setAttribute(Index_Attr,"No")            
        Index_Attr = Line.fieldNameIndex("Precio unitario (€/km) ")
        Line.setAttribute(Index_Attr, cost_conductor)
        Index_Attr = Line.fieldNameIndex("Distancia aproximada (m) ")
        Line.setAttribute(Index_Attr, LengthLine)
        Index_Attr = Line.fieldNameIndex("Coste por fase (€) ")
        Line.setAttribute(Index_Attr, CostLine)
        Index_Attr = Line.fieldNameIndex("Conductor de tierra ")
        if ground_line == True:
            Line.setAttribute(Index_Attr,"Sí")
            Index_Attr = Line.fieldNameIndex("Tipo de conductor de tierra ")
            Line.setAttribute(Index_Attr, info_ground)
        else:
            Line.setAttribute(Index_Attr,"No")  
#*****************************************************************************************************************************        
#*****************************************************************************************************************************
   
                                                        # Declara que el archivo de salida será tipo Line (Lineal)   
        Out_Geom_Type = QgsWkbTypes.LineString                                   

                                                                # Se declara la salida
        (Sink_Line, Dest_id_Line) = self.parameterAsSink(                       
            parameters,
            self.OUT_LINE,                                      # Salida
            context,
            fields = SinkFieldsLine,                            # Fields de la salida
            geometryType = Out_Geom_Type,                       # Tipo de la geometria de la salida
            crs = raster.crs(),                                 # CRS del archivo de salida
        )

        if Sink_Line is None:                                   # Mensaje de Error, si la salida estuviese vacía
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUT_LINE))


                                                                # En caso de tener que añadir la línea creada a un proyecto..
                                                                # .. ya existente, entonce se procede a continuación ..                                                               
        if exist_line != None:
            if len(list(exist_line.getFeatures())) > 0:
                if raster.crs() == exist_line.sourceCrs():
                    exist_line_feature = list(exist_line.getFeatures())     # .. se guarda todos los Features que tenga dicho proyecto
                else:                                                       # .. para juntarlo posteriormente con la línea creada.
                    raise QgsProcessingException(self.tr("Error! La capa vectorial del proyecto existente no tiene el mismo CRS que el raster."))                    
            else:                                                       # Mensajes de Error
                raise QgsProcessingException(self.tr("Error! La capa del proyecto existente introducida está vacío."))   


    
        if exist_line != None:                                  # Si hay que crear una Capa con los Features existentes + la línea diseñada
            if len(list(exist_line.getFeatures())) > 0:         # A continuación, se almacena todos los Features existentes ..
                exist_line_feature.append(Line)                 # .. más la línea creada, en una lista.
                Sink_Line.addFeatures(exist_line_feature, QgsFeatureSink.FastInsert)    # La lista se añade al contenedor de salida
        else:                                                   # Si solo hay que crear una Capa con la línea diseñada
            Sink_Line.addFeature(Line, QgsFeatureSink.FastInsert)       # Se añada al contenedor de salida la línea diseñada


        return {self.OUT_LINE: Dest_id_Line}                    # Salida, se dibuja la capa vectorial, con la línea diseñada ..
                                                                # .. y en caso de haber sido especificado, junto a los Features ..
                                                                # .. existentes del proyecto existente introducido como entrada.
#*************************************************************************************************************
    def name(self):
        return 'Transmission Line Routing'        # Para el nombre del título del cuadro de texto de ayuda

        

    def displayName(self):

        return self.tr(self.name())                             # Función para mostrar el título del cuadro de texto de ayuda

    def tr(self, string):			                # Función que escribe en el cuatro de texto
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):                                   # Función que instancia la clase
        return TransmissionLineRoutingAlgorithm()

    def shortHelpString(self):                                  # Texto del cuadro de ayuda del plugin
        return self.tr("""
        Este plugin traza el recorrido mínimo, comprendido entre un punto origen y un punto destino, dentro de una capa ráster.
        Enfocado a ayudar en la decisión de cuál recorrido es mejor para una línea eléctrica.
        También es posible introducir puntos intermedios si se quiere. Los parámetros son los siguientes:

        - Capa ráster: Ráster numérico de una sola banda. Sin valores No Data.
        - Apoyo Origen: Capa vectorial formado por un solo punto. Aquí comenzará la línea eléctrica.
        - Apoyo(s) Intermedio(s): Capa vectorial formado por uno o más puntos. Por aquí pasará la línea eléctrica.
        - Apoyo Final: Capa vectorial formado por un solo punto. Aquí terminará la línea eléctrica.
        - Proyecto existente de línea(s) eléctrica(s): Capa vectorial de una o más líneas. Se usa en caso de querer juntarlo con la línea a diseñar en el plugin.

        NOTA: Las Capas Vectoriales de entrada no pueden estar vacías sin ningún elemento geométrico. Además deben tener el mismo CRS que el Ráster.

        - Características del cable de la línea: Material, Sección , ...
        - Precio unitario del conductor: Precio que vale el cable conductor en €/km.
        - Tensión de la línea: Voltaje que tendrá la línea eléctrica en kV.
        - Se puede indicar si el sistema es de Doble Circuito y si tendrá un conductor para la tierra.
        - Características del cable de tierra: Material, Sección, ...
        - Identificación de la línea eléctrica: Para el nombre de la línea eléctrica que se diseña.""")
#*************************************************************************************************************

