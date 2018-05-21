#!/usr/local/bin/python
# -*- coding: utf-8 -*-
#======================================================================
#
# netstream.py - network data stream operation interface
#
# NOTE: The Replacement of TcpClient 
#
#======================================================================

import socket
import select
import struct
import time
import sys
import errno


#======================================================================
# netstream - basic tcp stream
#======================================================================
class netstream(object):
	def __init__(self, fmt = 0):
		self.sock = 0
		self.wbuf = ''
		self.rbuf = ''
		self.stat = 0
		self.errd = ( errno.EINPROGRESS, errno.EALREADY, errno.EWOULDBLOCK )
		self.conn = ( errno.EISCONN, 10057, 10053 )
		self.errc = 0
		self.bfmt = 'H'
		if fmt != 0: self.bfmt = '!H'

	def __try_connect(self):
		if (self.stat == 2):
			return 1
		if (self.stat != 1):
			return -1
		try:
			self.sock.recv(0)
		except socket.error, (code, strerror):
			if code in self.conn:
				return 0
			if code in self.errd:
				self.stat = 2
				self.rbuf = ''
				return 1
			#sys.stderr.write('[TRYCONN] '+strerror+'\n')
			self.close()
			return -1
		self.stat = 2
		return 1

	def __try_recv(self):
		rdata = ''
		while 1:
			text = ''
			try:
				text = self.sock.recv(1024)
				if not text:
					self.errc = 10000
					self.close()
					return -1
			except socket.error,(code, strerror):
				if not code in self.errd:
					#sys.stderr.write('[TRYRECV] '+strerror+'\n')
					self.errc = code
					self.close()
					return -1
			if text == '':
				break
			rdata = rdata + text
		self.rbuf = self.rbuf + rdata
		return len(rdata)

	def __try_send(self):
		wsize = 0
		if (len(self.wbuf) == 0):
			return 0
		try:
			wsize = self.sock.send(self.wbuf)
		except socket.error,(code, strerror):
			if not code in self.errd:
				#sys.stderr.write('[TRYSEND] '+strerror+'\n')
				self.errc = code
				self.close()
				return -1
		self.wbuf = self.wbuf[wsize:]
		return wsize

	def connect(self, address, port):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setblocking(0)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
		self.sock.connect_ex((address, port))
		self.stat = 1
		self.wbuf = ''
		self.rbuf = ''
		self.errc = 0
		return 0

	def close(self):
		self.stat = 0
		if not self.sock:
			return 0
		try:
			self.sock.close()
		except:
			pass
		self.sock = 0
		return 0
	
	def assign(self, sock):
		self.close()
		self.sock = sock
		self.sock.setblocking(0)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
		self.stat = 2
	
	def process(self):
		if self.stat == 0:
			return 0
		if self.stat == 1:
			self.__try_connect()
		if self.stat == 2:
			self.__try_recv()
		if self.stat == 2:
			self.__try_send()
		return 0

	def status(self):
		return self.stat
	
	def error(self):
		return self.errc
	
	def sendraw(self, data):
		self.wbuf = self.wbuf + data
		self.process()
		return 0
	
	def peekraw(self, size):
		self.process()
		if len(self.rbuf) == 0:
			return ''
		if size > len(self.rbuf):
			size = len(self.rbuf)
		rdata = self.rbuf[0:size]
		return rdata
	
	def recvraw(self, size):
		rdata = self.peekraw(size)
		size = len(rdata)
		self.rbuf = self.rbuf[size:]
		return rdata
	
	def send(self, data):
		wsize = struct.pack(self.bfmt, len(data) + 2)
		self.sendraw(wsize + data)
		return 0
	
	def recv(self):
		rsize = self.peekraw(2)
		if (len(rsize) < 2):
			return ''
		size = struct.unpack(self.bfmt, rsize)
		if (len(self.rbuf) < size[0]):
			return ''
		self.recvraw(2)
		return self.recvraw(size[0] - 2)

	def nodelay(self, nodelay = 0):
		if not 'TCP_NODELAY' in socket.__dict__:
			return -1
		self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, nodelay)
		return 0


#======================================================================
# nethost - basic tcp host
#======================================================================
NET_NEW =		0	# new connection£º(id,tag) ip/d,port/w   <hid>
NET_LEAVE =		1	# lost connection£º(id,tag)   		<hid>
NET_DATA =		2	# data comming£º(id,tag) data...	<hid>
NET_TIMER =		3	# timer event: (none, none) 


