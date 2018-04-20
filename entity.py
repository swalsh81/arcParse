import struct

class entity():

    name = ''
    subsquad = -1
    id = -1

    prof = -1
    elite = -1

    addr = -1

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


    def print(self):
        print(vars(self))