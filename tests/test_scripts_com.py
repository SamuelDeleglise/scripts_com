from unittest import TestCase
import unittest

import numpy

from pyinstruments.pyhardwaredb import instrument
vsa = instrument("vsa")

from scripts_com.analysis import convert_IQ
from scripts_com.common import *

class TestCrossSpectrum(TestCase):

    def setUp(self):
        vsa.active_label = label_IQ
        self.c_IQ = vsa.get_curve()
        vsa.active_label = label_cs
        self.c_cs = vsa.get_curve()

    def test_len(self):
        self.assertTrue(self.c_IQ.data.size == self.c_cs.data.size)
        
    def test_values(self):
        c_cs_IQ = convert_IQ(self.c_IQ,self.c_cs)
        self.assertTrue( c_cs_IQ.data.abs().all() == self.c_cs.data.all() )
    
class TestLock(TestCase):

    def setUp(self):
        vsa.active_label = label_pha
        self.c_phase = vsa.get_curve()
        vsa.active_label = label_int
        self.c_int = vsa.get_curve()
        self.freq=get_mmode_freq(self.c_phase)
    
    def test_freq(self):
        freq=get_mmode_freq(self.c_phase)
        self.assertTrue( (self.freq < 1.129e6) and (self.freq > 1.128e6) )

    def test_int(self):
        self.assertTrue( type(self.c_int.data.get(self.freq)) is numpy.float64 )
        

if __name__ == '__main__':
    unittest.main()