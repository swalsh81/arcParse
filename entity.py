import struct
from event import event
from reference import cbtstatechange, cbtresult, cbtbuffremove, cbtactivation

class entity():

    def __init__(self):
        self.name = -1
        self.account = -1
        self.character = -1
        self.subsquad = -1
        self.id = -1

        self.prof = -1
        self.elite = -1

        self.addr = -1

        self.inst_id = []

        self.damageInc = dict()
        self.damageTotal = 0

        self.firstSeen = -1
        self.lastSeen = -1

        self.downed = 0
        self.dead = 0

        self.isPOV = 0

        self.minions = []
        self.eventCount = 0
        self.events = []

        self.isPlayer = False

    def setElite(self, prof, elite):

        #print(prof)
        #print(elite)

        elite = struct.unpack("<l", elite)[0]

        if elite != -1:
            self.elite = elite
            self.prof = struct.unpack("<L", prof)[0]
            self.isPlayer = True
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
            split = self.name.split(":")
            print(split)
            self.character = split[0].rstrip('\x00')
            self.account = split[1].rstrip('\x00')

    def addEvent(self, evt):

        if evt.src == self.addr:
            if evt.is_statechange == cbtstatechange.CBTS_EXITCOMBAT:
                self.combatStartTime = evt.time
            if evt.is_statechange == cbtstatechange.CBTS_EXITCOMBAT:
                self.combatDuration = evt.time - self.combatStartTime
            if evt.is_statechange == cbtstatechange.CBTS_CHANGEDOWN:
                self.downed += 1
            if evt.is_statechange ==  cbtstatechange.CBTS_CHANGEDEAD:
                self.dead += 1
            if evt.is_statechange == cbtstatechange.CBTS_POINTOFVIEW:
                self.isPOV == 1

            if not evt.is_activation and not evt.is_buffremove and not evt.is_buff:
                None

        if evt.dest == self.addr:
            if not evt.is_activation and not evt.is_buffremove and not evt.is_buff:
                if evt.src not in self.damageInc:
                    self.damageInc[evt.src] = dict()
                if evt.skill_id not in self.damageInc[evt.src]:
                    self.damageInc[evt.src][evt.skill_id] = dict()
                    self.damageInc[evt.src][evt.skill_id]['count'] = 0
                    self.damageInc[evt.src][evt.skill_id]['damage'] = 0

                self.damageInc[evt.src][evt.skill_id]['count'] += 1
                self.damageInc[evt.src][evt.skill_id]['damage'] += evt.val
                self.damageTotal += evt.val

        self.eventCount += 1
        self.events.append(evt)

    def print(self):
        print(vars(self))