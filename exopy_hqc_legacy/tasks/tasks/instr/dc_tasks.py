# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Task to set the parameters of microwave sources..

"""
import time
import numbers
import numpy as np
from atom.api import (Float, Value, Str, Int, set_default, Enum, Tuple, List)

from exopy.tasks.api import (InstrumentTask, TaskInterface,
                            InterfaceableTaskMixin, validators)

CONVERSION_FACTORS = {'V': {'mV': 1e3, 'uV': 1e6, 'V': 1},
                      'mV': {'mV': 1, 'uV': 1e3, 'V': 1e-3},
                      'uV': {'mV': 1e-3, 'uV': 1, 'V': 1e-6}}

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
                    msg = ("Channel {} is not defined in the {}."
                           " Please define it yourself and try again.")
                    traceback[key] = msg.format(channel,
                                                task.selected_instrument[0])

                    channels_present = False

            return channels_present, traceback

    else:
        return True, {}


class GetDCVoltageTask(InstrumentTask):
    """Get the current DC voltage of an instrument
    """

    parallel = set_default({'activated': False, 'pool': 'instr'})
    database_entries = set_default({'voltage': 0.01})

    def perform(self, value=None):
        """Default interface.

        """
        if self.driver.owner != self.name:
            self.driver.owner = self.name
            if hasattr(self.driver, 'function') and\
                    self.driver.function != 'VOLT':
                msg = ('Instrument assigned to task {} is not configured to '
                       'output a voltage')
                raise ValueError(msg.format(self.name))

        #current_value = getattr(self.driver, 'voltage')
        current_value = self.driver.read_voltage_dc()
        self.write_in_database('voltage', float(current_value))


class SetDCVoltageTask(InterfaceableTaskMixin, InstrumentTask):
    """Set a DC voltage to the specified value.

    The user can choose to limit the rate by choosing an appropriate back step
    (larger step allowed), and a waiting time between each step.

    """
    #: Target value for the source (dynamically evaluated)
    target_value = Str().tag(pref=True, feval=validators.SkipLoop(types=numbers.Real))

    #: Largest allowed step when changing the output of the instr.
    back_step = Float().tag(pref=True)

    #: Largest allowed voltage
    safe_max = Float(0.0).tag(pref=True)

    #: Largest allowed delta compared to current value
    safe_delta = Float(0.0).tag(pref=True)

    #: Time to wait between changes of the output of the instr.
    delay = Float(0.01).tag(pref=True)

    parallel = set_default({'activated': True, 'pool': 'instr'})
    database_entries = set_default({'voltage': 0.01})

    def i_perform(self, value=None):
        """Default interface.

        """
        if self.driver.owner != self.name:
            self.driver.owner = self.name
            if hasattr(self.driver, 'function') and\
                    self.driver.function != 'VOLT':
                msg = ('Instrument assigned to task {} is not configured to '
                       'output a voltage')
                raise ValueError(msg.format(self.name))

        setter = lambda value: setattr(self.driver, 'voltage', value)
        current_value = getattr(self.driver, 'voltage')

        value = self.format_and_eval_string(self.target_value)

        if self.safe_delta and abs(current_value-value) > self.safe_delta:
            msg = ('Voltage asked for {} is too far away from the current voltage {}!')
            raise ValueError(msg.format(value,current_value))

        self.smooth_set(value, setter, current_value)

    def smooth_set(self, target_value, setter, current_value):
        """ Smoothly set the voltage.

        target_value : float
            Voltage to reach.

        setter : callable
            Function to set the voltage, should take as single argument the
            value.

        current_value: float
            Current voltage.

        """
        if target_value is not None:
            value = target_value
        else:
            value = self.format_and_eval_string(self.target_value)

        if self.safe_delta and abs(current_value-value) > self.safe_delta:
            msg = ('Requested voltage {} is too far away from the current voltage {}!')
            raise ValueError(msg.format(value, current_value))

        if self.safe_max and self.safe_max < abs(value):
            msg = 'Requested voltage {} exceeds safe max : {}'
            raise ValueError(msg.format(value, self.safe_max))

        last_value = current_value

        if abs(last_value - value) < 1e-12:
            self.write_in_database('voltage', value)
            return

        elif self.back_step == 0:
            self.write_in_database('voltage', value)
            setter(value)
            return

        else:
            if (value - last_value)/self.back_step > 0:
                step = self.back_step
            else:
                step = -self.back_step

        if abs(value-last_value) > abs(step):
            while not self.root.should_stop.is_set():
                # Avoid the accumulation of rounding errors
                last_value = round(last_value + step, 9)
                setter(last_value)
                if abs(value-last_value) > abs(step):
                    time.sleep(self.delay)
                else:
                    break

        if not self.root.should_stop.is_set():
            setter(value)
            self.write_in_database('voltage', value)
            return

        self.write_in_database('voltage', last_value)


class MultiChannelVoltageSourceInterface(TaskInterface):
    """Interface for multiple outputs sources.

    """
    #: Id of the channel to use.
    channel = Tuple(default=(1, 1)).tag(pref=True)
    #channel = Int(1).tag(pref=True)
    #: Reference to the driver for the channel.
    channel_driver = Value()

    def perform(self, value=None):
        """Set the specified voltage.

        """
        task = self.task
        if not self.channel_driver:
            self.channel_driver = task.driver.get_channel(self.channel)
        if self.channel_driver.owner != task.name:
            self.channel_driver.owner = task.name
            if hasattr(self.channel_driver, 'function') and\
                    self.channel_driver.function != 'VOLT':
                msg = ('Instrument output assigned to task {} is not '
                       'configured to output a voltage')
                raise ValueError(msg.format(self.name))

        setter = lambda value: setattr(self.channel_driver, 'voltage', value)
        current_value = getattr(self.channel_driver, 'voltage')

        task.smooth_set(value, setter, current_value)

    def check(self, *args, **kwargs):
        if kwargs.get('test_instr'):
            task = self.task
            traceback = {}
            with task.test_driver() as d:
                if d is None:
                    return True, {}
                if self.channel not in d.defined_channels:
                    key = task.get_error_path() + '_interface'
                    traceback[key] = 'Missing channel {}'.format(self.channel)

            if traceback:
                return False, traceback
            else:
                return True, traceback

        else:
            return True, {}


class SetDCCurrentTask(InterfaceableTaskMixin, InstrumentTask):
    """Set a DC current to the specified value.

    The user can choose to limit the rate by choosing an appropriate back step
    (larger step allowed), and a waiting time between each step.

    """
    #: Target value for the source (dynamically evaluated)
    target_value = Str().tag(pref=True, feval=validators.SkipLoop(types=numbers.Real))

    #: Largest allowed step when changing the output of the instr.
    back_step = Float().tag(pref=True)

    #: Largest allowed current
    safe_max = Float(0.0).tag(pref=True)

    #: Time to wait between changes of the output of the instr.
    delay = Float(0.01).tag(pref=True)

    parallel = set_default({'activated': True, 'pool': 'instr'})
    database_entries = set_default({'current': 0.01})

    def i_perform(self, value=None):
        """Default interface.

        """
        if self.driver.owner != self.name:
            self.driver.owner = self.name
            if hasattr(self.driver, 'function') and\
                    self.driver.function != 'CURR':
                msg = ('Instrument assigned to task {} is not configured to '
                       'output a current')
                raise ValueError(msg.format(self.name))

        setter = lambda value: setattr(self.driver, 'current', value)
        current_value = getattr(self.driver, 'current')

        self.smooth_set(value, setter, current_value)

    def smooth_set(self, target_value, setter, current_value):
        """ Smoothly set the current.

        target_value : float
            Current to reach.

        setter : callable
            Function to set the current, should take as single argument the
            value.

        """
        if target_value is not None:
            value = target_value
        else:
            value = self.format_and_eval_string(self.target_value)

        if self.safe_max and self.safe_max < abs(value):
            msg = 'Requested current {} exceeds safe max : {}'
            raise ValueError(msg.format(value, self.safe_max))

        last_value = current_value

        if abs(last_value - value) < 1e-9:
            self.write_in_database('current', value)
            return

        elif self.back_step == 0:
            self.write_in_database('current', value)
            setter(value)
            return

        else:
            if (value - last_value)/self.back_step > 0:
                step = self.back_step
            else:
                step = -self.back_step

        if abs(value-last_value) > abs(step):
            while not self.root.should_stop.is_set():
                # Avoid the accumulation of rounding errors
                last_value = round(last_value + step, 6)
                setter(last_value)
                if abs(value-last_value) > abs(step):
                    time.sleep(self.delay)
                else:
                    break

        if not self.root.should_stop.is_set():
            setter(value)
            self.write_in_database('current', value)
            return

        self.write_in_database('current', last_value)


class SetDCFunctionTask(InterfaceableTaskMixin, InstrumentTask):
    """Set a DC source function to the specified value: VOLT or CURR

    """
    #: Target value for the source (dynamically evaluated)
    switch = Str('VOLT').tag(pref=True, feval=validators.SkipLoop())

    database_entries = set_default({'function': 'VOLT'})

    def i_perform(self, switch=None):
        """Default interface.

        """
        if switch is None:
            switch = self.format_and_eval_string(self.switch)

        if switch == 'VOLT':
            self.driver.function = 'VOLT'
            self.write_in_database('function', 'VOLT')

        if switch == 'CURR':
            self.driver.function = 'CURR'
            self.write_in_database('function', 'CURR')


class SetDCOutputTask(InterfaceableTaskMixin, InstrumentTask):
    """Set a DC source output to the specified value: ON or OFF

    """
    #: Target value for the source output
    switch = Str('OFF').tag(pref=True, feval=validators.SkipLoop())

    database_entries = set_default({'output': 'OFF'})

    def i_perform(self, switch=None):
        """Default interface.

        """
        if self.switch == 'ON':
            self.driver.output = 'ON'
            self.write_in_database('output', 'ON')

        elif self.switch == 'OFF':
            self.driver.output = 'OFF'
            self.write_in_database('output', 'OFF')


class SetVoltageTask(InterfaceableTaskMixin, InstrumentTask):
    """Set a DC voltage to the specified value.
    """
    #: Target value for the source (dynamically evaluated)
    value = Str().tag(pref=True, feval=validators.SkipLoop(types=numbers.Real))
    wait_time = Float().tag(pref=True)
    unit = Enum('V', 'mV', 'uV').tag(pref=True)
    database_entries = set_default({'voltage': 0.01})

    def i_perform(self, value=None):
        if value is None:
            value = self.format_and_eval_string(self.value)
        value = self.convert(value, 'V')
        print('Setting voltage to {}'.format(value))
        time.sleep(self.wait_time)
        self.driver.voltage = value
        self.write_in_database('voltage', value)

    def check(self, *args, **kwargs):
        """Add the unit into the database.

        """
        test, traceback = super(SetVoltageTask, self).check(*args, **kwargs)
        return test, traceback

    def convert(self, voltage, unit):
        """ Convert a voltage to the given unit.
        """
        print('Converting {} {} to {}'.format(voltage, self.unit, unit))
        print('Convertion factor: ', CONVERSION_FACTORS[self.unit][unit])
        return voltage*CONVERSION_FACTORS[self.unit][unit]


class MultiChannelSetVoltageInterface(TaskInterface):
    """Set a DC voltage to the specified value for the specified channel.

    """
    #: Id of the channel whose central frequency should be set.
    channel = Int(1).tag(pref=True)
    channel_driver = Value()

    def perform(self, value=None):
        """Set the Voltage of the specified channel.

        """
        task = self.task
        if not self.channel_driver:
            self.channel_driver = task.driver.get_channel(self.channel)

        task.driver.owner = task.name
        self.channel_driver.owner = task.name

        if value is None:
            value = task.format_and_eval_string(task.value)
        time.sleep(task.wait_time)
        self.channel_driver.voltage = value
        task.write_in_database('voltage', value)

    def check(self, *args, **kwargs):
        """Make sure the specified channel does exists on the instrument.

        """
        test, tb = super(MultiChannelSetVoltageInterface, self).check(*args, **kwargs)
        task = self.task
        res = check_channels_presence(task, [self.channel], *args, **kwargs)
        tb.update(res[1])
        return test and res[0], tb


class SetCurrentTask(InterfaceableTaskMixin, InstrumentTask):
    """Set a DC Current to the specified value.
    """
    #: Target value for the source (dynamically evaluated)
    value = Str().tag(pref=True, feval=validators.SkipLoop(types=numbers.Real))
    wait_time = Float().tag(pref=True)
    unit = Enum('A', 'mA', 'μA', 'nA').tag(pref=True)
    database_entries = set_default({'current': 0.01})

    def i_perform(self, value=None):
        if value is None:
            value = self.value
            value = self.format_and_eval_string(value)
        time.sleep(self.wait_time)
        self.driver.current = value
        self.write_in_database('current', value)

    def check(self, *args, **kwargs):
        test, traceback = super(SetCurrentTask, self).check(*args, **kwargs)
        return test, traceback


class MultiChannelSetCurrentInterface(TaskInterface):
    """Set a DC Current to the specified value for the specified channel.

    """
    #: Id of the channel whose central frequency should be set.
    channel = Int(1).tag(pref=True)
    channel_driver = Value()

    def perform(self, value=None):
        """Set the current output of the specified channel.

        """
        task = self.task
        if not self.channel_driver:
            self.channel_driver = task.driver.get_channel(self.channel)

        task.driver.owner = task.name
        self.channel_driver.owner = task.name

        if value is None:
            value = task.format_and_eval_string(task.value)

        self.channel_driver.current = value
        task.write_in_database('current', value)

    def check(self, *args, **kwargs):
        """Make sure the specified channel does exists on the instrument.

        """
        test, tb = super(MultiChannelSetCurrentInterface, self).check(*args, **kwargs)
        task = self.task
        res = check_channels_presence(task, [self.channel], *args, **kwargs)
        tb.update(res[1])
        return test and res[0], tb


class GetVoltageTask(InterfaceableTaskMixin, InstrumentTask):
    """Get DC voltage from the device
    """
    wait_time = Float().tag(pref=True)
    database_entries = set_default({'voltage': np.array([0.00])})

    def i_perform(self, value=None):
        if self.driver.owner != self.name:
            self.driver.owner = self.name
        time.sleep(self.wait_time)
        current_value = self.driver.read_voltage_dc()
        #getattr(self.driver, 'voltage')
        self.write_in_database('voltage', float(current_value))
        #time.sleep(self.wait_time)
        #value = self.driver.voltage
        #self.write_in_database('voltage', float(value))

    def check(self, *args, **kwargs):
        test, traceback = super(GetVoltageTask, self).check(*args, **kwargs)
        return test, traceback


class MultiChannelGetVoltageInterface(TaskInterface):
    """Get DC voltage from the device from the specified channel.

    """
    #: Id of the channel whose central frequency should be set.
    channel = Int(1).tag(pref=True)
    channel_driver = Value()

    def perform(self):
        """Get the voltage from the specified channel.

        """
        task = self.task
        if not self.channel_driver:
            self.channel_driver = task.driver.get_channel(self.channel)
        task.driver.owner = task.name
        self.channel_driver.owner = task.name
        time.sleep(task.wait_time)
        value = self.channel_driver.voltage
        task.write_in_database('voltage', float(value))

    def check(self, *args, **kwargs):
        """Make sure the specified channel does exists on the instrument.

        """
        test, tb = super(MultiChannelGetVoltageInterface, self).check(*args, **kwargs)
        task = self.task
        res = check_channels_presence(task, [self.channel], *args, **kwargs)
        tb.update(res[1])
        return test and res[0], tb


class GetCurrentTask(InterfaceableTaskMixin, InstrumentTask):
    """Get the current
    """
    wait_time = Float().tag(pref=True)
    database_entries = set_default({'current': 0.00})

    def i_perform(self, value=None):
        if self.driver.owner != self.name:
            self.driver.owner = self.name
        time.sleep(self.wait_time)
        value = self.driver.current
        self.write_in_database('current', float(value))

    def check(self, *args, **kwargs):
        """Add the unit into the database.

        """
        test, traceback = super(GetCurrentTask, self).check(*args, **kwargs)
        return test, traceback


class MultiChannelGetCurrentInterface(TaskInterface):
    """Get the current from the specified channel.

    """
    #: Id of the channel whose current has to be read
    channel = Int(1).tag(pref=True)
    channel_driver = Value()

    def perform(self, value=None):
        """Read the current from the specific channel

        """
        task = self.task
        if not self.channel_driver:
            self.channel_driver = task.driver.get_channel(self.channel)
        task.driver.owner = task.name
        self.channel_driver.owner = task.name
        time.sleep(task.wait_time)
        value = self.channel_driver.current
        task.write_in_database('current', float(value))

    def check(self, *args, **kwargs):
        """Make sure the specified channel does exist on the instrument.

        """
        test, tb = super(MultiChannelGetCurrentInterface, self).check(*args, **kwargs)
        task = self.task
        res = check_channels_presence(task, [self.channel], *args, **kwargs)
        tb.update(res[1])
        return test and res[0], tb


class SetDummyTask(InterfaceableTaskMixin, InstrumentTask):
    """Get the current
    """
    wait_time = Float().tag(pref=True)
    database_entries = set_default({'current': 0.00})
    defined_channel = Int(1).tag(pref=True)
    defined_channels = List().tag(pref=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.defined_channels.items = self.driver.defined_channels
        except AttributeError:
            self.defined_channels.items = [1,2,3,4]

    def i_perform(self, value=None):
        if self.driver.owner != self.name:
            self.driver.owner = self.name
        time.sleep(self.wait_time)
        value = self.driver.current
        self.write_in_database('current', float(value))

    def check(self, *args, **kwargs):
        """Add the unit into the database.
        """

        test, traceback = super(SetDummyTask, self).check(*args, **kwargs)
        return test, traceback
