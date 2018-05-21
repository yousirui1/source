import sys, os, time

from npixia import *
from npixia.winkeys import *
import random as _random


screen = ibitmap_create(800, 600, 16)

textmap = ibitmap_create(320, 256, 16)
textbox = ibitmap_create(40, 40, 16)
shadow1 = ibitmap_create(32, 32, 16)
shadow2 = ibitmap_create(32, 32, 16)

aircraft1 = None
aircraft2 = None
textlines = []

MAX_STAR = 64

stars = []

random = lambda n: _random.randint(0, n)

for i in xrange(MAX_STAR):
	stars.append([ random(800), -100 + random(800) ])

c = 0x528a

ibitmap_fill(textbox, 0, 0, 40, 40, 0)

ibitmap_fill(textbox, 0, 0, 4, 1, c)
ibitmap_fill(textbox, 36, 0, 4, 1, c)
ibitmap_fill(textbox, 0, 0, 1, 4, c)
ibitmap_fill(textbox, 39, 0, 1, 4, c)
ibitmap_fill(textbox, 0, 39, 4, 1, c)
ibitmap_fill(textbox, 36, 39, 4, 1, c)
ibitmap_fill(textbox, 0, 36, 1, 4, c)
ibitmap_fill(textbox, 39, 36, 1, 4, c)

def init():
	global aircraft1
	global aircraft2
	global stars
	global shadow1
	global shadow2
	win.create(800, 600, 'Shadow Tracing')
	aircraft1 = pic_load('aircraft1.gif', 16)
	aircraft2 = pic_load('aircraft2.gif', 16)
	if (not aircraft1) or (not aircraft2):
		return -1
	ibitmap_blit(shadow1, 0, 0, aircraft1)
	ibitmap_blit(shadow2, 0, 0, aircraft2)
	c = 0xf81f
	for y in xrange(32):
		if y % 2 == 0: continue
		for x in xrange(32):
			if x % 2 == 0: continue
			ibitmap_fill(shadow1, x + 1, y + 1, 1, 1, c)
			ibitmap_fill(shadow2, x + 1, y + 1, 1, 1, c)
			ibitmap_fill(shadow1, x + 1, y + 0, 1, 1, c)
			ibitmap_fill(shadow2, x + 1, y + 0, 1, 1, c)
			ibitmap_fill(shadow1, x + 0, y + 1, 1, 1, c)
			ibitmap_fill(shadow2, x + 0, y + 1, 1, 1, c)
	return 0

def close():
	win.close()

def update():
	win.update(screen)

def caption(text = ''):
	if text: text = ' - %s'%text
	win.caption('Shadow Tracing' + text)

def clean():
	col = 0x120025
	col = 0
	ibitmap_fill(screen, 0, 0, 800, 600, col)

def output(text):
	global textlines, textmap
	if len(textlines) >= 10: 
		textlines = textlines[1:]
	textlines.append(str(text).strip('\r\n'))
	ibitmap_fill(textmap, 0, 0, 320, 256)
	for n in xrange(len(textlines)):
		drawtext(textmap, 0, n * 16, textlines[n], 0x888888)
	return 0

def log(text):
	current = time.strftime('%H:%M:%S', time.localtime())
	output('[%s] %s'%(current, str(text).strip('\r\n')))

def __update_text():
	ibitmap_blit(screen, 4, 600 - 200, textmap, 0, 0, 320, 256, 0)

def __update_craft(x, y, id = 0):
	global screen, aircraft1, aircraft2
	aircraft = aircraft1
	if id == 1: aircraft = aircraft2
	elif id == 2: aircraft = shadow1
	elif id == 3: aircraft = shadow2
	ibitmap_blit(screen, x - 16, y - 16, aircraft, cmask = 0xf81f) 

