#! /usr/bin/env python3
# download youtube video using Pytube3
# and save the informations

from pytube import YouTube
from make_cap_data import *

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




def example():
    pass

if __name__ == '__main__':
    example()
