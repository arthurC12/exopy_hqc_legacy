# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2021 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Task perform measurements with a VNA.

"""
from atom.api import (Int, Value, Enum)

from exopy.tasks.api import TaskInterface

CONVERSION_FACTORS = {'GHz': {'Hz': 1e9, 'kHz': 1e6, 'MHz': 1e3, 'GHz': 1},
                      'MHz': {'Hz': 1e6, 'kHz': 1e3, 'MHz': 1, 'GHz': 1e-3},
                      'kHz': {'Hz': 1e3, 'kHz': 1, 'MHz': 1e-3, 'GHz': 1e-6},
                      'Hz': {'Hz': 1, 'kHz': 1e-3, 'MHz': 1e-6, 'GHz': 1e-9},
                      'Deg': {'Rad': 0.017453292519943295, 'Deg': 1},
                      'Rad': {'Rad': 1, 'Deg': 57.29577951308232}}


def check_channels_presence(task, channels, *args, **kwargs):
    """ Check that all the channels are correctly defined on the PNA.

    """
    if kwargs.get('test_instr'):
        traceback = {}
        err_path = task.get_error_path()
        with task.test_driver() as instr:
            if instr is None:
                return False, traceback
            channels_present = True
            for channel in channels:
                if channel not in instr.defined_channels:
                    key = err_path + '_' + str(channel)
                    msg = ("Channel {} is not defined in the PNA {}."
                           " Please define it yourself and try again.")
                    traceback[key] = msg.format(channel,
                                                task.selected_instrument[0])

                    channels_present = False

            return channels_present, traceback

    else:
        return True, {}


class MCSetRFFrequencyInterface(TaskInterface):
    """Set the central frequency to be used for the specified channel.

    """
    #: Id of the channel whose central frequency should be set.
    channel = Int(1).tag(pref=True)
    unit = Enum('GHz', 'MHz', 'kHz', 'Hz').tag(pref=True)
    #: Driver for the channel.
    channel_driver = Value()

    def perform(self, frequency=None):
        """Set the central frequency of the specified channel.

        """
        task = self.task
        if not self.channel_driver:
            self.channel_driver = task.driver.get_channel(self.channel)

        task.driver.owner = task.name
        self.channel_driver.owner = task.name

        if frequency is None:
            frequency = task.format_and_eval_string(task.frequency)
            frequency = task.convert(frequency, 'Hz')

        self.channel_driver.frequency = frequency
        task.write_in_database('frequency', frequency)

    def check(self, *args, **kwargs):
        """Make sure the specified channel does exists on the instrument.

        """
        test, tb = super(MCSetRFFrequencyInterface,
                         self).check(*args, **kwargs)
        task = self.task
        res = check_channels_presence(task, [self.channel], *args, **kwargs)
        tb.update(res[1])
        return test and res[0], tb

    def convert(self, frequency, unit):
        """ Convert a frequency to the given unit.

        Parameters
        ----------
        frequency : float
            Frequency expressed in the task unit

        unit : {'Hz', 'kHz', 'MHz', 'GHz'}
            Unit in which to express the result

        Returns
        -------
        converted_frequency : float

        """
        return frequency*CONVERSION_FACTORS[self.unit][unit]


class MCSetRFPhaseInterface(TaskInterface):
    """Set the central frequency to be used for the specified channel.

    """
    #: Id of the channel whose central frequency should be set.
    channel = Int(1).tag(pref=True)

    #: Driver for the channel.
    channel_driver = Value()

    def perform(self, phase=None):
        """Set the central frequency of the specified channel.

        """
        task = self.task
        if not self.channel_driver:
            self.channel_driver = task.driver.get_channel(self.channel)

        task.driver.owner = task.name
        self.channel_driver.owner = task.name

        if phase is None:
            phase = task.format_and_eval_string(task.phase)
            phase = task.convert(phase, 'Deg')

        self.channel_driver.phase = phase
        task.write_in_database('phase', phase)

    def check(self, *args, **kwargs):
        """Make sure the specified channel does exists on the instrument.

        """
        test, tb = super(MCSetRFPhaseInterface,
                         self).check(*args, **kwargs)
        task = self.task
        res = check_channels_presence(task, [self.channel], *args, **kwargs)
        tb.update(res[1])
        return test and res[0], tb
        

class MCSetRFPowerInterface(TaskInterface):
    """Set the central power to be used for the specified channel.

    """
    #: Id of the channel whose central frequency should be set.
    channel = Int(1).tag(pref=True)

    #: Port whose output power should be set.
    port = Int(1).tag(pref=True)

    #: Driver for the channel.
    channel_driver = Value()

    def prepare(self):
        """Create the channel driver.

        """
        self.channel_driver = self.task.driver.get_channel(self.channel)

    def perform(self, power=None):
        """Set the power for the selected channel and port.

        """
        task = self.task

        task.driver.owner = task.name
        self.channel_driver.owner = task.name

        if power is None:
            power = task.format_and_eval_string(task.power)

        self.channel_driver.power = power
        task.write_in_database('power', power)

        if task.auto_start:
            task.driver.output = 'On'

    def check(self, *args, **kwargs):
        """Ensure the presence of the requested channel.

        """
        test, tb = super(MCSetRFPowerInterface, self).check(*args, **kwargs)
        task = self.task
        res = check_channels_presence(task, [self.channel], *args, **kwargs)
        tb.update(res[1])
        return test and res[0], tb


class MCSetRFOnOffInterface(TaskInterface):
    """Set the central frequency to be used for the specified channel.

    """
    #: Id of the channel whose central frequency should be set.
    channel = Int(1).tag(pref=True)

    #: Driver for the channel.
    channel_driver = Value()

    def perform(self, switch=None):
        """Set the central frequency of the specified channel.

        """
        task = self.task
        if not self.channel_driver:
            self.channel_driver = task.driver.get_channel(self.channel)

        task.driver.owner = task.name
        self.channel_driver.owner = task.name

        if switch is None:
            switch = task.format_and_eval_string(task.switch)
        
        if switch == 'On' or switch == 1:
            self.channel_driver.output = 'On'
            task.write_in_database('output', 1)
        else:  # if switch == 'Off' or switch == 0:
            self.channel_driver.output = 'Off'
            task.write_in_database('output', 0)

    def check(self, *args, **kwargs):
        """Make sure the specified channel does exists on the instrument.

        """
        test, tb = super(MCSetRFOnOffInterface,
                         self).check(*args, **kwargs)
        task = self.task
        res = check_channels_presence(task, [self.channel], *args, **kwargs)
        tb.update(res[1])
        return test and res[0], tb
