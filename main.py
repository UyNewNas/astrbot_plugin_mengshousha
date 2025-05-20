'''
Author: slava
Date: 2025-05-20 16:04:32
LastEditTime: 2025-05-20 17:09:05
LastEditors: ch4nslava@gmail.com
Description: 

'''
import re
import secrets
import logging
import time
from typing import Dict, List, Optional, Set, Tuple

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger


# 配置日志
logger = logging.getLogger("MengShouSha")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
    
class GroupMember:
    """群成员数据类"""
    def __init__(self, data: dict):
        self.user_id: str = str(data["user_id"])
        self.nickname: str = data["nickname"]
        self.card: str = data["card"]

    @property
    def display_info(self) -> str:
        """带QQ号的显示信息"""
        return f"{self.card or self.nickname}({self.user_id})"
@register("mengshousha", "UyNewNas", "猛兽杀插件", "v0.1","https://github.com/UyNewNas/astrbot_plugin_mengshousha")
class MengShouShaPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self.rooms = {}
        self.used_ids = set()
        self.ROOM_MIN_NUM = 8
        self.ROOM_MAX_NUM = 12
    
    def _generate_6digit_id(self) -> str:
        """生成6位唯一数字ID(含重试机制)"""
        for _ in range(10):  # 最多重试10次
            code = str(secrets.randbelow(900000) + 100000)  # 生成100000-999999[8](@ref)
            if code not in self.used_ids:
                self.used_ids.add(code)
                return code
        raise RuntimeError("ID生成失败,请稍后重试")
    def _parse_display_info(self, raw_info: str) -> Tuple[str, str]:
        try:
            if '(' in raw_info and raw_info.endswith(')'):
                name_part, qq_part = raw_info.rsplit('(', 1)
                return name_part.strip(), qq_part[:-1]
            if '(' not in raw_info:
                return raw_info, "未知QQ号"
            parts = raw_info.split('(')
            if len(parts) >= 2:
                return parts[0].strip(), parts[-1].replace(')', '')
            return raw_info, "解析失败"
        except Exception as e:
            print(f"解析display_info失败：{raw_info} | 错误：{str(e)}")
            return raw_info, "解析异常"

    def _format_display_info(self, raw_info: str) -> str:
        nickname, qq = self._parse_display_info(raw_info)
        max_len = self.config.get("display_name_max_length", 10)
        safe_nickname = nickname.replace("\n", "").replace("\r", "").strip()
        formatted_nickname = safe_nickname[:max_len] + "……" if len(safe_nickname) > max_len else safe_nickname
        return f"{formatted_nickname}({qq})"
    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        pass
    
    # 注册指令的装饰器。指令名为 helloworld。注册成功后，发送 `/helloworld` 就会触发这个指令，并回复 `你好, {user_name}!`
    @filter.command_group("猛")
    async def meng(self, event: AstrMessageEvent):
        """这是一个猛兽杀指令""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        pass
    
    @meng.command("创建房间")
    async def create_room(self, event: AstrMessageEvent):
        """处理创建房间指令"""
        try:
            room_id = self._generate_6digit_id()
            new_room = {
                "id": room_id,
                "players": [{event.get_sender_id(),event.get_sender_name()}],
                "owner": event.get_sender_id(),
                "status": "等待中",
                "create_time": time.time()
            }
            self.rooms[room_id] = new_room
            #  组装房间信息 编号+昵称+QQ号
            room_info = "\n".join([f"{i+1}. {self._format_display_info(player_info)}" for i, player_info in enumerate(new_room["players"])])
            
            reply = f"🎮 房间创建成功！\n房间号：{room_id}\n加入指令：/猛 加入房间 {room_id}"
            yield event.plain_result(reply)
        except Exception as e:
            yield event.plain_result(f"❌ 创建失败：{str(e)}")

    
    @meng.command("加入房间")
    async def join_room(self, event: AstrMessageEvent, room_id:str):
        """处理加入房间指令"""
        try:
            # 检查房间是否存在
            if room_id not in self.rooms:
                yield event.plain_result("❌ 房间不存在，请检查房间号。")
                return

            room = self.rooms[room_id]
            player_id = event.get_sender_id()
            
            # 检查玩家是否已经在房间里
            if player_id in room["players"]:
                yield event.plain_result("❌ 你已经在这个房间里了。")
                return
            
            # 检查房间是否已满
            if len(room["players"]) >= self.ROOM_MAX_NUM:
                yield event.plain_result("❌ 房间已满，无法加入。")
                return            

            # 将玩家加入房间
            room["players"].append(player_id)
            cur_room_count = len(room["players"])
            
            #  组装房间信息 编号+昵称+QQ号
            room_info = "\n".join([f"{i+1}. {self._format_display_info(player_info)}" for i, player_info in enumerate(room["players"])])
            # 检查房间是否已满
            if  cur_room_count == self.ROOM_MAX_NUM:
                yield event.plain_result(f"🎉 成功加入房间 {room_id}！\n🚀 当前房间人数:{cur_room_count}, 当前房间信息:\n{room_info}\n房间已满, 开始游戏指令: 输入/猛 开始游戏 {room_id}")
            elif cur_room_count >= self.ROOM_MIN_NUM:
                yield event.plain_result(f"🎉 成功加入房间 {room_id}！\n🚀 当前房间人数:{cur_room_count}, 当前房间信息:\n{room_info}\n开始游戏指令: 输入/猛 开始游戏 {room_id}")
            else:
                yield event.plain_result(f"🎉 成功加入房间 {room_id}！\n🚀 当前房间人数:{cur_room_count}, 当前房间信息:\n{room_info}\n未满足最低要求人数8, 往里进往里进！")
        except Exception as e:
            yield event.plain_result(f"❌ 加入失败：{str(e)}")
    
    @meng.command("开始游戏")
    async def start_game(self, event: AstrMessageEvent, room_id:str):
        """处理开始游戏指令"""
        try:
            # 校验房间是否存在
            if room_id not in self.rooms:
                yield event.plain_result("❌ 房间不存在，请检查房间号。")
                return

            room = self.rooms[room_id]
            
            # 验证房主身份
            if event.get_sender_id() != room['owner']:
                yield event.plain_result("❌ 只有房主可以开始游戏。")
                return
            
            # 检查房间状态
            if room["status"] != "等待中":
                yield event.plain_result(f"❌ 房间当前状态[{room['status']}]不允许开始游戏")
                return

            # 检查最低人数要求
            if len(room["players"]) < self.ROOM_MIN_NUM:
                yield event.plain_result(f"❌ 当前房间人数不足（{len(room['players'])}/{self.ROOM_MIN_NUM}），无法开始游戏")
                return

            # 此处添加游戏开始逻辑
            room["status"] = "进行中"
            yield event.plain_result("🎮 游戏开始！正在分配角色...")
            
            # TODO: 后续添加具体的游戏逻辑

        except Exception as e:
            logger.error(f"开始游戏异常: {str(e)}", exc_info=True)
            yield event.plain_result(f"❌ 开始游戏失败：{str(e)}")
    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""