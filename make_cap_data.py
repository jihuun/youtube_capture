#! /usr/bin/env python3
# Generate default video information json structure

from copy import deepcopy
from logger import *

video_info = {
        'url': '',
        'title': '',
        'video_id': '',
        'lang_code': 'en',
        'font_size': 30,
        'file_name': '',
        'file_path': '',
        'nosub_opt': False,
        'imgdiff_opt': False,
        'bg_opacity': 0.7,
        'thumbnail': '',
        'frame_infos': []
        }

class cap_data(dict):
    def __init__(self):
        self.update(video_info)

def example():
    logger.debug(cap_data())

if __name__ == '__main__':
    example()
