import os
from openai import OpenAI
from pydantic import BaseModel
from typing import Literal

API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL = os.getenv("LLM_MODEL")

client = OpenAI(
    api_key = API_KEY,
    base_url = BASE_URL

)

class UserIntent(BaseModel):
    intent:Literal["weather","chat"]
    city:str

response = client.responses.parse(
    model = MODEL,
    input = "帮我查一下北京今天的天气",
    text_format = UserIntent
)

result = response.output_parsed

print(result)
print("用户意图：",result.intent)
print("城市：",result.city)

if result.intent == "weather":
    print("下一步应该调用天气工具")
    print("查询城市：",result.city)
