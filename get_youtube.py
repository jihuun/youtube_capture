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
from PIL import Image, ImageFilter, ImageEnhance
import PIL.ImageOps
import imagehash
import json
from collections import OrderedDict
from pytesseract import image_to_string

DEFAULT_L_CODE = 'en'
DEFAULT_VID_NAME = 'dl_video'
IMG_FORMAT = '.jpg'
GEN_FILES_DEL = []
FONT_FILE = 'NanumGothic.ttf'
FILE_PATH = os.path.dirname(os.path.realpath(__file__))
RESULT_DIR = 'results'

def is_caption_exist(cap_class, caption_lang):
	ret = None
	caplist = cap_class.all()
	print('Available language codes :',  end=' ', flush=True)
	for i in caplist:
		get_code = i.__dict__['code']
		print(get_code, end=' ', flush=True)
		if get_code == 'ko': # FIXME: defalut ko?
			ret = 'ko'
		if get_code == caption_lang:
			ret = caption_lang

	print('')
	return ret

def download_youtube(args):
	url = args.url
	yt = YouTube(url)

	file_name = args.name
	if file_name == DEFAULT_VID_NAME:
		file_name = yt.video_id

	outpath = os.path.join(FILE_PATH, RESULT_DIR) # youtube_cature/results/
	if not os.path.exists(outpath):
		os.mkdir(outpath)

	outpath = os.path.join(outpath, file_name) # youtube_cature/results/<file_name>/
	if os.path.exists(outpath):
		print('The requested video is already in the DB. No need to capture again.')
		sys.exit()
	else:
		os.mkdir(outpath)

	# Stream selection
	#print(yt.streams.all(), '\n')
	stream = yt.streams.get_by_itag('18') #FIXME: itag:18-360p,mp4 #TODO: if no itag:18?

	# Sream download
	stream.download(output_path=outpath, filename=file_name)

	caption_lang = args.lang
	caption_file = os.path.join(outpath, file_name + '.srt')
	video_file = os.path.join(outpath, file_name + '.mp4')
	GEN_FILES_DEL.append(caption_file)
	GEN_FILES_DEL.append(video_file)

	video_infos = OrderedDict()
	video_infos['url'] = url
	video_infos['title'] = stream.title #TODO: fix from issue - KeyError: 'title'
	video_infos['video_id'] = yt.video_id
	video_infos['lang_code'] = args.lang
	video_infos['font_size'] = args.fontsize
	video_infos['file_name'] = file_name
	video_infos['file_path'] = outpath
	video_infos['nosub_opt'] = args.nosub
	video_infos['imgdiff_opt'] = args.imgdiff
	video_infos['bg_opacity'] = args.bg_opacity
	video_infos['thumbnail'] = 'https://img.youtube.com/vi/%s/maxresdefault.jpg' %yt.video_id
	video_infos['frame_infos'] = None
	print('The video informations:')
	print(video_infos)

	# Check if the caption code is exist in the video
	#print(yt.captions.all())
	caption_code = is_caption_exist(yt.captions, caption_lang)

	if caption_code:
		caption = yt.captions.get_by_language_code(caption_code)
	else:
		print('\'%s\' language code does not exist. Please try again with option \'-l <code>\'.\nAnyway Checking default language code \'en\' is exist or not' %caption_lang)
		caption_code = DEFAULT_L_CODE #defalut language code

	# Caption download
	caption = yt.captions.get_by_language_code(caption_code)
	if caption:
		fp = open(caption_file, 'w')
		fp.write(caption.generate_srt_captions())
		print('Downloading a caption file \'%s\' with language code \'%s\' is done.\n'  %(caption_file, caption_code))
		fp.close()
	else:
		print('There is no caption in the Youtube video. Can not capture this video, Sorry. language code: \'%s\'\n' %(caption_code))
		sys.exit()

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
	length_lines = len(lines)

	while line_cnt < length_lines:
		if not lines[line_cnt]:
			break;

		if line_cnt + 3 > length_lines:
			break;

		frame_num = lines[line_cnt][:-1]
		line_cnt += 1
		time_info = lines[line_cnt][:-1]
		line_cnt += 1
		script = lines[line_cnt][:-1]
		line_cnt += 2

		ts_dict = OrderedDict()
		ts_dict['frame_num'] = int(frame_num) - 1
		ts_dict['img_path'] = None
		ts_dict['time_info'] = get_srt_mean_time(time_info)
		ts_dict['script'] = remove_tags(script)
		ts_dict['ocr_script'] = None
		ts_dict['hash'] = None
		ts_dict['sub_hash'] = None
		ts_dict['usage'] = 'ok'

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
def modify_cap_time(v_infos):
	outpath = v_infos['file_path']
	url = v_infos['url']
	file_name = v_infos['file_name']
	caption_lang = v_infos['lang_code']
	caption_file = os.path.join(outpath, file_name + '.srt')

	fp = open(caption_file, 'r')
	new_cap_file = caption_file + '.modified'
	if os.path.exists(new_cap_file):
		os.remove(new_cap_file)
	nfp = open(new_cap_file, 'a')

	lines = fp.readlines()
	line_cnt = 0
	lenth_lines = len(lines)

	while line_cnt < lenth_lines:
		if not lines[line_cnt]:
			break;

		# a final caption
		if line_cnt + 5 > lenth_lines:
			if line_cnt < lenth_lines:
				nfp.write(lines[line_cnt])
			if line_cnt + 1 < lenth_lines:
				nfp.write(lines[line_cnt + 1])
			if line_cnt + 2 < lenth_lines:
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

