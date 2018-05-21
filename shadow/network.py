# -*- coding: utf-8 -*-
import sys, os, time, random
import netstream

from events import *
from netstream import NET_NEW, NET_LEAVE, NET_DATA


#----------------------------------------------------------------------
# network latency simulator
#----------------------------------------------------------------------
class netstream_delay(object):
	def __init__ (self, delay = 0.0):
		self.netstream = netstream.netstream()
		self.delay = int(delay * 1000) / 2
		self.noisy = int(self.delay * 2 / 3)
		self.tbase = time.time()
		self.block = 0
		self.sendmsg = []
		self.recvmsg = []
	def __current(self):
		return long((time.time() - self.tbase)* 1000)
	def __noisy(self):
		return self.delay - self.noisy / 2 + random.randint(0, self.noisy)
	def setdelay(self, delay = 0.0):
		self.delay = int(delay * 1000) / 2
		self.noisy = int(self.delay * 2 / 3)
	def setblock(self, block):
		self.block = block
	def process(self):
		current = self.__current()
		while self.block == 0:
			if len(self.sendmsg) == 0: break
			data, slap = self.sendmsg[0]
			if current < slap: break
			self.sendmsg = self.sendmsg[1:]
			self.netstream.send(data)
		self.netstream.process()
		while 1:
			data = self.netstream.recv()
			if data == '': break
			slap = current + self.__noisy()
			self.recvmsg.append((data, slap))
	def connect(self, ip, port):
		self.netstream.connect(ip, port)
		self.sendmsg = []
		self.recvmsg = []
		self.block = 0
	def assign(self, sock):
		self.netstream.assign(sock)
		self.sendmsg = []
		self.recvmsg = []
		self.block = 0
	def close(self):
		self.netstream.close()
		self.sendmsg = []
		self.recvmsg = []
		self.block = 0
	def status(self):
		return self.netstream.status()
	def error(self):
		return self.netstream.error()
	def send(self, data):
		current = self.__current()
		slap = current + self.__noisy()
		self.sendmsg.append((data, slap))
		self.process()
		return 0
	def recv(self):
		self.process()
		current = self.__current()
		if (len(self.recvmsg) == 0) or (self.block): return ''
		data, slap = self.recvmsg[0]
		if current < slap: return ''
		self.recvmsg = self.recvmsg[1:]
		return data


#----------------------------------------------------------------------
# hostaddr
#----------------------------------------------------------------------
def hostaddr():
	table = []
	try:
		import fcntl
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		total = 32 * 128
		bytes = array.array('B', '\0' * total)
		point = struct.pack('iL', total, bytes.buffer_info()[0])
		size = struct.unpack('iL', fcntl.ioctl(s.fileno(), 0x8912, point))[0]
		result = [ bytes[i:i+32].tostring() for i in range(0, size, 32) ]
		table = [ '.'.join(['%d'%ord(v) for v in n[-12:-8]]) for n in result ]
		s.close()
	except: table = socket.gethostbyname_ex(socket.gethostname())[2]
	return table

#----------------------------------------------------------------------
# gameaddr
#----------------------------------------------------------------------
def gameaddr(hostc = ''):
	f = lambda a: socket.inet_aton(a)
	table, result = hostaddr(), []
	if not hostc in [ '0.0.0.0', '127.0.0.1', '' ]: return hostc
	for i in xrange(len(table)):
		addr, a = table[i], f(table[i])
		if addr == '127.0.0.1': result.append((-1, addr))
		elif (a >= f('10.0.0.0') and a <= f('10.255.255.255')): 
			result.append((i, addr))
		elif (a >= f('172.16.0.0') and a <= f('172.31.255.255')):
			result.append((i, addr))
		elif (a >= f('192.168.0.0') and a <= f('192.168.255.255')):
			result.append((i, addr))
		else:
			result.append((i + len(table), addr))
	result.sort()
	return result[-1][1]


def __test_delay():
	host = netstream.nethost()
	host.startup()
	client = netstream_delay(0.15)
	client.connect('127.0.0.1', host.port)
	timeslap = time.time()
	print 'delay', client.delay, client.noisy
	while 1:
		time.sleep(0.001)
		host.process()
		client.process()
		current = time.time()
		if current - timeslap >= 2.0:
			timeslap = current
			client.send(str(current))
		while 1:
			event, wparam, lparam, data = host.read()
			if event < 0: break
			if event == NET_DATA:
				host.send(wparam, data)
		client.process()
		data = client.recv()
		if data != '':
			past = int((current - float(data)) * 1000)
			print 'ping %dms'%past, data, current
	host.shutdown()


if __name__ == '__main__':
	print gameaddr()
	__test_delay()

