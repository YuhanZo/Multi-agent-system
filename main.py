from dotenv import load_dotenv
from app.agent.research_team.graph import research_team_graph
from app.agent.analysis_team.graph import analysis_team_graph
import json

load_dotenv()

def main():
    company = "Notion"
    
    # 1. Research
    research_result = research_team_graph.invoke({"company_name": company})
    
    # 2. Analysis 
    analysis_input = {
        "company_name": research_result["company_name"],
        "product_info": research_result["product_info"],
        "market_info": research_result["market_info"],
        "business_info": research_result["business_info"],
        "company_profile": research_result["company_profile"],
        "reference_sources": research_result["reference_sources"],
    }
    
    # 3. Analysis
    analysis_result = analysis_team_graph.invoke(analysis_input)

    print(json.dumps(analysis_result, indent=2, ensure_ascii=False).encode("gbk", errors="ignore").decode("gbk"))
    # TODO: wire up research_team + analysis_team graphs

if __name__ == "__main__":
    main()