def cv_save_images(__frame, __duration, __path, __infos, __cnt, __tot_frame, __font_size): #TODO: try:except:
	rate = '%d/%d  %fs' %(__cnt, (__tot_frame - 1), __duration)
	font = cv2.FONT_HERSHEY_SIMPLEX
	font_scale = 0.8
	fs = round(__font_size * font_scale)
	pos = (10, fs + 10)
	color = (255, 255, 0) #(B,G,R)
	thickness = 1
	linetype = cv2.LINE_AA
	cv2.putText(__frame, rate, pos, font, font_scale, color, thickness, linetype)
	cv2.imwrite(__path, __frame)

def compare_hash(prev, curr, thresh = 0):
	if abs(prev - curr) <= thresh:
		ret = True
	else:
		ret = False
	return ret

# h_ratio: (1, 2, 3, ... )
# w_ratio: (0.0 ~ 1.0)
def crop_area(img, h_ratio=4, w_ratio=0.8):
	w, h = img.size # Get dimensions

	x = (w * (1 - w_ratio) * 0.5)
	y = (h - (h / h_ratio))
	wi = w - x
	he = y + (h - y)
	area = (x, y, wi, he)
	return area

def get_text_from_img(img):
	text = image_to_string(img, lang='kor', config='--psm 7')
	return text

def save_pil_img(pil_img, img_path):
	pil_img.save(img_path + '.jpg', 'JPEG')

# Image Pre-prosessing for better extracting the subscript text from the image by tesseract-ocr
def image_preprocess(img_orig, save_path=None):
	# 1. cropping caption area
	area = crop_area(img_orig, h_ratio=7, w_ratio=0.9) #cropping caption area
	img_crop = img_orig.crop(area)

	# 2. convert to grayscale
	img_gray = img_crop.convert('L') # grayscale image

	# convert to blur : not use
	img_gray_gaussian = img_gray.filter(ImageFilter.GaussianBlur(1))

	# 3. convert to low contrast for better edge detecting
	img_contrast_low = ImageEnhance.Contrast(img_gray_gaussian).enhance(0.7)

	# 4. get outline of text by edge detection
	img_outline = img_contrast_low.filter(ImageFilter.FIND_EDGES)

	# 5. change black background to white
	img_outline_invert = PIL.ImageOps.invert(img_outline)
	#save_pil_img(img_gray, img_path + '/gray_img_%d' % cap_cnt)
	#save_pil_img(img_contrast_low, img_path + '/img_contrast_low_%d' % cap_cnt)
	save_pil_img(img_outline_invert, save_path + '_outline.jpg')

	return img_outline_invert

