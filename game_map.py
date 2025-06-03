from .sp_mengshousha import DataMengShouSha

spm = DataMengShouSha()


def GameMapNode(
    NodeCode: int,
    NodeName: str,
    NextNodeList: list,
    # **kwargs
):
    NodeCode = NodeCode
    NodeName = NodeName
    NextNodeList = NextNodeList
    return {
        "NodeCode": NodeCode,
        "NodeName": NodeName,
        "NextNodeList": NextNodeList,
        # **kwargs
    }


MAP_NODES = [
    GameMapNode(0, "会议室", [1, 3]),
    GameMapNode(1, "会议室北面走廊", [0, 2, 4, 5, 18]),
    GameMapNode(2, "会议室东面走廊", [0, 1, 3, 24]),
    GameMapNode(3, "会议室南面走廊", [0, 2, 4, 12]),
    GameMapNode(4, "会议室西面走廊", [0, 1, 3, 16]),
    GameMapNode(5, "医疗舱西侧长条走廊", [1, 6, 19]),
    GameMapNode(6, "医疗舱", [5, 7]),
    GameMapNode(7, "供氧舱", [6, 8]),
    GameMapNode(8, "电力舱北侧走廊", [7, 9, 21]),
    GameMapNode(9, "电力舱", [8, 22]),
    GameMapNode(10, "电力舱南侧走廊", [9, 11, 23]),
    GameMapNode(11, "广播站北侧走廊", [10, 12, 25]),
    GameMapNode(12, "广播站西侧长条走廊", [3, 11, 13]),
    GameMapNode(13, "制氧舱南侧走廊", [12, 14, 27]),
    GameMapNode(14, "制氧舱", [13, 15]),
    GameMapNode(15, "下引擎室", [14, 16]),
    GameMapNode(16, "禁闭室", [4, 15, 17]),
    GameMapNode(17, "上引擎室", [16, 18]),
    GameMapNode(18, "温控舱", [1, 17, 19]),
    GameMapNode(19, "温控舱北侧走廊", [5, 18, 20]),
    GameMapNode(20, "左上炮塔", [19]),
    GameMapNode(21, "右上炮塔", [8]),
    GameMapNode(22, "驾驶室", [9]),
    GameMapNode(23, "右下炮塔", [10]),
    GameMapNode(24, "左下炮塔", [2]),
    GameMapNode(99, "停尸房", []),
]


