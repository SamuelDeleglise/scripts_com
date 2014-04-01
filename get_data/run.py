from PyQt4 import QtCore, QtGui
from pyinstruments.pyhardwaredb import instrument
from pyinstruments.curvestore import models
from time import sleep
import curve
import pandas as p
import math

vsa = instrument("vsa")
afg_fb=instrument("AFG_CHI")
osc = instrument("Atchoum")

class RunCOM(QtGui.QWidget):
    def __init__(self, default_sleep=10, default_sleep_lock_time=10000, default_gain=-400, default_angle=177, default_lock_pt=0):
        super(RunCOM, self).__init__()
        self.tags = [self.get_current_tag()]
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(default_sleep)
        self.timer.timeout.connect(self.take_data)
        
        self.timer_lock = QtCore.QTimer()
        self.timer_lock.setSingleShot(True)
        self.timer_lock.setInterval(default_sleep_lock_time)
        self.timer_lock.timeout.connect(self.lock)
        
        self.button_start = QtGui.QPushButton("Start")
        self.button_start.clicked.connect(self.button_start_clicked)
        
        self.button_stop = QtGui.QPushButton("Stop")
        self.button_stop.clicked.connect(self.button_stop_clicked)
        
        self.label_acq = QtGui.QLabel("Acquisition")
        
        self.label = QtGui.QLabel('sleep time (s)')
        self.sleep_time_box = QtGui.QSpinBox() 
        self.sleep_time_box.setMaximum(int(1e9))
        self.checkbox_auto_sleep = QtGui.QCheckBox("auto")
        
        self.checkbox_restart = QtGui.QCheckBox("Restart averaging on start")
        
        self.label_lock_time = QtGui.QLabel('lock duty time (ms)')
        self.sleep_time_lock_box = QtGui.QSpinBox() 
        self.sleep_time_lock_box.setMaximum(int(1e9))
        self.sleep_time_lock_box.setValue(default_sleep_lock_time)
        
        self.label_lock = QtGui.QLabel("Lock")
        
        self.lock_pt_label = QtGui.QLabel('Target')
        self.lock_pt_line = QtGui.QLineEdit(str(default_lock_pt))
