import os
import subprocess
from pytube import YouTube	#pip3 install pytube
import cv2			#pip3 install opencv-python
				# If there would be "numpy.core.multiarray" problem of numpy
				#Do 'pip3 uninstall numpy' few times until all numpy version will be removed.
				# https://docs.opencv.org/3.0-beta/doc/py_tutorials/py_gui/py_video_display/py_video_display.html

URL=['https://youtu.be/Z78zbnLlPUA', 'https://www.youtube.com/watch?v=9bZkp7q19f0', 'https://youtube.com/watch?v=XJGiS83eQLk', 'https://www.youtube.com/watch?v=ph5UVsuqPUU'] #TODO:
OUTPATH='/home/jihuun/project/scripts/youtube_capture' #TODO:
#FILENAME='file1'
FILENAME='trello'
CAPTION_LANG='en'
CAPTION_FILE = OUTPATH + '/' + FILENAME + '.srt'

def download_youtube(url):

	url = URL[3]
	yt = YouTube(url)
	print('Downloading a video \"%s\"\n' %yt.title)

	# Stream selection
	#print(yt.streams.all())
	stream = yt.streams.first() #TODO:

	# Sream download
	stream.download(output_path=OUTPATH, filename=FILENAME)

	# Caption download
	print(yt.captions.all())
	caption = yt.captions.get_by_language_code(CAPTION_LANG) #TODO: defalt:en, select:kor
	fp = open(CAPTION_FILE, 'w')
	fp.write(caption.generate_srt_captions())
	print('Downloading a caption file \"%s\"\n' %CAPTION_FILE)
	fp.close()


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

def get_ts_by_caption():
	fp = open(CAPTION_FILE, 'r')
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
def modify_cap_time():
	global CAPTION_FILE
	fp = open(CAPTION_FILE, 'r')
	new_cap_file = CAPTION_FILE + '.modified'
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
		#os.remove(CAPTION_FILE)  # FIXME:
		CAPTION_FILE = new_cap_file

	fp.close()
	nfp.close()


def imshow_by_caption_dur(__frame, __duration):
	dur_str = '%f' %__duration
	cv2.putText(__frame, dur_str, (0, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0)) #Add text on frame
	cv2.imshow('Img show by caption duration', __frame)
	#TODO: save image


def capture_video(target_file):
	#cap = cv2.VideoCapture(OUTPATH + FILENAME + '.mp4')
	cap = cv2.VideoCapture(target_file)

	cap_time_stamps, total_frames = get_ts_by_caption()
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

def make_ffmpeg_cmd(_input, _output, srt):
	return 'ffmpeg -i ' + _input + ' -vf' + ' subtitles=' + srt + ' -acodec copy ' + _output

def combine_caption():
	bg_pool = []

	caption_file = FILENAME + '.srt' + '.modified'
	input_video = FILENAME + '.mp4'
	output_video = FILENAME + '_sub' + '.mp4'

	path_output_video = OUTPATH + '/' + output_video
	if os.path.exists(path_output_video):
		os.remove(path_output_video)

	cmd = make_ffmpeg_cmd(input_video, output_video, caption_file)
	bg_pool.append(subprocess.Popen([cmd], cwd=OUTPATH, shell=True))
	wait_job_done(bg_pool)

	return OUTPATH + '/' + output_video

#TODO: is the caption has overlap issue?
def is_need_mod_cap():
	return True

def main():
	download_youtube(url)
	if is_need_mod_cap():
		modify_cap_time()

	video_file = combine_caption() #TODO:
	capture_video(video_file)

if __name__ == "__main__":
	main()
