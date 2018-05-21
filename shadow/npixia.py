#======================================================================
#
# npixia.py - pixia in python
#
# NOTE:
# for more information, please see the readme file 
# 
#======================================================================
import sys, os
import ctypes
import sys as _sys
from ctypes import c_long, c_char_p, c_voidp, c_int, c_short, c_byte
from ctypes import POINTER, CFUNCTYPE, pointer, byref, c_uint32
from ctypes import cast, addressof, cdll, Structure

if 'wintypes' in ctypes.__dict__:
	from ctypes.wintypes import *
if 'windll' in ctypes.__dict__:
	from ctypes import windll


DLLNAME = 'pixianew'
def loaddll(name):
	try: return ctypes.cdll.LoadLibrary(name)
	except: pass
	return None

lib = loaddll(DLLNAME)
if lib == None:
	for n in sys.path:
		lib = loaddll(os.path.join(n, DLLNAME))
		if lib: break
if not lib:
	raise 'cannot load %s'%DLLNAME

__export = lib.npixia_export
__export.argtypes = [ c_char_p ]
__export.restype = c_voidp

def export(name, funtype = None):
	result = __export(name)
	if not result: 
		raise StandardError('can not export %s'%name)
	if not funtype: 
		return result
	ptr = funtype(result)
	return ptr


#----------------------------------------------------------------------
# IBITMAP structure
#----------------------------------------------------------------------
class IBITMAP(ctypes.Structure):

	_fields_ = [ 
		("w", c_long),
		("h", c_long),
		("bpp", c_long),
		("pitch", c_long),
		("mask", c_long),
		("code", c_long),
		("mode", c_long),
		("pixel", c_voidp),
		("extra", c_voidp),
		("line", c_voidp)
	]

	__father_del = False
	__pointer = None
	destructor = None

	def release(self):
		if self.destructor:
			try: self.destructor(self)
			except: pass
			self.destructor = None
		self.__pointer = None

	def __del__(self):
		self.release()
		try: 
			if '__del__' in ctypes.Structure.__dict__:
				if not self.__father_del:
					super(IBITMAP, self).__del__()
		except: pass
		self.__father_del__ = True
	
	def address(self):
		if self.__pointer == None:
			self.__pointer = cast(self, c_voidp)
		return self.__pointer
	


LPIBITMAP = POINTER(IBITMAP)

#----------------------------------------------------------------------
# bitmap methods
#----------------------------------------------------------------------
_bmp_create		= export('ibitmap_create', CFUNCTYPE(c_voidp, c_int, c_int, c_int))
_bmp_release	= export('ibitmap_release', CFUNCTYPE(None, LPIBITMAP))
_bmp_blit		= export('ibitmap_blit', CFUNCTYPE(c_int, LPIBITMAP, c_int, c_int, 
					LPIBITMAP, c_int, c_int, c_int, c_int, c_uint32, c_int))
_bmp_fill		= export('ibitmap_fill', CFUNCTYPE(c_int, LPIBITMAP, c_int, c_int,
					c_int, c_int, c_uint32, c_int))
_bmp_funcset	= export('ibitmap_funcset', CFUNCTYPE(c_int, c_int, c_voidp))


def __release_bmp(self):
	ptr = pointer(self)
	if ptr: _bmp_release(ptr)
	#print '__release_bmp'
	#print 'xx'

def ibitmap_create(w, h, bpp = 32):
	ptr = _bmp_create(w, h, bpp)
	if not ptr:
		raise Exception, ('ibitmap_create', w, h, bpp)
	bmp = cast(ptr, POINTER(IBITMAP))[0]
	bmp.destructor = __release_bmp
	return bmp

def ibitmap_blit(dst, x, y, src, sx = 0, sy = 0, sw = -1, sh = -1, cmask = None):
	mode = 1
	if cmask == None: cmask = 0
	else: mode = 3
	if sw < 0: sw = src.w
	if sh < 0: sh = src.h
	return _bmp_blit(dst, x, y, src, sx, sy, sw, sh, cmask, mode)

