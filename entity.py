import struct
from event import event
from reference import cbtstatechange, cbtactivation

class Entity:

    def __init__(self):
        self.name = "Unknown"
        self.account = -1
        self.character = -1
        self.subsquad = -1
        self.id = -1

        self.prof = -1
        self.elite = -1

        self.addr = -1

        self.inst_id = []

        self.firstSeen = -1
        self.lastSeen = -1
        self.combatStartTime = 0
        self.combatDuration = 0
        self.downed = 0
        self.dead = 0
        self.deathTime = 1

        self.isPOV = 0

        self.minions = []

        self.isPlayer = False

        self.damage = Damage()
        self.buffs = Buffs()

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
        name = s.decode('utf-8').rstrip('\x00')
        if self.elite == -1:
            self.name = name
        else:
            self.subsquad = name[-1:]
            self.name = name[:-1]
            split = self.name.split(":")
            #print(split)
            self.character = split[0].rstrip('\x00')
            self.account = split[1].rstrip('\x00')

    def addEvent(self, evt, entityCheck):

        # if self.firstSeen == -1:
        #     self.firstSeen = evt.time
        #     # if self.isPlayer:
        #     #     print("%s first seen %s" % (self.character, evt.time))
        # self.lastSeen = evt.time

        if evt.src == self.addr:
            if evt.is_statechange == cbtstatechange.CBTS_ENTERCOMBAT:
                #print("%s enter %s", (self.name, evt.time))
                self.combatStartTime = evt.time
            if evt.is_statechange == cbtstatechange.CBTS_EXITCOMBAT:
                #if self.isPlayer == True:
                #    print("%s exit %s", (self.name, evt.time))
                self.combatDuration = evt.time - self.firstSeen
            if evt.is_statechange == cbtstatechange.CBTS_CHANGEDOWN:
                self.downed += 1
            if evt.is_statechange == cbtstatechange.CBTS_CHANGEDEAD:
                #print("%s dead %s", (self.name, evt.time))
                self.dead += 1
                self.deathTime = evt.time
            if evt.is_statechange == cbtstatechange.CBTS_POINTOFVIEW:
                self.isPOV = 1

            if evt.is_activation:
                self.damage.addCast(evt)

            if not evt.is_activation and not evt.is_buffremove and entityCheck is True:
                if evt.is_buff:
                    if evt.buff_dmg and not evt.val:
                        self.damage.addDamageOut(evt.dest, evt.skill_id, evt.buff_dmg, evt.dest == self.addr, True)
                elif not evt.is_buff:
                    self.damage.addDamageOut(evt.dest, evt.skill_id, evt.val, evt.dest == self.addr, False)

        if evt.dest == self.addr:
            if not evt.is_activation and not evt.is_buffremove:
                if evt.is_buff:
                    if evt.buff_dmg and not evt.val:
                        self.damage.addDamageIn(evt.src, evt.skill_id, evt.buff_dmg, evt.result, evt.is_shields, evt.dest == self.addr, True)

                elif not evt.is_buff:
                    self.damage.addDamageIn(evt.src, evt.skill_id, evt.val, evt.result, evt.is_shields, evt.dest == self.addr, False)

        # if not evt.is_activation and not evt.buff_dmg and evt.val:
        #     self.buffs.addApplication(evt.skill_id, evt.val, evt.src, evt.time)
            # if self.character == "Teeny Tiny Titan":
            #     evt.print()
            #     print("")
    def print(self):
        print(vars(self))

