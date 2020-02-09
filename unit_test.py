#! /usr/bin/env python3

import unittest
import os
import shutil
from make_cap_data import *
from download_youtube import *

class test_test(unittest.TestCase):
    def test_success(self):
        self.assertEqual(10, 10)

class test_make_cap_data(unittest.TestCase):
    def test_gen_structure(self):
        default_font_size = 30
        cd = cap_data()
        get_fs = cd['font_size']
        self.assertEqual(default_font_size, get_fs)

        cd2 = cap_data()
        get_fs2 = cd2['font_size']
        get_fs2 = 40

        self.assertEqual(30, get_fs)
        self.assertEqual(40, get_fs2)

class test_download_youtube(unittest.TestCase):
    def test_instance(self):
        test_url = 'https://youtu.be/MMmOLN5zBLY'
        y = youtube(test_url)
        self.assertEqual(test_url, y.vinfo['url'])
    
    def test_dl(self):
        test_url = 'https://youtu.be/MMmOLN5zBLY'
        test_fname = 'dl_video'
        test_fpath = os.path.join(get_curpath(), 'test_data/tmp_result') 
        if os.path.exists(test_fpath):
            shutil.rmtree(test_fpath, ignore_errors=True)
        os.mkdir(test_fpath)

        y = youtube(test_url)
        y.download_video(test_fpath, fname=test_fname)
        y.download_video(test_fpath)

        fn = os.path.join(test_fpath, test_fname + '.mp4')
        fnon = os.path.join(test_fpath, y.vinfo['video_id']  + '.mp4')
        self.assertEqual(True, os.path.exists(fn))
        self.assertEqual(True, os.path.exists(fnon))


def get_curpath():
    return os.getcwd()

if __name__ == '__main__':
    unittest.main()
