import os
import sys
import subprocess
import argparse
import shutil
import re
from caption import bake_caption
from pytube import YouTube	#pip3 install pytube
import cv2			#pip3 install opencv-python
				# If there would be "numpy.core.multiarray" problem of numpy
				#Do 'pip3 uninstall numpy' few times until all numpy version will be removed.
				# https://docs.opencv.org/3.0-beta/doc/py_tutorials/py_gui/py_video_display/py_video_display.html
from PIL import Image
import imagehash

IMG_FORMAT = '.jpg'
GEN_FILES_DEL = []
FONT_FILE = 'NanumGothic.ttf'
FILE_PATH = os.path.dirname(os.path.realpath(__file__))

def download_youtube(args):
	outpath = FILE_PATH
	url = args.url
	file_name = args.name
	caption_lang = args.lang
	caption_file = os.path.join(outpath, file_name + '.srt')
	video_file = os.path.join(outpath, file_name + '.mp4')
	video_infos = dict()

	yt = YouTube(url)
	video_infos['title'] = yt.title
	video_infos['thumbnail'] = yt.thumbnail_url.replace('default.jpg', 'maxresdefault.jpg')
	print('Downloading a video \"%s\"\n' %video_infos['title'])
	print('Thumbnail URL is \"%s\"\n' %video_infos['thumbnail'])
	'''
	high_resolution_thumbnail_url = pytube.YouTube(YOUR_youtube_url).thumbnail_url.replace('default.jpg', 'hqdefault.jpg')
	'''

	# Stream selection
	print(yt.streams.all())
	#stream = yt.streams.filter(file_extension='mp4').first() #TODO:
	stream = yt.streams.get_by_itag('18') #FIXME: itag:18-360p,mp4

	# Sream download
	stream.download(output_path=outpath, filename=file_name)
	GEN_FILES_DEL.append(video_file)

	# Caption download
	print(yt.captions.all())
	caption = yt.captions.get_by_language_code(caption_lang) #TODO: defalt:en, select:kor
	if caption:
		fp = open(caption_file, 'w')
		fp.write(caption.generate_srt_captions())
		print('Downloading a caption file \"%s\"\n' %caption_file)
		fp.close()
	else:
		print('Fail to download a caption file \"%s\"\n' %caption_file)
		sys.exit()
	GEN_FILES_DEL.append(caption_file)

	return video_file, caption_file, video_infos

def imshow_by_time(__frame, __fps, __fcnt, __duration, __sec):
	if (__fcnt % (__fps * __sec)) == 0:
		dur_str = '%f' %__duration
		cv2.putText(__frame, dur_str, (0, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0))
		cv2.imshow('Img show every %d second' %__sec, __frame)

def convert_to_sec(st):
	h, m, s, ms = st.replace(',', ':').split(':')
	tot_sec = int(h) * 3600 + int(m) * 60 + int(s)
	if (int(ms) > 500): tot_sec += 1

	return tot_sec

def get_split_time(ti, idx):
	subtime = ti.split(' --> ')
	return subtime[idx]

def get_srt_mean_time(ti):
	subtime = ti.split(' --> ')
	begin_ts = convert_to_sec(subtime[0]) #FIXME: get_split_time(ti, 0)
	end_ts = convert_to_sec(subtime[1]) #FIXME: get_split_time(ti, 1)

	return (begin_ts + end_ts) / 2

def remove_tags(text):
	cleanr =re.compile('<.*?>')
	cleantext = re.sub(cleanr, '', text)
	return cleantext

def get_ts_by_caption(caption_file):
	fp = open(caption_file, 'r')
	lines = fp.readlines()
	line_cnt = 0
	frame_infos = []

	while line_cnt < len(lines):
		if not lines[line_cnt]:
			break;

		frame_num = lines[line_cnt][:-1]
		line_cnt += 1
		time_info = lines[line_cnt][:-1]
		line_cnt += 1
		script = lines[line_cnt][:-1]
		line_cnt += 2

		ts_dict = dict()
		ts_dict['frame_num'] = frame_num
		ts_dict['time_info'] = get_srt_mean_time(time_info)
		ts_dict['script'] = remove_tags(script)
		ts_dict['hash'] = None
		ts_dict['sub_hash'] = None

		frame_infos.append(ts_dict)

	fp.close()

	return frame_infos, int(frame_num)

def merge_st_end_srt(st, end):
	return st + ' --> ' + end + '\n'

def gen_new_time_info(curr_t, next_t):
	curr_st = get_split_time(curr_t, 0)
	next_st = get_split_time(next_t, 0)

	return merge_st_end_srt(curr_st, next_st)

