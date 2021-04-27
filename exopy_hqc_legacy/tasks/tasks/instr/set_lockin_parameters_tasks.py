# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Task to send parameters to the lock-in.

"""
from time import sleep
import numbers
from inspect import cleandoc

from atom.api import (Str, Float, Bool, set_default)

from exopy.tasks.api import InstrumentTask, validators


class SetOscillatorFrequencyTask(InstrumentTask):
    """Sets the frequency outputted by a lockin.

    """
    # Frequency.
    frequency = Str().tag(pref=True)

    database_entries = set_default({'Frequency(Hz)': 137})

    def perform(self):
        """Set the specified frequency.

        """
        self.driver.set_osc_frequency(self.format_and_eval_string(self.frequency))

        self.write_in_database('Frequency(Hz)', self.format_and_eval_string(self.frequency))

class SetOscillatorAmplitudeTask(InstrumentTask):
    """Sets the Vrms outputted by a lockin.

    """
    # Amplitude.
    amplitude = Str().tag(pref=True)

    database_entries = set_default({'Vac(mV)': 100})

    def perform(self):
        """Set the specified amplitude.

        """
        self.driver.set_osc_amplitude(self.format_and_eval_string(self.amplitude))
        
        self.write_in_database('Vac(mV)', self.format_and_eval_string(self.amplitude))
