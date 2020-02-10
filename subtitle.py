#! /usr/bin/env python3

import srt
import copy
# See usage of srt module: https://srt.readthedocs.io/

class srt_to_list():
    def __init__(self, srt_file):
        with open(srt_file, 'r') as fp:
            self.data = list(srt.parse(fp.read()))
