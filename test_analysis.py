"""
Mock test for analysis_team graph.
Runs without the research_team (PR #18) by using hardcoded mock state.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from dotenv import load_dotenv
load_dotenv()

from app.agent.analysis_team.graph import analysis_team_graph

MOCK_STATE = {
    # --- From research_team (mocked) ---
    "company_name": "Notion",
    "product_info": (
        "Notion is an all-in-one workspace that combines notes, docs, wikis, "
        "and project management. Key features include a flexible block-based editor, "
        "database views (table, kanban, calendar, gallery), templates marketplace, "
        "and AI writing assistant (Notion AI). Target users range from individual "
        "knowledge workers to enterprise teams."
    ),
    "market_info": (
        "Notion has ~30M users globally as of 2024. Users praise its flexibility "
        "but criticize performance on large pages. Main competitors are Confluence "
        "(enterprise), Obsidian (local-first), and Coda. Notion holds strong brand "
        "recognition among tech-savvy and startup communities. G2 rating: 4.7/5."
    ),
    "business_info": (
        "Notion raised $275M Series C at a $10B valuation (2021). Revenue model is "
        "freemium SaaS: Free, Plus ($8/mo), Business ($15/mo), Enterprise (custom). "
        "Backed by Index Ventures, Sequoia, Coatue. Profitable at team/business tier. "
        "Notion AI is an add-on at $10/mo per user."
    ),
    "reference_sources": [
        {"company": "Notion", "dimension": "Product", "url": "https://notion.so"},
        {"company": "Notion", "dimension": "Market", "url": "https://g2.com/notion"},
        {"company": "Notion", "dimension": "Business", "url": "https://crunchbase.com/notion"},
    ],
    "company_profile": (
        "Notion is a leading all-in-one productivity platform with 30M+ users. "
        "It differentiates through its highly flexible block-based editor and deep "
        "database capabilities. Backed by top-tier VCs at a $10B valuation, Notion "
        "is transitioning from a prosumer tool to an enterprise solution, competing "
        "with both Atlassian and Microsoft in the collaboration space."
    ),
    # --- Analysis outputs (empty, to be filled by graph) ---
    "structured_info": {},
    "dimension_scores": {},
    "investment_advice": "",
    "analysis_report": "",
}

if __name__ == "__main__":
    print("Running analysis team graph with mock state...")
    print("-" * 60)

    result = analysis_team_graph.invoke(MOCK_STATE)

    print("\n[Structured Info]")
    import json
    print(json.dumps(result.get("structured_info", {}), indent=2, ensure_ascii=False))

    print("\n[Dimension Scores]")
    print(json.dumps(result.get("dimension_scores", {}), indent=2))

    print("\n[Investment Advice]")
    print(result.get("investment_advice", ""))

    print("\n[Final Report]")
    print(result.get("analysis_report", ""))
