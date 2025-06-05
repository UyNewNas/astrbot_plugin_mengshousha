"""
Author: slava
Date: 2025-05-29 15:20:09
LastEditTime: 2025-06-03 11:48:55
LastEditors: ch4nslava@gmail.com
Description:

"""

from typing import Dict, List, Optional, Set, Tuple

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from . import game_map, game_roles, game_room, game_scene


@register(
    "mengshousha",
    "UyNewNas",
    "猛兽杀插件",
    "v0.1",
    "https://github.com/UyNewNas/astrbot_plugin_mengshousha",
)
class MengShouShaPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self.used_ids = set()
        self.ROOM_MIN_NUM = self.config.get("ROOM_MIN_NUM", 8)
        self.ROOM_MAX_NUM = self.config.get("ROOM_MAX_NUM", 12)

    def _parse_display_info(self, raw_info: str) -> Tuple[str, str]:
        try:
            if "(" in raw_info and raw_info.endswith(")"):
                name_part, qq_part = raw_info.rsplit("(", 1)
                return name_part.strip(), qq_part[:-1]
            if "(" not in raw_info:
                return raw_info, "未知QQ号"
            parts = raw_info.split("(")
            if len(parts) >= 2:
                return parts[0].strip(), parts[-1].replace(")", "")
            return raw_info, "解析失败"
        except Exception as e:
            print(f"解析display_info失败：{raw_info} | 错误：{str(e)}")
            return raw_info, "解析异常"

    def _format_display_info(self, raw_info: str) -> str:
        nickname, qq = self._parse_display_info(raw_info)
        max_len = self.config.get("display_name_max_length", 10)
        safe_nickname = nickname.replace("\n", "").replace("\r", "").strip()
        formatted_nickname = (
            safe_nickname[:max_len] + "……"
            if len(safe_nickname) > max_len
            else safe_nickname
        )
        return f"{formatted_nickname}({qq})"

    @filter.command_group("猛")
    async def meng(self, event: AstrMessageEvent):
        """这是一个猛兽杀指令"""
        pass

    def _gen_room_info(self, room: dict) -> str:
        #  组装房间信息 编号+昵称+QQ号
        return "\n".join(
            [
                f"{i + 1}. {self._format_display_info(player_info)}"
                for i, player_info in enumerate(room["player_infos"])
            ]
        )

    """
    -------------------------------------------------------------------------------------------------------------------------------------
    房间指令集合
    -------------------------------------------------------------------------------------------------------------------------------------
    指令格式：/猛 创建房间 房间号
    指令格式：/猛 查看房间 房间号
    指令格式：/猛 解散房间 房间号
    指令格式：/猛 加入房间 房间号
    指令格式：/猛 退出房间 房间号
    指令格式：/猛 开始游戏 房间号
    -------------------------------------------------------------------------------------------------------------------------------------
    """

    # 在类内添加以下公共校验方法
    # 检查房间是否存在
    def _check_room_exist(self, event: AstrMessageEvent, room_id: str | None):
        if room_id is None:
            yield event.plain_result("❌ 你不在任何房间中。")
            return False
        gameroom = game_room.GameRoom()
        # 检查房间是否存在
        if not gameroom.check_room_exist(room_id):
            yield event.plain_result("❌ 房间不存在，请检查房间号。")
            return False
        return True

    # 检查玩家是否在房间里
    def _check_player_in_room(
        self, event: AstrMessageEvent, player_id: str, player_ids: List[str]
    ):
        if player_id not in player_ids:
            yield event.plain_result("❌ 你不在这个房间里。")
            return False
        return True

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    @meng.command("创建房间")  # type: ignore
    async def create_room(self, event: AstrMessageEvent):
        """处理创建房间指令"""
        try:
            player_id = event.get_sender_id()
            group_id = event.get_group_id()
            gameroom = game_room.GameRoom()
            room_status, room_id, room_dict = gameroom.create_new_room(
                player_id, event.get_sender_name(), group_id
            )
            room_info = self._gen_room_info(room_dict)
            # fix 房主没有加入唯一列表
            gameroom.update_player_room_unique(player_id, room_id)
            reply = f"🎮 房间创建成功！\n房间号：{room_id}\n当前房间状态:{room_status}\n当前房间信息:\n{room_info}\n加入指令：/猛 加入房间 {room_id}"
            yield event.plain_result(reply)
        except Exception as e:
            logger.error(f"创建房间异常: {str(e)}", exc_info=True)
            yield event.plain_result(f"❌ 创建失败，请联系管理员。")

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    @meng.command("查询房间", alias={"查看房间"})  # type: ignore
    async def view_room(self, event: AstrMessageEvent, room_id: str):
        """处理查询房间指令"""
        try:
            gameroom = game_room.GameRoom()
            if not self._check_room_exist(event, room_id) or room_id is None:
                return
            room = gameroom.get_room(room_id)
            room_status = room["status"]
            room_info = self._gen_room_info(room)
            reply = f"🎮 房间查询成功！\n房间号：{room_id}\n当前房间状态:{room_status}\n当前房间信息:\n{room_info}\n加入指令：/猛 加入房间 {room_id}"
            yield event.plain_result(reply)
        except Exception as e:
            logger.error(f"查看房间异常: {str(e)}", exc_info=True)
            yield event.plain_result(f"❌ 查看失败，请联系管理员。")

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    @meng.command("解散房间")  # type: ignore
    async def dismiss_room(self, event: AstrMessageEvent, room_id: str):
        """处理解散房间指令"""
        try:
            gameroom = game_room.GameRoom()
            if not self._check_room_exist(event, room_id) or room_id is None:
                return
            room = gameroom.get_room(room_id)
            player_id = event.get_sender_id()
            # 检查是否为房主
            if player_id != room["owner"]:
                yield event.plain_result("❌ 只有房主可以解散房间。")
                return
            # 解散房间
            gameroom.dismiss_room(room_id)
            yield event.plain_result(f"🎮 房间 {room_id} 已解散。")
        except Exception as e:
            logger.error(f"解散房间异常: {str(e)}", exc_info=True)
            yield event.plain_result(f"❌ 解散失败，请联系管理员。")

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    @meng.command("加入房间")  # type: ignore
    async def join_room(self, event: AstrMessageEvent, room_id: str):
        """处理加入房间指令"""
        try:
            gameroom = game_room.GameRoom()
            if not self._check_room_exist(event, room_id) or room_id is None:
                return
            room = gameroom.get_room(room_id)
            player_id = event.get_sender_id()
            player_name = event.get_sender_name()
            player_room_unique = gameroom.get_player_room_unique(player_id)

            # 检查玩家是否已经在房间里
            if player_id in room["player_ids"]:
                yield event.plain_result("❌ 你已经在这个房间里了。")
                return

            cur_room_count = len(room["player_ids"])
            # 检查房间是否已满
            if cur_room_count >= self.ROOM_MAX_NUM:
                yield event.plain_result("❌ 房间已满，无法加入。")
                return

            # 检查玩家是否已经在其他房间里
            if player_room_unique is not None:
                yield event.plain_result("❌ 你已经在其他房间里了。")
                return

            # 将玩家加入房间
            gameroom.join_room(room_id, player_id, player_name)
            gameroom.update_player_room_unique(player_id, room_id)
            room = gameroom.get_room(room_id)
            cur_room_count = len(room["player_ids"])

            #  组装房间信息 编号+昵称+QQ号
            room_status = room["status"]
            room_info = self._gen_room_info(room)

            # 检查加入后房间是否已满
            if cur_room_count == self.ROOM_MAX_NUM:
                yield event.plain_result(
                    f"🎉 成功加入房间 {room_id}！\n🚀 当前房间人数:{cur_room_count}\n当前房间状态:{room_status}\n当前房间信息:\n{room_info}\n房间已满({self.ROOM_MAX_NUM}), 开始游戏指令: 输入/猛 开始游戏 {room_id}"
                )
            elif cur_room_count >= self.ROOM_MIN_NUM:
                yield event.plain_result(
                    f"🎉 成功加入房间 {room_id}！\n🚀 当前房间人数:{cur_room_count}\n当前房间状态:{room_status}\n当前房间信息:\n{room_info}\n当前房间人数（{len(room['player_ids'])}/{self.ROOM_MIN_NUM}）可以开始游戏,\n开始游戏指令: 输入/猛 开始游戏 {room_id}"
                )
            else:
                yield event.plain_result(
                    f"🎉 成功加入房间 {room_id}！\n🚀 当前房间人数:{cur_room_count}\n当前房间状态:{room_status}\n当前房间信息:\n{room_info}\n当前房间人数不足（{len(room['player_ids'])}/{self.ROOM_MIN_NUM}）\n\n 往里进往里进！"
                )
        except Exception as e:
            logger.error(f"加入房间异常: {str(e)}", exc_info=True)
            yield event.plain_result(f"❌ 加入失败，请联系管理员。")

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    @meng.command("退出房间")  # type: ignore
    async def quit_room(self, event: AstrMessageEvent, room_id: str):
        """处理退出房间指令"""
        try:
            gameroom = game_room.GameRoom()
            if not self._check_room_exist(event, room_id) or room_id is None:
                return
            room = gameroom.get_room(room_id)
            player_id = event.get_sender_id()
            player_name = event.get_sender_name()
            player_room_unique = gameroom.get_player_room_unique(player_id)
            # 检查是否为房主
            if player_id == room["owner"]:
                yield event.plain_result(
                    "❌ 房主无法退出房间。请用解散指令解散房间：/猛 解散房间 {room_id}"
                )
                return
            player_ids = room["player_ids"]
            if not self._check_player_in_room(event, player_id, player_ids):
                return
            # 移除玩家
            gameroom.exit_room(room_id, player_id, player_name)
            gameroom.update_player_room_unique(player_id, None)
            # 组装房间信息 编号+昵称+QQ号
            room = gameroom.get_room(room_id)
            cur_room_count = len(room["player_ids"])
            room_status = room["status"]
            room_info = self._gen_room_info(room)
            yield event.plain_result(
                f"🎉 成功退出房间 {room_id}！\n当前房间人数:{cur_room_count}\n当前房间状态:{room_status}\n当前房间信息:\n{room_info}\n"
            )
        except Exception as e:
            logger.error(f"退出房间异常: {str(e)}", exc_info=True)
            yield event.plain_result(f"❌ 退出失败，请联系管理员。")

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    @meng.command("开始游戏")  # type: ignore
    async def start_game(self, event: AstrMessageEvent, room_id: str):
        """处理开始游戏指令"""
        try:
            gameroom = game_room.GameRoom()
            if not self._check_room_exist(event, room_id) or room_id is None:
                return
            room = gameroom.get_room(room_id)
            # 验证房主身份
            if event.get_sender_id() != room["owner"]:
                yield event.plain_result("❌ 只有房主可以开始游戏。")
                return
            # 检查房间状态
            if room["status"] != "等待中":
                yield event.plain_result(
                    f"❌ 房间当前状态[{room['status']}]不允许开始游戏"
                )
                return
            # 检查最低人数要求
            if len(room["player_ids"]) < self.ROOM_MIN_NUM:
                yield event.plain_result(
                    f"❌ 当前房间人数不足（{len(room['player_ids'])}/{self.ROOM_MIN_NUM}），无法开始游戏"
                )
                return
            # 开始游戏
            gameroom.room_game_start(room_id)
            player_ids = room["player_ids"]
            player_infos = room["player_infos"]
            logger.info(f"房间{room_id}{room['player_infos']}开始游戏")
            yield event.plain_result("🎮 游戏开始！正在分配角色，请稍候...")
            gamescene = game_scene.GameScene()

            status, scene_id, scene = gamescene.create_new_scene(room_id, player_ids)
            status, role_info = gamescene.assign_role(scene_id)
            role_code_list = [role_code for role_code in role_info.values()]
            role_code_list.sort()
            role_list = [
                game_roles.GameRoleConstDict[game_roles.GameRoleEnum(role_code).name]
                for role_code in role_code_list
            ]
            role_list = ",".join(role_list)
            yield event.plain_result(
                f"✅ 角色分配完成！游戏已知的角色列表有:\n{role_list}\n请私聊bot查询身份\n指令: /猛 查询身份"
            )

            # 初始化地图信息
            gamemap = game_map.GameMap()
            map_id, map = gamemap.create_new_map(room_id, player_ids)
            yield event.plain_result(
                f"✅ 地图初始化完成！已将所有玩家放置在会议室。\n请私聊bot查询位置\n指令: /猛 查询位置"
            )
        except Exception as e:
            logger.error(f"开始游戏异常: {str(e)}", exc_info=True)
            # 状态回滚
            gameroom = game_room.GameRoom()
            gameroom.room_game_start_fail(room_id)
            yield event.plain_result(f"❌ 开始游戏失败，请联系管理员。")

    """
        私聊指令集合
        指令格式：/猛 查询身份
        指令格式：/猛 查询位置
        会议下指令格式：/猛 移动 位置
        会议下指令格式：/猛 铲除 位置
        会议下指令格式：/猛 吞噬 位置
        会议下指令格式：/猛 感染 位置
    """

    # 开始游戏后的公共校验方法
    def _game_not_start(self, event: AstrMessageEvent):
        yield event.plain_result("❌ 游戏未开始，请联系房主开始游戏。")
        return

    @filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
    @meng.command("查询身份")  # type: ignore
    async def query_role(self, event: AstrMessageEvent):
        """处理查询身份指令"""
        try:
            gameroom = game_room.GameRoom()
            player_id = event.get_sender_id()
            player_name = event.get_sender_name()
            room_id = gameroom.get_player_room_unique(player_id)
            if not self._check_room_exist(event, room_id) or room_id is None:
                return
            # 检查玩家是否在房间里
            room = gameroom.get_room(room_id)
            player_ids = room["player_ids"]
            if not self._check_player_in_room(event, player_id, player_ids):
                return
            # 反查玩家在房间的编号
            player_index = player_ids.index(player_id)
            # 查询身份
            gamescene = game_scene.GameScene()
            scene_id, scene = gamescene.get_scene_from_room(room_id)
            if scene_id is None or scene is None:
                self._game_not_start(event)
                return
            # 检查游戏是否开始
            if scene["status"] != "游戏中":
                yield event.plain_result(
                    f"❌ 房间当前状态[{room['status']}]不允许查询身份"
                )
                return
            role_info = scene["role_info"]
            player_role_code = role_info[player_id]
            player_role = game_roles.GameRoleEnum(player_role_code).name
            player_role_cn_name = game_roles.GameRoleConstDict[player_role]
            yield event.plain_result(
                f"🎮 房间{room_id}身份查询成功\n{player_index + 1}号玩家{player_name}({player_id})的身份是：\n{player_role_cn_name}"
            )
        except Exception as e:
            logger.error(f"查询身份异常: {str(e)}", exc_info=True)
            yield event.plain_result(f"❌ 查询身份失败，请联系管理员。")

    @filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
    @meng.command("查询位置")  # type: ignore
    async def query_position(self, event: AstrMessageEvent):
        """处理查询位置指令"""
        try:
            gameroom = game_room.GameRoom()
            player_id = event.get_sender_id()
            player_name = event.get_sender_name()
            room_id = gameroom.get_player_room_unique(player_id)
            if not self._check_room_exist(event, room_id) or room_id is None:
                return
            # 检查玩家是否在房间里
            room = gameroom.get_room(room_id)
            player_ids = room["player_ids"]
            if not self._check_player_in_room(event, player_id, player_ids):
                return
            gamescene = game_scene.GameScene()
            scene_id, scene = gamescene.get_scene_from_room(room_id)
            if scene_id is None or scene is None:
                self._game_not_start(event)
                return
            dead_info = scene["dead_info"]
            # 查询位置
            gamemap = game_map.GameMap()
            map_id, map = gamemap.get_map_from_room(room_id)
            if map_id is None or map is None:
                self._game_not_start(event)
                return
            now_node_code, now_node_name = (
                map["players_in_map_info"][player_id]["node_code"],
                map["players_in_map_info"][player_id]["node_name"],
            )
            # 查询可移动的位置
            next_nodes = gamemap.get_next_nodes(player_id, now_node_code)
            eg_first_node_code = next_nodes[0]
            eg_first_node_name = gamemap.get_node_name(eg_first_node_code)
            next_nodes = [
                f"{node_code}:{gamemap.get_node_name(node_code)}"
                for node_code in next_nodes
            ]
            next_nodes_format = ",\n".join(next_nodes)
            # 查询当前位置有哪些玩家
            others_in_node = gamemap.get_players_in_node(player_id, now_node_code)
            players_in_node = []
            players_in_game = gameroom.get_players_in_game(room_id)
            players_in_game_list = list(players_in_game)
            for other_id_in_node in others_in_node:
                if other_id_in_node in players_in_game_list:
                    player_name_in_node = players_in_game[other_id_in_node][
                        "player_name"
                    ]
                    # 判断是否是尸体
                    if other_id_in_node in dead_info:
                        player_name_in_node = f"{player_name_in_node}（已死亡）"
                    player_index = players_in_game[other_id_in_node]["player_index"]
                    players_in_node.append(
                        f"{player_index + 1}.{player_name_in_node}({other_id_in_node})"
                    )
            players_in_node = "\n".join(players_in_node)
            player_index = players_in_game[player_id]["player_index"]
            plaint_texts = [
                f"🎮 玩家位置查询成功\n{player_index + 1}号玩家{player_name}({player_id})当前位置是：\n{now_node_code}.{now_node_name}",
                f"您当前可移动的位置有：\n{next_nodes_format}\n如需移动角色请输入移动指令:\n/猛 移动 位置数字编号 或 /猛 移动 位置名称",
                f"例如：\n/猛 移动 {eg_first_node_code} 或 /猛 移动 {eg_first_node_name}",
                f"当前位置有以下玩家：\n{players_in_node}"
                if players_in_node
                else "当前位置没有看到其他玩家。",
                f"如果您的身份可以使用技能或者您看到当前位置有玩具死去，请输入以下指令：",
                f"/猛 报警 X（死去的玩家在房间里的编号）",
                f"/猛 铲除 X（想铲除的玩家在房间里的编号）",
            ]
            yield event.plain_result("\n".join(plaint_texts))
        except Exception as e:
            logger.error(f"查询位置异常: {str(e)}", exc_info=True)
            yield event.plain_result("❌ 查询位置失败，请联系管理员。")

    """
        玩家会议下的技能指令
        PLAYER SKILLS UNDER MEETING
        0. 移动（任何不在死亡列表和被吃列表的玩家）
        1. 铲除（带刀角色）
        2. 吞噬（食肉动物）
        3. 感染（哈卡）
        4. 变脸（变脸杀手）
        5. 隐身（隐身杀手）
        6. 检查（花生侠）
        7. 报警（任何人接触到尸体、刀到尖叫）
        8. 进管道（工程侠、普通杀手）
        9. 出管道（工程侠、普通杀手）
        10. 静音（不打算做）
    """
    # 公共方法

    def _check_room_status(
        self, event: AstrMessageEvent, check_status: str, expected_status: str
    ):
        if check_status != expected_status:
            yield event.plain_result(f"❌ 房间当前状态[{check_status}]不允许使用技能")
            return False
        return True

    def _check_target_in_room(
        self,
        event: AstrMessageEvent,
        target_player_id: str,
        target_player_infos,
        player_ids: List[str],
    ):
        if target_player_id not in player_ids:
            yield event.plain_result(
                f"❌ 目标玩家{target_player_infos}不在这个房间里。"
            )
            return False
        return True

    def _check_target_is_source(
        self, event: AstrMessageEvent, source_player_id: str, target_player_id: str
    ):
        if source_player_id == target_player_id:
            yield event.plain_result("❌ 你不能对自己使用技能。")
            return True
        return False

    def _check_scene_status(
        self, event: AstrMessageEvent, scene: dict, expected_status: str
    ):
        if scene["status"] != expected_status:
            yield event.plain_result(
                f"❌ 游戏当前状态[{scene['status']}]不允许使用技能"
            )
            return False

    def _check_player_is_dead(
        self, event: AstrMessageEvent, player_id: str, dead_info: List[str],
        is_move: bool
    ):
        if player_id in dead_info:
            if is_move:
                yield event.plain_result("❌ 你已经死亡，无法移动。")
            else:
                yield event.plain_result("❌ 你已经死亡，无法使用技能。")
            return True
        return False
    def _check_player_is_ate(
        self, event: AstrMessageEvent, player_id: str, ate_info: List[str],
        is_move: bool
    ):
        if player_id in ate_info:
            if is_move:
                yield event.plain_result("❌ 你已经被吃，无法移动。")
            else:
                yield event.plain_result("❌ 你已经被吃，无法使用技能。")
            return True
    @filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
    @meng.command("移动")  # type: ignore
    async def move(self, event: AstrMessageEvent, node_code_or_name: str):
        """处理移动指令"""
        try:
            gameroom = game_room.GameRoom()
            player_id = event.get_sender_id()
            player_name = event.get_sender_name()
            room_id = gameroom.get_player_room_unique(player_id)
            if not self._check_room_exist(event, room_id) or room_id is None:
                return
            # 检查玩家是否在房间里
            room = gameroom.get_room(room_id)
            player_ids = room["player_ids"]
            if not self._check_player_in_room(event, player_id, player_ids):
                return
            # 检查游戏是否开始
            if room["status"] != "游戏中":
                yield event.plain_result(f"❌ 房间当前状态[{room['status']}]不允许移动")
                return
            # 检查玩家是否存活
            gamescene = game_scene.GameScene()
            scene_id, scene = gamescene.get_scene_from_room(room_id)
            if scene_id is None or scene is None:
                self._game_not_start(event)
                return
            dead_info = scene["dead_info"]
            ate_info = scene["ate_info"]
            # TODO目前先不开发死后支持继续移动做任务功能
            if self._check_player_is_dead(event, player_id, dead_info, True): return
            if self._check_player_is_ate(event, player_id, ate_info, True): return
            gamemap = game_map.GameMap()
            # 获得玩家当前的node
            map_id, map = gamemap.get_map_from_room(room_id)
            if map_id is None or map is None:
                self._game_not_start(event)
                return
            now_node_code, now_node_name = (
                map["players_in_map_info"][player_id]["node_code"],
                map["players_in_map_info"][player_id]["node_name"],
            )
            # 获得玩家可移动的位置
            next_nodes = gamemap.get_next_nodes(player_id, now_node_code)
            # 检查输入的位置是否合法
            target_node_code, target_node_name, target_next = gamemap.get_node(
                node_code_or_name
            )
            if target_node_code not in next_nodes:
                yield event.plain_result(
                    f"❌ 您当前位置{now_node_name}({now_node_code})无法移动到{target_node_name}({target_node_code})"
                )
                return
            # 移动玩家
            if gamemap.move_to_next_node(player_id, target_node_code):
                yield event.plain_result(
                    f"🎮 移动成功\n{player_name}({player_id})移动到了{target_node_name}({target_node_code})"
                )
            else:
                yield event.plain_result(
                    f"❌ 移动失败\n{player_name}({player_id})的当前位置{now_node_name}({now_node_code})"
                )

        except Exception as e:
            logger.error(f"移动异常: {str(e)}", exc_info=True)
            yield event.plain_result("❌ 移动失败，请联系管理员。")

    @filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
    @meng.command("铲除")  # type: ignore
    async def kill(self, event: AstrMessageEvent, target_player_index: str):
        """处理技能指令"""
        try:
            gameroom = game_room.GameRoom()
            source_player_id = event.get_sender_id()
            room_id = gameroom.get_player_room_unique(source_player_id)
            if not self._check_room_exist(event, room_id) or room_id is None:
                return
            room = gameroom.get_room(room_id)
            player_ids = room["player_ids"]
            target_player_id = player_ids[int(target_player_index) - 1]
            target_player_infos = room["player_infos"][int(target_player_index) - 1]
            if not self._check_player_in_room(event, source_player_id, player_ids):
                return
            # 检查游戏是否开始
            if not self._check_room_status(event, room["status"], "游戏中"):
                return
            # 检查玩家是否存活或者是否被吃
            gamescene = game_scene.GameScene()
            scene_id, scene = gamescene.get_scene_from_room(room["room_id"])
            if scene_id is None or scene is None:
                self._game_not_start(event)
                return
            if not self._check_scene_status(event, scene, "会议下"):
                return
            dead_info = scene["dead_info"]
            ate_info = scene["ate_info"]
            # TODO目前先不开发死后支持继续移动做任务功能
            if self._check_player_is_dead(event, source_player_id, dead_info, False): return
            if self._check_player_is_ate(event, source_player_id, ate_info, False): return
            # 检查玩家是否有这个技能
            role_info = scene["role_info"]
            player_role_code = role_info[source_player_id]
            # 是否是食肉动物
            if player_role_code == game_roles.GameRoleEnum.CARNIVORE.value:
                yield event.plain_result(
                    "❌ 食肉动物无法使用此技能，请使用吞噬技能，指令：/猛 吞噬 玩家编号"
                )
                return
            # 中立刀优先判断，其实就是死神
            if player_role_code in game_roles.GameRoleEnum.NEUTRALMAN_CAN_V.value:
                can_kill = True
            # 是否是好人刀 TODO 单刀只能出一次刀,出完不能再出,复仇只能在目击过同一房间里发生铲除事件时才能使用铲除技能
            # 但是复仇技能太难实现了默认可以出刀
            elif player_role_code in game_roles.GameRoleEnum.GOODMAN_CAN_V.value:
                can_kill = True
            # 11到15是坏人
            elif player_role_code in game_roles.GameRoleEnum.BADMAN.value:
                can_kill = True
            else:
                can_kill = False
            if not can_kill:
                yield event.plain_result("❌ 你无法使用铲除技能")
                return

            #  检查是否是自己
            if self._check_target_is_source(event, source_player_id, target_player_id):
                return
            # 检查是否在同一个node里
            gamemap = game_map.GameMap()
            map_id, map = gamemap.get_map_from_room(room["room_id"])
            if map_id is None or map is None:
                self._game_not_start(event)
                return
            now_node_code, now_node_name = (
                map["players_in_map_info"][source_player_id]["node_code"],
                map["players_in_map_info"][source_player_id]["node_name"],
            )
            others_in_node = gamemap.get_players_in_node(
                source_player_id, now_node_code
            )
            if target_player_id not in others_in_node:
                yield event.plain_result(
                    f"❌ 目标玩家{target_player_infos}和您不在同一个位置, 铲除失败"
                )
                return

            # 检查目标玩家是否已经死亡或者被吃
            if target_player_id in dead_info:
                yield event.plain_result(
                    f"❌ 目标玩家{target_player_infos}已经死亡，无法使用技能。"
                )
                return
            if target_player_id in ate_info:
                yield event.plain_result(
                    f"❌ 目标玩家{target_player_infos}已经消失，无法使用技能。"
                )
                return

            # 检查目标玩家是否隐身
            players_in_map_info = map["players_in_map_info"]
            target_player_info = players_in_map_info[target_player_id]
            if (
                "isVisible" in target_player_info
                and target_player_info["isVisible"] == False
            ):
                yield event.plain_result(
                    f"❌ 目标玩家{target_player_infos}已经消失，无法使用技能。"
                )
                return

            # 击杀
            gamescene.player_to_dead(scene_id, source_player_id, target_player_id)
            yield event.plain_result(
                f"🔪 成功击杀{target_player_index}号玩家:{target_player_infos}"
            )
            # 保安的代价
            target_player_role_code = role_info[target_player_id]
            if player_role_code == game_roles.GameRoleEnum.GUARD.value:
                # 检查目标玩家是否是好人
                target_player_role_code = role_info[target_player_id]
                if target_player_role_code in game_roles.GameRoleEnum.GOODMAN.value:
                    gamescene.player_to_dead(
                        scene_id, source_player_id, source_player_id
                    )
                    yield event.plain_result("❌ 保安击杀了好人，您已自杀")
                    return
            # 食肉动物被击杀后释放被吃的玩家
            if target_player_role_code == game_roles.GameRoleEnum.CARNIVORE.value:
                # 将所有被吃的玩家释放到目标玩家位置
                for ate_player in ate_info:
                    ate_player_id = ate_player["target_player_id"]
                    gamemap.force_move_player_to_node(ate_player_id, now_node_code)
                # 清空被吃列表
                gamescene.clear_ate_info(scene_id)
            # 击杀尖叫
            elif target_player_role_code == game_roles.GameRoleEnum.SCREAM.value:
                gamescene.touch_body_alert(scene_id, source_player_id, target_player_id)

        except Exception as e:
            logger.error(f"铲除指令异常: {str(e)}", exc_info=True)
            yield event.plain_result("❌ 铲除指令失败，请联系管理员。")

    @filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
    @meng.command("吞噬", alias={"吃"})  # type: ignore
    async def eat(self, event: AstrMessageEvent, target_player_index: str):
        """处理食肉动物的吞噬技能指令"""
        try:
            gameroom = game_room.GameRoom()
            source_player_id = event.get_sender_id()
            room_id = gameroom.get_player_room_unique(source_player_id)
            if not self._check_room_exist(event, room_id) or room_id is None:
                return
            room = gameroom.get_room(room_id)
            player_ids = room["player_ids"]
            target_player_id = player_ids[int(target_player_index) - 1]
            target_player_infos = room["player_infos"][int(target_player_index) - 1]
            if not self._check_player_in_room(event, source_player_id, player_ids):
                return
            if not self._check_target_in_room(
                event, target_player_id, target_player_infos, player_ids
            ):
                return
            # 检查游戏是否开始
            if not self._check_room_status(event, room["status"], "游戏中"):
                return
            # 检查玩家是否存活或者是否被吃
            gamescene = game_scene.GameScene()
            scene_id, scene = gamescene.get_scene_from_room(room["room_id"])
            if scene_id is None or scene is None:
                self._game_not_start(event)
                return
            dead_info = scene["dead_info"]
            ate_info = scene["ate_info"]
            # TODO目前先不开发死后支持继续移动做任务功能
            if self._check_player_is_dead(event, source_player_id, dead_info, False): return
            if self._check_player_is_ate(event, source_player_id, ate_info, False): return
            # 检查玩家是否有这个技能
            role_info = scene["role_info"]
            player_role_code = role_info[source_player_id]
            # 是否是食肉动物
            if player_role_code != game_roles.GameRoleEnum.CARNIVORE.value:
                yield event.plain_result("❌ 只有食肉动物才能使用此技能!")
                return
            #  检查是否是自己
            if self._check_target_is_source(event, source_player_id, target_player_id):
                return
            # 检查是否在同一个node里
            gamemap = game_map.GameMap()
            map_id, map = gamemap.get_map_from_room(room["room_id"])
            if map_id is None or map is None:
                self._game_not_start(event)
                return
            now_node_code, now_node_name = (
                map["players_in_map_info"][source_player_id]["node_code"],
                map["players_in_map_info"][source_player_id]["node_name"],
            )
            others_in_node = gamemap.get_players_in_node(
                source_player_id, now_node_code
            )
            if target_player_id not in others_in_node:
                yield event.plain_result(
                    f"❌ 目标玩家{target_player_infos}和您不在同一个位置, 吞噬失败"
                )
                return

            # 检查目标玩家是否已经死亡或者被吃
            if target_player_id in dead_info:
                yield event.plain_result(
                    f"❌ 目标玩家{target_player_infos}已经死亡，无法使用技能。"
                )
                return
            if target_player_id in ate_info:
                yield event.plain_result(
                    f"❌ 目标玩家{target_player_infos}已经被您吞噬，请勿重复指令。"
                )
                return
            # 检查目标玩家是否隐身
            players_in_map_info = map["players_in_map_info"]
            target_player_info = players_in_map_info[target_player_id]
            if (
                "isVisible" in target_player_info
                and target_player_info["isVisible"] == False
            ):
                yield event.plain_result(
                    f"❌ 目标玩家{target_player_infos}已经消失，无法使用技能。"
                )
                return
            # 吞噬
            gamescene.player_to_ate(scene_id, source_player_id, target_player_id)
            yield event.plain_result(
                f"🍖 成功吞噬{target_player_index}号玩家:{target_player_infos}"
            )
            # 吞噬尖叫
            target_player_role_code = role_info[target_player_id]
            if target_player_role_code == game_roles.GameRoleEnum.SCREAM.value:
                gamescene.touch_body_alert(scene_id, source_player_id, target_player_id)
        except Exception as e:
            logger.error(f"吞噬指令异常: {str(e)}", exc_info=True)
            yield event.plain_result("❌ 吞噬指令失败，请联系管理员。")

    @filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
    @meng.command("感染", alias={"摸"})  # type: ignore
    async def infect(self, event: AstrMessageEvent, target_player_index: str):
        """处理哈卡的感染技能指令"""
        try:
            gameroom = game_room.GameRoom()
            source_player_id = event.get_sender_id()
            room_id = gameroom.get_player_room_unique(source_player_id)
            if not self._check_room_exist(event, room_id) or room_id is None:
                return
            room = gameroom.get_room(room_id)
            player_ids = room["player_ids"]
            target_player_id = player_ids[int(target_player_index) - 1]
            target_player_infos = room["player_infos"][int(target_player_index) - 1]
            if not self._check_player_in_room(event, source_player_id, player_ids):
                return
            if not self._check_target_in_room(
                event, target_player_id, target_player_infos, player_ids
            ):
                return
            # 检查游戏是否开始
            if not self._check_room_status(event, room["status"], "游戏中"):
                return
            # 检查玩家是否存活或者是否被吃
            gamescene = game_scene.GameScene()
            scene_id, scene = gamescene.get_scene_from_room(room["room_id"])
            if scene_id is None or scene is None:
                self._game_not_start(event)
                return
            dead_info = scene["dead_info"]
            ate_info = scene["ate_info"]
            infected_info = scene["infected_info"]
            # TODO目前先不开发死后支持继续移动做任务功能
            if self._check_player_is_dead(event, source_player_id, dead_info, False): return
            if self._check_player_is_ate(event, source_player_id, ate_info, False): return
            # 检查玩家是否有这个技能
            role_info = scene["role_info"]
            player_role_code = role_info[source_player_id]
            # 是否是哈卡
            if player_role_code != game_roles.GameRoleEnum.HAKA.value:
                yield event.plain_result("❌ 只有哈卡才能使用此技能!")
                return
            #  检查是否是自己
            if self._check_target_is_source(event, source_player_id, target_player_id):
                return
            # 检查是否在同一个node里
            gamemap = game_map.GameMap()
            map_id, map = gamemap.get_map_from_room(room["room_id"])
            if map_id is None or map is None:
                self._game_not_start(event)
                return
            now_node_code, now_node_name = (
                map["players_in_map_info"][source_player_id]["node_code"],
                map["players_in_map_info"][source_player_id]["node_name"],
            )
            others_in_node = gamemap.get_players_in_node(
                source_player_id, now_node_code
            )
            if target_player_id not in others_in_node:
                yield event.plain_result(
                    f"❌ 目标玩家{target_player_infos}和您不在同一个位置, 感染失败"
                )
                return

            # 检查目标玩家是否已经死亡或者被吃
            if target_player_id in dead_info:
                yield event.plain_result(
                    f"❌ 目标玩家{target_player_infos}已经死亡，无法使用技能。"
                )
                return
            if target_player_id in ate_info:
                yield event.plain_result(
                    f"❌ 目标玩家{target_player_infos}已经消失，无法使用技能。"
                )
                return
            if target_player_id in infected_info:
                yield event.plain_result(
                    f"❌ 目标玩家{target_player_infos}已经被感染，请勿重复指令。"
                )
                return
            # 检查目标玩家是否隐身
            players_in_map_info = map["players_in_map_info"]
            target_player_info = players_in_map_info[target_player_id]
            if (
                "isVisible" in target_player_info
                and target_player_info["isVisible"] == False
            ):
                yield event.plain_result(
                    f"❌ 目标玩家{target_player_infos}已经消失，无法使用技能。"
                )
                return
            # 感染
            gamescene.player_to_infected(scene_id, source_player_id, target_player_id)
            yield event.plain_result(
                f"🤒 成功感染{target_player_index}号玩家:{target_player_infos}"
            )
        except Exception as e:
            logger.error(f"感染指令异常: {str(e)}", exc_info=True)
            yield event.plain_result("❌ 感染指令失败，请联系管理员。")

    @filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
    @meng.command("变脸", alias={"变", "变身"})  # type: ignore
    async def change(self, event: AstrMessageEvent, target_player_index: str):
        """处理变脸杀手的变脸技能指令"""
        try:
            gameroom = game_room.GameRoom()
            source_player_id = event.get_sender_id()
            room_id = gameroom.get_player_room_unique(source_player_id)
            if not self._check_room_exist(event, room_id) or room_id is None:
                return
            room = gameroom.get_room(room_id)
            player_ids = room["player_ids"]
            target_player_id = player_ids[int(target_player_index) - 1]
            target_player_infos = room["player_infos"][int(target_player_index) - 1]
            if not self._check_player_in_room(event, source_player_id, player_ids):
                return
            if not self._check_target_in_room(
                event, target_player_id, target_player_infos, player_ids
            ):
                return
            # 检查游戏是否开始
            if not self._check_room_status(event, room["status"], "游戏中"):
                return
            # 检查玩家是否存活或者是否被吃
            gamescene = game_scene.GameScene()
            scene_id, scene = gamescene.get_scene_from_room(room["room_id"])
            if scene_id is None or scene is None:
                self._game_not_start(event)
                return
            dead_info = scene["dead_info"]
            ate_info = scene["ate_info"]
            # TODO目前先不开发死后支持继续移动做任务功能
            if self._check_player_is_dead(event, source_player_id, dead_info, False): return
            if self._check_player_is_ate(event, source_player_id, ate_info, False): return
            # 检查玩家是否有这个技能
            role_info = scene["role_info"]
            player_role_code = role_info[source_player_id]
            # 是否是变脸杀手
            if player_role_code!= game_roles.GameRoleEnum.VARIETY_KILLER.value:
                yield event.plain_result("❌ 只有变脸杀手才能使用此技能!")
                return
            #  检查是否是自己
            if self._check_target_is_source(event, source_player_id, target_player_id):
                return
            # 原版的变脸需要在身边才能采样变脸, 很不方便, 我决定去掉这个限制, 可以自由在会议下变脸成任何玩家
            # # 检查是否在同一个node里
            # gamemap = game_map.GameMap()
            # map_id, map = gamemap.get_map_from_room(room["room_id"])
            # if map_id is None or map is None:
            #     self._game_not_start(event)
            #     return
            # now_node_code, now_node_name = (
            #     map["players_in_map_info"][source_player_id]["node_code"], 
            #     map["players_in_map_info"][source_player_id]["node_name"],
            # )
            # others_in_node = gamemap.get_players_in_node(
            #     source_player_id, now_node_code 
            # )
            # if target_player_id not in others_in_node:
            #     yield event.plain_result(
            #         f"❌ 目标玩家{target_player_infos}和您不在同一个位置, 变脸失败"
            #     )
            #     return
            
            # 变脸成目标角色
            
            
        except Exception as e:
            logger.error(f"变脸指令异常: {str(e)}", exc_info=True)
            yield event.plain_result("❌ 变脸指令失败，请联系管理员。")

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
        # 猛兽杀数据的清理
        # sp.remove("mengshousha")
        pass
