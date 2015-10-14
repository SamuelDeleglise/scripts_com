from pyinstruments.curvestore import models
from pandas import *
from scipy.optimize import curve_fit, leastsq
from numpy import array,where
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
    p1, succ = leastsq(errfunc, p0, args=(array(trans[f_min:f_max].index,dtype=float),trans[f_min:f_max].values))
    figure()
    trans.abs().plot()
    plot(trans.index,abs(fitfunc(p1,trans.index)))
    return p1, succ


def lorentz(x, scale, x0, bandwidth,y0):
    return scale/(1+((x-x0)/bandwidth)*((x-x0)/bandwidth))+y0

def guesslorentz(c):
        x0 = c.data.argmax()
        max = c.data.max()
        min = c.data.min()
        bw = x0-c.data.index[where(c.data.values>(max-min)/2.)[0][0]]
        return [(max-min), x0, bw, min]


def double_lorentz(x, s1, x01, b1, s2, x02, b2, y0):
    return lorentz(x, s1,x01,b1,0)+lorentz(x, s2,x02,b2,0)+y0

def guesslorentz_double(c):
        x0 = c.data.argmax()
        max = c.data.max()
        min = c.data.min()
        return [(max-min)/2., x0, (max-min)/2., x0, min]

def get_biref(c1_id, c2_id, cdbl_id):
    c_mod1=models.CurveDB.objects.get(id=c1_id)
    c_mod2=models.CurveDB.objects.get(id=c2_id)
    c_double=models.CurveDB.objects.get(id=cdbl_id)
    fitfunc_l = lambda p, x: p[0]/(1+((x-p[1])/p[2])*((x-p[1])/p[2]))+p[3] #lorentz(x, p[0],p[1],p[2],p[3])
    errfunc_l = lambda p, x, y: fitfunc_l(p,x) - y
    bws=[0.,0.]
    for c,i in zip((c_mod1, c_mod2),[0,1]):
        p0=guesslorentz(c)
        p1, succ = leastsq(errfunc_l, p0, args=(array(c.data.index,dtype=float),c.data.values))
        bws[i]=p1[2]
        figure()
        c.plot()
        plot(array(c.data.index,dtype=float),fitfunc_l(p1,array(c.data.index,dtype=float)))
    fitfunc_dl = lambda p, x: double_lorentz(x, p[0],p[1],bws[0], p[2], p[3], bws[1], p[4])
    errfunc_dl = lambda p, x, y: fitfunc_dl(p,x) - y
    p0=guesslorentz_double(c_double)
    p1, succ = leastsq(errfunc_dl, p0, args=(array(c_double.data.index,dtype=float),c_double.data.values))
    figure()
    c_double.plot()
    plot(array(c_double.data.index,dtype=float),fitfunc_dl(p1,array(c_double.data.index,dtype=float)))
    return (p1[1]-p1[3])/bws[0]
