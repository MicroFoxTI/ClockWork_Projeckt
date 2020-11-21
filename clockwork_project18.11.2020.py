from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QFileDialog, QMessageBox, QInputDialog, QListWidgetItem
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QTimer, QUrl, Qt, QDateTime, QDate, QSize
from PyQt5.QtGui import QIcon, QPixmap
from datetime import datetime
from mutagen.mp3 import MP3
from threading import Timer
from PyQt5 import uic
import sqlite3 as sql
import random
import time
import sys


class Clock_Work(QMainWindow):
    def __init__(self):
        self.week_dict = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday",
                          6: "Saturday", 7: "Sunday"}
        self.timezonesoffsets = {"Moscow": 10800, "London": 0, "Paris": 3600, "Vladivostok": 36000,
                                 "Saint Petersburg": 10800, "Berlin": 3600, "Tokyo": 32400, "Riga": 7200,
                                 "Helsinki": 7200, "Split": 3600}
        self.ime = None

        super().__init__()
        self.tbl = sql.connect("clockworkdb.db")
        self.curs = self.tbl.cursor()

        uic.loadUi("clock_work.ui", self)

        self.timezone = 10800
        time_update = QTimer(self)
        time_update.timeout.connect(self.showTime)
        time_update.start(1000)
        self.showTime()

        self.cw_timezone.currentIndexChanged.connect(self.change_timezone_change)
        self.ss_win = Sound_Settings(self)
        self.ss_win.get_start_time.hide()
        self.ss_win.save_ss.hide()
        self.ss_win.startTime.hide()
        self.clockwork_check = QTimer(self)

        self.sw_win = StopWatches()
        self.conf_win = ListPB(self)
        self.t_win = t_Timer()

        self.play_btn.hide()
        self.sound_settings.clicked.connect(self.ss_win.show)
        self.stopwatch_btn.clicked.connect(self.sw_win.show)
        self.cw_confs.clicked.connect(self.conf_win.show)
        self.t_timer.clicked.connect(self.t_win.show)

        for btn in self.b_cc.buttons():
            btn.setStyleSheet('''QPushButton{background-color: rgb(73, 73, 73)}''')
        self.clockwork_alarm = None

    def showTime(self):
        curr = (QDateTime.currentDateTime().toOffsetFromUtc(self.timezone).toString(Qt.ISODate)).split('T')
        timemass = str(curr[1].split('+')[0]).split(':')
        if QDate.currentDate().toString('yyyy-M-d') != curr[0]:
            self.week_day.setText(self.week_dict[QDate.currentDate().dayOfWeek() + 1])
        else:
            self.week_day.setText(self.week_dict[QDate.currentDate().dayOfWeek()])
        self.c_time.setText(str(f"{timemass[0]}:{timemass[1]}"))
        self.date_month.setText(str(f"{curr[0].split('-')[2]}/{curr[0].split('-')[1]}"))

    def check_clockwork(self):
        to_day_work = [[*i] for i in self.curs.execute("""SELECT name, time FROM clockworkbase
         WHERE weekdays like '%""" + str(datetime.today().isoweekday()) + """%' and onnn = 1""").fetchall()]

        for elem in range(len(to_day_work)):
            a = int(str(to_day_work[elem][1]).split(':')[1]) * 60 + int(
                str(to_day_work[elem][1]).split(':')[0]) * 60 * 60 \
                - (int(round(float(str(datetime.today().time()).split(':')[2]))) +
                   int(str(datetime.today().time()).split(':')[1]) * 60
                   + int(str(datetime.today().time()).split(':')[0]) * 60 * 60)
            if a < 0:
                a = 9999
            to_day_work[elem][1] = a

        self.ime = sorted(to_day_work, key=lambda x: x[1])
        if self.ime:
            self.ime = self.ime[0]
            print(int(self.ime[1]))
            self.clockwork_check.singleShot(int(self.ime[1]) * 1000, self.check_clockwork_1)

    def check_clockwork_1(self):
        print(str(self.ime[0]))
        cw_mass = self.curs.execute("""SELECT name, weekdays, time, song,  sleep, extreme, onnn, volume, start_time
         FROM clockworkbase WHERE name = """ + str(self.ime[0])).fetchone()

        print(cw_mass)
        if self.clockwork_alarm:
            self.clockwork_alarm.close()
        self.clockwork_alarm = Clock_alarm(*cw_mass)
        self.clockwork_alarm.show()
        self.check_clockwork()

    def change_timezone_change(self):
        self.timezone = self.timezonesoffsets[self.cw_timezone.currentText()]
        self.showTime()


