import os

from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI


API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_ERL")
MODEL = os.getenv("LLM_MODEL","gpt-5.6-luna")

client = OpenAI(
    api_key = API_KEY,
    base_url = BASE_URL
)

app = FastAPI()

class ChatRequest(BaseModel):
    message:str

def ask_llm(question:str):

    response = client.responses.create(
        model = MODEL,
        input = question
    )

    return response.output_text

@app.post("/chat")

def chat(data:ChatRequest):

    answer = ask_llm(data.message)

    return{
        "answer":answer
    }