# -*- coding: utf-8 -*-

import os
import core.data
import core.calculation
import core.file
import util.message as message


class PymoldynTest(object):
    def __init__(self):
        self.path = os.path.abspath("../xyz")
        self.calculation = core.calculation.Calculation()


def main():
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
    f = os.path.join(p.path, "GST_111_128_bulk.xyz")
    cs = core.calculation.CalculationSettings([f], [0], 96, True, True, True)
    r = p.calculation.calculate(cs)
    print r


def addelements():
    import h5py

    p = PymoldynTest()
    cd = p.calculation.cache.directory
    fl = core.file.File.listdir(cd)
    fl = [os.path.abspath(os.path.join(cd, f)) for f in fl]

    for fpath in fl:
        with h5py.File(fpath) as rf:
            info = core.data.ResultInfo(rf["info"])
            sf = core.file.File.open(info.sourcefilepath)
            for gname in rf["atoms"].keys():
                frame = int(gname[5:])
                group = rf["atoms/frame{}".format(frame)]
                if not "elements" in group:
                    satoms = sf.getatoms(frame)
                    group["elements"] = satoms.elements


def testpartialpdf():
    pass

if __name__ == "__main__":
    #main()
    #addelements()
    testpartialpdf()
