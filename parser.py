import struct
import reference
from event import event
from entity import entity

class Parser(object):
    def __init__(self, filepath):
        with open(filepath, 'rb') as fh:
            self.parse(fh)

    def parse(self, fh):
        fh.read(4) # skip random EVTC tag
        version = fh.read(8)
        fh.read(1) # skip
        inst_id = struct.unpack("<h", fh.read(2))[0]
        fh.read(1) # skip
        player_count = struct.unpack("<I", fh.read(4))[0]
        print("count %s" % player_count )

        entities = [0]

        for i in range(player_count):
            e = entity()
            agent = struct.unpack("<Q", fh.read(8))[0]
            e.setElite(fh.read(4), fh.read(4))
            tough = struct.unpack("<i", fh.read(4))[0]
            healing = struct.unpack("<i", fh.read(4))[0]
            condi = struct.unpack("<i", fh.read(4))[0]
            e.setName(fh.read(68))
            e.print()
            #if elite != -1:
            #print("%s - Entity: %s Subsquad: %s Profession: %s : %s %s %s" % (elite, name, subsquad, prof, tough, healing, condi))
        print(version)
        print(inst_id)
        print(player_count)

        skill_count = struct.unpack("<i", fh.read(4))[0]
        print("Skill count: %s" % skill_count)

        for i in range(skill_count):
            skill_id = struct.unpack("<i", fh.read(4))[0]
            name = fh.read(64).decode('ascii').rstrip('\x00')
            #print("Action: %s id: %s" % (name, skill_id))

        events = [0]
        eventCount = 0
        startTime = 0
        print("start events")

        for i in range(10):
            e = event()
            e.time = struct.unpack("<Q", fh.read(8))[0]
            if startTime == 0:
                startTime = e.time
            e.src = struct.unpack("<Q", fh.read(8))[0]
            e.dest = struct.unpack("<Q", fh.read(8))[0]
            e.val = struct.unpack("<l", fh.read(4))[0]
            e.buff_dmg = struct.unpack("<l", fh.read(4))[0]
            e.overstack_val = struct.unpack("<I", fh.read(4))[0]
            e.skill_id = struct.unpack("<I", fh.read(4))[0]
            e.src_instid = struct.unpack("<I", fh.read(4))[0]
            e.dst_instid = struct.unpack("<I", fh.read(4))[0]
            e.src_master_instid = struct.unpack("<I", fh.read(4))[0]
            iss_offset = struct.unpack("<H", fh.read(2))[0] #internal tracking garbage
            iss_offset_target = struct.unpack("<H", fh.read(2))[0] #internal tracking garbage
            iss_bd_offset = struct.unpack("<H", fh.read(2))[0] #internal tracking garbage
            iss_bd_offset_target = struct.unpack("<H", fh.read(2))[0] #internal tracking garbage
            iss_alt_offset = struct.unpack("<H", fh.read(2))[0] #internal tracking garbage
            iss_alt_offset_target = struct.unpack("<H", fh.read(2))[0] #internal tracking garbage
            skar = struct.unpack("<H", fh.read(2))[0] #internal tracking garbage
            skar_alt = struct.unpack("<H", fh.read(2))[0] #internal tracking garbage
            skar_use_alt = struct.unpack("<H", fh.read(2))[0] #internal tracking garbage
            e.iff = struct.unpack("<H", fh.read(2))[0]
            e.buff = struct.unpack("<H", fh.read(2))[0]
            e.result = struct.unpack("<H", fh.read(2))[0]
            e.is_activation = struct.unpack("<H", fh.read(2))[0]
            e.is_buffremove = struct.unpack("<H", fh.read(2))[0]
            e.is_ninety = struct.unpack("<H", fh.read(2))[0]
            e.is_fifty = struct.unpack("<H", fh.read(2))[0]
            e.is_moving = struct.unpack("<H", fh.read(2))[0]
            e.is_statechange = struct.unpack("<H", fh.read(2))[0]
            e.is_flanking = struct.unpack("<H", fh.read(2))[0]
            e.is_shields = struct.unpack("<H", fh.read(2))[0]
            result_local = struct.unpack("<H", fh.read(2))[0] #internal tracking garbage
            ident_local = struct.unpack("<H", fh.read(2))[0] #internal tracking garbage
            e.print()
            events[eventCount] = e




if __name__ == '__main__':
    p = Parser('./test2.evtc')