import sys, os, time
from header import *

CS_PING		= 0x6001
CS_LOGIN	= 0x6002
CS_UPDATE	= 0x6003
CS_PHASE	= 0x6004

SC_PING		= 0x8001
SC_CONFIRM  = 0x8002
SC_UPDATE	= 0x8003
SC_REFRESH	= 0x8004

timestart = time.time()
timenow = lambda : int(int((time.time() - timestart) * 1000) & 0x7fffffff)


class cs_ping(lazy_header):
	def __init__ (self, current = -1):
		super(cs_ping, self).__init__(CS_PING)
		if current < 0: current = timenow()
		self.append_param("current", current, "I")

class sc_ping(lazy_header):
	def __init__ (self, current = -1):
		super(sc_ping, self).__init__(SC_PING)
		if current < 0: current = timenow()
		self.append_param("current", current, "I")

class cs_login(lazy_header):
	def __init__ (self, name = ''):
		super(cs_login, self).__init__(CS_LOGIN)
		self.append_param("name", name, "s")

class sc_confirm(lazy_header):
	def __init__ (self, entity = 0, timebase = 0, name = ''):
		super(sc_confirm, self).__init__(SC_CONFIRM)
		self.append_param("entity", entity, "I")
		self.append_param("timebase", timebase, "I")
		self.append_param("name", name, "s")

class cs_update(lazy_header):
	def __init__ (self, entity = 0, frame = 0, x = 0, y = 0, d = 0, v = 1):
		super(cs_update, self).__init__(CS_UPDATE)
		self.append_param("entity", entity, "I")
		self.append_param("frame", frame, "I")
		self.append_param("x", x, "i")
		self.append_param("y", y, "i")
		self.append_param("d", d, "i")
		self.append_param("v", v, "i")
		self.append_param("debug", '', "s")

class cs_phase(lazy_header):
	def __init__ (self, phaselag = 0):
		super(cs_phase, self).__init__(CS_PHASE)
		self.append_param("phaselag", phaselag, "I")

class sc_update(lazy_header):
	def __init__ (self, entity = 0, frame = 0, x = 0, y = 0, d = 0, v = 1):
		super(sc_update, self).__init__(SC_UPDATE)
		self.append_param("entity", entity, "I")
		self.append_param("frame", frame, "I")
		self.append_param("x", x, "i")
		self.append_param("y", y, "i")
		self.append_param("d", d, "i")
		self.append_param("v", v, "i")
		self.append_param("debug", '', "s")

class sc_refresh(object):
	def __init__ (self, phaselag = 0):
		self.update = []
		self.phaselag = phaselag
	def __len__ (self):
		return len(self.update)
	def __getitem__ (self, index):
		return self.update[index]
	def __setitem__ (self, index, value):
		self.update[index] = value
	def append(self, update):
		data = sc_update()
		data.entity = update.entity
		data.frame = update.frame
		data.x = update.x
		data.y = update.y
		data.d = update.d
		data.v = update.v
		data.debug = update.debug
		self.update.append(data)
	def marshal(self):
		from struct import pack
		data = pack('=HHH', SC_REFRESH, self.phaselag, len(self.update))
		for update in self.update:
			d = update.marshal()
			data += pack('=H', len(d)) + d
		return data
	def unmarshal(self, data):
		from struct import unpack
		if len(data) < 4: 
			raise 'sc_refresh.unmarshal error: length < 4'
		event, phaselag, count = unpack("=HHH", data[:6])
		self.phaselag = phaselag
		pos = 6
		self.update = []
		update = sc_update()
		for i in xrange(count):
			size = unpack("=H", data[pos:pos+2])[0]
			update.unmarshal(data[pos+2:pos+2+size])
			pos += 2 + size
			self.append(update)
		return 0
	def next(self):
		return self.update.next()
	def clean(self):
		self.update = []


if __name__ == '__main__':
	refresh = sc_refresh(phaselag=10)
	update = sc_update()
	for i in xrange(10): 
		update.entity = i
		refresh.append(update)
	d = refresh.marshal()
	refresh = sc_refresh()
	print len(refresh)
	refresh.unmarshal(d)
	print len(refresh)
	for u in refresh: 
		print 'entity', u.entity
	print 'phaselag =', refresh.phaselag


