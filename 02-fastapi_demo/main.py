from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# @app.get("/hello")

# def hello(name:str):
#     return {"message":f"你好，{name}"}

# @app.get("/add")

# def add(a:int,b:int):
#     result = a+b

#     return {"message":result}

# @app.get("/square")

# def square(num:int):
#     result = num * num
#     return {"result":result}

# @app.get("/introduce")

# def introduce(name:str,age:int):

#     result = f"我叫：{name} ，年龄是： {age}"
    
#     return{"message":result}

# class UserInfo(BaseModel):
#     name:str
#     age:int

# @app.post("/introduce")
# def introduce(user:UserInfo):

#     message = f"我叫{user.name},今年{user.age}岁"

#     return {
#         "message":message
#     }


# class Chatrequest(BaseModel):
#     message:str
# @app.post("/chat")

# def chatrequest(request:Chatrequest):
#     user_message = request.message

#     ai_message = f"你好，你刚才说的是：{user_message}"

#     return {"answer":ai_message}

class addmethod(BaseModel):
    a:int
    b:int

@app.post("/add")

def add(plus:addmethod):

    result = plus.a + plus.b

    return {
        "message":result
    }