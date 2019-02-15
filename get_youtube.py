# Convert Youtube to images
# Author: Ji-Hun Kim (jihuun.k@gmail.com)
# v0.1.0

from pytube import YouTube	#pip3 install pytube
import cv2			#pip3 install opencv-python
				# If there would be "numpy.core.multiarray" problem of numpy
				#Do 'pip3 uninstall numpy' few times until all numpy version will be removed.
				# https://docs.opencv.org/3.0-beta/doc/py_tutorials/py_gui/py_video_display/py_video_display.html

# TODO: build_bg_pool.append(subprocess.Popen([cmd], cwd='../hlos', shell=True, stdin=PIPE, stderr    =PIPE))

URL=['https://youtu.be/Z78zbnLlPUA', 'https://www.youtube.com/watch?v=9bZkp7q19f0', 'https://youtube.com/watch?v=XJGiS83eQLk']
OUTPATH='/home/jihuun/project/scripts/'
FILENAME='file1'
CAPTION_LANG='en'

def download_youtube():

	yt = YouTube(URL[2])
	print('Downloading a video \"%s\"\n' %yt.title)

	# Stream selection
	#print(yt.streams.all())
	stream = yt.streams.first()

	# Sream download
	stream.download(output_path=OUTPATH, filename=FILENAME)

	# Caption download
	#print(yt.captions.all())
	caption = yt.captions.get_by_language_code(CAPTION_LANG)
	fp = open(OUTPATH + FILENAME + '.srt', 'w')
	fp.write(caption.generate_srt_captions())
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

def get_mean_value(ti):
	subtime = ti.split(' --> ')
	begin_ts = convert_to_sec(subtime[0])
	end_ts = convert_to_sec(subtime[1])

	return (begin_ts + end_ts) / 2

def get_ts_by_caption():
	fp = open(OUTPATH + FILENAME + '.srt', 'r')
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

		ts_dict[int(frame_num)] = get_mean_value(time_info)

	fp.close()

	return ts_dict, int(frame_num)

def imshow_by_caption_dur(__frame, __duration):
	dur_str = '%f' %__duration
	cv2.putText(__frame, dur_str, (0, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0)) #Add text on frame
	cv2.imshow('Img show by caption duration', __frame)


def capture_video():
	cap = cv2.VideoCapture(OUTPATH + FILENAME + '.mp4')

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


if __name__ == "__main__":
	download_youtube()
	#combine_caption()
	capture_video()

