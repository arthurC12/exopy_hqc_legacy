# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Driver for the Cryomagnetic superconducting magnet power supply CS4.

"""
from inspect import cleandoc
from time import sleep
import logging

from ..driver_tools import (InstrIOError, secure_communication,
                            instrument_property, InstrJob)
from ..visa_tools import VisaInstrument


_GET_HEATER_DICT = {'0': 'Off',
                    '1': 'On'}

_ACTIVITY_DICT = {'To set point': 'UP',
                  'Hold': 'PAUSE'}


class CS4(VisaInstrument):
    """Driver for the superconducting magnet power supply Cryomagnetics CS4.

    """

    #: Typical fluctuations at the output of the instrument.
    #: We use a class variable since we expect this to be identical for all
    #: instruments.
    OUTPUT_FLUCTUATIONS = 3e-4

    caching_permissions = {'heater_state': True,
                           'target_field': True,
                           'sweep_rate_field': True,
                           }

    log_prefix= 'CS4 Driver: '

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):
        super().__init__(connection_info, caching_allowed,
                                  caching_permissions)
        try:
            mc = connection_info['magnet_conversion']
            self.field_current_ratio = float(mc)
            log = logging.getLogger(__name__)
            msg = ('Field current ratio is %s T/A')
            log.info(self.log_prefix+msg,float(mc))
        except KeyError:
            raise InstrIOError(cleandoc('''The field to current ratio
                 of the currently used magnet need to be specified in
                 the instrument settings. One should also check that
                 the switch heater current is correct.'''))
        try:
            lfl = connection_info['lower_field_limit']
            self.lower_field_limit = float(lfl)
            log = logging.getLogger(__name__)
            msg = ('Lower field limit is %s T')
            log.info(self.log_prefix+msg,float(lfl))
        except KeyError:
            raise InstrIOError(cleandoc('''The lower field limit
                 of the currently used magnet need to be specified in
                 the instrument settings. One should also check that
                 the switch heater current is correct.'''))
                         
        if 'output_fluctuations' in connection_info:
            self.output_fluctuations = connection_info['output_fluctuations']
        else:
            self.output_fluctuations = self.OUTPUT_FLUCTUATIONS

        # Setup the correct unit and range.
        self.write('UNITS T')
        self.write('RANGE 0 50;')  # HINT the CG4 requires the ;
        # we'll only use the command sweep up (ie to upper limit)
        # however upper limit can't be lower than lower limit for
        # some sources : G4 for example
        # set lower limit to lowest value
        self.write('LLIM {}'.format(self.lower_field_limit))

    def open_connection(self, **para):
        """Open the connection and set up the parameters.

        """

        log = logging.getLogger(__name__)
        msg = ('Establishing a connection with cs4')
        log.info(self.log_prefix+msg)

        super(CS4, self).open_connection(**para)
        if not para:
            self.write_termination = '\n'
            self.read_termination = '\n'

    @secure_communication()
    def read_output_field(self):
        """Read the current value of the output field.

        """
        reading_field = float(self.query('IOUT?').strip(' T'))
        log = logging.getLogger(__name__)
        msg = ('Reading output field as %s T')
        log.info(self.log_prefix+msg,reading_field)
        return reading_field

    @secure_communication()
    def read_persistent_field(self):
        """Read the current value of the persistent field.

        """
        reading_field = float(self.query('IMAG?').strip(' T'))
        log = logging.getLogger(__name__)
        msg = ('Reading persistent field as %s T')
        log.info(self.log_prefix+msg,reading_field)
        return reading_field

    def is_target_reached(self):
        """Check whether the target field has been reached.

        """
        log = logging.getLogger(__name__)
        msg = ('Assessing completion')
        log.info(self.log_prefix+msg)
        return (abs(self.read_output_field() - self.target_field) <
                self.output_fluctuations)

    def sweep_to_persistent_field(self):
        """Convenience function ramping the field to the persistent.

        Once the value is reached one can safely turn on the switch heater.

        """
        log = logging.getLogger(__name__)
        msg = ('Going to permanent field')
        log.info(self.log_prefix+msg)
        return self.sweep_to_field(self.read_persistent_field())

    def sweep_to_field(self, value, rate=None):
        """Convenience function to ramp up the field to the specified value.

        """
        # Set rate. Always the fast sweep rate if the switch heater is off.
        if rate is not None:
            self.field_sweep_rate = rate
        rate = (self.field_sweep_rate if self.heater_state == 'On' else
                self.fast_sweep_rate)
        # Start ramping.
        self.target_field = value
        # Added a pause and then sweep up due to a buggy behavior of the source
        sleep(1)
        self.activity = 'Hold'
        sleep(1)
        self.activity = 'To set point'

        # Create job.
        span = abs(self.read_output_field() - value)
        wait = 60 * span / rate
        log = logging.getLogger(__name__)
        msg = ('Starting sweep, with wait of %s s')
        log.info(self.log_prefix+msg,wait)
        job = InstrJob(self.is_target_reached, wait, cancel=self.stop_sweep,
                       timeout_handler=self.stop_sweep_safe)
        return job

    @secure_communication()
    def stop_sweep(self):
        """Stop the field sweep at the current value.

        """
        log = logging.getLogger(__name__)
        msg = ('Stopping sweep (switch heater on)')
        log.info(self.log_prefix+msg)
        self.activity = 'Hold'

    @secure_communication()
    def stop_sweep_safe(self):
        """Stop the field sweep at the current value, and turn of the switch heater.

        """
        log = logging.getLogger(__name__)
        msg = ('Stopping sweep safe (switch heater off)')
        log.info(self.log_prefix+msg)
        self.activity = 'Hold'
        self.heater_state = 'Off'
        sleep(self.post_switch_wait)

    def check_connection(self):
        pass

    @instrument_property
    @secure_communication()
    def heater_state(self):
        """State of the switch heater allowing to inject current into the
        coil.

        """
        log = logging.getLogger(__name__)
        msg = ('Ask heater state (instr prop)')
        log.info(self.log_prefix+msg)
        heat = self.query('PSHTR?').strip()
        try:
            return _GET_HEATER_DICT[heat]
        except KeyError:
            raise ValueError('The switch is in fault or absent')

    @heater_state.setter
    @secure_communication()
    def heater_state(self, state):
        if state in ['On', 'Off']:
            log = logging.getLogger(__name__)
            msg = ('Write heater state (instr prop)')
            log.info(self.log_prefix+msg)
            self.write('PSHTR {}'.format(state))
            sleep(1)

    @instrument_property
    @secure_communication()
    def field_sweep_rate(self):
        """Rate at which to ramp the field (T/min).

        """
        # converted from A/s to T/min
        log = logging.getLogger(__name__)
        msg = ('Ask A/s rate (instr prop)')
        log.info(self.log_prefix+msg)
        rate = float(self.query('RATE? 0'))
        return rate * (60 * self.field_current_ratio)

    @field_sweep_rate.setter
    @secure_communication()
    def field_sweep_rate(self, rate):
        # converted from T/min to A/s
        log = logging.getLogger(__name__)
        msg = ('Set A/s rate (instr prop)')
        log.info(self.log_prefix+msg)
        rate /= 60 * self.field_current_ratio
        self.write('RATE 0 {}'.format(rate))

    @instrument_property
    @secure_communication()
    def fast_sweep_rate(self):
        """Rate at which to ramp the field when the switch heater is off
        (T/min).

        """
        log = logging.getLogger(__name__)
        msg = ('Ask fast rate (instr prop)')
        log.info(self.log_prefix+msg)
        rate = float(self.query('RATE? 3'))
        return rate * (60 * self.field_current_ratio)

    @fast_sweep_rate.setter
    @secure_communication()
    def fast_sweep_rate(self, rate):
        log = logging.getLogger(__name__)
        msg = ('Set fast rate (instr prop)')
        log.info(self.log_prefix+msg)
        rate /= 60 * self.field_current_ratio
        self.write('RATE 3 {}'.format(rate))

    @instrument_property
    @secure_communication()
    def target_field(self):
        """Field that the source will try to reach.

        """
        # in T
        log = logging.getLogger(__name__)
        msg = ('Ask field target (instr prop)')
        log.info(self.log_prefix+msg)
        return float(self.query('ULIM?').strip(' T'))

    @target_field.setter
    @secure_communication()
    def target_field(self, target):
        """Sweep the output intensity to reach the specified ULIM (in T)
        at a rate depending on the intensity, as defined in the range(s).

        """
        log = logging.getLogger(__name__)
        msg = ('Set field target (instr prop)')
        log.info(self.log_prefix+msg)
        self.write('ULIM {}'.format(target))

    @instrument_property
    @secure_communication()
    def persistent_field(self):
        """Last known value of the magnet field.

        """
        log = logging.getLogger(__name__)
        msg = ('Ask persistent field (instr prop)')
        log.info(self.log_prefix+msg)
        return float(self.query('IMAG?').strip(' T'))

    @instrument_property
    @secure_communication()
    def activity(self):
        """Current activity of the power supply (idle, ramping).

        """
        log = logging.getLogger(__name__)
        msg = ('Ask activity (instr prop)')
        log.info(self.log_prefix+msg)
        return self.query('SWEEP?').strip()

    @activity.setter
    @secure_communication()
    def activity(self, value):
        par = _ACTIVITY_DICT.get(value, None)
        if par != 'PAUSE':
            if self.heater_state == 'Off':
                par += ' FAST'
            else:
                par += ' SLOW'
        if par:
            log = logging.getLogger(__name__)
            msg = ('Set activity (instr prop) as %s')
            log.info(self.log_prefix+msg,'SWEEP ' + par)
            self.write('SWEEP ' + par)
        else:
            raise ValueError(cleandoc(''' Invalid parameter {} sent to
                             CS4 set_activity method'''.format(value)))
