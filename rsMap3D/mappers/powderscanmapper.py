'''
 Copyright (c) 2017 UChicago Argonne, LLC
 See LICENSE file.
'''
import os
import numpy as np
from rsMap3D.exception.rsmap3dexception import RSMap3DException
from rsMap3D.transforms.unitytransform3d import UnityTransform3D
from xrayutilities.gridder import Gridder1D
import logging
from rsMap3D.gui.rsm3dcommonstrings import EMPTY_STR
from rsMap3D.config.rsmap3dlogging import METHOD_ENTER_STR
logger = logging.getLogger(__name__)
X_COORD_OPTIONS = ["tth", "q"]
Y_SCALING_OPTIONS  = ["Linear","log"]


class PowderScanMapper():
    '''
    This mapper takes data from a general diffraction scan and maps 
    the data as Intensity vs q or intensity vs 2-theta.  This outputs
    data into one three column text file per selected scan.
    '''
    def __init__(self,
                 dataSource,
                 outputFileName,
                 transform = None,
                 gridWriter = None,
                 appConfig = None,
                 dataCoord = X_COORD_OPTIONS[0],
                 xCoordMin = None,
                 xCoordMax = None,
                 xCoordStep = None,
                 plotResults = False,
                 yScaling  = Y_SCALING_OPTIONS[0],
                 writeXyeFile = True
                 ):
        self.dataSource = dataSource
        self.outputFileName = outputFileName
        self.gridWriter = gridWriter
        self.appConfig = None
        self.progressUpdater = None
        if transform is None:
            self.transform = UnityTransform3D()
        else:
            self.transform = transform
        if not (appConfig is None):
            self.appConfig = appConfig
        else:
            raise RSMap3DException("No AppConfig object received")
        self.dataCoord = dataCoord
        self.yScaling = yScaling
        self.plotResults = plotResults
        self.writeXyeFile = writeXyeFile
        self.xCoordMin = xCoordMin
        self.xCoordMax = xCoordMax
        self.XCoordStep = xCoordStep
    
        
    def doMap(self):
        '''
        This method controls the processing of the mapping and subsequent 
        writing of the map file.  This method should be launched by the 
        runMapper of a "process" map output gui.
        '''
        """ 
        #===== ZZ 2020/02/19
        # Now do not just do one map per scan here, instead, 
        #  at this level, one map per group of scans
        for scan in self.dataSource.getAvailableScans():
            self.currentMapScans = [scan,]
            x, y, e = self.processMap()

            self.gridWriter.setData(x, y, e)
            self.gridWriter.setFileInfo(self.getFileInfo())
            self.gridWriter.write()
        """
        self.currentMapScans =  self.dataSource.getAvailableScans()
        x, y, e = self.processMap()

        if self.writeXyeFile or self.plotResults:
            self.gridWriter.setData(x, y, e)
            self.gridWriter.setFileInfo(self.getFileInfo())
          
        if self.writeXyeFile:
            self.gridWriter.write()
        if self.plotResults:
            self.gridWriter.plot()
        
        
    def getFileInfo(self):
        '''
        Pack together information needed to write the data.
        '''
        xMin = self.getXCoordMin()
        xMax = self.getXCoordMax()
        xStep = float(self.XCoordStep)
        numBins = np.round((xMax-xMin)/xStep)
        return (str(os.path.join(self.dataSource.projectDir, self.dataSource.projectName)),
                self.currentMapScans[0],
                numBins,
                self.outputFileName,
                self.dataCoord,
                self.yScaling) #===== carry over the xlabel and y scanling, ZZ 
        
    def getXCoordMax(self):
        '''
        for this one dimensional mapping get the maximum value of the 
        x coordinate.  If a value was specified on the input then that 
        value will be used.  If no value was specified, then one is 
        calculated from the qx, qy, qz values.
        '''
        logger.debug(METHOD_ENTER_STR)
        xMax = None
        scans = self.currentMapScans
        wavelen = 12398.41290/self.dataSource.getIncidentEnergy()[scans[0]]
        if not (self.xCoordMax is None) and \
            not (self.xCoordMax == EMPTY_STR):
            xMax = float(self.xCoordMax)
        else:
            qxMin, qxMax, qMin, qyMax, qzMin, qzMax = \
                self.dataSource.getRangeBounds()
            absQxMax = np.max(np.fabs([qxMin, qxMax]))
            absQyMax = np.max(np.fabs([qMin, qyMax]))
            absQzMax = np.max(np.fabs([qzMin, qzMax]))
            QMax = np.sqrt(absQxMax**2 + absQyMax**2 + absQzMax**2)
            if self.dataCoord == X_COORD_OPTIONS[0]:
                xMax = np.rad2deg(np.arcsin((QMax*wavelen)/
                    (4.0 * np.pi))*2.0)
            else:
                xMax = QMax
        logger.debug("xMax %f" % xMax)
        return xMax
        
    def getXCoordMin(self):
        '''
        for this one dimensional mapping get the minimum value of the 
        x coordinate.  If a value was specified on the input then that 
        value will be used.  If no value was specified, then one is 
        calculated from the qx, qy, qz values.
        '''
        logger.debug(METHOD_ENTER_STR)
        xMin = None
        scans = self.currentMapScans
        wavelen = 12398.41290/self.dataSource.getIncidentEnergy()[scans[0]]
        if not (self.xCoordMin is None) and not (self.xCoordMin == EMPTY_STR):
            xMin = float(self.xCoordMin)
        else:
            qxMin, qxMax, qyMin, qyMax, qzMin, qzMax = \
                self.dataSource.getRangeBounds()
            absQxMin = None
            if np.sign(qxMin) != np.sign(qxMax):
                absQxMin = 0.0
            else:
                absQxMin =  np.min(np.fabs([qxMin, qxMax]))
            absQyMin = None
            if np.sign(qyMin) != np.sign(qyMax):
                absQyMin = 0.0
            else:
                absQyMin =  np.min(np.fabs([qyMin, qyMax]))
            absQzMin = None
            if np.sign(qzMin) != np.sign(qzMax):
                absQzMin = 0.0
            else:
                absQzMin =  np.min(np.fabs([qzMin, qzMax]))
            QMin = np.sqrt(absQxMin**2 + absQyMin**2 + absQzMin**2)
            if self.dataCoord == X_COORD_OPTIONS[0]:
