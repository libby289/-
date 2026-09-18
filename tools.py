# -*- coding: utf-8 -*-
"""
工具层：把宿舍管理系统的增删改查封装成 Agent 可调用的"工具函数"。
每个工具都有清晰的中文 docstring —— 这些 docstring 会作为 LLM Function Calling
的 tool 描述，告诉大模型"这个工具做什么、需要哪些参数"。
"""
from typing import List, Dict, Any
from dorm_data import Dormitory, Student

# 全局宿舍楼实例（Agent 全程操作同一份数据）
dorm = Dormitory()


def query_by_room(room_id: str) -> str:
    """按宿舍号查询该宿舍的全部学生信息。参数 room_id 如 '101'。"""
    return dorm.query_by_room(room_id)


def query_by_name(name: str) -> str:
    """按学生姓名（支持模糊匹配）查询该学生所在宿舍信息。参数 name 为学生姓名。"""
    return dorm.query_by_name(name)


def query_by_id(studentid: str) -> str:
    """按学号（支持模糊匹配）查询学生所在宿舍信息。参数 studentid 为学号。"""
    return dorm.query_by_id(studentid)


def check_in(room_id: str, name: str, studentid: str = "", age: str = "",
            gender: str = "", address: str = "", phonenumber: str = "", QQid: str = "") -> str:
    """为学生办理入住。必填宿舍号与姓名，其余信息缺省时填“未填”。"""
    stu = Student(name, studentid, age, gender, address, phonenumber, QQid)
    return dorm.check_in(room_id, stu)


def check_out(room_id: str, name: str) -> str:
    """为学生办理退房（从指定宿舍移除该学生）。参数 room_id 宿舍号，name 学生姓名。"""
    return dorm.check_out(room_id, name)


def modify(room_id: str, name: str, field: str, value: str) -> str:
    """修改指定宿舍中某学生的某项信息。field 可选：姓名/学号/年龄/性别/家庭住址/电话/QQ。"""
    return dorm.modify(room_id, name, field, value)


def stats() -> str:
    """查询宿舍楼整体概况：总房间数、已入住/空房数量、总入住学生人数、满租率。"""
    return dorm.stats()


def list_rooms(status: str = "全部") -> str:
    """列出宿舍号清单。status 可选：全部 / 已入住 / 空房。"""
    status = (status or "全部").strip()
    picked = []
    for rid in sorted(dorm.rooms.keys()):
        room = dorm.rooms[rid]
        if status.startswith("已入住") and room.stunumbers == 0:
            continue
        if status.startswith("空") and room.stunumbers > 0:
            continue
        picked.append(f"{rid}({room.stunumbers}人)" if room.stunumbers else rid)
    if not picked:
        return "没有符合条件的宿舍。"
    name = "已入住宿舍" if status.startswith("已入住") else ("空宿舍" if status.startswith("空") else "全部宿舍")
    return f"{name}共 {len(picked)} 间：\n" + "  ".join(picked)


# 工具名 -> 函数 的映射，Agent 拿到工具名后调用对应函数
TOOL_FUNCS = {
    "query_by_room": query_by_room,
    "query_by_name": query_by_name,
    "query_by_id": query_by_id,
    "check_in": check_in,
    "check_out": check_out,
    "modify": modify,
    "stats": stats,
    "list_rooms": list_rooms,
}

# 给 LLM 的 Function Calling 工具描述（OpenAI / 通义千问 / DeepSeek 兼容格式）
TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {"type": "function", "function": {
        "name": "query_by_room", "description": "按宿舍号查询宿舍全部学生信息",
        "parameters": {"type": "object", "properties": {
            "room_id": {"type": "string", "description": "宿舍号，如 101"}}, "required": ["room_id"]}}},
    {"type": "function", "function": {
        "name": "query_by_name", "description": "按学生姓名模糊查询所在宿舍",
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string", "description": "学生姓名"}}, "required": ["name"]}}},
    {"type": "function", "function": {
        "name": "query_by_id", "description": "按学号模糊查询所在宿舍",
        "parameters": {"type": "object", "properties": {
            "studentid": {"type": "string", "description": "学号"}}, "required": ["studentid"]}}},
    {"type": "function", "function": {
        "name": "check_in", "description": "为学生办理入住，必填宿舍号与姓名，其余信息可省略",
        "parameters": {"type": "object", "properties": {
            "room_id": {"type": "string", "description": "宿舍号"},
            "name": {"type": "string", "description": "学生姓名"},
            "studentid": {"type": "string", "description": "学号（可省略）"},
            "age": {"type": "string", "description": "年龄（可省略）"},
            "gender": {"type": "string", "description": "性别（可省略）"},
            "address": {"type": "string", "description": "家庭住址（可省略）"},
            "phonenumber": {"type": "string", "description": "电话（可省略）"},
            "QQid": {"type": "string", "description": "QQ（可省略）"}},
            "required": ["room_id", "name"]}}},
    {"type": "function", "function": {
        "name": "check_out", "description": "为学生办理退房",
        "parameters": {"type": "object", "properties": {
            "room_id": {"type": "string", "description": "宿舍号"},
            "name": {"type": "string", "description": "学生姓名"}}, "required": ["room_id", "name"]}}},
    {"type": "function", "function": {
        "name": "modify", "description": "修改学生某项信息",
        "parameters": {"type": "object", "properties": {
            "room_id": {"type": "string"}, "name": {"type": "string"},
            "field": {"type": "string", "description": "姓名/学号/年龄/性别/家庭住址/电话/QQ"},
            "value": {"type": "string", "description": "新值"}}, "required": ["room_id", "name", "field", "value"]}}},
    {"type": "function", "function": {
        "name": "stats", "description": "查询宿舍楼整体概况统计",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "list_rooms", "description": "列出宿舍号清单，可按入住状态筛选",
        "parameters": {"type": "object", "properties": {
            "status": {"type": "string", "description": "筛选条件：全部 / 已入住 / 空房，默认全部"}}}}},
]