class Damage:

    def __init__(self):

        self.foes = dict()
        self.skills = dict()

        self.totalPhysIn = 0
        self.totalCondiIn = 0
        self.totalBarrier = 0
        self.totalIn = 0

        self.totalPhysOut = 0
        self.totalCondiOut = 0
        self.totalMinionOut = 0
        self.totalOut = 0

    def addMinionDamage(self, dest, val):
        self.totalMinionOut += val
        self.totalOut += val

        if dest not in self.foes:
            self.foes[dest] = Foe()
        self.foes[dest].totalDamageIn += val

    def addDamageOut(self, dest, skill_id, val, selfInflicted, isCondi):
        if dest not in self.foes:
            self.foes[dest] = Foe()

        f:Foe = self.foes[dest]
        f.totalDamageIn += val

        if skill_id not in f.skillsIn:
            f.skillsIn[skill_id] = Skill()

        s:Skill = f.skillsIn[skill_id]
        s.totalDamage += val
        s.totalImpacts += 1

        if not selfInflicted:
            self.totalOut += val
            if isCondi:
                self.totalCondiOut += val
            else:
                self.totalPhysOut += val

            if skill_id not in self.skills:
                self.skills[skill_id] = Skill()
            s:Skill = self.skills[skill_id]

            s.totalDamage += val
            s.totalImpacts += 1

    def addDamageIn(self, src, skill_id, val, result, is_shields, selfInflicted, isCondi):
        if src not in self.foes:
            self.foes[src] = Foe()
        f:Foe = self.foes[src]

        if skill_id not in f.skillsOut:
            f.skillsOut[skill_id] = Skill()
        s:Skill = f.skillsOut[skill_id]

        f.totalDamageOut += val
        s.totalDamage += val
        s.totalImpacts += 1

        if is_shields:
            s.totalBarrier += val

        if result not in s.results:
            s.results[result] = 0
        s.results[result] += 1

        if not selfInflicted:
            self.totalIn += val
            if isCondi:
                self.totalCondiIn += val
            else:
                self.totalPhysIn += val

    def addCast(self, evt: event):
        if evt.skill_id not in self.skills:
            self.skills[evt.skill_id] = Skill()
        # if evt.skill_id not in self.foes[evt.dest].skillsIn[evt.skill_id]:
        #     self.foes[evt.dest].skillsIn[evt.skill_id] = Skill()

        if evt.is_activation == cbtactivation.ACTV_CANCEL_CANCEL:# or evt.is_activation == cbtactivation.ACTV_CANCEL_FIRE:
            self.skills[evt.skill_id].canceled += 1
            self.skills[evt.skill_id].casts += 1
            self.skills[evt.skill_id].wasted += evt.val
            self.skills[evt.skill_id].totalCastTime += evt.val
            # self.foes[evt.dest].skillsIn[evt.skill_id].canceled += 1
            # self.foes[evt.dest].skillsIn[evt.skill_id].wasted += evt.val
            # self.foes[evt.dest].skillsIn[evt.skill_id].totalCastTime += evt.val

        elif evt.is_activation == cbtactivation.ACTV_NORMAL or evt.is_activation == cbtactivation.ACTV_QUICKNESS:
            self.skills[evt.skill_id].casts += 1
            self.skills[evt.skill_id].totalCastTime += evt.val
            # self.foes[evt.dest].skillsIn[evt.skill_id].casts += 1
            # self.foes[evt.dest].skillsIn[evt.skill_id].totalCastTime += evt.val

class Foe:
    def __init__(self):
        self.totalDamageIn = 0
        self.totalDamageOut = 0
        self.skillsIn = dict()
        self.skillsOut = dict()

class Skill:
    def __init__(self):
        self.totalDamage = 0
        self.totalImpacts = 0
        self.totalBarrier = 0
        self.canceled = 0
        self.casts = 0
        self.totalCastTime = 0
        self.wasted = 0
        self.results = dict()

class Buffs:
    def __init__(self):
        self.buffList = dict()

    def addApplication(self, buffId, duration, src, time):

        # if id == 740:
        #     print("")

        if buffId not in self.buffList:
            self.buffList[buffId] = []
        self.buffList[buffId].append(Buff(time, duration, src))
        self.buffList[buffId].append(Buff(time + duration, 0, None, 1))

class Buff:
    def __init__(self, time, dur, src, remove = 0):
        self.time = time
        self.duration = dur
        self.source = src
        self.isRemove = remove
