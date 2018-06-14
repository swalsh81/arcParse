from PyQt5 import QtGui

classes = [-1,-1,-1,-1,-1,-1,"Mesmer","Necromancer",-1]

HIGHLIGHT_COLOR = QtGui.QColor(100,100,255,40)
HIGHLIGHT_COLOR_ARRAY = [100/255,100/255,255/255,40/100]

CLASS_COLORS = ["",(0,136,170), (195, 131, 1), (135,77,36), (94,143,17), (140,65,74), (186,9,24), (136,0,170), (0,85,68),(103,15,15)]

def getClass(i):

    if classes[i-1]  == -1:
        return i
    else:
        return classes[i-1]


class cbtresult:
    CBTR_NORMAL = 0
    CBTR_CRIT =1
    CBTR_GLANCE = 2
    CBTR_BLOCK = 3
    CBTR_EVADE = 4
    CBTR_INTERRUPT = 5
    CBTR_ABSORB = 6
    CBTR_BLIND = 7
    CBTR_KILLINGBLOW = 8

class iff:
	IFF_FRIEND = 0
	IFF_FOE = 1
	IFF_UNKNOWN = 2

class cbtactivation:
    ACTV_NONE = 0
    ACTV_NORMAL = 1
    ACTV_QUICKNESS = 2
    ACTV_CANCEL_FIRE = 3
    ACTV_CANCEL_CANCEL = 4
    ACTV_RESET = 5

class cbtstatechange:
    CBTS_NONE = 0 
    CBTS_ENTERCOMBAT = 1
    CBTS_EXITCOMBAT = 2
    CBTS_CHANGEUP = 3
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

class cbtbuffremove:
    CBTB_NONE = 0 
    CBTB_ALL = 1 
    CBTB_SINGLE = 2 
    CBTB_MANUAL = 3

class icons:

    base = dict()
    elite = dict()

    base['Warrior']="https://wiki.guildwars2.com/images/d/db/Warrior_tango_icon_200px.png"
    base['Guardian']="https://wiki.guildwars2.com/images/6/6c/Guardian_tango_icon_200px.png"
    base['Revenant']="https://wiki.guildwars2.com/images/a/a8/Revenant_tango_icon_200px.png"
    base['Engineer']="https://wiki.guildwars2.com/images/2/2f/Engineer_tango_icon_200px.png"
    base['Ranger']="https://wiki.guildwars2.com/images/5/51/Ranger_tango_icon_200px.png"
    base['Thief']="https://wiki.guildwars2.com/images/1/19/Thief_tango_icon_200px.png"
    base['Elementalist']="https://wiki.guildwars2.com/images/a/a0/Elementalist_tango_icon_200px.png"
    base['Necromancer']="https://wiki.guildwars2.com/images/c/cd/Necromancer_tango_icon_200px.png"
    base['Mesmer']="https://wiki.guildwars2.com/images/7/73/Mesmer_tango_icon_200px.png"

    elite['Spellbreaker']="https://wiki.guildwars2.com/images/7/78/Spellbreaker_tango_icon_200px.png"
    elite['Berserker']="https://wiki.guildwars2.com/images/8/80/Berserker_tango_icon_200px.png"
    elite['Firebrand']="https://wiki.guildwars2.com/images/7/73/Firebrand_tango_icon_200px.png"
    elite['Dragonhunter']="https://wiki.guildwars2.com/images/1/1f/Dragonhunter_tango_icon_200px.png"
    elite['Herald']="https://wiki.guildwars2.com/images/c/c7/Herald_tango_icon_200px.png"
    elite['Renegade']="https://wiki.guildwars2.com/images/b/bc/Renegade_tango_icon_200px.png"
    elite['Scrapper']="https://wiki.guildwars2.com/images/3/3a/Scrapper_tango_icon_200px.png"
    elite['Holosmith']="https://wiki.guildwars2.com/images/a/ae/Holosmith_tango_icon_200px.png"
    elite['Druid']="https://wiki.guildwars2.com/images/6/6d/Druid_tango_icon_200px.png"
    elite['Soulbeast']="https://wiki.guildwars2.com/images/f/f6/Soulbeast_tango_icon_200px.png"
    elite['Deadeye']="https://wiki.guildwars2.com/images/b/b0/Deadeye_tango_icon_200px.png"
    elite['Daredevil']="https://wiki.guildwars2.com/images/c/ca/Daredevil_tango_icon_200px.png"
    elite['Tempest']="https://wiki.guildwars2.com/images/9/90/Tempest_tango_icon_200px.png"
    elite['Weaver']="https://wiki.guildwars2.com/images/3/31/Weaver_tango_icon_200px.png"
    elite['Chronomancer']="https://wiki.guildwars2.com/images/8/8b/Chronomancer_tango_icon_200px.png"
    elite['Mirage']="https://wiki.guildwars2.com/images/a/a9/Mirage_tango_icon_200px.png"
    elite['Reaper']="https://wiki.guildwars2.com/images/9/95/Reaper_tango_icon_200px.png"
    elite['Scourge']="https://wiki.guildwars2.com/images/8/8a/Scourge_tango_icon_200px.png"