def ibitmap_fill(dst, x, y, w, h, col = 0, noclip = 0):
	return _bmp_fill(dst, x, y, w, h, col, noclip)

def ibitmap_funcset(id, func):
	return _bmp_funcset(id, func)


#----------------------------------------------------------------------
# x86 optimaze
#----------------------------------------------------------------------
_x86_choose_blitter = export('_x86_choose_blitter', CFUNCTYPE(None, ))
_x86_choose_blitter()
ibitmap_funcset(0, 0)


#----------------------------------------------------------------------
# win32 export
#----------------------------------------------------------------------
_wincreate	= export('iWinCreate', CFUNCTYPE(c_int, c_int, c_int, c_char_p, c_int))
_winclose	= export('iWinClose', CFUNCTYPE(c_int, ))
_winresize	= export('iWinSizeClient', CFUNCTYPE(None, c_int, c_int))
_winmessage	= export('iWinMessage', CFUNCTYPE(c_int, ))
_winhandle	= export('iWinHandle', CFUNCTYPE(c_long, ))
_winvisible	= export('iWinShow', CFUNCTYPE(None, c_int))
_winexitmsg	= export('iWinExitMsg', CFUNCTYPE(c_int, ))
_wincaption	= export('iWinCaption', CFUNCTYPE(None, c_char_p))
_winkey		= export('iWinKey', CFUNCTYPE(c_int, c_int))
_winmouse	= export('iWinMouse', CFUNCTYPE(c_int, POINTER(c_int), 
				POINTER(c_int), POINTER(c_int)))
_winkreset	= export('iWinKeyClear', CFUNCTYPE(None, ))
_winmreset	= export('iWinMouseClear', CFUNCTYPE(None, ))
_wincenter	= export('iWinCenterPos', CFUNCTYPE(None, c_long))
_wingetdc	= export('iWinGetDC', CFUNCTYPE(c_long, ))
_winresetdc	= export('iWinReleaseDC', CFUNCTYPE(None, ))
_windraw2dc	= export('idraw2dc', CFUNCTYPE(None, c_long, c_int, c_int, c_int, 
				c_int, LPIBITMAP, c_int, c_int, c_int, c_int))


def draw2dc(hdc, x, y, w, h, bmp, sx = 0, sy = 0, sw = -1, sh = -1):
	if sw < 0: sw = w
	if sh < 0: sh = h
	_windraw2dc(hdc, x, y, w, h, bmp, sx, sy, sw, sh)

#----------------------------------------------------------------------
# win32 class
#----------------------------------------------------------------------
class __win(object):

	def __init__(self):
		self.__created = False
		self.__handle = 0
		self.__dc = 0
		self.__w = 0
		self.__h = 0
	
	def __del__(self):
		if self.__created:
			try: self.close()
			except: pass

	def create(self, w = 640, h = 480, caption = None, mode = 0):
		if caption == None:
			caption = sys.argv[0]
		caption = str(caption)
		result = _wincreate(w, h, caption, mode)
		if result != 0:
			raise 'create window error %d'%result
		self.__handle = _winhandle()
		self.__dc = 0
		for i in xrange(100):
			self.process()
		self.__w = w
		self.__h = h
	
	def close(self):
		self.__created = False
		self.__handle = 0
		self.__dc = 0
		self.__w = 0
		self.__h = 0
		_winclose()
	
	def handle(self):
		return self.__handle
	
	def resize(self, w, h):
		_winresize(w, h)
		self.__w = w
		self.__h = h
	
	def process(self):
		return _winmessage()
	
	def visible(self, isvisible = True):
		_winvisible(isvisible)
	
	def caption(self, caption = ''):
		_wincaption(caption)
	
	def keyon(self, key):
		if type(key) == type(''):
			key = ord(str(key[:1]).upper())
		return _winkey(key)
	
	def mouse(self):
		x = ctypes.c_int()
		y = ctypes.c_int()
		b = ctypes.c_int()
		_winmouse(byref(x), byref(y), byref(b))
		return (x, y, b)
	
	def reset_input():
		_winkreset()
		_winmreset()
	
	def beclosing(self):
		return _winexitmsg() and True or False
	
	def center(self):
		_wincenter(self.__handle)
	
	def getdc(self):
		if self.__dc == 0:
			self.__dc = _wingetdc()
		return self.__dc
	
	def releasedc(self):
		if self.__dc > 0:
			_winresetdc()
		self.__dc = 0
	
	def update(self, bmp, x = 0, y = 0, w = -1, h = -1, sx = 0, sy = 0, 
				sw = -1, sh = -1, restdc = True):
		if w < 0: w = bmp.w
		if h < 0: h = bmp.h
		if sw < 0: sw = bmp.w
		if sh < 0: sh = bmp.h
		if self.__handle == 0: return 0
		draw2dc(self.getdc(), x, y, w, h, bmp, sx, sy, sw, sh)
		if restdc:
			self.releasedc()
		return 0


