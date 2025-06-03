
from enum import Enum
from .sp_mengshousha import DataMengShouSha
spm = DataMengShouSha()
roleCountConfig = {
    3: {
        "Good": 1,
        "Bad": 1,
        "Neutral": 1
    },
    8: {
        "Good": 5,
        "Bad": 2,
        "Neutral": 1            
    },
    9: {
        "Good": 6,
        "Bad": 2,
        "Neutral": 1
    },
    10: {
        "Good": 6,
        "Bad": 2,
        "Neutral": 2
    },
    11: {
        "Good": 7,
        "Bad": 2,
        "Neutral": 2
    },
    12: {
        "Good": 7, 
        "Bad": 3,
        "Neutral": 2
    }
}

class GameSceneEnum(Enum): # 游戏场景状态机
    WAITING = "等待中"
    STARTING = "游戏中"
    MEETING = "会议中"
    ENDING = "结束"

class GameScene():
    
    def __init__(self):
        pass
    
    def create_new_scene(self, room_id:str, player_ids:list):
        scene_id = spm.generate_6digit_id()
        new_scene = {
            "scene_id": scene_id,
            "room_id": room_id,
            "player_ids": player_ids,
            "status": "待分配角色",
            "count": len(player_ids),
            "role_info": {},
            "ate_info": [],
            "dead_info": [],
            "dead_info_in_this_meeting": [],
            "meeting":{}
        }
        spm.update_game_scene(scene_id, new_scene)
        return "待分配角色",scene_id,new_scene
    
    def get_game_scene(self, scene_id:str):
        return spm.get_game_scene(scene_id)
    
    def get_game_scenes(self):
        return spm.get_game_scenes()
    
    def get_scene_from_room(self, room_id:str):
        scenes = spm.get_game_scenes()
        for scene_id, scene in scenes.items():
            if scene["room_id"] == room_id:
                return scene_id, scene
        return None, None
    
    def assign_role(self, scene_id:str):
        import random
        scene = spm.get_game_scene(scene_id)
        count = scene["count"]
        if count < 8:
            if count != 3:
                raise ValueError(f"玩家数量{count}不足,无法开始游戏")
        if count > 12:
            raise ValueError(f"玩家数量{count}过多,无法开始游戏")
        roleCount = roleCountConfig[count]
        goodRoleList = list(range(0, 10+1))
        if count >= 11:
            goodRoleList.append(20)
        badRoleList = list(range(11, 15+1))
        neutralRoleList = list(range(16, 19+1))
        
        player_ids = scene["player_ids"]
        playerList = player_ids.copy()
        random.shuffle(playerList)
        goodPlayerList = playerList[:roleCount["Good"]]
        badPlayerList = playerList[roleCount["Good"]:roleCount["Good"]+roleCount["Bad"]]
        neutralPlayerList = playerList[roleCount["Good"]+roleCount["Bad"]:roleCount["Good"]+roleCount["Bad"]+roleCount["Neutral"]]
        
        goodRoleList = random.sample(goodRoleList, roleCount["Good"])
        badRoleList = random.sample(badRoleList, roleCount["Bad"])
        neutralRoleList = random.sample(neutralRoleList, roleCount["Neutral"])
        
        for index, player in enumerate(goodPlayerList):
            scene["role_info"][player] = goodRoleList[index]
        for index, player in enumerate(badPlayerList):
            scene["role_info"][player] = badRoleList[index]
        for index, player in enumerate(neutralPlayerList):
            scene["role_info"][player] = neutralRoleList[index]
        
        scene["status"] = "游戏中"
        spm.update_game_scene(scene_id, scene)
        return scene["status"],scene["role_info"]

    def player_to_dead(self, scene_id:str, source_player_id:str, target_player_id:str):
        scene = spm.get_game_scene(scene_id)
        scene["dead_info_in_this_meeting"].append(target_player_id)
        scene["dead_info"].append(target_player_id)
        # TODO 添加具体死亡信息日志
        spm.update_game_scene(scene_id, scene)
        return True
    
    def player_to_ate(self, scene_id:str, source_player_id:str, target_player_id:str):
        scene = spm.get_game_scene(scene_id)
        scene["ate_info"].append({"source_player_id": source_player_id, "target_player_id": target_player_id})
        # TODO 添加具体被吃信息日志
        spm.update_game_scene(scene_id, scene)
        return True
    
    def clear_ate_info(self, scene_id:str):
        scene = spm.get_game_scene(scene_id)
        scene["ate_info"] = []
        spm.update_game_scene(scene_id, scene)
        return True
    
    # 召开会议
    def meeting_start(self, scene_id:str, alert_player_id:str, target_player_id:str|None=None):
        scene = spm.get_game_scene(scene_id)
        scene["meeting"] = {
            "alert_player_id": alert_player_id, 
            "target_player_id": target_player_id,
            "dead_player_ids": scene["dead_info_in_this_meeting"]}
        scene["status"] = "会议中"
        spm.update_game_scene(scene_id, scene)
        return True
    
    # 触摸尸体报警召开会议
    def touch_body_alert(self, scene_id:str, source_player_id:str, target_player_id:str):
        self.meeting_start(scene_id, source_player_id)
    
    #  结束会议
    def meeting_end(self, scene_id:str):
        scene = spm.get_game_scene(scene_id)
        scene["dead_info_in_this_meeting"] = []
        spm.update_game_scene(scene_id, scene)        
        return True