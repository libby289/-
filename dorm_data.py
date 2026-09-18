
"""
文件格式（与原 C++ 兼容）：
    房间行：<room_id> <stunumbers>
    学生行：<name> <studentid> <age> <gender> <address> <phonenumber> <QQ>
    空房间：<room_id> 0
"""

from dataclasses import dataclass, field
#from typing import List, Optional

N = 210          # 宿舍楼总房间数
M = 6            # 每间宿舍最多人数
DATA_FILE = "data.txt"


@dataclass
class Student:
    """单个学生"""
    name: str = ""
    studentid: str = ""
    age: str = ""
    gender: str = ""
    address: str = ""
    phonenumber: str = ""
    QQid: str = ""

    def show(self) -> str:
        return (f"姓名：{self.name} 学号：{self.studentid} 年龄：{self.age} "
                f"性别：{self.gender} 家庭住址：{self.address} "
                f"电话：{self.phonenumber} QQ：{self.QQid}")

    def to_line(self) -> str:
        return " ".join([self.name, self.studentid, self.age, self.gender,
                         self.address, self.phonenumber, self.QQid])



class Dormroom:
    """一间宿舍"""
    def __init__(self, roomid: str = '', students: list = None):
        self.roomid = roomid
        self.students = students if students is not None else []

    @property
    def stunumbers(self) -> int:
        return len(self.students)   # 每次现算，入住/退房后自动跟着变

    def show(self) -> str:
        lines = [f"宿舍号：{self.roomid} 人数：{self.stunumbers}"]
        for s in self.students:
            lines.append("  " + s.show())
        return "\n".join(lines)


class Dormitory:
    """一栋宿舍楼（对应原 C++ 的 Dormitory 类），用字典做 O(1) 查找。"""

    def __init__(self, data_file: str = DATA_FILE):
        self.data_file = data_file 
        self.rooms: dict[str, Dormroom] = {}
        self.n = 0  # 已入住房间数
        self.init()

    # ---------- 数据读取（对应原 C++ init()）----------
    def init(self):
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                lines = [ln.strip() for ln in f if ln.strip()]
        except FileNotFoundError:
            # 没有数据文件时初始化 210 个空房间，保证系统可运行
            for i in range(1, N + 1):
                self.rooms[f"{i:03d}"] = Dormroom(roomid=f"{i:03d}")
            return

        idx = 0
        while idx < len(lines):
            parts = lines[idx].split()
            if len(parts) < 2:
                idx += 1
                continue
            room_id, cnt = parts[0], int(parts[1])
            room = Dormroom(roomid=room_id)
            for _ in range(cnt):
                idx += 1
                sp = lines[idx].split()
                if len(sp) >= 7:
                    room.students.append(Student(*sp[:7]))
            self.rooms[room_id] = room
            idx += 1
        # 注意：不再“补齐”未出现的房间号——数据文件本身就是完整房间清单，
        # 强行补齐会把 001-210 等不存在的房间混入，导致统计与列表数量对不上。
        self.n = sum(1 for r in self.rooms.values() if r.stunumbers > 0)

    # ---------- 数据持久化（对应原 C++ update()）----------
    def save(self):
        with open(self.data_file, "w", encoding="utf-8") as f:
            for rid in sorted(self.rooms.keys()):
                room = self.rooms[rid]
                f.write(f"{rid} {room.stunumbers}\n")
                for s in room.students:
                    f.write(s.to_line() + "\n")
                f.write("\n")

    # ---------- 查询（对应原 C++ function1，字典 O(1)）----------
    def query_by_room(self, room_id: str) -> str:
        room = self.rooms.get(room_id)
        if not room:
            return f"未找到宿舍 {room_id}"
        if room.stunumbers == 0:
            return f"宿舍 {room_id} 目前为空房"
        return room.show()

    def query_by_name(self, name: str) -> str:
        hits = []
        for room in self.rooms.values():
            for s in room.students:
                if name in s.name:
                    hits.append(f"宿舍 {room.roomid} | {s.show()}")
        if not hits:
            return f"未找到姓名包含「{name}」的学生"
        return "\n".join(hits)

    def query_by_id(self, studentid: str) -> str:
        for room in self.rooms.values():
            for s in room.students:
                if studentid in s.studentid:
                    return f"宿舍 {room.roomid} | {s.show()}"
        return f"未找到学号包含「{studentid}」的学生"

    # ---------- 入住（对应原 C++ function4）----------
    def check_in(self, room_id: str, student: Student) -> str:
        room = self.rooms.get(room_id)
        if not room:
            return f"未找到宿舍 {room_id}"
        if room.stunumbers >= M:
            return f"宿舍 {room_id} 已满（{M}人），无法入住"
        room.students.append(student)
        self.n = sum(1 for r in self.rooms.values() if r.stunumbers > 0)
        self.save()
        return f"入住成功！{student.name} 已入住 {room_id}（现 {room.stunumbers} 人）"

    # ---------- 退房（对应原 C++ function5）----------
    def check_out(self, room_id: str, name: str) -> str:
        room = self.rooms.get(room_id)
        if not room or room.stunumbers == 0:
            return f"宿舍 {room_id} 为空或不存在"
        for i, s in enumerate(room.students):
            if s.name == name:
                removed = room.students.pop(i)
                self.n = sum(1 for r in self.rooms.values() if r.stunumbers > 0)
                self.save()
                return f"退房成功！{removed.name} 已离开 {room_id}（现 {room.stunumbers} 人）"
        return f"在 {room_id} 未找到名为「{name}」的学生"

    # ---------- 修改（对应原 C++ function2）----------
    def modify(self, room_id: str, name: str, field: str, value: str) -> str:
        field_map = {
            "姓名": "name", "学号": "studentid", "年龄": "age", "性别": "gender",
            "家庭住址": "address", "电话": "phonenumber", "QQ": "QQid",
        }
        attr = field_map.get(field, field)
        room = self.rooms.get(room_id)
        if not room:
            return f"未找到宿舍 {room_id}"
        for s in room.students:
            if s.name == name:
                setattr(s, attr, value)
                self.save()
                return f"修改成功！{name} 的{field}已更新为 {value}"
        return f"在 {room_id} 未找到名为「{name}」的学生"

    # ---------- 统计（对应原 C++ function3）----------
    def stats(self) -> str:
        total = len(self.rooms)            # 真实房间数，避免写死 N 与数据不符
        total_students = sum(r.stunumbers for r in self.rooms.values())
        occupied = sum(1 for r in self.rooms.values() if r.stunumbers > 0)
        empty = total - occupied
        rate = occupied / total * 100 if total else 0
        return (f"宿舍楼概况：总房间数 {total}，已入住 {occupied} 间，空房 {empty} 间；"
                f"总入住学生 {total_students} 人，平均满租率 {rate:.1f}%")


if __name__ == "__main__":
    d = Dormitory()
    print(d.stats())
    print(d.query_by_room("101"))
