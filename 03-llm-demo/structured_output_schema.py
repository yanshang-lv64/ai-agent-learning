import os
from openai import OpenAI
from pydantic import BaseModel

API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL = os.getenv("LLM_MODEL")

client = OpenAI(
    api_key = API_KEY,
    base_url = BASE_URL
)

class WeatherResult(BaseModel):
    city:str
    weather:str
    temperature:int

response = client.responses.parse(
    model=MODEL,
    input = "北京今天晴天，温度25摄氏度，请提取天气信息。",
    text_format = WeatherResult
)

result = response.output_parsed
print(result)
print(type(result))

print("城市：",result.city)
print("天气：",result.weather)
print("温度：",result.temperature)

print(type(result.temperature))
