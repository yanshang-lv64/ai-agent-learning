import os
from openai import OpenAI


API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL = os.getenv("LLM_MODEL","gpt-5.6-luna")

client = OpenAI(
    api_key = API_KEY,
    base_url = BASE_URL
)

# response = client.responses.create(
#     model = MODEL,
#     input = "你好你是什么模型？请用一句话介绍一下你自己。"

# )

# answer = response.output_text

# print(answer)

def ask_llm(question:str):

    response = client.responses.create(
        model = MODEL,
        input = question
    )

    answer = response.output_text

    return answer

result = ask_llm("什么是API？")

print(result)