import os
import json

from openai import OpenAI

API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL = os.getenv("LLM_MODEL")

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

tools = [
    {
        "type":"function",
        "name":"get_weather",
        "description":"获取指定城市的当前天气信息",
        "parameters":{
            "type":"object",
            "properties":{
                "city":{
                    "type":"string",
                    "description":"需要查询天气的城市，例如北京，上海"
                }
                },
                "required":["city"],
                "additionalProperties":False
            },
            "strict":True
        }
   
    
    
]

response = client.responses.create(
    model = MODEL,
    tools = tools,
    input = "北京今天的天气怎样？"
)  

for item in response.output:
    print("类型：",item.type)

    if item.type == "function_call":
        print("模型想调用的工具：",item.name)

        print("模型给出的参数：",item.arguments)

        arguments = json.loads(item.arguments)

        print("Python解析后的参数：",arguments)
        print("城市：",arguments["city"])