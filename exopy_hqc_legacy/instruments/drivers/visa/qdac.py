# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy HqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Drivers for the QDevil QDAC using VISA library.

"""
from inspect import cleandoc

from pyvisa.errors import InvalidSession, VisaIOError

from ..driver_tools import (BaseInstrument, InstrIOError, secure_communication,
                            instrument_property)
from ..visa_tools import VisaInstrument

import serial
import pyvisa


class QDacChannel(BaseInstrument):

    secure_com_except = (InvalidSession, InstrIOError, VisaIOError)

    def __init__(self, QDac, channel_num, caching_allowed=True,
                 caching_permissions={}):
        super().__init__(None, caching_allowed, caching_permissions)
        self._QDac = QDac
        self._channel = channel_num
        self._voltage_range = 10.0  # 10 Volts by default
        self._current_range = 100E-6  # 100 microAmps by default
        self.verbose = True
        
    def reopen_connection(self, *args, **kwargs):
        self._QDac.reopen_connection(*args, **kwargs)

    @instrument_property
    @secure_communication()
    def voltage(self):
        """output value getter method
        """
        _query = "set {}".format(self._channel)
        response = QDac.check_for_error(self._QDac.query(_query))
        if self.verbose:
            # response = ‘Output: <voltage> to Channel: <channel>\n’
            try:
                value = float(response.split(' ')[-1].strip())
            except ValueError:
                value = response
        else:
            # response = '<voltage>\n’
            try:
                value = float(response.strip())
            except ValueError:
                value = response
        return value

    @voltage.setter
    @secure_communication()
    def voltage(self, value):
        """Output value setter method
        """
        _query = "set {} {}".format(self._channel, value)
        QDac.check_for_error(self._QDac.query(_query))

    def read_voltage_dc(self):
        return self.voltage

    @secure_communication()
    def read_current_dc(self):
        """output value getter method
        """
        _query = "get {}".format(self._channel)
        response = QDac.check_for_error(self._QDac.query(_query))
        if self.verbose:
            # response = 'Channel <channel> current: <current> uA\n' (verbose on)
            value = float(response.split(':')[1].strip().split(' ')[0])
        else:
            # response = ‘<current>\n’ (
            value = float(response.strip())
        return value*1E-6

    @instrument_property
    def current(self):
        return self.read_current_dc()

    @instrument_property
    @secure_communication()
    def voltage_range(self):
        """
        Get voltage range for the specific channel. 0 = +/- 10V, 1 = +/- 1.1 V
        """
        _query = "vol {}".format(self._channel)
        response = QDac.check_for_error(self._QDac.query(_query))
        if self.verbose:
            # Response = 'Voltage range on Channel <channel> set to: <range>\n’, <range> = {'x1', 'x0.1'}
            value = int(response.split('x')[1][0])
            if value == 1:
                return 10
            else:
                return 1.1
        else:
            value = int(response)
            if response == 0:
                return 10
            else:
                return 1.1

    @voltage_range.setter
    @secure_communication()
    def voltage_range(self, value):
        """
        Set voltage range for the specific channel, possible values = {10 V = 0, 1.1 V = 1}
        """
        if value == 10:
            value = 0
        else:
            value = 1
        _query = "vol {} {}".format(self._channel, value)
        QDac.check_for_error(self._QDac.query(_query))

    @instrument_property
    @secure_communication()
    def current_range(self):
        """
        Get voltage range for the specific channel. 0 => 1 uA, 1 => 100 mA
        """
        _query = "cur {}".format(self._channel)
        response = QDac.check_for_error(self._QDac.query(_query))
        if self.verbose:
            # response = 'Current range on Channel <channel> set to: <range>\n’, <range> = 'Low', 'High'
            value = response.split(':')[1].strip()
            if value == "Low":
                return 1E-6
            else:
                return 1E-4
        else:
            # response = '0', '1'
            if response == '0':
                return 1E-6
            else:
                return 1E-4

    @current_range.setter
    @secure_communication()
    def current_range(self, value):
        """
        Set voltage range for the specific channel, possible values = {1 uA => 0, 100 uA => 1}
        """
        if value == 1:
            value = 0
        else:
            value = 1
        _query = "cur {} {}".format(self._channel, value)
        QDac.check_for_error(self._QDac.query(_query))


class QDac(VisaInstrument):
    """
    """
    caching_permissions = {'defined_channels': True}
    secure_com_except = (InvalidSession, InstrIOError, VisaIOError)

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):
        self.baud_rate = 460800
        self.verbose = True
        self.resource_name = connection_info['resource_name']
        rm = pyvisa.ResourceManager()
        self.port_name = rm.list_resources_info()[self.resource_name].alias
        
        super().__init__(connection_info, caching_allowed,
                                       caching_permissions, auto_open)
        self.channels = {}
        self.defined_channels = list(range(1, 25))

    def open_connection(self, **para):
        """Open the connection to the instr using the `connection_str`
        """
        self.port = serial.Serial(self.port_name, self.baud_rate)
        # \r termination for the serial communication
        
    def close_connection(self):
        self.port.close()
        super().close_connection()
        
    def get_channel(self, num):
        """num is a tuple containing (module_number,channel_number)
        """
        defined = self.defined_channels
        if num not in defined:
            msg = 'No channel {}, only channels {} exist'
            raise KeyError(msg.format(num, defined))

        if num in self.channels:
            return self.channels[num]
        else:
            channel = QDacChannel(self, num)
            print("Channel #{} created".format(num))
            self.channels[num] = channel
            return self.channels[num]

    @instrument_property
    def serial_number(self):
        _query = b"sernum"
        response = QDac.check_for_error(_query)
        return response

    def query(self, message, *args, **kwargs):
        """
        For debug purposes only; to be removed
        """
        self.port.write("{}\n".format(message).encode())
        return self.port.readline()
        #print(message)
        #return super(QDac, self).query(message, *args, **kwargs)
    
    
    @staticmethod
    def check_for_error(msg):
        """
        Error handling
        """
        if msg[:5] == b"Error":
            raise InstrIOError(cleandoc('''QDAc communication error'''))
        else:
            try:
                return msg.decode("utf-8")
            except AttributeError:
                raise InstrIOError(cleandoc("Error response from QDAC: <{}>".format(msg)))

class QDac_(VisaInstrument):
    """
    """
    caching_permissions = {'defined_channels': True}
    secure_com_except = (InvalidSession, InstrIOError, VisaIOError)

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):
        super().__init__(connection_info, caching_allowed,
                                       caching_permissions, auto_open)
        self.baud_rate = 460800
        self.query_delay = 0.5
        self.channels = {}
        self.defined_channels = list(range(1, 25))

    def open_connection(self, **para):
        """Open the connection to the instr using the `connection_str`
        """
        super().open_connection(**para)
        # \r termination for the serial communication
        self.write_termination = '\n'
        self.read_termination = ''

    def get_channel(self, num):
        """num is a tuple containing (module_number,channel_number)
        """
        defined = self.defined_channels
        if num not in defined:
            msg = 'No channel {}, only channels {} exist'
            raise KeyError(msg.format(num, defined))

        if num in self.channels:
            return self.channels[num]
        else:
            channel = QDacChannel(self, num)
            print("Channel #{} created".format(num))
            self.channels[num] = channel
            return self.channels[num]

    @instrument_property
    def serial_number(self):
        _query = b"sernum"
        response = QDac.check_for_error(_query)
        return response

    '''    
    def query(self, message, *args, **kwargs):
        """
        For debug purposes only; to be removed
        """
        print(message)
        return super().query('{}\n'.format(message), *args, **kwargs)
        #return super().query("\n")
    '''
    
    @staticmethod
    def check_for_error(msg):
        """
        Error handling
        """
        if msg[:5] == b"Error":
            raise InstrIOError(cleandoc('''QDAc communication error'''))
        else:
            try:
                return msg.decode("utf-8")
            except AttributeError:
                raise InstrIOError(cleandoc("Error response from QDAC: <{}>".format(msg)))
                
class QDacSingleChannel_(VisaInstrument):
    """
    """

    caching_permissions = {'defined_channels': True}
    secure_com_except = (InvalidSession, InstrIOError, VisaIOError)

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):
        super(QDacSingleChannel, self).__init__(connection_info, caching_allowed,
                                       caching_permissions, auto_open)
        self.baud_rate = 460800
        self._channel = 1
        self.verbose = False
        
    def open_connection(self, **para):
        """Open the connection to the instr using the `connection_str`
        """
        para['data_bits'] = serial.EIGHTBITS
        #para['parity'] = serial.PARITY_NONE
        #para['stop_bits'] = serial.STOPBITS_ONE
        #para['timeout'] = 0.5
        super(QDacSingleChannel, self).open_connection(**para)
        # \r termination for the serial communication
        self.write_termination = ''
        self.read_termination = ''

    
    @instrument_property
    @secure_communication()
    def voltage(self):
        """output value getter method
        """
        return self.read_voltage_dc()
        """
        _query = "set {}".format(self._channel)
        response = self.check_for_error(self.query(_query))
        if self.verbose:
            # response = ‘Output: <voltage> to Channel: <channel>\n’
            try:
                value = float(response.split("Output:")[1].split("(")[0].strip(" "))
            except ValueError:
                value = 1.2345
        else:
            # response = '<voltage>\n’
            try:
                value = float(response.strip())
            except ValueError:
                value = 0.9876
        return value
        """
        
    @secure_communication()
    def read_voltage_dc(self):
        """output value getter method
        """
        _query = "set {}\n".format(self._channel)
        response = self.check_for_error(self.query(_query))
                
        if self.verbose:
            # response = ‘Output: <voltage> to Channel: <channel>\n’
            try:
                value = float(response.split("Output:")[1].split("(")[0].strip(" "))
            except ValueError:
                value = 1.2345
        else:
            # response = '<voltage>\n’
            try:
                value = float(response.strip())
            except ValueError:
                value = 0.9876
        return value
    
    @secure_communication()
    @voltage.setter
    def voltage(self, value):
        """Output value setter method
        """
        _query = "set {} {}\n".format(self._channel, value)
        #self.check_for_error(self.query(_query))
        self.check_for_error(self.query(_query))

    @secure_communication()
    def read_current_dc(self):
        """output value getter method
        """
        _query = "get {}\n".format(self._channel)
        response = self.check_for_error(self.query(_query))
        if self.verbose:
            # response = 'Channel <channel> current: <current> uA\n' (verbose on)
            value = float(response.split(":", 1)[1][:-2])
        else:
            # response = ‘<current>\n’ (
            value = float(response.strip())
        return value * 1E-6

    @instrument_property
    def current(self):
        return self.read_current_dc()

    @instrument_property
    @secure_communication()
    def voltage_range(self):
        """
        Get voltage range for the specific channel. 0 = +/- 10V, 1 = +/- 1.1 V
        """
        _query = "vol {}\n".format(self._channel)
        response = self.check_for_error(self.query(_query))
        if self.verbose:
            # Response = 'Voltage range on Channel <channel> set to: <range>\n’, <range> = {'x1', 'x0.1'}
            value = int(response.split('x')[1][0])
            if value == 1:
                return 10
            else:
                return 1.1
        else:
            value = int(response)
            if response == 0:
                return 10
            else:
                return 1.1

    @voltage_range.setter
    @secure_communication()
    def voltage_range(self, value):
        """
        Set voltage range for the specific channel, possible values = {10 V = 0, 1.1 V = 1}
        """
        if value == 10:
            value = 0
        else:
            value = 1
        _query = "vol {} {}\n".format(self._channel, value)
        self.check_for_error(self.query(_query))

    @instrument_property
    @secure_communication()
    def current_range(self):
        """
        Get voltage range for the specific channel. 0 => 1 uA, 1 => 100 mA
        """
        _query = "cur {}\n".format(self._channel)
        response = self.check_for_error(self.query(_query))
        if self.verbose:
            # response = 'Current range on Channel <channel> set to: <range>\n’, <range> = 'Low', 'High'
            value = response.split(':')[1].strip()
            if value == "Low":
                return 1E-6
            else:
                return 1E-4
        else:
            # response = '0', '1'
            if response == '0':
                return 1E-6
            else:
                return 1E-4

    @current_range.setter
    @secure_communication()
    def current_range(self, value):
        """
        Set voltage range for the specific channel, possible values = {1 uA => 0, 100 uA => 1}
        """
        if value == 1:
            value = 0
        else:
            value = 1
        _query = "cur {} {}\n".format(self._channel, value)
        self.check_for_error(self.query(_query))

    def check_for_error(self, msg):
        """
        Error handling
        """
        if msg[:5] == b"Error":
            raise InstrIOError(cleandoc('''QDAc communication error'''))
        else:
            try:
                return msg.decode("utf-8")
            except AttributeError:
                raise InstrIOError(cleandoc('''QDAc communication error'''))

    def query(self, message, *args, **kwargs):
        """
        For debug purposes only; to be removed
        """
        print(message)
        return super().query(message, *args, **kwargs)
    
class QDacSingleChannel(VisaInstrument):
    """
    """

    caching_permissions = {'defined_channels': True}
    secure_com_except = (InvalidSession, InstrIOError, VisaIOError)

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):
        self.baud_rate = 460800
        self._channel = 1
        self.verbose = True
        self.resource_name = connection_info['resource_name']
        rm = pyvisa.ResourceManager()
        self.port_name = rm.list_resources_info()[self.resource_name].alias
        super(QDacSingleChannel, self).__init__(connection_info, caching_allowed,
                                       caching_permissions, auto_open)
        
    def open_connection(self, **para):
        """Open the connection to the instr using the `connection_str`
        """
        print('OPEN', para)
        self.port = serial.Serial(self.port_name, 460800)
    
    def close_connection(self):
        self.port.close()
        
    @instrument_property
    @secure_communication()
    def voltage(self):
        """output value getter method
        """
        return self.read_voltage_dc()

    @secure_communication()
    def read_voltage_dc(self):
        """output value getter method
        """
        _query = "set {}\n".format(self._channel)
        response = self.check_for_error(self.query(_query))
                
        if self.verbose:
            # response = ‘Output: <voltage> to Channel: <channel>\n’
            try:
                value = float(response.split(' ')[-1].strip())
            except ValueError:
                value = response
        else:
            # response = '<voltage>\n’
            try:
                value = float(response.strip())
            except ValueError:
                raise InstrIOError("Cannot parse output from the device")
        return value
    
    @voltage.setter
    @secure_communication()
    def voltage(self, value):
        """Output value setter method
        """
        _query = "set {} {}\n".format(self._channel, value)
        self.check_for_error(self.query(_query))

    @secure_communication()
    def read_current_dc(self):
        """output value getter method
        """
        _query = "get {}\n".format(self._channel)
        response = self.check_for_error(self.query(_query))
        if self.verbose:
            # response = 'Channel <channel> current: <current> uA\n' (verbose on)
            value = float(response.split(":", 1)[1][:-2])
        else:
            # response = ‘<current>\n’ (
            value = float(response.strip())
        return value * 1E-6

    @instrument_property
    def current(self):
        return self.read_current_dc()

    @instrument_property
    @secure_communication()
    def voltage_range(self):
        """
        Get voltage range for the specific channel. 0 = +/- 10V, 1 = +/- 1.1 V
        """
        _query = "vol {}\n".format(self._channel)
        response = self.check_for_error(self.query(_query))
        if self.verbose:
            # Response = 'Voltage range on Channel <channel> set to: <range>\n’, <range> = {'x1', 'x0.1'}
            value = int(response.split('x')[1][0])
            if value == 1:
                return 10
            else:
                return 1.1
        else:
            value = int(response)
            if response == 0:
                return 10
            else:
                return 1.1

    @voltage_range.setter
    @secure_communication()
    def voltage_range(self, value):
        """
        Set voltage range for the specific channel, possible values = {10 V = 0, 1.1 V = 1}
        """
        if value == 10:
            value = 0
        else:
            value = 1
        _query = "vol {} {}\n".format(self._channel, value)
        self.check_for_error(self.query(_query))

    @instrument_property
    @secure_communication()
    def current_range(self):
        """
        Get voltage range for the specific channel. 0 => 1 uA, 1 => 100 mA
        """
        _query = "cur {}\n".format(self._channel)
        response = self.check_for_error(self.query(_query))
        if self.verbose:
            # response = 'Current range on Channel <channel> set to: <range>\n’, <range> = 'Low', 'High'
            value = response.split(':')[1].strip()
            if value == "Low":
                return 1E-6
            else:
                return 1E-4
        else:
            # response = '0', '1'
            if response == '0':
                return 1E-6
            else:
                return 1E-4

    @current_range.setter
    @secure_communication()
    def current_range(self, value):
        """
        Set voltage range for the specific channel, possible values = {1 uA => 0, 100 uA => 1}
        """
        if value == 1:
            value = 0
        else:
            value = 1
        _query = "cur {} {}\n".format(self._channel, value)
        self.check_for_error(self.query(_query))

    def check_for_error(self, msg):
        """
        Error handling
        """
        if msg[:5] == b"Error":
            raise InstrIOError(cleandoc('''QDAc communication error'''))
        else:
            try:
                return msg.decode("utf-8")
            except AttributeError:
                raise InstrIOError(cleandoc('''QDAc communication error'''))

    def query(self, message, *args, **kwargs):
        """
        For debug purposes only; to be removed
        """
        print(message)
        self.port.write(message.encode())
        return self.port.readline()