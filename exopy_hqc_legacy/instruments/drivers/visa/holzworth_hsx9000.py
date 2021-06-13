# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2021 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""
This module defines drivers for Holzworth HSX 9000 RF synthesizer.
:Contains:
    SpecDescriptor
    Holzworth HSX9000
"""
from inspect import cleandoc
import numpy as np
from ..driver_tools import (InstrIOError, secure_communication, instrument_property)
from ..visa_tools import VisaInstrument, BaseInstrument


'''
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
'''

class HolzworthHSX9000Channel(BaseInstrument):
    """
    """
    caching_permissions = {'start_frequency_SA': False,
                           'stop_frequency_SA': False,
                           'mode': False}

    def __init__(self, channel, connection_info, caching_allowed=True, caching_permissions={}, auto_open=True):
        super(HolzworthHSX9000Channel, self).__init__(connection_info, caching_allowed, caching_permissions, auto_open)
        self._channel = channel
        #self.spec_header = SpecDescriptor()

    @secure_communication(2)
    def get_spec_header(self):
        pass
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
                raise InstrIOError(cleandoc('''Holzworth HXS did not return its
                        mode'''))
        else:
            raise '''Holzworth HSX is not in Spectrum mode'''
        """

    @instrument_property
    @secure_communication()
    def mode(self):
        """
        """
        result = self.query("CH{}:PWR:MODE?".format(self._channel))
        if result:
            return result
        else:
            raise InstrIOError(cleandoc('''Holzworth HXS did not return its mode'''))

    @mode.setter
    @secure_communication()
    def mode(self, mode):
        """
        """
        if mode in ['AUTO', 'HIGH', 'NORMAL', 'FIX']:
            result = self.query("CH{}:PWR:MODE:{}".format(self._channel, mode))
            if not result:
                raise InstrIOError(cleandoc('''Holzworth HXS did not set its mode correctly'''))
            return
        raise InstrIOError(cleandoc('''Incorrect mode for Holzworth HXS'''))

    @instrument_property
    @secure_communication()
    def frequency(self):
        result = self.query(':CH{}:FREQ?'.format(self._channel))
        if result:
            value = float(result.split(' ')[0])
            suffix = result.split[1]
            if suffix == 'MHz':
                value *= 1E6
            elif suffix == 'GHz':
                value *= 1E9
            else:
                raise InstrIOError(cleandoc('''Holzworth HSX did not return correctly the
                     output frequency'''))
            return value
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not return correctly the
                     output frequency'''))

    @frequency.setter
    @secure_communication()
    def frequency(self, value):
        '''
        Set Channel Output Frequency
        '''
        if type(value) != str:
            value = '{}MHz'.format(value/10**6)
        else:
            if value.endswith('Hz'):
                pass
            else:
                raise InstrIOError(cleandoc('''Incorrect frequency value is given. Allowed: number (in MHz) of string with *Hz suffix'''))
        self.write(':CH{}:FREQ:{}'.format(self._channel, value))
        result = self.query(':CH{}:FREQ?'.format(self._channel))
        if not result:
            raise InstrIOError(cleandoc('''Holzworth HSX did not set correctly the output frequency'''))

    @instrument_property
    @secure_communication()
    def min_frequency(self):
        result = self.query(':CH{}:FREQ:MIN?'.format(self._channel))
        if result:
            value = float(result.split(' ')[0])
            suffix = result.split[1]
            if suffix == 'MHz':
                value *= 1E6
            elif suffix == 'GHz':
                value *= 1E9
            else:
                raise InstrIOError(cleandoc('''Holzworth HSX did not return correctly the
                     minimum  output frequency'''))
            return value
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not return correctly the
                     minimum  output frequency'''))

    @instrument_property
    @secure_communication()
    def max_frequency(self):
        result = self.query(':CH{}:FREQ:MAX?'.format(self._channel))
        if result:
            value = float(result.split(' ')[0])
            suffix = result.split[1]
            if suffix == 'MHz':
                value *= 1E6
            elif suffix == 'GHz':
                value *= 1E9
            else:
                raise InstrIOError(cleandoc('''Holzworth HSX did not return correctly the
                     maximum  output frequency'''))
            return value
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not return correctly the
                     maximum  output frequency'''))

    @instrument_property
    @secure_communication()
    def power(self):
        result = self.query(':CH{}:PWR?'.format(self._channel))
        if result:
            return result
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not return correctly the output power'''))

    @power.setter
    @secure_communication()
    def power(self, power):
        result = self.write(":CH{}:PWR:{}dBm".format(self._channel, power))
        if not result:
            raise InstrIOError(cleandoc('''Holzworth HSX did not set correctly the output power'''))

    @instrument_property
    @secure_communication()
    def phase(self):
        result = self.query(':CH{}:PHASE?'.format(self._channel))
        if result:
            return result
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not return correctly the output phase'''))

    @phase.setter
    @secure_communication()
    def phase(self, phase):
        self.write(":CH{}:PHASE:{}".format(self._channel, phase))
        result = self.query(':CH{}:PHASE?'.format(self._channel))
        if not result:
            raise InstrIOError(cleandoc('''Holzworth HSX did not set correctly the output phase'''))

    @instrument_property
    @secure_communication
    def phase_max(self):
        result = self.query(':CH{}:PHASE:MAX?'.format(self._channel))
        if result:
            return result
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not return correctly the output phase'''))

    @instrument_property
    @secure_communication
    def phase_resolution(self):
        result = self.query(':CH{}:PHASE:RES?'.format(self._channel))
        if result:
            return result
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not return correctly the output phase'''))

    @secure_communication()
    def on(self):
        result = self.write(":CH{}:PWR:RF:ON".format(self._channel))
        if not result:
            raise InstrIOError(cleandoc('''Holzworth HSX did not powered on the output'''))

    @secure_communication()
    def off(self):
        result = self.write(":CH{}:PWR:RF:OFF".format(self._channel))
        if not result:
            raise InstrIOError(cleandoc('''Holzworth HSX did not powered on the output'''))

    @instrument_property
    @secure_communication()
    def output_status(self):
        result = self.write(":CH{}:PWR:RF?".format(self._channel))
        if result:
            return result == 'ON'
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not powered on the output'''))
    
    
    @instrument_property
    @secure_communication
    def temp(self):
        result = self.query(':CH{}:TEMP?'.format(self._channel))
        if result:
            return 'Channel #{} temperature: {}'.format(self._channel, result)
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not return temperature of the channel #{}'''.format(self._channel)))   

