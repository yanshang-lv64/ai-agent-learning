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

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

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

    target.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    target.write_text(
        content,
        encoding="utf-8"
    )

    return f"文件 {path} 写入成功"


# =====================================================
# 4. Todo / Planning State
# =====================================================

class TodoManager:
    def __init__(self):
        self.items = []

    def update(self, items: list) -> str:
        validated = []
        in_progress_count = 0

        for item in items:
            status = item.get("status", "pending")

            if status not in {
                "pending",
                "in_progress",
                "completed"
            }:
                raise ValueError(
                    f"未知 Todo 状态：{status}"
                )

            if status == "in_progress":
                in_progress_count += 1

            validated.append({
                "id": item["id"],
                "text": item["text"],
                "status": status
            })

        if in_progress_count > 1:
            raise ValueError(
                "同时只能有一个任务处于 in_progress 状态"
            )

        if validated == self.items:
            return (
                "Todo 未发生变化，"
                "请继续执行当前任务，"
                "不要重复提交相同 Todo。"
            )

        self.items = validated

        return self.render()

    def render(self) -> str:
        if not self.items:
            return "当前没有 Todo"

        lines = []

        for item in self.items:
            status = item["status"]

            if status == "completed":
                mark = "[x]"
            elif status == "in_progress":
                mark = "[>]"
            else:
                mark = "[ ]"

            lines.append(
                f'{mark} {item["id"]}. {item["text"]}'
            )

        return "\n".join(lines)


TODO = TodoManager()


def todo_write(items: list) -> str:
    return TODO.update(items)


# =====================================================
# 5. Tool Registry
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
    },

    "todo_write": {
        "handler": todo_write,
        "permission": "allow",
        "schema": {
            "type": "function",
            "name": "todo_write",
            "description": (
                "创建或更新复杂任务的完整 Todo 计划。"
                "仅当任务内容或状态真正发生变化时调用，"
                "每次必须提交完整 Todo 列表，"
                "不要重复提交相同 Todo。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "description": (
                            "当前完整 Todo 列表，不是增量更新。"
                            "只包含完成用户目标所需的实际执行步骤，"
                            "不包含制定计划、更新 Todo、确认完成等元任务。"
                        ),
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "integer",
                                    "description": "任务编号"
                                },
                                "text": {
                                    "type": "string",
                                    "description": "任务内容"
                                },
                                "status": {
                                    "type": "string",
                                    "enum": [
                                        "pending",
                                        "in_progress",
                                        "completed"
                                    ],
                                    "description": "任务状态"
                                }
                            },
                            "required": [
                                "id",
                                "text",
                                "status"
                            ],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["items"],
                "additionalProperties": False
            },
            "strict": True
        }
    }
}


TOOLS = [
    tool["schema"]
    for tool in REGISTRY.values()
]


# =====================================================
# 6. Hooks
# =====================================================

HOOKS = {
    "PreToolUse": [],
    "PostToolUse": []
}


def register_hook(event_name: str, hook_func):
    if event_name not in HOOKS:
        raise ValueError(
            f"未知 Hook 事件：{event_name}"
        )

    HOOKS[event_name].append(hook_func)


def run_hooks(event_name: str, **context):
    for hook_func in HOOKS[event_name]:
        hook_func(**context)


def log_pre_tool(
    tool_name: str,
    arguments: dict,
    **kwargs
):
    print(
        f"\n[PreToolUse] 准备调用工具：{tool_name}"
    )
    print(
        f"参数：{arguments}"
    )


def log_post_tool(
    tool_name: str,
    result: str,
    **kwargs
):
    print(
        f"\n[PostToolUse] 工具执行完成：{tool_name}"
    )
    print(
        f"结果：{result}"
    )


register_hook(
    "PreToolUse",
    log_pre_tool
)

register_hook(
    "PostToolUse",
    log_post_tool
)


# =====================================================
# 7. Permission + Tool Execution
# =====================================================

def check_permission(
    name: str,
    arguments: dict
) -> bool:
    permission = REGISTRY[name]["permission"]

    if permission == "allow":
        return True

    if permission == "deny":
        return False

    print(
        f"\nAgent 想调用工具：{name}"
    )
    print(
        f"参数：{arguments}"
    )

    confirm = input(
        "允许执行吗？(y/n)："
    )

    return confirm.lower() == "y"


def execute_tool(
    name: str,
    arguments: dict
) -> str:
    tool = REGISTRY.get(name)

    if tool is None:
        return f"未知工具：{name}"

    run_hooks(
        "PreToolUse",
        tool_name=name,
        arguments=arguments
    )

    if not check_permission(
        name,
        arguments
    ):
        return (
            f"工具 {name} 未执行，"
            "因为权限未通过"
        )

    try:
        result = tool["handler"](
            **arguments
        )

    except Exception as e:
        result = (
            f"工具 {name} 执行失败：{e}"
        )

    run_hooks(
        "PostToolUse",
        tool_name=name,
        arguments=arguments,
        result=result
    )

    return result


# =====================================================
# 8. Agent Instructions
# =====================================================

SYSTEM_PROMPT = """
你是一个 Coding Agent，可以通过工具完成编程任务。

Todo 使用规则：

1. 只有当任务包含多个实际执行步骤时，才使用 todo_write。

2. Todo 只记录完成用户目标所需的实际任务。
不要把“制定计划”“更新 Todo”“确认任务完成”等管理 Todo 本身的动作写成 Todo。

3. 第一次创建 Todo 后，每次更新都必须提交完整 Todo 列表，
而不是只提交发生变化的某一个任务。

4. 只有当 Todo 的内容或状态真正发生变化时，才调用 todo_write。
不要连续提交完全相同的 Todo。

5. 同一时间最多只能有一个任务处于 in_progress 状态。

6. 一个实际任务完成后，再把它改成 completed，
并将下一个需要执行的任务改成 in_progress。

7. 如果一个工具的返回结果已经能够直接证明任务是否成功，
不要为了验证同一件事情重复执行相同或等价的工具调用。

8. 当所有 Todo 都 completed，并且用户目标已经完成时，
直接给出最终答复，不要再执行无必要的工具。

9. 对于使用 Todo 的任务，应保持 Todo 与真实执行进度一致。
完成一个 Todo 后，应在继续下一个实际任务前更新 Todo 状态。
"""


# =====================================================
# 9. Agent Loop
# =====================================================

def agent_loop(
    query: str,
    max_steps: int = 20
):
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": query
        }
    ]

    for _ in range(max_steps):
        response = client.responses.create(
            model=MODEL,
            tools=TOOLS,
            input=messages
        )

        messages += response.output

        tool_called = False
        seen_calls = set()

        for item in response.output:
            if item.type != "function_call":
                continue

            tool_called = True

            arguments = json.loads(
                item.arguments
            )

            normalized_arguments = json.dumps(
                arguments,
                sort_keys=True,
                ensure_ascii=False
            )

            call_key = (
                item.name,
                normalized_arguments
            )

            if call_key in seen_calls:
                result = (
                    f"跳过重复工具调用：{item.name}。"
                    "本轮已经执行过参数完全相同的调用。"
                )

            else:
                seen_calls.add(call_key)

                result = execute_tool(
                    item.name,
                    arguments
                )

            messages.append({
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": result
            })

        if not tool_called:
            print("\nAgent:")
            print(response.output_text)
            return

    print(
        "\n达到最大执行步数，Agent 已停止。"
    )


# =====================================================
# 10. 用户入口
# =====================================================

if __name__ == "__main__":
    query = input("你：")
    agent_loop(query)