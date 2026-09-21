import os
import json
import subprocess
from pathlib import Path
from openai import OpenAI

# 1. 基础配置与沙箱路径（严格防穿越）
WORKDIR = Path(__file__).resolve().parent / "sandbox"
WORKDIR.mkdir(exist_ok=True)

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL")
)
MODEL = os.getenv("LLM_MODEL")

def safe_path(relative_path: str) -> Path:
    """统一路径解析并防止目录穿越 (Path Traversal)"""
    target = (WORKDIR / relative_path).resolve()
    if not str(target).startswith(str(WORKDIR)):
        raise PermissionError("禁止访问沙箱外的目录路径！")
    return target

# 2. 工具集中注册（消除割裂感，统一管理实现与权限）
REGISTRY = {}

def register_tool(name: str, desc: str, params: dict, permission="ask"):
    def decorator(fn):
        REGISTRY[name] = {
            "handler": fn,
            "permission": permission,
            "schema": {
                "type": "function",
                "function": {
                    "name": name,
                    "description": desc,
                    "parameters": params
                }
            }
        }
        return fn
    return decorator

@register_tool("run_command", "在沙箱执行命令", {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}, permission="ask")
def run_command(command: str) -> str:
    try:
        res = subprocess.run(["powershell", "-NoProfile", "-Command", command], cwd=WORKDIR, capture_output=True, text=True, timeout=15)
        return res.stdout + (f"\nSTDERR:\n{res.stderr}" if res.stderr else "")
    except Exception as e:
        return f"执行失败: {e}"

@register_tool("read_file", "读取沙箱文件", {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}, permission="allow")
def read_file(path: str) -> str:
    try:
        return safe_path(path).read_text(encoding="utf-8")
    except Exception as e:
        return f"读取失败: {e}"

@register_tool("write_file", "写入文件", {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}, permission="ask")
def write_file(path: str, content: str) -> str:
    try:
        p = safe_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"文件 {path} 写入成功"
    except Exception as e:
        return f"写入失败: {e}"

# 3. 权限判断与执行闭环
def execute_tool(name: str, args: dict) -> str:
    tool_meta = REGISTRY.get(name)
    if not tool_meta:
        return f"错误：未知工具 {name}"

    # 权限拦截
    if tool_meta["permission"] == "ask":
        print(f"\n[确认请求] 工具: {name}\n参数: {args}")
        if input("允许运行吗？(y/n): ").strip().lower() != "y":
            return f"用户已拒绝执行工具 {name}。"

    return tool_meta["handler"](**args)

# 4. Agent 主循环（标准 OpenAI API 格式，带步数限制）
def agent_loop(query: str, max_steps: int = 10):
    messages = [{"role": "user", "content": query}]
    tools_schema = [t["schema"] for t in REGISTRY.values()]

    for _ in range(max_steps):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools_schema
        )
        msg = response.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            print(f"\nAgent:\n{msg.content}")
            return

        for tool_call in msg.tool_calls:
            fn_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            output = execute_tool(fn_name, args)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": output
            })
    print("\n达到最大执行步数限制，退出循环。")