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
            e.addr = struct.unpack("<Q", fh.read(8))[0]
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

        events = []
        print("start events")

        while(1):
            e = event()
            test = fh.read(8)
            if len(test) < 8:
                break
            e.time = struct.unpack("<Q", test)[0]
            e.src = struct.unpack("<Q", fh.read(8))[0]
            e.dest = struct.unpack("<Q", fh.read(8))[0]
            e.val = struct.unpack("<l", fh.read(4))[0]
            e.buff_dmg = struct.unpack("<l", fh.read(4))[0]
            e.overstack_val = struct.unpack("<H", fh.read(2))[0]
            e.skill_id = struct.unpack("<H", fh.read(2))[0]
            e.src_instid = struct.unpack("<H", fh.read(2))[0]
            e.dst_instid = struct.unpack("<H", fh.read(2))[0]
            e.src_master_instid = struct.unpack("<H", fh.read(2))[0]
            iss_offset = struct.unpack("<B", fh.read(1))[0] #internal tracking garbage
            iss_offset_target = struct.unpack("<B", fh.read(1))[0] #internal tracking garbage
            iss_bd_offset = struct.unpack("<B", fh.read(1))[0] #internal tracking garbage
            iss_bd_offset_target = struct.unpack("<B", fh.read(1))[0] #internal tracking garbage
            iss_alt_offset = struct.unpack("<B", fh.read(1))[0] #internal tracking garbage
            iss_alt_offset_target = struct.unpack("<B", fh.read(1))[0] #internal tracking garbage
            skar = struct.unpack("<B", fh.read(1))[0] #internal tracking garbage
            skar_alt = struct.unpack("<B", fh.read(1))[0] #internal tracking garbage
            skar_use_alt = struct.unpack("<B", fh.read(1))[0] #internal tracking garbage
            e.iff = struct.unpack("<B", fh.read(1))[0]
            e.buff = struct.unpack("<B", fh.read(1))[0]
            e.result = struct.unpack("<B", fh.read(1))[0]
            e.is_activation = struct.unpack("<B", fh.read(1))[0]
            e.is_buffremove = struct.unpack("<B", fh.read(1))[0]
            e.is_ninety = struct.unpack("<B", fh.read(1))[0]
            e.is_fifty = struct.unpack("<B", fh.read(1))[0]
            e.is_moving = struct.unpack("<B", fh.read(1))[0]
            e.is_statechange = struct.unpack("<B", fh.read(1))[0]
            e.is_flanking = struct.unpack("<B", fh.read(1))[0]
            e.is_shields = struct.unpack("<B", fh.read(1))[0]
            result_local = struct.unpack("<B", fh.read(1))[0] #internal tracking garbage
            ident_local = struct.unpack("<B", fh.read(1))[0] #internal tracking garbage
            #e.print()
            events.append(e)
        events[0].print()
        events[len(events)-1].print()

        print("Encounter Length: %s" % str(events[len(events)-1].time - events[0].time))



if __name__ == '__main__':
    p = Parser('./test2.evtc')