class GameMap:
    def __init__(self):
        pass

    def create_new_map(self, room_id: str, player_ids: list):
        map_id = spm.generate_6digit_id()

        new_game_map = {
            "map_id": map_id,
            "room_id": room_id,
            "player_ids": player_ids,
            "map_nodes": MAP_NODES.copy(),
            "players_in_map_info": {
                player_id: {"node_code": 0, "node_name": "会议室"}
                for player_id in player_ids
            },
            "players_in_map_info_history": {
                player_id: [{"node_code": 0, "node_name": "会议室"}]
                for player_id in player_ids
            },
        }
        spm.update_game_map(map_id, new_game_map)
        return map_id, new_game_map

    def get_map_from_room(self, room_id):
        game_maps = spm.get_game_maps()
        for map_id, game_map in game_maps.items():
            if game_map["room_id"] == room_id:
                return map_id, game_map
        return None, None

    def get_node(self, node_code_or_name: str):
        for node in MAP_NODES:
            if (
                node["NodeCode"] == node_code_or_name
                or node["NodeName"] == node_code_or_name
            ):
                return node["NodeCode"], node["NodeName"], node["NextNodeList"]
        raise ValueError(f"节点{node_code_or_name}不存在")

    @staticmethod
    def get_node_name(node_code: int):
        for node in MAP_NODES:
            if node["NodeCode"] == node_code:
                return node["NodeName"]
        raise ValueError(f"节点{node_code}不存在")

    def get_next_nodes(
        self, player_id: str, node_code_or_name: str, in_vent: bool = False
    ) -> list:
        room_id = spm.get_player_room_unique()[player_id]
        map_id, game_map = self.get_map_from_room(room_id)
        if map_id is None or game_map is None:
            raise ValueError(f"玩家{player_id}不在任何房间中,查询位置失败")
        if not in_vent:
            node_code, node_name, next_node_list = self.get_node(node_code_or_name)
            return next_node_list
        else:
            # TODO 处理管道移动逻辑
            return []

    def move_to_next_node(
        self, player_id: str, next_node_code: int, in_vent: bool = False
    ):
        room_id = spm.get_player_room_unique()[player_id]
        map_id, game_map = self.get_map_from_room(room_id)
        if map_id is None or game_map is None:
            raise ValueError(f"玩家{player_id}不在任何房间中,查询位置失败")
        if not in_vent:
            # 检查移动是否合法
            if next_node_code not in self.get_next_nodes(
                player_id, game_map["players_in_map_info"][player_id]["node_code"]
            ):
                raise ValueError(f"玩家{player_id}无法移动到节点{next_node_code}")
            for node in game_map["map_nodes"]:
                if node["NodeCode"] == next_node_code:
                    game_map["players_in_map_info"][player_id]["node_code"] = (
                        next_node_code
                    )
                    game_map["players_in_map_info"][player_id]["node_name"] = node[
                        "NodeName"
                    ]
                    game_map["players_in_map_info_history"][player_id].append(
                        {"node_code": next_node_code, "node_name": node["NodeName"]}
                    )
                    spm.update_game_map(map_id, game_map)
                    return True
        else:
            # TODO 处理管道移动逻辑
            pass
        return False

    def get_players_in_node(self, player_id: str, node_code: int):
        room_id = spm.get_player_room_unique()[player_id]
        map_id, game_map = self.get_map_from_room(room_id)
        if map_id is None or game_map is None:
            raise ValueError(f"玩家{player_id}不在任何房间中,查询位置失败")
        players_in_map_info = game_map["players_in_map_info"]
        players_in_node = []
        for _player_id, player_info in players_in_map_info.items():
            if player_info["node_code"] == node_code:
                # 处理隐身逻辑
                if "isVisible" in player_info and player_info["isVisible"] == 0:
                    continue
                #  玩家自己不包括
                if player_id == _player_id:
                    continue
                players_in_node.append(_player_id)
        return players_in_node

    def get_player_node_history(self, player_id: int):
        room_id = spm.get_player_room_unique()[player_id]
        map_id, game_map = self.get_map_from_room(room_id)
        if map_id is None or game_map is None:
            raise ValueError(f"玩家{player_id}不在任何房间中,查询位置失败")
        return "→".join(
            [
                node["NodeName"]
                for node in game_map["players_in_map_info_history"][player_id]
            ]
        )

    def get_map_nodes(self, player_id: str):
        room_id = spm.get_player_room_unique()[player_id]
        map_id, game_map = self.get_map_from_room(room_id)
        if map_id is None or game_map is None:
            raise ValueError(f"玩家{player_id}不在任何房间中,查询位置失败")
        return game_map["map_nodes"]

    # 强制移动玩家到指定节点
    def force_move_player_to_node(self, player_id: str, target_node_code: int):
        room_id = spm.get_player_room_unique()[player_id]
        map_id, game_map = self.get_map_from_room(room_id)
        if map_id is None or game_map is None:
            raise ValueError(f"玩家{player_id}不在任何房间中,查询位置失败")
        source_node_code = game_map["players_in_map_info"][player_id]["node_code"]
        if target_node_code not in MAP_NODES:
            raise ValueError(f"节点{target_node_code}不存在")
        for node in game_map["map_nodes"]:
            if node["NodeCode"] == target_node_code:
                game_map["players_in_map_info"][player_id]["node_code"] = (
                    target_node_code
                )
                game_map["players_in_map_info"][player_id]["node_name"] = node[
                    "NodeName"
                ]
                game_map["players_in_map_info_history"][player_id].append(
                    {"node_code": target_node_code, "node_name": node["NodeName"]}
                )
                return True
        return False
