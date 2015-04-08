from pyinstruments.curvestore import models
from pandas import *
from scipy.optimize import curve_fit, leastsq
from numpy import array
from pylab import plot,figure

def get_bw_refl(c_id, cal_id, f_min=0., f_max=20e6):
    c_scan=models.CurveDB.objects.get(id=c_id)
    c_calib=models.CurveDB.objects.get(id=cal_id)
    refl=c_scan.data/c_calib.data
#    bw=fit_refl( refl, f_min, f_max )
    fitfunc = lambda p, x: (p[1]+1j*x/p[0]) / (1.+1j*x/p[0])
    errfunc = lambda p, x, y: abs( fitfunc(p,x) - y )
    p0=[1e6,1e-6,0.]
    p1, succ = leastsq(errfunc, p0, args=(refl.values,array(refl.index,dtype=float)))
    return p1

def fit_refl(data, f_min=0., f_max=20e6):
    parms, cov = curve_fit(fit_func_refl, data.index, data.data)
    return parms
    
def fit_func_refl(o, l, bw):
    bw=float(bw)
#l is (gamma-P)/gamma, bw is the bandwidth
    return (l+1j*o/bw)/(1-1j*o/bw)


def get_bw_trans(c_id, cal_id, f_min=0., f_max=20e6):
    c_scan=models.CurveDB.objects.get(id=c_id)
    c_calib=models.CurveDB.objects.get(id=cal_id)
    trans=c_scan.data/c_calib.data
#    bw=fit_refl( refl, f_min, f_max )
    fitfunc = lambda p, x: p[1] / (1.+1j*x/p[0])
    errfunc = lambda p, x, y: abs( fitfunc(p,x) - y )
    p0=[1e6,1.]
    p1, succ = leastsq(errfunc, p0, args=(trans.values,array(trans.index,dtype=float)))
    figure()
    trans.abs().plot()
    plot(trans.index,abs(fitfunc(p1,trans.index)))
    return p1, succ

