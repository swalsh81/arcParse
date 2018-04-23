import struct
from event import event

class entity():

    def __init__(self):
        self.name = -1
        self.subsquad = -1
        self.id = -1

        self.prof = -1
        self.elite = -1

        self.addr = -1

        self.inst_id = []

        self.damageInc = dict()

    def setElite(self, prof, elite):

        #print(prof)
        #print(elite)

        elite = struct.unpack("<l", elite)[0]

        if elite != -1:
            self.elite = elite
            self.prof = struct.unpack("<L", prof)[0]
        else:
            upper = struct.unpack("<H", prof[-2:])[0]
            lower = struct.unpack("<H", prof[:-2])[0]
            #print(upper)
            #print(lower)
            if upper == -1:
                self.id = lower
            else:
                self.id = lower

    def setName(self, s):
        name = s.decode('ascii').rstrip('\x00')
        if self.elite == -1:
            self.name = name
        else:
            self.subsquad = name[-1:]
            self.name = name[:-1]
            self.id = self.name #for now

    #def addEvent(self, evt):


    def print(self):
        print(vars(self))