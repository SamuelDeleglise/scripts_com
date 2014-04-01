import pandas as pd
import numpy as np
from pyinstruments.curvestore import models
import gc
import math
from matplotlib.pyplot import figure
from curve import Curve

label_phase='A'
label_int='B'
label_cs='C'
label_IQ='D'
	

class Run:
	def __init__(self,idmin, idmax):
		runs=range(idmin,idmax+1)
		curves = models.CurveDB.objects.filter_tag("runCOM").filter_param("id", value__in=runs)
		self.curves_pha = curves.filter_param("trace_label",value='A')
		self.curves_int = curves.filter_param("trace_label",value='B')
		self.curves_cs = curves.filter_param("trace_label",value='C')
		self.curves_cs_lock_re = curves.filter_param("trace_label",value='G')
		self.curves_cs_lock_im = curves.filter_param("trace_label",value='H')

def conv_cs(Run, exclude=None):
	mean_cs=[]
	rms_cs=[]
	m=mask(Run.curves_pha[0], exclude)
	for c in Run.curves_cs:
		mean=c.data[m].mean()
		rms=c.params["current_average"]
		mean_cs.append(mean)
		rms_cs.append(rms)
	data=pd.Series(mean_cs,index=rms_cs)
	return data

def conv_lock(Run):
	lock_point_re=[]
	lock_point_im=[]
	rms_cs_re=[]
	rms_cs_im=[]
	angles=[]
	for c in Run.curves_cs_lock_re:
		re=c.data[(c.data.size-1)/2]
		rms=c.params["current_average"]
		lock_point_re.append(re)
		rms_cs_re.append(rms)
		angles.append(float(c.params["angle"]))
	lock_re=pd.Series(lock_point_re,index=rms_cs_re)
	angles=pd.Series(angles,index=rms_cs_re)
	for c in Run.curves_cs_lock_im:
		im=c.data[(c.data.size-1)/2]
		rms=c.params["current_average"]
		lock_point_im.append(im)
		rms_cs_im.append(rms)
	lock_im=pd.Series(lock_point_im,index=rms_cs_im)
	lock=np.cos(np.radians(angles))*lock_re+np.sin(np.radians(angles))*lock_im
	return lock

def conv_cor(Run, exclude=None):
	mean_cs=[]
	mean_pha=[]
	mean_int=[]
	rms=[]
	m=mask(Run.curves_pha[0], exclude)
	for c in Run.curves_cs:
		cs=c.data[m].mean()
		cur_rms=c.params["current_average"]
		mean_cs.append(cs)
		rms.append(cur_rms)
	data_cs=pd.Series(mean_cs,index=rms)
	rms=[]
	for c in Run.curves_pha:
		pha=c.data[m].mean()
		cur_rms=c.params["current_average"]
		mean_pha.append(pha)
		rms.append(cur_rms)
	data_pha=pd.Series(mean_pha,index=rms)
	rms=[]
	for c in Run.curves_int:
		int=c.data[m].mean()
		cur_rms=c.params["current_average"]
		mean_int.append(int)
		rms.append(cur_rms)
	data_int=pd.Series(mean_int,index=rms)
	data=data_cs/np.sqrt(data_pha*data_int)
	return data

def conv_cor_IQ(Run, exclude=None):
	mean_cs=[]
	mean_pha=[]
	mean_int=[]
	rms=[]
	m=mask(Run.curves_pha[0], exclude)
	for c in Run.curves_cs:
		cs=c.data[m].mean()
		cur_rms=c.params["current_average"]
		mean_cs.append(cs)
		rms.append(cur_rms)
	data_cs=pd.Series(mean_cs,index=rms)
	rms=[]
	for c in Run.curves_pha:
		pha=c.data[m].mean()
		cur_rms=c.params["current_average"]
		mean_pha.append(pha)
		rms.append(cur_rms)
	data_pha=pd.Series(mean_pha,index=rms)
	rms=[]
	for c in Run.curves_int:
		int=c.data[m].mean()
		cur_rms=c.params["current_average"]
		mean_int.append(int)
		rms.append(cur_rms)
	data_int=pd.Series(mean_int,index=rms)
	data=data_cs/np.sqrt(data_pha*data_int)
	return data

def conv_cor_huge(idmin, idmax,exclude=None):
	runs=range(idmin,idmax+1)
	curves = models.CurveDB.objects.filter_tag("runCOM").filter_param("id", value__in=runs)
	curves_pha = curves.filter_param("trace_label",value='A')
	del curves
	m=mask(curves_pha[0], exclude)
	gc.collect()
	mean_cs=[]
	mean_pha=[]
	mean_int=[]
	rms=[]
	for c in curves_pha:
		pha=c.data[m].mean()
		cur_rms=c.params["current_average"]
		mean_pha.append(pha)
		rms.append(cur_rms)
	data_pha=pd.Series(mean_pha,index=rms)
	data_pha.sort_index()
	rms=[]
	del curves_pha
	del mean_pha
	gc.collect()
	curves = models.CurveDB.objects.filter_tag("runCOM").filter_param("id", value__in=runs)
	curves_int = curves.filter_param("trace_label",value='B')
	del curves
	gc.collect()
	for c in curves_int:
		inte=c.data[m].mean()
		cur_rms=c.params["current_average"]
		mean_int.append(inte)
		rms.append(cur_rms)
	data_int=pd.Series(mean_int,index=rms)
	data_int.sort_index()
	rms=[]
	del curves_int
	del mean_int
	gc.collect()
	prod=data_pha*data_int
	del data_pha
	del data_int
	gc.collect()
	prod=np.sqrt(prod)
	curves = models.CurveDB.objects.filter_tag("runCOM").filter_param("id", value__in=runs)
	curves_cs = curves.filter_param("trace_label",value='C')
	del curves
	gc.collect()
	for c in curves_cs:
		cs=c.data[m].mean()
		cur_rms=c.params["current_average"]
		mean_cs.append(cs)
		rms.append(cur_rms)
	data_cs=pd.Series(mean_cs,index=rms)
	del rms
	del mean_cs
	gc.collect()
	return data_cs/prod

def convert_IQ(cs_IQ, spectrum, imped=50.):
	data=pd.Series(index = spectrum.data.index, data = cs_IQ.data.index+1j*cs_IQ.data.values)
	c = Curve()
	c.set_params(**cs_IQ.params)
	data=data/imped*(c.params["bandwidth"])**2
	c.set_data(data)
	return c

def mask(c, exclude):
	exclude_points = lambda c,min_freq,max_freq: (c.data.index<min_freq) | (c.data.index>max_freq)
	mask=pd.Series(True,index=c.data.index)
	if exclude is not None:
		for freqs in exclude:
			mask = exclude_points(c,freqs[0],freqs[1])*mask
	return mask

def full_analysis(Run, exclude=None):
	cor = conv_cor(Run,exclude)
	f_cor=figure("Correlations")
	cor.plot()
	cs = conv_cs(Run,exclude)
	f_cs=figure("Cross Spectrum")
	cs.plot()
	lock = conv_lock(Run)
	f_lock=figure("Lock")
	lock.plot()
