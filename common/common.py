import pandas as pd
from curve import Curve

from numpy import array, float64

label_pha='A'
label_int='B'
label_cs='C'
label_iq='D'

def get_mmode_freq(curve_phase):
    return curve_phase.data.idxmax()

def convert_IQ(cs_IQ, spectrum, imped=50.):
    data = pd.Series(index=spectrum.data.index, data=array(cs_IQ.data.index, dtype=float64) + 1j*cs_IQ.data.values)
    data = data/imped/(cs_IQ.params["bandwidth"])*1e6#working in mJ with vsa software, plus an extra 1000 factor that comes from the software and thar i don't understand !
    c = Curve()
    c.set_params(**cs_IQ.params)
    c.set_data(data)
    return c

def test_mod_freq(freq, expc_freq):
    expr = ( (freq>(expc_freq.params["bandwidth"]+expc_freq.params["mod"])) or (freq<(-expc_freq.params["bandwidth"]+expc_freq.params["mod"])) )
    return not expr

