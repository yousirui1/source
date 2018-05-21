# -*- coding: utf-8 -*-
#======================================================================
#
# game.py - main logic of shadow game
#
# NOTE:
# for more information, please see the readme file
#
#======================================================================
import sys, os, time, random, struct
import drawing, events, network, netstream

timestart = time.time()
timenow = lambda : int(int((time.time() - timestart) * 1000) & 0x7fffffff)


ctimebase = 0
ctimesvr = 0

ctimenow = lambda : ctimesvr + (timenow() - ctimebase)
middle = lambda begin, n, end: max(begin, min(n, end))


direction = ( (0, 0), (0, -1), (1, -1), (1, 0), (1, 1), 
	(0, 1), (-1, 1), (-1, 0), (-1, -1) )


#----------------------------------------------------------------------
# 战斗机对象：包含主体(entity)/影子(shadow)坐标
#----------------------------------------------------------------------
class aircraft(object):
	def __init__ (self, id = 0):
		self.x = 0
		self.y = 0
		self.d = 0
		self.v = 0
		self.sx = 0
		self.sy = 0
		self.sd = 0
		self.sv = 0
		self.id = id
		self.mode = -1
		self.name = ''
		self.trace_mode = 1
	# 绘制影子
	def draw_shadow(self):
		drawing.draw_shadow(self.sx, self.sy, self.id)
		drawing.drawtext(drawing.screen, self.sx + 4, self.sy - 20, 
			'S%d'%(self.id+1), 0x111111)
	# 绘制主角
	def draw_craft(self):
		drawing.draw_craft(self.x, self.y, self.id)
		drawing.drawtext(drawing.screen, self.x - 20, self.y - 20, 
			'P%d'%(self.id+1), 0x222222)
	# 影子移动
	def shadow_move(self, step = 0):
		sx, sy, sd, sv = self.sx, self.sy, self.sd, self.sv
		inc = 1
		if step < 0: 
			step = -step
			inc = -1
		for i in xrange(step):
			sx += sv * direction[sd][0] * inc
			sy += sv * direction[sd][1] * inc
			sx = middle(0, sx, 800)
			sy = middle(0, sy, 600) 
		self.sx, self.sy = sx, sy
	# 飞船移动
	def craft_move(self, step = 0):
		x, y, d, v = self.x, self.y, self.d, self.v
		for i in xrange(step):
			x += v * direction[d][0]
			y += v * direction[d][1]
			x = middle(0, x, 800)
			y = middle(0, y, 600)
		self.x, self.y = x, y
	# 初始化
	def initpos(self):
		self.x = 400 - 40 * 4 + self.id * 40
		self.y = 350
		self.v = 3
		self.d = 0
		self.sx, self.sy, self.sv, self.sd = self.x, self.y, self.v, self.d
		return 0
	# 影子插值
	def adjust(self, curframe, oldframe):
		self.shadow_move(curframe - oldframe)
		return 0
	# 跟随方式1：同步跟随
	def trace1(self, step = 0):
		sx, sy, sd, sv = self.sx, self.sy, self.sd, self.sv
		x, y = self.x, self.y
		v2 = sv * 2
		for i in xrange(step):
			if x < sx: x += min(sx - x, v2)
			elif x > sx: x -= min(x - sx, v2)
			if y < sy: y += min(sy - y, v2)
			elif y > sy: y -= min(y - sy, v2)
		self.x, self.y = x, y
	# 跟随方式2：相位滞后
	def trace2(self, step = 0):
		sx, sy, sd, sv = self.sx, self.sy, self.sd, self.sv
		x, y = self.x, self.y
		v2 = sv * 2
		def newpos(x, sx):
			if x == sx: return x
			if x < sx:
				d1 = min(sx - x, v2)
				d2 = min(sx - x, sv)
				if sx - x > sv * 35: x += d1
				else: x += d2
			elif x > sx:
				d1 = min(x - sx, v2)
				d2 = min(x - sx, sv)
				if x - sx > sv * 35: x -= d1
				else: x -= d2
			return x
		for i in xrange(step):
			x = newpos(x, sx)
			y = newpos(y, sy)
		self.x, self.y = x, y
	def trace(self, step = 0):
		if self.trace_mode == 0: 
			self.trace1(step)
		else:
			self.trace2(step)


#client = network.netstream_delay(0.15)

FRAME_DELAY = 20

