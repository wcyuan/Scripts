#
# $Header: /u/yuanc/testbed/python/RCS/dispvar.py,v 1.2 2012/11/14 02:54:11 yuanc Exp $
#
# To use this, run:
#
#   $ ipython --pylab
#   In [1]: import path.to.dispvar
#
# Then all ipython variables will show up in a separate pylab window.
#

import pylab
from IPython import ipapi

def user_vars(self):
    '''
    A function that returns all the user variables in an ipython session.

    Based on IPython.Magic.magic_who_ls
    '''
    ip = self.api
    allvars = []
    for var in ip.user_ns:
        if (var.startswith("_") or
            var in ip.IP.user_config_ns or
            var in ip.IP.internal_ns):
            continue
        yield var, ip.user_ns[var]

def disphook(self):
    '''
    A function that displays all ipython variables in a pylab window.
    '''
    text = ""
    for (var, val) in sorted(user_vars(self)):
        text += '%s  = %s\n' % (var, val)
    pylab.clf()
    pylab.axes([0, 0, 1, 1])
    pylab.text(0.1, 0.1, text)
    pylab.show()

ipapi.get().set_hook("pre_prompt_hook", disphook)
