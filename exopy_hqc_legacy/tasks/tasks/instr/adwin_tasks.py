# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Task to run processed on Adwin

"""

import numpy as np

from atom.api import (Float, Value, Str, Int, set_default, Enum, Tuple, Bool)

from exopy.tasks.api import (InstrumentTask, TaskInterface)

CONVERSION_FACTORS = {'V': {'mV': 1e3, 'uV': 1e6, 'V': 1},
                      'mV': {'mV': 1, 'uV': 1e3, 'V': 1e-3},
                      'uV': {'mV': 1e-3, 'uV': 1, 'V': 1e-6}}


class _RecordIVTask(InstrumentTask):
    """Record the IV using Adwin
    """
    voltage = Float().tag(pref=True)
    number_of_points = Int().tag(pref=True)
    parallel = set_default({'activated': False, 'pool': 'instr'})
    database_entries = set_default({'voltage': np.array([0.0]), 'current': np.array([1.0])})

    def perform(self, value=None):
        """Default interface for IV measurement.

        """
        if self.driver.owner != self.name:
            self.driver.owner = self.name
        x, y = self.driver._record_IV(self.voltage, self.number_of_points)
        self.write_in_database('voltage', x)
        self.write_in_database('current', y)


class RecordIVTask(InstrumentTask):
    """Record the IV using Adwin
    """
    voltage_min = Float(0.0).tag(pref=True)
    voltage_max = Float(1.0).tag(pref=True)
    number_of_points = Int(100).tag(pref=True)
    process_delay = Float(0.00).tag(pref=True)
    loops_waiting = Int(1).tag(pref=True)
    points_av = Int(1).tag(pref=True)
    log = Bool().tag(pref=True)
    lin_gain = Float(1.0).tag(pref=True)
    log_conversion = Bool().tag(pref=True)
    process_file = Int().tag(pref=True)
    parallel = set_default({'activated': False, 'pool': 'instr'})
    database_entries = set_default({'voltage': np.array([0.0]), 'current': np.array([1.0])})

    def perform(self, value=None):
        """Default interface for IV measurement.

        """
        voltage = np.linspace(self.voltage_min, self.voltage_max, self.number_of_points)
        if self.driver.owner != self.name:
            self.driver.owner = self.name
        x, y = self.driver.record_IV(voltage, self.process_delay, self.loops_waiting,
                                     self.points_av, self.log, self.lin_gain, self.log_conversion, self.process_file)
        self.write_in_database('voltage', x)
        self.write_in_database('current', y)


class AdwinVoltageTask(InstrumentTask):
    """Record the IV using Adwin
    """
    value = Float(0.0).tag(pref=True)
    process_delay = Float(0.00).tag(pref=True)
    out_channel = Int(1).tag(pref=True)
    in_channel = Int(1).tag(pref=True)
    parallel = set_default({'activated': False, 'pool': 'instr'})
    database_entries = set_default({'out_voltage': 0.0, 'in_voltage': 0.0})

    def perform(self, value=None):
        """Default interface for IV measurement.

        """
        if value is None:
            value = self.value
        if self.driver.owner != self.name:
            self.driver.owner = self.name
        x = self.driver.set_voltage(self.value, self.out_channel, self.in_channel, self.process_delay)
        self.write_in_database('out_voltage', value)
        self.write_in_database('in_voltage', x)


class AdwinSetVoltageInterface(TaskInterface):
    """Set a DC voltage to the specified value for the specified channel of Adwin

    """
    #: Id of the channel whose central frequency should be set.
    out_channel = Int(1).tag(pref=True)
    database_entries = set_default({'voltage': 0.0})

    def perform(self, value=None):
        """Set the Voltage of the specified channel.

        """
        task = self.task
        task.driver.owner = task.name
        if value is None:
            value = self.convert(task.format_and_eval_string(task.value),'V')
        task.driver.set_voltage(value, self.out_channel)
        task.write_in_database('voltage', value)

    def check(self, *args, **kwargs):
        """

        """
        return super().check(*args, **kwargs)

    def convert(self, voltage, unit):
        """ Convert a voltage to the given unit.
        """
        print('Converting {} {} to {}'.format(voltage, self.task.unit, unit))
        print('Convertion factor: ', CONVERSION_FACTORS[self.task.unit][unit])
        return voltage*CONVERSION_FACTORS[self.task.unit][unit]


class AdwinGetVoltageInterface(TaskInterface):
    """Read a DC voltage from the specified channel of Adwin

    """
    #: Id of the channel whose central frequency should be set.
    in_channel = Int(1).tag(pref=True)
    database_entries = set_default({'voltage': 0.0})

    def perform(self):
        """Set the Voltage of the specified channel.

        """
        task = self.task
        task.driver.owner = task.name
        # if value is None:
        #    value = task.format_and_eval_string(task.value)
        x = task.driver.get_voltage(self.in_channel)
        task.write_in_database('voltage', float(x))

    def check(self, *args, **kwargs):
        """

        """
        return super().check(*args, **kwargs)

class LoadProcessTask(InstrumentTask):
    """Load Process from the file
    """
    process_name = Str().tag(pref=True)
    parallel = set_default({'activated': False, 'pool': 'instr'})

    def perform(self, value=None):
        """Default interface.

        """
        if self.driver.owner != self.name:
            self.driver.owner = self.name
        self.driver.load_process(self.process_name)