win = __win()

__pic_load_file = export('ipic_load_file', CFUNCTYPE(LPIBITMAP, c_char_p, c_long, c_voidp))
__pic_convert  = export('ipic_convert', CFUNCTYPE(LPIBITMAP, LPIBITMAP, c_int, c_voidp))
__pic_save_bmp = export('isave_bmp_file', CFUNCTYPE(int, c_char_p, LPIBITMAP, c_voidp))
__pic_save_tga = export('isave_tga_file', CFUNCTYPE(int, c_char_p, LPIBITMAP, c_voidp))
__pic_save_gif = export('isave_gif_file', CFUNCTYPE(int, c_char_p, LPIBITMAP, c_voidp))

__palette = ctypes.create_string_buffer('\x00' * 256 * 4)

def pic_load(name, destbpp = 0, pos = 0, pal = None):
	if pal == None: pal = __palette
	ptr = __pic_load_file(name, pos, pal)
	if not ptr: 
		raise Exception, ('pic_load', name, pos)
	bmp = cast(ptr, LPIBITMAP)[0]
	bmp.destructor = __release_bmp
	if destbpp > 0:
		tmp = bmp
		bmp = __pic_convert(pointer(tmp), destbpp, pal)[0]
		del tmp
	return bmp


#----------------------------------------------------------------------
# font printer
#----------------------------------------------------------------------
# void _ipixel_font_put(IBITMAP *bmp, int x, int y, ICOLORD col, int mode,
#	const char *text, int size)
__ipixel_font_put = export('_ipixel_font_put', CFUNCTYPE(None, 
	LPIBITMAP, c_int, c_int, c_uint32, c_int, c_char_p, c_int))

def ipixel_font_put(bmp, x, y, text, col = 0, mode = 0):
	__ipixel_font_put(bmp, x, y, col, mode, text, len(text))

def drawtext(bmp, x, y, text, col = 0xff00ff, mode = 1):
	ipixel_font_put(bmp, x, y, text, col, mode)


#----------------------------------------------------------------------
# package installation
#----------------------------------------------------------------------
def install_package(name, code):
	import imp
	packname = '%s.%s'%(__name__, name)
	if __name__ == '__main__': 
		packname = name
	if packname in _sys.modules:
		return False
	module = imp.new_module(name)
	_sys.modules[packname] = module
	exec code in module.__dict__
	_sys.modules[__name__].__dict__[name] = module
	return True


