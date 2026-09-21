import os
import json
import subprocess
from pathlib import Path
from openai import OpenAI


# =====================================================
# 1. 基础配置
# =====================================================

API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL = os.getenv("LLM_MODEL")

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

WORKDIR = (Path(__file__).resolve().parent / "sandbox").resolve()
WORKDIR.mkdir(exist_ok=True)


# =====================================================
# 2. 路径安全
# =====================================================

def safe_path(path: str) -> Path:
    target = (WORKDIR / path).resolve()

    if not target.is_relative_to(WORKDIR):
        raise PermissionError("禁止访问 sandbox 外的文件")

    return target


# =====================================================
# 3. Tool Implementation
# =====================================================

def run_command(command: str) -> str:
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        cwd=WORKDIR,
        capture_output=True,
        text=True,
        timeout=30
    )

    output = result.stdout

    if result.stderr:
        output += "\n错误信息：\n" + result.stderr

    return output


def read_file(path: str) -> str:
    return safe_path(path).read_text(encoding="utf-8")


def write_file(path: str, content: str) -> str:
    target = safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    return f"文件 {path} 写入成功"


# =====================================================
# 4. Tool Registry
# =====================================================

REGISTRY = {
    "run_command": {
        "handler": run_command,
        "permission": "ask",
        "schema": {
            "type": "function",
            "name": "run_command",
            "description": "在当前工作目录中执行 PowerShell 命令",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "需要执行的 PowerShell 命令"
                    }
                },
                "required": ["command"],
                "additionalProperties": False
            },
            "strict": True
        }
    },

    "read_file": {
        "handler": read_file,
        "permission": "allow",
        "schema": {
            "type": "function",
            "name": "read_file",
            "description": "读取 sandbox 中的文本文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "需要读取的文件路径"
                    }
                },
                "required": ["path"],
                "additionalProperties": False
            },
            "strict": True
        }
    },

    "write_file": {
        "handler": write_file,
        "permission": "ask",
        "schema": {
            "type": "function",
            "name": "write_file",
            "description": "在 sandbox 中创建或覆盖文本文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "需要写入的文件路径"
                    },
                    "content": {
                        "type": "string",
                        "description": "需要写入的完整内容"
                    }
                },
                "required": ["path", "content"],
                "additionalProperties": False
            },
            "strict": True
        }
    }
}


TOOLS = [tool["schema"] for tool in REGISTRY.values()]



# =====================================================
# HOOKS
# =====================================================

HOOKS = {
    "PreToolUse":[],
    "PostToolUse":[]
}

def register_hook(event_name:str,hook_func):
    if event_name not in HOOKS:
        raise ValueError(f"未知Hook事件：{event_name}")

    HOOKS[event_name].append(hook_func)

def run_HOOKS(event_name:str,**context):
    for hook_func in HOOKS[event_name]:
        hook_func(**context)

def log_pre_tool(tool_name:str,arguments:dict,**kwargs):

    print(f"\n[PreToolUse]准备调用工具：{tool_name}")
    print(f"参数：{arguments}")

def log_post_tool(tool_name:str,result:str,**kwargs):
    print(f"\n[PostToolUse]工具执行完成：{tool_name}")
    print(f"结果：{result}")

register_hook("PreToolUse",log_pre_tool)
register_hook("PostToolUse",log_post_tool)

# =====================================================
# 5. Permission + Tool Execution
# =====================================================

def check_permission(name: str, arguments: dict) -> bool:
    permission = REGISTRY[name]["permission"]

    if permission == "allow":
        return True

    if permission == "deny":
        return False

    print(f"\nAgent 想调用工具：{name}")
    print(f"参数：{arguments}")

    confirm = input("允许执行吗？(y/n)：")
    return confirm.lower() == "y"


def execute_tool(name: str, arguments: dict) -> str:
    tool = REGISTRY.get(name)

    if tool is None:
        return f"未知工具：{name}"

    run_HOOKS("PreToolUse",tool_name = name,arguments = arguments)

    if not check_permission(name, arguments):
        return f"工具 {name} 未执行，因为权限未通过"

    try:
        return tool["handler"](**arguments)
    except Exception as e:
        return f"工具 {name} 执行失败：{e}"

    run_HOOKS(
        "PostToolUse",
        tool_name = name,
        arguments = arguments,
        result = result

    )

    return result


# =====================================================
# 6. Agent Loop
# =====================================================

def agent_loop(query: str, max_steps: int = 10):
    messages = [{"role": "user", "content": query}]

    for _ in range(max_steps):
        response = client.responses.create(model=MODEL, tools=TOOLS, input=messages)

        messages += response.output
        tool_called = False

        for item in response.output:
            if item.type != "function_call":
                continue

            tool_called = True

            arguments = json.loads(item.arguments)
            result = execute_tool(item.name, arguments)

            messages.append({
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": result
            })

        if not tool_called:
            print("\nAgent:")
            print(response.output_text)
            return

    print("\n达到最大执行步数，Agent 已停止。")


# =====================================================
# 7. 用户入口
# =====================================================

query = input("你：")
agent_loop(query)