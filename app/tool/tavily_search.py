import os
from tavily import TavilyClient
from dotenv import load_dotenv
from langchain.tools import tool

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


@tool
def tavily_search(query: str) -> list[dict]:
    """
        1. 接收一个query
        2. 检查输入是否合法
        3. 调用底层搜索请求函数
        4. 统一格式
        5. 返回给agent
    """

    # 1. 接收一个query
    # 2. 检查输入是否合法
    _validate_query(query)

    # 3. 调用底层搜索请求函数
    raw_results = _fetch_tavily_results(query)

    # 4. 统一格式
    formatted_results = _format_search_results(raw_results)

    # 5. 返回给agent
    return formatted_results
    

def _fetch_tavily_results(query: str):
    """
        调用tavily search的API，并拿回原始响应
    """
    tavily_client = TavilyClient(api_key = TAVILY_API_KEY)
    response = tavily_client.search(query)
    return response

def _format_search_results(raw_results):
    """
        从原始响应提取真正需要的字段，忽略多余信息，把结果调整成统一格式
    """
    results = raw_results.get("results", [])

    formatted = []

    for item in results:
        formatted.append({
            "title": item.get("title", ""), 
            "url": item.get("url", ""), 
            "snippet": item.get("content", "")
        })

    return formatted

def _validate_query(query: str) -> None:
    """
        检查query的合法性
    """

    # 1. 检查query的类型
    if not isinstance(query, str):
        raise TypeError("Query must be a string.")

    # 2. 去除首尾空格
    query = query.strip()

    # 3. 检查query是否为空字符
    if not query:
        raise ValueError("Query cannot be empty.")