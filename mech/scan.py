from pyinstruments.pyhardwaredb import instrument
from pyinstruments.curvestore import models
from pandas import *
from time import sleep

na = instrument("NA")

def get_span(bw,points,ppb):
    return float(bw)*points/ppb

def get_cfs(start,stop,span):
    n_cf=int( (stop-start)/span )
    s = Series( range(n_cf) )
    s=s*span
    s=s+start+span/2.
    return s

def scan(start=200e3, stop=5e6, bw=10., ppb=10., points=1601):
    na.driver.sc_active_channel.points=points
    na.driver.sc.if_bandwidth=bw
    span=get_span(bw,points,ppb)
    na.driver.sc.span=span
    swp_time=na.driver.sc.sweep_time+2.
    centers=get_cfs(start,stop,span)
    for c in centers:
        na.driver.sc.frequency_center=c
        sleep(swp_time)
        curve=na.get_curve()
        curve.save()

def concat(pid):
    cp=models.CurveDB.objects.get(id=pid)
    cs=cp.childs.filter_param("name",value__contains='na_curve')
    s=Series()
    for c in cs:
        s=s.append(c.data)
    return s

def sxrad(mod,rep,shot,therm):
    '''return the sxrad/sxT ratio'''
    return(rep.max()/mod.max()/therm[rep.argmax()])*shot.mean()


def align(c_1, c_2):
    '''align c_2 on c_1'''
    try:
        d = c_1.data.argmax()-c_2.data.argmax()
        a = Series(data=c_2.data.values,index=d+c_2.data.index)
    except AttributeError:
        d = c_1.argmax()-c_2.argmax()
        a = Series(data=c_2.values,index=d+c_2.index)
    except:
        raise
    return a

def scaledb(c_1,c_2):
    '''scale c_2 on c_1, max are then the same'''
    try:
        d = c_1.data.max()-c_2.data.max()
        a = Series(data=c_2.data.values+d,index=c_2.data.index)
    except AttributeError:
       d = c_1.max()-c_2.max()
       a = Series(data=c_2.values+d,index=c_2.index)
    except:
        raise
    return a

    