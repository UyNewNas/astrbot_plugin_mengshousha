from enum import Enum

GameRoleConstDict = {
    "ORDINARY": "普通良民",
    "PEANUT": "花生侠",
    "DOCTOR": "法医侠",
    "ONEHIT": "单刀侠",
    "GUARD": "保安侠",
    "REVENGE": "复仇侠",
    "SCREAM": "尖叫侠",
    "ANCHOR": "主播侠",
    "BIG_EAR": "大耳侠",
    "ENGINEER": "工程侠",
    "WOLF_OLD": "狼外婆侠",
    "ORDINARY_EXTRA": "普通良民",
    "ORDINARY_KILLER": "普通杀手",
    "VARIETY_KILLER": "变脸杀手",
    "RIDDLE_KILLER": "谜语杀手",
    "INVISIBLE_KILLER": "隐身杀手",
    "PROFESSIONAL_KILLER": "专业杀手",
    "BAWU": "阿呆",
    "HAKA": "哈卡",
    "CARNIVORE": "食肉动物",
    "DEAD": "死神"    
}



# name = value
class GameRoleEnum(Enum):
    
    GOODMAN = list(range(0, 10+1)).append(20)
    GOODMAN_CAN_V = [3,4,5]
    # 普通良民
    ORDINARY = 0 
    # 花生侠
    PEANUT = 1 
    # 法医侠
    DOCTOR = 2 
    # 单刀侠
    ONEHIT = 3
    # 保安侠 
    GUARD = 4
    # 复仇侠
    REVENGE = 5
    # 尖叫侠
    SCREAM = 6
    # 主播侠
    ANCHOR = 7
    # 大耳侠
    BIG_EAR = 8
    # 工程侠
    ENGINEER = 9
    # 狼外婆侠
    WOLF_OLD = 10
    
    # 额外的普通良民(11-12人局启用)
    ORDINARY_EXTRA = 20
    
    BADMAN = list(range(11,15+1))
    # 普通杀手
    ORDINARY_KILLER = 11
    # 变脸杀手
    VARIETY_KILLER = 12
    # 谜语杀手
    RIDDLE_KILLER = 13
    # 隐身杀手
    INVISIBLE_KILLER = 14
    # 专业杀手
    PROFESSIONAL_KILLER = 15
    # 静音杀手
    MUTING_KILLER = 66
    
    NEUTRALMAN = list(range(16, 19+1))
    NEUTRALMAN_CAN_V = [18,19]
    # 阿呆
    BAWU = 16
    # 哈卡
    HAKA = 17
    # 食肉动物
    CARNIVORE = 18
    # 死神
    DEAD = 19
    
    

    
    
    