#                 logger.debug("QMin %f, wavelen %f, arcsin(arg) %f" %
#                              (QMin, wavelen, ))
                xMin = np.rad2deg(np.arcsin((QMin*wavelen)/
                    (4.0 * np.pi))*2.0)
            else:
                xMin = QMin
        logger.debug("xMin %f" % xMin)
        return xMin
    
    def processMap(self):
        '''
        read frames grid them and write the results
        '''
        maxImageMem = self.appConfig.getMaxImageMemory()
        xStep = float(self.XCoordStep)
        xMin = self.getXCoordMin() - xStep/2.0
        xMax = self.getXCoordMax() + xStep/2.0
        numBins = np.round((xMax - xMin) / xStep)
        gridder = Gridder1D(int(numBins))
        gridder.KeepData(True)
        gridder.dataRange(xMin, xMax)

        imageToBeUsed = self.dataSource.getImageToBeUsed()
        imageSize = np.prod(self.dataSource.getDetectorDimensions())
        #===== Add progress indicator, ZZ 2020/02/14
        progress = 0
        data_segment = len(self.currentMapScans)
        #logger.info('Total number of scans : %s (%s)' % (data_segment, self.currentMapScans) )
        #=====
        for scan in self.currentMapScans:
            wavelen = 12398.41290/self.dataSource.getIncidentEnergy()[scan]
            logger.info("Scan Number %s" % scan)
            numImages = len(imageToBeUsed[scan])
            if imageSize * 4 * numImages <= maxImageMem:
                logger.info("Only 1 pass required")
                qx, qy, qz, intensity = self.dataSource.rawmap((scan,),
                                                   mask = imageToBeUsed[scan])
                Q = np.sqrt(qx**2 + qy**2 + qz**2)
                coordsX = None
                if self.dataCoord == X_COORD_OPTIONS[0]:    # tth
                    coordsX = np.rad2deg(np.arcsin((Q*wavelen)/(4.0*np.pi))*2.0)
                else:
                    coordsX = Q
                gridder(np.ravel(coordsX), np.ravel(intensity))
                #===== ZZ
                progress += 100.0/data_segment
                if self.progressUpdater is not None:
                    self.progressUpdater(int(progress))
                #=====
            else:
                # np.int() deprecated; use int() instead. ZZ
                nPasses = int(np.floor(imageSize*4*numImages/maxImageMem)+1)
                for thisPass in range(nPasses):
                    logger.info("Pass Number %d of %d" % \
                                (thisPass+1, nPasses))
                    imageToBeUsedInPass = np.array(imageToBeUsed[scan])
                    imageToBeUsedInPass[:int(thisPass*numImages/nPasses)] = \
                        False
                    imageToBeUsedInPass[int((thisPass+1)*numImages/nPasses):] = False
                    qx, qy, qz, intensity = self.dataSource.rawmap((scan,), \
                                                       mask=imageToBeUsedInPass)
                    Q = np.sqrt(qx**2 + qy**2 + qz**2)
                    coordsX = None
                    if self.dataCoord == X_COORD_OPTIONS[0]:
                        coordsX = np.rad2deg(np.arcsin((Q*wavelen)/
                                                     (4.0*np.pi))*2.0)
                    else:
                        coordsX = Q
                    gridder(np.ravel(coordsX), np.ravel(intensity))
                    #===== ZZ
                    progress += 100.0/nPasses / data_segment
                    if self.progressUpdater is not None:
                        self.progressUpdater(int(progress))
                    #=====
        err = np.where(gridder._gnorm > 0.0, 
                       np.sqrt(gridder._gdata)/gridder._gnorm, 0.0)

        return gridder.xaxis, gridder.data, err
    
    def setProgressUpdater(self, updater):
        '''
        Set the updater that will be used to maintain the progress bar 
        value 
        '''
        self.progressUpdater = updater

    def setGridWriter(self, gridWriter):
        ''' 
        set the GridWriter for this instance of the mapper.  Changing 
        the writer will change the output.  For now only the 
        PowderScanWriter is appropriate though
        '''
        self.gridWriter = gridWriter
