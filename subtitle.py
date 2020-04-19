#! /usr/bin/env python3
import datetime
import srt
# See usage of srt module: https://srt.readthedocs.io/
# datetime: https://minus31.github.io/2018/07/28/python-date/
import pysrt
import copy
import pprint
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

# using pysrt module
class srt_to_list(list):
    def __init__(self, srt_file):
        subs = pysrt.open(srt_file)
        self.make_frame_list(subs)

    def make_frame_list(self, subs):
        for idx, sub in enumerate(subs):
            ts = self.calc_timestamp(sub.start.seconds, sub.end.seconds)
            script = sub.text
            frame = self.set_ts_dict(idx, ts, script)
            self.append(frame)

    def calc_timestamp(self, st, ed):
        return st + float((ed - st) / 2)

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

# using srt module: deprecated
class srt_to_list_deprecated(list):
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

FONT_FILE = 'NanumGothic.ttf'
FONT_SIZE = 30
PAD = 1

def drawTextWithOutline(text, x, y):
	draw.text((x-PAD, y-PAD), text,(0,0,0),font=font)
	draw.text((x+PAD, y-PAD), text,(0,0,0),font=font)
	draw.text((x+PAD, y+PAD), text,(0,0,0),font=font)
	draw.text((x-PAD, y+PAD), text,(0,0,0),font=font)
	draw.text((x, y), text, (255,255,255), font=font)
	return


def make_bg_color(bg_opacity):
	if bg_opacity > 1:
		bg_opacity = 1
	elif bg_opacity < 0:
		bg_opacity = 0
	op = round(255 * bg_opacity)
	return (0,0,0,op)

def drawText(img, draw, msg, pos, font, size, bg_opacity):
	fontSize = size
	lines = []

	w, h = draw.textsize(msg, font)
	imgWidthWithPadding = img.width * 0.99

	# 1. how many lines for the msg to fit ?
	lineCount = 1
	if(w > imgWidthWithPadding):
		lineCount = int(round((w / imgWidthWithPadding) + 1))

	if lineCount > 2:
		while 1:
			fontSize -= 2
			w, h = draw.textsize(msg, font)
			lineCount = int(round((w / imgWidthWithPadding) + 1))
			#print("try again with fontSize={} => {}".format(fontSize, lineCount))
			if lineCount < 3 or fontSize < 10:
				break


	#print("img.width: {}, text width: {}".format(img.width, w))
	#print("Text length: {}".format(len(msg)))
	#print("Lines: {}".format(lineCount))


	# 2. divide text in X lines
	lastCut = 0
	isLast = False
	for i in range(0,lineCount):
		if lastCut == 0:
			cut = int((len(msg) / lineCount) * i)
		else:
			cut = lastCut

		if i < lineCount-1:
			nextCut = int((len(msg) / lineCount) * (i+1))
		else:
			nextCut = len(msg)
			isLast = True

		#print("cut: {} -> {}".format(cut, nextCut))

		# make sure we don't cut words in half
		if nextCut == len(msg) or msg[nextCut] == " ":
			None
		else:
			#print("may not cut")
			while msg[nextCut] != " ":
				nextCut += 1
			#print("new cut: {}".format(nextCut))

		line = msg[cut:nextCut].strip()

		# is line still fitting ?
		w, h = draw.textsize(line, font)
		if not isLast and w > imgWidthWithPadding:
			#print("overshot")
			nextCut -= 1
			while msg[nextCut] != " ":
				nextCut -= 1
			#print("new cut: {}".format(nextCut))

		lastCut = nextCut
		lines.append(msg[cut:nextCut].strip())

	# 3. print each line centered
	lastY = -h
	if pos == "bottom":
		lastY = img.height - h * (lineCount+1) - 10

	for i in range(0,lineCount):
		w, h = draw.textsize(lines[i], font)
		textX = img.width/2 - w/2
		#if pos == "top":
		#	textY = h * i
		#else:
		#	textY = img.height - h * i
		textY = lastY + h
		# background
		if bg_opacity:
			bg_color = make_bg_color(bg_opacity)
			draw.rectangle(((textX, textY), (textX+w, textY+h)), fill=bg_color)
		draw.text((textX-PAD, textY-PAD),lines[i],(0,0,0),font=font)
		draw.text((textX+PAD, textY-PAD),lines[i],(0,0,0),font=font)
		draw.text((textX+PAD, textY+PAD),lines[i],(0,0,0),font=font)
		draw.text((textX-PAD, textY+PAD),lines[i],(0,0,0),font=font)
		draw.text((textX, textY),lines[i],(255,255,255),font=font)
		lastY = textY

	return

# FIXME: refactoring to class
# This code is referenced from https://blog.lipsumarium.com/caption-memes-in-python/
def bake_caption(img_file, msg, font_file, font_size, bg_opacity):
	img = Image.open(img_file)
	draw = ImageDraw.Draw(img, 'RGBA')
	font = ImageFont.truetype(font_file, font_size)
	drawText(img, draw, msg, "bottom", font, font_size, bg_opacity)
	img.save(img_file)
	print('.', end='', flush=True)
	return

def main():
    a = srt_to_list('/Users/jihuun/project/youtube_capture/test_data/MMmOLN5zBLY/MMmOLN5zBLY.srt')
    pprint.pprint(a)

if __name__ == '__main__':
    main()
