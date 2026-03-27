from dotenv import load_dotenv
from app.agent.graph import main_graph
import json

load_dotenv()

def main():
    company = "Notion"
    result = main_graph.invoke({"company_name": company})
    print(json.dumps(result, indent=2, ensure_ascii=False).encode("gbk", errors="ignore").decode("gbk"))

if __name__ == "__main__":
    main()
