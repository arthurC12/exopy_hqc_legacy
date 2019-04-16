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
from matplotlib.colors import LinearSegmentedColormap

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
        avg = bit.mean(-1)
        avg = np.transpose(avg)
        wig_plus = avg[0]
        wig_minus = avg[1]
        wig = wig_plus - wig_minus
        
        popt, pcov = curve_fit(gauss_pi, angle, wig, p0=(angle[np.argmax(wig)], np.amax(wig), 1))
        angle_fit = np.linspace(np.amin(angle), np.amax(angle), 51)
        wig_fit = gauss_pi(angle_fit, *popt)
        err = np.sqrt(pcov[0,0])/np.pi
        fitted_angle = popt[0]
        print('angle-> exopy= %.3f, err = %.1f%%'%(popt[0], 100*err))
        
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
        
class GetBlobPos(SimpleTask):
    """ Store the pair(s) of index/value for the extrema(s) of an array.

    Wait for any parallel operation before execution.

    """
    #: Name of the target in the database.
    bit_array = Unicode().tag(pref=True)
    
    #: Name of the I and Q quadrature of the wigner.
    I_array = Unicode().tag(pref=True)
    Q_array = Unicode().tag(pref=True)
    
    database_entries = set_default({'pos1': 1.0, 'pos2':1.0})
    
    wait = set_default({'activated': True})  # Wait on all pools by default.

    def perform(self):
        """ Find extrema of database array and store index/value pairs.

        """
        bit = self.format_and_eval_string(self.bit_array)
        I = self.format_and_eval_string(self.I_array)
        Q = self.format_and_eval_string(self.Q_array)
        avg = bit.mean(-1)
        avg = np.transpose(avg, (2,1,0))
        wig = avg[0] - avg[1]
        
        popt = fit_blob(I, Q, wig, 0.5)
        I_fit, Q_fit = np.meshgrid(I, Q)
        
        blob1 = popt[4]+1j*popt[6]
        blob2 = popt[5]+1j*popt[7]
        print('\n')
        if popt[2]<0 or popt[3]<0:
            if popt[2]<0:    
                print('Neg_blob is in (%.3f, %.3f) with height %.3f'%(popt[4], popt[6], popt[2]))
                pos1 = blob2
                pos2 = blob1
                # first blob should be positive
            else:    
                print('\n'+'Neg_blob is in (%.3f, %.3f) with height %.3f'%(popt[5], popt[7],popt[3]))
                pos1 = blob1
                pos2 = blob2
        else:
            if np.abs(blob1)>np.abs(blob2):
                pos1 = blob2
                pos2 = blob1
            else:
                pos1 = blob1
                pos2 = blob2
                
                
        print('Blobs are in (%.3f, %.3f), (%.3f, %.3f)'%(np.real(pos1), 
                             np.imag(pos1), np.real(pos2), np.imag(pos2)))
        
        theta = np.angle(blob1-blob2)
        alpha1 = np.abs(pos1)
        alpha2 = np.abs(pos2)
        print('theta = %.3f'%(theta*180/np.pi))
        print('alpha1 = %.3f'%alpha1)
        print('alpha2 = %.3f'%alpha2)
        
        # if one positive blob should be pos1
        # if one blob is near center, should be pos1
        self.write_in_database('pos1', pos1)
        self.write_in_database('pos2', pos2)
        
        plot = False
        if plot:
            plt.close('all')
            fig, ax = plt.subplots(1,2, figsize = (8,6))
            cmap = enhance_neg_cmap(1)
            vmax = np.amax(wig)
            ax[0].pcolor(I, Q, wig, cmap=cmap, vmin=[-vmax, vmax])
            ax[1].pcolor(I, Q, blob(I_fit, Q_fit, *popt), cmap=cmap, vmin=[-vmax, vmax])
            plt.show()        

    def check(self, *args, **kwargs):
        """ Check the target array can be found and has the right column.

        """
        test, traceback = super(GetBlobPos, self).check(*args, **kwargs)

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
   
