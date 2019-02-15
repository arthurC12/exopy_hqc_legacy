# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Tasks to set the parameters of arbitrary waveform generators.

"""
import numbers
import numpy as np

from atom.api import Enum, Unicode, Value, set_default

from exopy.tasks.api import (InstrumentTask, validators)
import exopy_hqc_legacy.instruments.drivers.dll.SA124B as sa

SA_SWEEPING = 0x0
SA_REAL_TIME = 0x1

VAL_REAL = validators.Feval(types=numbers.Real)

class SpikeGetTrace(InstrumentTask):
    """ Task to get a trace from Spike instrument

    """

    # Get user inputs
    f0 = Unicode('6e9').tag(pref=True, feval=VAL_REAL)
    span = Unicode('100e6').tag(pref=True, feval=VAL_REAL)
    rbw = Unicode('250e3').tag(pref=True, feval=VAL_REAL)
    vbw = Unicode('250e3').tag(pref=True, feval=VAL_REAL)
    
    database_entries = set_default({'f0':1, 'span':1, 'rbw':1, 'vbw':1,
                                    'sweep_freq': 1, 'spectrum': 1})

    def check(self, *args, **kwargs):
        ''' Default checks and check different AWG channels
        '''
        test, traceback = super(SpikeGetTrace, self).check(*args, **kwargs)
        if not test:
            return test, traceback

        return test, traceback

    def perform(self):
        """Default interface behavior.

        """

        # get power for optimal parameters at sig, leakage and sideband
        self.driver.do_set_f0_span(self.format_and_eval_string(self.f0),
                                   self.format_and_eval_string(self.span))
        self.driver.do_set_rbw_vbw(self.format_and_eval_string(self.rbw),
                                    self.format_and_eval_string(self.vbw))
        sweep_freq, spectrum = self.driver.sweep()

        # log values
        self.write_in_database('sweep_freq', sweep_freq)
        self.write_in_database('spectrum', spectrum)
#        self.driver._close()