class Holzworth9000(VisaInstrument):
    """
    """

    caching_permissions = {'defined_channels': True,
                           'trigger_scope': True,
                           'data_format': True}

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):
        super(Holzworth9000, self).__init__(connection_info, caching_allowed, caching_permissions, auto_open)
        self.num_channels = 0
        self.defined_channels = None
        self.channels = {}

    def open_connection(self, **para):
        """Open the connection to the instr using the `connection_str`.

        """
        super(Holzworth9000, self).open_connection(**para)
        self.write_termination = '\n'
        self.read_termination = '\n'
        # clearing buffers to avoid running into queue overflow
        self.write('*CLS')
        '''
        defining number of channels of the HSX
        *IDN? returns 'Holzworth Instrumentation, HSX9004A, '
        HSX9001 -> 1 channel
        HSX9002 -> 2 channels
        HSX9003 -> 3 channels
        HSX9004 -> 4 channels
        '''
        result = self.query('*IDN?')
        if result:
            hsx = result.find('HSX')
            if hsx != -1:
                try:
                    model = int(result[hsx+3 : hsx+7])
                except ValueError:
                    raise InstrIOError(cleandoc('''Holzworth HSX did not result the model name'''))
                num_channels = model % 10
                self.defined_channels = list(range(1, num_channels + 1))
            else:
                raise InstrIOError(cleandoc('''Holzworth HSX did not result the model name'''))
        raise InstrIOError(cleandoc('''Holzworth HSX did not respond'''))
    
    def get_channel(self, num):
        if num not in self.defined_channels:
            return None
        if num in self.channels:
            return self.channels[num]
        else:
            channel = HolzworthHSX9000Channel(self, num)
            self.channels[num] = channel
            return channel
    
    
    @secure_communication()    
    def reset(self):
        result = self.query('*RST')
        if not result:
            raise InstrIOError(cleandoc('''Holzworth HSX did not perform reset'''))            
    
    @instrument_property
    @secure_communication()
    def reference(self):
        result = self.query(':REF:STATUS?')
        if result:
            return result
        else:
             raise InstrIOError(cleandoc('''Holzworth HSX did not return reference status'''))            
    
    @reference.setter
    @secure_communication()
    def reference(self, value):
        '''
        Set the reference frequency
        ----------
        value : str
            possible values: EXT100, 100EXT, EXT10, 10EXT, INT100, 100INT, INT10, 10INT for 100/10 MHz external/internal

        Returns
        -------
        None.

        '''
        values = {'100EXT': 'EXT:100MHz',
                  '100INT': 'INT:100MHz',
                  '10EXT': 'EXT:10MHz',
                  '10INT': 'INT:10MHz',
                  'EXT100': 'EXT:100MHz',
                  'INT100': 'INT:100MHz',
                  'EXT10': 'EXT:10MHz',
                  '10INT10': 'INT:10MHz'}
        if value in values.keys():
            result = self.query (':REF:{}'.format(values[value]))
            if not result:
                raise InstrIOError(cleandoc('''Holzworth HSX did not set reference'''))
        else:
            raise InstrIOError(cleandoc('''Incorrect reference specified, \
                                        allowed values EXT100, 100EXT, EXT10, 10EXT, INT100, 100INT, INT10, 10INT'''))
                                        
    
    @instrument_property
    @secure_communication()
    def pll(self):
        result = self.query(':REF:PLL?')
        if result:
            return result
        raise InstrIOError(cleandoc('''Holzworth HSX did not return PLL status'''))
        
        
    @instrument_property
    @secure_communication
    def temp(self):
        result = self.query(':TEMP?')
        if result:
            return result
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not return temperature'''))   
            
    @secure_communication
    def diag(self):
        result = self.query(':HSX:DIAG:MIN:START')
        if result:
            return result
        raise InstrIOError(cleandoc('''Holzworth HSX did not run diagnostics'''))
    
    @secure_communication
    def status(self):
        result = self.query(':HSX:DIAG:DONE?')
        if result:
            return result
        raise InstrIOError(cleandoc('''Holzworth HSX did not return diagnostics status'''))    