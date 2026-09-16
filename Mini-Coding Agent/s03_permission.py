# ==================
# 1.导入库
# ==================
import os
import json]
import subprocess
from openai import OpenAI


# ==================
# 2 .配置LLM
# ==================
API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL = os.getenv("LLM_MODEL")

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

# ======================
# 3. 创建agent工作目录
# ======================

WORKDIR = os.path.join(
    os.path.dirname(__file__),
    "sandbox"
)

os.makedirs(WORKDIR,exist_ok=True)


# =========================
# 4. 真正的工具
# =========================

def run_command(command:str):
    
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
        timeout=15
    )

    output = result.stdout

    if result.stderr:
        output += "\n错误信息：\n" + result.stderr

    return output

def read_flie(path:str):

    full_path = os.path.join(
        WORKDIR,
        path
    )

    with open(
        full_path,
        "r",
        encoding = "utf-8"
    )as file:

        content = file.read()

    return content

def write_file(path:str,content:str):

    full_path = os.path.join(
        WORKDIR,
        path
    )

    with open(
        full_path,
        "w",
        encoding = "utf-8"

    )as file:
        file.write(content)

    return f"文件{path}写入成功"



# =========================
# 5.工具注册表
# =========================

PERMISSION_RULES = {
    "read_file" : "allow",
    "write_file" : "ask",
    "run_command" : "ask"
}

def check_permission(tool_name:str,arguments:dict):

    decision = PERMISSION_RULES.get(
        tool_name,
        "deny"
    )

    if decision == "allow":
        return True

    if decision == "deny":
        print(f"\n权限拒绝：{tool_name}")
        return False

    if decision == "ask":
        print("\nAgent 想调用工具:")
        print(tool_name)

        print("参数：")
        print(arguments)

        confirm = input("允许执行吗？(y / n):")

        return confirm.lower() == "y"

    return False



TOOL_HANDLERS = {
    "run_command":read_flie,
    "read_file":read_flie,
    "write_file":write_file

}


# =========================
# 6.给LLM看的工具说明
# =========================

TOOLS = [
    {
        "type":"function",
        "name":"run_command",
        "description":"在当前目录执行Powershell命令。可以查看文件，创建文件，运行Python脚本。",
        "parameters":{
            "type":"object",
            "properties":{
                "command":{
                    "type":"string",
                    "description":"需要执行powershell命令"

                }
            },

            "required":["command"],
            "additionalProperties":False
        },
    

        "strict":True
    },

    {
        "type":"function",
        "name":"read_flie",
        "description":"读取当前目录中的文本文件内容",
        "parameters":{
            "type":"object",
            "properties":{
                "path":{
                    "type":"string",
                    "description":"需要读取文件路径"
                }
            },

            "required":["path"],
            "additionalProperties":False
        },

        "strict":True

    },



    {
        "type":"function",
        "name":"write_file",
        "description":"在当前目录中创建或者覆盖一个文本文件",
        "parameters":{
            "type":"object",
            "properties":{
                "path":{
                    "type":"string",
                    "description":"需要写入的文件路径"
                },

                "content":{
                    "type":"string",
                    "description":"需要写入的完整的内容"
                }
            },

            "required":["path","content"],
            "additionalProperties":False
        },

        "strict":True
    }
]




# =========================
# 7.agent loop
#==========================

def agent_loop(query:str):

    messages = [
        {
            "role":"user",
            "content":query
        }
    ]

    while True:

         # 把当前状态 + 工具说明交给 LLM，让模型决定下一步

        response = client.responses.creat(
            model = MODEL,
            tools = TOOLS,
            input = messages
        )

        # 保存模型这一轮的决定

        messages += response.output

        tool_called = False

        # 3. 检查模型这一轮有没有 Tool Call

        for item in response.output:

            if item.type == "function_call":

                tool_called = True

                arguments = json.loads(
                    item.arguments
                )

            # 4. 先进行权限检查

                allowed = check_permission(
                    item.name,
                    arguments
                )

                if not allowed:
                    result = (
                        f"工具{item.name} 未执行，"
                        f"因为权限未通过。"
                    )



                handler =TOOL_HANDLERS.get(
                    item.name
                )

        if handler is None:
            result = f"未知工具：{item.name}"

        else:

            result = handler(**arguments)

        messages.append(
            {
                "type":"function_call_output",
                "call_id":item.call_id,
                "output":result
            }
        )

        if not tool_called:

            print("\nAgent:")
            print(response.output_text)

            return 



# ===========================
# 8. 程序入口
# ===========================
query = input("你：")
agent_loop(query)

