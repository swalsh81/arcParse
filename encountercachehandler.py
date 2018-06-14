from PyQt5.QtCore import pyqtSignal, QObject

import os, sqlite3

import worker

import sched, time

from encounter import Encounter

DIR_RESOURCE = "./resources"

DB_URL = "cache.db"

class EncounterCacheHandler(QObject):

    init = False

    timerTick = 10
    lastAccessed = 0

    timerTicked = pyqtSignal()

    def __init__(self):
        super(EncounterCacheHandler, self).__init__()
        self.timer = sched.scheduler(time.time, time.sleep)
        path = os.path.abspath(self.getResourceDir() + "/" + DB_URL)
        self.connection = sqlite3.connect(path)
        self.initDB(self.connection)
        self.timerTicked.connect(self.checkTimer)

    def getConnection(self):
        self.lastAccessed = time.time()
        if self.connection is None or self.init is False:
            print("connecting")
            path = os.path.abspath(self.getResourceDir() + "/" + DB_URL)
            self.connection = sqlite3.connect(path)
            self.initDB(self.connection)
            self.startConnectionTimeout()
        return self.connection

    def startConnectionTimeout(self):
        self.timer.enter(self.timerTick, 1, self.doTick)
        print("start")
        job = worker.Job(self.timer.run)
        worker.ThreadPool.start(job)

    def doTick(self):
        self.timerTicked.emit()

    def checkTimer(self):
        print("check")
        if self.lastAccessed + self.timerTick*2 < time.time():
            self.connection.close()
            self.connection = None
            print("connection closed")
        else:
            print("reset")
            self.startConnectionTimeout()

    def initDB(self, conn):

        c = conn.cursor()

        c.execute("""CREATE TABLE IF NOT EXISTS encounters(
                            timestamp INT,
                            loglength INT,
                            fileName TEXT,
                            result INT,
                            lastBossHealth INT,
                            length INT,
                            raidar TEXT,
                            dpsreport TEXT,
                            instance TEXT    
                            )""")

        # c.execute("""CREATE TABLE IF NOT EXIST players(
        #                     timestamp INT,
        #                     loglength INT,
        #                     char0 TEXT,
        #                     char1 TEXT,
        #                     char2 TEXT,
        #                     char3 TEXT,
        #                     char4 TEXT,
        #                     char5 TEXT,
        #                     char6 TEXT,
        #                     char7 TEXT,
        #                     char8 TEXT,
        #                     char9 TEXT
        #                     )""")

        self.init = True
        conn.commit()

    def getResourceDir(self):
        if not os.path.exists(DIR_RESOURCE) or not os.path.isdir(DIR_RESOURCE):
            os.makedirs(DIR_RESOURCE)
        return DIR_RESOURCE

    def getInfo(self, path):
        conn = self.getConnection()
        c = conn.cursor()

        c.execute("""SELECT * FROM encounters WHERE filename = ?""", (path,))
        enc = c.fetchone()
        #print(enc)

        info = None
        e = None

        if enc is not None:
            info = EncounterInfo(*enc)

        if enc is None:
            e = Encounter(path)
            logTime, loglength = e.getLogLength()
            c.execute("""SELECT * FROM encounters WHERE timestamp = ? AND loglength = ?""", (logTime, loglength,))
            enc = c.fetchone()

        if enc is None:
            e.parseQuick()
            info = EncounterInfo(e.startTime, loglength, path, e.kill, e.lowestBossHealth, e.encounterLength, "", "", e.entities[e.boss_addr].name)
            c.execute("""INSERT INTO encounters VALUES(?,?,?,?,?,?,?,?,?)""",(e.startTime, loglength, path, e.kill, e.lowestBossHealth, e.encounterLength, "", "", e.entities[e.boss_addr].name))
            conn.commit()
            info.new = True
        #
        # c.execute("""SELECT * FROM players WHERE timestamp = ? AND loglength = ?""", (info.timestamp, info.loglength,))
        # players = c.fetchone()
        #
        # if players == None:
        #     if e == None:
        #         e = Encounter(path)
        #
        #     if len(e.players) == 0:
        #         e.parseQuick()
        #
        #     info.players = e.players
        #     while(len(info.players < 10)):
        #         info.players.append("-1")
        #
        #     c.execute("""INSERT INTO players VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""", (info.timestamp, info.loglength, *info.players))
        #     conn.commit()

        return info

class EncounterInfo():
    def __init__(self, timestamp = -1, loglength = -1, fileName = "", kill = "Unknown", lastBossHealth = -1, length = -1, raidar = "", dpsreport = "", instance = ""):
        self.timestamp = timestamp
        self.loglength = loglength
        self.fileName = fileName
        self.kill = kill
        self.lastBossHealth = lastBossHealth
        self.length = length
        self.raidar = raidar
        self.dpsreport = dpsreport
        self.instance = instance
        self.new = False

if __name__ == '__main__':
    EncounterCacheHandler().getInfo("E:/arcdps.cbtlogs/Xera/20180430-214441.evtc")