#----------------------------------------------------------------------
# 客户端逻辑
#----------------------------------------------------------------------
class cclient(object):
	def __init__ (self):
		self.client = network.netstream_delay(0.15) 
		self.crafts = [ aircraft(i) for i in xrange(8) ]
		self.timebase = timenow()
		self.timesvr = 0
		self.myself = -1
		self.state = 0
		self.craft = self.crafts[0]
		self.frame = 0
		self.frameslap = 0
		self.recvmsg = []
		self.update = events.cs_update()
		self.refresh = events.sc_refresh()
		self.current = 0
		self.phaselag = 0
		self.phasekey = 0
	def startup(self, ip, port, delay = 0.150):
		self.client.connect(ip, port)
		self.client.setdelay(delay)
		#self.client.setdelay(0.0)
		drawing.record_ping(200)
		print 'connect to %s:%d ...'%(ip, port),
		self.state = 1
	def __current(self):
		return self.timesvr + timenow() - self.timebase
	def process(self):
		if self.state == 1:
			self.client.process()
			if self.client.status() == 2:
				print 'ok'
				data = events.cs_login().marshal()
				self.client.send(data)
				self.state = 2
			if self.client.status() == 0:
				print 'faild'
				self.state = -1
		if self.state == 2:
			self.client.process()
			if self.client.status() != 2:
				print 'disconnected'
				self.state = -1
			data = self.client.recv()
			if len(data) > 0:
				sc_confirm = events.sc_confirm()
				if 1:
					cmd = struct.unpack('=H', data[:2])[0]
					sc_confirm.unmarshal(data)
					self.myself = sc_confirm.entity
					self.state = 3
					self.timebase = timenow()
					self.timesvr = sc_confirm.timebase
					self.frame = self.__current() / FRAME_DELAY
					self.frameslap = (self.frame + 1) * FRAME_DELAY
					self.recvmsg = []
					print 'login as P%d tb=%d'%(self.myself + 1, sc_confirm.timebase)
				else:
					print 'login failed'
					self.client.close()
					self.state = -1
		if self.state == 3:
			self.craft = self.crafts[self.myself]
			self.craft.initpos()
			self.craft.mode = 1
			drawing.init()
			drawing.caption('P%d'%(self.myself + 1))
			self.state = 4
			self.pingtime = self.__current() + 5000
		if self.state == 4:
			self.client.process()
			for i in xrange(10): drawing.win.process()
			exitflag = 0
			if drawing.keyon(drawing.VK_ESCAPE): 
				self.client.close()
			if drawing.win.beclosing() or self.client.status() != 2:
				drawing.close()
				self.client.close()
				self.state = -1
			self.current = self.__current()
			current = self.current
			if current >= self.pingtime:
				self.pingtime = current + 1000
				ping = events.cs_ping(current)
				self.client.send(ping.marshal())
			while 1:
				data = self.client.recv()
				if data == '': break
				if len(data) < 2: continue
				cmd = struct.unpack('=H', data[:2])[0]
				if cmd != events.SC_PING:
					self.recvmsg.append(data)
				else:
					ping = events.sc_ping()
					try: 
						ping.unmarshal(data)
						delta = current - ping.current
						drawing.record_ping(delta)
					except: pass
			while current >= self.frameslap:
				self.frame += 1
				self.frameslap += FRAME_DELAY
				self.ontimer()
	def recv(self):
		if len(self.recvmsg) == 0: return ''
		data = self.recvmsg[0]
		self.recvmsg = self.recvmsg[1:]
		return data
	# 客户端主程序
	def ontimer(self):
		current = self.__current()
		frame = self.frame
		d = drawing.keyboard_dir()
		self.craft.d = d
		self.craft.v = 4
		self.craft.craft_move(1)
		# 每1/10秒报告一次状态
		if frame % 5 == 0:
			update = self.update
			update.entity = self.craft.id
			update.frame = frame
			update.x = self.craft.x
			update.y = self.craft.y
			update.d = self.craft.d
			update.v = self.craft.v
			# 按空格则不发送自我更新
			if drawing.keyon(' ') == 0:
				self.client.send(update.marshal())
			# 检测是否需要启用相位滞后
			self.check_phase()
		while 1:
			data = self.recv()
			if data == '': break
			refresh = self.refresh
			refresh.unmarshal(data)
			self.phaselag = refresh.phaselag
			mode = [ 0 for i in xrange(8) ]
			for update in refresh: # 更新战斗机影子
				mode[update.entity] = 1
				craft = self.crafts[update.entity]
				craft.sx = update.x
				craft.sy = update.y
				craft.sd = update.d
				craft.sv = update.v
				debug = update.debug.split(' ')
				stime, sframe = int(debug[0]), int(debug[1])
				if craft.mode < 0: craft.mode = 0
				text = 'ts=%d tc=%d dt=%d fs=%d fc=%d df=%d'%(
					stime, self.current, stime - self.current,
					sframe, self.frame, sframe - self.frame)
				drawing.log(text)
				#print 'update', frame, frame - update.frame, self.current, stime, sframe
				craft.adjust(frame, update.frame)
			for i in xrange(8):  # 删除战斗机
				if mode[i] == 0: self.crafts[i].mode = -1
		drawing.newframe()
		# 更新非主角飞船：让他们的影子按既定方向移动
		for i in xrange(8):
			craft = self.crafts[i]
			if craft.mode < 0: continue
			craft.shadow_move(1)
			craft.draw_shadow()
		# 更新非主角飞船：让他们朝自己的影子飞过去
		for i in xrange(8):
			craft = self.crafts[i]
			if craft.mode < 0: continue
			if craft.mode == 0: 
				craft.trace_mode = self.phaselag # 是否开启相位滞后
				craft.trace(1)
			craft.draw_craft()
		#text = 'TIME: %d f=%d fc=%d'%(current, frame, current/ FRAME_DELAY)
		#drawing.drawtext(drawing.screen, 4, 20, text, 0xffffff)
		drawing.phaselag = self.phaselag
		drawing.flush()
		return 0
	# 检测是否需要相位滞后
	def check_phase(self):
		if self.phasekey == 0 and drawing.keyon(drawing.VK_RETURN):
			self.phasekey = 1
			phase = events.cs_phase(self.phaselag ^ 1)
			self.client.send(phase.marshal())
		elif drawing.keyon(drawing.VK_RETURN) == 0:
			self.phasekey = 0



