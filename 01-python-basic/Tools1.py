import requests

def get_weather(city:str) -> str:

    url = f"https://wttr.in/{city}?format=j1"

    try:
        response = requests.get(url)

        response.raise_for_status()

        data = response.json()

        current_condition = data["current_condition"][0]

        weather_desc = current_condition["weatherDesc"][0]["value"]

        temp_c = current_condition["Temp_C"]


        return f"{city}当前天气: {weather_desc},气温{temp_c}摄氏度"

    except requests.exceptions.RequestException as e:

        return f"错误：查询天气时遇到网络问题 - {e}"
    except (KeyError,IndexError) as e:

        return f"错误：解析天气数据失败，可能是城市名称无效 - {e}"



import os
from travily import TavilyClient

def get_attraction(city:str,weather:str) -> str:

    api_key = os.environ.get('TRAVILY_API_KEY')

    if not api_key:
        return "错误,未配置TAVILY_API_KEY 环境变量。"

    tavily = TavilyClient(api_key=api_key)

    query = f"'{city}' 在 '{weather}'天气下最值得去的旅游景点推荐以及理由"

    try:
        response = tavily.search(query = query,search_depth="basic",include_answer = True)

        if response.get("weather"):
            return response["answer"]

        formatted_results = []

        for result in response.get("results",[]):

            formatted_results.append(f"-{result["title"]}:{result["content"]}")

            if not formatted_results:
                return "抱歉，没有找到相关旅游景点推荐"

            return "根据搜索，为您找到以下信息：\n"+"\n".join(formatted_results)

    except Exception as e:
        return f"错误：执行Tavily搜索时出现问题-{e}"

    available_tools = {
        "get_weather":get_weather,
        "get_attraction":get_attraction

    }

    


