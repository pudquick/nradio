# -*- coding: utf-8 -*-
# autor: maciej plonski / mplonski / sokoli.pl
# licence GNU GPL
import sys, id3reader, audioread
from PyQt4 import QtCore, QtGui
from PyQt4.phonon import Phonon
from os.path import isfile
from time import time, sleep
from datetime import datetime

# ui import
from nradio import Ui_nradio

class StartQT4(QtGui.QMainWindow):
	def __init__(self, parent=None):

		self.player = None
		self.time_sleep = 300

		self.j2 = None
		self.isjingle = 1
		self.jingletime = 0
		self.jingle_volume = 100
		self.jinglefile = "../plik.mp3"
		self.jingleTimeLeft = -1
		self.currenttime = 0

		QtGui.QWidget.__init__(self, parent)
		self.ui = Ui_nradio()
		self.ui.setupUi(self)
		self.PlaylistEta = QtCore.QTimer()
		self.timer = QtCore.QTimer()

		QtCore.QObject.connect(self.ui.add_new,QtCore.SIGNAL("clicked()"), self.add_new)
		QtCore.QObject.connect(self.ui.add_m3u,QtCore.SIGNAL("clicked()"), self.add_m3u)
		QtCore.QObject.connect(self.ui.delete_button,QtCore.SIGNAL("clicked()"), self.delete_pos)

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
		self.PlaylistEta.start(1000)

	def save_settings(self):
		self.jingletime = int(self.ui.jingle_time.text())
		self.jingle_volume = int(self.ui.jingle_volume.text())

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

	def add_new(self):
		fd = QtGui.QFileDialog(self)
		self.filename = fd.getOpenFileName()
		if isfile(self.filename):
			self.add_file(self.filename)

	def delete_pos(self):
		root = self.ui.playlist.invisibleRootItem()
		for item in self.ui.playlist.selectedItems():
			    (item.parent() or root).removeChild(item)

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
		self.timer.singleShot(self.time_sleep, self.singletimer)

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

if __name__ == "__main__":
	app = QtGui.QApplication(sys.argv)
	myapp = StartQT4()
	myapp.show()
	sys.exit(app.exec_())
