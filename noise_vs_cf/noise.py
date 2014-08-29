from pyinstruments.pyhardwaredb import instrument
from pyinstruments.curvestore import models
from numpy import *
from time import sleep

def n_vs_cf(stp=0, srt=10.,npt=100, n_avg=100, vsa_chan="A", afg_='Obelix/2', oscl_='Atchoum/4', parent=None):
    '''
    Give the noise spectrum for different AOM carrier frequency
    '''   
    prt=get_parent('noise_vs_carrier', parent=parent)
    print "Configuring the AFG"
    afg = instrument( afg_.split("/")[0] )
    afg.channel_idx = int(afg_.split("/")[1])
    afg.waveform = 'DC'
    print "Getting the scope"
    oscl = instrument(oscl_.split("/")[0])
    oscl.channel_idx = int(afg_.split("/")[1])
    print "Getting vsa"
    vsa = instrument("vsa")
    vsa.active_label = vsa_chan
    vsa.set_average(n_avg)
    print 'Beginning measurement'
    for v in linspace(stp,srt,npt):
        print "offset %.2f"%(v)
        afg.offset=v
        sleep(1)
        vsa.restart()
        sleep(1)
        vsa.wait_average(n_avg)
        vsa.pause()
        print "taking data"
        take_curve(v, prt, vsa, oscl)
        print 'ok'

def take_curve(v, prt_crv, vsa, oscl):
    prt = get_parent("%.3f"%(v)+"V")
    prt.move(prt_crv)
    prt.save()
    curve = vsa.get_curve()
    curve2 = oscl.get_curve()
    curve.params["name"] = "Noise_%.3f"%(v)+"V"
    curve2.params["name"] = "Int_%.3f"%(v)+"V"
    curve.params["volt"]=v
    curve2.params["volt"]=v
    curve.move(prt)
    curve2.move(prt)
    curve.save()
    curve2.save()
    
def get_parent(name, parent=None):
        if parent is None:
            prt=models.CurveDB()
            prt.name=name
            prt.save()
            return prt
        else:
            prt=models.CurveDB.objects.get(id=parent)
            return prt
        