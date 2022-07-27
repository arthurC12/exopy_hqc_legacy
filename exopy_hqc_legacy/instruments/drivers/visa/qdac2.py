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

from ..driver_tools import (
    BaseInstrument,
    InstrIOError,
    secure_communication,
    instrument_property,
)
from ..visa_tools import VisaInstrument

import serial
import pyvisa


class QDac2Channel(BaseInstrument):

    secure_com_except = (InvalidSession, InstrIOError, VisaIOError)

    def __init__(
        self, QDac2, channel_num, caching_allowed=True, caching_permissions={}
    ):
        super().__init__(None, caching_allowed, caching_permissions)
        self._QDac2 = QDac2
        self._channel = channel_num
        self._voltage_range = 2  # 10 Volts by default
        # self._current_range = 100e-6  # 100 microAmps by default
        # self.verbose = True

    def reopen_connection(self, *args, **kwargs):
        self._QDac2.reopen_connection(*args, **kwargs)

    @instrument_property
    @secure_communication()
    def voltage(self):
        """output value getter method
        """
        # getvoltage = "SOURce{}:VOLT ?".format(self._channel)
        value = self._QDac2.query("SOURce{}:VOLT?".format(self._channel))
        if value:
            return float(value)
        else:
            raise InstrIOError("Instrument did not return the voltage")

    @voltage.setter
    @secure_communication()
    def voltage(self, value):
        """Output value setter method
        """
        # setvoltage = "SOURce{}:VOLT {}".format(self._channel, value)
        self._QDac2.write("SOURce{}:VOLT {}".format(self._channel, value))
        result = float(self._QDac2.query("SOURce{}:VOLT?".format(self._channel)))
        if abs(result - round(value, 9)) > 5e-6:
            raise InstrIOError("Instrument did not set correctly the voltage")

    @secure_communication()
    def read_voltage_dc(self):
        return self.voltage

    @instrument_property
    @secure_communication()
    def output_filter(self):
        filter_state = self._QDac2.query("sour{}:filt?".format(self._channel))
        return filter_state

    @output_filter.setter
    @secure_communication()
    def output_filter(self, state):

        if state.lower() not in ["dc", "medium", "high"]:
            raise InstrIOError(
                'the output filter should be either "DC"(10Hz), "MED" (10kHz) or "HIGH" (230MHz)'
            )

        self._QDac2.write("sour{}:filt {}".format(self._channel,state))
        output = self._QDac2.query("sour{}:filt?".format(self._channel))
        if state.lower() == output.lower():
            print("Channel {} output filter set to {}".format(self._channel, state))
            return state
        else:
            raise InstrIOError("the output filter has not been set correctly")

    @instrument_property
    @secure_communication()
    def output_range(self):
        range = self._QDac2.query("sour{}:rang?".format(self._channel))
        return range

    @output_filter.setter
    @secure_communication()
    def output_range(self, state):

        if state.lower() not in ["low", "high"]:
            raise InstrIOError(
                'the range should be either "LOW"(+-2V) or "HIGH" (+-10V)'
            )

        self._QDac2.write("sour{}:rang {}".format(self._channel,state))
        output = self._QDac2.query("sour{}:rang?".format(self._channel))
        if state.lower() == output.lower():
            print("Channel {} range set to {}".format(self._channel, state))
            return state
        else:
            raise InstrIOError("the output range has not been set correctly")





class QDac2(VisaInstrument):
    """
    """

    caching_permissions = {"defined_channels": True}
    secure_com_except = (InvalidSession, InstrIOError, VisaIOError)

    def __init__(
        self,
        connection_info,
        caching_allowed=True,
        caching_permissions={},
        auto_open=True,
    ):
        if connection_info["resource_name"].find("ASRL") != -1:
            self.baud_rate = 921600
        self.verbose = True
        self.resource_name = connection_info["resource_name"]
        # rm = pyvisa.ResourceManager()
        # self.port_name = rm.list_resources_info()[self.resource_name].alias
        self.channels = {}
        self.defined_channels = list(range(1, 25))
        super().__init__(
            connection_info, caching_allowed, caching_permissions, auto_open
        )
        # self.channels = {}
        # self.defined_channels = list(range(1, 25))

    def open_connection(self, **para):
        """Open the connection to the instr using the `connection_str`
        """
        # super(QDac2, self).open_connection(**para)
        rm = pyvisa.ResourceManager("@py")
        try:
            self._driver = rm.open_resource(
                self.connection_str, open_timeout=1000, **para
            )
        except errors.VisaIOError as er:
            self._driver = None
            raise InstrIOError(str(er))

        self.write_termination = "\n"
        self.read_termination = "\n"

        # These prevent to perform tasks, another task created in orde to do it manually
        # temporary: sets the DC outputs range to LOW in order to reduce noise floor
        # self.write("SOURce:RANGe LOW, (@1:24)")
        #
        # temporary: sets the cutoff frequency of the output low pass filter to MEDium (10kHz)
        # self.write("SOUR:FILT MED, (@1:24)")

        # for channel in self.defined_channels:
        #     msg = self.query("SOURce:RANGe?")
        #     if msg == "HIGH":
        #         self.write("SOUR{}:RANGe LOW".format(channel))
        #     msg2 = self.query("SOURce:FILTer?")
        #     if ((msg2 == "HIGH") or (msg2 == 'DC')):
        #         self.write("SOURce{}:FILTer:MED")

        # self.port = serial.Serial(self.port_name, self.baud_rate)
        # \r termination for the serial communication

    def close_connection(self):
        # self.port.close()
        super().close_connection()

    def get_channel(self, num):
        """num is a tuple containing (module_number,channel_number)
        """
        defined = self.defined_channels
        if num not in defined:
            msg = "No channel {}, only channels {} exist"
            raise KeyError(msg.format(num, defined))

        if num in self.channels:
            return self.channels[num]
        else:
            channel = QDac2Channel(self, num)
            print("Channel #{} created".format(num))
            self.channels[num] = channel
            return self.channels[num]