#        self.lock_pt_box.setMaximum(1e-7)
#        self.lock_pt_box.setMinimum(-1e-7)
        
        self.power_label = QtGui.QLabel('input power (mW)')
        self.power_box = QtGui.QDoubleSpinBox() 
        
        self.gain_label = QtGui.QLabel('gain')
        self.gain_box=QtGui.QSpinBox()
        self.gain_box.setMaximum(100000)
        self.gain_box.setMinimum(-100000)
        self.gain_box.setValue(default_gain)
        
        self.angle_label = QtGui.QLabel('angle')
        self.angle_box = QtGui.QDoubleSpinBox()
        self.angle_box.setMaximum(180.)
        self.angle_box.setMinimum(-180.)
        self.angle_box.setValue(default_angle)
        
        self.button_start_lock = QtGui.QPushButton("Start")
        self.button_start_lock.clicked.connect(self.button_start_lock_clicked)
        
        self.button_stop_lock = QtGui.QPushButton("Stop")
        self.button_stop_lock.clicked.connect(self.button_stop_lock_clicked)
        
        self.hlay1 = QtGui.QHBoxLayout()
        self.hlay1.addWidget(self.label_acq)
        self.hlay1.addStretch(1)
        self.hlay1.addWidget(self.button_start)
        self.hlay1.addWidget(self.button_stop)
        
        
        self.hlay5 = QtGui.QHBoxLayout()
        self.hlay5.addStretch(1)
        self.hlay5.addWidget(self.checkbox_restart)
        
        self.hlay2 = QtGui.QHBoxLayout()
        self.hlay2.addWidget(self.label)
        self.hlay2.addWidget(self.sleep_time_box)
        self.hlay2.addStretch(1)
        self.hlay2.addWidget(self.checkbox_auto_sleep)

        self.hlay3 = QtGui.QHBoxLayout()
        self.hlay3.addWidget(self.label_lock_time)
        self.hlay3.addWidget(self.sleep_time_lock_box)
        self.hlay3.addStretch(1)
        self.hlay3.addWidget(self.gain_label)
        self.hlay3.addWidget(self.gain_box)

        self.hlay4 = QtGui.QHBoxLayout()
        self.hlay4.addWidget(self.power_label)
        self.hlay4.addWidget(self.power_box)
        
        self.hlay6 = QtGui.QHBoxLayout()
        self.hlay6.addWidget(self.label_lock)
        self.hlay6.addStretch(1)
        self.hlay6.addWidget(self.button_start_lock)
        self.hlay6.addWidget(self.button_stop_lock)

        self.hlay7 = QtGui.QHBoxLayout()
        self.hlay7.addWidget(self.lock_pt_label)
        self.hlay7.addWidget(self.lock_pt_line)
        self.hlay7.addStretch(1)
        self.hlay7.addWidget(self.angle_label)
        self.hlay7.addWidget(self.angle_box)

        self.v_lay = QtGui.QVBoxLayout()
        self.v_lay.addLayout(self.hlay1)
        self.v_lay.addLayout(self.hlay5)
        self.v_lay.addLayout(self.hlay2)
        self.v_lay.addLayout(self.hlay6)
        self.v_lay.addLayout(self.hlay3)
        self.v_lay.addLayout(self.hlay7)
        self.v_lay.addLayout(self.hlay4)
        self.setLayout(self.v_lay)
        self.setWindowTitle("runCOM")
        
        self.sleep_time = default_sleep
        self.show()
        
        self.curveLock_rms=[]
        self.curveLock_intg=[]
        self.curveLock_cor=[]
        self.gain=default_gain
        self.angle=default_angle
        self.lock_pt=default_lock_pt

    def button_start_clicked(self):
        if self.isRestart:
            vsa.restart()
            vsa.pause()
            sleep(5)
            vsa.pause()
        self.take_data()
        self.timer.setInterval(1000*(self.sleep_time))
        self.timer.start()
        
    def button_stop_clicked(self):
        self.timer.stop()
        
    def button_start_lock_clicked(self):
        afg_fb.sc.channel_idx=2
        self.residual_offset=afg_fb.sc.offset
        self.lock()
        self.timer_lock.setInterval(self.sleep_lock_time)
        self.timer_lock.start()
        
    def button_stop_lock_clicked(self):
        self.timer_lock.stop()
            
    def take_curve(self, label, n_av):
        vsa.active_label = label
        curve = vsa.get_curve()
        curve.tags+= self.tags
        curve.params["current_average"] = n_av
        curve.params["name"] = curve.params["data_name"] + "_" +\
                                str(curve.params["current_average"])
        curve.params["power"] = self.power
        curve.params["angle"] = self.angle
        curve.params["lock"] = self.lock_pt
        curve.save()
        
    def take_data(self):
        print 'taking data'
        vsa.pause()
        n_av = vsa.current_average("C") # bug du vsa, seuls les cross-spectra ont le bon RMS
        self.take_curve('A',n_av)
        self.take_curve('B',n_av)
        self.take_curve('C',n_av)
        self.take_curve('E',n_av)
        self.take_curve('F',n_av)
        self.take_curve('G',n_av)
        self.take_curve('H',n_av)
        if self.isAuto:
            self.sleep_time=self.sleep_time*2
        self.timer.setInterval(1000*self.sleep_time)
        vsa.resume()
        self.timer.start()
        
    @property
    def sleep_time(self):
        return self.sleep_time_box.value()
    
    @sleep_time.setter
    def sleep_time(self, val):
        self.sleep_time_box.setValue(val)
        
    @property
    def sleep_lock_time(self):
        return self.sleep_time_lock_box.value()
    
    @sleep_lock_time.setter
    def sleep_lock_time(self, val):
        self.sleep_time_lock_box.setValue(val)
        
    @property
    def gain(self):
        return self.gain_box.value()
    
    @gain.setter
    def gain(self, val):
        self.gain_box.setValue(val) 

    @property
    def angle(self):
        return self.angle_box.value()

    @angle.setter
    def angle(self, val):
        self.angle_box.setValue(val)

    @property
    def lock_pt(self):
        while True:
            try:
                return float(self.lock_pt_line.text())
            except ValueError:
                print "invalid lock point"

    @lock_pt.setter
    def lock_pt(self,val):
        try:
            self.lock_pt_line.setText(str(val))
        except ValueError:
            print "invalid lock point"

    @property
    def power(self):
        return self.power_box.value()
    
    @power.setter
    def power(self, val):
        self.power_box.setValue(val)

    def get_current_tag(self):
        existing = models.Tag.objects.filter(name__startswith="runCOM")
        num_max = 0
        for tag in existing:
            num_str = tag.name.split("/")[-1]
            try:
                num = int(num_str)
            except ValueError:
                pass
            else:
                num_max = max(num_max, num)
        return "runCOM/%04i"%(num_max+1)

    @property
    def isAuto(self):
        return bool(self.checkbox_auto_sleep.checkState())

    @isAuto.setter
    def isAuto(self, val):
        return self.checkbox_auto_sleep.setCheckState(2*val)
    @property
    def isRestart(self):
       return bool(self.checkbox_restart.checkState())
    
    @isRestart.setter
    def isRestart(self, val):
       return self.checkbox_restart.setCheckState(2*val)

    @property
    def intgr(self):
        vsa.active_label='G'
        c_re=vsa.get_curve()
        vsa.active_label='H'
        c_im=vsa.get_curve()
        re = c_re.data[(c_re.data.size-1)/2]
        im = c_im.data[(c_im.data.size-1)/2]
        intgr = math.cos(math.radians(self.angle))*re+math.sin(math.radians(self.angle))*im
        return intgr*vsa.current_average('C')
