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
from atom.api import Float, Value, Str, Int, set_default, Enum, Tuple, List
from collections import Iterable

# from ..validators import Feval
from exopy.tasks.api import (
    InstrumentTask,
    TaskInterface,
    InterfaceableTaskMixin,
    validators,
)


def check_channels_presence(task, channels, *args, **kwargs):
    """ Check that all the channels are correctly defined on the PNA.

    """
    if kwargs.get("test_instr"):
        traceback = {}
        err_path = task.get_error_path()
        with task.test_driver() as instr:
            if instr is None:
                return False, traceback
            channels_present = True
            for channel in channels:
                if channel not in instr.defined_channels:
                    key = err_path + "_" + str(channel)
                    msg = (
                        "Channel {} is not defined in the {}."
                        " Please define it yourself and try again."
                    )
                    traceback[key] = msg.format(channel, task.selected_instrument[0])

                    channels_present = False

            return channels_present, traceback

    else:
        return True, {}


class SetOutputFilterTask(InterfaceableTaskMixin, InstrumentTask):
    """
    Sets the output filter of the QDACII
    """

    # desired state of the filter
    # filter_state = Enum('DC', 'MID', 'HIGH').tag(oref=True)
    filter_state = Str("MEDIUM").tag(
        pref=True,
        # feval=validators.SkipLoop()
    )

    database_entries = set_default({"filter_state": "MEDIUM"})

    def i_perform(self, filter_state=None):
        """
        Default interface for single channel
        """
        # print
        if filter_state is None:
            filter_state = self.filter_state
        if filter_state == "DC":
            self.driver.output_filter = "DC"
            self.write_in_database("filter_state", "DC")
        elif filter_state == "MEDIUM":
            self.driver.output_filter = "MEDIUM"
            self.write_in_database("filter_state", "MEDIUM")
        elif filter_state == "HIGH":
            self.driver.output_filter = "HIGH"
            self.write_in_database("filter_state", "HIGH")


class MultiChannelQDacSettingsOutputFilter(TaskInterface):
    """Interface for multiple outputs sources.

    """

    #: Id of the channel to use.
    # channel = Tuple(default=(1, 1)).tag(pref=True)
    channel = Int(1).tag(pref=True)
    #: Reference to the driver for the channel.
    channel_driver = Value()

    def perform(self, value=None):
        """Set the specified voltage.

        """
        task = self.task
        if not self.channel_driver:
            self.channel_driver = task.driver.get_channel(self.channel)

        task.driver.owner = task.name
        self.channel_driver.owner = task.name

        if value is None:
            value = task.filter_state
        self.channel_driver.output_filter = value
        task.write_in_database("filter_state", value)

    def check(self, *args, **kwargs):
        if kwargs.get("test_instr"):
            task = self.task
            traceback = {}
            with task.test_driver() as d:
                if d is None:
                    return True, {}
                if self.channel not in d.defined_channels:
                    key = task.get_error_path() + "_interface"
                    traceback[key] = "Missing channel {}".format(self.channel)

            if traceback:
                return False, traceback
            else:
                return True, traceback

        else:
            return True, {}


class SetOutputRangeTask(InterfaceableTaskMixin, InstrumentTask):
    """
    Sets the output range of the QDACII
    """

    # desired state of the filter
    # filter_state = Enum('DC', 'MID', 'HIGH').tag(oref=True)
    desired_range = Str("LOW").tag(
        pref=True,
        # feval=validators.SkipLoop()
    )

    database_entries = set_default({"range": "LOW"})

    def i_perform(self, desired_range=None):
        """
        Default interface for single channel
        """
        # print
        if desired_range is None:
            desired_range = self.desired_range
            # print(filter_state)
        if desired_range == "LOW":
            self.driver.output_range = "LOW"
            self.write_in_database("range", "LOW")
        elif desired_range == "HIGH":
            self.driver.output_range = "HIGH"
            self.write_in_database("range", "HIGH")


class MultiChannelQDacSettingsOutputRange(TaskInterface):
    """Interface for multiple outputs sources.

    """

    #: Id of the channel to use.
    # channel = Tuple(default=(1, 1)).tag(pref=True)
    channel = Int(1).tag(pref=True)
    #: Reference to the driver for the channel.
    channel_driver = Value()

    def perform(self, value=None):
        """Set the specified voltage.

        """
        task = self.task
        if not self.channel_driver:
            self.channel_driver = task.driver.get_channel(self.channel)

        task.driver.owner = task.name
        self.channel_driver.owner = task.name

        if value is None:
            value = task.desired_range
        self.channel_driver.output_range = value
        task.write_in_database("range", value)

    def check(self, *args, **kwargs):
        if kwargs.get("test_instr"):
            task = self.task
            traceback = {}
            with task.test_driver() as d:
                if d is None:
                    return True, {}
                if self.channel not in d.defined_channels:
                    key = task.get_error_path() + "_interface"
                    traceback[key] = "Missing channel {}".format(self.channel)

            if traceback:
                return False, traceback
            else:
                return True, traceback

        else:
            return True, {}