class Sound_Settings(QWidget):
    def __init__(self, parent):
        self.parent = parent
        super().__init__()
        uic.loadUi("song_settings_window.ui", self)
        self.song_path_set.clicked.connect(self.song_choice)
        self.volume_slider.valueChanged.connect(self.volume_control)
        self.song_status.clicked.connect(self.sound_check)
        self.volume_percents.setText(str(self.volume_slider.value()) + '%')
        self.modded = False
        for btn in self.b_cc.buttons():
            btn.setStyleSheet('''QPushButton{background-color: rgb(75, 75, 75)}''')
        self.save_ss.clicked.connect(self.save_ss_to_global)
        self.get_start_time.clicked.connect(self.get_st)
        self.st_time = 0

    def song_choice(self):
        try:
            self.fname = QFileDialog.getOpenFileName(self, "песню выбрал, быстра", '', 'Песни (*.mp3)')[0]
            self.all_music_time = round(MP3(self.fname).info.length * 1000)
            self.str_lenght = (str(int(str(round(round(MP3(self.fname).info.length, 2) / 60, 2)).split('.')[1]) * 60)[
                               :2] + '.' + str(
                int(str(round(round(MP3(self.fname).info.length, 2) / 60, 2)).split('.')[1]) * 60)[2:])
            if self.str_lenght.split('.')[1] >= '50':
                self.str_lenght = str(int(self.str_lenght.split('.')[0]) + 1)
            else:
                self.str_lenght = str(int(self.str_lenght.split('.')[0]))
            self.str_min_lenght = str(round(round(MP3(self.fname).info.length, 2) / 60, 2)).split('.')[0]
            self.all_audio_time.setText(self.str_min_lenght + ':' + self.str_lenght)
            self.song_name.setText((self.fname.split('/')[-1]).split('.')[0])
            self.player = QMediaPlayer()
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(self.fname)))
            self.player.play()
            self.player.pause()
            self.volume_slider.setValue(10)
            self.player.setVolume(self.volume_slider.value())
            self.paused = True
            self.song_timing.valueChanged.connect(self.time_travel)
            song_time_updater = QTimer(self)
            song_time_updater.timeout.connect(self.normal_going)
            song_time_updater.start(1000)
            self.save_ss.clicked.connect(self.save)
        except:
            print('ошибка выбора файла')

    def sound_check(self):
        try:
            if self.paused:
                self.player.play()
                self.song_status.setText('Now playing')
                self.paused = False
            else:
                self.player.pause()
                self.song_status.setText('Paused')
                self.paused = True
        except:
            print('плеер пуст')

    def volume_control(self):
        try:
            self.player.setVolume(self.volume_slider.value())
            self.volume_percents.setText(str(self.volume_slider.value()) + '%')
        except:
            print('плеер пуст')

    def normal_going(self):
        self.song_timing.blockSignals(True)
        self.curr_music_time = self.player.position()
        self.song_timing.setValue(round(self.curr_music_time / self.all_music_time * 100))
        if int(
                round(self.curr_music_time / 1000) - 60 * int(
                    str(str((self.curr_music_time / 1000) / 60)).split('.')[0])) < 10:
            self.cur_audio_time.setText(str(str((self.curr_music_time / 1000) / 60)).split('.')[0] + ":0" + str(
                round(self.curr_music_time / 1000) - 60 * int(
                    str(str((self.curr_music_time / 1000) / 60)).split('.')[0])))
        else:
            self.cur_audio_time.setText(str(str((self.curr_music_time / 1000) / 60)).split('.')[0] + ":" + str(
                round(self.curr_music_time / 1000) - 60 * int(
                    str(str((self.curr_music_time / 1000) / 60)).split('.')[0])))
        self.song_timing.blockSignals(False)

    def time_travel(self, value):
        self.player.setPosition(round(self.all_music_time * (value / 100)))
        self.curr_music_time = self.player.position()
        self.curr_reserv = self.player.position()
        self.song_timing.setValue(value)
        if int(
                round(self.curr_music_time / 1000) - 60 * int(
                    str(str((self.curr_music_time / 1000) / 60)).split('.')[0])) < 10:
            self.cur_audio_time.setText(str(str((self.curr_music_time / 1000) / 60)).split('.')[0] + ":0" + str(
                round(self.curr_music_time / 1000) - 60 * int(
                    str(str((self.curr_music_time / 1000) / 60)).split('.')[0])))
        else:
            self.cur_audio_time.setText(str(str((self.curr_music_time / 1000) / 60)).split('.')[0] + ":" + str(
                round(self.curr_music_time / 1000) - 60 * int(
                    str(str((self.curr_music_time / 1000) / 60)).split('.')[0])))

    def save_ss_to_global(self):
        self.parent.song = self.fname
        self.parent.cw_song_name.setText('.'.join(self.parent.song.split('/')[-1].split('.')[:-1]))
        self.parent.volume = self.volume_slider.value()
        if self.startTime.isChecked():
            self.parent.start_time = self.st_time // 1000

    def get_st(self):
        try:
            self.st_time = self.player.position()
            seconds = (self.st_time / 1000)
            minutes = (self.st_time / 1000) // 60
            self.get_start_time.setText(f"{str(minutes).split('.')[0]}:{str(seconds - (60 * minutes)).split('.')[0]}")
        except:
            print('песня ещё не выбрана')
            self.st_time = 0

    def closeEvent(self, event):
        close = QMessageBox.question(self,
                                     "QUIT",
                                     "Are you sure want to exit?",
                                     QMessageBox.Yes | QMessageBox.No)
        if close == QMessageBox.Yes:
            event.accept()
            try:
                if not self.paused:
                    self.sound_check()
                else:
                    self.player.pause()
                    self.song_status.setText('Paused')
            except:
                print('плеер не играет')
        else:
            event.ignore()