def capture_by_subtitle(cap, v_infos, caption_file, img_path_name):

	frame_infos, total_frames = get_ts_by_caption(caption_file)
	fps = int(cap.get(cv2.CAP_PROP_FPS))
	font_size = v_infos['font_size']
	no_add_caption = v_infos['nosub_opt']
	background_opacity = float(v_infos['bg_opacity'])
	cap_cnt = 0
	fcnt = 0
	dup_cnt = 0

	print("number of total frames: %d\nProcessing" %total_frames)

	while(cap_cnt < total_frames):
		ret, frame = cap.read()
		duration = float(fcnt) / float(fps)

		if (duration > frame_infos[cap_cnt].get('time_info')):
			#cv_show_images(frame, duration)

			# 1. Save image
			img_name_numbered = img_path_name + '_0' + str(cap_cnt)
			savepath = img_name_numbered + IMG_FORMAT
			cv_save_images(frame, duration, savepath, frame_infos[cap_cnt], cap_cnt, total_frames, font_size)


			# 2. Compare hash in case of --no-sub option.
			#    Need to compare if closed-caption was changed or not.
			if no_add_caption:
				img_orig = Image.open(savepath)
				# Image Preprosessing
				preprocessed_img = image_preprocess(img_orig, img_name_numbered)

				frame_hash = imagehash.average_hash(preprocessed_img)

				prev_frame_hash = None
				prev_frame_hash_str = frame_infos[cap_cnt-1]['sub_hash']
				if prev_frame_hash_str:
					prev_frame_hash = imagehash.hex_to_hash(prev_frame_hash_str)

				# Save hash value with string
				frame_infos[cap_cnt]['sub_hash'] = '%s' %frame_hash

				# extract a script from the image using Tesseract-ocr
				frame_infos[cap_cnt]['ocr_script'] = get_text_from_img(preprocessed_img)

				# The threah is a tunnable value
				# With a highier value, It would delete more duplicated images.
				'''
				if prev_frame_hash and compare_hash(prev_frame_hash, frame_hash, thresh=0):
					print('.', end='', flush=True)
					savepath_dup = savepath + '.dupli.jpg'
					shutil.move(savepath, savepath_dup)
					frame_infos[cap_cnt]['img_path'] = savepath_dup
					frame_infos[cap_cnt]['usage'] = 'duplicated'
					dup_cnt +=1
					cap_cnt += 1
					fcnt += 1
					continue
				else:
					None
				'''

			# 3. Add caption text in plain frame
			else:
				text = frame_infos[cap_cnt].get('script')
				bake_caption(savepath, text, FONT_FILE, font_size, background_opacity)

			frame_infos[cap_cnt]['img_path'] = savepath
			cap_cnt += 1

		fcnt += 1

		if cv2.waitKey(1) & 0xFF == ord('q'):
			break

	print('Done: %d duplicated image was deleted.' %dup_cnt)
	return frame_infos, total_frames

def cv_to_pil(cv_img):
	cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
	pil_img = Image.fromarray(cv_img)

	return pil_img

def capture_by_image_diff(cap, v_infos, img_path_name):
	fps = int(cap.get(cv2.CAP_PROP_FPS))
	tot_fcnt = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
	play_time = tot_fcnt / fps

	print(fps, tot_fcnt, play_time)

	cap_cnt = 0
	frame_no = 0
	dup_cnt = 0
	total_frames = round(play_time)
	frame_infos = []

	while (frame_no < tot_fcnt):
		cap.set(1, frame_no);
		ret, frame = cap.read()

		img_name_numbered = img_path_name + '_0' + str(cap_cnt)
		savepath = img_name_numbered + IMG_FORMAT
		cv2.imwrite(savepath, frame)

		#print(frame_no, cap_cnt)

		ts_dict = OrderedDict()
		ts_dict['frame_num'] = frame_no
		ts_dict['img_path'] = None
		ts_dict['time_info'] = cap_cnt
		ts_dict['script'] = None
		ts_dict['ocr_script'] = None
		ts_dict['hash'] = None
		ts_dict['sub_hash'] = None
		ts_dict['usage'] = 'ok'
		frame_infos.append(ts_dict)

		#TODO:
		img_orig = cv_to_pil(frame)

		# Image Preprosessing
		preprocessed_img = image_preprocess(img_orig, img_name_numbered)

		# get image-hash
		frame_hash = imagehash.average_hash(preprocessed_img)
		prev_frame_hash = None
		prev_frame_hash_str = frame_infos[cap_cnt-1]['sub_hash']
		if prev_frame_hash_str:
			prev_frame_hash = imagehash.hex_to_hash(prev_frame_hash_str)

		# Save hash value with string
		frame_infos[cap_cnt]['sub_hash'] = '%s' %frame_hash

		# The threah is a tunnable value
		# With a highier value, It would delete more duplicated images.
		if prev_frame_hash and compare_hash(prev_frame_hash, frame_hash, thresh=0):
			print('.', end='', flush=True)
			savepath_dup = savepath + '.dupli.jpg'
			shutil.move(savepath, savepath_dup)
			frame_infos[cap_cnt]['img_path'] = savepath_dup
			frame_infos[cap_cnt]['usage'] = 'duplicated'
			dup_cnt +=1

		cap_cnt += 1
		frame_no = fps * cap_cnt

	print('Done: %d duplicated image was deleted.' %dup_cnt)

	return frame_infos, total_frames


