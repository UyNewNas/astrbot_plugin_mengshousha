'''
Author: slava
Date: 2025-05-29 15:28:07
LastEditTime: 2025-06-03 09:45:14
LastEditors: ch4nslava@gmail.com
Description: 

'''
import os
import json
import secrets
from typing import Dict, List, Optional, Set, Tuple

class IOMengShousha():
    """
    读取和写入mengshousha.json文件
    """
    
    def __init__(self):
        # 读取当前目录下的json文件
        path = os.path.dirname(__file__)
        path = os.path.join(path, "mengshousha.json")
        self.path = path
        self.data = self._read_json()
        self.data = self.data if self.data is not None else {}
        self.data = self.data if self.data != {} else {"mengshousha": {"rooms": {}, "player_room_unique": {}, "game_scenes": {}, "game_maps": {}, "used_ids": []}}
    
    def _read_json(self) -> Dict:
        """
        读取json文件
        """
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                os.remove(self.path)
        return {}

    def _write_json(self, data: Dict) -> None:
        """
        写入json文件
        """
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())

    def get(self, key: str) -> Dict:
        """
        获取json文件中的数据
        """
        return self.data.get(key, {})

    def put(self, key: str, value: Dict) -> None:
        """
        写入json文件中的数据
        """
        self.data[key] = value
        self._write_json(self.data)
        self.data = self._read_json()
        




class DataMengShouSha():    
    def __init__(self):
        self.sp = IOMengShousha() 
        sp_mengshousha_dict: None|Dict  = self.sp.get("mengshousha")
        if sp_mengshousha_dict is None or sp_mengshousha_dict == {}:
            sp_mengshousha_dict = {
                "rooms": {},
                "player_room_unique": {},
                "game_scenes": {},
                "game_maps": {},
                "used_ids": []
            }
            self.sp.put("mengshousha", sp_mengshousha_dict) # type: ignore
    
    def new_io_mengshousha(self):
        # 每次查询修改前重新实例化防止内存和实际数据不一致
        self.sp = IOMengShousha()
    
    def get_rooms(self) -> Dict:
        self.new_io_mengshousha()
        mss:dict = self.sp.get("mengshousha") # type: ignore        
        return mss["rooms"] # type: ignore
    def get_room(self, room_id: str) -> Dict:
        self.new_io_mengshousha()
        mss:dict = self.sp.get("mengshousha") # type: ignore        
        return mss["rooms"][room_id] # type: ignore
    def update_room(self, room_id: str, room_info: dict) -> Dict:
        """更新房间信息"""
        self.new_io_mengshousha()
        mss:dict = self.sp.get("mengshousha") # type: ignore
        mss["rooms"][room_id] = room_info
        self.sp.put("mengshousha", mss) 
        return mss["rooms"][room_id]
    def get_player_room_unique(self) -> Dict:
        self.new_io_mengshousha()
        mss:dict = self.sp.get("mengshousha") # type: ignore    
        return mss["player_room_unique"] # type: ignore
    def update_player_room_unique(self, player_id: str, room_id: str|None) -> Dict|None:
        """更新玩家房间唯一信息"""
        self.new_io_mengshousha()
        mss:dict = self.sp.get("mengshousha") # type: ignore
        mss["player_room_unique"][player_id] = room_id
        self.sp.put("mengshousha", mss) # type: ignore
    
    def get_game_scenes(self) -> Dict:
        self.new_io_mengshousha()
        mss:dict = self.sp.get("mengshousha") # type: ignore
        return mss["game_scenes"] # type: ignore
    def get_game_scene(self, scene_id) -> Dict:
        self.new_io_mengshousha()
        mss:dict = self.sp.get("mengshousha") # type: ignore
        return mss["game_scenes"][scene_id] # type: ignore
    def update_game_scene(self, scene_id: str, scene_info: dict):
        """更新游戏场景信息"""
        self.new_io_mengshousha()
        mss:dict = self.sp.get("mengshousha") # type: ignore
        mss["game_scenes"][scene_id] = scene_info
        self.sp.put("mengshousha", mss)
    
    def get_game_maps(self) -> Dict:
        self.new_io_mengshousha()
        mss:dict = self.sp.get("mengshousha") # type: ignore
        return mss["game_maps"] # type: ignore
    
    def get_game_map(self, map_id) -> Dict:
        self.new_io_mengshousha()
        mss:dict = self.sp.get("mengshousha") # type: ignore
        return mss["game_maps"][map_id] # type: ignore
    
    def update_game_map(self, map_id: str, map_info: dict):
        """更新游戏地图信息"""
        self.new_io_mengshousha()
        mss:dict = self.sp.get("mengshousha") # type: ignore
        mss["game_maps"][map_id] = map_info
        self.sp.put("mengshousha", mss)
    
    def get_used_ids(self) -> List:
        self.new_io_mengshousha()
        mss:dict = self.sp.get("mengshousha") # type: ignore
        return mss["used_ids"] # type: ignore
    
    def generate_6digit_id(self) -> str:
        """生成6位数字ID"""
        self.new_io_mengshousha()
        used_ids = self.get_used_ids()
        while True:
            id = str(secrets.randbelow(1000000)).zfill(6)
            if id not in used_ids:
                used_ids.append(id)
                mss:dict = self.sp.get("mengshousha") # type: ignore
                mss["used_ids"] = used_ids # type: ignore
                self.sp.put("mengshousha", mss) # type: ignore
                return id
            raise RuntimeError("ID生成失败,请稍后重试")