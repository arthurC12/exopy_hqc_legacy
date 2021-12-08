# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Task to measure DC properties.

"""
from time import sleep

from atom.api import Float, Int, Value, set_default, List

from exopy.tasks.api import InstrumentTask, InterfaceableTaskMixin, TaskInterface



# def check_channels_presence(task, channels, *args, **kwargs):
#     """ Check that all the channels are correctly defined on the PNA.

#     """
#     if kwargs.get('test_instr'):
#         traceback = {}
#         err_path = task.get_error_path()
#         with task.test_driver() as instr:
#             if instr is None:
#                 return False, traceback
#             channels_present = True
#             for channel in channels:
#                 if channel not in instr.defined_channels:
#                     key = err_path + '_' + str(channel)
#                     msg = ("Channel {} is not defined in the {}."
#                            " Please define it yourself and try again.")
#                     traceback[key] = msg.format(channel,
#                                                 task.selected_instrument[0])

#                     channels_present = False

#             return channels_present, traceback

#     else:
#         return True, {}


class MeasDCVoltageTask(InstrumentTask):
    """Measure a dc voltage.

    Wait for any parallel operation before execution and then wait the
    specified time before perfoming the measure.

    """
    # Time to wait before the measurement.
    wait_time = Float().tag(pref=True)

    database_entries = set_default({'voltage': 1.0})

    wait = set_default({'activated': True, 'wait': ['instr']})

    def perform(self):
        """Wait and read the DC voltage.

        """
        sleep(self.wait_time)

        value = self.driver.read_voltage_dc()
        self.write_in_database('voltage', value)


# class MultiChannelMeasDCVoltageInterface(TaskInterface):
#     """Measure a dc voltage from a multichannel device

#     Wait for any parallel operation before execution and then wait the
#     specified time before performing the measure.

#     """
#     # Channel
#     channel = Int(1).tag(pref=True)
#     #: Driver for the channel.
#     channel_driver = Value()
#     # wait_time = Float().tag(pref=True)
#     # database_entries = set_default({'voltage': 1.0})
#     defined_channels = List()
#     def perform(self):
#         """Set the voltage of the specified channel.

#         """
#         task = self.task
#         if not self.channel_driver:
#             self.channel_driver = task.driver.get_channel(self.channel)
#         task.driver.owner = task.name
#         self.channel_driver.owner = task.name
#         sleep(task.wait_time)
#         value = self.channel_driver.voltage#read_voltage_dc()
#         task.write_in_database('voltage', value)

#     def check(self, *args, **kwargs):
#         """Make sure the specified channel does exist on the instrument.

#         """
#         self.defined_channels = self.task.driver.defined_channels
#         test, tb = super(MultiChannelMeasDCVoltageInterface,self).check(*args, **kwargs)
#         task = self.task
#         res = check_channels_presence(task, [self.channel], *args, **kwargs)
#         tb.update(res[1])
#         return test and res[0], tb


class MeasDCCurrentTask(InstrumentTask):
    """Measure a dc current.

    Wait for any parallel operation before execution and then wait the
    specified time before perfoming the measure.

    """
    # Time to wait before the measurement.
    wait_time = Float().tag(pref=True)

    database_entries = set_default({'current': 1.0})

    wait = set_default({'activated': True, 'wait': ['instr']})

    def perform(self):
        """Wait and read the DC voltage.

        """
        sleep(self.wait_time)

        value = self.driver.current
        self.write_in_database('current', value)