# FIXME: tmp solution: overlap subtitle issue for auto-genenated subtitle from a Youtube video
# convert start/end time of the .sub file
# 1st end-time will be 2st start-time
# 2st end-time will be 3st start-time
# ...
# Nst end-time does not need to modify
def modify_cap_time(args):
	outpath = FILE_PATH
	url = args.url
	file_name = args.name
	caption_lang = args.lang
	caption_file = os.path.join(outpath, file_name + '.srt')

	fp = open(caption_file, 'r')
	new_cap_file = caption_file + '.modified'
	if os.path.exists(new_cap_file):
		os.remove(new_cap_file)
	nfp = open(new_cap_file, 'a')

	lines = fp.readlines()
	line_cnt = 0

	while line_cnt < len(lines):
		if not lines[line_cnt]:
			break;

		# a final caption
		if line_cnt + 5 > len(lines):
			nfp.write(lines[line_cnt])
			nfp.write(lines[line_cnt + 1])
			nfp.write(lines[line_cnt + 2])
			break;

		frame_num = lines[line_cnt]
		nfp.write(frame_num)
		curr_time_info = lines[line_cnt + 1][:-1]
		next_time_info = lines[line_cnt + 5][:-1]
		modified_time_info = gen_new_time_info(curr_time_info, next_time_info)
		nfp.write(modified_time_info)
		nfp.write(lines[line_cnt + 2])
		nfp.write(lines[line_cnt + 3])

		line_cnt += 4

	# replace original srt to new srt
	if os.path.exists(new_cap_file):
		caption_file = new_cap_file
		GEN_FILES_DEL.append(caption_file)

	fp.close()
	nfp.close()

	return caption_file

def cv_show_images(__frame, __duration):
	dur_str = '%f' %__duration
	cv2.putText(__frame, dur_str, (0, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0))
	cv2.imshow('Img show by caption duration', __frame)

def cv_save_images(__frame, __duration, __path, __infos, __cnt): #TODO: try:except:
	dur_str = '%d, %f ' %(__cnt, __duration)
	cv2.putText(__frame, dur_str, (0, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0))
	cv2.imwrite(__path, __frame)

def compare_hash(prev, curr, thresh = 0):
	if abs(prev - curr) <= thresh:
		ret = True
	else:
		ret = False
	return ret

def crop_img(img, h_ratio=4):
	w, h = img.size # Get dimensions

	x = 0
	y = h - (h / h_ratio)
	wi = x + w
	he = y + (h - y)
	area = (x, y, wi, he)
	return area

def capture_video(args, target_file, caption_file):
	cap = cv2.VideoCapture(target_file)

	frame_infos, total_frames = get_ts_by_caption(caption_file)
	fps = int(cap.get(cv2.CAP_PROP_FPS))
	cap_cnt = 0
	fcnt = 0
	dup_cnt = 0

	outpath = FILE_PATH
	img_path = os.path.join(outpath, 'imgs')
	file_name = args.name
	caption_file = os.path.join(outpath, file_name + '.srt')
	font_size = args.fontsize
	no_add_caption = args.nosub

	if os.path.exists(img_path):
		print("remove %s" %img_path)
		shutil.rmtree(img_path, ignore_errors=True)
	os.mkdir(img_path)

	print("number of total frames: %d\ntime stamps of each images:\n" %total_frames)
	#print(frame_infos)

	while(cap_cnt < total_frames):
		ret, frame = cap.read()
		duration = float(fcnt) / float(fps)

		if (duration > frame_infos[cap_cnt].get('time_info')):
			#cv_show_images(frame, duration)

			# 1. Save image
			savepath = os.path.join(img_path, file_name + str(cap_cnt) + IMG_FORMAT) #TODO:imgs
			cv_save_images(frame, duration, savepath, frame_infos[cap_cnt], cap_cnt)

			# 2. Compare hash in case of --no-sub option.
			#    Need to compare if closed-caption was changed or not.
			if no_add_caption:
				img_ori = Image.open(savepath)
				#TODO: convert gray scale img_ori
				#TODO: crop_img: width should be more narrow
				area = crop_img(img_ori, h_ratio=4) #cropping caption area
				#print(area)
				img_c = img_ori.crop(area)

				frame_hash = imagehash.average_hash(img_c)
				prev_frame_hash = frame_infos[cap_cnt-1]['hash']
				#print(prev_frame_hash, frame_hash)

				# threah is tunnable value
				# With a highier value, It would delete more duplicated images.
				if prev_frame_hash and compare_hash(prev_frame_hash, frame_hash, thresh=1):
					print('.', end='', flush=True)
					shutil.move(savepath, savepath + 'dupli.jpg')
					dup_cnt +=1
					cap_cnt += 1
					fcnt += 1
					continue
				else:
					#print(frame_hash, prev_frame_hash)
					None

				frame_infos[cap_cnt]['hash'] = frame_hash

			# 3. Add caption text in plain frame
			else:
				text = frame_infos[cap_cnt].get('script')
				bake_caption(savepath, text, FONT_FILE, font_size) # add subtitle

			cap_cnt += 1
		fcnt += 1

		if cv2.waitKey(1) & 0xFF == ord('q'):
			break

	print('Done: %d duplicated image was deleted.' %dup_cnt)
	cap.release()
	cv2.destroyAllWindows()

	return total_frames, img_path

