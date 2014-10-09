# -*- coding: utf-8 -*-

import os
from core.file import FileManager
from core.calculation import Calculation
import util.message as message


class PymoldynTest(object):
    def __init__(self):
        path = os.path.abspath("../xyz")
        self.filemanager = FileManager(path)


if __name__ == "__main__":
    def print_message(*s):
        print "message:", s[0],
        for x in s[1:]:
            print ";", x,
        print

    def progress(*s):
        print "progress:", s[0],
        for x in s[1:]:
            print ";", x,
        print

    def finish():
        print "finish"

    message.set_output_callbacks(progress, print_message, finish)

    p = PymoldynTest()
    f = p.filemanager["GST_111_128_bulk.xyz"]
    c = Calculation()
    r = c[f, 0, 96, False]
