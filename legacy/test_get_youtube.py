import os, shutil
import unittest
from get_youtube import *

DL_NAME = 'download_test'

class fake_args():
    def __init__(self):
        self.url = 'https://www.youtube.com/watch?v=psN1DORYYV0'
        self.name = DL_NAME
        self.lang = 'ko'
        self.fontsize = 30
        self.nosub = False
        self.imgdiff = False
        self.bg_opacity = 0.7

class subtitle_test(unittest.TestCase):
    def test_get_split_time(self):
        time_str = '13:02:00 --> 13:02:10'
        ret0 = get_split_time(time_str, 0)
        self.assertEqual(ret0, '13:02:00')
        ret0 = get_split_time(time_str, 1)
        self.assertEqual(ret0, '13:02:10')

class download_test(unittest.TestCase):
    gen_test_files = []

    def setUp(self):
        cur_path = os.getcwd()
        result_test_path = os.path.join(cur_path, 'results', DL_NAME)
        self.gen_test_files.append(result_test_path)
        self._delete_gen_files()

    def tearDown(self):
        self._delete_gen_files()

    def _delete_gen_files(self):
        for f in self.gen_test_files:
            self._rm_test_file(f)

    def _file_exist(self, f):
        return os.path.exists(f)
    
    def _rm_test_file(self, f):
        if not self._file_exist(f):
            return
        if os.path.isdir(f):
            shutil.rmtree(f, ignore_errors=True)
        else:
            os.remove(f)

    def test_download_youtube(self):
        ex_vid = 'psN1DORYYV0'
        args = fake_args()
        video, caption, v_infos = download_youtube(args)

        self.assertEqual(True, self._file_exist(video))
        self.assertEqual(True, self._file_exist(caption))
        self.assertEqual(v_infos['video_id'], ex_vid)

if __name__ == '__main__':
    unittest.main()
