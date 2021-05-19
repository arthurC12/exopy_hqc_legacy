# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2021 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""
This module defines drivers for agilent PXA.

:Contains:
    SpecDescriptor
    AgilentPXA

"""
from inspect import cleandoc
import numpy as np
from ..driver_tools import (InstrIOError, secure_communication,
                            instrument_property)
from ..visa_tools import VisaInstrument


DATA_FORMATTING_DICT = {'raw I/Q data': 0,
                        'descriptor': 1,
                        '(I,Q) vs time': 3,
                        'log(mag) vs freq': 4,
                        'average of log(mag) vs freq': 7,
                        'mag vs freq in Vrms': 11,
                        'average of mag vs freq in Vrms': 12}


class SpecDescriptor():
    def __init__(self):
        self.initialized = False
        self.FFTpeak = 0
        self.FFTfreq = 0
        self.FFTnbrSteps = 2
        self.Firstfreq = 0
        self.Freqstep = 0
        self.TimenbrSteps = 2
        self.firsttime = 0
        self.TimeStep = 0.1
        self.timedomaincheck = 1
        self.totaltime = 1.0
        self.averagenbr = 1


class AgilentPXA(VisaInstrument):
    """
    """
    caching_permissions = {'start_frequency_SA': False,
                           'stop_frequency_SA': False,
                           'mode': False}

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):
        super(AgilentPXA, self).__init__(connection_info,
                                         caching_allowed,
                                         caching_permissions,
                                         auto_open)
        self.mode = 'SA'

    @secure_communication(2)
    def get_spec_header(self):
        """
        """
        if self.mode == 'SPEC':
            answer = self.query_ascii_values("FETCH:SPEC1?")
            if answer:
                self.spec_header.initialized = True
                self.spec_header.FFTpeak = answer[0]
                self.spec_header.FFTfreq = answer[1]/1e9
                self.spec_header.FFTnbrSteps = answer[2]
                self.spec_header.Firstfreq = answer[3]/1e9
                self.spec_header.Freqstep = answer[4]/1e9
                self.spec_header.TimenbrSteps = answer[5]
                self.spec_header.firsttime = answer[6]
                self.spec_header.TimeStep = answer[7]
                self.spec_header.timedomaincheck = answer[8]
                self.spec_header.totaltime = answer[9]
                self.spec_header.averagenbr = answer[10]
            else:
                raise InstrIOError(cleandoc('''Agilent PXA did not return its
                        mode'''))
        else:
            raise '''PXA is not in Spectrum mode'''

    @secure_communication()
    def read_data(self, trace):
        """
        """
        # must be read in ASCii format
        self.write("FORM:DATA ASCii")
        # stop all the measurements
        self.write(":ABORT")
        # go to the "Single sweep" mode
        self.write(":INIT:CONT OFF")
        # initiate measurement
        self.write(":INIT")

        #
        self.query("SWEEP:TIME?")

        self.write("*WAI")  # SA waits until the averaging is done
        # Loop to see when the averaging is done
        while True:
            try:
                self.query("SWEEP:TIME?")
                break
            except:
                pass

        data = self.query_ascii_values('trace? trace{}'.format(trace))

        if data:
            freq = np.linspace(self.start_frequency_SA,
                               self.stop_frequency_SA,
                               self.sweep_points_SA)
            return np.rec.fromarrays([freq, np.array(data)],
                                         names=['Frequency',
                                                'Data'])
        else:
            raise InstrIOError(cleandoc('''Agilent PXA did not return the
                trace {} data'''.format(trace)))

    @instrument_property
    @secure_communication()
    def start_frequency_SA(self):
        """Start frequency getter method
        """

        if self.mode == 'SA':
            freq = self.query('FREQ:STAR?')
            if freq:
                return float(freq)/1e9
            else:
                raise InstrIOError(cleandoc('''Agilent PXA did not return the
                    start frequency'''))
        elif self.mode == 'SPEC':
            if not self.spec_header.initialized:
                self.get_spec_header()

            return self.spec_header.Firstfreq

        else:
            raise '''PXA is not in the appropriate mode to get correctly the
                    start frequency'''

    @start_frequency_SA.setter
    @secure_communication()
    def start_frequency_SA(self, value):
        """Start frequency setter method
        """
        if self.mode == 'SA':
            self.write('FREQ:STAR {} GHz'.format(value))
            result = self.query('FREQ:STAR?')
            if result:
                if abs(float(result)/1e9 - value)/value > 10**-12:
                    raise InstrIOError(cleandoc('''PXA did not set correctly
                    the start frequency'''))
            else:
                raise InstrIOError(cleandoc('''PXA did not set correctly the
                    start frequency'''))
        else:
            raise '''PXA is not in the appropriate mode to set correctly the
                    start frequency'''

    @instrument_property
    @secure_communication()
    def stop_frequency_SA(self):
        """Stop frequency getter method
        """
        if self.mode == 'SA':
            freq = self.query('FREQ:STOP?')
            if freq:
                return float(freq)/1e9
            else:
                raise InstrIOError(cleandoc('''Agilent PXA did not return the
                    stop frequency'''))

        else:
            raise '''PXA is not in the appropriate mode to get correctly the
                    stop frequency'''

    @stop_frequency_SA.setter
    @secure_communication()
    def stop_frequency_SA(self, value):
        """Stop frequency setter method
        """
        if self.mode == 'SA':
            self.write('FREQ:STOP {} GHz'.format(value))
            result = self.query('FREQ:STOP?')
            if result:
                if abs(float(result)/1e9 - value)/value > 10**-12:
                    raise InstrIOError(cleandoc('''PXA did not set correctly
                    the stop frequency'''))
            else:
                raise InstrIOError(cleandoc('''PXA did not set correctly the
                    stop frequency'''))
        else:
            raise '''PXA is not in the appropriate mode to set correctly the
                    stop frequency'''

    @instrument_property
    @secure_communication()
    def center_frequency(self):
        """Center frequency getter method
        """

        freq = self.query('FREQ:CENT?')
        if freq:
            return float(freq)/1e9
        else:
            raise InstrIOError(cleandoc('''Agilent PXA did not return the
                    center frequency'''))

    @center_frequency.setter
    @secure_communication()
    def center_frequency(self, value):
        """center frequency setter method
        """

        self.write('FREQ:CENT {} GHz'.format(value))
        result = self.query('FREQ:CENT?')
        if result:
            if abs(float(result)/1e9 - value)/value > 10**-12:
                raise InstrIOError(cleandoc('''PXA did not set correctly the
                    center frequency'''))
        else:
            raise InstrIOError(cleandoc('''PXA did not set correctly the
                    center frequency'''))

    @instrument_property
    @secure_communication()
    def span_frequency(self):
        """Span frequency getter method
        """

        if self.mode == 'SPEC':
            freq = self.query('SENS:SPEC:FREQ:SPAN?')
            if freq:
                return float(freq)/1e9
            else:
                raise InstrIOError(cleandoc('''Agilent PXA did not return the
                    span frequency'''))
        elif self.mode == 'SA':
            freq = self.query('FREQ:SPAN?')
            if freq:
                return float(freq)/1e9
            else:
                raise InstrIOError(cleandoc('''Agilent PXA did not return the
                    span frequency'''))

        else:
            raise '''PXA is not in the appropriate mode to get correctly the
                    span frequency'''

    @span_frequency.setter
    @secure_communication()
    def span_frequency(self, value):
        """span frequency setter method
        """
        if self.mode == 'SA':
            self.write('FREQ:SPAN {} GHz'.format(value))
            result = self.query('FREQ:SPAN?')
            if result:
                if abs(float(result)/1e9 - value)/value > 10**-12:
                    raise InstrIOError(cleandoc('''PXA did not set correctly
                    the span frequency'''))
            else:
                raise InstrIOError(cleandoc('''PXA did not set correctly the
                    span frequency'''))

        elif self.mode == 'SPEC':
            self.write('SENS:SPEC:FREQ:SPAN {} GHz'.format(value))
            result = self.query('SENS:SPEC:FREQ:SPAN?')
            if result:
                if abs(float(result)/1e9 - value)/value > 10**-12:
                    raise InstrIOError(cleandoc('''PXA did not set correctly
                    the span frequency'''))
            else:
                raise InstrIOError(cleandoc('''PXA did not set correctly the
                    span frequency'''))

        else:
            raise '''PXA is not in the appropriate mode to set correctly the
                    span frequency'''

    @instrument_property
    @secure_communication()
    def sweep_time(self):
        """Sweep time getter method
        """

        if self.mode == 'WAV':
            sweep = self.query('SENS:WAV:SWEEP:TIME?')
            if sweep:
                return float(sweep)
            else:
                raise InstrIOError(cleandoc('''Agilent PXA did not return the
                    sweep time'''))
        elif self.mode == 'SA':
            sweep = self.query('SWEEP:TIME?')
            if sweep:
                return float(sweep)
            else:
                raise InstrIOError(cleandoc('''Agilent PXA did not return the
                    sweep time'''))
        else:
            raise '''PXA is not in the appropriate mode to get correctly the
                    sweep time'''

    @sweep_time.setter
    @secure_communication()
    def sweep_time(self, value):
        """sweep time setter method
        """

        if self.mode == 'WAV':
            self.write('SENS:WAV:SWEEP:TIME {}'.format(value))
            result = self.query('SENS:WAV:SWEEP:TIME?')
            if result:
                if abs(float(result) - value)/value > 10**-12:
                    raise InstrIOError(cleandoc('''PXA did not set correctly
                    the sweep time'''))
            else:
                raise InstrIOError(cleandoc('''PXA did not set correctly the
                    sweep time'''))
        elif self.mode == 'SA':
            self.write('SWEEP:TIME {}'.format(value))
            result = self.query('SWEEP:TIME?')
            if result:
                if abs(float(result) - value)/value > 10**-12:
                    raise InstrIOError(cleandoc('''PXA did not set correctly
                    the sweep time'''))
            else:
                raise InstrIOError(cleandoc('''PXA did not set correctly the
                    sweep time'''))
        else:
            raise '''PXA is not in the appropriate mode to set correctly the
                    sweep time'''

    @instrument_property
    @secure_communication()
    def RBW(self):
        """
        """
        if self.mode == 'WAV':
            rbw = self.query('SENS:WAV:BWIDTH?')
            if rbw:
                return float(rbw)
            else:
                raise InstrIOError(cleandoc('''Agilent PXA did not return the
                    RBW'''))
        elif self.mode == 'SPEC':
            rbw = self.query('SENS:SPEC:BWIDTH?')
            if rbw:
                return float(rbw)
            else:
                raise InstrIOError(cleandoc('''Agilent PXA did not return the
                    RBW'''))
        else:
            rbw = self.query('BWIDTH?')
            if rbw:
                return float(rbw)
            else:
                raise InstrIOError(cleandoc('''Agilent PXA did not return the
                    channel Resolution bandwidth'''))

    @RBW.setter
    @secure_communication()
    def RBW(self, value):
        """
        """
        if self.mode == 'WAV':
            self.write('SENS:WAV:BWIDTH {}'.format(value))
            result = self.query('SENS:WAV:BWIDTH?')
            if result:
                if abs(float(result) - value) > 10**-12:
                    raise InstrIOError(cleandoc('''PXA did not set correctly
                    the channel Resolution bandwidth'''))
            else:
                raise InstrIOError(cleandoc('''PXA did not set correctly the
                    channel Resolution bandwidth'''))

        elif self.mode == 'SPEC':
            self.write('SENS:SPEC:BWIDTH {}'.format(value))
            result = self.query('SENS:SPEC:BWIDTH?')
            if result:
                if abs(float(result) - value) > 10**-12:
                    raise InstrIOError(cleandoc('''PXA did not set correctly
                    the channel Resolution bandwidth'''))
            else:
                raise InstrIOError(cleandoc('''PXA did not set correctly the
                    channel Resolution bandwidth'''))
        else:
            self.write('BAND {}'.format(value))
            result = self.query('BWIDTH?')
            if result:
                if abs(float(result) - value) > 10**-12:
                    raise InstrIOError(cleandoc('''PXA did not set correctly
                    the channel Resolution bandwidth'''))
            else:
                raise InstrIOError(cleandoc('''PXA did not set correctly the
                    channel Resolution bandwidth'''))

    @instrument_property
    @secure_communication()
    def VBW_SA(self):
        """
        """
        if self.mode == 'SA':

            vbw = self.query('BAND:VID?')
            if vbw:
                return float(vbw)
            else:
                raise InstrIOError(cleandoc('''Agilent PXA did not return the
                    channel Video bandwidth'''))
        else:
            raise '''PXA is not in the appropriate mode to set correctly the
                    sweep time'''

    @VBW_SA.setter
    @secure_communication()
    def VBW_SA(self, value):
        """
        """
        if self.mode == 'WAV':
            raise InstrIOError(cleandoc('''PXA did not set correctly the
                    channel Resolution bandwidth'''))
        elif self.mode == 'SPEC':
            raise InstrIOError(cleandoc('''PXA did not set correctly the
                    channel Resolution bandwidth'''))
        else:
            self.write('BAND:VID {}'.format(value))
            result = self.query('BAND:VID?')
            if result:
                if abs(float(result) - value) > 10**-12:
                    raise InstrIOError(cleandoc('''PXA did not set correctly
                    the channel Video bandwidth'''))
            else:
                raise InstrIOError(cleandoc('''PXA did not set correctly the
                    channel Video bandwidth'''))

    @instrument_property
    @secure_communication()
    def sweep_points_SA(self):
        """
        """
        points = self.query('SENSe:SWEep:POINts?')
        if points:
            return int(points)
        else:
            raise InstrIOError(cleandoc('''Agilent PXA did not return the
                    sweep point number'''))

    @sweep_points_SA.setter
    @secure_communication()
    def sweep_points_SA(self, value):
        """
        """
        self.write('SENSe:SWEep:POINts {}'.format(value))
        result = self.query('SENSe:SWEep:POINts?')
        if result:
            if int(result) != value:
                raise InstrIOError(cleandoc('''PXA did not set correctly the
                    sweep point number'''))
        else:
            raise InstrIOError(cleandoc('''PXA did not set correctly the
                    sweep point number'''))

    @instrument_property
    @secure_communication()
    def average_count_SA(self):
        """
        """
        count = self.query('AVERage:COUNt?')
        if count:
            return int(count)
        else:
            raise InstrIOError(cleandoc('''Agilent PXA did not return the
                     average count'''))

    @average_count_SA.setter
    @secure_communication()
    def average_count_SA(self, value):
        """
        """
        self.write('AVERage:COUNt {}'.format(value))
        result = self.query('AVERage:COUNt?')
        if result:
            if int(result) != value:
                raise InstrIOError(cleandoc('''PXA did not set correctly the
                     average count'''))
        else:
            raise InstrIOError(cleandoc('''PXA did not set correctly the
                     average count'''))

    @instrument_property
    @secure_communication()
    def average_state_SA(self):
        """
        """
        mode = self.query('AVERage?')
        if mode:
            return mode
        else:
            raise InstrIOError(cleandoc('''Agilent PXA did not return the
                    average state'''))

    @average_state_SA.setter
    @secure_communication()
    def average_state_SA(self, value):
        """
        """
        self.write('AVERage:STATE {}'.format(value))
        result = self.query('AVERage?')

        if result.lower() != value.lower()[:len(result)]:
            raise InstrIOError(cleandoc('''PXA did not set correctly the
                average state'''))