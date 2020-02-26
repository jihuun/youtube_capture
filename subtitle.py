#! /usr/bin/env python3
import datetime
import srt
import copy
import pprint
# See usage of srt module: https://srt.readthedocs.io/
# datetime: https://minus31.github.io/2018/07/28/python-date/

class srt_to_list(list):
    def __init__(self, srt_file):
        with open(srt_file, 'r') as fp:
            self.data = list(srt.parse(fp.read()))
        self.make_frame_list()

    def make_frame_list(self):
        for idx, ele in enumerate(self.data):
            ts = self.calc_timestamp(ele)
            script = self.get_script(ele)
            frame = self.set_ts_dict(idx, ts, script)
            self.append(frame)

    def calc_timestamp(self, datetime):
        st = datetime.start.seconds
        ed = datetime.end.seconds
        ret = st + float((ed - st) / 2)
        return ret

    def get_script(self, srts):
        return srts.content

    def set_ts_dict(self, idx, ts, script):
        ts_dict = dict()
        ts_dict['frame_num'] = idx
        ts_dict['img_path'] = None
        ts_dict['time_info'] = ts
        ts_dict['script'] = script
        ts_dict['ocr_script'] = None
        ts_dict['hash'] = None
        ts_dict['sub_hash'] = None
        ts_dict['usage'] = 'ok'
        return ts_dict

def main():
    a = srt_to_list('/Users/jihuun/project/youtube_capture/test_data/MMmOLN5zBLY/MMmOLN5zBLY.srt')
    pprint.pprint(a)

if __name__ == '__main__':
    main()
