from tavily import TavilyClient
from dotenv import load_dotenv
from app.core.config import settings
import os


tavily_client = TavilyClient(api_key = settings.TAVILY_API_KEY)
response = tavily_client.search("Who is Yuxiang Duan?")

print(response)