#        return -im
#        return norm*vsa.current_average()*signe_re

    def apply_cor(self,cor):
        afg_fb.sc.channel_idx=2
        afg_fb.sc.offset=cor
        
    def lock(self):
        print "Locking"
        gain_fb=-self.gain*self.sleep_lock_time
        cur_intgr=self.intgr
        n_av=vsa.current_average('C')
        cor=-gain_fb*(cur_intgr-self.lock_pt*n_av)*1e1+self.residual_offset
        if cor>5:
            cor=5
        if cor<-5:
            cor=-5
        self.apply_cor(cor)
        print "intgr : %g cor : %.4f lock %g" %(cur_intgr, cor, cur_intgr/n_av)
        self.curveLock_rms.append(vsa.current_average())
        self.curveLock_intg.append(cur_intgr)
        self.curveLock_cor.append(cor)
        self.timer_lock.setInterval(self.sleep_lock_time)
        self.timer_lock.start()

    def get_lock_curveDB(self):
        return p.DataFrame({"cor":self.curveLock_cor,"err":self.curveLock_intg},
                    index=self.curveLock_rms)

def check_lock(trshld=3e-2):
    osc.channel_idx=4
    c = osc.get_curve()
    if c.data.mean()>trshld:
        print "Acquisition posed"
        vsa.pause()

class Watch_lock():
    def __init__(self, time=100., trshld=3e-2, meas=0):
        self.timer = QtCore.QTimer()
        self.timer.setInterval(time)
        self.timer.timeout.connect(self.check_lock)
        self.timer.start()
        self.trshld = trshld
        self.meas=meas

    def check_lock(self):
        osc.channel_idx=4
        c = osc.get_curve()
        if c.data.mean()>self.trshld:
            print "Acquisition paused"
            vsa.pause(self.meas)
        else:
            print "Locked"
            self.timer.start()


