# -*- coding: utf-8 -*-
"""生成示例 data.txt：210 间宿舍（11号宿舍楼），前若干间入住学生，其余空房。"""
import random

N = 210
M = 6
random.seed(2023213903)  # 固定种子，保证可复现

surnames = "王李张刘陈杨黄赵周吴徐孙马朱胡郭何高林罗郑梁谢宋唐许"
given = ["伟", "芳", "娜", "敏", "静", "强", "磊", "军", "洋", "勇",
         "艳", "杰", "娟", "涛", "明", "超", "霞", "平", "刚", "桂英"]
cities = ["安徽合肥", "山东济南", "河南郑州", "江苏南京", "浙江杭州", "湖北武汉"]
genders = ["男", "女"]


def make_student(rid: str, i: int) -> str:
    name = random.choice(surnames) + random.choice(given)
    sid = f"2023{rid}{i:02d}"          # 学号示例
    age = str(random.randint(18, 22))
    gender = random.choice(genders)
    addr = random.choice(cities)
    phone = f"1{random.randint(3,9)}{random.randint(10**8, 10**9-1)}"
    qq = str(random.randint(10**8, 10**9))
    return f"{name} {sid} {age} {gender} {addr} {phone} {qq}"


with open("data.txt", "w", encoding="utf-8") as f:
    for n in range(1, N + 1):
        # 真实宿舍编号：楼层(1-7) + 房号(01-30)，如 101、205、730
        floor = (n - 1) // 30 + 1
        roomnum = (n - 1) % 30 + 1
        rid = f"{floor}{roomnum:02d}"
        if n <= 28:                      # 前 28 间（101-128）入住 4~6 人
            cnt = random.randint(4, M)
            f.write(f"{rid} {cnt}\n")
            for i in range(cnt):
                f.write(make_student(rid, i + 1) + "\n")
        else:                           # 其余空房
            f.write(f"{rid} 0\n")
        f.write("\n")

print("已生成 data.txt：210 间宿舍，前 28 间入住学生。")
