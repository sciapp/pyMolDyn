# -*- coding: utf-8 -*-


__all__ = ["trap"]


import sys
import os
import inspect


stream = sys.stdout
ignore = ["DEPRECATED"]


def trap(*args):
    st = inspect.stack()
    if len(args) > 0:
        name = args[0]
        args = args[1:]
    else:
        name = "TRAP"
    if name in ignore:
        return
    print >>stream, "{}:".format(name),
    for a in args:
        print >>stream, a,
    print >>stream, \
            "in {} ({}:{}), called by {} ({}:{})" \
            .format(st[1][3],
                    os.path.relpath(st[1][1]),
                    st[1][2],
                    st[2][3],
                    os.path.relpath(st[2][1]),
                    st[2][2])

