class event():

    time = -1
    src = -1
    dest = -1
    val = -1
    buff_dmg = -1
    overstack_val = -1
    skill_id = -1
    src_instid = -1
    dst_instid = -1
    src_master_instid = -1
    iff = -1
    is_buff = -1
    result = -1
    is_activation = -1
    is_buffremove = -1
    is_ninety = -1
    is_fifty = -1
    is_moving = -1
    is_statechange = -1
    is_flanking = -1
    is_shields = -1

    def print(self):
        print(vars(self))