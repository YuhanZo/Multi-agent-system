from tavily import TavilyClient
from dotenv import load_dotenv
import os

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

tavily_client = TavilyClient(api_key = os.getenv("TAVILY_API_KEY"))
response = tavily_client.search("Who is Yuxiang Duan?")

print(response)