# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Driver for the Rohde and Schwartz VNA ZNB20.

"""
import logging
from inspect import cleandoc
import numpy as np
import re
from textwrap import fill

try:
    from visa import ascii, single, double
except ImportError:
    ascii = 2
    single = 1
    double = 3

from ..driver_tools import (BaseInstrument, InstrIOError, InstrError,
                            secure_communication, instrument_property)
from ..visa_tools import VisaInstrument
from visa import VisaTypeError


FORMATTING_DICT = {'PHAS': lambda x: np.angle(x, deg=True),
                   'MLIN': np.abs,
                   'MLOG': lambda x: 10*np.log10(np.abs(x)),
                   'REAL': np.real,
                   'IMAG': np.imag}


class ZNB20ChannelError(Exception):
    """ZNB20 channel related error.

    """
    pass


class ZNB20Channel(BaseInstrument):
    """Object representing a channel on the ZNB20.

    """
    caching_permissions = {'frequency': True,
                           'power': True,
                           'selected_measure': True,
                           'if_bandwidth': True,
                           'sweep_type': True,
                           'sweep_points': True,
                           'average_state': True,
                           'average_count': True,
                           'average_mode': True}

    def __init__(self, pna, channel_num, caching_allowed=True,
                 caching_permissions={}):
        super(ZNB20Channel, self).__init__(None, caching_allowed,
                                           caching_permissions)
        self._pna = pna
        self._channel = channel_num
        self.port = 1

    def reopen_connection(self):
        """
        """
        self._pna.reopen_connection()

    # TODO ZL needs checking
    @secure_communication()
    def read_formatted_data(self, meas_name=''):
        """ Read formatted data for a measure.

        Parameters
        ----------
        meas_name : str
            Name of the measure which should be read. If not provided the data
            for the currently selected measure will be read. This measure will
            be the new selected measure once this function returns.

        Returns
        -------
        data : numpy.array
            Array of Floating points holding the data.

        """
        if meas_name:
            self.selected_measure = meas_name
        else:
            meas_name = self.selected_measure

        data_request = 'CALCulate{}:DATA? FDATA'.format(self._channel)
        if self._pna.data_format == 'REAL,32':
            data = self._pna.ask_for_values(data_request, single)

        elif self._pna.data_format == 'REAL,64':
            data = self._pna.ask_for_values(data_request, double)

        else:
            data = self._pna.ask_for_values(data_request, ascii)

        if data:
            return np.array(data)
        else:
            raise InstrIOError(cleandoc('''ZNB20 did not return the
                channel {} formatted data for meas {}'''.format(
                self._channel, meas_name)))

    # TODO ZL needs checking
    @secure_communication()
    def read_raw_data(self, meas_name=''):
        """ Read raw data for a measure.

        Parameters
        ----------
        meas_name : str, optional
            Name of the measure which should be read. If not provided the data
            for the currently selected measure will be read. This measure will
            be the new selected measure once this function returns.

        Returns
        -------
        data : numpy.array
            Array of Floating points holding the data.

        """
        if meas_name:
            self.selected_measure = meas_name

        data_request = 'CALCulate{}:DATA? SDATA'.format(self._channel)
        if self._pna.data_format == 'REAL,32':
            data = self._pna.ask_for_values(data_request, single)

        elif self._pna.data_format == 'REAL,64':
            data = self._pna.ask_for_values(data_request, double)

        else:
            data = self._pna.ask_for_values(data_request, ascii)

        if not meas_name:
            meas_name = self.selected_measure

        if data:
            aux = np.array(data)
            return aux[::2] + 1j*aux[1::2]
        else:
            raise InstrIOError(cleandoc('''ZNB20 did not return the
                channel {} formatted data for meas {}'''.format(
                self._channel, meas_name)))

    # TODO ZL needs checking
    def read_and_format_raw_data(self, meas_format, meas_name=''):
        """
        """
        data = self.read_raw_data(meas_name)
        return FORMATTING_DICT[meas_format](data)

    # TODO ZL needs checking
    @secure_communication()
    def run_averaging(self, aver_count=''):
        """ Restart averaging on the channel and wait until it is over

        Parameters
        ----------
        aver_count : str, optional
            Number of averages to perform. Default value is the current one
        """
        self._pna.trigger_source = 'Immediate'
        self.sweep_mode = 'Hold'
        self._pna.clear_averaging()
        self._pna.timeout = 10

        if aver_count:
            self.average_count = aver_count

        self.average_state = 1
        for i in range(0, int(self.average_count)):
            while True:
                try:
                    done = self._pna.ask_for_values('*OPC?')[0]
                    break
                except Exception:
                    self._pna.timeout = self._pna.timeout*2
                    logger = logging.getLogger(__name__)
                    msg = cleandoc('''ZNB20 timeout increased to {} s
                        This will make the ZNB20 diplay 420 error w/o issue''')
                    logger.info(msg.format(self._pna.timeout))

            if done != 1:
                raise InstrError(cleandoc('''ZNB20 did could  not perform
                the average on channel {} '''.format(self._channel)))

    @secure_communication()
    def list_existing_measures(self):
        """
        """
        request = 'CALCulate{}:PARameter:CATalog:SENDed?'
        meas = self._pna.ask(request.format(self._channel))

        if meas:
            if meas == "''":
                return []
            param = meas[1:-1].split(',')
            aux = [{'name': param[2*i], 'parameters': param[2*i+1]}
                   for i in range(int(len(param)/2))]
            return aux
        else:
            raise InstrIOError(cleandoc('''ZNB20 did not return the
                    channel {} selected measure'''.format(self._channel)))

    @secure_communication()
    def create_meas(self, meas_name):
        """
        """
        catalog_request = 'CALCulate{}:PARameter:CATalog:SENDed?'

        param = meas_name.split(':')[1]

        create_meas = "CALCulate{}:PARameter:SDEFine '{}','{}'"
        self._pna.write(create_meas.format(self._channel,
                                           meas_name.replace(':', '_'),
                                           param))

        meas = self._pna.ask(catalog_request.format(self._channel))
        if meas:
            if param not in meas:
                mess = cleandoc('''The Pna did not create the
                    meas {} for channel {}'''.format(meas_name,
                                                     self._channel))
                raise InstrIOError(mess)

    # TODO ZL needs checking
    @secure_communication()
    def delete_meas(self, meas_name):
        """
        """
        self._pna.write(
            "CALCulate{}:PARameter:DELete '{}'".format(self._channel,
                                                       meas_name))
        meas = self._pna.ask('CALCulate{}:PARameter:CATalog:SENDed?'.format(
                             self._channel))
        if meas:
            if meas_name in meas:
                raise InstrIOError(cleandoc('''The Pna did not delete the meas
                {} for channel {}'''.format(meas_name, self._channel)))

    @secure_communication()
    def delete_all_meas(self):
        """
        """
        for meas in self.list_existing_measures():
            self._pna.write(
                "CALCulate{}:PARameter:DELete {}".format(self._channel,
                                                         meas['name']))
        self.clear_cache(['selected_measure'])
        if self.list_existing_measures():
            raise InstrIOError(cleandoc('''The Pna did not delete all meas
                for channel {}'''.format(self._channel)))

    @secure_communication()
    def format_meas(self, meas_format, meas_name=''):
        """
        """
        if meas_name:
            selected_meas = self.selected_measure
            self.selected_measure = meas_name
        self._pna.write('CALCulate{}:FORMat {}'.format(self._channel,
                                                       meas_format))
        res = self._pna.ask('CALCulate{}:FORMat?'.format(self._channel))
        if meas_name and selected_meas:
            self.selected_measure = selected_meas
        else:
            meas_name = self.selected_measure

        if res != meas_format:
            raise InstrIOError(cleandoc('''The Pna did not format the meas
                for channel {}'''.format(self._channel)))

    @secure_communication()
    def bind_meas_to_window(self, meas_name, window_num, trace_num):
        """
        """
        if window_num not in self._pna.windows:
            self._pna.write('DISPlay:WINDow{} ON'.format(window_num))

        self._pna.write("DISPlay:WINDow{}:TRACe{}:EFEed '{}'".
                        format(window_num, 1, meas_name.replace(':', '_')))

        traces = self._pna.ask('DISPlay:WINDow{}:TRACe1:CATalog?'.
                               format(window_num))
        if str(meas_name.replace(':', '_')) not in traces:
            raise InstrIOError(cleandoc('''The Pna did not bind the meas {}
                to window {}'''.format(meas_name, window_num)))

    def prepare_measure(self, meas_name, window_num, trace_num=1,
                        clear_window=True):
        """
        """
        info = meas_name.split(':')
        self.create_meas(meas_name)
        if len(info) > 2:
            if info[2] == '':
                measformat = 'POL'
            else:
                measformat = info[2]
            self.format_meas(measformat, meas_name)
        else:
            self.format_meas('MLIN', meas_name)
        if clear_window:
            if window_num in self._pna.windows:
                self._pna.clear_traces_from_window(window_num)
        self.bind_meas_to_window(meas_name, window_num, trace_num)

    @secure_communication()
    def prepare_sweep(self, sweep_type, start, stop, sweep_points):
        """
        """
        # TODO Add checks
        if sweep_type == 'FREQUENCY':
            self.sweep_type = 'LIN'
            self.sweep_points = sweep_points
            self._pna.write('SENSe{}:FREQuency:STARt {}'.format(self._channel,
                                                                start))
            self._pna.write('SENSe{}:FREQuency:STOP {}'.format(self._channel,
                                                               stop))
        elif sweep_type == 'POWER':
            self.sweep_type = 'POW'
            self.sweep_points = sweep_points
            self._pna.write('SOURce{}:POWer:STARt {}'.format(self._channel,
                                                             start))
            self._pna.write('SOURce{}:POWer:STOP {}'.format(self._channel,
                                                            stop))
        elif sweep_type == 'CW':
            self.sweep_type ='POINT'
            self.sweep_points = sweep_points
            self._pna.write('SENSe{}:FREQuency:CW {}'.format(self._channel,
                                                               start))
        else:
            raise ZNB20ChannelError(cleandoc('''Unsupported type of sweep
            : {} was specified for channel'''.format(sweep_type,
                                                     self._channel)))

    @instrument_property
    @secure_communication()
    def frequency(self):
        """Frequency getter method
        """
        freq = self._pna.ask_for_values('SENS{}:FREQuency:CENTer?'.format(
                                        self._channel))
        if freq:
            return freq[0]
        else:
            raise InstrIOError(cleandoc('''ZNB20 did not return the
                    channel {} frequency'''.format(self._channel)))

    @frequency.setter
    @secure_communication()
    def frequency(self, value):
        """Frequency setter method
        """
        self._pna.write('SENS{}:FREQuency:CENTer {}'.format(self._channel,
                                                            value))
        result = self._pna.ask_for_values('SENS{}:FREQuency:CENTer?'.format(
                                          self._channel))
        if result:
            if abs(result[0] - value)/value > 10**-12:
                raise InstrIOError(cleandoc('''ZNB20 did not set correctly the
                    channel {} frequency'''.format(self._channel)))
        else:
            raise InstrIOError(cleandoc('''ZNB20 did not set correctly the
                    channel {} frequency'''.format(self._channel)))

    @instrument_property
    @secure_communication()
    def tracenb(self):
        """Current trace number getter method

        WARNING: this command will not work if the trace selection has not been
        made by the software beforehand
        """
        trace_nb = self._pna.ask_for_values('CALC{}:PAR:MNUM?'.format(
            self._channel))
        if trace_nb:
            return trace_nb[0]
        else:
            raise InstrIOError(cleandoc('''ZNB20 did not return the
                    trace number on channel {} '''.format(self._channel)))

    @tracenb.setter
    @secure_communication()
    def tracenb(self, value):
        """Current trace number setter method
        """
        self._pna.write('CALC{}:PAR:MNUM {}'.format(self._channel, value))
        result = self._pna.ask_for_values('CALC{}:PAR:MNUM?'.format(
                                          self._channel))
        if result:
            if abs(result[0] - value)/value > 10**-12:
                raise InstrIOError(cleandoc('''ZNB20 could not set the
                    trace number {} on channel {}'''.format(value,
                                                            self._channel)))
        else:
            raise InstrIOError(cleandoc('''ZNB20 could not set the
                    trace number {} on channel {}'''.format(value,
                                                            self._channel)))

    @instrument_property
    @secure_communication()
    def sweep_x_axis(self):
        """List of values on the Sweep X axis getter method.

        """
        sweep_type = self.sweep_type
        sweep_points = self.sweep_points
        if sweep_type == 'LIN':
            sweep_start = self._pna.ask_for_values(
                'SENSe{}:FREQuency:STARt?'.format(self._channel))[0]*1e-9
            sweep_stop = self._pna.ask_for_values(
                'SENSe{}:FREQuency:STOP?'.format(self._channel))[0]*1e-9
            return np.linspace(sweep_start, sweep_stop, sweep_points)
        elif sweep_type == 'POW':
            sweep_start = self._pna.ask_for_values('SOURce{}:POWer:STARt?'
                                                   .format(self._channel))[0]
            sweep_stop = self._pna.ask_for_values('SOURce{}:POWer:STOP?'
                                                  .format(self._channel))[0]
            return np.linspace(sweep_start, sweep_stop, sweep_points)
        elif sweep_type == 'LOG':
            sweep_start = self._pna.ask_for_values(
                            'SENSe{}:FREQuency:STARt?'
                            .format(self._channel))[0]*1e-9
            sweep_stop = self._pna.ask_for_values(
                            'SENSe{}:FREQuency:STOP?'
                            .format(self._channel))[0]*1e-9
            return np.logspace(sweep_start, sweep_stop, sweep_points)
        elif sweep_type == 'POIN' or sweep_type == 'POINT':
            frequency = self._pna.ask_for_values(
                            'SENSe{}:FREQuency:CW?'
                            .format(self._channel))[0]*1e-9
            return np.ones(sweep_points)*frequency
        else:
            raise InstrIOError(cleandoc('''Sweep type of ZNB20 not yet
                supported for channel {}'''.format(self._channel)))

    @instrument_property
    @secure_communication()
    def power(self):
        """Power getter method
        """
        power = self._pna.ask_for_values('SOUR{}:POWer{}:AMPL?'.format(
                                         self._channel,
                                         self.port))
        if power:
            return power[0]
        else:
            raise InstrIOError(cleandoc('''ZNB20 did not return the
                    channel {} power for port {}'''.format(self._channel,
                                                           self.port)))

    @power.setter
    @secure_communication()
    def power(self, value):
        """Power setter method
        """
        self._pna.write('SOUR{}:POWer{}:AMPL {}'.format(self._channel,
                                                        self.port,
                                                        value))
        result = self._pna.ask_for_values('SOUR{}:POWer{}:AMPL?'.format(
                                          self._channel,
                                          self.port))
        if result:
            if abs(result[0] > value) > 10**-12:
                raise InstrIOError(cleandoc('''ZNB20 did not set correctly the
                    channel {} power for port {}'''.format(self._channel,
                                                           self.port)))
        else:
            raise InstrIOError(cleandoc('''ZNB20 did not set correctly the
                    channel {} power for port {}'''.format(self._channel,
                                                           self.port)))

    @instrument_property
    @secure_communication()
    def selected_measure(self):
        """Name of the selected measurement

        WARNING: this command will not work if the trace selection has not been
        made by the software beforehand
        """
        meas = self._pna.ask('CALC{}:PARameter:SELect?'.format(self._channel))
        if meas:
            return meas[1:-1]
        else:
            raise InstrIOError(cleandoc('''ZNB20 did not return the
                    channel {} selected measure'''.format(self._channel)))

    @selected_measure.setter
    @secure_communication()
    def selected_measure(self, value):
        """
        """
        value = value.replace(':', '_')
        mess0 = "CALC{}:PARameter:SELect '{}'".format(self._channel, value)
        self._pna.write(mess0)
        mess = 'CALC{}:PARameter:SELect?'.format(self._channel)
        result = self._pna.ask(mess)
        if result:
            if result[1:-1] != value:
                raise InstrIOError(cleandoc('''ZNB20 did not set correctly the
                    channel {} selected measure'''.format(self._channel)))

    @instrument_property
    @secure_communication()
    def if_bandwidth(self):
        """
        """
        if_bw = self._pna.ask_for_values('SENSe{}:BANDwidth?'.format(
                                         self._channel))
        if if_bw:
            return if_bw[0]
        else:
            raise InstrIOError(cleandoc('''ZNB20 did not return the
                    channel {} IF bandwidth'''.format(self._channel)))

    @if_bandwidth.setter
    @secure_communication()
    def if_bandwidth(self, value):
        """
        """
        self._pna.write('SENSe{}:BANDwidth {}'.format(self._channel, value))
        result = self._pna.ask_for_values('SENSe{}:BANDwidth?'.format(
                                          self._channel))
        if result:
            if abs(result[0] > value) > 10**-12:
                raise InstrIOError(cleandoc('''ZNB20 did not set correctly the
                    channel {} IF bandwidth'''.format(self._channel)))
        else:
            raise InstrIOError(cleandoc('''ZNB20 did not set correctly the
                    channel {} IF bandwidth'''.format(self._channel)))

    @instrument_property
    @secure_communication()
    def sweep_mode(self):
        """
        """
        mode = self._pna.ask('SENSe{}:SWEep:MODE?'.format(self._channel))
        if mode:
            return mode
        else:
            raise InstrIOError(cleandoc('''ZNB20 did not return the
                    channel {} sweep mode'''.format(self._channel)))

    @sweep_mode.setter
    @secure_communication()
    def sweep_mode(self, value):
        """
        """
        self._pna.write('SENSe{}:SWEep:MODE {}'.format(self._channel, value))
        result = self._pna.ask('SENSe{}:SWEep:MODE?'.format(self._channel))

        if result.lower() != value.lower()[:len(result)]:
            raise InstrIOError(cleandoc('''ZNB20 did not set correctly the
                channel {} sweep mode'''.format(self._channel)))

    @instrument_property
    @secure_communication()
    def sweep_type(self):
        """
        """
        sweep_type = self._pna.ask('SENSe{}:SWEep:Type?'.format(self._channel))
        if sweep_type:
            return sweep_type
        else:
            raise InstrIOError(cleandoc('''ZNB20 did not return the
                    channel {} sweep type'''.format(self._channel)))

    @sweep_type.setter
    @secure_communication()
    def sweep_type(self, value):
        """
        """
        self._pna.write('SENSe{}:SWEep:TYPE {}'.format(self._channel, value))
        result = self._pna.ask('SENSe{}:SWEep:TYPE?'.format(self._channel))

        if result.lower() != value.lower()[:len(result)]:
            raise InstrIOError(cleandoc('''ZNB20 did not set correctly the
                channel {} sweep type'''.format(self._channel)))

    @instrument_property
    @secure_communication()
    def sweep_points(self):
        """
        """
        points = self._pna.ask_for_values('SENSe{}:SWEep:POINts?'.format(
                                          self._channel))
        if points:
            return int(points[0])
        else:
            raise InstrIOError(cleandoc('''ZNB20 did not return the
                    channel {} sweep point number'''.format(self._channel)))

    @sweep_points.setter
    @secure_communication()
    def sweep_points(self, value):
        """
        """
        self._pna.write('SENSe{}:SWEep:POINts {}'.format(self._channel, value))
        result = self._pna.ask_for_values('SENSe{}:SWEep:POINts?'.format(
                                          self._channel))
        if result:
            if result[0] != value:
                raise InstrIOError(cleandoc('''ZNB20 not set correctly the
                    channel {} sweep point number'''.format(self._channel)))
        else:
            raise InstrIOError(cleandoc('''ZNB20 did not set correctly the
                    channel {} sweep point number'''.format(self._channel)))

    @instrument_property
    @secure_communication()
    def sweep_time(self):
        """Sweep time in seconds
        """
        time = self._pna.ask_for_values('sense{}:sweep:time?'.format(
            self._channel))
        if time:
            return time[0]
        else:
            raise InstrIOError(cleandoc('''ZNB20 did not return the
                    channel {} sweep point number'''.format(self._channel)))

    @sweep_time.setter
    @secure_communication()
    def sweep_time(self, value):
        """
        """
        self._pna.write('sense{}:sweep:time {}'.format(self._channel, value))

    @instrument_property
    @secure_communication()
    def average_state(self):
        """
        """
        state = self._pna.ask('SENSe{}:AVERage:STATe?'.format(self._channel))
        if state:
            return bool(state)
        else:
            raise InstrIOError(cleandoc('''ZNB20 did not return the
                    channel {} average state'''.format(self._channel)))

    @average_state.setter
    @secure_communication()
    def average_state(self, value):
        """
        """
        self._pna.write('SENSe{}:AVERage:STATe {}'.format(self._channel,
                        value))
        result = self._pna.ask('SENSe{}:AVERage:STATe?'.format(self._channel))

        if bool(result) != value:
            raise InstrIOError(cleandoc('''ZNB20 did not set correctly the
                channel {} average state'''.format(self._channel)))

    @instrument_property
    @secure_communication()
    def average_count(self):
        """
        """
        count = self._pna.ask_for_values('SENSe{}:AVERage:COUNt?'.format(
                                         self._channel))
        if count:
            return count[0]
        else:
            raise InstrIOError(cleandoc('''ZNB20 did not return the
                    channel {} average count'''.format(self._channel)))

    @average_count.setter
    @secure_communication()
    def average_count(self, value):
        """
        """

        self._pna.write('SENSe{}:AVERage:COUNt {}'.format(self._channel,
                        value))
        self._pna.write('SENSe{}:SWE:GRO:COUNt {}'.format(self._channel,
                        value))
        result = self._pna.ask_for_values('SENSe{}:AVERage:COUNt?'.format(
                                          self._channel))
        if result:
            if result[0] == value:
                raise InstrIOError(cleandoc('''ZNB20 did not set correctly the
                    channel {} average count'''.format(self._channel)))
        else:
            raise InstrIOError(cleandoc('''ZNB20 did not set correctly the
                    channel {} average count'''.format(self._channel)))

    @instrument_property
    @secure_communication()
    def average_mode(self):
        """
        """
        mode = self._pna.ask('SENSe{}:AVERage:MODE?'.format(self._channel))
        if mode:
            return mode
        else:
            raise InstrIOError(cleandoc('''ZNB20 did not return the
                    channel {} average mode'''.format(self._channel)))

    @average_mode.setter
    @secure_communication()
    def average_mode(self, value):
        """
        """
        self._pna.write('SENSe{}:AVERage:MODE {}'.format(self._channel, value))
        result = self._pna.ask('SENSe{}:AVERage:MODE?'.format(self._channel))

        if result.lower() != value.lower()[:len(result)]:
            raise InstrIOError(cleandoc('''ZNB20 did not set correctly the
                channel {} average mode'''.format(self._channel)))

    @instrument_property
    @secure_communication()
    def electrical_delay(self):
        """electrical delay for the selected trace in ns
        """
        mode = self._pna.ask_for_values('CORRection:EDELay{}?'.format(
                                                    self._channel))
        if mode:
            return mode[0]*1000000000.0
        else:
            raise InstrIOError(cleandoc('''ZNB20 did not return the
                    channel {} electrical delay'''.format(self._channel)))

    @electrical_delay.setter
    @secure_communication()
    def electrical_delay(self, value):
        """
        electrical delay for the selected trace in ns
        """
        self._pna.write('CORRection:EDELay{} {}NS'.format(self._channel,
                                                          value))


class ZNB20(VisaInstrument):
    """
    """

    caching_permissions = {'defined_channels': True,
                           'trigger_scope': True,
                           'data_format': True}

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):
        super(ZNB20, self).__init__(connection_info, caching_allowed,
                                    caching_permissions, auto_open)
        self.channels = {}

    def open_connection(self, **para):
        """Open the connection to the instr using the `connection_str`.

        """
        super(ZNB20, self).open_connection(**para)
        self.write_termination = '\n'
        self.read_termination = '\n'
        # clearing buffers to avoid running into queue overflow
        self.write('*CLS')

    def get_channel(self, num):
        """
        """
        if num not in self.defined_channels:
            return None

        if num in self.channels:
            return self.channels[num]
        else:
            channel = ZNB20Channel(self, num)
            self.channels[num] = channel
            return channel

    @secure_communication()
    def clear_traces_from_window(self, window_num):
        """
        """
        traces_list = self.ask('DISPlay:WINDow{}:TRACe:CATalog?'.
                               format(window_num))[1:-1].split(',')
        traces = [int(traces_list[2*ii])
                  for ii in range(int(len(traces_list)/2))]
        if len(traces) > 0:
            for trace in traces:
                mess = 'DISPlay:WINDow{}:TRACe{}:DELete'.format(window_num,
                                                                int(trace))
                self.write(mess)
            traces_list = self.ask('DISPlay:WINDow{}:TRACe:CATalog?'.
                                   format(window_num))[1:-1].split(',')
            traces = [int(traces_list[2*ii])
                      for ii in range(int(len(traces_list)/2))]
            if len(traces) > 0:
                raise InstrIOError(cleandoc('''ZNB20 did not clear all
                    traces from window {}'''.format(window_num)))

    # ZL for this to work, I needed to set trigger source to IMM
    @secure_communication()
    def fire_trigger(self, channel=None):
        """
        """
        if channel is None:
            self.write('INITiate:IMMediate')
        else:
            self.write('INITiate{}:IMMediate'.format(channel))
        self.write('*OPC')

    @secure_communication()
    def check_operation_completion(self):
        """
        """
        return bool(int(self.ask('*OPC?')))

    @secure_communication()
    def set_all_chanel_to_hold(self):
        """
        """
        for channel in self.defined_channels:
            self.write('INITiate{}:CONTinuous OFF'.format(channel))
            # TODO: find correct syntax to ask for sweep control state
# =============================================================================
#         for channel in self.defined_channels:
#             result = self.ask('SENSe{}:SWEep:MODE?'.format(channel))
#             if result != 'HOLD':
#                 raise InstrIOError(cleandoc('''ZNB20 did not set correctly
#                     the channel {} sweep mode while setting all
#                     defined channels
#                     to HOLD, instead channel mode is {}'''.
#                                    format(channel, result)))
# =============================================================================

    @secure_communication()
    def clear_averaging(self):
        """Clear and restart averaging of the measurement data.

        """
        self.write('SENS:AVER:CLE')

    @instrument_property
    @secure_communication()
    def defined_channels(self):
        """
        """
        channels = self.ask('CONFigure:CHANnel:CATalog?')
        if channels:
            channels_number_list = channels[1:-2].split(',')
            n_channels = int(len(channels_number_list)/2)
            defined_channels = [int(channels_number_list[2*ii])
                                for ii in range(n_channels)]
            return defined_channels
        else:
            raise InstrIOError(cleandoc('''ZNB20 did not return the
                    defined channels'''))

    @instrument_property
    @secure_communication()
    def get_all_trace_names(self):
        tracelist_raw = self.ask('CONFigure:TRACe:CATalog?')
        tracelist = tracelist_raw[1:-1].split(',')
        tracelist = np.reshape(tracelist, (int(len(tracelist)/2), 2))
        tracelist = tracelist[:, 1]
        return tracelist

    @instrument_property
    @secure_communication()
    def windows(self):
        """
        """
        windows = self.ask('DISPlay:CATalog?')
        if windows:
            windows_number_list = windows[1:-2].split(',')
            aux = [int(windows_number_list[2*ii])
                   for ii in range(int(len(windows_number_list)/2))]
            return aux
        else:
            raise InstrIOError(cleandoc('''ZNB20 did not return the
                    defined windows'''))

    # TODO ZL needs more checking
    @instrument_property
    @secure_communication()
    def trigger_scope(self):
        """
        """
        channel = self.defined_channels[0]
        scope = self.ask('INITiate'+format(channel)+':SCOPe?')
        if scope:
            if scope == 'SINGle' or scope == 'SING':
                scope = 'CURRent'
            return scope
        else:
            raise InstrIOError(cleandoc('''ZNB20 did not return the
                    trigger scope'''))

    @trigger_scope.setter
    @secure_communication()
    def trigger_scope(self, value):
        """
        """
        # translating the PNA to ZNB instruction
        if value == 'CURRent' or value == 'CURR':
            value = 'SINGle'
        channel = self.defined_channels[0]
        self.write('INITiate'+format(channel)+':SCOPe {}'.format(value))
        result = self.ask('INITiate'+format(channel)+':SCOPe?')

        if result.lower() != value.lower()[:len(result)]:
            raise InstrIOError(cleandoc('''ZNB20 did not set correctly the
                trigger scope'''))

    @instrument_property
    @secure_communication()
    def trigger_source(self):
        """
        """
        scope = self.ask('TRIGger:SEQuence:SOURce?')
        if scope:
            return scope
        else:
            raise InstrIOError(cleandoc('''ZNB20 did not return the
                    trigger source'''))

    @trigger_source.setter
    @secure_communication()
    def trigger_source(self, value):
        """
        """
        # ZL I am forcing this to 'IMM' so that
        # INITiate will start the measurement
        value = 'IMM'
        self.write('TRIGger:SEQuence:SOURce {}'.format(value))
        result = self.ask('TRIGger:SEQuence:SOURce?')

        if result.lower() != value.lower()[:len(result)]:
            raise InstrIOError(cleandoc('''ZNB20 did not set correctly the
                trigger source'''))

    @instrument_property
    @secure_communication()
    def data_format(self):
        """
        """
        data_format = self.ask('FORMAT:DATA?')
        if data_format:
            return data_format
        else:
            raise InstrIOError(cleandoc('''ZNB20 did not return the
                    data format'''))

    @data_format.setter
    @secure_communication()
    def data_format(self, value):
        """
        """
        self.write('FORMAT:DATA {}'.format(value))
        result = self.ask('FORMAT:DATA?')

        if result.lower() != value.lower()[:len(result)]:
            raise InstrIOError(cleandoc('''ZNB20 did not set correctly the
                data format'''))

    @instrument_property
    @secure_communication()
    def output(self):
        """Output state of the source.

        """
        output = self.ask_for_values(':OUTP?')
        if output is not None:
            return bool(output[0])
        else:
            mes = 'ZNB signal generator did not return its output'
            raise InstrIOError(mes)

    @output.setter
    @secure_communication()
    def output(self, value):
        """Output setter method.

        """
        on = re.compile('on', re.IGNORECASE)
        off = re.compile('off', re.IGNORECASE)
        if on.match(value) or value == 1:
            self.write(':OUTPUT ON')
            if self.ask(':OUTPUT?') != '1':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the output'''))
        elif off.match(value) or value == 0:
            self.write(':OUTPUT OFF')
            if self.ask(':OUTPUT?') != '0':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the output'''))
        else:
            mess = fill(cleandoc('''The invalid value {} was sent to
                        switch_on_off method''').format(value), 80)
            raise VisaTypeError(mess)
