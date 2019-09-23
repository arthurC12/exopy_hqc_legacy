# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2019 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Drivers for lock-in from Signal Recovery using VISA library.

"""
from ..driver_tools import (InstrIOError, secure_communication)
from ..visa_tools import VisaInstrument


class CryoCon32B(VisaInstrument):
    """Driver for a CryoCon32B lock-in, using the VISA library.

    This driver does not give access to all the functionnality of the
    instrument but you can extend it if needed. See the documentation of the
    driver_tools package for more details about writing instruments drivers.

    Parameters
    ----------
    see the `VisaInstrument` parameters in the `driver_tools` module

    Methods
    -------
    read_temperature()
        Return the temperature measured by the instrument

    Notes
    -----
    The completion of each command is checked by reading the status byte (see
    `_check_completion` method)

    """
    def open_connection(self, **para):
        """Open the connection to the instr using the `connection_str`.

        """
        super(CryoCon32B, self).open_connection(**para)
        self.write_termination = '\n'
        self.read_termination = '\n'

    @secure_communication()
    def read_temperature(self):
        """
        Return the temperature for the channel A measured by the instrument

        """
        value = self.ask_for_values('INPUT A:TEMPER?')
        
        return value[0]