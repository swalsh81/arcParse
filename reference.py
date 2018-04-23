from enum import Enum

classes = [-1,-1,-1,-1,-1,-1,"Mesmer","Necromancer",-1]

def getClass(i):

    if classes[i-1]  == -1:
        return i
    else:
        return classes[i-1]


class cbtresult(Enum):
    CBTR_NORMAL = 0
    CBTR_CRIT =1
    CBTR_GLANCE = 2
    CBTR_BLOCK = 3
    CBTR_EVADE = 4
    CBTR_INTERRUPT = 5
    CBTR_ABSORB = 6
    CBTR_BLIND = 7
    CBTR_KILLINGBLOW = 8

class cbtactivation(Enum):
    ACTV_NONE = 0
    ACTV_NORMAL = 1
    ACTV_QUICKNESS = 2
    ACTV_CANCEL_FIRE = 3
    ACTV_CANCEL_CANCEL = 4
    ACTV_RESET = 5

class cbtstatechange(Enum):
    CBTS_NONE = 0 
    CBTS_ENTERCOMBAT = 1
    CBTS_EXITCOMBAT = 2
    CBTS_CHANGEUP =3 
    CBTS_CHANGEDEAD = 4
    CBTS_CHANGEDOWN = 5
    CBTS_SPAWN = 6 
    CBTS_DESPAWN = 7 
    CBTS_HEALTHUPDATE = 8 
    CBTS_LOGSTART = 9
    CBTS_LOGEND = 10 
    CBTS_WEAPSWAP = 11
    CBTS_MAXHEALTHUPDATE = 12 
    CBTS_POINTOFVIEW = 13
    CBTS_LANGUAGE = 14
    CBTS_GWBUILD = 15
    CBTS_SHARDID = 16 
    CBTS_REWARD = 17

class cbtbuffremove(Enum):
    CBTB_NONE = 0 
    CBTB_ALL = 1 
    CBTB_SINGLE = 2 
    CBTB_MANUAL = 3