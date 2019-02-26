# This code is referenced from https://blog.lipsumarium.com/caption-memes-in-python/

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

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



def drawText(img, draw, msg, pos, font, size):
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
		draw.text((textX-PAD, textY-PAD),lines[i],(0,0,0),font=font)
		draw.text((textX+PAD, textY-PAD),lines[i],(0,0,0),font=font)
		draw.text((textX+PAD, textY+PAD),lines[i],(0,0,0),font=font)
		draw.text((textX-PAD, textY+PAD),lines[i],(0,0,0),font=font)
		draw.text((textX, textY),lines[i],(255,255,255),font=font)
		lastY = textY

	return

def bake_caption(img_file, msg, font_file, font_size):
	img = Image.open(img_file)
	draw = ImageDraw.Draw(img)
	font = ImageFont.truetype(font_file, font_size)
	drawText(img, draw, msg, "bottom", font, font_size)
	img.save(img_file)

	#print("Baking caption done")
	print('.', end='', flush=True)

	return
