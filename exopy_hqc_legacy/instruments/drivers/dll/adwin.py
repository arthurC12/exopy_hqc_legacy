# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Drivers for ADwin system using DLL library.

"""
#from ..driver_tools import (InstrIOError, secure_communication, instrument_property)

from ..dll_tools import DllInstrument
import numpy as np
import os
import time
import os.path
import ADwin


class Adwin(DllInstrument):
    """
    Driver for an Adwin Data Acquisition device, using the VISA library.

    Methods
    -------


    """
    def __init__(self, connection_info, caching_allowed=True, caching_permissions={}, auto_open=True):
        super().__init__(connection_info, caching_allowed,
                                         caching_permissions, auto_open)
        print('Connection_info:', connection_info)
        self.address = connection_info['instr_id'] or 0x1
        self.lib_dir = connection_info['lib_dir']
        #files = os.listdir(self.lib_dir)
        self._boot(18)
        #ind = 0
        #for file in files:
        #    if file[:-1].endswith('TB'):
        #        ind += 1
        #        print('Loading process #{}: '.format(ind))
        #        self._load_process(file)
        files = ['setvoltage.tb1', 'getvoltage.tb1']
        for ind, file in enumerate(files):
            print('Loading {} as process #{}'.format(file, ind+1))
            try:
                self._load_process(os.path.join(self.lib_dir, file))
            except ADwin.ADwinError as err:
                print(err)
        if auto_open:
            self.open_connection()

    def open_connection(self, **para):
        """Open the connection to the instr using the `connection_str`.

        """
        print('Open connection:', para)
        pass
        #self._adwin = ADwin.ADwin(self.address, 1)
        # super().open_connection(**para)
        # self.write_termination = ''
        # self.read_termination = ''
        # self._boot(18)

    def close_connection(self):
        pass

    def _record_IV(self, v, n):
        x = np.linspace(-v, v, n)
        y = 0.01*x
        return x, y

    def set_voltage(self, voltage, out_channel=1, in_channel=1, process_delay=0.00):
        debug = False
        if debug:
            print('Output {}V on channel {}, taking {} from channel {}'.format(voltage, out_channel, 0.2*voltage, in_channel))
            return 0.2*voltage
        else:
            output_range = 10.0
            input_range = 10.0
            resolution_output = 16
            resolution_input = 18
            out_bin, voltage = Adwin.convert_V_to_bin(voltage, output_range, resolution_output)
            refresh_rate = 100 # Hz
            self._set_Par(1, out_bin)
            self._set_Par(2, out_channel)
            self._set_Par(3, in_channel)
            self._set_Par(5, int(1))  # process is still running
            self._start_process(1)  # setvoltage.tb1
            check = True
            while check:
                if self._get_Par(5) == 1:
                    time.sleep(1 / refresh_rate)
                else:
                    self._stop_process(1)
                    check = False
            self._set_Par(5, int(1))
            time.sleep(process_delay)
            self._start_process(2)  # getvoltage.tb1
            check = True
            while check:
                if self._get_Par(5) == 1:
                    time.sleep(1 / refresh_rate)
                    time.sleep(0.001)
                else:
                    self._stop_process(2)
                    check = False
            in_bin = self._get_Par(4)
            measured = Adwin.convert_bin_to_V(in_bin, input_range, resolution_input)
            return measured

    def set_voltage_(self, voltage, out_channel=1, process_delay=0.00):
        debug = False
        if debug:
            print('Output {}V on channel {}'.format(voltage, out_channel))
            return 0.2*voltage
        else:
            output_range = 10.0
            resolution_output = 16
            out_bin, voltage = Adwin.convert_V_to_bin(voltage, output_range, resolution_output)
            refresh_rate = 100 # Hz
            self._set_Par(1, out_bin)
            self._set_Par(2, out_channel)
            self._set_Par(5, int(1))  # process is still running
            self._start_process(1)  # setvoltage.tb1
            check = True
            while check:
                if self._get_Par(5) == 1:
                    time.sleep(1 / refresh_rate)
                else:
                    self._stop_process(1)
                    check = False
            self._set_Par(5, int(1))
            time.sleep(process_delay)

    def get_voltage(self, in_channel=1):
        debug = False
        if debug:
            return 0.12345
        else:
            input_range = 10.0
            resolution_input = 18
            refresh_rate = 100 # Hz
            self._set_Par(3, in_channel)
            self._set_Par(5, int(1))  # process is still running
            self._start_process(2)  # getvoltage.tb1
            check = True
            while check:
                if self._get_Par(5) == 1:
                    time.sleep(1 / refresh_rate)
                    time.sleep(0.001)
                else:
                    self._stop_process(2)
                    check = False
            in_bin = self._get_Par(4)
            measured = Adwin.convert_bin_to_V(in_bin, input_range, resolution_input)
            return measured

    def record_IV(self, Voltage, process_delay, loops_waiting, points_av, log, lin_gain, log_conversion, process_file):
        #def record_IV(self, *args, **kwargs):
        # record I(V) using ADwin
        """
        resolution_input = 18
        resolution_output = 16
        output_range = 10.0  # AO1 output range
        input_range = 2.5
        refresh_rate = 100.0 # hz, taken from Boot.py
        V_bin, Voltage = Adwin.convert_V_to_bin(Voltage, output_range, resolution_output)
        NumBias = len(V_bin)
        self.load_process(process_file)
        self._set_data_long(1, Adwin.convert_to_list(V_bin))  # send arrays of the voltages
        self._set_data_float(10, log_conversion)  # send arrays of the voltages
        self._set_processdelay(1, int(process_delay))  # set process delay
        self._set_Par(55, int(points_av))  # set points to average
        self._set_Par(56, int(loops_waiting))  # set settling time
        self._set_Par(57, int(len(Voltage)))  # array length
        self._set_Par(59, int(1))  # process is still running

        ## RUN PROCESS ##
        self._start_process(1)
        check = True
        while check:
            if self._get_Par(59) == 1:
                time.sleep(1 / refresh_rate)
                time.sleep(0.001)
            else:
                self._stop_process(1)
                check = False

                ## GET DATA ##
        current1 = self._get_data_float(4, NumBias)  # get averaged MUX1 current values
        # current2 = self._adwin._get_data_float(5,NumBias)     # get averaged MUX2 current values
        # bin1 = self._adwin._get_data_float(2,NumBias)     # get averaged MUX1 bin values
        bin2 = self._get_data_float(3, NumBias)  # get averaged MUX2 bin values

        # if log == False:
        # current1 = convert_bin_to_V(bin1, input_range, resolution_input) / lin_gain
        current2 = Adwin.convert_bin_to_V(bin2, input_range, resolution_input) / lin_gain

        # return array(bin1), array(bin2)
        return np.array(current1), np.array(current2)
        """
        data = [0.01*i for i in Voltage]
        return Voltage, data

    @staticmethod
    def convert_V_to_bin(V, V_range, resolution):
        # converts ADC/DAC voltage to bin number, given the voltage range and the resolution (in bits)
        voltage = np.linspace(-V_range, V_range, 2**resolution)
        try:
            N_bin = [np.argmin(np.abs(voltage - v)) for v in V]
            # l = len(V)
            # N_bin = np.zeros(l, dtype=np.int32)
            # for i in range(0, len(V)):
            #    diff = np.abs(voltage - V[i])
            #    N_bin[i] = diff.argmin()
        except TypeError:
            diff = np.abs(voltage - V)
            N_bin = diff.argmin()
        # return N_bin, Adwin.convert_bin_to_V(N_bin, V_range, resolution)
        return N_bin, voltage[N_bin]

    @staticmethod
    def convert_bin_to_V(N_bin, V_range, resolution):
        # converts ADC/DAC bins to voltage, given the voltage range and the resolution (in bits)
        voltage = np.linspace(-V_range, V_range, 2**resolution)
        try:
            N_bin = int(N_bin)
            data = voltage[N_bin]
        except TypeError:
            data = [voltage[_] for _ in N_bin]
        return data

    @staticmethod
    def convert_to_list(data):
        return [int(i) for i in data]

    @staticmethod
    def convert_to_list_float(data):
        return [float(i) for i in data]

    # Standard functions from the driver
    def _boot(self, resolution):
        print('Adwin booted with the resolution of {}'.format(resolution))
        """
        if resolution == 16:
            boot_script = r'C:\ADwin\ADwin9.btl'
        elif resolution == 18:
            boot_script = r'C:\ADwin\ADwin11.btl'
        self._adwin.Boot(boot_script)
        """
        pass
        return None

    def _get_version(self):
        name = self._adwin.Test_Version()
        print('Version {} '.format(name))
        return None

    def _get_processor_type(self):
        name = self._adwin.Processor_Type()
        print('Processor type: {} '.format(name))
        return None

    def _load_process(self, process_name):
        # self._adwin.Load_Process(process_name)
        print('Process {} has been loaded'.format(process_name))
        return None

    def _start_process(self, process_number):
        self._adwin.Start_Process(process_number)
        return None

    def _process_status(self, process_number, output):
        status = self._adwin.Process_Status(process_number)
        if output == 'string':
            if status == 0:
                print('Process %1.0f is not running' % process_number)
            if status == 1:
                print('Process %1.0f is running' % process_number)
            if status < 0:
                print('Process %1.0f is stopped' % process_number)
            return None
        elif output == 'int':
            return status

    def _stop_process(self, process_number):
        self._adwin.Stop_Process(process_number)
        # print 'Process %1.0f has been stopped' % process_number
        return None

    def _stop_all_process(self):
        for i in range(1, 11):
            self._adwin.Stop_Process(i)
            # print 'Process %1.0f has been stopped' % i
        return None

    def _clear_process(self, process_number):
        self._adwin.Clear_Process(process_number)
        print('Process %1.0f has been removed' % process_number)
        return None

    def _clear_all_process(self, ):
        for i in range(1, 11):
            self._adwin.Clear_Process(i)
            print('Process %1.0f has been cleared'.format(i))
        return None

    def _get_processdelay(self, process_number):
        delay = self._adwin.Get_Processdelay(process_number)
        return delay

    def _set_processdelay(self, process_number, process_delay):
        self._adwin.Set_Processdelay(process_number, process_delay)

    def _set_FPar(self, parameter, value):
        self._adwin.Set_FPar(parameter, value)

    def _get_FPar(self, par):
        value = self._adwin.Get_FPar(par)
        return value

    def _get_all_FPar(self):
        for i in range(1, 81):
            print(self._get_FPar(i))

    def _set_Par(self, parameter, value):
        self._adwin.Set_Par(parameter, value)

    def _get_Par(self, parameter):
        value = self._adwin.Get_Par(parameter)
        # print 'Par %1.0f is %1.2f' % (par, value)
        return value

    def _get_all_Par(self):
        for i in range(1, 81):
            print(self._get_Par(i))

    def _get_data_length(self, parameter):
        length = self._adwin.Data_Length(parameter)
        return length

    def _set_data_long(self, parameter, array):
        self._adwin.SetData_Long(array, parameter, 1, len(array))

    def _get_data_long(self, parameter, counts):
        data = self._adwin.GetData_Long(parameter, 1, counts)
        data = [int(i) for i in data]
        return data

    def _set_data_float(self, parameter, array):
        self._adwin.SetData_Float(array, parameter, 1, len(array))

    def _get_data_float(self, par, counts):
        data = self._adwin.GetData_Float(par, 1, counts)
        data = [float(i) for i in data]
        return data