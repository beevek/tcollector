#!/usr/bin/python
#
# ps.py -- a process collector for tcollector/OpenTSDB
# Copyright (C) 2015 NSONE, Inc.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.  This program is distributed in the hope that it
# will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser
# General Public License for more details.  You should have received a copy
# of the GNU Lesser General Public License along with this program.  If not,
# see <http://www.gnu.org/licenses/>.

import sys
import time
try:
    import psutil
except ImportError:
    psutil = None  # This is handled gracefully in main()

from collectors.lib import utils

INTERVAL = 300
PYTHON_INTERP = 'python'

# items in this list should match process name
PROCS = []
# items in this list should include .py extension if script is so named
PYTHON_PROCS = []
try:
    from collectors.etc import psconf
    PROCS = psconf.get_procs_to_monitor()
    PYTHON_PROCS = psconf.get_python_procs_to_monitor()
except:
    # handled in main()
    pass


def add_metrics(proc, lines, name):
    if name.endswith('.py'):
        name = name[0:-3]
    ts = int(time.time())

    metric_name = 'ps.%s' % name

    def add_line(met, val, tags=None):
        l = '%s.%s %d %s pid=%d' % (metric_name,
                                    met,
                                    ts,
                                    val,
                                    proc.pid)
        if tags:
            for k, v in tags.iteritems():
                l += " %s=%s" % (k, v)
        lines.append(l)

    mi = proc.get_memory_info()
    add_line('mem.resident', mi.rss)
    add_line('mem.virtual', mi.vms)

    cpu = proc.get_cpu_times()
    add_line('cpu', cpu.user, {'type': 'user'})
    add_line('cpu', cpu.system, {'type': 'system'})



def main():
    utils.drop_privileges()
    if psutil is None:
       print >>sys.stderr, "error: python module `psutil' is missing"
       return 13
    if not len(PROCS) and not len(PYTHON_PROCS):
        print >>sys.stderr, "error: no PROCS or PYTHON_PROCS specified, " \
                            "create psconf module"
        return 14

    while True:

        lines = []
        for proc in psutil.process_iter():
            if len(PYTHON_PROCS) and proc.name() == PYTHON_INTERP:
                for pp in PYTHON_PROCS:
                    if proc.cmdline()[1].endswith(pp):
                        add_metrics(proc, lines, pp)
            elif proc.name() in PROCS:
                add_metrics(proc, lines, proc.name())

        if len(lines):
            for l in lines:
                print l

        sys.stdout.flush()
        time.sleep(INTERVAL)

if __name__ == '__main__':
    sys.exit(main())
