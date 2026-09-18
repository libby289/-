# -*- coding: utf-8 -*-
"""
Agent 层（纯真实 LLM 模式，对接智谱 GLM，走 Anthropic 兼容接口）
用户自然语言 -> 智谱 GLM 理解意图并 Function Calling -> 调用 tools.py 里的工具 -> 返回结果

运行（无需每次设环境变量，配置写在 .env 里）：
    直接双击 run.bat，或命令行：python dorm_agent.py
"""
import os
import re
import time
from typing import List

import anthropic
from dotenv import load_dotenv

import tools
from tools import TOOL_FUNCS, TOOL_SCHEMAS

load_dotenv()  # 从 .env 一次性读取 API key / base_url / model


# ---------------- 工具描述：OpenAI 格式 -> Anthropic 格式 ----------------
def to_anthropic_tools(schemas):
    out = []
    for s in schemas:
        f = s["function"]
        out.append({
            "name": f["name"],
            "description": f["description"],
            "input_schema": f.get("parameters", {"type": "object", "properties": {}}),
        })
    return out


ANTHROPIC_TOOLS = to_anthropic_tools(TOOL_SCHEMAS)


# ---------------- 系统设定 + 欢迎语 ----------------
# 模型自己不知道运行中的具体型号/厂商，把 .env 里的配置写进设定，它才能准确自报家门
_CURRENT_MODEL = os.getenv("LLM_MODEL", "GLM-4.6V-Flash")

# 根据接口地址自动识别厂商（换 .env 的 BASE_URL 后身份自动跟着变）
_BASE_URL = os.getenv("LLM_BASE_URL", "")
if "deepseek" in _BASE_URL:
    _VENDOR = "DeepSeek（深度求索）"
elif "bigmodel" in _BASE_URL or "zhipu" in _BASE_URL:
    _VENDOR = "智谱AI"
elif "dashscope" in _BASE_URL or "aliyun" in _BASE_URL:
    _VENDOR = "阿里云通义千问"
else:
    _VENDOR = os.getenv("LLM_VENDOR", "智谱AI")   # 识别不出时可在 .env 里配 LLM_VENDOR

SYSTEM_PROMPT = (
    "你是一个高校宿舍管理系统的智能助手，可以通过自然语言帮用户查询宿舍、"
    "列出宿舍号清单、办理学生入住/退房、修改信息、查看整栋楼概况。"
    "请用简洁的中文回答。不要在回答中输出 <think> 思考过程。\n"
    "重要：只有当用户明确要查询或操作宿舍数据时，才调用工具函数。"
    "对于自我介绍、问候、闲聊（如'你是谁''你好''吃饭了吗'），"
    "不要调用任何工具，直接用文字回答。\n"
    f"关于你的身份：你由{_VENDOR}研发，底层模型是{_CURRENT_MODEL}。"
    "当用户问你是谁/什么模型/具体哪款/是不是某个版本时，"
    f"都明确回答你是{_CURRENT_MODEL}（{_VENDOR}研发），"
    "不要含糊，也不要说成其他公司的模型。"
)

WELCOME = """====================================================
        宿舍管理智能助手（大模型驱动）
====================================================
我可以帮你做这些事：
  - 查询宿舍：按宿舍号 / 学生姓名 / 学号查学生信息
  - 列出宿舍：全部 / 已入住 / 空房 清单
  - 办理入住 / 退房 / 调房 / 修改学生信息
  - 查看整栋楼概况统计
  - 闲聊问答（试试问我“你是谁”）
----------------------------------------------------
直接输入自然语言即可，输入 exit / 退出 结束。
"""


def strip_think(text: str) -> str:
    """GLM 有时会把思考过程以 <think>...</think> 混在正文里输出，过滤掉。"""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()


def call_tool(name: str, args: dict) -> str:
    """真正执行底层工具函数，返回结果文本。"""
    func = TOOL_FUNCS.get(name)
    if not func:
        return f"工具 {name} 不存在"
    try:
        return func(**args)
    except Exception as e:
        return f"执行出错：{e}"


class GLMAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL", "https://open.bigmodel.cn/api/anthropic"),
        )
        self.model = os.getenv("LLM_MODEL", "glm-4.6v-flash")
        self.history: List[dict] = []   # 多轮对话记忆

    def _create(self):
        return self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=self.history,      # ★带回完整历史，模型才有上下文
            tools=ANTHROPIC_TOOLS,
        )

    def _create_with_retry(self):
        """智谱服务端偶发 529 过载 / 500 内部错误，自动等待重试，界面显示'正在思考中'。"""
        for attempt in range(5):
            try:
                return self._create()
            except anthropic.APIError as e:   # APIError 是所有服务端错误的基类（529/500/502...）
                if attempt < 4:
                    print("（正在思考中...）")
                    time.sleep(2 * (attempt + 1))
                else:
                    print(f"（服务端连续异常：{type(e).__name__}，已重试4次）")
        return None

    def chat(self, user_input: str) -> str:
        """一轮对话：把用户输入记入历史，处理可能的多步工具调用，返回最终文本。"""
        self.history.append({"role": "user", "content": user_input})

        # 工具调用可能是多步的（如“把张三从101调到105”=退房+入住），
        # 用一个循环直到模型给出纯文本的最终回答。
        while True:
            resp = self._create_with_retry()
            if resp is None:
                self.history.pop()      # 回滚本条输入，避免脏历史
                return "模型当前繁忙，请稍后重试。"

            # 记录模型这条消息（可能同时含文本和 tool_use）
            self.history.append({"role": "assistant", "content": resp.content})

            tool_uses = [b for b in resp.content if b.type == "tool_use"]
            text_parts = [b.text for b in resp.content if b.type == "text"]

            if not tool_uses:
                return strip_think("".join(text_parts)) or "（无内容）"

            # 执行工具，把结果作为 tool_result 回传模型，让它继续生成
            results = []
            for tu in tool_uses:
                args = tu.input if isinstance(tu.input, dict) else {}
                results.append({
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": call_tool(tu.name, args),
                })
            self.history.append({"role": "user", "content": results})


def main():
    if not os.getenv("LLM_API_KEY"):
        print("未读取到 LLM_API_KEY。请在 .env 文件里配置，或临时用环境变量设置。")
        return
    agent = GLMAgent()
    print(WELCOME)
    while True:
        try:
            q = input("你：")
        except (EOFError, KeyboardInterrupt):
            break
        if q.strip().lower() in ("exit", "quit", "退出"):
            break
        print("助手：" + agent.chat(q) + "\n")


if __name__ == "__main__":
    main()