class SendListAndInit(InterfaceableTaskMixin, InstrumentTask):
    """
    initializes the list mode and send the list of values
    """

    # desired state of the filter
    # filter_state = Enum('DC', 'MID', 'HIGH').tag(oref=True)
    trigger_source = Str("EXT1").tag(
        pref=True,
        # feval=validators.SkipLoop()
    )
    voltage_list = Str("np.linspace(-1,1,11)").tag(
        pref=True, feval=validators.Feval(types=Iterable)
    )

    database_entries = set_default(
        {"trigger_source": "EXT1", "voltage_list": np.array([0])}
    )
    # database_entries = set_default({'sweep_data': np.array([0])})
    def i_perform(self, trigger_source=None, voltage_list=None):
        """
        Default interface for single channel
        """
        # print
        if trigger_source is None:
            trigger_source = self.trigger_source
        if trigger_source == "EXT1":
            self.driver.trigger_source = "EXT1"
            self.write_in_database("trigger_source", "EXT1")
        elif trigger_source == "EXT2":
            self.driver.trigger_source = "EXT2"
            self.write_in_database("trigger_source", "EXT2")
        elif trigger_source == "EXT3":
            self.driver.trigger_source = "EXT3"
            self.write_in_database("trigger_source", "EXT3")
        elif trigger_source == "IMM":
            self.driver.trigger_source = "IMM"
            self.write_in_database("trigger_source", "IMM")
        # TODO: implement a smooth_set for the 1st value
        if voltage_list is None:
            voltage_list = self.format_and_eval_string(self.voltage_list)
            self.driver.channel_mode = "FIX"
            self.driver.voltage = np.array(voltage_list)[0]
            self.driver.list_values = np.array(voltage_list)
            self.driver.list_parameter_count = "INF"
            self.driver.list_trigger_mode = "STEP"
            # self.driver.voltage = voltage_list[0]
            self.write_in_database("voltage_list", np.array(voltage_list))


class MultiChannelQDacSendListAndInit(TaskInterface):
    """Interface for multiple outputs sources.

    """

    #: Id of the channel to use.
    # channel = Tuple(default=(1, 1)).tag(pref=True)
    channel = Int(1).tag(pref=True)
    #: Reference to the driver for the channel.
    channel_driver = Value()

    def perform(
        self,
        trigger_source=None,
        list_values=None,
        trigger_mode=None,
        parameter_count=None,
    ):
        """Set the specified voltage.

        """
        task = self.task
        if not self.channel_driver:
            self.channel_driver = task.driver.get_channel(self.channel)

        task.driver.owner = task.name
        self.channel_driver.owner = task.name

        if trigger_source is None:
            self.channel_driver.trigger_source = task.trigger_source
            task.write_in_database("trigger_source", task.trigger_source)

        if list_values is None:
            list_values = task.format_and_eval_string(task.voltage_list)
            self.channel_driver.list_values = task.format_and_eval_string(
                task.voltage_list
            )
            task.write_in_database("voltage_list", list_values)
            self.channel_driver.channel_mode = "FIX"
            self.channel_driver.voltage = np.array(list_values)[0]

        if trigger_mode is None:
            self.channel_driver.list_trigger_mode = "STEP"

        if parameter_count is None:
            self.channel_driver.list_parameter_count = "INF"
            self.channel_driver.channel_mode = "LIST"

    def check(self, *args, **kwargs):
        if kwargs.get("test_instr"):
            task = self.task
            traceback = {}
            with task.test_driver() as d:
                if d is None:
                    return True, {}
                if self.channel not in d.defined_channels:
                    key = task.get_error_path() + "_interface"
                    traceback[key] = "Missing channel {}".format(self.channel)

            if traceback:
                return False, traceback
            else:
                return True, traceback

        else:
            return True, {}


class SetOutputModeTask(InterfaceableTaskMixin, InstrumentTask):
    """
    Sets the output range of the QDACII
    """

    # desired state of the filter
    # filter_state = Enum('DC', 'MID', 'HIGH').tag(oref=True)
    desired_mode = Str("FIX").tag(
        pref=True,
        # feval=validators.SkipLoop()
    )

    database_entries = set_default({"mode": "FIX"})

    def i_perform(self, desired_mode=None):
        """
        Default interface for single channel
        """
        # print
        if desired_mode is None:
            desired_mode = self.desired_mode
            # print(filter_state)
        if desired_mode == "FIX":
            self.driver.channel_mode = "FIX"
            self.write_in_database("mode", "FIX")
        elif desired_mode == "LIST":
            self.driver.channel_mode = "LIST"
            self.write_in_database("mode", "LIST")


class MultiChannelQDacSettingsOutputMode(TaskInterface):
    """Interface for multiple outputs sources.

    """

    #: Id of the channel to use.
    # channel = Tuple(default=(1, 1)).tag(pref=True)
    channel = Int(1).tag(pref=True)
    #: Reference to the driver for the channel.
    channel_driver = Value()

    def perform(self, value=None):
        """Set the specified voltage.

        """
        task = self.task
        if not self.channel_driver:
            self.channel_driver = task.driver.get_channel(self.channel)

        task.driver.owner = task.name
        self.channel_driver.owner = task.name

        if value is None:
            value = task.desired_mode
        self.channel_driver.output_range = value
        task.write_in_database("mode", value)

    def check(self, *args, **kwargs):
        if kwargs.get("test_instr"):
            task = self.task
            traceback = {}
            with task.test_driver() as d:
                if d is None:
                    return True, {}
                if self.channel not in d.defined_channels:
                    key = task.get_error_path() + "_interface"
                    traceback[key] = "Missing channel {}".format(self.channel)

            if traceback:
                return False, traceback
            else:
                return True, traceback

        else:
            return True, {}