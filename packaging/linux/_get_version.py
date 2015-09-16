#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys


def get_version(src_dir):
    sys.path.insert(0, src_dir)
    import _version
    del sys.path[0]
    return _version.__version__


if __name__ == "__main__":
    print(get_version(sys.argv[1]))
