'''
Author: slava
Date: 2025-05-29 15:25:23
LastEditTime: 2025-06-03 10:45:47
LastEditors: ch4nslava@gmail.com
Description: 

'''
import time
from .sp_mengshousha import DataMengShouSha
spm = DataMengShouSha()

class GameRoom():
    
    def __init__(self):
        pass
    
    def create_new_room(self, owner_id:str,owner_name:str):
        room_id = spm.generate_6digit_id()
        new_room = {
            "room_id": room_id,
            "player_ids":[owner_id],
            "player_infos": [f"{owner_name}({owner_id})"],
            "players_in_game": {owner_id:{"player_index":0,"player_name":owner_name}}, # "player_id": {"player_name": "player_name"}
            "owner": owner_id,
            "status": "等待中",
            "create_time": time.time()
        }
        spm.update_room(room_id, new_room)
        return "等待中",room_id,new_room
    
    def check_room_exist(self, room_id:str):
        rooms = spm.get_rooms()
        if room_id in rooms:
            return True
        return False
    
    def get_room(self, room_id:str):
        return spm.get_room(room_id)
    
    def dismiss_room(self, room_id:str):
        rooms = spm.get_rooms()
        if room_id in rooms:
            del rooms[room_id]
            spm.update_room(room_id, rooms)
            return True
        return False
    
    def join_room(self, room_id:str, player_id:str, player_name:str):
        room = self.get_room(room_id)
        player_ids = room["player_ids"]
        if player_id in player_ids:
            return False
        player_ids.append(player_id)
        room["player_infos"].append(f"{player_name}({player_id})")
        room["players_in_game"][player_id] = {"player_index":player_ids.index(player_id),"player_name": player_name}
        spm.update_room(room_id, room)
        
    def exit_room(self, room_id:str, player_id:str, player_name:str):
        room = self.get_room(room_id)
        if player_id not in room["player_ids"]:
            return False
        room["player_ids"].remove(player_id)
        room["player_infos"].remove(f"{player_name}({player_id})")
        del room["players_in_game"][player_id]
        spm.update_room(room_id, room)
        
    def room_game_start(self, room_id:str):
        room = self.get_room(room_id)
        room["status"] = "游戏中"
        spm.update_room(room_id, room)
        
    def room_game_start_fail(self, room_id:str):
        room = self.get_room(room_id)
        room["status"] = "等待中"
        spm.update_room(room_id, room)
    
    def get_player_room_unique(self, player_id:str):
        player_room_unique = spm.get_player_room_unique()
        if player_id in player_room_unique:
            return player_room_unique[player_id]
        return None
    
    def update_player_room_unique(self, player_id:str, room_id:str|None):
        player_room_unique = spm.get_player_room_unique()
        player_room_unique[player_id] = room_id
        spm.update_player_room_unique(player_id, room_id)
        return player_room_unique[player_id]
    
    def get_players_in_game(self, room_id:str):
        room = self.get_room(room_id)
        return room["players_in_game"]
    
    