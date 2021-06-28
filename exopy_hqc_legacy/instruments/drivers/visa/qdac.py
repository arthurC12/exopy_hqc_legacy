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
        response = self._check(self._QDac.query(b"set %d" % self._channel)).decode("utf-8")
        if self.verbose:
            # response = ‘Output: <voltage> to Channel: <channel>\n’
            value = float(response.split("Output:")[1].split("(")[0].strip(" "))
        else:
            # response = '<voltage>\n’
            value = float(response.strip())
        return value

    @voltage.setter
    @secure_communication()
    def voltage(self, value):
        """Output value setter method
        """
        self._check(self._QDac.query(b"set %d %g" % (self._channel, value))).decode("utf-8")

    def read_voltage_dc(self):
        return self.voltage

    @instrument_property
    @secure_communication()
    def current(self):
        """output value getter method
        """
        response = self._check(self._QDac.query(b"get %d" % self._channel)).decode("utf-8")
        if self.verbose:
            # response = 'Channel <channel> current: <current> uA\n' (verbose on)
            value = float(response.split(":", 1)[1][:-2])
        else:
            # response = ‘<current>\n’ (
            value = float(response.strip())
        return value*1E-6

    @instrument_property
    @secure_communication()
    def voltage_range(self):
        """
        Get voltage range for the specific channel. 0 = +/- 10V, 1 = +/- 1.1 V
        """
        response = self._check(self._QDac.query(b"vol %d" % self._channel)).decode("utf-8")
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
        self._check(self._QDac.query(b"vol %d %d" % (self._channel, value))).decode("utf-8")

    @instrument_property
    @secure_communication()
    def current_range(self):
        """
        Get voltage range for the specific channel. 0 => 1 uA, 1 => 100 mA
        """
        response = self._check(self._QDac.query(b"cur %d" % self._channel)).decode("utf-8")
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
        self._check(self._QDac.query(b"cur %d %d" % (self._channel, value))).decode("utf-8")

    def _check(self, msg):
        """
        Error handling
        """
        if msg[:5] == b"Error":
            raise InstrIOError(cleandoc('''QDAc communication error'''))
        else:
            return msg


class QDac(VisaInstrument):
    """
    """
    caching_permissions = {'defined_channels': True}
    secure_com_except = (InvalidSession, InstrIOError, VisaIOError)

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):
        super(QDac, self).__init__(connection_info, caching_allowed,
                                       caching_permissions, auto_open)
        self.baud_rate = 460800
        self.channels = {}
        self.defined_channels = list(range(1, 25))

    def open_connection(self, **para):
        """Open the connection to the instr using the `connection_str`
        """
        super(QDac, self).open_connection(**para)
        # \r termination for the serial communication
        self.write_termination = '\r'
        self.read_termination = '\r'

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
            self.channels[num] = channel
            return channel

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
        super(QDacSingleChannel, self).__init__(connection_info, caching_allowed,
                                       caching_permissions, auto_open)
        self.baud_rate = 460800
        self._channel = 1
        self.verbose = True

    def open_connection(self, **para):
        """Open the connection to the instr using the `connection_str`
        """
        super(QDacSingleChannel, self).open_connection(**para)
        # \r termination for the serial communication
        self.write_termination = '\r'
        self.read_termination = '\r'

    @instrument_property
    @secure_communication()
    def voltage(self):
        """output value getter method
        """
        response = self._check(self.query(b"set %d" % self._channel)).decode("utf-8")
        if self.verbose:
            # response = ‘Output: <voltage> to Channel: <channel>\n’
            value = float(response.split("Output:")[1].split("(")[0].strip(" "))
        else:
            # response = '<voltage>\n’
            value = float(response.strip())
        return value


    @voltage.setter
    @secure_communication()
    def voltage(self, value):
        """Output value setter method
        """
        self._check(self.query(b"set %d %g" % (self._channel, value))).decode("utf-8")

    def read_voltage_dc(self):
        return self.voltage

    @instrument_property
    @secure_communication()
    def current(self):
        """output value getter method
        """
        response = self._check(self.query(b"get %d" % self._channel)).decode("utf-8")
        if self.verbose:
            # response = 'Channel <channel> current: <current> uA\n' (verbose on)
            value = float(response.split(":", 1)[1][:-2])
        else:
            # response = ‘<current>\n’ (
            value = float(response.strip())
        return value*1E-6

    @instrument_property
    @secure_communication()
    def voltage_range(self):
        """
        Get voltage range for the specific channel. 0 = +/- 10V, 1 = +/- 1.1 V
        """
        response = self._check(self.query(b"vol %d" % self._channel)).decode("utf-8")
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
        self._check(self.query(b"vol %d %d" % (self._channel, value))).decode("utf-8")

    @instrument_property
    @secure_communication()
    def current_range(self):
        """
        Get voltage range for the specific channel. 0 => 1 uA, 1 => 100 mA
        """
        response = self._check(self.query(b"cur %d" % self._channel)).decode("utf-8")
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
        self._check(self.query(b"cur %d %d" % (self._channel, value))).decode("utf-8")

    def _check(self, msg):
        """
        Error handling
        """
        if msg[:5] == b"Error":
            raise InstrIOError(cleandoc('''QDAc communication error'''))
        else:
            return msg


    def query(self, message, *args, **kwargs):
        """
        For debug purposes only; to be removed
        """
        print(message)
        return super().query(message, *args, **kwargs)