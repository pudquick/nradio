# -*- coding: utf-8 -*-
# autor: maciej plonski / mplonski / sokoli.pl
# licence GNU GPL
import sys, id3reader, audioread
from PyQt4 import QtCore, QtGui
from PyQt4.phonon import Phonon
from os.path import isfile
from time import time, sleep
from datetime import datetime
from re import sub

# ui import
from nradio import Ui_nradio

class StartQT4(QtGui.QMainWindow):
	def __init__(self, parent=None):

		self.player = None
		self.timer_sleep = 100
		self.timer_count = 0

		self.j2 = None
		self.isjingle = 1
		self.jingletime = None
		self.jingle_volume = None
		self.jingle_volume_abs = None
		self.jinglefile = None
		self.jingleTimeLeft = -1
		self.currenttime = 0

		self.settings_file = './nradio.conf'
	
		QtGui.QWidget.__init__(self, parent)
		self.ui = Ui_nradio()
		self.ui.setupUi(self)

		self.PlaylistEta = QtCore.QTimer()
		self.timer = QtCore.QTimer()

		QtCore.QObject.connect(self.ui.add_new,QtCore.SIGNAL("clicked()"), self.add_new)
		QtCore.QObject.connect(self.ui.add_m3u,QtCore.SIGNAL("clicked()"), self.add_m3u)
		QtCore.QObject.connect(self.ui.delete_button,QtCore.SIGNAL("clicked()"), self.delete_pos)
		QtCore.QObject.connect(self.ui.set_jingle,QtCore.SIGNAL("clicked()"), self.set_jingle)
		QtCore.QObject.connect(self.ui.save_to_file_button,QtCore.SIGNAL("clicked()"), self.save_file_settings)

		QtCore.QObject.connect(self.ui.play_button, QtCore.SIGNAL("clicked()"), self.play_button)
		QtCore.QObject.connect(self.ui.pause_button, QtCore.SIGNAL("clicked()"), self.pause_button)
		QtCore.QObject.connect(self.ui.stop_button, QtCore.SIGNAL("clicked()"), self.stop_button)

		QtCore.QObject.connect(self.ui.save_settings, QtCore.SIGNAL("clicked()"), self.save_settings)
		QtCore.QObject.connect(self.ui.jingle_start, QtCore.SIGNAL("clicked()"), self.jingle_start)

		QtCore.QObject.connect(self.ui.volume_locked, QtCore.SIGNAL("stateChanged(int)"), self.volume_locked)
		QtCore.QObject.connect(self.ui.seek_locked, QtCore.SIGNAL("stateChanged(int)"), self.seek_locked)

		self.player = Phonon.MediaObject(self)
		self.jingle = Phonon.MediaObject(self)

		QtCore.QObject.connect(self.PlaylistEta, QtCore.SIGNAL("timeout()"), self.UpdatePlaylistEta)
		QtCore.QObject.connect(self.jingle, QtCore.SIGNAL("finished()"), self.jingleEnd)

		self.load_file_settings()

		self.PlaylistEta.start(1000)

	def save_file_settings(self):
		self.save_settings()
		plik = open(self.settings_file, 'w')
		plik.write("jingle_time=" + str(self.jingletime))
		plik.write("\njingle_file=" + str(self.jinglefile))
		if self.jingle_volume > 0:
			plik.write("\njingle_volume=" + str(self.jingle_volume))
		else:
			plik.write("\njingle_volume_abs=" + str(self.jingle_volume_abs))
		plik.close()

	def load_file_settings(self):
		try:
			plik = open(self.settings_file)
		except:
			self.jingletime = 0
			self.jingle_volume = 100
			self.jinglefile = "../plik.mp3"
			self.save_file_settings()
		else:
			data = plik.readline()
			while (data != ''):
				datas = sub('\n$', '', data).split("=")
				if datas[0] == 'jingle_time':
					try:
						self.jingletime = int(datas[1])
					except:
						self.jingletime = 0
				elif datas[0] == 'jingle_volume':
					try:
						self.jingle_volume = int(datas[1])
					except:
						self.jingle_volume = 100
				elif datas[0] == 'jingle_volume_abs':
					try:
						self.jingle_volume = int(datas[1])
					except:
						self.jingle_volume = 1
				elif datas[0] == 'jingle_file':
					if isfile(datas[1]):
						self.jinglefile = datas[1]
				data = plik.readline()
			plik.close()

			if self.jinglefile == None:
				self.jinglefile = ""
			if self.jingletime == None:
				self.jingletime = 0

			self.ui.jingle_time.setText(str(self.jingletime))

			if self.jingle_volume != None:
				if self.jingle_volume > 0:
					self.ui.jingle_volume.setText(str(self.jingle_volume))
				else:
					self.jingle_volume = None
			if self.jingle_volume_abs != None:
				if self.jingle_volume_abs > 0:
					self.ui.jingle_volume_abs.setText(str(self.jingle_volume_abs))
				else:
					self.jingle_volume_abs = None
			if (self.jingle_volume_abs == None) and (self.jingle_volume == None):
				self.ui.jingle_volume.setText('100')
				self.jingle_volume = 100
			# TODO what if it's not media file?
			self.ui.jingle_file.setText(self.jinglefile)

				
	# TODO rest, autosave :-)			
	def save_settings(self):
		self.jingletime = int(self.ui.jingle_time.text())
		self.jingle_volume = int(self.ui.jingle_volume.text())

	# TODO what if it's not media file?
	def set_jingle(self):
		fd = QtGui.QFileDialog(self)
		self.filename = fd.getOpenFileName()
		if isfile(self.filename):
			self.jinglefile = self.filename
			self.ui.jingle_file.setText(self.filename)

	def add_file(self, fil):
		a = QtGui.QTreeWidgetItem(self.ui.playlist)
		a.setFlags(a.flags() & ~QtCore.Qt.ItemIsDropEnabled)
		id3r = id3reader.Reader(str(fil))
		if (id3r.getValue('performer') != None):
			a.setText(0, id3r.getValue('performer'))
		else:
			a.setText(0, '---')
		if (id3r.getValue('title') != None):
			a.setText(1, id3r.getValue('title'))
		else:
			a.setText(1, '---')
		time = int(audioread.audio_open(str(fil)).duration)
		a.setText(2, "%i:%i (%is)" % (time/60, time % 60, time))
		a.setText(3, '---')
		a.setText(4, fil)

	def add_m3u(self):
		fd = QtGui.QFileDialog(self)
		self.filename = fd.getOpenFileName()
		if isfile(self.filename):
			plik = open(self.filename)
			files = plik.readlines()
			close(plik)
			for l in files:
				if isfile(l):
					self.add_file(l)

	# TODO autoplay
	def add_new(self):
		fd = QtGui.QFileDialog(self)
		self.filename = fd.getOpenFileName()
		if isfile(self.filename):
			self.add_file(self.filename)

	def delete_pos(self):
		root = self.ui.playlist.invisibleRootItem()
		for item in self.ui.playlist.selectedItems():
			    (item.parent() or root).removeChild(item)

	# TODO first song should have minus time
	def UpdatePlaylistEta(self):
		eta = 0
		for i in xrange(self.ui.playlist.topLevelItemCount()):
			stime = int(self.ui.playlist.topLevelItem(i).text(2).split('(')[1].split('s')[0])
			self.ui.playlist.topLevelItem(i).setText(3, datetime.fromtimestamp(int(time()) + eta).strftime("%H:%M:%S"))
			eta += stime
		if not self.player == None:
			time2 = self.player.currentTime()
			time3 = self.player.remainingTime()
			self.ui.lcd1.setText(str(time2/60000) + ":" + str((time2/1000)%60) + " -" + str(time3/60000) + ":" + str((time3/1000)%60))

	# WARNING!
	# Phonon has to wait some time for audioOutput to get working, so we need some time (e.g. 500ms before changing volume)
	def change_volume(self, to):
		self.setvolume = to
		audioOutput.setVolume(to)
		self.timer.singleShot(self.timer_sleep, self.singletimer)

	def play_button(self):
		global audioOutput
		self.player.setCurrentSource(Phonon.MediaSource('/media/DYSK/muzyka/Cisza jak ta/Cisza Jak Ta - Bo tak Cie kocham....mp3'))
		audioOutput = Phonon.AudioOutput(Phonon.MusicCategory, self)
		audioOutput.setName('nradio')
		self.ui.player_volume.setAudioOutput(audioOutput)
		self.ui.player_seek.setMediaObject(self.player)
		Phonon.createPath(self.player, audioOutput)
		self.player.play()
		self.change_volume(0.2) #debug only	
	
	def pause_button(self):
		self.player.pause()

	def stop_button(self):
		self.player.stop()
		
	def jingle_start(self):
		audioOutput.setName('nradio')
		Phonon.createPath(self.jingle, audioOutput)
		self.jingle.setCurrentSource(Phonon.MediaSource(self.jinglefile))

		self.player.pause()
		self.jingle.play()
		self.change_volume(audioOutput.volume()*self.jingle_volume/100.0)

		self.ui.jingle_volume.readOnly = True
		self.ui.volume_locked.setChecked(False)
		self.ui.seek_locked.setChecked(False)

	def jingleEnd(self):
		self.ui.jingle_volume.readOnly = False
		self.ui.volume_locked.setChecked(True)
		self.ui.seek_locked.setChecked(True)
			
		self.player.play()
		self.change_volume(audioOutput.volume()/(self.jingle_volume/100.0))

	def volume_locked(self, i):
		if(i == 0):
			self.ui.player_volume.setEnabled(False)
		else:
			self.ui.player_volume.setEnabled(True)

	def seek_locked(self, i):
		if(i == 0):
			self.ui.player_seek.setEnabled(False)
		else:
			self.ui.player_seek.setEnabled(True)

	def singletimer(self):
			audioOutput.setVolume(self.setvolume)
			if(self.timer_count < 10):
				self.timer_count += 1
				self.timer.singleShot(self.timer_sleep, self.singletimer)
			else:
				self.time_count = 0

if __name__ == "__main__":
	app = QtGui.QApplication(sys.argv)
	myapp = StartQT4()
	myapp.show()
	sys.exit(app.exec_())