def capture_video(v_infos, target_file, caption_file):
	cap = cv2.VideoCapture(target_file)

	outpath = v_infos['file_path']
	img_path = os.path.join(outpath, 'imgs')
	file_name = v_infos['file_name']
	img_path_name = os.path.join(img_path, file_name)
	caption_file = os.path.join(outpath, file_name + '.srt')
	img_diff_opt = v_infos['imgdiff_opt']

	if os.path.exists(img_path):
		print("remove %s" %img_path)
		shutil.rmtree(img_path, ignore_errors=True)
	os.mkdir(img_path)

	# if no-sub is false
	if img_diff_opt:
		frame_infos, total_frames = capture_by_image_diff(cap, v_infos, img_path_name)
	else:
		frame_infos, total_frames = capture_by_subtitle(cap, v_infos, caption_file, img_path_name)

	cap.release()
	cv2.destroyAllWindows()

	return total_frames, img_path, frame_infos

def wait_job_done(pool):
	for p in pool:
		p.wait()
		if p.returncode and p.returncode != 0:
			raise subprocess.CalledProcessError(p.returncode, p.args)

# This is ffmped command on bash shell
# Not using anymore
def make_ffmpeg_cmd(_input, _output, srt, font_size):
	return 'ffmpeg -i ' + _input + ' -vf' + ' subtitles=' + srt + ':force_style=\'Fontsize=' + str(font_size) + '\'' + ' -acodec copy ' + _output


def combine_caption(v_infos, input_video, caption_file):
	bg_pool = []
	outpath = v_infos['file_path']
	output_video = v_infos['file_name'] + '_sub' + '.mp4'

	path_output_video = os.path.join(outpath, output_video)
	if os.path.exists(path_output_video):
		os.remove(path_output_video)

	cmd = make_ffmpeg_cmd(input_video, output_video, caption_file, v_infos['font_size'])
	bg_pool.append(subprocess.Popen([cmd], cwd=outpath, shell=True))
	wait_job_done(bg_pool)
	GEN_FILES_DEL.append(path_output_video)

	return path_output_video

def md_insert_hyperlink(src, link):
	return '[' + src + '](' + link + ')  \n'

def md_insert_img(name, link):
	return '![' + name + '](' + link + ')  \n'

def md_insert_header(subject, depth):
	header = ''
	for i in range(depth):
		header += '#'
	header += ' ' + subject + '  \n----\n'
	return header

def make_md_page(v_infos, nr_img, path_img, video_infos):
	print(nr_img)
	outpath = v_infos['file_path']
	name_img = v_infos['file_name']
	#url = args.url.lstrip("'").rstrip("'")
	url = v_infos['url'].lstrip("'").rstrip("'")

	md_file = os.path.join(outpath, name_img + '.md')
	fd = open(md_file, 'w')

	format_title = md_insert_header(video_infos['title'], 1)
	fd.write(format_title)
	format_source = md_insert_hyperlink('Source: ' + url, url)
	fd.write(format_source)
	format_thumbnail_img = md_insert_img('thumbnail', video_infos['thumbnail'])
	fd.write(format_thumbnail_img)

	for nr in range(nr_img):
		numberd_name = name_img + '_0' + str(nr)
                #FIXME: /imgs/* path must be a reletive path
		#img = os.path.join(path_img, numberd_name) + IMG_FORMAT
		img = os.path.join('imgs', numberd_name) + IMG_FORMAT

		img_path = os.path.join(outpath, img)
		if os.path.exists(img_path):
			format_md_img = md_insert_img(numberd_name, img)
			fd.write(format_md_img)

	format_source = md_insert_hyperlink('Source: ' + url, url)
	fd.write(format_source)
	fd.close()