#----------------------------------------------------------------------
# 服务器逻辑
#----------------------------------------------------------------------
class cserver(object):
	def __init__ (self):
		self.crafts = [ aircraft(i) for i in xrange(8) ]
		self.host = netstream.nethost()
		self.timebase = timenow()
		self.clients = {}
		self.frame = 0
		self.frameslap = 0
		self.update = events.sc_update()
		self.refresh = events.sc_refresh()
		self.update = 0
		self.phaselag = 0
	def __current (self):
		return timenow() - self.timebase
	def startup (self, port = 2000):
		self.host.startup(port)
		self.port = self.host.port
		self.crafts = [ aircraft(i) for i in xrange(8) ]
		self.timebase = timenow()
		self.clients = {}
		self.frame = 0
		self.frameslap = self.__current() + FRAME_DELAY
		self.local = network.gameaddr()
		drawing.log('hosting on %s:%d'%(self.local, self.port))
	def packet_status (self):
		refresh = events.sc_refresh()
		update = events.sc_update()
		for craft in self.crafts:
			if craft.mode < 0: continue
			update.x = craft.sx
			update.y = craft.sy
			update.v = craft.sv
			update.d = craft.sd
			update.frame = self.frame
			update.entity = craft.id
			update.debug = '%d %d'%(self.current, self.frame)
			refresh.append(update)
		refresh.phaselag = self.phaselag
		self.update_packet = refresh.marshal()
		return self.update_packet
	def process (self):
		self.host.process()
		self.current = self.__current()
		current = self.current
		while current >= self.frameslap:
			self.frameslap += FRAME_DELAY
			self.frame += 1
			self.ontimer()
		while 1:
			event, wparam, lparam, data = self.host.read()
			if event < 0: break
			if event == netstream.NET_NEW:
				self.host.settag(wparam, 100)
				pass
			elif event == netstream.NET_LEAVE:
				if lparam < 8:
					self.crafts[lparam].mode = -1
					drawing.log('craft P%d quited'%(lparam + 1))
			elif event == netstream.NET_DATA:
				if len(data) < 2:
					self.host.close(wparam)
				else:
					cmd = struct.unpack('=H', data[:2])[0]
					if cmd == events.CS_LOGIN:
						self.onlogin(wparam, lparam, data)
					elif cmd == events.CS_UPDATE:
						self.onupdate(wparam, lparam, data)
					elif cmd == events.CS_PING:
						ping = events.cs_ping()
						try:
							ping.unmarshal(data)
							p2 = events.sc_ping(ping.current)
							self.host.send(wparam, p2.marshal())
						except: pass
					elif cmd == events.CS_PHASE:
						phase = events.cs_phase()
						phase.unmarshal(data)
						self.phaselag = phase.phaselag
		return 0
	def onlogin (self, wparam, lparam, data):
		login = events.cs_login()
		try: login.unmarshal(data)
		except: 
			self.host.close(wparam)
			return -1
		pos = -1
		for i in xrange(8):
			if self.crafts[i].mode < 0: 
				pos = i
				break
		if pos < 0:
			self.host.close(wparam)
			return -2
		craft = self.crafts[pos]
		craft.mode = 0
		craft.hid = wparam
		craft.initpos()
		self.host.settag(wparam, pos)
		confirm = events.sc_confirm(pos, self.__current())
		self.host.send(wparam, confirm.marshal())
		drawing.log('new craft connected for P%d'%(pos + 1))
		return 0
	def onupdate (self, wparam, lparam, data):
		frame = self.frame
		update = events.cs_update()
		update.unmarshal(data)
		craft = self.crafts[update.entity]
		craft.sx = update.x
		craft.sy = update.y
		craft.sd = update.d
		craft.sv = update.v
		#print 'update', frame, update.frame, frame - update.frame
		craft.adjust(frame - 1, update.frame)
		return 0
	def ontimer (self):
		frame = self.frame
		# 十分之一秒广播全体状态
		if frame % 5 == 0:
			refresh = self.packet_status()
			for i in xrange(8):
				craft = self.crafts[i]
				if craft.mode < 0: continue
				self.host.send(craft.hid, refresh)
		for i in xrange(8):
			craft = self.crafts[i]
			if craft.mode < 0: continue
			craft.shadow_move(1)
		#print 'FPDATE %d %d'%(frame, self.__current() / FRAME_DELAY)
		return 0



