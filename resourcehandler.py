from PyQt5.QtCore import pyqtSignal, QObject

import urllib.request, json, os, sqlite3
from urllib.request import HTTPError

import reference, worker

import sched, time


GW2API_SPECIALIZATIONS = "https://api.guildwars2.com/v2/specializations"
GW2API_PROFESSIONS = "https://api.guildwars2.com/v2/professions"
GW2API_SKILLS = "https://api.guildwars2.com/v2/skills"

DIR_RESOURCE = "./resources"

DB_URL = "resources.db"

class ResourceHandler(QObject):
    ID = -100
    PROF_ID = -101
    NAME = -102
    PROFESSION = -103
    PROFESSION_ICON = -104

    init = False

    connection = None

    timerTick = 10
    lastAccessed = 0

    timerTicked = pyqtSignal()

    def __init__(self):
        super(ResourceHandler, self).__init__()
        self.timer = sched.scheduler(time.time, time.sleep)
        self.getConnection()
        self.timerTicked.connect(self.checkTimer)

    def getConnection(self):
        self.lastAccessed = time.time()
        if self.connection == None or self.init == False:
            print("Open DB")
            path = os.path.abspath(self.getResourceDir() + "/" + DB_URL)
            self.connection = sqlite3.connect(path)
            self.initDB(self.connection)
            self.startConnectionTimeout()
        return self.connection

    def startConnectionTimeout(self):
        self.timer.enter(self.timerTick, 1, self.doTick)
        #print("start")
        job = worker.Job(self.timer.run)
        worker.ThreadPool.start(job)

    def doTick(self):
        self.timerTicked.emit()

    def checkTimer(self):
        #print("check")
        if self.lastAccessed + self.timerTick*2 < time.time():
            self.connection.close()
            self.connection = None
            print("Close DB")
        else:
            #print("reset")
            self.startConnectionTimeout()

    def initDB(self, conn):

        c = conn.cursor()

        c.execute("""SELECT * FROM sqlite_master WHERE type = ? AND name = ?""",('table','profs',))
        result = c.fetchall()
        if len(result) < 1:
            c.execute("""CREATE TABLE IF NOT EXISTS profs(
                                        id INTEGER NOT NULL,
                                        name TEXT
                                        )""")
            profs = json.loads(self.getFromUrl(GW2API_PROFESSIONS))
            for i in range(1,10):
                c.execute("""INSERT INTO profs VALUES(?,?)""",(i, profs[i-1]))

        c.execute("""CREATE TABLE IF NOT EXISTS specs(
                            id INTEGER NOT NULL,
                            prof_id INTEGER NOT NULL,
                            name TEXT,
                            profession TEXT,
                            profession_icon BLOB    
                            )""")

        c.execute("""CREATE TABLE IF NOT EXISTS skills(
                            id INTEGER NOT NULL,
                            icon BLOB)""")

        self.init = True
        conn.commit()

    def getResourceDir(self):
        if not os.path.exists(DIR_RESOURCE) or not os.path.isdir(DIR_RESOURCE):
            os.makedirs(DIR_RESOURCE)
        return DIR_RESOURCE

    def getSpecialization(self, id, prof):
        conn = self.getConnection()
        c = conn.cursor()

        c.execute("""SELECT * FROM specs WHERE id = ? AND prof_id = ?""",(id,prof,))

        spec = c.fetchone()

        if len(c.fetchall()) < 1:
            data = None
            iconBlob = None
            #print("ID %s" % id)

            if id == 0:
                c.execute("""SELECT * FROM profs WHERE id = ?""",(prof,))
                profName = c.fetchone()[1]
                data = json.loads(self.getFromUrl(GW2API_PROFESSIONS + "/%s" % profName))
                data['profession'] = profName
                iconBlob = self.getFromUrl(reference.icons.base[profName])
            else:
                data = json.loads(self.getFromUrl(GW2API_SPECIALIZATIONS + "/%s" % str(id)))
                iconBlob = self.getFromUrl(reference.icons.elite[data['name']])

            if data != None and iconBlob != None:
                try:
                    c.execute("""INSERT INTO specs VALUES(?,?,?,?,?)""", (id, prof, data['name'], data['profession'], iconBlob))
                    conn.commit()
                except Exception as e:
                    print("except")
                    print(e)
            #print("try again")

            c.execute("""SELECT * FROM specs WHERE id = ? AND prof_id = ?""", (id, prof,))
            spec = c.fetchone()

        info = dict()
        info[self.ID] = spec[0]
        info[self.PROF_ID] = spec[1]
        info[self.NAME] = spec[2]
        info[self.PROFESSION] = spec[3]
        info[self.PROFESSION_ICON] = spec[4]

        return info

    def getFromUrl(self, link, counter = 0):
        try:
            with urllib.request.urlopen(link) as url:
                data = url.read()
                return data
        except HTTPError as e:
            None
            #print(e)

    def getSkillIcon(self,skill):
        conn = self.getConnection()
        c = conn.cursor()

        c.execute("""SELECT * FROM skills WHERE id = ?""", (skill,))
        iconBlob = None
        if len(c.fetchall()) < 1:
            url = "%s/%s" %(GW2API_SKILLS, skill)
            data = json.loads(self.getFromUrl("%s/%s" %(GW2API_SKILLS, skill)))
            iconUrl = data['icon']
            iconBlob = self.getFromUrl(data['icon'])

            if iconBlob != None:
                try:
                    c.execute("""INSERT INTO skills VALUES(?,?)""",(skill, iconBlob))
                    conn.commit()
                except Exception as e:
                    None
                    #print("No Icon %S" % e)
        else:
            iconBlob = c.fetchone()[1]
        return iconBlob


if __name__ == '__main__':
    i = ResourceHandler().getSkillIcon(5492)
    print(i)
    img = 'https://render.guildwars2.com/file/1C91E9C799469ACC6EAF1ACD4B0AD8ACAB0C69A2/103035.png'
    r = ResourceHandler()
    i = r.getFromUrl(img, 0)
    print(i)
    print("done")