class StopWatches(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("stopwatch.ui", self)
        self.sw_start.clicked.connect(self.start_time)
        self.sw_clear.clicked.connect(self.clear_sw_marklist)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.time_upd)
        self.all_marks_list = []
        self.started = False
        self.paused = False
        self.sw_marklist_count = 0
        self.sw_makepoint.clicked.connect(self.make_sw_point)
        self.sw_totxt.clicked.connect(self.write_to_txt)

        for btn in self.b_cc.buttons():
            btn.setStyleSheet('''QPushButton{background-color: rgb(75, 75, 75)}''')

    def start_time(self):
        if not self.started:
            if not self.paused:
                self.start_time = time.time()
            else:
                self.start_time = self.start_time + (time.time() - self.pause_time)
                self.paused = False
            self.timer.start(1)
            self.sw_start.setText('Stop')
            self.started = True
        else:
            self.timer.stop()
            self.sw_start.setText('Start')
            self.started = False
            self.paused = True
            self.pause_time = time.time()
            a = (str(int(str(time.time() - self.start_time).split('.')[0]) // 60))
            b = int(str(time.time() - self.start_time).split('.')[0]) - 60 * (
                    int(str(int(str(time.time() - self.start_time).split('.')[0]))) // 60)
            self.to_list_paused = str(
                f"{a}-{b}-{(str(time.time() - self.start_time).split('.')[1][:3])}")

    def time_upd(self):
        if int(str(int(str(time.time() - self.start_time).split('.')[0]) // 60)) < 10:
            self.sw_minutes.setText(
                f"0{(str(int(str(time.time() - self.start_time).split('.')[0]) // 60))}")
        else:
            self.sw_minutes.setText(
                f"{(str(int(str(time.time() - self.start_time).split('.')[0]) // 60))}")
        if int(int(str(time.time() - self.start_time).split('.')[0]) - 60 * (
                int(str(int(str(time.time() - self.start_time).split('.')[0]))) // 60)) < 10:
            self.sw_seconds.setText(
                f"0{int(str(time.time() - self.start_time).split('.')[0]) - 60 * (int(str(int(str(time.time() - self.start_time).split('.')[0]))) // 60)}")
        else:
            self.sw_seconds.setText(
                f"{int(str(time.time() - self.start_time).split('.')[0]) - 60 * (int(str(int(str(time.time() - self.start_time).split('.')[0]))) // 60)}")
        self.sw_time_ms.setText(f"{(str(time.time() - self.start_time).split('.')[1][:3])}")

    def make_sw_point(self):
        try:
            if int(self.sw_minutes.text()) or int(self.sw_seconds.text()) or int(self.sw_time_ms.text()):
                self.sw_marklist_count += 1
                if not self.paused:
                    a = (str(int(str(time.time() - self.start_time).split('.')[0]) // 60))
                    print('робитен')
                    b = int(str(time.time() - self.start_time).split('.')[0]) - 60 * (
                            int(str(int(str(time.time() - self.start_time).split('.')[0]))) // 60)
                    self.to_list = str(
                        f"{self.sw_marklist_count}: {a}-{b}-{(str(time.time() - self.start_time).split('.')[1][:3])}")
                else:
                    self.to_list = str(f"{self.sw_marklist_count}: {self.to_list_paused}")
                self.all_marks_list.append(self.to_list)
                self.sw_marklist.addItem(self.to_list)
            else:
                print('секундомер не запущен')
        except:
            print("ошибка создания круга.")

    def clear_sw_marklist(self):
        self.sw_minutes.setText('00')
        self.sw_seconds.setText('00')
        self.sw_time_ms.setText('000')
        self.timer.stop()
        self.sw_start.setText('Start')
        self.started = False
        self.all_marks_list = []
        self.sw_marklist.clear()
        self.sw_marklist_count = 0
        self.paused = False
        self.pause_time = 0
        self.start_time = 0
        self.to_list_paused = 0
        self.to_list = ''

    def write_to_txt(self):
        text, ok = QInputDialog.getText(self, 'File name is?',
                                        'Enter the File name(without .txt):')
        if ok:
            with open(f"{text}.txt", mode="w") as text_to_write:
                for i in self.all_marks_list:
                    text_to_write.write(i + '\n')

    def closeEvent(self, event):
        self.clear_sw_marklist()


class ListPB(QWidget):
    def __init__(self, parent):
        super().__init__()
        uic.loadUi("btn_list.ui", self)
        self.parent = parent
        self.new_elements()
        self.list_of_btns.itemDoubleClicked.connect(self.editclockwork)
        self.create_new.clicked.connect(self.createwidget)
        self.cw_win = RealClockWork(self)
        self.cw_edit = False

    def new_elements(self):
        self.list_of_btns.clear()
        self.conn = sql.connect('clockworkdb.db')
        self.c = self.conn.cursor()
        cw_mass = self.c.execute("""SELECT * FROM clockworkbase""").fetchall()
        days = ''
        for i in cw_mass:
            id = i[0]
            if int(i[2].split(':')[0]) < 10:
                cw_time_hour = '0' + i[2].split(':')[0]
            else:
                cw_time_hour = i[2].split(':')[0]
            if int(i[2].split(':')[1]) < 10:
                cw_time_minute = '0' + i[2].split(':')[1]
            else:
                cw_time_minute = i[2].split(':')[1]
            for symbl in ''.join(sorted([smbl for smbl in str(i[1])])):
                week_dict = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri",
                             6: "Sat", 7: "Sun"}
                days += (week_dict[int(symbl)] + '; ')

            itm = QListWidgetItem(f"{id} | {cw_time_hour}:{cw_time_minute} | {days}")
            if not i[-1]:
                itm.setIcon(QIcon(r"pusto.png"))
            else:
                itm.setIcon(QIcon(i[-1]))
            self.list_of_btns.setIconSize(QSize(30, 30))
            self.list_of_btns.addItem(itm)  # .setIcon('alliteamsicon.jpg')
            days = ''
        self.parent.check_clockwork()

    def createwidget(self):
        cw_mass = sorted(self.c.execute("""SELECT name FROM clockworkbase""").fetchall())[-1][0]
        self.c.execute("""INSERT INTO clockworkbase
                    (name, weekdays, time, song,  sleep, extreme, onnn, volume, start_time, icon_path)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) """, (cw_mass + 1, '', '0:0',
                                                                    'S3RL - HentaiExtreme Bass Boosted.mp3', 0,
                                                                    0, 0, 10, 0, 'pusto.png'))
        self.conn.commit()
        self.new_elements()

    def editclockwork(self, value):
        self.cw_edit = True
        cw_mass = self.c.execute("""SELECT * FROM clockworkbase
            WHERE name = """ + value.text().split('|')[0].strip()).fetchone()
        self.cw_win.update_parameters(cw_mass)
        self.cw_win.show()

    def closeEvent(self, event):
        self.cw_edit = False
        self.close()
        self.cw_win.close()


class RealClockWork(QWidget):
    def __init__(self, parent):
        self.parent = parent
        super().__init__()
        uic.loadUi("realclockwork.ui", self)
        self.day_mass = []
        self.week_dict = {"Mon": 1, "Tue": 2, "Wed": 3, "Thu": 4, "Fri": 5,
                          "Sat": 6, "Sun": 7}
        self.week_dict_reversed = {1: self.cw_mon, 2: self.cw_tue, 3: self.cw_wed, 4: self.cw_thu,
                                   5: self.cw_fri, 6: self.cw_sat, 7: self.cw_sun}
        self.start_time = 0
        self.onnn = 0
        self.cwdb = sql.connect('clockworkdb.db')
        self.icon_path = 'pusto.png'
        self.curs = self.cwdb.cursor()
        self.volume = 100
        self.extreme = 0
        self.sleep = 0
        self.song = 'S3RL - HentaiExtreme Bass Boosted.mp3'
        self.name = 0

        self.cw_icon.setPixmap(QPixmap("pusto.png").scaled(30, 30))
        self.cw_icon.resize(30, 30)
        for btn in self.cw_weekgroup.buttons():
            btn.clicked.connect(self.change_state)
        for btn in self.cw_change_color.buttons():
            btn.setStyleSheet('''QPushButton{background-color: rgb(73, 73, 73)}''')

        self.cw_chooseIcon.clicked.connect(self.choose_icon)
        self.cw_hour.currentIndexChanged.connect(self.timeset)
        self.cw_minute.currentIndexChanged.connect(self.timeset)
        self.cw_sonsel.clicked.connect(self.cw_song_shoose_show)
        self.cw_delete.clicked.connect(self.delete_clockwork)
        self.cw_save.clicked.connect(self.test_clockwork)

    def set_time(self, hours, minutes):
        if len(hours) == 1:
            hours = '0' + hours
        if len(minutes) == 1:
            minutes = '0' + minutes

        self.cw_time_hour_0.setText(hours[0])
        self.cw_time_hour_1.setText(hours[-1])
        self.cw_time_minute_0.setText(minutes[0])
        self.cw_time_minute_1.setText(minutes[-1])

    def choose_icon(self):
        self.icon_path = QFileDialog.getOpenFileName(self, "картинку выбрал, быстра", '', 'Картинки (*.jpg *.png)')[0]
        try:
            self.cw_icon.setPixmap(QPixmap(self.icon_path).scaled(30, 30))
            self.cw_icon.resize(30, 30)
        except:
            print('непредвиденная ошибка')

    def update_parameters(self, date_time_2):
        self.name, weekdays, time, self.song, self.sleep, self.extreme, \
        self.onnn, self.volume, self.start_time, self.icon_path = date_time_2
        self.set_time(*time.split(':'))

        self.day_mass = []
        for i in self.week_dict_reversed:
            self.week_dict_reversed[i].setStyleSheet(
                '''QPushButton{background-color: rgb(75, 75, 75, 80)}''')
        for i in list(str(weekdays)):
            self.day_mass.append(self.week_dict_reversed[int(i)])
            self.week_dict_reversed[int(i)].setStyleSheet(
                '''QPushButton{background-color: rgb(255, 121, 215, 30)}''')

        self.cw_icon.setPixmap(QPixmap(self.icon_path).scaled(30, 30))
        self.cw_icon.resize(30, 30)
        self.cw_song_name.setText('.'.join(self.song.split('/')[-1].split('.')[:-1]))
        self.cw_sleep.setChecked(self.sleep)
        self.cw_exmode.setChecked(self.extreme)
        self.cw_onnn.setChecked(self.onnn)
        self.cw_testalarm.clicked.connect(self.test_alarm)

    def change_state(self):
        day_info = self.sender()
        if day_info not in self.day_mass:
            self.day_mass.append(day_info)
            self.sender().setStyleSheet('''QPushButton{background-color: rgb(255, 121, 215, 30)}''')
        else:
            self.day_mass.remove(day_info)
            self.sender().setStyleSheet('''QPushButton{background-color: rgb(75, 75, 75, 80)}''')

    def timeset(self):
        self.set_time(str(int(self.cw_hour.currentIndex())),
                      str(int(self.cw_minute.currentIndex())))

    def cw_song_shoose_show(self):
        self.cw_song_shoose = Sound_Settings(self)
        self.cw_song_shoose.show()

    def test_clockwork(self):
        weekdays = ''
        for i in self.day_mass:
            weekdays += str(self.week_dict[i.text()])
        time = str(int(self.cw_time_hour_0.text() + self.cw_time_hour_1.text())) + ':' \
               + str(int(self.cw_time_minute_0.text() + self.cw_time_minute_1.text()))
        self.curs.execute("""DELETE FROM clockworkbase
            WHERE name = """ + str(self.name))
        self.cwdb.commit()
        self.curs.execute("""INSERT INTO clockworkbase
         (name, weekdays, time, song,  sleep, extreme, onnn, volume, start_time, icon_path)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) """,
                          (self.name, weekdays, time, self.song, self.cw_sleep.isChecked(), self.cw_exmode.isChecked(),
                           self.cw_onnn.isChecked(), self.volume, self.start_time, self.icon_path))
        self.cwdb.commit()
        self.parent.new_elements()

    def test_alarm(self):
        weekdays = ''
        for i in self.day_mass:
            weekdays += str(self.week_dict[i.text()])
        time = self.cw_time_hour_0.text() + self.cw_time_hour_1.text() + ':' \
               + self.cw_time_minute_0.text() + self.cw_time_minute_1.text()
        self.alarm = Clock_alarm(self.name, weekdays, time, self.song, self.cw_sleep.isChecked(),
                                 self.cw_exmode.isChecked(),
                                 self.cw_onnn.isChecked(), self.volume, self.start_time)
        self.alarm.show()

    def delete_clockwork(self):
        print(self.curs.execute("""SELECT * FROM clockworkbase""").fetchall())
        if len(self.curs.execute("""SELECT * FROM clockworkbase""").fetchall()) > 1:
            close = QMessageBox.question(self,
                                         "Deleting clockwork",
                                         "Are you sure you want to delete this cw?",
                                         QMessageBox.Yes | QMessageBox.No)
            if close == QMessageBox.Yes:
                self.curs.execute("""DELETE FROM clockworkbase
                                    WHERE name = """ + str(self.name))
                self.cwdb.commit()
                self.parent.new_elements()
                self.close()
            else:
                pass
        else:
            print(1)
            close = QMessageBox.question(self,
                                         "ERR (fox)",
                                         "This clockwork is the last of its kind.\n"
                                         "U cant kill it.\n"
                                         "Please, edit it, if u need.",
                                         QMessageBox.Ok)
            if close == QMessageBox.Yes:
                self.close()
            else:
                self.close()


class Clock_alarm(QWidget):
    def __init__(self, name, weekdays, time, song, sleep, extreme, onnn, volume, start_time):
        super().__init__()
        uic.loadUi("clock_alarm.ui", self)
        hours, minutes = time.split(':')
        if len(hours) == 1:
            hours = '0' + hours
        if len(minutes) == 1:
            minutes = '0' + minutes
        self.ca_cw_alarm.setText(hours + ':' + minutes)

        self.DeActivate.clicked.connect(self.alarm_deactivate)

        self.setWindowFlags(Qt.FramelessWindowHint)

        self.player = QMediaPlayer()
        if not extreme:
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(song)))
        else:
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile("S3RL - HentaiExtreme Bass Boosted.mp3")))
        self.player.setVolume(volume)
        if start_time:
            self.player.setPosition(start_time * 1000)
        self.player.play()

        self.extreme = extreme
        self.sleep = sleep

    def alarm_deactivate(self):
        if not self.extreme:
            if not self.sleep:
                self.player.stop()
                self.hide()
            else:
                self.slch_win = SleepCheck(self)
                self.slch_win.show()
        else:
            self.player.setVolume(100)


class SleepCheck(QWidget):
    def __init__(self, parent):
        self.parent = parent
        super().__init__()
        uic.loadUi("sleepcheck.ui", self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        for buttns in self.sc_ans_var.buttons():
            buttns.clicked.connect(self.try_to_deactivate)
            buttns.setStyleSheet('''QPushButton{background-color: rgb(75, 75, 75, 80)}''')
        self.update_value()

    def update_value(self):
        self.a = random.randint(-50, 50)
        self.b = random.randint(-50, 50)
        self.c = random.randint(-50, 50)
        self.close_event = False
        self.first_task = random.choice(['*', '-', '+'])
        self.second_task = random.choice(['*', '-', '+'])
        if self.a < 0:
            self.a = str(f"({self.a})")
        if self.b < 0:
            self.b = str(f"({self.b})")
        if self.c < 0:
            self.c = str(f"({self.c})")
        self.all_task = str(f'{self.a} {self.first_task} ( {self.b} {self.second_task} {self.c} )')
        self.sc_tosolve.setText(self.all_task)
        setted = False
        btn = list(self.sc_ans_var.buttons())
        for _ in range(4):
            randomed_btn = random.choice(btn)
            if not setted:
                randomed_btn.setText(str(eval(self.all_task)))
                setted = True
            else:
                randomed_btn.setText(
                    str(eval(str(f"{eval(self.all_task)} {random.choice(['-', '+'])} {random.randint(-7, 7)}"))))
            del btn[btn.index(randomed_btn)]

    def try_to_deactivate(self):
        if self.sender().text() == str(eval(self.all_task)):
            QMessageBox.question(self, "Quitting", "Ur good.", QMessageBox.Yes)
            self.close()
            self.parent.close()
            self.parent.player.stop()
        else:
            self.update_value()


class t_Timer(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("timer.ui", self)
        self.t_stimer.clicked.connect(self.try_to_start)
        self.a = 0
        self.is_work = False
        self.timer_for_timer = None
        self.t_stimer.setStyleSheet('''QPushButton{background-color: rgb(75, 75, 75, 80)}''')
        self.t_clear.clicked.connect(self.clear_timer_positions)
        self.assist = QMediaPlayer()

    def try_to_start(self):
        try:
            if not self.is_work:
                print(self.t_hours.text(), self.t_minutes.text(), self.t_seconds.text())
                if self.t_hours.text() == '00' and self.t_minutes.text() == '00' and self.t_seconds.text() == '00':
                    print('try')
                    hours = int(self.t_hou.text()) * 60 * 60
                    minutes = int(self.t_min.text()) * 60
                    secs = int(self.t_sex.text())
                    self.a = hours + minutes + secs
                    self.t_stimer.setText('Start')
                if self.a > 0:
                    self.assist.setMedia(QMediaContent(QUrl.fromLocalFile("Start_timer1.mp3")))
                    self.assist.setVolume(100)
                    self.assist.play()
                    self.timer_for_timer = Timer(1, self.upd_timer)
                    self.timer_for_timer.start()
                    self.is_work = True
                    self.t_stimer.setText('On Going')
                hours = self.a // 60 // 60
                minutes = (self.a - (hours * 60 * 60)) // 60
                secs = self.a - (hours * 60 * 60) - (minutes * 60)
                if hours < 10:
                    hours = str(f'0{hours}')
                if minutes < 10:
                    minutes = str(f'0{minutes}')
                if secs < 10:
                    secs = str(f'0{secs}')
                self.t_hours.setText(str(hours))
                self.t_minutes.setText(str(minutes))
                self.t_seconds.setText(str(secs))
            else:
                self.t_stimer.setText('Paused')
                self.assist.setMedia(QMediaContent(QUrl.fromLocalFile("Pause_time1.mp3")))
                self.assist.setVolume(100)
                self.assist.play()
                self.is_work = False
        except:
            print('ошЫбка при получении времени')

    def upd_timer(self):
        try:
            if self.is_work:
                self.a -= 1
                if self.a < 0:
                    self.t_stimer.setText('Start')
                    self.is_work = False
                else:
                    hours = self.a // 60 // 60
                    minutes = (self.a - (hours * 60 * 60)) // 60
                    secs = self.a - (hours * 60 * 60) - (minutes * 60)
                    if hours < 10:
                        hours = str(f'0{hours}')
                    if minutes < 10:
                        minutes = str(f'0{minutes}')
                    if secs < 10:
                        secs = str(f'0{secs}')
                    self.t_hours.setText(str(hours))
                    self.t_minutes.setText(str(minutes))
                    self.t_seconds.setText(str(secs))
                    self.timer_for_timer = Timer(1, self.upd_timer)
                    self.timer_for_timer.start()
                    if self.a == 0:
                        self.assist.setMedia(QMediaContent(QUrl.fromLocalFile("End_timer1.mp3")))
                        self.assist.setVolume(100)
                        self.assist.play()
        except:
            print('неизвестная ошибка')

    def clear_timer_positions(self):
        self.is_work = False
        self.t_hours.setText('00')
        self.t_minutes.setText('00')
        self.t_seconds.setText('00')
        self.t_hou.setText('00')
        self.t_min.setText('00')
        self.t_sex.setText('00')

    def closeEvent(self, event):
        self.clear_timer_positions()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = Clock_Work()
    ex.show()
    sys.exit(app.exec())
