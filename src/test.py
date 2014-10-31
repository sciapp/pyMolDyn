# -*- coding: utf-8 -*-

import os
import core.calculation
import core.file
import util.message as message


class PymoldynTest(object):
    def __init__(self):
        self.path = os.path.abspath("../xyz")
        self.calculation = core.calculation.Calculation()


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
    f = core.file.File.open(os.path.join(p.path, "GST_111_128_bulk.xyz"))
    r = p.calculation.calculate(f, 0, 96, False)
