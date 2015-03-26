from pyinstruments.curvestore import models
from pandas import *
from scipy.optimize import curve_fit

def get_bw_refl(c_id, cal_id, f_min=0., f_max=20e6):
    c_scan=models.CurveDB.objects.get(id=c_id)
    c_calib=models.CurveDB.objects.get(id=cal_id)
    relf=c_scan.data/c_calib.data
    bw=fit_refl( refl, f_min, f_max )


def fit_refl(data, f_min=0., f_max=20e6):
    parms, cov = curve_fit(fit_func_refl_int, data.index, data.data)
    return parms
    
def fit_func_refl(o, l, bw):
    bw=float(bw)
#l is (gamma-P)/gamma, bw is the bandwidth
    return (l+1j*o/bw)/(1-1j*o/bw) 