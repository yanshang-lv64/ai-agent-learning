import os
import json
from openai import OpenAI
from pydantic import BaseModel

API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL = os.getenv("LLM_MODEL","gpt-5.6-luna")


class WeatherResult(BaseModel):

    city:str
    weather:str
    temperature:int


client = OpenAI(
    api_key= API_KEY,
    base_url= BASE_URL
)


prompt = """
请你分析下面的信息：

北京今天晴天，温度25℃。

请按照下面的json格式返回：
{
"city":"城市"，
"weather":"天气"，
"temperature":"温度"


}

要求：temperature 必须是整数，只能返回数字，不要包含"℃或者其他单位。"

"""

response = client.responses.create(
    model = MODEL,
    input = prompt
)

answer = response.output_text

print(answer)

data = json.loads(answer)

weather_result = WeatherResult.model_validate(data)

print(weather_result)









# print(type(answer))
# print(type(data))
# print(type(data["temperature"]))

# print(data["city"])
# print(data["weather"])
# print(data["temperature"])