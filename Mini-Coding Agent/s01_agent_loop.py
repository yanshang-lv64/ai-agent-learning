import os
import json
import subprocess

from openai import OpenAI

API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL = os.getenv("LLM_MODEL")

client = OpenAI(
    api_key = API_KEY,
    base_url = BASE_URL
)

WORKDIR = os.path.join(
    os.path.dirname(__file__),
    "sandbox"
)

os.makedirs(WORKDIR,exist_ok=True)


# ==========================
# 1:真正的工具
# ==========================

def run_command(command:str):
    print("\nAgent 想执行：")
    print(command)

    confirm = input("允许执行吗? (y / n)")

    if confirm.lower() != "y":
        return "用户拒绝执行这个命令。"

    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-command",
            command
        ],
        cwd = WORKDIR,
        capture_output=True,
        text = True,
        timeout = 30

    )

    output = result.stdout

    if result.stderr:
        output += "\n错误信息：\n" + result.stderr

    return output


# =====================================
# 2. 给LLM看的工具说明
# =====================================

TOOLS = [
    {
        "type":"function",
        "name":"run_command",
        "description":"在当前工作目录中执行 Powershell命令。可以查看文件,创建文件,运行Python程序等。",
        "parameters":{
            "type":"object",
            "properties":{
                "command":{
                    "type":"string",
                    "description":"需要执行Powershell命令"
                }
            },
            "required":["command"],
            "additionalProperties":False
        },
        "strict":True
    }
]

# ========================================
# 3. agent_loop
# ========================================

def agent_loop(query:str):

    messages = [
        {
            "role":"user",
            "content":query
        }
    ]

    while True:

        response = client.responses.create(
            model = MODEL,
            tools= TOOLS,
            input=messages
        )
        
        # 保存模型这一轮的输出

        messages += response.output

        tool_called = False

        for item in response.output:

            if item.type == "function_call":

                tool_called = True

                arguments = json.loads(
                    item.arguments
                )

                if item.name == "run_command":

                    result = run_command(
                        arguments['command']
                    )

                    messages.append(
                        {
                            "type":"function_call_output",
                            "call_id" : item.call_id,
                            "output":result
                        }
                    )

            # 如果没有工具调用，则这一轮结束
            # 说明模型任务任务结束

        if not tool_called:
            print("\nAgent:")
            print(response.output_text)

            return


# ======================================================
# 4. 用户入口
# ======================================================

query = input("你：")
agent_loop(query)



            