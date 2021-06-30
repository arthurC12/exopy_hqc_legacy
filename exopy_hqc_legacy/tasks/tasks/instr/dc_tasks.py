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

from atom.api import (Float, Value, Str, Int, List, set_default, Enum, Tuple)

from exopy.tasks.api import (InstrumentTask, TaskInterface,
                            InterfaceableTaskMixin, validators)

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

        current_value = getattr(self.driver, 'voltage')
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

    #: Largest allowed delta compared to current voltage. 0 = ignored
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
    database_entries = set_default({'voltage': 0.01})
    def perform(self, value=None):
        value = self.format_and_eval_string(self.value)
        time.sleep(self.wait_time)
        self.driver.voltage = value
        self.write_in_database('voltage', value)


class MultiChannelSetVoltageInterface(TaskInterface):
    """Set the central frequency to be used for the specified channel.

    """
    #: Id of the channel whose central frequency should be set.
    channel = Int(1).tag(pref=True)
    channel_driver = Value()

    def perform(self, value=None):
        """Set the central frequency of the specified channel.

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
    """Set a DC voltage to the specified value.
    """
    #: Target value for the source (dynamically evaluated)
    value = Str().tag(pref=True, feval=validators.SkipLoop(types=numbers.Real))
    wait_time = Float().tag(pref=True)
    database_entries = set_default({'current': 0.01})
    def perform(self, value=None):
        value = self.format_and_eval_string(self.value)
        time.sleep(self.wait_time)
        self.driver.current = value
        self.write_in_database('current', value)


class MultiChannelSetCurrentInterface(TaskInterface):
    """Set the central frequency to be used for the specified channel.

    """
    #: Id of the channel whose central frequency should be set.
    channel = Int(1).tag(pref=True)
    channel_driver = Value()

    def perform(self, value=None):
        """Set the central frequency of the specified channel.

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
    """Set a DC voltage to the specified value.
    """
    #: Target value for the source (dynamically evaluated)
    value = Str().tag(pref=True, feval=validators.SkipLoop(types=numbers.Real))
    wait_time = Float().tag(pref=True)
    database_entries = set_default({'voltage': 0.01})

    def perform(self):
        time.sleep(self.wait_time)
        value = self.driver.voltage
        self.write_in_database('voltage', float(value))


class MultiChannelGetVoltageInterface(TaskInterface):
    """Set the central frequency to be used for the specified channel.

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
    #: Target value for the source (dynamically evaluated)
    wait_time = Float().tag(pref=True)
    database_entries = set_default({'current': 0.01})

    def perform(self):
        time.sleep(self.wait_time)
        value = self.driver.current
        self.write_in_database('current', float(value))


class MultiChannelGetCurrentInterface(TaskInterface):
    """Get the current from the specified channel.

    """
    #: Id of the channel whose central frequency should be set.
    channel = Int(1).tag(pref=True)
    channel_driver = Value()
    
    def perform(self):
        """Set the central frequency of the specified channel.

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
        """Make sure the specified channel does exists on the instrument.

        """
        test, tb = super(MultiChannelGetCurrentInterface, self).check(*args, **kwargs)
        task = self.task
        res = check_channels_presence(task, [self.channel], *args, **kwargs)
        tb.update(res[1])
        return test and res[0], tb