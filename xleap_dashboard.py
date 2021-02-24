import time
from os import path
from pydm import Display
from pydm.widgets import channel
from pydm.widgets.waveformplot import WaveformCurveItem
from qtpy.QtWidgets import QCheckBox, QWidget, QVBoxLayout
from qtpy.QtCore import Signal, Slot, Property, QTimer, QThread
from PyQt5.QtGui import QColor
import time
import numpy as np
#import h5py as h5py


class xleap_dashboard(Display):
    def __init__(self, parent=None, args=None, macros=None):
        super(xleap_dashboard, self).__init__(parent=parent, args=args, macros=None)

        self.specSumCurve=self.ui.PyDMTimePlot.addYChannel(y_channel=None, name='Sum spec', color='#ea2e06', lineStyle=1, lineWidth=1, symbol=None, symbolSize=None)
        self.specRmsCurve=self.ui.PyDMTimePlot.addYChannel(y_channel=None, name='FWHM spec', color='#f59042', lineStyle=0, lineWidth=1, symbol=1, symbolSize=2)

#Set up analysis channel        
        mypv = channel.PyDMChannel(address='TMO:VLS:CAM:01:IMAGE2:ArrayData', value_slot=self.forwardWaveformStats)
        mypv.connect()
        self.WFthread=None
        self.sumScale=10000
        self.rmsScale=1;
        abscissa=np.linspace(-10,10,25); #About 15px/eV, so 3px rms is a safe filter
        self.filter=np.exp(-0.5*(abscissa/3)**2)
        self.filter=self.filter/np.sum(self.filter)
#Plot settings        
        #QColor(255, 0, 0, 127)
        self.PyDMTimePlot.maxRedrawRate=1
        self.PyDMWaveformPlot.maxRedrawRate=1
        self.RefreshRateTimechart.returnPressed.connect(self.setRefreshRateTimechart)
        self.RefreshRateWaveform.returnPressed.connect(self.setRefreshRateWaveform)

        self.timeYmin.returnPressed.connect(self.setTimechartYRange)
        self.timeYmax.returnPressed.connect(self.setTimechartYRange)
        self.timeSumScale.returnPressed.connect(self.setTimeSumScale)
        self.timeRmsScale.returnPressed.connect(self.setTimeRmsScale)
        
        self.specXmin.returnPressed.connect(self.setWaveformXRange)
        self.specXmax.returnPressed.connect(self.setWaveformXRange)       
        
        self.PyDMWaveformPlot.autoRangeY=False
        self.PyDMWaveformPlot.minYRange=300
        self.PyDMWaveformPlot.maxYRange=800
