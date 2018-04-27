
def prettyTimestamp(time):
    millis = time %1000
    time = int((time - millis)/1000)
    sec = int(time%60)
    min = int((time - sec)/60)

    return "{:0>2d}:{:0>2d}.{:0>3d}".format(min, sec, millis)