def __update_stars():
	global screen, stars
	limit = MAX_STAR / 3
	for i in xrange(len(stars)):
		star = stars[i]
		star[1] += (i < limit) and 5 or 3
		if star[1] >= 600:
			star[0], star[1] = random(800), (-200 + random(150))
		w, h, c = 1, 2, 0x7bef
		if i < limit: w, h, c = 2, 3, 0xbdd7
		ibitmap_fill(screen, star[0], star[1], w, h, c, noclip = 0)

def draw_shadow(x, y, id):
	global screen, textbox
	__update_craft(x, y, (id & 1) + 2)
	ibitmap_blit(screen, x - 20, y - 20, textbox, cmask = 0)

def draw_craft(x, y, id):
	global screen
	__update_craft(x, y, (id & 1))




pinglist = [ 0 for i in xrange(25) ]
pingnow = 0
pingtime = time.time() + 1.0
phaselag = 0

def record_ping(ping):
	global pingnow
	pingnow = ping

def __update_ping():
	global pinglist, pingnow, pingtime, phaselag
	current = time.time()
	while current >= pingtime:
		pingtime += 1.0
		pinglist = pinglist[1:]
		pinglist.append(pingnow)
	for i in xrange(25):
		p = pinglist[i]
		c = 0x8410
		y = p * 30 / 200
		if p >= 200: c = 0x7800
		if y > 30: y = 30
		if p < 150: c = 0x400
		if p == 0: continue
		ibitmap_fill(screen, 742 + 2 * i, 4, 1, y, c)
	text = "RTT: %3dms                   PhaseLag %s (press Enter to switch)"
	text = text%(pingnow, ('OFF ','ON  ')[phaselag])
	drawtext(screen, 4, 4, text, 0x777777, 3)

def newframe():
	clean()
	__update_stars()

def flush():
	__update_text()
	__update_ping()
	update()

def wait():
	for i in xrange(10): win.process()
	time.sleep(0.001)
	if win.beclosing(): return -1
	return 0

keylist = (
	( VK_UP, VK_DOWN, VK_LEFT, VK_RIGHT ),
	( 'W', 'S', 'A', 'D' ),
	( 'I', 'K', 'J', 'L' ),
	( 'T', 'G', 'F', 'H' ))

user32 = ctypes.windll.LoadLibrary("user32.dll")
GetAsyncKeyState = user32.GetAsyncKeyState
GetAsyncKeyState.restype = ctypes.c_short
GetAsyncKeyState.argtypes = [ ctypes.c_int ]

keyon = lambda n: win.keyon(n)

def AsyncKeyState(n):
	if type(n) == type(0): return GetAsyncKeyState(n)
	return GetAsyncKeyState(ord(n))

def keyboard_dir(id = 0, keydef = None):
	if id < 0: id = 0
	if id > 3: id = 3
	key = [ keylist[id][i] for i in xrange(4) ]
	if keydef:
		try: key = [ keydef[i] for i in xrange(4) ]
		except: pass
	for i in xrange(4):
		key[i] = keyon(key[i])
	d = 0
	if key[0] == 1:
		if key[2] == 1: d = 8
		elif key[3] == 1: d = 2
		else: d = 1
	if key[1] == 1:
		if key[2] == 1: d = 6
		elif key[3] == 1: d = 4
		else: d = 5
	if d == 0:
		if key[2] == 1: d = 7
		if key[3] == 1: d = 3
	return d
		



if __name__ == '__main__':
	init()
	current = time.time()
	while not win.beclosing():
		win.process()
		clean()
		__update_stars()
		__update_craft(400, 300, 0)
		__update_craft(440, 300, 1)
		__update_craft(480, 300, 2)
		__update_craft(520, 300, 3)
		draw_shadow(580, 300, 0)
		ibitmap_blit(screen, 320, 240, textbox, cmask = 0)
		record_ping(random(300))
		flush()
		time.sleep(0.005)
		if time.time() - current >= 1.0:
			current = time.time()
			d = keyboard_dir(0)
			log('update time ' + str(time.time()) + ' ' + str(d))