def blob(x, y, sigma, A0, A1, A2, x1, x2, y1, y2):
    A = [A0, A1, A2]
    x0 = [x1, x2]
    y0 = [y1, y2]
    z = A[0]
    for ii in range(2):
        z+=A[ii+1]*np.exp(-((x-x0[ii])/sigma)**2/2)*np.exp(-((y-y0[ii])/sigma)**2/2)
    return z

def fit_blob(x, y, z, sigma, debug=False):
    # uses sigma to mask the first found blob
    _z = z.copy()
    shape = z.shape
    _x, _y = np.meshgrid(x, y)
    A_guess = []
    x_guess = []
    y_guess = []
    debug=False
    if debug:
        cmap = enhance_neg_cmap(1)
        fig, ax = plt.subplots(3,2)
        vmax = np.amax(_z)
        ax[0,0].pcolor(x, y, _z, vmin=[-vmax,vmax], cmap=cmap)
    for ii in range(2):
        index_max = np.unravel_index(np.nanargmax(np.abs(_z)), shape)
        A_guess.append(z[index_max])
        x_guess.append(x[index_max[1]])
        y_guess.append(y[index_max[0]])
        dist_array = ((_x-x_guess[-1])**2+(_y-y_guess[-1])**2)**0.5
        _z = np.where(dist_array>1.5*sigma, _z, np.nan)
        if debug:
            ax[ii+1,0].pcolor(x, y, _z, vmin=[-vmax,vmax], cmap=cmap)
            ax[ii+1,0].pcolor(ax[ii+1,1], x, y, dist_array, vmin=0)
    A_guess = [np.nanmean(_z)]+A_guess
    popt, pcov = surface_fit(blob, x, y, z, (sigma, A_guess[0], A_guess[1], A_guess[2], x_guess[0], x_guess[1], y_guess[0], y_guess[1]))
    return popt

def surface_fit(f, xData, yData, zData, p0, weights=None, bounds=()):
    if len(np.shape(xData))!=1:
        raise ValueError('xData should be 1d-array')
    if len(np.shape(yData))!=1:
        raise ValueError('yData should be 1d-array')
    if len(np.shape(zData))!=2:
        raise ValueError('zData should be 2d-array')
    nx = len(xData)
    ny = len(yData)
    nz_x = zData.shape[1]
    nz_y = zData.shape[0]
    if nx!=nz_x or ny!=nz_y:
        raise ValueError('xyData-shape ({}, {}) doesn\'t match zData-shape ({}, {})'.format(nx, ny, nz_x, nz_y))
    nz = nx*ny

    if np.isscalar(p0):
        p0 = np.array([p0])

    def residuals(params, x, y, z):
        _x, _y = np.meshgrid(x, y)
        if weights is not None:
            diff = weights * f(_x, _y, *params) - z
        else:
            diff = f(_x, _y, *params) - z
        flatdiff = diff.reshape(len(x)*len(y))
        return flatdiff

    res = leastsq(residuals, p0, args=(xData, yData, zData),maxfev=1000,
                  ftol=1e-2, full_output=1)
    popt, pcov, infodict, errmsg, ier = res
    cost = np.sum(infodict['fvec'] ** 2)
    zData= np.array(zData)
    p0= np.array(p0)
    if pcov is not None:
        if nz > p0.size:
            s_sq = cost / (nz - p0.size)
            pcov = pcov * s_sq
        else:
            raise ValueError('zData length should be greater than the number of parameters.')
    return popt, pcov

def enhance_neg_cmap(fold):
    cdict = {'red':  ((0.0, 0.0, 0.0),
                       (1/(fold+1), 1.0, 1.0),
                       (1.0, 1.0, 1.0)),
    
             'green': ((0.0, 0.0, 0.0),
                       (1/(fold+1), 1.0, 1.0),
                       (1.0, 0.0, 0.0)),
    
             'blue':  ((0.0, 1.0, 1.0),
                       (1/(fold+1), 1.0, 1.0),
                       (1.0, 0.0, 0.0))
            }
    return LinearSegmentedColormap('my_cm', cdict)
