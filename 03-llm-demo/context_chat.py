import os

from openai import OpenAI

API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL = os.getenv("LLM_MODEL","gpt-5.6-luna")

client = OpenAI(
    api_key = API_KEY,
    base_url = BASE_URL
)

SYSTEM_PROMPT = """

你是一个友好的AI助手。
使用简单，清晰的语言回答用户。

"""

history = []

while True:
    question = input("你：")

    if question == "退出":
        break

    history.append({
        "role":"user",
        "content":question
    })

    response = client.responses.create(
        model = MODEL,
        instructions = SYSTEM_PROMPT,
        input = history
    )

    answer = response.output_text

    print("AI:",answer)

    history.append({
        "role":"assistant",
        "content":answer
    })