#----------------------------------------------------------------------
# game main
#----------------------------------------------------------------------
def game_main(ip = '', port = 2000, phaselag = 0):
	server = cserver()
	client = cclient()
	if ip == '':
		server.startup(port)
		client.startup('127.0.0.1', server.port)
	else:
		client.startup(ip, port)
	while 1:
		time.sleep(0.001)
		if ip == '': server.process()
		client.process()
		if client.state < 0: break
	drawing.close()
	return 0


def startgame(phaselag = 0):
	argv = sys.argv
	if len(sys.argv) <= 2: 
		port = 2000
		if len(sys.argv) == 2: port = int(sys.argv[1])
		game_main('', port, phaselag)
	else:
		ip = sys.argv[1]
		port = int(sys.argv[2])
		game_main(ip, port, phaselag)
	return 0


#----------------------------------------------------------------------
# testing case
#----------------------------------------------------------------------
def __test_network():
	server = cserver()
	client = cclient()
	server.startup()
	client.startup('127.0.0.1', server.port)
	oframe = 0
	while 1:
		time.sleep(0.001)
		server.process()
		client.process()
		if client.state < 0: break
		if server.frame != oframe:
			oframe = server.frame
			'''
			print '%d-%d=%d %d-%d=%d'%(server.current, client.current, 
				server.current - client.current, server.frame, client.frame,
				server.frame - client.frame)
			'''
	drawing.close()
	#client.close()
	#print 'exit'
	return 0

def __test_trace():
	drawing.init()
	craft = aircraft(7)
	craft.x, craft.y, craft.d, craft.v = 400, 300, 0, 1
	craft.sx, craft.sy, craft.sd, craft.sv = 500, 300, 0, 3
	time_delay = 1000 / 50
	time_slap = timenow() + time_delay
	frame = 0
	while drawing.wait() != -1:
		current = timenow()
		if current < time_slap: continue
		time_slap += time_delay
		frame += 1
		# 逻辑贞
		if frame > 0:
			sdir = drawing.keyboard_dir()
			craft.sd = sdir			
		# 显示贞
		craft.shadow_move(1)
		if drawing.keyon(' ') == 0: 
			craft.trace(1)
		drawing.clean()
		drawing.__update_stars()
		craft.draw_shadow()
		craft.draw_craft()
		drawing.update()
	drawing.close()



if __name__ == '__main__':
	#__test_trace()
	#__test_network()
	startgame() 

