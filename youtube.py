#! /usr/bin/env python3
# download youtube video using Pytube3
# and save the informations

import os, sys
from pytube import YouTube
from make_cap_data import *
from logger import *

class youtube():
    def __init__(self, url):
        self.vinfo = cap_data()
        self.info = YouTube(url)
        self.save_video_info(self.vinfo, url)

    def get_streams(self):
        if self.info:
            return self.info.streams
        return None

    def get_streams_itag(self, itag):
        if self.info:
            return self.get_streams().get_by_itag(itag)
        return None

    def save_video_info(self, vi, url):
        vi['url'] = url
        vi['title'] = self.info.title
        vi['video_id'] = self.info.video_id
        vi['thumbnail'] = self.info.thumbnail_url

    def download_video(self, fpath, fname=None, itag='18'):
        st = self.get_streams_itag(itag) #FIXME: best way to select itag
        if fname == None:
           fname = self.vinfo['video_id']
        st.download(output_path=fpath, filename=fname)
        result = os.path.join(fpath, fname + '.mp4')
        logger.info('The video is downloaded in "%s" ' %result)
        return result

    def get_captions(self):
        return self.info.captions

    def __save_caption_code(self, code):
        self.vinfo['lang'] = code

    def is_lang_available(self, cap, lang):
        for l in cap.all():
            lang_code = l.__dict__['code']
            if lang_code == lang:
                return True
        return False

    def get_available_langs(self, cap):
        ret = []
        for key, val in cap.lang_code_index.items():
            ret.append(val.code) #NOTE: val.name show name of code
        return ret

    def __save_caption_file(self, cap, fpath, fname):
        if fname == None:
            fname = self.vinfo['video_id']
        tgt = os.path.join(fpath, fname + '.srt')
        with open(tgt, 'w') as fp:
            fp.write(cap.generate_srt_captions())
        return tgt

    def download_caption(self, fpath, fname=None, lang='en'):
        captions = self.get_captions()
        if not self.is_lang_available(captions, lang):
            alternative_langs = self.get_available_langs(captions)
            logger.critical('The caption language (%s) is not exist, try another lang in %s' %(lang, alternative_langs))
            raise SystemExit
        self.__save_caption_code(lang)
        caption = captions.get_by_language_code(lang)
        result = self.__save_caption_file(caption, fpath, fname)
        logger.info('The caption is downloaded in %s' %result)
        return result


def example():
    pass

if __name__ == '__main__':
    example()