def wait_job_done(pool):
	for p in pool:
		p.wait()
		if p.returncode and p.returncode != 0:
			raise subprocess.CalledProcessError(p.returncode, p.args)

# This is ffmped command on bash shell
def make_ffmpeg_cmd(_input, _output, srt, font_size):
	return 'ffmpeg -i ' + _input + ' -vf' + ' subtitles=' + srt + ':force_style=\'Fontsize=' + str(font_size) + '\'' + ' -acodec copy ' + _output


def combine_caption(args, input_video, caption_file):
	bg_pool = []
	outpath = FILE_PATH
	output_video = args.name + '_sub' + '.mp4'

	path_output_video = os.path.join(outpath, output_video)
	if os.path.exists(path_output_video):
		os.remove(path_output_video)

	cmd = make_ffmpeg_cmd(input_video, output_video, caption_file, args.fontsize)
	bg_pool.append(subprocess.Popen([cmd], cwd=outpath, shell=True))
	wait_job_done(bg_pool)
	GEN_FILES_DEL.append(path_output_video)

	return path_output_video

def md_insert_hyperlink(src, link):
	return '[' + src + '](' + link + ')'

def md_insert_img(name, link):
	return '![' + name + '](' + link + ')  \n'

def md_insert_header(subject, depth):
	header = ''
	for i in range(depth):
		header += '#'
	header += ' ' + subject + '  \n'
	return header

def make_md_page(nr_img, path_img, name_img, video_infos):
	outpath = FILE_PATH
	md_file = os.path.join(outpath, name_img + '.md')
	fd = open(md_file, 'w')

	format_title = md_insert_header(video_infos['title'], 1)
	fd.write(format_title)
	format_thumbnail_img = md_insert_img('thumbnail', video_infos['thumbnail'])
	fd.write(format_thumbnail_img)

	for nr in range(nr_img):
		numberd_name = name_img + str(nr)
                #FIXME: /imgs/* path must be a reletive path
		#img = os.path.join(path_img, numberd_name) + IMG_FORMAT
		img = os.path.join('imgs', numberd_name) + IMG_FORMAT

		img_path = os.path.join(outpath, img)
		if os.path.exists(img_path):
			format_md_img = md_insert_img(numberd_name, img)
			fd.write(format_md_img)

	fd.close()

#TODO: is the caption has overlap issue?
def need_modify_cap():
	return True

def parse_args():
	parser = argparse.ArgumentParser(description='Screen capture automatically from Youtube video\nexample: python3 get_youtube.py -u <youtube link> -n <outfile name> -l <language> -f <fontsize>')
	parser.add_argument('-u', '--url', dest='url', help='Youtube vedio url')
	parser.add_argument('-n', '--name', dest='name', default='downloaded_video', help='Output file name')
	parser.add_argument('-l', '--lang', dest='lang', default='en', help='Caption language code (default: en)')
	parser.add_argument('-f', '--fontsize', dest='fontsize', default=30, type=int, help='Font size of caption (default: 30)')
	parser.add_argument('--no-sub', dest='nosub', action='store_true', help='If the video has a closed caption, no need to add caption additionally')

	args = parser.parse_args()
	print(args)
	return args

def main():
	args = parse_args()
	video, caption, infos = download_youtube(args)
	if need_modify_cap():
		caption = modify_cap_time(args)

	#video_sub = combine_caption(args, video, caption) #TODO:
	print(GEN_FILES_DEL)
	nr_imgs, img_path = capture_video(args, video, caption)
	make_md_page(nr_imgs, img_path, args.name, infos)

if __name__ == "__main__":
	main()