def get_num_img_path(outpath, name_img, num):
	numberd_name = name_img + '_0' + str(num)
	img = os.path.join('imgs', numberd_name) + IMG_FORMAT
	img_path = os.path.join(outpath, img)

	return img_path

def get_img_size(img_path):
	img = Image.open(img_path)
	return img.size

def make_single_picture(v_infos, nr_img, path_img, video_infos):
	outpath = v_infos['file_path']
	name_img = v_infos['file_name']
	url = v_infos['url'].lstrip("'").rstrip("'")
	x = 0
	y = 0
	img0_path = get_num_img_path(outpath, name_img, 0)
	tot_w, tot_h = get_img_size(img0_path)
	tot_h = tot_h * nr_img

	print('Result image size: %d x %d' %(tot_w, tot_h))
	result = Image.new("RGB", (tot_w, tot_h))

	for nr in range(nr_img):
		img_path = get_num_img_path(outpath, name_img, nr)

		if os.path.exists(img_path):
			# append pic under the orig pic
			img_append = Image.open(img_path)
			w, h = img_append.size
			img_append.thumbnail((w, h), Image.ANTIALIAS)
			result.paste(img_append, (x, y, x + w, y + h))
			y = y + h

	result.save(os.path.join(outpath, name_img + '_conbined.jpg'))

#TODO: is the caption has overlap issue?
def need_modify_cap():
	return True

def parse_args():
	parser = argparse.ArgumentParser(description='Screen capture automatically from Youtube video\nexample: python3 get_youtube.py -u <youtube link> -n <outfile name> -l <language> -f <fontsize>')
	parser.add_argument('-u', '--url', dest='url', help='Youtube vedio url')
	parser.add_argument('-n', '--name', dest='name', default=DEFAULT_VID_NAME, help='Output file name')
	parser.add_argument('-l', '--lang', dest='lang', default=DEFAULT_L_CODE, help='Caption language code (default: en)')
	parser.add_argument('-f', '--fontsize', dest='fontsize', default=30, type=int, help='Font size of caption (default: 30)')
	parser.add_argument('-b', '--bg-opacity', dest='bg_opacity', default=0, type=float, help='Add backgound behind of caption text with opacity (0.0 ~ 1.0) (default opacity : 0.0)')
	parser.add_argument('--no-sub', dest='nosub', action='store_true', help='If the video has a closed caption, no need to add caption additionally')
	parser.add_argument('--img-diff', dest='imgdiff', action='store_true', help='capture frame by imagediff')

	args = parser.parse_args()
	print(args)
	return args

def make_json(v_infos):
	outpath = v_infos['file_path']
	file_name = v_infos['file_name']
	json_file = os.path.join(outpath, file_name + '.json')

	if os.path.exists(json_file):
		os.remove(json_file)

	fd = open(json_file, 'w')
	v_infos_json = json.dumps(v_infos, ensure_ascii=False, indent="\t")
	fd.write(v_infos_json)

def del_unneccesary_files(gen_files):
	print('These unneccesary files are removed\n', gen_files)
	for f in gen_files:
		if os.path.exists(f):
			os.remove(f)

def main():
	args = parse_args()
	video, caption, v_infos = download_youtube(args)
	if need_modify_cap():
		caption = modify_cap_time(v_infos)

	nr_imgs, img_path, f_infos = capture_video(v_infos, video, caption)
	make_md_page(v_infos, nr_imgs, img_path, v_infos)

	v_infos['frame_infos'] = f_infos
	make_json(v_infos)
	del_unneccesary_files(GEN_FILES_DEL)
	make_single_picture(v_infos, nr_imgs, img_path, v_infos)

if __name__ == "__main__":
	main()
