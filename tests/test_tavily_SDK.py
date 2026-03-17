from tavily import TavilyClient
from dotenv import load_dotenv
import os

tavily_client = TavilyClient(api_key = os.getenv("TAVILY_API_KEY"))
response = tavily_client.search("Who is Yuxiang Duan?")

print(response)