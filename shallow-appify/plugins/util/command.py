# coding: utf-8

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

import subprocess


__author__ = 'Ingo Heimbach'
__email__ = 'i.heimbach@fz-juelich.de'


def exec_cmd(*cmd):
    cmd = ' '.join(cmd)
    p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    return stdout


def which(cmd):
    return exec_cmd('which', cmd).strip()
