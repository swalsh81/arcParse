classes = [-1,-1,-1,-1,-1,-1,"Mesmer","Necromancer",-1]

def getClass(i):

    if classes[i-1] == -1:
        return i
    else:
        return classes[i-1]