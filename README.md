# 项目五：基于大模型 Agent 的智能宿舍管理系统

## 项目背景
前身是本人大一《C 程序设计课程设计》的「11 号宿舍楼管理系统」：用 C++ 面向对象
（Student / Dormroom / Dormitory 三个类）实现了查询、修改、入住、退房、统计，数据
持久化到 `data.txt`。原系统有两个明显限制：①只能菜单式输入编号操作；②TXT 不支持
中文（当时用英文绕开）。

本项目用 **Python + 大模型 Agent** 对其进行智能化重构：用户不再输入菜单编号，而是用
**自然语言**下指令（"查一下 101 宿舍谁住""让李四入住 105"），由大模型做意图识别与
参数抽取，通过 **Function Calling（工具调用）** 调用底层增删改查工具，返回结果。

## 技术栈
- Python 3.9+
- 大模型接入：Anthropic 兼容 SDK（`anthropic`），可对接 DeepSeek / 智谱 GLM / 通义千问等
- Function Calling（工具调用）
- 自研数据层（字典索引，查询 O(1)，原生中文）

## 目录结构
```
dorm_data.py      数据层：Student/Dormroom/Dormitory + 文件持久化（中文原生支持）
tools.py          工具层：8 个可调用工具 + 给 LLM 的 Function Calling schema
dorm_agent.py     Agent 层：自然语言解析 -> 工具调用 -> 结果返回（多轮对话 + 多步工具调用）
gen_sample_data.py 生成示例 data.txt（210 间宿舍，前 28 间入住学生）
data.txt          宿舍数据（由脚本生成，已 .gitignore）
.env / .env.example 配置（API key / base_url / model，.env 不入库）
run.bat           一键启动（Windows 双击即可）
requirements.txt  依赖
```

## 运行
```bash
pip install -r requirements.txt

# 复制配置模板并填入你自己的 key
cp .env.example .env        # 编辑 .env：LLM_API_KEY / LLM_BASE_URL / LLM_MODEL

# 运行（双击 run.bat 或）
python dorm_agent.py
```
配置写在 `.env`，无需每次设环境变量。模型厂商/型号由 `.env` 驱动，换供应商零代码改动。

## 核心设计
1. **数据层重构**：原 C++ 用 `Student a[M]` / `Dormroom a[N]` 数组 + 遍历查找；
   Python 版用 `dict[room_id -> Dormroom]` + `list[Student]`，查询从 O(N*M) 降到 O(1)，
   并原生支持中文（解决原系统 TXT 中文乱码）；人数用 `@property` 现算，避免缓存过期。
2. **工具化（Tool Calling）**：把"查询/入住/退房/修改/统计/列清单"封装成 8 个带中文
   docstring 的函数，docstring 同时作为 LLM Function Calling 的 `description`，让模型知道
   何时调、怎么调；必填/可选参数在 schema 中标明，提升工具选择准确率。
3. **Agent 编排**：自然语言 -> 大模型解析意图与槽位 -> 调用对应工具 -> 回写结果。
   支持多步组合指令（如"把张三从 101 调到 105"可拆为退房+入住两步循环执行）、
   多轮对话记忆（历史随请求回传，上下文连贯）。
4. **稳健性**：服务端偶发 529/500 自动重试并提示"正在思考中"；模型身份（厂商/型号）
   从配置动态注入 system prompt，避免串台。

## 亮点（可用于简历/面试）
- 从"菜单式系统"升级为"对话式系统"，操作效率显著提升
- 完整走通 LLM 应用开发的典型链路：意图理解 -> 工具定义 -> 函数调用 -> 结果回写
- 解决了原课程设计的中文兼容性限制，并把数组遍历优化为字典索引
- 配置驱动（模型/厂商可切换）、数据层与 Agent 层解耦，扩展新功能只需新增一个工具函数