#----------------------------------------------------------------------
# package keys
#----------------------------------------------------------------------
package_keys = '''
VK_LBUTTON = 1
VK_RBUTTON = 2
VK_CANCEL = 3
VK_MBUTTON = 4
VK_BACK = 8
VK_TAB = 9
VK_CLEAR = 12
VK_RETURN = 13
VK_SHIFT = 16
VK_CONTROL = 17
VK_MENU = 18
VK_PAUSE = 19
VK_CAPITAL = 20
VK_ESCAPE = 0x1B
VK_SPACE = 32
VK_PRIOR = 33
VK_NEXT = 34
VK_END = 35
VK_HOME = 36
VK_LEFT = 37
VK_UP = 38
VK_RIGHT = 39
VK_DOWN = 40
VK_SELECT = 41
VK_PRINT = 42
VK_EXECUTE = 43
VK_SNAPSHOT = 44
VK_INSERT = 45
VK_DELETE = 46
VK_HELP = 47
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_APPS = 0x5D
VK_NUMPAD0 = 0x60
VK_NUMPAD1 = 0x61
VK_NUMPAD2 = 0x62
VK_NUMPAD3 = 0x63
VK_NUMPAD4 = 0x64
VK_NUMPAD5 = 0x65
VK_NUMPAD6 = 0x66
VK_NUMPAD7 = 0x67
VK_NUMPAD8 = 0x68
VK_NUMPAD9 = 0x69
VK_MULTIPLY = 0x6A
VK_ADD = 0x6B
VK_SEPARATOR = 0x6C
VK_SUBTRACT = 0x6D
VK_DECIMAL = 0x6E
VK_DIVIDE = 0x6F
VK_F1 = 0x70
VK_F2 = 0x71
VK_F3 = 0x72
VK_F4 = 0x73
VK_F5 = 0x74
VK_F6 = 0x75
VK_F7 = 0x76
VK_F8 = 0x77
VK_F9 = 0x78
VK_F10 = 0x79
VK_F11 = 0x7A
VK_F12 = 0x7B
VK_F13 = 0x7C
VK_F14 = 0x7D
VK_F15 = 0x7E
VK_F16 = 0x7F
VK_F17 = 0x80
VK_F18 = 0x81
VK_F19 = 0x82
VK_F20 = 0x83
VK_F21 = 0x84
VK_F22 = 0x85
VK_F23 = 0x86
VK_F24 = 0x87
VK_NUMLOCK = 0x90
VK_SCROLL = 0x91
VK_LSHIFT = 0xA0
VK_RSHIFT = 0xA1
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_LMENU = 0xA4
VK_RMENU = 0xA5
VK_PROCESSKEY = 0xE5
VK_ATTN = 0xF6
VK_CRSEL = 0xF7
VK_EXSEL = 0xF8
VK_EREOF = 0xF9
VK_PLAY = 0xFA
VK_ZOOM = 0xFB
VK_NONAME = 0xFC
VK_PA1 = 0xFD
VK_OEM_CLEAR = 0xFE
'''

install_package('winkeys', package_keys)



#----------------------------------------------------------------------
# testing case
#----------------------------------------------------------------------
if __name__ == '__main__':
	b = ibitmap_create(800, 600, 16)
	d = pic_load('monkey.bmp', 16)
	#print b.w, b.h, b.bpp
	win.create(800, 600)
	import time
	from winkeys import *
	x, y = 0, 0
	fps_count = 0
	fps_time = time.time()
	a1 = pic_load('resource/aircraft1.gif', 16)
	a2 = pic_load('resource/game1.tga', 16)

	while not win.beclosing():
		win.process()
		#time.sleep(0.01)
		if win.keyon('Q'):
			break
		if win.keyon(VK_UP): y -= 2
		if win.keyon(VK_DOWN): y += 2
		if win.keyon(VK_LEFT): x -= 2
		if win.keyon(VK_RIGHT): x += 2
		ibitmap_blit(b, 0, 0, d)
		ibitmap_blit(b, x, y, a1, cmask = 0xf81f)
		drawtext(b, 0, 0, 'hahahaha')
		win.update(b)
		current = time.time()
		last = current - fps_time
		fps_count += 1
		if last >= 1.0:
			fps = fps_count / last
			fps_time = current
			fps_count = 0
			win.caption('fps %.2f'%fps)
	win.close()
	import winkeys
	#print dir(winkeys)