#Persistance
        self.numPersist=10;
        self.waveformPersistIdx=0;
        self.NPersist.returnPressed.connect(self.setNpersist)
        self.waveformPersists=[];
        for x in range(self.numPersist):
            plot_opts = {}
            plot_opts['lineStyle'] = 1
            plot_opts['lineWidth'] = 1
            plot_opts['redraw_mode'] = WaveformCurveItem.REDRAW_ON_EITHER
            self.ui.PyDMWaveformPlot._needs_redraw = False
            curve = WaveformCurveItem(y_addr=None,
                                      x_addr=None,
                                      name=None,
                                      color=QColor(255,0,0,60),
                                      **plot_opts)
            self.ui.PyDMWaveformPlot.channel_pairs[(None, None)] = curve
            self.ui.PyDMWaveformPlot.addCurve(curve, curve_color=QColor(255,0,0,200))
            curve.data_changed.connect(self.ui.PyDMWaveformPlot.set_needs_redraw)
            self.waveformPersists.append(curve)
        persistPV = channel.PyDMChannel(address='TMO:VLS:CAM:01:IMAGE2:ArrayData', value_slot=self.persistCallback)
        persistPV.connect()       
                               
    def ui_filename(self):
        # Point to our UI file
        return 'xleap_dashboard.ui'

    def ui_filepath(self):
        # Return the full path to the UI file
        return path.join(path.dirname(path.realpath(__file__)), self.ui_filename())
    
    def setNpersist(self):
        # Just delete all old curves and add N new ones. Overhead ok if not done often.
        [self.ui.PyDMWaveformPlot.removeChannel(x) for x in self.waveformPersists]
        self.numPersist=int(self.setNpersist.text())
        self.waveformPersists=[];
        for x in range(self.numPersist):
            plot_opts = {}
            plot_opts['lineStyle'] = 1
            plot_opts['lineWidth'] = 1
            plot_opts['redraw_mode'] = WaveformCurveItem.REDRAW_ON_EITHER
            self.ui.PyDMWaveformPlot._needs_redraw = False
            curve = WaveformCurveItem(y_addr=None,
                                      x_addr=None,
                                      name=None,
                                      color=QColor(255,0,0,60),
                                      **plot_opts)
            self.ui.PyDMWaveformPlot.channel_pairs[(None, None)] = curve
            self.ui.PyDMWaveformPlot.addCurve(curve, curve_color=QColor(255,0,0,200))
            curve.data_changed.connect(self.ui.PyDMWaveformPlot.set_needs_redraw)
            self.waveformPersists.append(curve)
        persistPV = channel.PyDMChannel(address='TMO:VLS:CAM:01:IMAGE2:ArrayData', value_slot=self.persistCallback)
        persistPV.connect()
        return None
    
    @Slot(np.ndarray)
    def persistCallback(self,values):
        self.waveformPersists[self.waveformPersistIdx].receiveYWaveform(values)
        if self.waveformPersistIdx<(len(self.waveformPersists)-1):
             self.waveformPersistIdx= self.waveformPersistIdx+1
        else:
             self.waveformPersistIdx=0
        
    def setRefreshRateTimechart(self):
        try:
            self.PyDMTimePlot.maxRedrawRate=float(self.RefreshRateTimechart.text())
        except:
            pass
    def setRefreshRateWaveform(self):
        try:
            self.PyDMWaveformPlot.maxRedrawRate=float(self.RefreshRateWaveform.text())
        except:
            pass
    def setTimechartYRange(self):
        self.PyDMTimePlot.autoRangeY=False
        if len(self.timeYmin.text())>0:
            try:
                self.PyDMTimePlot.minYRange=float(self.timeYmin.text())
            except:
                pass
        if len(self.timeYmax.text())>0:
            try:
                self.PyDMTimePlot.maxYRange=float(self.timeYmax.text())
            except:
                pass
    def setTimeSumScale(self):
        try:
            self.sumScale=float(self.timeSumScale.text())*10000
        except:
            pass
    def setTimeRmsScale(self):
        try:
            self.rmsScale=float(self.timeRmsScale.text())
        except:
            pass
    def setWaveformXRange(self):
        self.PyDMWaveformPlot.autoRangeX=False
        if len(self.specXmin.text())>0:
            try:
                self.PyDMWaveformPlot.minXRange=float(self.specXmin.text())
            except:
                pass
        if len(self.specXmax.text())>0:
            try:
                self.PyDMWaveformPlot.maxXRange=float(self.specXmax.text())
            except:
                pass

    
    @Slot(np.ndarray)
    def forwardWaveformStats(self,values):
        """
        Calls thread to analysze waveform stats and sends them to a time plot, provided we are not currently processing a waveform.
        Values is the waveform.
        """
        if self.WFthread is not None and not self.WFthread.isFinished():
            #logger.warning(
            #    "Image processing has taken longer than the refresh rate.")
            return
        self.waveform=values
        self.WFthread = waveformUpdateThread(self)
        self.WFthread.updateSignal.connect(self.__updateWaveformStats) #when waveformUpdateThread emits we run __updateWaveformStats and it sends the data to the plotting widget
        #logging.debug("ImageView RedrawImage Thread Launched")
        self.WFthread.start()        
    def __updateWaveformStats(self,data):
        fwhm,tot=data[0],data[1]
        self.specRmsCurve.receiveNewValue(tot)
        self.specSumCurve.receiveNewValue(fwhm)
        
    def SpecAnalysis(self,values):
        if int(self.PyDMWaveformPlot.minXRange)<int(self.PyDMWaveformPlot.maxXRange):
            values=values[int(self.PyDMWaveformPlot.minXRange):int(self.PyDMWaveformPlot.maxXRange)]
        values=np.convolve(values,self.filter,'same')
        lowmask=values<np.percentile(values,25)
        bg=np.median(values[lowmask])
        values=values-bg
        total=sum(values)/self.sumScale
        #self.specSumCurve.receiveNewValue(sum(values)/self.sumScale)
        idx=np.argmax(values)
        idx1=np.clip(idx-5,0,len(values))
        idx2=np.clip(idx+5,0,len(values))
        if np.mean(values[idx1:idx2])>(50+3*np.std(values[lowmask])+np.mean(values[lowmask])):
            fwhm=np.abs(np.diff(peak_fwhm(idx,values,outfrompeak=True,interp=True)))
            #self.specRmsCurve.receiveNewValue(fwhm/self.rmsScale)
        else:
            fwhm=0;
        return total,fwhm
    
