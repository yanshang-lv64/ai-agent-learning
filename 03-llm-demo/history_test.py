history = []


question1 = input("你第一次说：")




history.append({
    "role":"user",
    "content":question1
    })

print(history)

question2 = input("你第二次说：")
history.append({
    "role":"user",
    "content":question2
    })

print(history)

history = [
    {
        "role":"user",
        "content":"我今年24岁"
    },
    {
        "role":"assistant",
        "content":"好的，我知道了"},
    {
        "role":"user",
        "content":"我今年几岁？"
    }

    ]



# history.append({
#     "role":"assistant",
#     "content":"你好，小吕！"
# })

# print("AI回答以后：")
# print(history)