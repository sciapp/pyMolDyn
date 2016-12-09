#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


import re
import sys


def binary_replace(file_path, old, new):
    def replace(match):
        old_text = match.group()
        new_text = old_text.replace(old, new)
        if len(new) > len(old):
            new_text = new_text[:len(old_text)]
            padding = 0
        else:
            padding = len(old_text) - len(new_text)
        return new_text + b'\0' * padding

    if isinstance(old, unicode):
        old = old.encode('utf-8')
    if isinstance(new, unicode):
        new = new.encode('utf-8')
    with open(file_path, 'rb') as f:
        data = f.read()
    unpatched_data_len = len(data)
    fill_len = max(0, len(new) - len(old))
    pattern = re.compile(re.escape(old) + b'([^\0]*?)\0' + ('.{%d}' % fill_len))
    data = pattern.sub(replace, data)
    assert(unpatched_data_len == len(data))
    with open(file_path, 'wb') as f:
        f.write(data)


def main():
    if len(sys.argv) < 4:
        print('Usage: {name} file_path old_string new_string'.format(name=sys.argv[0]))
        print('       Opens a binary file and replaces every occurance of old_string with new_string.')
        sys.exit(0)

    file_path, old_string, new_string = sys.argv[1:4]
    binary_replace(file_path, old_string, new_string)


if __name__ == '__main__':
    main()