class QDac2SingleChannel(VisaInstrument):
    """
       """

    caching_permissions = {"defined_channels": True}
    secure_com_except = (InvalidSession, InstrIOError, VisaIOError)

    def __init__(
        self,
        connection_info,
        caching_allowed=True,
        caching_permissions={},
        auto_open=True,
    ):
        self._channel = 9
        # self.verbose = True
        self.resource_name = connection_info["resource_name"]
        # rm = pyvisa.ResourceManager('@py')
        # self.port_name = rm.list_resources_info()[self.resource_name].alias
        super(QDac2SingleChannel, self).__init__(
            connection_info, caching_allowed, caching_permissions, auto_open
        )

    def open_connection(self, **para):
        """Open the connection to the instr using the `connection_str`
        """
        # super(QDac2, self).open_connection(**para)
        rm = pyvisa.ResourceManager("@py")
        try:
            self._driver = rm.open_resource(
                self.connection_str, open_timeout=1000, **para
            )
        except errors.VisaIOError as er:
            self._driver = None
            raise InstrIOError(str(er))

        self.write_termination = "\n"
        self.read_termination = "\n"
        # self.write("*rst")
        # temporary: sets the DC outputs range to LOW in order to reduce noise floor
        # self.write("SOURce:RANGe LOW, (@1:24)")

        # temporary: sets the cutoff frequency of the output low pass filter to MEDium (10kHz)
        # self.write("SOUR:FILT MED, (@1:24)")

    # def open_connection(self, **para):
    #     """Open the connection to the instr using the `connection_str`
    #     """
    #     print('OPEN', para)
    #     self.port = serial.Serial(self.port_name, 460800)

    # def close_connection(self):
    #     self.port.close()

    @instrument_property
    @secure_communication()
    def voltage(self):
        """output value getter method
        """
        # self.write('*IDN?')
        # self.read_bytes(1)
        value = self.query("SOURce9:VOLT?")
        if value:
            return float(value)
        else:
            raise InstrIOError("Instrument did not return the voltage")

    @secure_communication()
    def read_voltage_dc(self):

        return self.voltage

    @voltage.setter
    @secure_communication()
    def voltage(self, value):
        """Output value setter method
        """
        self.write("SOURce9:VOLT {}".format(value))
        result = float(self.query("SOURce9:VOLT?"))
        if abs(result - round(value, 9)) > 5e-6:
            raise InstrIOError("Instrument did not set correctly the voltage")

    @instrument_property
    @secure_communication()
    def output_filter(self):
        filter_state = self.query("sour9:filt?")
        return filter_state

    @output_filter.setter
    @secure_communication()
    def output_filter(self, state):

        if state.lower() not in ["dc", "medium", "high"]:
            raise InstrIOError(
                'the output filter should be either "DC"(10Hz), "MED" (10kHz) or "HIGH" (230MHz)'
            )

        self.write("sour9:filt {}".format(state))
        output = self.query("sour9:filt?")
        if state.lower() == output.lower():
            return state
        else:
            raise InstrIOError("the output filter has not been set correctly")

    @instrument_property
    @secure_communication()
    def output_range(self):
        range = self.query("sour9:rang?")
        return range

    @output_filter.setter
    @secure_communication()
    def output_range(self, state):

        if state.lower() not in ["low", "high"]:
            raise InstrIOError(
                'the range should be either "LOW"(+-2V) or "HIGH" (+-10V)'
            )

        self.write("sour9:rang {}".format(state))
        output = self.query("sour9:rang?")
        if state.lower() == output.lower():
            return state
        else:
            raise InstrIOError("the output range has not been set correctly")