class waveformUpdateThread(QThread):
    """Single thread for running waveform analysis. Emits results of calcultion when done. Has an inhereited .isFinished() which is used to check when analysis is done.
"""
    updateSignal = Signal(list)

    def __init__(self, dashboard_view):
        QThread.__init__(self)
        self.dashboard_view = dashboard_view

    def run(self):
        waveform = self.dashboard_view.waveform       

        if len(waveform) <= 0:
            return

        total,fwhm = self.dashboard_view.SpecAnalysis(waveform)
        self.updateSignal.emit([total,fwhm])
        
def peak_fwhm(pk_idx,lis,thresh=None,outfrompeak=True,interp=False):
    """
    pk_idx: integer index of the peak in list
    lis: the list of values
    thresh: the value of the threshold. An absolute number. Default is max(list)/2 which would give FWM
    outfrompeak: bool choice whether to search starting from peak, or from edges of list
    interp: bool choice whether to interpolate value between last two points.
    
    Note search is exclusice: so values found will be at or lower than Thresh (rather than last "Good" point)
    returns: pt1,pt2
    """
    m=lis[pk_idx]
    if thresh==None:
        thresh=m/2
    pt1=pk_idx;pt2=pk_idx;
    if outfrompeak:
        try:
            for idx,l in enumerate(np.flip(lis[0:pk_idx],0)):
                if l<=thresh:
                    pt1=pk_idx-idx-1;
                    break
        except:
            pt1=0
        try:
            for idx,l in enumerate(lis[pk_idx:]):
                if l<=thresh:
                    pt2=pk_idx+idx;
                    break
        except:
            pt2=len(lis)
    else:
        try:
            for idx,l in enumerate(lis[0:pk_idx]):
                if l>=thresh:
                    pt1=idx-1;
                    break
        except:
            pt1=0
        try:
            for idx,l in enumerate(np.flip(lis[pk_idx:],0)):
                if l>=thresh:
                    pt2=len(lis)-idx;
                    break
        except:
            pt2=len(lis)
        pt1=np.clip(pt1,1,len(lis)-2)
        pt2=np.clip(pt2,1,len(lis)-2)
    #print(lis[pt1],lis[pt2])
    if interp:
        try:
            invweights=np.abs(np.array(lis[pt1:pt1+2])-thresh)
            invweights[invweights==0]=1e5;
            weights=1/invweights
            pt1=np.sum(np.array([pt1,pt1+1]*weights)/np.sum(weights))
        except:
            pt1=pt1
        try:
            invweights=np.abs(np.array(lis[pt2-1:pt2+1])-thresh)
            invweights[invweights==0]=1e-5;
            weights=1/invweights
            pt2=np.sum(np.array([pt2-1,pt2]*weights)/np.sum(weights))
        except:
            pt2=pt2
        pt1=np.clip(pt1,0,len(lis)-2)
        pt2=np.clip(pt2,0,len(lis)-2)
    return pt1,pt2