#======================================================================
# nethost - basic tcp host
#======================================================================
class nethost(object):
	def __init__ (self, fmt = 0):
		self.host = 0
		self.stat = 0
		self.clients = []
		self.index = 1
		self.queue = []
		self.count = 0
		self.bfmt = 'H'
		self.sock = 0
		self.port = 0
		if fmt: self.bfmt = '!H'
		self.timeout = 70.0
		self.timeslap = long(time.time() * 1000)
		self.period = 0
	
	def startup(self, port = 0):
		self.shutdown()
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		try: self.sock.bind(('0.0.0.0', port))
		except: 
			try: self.sock.close()
			except: pass
			return -1
		self.sock.listen(65536)
		self.sock.setblocking(0)
		self.port = self.sock.getsockname()[1]
		self.stat = 1
		self.timeslap = long(time.time() * 1000)
		return 0

	def shutdown(self):
		if self.sock: 
			try: self.sock.close()
			except: pass
		self.sock = 0
		self.index = 1
		for n in self.clients:
			if not n: continue
			try: n.close()
			except: pass
		self.clients = []
		self.queue = []
		self.stat = 0
		self.count = 0
	
	def __close(self, hid, code = 0):
		pos = hid & 0xffff
		if (pos < 0) or (pos >= len(self.clients)): return -1
		client = self.clients[pos]
		if client == None: return -2
		if client.hid != hid: return -3
		client.close()
		return 0
	
	def __send(self, hid, data):
		pos = hid & 0xffff
		if (pos < 0) or (pos >= len(self.clients)): return -1
		client = self.clients[pos]
		if client == None: return -2
		if client.hid != hid: return -3
		client.send(data)
		client.process()
		return 0

	def process(self):
		current = time.time()
		if self.stat != 1: return 0
		sock = None
		try: 
			sock, remote = self.sock.accept()
			sock.setblocking(0)
		except: pass
		if self.count >= 0x10000:
			try: sock.close()
			except: pass
			sock = None
		if sock:
			pos = -1
			for i in xrange(len(self.clients)):
				if self.clients[i] == None:
					pos = i
					break
			if pos < 0:
				pos = len(self.clients)
				self.clients.append(None)
			hid = (pos & 0xffff) | (self.index << 16)
			self.index += 1
			if self.index >= 0x7fff: self.index = 1
			client = netstream(self.bfmt == '!H' and 1 or 0)
			client.assign(sock)
			client.hid = hid
			client.tag = 0
			client.active = current
			client.peername = sock.getpeername()
			self.clients[pos] = client
			self.count += 1
			self.queue.append((NET_NEW, hid, 0, repr(client.peername)))
		for pos in xrange(len(self.clients)):
			client = self.clients[pos]
			if not client: continue
			client.process()
			while client.status() == 2:
				data = client.recv()
				if data == '': break
				self.queue.append((NET_DATA, client.hid, client.tag, data))
				client.active = current
			timeout = current - client.active
			if (client.status() == 0) or (timeout >= self.timeout):
				hid, tag = client.hid, client.tag
				self.queue.append((NET_LEAVE, hid, tag, ''))
				self.clients[pos] = None
				client.close()
				del client
				self.count -= 1
		current = long(time.time() * 1000)
		if current - self.timeslap > 100000:
			self.timeslap = current
		period = self.period
		if period > 0:
			while self.timeslap < current:
				self.queue.append((NET_TIMER, 0, 0, ''))
				self.timeslap += period
		return 0

	def send(self, hid, data):
		return self.__send(hid, data)
	
	def close(self, hid):
		return self.__close(hid, hid)
	
	def settag(self, hid, tag = 0):
		pos = hid & 0xffff
		if (pos < 0) or (pos >= len(self.clients)): return -1
		client = self.clients[pos]
		if client == None: return -2
		if hid != client.hid: return -3
		client.tag = tag
		return 0
	
	def gettag(self, hid):
		pos = hid & 0xffff
		if (pos < 0) or (pos >= len(self.clients)): return -1
		client = self.clients[pos]
		if client == None: return -1
		if hid != client.hid: return -1
		return client.tag
	
	def read(self):
		if len(self.queue) == 0:
			return (-1, 0, 0, '')
		event = self.queue[0]
		self.queue = self.queue[1:]
		return event
	
	def settimer(self, millisec = 1000):
		if millisec <= 0: 
			millisec = 0
		self.period = millisec
		self.timeslap = long(time.time() * 1000)

	def nodelay (self, hid, nodelay = 0):
		pos = hid & 0xffff
		if (pos < 0) or (pos >= len(self.clients)): return -1
		client = self.clients[pos]
		if client == None: return -1
		if hid != client.hid: return -1
		return client.nodelay(nodelay)


#----------------------------------------------------------------------
# testing case
#----------------------------------------------------------------------
if __name__ == '__main__':
	host = nethost()
	host.startup(2000)
	sock = netstream()
	last = time.time()
	sock.connect('127.0.0.1', 2000)
	sock.send('Hello, world !!')
	stat = 0
	last = time.time()
	print 'service startup at port', host.port
	host.settimer(5000)
	sock.nodelay(0)
	sock.nodelay(1)
	while 1:
		time.sleep(0.1)
		host.process()
		sock.process()
		if stat == 0:
			if sock.status() == 2:
				stat = 1
				sock.send('Hello, world !!')
				last = time.time()
		elif stat == 1:
			if time.time() - last >= 3.0:
				sock.send('VVVV')
				stat = 2
		elif stat == 2:
			if time.time() - last >= 5.0:
				sock.send('exit')
				stat = 3
		event, wparam, lparam, data = host.read()
		if event < 0: continue
		print 'event=%d wparam=%xh lparam=%xh data="%s"'%(event, wparam, lparam, data)
		if event == NET_DATA:
			host.send(wparam, 'RE: ' + data)
			if data == 'exit': 
				print 'client request to exit'
				host.close(wparam)
		elif event == NET_NEW:
			host.send(wparam, 'HELLO CLIENT %X'%(wparam))
			host.settag(wparam, wparam)
			host.nodelay(wparam, 1)


