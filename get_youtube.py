import os
import subprocess
import argparse
from pytube import YouTube	#pip3 install pytube
import cv2			#pip3 install opencv-python
				# If there would be "numpy.core.multiarray" problem of numpy
				#Do 'pip3 uninstall numpy' few times until all numpy version will be removed.
				# https://docs.opencv.org/3.0-beta/doc/py_tutorials/py_gui/py_video_display/py_video_display.html

URL=['https://youtu.be/Z78zbnLlPUA', 'https://www.youtube.com/watch?v=9bZkp7q19f0', 'https://youtube.com/watch?v=XJGiS83eQLk', 'https://www.youtube.com/watch?v=ph5UVsuqPUU'] #TODO:
OUTPATH = os.getcwd()
FILENAME = 'trello'
CAPTION_LANG = 'en'
CAPTION_FILE = os.path.join(OUTPATH, FILENAME + '.srt')
GEN_FILES_DEL = []

def download_youtube(args):
	outpath = os.getcwd()
	url = args.url
	file_name = args.name
	caption_lang = args.lang
	caption_file = os.path.join(outpath, file_name + '.srt')
	video_file = os.path.join(outpath, file_name + '.mp4')

	yt = YouTube(url)
	print('Downloading a video \"%s\"\n' %yt.title)

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
	fp = open(caption_file, 'w')
	fp.write(caption.generate_srt_captions())
	print('Downloading a caption file \"%s\"\n' %caption_file)
	GEN_FILES_DEL.append(caption_file)
	fp.close()

	return video_file, caption_file

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

def get_ts_by_caption(caption_file):
	fp = open(caption_file, 'r')
	lines = fp.readlines()
	line_cnt = 0
	ts_dict = dict()

	while line_cnt < len(lines):
		if not lines[line_cnt]:
			break;

		frame_num = lines[line_cnt][:-1]
		line_cnt += 1
		time_info = lines[line_cnt][:-1]
		line_cnt += 3

		ts_dict[int(frame_num)] = get_srt_mean_time(time_info)

	fp.close()

	return ts_dict, int(frame_num)

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
	outpath = os.getcwd()
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
		#os.remove(caption_file)  # FIXME:
		caption_file = new_cap_file
		GEN_FILES_DEL.append(caption_file)

	fp.close()
	nfp.close()

	return caption_file

def imshow_by_caption_dur(__frame, __duration):
	dur_str = '%f' %__duration
	cv2.putText(__frame, dur_str, (0, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0)) #Add text on frame
	cv2.imshow('Img show by caption duration', __frame)
	#TODO: save image


def capture_video(args, target_file, caption_file):
	cap = cv2.VideoCapture(target_file)

	cap_time_stamps, total_frames = get_ts_by_caption(caption_file)
	fps = int(cap.get(cv2.CAP_PROP_FPS))
	cap_cnt = 1
	fcnt = 0

	print(cap_time_stamps, total_frames)

	while(cap_cnt <= total_frames):
		ret, frame = cap.read()
		duration = float(fcnt) / float(fps)

		if (duration > cap_time_stamps[cap_cnt]):
			imshow_by_caption_dur(frame, duration)
			cap_cnt += 1
		fcnt += 1

		if cv2.waitKey(1) & 0xFF == ord('q'):
			break
	cap.release()
	cv2.destroyAllWindows()

def wait_job_done(pool):
	for p in pool:
		p.wait()
		if p.returncode and p.returncode != 0:
			raise subprocess.CalledProcessError(p.returncode, p.args)

# This is ffmped command on bash shell
def make_ffmpeg_cmd(_input, _output, srt):
	return 'ffmpeg -i ' + _input + ' -vf' + ' subtitles=' + srt + ' -acodec copy ' + _output

def combine_caption(args, input_video, caption_file):
	bg_pool = []

	output_video = args.name + '_sub' + '.mp4'

	path_output_video = os.path.join(OUTPATH, output_video)
	if os.path.exists(path_output_video):
		os.remove(path_output_video)

	cmd = make_ffmpeg_cmd(input_video, output_video, caption_file)
	bg_pool.append(subprocess.Popen([cmd], cwd=OUTPATH, shell=True))
	wait_job_done(bg_pool)
	GEN_FILES_DEL.append(path_output_video)

	return path_output_video

#TODO: is the caption has overlap issue?
def is_need_mod_cap():
	return True

def parse_args():
	#argparser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
	parser = argparse.ArgumentParser(description='Screen capture automatically from Youtube video')
	parser.add_argument('-u', '--url', dest='url', help='Youtube vedio url')
	parser.add_argument('-n', '--name', dest='name', default='downloaded_video', help='Output file name')
	parser.add_argument('-l', '--lang', dest='lang', default='en', help='Caption language')

	args = parser.parse_args()
	print(args)
	return args

def main():
	args = parse_args()
	video, caption = download_youtube(args)
	if is_need_mod_cap():
		caption = modify_cap_time(args)

	video_sub = combine_caption(args, video, caption) #TODO:
	print(GEN_FILES_DEL)
	capture_video(args, video_sub, caption)

if __name__ == "__main__":
	main()
