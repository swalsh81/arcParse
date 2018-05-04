import struct
from event import event
from reference import cbtstatechange, cbtresult, cbtbuffremove, cbtactivation

class entity():

    SKILL_INC_TOTAL_DAMAGE = -100
    SKILL_INC_IMPACT = -101
    SRC_INC_TOTAL_DAMAGE = -102

    RESULT_MODIFIER = 200

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
        self.physDamageTotal = 0
        self.condiDamageTotal = 0

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
            if not evt.is_activation and not evt.is_buffremove:
                # if evt.result != cbtresult.CBTR_NORMAL:
                #     evt.print()
                #     print(cbtresult.keys(evt.result))
                if evt.is_buff:
                    if evt.buff_dmg and not evt.val:
                        self.addIncDamage(evt.src, evt.skill_id, evt.buff_dmg, evt.result)
                        self.condiDamageTotal += evt.buff_dmg

                elif not evt.is_buff:
                    self.addIncDamage(evt.src, evt.skill_id, evt.val, evt.result)
                    self.physDamageTotal += evt.val

        self.eventCount += 1
        self.events.append(evt)

    def addIncDamage(self, src, skill_id, val, result):
        if src not in self.damageInc:
            self.damageInc[src] = dict()
            self.damageInc[src][self.SRC_INC_TOTAL_DAMAGE] = 0
        if skill_id not in self.damageInc[src]:
            self.damageInc[src][skill_id] = dict()
            self.damageInc[src][skill_id][self.SKILL_INC_IMPACT] = 0
            self.damageInc[src][skill_id][self.SKILL_INC_TOTAL_DAMAGE] = 0

        self.damageInc[src][self.SRC_INC_TOTAL_DAMAGE] += val
        self.damageInc[src][skill_id][self.SKILL_INC_IMPACT] += 1
        self.damageInc[src][skill_id][self.SKILL_INC_TOTAL_DAMAGE] += val

        if (self.RESULT_MODIFIER + result) not in self.damageInc[src][skill_id]:
            self.damageInc[src][skill_id][self.RESULT_MODIFIER + result] = 0
        self.damageInc[src][skill_id][self.RESULT_MODIFIER + result] += 1

    def print(self):
        print(vars(self))