# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Drivers for ADwin system using VISA library.

"""
from ..driver_tools import (InstrIOError, secure_communication, instrument_property)
from ..dll_tools import DllInstrument
import numpy as np
import time
import ADwin


class Dummy(DllInstrument):
    """
    Driver for an Adwin Data Acquisition device, using the VISA library.

    Methods
    -------


    """
    #def __init__(self, *args, **kwargs):
    #    super().__init__(*args, **kwargs)
    def __init__(self, connection_infos, caching_allowed=True, caching_permissions={}, auto_open=True):
        super().__init__(connection_infos, caching_allowed,
                                         caching_permissions, auto_open)

        if auto_open:
            self.open_connection()
        self._voltage = 0
        self._voltages = (0.02*i for i in range(10))
        self.defined_channels = [1,2,3,4,5,6]

    def open_connection(self, **para):
        """Open the connection to the instr using the `connection_str`.

        """
        pass


    def close_connection(self):
        pass

    @instrument_property
    def voltage(self):
        print('Current voltage: {}V'.format(self._voltage))
        return self._voltage

    def read_voltage_dc(self):
        try:
            return next(self._voltages)
        except StopIteration:
            return self.voltage

    @voltage.setter
    def voltage(self, value):
        self._voltage = value
        print('Set new voltage: {}V'.format(self._voltage))
