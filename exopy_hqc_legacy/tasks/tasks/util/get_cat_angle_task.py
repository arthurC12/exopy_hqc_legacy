# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2017 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Tasks to operate on numpy.arrays.

"""
import numpy as np
from atom.api import (Enum, Bool, Unicode, set_default, Float, Int)
from scipy.interpolate import splrep, sproot, splev
from scipy.optimize import curve_fit, leastsq
import scipy.ndimage.filters as flt
import matplotlib.pyplot as plt
import scipy

import logging
from exopy.tasks.api import SimpleTask, InterfaceableTaskMixin, TaskInterface
from exopy.tasks.api import validators

ARR_VAL = validators.Feval(types=np.ndarray)


class GetCatAngle(SimpleTask):
    """ Store the pair(s) of index/value for the extrema(s) of an array.

    Wait for any parallel operation before execution.

    """
    #: Name of the target in the database.
    bit_array = Unicode().tag(pref=True)
    
    #: Name of the angles of the wigner circle.
    angle_array = Unicode().tag(pref=True)
    
    database_entries = set_default({'fitted_angle': 1.0})
    
    wait = set_default({'activated': True})  # Wait on all pools by default.

    def perform(self):
        """ Find extrema of database array and store index/value pairs.

        """
        bit = self.format_and_eval_string(self.bit_array)
        angle = self.format_and_eval_string(self.angle_array)
        bit_shape = bit.shape
        bit = np.reshape(bit, (bit_shape[0], 2, int(bit_shape[1]/2)))
        bit = np.moveaxis(bit, 1, 0)
        wig_plus = bit[0].mean(0)
        wig_minus = bit[1].mean(0)
        wig = wig_plus - wig_minus
        
        popt, _ = curve_fit(gauss_pi, angle, wig, p0=(angle[np.argmax(wig)], np.amax(wig), 1))
        angle_fit = np.linspace(np.amin(angle), np.amax(angle), 51)
        wig_fit = gauss_pi(angle_fit, *popt)
        fitted_angle = popt[0]
        print('angle-> exopy= %.3f'%(popt[0]))
        
        plot=False
        if plot:
            plt.close('all')
            fig, ax = plt.subplots(figsize = (8,6))
            ax.plot(angle, wig, '.')
            ax.plot(angle, wig_plus, '.', label='plus')
            ax.plot(angle, wig_minus, '.', label='minus')
            ax.plot(angle_fit, wig_fit)
            plt.show()

#        print('bit_array : '+str(bit_array.shape))
#        print('angle_array : '+str(angle_array.shape))
        self.write_in_database('fitted_angle', fitted_angle)

    def check(self, *args, **kwargs):
        """ Check the target array can be found and has the right column.

        """
        test, traceback = super(GetCatAngle, self).check(*args, **kwargs)

        if not test:
            return test, traceback
#        array = self.format_and_eval_string(self.target_array)
#        print(self.target_array)
#        print(array)
#        print('blaaaaah')
#        err_path = self.get_error_path()
#
#        if self.column_name:
#            if array.dtype.names:
#                names = array.dtype.names
#                if self.column_name not in names:
#                    msg = 'No column named {} in array. (column are : {})'
#                    traceback[err_path] = msg.format(self.column_name, names)
#                    return False, traceback
#            else:
#                traceback[err_path] = 'Array has no named columns'
#                return False, traceback
#
#        else:
#            if array.dtype.names:
#                msg = 'The target array has names columns : {}. Choose one'
#                traceback[err_path] = msg.format(array.dtype.names)
#                return False, traceback
#            elif len(array.shape) > 1:
#                msg = 'Must use 1d array when using non record arrays.'
#                traceback[err_path] = msg
#                return False, traceback

        return test, traceback

#    def _post_setattr_mode(self, old, new):
#        """ Update the database entries according to the mode.
#
#        """
#        if new == 'Max':
#            self.database_entries = {'I': 0, 'Q': 2.0}
#        else:
#            self.database_entries = {'I': 0, 'Q': 1.0}
        
def gauss_pi(x, x0, A, sigma):
    return A*np.exp(-((x-x0)%np.pi)**2/(2*sigma**2))+A*np.exp(-((x-x0)%np.pi+np.pi)**2/(2*sigma**2))+A*np.exp(-((x-x0)%np.pi-np.pi)**2/(2*sigma**2))
   