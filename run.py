#! /usr/bin/env python3
import os
import argparse
import shutil
import pprint
import json
from logger import *
from youtube import youtube
from subtitle import srt_to_list
from make_cap_data import cap_data

class make_youtube_info(dict):
    def __init__(self, args):
        self.args = args
        self.update(cap_data())
        vid, srt = self.download_youtube()
        self.save_variables(vid, srt)
        self.set_frame_info(srt)

    def save_variables(self, vid, srt):
        self.vid_path = vid
        self.srt_path = srt
        self.json_path = srt.replace('.srt', '.json')

    def download_youtube(self):
        yt = youtube(self.args.url)
        res_dir = self.make_download_dir()
        vid_path = yt.download_video(res_dir, fname=self.args.name)
        srt_path = yt.download_caption(res_dir, fname=self.args.name, lang=self.args.lang)
        return vid_path, srt_path

    def set_frame_info(self, srtfile_path):
        self['frame_infos'] = srt_to_list(srtfile_path)

    def save_json(self):
        with open(self.json_path, 'w') as fp:
            v_infos_json = json.dumps(self, ensure_ascii=False, indent="\t")
            fp.write(v_infos_json)

    def make_download_dir(self):
        result_path = os.path.join(get_curpath(), 'results', self.args.name)
        if self.args.retry and os.path.exists(result_path):
            shutil.rmtree(result_path)
        os.makedirs(result_path)
        return result_path

def get_curpath():
    return os.getcwd()

DEFAULT_L_CODE = 'en'
DEFAULT_VID_NAME = 'dl_video'
def parse_args():
	parser = argparse.ArgumentParser(description='Screen capture automatically from Youtube video\nexample: run.py -u <youtube link> -n <outfile name> -l <language> -f <fontsize>')
	parser.add_argument('-u', '--url', dest='url', help='Youtube vedio url')
	parser.add_argument('-n', '--name', dest='name', default=DEFAULT_VID_NAME, help='Output file name')
	parser.add_argument('-l', '--lang', dest='lang', default=DEFAULT_L_CODE, help='Caption language code (default: en)')
	parser.add_argument('-f', '--fontsize', dest='fontsize', default=30, type=int, help='Font size of caption (default: 30)')
	parser.add_argument('-b', '--bg-opacity', dest='bg_opacity', default=0, type=float, help='Add backgound behind of caption text with opacity (0.0 ~ 1.0) (default opacity : 0.0)')
	parser.add_argument('--no-sub', dest='nosub', action='store_true', help='If the video has a closed caption, no need to add caption additionally')
	parser.add_argument('--img-diff', dest='imgdiff', action='store_true', help='capture frame by imagediff')
	parser.add_argument('-r', '--retry', dest='retry', action='store_true', help='Retry download video')

	args = parser.parse_args()
	logger.info(args)
	return args

def main():
    args = parse_args()
    video_info = make_youtube_info(args)
    video_info.save_json()
    '''
    video, caption, v_infos = download_youtube(args)
    if need_modify_cap():
            caption = modify_cap_time(v_infos)

    nr_imgs, img_path, f_infos = capture_video(v_infos, video, caption)
    make_md_page(v_infos, nr_imgs, img_path, v_infos)

    v_infos['frame_infos'] = f_infos
    make_json(v_infos)
    del_unneccesary_files(GEN_FILES_DEL)
    make_single_picture(v_infos, nr_imgs, img_path, v_infos)
    '''

if __name__ == "__main__":
    main()
