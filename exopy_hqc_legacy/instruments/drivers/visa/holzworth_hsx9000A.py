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
    Holzworth HSX9000 Channel
    Holzworth HSX9000
"""
from inspect import cleandoc
from ..driver_tools import (InstrIOError, secure_communication, instrument_property)
from ..visa_tools import VisaInstrument
from pyvisa import VisaTypeError


class Holzworth9000SingleChannel(VisaInstrument):
    """
    Generic driver for Holzworth HSX 900X SignalGenerator,
    using the VISA library.

    Parameters
    ----------
    see the `VisaInstrument` parameters

    Attributes
    ----------
    frequency_unit : str
        Frequency unit used by the driver. The default unit is 'GHz'. Other
        valid units are : 'MHz', 'KHz', 'Hz'
    """
    caching_permissions = {'defined_channels': True,
                           'trigger_scope': True,
                           'data_format': True}

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):
        super(Holzworth9000SingleChannel, self).__init__(connection_info, caching_allowed, caching_permissions, auto_open)
        self.frequency_unit = "GHz"
        self._channel = 1

    def open_connection(self, **para):
        """Open the connection to the instr using the `connection_str`.

        """
        super(Holzworth9000SingleChannel, self).open_connection(**para)
        self.write_termination = '\n'
        self.read_termination = '\n'
        # clearing buffers to avoid running into queue overflow
        self.write('*CLS')

    @secure_communication()
    def reset(self):
        """
        Reset the device
        """
        result = self.query('*RST')
        if not result:
            raise InstrIOError(cleandoc('''Holzworth HSX did not perform reset'''))            
    
    @instrument_property
    @secure_communication()
    def reference(self):
        """
        Query status of the reference
        """
        result = self.query(':REF:STATUS?')
        if result:
            return result
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not return reference status'''))
    
    @reference.setter
    @secure_communication()
    def reference(self, value):
        """
        Set the reference frequency
        ----------
        value : str
            possible values: EXT100, 100EXT, EXT10, 10EXT, INT100, 100INT, INT10, 10INT for 100/10 MHz external/internal

        Returns
        -------
        None.

        """
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
        """
        Query status of the PLL
        """
        result = self.query(':REF:PLL?')
        if result:
            return result
        raise InstrIOError(cleandoc('''Holzworth HSX did not return PLL status'''))

    @secure_communication
    def diag(self):
        """
        Run self-minidiagnostics
        """
        result = self.query(':HSX:DIAG:MIN:START')
        if result:
            return result
        raise InstrIOError(cleandoc('''Holzworth HSX did not run diagnostics'''))
    
    @secure_communication
    def status(self):
        """
        Returns status of self-minidiagnostics
        """

        result = self.query(':HSX:DIAG:DONE?')
        if result:
            return result
        raise InstrIOError(cleandoc('''Holzworth HSX did not return diagnostics status'''))

    @instrument_property
    @secure_communication
    def gpib(self):
        """
        Query Instrument GPIB Address
        """
        result = self.query('GPIB:ADDR?')
        if result:
            ''' expected: GPIB Address: N, 0 <= N <= 30'''
            try:
                addr = int(result.split(':')[1])
                return addr
            except ValueError:
                return result
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not return its GPIB address'''))

    @gpib.setter
    @secure_communication
    def gpib(self, addr):
        """
        Set Instrument GPIB Address
        """
        if type(addr) == int and (0 <= addr <= 30):
            self.write(':GPIB:ADDR:{}'.format(addr))
            result = self.query('GPIB:ADDR?')
            if result:
                ''' expected: GPIB Address: N'''
                try:
                    set_addr = int(result.split(':')[1])
                    if not set_addr == addr:
                        InstrIOError(cleandoc('''Holzworth HSX did not set its GPIB address correctly'''))
                except ValueError:
                    pass
            else:
                raise InstrIOError(cleandoc('''Holzworth HSX did not return its GPIB address'''))
        else:
            raise VisaTypeError(cleandoc('''Incorrect address given to Holzworth HSX'''))

    @instrument_property
    @secure_communication
    def gpib_respond(self):
        """
        Query Instrument GPIB respond
        """
        result = self.query('GPIB:RESPOND?')
        if result:
            return result
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not return GPIB respond status'''))

    @gpib_respond.setter
    @secure_communication
    def gpib_respond(self, value):
        """
        Set Instrument GPIB to always return a response
        """
        if value in ['ON', 'OFF', 'on', 'off']:
            result = self.query('GPIB:RESPOND:{}'.format(value))
            if not result:
                raise InstrIOError(cleandoc('''Holzworth HSX did not return GPIB respond status'''))
        else:
            raise VisaTypeError(cleandoc('''Incorrect response value given to Holzworth HSX'''))

    @instrument_property
    @secure_communication
    def gpib_eoiwlc(self):
        """
        Query Instrument GPIB EOI with last character
        """
        result = self.query(':GPIB:EOIWLC?')
        if result:
            return result
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not return GPIB End-Of-Input status'''))

    @gpib_eoiwlc.setter
    @secure_communication
    def gpib_eoiwlc(self, value):
        """
        Set Instrument GPIB EOI with last character
        """
        if value in ['ON', 'OFF', 'on', 'off']:
            result = self.query('GPIB:EOIWLC:{}'.format(value))
            if not result:
                raise InstrIOError(cleandoc('''Holzworth HSX did not return GPIB End-Of-Input status'''))
        else:
            raise VisaTypeError(cleandoc('''Incorrect response value given to Holzworth HSX'''))



    @instrument_property
    @secure_communication
    def comm_respond(self):
        """
        Query Ethernet, USB, and RS-232 response status
        """
        result = self.query('COMM:RESPOND?')
        if result:
            return result
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not return its respond status'''))

    @comm_respond.setter
    @secure_communication
    def comm_respond(self, value):
        """
        Set Ethernet, USB, and RS-232 response status
        """
        if type(value) == str:
            if value.upper in ['ON', 'OFF']:
                result = self.query('COMM:RESPOND:{}'.format(value.upper()))
                if not result:
                    raise InstrIOError(cleandoc('''Holzworth HSX did not return its respond status'''))
            else:
                raise VisaTypeError(cleandoc('''Incorrect response value given to Holzworth HSX'''))
        raise VisaTypeError(cleandoc('''Incorrect response value given to Holzworth HSX'''))

    @instrument_property
    @secure_communication
    def ip_address(self):
        """
        Query Instrument Static IP Address
        """
        result = self.query('IP:ADDR?')
        if result:
            return result
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not return its IP address'''))

    @ip_address.setter
    @secure_communication
    def ip_address(self, addr):
        """
        set instrument static IP address
        """
        if type(addr) == str:
            values = addr.split('.')
            if len(values) == 4:
                try:
                    values_num = [int(value) for value in values]
                except ValueError:
                    raise VisaTypeError(cleandoc('''Incorrect address given to Holzworth HSX'''))
                self.query('IP:ADDR:{}'.format(addr))

    @instrument_property
    @secure_communication
    def ip_gateway(self):
        """
        Query Instrument GAteway Address
        """
        result = self.query('IP:GATEWAY?')
        if result:
            return result
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not return its IP gateway'''))

    @ip_gateway.setter
    @secure_communication
    def ip_gateway(self, addr):
        """
        set instrument IP gateway
        """
        if type(addr) == str:
            values = addr.split('.')
            if len(values) == 4:
                try:
                    values_num = [int(value) for value in values]
                except ValueError:
                    raise VisaTypeError(cleandoc('''Incorrect gateway given to Holzworth HSX'''))
                self.query('IP:GATEWAY:{}'.format(addr))

    @instrument_property
    @secure_communication
    def ip_subnet(self):
        """
        Query Instrument Subnet mask Address
        """
        result = self.query('IP:SUBNET?')
        if result:
            return result
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not return its IP gateway'''))

    @ip_subnet.setter
    @secure_communication
    def ip_subnet(self, addr):
        """
        set instrument subnet mask address
        """
        if type(addr) == str:
            values = addr.split('.')
            if len(values) == 4:
                try:
                    values_num = [int(value) for value in values]
                except ValueError:
                    raise VisaTypeError(cleandoc('''Incorrect subnet mask given to Holzworth HSX'''))
                self.query('IP:SUBNET:{}'.format(addr))

    @instrument_property
    @secure_communication
    def ip_status(self):
        """
        Query Instrument IP Status
        """
        result = self.query('IP:STATUS?')
        if result:
            return result
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not return its IP status'''))

    @ip_status.setter
    @secure_communication
    def ip_status(self, value):
        """
        Toggle Instrument Static/Dynamic IP Address
        """
        if type(value) == str:
            if value.upper() in ['DHCP', 'STATIC']:
                self.query('IP:STATUS:{}'.format(value.upper()))
            else:
                raise VisaTypeError(cleandoc('''Incorrect IP address status given'''))
        else:
            raise VisaTypeError(cleandoc('''Incorrect IP address status given'''))

    @instrument_property
    @secure_communication
    def diag_info(self):
        """
        Query board information
        """
        result = self.query(':DIAG:INFO:BOARDS?')
        if result:
            return result
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not return Board information'''))

    @instrument_property
    @secure_communication()
    def mode(self):
        """
        Query the mode of the channel
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
        Set the operating mode the the channel
        """
        if mode.upper() in ['AUTO', 'HIGH', 'NORMAL', 'FIX']:
            result = self.query("CH{}:PWR:MODE:{}".format(self._channel, mode.upper()))
            if not result:
                raise InstrIOError(cleandoc('''Holzworth HXS did not set its mode correctly'''))
            return
        raise VisaTypeError(cleandoc('''Incorrect mode for Holzworth HSX'''))

    @instrument_property
    @secure_communication()
    def frequency(self):
        """
        Query Channel Output Frequency Setting
        TODO: to check an actual output string
        """
        result = self.query(':CH{}:FREQ?'.format(self._channel))
        if result:
            results = result.split(' ')  # <- to check if there is a space in the output string
            if len(results) == 2:
                value = float(results[0])
                suffix = results[1]
                if suffix == 'MHz':
                    value *= 1E6
                elif suffix == 'GHz':
                    value *= 1E9
                elif suffix == 'kHz':
                    value *= 1E3
                else:
                    raise InstrIOError(cleandoc('''Holzworth HSX did not return correctly the  output frequency'''))
            else:
                value = result
            return value
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not return correctly the output frequency'''))

    @frequency.setter
    @secure_communication()
    def frequency(self, value):
        """
        Set Channel Output Frequency
        """
        unit = self.frequency_unit
        if type(value) != str:
            value = '{}{}'.format(value,unit)
        else:
            if not value.endswith('Hz'):
                raise InstrIOError(cleandoc('''Incorrect frequency value is given. Allowed: number (in MHz) of string with *Hz suffix'''))
        self.write(':CH{}:FREQ:{}'.format(self._channel, value))
        result = self.query(':CH{}:FREQ?'.format(self._channel))
        if not result:
            raise InstrIOError(cleandoc('''Holzworth HSX did not set correctly the output frequency'''))

    @instrument_property
    @secure_communication()
    def min_frequency(self):
        """
        Query Minimum Channel Output Frequency
        """
        result = self.query(':CH{}:FREQ:MIN?'.format(self._channel))
        if result:
            value = float(result.split(' ')[0])
            suffix = result.split(' ')[1]
            if suffix == 'MHz':
                value *= 1E6
            elif suffix == 'GHz':
                value *= 1E9
            elif suffix == 'kHz':
                value *= 1E3
            return value
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not return correctly the
                     minimum  output frequency'''))

    @instrument_property
    @secure_communication()
    def max_frequency(self):
        """
        Query Maximum Channel Output Frequency
        """
        result = self.query(':CH{}:FREQ:MAX?'.format(self._channel))
        if result:
            value = float(result.split(' ')[0])
            suffix = result.split(' ')[1]
            if suffix == 'MHz':
                value *= 1E6
            elif suffix == 'GHz':
                value *= 1E9
            elif suffix == 'kHz':
                value *= 1E3
            return value
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not return correctly the
                     maximum  output frequency'''))

    @instrument_property
    @secure_communication()
    def power(self):
        """
        Query Channel Output Power Setting
        """
        result = self.query(':CH{}:PWR?'.format(self._channel))
        if result:
            return result
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not return correctly the output power'''))

    @power.setter
    @secure_communication()
    def power(self, power):
        """
        Set Channel Output Power
        """
        try:
            power = float(power)
            result = self.query(":CH{}:PWR:{}dBm".format(self._channel, power))
            if not result:
                raise InstrIOError(cleandoc('''Holzworth HSX did not set correctly the output power'''))
        except ValueError:
            raise VisaTypeError(cleandoc('''Incorrect power value given to device'''))

    @instrument_property
    @secure_communication()
    def phase(self):
        """
        Query Channel Output Phase Offset Setting
        """
        result = self.query(':CH{}:PHASE?'.format(self._channel))
        if result:
            try:
                value = float(result.split(' ')[0])
                return value
            except ValueError:
                return result
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not return correctly the output phase'''))

    @phase.setter
    @secure_communication()
    def phase(self, phase):
        """
        Set Channel Output Phase Offset
        """
        self.write(":CH{}:PHASE:{}".format(self._channel, phase))
        result = self.query(':CH{}:PHASE?'.format(self._channel))
        if not result:
            raise InstrIOError(cleandoc('''Holzworth HSX did not set correctly the output phase'''))

    @instrument_property
    @secure_communication
    def phase_max(self):
        """
        Query Channel Maximum Phase Offset Setting for Current Output Frequency
        """
        result = self.query(':CH{}:PHASE:MAX?'.format(self._channel))
        if result:
            try:
                value = float(result.split(' ')[0])
                return value
            except ValueError:
                return result
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not return correctly the output phase'''))

    @instrument_property
    @secure_communication
    def phase_resolution(self):
        """
        Query Channel Maximum Phase Offset Resolution Setting for Current Output Frequency
        """
        result = self.query(':CH{}:PHASE:RES?'.format(self._channel))
        if result:
            try:
                value = float(result.split(' ')[0])
                return value
            except ValueError:
                return result
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not return correctly the output phase'''))

    @secure_communication()
    def on(self):
        """
        Set Channel RF Output ON
        """
        result = self.query(":CH{}:PWR:RF:ON".format(self._channel))
        if not result:
            raise InstrIOError(cleandoc('''Holzworth HSX did not power on the output'''))

    @secure_communication()
    def off(self):
        """
        Set Channel RF Output OFF
        """
        result = self.query(":CH{}:PWR:RF:OFF".format(self._channel))
        if not result:
            raise InstrIOError(cleandoc('''Holzworth HSX did not power off the output'''))

    @instrument_property
    @secure_communication()
    def output(self):
        """
        Query Channel RF Output Status
        """
        result = self.query(":CH{}:PWR:RF?".format(self._channel))
        if result:
            return result
        else:
            raise InstrIOError(cleandoc('''Holzworth HSX did not return channel output status'''))

    @output.setter
    @secure_communication()
    def output(self, value):
        """
        Set Channel RF Output On/Off
        """
        if value.upper() in ['ON', 'OFF']:
            result = self.query(":CH{}:PWR:RF:{}".format(self._channel, value))
            if not result:
                raise InstrIOError(cleandoc('''Holzworth HSX did not power {} the output'''.format(value)))
        else:
            raise VisaTypeError(cleandoc('''Incorrect value given to device, allowed: ON, OFF'''))

    @instrument_property
    @secure_communication
    def temp(self):
        result = self.query(':CH{}:TEMP?'.format(self._channel))
        if result:
            return 'Channel #{} temperature: {}'.format(self._channel, result)
        else:
            raise InstrIOError(
                cleandoc('''Holzworth HSX did not return temperature of the channel #{}'''.format(self._channel)))
